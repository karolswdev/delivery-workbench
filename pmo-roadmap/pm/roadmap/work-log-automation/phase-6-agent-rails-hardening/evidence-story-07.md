# Evidence - WLA-6-07

- **Story:** WLA-6-07 - Harden onboarding and adoption bridge
- **Status:** done
- **Date:** 2026-07-02

## What shipped

- **`dw adopt --from-report`** (`dw_pmo/adopt.py`): parses the
  discovery report's Proposed Phase Index and Proposed First Stories
  tables (stabilized with a Title column and a machine-consumption note
  in the prompt template) into the same phase/story mutation plans the
  CLI uses. Preview by default — nothing written without `--apply` —
  and malformed tables (wrong column count, bad story IDs, stories
  referencing unknown phases, duplicate phase numbers) are refused with
  line-numbered errors, never a partial scaffold. The project slug and
  prefix come from the report itself (Roadmap root line, story IDs); a
  minimal project README is created when missing, with the current-phase
  pointer aimed at the first proposed phase.
- **Safe-by-default adoption docs.** Both READMEs now document the
  sandboxed agent modes as the happy path, frame `--dangerous` as the
  exception with its exact bypass flags named, and close the loop with
  the third command (`dw adopt` → `dw doctor` → `dw next`). Adoption is
  now genuinely three commands.
- **Injection-proof rendering.** `new-project.sh` and
  `adopt-project.sh` render templates with literal bash substitution
  instead of `sed` (a project named `A|B & C\D` renders byte-exact),
  and the rendered committed artifacts (discovery prompt, session
  intake) carry repo-relative paths only — no absolute machine paths.
- **Installer honesty.** `install.sh` refuses to take over a foreign
  `core.hooksPath` (husky et al) without `--force`, warns when
  `.git/hooks` contains active hooks that `.githooks` will disable,
  refuses to overwrite a non-framework `.githooks/pre-commit`, and the
  `.gitignore` idempotency check accepts common `.tmp` spellings;
  `update.sh` now keeps the entry present too.
- **Intake right-sized.** The interactive interview asks 4 core
  questions (goal, direction, constraints, handoff) by default;
  `--extended` restores the full 14 (the onboarding demo shim uses it,
  keeping the VHS tape sequence valid); `--list-questions` makes both
  sets testable; and an intake whose core answers are mostly blank gets
  a visible "mostly unanswered" note so discovery treats intent as
  unresolved instead of trusting an Enter-through.

## Acceptance proof

All CI-run in the extended `adoption-discovery.sh`: the three-command
adoption on a temp repo ending with `dw doctor` healthy and `dw check`
green; preview-writes-nothing and malformed-report refusal (line-numbered,
no partial scaffold); the hostile-name (`A|B & C\D`) install/scaffold/
render/check pass; foreign-hooksPath refusal and `--force` takeover;
active-`.git/hooks` warning; idempotent re-runs (single `.gitignore`
entry, single agent-docs block); question counts (4 core / 14 total);
banner present on blank intakes and absent on answered ones; and the
absolute-path absence assertions. Parser fixtures live in the unit
suite (52 tests). The first captured run below is the manual acceptance
item — a complete real adoption of a scratch clone, ending in
`dw doctor: healthy`, `dw check: ok`, and `dw next` returning the
scaffolded story.

## Proof — captured runs (appended by `dw evidence capture`)

### Captured run — 2026-07-02T17:39:29Z

- **Command:** `sh -c 
set -e
SCRATCH=$(mktemp -d /tmp/scratch-adoption.XXXXXX)
trap "rm -rf $SCRATCH" EXIT
git -C "$SCRATCH" init -q && git -C "$SCRATCH" config user.name demo && git -C "$SCRATCH" config user.email demo@example.test
mkdir -p "$SCRATCH/src"; echo "console.log(1)" > "$SCRATCH/src/index.js"; echo "{\"name\":\"scratch-app\"}" > "$SCRATCH/package.json"
git -C "$SCRATCH" add -A && git -C "$SCRATCH" commit -qm "existing project history"
echo "== command 1: install =="
pmo-roadmap/install.sh "$SCRATCH" --skip-bootstrap | grep -E "agent docs|doctor|✓ pmo" | head -3
echo "== command 2: intake + discovery prompt =="
pmo-roadmap/bootstrap/session-intake.sh "$SCRATCH" --project-slug scratch-app --project-prefix SA --goal "Adopt PMO rails" --direction "Keep behavior" --constraints "none" --handoff "next story pickable" --no-prompt >/dev/null
pmo-roadmap/bootstrap/adopt-project.sh "$SCRATCH" --project-slug scratch-app --project-prefix SA --require-intake | tail -2
cat > "$SCRATCH/pm/roadmap/scratch-app/adoption/adoption-discovery.md" <<EOF
- **Roadmap root:** \`pm/roadmap/scratch-app/\`

## Proposed Phase Index
| Phase | Title | Goal | Why now |
|---|---|---|---|
| 0 | Baseline | Prove the build | first |

## Proposed First Stories
| ID | Title | Acceptance evidence | Notes |
|---|---|---|---|
| SA-0-01 | Add a smoke test | test run output | - |
EOF
echo "== command 3: dw adopt (preview, then apply) =="
cd "$SCRATCH"
./.githooks/dw adopt --from-report pm/roadmap/scratch-app/adoption/adoption-discovery.md 2>/dev/null
./.githooks/dw adopt --from-report pm/roadmap/scratch-app/adoption/adoption-discovery.md --apply 2>/dev/null
echo "== verification =="
./.githooks/dw doctor | tail -2
./.githooks/dw check scratch-app
./.githooks/dw next scratch-app
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fb00a4b7a66645ad22f7836dffdee1cd01d10ac0

```text
== command 1: install ==
  ✓ agent docs block created in CLAUDE.md
✓ pmo-roadmap installed. Verify the wiring any time with: .githooks/dw doctor
== command 2: intake + discovery prompt ==
  Intake: pm/roadmap/scratch-app/adoption/session-intake.md
  Report target: pm/roadmap/scratch-app/adoption/adoption-discovery.md
== command 3: dw adopt (preview, then apply) ==
dw adopt preview for project 'scratch-app' (nothing written):
  - create pm/roadmap/scratch-app/README.md (minimal project README)
  - create pm-phase phase-0-baseline/ (goal: Prove the build)
  - create story SA-0-01 — Add a smoke test
dw adopt applied for project 'scratch-app':
  - pm/roadmap/scratch-app/phase-0-baseline/current-phase-status.md
  - pm/roadmap/scratch-app/README.md
  - pm/roadmap/scratch-app/phase-0-baseline/story-01-add-a-smoke-test.md
  - pm/roadmap/scratch-app/phase-0-baseline/current-phase-status.md
== verification ==

dw doctor: healthy. Canonical invocation: .githooks/dw <command>
dw check: ok
SA-0-01	backlog	phase-0-baseline	Add a smoke test
```

### Captured run — 2026-07-02T17:39:40Z

- **Command:** `pmo-roadmap/tests/adoption-discovery.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fb00a4b7a66645ad22f7836dffdee1cd01d10ac0

```text
adoption-discovery.sh: ok
```

### Captured run — 2026-07-02T17:39:44Z

- **Command:** `pmo-roadmap/tests/canon-lint.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fb00a4b7a66645ad22f7836dffdee1cd01d10ac0

```text
canon-lint.sh: ok
```
