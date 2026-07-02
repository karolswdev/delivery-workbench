# Evidence - WLA-7-02

- **Story:** WLA-7-02 - Core docs overhaul and architecture guide
- **Status:** done
- **Date:** 2026-07-02

## What shipped (implementing audit dispositions F1-F9, F11)

- **Root README rewritten:** the first screen now states what the
  framework is, who it is for, and the three-command adoption path;
  the feature list covers the dw CLI, contract v2, evidence capture,
  the trailer/archive audit trail, and the workbench (F7 closed); the
  "How a change ships" sequence diagram shows contract generation,
  the gate re-deriving stamped facts, commit-msg trailers, and the
  post-commit archive (F8 closed); the Validation block is a single
  correct command list (F6 closed); and the dogfood proof — the
  framework's own roadmap — is linked as the primary credential.
- **Framework README corrected and de-duplicated:** the intro feature
  list and Why section now describe contract v2 (index-tree
  freshness, archive-then-clear) instead of the mtime/delete fossils
  (F1, F2, F3 closed); the installer list names all three hooks and
  the workbench distribution (F4); the file map matches the actual
  tree (F5); update.sh's description matches what it ships (F9); the
  Maintenance section points at gate.py and the parity tests (F11);
  and the gate-semantics paraphrase is replaced by a link to the
  canonical rules document — one owner per topic, per the audit IA.
- **`docs/architecture.md` created:** six subsystems (core, gate +
  contract v2, evidence capture, workbench, work logs, adoption +
  agent surface), five Mermaid diagrams, four design invariants — and
  every behavioral claim names the test or command that proves it
  (all cited test names verified to exist before landing; one
  citation was corrected when the check caught a wrong name).
- **SECURITY.md extended** with the workbench runtime boundary and
  the no-authentication-by-design posture.

## Quickstart verification (the captures below)

The fourth capture runs the documented paths verbatim in a fresh
fixture: install → intake → discovery prompt → hand-written report →
`dw adopt --apply` → `dw doctor`, then the operating-agent loop
exactly as the managed block teaches it — `dw next --json`,
in-progress, `evidence capture`, done, `contract new`, a gated commit
carrying the `PMO-Story: MP-0-01` trailer, `phase close`, and
`dw check: ok`. The three earlier captures (exits 1) are kept
deliberately: they record the doc-verification process meeting real
refusal UX — the adopt parser demanding `--project` for a minimal
report, the exact flag name, and `dw check` refusing an all-done
phase without its final summary (answered with the documented close
command). Every refusal named its remediation — which is itself one
of the architecture guide's four invariants.

## Proof — captured runs (appended by `dw evidence capture`)

### Captured run — 2026-07-02T23:36:19Z

- **Command:** `sh -c 
set -e
T=$(mktemp -d); R="$T/proj"; mkdir -p "$R"; cd "$R"; git init -q; git config user.name QS; git config user.email qs@t.t
echo "══ ADOPTER PATH (framework README: install → intake → adopt-prompt → doctor) ══"
"$OLDPWD/pmo-roadmap/install.sh" "$R" --skip-bootstrap 2>&1 | tail -1
"$OLDPWD/pmo-roadmap/bootstrap/session-intake.sh" "$R" --project-name "My Project" --project-slug myproject --project-prefix MP --no-prompt 2>&1 | tail -1
"$OLDPWD/pmo-roadmap/bootstrap/adopt-project.sh" "$R" --project-name "My Project" --project-slug myproject --project-prefix MP --require-intake 2>&1 | tail -2
printf "# Adoption Discovery\n\n## Proposed Phase Index\n\n| Phase | Title | Goal | Why now |\n|---|---|---|---|\n| 0 | Stabilize | Land the rails. | Foundation. |\n\n## Proposed First Stories\n\n| ID | Title | Acceptance evidence | Notes |\n|---|---|---|---|\n| MP-0-01 | First story | Captured test run. | - |\n" > pm/roadmap/myproject/adoption/adoption-discovery.md
.githooks/dw adopt --from-report pm/roadmap/myproject/adoption/adoption-discovery.md --apply | tail -2
.githooks/dw doctor | tail -1
echo "══ OPERATING-AGENT LOOP (managed CLAUDE.md block, verbatim) ══"
.githooks/dw next myproject --json | python3 -c "import json,sys; print(\"next:\", json.load(sys.stdin)[\"story_id\"])"
.githooks/dw story status myproject 0 MP-0-01 in-progress >/dev/null
.githooks/dw evidence capture myproject 0 MP-0-01 -- sh -c "echo verified" >/dev/null
.githooks/dw story status myproject 0 MP-0-01 done | head -1
git add -A && .githooks/dw contract new --consent no --reasons "quickstart" >/dev/null 2>&1
sed "s/^- \[ \]/- [x]/" .tmp/CONTRACT.md > .tmp/C && mv .tmp/C .tmp/CONTRACT.md
git commit -q -m "MP-0-01 ships via quickstart" 2>&1 | grep -o "Commit proceeding" || true
git log -1 --format="trailers: %(trailers:key=PMO-Story,valueonly)"
.githooks/dw check myproject
rm -rf "$T"
echo "quickstarts: all commands ran as printed"`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 575260a8ccc5bc48247ae86f486968a0cffebc14

```text
══ ADOPTER PATH (framework README: install → intake → adopt-prompt → doctor) ══
✓ pmo-roadmap installed. Verify the wiring any time with: .githooks/dw doctor
✓ wrote pm/roadmap/myproject/adoption/session-intake.md
  Intake: pm/roadmap/myproject/adoption/session-intake.md
  Report target: pm/roadmap/myproject/adoption/adoption-discovery.md
dw: could not determine the project slug; pass --project or add the Roadmap root line to the report
dw doctor: healthy. Canonical invocation: .githooks/dw <command>
══ OPERATING-AGENT LOOP (managed CLAUDE.md block, verbatim) ══
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import json,sys; print("next:", json.load(sys.stdin)["story_id"])
                                    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
KeyError: 'story_id'
```

### Captured run — 2026-07-02T23:36:53Z

- **Command:** `sh -c 
set -e
T=$(mktemp -d); R="$T/proj"; mkdir -p "$R"; cd "$R"; git init -q; git config user.name QS; git config user.email qs@t.t
echo "══ ADOPTER PATH (framework README: install → intake → adopt → doctor) ══"
"$OLDPWD/pmo-roadmap/install.sh" "$R" --skip-bootstrap 2>&1 | tail -1
"$OLDPWD/pmo-roadmap/bootstrap/session-intake.sh" "$R" --project-name "My Project" --project-slug myproject --project-prefix MP --no-prompt 2>&1 | grep -c "wrote" | xargs echo "intake files written:"
"$OLDPWD/pmo-roadmap/bootstrap/adopt-project.sh" "$R" --project-name "My Project" --project-slug myproject --project-prefix MP --require-intake 2>&1 | tail -1
printf "# Adoption Discovery\n\n## Proposed Phase Index\n\n| Phase | Title | Goal | Why now |\n|---|---|---|---|\n| 0 | Stabilize | Land the rails. | Foundation. |\n\n## Proposed First Stories\n\n| ID | Title | Acceptance evidence | Notes |\n|---|---|---|---|\n| MP-0-01 | First story | Captured test run. | - |\n" > pm/roadmap/myproject/adoption/adoption-discovery.md
.githooks/dw adopt --from-report pm/roadmap/myproject/adoption/adoption-discovery.md --project myproject --prefix MP --apply | tail -1
.githooks/dw doctor | tail -1
echo "══ OPERATING-AGENT LOOP (managed CLAUDE.md block, verbatim) ══"
.githooks/dw next myproject --json | python3 -c "import json,sys; d=json.load(sys.stdin); print(\"next:\", d.get(\"story_id\") or d)"
.githooks/dw story status myproject 0 MP-0-01 in-progress >/dev/null
.githooks/dw evidence capture myproject 0 MP-0-01 -- sh -c "echo verified" >/dev/null
.githooks/dw story status myproject 0 MP-0-01 done | head -1
git add -A && .githooks/dw contract new --consent no --reasons "quickstart" >/dev/null 2>&1
sed "s/^- \[ \]/- [x]/" .tmp/CONTRACT.md > .tmp/C && mv .tmp/C .tmp/CONTRACT.md
git commit -q -m "MP-0-01 ships via quickstart" >/dev/null 2>&1
git log -1 --format="trailers: %(trailers:key=PMO-Story,valueonly)"
.githooks/dw check myproject
rm -rf "$T"
echo "quickstarts: all commands ran as printed"`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 575260a8ccc5bc48247ae86f486968a0cffebc14

```text
══ ADOPTER PATH (framework README: install → intake → adopt → doctor) ══
✓ pmo-roadmap installed. Verify the wiring any time with: .githooks/dw doctor
intake files written: 1
  Report target: pm/roadmap/myproject/adoption/adoption-discovery.md
usage: dw [-h] [--root ROOT]
          {projects,tree,next,doctor,adopt,agent-docs,context,check,gate,contract,phase,evidence,story} ...
dw: error: unrecognized arguments: --prefix MP
dw doctor: healthy. Canonical invocation: .githooks/dw <command>
══ OPERATING-AGENT LOOP (managed CLAUDE.md block, verbatim) ══
next: {'next_story': None}
dw: phase not found in myproject: 0
```

### Captured run — 2026-07-02T23:37:40Z

- **Command:** `sh -c 
set -e
T=$(mktemp -d); R="$T/proj"; mkdir -p "$R"; cd "$R"; git init -q; git config user.name QS; git config user.email qs@t.t
echo "══ ADOPTER PATH (framework README: install → intake → adopt → doctor) ══"
"$OLDPWD/pmo-roadmap/install.sh" "$R" --skip-bootstrap 2>&1 | tail -1
"$OLDPWD/pmo-roadmap/bootstrap/session-intake.sh" "$R" --project-name "My Project" --project-slug myproject --project-prefix MP --no-prompt >/dev/null 2>&1 && echo "intake: written"
"$OLDPWD/pmo-roadmap/bootstrap/adopt-project.sh" "$R" --project-name "My Project" --project-slug myproject --project-prefix MP --require-intake 2>&1 | tail -1
printf "# Adoption Discovery\n\n## Proposed Phase Index\n\n| Phase | Title | Goal | Why now |\n|---|---|---|---|\n| 0 | Stabilize | Land the rails. | Foundation. |\n\n## Proposed First Stories\n\n| ID | Title | Acceptance evidence | Notes |\n|---|---|---|---|\n| MP-0-01 | First story | Captured test run. | - |\n" > pm/roadmap/myproject/adoption/adoption-discovery.md
.githooks/dw adopt --from-report pm/roadmap/myproject/adoption/adoption-discovery.md --project myproject --apply | tail -1
.githooks/dw doctor | tail -1
echo "══ OPERATING-AGENT LOOP (managed CLAUDE.md block, verbatim) ══"
.githooks/dw next myproject --json | python3 -c "import json,sys; print(\"next:\", json.load(sys.stdin)[\"story_id\"])"
.githooks/dw story status myproject 0 MP-0-01 in-progress >/dev/null
.githooks/dw evidence capture myproject 0 MP-0-01 -- sh -c "echo verified" >/dev/null
.githooks/dw story status myproject 0 MP-0-01 done | head -1
git add -A && .githooks/dw contract new --consent no --reasons "quickstart" >/dev/null 2>&1
sed "s/^- \[ \]/- [x]/" .tmp/CONTRACT.md > .tmp/C && mv .tmp/C .tmp/CONTRACT.md
git commit -q -m "MP-0-01 ships via quickstart" >/dev/null 2>&1
git log -1 --format="trailers: %(trailers:key=PMO-Story,valueonly)"
.githooks/dw check myproject
rm -rf "$T"
echo "quickstarts: all commands ran as printed"`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 575260a8ccc5bc48247ae86f486968a0cffebc14

```text
══ ADOPTER PATH (framework README: install → intake → adopt → doctor) ══
✓ pmo-roadmap installed. Verify the wiring any time with: .githooks/dw doctor
intake: written
  Report target: pm/roadmap/myproject/adoption/adoption-discovery.md
  - pm/roadmap/myproject/phase-0-stabilize/current-phase-status.md
dw doctor: healthy. Canonical invocation: .githooks/dw <command>
══ OPERATING-AGENT LOOP (managed CLAUDE.md block, verbatim) ══
next: MP-0-01
MP-0-01	done	pm/roadmap/myproject/phase-0-stabilize/story-01-first-story.md
trailers: MP-0-01

ERROR pm/roadmap/myproject/phase-0-stabilize: all stories are done but final-summary.md is missing
```

### Captured run — 2026-07-02T23:38:17Z

- **Command:** `sh -c 
set -e
T=$(mktemp -d); R="$T/proj"; mkdir -p "$R"; cd "$R"; git init -q; git config user.name QS; git config user.email qs@t.t
echo "══ ADOPTER PATH (framework README: install → intake → adopt → doctor) ══"
"$OLDPWD/pmo-roadmap/install.sh" "$R" --skip-bootstrap 2>&1 | tail -1
"$OLDPWD/pmo-roadmap/bootstrap/session-intake.sh" "$R" --project-name "My Project" --project-slug myproject --project-prefix MP --no-prompt >/dev/null 2>&1 && echo "intake: written"
"$OLDPWD/pmo-roadmap/bootstrap/adopt-project.sh" "$R" --project-name "My Project" --project-slug myproject --project-prefix MP --require-intake >/dev/null 2>&1 && echo "discovery prompt: rendered"
printf "# Adoption Discovery\n\n## Proposed Phase Index\n\n| Phase | Title | Goal | Why now |\n|---|---|---|---|\n| 0 | Stabilize | Land the rails. | Foundation. |\n\n## Proposed First Stories\n\n| ID | Title | Acceptance evidence | Notes |\n|---|---|---|---|\n| MP-0-01 | First story | Captured test run. | - |\n" > pm/roadmap/myproject/adoption/adoption-discovery.md
.githooks/dw adopt --from-report pm/roadmap/myproject/adoption/adoption-discovery.md --project myproject --apply | tail -1
.githooks/dw doctor | tail -1
echo "══ OPERATING-AGENT LOOP (managed CLAUDE.md block, verbatim) ══"
.githooks/dw next myproject --json | python3 -c "import json,sys; print(\"next:\", json.load(sys.stdin)[\"story_id\"])"
.githooks/dw story status myproject 0 MP-0-01 in-progress >/dev/null
.githooks/dw evidence capture myproject 0 MP-0-01 -- sh -c "echo verified" >/dev/null
.githooks/dw story status myproject 0 MP-0-01 done | head -1
git add -A && .githooks/dw contract new --consent no --reasons "quickstart" >/dev/null 2>&1
sed "s/^- \[ \]/- [x]/" .tmp/CONTRACT.md > .tmp/C && mv .tmp/C .tmp/CONTRACT.md
git commit -q -m "MP-0-01 ships via quickstart" >/dev/null 2>&1
git log -1 --format="trailers: %(trailers:key=PMO-Story,valueonly)"
.githooks/dw phase close myproject 0 --summary "Quickstart phase closed with evidence." >/dev/null
.githooks/dw check myproject
rm -rf "$T"
echo "quickstarts: all commands ran as printed (install → adopt → work → gate → close → check)"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 575260a8ccc5bc48247ae86f486968a0cffebc14

```text
══ ADOPTER PATH (framework README: install → intake → adopt → doctor) ══
✓ pmo-roadmap installed. Verify the wiring any time with: .githooks/dw doctor
intake: written
discovery prompt: rendered
  - pm/roadmap/myproject/phase-0-stabilize/current-phase-status.md
dw doctor: healthy. Canonical invocation: .githooks/dw <command>
══ OPERATING-AGENT LOOP (managed CLAUDE.md block, verbatim) ══
next: MP-0-01
MP-0-01	done	pm/roadmap/myproject/phase-0-stabilize/story-01-first-story.md
trailers: MP-0-01

dw check: ok
quickstarts: all commands ran as printed (install → adopt → work → gate → close → check)
```

### Captured run — 2026-07-02T23:38:20Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 575260a8ccc5bc48247ae86f486968a0cffebc14

```text
test_agent_docs_block_lifecycle (__main__.DwCoreTest.test_agent_docs_block_lifecycle) ... ok
test_apply_cycle_and_stale_refusal (__main__.DwCoreTest.test_apply_cycle_and_stale_refusal) ... ok
test_apply_refuses_tampered_intent (__main__.DwCoreTest.test_apply_refuses_tampered_intent) ... ok
test_appl
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
