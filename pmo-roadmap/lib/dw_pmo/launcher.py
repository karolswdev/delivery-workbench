"""Global `dw` entry point for the packaged distribution.

Implements the distribution contract (docs/distribution.md): the
per-repo vendored rails are the only gating authority, so a globally
installed `dw` invoked inside an adopted repository execs
`.githooks/dw` unconditionally — even when the global version is
newer. Staleness is reported on stderr, never silently "fixed". The
global CLI acts in its own right only for the bootstrap verbs
(init / install / update / adopt-project / new-project / intake), which
operate on a target repo from outside its rails, and outside adopted
repositories (where it delegates to the packaged copy of bin/dw).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

BOOTSTRAP_VERBS = {
    "init": "install.sh",
    "install": "install.sh",
    "update": "update.sh",
    "adopt-project": "bootstrap/adopt-project.sh",
    "new-project": "bootstrap/new-project.sh",
    "intake": "bootstrap/session-intake.sh",
}

_VERSION_RE = re.compile(r'__version__\s*=\s*"([^"]+)"')


def payload_dir() -> Path | None:
    """Locate the pmo-roadmap payload for the running installation.

    Packaged layout: the payload ships as ``dw_pmo/_payload/``
    mirroring the source tree. Checkout layout: this file lives at
    ``pmo-roadmap/lib/dw_pmo/launcher.py`` and the payload is the
    ``pmo-roadmap`` directory itself — same relative turns either way.
    """
    here = Path(__file__).resolve().parent
    packaged = here / "_payload"
    if (packaged / "install.sh").is_file():
        return packaged
    checkout = here.parent.parent
    if (checkout / "install.sh").is_file() and (checkout / "hooks").is_dir():
        return checkout
    return None


def repo_dw(cwd: Path) -> Path | None:
    """The vendored CLI of the repository containing cwd, if any."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            stdin=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    top = Path(out.strip())
    candidate = top / ".githooks" / "dw"
    return candidate if candidate.is_file() else None


def vendored_version(dw_path: Path) -> str | None:
    init = dw_path.parent / "dw_pmo" / "__init__.py"
    try:
        m = _VERSION_RE.search(init.read_text(encoding="utf-8"))
    except OSError:
        return None
    return m.group(1) if m else None


def _run(argv: list[str]) -> int:
    try:
        # stdin=None (inherit) is deliberate: this is the terminal
        # launcher handing the TTY to the real CLI, which may
        # prompt. Every other dw_pmo child gets DEVNULL (WLA-12-08).
        return subprocess.call(argv, stdin=None)
    except KeyboardInterrupt:
        return 130


def _init_usage() -> str:
    return """Usage: dw init <path> [--inside-existing-repo]

Initialize an empty directory (or an existing empty Git repository), then
vendor Delivery Workbench rails with install.sh --skip-bootstrap.

By default, a target nested anywhere inside another Git repository is refused.
Pass --inside-existing-repo to explicitly make that empty target an independent
nested repository. The target must be the repository root; non-empty projects
should use `dw install <path> --skip-bootstrap` instead.

This command creates no roadmap project and starts no agent or background work.
"""


def _git_toplevel(target: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "--show-toplevel"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def _has_head(target: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(target), "rev-parse", "--verify", "HEAD"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def _init_components(target: Path) -> dict[str, bool]:
    return {
        "Git repository": (target / ".git").exists(),
        "vendored hooks": all(
            (target / ".githooks" / name).is_file()
            for name in ("pre-commit", "commit-msg", "post-commit")
        ),
        "vendored CLI and core": (
            (target / ".githooks" / "dw").is_file()
            and (target / ".githooks" / "dw_pmo" / "__init__.py").is_file()
        ),
        "roadmap canon": all(
            (target / "pm" / "roadmap" / name).is_file()
            for name in ("roadmap-builder.md", "PMO-CONTRACT.md")
        ),
        "agent commands": (target / ".claude" / "commands" / "dw-adopt.md").is_file(),
        "MCP configuration": (target / ".mcp.json").is_file(),
        "agent guidance": any((target / name).is_file() for name in ("CLAUDE.md", "AGENTS.md")),
        "scratch exclusions": (target / ".gitignore").is_file(),
    }


def _print_completed_init(target: Path) -> None:
    print()
    print(f"Delivery Workbench rails are ready in {target}.")
    print("Next, start the intake conversation that will create your roadmap project:")
    print("  1. Open this directory in Claude Code.")
    print("  2. Run /dw-scope and describe what you want to build.")
    print("No project or agent was started automatically.")


def _run_init(payload: Path, argv: list[str]) -> int:
    inside_existing = False
    target_arg: str | None = None
    for arg in argv:
        if arg in {"-h", "--help"}:
            print(_init_usage(), end="")
            return 0
        if arg == "--inside-existing-repo":
            inside_existing = True
            continue
        if arg.startswith("-"):
            print(f"dw init: unknown option: {arg}", file=sys.stderr)
            print(_init_usage(), file=sys.stderr, end="")
            return 2
        if target_arg is not None:
            print(f"dw init: unexpected argument: {arg}", file=sys.stderr)
            print(_init_usage(), file=sys.stderr, end="")
            return 2
        target_arg = arg

    if target_arg is None:
        print("dw init: target path is required", file=sys.stderr)
        print(_init_usage(), file=sys.stderr, end="")
        return 2

    target = Path(target_arg).expanduser()
    if not target.is_dir():
        print(f"dw init: target must be an existing directory: {target}", file=sys.stderr)
        return 2
    target = target.resolve()

    git_root = _git_toplevel(target)
    nested = git_root is not None and git_root != target
    if nested and not inside_existing:
        print(
            f"dw init: refusing target nested inside another repository ({git_root}); "
            "pass --inside-existing-repo to explicitly create an independent nested repository",
            file=sys.stderr,
        )
        return 2

    components = _init_components(target)
    if git_root == target and all(components.values()):
        print(f"Delivery Workbench is already initialized in {target}:")
        for name in components:
            print(f"  already present: {name}")
        _print_completed_init(target)
        return 0

    worktree_entries = [entry for entry in target.iterdir() if entry.name != ".git"]
    if worktree_entries:
        print(
            "dw init: target is not empty; use `dw install <path> --skip-bootstrap` "
            "for an existing project",
            file=sys.stderr,
        )
        return 2
    if git_root == target and _has_head(target):
        print(
            "dw init: target repository already has a commit; use "
            "`dw install <path> --skip-bootstrap` instead",
            file=sys.stderr,
        )
        return 2

    if git_root != target:
        try:
            initialized = subprocess.run(
                ["git", "init", "-q", str(target)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        except OSError as exc:
            print(f"dw init: could not run git init: {exc}", file=sys.stderr)
            return 2
        if initialized.returncode != 0:
            detail = initialized.stderr.strip() or initialized.stdout.strip()
            print(f"dw init: git init failed: {detail}", file=sys.stderr)
            return initialized.returncode or 2
        print(f"initialized Git repository: {target}")
    else:
        print(f"Git repository already present: {target}")

    try:
        installed = subprocess.run(
            ["bash", str(payload / "install.sh"), str(target), "--skip-bootstrap"],
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except KeyboardInterrupt:
        return 130
    except OSError as exc:
        print(f"dw init: could not run install.sh: {exc}", file=sys.stderr)
        return 2
    if installed.stdout:
        print(installed.stdout, end="")
    if installed.stderr:
        print(installed.stderr, file=sys.stderr, end="")
    if installed.returncode != 0:
        return installed.returncode

    _print_completed_init(target)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    from dw_pmo import __version__

    # Bootstrap verbs operate on a target repo from outside its rails;
    # they never defer.
    if args and args[0] in BOOTSTRAP_VERBS:
        payload = payload_dir()
        if payload is None:
            print("dw: cannot locate the packaged pmo-roadmap payload", file=sys.stderr)
            return 2
        if args[0] == "init":
            return _run_init(payload, args[1:])
        script = payload / BOOTSTRAP_VERBS[args[0]]
        return _run(["bash", str(script), *args[1:]])

    # Defer-to-repo rule: inside an adopted repository the vendored
    # copy is the only truthful voice.
    vendored = repo_dw(Path.cwd())
    if vendored is not None:
        theirs = vendored_version(vendored)
        if theirs and theirs != __version__:
            print(
                f"dw: deferring to vendored rails v{theirs} (installed v{__version__}); "
                f"refresh with: dw update {vendored.parent.parent}",
                file=sys.stderr,
            )
        python = os.environ.get("PMO_GATE_PYTHON") or sys.executable
        return _run([python, str(vendored), *args])

    # Outside any adopted repo: delegate to the packaged bin/dw for
    # the roadmap commands (--version, help, etc.).
    payload = payload_dir()
    if payload is None:
        print("dw: cannot locate the packaged pmo-roadmap payload", file=sys.stderr)
        return 2
    return _run([sys.executable, str(payload / "bin" / "dw"), *args])


if __name__ == "__main__":
    sys.exit(main())
