# Evidence - WLA-35-02

- **Story:** WLA-35-02 - Explainable recall
- **Status:** done
- **Date:** 2026-08-01

## Proof

Implemented by Sol (GPT-5.6) under orchestration; reviewed and verified by the operator session.

What shipped: `pmo-roadmap/lib/dw_pmo/memory_recall.py` — a pure, stdlib-only `build_memory_recall(...)` emitting documents valid under the `delivery-workbench-memory-recall@1` contract from WLA-35-01. All inputs are caller-supplied (no Git/file/clock/env/random/network reads, policed by the extended purity and authority guards in repository_knowledge_tests.py). Deterministic additive integer ranking (failure-signature 16000, story 14000, phase 12000, symbol 10000, test 9000, file 8000, grounded-location 7000, tag 6000, criteria-term 250 x <=20, bounded delivery-state/confidence/recency tie-breakers, stable-hash final tie-breaker); seven source kinds; 32 KiB default budget with whole-item drops; exclusions for byte-budget, stale-source, superseded, low-score, and audience-filter; honest empty recall; audience slices. Mirror `.githooks/dw_pmo/memory_recall.py` is byte-identical and enrolled in the hook-payload byte-identity test.

The authoritative run is the first capture below: knowledge_packet_tests.py (5 unit + 3 integration -> 11 unit + 3 integration), exit 0. The second capture proves the knowledge contract suite (28 tests, now policing memory_recall purity and mirror sync) stays green.

### Captured run — 2026-08-01T17:25:52Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/knowledge_packet_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b64a0c2f326614836fb85d45b6294770e249e261

```text
test_absent_and_explicit_zero_are_distinct_end_to_end_values (__main__.HonestUsageTest) ... ok
test_budget_drops_whole_lowest_scored_items_and_names_them (__main__.KnowledgePacketTest) ... ok
test_hint_free_packet_is_explicit_and_does_not_guess (__main__.KnowledgePacketTest) ... ok
test_same_inputs_are_byte_identical_with_stable_ties (__main__.KnowledgePacketTest) ... ok
test_stale_grounding_is_a_typed_refusal_not_empty_packet (__main__.KnowledgePacketTest) ... ok
test_audience_slice_filters_without_changing_the_source_snapshot (__main__.MemoryRecallTest) ... ok
test_builder_imports_only_pure_stdlib_and_has_no_ambient_read_calls (__main__.MemoryRecallTest) ... ok
test_empty_inputs_produce_honest_bounded_empty_recall (__main__.MemoryRecallTest) ... ok
test_every_typed_exclusion_is_explained_and_budget_drops_whole_items (__main__.MemoryRecallTest) ... ok
test_recall_is_byte_identical_and_matches_the_closed_contract (__main__.MemoryRecallTest) ... ok
test_structural_formula_ranks_all_supported_source_kinds (__main__.MemoryRecallTest) ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.009s

OK
test_packet_is_bounded_structured_and_contains_no_provider_command (dw_core_evidence_tests.OrchestrationDriverTest) ... ok
test_stale_knowledge_uses_existing_packet_assembly_failure_receipt (dw_core_evidence_tests.OrchestrationDriverTest) ... ok
test_fixture_absent_usage_is_unknown_in_receipt_and_ledger (dw_core_evidence_tests.OrchestrationDriverTest) ... ok

----------------------------------------------------------------------
Ran 3 tests in 5.753s

OK
WLA-29-04 EVIDENCE {"assembly_failure_path": true, "budget_bytes": 1500, "deterministic": true, "explicit_zero_preserved": 0, "honest_emptiness": "hint-free", "named_exclusions": ["source:pkg.py:pkg.beta", "source:pkg.py:pkg.alpha", "test:tests/test_beta.py:pkg.beta", "test:tests/test_pkg.py:pkg.beta", "test:tests/test_pkg.py:pkg.alpha", "lesson:sha256:2222222222222222222222222222222222222222222222222222222222222222"], "receipt_ledger_unknown": true, "stale_refusal": "StaleKnowledgePacket", "unknown_cost": null, "unknown_usage": "unknown", "used_bytes": 1204, "whole_symbols": true}
```

### Captured run — 2026-08-01T17:25:58Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/repository_knowledge_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b64a0c2f326614836fb85d45b6294770e249e261

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
Ran 28 tests in 0.160s

OK
```
