# Evidence - WLA-27-07

- **Story:** WLA-27-07 - Turn decisions, blockers, permissions, and cost into
  actions
- **Status:** done
- **Date:** 2026-07-25

## One source-backed bounded-actions model

The new pure
[`bounded_actions.py`](../../../../lib/dw_pmo/bounded_actions.py) projection
attaches `delivery-workbench-bounded-actions@1` to both the canonical
bounded-run and program views. Workbench, CLI JSON, MCP, HTTP, and SSE
therefore receive the same action facts rather than reconstructing safety
semantics in each renderer.

The projection consumes only already-derived controls, outstanding requests,
blockers, permission, limits, progress, failures, and receipts. It reports
false for starting work, writing events, selecting an action or next work,
granting authority, changing retry policy, and sending notifications.

## Decisions and blockers become bounded choices

Every inbox item names:

1. the affected work;
2. why it cannot proceed;
3. who or what can resolve it;
4. every currently valid choice and its consequence; and
5. what happens when no choice is made.

Decision choices come only from the exact current run request or program
checkpoint controls. A response retains its exact request binding for the
existing preview and apply boundary. Stale, closed, mismatched, unauthorized,
and duplicate responses continue to refuse in the canonical core; the
application neither widens the response set nor suggests an ambiguous retry.

## Permission, cost, and consequence-first controls

The action center puts permission before action: concrete allowed effects,
scope, ceilings, expiry and stop conditions, current consumption, and still
forbidden effects. Each usage row keeps limit, estimate, actual use, and
remaining capacity separate. Finite values, zero, explicit unbounded state,
unknown values, and not-applicable measures cannot collapse into one display.
Incomparable units are never added.

Continue and saved repair, pause, resume, permanent revoke, cancel, rejection,
unavailable retry, and separate permission elevation all have distinct labels
and consequences. Available mutations first open the existing exact preview.
No state change occurs until its fresh token is confirmed. Completion then
shows a readable receipt with its exact reference under **Technical details**.
Read-only reload, inspect-limits, inspect-failure, decide-later, leave, and
technical-inspection paths require no confirmation and start no work.

## Refusal and recovery language

Failures state what happened, what stayed unchanged, whether an effect may
already have occurred, the safe next step, and how to inspect exact evidence.
A conclusive stale or inapplicable preview says no effect occurred. A lost or
inconclusive transport result says the effect is unknown until canonical
history is reloaded; it never recommends a blind retry.

Run and program receipts remain ledger-derived. Browser snapshots preserve the
last verified state, exact-action previews remain pure, and already-applied
outcomes are discovered by replay rather than inferred from transport success.

## Notifications and remote response boundary

Run and program request notifications now carry affected work, the exact
closed choices, and what follows each choice. Telegram can route a typed
program checkpoint response as well as a bounded-run response, but the remote
message supplies no token or authority. Canonical local principal, outstanding
request, response-set, ledger, generation, freshness, and exact apply checks
remain decisive. Foreign principals, stale requests, and altered responses
refuse locally.

## Device and journey proof

The browser harness renders 88 canonical viewports at 1440x900 and 390x844.
Six new wide/narrow capture pairs cover:

- bounded-run decision actions;
- a decision consequence preview;
- a structured stale refusal;
- program remaining permission and cost;
- a program pause preview; and
- a program stop receipt.

The usability inventory now contains 23 reachable states. Manual snapshot
inspection confirms that the decision inbox is usable without raw JSON,
permission and usage precede state-changing controls, dangerous consequences
are visible before confirmation, stale responses give a safe reload path, and
exact tokens and receipts remain under **Technical details**.

## Regression and distribution proof

- Six focused bounded-actions and run/program surface parity tests pass in
  5.969 seconds.
- The Telegram suite passes all 153 tests (nine optional Pillow cases skipped),
  including owner, stranger, stale-correlation, and program response-carrier
  paths.
- The complete core suite passes all 488 tests in 956.214 seconds with the new
  projection and unchanged exact authority behavior.
- The Workbench browser suite passes all 88 desktop/mobile renders. A retained
  `.tmp/wla27-story07-final` pass was visually inspected after correcting the
  fixture to use a real outstanding decision and making snapshot focus
  independent of browser scroll behavior.
- The package smoke builds and installs the Python 3.9 wheel, requires the
  packaged bounded-actions module/export, and keeps guided status, deliberate
  step, bounded orchestration, outward signals, autonomous delivery, and the
  dormant no-program consumer green.
- The packaged autonomous exam completes three stories across two phases with
  203 replayed/streamed events, nine conductor and eighteen delivery-boundary
  crash recoveries, three commits/pushes, one repair round, and zero duplicate
  starts.
- Product-language, usability-journey, source/installed HTTP explorer,
  Telegram, docs/snippets/canon, syntax, source/vendor byte identity,
  update-alignment, and diff checks pass. The executable inventories report
  ten product concepts, eighteen surfaces, eighteen reserved terms, thirteen
  language fixtures, thirteen journeys, twenty-three reachable states, and
  six red journey fixtures.

The certification command and its exact output are recorded by the story's
captured evidence run and guarded commit contract.

### Captured run — 2026-07-25T16:14:54Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py BoundedActionsProjectionTest OrchestrationConductorTest.test_run_view_is_pure_rich_and_excludes_private_semantics OrchestrationConductorTest.test_run_view_static_contract_has_consent_privacy_and_no_poller ProgramSurfaceTest.test_cli_mcp_http_view_tail_and_sse_are_one_canonical_document
python3 pmo-roadmap/tests/telegram-interface-tests.py NotificationDecisionTest
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/usability-journey-contract.py
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
node --check pmo-roadmap/workbench/app.js
bash -n pmo-roadmap/tests/workbench-ui-smoke.sh
python3 -m py_compile pmo-roadmap/lib/dw_pmo/bounded_actions.py pmo-roadmap/lib/dw_pmo/notifications.py pmo-roadmap/lib/dw_pmo/orchestration_surface.py pmo-roadmap/lib/dw_pmo/program_run.py pmo-roadmap/lib/dw_pmo/program_surface.py integrations/telegram/dw_telegram/interface.py integrations/telegram/dw_telegram/rails.py
cmp pmo-roadmap/lib/dw_pmo/bounded_actions.py .githooks/dw_pmo/bounded_actions.py
cmp pmo-roadmap/lib/dw_pmo/__init__.py .githooks/dw_pmo/__init__.py
cmp pmo-roadmap/lib/dw_pmo/notifications.py .githooks/dw_pmo/notifications.py
cmp pmo-roadmap/lib/dw_pmo/orchestration_surface.py .githooks/dw_pmo/orchestration_surface.py
cmp pmo-roadmap/lib/dw_pmo/program_run.py .githooks/dw_pmo/program_run.py
cmp pmo-roadmap/lib/dw_pmo/program_surface.py .githooks/dw_pmo/program_surface.py
cmp pmo-roadmap/workbench/app.js .githooks/workbench/app.js
cmp pmo-roadmap/workbench/style.css .githooks/workbench/style.css
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b238ce00cefe48dd09f8c8a9f45277a83c7678fc

```text
test_measurements_never_confuse_zero_unbounded_unknown_or_na (__main__.BoundedActionsProjectionTest.test_measurements_never_confuse_zero_unbounded_unknown_or_na) ... ok
test_program_request_and_remote_guidance_never_mint_authority (__main__.BoundedActionsProjectionTest.test_program_request_and_remote_guidance_never_mint_authority) ... ok
test_run_decisions_blockers_permission_and_actions_are_closed (__main__.BoundedActionsProjectionTest.test_run_decisions_blockers_permission_and_actions_are_closed) ... ok
test_run_view_is_pure_rich_and_excludes_private_semantics (__main__.OrchestrationConductorTest.test_run_view_is_pure_rich_and_excludes_private_semantics) ... ok
test_run_view_static_contract_has_consent_privacy_and_no_poller (__main__.OrchestrationConductorTest.test_run_view_static_contract_has_consent_privacy_and_no_poller) ... ok
test_cli_mcp_http_view_tail_and_sse_are_one_canonical_document (__main__.ProgramSurfaceTest.test_cli_mcp_http_view_tail_and_sse_are_one_canonical_document) ... dw-workbench: 127.0.0.1 "GET /api/programs/program-ebdb26de7b7d4f89fbf0acf8/events?from=0&follow=0 HTTP/1.1" 200 -
ok

----------------------------------------------------------------------
Ran 6 tests in 4.879s

OK
test_decision_applies_through_the_rails_for_the_owner (__main__.NotificationDecisionTest.test_decision_applies_through_the_rails_for_the_owner) ... ok
test_decision_from_a_stranger_is_refused (__main__.NotificationDecisionTest.test_decision_from_a_stranger_is_refused) ... ok
test_decision_refuses_stale_correlation_and_bad_usage (__main__.NotificationDecisionTest.test_decision_refuses_stale_correlation_and_bad_usage) ... ok
test_program_response_is_carried_to_the_local_exact_boundary (__main__.NotificationDecisionTest.test_program_response_is_carried_to_the_local_exact_boundary) ... ok
test_push_pass_sends_outbound_and_records_delivery (__main__.NotificationDecisionTest.test_push_pass_sends_outbound_and_records_delivery) ... ok
test_push_pass_without_pairing_sends_nothing (__main__.NotificationDecisionTest.test_push_pass_without_pairing_sends_nothing) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.115s

OK
product-language-contract: ok (10 concepts, 18 surfaces, 18 reserved terms, 13 fixtures)
usability-journey-contract: ok (13 journeys, 23 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
docs-lint: ok (470 markdown files)
docs-lint.sh: ok (1s)
canon-lint.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
