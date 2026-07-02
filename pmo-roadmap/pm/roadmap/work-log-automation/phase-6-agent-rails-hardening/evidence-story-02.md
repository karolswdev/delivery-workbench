# Evidence - WLA-6-02 - Unify the commit gate into a single dw gate engine

- **Story:** [story-02-single-gate-engine](./story-02-single-gate-engine.md)
- **Status:** done
- **Date:** 2026-07-02

## What shipped

- `pmo-roadmap/lib/dw_pmo/gate.py` (456 lines): the single
  implementation of every structural commit rule — contract
  presence/freshness/checkboxes, shipped-story detection, atomicity,
  forward and reverse evidence pairing, and work-log capture
  preconditions — exposed as `dw gate [--porcelain]`.
- `hooks/pre-commit` (339 lines, zero rule logic): a shim that wires
  `pre-commit.config`, invokes the gate (fail-closed message naming the
  python3 dependency when it is missing, testable via
  `PMO_GATE_PYTHON`), rebuilds the `pre-commit.local` seam variables
  from the gate's porcelain output, captures the consented work-log
  payload, and cleans up on success. `grep -n 'Status\|evidence-story'
  hooks/pre-commit` finds no rule logic — only the payload mechanics.
- Detection redesign that fixes the drift-bug family structurally:
  shipped = story's `**Status:**` header not-done in `HEAD` and done in
  the index, using the shared `DONE_STATUSES` vocabulary. This closes
  the synonym bypass (`complete` now gates like `done`), the
  rename/reformat false flips (HEAD-vs-index comparison, `-M` rename
  pairing), and grep-on-diff fragility. Evidence numbers compare as
  integers (padding drift closed); staged paths parse NUL-separated
  (spaces safe); `- [X]` counts as checked.
- Evidence lifecycle rules per the story: deletions pass unless they
  orphan a story that remains done in the index (blocked with the
  story named); modified evidence is legal while its story is done;
  added evidence still requires a same-commit flip.
- Unified config precedence: `EXPECTED_BOXES`, `PMO_WORK_LOG_ENABLED`,
  and `PMO_WORK_LOG_DIR` resolve as config > environment > default,
  applied identically by the gate, both hooks, `work-log-read`,
  `work-log-summarize`, and `dw context` (`work_log_root(root)` parses
  simple config assignments).
- Self-hosting fixed natively: the gate derives the roadmap prefix from
  `dw_pmo.roadmap_dir`, so the nested `pmo-roadmap/pm/roadmap` layout
  is enforced without duplication — this repo's
  `.githooks/pre-commit.local` shrank from 80 lines of copied rule
  logic to a comment, exactly as predicted in evidence-story-01
  friction item 2. Friction item 4 (wrong rules-doc path in the banner)
  is also fixed: the gate resolves the actual canon location.
- `dw gate --porcelain` documented in `pmo-roadmap/README.md`
  ("The commit gate (`dw gate`)") and asserted verbatim in a unit test.
- The freshness check remains mtime-based by design; index-tree
  freshness is WLA-6-03. `os.path.getmtime` replaces the BSD/GNU `stat`
  branch, removing that portability seam.

## Command output

Unit suite (28 cases: 12 core + 16 gate, at least one per fixed bug —
synonym, padding both directions, rename, spaces, capital-X, deletion
orphan/regressed/stray, added orphan, modified-evidence, atomicity +
BUNDLE-OK, config-beats-env for EXPECTED_BOXES and PMO_WORK_LOG_DIR,
work-log preconditions, porcelain verbatim):

```text
$ python3 pmo-roadmap/tests/dw-core-tests.py
Ran 28 tests in 2.272s
OK
```

Parity suite — 16 scenarios, each verdict asserted twice (installed
shim via real `git commit`, and `dw gate` directly) plus seam and
fail-closed checks:

```text
$ pmo-roadmap/tests/gate-parity.sh
gate-parity.sh: ok
```

Scenario map: base pass; single flip pass; synonym flip w/o evidence
FAIL (bypass closed); unpadded story + padded evidence pass; unpadded
evidence pass; rename of done story pass; "story-05-has space.md" flip
pass; capital-X pass; unchecked FAIL; missing contract FAIL; multi-flip
FAIL then BUNDLE-OK pass; evidence deletion orphaning done story FAIL
(message names the story); deletion with regressed story pass; added
orphan evidence FAIL; config seam EXPECTED_BOXES=8 (7 boxes FAIL /
8 boxes pass, gate and shim agreeing because the gate parses the same
config); local seam blocks via `fail` and reads `$SHIPPED_COUNT`;
`PMO_GATE_PYTHON=/nonexistent` fails closed naming python3; env
`PMO_WORK_LOG_DIR` honored identically by pre-commit capture,
post-commit append, `work-log-read --list`, and `dw context`.

Full validation set:

```text
bash -n <all shipped scripts + gate-parity.sh>  -> ok
python3 -m py_compile pmo-roadmap/bin/dw        -> ok
python3 -m compileall -q pmo-roadmap/lib/dw_pmo -> ok
pmo-roadmap/tests/adoption-discovery.sh         -> adoption-discovery.sh: ok
pmo-roadmap/tests/gate-parity.sh                -> gate-parity.sh: ok
pmo-roadmap/tests/roadmap-cli.sh                -> roadmap-cli.sh: ok
pmo-roadmap/tests/work-log-mvp.sh               -> work-log-mvp.sh: ok   (drives the new shim
                                                   through real, aborted, and amended commits)
```

Manual block trigger on this repo (test plan), non-consuming preflight:

```text
$ .githooks/dw gate      # contract with '- [ ] three'
✗ .tmp/CONTRACT.md still has unchecked items.
    5: - [ ] three
  To proceed: Flip every '- [ ]' to '- [x]' only after honestly verifying each rule.
exit=1
```

The commit that ships this story is itself the final proof: WLA-6-02
flips to done with this evidence file staged, verified by `dw gate`
natively on the nested roadmap (the old `pre-commit.local` duplication
is deleted in the same commit), and the success banner reads
"evidence verified by dw gate".

## Acceptance criteria check

- [x] `hooks/pre-commit` contains no structural rule logic; every check
  runs through `dw gate`; the config and local seams are covered by
  parity scenarios S13/S14.
- [x] `pmo-roadmap/tests/gate-parity.sh` asserts identical shim/gate
  verdicts across the required fixture set (synonyms, unpadded numbers,
  evidence deletion, rename of a done story, paths with spaces,
  capital-X).
- [x] Evidence deletion passes when it does not orphan a done story
  (regressed-story and stray-evidence cases) and is blocked naming the
  story when it would (unit + parity).
- [x] Porcelain output documented in `pmo-roadmap/README.md` and
  asserted verbatim in `test_porcelain_verbatim`.
- [x] Env-only `PMO_WORK_LOG_DIR` produces identical write/read
  locations across pre-commit, post-commit, `work-log-read`, and
  `dw context` (parity scenario S16).
