# Evidence - WLA-12-03

- **Story:** WLA-12-03 - Build the HoldSpeak story actuator
- **Status:** done
- **Date:** 2026-07-03

## Proof

Four captured runs, in order:

1. **The actuator test suite (04:09:46Z):** 13 tests across three
   classes — proposal building on both paths (explicit `dw_action`
   and canned-LLM), invented-story-ID and illegal-status refusals,
   connector argv construction, out-of-allow-list refusal before
   egress, foreign-repo payload refusal, and the end-to-end class:
   green flip lands in the fixture, the crown case (approved
   done-flip refused by the dw gate, banner asserted verbatim),
   policy-defaults-execute-nothing, and parity-mismatch-no-egress.
2. **A failed crown proof (04:10:31Z), kept in per the charter:**
   the system worked and my script didn't — the real LLM chose
   `WSH-1-01` ("mid-flight" cart → in-progress), a sharper reading
   than the `WSH-1-02` my assertions hardcoded. The green flip and
   the gate refusal both actually fired in that run; only my
   fixture check looked at the wrong file.
3. **The crown proof (04:11:06Z), real everything:** the desk's
   real LLM proposed from the transcript, HoldSpeak's real db
   stored and approved, the real executor egressed through the
   gated connector, the flip landed in the fixture — and then the
   approved dishonest done-flip came back `failed` with
   `dw: refusing to mark story done without evidence` verbatim,
   fixture unchanged, audit trail `proposed -> approved -> failed`.
   Two consent systems, stacked, each doing its own job.
4. **Desk install (04:11:21Z):** both pack files discovered
   side-by-side by the real loader, no errors.

Reality deltas, recorded here and in `docs/riders.md`: the 0.3.1
loader is one plugin per pack file (module exports one `MANIFEST`),
so the actuator ships as `delivery_workbench_actuator_pack.py`
beside the synthesizer pack rather than inside it; the connector
resolves `dw` as the target repo's own `.githooks/dw` first,
installed `dw --root` second (resolving the story's open question);
and a proposal carries domain fields only — argv is built by the
connector from the stored payload at egress, never by the model.
The desk's own "Pending actions" execution wiring for *pack*
actuators (as opposed to built-ins) is unverified and pending,
recorded with the live-meeting screenshot as owed, not faked.

### Captured run — 2026-07-04T04:09:46Z

- **Command:** `/Users/karol/dev/tools/HoldSpeak/.venv/bin/python pmo-roadmap/tests/holdspeak-pack-tests.py ActuatorProposalTest ActuatorConnectorTest ActuatorEndToEndTest`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 75b969109b8fdc3cf827ef069be8501a2adae64f

```text
test_create_proposal_targets_a_real_phase (__main__.ActuatorProposalTest.test_create_proposal_targets_a_real_phase) ... ok
test_explicit_action_builds_status_proposal (__main__.ActuatorProposalTest.test_explicit_action_builds_status_proposal) ... ok
test_illegal_status_is_refused (__main__.ActuatorProposalTest.test_illegal_status_is_refused) ... ok
test_invented_story_id_is_refused (__main__.ActuatorProposalTest.test_invented_story_id_is_refused) ... ok
test_llm_path_builds_the_same_proposal (__main__.ActuatorProposalTest.test_llm_path_builds_the_same_proposal) ... ok
test_no_action_meeting_raises (__main__.ActuatorProposalTest.test_no_action_meeting_raises) ... ok
test_foreign_repo_payload_is_refused (__main__.ActuatorConnectorTest.test_foreign_repo_payload_is_refused) ... ok
test_happy_path_builds_allowlisted_argv (__main__.ActuatorConnectorTest.test_happy_path_builds_allowlisted_argv) ... ok
test_out_of_allowlist_verb_is_refused_before_egress (__main__.ActuatorConnectorTest.test_out_of_allowlist_verb_is_refused_before_egress) ... gated connector 'dw_story_writer' refused operation [subprocess: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmpbyiky1ls/rails/.githooks/dw story delete] (not on manifest)
ok
test_crown_case_gate_refuses_dishonest_done_flip (__main__.ActuatorEndToEndTest.test_crown_case_gate_refuses_dishonest_done_flip) ... actuator connector failed for 8443a3b865764dcc9a3e69d7ef96696d: dw exited 1: 
dw: refusing to mark story done without evidence; pass --evidence-body or --evidence-from-file
ok
test_green_path_approved_flip_executes (__main__.ActuatorEndToEndTest.test_green_path_approved_flip_executes) ... ok
test_parity_mismatch_aborts_without_egress (__main__.ActuatorEndToEndTest.test_parity_mismatch_aborts_without_egress) ... actuator payload parity mismatch for 4cb9439392ea4bd9949ab948d6d94f6d (approved deadbeefdead != current cab31f9f6a9b)
ok
test_policy_defaults_execute_nothing (__main__.ActuatorEndToEndTest.test_policy_defaults_execute_nothing) ... ok

----------------------------------------------------------------------
Ran 13 tests in 5.473s

OK
```

### Captured run — 2026-07-04T04:10:31Z

- **Command:** `/Users/karol/dev/tools/HoldSpeak/.venv/bin/python /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/fdc6877b-9071-406e-94f9-c2020d111439/scratchpad/actuator-real-llm-proof.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 75b969109b8fdc3cf827ef069be8501a2adae64f

```text
actuator connector failed for ba523c3843844a4385a797f1eb807999: dw exited 1: 
dw: refusing to mark story done without evidence; pass --evidence-body or --evidence-from-file
host result: status=proposed
REAL-LLM proposal: action=dw_story_status payload={'repo': '/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmpshpdmjsw/rails', 'verb': 'status', 'project': 'webshop', 'phase': '1', 'story': 'WSH-1-01', 'status': 'in-progress'}
preview: Flip WSH-1-01 (Build the cart API) from [backlog] to [in-progress] in webshop at /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmpshpdmjsw/rails. Reversal: flip the status back with the same command. The dw gate still applies (a done-flip without evidence will be refused). Meeting basis: The cart API is mid-flight — endpoints are sketched, tests half done. If nothing interrupts, it lands this week.

fixture before green path: WSH-1-02 is [backlog]
green path: executed=True stdout=WSH-1-01	in-progress	pm/roadmap/webshop/phase-1-checkout-flow/story-01-build-the-cart-api.md
fixture after: WSH-1-02 is [backlog]

--- CROWN CASE: approved dishonest done-flip ---
crown outcome: status=failed
the rails said, verbatim:
RuntimeError: dw exited 1: 
dw: refusing to mark story done without evidence; pass --evidence-body or --evidence-from-file
Traceback (most recent call last):
  File "/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/fdc6877b-9071-406e-94f9-c2020d111439/scratchpad/actuator-real-llm-proof.py", line 140, in <module>
    assert story_status("story-02-add-payment-provider.md") == "in-progress"
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
```

### Captured run — 2026-07-04T04:11:06Z

- **Command:** `/Users/karol/dev/tools/HoldSpeak/.venv/bin/python /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/fdc6877b-9071-406e-94f9-c2020d111439/scratchpad/actuator-real-llm-proof.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 75b969109b8fdc3cf827ef069be8501a2adae64f

```text
actuator connector failed for a5159d0b814c4392afe532a1d2094c01: dw exited 1: 
dw: refusing to mark story done without evidence; pass --evidence-body or --evidence-from-file
host result: status=proposed
REAL-LLM proposal: action=dw_story_status payload={'repo': '/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmpfzwl_i9q/rails', 'verb': 'status', 'project': 'webshop', 'phase': '1', 'story': 'WSH-1-01', 'status': 'in-progress'}
preview: Flip WSH-1-01 (Build the cart API) from [backlog] to [in-progress] in webshop at /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmpfzwl_i9q/rails. Reversal: flip the status back with the same command. The dw gate still applies (a done-flip without evidence will be refused). Meeting basis: The cart API is mid-flight — endpoints are sketched, tests half done. If nothing interrupts, it lands this week.

fixture before green path: WSH-1-01 is [backlog]
green path: executed=True stdout=WSH-1-01	in-progress	pm/roadmap/webshop/phase-1-checkout-flow/story-01-build-the-cart-api.md
fixture after: WSH-1-01 is [in-progress]

--- CROWN CASE: approved dishonest done-flip ---
crown outcome: status=failed
the rails said, verbatim:
RuntimeError: dw exited 1: 
dw: refusing to mark story done without evidence; pass --evidence-body or --evidence-from-file

fixture unchanged by the refused flip: WSH-1-01 still [in-progress]
audit trail: proposed -> approved -> failed

PASS: two consent systems stacked; the gate kept final say
```

### Captured run — 2026-07-04T04:11:21Z

- **Command:** `bash -c cp integrations/holdspeak/delivery_workbench_actuator_pack.py ~/.holdspeak/plugin_packs/ && /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -c "
from holdspeak.plugin_pack_loader import DEFAULT_USER_PACK_DIR, discover_user_packs
packs, errors = discover_user_packs(DEFAULT_USER_PACK_DIR)
found = sorted((p.manifest.id, p.manifest.kind) for p in packs)
print(\"desk discovers:\", found, \"errors:\", list(errors))
assert found == [(\"delivery_workbench\", \"synthesizer\"), (\"delivery_workbench_actuator\", \"actuator\")] and not errors
print(\"PASS: both packs live on the desk\")"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 75b969109b8fdc3cf827ef069be8501a2adae64f

```text
desk discovers: [('delivery_workbench', 'synthesizer'), ('delivery_workbench_actuator', 'actuator')] errors: []
PASS: both packs live on the desk
```
