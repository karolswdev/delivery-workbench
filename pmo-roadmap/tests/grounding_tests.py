#!/usr/bin/env python3
"""WLA-29-03 story-grounding unit and integration tests."""

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
from dw_pmo.grounding import (
    MAX_SUGGESTIONS,
    ground_hints,
    ground_project_story,
    parse_localization_hints,
)
from dw_pmo.knowledge import DerivedFactStore, StaleDerivedFact
from dw_pmo.mcpserver import call_tool
from dw_pmo.parse import get_project, parse_story_rows
from dw_pmo.repository_map import SYMBOL_MAP_FACT_KIND, refresh_symbol_map


EVIDENCE = {}


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], stderr=subprocess.STDOUT
    )


class GroundingUnitTest(unittest.TestCase):
    def test_parser_requires_nested_lists_and_preserves_explicit_new_marker(self):
        parsed = parse_localization_hints("""# Story

## Localization hints

- **Affected files:**
  - `pkg.py`
  - `planned.py` (new)
- **Target symbols:**
  - `pkg.exact_target`
  - `planned_symbol` (new)

## Acceptance criteria

- [ ] Behavior works.
""")
        self.assertTrue(parsed["present"])
        self.assertEqual(parsed["diagnostics"], [])
        self.assertEqual(
            [(item["value"], item["declared_new"])
             for item in parsed["affected_files"]],
            [("pkg.py", False), ("planned.py", True)],
        )
        self.assertEqual(
            [(item["value"], item["declared_new"])
             for item in parsed["target_symbols"]],
            [("pkg.exact_target", False), ("planned_symbol", True)],
        )

    def test_commented_template_example_is_not_parsed_as_real_hints(self):
        template = (REPOSITORY_ROOT / "pmo-roadmap" / "templates"
                    / "story.md.tmpl").read_text(encoding="utf-8")
        parsed = parse_localization_hints(template)
        self.assertTrue(parsed["present"])
        self.assertEqual(parsed["affected_files"], [])
        self.assertEqual(parsed["target_symbols"], [])
        self.assertEqual(parsed["diagnostics"], [])

    def test_suggestions_are_bounded_by_name_distance(self):
        symbols = []
        for index, name in enumerate((
                "target_name", "target_names", "target_named",
                "target_namex", "target_namer", "unrelated"), 1):
            symbols.append({
                "kind": "function",
                "name": name,
                "qualified_name": "pkg.%s" % name,
                "file": "pkg.py",
                "line_start": index,
                "line_end": index,
            })
        model = {
            "kind": "delivery-workbench-symbol-structure-map",
            "schema_version": 1,
            "index_tree": "1" * 40,
            "tracked_files": [],
            "symbols": symbols,
            "gaps": [],
        }
        parsed = {
            "affected_files": [],
            "target_symbols": [{
                "value": "target_nam",
                "declared_new": False,
                "line": 1,
            }],
        }
        item = ground_hints(model, parsed, lambda _blob: b"")["target_symbols"][0]
        self.assertEqual(item["classification"], "unknown")
        self.assertLessEqual(len(item["suggestions"]), MAX_SUGGESTIONS)
        self.assertEqual(item["suggestions"][0]["qualified_name"], "pkg.target_name")


class GroundingIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dw-grounding-test."))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "tests@example.invalid")
        git(self.root, "config", "user.name", "Tests")
        self.write(
            "pkg.py",
            "def exact_target():\n    return 1\n\n"
            "def exact_taster():\n    return 2\n",
        )
        self.write(
            "web/app.js",
            "export function gap_target() { return 1; }\n",
        )
        self.write("pm/roadmap/demo/README.md", """# Demo - Roadmap

**Current phase:** [Phase 1](./phase-1-ground/current-phase-status.md).

## Project metadata

- **Slug:** `demo`
- **Story ID prefix:** DM
""")
        self.write("pm/roadmap/demo/phase-1-ground/current-phase-status.md", """# Phase 1

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DM-1-01 | Ground fixture | in-progress | [story-01-ground](./story-01-ground.md) | - |
""")
        self.write(
            "pm/roadmap/demo/phase-1-ground/story-01-ground.md",
            self.story_text(),
        )
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "fixture")
        repofacts.reset_cache()
        self.addCleanup(repofacts.reset_cache)
        refresh_symbol_map(self.root)

    @staticmethod
    def story_text(extra_symbol=""):
        extra = "  - `%s` (new)\n" % extra_symbol if extra_symbol else ""
        return """# DM-1-01 - Ground fixture

- **Project:** demo
- **Phase:** 1
- **Status:** in-progress

## Problem

Fixture.

## Localization hints

- **Affected files:**
  - `pkg.py`
  - `planned.py` (new)
- **Target symbols:**
  - `exact_target`
  - `planned_symbol` (new)
  - `exact_targte`
%s
## Acceptance criteria

- [ ] The `exact_target` behavior is observable.

## Test plan

- **Unit:** fixture
""" % extra

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def ground(self):
        return ground_project_story(
            self.root, get_project(self.root, "demo"), "DM-1-01"
        )

    def test_fixture_story_classifies_verified_new_and_misspelled_with_evidence(self):
        result = self.ground()
        by_hint = {
            item["hint"]: item
            for item in result["affected_files"] + result["target_symbols"]
        }
        self.assertEqual(by_hint["pkg.py"]["classification"], "verified")
        self.assertEqual(by_hint["exact_target"]["classification"], "verified")
        self.assertEqual(by_hint["planned.py"]["classification"], "new")
        self.assertEqual(by_hint["planned_symbol"]["classification"], "new")
        self.assertEqual(by_hint["exact_targte"]["classification"], "unknown")
        self.assertTrue(by_hint["exact_targte"]["evidence"]["no_match"])
        self.assertTrue(by_hint["exact_targte"]["evidence"]["no_match_complete"])
        self.assertIn(
            "exact_target",
            [item["name"] for item in by_hint["exact_targte"]["suggestions"]],
        )
        for name in ("pkg.py", "exact_target"):
            location = by_hint[name]["locations"][0]
            self.assertTrue(location["file"])
            self.assertGreaterEqual(location["line_start"], 1)
            self.assertGreaterEqual(location["line_end"], location["line_start"])
        self.assertEqual(
            by_hint["planned_symbol"]["evidence"]["symbol_map_exact_matches"],
            0,
        )
        self.assertTrue(
            by_hint["planned_symbol"]["evidence"]["no_match_complete"]
        )
        EVIDENCE.update({
            "verified": result["summary"]["verified"],
            "new": result["summary"]["new"],
            "unknown": result["summary"]["unknown"],
            "misspelling_suggestions": len(
                by_hint["exact_targte"]["suggestions"]
            ),
            "complete_no_match": True,
        })

    def test_gap_text_match_prevents_explicit_new_classification(self):
        story = self.root / "pm/roadmap/demo/phase-1-ground/story-01-ground.md"
        story.write_text(self.story_text("gap_target"), encoding="utf-8")
        git(self.root, "add", str(story.relative_to(self.root)))
        refresh_symbol_map(self.root)
        result = self.ground()
        item = next(item for item in result["target_symbols"]
                    if item["hint"] == "gap_target")
        self.assertEqual(item["classification"], "unknown")
        self.assertTrue(item["declared_new"])
        self.assertEqual(
            item["evidence"]["grep_fallback"]["matches"][0]["file"],
            "web/app.js",
        )
        self.assertFalse(item["evidence"]["no_match"])

    def test_stale_map_refuses_instead_of_answering(self):
        self.write("pkg.py", "def changed_target():\n    return 2\n")
        git(self.root, "add", "pkg.py")
        with self.assertRaises(StaleDerivedFact):
            self.ground()

        cli = REPOSITORY_ROOT / "pmo-roadmap" / "bin" / "dw"
        run = subprocess.run([
            sys.executable, str(cli), "--root", str(self.root),
            "check", "demo",
        ], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("WARNING pm/roadmap/demo/phase-1-ground/story-01-ground.md: grounding unavailable:", run.stdout)
        self.assertIn("is stale", run.stdout)
        self.assertNotIn("localization target-symbol hint", run.stdout)

    def test_cli_and_mcp_are_byte_identical_and_read_only(self):
        cli = REPOSITORY_ROOT / "pmo-roadmap" / "bin" / "dw"
        fact_path = DerivedFactStore(self.root)._path(SYMBOL_MAP_FACT_KIND)
        before = fact_path.read_bytes()
        cli_raw = subprocess.check_output([
            sys.executable, str(cli), "--root", str(self.root),
            "knowledge", "ground", "demo", "DM-1-01", "--json",
        ]).rstrip(b"\n")
        mcp = call_tool(self.root, "dw_knowledge_ground", {
            "project": "demo", "story": "DM-1-01",
        })
        after = fact_path.read_bytes()
        self.assertNotIn("isError", mcp)
        self.assertEqual(cli_raw, mcp["content"][0]["text"].encode("utf-8"))
        self.assertEqual(json.loads(cli_raw), mcp["structuredContent"])
        self.assertEqual(before, after)

    def test_check_warnings_are_greppable_and_do_not_change_exit_code(self):
        cli = REPOSITORY_ROOT / "pmo-roadmap" / "bin" / "dw"
        run = subprocess.run([
            sys.executable, str(cli), "--root", str(self.root),
            "check", "demo",
        ], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("WARNING pm/roadmap/demo/phase-1-ground/story-01-ground.md:", run.stdout)
        self.assertIn("`exact_targte` is unknown", run.stdout)
        self.assertIn("acceptance criteria name exact code identifier `exact_target`", run.stdout)
        self.assertTrue(run.stdout.rstrip().endswith("dw check: ok"))

        mcp = call_tool(self.root, "dw_check", {"project": "demo"})
        self.assertTrue(mcp["structuredContent"]["ok"])
        self.assertEqual(mcp["structuredContent"]["issues"], [])
        self.assertTrue(mcp["structuredContent"]["warnings"])
        self.assertIn("WARNING ", mcp["content"][0]["text"])

    def test_story_table_parser_is_unchanged_by_optional_story_section(self):
        status = self.root / "pm/roadmap/demo/phase-1-ground/current-phase-status.md"
        before = parse_story_rows(status)
        story = self.root / "pm/roadmap/demo/phase-1-ground/story-01-ground.md"
        story.write_text(story.read_text(encoding="utf-8").replace(
            "## Localization hints", "## Localization hints\n\n<!-- advisory -->"
        ), encoding="utf-8")
        after = parse_story_rows(status)
        self.assertEqual(before, after)
        self.assertEqual(after[0].story_id, "DM-1-01")


if __name__ == "__main__":
    program = unittest.main(verbosity=2, exit=False)
    if program.result.wasSuccessful():
        print("WLA-29-03 EVIDENCE " + json.dumps(EVIDENCE, sort_keys=True))
    raise SystemExit(0 if program.result.wasSuccessful() else 1)
