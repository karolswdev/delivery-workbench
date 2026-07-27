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
            "story_id": "WLA-29-01",
            "outcome": "delivered",
            "summary": "Contracted the repository knowledge boundary.",
            "evidence_ref": "evidence-story-01.md",
        }
        detail.update(updates)
        return detail

    @staticmethod
    def lesson_detail(**updates):
        detail = {
            "subject": "freshness",
            "lesson": "Bind every derived answer to the current index tree.",
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

    def earned_path(self, kind=knowledge.DELIVERY_RECORD_KIND):
        return (self.git_dir / "pmo-knowledge" / "earned"
                / (kind + ".jsonl"))

    def rewrite_single_record(self, mutate):
        path = self.earned_path()
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
        lesson = self.earned.append(
            knowledge.LESSON_KIND,
            self.lesson_detail(supersedes=delivery["record_hash"]),
            origin_kind="operator",
            origin="karol",
            head_sha=HEAD,
            timestamp=STAMP,
        )
        self.assertEqual(
            self.earned.read(knowledge.DELIVERY_RECORD_KIND), [delivery]
        )
        self.assertEqual(self.earned.read(knowledge.LESSON_KIND), [lesson])
        for record in (delivery, lesson):
            self.assertIs(record["starts_work"], False)
            self.assertIs(record["authorizes"], False)
            self.assertIs(record["satisfies_gate"], False)
            self.assertIs(record["substitutes_for_evidence"], False)

    def test_read_revalidates_closed_fields_caps_and_provenance(self):
        mutations = (
            lambda record: record["detail"].update({"prompt": "smuggled"}),
            lambda record: record["detail"].update({"summary": "x" * 501}),
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
            self.delivery_detail(summary="A second delivery record."),
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
        records[0]["detail"]["summary"] = "rewritten"
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
                                   "dw_pmo.knowledge", "dw_pmo.knowledge_packet"
                               }
                               or alias.name.startswith("dw_pmo.knowledge."))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module in {"knowledge", "knowledge_packet"} or module.endswith(
                        (".knowledge", ".knowledge_packet")):
                    imports.append(module)
                if module == "dw_pmo" and any(
                        alias.name in {"knowledge", "knowledge_packet"}
                        for alias in node.names):
                    imports.append("dw_pmo.knowledge")
        store_reads = [needle for needle in (
            "pmo-knowledge", "DerivedFactStore", "EarnedRecordStore"
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

    def test_authority_guard_rejects_a_planted_knowledge_read(self):
        planted = "from dw_pmo.knowledge import DerivedFactStore\n"
        self.assertTrue(self.authority_knowledge_reads(planted))
        planted = 'path = root / ".git" / "pmo-knowledge"\n'
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
            "repository_map.py", "symbol_map.py",
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
