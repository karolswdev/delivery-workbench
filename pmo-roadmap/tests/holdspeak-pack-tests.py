#!/usr/bin/env python3
"""Tests for the HoldSpeak plugin pack (WLA-12-02).

Requires holdspeak importable (CI installs it from the pinned
v0.4.0 tag; locally use HoldSpeak's venv python). Without it the
whole module skips loudly rather than passing vacuously.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent
PACK_PATH = REPO_ROOT / "integrations" / "holdspeak" / "delivery_workbench_pack.py"
TRANSCRIPT_PATH = (
    REPO_ROOT / "integrations" / "holdspeak" / "fixtures"
    / "delivery-meeting-transcript.txt"
)
DW = REPO_ROOT / "pmo-roadmap" / "bin" / "dw"

try:
    import holdspeak  # noqa: F401

    HAVE_HOLDSPEAK = True
except ImportError:
    HAVE_HOLDSPEAK = False


def _load_pack():
    spec = importlib.util.spec_from_file_location(
        "delivery_workbench_pack", PACK_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_rails_fixture(root: Path) -> None:
    """A minimal rails repo: one project, one phase, two stories."""
    project = root / "pm" / "roadmap" / "webshop"
    project.mkdir(parents=True)
    (project / "README.md").write_text(
        "# Webshop - Roadmap\n\n"
        "**Last updated:** 2026-07-03.\n"
        "**Current phase:** n/a.\n"
        "**Status:** planning.\n\n"
        "## Phase index\n\n"
        "| Phase | Goal (one line) | Status | Folder |\n"
        "|---|---|---|---|\n\n"
        "## Project metadata\n\n"
        "- **Slug:** `webshop`\n"
        "- **Story ID prefix:** `WSH`\n",
        encoding="utf-8",
    )

    def dw(*args: str) -> None:
        subprocess.run(
            [sys.executable, str(DW), "--root", str(root), *args],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    dw("phase", "create", "webshop", "1", "Checkout flow", "--goal", "Ship checkout.")
    dw("story", "create", "webshop", "1", "Build the cart API")
    dw("story", "create", "webshop", "1", "Add payment provider")
    dw("story", "status", "webshop", "1", "WSH-1-01", "in-progress")
    # The pack prefers <repo>/.githooks/dw when present; give the
    # fixture a shim so resolution exercises the real path.
    hooks = root / ".githooks"
    hooks.mkdir()
    shim = hooks / "dw"
    shim.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" "{DW}" --root "{root}" "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)


GOOD_RESPONSE = """```json
{
  "aligned": [
    {"item": "Ship the cart API before payments", "kind": "decision",
     "story_id": "WSH-1-01", "why": "names the cart API work"},
    {"item": "Wire up the payment provider next", "kind": "action_item",
     "story_id": "WSH-1-02", "why": "names the payment story"}
  ],
  "drift": [
    {"item": "Dark mode for the storefront", "reason": "no story covers it"}
  ],
  "meeting_note": "Cart first, payments second, dark mode parked."
}
```"""

HALLUCINATED_RESPONSE = """```json
{
  "aligned": [
    {"item": "Rewrite everything in Rust", "kind": "decision",
     "story_id": "WSH-9-99", "why": "sounds plausible"}
  ],
  "drift": [],
  "meeting_note": "Ambitions exceeded the roadmap."
}
```"""


@unittest.skipUnless(
    HAVE_HOLDSPEAK,
    "holdspeak not importable — install it (CI pins the v0.4.0 tag) "
    "or run with HoldSpeak's venv python",
)
class PackUnitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = _load_pack()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rails = Path(self.tmp.name) / "rails"
        self.rails.mkdir()
        _build_rails_fixture(self.rails)
        self.transcript = TRANSCRIPT_PATH.read_text(encoding="utf-8")

    def _plugin(self, response: str, **kwargs):
        return self.pack.DeliveryWorkbenchAlignment(
            intel_call=lambda _messages: response, **kwargs
        )

    def _context(self, **extra):
        base = {
            "transcript": self.transcript,
            "active_intents": ["delivery"],
            "project_path": str(self.rails),
        }
        base.update(extra)
        return base

    def test_success_grounds_real_story_ids(self) -> None:
        out = self._plugin(GOOD_RESPONSE).run(self._context())
        self.assertEqual(out["confidence_hint"], 1.0)
        alignment = out["roadmap_alignment"]
        grounded = alignment["grounded_story_ids"]
        self.assertIn("WSH-1-01", grounded)
        self.assertIn("WSH-1-02", grounded)
        self.assertEqual(
            alignment["next_story"]["story_id"], "WSH-1-01",
            "next actionable story comes from dw context, not the model",
        )
        self.assertTrue(
            any("Dark mode" in d["item"] for d in alignment["drift"])
        )
        self.assertIn("WSH-1-01", out["summary"])
        self.assertIn("Drift", out["summary"])

    def test_hallucinated_story_id_is_demoted_to_drift(self) -> None:
        out = self._plugin(HALLUCINATED_RESPONSE).run(self._context())
        self.assertEqual(out["confidence_hint"], 1.0)
        alignment = out["roadmap_alignment"]
        self.assertEqual(alignment["aligned"], [])
        self.assertEqual(alignment["grounded_story_ids"], [])
        self.assertTrue(
            any("WSH-9-99" in d["reason"] for d in alignment["drift"]),
            "the invented ID must be named in the drift reason",
        )

    def test_unparseable_response_is_failure_shape(self) -> None:
        out = self._plugin("Sure! Here are my thoughts, no JSON.").run(
            self._context()
        )
        self.assertEqual(out["confidence_hint"], 0.0)
        self.assertNotIn("roadmap_alignment", out)
        self.assertIn("parseable", out["summary"])

    def test_no_roadmap_resolvable_fails_before_llm(self) -> None:
        calls: list = []

        def intel(messages):
            calls.append(messages)
            return GOOD_RESPONSE

        plugin = self.pack.DeliveryWorkbenchAlignment(
            intel_call=intel,
            config_path=Path(self.tmp.name) / "missing-config.json",
        )
        out = plugin.run(
            {
                "transcript": self.transcript,
                "active_intents": ["delivery"],
                "project_name": "unmapped-project",
            }
        )
        self.assertEqual(out["confidence_hint"], 0.0)
        self.assertNotIn("roadmap_alignment", out)
        self.assertIn("no roadmap resolvable", out["summary"])
        self.assertEqual(calls, [], "the LLM must not run without a roadmap")

    def test_broken_dw_is_failure_shape(self) -> None:
        shim = self.rails / ".githooks" / "dw"
        shim.write_text("#!/bin/sh\necho boom >&2\nexit 3\n", encoding="utf-8")
        out = self._plugin(GOOD_RESPONSE).run(self._context())
        self.assertEqual(out["confidence_hint"], 0.0)
        self.assertIn("exited 3", out["summary"])

    def test_empty_transcript_is_failure_shape(self) -> None:
        out = self._plugin(GOOD_RESPONSE).run(self._context(transcript="  "))
        self.assertEqual(out["confidence_hint"], 0.0)
        self.assertIn("no transcript", out["summary"])


@unittest.skipUnless(
    HAVE_HOLDSPEAK,
    "holdspeak not importable — install it (CI pins the v0.4.0 tag) "
    "or run with HoldSpeak's venv python",
)
class PackHostIntegrationTest(unittest.TestCase):
    """The pack through HoldSpeak's real discovery and host."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rails = Path(self.tmp.name) / "rails"
        self.rails.mkdir()
        _build_rails_fixture(self.rails)
        self.pack_dir = Path(self.tmp.name) / "packs"
        self.pack_dir.mkdir()
        (self.pack_dir / "delivery_workbench_pack.py").write_text(
            PACK_PATH.read_text(encoding="utf-8"), encoding="utf-8"
        )
        self.fixture_response = Path(self.tmp.name) / "canned.txt"
        self.fixture_response.write_text(GOOD_RESPONSE, encoding="utf-8")
        self.transcript = TRANSCRIPT_PATH.read_text(encoding="utf-8")

    def _context(self):
        return {
            "transcript": self.transcript,
            "active_intents": ["delivery"],
            "project_path": str(self.rails),
        }

    def _fresh_host(self, **kwargs):
        from holdspeak.plugins.host import PluginHost

        return PluginHost(default_timeout_seconds=60.0, **kwargs)

    def _register_pack(self, host):
        from holdspeak.plugin_pack_loader import load_and_register_plugin_packs

        registered, errors = load_and_register_plugin_packs(
            host, user_packs_dir=self.pack_dir, forbidden_ids=frozenset()
        )
        return registered, errors

    def test_discovery_registers_the_pack(self) -> None:
        host = self._fresh_host(enabled_capabilities={"llm"})
        registered, errors = self._register_pack(host)
        self.assertEqual(registered, ["delivery_workbench"])
        self.assertEqual(errors, [])
        self.assertIsNotNone(host.get_plugin("delivery_workbench"))

    def test_blocked_without_llm_capability(self) -> None:
        host = self._fresh_host()  # no capabilities enabled
        self._register_pack(host)
        result = host.execute(
            "delivery_workbench",
            context=self._context(),
            meeting_id="m-1",
            window_id="w-1",
            transcript_hash="h-1",
        )
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.error, "Missing capabilities: llm")

    def test_deferred_queue_then_drain_produces_alignment(self) -> None:
        os.environ["DW_PACK_INTEL_FIXTURE"] = str(self.fixture_response)
        self.addCleanup(os.environ.pop, "DW_PACK_INTEL_FIXTURE", None)
        host = self._fresh_host(enabled_capabilities={"llm"})
        self._register_pack(host)
        queued = host.execute(
            "delivery_workbench",
            context=self._context(),
            meeting_id="m-1",
            window_id="w-1",
            transcript_hash="h-1",
        )
        self.assertEqual(queued.status, "queued", "deferred plugins queue first")
        drained = host.process_next_deferred_run()
        self.assertIsNotNone(drained, "one deferred run must be waiting")
        self.assertEqual(drained.status, "success")
        alignment = drained.output["roadmap_alignment"]
        self.assertIn("WSH-1-01", alignment["grounded_story_ids"])

    def test_synthesized_artifact_carries_the_summary(self) -> None:
        os.environ["DW_PACK_INTEL_FIXTURE"] = str(self.fixture_response)
        self.addCleanup(os.environ.pop, "DW_PACK_INTEL_FIXTURE", None)
        from holdspeak.plugins.synthesis import synthesize_meeting_artifacts

        host = self._fresh_host(enabled_capabilities={"llm"})
        self._register_pack(host)
        result = host.execute(
            "delivery_workbench",
            context=self._context(),
            meeting_id="m-1",
            window_id="w-1",
            transcript_hash="h-1",
            defer_heavy=False,
        )
        self.assertEqual(result.status, "success")
        drafts = synthesize_meeting_artifacts(
            meeting_id="m-1",
            plugin_runs=[
                {
                    "id": "run-1",
                    "meeting_id": "m-1",
                    "window_id": "w-1",
                    "plugin_id": "delivery_workbench",
                    "plugin_version": result.plugin_version,
                    "status": result.status,
                    "output": result.output,
                    "created_at": "2026-07-03T00:00:00Z",
                }
            ],
        )
        self.assertEqual(len(drafts), 1)
        draft = drafts[0]
        # Verified reality (0.3.1 through 0.4.0, re-checked 2026-07-05):
        # packs cannot register renderers or
        # artifact types, so the artifact lands as plugin_output and
        # the rich markdown summary IS the rendered body.
        self.assertEqual(draft.artifact_type, "plugin_output")
        self.assertIn("WSH-1-01", draft.body_markdown)
        self.assertIn("Drift", draft.body_markdown)
        self.assertEqual(draft.status, "draft")


ACTUATOR_PACK_PATH = (
    REPO_ROOT / "integrations" / "holdspeak"
    / "delivery_workbench_actuator_pack.py"
)


def _load_actuator_pack():
    spec = importlib.util.spec_from_file_location(
        "delivery_workbench_actuator_pack", ACTUATOR_PACK_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ACTUATOR_LLM_RESPONSE = """```json
{"kind": "status", "project": "webshop", "story_id": "WSH-1-02",
 "status": "in-progress", "title": null,
 "why": "Dev picks up the payment provider next"}
```"""


class _FakeCompleted:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _RecordingRunner:
    def __init__(self, result=None):
        self.calls = []
        self.result = result or _FakeCompleted(stdout="ok")

    def __call__(self, argv, **kwargs):
        self.calls.append(list(argv))
        return self.result


@unittest.skipUnless(
    HAVE_HOLDSPEAK,
    "holdspeak not importable — install it (CI pins the v0.4.0 tag) "
    "or run with HoldSpeak's venv python",
)
class ActuatorProposalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = _load_actuator_pack()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rails = Path(self.tmp.name) / "rails"
        self.rails.mkdir()
        _build_rails_fixture(self.rails)

    def _plugin(self, response: str = ACTUATOR_LLM_RESPONSE):
        return self.pack.DeliveryWorkbenchStoryActuator(
            intel_call=lambda _messages: response
        )

    def _context(self, **extra):
        base = {
            "transcript": "Dev picks up the payment provider next.",
            "active_intents": ["delivery"],
            "project_path": str(self.rails),
        }
        base.update(extra)
        return base

    def test_explicit_action_builds_status_proposal(self) -> None:
        out = self._plugin().run(
            self._context(
                dw_action={
                    "kind": "status",
                    "project": "webshop",
                    "story_id": "WSH-1-02",
                    "status": "in-progress",
                    "why": "explicit desk request",
                }
            )
        )
        self.assertEqual(out["action"], "dw_story_status")
        self.assertEqual(out["payload"]["story"], "WSH-1-02")
        self.assertEqual(out["payload"]["status"], "in-progress")
        self.assertTrue(out["reversible"])
        self.assertIn("Reversal:", out["preview"])
        self.assertIn("dw gate still applies", out["preview"])

    def test_llm_path_builds_the_same_proposal(self) -> None:
        out = self._plugin().run(self._context())
        self.assertEqual(out["action"], "dw_story_status")
        self.assertEqual(out["payload"]["story"], "WSH-1-02")

    def test_invented_story_id_is_refused(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self._plugin().run(
                self._context(
                    dw_action={
                        "kind": "status",
                        "project": "webshop",
                        "story_id": "WSH-9-99",
                        "status": "done",
                    }
                )
            )
        self.assertIn("WSH-9-99", str(ctx.exception))

    def test_illegal_status_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self._plugin().run(
                self._context(
                    dw_action={
                        "kind": "status",
                        "project": "webshop",
                        "story_id": "WSH-1-01",
                        "status": "obliterated",
                    }
                )
            )

    def test_create_proposal_targets_a_real_phase(self) -> None:
        out = self._plugin().run(
            self._context(
                dw_action={
                    "kind": "create",
                    "project": "webshop",
                    "title": "Add gift cards",
                }
            )
        )
        self.assertEqual(out["action"], "dw_story_create")
        self.assertEqual(out["payload"]["phase"], "1")
        self.assertIn("deletable before anything commits", out["preview"])

    def test_no_action_meeting_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self._plugin().run(self._context(dw_action={"kind": "none"}))
        self.assertIn("no explicit roadmap action", str(ctx.exception))


@unittest.skipUnless(
    HAVE_HOLDSPEAK,
    "holdspeak not importable — install it (CI pins the v0.4.0 tag) "
    "or run with HoldSpeak's venv python",
)
class ActuatorConnectorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = _load_actuator_pack()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rails = Path(self.tmp.name) / "rails"
        self.rails.mkdir()
        _build_rails_fixture(self.rails)

    def _proposal(self, payload):
        from holdspeak.plugins.actuators import ActuatorProposal

        return ActuatorProposal(
            target="delivery-workbench",
            action="dw_story_status",
            preview="p",
            payload=payload,
            reversible=True,
            required_capabilities=("actuator",),
        )

    def test_happy_path_builds_allowlisted_argv(self) -> None:
        runner = _RecordingRunner()
        connector = self.pack.build_dw_connector(self.rails, runner=runner)
        out = connector(
            self._proposal(
                {
                    "repo": str(self.rails),
                    "verb": "status",
                    "project": "webshop",
                    "phase": "1",
                    "story": "WSH-1-02",
                    "status": "in-progress",
                }
            )
        )
        self.assertEqual(len(runner.calls), 1)
        argv = runner.calls[0]
        self.assertEqual(argv[-4:], ["webshop", "1", "WSH-1-02", "in-progress"])
        self.assertIn("story", argv)
        self.assertEqual(out["argv"], argv)

    def test_out_of_allowlist_verb_is_refused_before_egress(self) -> None:
        from holdspeak.plugins.gated_connector import ConnectorOperationRefused

        runner = _RecordingRunner()
        connector = self.pack.build_dw_connector(self.rails, runner=runner)
        with self.assertRaises(ConnectorOperationRefused):
            connector(
                self._proposal(
                    {"repo": str(self.rails), "verb": "delete", "project": "x"}
                )
            )
        self.assertEqual(runner.calls, [], "refusal must precede any egress")

    def test_foreign_repo_payload_is_refused(self) -> None:
        runner = _RecordingRunner()
        connector = self.pack.build_dw_connector(self.rails, runner=runner)
        with self.assertRaises(Exception):
            connector(
                self._proposal(
                    {
                        "repo": "/somewhere/else",
                        "verb": "status",
                        "project": "webshop",
                        "phase": "1",
                        "story": "WSH-1-02",
                        "status": "done",
                    }
                )
            )
        self.assertEqual(runner.calls, [])


@unittest.skipUnless(
    HAVE_HOLDSPEAK,
    "holdspeak not importable — install it (CI pins the v0.4.0 tag) "
    "or run with HoldSpeak's venv python",
)
class ActuatorEndToEndTest(unittest.TestCase):
    """propose → approve → execute against a real rails fixture,
    through HoldSpeak's real host, db, executor, and gated connector."""

    def setUp(self) -> None:
        self.pack = _load_actuator_pack()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rails = Path(self.tmp.name) / "rails"
        self.rails.mkdir()
        _build_rails_fixture(self.rails)

    def _db(self):
        from datetime import datetime

        from holdspeak.db import Database
        from holdspeak.meeting_session import MeetingState

        db = Database(Path(self.tmp.name) / "exec.db")
        db.meetings.save_meeting(
            MeetingState(
                id="m1", started_at=datetime.now(), title="t", segments=[]
            )
        )
        return db

    def _propose_via_host(self, dw_action):
        from holdspeak.plugins.host import PluginHost

        host = PluginHost(
            default_timeout_seconds=120.0,
            enabled_capabilities={"llm", "actuator"},
        )
        host.register(
            self.pack.DeliveryWorkbenchStoryActuator(
                intel_call=lambda _m: ACTUATOR_LLM_RESPONSE
            )
        )
        result = host.execute(
            "delivery_workbench_actuator",
            context={
                "transcript": "meeting",
                "active_intents": ["delivery"],
                "project_path": str(self.rails),
                "dw_action": dw_action,
            },
            meeting_id="m1",
            window_id="w-1",
            transcript_hash="h-1",
        )
        self.assertEqual(result.status, "proposed")
        return result

    def _approved_proposal(self, db, output):
        record = db.actuators.record_proposal(
            meeting_id="m1",
            window_id="w-1",
            plugin_id="delivery_workbench_actuator",
            plugin_version="0.1.0",
            idempotency_key=f"k-{output['action']}-{output['payload'].get('status', output['payload'].get('title'))}",
            target=output["target"],
            action=output["action"],
            preview=output["preview"],
            payload=output["payload"],
            reversible=output["reversible"],
            required_capabilities=list(output["required_capabilities"]),
        )
        db.actuators.transition_proposal(
            record.id, to_status="approved", actor="karol"
        )
        return record

    def _story_status_in_fixture(self, story_file: str) -> str:
        text = (
            self.rails / "pm" / "roadmap" / "webshop"
            / "phase-1-checkout-flow" / story_file
        ).read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("- **Status:**"):
                return line.split(":**", 1)[1].strip()
        return "?"

    def test_green_path_approved_flip_executes(self) -> None:
        from holdspeak.plugins.actuator_executor import ActuatorExecutor

        db = self._db()
        result = self._propose_via_host(
            {
                "kind": "status",
                "project": "webshop",
                "story_id": "WSH-1-02",
                "status": "in-progress",
            }
        )
        record = self._approved_proposal(db, result.output)
        executor = ActuatorExecutor(
            db,
            connector=self.pack.build_dw_connector(self.rails),
            allow_actuators=True,
            allowed_actuator_ids=["delivery_workbench_actuator"],
        )
        outcome = executor.execute(record.id)
        self.assertEqual(outcome.status, "executed")
        self.assertEqual(
            self._story_status_in_fixture("story-02-add-payment-provider.md"),
            "in-progress",
            "the rails fixture must show the flip",
        )

    def test_crown_case_gate_refuses_dishonest_done_flip(self) -> None:
        from holdspeak.plugins.actuator_executor import ActuatorExecutor

        db = self._db()
        result = self._propose_via_host(
            {
                "kind": "status",
                "project": "webshop",
                "story_id": "WSH-1-02",
                "status": "done",
            }
        )
        record = self._approved_proposal(db, result.output)
        executor = ActuatorExecutor(
            db,
            connector=self.pack.build_dw_connector(self.rails),
            allow_actuators=True,
            allowed_actuator_ids=["delivery_workbench_actuator"],
        )
        outcome = executor.execute(record.id)
        self.assertEqual(
            outcome.status, "failed",
            "approved by HoldSpeak, executed, and refused by the rails",
        )
        self.assertIn(
            "refusing to mark story done without evidence",
            outcome.error or "",
            "the dw banner must ride the proposal's error verbatim",
        )
        self.assertEqual(
            self._story_status_in_fixture("story-02-add-payment-provider.md"),
            "backlog",
            "the dishonest flip must not have landed",
        )

    def test_policy_defaults_execute_nothing(self) -> None:
        from holdspeak.plugins.actuator_executor import (
            ActuatorExecutor,
            ActuatorPolicyError,
        )

        db = self._db()
        result = self._propose_via_host(
            {
                "kind": "status",
                "project": "webshop",
                "story_id": "WSH-1-02",
                "status": "in-progress",
            }
        )
        record = self._approved_proposal(db, result.output)
        connector_calls = []
        executor = ActuatorExecutor(
            db,
            connector=lambda p: connector_calls.append(p) or {},
            allow_actuators=False,
        )
        with self.assertRaises(ActuatorPolicyError):
            executor.execute(record.id)
        executor_listed = ActuatorExecutor(
            db,
            connector=lambda p: connector_calls.append(p) or {},
            allow_actuators=True,
            allowed_actuator_ids=["some_other_actuator"],
        )
        with self.assertRaises(ActuatorPolicyError):
            executor_listed.execute(record.id)
        self.assertEqual(connector_calls, [], "no egress under default policy")

    def test_parity_mismatch_aborts_without_egress(self) -> None:
        from holdspeak.plugins.actuator_executor import ActuatorExecutor

        db = self._db()
        result = self._propose_via_host(
            {
                "kind": "status",
                "project": "webshop",
                "story_id": "WSH-1-02",
                "status": "in-progress",
            }
        )
        record = self._approved_proposal(db, result.output)
        connector_calls = []
        executor = ActuatorExecutor(
            db,
            connector=lambda p: connector_calls.append(p) or {},
            allow_actuators=True,
            allowed_actuator_ids=["delivery_workbench_actuator"],
        )
        outcome = executor.execute(
            record.id, approved_payload_hash="deadbeef" * 8
        )
        self.assertEqual(outcome.status, "failed")
        self.assertEqual(connector_calls, [], "no egress on parity mismatch")


if __name__ == "__main__":
    unittest.main(verbosity=2)
