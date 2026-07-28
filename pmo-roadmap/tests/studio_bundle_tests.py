#!/usr/bin/env python3
"""WLA-30-08 generated-bundle Program Studio review tests."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PMO_ROOT = TESTS_DIR.parent
FIXTURES = TESTS_DIR / "fixtures" / "program-scaffold"
sys.path.insert(0, str(PMO_ROOT / "lib"))

from dw_pmo.orchestration_driver import write_driver_config
from dw_pmo.program_scaffold import (
    load_scaffold_answers,
    scaffold_program,
    simulate_scaffold_proposal,
)
from dw_pmo.workbench import handle_api


def tree_snapshot(root: Path):
    result = {}
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root))
        info = path.lstat()
        if path.is_symlink():
            value = os.readlink(path).encode("utf-8")
            kind = "link"
        elif path.is_file():
            value = path.read_bytes()
            kind = "file"
        else:
            value = b""
            kind = "dir"
        result[relative] = (kind, info.st_mode, hashlib.sha256(value).hexdigest())
    return result


class StudioBundleTest(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="dw-studio-bundle.")).resolve()
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        self.root = self.temp / "repo"
        self.root.mkdir()
        subprocess.run(
            ["git", "-C", str(self.root), "init", "-q", "-b", "main"],
            check=True,
        )
        self._write_roadmap()
        self.roster = self._roster()
        write_driver_config(self.root, self.roster)
        self.answers = load_scaffold_answers(
            (FIXTURES / "greenfield-build.json").read_text(encoding="utf-8")
        )

    def _write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def _write_roadmap(self):
        self._write("pm/roadmap/demo/README.md", """# Demo - Roadmap

**Last updated:** 2026-07-27.
**Current phase:** [Phase 1](./phase-1-demo/current-phase-status.md).
**Status:** active.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 1 | Demo | in-progress | [phase-1-demo](./phase-1-demo/) |

## Project metadata

- **Slug:** `demo`
- **Story ID prefix:** DM
""")
        self._write("pm/roadmap/demo/phase-1-demo/current-phase-status.md", """# Phase 1 - Demo

**Last updated:** 2026-07-27.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DM-1-01 | Build first feature | ready | [story-01-build](./story-01-build.md) | - |
""")
        self._write(
            "pm/roadmap/demo/phase-1-demo/story-01-build.md",
            "# DM-1-01 - Build first feature\n\n- **Project:** demo\n- **Phase:** 1\n- **Status:** ready\n- **Depends on:** none\n",
        )

    @staticmethod
    def _roster():
        return {
            "kind": "delivery-workbench-driver-config",
            "schema_version": 1,
            "workspace_root": None,
            "profiles": {
                "claude-builder": {
                    "adapter": "fixture",
                    "adapter_version": "fixture-v1",
                    "provider_family": "anthropic",
                    "capabilities": ["repository-read", "repository-write"],
                    "workspace_modes": ["isolated-worktree"],
                    "principal": "builder-principal",
                    "provider": "anthropic",
                    "model": "builder-model",
                    "model_binding": "requested-alias",
                },
                "codex-reviewer": {
                    "adapter": "fixture",
                    "adapter_version": "fixture-v1",
                    "provider_family": "openai",
                    "capabilities": ["repository-read"],
                    "workspace_modes": ["read-only"],
                    "principal": "reviewer-principal",
                    "provider": "openai",
                    "model": "reviewer-model",
                    "model_binding": "requested-alias",
                },
            },
        }

    def _proposal(self):
        return scaffold_program(
            self.root, self.answers, driver_config=self.roster,
        )

    def _save(self, proposal, name="proposal.json"):
        return self._write(name, json.dumps(proposal, sort_keys=True) + "\n")

    def _review(self, proposal=None, query=None):
        if query is None:
            path = self._save(proposal if proposal is not None else self._proposal())
            query = {"proposal_file": [str(path.relative_to(self.root))]}
        status, response = handle_api(self.root, "/api/setup/bundle", query)
        self.assertEqual(status, 200)
        self.assertTrue(response["ok"])
        return response["data"]

    def test_ready_bundle_is_one_product_language_model(self):
        model = self._review(self._proposal())
        self.assertTrue(model["valid"], model["diagnostics"])
        self.assertEqual(model["kind"], "delivery-workbench-program-studio-bundle-review")
        self.assertEqual(model["roadmap_scope"]["story_ids"], ["DM-1-01"])
        self.assertEqual([seat["duty"] for seat in model["team"]["seats"]], ["implementer", "verifier"])
        self.assertEqual(model["team"]["seats"][1]["independent_from"], ["implementer"])
        self.assertEqual(model["team"]["independence_rules"][0]["kind"], "provider-family")
        self.assertTrue(all(seat["local"]["available"] for seat in model["team"]["seats"]))
        mechanical = [
            criterion
            for rubric in model["rubrics"]
            for criterion in rubric["criteria"]
            if criterion["producing_check"] is not None
        ]
        self.assertTrue(mechanical)
        self.assertTrue(all(item["producer_exists"] for item in mechanical))
        self.assertIn("max_check_starts", model["budgets"])
        self.assertIn("budget-exhausted", model["stop_conditions"])
        self.assertEqual(model["configuration"]["label"], "configuration, not permission")
        self.assertTrue(model["configuration"]["tracked"]["non_authorizing"])
        self.assertTrue(model["configuration"]["git_local"]["non_authorizing"])
        self.assertEqual(
            model["handoff"]["command"],
            ".githooks/dw program plan demo-generated-program",
        )
        self.assertFalse(model["handoff"]["browser_executes"])
        self.assertFalse(model["starts_work"])
        self.assertFalse(model["creates_grant"])

    def test_invalid_missing_driver_budget_and_diversity_states_anchor_diagnostics(self):
        cases = []

        planted = self._proposal()
        criterion = planted["tracked_content"]["policy"]["rubrics"][0]["document"]["criteria"][0]
        criterion["evaluation"]["fact"] = "check-that-does-not-exist"
        cases.append(("planted-fact-mismatch", planted, self.roster, "bundle-checks"))

        missing_driver = self._proposal()
        missing_roster = copy.deepcopy(self.roster)
        del missing_roster["profiles"]["codex-reviewer"]
        cases.append(("missing-driver", missing_driver, missing_roster, "bundle-drivers"))

        insufficient = self._proposal()
        insufficient["tracked_content"]["policy"]["program"]["document"]["budgets"]["max_check_starts"] = 1
        cases.append(("insufficient-budget", insufficient, self.roster, "bundle-budgets"))

        same_family = self._proposal()
        same_roster = copy.deepcopy(self.roster)
        same_roster["profiles"]["codex-reviewer"]["provider_family"] = "anthropic"
        same_roster["profiles"]["codex-reviewer"]["provider"] = "anthropic"
        cases.append(("same-family-refused", same_family, same_roster, "bundle-drivers"))

        for name, proposal, roster, anchor in cases:
            with self.subTest(state=name):
                write_driver_config(self.root, roster)
                model = self._review(proposal)
                self.assertFalse(model["valid"], model)
                self.assertTrue(model["diagnostics"])
                self.assertIn(anchor, {item["anchor_id"] for item in model["diagnostics"]})
                for diagnostic in model["diagnostics"]:
                    self.assertTrue(diagnostic["source"])
                    self.assertTrue(diagnostic["pointer"].startswith("/"))
                    self.assertEqual(
                        diagnostic["anchor_href"],
                        "#/program-studio/bundle/%s" % diagnostic["anchor_id"],
                    )
                    self.assertIn(diagnostic["anchor_id"], model["sections"].values())

    def test_embedded_simulation_has_exact_core_parity(self):
        proposal = self._proposal()
        model = self._review(proposal)
        core = simulate_scaffold_proposal(proposal)
        shared = (
            "kind", "schema_version", "bounded", "green_route", "repair_route",
            "failure_routes", "starts_work", "writes_state",
        )
        self.assertEqual(
            {field: model["simulation"][field] for field in shared},
            {field: core[field] for field in shared},
        )

    def test_open_and_refresh_are_pure(self):
        path = self._save(self._proposal())
        query = {"proposal_file": [str(path.relative_to(self.root))]}
        before = tree_snapshot(self.root)
        first = self._review(query=query)
        middle = tree_snapshot(self.root)
        second = self._review(query=query)
        self.assertEqual(first, second)
        self.assertEqual(before, middle)
        self.assertEqual(before, tree_snapshot(self.root))
        self.assertFalse((self.root / ".git" / "pmo-programs").exists())

    def test_route_emits_or_accepts_no_setup_or_program_token(self):
        path = self._save(self._proposal())
        relative = str(path.relative_to(self.root))
        ready = self._review(query={"proposal_file": [relative]})

        def keys(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    yield key
                    yield from keys(item)
            elif isinstance(value, list):
                for item in value:
                    yield from keys(item)

        self.assertNotIn("expect", set(keys(ready)))
        self.assertNotIn("token", set(keys(ready)))
        encoded = json.dumps(ready, sort_keys=True)
        self.assertNotIn("setup-sha256:", encoded)
        self.assertNotIn('"sha256:', encoded)

        before = tree_snapshot(self.root)
        setup_cross_use = self._review(query={
            "proposal_file": [relative],
            "expect": ["setup-sha256:" + "1" * 64],
        })
        program_cross_use = self._review(query={
            "proposal_file": [relative],
            "expect": ["sha256:" + "2" * 64],
        })
        self.assertFalse(setup_cross_use["valid"])
        self.assertFalse(program_cross_use["valid"])
        self.assertEqual(setup_cross_use["refusal"], program_cross_use["refusal"])
        self.assertNotIn("1" * 64, json.dumps(setup_cross_use))
        self.assertNotIn("2" * 64, json.dumps(program_cross_use))
        self.assertEqual(before, tree_snapshot(self.root))

    def test_bundle_route_stays_in_studio_and_navigation_inventory_is_unchanged(self):
        index = (PMO_ROOT / "workbench" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(index.count('class="navlink"'), 7)
        self.assertNotIn("generated bundle", index.lower())
        app_source = (PMO_ROOT / "workbench" / "app.js").read_text(encoding="utf-8")
        self.assertIn('parts[1] === "bundle"', app_source)
        self.assertIn("viewStudioBundle", app_source)
        self.assertIn("Review the generated program as one linked bundle", app_source)
        self.assertNotIn("postJson(\"/api/setup/bundle", app_source)
        css = (PMO_ROOT / "workbench" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".bundle-config-cards .tracked", css)
        self.assertIn(".bundle-config-cards .git-local", css)
        self.assertIn("@media (max-width: 600px)", css)
        self.assertIn("@media (prefers-color-scheme: light)", css)


if __name__ == "__main__":
    unittest.main()
