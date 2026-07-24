# Delivery setup and first arrival

Delivery Workbench opens with useful ordinary work. Optional coordination is a
choice, not an installation error, migration, or prerequisite.

The first-arrival surface answers two questions in order:

1. What are you delivering?
2. How much coordination does this delivery need?

Exact score, compiler, hash, capability, and policy information remains
available under **Technical details**. It does not lead the task.

This application view implements the `healthy-first-arrival`,
`deliberate-capability-choice`, and `preflight` journeys in the
[whole-task usability contract](./usability-journeys.md). It changes no
eligibility, permission, persistence, or runtime rule.

## One shared read model

`delivery_setup.build_delivery_setup` returns
`delivery-workbench-delivery-setup` schema version 1. It composes facts from
three existing, unchanged sources:

| Source | Delivery question it answers |
|---|---|
| `status.build_status` | Which roadmap project and current work are ready? |
| `orchestration.score_inventory` | Is a valid one-delivery plan available to review? |
| `program_studio.build_program_studio` | Is optional program policy absent, draftable, or configured? |

The projection owns presentation policy only. It cannot create or modify any
of those sources.

The Workbench reads it through
`GET /api/delivery-setup?project=<slug>`. Human `dw status` adds a compact
pointer to the choice, and `dw setup [project] [--technical]` renders the same
choice labels and readiness. `dw status --json`, MCP status, and all existing
machine documents remain unchanged.

## The three choices

No choice is preselected in Workbench.

| Choice | Meaning now | Later boundary |
|---|---|---|
| Continue with the roadmap | Open current ordinary work. No optional setup is needed. | None. |
| Review one bounded delivery | Inspect one delivery plan, its order, review, limits, and stops. | A separate exact start review is still required before a run or process exists. |
| Set up an optional delivery program | Seed an unsaved delivery-plan draft with the selected project and phase. | Saving requires the existing exact preview and confirmation; a separate reviewed program start is still required before work begins. |

Every review states:

- what setup creates;
- what could change only after a later confirmation;
- what remains disabled; and
- what separate permission is still needed.

A configured optional program never displaces the ordinary choice. A missing
program remains a healthy `ready-to-set-up` state.

## Workbench flow

The overview leads with the readiness answer, current work, and two plain
actions:

- **Open current work**
- **Review delivery options**

The prior rail, workspace, contract, gate, and exact-command panel remains
available under **Technical details**.

`#/program-studio` is the delivery-choice route:

1. select the roadmap project and phase;
2. compare all three modes;
3. review the selected mode's effects and remaining permission;
4. continue, compare again, or leave.

The optional technical editor remains under explicit family routes such as
`#/program-studio/program`. Entering it from setup seeds only browser memory.
The tracked draft does not exist until the person reviews and confirms the
existing Program Studio save preview.

The bounded path opens delivery readiness first. A valid preflight leads with
work and order, team, review, permission, limits and stops, and one next step.
Hashes, exact capability/profile names, scheduling simulation, output lineage,
and compiler routes sit under **Technical details**. An invalid preflight leads
with the affected delivery decision and one correction; raw pointers and codes
remain in the technical view.

## Safe exploration

Building, rendering, comparing, opening details, and leaving all report these
effects as false:

| Effect | Setup/exploration |
|---|---|
| Start work or a process | false |
| Write tracked policy or roadmap files | false |
| Write run state or a ledger | false |
| Create a grant | false |
| Start an observer or send a notification | false |
| Use the network | false |

The browser flow has no POST, event stream, timer poller, or local-storage
write. **Leave for now** clears the unsaved browser handoff and returns to the
ordinary overview.

Only two downstream acts can persist anything:

- Program Studio's already-guarded save preview can write one reviewed tracked
  policy after exact confirmation.
- Existing bounded/program start boundaries can create their finite authority
  only after their own fresh review and explicit confirmation.

Neither is implied by choosing a card or visiting a route.

## Incomplete and invalid states

The first explanation names the delivery decision, not an internal identifier:

- no selected project → choose the delivery scope;
- no valid bounded plan → create or choose a valid delivery plan;
- no current work → choose current roadmap work;
- unhealthy roadmap/repository → resolve the named readiness issue.

Unavailable ordinary/program continuations are disabled. The bounded option may
still open delivery plans as its corrective action. Exact compiler targets are
available under **Technical details**.

## Proof

The behavior is pinned at four levels:

```bash
python3 pmo-roadmap/tests/dw-core-tests.py DeliverySetupTest
bash pmo-roadmap/tests/workbench-explorer.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
python3 pmo-roadmap/tests/autonomous-program-packaged-exam.py
```

The focused unit contract covers configured, missing, invalid, incomplete, and
ready states plus CLI/HTTP parity and repeated no-write reads. The explorer
checks the HTTP and installed CLI surfaces. The viewport suite captures both
390×844 and 1440×900 setup/review states and statically forbids mutation/live
browser primitives in the front-door renderer. The fresh-wheel no-program
consumer proves the same three choices while optional policy and runtime stores
remain absent.
