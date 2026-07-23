# Evidence - WLA-26-08

- **Story:** WLA-26-08 - Grant continuous program authority explicitly
- **Status:** done
- **Date:** 2026-07-22

## Proof

### Finite consent and decider identity

- `program_run.py` adds a pure `delivery-workbench-program-start-plan@1` over
  the current program plan. It binds accountable operator/intent, exact scope
  and selection, policy/bundle/roadmap/repository hashes, worst-case envelope,
  explicit mode, complete finite budgets, capabilities, stop conditions,
  expiry, permanent exclusions, and all assigned seats while every work/write/
  grant effect remains false.
- The roster freezes stable seat address, assignment generation, logical
  profile, principal/workspace/session, harness and adapter version,
  router/provider, model vendor/family/id/revision-or-honest-alias,
  authentication domain, and capability fingerprint. A judge council records
  its preassigned `decider_seat`; a rule council records no fake agent decider,
  while an explicitly declared judge tie route records that seat only when the
  tie route is actually taken.
- Exact start re-plans inside one exclusive lock, refuses future/unissued,
  expired, stale, dirty, widened, divergent, or changed facts, and creates one
  unpredictable run id with immutable `plan.json`, `grant.json`, and
  authoritative `ledger.jsonl` only under `.git/pmo-programs/runs/`.
  Repeating the same start token is idempotent.

### Claims, replay, controls, and least authority

- Advisory grants contain no dispatch/mutation capability. Checkpointed and
  continuous grants share one machinery with named typed checkpoint ports.
  Capability prerequisites are closed and now include selection, verdict,
  council decision, and obligation record/materialization/disposition as
  separate bits rather than implications.
- Every claim is exclusive and idempotent, names one contracted category and
  exact subject, reserves phase/story/child/agent/provider/model/check/round/
  council/repair/verdict/obligation/integration/Git/nudge/byte/token/observed-
  cost budgets before work, and appends one closed hash-chained event. Replay
  validates sequence, timestamps, generations, deterministic claim ids,
  request hashes, scope, capability, typed port, and mechanically re-derived
  budget; a caller cannot make a forged preview authoritative by rehashing it.
- Child grants are unstored mechanical intersections of current program,
  assigned role, repository, roadmap, remaining budget, and expiry. Evidence,
  integration, certification, obligation materialization/disposition, Git, and
  roadmap rails remain non-delegable even when a child may dispatch or write.
- Completion previews bind one active claim and fresh observed repository and
  roadmap facts. Pause/resume/revoke/cancel previews bind action, approval,
  reason, ledger head, state and generation. Revoke/cancel increments the
  generation, expires typed requests, blocks future claims, and preserves
  bounded completion receipts; cancel additionally enumerates active claims to
  interrupt. Safety revoke remains available through policy/provider drift.
- Start and live-claim freshness cover program semantic/bundle, complete
  driver roster, repository/remote, and roadmap snapshot. Provider/model,
  adapter, auth-domain, policy, repository, or roadmap changes therefore cannot
  silently substitute the decider or any other assigned execution identity.

### Compatibility and surface boundary

- No mode is inferred. An absent program store is a healthy empty inventory;
  install/update, ordinary status/step/gate use, Program Studio, and Phase
  24/25 bounded runs create no program grant, observer, background process, or
  policy. Program Studio's existing Authority view continues to preview the
  optional mode/capability envelope without starting work.
- The source and vendored packages export identical start, replay, freshness,
  child-grant, claim, completion, control, and inventory APIs. WLA-26-09 owns
  conductor dispatch/recovery, WLA-26-10 owns exact integration and roadmap
  acts plus durable obligation disposition, and WLA-26-11 owns CLI/MCP/HTTP/
  Workbench live-control parity; none may introduce a second authority model.

### Verification summary

- Core suite: 433/433 on Python 3.14 and 433/433 on the Python 3.9 floor.
- Focused program-authority slice: 17/17 on both floors; broader program
  planner/workflow/organization/studio/authority/deliberation/verdict slice:
  89/89 on both floors.
- Fresh-wheel package smoke passed on Python 3.9, including source/vendored/
  installed program-authority exports, healthy empty inventory, and the prior
  bounded orchestration/outward-loop packaged exams.
- Canon lint, documentation links/anchors, executable snippets, agent-surface
  parity, update parity, compile checks, and diff checks passed.

### Captured run — 2026-07-23T00:30:44Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramRunAuthorityTest
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramRunAuthorityTest
pmo-roadmap/tests/canon-lint.sh
pmo-roadmap/tests/docs-lint.sh
pmo-roadmap/tests/docs-snippet-smoke.sh
pmo-roadmap/tests/agent-surface.sh
pmo-roadmap/update.sh . --check
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 65ed5450f00d33e7c0efec3e1fb43022c980a0e0

```text
----------------------------------------------------------------------
Ran 17 tests in 22.484s

OK
----------------------------------------------------------------------
Ran 17 tests in 19.895s

OK
canon-lint.sh: ok
docs-lint: ok (441 markdown files)
docs-lint.sh: ok (0s)
ok: CONTRIBUTING.md snippet 'contributor-setup' ran as printed
ok: CONTRIBUTING.md snippet 'contributor-gated-commit' ran as printed
ok: pmo-roadmap/README.md snippet 'install' ran as printed
ok: pmo-roadmap/README.md snippet 'update' ran as printed
ok: pmo-roadmap/README.md snippet 'new-project' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-three-step' ran as printed
ok: pmo-roadmap/README.md snippet 'intake-no-prompt' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-close-loop' ran as printed
docs-lint snippets: ok
docs-snippet-smoke.sh: ok
agent-surface.sh: ok
update.sh: up to date (vendored rails match source v1.14.0)
```

### Captured run — 2026-07-23T00:49:51Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramPlannerTest ProgramOrganizationTest ProgramWorkflowTest ProgramStudioTest ProgramRunAuthorityTest ProgramDeliberationTest ProgramVerdictTest
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramPlannerTest ProgramOrganizationTest ProgramWorkflowTest ProgramStudioTest ProgramRunAuthorityTest ProgramDeliberationTest ProgramVerdictTest
pmo-roadmap/tests/canon-lint.sh
pmo-roadmap/tests/docs-lint.sh
pmo-roadmap/tests/docs-snippet-smoke.sh
pmo-roadmap/tests/agent-surface.sh
pmo-roadmap/update.sh . --check
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 65ed5450f00d33e7c0efec3e1fb43022c980a0e0

```text
----------------------------------------------------------------------
Ran 89 tests in 25.048s

OK
----------------------------------------------------------------------
Ran 89 tests in 23.517s

OK
canon-lint.sh: ok
docs-lint: ok (441 markdown files)
docs-lint.sh: ok (0s)
ok: CONTRIBUTING.md snippet 'contributor-setup' ran as printed
ok: CONTRIBUTING.md snippet 'contributor-gated-commit' ran as printed
ok: pmo-roadmap/README.md snippet 'install' ran as printed
ok: pmo-roadmap/README.md snippet 'update' ran as printed
ok: pmo-roadmap/README.md snippet 'new-project' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-three-step' ran as printed
ok: pmo-roadmap/README.md snippet 'intake-no-prompt' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-close-loop' ran as printed
docs-lint snippets: ok
docs-snippet-smoke.sh: ok
agent-surface.sh: ok
update.sh: up to date (vendored rails match source v1.14.0)
```
