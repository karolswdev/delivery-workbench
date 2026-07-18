# Evidence - WLA-24-07

- **Story:** WLA-24-07 - Expose and monitor runs across every surface
- **Status:** done
- **Date:** 2026-07-18

## Proof

### Result interpretation

- Ten focused core tests prove exact transport documents, intent-bound stale
  refusal before work/events, pure/private Run views, bounded explicit
  streams, closed adapter schemas, content-safe mission summaries, and the
  no-poller/no-generic-shell browser contract.
- The installed real-process interop fixture uses HTTP for grant/start and a
  conductor tick, MCP for pause and checkpoint approval, and CLI for resume
  and terminal advancement. It deliberately replays tokens through another
  adapter and verifies the ledger remains byte-identical.
- The Workbench integration remains green, and Firefox produced 32 data-
  bearing renders: 14 views plus attention and ambiguity at desktop/mobile,
  including active, fail→repair, and terminal orchestration Run states.
- The Python-3.9 package smoke built both distribution artifacts, installed
  the wheel, found every new core/tool/route/UI surface, and completed the
  pre-existing guided and deliberate-step gated consumer exams. Full 297-test
  suites also passed separately on the local and declared Python 3.9 runtimes.

### Captured run — 2026-07-18T07:57:14Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact OrchestrationConductorTest.test_tick_result_is_returned_unmodified_by_cli_mcp_and_http OrchestrationConductorTest.test_run_act_token_binds_action_reason_decision_and_state OrchestrationConductorTest.test_stale_tick_preview_refuses_before_dispatch_or_event OrchestrationConductorTest.test_run_view_is_pure_rich_and_excludes_private_semantics OrchestrationConductorTest.test_run_stream_is_explicit_bounded_and_injection_safe OrchestrationConductorTest.test_cli_and_mcp_controls_require_fresh_preview_tokens OrchestrationConductorTest.test_adapters_reject_score_semantics_driver_config_and_argv OrchestrationConductorTest.test_mission_control_run_summary_is_content_safe OrchestrationConductorTest.test_run_view_static_contract_has_consent_privacy_and_no_poller
pmo-roadmap/tests/orchestration-interop.sh
pmo-roadmap/tests/workbench-explorer.sh
pmo-roadmap/tests/workbench-ui-smoke.sh
pmo-roadmap/tests/package-smoke.sh
pmo-roadmap/tests/docs-lint.sh
pmo-roadmap/update.sh . --check
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ba0e6478866769d1c7ed0b5a40e7e721ee8d12b7

```text
test_run_interop_compiler_plan_projection_and_preview_are_exact (__main__.OrchestrationConductorTest.test_run_interop_compiler_plan_projection_and_preview_are_exact) ... ok
test_tick_result_is_returned_unmodified_by_cli_mcp_and_http (__main__.OrchestrationConductorTest.test_tick_result_is_returned_unmodified_by_cli_mcp_and_http)
Applying adapters wrap the one core document; none reinterprets it. ... ok
test_run_act_token_binds_action_reason_decision_and_state (__main__.OrchestrationConductorTest.test_run_act_token_binds_action_reason_decision_and_state) ... ok
test_stale_tick_preview_refuses_before_dispatch_or_event (__main__.OrchestrationConductorTest.test_stale_tick_preview_refuses_before_dispatch_or_event) ... ok
test_run_view_is_pure_rich_and_excludes_private_semantics (__main__.OrchestrationConductorTest.test_run_view_is_pure_rich_and_excludes_private_semantics) ... ok
test_run_stream_is_explicit_bounded_and_injection_safe (__main__.OrchestrationConductorTest.test_run_stream_is_explicit_bounded_and_injection_safe) ... ok
test_cli_and_mcp_controls_require_fresh_preview_tokens (__main__.OrchestrationConductorTest.test_cli_and_mcp_controls_require_fresh_preview_tokens) ... ok
test_adapters_reject_score_semantics_driver_config_and_argv (__main__.OrchestrationConductorTest.test_adapters_reject_score_semantics_driver_config_and_argv) ... ok
test_mission_control_run_summary_is_content_safe (__main__.OrchestrationConductorTest.test_mission_control_run_summary_is_content_safe) ... ok
test_run_view_static_contract_has_consent_privacy_and_no_poller (__main__.OrchestrationConductorTest.test_run_view_static_contract_has_consent_privacy_and_no_poller) ... ok

----------------------------------------------------------------------
Ran 10 tests in 13.274s

OK
orchestration interop: exact CLI/MCP/HTTP lifecycle reached awaiting-certification
orchestration-interop.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-orchestration-interop.KsrxFs/repo
dw-workbench: http://127.0.0.1:23516/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.mMlk2O/repo
dw-workbench: http://127.0.0.1:18585/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.mMlk2O/installed
dw-workbench: http://127.0.0.1:18586/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.mMlk2O/repo
dw-workbench: http://127.0.0.1:18585/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
workbench-ui-smoke.sh: ok (32 viewport renders: 14 views + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.rswDLY/repo
dw-workbench: http://127.0.0.1:22524/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require /api/mutations preview→apply or an exact /api/step/apply token; never stages, certifies, or commits
package-smoke.sh: skipping unhealthy interpreter: python3
package-smoke.sh: building with: /usr/bin/python3 (Python 3.9.6)
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for sdist...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building sdist...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for wheel...
warning: no previously-included files matching '__pycache__/*' found anywhere in distribution
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building wheel...
warning: no previously-included files matching '__pycache__/*' found anywhere in distribution
warning: no previously-included files matching '*.pyc' found anywhere in distribution
package-smoke.sh: built delivery_workbench-1.14.0-py3-none-any.whl and delivery_workbench-1.14.0.tar.gz
package-smoke.sh: pipx cannot create environments here; falling back to venv+pip
WARNING: You are using pip version 21.2.4; however, version 26.0.1 is available.
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.zE6WpF/appenv/bin/python -m pip install --upgrade pip' command.
package-smoke.sh: installed via venv+pip
ready     review-workspace   absent     not-applicable
ready     generate-contract  absent     fail
ready     certify-contract   unchecked  fail
ready     commit             passing    pass
ready     start-story        absent     not-applicable
ready     continue-story     absent     not-applicable
attention repair-roadmap     absent     not-applicable
ready     continue-story     absent     not-applicable
ready     continue-story     absent     not-applicable
attention finish-story       absent     not-applicable
ready     review-workspace   absent     not-applicable
ready     generate-contract  absent     fail
ready     certify-contract   unchecked  fail
ready     generate-contract  stale      fail
ready     certify-contract   unchecked  fail
ready     commit             passing    pass
ready     start-story        absent     not-applicable
commit     3e59b33101df         trailers+archive+verify=ok
guided-status-loop.sh: ok (packaged CLI/MCP/HTTP recommendation sequence)
authorize 01 cli  review-workspace   -> review-workspace
authorize 02 mcp  generate-contract  -> certify-contract
refuse   bootstrap certification started=0 step_events=+0
refuse   bootstrap commit       started=0 step_events=+0
authorize 03 http start-story        -> continue-story
refuse   same-id stale token    started=0 step_events=+0
authorize 04 mcp  continue-story     -> continue-story
authorize 05 cli  finish-story       -> review-workspace
authorize 06 http review-workspace   -> review-workspace
authorize 07 cli  generate-contract  -> certify-contract
refuse   story certification    started=0 step_events=+0
refuse   story commit           started=0 step_events=+0
bootstrap  e4188b132491         certification+commit=manual
commit     95e493aa4d24         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
package-smoke.sh: ok
docs-lint: ok (395 markdown files)
docs-lint.sh: ok (0s)
update.sh: up to date (vendored rails match source v1.14.0)
```
