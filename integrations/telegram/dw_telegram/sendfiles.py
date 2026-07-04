"""Send files through seven locks (WLA-14-06, absorption map §5).

`/send` gives the read ring a file leg: pull a diff, a screenshot,
an evidence file to the phone. The guard pipeline is absorbed
nearly verbatim from ccgram's `send_security.py` — the most
rigorous surface in their codebase — reordered cheap-to-expensive
and extended with the workbench's own state-file lock (lock 7).

Every lock returns a named refusal, and the checks run in an order
that never pays for a subprocess before a stat has ruled the file
out. A clean file passes all seven and just sends — no ceremony on
the happy path (§5).

`validate_sendable(path, root) -> str | None` is pure: None means
sendable, a string is the refusal naming the lock that fired.
"""

from __future__ import annotations

import fnmatch
import re
import stat
import subprocess
from pathlib import Path

SIZE_LIMIT_BYTES = 50 * 1024 * 1024  # Telegram's document ceiling

# Lock 3: names that look like credentials never leave the box.
_SECRET_PATTERNS = (
    "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore",
    "*.token", "*credential*", "*secret*", ".env", ".env.*",
    "id_rsa", "id_ed25519", "*.ppk",
)

# Lock 7: the workbench's own runtime files are unsendable by name,
# ever — the operator config, runtime state, contract scratch, and
# the agent-events / rail-events streams. This lock is ours, not
# ccgram's, and it is why the credential grep in CI stays clean even
# with a file leg.
_WORKBENCH_STATE_NAMES = (
    "telegram.json",
    "telegram-state.json",
    "agent-events.jsonl",
    "delivery_workbench.json",
    "agent_sessions.json",
    "CONTRACT.md",
    "BUNDLE-OK.md",
    "pmo-events.jsonl",
)
_WORKBENCH_STATE_DIRS = (".tmp", ".git")


def _resolved_within(path: Path, root: Path) -> Path | None:
    try:
        resolved = path.resolve()
        resolved.relative_to(root.resolve())
        return resolved
    except (OSError, ValueError):
        return None


def _lock_containment(path: Path, root: Path) -> str | None:
    if _resolved_within(path, root) is None:
        return "outside the repo — path traversal refused (lock 1: containment)"
    return None


def _lock_hidden(path: Path, root: Path) -> str | None:
    resolved = _resolved_within(path, root)
    if resolved is None:
        return None
    rel = resolved.relative_to(root.resolve())
    if any(part.startswith(".") for part in rel.parts):
        return f"hidden file or dir refused (lock 2: hidden): {rel}"
    return None


def _lock_secret(path: Path, root: Path) -> str | None:
    name = path.name.lower()
    for pattern in _SECRET_PATTERNS:
        if fnmatch.fnmatch(name, pattern):
            return f"looks like a credential — refused (lock 3: secret pattern {pattern})"
    return None


def _lock_size_and_type(path: Path, root: Path) -> str | None:
    try:
        info = path.stat()
    except OSError:
        return "file not accessible (lock 4: size/type)"
    if not stat.S_ISREG(info.st_mode):
        return "not a regular file (lock 4: size/type)"
    if info.st_size > SIZE_LIMIT_BYTES:
        return (
            f"too large: {info.st_size / (1024 * 1024):.0f} MB, "
            "limit 50 MB (lock 4: size/type)"
        )
    return None


def _lock_gitignore(path: Path, root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-q", str(path)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None  # not a git repo, or git missing — this lock abstains
    if completed.returncode == 0:
        return "the repo ignores this file, so the bot does too (lock 5: gitignore)"
    return None


def _lock_gitleaks(path: Path, root: Path) -> str | None:
    toml_path = root / ".gitleaks.toml"
    if not toml_path.is_file():
        return None
    try:
        import tomllib
    except ModuleNotFoundError:  # < 3.11
        return None
    try:
        with toml_path.open("rb") as handle:
            config = tomllib.load(handle)
        rel = str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return None
    for rule in config.get("rules", []) or []:
        rule_path = rule.get("path") if isinstance(rule, dict) else None
        if not rule_path:
            continue
        try:
            if re.search(rule_path, rel):
                rule_id = rule.get("id", "gitleaks rule")
                return f"matches a gitleaks rule (lock 6: gitleaks {rule_id})"
        except re.error:
            continue
    return None


def _lock_workbench_state(path: Path, root: Path) -> str | None:
    if path.name in _WORKBENCH_STATE_NAMES:
        return f"a workbench state file is never sendable (lock 7: state): {path.name}"
    resolved = _resolved_within(path, root)
    parts = resolved.parts if resolved else path.parts
    if any(part in _WORKBENCH_STATE_DIRS for part in parts):
        return "inside a workbench state dir, never sendable (lock 7: state)"
    return None


# Ordered cheap-to-expensive: containment and stat before subprocess.
LOCKS = (
    _lock_containment,
    _lock_hidden,
    _lock_secret,
    _lock_size_and_type,
    _lock_workbench_state,
    _lock_gitleaks,
    _lock_gitignore,
)


def validate_sendable(path: Path, root: Path) -> str | None:
    """None if the file may be sent; otherwise the first lock's
    named refusal."""
    for lock in LOCKS:
        refusal = lock(path, root)
        if refusal is not None:
            return refusal
    return None


def resolve_matches(spec: str, root: Path, limit: int = 25) -> list[Path]:
    """Resolve a /send argument to candidate files: an exact path, a
    glob, or a filename substring — searched within the repo, never
    outside it. Containment is re-checked per match at send time."""
    root = root.resolve()
    direct = (root / spec) if not Path(spec).is_absolute() else Path(spec)
    if direct.is_file() and _resolved_within(direct, root) is not None:
        return [direct.resolve()]
    matches: list[Path] = []
    if any(ch in spec for ch in "*?["):
        for candidate in sorted(root.glob(spec)):
            if candidate.is_file():
                matches.append(candidate.resolve())
    else:
        needle = spec.lower()
        for candidate in sorted(root.rglob("*")):
            if len(matches) >= limit:
                break
            if candidate.is_file() and needle in candidate.name.lower():
                if _resolved_within(candidate, root) is not None:
                    matches.append(candidate.resolve())
    return matches[:limit]
