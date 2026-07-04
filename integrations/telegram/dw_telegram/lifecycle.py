"""Project lifecycle from chat: open, install, create (§4 ring 2).

Every act is a proposal with a preview and an approval tap, and
every path is allow-listed: a target outside the operator's
declared ``workspace_roots`` is refused before any step plans, let
alone runs. "Create" means *on the rails or it didn't happen*:
scaffolded git repo → rails installed → roadmap skeleton →
``dw doctor`` green → first gated commit, executed step by step
with the first failure reported honestly and nothing papered over.

The bootstrap commit and certification-by-recorded-consent: the
first commit of a freshly scaffolded repo must pass the gate like
any other, and certification is human, always. Here the human act
is the owner's approval tap on a preview that says exactly what
will be certified; the interface records that consent in the
contract (``--consent yes --reasons``) and flips the boxes of the
*bootstrap contract only* — a commit in a repo that has no stories,
no evidence, and no history, where every rule is mechanically
checkable and the dw gate re-verifies each fact downstream anyway.
Story-work certification is never delegated this way; the two
allow-listed story verbs cannot commit at all.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .config import Config
from .rails import RailsClient

LIFECYCLE_TIMEOUT_SECONDS = 300

BOOTSTRAP_COMMIT_MESSAGE = "Adopt Delivery Workbench rails"
BOOTSTRAP_CONSENT_REASON = (
    "bootstrap scaffold approved by the paired owner in chat"
)


def subprocess_runner(argv: list[str], cwd: str | None = None):
    return subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=LIFECYCLE_TIMEOUT_SECONDS,
    )


def within_roots(path: Path, roots: list[Path]) -> bool:
    """True when path is inside (or is) one of the workspace roots."""
    try:
        resolved = path.resolve()
    except OSError:
        return False
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def is_rails_repo(path: Path) -> bool:
    return (path / "pm" / "roadmap").is_dir() and (
        path / ".githooks" / "dw"
    ).is_file()


def payload_dir() -> Path | None:
    """The pmo-roadmap payload of the checkout this interface runs
    from (integrations/telegram/dw_telegram → repo root)."""
    root = Path(__file__).resolve().parents[3]
    candidate = root / "pmo-roadmap"
    if (candidate / "install.sh").is_file():
        return candidate
    return None


class LifecycleClient:
    def __init__(
        self, config: Config, rails: RailsClient, runner=None
    ) -> None:
        self._config = config
        self._rails = rails
        self._run = runner or subprocess_runner

    def check_open(self, path: Path) -> tuple[bool, str]:
        if not within_roots(path, self._config.workspace_roots):
            return False, f"{path} is outside the allow-listed workspace roots"
        if not path.is_dir():
            return False, f"{path} does not exist"
        if not is_rails_repo(path):
            return False, f"{path} is not a rails repo (pm/roadmap + .githooks/dw)"
        return True, "ok"

    def plan_install(self, path: Path) -> tuple[list | None, str]:
        if not within_roots(path, self._config.workspace_roots):
            return None, f"{path} is outside the allow-listed workspace roots"
        if not (path / ".git").is_dir():
            return None, f"{path} is not a git repository"
        payload = payload_dir()
        if payload is None:
            return None, "cannot locate the pmo-roadmap payload"
        steps = [
            ("install rails", ["bash", str(payload / "install.sh"), str(path)], None),
            ("doctor", None, "doctor"),
        ]
        return steps, "ok"

    def plan_create(
        self, path: Path, slug: str, prefix: str, name: str
    ) -> tuple[list | None, str]:
        if not within_roots(path, self._config.workspace_roots):
            return None, f"{path} is outside the allow-listed workspace roots"
        if path.exists():
            return None, f"{path} already exists"
        payload = payload_dir()
        if payload is None:
            return None, "cannot locate the pmo-roadmap payload"
        steps = [
            ("git init", ["git", "init", "-q", str(path)], None),
            ("install rails", ["bash", str(payload / "install.sh"), str(path)], None),
            (
                "roadmap skeleton",
                [
                    "bash",
                    str(payload / "bootstrap" / "new-project.sh"),
                    str(path), slug, name, prefix,
                ],
                None,
            ),
            ("doctor", None, "doctor"),
            ("stage", ["git", "-C", str(path), "add", "-A"], None),
            ("contract", None, "contract"),
            ("certify bootstrap contract", None, "certify"),
            (
                "first gated commit",
                ["git", "-C", str(path), "commit", "-q", "-m", BOOTSTRAP_COMMIT_MESSAGE],
                None,
            ),
        ]
        return steps, "ok"

    def execute(self, path: Path, steps: list) -> tuple[bool, list[str]]:
        """Run steps in order; stop at the first failure. Returns
        (ok, per-step report lines)."""
        report: list[str] = []
        for label, argv, special in steps:
            if special == "doctor":
                base = self._rails.dw_base(path)
                argv = [*base, "doctor"] if base else None
                if argv is None:
                    report.append(f"✗ {label}: no dw CLI in {path}")
                    return False, report
            elif special == "contract":
                base = self._rails.dw_base(path)
                if base is None:
                    report.append(f"✗ {label}: no dw CLI in {path}")
                    return False, report
                argv = [
                    *base, "contract", "new",
                    "--consent", "yes",
                    "--reasons", BOOTSTRAP_CONSENT_REASON,
                ]
            elif special == "certify":
                ok, message = self._certify_bootstrap_contract(path)
                report.append(
                    (f"✓ {label}" if ok else f"✗ {label}: {message}")
                )
                if not ok:
                    return False, report
                continue
            try:
                completed = self._run(argv, str(path) if path.exists() else None)
            except (OSError, subprocess.TimeoutExpired) as exc:
                report.append(f"✗ {label}: {exc}")
                return False, report
            if completed.returncode != 0:
                detail = (
                    (completed.stderr or "").strip()
                    or (completed.stdout or "").strip()
                )
                report.append(f"✗ {label}: {detail[:400]}")
                return False, report
            report.append(f"✓ {label}")
        return True, report

    @staticmethod
    def _certify_bootstrap_contract(path: Path) -> tuple[bool, str]:
        contract = path / ".tmp" / "CONTRACT.md"
        if not contract.is_file():
            return False, "no contract was generated"
        text = contract.read_text(encoding="utf-8")
        if "- [ ]" not in text:
            return True, "nothing to certify"
        contract.write_text(
            text.replace("- [ ]", "- [x]"), encoding="utf-8"
        )
        return True, "ok"
