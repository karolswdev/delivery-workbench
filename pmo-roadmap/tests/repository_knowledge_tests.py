#!/usr/bin/env python3
"""WLA-29-01 repository-knowledge unit and architecture fitness tests."""

from __future__ import annotations

import ast
import inspect
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

TESTS_DIR = Path(__file__).resolve().parent
LIB_DIR = TESTS_DIR.parent / "lib" / "dw_pmo"
REPOSITORY_ROOT = TESTS_DIR.parent.parent
sys.path.insert(0, str(TESTS_DIR.parent / "lib"))

import dw_pmo.knowledge as knowledge
from dw_pmo import DwError


INDEX_A = "1" * 40
INDEX_B = "2" * 40
HEAD = "a" * 40
STAMP = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)


class RepositoryKnowledgeTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dw-knowledge-test."))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.git_dir = self.root / ".git"
        self.git_dir.mkdir()
        patcher = mock.patch.object(
            knowledge.repofacts, "git_dir", return_value=self.git_dir
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.derived = knowledge.DerivedFactStore(self.root)
        self.earned = knowledge.EarnedRecordStore(self.root)

    @staticmethod
    def delivery_detail(**updates):
        detail = {
            "story_ids": knowledge.encode_identifier_list(["WLA-29-01"], "story_ids"),
            "story_count": "1",
            "files_touched": knowledge.encode_identifier_list(
                ["dw_pmo/knowledge.py"], "files_touched"
            ),
            "file_count": "1",
            "verdict_outcome": "passed",
            "obligation_ids": knowledge.encode_identifier_list([], "obligation_ids"),
            "obligation_count": "0",
        }
        detail.update(updates)
        return detail

    @staticmethod
    def lesson_detail(**updates):
        detail = {
            "claim": "Bind every derived answer to the current index tree.",
            "locations": knowledge.encode_lesson_locations([{
                "reference": "DerivedFactStore.read",
                "status": "resolved",
                "file": "dw_pmo/knowledge.py",
                "symbol": "dw_pmo.knowledge.DerivedFactStore.read",
                "line_start": 301,
                "line_end": 309,
            }]),
            "confidence": "high",
            "supersedes": "",
        }
        detail.update(updates)
        return detail

    @staticmethod
    def terminal_detail(**updates):
        detail = {
            "receipt_id": "sha256:" + "1" * 64,
            "subject": "sha256:" + "2" * 64,
            "terminal_state": "succeeded",
            "memory_state": "confirmed",
            "story_ids": knowledge.encode_identifier_list(
                ["WLA-35-01"], "story_ids"
            ),
            "recalled_memory_ids": knowledge.encode_identifier_list(
                ["sha256:" + "3" * 64], "recalled_memory_ids"
            ),
            "decision_refs": knowledge.encode_identifier_list(
                ["decision-1"], "decision_refs"
            ),
            "evidence_refs": knowledge.encode_identifier_list(
                ["evidence-story-01.md"], "evidence_refs"
            ),
            "check_refs": knowledge.encode_identifier_list(
                ["check-1"], "check_refs"
            ),
            "changed_files": knowledge.encode_identifier_list(
                ["dw_pmo/knowledge.py"], "changed_files"
            ),
            "failure_signatures": knowledge.encode_identifier_list(
                [], "failure_signatures"
            ),
            "accepted_lesson_hashes": knowledge.encode_identifier_list(
                ["sha256:" + "4" * 64], "accepted_lesson_hashes"
            ),
            "discarded_lesson_count": "0",
            "supersedes": "",
        }
        detail.update(updates)
        return detail

    def append_delivery(self, **updates):
        arguments = {
            "origin_kind": "run",
            "origin": "run-29-01",
            "head_sha": HEAD,
            "timestamp": STAMP,
        }
        arguments.update(updates)
        return self.earned.append(
            knowledge.DELIVERY_RECORD_KIND,
            self.delivery_detail(),
            **arguments,
        )

    def append_terminal(self, detail=None, **updates):
        arguments = {
            "origin_kind": "run",
            "origin": "run-35-01",
            "head_sha": HEAD,
            "timestamp": STAMP,
        }
        arguments.update(updates)
        return self.earned.append(
            knowledge.TERMINAL_OUTCOME_KIND,
            detail or self.terminal_detail(),
            **arguments,
        )

    def earned_path(self, kind=knowledge.DELIVERY_RECORD_KIND):
        return (self.git_dir / "pmo-knowledge" / "earned"
                / (kind + ".jsonl"))

    def rewrite_single_record(self, mutate, kind=knowledge.DELIVERY_RECORD_KIND):
        path = self.earned_path(kind)
        record = json.loads(path.read_text(encoding="utf-8"))
        mutate(record)
        unsigned = {key: value for key, value in record.items()
                    if key != "record_hash"}
        record["record_hash"] = knowledge._sha(unsigned)
        path.write_text(knowledge._canonical_json(record) + "\n",
                        encoding="utf-8")

    # -- contract and total classification --------------------------------

    def test_storage_classification_is_total_and_unknowns_refuse(self):
        self.assertEqual(
            set(knowledge.KNOWLEDGE_ITEM_CLASSES),
            {
                knowledge.DERIVED_FACT_KIND,
                knowledge.DELIVERY_RECORD_KIND,
                knowledge.LESSON_KIND,
                knowledge.CERTIFIED_LESSON_KIND,
                knowledge.LESSON_DELIVERY_OBSERVATION_KIND,
                knowledge.TERMINAL_OUTCOME_KIND,
            },
        )
        self.assertEqual(
            {knowledge.storage_class(kind)
             for kind in knowledge.KNOWLEDGE_ITEM_CLASSES},
            set(knowledge.STORAGE_CLASSES),
        )
        self.assertEqual(
            knowledge.storage_class(knowledge.DERIVED_FACT_KIND),
            knowledge.DERIVED,
        )
        for kind in knowledge.EARNED_RECORD_KINDS:
            self.assertEqual(knowledge.storage_class(kind), knowledge.EARNED)
        with self.assertRaises(DwError):
            knowledge.storage_class("plausible-but-undeclared")

    def test_machine_contract_is_versioned_total_and_authority_free(self):
        contract = knowledge.contract_document()
        self.assertEqual(
            contract["contract"],
            "delivery-workbench-repository-knowledge@1",
        )
        self.assertEqual(contract["schema_version"], 1)
        self.assertEqual(set(contract["classes"]), set(knowledge.STORAGE_CLASSES))
        self.assertEqual(
            set(contract["item_classes"]), set(knowledge.KNOWLEDGE_ITEM_CLASSES)
        )
        self.assertEqual(
            contract["authority_exclusion"],
            {
                "mints_authority": False,
                "satisfies_gate": False,
                "substitutes_for_evidence": False,
            },
        )
        json.dumps(contract)

    def test_memory_document_contracts_are_closed_bounded_and_provenance_bound(self):
        expected_fields = {
            "delivery-workbench-memory-recall@1": {
                "kind", "schema_version", "recall_id", "subject", "audience",
                "source_revision", "source_heads", "items", "exclusions",
                "byte_budget", "used_bytes", "starts_work", "authorizes",
                "satisfies_gate", "substitutes_for_evidence",
            },
            "delivery-workbench-memory-writeback@1": {
                "kind", "schema_version", "writeback_id", "origin_kind",
                "origin", "terminal_state", "memory_state", "subject",
                "head_sha", "terminal_event_ref", "story_ids",
                "recalled_memory_ids", "decision_refs", "evidence_refs",
                "check_refs", "changed_files", "failure_signatures",
                "accepted_lesson_hashes", "discarded_lesson_count",
                "source_revision", "starts_work", "authorizes",
                "satisfies_gate", "substitutes_for_evidence",
            },
            "delivery-workbench-decision-basis@1": {
                "kind", "schema_version", "decision_id", "subject",
                "decision_kind", "basis_type", "outcome", "reason_code",
                "rule_ref", "score_ref", "input_receipt_refs",
                "memory_refs", "dissent_refs", "resulting_ledger_event",
                "source_revision", "starts_work", "authorizes",
                "satisfies_gate", "substitutes_for_evidence",
            },
        }
        required_authority = {
            "starts_work": False,
            "authorizes": False,
            "satisfies_gate": False,
            "substitutes_for_evidence": False,
        }
        documents = knowledge.contract_document()["memory_documents"]
        self.assertEqual(set(documents), set(expected_fields))
        for versioned_kind, expected in expected_fields.items():
            with self.subTest(kind=versioned_kind):
                declaration = documents[versioned_kind]
                fields = set(declaration["closed_fields"])
                self.assertEqual(fields, expected)
                self.assertEqual(
                    versioned_kind,
                    "%s@%d" % (
                        declaration["kind"], declaration["schema_version"]
                    ),
                )
                identity = declaration["identity"]
                self.assertIn(identity["field"], fields)
                self.assertEqual(identity["algorithm"], "sha256-canonical-json")
                self.assertEqual(
                    set(identity["inputs"]), fields - {identity["field"]}
                )
                self.assertGreater(declaration["byte_caps"]["document"], 0)
                self.assertTrue(declaration["item_caps"])
                self.assertTrue(all(
                    isinstance(cap, int) and cap > 0
                    for cap in declaration["byte_caps"].values()
                ))
                self.assertTrue(all(
                    isinstance(cap, int) and cap > 0
                    for cap in declaration["item_caps"].values()
                ))
                self.assertLessEqual(
                    set(declaration["provenance_references"]), fields
                )
                self.assertTrue(declaration["provenance_references"])
                self.assertEqual(
                    declaration["authority_fields"], required_authority
                )
                self.assertLessEqual(set(required_authority), fields)

    def test_memory_contract_identity_is_deterministic_and_returned_by_value(self):
        first = knowledge.contract_document()
        second = knowledge.contract_document()
        self.assertEqual(
            knowledge._canonical_json(first), knowledge._canonical_json(second)
        )
        first["memory_documents"]["delivery-workbench-memory-recall@1"][
            "closed_fields"
        ].append("smuggled")
        self.assertNotIn(
            "smuggled",
            knowledge.contract_document()["memory_documents"][
                "delivery-workbench-memory-recall@1"
            ]["closed_fields"],
        )
        self.assertEqual(
            knowledge.contract_document()["memory_states"],
            ["confirmed", "candidate", "superseded"],
        )
        rules = knowledge.contract_document()["memory_state_rules"]
        self.assertEqual(
            rules["confirmed_terminal_states"], ["complete", "succeeded"]
        )
        self.assertEqual(
            set(rules["terminal_states"]), set(knowledge.TERMINAL_OUTCOME_STATES)
        )
        self.assertEqual(
            rules["unsuccessful_terminal_states"],
            "candidate-or-superseded-only",
        )
        self.assertEqual(
            rules["superseded_requires"],
            "earlier-terminal-outcome-record-hash",
        )

    # -- derived facts ------------------------------------------------------

    def test_derived_read_refuses_a_different_current_index_tree(self):
        self.derived.write("symbol-map", INDEX_A, {"symbols": ["main"]})
        with self.assertRaises(knowledge.StaleDerivedFact) as caught:
            self.derived.read("symbol-map", INDEX_B)
        self.assertEqual(caught.exception.stored_index_tree, INDEX_A)
        self.assertEqual(caught.exception.current_index_tree, INDEX_B)

    def test_explicit_recompute_path_replaces_stale_and_reuses_fresh(self):
        self.derived.write("symbol-map", INDEX_A, {"generation": 1})
        calls = []

        def compute():
            calls.append(1)
            return {"generation": 2}

        fresh = self.derived.read_or_recompute("symbol-map", INDEX_B, compute)
        self.assertEqual(fresh["index_tree"], INDEX_B)
        self.assertEqual(fresh["value"], {"generation": 2})
        again = self.derived.read_or_recompute("symbol-map", INDEX_B, compute)
        self.assertEqual(again, fresh)
        self.assertEqual(len(calls), 1)

    def test_incremental_refresh_exposes_old_value_only_to_compute(self):
        old = self.derived.write("symbol-map", INDEX_A, {"files": ["old.py"]})
        seen = []

        def compute(previous):
            seen.append(previous)
            return {"files": ["new.py"]}

        fresh = self.derived.refresh("symbol-map", INDEX_B, compute)
        self.assertEqual(seen, [old])
        self.assertEqual(fresh["value"], {"files": ["new.py"]})
        self.assertEqual(self.derived.read("symbol-map", INDEX_B), fresh)
        with self.assertRaises(knowledge.StaleDerivedFact):
            self.derived.read("symbol-map", INDEX_A)

    def test_deleting_derived_cache_changes_only_recompute_latency(self):
        first = self.derived.read_or_recompute(
            "structure", INDEX_A, lambda: {"paths": ["dw_pmo"]}
        )
        shutil.rmtree(self.git_dir / "pmo-knowledge" / "derived")
        second = self.derived.read_or_recompute(
            "structure", INDEX_A, lambda: {"paths": ["dw_pmo"]}
        )
        self.assertEqual(first, second)

    def test_derived_identity_is_deterministic_and_tamper_refuses(self):
        first = self.derived.write("structure", INDEX_A, {"paths": ["a", "b"]})
        second = self.derived.write("structure", INDEX_A, {"paths": ["a", "b"]})
        self.assertEqual(first, second)
        path = self.derived._path("structure")
        record = json.loads(path.read_text(encoding="utf-8"))
        record["value"]["paths"].append("tampered")
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        with self.assertRaises(knowledge.MalformedKnowledge):
            self.derived.read("structure", INDEX_A)

    # -- earned records -----------------------------------------------------

    def test_earned_shapes_are_closed_and_caps_apply_on_append(self):
        with self.assertRaises(DwError):
            self.earned.append(
                knowledge.DELIVERY_RECORD_KIND,
                dict(self.delivery_detail(), prompt="unbounded channel"),
                origin_kind="run", origin="run-1", head_sha=HEAD,
                timestamp=STAMP,
            )
        for field, cap in knowledge.EARNED_FIELD_CAPS.items():
            kind = (knowledge.LESSON_KIND
                    if field in knowledge.EARNED_RECORD_FIELDS[knowledge.LESSON_KIND]
                    else knowledge.DELIVERY_RECORD_KIND)
            detail = (self.lesson_detail() if kind == knowledge.LESSON_KIND
                      else self.delivery_detail())
            detail[field] = "x" * (cap + 1)
            with self.subTest(field=field), self.assertRaises(DwError):
                self.earned.append(
                    kind, detail, origin_kind="operator", origin="karol",
                    head_sha=HEAD, timestamp=STAMP,
                )

    def test_every_earned_record_requires_valid_provenance(self):
        invalid = (
            {"origin_kind": "agent", "origin": "x", "head_sha": HEAD},
            {"origin_kind": "run", "origin": "", "head_sha": HEAD},
            {"origin_kind": "operator", "origin": "karol", "head_sha": "abc"},
        )
        for arguments in invalid:
            with self.subTest(arguments=arguments), self.assertRaises(DwError):
                self.earned.append(
                    knowledge.DELIVERY_RECORD_KIND,
                    self.delivery_detail(), timestamp=STAMP, **arguments
                )
        record = self.append_delivery()
        self.assertEqual(record["origin_kind"], "run")
        self.assertEqual(record["origin"], "run-29-01")
        self.assertEqual(record["timestamp"], "2026-07-26T12:00:00Z")
        self.assertEqual(record["head_sha"], HEAD)

    def test_delivery_and_lesson_append_as_typed_hash_chains(self):
        delivery = self.append_delivery()
        earlier = self.earned.append(
            knowledge.LESSON_KIND,
            self.lesson_detail(),
            origin_kind="run",
            origin="run-29-01",
            head_sha=HEAD,
            timestamp=STAMP,
        )
        lesson = self.earned.append(
            knowledge.LESSON_KIND,
            self.lesson_detail(
                claim="Prefer the current index tree before every derived read.",
                supersedes=earlier["record_hash"],
            ),
            origin_kind="run",
            origin="run-29-02",
            head_sha=HEAD,
            timestamp=STAMP,
        )
        self.assertEqual(
            self.earned.read(knowledge.DELIVERY_RECORD_KIND), [delivery]
        )
        self.assertEqual(self.earned.read(knowledge.LESSON_KIND), [earlier, lesson])
        for record in (delivery, earlier, lesson):
            self.assertIs(record["starts_work"], False)
            self.assertIs(record["authorizes"], False)
            self.assertIs(record["satisfies_gate"], False)
            self.assertIs(record["substitutes_for_evidence"], False)

    def test_terminal_outcomes_are_typed_bounded_hash_chained_records(self):
        candidate = self.append_terminal(self.terminal_detail(
            receipt_id="sha256:" + "5" * 64,
            terminal_state="failed",
            memory_state="candidate",
            accepted_lesson_hashes=knowledge.encode_identifier_list(
                [], "accepted_lesson_hashes"
            ),
        ))
        confirmed = self.append_terminal(self.terminal_detail(
            receipt_id="sha256:" + "6" * 64,
            terminal_state="succeeded",
            memory_state="confirmed",
            supersedes=candidate["record_hash"],
        ))
        superseded = self.append_terminal(self.terminal_detail(
            receipt_id="sha256:" + "7" * 64,
            terminal_state="failed",
            memory_state="superseded",
            accepted_lesson_hashes=knowledge.encode_identifier_list(
                [], "accepted_lesson_hashes"
            ),
            supersedes=confirmed["record_hash"],
        ))
        self.assertEqual(
            self.earned.read(knowledge.TERMINAL_OUTCOME_KIND),
            [candidate, confirmed, superseded],
        )
        self.assertEqual([candidate["seq"], confirmed["seq"], superseded["seq"]],
                         [0, 1, 2])
        self.assertIsNone(candidate["prev_hash"])
        self.assertEqual(confirmed["prev_hash"], candidate["record_hash"])
        self.assertEqual(superseded["prev_hash"], confirmed["record_hash"])
        self.assertEqual(
            {record["detail"]["memory_state"]
             for record in (candidate, confirmed, superseded)},
            {"confirmed", "candidate", "superseded"},
        )
        for record in (candidate, confirmed, superseded):
            for field in (
                "starts_work", "authorizes", "satisfies_gate",
                "substitutes_for_evidence",
            ):
                self.assertIs(record[field], False)

    def test_unsuccessful_terminal_outcomes_cannot_claim_confirmation(self):
        unsuccessful = set(knowledge.TERMINAL_OUTCOME_STATES) - {
            "complete", "succeeded"
        }
        self.assertGreaterEqual(
            unsuccessful,
            {"failed", "cancelled", "revoked", "lost", "timed-out", "exhausted"},
        )
        for state in sorted(unsuccessful):
            with self.subTest(state=state), self.assertRaisesRegex(
                    DwError, "cannot confirm"):
                self.append_terminal(self.terminal_detail(
                    terminal_state=state,
                    memory_state="confirmed",
                ))
        self.assertEqual(self.earned.read(knowledge.TERMINAL_OUTCOME_KIND), [])

    def test_terminal_outcome_shape_caps_lists_and_supersession_are_validated(self):
        invalid = (
            dict(self.terminal_detail(), prompt="raw transcript"),
            self.terminal_detail(memory_state="agent-says-confirmed"),
            self.terminal_detail(memory_state="superseded"),
            self.terminal_detail(terminal_state="maybe-finished"),
            self.terminal_detail(story_ids='["b","a"]'),
            self.terminal_detail(discarded_lesson_count="-1"),
            self.terminal_detail(accepted_lesson_hashes="[\"not-a-hash\"]"),
            self.terminal_detail(failure_signatures="x" * (
                knowledge.EARNED_FIELD_CAPS["failure_signatures"] + 1
            )),
            self.terminal_detail(supersedes="sha256:" + "8" * 64),
        )
        for detail in invalid:
            with self.subTest(detail=detail), self.assertRaises(DwError):
                self.append_terminal(detail)
        self.assertEqual(self.earned.read(knowledge.TERMINAL_OUTCOME_KIND), [])

    def test_terminal_outcome_read_revalidates_status_and_chain_integrity(self):
        self.append_terminal(self.terminal_detail(
            terminal_state="failed",
            memory_state="candidate",
            accepted_lesson_hashes=knowledge.encode_identifier_list(
                [], "accepted_lesson_hashes"
            ),
        ))
        self.rewrite_single_record(
            lambda record: record["detail"].update({"memory_state": "confirmed"}),
            knowledge.TERMINAL_OUTCOME_KIND,
        )
        with self.assertRaisesRegex(
                knowledge.MalformedKnowledge, "cannot confirm"):
            self.earned.read(knowledge.TERMINAL_OUTCOME_KIND)

    def test_read_revalidates_closed_fields_caps_and_provenance(self):
        mutations = (
            lambda record: record["detail"].update({"prompt": "smuggled"}),
            lambda record: record["detail"].update({"story_ids": "x" * 2049}),
            lambda record: record.update({"head_sha": "not-a-sha"}),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                if self.earned_path().exists():
                    self.earned_path().unlink()
                self.append_delivery()
                self.rewrite_single_record(mutate)
                with self.assertRaises(knowledge.MalformedKnowledge):
                    self.earned.read(knowledge.DELIVERY_RECORD_KIND)

    def test_earned_store_is_append_only_and_tamper_refuses(self):
        first = self.append_delivery()
        second = self.earned.append(
            knowledge.DELIVERY_RECORD_KIND,
            self.delivery_detail(verdict_outcome="awaiting-certification"),
            origin_kind="operator", origin="karol", head_sha=HEAD,
            timestamp=STAMP,
        )
        self.assertEqual(second["seq"], 1)
        self.assertEqual(second["prev_hash"], first["record_hash"])
        self.assertFalse(hasattr(self.earned, "update"))
        self.assertFalse(hasattr(self.earned, "rewrite"))
        path = self.earned_path()
        records = [json.loads(line) for line in path.read_text(
            encoding="utf-8").splitlines()]
        records[0]["detail"]["verdict_outcome"] = "rewritten"
        path.write_text("\n".join(json.dumps(record) for record in records) + "\n",
                        encoding="utf-8")
        with self.assertRaises(knowledge.MalformedKnowledge):
            self.earned.read(knowledge.DELIVERY_RECORD_KIND)


class RepositoryKnowledgeFitnessTest(unittest.TestCase):
    """The knowledge boundary stays below authority and above ambient I/O."""

    AUTHORITY_MODULES = (
        "contract.py",
        "gate.py",
        "orchestration_run.py",
        "program_run.py",
        "program_verdict.py",
    )
    FORBIDDEN_IMPORT_ROOTS = {
        "socket", "urllib", "http", "ssl", "ftplib", "smtplib", "imaplib",
        "poplib", "telnetlib", "xmlrpc", "subprocess", "requests", "aiohttp",
        "httpx", "random", "secrets", "uuid",
    }
    ALLOWED_ABSOLUTE_IMPORTS = {
        "__future__", "fcntl", "hashlib", "json", "os", "tempfile",
        "contextlib", "datetime", "pathlib",
    }
    ALLOWED_RELATIVE_IMPORTS = {"repofacts", "model"}

    @staticmethod
    def authority_knowledge_reads(source):
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names
                               if alias.name in {
                                   "dw_pmo.knowledge", "dw_pmo.knowledge_packet",
                                   "dw_pmo.knowledge_writeback",
                                   "dw_pmo.memory_recall",
                               }
                               or alias.name.startswith((
                                   "dw_pmo.knowledge.", "dw_pmo.memory_",
                               )))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if (
                    module in {
                        "knowledge", "knowledge_packet", "knowledge_writeback",
                    }
                    or module.startswith("memory_")
                    or ".memory_" in module
                    or module.endswith((
                        ".knowledge", ".knowledge_packet",
                        ".knowledge_writeback",
                    ))
                ):
                    imports.append(module)
                if module == "dw_pmo" and any(
                        alias.name in {
                            "knowledge", "knowledge_packet", "knowledge_writeback",
                        } or alias.name.startswith("memory_")
                        for alias in node.names):
                    imports.append("dw_pmo.knowledge")
        store_reads = [needle for needle in (
            "pmo-knowledge", "DerivedFactStore", "EarnedRecordStore",
            "build_memory_recall", "delivery-workbench-memory-recall",
            "delivery-workbench-memory-writeback",
            "delivery-workbench-decision-basis",
        ) if needle in source]
        return imports + store_reads

    def test_gate_contract_grant_and_verdict_paths_do_not_read_knowledge(self):
        offenders = {}
        for name in self.AUTHORITY_MODULES:
            path = LIB_DIR / name
            reads = self.authority_knowledge_reads(path.read_text(encoding="utf-8"))
            if reads:
                offenders[name] = reads
        self.assertEqual(
            offenders, {},
            "knowledge may inform but never enter gate, contract, grant, or "
            "verdict paths: %r" % offenders,
        )

    def test_authority_guard_rejects_planted_knowledge_and_memory_reads(self):
        planted_reads = (
            "from dw_pmo.knowledge import DerivedFactStore\n",
            "from dw_pmo.memory_recall import build_memory_recall\n",
            "from dw_pmo import memory_recall\n",
            'path = root / ".git" / "pmo-knowledge"\n',
            'kind = "delivery-workbench-memory-writeback"\n',
            'kind = "delivery-workbench-decision-basis"\n',
        )
        for planted in planted_reads:
            with self.subTest(planted=planted):
                self.assertTrue(self.authority_knowledge_reads(planted))

    def test_knowledge_imports_are_stdlib_offline_and_non_spawning(self):
        path = LIB_DIR / "knowledge.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        unexpected = []
        forbidden = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in self.FORBIDDEN_IMPORT_ROOTS:
                        forbidden.append(alias.name)
                    if root not in self.ALLOWED_ABSOLUTE_IMPORTS:
                        unexpected.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".", 1)[0]
                if root in self.FORBIDDEN_IMPORT_ROOTS:
                    forbidden.append(node.module)
                if node.level:
                    relatives = ({node.module} if node.module else
                                 {alias.name for alias in node.names})
                    for relative in relatives:
                        if relative not in self.ALLOWED_RELATIVE_IMPORTS:
                            unexpected.append("." * node.level + str(relative))
                elif root not in self.ALLOWED_ABSOLUTE_IMPORTS:
                    unexpected.append(str(node.module))
        self.assertEqual(forbidden, [], "knowledge imports ambient I/O: %r" % forbidden)
        self.assertEqual(
            unexpected, [],
            "knowledge imports a non-stdlib or undeclared first-party module: %r"
            % unexpected,
        )
        self.assertNotIn("subprocess", source)
        self.assertNotIn("os.system", source)
        self.assertNotIn("os.popen", source)
        self.assertNotIn("os.spawn", source)

    def test_symbol_map_extractor_is_stdlib_offline_and_non_spawning(self):
        path = LIB_DIR / "symbol_map.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        allowed = {"__future__", "ast", "pathlib", "typing"}
        unexpected = []
        forbidden = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""] if not node.level else ["relative"]
            else:
                continue
            for module in modules:
                root = module.split(".", 1)[0]
                if root in self.FORBIDDEN_IMPORT_ROOTS:
                    forbidden.append(module)
                if root not in allowed:
                    unexpected.append(module)
        self.assertEqual(forbidden, [])
        self.assertEqual(unexpected, [])
        for token in ("subprocess", "run_git", "socket", "datetime", "random"):
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_grounding_is_stdlib_offline_and_uses_the_repository_fact_boundary(self):
        path = LIB_DIR / "grounding.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        allowed_absolute = {"__future__", "re", "pathlib", "typing"}
        allowed_relative = {
            "repofacts", "knowledge", "model", "parse", "paths",
            "repository_map", "symbol_map",
        }
        unexpected = []
        forbidden = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
                relative = False
            elif isinstance(node, ast.ImportFrom):
                modules = (
                    [node.module]
                    if node.module
                    else [alias.name for alias in node.names]
                )
                relative = bool(node.level)
            else:
                continue
            for module in modules:
                root = module.split(".", 1)[0]
                if root in self.FORBIDDEN_IMPORT_ROOTS:
                    forbidden.append(module)
                allowed = allowed_relative if relative else allowed_absolute
                if root not in allowed:
                    unexpected.append(("." if relative else "") + module)
        self.assertEqual(forbidden, [])
        self.assertEqual(unexpected, [])
        self.assertIn("repofacts.blob_content", source)

    def test_knowledge_packet_is_stdlib_offline_and_authority_free(self):
        path = LIB_DIR / "knowledge_packet.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        allowed_absolute = {
            "__future__", "hashlib", "json", "re", "pathlib", "typing",
        }
        allowed_relative = {
            "repofacts", "grounding", "knowledge", "model",
            "repository_map", "symbol_map",
        }
        forbidden = []
        unexpected = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
                relative = False
            elif isinstance(node, ast.ImportFrom):
                modules = (
                    [node.module]
                    if node.module
                    else [alias.name for alias in node.names]
                )
                relative = bool(node.level)
            else:
                continue
            for module in modules:
                root = module.split(".", 1)[0]
                if root in self.FORBIDDEN_IMPORT_ROOTS:
                    forbidden.append(module)
                allowed = allowed_relative if relative else allowed_absolute
                if root not in allowed:
                    unexpected.append(("." if relative else "") + module)
        self.assertEqual(forbidden, [])
        self.assertEqual(unexpected, [])
        for authority in (
            "contract", "gate", "grant", "program_verdict", "verdict"
        ):
            self.assertNotIn("from .%s" % authority, source)

    def test_writeback_adapter_cannot_import_authority_or_verdict_paths(self):
        source = (LIB_DIR / "knowledge_writeback.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if any(token in module for token in (
                    "contract", "gate", "grant", "program_run", "program_verdict",
                )):
                    imported.append(module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if any(token in alias.name for token in (
                        "contract", "gate", "grant", "program_run", "program_verdict",
                    )):
                        imported.append(alias.name)
        self.assertEqual(imported, [])

    def test_derived_fact_computation_has_no_clock_or_random_input(self):
        sources = "\n".join((
            inspect.getsource(knowledge._derived_document),
            inspect.getsource(knowledge.DerivedFactStore.write),
            inspect.getsource(knowledge.DerivedFactStore.read_or_recompute),
        ))
        for token in (
            "datetime", "time.", "random", "secrets", "uuid", "urandom"
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, sources)

    def test_documented_contract_names_both_classes_and_authority_exclusion(self):
        text = (REPOSITORY_ROOT / "docs" / "repository-knowledge.md").read_text(
            encoding="utf-8"
        )
        for required in (
            "delivery-workbench-repository-knowledge@1",
            ".git/pmo-knowledge/derived/",
            ".git/pmo-knowledge/earned/",
            "Knowledge may inform; it may never authorize",
            "latency only",
            "No authoritative answer changes",
        ):
            with self.subTest(required=required):
                self.assertIn(required.lower(), text.lower())

    def test_hook_payload_keeps_knowledge_modules_byte_identical(self):
        for name in (
            "grounding.py", "knowledge.py", "knowledge_packet.py",
            "knowledge_writeback.py", "memory_recall.py", "repository_map.py",
            "symbol_map.py",
        ):
            with self.subTest(module=name):
                canonical = LIB_DIR / name
                vendored = REPOSITORY_ROOT / ".githooks" / "dw_pmo" / name
                self.assertTrue(
                    vendored.is_file(), "the hook payload must include %s" % name
                )
                self.assertEqual(vendored.read_bytes(), canonical.read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
