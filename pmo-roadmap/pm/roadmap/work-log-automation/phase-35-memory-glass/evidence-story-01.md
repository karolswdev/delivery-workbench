# Evidence - WLA-35-01

- **Story:** WLA-35-01 - Memory contract
- **Status:** done
- **Date:** 2026-08-01

## Proof

Implemented by Sol (GPT-5.6) under orchestration; reviewed and verified by the operator session.

What shipped: three new document kinds in `dw_pmo.knowledge.contract_document()` — `delivery-workbench-memory-recall@1`, `delivery-workbench-memory-writeback@1`, `delivery-workbench-decision-basis@1` — each with a closed field set, canonical-JSON SHA-256 identity, byte/item caps, provenance references, and the four false-authority fields fixed `false`; a `terminal-outcome` earned record kind in `EarnedRecordStore` (sequence, timestamp, hash-chain, exact-field, and cap validation intact) carrying `memory_state` in {confirmed, candidate, superseded}, with unsuccessful terminal states rejected when paired with `confirmed` and supersession requiring an ancestor reference; and an extended authority import guard covering the new memory surface. `.githooks/dw_pmo/knowledge.py` is byte-identical to the canonical module (`cmp` clean).

The authoritative run is the first capture below: `repository_knowledge_tests.py`, 22 → 28 tests, exit 0. The second capture proves no collateral damage: `knowledge_packet_tests.py` (8) and `knowledge_writeback_tests.py` (6) both green, unmodified.

### Captured run — 2026-08-01T17:15:05Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/repository_knowledge_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 11abfbc7dd5b0701481595039ab25a275de389ab

```text
test_authority_guard_rejects_planted_knowledge_and_memory_reads (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_derived_fact_computation_has_no_clock_or_random_input (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_documented_contract_names_both_classes_and_authority_exclusion (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_gate_contract_grant_and_verdict_paths_do_not_read_knowledge (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_grounding_is_stdlib_offline_and_uses_the_repository_fact_boundary (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_hook_payload_keeps_knowledge_modules_byte_identical (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_knowledge_imports_are_stdlib_offline_and_non_spawning (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_knowledge_packet_is_stdlib_offline_and_authority_free (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_symbol_map_extractor_is_stdlib_offline_and_non_spawning (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_writeback_adapter_cannot_import_authority_or_verdict_paths (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_deleting_derived_cache_changes_only_recompute_latency (__main__.RepositoryKnowledgeTest) ... ok
test_delivery_and_lesson_append_as_typed_hash_chains (__main__.RepositoryKnowledgeTest) ... ok
test_derived_identity_is_deterministic_and_tamper_refuses (__main__.RepositoryKnowledgeTest) ... ok
test_derived_read_refuses_a_different_current_index_tree (__main__.RepositoryKnowledgeTest) ... ok
test_earned_shapes_are_closed_and_caps_apply_on_append (__main__.RepositoryKnowledgeTest) ... ok
test_earned_store_is_append_only_and_tamper_refuses (__main__.RepositoryKnowledgeTest) ... ok
test_every_earned_record_requires_valid_provenance (__main__.RepositoryKnowledgeTest) ... ok
test_explicit_recompute_path_replaces_stale_and_reuses_fresh (__main__.RepositoryKnowledgeTest) ... ok
test_incremental_refresh_exposes_old_value_only_to_compute (__main__.RepositoryKnowledgeTest) ... ok
test_machine_contract_is_versioned_total_and_authority_free (__main__.RepositoryKnowledgeTest) ... ok
test_memory_contract_identity_is_deterministic_and_returned_by_value (__main__.RepositoryKnowledgeTest) ... ok
test_memory_document_contracts_are_closed_bounded_and_provenance_bound (__main__.RepositoryKnowledgeTest) ... ok
test_read_revalidates_closed_fields_caps_and_provenance (__main__.RepositoryKnowledgeTest) ... ok
test_storage_classification_is_total_and_unknowns_refuse (__main__.RepositoryKnowledgeTest) ... ok
test_terminal_outcome_read_revalidates_status_and_chain_integrity (__main__.RepositoryKnowledgeTest) ... ok
test_terminal_outcome_shape_caps_lists_and_supersession_are_validated (__main__.RepositoryKnowledgeTest) ... ok
test_terminal_outcomes_are_typed_bounded_hash_chained_records (__main__.RepositoryKnowledgeTest) ... ok
test_unsuccessful_terminal_outcomes_cannot_claim_confirmation (__main__.RepositoryKnowledgeTest) ... ok

----------------------------------------------------------------------
Ran 28 tests in 0.174s

OK
```

### Captured run — 2026-08-01T17:15:11Z

- **Command:** `/bin/sh -c /usr/bin/python3 pmo-roadmap/tests/knowledge_packet_tests.py && /usr/bin/python3 pmo-roadmap/tests/knowledge_writeback_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 11abfbc7dd5b0701481595039ab25a275de389ab

```text
test_absent_and_explicit_zero_are_distinct_end_to_end_values (__main__.HonestUsageTest) ... ok
test_budget_drops_whole_lowest_scored_items_and_names_them (__main__.KnowledgePacketTest) ... ok
test_hint_free_packet_is_explicit_and_does_not_guess (__main__.KnowledgePacketTest) ... ok
test_same_inputs_are_byte_identical_with_stable_ties (__main__.KnowledgePacketTest) ... ok
test_stale_grounding_is_a_typed_refusal_not_empty_packet (__main__.KnowledgePacketTest) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.001s

OK
test_packet_is_bounded_structured_and_contains_no_provider_command (dw_core_evidence_tests.OrchestrationDriverTest) ... ok
test_stale_knowledge_uses_existing_packet_assembly_failure_receipt (dw_core_evidence_tests.OrchestrationDriverTest) ... ok
test_fixture_absent_usage_is_unknown_in_receipt_and_ledger (dw_core_evidence_tests.OrchestrationDriverTest) ... ok

----------------------------------------------------------------------
Ran 3 tests in 6.230s

OK
WLA-29-04 EVIDENCE {"assembly_failure_path": true, "budget_bytes": 1500, "deterministic": true, "explicit_zero_preserved": 0, "honest_emptiness": "hint-free", "named_exclusions": ["source:pkg.py:pkg.beta", "source:pkg.py:pkg.alpha", "test:tests/test_beta.py:pkg.beta", "test:tests/test_pkg.py:pkg.beta", "test:tests/test_pkg.py:pkg.alpha", "lesson:sha256:2222222222222222222222222222222222222222222222222222222222222222"], "receipt_ledger_unknown": true, "stale_refusal": "StaleKnowledgePacket", "unknown_cost": null, "unknown_usage": "unknown", "used_bytes": 1204, "whole_symbols": true}
test_delivery_shape_is_only_ledger_identifiers_and_counts (__main__.KnowledgeWritebackTest) ... ok
test_lesson_inventory_lists_provenance_and_supersession (__main__.KnowledgeWritebackTest) ... ok
test_only_success_terminal_persists_and_cap_is_per_run (__main__.KnowledgeWritebackTest) ... ok
test_second_packet_prefers_superseding_lesson_and_keeps_chain (__main__.KnowledgeWritebackTest) ... ok
test_terminal_retry_deduplicates_exact_records (__main__.KnowledgeWritebackTest) ... ok
test_typed_output_is_closed_and_bounded (__main__.KnowledgeWritebackTest) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.016s

OK
WLA-29-07 EVIDENCE {"abandoned_lessons": 0, "age_label": "recorded-at:2026-07-26T13:00:00Z", "authority": false, "delivery_records": 2, "kind": "delivery-workbench-writeback-evidence", "per_run_cap": 1, "provenance_head": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "retrieved_lessons": 1, "retrieved_run": "program-222222222222222222222222", "superseding_hash": "sha256:697b27233a10ec9616a553af1633bc6e14cf6504aa8e2e589fa48c2145bbb071", "supersession_chain": ["sha256:f6277a538764a430afc124627110e1ee31c1fd8e5365763a10f472d313bef5f5"], "terminal_completion": "persisted", "unresolved_marked": true}
```
