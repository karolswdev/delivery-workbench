# Evidence - WLA-27-06

- **Story:** WLA-27-06 - Make live delivery explain progress and next steps
- **Status:** done
- **Date:** 2026-07-24

## One source-backed live-progress model

The new pure
[`live_progress.py`](../../../../lib/dw_pmo/live_progress.py) projection
attaches `delivery-workbench-live-progress@1` to both bounded-run and program
views. CLI, MCP, HTTP, SSE, and Workbench therefore receive the same
source-traceable document instead of rebuilding progress in each renderer.

The document directly answers:

1. what is being delivered;
2. who is doing and reviewing it;
3. what passed;
4. what is blocked;
5. who needs to decide;
6. what permission and measured cost remain; and
7. what happens next.

Every answer names its canonical source. The projection reports false for
starting work, writing events, selecting next work, deciding recovery, and
granting authority.

## Honest state, proof, and next work

The application view groups exact run and program facts into understandable
active, waiting, review, repair, blocked, stopped, revoked, recovering, and
complete states. Exact story, run, lane, node, request, receipt, decision,
artifact, and event identities remain available under **Technical details**.
A dependency wait is not presented as a blocker unless canonical state records
one.

Mechanical checks, agent judgment, dissent, repair outcomes, and final governed
decisions are separate proof classes. No class is allowed to imply another.
Counts retain declared denominators, and incomparable units are not summed.
Money cost is shown as measured only when canonical counters record it;
otherwise the view says it is not recorded.

There is one displayed next step. Terminal state, outstanding human requests,
active reconciliation, saved repair routes, and canonical conductor/program
frontiers determine it. The browser neither chooses an alternative nor creates
authority.

## Readable activity and exact inspection

The default Workbench control room now leads with **Live delivery**, the seven
answers, the canonical next step, grouped work, team and review proof,
remaining limits, readable activity, and recovery truth. A toolbar button opens
the exact technical view on demand.

Readable activity groups related work and outcomes but does not alter the
ledger. Exact state, ordered hash-linked events, limits, controls, routes,
sessions, artifacts, requests, notification receipts, and provenance remain
in the existing technical panels. The source and vendored Workbench renderers
are byte-identical.

## Disconnect and crash recovery

SSE connection state is explicit. A disconnect retains the last verified
projection and says that completed work remains recorded. Manual refresh
preserves that view if the request fails. Recovery distinguishes replayed
history from active reconciliation, names preserved completed work and active
technical references, and explains the ledger/receipt duplicate protection.
It never claims that delivery was lost or restarted without canonical proof.

The focused two-story recovery test crashes after each external effect, renders
the recovering state before continuation, and then proves completion without
duplicate delivery. The installed autonomous exam independently passes
eighteen delivery-boundary crashes and nine conductor crashes with zero
duplicate restarts.

## Device and journey proof

The browser harness renders 76 canonical viewports at 1440x900 and 390x844.
New wide and narrow captures cover ordinary active, repair, terminal, stale,
and exact technical states plus the program technical state. Manual inspection
confirmed that:

- dependency waits do not appear as blockers;
- repair asks for its saved outcome;
- terminal work does not invent another bounded job;
- stale mode preserves verified history and gives one refresh path; and
- technical mode opens exact state before the ordinary summary.

The usability inventory now contains seventeen reachable states. All thirteen
journeys, six red fixtures, ten product concepts, eighteen surfaces, eighteen
reserved terms, and twelve language fixtures pass their executable contracts.

## Regression and distribution proof

- `python3 pmo-roadmap/tests/dw-core-tests.py` passes all 485 tests in
  996.443 seconds.
- Four focused projection, run-surface, program-parity, and crash-recovery
  tests pass in 69.654 seconds.
- `bash pmo-roadmap/tests/workbench-ui-smoke.sh` passes all 76 desktop/mobile
  renders.
- `bash pmo-roadmap/tests/package-smoke.sh` builds and installs the Python 3.9
  wheel, requires the packaged live-progress module and export, and passes
  guided status, deliberate step, bounded orchestration, outward signals, and
  the autonomous multi-phase exam.
- The packaged autonomous exam completes three stories across two phases with
  203 replayed/streamed events, nine conductor and eighteen delivery-boundary
  crash recoveries, three commits/pushes, independent review,
  council/meta/architect proof, one repair round, and the full refusal matrix.
- Its separate vanilla consumer keeps program, run, and notification stores,
  ambient network, background polling, setup writes, and work starts absent.
- Product-language, usability-journey, source/installed HTTP explorer,
  docs/snippets/canon, source/vendor, syntax, update-alignment, and diff checks
  pass.

### Captured run — 2026-07-25T03:05:48Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py LiveProgressProjectionTest OrchestrationConductorTest.test_run_view_is_pure_rich_and_excludes_private_semantics OrchestrationConductorTest.test_run_view_static_contract_has_consent_privacy_and_no_poller ProgramSurfaceTest.test_cli_mcp_http_view_tail_and_sse_are_one_canonical_document ProgramDeliveryTest.test_two_story_commits_phase_transition_and_every_effect_recover
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/usability-journey-contract.py
bash pmo-roadmap/tests/workbench-explorer.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
node --check pmo-roadmap/workbench/app.js
python3 -m py_compile pmo-roadmap/lib/dw_pmo/live_progress.py pmo-roadmap/lib/dw_pmo/orchestration_surface.py pmo-roadmap/lib/dw_pmo/program_surface.py
cmp pmo-roadmap/lib/dw_pmo/live_progress.py .githooks/dw_pmo/live_progress.py
cmp pmo-roadmap/lib/dw_pmo/__init__.py .githooks/dw_pmo/__init__.py
cmp pmo-roadmap/lib/dw_pmo/orchestration_surface.py .githooks/dw_pmo/orchestration_surface.py
cmp pmo-roadmap/lib/dw_pmo/program_surface.py .githooks/dw_pmo/program_surface.py
cmp pmo-roadmap/workbench/app.js .githooks/workbench/app.js
cmp pmo-roadmap/workbench/style.css .githooks/workbench/style.css
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 622d19c67bfb1f7b463ab33215dd52e7567cdaef

```text
test_repair_and_recovery_use_only_canonical_run_facts (__main__.LiveProgressProjectionTest.test_repair_and_recovery_use_only_canonical_run_facts) ... ok
test_run_view_is_pure_rich_and_excludes_private_semantics (__main__.OrchestrationConductorTest.test_run_view_is_pure_rich_and_excludes_private_semantics) ... ok
test_run_view_static_contract_has_consent_privacy_and_no_poller (__main__.OrchestrationConductorTest.test_run_view_static_contract_has_consent_privacy_and_no_poller) ... ok
test_cli_mcp_http_view_tail_and_sse_are_one_canonical_document (__main__.ProgramSurfaceTest.test_cli_mcp_http_view_tail_and_sse_are_one_canonical_document) ... dw-workbench: 127.0.0.1 "GET /api/programs/program-2addaec973d9452df4a7faa1/events?from=0&follow=0 HTTP/1.1" 200 -
ok
test_two_story_commits_phase_transition_and_every_effect_recover (__main__.ProgramDeliveryTest.test_two_story_commits_phase_transition_and_every_effect_recover) ... ok

----------------------------------------------------------------------
Ran 5 tests in 83.000s

OK
product-language-contract: ok (10 concepts, 18 surfaces, 18 reserved terms, 12 fixtures)
usability-journey-contract: ok (13 journeys, 17 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.Hd6ral/repo
dw-workbench: http://127.0.0.1:18485/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.Hd6ral/installed
dw-workbench: http://127.0.0.1:18486/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.Hd6ral/repo
dw-workbench: http://127.0.0.1:18485/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.GnFSzD/repo
dw-workbench: http://127.0.0.1:22655/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
workbench-ui-smoke.sh: ok (76 viewport renders: 29 data views + delivery setup/review + program planning/active/technical/certified/revoked + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.GnFSzD/dw-program-test.kxzld3hc/repo
dw-workbench: http://127.0.0.1:24230/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
docs-lint: ok (469 markdown files)
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
canon-lint.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
