#!/usr/bin/env python3
"""Whole-bundle program validation regressions for WLA-30-06."""

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
sys.path.insert(0, str(TESTS_DIR.parent / "lib"))

from dw_pmo.mcpserver import _tool_program_validate
from dw_pmo.orchestration import canonical_json
from dw_pmo.orchestration_driver import write_driver_config
from dw_pmo.program_conductor import CONDUCTOR_NODE_TYPES
from dw_pmo.program_workflow import NODE_TYPES
from dw_pmo.programs import validate_program, validate_program_path
from dw_pmo.workbench import handle_api


class BundleValidationFixture(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="dw-bundle-validation.")).resolve()
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        self.root = self.temp / "repo"
        self.root.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Bundle Fixture")
        self.git("config", "user.email", "bundle@example.test")
        self.write_roadmap()
        self.write_bundle()
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        self.roster = self.driver_roster("family-a", "family-b")
        write_driver_config(self.root, self.roster)

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_json(self, relative, value):
        return self.write(relative, json.dumps(value, indent=2, sort_keys=True) + "\n")

    def read_json(self, relative):
        return json.loads((self.root / relative).read_text(encoding="utf-8"))

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
| DM-1-01 | Validate bundle | in-progress | [story-01-validate-bundle](./story-01-validate-bundle.md) | - |
""")
        self.write("pm/roadmap/demo/phase-1-demo/story-01-validate-bundle.md", """# DM-1-01 - Validate bundle

- **Project:** demo
- **Phase:** 1
- **Status:** in-progress
- **Depends on:** none
- **Owner:** unassigned

## Problem

Fixture story.
""")

    @staticmethod
    def role(role_id, duty, pool, workspace, driver_capabilities, ceiling, independent=()):
        return {
            "id": role_id,
            "duty": duty,
            "pool": pool,
            "required": True,
            "cardinality": 1,
            "capability_ceiling": ceiling,
            "driver_capabilities": driver_capabilities,
            "workspace": workspace,
            "context": {
                "allow": [
                    "story", "phase", "roadmap", "workflow-inputs",
                    "candidate-diff", "mechanical-receipts", "prior-verdicts",
                    "public-artifacts",
                ],
                "expressions": ["context", "parameter", "literal", "artifact"],
                "max_bytes": 500000,
            },
            "artifacts": {
                "read": ["markdown", "json", "text", "git-diff", "mechanical-fact", "verdict"],
                "write": ["git-diff", "markdown", "json", "text"] if workspace == "isolated-worktree" else ["verdict"],
                "max_bytes": 10000000,
            },
            "output_schema": "fixture-output@1" if workspace == "isolated-worktree" else None,
            "verdict_schema": None if workspace == "isolated-worktree" else "fixture-verdict@1",
            "max_concurrency": 1,
            "resource_groups": ["repository-writer"] if workspace == "isolated-worktree" else [],
            "may_request": [],
            "may_judge": ["implementer"] if duty == "verifier" else [],
            "independent_from": list(independent),
            "replacement": {
                "reasons": [],
                "max_replacements": 0,
                "fallback_pools": [],
                "on_exhausted": "block",
                "preserve_history": True,
            },
        }

    def write_bundle(self):
        self.workflow = {
            "kind": "delivery-workbench-workflow",
            "schema_version": 1,
            "slug": "bundle-flow",
            "title": "Bundle flow",
            "version": "1.0.0",
            "parameters": [{
                "id": "story-id", "type": "string", "required": True,
                "max_bytes": 128,
            }],
            "defaults": {},
            "nodes": [
                {
                    "id": "implement",
                    "type": "agent",
                    "role": "implementer",
                    "task": "Implement the selected story.",
                    "workspace": "isolated-worktree",
                    "capability_ceiling": ["agent:dispatch", "workspace:write"],
                    "timeout_seconds": 600,
                    "max_attempts": 1,
                    "inputs": {"story": {"kind": "parameter", "name": "story-id"}},
                    "outputs": [{"id": "candidate", "kind": "git-diff", "max_bytes": 1000000}],
                    "on_failure": {"kind": "action", "target": "block"},
                },
                {
                    "id": "required-check",
                    "type": "check",
                    "needs": ["implement"],
                    "runner": {"kind": "builtin", "name": "diff-scope", "allowed_paths": ["src/**"], "output_bytes": 100000},
                    "expect": {"exit_code": 0},
                    "timeout_seconds": 60,
                    "max_attempts": 1,
                    "outputs": [{"id": "fact", "kind": "mechanical-fact", "max_bytes": 100000}],
                    "on_failure": {"kind": "action", "target": "block"},
                },
                {
                    "id": "verify",
                    "type": "verdict",
                    "needs": ["required-check"],
                    "role": "verifier",
                    "rubric": "story-quality",
                    "subject": {"kind": "artifact", "name": "implement.candidate"},
                    "freshness_seconds": 3600,
                    "max_rationale_bytes": 10000,
                    "max_attempts": 1,
                    "results": ["pass", "fail", "abstain", "inconclusive"],
                    "routes": {
                        "pass": {"kind": "terminal", "target": "complete"},
                        "fail": {"kind": "action", "target": "block"},
                        "abstain": {"kind": "action", "target": "checkpoint"},
                        "inconclusive": {"kind": "action", "target": "block"},
                    },
                    "outputs": [{"id": "verdict", "kind": "verdict", "max_bytes": 50000}],
                },
            ],
            "terminals": [{"id": "complete", "meaning": "complete"}],
        }
        self.rubric = {
            "kind": "delivery-workbench-rubric",
            "schema_version": 1,
            "slug": "story-quality",
            "title": "Story quality",
            "version": "1.0.0",
            "subject_type": "diff",
            "result_vocabulary": ["pass", "fail", "needs-repair", "escalate"],
            "freshness": {
                "max_age_seconds": 3600,
                "bind": ["subject", "repository", "program", "assignment", "rubric", "ledger"],
            },
            "criteria": [{
                "id": "required-checks",
                "question": "Did the required check pass?",
                "evaluation": {"kind": "mechanical-fact", "fact": "required-check"},
                "required_evidence_kinds": [],
                "min_citations": 0,
                "allowed_results": ["pass", "fail", "abstain", "inconclusive"],
                "veto": True,
                "rationale_max_bytes": 512,
            }],
            "aggregation": {
                "method": "all", "threshold": 1, "on_pass": "pass",
                "on_fail": "needs-repair", "on_abstain": "escalate",
                "on_inconclusive": "needs-repair",
            },
        }
        self.organization = {
            "kind": "delivery-workbench-organization",
            "schema_version": 1,
            "slug": "story-cell",
            "title": "Story cell",
            "agents": [
                {
                    "id": "builder", "profile": "builder", "duties": ["implementer"],
                    "workspace_domain": "implementation", "capability_ceiling": ["agent:dispatch", "workspace:write"],
                    "max_concurrency": 1, "weight": 1,
                },
                {
                    "id": "reviewer", "profile": "reviewer", "duties": ["verifier"],
                    "workspace_domain": "verification", "capability_ceiling": ["agent:dispatch", "verdict:issue"],
                    "max_concurrency": 1, "weight": 1,
                },
            ],
            "pools": [
                {"id": "builders", "agents": ["builder"]},
                {"id": "reviewers", "agents": ["reviewer"]},
            ],
            "teams": [{
                "id": "delivery",
                "roles": [
                    self.role(
                        "implementer", "implementer", "builders",
                        "isolated-worktree", ["repository-read", "repository-write"],
                        ["agent:dispatch", "workspace:write"],
                    ),
                    self.role(
                        "verifier", "verifier", "reviewers", "read-only",
                        ["repository-read"], ["agent:dispatch", "verdict:issue"],
                        independent=("implementer",),
                    ),
                ],
            }],
            "councils": [],
            "diversity": [{
                "id": "cross-provider-review",
                "kind": "provider-family",
                "roles": ["implementer", "verifier"],
            }],
            "layout": {},
        }
        self.program = {
            "kind": "delivery-workbench-program",
            "schema_version": 1,
            "slug": "bundle-program",
            "title": "Bundle program",
            "scope": {
                "project": "demo",
                "phases": {"from": 1, "through": 1},
                "stories": {"include": ["DM-1-01"]},
                "selection": "roadmap-frontier-v1",
                "blocked_policy": "stop",
            },
            "organization": "story-cell",
            "bindings": [{
                "id": "delivery", "priority": 10,
                "match": {"phase_from": 1, "phase_through": 1, "story_ids": ["DM-1-01"]},
                "workflow": "bundle-flow",
                "with": {"story-id": {"kind": "context", "name": "story.id"}},
                "team": "delivery",
                "rubrics": ["story-quality"],
            }],
            "phase_gates": [],
            "mode_ceiling": "checkpointed",
            "requested_capabilities": [
                "program:select", "agent:dispatch", "check:execute",
                "workspace:write", "verdict:issue",
            ],
            "budgets": {
                "max_phases": 1, "max_stories": 1, "max_child_runs": 3,
                "max_agent_starts": 3, "max_provider_starts": 3,
                "max_model_starts": 3, "max_check_starts": 1,
                "max_loop_rounds": 1, "max_debate_rounds": 1,
                "max_councils": 1, "max_repairs_per_story": 1,
                "max_verdicts": 1, "max_obligations": 1,
                "max_obligation_materializations": 1,
                "max_obligation_dispositions": 1, "max_integrations": 1,
                "max_commits": 1, "max_pushes": 1, "max_nudges": 1,
                "max_lessons": 1, "max_artifact_bytes": 5000000,
                "max_tokens": 100000, "max_observed_cost_microunits": 100000,
                "max_wall_seconds": 5000,
            },
            "stop_conditions": ["scope-complete", "checkpoint-required", "budget-exhausted"],
            "layout": {},
        }
        self.flush_bundle()

    def flush_bundle(self):
        self.write_json("pm/workflows/bundle-flow.json", self.workflow)
        self.write_json("pm/rubrics/story-quality.json", self.rubric)
        self.write_json("pm/organizations/story-cell.json", self.organization)
        self.program_path = self.write_json("pm/programs/bundle-program.json", self.program)

    @staticmethod
    def driver_roster(builder_family, reviewer_family):
        return {
            "kind": "delivery-workbench-driver-config",
            "schema_version": 1,
            "workspace_root": None,
            "profiles": {
                "builder": {
                    "adapter": "fixture",
                    "adapter_version": "fixture-v1",
                    "provider_family": builder_family,
                    "capabilities": ["repository-read", "repository-write"],
                    "workspace_modes": ["isolated-worktree"],
                    "principal": "builder-principal",
                    "model": "builder-model",
                    "model_binding": "requested-alias",
                },
                "reviewer": {
                    "adapter": "fixture",
                    "adapter_version": "fixture-v1",
                    "provider_family": reviewer_family,
                    "capabilities": ["repository-read"],
                    "workspace_modes": ["read-only"],
                    "principal": "reviewer-principal",
                    "model": "reviewer-model",
                    "model_binding": "requested-alias",
                },
            },
        }

    def validate(self, driver_config=None, supplied=True):
        if supplied:
            return validate_program(
                self.root, copy.deepcopy(self.program),
                "pm/programs/bundle-program.json",
                driver_config=copy.deepcopy(driver_config if driver_config is not None else self.roster),
            )
        return validate_program(
            self.root, copy.deepcopy(self.program),
            "pm/programs/bundle-program.json", driver_config=None,
        )

    def diagnostic(self, document, code):
        return next(item for item in document["diagnostics"] if item["code"] == code)

    def assert_source_pointer_remediation(self, diagnostic):
        self.assertTrue(diagnostic["source"])
        self.assertTrue(diagnostic["pointer"].startswith("/"))
        self.assertTrue(diagnostic["remediation"])


class BundleFactAndBudgetTest(BundleValidationFixture):
    def test_fact_check_match_and_phase_29_mismatch_regression(self):
        valid = self.validate()
        self.assertTrue(valid["valid"], valid["diagnostics"])

        # Phase 29 attempt 7 used the output label "required-checks" where the
        # runtime fact id was the producing check node id. Attempt 8 then paid
        # again when that fact's old subject binding reached the live verdict.
        self.rubric["criteria"][0]["evaluation"]["fact"] = "required-checks"
        self.flush_bundle()
        refused = self.validate()
        diagnostic = self.diagnostic(refused, "mechanical-fact-unproduced")
        self.assertEqual(diagnostic["source"], "pm/rubrics/story-quality.json")
        self.assertEqual(diagnostic["pointer"], "/criteria/0/evaluation/fact")
        self.assert_source_pointer_remediation(diagnostic)

    def test_team_cardinality_verifier_and_fanout_budgets(self):
        self.program["budgets"].update({
            "max_child_runs": 1,
            "max_agent_starts": 1,
            "max_provider_starts": 1,
            "max_model_starts": 1,
        })
        self.program["budgets"]["max_verdicts"] = 1
        refused = self.validate()
        codes = {item["code"] for item in refused["diagnostics"]}
        self.assertIn("team-exceeds-budget", codes)
        self.assertIn("workflow-exceeds-budget", codes)
        for item in refused["diagnostics"]:
            if item["code"] in {"team-exceeds-budget", "workflow-exceeds-budget"}:
                self.assert_source_pointer_remediation(item)

        self.program["budgets"].update({
            "max_child_runs": 3,
            "max_agent_starts": 3,
            "max_provider_starts": 3,
            "max_model_starts": 3,
        })
        self.assertTrue(self.validate()["valid"])

    def test_larger_required_team_changes_the_minimum_budget_envelope(self):
        researcher = self.role(
            "researcher", "researcher", "researchers", "read-only",
            ["repository-read"], ["agent:dispatch"],
        )
        researcher["cardinality"] = 2
        researcher["output_schema"] = "fixture-output@1"
        researcher["verdict_schema"] = None
        self.organization["teams"][0]["roles"].append(researcher)
        self.organization["agents"].extend([
            {
                "id": "researcher-a", "profile": "researcher-a",
                "duties": ["researcher"], "workspace_domain": "research-a",
                "capability_ceiling": ["agent:dispatch"],
                "max_concurrency": 1, "weight": 1,
            },
            {
                "id": "researcher-b", "profile": "researcher-b",
                "duties": ["researcher"], "workspace_domain": "research-b",
                "capability_ceiling": ["agent:dispatch"],
                "max_concurrency": 1, "weight": 1,
            },
        ])
        self.organization["pools"].append({
            "id": "researchers", "agents": ["researcher-a", "researcher-b"],
        })
        roster = copy.deepcopy(self.roster)
        for name in ("researcher-a", "researcher-b"):
            roster["profiles"][name] = {
                "adapter": "fixture", "adapter_version": "fixture-v1",
                "provider_family": "family-a",
                "capabilities": ["repository-read"],
                "workspace_modes": ["read-only"],
                "principal": name + "-principal",
                "model": "research-model", "model_binding": "requested-alias",
            }
        self.program["budgets"].update({
            "max_child_runs": 3, "max_agent_starts": 3,
            "max_provider_starts": 3, "max_model_starts": 3,
        })
        self.flush_bundle()
        refused = self.validate(roster)
        self.assertIn(
            "team-exceeds-budget",
            {item["code"] for item in refused["diagnostics"]},
        )
        self.program["budgets"].update({
            "max_child_runs": 4, "max_agent_starts": 4,
            "max_provider_starts": 4, "max_model_starts": 4,
        })
        accepted = self.validate(roster)
        self.assertTrue(accepted["valid"], accepted["diagnostics"])

    def test_complete_green_route_is_required(self):
        self.workflow["terminals"] = [{"id": "complete", "meaning": "blocked"}]
        self.flush_bundle()
        refused = self.validate()
        diagnostic = self.diagnostic(refused, "no-complete-green-route")
        self.assertEqual(diagnostic["source"], "pm/workflows/bundle-flow.json")
        self.assert_source_pointer_remediation(diagnostic)


class BundleRosterAndParityTest(BundleValidationFixture):
    def test_diversity_satisfiable_unsatisfiable_and_roster_absent(self):
        self.assertTrue(self.validate()["valid"])

        same_family = self.driver_roster("family-a", "family-a")
        refused = self.validate(same_family)
        diagnostic = self.diagnostic(refused, "provider-diversity-unsatisfied")
        self.assertEqual(diagnostic["source"], "pm/organizations/story-cell.json")
        self.assertEqual(diagnostic["pointer"], "/diversity/0")
        self.assert_source_pointer_remediation(diagnostic)

        absent = self.validate(supplied=False)
        self.assertTrue(absent["valid"], absent["diagnostics"])
        self.assertEqual(absent["driver_roster"]["status"], "unverifiable-locally")
        self.assertEqual(absent["findings"][0]["type"], "unverifiable-locally")
        self.assert_source_pointer_remediation(absent["findings"][0])

        (self.root / ".git/pmo-orchestration/drivers.json").unlink()
        cli = subprocess.run(
            [
                sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
                "--root", str(self.root), "program", "validate",
                "bundle-program",
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(cli.returncode, 0, cli.stderr)
        self.assertIn("FINDING .git/pmo-orchestration/drivers.json:/", cli.stdout)
        self.assertIn("driver-roster-unverifiable-locally", cli.stdout)

    def test_roster_diagnostics_are_closed_and_credential_safe(self):
        document = self.validate()
        profiles = document["driver_roster"]["profiles"]
        self.assertEqual([item["profile"] for item in profiles], ["builder", "reviewer"])
        self.assertEqual(profiles[0]["adapter"], {"kind": "fixture", "version": "fixture-v1"})
        for key in (
            "provider_family", "capabilities", "principal", "workspace_modes", "model",
        ):
            self.assertIn(key, profiles[0])
        self.assertFalse(document["driver_roster"]["stores_credentials"])

        secret = "TOP-SECRET-CREDENTIAL-123"
        adversarial = copy.deepcopy(self.roster)
        adversarial["profiles"]["builder"]["api_key"] = secret
        refused = self.validate(adversarial)
        encoded = canonical_json(refused)
        self.assertIn("driver-roster-invalid", encoded)
        self.assertNotIn(secret, encoded)
        self.assertNotIn("api_key", encoded)
        self.assertNotIn("credential-123", encoded.lower())

        value_adversarial = copy.deepcopy(self.roster)
        value_adversarial["profiles"]["builder"]["model"] = secret
        redacted = self.validate(value_adversarial)
        self.assertTrue(redacted["valid"], redacted["diagnostics"])
        encoded = canonical_json(redacted)
        self.assertNotIn(secret, encoded)
        self.assertEqual(
            redacted["driver_roster"]["profiles"][0]["model"]["alias"],
            "[redacted]",
        )

        family_adversarial = self.driver_roster(secret, secret)
        refused = self.validate(family_adversarial)
        self.assertFalse(refused["valid"])
        self.assertNotIn(secret, canonical_json(refused))

    def test_unconductable_builtin_check_name_refuses_at_validation(self):
        # The Phase 30 exam's first live attempt refused at its first
        # tick on rail-status (separately authorized rail adapter);
        # builtin runner names now share the parity rule.
        self.workflow["nodes"][1]["runner"] = {
            "kind": "builtin", "name": "rail-status", "output_bytes": 100000,
        }
        self.flush_bundle()
        refused = self.validate()
        diagnostic = self.diagnostic(refused, "unconductable-builtin-check")
        self.assertIn("rail-status", diagnostic["message"])
        self.assertIn("diff-scope", diagnostic["remediation"])
        self.assert_source_pointer_remediation(diagnostic)

    def test_compiler_conductor_node_sets_are_code_owned_and_checkpoint_refuses(self):
        compiler_only = set(NODE_TYPES) - set(CONDUCTOR_NODE_TYPES)
        self.assertEqual(
            compiler_only,
            {"bounded_run", "gate", "checkpoint", "rail"},
        )
        self.assertIn("checkpoint", compiler_only)

        self.workflow["nodes"] = [{
            "id": "approval",
            "type": "checkpoint",
            "prompt_id": "approval",
            "prompt": "Choose the declared route.",
            "expires_seconds": 600,
            "options": [
                {"id": "continue", "label": "Continue", "route": {"kind": "terminal", "target": "complete"}},
                {"id": "stop", "label": "Stop", "route": {"kind": "action", "target": "block"}},
            ],
        }]
        self.flush_bundle()
        refused = self.validate()
        diagnostic = self.diagnostic(refused, "unconductable-node-type")
        self.assertEqual(diagnostic["pointer"], "/nodes/0/type")
        self.assertIn("checkpoint", diagnostic["message"])
        self.assert_source_pointer_remediation(diagnostic)


class BundlePolicyPurityAndParityTest(BundleValidationFixture):
    def test_tracked_execution_controls_refuse_with_pointers(self):
        cases = (
            ("executable", "tracked-executable"),
            ("argv", "tracked-argv"),
            ("environment", "tracked-environment"),
            ("driver_flags", "tracked-driver-flags"),
        )
        for key, code in cases:
            with self.subTest(key=key):
                program = copy.deepcopy(self.program)
                program[key] = ["forbidden"] if key in {"argv", "driver_flags"} else "forbidden"
                document = validate_program(
                    self.root, program, "pm/programs/bundle-program.json",
                    driver_config=self.roster,
                )
                diagnostic = self.diagnostic(document, code)
                self.assertEqual(diagnostic["pointer"], "/" + key)
                self.assert_source_pointer_remediation(diagnostic)

        self.organization["executable"] = "forbidden-local-binary"
        self.flush_bundle()
        linked = self.validate()
        diagnostic = self.diagnostic(linked, "tracked-executable")
        self.assertEqual(diagnostic["source"], "pm/organizations/story-cell.json")
        self.assertEqual(diagnostic["pointer"], "/executable")

        self.organization.pop("executable")

        # The one sanctioned command channel: a check node's runner with
        # exact tokenized argv (the shape the Phase 29 exit exam ran its
        # declared regression command through). Conforming form: accepted.
        self.workflow["nodes"][1]["runner"] = {
            "kind": "command",
            "argv": ["python3", "tests.py"],
            "cwd": ".",
            "writes": [],
            "output_bytes": 1000,
        }
        self.flush_bundle()
        document = self.validate()
        codes = {item["code"] for item in document["diagnostics"]}
        self.assertNotIn("tracked-executable", codes)
        self.assertNotIn("tracked-argv", codes)

        # Any deviation from the sanctioned shape loses the exemption:
        # an environment key inside the runner refuses the whole channel.
        self.workflow["nodes"][1]["runner"]["env"] = {"PATH": "/tmp"}
        self.flush_bundle()
        document = self.validate()
        self.assertEqual(
            self.diagnostic(document, "tracked-executable")["pointer"],
            "/nodes/1/runner/kind",
        )
        self.assertEqual(
            self.diagnostic(document, "tracked-environment")["pointer"],
            "/nodes/1/runner/env",
        )

        # And the same command shape anywhere outside a check node's
        # runner position is refused outright.
        del self.workflow["nodes"][1]["runner"]["env"]
        self.workflow["nodes"][0]["runner"] = {
            "kind": "command",
            "argv": ["python3", "tests.py"],
            "cwd": ".",
            "writes": [],
            "output_bytes": 1000,
        }
        self.flush_bundle()
        document = self.validate()
        self.assertEqual(
            self.diagnostic(document, "tracked-executable")["pointer"],
            "/nodes/0/runner/kind",
        )

    def test_validation_is_byte_stable_and_writes_nothing(self):
        before = {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in self.root.rglob("*") if path.is_file()
        }
        first = validate_program_path(self.root, self.program_path)
        second = validate_program_path(self.root, self.program_path)
        after = {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in self.root.rglob("*") if path.is_file()
        }
        self.assertEqual(canonical_json(first), canonical_json(second))
        self.assertEqual(before, after)
        for field in (
            "starts_work", "writes_state", "writes_policy", "writes_roster",
            "writes_grant", "writes_run", "writes_roadmap",
        ):
            self.assertFalse(first[field])
        self.assertFalse((self.root / ".git/pmo-programs/grants").exists())
        self.assertFalse((self.root / ".git/pmo-programs/runs").exists())

    def test_cli_mcp_and_http_validate_share_canonical_bytes(self):
        cli = subprocess.run(
            [
                sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
                "--root", str(self.root), "program", "validate",
                "bundle-program", "--json",
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(cli.returncode, 0, cli.stderr)
        mcp_text, mcp_document = _tool_program_validate(
            self.root, {"program": "bundle-program"},
        )
        status, http_envelope = handle_api(
            self.root, "/api/programs/bundle-program/validate", {},
        )
        self.assertEqual(status, 200)
        http_document = http_envelope["data"]
        self.assertEqual(cli.stdout.strip().encode("utf-8"), mcp_text.encode("utf-8"))
        self.assertEqual(mcp_document, http_document)
        self.assertEqual(
            mcp_text.encode("utf-8"),
            json.dumps(http_document, sort_keys=True).encode("utf-8"),
        )


class BundleRealPhase29IntegrationTest(unittest.TestCase):
    def test_real_phase_29_bundle_is_preflighted_as_one_linked_object(self):
        # The checked-in bundle carries the corrected attempt-7 fact id, the
        # enlarged attempt-4/5 team budget, and its declared regression
        # command in the one sanctioned position (a check node's exact
        # tokenized runner). Whole-bundle validation checks the historical
        # defect classes and compiler/conductor parity while accepting the
        # sanctioned command channel the exit exam actually ran through —
        # the bundle that delivered WLA-29-09 must preflight clean of
        # command-channel refusals.
        program = REPO_ROOT / "pm/programs/wla-29-08-first-real-run.json"
        document = validate_program_path(REPO_ROOT, program)
        codes = {item["code"] for item in document["diagnostics"]}
        self.assertNotIn("tracked-executable", codes)
        self.assertNotIn("tracked-argv", codes)
        self.assertNotIn("mechanical-fact-unproduced", codes)
        self.assertFalse(document["starts_work"])
        for item in document["diagnostics"]:
            self.assertTrue(item["source"])
            self.assertTrue(item["pointer"].startswith("/"))
            self.assertTrue(item["remediation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
