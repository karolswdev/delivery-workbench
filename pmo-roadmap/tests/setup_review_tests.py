#!/usr/bin/env python3
"""WLA-30-05 adoption-review model, transport, and purity tests."""

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
PMO_ROOT = TESTS_DIR.parent
LIB_ROOT = PMO_ROOT / "lib"
sys.path.insert(0, str(LIB_ROOT))

from dw_pmo.setup_lease import preview_setup
from dw_pmo.workbench import handle_api


def provenance(kind="user-answer", note="Recorded during setup review."):
    return {"kind": kind, "source_note": note}


def text_item(text, kind="user-answer"):
    return {"text": text, "provenance": provenance(kind)}


def proposal_fixture(slug="review-project", prefix="RP", mode="build"):
    return {
        "schema": "delivery-workbench-setup-proposal@1",
        "state": "reviewed",
        "project": {
            "slug": slug,
            "prefix": prefix,
            "title": "Review project" if mode == "build" else "Existing project",
            "provenance": provenance(),
        },
        "source_intent": {
            "idea": "Make one useful setup path understandable before saving it.",
            "mode": mode,
            "provenance": provenance(),
        },
        "tracked_content": {
            "roadmap": {
                "phases": [{
                    "number": 1,
                    "title": "First proof",
                    "goal": "Prove one useful path end to end.",
                    "provenance": provenance("recommendation"),
                    "stories": [{
                        "id_sketch": "%s-1-01" % prefix,
                        "title": "Prove the first path",
                        "problem": "The first useful path is not proven.",
                        "scope_in": [text_item("Build the bounded path.")],
                        "scope_out": [text_item("Hosted operation stays out.", "recommendation")],
                        "acceptance_criteria": [text_item("A focused check proves the path.")],
                        "dependencies": [{
                            "id_sketch": "%s-0-01" % prefix,
                            "provenance": provenance("repository-fact"),
                        }],
                        "provenance": provenance("recommendation"),
                    }],
                }],
                "exit_criteria": [text_item("The first path is reviewable.", "recommendation")],
            },
            "policy": None,
        },
        "local_content": {
            "driver_bindings": {
                "implementer": {
                    "adapter": "fixture",
                    "model": "fixture-model",
                    "provider": "fixture",
                    "provenance": provenance("repository-fact"),
                }
            }
        },
        "unresolved_questions": [],
        "starts_work": False,
        "creates_grant": False,
        "certifies": False,
        "commits": False,
    }


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


class SetupReviewTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dw-setup-review-")
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "Review Test"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "review@example.test"], check=True)
        (self.root / "pm" / "roadmap").mkdir(parents=True)
        self.proposal_path = self.root / "setup-proposal.json"

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, proposal, name="setup-proposal.json"):
        path = self.root / name
        path.write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")
        return path

    def review(self, path=None, proposal_id=None):
        query = {}
        if path is not None:
            query["proposal_file"] = [str(path.relative_to(self.root))]
        if proposal_id is not None:
            query["proposal"] = [proposal_id]
        status, response = handle_api(self.root, "/api/setup/review", query)
        self.assertEqual(status, 200)
        self.assertTrue(response["ok"])
        return response["data"]

    def test_draft_proposals_render_for_review_before_the_lease_gate(self):
        # A draft is exactly what a human reviews; the reviewed-state
        # gate belongs to lease minting, not the read-only review
        # (orchestrator correction while landing WLA-30-05: the first
        # cut reused the preview gate and refused every draft).
        draft = proposal_fixture()
        draft["state"] = "draft"
        model = self.review(self.write(draft, "draft.json"))
        self.assertTrue(model["valid"])
        self.assertEqual(model["configuration"]["label"], "configuration, not permission")
        self.assertTrue(model["review_only"])

    def test_four_proposal_states_render_honest_models(self):
        green = proposal_fixture()
        green["tracked_content"]["policy"] = {
            "program": {"document": {"slug": "review-program"}, "provenance": provenance("recommendation")},
            "workflows": [{"document": {"slug": "review-workflow"}, "provenance": provenance("recommendation")}],
            "organization": {"document": {"slug": "review-team"}, "provenance": provenance("recommendation")},
            "rubrics": [{"document": {"slug": "review-rubric"}, "provenance": provenance("recommendation")}],
            "provenance": provenance("recommendation"),
        }
        green_model = self.review(self.write(green, "greenfield.json"))
        self.assertTrue(green_model["valid"])
        self.assertEqual(green_model["project"]["context"], "This starts a new project roadmap.")
        self.assertTrue(green_model["configuration"]["policy"]["present"])
        self.assertEqual(green_model["configuration"]["label"], "configuration, not permission")

        existing_dir = self.root / "pm" / "roadmap" / "existing-project"
        existing_dir.mkdir(parents=True)
        (existing_dir / "README.md").write_text(
            "# Existing project - Roadmap\n\n**Current phase:** n/a.\n\n"
            "## Phase index\n\n| Phase | Goal (one line) | Status | Folder |\n"
            "|---|---|---|---|\n\n## Project metadata\n\n"
            "- **Slug:** `existing-project`\n- **Story ID prefix:** EP\n",
            encoding="utf-8",
        )
        existing = proposal_fixture("existing-project", "EP", "maintain")
        existing_model = self.review(self.write(existing, "existing.json"))
        self.assertTrue(existing_model["valid"])
        self.assertEqual(existing_model["project"]["context"], "This adds to a project that already exists.")

        unresolved = proposal_fixture("questions-project", "QP")
        unresolved["unresolved_questions"] = [
            {"question": "Who owns review?", "provenance": provenance()},
            {"question": "What is the later deployment target?", "provenance": provenance("recommendation")},
            {"question": "What cost ceiling applies?", "provenance": provenance("repository-fact")},
        ]
        unresolved_model = self.review(self.write(unresolved, "unresolved.json"))
        self.assertEqual(len(unresolved_model["unresolved_questions"]["items"]), 3)
        self.assertIn("3 assumptions", unresolved_model["unresolved_questions"]["summary"])

        invalid = copy.deepcopy(green)
        del invalid["project"]["title"]
        invalid_model = self.review(self.write(invalid, "invalid.json"))
        self.assertFalse(invalid_model["valid"])
        self.assertEqual(invalid_model["refusal"], "/project/title: field is required")
        self.assertIn("unknown", invalid_model["unresolved_questions"]["summary"])

    def test_http_review_and_cli_preview_share_exact_plan_facts(self):
        path = self.write(proposal_fixture())
        before = tree_snapshot(self.root)
        review = self.review(path)
        self.assertEqual(tree_snapshot(self.root), before, "GET review minted or wrote state")

        cli_preview = preview_setup(self.root, path)
        self.assertEqual(review["technical_details"]["proposal_hash"], cli_preview["proposal_hash"])
        self.assertEqual(review["technical_details"]["changes"], cli_preview["changes"])
        self.assertEqual(review["changes"]["paths"], [item["path"] for item in cli_preview["changes"]])
        self.assertEqual(
            set(review["changes"]["paths"]),
            {item["path"] for item in review["changes"]["tracked"] + review["changes"]["git_local"]},
        )
        self.assertNotIn("expect", review["technical_details"])
        self.assertFalse(review["starts_work"])
        self.assertFalse(review["creates_grant"])

    def test_pending_preview_review_is_read_only_and_preserves_exact_preview(self):
        path = self.write(proposal_fixture())
        preview = preview_setup(self.root, path)
        before = tree_snapshot(self.root)
        model = self.review(proposal_id=preview["proposal_id"])
        self.assertEqual(tree_snapshot(self.root), before)
        self.assertEqual(model["technical_details"]["pending_preview"], preview)
        self.assertEqual(model["changes"]["paths"], [item["path"] for item in preview["changes"]])

    def test_open_refresh_mark_and_abandon_surface_has_no_write_transport(self):
        path = self.write(proposal_fixture())
        before = tree_snapshot(self.root)
        first = self.review(path)
        second = self.review(path)
        self.assertEqual(first, second)
        self.assertEqual(tree_snapshot(self.root), before)
        self.assertFalse((self.root / ".git" / "pmo-setup-leases").exists())

        app_source = (PMO_ROOT / "workbench" / "app.js").read_text(encoding="utf-8")
        review_source = app_source[
            app_source.index("const adoptionReviewMarks"):
            app_source.index("const STATUS_VOCAB")
        ]
        for forbidden in ("postJson", "localStorage", "sessionStorage", "indexedDB"):
            self.assertNotIn(forbidden, review_source)
        for required in ("adoptionReviewMarks", "Accepted for preview", "Reject with corrections", "Abandon this mark"):
            self.assertIn(required, review_source)
        self.assertIn("browser page only", review_source)

    def test_route_is_contextual_and_does_not_add_primary_navigation(self):
        index = (PMO_ROOT / "workbench" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(index.count('class="navlink"'), 7)
        self.assertNotIn("adoption", index.lower())
        app_source = (PMO_ROOT / "workbench" / "app.js").read_text(encoding="utf-8")
        self.assertIn('adoption_review: "review adoption"', app_source)
        self.assertIn('parts[0] === "edit"', app_source)
        self.assertIn("captureAppFocus", app_source)
        css = (PMO_ROOT / "workbench" / "style.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 600px)", css)
        self.assertIn("color-scheme: light", css)
        self.assertIn("@media (prefers-color-scheme: dark)", css)


if __name__ == "__main__":
    unittest.main()
