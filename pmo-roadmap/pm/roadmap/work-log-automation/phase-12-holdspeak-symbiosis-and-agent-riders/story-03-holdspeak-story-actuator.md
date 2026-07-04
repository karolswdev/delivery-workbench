# WLA-12-03 - Build the HoldSpeak story actuator

- **Project:** work-log-automation
- **Phase:** 12
- **Status:** backlog
- **Depends on:** WLA-12-02
- **Unblocks:** WLA-12-07
- **Owner:** unassigned

## Problem

Once a meeting is grounded in the roadmap (WLA-12-02), the natural
next want is action: "take WLA-12-05 in-progress", "add a story for
the thing we just decided". Doing that silently from a meeting
would betray both projects' ethos at once. The right shape is the
two consent systems stacked: HoldSpeak actuators only propose —
a human approves, an allow-listed connector executes — and even
then the Delivery Workbench gate still refuses anything the rails
consider dishonest (a done-flip without evidence, above all). An
approved proposal that gets refused by the gate is not a bug; it is
the demonstration that the stack works, and it belongs in the
journal and the evidence.

## Scope

- **In:** An actuator plugin (`kind: actuator`) in the same
  `delivery_workbench_pack.py`, proposing exactly two actions
  against a rails repo: `dw story status <project> <phase> <story>
  <status>` and `dw story create <project> <phase> <title>`. Each
  proposal carries the full `ActuatorProposal` shape (target
  `delivery-workbench`, action verb, human-readable preview, machine
  payload, `reversible: true` — statuses can be flipped back,
  stories deleted before commit). A `WriteConnectorManifest` with
  the `shell:exec` permission whose `allowed_argv_prefixes` admits
  only those two `dw story` argv forms — an approved proposal for
  anything else must be refused by the connector before egress.
  Unit tests for proposal building, the allow-list refusal, and the
  payload-parity path. End-to-end proof through HoldSpeak's
  propose → approve → execute flow against a rails fixture repo,
  including the crown case: an approved `story status … done` for a
  story without evidence, executed, and *refused by the dw gate* —
  captured verbatim. Journal entry written in the moment.
- **Out:** Proposing commits, contract generation, or certification
  (certification is never machine work — canon); `dw evidence`
  or `dw phase` verbs (start narrow, widen only with a recorded
  decision); Slack/aftercare delivery of proposals (HoldSpeak
  already owns that).

## Acceptance criteria

- [ ] The actuator proposes from a real transcript through the
  HoldSpeak host; nothing executes with `allow_actuators` off or
  the actuator absent from `allowed_actuators` (both defaults).
- [ ] An approved in-progress flip executes through the gated
  connector and the rails fixture shows the status change.
- [ ] An approved done-flip on an evidence-less story is executed
  and refused by `dw story status` with its real banner; the
  refusal text appears in the evidence file.
- [ ] A crafted proposal outside the two allowed argv prefixes is
  refused by the connector (`ConnectorOperationRefused`) before any
  egress; unit test proves it.
- [ ] Unit and integration tests run in this repo's CI.

## Test plan

- **Unit:** proposal shape, allow-list refusal, parity-hash
  mismatch abort.
- **Integration:** scripted propose → approve → execute against a
  rails fixture repo, green path and both refusal paths.
- **Manual / device:** the flow once through the live Desk
  ("Pending actions" panel); screenshot under evidence `assets/`.

## Notes / open questions

- `reversible: true` is honest for status flips and pre-commit
  story files, but say in the preview *what* reversal means so the
  approver is never guessing.
- The connector must run `dw` from the target repo's own
  `.githooks/` (or installed `dw`) — resolve which and record it.
