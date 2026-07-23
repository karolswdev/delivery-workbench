# Evidence - WLA-26-10

- **Story:** WLA-26-10 - Integrate work and advance exact roadmap rails
- **Status:** done
- **Date:** 2026-07-23

## Proof

### One exact delivery protocol over the program ledger

- `program_delivery.py` adds a pure
  `delivery-workbench-program-delivery-preview@1`, immutable
  `delivery-workbench-program-delivery-plan@1`, ledger-bound
  `delivery-workbench-program-delivery-receipt@1`, and replay/tick/supervise
  functions. It composes the existing Phase 26 grant, claim, and hash-chained
  ledger; it does not add an authority store.
- Preview binds the exact program/grant/ledger head and claim, current
  proof/verdict/decision/obligation set, story and phase, candidate artifact,
  repository HEAD/index/worktree/result tree, evidence, contract, commit
  message, optional remote/ref/URL/head, requested acts, capabilities, budgets,
  and dependencies. It is pure: applicable or refusing previews create no
  program, Git, contract, roadmap, or remote state.
- Start independently re-previews under the program lock and freezes the exact
  plan. Each tick replays immutable receipts, rechecks standing authority and
  freshness, reserves at most one dependency-ready claim, reconciles an
  already-observed effect before retry, performs one fixed effect, records one
  receipt, and stops. Supervision only repeats that tick inside finite limits.
- Evidence, integration, contract generation, objective certification,
  governed certification, commit, push, story completion, phase advancement,
  next-story start, obligation materialization, and obligation disposition
  remain distinct capabilities, claim categories, operations, and receipts. A
  green workflow result never grants a delivery act by implication.

### Exact candidate tree, proof, contract, and commit

- The adapter writes the candidate artifact only to temporary storage and uses
  temporary Git object/index stores to calculate the exact base-to-result tree
  before touching the repository. Apply uses fixed
  `git apply --index --binary`, allowed-path validation, and expected base,
  artifact, index, worktree, and result-tree hashes. It has no three-way,
  conflict-resolution, merge, rebase, arbitrary command, or shell route.
- Preview requires a fresh closed mechanical program check and every declared
  governed verdict, meta-audit, architect gate, and decision authority needed
  by the binding. Failed, pending, dissenting, stale, tampered, manual-only,
  exhausted, revoked, under-capable, dirty, or divergent state refuses before
  partial advancement.
- Evidence and roadmap content are generated through canonical planning cores
  with deterministic evidence/summary dates. `plan_phase_advance` validates
  the current status pointer, completed story set, phase dependencies and next
  phase, then returns one guarded phase-summary, pointer, and header plan.
- Contract generation reads the complete staged candidate tree. Every
  objective box must map to current mechanical proof or an explicitly
  authorized governed verdict; the checked lines and archive record exact
  program/grant/plan/proof provenance and state that no human attestation is
  represented.
- Commit runs normal `git commit`, the real Delivery Workbench gate and hooks,
  and one-commit `run_verify`; there is no `--no-verify` route. Replay
  reconciles the contract archive, exact parent/tree/message and resulting
  commit before retry, preventing a duplicate archive or commit.

### Fast-forward push and canonical roadmap advancement

- Push is optional and separately granted. Preview binds one exact tracking
  remote, URL fingerprint, branch/ref, local head, and observed remote head.
  Apply resolves and re-observes that same remote, requires the candidate
  commit to be a fast-forward descendant, pushes the exact ref without force,
  verifies the outward head, and rebinds the local tracking fact.
- A changed URL, branch, remote head, local parent/tree, rewritten history,
  missing tracking ref, non-fast-forward relation, or network observation
  failure refuses. Force push, merge, release, deployment, and publication are
  impossible.
- Story evidence/status, phase close/current transition, and next-story start
  use canonical guarded roadmap mutation plans. A two-story fixture performs
  exactly two commits and one phase transition, leaving one evidence block,
  status flip, phase summary, pointer update, and next-story start for each
  intended act.

### Durable obligation handling and crash recovery

- Any open blocking council obligation refuses story or phase advancement.
  Non-blocking backlog, technical-debt, risk, research, and follow-up items
  remain ledger-visible without forcing roadmap mutation.
- `build_program_obligation_materialization_preview` plus apply may create one
  traced roadmap story only with separate roadmap-write authority. Stable
  source decision/obligation identifiers and canonical story-create planning
  deduplicate retries and repeated requests.
- `build_program_obligation_disposition_preview` plus apply records completion,
  supersession, escalation, or an exact accountable waiver only with the
  matching capability/authority. The original obligation and source decision
  remain immutable and linked from every disposition receipt.
- Fixture crashes after first-story outward effects and second-story receipts
  reconcile to the same evidence, integration, contract archive, commit,
  remote ref, story state, phase transition, and next-story start. Separate
  obligation crashes recover without duplicate stories or dispositions.
- Red paths include dirty and tampered candidates, missing objective
  capability, open blocking debt, hook failure, planted remote divergence,
  duplicate materialization, unauthorized waiver, and external repair before
  safe replay. None exposes a bypass or force path.

### Compatibility, packaging, and documentation

- No-program vanilla use and Phase 24/25 bounded runs keep their existing
  schemas, grants, commands, defaults, and absence of ambient runtime state.
  The delivery adapter is an embedded shared-core API; WLA-26-11 still owns
  CLI/MCP/HTTP/Workbench public program operations and the control room.
- Source and vendored packages are byte-synchronized, and package smoke asserts
  that the wheel contains `dw_pmo/program_delivery.py`.
- Root/framework READMEs, solution overview, architecture, interop inventory,
  autonomous-program contract, Unreleased changelog, status, handover, and
  story evidence describe the delivery authority/recovery boundary and the
  remaining WLA-26-11/12 work.

## Verification summary

- `ProgramDeliveryTest`: 6/6 on Python 3.14 and 6/6 on the Python 3.9 floor.
- Full core suite: 464/464 on Python 3.14 and 464/464 on Python 3.9.
- The two-story/local-remote specimen itself runs `dw check` and
  `run_verify --all` after recovery and exact phase advancement.
- Fresh-wheel packaging passed on Python 3.9: sdist and wheel build/install,
  packaged guided and deliberate-step loops, multi-agent orchestration with
  zero duplicate restarts, and outward-loop orchestration with zero duplicate
  starts/nudges.
- Python compilation on both floors, canon lint, all Markdown, executable
  documentation snippets, agent surfaces, roadmap validation, rendered rider,
  source/vendored update parity, and diff checks passed.

## Captured validation - 2026-07-23

```text
$ python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramDeliveryTest
Ran 6 tests in 159.977s
OK

$ /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramDeliveryTest
Ran 6 tests in 148.752s
OK

$ python3 pmo-roadmap/tests/dw-core-tests.py -q
Ran 464 tests in 804.517s
OK

$ /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
Ran 464 tests in 711.352s
OK

$ pmo-roadmap/tests/package-smoke.sh
package-smoke.sh: built delivery_workbench-1.14.0-py3-none-any.whl
package-smoke.sh: built delivery_workbench-1.14.0.tar.gz
guided-status-loop.sh: ok
deliberate-step-loop.sh: ok
packaged multi-agent orchestration: duplicate_restarts=0, verify_all=ok
packaged outward exam: duplicate_starts=0, duplicate_nudges=0
package-smoke.sh: ok

$ pmo-roadmap/tests/canon-lint.sh
canon-lint.sh: ok

$ pmo-roadmap/tests/docs-lint.sh
docs-lint: ok (444 markdown files)
docs-lint.sh: ok

$ pmo-roadmap/tests/docs-snippet-smoke.sh
docs-snippet-smoke.sh: ok

$ pmo-roadmap/tests/agent-surface.sh
agent-surface.sh: ok

$ .githooks/dw check work-log-automation
dw check: ok

$ .githooks/dw rider docs --check
dw rider docs: all rendered surfaces match canon

$ pmo-roadmap/update.sh . --check
update.sh: up to date (vendored rails match source v1.14.0)

$ python3 -m compileall -q pmo-roadmap/lib/dw_pmo .githooks/dw_pmo
(no output)

$ /usr/bin/python3 -m compileall -q \
    pmo-roadmap/lib/dw_pmo .githooks/dw_pmo
(no output)

$ git diff --check
(no output)
```
