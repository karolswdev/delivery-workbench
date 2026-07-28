#!/usr/bin/env python3
"""WLA-30-04 guarded, atomic setup lease tests."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
LIB_ROOT = TESTS_DIR.parent / "lib"
CLI = TESTS_DIR.parent / "bin" / "dw"
sys.path.insert(0, str(LIB_ROOT))
sys.path.insert(0, str(TESTS_DIR))

from dw_pmo import DwError
from dw_pmo.mcpserver import call_tool
from dw_pmo.setup_lease import apply_setup, canonical_setup_preview, preview_setup
from dw_pmo.workbench import handle_mutation
from setup_proposal_tests import policy_document, proposal_fixture, provenance


def run(*args, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def file_snapshot(root: Path) -> dict[str, str]:
    ignored = {"pmo-setup-leases"}
    result = {}
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: str(item)):
        if ".git" in path.parts:
            git_index = path.parts.index(".git")
            if git_index + 1 < len(path.parts) and path.parts[git_index + 1] in ignored:
                continue
        result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


class SetupLeaseTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "pm" / "roadmap").mkdir(parents=True)
        (self.root / ".githooks").mkdir()
        (self.root / ".githooks" / "dw").write_text("#!/bin/sh\n", encoding="utf-8")
        run("git", "init", "-q", cwd=self.root)
        run("git", "config", "user.email", "setup-tests@example.invalid", cwd=self.root)
        run("git", "config", "user.name", "Setup Tests", cwd=self.root)
        (self.root / "seed.txt").write_text("seed\n", encoding="utf-8")
        run("git", "add", ".", cwd=self.root)
        run("git", "commit", "-qm", "seed", cwd=self.root)
        self.proposal = proposal_fixture()
        self.proposal["state"] = "reviewed"
        self.proposal["project"].update({"slug": "lease-demo", "prefix": "LD", "title": "Lease demo"})
        self.proposal["tracked_content"]["roadmap"]["phases"][0]["stories"][0]["dependencies"] = []
        self.proposal_path = self.root / "proposal.json"
        self.write_proposal()

    def tearDown(self):
        self._tmp.cleanup()

    def write_proposal(self):
        self.proposal_path.write_text(json.dumps(self.proposal, sort_keys=True), encoding="utf-8")

    def add_policy(self):
        def wrapper(kind, slug):
            item = policy_document(kind)
            item["document"]["slug"] = slug
            return item
        self.proposal["tracked_content"]["policy"] = {
            "program": wrapper("delivery-workbench-program", "lease-program"),
            "workflows": [wrapper("delivery-workbench-workflow", "lease-workflow")],
            "organization": wrapper("delivery-workbench-organization", "lease-organization"),
            "rubrics": [wrapper("delivery-workbench-rubric", "lease-rubric")],
            "provenance": provenance("recommendation", "Generated complete policy bundle."),
        }
        self.write_proposal()

    def test_happy_path_lands_roadmap_policy_and_roster_atomically(self):
        self.add_policy()
        before_head = run("git", "rev-parse", "HEAD", cwd=self.root).stdout.strip()
        preview = preview_setup(self.root, self.proposal_path)
        self.assertEqual(preview["kind"], "delivery-workbench-setup-preview")
        self.assertTrue(all(change["before_hash"] is None for change in preview["changes"]))
        applied = run(
            str(CLI), "--root", str(self.root), "setup", "apply",
            "--proposal", preview["proposal_id"], "--expect", preview["expect"],
            cwd=self.root,
        )
        result = json.loads(applied.stdout)
        self.assertEqual(result["journey_state"], "configured")
        self.assertTrue((self.root / "pm/roadmap/lease-demo/README.md").is_file())
        self.assertTrue((self.root / "pm/programs/lease-program.json").is_file())
        self.assertTrue((self.root / "pm/workflows/lease-workflow.json").is_file())
        self.assertTrue((self.root / "pm/organizations/lease-organization.json").is_file())
        self.assertTrue((self.root / "pm/rubrics/lease-rubric.json").is_file())
        roster = json.loads((self.root / ".git/pmo-orchestration/drivers.json").read_text(encoding="utf-8"))
        self.assertIn("implementer", roster["profiles"])
        self.assertEqual(run("git", "rev-parse", "HEAD", cwd=self.root).stdout.strip(), before_head)
        self.assertFalse((self.root / ".tmp/CONTRACT.md").exists())
        self.assertFalse((self.root / ".git/pmo-orchestration/runs").exists())
        self.assertFalse((self.root / ".git/pmo-orchestration/grants").exists())
        for field in ("starts_work", "creates_grant", "certifies", "commits"):
            self.assertIs(result[field], False)

    def _assert_drift_refuses_without_writing(self, mutator):
        preview = preview_setup(self.root, self.proposal_path)
        mutator()
        before_apply = file_snapshot(self.root)
        with self.assertRaisesRegex(DwError, "stale setup lease"):
            apply_setup(self.root, preview["proposal_id"], preview["expect"])
        self.assertEqual(file_snapshot(self.root), before_apply)
        self.assertFalse((self.root / "pm/roadmap/lease-demo").exists())

    def test_maintain_mode_updates_index_and_merges_roster(self):
        first = preview_setup(self.root, self.proposal_path)
        apply_setup(self.root, first["proposal_id"], first["expect"])
        maintained = copy.deepcopy(self.proposal)
        maintained["source_intent"]["mode"] = "maintain"
        phase = maintained["tracked_content"]["roadmap"]["phases"][0]
        phase["number"] = 2
        phase["title"] = "Second slice"
        phase["stories"][0]["id_sketch"] = "LD-2-01"
        maintained["local_content"]["driver_bindings"] = {
            "reviewer": {
                "adapter": "fixture", "model": "review-model", "provider": "fixture",
                "provenance": provenance("recommendation", "Add a review profile."),
            }
        }
        path = self.root / "maintain.json"
        path.write_text(json.dumps(maintained, sort_keys=True), encoding="utf-8")
        preview = preview_setup(self.root, path)
        self.assertIn("update", {item["action"] for item in preview["changes"]})
        apply_setup(self.root, preview["proposal_id"], preview["expect"])
        readme = (self.root / "pm/roadmap/lease-demo/README.md").read_text(encoding="utf-8")
        self.assertIn("| 1 |", readme)
        self.assertIn("| 2 |", readme)
        roster = json.loads((self.root / ".git/pmo-orchestration/drivers.json").read_text(encoding="utf-8"))
        self.assertEqual(set(roster["profiles"]), {"implementer", "reviewer"})

    def test_apply_preserves_existing_full_profiles_and_refuses_divergence(self):
        # An operator's full local profile is configuration the proposal
        # may reference but never rewrite (found by the WLA-30-10
        # rehearsal: the first cut replaced full profiles with
        # capability-less stubs, breaking role matching).
        roster_path = self.root / ".git/pmo-orchestration/drivers.json"
        first = preview_setup(self.root, self.proposal_path)
        apply_setup(self.root, first["proposal_id"], first["expect"])
        roster = json.loads(roster_path.read_text(encoding="utf-8"))
        full = dict(next(iter(roster["profiles"].values())))
        full.update({
            "adapter": "fixture", "model": "review-model",
            "provider": "fixture", "capabilities": ["repository-read"],
        })
        roster["profiles"]["seatful"] = full
        roster_path.write_text(json.dumps(roster, sort_keys=True), encoding="utf-8")

        referencing = copy.deepcopy(self.proposal)
        referencing["source_intent"]["mode"] = "maintain"
        referencing["tracked_content"]["roadmap"]["phases"][0]["number"] = 3
        referencing["tracked_content"]["roadmap"]["phases"][0]["stories"][0]["id_sketch"] = "LD-3-01"
        referencing["local_content"]["driver_bindings"] = {
            "seatful": {
                "adapter": "fixture", "model": "review-model", "provider": "fixture",
                "provenance": provenance("repository-fact", "Existing local profile."),
            }
        }
        path = self.root / "referencing.json"
        path.write_text(json.dumps(referencing, sort_keys=True), encoding="utf-8")
        preview = preview_setup(self.root, path)
        apply_setup(self.root, preview["proposal_id"], preview["expect"])
        after = json.loads(roster_path.read_text(encoding="utf-8"))
        self.assertEqual(after["profiles"]["seatful"]["capabilities"], ["repository-read"])

        divergent = copy.deepcopy(referencing)
        divergent["tracked_content"]["roadmap"]["phases"][0]["number"] = 4
        divergent["tracked_content"]["roadmap"]["phases"][0]["stories"][0]["id_sketch"] = "LD-4-01"
        divergent["local_content"]["driver_bindings"]["seatful"]["model"] = "other-model"
        path.write_text(json.dumps(divergent, sort_keys=True), encoding="utf-8")
        with self.assertRaises(Exception) as refusal:
            preview_setup(self.root, path)
        self.assertIn("disagrees with the proposal binding", str(refusal.exception))

    def test_changed_head_refuses(self):
        def mutate():
            (self.root / "head-drift.txt").write_text("head\n", encoding="utf-8")
            run("git", "add", "head-drift.txt", cwd=self.root)
            run("git", "commit", "-qm", "head drift", cwd=self.root)
        self._assert_drift_refuses_without_writing(mutate)

    def test_changed_index_refuses(self):
        def mutate():
            (self.root / "index-drift.txt").write_text("index\n", encoding="utf-8")
            run("git", "add", "index-drift.txt", cwd=self.root)
        self._assert_drift_refuses_without_writing(mutate)

    def test_changed_roadmap_refuses(self):
        def mutate():
            (self.root / "pm/roadmap/ambient.md").write_text("drift\n", encoding="utf-8")
        self._assert_drift_refuses_without_writing(mutate)

    def test_changed_policy_refuses(self):
        def mutate():
            path = self.root / "pm/programs/ambient.json"
            path.parent.mkdir(parents=True)
            path.write_text("{}\n", encoding="utf-8")
        self._assert_drift_refuses_without_writing(mutate)

    def test_changed_roster_refuses(self):
        def mutate():
            path = self.root / ".git/pmo-orchestration/drivers.json"
            path.parent.mkdir(parents=True)
            path.write_text("{}\n", encoding="utf-8")
        self._assert_drift_refuses_without_writing(mutate)

    def test_token_reuse_refuses_without_writing(self):
        preview = preview_setup(self.root, self.proposal_path)
        applied = call_tool(self.root, "dw_setup_apply", {
            "proposal": preview["proposal_id"], "expect": preview["expect"],
        })
        self.assertNotIn("isError", applied)
        self.assertEqual(applied["structuredContent"]["outcome"], "applied")
        snapshot = file_snapshot(self.root)
        with self.assertRaisesRegex(DwError, "already used"):
            apply_setup(self.root, preview["proposal_id"], preview["expect"])
        self.assertEqual(file_snapshot(self.root), snapshot)

    def test_malformed_proposal_and_unknown_id_refuse(self):
        self.proposal_path.write_text('{"schema":', encoding="utf-8")
        before = file_snapshot(self.root)
        with self.assertRaisesRegex(DwError, "cannot parse setup proposal JSON"):
            preview_setup(self.root, self.proposal_path)
        self.assertEqual(file_snapshot(self.root), before)
        with self.assertRaisesRegex(DwError, "unknown setup proposal id"):
            apply_setup(self.root, "setup:" + "0" * 64, "setup-sha256:" + "0" * 64)
        self.assertEqual(file_snapshot(self.root), before)

    def test_planted_failure_rolls_back_exactly(self):
        self.add_policy()
        preview = preview_setup(self.root, self.proposal_path)
        before = file_snapshot(self.root)
        with self.assertRaisesRegex(DwError, "planted setup transaction failure"):
            apply_setup(self.root, preview["proposal_id"], preview["expect"], fail_after=3)
        self.assertEqual(file_snapshot(self.root), before)
        self.assertFalse((self.root / "pm/roadmap/lease-demo").exists())

    def test_cli_mcp_http_preview_parity(self):
        cli = run(str(CLI), "--root", str(self.root), "setup", "preview", str(self.proposal_path), cwd=self.root)
        cli_payload = json.loads(cli.stdout)
        mcp = call_tool(self.root, "dw_setup_preview", {"proposal_file": str(self.proposal_path)})
        self.assertNotIn("isError", mcp)
        status, http = handle_mutation(self.root, "/api/setup/preview", {"proposal_file": str(self.proposal_path)})
        self.assertEqual(status, 200)
        mcp_payload = mcp["structuredContent"]
        http_payload = http["data"]
        self.assertEqual(canonical_setup_preview(cli_payload), canonical_setup_preview(mcp_payload))
        self.assertEqual(canonical_setup_preview(cli_payload), canonical_setup_preview(http_payload))
        self.assertEqual(mcp["content"][0]["text"], canonical_setup_preview(cli_payload))

    def test_setup_and_program_tokens_are_typed_and_non_substitutable(self):
        from dw_pmo.program_surface import start_program_by_id

        preview = preview_setup(self.root, self.proposal_path)
        before = file_snapshot(self.root)
        with self.assertRaisesRegex(DwError, "wrong token type"):
            apply_setup(self.root, preview["proposal_id"], "sha256:" + "0" * 64)
        with self.assertRaisesRegex(DwError, "wrong token type"):
            start_program_by_id(
                self.root, "missing-program", mode="no-commit", operator="operator",
                approval_reason="cross-use proof", intent_id="intent", capabilities=None,
                budgets=None, issued_at="2026-07-27T00:00:00Z",
                expires_at="2026-07-27T01:00:00Z", remote=None, remote_ref=None,
                expect=preview["expect"],
            )
        self.assertEqual(file_snapshot(self.root), before)
        self.assertTrue(preview["expect"].startswith("setup-sha256:"))

    def test_apply_advances_only_through_transition_function(self):
        preview = preview_setup(self.root, self.proposal_path)
        status, response = handle_mutation(self.root, "/api/setup/apply", {
            "proposal": preview["proposal_id"], "expect": preview["expect"],
        })
        self.assertEqual(status, 200)
        result = response["data"]
        self.assertEqual(result["journey_state"], "configured")
        record = self.root / ".git/pmo-setup-leases/pending" / (preview["proposal_id"].split(":", 1)[1] + ".json")
        self.assertEqual(json.loads(record.read_text(encoding="utf-8"))["proposal"]["state"], "configured")


if __name__ == "__main__":
    unittest.main()
