"""The commit gate engine.

Single implementation of every structural rule the pre-commit hook
enforces: contract presence/freshness/checkboxes, shipped-story
detection, one-story-per-commit atomicity, forward and reverse
evidence pairing, and work-log capture preconditions. The bash
pre-commit shim only wires configuration and invokes this engine; the
verdict here is the verdict everywhere.

Design decisions that fix the historical bash/python drift:

- Shipped-story detection compares the story's **Status** header in the
  HEAD blob against the index blob, using the shared ``DONE_STATUSES``
  vocabulary. Renames and reformatting of already-done stories are not
  flips; a flip to any done synonym (``done|complete|closed|shipped``)
  is a flip.
- Evidence numbers are compared as integers, so ``evidence-story-1.md``
  and ``evidence-story-01.md`` pair with ``story-1-*`` and
  ``story-01-*`` alike.
- Staged paths are read NUL-separated (``-z``), so spaces never split.
- Checkboxes accept ``[x]`` and ``[X]``.
- The roadmap prefix comes from ``roadmap_dir(root)``, so a self-hosted
  layout (``pmo-roadmap/pm/roadmap``) is enforced exactly like the
  standard ``pm/roadmap``.
- Evidence deletions are legal unless they orphan a story that remains
  done in the index; modified evidence is legal while its story is done
  in the index; added evidence still requires its story to flip in the
  same commit.

Configuration precedence for ``EXPECTED_BOXES`` / ``PMO_WORK_LOG_ENABLED``:
simple assignments in ``.githooks/pre-commit.config`` beat the
environment, which beats the default. (The shim sources the config as
bash and exports the result, so computed assignments still reach the
gate via the environment.)
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .model import DONE_STATUSES, DwError
from .paths import read_text, rel, roadmap_dir

CONTRACT_REL = ".tmp/CONTRACT.md"
BUNDLE_OK_REL = ".tmp/BUNDLE-OK.md"

_STATUS_LINE_RE = re.compile(r"^- \*\*Status:\*\*\s*(.+)$")
_CHECKED_BOX_RE = re.compile(r"^- \[[xX]\]")
_UNCHECKED_BOX_RE = re.compile(r"^- \[ \]")
_CONSENT_RE = re.compile(r"^\*\*Work-log consent:\*\*[ \t]*yes([ \t]|$)", re.IGNORECASE | re.MULTILINE)


@dataclass
class GateFailure:
    rule: str
    message: str
    remediation: str
    details: list[str] = field(default_factory=list)


@dataclass
class GateResult:
    ok: bool
    root: Path
    failure: GateFailure | None
    expected_boxes: int
    checked_boxes: int
    staged: list[str] = field(default_factory=list)
    staged_stories: list[str] = field(default_factory=list)
    staged_evidence: list[str] = field(default_factory=list)
    shipped_stories: list[str] = field(default_factory=list)
    worklog_capture: bool = False


def _git(root: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None


def _config_value(root: Path, key: str) -> str | None:
    """Parse a simple KEY=value assignment from .githooks/pre-commit.config.

    Only plain (optionally quoted) assignments are recognized; computed
    bash still reaches the gate through the environment via the shim.
    The last assignment wins, matching bash sourcing.
    """
    cfg = root / ".githooks" / "pre-commit.config"
    if not cfg.is_file():
        return None
    pattern = re.compile(r"^\s*(?:export\s+)?" + re.escape(key) + r"=([\"']?)(.*?)\1\s*$")
    value: str | None = None
    try:
        for line in read_text(cfg).splitlines():
            m = pattern.match(line)
            if m:
                value = m.group(2)
    except OSError:
        return None
    return value


def _enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "yes", "true", "on"}


def _status_of(content: str | None) -> str | None:
    if content is None:
        return None
    for line in content.splitlines():
        m = _STATUS_LINE_RE.match(line)
        if m:
            return m.group(1).strip().lower()
    return None


def _index_blob(root: Path, path: str) -> str | None:
    return _git(root, "show", f":0:{path}")


def _head_blob(root: Path, path: str) -> str | None:
    return _git(root, "show", f"HEAD:{path}")


def _staged_entries(root: Path) -> list[tuple[str, str, str | None]]:
    """Return (status, path, old_path) tuples from the staged diff.

    Renames yield ('R', new_path, old_path). NUL-separated parsing keeps
    paths with spaces intact.
    """
    out = _git(root, "diff", "--cached", "--name-status", "-z", "-M")
    if out is None:
        return []
    tokens = out.split("\0")
    entries: list[tuple[str, str, str | None]] = []
    i = 0
    while i < len(tokens):
        status = tokens[i]
        if not status:
            i += 1
            continue
        kind = status[0]
        if kind in {"R", "C"} and i + 2 < len(tokens) + 1:
            old_path = tokens[i + 1] if i + 1 < len(tokens) else ""
            new_path = tokens[i + 2] if i + 2 < len(tokens) else ""
            if new_path:
                entries.append((kind, new_path, old_path))
            i += 3
        else:
            path = tokens[i + 1] if i + 1 < len(tokens) else ""
            if path:
                entries.append((kind, path, None))
            i += 2
    return entries


def _in_rewrite_state(root: Path) -> bool:
    git_dir = (_git(root, "rev-parse", "--git-dir") or "").strip()
    if not git_dir:
        return False
    gd = Path(git_dir)
    if not gd.is_absolute():
        gd = root / gd
    return (
        (gd / "rebase-merge").is_dir()
        or (gd / "rebase-apply").is_dir()
        or (gd / "CHERRY_PICK_HEAD").is_file()
        or (gd / "REVERT_HEAD").is_file()
    )


def _roadmap_prefix(root: Path) -> str | None:
    try:
        rd = roadmap_dir(root)
    except DwError:
        return None
    prefix = rel(rd, root).replace(os.sep, "/")
    return prefix.rstrip("/") + "/"


def _index_story_status_for(root: Path, phase_dir: str, num: int, story_re: re.Pattern[str]) -> tuple[str | None, str | None]:
    """Find the story file for (phase_dir, num) in the index; return (path, status)."""
    out = _git(root, "ls-files", "-z", "--", phase_dir)
    if out is None:
        return None, None
    for path in out.split("\0"):
        if not path:
            continue
        m = story_re.match(path)
        if m and Path(path).parent.as_posix() == phase_dir and int(m.group(1)) == num:
            return path, _status_of(_index_blob(root, path))
    return None, None


def run_gate(
    root: Path,
    expected_boxes: int | None = None,
    work_log_enabled: bool | None = None,
) -> GateResult:
    if expected_boxes is None:
        raw = _config_value(root, "EXPECTED_BOXES") or os.environ.get("EXPECTED_BOXES") or "7"
        try:
            expected_boxes = int(raw)
        except ValueError:
            expected_boxes = 7
    if work_log_enabled is None:
        raw_enabled = _config_value(root, "PMO_WORK_LOG_ENABLED")
        if raw_enabled is None:
            raw_enabled = os.environ.get("PMO_WORK_LOG_ENABLED")
        work_log_enabled = _enabled(raw_enabled)

    result = GateResult(
        ok=True,
        root=root,
        failure=None,
        expected_boxes=expected_boxes,
        checked_boxes=0,
    )

    def failed(rule: str, message: str, remediation: str, details: list[str] | None = None) -> GateResult:
        result.ok = False
        result.failure = GateFailure(rule, message, remediation, details or [])
        return result

    contract_path = root / CONTRACT_REL
    bundle_ok_path = root / BUNDLE_OK_REL

    # 1. Contract exists.
    if not contract_path.is_file():
        return failed(
            "contract-missing",
            "Missing .tmp/CONTRACT.md — commit blocked.",
            f"Write {CONTRACT_REL} per the contract template with all "
            f"{expected_boxes} checkboxes set to [x]; it is deleted on successful commit.",
        )

    contract_text = read_text(contract_path)

    # 2. Freshness — mtime must not be older than HEAD's committer time.
    head_epoch_raw = (_git(root, "log", "-1", "--format=%ct", "HEAD") or "").strip()
    if head_epoch_raw:
        head_epoch = int(head_epoch_raw)
        contract_epoch = int(contract_path.stat().st_mtime)
        # Strictly older than HEAD = stale. Equality is allowed: the
        # previous commit's hook deleted any prior contract, so a
        # same-second contract is necessarily for this commit.
        if contract_epoch < head_epoch:
            return failed(
                "contract-stale",
                ".tmp/CONTRACT.md is stale (older than last commit).",
                "Re-write .tmp/CONTRACT.md for this commit.",
            )

    # 3. No unchecked boxes.
    unchecked = [
        f"{i}: {line}"
        for i, line in enumerate(contract_text.splitlines(), start=1)
        if _UNCHECKED_BOX_RE.match(line)
    ]
    if unchecked:
        return failed(
            "contract-unchecked",
            ".tmp/CONTRACT.md still has unchecked items.",
            "Flip every '- [ ]' to '- [x]' only after honestly verifying each rule.",
            details=unchecked,
        )

    # 4. Enough checked boxes ([x] or [X]).
    result.checked_boxes = sum(
        1 for line in contract_text.splitlines() if _CHECKED_BOX_RE.match(line)
    )
    if result.checked_boxes < expected_boxes:
        return failed(
            "contract-boxes",
            f".tmp/CONTRACT.md has only {result.checked_boxes}/{expected_boxes} required [x] checkboxes.",
            "Complete the contract template; project extensions may raise the count via EXPECTED_BOXES.",
        )

    # Work-log capture preconditions (reported even when no stories staged).
    result.worklog_capture = bool(
        work_log_enabled and _CONSENT_RE.search(contract_text) and not _in_rewrite_state(root)
    )

    # Structural checks are scoped to the actual roadmap tree.
    entries = _staged_entries(root)
    result.staged = [path for _status, path, _old in entries]

    prefix = _roadmap_prefix(root)
    if prefix is None:
        return result

    story_re = re.compile(rf"^{re.escape(prefix)}[^/]+/phase-[^/]+/story-(\d+)-.*\.md$")
    evidence_re = re.compile(rf"^{re.escape(prefix)}[^/]+/phase-[^/]+/evidence-story-(\d+)\.md$")

    story_entries: list[tuple[str, str, str | None, int]] = []
    evidence_entries: list[tuple[str, str, int]] = []
    for status, path, old_path in entries:
        m = story_re.match(path)
        if m:
            story_entries.append((status, path, old_path, int(m.group(1))))
            result.staged_stories.append(path)
        m = evidence_re.match(path)
        if m:
            evidence_entries.append((status, path, int(m.group(1))))
            result.staged_evidence.append(path)
        if status == "R" and old_path:
            m_old = evidence_re.match(old_path)
            if m_old:
                evidence_entries.append(("D", old_path, int(m_old.group(1))))

    # 5. Shipped-story detection: HEAD status vs index status, shared vocabulary.
    for status, path, old_path, _num in story_entries:
        if status == "D":
            continue
        new_status = _status_of(_index_blob(root, path))
        if new_status not in DONE_STATUSES:
            continue
        head_source = old_path if (status == "R" and old_path) else path
        old_status = _status_of(_head_blob(root, head_source))
        if old_status not in DONE_STATUSES:
            result.shipped_stories.append(path)

    shipped_keys = {
        (Path(p).parent.as_posix(), int(story_re.match(p).group(1)))  # type: ignore[union-attr]
        for p in result.shipped_stories
    }

    # 6. Atomicity: one shipped story per commit unless BUNDLE-OK exists.
    if len(result.shipped_stories) > 1 and not bundle_ok_path.is_file():
        return failed(
            "atomicity",
            f"Atomicity violation — {len(result.shipped_stories)} stories flipped to done in one commit.",
            "Rule: one PR per story. To bundle intentionally, write .tmp/BUNDLE-OK.md "
            "with a one-line rationale (auto-deleted on successful commit).",
            details=[f"shipped: {p}" for p in result.shipped_stories],
        )

    # 7. Forward pairing: each shipped story ships its evidence in this commit.
    staged_evidence_present = {
        (Path(p).parent.as_posix(), num)
        for status, p, num in evidence_entries
        if status != "D"
    }
    for path in result.shipped_stories:
        phase_dir = Path(path).parent.as_posix()
        num = int(story_re.match(path).group(1))  # type: ignore[union-attr]
        if (phase_dir, num) not in staged_evidence_present:
            expected_name = f"{phase_dir}/evidence-story-{num:02d}.md"
            return failed(
                "evidence-missing",
                f"Evidence missing — story {path} flipped to done but {expected_name} is not in this commit.",
                "A story flipping to done must ship its evidence file in the same commit "
                "(unpadded numbering is accepted).",
            )

    # 8. Reverse pairing: evidence appears/disappears only in legal states.
    for status, path, num in evidence_entries:
        phase_dir = Path(path).parent.as_posix()
        story_path, story_status = _index_story_status_for(root, phase_dir, num, story_re)
        if status == "D":
            if story_path is not None and story_status in DONE_STATUSES:
                return failed(
                    "evidence-deletion-orphans-story",
                    f"Evidence deletion blocked — deleting {path} would orphan done story {story_path}.",
                    "Regress or remove the story in the same commit, or keep its evidence.",
                )
            continue
        if status == "A":
            if (phase_dir, num) not in shipped_keys:
                return failed(
                    "orphan-evidence",
                    f"Orphan evidence — {path} added but no story-{num}-*.md in this phase "
                    "flipped to done in this commit.",
                    "Evidence files appear only when their story ships.",
                )
            continue
        # Modified (or rename target) evidence: legal while its story is done in the index.
        if (phase_dir, num) in shipped_keys:
            continue
        if story_path is None or story_status not in DONE_STATUSES:
            return failed(
                "orphan-evidence",
                f"Orphan evidence — {path} changed but its story is not done in this commit's index.",
                "Amend evidence only for a story that is (or is flipping) done.",
            )

    return result


# ── rendering ────────────────────────────────────────────────────────

_BAR = "━" * 68

_RULES_REMINDER = """Before this commit lands, certify in .tmp/CONTRACT.md that you followed:

  1. Evidence, not vibes — claimed work has on-disk command output.
  2. Master docs updated in this same commit (story header,
     current-phase-status, project README, BACKLOG/CHANGELOG).
  3. Tests actually ran via the project's documented scripts.
  4. Greenfield discipline (no migrations / shims, where applicable).
  5. No --no-verify, no unauthorized Co-Authored-By, no scope creep.
  6. If a story flipped to "done", evidence-story-*.md ships with it.
  7. One PR per story (or bundling documented)."""


def _rules_doc(root: Path) -> str:
    for candidate in ("pm/roadmap/PMO-CONTRACT.md", "pmo-roadmap/templates/PMO-CONTRACT.md"):
        if (root / candidate).is_file():
            return candidate
    return "pm/roadmap/PMO-CONTRACT.md"


def render_gate_failure(result: GateResult) -> str:
    failure = result.failure
    if failure is None:
        return ""
    lines = [_BAR, "PMO HYGIENE GATE — dw gate", _BAR]
    if failure.rule.startswith("contract-"):
        lines.append(_RULES_REMINDER)
        lines.append("")
        lines.append(f"  Full rules: {_rules_doc(result.root)} §\"Contract template\"")
        lines.append("")
    lines.append(f"✗ {failure.message}")
    for detail in failure.details:
        lines.append(f"    {detail}")
    lines.append(f"  To proceed: {failure.remediation}")
    lines.append(_BAR)
    return "\n".join(lines) + "\n"


def render_gate_porcelain(result: GateResult) -> str:
    lines = [
        f"gate={'pass' if result.ok else 'fail'}",
        f"expected_boxes={result.expected_boxes}",
        f"checked_boxes={result.checked_boxes}",
        f"shipped_count={len(result.shipped_stories)}",
        f"worklog_capture={'yes' if result.worklog_capture else 'no'}",
    ]
    lines.extend(f"staged={p}" for p in result.staged)
    lines.extend(f"staged_story={p}" for p in result.staged_stories)
    lines.extend(f"staged_evidence={p}" for p in result.staged_evidence)
    lines.extend(f"shipped_story={p}" for p in result.shipped_stories)
    if result.failure is not None:
        lines.append(f"rule={result.failure.rule}")
        lines.append(f"message={result.failure.message}")
        lines.append(f"remediation={result.failure.remediation}")
    return "\n".join(lines) + "\n"
