"""One canonical brief, many rendered surfaces (WLA-12-04).

The agent brief's canon lives in `agentdocs` (embedded block with a
template override); the command specs' canon lives here as
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

COMMAND_NAMES = ("dw-adopt", "dw-contract", "dw-next", "dw-scope", "dw-story-done")

# Directories (relative to the repo root) that hold rendered command
# copies when they exist. pmo-roadmap/agent/ is canon, not a target.
COMMAND_TARGET_DIRS = (".claude/commands", "plugin/commands")

_EMBEDDED_COMMANDS: dict[str, str] = {
    "dw-adopt": """---
description: Drive Delivery Workbench adoption for this repository (intake → discovery → roadmap).
---

Drive the Delivery Workbench adoption flow for this repository. Ask
the user for anything you cannot infer; do not fabricate intent.

## Delivery task

Establish the repository's delivery scope, current work, and first safe next
step. Report what will change before creating roadmap files.

## Technical details

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

## Delivery task

Review the intended files and their proof, then prepare the final commit check.
Never claim a rule passed without verifying it.

## Technical details

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
description: Start from the Delivery Workbench status briefing and pick up the next story.
---

Orient yourself in this repository's Delivery Workbench roadmap and
report what to work on next. Do not change anything yet.

## Delivery task

Report readiness, current work, any blocker, progress, and the source-backed
next step. Ask for a missing delivery-scope decision instead of guessing.

## Technical details

1. Run `.githooks/dw status --json` and read its JSON even if it exits 1.
   Exit 0 means `ready`; exit 1 means `attention`, which is valid data. If
   its action is blocking, report the named repair and stop. If it requires
   project selection, ask rather than guessing, then rerun with that slug.
2. Read `next_action`; this command is report-only, so do not execute a
   mutation yet. Use `.githooks/dw next --json` for the focused story object
   (exit 2 means nothing is actionable).
3. Run `.githooks/dw check` and `.githooks/dw context --compact`; read
   the current phase's `current-phase-status.md` "Where we are" section
   and the story file itself.
4. Report: the status verdict and recommendation, story ID and title, its acceptance criteria, any lint
   issues or warnings that affect it, and your plan to complete it.

If the user confirms, run `.githooks/dw step [project] --json` and review the
fresh lease. Require `applicable: true` and action `start-story`, then invoke
that document's exact `apply_command`; never reconstruct or modify its argv.
Stop after its one receipt and report the newly observed action. If the lease
is stale, manual, prohibited, or names anything else, do not apply it. Never
continue into a step loop.
""",
    "dw-scope": """---
description: Hold one scope conversation and draft one inert Delivery Workbench setup proposal.
---

Turn a rough idea or an existing project's next direction into one reviewable
setup proposal. This is a drafting conversation. It does not authorize or save
roadmap work.

## Choose one mode

Name the mode at the start and keep it for the whole conversation.

- **Build mode:** use this for a rails-ready repository and a new idea. Read the
  Delivery Workbench status first. If the rails are not healthy or the
  repository already has roadmap canon that would make this a maintenance
  change, explain the mismatch and stop rather than silently switching modes.
- **Maintain mode:** use this for an existing codebase or roadmap. Inspect it
  before asking the user to restate facts the repository already supplies. Use
  only the dedicated read surfaces `dw_status`, `dw_context`, `dw_board`, and
  `dw_story_show`, plus file reads. Read the project README, current phase,
  relevant stories, source canon, tests, and package or build files needed to
  understand the requested change. If a dedicated read surface is unavailable,
  ask the user for its output instead of replacing it with a shell command.

In either mode, read
`docs/setup-proposal.md`, `pmo-roadmap/lib/dw_pmo/setup_proposal.py`, and
`pmo-roadmap/templates/roadmap-builder.md` before drafting. Use read operations
only until the final proposal write.

## Hold one guided conversation

Start with one open question: what should this project make possible, and for
whom? Use the answer and repository facts to avoid a mechanical questionnaire.
Ask follow-ups together when they are related, but do not finish until these
minimum subjects are answered or recorded as unresolved:

1. Project identity: title, stable kebab-case slug, and uppercase story prefix.
2. Desired outcome: what changes for the user when the work succeeds.
3. Intended users: who uses or depends on the result.
4. First usable milestone: the smallest end-to-end result worth handing over.
5. Constraints: technical, product, time, compliance, compatibility, or
   operating limits.
6. Non-goals: nearby work that must stay out of scope.
7. Verification expectations: the checks and observable evidence that should
   prove the milestone works.
8. Desired autonomy level: how independently agents may work, what must be
   reviewed, and where the person expects a stop or approval.

Offer a recommendation when it helps the user react to something concrete, but
label it as a recommendation. Do not turn uncertainty into a fact. If two
reasonable interpretations would produce materially different phases, stories,
criteria, policy, or driver choices, ask. If the user cannot answer yet, add an
entry to `unresolved_questions`.

## Keep provenance honest

Every generated project identity, source intent, phase, story, scope item,
acceptance criterion, dependency, policy choice, policy document, driver
binding, and unresolved question must carry exactly one provenance object:

```json
{"kind":"user-answer","source_note":"The user named the first usable milestone."}
```

`kind` is exactly one of:

- `user-answer` for a value the person supplied;
- `repository-fact` for a value established by a named repository read; or
- `recommendation` for a value you proposed for review.

Use a specific `source_note`. Name the answer or repository path that supports
the item. A recommendation remains a recommendation even when it looks
obvious. An unresolved question is an item location, not a fourth provenance
kind; its provenance records where the uncertainty came from.

## Assemble the contracted proposal

Write exactly one `delivery-workbench-setup-proposal@1` object with these
closed fields:

```text
schema, state, project, source_intent, tracked_content, local_content,
unresolved_questions, starts_work, creates_grant, certifies, commits
```

Set `state` to `draft`. Set all four inertness fields to the JSON boolean
`false`.

Use these exact nested shapes:

```text
project = {slug, prefix, title, provenance}
source_intent = {idea, mode, provenance}
tracked_content = {roadmap, policy}
roadmap = {phases, exit_criteria}
phase = {number, title, goal, provenance, stories}
story = {id_sketch, title, problem, scope_in, scope_out,
         acceptance_criteria, dependencies, provenance}
text item = {text, provenance}
dependency = {id_sketch, provenance}
local_content = {driver_bindings}
driver binding = {adapter, model, provider, provenance}
unresolved question = {question, provenance}
provenance = {kind, source_note}
```

The roadmap needs at least one phase, one story in every phase, one acceptance
criterion in every story, and one roadmap exit criterion. Phase numbers must be
unique integers from 0 through 9999. Keep story `id_sketch` values stable within
the draft and use the selected project prefix. Lists may be empty only where the
contract permits it, such as story dependencies and scope lists.

Set `tracked_content.policy` to `null` unless the conversation has enough
information for one complete policy bundle. A non-null bundle has exactly
`program`, `workflows`, `organization`, `rubrics`, and `provenance`; each
wrapped document has exactly `document` and `provenance`. Do not invent a
partial policy to fill the field.

`local_content.driver_bindings` is an object keyed by logical profile name. It
may contain only non-secret adapter metadata. Never include credentials,
tokens, passwords, secrets, API keys, or a key whose name suggests one. An
empty object is valid.

Map the autonomy answer into concrete, traced scope, criteria, policy, or driver
choices only when the answer supports them. Otherwise add an unresolved
question. The proposal has no free-form autonomy field and its closed schema
must not be extended.

## Validate without acting

Validate the complete in-memory object against every closed field, bound,
identifier rule, provenance location, and inertness rule in
`setup_proposal.py`. Material ambiguity must be present in
`unresolved_questions`, not hidden in prose. Re-read the finished file and make
sure it is the same object you validated.

Before writing, read `.gitignore` and confirm that `.tmp/` is ignored. If it is
not ignored, report the blocker and do not edit `.gitignore` or write the
proposal. If it is ignored, the only write this skill may make is:

```text
.tmp/setup-proposal.json
```

Serialize as UTF-8 canonical JSON: object keys sorted recursively, compact
separators, Unicode preserved, finite JSON values only, and no trailing newline.
The serialization must match `canonical_json` from the contract module.

For a revision, start from the last validated proposal. Change only the sections
whose source answer or derived recommendation changed. Preserve every unaffected
JSON value exactly, keep list ordering deterministic, then serialize again with
the same canonical rules. Compare the canonical bytes of each unaffected
section before replacing the file. If an unaffected section changed, restore it
before writing. This makes one changed answer produce byte-stable unchanged
sections.

## Hard boundary

Do not create or edit any file outside `.tmp/setup-proposal.json`. Do not use a
shell or a general-purpose command runner. Never invoke `phase create`,
`story create`, `story status`, `setup apply`, `git commit`, a setup preview, or any
other mutation. Do not start a story, process, run, or program. Do not mint a
lease or grant. Do not certify anything. The finished JSON remains inert even
when it has no unresolved questions.

End every successful conversation with these exact three lines, unchanged:

```text
Review it in the Workbench under Roadmap changes (`#/edit`).
Next command: `dw setup preview .tmp/setup-proposal.json`
nothing has been saved
```
""",
    "dw-story-done": """---
description: Prove, flip, and ship the current story through the PMO gate.
---

Close out the story the user names (or the current in-progress story
from `.githooks/dw next`). Evidence first, then the flip, then the
gated commit.

## Delivery task

Prove the work, complete its roadmap state, review the final files, and commit
only the delivery that the saved proof supports.

## Technical details

1. Prove the work with real runs — for each documented verification
   command:
   `.githooks/dw evidence capture <project> <phase> <story> -- <command>`
   Nonzero exits are recorded honestly; fix and re-capture until the
   run that matters passes. Add narrative context to the evidence file
   around the captured blocks; screenshots/binaries go in `assets/`
   next to it.
2. Preview `.githooks/dw step [project] --json`; require a fresh,
   `applicable: true` `finish-story` lease for the intended story. Invoke only
   its exact `apply_command`, then stop. Never reconstruct the guarded status
   argv or continue automatically. A stale token or missing evidence refuses
   without starting the transition.
3. Update the phase's "Where we are" pickup snapshot and any canon doc
   the story touches — the gate requires master docs in the same
   commit.
4. Stage everything, then run /dw-contract (generate → verify → certify;
   use `--tests-capture` for the captured run from step 1).
5. Run `git commit` yourself with a clear message — `dw step` cannot commit.
   The gate verifies the flip ships
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
    for path, expected, _canon in _command_targets(root) + _codex_targets(root) + _pi_targets(root):
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
    hs = refresh_hs_context(root)
    if hs is not None:
        actions.append(hs)
    return actions


CODEX_SKILLS_DIR = ".codex/skills"


def _spec_parts(name: str) -> tuple[str, str]:
    """(description, body) parsed from a command spec's frontmatter."""
    text = command_spec(name)
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            header = text[4:end]
            body = text[end + 5 :].lstrip("\n")
            for line in header.splitlines():
                if line.startswith("description:"):
                    return line.split(":", 1)[1].strip(), body
            return "", body
    return "", text


def codex_skill(name: str) -> str:
    """One command spec rendered as a Codex skill (SKILL.md).

    Verified on codex-cli 0.142.4 (WLA-12-01 matrix): repo-level
    `.codex/skills/<name>/SKILL.md` is discovered by `codex exec`
    with no flags; `~/.codex/prompts` is not expanded there."""
    description, body = _spec_parts(name)
    return (
        f"---\nname: {name}\ndescription: {description}\n---\n\n{body}"
    )


def codex_mcp_snippet(root: Path) -> str:
    """The MCP registration for ~/.codex/config.toml — printed for
    the operator, never written into their home config (recorded
    decision, WLA-12-05)."""
    dw_mcp = (root / ".githooks" / "dw-mcp").resolve()
    return (
        "# Add the Delivery Workbench MCP server to Codex (global config):\n"
        f"#   codex mcp add delivery-workbench -- python3 {dw_mcp} --root {root.resolve()}\n"
        "# or paste into ~/.codex/config.toml:\n"
        "[mcp_servers.delivery-workbench]\n"
        'command = "python3"\n'
        f'args = ["{dw_mcp}", "--root", "{root.resolve()}"]\n'
    )


def install_codex_rider(root: Path) -> dict:
    """Wire the Codex rider into a rails repo, idempotently:
    AGENTS.md managed block (agents variant), the commands as
    repo-level Codex skills, and the MCP snippet (returned, not
    installed). Re-running changes nothing."""
    from .agentdocs import write_agent_docs

    actions: list[tuple[Path, str]] = []
    agents_path, action = write_agent_docs(root, root / "AGENTS.md")
    actions.append((agents_path, action))
    skills_root = root / CODEX_SKILLS_DIR
    for name in COMMAND_NAMES:
        directory = skills_root / name
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / "SKILL.md"
        expected = codex_skill(name)
        if not target.exists():
            write_text(target, expected)
            actions.append((target, "created"))
        elif read_text(target) != expected:
            write_text(target, expected)
            actions.append((target, "refreshed"))
        else:
            actions.append((target, "unchanged"))
    return {"actions": actions, "mcp_snippet": codex_mcp_snippet(root)}


PI_PROMPTS_DIR = ".pi/prompts"

# Strings that must never appear in pi-native rendered files: pi has
# no MCP by design and no Claude affordances; the purity check is
# mechanical, per the WLA-12-06 acceptance criteria.
PI_FORBIDDEN_FRAGMENTS = ("mcp", "MCP", ".claude", "Claude", ".mcp.json")


def pi_prompt(name: str) -> str:
    """One command spec rendered as a pi prompt template.

    pi's template format (frontmatter `description:` + body, filename
    becomes /name) is byte-identical to the command-spec format, so
    the rendering is the canon, verbatim — the minimalist surface
    needs no transformation at all."""
    return command_spec(name)


def pi_purity_violations(text: str) -> list[str]:
    return [frag for frag in PI_FORBIDDEN_FRAGMENTS if frag in text]


def install_pi_rider(root: Path) -> dict:
    """Wire the pi rider, idempotently: the shared AGENTS.md managed
    block (agents variant — one file serves every AGENTS.md-reading
    harness; the shared-file answer is recorded in docs/riders.md)
    and the commands as project prompt templates in
    .pi/prompts/ (pure CLI text, mechanically checked)."""
    from .agentdocs import write_agent_docs

    actions: list[tuple[Path, str]] = []
    agents_path, action = write_agent_docs(root, root / "AGENTS.md")
    actions.append((agents_path, action))
    prompts_root = root / PI_PROMPTS_DIR
    prompts_root.mkdir(parents=True, exist_ok=True)
    for name in COMMAND_NAMES:
        expected = pi_prompt(name)
        violations = pi_purity_violations(expected)
        if violations:
            raise ValueError(
                f"pi prompt {name} failed the purity check: {violations}"
            )
        target = prompts_root / f"{name}.md"
        if not target.exists():
            write_text(target, expected)
            actions.append((target, "created"))
        elif read_text(target) != expected:
            write_text(target, expected)
            actions.append((target, "refreshed"))
        else:
            actions.append((target, "unchanged"))
    return {"actions": actions}


def _pi_targets(root: Path) -> list[tuple[Path, str, str]]:
    """Rendered pi prompt templates come under the drift rule."""
    targets: list[tuple[Path, str, str]] = []
    prompts_root = root / PI_PROMPTS_DIR
    if not prompts_root.is_dir():
        return targets
    for name in COMMAND_NAMES:
        target = prompts_root / f"{name}.md"
        targets.append((target, pi_prompt(name), command_canon_label(name)))
    return targets


def _codex_targets(root: Path) -> list[tuple[Path, str, str]]:
    """Rendered Codex skills that exist come under the drift rule."""
    targets: list[tuple[Path, str, str]] = []
    skills_root = root / CODEX_SKILLS_DIR
    if not skills_root.is_dir():
        return targets
    for name in COMMAND_NAMES:
        target = skills_root / name / "SKILL.md"
        if target.parent.is_dir():
            targets.append((target, codex_skill(name), command_canon_label(name)))
    return targets


def rider_docs_issues(root: Path) -> list[str]:
    """Drift between rendered copies and canon, as `dw check` issue
    strings (empty when clean)."""
    issues: list[str] = []
    for path, expected, canon in _command_targets(root) + _codex_targets(root) + _pi_targets(root):
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

# ---------------------------------------------------------------------
# HoldSpeak Desk presence (WLA-12-07): a live-rendered roadmap block in
# .hs/context.md — the project-context directory HoldSpeak reads for
# dictation and project detection. Live state by definition, so it is
# deliberately NOT under the byte-drift rule: `dw rider docs` and
# `dw rider install holdspeak` refresh it; `dw doctor` notes staleness.

HS_DIR = ".hs"
HS_CONTEXT_FILE = "context.md"


def hs_state_block(root: Path) -> str:
    from .api import next_story
    from .parse import discover_projects
    from .validate import project_warnings

    lines = ["## Delivery Workbench roadmap state", ""]
    lines.append(
        "This block is rendered from the rails by `dw rider docs`; "
        "edit outside the markers only."
    )
    lines.append("")
    for project in discover_projects(root):
        found = next_story(project, root)
        warnings = project_warnings(project, root)
        lines.append(f"### {project.slug}")
        lines.append("")
        if found:
            lines.append(
                f"- Current phase: {found['phase']} ({found['phase_path']})"
            )
            lines.append(
                f"- Next story: {found['story_id']} — {found['title']} "
                f"[{found['status']}]"
            )
        else:
            lines.append("- Next story: nothing actionable")
        lines.append(f"- Open roadmap warnings: {len(warnings)}")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_hs_block(root: Path) -> str:
    from .agentdocs import BEGIN_MARKER, END_MARKER

    return f"{BEGIN_MARKER}\n\n{hs_state_block(root)}\n\n{END_MARKER}"


def refresh_hs_context(root: Path, *, create: bool = False) -> tuple[Path, str] | None:
    """Refresh (or with create=True, establish) the managed roadmap
    block in .hs/context.md, preserving operator content outside the
    markers. Returns (path, action) or None when absent and not
    creating."""
    from .agentdocs import managed_region

    target = root / HS_DIR / HS_CONTEXT_FILE
    if not target.exists() and not create:
        return None
    block = render_hs_block(root)
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        write_text(target, block + "\n")
        return target, "created"
    text = read_text(target)
    region = managed_region(text)
    if region is None:
        joined = (
            text.rstrip("\n") + "\n\n" + block + "\n" if text.strip() else block + "\n"
        )
        write_text(target, joined)
        return target, "added"
    if text[region[0]:region[1]] == block:
        return target, "unchanged"
    write_text(target, text[: region[0]] + block + text[region[1] :])
    return target, "refreshed"


def install_holdspeak_presence(root: Path) -> dict:
    result = refresh_hs_context(root, create=True)
    assert result is not None
    return {"actions": [result]}


# ---------------------------------------------------------------------
# Rider report (WLA-12-07): which surfaces are wired here, and are they
# healthy. Consumed by `dw doctor`; honest about what it cannot see.


def rider_report(root: Path) -> list[tuple[bool, str, str]]:
    """(ok, name, detail) per rider surface. Absent surfaces are ok
    ("not installed" is a state, not a failure); drifted ones are not."""
    import shutil as _shutil

    report: list[tuple[bool, str, str]] = []
    issues = rider_docs_issues(root)

    def surface(name: str, present: bool, prefixes: tuple[str, ...], extra: str = "") -> None:
        if not present:
            report.append((True, f"rider:{name}", "not installed (optional)"))
            return
        mine = [i for i in issues if any(i.startswith(p) for p in prefixes)]
        if mine:
            report.append((False, f"rider:{name}", f"drifted: {mine[0]}"))
        else:
            detail = "wired, matches canon"
            if extra:
                detail += f"; {extra}"
            report.append((True, f"rider:{name}", detail))

    surface(
        "claude",
        (root / ".claude" / "commands").is_dir(),
        (".claude/commands/", "CLAUDE.md:"),
    )
    surface(
        "codex",
        (root / CODEX_SKILLS_DIR).is_dir(),
        (".codex/skills/",),
        extra=(
            "codex CLI on PATH" if _shutil.which("codex") else "codex CLI not on PATH (cannot verify runtime)"
        ),
    )
    surface(
        "pi",
        (root / PI_PROMPTS_DIR).is_dir(),
        (".pi/prompts/",),
        extra=(
            "pi CLI on PATH" if _shutil.which("pi") else "pi CLI not on PATH (cannot verify runtime)"
        ),
    )

    # HoldSpeak: pack staleness is only checkable where the canonical
    # pack sources live (the framework repo / integrations dir).
    pack_src = root / "integrations" / "holdspeak"
    pack_dir = Path.home() / ".holdspeak" / "plugin_packs"
    if pack_src.is_dir():
        installed = []
        stale = []
        for pack in sorted(pack_src.glob("delivery_workbench*.py")):
            target = pack_dir / pack.name
            if not target.exists():
                continue
            installed.append(pack.name)
            if read_text(target) != read_text(pack):
                stale.append(pack.name)
        if not installed:
            report.append((True, "rider:holdspeak", "packs not installed on this desk (optional)"))
        elif stale:
            report.append(
                (False, "rider:holdspeak", f"installed pack stale vs repo: {', '.join(stale)} — re-copy to {pack_dir}")
            )
        else:
            report.append((True, "rider:holdspeak", f"packs installed and current: {', '.join(installed)}"))
    hs_target = root / HS_DIR / HS_CONTEXT_FILE
    if hs_target.exists():
        from .agentdocs import managed_region

        text = read_text(hs_target)
        region = managed_region(text)
        if region is not None and text[region[0]:region[1]] != render_hs_block(root):
            report.append(
                (True, "rider:hs-context", "roadmap block stale (live state moved) — run dw rider docs")
            )
        else:
            report.append((True, "rider:hs-context", ".hs/context.md roadmap block current"))
    return report
