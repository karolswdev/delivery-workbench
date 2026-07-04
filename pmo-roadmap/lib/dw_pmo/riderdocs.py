"""One canonical brief, many rendered surfaces (WLA-12-04).

The agent brief's canon lives in `agentdocs` (embedded block with a
template override); the four command specs' canon lives here as
embedded text, overridden by `pmo-roadmap/agent/<name>.md` whenever
the framework source tree is present — the same fallback pattern
`agentdocs`/`paths.template_dir` already use, which is what lets a
consumer repo (vendored `dw_pmo` only) render and drift-check without
the framework checkout.

Rendered copies are committed, per the Phase 12 design decision: a
fresh clone works in every harness without running a generator, and
drift is *caught*, not prevented — `dw check` re-renders every
existing copy from canon and reports any difference as an ERROR.
`dw rider docs` regenerates. Codex and pi renderers (WLA-12-05/06)
add their targets on this seam.
"""

from __future__ import annotations

from pathlib import Path

from .agentdocs import (
    agents_variant_for,
    managed_region,
    render_block_for,
)
from .paths import read_text, write_text

COMMAND_NAMES = ("dw-adopt", "dw-contract", "dw-next", "dw-story-done")

# Directories (relative to the repo root) that hold rendered command
# copies when they exist. pmo-roadmap/agent/ is canon, not a target.
COMMAND_TARGET_DIRS = (".claude/commands", "plugin/commands")

_EMBEDDED_COMMANDS: dict[str, str] = {
    "dw-adopt": """---
description: Drive Delivery Workbench adoption for this repository (intake → discovery → roadmap).
---

Drive the Delivery Workbench adoption flow for this repository. Ask
the user for anything you cannot infer; do not fabricate intent.

1. Verify the install: `.githooks/dw doctor`. If the framework is not
   installed, run `<framework>/pmo-roadmap/install.sh <this-repo> --skip-bootstrap`
   first (ask the user where the framework checkout lives).
2. Capture intent — run the session intake (interactive when the user
   is present, flags otherwise):
   `<framework>/pmo-roadmap/bootstrap/session-intake.sh <this-repo> --project-name "…" --project-slug <slug> --project-prefix <PFX>`
3. Run adoption discovery:
   `<framework>/pmo-roadmap/bootstrap/adopt-project.sh <this-repo> --project-name "…" --project-slug <slug> --project-prefix <PFX> --require-intake`
   Read the generated `pm/roadmap/<slug>/adoption/adoption-discovery.md`.
4. Turn the report's proposed phases and first stories into a real
   roadmap with `.githooks/dw phase create` and
   `.githooks/dw story create` (show the user the plan first).
5. Finish with `.githooks/dw doctor` and `.githooks/dw check`, and
   report the next actionable story from `.githooks/dw next`.
""",
    "dw-contract": """---
description: Generate and honestly certify the commit contract for the staged work.
---

Author the PMO commit contract for the currently staged work.

1. Confirm staging is final (`git status`, `git diff --cached --stat`).
   The contract stamps the staged index tree — restaging afterwards
   invalidates it.
2. Generate it:
   `.githooks/dw contract new [--story <ID>] [--consent yes --reasons "…"] [--tests-capture <evidence-path>[#ts]]`
   Use `--tests-capture` whenever a passing captured run exists in the
   staged evidence — it discharges the "Tests ran." rule mechanically.
3. Read `.tmp/CONTRACT.md`. For each remaining `- [ ]` box, actually
   verify the rule against the staged diff (evidence on disk, master
   docs updated in this commit, no bypasses, pairing, atomicity). Only
   then flip it to `- [x]`. Never flip a box you have not verified —
   the archived contract and digest trailer make this certification
   permanent.
4. Preflight with `.githooks/dw gate` (non-consuming). If it fails,
   the banner names the rule and the fix.
5. Report the contract summary (story, consent, discharged rules) and
   that the commit is ready.
""",
    "dw-next": """---
description: Orient in the Delivery Workbench roadmap and pick up the next story.
---

Orient yourself in this repository's Delivery Workbench roadmap and
report what to work on next. Do not change anything yet.

1. Run `.githooks/dw doctor` — if anything FAILs, report it and stop.
2. Run `.githooks/dw next --json`. Exit 0 means a story was found;
   exit 2 means nothing is actionable (report that and stop).
3. Run `.githooks/dw check` and `.githooks/dw context --compact`; read
   the current phase's `current-phase-status.md` "Where we are" section
   and the story file itself.
4. Report: the story ID and title, its acceptance criteria, any lint
   issues or warnings that affect it, and your plan to complete it.

If the user confirms, flip it in-progress before working:
`.githooks/dw story status <project> <phase> <story> in-progress`
""",
    "dw-story-done": """---
description: Prove, flip, and ship the current story through the PMO gate.
---

Close out the story the user names (or the current in-progress story
from `.githooks/dw next`). Evidence first, then the flip, then the
gated commit.

1. Prove the work with real runs — for each documented verification
   command:
   `.githooks/dw evidence capture <project> <phase> <story> -- <command>`
   Nonzero exits are recorded honestly; fix and re-capture until the
   run that matters passes. Add narrative context to the evidence file
   around the captured blocks; screenshots/binaries go in `assets/`
   next to it.
2. Flip it: `.githooks/dw story status <project> <phase> <story> done`
   (it refuses without evidence and updates the phase table
   transactionally).
3. Update the phase's "Where we are" pickup snapshot and any canon doc
   the story touches — the gate requires master docs in the same
   commit.
4. Stage everything, then run /dw-contract (generate → verify → certify;
   use `--tests-capture` for the captured run from step 1).
5. `git commit` with a clear message. The gate verifies the flip ships
   its evidence; trailers and the contract archive are automatic.
   Exactly one story flips per commit — bundle only with
   `.tmp/BUNDLE-OK.md` and a one-line rationale.
6. Run `.githooks/dw check` and report the outcome with the commit sha.
""",
}


def _agent_spec_dir() -> Path | None:
    """pmo-roadmap/agent when the framework tree is reachable.

    Source layout: lib/dw_pmo/ -> parents[2] is pmo-roadmap/.
    Vendored layout in the framework repo: .githooks/dw_pmo/ ->
    parents[2] is the repo root, whose pmo-roadmap/agent is canon.
    Consumer repos hit neither and use the embedded specs."""
    base = Path(__file__).resolve().parents[2]
    for candidate in (base / "agent", base / "pmo-roadmap" / "agent"):
        if candidate.is_dir():
            return candidate
    return None


def command_spec(name: str) -> str:
    """Canonical text for one command; source files win when present."""
    if name not in _EMBEDDED_COMMANDS:
        raise KeyError(f"unknown command spec: {name}")
    specs = _agent_spec_dir()
    if specs is not None:
        path = specs / f"{name}.md"
        if path.exists():
            return read_text(path)
    return _EMBEDDED_COMMANDS[name]


def command_canon_label(name: str) -> str:
    specs = _agent_spec_dir()
    if specs is not None and (specs / f"{name}.md").exists():
        return f"pmo-roadmap/agent/{name}.md"
    return f"dw_pmo.riderdocs embedded spec for {name}"


def _command_targets(root: Path) -> list[tuple[Path, str, str]]:
    """(rendered path, expected content, canon label) for every
    command-copy directory that exists in this repo."""
    targets: list[tuple[Path, str, str]] = []
    for reldir in COMMAND_TARGET_DIRS:
        directory = root / reldir
        if not directory.is_dir():
            continue
        for name in COMMAND_NAMES:
            targets.append(
                (directory / f"{name}.md", command_spec(name), command_canon_label(name))
            )
    return targets


def _doc_targets(root: Path) -> list[Path]:
    return [root / name for name in ("CLAUDE.md", "AGENTS.md") if (root / name).exists()]


def write_rider_docs(root: Path) -> list[tuple[Path, str]]:
    """Regenerate every rendered surface from canon. Returns
    (path, created|refreshed|unchanged) per target."""
    from .agentdocs import write_agent_docs

    actions: list[tuple[Path, str]] = []
    for path, expected, _canon in _command_targets(root):
        if not path.exists():
            write_text(path, expected)
            actions.append((path, "created"))
        elif read_text(path) != expected:
            write_text(path, expected)
            actions.append((path, "refreshed"))
        else:
            actions.append((path, "unchanged"))
    doc_targets = _doc_targets(root) or [None]
    for target in doc_targets:
        path, action = write_agent_docs(root, target)
        actions.append((path, action))
    return actions


def rider_docs_issues(root: Path) -> list[str]:
    """Drift between rendered copies and canon, as `dw check` issue
    strings (empty when clean)."""
    issues: list[str] = []
    for path, expected, canon in _command_targets(root):
        rel = path.relative_to(root)
        if not path.exists():
            issues.append(f"{rel}: rendered command missing — run dw rider docs (canon: {canon})")
        elif read_text(path) != expected:
            issues.append(f"{rel}: drifted from {canon} — run dw rider docs")
    for target in _doc_targets(root):
        text = read_text(target)
        region = managed_region(text)
        if region is None:
            continue  # adoption state; dw doctor owns the "missing block" nudge
        expected_block = render_block_for(target)
        if text[region[0]:region[1]] != expected_block:
            variant = "agents" if agents_variant_for(target) else "claude"
            issues.append(
                f"{target.name}: managed block drifted from canon ({variant} variant) — run dw rider docs"
            )
    return issues
