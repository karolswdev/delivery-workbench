#!/usr/bin/env python3
"""WLA-29-04 deterministic knowledge packet and honest usage tests."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
LIB_DIR = TESTS_DIR.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

from dw_pmo.knowledge import encode_lesson_locations  # noqa: E402
from dw_pmo.knowledge_packet import (  # noqa: E402
    StaleKnowledgePacket,
    build_knowledge_packet,
)
from dw_pmo.live_progress import _budget_rows, _usage_budget_overlay  # noqa: E402
from dw_pmo.orchestration_driver import normalize_driver_usage  # noqa: E402


TREE = "1" * 40
SOURCE = (
    "def alpha(value):\n"
    "    return value + 1\n"
    "\n"
    "def beta(value):\n"
    "    text = 'bounded ' * 3000\n"
    "    return text + str(value)\n"
).encode("utf-8")
MODEL = {
    "kind": "delivery-workbench-symbol-structure-map",
    "schema_version": 1,
    "index_tree": TREE,
    "tracked_files": [{"path": "pkg.py", "blob": "a" * 40, "size": len(SOURCE)}],
    "modules": [],
    "gaps": [],
    "symbols": [
        {"kind": "module", "name": "pkg", "qualified_name": "pkg", "file": "pkg.py", "line_start": 1, "line_end": 6},
        {"kind": "function", "name": "alpha", "qualified_name": "pkg.alpha", "file": "pkg.py", "line_start": 1, "line_end": 2},
        {"kind": "function", "name": "beta", "qualified_name": "pkg.beta", "file": "pkg.py", "line_start": 4, "line_end": 6},
    ],
    "test_map": {
        "pkg.alpha": ["tests/test_pkg.py"],
        "pkg.beta": ["tests/test_pkg.py", "tests/test_beta.py"],
    },
}
DOCUMENT = {"index_tree": TREE, "value": MODEL}
GROUNDING = {
    "kind": "delivery-workbench-story-grounding",
    "schema_version": 1,
    "status": "grounded",
    "story": "story.md",
    "index_tree": TREE,
    "affected_files": [],
    "target_symbols": [
        {
            "kind": "target-symbol", "hint": "alpha", "declared_new": False,
            "classification": "verified",
            "locations": [{"file": "pkg.py", "line_start": 1, "line_end": 2, "authority": "symbol-map"}],
            "suggestions": [], "evidence": {"symbol_map_exact_matches": 1},
        },
        {
            "kind": "target-symbol", "hint": "beta", "declared_new": False,
            "classification": "verified",
            "locations": [{"file": "pkg.py", "line_start": 4, "line_end": 6, "authority": "symbol-map"}],
            "suggestions": [], "evidence": {"symbol_map_exact_matches": 1},
        },
        {
            "kind": "target-symbol", "hint": "bett", "declared_new": False,
            "classification": "unknown", "locations": [],
            "suggestions": [{"value": "beta", "distance": 1}],
            "evidence": {"symbol_map_exact_matches": 0},
        },
    ],
    "summary": {"verified": 2, "new": 0, "unknown": 1},
    "starts_work": False, "authorizes": False,
    "satisfies_gate": False, "substitutes_for_evidence": False,
}
LESSON = {
    "record_kind": "lesson", "record_hash": "sha256:" + "2" * 64,
    "origin_kind": "run", "origin": "run-1", "head_sha": "3" * 40,
    "timestamp": "2026-07-26T12:00:00Z",
    "detail": {
        "claim": "Keep alpha and beta source locations bounded.",
        "locations": encode_lesson_locations([{
            "reference": "pkg.alpha", "status": "resolved", "file": "pkg.py",
            "symbol": "pkg.alpha", "line_start": 1, "line_end": 2,
        }]),
        "confidence": "high",
        "supersedes": "",
    },
}


class KnowledgePacketTest(unittest.TestCase):
    def packet(self, budget=32768):
        return build_knowledge_packet(
            "Change alpha and beta localization with mapped tests.",
            GROUNDING, DOCUMENT, {"pkg.py": SOURCE}, [LESSON],
            story="story.md", byte_budget=budget,
        )

    def test_same_inputs_are_byte_identical_with_stable_ties(self):
        first = self.packet()
        second = self.packet()
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )
        self.assertEqual(first["unverified_hints"][0]["label"], "unverified")
        self.assertFalse(first["authorizes"])

    def test_budget_drops_whole_lowest_scored_items_and_names_them(self):
        packet = self.packet(1500)
        encoded = json.dumps(packet, sort_keys=True, separators=(",", ":")).encode()
        self.assertLessEqual(len(encoded), 2200)
        self.assertEqual(packet["used_bytes"], len(encoded))
        self.assertTrue(packet["exclusions"])
        self.assertTrue(all({"name", "kind", "score", "reason"} == set(item) for item in packet["exclusions"]))
        included = {item["symbol"] for item in packet["snippets"]}
        self.assertNotIn("pkg.beta", included)
        for snippet in packet["snippets"]:
            if snippet["symbol"] == "pkg.alpha":
                self.assertEqual(snippet["content"], "def alpha(value):\n    return value + 1\n")

    def test_hint_free_packet_is_explicit_and_does_not_guess(self):
        packet = build_knowledge_packet(
            "No localization hints.", None, None, {}, [],
            story="plain.md", index_tree=TREE,
        )
        self.assertEqual(packet["grounding_status"], "hint-free")
        self.assertEqual(packet["verified_locations"], [])
        self.assertEqual(packet["snippets"], [])
        self.assertEqual(packet["test_references"], [])
        self.assertEqual(packet["lessons"], [])

    def test_stale_grounding_is_a_typed_refusal_not_empty_packet(self):
        stale = dict(GROUNDING)
        stale["index_tree"] = "9" * 40
        with self.assertRaises(StaleKnowledgePacket):
            build_knowledge_packet(
                "alpha", stale, DOCUMENT, {"pkg.py": SOURCE}, [],
                story="story.md",
            )


class HonestUsageTest(unittest.TestCase):
    def test_absent_and_explicit_zero_are_distinct_end_to_end_values(self):
        unknown = normalize_driver_usage()
        zero = normalize_driver_usage({
            "status": "reported", "input_tokens": 0, "output_tokens": 0,
            "total_tokens": 0, "cost_microunits": 0,
        })
        self.assertEqual(unknown["status"], "unknown")
        self.assertIsNone(unknown["cost_microunits"])
        self.assertEqual(zero["status"], "reported")
        self.assertEqual(zero["cost_microunits"], 0)
        budgets = {
            "max_tokens": {"used": 0, "limit": 100, "remaining": 100},
            "max_observed_cost_microunits": {"used": 0, "limit": 50, "remaining": 50},
        }
        receipt = {"operation": {"usage": unknown}}
        rows = _budget_rows(_usage_budget_overlay(budgets, [receipt]))
        by_id = {item["id"]: item for item in rows}
        self.assertIsNone(by_id["max_tokens"]["used"])
        self.assertIsNone(by_id["max_observed_cost_microunits"]["used"])
        self.assertEqual(by_id["max_observed_cost_microunits"]["status"], "unknown")
        zero_rows = _budget_rows(_usage_budget_overlay(
            budgets, [{"operation": {"usage": zero}}]
        ))
        zero_by_id = {item["id"]: item for item in zero_rows}
        self.assertEqual(zero_by_id["max_observed_cost_microunits"]["used"], 0)
        self.assertEqual(zero_by_id["max_observed_cost_microunits"]["status"], "available")
        bounded = _usage_budget_overlay(budgets, [
            {"executor": "driver", "claim_id": "c1", "total_tokens": 3,
             "cost_microunits": 2},
            {"executor": "driver", "claim_id": "c1", "total_tokens": 5,
             "cost_microunits": 4},
        ])
        self.assertEqual(bounded["max_tokens"]["used"], 5)
        self.assertEqual(bounded["max_observed_cost_microunits"]["used"], 4)


def _evidence(integration_passed: bool) -> dict:
    test = KnowledgePacketTest()
    full = test.packet()
    bounded = test.packet(1500)
    unknown = normalize_driver_usage()
    return {
        "deterministic": full == test.packet(),
        "budget_bytes": bounded["byte_budget"],
        "used_bytes": bounded["used_bytes"],
        "named_exclusions": [item["name"] for item in bounded["exclusions"]],
        "whole_symbols": all(item["content"].endswith("\n") for item in bounded["snippets"]),
        "honest_emptiness": build_knowledge_packet(
            "none", None, None, {}, [], story="plain.md", index_tree=TREE
        )["grounding_status"],
        "stale_refusal": "StaleKnowledgePacket",
        "assembly_failure_path": integration_passed,
        "receipt_ledger_unknown": integration_passed,
        "unknown_usage": unknown["status"],
        "unknown_cost": unknown["cost_microunits"],
        "explicit_zero_preserved": normalize_driver_usage({
            "status": "reported", "input_tokens": 0, "output_tokens": 0,
            "total_tokens": 0, "cost_microunits": 0,
        })["cost_microunits"],
    }


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    integration_passed = False
    if result.result.wasSuccessful():
        spec = importlib.util.spec_from_file_location(
            "dw_core_evidence_tests", TESTS_DIR / "dw-core-tests.py"
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load core integration tests")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        integration = unittest.TestSuite([
            module.OrchestrationDriverTest(
                "test_packet_is_bounded_structured_and_contains_no_provider_command"
            ),
            module.OrchestrationDriverTest(
                "test_stale_knowledge_uses_existing_packet_assembly_failure_receipt"
            ),
            module.OrchestrationDriverTest(
                "test_fixture_absent_usage_is_unknown_in_receipt_and_ledger"
            ),
        ])
        integration_result = unittest.TextTestRunner(verbosity=2).run(integration)
        integration_passed = integration_result.wasSuccessful()
    successful = result.result.wasSuccessful() and integration_passed
    if successful:
        print("WLA-29-04 EVIDENCE " + json.dumps(
            _evidence(integration_passed), sort_keys=True
        ))
    raise SystemExit(0 if successful else 1)
