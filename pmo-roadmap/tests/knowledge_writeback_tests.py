#!/usr/bin/env python3
"""WLA-29-07 terminal delivery and lesson write-back proof."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent / "lib"))

from dw_pmo import knowledge  # noqa: E402
from dw_pmo.knowledge_packet import build_knowledge_packet  # noqa: E402
from dw_pmo.knowledge_writeback import (  # noqa: E402
    LESSON_OUTPUT_KIND,
    delivery_detail_from_projection,
    parse_lesson_output,
    persist_completed_program,
    validate_lesson_output,
)
from dw_pmo.model import DwError  # noqa: E402


HEAD = "a" * 40
TREE = "b" * 40
STAMP = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
MODEL = {
    "kind": "delivery-workbench-symbol-structure-map",
    "schema_version": 1,
    "index_tree": TREE,
    "tracked_files": [{"path": "pkg/delivery.py", "blob": "c" * 40, "size": 30}],
    "modules": [],
    "gaps": [],
    "symbols": [{
        "kind": "function",
        "name": "deliver",
        "qualified_name": "pkg.delivery.deliver",
        "file": "pkg/delivery.py",
        "line_start": 1,
        "line_end": 2,
    }],
    "test_map": {"pkg.delivery.deliver": ["tests/test_delivery.py"]},
}
DOCUMENT = {"index_tree": TREE, "value": MODEL}
GROUNDING = {
    "kind": "delivery-workbench-story-grounding",
    "schema_version": 1,
    "status": "grounded",
    "story": "story.md",
    "index_tree": TREE,
    "affected_files": [],
    "target_symbols": [{
        "kind": "target-symbol",
        "hint": "deliver",
        "declared_new": False,
        "classification": "verified",
        "locations": [{
            "file": "pkg/delivery.py", "line_start": 1, "line_end": 2,
            "authority": "symbol-map",
        }],
        "suggestions": [],
        "evidence": {"symbol_map_exact_matches": 1},
    }],
    "summary": {"verified": 1, "new": 0, "unknown": 0},
    "starts_work": False,
    "authorizes": False,
    "satisfies_gate": False,
    "substitutes_for_evidence": False,
}
SOURCE = b"def deliver():\n    return 1\n"


def projection(run_id="program-" + "1" * 24, state="complete"):
    return {
        "run_id": run_id,
        "state": state,
        "delivery_facts": {
            "story_ids": ["WLA-29-07"],
            "files_touched": ["pkg/delivery.py", "tests/test_delivery.py"],
            "head_sha": HEAD,
            "verdict_outcome": "passed",
            "obligation_ids": ["obligation-follow-up"],
        } if state == "complete" else None,
    }


def lesson_document(claim="Keep delivery writes terminal and bounded.", *,
                    supersedes="", locations=None, count=1):
    items = []
    for index in range(count):
        items.append({
            "claim": claim + (" %d" % index if count > 1 else ""),
            "locations": locations or ["pkg.delivery.deliver", "missing.symbol"],
            "confidence": "high",
            "supersedes": supersedes if index == 0 else "",
        })
    return {
        "kind": LESSON_OUTPUT_KIND,
        "schema_version": 1,
        "lessons": items,
    }


class KnowledgeWritebackTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dw-writeback-test."))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.git_dir = self.root / ".git"
        self.git_dir.mkdir()
        git_patch = mock.patch.object(
            knowledge.repofacts, "git_dir", return_value=self.git_dir
        )
        git_patch.start()
        self.addCleanup(git_patch.stop)
        map_patch = mock.patch(
            "dw_pmo.knowledge_writeback._symbol_model", return_value=MODEL
        )
        map_patch.start()
        self.addCleanup(map_patch.stop)

    def test_typed_output_is_closed_and_bounded(self):
        from dw_pmo.program_conductor import _packet_outputs
        from dw_pmo.program_workflow import ARTIFACT_KINDS

        self.assertIn("lesson", ARTIFACT_KINDS)
        self.assertEqual(_packet_outputs([{
            "id": "lessons", "kind": "lesson", "max_bytes": 10_000,
        }])[0]["format"], "json")
        document = lesson_document()
        self.assertEqual(
            parse_lesson_output(json.dumps(document).encode("utf-8")),
            document,
        )
        with self.assertRaises(DwError):
            validate_lesson_output(dict(document, prompt="unbounded"))
        with self.assertRaises(DwError):
            validate_lesson_output(lesson_document(locations=["x"] * 9))
        with self.assertRaises(DwError):
            validate_lesson_output(lesson_document(claim="x" * 1001))

    def test_delivery_shape_is_only_ledger_identifiers_and_counts(self):
        detail = delivery_detail_from_projection(projection())
        self.assertEqual(set(detail), set(knowledge.EARNED_RECORD_FIELDS["delivery-record"]))
        self.assertEqual(json.loads(detail["story_ids"]), ["WLA-29-07"])
        self.assertEqual(detail["story_count"], "1")
        self.assertEqual(detail["file_count"], "2")
        self.assertEqual(detail["obligation_count"], "1")
        for forbidden in ("summary", "description", "output", "diff", "prompt"):
            self.assertNotIn(forbidden, detail)

    def test_only_success_terminal_persists_and_cap_is_per_run(self):
        for state in ("revoked", "cancelled", "expired", "exhausted", "running"):
            result = persist_completed_program(
                self.root, projection(state=state), [lesson_document()],
                max_lessons=2, timestamp=STAMP,
            )
            self.assertEqual(result["lessons"], 0)
        self.assertFalse((self.git_dir / "pmo-knowledge" / "earned").exists())

        result = persist_completed_program(
            self.root, projection(), [lesson_document(count=4)],
            max_lessons=2, timestamp=STAMP,
        )
        self.assertEqual(result["lessons"], 2)
        self.assertEqual(result["discarded_lessons"], 2)
        records = knowledge.EarnedRecordStore(self.root).read("lesson")
        self.assertEqual(len(records), 2)
        locations = knowledge.decode_lesson_locations(records[0]["detail"]["locations"])
        self.assertEqual(locations[0]["status"], "resolved")
        self.assertEqual(locations[1]["status"], "unresolved")

    def test_terminal_retry_deduplicates_exact_records(self):
        first = persist_completed_program(
            self.root, projection(), [lesson_document()],
            max_lessons=5, timestamp=STAMP,
        )
        second = persist_completed_program(
            self.root, projection(), [lesson_document()],
            max_lessons=5, timestamp=STAMP + timedelta(minutes=1),
        )
        self.assertEqual(first["delivery_record_hash"], second["delivery_record_hash"])
        self.assertEqual(first["lesson_hashes"], second["lesson_hashes"])
        store = knowledge.EarnedRecordStore(self.root)
        self.assertEqual(len(store.read("delivery-record")), 1)
        self.assertEqual(len(store.read("lesson")), 1)

    def test_second_packet_prefers_superseding_lesson_and_keeps_chain(self):
        first = persist_completed_program(
            self.root, projection(), [lesson_document()],
            max_lessons=5, timestamp=STAMP,
        )
        old_hash = first["lesson_hashes"][0]
        second_projection = projection("program-" + "2" * 24)
        second = persist_completed_program(
            self.root,
            second_projection,
            [lesson_document(
                "Delivery write-back belongs only at terminal completion.",
                supersedes=old_hash,
                locations=["pkg.delivery.deliver"],
            )],
            max_lessons=5,
            timestamp=STAMP + timedelta(hours=1),
        )
        packet = self.packet()
        self.assertEqual(len(packet["lessons"]), 1)
        lesson = packet["lessons"][0]
        self.assertEqual(lesson["record_hash"], second["lesson_hashes"][0])
        self.assertEqual(lesson["supersession_chain"], [old_hash])
        self.assertEqual(lesson["origin"], second_projection["run_id"])
        self.assertEqual(lesson["head_sha"], HEAD)
        self.assertEqual(lesson["age_label"], "recorded-at:2026-07-26T13:00:00Z")

        source_sections = {
            key: packet[key]
            for key in (
                "verified_locations", "snippets", "test_references",
                "grounding_status", "criteria_sha256", "index_tree",
                "starts_work", "authorizes", "satisfies_gate",
                "substitutes_for_evidence",
            )
        }
        shutil.rmtree(self.git_dir / "pmo-knowledge" / "earned")
        without = self.packet()
        self.assertEqual(without["lessons"], [])
        self.assertEqual(source_sections, {key: without[key] for key in source_sections})

    def packet(self):
        records = knowledge.EarnedRecordStore(self.root).read("lesson")
        return build_knowledge_packet(
            "Keep delivery terminal with bounded write-back.",
            GROUNDING,
            DOCUMENT,
            {"pkg/delivery.py": SOURCE},
            records,
            story="story.md",
        )

    def test_lesson_inventory_lists_provenance_and_supersession(self):
        result = persist_completed_program(
            self.root, projection(), [lesson_document()],
            max_lessons=5, timestamp=STAMP,
        )
        inventory = knowledge.build_lesson_inventory(self.root)
        self.assertEqual(inventory["count"], 1)
        self.assertEqual(inventory["lessons"][0]["record_hash"], result["lesson_hashes"][0])
        self.assertEqual(inventory["lessons"][0]["origin"], projection()["run_id"])
        self.assertFalse(inventory["authorizes"])


def evidence_scenario() -> dict:
    root = Path(tempfile.mkdtemp(prefix="dw-writeback-evidence."))
    git_dir = root / ".git"
    git_dir.mkdir()
    try:
        with mock.patch.object(knowledge.repofacts, "git_dir", return_value=git_dir), mock.patch(
            "dw_pmo.knowledge_writeback._symbol_model", return_value=MODEL
        ):
            abandoned = persist_completed_program(
                root, projection(state="cancelled"), [lesson_document()],
                max_lessons=1, timestamp=STAMP,
            )
            first = persist_completed_program(
                root, projection(), [lesson_document()],
                max_lessons=1, timestamp=STAMP,
            )
            old_hash = first["lesson_hashes"][0]
            second = persist_completed_program(
                root,
                projection("program-" + "2" * 24),
                [lesson_document(
                    "Terminal delivery lessons help the next plan.",
                    supersedes=old_hash,
                    locations=["pkg.delivery.deliver"],
                )],
                max_lessons=1,
                timestamp=STAMP + timedelta(hours=1),
            )
            records = knowledge.EarnedRecordStore(root).read("lesson")
            packet = build_knowledge_packet(
                "Plan terminal delivery lessons.", GROUNDING, DOCUMENT,
                {"pkg/delivery.py": SOURCE}, records, story="next-story.md",
            )
            return {
                "kind": "delivery-workbench-writeback-evidence",
                "terminal_completion": first["status"],
                "delivery_records": len(
                    knowledge.EarnedRecordStore(root).read("delivery-record")
                ),
                "abandoned_lessons": abandoned["lessons"],
                "per_run_cap": 1,
                "retrieved_lessons": len(packet["lessons"]),
                "retrieved_run": packet["lessons"][0]["origin"],
                "provenance_head": packet["lessons"][0]["head_sha"],
                "age_label": packet["lessons"][0]["age_label"],
                "superseding_hash": second["lesson_hashes"][0],
                "supersession_chain": packet["lessons"][0]["supersession_chain"],
                "unresolved_marked": any(
                    location["status"] == "unresolved"
                    for location in knowledge.decode_lesson_locations(
                        records[0]["detail"]["locations"]
                    )
                ),
                "authority": False,
            }
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(KnowledgeWritebackTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("WLA-29-07 EVIDENCE " + json.dumps(evidence_scenario(), sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
