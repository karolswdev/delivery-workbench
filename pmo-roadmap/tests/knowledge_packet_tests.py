#!/usr/bin/env python3
"""WLA-29-04 deterministic knowledge packet and honest usage tests."""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
import tempfile
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
from dw_pmo.memory_dispatch import (  # noqa: E402
    MemoryRecallActionNeeded,
    persist_recall_slices,
    recall_audience,
)
from dw_pmo.memory_recall import (  # noqa: E402
    SOURCE_KINDS,
    build_memory_recall,
)
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


class MemoryRecallTest(unittest.TestCase):
    HEADS = {
        "repository_index": TREE,
        "earned_record_chains": "sha256:" + "4" * 64,
        "referenced_ledgers": "sha256:" + "5" * 64,
    }

    @staticmethod
    def candidate(source_kind, source_ref, **values):
        return {
            "source_kind": source_kind,
            "source_ref": source_ref,
            "source_revision": TREE,
            "confidence": "unknown",
            "delivery_state": "candidate",
            "summary": "One bounded factual recall item.",
            **values,
        }

    def recall(self, candidates=(), **values):
        arguments = {
            "subject": "run:recall-1",
            "source_revision": TREE,
            "source_heads": self.HEADS,
            "audience": "implementer",
            "story_ids": ["WLA-35-02"],
            "grounded_files": ["dw_pmo/memory.py"],
            "grounded_symbols": ["dw_pmo.memory.build_memory_recall"],
            "test_names": ["test_explainable_recall"],
            "failure_signatures": ["RecallError:E42"],
            "orchestration_tags": ["memory-glass"],
        }
        arguments.update(values)
        return build_memory_recall("Explain bounded recall.", candidates, **arguments)

    def test_recall_is_byte_identical_and_matches_the_closed_contract(self):
        candidate = self.candidate(
            "lesson", "sha256:" + "6" * 64, story_ids=["WLA-35-02"],
            confidence="high", delivery_state="confirmed", recency=99,
        )
        tied = self.candidate(
            "lesson", "sha256:" + "7" * 64, story_ids=["WLA-35-02"],
            confidence="high", delivery_state="confirmed", recency=99,
        )
        first = self.recall([candidate, tied])
        second = self.recall([dict(tied), dict(candidate)])
        first_bytes = json.dumps(
            first, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        second_bytes = json.dumps(
            second, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(first["used_bytes"], len(first_bytes))
        self.assertEqual(set(first), {
            "kind", "schema_version", "recall_id", "subject", "audience",
            "source_revision", "source_heads", "items", "exclusions",
            "byte_budget", "used_bytes", "starts_work", "authorizes",
            "satisfies_gate", "substitutes_for_evidence",
        })
        self.assertEqual(first["source_heads"], self.HEADS)
        self.assertTrue(first["recall_id"].startswith("sha256:"))
        self.assertFalse(first["starts_work"])
        self.assertFalse(first["authorizes"])
        self.assertFalse(first["satisfies_gate"])
        self.assertFalse(first["substitutes_for_evidence"])

    def test_structural_formula_ranks_all_supported_source_kinds(self):
        candidates = [
            self.candidate(
                "repository-snippet", "repo:symbol",
                symbols=["dw_pmo.memory.build_memory_recall"],
            ),
            self.candidate(
                "terminal-outcome", "outcome:failure",
                failure_signatures=["RecallError:E42"],
            ),
            self.candidate(
                "evidence-digest", "evidence:file",
                files=["dw_pmo/memory.py"],
            ),
            self.candidate("lesson", "lesson:story", story_ids=["WLA-35-02"]),
            self.candidate("decision", "decision:phase", phase_ids=["WLA-35"]),
            self.candidate(
                "test-reference", "test:exact",
                test_names=["test_explainable_recall"],
            ),
            self.candidate(
                "grounding", "grounding:tag", orchestration_tags=["memory-glass"]
            ),
        ]
        recall = self.recall(candidates)
        self.assertEqual(set(item["source_kind"] for item in recall["items"]), set(SOURCE_KINDS))
        self.assertEqual([item["source_ref"] for item in recall["items"]], [
            "lesson:story", "repo:symbol", "outcome:failure", "evidence:file",
            "decision:phase", "test:exact", "grounding:tag",
        ])
        self.assertEqual(
            [item["score"] for item in recall["items"]],
            sorted((item["score"] for item in recall["items"]), reverse=True),
        )
        for item in recall["items"]:
            self.assertIsInstance(item["score"], int)
            self.assertTrue(item["match_reasons"])
            self.assertIn("source_kind", item)

    def test_every_typed_exclusion_is_explained_and_budget_drops_whole_items(self):
        candidates = [
            self.candidate(
                "terminal-outcome", "keep:failure",
                failure_signatures=["RecallError:E42"], summary="Keep this fact whole.",
            ),
            self.candidate(
                "lesson", "drop:budget", orchestration_tags=["memory-glass"],
                summary="B" * 1_000,
            ),
            self.candidate(
                "repository-snippet", "drop:stale", story_ids=["WLA-35-02"],
                source_head="repository_index", source_revision="9" * 40,
            ),
            self.candidate(
                "lesson", "drop:superseded", story_ids=["WLA-35-02"],
                delivery_state="superseded",
            ),
            self.candidate(
                "decision", "drop:audience", story_ids=["WLA-35-02"],
                audiences=["verifier"],
            ),
            self.candidate(
                "grounding", "drop:low-score", summary="Opaque datum."
            ),
        ]
        recall = self.recall(candidates, byte_budget=2_500)
        reasons = {item["reason"] for item in recall["exclusions"]}
        self.assertEqual(reasons, {
            "byte-budget", "stale-source", "superseded", "low-score",
            "audience-filter",
        })
        self.assertEqual(
            [item["source_ref"] for item in recall["items"]], ["keep:failure"]
        )
        self.assertEqual(recall["items"][0]["summary"], "Keep this fact whole.")
        budget_drop = next(
            item for item in recall["exclusions"] if item["reason"] == "byte-budget"
        )
        self.assertEqual(budget_drop["source_ref"], "drop:budget")
        self.assertLessEqual(recall["used_bytes"], recall["byte_budget"])

    def test_empty_inputs_produce_honest_bounded_empty_recall(self):
        recall = self.recall([])
        self.assertEqual(recall["items"], [])
        self.assertEqual(recall["exclusions"], [])
        self.assertEqual(recall["used_bytes"], len(json.dumps(
            recall, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")))

    def test_audience_slice_filters_without_changing_the_source_snapshot(self):
        candidates = [
            self.candidate(
                "lesson", "lesson:implementer", story_ids=["WLA-35-02"],
                audiences=["implementer", "shared"],
            ),
            self.candidate(
                "decision", "decision:verifier", story_ids=["WLA-35-02"],
                audiences=["verifier"],
            ),
        ]
        recall = self.recall(candidates)
        self.assertEqual(
            [item["source_ref"] for item in recall["items"]],
            ["lesson:implementer"],
        )
        self.assertEqual(recall["exclusions"], [{
            "source_ref": "decision:verifier", "source_kind": "decision",
            "score": recall["exclusions"][0]["score"],
            "reason": "audience-filter",
        }])
        self.assertEqual(recall["source_revision"], TREE)
        self.assertEqual(recall["source_heads"], self.HEADS)

    def test_builder_imports_only_pure_stdlib_and_has_no_ambient_read_calls(self):
        source = (LIB_DIR / "dw_pmo" / "memory_recall.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        allowed = {"__future__", "hashlib", "json", "re", "typing"}
        forbidden_imports = {
            "socket", "urllib", "http", "subprocess", "random", "secrets",
            "uuid", "os", "pathlib", "datetime", "time", "tempfile",
        }
        unexpected = []
        forbidden = []
        ambient_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                modules = []
            for module in modules:
                root = module.split(".", 1)[0]
                if root in forbidden_imports:
                    forbidden.append(module)
                if root not in allowed:
                    unexpected.append(module)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in {
                    "open", "getenv", "urandom",
                }:
                    ambient_calls.append(node.func.id)
                if isinstance(node.func, ast.Attribute) and node.func.attr in {
                    "read_text", "read_bytes", "open", "system", "popen",
                }:
                    ambient_calls.append(node.func.attr)
        self.assertEqual(forbidden, [])
        self.assertEqual(unexpected, [])
        self.assertEqual(ambient_calls, [])


class MemoryDispatchTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dw-memory-dispatch.")
        self.run_dir = Path(self.temporary.name) / "run"
        self.run_dir.mkdir()
        self.knowledge = build_knowledge_packet(
            "No localization hints.", None, None, {}, [],
            story="plain.md", index_tree=TREE,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def persist(self, knowledge=None):
        return persist_recall_slices(
            self.run_dir,
            subject="run-memory-fixture",
            knowledge=self.knowledge if knowledge is None else knowledge,
            story_criteria="No localization hints.",
            story_ids=["WLA-35-03"],
            phase_ids=["35"],
            orchestration_tags=["memory-glass"],
        )

    def test_hint_free_slices_are_explicit_persisted_and_reused(self):
        first, built = self.persist()
        second, rebuilt = self.persist()
        self.assertTrue(built)
        self.assertFalse(rebuilt)
        self.assertEqual(
            {audience: document["recall_id"] for audience, document in first.items()},
            {audience: document["recall_id"] for audience, document in second.items()},
        )
        self.assertTrue(all(document["items"] == [] for document in first.values()))
        self.assertTrue(all(document["exclusions"] == [] for document in first.values()))
        self.assertTrue((self.run_dir / "memory" / "manifest.json").is_file())

    def test_cross_run_outcomes_decisions_and_role_stems_reach_recall(self):
        failure = "sha256:" + "f" * 64
        source = {
            **self.knowledge,
            "verified_locations": [{"file": "pkg.py", "symbol": "pkg.alpha"}],
            "failure_signatures": [failure],
            "terminal_outcomes": [{
                "record_hash": "sha256:" + "a" * 64,
                "terminal_state": "failed",
                "memory_state": "candidate",
                "story_ids": ["WLA-35-02"],
                "changed_files": ["pkg.py"],
                "failure_signatures": [failure],
            }],
            "decisions": [{
                "decision_id": "sha256:" + "b" * 64,
                "summary": "Prior dissent remains advisory.",
                "files": ["pkg.py"],
                "audiences": ["judge"],
            }],
        }
        documents, created = self.persist(source)
        self.assertTrue(created)
        self.assertEqual(recall_audience("coordinator"), "coordinator")
        self.assertEqual(recall_audience("verifier"), "verifier")
        shared = {item["source_kind"]: item for item in documents["shared"]["items"]}
        self.assertEqual(shared["terminal-outcome"]["delivery_state"], "candidate")
        self.assertTrue(shared["terminal-outcome"]["advisory_only"])
        judge_kinds = {item["source_kind"] for item in documents["judge"]["items"]}
        self.assertIn("decision", judge_kinds)
        shared_exclusions = {
            item["source_kind"]: item["reason"]
            for item in documents["shared"]["exclusions"]
        }
        self.assertEqual(shared_exclusions["decision"], "audience-filter")

    def test_missing_slice_is_typed_action_needed(self):
        self.persist()
        (self.run_dir / "memory" / "recalls" / "verifier.json").unlink()
        with self.assertRaises(MemoryRecallActionNeeded) as caught:
            self.persist()
        self.assertEqual(caught.exception.reason, "missing")

    def test_malformed_slice_is_typed_action_needed(self):
        self.persist()
        path = self.run_dir / "memory" / "recalls" / "coordinator.json"
        path.write_text("{not-json\n", encoding="utf-8")
        with self.assertRaises(MemoryRecallActionNeeded) as caught:
            self.persist()
        self.assertEqual(caught.exception.reason, "malformed")

    def test_tampered_slice_is_typed_action_needed(self):
        self.persist()
        path = self.run_dir / "memory" / "recalls" / "implementer.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["items"].append({"planted": "tamper"})
        path.write_text(json.dumps(document) + "\n", encoding="utf-8")
        with self.assertRaises(MemoryRecallActionNeeded) as caught:
            self.persist()
        self.assertEqual(caught.exception.reason, "tampered")

    def test_stale_source_is_typed_action_needed(self):
        self.persist()
        changed = {**self.knowledge, "index_tree": "9" * 40}
        with self.assertRaises(MemoryRecallActionNeeded) as caught:
            self.persist(changed)
        self.assertEqual(caught.exception.reason, "stale")


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
