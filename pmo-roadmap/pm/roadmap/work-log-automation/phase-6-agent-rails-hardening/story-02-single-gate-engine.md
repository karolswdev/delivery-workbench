# WLA-6-02 - Unify the commit gate into a single dw gate engine

- **Project:** work-log-automation
- **Phase:** 6
- **Status:** done
- **Depends on:** WLA-6-01
- **Unblocks:** WLA-6-03, WLA-6-04, WLA-6-08
- **Owner:** unassigned

## Problem

The structural commit rules are implemented three times in two languages:
awk/bash in `hooks/pre-commit`, awk in `hooks/post-commit`, and Python in
`bin/dw`. The copies have already drifted, and the drift includes real
bypasses of the framework's only hard checks:

- Status-synonym bypass: `dw` treats `done|complete|closed|shipped` as done
  and requires evidence for all of them, but the hook only detects the
  literal `+- **Status:** done`. Writing `Status: complete` flips a story
  done in `dw`'s eyes while skipping the hook's atomicity and
  evidence-pairing gates entirely.
- Evidence-number padding drift: the hook derives `evidence-story-<n>.md`
  verbatim from the story filename while `dw` always zero-pads; a
  `story-1-foo.md` satisfies one tool and fails the other.
- Evidence deletion is impossible: staged deletions (the hook's
  `--diff-filter` includes `D`) always trip the orphan-evidence check, with
  no documented escape hatch other than the forbidden `--no-verify`.
- Rename/reformat false positives: renaming or reformatting an already-done
  story re-emits the `+- **Status:** done` line in the cached diff and
  demands fresh evidence.
- Robustness gaps: unquoted `$SHIPPED_STORIES`/path word-splitting, `grep -qx`
  without `-F` treating paths as regexes, `- [X]` (capital X) counted
  neither as checked nor unchecked, `PMO_WORK_LOG_DIR` honored from the
  environment by the readers but ignored by the hooks, and mtime-based
  contract freshness that breaks under clock skew.

Every new rule multiplies this drift. There must be exactly one
implementation of the gate.

## Scope

- **In:** A `dw gate` subcommand (built on the `dw_pmo` core boundary from
  WLA-5-02) that implements every structural check the hook performs today:
  contract presence, freshness, checkbox validation, shipped-story
  detection, one-story-per-commit atomicity, forward and reverse evidence
  pairing, and work-log capture preconditions. `hooks/pre-commit` becomes a
  thin shim that execs `dw gate --hook pre-commit` and fails closed with a
  clear message if `python3` is unavailable. Machine-readable output:
  `dw gate --porcelain` reports which stories were considered shipped,
  which rule fired, and the exact remediation artifact as stable
  key-value lines. Fix the enumerated bug family with one shared status
  vocabulary, zero-padded evidence resolution that accepts both spellings
  on read, explicit handling for staged evidence deletions and renames of
  already-done stories, quoted/`-F` string handling, capital-X checkbox
  acceptance, and a single documented `PMO_WORK_LOG_DIR` precedence
  (config over environment over default) applied identically by hooks,
  readers, and `dw`.
- **Out:** Contract content redesign and index-tree freshness (WLA-6-03);
  evidence content linting (WLA-6-04); new rules beyond parity plus the
  listed fixes; removing the bash hooks from distribution.

## Acceptance criteria

- [ ] `hooks/pre-commit` contains no structural rule logic; all checks run
  through `dw gate`, and the `pre-commit.config`/`pre-commit.local` seams
  keep working (covered by a test).
- [ ] A parity regression suite runs the same staged fixtures through the
  installed shim and through `dw gate` directly and asserts identical
  verdicts, including: synonym statuses, unpadded story numbers, staged
  evidence deletion for a non-regressing story, rename of a done story,
  paths with spaces, and capital-X checkboxes.
- [ ] Staged deletion of an evidence file whose story is not simultaneously
  regressed passes the gate; a deletion that orphans a done story is
  blocked with a message naming the story.
- [ ] `dw gate --porcelain` output is documented in the framework README and
  asserted verbatim in tests.
- [ ] `PMO_WORK_LOG_DIR` set only in the environment produces the same
  write and read locations across pre-commit, post-commit, `work-log-read`,
  and `dw context`.

## Test plan

- **Unit:** Core gate-rule tests over staged-diff fixtures in the `dw_pmo`
  test suite, at least one per fixed bug.
- **Integration / Cypress:** Extended `pmo-roadmap/tests/roadmap-cli.sh`
  plus a new `pmo-roadmap/tests/gate-parity.sh` driving real `git commit`
  attempts through the installed shim.
- **Manual / device:** Trigger each block on this repo and confirm the
  remediation text is sufficient to recover without reading framework
  source.

## Notes / open questions

Coordinate with WLA-5-02: the core extraction should land first or in the
same effort, so the gate engine is a consumer of `dw_pmo`, not a fourth
implementation. The fallback question is settled as fail-closed: python3
becomes a hard runtime dependency of the gate, and the docs must stop
claiming "pure bash, no external runtime dependencies."
