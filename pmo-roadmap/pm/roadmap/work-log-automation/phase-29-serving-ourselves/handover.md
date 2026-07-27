# Phase 29 handover

**State at close (2026-07-27):** 9/9 done, suite 604 green, `dw verify`
clean, phase frozen by final-summary.md. Phases 25-29 remain unreleased;
v1.14.0 is still the published version. Landing/release is a deliberate
separate decision, unchanged from the phase-28 handover.

## The obvious next work, and where it lives

1. **The friction backlog.** Evidence-story-08 carries a 17-entry ledger
   from the first real program run. The structural items: automatic lesson
   write-back fires only inside the commit-capable delivery bundle, so a
   no-commit grant (the safest kind) can never leave lessons — decide
   whether the terminal seam should persist them under `evidence:materialize`
   authority; a guarded operator act to close stranded claims so a
   crash-dirty run is recoverable; compiler/conductor parity for workflow
   node types (checkpoint nodes compile but do not conduct); driver env
   allowlists (`NODE_EXTRA_CA_CERTS`, lowercase proxy variants);
   validate-time cross-checks (rubric mechanical facts vs the bound
   workflow's check nodes; grant budgets vs team size).
2. **Second real run, cheaper.** The exam cost thirteen grants because
   every defect class was new. The machinery fixes are all shipped; a
   second program on the next maintenance story should measure the
   compounding claim directly — and its packet will retrieve whatever
   lessons the write-back decision above makes possible.
3. **Conversational intake** stays deferred by phase-status decision:
   a Scope-Chat-shaped front door drafting phases/stories through the
   guarded mutation surface, now that WLA-29-08 proved the engine.

## Operational notes for the next session

The worktree `core.hooksPath` friction is fixed by WLA-29-09 itself
(`dw doctor --fix-hooks`; same-clone absolute is healthy). Supervise the
conductor with stdin redirected (`< /dev/null`) out of habit even though
the drivers now detach child stdin. Under a MITM-proxy sandbox, launch the
conductor proxy-free until the allowlist follow-up lands. The knowledge
map goes stale with every commit by design — `dw knowledge refresh` before
grounding or planning is the normal rhythm.
