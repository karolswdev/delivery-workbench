#!/usr/bin/env python3
"""WLA-30-01 setup-proposal contract and architecture fitness tests."""

from __future__ import annotations

import copy
import inspect
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
LIB_ROOT = TESTS_DIR.parent / "lib"
sys.path.insert(0, str(LIB_ROOT))

import dw_pmo.setup_proposal as setup_proposal
from dw_pmo import DwError


def provenance(kind="user-answer", note="The operator supplied this answer."):
    return {"kind": kind, "source_note": note}


def text_item(text, kind="user-answer"):
    return {"text": text, "provenance": provenance(kind)}


def proposal_fixture():
    return {
        "schema": setup_proposal.SCHEMA,
        "state": "draft",
        "project": {
            "slug": "sample-project",
            "prefix": "SP",
            "title": "Sample project",
            "provenance": provenance(),
        },
        "source_intent": {
            "idea": "Build a small tool that keeps delivery work reviewable.",
            "mode": "build",
            "provenance": provenance(),
        },
        "tracked_content": {
            "roadmap": {
                "phases": [{
                    "number": 1,
                    "title": "First useful slice",
                    "goal": "Deliver one reviewable end-to-end path.",
                    "provenance": provenance("recommendation", "Suggested sequencing."),
                    "stories": [{
                        "id_sketch": "SP-1-01",
                        "title": "Ship the first slice",
                        "problem": "There is no usable path yet.",
                        "scope_in": [text_item("Implement the bounded path.")],
                        "scope_out": [text_item("Hosted operation is deferred.", "recommendation")],
                        "acceptance_criteria": [
                            text_item("The path is covered by a deterministic test.")
                        ],
                        "dependencies": [{
                            "id_sketch": "SP-0-01",
                            "provenance": provenance(
                                "repository-fact", "The existing roadmap names this dependency."
                            ),
                        }],
                        "provenance": provenance(),
                    }],
                }],
                "exit_criteria": [
                    text_item("A fresh checkout passes the focused test.", "recommendation")
                ],
            },
            "policy": None,
        },
        "local_content": {
            "driver_bindings": {
                "implementer": {
                    "adapter": "fixture",
                    "model": "fixture-model",
                    "provider": "fixture",
                    "provenance": provenance(
                        "repository-fact", "The local driver roster exposes this profile."
                    ),
                }
            }
        },
        "unresolved_questions": [{
            "question": "Which deployment target should a later phase cover?",
            "provenance": provenance(
                "recommendation", "The rough idea does not choose a target."
            ),
        }],
        "starts_work": False,
        "creates_grant": False,
        "certifies": False,
        "commits": False,
    }


def policy_document(kind):
    return {
        "document": {"kind": kind, "schema_version": 1, "values": ["bounded"]},
        "provenance": provenance("recommendation", "Generated default for review."),
    }


class SetupProposalContractTest(unittest.TestCase):
    def test_canonical_serialization_is_byte_stable_across_round_trip(self):
        proposal = proposal_fixture()
        first = setup_proposal.canonical_json(proposal).encode("utf-8")
        second = setup_proposal.canonical_json(proposal).encode("utf-8")
        loaded = setup_proposal.load_proposal(first)
        third = setup_proposal.canonical_json(loaded).encode("utf-8")
        self.assertEqual(first, second)
        self.assertEqual(first, third)
        self.assertEqual(json.loads(first), proposal)

    def test_closed_fields_refuse_at_top_level_and_nested_paths(self):
        cases = []
        top = proposal_fixture()
        top["authority"] = False
        cases.append((top, "/authority: unknown field"))
        nested = proposal_fixture()
        nested["tracked_content"]["roadmap"]["phases"][0]["stories"][0]["extra"] = "x"
        cases.append((nested, "/tracked_content/roadmap/phases/0/stories/0/extra"))
        for proposal, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic), self.assertRaisesRegex(
                DwError, re.escape(diagnostic)
            ):
                setup_proposal.validate_proposal(proposal)

    def test_unsupported_schema_and_missing_project_identity_refuse(self):
        wrong_schema = proposal_fixture()
        wrong_schema["schema"] = "delivery-workbench-setup-proposal@2"
        with self.assertRaisesRegex(DwError, r"^/schema: unsupported"):
            setup_proposal.validate_proposal(wrong_schema)

        missing_identity = proposal_fixture()
        del missing_identity["project"]["title"]
        with self.assertRaisesRegex(DwError, r"^/project/title: field is required"):
            setup_proposal.validate_proposal(missing_identity)

    def test_each_inertness_field_is_required_and_exactly_false(self):
        for field in ("starts_work", "creates_grant", "certifies", "commits"):
            missing = proposal_fixture()
            del missing[field]
            with self.subTest(field=field, value="missing"), self.assertRaisesRegex(
                DwError, "^/%s:" % field
            ):
                setup_proposal.validate_preview(missing)
            active = proposal_fixture()
            active[field] = True
            with self.subTest(field=field, value=True), self.assertRaisesRegex(
                DwError, "^/%s: must be false" % field
            ):
                setup_proposal.validate_preview(active)

    def test_string_list_and_opaque_document_bounds_refuse(self):
        title = proposal_fixture()
        title["project"]["title"] = "x" * (setup_proposal.MAX_TITLE + 1)
        with self.assertRaisesRegex(DwError, r"^/project/title: must be a bounded string"):
            setup_proposal.validate_proposal(title)

        phases = proposal_fixture()
        phase = phases["tracked_content"]["roadmap"]["phases"][0]
        phases["tracked_content"]["roadmap"]["phases"] = [
            copy.deepcopy(phase) for _ in range(setup_proposal.MAX_PHASES + 1)
        ]
        with self.assertRaisesRegex(DwError, r"^/tracked_content/roadmap/phases: must be a bounded list"):
            setup_proposal.validate_proposal(phases)

        opaque = proposal_fixture()
        opaque["tracked_content"]["policy"] = {
            "program": policy_document("delivery-workbench-program"),
            "workflows": [policy_document("delivery-workbench-workflow")],
            "organization": policy_document("delivery-workbench-organization"),
            "rubrics": [policy_document("delivery-workbench-rubric")],
            "provenance": provenance("recommendation"),
        }
        opaque["tracked_content"]["policy"]["program"]["document"]["large"] = (
            "x" * (setup_proposal.MAX_OPAQUE_STRING + 1)
        )
        with self.assertRaisesRegex(DwError, r"/tracked_content/policy/program/document/large"):
            setup_proposal.validate_proposal(opaque)

    def test_optional_embedded_policy_documents_are_opaque_but_bounded_objects(self):
        proposal = proposal_fixture()
        proposal["tracked_content"]["policy"] = {
            "program": policy_document("not-revalidated-here"),
            "workflows": [policy_document("also-opaque")],
            "organization": policy_document("opaque-organization"),
            "rubrics": [policy_document("opaque-rubric")],
            "provenance": provenance("recommendation"),
        }
        self.assertIs(setup_proposal.validate_proposal(proposal), proposal)
        proposal["tracked_content"]["policy"]["program"]["document"] = []
        with self.assertRaisesRegex(DwError, r"/tracked_content/policy/program/document: must be an opaque JSON object"):
            setup_proposal.validate_proposal(proposal)

    def test_all_provenance_vocabularies_are_accepted(self):
        for kind in setup_proposal.PROVENANCE_KINDS:
            proposal = proposal_fixture()
            proposal["project"]["provenance"] = provenance(kind)
            setup_proposal.validate_proposal(proposal)

    def test_missing_and_unknown_provenance_refuse(self):
        missing = proposal_fixture()
        del missing["tracked_content"]["roadmap"]["phases"][0]["provenance"]
        with self.assertRaisesRegex(DwError, r"/phases/0/provenance: field is required"):
            setup_proposal.validate_proposal(missing)

        unknown = proposal_fixture()
        unknown["tracked_content"]["roadmap"]["exit_criteria"][0]["provenance"]["kind"] = "agent-guess"
        with self.assertRaisesRegex(DwError, r"/exit_criteria/0/provenance/kind"):
            setup_proposal.validate_proposal(unknown)

    def test_unresolved_questions_are_explicit_bounded_provenanced_items(self):
        proposal = proposal_fixture()
        validated = setup_proposal.validate_proposal(proposal)
        self.assertEqual(
            validated["unresolved_questions"][0]["question"],
            "Which deployment target should a later phase cover?",
        )
        missing = proposal_fixture()
        del missing["unresolved_questions"][0]["provenance"]
        with self.assertRaisesRegex(DwError, r"^/unresolved_questions/0/provenance"):
            setup_proposal.validate_proposal(missing)

    def test_driver_binding_rejects_credential_pattern_at_any_key(self):
        for secret_key in ("credential", "access_token", "client-secret", "password", "api_key"):
            proposal = proposal_fixture()
            binding = proposal["local_content"]["driver_bindings"]["implementer"]
            binding[secret_key] = "must-not-be-representable"
            with self.subTest(secret_key=secret_key), self.assertRaises(DwError):
                setup_proposal.validate_proposal(proposal)

        profile_key = proposal_fixture()
        profile_key["local_content"]["driver_bindings"]["api_token"] = (
            profile_key["local_content"]["driver_bindings"].pop("implementer")
        )
        with self.assertRaisesRegex(DwError, r"credential|token|contracted identifier"):
            setup_proposal.validate_proposal(profile_key)

    def test_duplicate_json_keys_and_non_finite_numbers_refuse(self):
        with self.assertRaises(DwError):
            setup_proposal.load_proposal('{"schema":"a","schema":"b"}')
        text = setup_proposal.canonical_json(proposal_fixture()).replace(
            '"number":1', '"number":NaN'
        )
        with self.assertRaises(DwError):
            setup_proposal.load_proposal(text)


class SetupProposalJourneyTest(unittest.TestCase):
    def test_fixture_walks_all_six_named_states(self):
        reached = [setup_proposal.JOURNEY_STATES[0]]
        for target in setup_proposal.JOURNEY_STATES[1:]:
            reached.append(setup_proposal.transition_state(reached[-1], target))
        self.assertEqual(tuple(reached), setup_proposal.JOURNEY_STATES)
        self.assertEqual(setup_proposal.transition_state("reviewed", "draft"), "draft")

    def test_every_other_transition_refuses(self):
        allowed = set(zip(
            setup_proposal.JOURNEY_STATES,
            setup_proposal.JOURNEY_STATES[1:],
        )) | {("reviewed", "draft")}
        for current in setup_proposal.JOURNEY_STATES:
            for target in setup_proposal.JOURNEY_STATES:
                if (current, target) in allowed:
                    continue
                with self.subTest(current=current, target=target), self.assertRaises(DwError):
                    setup_proposal.transition_state(current, target)

    def test_validation_never_moves_state_implicitly(self):
        proposal = proposal_fixture()
        before = proposal["state"]
        setup_proposal.validate_proposal(proposal)
        setup_proposal.validate_preview(proposal)
        setup_proposal.canonical_json(proposal)
        self.assertEqual(proposal["state"], before)
        with self.assertRaises(TypeError):
            setup_proposal.transition_state(before)  # type: ignore[call-arg]


class SetupProposalFitnessTest(unittest.TestCase):
    def test_load_and_validate_create_no_files(self):
        proposal = proposal_fixture()
        raw = setup_proposal.canonical_json(proposal)
        previous = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="dw-setup-proposal-fitness.") as directory:
            root = Path(directory)
            os.chdir(root)
            try:
                self.assertEqual(list(root.iterdir()), [])
                setup_proposal.load_proposal(raw)
                setup_proposal.validate_proposal(proposal)
                setup_proposal.validate_preview(proposal)
                self.assertEqual(list(root.iterdir()), [])
            finally:
                os.chdir(previous)

    def test_module_is_pure_stdlib_offline_and_non_spawning(self):
        source = inspect.getsource(setup_proposal)
        imports = set(re.findall(
            r"^\s*(?:from\s+([\w.]+)|import\s+([\w.]+))",
            source,
            flags=re.MULTILINE,
        ))
        flattened = {left or right for left, right in imports}
        self.assertEqual(flattened, {"__future__", "json", "re", "typing", ".model"})
        for forbidden in ("subprocess", "socket", "urllib", "requests", "os.", "open("):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
