#!/usr/bin/env python3
"""WLA-29-07 delivery lessons and WLA-35-04 terminal memory writeback proof."""

from __future__ import annotations

import hashlib
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
from dw_pmo.memory_dispatch import persist_recall_slices  # noqa: E402
from dw_pmo.memory_read import (  # noqa: E402
    build_memory_recall_projection,
    build_memory_record_projection,
    build_memory_writeback_projection,
    render_memory_projection,
)
from dw_pmo.knowledge_writeback import (  # noqa: E402
    LESSON_OUTPUT_KIND,
    build_terminal_writeback,
    delivery_detail_from_projection,
    ensure_terminal_writeback,
    parse_lesson_output,
    persist_completed_program,
    persist_terminal_writeback,
    read_terminal_writeback_status,
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


def terminal_projection(state="complete", *, event_ref=None):
    terminal = {
        "awaiting-certification": "succeeded",
        "expired": "timed-out",
    }.get(state, "failed" if state == "blocked" else state)
    return {
        "run_id": "run-" + "1" * 24,
        "state": state,
        "terminal_event_ref": event_ref or "sha256:" + "d" * 64,
        "head_sha": HEAD,
        "story": {"id": "WLA-35-04"},
        "memory_recalls": [],
        "request_history": [{
            "correlation_id": "req-" + "2" * 24,
            "response_hash": "sha256:" + "3" * 64,
        }],
        "checkpoints": [],
        "node_receipts": [
            {"executor": "driver", "receipt_hash": "sha256:" + "4" * 64},
            {"executor": "check", "receipt_hash": "sha256:" + "5" * 64},
        ],
        "completed_claims": (
            [] if terminal in {"complete", "succeeded"} else [{
                "node_id": "implement", "attempt": 1,
                "outcome": "lost" if terminal == "lost" else "failed",
                "reason": "bounded failure",
            }]
        ),
        "routes": ([{"action": "exhausted"}] if terminal == "exhausted" else []),
        "budgets": {"max_wall_seconds": {"used": 0, "limit": 100}},
        "expired": state == "expired",
        "delivery_facts": None,
    }


def recall_manifest(run_dir):
    memory = run_dir / "memory"
    memory.mkdir(parents=True)
    unsigned = {
        "kind": "delivery-workbench-memory-recall-manifest",
        "schema_version": 1,
        "subject": "run-" + "1" * 24,
        "source_revision": "sha256:" + "6" * 64,
        "source_heads": {"index_tree": TREE},
        "source_hash": "sha256:" + "7" * 64,
        "audiences": {
            "coordinator": "sha256:" + "8" * 64,
            "implementer": "sha256:" + "9" * 64,
        },
    }
    unsigned["manifest_hash"] = "sha256:" + hashlib.sha256(
        json.dumps(
            unsigned, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    (memory / "manifest.json").write_text(
        json.dumps(unsigned, sort_keys=True) + "\n", encoding="utf-8"
    )


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

    def test_every_terminal_outcome_builds_a_closed_bounded_receipt(self):
        successful = {"complete", "succeeded"}
        states = (
            "complete", "succeeded", "failed", "cancelled", "revoked",
            "lost", "timed-out", "exhausted",
        )
        for state in states:
            document = build_terminal_writeback(
                origin_kind="run",
                origin="run-" + "1" * 24,
                terminal_state=state,
                subject="sha256:" + "1" * 64,
                head_sha=HEAD,
                terminal_event_ref="sha256:" + "2" * 64,
                story_ids=["WLA-35-04"],
                recalled_memory_ids=["sha256:" + "3" * 64],
                decision_refs=["sha256:" + "4" * 64],
                evidence_refs=["sha256:" + "5" * 64],
                check_refs=["sha256:" + "6" * 64],
                changed_files=["pkg/delivery.py"],
                failure_signatures=(
                    [] if state in successful else ["sha256:" + "7" * 64]
                ),
                accepted_lesson_hashes=["sha256:" + "8" * 64],
                discarded_lesson_count=2,
                source_revision="sha256:" + "9" * 64,
            )
            self.assertEqual(
                set(document),
                set(knowledge.MEMORY_DOCUMENT_FIELDS[knowledge.MEMORY_WRITEBACK_KIND]),
            )
            self.assertEqual(
                document["memory_state"],
                "confirmed" if state in successful else "candidate",
            )
            self.assertLessEqual(
                len(json.dumps(document, sort_keys=True).encode("utf-8")),
                knowledge.MEMORY_DOCUMENT_BYTE_CAPS[knowledge.MEMORY_WRITEBACK_KIND]["document"],
            )
            for forbidden in (
                "prompt", "transcript", "tool_output", "credentials", "thinking",
            ):
                self.assertNotIn(forbidden, document)

    def test_terminal_writeback_persists_manifest_recall_ids_and_exact_facts(self):
        run_dir = self.root / "run-store" / ("run-" + "1" * 24)
        recall_manifest(run_dir)
        result = persist_terminal_writeback(
            self.root,
            run_dir,
            projection=terminal_projection(),
            origin_kind="run",
            timestamp=STAMP,
            discarded_lesson_count=3,
        )
        document = result["document"]
        self.assertEqual(document["terminal_state"], "complete")
        self.assertEqual(document["story_ids"], ["WLA-35-04"])
        self.assertEqual(document["recalled_memory_ids"], [
            "sha256:" + "8" * 64,
            "sha256:" + "9" * 64,
        ])
        self.assertEqual(document["decision_refs"], [
            "req-" + "2" * 24,
            "sha256:" + "3" * 64,
        ])
        self.assertEqual(document["evidence_refs"], ["sha256:" + "4" * 64])
        self.assertEqual(document["check_refs"], ["sha256:" + "5" * 64])
        self.assertEqual(document["discarded_lesson_count"], 3)
        self.assertEqual(document["failure_signatures"], [])
        receipt_path = Path(result["receipt_path"])
        self.assertTrue(receipt_path.is_file())
        records = knowledge.EarnedRecordStore(self.root).read(
            knowledge.TERMINAL_OUTCOME_KIND
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["detail"]["receipt_id"], document["writeback_id"])
        self.assertEqual(records[0]["detail"]["memory_state"], "confirmed")

    def test_terminal_replay_deduplicates_receipt_and_earned_outcome(self):
        run_dir = self.root / "run-store" / ("run-" + "1" * 24)
        recall_manifest(run_dir)
        first = persist_terminal_writeback(
            self.root, run_dir, projection=terminal_projection(),
            origin_kind="run", timestamp=STAMP,
        )
        second = persist_terminal_writeback(
            self.root, run_dir, projection=terminal_projection(),
            origin_kind="run", timestamp=STAMP + timedelta(minutes=1),
        )
        self.assertEqual(first["writeback_id"], second["writeback_id"])
        self.assertEqual(first["record_hash"], second["record_hash"])
        self.assertTrue(second["deduplicated"])
        self.assertEqual(
            len(knowledge.EarnedRecordStore(self.root).read(
                knowledge.TERMINAL_OUTCOME_KIND
            )),
            1,
        )
        self.assertEqual(len(list((run_dir / "memory" / "writebacks").iterdir())), 1)

    def test_crash_after_earned_append_replays_the_same_receipt(self):
        run_dir = self.root / "run-store" / ("run-" + "1" * 24)
        recall_manifest(run_dir)
        from dw_pmo import knowledge_writeback

        real_atomic = knowledge_writeback._atomic_json
        crashed = {"done": False}

        def crash_once(path, value):
            if path.parent.name == "writebacks" and not crashed["done"]:
                crashed["done"] = True
                raise OSError("planted crash after earned append")
            return real_atomic(path, value)

        with mock.patch(
            "dw_pmo.knowledge_writeback._atomic_json", side_effect=crash_once
        ):
            with self.assertRaises(OSError):
                persist_terminal_writeback(
                    self.root, run_dir, projection=terminal_projection(),
                    origin_kind="run", timestamp=STAMP,
                )
        self.assertEqual(
            len(knowledge.EarnedRecordStore(self.root).read(
                knowledge.TERMINAL_OUTCOME_KIND
            )),
            1,
        )
        replayed = persist_terminal_writeback(
            self.root, run_dir, projection=terminal_projection(),
            origin_kind="run", timestamp=STAMP + timedelta(minutes=1),
        )
        self.assertEqual(replayed["status"], "persisted")
        self.assertEqual(
            len(knowledge.EarnedRecordStore(self.root).read(
                knowledge.TERMINAL_OUTCOME_KIND
            )),
            1,
        )
        self.assertEqual(len(list((run_dir / "memory" / "writebacks").iterdir())), 1)

    def test_program_terminal_vocabulary_maps_expiry_without_confirming_it(self):
        run_dir = self.root / "program-store" / ("program-" + "1" * 24)
        recall_manifest(run_dir)
        for index, state in enumerate(("cancelled", "revoked", "exhausted", "expired")):
            current = terminal_projection(
                state, event_ref="sha256:" + format(index + 10, "064x")
            )
            current.update({
                "run_id": "program-" + "1" * 24,
                "selected_stories": ["WLA-35-04"],
                "scope": {"story_ids": ["WLA-35-04"]},
                "expected_repository": {"head": HEAD},
                "delivery_facts": None,
            })
            result = persist_terminal_writeback(
                self.root, run_dir, projection=current,
                origin_kind="program",
                timestamp=STAMP + timedelta(minutes=index),
            )
            self.assertEqual(
                result["document"]["terminal_state"],
                "timed-out" if state == "expired" else state,
            )
            self.assertEqual(result["document"]["memory_state"], "candidate")

    def test_unsuccessful_outcome_is_candidate_and_supersession_appends(self):
        run_dir = self.root / "run-store" / ("run-" + "1" * 24)
        recall_manifest(run_dir)
        failed = persist_terminal_writeback(
            self.root, run_dir, projection=terminal_projection("blocked"),
            origin_kind="run", timestamp=STAMP,
        )
        self.assertEqual(failed["document"]["terminal_state"], "failed")
        self.assertEqual(failed["document"]["memory_state"], "candidate")
        self.assertTrue(failed["document"]["failure_signatures"])

        corrected_projection = terminal_projection(
            "blocked", event_ref="sha256:" + "e" * 64
        )
        corrected = persist_terminal_writeback(
            self.root,
            run_dir,
            projection=corrected_projection,
            origin_kind="run",
            timestamp=STAMP + timedelta(minutes=1),
            supersedes=failed["record_hash"],
        )
        self.assertEqual(corrected["document"]["memory_state"], "superseded")
        records = knowledge.EarnedRecordStore(self.root).read(
            knowledge.TERMINAL_OUTCOME_KIND
        )
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["record_hash"], failed["record_hash"])
        self.assertEqual(records[1]["detail"]["supersedes"], failed["record_hash"])

    def test_writeback_failure_is_action_needed_and_not_retried_implicitly(self):
        run_dir = self.root / "run-store" / ("run-" + "1" * 24)
        recall_manifest(run_dir)
        terminal = terminal_projection("cancelled")
        with mock.patch(
            "dw_pmo.knowledge_writeback.persist_terminal_writeback",
            side_effect=DwError("earned store unavailable"),
        ) as adapter:
            first = ensure_terminal_writeback(
                self.root, run_dir, projection=terminal, origin_kind="run",
                timestamp=STAMP,
            )
            second = ensure_terminal_writeback(
                self.root, run_dir, projection=terminal, origin_kind="run",
                timestamp=STAMP + timedelta(minutes=1),
            )
        self.assertEqual(adapter.call_count, 1)
        self.assertEqual(first["status"], "action-needed")
        self.assertEqual(second["status"], "action-needed")
        self.assertEqual(terminal["state"], "cancelled")
        self.assertEqual(terminal["terminal_event_ref"], "sha256:" + "d" * 64)
        self.assertEqual(read_terminal_writeback_status(run_dir), first)
        self.assertEqual(
            knowledge.EarnedRecordStore(self.root).read(
                knowledge.TERMINAL_OUTCOME_KIND
            ),
            [],
        )

    def test_writeback_failure_reaches_needs_you_without_changing_terminal_state(self):
        from dw_pmo.bounded_actions import _program_inbox, _run_inbox
        from dw_pmo.orthogonal_state import _derive_attention

        failure = {
            "status": "action-needed",
            "terminal_event_ref": "sha256:" + "d" * 64,
            "reason": "terminal writeback failed: earned store unavailable",
        }
        run_projection = terminal_projection("cancelled")
        run_projection["memory_writeback"] = failure
        run_inbox = _run_inbox(run_projection, {"blocked": []}, [], [])
        self.assertEqual(run_inbox[0]["id"], "blocker:memory-writeback")
        self.assertEqual(run_inbox[0]["source"]["path"], "/memory_writeback")
        self.assertEqual(run_projection["state"], "cancelled")

        program_projection = {
            "state": "revoked",
            "selection": {"story": "WLA-35-04"},
            "outstanding_requests": [],
            "blocking_obligations": [],
            "memory_writeback": failure,
        }
        program_inbox = _program_inbox(
            program_projection, {"stop": "scope-complete"}, [], None
        )
        self.assertEqual(program_inbox[0]["id"], "blocker:memory-writeback")
        self.assertEqual(program_projection["state"], "revoked")

        attention, detail = _derive_attention(
            "WLA-35-04",
            "in-progress",
            [{
                "valid": True,
                "run": {
                    "story": {"id": "WLA-35-04"},
                    "memory_writeback": failure,
                    "outstanding_requests": [],
                    "state": "cancelled",
                },
            }],
            [],
        )
        self.assertEqual(attention, "blocked")
        self.assertEqual(detail["kind"], "memory-writeback-action-needed")

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

    def _persist_memory_recall(self, run_id):
        run_dir = self.git_dir / "pmo-orchestration" / "runs" / run_id
        persist_recall_slices(
            run_dir,
            subject=run_id,
            knowledge={
                "index_tree": TREE,
                "verified_locations": [{
                    "file": "pkg/delivery.py",
                    "symbol": "pkg.delivery.deliver",
                }],
                "snippets": [],
                "test_references": [],
                "lessons": [{
                    "record_hash": "sha256:" + "e" * 64,
                    "claim": "An unrelated lesson that should be excluded.",
                    "delivery_state": "candidate",
                    "confidence": "high",
                }],
            },
            story_criteria="Change pkg/delivery.py at pkg.delivery.deliver.",
            story_ids=["WLA-35-05"],
            phase_ids=["35"],
            orchestration_tags=["memory-read"],
        )
        return run_dir

    def test_memory_read_groups_recall_writeback_and_ledger_coordinates(self):
        run_id = "run-" + "1" * 24
        run_dir = self._persist_memory_recall(run_id)
        persisted = persist_terminal_writeback(
            self.root,
            run_dir,
            projection=terminal_projection(),
            origin_kind="run",
            timestamp=STAMP,
        )

        recalled = build_memory_recall_projection(self.root, run=run_id)
        self.assertEqual(recalled["status"], "ok")
        self.assertEqual(
            set(recalled["groups"]),
            {"recalled", "used-as-basis", "written-back", "superseded", "excluded"},
        )
        self.assertEqual(len(recalled["groups"]["recalled"]), 5)
        self.assertEqual(len(recalled["groups"]["excluded"]), 5)
        self.assertEqual(recalled["groups"]["used-as-basis"], [])
        self.assertEqual(len(recalled["groups"]["written-back"]), 1)
        written = recalled["groups"]["written-back"][0]
        self.assertEqual(written["record_hash"], persisted["record_hash"])
        self.assertEqual(written["story_ids"], ["WLA-35-04"])
        self.assertEqual(written["ledger_coordinates"]["seq"], 0)
        self.assertIn("terminal-outcome.jsonl", written["ledger_coordinates"]["path"])
        self.assertEqual(render_memory_projection(recalled), json.dumps(
            recalled, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ))

        filtered = build_memory_writeback_projection(
            self.root, run=run_id, story="WLA-35-04", state="confirmed"
        )
        self.assertEqual(filtered["status"], "ok")
        self.assertEqual(filtered["count"], 1)
        self.assertEqual(filtered["writebacks"][0]["writeback_id"], persisted["writeback_id"])
        self.assertEqual(
            build_memory_writeback_projection(
                self.root, run=run_id, story="WLA-99-99"
            )["count"],
            0,
        )

        record = build_memory_record_projection(self.root, persisted["record_hash"])
        self.assertEqual(record["status"], "ok")
        self.assertEqual(len(record["groups"]["written-back"]), 1)
        self.assertEqual(
            record["groups"]["written-back"][0]["record_hash"],
            persisted["record_hash"],
        )

    def test_memory_read_groups_supersession_without_losing_hashes(self):
        run_id = "run-" + "1" * 24
        run_dir = self._persist_memory_recall(run_id)
        first = persist_terminal_writeback(
            self.root, run_dir, projection=terminal_projection(),
            origin_kind="run", timestamp=STAMP,
        )
        second_projection = terminal_projection(
            event_ref="sha256:" + "f" * 64
        )
        second = persist_terminal_writeback(
            self.root, run_dir, projection=second_projection,
            origin_kind="run", timestamp=STAMP + timedelta(minutes=1),
            supersedes=first["record_hash"],
        )

        result = build_memory_recall_projection(self.root, run=run_id)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["groups"]["written-back"], [])
        self.assertEqual(
            {entry["record_hash"] for entry in result["groups"]["superseded"]},
            {first["record_hash"], second["record_hash"]},
        )
        prior = next(
            entry for entry in result["groups"]["superseded"]
            if entry["record_hash"] == first["record_hash"]
        )
        self.assertEqual(prior["superseded_by"], second["record_hash"])

    def test_memory_read_refuses_missing_stale_malformed_and_tampered_sources(self):
        missing_run = "run-" + "2" * 24
        missing = build_memory_recall_projection(self.root, run=missing_run)
        self.assertEqual(missing["status"], "refused")
        self.assertEqual(missing["refusal"]["reason"], "missing")
        self.assertTrue(all(not values for values in missing["groups"].values()))

        malformed_run = "run-" + "3" * 24
        malformed_dir = self._persist_memory_recall(malformed_run)
        (malformed_dir / "memory" / "source.json").write_text("{", encoding="utf-8")
        malformed = build_memory_recall_projection(self.root, run=malformed_run)
        self.assertEqual(malformed["refusal"]["reason"], "malformed")

        tampered_run = "run-" + "4" * 24
        tampered_dir = self._persist_memory_recall(tampered_run)
        recall_path = tampered_dir / "memory" / "recalls" / "shared.json"
        recall = json.loads(recall_path.read_text(encoding="utf-8"))
        recall["items"][0]["summary"] = "changed after persistence"
        recall_path.write_text(json.dumps(recall), encoding="utf-8")
        tampered = build_memory_recall_projection(self.root, run=tampered_run)
        self.assertEqual(tampered["refusal"]["reason"], "tampered")

        stale_run = "run-" + "5" * 24
        stale_dir = self._persist_memory_recall(stale_run)
        memory = stale_dir / "memory"
        source_path = memory / "source.json"
        manifest_path = memory / "manifest.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))
        source["index_tree"] = "c" * 40
        source_path.write_text(json.dumps(source), encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        source_hash = "sha256:" + hashlib.sha256(json.dumps(
            source, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")).hexdigest()
        manifest["source_hash"] = source_hash
        manifest["source_heads"] = {
            "index_tree": source["index_tree"], "knowledge_packet": source_hash,
        }
        manifest["source_revision"] = "sha256:" + hashlib.sha256(json.dumps(
            {"subject": stale_run, "knowledge": source},
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")).hexdigest()
        unsigned = {key: value for key, value in manifest.items() if key != "manifest_hash"}
        manifest["manifest_hash"] = "sha256:" + hashlib.sha256(json.dumps(
            unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        stale = build_memory_recall_projection(self.root, run=stale_run)
        self.assertEqual(stale["refusal"]["reason"], "stale")

    def test_memory_writeback_read_refuses_a_tampered_receipt(self):
        run_id = "run-" + "1" * 24
        run_dir = self._persist_memory_recall(run_id)
        persisted = persist_terminal_writeback(
            self.root, run_dir, projection=terminal_projection(),
            origin_kind="run", timestamp=STAMP,
        )
        receipt_path = Path(persisted["receipt_path"])
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["terminal_state"] = "failed"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        result = build_memory_writeback_projection(self.root, run=run_id)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["refusal"]["reason"], "tampered")
        self.assertEqual(result["writebacks"], [])

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
