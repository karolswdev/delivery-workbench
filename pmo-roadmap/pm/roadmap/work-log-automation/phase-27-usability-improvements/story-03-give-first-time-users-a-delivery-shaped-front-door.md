# WLA-27-03 - Give first-time users a delivery-shaped front door

- **Project:** work-log-automation
- **Phase:** 27
- **Status:** done
- **Depends on:** WLA-27-01, WLA-27-02
- **Unblocks:** WLA-27-06 through WLA-27-10
- **Owner:** unassigned

## Problem

The shipped application correctly treats missing program configuration as
healthy, but the path from ordinary Delivery Workbench to optional delivery
coordination is described in implementation-shaped concepts. A first-time user
must be able to understand what is available, choose a capability deliberately,
and leave safely without learning the internal protocol.

This story makes the front door and setup flow explain the product in delivery
terms while preserving the no-program invariant and every separate consent
step.

## Scope

- **In:** Workbench first-run and empty states; progressive disclosure of
  vanilla, bounded, and program capabilities; a plain-language setup path that
  starts with what is being delivered; preflight/readiness explanations;
  human CLI status/help pointers into the same task; cancel, save-draft, and
  inspect-technical-details paths; wide and narrow fixtures.
- **Out:** automatic setup, default program creation, provider credential
  acquisition, starting work as a side effect of visiting setup, changing
  capability semantics, or redesigning the detailed plan/team editors owned by
  WLA-27-04 and WLA-27-05.

## Acceptance criteria

- [x] A fresh install opens in a useful healthy state with ordinary roadmap
  work available and optional coordination explained, not as an error or
  required migration.
- [x] Setup begins with delivery scope and desired operating mode; engineering
  artifacts and exact protocol details appear only where needed or when the
  user opens the technical view.
- [x] The flow explains what will be created, what can change, what remains
  disabled, and what separate permission will still be required before any
  work starts.
- [x] Cancel and read-only exploration create no policy, run, grant, ledger,
  observer, notification store, process, network activity, or roadmap change.
- [x] Invalid or incomplete setup identifies the affected delivery decision
  and a corrective next step without dumping raw internal identifiers as the
  primary explanation.
- [x] Workbench and human CLI guidance lead to the same capability choice and
  readiness outcome; machine-facing responses remain unchanged.

## Test plan

- **Unit:** exercise application-view renderers for fresh, vanilla, configured,
  incomplete, invalid, and ready states.
- **Integration:** extend Workbench/CLI smoke coverage and the no-program
  consumer proof to assert read-only arrival, cancel, draft, and preflight
  behavior.
- **Manual / device:** complete the first-arrival and setup journeys by
  keyboard at narrow and wide viewports, including opening and closing exact
  technical details.

## Notes / open questions

Setup may recommend a path but must never infer authority or silently select a
higher capability tier. Starting a delivery remains a separate, explicit act.
