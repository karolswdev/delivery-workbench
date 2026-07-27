# Evidence - WLA-29-03

- **Story:** WLA-29-03 - Ground the work before it starts
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-27T02:24:45Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/grounding_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8cc0ed5b78fce004d43e06e1eca0af9ab7a4aea4

```text
test_check_warnings_are_greppable_and_do_not_change_exit_code (__main__.GroundingIntegrationTest) ... ok
test_cli_and_mcp_are_byte_identical_and_read_only (__main__.GroundingIntegrationTest) ... ok
test_fixture_story_classifies_verified_new_and_misspelled_with_evidence (__main__.GroundingIntegrationTest) ... ok
test_gap_text_match_prevents_explicit_new_classification (__main__.GroundingIntegrationTest) ... ok
test_stale_map_refuses_instead_of_answering (__main__.GroundingIntegrationTest) ... ok
test_story_table_parser_is_unchanged_by_optional_story_section (__main__.GroundingIntegrationTest) ... ok
test_commented_template_example_is_not_parsed_as_real_hints (__main__.GroundingUnitTest) ... ok
test_parser_requires_nested_lists_and_preserves_explicit_new_marker (__main__.GroundingUnitTest) ... ok
test_suggestions_are_bounded_by_name_distance (__main__.GroundingUnitTest) ... ok

----------------------------------------------------------------------
Ran 9 tests in 1.449s

OK
WLA-29-03 EVIDENCE {"complete_no_match": true, "misspelling_suggestions": 2, "new": 2, "unknown": 1, "verified": 2}
```
