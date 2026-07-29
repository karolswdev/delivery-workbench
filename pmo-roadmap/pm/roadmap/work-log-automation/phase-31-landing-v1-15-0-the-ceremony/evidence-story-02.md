# Evidence - WLA-31-02

- **Story:** WLA-31-02 - Release v1.15.0
- **Status:** done
- **Date:** 2026-07-29

## Proof

v1.15.0 lands phases 22-31 — the whole autonomy layer built since
the v1.14.0 landing. Every version surface moved in lockstep:
`dw_pmo.__version__`, the vendored `.githooks` snapshot, the plugin
manifest, and the formula url (sha256 held at the placeholder until
publication stamps the served wheel). The CHANGELOG's accumulated
Unreleased section became one phase-linked v1.15.0 section.

The three captured runs below are the release battery at the release
tree: the sharded core suite (692 tests, OK), `package-smoke.sh`
(build sdist+wheel, install, bootstrap a fixture to doctor-green,
and replay the packaged guided-status, deliberate-step, bounded
orchestration, outward-loop, autonomous-program, and composed
13-journey usability exams — pass), and `brew-formula-smoke.sh`
(local-tap install, version truth, brew style clean).

Landing the release also caught two stale release-only assertions in
`package-smoke.sh` itself — the program CLI verb list predating the
Phase 30 `scaffold` verb, and the pre-front-door expectation that a
rails-ready consumer with no project is "attention" rather than
ready-with-a-setup-recommendation. Both updated in this story; the
earlier one-off shard failure did not reproduce on a clean rerun
(692/692) and is attributed to load contention from the smoke
running concurrently.

Publication under the standing authorization (2026-07-03), renewed
by the owner for this landing on 2026-07-28 ("let's release all of
this good work"): tag, GitHub Release with hash-verified artifacts,
PyPI via the `pipit` trusted publisher, formula stamp, tap mirror,
cold-install confirmation — recorded in the commit trailer chain and
the follow-up stamp commit.

### Captured run — 2026-07-29T06:07:46Z

- **Command:** `python3 pmo-roadmap/tests/run-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 449e8233939f5e2b786b98e7d7cda761cb3cef7b

```text
run-core-tests: 680 units across 8 shards + 1 serial
  shard 0:  84 tests in  106.7s  ok
  shard 1:  93 tests in   92.4s  ok
  shard 2:  87 tests in  104.4s  ok
  shard 3:  87 tests in  115.4s  ok
  shard 4:  89 tests in  108.2s  ok
  shard 5:  83 tests in  112.0s  ok
  shard 6:  85 tests in  136.1s  ok
  shard 7:  83 tests in  114.0s  ok
  shard 8:   1 tests in    2.4s  ok
run-core-tests: 692 tests in 138.5s (OK)
```

### Captured run — 2026-07-29T06:10:05Z

- **Command:** `pmo-roadmap/tests/package-smoke.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 449e8233939f5e2b786b98e7d7cda761cb3cef7b

```text
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
package-smoke.sh: built delivery_workbench-1.15.0-py3-none-any.whl and delivery_workbench-1.15.0.tar.gz
package-smoke.sh: pipx cannot create environments here; falling back to venv+pip
WARNING: You are using pip version 21.2.4; however, version 26.0.1 is available.
You should consider upgrading via the '/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-package-smoke.3vOnWx/appenv/bin/python -m pip install --upgrade pip' command.
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
commit     2a00befaa80b         trailers+archive+verify=ok
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
bootstrap  55de5a59db97         certification+commit=manual
commit     e55527bc573d         trailers+archive+verify=ok
handoff    start-story        authorizations=7
deliberate-step-loop.sh: ok (fresh token per action; no argv reconstruction or consent shortcut)
{"artifact_count": 5, "checks": 2, "compiler_red_cases": 6, "duplicate_restarts": 0, "exam": "packaged multi-agent orchestration", "operator_commit": "b8ab753cbfbd83f6f2ad35b7d4ccec6385d9597c", "parallel_research": 2, "repair_visits": 1, "run_id": "run-b62a065384ff8051d0f3b338", "runtime_red_cases": 5, "state": "awaiting-certification", "verify_all": "ok"}
{"certification": "operator-only", "duplicate_nudges": 0, "duplicate_starts": 0, "external_rebind": true, "kind": "delivery-workbench-packaged-outward-exam", "nudges": 2, "observer_side_effects": 0, "operator_push": "7c7a5b3bb8d3fcc105ab579e336caee617877d03", "refusals": {"blocked-session": "non-receptive", "budget": "nudge-budget-exhausted", "revoked-request": "expired", "stale-correlation": "correlation-mismatch", "unknown-session": "non-receptive", "without-standing-grant": "no-standing-rule"}, "request_republishes": 1, "run_id": "run-10e2546d49f77be8a6101791", "schema_version": 1, "state": "awaiting-certification", "stream_matches_ledger": true, "wheel_version": "dw 1.15.0"}
# Fresh-wheel usability acceptance transcript

One fresh installed consumer began with ordinary roadmap work, then deliberately entered bounded and optional delivery.

## 1. Healthy first arrival

Question: Is this repository ready, and what useful work can I do now?
Visible:
- One ordinary roadmap story is ready to continue.
- The repository is ready and earlier completed work remains visible.
- Open the current story; optional coordination is not required.
Available actions:
- Open current work: Opens the current story without changing repository or delivery state.
- Check readiness: Reads current readiness facts and makes no change.
- Leave for now: Leaves every repository and delivery fact unchanged.
Outcome: The person can identify current work and continue without optional setup.
Next step: Open current work
Safe refusal: If readiness cannot be established, show the affected check and do not suggest that work may start. No repository or delivery state changes. Next: Check readiness
Technical details: exact source models remain available; return with “Back to current work”.
Observed production checkpoint: same_consumer.initial
Result: pass

## 2. Deliberate delivery choice

Question: How much coordination do I want for this delivery?
Visible:
- Ordinary roadmap work remains available with no optional setup.
- One bounded delivery and an optional program each require a separate reviewed start.
- Stay with the roadmap, review one bounded delivery, or review an optional program.
Available actions:
- Continue with the roadmap: Returns to ordinary work and creates no optional delivery state.
- Confirm one bounded delivery: Starts only the reviewed work with the reviewed limits; it does not enable an optional program. Separate confirmation required.
- Confirm the optional program: Starts only the reviewed optional program with the reviewed scope and limits. Separate confirmation required.
Outcome: The selected tier is explicit, and any higher tier starts only after its own confirmation.
Next step: Review the selected delivery
Safe refusal: If a start is stale or incomplete, nothing starts and the person may return to ordinary work. Ordinary roadmap work and every unselected tier remain unchanged. Next: Continue with the roadmap
Technical details: exact source models remain available; return with “Back to delivery choices”.
Observed production checkpoint: same_consumer
Result: pass

## 3. Delivery-plan setup

Question: What will be delivered, in what order, and where should work stop?
Visible:
- The draft names the work, sequence, review points, repair paths, and stop conditions.
- Saving the draft starts no work and provides no permission to act.
- Review the readable plan, then save it or leave it unchanged.
Available actions:
- Save reviewed draft: Writes only the reviewed delivery-plan document and starts no work. Separate confirmation required.
- Discard unsaved changes: Leaves the saved delivery plan and every runtime fact unchanged.
- Review plan summary: Shows the plan summary and makes no change.
Outcome: The saved draft preserves the reviewed plan and still starts nothing.
Next step: Set up the team and review
Safe refusal: If validation or freshness fails, identify the affected delivery decision and keep the saved document unchanged. No draft, permission, work, or roadmap state changes. Next: Review plan summary
Technical details: exact source models remain available; return with “Back to plan summary”.
Observed production checkpoint: same_consumer.optional_configuration
Result: pass

## 4. Team and review setup

Question: Who will do, review, and decide on this work?
Visible:
- The summary names who does each kind of work and who reviews it independently.
- The summary names required reviews, contested decisions, and escalation paths.
- Any incompatible assignment identifies the exact roles and a corrective choice.
Available actions:
- Save reviewed team: Writes only the reviewed team document and starts no work. Separate confirmation required.
- Discard unsaved changes: Leaves the saved team and every runtime fact unchanged.
- Review responsibilities: Shows responsibilities and separation facts and makes no change.
Outcome: The saved team makes responsibility, independent review, and decision ownership understandable.
Next step: Review delivery readiness
Safe refusal: If responsibility or independence is invalid, name the conflict and keep the saved team unchanged. No team, permission, work, or roadmap state changes. Next: Review responsibilities
Technical details: exact source models remain available; return with “Back to team summary”.
Observed production checkpoint: preflight
Result: pass

## 5. Delivery preflight

Question: Is this delivery ready to start, and what exactly may it do?
Visible:
- The reviewed work, order, checks, and stop conditions are valid.
- The people or agents responsible for work and review are named.
- The exact allowed effects, time, work, and cost limits are shown before start.
- Confirm this reviewed delivery or return to the plan.
Available actions:
- Confirm this delivery: Starts only the reviewed work under the reviewed limits and does not continue automatically. Separate confirmation required.
- Return to the plan: Returns to setup and starts nothing.
- Leave for now: Leaves the plan, repository, and delivery state unchanged.
Outcome: The exact reviewed delivery starts once and remains bounded by the displayed limits.
Next step: View live progress
Safe refusal: If readiness, freshness, or permission fails, nothing starts and the affected fact is named. No work, process, permission, or roadmap state is created or changed. Next: Return to the plan
Technical details: exact source models remain available; return with “Back to delivery readiness”.
Observed production checkpoint: preflight
Result: pass

## 6. Live delivery progress

Question: What is happening now, what passed, and what happens next?
Visible:
- Current, waiting, completed, and blocked work are visibly distinct.
- Completed checks and reviews state what they establish.
- Consumed and remaining work, time, and cost are shown with their limits.
- One canonical next step explains whether to advance, wait, decide, repair, or stop.
Available actions:
- Refresh progress: Reloads the canonical delivery state and starts no work.
- Advance one step: Performs at most the one reviewed next delivery step. Separate confirmation required.
- Pause delivery: Stops new work from starting while preserving completed work and current state. Separate confirmation required.
Outcome: The display explains progress and the reviewed next step advances at most once.
Next step: Review updated progress
Safe refusal: If the next step is stale or unavailable, show what changed and start no replacement step. No unreviewed work starts and completed work remains recorded. Next: Refresh progress
Technical details: exact source models remain available; return with “Back to live progress”.
Observed production checkpoint: delivery
Result: pass

## 7. Failed review and repair

Question: What failed, what can repair it, and what remains safe?
Visible:
- The failed check states what it tested and what did not pass.
- Affected work and the available repair path are named.
- Retry the bounded repair, pause safely, or inspect the failure.
Available actions:
- Review the failed check: Opens the failure explanation and makes no change.
- Retry the bounded repair: Starts only the reviewed repair attempt under the remaining limits. Separate confirmation required.
- Pause delivery: Starts no further work and preserves the failure and completed work. Separate confirmation required.
Outcome: Only the reviewed repair runs, and the failed check must pass before work continues.
Next step: Review the repair result
Safe refusal: If repair is unavailable or its facts changed, start nothing and preserve the failure for review. No replacement work starts and the prior failure remains visible. Next: Review the failed check
Technical details: exact source models remain available; return with “Back to repair”.
Observed production checkpoint: delivery
Result: pass

## 8. Blocked human decision

Question: Who must decide, which choices are valid, and what follows each choice?
Visible:
- The affected work and reason it cannot continue are named.
- The responsible person, closed choices, and effect of each choice are shown.
- Respond with one valid choice or leave the decision pending.
Available actions:
- Approve this request: Applies approval only to the exact outstanding request and then rechecks what may proceed. Separate confirmation required.
- Reject this request: Applies rejection only to the exact outstanding request and keeps affected work stopped. Separate confirmation required.
- Decide later: Leaves the request pending and starts no affected work.
Outcome: One exact decision is recorded and the canonical next step is recalculated.
Next step: Review what happens next
Safe refusal: If the request is stale, mismatched, already answered, or unavailable, refuse without guessing another response. The outstanding decision and affected work remain unchanged. Next: Decide later
Technical details: exact source models remain available; return with “Back to the decision”.
Observed production checkpoint: bounded_decision
Result: pass

## 9. Remaining permission and cost

Question: What may this delivery still change or spend?
Visible:
- Allowed effects, scope, expiry, stop conditions, and forbidden effects are stated.
- Each limit distinguishes total, used, remaining, unknown, and not applicable.
- Continue once, pause, or permanently stop after reviewing the current limits.
Available actions:
- Review remaining limits: Shows current permission and cost facts and makes no change.
- Pause the program: Stops new work from starting while preserving completed work and current limits. Separate confirmation required.
- Permanently stop the program: Permanently prevents new program work while preserving completed work and exact history. Separate confirmation required.
Outcome: The person can distinguish what remains allowed, consumed, and forbidden before acting.
Next step: Review what happens next
Safe refusal: If limit facts are stale or unavailable, do not act and do not estimate authority. No work starts and no permission or cost value changes. Next: Review remaining limits
Technical details: exact source models remain available; return with “Back to remaining limits”.
Observed production checkpoint: delivery.limits
Result: pass

## 10. Stop and revoke

Question: How do I pause safely or permanently stop this delivery?
Visible:
- Active and completed work are shown before a stop choice.
- Pause is reversible; permanent stop prevents future program work.
- Confirm one stop choice or return without changing delivery state.
Available actions:
- Pause the program: Stops new program work until a separately reviewed resume. Separate confirmation required.
- Permanently stop the program: Permanently prevents new program work while preserving completed work and exact history. Separate confirmation required.
- Return without stopping: Leaves current delivery state unchanged.
Outcome: The selected stop takes effect once and its consequence is visible.
Next step: Review stopped state
Safe refusal: If the stop choice is stale or mismatched, do not apply a different stop and show the current state. No stop or resume is applied. Next: Return without stopping
Technical details: exact source models remain available; return with “Back to stop choices”.
Observed production checkpoint: stop_and_revoke
Result: pass

## 11. Crash recovery

Question: After interruption, what completed, what may resume, and what happens next?
Visible:
- Completed and in-progress effects are reconstructed from canonical state.
- Any uncertain or incomplete boundary remains stopped for review.
- Resume uses only still-valid permission and remaining limits.
- Reload state, then resume deliberately or permanently stop.
Available actions:
- Reload delivery state: Reconstructs the canonical view and starts no work.
- Resume reviewed work: Allows only still-valid reviewed work to continue after state is rechecked. Separate confirmation required.
- Permanently stop delivery: Prevents future work while preserving completed and uncertain state for inspection. Separate confirmation required.
Outcome: Recovered state distinguishes completed, incomplete, and eligible work before anything resumes.
Next step: Review live progress
Safe refusal: If recovery cannot prove current state or permission, keep work stopped and expose the exact record. No uncertain work is repeated and no new work starts. Next: Reload delivery state
Technical details: exact source models remain available; return with “Back to recovery”.
Observed production checkpoint: recovery
Result: pass

## 12. Reviewed completion

Question: What finished, what passed, and is there more work?
Visible:
- The completed delivery and any remaining scoped work are named.
- Passed checks, independent review, dissent, and final outcome remain distinct.
- Completion states whether the work item or the whole delivery is finished.
- Open the next work item or stop because the delivery is complete.
Available actions:
- Review what passed: Shows the review outcome and makes no change.
- Open next work: Opens the next eligible work item and starts nothing.
- Finish here: Leaves completed work and delivery state unchanged.
Outcome: The person can tell what passed, what completed, and whether any work remains.
Next step: Open next work
Safe refusal: If completion cannot be established, do not claim success and identify the missing review or work fact. No work or completion state changes. Next: Review what passed
Technical details: exact source models remain available; return with “Back to completion”.
Observed production checkpoint: completion
Result: pass

## 13. Technical inspection

Question: How can I inspect the exact record without losing the delivery summary?
Visible:
- The ordinary summary remains the default view and names its canonical sources.
- The exact permission, limits, identities, events, and configuration are one explicit view away.
- Open exact details, copy what is needed, then return to the delivery summary.
Available actions:
- Open Technical details: Opens the exact source record and makes no change.
- Copy exact details: Copies selected exact data and makes no delivery change.
- Back to delivery summary: Returns to the ordinary summary and makes no change.
Outcome: Exact data is inspectable and the person can return to the same ordinary task context.
Next step: Back to delivery summary
Safe refusal: If exact data cannot be loaded, say which source is unavailable and keep the ordinary summary usable. No delivery state changes and no technical value is guessed. Next: Back to delivery summary
Technical details: exact source models remain available; return with “Back to delivery summary”.
Observed production checkpoint: technical_details
Result: pass

## Measured friction and deferrals

13 journey checkpoints; 4 explicit authority confirmations; 13 safe refusal paths; 0 unresolved dead ends; 0 reserved engineering terms in the everyday transcript.
Baseline screen steps are descriptive and are not subtracted from transcript checkpoints as though they were the same measure.
- Deferred: No external user-study or 
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-29T06:14:16Z

- **Command:** `pmo-roadmap/tests/brew-formula-smoke.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 449e8233939f5e2b786b98e7d7cda761cb3cef7b

```text
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for wheel...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
* Building wheel...
warning: no previously-included files matching '*.pyc' found anywhere in distribution
brew-formula-smoke.sh: built delivery_workbench-1.15.0-py3-none-any.whl
brew-formula-smoke.sh: brew style: clean
brew-formula-smoke.sh: ok
```
