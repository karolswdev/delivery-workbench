# Evidence - WLA-29-04

- **Story:** WLA-29-04 - Serve knowledge packets to agents
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-27T03:22:23Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/knowledge_packet_tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8b920716b5813de92aeff61a4a08653a10d4c3c6

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
Ran 3 tests in 5.466s

OK
WLA-29-04 EVIDENCE {"assembly_failure_path": true, "budget_bytes": 1500, "deterministic": true, "explicit_zero_preserved": 0, "honest_emptiness": "hint-free", "named_exclusions": ["source:pkg.py:pkg.beta"], "receipt_ledger_unknown": true, "stale_refusal": "StaleKnowledgePacket", "unknown_cost": null, "unknown_usage": "unknown", "used_bytes": 1480, "whole_symbols": true}
```
