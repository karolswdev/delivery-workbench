# WLA-29-07 - Write the delivery back

- **Project:** work-log-automation
- **Phase:** 29
- **Status:** backlog
- **Depends on:** WLA-29-01, WLA-29-04
- **Unblocks:** WLA-29-08
- **Owner:** unassigned

## Problem

Without write-back, the knowledge layer is a cache, not a memory. The studied
prototype's compounding loop — every delivery records what it touched and
what it learned, and later retrieval finds it — is what makes the second
delivery cheaper than the first. Delivery Workbench already produces the raw
material: run ledgers know what was dispatched, verdicts know what passed,
receipts know what was touched. What is missing is the earned-knowledge
record: a bounded delivery summary plus lessons an agent chose to leave
behind.

The risk is equally clear from the study: an unbounded prose channel with no
provenance. Earned records must ride the WLA-29-01 typed shapes — closed
fields, caps, run-id provenance — in the same spirit as the signals content
boundary, and writing one must never be mistakable for an authoritative act.

## Scope

- **In:** a **delivery record** appended on run/program completion, derived
  from ledger facts (story ids, files touched, verdict outcome, obligations
  raised — identifiers and counts, never diff or output prose); a **lesson**
  record agents may emit through a typed output convention during a run
  (bounded fields: claim, location references resolved against the symbol
  map, confidence tag), persisted to the earned store only when the run
  reaches its terminal or certification seam — abandoned runs leave no
  lessons; retrieval integration so WLA-29-04 packets include relevant
  lessons scored by the same deterministic relevance rules, labeled with
  provenance and age; `dw knowledge lessons` read surface; caps on store
  growth per run (a run may leave at most N lessons, declared in the score
  or program policy).
- **Out:** lessons from humans (they have stories, notes, and canon — this
  channel is for the machine loop); editing or deleting earned records
  (append-only; a wrong lesson is superseded by a later one referencing it);
  any gate, verdict, or evidence role for lessons — a lesson is advice with
  provenance, nothing more; cross-repository lesson sync.

## Acceptance criteria

- [ ] Delivery records derive purely from ledger facts, append on completion
  with run-id and head-SHA provenance, and contain no free prose fields —
  proven by shape tests with per-field caps.
- [ ] Lessons arrive only through the typed output convention, are persisted
  only at the terminal/certification seam, respect the per-run cap, and
  reference locations that resolve (or are marked unresolved) against the
  map — never silently trusted.
- [ ] An abandoned, revoked, or cancelled run persists zero lessons, proven
  by test.
- [ ] Packets for a story near previously delivered work include the relevant
  lessons with provenance and age labels; deleting the earned store yields
  packets that simply lack lessons — no other answer changes anywhere.
- [ ] Supersession works: a lesson may name an earlier lesson it corrects,
  and retrieval prefers the superseding record while keeping the chain
  auditable.
- [ ] No authority surface reads the earned store, re-proven by the
  WLA-29-01 fitness test after this story's wiring.

## Test plan

- **Unit:** record shapes and caps; persistence seam (terminal-only);
  supersession preference; provenance stamping.
- **Integration:** `dw evidence capture` of a fixture program run that emits
  lessons, completes, and a second plan whose packet retrieves them; the
  abandoned-run zero-lesson case.
- **Manual:** read the lessons left by the fixture run and judge whether a
  future implementer would be helped or misled.

## Notes / open questions

Lesson *quality* is unprovable in this story and is not claimed; WLA-29-08's
real run is where lesson usefulness gets its first honest observation. The
per-run cap and typed shape exist so that even useless lessons are cheap and
auditable rather than corrosive.

Whether the earned store should eventually be repository-tracked (so lessons
travel with clones) stays deferred as recorded in the phase status.
