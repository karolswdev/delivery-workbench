#!/usr/bin/env python3
"""Deterministic governed-program scaffold regressions for WLA-30-07."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent
FIXTURES = TESTS_DIR / "fixtures/program-scaffold"
sys.path.insert(0, str(TESTS_DIR.parent / "lib"))

from dw_pmo.model import DwError
from dw_pmo.orchestration_driver import write_driver_config
from dw_pmo.program_scaffold import (
    EXCLUDED_CAPABILITIES,
    derive_program_budgets,
    load_scaffold_answers,
    normalize_scaffold_answers,
    scaffold_program,
    simulate_scaffold_proposal,
)
from dw_pmo.programs import validate_program
from dw_pmo.setup_proposal import canonical_json, validate_proposal


class ProgramScaffoldFixture(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="dw-program-scaffold.")).resolve()
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        self.root = self.temp / "repo"
        self.root.mkdir()
        subprocess.run(
            ["git", "-C", str(self.root), "init", "-q", "-b", "main"],
            check=True,
        )
        self.write_roadmap()
        self.roster = self.driver_roster()
        write_driver_config(self.root, self.roster)

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_roadmap(self):
        self.write("pm/roadmap/demo/README.md", """# Demo - Roadmap

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
        self.write("pm/roadmap/demo/phase-1-demo/current-phase-status.md", """# Phase 1 - Demo

**Last updated:** 2026-07-27.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DM-1-01 | Build first feature | in-progress | [story-01-build](./story-01-build.md) | - |
| DM-1-02 | Maintain first feature | ready | [story-02-maintain](./story-02-maintain.md) | - |
""")
        for number, title in ((1, "Build first feature"), (2, "Maintain first feature")):
            self.write(
                "pm/roadmap/demo/phase-1-demo/story-%02d-item.md" % number,
                "# DM-1-%02d - %s\n\n- **Project:** demo\n- **Phase:** 1\n- **Status:** ready\n- **Depends on:** none\n" % (number, title),
            )

    @staticmethod
    def driver_roster(same_family=False):
        reviewer_family = "anthropic" if same_family else "openai"
        return {
            "kind": "delivery-workbench-driver-config",
            "schema_version": 1,
            "workspace_root": None,
            "profiles": {
                "claude-builder": {
                    "adapter": "fixture", "adapter_version": "fixture-v1",
                    "provider_family": "anthropic",
                    "capabilities": ["repository-read", "repository-write"],
                    "workspace_modes": ["isolated-worktree"],
                    "principal": "claude-principal", "provider": "anthropic",
                    "model": "claude-bounded-alias", "model_binding": "requested-alias",
                },
                "codex-reviewer": {
                    "adapter": "fixture", "adapter_version": "fixture-v1",
                    "provider_family": "openai",
                    "capabilities": ["repository-read"],
                    "workspace_modes": ["read-only"],
                    "principal": "codex-principal", "provider": "openai",
                    "model": "codex-bounded-alias", "model_binding": "requested-alias",
                },
                "single-builder": {
                    "adapter": "fixture", "adapter_version": "fixture-v1",
                    "provider_family": "anthropic",
                    "capabilities": ["repository-read", "repository-write"],
                    "workspace_modes": ["isolated-worktree"],
                    "principal": "single-builder-principal", "provider": "anthropic",
                    "model": "single-builder-model", "model_binding": "requested-alias",
                },
                "single-reviewer": {
                    "adapter": "fixture", "adapter_version": "fixture-v1",
                    "provider_family": reviewer_family,
                    "capabilities": ["repository-read"],
                    "workspace_modes": ["read-only"],
                    "principal": "single-reviewer-principal", "provider": reviewer_family,
                    "model": "single-reviewer-model", "model_binding": "requested-alias",
                },
            },
        }

    def fixture(self, name):
        return load_scaffold_answers((FIXTURES / name).read_text(encoding="utf-8"))

    @staticmethod
    def policy_parts(proposal):
        policy = proposal["tracked_content"]["policy"]
        program = policy["program"]["document"]
        organization = policy["organization"]["document"]
        workflows = {
            wrapper["document"]["slug"]: wrapper["document"]
            for wrapper in policy["workflows"]
        }
        rubrics = {
            wrapper["document"]["slug"]: wrapper["document"]
            for wrapper in policy["rubrics"]
        }
        return program, {
            "workflows": workflows,
            "organizations": {organization["slug"]: organization},
            "rubrics": rubrics,
        }

    def files(self):
        return {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in self.root.rglob("*") if path.is_file()
        }


class ProgramScaffoldAnswersTest(ProgramScaffoldFixture):
    def test_closed_answers_default_checkpointed_and_pointer_refusals(self):
        answers = json.loads((FIXTURES / "greenfield-build.json").read_text())
        normalized = normalize_scaffold_answers(answers)
        self.assertEqual(normalized["autonomy_mode"], "checkpointed")

        cases = []
        unknown = copy.deepcopy(answers)
        unknown["extra"] = True
        cases.append((unknown, "/extra"))
        missing = copy.deepcopy(answers)
        del missing["profiles"]["verifier"]
        cases.append((missing, "/profiles/verifier"))
        wrong = copy.deepcopy(answers)
        wrong["size"]["fan_out"] = "two"
        cases.append((wrong, "/size/fan_out"))
        bad_scope = copy.deepcopy(answers)
        bad_scope["scope"]["story_ids"] = []
        cases.append((bad_scope, "/scope/story_ids"))
        for value, pointer in cases:
            with self.subTest(pointer=pointer):
                with self.assertRaisesRegex(DwError, "^" + pointer):
                    normalize_scaffold_answers(value)

    def test_unknown_check_and_argv_refuse(self):
        answers = json.loads((FIXTURES / "greenfield-build.json").read_text())
        answers["verification"]["built_in_checks"] = ["hope-tests-pass"]
        with self.assertRaisesRegex(DwError, r"^/verification/built_in_checks/0"):
            normalize_scaffold_answers(answers)
        answers["verification"]["built_in_checks"] = ["diff-scope"]
        answers["verification"]["regression_argv"] = []
        with self.assertRaisesRegex(DwError, r"^/verification/regression_argv"):
            normalize_scaffold_answers(answers)

    def test_duplicate_json_keys_refuse(self):
        text = '{"schema":"a","schema":"b"}'
        with self.assertRaisesRegex(DwError, r"^/: cannot parse"):
            load_scaffold_answers(text)


class ProgramScaffoldCompilerTest(ProgramScaffoldFixture):
    def test_deterministic_byte_identical_and_no_write(self):
        answers = self.fixture("greenfield-build.json")
        before = self.files()
        first = scaffold_program(self.root, answers, driver_config=self.roster)
        middle = self.files()
        second = scaffold_program(self.root, answers, driver_config=self.roster)
        after = self.files()
        self.assertEqual(canonical_json(first).encode(), canonical_json(second).encode())
        self.assertEqual(before, middle)
        self.assertEqual(before, after)
        self.assertFalse((self.root / "pm/programs").exists())
        self.assertFalse(first["starts_work"])
        self.assertFalse(first["creates_grant"])

    def test_safe_capabilities_local_bindings_and_certified_terminal(self):
        proposal = scaffold_program(
            self.root, self.fixture("cross-provider-cell.json"),
            driver_config=self.roster,
        )
        validate_proposal(proposal)
        program, documents = self.policy_parts(proposal)
        self.assertFalse(EXCLUDED_CAPABILITIES.intersection(program["requested_capabilities"]))
        encoded = canonical_json(proposal)
        for capability in (
            "git:commit", "git:push", "integration:apply", "contract:generate",
            "release", "deploy", "publish", "arbitrary-shell", "arbitrary-network",
        ):
            self.assertNotIn('"%s"' % capability, encoded)
        bindings = proposal["local_content"]["driver_bindings"]
        self.assertEqual(bindings["claude-builder"]["model"], "claude-bounded-alias")
        self.assertEqual(bindings["codex-reviewer"]["provider"], "openai")
        workflow = next(iter(documents["workflows"].values()))
        self.assertEqual(workflow["terminals"][0]["id"], "certified-handoff")
        self.assertEqual(workflow["terminals"][0]["meaning"], "complete")

    def test_budgets_change_with_shape_and_are_not_phase_29_copy(self):
        small = self.fixture("greenfield-build.json")
        large = self.fixture("cross-provider-cell.json")
        small_budgets = derive_program_budgets(small)
        large_budgets = derive_program_budgets(large)
        self.assertNotEqual(small_budgets, large_budgets)
        for key in (
            "max_child_runs", "max_check_starts", "max_tokens",
            "max_artifact_bytes", "max_wall_seconds",
        ):
            self.assertGreater(large_budgets[key], small_budgets[key])
        # The phase-29 hand-written example used 1,000,000 tokens, 20,000,000
        # artifact bytes, 50,000,000 cost units, and 18,000 seconds. The
        # compiler derives all four from scope x complexity x fan-out x repair
        # x mode rather than copying those trial-authored constants.
        phase_29 = {
            "max_tokens": 1_000_000,
            "max_artifact_bytes": 20_000_000,
            "max_observed_cost_microunits": 50_000_000,
            "max_wall_seconds": 18_000,
        }
        for key, value in phase_29.items():
            self.assertNotEqual(large_budgets[key], value)

        oversized = copy.deepcopy(large)
        oversized["scope"]["story_ids"] = [
            "DM-1-%d" % index for index in range(1, 2_001)
        ]
        oversized = normalize_scaffold_answers(oversized)
        with self.assertRaisesRegex(DwError, r"^/size: derived"):
            derive_program_budgets(oversized)

    def test_named_profile_refusals_are_not_best_effort(self):
        answers = self.fixture("greenfield-build.json")
        missing = copy.deepcopy(answers)
        missing["profiles"]["verifier"] = "absent-reviewer"
        with self.assertRaisesRegex(DwError, r"^/profiles/verifier"):
            scaffold_program(self.root, missing, driver_config=self.roster)

        same = self.fixture("single-provider-refusal.json")
        with self.assertRaisesRegex(DwError, r"^/profiles/verifier: named profiles do not satisfy"):
            scaffold_program(
                self.root, same, driver_config=self.driver_roster(same_family=True),
            )


class ProgramScaffoldGoldenTest(ProgramScaffoldFixture):
    def test_three_emitted_goldens_validate_and_simulate(self):
        for fixture_name in (
            "greenfield-build.json", "existing-maintenance.json",
            "cross-provider-cell.json",
        ):
            with self.subTest(fixture=fixture_name):
                answers = self.fixture(fixture_name)
                proposal = scaffold_program(
                    self.root, answers, driver_config=self.roster,
                )
                expected_path = FIXTURES / fixture_name.replace(
                    ".json", ".proposal.json"
                )
                self.assertEqual(
                    canonical_json(proposal),
                    expected_path.read_text(encoding="utf-8").strip(),
                )
                program, documents = self.policy_parts(proposal)
                validation = validate_program(
                    self.root, program, "golden:" + fixture_name,
                    driver_config=self.roster, bundle_documents=documents,
                )
                self.assertTrue(validation["valid"], validation["diagnostics"])
                self.assertEqual(validation["diagnostics"], [])
                simulation = simulate_scaffold_proposal(proposal)
                self.assertTrue(simulation["bounded"])
                self.assertEqual(simulation["green_route"][-1], "certified-handoff")
                self.assertEqual(simulation["repair_route"][0], "verify-initial:fail")
                self.assertEqual(
                    {route["type"] for route in simulation["failure_routes"]},
                    {
                        "check-failed", "verifier-abstained", "repair-failed",
                        "final-verdict-failed", "budget-exhausted",
                    },
                )

    def test_cross_provider_generated_bundle_is_simpler_than_phase_29(self):
        proposal = scaffold_program(
            self.root, self.fixture("cross-provider-cell.json"),
            driver_config=self.roster,
        )
        program, documents = self.policy_parts(proposal)
        organization = next(iter(documents["organizations"].values()))
        # Side-by-side with pm/programs/wla-29-08-first-real-run.json: the
        # generated cell requests six capabilities instead of nine — the
        # sixth is knowledge:lesson-writeback so the safest run still
        # learns (WLA-30-09) — omits integration/contract/roadmap-start
        # authority, has exactly two seats, binds mechanical facts to
        # their producing node ids, and expresses one route-activated
        # repair rather than relying on live grant attempts to discover
        # contradictions.
        self.assertEqual(len(program["requested_capabilities"]), 6)
        self.assertIn("knowledge:lesson-writeback", program["requested_capabilities"])
        self.assertEqual(len(organization["agents"]), 2)
        self.assertEqual(len(organization["diversity"]), 1)
        for rubric in documents["rubrics"].values():
            facts = [
                criterion["evaluation"]["fact"]
                for criterion in rubric["criteria"]
                if criterion["evaluation"]["kind"] == "mechanical-fact"
            ]
            workflow = next(iter(documents["workflows"].values()))
            node_ids = {node["id"] for node in workflow["nodes"]}
            self.assertTrue(set(facts) <= node_ids)

    def test_single_provider_golden_is_a_typed_refusal(self):
        expected = json.loads(
            (FIXTURES / "single-provider-refusal.expected.json").read_text(
                encoding="utf-8"
            )
        )
        with self.assertRaises(DwError) as raised:
            scaffold_program(
                self.root, self.fixture("single-provider-refusal.json"),
                driver_config=self.driver_roster(same_family=True),
            )
        self.assertEqual(
            raised.exception.message,
            expected["pointer"] + ": " + expected["message"],
        )

    def test_cli_emits_canonical_proposal_and_writes_nothing(self):
        answers_path = self.write(
            "answers.json",
            (FIXTURES / "greenfield-build.json").read_text(encoding="utf-8"),
        )
        before = self.files()
        result = subprocess.run(
            [
                "/usr/bin/python3", str(TESTS_DIR.parent / "bin/dw"),
                "--root", str(self.root), "program", "scaffold",
                "--answers", str(answers_path), "--json",
            ],
            check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        proposal = json.loads(result.stdout)
        self.assertEqual(result.stdout.strip(), canonical_json(proposal))
        self.assertEqual(before, self.files())
        self.assertFalse(proposal["starts_work"])


class ProgramScaffoldBaseProposalTest(ProgramScaffoldFixture):
    """Build mode before the roadmap exists: scope against the draft.

    The front-door journey scaffolds BEFORE `dw setup apply` creates the
    roadmap, so the conversation's proposal is the only truthful roadmap
    source; the scaffold embeds policy into it without editing it.
    """

    def base_proposal(self):
        return json.loads(
            (FIXTURES.parent / "scope-chat-build-proposal.json").read_text(
                encoding="utf-8"
            )
        )

    def base_answers(self):
        base = self.base_proposal()
        answers = self.fixture("greenfield-build.json")
        answers["project"] = {
            "slug": base["project"]["slug"],
            "prefix": base["project"]["prefix"],
            "title": base["project"]["title"],
            "mode": "build",
            "idea": base["source_intent"]["idea"],
        }
        answers["scope"] = {"phase_numbers": [1], "story_ids": ["PP-1-01"]}
        return answers

    def test_build_mode_scopes_against_the_base_proposal(self):
        base = self.base_proposal()
        proposal = scaffold_program(
            self.root, self.base_answers(),
            driver_config=self.roster, base_proposal=base,
        )
        self.assertEqual(
            proposal["tracked_content"]["roadmap"], base["tracked_content"]["roadmap"],
        )
        self.assertEqual(proposal["state"], base["state"])
        self.assertEqual(
            proposal["unresolved_questions"], base["unresolved_questions"],
        )
        self.assertIn("program", proposal["tracked_content"]["policy"])
        self.assertEqual(
            sorted(proposal["local_content"]["driver_bindings"]),
            ["claude-builder", "codex-reviewer"],
        )

    def test_scope_missing_from_base_and_identity_mismatch_refuse(self):
        answers = self.base_answers()
        answers["scope"]["story_ids"] = ["PP-1-99"]
        with self.assertRaises(DwError) as missing:
            scaffold_program(
                self.root, answers,
                driver_config=self.roster, base_proposal=self.base_proposal(),
            )
        self.assertIn("/scope/story_ids", str(missing.exception))

        answers = self.base_answers()
        answers["project"]["title"] = "Different Title"
        with self.assertRaises(DwError) as mismatch:
            scaffold_program(
                self.root, answers,
                driver_config=self.roster, base_proposal=self.base_proposal(),
            )
        self.assertIn("/project/title", str(mismatch.exception))

    def test_build_mode_without_base_or_project_names_the_remedy(self):
        answers = self.base_answers()
        with self.assertRaises(DwError) as refusal:
            scaffold_program(self.root, answers, driver_config=self.roster)
        self.assertIn("--proposal", str(refusal.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
