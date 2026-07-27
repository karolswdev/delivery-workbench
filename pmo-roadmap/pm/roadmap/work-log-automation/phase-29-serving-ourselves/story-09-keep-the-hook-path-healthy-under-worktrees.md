# WLA-29-09 - Keep the hook path healthy under worktrees

- **Project:** work-log-automation
- **Phase:** 29
- **Status:** done
- **Depends on:** -
- **Unblocks:** -
- **Owner:** unassigned

## Problem

Agent tooling that creates git worktrees keeps rewriting `core.hooksPath`
from the relative `.githooks` to an absolute path. `dw doctor` treats the
absolute form as a FAIL and `dw status`/`dw step` escalate it to a blocking
`repair-rails` action, so every worktree spawn costs an operator a doctor
lease plus a manual `git config core.hooksPath .githooks`. This recurred
four times while delivering this phase and is recorded in the WLA-29-08
friction ledger. The gate itself never stopped working — the absolute path
points at the same hooks — so the pain is a health check stricter than the
actual risk, paid on every worktree.

## Scope

- **In:** make the rails tolerant of an absolute `core.hooksPath` that
  resolves to this clone's own `.githooks` directory: `dw doctor` reports it
  healthy with a normalization hint instead of FAIL, and `dw status`/`dw
  step` stop escalating it as blocking repair; a `dw doctor --fix-hooks`
  (or equivalently scoped, explicitly invoked repair) that rewrites the
  value back to the relative form; a regression test covering relative,
  same-clone absolute, and foreign-path forms (a foreign path stays FAIL);
  documentation of the rule in the doctor section of the docs.
- **Out:** preventing external tools from rewriting the value (not ours to
  control); watching or hooking worktree events; any change to hook
  execution, gate semantics, or what happens on a genuinely wrong hooks
  path — foreign paths must keep failing loudly.

## Localization hints

- **Affected files:**
  - `pmo-roadmap/lib/dw_pmo/doctor.py`
- **Target symbols:**
  - `run_doctor`

## Acceptance criteria

- [ ] `dw doctor` reports healthy (with a normalization hint) when
  `core.hooksPath` is an absolute path resolving to this clone's
  `.githooks`, and still FAILs on any path that does not resolve there.
- [ ] `dw status` and `dw step` no longer emit a blocking `repair-rails`
  action for the same-clone absolute form.
- [ ] An explicitly invoked repair normalizes the value back to `.githooks`
  and is covered by test; nothing normalizes implicitly.
- [ ] Regression tests cover relative, same-clone absolute, and foreign
  forms on both the doctor and status paths.
- [ ] The rule is documented where the doctor checks are documented.

## Test plan

- **Unit:** the three-form classification; the explicit repair.
- **Integration:** `dw evidence capture` of the regression test module; a
  planted foreign path still fails.
- **Manual:** create a worktree, observe the absolute rewrite, confirm
  doctor stays healthy and the explicit repair restores the relative form.

## Notes / open questions

Authored as the target story for WLA-29-08's real autonomous program run —
deliberately maintenance-scale: real code, real tests, bounded blast
radius. The exact file/symbol hints above were grounded against the symbol
map at authoring time; the implementing agent must re-verify (the hints are
advisory by contract).

Delivered by the autonomous program run `program-a8b7131ba635a59ac3162dec`
(attempt 13 of WLA-29-08's exam): implemented by a live claude agent in an
isolated worktree from a knowledge packet carrying this story's verified
hints, mechanically checked by the focused doctor/status/step regression
(pass), and independently certified by a live codex verdict — pass on all
four rubric criteria under the cross-provider diversity rule. The operator
applied the certified candidate, re-ran the full suite (604 tests green),
and verified the behavior live: a same-clone absolute `core.hooksPath` now
reads healthy with a normalization hint, `--fix-hooks` restores the
relative form, and a foreign path still fails. The evidence file captures
the regression run plus the live doctor demonstration.
