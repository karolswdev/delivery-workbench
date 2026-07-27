# Evidence - WLA-29-07

- **Story:** WLA-29-07 - Write the delivery back
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-27T04:15:40Z

- **Command:** `sh -c python3 -c "import importlib.util,pathlib,unittest; p=pathlib.Path(\"pmo-roadmap/tests/dw-core-tests.py\").resolve(); s=importlib.util.spec_from_file_location(\"dwcore_evidence\",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); r=unittest.TextTestRunner(verbosity=1).run(m.ProgramConductorTest(\"test_cross_phase_continuation_carries_obligation_and_completes_scope\")); raise SystemExit(0 if r.wasSuccessful() else 1)" && python3 pmo-roadmap/tests/knowledge_writeback_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 10b8e03df632583ec8febf92c01f1285b9b0e11b

```text
.
----------------------------------------------------------------------
Ran 1 test in 13.809s

OK
test_delivery_shape_is_only_ledger_identifiers_and_counts (__main__.KnowledgeWritebackTest.test_delivery_shape_is_only_ledger_identifiers_and_counts) ... ok
test_lesson_inventory_lists_provenance_and_supersession (__main__.KnowledgeWritebackTest.test_lesson_inventory_lists_provenance_and_supersession) ... ok
test_only_success_terminal_persists_and_cap_is_per_run (__main__.KnowledgeWritebackTest.test_only_success_terminal_persists_and_cap_is_per_run) ... ok
test_second_packet_prefers_superseding_lesson_and_keeps_chain (__main__.KnowledgeWritebackTest.test_second_packet_prefers_superseding_lesson_and_keeps_chain) ... ok
test_terminal_retry_deduplicates_exact_records (__main__.KnowledgeWritebackTest.test_terminal_retry_deduplicates_exact_records) ... ok
test_typed_output_is_closed_and_bounded (__main__.KnowledgeWritebackTest.test_typed_output_is_closed_and_bounded) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.010s

OK
WLA-29-07 EVIDENCE {"abandoned_lessons": 0, "age_label": "recorded-at:2026-07-26T13:00:00Z", "authority": false, "delivery_records": 2, "kind": "delivery-workbench-writeback-evidence", "per_run_cap": 1, "provenance_head": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "retrieved_lessons": 1, "retrieved_run": "program-222222222222222222222222", "superseding_hash": "sha256:697b27233a10ec9616a553af1633bc6e14cf6504aa8e2e589fa48c2145bbb071", "supersession_chain": ["sha256:f6277a538764a430afc124627110e1ee31c1fd8e5365763a10f472d313bef5f5"], "terminal_completion": "persisted", "unresolved_marked": true}
```
