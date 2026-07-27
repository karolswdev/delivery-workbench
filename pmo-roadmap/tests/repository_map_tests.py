#!/usr/bin/env python3
"""WLA-29-02 symbol/structure map unit and integration tests."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = TESTS_DIR.parent.parent
LIB_ROOT = TESTS_DIR.parent / "lib"
sys.path.insert(0, str(LIB_ROOT))

from dw_pmo import repofacts
from dw_pmo.knowledge import DerivedFactStore, StaleDerivedFact
from dw_pmo.mcpserver import call_tool
from dw_pmo.repository_map import (
    SYMBOL_MAP_FACT_KIND,
    read_symbol_map,
    refresh_symbol_map,
)
from dw_pmo.symbol_map import GREP_FALLBACK, build_symbol_map


EVIDENCE = {}


def git(root, *args, input_bytes=None):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], input=input_bytes,
        stderr=subprocess.STDOUT,
    )


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


class SymbolMapUnitTest(unittest.TestCase):
    TREE = "1" * 40

    def build(self, sources, previous=None, parsed=None):
        blobs = {}
        tracked = []
        for number, (path, source) in enumerate(sorted(sources.items()), 1):
            blob = ("%040x" % number)[-40:]
            encoded = source if isinstance(source, bytes) else source.encode("utf-8")
            blobs[blob] = encoded
            tracked.append({"path": path, "blob": blob, "size": len(encoded)})
        return build_symbol_map(
            self.TREE, tracked, blobs.__getitem__, previous=previous,
            on_parse=(parsed.append if parsed is not None else None),
        )

    def test_nested_async_symbols_imports_spans_and_module_inventory(self):
        model = self.build({
            "pkg/mod.py": (
                "import os\nfrom .helpers import useful as helper\n\n"
                "class Outer:\n"
                "    class Inner:\n"
                "        async def work(self):\n"
                "            def nested():\n"
                "                return helper()\n"
                "            return nested()\n"
                "\nasync def top():\n    return Outer()\n"
            ),
        })
        module = model["modules"][0]
        self.assertEqual(module["imports"], [".helpers.useful", "os"])
        by_name = {item["qualified_name"]: item for item in model["symbols"]}
        self.assertEqual(by_name["pkg.mod"]["kind"], "module")
        self.assertEqual(by_name["pkg.mod.Outer"]["kind"], "class")
        self.assertEqual(by_name["pkg.mod.Outer.Inner.work"]["kind"], "method")
        self.assertEqual(
            by_name["pkg.mod.Outer.Inner.work.nested"]["kind"], "function"
        )
        self.assertEqual(by_name["pkg.mod.top"]["kind"], "function")
        self.assertGreaterEqual(
            by_name["pkg.mod.Outer.Inner.work"]["line_end"], 9
        )

    def test_test_resolution_keeps_terminal_name_collisions(self):
        model = self.build({
            "a.py": "def shared():\n    return 1\n",
            "b.py": "def shared():\n    return 2\n",
            "tests/test_both.py": (
                "from a import shared\n\n"
                "def test_shared():\n    assert shared() == 1\n"
            ),
        })
        test = next(item for item in model["tests"]
                    if item["file"] == "tests/test_both.py")
        self.assertEqual(test["symbols"], ["a.shared", "b.shared"])
        self.assertFalse(model["test_resolution"]["resolves_import_alias_targets"])

    def test_non_python_and_unparseable_python_are_named_gaps(self):
        model = self.build({
            "broken.py": "def nope(:\n",
            "script.sh": "printf '%s\\n' hello\n",
            "web/app.js": "export const answer = 42;\n",
        })
        self.assertEqual(
            [(item["file"], item["kind"]) for item in model["gaps"]],
            [
                ("broken.py", "unparseable-python"),
                ("script.sh", "non-python"),
                ("web/app.js", "non-python"),
            ],
        )
        self.assertTrue(all(item["reason"] == GREP_FALLBACK
                            for item in model["gaps"]))
        self.assertEqual(model["modules"][0]["parse_status"], "gap")

    def test_same_tree_extraction_is_byte_identical(self):
        sources = {
            "z.py": "from a import x\n\ndef zed():\n    return x\n",
            "a.py": "def x():\n    return 1\n",
            "README.md": "text\n",
        }
        first = self.build(sources)
        second = self.build(dict(reversed(list(sources.items()))))
        self.assertEqual(canonical(first), canonical(second))

    def test_previous_blob_reuse_parses_only_the_changed_file(self):
        sources = {
            "a.py": "def a():\n    return 1\n",
            "b.py": "def b():\n    return 2\n",
        }
        first = self.build(sources)
        changed_sources = dict(sources, **{"a.py": "def a():\n    return 3\n"})
        # Keep b's synthetic blob stable while assigning a a new id.
        blobs = {
            "a" * 40: changed_sources["a.py"].encode(),
            first["modules"][1]["blob"]: changed_sources["b.py"].encode(),
        }
        tracked = [
            {"path": "a.py", "blob": "a" * 40, "size": len(blobs["a" * 40])},
            {"path": "b.py", "blob": first["modules"][1]["blob"],
             "size": len(blobs[first["modules"][1]["blob"]])},
        ]
        parsed = []
        build_symbol_map(
            "2" * 40, tracked, blobs.__getitem__, previous=first,
            on_parse=parsed.append,
        )
        self.assertEqual(parsed, ["a.py"])


class RepositoryMapIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dw-repository-map-test."))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "tests@example.invalid")
        git(self.root, "config", "user.name", "Tests")
        self.write("pkg.py", "def target():\n    return 1\n")
        self.write(
            "tests/test_pkg.py",
            "from pkg import target\n\ndef test_target():\n    assert target() == 1\n",
        )
        self.write("broken.py", "def broken(:\n")
        self.write("README.md", "fixture\n")
        self.write("pm/roadmap/demo/README.md", "# Demo roadmap\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "fixture")
        repofacts.reset_cache()
        self.addCleanup(repofacts.reset_cache)

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_stale_read_refuses_and_one_file_refresh_parses_one_file(self):
        initial_parses = []
        first = refresh_symbol_map(self.root, on_parse=initial_parses.append)
        self.assertEqual(len(initial_parses), 3)
        first_tree = first["index_tree"]
        self.assertEqual(first["value"]["index_tree"], first_tree)

        self.write("pkg.py", "def target():\n    return 2\n")
        git(self.root, "add", "pkg.py")
        current_tree = git(self.root, "write-tree").decode().strip()
        self.assertNotEqual(first_tree, current_tree)
        with self.assertRaises(StaleDerivedFact):
            read_symbol_map(self.root)

        reparsed = []
        second = refresh_symbol_map(self.root, on_parse=reparsed.append)
        self.assertEqual(reparsed, ["pkg.py"])
        self.assertEqual(second["index_tree"], current_tree)
        self.assertEqual(read_symbol_map(self.root), second)
        EVIDENCE["incremental_reparsed"] = list(reparsed)
        EVIDENCE["stale_refusal"] = True

    def test_cli_and_mcp_return_byte_identical_read_only_model(self):
        cli = REPOSITORY_ROOT / ".githooks" / "dw"
        refresh_raw = subprocess.check_output([
            sys.executable, str(cli), "--root", str(self.root),
            "knowledge", "refresh", "--json",
        ])
        refresh_document = json.loads(refresh_raw)
        fact_path = DerivedFactStore(self.root)._path(SYMBOL_MAP_FACT_KIND)
        before = fact_path.read_bytes()

        cli_raw = subprocess.check_output([
            sys.executable, str(cli), "--root", str(self.root),
            "knowledge", "map", "--json",
        ]).rstrip(b"\n")
        mcp_result = call_tool(self.root, "dw_knowledge_map", {})
        text = mcp_result["content"][0]["text"]
        structured = mcp_result["structuredContent"]
        after = fact_path.read_bytes()

        self.assertNotIn("isError", mcp_result)
        self.assertEqual(cli_raw, text.encode("utf-8"))
        self.assertEqual(json.loads(cli_raw), structured)
        self.assertEqual(structured, refresh_document)
        self.assertEqual(before, after, "map surfaces must not rewrite the cache")
        EVIDENCE["cli_mcp_parity"] = True


class RealRepositoryMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        facts = repofacts.Derivation(REPOSITORY_ROOT)
        cls.tree = repofacts.index_tree(REPOSITORY_ROOT, facts)
        cls.tracked = repofacts.tracked_files(REPOSITORY_ROOT, cls.tree, facts)
        cls.parsed = []
        cls.model = build_symbol_map(
            cls.tree,
            cls.tracked,
            lambda blob: repofacts.blob_content(REPOSITORY_ROOT, blob, facts),
            on_parse=cls.parsed.append,
        )

    def test_full_repository_covers_every_tracked_python_and_names_all_other_gaps(self):
        python_paths = sorted(item["path"] for item in self.tracked
                              if item["path"].endswith(".py"))
        self.assertEqual(
            sorted(module["file"] for module in self.model["modules"]),
            python_paths,
        )
        named_gaps = {item["file"] for item in self.model["gaps"]}
        non_python = {item["path"] for item in self.tracked
                      if not item["path"].endswith(".py")}
        self.assertTrue(non_python.issubset(named_gaps))
        self.assertEqual(self.model["index_tree"], self.tree)
        EVIDENCE.update({
            "index_tree": self.tree,
            "tracked_files": len(self.tracked),
            "python_files": len(python_paths),
            "symbols": len(self.model["symbols"]),
            "gaps": len(self.model["gaps"]),
        })

    def test_real_extraction_is_byte_deterministic(self):
        facts = repofacts.Derivation(REPOSITORY_ROOT)
        second = build_symbol_map(
            self.tree,
            repofacts.tracked_files(REPOSITORY_ROOT, self.tree, facts),
            lambda blob: repofacts.blob_content(REPOSITORY_ROOT, blob, facts),
        )
        self.assertEqual(canonical(self.model), canonical(second))
        EVIDENCE["deterministic_bytes"] = len(canonical(self.model))

    def test_real_core_tests_reference_sampled_dw_pmo_symbols(self):
        test_links = {
            item["file"]: set(item["symbols"]) for item in self.model["tests"]
        }
        samples = {
            "DerivedFactStore": "pmo-roadmap/tests/repository_knowledge_tests.py",
            "build_status": "pmo-roadmap/tests/dw-core-tests.py",
            "run_gate": "pmo-roadmap/tests/dw-core-tests.py",
            "run_verify": "pmo-roadmap/tests/dw-core-tests.py",
            "story_detail": "pmo-roadmap/tests/dw-core-tests.py",
        }
        symbols_by_name = {}
        for symbol in self.model["symbols"]:
            symbols_by_name.setdefault(symbol["name"], set()).add(
                symbol["qualified_name"]
            )
        for name, test_file in samples.items():
            with self.subTest(symbol=name):
                expected = symbols_by_name[name]
                self.assertTrue(expected & test_links[test_file])
        EVIDENCE["sampled_symbol_test_links"] = len(samples)


if __name__ == "__main__":
    program = unittest.main(verbosity=2, exit=False)
    if program.result.wasSuccessful():
        print("WLA-29-02 EVIDENCE " + json.dumps(EVIDENCE, sort_keys=True))
    raise SystemExit(0 if program.result.wasSuccessful() else 1)
