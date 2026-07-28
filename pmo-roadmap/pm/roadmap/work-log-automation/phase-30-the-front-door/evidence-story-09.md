# Evidence - WLA-30-09

- **Story:** WLA-30-09 - Let the safest runs leave lessons
- **Status:** done
- **Date:** 2026-07-27

## Proof

No-commit grants can now leave lessons. A new narrow capability,
`knowledge:lesson-writeback`, is requestable by checkpointed no-commit
programs and carries its own finite budget (`max_lesson_writebacks`,
one unit reserved per certified handoff; `max_lessons` stays the
per-handoff record cap). Capability-set assertions prove the bit grants
no integration, contract, certification, commit, push, or roadmap
authority. Lessons persist at exactly one terminal — frontier
`story-certified` with stop `integration-required`, grant holding the
capability, at least one typed lesson artifact — and at no other state:
the negative matrix covers advisory, checkpoint, paused, expired,
exhausted, revoked, cancelled, complete, running, failed, refused,
lost, malformed, and uncertified. Two new append-only earned-record
kinds (`certified-handoff-lesson`, `lesson-delivery-observation`) carry
a closed delivery-state vocabulary — `certified-not-integrated`,
`confirmed`, `superseded` — and the existing commit-capable delivery
path appends the confirming record when the candidate lands. Replay is
idempotent by construction: the terminal receipt id is a SHA-256 over
run, story, candidate subject, green verdict receipt, lesson-emitter
receipts, and grant hash; a crash between persist and acknowledgment
replays onto the same claim, appends nothing, and spends no second
budget unit. Knowledge packets retrieve the lesson with its
delivery-state label preserved, and the knowledge-never-authorizes
fitness suite now covers the new record kinds. Implementation by Sol
(GPT-5.6) under orchestration in an isolated worktree; ported to main
and re-verified there.

Per the story's test plan, the live manual proof belongs to the
WLA-30-10 exam; the captures here are the two-run fixture and negative
matrix (**6 lesson tests**), the existing write-back regression suite,
and the **full core suite** via `tests/run-core-tests.py` (final
capture, machine-verified exit code).

### Captured run — 2026-07-28T00:34:18Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/lesson_writeback_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** adef4797bccab8301cdfcae5d926d449cb1c8dc1

```text
test_confirm_and_supersede_are_append_only_closed_observations (__main__.LessonWritebackTest) ... ok
test_crash_replay_receipt_is_idempotent_and_budget_stays_one (__main__.LessonWritebackTest) ... ok
test_every_non_success_terminal_persists_nothing (__main__.LessonWritebackTest) ... ok
test_new_record_kinds_remain_unfit_for_authority (__main__.LessonWritebackTest) ... ok
test_no_commit_capability_is_narrow_and_independently_budgeted (__main__.LessonWritebackTest) ... ok
test_two_run_packet_keeps_certified_not_integrated_label (__main__.LessonWritebackTest) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.018s

OK
```

### Captured run — 2026-07-28T00:34:18Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/knowledge_writeback_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** adef4797bccab8301cdfcae5d926d449cb1c8dc1

```text
test_delivery_shape_is_only_ledger_identifiers_and_counts (__main__.KnowledgeWritebackTest) ... ok
test_lesson_inventory_lists_provenance_and_supersession (__main__.KnowledgeWritebackTest) ... ok
test_only_success_terminal_persists_and_cap_is_per_run (__main__.KnowledgeWritebackTest) ... ok
test_second_packet_prefers_superseding_lesson_and_keeps_chain (__main__.KnowledgeWritebackTest) ... ok
test_terminal_retry_deduplicates_exact_records (__main__.KnowledgeWritebackTest) ... ok
test_typed_output_is_closed_and_bounded (__main__.KnowledgeWritebackTest) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.014s

OK
WLA-29-07 EVIDENCE {"abandoned_lessons": 0, "age_label": "recorded-at:2026-07-26T13:00:00Z", "authority": false, "delivery_records": 2, "kind": "delivery-workbench-writeback-evidence", "per_run_cap": 1, "provenance_head": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "retrieved_lessons": 1, "retrieved_run": "program-222222222222222222222222", "superseding_hash": "sha256:697b27233a10ec9616a553af1633bc6e14cf6504aa8e2e589fa48c2145bbb071", "supersession_chain": ["sha256:f6277a538764a430afc124627110e1ee31c1fd8e5365763a10f472d313bef5f5"], "terminal_completion": "persisted", "unresolved_marked": true}
```

### Captured run — 2026-07-28T00:34:28Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** adef4797bccab8301cdfcae5d926d449cb1c8dc1

```text
run-core-tests: 650 units across 8 shards + 1 serial
  shard 0:  83 tests in   88.0s  ok
  shard 1:  84 tests in   85.5s  ok
  shard 2:  84 tests in  107.6s  ok
  shard 3:  84 tests in   98.4s  ok
  shard 4:  86 tests in  100.7s  ok
  shard 5:  79 tests in  113.7s  ok
  shard 6:  79 tests in  107.1s  ok
  shard 7:  79 tests in  106.9s  ok
  shard 8:   1 tests in    2.3s  ok
run-core-tests: 659 tests in 116.0s (OK)
```
