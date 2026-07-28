#!/usr/bin/env python3
"""Scope-Chat proposal, rider, and revision fitness tests (WLA-30-03)."""

from __future__ import annotations

import copy
import json
import re
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
FRAMEWORK_ROOT = TESTS_DIR.parent
REPO_ROOT = FRAMEWORK_ROOT.parent
FIXTURES = TESTS_DIR / "fixtures"
SKILL = FRAMEWORK_ROOT / "agent" / "dw-scope.md"
sys.path.insert(0, str(FRAMEWORK_ROOT / "lib"))

from dw_pmo import riderdocs  # noqa: E402
from dw_pmo.setup_proposal import canonical_json, validate_proposal  # noqa: E402

BUILD_FIXTURE = FIXTURES / "scope-chat-build-proposal.json"
MAINTAIN_FIXTURE = FIXTURES / "scope-chat-maintain-proposal.json"
MAINTAIN_SHAPE = FIXTURES / "scope-chat-maintain-repo-shape.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def provenance_kinds(value):
    """Return every contracted provenance kind found in a JSON tree."""
    found = []
    if isinstance(value, dict):
        provenance = value.get("provenance")
        if isinstance(provenance, dict) and "kind" in provenance:
            found.append(provenance["kind"])
        for item in value.values():
            found.extend(provenance_kinds(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(provenance_kinds(item))
    return found


def canonical_section(value) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def regenerate_source_intent(proposal, *, idea, source_note):
    """Apply one revised interview answer without rebuilding other sections."""
    revised = copy.deepcopy(proposal)
    previous = revised["source_intent"]
    revised["source_intent"] = {
        "idea": idea,
        "mode": previous["mode"],
        "provenance": {
            "kind": "user-answer",
            "source_note": source_note,
        },
    }
    return revised


class ScopeChatFixtureTest(unittest.TestCase):
    def test_build_and_maintain_fixtures_validate(self):
        build = validate_proposal(load_json(BUILD_FIXTURE))
        maintain = validate_proposal(load_json(MAINTAIN_FIXTURE))
        self.assertEqual(build["source_intent"]["mode"], "build")
        self.assertEqual(maintain["source_intent"]["mode"], "maintain")
        self.assertFalse(build["starts_work"])
        self.assertFalse(maintain["starts_work"])

    def test_provenance_vocabularies_and_unresolved_items_are_distinct(self):
        for path in (BUILD_FIXTURE, MAINTAIN_FIXTURE):
            proposal = load_json(path)
            self.assertEqual(
                set(provenance_kinds(proposal)),
                {"user-answer", "repository-fact", "recommendation"},
                path.name,
            )
            self.assertGreaterEqual(len(proposal["unresolved_questions"]), 1)
            for item in proposal["unresolved_questions"]:
                self.assertEqual(set(item), {"question", "provenance"})
                self.assertIn(
                    item["provenance"]["kind"],
                    {"user-answer", "repository-fact", "recommendation"},
                )
                self.assertNotEqual(item["provenance"]["kind"], "unresolved")

    def test_maintain_fixture_is_grounded_in_fixture_repo_shape(self):
        shape = load_json(MAINTAIN_SHAPE)["files"]
        proposal = load_json(MAINTAIN_FIXTURE)
        project = shape["pm/roadmap/task-board/README.md"]
        phase = shape[
            "pm/roadmap/task-board/phase-2-shared-queue/current-phase-status.md"
        ]
        self.assertEqual(proposal["project"]["slug"], project["slug"])
        self.assertEqual(proposal["project"]["prefix"], project["prefix"])
        draft_phase = proposal["tracked_content"]["roadmap"]["phases"][0]
        self.assertEqual(draft_phase["number"], phase["phase"])
        self.assertEqual(draft_phase["goal"], phase["phase_goal"])
        notes = "\n".join(
            item["source_note"]
            for item in self._provenance_objects(proposal)
            if item["kind"] == "repository-fact"
        )
        for path in shape:
            self.assertIn(path, notes)

    @staticmethod
    def _provenance_objects(value):
        found = []
        if isinstance(value, dict):
            provenance = value.get("provenance")
            if isinstance(provenance, dict):
                found.append(provenance)
            for item in value.values():
                found.extend(ScopeChatFixtureTest._provenance_objects(item))
        elif isinstance(value, list):
            for item in value:
                found.extend(ScopeChatFixtureTest._provenance_objects(item))
        return found


class ScopeChatRevisionTest(unittest.TestCase):
    def test_revised_answer_keeps_unaffected_sections_byte_stable(self):
        original = validate_proposal(load_json(BUILD_FIXTURE))
        revised = regenerate_source_intent(
            original,
            idea=(
                "Help a household notice pantry food that should be used soon, "
                "including frozen food, without requiring a full inventory system."
            ),
            source_note=(
                "The revised user answer added frozen food while keeping the local "
                "household outcome."
            ),
        )
        validate_proposal(revised)

        self.assertNotEqual(
            canonical_section(original["source_intent"]),
            canonical_section(revised["source_intent"]),
        )
        for key in sorted(set(original) - {"source_intent"}):
            self.assertEqual(
                canonical_section(original[key]),
                canonical_section(revised[key]),
                "unchanged section %s drifted" % key,
            )

        first = canonical_json(revised)
        second = canonical_json(regenerate_source_intent(
            original,
            idea=revised["source_intent"]["idea"],
            source_note=revised["source_intent"]["provenance"]["source_note"],
        ))
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))


class ScopeChatSkillFitnessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text(encoding="utf-8")

    def test_skill_names_both_modes_and_minimum_interview(self):
        self.assertRegex(self.text, r"(?im)^- \*\*Build mode:\*\*")
        self.assertRegex(self.text, r"(?im)^- \*\*Maintain mode:\*\*")
        for subject in (
            "Project identity",
            "Desired outcome",
            "Intended users",
            "First usable milestone",
            "Constraints",
            "Non-goals",
            "Verification expectations",
            "Desired autonomy level",
        ):
            self.assertIn(subject, self.text)

    def test_skill_allows_read_surfaces_and_only_tmp_proposal_write(self):
        for surface in ("dw_status", "dw_context", "dw_board", "dw_story_show"):
            self.assertIn(surface, self.text)
        self.assertIn("the only write this skill may make", self.text)
        self.assertIn(".tmp/setup-proposal.json", self.text)
        self.assertIn("Do not use a\nshell or a general-purpose command runner.", self.text)
        self.assertNotIn(".githooks/dw", self.text)

        # Mutation vocabulary may appear only in an explicit refusal sentence.
        hard_boundary = self.text.split("## Hard boundary", 1)[1].split(
            "End every successful conversation", 1
        )[0]
        for fragment in (
            "story status",
            "phase create",
            "story create",
            "setup apply",
            "git commit",
        ):
            self.assertEqual(self.text.count(fragment), 1, fragment)
            self.assertIn(fragment, hard_boundary)
        self.assertRegex(
            hard_boundary, r"(?s)Never invoke `phase create`.*`git commit`"
        )
        affirmative = re.compile(
            r"(?im)^\s*(?:run|call|invoke|execute)\b.*(?:story status|phase create|"
            r"story create|setup apply|git commit)"
        )
        self.assertIsNone(affirmative.search(self.text))

    def test_skill_has_exact_closing_handoff(self):
        closing = (
            "Review it in the Workbench under Roadmap changes (`#/edit`).\n"
            "Next command: `dw setup preview .tmp/setup-proposal.json`\n"
            "nothing has been saved"
        )
        self.assertIn(closing, self.text)
        self.assertTrue(self.text.rstrip().endswith("```"))

    def test_rider_inventory_distributes_scope_command_in_sync(self):
        self.assertIn("dw-scope", riderdocs.COMMAND_NAMES)
        canonical = riderdocs.command_spec("dw-scope")
        self.assertEqual(canonical, self.text)
        for relative in (".claude/commands/dw-scope.md", "plugin/commands/dw-scope.md"):
            target = REPO_ROOT / relative
            self.assertTrue(target.exists(), relative)
            self.assertEqual(target.read_text(encoding="utf-8"), canonical, relative)


if __name__ == "__main__":
    unittest.main()
