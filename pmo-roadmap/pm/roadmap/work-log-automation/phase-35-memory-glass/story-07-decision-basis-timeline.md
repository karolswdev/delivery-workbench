# WLA-35-07 - Decision basis timeline

- **Project:** work-log-automation
- **Phase:** 35
- **Status:** done
- **Depends on:** WLA-35-03, WLA-35-05, WLA-35-06
- **Unblocks:** WLA-35-08, WLA-35-09
- **Owner:** unassigned

## Problem

Operators ask 'why did the run do that?' The answer must come from structured facts already recorded — grants, scores, ledgers, receipts, recalled memory — as an audit surface, never a chain-of-thought viewer.

## Scope

- **In:** `delivery-workbench-decision-basis@1` emission for scheduler choices, failure routes, council decisions, verdict outcomes, and terminal transitions; a decision-basis timeline in the Memory pane and session stream.
- **Out:** Any field containing or reconstructing private model reasoning.

## Acceptance criteria

- [ ] Decision-basis documents are emitted for scheduler choices, failure routes, council decisions, verdict outcomes, and terminal transitions that can affect what happens next.
- [ ] Each record contains a stable decision ID, outcome, reason code, rule or score reference, input receipt references, memory references, dissent references where present, and the resulting ledger event.
- [ ] The timeline renders in the Memory pane and existing session stream; selecting a decision highlights the recalled items it referenced and links to the originating grant, check, verdict, or council receipt.
- [ ] The UI states whether a basis is mechanical, agent-reported, panel-derived, or operator-supplied; mechanical checks and model judgments never share the same visual or textual authority label.
- [ ] No API or UI field contains raw chain of thought, hidden thinking, reconstructed reasoning, or a full agent transcript; tests reject fields named or shaped as private reasoning content.
- [ ] Timeline updates reconcile by event ID after SSE reconnect and do not duplicate decisions already received in the snapshot or history fetch.

## Test plan

- **Unit:** covered by the verification command below.
- **Integration:** `bash pmo-roadmap/tests/workbench-explorer.sh`
- **Manual / device:** n/a unless named in the acceptance criteria.

## Notes / open questions

Basis explains a decision through recorded inputs and rules — 'which facts and rules produced this result', nothing more.
