# Evidence - WLA-35-05

- **Story:** WLA-35-05 - Memory read surfaces
- **Status:** done
- **Date:** 2026-08-01

## Proof

Implemented by Sol (GPT-5.6) under orchestration; reviewed and verified by the operator session.

What shipped: one byte-consistent memory read model (`memory_read.py`) behind three transports. CLI: `dw knowledge recall (--run|--program)` and `dw knowledge writebacks [--run|--program] [--story] [--state]`, canonical compact JSON, exit 1 with a typed refusal. MCP: `dw_knowledge_recall` and `dw_knowledge_writebacks`, `content[0].text` byte-identical to CLI stdout for success AND refusal. HTTP: read-only `GET /api/runs/{run_id}/memory`, `/api/programs/{program}/memory`, `/api/memory/records/{record_hash}` — 200 ok, 404 missing, 409 stale/malformed/tampered, localhost/tailnet guard, no mutation form; a repeated-read checksum proof shows reads never mutate the stores. The model groups recalled / used-as-basis / written-back / superseded / excluded, preserving record hashes and ledger coordinates (`used-as-basis` structured now, populated when WLA-35-07 emits decision-basis records). Inventories updated deliberately: MCP TOOLS registry + pinned smoke inventory, CLI verb census, interop model-stamp census, docs/interop.md, docs/mcp.md.

Honest repair note: the POST-route equality census (17 → 19) and several workbench-explorer assertions were stale on main — the post-phase-34 board-redesign commits added `/api/requests/respond` + `/api/suggestions` equality routes and replaced the five-destination nav without updating those guards. This story realigns them to current reality; nothing was weakened (the explorer suite gained memory-endpoint, typed-404, and no-side-effect coverage).

The authoritative run is the first capture below: mcp-server.sh (5 → 6 named checks, including CLI/MCP memory byte-parity) + workbench-explorer.sh (memory endpoints, typed refusals, repeated-read checksums), both exit 0. The second capture: repository knowledge 29 → 30, writeback 14 → 18, and the two realigned dw-core-tests classes green.

### Captured run — 2026-08-01T19:45:42Z

- **Command:** `/bin/sh -c bash pmo-roadmap/tests/mcp-server.sh && bash pmo-roadmap/tests/workbench-explorer.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d12647dd807afa05242038ca177a356295b1e875

```text
protocol exchange: ok (9 replies)
memory CLI/MCP parity: ok (5 projections)
no-rails refusal: ok
mutation walk: ok (done-without-evidence refused; contract stamped, certification manual)
gate still blocks uncertified commits: ok
MCP/CLI byte-parity (timestamps normalized): ok
mcp-server.sh: ok
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.Gzg969/repo
dw-workbench: http://127.0.0.1:19418/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.Gzg969/installed
dw-workbench: http://127.0.0.1:19419/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.Gzg969/repo
dw-workbench: http://127.0.0.1:19418/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
```

### Captured run — 2026-08-01T19:46:07Z

- **Command:** `/bin/sh -c /usr/bin/python3 pmo-roadmap/tests/repository_knowledge_tests.py && /usr/bin/python3 pmo-roadmap/tests/knowledge_writeback_tests.py && /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py DwCoreTest.test_missioncontrol_readonly_fitness_guard DwCoreTest.test_interop_doc_names_every_surface`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d12647dd807afa05242038ca177a356295b1e875

```text
test_authority_guard_rejects_planted_knowledge_and_memory_reads (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_derived_fact_computation_has_no_clock_or_random_input (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_documented_contract_names_both_classes_and_authority_exclusion (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_gate_contract_grant_and_verdict_paths_do_not_read_knowledge (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_grounding_is_stdlib_offline_and_uses_the_repository_fact_boundary (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_hook_payload_keeps_knowledge_modules_byte_identical (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_knowledge_imports_are_stdlib_offline_and_non_spawning (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_knowledge_packet_is_stdlib_offline_and_authority_free (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_memory_dispatch_adapter_is_offline_non_spawning_and_non_authoritative (__main__.RepositoryKnowledgeFitnessTest) ... ok
test_memory_read_adapter_is_offline_non_spawning_and_read_only (__main__.RepositoryKnowledgeFitnessTest) ... ok
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
Ran 30 tests in 0.193s

OK
test_crash_after_earned_append_replays_the_same_receipt (__main__.KnowledgeWritebackTest) ... ok
test_delivery_shape_is_only_ledger_identifiers_and_counts (__main__.KnowledgeWritebackTest) ... ok
test_every_terminal_outcome_builds_a_closed_bounded_receipt (__main__.KnowledgeWritebackTest) ... ok
test_lesson_inventory_lists_provenance_and_supersession (__main__.KnowledgeWritebackTest) ... ok
test_memory_read_groups_recall_writeback_and_ledger_coordinates (__main__.KnowledgeWritebackTest) ... ok
test_memory_read_groups_supersession_without_losing_hashes (__main__.KnowledgeWritebackTest) ... ok
test_memory_read_refuses_missing_stale_malformed_and_tampered_sources (__main__.KnowledgeWritebackTest) ... ok
test_memory_writeback_read_refuses_a_tampered_receipt (__main__.KnowledgeWritebackTest) ... ok
test_only_success_terminal_persists_and_cap_is_per_run (__main__.KnowledgeWritebackTest) ... ok
test_program_terminal_vocabulary_maps_expiry_without_confirming_it (__main__.KnowledgeWritebackTest) ... ok
test_second_packet_prefers_superseding_lesson_and_keeps_chain (__main__.KnowledgeWritebackTest) ... ok
test_terminal_replay_deduplicates_receipt_and_earned_outcome (__main__.KnowledgeWritebackTest) ... ok
test_terminal_retry_deduplicates_exact_records (__main__.KnowledgeWritebackTest) ... ok
test_terminal_writeback_persists_manifest_recall_ids_and_exact_facts (__main__.KnowledgeWritebackTest) ... ok
test_typed_output_is_closed_and_bounded (__main__.KnowledgeWritebackTest) ... ok
test_unsuccessful_outcome_is_candidate_and_supersession_appends (__main__.KnowledgeWritebackTest) ... ok
test_writeback_failure_is_action_needed_and_not_retried_implicitly (__main__.KnowledgeWritebackTest) ... ok
test_writeback_failure_reaches_needs_you_without_changing_terminal_state (__main__.KnowledgeWritebackTest) ... ok

----------------------------------------------------------------------
Ran 18 tests in 0.092s

OK
WLA-29-07 EVIDENCE {"abandoned_lessons": 0, "age_label": "recorded-at:2026-07-26T13:00:00Z", "authority": false, "delivery_records": 2, "kind": "delivery-workbench-writeback-evidence", "per_run_cap": 1, "provenance_head": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "retrieved_lessons": 1, "retrieved_run": "program-222222222222222222222222", "superseding_hash": "sha256:697b27233a10ec9616a553af1633bc6e14cf6504aa8e2e589fa48c2145bbb071", "supersession_chain": ["sha256:f6277a538764a430afc124627110e1ee31c1fd8e5365763a10f472d313bef5f5"], "terminal_completion": "persisted", "unresolved_marked": true}
test_missioncontrol_readonly_fitness_guard (__main__.DwCoreTest) ... ok
test_interop_doc_names_every_surface (__main__.DwCoreTest)
docs/interop.md is the read-surface contract; a new route, ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.045s

OK
```
