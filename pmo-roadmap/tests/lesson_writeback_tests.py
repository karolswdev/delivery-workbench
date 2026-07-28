#!/usr/bin/env python3
"""WLA-30-09 certified-handoff lesson write-back proof."""

from __future__ import annotations

import hashlib
import inspect
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

TESTS_DIR = Path(__file__).resolve().parent
LIB_DIR = TESTS_DIR.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

from dw_pmo import knowledge  # noqa: E402
from dw_pmo.knowledge_packet import build_knowledge_packet  # noqa: E402
from dw_pmo.knowledge_writeback import (  # noqa: E402
    CERTIFIED_HANDOFF_STATE,
    CERTIFIED_HANDOFF_STOP,
    LESSON_OUTPUT_KIND,
    certified_lesson_receipt_id,
    observe_lesson_integration,
    persist_certified_handoff,
)
from dw_pmo.model import DwError  # noqa: E402
from dw_pmo.program_run import _CLAIM_RULES, _capability_issues  # noqa: E402
from dw_pmo.programs import PROGRAM_CAPABILITIES  # noqa: E402


RUN_ID = "program-" + "1" * 24
HEAD = "a" * 40
COMMIT = "b" * 40
SUBJECT = "sha256:" + "c" * 64
VERDICT = "sha256:" + "d" * 64
TERMINAL_RECEIPT = "sha256:" + "e" * 64
STAMP = datetime(2026, 7, 27, 12, 0, tzinfo=timezone.utc)
TREE = "f" * 40
MODEL = {
    "kind": "delivery-workbench-symbol-structure-map",
    "schema_version": 1,
    "index_tree": TREE,
    "tracked_files": [{"path": "pkg/front.py", "blob": "1" * 40, "size": 20}],
    "modules": [],
    "gaps": [],
    "symbols": [{
        "kind": "function",
        "name": "handoff",
        "qualified_name": "pkg.front.handoff",
        "file": "pkg/front.py",
        "line_start": 1,
        "line_end": 2,
    }],
    "test_map": {},
}
GROUNDING = {
    "kind": "delivery-workbench-story-grounding",
    "schema_version": 1,
    "status": "grounded",
    "story": "story.md",
    "index_tree": TREE,
    "affected_files": [],
    "target_symbols": [{
        "kind": "target-symbol",
        "hint": "handoff",
        "declared_new": False,
        "classification": "verified",
        "locations": [{
            "file": "pkg/front.py", "line_start": 1, "line_end": 2,
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
DOCUMENT = {"index_tree": TREE, "value": MODEL}


def lesson_document(claim="Certified handoff keeps lesson status visible."):
    return {
        "kind": LESSON_OUTPUT_KIND,
        "schema_version": 1,
        "lessons": [{
            "claim": claim,
            "locations": ["pkg.front.handoff"],
            "confidence": "high",
            "supersedes": "",
        }],
    }


def emission(claim="Certified handoff keeps lesson status visible."):
    return {
        "document": lesson_document(claim),
        "adapter": "fixture-adapter",
        "driver_profile": "fixture-profile",
        "emitter_receipt": "sha256:" + "9" * 64,
    }


class LessonWritebackTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dw-certified-lesson-test."))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.git_dir = self.root / ".git"
        self.git_dir.mkdir()
        git_patch = mock.patch.object(
            knowledge.repofacts, "git_dir", return_value=self.git_dir
        )
        git_patch.start()
        self.addCleanup(git_patch.stop)
        symbol_patch = mock.patch(
            "dw_pmo.knowledge_writeback._symbol_model", return_value=MODEL
        )
        symbol_patch.start()
        self.addCleanup(symbol_patch.stop)

    def persist(self, **updates):
        values = {
            "root": self.root,
            "run_id": RUN_ID,
            "story": "WLA-30-09",
            "subject": SUBJECT,
            "head_sha": HEAD,
            "verdict_ref": VERDICT,
            "terminal_receipt_id": TERMINAL_RECEIPT,
            "lesson_emissions": [emission()],
            "max_lessons": 1,
            "frontier_state": CERTIFIED_HANDOFF_STATE,
            "frontier_stop": CERTIFIED_HANDOFF_STOP,
            "timestamp": STAMP,
        }
        values.update(updates)
        root = values.pop("root")
        return persist_certified_handoff(root, **values)

    def test_no_commit_capability_is_narrow_and_independently_budgeted(self):
        capability = "knowledge:lesson-writeback"
        self.assertIn(capability, PROGRAM_CAPABILITIES)
        granted = {
            "program:select", "agent:dispatch", "check:execute",
            "workspace:write", "verdict:issue", capability,
        }
        self.assertEqual(
            _capability_issues("checkpointed", sorted(granted), sorted(granted)),
            [],
        )
        forbidden = {
            "integration:apply", "contract:generate",
            "certification:objective", "certification:verdict",
            "git:commit", "git:push", "roadmap:story-start",
            "roadmap:story-complete", "roadmap:phase-advance",
        }
        self.assertFalse(granted & forbidden)
        self.assertEqual(
            _CLAIM_RULES["lesson-writeback"],
            (capability, "record", {"max_lesson_writebacks": 1}),
        )

    def test_two_run_packet_keeps_certified_not_integrated_label(self):
        result = self.persist()
        self.assertEqual(result["new_lessons"], 1)
        record = knowledge.EarnedRecordStore(self.root).read(
            knowledge.CERTIFIED_LESSON_KIND
        )[0]
        detail = record["detail"]
        self.assertEqual(detail["delivery_state"], "certified-not-integrated")
        self.assertEqual(detail["story"], "WLA-30-09")
        self.assertEqual(detail["subject"], SUBJECT)
        self.assertEqual(detail["adapter"], "fixture-adapter")
        self.assertEqual(detail["driver_profile"], "fixture-profile")
        self.assertEqual(detail["verdict_ref"], VERDICT)
        self.assertEqual(record["origin"], RUN_ID)

        packet = build_knowledge_packet(
            "A later run should use the certified handoff lesson.",
            GROUNDING,
            DOCUMENT,
            {"pkg/front.py": b"def handoff():\n    pass\n"},
            knowledge.read_lesson_knowledge(self.root),
            story="second-run.md",
        )
        self.assertEqual(len(packet["lessons"]), 1)
        retrieved = packet["lessons"][0]
        self.assertEqual(retrieved["delivery_state"], "certified-not-integrated")
        self.assertEqual(retrieved["receipt_id"], result["receipt_ids"][0])
        self.assertEqual(retrieved["origin"], RUN_ID)

    def test_every_non_success_terminal_persists_nothing(self):
        # Program authority states are advisory/running/checkpoint/paused/expired/
        # exhausted/revoked/cancelled/complete. Running is not terminal; its
        # uncertified and malformed/refused/failed/lost outcomes are represented
        # by stopped frontiers. Only the exact pair below may write.
        terminals = [
            ("advisory", "authority-not-running"),
            ("checkpoint", "authority-not-running"),
            ("paused", "authority-not-running"),
            ("expired", "authority-not-running"),
            ("exhausted", "authority-not-running"),
            ("revoked", "authority-not-running"),
            ("cancelled", "authority-not-running"),
            ("complete", "authority-not-running"),
            ("stopped", "failed"),
            ("stopped", "refused"),
            ("stopped", "lost"),
            ("stopped", "malformed"),
            ("stopped", "uncertified"),
            ("stopped", "cancelled"),
            ("story-certified", "malformed"),
            ("story-certified", "uncertified"),
            ("running", None),
        ]
        for state, stop in terminals:
            with self.subTest(state=state, stop=stop):
                result = self.persist(frontier_state=state, frontier_stop=stop)
                self.assertEqual(result["lessons"], 0)
        self.assertFalse((self.git_dir / "pmo-knowledge" / "earned").exists())

    def test_crash_replay_receipt_is_idempotent_and_budget_stays_one(self):
        # The conductor reserves one max_lesson_writebacks unit before this
        # append. A planted crash after append but before claim completion reuses
        # the active idempotency key; this replay reports no new write.
        first = self.persist()
        replay = self.persist(timestamp=STAMP + timedelta(minutes=1))
        self.assertEqual(first["receipt_ids"], replay["receipt_ids"])
        self.assertEqual(first["lesson_hashes"], replay["lesson_hashes"])
        self.assertEqual(first["new_lessons"], 1)
        self.assertEqual(replay["new_lessons"], 0)
        self.assertEqual(replay["deduplicated_lessons"], 1)
        self.assertEqual(
            len(knowledge.EarnedRecordStore(self.root).read(
                knowledge.CERTIFIED_LESSON_KIND
            )),
            1,
        )
        self.assertEqual(
            _CLAIM_RULES["lesson-writeback"][2]["max_lesson_writebacks"], 1
        )

        normalized = lesson_document()["lessons"][0]
        expected = "sha256:" + hashlib.sha256(json.dumps({
            "kind": "delivery-workbench-certified-lesson-receipt",
            "schema_version": 1,
            "terminal_receipt_id": TERMINAL_RECEIPT,
            "ordinal": 0,
            "lesson": normalized,
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(
            certified_lesson_receipt_id(TERMINAL_RECEIPT, 0, normalized),
            expected,
        )

    def test_confirm_and_supersede_are_append_only_closed_observations(self):
        self.persist()
        original = knowledge.EarnedRecordStore(self.root).read(
            knowledge.CERTIFIED_LESSON_KIND
        )[0]
        confirmed = observe_lesson_integration(
            self.root,
            run_id=RUN_ID,
            story="WLA-30-09",
            commit_sha=COMMIT,
            delivery_state="confirmed",
            timestamp=STAMP + timedelta(minutes=1),
        )
        superseded = observe_lesson_integration(
            self.root,
            run_id=RUN_ID,
            story="WLA-30-09",
            commit_sha="c" * 40,
            delivery_state="superseded",
            timestamp=STAMP + timedelta(minutes=2),
        )
        self.assertEqual(confirmed["new_observations"], 1)
        self.assertEqual(superseded["new_observations"], 1)
        store = knowledge.EarnedRecordStore(self.root)
        self.assertEqual(
            store.read(knowledge.CERTIFIED_LESSON_KIND)[0], original
        )
        self.assertEqual(
            original["detail"]["delivery_state"],
            "certified-not-integrated",
        )
        self.assertEqual(
            len(store.read(knowledge.LESSON_DELIVERY_OBSERVATION_KIND)), 2
        )
        resolved = knowledge.read_lesson_knowledge(self.root)[0]
        self.assertEqual(resolved["effective_delivery_state"], "superseded")
        with self.assertRaises(DwError):
            observe_lesson_integration(
                self.root,
                run_id=RUN_ID,
                story="WLA-30-09",
                commit_sha=COMMIT,
                delivery_state="landed",
            )

    def test_new_record_kinds_remain_unfit_for_authority(self):
        self.persist()
        observe_lesson_integration(
            self.root,
            run_id=RUN_ID,
            story="WLA-30-09",
            commit_sha=COMMIT,
            timestamp=STAMP + timedelta(minutes=1),
        )
        store = knowledge.EarnedRecordStore(self.root)
        for kind in (
            knowledge.CERTIFIED_LESSON_KIND,
            knowledge.LESSON_DELIVERY_OBSERVATION_KIND,
        ):
            record = store.read(kind)[0]
            for marker in (
                "starts_work", "authorizes", "satisfies_gate",
                "substitutes_for_evidence",
            ):
                self.assertIs(record[marker], False)

        authority_modules = (
            "contract.py", "gate.py", "program_run.py", "program_verdict.py"
        )
        for name in authority_modules:
            source = (LIB_DIR / "dw_pmo" / name).read_text(encoding="utf-8")
            self.assertNotIn("CERTIFIED_LESSON_KIND", source)
            self.assertNotIn("LESSON_DELIVERY_OBSERVATION_KIND", source)
            self.assertNotIn("read_lesson_knowledge", source)

        from dw_pmo import program_delivery
        certification = inspect.getsource(program_delivery._execute_certification)
        self.assertNotIn("lesson", certification.lower())
        self.assertNotIn("knowledge", certification.lower())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(LessonWritebackTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
