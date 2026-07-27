# Evidence - WLA-29-01

- **Story:** WLA-29-01 - Contract repository knowledge
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-27T01:24:15Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/repository_knowledge_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6e7c98baceb0d310eee4eded05dd33b1e1fc346a

```text
test_authority_guard_rejects_a_planted_knowledge_read (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_derived_fact_computation_has_no_clock_or_random_input (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_documented_contract_names_both_classes_and_authority_exclusion (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_gate_contract_grant_and_verdict_paths_do_not_read_knowledge (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_hook_payload_keeps_the_contract_module_byte_identical (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_knowledge_imports_are_stdlib_offline_and_non_spawning (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_deleting_derived_cache_changes_only_recompute_latency (__main__.RepositoryKnowledgeTest) ... ok
test_delivery_and_lesson_append_as_typed_hash_chains (__main__.RepositoryKnowledgeTest) ... ok
test_derived_identity_is_deterministic_and_tamper_refuses (__main__.RepositoryKnowledgeTest) ... ok
test_derived_read_refuses_a_different_current_index_tree (__main__.RepositoryKnowledgeTest) ... ok
test_earned_shapes_are_closed_and_caps_apply_on_append (__main__.RepositoryKnowledgeTest) ... ok
test_earned_store_is_append_only_and_tamper_refuses (__main__.RepositoryKnowledgeTest) ... ok
test_every_earned_record_requires_valid_provenance (__main__.RepositoryKnowledgeTest) ... ok
test_explicit_recompute_path_replaces_stale_and_reuses_fresh (__main__.RepositoryKnowledgeTest) ... ok
test_machine_contract_is_versioned_total_and_authority_free (__main__.RepositoryKnowledgeTest) ... ok
test_read_revalidates_closed_fields_caps_and_provenance (__main__.RepositoryKnowledgeTest) ... ok
test_storage_classification_is_total_and_unknowns_refuse (__main__.RepositoryKnowledgeTest) ... ok

----------------------------------------------------------------------
Ran 17 tests in 0.129s

OK
```
