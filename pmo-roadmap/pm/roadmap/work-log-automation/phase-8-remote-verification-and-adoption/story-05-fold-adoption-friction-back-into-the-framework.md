# WLA-8-05 - Fold adoption friction back into the framework

- **Project:** work-log-automation
- **Phase:** 8
- **Status:** done
- **Depends on:** WLA-8-04
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

A friction log that nobody acts on is theater. The value of the
external adoption (WLA-8-04) is realized only when each finding
either changes the framework, changes the docs, or is explicitly
declined with a reason — and the fix is proven the same way the
friction was found.

## Scope

- **In:** Triage every entry in `adoption-friction.md` into
  fix-now / defer / decline with rationale recorded in the story
  file; implement all fix-now items (code, install/adopt scripts, or
  docs as each demands); re-run the failing step from the friction
  log against the fixed framework to prove each fix; add regression
  coverage where the friction revealed a testable gap (extend the
  relevant suite under `pmo-roadmap/tests/`).
- **Out:** Deferred items beyond recording them (they become
  candidate stories for a future phase), redesigns that exceed the
  papercut scale — those get written up as proposals instead.

## Acceptance criteria

- [ ] Every friction entry has a triage verdict and rationale; none
  are silently dropped (counts match the WLA-8-04 log).
- [ ] Each fix-now item's original failing step now succeeds,
  demonstrated in captured evidence.
- [ ] Test suites extended where applicable and green; docs-lint and
  canon-lint pass after doc changes.
- [ ] Deferred/declined items are listed in the phase status file's
  decisions section.

## Test plan

- **Unit:** new or extended cases in the touched suites.
- **Integration:** full `pmo-roadmap/tests/` relevant suites green;
  re-run of the WLA-8-04 failing steps.
- **Manual / device:** spot-check the worst blocker end-to-end.

## Notes / open questions

- If WLA-8-04 genuinely surfaces no friction, this story shrinks to
  recording that outcome and hardening the claim (e.g. a second
  adoption target) — decide at triage time.
