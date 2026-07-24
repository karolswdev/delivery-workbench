# Evidence - WLA-26-12

- **Story:** WLA-26-12 - Prove a fully autonomous multi-phase program
- **Status:** done
- **Date:** 2026-07-23

## Proof

### One grant, three stories, two phases

- `tests/autonomous-program-packaged-exam.py` is a standalone consumer exam. It
  receives only the wheel-installed `dw` entry point, creates fresh
  repositories, and imports runtime modules from that installed payload rather
  than the source tree.
- The green consumer authors a two-phase roadmap, reusable workflows,
  organization, rubrics, exact execution roster, and one program. Pure
  validation, simulation, graph/config round trips, and start planning explain
  the complete scope, finite envelope, resolved seats, capabilities, stops,
  and permanent exclusions before any grant or runtime store exists.
- One exact continuous grant then selects `AX-1-01`, `AX-1-02`, and `AX-2-01`
  in order. There is no checkpoint response, renewed grant, manual tick choice,
  or other human act after start.
- Story A is implemented in an isolated worktree, rejected by its preassigned
  independent verifier, repaired exactly once through the declared route, and
  passed by a later fresh verdict.
- Story B runs a finite propose→critique→rebuttal council across architect,
  critic, and verifier seats. Its dissent remains in the issued decision, its
  declared authority resolves without self-selection, a non-blocking technical
  debt obligation remains durably open, and a distinct meta-verifier performs
  the full audit.
- The final story in Phase 1 passes a master-architect gate and advances the
  authoritative roadmap into Phase 2. Story C is then selected, delivered, and
  completed under the same grant; the next release-decision story is parked
  and outside the program scope, preserving the exclusion of merge, release,
  deploy, and publication authority.
- All three stories materialize canonical evidence, apply their exact binary
  candidate diff, receive objective and governed certification, pass the real
  gate and range verifier, create one trailered commit, and fast-forward push
  that commit to a local bare remote. The result is exactly three integrations,
  evidence acts, story completions, commits, and pushes, plus one Phase 1
  transition.

### Recovery is the same execution, not a second happy path

- The exam plants conductor crashes both before and after child dispatch,
  verdict issuance, debate rebuttal, council judgment, architect verdict, and
  scope-completion receipt boundaries. Replay reconciles the deterministic
  operation key and persisted receipt before planning another act.
- Every acceptance-critical delivery category is crashed after both its outward
  effect and its durable receipt: integration, evidence, story completion,
  phase advancement, commit, and push are included. The remote is also moved
  deliberately before one push to prove divergence refusal before the exact
  lease is restored.
- Final replay reports nine conductor crashes and eighteen delivery crash
  recoveries with one repair, three commits, three pushes, two architect gates,
  one meta-audit, and no duplicate agent/check/round/verdict/evidence/status/
  integration/commit/push act.
- The verified program ledger and the canonical SSE replay contain the same
  203 ordered events. Cursor resume returns the exact suffix and an
  authority-free stream request refuses.

### Complete refusal matrix

The installed payload proves these failures without unintended delivery:

- unbounded workflow loop;
- self-verifier/impossible separation, impossible quorum, blocked agent, and
  unknown agent profile;
- decider self-selection and undeclared provider fallback;
- missing or changed model fingerprint;
- forged mechanical fact, stale verdict, and failed/dissenting verdict;
- blocking obligation and architect veto;
- no grant, missing capability, revoked grant, and exhausted story, phase,
  round, integration, or other required budget;
- stale roadmap, dirty repository, divergent remote, and authority-free stream.

The red authority and architect-veto specimens use separate cloned consumers,
so their deliberate corruption, exhaustion, and revocation cannot be hidden by
the green run.

### Canonical surfaces and visible organization

- CLI JSON, MCP `structuredContent`, HTTP `data`, Workbench bootstrap, and SSE
  derive from one canonical program view at the same ledger head. Tail/cursor
  payloads match byte-for-byte after normalization.
- The Workbench browser smoke now renders 60 desktop/mobile views. In addition
  to the existing Program Studio scenarios, a real conductor-built
  council-certified program ledger displays dissent, meta-audit, and its
  carried obligation alongside real active and revoked program states.
- Installed-wheel package smoke invokes the autonomous exam after the Phase
  22/23 guided and deliberate-step loops and the Phase 24/25 exit exams. A
  failure of the multi-phase proof therefore fails distribution validation.

### Separate no-program consumer

- The same installed wheel creates a second ordinary repository with no
  program, workflow, organization, or rubric policy.
- Ordinary `status`, `next`, `step`, `gate`, Workbench project reads, and pure
  bounded-orchestration simulation remain available.
- Program inventory is a healthy empty document. There is no program store,
  grant, run, program process, observer, stream, poller, notification store,
  notification, background network call, setup requirement, or default route
  change. Program Studio reports `#/` as the default front door.

### Honest provider and environment claims

- The governed roster resolves one group through the shipped `claude-exec`
  contract with Anthropic/Claude/Sonnet-like metadata and another through the
  shipped `pi-exec` contract with OpenRouter/Moonshot/Kimi-like metadata.
  Deterministic `ProgramFixtureDriver` instances are injected behind both
  registered adapter names. No credential or network access is used.
- This proves exact roster, adapter, provider/model/auth fingerprint,
  independence, scheduling, and receipt binding. It does **not** claim that
  variable live Claude or Kimi output passed the autonomous program.
- No explicit authenticated live-agent run was requested, so the optional live
  specimen is recorded as `not-run`, not passed.
- Homebrew is `not-applicable` in this wheel exam. The formula/environment lane
  remains owned by clean-machine macOS CI; no installed operator package is
  removed or simulated.
- The local Homebrew check found an existing operator installation of
  `delivery-workbench`, so the destructive install/uninstall smoke was
  deliberately not run. This is an environment abstention, not a pass; the
  operator installation was left untouched.

### Product finding captured as a regression

The first full exam exposed a real isolated-worktree defect: plain
`git status --porcelain -z` collapsed a nested untracked candidate to its
directory (`src/`), while the binary diff correctly named the file. Exact
allowed-path comparison therefore rejected valid work. The driver now requests
`--untracked-files=all`, and
`OrchestrationDriverTest.test_git_diff_artifact_keeps_exact_nested_untracked_paths`
pins the file-level path and diff header. The exam does not paper over the
runtime boundary.

## Verification summary

- Autonomous fresh-wheel exam: complete, three stories/two phases, one repair,
  one dissent-preserving council decision, one meta-audit, two architect gates,
  three commits, three pushes, nine conductor crashes, eighteen delivery
  crashes, and 203 ledger/SSE events.
- Focused exact nested-untracked-path regression: passed.
- The full dual-Python, fresh-wheel package, 60-render Workbench, documentation,
  canon, rider, vendoring, shell, roadmap, range, and history closeout matrix is
  captured below.

## Captured validation - 2026-07-23

```text
$ /usr/bin/python3 pmo-roadmap/tests/autonomous-program-packaged-exam.py \
    --dw /tmp/dw-exam-dev.WJ16nD/app/bin/dw
state=complete
selected_phases=[1, 2]
selected_stories=[AX-1-01, AX-1-02, AX-2-01]
repair_rounds=1 council_dissent_preserved=true
meta_audits=1 architect_gates=2
commits=3 pushes=3
conductor_crashes=9 delivery_crashes=18
ledger_events=203 stream_events=203
surfaces=[CLI, MCP, HTTP, Workbench, SSE]
optional_live_specimen=not-run
```

```text
$ python3 pmo-roadmap/tests/dw-core-tests.py -q
Ran 473 tests in 841.385s
OK

$ /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
Ran 473 tests in 791.076s
OK

$ PMO_PACKAGE_PYTHON=/usr/bin/python3 \
    pmo-roadmap/tests/package-smoke.sh
package-smoke.sh: building with: /usr/bin/python3 (Python 3.9.6)
package-smoke.sh: built delivery_workbench-1.14.0-py3-none-any.whl and
delivery_workbench-1.14.0.tar.gz
guided-status-loop.sh: ok
deliberate-step-loop.sh: ok
packaged multi-agent orchestration: duplicate_restarts=0, verify_all=ok
packaged outward exam: duplicate_starts=0, duplicate_nudges=0
packaged autonomous exam: state=complete, phases=2, stories=3,
repair_rounds=1, commits=3, pushes=3, conductor_crashes=9,
delivery_crashes=18, ledger_events=203, stream_events=203
package-smoke.sh: ok
```

```text
$ pmo-roadmap/tests/workbench-ui-smoke.sh
workbench-ui-smoke.sh: ok (60 viewport renders: 23 data views + empty
Studio + program planning/active/certified/revoked + attention + ambiguity,
desktop+mobile)

$ pmo-roadmap/tests/workbench-explorer.sh
workbench-explorer.sh: ok

$ python3 pmo-roadmap/tests/telegram-interface-tests.py -q
Ran 152 tests in 12.189s
OK (skipped=9)

$ python3 pmo-roadmap/tests/telegram-fitness-tests.py -q
Ran 10 tests in 0.126s
OK
```

```text
$ pmo-roadmap/tests/mcp-server.sh
mcp-server.sh: ok

$ pmo-roadmap/tests/step-interop.sh
step-interop.sh: ok

$ pmo-roadmap/tests/orchestration-interop.sh
orchestration-interop.sh: ok

$ pmo-roadmap/tests/verify-range.sh
verify-range.sh: ok

$ python3 pmo-roadmap/bin/dw verify --all
dw verify: ok (161 commits verified, 17 pre-epoch skipped)
```

```text
$ pmo-roadmap/tests/docs-lint.sh
docs-lint: ok (447 markdown files)
docs-lint.sh: ok

$ pmo-roadmap/tests/canon-lint.sh
canon-lint.sh: ok

$ pmo-roadmap/tests/docs-snippet-smoke.sh
docs-snippet-smoke.sh: ok

$ pmo-roadmap/tests/agent-surface.sh
agent-surface.sh: ok

$ pmo-roadmap/tests/gate-parity.sh
gate-parity.sh: ok

$ pmo-roadmap/tests/roadmap-cli.sh
roadmap-cli.sh: ok

$ pmo-roadmap/tests/contributor-flow.sh
contributor-flow.sh: ok

$ pmo-roadmap/tests/work-log-mvp.sh
work-log-mvp.sh: ok

$ pmo-roadmap/tests/upgrade-path.sh
upgrade-path.sh: ok

$ .githooks/dw check work-log-automation
dw check: ok

$ .githooks/dw rider docs --check
dw rider docs: all rendered surfaces match canon

$ pmo-roadmap/update.sh . --check
update.sh: up to date (vendored rails match source v1.14.0)

$ shellcheck -e SC2317 <the exact validation.yml shell-file set>
(no output)

$ git diff --check
(no output)

$ brew list --formula delivery-workbench
Homebrew abstention: operator formula already installed; smoke not run and
installation left untouched.
```
