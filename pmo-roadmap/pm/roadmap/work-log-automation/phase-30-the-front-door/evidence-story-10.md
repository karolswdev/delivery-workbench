# Evidence - WLA-30-10

- **Story:** WLA-30-10 - Pass the empty-directory exam
- **Status:** done
- **Date:** 2026-07-27

## Proof

The empty-directory exam passed on attempt 5 — and the four attempts
before it are the strongest part of the evidence, because each one
forced a real product fix that now ships:

1. **Attempt 1** (1 grant): the generated bundle's only builtin check,
   `rail-status`, is the one name the conductor deliberately refuses.
   Fixed: the scaffold's check vocabulary became the conductable
   governance guard `diff-scope`, and whole-bundle validation gained
   the `unconductable-builtin-check` parity diagnostic.
2. **Attempt 2** (2 grants): reached the certified handoff — live
   claude implemented, live codex certified — but exposed that a
   passing first verdict routed into the repair seat (whose honest
   "nothing to repair" refusal killed the run) and that zero lessons
   could persist because no lesson output existed. Also hit the
   stale-baseline-workspace friction from a recreated repo path
   (recorded; same family as the deferred stranded-claim recovery).
3. **Attempt 3** (2 grants): the implementer authored a perfect lesson
   document into its final message — write-mode claude-exec had no
   materialization channel for non-diff outputs at all. Fixed: write
   mode mirrors the read-only response contract; then one sentence of
   prose before the JSON cost a second grant, so the JSON response
   contract now deterministically takes the final well-formed document.
4. **Attempt 4** (2 grants): the first genuinely red live verdict
   (codex vetoed scope-and-quality: tests bypassed the CLI) aggregated
   to `needs-repair` — a rubric vocabulary value the closed workflow
   route table cannot name — and blocked a run with a declared repair
   leg. Fixed: the conductor maps every aggregate into the workflow
   vocabulary (red routes as fail). Grant 2 then blocked honestly on a
   REAL defect: the candidate imported pytest and baseline subtraction
   classified the failures as introduced — the phase-29 hard rule
   working on real bad code. Operator response: a conversation
   revision naming the exact stdlib-only test command.
5. **Attempt 5** (1 grant): the clean journey. `dw init` → the
   Scope-Chat proposal → scaffold → both workbench reviews → setup
   lease applied atomically (approval 1) → gated adopt commit → grant
   issued (approval 2) → live claude implemented, diff-scope and the
   declared stdlib regression passed, live codex certified → certified
   handoff with no commit authority → one lesson persisted
   (`certified-not-integrated`) → operator integrated with
   `git apply --index`, re-ran the declared tests (3 passing),
   hand-certified the contract (approval 3), committed → `dw verify:
   ok` over the whole exam history → the second-pass grounded packet
   for URL-1-02 retrieves the lesson with its label → cold-install
   repetition green in a second neutral directory.

The complete human-readable transcript is
[assets/exam-transcript.md](./assets/exam-transcript.md). The captured
run below is the machine-checked summary: it asserts every acceptance
criterion from the exam repository's own artifacts — gated commits on
the release-candidate wheel, two declared provider families
(anthropic implementer, openai verifier), exactly one grant in the
successful attempt with unknown provider cost reported unknown, six
granted capabilities with the permanent exclusions enumerated inside
the grant itself, the persisted and retrieved lesson, three
hand-certified archived contracts with `dw verify` green, and the
cold-install repetition — exit 0.

Grant ledger across the campaign: 8 grants over five attempts against
Phase 29's 13-grant baseline for one story; the successful attempt
used 1. Friction for the next phase, recorded: stale baseline
workspaces from recreated repository paths need a guarded janitorial
act (with stranded-claim recovery), and the localization-hint syntax
still only self-documents after failure (bit again this exam).

### Captured run — 2026-07-28T02:37:42Z

- **Command:** `/usr/bin/python3 /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/c4dc647a-d1b5-41ba-83af-e7d70e987de9/scratchpad/exam-summary.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c754f5ed47fa668fa6f29b1d0adf305817d02ec9

```text
== 1. journey: empty directory on a release-candidate wheel ==
wheel: delivery_workbench-1.14.0-py3-none-any.whl
exam commits: 3 | adopt + story + hints, all gated

== 2. cross-provider families, evidenced ==
roles dispatched: ['implementer', 'verifier']
profile families: {'claude-implementer': 'anthropic', 'codex-verifier': 'openai'}

== 3. the successful attempt used ONE grant; budgets honest ==
grants in the attempt-5 repository: 1
unknown provider cost reported unknown, never zero

== 4. no excluded authority in the grant ==
granted capabilities: ['agent:dispatch', 'check:execute', 'knowledge:lesson-writeback', 'program:select', 'verdict:issue', 'workspace:write']
permanent exclusions enumerated inside the grant itself

== 5. the no-commit run left a lesson a later packet retrieves ==
certified-handoff lessons: 1 | state: certified-not-integrated
second-pass grounded packet carries the lesson, label preserved

== 6. certification hand-checked, commit human, verify green ==
dw verify: ok (3 commits verified, 0 pre-epoch skipped)
hand-certified contracts archived: 3

== 7. cold-install repetition ==
second neutral directory: verdict ready, setup-project next

exam summary: every criterion machine-checked; exit 0
```

### Captured run — 2026-07-28T02:38:45Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c754f5ed47fa668fa6f29b1d0adf305817d02ec9

```text
run-core-tests: 680 units across 8 shards + 1 serial
  shard 0:  84 tests in   82.0s  ok
  shard 1:  93 tests in   70.9s  ok
  shard 2:  87 tests in   80.1s  ok
  shard 3:  87 tests in   91.0s  ok
  shard 4:  89 tests in   83.5s  ok
  shard 5:  83 tests in   86.9s  ok
  shard 6:  85 tests in  108.3s  ok
  shard 7:  83 tests in   89.2s  ok
  shard 8:   1 tests in    2.1s  ok
run-core-tests: 692 tests in 110.3s (OK)
```
