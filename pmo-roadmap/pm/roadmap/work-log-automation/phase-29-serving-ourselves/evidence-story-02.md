# Evidence - WLA-29-02

- **Story:** WLA-29-02 - Build the symbol and structure map
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-27T01:52:52Z

- **Command:** `python3 pmo-roadmap/tests/repository_map_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 84d05a444f3f0d80aa1350adbc5386aa2021a012

```text
test_full_repository_covers_every_tracked_python_and_names_all_other_gaps (__main__.RealRepositoryMapTest.test_full_repository_covers_every_tracked_python_and_names_all_other_gaps) ... ok
test_real_core_tests_reference_sampled_dw_pmo_symbols (__main__.RealRepositoryMapTest.test_real_core_tests_reference_sampled_dw_pmo_symbols) ... ok
test_real_extraction_is_byte_deterministic (__main__.RealRepositoryMapTest.test_real_extraction_is_byte_deterministic) ... ok
test_cli_and_mcp_return_byte_identical_read_only_model (__main__.RepositoryMapIntegrationTest.test_cli_and_mcp_return_byte_identical_read_only_model) ... ok
test_stale_read_refuses_and_one_file_refresh_parses_one_file (__main__.RepositoryMapIntegrationTest.test_stale_read_refuses_and_one_file_refresh_parses_one_file) ... ok
test_nested_async_symbols_imports_spans_and_module_inventory (__main__.SymbolMapUnitTest.test_nested_async_symbols_imports_spans_and_module_inventory) ... ok
test_non_python_and_unparseable_python_are_named_gaps (__main__.SymbolMapUnitTest.test_non_python_and_unparseable_python_are_named_gaps) ... ok
test_previous_blob_reuse_parses_only_the_changed_file (__main__.SymbolMapUnitTest.test_previous_blob_reuse_parses_only_the_changed_file) ... ok
test_same_tree_extraction_is_byte_identical (__main__.SymbolMapUnitTest.test_same_tree_extraction_is_byte_identical) ... ok
test_test_resolution_keeps_terminal_name_collisions (__main__.SymbolMapUnitTest.test_test_resolution_keeps_terminal_name_collisions) ... ok

----------------------------------------------------------------------
Ran 10 tests in 6.825s

OK
WLA-29-02 EVIDENCE {"cli_mcp_parity": true, "deterministic_bytes": 2680222, "gaps": 624, "incremental_reparsed": ["pkg.py"], "index_tree": "84d05a444f3f0d80aa1350adbc5386aa2021a012", "python_files": 147, "sampled_symbol_test_links": 5, "stale_refusal": true, "symbols": 4388, "tracked_files": 771}
```
