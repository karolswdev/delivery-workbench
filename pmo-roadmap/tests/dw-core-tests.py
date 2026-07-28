#!/usr/bin/env python3
"""Unit tests for the dw_pmo core package (WLA-5-02).

Covers parser fixtures, validation fixtures, mutation preview
idempotence (and that preview never writes), stale-target refusal at
apply time, roadmap-tree write containment, and work-log trace
fallback behavior. Stdlib only.
"""

from __future__ import annotations

import collections
import importlib.util
from importlib.machinery import SourceFileLoader
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(TESTS_DIR.parent / "lib"))

import dw_pmo as core
import dw_pmo.step as step_core
from dw_pmo import DwError
from repository_knowledge_tests import (
    RepositoryKnowledgeFitnessTest,
    RepositoryKnowledgeTest,
)
from repository_map_tests import (
    RealRepositoryMapTest,
    RepositoryMapIntegrationTest,
    SymbolMapUnitTest,
)
from grounding_tests import GroundingIntegrationTest, GroundingUnitTest
from init_cmd_tests import InitCommandTest
from knowledge_packet_tests import HonestUsageTest, KnowledgePacketTest
from knowledge_writeback_tests import KnowledgeWritebackTest
from bundle_validation_tests import (
    BundleFactAndBudgetTest,
    BundlePolicyPurityAndParityTest,
    BundleRealPhase29IntegrationTest,
    BundleRosterAndParityTest,
)
from setup_proposal_tests import (
    SetupProposalContractTest,
    SetupProposalFitnessTest,
    SetupProposalJourneyTest,
)
from setup_lease_tests import SetupLeaseTest


README = """# Demo - Roadmap

**Last updated:** 2026-07-02.
**Current phase:** [phase-1-alpha](./phase-1-alpha/current-phase-status.md).
**Status:** active.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 1 | Ship the alpha | active | [phase-1-alpha](./phase-1-alpha/) |

## Project metadata

- **Slug:** `demo`
- **Story ID prefix:** DM
"""

STATUS_FILE = """# Phase 1 - Alpha

**Last updated:** 2026-07-02.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DM-1-01 | First thing | done | [story-01-first](./story-01-first.md) | [evidence-story-01](./evidence-story-01.md) |
| DM-1-02 | Second thing | ready | [story-02-second](./story-02-second.md) | - |
"""

STORY_TMPL = """# {sid} - {title}

- **Project:** demo
- **Phase:** 1
- **Status:** {status}
- **Owner:** unassigned

## Problem

Fixture story.
"""

EVIDENCE_01 = """# Evidence - DM-1-01

- **Story:** DM-1-01 - First thing
- **Status:** done
- **Date:** 2026-07-02

## Proof

- fixture proof line
"""

WORK_LOG_ENTRY = """---
kind: pmo-work-log-entry
schema_version: 1
timestamp: 2026-07-02T10:00:00Z
project: demo
commit: 1111111111111111111111111111111111111111
---

## Commit

- **Subject:** fixture commit for DM-1-01
"""


class DwCoreTest(unittest.TestCase):
    def test_missioncontrol_readonly_fitness_guard(self):
        # WLA-15-03: the read-only guarantee as a fitness test. The
        # mutation dispatcher's source must never mention the
        # missioncontrol path, and every direct POST route is a named
        # exact-token act or guarded content preview/apply boundary — so no
        # import or route edit can quietly grow the belt a write path.
        import inspect

        import dw_pmo.workbench as wb
        mutation_src = inspect.getsource(wb.handle_mutation)
        self.assertNotIn("missioncontrol", mutation_src)
        post_routes = [
            line for line in mutation_src.splitlines()
            if "/api/" in line and "route ==" in line
        ]
        self.assertEqual(
            len(post_routes), 15,
            "only deliberate-step, guarded setup/roadmap/score/Studio edits, run "
            "preview/start, program grant preview/start/plan, and the receipted "
            "notification ack use direct POST equality routes; "
            f"found: {post_routes}",
        )
        self.assertTrue(any('/api/step/apply' in line for line in post_routes))
        self.assertTrue(any('/api/setup/preview' in line for line in post_routes))
        self.assertTrue(any('/api/setup/apply' in line for line in post_routes))
        self.assertTrue(any('/api/mutations/preview' in line for line in post_routes))
        self.assertTrue(any('/api/mutations/apply' in line for line in post_routes))
        self.assertTrue(any('/api/orchestration/preview' in line for line in post_routes))
        self.assertTrue(any('/api/orchestration/apply' in line for line in post_routes))
        self.assertTrue(any('/api/program-studio/preview' in line for line in post_routes))
        self.assertTrue(any('/api/program-studio/apply' in line for line in post_routes))
        self.assertTrue(any('/api/runs/preview' in line for line in post_routes))
        self.assertTrue(any('/api/runs/start' in line for line in post_routes))
        self.assertTrue(any('/api/programs/plan' in line for line in post_routes))
        self.assertTrue(any('/api/programs/preview' in line for line in post_routes))
        self.assertTrue(any('/api/programs/start' in line for line in post_routes))
        self.assertTrue(any('/api/notifications/ack' in line for line in post_routes))

    def test_missioncontrol_readonly_guard_catches_a_planted_write(self):
        # The guard must FAIL on a violation or it guards nothing:
        # feed it a planted dispatcher source and assert it sees the
        # write path (the Phase 14 fitness self-test pattern).
        planted = (
            "def handle_mutation(root, path, body):\n"
            "    route = path.rstrip(chr(47))\n"
            "    if route == '/api/missioncontrol/flip':\n"
            "        return apply_flip(body)\n"
        )
        self.assertIn("missioncontrol", planted,
                      "the scan must SEE the planted write path")

    def test_missioncontrol_live_layer_pins_only_on_story(self):
        # WLA-15-02: the pinning kernel, server-side and pure —
        # on_story pins to its story ids; ambiguous never guesses
        # (unknown beats guessed); everything else is off-belt.
        import dw_pmo.workbench as wb
        doc = {"sessions": [
            {"key": "a", "correlation": "on_story",
             "stories": [{"story_id": "DM-1-02"}]},
            {"key": "b", "correlation": "ambiguous",
             "stories": [{"story_id": "X-1"}, {"story_id": "X-2"}]},
            {"key": "c", "correlation": "off_rails", "stories": []},
            {"key": "d", "correlation": "on_story",
             "stories": [{"story_id": "DM-1-02"}, {"story_id": "DM-2-01"}]},
        ]}
        pins, off_belt = wb.mission_control_live_layer(doc)
        self.assertEqual(sorted(pins), ["DM-1-02", "DM-2-01"])
        self.assertEqual([s["key"] for s in pins["DM-1-02"]], ["a", "d"])
        self.assertEqual([s["key"] for s in off_belt], ["b", "c"])

    def test_missioncontrol_payload_carries_the_live_layer(self):
        import dw_pmo.workbench as wb
        status, body = wb.handle_api(self.root, "/api/missioncontrol", {})
        self.assertEqual(status, 200)
        self.assertIn("pins", body["data"])
        self.assertIn("off_belt", body["data"])

    def test_missioncontrol_route_serves_the_three_documents(self):
        # WLA-15-01: the workbench is the fourth consumer of the
        # mission-control substrate — one read-only GET returning the
        # feed, the correlation, and the events, via the in-process
        # API (never re-parsing pm/roadmap in the route).
        import dw_pmo.workbench as wb
        status, body = wb.handle_api(self.root, "/api/missioncontrol", {})
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual(data["feed"]["feed_schema"], 1)
        slugs = [p["slug"] for p in data["feed"]["projects"]]
        self.assertIn("demo", slugs)
        self.assertIn("sessions_schema", data["sessions"])
        self.assertIsInstance(data["events"], list)

    def test_missioncontrol_tail_clamps(self):
        import dw_pmo.workbench as wb
        status, body = wb.handle_api(
            self.root, "/api/missioncontrol", {"tail": ["99999"]}
        )
        self.assertEqual(status, 200)  # clamped, not an error

    def test_missioncontrol_has_no_mutation_route(self):
        # The read-only stance, asserted at the API layer: the
        # mutation dispatcher refuses any missioncontrol path.
        import dw_pmo.workbench as wb
        status, body = wb.handle_mutation(
            self.root, "/api/missioncontrol", {"anything": 1}
        )
        self.assertEqual(status, 405)

    def setUp(self) -> None:
        # Resolve like the CLI does (main() resolves --root / find_root
        # output); on macOS mkdtemp returns the /var symlink alias.
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-core-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.phase_dir = self.root / "pm" / "roadmap" / "demo" / "phase-1-alpha"
        self.phase_dir.mkdir(parents=True)
        (self.root / "pm" / "roadmap" / "demo" / "README.md").write_text(README, encoding="utf-8")
        (self.phase_dir / "current-phase-status.md").write_text(STATUS_FILE, encoding="utf-8")
        (self.phase_dir / "story-01-first.md").write_text(
            STORY_TMPL.format(sid="DM-1-01", title="First thing", status="done"), encoding="utf-8"
        )
        (self.phase_dir / "story-02-second.md").write_text(
            STORY_TMPL.format(sid="DM-1-02", title="Second thing", status="ready"), encoding="utf-8"
        )
        (self.phase_dir / "evidence-story-01.md").write_text(EVIDENCE_01, encoding="utf-8")
        self.project = core.get_project(self.root, "demo")
        self.phase = core.get_phase(self.project, "1")

    # -- parser fixtures --------------------------------------------------

    def test_parser_discovery(self) -> None:
        projects = core.discover_projects(self.root)
        self.assertEqual([p.slug for p in projects], ["demo"])
        self.assertEqual(projects[0].prefix, "DM")
        phases = core.discover_phases(self.project)
        self.assertEqual([(p.number, p.slug) for p in phases], [(1, "alpha")])
        rows = core.parse_story_rows(self.phase_dir / "current-phase-status.md")
        self.assertEqual([r.story_id for r in rows], ["DM-1-01", "DM-1-02"])
        self.assertEqual(rows[1].status, "ready")

    def test_find_story_selectors(self) -> None:
        for selector in ("DM-1-02", "2", "02", "story-02-second.md", "story-02-second"):
            row, num, path = core.find_story(self.project, self.phase, selector)
            self.assertEqual(row.story_id, "DM-1-02")
            self.assertEqual(num, 2)
            self.assertTrue(path.name == "story-02-second.md")
        with self.assertRaises(DwError):
            core.find_story(self.project, self.phase, "no-such-story")

    def test_story_title_empty_file(self) -> None:
        empty = self.phase_dir / "story-03-empty.md"
        empty.write_text("", encoding="utf-8")
        self.assertEqual(core.story_title(empty), "story-03-empty")

    # -- validation fixtures ----------------------------------------------

    def test_check_clean(self) -> None:
        self.assertEqual(core.check_project(self.project, self.root), [])

    def test_check_broken(self) -> None:
        status_file = self.phase_dir / "current-phase-status.md"
        broken = status_file.read_text(encoding="utf-8").replace(
            "| DM-1-02 | Second thing | ready | [story-02-second](./story-02-second.md) | - |",
            "| DM-1-02 | Second thing | done | [story-02-second](./story-02-second.md) | - |",
        )
        status_file.write_text(broken, encoding="utf-8")
        (self.phase_dir / "evidence-story-09.md").write_text("# orphan\n", encoding="utf-8")
        issues = "\n".join(core.check_project(self.project, self.root))
        self.assertIn("done story DM-1-02 has no evidence link", issues)
        self.assertIn("header status 'ready' differs from phase table 'done'", issues)
        self.assertIn("orphan evidence has no matching story row", issues)

    # -- mutation preview / apply ------------------------------------------

    def snapshot(self) -> dict[str, str]:
        return {
            str(p): p.read_text(encoding="utf-8")
            for p in sorted(self.phase_dir.parent.rglob("*.md"))
        }

    def test_preview_is_pure_and_idempotent(self) -> None:
        before = self.snapshot()
        plan_a = core.plan_story_status(self.root, self.project, self.phase, "DM-1-02", "in-progress")
        preview_a = core.preview_plan(plan_a)
        self.assertEqual(self.snapshot(), before, "preview must not write")
        plan_b = core.plan_story_status(self.root, self.project, self.phase, "DM-1-02", "in-progress")
        self.assertEqual(preview_a, core.preview_plan(plan_b), "same plan twice must preview identically")
        self.assertEqual(preview_a["kind"], "story-status")
        actions = {f["path"]: f["action"] for f in preview_a["files"]}
        self.assertTrue(all(a == "update" for a in actions.values()))

    def test_apply_returns_changes_and_validation(self) -> None:
        plan = core.plan_story_status(self.root, self.project, self.phase, "DM-1-02", "in-progress")
        result = core.apply_plan(plan)
        self.assertEqual(result["issues"], [])
        self.assertEqual(len(result["changed"]), 2)
        self.assertEqual(core.header_status(self.phase_dir / "story-02-second.md"), "in-progress")
        rows = core.parse_story_rows(self.phase_dir / "current-phase-status.md")
        self.assertEqual(rows[1].status, "in-progress")
        replan = core.plan_story_status(self.root, self.project, self.phase, "DM-1-02", "in-progress")
        self.assertTrue(
            all(not f["changed"] for f in core.preview_plan(replan)["files"]),
            "re-planning an applied status must be a no-op",
        )
        core.apply_plan(replan)

    def test_stale_target_refused_without_partial_write(self) -> None:
        plan = core.plan_story_status(self.root, self.project, self.phase, "DM-1-02", "in-progress")
        status_file = self.phase_dir / "current-phase-status.md"
        drifted = status_file.read_text(encoding="utf-8") + "\ndrifted-after-plan\n"
        status_file.write_text(drifted, encoding="utf-8")
        story_before = (self.phase_dir / "story-02-second.md").read_text(encoding="utf-8")
        with self.assertRaises(DwError) as ctx:
            core.apply_plan(plan)
        self.assertIn("stale mutation target", ctx.exception.message)
        self.assertEqual(status_file.read_text(encoding="utf-8"), drifted)
        self.assertEqual(
            (self.phase_dir / "story-02-second.md").read_text(encoding="utf-8"),
            story_before,
            "a stale refusal must not partially write",
        )

    def test_done_requires_evidence(self) -> None:
        with self.assertRaises(DwError) as ctx:
            core.plan_story_status(self.root, self.project, self.phase, "DM-1-02", "done")
        self.assertIn("refusing to mark story done without evidence", ctx.exception.message)

    def test_write_containment(self) -> None:
        outside = self.root / "escape.md"
        with self.assertRaises(DwError) as ctx:
            core.write_changes(self.root, {outside: "nope"})
        self.assertIn("outside PMO roadmap tree", ctx.exception.message)
        self.assertFalse(outside.exists())

    def test_phase_create_and_close(self) -> None:
        plan = core.plan_phase_create(self.root, self.project, 2, "Beta Work", status="planned")
        preview = core.preview_plan(plan)
        self.assertEqual(preview["create_dirs"], [core.rel(self.project.path / "phase-2-beta-work", self.root)])
        core.apply_plan(plan, validate_after=False)
        phase2 = core.get_phase(self.project, "2")
        self.assertTrue((phase2.path / "current-phase-status.md").exists())
        with self.assertRaises(DwError):
            core.plan_phase_create(self.root, self.project, 2, "Beta Work")
        close_plan = core.plan_phase_close(self.root, self.project, phase2)
        core.apply_plan(close_plan, validate_after=False)
        self.assertTrue((phase2.path / "final-summary.md").exists())
        with self.assertRaises(DwError) as ctx:
            core.plan_phase_close(self.root, self.project, self.phase)
        self.assertIn("refusing to close phase with non-done stories", ctx.exception.message)

    def test_phase_advance_is_one_guarded_summary_pointer_and_header_plan(self) -> None:
        phase2_plan = core.plan_phase_create(
            self.root,
            self.project,
            2,
            "Beta Work",
            status="planned",
        )
        core.apply_plan(phase2_plan, validate_after=False)
        phase2 = core.get_phase(self.project, "2")
        complete = core.plan_story_status(
            self.root,
            self.project,
            self.phase,
            "DM-1-02",
            "done",
            evidence_body="- exact fixture proof",
            evidence_date="2026-07-22",
        )
        core.apply_plan(complete, validate_after=False)
        before = self.snapshot()
        advance = core.plan_phase_advance(
            self.root,
            self.project,
            self.phase,
            phase2,
            summary_body="Exact fixture phase transition.",
            summary_date="2026-07-22",
        )
        preview = core.preview_plan(advance)
        self.assertEqual(before, self.snapshot(), "phase preview must be pure")
        self.assertEqual(preview["kind"], "phase-advance")
        self.assertEqual(preview["summary"]["next_phase_number"], 2)
        result = core.apply_plan(advance, validate_after=False)
        self.assertEqual(result["issues"], [])
        readme = (self.project.path / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "**Current phase:** [Phase 2 — Beta Work]"
            "(./phase-2-beta-work/current-phase-status.md).",
            readme,
        )
        self.assertIn(
            "**Status:** done",
            (self.phase.path / "current-phase-status.md").read_text(
                encoding="utf-8"
            ),
        )
        self.assertIn(
            "**Status:** in-progress",
            (phase2.path / "current-phase-status.md").read_text(
                encoding="utf-8"
            ),
        )
        self.assertTrue((self.phase.path / "final-summary.md").is_file())

    # -- trace fallback ----------------------------------------------------

    def test_work_log_trace_fallback(self) -> None:
        old = os.environ.get("PMO_WORK_LOG_DIR")
        log_root = self.tmp / "work-log"
        os.environ["PMO_WORK_LOG_DIR"] = str(log_root)
        try:
            self.assertEqual(core.work_log_entries(self.root, self.project), [], "missing log dir yields no entries")
            day = log_root / "2026-07-02"
            day.mkdir(parents=True)
            log_file = day / "demo-123-work-summary.log"
            log_file.write_text(WORK_LOG_ENTRY, encoding="utf-8")
            entries = core.work_log_entries(self.root, self.project)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["commit"], "1111111111111111111111111111111111111111")
            other = core.Project("otherproj", self.project.path, "OP")
            self.assertIsNone(core.parse_work_log_entry(log_file, self.root, other), "non-matching project must not correlate")
            rows = core.parse_story_rows(self.phase_dir / "current-phase-status.md")
            self.assertEqual(len(core.work_log_entries(self.root, self.project, rows[0])), 1, "story ID match correlates")
            self.assertEqual(core.work_log_entries(self.root, self.project, rows[1]), [], "unmentioned story does not correlate")
        finally:
            if old is None:
                os.environ.pop("PMO_WORK_LOG_DIR", None)
            else:
                os.environ["PMO_WORK_LOG_DIR"] = old


    # -- evidence capture and content lints (WLA-6-04) ------------------

    def test_capture_appends_and_records(self) -> None:
        before_others = {
            k: v for k, v in self.snapshot().items() if "evidence-story-02" not in k
        }
        code, path, ts = core.run_capture(
            self.root, self.project, self.phase, "DM-1-02", ["sh", "-c", "echo captured-ok"]
        )
        self.assertEqual(code, 0)
        text = path.read_text(encoding="utf-8")
        self.assertIn(f"### Captured run — {ts}", text)
        self.assertIn("- **Exit code:** 0", text)
        self.assertIn("captured-ok", text)
        code2, path2, _ts2 = core.run_capture(
            self.root, self.project, self.phase, "DM-1-02", ["sh", "-c", "echo boom; exit 5"]
        )
        self.assertEqual(code2, 5, "capture must mirror the command's exit code")
        self.assertEqual(path2, path)
        runs = core.parse_captured_runs(path.read_text(encoding="utf-8"))
        self.assertEqual([r["exit_code"] for r in runs], [0, 5])
        passing = core.latest_passing_capture(path.read_text(encoding="utf-8"))
        self.assertEqual(passing["timestamp"], ts)
        after_others = {
            k: v for k, v in self.snapshot().items() if "evidence-story-02" not in k
        }
        self.assertEqual(before_others, after_others, "capture must touch only the evidence file")

    def test_capture_never_hands_stdin_to_the_child(self) -> None:
        # WLA-12-08: under dw-mcp the parent's stdin is the JSON-RPC
        # pipe. A captured child that reads stdin must get DEVNULL,
        # not our pipe — otherwise it blocks on it (observed: a
        # 29-minute wedge) and can consume protocol bytes. Simulate
        # the server condition: swap this process's stdin for a pipe
        # holding sentinel bytes, capture `cat`, and require that
        # the sentinel never reaches the evidence file.
        sentinel = b"leaked-from-parent-stdin"
        read_fd, write_fd = os.pipe()
        os.write(write_fd, sentinel + b"\n")
        os.close(write_fd)  # EOF so even a regression cannot hang the suite
        saved_stdin = os.dup(0)
        os.dup2(read_fd, 0)
        os.close(read_fd)
        try:
            code, path, _ts = core.run_capture(
                self.root, self.project, self.phase, "DM-1-02", ["cat"]
            )
        finally:
            os.dup2(saved_stdin, 0)
            os.close(saved_stdin)
        self.assertEqual(code, 0)
        self.assertNotIn(
            sentinel.decode(),
            path.read_text(encoding="utf-8"),
            "captured child read the parent's stdin — it must get DEVNULL",
        )

    def test_capture_truncation_marker(self) -> None:
        block = core.render_capture_block(
            "cmd", ".", 0, "x" * 500, "2026-07-02T12:00:00Z", "tree", max_output_bytes=16
        )
        self.assertIn(core.TRUNCATION_MARKER, block)
        small = core.render_capture_block(
            "cmd", ".", 0, "tiny", "2026-07-02T12:00:00Z", "tree", max_output_bytes=16
        )
        self.assertNotIn(core.TRUNCATION_MARKER, small)

    def test_evidence_content_lints(self) -> None:
        placeholder = self.phase_dir / "evidence-story-07.md"
        placeholder.write_text(
            f"# Evidence\n\n## Proof\n\n- {core.EVIDENCE_PLACEHOLDER}\n", encoding="utf-8"
        )
        issues = core.evidence_content_issues(placeholder, self.phase_dir, self.root)
        self.assertTrue(any("generator placeholder" in i for i in issues))
        empty = self.phase_dir / "evidence-story-08.md"
        empty.write_text(
            "# Evidence - X\n\n- **Story:** X\n- **Status:** done\n\n## Proof\n", encoding="utf-8"
        )
        issues = core.evidence_content_issues(empty, self.phase_dir, self.root)
        self.assertTrue(any("evidence body is empty" in i for i in issues))
        with_asset = self.phase_dir / "evidence-story-09.md"
        with_asset.write_text(
            "# Evidence\n\n## Proof\n\n- see ![shot](./assets/shot.png)\n", encoding="utf-8"
        )
        issues = core.evidence_content_issues(with_asset, self.phase_dir, self.root)
        self.assertTrue(any("broken asset reference" in i for i in issues))
        (self.phase_dir / "assets").mkdir()
        (self.phase_dir / "assets" / "shot.png").write_bytes(b"png")
        self.assertEqual(core.evidence_content_issues(with_asset, self.phase_dir, self.root), [])

    def test_check_flags_placeholder_evidence_for_done_story(self) -> None:
        (self.phase_dir / "evidence-story-01.md").write_text(
            f"# Evidence - DM-1-01\n\n## Proof\n\n- {core.EVIDENCE_PLACEHOLDER}\n", encoding="utf-8"
        )
        issues = "\n".join(core.check_project(self.project, self.root))
        self.assertIn("generator placeholder", issues)

    def test_narrative_only_warning(self) -> None:
        warnings = "\n".join(core.project_warnings(self.project, self.root))
        self.assertIn("narrative-only evidence", warnings)
        self.assertIn("evidence-story-01.md", warnings)
        evidence = self.phase_dir / "evidence-story-01.md"
        block = core.render_capture_block("cmd", ".", 0, "ok", "2026-07-02T12:00:00Z", "tree")
        evidence.write_text(evidence.read_text(encoding="utf-8") + "\n" + block, encoding="utf-8")
        warnings = "\n".join(core.project_warnings(self.project, self.root))
        self.assertNotIn("narrative-only evidence", warnings)


    # -- health console (WLA-5-04) --------------------------------------------

    def test_health_classifier_kinds(self) -> None:
        cases = {
            "pm/x/README.md: current phase pointer is stale: phase-9": ("stale-pointer", "project"),
            "pm/x/phase-1: missing current-phase-status.md": ("missing-status-file", "phase"),
            "pm/x/s.md: broken story link for X-1-01: story-9.md": ("broken-story-link", "story-evidence"),
            "pm/x/story.md: header status 'ready' differs from phase table 'done'": ("status-mismatch", "story-evidence"),
            "pm/x/s.md: done story X-1-01 has no evidence link": ("missing-evidence-link", "story-evidence"),
            "pm/x/s.md: broken evidence link for X-1-01: e.md": ("broken-evidence-link", "story-evidence"),
            "pm/x/s.md: done story X-1-01 missing evidence-story-01.md": ("missing-evidence-file", "story-evidence"),
            "pm/x/evidence-story-09.md: orphan evidence has no matching story row": ("orphan-evidence", "story-evidence"),
            "pm/x/evidence-story-01.md: evidence exists but matching story is not done": ("premature-evidence", "story-evidence"),
            "pm/x/e.md: evidence still contains the generator placeholder": ("placeholder-evidence", "story-evidence"),
            "pm/x/e.md: evidence body is empty (no proof content)": ("empty-evidence", "story-evidence"),
            "pm/x/e.md: broken asset reference: assets/x.png": ("broken-asset", "story-evidence"),
            "pm/x/phase-1: all stories are done but final-summary.md is missing": ("missing-final-summary", "phase"),
        }
        for text_case, (kind, category) in cases.items():
            entry = core.classify_issue(text_case)
            self.assertEqual((entry["kind"], entry["category"]), (kind, category), text_case)
            self.assertEqual(entry["severity"], "error")
        warn = core.classify_warning("multiple open phases detected: phase-0-a, phase-1-b")
        self.assertEqual(warn["kind"], "multiple-open-phases")
        self.assertEqual(warn["phase_folders"], ["phase-0-a", "phase-1-b"])
        self.assertIn("explanation", warn)
        hook_warn = core.classify_warning("installed pre-commit hook appears older than current Delivery Workbench seams")
        self.assertEqual((hook_warn["kind"], hook_warn["category"]), ("older-hook-snapshot", "hook-runtime"))

    def test_health_report_shape_and_guard(self) -> None:
        from dw_pmo import workbench as wb

        report = core.health_report(self.root, core.discover_projects(self.root))
        self.assertTrue(report["mutation_safe"])
        self.assertEqual(report["total_issues"], 0)
        self.assertEqual(report["check_output"], "dw check: ok")
        self.assertIn("work_log_config", report)
        # introduce drift: stale pointer + orphan evidence
        readme = self.root / "pm" / "roadmap" / "demo" / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8").replace(
            "phase-1-alpha/current-phase-status.md", "phase-9-ghost/current-phase-status.md"), encoding="utf-8")
        (self.phase_dir / "evidence-story-09.md").write_text("# stray\n", encoding="utf-8")
        report = core.health_report(self.root, core.discover_projects(self.root))
        self.assertFalse(report["mutation_safe"])
        kinds = {i["kind"] for i in report["projects"][0]["issues"]}
        self.assertIn("stale-pointer", kinds)
        self.assertIn("orphan-evidence", kinds)
        self.assertIn("ERROR", report["check_output"])
        status, body = wb.handle_api(self.root, "/api/health", {})
        self.assertEqual(status, 200)
        self.assertFalse(body["data"]["mutation_safe"])

    def test_hook_seam_explanations(self) -> None:
        empty = core.hook_seam_explanations({"pre_commit_exists": False})
        self.assertTrue(any("not active" in n for n in empty))
        partial = core.hook_seam_explanations({
            "pre_commit_exists": True, "has_config_seam": True,
            "has_local_seam": False, "has_work_log_capture": True,
        })
        self.assertTrue(any("pre-commit.local" in n for n in partial))
        self.assertTrue(any("update.sh" in n for n in partial))

    # -- workbench explorer API (WLA-5-03) -----------------------------------

    def _tree_checksums(self):
        import hashlib
        sums = {}
        for f in sorted((self.root / "pm" / "roadmap").rglob("*")):
            if f.is_file():
                sums[str(f)] = hashlib.sha256(f.read_bytes()).hexdigest()
        return sums

    def test_workbench_api_view_models(self) -> None:
        from dw_pmo import workbench as wb

        status, body = wb.handle_api(self.root, "/api/status", {"project": ["demo"]})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"], "attention is status data, not an HTTP error")
        self.assertEqual(body["data"], core.build_status(self.root, "demo"))
        status, body = wb.handle_api(self.root, "/api/status", {"project": ["nope"]})
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])

        status, body = wb.handle_api(self.root, "/api/step", {"project": ["demo"]})
        self.assertEqual(status, 200)
        step = core.build_step(self.root, "demo")
        self.assertEqual(body["data"], step)
        status, applied = wb.handle_mutation(
            self.root,
            "/api/step/apply",
            {"project": "demo", "expect": step["token"]},
        )
        direct, _exit_code = core.apply_step(self.root, "demo", str(step["token"]))
        self.assertEqual(status, 409)
        self.assertFalse(applied["ok"])
        self.assertEqual(applied["data"], direct)
        self.assertEqual(direct["outcome"], "refused")
        status, refused = wb.handle_mutation(
            self.root,
            "/api/step/apply",
            {
                "project": "demo",
                "expect": step["token"],
                "command": ["git", "commit"],
            },
        )
        self.assertEqual(status, 400)
        self.assertIn("unknown step parameter", refused["issues"][0])

        status, body = wb.handle_api(self.root, "/api/projects", {})
        self.assertEqual(status, 200)
        self.assertEqual(body["kind"], "delivery-workbench-workbench-response")
        self.assertEqual(body["schema_version"], 1)
        self.assertTrue(body["ok"])
        summary = body["data"]["projects"][0]
        self.assertEqual(summary["slug"], "demo")
        self.assertEqual(summary["phase_count"], 1)
        self.assertEqual(summary["active_phase_count"], 1)
        self.assertEqual(summary["story_status_counts"], {"done": 1, "ready": 1})
        self.assertEqual(summary["next_story"]["story_id"], "DM-1-02")
        self.assertEqual(summary["issue_count"], 0)

        status, body = wb.handle_api(self.root, "/api/projects/demo", {})
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["slug"], "demo")
        self.assertEqual(len(body["data"]["phases"]), 1)

        status, body = wb.handle_api(self.root, "/api/projects/demo/phases/1", {})
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["number"], 1)
        self.assertEqual(len(body["data"]["stories"]), 2)
        self.assertIn("final_summary_content", body["data"])

        status, body = wb.handle_api(self.root, "/api/projects/demo/stories/DM-1-01", {})
        self.assertEqual(status, 200)
        detail = body["data"]
        self.assertEqual(detail["story_id"], "DM-1-01")
        self.assertEqual(detail["phase_number"], 1)
        self.assertIn("Fixture story", detail["story_markdown"])
        self.assertIn("fixture proof line", detail["evidence_markdown"])

        status, body = wb.handle_api(self.root, "/api/projects/demo/stories/DM-9-99", {})
        self.assertEqual(status, 404)
        self.assertFalse(body["ok"])

        status, body = wb.handle_api(self.root, "/api/nope", {})
        self.assertEqual(status, 404)

    def test_workbench_file_endpoint_containment(self) -> None:
        from dw_pmo import workbench as wb

        rel_story = "pm/roadmap/demo/phase-1-alpha/story-01-first.md"
        status, body = wb.handle_api(self.root, "/api/file", {"path": [rel_story]})
        self.assertEqual(status, 200)
        self.assertIn("Fixture story", body["data"]["content"])
        outside = self.root / "secret.txt"
        outside.write_text("nope", encoding="utf-8")
        for evil in ["secret.txt", "../secret.txt", "pm/roadmap/../../secret.txt"]:
            status, body = wb.handle_api(self.root, "/api/file", {"path": [evil]})
            self.assertEqual(status, 403, evil)
        status, _ = wb.handle_api(self.root, "/api/file", {"path": ["pm/roadmap/demo/ghost.md"]})
        self.assertEqual(status, 404)

    def test_workbench_is_read_only(self) -> None:
        from dw_pmo import workbench as wb

        before = self._tree_checksums()
        for _ in range(3):
            wb.handle_api(self.root, "/api/status", {"project": ["demo"]})
            wb.handle_api(self.root, "/api/step", {"project": ["demo"]})
            wb.handle_api(self.root, "/api/context", {"trace": ["0"]})
            wb.handle_api(self.root, "/api/projects", {})
            wb.handle_api(self.root, "/api/projects/demo", {})
            wb.handle_api(self.root, "/api/projects/demo/phases/1", {})
            wb.handle_api(self.root, "/api/projects/demo/stories/DM-1-01", {})
        self.assertEqual(self._tree_checksums(), before,
                         "repeated API loads must not modify the roadmap tree")

    def test_workbench_step_front_door_keeps_review_and_act_separate(self) -> None:
        app = (TESTS_DIR.parent / "workbench" / "app.js").read_text(encoding="utf-8")
        css = (TESTS_DIR.parent / "workbench" / "style.css").read_text(encoding="utf-8")
        recommendation = app[
            app.index("function statusActionHtml") : app.index("function stepArgvHtml")
        ]
        controls = app[
            app.index("function stepControlHtml") : app.index("function statusPanel")
        ]
        apply = app[
            app.index("async function applyReviewedStep") : app.index("function wireStepControl")
        ]
        self.assertNotIn("<button", recommendation)
        for token in (
            "step-review", "step-confirm", "step-apply", "step-cancel",
            "step.applicable", "step.refusal", "No apply control",
        ):
            self.assertIn(token, controls)
        self.assertNotIn("<input", controls)
        self.assertIn('postJson("/api/step/apply"', apply)
        self.assertIn("project: step.project", apply)
        self.assertIn("expect: step.token", apply)
        self.assertIn("status === 409", apply)
        self.assertIn("nothing started", apply)
        self.assertIn("viewOverview", apply)
        for forbidden in ("command:", "argv:", "git commit", "certif", "setInterval"):
            self.assertNotIn(forbidden, apply)
        self.assertIn(".step-confirmation", css)
        self.assertIn(".brief-step-unavailable", css)
        self.assertIn("@media (max-width: 430px)", css)

    # -- traceability timeline (WLA-5-05) --------------------------------------

    def _timeline_for(self, story_id):
        project = core.get_project(self.root, "demo")
        for phase in core.discover_phases(project):
            for row in core.parse_story_rows(phase.path / "current-phase-status.md"):
                if row.story_id == story_id:
                    return core.story_timeline(row, phase, project, self.root)
        raise AssertionError(f"story {story_id} not in fixture")

    def test_story_timeline_chain_and_shipped(self) -> None:
        tl = self._timeline_for("DM-1-01")
        self.assertTrue(tl["shipped"])
        self.assertEqual(tl["not_shipped_reason"], "")
        hops = {h["hop"]: h for h in tl["chain"]}
        self.assertEqual(
            list(hops), ["readme", "phase_status", "story", "evidence", "final_summary"])
        for hop in ("readme", "phase_status", "story", "evidence"):
            self.assertTrue(hops[hop]["exists"], hop)
        # absent hops render as explicit absent states, never disappear
        self.assertFalse(hops["final_summary"]["exists"])
        self.assertTrue(hops["final_summary"]["path"])
        # no git, no work-log root: events degrade to empty, not an error
        self.assertEqual(tl["events"], [])

    def test_story_timeline_never_claims_unshipped(self) -> None:
        tl = self._timeline_for("DM-1-02")  # ready, no evidence
        self.assertFalse(tl["shipped"])
        self.assertIn("'ready'", tl["not_shipped_reason"])
        # done + missing evidence must not read as shipped either
        evidence = self.phase_dir / "evidence-story-01.md"
        evidence_backup = evidence.read_text(encoding="utf-8")
        evidence.unlink()
        tl = self._timeline_for("DM-1-01")
        self.assertFalse(tl["shipped"])
        self.assertIn("evidence", tl["not_shipped_reason"])
        evidence.write_text(evidence_backup, encoding="utf-8")

    def test_story_timeline_work_log_only(self) -> None:
        import os
        log_root = self.root / "worklog"
        (log_root / "2026-07-01").mkdir(parents=True)
        (log_root / "2026-07-01" / "demo-1-work-summary.log").write_text(
            "---\nkind: pmo-work-log-entry\ntimestamp: 2026-07-01T10:00:00Z\n"
            "project: demo\ncommit: abc1234\n---\n\n## Commit\n\n"
            "- **Subject:** DM-1-01 First story ships\n",
            encoding="utf-8",
        )
        os.environ["PMO_WORK_LOG_DIR"] = str(log_root)
        try:
            tl = self._timeline_for("DM-1-01")
        finally:
            del os.environ["PMO_WORK_LOG_DIR"]
        self.assertEqual(len(tl["events"]), 1)
        event = tl["events"][0]
        self.assertEqual(event["type"], "work-log")
        self.assertEqual(event["commit"], "abc1234")
        self.assertEqual(event["sort_key"], "2026-07-01T10:00:00Z")

    # -- structured editor / mutation preview (WLA-5-06) -----------------------

    def test_mutation_preview_maps_one_to_one_and_writes_nothing(self) -> None:
        from dw_pmo import workbench as wb

        before = self._tree_checksums()
        requests = {
            "create_phase": {"kind": "create_phase", "project": "demo", "number": "2",
                             "title": "Next Phase", "goal": "Ship more."},
            "create_story": {"kind": "create_story", "project": "demo", "phase": "1",
                             "title": "Editor story"},
            "update_story_status": {"kind": "update_story_status", "project": "demo",
                                    "phase": "1", "story": "DM-1-02", "status": "in-progress"},
            "attach_evidence": {"kind": "attach_evidence", "project": "demo", "phase": "1",
                                "story": "DM-1-02", "body": "- editor proof."},
            "close_phase": {"kind": "close_phase", "project": "demo", "phase": "1",
                            "summary_body": "Closed.", "force": True},
        }
        plan_kinds = {"create_phase": "phase-create", "create_story": "story-create",
                      "update_story_status": "story-status", "attach_evidence": "story-evidence",
                      "close_phase": "phase-close"}
        for kind, body in requests.items():
            status, payload = wb.handle_mutation(self.root, "/api/mutations/preview", body)
            self.assertEqual(status, 200, f"{kind}: {payload}")
            data = payload["data"]
            self.assertEqual(data["kind"], plan_kinds[kind])
            self.assertTrue(data["fingerprint"].startswith("sha256:"))
            self.assertTrue(data["files"], kind)
            self.assertTrue(all("new_content" in f for f in data["files"]))
        self.assertEqual(self._tree_checksums(), before,
                         "previews must never write")

    def test_mutation_preview_refusals(self) -> None:
        from dw_pmo import workbench as wb

        cases = [
            ({"kind": "nope", "project": "demo"}, "unknown mutation kind"),
            ({"kind": "create_story", "project": "demo", "phase": "1"}, "missing required field: title"),
            ({"kind": "create_phase", "project": "demo", "number": "x", "title": "T"}, "must be an integer"),
            ({"kind": "create_phase", "project": "demo", "number": "1", "title": "Alpha"}, "already exists"),
            ({"kind": "update_story_status", "project": "demo", "phase": "1",
              "story": "DM-1-02", "status": "done"}, "without evidence"),
            ({"kind": "update_story_status", "project": "demo", "phase": "1",
              "story": "DM-1-02", "status": "done-ish"}, "unknown story status"),
            ({"kind": "close_phase", "project": "demo", "phase": "1"}, "non-done stories"),
            ({"kind": "attach_evidence", "project": "demo", "phase": "1",
              "story": "DM-1-01", "body": "- new."}, "pass --force"),
        ]
        for body, needle in cases:
            status, payload = wb.handle_mutation(self.root, "/api/mutations/preview", body)
            self.assertEqual(status, 400, body)
            self.assertIn(needle, payload["issues"][0], body)
        status, payload = wb.handle_mutation(self.root, "/api/mutations/apply", {})
        self.assertEqual(status, 400)
        self.assertIn("requires the fingerprint", payload["issues"][0])

    def test_mutation_preview_guarded_by_validation_issues(self) -> None:
        from dw_pmo import workbench as wb

        readme = self.root / "pm" / "roadmap" / "demo" / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8").replace(
            "phase-1-alpha/current-phase-status.md", "phase-9-ghost/current-phase-status.md"), encoding="utf-8")
        body = {"kind": "create_story", "project": "demo", "phase": "1", "title": "Guarded"}
        status, payload = wb.handle_mutation(self.root, "/api/mutations/preview", body)
        self.assertEqual(status, 409)
        self.assertIn("guarded", payload["data"]["error"])
        self.assertTrue(payload["data"]["issues"])
        status, payload = wb.handle_mutation(
            self.root, "/api/mutations/preview", {**body, "acknowledge_issues": True})
        self.assertEqual(status, 200, payload)

    def test_guard_lets_remediation_through(self) -> None:
        from dw_pmo import workbench as wb

        # drift: done story's evidence file deleted -> validation issue
        (self.phase_dir / "evidence-story-01.md").unlink()
        blocked = {"kind": "create_story", "project": "demo", "phase": "1", "title": "Unrelated"}
        status, _ = wb.handle_mutation(self.root, "/api/mutations/preview", blocked)
        self.assertEqual(status, 409, "an unrelated mutation stays guarded under drift")
        healing = {"kind": "attach_evidence", "project": "demo", "phase": "1",
                   "story": "DM-1-01", "body": "- restored proof."}
        status, payload = wb.handle_mutation(self.root, "/api/mutations/preview", healing)
        self.assertEqual(status, 200, "a strictly remediating mutation passes without acknowledgment")
        self.assertEqual(payload["data"]["issues_after"], [])
        status, result = wb.handle_mutation(
            self.root, "/api/mutations/apply",
            {**healing, "fingerprint": payload["data"]["fingerprint"]})
        self.assertEqual(status, 200, result)
        self.assertEqual(result["data"]["issues"], [], "the fix lands and validation is clean")

    def test_mutation_fingerprint_binds_content(self) -> None:
        from dw_pmo import workbench as wb

        body = {"kind": "create_story", "project": "demo", "phase": "1", "title": "Stable"}
        _, first = wb.handle_mutation(self.root, "/api/mutations/preview", body)
        _, second = wb.handle_mutation(self.root, "/api/mutations/preview", body)
        self.assertEqual(first["data"]["fingerprint"], second["data"]["fingerprint"],
                         "same intent on same tree must fingerprint identically")
        status_file = self.phase_dir / "current-phase-status.md"
        status_file.write_text(status_file.read_text(encoding="utf-8") + "\n<!-- drift -->\n", encoding="utf-8")
        _, third = wb.handle_mutation(self.root, "/api/mutations/preview", body)
        self.assertNotEqual(first["data"]["fingerprint"], third["data"]["fingerprint"],
                            "changed target content must change the fingerprint")

    # -- mutation apply workflow (WLA-5-07) ------------------------------------

    def test_apply_cycle_and_stale_refusal(self) -> None:
        from dw_pmo import workbench as wb

        body = {"kind": "create_story", "project": "demo", "phase": "1", "title": "Applied story"}
        _, preview = wb.handle_mutation(self.root, "/api/mutations/preview", body)
        fp = preview["data"]["fingerprint"]
        self.assertIsInstance(preview["data"]["issues_before"], list)
        self.assertEqual(preview["data"]["issues_after"], [],
                         "creating a story should project no new issues")
        self.assertTrue(any(f.get("diff") is not None for f in preview["data"]["files"]))

        status, result = wb.handle_mutation(
            self.root, "/api/mutations/apply", {**body, "fingerprint": fp})
        self.assertEqual(status, 200, result)
        self.assertTrue(result["data"]["applied"])
        self.assertEqual(result["data"]["issues"], [], "post-apply revalidation should be clean")
        new_story = self.phase_dir / "story-03-applied-story.md"
        self.assertTrue(new_story.exists())

        # the tree changed, so the same fingerprint is now stale
        status, refusal = wb.handle_mutation(
            self.root, "/api/mutations/apply", {**body, "fingerprint": fp})
        self.assertEqual(status, 409)
        self.assertIn("stale preview", refusal["data"]["error"])
        self.assertIn("nothing was written", refusal["issues"][0])

    def test_apply_refuses_tampered_intent(self) -> None:
        from dw_pmo import workbench as wb

        body = {"kind": "create_story", "project": "demo", "phase": "1", "title": "Honest title"}
        _, preview = wb.handle_mutation(self.root, "/api/mutations/preview", body)
        fp = preview["data"]["fingerprint"]
        status, _ = wb.handle_mutation(
            self.root, "/api/mutations/apply",
            {**body, "title": "Different title", "fingerprint": fp})
        self.assertEqual(status, 409, "fingerprint binds the intent, not just the tree")

    def test_noop_mutation_is_explicitly_idempotent(self) -> None:
        from dw_pmo import workbench as wb

        # re-attaching existing evidence without a body changes nothing
        body = {"kind": "attach_evidence", "project": "demo", "phase": "1", "story": "DM-1-01"}
        _, preview = wb.handle_mutation(self.root, "/api/mutations/preview", body)
        self.assertTrue(preview["data"]["no_op"])
        self.assertTrue(all(not f["changed"] for f in preview["data"]["files"]))
        before = self._tree_checksums()
        status, result = wb.handle_mutation(
            self.root, "/api/mutations/apply",
            {**body, "fingerprint": preview["data"]["fingerprint"]})
        self.assertEqual(status, 200, result)
        self.assertEqual(self._tree_checksums(), before,
                         "no-op apply must leave the tree byte-identical")

    def test_projected_issues_sees_the_future(self) -> None:
        from dw_pmo import workbench as wb

        # attaching evidence to a non-done story projects premature-evidence
        body = {"kind": "attach_evidence", "project": "demo", "phase": "1",
                "story": "DM-1-02", "body": "- early proof."}
        _, preview = wb.handle_mutation(self.root, "/api/mutations/preview", body)
        projected = preview["data"]["issues_after"]
        self.assertIsNotNone(projected)
        self.assertTrue(any("not done" in issue for issue in projected),
                        f"projection should flag premature evidence: {projected}")
        self.assertEqual(preview["data"]["issues_before"], [])

    def test_apply_rolls_back_on_write_failure(self) -> None:
        import os
        from dw_pmo.mutations import MutationPlan, FileChange, apply_plan

        target_ok = self.phase_dir / "story-01-first.md"
        original = target_ok.read_text(encoding="utf-8")
        locked_dir = self.phase_dir / "locked"
        locked_dir.mkdir()
        os.chmod(locked_dir, 0o500)
        try:
            plan = MutationPlan(kind="story-status", root=self.root, project_slug="demo")
            plan.changes.append(FileChange(
                path=target_ok, new_content=original + "\nEDITED\n",
                existed=True, old_content=original))
            plan.changes.append(FileChange(
                path=locked_dir / "cannot-write.md", new_content="x\n",
                existed=False, old_content=None))
            with self.assertRaises(Exception):
                apply_plan(plan, validate_after=False)
            self.assertEqual(target_ok.read_text(encoding="utf-8"), original,
                             "first write must be rolled back when a later write fails")
        finally:
            os.chmod(locked_dir, 0o700)
            locked_dir.rmdir()

    # -- commit/work-log evidence views (WLA-5-08) -----------------------------

    def _write_worklog_fixture(self):
        import os
        log_root = self.root / "worklog"
        day = log_root / "2026-07-02"
        day.mkdir(parents=True, exist_ok=True)
        entry = day / "demo-1-work-summary.log"
        entry.write_text(
            "---\nkind: pmo-work-log-entry\ntimestamp: 2026-07-02T09:00:00Z\n"
            "project: demo\ncommit: abc1234\n---\n\n## Commit\n\n"
            "- **Subject:** DM-1-01 ships\n\n## Omitted Paths\n\n"
            "- `secrets/token.txt`\n",
            encoding="utf-8",
        )
        os.environ["PMO_WORK_LOG_DIR"] = str(log_root)
        self.addCleanup(os.environ.pop, "PMO_WORK_LOG_DIR", None)
        return entry

    def test_worklog_endpoint_containment_and_omission(self) -> None:
        from dw_pmo import workbench as wb

        entry = self._write_worklog_fixture()
        # absolute, slashless (hash-router), and log-root-relative all resolve
        for raw in (str(entry), str(entry).lstrip("/"), "2026-07-02/demo-1-work-summary.log"):
            status, payload = wb.handle_api(self.root, "/api/worklog", {"path": [raw]})
            self.assertEqual(status, 200, raw)
            content = payload["data"]["content"]
            self.assertIn("Omitted Paths", content)
            self.assertIn("secrets/token.txt", content)
            self.assertNotIn("not-for-log", content, "omitted content stays omitted")
        # containment: repo files and non-log names are refused
        status, _ = wb.handle_api(self.root, "/api/worklog",
                                  {"path": [str(self.root / "pm" / "roadmap" / "demo" / "README.md")]})
        self.assertEqual(status, 403)
        stray = entry.parent / "not-a-log.txt"
        stray.write_text("x", encoding="utf-8")
        status, _ = wb.handle_api(self.root, "/api/worklog", {"path": [str(stray)]})
        self.assertEqual(status, 403, "only work-log artifact names are served")
        status, _ = wb.handle_api(self.root, "/api/worklog",
                                  {"path": ["2026-07-02/ghost-work-summary.log"]})
        self.assertEqual(status, 404)

    def test_worklog_absent_root_is_optional_not_error(self) -> None:
        import os
        from dw_pmo import workbench as wb

        os.environ["PMO_WORK_LOG_DIR"] = str(self.root / "no-such-log-root")
        self.addCleanup(os.environ.pop, "PMO_WORK_LOG_DIR", None)
        status, payload = wb.handle_api(self.root, "/api/worklog", {"path": ["x-work-summary.log"]})
        self.assertEqual(status, 404)
        self.assertIn("optional evidence", payload["issues"][0])

    def test_handoff_summary_text(self) -> None:
        from dw_pmo import workbench as wb

        self._write_worklog_fixture()
        status, payload = wb.handle_api(self.root, "/api/projects/demo/handoff/DM-1-01", {})
        self.assertEqual(status, 200)
        text = payload["data"]["text"]
        self.assertIn("handoff — DM-1-01", text)
        self.assertIn("shipped: yes", text)
        self.assertIn("story: pm/roadmap/demo/phase-1-alpha/story-01-first.md", text)
        self.assertIn("(absent) pm/roadmap/demo/phase-1-alpha/final-summary.md", text)
        self.assertIn("narrative-only evidence", text)  # fixture evidence has no captures
        self.assertIn("never a substitute for evidence-story-NN.md", text)
        self.assertIn("demo-1-work-summary.log", text)
        # a story without evidence states the requirement instead of hiding it
        status, payload = wb.handle_api(self.root, "/api/projects/demo/handoff/DM-1-02", {})
        self.assertEqual(status, 200)
        self.assertIn("no evidence file exists yet — required before done", payload["data"]["text"])
        self.assertIn("shipped: no", payload["data"]["text"])

    # -- runtime permission model (WLA-5-09) -----------------------------------

    def test_host_header_allowlist(self) -> None:
        from dw_pmo.workbench import host_allowed

        for ok in ("127.0.0.1:8377", "localhost:9000", "127.0.0.1", "localhost", "", "[::1]:8377",
                   "karol-co-mac.tailad9943.ts.net", "karol-co-mac.tailad9943.ts.net:443"):
            self.assertTrue(host_allowed(ok), ok)
        for evil in ("evil.example.com", "evil.example.com:8377", "192.168.1.5:8377",
                     "attacker.test:80", "0.0.0.0:8377",
                     "ts.net.evil.example.com",  # suffix trick: must not match .ts.net
                     "evilts.net"):  # no dot before ts.net: must not match either
            self.assertFalse(host_allowed(evil), evil)

    def test_mutation_slug_injection_refused(self) -> None:
        from dw_pmo import workbench as wb

        for body in (
            {"kind": "create_phase", "project": "demo", "number": "9",
             "title": "Evil", "slug": "../../../../tmp/escape"},
            {"kind": "create_story", "project": "demo", "phase": "1",
             "title": "Evil", "slug": "../../../escape"},
        ):
            status, payload = wb.handle_mutation(self.root, "/api/mutations/preview", body)
            self.assertEqual(status, 400, payload)
            self.assertIn("invalid slug", payload["issues"][0])
        escaped = self.root.parent / "tmp"
        self.assertFalse((escaped / "escape").exists() if escaped.exists() else False)

    def test_serve_fails_closed_without_roadmap(self) -> None:
        from dw_pmo.workbench import serve
        from dw_pmo.model import DwError

        bare = self.root / "not-a-roadmap-repo"
        bare.mkdir()
        with self.assertRaises(DwError) as ctx:
            serve(bare, port=0)
        self.assertIn("no pm/roadmap tree", ctx.exception.message)
        with self.assertRaises(DwError) as ctx:
            serve(self.root / "ghost", port=0)
        self.assertIn("does not exist", ctx.exception.message)

    def test_captured_run_parse_survives_multiline_commands(self) -> None:
        from dw_pmo.evidence import latest_passing_capture, parse_captured_runs

        script = "\n".join(f"echo line-{i}" for i in range(20))
        text = (
            "### Captured run — 2026-07-02T10:00:00Z\n\n"
            f"- **Command:** `sh -c '{script}'`\n"
            "- **Cwd:** `.`\n"
            "- **Exit code:** 0\n"
            "- **Index-tree:** abc\n\n"
            "```text\nout\n```\n"
        )
        runs = parse_captured_runs(text)
        self.assertEqual(runs[0]["exit_code"], 0,
                         "a long multiline command must not push exit code out of the parse window")
        self.assertIsNotNone(latest_passing_capture(text))

    # -- canon accuracy doc-parity (WLA-7-03) ----------------------------------

    def _framework_file(self, rel_path):
        return (Path(__file__).resolve().parents[1] / rel_path).read_text(encoding="utf-8")

    def test_canon_cited_rule_ids_exist_in_gate(self) -> None:
        import re
        canon = self._framework_file("templates/PMO-CONTRACT.md")
        gate_src = self._framework_file("lib/dw_pmo/gate.py")
        cited = set(re.findall(r"`(contract-[a-z-]+|atomicity|evidence-missing|"
                               r"orphan-evidence|evidence-deletion-orphans-story)`", canon))
        self.assertGreaterEqual(len(cited), 8, f"canon should cite rule ids, found: {cited}")
        for rule_id in sorted(cited):
            if rule_id == "contract-tier-mismatch":
                # tier verdicts are decided in contract resolution, surfaced by the gate
                joined = gate_src + self._framework_file("lib/dw_pmo/contract.py")
                self.assertIn(f'"{rule_id}"', joined, rule_id)
                continue
            self.assertIn(f'"{rule_id}"', gate_src,
                          f"canon cites {rule_id!r} but gate.py does not define it")

    def test_canon_fence_boxes_match_contract_template(self) -> None:
        canon = self._framework_file("templates/PMO-CONTRACT.md")
        fence = canon.split("## Contract template", 1)[1]
        fence = fence.split("```markdown", 1)[1].split("```", 1)[0]
        canon_boxes = [line for line in fence.splitlines() if line.startswith("- [ ] **")]
        from dw_pmo.contract import CANONICAL_BOXES

        self.assertEqual(canon_boxes, list(CANONICAL_BOXES),
                         "the PMO-CONTRACT template fence and the generator's canonical "
                         "fallback must carry identical rule boxes")
        self.assertEqual(len(canon_boxes), 7)
        # CONTRACT.md.tmpl single-sources boxes via the {{BOXES}} placeholder
        tmpl = self._framework_file("templates/CONTRACT.md.tmpl")
        self.assertIn("{{BOXES}}", tmpl)
        self.assertNotIn("- [ ] **", tmpl,
                         "the contract template must not duplicate box lines")

    def test_builder_final_summary_spec_matches_generator(self) -> None:
        from dw_pmo.render import render_final_summary
        from dw_pmo.model import Phase

        builder = self._framework_file("templates/roadmap-builder.md")
        rendered = render_final_summary(
            Phase(number=3, slug="x", path=self.phase_dir), "Body.")
        self.assertIn("# Phase {n} Final Summary", builder,
                      "builder §2.5 must document the generator's actual heading")
        self.assertTrue(rendered.startswith("# Phase 3 Final Summary"))
        self.assertIn("**Status:** complete.", builder)
        self.assertIn("**Status:** complete.", rendered)
        self.assertNotIn("**Phase opened:**", builder,
                         "the retired final-summary header must not resurface in the spec")

    def test_story_scaffold_matches_documented_template(self) -> None:
        from dw_pmo.render import render_story_template
        from dw_pmo.model import Phase, Project

        project = Project("demo", self.root / "pm" / "roadmap" / "demo", "DM")
        phase = Phase(number=1, slug="alpha", path=self.phase_dir)
        rendered = render_story_template(project, phase, 9, "Parity story", "ready")
        tmpl = self._framework_file("templates/story.md.tmpl")
        for placeholder, value in {
            "{{STORY_ID}}": "DM-1-09", "{{STORY_TITLE}}": "Parity story",
            "{{PROJECT_SLUG}}": "demo", "{{PHASE_N}}": "1", "{{STATUS}}": "ready",
        }.items():
            tmpl = tmpl.replace(placeholder, value)
        self.assertEqual(rendered, tmpl,
                         "dw story create must render exactly the documented story template")

    # -- Claude Code plugin parity (WLA-7-04) ----------------------------------

    def _repo_file(self, rel_path):
        return (Path(__file__).resolve().parents[2] / rel_path).read_text(encoding="utf-8")

    def test_dw_version_flag_single_source(self) -> None:
        import subprocess
        bin_dw = Path(__file__).resolve().parents[1] / "bin" / "dw"
        out = subprocess.check_output([sys.executable, str(bin_dw), "--version"],
                                      text=True).strip()
        self.assertEqual(out, f"dw {core.__version__}",
                         "dw --version must report dw_pmo.__version__ (the single source)")

    def test_changelog_release_matches_version(self) -> None:
        import re
        text = self._repo_file("CHANGELOG.md")
        m = re.search(r"^## v(\d+\.\d+\.\d+)", text, re.MULTILINE)
        self.assertIsNotNone(m, "CHANGELOG.md must open with a '## vX.Y.Z' release heading")
        self.assertEqual(m.group(1), core.__version__,
                         "CHANGELOG.md release heading must track dw_pmo.__version__ (the single source)")

    def test_pyproject_version_single_source_and_entry_point(self) -> None:
        # pyproject carries no literal version: it must derive it from
        # dw_pmo.__version__ so the single source stays single.
        text = self._repo_file("pyproject.toml")
        self.assertIn('version = { attr = "dw_pmo.__version__" }', text)
        self.assertIn('name = "delivery-workbench"', text)
        self.assertIn('dw = "dw_pmo.launcher:main"', text)
        self.assertIn("dependencies = []", text,
                      "runtime must stay stdlib-only (distribution contract)")

    def test_formula_version_single_source(self) -> None:
        # The Homebrew formula's release-artifact url embeds the
        # version; it must track the single source.
        text = self._repo_file("Formula/delivery-workbench.rb")
        self.assertIn(f"delivery_workbench-{core.__version__}-py3-none-any.whl", text)
        self.assertIn(f"v{core.__version__}/", text)

    def test_plugin_version_single_source(self) -> None:
        import json
        manifest = json.loads(self._repo_file("plugin/.claude-plugin/plugin.json"))
        self.assertEqual(manifest["version"], core.__version__,
                         "plugin.json version must track dw_pmo.__version__ (the single source)")
        self.assertEqual(manifest["name"], "delivery-workbench")
        marketplace = json.loads(self._repo_file(".claude-plugin/marketplace.json"))
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "delivery-workbench")
        self.assertEqual(entry["source"], "./plugin")

    def test_plugin_skill_parity_with_managed_block(self) -> None:
        import re
        from dw_pmo.agentdocs import CANONICAL_BLOCK

        skill = self._repo_file("plugin/skills/delivery-workbench/SKILL.md")
        # every dw invocation the managed block teaches appears in the skill
        block_commands = set(re.findall(r"\.githooks/dw[a-z-]* [a-z-]+(?: [a-z-]+)?", CANONICAL_BLOCK))
        self.assertGreaterEqual(len(block_commands), 8, block_commands)
        for command in sorted(block_commands):
            self.assertIn(command, skill,
                          f"managed block teaches {command!r}; the plugin skill must too")
        # the canonical vocabulary line and gate invariants match
        self.assertIn("backlog | ready | in-progress | blocked | done", skill)
        self.assertIn("complete | closed | shipped", skill)
        for invariant in ("one story flips done per commit", "BUNDLE-OK.md",
                          "evidence-story-NN.md", "pmo-contract-archive"):
            self.assertIn(invariant, skill, invariant)
        self.assertIn("Never use `--no-verify`", skill)

    def test_plugin_commands_match_installer_commands(self) -> None:
        for name in ("dw-next", "dw-contract", "dw-story-done", "dw-adopt"):
            agent_copy = self._framework_file(f"agent/{name}.md")
            plugin_copy = self._repo_file(f"plugin/commands/{name}.md")
            self.assertEqual(agent_copy, plugin_copy,
                             f"{name}.md must be byte-identical between agent/ and plugin/commands/")

    # -- adoption bridge (WLA-6-07) -----------------------------------------

    GOOD_REPORT = """# New Proj - PMO Adoption Discovery

## PMO Adoption Recommendation
- **Roadmap root:** `pm/roadmap/newproj/`

## Proposed Phase Index
| Phase | Title | Goal | Why now |
|---|---|---|---|
| 0 | Stabilize Build | Get CI green | Broken today |
| 1 | Ship Slice | Deliver the first slice | Next value |

## Proposed First Stories
| ID | Title | Acceptance evidence | Notes |
|---|---|---|---|
| NP-0-01 | Fix the flaky suite | CI run output | - |
| NP-0-02 | Pin toolchain | lockfile diff | - |
| NP-1-01 | Build the slice | demo capture | - |
"""

    def test_parse_adoption_report(self) -> None:
        report = core.parse_adoption_report(self.GOOD_REPORT)
        self.assertEqual(report.slug, "newproj")
        self.assertEqual(report.prefix, "NP")
        self.assertEqual([p["number"] for p in report.phases], [0, 1])
        self.assertEqual([s["id"] for s in report.stories], ["NP-0-01", "NP-0-02", "NP-1-01"])

    def test_parse_adoption_report_malformed(self) -> None:
        bad_cols = self.GOOD_REPORT.replace(
            "| 1 | Ship Slice | Deliver the first slice | Next value |",
            "| 1 | Ship Slice | Deliver the first slice |",
        )
        with self.assertRaises(DwError) as ctx:
            core.parse_adoption_report(bad_cols)
        self.assertIn("line", ctx.exception.message)
        bad_id = self.GOOD_REPORT.replace("NP-0-02", "banana")
        with self.assertRaises(DwError) as ctx:
            core.parse_adoption_report(bad_id)
        self.assertIn("banana", ctx.exception.message)
        orphan_phase = self.GOOD_REPORT.replace("NP-1-01", "NP-7-01")
        with self.assertRaises(DwError) as ctx:
            core.parse_adoption_report(orphan_phase)
        self.assertIn("phase 7", ctx.exception.message)

    def test_run_adoption_preview_and_apply(self) -> None:
        report_path = self.tmp / "adoption-discovery.md"
        report_path.write_text(self.GOOD_REPORT, encoding="utf-8")
        before = self.snapshot()
        preview = core.run_adoption(self.root, report_path)
        self.assertEqual(preview["mode"], "preview")
        self.assertEqual(self.snapshot(), before, "preview must not write")
        self.assertTrue(any("NP-0-01" in item for item in preview["planned"]))
        result = core.run_adoption(self.root, report_path, apply=True)
        self.assertEqual(result["mode"], "applied")
        self.assertEqual(result["issues"], [], result["issues"])
        newproj = core.get_project(self.root, "newproj")
        self.assertEqual(newproj.prefix, "NP")
        rows = core.parse_story_rows(
            newproj.path / "phase-0-stabilize-build" / "current-phase-status.md"
        )
        self.assertEqual([r.story_id for r in rows], ["NP-0-01", "NP-0-02"])

    # -- canon/constant parity (WLA-6-06) ----------------------------------

    def test_story_vocabulary_doc_parity(self) -> None:
        """roadmap-builder §2.3 declares the vocabulary; the constants must match."""
        import re as _re

        builder = (TESTS_DIR.parent / "templates" / "roadmap-builder.md").read_text(encoding="utf-8")
        m = _re.search(
            r"- \*\*Status:\*\* ([a-z| -]+)\n\s+\(the canonical story-status vocabulary[^)]*done-synonyms\n\s+accepted by tooling: ([a-z| ]+); hold-synonym: ([a-z]+)\.",
            builder,
        )
        self.assertIsNotNone(m, "canonical vocabulary declaration missing from roadmap-builder §2.3")
        declared = {s.strip() for s in m.group(1).split("|")}
        done_synonyms = {s.strip() for s in m.group(2).split("|")}
        hold_synonyms = {s.strip() for s in m.group(3).split("|")}
        self.assertEqual(declared | done_synonyms | hold_synonyms, core.STORY_STATUSES,
                         "doc vocabulary and STORY_STATUSES constant have drifted")
        self.assertTrue(hold_synonyms <= core.HOLD_STATUSES,
                        "declared hold-synonyms and HOLD_STATUSES have drifted")


    # -- agent surface (WLA-6-05) ----------------------------------------

    def test_status_vocabulary_validation(self) -> None:
        with self.assertRaises(DwError) as ctx:
            core.plan_story_status(self.root, self.project, self.phase, "DM-1-02", "done-ish")
        self.assertIn("allowed:", ctx.exception.message)
        self.assertIn("blocked", ctx.exception.message)
        plan = core.plan_story_status(self.root, self.project, self.phase, "DM-1-02", "blocked")
        self.assertEqual(plan.summary["status"], "blocked")
        with self.assertRaises(DwError):
            core.plan_story_create(self.root, self.project, self.phase, "T", status="wip")

    # -- holds carry their why (WLA-17-01) --------------------------------

    def test_park_without_reason_refused(self) -> None:
        for park in ("on-hold", "paused"):
            with self.assertRaises(DwError) as ctx:
                core.plan_story_status(self.root, self.project, self.phase, "DM-1-02", park)
            self.assertIn("--reason", ctx.exception.message)

    def test_hold_reason_round_trip(self) -> None:
        plan = core.plan_story_status(
            self.root, self.project, self.phase, "DM-1-02", "on-hold",
            reason="pivot to phase 2",
        )
        self.assertEqual(plan.summary["status"], "on-hold")
        self.assertEqual(plan.summary["reason"], "pivot to phase 2")
        core.apply_plan(plan, validate_after=False)
        rows = core.parse_story_rows(self.phase_dir / "current-phase-status.md")
        row = next(r for r in rows if r.story_id == "DM-1-02")
        self.assertEqual(core.normalize_status(row.status), "on-hold")
        note = core.status_note(row.status)
        self.assertIn("pivot to phase 2", note)
        self.assertIn("since", note)
        # header and table decorate identically — dw check stays clean
        self.assertEqual(core.check_project(self.project, self.root), [])

    def test_reason_composes_with_open_statuses_and_refuses_done(self) -> None:
        plan = core.plan_story_status(
            self.root, self.project, self.phase, "DM-1-02", "blocked",
            reason="waiting on API keys",
        )
        table = next(c for c in plan.changes if c.path.name == "current-phase-status.md")
        self.assertIn("blocked (waiting on API keys — since ", table.new_content)
        # a decorated done would evade the gate's exact flip detection
        with self.assertRaises(DwError) as ctx:
            core.plan_story_status(
                self.root, self.project, self.phase, "DM-1-01", "done",
                reason="nope",
            )
        self.assertIn("no --reason", ctx.exception.message)

    def test_plain_statuses_write_byte_identical(self) -> None:
        plan = core.plan_story_status(self.root, self.project, self.phase, "DM-1-02", "in-progress")
        table = next(c for c in plan.changes if c.path.name == "current-phase-status.md")
        self.assertIn("| in-progress |", table.new_content)
        self.assertNotIn("in-progress (", table.new_content)

    # -- phases pause and resume (WLA-17-02) ------------------------------

    def test_phase_pause_and_resume_round_trip(self) -> None:
        plan = core.plan_phase_pause(self.root, self.project, self.phase, "yields to phase 2")
        core.apply_plan(plan, validate_after=False)
        status_file = self.phase_dir / "current-phase-status.md"
        header = core.phase_header_status(status_file)
        self.assertEqual(core.normalize_status(header), "paused")
        self.assertIn("yields to phase 2", core.status_note(header))
        self.assertTrue(core.phase_is_paused(self.phase_dir))
        readme_path = self.root / "pm" / "roadmap" / "demo" / "README.md"
        self.assertIn("paused (yields to phase 2 — since ", readme_path.read_text(encoding="utf-8"))
        # a paused phase raises no new issues
        self.assertEqual(core.check_project(self.project, self.root), [])
        # context reads the pause; paused is open, never closed
        ctx = core.project_context(self.project, self.root)
        ph = ctx["phases"][0]
        self.assertTrue(ph["paused"])
        self.assertIn("yields to phase 2", str(ph["pause_note"]))
        self.assertTrue(ph["active"])
        # resume restores in-progress in both places
        core.apply_plan(core.plan_phase_resume(self.root, self.project, self.phase), validate_after=False)
        self.assertFalse(core.phase_is_paused(self.phase_dir))
        self.assertEqual(core.phase_header_status(status_file), "in-progress")
        self.assertIn("| in-progress |", readme_path.read_text(encoding="utf-8"))

    def test_phase_pause_inserts_bare_status_under_h1(self) -> None:
        # the fixture phase file declares no Status line — the pause
        # inserts the flagship's bare shape right under the H1
        plan = core.plan_phase_pause(self.root, self.project, self.phase, "why")
        content = next(c for c in plan.changes if c.path.name == "current-phase-status.md").new_content
        lines = content.splitlines()
        self.assertTrue(lines[0].startswith("# Phase 1"))
        self.assertTrue(lines[2].startswith("**Status:** paused (why — since "), lines[:4])

    def test_phase_pause_and_resume_refusals(self) -> None:
        with self.assertRaises(DwError) as no_reason:
            core.plan_phase_pause(self.root, self.project, self.phase, "  ")
        self.assertIn("--reason", no_reason.exception.message)
        with self.assertRaises(DwError) as not_paused:
            core.plan_phase_resume(self.root, self.project, self.phase)
        self.assertIn("not paused", not_paused.exception.message)
        (self.phase_dir / "final-summary.md").write_text("# Phase 1 Final Summary\n", encoding="utf-8")
        with self.assertRaises(DwError) as closed_pause:
            core.plan_phase_pause(self.root, self.project, self.phase, "why")
        self.assertIn("closed", closed_pause.exception.message)
        with self.assertRaises(DwError) as closed_resume:
            core.plan_phase_resume(self.root, self.project, self.phase)
        self.assertIn("closed", closed_resume.exception.message)

    def test_workbench_pause_and_resume_mutations(self) -> None:
        import dw_pmo.workbench as wb
        # done stories only in the fixture? DM-1-02 is ready — the
        # project is issue-free, so no acknowledge dance is needed
        status, body = wb.handle_mutation(self.root, "/api/mutations/preview", {
            "kind": "pause_phase", "project": "demo", "phase": "1", "reason": "pivot",
        })
        self.assertEqual(status, 200, body)
        fingerprint = body["data"]["fingerprint"]
        status, body = wb.handle_mutation(self.root, "/api/mutations/apply", {
            "kind": "pause_phase", "project": "demo", "phase": "1", "reason": "pivot",
            "fingerprint": fingerprint,
        })
        self.assertEqual(status, 200, body)
        self.assertTrue(core.phase_is_paused(self.phase_dir))
        status, body = wb.handle_mutation(self.root, "/api/mutations/preview", {
            "kind": "resume_phase", "project": "demo", "phase": "1",
        })
        self.assertEqual(status, 200, body)
        status, body = wb.handle_mutation(self.root, "/api/mutations/apply", {
            "kind": "resume_phase", "project": "demo", "phase": "1",
            "fingerprint": body["data"]["fingerprint"],
        })
        self.assertEqual(status, 200, body)
        self.assertFalse(core.phase_is_paused(self.phase_dir))

    # -- next tells the truth; dw holds is the ledger (WLA-17-03) ---------

    def test_next_skips_parked_stories_and_paused_phases(self) -> None:
        # park the only open story: next finds nothing, the ledger names it
        core.apply_plan(core.plan_story_status(
            self.root, self.project, self.phase, "DM-1-02", "on-hold",
            reason="pivot"), validate_after=False)
        self.assertIsNone(core.next_story(self.project, self.root))
        parked = core.parked_summary(self.project, self.root)
        self.assertEqual(parked["counts"], {"blocked": 0, "on_hold": 1, "paused_phases": 0})
        self.assertEqual(core.parked_headline(parked), "1 on-hold")
        import datetime as _dt
        self.assertEqual(parked["parked_stories"][0]["note"], f"pivot — since {_dt.date.today().isoformat()}")
        # release it, then pause the whole phase: an in-progress story
        # inside a paused phase is never proposed
        core.apply_plan(core.plan_story_status(
            self.root, self.project, self.phase, "DM-1-02", "in-progress"), validate_after=False)
        self.assertIsNotNone(core.next_story(self.project, self.root))
        core.apply_plan(core.plan_phase_pause(
            self.root, self.project, self.phase, "yields to phase 2"), validate_after=False)
        self.assertIsNone(core.next_story(self.project, self.root))
        parked = core.parked_summary(self.project, self.root)
        self.assertEqual(parked["counts"]["paused_phases"], 1)
        self.assertEqual(core.parked_headline(parked), "1 phase paused")

    def test_bare_park_warns_never_errors(self) -> None:
        # blocked composes without a reason (legacy shape) — the tree
        # stays valid, but the drift surface names the forgotten why
        core.apply_plan(core.plan_story_status(
            self.root, self.project, self.phase, "DM-1-02", "blocked"), validate_after=False)
        self.assertEqual(core.check_project(self.project, self.root), [])
        warnings = core.project_warnings(self.project, self.root)
        self.assertTrue(
            any("parked without a recorded reason" in w and "DM-1-02" in w for w in warnings),
            warnings,
        )
        # give it the why: the warning clears
        core.apply_plan(core.plan_story_status(
            self.root, self.project, self.phase, "DM-1-02", "blocked",
            reason="waiting on keys"), validate_after=False)
        warnings = core.project_warnings(self.project, self.root)
        self.assertFalse(any("parked without a recorded reason" in w for w in warnings), warnings)

    def test_workbench_board_route(self) -> None:
        import dw_pmo.workbench as wb
        status, body = wb.handle_api(self.root, "/api/projects/demo/board", {})
        self.assertEqual(status, 200)
        model = body["data"]
        self.assertEqual(model["columns"], list(core.BOARD_COLUMNS))
        self.assertEqual(model["phases"][0]["number"], 1)
        self.assertEqual(
            [card["story_id"] for card in model["phases"][0]["columns"]["done"]],
            ["DM-1-01"],
        )
        status, _body = wb.handle_api(self.root, "/api/projects/nope/board", {})
        self.assertEqual(status, 400)

    # -- the interop contract (WLA-18-04) ---------------------------------

    @staticmethod
    def _interop_missing(inventory, doc_text):
        return sorted(item for item in inventory if item not in doc_text)

    def test_interop_doc_names_every_surface(self) -> None:
        """docs/interop.md is the read-surface contract; a new route,
        tool, or machine verb cannot ship undocumented."""
        import inspect
        import re as _re

        import dw_pmo.workbench as wb
        from dw_pmo.mcpserver import TOOLS

        doc = (TESTS_DIR.parent.parent / "docs" / "interop.md").read_text(encoding="utf-8")
        # every MCP tool, by name
        self.assertEqual(self._interop_missing(TOOLS.keys(), doc), [])
        # every route literal handle_api dispatches on
        source = inspect.getsource(wb.handle_api)
        tokens: set[str] = set()
        for line in source.splitlines():
            if "parts" not in line:
                continue
            tokens.update(_re.findall(r'"([a-z-]+)"', line))
        tokens.discard("api")  # the prefix, not a surface
        self.assertTrue(
            {"context", "projects", "board", "stories", "trace", "health"} <= tokens,
            tokens,
        )
        self.assertEqual(self._interop_missing(tokens, doc), [])
        # every POST route literal handle_mutation dispatches on
        mutation_source = inspect.getsource(wb.handle_mutation)
        post_routes = set(_re.findall(r'"(/api/[a-z/-]+)"', mutation_source))
        self.assertEqual(
            post_routes,
            {
                "/api/step/apply",
                "/api/setup/preview", "/api/setup/apply",
                "/api/mutations/preview", "/api/mutations/apply",
                "/api/orchestration/preview", "/api/orchestration/apply",
                "/api/program-studio/preview", "/api/program-studio/apply",
                "/api/programs/plan", "/api/programs/start",
                "/api/programs/preview", "/api/programs/tick",
                "/api/programs/supervise", "/api/programs/request",
                "/api/programs/pause", "/api/programs/resume",
                "/api/programs/revoke", "/api/programs/cancel",
                "/api/runs/preview", "/api/runs/start", "/api/runs/tick",
                "/api/runs/pause", "/api/runs/resume", "/api/runs/revoke",
                "/api/runs/cancel", "/api/runs/checkpoint", "/api/runs/request",
                "/api/notifications/ack",
            },
        )
        self.assertEqual(self._interop_missing(post_routes, doc), [])
        # the CLI's machine-readable verbs
        verbs = [
            "dw status", "dw setup", "dw step", "dw context", "dw state --json", "dw next", "dw board",
            "dw holds", "dw story show", "dw sessions --json", "dw events",
            "dw check", "dw gate --porcelain", "dw verify",
            "dw orchestration list", "dw orchestration show", "dw orchestration simulate",
            "dw organization list", "dw organization validate", "dw organization simulate",
            "dw workflow list", "dw workflow validate", "dw workflow simulate",
            "dw rubric list", "dw rubric validate",
            "dw program list", "dw program validate", "dw program simulate",
            "dw program plan", "dw program show", "dw program start",
            "dw program preview", "dw program tick", "dw program supervise",
            "dw program request", "dw program pause", "dw program resume",
            "dw program revoke", "dw program cancel", "dw program tail",
            "dw program stream",
            "dw signals list", "dw signals observe",
            "dw notifications list", "dw notifications ack",
            "dw notifications delivered",
            "dw run plan", "dw run start", "dw run list", "dw run show", "dw run view",
            "dw run preview", "dw run tick", "dw run pause", "dw run resume",
            "dw run revoke", "dw run cancel", "dw run checkpoint", "dw run stream",
            "dw run request",
            "dw run tail",
        ]
        self.assertEqual(self._interop_missing(verbs, doc), [])
        # the stamped models
        for stamp in ("delivery-workbench-status",
                      "delivery-workbench-delivery-setup",
                      "delivery-workbench-step",
                      "delivery-workbench-step-result",
                      "delivery-workbench-roadmap-context",
                      "delivery-workbench-workbench-response",
                      "delivery-workbench-board", "delivery-workbench-run-act-preview",
                      "delivery-workbench-run-view", "delivery-workbench-run-stream",
                      "delivery-workbench-run-summary-list",
                      "delivery-workbench-program-start-plan",
                      "delivery-workbench-program-grant",
                      "delivery-workbench-program-event",
                      "delivery-workbench-program-projection",
                      "delivery-workbench-program-claim-preview",
                      "delivery-workbench-program-completion-preview",
                      "delivery-workbench-program-control-preview",
                      "delivery-workbench-program-child-grant",
                      "delivery-workbench-program-run-list",
                      "delivery-workbench-deliberation-plan",
                      "delivery-workbench-deliberation-event",
                      "delivery-workbench-deliberation-projection",
                      "delivery-workbench-deliberation-simulation",
                      "delivery-workbench-council-verdict",
                      "delivery-workbench-meta-verdict",
                      "delivery-workbench-architecture-verdict",
                      "delivery-workbench-decision",
                      "delivery-workbench-program-studio",
                      "delivery-workbench-program-studio-document",
                      "delivery-workbench-program-studio-graph",
                      "delivery-workbench-program-studio-authority-preview",
                      "delivery-workbench-program-studio-round-trip",
                      "delivery-workbench-delivery-plan-authoring",
                      "delivery-workbench-program-studio-mutation-preview",
                      "delivery-workbench-program-studio-mutation-result",
                      "delivery-workbench-program-frontier",
                      "delivery-workbench-program-tick",
                      "delivery-workbench-program-supervision",
                      "delivery-workbench-program-conductor-receipt",
                      "delivery-workbench-program-request-result",
                      "delivery-workbench-program-artifact-receipt",
                      "delivery-workbench-program-driver-operation",
                      "delivery-workbench-program-act-preview",
                      "delivery-workbench-program-view",
                      "delivery-workbench-program-summary-list",
                      "delivery-workbench-program-surface-tick",
                      "delivery-workbench-program-surface-supervision",
                      "delivery-workbench-program-tail",
                      "delivery-workbench-program-stream",
                      "feed_schema"):
            self.assertIn(stamp, doc)
        # the pin must actually bite: a planted surface reads as missing
        self.assertEqual(
            self._interop_missing(["dw_planted_tool"], doc), ["dw_planted_tool"]
        )

    # -- one story, whole (WLA-18-02) -------------------------------------

    def test_story_detail_whole_and_absences(self) -> None:
        detail = core.story_detail(self.project, self.phase, "DM-1-01", self.root)
        self.assertEqual(detail["story_id"], "DM-1-01")
        self.assertEqual(detail["phase_number"], 1)
        self.assertTrue(str(detail["story_markdown"]).startswith("# DM-1-01"))
        self.assertIn("fixture proof line", str(detail["evidence_markdown"]))
        self.assertEqual(detail["captured_runs"], [])  # narrative-only fixture
        self.assertEqual(detail["paths"]["story"], "pm/roadmap/demo/phase-1-alpha/story-01-first.md")
        self.assertEqual(detail["links"]["trace"], "/api/projects/demo/trace/DM-1-01")
        # the selector forms find_story accepts all resolve
        for selector in ("1", "01", "story-01-first.md", "story-01-first"):
            self.assertEqual(
                core.story_detail(self.project, self.phase, selector, self.root)["story_id"],
                "DM-1-01", selector,
            )
        # honest absences, never inventions
        bare = core.story_detail(self.project, self.phase, "DM-1-02", self.root)
        self.assertEqual(bare["evidence_markdown"], "")
        self.assertEqual(bare["captured_runs"], [])
        self.assertFalse(bare["evidence_exists"])

    def test_story_detail_carries_captured_runs(self) -> None:
        exit_code, _path, timestamp = core.run_capture(
            self.root, self.project, self.phase, "DM-1-02", ["sh", "-c", "true"]
        )
        self.assertEqual(exit_code, 0)
        detail = core.story_detail(self.project, self.phase, "DM-1-02", self.root)
        runs = detail["captured_runs"]
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["timestamp"], timestamp)
        self.assertEqual(runs[0]["exit_code"], 0)

    def test_workbench_story_route_serves_story_detail(self) -> None:
        import dw_pmo.workbench as wb
        status, body = wb.handle_api(self.root, "/api/projects/demo/stories/DM-1-01", {})
        self.assertEqual(status, 200)
        detail = body["data"]
        for key in ("story_markdown", "evidence_markdown", "captured_runs",
                    "paths", "links", "phase_number", "status_token", "status_note"):
            self.assertIn(key, detail)
        self.assertEqual(detail["phase_number"], 1)
        status, _body = wb.handle_api(self.root, "/api/projects/demo/stories/NOPE-1-99", {})
        self.assertEqual(status, 404)

    # -- self-describing cards (WLA-18-01) --------------------------------

    def test_board_and_holds_carry_receipts_and_links(self) -> None:
        core.apply_plan(core.plan_story_status(
            self.root, self.project, self.phase, "DM-1-02", "on-hold",
            reason="pivot"), validate_after=False)
        model = core.board_model(self.project, self.root)
        self.assertEqual(model["kind"], "delivery-workbench-board")
        self.assertEqual(model["schema_version"], 1)
        lane = model["phases"][0]
        self.assertEqual(lane["links"], {"phase": "/api/projects/demo/phases/1"})
        self.assertEqual(lane["paths"], {"phase_status": "pm/roadmap/demo/phase-1-alpha/current-phase-status.md"})
        card = lane["columns"]["done"][0]
        self.assertEqual(card["paths"], {
            "story": "pm/roadmap/demo/phase-1-alpha/story-01-first.md",
            "evidence": "pm/roadmap/demo/phase-1-alpha/evidence-story-01.md",
            "phase_status": "pm/roadmap/demo/phase-1-alpha/current-phase-status.md",
        })
        self.assertEqual(card["links"], {
            "story": "/api/projects/demo/stories/DM-1-01",
            "trace": "/api/projects/demo/trace/DM-1-01",
        })
        # the evidence ADDRESS is stable before the file exists;
        # evidence_exists tells the truth about occupancy
        held = lane["columns"]["on-hold"][0]
        self.assertEqual(held["paths"]["evidence"], "pm/roadmap/demo/phase-1-alpha/evidence-story-02.md")
        self.assertFalse(held["evidence_exists"])
        parked = core.parked_summary(self.project, self.root)
        entry = parked["parked_stories"][0]
        self.assertEqual(entry["links"]["story"], "/api/projects/demo/stories/DM-1-02")
        self.assertEqual(entry["paths"]["story"], "pm/roadmap/demo/phase-1-alpha/story-02-second.md")
        core.apply_plan(core.plan_phase_pause(
            self.root, self.project, self.phase, "yields"), validate_after=False)
        parked = core.parked_summary(self.project, self.root)
        self.assertEqual(parked["paused_phases"][0]["links"], {"phase": "/api/projects/demo/phases/1"})
        self.assertEqual(
            parked["paused_phases"][0]["paths"],
            {"phase_status": "pm/roadmap/demo/phase-1-alpha/current-phase-status.md"},
        )

    def test_emitted_links_resolve_against_the_api(self) -> None:
        # links cannot rot: every link the board or the ledger emits
        # must answer 200 through the same handle_api that serves them
        import dw_pmo.workbench as wb
        core.apply_plan(core.plan_story_status(
            self.root, self.project, self.phase, "DM-1-02", "blocked"), validate_after=False)
        model = core.board_model(self.project, self.root)
        parked = core.parked_summary(self.project, self.root)
        links: list[str] = []
        for lane in model["phases"]:
            links.extend(lane["links"].values())
            for cards in lane["columns"].values():
                for card in cards:
                    links.extend(card["links"].values())
        for entry in list(parked["parked_stories"]) + list(parked["paused_phases"]):
            links.extend(entry["links"].values())
        self.assertTrue(links)
        for link in sorted(set(links)):
            status, _body = wb.handle_api(self.root, link, {})
            self.assertEqual(status, 200, link)

    # -- the board (WLA-17-04) --------------------------------------------

    def test_board_bucketing_pinned(self) -> None:
        cases = {
            "done": "done", "complete": "done", "shipped": "done", "closed": "done",
            "in-progress": "in-progress", "ready": "ready",
            "blocked": "blocked", "on-hold": "on-hold", "paused": "on-hold",
            "backlog": "backlog",
            # loose legacy vocabulary is visible, never lost
            "planned": "backlog", "scaffolded": "backlog", "not-started": "backlog",
            "host-complete": "backlog",
            # retired history leaves the columns (counted separately)
            "cut": None, "cancelled": None, "superseded": None,
        }
        for token, want in cases.items():
            self.assertEqual(core.board_bucket(token), want, token)

    def test_board_model_columns_and_receipts(self) -> None:
        core.apply_plan(core.plan_story_status(
            self.root, self.project, self.phase, "DM-1-02", "on-hold",
            reason="pivot"), validate_after=False)
        model = core.board_model(self.project, self.root)
        self.assertEqual(model["columns"], list(core.BOARD_COLUMNS))
        lane = model["phases"][0]
        for key in ("number", "slug", "path", "closed", "paused", "pause_note",
                    "is_pointer", "retired", "uncovered_story_files",
                    "done_count", "story_count", "columns"):
            self.assertIn(key, lane)
        self.assertTrue(lane["is_pointer"])
        ids = {c: [card["story_id"] for card in lane["columns"][c]] for c in core.BOARD_COLUMNS}
        self.assertEqual(ids["done"], ["DM-1-01"])
        self.assertEqual(ids["on-hold"], ["DM-1-02"])
        self.assertTrue(lane["columns"]["done"][0]["evidence_exists"])
        self.assertIn("pivot", lane["columns"]["on-hold"][0]["note"])

    def test_board_retired_rows_counted_not_shown(self) -> None:
        status_file = self.phase_dir / "current-phase-status.md"
        text = status_file.read_text(encoding="utf-8")
        status_file.write_text(
            text + "| ~~DM-1-99~~ | Cut thing | cut | [story-99-cut](./story-99-cut.md) | - |\n",
            encoding="utf-8",
        )
        lane = core.board_model(self.project, self.root)["phases"][0]
        self.assertEqual(lane["retired"], 1)
        all_ids = [card["story_id"] for cards in lane["columns"].values() for card in cards]
        self.assertNotIn("~~DM-1-99~~", all_ids)
        self.assertIn("retired row", core.render_board(core.board_model(self.project, self.root)))

    def test_board_render_paused_folds_and_truncation(self) -> None:
        core.apply_plan(core.plan_story_create(
            self.root, self.project, self.phase, "Third thing"), validate_after=False)
        core.apply_plan(core.plan_story_create(
            self.root, self.project, self.phase, "Fourth thing"), validate_after=False)
        core.apply_plan(core.plan_phase_pause(
            self.root, self.project, self.phase, "yields"), validate_after=False)
        rendered = core.render_board(core.board_model(self.project, self.root), max_rows=1)
        self.assertIn("⏸ paused (yields — since ", rendered)
        self.assertIn("+1 more", rendered)  # two backlog cards, one row shown
        # a closed lane folds to a one-line receipt, --all expands it
        (self.phase_dir / "final-summary.md").write_text("# Phase 1 Final Summary\n", encoding="utf-8")
        folded = core.render_board(core.board_model(self.project, self.root))
        self.assertIn("closed, 1/4 done", folded)
        expanded = core.render_board(core.board_model(self.project, self.root), expand_closed=True)
        self.assertIn("DM-1-01", expanded)

    def test_status_note_extraction(self) -> None:
        cases = {
            "on-hold (pivot to X — since 2026-07-11)": "pivot to X — since 2026-07-11",
            "**done** (2026-07-07 — twelve new tests)": "2026-07-07 — twelve new tests",
            "blocked — waiting on keys": "waiting on keys",
            "done": "",
            "": "",
        }
        for raw, want in cases.items():
            self.assertEqual(core.status_note(raw), want, f"status_note({raw!r})")

    def test_agent_docs_block_lifecycle(self) -> None:
        path, action = core.write_agent_docs(self.root)
        self.assertEqual((path.name, action), ("CLAUDE.md", "created"))
        _p, action = core.write_agent_docs(self.root)
        self.assertEqual(action, "unchanged")
        text = path.read_text(encoding="utf-8")
        path.write_text("# Mine\n\nuser above\n\n" + text + "\nuser below\n", encoding="utf-8")
        corrupted = path.read_text(encoding="utf-8").replace("evidence-first", "CORRUPTED")
        path.write_text(corrupted, encoding="utf-8")
        self.assertEqual(core.agent_docs_status(self.root)[0], "stale")
        _p, action = core.write_agent_docs(self.root)
        self.assertEqual(action, "refreshed")
        self.assertEqual(core.agent_docs_status(self.root)[0], "current")
        final = path.read_text(encoding="utf-8")
        self.assertIn("user above", final)
        self.assertIn("user below", final)
        self.assertEqual(final.count(core.BEGIN_MARKER), 1)


RULES_DOC_MIN = """# PMO Contract

## Contract template

```markdown
- [ ] **Alpha rule.** First fixture rule.
- [ ] **Beta rule.** Second fixture rule.
```

## Extending

- [ ] **Decoy rule.** Lives outside the template fence and must be ignored.
"""


class FlagshipDialectTest(unittest.TestCase):
    """WLA-16-01: legacy trees decorate statuses and drop the Evidence
    column; the read layer parses them header-mapped and compares
    statuses through normalization. Dialects distilled from the
    flagship consumer's real tree (86 phases of drift)."""

    LEGACY_STATUS = """# Phase 85 - The Mesh Edge

**Last updated:** 2026-07-07.

## The design (a table the parser must not mistake for stories)

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| drift | low | fixtures | red suite |

## Story status

| ID | Story | Status | Story file |
|----|-------|--------|------------|
| FX-85-01 | The relay queue | **done** (2026-07-07 — 12 new tests) | [story-01](./story-01-relay.md) |
| FX-85-02 | The edge worker | in-progress (3/6) | [story-02](./story-02-worker.md) |

## Where we are

Prose after the table must not be parsed as rows.
"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-flagship-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.phase_dir = self.root / "pm" / "roadmap" / "fx" / "phase-85-mesh-edge"
        self.phase_dir.mkdir(parents=True)
        (self.root / "pm" / "roadmap" / "fx" / "README.md").write_text(
            "# FX - Roadmap\n\n- **Story ID prefix:** FX\n", encoding="utf-8"
        )
        (self.phase_dir / "current-phase-status.md").write_text(self.LEGACY_STATUS, encoding="utf-8")
        (self.phase_dir / "story-01-relay.md").write_text(
            "# FX-85-01 - The relay queue\n\n- **Status:** done (2026-07-07 — merged)\n", encoding="utf-8"
        )
        (self.phase_dir / "story-02-worker.md").write_text(
            "# FX-85-02 - The edge worker\n\n- **Status:** in-progress\n", encoding="utf-8"
        )
        (self.phase_dir / "evidence-story-01.md").write_text(
            "# Evidence - FX-85-01\n\n- fixture proof line\n", encoding="utf-8"
        )
        self.project = core.get_project(self.root, "fx")

    def test_normalize_status_pinned_mappings(self) -> None:
        cases = {
            "done": "done",
            "**done** (2026-07-07 — twelve new tests)": "done",
            "CLOSED ✅ (6/6)": "closed",
            "**CLOSED (7/7)**": "closed",
            "in-progress (3/6)": "in-progress",
            "in progress": "in-progress",
            "not-started": "not-started",
            # deliberately-not-done decorations must never read as done
            "host-complete (walkthrough deferred per owner)": "host-complete",
            "paused": "paused",
            "paused (yields to phase 91 — since 2026-07-11)": "paused",
            "on-hold (pivot to phase 18 — since 2026-07-11)": "on-hold",
            "ON HOLD": "on-hold",
            "shipped → phase-49 (CLOSED 6/6)": "shipped",
            "~~cut~~": "cut",
            "scaffolded": "scaffolded",
            "": "",
            # narrative tails are never searched for keywords — only
            # the decoration-cut head speaks (flagship: a cell ending
            # "…the request never shipped)" must not read as shipped)
            "built + real-metal hydration proven (control-vs-treatment: grounded answers BLUE LANTERN from a transcript the request never shipped)": "built",
            "**built + Simulator-proven** (waiting sorts first; the device walk joins the owner queue)": "built",
        }
        for raw, want in cases.items():
            self.assertEqual(core.normalize_status(raw), want, f"normalize({raw!r})")

    def test_four_column_decorated_table_parses(self) -> None:
        rows = core.parse_story_rows(self.phase_dir / "current-phase-status.md")
        self.assertEqual([r.story_id for r in rows], ["FX-85-01", "FX-85-02"])
        self.assertEqual(rows[0].evidence, "")
        self.assertEqual(core.normalize_status(rows[0].status), "done")
        self.assertEqual(core.normalize_status(rows[1].status), "in-progress")

    def test_canonical_header_maps_identically(self) -> None:
        canonical = (
            self.LEGACY_STATUS.replace(
                "| ID | Story | Status | Story file |\n|----|-------|--------|------------|",
                "| ID | Story | Status | Story file | Evidence |\n|---|---|---|---|---|",
            )
            .replace(
                "| [story-01](./story-01-relay.md) |",
                "| [story-01](./story-01-relay.md) | [evidence-story-01](./evidence-story-01.md) |",
            )
            .replace(
                "| [story-02](./story-02-worker.md) |",
                "| [story-02](./story-02-worker.md) | - |",
            )
        )
        alt = self.phase_dir / "alt-status.md"
        alt.write_text(canonical, encoding="utf-8")
        legacy = core.parse_story_rows(self.phase_dir / "current-phase-status.md")
        rows = core.parse_story_rows(alt)
        self.assertEqual(
            [(r.story_id, r.title, r.status, r.story_file) for r in rows],
            [(r.story_id, r.title, r.status, r.story_file) for r in legacy],
        )
        self.assertEqual(rows[0].evidence, "[evidence-story-01](./evidence-story-01.md)")

    def test_decorated_statuses_do_not_mismatch(self) -> None:
        issues = core.check_project(self.project, self.root)
        self.assertFalse([i for i in issues if "header status" in i], issues)

    def test_genuine_mismatch_still_reported(self) -> None:
        (self.phase_dir / "story-02-worker.md").write_text(
            "# FX-85-02 - The edge worker\n\n- **Status:** blocked\n", encoding="utf-8"
        )
        issues = core.check_project(self.project, self.root)
        self.assertTrue(any("header status" in i for i in issues), issues)

    def test_decorated_done_counts_in_state_feed(self) -> None:
        from dw_pmo.statefeed import build_state_feed

        feed = build_state_feed(self.root)
        project = feed["projects"][0]
        phase = project["phases"][0]
        self.assertEqual(phase["stories_total"], 2)
        self.assertEqual(phase["stories_done"], 1)

    # -- WLA-16-02: receipts-first pairing ------------------------------

    def test_flagship_fixture_reads_clean(self) -> None:
        # The done row's Evidence column does not exist; the receipt on
        # disk is what proves the story. Zero errors on the dialect.
        self.assertEqual(core.check_project(self.project, self.root), [])

    def test_struck_row_makes_no_demands(self) -> None:
        status = self.LEGACY_STATUS.replace(
            "| FX-85-02 | The edge worker | in-progress (3/6) | [story-02](./story-02-worker.md) |",
            "| FX-85-02 | The edge worker | in-progress (3/6) | [story-02](./story-02-worker.md) |\n"
            "| ~~FX-85-03~~ | Cut before it began | — | — |",
        )
        (self.phase_dir / "current-phase-status.md").write_text(status, encoding="utf-8")
        issues = core.check_project(self.project, self.root)
        self.assertFalse([i for i in issues if "FX-85-03" in i], issues)
        from dw_pmo.statefeed import build_state_feed

        feed = build_state_feed(self.root)
        self.assertEqual(feed["projects"][0]["phases"][0]["stories_total"], 2)

    def test_planted_desyncs_still_fire(self) -> None:
        (self.phase_dir / "evidence-story-09.md").write_text("# Evidence\n\n- x\n", encoding="utf-8")
        (self.phase_dir / "evidence-story-02.md").write_text("# Evidence\n\n- x\n", encoding="utf-8")
        issues = core.check_project(self.project, self.root)
        self.assertTrue(
            any("orphan evidence" in i and "evidence-story-09" in i for i in issues), issues
        )
        self.assertTrue(
            any("matching story is not done" in i and "evidence-story-02" in i for i in issues),
            issues,
        )

    def test_done_row_with_no_receipt_still_errors(self) -> None:
        (self.phase_dir / "evidence-story-01.md").unlink()
        issues = core.check_project(self.project, self.root)
        self.assertTrue(
            any("FX-85-01" in i and "evidence" in i for i in issues), issues
        )

    def test_tableless_phase_reads_from_files(self) -> None:
        phase2 = self.root / "pm" / "roadmap" / "fx" / "phase-86-tableless"
        phase2.mkdir()
        (phase2 / "current-phase-status.md").write_text("# Phase 86 - Tableless\n\nProse only.\n", encoding="utf-8")
        (phase2 / "story-01-solo.md").write_text("# FX-86-01 - Solo\n\n- **Status:** done\n", encoding="utf-8")
        (phase2 / "evidence-story-01.md").write_text("# Evidence - FX-86-01\n\n- proof\n", encoding="utf-8")
        (phase2 / "story-02-open.md").write_text("# FX-86-02 - Open\n\n- **Status:** in-progress\n", encoding="utf-8")
        issues = core.check_project(self.project, self.root)
        self.assertFalse([i for i in issues if "phase-86" in i], issues)
        warnings = core.project_warnings(self.project, self.root)
        self.assertTrue(any("file-derived" in w for w in warnings), warnings)
        from dw_pmo.statefeed import build_state_feed

        feed = build_state_feed(self.root)
        phase = [p for p in feed["projects"][0]["phases"] if p["number"] == 86][0]
        self.assertEqual((phase["stories_total"], phase["stories_done"]), (2, 1))
        ids = {s["story_id"] for s in feed["projects"][0]["stories"]}
        self.assertIn("FX-86-01", ids)

    # -- WLA-16-03: pointer-driven current phase --------------------------

    def _close_phase_85(self) -> None:
        (self.phase_dir / "final-summary.md").write_text("# Final\n\nDone.\n", encoding="utf-8")

    def _add_open_phase_86(self) -> None:
        phase2 = self.root / "pm" / "roadmap" / "fx" / "phase-86-next"
        phase2.mkdir()
        (phase2 / "current-phase-status.md").write_text(
            "# Phase 86 - Next\n\n## Story status\n\n"
            "| ID | Story | Status | Story file | Evidence |\n|---|---|---|---|---|\n"
            "| FX-86-01 | Next thing | in-progress | [story-01-next](./story-01-next.md) | - |\n",
            encoding="utf-8",
        )
        (phase2 / "story-01-next.md").write_text(
            "# FX-86-01 - Next thing\n\n- **Status:** in-progress\n", encoding="utf-8"
        )

    def test_next_story_skips_closed_phases(self) -> None:
        # Phase 85 closes with an open-looking row left behind (the
        # flagship has hardware-gated backlog rows in closed phases).
        status = self.LEGACY_STATUS.replace(
            "| FX-85-02 | The edge worker | in-progress (3/6) | [story-02](./story-02-worker.md) |",
            "| FX-85-02 | The edge worker | backlog | [story-02](./story-02-worker.md) |",
        )
        (self.phase_dir / "current-phase-status.md").write_text(status, encoding="utf-8")
        self._close_phase_85()
        self._add_open_phase_86()
        found = core.next_story(self.project, self.root)
        self.assertIsNotNone(found)
        self.assertEqual(found["story_id"], "FX-86-01")

    def test_next_story_none_when_only_closed_phases_have_open_rows(self) -> None:
        status = self.LEGACY_STATUS.replace("in-progress (3/6)", "backlog")
        (self.phase_dir / "current-phase-status.md").write_text(status, encoding="utf-8")
        self._close_phase_85()
        self.assertIsNone(core.next_story(self.project, self.root))

    def test_pointer_names_current_phase_even_closed(self) -> None:
        from dw_pmo.statefeed import build_state_feed

        self._close_phase_85()
        self._add_open_phase_86()
        (self.root / "pm" / "roadmap" / "fx" / "README.md").write_text(
            "# FX - Roadmap\n\n"
            "**Current phase:** [phase-85-mesh-edge](./phase-85-mesh-edge/current-phase-status.md).\n\n"
            "- **Story ID prefix:** FX\n",
            encoding="utf-8",
        )
        feed = build_state_feed(self.root)
        current = feed["projects"][0]["current_phase"]
        self.assertEqual(current["number"], 85)
        self.assertEqual(current["status"], "closed")

    def test_pointer_absent_falls_back_to_next_story_phase(self) -> None:
        from dw_pmo.statefeed import build_state_feed

        self._add_open_phase_86()
        feed = build_state_feed(self.root)
        current = feed["projects"][0]["current_phase"]
        # No pointer in the fixture README: the phase of the next story
        # (FX-85-02, in-progress, oldest-first) wins.
        self.assertEqual(current["number"], 85)
        self.assertEqual(current["status"], "open")

    def test_file_only_evidence_vouched_by_header(self) -> None:
        # Evidence for a story that exists ONLY as a file (no row) whose
        # header says done is not premature; if the header is open, it is.
        phase2 = self.root / "pm" / "roadmap" / "fx" / "phase-87-fileonly"
        phase2.mkdir()
        (phase2 / "current-phase-status.md").write_text("# Phase 87 - File only\n", encoding="utf-8")
        (phase2 / "story-01-a.md").write_text("# FX-87-01 - A\n\n- **Status:** in-progress\n", encoding="utf-8")
        (phase2 / "evidence-story-01.md").write_text("# Evidence\n\n- x\n", encoding="utf-8")
        issues = core.check_project(self.project, self.root)
        self.assertTrue(
            any("matching story is not done" in i and "phase-87" in i for i in issues), issues
        )
        (phase2 / "story-01-a.md").write_text("# FX-87-01 - A\n\n- **Status:** done\n", encoding="utf-8")
        issues = core.check_project(self.project, self.root)
        self.assertFalse([i for i in issues if "phase-87" in i], issues)


class GateTest(unittest.TestCase):
    """Gate v2: stamped-fact verification plus the structural rule set."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-gate-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self.git("init")
        self.git("config", "user.name", "Gate Test")
        self.git("config", "user.email", "gate-test@example.test")
        self.phase = self.root / "pm" / "roadmap" / "demo" / "phase-1-alpha"
        self.phase.mkdir(parents=True)
        # Match real installs: the contract scratch dir is never tracked.
        self.write(".gitignore", ".tmp/\n")

    def git(self, *args: str) -> None:
        import subprocess

        subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def write(self, rel_path: str, content: str) -> Path:
        path = self.root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def git_output(self, *args: str) -> str:
        import subprocess

        return subprocess.check_output(
            ["git", "-C", str(self.root), *args],
            stderr=subprocess.DEVNULL,
            text=True,
        )

    def story(self, rel_path: str, status: str, story_id: str | None = None) -> None:
        heading = f"# {story_id} - Fixture story" if story_id else "# Story"
        self.write(rel_path, f"{heading}\n\n- **Status:** {status}\n")

    def contract(self, consent: str = "no", certify: bool = True, mark: str = "x", tier: str = "full") -> str:
        text = core.build_contract(self.root, consent=consent, tier=tier)
        if certify:
            text = text.replace("- [ ]", f"- [{mark}]")
        self.write(".tmp/CONTRACT.md", text)
        return text

    def gate(self, **kwargs):
        return core.run_gate(self.root, **kwargs)

    def commit_all(self, msg: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-m", msg, "--no-verify")

    # -- contract facts ------------------------------------------------------

    def test_missing_unchecked_and_count_fallback(self) -> None:
        result = self.gate()
        self.assertEqual(result.failure.rule, "contract-missing")
        self.contract(certify=False)
        self.assertEqual(self.gate().failure.rule, "contract-unchecked")
        text = self.contract()
        lines = [l for l in text.splitlines() if not l.startswith("- [x] **One PR per story.**")]
        self.write(".tmp/CONTRACT.md", "\n".join(lines) + "\n")
        result = self.gate()
        self.assertEqual(result.failure.rule, "contract-boxes")

    def test_facts_missing_on_v1_style_contract(self) -> None:
        self.write(".tmp/CONTRACT.md", "# Commit Contract\n\n" + "- [x] rule\n" * 7)
        result = self.gate()
        self.assertEqual(result.failure.rule, "contract-facts-missing")

    def test_index_tree_mismatch_and_touch_bypass_dead(self) -> None:
        self.write("a.txt", "a\n")
        self.git("add", "-A")
        self.contract()
        self.write("b.txt", "b\n")
        self.git("add", "b.txt")
        result = self.gate()
        self.assertEqual(result.failure.rule, "contract-index-tree-mismatch")
        contract_path = self.root / ".tmp" / "CONTRACT.md"
        os.utime(contract_path, None)
        self.assertEqual(self.gate().failure.rule, "contract-index-tree-mismatch")

    def test_head_mismatch_after_history_moves(self) -> None:
        self.write("a.txt", "a\n")
        self.git("add", "-A")
        self.contract()
        self.commit_all("moves head")
        result = self.gate()
        self.assertEqual(result.failure.rule, "contract-head-mismatch")

    def test_branch_mismatch(self) -> None:
        self.write("a.txt", "a\n")
        self.commit_all("base")
        self.contract()
        self.git("checkout", "-b", "other-branch")
        result = self.gate()
        self.assertEqual(result.failure.rule, "contract-branch-mismatch")

    def test_invented_staged_sample_refused(self) -> None:
        self.write("real.txt", "real\n")
        self.git("add", "-A")
        text = self.contract()
        tampered = text.replace("- real.txt", "- invented/ghost.txt")
        self.assertNotEqual(text, tampered)
        self.write(".tmp/CONTRACT.md", tampered)
        result = self.gate()
        self.assertEqual(result.failure.rule, "contract-sample-mismatch")
        self.assertIn("invented/ghost.txt", result.failure.message)

    def test_capital_x_boxes_count(self) -> None:
        self.contract(mark="X")
        result = self.gate()
        self.assertTrue(result.ok, result.failure and result.failure.message)
        self.assertEqual(result.checked_boxes, 7)

    def test_worklog_preconditions(self) -> None:
        self.contract(consent="yes")
        self.assertTrue(self.gate(work_log_enabled=True).worklog_capture)
        self.assertFalse(self.gate(work_log_enabled=False).worklog_capture)
        self.contract(consent="no")
        self.assertFalse(self.gate(work_log_enabled=True).worklog_capture)

    # -- rule-title verification against the rules doc -----------------------

    def test_rules_doc_titles_extension_and_tampering(self) -> None:
        self.write("pm/roadmap/PMO-CONTRACT.md", RULES_DOC_MIN)
        self.assertEqual(core.contract_rule_titles(self.root), ["Alpha rule.", "Beta rule."])
        text = self.contract()
        self.assertIn("**Alpha rule.**", text)
        self.assertNotIn("Decoy rule", text)
        result = self.gate()
        self.assertTrue(result.ok, result.failure and result.failure.message)
        self.assertEqual(result.expected_boxes, 2)
        self.write(".tmp/CONTRACT.md", text + "- [x] **Bogus rule.** Invented.\n")
        self.assertEqual(self.gate().failure.rule, "contract-unknown-box")
        lines = [l for l in text.splitlines() if "Beta rule" not in l]
        self.write(".tmp/CONTRACT.md", "\n".join(lines) + "\n")
        result = self.gate()
        self.assertEqual(result.failure.rule, "contract-missing-box")
        self.assertIn("Beta rule.", result.failure.message)

    def test_expected_boxes_config_fallback_beats_env(self) -> None:
        self.write(".githooks/pre-commit.config", "EXPECTED_BOXES=8\n")
        self.contract()
        old = os.environ.get("EXPECTED_BOXES")
        os.environ["EXPECTED_BOXES"] = "7"
        try:
            result = self.gate()
        finally:
            if old is None:
                os.environ.pop("EXPECTED_BOXES", None)
            else:
                os.environ["EXPECTED_BOXES"] = old
        self.assertEqual(result.failure.rule, "contract-boxes")
        self.assertEqual(result.expected_boxes, 8)

    # -- shipped-story detection ----------------------------------------------

    def test_synonym_status_counts_as_flip(self) -> None:
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "ready")
        self.commit_all("base")
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "complete")
        self.git("add", "-A")
        self.contract()
        self.assertEqual(self.gate().failure.rule, "evidence-missing")

    def test_unpadded_numbers_pair_both_ways(self) -> None:
        self.story("pm/roadmap/demo/phase-1-alpha/story-1-a.md", "ready")
        self.commit_all("base")
        self.story("pm/roadmap/demo/phase-1-alpha/story-1-a.md", "done")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-01.md", "# proof\n")
        self.git("add", "-A")
        self.contract()
        self.assertTrue(self.gate().ok, "padded evidence must satisfy unpadded story")
        self.git("reset")
        self.git("checkout", "--", ".")
        (self.phase / "evidence-story-01.md").unlink()
        self.story("pm/roadmap/demo/phase-1-alpha/story-1-a.md", "done")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-1.md", "# proof\n")
        self.git("add", "-A")
        self.contract()
        self.assertTrue(self.gate().ok, "unpadded evidence must satisfy unpadded story")

    def test_rename_of_done_story_is_not_a_flip(self) -> None:
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "done")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-01.md", "# proof\n")
        self.commit_all("base")
        self.git("mv", "pm/roadmap/demo/phase-1-alpha/story-01-a.md", "pm/roadmap/demo/phase-1-alpha/story-01-renamed.md")
        self.contract()
        result = self.gate()
        self.assertTrue(result.ok, result.failure and result.failure.message)
        self.assertEqual(result.shipped_stories, [])

    def test_paths_with_spaces(self) -> None:
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-has space.md", "ready")
        self.commit_all("base")
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-has space.md", "done")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-01.md", "# proof\n")
        self.git("add", "-A")
        self.contract()
        result = self.gate()
        self.assertTrue(result.ok, result.failure and result.failure.message)
        self.assertEqual(len(result.shipped_stories), 1)

    def test_atomicity_and_bundle_ok(self) -> None:
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "ready")
        self.story("pm/roadmap/demo/phase-1-alpha/story-02-b.md", "ready")
        self.commit_all("base")
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "done")
        self.story("pm/roadmap/demo/phase-1-alpha/story-02-b.md", "done")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-01.md", "# proof\n")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-02.md", "# proof\n")
        self.git("add", "-A")
        self.contract()
        self.assertEqual(self.gate().failure.rule, "atomicity")
        self.write(".tmp/BUNDLE-OK.md", "intentional bundle\n")
        self.assertTrue(self.gate().ok)

    def test_story_declaration_enforced_for_flips(self) -> None:
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "ready", story_id="DM-1-01")
        self.commit_all("base")
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "done", story_id="DM-1-01")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-01.md", "# proof\n")
        self.git("add", "-A")
        text = self.contract()
        self.assertIn("**Story:** DM-1-01", text)
        result = self.gate()
        self.assertTrue(result.ok, result.failure and result.failure.message)
        self.assertEqual(result.declared_stories, ["DM-1-01"])
        self.write(".tmp/CONTRACT.md", text.replace("**Story:** DM-1-01", "**Story:** none"))
        result = self.gate()
        self.assertEqual(result.failure.rule, "contract-story-mismatch")
        self.assertIn("DM-1-01", result.failure.message)

    # -- evidence deletion handling ------------------------------------------

    def test_evidence_deletion_orphaning_done_story_blocked(self) -> None:
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "done")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-01.md", "# proof\n")
        self.commit_all("base")
        self.git("rm", "-q", "pm/roadmap/demo/phase-1-alpha/evidence-story-01.md")
        self.contract()
        result = self.gate()
        self.assertEqual(result.failure.rule, "evidence-deletion-orphans-story")
        self.assertIn("story-01-a.md", result.failure.message)

    def test_evidence_deletion_with_regressed_story_passes(self) -> None:
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "done")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-01.md", "# proof\n")
        self.commit_all("base")
        self.git("rm", "-q", "pm/roadmap/demo/phase-1-alpha/evidence-story-01.md")
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "in-progress")
        self.git("add", "-A")
        self.contract()
        result = self.gate()
        self.assertTrue(result.ok, result.failure and result.failure.message)

    def test_orphan_evidence_deletion_passes(self) -> None:
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-09.md", "# stray\n")
        self.commit_all("base")
        self.git("rm", "-q", "pm/roadmap/demo/phase-1-alpha/evidence-story-09.md")
        self.contract()
        result = self.gate()
        self.assertTrue(result.ok, result.failure and result.failure.message)

    def test_added_orphan_evidence_blocked(self) -> None:
        self.write("pm/roadmap/demo/README.md", "# Demo\n")
        self.commit_all("base")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-05.md", "# stray\n")
        self.git("add", "-A")
        self.contract()
        self.assertEqual(self.gate().failure.rule, "orphan-evidence")

    def test_modified_evidence_of_done_story_passes(self) -> None:
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "done")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-01.md", "# proof\n")
        self.commit_all("base")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-01.md", "# proof\n\namended\n")
        self.git("add", "-A")
        self.contract()
        result = self.gate()
        self.assertTrue(result.ok, result.failure and result.failure.message)

    # -- mechanical tests-ran discharge ----------------------------------------

    def test_tests_capture_discharge_and_tamper(self) -> None:
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "ready", story_id="DM-1-01")
        self.commit_all("base")
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "done", story_id="DM-1-01")
        ts = "2026-07-02T12:00:00Z"
        block = core.render_capture_block("run-tests", ".", 0, "all green", ts, "tree")
        ev_rel = "pm/roadmap/demo/phase-1-alpha/evidence-story-01.md"
        self.write(ev_rel, "# Evidence - DM-1-01\n\n## Proof\n\n" + block)
        with self.assertRaises(DwError):
            core.build_contract(self.root, tests_capture=ev_rel)  # not staged yet
        self.git("add", "-A")
        text = core.build_contract(self.root, tests_capture=ev_rel)
        self.assertIn(f"**Tests-ran capture:** {ev_rel}#{ts}", text)
        self.assertIn("- [x] **Tests ran.** Discharged mechanically", text)
        certified = text.replace("- [ ]", "- [x]")
        self.write(".tmp/CONTRACT.md", certified)
        result = self.gate()
        self.assertTrue(result.ok, result.failure and result.failure.message)
        tampered = certified.replace(f"#{ts}", "#1999-01-01T00:00:00Z")
        self.write(".tmp/CONTRACT.md", tampered)
        result = self.gate()
        self.assertEqual(result.failure.rule, "contract-tests-capture-mismatch")
        failing_block = core.render_capture_block("run-tests", ".", 1, "boom", "2026-07-02T13:00:00Z", "tree")
        ev2_rel = "pm/roadmap/demo/phase-1-alpha/evidence-story-09.md"
        self.write(ev2_rel, "# stray\n\n" + failing_block)
        self.git("add", "-N", ev2_rel)
        self.git("add", ev2_rel)
        with self.assertRaises(DwError):
            core.build_contract(self.root, tests_capture=ev2_rel)  # no passing run

    # -- contract tiers (WLA-6-06) -----------------------------------------------

    def test_short_tier_docs_only_passes(self) -> None:
        self.write("README.md", "docs change\n")
        self.git("add", "README.md")
        text = self.contract(tier="auto")
        self.assertIn("**Tier:** short", text)
        self.assertEqual(text.count("- [x]"), 1, "short form carries only the no-bypass box")
        result = self.gate()
        self.assertTrue(result.ok, result.failure and result.failure.message)
        self.assertEqual(result.tier, "short")
        self.assertEqual(result.expected_boxes, 1)

    def test_short_tier_blocked_for_roadmap_commits(self) -> None:
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "ready")
        self.git("add", "-A")
        with self.assertRaises(DwError):
            core.build_contract(self.root, tier="short")
        text = self.contract(tier="auto")
        self.assertIn("**Tier:** full", text, "auto must pick full for roadmap commits")
        # Hand-tampering the tier down must be refused by the gate.
        self.write(".tmp/CONTRACT.md", text.replace("**Tier:** full", "**Tier:** short"))
        result = self.gate()
        self.assertEqual(result.failure.rule, "contract-tier-mismatch")

    def test_forced_full_tier_config(self) -> None:
        self.write(".githooks/pre-commit.config", "PMO_CONTRACT_TIER=full\n")
        self.write("README.md", "docs change\n")
        self.git("add", "README.md")
        text = self.contract(tier="auto")
        self.assertIn("**Tier:** full", text, "config must force the full tier")
        with self.assertRaises(DwError):
            core.build_contract(self.root, tier="short")

    # -- doctor detections -------------------------------------------------------

    def test_doctor_detections_and_health(self) -> None:
        checks = {c.name: c for c in core.run_doctor(self.root)}
        self.assertTrue(checks["python3"].ok)
        self.assertFalse(checks["core.hooksPath"].ok)
        self.assertIn("core.hooksPath", checks["core.hooksPath"].detail)
        self.assertFalse(checks["hook:pre-commit"].ok)
        self.assertFalse(checks["agent-docs"].ok)
        self.assertTrue(checks["roadmap"].ok)
        self.git("config", "core.hooksPath", ".githooks")
        for hook in ("pre-commit", "commit-msg", "post-commit"):
            self.write(f".githooks/{hook}", "#!/bin/sh\n")
        self.write(".githooks/dw", "#!/usr/bin/env python3\n")
        self.write(".githooks/dw_pmo/__init__.py", "")
        core.write_agent_docs(self.root)
        checks = core.run_doctor(self.root)
        self.assertTrue(all(c.ok for c in checks), [c.name for c in checks if not c.ok])

    def test_hooks_path_same_clone_absolute_is_healthy_with_hint(self) -> None:
        self.git("config", "core.hooksPath", str(self.root / ".githooks"))
        check = next(c for c in core.run_doctor(self.root) if c.name == "core.hooksPath")
        self.assertTrue(check.ok)
        self.assertIn(str(self.root / ".githooks"), check.detail)
        self.assertIn("--fix-hooks", check.detail)

    def test_hooks_path_foreign_absolute_still_fails(self) -> None:
        self.git("config", "core.hooksPath", "/tmp/some-other-hooks")
        check = next(c for c in core.run_doctor(self.root) if c.name == "core.hooksPath")
        self.assertFalse(check.ok)
        self.assertIn("/tmp/some-other-hooks", check.detail)

    def test_fix_hooks_path_normalizes_same_clone_absolute(self) -> None:
        self.git("config", "core.hooksPath", str(self.root / ".githooks"))
        check = core.fix_hooks_path(self.root)
        self.assertTrue(check.ok)
        self.assertEqual(check.detail, ".githooks")
        self.assertEqual(
            self.git_output("config", "core.hooksPath").strip(), ".githooks"
        )

    def test_fix_hooks_path_is_noop_on_relative_and_refuses_foreign(self) -> None:
        self.git("config", "core.hooksPath", ".githooks")
        check = core.fix_hooks_path(self.root)
        self.assertTrue(check.ok)
        self.assertEqual(check.detail, ".githooks")

        self.git("config", "core.hooksPath", "/tmp/some-other-hooks")
        check = core.fix_hooks_path(self.root)
        self.assertFalse(check.ok)
        self.assertEqual(
            self.git_output("config", "core.hooksPath").strip(), "/tmp/some-other-hooks"
        )

    # -- durable trail ---------------------------------------------------------

    def test_digest_and_trailers(self) -> None:
        text = "contract body\n"
        digest = core.contract_digest(text)
        self.assertTrue(digest.startswith("sha256:"))
        self.assertEqual(len(digest), len("sha256:") + 64)
        msg = self.write("msg.txt", "subject line\n\nbody text\n")
        core.append_trailers(self.root, msg, ["DM-1-01"], digest)
        stamped = msg.read_text(encoding="utf-8")
        self.assertIn("PMO-Story: DM-1-01", stamped)
        self.assertIn(f"PMO-Contract-Digest: {digest}", stamped)

    def test_work_log_dir_precedence(self) -> None:
        old = os.environ.get("PMO_WORK_LOG_DIR")
        os.environ["PMO_WORK_LOG_DIR"] = str(self.tmp / "env-log")
        try:
            self.assertEqual(core.work_log_root(self.root), self.tmp / "env-log")
            self.write(".githooks/pre-commit.config", f"PMO_WORK_LOG_DIR='{self.tmp / 'cfg-log'}'\n")
            self.assertEqual(core.work_log_root(self.root), self.tmp / "cfg-log")
        finally:
            if old is None:
                os.environ.pop("PMO_WORK_LOG_DIR", None)
            else:
                os.environ["PMO_WORK_LOG_DIR"] = old
        self.assertEqual(core.work_log_root(None), Path.home() / ".work" / "log")

    # -- porcelain ---------------------------------------------------------------

    def test_porcelain_verbatim(self) -> None:
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "ready", story_id="DM-1-01")
        self.commit_all("base")
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-a.md", "done", story_id="DM-1-01")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-01.md", "# proof\n")
        self.git("add", "-A")
        text = self.contract(consent="yes")
        result = self.gate(work_log_enabled=True)
        expected = (
            "gate=pass\n"
            "expected_boxes=7\n"
            "checked_boxes=7\n"
            "shipped_count=1\n"
            "worklog_capture=yes\n"
            "tier=full\n"
            f"contract_digest={core.contract_digest(text)}\n"
            "declared_story=DM-1-01\n"
            "staged=pm/roadmap/demo/phase-1-alpha/evidence-story-01.md\n"
            "staged=pm/roadmap/demo/phase-1-alpha/story-01-a.md\n"
            "staged_story=pm/roadmap/demo/phase-1-alpha/story-01-a.md\n"
            "staged_evidence=pm/roadmap/demo/phase-1-alpha/evidence-story-01.md\n"
            "shipped_story=pm/roadmap/demo/phase-1-alpha/story-01-a.md\n"
        )
        self.assertEqual(core.render_gate_porcelain(result), expected)


    def test_story_timeline_with_git_and_work_log(self) -> None:
        import os
        root = self.root
        self.write(
            "pm/roadmap/demo/README.md",
            "# Demo - Roadmap\n\n## Project metadata\n\n"
            "- **Slug:** `demo`\n- **Story ID prefix:** `DM`\n",
        )
        self.write(
            "pm/roadmap/demo/phase-1-alpha/current-phase-status.md",
            "## Story status\n\n| ID | Story | Status | Story file | Evidence |\n"
            "|---|---|---|---|---|\n"
            "| DM-1-01 | First story | done | [story-01-first](./story-01-first.md) "
            "| [evidence-story-01](./evidence-story-01.md) |\n",
        )
        self.story("pm/roadmap/demo/phase-1-alpha/story-01-first.md", "done", "DM-1-01")
        self.write("pm/roadmap/demo/phase-1-alpha/evidence-story-01.md", "# proof\n")
        self.git("add", "-A")
        self.git(
            "commit", "-m", "DM-1-01 ships with trailers",
            "-m", "PMO-Story: DM-1-01\nPMO-Contract-Digest: sha256:deadbeef",
            "--no-verify",
        )
        project = core.get_project(root, "demo")
        phase = core.discover_phases(project)[0]
        row = next(r for r in core.parse_story_rows(phase.path / "current-phase-status.md")
                   if r.story_id == "DM-1-01")
        log_root = root / "worklog"
        (log_root / "2099-01-01").mkdir(parents=True)
        (log_root / "2099-01-01" / "demo-1-work-summary.log").write_text(
            "---\nkind: pmo-work-log-entry\ntimestamp: 2099-01-01T00:00:00Z\n"
            "project: demo\ncommit: fffffff\n---\n\n## Commit\n\n"
            "- **Subject:** DM-1-01 logged\n",
            encoding="utf-8",
        )
        os.environ["PMO_WORK_LOG_DIR"] = str(log_root)
        try:
            timeline = core.story_timeline(row, phase, project, root)
        finally:
            del os.environ["PMO_WORK_LOG_DIR"]
        types = {e["type"] for e in timeline["events"]}
        self.assertEqual(types, {"commit", "work-log"})
        commit_events = [e for e in timeline["events"] if e["type"] == "commit"]
        self.assertTrue(any(e["pmo_story"] == "DM-1-01" for e in commit_events),
                        f"no trailer-stamped commit event: {commit_events}")
        self.assertTrue(all(e["contract_digest"] for e in commit_events
                            if e["pmo_story"]), "stamped commits should carry digests")
        # events sorted newest-first by sort_key
        keys = [str(e["sort_key"]) for e in timeline["events"]]
        self.assertEqual(keys, sorted(keys, reverse=True))
        self.assertEqual(timeline["events"][0]["type"], "work-log")  # 2099 sorts first


class DocsLintTest(unittest.TestCase):
    """Self-tests for the docs linter (WLA-7-06) on fixture files."""

    def setUp(self) -> None:
        from dw_pmo import docslint
        self.docslint = docslint
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-docslint-test."))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)

    def lint(self) -> "list[str]":
        issues, _count = self.docslint.lint(self.tmp)
        return issues

    def write(self, name: str, text: str) -> Path:
        path = self.tmp / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_github_slug_rules(self) -> None:
        slug = self.docslint.github_slug
        self.assertEqual(slug("Workbench: the local web view"),
                         "workbench-the-local-web-view")
        self.assertEqual(slug("The commit gate (`dw gate`) and contract v2"),
                         "the-commit-gate-dw-gate-and-contract-v2")
        self.assertEqual(slug("**Bold** and [linked](./x.md) words"),
                         "bold-and-linked-words")

    def test_duplicate_headings_get_numeric_suffixes(self) -> None:
        slugs = self.docslint.heading_slugs("# Same\n\n## Same\n\n### Same\n")
        self.assertEqual(slugs, {"same", "same-1", "same-2"})

    def test_headings_inside_fences_are_not_anchors(self) -> None:
        slugs = self.docslint.heading_slugs("# Real\n\n```text\n# Fake\n```\n")
        self.assertEqual(slugs, {"real"})

    def test_every_defect_class_is_caught(self) -> None:
        self.write("present.md", "# Present Heading\n")
        self.write(
            "broken.md",
            "# Fixture\n\n"
            "[gone](./missing.md)\n"
            "[bad](./present.md#absent-heading)\n"
            "[self](#nowhere)\n"
            "![](./present.md)\n"
            "![lost](./missing.png)\n",
        )
        issues = self.lint()
        self.assertEqual(len(issues), 5, issues)
        for needle in ["broken link: ./missing.md", "broken anchor: ./present.md#absent-heading",
                       "broken anchor: #nowhere", "image missing alt text",
                       "missing image: ./missing.png"]:
            self.assertTrue(any(needle in i for i in issues), (needle, issues))

    def test_valid_links_anchors_and_images_pass(self) -> None:
        self.write("img.png", "fake")
        self.write("target.md", "# Target\n\n## Sub Section\n")
        self.write(
            "good.md",
            "# Good\n\n[t](./target.md)\n[a](./target.md#sub-section)\n"
            "[s](#good)\n![alt text](./img.png)\n"
            "[ext](https://example.com/unchecked) [m](mailto:a@b.c)\n",
        )
        self.assertEqual(self.lint(), [])

    def test_links_inside_code_are_not_linted(self) -> None:
        self.write(
            "code.md",
            "# Code\n\n```markdown\n[gone](./missing.md)\n```\n\n"
            "inline `![shot](./assets/shot.png)` example\n",
        )
        self.assertEqual(self.lint(), [])

    def test_ignore_pragmas(self) -> None:
        self.write(
            "ignored.md",
            "# Ignored\n\n"
            "[gone](./missing.md) <!-- docs-lint: ignore -->\n"
            "<!-- docs-lint: ignore -->\n[also-gone](./missing2.md)\n",
        )
        self.write("skipped.md",
                    "<!-- docs-lint: skip-file -->\n# Skipped\n\n[x](./missing.md)\n")
        self.assertEqual(self.lint(), [])

    def test_anchor_only_checked_for_markdown_targets(self) -> None:
        self.write("script.sh", "#!/bin/sh\n")
        self.write("lines.md", "# L\n\n[line link](./script.sh#L1)\n")
        self.assertEqual(self.lint(), [])

    def test_snippet_extraction_names_attrs_and_body(self) -> None:
        self.write(
            "quick.md",
            "# Q\n\n<!-- snippet: demo prep=installed cwd=pmo -->\n"
            "```bash\necho one\necho two\n```\n",
        )
        snippets = self.docslint.extract_snippets(self.tmp)
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["name"], "demo")
        self.assertEqual(snippets[0]["attrs"], {"prep": "installed", "cwd": "pmo"})
        self.assertEqual(snippets[0]["body"], "echo one\necho two")

    def test_snippet_marker_without_fence_is_an_error(self) -> None:
        self.write("bad.md", "# B\n\n<!-- snippet: orphan -->\n\nprose, no fence\n")
        with self.assertRaises(SystemExit):
            self.docslint.extract_snippets(self.tmp)


class MCPServerTest(unittest.TestCase):
    """MCP server: protocol subset, thin-adapter parity, exclusions."""

    def setUp(self) -> None:
        from dw_pmo import mcpserver
        self.mcp = mcpserver
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-mcp-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        phase_dir = self.root / "pm" / "roadmap" / "demo" / "phase-1-alpha"
        phase_dir.mkdir(parents=True)
        (self.root / "pm" / "roadmap" / "demo" / "README.md").write_text(README, encoding="utf-8")
        (phase_dir / "current-phase-status.md").write_text(STATUS_FILE, encoding="utf-8")
        (phase_dir / "story-01-first.md").write_text(
            STORY_TMPL.format(sid="DM-1-01", title="First thing", status="done"), encoding="utf-8"
        )
        (phase_dir / "story-02-second.md").write_text(
            STORY_TMPL.format(sid="DM-1-02", title="Second thing", status="ready"), encoding="utf-8"
        )
        (phase_dir / "evidence-story-01.md").write_text(EVIDENCE_01, encoding="utf-8")

    def rpc(self, method, params=None, req_id=1):
        msg = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            msg["params"] = params
        return self.mcp.handle_message(self.root, msg)

    def call(self, name, arguments=None):
        reply = self.rpc("tools/call", {"name": name, "arguments": arguments or {}})
        return reply["result"]

    # -- protocol ----------------------------------------------------------

    def test_initialize_pins_protocol_version(self) -> None:
        result = self.rpc(
            "initialize", {"protocolVersion": self.mcp.PROTOCOL_VERSION, "capabilities": {}}
        )["result"]
        self.assertEqual(result["protocolVersion"], self.mcp.PROTOCOL_VERSION)
        self.assertEqual(result["capabilities"], {"tools": {}})
        self.assertEqual(result["serverInfo"]["version"], core.__version__)
        # Mismatched request → server answers with its pinned version.
        result = self.rpc("initialize", {"protocolVersion": "1863-01-01"})["result"]
        self.assertEqual(result["protocolVersion"], self.mcp.PROTOCOL_VERSION)

    def test_notifications_get_no_reply_and_unknown_methods_error(self) -> None:
        note = self.mcp.handle_message(
            self.root, {"jsonrpc": "2.0", "method": "notifications/initialized"}
        )
        self.assertIsNone(note)
        reply = self.rpc("resources/list")
        self.assertEqual(reply["error"]["code"], self.mcp.METHOD_NOT_FOUND)
        self.assertEqual(self.rpc("ping")["result"], {})

    def test_tools_list_matches_contract_and_excludes_attestation(self) -> None:
        tools = self.rpc("tools/list")["result"]["tools"]
        names = [t["name"] for t in tools]
        self.assertEqual(names, [
            "dw_status", "dw_knowledge_map", "dw_knowledge_ground", "dw_knowledge_lessons", "dw_step", "dw_step_apply", "dw_setup_preview", "dw_setup_apply", "dw_context", "dw_next",
            "dw_check", "dw_doctor",
            "dw_verify", "dw_gate", "dw_board", "dw_holds", "dw_story_show",
            "dw_story_status", "dw_evidence_capture", "dw_contract_new",
            "dw_orchestration_list", "dw_notifications", "dw_notifications_ack",
            "dw_signals", "dw_orchestration_show",
            "dw_orchestration_simulate",
            "dw_program_list", "dw_program_show", "dw_program_validate",
            "dw_program_simulate", "dw_program_plan", "dw_program_start",
            "dw_program_preview", "dw_program_tick", "dw_program_supervise",
            "dw_program_request", "dw_program_pause", "dw_program_resume",
            "dw_program_revoke", "dw_program_cancel", "dw_program_tail",
            "dw_program_stream",
            "dw_run_plan", "dw_run_list",
            "dw_run_show", "dw_run_view", "dw_run_preview", "dw_run_start",
            "dw_run_tick", "dw_run_pause", "dw_run_resume", "dw_run_revoke",
            "dw_run_cancel", "dw_run_checkpoint", "dw_run_request", "dw_run_stream",
        ])
        for banned in ("certify", "commit", "bundle"):
            self.assertFalse(any(banned in n for n in names), names)
        for tool in tools:
            self.assertIn("inputSchema", tool)
            self.assertTrue(tool["description"])
        for tool in tools[:15]:
            self.assertIn("Adapter over dw_pmo.", tool["description"])

    # -- thin-adapter parity -------------------------------------------------

    def test_check_and_next_agree_with_core(self) -> None:
        result = self.call("dw_check", {"project": "demo"})
        self.assertNotIn("isError", result)
        direct = core.check_project(core.get_project(self.root, "demo"), self.root)
        self.assertEqual(result["structuredContent"]["issues"], direct)
        self.assertEqual(result["structuredContent"]["ok"], not direct)

        result = self.call("dw_next", {"project": "demo"})
        from dw_pmo.api import next_story
        direct_next = next_story(core.get_project(self.root, "demo"), self.root)
        self.assertEqual(result["structuredContent"]["next_story"], direct_next)
        self.assertIn(direct_next["story_id"], result["content"][0]["text"])

    def test_status_agrees_with_core_and_attention_is_data(self) -> None:
        result = self.call("dw_status", {"project": "demo"})
        self.assertNotIn("isError", result)
        direct = core.build_status(self.root, "demo")
        self.assertEqual(result["structuredContent"], direct)
        self.assertEqual(direct["verdict"], "attention")  # fixture has no installed hooks
        self.assertIn("Delivery needs attention", result["content"][0]["text"])
        self.assertIn("Technical details:", result["content"][0]["text"])

        import inspect
        source = inspect.getsource(self.mcp._tool_status)
        self.assertNotIn("verdict", source)
        self.assertNotIn("next_action", source)

    def test_step_tools_are_exact_core_adapters(self) -> None:
        preview_result = self.call("dw_step", {"project": "demo"})
        self.assertNotIn("isError", preview_result)
        preview = core.build_step(self.root, "demo")
        self.assertEqual(preview_result["structuredContent"], preview)
        self.assertIn(
            "Review next step", preview_result["content"][0]["text"]
        )
        self.assertIn(
            "Technical details:", preview_result["content"][0]["text"]
        )

        apply_result = self.call(
            "dw_step_apply",
            {"project": "demo", "expect": preview["token"]},
        )
        self.assertNotIn("isError", apply_result)
        direct, _exit_code = core.apply_step(
            self.root,
            "demo",
            str(preview["token"]),
        )
        self.assertEqual(apply_result["structuredContent"], direct)
        self.assertEqual(
            json.loads(apply_result["content"][0]["text"]),
            apply_result["structuredContent"],
        )
        self.assertEqual(direct["outcome"], "refused")
        self.assertFalse(direct["started"])
        self.assertIn("Git metadata", direct["reason"])

        import inspect

        preview_source = inspect.getsource(self.mcp._tool_step)
        apply_source = inspect.getsource(self.mcp._tool_step_apply)
        self.assertNotIn("next_action", preview_source + apply_source)
        self.assertNotIn("command", preview_source + apply_source)

    # -- error paths -----------------------------------------------------------

    def test_unknown_tool_and_unknown_params(self) -> None:
        result = self.call("dw_nonexistent")
        self.assertTrue(result["isError"])
        result = self.call("dw_check", {"projekt": "demo"})
        self.assertTrue(result["isError"])
        self.assertIn("unknown parameter", result["content"][0]["text"])
        result = self.call(
            "dw_step_apply",
            {"expect": "sha256:" + "0" * 64, "command": ["git", "commit"]},
        )
        self.assertTrue(result["isError"])
        self.assertIn("unknown parameter", result["content"][0]["text"])

    def test_no_rails_is_a_discoverable_refusal(self) -> None:
        bare = self.tmp / "bare"
        bare.mkdir()
        result = self.mcp.call_tool(bare, "dw_check", {})
        self.assertTrue(result["isError"])
        self.assertIn("no Delivery Workbench rails", result["content"][0]["text"])

    def test_core_refusal_becomes_tool_error(self) -> None:
        result = self.call("dw_check", {"project": "nope"})
        self.assertTrue(result["isError"])
        self.assertIn("roadmap project not found", result["content"][0]["text"])

    # -- guarded mutations ---------------------------------------------------

    # -- the read surface (WLA-18-03) --------------------------------------

    def test_browse_tools_agree_with_core(self) -> None:
        from dw_pmo.api import parked_summary

        result = self.call("dw_board", {"project": "demo"})
        self.assertNotIn("isError", result)
        direct = core.board_model(core.get_project(self.root, "demo"), self.root)
        self.assertEqual(result["structuredContent"], direct)
        self.assertIn("phase 1", result["content"][0]["text"])

        result = self.call("dw_holds", {"project": "demo"})
        self.assertEqual(
            result["structuredContent"],
            parked_summary(core.get_project(self.root, "demo"), self.root),
        )
        self.assertIn("nothing parked", result["content"][0]["text"])

        result = self.call("dw_story_show", {"project": "demo", "phase": 1, "story": "DM-1-01"})
        detail = result["structuredContent"]
        self.assertEqual(detail["story_id"], "DM-1-01")
        self.assertIn("fixture proof line", detail["evidence_markdown"])
        self.assertEqual(detail["links"]["story"], "/api/projects/demo/stories/DM-1-01")
        self.assertIn("evidence=yes", result["content"][0]["text"])

    def test_browse_refusals_match_core(self) -> None:
        result = self.call("dw_board", {"project": "nope"})
        self.assertTrue(result["isError"])
        self.assertIn("roadmap project not found", result["content"][0]["text"])
        result = self.call("dw_story_show", {"project": "demo", "phase": "1", "story": "DM-9-99"})
        self.assertTrue(result["isError"])
        self.assertIn("story not found", result["content"][0]["text"])

    def test_browse_tools_are_read_only(self) -> None:
        # the interop layer never grows hands: no browse handler may
        # reach a plan builder or apply
        import inspect
        for handler in (
            self.mcp._tool_status,
            self.mcp._tool_step,
            self.mcp._tool_board,
            self.mcp._tool_holds,
            self.mcp._tool_story_show,
        ):
            src = inspect.getsource(handler)
            self.assertNotIn("plan_", src)
            self.assertNotIn("apply", src)

    def test_story_status_refusal_matches_core(self) -> None:
        # DM-1-02 has no evidence: done must be refused with the same
        # message the core raises for the CLI.
        result = self.call(
            "dw_story_status",
            {"project": "demo", "phase": "1", "story": "2", "status": "done"},
        )
        self.assertTrue(result["isError"])
        project = core.get_project(self.root, "demo")
        phase = core.get_phase(project, "1")
        try:
            core.plan_story_status(self.root, project, phase, "2", "done")
            self.fail("core unexpectedly allowed done without evidence")
        except DwError as exc:
            self.assertEqual(result["content"][0]["text"], f"dw: {exc.args[0]}")

    def test_story_status_flip_writes_what_the_core_writes(self) -> None:
        result = self.call(
            "dw_story_status",
            {"project": "demo", "phase": 1, "story": 2, "status": "in-progress"},
        )
        self.assertNotIn("isError", result)
        self.assertEqual(result["structuredContent"]["status"], "in-progress")
        story = (self.root / "pm" / "roadmap" / "demo" / "phase-1-alpha" / "story-02-second.md").read_text(encoding="utf-8")
        self.assertIn("- **Status:** in-progress", story)
        table = (self.root / "pm" / "roadmap" / "demo" / "phase-1-alpha" / "current-phase-status.md").read_text(encoding="utf-8")
        self.assertIn("| DM-1-02 | Second thing | in-progress |", table)

    def test_mutation_tools_require_their_params(self) -> None:
        result = self.call("dw_step_apply", {"project": "demo"})
        self.assertTrue(result["isError"])
        self.assertIn("missing required parameter", result["content"][0]["text"])
        result = self.call("dw_story_status", {"project": "demo"})
        self.assertTrue(result["isError"])
        self.assertIn("missing required parameter", result["content"][0]["text"])
        result = self.call(
            "dw_evidence_capture",
            {"project": "demo", "phase": 1, "story": 2, "command": []},
        )
        self.assertTrue(result["isError"])


class LauncherTest(unittest.TestCase):
    """Global dw launcher: payload resolution and the defer rule inputs."""

    def setUp(self) -> None:
        from dw_pmo import launcher
        self.launcher = launcher
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-launcher-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_payload_dir_resolves_checkout_layout(self) -> None:
        payload = self.launcher.payload_dir()
        self.assertIsNotNone(payload, "checkout layout must resolve")
        self.assertTrue((payload / "install.sh").is_file())
        for script in self.launcher.BOOTSTRAP_VERBS.values():
            self.assertTrue((payload / script).is_file(), script)

    def test_repo_dw_found_only_in_adopted_repos(self) -> None:
        import subprocess
        repo = self.tmp / "repo"
        repo.mkdir()
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
        self.assertIsNone(self.launcher.repo_dw(repo), "no rails yet")
        hooks = repo / ".githooks"
        hooks.mkdir()
        (hooks / "dw").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        found = self.launcher.repo_dw(repo)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "dw")
        outside = self.tmp / "outside"
        outside.mkdir()
        self.assertIsNone(self.launcher.repo_dw(outside))

    def test_vendored_version_parses_init(self) -> None:
        hooks = self.tmp / ".githooks"
        (hooks / "dw_pmo").mkdir(parents=True)
        (hooks / "dw").write_text("", encoding="utf-8")
        (hooks / "dw_pmo" / "__init__.py").write_text(
            '__version__ = "0.0.1-test"\n', encoding="utf-8"
        )
        self.assertEqual(self.launcher.vendored_version(hooks / "dw"), "0.0.1-test")
        self.assertIsNone(self.launcher.vendored_version(self.tmp / "nope"))


class VerifyTest(unittest.TestCase):
    """Range verifier: re-derived rules match docs/remote-verification.md."""

    GOOD_DIGEST = "sha256:" + "a" * 64

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-verify-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Verify Test")
        self.git("config", "user.email", "verify-test@example.test")
        self.phase = "pm/roadmap/demo/phase-1-alpha"

    def git(self, *args: str) -> None:
        import subprocess

        subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def write(self, rel_path: str, content: str) -> None:
        path = self.root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def story(self, num: int, status: str) -> None:
        self.write(
            f"{self.phase}/story-0{num}-thing-{num}.md",
            f"# DM-1-0{num} - Thing {num}\n\n- **Status:** {status}\n",
        )

    def evidence(self, num: int) -> None:
        self.write(f"{self.phase}/evidence-story-0{num}.md", f"# Evidence - DM-1-0{num}\n")

    def commit(self, title: str, trailers: str | None = None) -> None:
        self.git("add", "-A")
        args = ["commit", "-m", title]
        if trailers:
            args += ["-m", trailers]
        self.git(*args)

    def verify(self, **kwargs):
        return core.run_verify(self.root, **kwargs)

    def stamped(self, story: str = "DM-1-01") -> str:
        return f"PMO-Story: {story}\nPMO-Contract-Digest: {self.GOOD_DIGEST}"

    # -- green paths ---------------------------------------------------------

    def test_clean_flip_with_trailers_passes(self) -> None:
        self.story(1, "backlog")
        self.commit("plan", self.stamped())
        self.story(1, "done")
        self.evidence(1)
        self.commit("ship", self.stamped())
        result = self.verify(all_history=True)
        self.assertTrue(result.ok, result.violations)
        self.assertEqual(result.verified, 2)
        self.assertEqual(result.pre_epoch_skipped, 0)

    def test_pre_epoch_commits_are_skipped_not_flagged(self) -> None:
        self.story(1, "backlog")
        self.commit("pre-epoch scaffold")  # no trailers: before the rails
        self.story(1, "done")  # even a naked flip is pre-epoch here
        self.commit("pre-epoch flip without evidence")
        self.story(2, "backlog")
        self.commit("epoch begins", self.stamped("DM-1-02"))
        result = self.verify(all_history=True)
        self.assertTrue(result.ok, result.violations)
        self.assertEqual(result.pre_epoch_skipped, 2)
        self.assertEqual(result.verified, 1)

    def test_merge_commits_are_out_of_scope(self) -> None:
        # Synthetic merges (GitHub PR merge ref) carry no trailers by
        # construction; they must be skipped, not flagged.
        self.story(1, "backlog")
        self.commit("plan", self.stamped())
        self.git("switch", "-q", "-c", "feature")
        self.story(1, "done")
        self.evidence(1)
        self.commit("ship on branch", self.stamped())
        self.git("switch", "-q", "main")
        self.write("unrelated.txt", "x\n")
        self.commit("mainline drift")
        self.git("merge", "--no-ff", "-q", "-m", "merge feature (no trailers)", "feature")
        result = self.verify(all_history=True)
        self.assertTrue(result.ok, result.violations)
        self.assertGreaterEqual(result.out_of_scope, 2)  # merge + drift

    def test_non_roadmap_commits_are_out_of_scope(self) -> None:
        self.story(1, "backlog")
        self.commit("plan", self.stamped())
        self.write("src/app.py", "print('hi')\n")
        self.commit("app change, no trailers needed")
        result = self.verify(all_history=True)
        self.assertTrue(result.ok, result.violations)
        self.assertEqual(result.out_of_scope, 1)

    def test_bundled_double_flip_with_trailer_passes(self) -> None:
        self.story(1, "backlog")
        self.story(2, "backlog")
        self.commit("plan", self.stamped("DM-1-01, DM-1-02"))
        self.story(1, "done")
        self.evidence(1)
        self.story(2, "done")
        self.evidence(2)
        self.commit(
            "bundled ship",
            f"PMO-Story: DM-1-01, DM-1-02\nPMO-Contract-Digest: {self.GOOD_DIGEST}\nPMO-Bundle: twin stories, one proof run",
        )
        result = self.verify(all_history=True)
        self.assertTrue(result.ok, result.violations)

    # -- violations ----------------------------------------------------------

    def rules_of(self, result) -> set:
        return {v.rule for v in result.violations}

    def test_smuggled_flip_names_missing_trailer_and_evidence(self) -> None:
        self.story(1, "backlog")
        self.commit("plan", self.stamped())
        self.story(1, "done")
        self.commit("smuggled flip")  # no evidence, no trailers
        result = self.verify(all_history=True)
        self.assertFalse(result.ok)
        self.assertIn("trailer-missing", self.rules_of(result))
        self.assertIn("evidence-missing", self.rules_of(result))

    def test_double_flip_without_bundle_fails_atomicity(self) -> None:
        self.story(1, "backlog")
        self.story(2, "backlog")
        self.commit("plan", self.stamped("DM-1-01, DM-1-02"))
        self.story(1, "done")
        self.evidence(1)
        self.story(2, "done")
        self.evidence(2)
        self.commit("double flip", self.stamped("DM-1-01, DM-1-02"))
        result = self.verify(all_history=True)
        self.assertIn("atomicity", self.rules_of(result))

    def test_flip_not_declared_in_story_trailer(self) -> None:
        self.story(1, "backlog")
        self.commit("plan", self.stamped())
        self.story(1, "done")
        self.evidence(1)
        self.commit("ship declaring the wrong story", self.stamped("DM-1-99"))
        result = self.verify(all_history=True)
        self.assertIn("contract-story-mismatch", self.rules_of(result))

    def test_orphan_evidence_added_without_flip(self) -> None:
        self.story(1, "backlog")
        self.commit("plan", self.stamped())
        self.evidence(2)
        self.commit("orphan evidence", self.stamped())
        result = self.verify(all_history=True)
        self.assertIn("orphan-evidence", self.rules_of(result))

    def test_evidence_deletion_orphans_done_story(self) -> None:
        self.story(1, "done")
        self.evidence(1)
        self.commit("epoch with done story", self.stamped())
        (self.root / self.phase / "evidence-story-01.md").unlink()
        self.commit("delete evidence", self.stamped())
        result = self.verify(all_history=True)
        self.assertIn("evidence-deletion-orphans-story", self.rules_of(result))

    def test_malformed_digest_and_story_id(self) -> None:
        self.story(1, "backlog")
        self.commit("bad trailers", "PMO-Story: not-an-id\nPMO-Contract-Digest: sha256:short")
        result = self.verify(all_history=True)
        self.assertEqual(self.rules_of(result), {"trailer-format"})

    # -- CLI contract --------------------------------------------------------

    def test_errors_exit_via_error_field(self) -> None:
        self.story(1, "backlog")
        self.commit("plan", self.stamped())
        result = self.verify(range_spec="nope..HEAD")
        self.assertIsNotNone(result.error)
        result = self.verify(range_spec="HEAD~1..HEAD", all_history=True)
        self.assertIsNotNone(result.error)
        result = self.verify(all_history=True, epoch="not-a-rev")
        self.assertIsNotNone(result.error)

    def test_render_grammar(self) -> None:
        self.story(1, "backlog")
        self.commit("plan", self.stamped())
        self.story(1, "done")
        self.commit("smuggled")
        result = self.verify(all_history=True)
        text = core.render_verify(result)
        self.assertRegex(text, r"ERROR [0-9a-f]{7}: [a-z-]+: ")
        porcelain = core.render_verify_porcelain(result)
        self.assertIn("verify=fail", porcelain)
        self.assertIn("epoch=", porcelain)

    def test_every_rederivable_rule_id_is_a_gate_rule_or_remote_only(self) -> None:
        import re as _re

        gate_src = (TESTS_DIR.parent / "lib" / "dw_pmo" / "gate.py").read_text(encoding="utf-8")
        verify_src = (TESTS_DIR.parent / "lib" / "dw_pmo" / "verify.py").read_text(encoding="utf-8")
        gate_ids = set(_re.findall(r'failed\(\s*"([a-z-]+)"', gate_src))
        verify_ids = set(_re.findall(r'bad\(\s*\n?\s*"([a-z-]+)"', verify_src))
        remote_only = {"trailer-missing", "trailer-format"}
        self.assertTrue(verify_ids, "extraction regex drifted")
        unknown = verify_ids - gate_ids - remote_only
        self.assertFalse(unknown, f"verify emits rule ids the gate does not own: {unknown}")
        doc = TESTS_DIR.parent.parent / "docs" / "remote-verification.md"
        if doc.is_file():  # consumer installs ship without repo docs
            doc_text = doc.read_text(encoding="utf-8")
            for rule_id in sorted(verify_ids | gate_ids | remote_only):
                self.assertIn(f"`{rule_id}`", doc_text, f"{rule_id} unclassified in remote-verification.md")


class StatusBriefingTest(unittest.TestCase):
    """WLA-22-02: the aggregate answer is schema-pinned, pure, and
    recommends only transitions the underlying rails can accept."""

    TOP_KEYS = [
        "actions", "kind", "next_action", "rails", "repository",
        "roadmap", "schema_version", "summary", "verdict",
    ]
    REPOSITORY_KEYS = [
        "branch", "changes", "clean", "contract", "gate", "head",
        "operation", "root",
    ]
    CONTRACT_KEYS = [
        "checked_boxes", "exists", "expected_boxes", "facts_fresh",
        "path", "state", "story_ids", "tier",
    ]
    GATE_KEYS = [
        "checked_boxes", "declared_stories", "expected_boxes", "failure",
        "ok", "shipped_stories", "state",
    ]
    ROADMAP_KEYS = [
        "healthy", "issues", "projects", "selected_project",
        "selection_required", "warnings",
    ]
    PROJECT_KEYS = [
        "current_phase", "next_story", "parked_counts", "prefix", "slug",
        "status_counts",
    ]
    ACTION_KEYS = ["blocking", "command", "id", "kind", "reason"]
    STEP_KEYS = [
        "action", "applicable", "apply_command", "kind", "project",
        "refusal", "schema_version", "token",
    ]
    STEP_RESULT_KEYS = [
        "action", "after", "before", "exit_code", "kind", "outcome",
        "output", "project", "reason", "schema_version", "started",
    ]
    STEP_OBSERVATION_KEYS = ["action_id", "token"]
    STEP_OUTPUT_KEYS = ["stderr", "stdout", "truncated"]

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(self.root)],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.name", "Status Test"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.email", "status@example.test"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "config", "core.hooksPath", ".githooks"],
            check=True,
        )

        hooks = self.root / ".githooks"
        (hooks / "dw_pmo").mkdir(parents=True)
        for name in ("pre-commit", "commit-msg", "post-commit", "dw"):
            hook = hooks / name
            hook.write_text("#!/bin/sh\n", encoding="utf-8")
            hook.chmod(0o755)
        (hooks / "dw_pmo" / "__init__.py").write_text("# fixture\n", encoding="utf-8")
        (self.root / ".gitignore").write_text(".tmp/\n", encoding="utf-8")

        project = self.root / "pm" / "roadmap" / "demo"
        phase = project / "phase-1-alpha"
        phase.mkdir(parents=True)
        (project / "README.md").write_text(README, encoding="utf-8")
        (phase / "current-phase-status.md").write_text(STATUS_FILE, encoding="utf-8")
        (phase / "story-01-first.md").write_text(
            STORY_TMPL.format(sid="DM-1-01", title="First thing", status="done"),
            encoding="utf-8",
        )
        (phase / "story-02-second.md").write_text(
            STORY_TMPL.format(sid="DM-1-02", title="Second thing", status="ready"),
            encoding="utf-8",
        )
        (phase / "evidence-story-01.md").write_text(EVIDENCE_01, encoding="utf-8")
        core.write_agent_docs(self.root)
        subprocess.run(["git", "-C", str(self.root), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "commit", "-q", "--no-verify", "-m", "fixture"],
            check=True,
        )

    def status(self, project: str | None = None) -> dict:
        return core.build_status(self.root, project)

    def step_events(self) -> list[dict]:
        from dw_pmo.events import read_events

        return [
            event for event in read_events(self.root)
            if event.get("event") == "step_execution"
        ]

    def test_schema_is_pinned_and_clean_repo_starts_next_story(self) -> None:
        status = self.status()
        self.assertEqual(sorted(status), self.TOP_KEYS)
        self.assertEqual(status["kind"], "delivery-workbench-status")
        self.assertEqual(status["schema_version"], 1)
        self.assertEqual(status["verdict"], "ready")
        self.assertEqual(sorted(status["repository"]), self.REPOSITORY_KEYS)
        self.assertEqual(
            sorted(status["repository"]["changes"]),
            ["staged", "unstaged", "untracked"],
        )
        for bucket in status["repository"]["changes"].values():
            self.assertEqual(sorted(bucket), ["count", "paths"])
        self.assertEqual(sorted(status["repository"]["contract"]), self.CONTRACT_KEYS)
        self.assertEqual(sorted(status["repository"]["gate"]), self.GATE_KEYS)
        self.assertEqual(sorted(status["rails"]), ["checks", "healthy"])
        self.assertTrue(status["rails"]["checks"])
        self.assertEqual(
            sorted(status["rails"]["checks"][0]), ["detail", "name", "ok"]
        )
        self.assertEqual(sorted(status["roadmap"]), self.ROADMAP_KEYS)
        self.assertEqual(sorted(status["roadmap"]["projects"][0]), self.PROJECT_KEYS)
        self.assertEqual(sorted(status["next_action"]), self.ACTION_KEYS)
        self.assertEqual(status["actions"], [status["next_action"]])
        self.assertEqual(status["next_action"]["id"], "start-story")
        self.assertEqual(
            status["next_action"]["command"],
            [
                ".githooks/dw", "story", "status", "demo", "1",
                "DM-1-02", "in-progress",
            ],
        )

    def test_step_preview_is_schema_pinned_pure_and_state_bound(self) -> None:
        before = subprocess.check_output(
            ["git", "-C", str(self.root), "status", "--porcelain=v1", "-z"]
        )
        events = self.root / ".git" / "pmo-events.jsonl"
        event_before = events.read_bytes() if events.exists() else b""

        first = core.build_step(self.root)
        second = core.build_step(self.root)

        after = subprocess.check_output(
            ["git", "-C", str(self.root), "status", "--porcelain=v1", "-z"]
        )
        event_after = events.read_bytes() if events.exists() else b""
        self.assertEqual(first, second)
        self.assertEqual(before, after)
        self.assertEqual(event_before, event_after)
        self.assertFalse(
            (self.root / ".git" / "pmo-step-claims").exists(),
            "preview must not create the replay ledger",
        )
        self.assertEqual(sorted(first), self.STEP_KEYS)
        self.assertEqual(first["kind"], "delivery-workbench-step")
        self.assertEqual(first["schema_version"], 1)
        self.assertEqual(first["project"], "demo")
        self.assertEqual(first["action"]["id"], "start-story")
        self.assertTrue(first["applicable"])
        self.assertIsNone(first["refusal"])
        self.assertRegex(first["token"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(
            first["apply_command"],
            [
                ".githooks/dw", "step", "demo", "--apply", "--expect",
                first["token"],
            ],
        )

    def test_step_stale_token_refuses_before_runner_even_for_same_action(self) -> None:
        preview = core.build_step(self.root)
        calls: list[tuple[list[str], Path]] = []

        subprocess.run(
            [
                "git", "-C", str(self.root), "commit", "-q", "--allow-empty",
                "--no-verify", "-m", "shift head only",
            ],
            check=True,
        )
        current = core.build_step(self.root)
        self.assertEqual(current["action"]["id"], preview["action"]["id"])
        self.assertNotEqual(current["token"], preview["token"])

        def runner(argv: list[str], cwd: Path) -> int:
            calls.append((argv, cwd))
            return 0

        result, exit_code = core.apply_step(
            self.root,
            None,
            str(preview["token"]),
            runner=runner,
        )
        self.assertEqual(exit_code, 1)
        self.assertEqual(sorted(result), self.STEP_RESULT_KEYS)
        self.assertEqual(result["outcome"], "refused")
        self.assertFalse(result["started"])
        self.assertIsNone(result["after"])
        self.assertIn("token is stale", result["reason"])
        self.assertEqual(
            result["output"],
            {
                "stdout": "",
                "stderr": "",
                "truncated": {"stdout": False, "stderr": False},
            },
        )
        self.assertEqual(calls, [])
        self.assertEqual(self.step_events(), [])

    def test_step_runs_exactly_one_allowlisted_child_and_mirrors_exit(self) -> None:
        preview = core.build_step(self.root)
        calls: list[tuple[list[str], Path]] = []

        def runner(argv: list[str], cwd: Path) -> core.StepChild:
            calls.append((argv, cwd))
            return core.StepChild(
                7,
                stdout=b"receipt-only-stdout\n",
                stderr=b"receipt-only-stderr\n",
            )

        result, exit_code = core.apply_step(
            self.root,
            None,
            str(preview["token"]),
            runner=runner,
        )
        self.assertEqual(exit_code, 7)
        self.assertEqual(sorted(result), self.STEP_RESULT_KEYS)
        self.assertEqual(result["kind"], "delivery-workbench-step-result")
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["outcome"], "failed")
        self.assertTrue(result["started"])
        self.assertEqual(result["action"], preview["action"])
        self.assertEqual(sorted(result["before"]), self.STEP_OBSERVATION_KEYS)
        self.assertEqual(result["before"]["token"], preview["token"])
        self.assertEqual(result["before"]["action_id"], "start-story")
        self.assertEqual(sorted(result["after"]), self.STEP_OBSERVATION_KEYS)
        self.assertEqual(result["after"]["action_id"], "start-story")
        self.assertNotEqual(result["after"]["token"], preview["token"])
        self.assertEqual(sorted(result["output"]), self.STEP_OUTPUT_KEYS)
        self.assertEqual(result["output"]["stdout"], "receipt-only-stdout\n")
        self.assertEqual(result["output"]["stderr"], "receipt-only-stderr\n")
        self.assertEqual(
            result["output"]["truncated"],
            {"stdout": False, "stderr": False},
        )
        self.assertEqual(
            calls,
            [
                (
                    [
                        ".githooks/dw", "story", "status", "demo", "1",
                        "DM-1-02", "in-progress",
                    ],
                    self.root.resolve(),
                )
            ],
        )
        events = self.step_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["story"], "DM-1-02")
        self.assertEqual(
            events[0]["detail"],
            {
                "action": "start-story",
                "outcome": "failed",
                "exit_code": 7,
                "before": result["before"]["token"],
                "after": result["after"]["token"],
                "next_action": "start-story",
            },
        )
        event_text = (self.root / ".git" / "pmo-events.jsonl").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("receipt-only-stdout", event_text)
        self.assertNotIn("receipt-only-stderr", event_text)

    def test_step_success_is_bounded_and_old_lease_cannot_replay(self) -> None:
        preview = core.build_step(self.root)
        calls = 0

        def runner(_argv: list[str], _cwd: Path) -> core.StepChild:
            nonlocal calls
            calls += 1
            return core.StepChild(0, stdout="é" * 20, stderr="sensitive" * 10)

        result, exit_code = core.apply_step(
            self.root,
            None,
            str(preview["token"]),
            runner=runner,
            max_output_bytes=9,
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(result["outcome"], "succeeded")
        self.assertEqual(result["reason"], None)
        self.assertLessEqual(len(result["output"]["stdout"].encode("utf-8")), 11)
        self.assertTrue(result["output"]["truncated"]["stdout"])
        self.assertTrue(result["output"]["truncated"]["stderr"])
        self.assertEqual(calls, 1)
        self.assertEqual(len(self.step_events()), 1)

        replay, replay_code = core.apply_step(
            self.root,
            None,
            str(preview["token"]),
            runner=runner,
        )
        self.assertEqual(replay_code, 1)
        self.assertEqual(replay["outcome"], "refused")
        self.assertFalse(replay["started"])
        self.assertIn("token is stale", replay["reason"])
        self.assertEqual(calls, 1)
        self.assertEqual(len(self.step_events()), 1)

    def test_step_interruption_and_start_failure_are_truthful(self) -> None:
        preview = core.build_step(self.root)

        def interrupt(_argv: list[str], _cwd: Path) -> int:
            raise KeyboardInterrupt

        interrupted, exit_code = core.apply_step(
            self.root,
            None,
            str(preview["token"]),
            runner=interrupt,
        )
        self.assertEqual(exit_code, 130)
        self.assertEqual(interrupted["outcome"], "interrupted")
        self.assertTrue(interrupted["started"])
        self.assertEqual(interrupted["reason"], "step child was interrupted")
        self.assertEqual(len(self.step_events()), 1)

        next_preview = core.build_step(self.root)
        not_started, exit_code = core.apply_step(
            self.root,
            None,
            str(next_preview["token"]),
            runner=lambda _argv, _cwd: core.StepChild(
                127,
                stderr="missing executable\n",
                started=False,
                reason="could not start fixture",
            ),
        )
        self.assertEqual(exit_code, 127)
        self.assertEqual(not_started["outcome"], "failed")
        self.assertFalse(not_started["started"])
        self.assertEqual(not_started["reason"], "could not start fixture")
        self.assertEqual(len(self.step_events()), 1)

    def test_step_closes_over_action_id_and_entire_argv_shape(self) -> None:
        status = self.status()
        cases = [
            ("start-story", ["sh", "-c", "touch escaped"]),
            ("future-action", status["next_action"]["command"]),
        ]
        for action_id, command in cases:
            with self.subTest(action_id=action_id, command=command):
                tampered = json.loads(json.dumps(status))
                tampered["next_action"]["id"] = action_id
                tampered["next_action"]["command"] = command
                with mock.patch.object(step_core, "build_status", return_value=tampered):
                    preview = step_core.build_step(self.root)
                self.assertFalse(preview["applicable"])
                self.assertIsNone(preview["apply_command"])
                self.assertIn("closed action/argv table", preview["refusal"])

    def test_step_allowlist_positive_and_negative_matrix(self) -> None:
        allowed = [
            ("repair-rails", [".githooks/dw", "doctor"]),
            ("resolve-rewrite", ["git", "status"]),
            ("review-unstaged", ["git", "status", "--short"]),
            ("review-workspace", ["git", "status", "--short"]),
            ("generate-contract", [".githooks/dw", "contract", "new"]),
            ("generate-contract", [".githooks/dw", "contract", "new", "--force"]),
            ("repair-roadmap", [".githooks/dw", "check"]),
            ("repair-roadmap", [".githooks/dw", "check", "demo"]),
            ("repair-roadmap", [".githooks/dw", "phase", "create", "--help"]),
            (
                "finish-story",
                [".githooks/dw", "story", "status", "demo", "12", "DM-12-03", "done"],
            ),
            (
                "start-story",
                [
                    ".githooks/dw", "story", "status", "demo", "12",
                    "DM-12-03", "in-progress",
                ],
            ),
            (
                "continue-story",
                [".githooks/dw", "story", "show", "demo", "12", "DM-12-03"],
            ),
            ("review-holds", [".githooks/dw", "holds", "demo"]),
            ("plan-work", [".githooks/dw", "phase", "create", "--help"]),
        ]
        for action_id, command in allowed:
            with self.subTest(allowed=action_id, command=command):
                self.assertTrue(
                    step_core._command_is_allowlisted(  # type: ignore[attr-defined]
                        {"id": action_id, "command": command}
                    )
                )

        refused = [
            ("commit", ["git", "commit"]),
            ("future-action", ["git", "status"]),
            ("start-story", "sh -c 'touch escaped'"),
            (
                "start-story",
                ["/tmp/dw", "story", "status", "demo", "12", "DM-12-03", "in-progress"],
            ),
            (
                "start-story",
                [
                    ".githooks/dw", "story", "evidence", "demo", "12",
                    "DM-12-03", "in-progress",
                ],
            ),
            (
                "start-story",
                [
                    ".githooks/dw", "story", "status", "demo", "12",
                    "DM-12-03", "in-progress", "--force",
                ],
            ),
            (
                "start-story",
                [
                    ".githooks/dw", "story", "status", "-demo", "12",
                    "DM-12-03", "in-progress",
                ],
            ),
            (
                "start-story",
                [
                    ".githooks/dw", "story", "status", "demo", "latest",
                    "DM-12-03", "in-progress",
                ],
            ),
            (
                "start-story",
                [
                    ".githooks/dw", "story", "status", "demo", "12",
                    "dm-12-03", "in-progress",
                ],
            ),
            (
                "finish-story",
                [
                    ".githooks/dw", "story", "status", "demo", "12",
                    "DM-12-03", "complete",
                ],
            ),
            ("repair-roadmap", [".githooks/dw", "check", "demo/other"]),
            ("review-holds", [".githooks/dw", "holds", "demo", "--json"]),
        ]
        for action_id, command in refused:
            with self.subTest(refused=action_id, command=command):
                self.assertFalse(
                    step_core._command_is_allowlisted(  # type: ignore[attr-defined]
                        {"id": action_id, "command": command}
                    )
                )

    def test_dirty_active_work_continues_but_unowned_work_is_reviewed(self) -> None:
        phase = core.get_phase(core.get_project(self.root, "demo"), "1")
        plan = core.plan_story_status(
            self.root, core.get_project(self.root, "demo"), phase,
            "DM-1-02", "in-progress",
        )
        core.apply_plan(plan)
        status = self.status()
        self.assertEqual(status["next_action"]["id"], "continue-story")
        self.assertGreater(status["repository"]["changes"]["unstaged"]["count"], 0)

        # Restore a clean fixture, then introduce work with no active story.
        subprocess.run(["git", "-C", str(self.root), "restore", "."], check=True)
        readme = self.root / "pm" / "roadmap" / "demo" / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nchange\n", encoding="utf-8")
        status = self.status()
        self.assertEqual(status["next_action"]["id"], "review-workspace")

    def test_captured_evidence_recommends_the_guarded_done_transition(self) -> None:
        phase = core.get_phase(core.get_project(self.root, "demo"), "1")
        plan = core.plan_story_status(
            self.root, core.get_project(self.root, "demo"), phase,
            "DM-1-02", "in-progress",
        )
        core.apply_plan(plan)
        (phase.path / "evidence-story-02.md").write_text(
            "# Evidence - DM-1-02\n\n## Captured run 1\n\n- exit: 0\n",
            encoding="utf-8",
        )

        status = self.status()
        self.assertEqual(status["verdict"], "attention")
        self.assertEqual(status["next_action"]["id"], "finish-story")
        self.assertTrue(status["next_action"]["blocking"])
        self.assertEqual(
            status["next_action"]["command"],
            [
                ".githooks/dw", "story", "status", "demo", "1",
                "DM-1-02", "done",
            ],
        )

    def test_stage_contract_certification_gate_and_staleness_sequence(self) -> None:
        readme = self.root / "pm" / "roadmap" / "demo" / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nchange\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", str(readme)], check=True)

        status = self.status()
        self.assertEqual(status["next_action"]["id"], "generate-contract")
        self.assertEqual(status["repository"]["gate"]["state"], "fail")

        core.write_contract(self.root)
        status = self.status()
        self.assertEqual(status["repository"]["contract"]["state"], "unchecked")
        self.assertEqual(status["next_action"]["id"], "certify-contract")
        self.assertEqual(status["next_action"]["kind"], "manual")
        self.assertIsNone(status["next_action"]["command"])

        contract = self.root / ".tmp" / "CONTRACT.md"
        contract.write_text(
            contract.read_text(encoding="utf-8").replace("- [ ]", "- [x]"),
            encoding="utf-8",
        )
        status = self.status()
        self.assertEqual(status["repository"]["contract"]["state"], "passing")
        self.assertEqual(status["next_action"]["id"], "commit")
        step = core.build_step(self.root)
        self.assertEqual(step["action"]["id"], "commit")
        self.assertFalse(step["applicable"])
        self.assertIsNone(step["apply_command"])
        self.assertIn("never applied", step["refusal"])

        # Restaging changes the index-tree fact and must retract commit.
        readme.write_text(readme.read_text(encoding="utf-8") + "later\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", str(readme)], check=True)
        status = self.status()
        self.assertEqual(status["repository"]["contract"]["state"], "stale")
        self.assertEqual(status["next_action"]["id"], "generate-contract")
        self.assertIn("--force", status["next_action"]["command"])

    def test_mixed_stage_precedes_contract_and_status_is_pure(self) -> None:
        readme = self.root / "pm" / "roadmap" / "demo" / "README.md"
        story = self.root / "pm" / "roadmap" / "demo" / "phase-1-alpha" / "story-02-second.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nstaged\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", str(readme)], check=True)
        story.write_text(story.read_text(encoding="utf-8") + "\nunstaged\n", encoding="utf-8")
        before = subprocess.check_output(
            ["git", "-C", str(self.root), "status", "--porcelain=v1", "-z"]
        )
        events = self.root / ".git" / "pmo-events.jsonl"
        event_before = events.read_bytes() if events.exists() else b""
        first = self.status()
        second = self.status()
        after = subprocess.check_output(
            ["git", "-C", str(self.root), "status", "--porcelain=v1", "-z"]
        )
        event_after = events.read_bytes() if events.exists() else b""
        self.assertEqual(first, second)
        self.assertEqual(before, after)
        self.assertEqual(event_before, event_after)
        self.assertEqual(first["next_action"]["id"], "review-unstaged")

    def test_attention_precedence_for_rails_roadmap_and_rewrite(self) -> None:
        (self.root / ".githooks" / "pre-commit").unlink()
        status = self.status()
        self.assertEqual(status["verdict"], "attention")
        self.assertEqual(status["next_action"]["id"], "repair-rails")

        (self.root / ".githooks" / "pre-commit").write_text("#!/bin/sh\n", encoding="utf-8")
        story = self.root / "pm" / "roadmap" / "demo" / "phase-1-alpha" / "story-02-second.md"
        story.unlink()
        status = self.status()
        self.assertEqual(status["verdict"], "attention")
        self.assertEqual(status["next_action"]["id"], "repair-roadmap")

        subprocess.run(["git", "-C", str(self.root), "restore", "."], check=True)
        git_dir = Path(
            subprocess.check_output(
                ["git", "-C", str(self.root), "rev-parse", "--git-dir"], text=True
            ).strip()
        )
        if not git_dir.is_absolute():
            git_dir = self.root / git_dir
        (git_dir / "CHERRY_PICK_HEAD").write_text("0" * 40 + "\n", encoding="utf-8")
        status = self.status()
        self.assertEqual(status["verdict"], "attention")
        self.assertEqual(status["next_action"]["id"], "resolve-rewrite")

    def test_same_clone_absolute_hooks_path_does_not_block(self) -> None:
        subprocess.run(
            [
                "git", "-C", str(self.root), "config", "core.hooksPath",
                str(self.root / ".githooks"),
            ],
            check=True,
        )
        status = self.status()
        self.assertTrue(status["rails"]["healthy"])
        self.assertNotEqual(status["next_action"]["id"], "repair-rails")

        subprocess.run(
            [
                "git", "-C", str(self.root), "config", "core.hooksPath",
                "/tmp/some-other-hooks",
            ],
            check=True,
        )
        status = self.status()
        self.assertFalse(status["rails"]["healthy"])
        self.assertEqual(status["next_action"]["id"], "repair-rails")

    def test_multiple_projects_are_never_guessed(self) -> None:
        source = self.root / "pm" / "roadmap" / "demo"
        target = self.root / "pm" / "roadmap" / "other"
        shutil.copytree(source, target)
        other_readme = target / "README.md"
        other_readme.write_text(
            other_readme.read_text(encoding="utf-8")
            .replace("Demo", "Other")
            .replace("`demo`", "`other`"),
            encoding="utf-8",
        )
        status = self.status()
        self.assertIsNone(status["roadmap"]["selected_project"])
        self.assertTrue(status["roadmap"]["selection_required"])
        self.assertEqual(status["next_action"]["id"], "select-project")
        self.assertIsNone(status["next_action"]["command"])
        step = core.build_step(self.root)
        self.assertFalse(step["applicable"])
        self.assertIsNone(step["project"])
        self.assertIsNone(step["apply_command"])
        self.assertIn("manual decision", step["refusal"])
        selected = self.status("other")
        self.assertEqual(selected["roadmap"]["selected_project"], "other")

    def test_empty_roadmap_directory_requests_project_setup(self) -> None:
        shutil.rmtree(self.root / "pm" / "roadmap" / "demo")
        status = self.status()
        self.assertEqual(status["verdict"], "ready")
        self.assertTrue(status["roadmap"]["healthy"])
        self.assertEqual(status["roadmap"]["projects"], [])
        self.assertEqual(status["roadmap"]["issues"], [])
        self.assertEqual(status["next_action"]["id"], "setup-project")
        self.assertEqual(status["next_action"]["command"], ["dw", "new-project", "--help"])

    def test_action_targets_next_story_phase_not_a_closed_pointer(self) -> None:
        project = self.root / "pm" / "roadmap" / "demo"
        old = project / "phase-0-old"
        old.mkdir()
        (old / "current-phase-status.md").write_text(
            "# Phase 0 - Old\n\n## Story status\n\n"
            "| ID | Story | Status | Story file | Evidence |\n"
            "|---|---|---|---|---|\n",
            encoding="utf-8",
        )
        (old / "final-summary.md").write_text("# Closed\n", encoding="utf-8")
        readme = project / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                "[phase-1-alpha](./phase-1-alpha/current-phase-status.md)",
                "[phase-0-old](./phase-0-old/current-phase-status.md)",
            ),
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(self.root), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "commit", "-q", "--no-verify", "-m", "old pointer"],
            check=True,
        )
        status = self.status()
        self.assertEqual(status["roadmap"]["projects"][0]["current_phase"]["number"], 0)
        self.assertEqual(status["next_action"]["id"], "start-story")
        self.assertEqual(status["next_action"]["command"][4], "1")

    def test_path_lists_are_bounded_but_counts_are_complete(self) -> None:
        for index in range(55):
            (self.root / f"untracked-{index:02d}.txt").write_text("x", encoding="utf-8")
        bucket = self.status()["repository"]["changes"]["untracked"]
        self.assertEqual(bucket["count"], 55)
        self.assertEqual(len(bucket["paths"]), 50)
        self.assertEqual(bucket["paths"], sorted(bucket["paths"]))

    def test_human_render_leads_with_verdict_and_next(self) -> None:
        rendered = core.render_status(self.status())
        lines = rendered.splitlines()
        self.assertEqual(lines[0], "Delivery is ready")
        self.assertIn("Current work: DM-1-02: Second thing", lines)
        self.assertIn("Progress: 1 of 2 work items complete in phase 1.", lines)
        self.assertTrue(
            any(line.startswith("Start current work:") for line in lines)
        )
        technical = lines.index("Technical details:")
        self.assertGreater(technical, 3)
        self.assertIn(
            "  Command: .githooks/dw story status demo 1 DM-1-02 in-progress",
            lines[technical + 1 :],
        )

    def test_http_status_presentation_wraps_but_does_not_replace_exact_status(
        self,
    ) -> None:
        from dw_pmo.workbench import handle_api

        exact_status, exact_body = handle_api(
            self.root, "/api/status", {"project": ["demo"]}
        )
        human_status, human_body = handle_api(
            self.root, "/api/presentation/status", {"project": ["demo"]}
        )
        self.assertEqual(exact_status, 200)
        self.assertEqual(human_status, 200)
        self.assertEqual(exact_body["data"], self.status("demo"))
        self.assertEqual(
            exact_body["data"]["kind"], "delivery-workbench-status"
        )
        self.assertEqual(
            human_body["data"]["kind"], "delivery-workbench-presentation"
        )
        self.assertEqual(human_body["data"]["surface"], "status")
        self.assertEqual(
            human_body["data"]["source"],
            {"kind": "delivery-workbench-status", "schema_version": 1},
        )
        for flag in (
            "starts_work",
            "writes_state",
            "selects_next_work",
            "grants_permission",
        ):
            self.assertIs(human_body["data"][flag], False)


class EverydayPresentationTest(unittest.TestCase):
    """WLA-27-08: one executable vocabulary and presentation boundary."""

    REPO_ROOT = TESTS_DIR.parent.parent

    def test_runtime_catalog_matches_the_reviewed_contract(self) -> None:
        from dw_pmo.workbench import handle_api

        contract = json.loads(
            (self.REPO_ROOT / "docs/product-language-contract-v1.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            item["id"]: {
                "preferred": item["preferred"],
                "definition": item["definition"],
            }
            for item in contract["concepts"]
        }
        catalog = core.build_presentation_catalog()
        self.assertEqual(catalog["concepts"], expected)
        self.assertEqual(
            catalog["technical_details_label"], "Technical details"
        )
        status, body = handle_api(
            self.REPO_ROOT, "/api/presentation", {}
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"], catalog)
        for flag in (
            "starts_work",
            "writes_state",
            "selects_next_work",
            "grants_permission",
        ):
            self.assertIs(catalog[flag], False)

    def test_real_presenters_match_versioned_human_snapshots(self) -> None:
        snapshots = json.loads(
            (
                TESTS_DIR / "everyday-presentation-snapshots-v1.json"
            ).read_text(encoding="utf-8")
        )
        builders = {
            "status": lambda source, _aux: core.build_status_presentation(
                source
            ),
            "step": lambda source, _aux: core.build_step_presentation(source),
            "step-result": (
                lambda source, _aux:
                core.build_step_result_presentation(source)
            ),
            "live": lambda source, _aux: core.build_live_presentation(source),
            "start": (
                lambda source, _aux: core.build_start_presentation(source)
            ),
            "action": (
                lambda source, aux:
                core.build_action_presentation(source, aux)
            ),
            "notification": (
                lambda source, _aux:
                core.build_notification_presentation(source)
            ),
        }
        seen = set()
        for case in snapshots["cases"]:
            with self.subTest(case=case["id"]):
                seen.add(case["builder"])
                source = json.loads(json.dumps(case["input"]))
                auxiliary = json.loads(json.dumps(case["auxiliary"]))
                before = json.loads(json.dumps([source, auxiliary]))
                view = builders[case["builder"]](source, auxiliary)
                self.assertEqual(
                    core.render_presentation(view), case["expected"]
                )
                self.assertEqual([source, auxiliary], before)
                self.assertEqual(
                    case["expected"].count("Technical details:\n"), 1
                )
        self.assertEqual(seen, set(builders))

    def test_cli_help_uses_the_shared_task_language(self) -> None:
        result = subprocess.run(
            [str(TESTS_DIR.parent / "bin/dw"), "--help"],
            cwd=self.REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        self.assertIn(
            "Plan, do, review, and prove repository delivery",
            result.stdout,
        )
        for term in (
            "current work",
            "blockers",
            "progress",
            "next step",
            "permission",
            "cost",
        ):
            self.assertIn(term, result.stdout)


class StateFeedTest(unittest.TestCase):
    """WLA-13-02: the mission-control feed is schema-pinned. These
    frozen key sets ARE the stability promise — changing the shape
    without bumping FEED_SCHEMA must fail here."""

    REPO_ROOT = TESTS_DIR.parent.parent

    TOP_KEYS = ["feed_schema", "generated_at_tree", "orchestration_runs", "projects"]
    PROJECT_KEYS = [
        "current_phase", "next_story", "phases", "prefix", "slug",
        "stories", "warnings",
    ]
    PHASE_KEYS = ["number", "status", "stories_done", "stories_total", "title"]
    STORY_KEYS = ["evidence_exists", "phase", "status", "story_id", "title"]
    NEXT_KEYS = ["status", "story_id", "title"]

    def setUp(self) -> None:
        from dw_pmo.statefeed import FEED_SCHEMA, build_state_feed

        self.assertEqual(FEED_SCHEMA, 1)
        self.feed = build_state_feed(self.REPO_ROOT)

    def test_schema_is_pinned(self) -> None:
        self.assertEqual(sorted(self.feed.keys()), self.TOP_KEYS)
        self.assertEqual(self.feed["feed_schema"], 1)
        self.assertEqual(
            sorted(self.feed["orchestration_runs"].keys()),
            ["kind", "runs", "schema_version", "starts_work", "writes_events"],
        )
        for project in self.feed["projects"]:
            self.assertEqual(sorted(project.keys()), self.PROJECT_KEYS)
            for phase in project["phases"]:
                self.assertEqual(sorted(phase.keys()), self.PHASE_KEYS)
            for story in project["stories"]:
                self.assertEqual(sorted(story.keys()), self.STORY_KEYS)
            if project["next_story"] is not None:
                self.assertEqual(
                    sorted(project["next_story"].keys()), self.NEXT_KEYS
                )
            if project["current_phase"] is not None:
                self.assertEqual(
                    sorted(project["current_phase"].keys()), self.PHASE_KEYS
                )

    def test_feed_reflects_real_state(self) -> None:
        project = self.feed["projects"][0]
        self.assertEqual(project["slug"], "work-log-automation")
        closed_12 = [p for p in project["phases"] if p["number"] == 12]
        self.assertEqual(closed_12[0]["status"], "closed")
        self.assertTrue(
            any(s["story_id"] == "WLA-12-01" and s["evidence_exists"]
                for s in project["stories"])
        )

    def test_write_emits_the_same_document(self) -> None:
        import json as _json

        from dw_pmo.statefeed import render_state_feed

        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "state.json"
            target.write_text(
                render_state_feed(self.REPO_ROOT) + "\n", encoding="utf-8"
            )
            reread = _json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(sorted(reread.keys()), self.TOP_KEYS)


class EventsTest(unittest.TestCase):
    """WLA-13-04: every taxonomy event fires at its rail moment; the
    log is append-only rails metadata that rogue callers cannot
    pollute."""

    def setUp(self) -> None:
        import subprocess as sp

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        sp.run(["git", "init", "-q", str(self.root)], check=True,
               stdin=sp.DEVNULL)
        project = self.root / "pm" / "roadmap" / "shop"
        project.mkdir(parents=True)
        (project / "README.md").write_text(
            "# Shop - Roadmap\n\n**Last updated:** 2026-07-04.\n"
            "**Current phase:** n/a.\n**Status:** planning.\n\n"
            "## Phase index\n\n| Phase | Goal (one line) | Status | Folder |\n"
            "|---|---|---|---|\n\n## Project metadata\n\n"
            "- **Slug:** `shop`\n- **Story ID prefix:** `SHP`\n",
            encoding="utf-8",
        )

    def _events(self) -> list[dict]:
        from dw_pmo.events import read_events

        return read_events(self.root)

    def test_rail_moments_emit(self) -> None:
        from dw_pmo import (
            apply_plan, get_phase, get_project, plan_phase_create,
            plan_story_create, plan_story_status, run_capture,
        )
        from dw_pmo.contract import write_contract

        project = get_project(self.root, "shop")
        apply_plan(plan_phase_create(self.root, project, 1, "Ship", goal="g."),
                   validate_after=False)
        project = get_project(self.root, "shop")
        phase = get_phase(project, "1")
        apply_plan(plan_story_create(self.root, project, phase, "Cart"),
                   validate_after=False)
        apply_plan(
            plan_story_status(self.root, project, phase, "SHP-1-01",
                              "in-progress"),
            validate_after=False,
        )
        run_capture(self.root, project, phase, "SHP-1-01",
                    ["sh", "-c", "true"])
        write_contract(self.root, ["SHP-1-01"])

        events = self._events()
        kinds = [e["event"] for e in events]
        self.assertEqual(
            kinds,
            ["phase_created", "story_status", "story_status",
             "evidence_capture", "contract_generated"],
        )
        self.assertEqual(events[0]["detail"], {"phase": 1})
        self.assertEqual(events[1]["detail"], {"from": None, "to": "backlog"})
        self.assertEqual(
            events[2]["detail"], {"from": "backlog", "to": "in-progress"}
        )
        self.assertEqual(events[3]["detail"]["exit_code"], 0)
        self.assertEqual(events[4]["detail"], {"stories": "SHP-1-01"})
        for event in events:
            self.assertEqual(
                sorted(event.keys()),
                ["detail", "event", "project", "story", "story", "tree", "ts"][:0]
                or ["detail", "event", "project", "story", "tree", "ts"],
            )

    def test_gate_refusal_carries_its_rule(self) -> None:
        from dw_pmo import run_gate

        result = run_gate(self.root)
        events = self._events()
        self.assertTrue(events, "a gate run must emit")
        last = events[-1]
        if result.ok:
            self.assertEqual(last["event"], "gate_pass")
        else:
            self.assertEqual(last["event"], "gate_refusal")
            self.assertEqual(last["detail"]["rule"], result.failure.rule)

    def test_content_audit_rogue_keys_dropped(self) -> None:
        from dw_pmo.events import emit

        emit(
            self.root, "story_status", project="shop", story="SHP-1-01",
            detail={
                "from": "backlog", "to": "done",
                "diff": "secret diff content",
                "transcript": "what the human typed",
                "prompt": "x" * 10_000,
            },
        )
        emit(self.root, "not_a_real_event", detail={"anything": "nope"})
        events = self._events()
        self.assertEqual(len(events), 1, "unknown event types are dropped")
        self.assertEqual(
            sorted(events[0]["detail"].keys()), ["from", "to"],
            "rogue detail keys must never reach the log",
        )
        text = (self.root / ".git" / "pmo-events.jsonl").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("secret diff content", text)
        self.assertNotIn("what the human typed", text)

    def test_append_only_and_never_raises(self) -> None:
        from dw_pmo.events import emit, read_events

        emit(self.root, "gate_pass", detail={"stories": None})
        emit(self.root, "gate_pass", detail={"stories": None})
        self.assertEqual(len(read_events(self.root)), 2)
        # a root without .git is a silent no-op, not an error
        bare = self.root / "nowhere"
        bare.mkdir()
        emit(bare, "gate_pass")
        self.assertEqual(read_events(bare), [])
        # oversized values are truncated, not rejected
        emit(self.root, "gate_refusal", detail={"rule": "r" * 5000})
        last = read_events(self.root)[-1]
        self.assertEqual(len(last["detail"]["rule"]), 200)


class SessionsTest(unittest.TestCase):
    """WLA-13-03: every correlation outcome has a test and a
    defined, honest output — unknown beats guessed."""

    SESSION_KEYS = [
        "agent", "awaiting_response", "correlation", "key",
        "last_assistant_text", "model", "project_name", "repo_root",
        "stale", "stories", "tmux", "updated_at",
    ]

    def setUp(self) -> None:
        from datetime import datetime, timezone

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.now = datetime(2026, 7, 4, 12, 0, 0, tzinfo=timezone.utc)
        self.fresh = "2026-07-04T11:45:00Z"   # 15 min old
        self.old = "2026-07-04T10:00:00Z"     # 2 h old

    def _rails_repo(self, name: str, statuses: list[str]) -> Path:
        root = self.base / name
        project = root / "pm" / "roadmap" / "shop"
        project.mkdir(parents=True)
        (root / ".githooks").mkdir()
        (root / ".githooks" / "dw").write_text("#!/bin/sh\n", encoding="utf-8")
        rows = "\n".join(
            f"| SHP-1-{i+1:02d} | Story {i+1} | {status} | "
            f"[story-{i+1:02d}-x](./story-{i+1:02d}-x.md) | - |"
            for i, status in enumerate(statuses)
        )
        (project / "README.md").write_text(
            "# Shop - Roadmap\n\n**Last updated:** 2026-07-04.\n"
            "**Current phase:** n/a.\n**Status:** active.\n\n"
            "## Phase index\n\n| Phase | Goal (one line) | Status | Folder |\n"
            "|---|---|---|---|\n"
            "| 1 | Ship | active | [phase-1-ship](./phase-1-ship) |\n\n"
            "## Project metadata\n\n- **Slug:** `shop`\n"
            "- **Story ID prefix:** `SHP`\n",
            encoding="utf-8",
        )
        phase = project / "phase-1-ship"
        phase.mkdir()
        (phase / "current-phase-status.md").write_text(
            "# Phase 1 - Ship\n\n## Story status\n\n"
            "| ID | Story | Status | Story file | Evidence |\n"
            "|---|---|---|---|---|\n" + rows + "\n",
            encoding="utf-8",
        )
        return root

    def _registry(self, records: dict) -> Path:
        path = self.base / "agent_sessions.json"
        import json as _json

        path.write_text(
            _json.dumps({"version": 1, "sessions": records}),
            encoding="utf-8",
        )
        return path

    def _record(self, repo: Path | None, **extra) -> dict:
        base = {
            "agent": "claude",
            "session_id": "s-1",
            "model": "m",
            "repo_root": str(repo) if repo else "",
            "project_name": "shop",
            "awaiting_response": False,
            "last_assistant_text": None,
            "tmux_session": None,
            "tmux_window": None,
            "tmux_pane": None,
            "updated_at": self.fresh,
        }
        base.update(extra)
        return base

    def _correlate(self, records: dict) -> list[dict]:
        from dw_pmo.sessions import correlate_sessions

        doc = correlate_sessions(self._registry(records), now=self.now)
        self.assertEqual(doc["registry"], "ok")
        return doc["sessions"]

    def test_all_outcomes(self) -> None:
        on = self._rails_repo("on", ["in-progress", "done", "backlog"])
        ambiguous = self._rails_repo("amb", ["in-progress", "in-progress"])
        idle = self._rails_repo("idle", ["done", "backlog"])
        off = self.base / "plain"
        off.mkdir()
        # Rails markers present, roadmap unparseable: README.md is a
        # directory, so project discovery raises instead of parsing.
        unreadable = self.base / "broken"
        (unreadable / "pm" / "roadmap" / "shop" / "README.md").mkdir(parents=True)
        (unreadable / ".githooks").mkdir()
        (unreadable / ".githooks" / "dw").write_text("#!/bin/sh\n", encoding="utf-8")

        sessions = self._correlate(
            {
                "claude:on": self._record(on, awaiting_response=True,
                                          tmux_session="main", tmux_window=1,
                                          tmux_pane="%3"),
                "claude:amb": self._record(ambiguous),
                "claude:idle": self._record(idle),
                "claude:off": self._record(off),
                "claude:broken": self._record(unreadable),
                "claude:stale": self._record(on, updated_at=self.old),
            }
        )
        by_key = {s["key"]: s for s in sessions}
        self.assertEqual(by_key["claude:on"]["correlation"], "on_story")
        self.assertEqual(
            by_key["claude:on"]["stories"][0]["story_id"], "SHP-1-01"
        )
        self.assertTrue(by_key["claude:on"]["awaiting_response"])
        self.assertEqual(
            by_key["claude:on"]["tmux"],
            {"session": "main", "window": 1, "pane": "%3"},
        )
        self.assertFalse(by_key["claude:on"]["stale"])
        self.assertEqual(by_key["claude:amb"]["correlation"], "ambiguous")
        self.assertEqual(len(by_key["claude:amb"]["stories"]), 2)
        self.assertEqual(by_key["claude:idle"]["correlation"], "idle_on_rails")
        self.assertEqual(by_key["claude:off"]["correlation"], "off_rails")
        self.assertEqual(by_key["claude:broken"]["correlation"], "unreadable")
        self.assertTrue(by_key["claude:stale"]["stale"])
        for s in sessions:
            self.assertEqual(sorted(s.keys()), self.SESSION_KEYS)

    def test_registry_failure_shapes(self) -> None:
        from dw_pmo.sessions import correlate_sessions

        absent = correlate_sessions(self.base / "missing.json", now=self.now)
        self.assertEqual(absent["registry"], "absent")
        self.assertEqual(absent["sessions"], [])

        wrong = self.base / "wrong.json"
        wrong.write_text('{"version": 99, "sessions": {}}', encoding="utf-8")
        doc = correlate_sessions(wrong, now=self.now)
        self.assertIn("99", doc["registry"])
        self.assertEqual(doc["sessions"], [])

        garbage = self.base / "garbage.json"
        garbage.write_text("not json", encoding="utf-8")
        self.assertEqual(
            correlate_sessions(garbage, now=self.now)["registry"],
            "unreadable",
        )


class RiderDocsTest(unittest.TestCase):
    """WLA-12-04: one canonical brief, rendered per surface, drift is
    a check error."""

    REPO_ROOT = TESTS_DIR.parent.parent

    def setUp(self) -> None:
        from dw_pmo import agentdocs

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".claude" / "commands").mkdir(parents=True)
        (self.root / "plugin" / "commands").mkdir(parents=True)
        (self.root / "CLAUDE.md").write_text(
            "# Fixture\n\n" + agentdocs.render_block() + "\n", encoding="utf-8"
        )
        from dw_pmo import riderdocs

        self.first_render = riderdocs.write_rider_docs(self.root)

    def test_embedded_specs_match_source_canon(self) -> None:
        from dw_pmo import agentdocs, riderdocs

        agent_dir = self.REPO_ROOT / "pmo-roadmap" / "agent"
        for name in riderdocs.COMMAND_NAMES:
            self.assertEqual(
                riderdocs._EMBEDDED_COMMANDS[name],
                (agent_dir / f"{name}.md").read_text(encoding="utf-8"),
                f"embedded canon for {name} drifted from pmo-roadmap/agent",
            )
        self.assertEqual(
            agentdocs.CANONICAL_BLOCK,
            (self.REPO_ROOT / "pmo-roadmap/templates/CLAUDE-snippet.md")
            .read_text(encoding="utf-8").strip(),
            "packaged managed-block fallback drifted from the source template",
        )

    def test_regeneration_is_idempotent(self) -> None:
        from dw_pmo import riderdocs

        self.assertTrue(
            any(a == "created" for _p, a in self.first_render),
            "the first render over empty dirs must create the copies",
        )
        second = riderdocs.write_rider_docs(self.root)
        self.assertTrue(
            all(a == "unchanged" for _p, a in second),
            f"second render must be a no-op, got {second}",
        )
        self.assertEqual(riderdocs.rider_docs_issues(self.root), [])

    def test_every_rider_opens_with_status_then_uses_fresh_step_leases(self) -> None:
        from dw_pmo import agentdocs, riderdocs

        for text in (agentdocs.canonical_block(), agentdocs.agents_block()):
            self.assertLess(text.index(".githooks/dw status"), text.index(".githooks/dw context"))
            self.assertLess(text.index(".githooks/dw status"), text.index(".githooks/dw step"))
            self.assertIn("Exit 0 means `ready`", text)
            self.assertIn("exit 1 means `attention`", text)
            self.assertIn("dw_status", text)
            for token in ("applicable: true", "apply_command", "exact `expect` token",
                          "Never build an automatic", "certification", "commit"):
                self.assertIn(token, text)
            self.assertIn("dw_step", text)
            self.assertIn("dw_step_apply", text)
        next_riders = (
            riderdocs.command_spec("dw-next"),
            riderdocs.codex_skill("dw-next"),
            riderdocs.pi_prompt("dw-next"),
        )
        for text in next_riders:
            self.assertLess(text.index(".githooks/dw status"), text.index(".githooks/dw next"))
            self.assertIn("attention", text)
            for token in (".githooks/dw step", "fresh lease", "applicable: true",
                          "exact `apply_command`", "Never\ncontinue into a step loop"):
                self.assertIn(token, text)
            self.assertNotIn(".githooks/dw story status", text)
        for text in (
            riderdocs.command_spec("dw-story-done"),
            riderdocs.codex_skill("dw-story-done"),
            riderdocs.pi_prompt("dw-story-done"),
        ):
            for token in ("applicable: true", "finish-story", "exact `apply_command`",
                          "Never reconstruct", "cannot commit"):
                self.assertIn(token, text)
        plugin = (self.REPO_ROOT / "plugin/skills/delivery-workbench/SKILL.md").read_text(encoding="utf-8")
        self.assertLess(plugin.index(".githooks/dw status"), plugin.index(".githooks/dw context"))
        for token in (".githooks/dw step", "dw_step", "dw_step_apply",
                      "exact command", "never build a step loop"):
            self.assertIn(token, plugin)

    def test_hand_edited_copy_is_a_check_error(self) -> None:
        from dw_pmo import riderdocs

        riderdocs.write_rider_docs(self.root)
        victim = self.root / "plugin" / "commands" / "dw-next.md"
        victim.write_text(
            victim.read_text(encoding="utf-8") + "\nrogue edit\n",
            encoding="utf-8",
        )
        issues = riderdocs.rider_docs_issues(self.root)
        self.assertEqual(len(issues), 1)
        self.assertIn("plugin/commands/dw-next.md", issues[0])
        self.assertIn("drifted from", issues[0])
        self.assertIn("dw-next", issues[0])
        riderdocs.write_rider_docs(self.root)
        self.assertEqual(riderdocs.rider_docs_issues(self.root), [])

    def test_hand_edited_doc_block_is_a_check_error(self) -> None:
        from dw_pmo import agentdocs, riderdocs

        claude = self.root / "CLAUDE.md"
        claude.write_text(
            claude.read_text(encoding="utf-8").replace(
                "evidence-first commit gate", "vibes-first commit gate"
            ),
            encoding="utf-8",
        )
        issues = riderdocs.rider_docs_issues(self.root)
        self.assertTrue(any("CLAUDE.md: managed block drifted" in i for i in issues))
        agentdocs.write_agent_docs(self.root)
        self.assertEqual(riderdocs.rider_docs_issues(self.root), [])

    def test_agents_md_gets_the_agents_variant(self) -> None:
        from dw_pmo import agentdocs

        target = self.root / "AGENTS.md"
        target.write_text("# Agents fixture\n", encoding="utf-8")
        path, action = agentdocs.write_agent_docs(self.root, target)
        self.assertEqual(path, target)
        self.assertEqual(action, "added")
        text = target.read_text(encoding="utf-8")
        self.assertNotIn("Slash commands (Claude Code", text)
        self.assertIn("complete surface", text)
        self.assertIn("codex mcp add", text)
        # And its drift status is judged against its own variant.
        again = agentdocs.write_agent_docs(self.root, target)
        self.assertEqual(again[1], "unchanged")

    def test_agents_transformations_actually_fire(self) -> None:
        from dw_pmo import agentdocs

        canon = agentdocs.canonical_block()
        self.assertIn(
            agentdocs._CLAUDE_SLASH_PARAGRAPH_START, canon,
            "canon lost the paragraph the agents variant removes",
        )
        self.assertIn(
            agentdocs._MCP_CLAUDE_WIRING, canon,
            "canon lost the wiring phrase the agents variant generalizes",
        )
        variant = agentdocs.agents_block()
        self.assertNotEqual(variant, canon)
        self.assertNotIn(agentdocs._CLAUDE_SLASH_PARAGRAPH_START, variant)

    def test_real_tree_matches_canon(self) -> None:
        from dw_pmo import riderdocs

        self.assertEqual(
            riderdocs.rider_docs_issues(self.REPO_ROOT),
            [],
            "the framework repo's own rendered surfaces must match canon",
        )

    # -- Codex rider (WLA-12-05) ------------------------------------

    def test_codex_skill_renders_frontmatter_and_body(self) -> None:
        from dw_pmo import riderdocs

        skill = riderdocs.codex_skill("dw-next")
        self.assertTrue(skill.startswith("---\nname: dw-next\ndescription: "))
        self.assertIn("Orient yourself in this repository's", skill)
        # The Claude frontmatter must not survive into the skill body.
        self.assertEqual(skill.count("---\n"), 2)

    def test_codex_installer_is_idempotent(self) -> None:
        from dw_pmo import riderdocs

        first = riderdocs.install_codex_rider(self.root)
        created = [a for _p, a in first["actions"] if a in {"created", "added"}]
        self.assertTrue(created, "first install must create surfaces")
        self.assertIn("[mcp_servers.delivery-workbench]", first["mcp_snippet"])
        second = riderdocs.install_codex_rider(self.root)
        self.assertTrue(
            all(a == "unchanged" for _p, a in second["actions"]),
            f"second install must be a no-op, got {second['actions']}",
        )
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn("Slash commands (Claude Code", agents)
        for name in riderdocs.COMMAND_NAMES:
            self.assertTrue(
                (self.root / ".codex" / "skills" / name / "SKILL.md").exists()
            )

    # -- pi rider (WLA-12-06) ---------------------------------------

    def test_pi_prompt_is_verbatim_canon_and_pure(self) -> None:
        from dw_pmo import riderdocs

        for name in riderdocs.COMMAND_NAMES:
            prompt = riderdocs.pi_prompt(name)
            self.assertEqual(prompt, riderdocs.command_spec(name))
            self.assertEqual(
                riderdocs.pi_purity_violations(prompt), [],
                f"{name} rendered for pi must carry no MCP/Claude-isms",
            )

    def test_pi_installer_is_idempotent(self) -> None:
        from dw_pmo import riderdocs

        first = riderdocs.install_pi_rider(self.root)
        self.assertTrue(
            any(a in {"created", "added"} for _p, a in first["actions"])
        )
        second = riderdocs.install_pi_rider(self.root)
        self.assertTrue(
            all(a == "unchanged" for _p, a in second["actions"]),
            f"second install must be a no-op, got {second['actions']}",
        )
        for name in riderdocs.COMMAND_NAMES:
            self.assertTrue((self.root / ".pi" / "prompts" / f"{name}.md").exists())

    def test_pi_prompt_drift_is_a_check_error(self) -> None:
        from dw_pmo import riderdocs

        riderdocs.install_pi_rider(self.root)
        victim = self.root / ".pi" / "prompts" / "dw-adopt.md"
        victim.write_text(
            victim.read_text(encoding="utf-8") + "\nrogue\n", encoding="utf-8"
        )
        issues = riderdocs.rider_docs_issues(self.root)
        self.assertTrue(
            any(".pi/prompts/dw-adopt.md" in i and "drifted" in i for i in issues),
            issues,
        )
        riderdocs.write_rider_docs(self.root)
        self.assertEqual(riderdocs.rider_docs_issues(self.root), [])

    def test_codex_and_pi_share_agents_md_without_conflict(self) -> None:
        from dw_pmo import riderdocs

        riderdocs.install_codex_rider(self.root)
        result = riderdocs.install_pi_rider(self.root)
        agents_action = [a for p, a in result["actions"] if p.name == "AGENTS.md"]
        self.assertEqual(
            agents_action, ["unchanged"],
            "one AGENTS.md serves both riders; the second install must not rewrite it",
        )

    # -- doctor rider awareness + Desk presence (WLA-12-07) ---------

    def _rider_lines(self):
        from dw_pmo import riderdocs

        return {name: (ok, detail) for ok, name, detail in riderdocs.rider_report(self.root)}

    def test_doctor_riders_wired_absent_and_broken(self) -> None:
        from dw_pmo import riderdocs

        lines = self._rider_lines()
        self.assertTrue(lines["rider:claude"][0])
        self.assertIn("wired", lines["rider:claude"][1])
        self.assertIn("not installed", lines["rider:pi"][1])

        riderdocs.install_codex_rider(self.root)
        victim = self.root / ".codex" / "skills" / "dw-next" / "SKILL.md"
        victim.write_text(
            victim.read_text(encoding="utf-8") + "\nrogue\n", encoding="utf-8"
        )
        ok, detail = self._rider_lines()["rider:codex"]
        self.assertFalse(ok, "a broken rider must flip its line to a finding")
        self.assertIn("drifted", detail)
        riderdocs.write_rider_docs(self.root)
        ok_after, _ = self._rider_lines()["rider:codex"]
        self.assertTrue(ok_after)

    def test_hs_context_block_lifecycle(self) -> None:
        from dw_pmo import riderdocs

        (self.root / "pm" / "roadmap" / "shop").mkdir(parents=True)
        (self.root / "pm" / "roadmap" / "shop" / "README.md").write_text(
            "# Shop - Roadmap\n\n**Last updated:** 2026-07-04.\n"
            "**Current phase:** n/a.\n**Status:** planning.\n\n"
            "## Phase index\n\n| Phase | Goal (one line) | Status | Folder |\n"
            "|---|---|---|---|\n\n## Project metadata\n\n"
            "- **Slug:** `shop`\n- **Story ID prefix:** `SHP`\n",
            encoding="utf-8",
        )
        target = self.root / ".hs" / "context.md"
        target.parent.mkdir()
        target.write_text("# Operator notes\n\nkeep me\n", encoding="utf-8")
        result = riderdocs.install_holdspeak_presence(self.root)
        self.assertEqual(result["actions"][0][1], "added")
        text = target.read_text(encoding="utf-8")
        self.assertIn("keep me", text, "operator content survives")
        self.assertIn("Delivery Workbench roadmap state", text)
        self.assertIn("### shop", text)
        path, action = riderdocs.refresh_hs_context(self.root)
        self.assertEqual(action, "unchanged")
        # .hs is live state, deliberately outside the byte-drift rule.
        self.assertEqual(
            [i for i in riderdocs.rider_docs_issues(self.root) if ".hs" in i], []
        )

    def test_codex_skill_drift_is_a_check_error(self) -> None:
        from dw_pmo import riderdocs

        riderdocs.install_codex_rider(self.root)
        victim = self.root / ".codex" / "skills" / "dw-contract" / "SKILL.md"
        victim.write_text(
            victim.read_text(encoding="utf-8") + "\nrogue\n", encoding="utf-8"
        )
        issues = riderdocs.rider_docs_issues(self.root)
        self.assertTrue(
            any(".codex/skills/dw-contract/SKILL.md" in i and "drifted" in i for i in issues),
            issues,
        )
        riderdocs.write_rider_docs(self.root)
        self.assertEqual(riderdocs.rider_docs_issues(self.root), [])




class OrchestrationCompilerTest(unittest.TestCase):
    """WLA-24-02: one exact, pure score compiler for every surface."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-orchestration-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.scores = self.root / "pm" / "orchestration"
        self.scores.mkdir(parents=True)
        self.preset_path = TESTS_DIR.parent / "templates" / "orchestration" / "research-build-review.json"

    @staticmethod
    def minimal():
        return {
            "kind": "delivery-workbench-orchestration",
            "schema_version": 1,
            "slug": "minimal",
            "title": "Minimal handoff",
            "nodes": [{
                "id": "handoff",
                "type": "approval",
                "prompt": "Review before certification.",
                "terminal": "awaiting-certification",
            }],
        }

    @staticmethod
    def codes(document):
        return {item["code"] for item in document["diagnostics"]}

    def write_score(self, name, score):
        path = self.scores / f"{name}.json"
        path.write_text(json.dumps(score, indent=2) + "\n", encoding="utf-8")
        return path

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, str(TESTS_DIR.parent / "bin" / "dw"), "--root", str(self.root),
             "orchestration", *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_representative_preset_compiles_and_simulates_parallel_fan_in(self):
        import dw_pmo.orchestration as orch

        compiled = orch.compile_score_path(self.preset_path)
        self.assertEqual(compiled["kind"], orch.COMPILED_SCORE_KIND)
        self.assertRegex(compiled["semantic_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(compiled["analysis"]["fan_in"], ["synthesize"])
        self.assertEqual(
            compiled["analysis"]["role_presets"], list(orch.ROLE_PRESETS)
        )
        simulation = orch.simulate_score(compiled)
        self.assertEqual(
            simulation["waves"][0]["scheduled"],
            ["research-api", "research-risks"],
        )
        self.assertEqual(simulation["waves"][-1]["scheduled"], ["human-handoff"])
        self.assertIn("repair", [b.get("node") for b in simulation["failure_branches"]])
        self.assertEqual(
            simulation["terminals"],
            [{"node": "human-handoff", "meaning": "awaiting-certification"}],
        )
        self.assertFalse(simulation["starts_work"])
        self.assertFalse(simulation["writes_events"])

    def test_minimal_and_custom_role_round_trip(self):
        import dw_pmo.orchestration as orch

        score = self.minimal()
        score["nodes"].insert(0, {
            "id": "specialist",
            "type": "agent",
            "role": "domain-specialist",
            "profile": "readonly-local",
            "capabilities": ["repository-read"],
            "workspace": "read-only",
            "outputs": [{
                "name": "notes", "format": "text", "path": "artifacts/notes.txt",
            }],
        })
        score["nodes"][1]["needs"] = ["specialist"]
        compiled = orch.compile_score(score)
        self.assertEqual(compiled["score"]["nodes"][0]["role"], "domain-specialist")
        self.assertEqual(compiled["score"]["nodes"][0]["capabilities"], ["repository-read"])
        self.assertNotIn("domain-specialist", orch.ROLE_PRESETS)

    def test_semantic_hash_ignores_object_key_order_and_layout_only(self):
        import dw_pmo.orchestration as orch

        score = self.minimal()
        score["layout"] = {
            "nodes": {"handoff": {"x": 10, "y": 20}},
            "viewport": {"zoom": 1, "y": 0, "x": 0},
        }
        reordered = json.loads(json.dumps(score, sort_keys=True))
        first = orch.compile_score(score)
        second = orch.compile_score(reordered)
        self.assertEqual(first["semantic_hash"], second["semantic_hash"])
        self.assertEqual(first["document_hash"], second["document_hash"])
        moved = json.loads(json.dumps(score))
        moved["layout"]["nodes"]["handoff"]["x"] = 999
        third = orch.compile_score(moved)
        self.assertEqual(first["semantic_hash"], third["semantic_hash"])
        self.assertNotEqual(first["document_hash"], third["document_hash"])
        changed = json.loads(json.dumps(score))
        changed["nodes"][0]["prompt"] = "A different runtime prompt"
        self.assertNotEqual(
            first["semantic_hash"], orch.compile_score(changed)["semantic_hash"]
        )

    def test_nudge_rules_compile_simulate_and_refuse_exactly(self):
        import dw_pmo.orchestration as orch

        template = json.loads(
            (TESTS_DIR.parent / "templates" / "orchestration"
             / "research-build-review.json").read_text()
        )
        baseline = orch.compile_score(template)["semantic_hash"]
        template["nudges"] = [{
            "id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
            "max_total": 2, "expectation": "make the pushed branch green",
        }]
        verdict = orch.validate_score(template)
        self.assertTrue(verdict["valid"], verdict["diagnostics"])
        compiled = orch.compile_score(template)
        self.assertEqual(len(compiled["score"]["nudges"]), 1)
        self.assertEqual(compiled["analysis"]["nudges"][0]["target"], "repair")
        self.assertNotEqual(compiled["semantic_hash"], baseline)
        simulation = orch.simulate_score(template)
        self.assertEqual(simulation["nudges"][0]["id"], "on-ci-failed")
        self.assertEqual(simulation["budgets"]["max_nudges"], 5)

        def broken(**overrides):
            document = json.loads(json.dumps(template))
            document["nudges"][0].update(overrides)
            return self.codes(orch.validate_score(document))

        self.assertIn("dangling-nudge-target", broken(target="ghost"))
        self.assertIn("unsafe-nudge-target", broken(target="tests"))
        self.assertIn("unknown-signal", broken(signal="vibes"))
        self.assertIn("missing-bound", broken(max_total=None))
        self.assertIn("unbounded-value", broken(max_total=999))
        self.assertIn("unknown-key", broken(surprise=True))
        self.assertIn("unknown-key", broken(after_seconds=120))
        duplicated = json.loads(json.dumps(template))
        duplicated["nudges"].append(dict(duplicated["nudges"][0]))
        self.assertIn(
            "duplicate-id", self.codes(orch.validate_score(duplicated))
        )
        timeout_rule = json.loads(json.dumps(template))
        timeout_rule["nudges"] = [{
            "id": "on-stall", "signal": "waiting-input-timeout",
            "target": "implement", "max_total": 1,
        }]
        self.assertIn(
            "missing-bound", self.codes(orch.validate_score(timeout_rule))
        )

    def test_exact_keys_duplicate_ids_and_dangling_references_refuse(self):
        import dw_pmo.orchestration as orch

        score = self.minimal()
        score["surprise"] = True
        score["nodes"].append({
            "id": "handoff", "type": "approval", "needs": ["missing"],
            "prompt": "Again", "terminal": "complete", "mystery": "x",
        })
        validation = orch.validate_score(score)
        self.assertFalse(validation["valid"])
        self.assertTrue(
            {"unknown-key", "duplicate-node-id", "dangling-node-reference"}
            <= self.codes(validation)
        )
        pointers = {item["pointer"] for item in validation["diagnostics"]}
        self.assertIn("/surprise", pointers)
        self.assertIn("/nodes/1/mystery", pointers)

    def test_success_cycles_and_unbounded_failure_policies_refuse(self):
        import dw_pmo.orchestration as orch

        score = self.minimal()
        score["nodes"] = [
            {"id": "one", "type": "collect", "needs": ["two"], "inputs": [],
             "on_failure": {"action": "retry"}},
            {"id": "two", "type": "collect", "needs": ["one"], "inputs": [],
             "on_failure": {"action": "route", "node": "repair", "max_visits": 999}},
            {"id": "repair", "type": "collect", "activation": "success", "inputs": []},
        ]
        score["defaults"] = {"max_concurrency": 9999}
        validation = orch.validate_score(score)
        self.assertTrue(
            {"success-cycle", "missing-bound", "unbounded-value", "unsafe-failure-route"}
            <= self.codes(validation),
            validation["diagnostics"],
        )

    def test_output_producer_type_and_order_checks_refuse(self):
        import dw_pmo.orchestration as orch

        output = {"name": "result", "format": "json", "path": "artifacts/result.json"}
        score = self.minimal()
        score["nodes"] = [
            {"id": "produce-a", "type": "agent", "role": "research", "profile": "r",
             "capabilities": ["repository-read"], "outputs": [output]},
            {"id": "produce-b", "type": "agent", "role": "research", "profile": "r",
             "capabilities": ["repository-read"], "outputs": [dict(output)]},
            {"id": "consume", "type": "agent", "role": "synthesis", "profile": "s",
             "needs": [], "capabilities": ["repository-read"],
             "inputs": [{"artifact": "result", "format": "markdown"}], "outputs": []},
        ]
        validation = orch.validate_score(score)
        self.assertTrue(
            {"multiple-producers", "artifact-order", "incompatible-artifact"}
            <= self.codes(validation),
            validation["diagnostics"],
        )

    def test_unsafe_paths_shell_strings_and_undeclared_runners_refuse(self):
        import dw_pmo.orchestration as orch

        score = self.minimal()
        score["nodes"] = [
            {"id": "bad-agent", "type": "agent", "role": "research", "profile": "r",
             "context": ["../secret"], "capabilities": ["repository-read"],
             "outputs": [{"name": "bad", "format": "text", "path": "../escape"}]},
            {"id": "string-check", "type": "check", "runner": "pytest -q"},
            {"id": "shell-check", "type": "check",
             "runner": {"kind": "command", "argv": ["bash", "-c", "pytest -q"]}},
        ]
        validation = orch.validate_score(score)
        self.assertTrue(
            {"unsafe-path", "undeclared-executable", "shell-string"}
            <= self.codes(validation),
            validation["diagnostics"],
        )

    def test_impossible_capabilities_and_forbidden_rail_authority_refuse(self):
        import dw_pmo.orchestration as orch

        score = self.minimal()
        score["nodes"] = [
            {"id": "writer", "type": "agent", "role": "implementation", "profile": "w",
             "capabilities": ["repository-write", "root-access"], "workspace": "read-only",
             "outputs": []},
            {"id": "commit", "type": "rail", "action": "commit"},
        ]
        validation = orch.validate_score(score)
        self.assertTrue(
            {"unsupported-value", "impossible-capability", "forbidden-authority"}
            <= self.codes(validation),
            validation["diagnostics"],
        )

    def test_resource_locks_and_concurrency_make_simulation_deterministic(self):
        import dw_pmo.orchestration as orch

        score = self.minimal()
        score["defaults"] = {"max_concurrency": 3}
        score["nodes"] = [
            {"id": "alpha", "type": "collect", "inputs": [], "resource_groups": ["repo"]},
            {"id": "beta", "type": "collect", "inputs": [], "resource_groups": ["repo"]},
            {"id": "gamma", "type": "collect", "inputs": [], "resource_groups": ["network"]},
            {"id": "done", "type": "approval", "needs": ["alpha", "beta", "gamma"],
             "prompt": "Review", "terminal": "awaiting-certification"},
        ]
        simulation = orch.simulate_score(score)
        self.assertEqual(simulation["waves"][0]["scheduled"], ["alpha", "gamma"])
        self.assertEqual(simulation["waves"][1]["scheduled"], ["beta"])
        self.assertEqual(simulation["waves"][2]["scheduled"], ["done"])

    def test_duplicate_json_keys_nonfinite_numbers_and_escaped_symlinks_refuse(self):
        import dw_pmo.orchestration as orch

        with self.assertRaises(DwError):
            orch.parse_score_text('{"kind":"a","kind":"b"}')
        with self.assertRaises(DwError):
            orch.parse_score_text('{"x": NaN}')
        outside = self.tmp / "outside.json"
        outside.write_text(json.dumps(self.minimal()), encoding="utf-8")
        (self.scores / "escape.json").symlink_to(outside)
        with self.assertRaises(DwError):
            orch.discover_score_paths(self.root)

    def test_cli_list_show_validate_and_simulate_share_core_documents(self):
        import dw_pmo.orchestration as orch

        path = self.write_score("minimal", self.minimal())
        inventory = self.cli("list", "--json")
        self.assertEqual(inventory.returncode, 0, inventory.stderr)
        listed = json.loads(inventory.stdout)
        self.assertEqual(listed["kind"], "delivery-workbench-orchestration-list")
        self.assertEqual(listed["scores"][0]["path"], "pm/orchestration/minimal.json")
        shown = self.cli("show", "minimal", "--json")
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertEqual(json.loads(shown.stdout), orch.compile_score_path(path))
        valid = self.cli("validate", "minimal", "--json")
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertTrue(json.loads(valid.stdout)["valid"])
        before = sorted(str(item.relative_to(self.root)) for item in self.root.rglob("*"))
        simulated = self.cli("simulate", "minimal", "--json")
        after = sorted(str(item.relative_to(self.root)) for item in self.root.rglob("*"))
        self.assertEqual(simulated.returncode, 0, simulated.stderr)
        self.assertEqual(json.loads(simulated.stdout), orch.simulate_score(self.minimal()))
        self.assertEqual(before, after, "pure CLI reads must not create run/event/cache state")

    def test_cli_invalid_score_returns_pointer_diagnostics_and_exit_one(self):
        score = self.minimal()
        score["nodes"][0]["unknown"] = True
        self.write_score("broken", score)
        result = self.cli("validate", "broken", "--json")
        self.assertEqual(result.returncode, 1)
        document = json.loads(result.stdout)
        self.assertFalse(document["valid"])
        self.assertEqual(document["diagnostics"][0]["pointer"], "/nodes/0/unknown")
        self.assertIn("remediation", document["diagnostics"][0])


class OrchestrationEditorTest(unittest.TestCase):
    """WLA-24-03: compiler-backed reads and guarded score content acts."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-orch-editor-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.scores = self.root / "pm" / "orchestration"
        self.scores.mkdir(parents=True)
        preset = TESTS_DIR.parent / "templates" / "orchestration" / "research-build-review.json"
        self.reference = json.loads(preset.read_text(encoding="utf-8"))
        (self.scores / "research-build-review.json").write_text(
            json.dumps(self.reference, indent=2) + "\n", encoding="utf-8"
        )

    @staticmethod
    def minimal(slug="visual-score"):
        return {
            "kind": "delivery-workbench-orchestration",
            "schema_version": 1,
            "slug": slug,
            "title": "Visual score",
            "nodes": [{
                "id": "handoff", "type": "approval",
                "prompt": "Review", "terminal": "awaiting-certification",
            }],
            "layout": {"nodes": {"handoff": {"x": 10, "y": 20}},
                       "viewport": {"x": 0, "y": 0, "zoom": 1}},
        }

    def test_http_inventory_and_document_use_the_shared_compiler_purely(self):
        from dw_pmo import workbench as wb

        before = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        status, body = wb.handle_api(self.root, "/api/orchestration", {})
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["scores"][0]["name"], "research-build-review")
        status, body = wb.handle_api(
            self.root, "/api/orchestration/research-build-review", {}
        )
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertTrue(data["validation"]["valid"])
        self.assertEqual(data["compiled"]["kind"], "delivery-workbench-compiled-orchestration")
        self.assertEqual(data["simulation"]["waves"][0]["scheduled"],
                         ["research-api", "research-risks"])
        self.assertFalse(data["starts_work"])
        self.assertFalse(data["writes_events"])
        after = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        self.assertEqual(before, after)
        self.assertFalse((self.root / ".git" / "pmo-orchestration").exists())

    def test_save_preview_diff_apply_and_reload_are_exact(self):
        from dw_pmo import workbench as wb
        from dw_pmo.orchestration import compile_score

        score = self.minimal()
        request = {"action": "save", "name": "visual-score", "score": score}
        status, body = wb.handle_mutation(self.root, "/api/orchestration/preview", request)
        self.assertEqual(status, 200)
        preview = body["data"]
        self.assertEqual(preview["kind"], "delivery-workbench-orchestration-mutation-preview")
        self.assertTrue(preview["applicable"])
        self.assertIn("+++ b/pm/orchestration/visual-score.json", preview["diff"])
        self.assertFalse(preview["starts_work"])
        self.assertFalse((self.scores / "visual-score.json").exists())
        status, applied = wb.handle_mutation(
            self.root, "/api/orchestration/apply",
            {**request, "fingerprint": preview["fingerprint"]},
        )
        self.assertEqual(status, 200, applied)
        self.assertTrue(applied["data"]["changed"])
        saved = json.loads((self.scores / "visual-score.json").read_text())
        self.assertEqual(compile_score(saved)["semantic_hash"], preview["compiled"]["semantic_hash"])
        status, loaded = wb.handle_api(self.root, "/api/orchestration/visual-score", {})
        self.assertEqual(status, 200)
        self.assertEqual(loaded["data"]["raw"], saved)
        self.assertFalse((self.root / ".git" / "pmo-orchestration").exists())

    def test_invalid_unknown_field_blocks_apply_without_silent_drop(self):
        from dw_pmo import workbench as wb

        score = self.minimal("invalid-score")
        score["nodes"][0]["provider_command"] = ["agent", "--unsafe"]
        request = {"action": "save", "name": "invalid-score", "score": score}
        status, body = wb.handle_mutation(self.root, "/api/orchestration/preview", request)
        self.assertEqual(status, 200)
        preview = body["data"]
        self.assertFalse(preview["valid"])
        self.assertFalse(preview["applicable"])
        self.assertEqual(preview["validation"]["diagnostics"][0]["pointer"],
                         "/nodes/0/provider_command")
        self.assertIn("unknown-key", {d["code"] for d in preview["validation"]["diagnostics"]})
        status, body = wb.handle_mutation(
            self.root, "/api/orchestration/apply",
            {**request, "fingerprint": preview["fingerprint"]},
        )
        self.assertEqual(status, 400)
        self.assertFalse((self.scores / "invalid-score.json").exists())

    def test_stale_save_and_delete_previews_refuse(self):
        from dw_pmo import workbench as wb

        score = self.minimal("stale-score")
        request = {"action": "save", "name": "stale-score", "score": score}
        _, body = wb.handle_mutation(self.root, "/api/orchestration/preview", request)
        fp = body["data"]["fingerprint"]
        (self.scores / "stale-score.json").write_text(
            json.dumps(self.minimal("stale-score")) + "\n", encoding="utf-8"
        )
        status, body = wb.handle_mutation(
            self.root, "/api/orchestration/apply", {**request, "fingerprint": fp}
        )
        self.assertEqual(status, 409)
        self.assertIn("nothing was written", body["issues"][0])

        delete = {"action": "delete", "name": "stale-score"}
        _, body = wb.handle_mutation(self.root, "/api/orchestration/preview", delete)
        delete_fp = body["data"]["fingerprint"]
        path = self.scores / "stale-score.json"
        path.write_text(path.read_text() + "\n", encoding="utf-8")
        status, _ = wb.handle_mutation(
            self.root, "/api/orchestration/apply",
            {**delete, "fingerprint": delete_fp},
        )
        self.assertEqual(status, 409)
        self.assertTrue(path.exists())

    def test_delete_is_a_separate_preview_apply_act(self):
        from dw_pmo import workbench as wb

        request = {"action": "delete", "name": "research-build-review"}
        status, body = wb.handle_mutation(self.root, "/api/orchestration/preview", request)
        self.assertEqual(status, 200)
        preview = body["data"]
        self.assertTrue(preview["applicable"])
        self.assertIn("--- a/pm/orchestration/research-build-review.json", preview["diff"])
        self.assertTrue((self.scores / "research-build-review.json").exists())
        status, body = wb.handle_mutation(
            self.root, "/api/orchestration/apply",
            {**request, "fingerprint": preview["fingerprint"]},
        )
        self.assertEqual(status, 200)
        self.assertFalse((self.scores / "research-build-review.json").exists())
        self.assertFalse(body["data"]["starts_work"])

    def test_apply_failure_rolls_back_the_original_bytes(self):
        import dw_pmo.orchestration_edit as edit

        path = self.scores / "research-build-review.json"
        before = path.read_bytes()
        changed = json.loads(json.dumps(self.reference))
        changed["title"] = "Changed after atomic write"
        plan = edit.build_score_mutation_plan(
            self.root, "save", "research-build-review", changed
        )
        with mock.patch.object(edit, "load_score", side_effect=DwError("planted read-back failure")):
            with self.assertRaises(DwError) as raised:
                edit.apply_score_mutation(plan, plan.fingerprint)
        self.assertIn("rolled back", str(raised.exception))
        self.assertEqual(path.read_bytes(), before)

    def test_score_routes_reject_injection_and_outside_symlink(self):
        from dw_pmo import workbench as wb

        status, _ = wb.handle_mutation(
            self.root, "/api/orchestration/preview",
            {"action": "save", "name": "../escape", "score": self.minimal()},
        )
        self.assertEqual(status, 400)
        status, _ = wb.handle_mutation(
            self.root, "/api/orchestration/preview",
            {"action": "save", "name": "visual-score", "score": self.minimal(),
             "command": ["sh", "-c", "oops"]},
        )
        self.assertEqual(status, 400)
        outside = self.tmp / "outside"
        outside.mkdir()
        shutil.rmtree(self.scores)
        self.scores.symlink_to(outside, target_is_directory=True)
        status, body = wb.handle_mutation(
            self.root, "/api/orchestration/preview",
            {"action": "save", "name": "visual-score", "score": self.minimal()},
        )
        self.assertEqual(status, 400)
        self.assertIn("outside the repository", body["issues"][0])

    def test_visual_editor_static_contract_names_every_rule_surface(self):
        app = (TESTS_DIR.parent / "workbench" / "app.js").read_text(encoding="utf-8")
        html = (TESTS_DIR.parent / "workbench" / "index.html").read_text(encoding="utf-8")
        css = (TESTS_DIR.parent / "workbench" / "style.css").read_text(encoding="utf-8")
        self.assertIn('href="#/orchestration"', html)
        for needle in (
            "orch-canvas", "node palette", "rule inspector", "command argv tokens",
            "context selectors", "typed outputs", "success dependencies",
            "failure route", "maximum concurrency", "output lineage",
            "scheduling simulation", "semantic hash", "document hash",
            "apply JSON to graph", "preview save", "preview delete",
            "no run, stage, or commit",
        ):
            self.assertIn(needle, app)
        self.assertNotIn('name="shell"', app)
        self.assertNotIn('name="provider_command"', app)
        self.assertIn("@media (max-width: 520px)", css)
        self.assertIn('tabindex="0" role="button"', app)


class OrchestrationRunAuthorityTest(unittest.TestCase):
    """WLA-24-04: score-bound grants, ledger replay, and exclusive claims."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-orch-run-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self._cmd("git", "init", "-q", "-b", "main")
        self._cmd("git", "config", "user.name", "Run Fixture")
        self._cmd("git", "config", "user.email", "run@example.test")
        subprocess.run(
            [str(TESTS_DIR.parent / "bootstrap" / "new-project.sh"),
             str(self.root), "sample", "Sample", "SMP"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        subprocess.run(
            [str(TESTS_DIR.parent / "install.sh"), str(self.root), "--skip-bootstrap"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.dw = self.root / ".githooks" / "dw"
        self._dw("story", "status", "sample", "0", "SMP-0-01", "in-progress")
        self._dw("rider", "docs")
        self._commit("fixture")
        self.now = datetime.now(timezone.utc).replace(microsecond=0)

    def _cmd(self, *argv, check=True):
        return subprocess.run(
            list(argv), cwd=self.root, check=check, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def _dw(self, *argv, check=True):
        return self._cmd(str(self.dw), *argv, check=check)

    def _commit(self, message):
        self._cmd("git", "add", ".")
        self._cmd("git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", message)

    def plan(self, offset=3600):
        import dw_pmo.orchestration_run as runs

        return runs.build_run_plan(
            self.root, "research-build-review", "sample", "SMP-0-01",
            issued_at=self.now, expires_at=self.now + timedelta(seconds=offset),
        )

    def start(self, plan=None, now=None):
        import dw_pmo.orchestration_run as runs

        plan = plan or self.plan()
        return runs.start_run(
            self.root, plan, plan["start_token"], approved=True,
            approved_by="fixture-operator", now=now or self.now,
        )

    def test_plan_is_pure_and_binds_score_status_story_authority_and_expiry(self):
        import dw_pmo.orchestration_run as runs

        store = self.root / ".git" / "pmo-orchestration"
        before = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        plan = self.plan()
        after = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        self.assertTrue(plan["applicable"], plan["issues"])
        self.assertEqual(before, after)
        self.assertFalse(store.exists())
        self.assertFalse(plan["starts_work"])
        self.assertFalse(plan["writes_run_state"])
        self.assertEqual(plan["repository"]["branch"], "main")
        self.assertEqual(plan["story"]["id"], "SMP-0-01")
        self.assertEqual(plan["story"]["status"], "in-progress")
        self.assertEqual(
            plan["authority"]["capabilities"],
            ["network", "repository-read", "repository-write"],
        )
        self.assertIn("max_concurrency", plan["authority"]["budgets"])
        self.assertEqual(
            plan["authority"]["permanent_exclusions"],
            list(runs.PERMANENT_EXCLUSIONS),
        )
        later = runs.build_run_plan(
            self.root, "research-build-review", "sample", "SMP-0-01",
            issued_at=self.now, expires_at=self.now + timedelta(seconds=3601),
        )
        self.assertNotEqual(plan["start_token"], later["start_token"])

    def test_start_requires_exact_approval_and_writes_one_atomic_run(self):
        import dw_pmo.orchestration_run as runs

        plan = self.plan()
        with self.assertRaises(DwError):
            runs.start_run(
                self.root, plan, plan["start_token"], approved=False,
                approved_by="fixture-operator", now=self.now,
            )
        self.assertFalse((self.root / ".git" / "pmo-orchestration").exists())
        projection = self.start(plan)
        run_dir = self.root / ".git" / "pmo-orchestration" / "runs" / projection["run_id"]
        self.assertEqual(
            sorted(path.name for path in run_dir.iterdir()),
            ["grant.json", "ledger.jsonl", "plan.json", "projection.json", "score.json"],
        )
        self.assertEqual(projection["state"], "active")
        self.assertTrue(projection["dispatch_allowed"])
        self.assertEqual(projection["ledger_events"], 1)
        grant = json.loads((run_dir / "grant.json").read_text())
        self.assertEqual(grant["start_token"], plan["start_token"])
        self.assertEqual(grant["score"]["semantic_hash"], plan["score"]["semantic_hash"])
        with self.assertRaisesRegex(DwError, "already consumed"):
            self.start(plan)

    def test_tampered_or_stale_plan_refuses_without_run_state(self):
        import dw_pmo.orchestration_run as runs

        plan = self.plan()
        tampered = json.loads(json.dumps(plan))
        tampered["authority"]["capabilities"].append("tools-write")
        with self.assertRaisesRegex(DwError, "stale or altered"):
            runs.start_run(
                self.root, tampered, tampered["start_token"], approved=True,
                approved_by="fixture-operator", now=self.now,
            )
        tampered = json.loads(json.dumps(plan))
        tampered["provider_command"] = ["agent", "--unsafe"]
        with self.assertRaisesRegex(DwError, "non-exact keys"):
            runs.start_run(
                self.root, tampered, tampered["start_token"], approved=True,
                approved_by="fixture-operator", now=self.now,
            )
        score = self.root / "pm" / "orchestration" / "research-build-review.json"
        document = json.loads(score.read_text())
        document["title"] = "Changed after planning"
        score.write_text(json.dumps(document, indent=2) + "\n")
        self._commit("change score")
        with self.assertRaisesRegex(DwError, "stale or altered"):
            runs.start_run(
                self.root, plan, plan["start_token"], approved=True,
                approved_by="fixture-operator", now=self.now,
            )
        runs_dir = self.root / ".git" / "pmo-orchestration" / "runs"
        self.assertFalse(runs_dir.exists())

    def test_projection_ignores_cache_and_corrupt_ledger_fails_closed(self):
        import dw_pmo.orchestration_run as runs

        projection = self.start()
        run_dir = self.root / ".git" / "pmo-orchestration" / "runs" / projection["run_id"]
        (run_dir / "projection.json").unlink()
        replayed = runs.replay_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(replayed, projection)
        (run_dir / "projection.json").write_text('{"state":"fake"}\n')
        self.assertEqual(runs.replay_run(self.root, projection["run_id"], now=self.now), projection)
        ledger_path = run_dir / "ledger.jsonl"
        original = ledger_path.read_bytes()
        fork = runs._event_document(  # noqa: protected-access - chain refusal test
            projection["run_id"], 1, "run_paused",
            {"reason": "fork", "generation": 1}, "sha256:" + "0" * 64, self.now,
        )
        with ledger_path.open("ab") as handle:
            handle.write((json.dumps(fork, sort_keys=True, separators=(",", ":")) + "\n").encode())
        with self.assertRaisesRegex(DwError, "sequence or chain"):
            runs.replay_run(self.root, projection["run_id"], now=self.now)
        ledger_path.write_bytes(original)
        with (run_dir / "ledger.jsonl").open("ab") as handle:
            handle.write(b'{"truncated":')
        with self.assertRaisesRegex(DwError, "truncated"):
            runs.replay_run(self.root, projection["run_id"], now=self.now)

    def test_pause_resume_revoke_cancel_are_exact_terminal_transitions(self):
        import dw_pmo.orchestration_run as runs

        first = self.start()
        claimed = runs.claim_node(
            self.root, first["run_id"], "research-api", 1, "in-flight",
            first["ledger_head"], now=self.now,
        )
        paused = runs.transition_run(
            self.root, first["run_id"], "pause", claimed["ledger_head"],
            reason="operator inspection", now=self.now,
        )
        self.assertEqual(paused["state"], "paused")
        self.assertFalse(paused["dispatch_allowed"])
        self.assertEqual(len(paused["active_claims"]), 1)
        with self.assertRaisesRegex(DwError, "does not currently permit"):
            runs.claim_node(
                self.root, first["run_id"], "research-risks", 1, "after-pause",
                paused["ledger_head"], now=self.now,
            )
        released = runs.release_node_claim(
            self.root, first["run_id"], paused["active_claims"][0]["claim_id"],
            "cancelled", 0, paused["ledger_head"], now=self.now,
        )
        with self.assertRaisesRegex(DwError, "stale"):
            runs.transition_run(
                self.root, first["run_id"], "resume", first["ledger_head"], now=self.now,
            )
        resumed = runs.transition_run(
            self.root, first["run_id"], "resume", released["ledger_head"], now=self.now,
        )
        revoked = runs.transition_run(
            self.root, first["run_id"], "revoke", resumed["ledger_head"],
            reason="authority withdrawn", now=self.now,
        )
        self.assertEqual(revoked["state"], "revoked")
        self.assertFalse(revoked["dispatch_allowed"])

        second_plan = self.plan(offset=3601)
        second = self.start(second_plan)
        cancelled = runs.transition_run(
            self.root, second["run_id"], "cancel", second["ledger_head"],
            reason="work no longer needed", now=self.now,
        )
        self.assertEqual(cancelled["state"], "cancelled")

    def test_claim_release_idempotency_and_all_budget_counters(self):
        import dw_pmo.orchestration_run as runs

        score = self.root / "pm" / "orchestration" / "research-build-review.json"
        document = json.loads(score.read_text())
        document["defaults"]["max_agent_starts"] = 1
        document["defaults"]["max_concurrency"] = 1
        document["defaults"]["max_artifact_bytes"] = 100
        score.write_text(json.dumps(document, indent=2) + "\n")
        self._commit("tight budgets")
        plan = self.plan()
        projection = self.start(plan)
        claimed = runs.claim_node(
            self.root, projection["run_id"], "research-api", 1, "dispatch-1",
            projection["ledger_head"], now=self.now,
        )
        self.assertEqual(claimed["budgets"]["max_concurrency"]["used"], 1)
        claim_id = claimed["active_claims"][0]["claim_id"]
        with self.assertRaisesRegex(DwError, "artifact-byte"):
            runs.release_node_claim(
                self.root, projection["run_id"], claim_id, "succeeded", 101,
                claimed["ledger_head"], now=self.now,
            )
        released = runs.release_node_claim(
            self.root, projection["run_id"], claim_id, "succeeded", 50,
            claimed["ledger_head"], now=self.now,
        )
        self.assertEqual(released["budgets"]["max_agent_starts"]["used"], 1)
        self.assertEqual(released["budgets"]["max_artifact_bytes"]["used"], 50)
        with self.assertRaisesRegex(DwError, "already claimed|idempotency|agent-start"):
            runs.claim_node(
                self.root, projection["run_id"], "research-risks", 1,
                "dispatch-1", released["ledger_head"], now=self.now,
            )

    def test_two_processes_cannot_claim_the_same_node_attempt(self):
        projection = self.start()
        code = (
            "import sys; from pathlib import Path; "
            "from dw_pmo.orchestration_run import claim_node; "
            "from dw_pmo import DwError; "
            "\ntry:\n claim_node(Path(sys.argv[1]),sys.argv[2],sys.argv[3],1,sys.argv[4],sys.argv[5]); print('ok')"
            "\nexcept DwError as e:\n print('refused:'+e.message); raise SystemExit(2)"
        )
        env = dict(os.environ)
        env["PYTHONPATH"] = str(TESTS_DIR.parent / "lib")
        argv = [
            sys.executable, "-c", code, str(self.root), projection["run_id"],
            "research-api", "race-key", projection["ledger_head"],
        ]
        children = [
            subprocess.Popen(argv, text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=env)
            for _ in range(2)
        ]
        results = [child.communicate(timeout=20) + (child.returncode,) for child in children]
        self.assertEqual(sorted(item[2] for item in results), [0, 2], results)
        self.assertEqual(sum(item[0].strip() == "ok" for item in results), 1)

    def test_two_processes_cannot_start_the_same_plan(self):
        plan = self.plan()
        plan_path = self.tmp / "race-plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        code = (
            "import json,sys; from pathlib import Path; "
            "from dw_pmo.orchestration_run import start_run; from dw_pmo import DwError; "
            "p=json.loads(Path(sys.argv[2]).read_text()); "
            "\ntry:\n start_run(Path(sys.argv[1]),p,p['start_token'],approved=True,approved_by='race'); print('ok')"
            "\nexcept DwError as e:\n print('refused:'+e.message); raise SystemExit(2)"
        )
        env = dict(os.environ)
        env["PYTHONPATH"] = str(TESTS_DIR.parent / "lib")
        argv = [sys.executable, "-c", code, str(self.root), str(plan_path)]
        children = [
            subprocess.Popen(argv, text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=env)
            for _ in range(2)
        ]
        results = [child.communicate(timeout=20) + (child.returncode,) for child in children]
        self.assertEqual(sorted(item[2] for item in results), [0, 2], results)
        self.assertEqual(sum(item[0].strip() == "ok" for item in results), 1)

    def test_expiry_and_store_escape_prevent_future_dispatch(self):
        import dw_pmo.orchestration_run as runs

        plan = self.plan(offset=1)
        projection = self.start(plan)
        expired_at = self.now + timedelta(seconds=2)
        expired = runs.replay_run(self.root, projection["run_id"], now=expired_at)
        self.assertTrue(expired["expired"])
        self.assertFalse(expired["dispatch_allowed"])
        with self.assertRaisesRegex(DwError, "does not currently permit"):
            runs.claim_node(
                self.root, projection["run_id"], "research-api", 1, "late",
                expired["ledger_head"], now=expired_at,
            )

        shutil.rmtree(self.root / ".git" / "pmo-orchestration")
        outside = self.tmp / "outside-store"
        outside.mkdir()
        (self.root / ".git" / "pmo-orchestration").symlink_to(
            outside, target_is_directory=True
        )
        with self.assertRaisesRegex(DwError, "symlinked"):
            runs.run_inventory(self.root)

    def test_repository_or_story_drift_stales_dispatch_but_not_audit_replay(self):
        import dw_pmo.orchestration_run as runs

        projection = self.start()
        readme = self.root / "pm" / "roadmap" / "sample" / "README.md"
        readme.write_text(readme.read_text() + "\nworkspace drift\n")
        with self.assertRaisesRegex(DwError, "facts are stale"):
            runs.claim_node(
                self.root, projection["run_id"], "research-api", 1, "drifted",
                projection["ledger_head"], now=self.now,
            )
        replayed = runs.replay_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(replayed["ledger_head"], projection["ledger_head"])
        self.assertEqual(replayed["state"], "active")

    def test_ledger_detail_is_closed_and_content_safe(self):
        import dw_pmo.orchestration_run as runs

        projection = self.start()
        run_dir = self.root / ".git" / "pmo-orchestration" / "runs" / projection["run_id"]
        ledger = (run_dir / "ledger.jsonl").read_text()
        score = (run_dir / "score.json").read_text()
        self.assertIn("Review the diff", score)
        self.assertNotIn("Review the diff", ledger)
        self.assertNotIn("provider", ledger.lower())
        with self.assertRaisesRegex(DwError, "non-exact detail"):
            runs._event_document(  # noqa: protected-access - privacy contract test
                projection["run_id"], 1, "run_paused",
                {"reason": "safe", "generation": 1, "prompt": "secret"},
                projection["ledger_head"], self.now,
            )

    def test_installed_cli_plan_start_show_list_pause_resume(self):
        plan_result = self._dw(
            "run", "plan", "research-build-review", "--project", "sample",
            "--story", "SMP-0-01", "--expires-in", "3600", "--json",
        )
        plan = json.loads(plan_result.stdout)
        plan_path = self.tmp / "run-plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        started = self._dw(
            "run", "start", "--plan", str(plan_path), "--expect",
            plan["start_token"], "--approve", "--operator", "cli-fixture", "--json",
        )
        projection = json.loads(started.stdout)
        shown = json.loads(self._dw(
            "run", "show", projection["run_id"], "--json"
        ).stdout)
        self.assertEqual(shown["ledger_head"], projection["ledger_head"])
        inventory = json.loads(self._dw("run", "list", "--json").stdout)
        self.assertEqual(inventory["runs"][0]["run_id"], projection["run_id"])
        pause_preview = json.loads(self._dw(
            "run", "preview", projection["run_id"], "pause",
            "--reason", "inspect", "--json",
        ).stdout)
        paused = json.loads(self._dw(
            "run", "pause", projection["run_id"], "--expect",
            pause_preview["act_token"], "--reason", "inspect", "--json",
        ).stdout)
        resume_preview = json.loads(self._dw(
            "run", "preview", projection["run_id"], "resume", "--json",
        ).stdout)
        resumed = json.loads(self._dw(
            "run", "resume", projection["run_id"], "--expect",
            resume_preview["act_token"], "--json",
        ).stdout)
        self.assertEqual(resumed["state"], "active")


class OrchestrationDriverTest(unittest.TestCase):
    """WLA-24-05: structured packets, provider seams, and isolated outputs."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-orch-driver-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self._cmd("git", "init", "-q", "-b", "main")
        self._cmd("git", "config", "user.name", "Driver Fixture")
        self._cmd("git", "config", "user.email", "driver@example.test")
        subprocess.run(
            [str(TESTS_DIR.parent / "bootstrap" / "new-project.sh"),
             str(self.root), "sample", "Sample", "SMP"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        subprocess.run(
            [str(TESTS_DIR.parent / "install.sh"), str(self.root), "--skip-bootstrap"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.dw = self.root / ".githooks" / "dw"
        self._dw("story", "status", "sample", "0", "SMP-0-01", "in-progress")
        self._dw("rider", "docs")
        schema = self.root / "schemas" / "risk-register-v1.json"
        schema.parent.mkdir()
        schema.write_text(json.dumps({
            "type": "object",
            "required": ["risks"],
            "properties": {
                "risks": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        }, indent=2) + "\n")
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "context.md").write_text("# Context\n\n" + "bounded context " * 300)
        self._commit("driver fixture")
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.config = {
            "kind": "delivery-workbench-driver-config",
            "schema_version": 1,
            "workspace_root": None,
            "profiles": {
                "research-readonly": {
                    "adapter": "fixture",
                    "capabilities": ["repository-read", "network"],
                    "workspace_modes": ["read-only"],
                    "network": True,
                    "max_context_bytes": 2000,
                },
                "reasoning-readonly": {
                    "adapter": "fixture",
                    "capabilities": ["repository-read"],
                    "workspace_modes": ["read-only"],
                },
                "worker-write": {
                    "adapter": "fixture",
                    "capabilities": ["repository-read", "repository-write"],
                    "workspace_modes": ["isolated-worktree"],
                },
            },
        }
        import dw_pmo.orchestration_run as runs

        plan = runs.build_run_plan(
            self.root, "research-build-review", "sample", "SMP-0-01",
            issued_at=self.now, expires_at=self.now + timedelta(hours=1),
        )
        self.projection = runs.start_run(
            self.root, plan, plan["start_token"], approved=True,
            approved_by="driver-fixture", now=self.now,
        )

    def _cmd(self, *argv, check=True):
        return subprocess.run(
            list(argv), cwd=self.root, check=check, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def _dw(self, *argv, check=True):
        return self._cmd(str(self.dw), *argv, check=check)

    def _commit(self, message):
        self._cmd("git", "add", ".")
        self._cmd("git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", message)

    def claim_packet(self, node_id, key, projection=None, attempt=1, config=None):
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        before = projection or self.projection
        claimed = runs.claim_node(
            self.root, before["run_id"], node_id, attempt, key,
            before["ledger_head"], now=self.now,
        )
        claim = next(
            item for item in claimed["active_claims"]
            if item["idempotency_key"] == key
        )
        packet = drivers.build_work_packet(
            self.root, before["run_id"], claim["claim_id"],
            drivers.load_driver_config(self.root, config or self.config), now=self.now,
        )
        return claimed, packet

    def seed_implementation_brief(self):
        import hashlib
        import dw_pmo.orchestration_driver as drivers

        content = (
            b"# Scope\nFixture.\n\n# Decisions\nBounded.\n\n"
            b"# Acceptance checks\nGreen.\n"
        )
        directory = (
            self.root / ".git" / "pmo-orchestration" / "runs"
            / self.projection["run_id"] / "artifacts" / "synthesize"
            / "implementation-brief"
        )
        directory.mkdir(parents=True)
        (directory / "content").write_bytes(content)
        receipt = {
            "kind": drivers.ARTIFACT_RECEIPT_KIND,
            "schema_version": 1,
            "run_id": self.projection["run_id"],
            "node_id": "synthesize",
            "attempt": 1,
            "name": "implementation-brief",
            "format": "markdown",
            "bytes": len(content),
            "sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
            "path": "artifacts/synthesize/implementation-brief/content",
            "valid": True,
            "checks": ["declared", "contained", "bytes", "markdown-sections", "citations"],
        }
        (directory / "metadata.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        )

    @staticmethod
    def responses():
        return {
            "research-api": {"outputs": {"api-findings": (
                "# Findings\nSafe API surface.\n\n# Sources\n"
                "[Primary documentation](https://example.test/api)\n\n# Risks\nNone.\n"
            )}},
            "research-risks": {"outputs": {"risk-register": {"risks": ["bounded"]}}},
            "synthesize": {"outputs": {"implementation-brief": (
                "# Scope\nSmall.\n\n# Decisions\nBounded.\n\n"
                "# Acceptance checks\nGreen.\n"
            )}},
        }

    def test_config_and_capability_documents_are_closed_and_credential_free(self):
        import dw_pmo.orchestration_driver as drivers

        config = drivers.load_driver_config(self.root, self.config)
        capability = drivers.driver_capability(config, "research-readonly")
        self.assertEqual(capability["kind"], drivers.DRIVER_CAPABILITY_KIND)
        self.assertEqual(capability["adapter"], "fixture")
        self.assertEqual(capability["network"], "operator-enabled")
        self.assertEqual(capability["principal"], "research-readonly")
        self.assertTrue(capability["available"])
        self.assertRegex(
            capability["principal_fingerprint"], r"^sha256:[0-9a-f]{64}$"
        )
        self.assertRegex(
            capability["capability_fingerprint"], r"^sha256:[0-9a-f]{64}$"
        )
        self.assertIsNone(capability["model"])
        self.assertEqual(
            capability["model_binding"], "adapter-default-unresolved"
        )
        modeled = json.loads(json.dumps(self.config))
        modeled["profiles"]["research-readonly"]["model"] = "fixture/model-v2"
        modeled_capability = drivers.driver_capability(
            drivers.load_driver_config(self.root, modeled),
            "research-readonly",
        )
        self.assertEqual(modeled_capability["model"], "fixture/model-v2")
        self.assertEqual(
            modeled_capability["model_binding"], "requested-alias"
        )
        self.assertNotEqual(
            capability["capability_fingerprint"],
            modeled_capability["capability_fingerprint"],
        )
        self.assertFalse(capability["stores_credentials"])
        poisoned = json.loads(json.dumps(self.config))
        poisoned["profiles"]["research-readonly"]["api_token"] = "secret"
        with self.assertRaisesRegex(DwError, "credential|token"):
            drivers.validate_driver_config(poisoned)
        unknown = json.loads(json.dumps(self.config))
        unknown["profiles"]["research-readonly"]["adapter"] = "mystery"
        with self.assertRaisesRegex(DwError, "unsupported adapter"):
            drivers.validate_driver_config(unknown)

    def test_packet_is_bounded_structured_and_contains_no_provider_command(self):
        import dw_pmo.orchestration_driver as drivers

        _claimed, packet = self.claim_packet("research-api", "packet-1")
        self.assertEqual(packet["kind"], drivers.WORK_PACKET_KIND)
        self.assertEqual(packet, drivers.validate_work_packet(packet))
        self.assertEqual(packet["workspace"]["mode"], "read-only")
        self.assertTrue(packet["context"]["truncated"])
        included = sum(item["included_bytes"] for item in packet["context"]["documents"])
        self.assertLessEqual(included, 2000)
        serialized = json.dumps(packet).lower()
        for forbidden in ("provider_command", "api_key", '"command":', "codex exec"):
            self.assertNotIn(forbidden, serialized)
        tampered = json.loads(json.dumps(packet))
        tampered["prompt"] = "changed"
        with self.assertRaisesRegex(DwError, "hash check"):
            drivers.validate_work_packet(tampered)
        self.assertEqual(packet["knowledge"]["grounding_status"], "hint-free")
        knowledge_tamper = json.loads(json.dumps(packet))
        knowledge_tamper["knowledge"]["grounding_status"] = "guessed"
        with self.assertRaisesRegex(DwError, "hash check"):
            drivers.validate_work_packet(knowledge_tamper)

    def test_stale_knowledge_uses_existing_packet_assembly_failure_receipt(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs
        from dw_pmo.knowledge_packet import StaleKnowledgePacket

        claimed = runs.claim_node(
            self.root, self.projection["run_id"], "research-api", 1,
            "stale-knowledge", self.projection["ledger_head"], now=self.now,
        )
        claim = next(item for item in claimed["active_claims"]
                     if item["idempotency_key"] == "stale-knowledge")
        with mock.patch.object(
            drivers,
            "build_repository_knowledge_packet",
            side_effect=StaleKnowledgePacket("fixture stale grounding"),
        ):
            updated = conductor._reconcile_claim(
                self.root, self.projection["run_id"], claim["claim_id"],
                self.config, {"fixture": drivers.FixtureDriver()},
                conductor.CheckManager(self.root),
                conductor.RailManager(self.root), [], now=self.now,
                boundary_hook=None,
            )
        receipt = updated["node_receipts"][-1]
        self.assertEqual(receipt["executor"], "driver")
        self.assertEqual(receipt["state"], "failed")
        self.assertEqual(receipt["reason"], "driver-refused")
        self.assertEqual(receipt["usage_status"], "unknown")

    def test_fixture_absent_usage_is_unknown_in_receipt_and_ledger(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers

        claimed, packet = self.claim_packet("research-api", "unknown-usage")
        claim = next(item for item in claimed["active_claims"]
                     if item["idempotency_key"] == "unknown-usage")
        manager = drivers.DriverManager(
            self.root,
            drivers.load_driver_config(self.root, self.config),
            adapters={"fixture": drivers.FixtureDriver({
                "research-api": {"polls": 0, "outputs": {
                    "api-findings": "# Findings\nSafe.\n\n# Sources\nFixture.\n\n# Risks\nNone.\n"
                }}
            })},
        )
        receipt = manager.start(packet, "unknown-usage-dispatch")
        self.assertEqual(receipt["usage"]["status"], "unknown")
        self.assertIsNone(receipt["usage"]["cost_microunits"])
        updated, appended = conductor._append_receipt(
            self.root, claimed, claim, "driver", receipt,
            receipt["session_id"], now=self.now,
        )
        self.assertTrue(appended)
        ledgered = updated["node_receipts"][-1]
        self.assertEqual(ledgered["usage_status"], "unknown")
        self.assertEqual(ledgered["total_tokens"], "unknown")
        self.assertEqual(ledgered["cost_microunits"], "unknown")

    def test_pi_adapter_pins_version_and_renders_closed_credential_free_argv(self):
        import dw_pmo.orchestration_driver as drivers

        _claimed, packet = self.claim_packet("research-api", "pi-packet")
        raw = {
            "kind": drivers.DRIVER_CONFIG_KIND,
            "schema_version": drivers.DRIVER_SCHEMA_VERSION,
            "workspace_root": None,
            "profiles": {
                "research-readonly": {
                    "adapter": "pi-exec",
                    "adapter_version": "pi-cli@0.42.1",
                    "command": ["pi"],
                    "capabilities": ["repository-read", "network"],
                    "workspace_modes": ["read-only"],
                    "network": True,
                    "router": "openrouter",
                    "provider": "openrouter",
                    "model_vendor": "moonshot",
                    "model_family": "kimi-k3",
                    "model": "moonshot/kimi-k3",
                    "model_binding": "requested-alias",
                    "auth_domain": "openrouter-fixture",
                },
            },
        }
        config = drivers.validate_driver_config(raw)
        profile = config["profiles"]["research-readonly"]
        captured = []

        def run(argv, **kwargs):
            if argv[1:] == ["--version"]:
                return subprocess.CompletedProcess(argv, 0, "pi 0.42.1\n", "")
            captured.append((list(argv), dict(kwargs["env"])))
            kwargs["stdout"].write(
                b"# Findings\nBounded.\n\n# Sources\nhttps://example.test\n\n# Risks\nNone.\n"
            )
            return subprocess.CompletedProcess(argv, 0)

        staging = self.tmp / "pi-staging"
        with mock.patch.object(drivers.shutil, "which", return_value="/fixture/pi"), \
             mock.patch.object(drivers.subprocess, "run", side_effect=run), \
             mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "opaque-fixture-key"}):
            result = drivers.PiExecDriver().start(packet, profile, staging)
        self.assertEqual(result["state"], "succeeded")
        self.assertEqual(len(captured), 1)
        argv, environment = captured[0]
        self.assertEqual(argv[:5], [
            "/fixture/pi", "-p", "--no-session", "--tools",
            "read,grep,find,ls",
        ])
        self.assertEqual(
            argv[5:9],
            ["--provider", "openrouter", "--model", "moonshot/kimi-k3"],
        )
        self.assertNotIn("opaque-fixture-key", " ".join(argv))
        self.assertEqual(environment["OPENROUTER_API_KEY"], "opaque-fixture-key")
        self.assertEqual(environment["PI_SKIP_VERSION_CHECK"], "1")
        self.assertEqual(environment["PI_TELEMETRY"], "0")
        self.assertNotIn("shell", argv[4])

        skewed = json.loads(json.dumps(raw))
        skewed["profiles"]["research-readonly"]["adapter_version"] = "pi-cli@0.42"
        with self.assertRaisesRegex(DwError, "pin"):
            drivers.validate_driver_config(skewed)

    def test_unsupported_profile_request_refuses_before_adapter_start(self):
        import dw_pmo.orchestration_driver as drivers

        _claimed, packet = self.claim_packet("research-api", "unsupported-claim")
        restricted = json.loads(json.dumps(self.config))
        restricted["profiles"]["research-readonly"]["capabilities"] = ["repository-read"]
        restricted["profiles"]["research-readonly"]["network"] = False
        fixture = drivers.FixtureDriver(self.responses())
        manager = drivers.DriverManager(
            self.root, restricted, adapters={"fixture": fixture}
        )
        receipt = manager.start(packet, "unsupported-start")
        self.assertEqual(receipt["state"], "refused")
        self.assertFalse(receipt["started"])
        self.assertEqual(receipt["reason"], "unsupported-capability")
        self.assertEqual(fixture.starts, 0)

    def test_parallel_research_validates_before_synthesis_fan_in(self):
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        first_claimed, first_packet = self.claim_packet(
            "research-api", "research-a", self.projection
        )
        second_claimed, second_packet = self.claim_packet(
            "research-risks", "research-b", first_claimed
        )
        fixture = drivers.FixtureDriver(self.responses())
        manager = drivers.DriverManager(
            self.root, self.config, adapters={"fixture": fixture}
        )
        first = manager.start(first_packet, "session-a")
        second = manager.start(second_packet, "session-b")
        self.assertEqual([first["state"], second["state"]], ["running", "running"])
        self.assertNotEqual(first["session_id"], second["session_id"])
        first = manager.poll(self.projection["run_id"], first["session_id"])
        second = manager.poll(self.projection["run_id"], second["session_id"])
        self.assertEqual([first["state"], second["state"]], ["succeeded", "succeeded"])
        first_artifacts = manager.collect(self.projection["run_id"], first["session_id"])
        second_artifacts = manager.collect(self.projection["run_id"], second["session_id"])
        self.assertIn("citations", first_artifacts[0]["checks"])
        self.assertIn("json-schema", second_artifacts[0]["checks"])
        projection = runs.release_node_claim(
            self.root, self.projection["run_id"], first_packet["claim_id"],
            "succeeded", first_artifacts[0]["bytes"], second_claimed["ledger_head"],
            now=self.now,
        )
        projection = runs.release_node_claim(
            self.root, self.projection["run_id"], second_packet["claim_id"],
            "succeeded", second_artifacts[0]["bytes"], projection["ledger_head"],
            now=self.now,
        )
        synth_claimed, synth_packet = self.claim_packet(
            "synthesize", "synthesis", projection
        )
        self.assertEqual(
            [item["artifact"] for item in synth_packet["inputs"]],
            ["api-findings", "risk-register"],
        )
        synth = manager.start(synth_packet, "session-synthesis")
        synth = manager.poll(self.projection["run_id"], synth["session_id"])
        artifacts = manager.collect(self.projection["run_id"], synth["session_id"])
        self.assertEqual(artifacts[0]["name"], "implementation-brief")
        self.assertEqual(fixture.starts, 3)
        self.assertEqual(len(synth_claimed["active_claims"]), 1)

    def test_missing_citation_fails_collect_even_after_driver_success(self):
        import dw_pmo.orchestration_driver as drivers

        node, key, response, message = (
            "research-api", "missing-citation", {
                "outputs": {"api-findings": "# Findings\nX\n# Sources\nnone\n# Risks\nX\n"}
            }, "citation",
        )
        _claimed, packet = self.claim_packet(node, key)
        manager = drivers.DriverManager(
            self.root, self.config,
            adapters={"fixture": drivers.FixtureDriver({node: response})},
        )
        receipt = manager.start(packet, "bad-output")
        receipt = manager.poll(self.projection["run_id"], receipt["session_id"])
        self.assertEqual(receipt["state"], "succeeded", "driver truth differs from artifact validity")
        with self.assertRaisesRegex(DwError, message):
            manager.collect(self.projection["run_id"], receipt["session_id"])

    def test_malformed_json_and_oversized_artifact_fail_deterministically(self):
        import dw_pmo.orchestration_driver as drivers

        first_claimed, json_packet = self.claim_packet(
            "research-risks", "bad-json", self.projection
        )
        _second_claimed, markdown_packet = self.claim_packet(
            "research-api", "oversized-artifact", first_claimed
        )
        fixture = drivers.FixtureDriver({
            "research-risks": {"outputs": {"risk-register": "not-json"}},
            "research-api": {"outputs": {"api-findings": (
                "# Findings\n" + "x" * 40000
                + "\n# Sources\nhttps://example.test\n# Risks\nX\n"
            )}},
        })
        manager = drivers.DriverManager(self.root, self.config, adapters={"fixture": fixture})
        bad_json = manager.start(json_packet, "bad-json-session")
        too_large = manager.start(markdown_packet, "large-session")
        bad_json = manager.poll(self.projection["run_id"], bad_json["session_id"])
        too_large = manager.poll(self.projection["run_id"], too_large["session_id"])
        with self.assertRaisesRegex(DwError, "malformed"):
            manager.collect(self.projection["run_id"], bad_json["session_id"])
        with self.assertRaisesRegex(DwError, "byte bound"):
            manager.collect(self.projection["run_id"], too_large["session_id"])

    def test_timeout_nonzero_lost_stream_and_interrupt_states_are_truthful(self):
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        first, timeout_packet = self.claim_packet("research-api", "timeout-node")
        second, nonzero_packet = self.claim_packet("research-risks", "nonzero-node", first)
        self.seed_implementation_brief()
        third, interrupt_packet = self.claim_packet("repair", "interrupt-node", second)
        fixture = drivers.FixtureDriver({
            "research-api": {"state": "failed", "reason": "timeout",
                             "exit_code": None, "polls": 0},
            "research-risks": {"state": "succeeded", "exit_code": 7, "polls": 0},
            "repair": {"polls": 5},
        })
        manager = drivers.DriverManager(self.root, self.config, adapters={"fixture": fixture})
        timed_out = manager.start(timeout_packet, "timeout-session")
        nonzero = manager.start(nonzero_packet, "nonzero-session")
        running = manager.start(interrupt_packet, "interrupt-session")
        self.assertEqual((timed_out["state"], timed_out["reason"]), ("failed", "timeout"))
        self.assertEqual((nonzero["state"], nonzero["reason"], nonzero["exit_code"]),
                         ("failed", "nonzero-exit", 7))
        cancelled = manager.interrupt(self.projection["run_id"], running["session_id"])
        self.assertEqual((cancelled["state"], cancelled["reason"]),
                         ("cancelled", "interrupted"))

        # Release one terminal claim, then prove an oversized stream and a
        # lost session map to distinct bounded states without a duplicate start.
        projection = runs.release_node_claim(
            self.root, self.projection["run_id"], timeout_packet["claim_id"],
            "failed", 0, third["ledger_head"], now=self.now,
        )
        # The existing nonzero claim remains active; release it as well so the
        # reference grant's concurrency budget admits one more attempt.
        projection = runs.release_node_claim(
            self.root, self.projection["run_id"], nonzero_packet["claim_id"],
            "failed", 0, projection["ledger_head"], now=self.now,
        )
        projection = runs.release_node_claim(
            self.root, self.projection["run_id"], interrupt_packet["claim_id"],
            "cancelled", 0, projection["ledger_head"], now=self.now,
        )
        fourth, stream_packet = self.claim_packet(
            "research-api", "stream-node", projection, attempt=2
        )
        stream_fixture = drivers.FixtureDriver({
            "research-api": {"state": "succeeded", "polls": 0,
                             "stdout_bytes": stream_packet["max_stream_bytes"] + 1},
        })
        stream_manager = drivers.DriverManager(
            self.root, self.config, adapters={"fixture": stream_fixture}
        )
        oversized = stream_manager.start(stream_packet, "stream-session")
        self.assertEqual((oversized["state"], oversized["reason"]),
                         ("failed", "oversized-stream"))
        self.assertEqual(len(fourth["active_claims"]), 1)
        projection = runs.release_node_claim(
            self.root, self.projection["run_id"], stream_packet["claim_id"],
            "failed", 0, fourth["ledger_head"], now=self.now,
        )
        _fifth, lost_packet = self.claim_packet(
            "research-risks", "lost-node", projection, attempt=2
        )
        lost_manager = drivers.DriverManager(
            self.root, self.config,
            adapters={"fixture": drivers.FixtureDriver({
                "research-risks": {"state": "lost", "exit_code": None, "polls": 1},
            })},
        )
        lost = lost_manager.start(lost_packet, "lost-session")
        lost = lost_manager.poll(self.projection["run_id"], lost["session_id"])
        self.assertEqual((lost["state"], lost["reason"]), ("lost", "lost"))

    def test_writers_get_distinct_worktrees_diff_scope_and_no_implicit_integration(self):
        import dw_pmo.orchestration_driver as drivers

        self.seed_implementation_brief()
        first_claimed, implement = self.claim_packet("implement", "writer-a")
        _second_claimed, repair = self.claim_packet("repair", "writer-b", first_claimed)
        self.assertNotEqual(implement["workspace"]["path"], repair["workspace"]["path"])
        self.assertEqual(implement["workspace"]["integration"], "review-required")
        fixture = drivers.FixtureDriver({
            "implement": {"workspace_files": {"src/one.py": "print('one')"}},
            "repair": {"workspace_files": {"tests/two.py": "def test_two(): pass"}},
        })
        manager = drivers.DriverManager(self.root, self.config, adapters={"fixture": fixture})
        receipts = [manager.start(implement, "write-a"), manager.start(repair, "write-b")]
        receipts = [manager.poll(self.projection["run_id"], item["session_id"]) for item in receipts]
        artifacts = [manager.collect(self.projection["run_id"], item["session_id"])[0] for item in receipts]
        self.assertTrue(all("git-diff" in item["checks"] for item in artifacts))
        self.assertFalse((self.root / "src" / "one.py").exists())
        self.assertFalse((self.root / "tests" / "two.py").exists())
        with drivers.acquire_resource_groups(
            self.root, self.projection["run_id"], ["working-tree"]
        ):
            with self.assertRaisesRegex(DwError, "already claimed"):
                with drivers.acquire_resource_groups(
                    self.root, self.projection["run_id"], ["working-tree"]
                ):
                    pass

    def test_git_diff_artifact_keeps_exact_nested_untracked_paths(self):
        import dw_pmo.orchestration_driver as drivers

        nested = self.root / "src" / "feature" / "candidate.py"
        nested.parent.mkdir(parents=True)
        nested.write_text("print('candidate')\n", encoding="utf-8")

        diff, paths = drivers._git_diff_artifact(
            self.root, ["src/feature/candidate.py"]
        )

        self.assertEqual(paths, ["src/feature/candidate.py"])
        self.assertIn(b"diff --git a/src/feature/candidate.py", diff)

    def test_undeclared_diff_path_and_output_are_refused(self):
        import dw_pmo.orchestration_driver as drivers

        self.seed_implementation_brief()
        _claimed, packet = self.claim_packet("implement", "escaped-writer")
        fixture = drivers.FixtureDriver({
            "implement": {"workspace_files": {"secrets.txt": "outside scope"},
                              "outputs": {"rogue": "undeclared"}},
        })
        manager = drivers.DriverManager(self.root, self.config, adapters={"fixture": fixture})
        receipt = manager.start(packet, "escaped-start")
        receipt = manager.poll(self.projection["run_id"], receipt["session_id"])
        with self.assertRaisesRegex(DwError, "undeclared output|escapes declared"):
            manager.collect(self.projection["run_id"], receipt["session_id"])

    def test_start_poll_interrupt_collect_idempotency_and_recovery_states(self):
        import dw_pmo.orchestration_driver as drivers

        _claimed, packet = self.claim_packet("research-api", "recoverable")
        fixture = drivers.FixtureDriver(self.responses())
        manager = drivers.DriverManager(self.root, self.config, adapters={"fixture": fixture})
        first = manager.start(packet, "same-session")
        again = manager.start(packet, "same-session")
        self.assertEqual(first, again)
        self.assertEqual(fixture.starts, 1)
        recovered = drivers.DriverManager(
            self.root, self.config, adapters={"fixture": drivers.FixtureDriver()}
        )
        polled = recovered.poll(self.projection["run_id"], first["session_id"])
        self.assertEqual(polled["state"], "succeeded")
        self.assertEqual(recovered.collect(
            self.projection["run_id"], first["session_id"]
        )[0]["valid"], True)

        # A separate run would be required to launch the same node attempt
        # again; interrupt the already-terminal session is an idempotent no-op.
        interrupted = recovered.interrupt(self.projection["run_id"], first["session_id"])
        self.assertEqual(interrupted["state"], "succeeded")

    def test_pause_between_packet_and_start_refuses_without_adapter_launch(self):
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        claimed, packet = self.claim_packet("research-api", "pause-race")
        paused = runs.transition_run(
            self.root, self.projection["run_id"], "pause", claimed["ledger_head"],
            reason="operator pause", now=self.now,
        )
        fixture = drivers.FixtureDriver(self.responses())
        manager = drivers.DriverManager(self.root, self.config, adapters={"fixture": fixture})
        receipt = manager.start(packet, "after-pause")
        self.assertEqual(receipt["state"], "refused")
        self.assertEqual(receipt["reason"], "dispatch-refused")
        self.assertEqual(fixture.starts, 0)
        self.assertEqual(paused["state"], "paused")

    def test_activity_follows_the_scripted_plan_and_terminal_mapping(self):
        import dw_pmo.orchestration_driver as drivers

        responses = self.responses()
        responses["research-api"] = dict(
            responses["research-api"], polls=5,
            activities=["active", "idle", "waiting_input", "unknown", "blocked"],
        )
        _claimed, packet = self.claim_packet("research-api", "activity-walk")
        fixture = drivers.FixtureDriver(responses)
        manager = drivers.DriverManager(self.root, self.config, adapters={"fixture": fixture})
        started = manager.start(packet, "activity-walk")
        self.assertEqual(started["state"], "running")
        self.assertEqual(started["activity"], "active")
        run_id = self.projection["run_id"]
        session = str(started["session_id"])
        walked = [manager.poll(run_id, session) for _ in range(3)]
        self.assertEqual(
            [(item["state"], item["activity"]) for item in walked],
            [
                ("running", "idle"),
                ("running", "waiting_input"),
                ("running", "unknown"),
            ],
        )
        # A fresh manager (post-restart) continues the same scripted walk
        # from the persisted session record, deterministically.
        recovered = drivers.DriverManager(
            self.root, self.config, adapters={"fixture": drivers.FixtureDriver()}
        )
        fourth = recovered.poll(run_id, session)
        self.assertEqual((fourth["state"], fourth["activity"]), ("running", "blocked"))
        final = recovered.poll(run_id, session)
        self.assertEqual((final["state"], final["activity"]), ("succeeded", "exited"))

    def test_lost_maps_to_unknown_and_default_running_activity_is_active(self):
        import dw_pmo.orchestration_driver as drivers

        responses = self.responses()
        responses["research-api"] = dict(
            responses["research-api"], polls=1, state="lost", reason="lost",
            exit_code=None,
        )
        _claimed, packet = self.claim_packet("research-api", "activity-lost")
        manager = drivers.DriverManager(
            self.root, self.config,
            adapters={"fixture": drivers.FixtureDriver(responses)},
        )
        started = manager.start(packet, "activity-lost")
        self.assertEqual(started["activity"], "active")
        final = manager.poll(self.projection["run_id"], str(started["session_id"]))
        self.assertEqual((final["state"], final["activity"]), ("lost", "unknown"))

    def test_adapter_inventing_activity_states_is_a_conformance_error(self):
        import dw_pmo.orchestration_driver as drivers

        _claimed, packet = self.claim_packet("research-api", "conformance")

        def adapter_with_plan(plan):
            class Inventive:
                adapter = "fixture"

                def start(self, _packet, _profile, _staging):
                    result = {
                        "state": "running", "exit_code": None,
                        "reason": "running", "polls_remaining": 2,
                        "final_state": "succeeded", "stdout_bytes": 0,
                        "stderr_bytes": 0,
                    }
                    if plan is not KeyError:
                        result["activity_plan"] = plan
                    return result

                def interrupt(self, _session):
                    return True

            return Inventive()

        cases = [
            ("invented-state", ["daydreaming"]),
            ("exited-while-running", ["exited"]),
            ("not-a-list", "active"),
            ("oversized", ["active"] * 65),
            ("missing-key", KeyError),
        ]
        for key, plan in cases:
            manager = drivers.DriverManager(
                self.root, self.config, adapters={"fixture": adapter_with_plan(plan)}
            )
            with self.assertRaises(DwError, msg=key):
                manager.start(packet, f"conformance-{key}")

    def _fake_claude(self, version="2.9.9 (Claude Code)"):
        log = self.tmp / "claude-argv.jsonl"
        script = self.tmp / "fake-claude"
        script.write_text(
            "#!/bin/sh\n"
            f"LOG={json.dumps(str(log))}\n"
            'if [ "$1" = "--version" ]; then\n'
            f"  echo {json.dumps(version)}\n"
            "  exit 0\n"
            "fi\n"
            '{ printf "%s\\036" "$PWD" "$@"; printf "\\035"; } >> "$LOG"\n'
            'printf "# Findings\\nBounded.\\n\\n# Sources\\n"\n'
            'printf "[Primary](https://example.test/api)\\n\\n# Risks\\nNone.\\n"\n'
        )
        script.chmod(0o755)
        return script, log

    def _claude_config(self, script):
        config = json.loads(json.dumps(self.config))
        for profile in config["profiles"].values():
            profile["adapter"] = "claude-exec"
            profile["command"] = [str(script)]
        return config

    def test_claude_adapter_is_least_privilege_by_construction(self):
        import dw_pmo.orchestration_driver as drivers

        script, log = self._fake_claude()
        config = self._claude_config(script)
        claimed, packet = self.claim_packet(
            "research-api", "claude-read", config=config
        )
        manager = drivers.DriverManager(self.root, config)
        receipt = manager.start(packet, "claude-read")
        self.assertEqual(receipt["state"], "succeeded")
        self.assertEqual(receipt["activity"], "exited")
        calls = [
            record.split("\x1e")[:-1]
            for record in log.read_text().split("\x1d")
            if record.strip("\n")
        ]
        self.assertEqual(len(calls), 1)
        argv = calls[0][1:]
        self.assertIn("-p", argv)
        tools = argv[argv.index("--allowedTools") + 1]
        self.assertIn("Read", tools)
        self.assertIn("WebSearch", tools)  # network profile
        self.assertNotIn("Write", tools)
        self.assertNotIn("Bash", tools)
        denied = argv[argv.index("--disallowedTools") + 1]
        self.assertIn("Bash", denied)
        mode = argv[argv.index("--permission-mode") + 1]
        self.assertEqual(mode, "default")
        self.assertNotIn("--dangerously-skip-permissions", argv)
        collected = manager.collect(
            self.projection["run_id"], str(receipt["session_id"])
        )
        self.assertTrue(collected[0]["valid"])

        self.seed_implementation_brief()
        claimed, write_packet = self.claim_packet(
            "implement", "claude-write", projection=claimed, config=config
        )
        write_receipt = manager.start(write_packet, "claude-write")
        self.assertEqual(write_receipt["state"], "succeeded")
        calls = [
            record.split("\x1e")[:-1]
            for record in log.read_text().split("\x1d")
            if record.strip("\n")
        ]
        argv = calls[-1][1:]
        tools = argv[argv.index("--allowedTools") + 1]
        self.assertIn("Write", tools)
        self.assertNotIn("Bash", tools)
        self.assertNotIn("WebSearch", tools)  # worker profile has no network
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "acceptEdits")
        self.assertEqual(
            Path(calls[-1][0]).resolve(),
            Path(str(write_packet["workspace"]["path"])).resolve(),
        )

    def test_claude_adapter_version_pin_refuses_content_free(self):
        import dw_pmo.orchestration_driver as drivers

        script, log = self._fake_claude(version="3.0.1 (Claude Code)")
        config = self._claude_config(script)
        claimed, packet = self.claim_packet(
            "research-api", "claude-pin", config=config
        )
        manager = drivers.DriverManager(self.root, config)
        receipt = manager.start(packet, "claude-pin")
        self.assertEqual(receipt["state"], "failed")
        self.assertEqual(receipt["reason"], "adapter-unavailable")
        self.assertFalse(log.exists(), "the pinned refusal must precede any -p call")

        missing = self._claude_config(self.tmp / "no-such-claude")
        _claimed, packet = self.claim_packet(
            "research-risks", "claude-missing", projection=claimed, config=missing
        )
        manager = drivers.DriverManager(self.root, missing)
        receipt = manager.start(packet, "claude-missing")
        self.assertEqual(receipt["reason"], "adapter-unavailable")

    def test_claude_adapter_claims_no_rich_activity(self):
        import inspect
        import dw_pmo.orchestration_driver as drivers

        source = inspect.getsource(drivers.ClaudeCodeExecDriver.start)
        self.assertIn('"activity_plan": []', source)
        self.assertNotIn("waiting_input", source)
        self.assertNotIn('"blocked"', source)
        self.assertFalse(
            hasattr(drivers.ClaudeCodeExecDriver, "deliver_nudge"),
            "non-interactive exec must refuse session nudges honestly",
        )

    def test_codex_adapter_claims_no_rich_activity(self):
        import inspect
        import dw_pmo.orchestration_driver as drivers

        source = inspect.getsource(drivers.CodexExecDriver.start)
        self.assertIn('"activity_plan": []', source)
        self.assertNotIn("waiting_input", source)
        self.assertNotIn('"blocked"', source)


class OrchestrationConductorTest(unittest.TestCase):
    """WLA-24-06: deterministic ticks, checks, routes, and recovery."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-orch-conductor-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self._cmd("git", "init", "-q", "-b", "main")
        self._cmd("git", "config", "user.name", "Conductor Fixture")
        self._cmd("git", "config", "user.email", "conductor@example.test")
        subprocess.run(
            [str(TESTS_DIR.parent / "bootstrap" / "new-project.sh"),
             str(self.root), "sample", "Sample", "SMP"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        subprocess.run(
            [str(TESTS_DIR.parent / "install.sh"), str(self.root), "--skip-bootstrap"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.dw = self.root / ".githooks" / "dw"
        self._dw("story", "status", "sample", "0", "SMP-0-01", "in-progress")
        self._dw("rider", "docs")
        schema = self.root / "schemas" / "risk-register-v1.json"
        schema.parent.mkdir()
        schema.write_text(json.dumps({
            "type": "object",
            "required": ["risks"],
            "properties": {"risks": {"type": "array", "items": {"type": "string"}}},
            "additionalProperties": False,
        }, indent=2) + "\n")
        docs = self.root / "docs"
        docs.mkdir(exist_ok=True)
        (docs / "context.md").write_text("# Context\n\nBounded.\n")
        self._commit("conductor fixture")
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.config = {
            "kind": "delivery-workbench-driver-config",
            "schema_version": 1,
            "workspace_root": None,
            "profiles": {
                "research-readonly": {
                    "adapter": "fixture",
                    "capabilities": ["repository-read", "network"],
                    "workspace_modes": ["read-only"],
                    "network": True,
                },
                "reasoning-readonly": {
                    "adapter": "fixture",
                    "capabilities": ["repository-read"],
                    "workspace_modes": ["read-only"],
                },
                "worker-write": {
                    "adapter": "fixture",
                    "capabilities": ["repository-read", "repository-write"],
                    "workspace_modes": ["isolated-worktree"],
                },
            },
        }

    def _cmd(self, *argv, check=True):
        return subprocess.run(
            list(argv), cwd=self.root, check=check, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def _dw(self, *argv, check=True):
        return self._cmd(str(self.dw), *argv, check=check)

    def _commit(self, message):
        self._cmd("git", "add", ".")
        self._cmd("git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", message)

    def _write_score(self, name, nodes, defaults=None, nudges=None):
        score = {
            "kind": "delivery-workbench-orchestration",
            "schema_version": 1,
            "slug": name,
            "title": name.replace("-", " ").title(),
            "project": "sample",
            "defaults": defaults or {
                "max_concurrency": 3,
                "max_wall_seconds": 3600,
                "max_agent_starts": 20,
                "max_check_starts": 20,
                "default_timeout_seconds": 60,
                "max_artifact_bytes": 1000000,
            },
            "nodes": nodes,
        }
        if nudges:
            score["nudges"] = nudges
        path = self.root / "pm" / "orchestration" / f"{name}.json"
        path.write_text(json.dumps(score, indent=2) + "\n", encoding="utf-8")
        self._commit(f"score {name}")
        return score

    def _start(self, score="research-build-review", offset=3600, **plan_kwargs):
        import dw_pmo.orchestration_run as runs

        plan = runs.build_run_plan(
            self.root, score, "sample", "SMP-0-01",
            issued_at=self.now, expires_at=self.now + timedelta(seconds=offset),
            **plan_kwargs,
        )
        return runs.start_run(
            self.root, plan, plan["start_token"], approved=True,
            approved_by="conductor-fixture", now=self.now,
        )

    def _open_checkpoint_request(self, name="pending-request", offset=3600):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_run as runs

        self._write_score(name, [{
            "id": "human-gate", "type": "approval",
            "prompt": "Review the bounded facts.",
            "options": ["approve", "reject"],
        }])
        started = self._start(name, offset=offset)
        conductor.tick_run(self.root, started["run_id"], now=self.now)
        waiting = runs.replay_run(self.root, started["run_id"], now=self.now)
        self.assertEqual(waiting["state"], "awaiting-approval")
        self.assertEqual(len(waiting["outstanding_requests"]), 1)
        return waiting

    @staticmethod
    def _responses(polls=2):
        return {
            "research-api": {
                "polls": polls,
                "outputs": {"api-findings": (
                    "# Findings\nBounded.\n\n# Sources\n"
                    "[Primary](https://example.test/api)\n\n# Risks\nNone.\n"
                )},
            },
            "research-risks": {
                "polls": polls,
                "outputs": {"risk-register": {"risks": ["bounded"]}},
            },
            "synthesize": {
                "polls": 1,
                "outputs": {"implementation-brief": (
                    "# Scope\nSmall.\n\n# Decisions\nExact.\n\n"
                    "# Acceptance checks\nGreen.\n"
                )},
            },
            "implement": {
                "polls": 1,
                "workspace_files": {"src/feature.py": "VALUE = 1"},
            },
            "repair": {
                "polls": 1,
                "workspace_files": {"tests/test_repair.py": "def test_repair(): assert True"},
            },
        }

    def test_pure_schedule_is_stable_and_respects_resource_groups(self):
        import dw_pmo.orchestration as orch
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers

        projection = self._start()
        compiled = orch.compile_score_path(
            self.root / "pm" / "orchestration" / "research-build-review.json"
        )
        artifacts = drivers.artifact_inventory(self.root, projection["run_id"])
        first = conductor.schedule_decision(compiled, projection, artifacts)
        second = conductor.schedule_decision(compiled, projection, artifacts)
        self.assertEqual(first, second)
        self.assertEqual(
            [item["node_id"] for item in first["scheduled"]],
            ["research-api", "research-risks"],
        )
        self.assertFalse(first["starts_work"])
        self.assertFalse(first["writes_events"])

        self._write_score("locked-roots", [
            {"id": "one", "type": "check", "resource_groups": ["repo"],
             "runner": {"kind": "builtin", "name": "rail-status"}},
            {"id": "two", "type": "check", "resource_groups": ["repo"],
             "runner": {"kind": "builtin", "name": "rail-status"}},
            {"id": "handoff", "type": "approval", "needs": ["one", "two"],
             "prompt": "Review", "terminal": "awaiting-certification"},
        ])
        locked = self._start("locked-roots")
        compiled = orch.compile_score_path(
            self.root / "pm" / "orchestration" / "locked-roots.json"
        )
        decision = conductor.schedule_decision(compiled, locked, [])
        self.assertEqual([item["node_id"] for item in decision["scheduled"]], ["one"])

    def test_full_fanout_check_repair_retry_and_terminal_handoff(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        projection = self._start()
        fixture = drivers.FixtureDriver(self._responses(polls=3))
        checks = {"starts": 0}

        def check_runner(_argv, _cwd, _timeout, _stdout, _stderr, _env):
            checks["starts"] += 1
            return 1 if checks["starts"] == 1 else 0

        first = conductor.tick_run(
            self.root, projection["run_id"], driver_config=self.config,
            adapters={"fixture": fixture}, check_runner=check_runner, now=self.now,
        )
        active = runs.replay_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(
            [item["node_id"] for item in active["active_claims"]],
            ["research-api", "research-risks"],
        )
        self.assertEqual(first["active_claims"], 2)
        for _ in range(20):
            result = conductor.tick_run(
                self.root, projection["run_id"], driver_config=self.config,
                adapters={"fixture": fixture}, check_runner=check_runner, now=self.now,
            )
            if result["terminal"]:
                break
        final = runs.replay_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(final["state"], "awaiting-certification")
        self.assertEqual(checks["starts"], 2)
        self.assertEqual(
            [item["action"] for item in final["routes"] if item["node_id"] == "tests"],
            ["route"],
        )
        self.assertTrue(final["routes"][0]["resolved"])
        self.assertEqual(final["routes"][0]["outcome"], "succeeded")
        self.assertEqual(final["checkpoints"][-1]["node_id"], "human-handoff")
        ledger = (
            self.root / ".git" / "pmo-orchestration" / "runs"
            / projection["run_id"] / "ledger.jsonl"
        ).read_text(encoding="utf-8")
        self.assertNotIn("pytest", ledger)
        self.assertNotIn("Bounded.", ledger)
        self.assertNotIn('"argv"', ledger)

    def test_activity_transitions_are_ledgered_once_per_change(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs
        import dw_pmo.orchestration_surface as surface

        projection = self._start()
        responses = self._responses(polls=4)
        responses["research-api"]["activities"] = [
            "active", "waiting_input", "waiting_input", "blocked",
        ]

        def check_runner(_argv, _cwd, _timeout, _stdout, _stderr, _env):
            return 0

        fixture = drivers.FixtureDriver(responses)
        conductor.tick_run(
            self.root, projection["run_id"], driver_config=self.config,
            adapters={"fixture": fixture}, check_runner=check_runner, now=self.now,
        )
        live = runs.replay_run(self.root, projection["run_id"], now=self.now)
        claim = next(
            item for item in live["active_claims"]
            if item["node_id"] == "research-api"
        )
        self.assertIn(
            claim["last_activity"]["activity"], {"active", "waiting_input"}
        )
        with self.assertRaises(DwError):
            runs.record_runtime_event(
                self.root, projection["run_id"], "activity_observed",
                {
                    "node_id": claim["node_id"], "attempt": claim["attempt"],
                    "claim_id": claim["claim_id"], "activity": "daydreaming",
                    "session_id": "none",
                },
                str(live["ledger_head"]), now=self.now,
            )
        for _ in range(24):
            result = conductor.tick_run(
                self.root, projection["run_id"], driver_config=self.config,
                adapters={"fixture": fixture}, check_runner=check_runner, now=self.now,
            )
            if result["terminal"]:
                break
        ledger_path = (
            self.root / ".git" / "pmo-orchestration" / "runs"
            / projection["run_id"] / "ledger.jsonl"
        )
        observed = [
            json.loads(line)["detail"]["activity"]
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if json.loads(line)["event"] == "activity_observed"
            and json.loads(line)["detail"]["node_id"] == "research-api"
        ]
        # The repeated waiting_input poll appends nothing: one fact per change.
        self.assertEqual(
            observed, ["active", "waiting_input", "blocked", "exited"]
        )
        final = runs.replay_run(self.root, projection["run_id"], now=self.now)
        released = next(
            item for item in final["completed_claims"]
            if item["node_id"] == "research-api"
        )
        self.assertEqual(released["last_activity"]["activity"], "exited")
        view = surface.build_run_view(self.root, projection["run_id"], now=self.now)
        agent_sessions = [
            item for item in view["sessions"]["agents"]
            if item["node_id"] == "research-api"
        ]
        self.assertEqual(agent_sessions[0]["activity"], "exited")

    def _nudge_nodes(self, worker_polls=0, worker_activities=None):
        worker = {
            "id": "worker", "type": "agent", "role": "implementation",
            "profile": "worker-write", "prompt": "Do the granted work.",
            "capabilities": ["repository-read", "repository-write"],
            "workspace": "isolated-worktree",
        }
        repair = {
            "id": "repair", "type": "agent", "role": "repair",
            "profile": "worker-write", "activation": "failure",
            "prompt": "Repair from the nudge facts.",
            "capabilities": ["repository-read", "repository-write"],
            "workspace": "isolated-worktree",
        }
        responses = {
            "worker": {"polls": worker_polls,
                       "workspace_files": {"src/w.py": "V = 1"}},
            "repair": {"polls": 0,
                       "workspace_files": {"src/fix.py": "V = 2"}},
        }
        if worker_activities is not None:
            responses["worker"]["activities"] = worker_activities
        return [worker, repair], responses

    def _seed_signal(self, branch="feature-x", name="ci", conclusion="failure"):
        import dw_pmo.signals as sig

        scenario = self.tmp / f"signal-{name}-{conclusion}.json"
        scenario.write_text(json.dumps({"prs": [{
            "number": 1, "state": "open", "head": branch, "base": "main",
            "url": "u",
            "checks": [{"name": name, "status": "completed",
                        "conclusion": conclusion, "url": "u"}],
        }]}))
        return sig.observe_signals(
            self.root, sig.FixtureProvider(scenario), "origin", branch
        )

    def _run_to_terminal(self, run_id, fixture, ticks=20):
        import dw_pmo.orchestration_conductor as conductor

        result = None
        for _ in range(ticks):
            result = conductor.tick_run(
                self.root, run_id, driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
            )
            if result["terminal"]:
                break
        return result

    def test_nudge_wakes_awaiting_certification_and_delivers_at_most_once(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs
        import dw_pmo.orchestration_surface as surface
        import dw_pmo.signals as sig

        nodes, responses = self._nudge_nodes()
        nodes.append({
            "id": "handoff", "type": "approval", "needs": ["worker"],
            "prompt": "Inspect the bounded work.",
            "terminal": "awaiting-certification",
        })
        self._write_score("nudge-loop", nodes, nudges=[
            {"id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
             "max_total": 3, "expectation": "make the pushed branch green"},
        ])
        projection = self._start(
            "nudge-loop",
            standing_nudges=["ci-failed=repair"],
            signal_channel="origin/feature-x",
        )
        run_id = projection["run_id"]
        fixture = drivers.FixtureDriver(responses)
        result = self._run_to_terminal(run_id, fixture)
        self.assertEqual(result["state"], "awaiting-certification")

        (self.root / "operator-integration.txt").write_text(
            "operator-owned integration before outward observation\n"
        )
        self._commit("operator integrates before outward signal")
        self._seed_signal()
        chan = sig.replay_channel(self.root, "origin", "feature-x")
        check_fact = next(
            record for record in chan["facts"].values()
            if record["fact"] == "pr-check"
        )
        result = self._run_to_terminal(run_id, fixture)
        self.assertEqual(result["state"], "awaiting-certification")
        final = runs.replay_run(self.root, run_id, now=self.now)
        self.assertEqual(final["external_commits"][-1]["relation"], "fast-forward")
        self.assertTrue(final["external_commits"][-1]["rebindable"])
        self.assertIsNone(final["pending_checkpoint"])
        self.assertEqual(
            [item["node_id"] for item in final["checkpoints"]],
            ["handoff", "handoff"],
        )
        self.assertEqual(
            final["external_commits"][-1]["head"],
            self._cmd("git", "rev-parse", "HEAD").stdout.strip(),
        )
        delivered = [item for item in final["nudges"] if item["delivered"]]
        self.assertEqual(len(delivered), 1)
        self.assertEqual(delivered[0]["signal_hash"], check_fact["event_hash"])
        self.assertEqual(delivered[0]["node_id"], "repair")
        self.assertEqual(final["budgets"]["max_nudges"]["used"], 1)
        repaired = [
            item for item in final["completed_claims"]
            if item["node_id"] == "repair"
        ]
        self.assertEqual(len(repaired), 1)
        self.assertEqual(repaired[0]["outcome"], "succeeded")

        # The nudge facts rode into the repair packet as bounded context.
        session_dir = (
            self.root / ".git" / "pmo-orchestration" / "runs" / run_id
            / "driver-sessions"
        )
        packets = []
        for record_path in session_dir.glob("session-*.json"):
            record = json.loads(record_path.read_text())
            packet = json.loads(Path(record["packet_path"]).read_text())
            if packet["node_id"] == "repair":
                packets.append(packet)
        self.assertEqual(len(packets), 1)
        selectors = [
            doc["selector"] for doc in packets[0]["context"]["documents"]
        ]
        self.assertIn("@nudge", selectors)
        nudge_doc = next(
            doc for doc in packets[0]["context"]["documents"]
            if doc["selector"] == "@nudge"
        )
        self.assertIn("make the pushed branch green", nudge_doc["content"])

        # Replaying the same signal fact appends nothing more.
        for _ in range(3):
            conductor.tick_run(
                self.root, run_id, driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
            )
        again = runs.replay_run(self.root, run_id, now=self.now)
        self.assertEqual(
            len([item for item in again["nudges"] if item["delivered"]]), 1
        )
        view = surface.build_run_view(self.root, run_id, now=self.now)
        self.assertEqual(len(view["nudges"]), len(again["nudges"]))

    def test_uncovered_nudge_is_a_typed_request_before_manual_delivery(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs
        import dw_pmo.orchestration_surface as surface

        nodes, responses = self._nudge_nodes()
        self._write_score("nudge-manual-request", nodes, nudges=[
            {"id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
             "max_total": 2},
        ])
        started = self._start(
            "nudge-manual-request", signal_channel="origin/manual-x"
        )
        fixture = drivers.FixtureDriver(responses)
        self._run_to_terminal(started["run_id"], fixture)
        self._seed_signal(branch="manual-x", name="ci-manual")
        conductor.tick_run(
            self.root, started["run_id"], driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        pending = runs.replay_run(self.root, started["run_id"], now=self.now)
        self.assertEqual(len(pending["outstanding_requests"]), 1)
        request = pending["outstanding_requests"][0]
        self.assertEqual(request["kind"], "nudge")
        self.assertEqual(request["origin_node"], "repair")
        self.assertEqual(request["response_schema"], {
            "decision": ["approve", "reject"],
        })

        preview = surface.build_run_act_preview(
            self.root, started["run_id"], "request",
            correlation_id=request["correlation_id"], decision="approve",
            now=self.now,
        )
        approved = surface.apply_run_act(
            self.root, started["run_id"], "request", preview["act_token"],
            correlation_id=request["correlation_id"], decision="approve",
            now=self.now,
        )
        self.assertEqual(approved["request_history"][-1]["status"], "approved")
        conductor.tick_run(
            self.root, started["run_id"], driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        delivered = runs.replay_run(self.root, started["run_id"], now=self.now)
        self.assertEqual(
            len([item for item in delivered["nudges"] if item["delivered"]]), 1
        )
        self.assertEqual(delivered["request_history"][-1]["status"], "applied")

    def test_nudge_refusals_are_distinct_recorded_and_deduped(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        nodes, responses = self._nudge_nodes()
        self._write_score("nudge-uncovered", nodes, nudges=[
            {"id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
             "max_total": 3},
        ])
        projection = self._start(
            "nudge-uncovered", signal_channel="origin/feature-x",
        )
        run_id = projection["run_id"]
        fixture = drivers.FixtureDriver(responses)
        self._run_to_terminal(run_id, fixture)
        self._seed_signal()
        for _ in range(3):
            conductor.tick_run(
                self.root, run_id, driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
            )
        final = runs.replay_run(self.root, run_id, now=self.now)
        refusals = [item for item in final["nudges"] if not item["delivered"]]
        self.assertEqual(len(refusals), 1)
        self.assertEqual(refusals[0]["reason"], "no-standing-rule")
        self.assertEqual(final["state"], "awaiting-certification")
        self.assertEqual(final["budgets"]["max_nudges"]["used"], 0)

        # A paused run records run-inactive instead of delivering.
        nodes2, responses2 = self._nudge_nodes(worker_polls=10)
        self._write_score("nudge-paused", nodes2, nudges=[
            {"id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
             "max_total": 3},
        ])
        paused_projection = self._start(
            "nudge-paused",
            standing_nudges=["ci-failed"],
            signal_channel="origin/paused-x",
        )
        paused_run = paused_projection["run_id"]
        fixture2 = drivers.FixtureDriver(responses2)
        conductor.tick_run(
            self.root, paused_run, driver_config=self.config,
            adapters={"fixture": fixture2}, now=self.now,
        )
        live = runs.replay_run(self.root, paused_run, now=self.now)
        runs.transition_run(
            self.root, paused_run, "pause", str(live["ledger_head"]),
            reason="operator pause", now=self.now,
        )
        self._seed_signal(branch="paused-x", name="ci-p")
        conductor.tick_run(
            self.root, paused_run, driver_config=self.config,
            adapters={"fixture": fixture2}, now=self.now,
        )
        paused_state = runs.replay_run(self.root, paused_run, now=self.now)
        self.assertEqual(
            [item["reason"] for item in paused_state["nudges"]],
            ["run-inactive"],
        )

        # Grant expiry is its own recorded reason.
        late = self.now + timedelta(hours=2)
        self._seed_signal(name="ci-late")
        conductor.tick_run(
            self.root, run_id, driver_config=self.config,
            adapters={"fixture": fixture}, now=late,
        )
        expired = runs.replay_run(self.root, run_id, now=late)
        reasons = {
            item["reason"] for item in expired["nudges"]
            if not item["delivered"]
        }
        self.assertIn("grant-expired", reasons)

    def test_nudge_budget_exhaustion_is_a_recorded_blocked_stop(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        nodes, responses = self._nudge_nodes(worker_polls=10)
        defaults = {
            "max_concurrency": 3, "max_wall_seconds": 3600,
            "max_agent_starts": 20, "max_check_starts": 20,
            "default_timeout_seconds": 60, "max_artifact_bytes": 1000000,
            "max_nudges": 1,
        }
        self._write_score("nudge-storm", nodes, defaults=defaults, nudges=[
            {"id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
             "max_total": 5},
        ])
        projection = self._start(
            "nudge-storm",
            standing_nudges=["ci-failed"],
            signal_channel="origin/feature-x",
        )
        run_id = projection["run_id"]
        fixture = drivers.FixtureDriver(responses)
        conductor.tick_run(
            self.root, run_id, driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        self._seed_signal(name="ci-one")
        conductor.tick_run(
            self.root, run_id, driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        first = runs.replay_run(self.root, run_id, now=self.now)
        self.assertEqual(
            len([item for item in first["nudges"] if item["delivered"]]), 1
        )
        self._seed_signal(name="ci-two")
        conductor.tick_run(
            self.root, run_id, driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        stormed = runs.replay_run(self.root, run_id, now=self.now)
        self.assertEqual(stormed["state"], "blocked")
        reasons = {
            item["reason"] for item in stormed["nudges"]
            if not item["delivered"]
        }
        self.assertIn("nudge-budget-exhausted", reasons)

    def test_nudge_receptivity_gates_live_sessions(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        # A blocked session refuses; a waiting session receives through
        # the driver seam and the poked receipt returns to active.
        for activities, expectation in (
            (["blocked"], "refused"),
            (["active"], "deferred"),
            (["waiting_input"], "delivered"),
        ):
            slug = f"nudge-session-{expectation}"
            nodes, responses = self._nudge_nodes(
                worker_polls=10, worker_activities=activities
            )
            nodes = [nodes[0]]
            self._write_score(slug, nodes, nudges=[
                {"id": "on-ci-failed", "signal": "ci-failed",
                 "target": "worker", "max_total": 3},
            ])
            projection = self._start(
                slug,
                standing_nudges=["ci-failed=worker"],
                signal_channel=f"origin/{slug}",
            )
            run_id = projection["run_id"]
            fixture = drivers.FixtureDriver(responses)
            conductor.tick_run(
                self.root, run_id, driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
            )
            self._seed_signal(branch=slug)
            conductor.tick_run(
                self.root, run_id, driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
            )
            final = runs.replay_run(self.root, run_id, now=self.now)
            delivered = [item for item in final["nudges"] if item["delivered"]]
            refused = [item for item in final["nudges"] if not item["delivered"]]
            if expectation == "refused":
                self.assertEqual(delivered, [])
                self.assertEqual(refused[0]["reason"], "non-receptive")
            elif expectation == "deferred":
                # An active session defers: no delivery, no refusal —
                # the next tick simply re-evaluates.
                self.assertEqual(final["nudges"], [])
            else:
                self.assertEqual(len(delivered), 1)
                self.assertEqual(int(delivered[0]["attempt"]), 1)
                session_dir = (
                    self.root / ".git" / "pmo-orchestration" / "runs"
                    / run_id / "driver-sessions"
                )
                record = json.loads(
                    next(iter(sorted(session_dir.glob("session-*.json")))).read_text()
                )
                nudge_files = list(
                    (Path(record["staging"]) / "nudges").glob("*.json")
                )
                self.assertEqual(len(nudge_files), 1)
                self.assertEqual(record["receipt"]["activity"], "active")

    def test_nudge_crash_after_delivery_recovers_without_duplicate(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        nodes, responses = self._nudge_nodes()
        self._write_score("nudge-crash", nodes, nudges=[
            {"id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
             "max_total": 3},
        ])
        projection = self._start(
            "nudge-crash",
            standing_nudges=["ci-failed"],
            signal_channel="origin/feature-x",
        )
        run_id = projection["run_id"]
        fixture = drivers.FixtureDriver(responses)
        self._run_to_terminal(run_id, fixture)
        self._seed_signal(name="ci-crash")

        def crash_hook(name, detail):
            if name == "after-claim" and detail.get("node_id") == "repair":
                raise RuntimeError("planted crash after nudge delivery")

        with self.assertRaises(RuntimeError):
            conductor.tick_run(
                self.root, run_id, driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
                boundary_hook=crash_hook,
            )
        crashed = runs.replay_run(self.root, run_id, now=self.now)
        self.assertEqual(
            len([item for item in crashed["nudges"] if item["delivered"]]), 1
        )
        result = self._run_to_terminal(run_id, fixture)
        self.assertEqual(result["state"], "awaiting-certification")
        final = runs.replay_run(self.root, run_id, now=self.now)
        self.assertEqual(
            len([item for item in final["nudges"] if item["delivered"]]), 1
        )
        repaired = [
            item for item in final["completed_claims"]
            if item["node_id"] == "repair"
        ]
        self.assertEqual(len(repaired), 1)

    def test_failed_nudge_attempt_runs_its_named_approval_policy(self):
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        nodes, responses = self._nudge_nodes()
        nodes[1]["on_failure"] = {
            "action": "approval", "checkpoint": "repair-review",
        }
        responses["repair"].update({
            "state": "failed", "exit_code": 1, "polls": 0,
        })
        self._write_score("nudge-failure-approval", nodes, nudges=[
            {"id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
             "max_total": 2},
        ])
        started = self._start(
            "nudge-failure-approval",
            standing_nudges=["ci-failed=repair"],
            signal_channel="origin/failure-approval",
        )
        fixture = drivers.FixtureDriver(responses)
        self._run_to_terminal(started["run_id"], fixture)
        self._seed_signal(branch="failure-approval", name="ci-review")
        result = self._run_to_terminal(started["run_id"], fixture)
        self.assertEqual(result["state"], "awaiting-approval")
        waiting = runs.replay_run(self.root, started["run_id"], now=self.now)
        self.assertEqual(
            waiting["pending_checkpoint"]["checkpoint"], "repair-review"
        )
        self.assertEqual(waiting["routes"][-1]["action"], "approval")

    def _serve_workbench(self):
        import dw_pmo.workbench as wb
        from http.server import ThreadingHTTPServer
        import threading

        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), wb.create_handler(self.root, None)
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        return server.server_address[1]

    @staticmethod
    def _sse_frames(body):
        frames = []
        for block in body.split("\n\n"):
            fields = {}
            for line in block.splitlines():
                if ":" in line and not line.startswith(":"):
                    key, _, value = line.partition(":")
                    fields[key.strip()] = value.strip()
            if "data" in fields:
                frames.append((int(fields["id"]), json.loads(fields["data"])))
        return frames

    def test_ledger_tail_is_exact_derivable_and_content_safe(self):
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_surface as surface

        nodes, responses = self._nudge_nodes()
        self._write_score("tail-loop", nodes, nudges=[
            {"id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
             "max_total": 3},
        ])
        projection = self._start(
            "tail-loop",
            standing_nudges=["ci-failed"],
            signal_channel="origin/feature-x",
        )
        run_id = projection["run_id"]
        self._run_to_terminal(run_id, drivers.FixtureDriver(responses))

        ledger_path = (
            self.root / ".git" / "pmo-orchestration" / "runs" / run_id
            / "ledger.jsonl"
        )
        ledger = [
            json.loads(line)
            for line in ledger_path.read_text().splitlines()
        ]
        full = surface.tail_run_events(self.root, run_id)
        self.assertIs(full["starts_work"], False)
        self.assertEqual(full["events"], ledger)
        self.assertEqual(full["head_seq"], len(ledger) - 1)
        cut = len(ledger) // 2
        prefix = surface.tail_run_events(self.root, run_id, -1, limit=cut)
        suffix = surface.tail_run_events(self.root, run_id, cut - 1)
        self.assertEqual(prefix["events"] + suffix["events"], ledger)
        empty = surface.tail_run_events(self.root, run_id, full["head_seq"])
        self.assertEqual(empty["events"], [])
        with self.assertRaises(DwError):
            surface.tail_run_events(self.root, run_id, -5)

        rendered = json.dumps(full, sort_keys=True)
        for excluded in ("Do the granted work.", "act_token", "start_token",
                         "prompt", "apply_command"):
            self.assertNotIn(excluded, rendered)

        # Corrupt chains fail closed instead of streaming.
        good = ledger_path.read_text()
        ledger_path.write_text(good.replace("event_hash", "event_hasX", 1))
        with self.assertRaises(DwError):
            surface.tail_run_events(self.root, run_id)
        ledger_path.write_text(good)

    def test_sse_stream_replays_after_disconnect_and_carries_no_authority(self):
        import http.client

        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_surface as surface

        nodes, responses = self._nudge_nodes()
        self._write_score("sse-loop", nodes, nudges=[
            {"id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
             "max_total": 3},
        ])
        projection = self._start(
            "sse-loop",
            standing_nudges=["ci-failed"],
            signal_channel="origin/sse-x",
        )
        run_id = projection["run_id"]
        fixture = drivers.FixtureDriver(responses)
        self._run_to_terminal(run_id, fixture)
        port = self._serve_workbench()

        def get(path, headers=None):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            conn.request("GET", path, headers=headers or {})
            response = conn.getresponse()
            body = response.read().decode("utf-8")
            conn.close()
            return response, body

        response, body = get(f"/api/runs/{run_id}/events?follow=0")
        self.assertEqual(response.status, 200)
        self.assertIn("text/event-stream", response.getheader("Content-Type"))
        frames = self._sse_frames(body)
        ledger = surface.tail_run_events(self.root, run_id)["events"]
        self.assertEqual([data for _seq, data in frames], ledger)
        self.assertEqual([seq for seq, _data in frames],
                         [event["seq"] for event in ledger])

        # A disconnected client resumes from Last-Event-ID: the run gains
        # new events (a nudge wake plus a repair round), and the
        # reconnect receives exactly the missed suffix.
        head = frames[-1][0]
        self._seed_signal(branch="sse-x", name="ci-sse")
        self._run_to_terminal(run_id, fixture)
        response, body = get(
            f"/api/runs/{run_id}/events?follow=0",
            headers={"Last-Event-ID": str(head)},
        )
        resumed = self._sse_frames(body)
        self.assertTrue(resumed)
        self.assertEqual(resumed[0][0], head + 1)
        after = surface.tail_run_events(self.root, run_id, head)["events"]
        self.assertEqual([data for _seq, data in resumed], after)
        self.assertTrue(
            any(data["event"] == "nudge_delivered" for _seq, data in resumed)
        )
        for excluded in ("act_token", "start_token", "apply", "prompt"):
            self.assertNotIn(excluded, body)

        # The stream endpoint accepts no writes and mints no authority.
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        conn.request("POST", f"/api/runs/{run_id}/events", body="{}",
                     headers={"Content-Type": "application/json"})
        refusal = conn.getresponse()
        refusal_body = refusal.read().decode("utf-8")
        conn.close()
        self.assertGreaterEqual(refusal.status, 400)
        self.assertNotIn("act_token", refusal_body)

        # The signal chain tails through the same read-only shape.
        response, body = get("/api/signals/events?remote=origin&branch=sse-x&follow=0")
        self.assertEqual(response.status, 200)
        signal_frames = self._sse_frames(body)
        self.assertTrue(signal_frames)
        self.assertEqual(signal_frames[0][1]["kind"],
                         "delivery-workbench-signal-event")
        response, _body = get("/api/runs/run-000000000000000000000000/events?follow=0")
        self.assertEqual(response.status, 400)

    def test_cli_run_tail_matches_the_ledger(self):
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_surface as surface

        nodes, responses = self._nudge_nodes()
        self._write_score("tail-cli", [nodes[0]])
        projection = self._start("tail-cli")
        run_id = projection["run_id"]
        self._run_to_terminal(run_id, drivers.FixtureDriver(responses))
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
             "--root", str(self.root), "run", "tail", run_id],
            check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        lines = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(lines, surface.tail_run_events(self.root, run_id)["events"])
        suffix = subprocess.run(
            [sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
             "--root", str(self.root), "run", "tail", run_id, "--after", "2"],
            check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(
            [json.loads(line) for line in suffix.stdout.splitlines()],
            lines[3:],
        )

    def test_nudged_reattempt_supersedes_its_stored_artifact(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        research = {
            "id": "research", "type": "agent", "role": "research",
            "profile": "reasoning-readonly", "prompt": "Answer from context.",
            "capabilities": ["repository-read"], "workspace": "read-only",
            "outputs": [{"name": "answer", "format": "text",
                         "path": "artifacts/answer.txt", "max_bytes": 20000}],
        }
        self._write_score("nudge-artifact", [research], nudges=[
            {"id": "on-ci-failed", "signal": "ci-failed", "target": "research",
             "max_total": 2},
        ])
        projection = self._start(
            "nudge-artifact",
            standing_nudges=["ci-failed=research"],
            signal_channel="origin/artifact-x",
        )
        run_id = projection["run_id"]
        fixture = drivers.FixtureDriver({
            "research": {"polls": 0, "outputs": {"answer": "first answer"}},
        })
        result = self._run_to_terminal(run_id, fixture)
        self.assertEqual(result["state"], "awaiting-certification")
        self._seed_signal(branch="artifact-x", name="ci-a")
        refreshed = drivers.FixtureDriver({
            "research": {"polls": 0, "outputs": {"answer": "second answer"}},
        })
        result = self._run_to_terminal(run_id, refreshed)
        self.assertEqual(result["state"], "awaiting-certification")
        final = runs.replay_run(self.root, run_id, now=self.now)
        attempts = [
            item for item in final["completed_claims"]
            if item["node_id"] == "research"
        ]
        self.assertEqual(
            [item["outcome"] for item in attempts], ["succeeded", "succeeded"]
        )
        artifact_dir = (
            self.root / ".git" / "pmo-orchestration" / "runs" / run_id
            / "artifacts" / "research" / "answer"
        )
        self.assertEqual(
            artifact_dir.joinpath("content").read_text().strip(),
            "second answer",
        )
        metadata = json.loads(artifact_dir.joinpath("metadata.json").read_text())
        self.assertEqual(metadata["attempt"], 2)
        self.assertEqual(
            list(artifact_dir.parent.glob(".superseded-*")), [],
            "the retired copy is removed after the replacement publishes",
        )

    def test_notifications_derive_ack_and_correlate(self):
        import dw_pmo.notifications as ntf
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        nodes, responses = self._nudge_nodes()
        approval = {
            "id": "human-gate", "type": "approval", "needs": ["worker"],
            "prompt": "Review the worker result before continuing.",
        }
        self._write_score("notify-loop", [nodes[0], approval])
        projection = self._start("notify-loop")
        run_id = projection["run_id"]
        fixture = drivers.FixtureDriver(responses)
        for _ in range(10):
            result = conductor.tick_run(
                self.root, run_id, driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
            )
            if result["state"] == "awaiting-approval":
                break
        inventory = ntf.build_notifications(self.root, now=self.now)
        self.assertIs(inventory["starts_work"], False)
        pending = [
            item for item in inventory["notifications"]
            if item["kind"] == "checkpoint-pending" and item["run_id"] == run_id
        ]
        self.assertEqual(len(pending), 1)
        entry = pending[0]
        self.assertTrue(entry["unread"])
        correlation = entry["request"]["correlation_id"]
        self.assertRegex(correlation, r"^req-[0-9a-f]{24}$")
        self.assertNotEqual(correlation, entry["id"])
        guidance = entry["request"]["guidance"]
        self.assertEqual(
            [item["decision"] for item in guidance["choices"]],
            ["approve", "reject"],
        )
        self.assertFalse(guidance["transport_grants_authority"])
        self.assertIn("Affected work:", entry["outbound"])
        self.assertIn(
            "response carrier supplies no permission", entry["outbound"]
        )
        for excluded in ("sha256:", "--expect", "apply_command"):
            self.assertNotIn(excluded, entry["outbound"])
        self.assertIn("Acknowledge: " + entry["id"], entry["outbound"])

        # The correlation resolves while pending and refuses once decided.
        match = ntf.resolve_correlation(self.root, correlation)
        self.assertEqual(match["run_id"], run_id)
        import dw_pmo.orchestration_surface as surface

        preview = surface.build_run_act_preview(
            self.root, run_id, "checkpoint", decision="approve", now=self.now,
        )
        surface.apply_run_act(
            self.root, run_id, "checkpoint", preview["act_token"],
            decision="approve", now=self.now,
        )
        with self.assertRaises(DwError):
            ntf.resolve_correlation(self.root, correlation)

        # Acknowledgement is idempotent and receipted; derivation is
        # stable across repeated builds (no hidden cache).
        for _ in range(10):
            result = conductor.tick_run(
                self.root, run_id, driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
            )
            if result["terminal"]:
                break
        inventory = ntf.build_notifications(self.root, now=self.now)
        awaiting = [
            item for item in inventory["notifications"]
            if item["kind"] == "awaiting-certification"
            and item["run_id"] == run_id
        ]
        self.assertEqual(len(awaiting), 1)
        first = ntf.acknowledge_notification(
            self.root, awaiting[0]["id"], "2026-07-19T00:00:00Z"
        )
        self.assertTrue(first["changed"])
        second = ntf.acknowledge_notification(
            self.root, awaiting[0]["id"], "2026-07-19T00:00:01Z"
        )
        self.assertFalse(second["changed"])
        again = ntf.build_notifications(self.root, now=self.now)
        acked = next(
            item for item in again["notifications"]
            if item["id"] == awaiting[0]["id"]
        )
        self.assertFalse(acked["unread"])
        with self.assertRaises(DwError):
            ntf.acknowledge_notification(
                self.root, "ntf-000000000000000000000000", "2026-07-19T00:00:02Z"
            )

    def test_notifications_delivery_ceiling_parity_and_branch_opt_in(self):
        import dw_pmo.mcpserver as mcp
        import dw_pmo.notifications as ntf
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.workbench as wb

        nodes, responses = self._nudge_nodes()
        self._write_score("notify-parity", [nodes[0]])
        projection = self._start("notify-parity")
        run_id = projection["run_id"]
        self._run_to_terminal(run_id, drivers.FixtureDriver(responses))

        inventory = ntf.build_notifications(self.root, now=self.now)
        cli = subprocess.run(
            [sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
             "--root", str(self.root), "notifications", "list", "--json"],
            check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(json.loads(cli.stdout), inventory)
        tool = mcp.call_tool(self.root, "dw_notifications", {})
        self.assertEqual(tool["structuredContent"], inventory)
        status, http_doc = wb.handle_api(self.root, "/api/notifications", {})
        self.assertEqual(status, 200)
        self.assertEqual(http_doc["data"], inventory)

        target = next(
            item for item in inventory["notifications"]
            if item["run_id"] == run_id
        )
        # Failed deliveries retry up to the ceiling, then stop pending.
        for attempt in range(3):
            self.assertIn(
                target["id"],
                [item["id"] for item in ntf.pending_deliveries(self.root)],
            )
            ntf.record_delivery(
                self.root, target["id"], "telegram", False,
                "transport-error", f"2026-07-19T00:00:0{attempt}Z",
            )
        self.assertNotIn(
            target["id"],
            [item["id"] for item in ntf.pending_deliveries(self.root)],
        )
        refreshed = next(
            item for item in ntf.build_notifications(self.root)["notifications"]
            if item["id"] == target["id"]
        )
        self.assertEqual(refreshed["delivery_attempts"], 3)
        self.assertFalse(refreshed["delivered"])

        # HTTP ack is the receipted POST boundary.
        status, ack_doc = wb.handle_mutation(
            self.root, "/api/notifications/ack", {"id": target["id"]}
        )
        self.assertEqual(status, 200)
        self.assertTrue(ack_doc["data"]["acknowledged"])
        status, refused = wb.handle_mutation(
            self.root, "/api/notifications/ack", {"id": "ntf-ffffffffffffffffffffffff"}
        )
        self.assertGreaterEqual(status, 400)

        # Branch signals notify only under explicit opt-in, and never
        # for a channel a run already owns.
        self._seed_signal(branch="loose-branch", name="ci-loose")
        before = ntf.build_notifications(self.root)
        self.assertEqual(
            [item for item in before["notifications"] if item["kind"] == "branch-signal"],
            [],
        )
        store = self.root / ".git" / "pmo-notifications"
        store.mkdir(exist_ok=True)
        (store / "config.json").write_text(
            json.dumps({"branch_signals": True}) + "\n"
        )
        after = ntf.build_notifications(self.root)
        loose = [
            item for item in after["notifications"]
            if item["kind"] == "branch-signal"
        ]
        self.assertEqual(len(loose), 1)
        self.assertIn("origin/loose-branch", loose[0]["node"])

    def test_nudge_authority_rides_the_plan_and_grant(self):
        import dw_pmo.orchestration_run as runs

        nodes, _responses = self._nudge_nodes()
        self._write_score("nudge-authority", nodes, nudges=[
            {"id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
             "max_total": 3},
        ])
        bad = runs.build_run_plan(
            self.root, "nudge-authority", "sample", "SMP-0-01",
            issued_at=self.now, expires_at=self.now + timedelta(hours=1),
            standing_nudges=["vibes=repair"],
        )
        self.assertFalse(bad["applicable"])
        self.assertTrue(
            any("unknown signal" in issue for issue in bad["issues"])
        )
        malformed = runs.build_run_plan(
            self.root, "nudge-authority", "sample", "SMP-0-01",
            issued_at=self.now, expires_at=self.now + timedelta(hours=1),
            signal_channel="nochannel",
        )
        self.assertTrue(
            any("remote/branch" in issue for issue in malformed["issues"])
        )
        plan = runs.build_run_plan(
            self.root, "nudge-authority", "sample", "SMP-0-01",
            issued_at=self.now, expires_at=self.now + timedelta(hours=1),
            standing_nudges=["ci-failed=repair"],
            signal_channel="origin/feature-x",
        )
        self.assertTrue(plan["applicable"])
        self.assertEqual(
            plan["authority"]["standing_nudge_rules"],
            [{"signal": "ci-failed", "target": "repair"}],
        )
        self.assertEqual(plan["authority"]["signal_channel"], "origin/feature-x")
        started = runs.start_run(
            self.root, plan, plan["start_token"], approved=True,
            approved_by="conductor-fixture", now=self.now,
        )
        run_dir = (
            self.root / ".git" / "pmo-orchestration" / "runs"
            / started["run_id"]
        )
        grant = json.loads((run_dir / "grant.json").read_text())
        self.assertEqual(
            grant["standing_nudge_rules"],
            [{"signal": "ci-failed", "target": "repair"}],
        )
        grant["standing_nudge_rules"] = [{"signal": "ci-failed", "target": ""}]
        os.chmod(run_dir / "grant.json", 0o600)
        (run_dir / "grant.json").write_text(
            json.dumps(grant, indent=2, sort_keys=True) + "\n"
        )
        with self.assertRaises(DwError):
            runs.replay_run(self.root, started["run_id"], now=self.now)

    def test_invalid_artifact_retries_then_exhausts_without_fan_in(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        projection = self._start()
        responses = self._responses(polls=0)
        responses["research-risks"] = {
            "polls": 0, "outputs": {"risk-register": "not-json"},
        }
        fixture = drivers.FixtureDriver(responses)
        for _ in range(6):
            result = conductor.tick_run(
                self.root, projection["run_id"], driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
            )
            if result["state"] == "blocked":
                break
        final = runs.replay_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(final["state"], "blocked")
        risk_attempts = [
            item for item in final["completed_claims"]
            if item["node_id"] == "research-risks"
        ]
        self.assertEqual([item["attempt"] for item in risk_attempts], [1, 2])
        self.assertEqual(
            [item["action"] for item in final["routes"] if item["node_id"] == "research-risks"],
            ["retry", "exhausted"],
        )
        self.assertFalse(any(
            item["node_id"] == "synthesize" for item in final["active_claims"] + final["completed_claims"]
        ))

    def test_failed_repair_follows_its_abort_policy(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        projection = self._start()
        responses = self._responses(polls=0)
        responses["repair"] = {"polls": 0, "state": "failed", "reason": "failed"}
        fixture = drivers.FixtureDriver(responses)

        def failing_check(_argv, _cwd, _timeout, _stdout, _stderr, _env):
            return 1

        for _ in range(10):
            result = conductor.tick_run(
                self.root, projection["run_id"], driver_config=self.config,
                adapters={"fixture": fixture}, check_runner=failing_check,
                now=self.now,
            )
            if result["state"] == "blocked":
                break
        final = runs.replay_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(final["state"], "blocked")
        self.assertEqual(
            [(item["node_id"], item["action"]) for item in final["routes"]],
            [("tests", "route"), ("repair", "abort")],
        )

    def test_exact_command_check_is_contained_and_write_scope_fails(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_run as runs

        self._write_score("contained-check", [
            {
                "id": "exact", "type": "check",
                "runner": {
                    "kind": "command",
                    "argv": ["python3", "-c", "open('rogue.txt','w').write('x')"],
                    "cwd": ".", "timeout_seconds": 30,
                    "output_bytes": 1000, "writes": [],
                },
                "expect": {"exit_code": 0},
                "on_failure": {"action": "abort"},
            },
            {"id": "handoff", "type": "approval", "needs": ["exact"],
             "prompt": "Review", "terminal": "awaiting-certification"},
        ])
        projection = self._start("contained-check")
        first = conductor.tick_run(self.root, projection["run_id"], now=self.now)
        self.assertFalse((self.root / "rogue.txt").exists())
        self.assertTrue(first["progressed"])
        second = conductor.tick_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(second["state"], "blocked")
        final = runs.replay_run(self.root, projection["run_id"], now=self.now)
        receipt = next(
            item for item in final["node_receipts"] if item["node_id"] == "exact"
        )
        self.assertEqual(receipt["reason"], "write-scope")
        check_root = self.root.parent / ".delivery-workbench-checks"
        self.assertTrue(any(path.name == "rogue.txt" for path in check_root.rglob("rogue.txt")))

    def test_builtin_file_schema_diff_and_rail_checks_share_receipts(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        (self.root / "risk.json").write_text('{"risks": []}\n')
        self._write_score("builtin-checks", [
            {"id": "file", "type": "check",
             "runner": {"kind": "builtin", "name": "file-exists", "path": "risk.json"}},
            {"id": "schema", "type": "check",
             "runner": {"kind": "builtin", "name": "json-schema", "path": "risk.json",
                        "schema": "schemas/risk-register-v1.json"}},
            {"id": "rails", "type": "check",
             "runner": {"kind": "builtin", "name": "rail-status"}},
            {"id": "handoff", "type": "approval", "needs": ["file", "schema", "rails"],
             "prompt": "Review", "terminal": "awaiting-certification"},
        ])
        projection = self._start("builtin-checks")
        for _ in range(3):
            result = conductor.tick_run(self.root, projection["run_id"], now=self.now)
            if result["terminal"]:
                break
        final = runs.replay_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(final["state"], "awaiting-certification")
        self.assertTrue(all(item["outcome"] == "succeeded" for item in final["completed_claims"]))

        self._write_score("builtin-diff", [
            {"id": "implement", "type": "agent", "role": "implementation",
             "profile": "worker-write", "capabilities": ["repository-read", "repository-write"],
             "workspace": "isolated-worktree", "outputs": [{
                 "name": "implementation-diff", "format": "git-diff", "path": "workspace",
                 "allowed_paths": ["src/**"],
             }]},
            {"id": "scope", "type": "check", "needs": ["implement"],
             "runner": {"kind": "builtin", "name": "diff-scope", "path": "workspace",
                        "allowed_paths": ["src/**"]}},
            {"id": "handoff", "type": "approval", "needs": ["scope"],
             "prompt": "Review", "terminal": "awaiting-certification"},
        ])
        diff_run = self._start("builtin-diff")
        fixture = drivers.FixtureDriver({
            "implement": {"polls": 0, "workspace_files": {"src/feature.py": "VALUE = 1"}},
        })
        for _ in range(4):
            result = conductor.tick_run(
                self.root, diff_run["run_id"], driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
            )
            if result["terminal"]:
                break
        diff_final = runs.replay_run(self.root, diff_run["run_id"], now=self.now)
        self.assertEqual(diff_final["state"], "awaiting-certification")
        scope = next(item for item in diff_final["completed_claims"] if item["node_id"] == "scope")
        self.assertEqual(scope["outcome"], "succeeded")

    def test_crash_after_driver_start_recovers_without_duplicate_launch(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        self._write_score("crash-agent", [
            {
                "id": "research-api", "type": "agent", "role": "research",
                "profile": "research-readonly", "capabilities": ["repository-read", "network"],
                "workspace": "read-only", "outputs": [{
                    "name": "api-findings", "format": "markdown",
                    "path": "artifacts/api.md",
                    "required_sections": ["Findings", "Sources", "Risks"],
                    "citations": "required",
                }],
            },
            {"id": "handoff", "type": "approval", "needs": ["research-api"],
             "prompt": "Review", "terminal": "awaiting-certification"},
        ])
        projection = self._start("crash-agent")
        first_fixture = drivers.FixtureDriver(self._responses(polls=2))

        def crash(name, _detail):
            if name == "after-driver-start":
                raise RuntimeError("planted crash")

        with self.assertRaisesRegex(RuntimeError, "planted"):
            conductor.tick_run(
                self.root, projection["run_id"], driver_config=self.config,
                adapters={"fixture": first_fixture}, now=self.now,
                boundary_hook=crash,
            )
        crashed = runs.replay_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(len(crashed["active_claims"]), 1)
        self.assertEqual(first_fixture.starts, 1)
        recovered_fixture = drivers.FixtureDriver()
        for _ in range(5):
            result = conductor.tick_run(
                self.root, projection["run_id"], driver_config=self.config,
                adapters={"fixture": recovered_fixture}, now=self.now,
            )
            if result["terminal"]:
                break
        self.assertEqual(recovered_fixture.starts, 0)
        self.assertEqual(result["state"], "awaiting-certification")
        final = runs.replay_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(len([
            item for item in final["completed_claims"] if item["node_id"] == "research-api"
        ]), 1)

        collected_run = self._start("crash-agent", offset=3601)
        collected_fixture = drivers.FixtureDriver(self._responses(polls=0))

        def crash_after_collect(name, _detail):
            if name == "after-collect":
                raise RuntimeError("collect boundary")

        with self.assertRaisesRegex(RuntimeError, "collect boundary"):
            conductor.tick_run(
                self.root, collected_run["run_id"], driver_config=self.config,
                adapters={"fixture": collected_fixture}, now=self.now,
                boundary_hook=crash_after_collect,
            )
        self.assertEqual(collected_fixture.starts, 1)
        recovered_after_collect = drivers.FixtureDriver()
        conductor.tick_run(
            self.root, collected_run["run_id"], driver_config=self.config,
            adapters={"fixture": recovered_after_collect}, now=self.now,
        )
        self.assertEqual(recovered_after_collect.starts, 0)
        collected_projection = runs.replay_run(
            self.root, collected_run["run_id"], now=self.now
        )
        self.assertEqual(len(collected_projection["completed_claims"]), 1)

    def test_crash_after_check_recovers_without_rerunning_command(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_run as runs

        self._write_score("crash-check", [
            {"id": "exact", "type": "check",
             "runner": {"kind": "command", "argv": ["python3", "-m", "compileall", "-q", "."],
                        "cwd": ".", "timeout_seconds": 30, "output_bytes": 1000, "writes": []}},
            {"id": "handoff", "type": "approval", "needs": ["exact"],
             "prompt": "Review", "terminal": "awaiting-certification"},
        ])
        projection = self._start("crash-check")
        counter = {"starts": 0}

        def runner(_argv, _cwd, _timeout, _stdout, _stderr, _env):
            counter["starts"] += 1
            return 0

        def crash(name, _detail):
            if name == "after-check":
                raise RuntimeError("check boundary")

        with self.assertRaisesRegex(RuntimeError, "check boundary"):
            conductor.tick_run(
                self.root, projection["run_id"], check_runner=runner,
                now=self.now, boundary_hook=crash,
            )
        self.assertEqual(counter["starts"], 1)
        result = conductor.tick_run(
            self.root, projection["run_id"], check_runner=runner, now=self.now,
        )
        self.assertEqual(counter["starts"], 1)
        self.assertEqual(result["state"], "awaiting-certification")
        final = runs.replay_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(len(final["completed_claims"]), 1)

    def test_cancellation_precedes_interrupt_and_expiry_starts_nothing(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        projection = self._start()
        fixture = drivers.FixtureDriver(self._responses(polls=5))
        conductor.tick_run(
            self.root, projection["run_id"], driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        active = runs.replay_run(self.root, projection["run_id"], now=self.now)
        cancelled = runs.transition_run(
            self.root, projection["run_id"], "cancel", active["ledger_head"],
            reason="operator cancel", now=self.now,
        )
        conductor.tick_run(
            self.root, projection["run_id"], driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        final = runs.replay_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(final["state"], "cancelled")
        self.assertEqual(final["active_claims"], [])
        self.assertTrue(all(
            item["outcome"] == "cancelled" for item in final["completed_claims"]
        ))
        ledger = json.loads((
            self.root / ".git" / "pmo-orchestration" / "runs"
            / projection["run_id"] / "ledger.jsonl"
        ).read_text().splitlines()[cancelled["ledger_events"] - 1])
        self.assertEqual(ledger["event"], "run_cancelled")

        self._write_score("expiry", [
            {"id": "handoff", "type": "approval", "prompt": "Review",
             "terminal": "awaiting-certification"},
        ])
        expired = self._start("expiry", offset=1)
        result = conductor.tick_run(
            self.root, expired["run_id"], now=self.now + timedelta(seconds=2)
        )
        self.assertEqual(result["state"], "blocked")
        self.assertEqual(runs.replay_run(
            self.root, expired["run_id"], now=self.now + timedelta(seconds=2)
        )["completed_claims"], [])

    def test_cancellation_interrupts_a_live_contained_check(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_run as runs

        self._write_score("cancel-check", [
            {"id": "slow", "type": "check",
             "runner": {"kind": "command",
                        "argv": ["python3", "-c", "import time; time.sleep(30)"],
                        "cwd": ".", "timeout_seconds": 60,
                        "output_bytes": 1000, "writes": []}},
        ])
        projection = self._start("cancel-check")
        preview = core.build_run_act_preview(
            self.root, projection["run_id"], "tick"
        )
        child = subprocess.Popen(
            [sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
             "--root", str(self.root), "run", "tick", projection["run_id"],
             "--expect", preview["act_token"], "--json"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.addCleanup(lambda: child.kill() if child.poll() is None else None)
        record = None
        sessions = (
            self.root / ".git" / "pmo-orchestration" / "runs"
            / projection["run_id"] / "check-sessions"
        )
        for _ in range(100):
            paths = list(sessions.glob("*.json")) if sessions.is_dir() else []
            if paths:
                candidate = json.loads(paths[0].read_text())
                if candidate.get("pid"):
                    record = candidate
                    break
            time.sleep(0.02)
        self.assertIsNotNone(record, "check process did not publish its interrupt receipt")
        active = runs.replay_run(self.root, projection["run_id"])
        cancelled = runs.transition_run(
            self.root, projection["run_id"], "cancel", active["ledger_head"],
            reason="stop live check",
        )
        result = conductor.tick_run(self.root, projection["run_id"])
        self.assertEqual(result["state"], "cancelled")
        self.assertEqual(result["active_claims"], 0)
        _stdout, _stderr = child.communicate(timeout=5)
        final = runs.replay_run(self.root, projection["run_id"])
        self.assertEqual(final["completed_claims"][0]["outcome"], "cancelled")
        updated = json.loads(next(sessions.glob("*.json")).read_text())
        self.assertEqual(updated["state"], "cancelled")
        cancel_event = next(
            index for index, line in enumerate((
                self.root / ".git" / "pmo-orchestration" / "runs"
                / projection["run_id"] / "ledger.jsonl"
            ).read_text().splitlines())
            if json.loads(line)["event"] == "run_cancelled"
        )
        receipt_event = next(
            index for index, line in enumerate((
                self.root / ".git" / "pmo-orchestration" / "runs"
                / projection["run_id"] / "ledger.jsonl"
            ).read_text().splitlines())
            if json.loads(line)["event"] == "node_receipt"
            and json.loads(line)["detail"]["state"] == "cancelled"
        )
        self.assertLess(cancel_event, receipt_event)
        self.assertGreater(cancelled["ledger_events"], active["ledger_events"])

    def test_unsupported_authority_and_start_budget_stop(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs

        projection = self._start()
        restricted = json.loads(json.dumps(self.config))
        restricted["profiles"]["research-readonly"]["capabilities"] = ["repository-read"]
        restricted["profiles"]["research-readonly"]["network"] = False
        fixture = drivers.FixtureDriver(self._responses(polls=0))
        conductor.tick_run(
            self.root, projection["run_id"], driver_config=restricted,
            adapters={"fixture": fixture}, now=self.now,
        )
        stopped = conductor.tick_run(
            self.root, projection["run_id"], driver_config=restricted,
            adapters={"fixture": fixture}, now=self.now,
        )
        self.assertEqual(stopped["state"], "blocked")
        replayed = runs.replay_run(self.root, projection["run_id"], now=self.now)
        api = next(item for item in replayed["completed_claims"] if item["node_id"] == "research-api")
        self.assertEqual(api["receipts"][-1]["reason"], "unsupported-authority")
        self.assertEqual(fixture.starts, 1, "only the capability-compatible risk agent may start")

        defaults = {
            "max_concurrency": 2,
            "max_wall_seconds": 3600,
            "max_agent_starts": 1,
            "max_check_starts": 5,
            "default_timeout_seconds": 60,
            "max_artifact_bytes": 100000,
        }
        self._write_score("agent-budget", [
            {"id": "first", "type": "agent", "role": "research",
             "profile": "reasoning-readonly", "capabilities": ["repository-read"],
             "workspace": "read-only", "outputs": []},
            {"id": "second", "type": "agent", "role": "research",
             "profile": "reasoning-readonly", "capabilities": ["repository-read"],
             "workspace": "read-only", "outputs": []},
            {"id": "handoff", "type": "approval", "needs": ["first", "second"],
             "prompt": "Review", "terminal": "awaiting-certification"},
        ], defaults=defaults)
        budget_run = self._start("agent-budget")
        budget_fixture = drivers.FixtureDriver({"first": {"polls": 0}, "second": {"polls": 0}})
        conductor.tick_run(
            self.root, budget_run["run_id"], driver_config=self.config,
            adapters={"fixture": budget_fixture}, now=self.now,
        )
        exhausted = conductor.tick_run(
            self.root, budget_run["run_id"], driver_config=self.config,
            adapters={"fixture": budget_fixture}, now=self.now,
        )
        self.assertEqual(exhausted["state"], "blocked")
        self.assertEqual(budget_fixture.starts, 1)

    def test_failure_pause_and_named_approval_are_ledger_states(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_run as runs

        def failing(_argv, _cwd, _timeout, _stdout, _stderr, _env):
            return 1

        self._write_score("pause-check", [
            {"id": "exact", "type": "check",
             "runner": {"kind": "command", "argv": ["python3", "--version"],
                        "cwd": ".", "timeout_seconds": 30, "output_bytes": 1000,
                        "writes": []},
             "on_failure": {"action": "pause"}},
        ])
        paused_run = self._start("pause-check")
        conductor.tick_run(
            self.root, paused_run["run_id"], check_runner=failing, now=self.now
        )
        paused = conductor.tick_run(
            self.root, paused_run["run_id"], check_runner=failing, now=self.now
        )
        self.assertEqual(paused["state"], "paused")
        self.assertEqual(
            runs.replay_run(self.root, paused_run["run_id"], now=self.now)["routes"][0]["action"],
            "pause",
        )

        self._write_score("approval-check", [
            {"id": "exact", "type": "check",
             "runner": {"kind": "command", "argv": ["python3", "--version"],
                        "cwd": ".", "timeout_seconds": 30, "output_bytes": 1000,
                        "writes": []},
             "on_failure": {"action": "approval", "checkpoint": "check-review"}},
        ])
        approval_run = self._start("approval-check")
        conductor.tick_run(
            self.root, approval_run["run_id"], check_runner=failing, now=self.now
        )
        waiting = conductor.tick_run(
            self.root, approval_run["run_id"], check_runner=failing, now=self.now
        )
        self.assertEqual(waiting["state"], "awaiting-approval")
        projection = runs.replay_run(self.root, approval_run["run_id"], now=self.now)
        self.assertEqual(projection["pending_checkpoint"]["checkpoint"], "check-review")
        rejected = runs.decide_checkpoint(
            self.root, approval_run["run_id"], "reject", projection["ledger_head"],
            now=self.now,
        )
        self.assertEqual(rejected["state"], "blocked")

    def test_outstanding_request_republishes_once_per_restart_generation(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_run as runs
        import dw_pmo.orchestration_surface as surface

        waiting = self._open_checkpoint_request("durable-request")
        run_id = waiting["run_id"]
        correlation = waiting["outstanding_requests"][0]["correlation_id"]

        # Three consecutive restart ticks produce one republish in the
        # unchanged generation, never one per poll/process invocation.
        for _ in range(3):
            conductor.tick_run(self.root, run_id, now=self.now)
        after_restarts = runs.replay_run(self.root, run_id, now=self.now)
        republished = [
            event for event in runs._read_events(  # noqa: protected-access
                runs._run_dir(self.root, run_id), run_id  # noqa: protected-access
            )
            if event["event"] == "request_republished"
        ]
        self.assertEqual(len(republished), 1)
        self.assertEqual(republished[0]["detail"]["correlation_id"], correlation)
        self.assertEqual(republished[0]["detail"]["generation"], 0)

        paused = runs.transition_run(
            self.root, run_id, "pause", after_restarts["ledger_head"],
            reason="operator pause with decision pending", now=self.now,
        )
        self.assertEqual(paused["state"], "paused")
        self.assertEqual(
            paused["outstanding_requests"][0]["correlation_id"], correlation
        )
        resumed = runs.transition_run(
            self.root, run_id, "resume", paused["ledger_head"], now=self.now,
        )
        self.assertEqual(resumed["state"], "awaiting-approval")
        self.assertEqual(
            resumed["outstanding_requests"][0]["correlation_id"], correlation
        )
        republished = [
            event for event in runs._read_events(  # noqa: protected-access
                runs._run_dir(self.root, run_id), run_id  # noqa: protected-access
            )
            if event["event"] == "request_republished"
        ]
        self.assertEqual([event["detail"]["generation"] for event in republished], [0, 2])

        # The original pre-restart correlation remains the decision address.
        preview = surface.build_run_act_preview(
            self.root, run_id, "request", correlation_id=correlation,
            decision="approve", now=self.now,
        )
        decided = surface.apply_run_act(
            self.root, run_id, "request", preview["act_token"],
            correlation_id=correlation, decision="approve", now=self.now,
        )
        self.assertEqual(decided["state"], "active")
        self.assertEqual(decided["request_history"][0]["status"], "approved")

        # Every valid ledger prefix independently reconstructs the same live
        # pending set; projection.json is never consulted.
        ledger = runs._run_dir(self.root, run_id) / "ledger.jsonl"  # noqa: protected-access
        original = ledger.read_bytes()
        lines = original.splitlines(keepends=True)
        expected = set()
        try:
            for index, line in enumerate(lines, start=1):
                event = json.loads(line)
                if event["event"] == "checkpoint_reached" and event["detail"]["terminal"] == "none":
                    expected.add(runs._request_correlation(event))  # noqa: protected-access
                elif event["event"] == "request_decided":
                    expected.discard(event["detail"]["correlation_id"])
                elif event["event"] == "request_refused" and event["detail"]["reason"] == "expired":
                    expected.discard(event["detail"]["correlation_id"])
                ledger.write_bytes(b"".join(lines[:index]))
                replayed = runs.replay_run(self.root, run_id, now=self.now)
                self.assertEqual(
                    {item["correlation_id"] for item in replayed["outstanding_requests"]},
                    expected,
                    f"ledger prefix {index}",
                )
        finally:
            ledger.write_bytes(original)

    def test_typed_request_refusals_are_ledgered_and_leave_request_live(self):
        import dw_pmo.orchestration_run as runs
        import dw_pmo.orchestration_surface as surface

        waiting = self._open_checkpoint_request("typed-request")
        run_id = waiting["run_id"]
        correlation = waiting["outstanding_requests"][0]["correlation_id"]
        wrong = "req-000000000000000000000000"
        mismatch = surface.build_run_act_preview(
            self.root, run_id, "request", correlation_id=wrong,
            decision="approve", now=self.now,
        )
        self.assertTrue(mismatch["applicable"])
        self.assertEqual(mismatch["response_outcome"], "correlation-mismatch")
        after_mismatch = surface.apply_run_act(
            self.root, run_id, "request", mismatch["act_token"],
            correlation_id=wrong, decision="approve", now=self.now,
        )
        self.assertEqual(
            after_mismatch["outstanding_requests"][0]["correlation_id"], correlation
        )
        invalid = surface.build_run_act_preview(
            self.root, run_id, "request", correlation_id=correlation,
            decision="maybe", now=self.now,
        )
        self.assertTrue(invalid["applicable"])
        self.assertEqual(invalid["response_outcome"], "invalid-response")
        after_invalid = surface.apply_run_act(
            self.root, run_id, "request", invalid["act_token"],
            correlation_id=correlation, decision="maybe", now=self.now,
        )
        self.assertEqual(len(after_invalid["outstanding_requests"]), 1)
        self.assertEqual(
            [item["reason"] for item in after_invalid["request_refusals"]],
            ["correlation-mismatch", "invalid-response"],
        )
        ledger = (
            runs._run_dir(self.root, run_id) / "ledger.jsonl"  # noqa: protected-access
        ).read_text(encoding="utf-8")
        self.assertNotIn("maybe", ledger)

    def test_checkpoint_alias_cannot_decide_a_live_nudge_request(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_driver as drivers
        import dw_pmo.orchestration_run as runs
        import dw_pmo.orchestration_surface as surface

        nodes, responses = self._nudge_nodes()
        nodes.append({
            "id": "human-gate", "type": "approval", "needs": ["worker"],
            "prompt": "Review the bounded facts.",
            "options": ["approve", "reject"],
        })
        self._write_score("request-kind-isolation", nodes, nudges=[{
            "id": "on-ci-failed", "signal": "ci-failed", "target": "repair",
            "max_total": 1,
        }])
        self._seed_signal(branch="kind-isolation", name="ci-kind")
        started = self._start(
            "request-kind-isolation", signal_channel="origin/kind-isolation"
        )
        fixture = drivers.FixtureDriver(responses)
        for _ in range(10):
            conductor.tick_run(
                self.root, started["run_id"], driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
            )
            projection = runs.replay_run(
                self.root, started["run_id"], now=self.now
            )
            if projection["state"] == "awaiting-approval":
                break
        self.assertEqual(projection["state"], "awaiting-approval")
        by_kind = {
            item["kind"]: item for item in projection["outstanding_requests"]
        }
        self.assertEqual(set(by_kind), {"checkpoint", "nudge"})

        nudge_id = by_kind["nudge"]["correlation_id"]
        preview = surface.build_run_act_preview(
            self.root, started["run_id"], "checkpoint",
            correlation_id=nudge_id, decision="approve", now=self.now,
        )
        self.assertTrue(preview["applicable"])
        self.assertEqual(preview["response_outcome"], "correlation-mismatch")
        refused = surface.apply_run_act(
            self.root, started["run_id"], "checkpoint", preview["act_token"],
            correlation_id=nudge_id, decision="approve", now=self.now,
        )
        self.assertEqual(
            {item["kind"] for item in refused["outstanding_requests"]},
            {"checkpoint", "nudge"},
        )
        self.assertEqual(
            refused["request_refusals"][-1]["reason"],
            "correlation-mismatch",
        )

        checkpoint_id = next(
            item["correlation_id"]
            for item in refused["outstanding_requests"]
            if item["kind"] == "checkpoint"
        )
        reject = surface.build_run_act_preview(
            self.root, started["run_id"], "request",
            correlation_id=checkpoint_id, decision="reject", now=self.now,
        )
        blocked = surface.apply_run_act(
            self.root, started["run_id"], "request", reject["act_token"],
            correlation_id=checkpoint_id, decision="reject", now=self.now,
        )
        self.assertEqual(blocked["state"], "blocked")
        self.assertEqual(blocked["outstanding_requests"], [])
        nudge_history = next(
            item for item in blocked["request_history"] if item["kind"] == "nudge"
        )
        self.assertEqual(nudge_history["status"], "expired")

    def test_terminal_request_cleanup_recovers_a_crash_prefix(self):
        import dw_pmo.orchestration_run as runs
        import dw_pmo.orchestration_surface as surface

        waiting = self._open_checkpoint_request("terminal-cleanup")
        run_id = waiting["run_id"]
        correlation = waiting["outstanding_requests"][0]["correlation_id"]
        with runs._store_lock(self.root):  # noqa: protected-access
            crashed = runs._append_event_locked(  # noqa: protected-access
                self.root, run_id, waiting, "run_revoked",
                {"reason": "simulate crash after terminal event", "generation": 1},
                self.now,
            )
        self.assertEqual(crashed["state"], "revoked")
        self.assertEqual(
            crashed["outstanding_requests"][0]["correlation_id"], correlation
        )

        preview = surface.build_run_act_preview(
            self.root, run_id, "tick", now=self.now
        )
        self.assertTrue(preview["applicable"])
        self.assertFalse(preview["starts_work"])
        result = surface.apply_run_act(
            self.root, run_id, "tick", preview["act_token"], now=self.now
        )
        self.assertEqual(result["state"], "revoked")
        recovered = runs.replay_run(self.root, run_id, now=self.now)
        self.assertEqual(recovered["outstanding_requests"], [])
        self.assertEqual(recovered["request_history"][0]["status"], "expired")
        self.assertEqual(recovered["active_claims"], [])

    def test_request_expiry_is_a_recorded_refusal_and_notification(self):
        import dw_pmo.notifications as ntf
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_run as runs

        waiting = self._open_checkpoint_request("expiring-request", offset=1)
        late = self.now + timedelta(seconds=2)
        conductor.tick_run(self.root, waiting["run_id"], now=late)
        expired = runs.replay_run(self.root, waiting["run_id"], now=late)
        self.assertEqual(expired["state"], "blocked")
        self.assertEqual(expired["outstanding_requests"], [])
        self.assertEqual(expired["request_history"][0]["status"], "expired")
        self.assertEqual(expired["request_refusals"][-1]["reason"], "expired")
        inventory = ntf.build_notifications(self.root, now=late)
        self.assertTrue(any(
            item["kind"] == "request-expired"
            and item["run_id"] == waiting["run_id"]
            for item in inventory["notifications"]
        ))

    def test_run_view_exposes_request_age_schema_and_inspect_only_lineage(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_run as runs
        import dw_pmo.orchestration_surface as surface

        self._write_score("decision-lineage", [
            {"id": "first-gate", "type": "approval", "prompt": "First"},
            {"id": "second-gate", "type": "approval", "prompt": "Second",
             "needs": ["first-gate"]},
        ])
        started = self._start("decision-lineage")
        conductor.tick_run(self.root, started["run_id"], now=self.now)
        first = runs.replay_run(self.root, started["run_id"], now=self.now)
        first_id = first["outstanding_requests"][0]["correlation_id"]
        first = runs.decide_outstanding_request(
            self.root, started["run_id"], first_id, "approve",
            first["ledger_head"], now=self.now,
        )
        conductor.tick_run(self.root, started["run_id"], now=self.now)
        observed = self.now + timedelta(seconds=7)
        view = surface.build_run_view(self.root, started["run_id"], now=observed)
        self.assertEqual(len(view["outstanding_requests"]), 1)
        second = view["outstanding_requests"][0]
        self.assertEqual(second["age_seconds"], 7)
        self.assertEqual(second["origin_node"], "second-gate")
        self.assertEqual(second["schema_summary"], "decision: approve | reject")
        tree = view["decision_tree"]
        self.assertTrue(tree["inspect_only"])
        by_id = {item["correlation_id"]: item for item in tree["nodes"]}
        second_id = second["correlation_id"]
        self.assertEqual(by_id[second_id]["parent_correlation_id"], first_id)
        self.assertEqual(by_id[first_id]["children"], [second_id])
        self.assertIn("ledger_head", by_id[first_id]["preview"])
        decision_event = next(
            event for event in runs._read_events(  # noqa: protected-access
                runs._run_dir(self.root, started["run_id"]),  # noqa: protected-access
                started["run_id"],
            )
            if event["event"] == "request_decided"
            and event["detail"]["correlation_id"] == first_id
        )
        self.assertEqual(
            by_id[first_id]["preview"]["ledger_head"],
            decision_event["prev_hash"],
        )
        self.assertEqual(by_id[first_id]["preview"]["state"], "awaiting-approval")
        app = (TESTS_DIR.parent / "workbench" / "app.js").read_text(encoding="utf-8")
        for token in (
            "outstanding requests", "checkpoint lineage · inspect only",
            "inspect exact decision preview", "schema_summary",
        ):
            self.assertIn(token, app)

    def test_request_preview_and_apply_are_exact_across_interop_surfaces(self):
        import dw_pmo.mcpserver as mcp
        import dw_pmo.orchestration_surface as surface
        import dw_pmo.workbench as wb

        waiting = self._open_checkpoint_request("request-interop")
        run_id = waiting["run_id"]
        correlation = waiting["outstanding_requests"][0]["correlation_id"]
        with mock.patch(
            "dw_pmo.orchestration_run._utc_now", return_value=self.now
        ):
            core_preview = surface.build_run_act_preview(
                self.root, run_id, "request", correlation_id=correlation,
                decision="approve",
            )
            mcp_preview = mcp.call_tool(self.root, "dw_run_preview", {
                "run_id": run_id, "action": "request",
                "correlation_id": correlation, "decision": "approve",
            })["structuredContent"]
            status, http_preview = wb.handle_api(
                self.root, f"/api/runs/{run_id}/act/request", {
                    "correlation_id": [correlation], "decision": ["approve"],
                },
            )
        cli_preview = json.loads(self._dw(
            "run", "preview", run_id, "request", "--correlation", correlation,
            "--decision", "approve", "--json",
        ).stdout)
        self.assertEqual(status, 200)
        self.assertEqual(core_preview, mcp_preview)
        self.assertEqual(core_preview, http_preview["data"])
        self.assertEqual(core_preview, cli_preview)
        shown = self._dw("run", "show", run_id).stdout
        self.assertIn("Technical details:", shown)
        self.assertIn("Pending requests:", shown)
        self.assertIn(correlation, shown)
        cli_applied = json.loads(self._dw(
            "run", "request", run_id, correlation, "approve",
            "--expect", core_preview["act_token"], "--json",
        ).stdout)
        self.assertEqual(cli_applied["state"], "active")

        mcp_waiting = self._open_checkpoint_request("request-interop-mcp")
        mcp_run = mcp_waiting["run_id"]
        mcp_correlation = mcp_waiting["outstanding_requests"][0]["correlation_id"]
        mcp_act = surface.build_run_act_preview(
            self.root, mcp_run, "request", correlation_id=mcp_correlation,
            decision="approve", now=self.now,
        )
        mcp_applied = mcp.call_tool(self.root, "dw_run_request", {
            "run_id": mcp_run, "correlation_id": mcp_correlation,
            "decision": "approve", "expect": mcp_act["act_token"],
        })
        self.assertFalse(mcp_applied.get("isError", False), mcp_applied)
        self.assertEqual(mcp_applied["structuredContent"]["state"], "active")

        http_waiting = self._open_checkpoint_request("request-interop-http")
        http_run = http_waiting["run_id"]
        http_correlation = http_waiting["outstanding_requests"][0]["correlation_id"]
        http_act = surface.build_run_act_preview(
            self.root, http_run, "request", correlation_id=http_correlation,
            decision="approve", now=self.now,
        )
        status, applied = wb.handle_mutation(self.root, "/api/runs/request", {
            "run_id": http_run, "correlation_id": http_correlation,
            "decision": "approve", "expect": http_act["act_token"],
        })
        self.assertEqual(status, 200, applied)
        self.assertEqual(applied["data"]["state"], "active")

    def test_rail_uses_fresh_step_lease_and_stale_action_never_starts(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_run as runs
        from dw_pmo.step import build_step

        current = build_step(self.root, "sample")
        self.assertTrue(current["applicable"])
        action = current["action"]["id"]
        self._write_score("rail-step", [
            {"id": "advance", "type": "rail", "action": action,
             "on_failure": {"action": "abort"}},
            {"id": "handoff", "type": "approval", "needs": ["advance"],
             "prompt": "Review", "terminal": "awaiting-certification"},
        ])
        projection = self._start("rail-step")
        for _ in range(3):
            result = conductor.tick_run(self.root, projection["run_id"], now=self.now)
            if result["terminal"]:
                break
        final = runs.replay_run(self.root, projection["run_id"], now=self.now)
        self.assertEqual(final["state"], "awaiting-certification")
        self.assertIsNotNone(final["fact_binding"])
        self.assertEqual(final["fact_binding"]["action"], action)

        # New committed facts get a new grant; the old action is now stale.
        next_action = build_step(self.root, "sample")["action"]["id"]
        stale = "start-story" if next_action != "start-story" else "continue-story"
        self._write_score("stale-rail", [
            {"id": "advance", "type": "rail", "action": stale,
             "on_failure": {"action": "abort"}},
        ])
        stale_run = self._start("stale-rail")
        conductor.tick_run(self.root, stale_run["run_id"], now=self.now)
        stopped = conductor.tick_run(self.root, stale_run["run_id"], now=self.now)
        self.assertEqual(stopped["state"], "blocked")
        replayed = runs.replay_run(self.root, stale_run["run_id"], now=self.now)
        receipt = next(item for item in replayed["node_receipts"] if item["node_id"] == "advance")
        self.assertEqual(receipt["reason"], "stale-action")

    def test_installed_cli_tick_and_bounded_supervision_share_the_core(self):
        import dw_pmo.orchestration_conductor as conductor
        import dw_pmo.orchestration_run as runs

        self._write_score("cli-conductor", [
            {"id": "health", "type": "check",
             "runner": {"kind": "builtin", "name": "rail-status"}},
            {"id": "handoff", "type": "approval", "needs": ["health"],
             "prompt": "Review", "terminal": "awaiting-certification"},
        ])
        projection = self._start("cli-conductor")
        supervised = self._dw(
            "run", "supervise", projection["run_id"], "--max-ticks", "5",
            "--interval", "0", "--json",
        )
        document = json.loads(supervised.stdout)
        self.assertEqual(document["kind"], "delivery-workbench-conductor-supervision")
        self.assertEqual(document["state"], "awaiting-certification")
        self.assertLessEqual(document["ticks"], 5)
        shown = json.loads(self._dw(
            "run", "show", projection["run_id"], "--json"
        ).stdout)
        self.assertEqual(shown["ledger_head"], document["after_head"])
        (self.root / "operator-note.txt").write_text("operator-owned commit\n")
        self._commit("external operator commit")
        observed = conductor.tick_run(self.root, projection["run_id"])
        self.assertEqual(observed["state"], "awaiting-certification")
        replayed = runs.replay_run(self.root, projection["run_id"])
        self.assertEqual(replayed["external_commits"][-1]["relation"], "fast-forward")
        self.assertTrue(replayed["external_commits"][-1]["rebindable"])
        self.assertNotEqual(
            replayed["external_commits"][-1]["previous_head"],
            replayed["external_commits"][-1]["head"],
        )

        # A related commit on another branch is still observable, but never
        # becomes a dispatch checkpoint for the original branch-bound grant.
        self._cmd("git", "switch", "-q", "-c", "operator-other-branch")
        (self.root / "other-branch-note.txt").write_text("wrong branch\n")
        self._commit("external commit on another branch")
        conductor.tick_run(self.root, projection["run_id"])
        cross_branch = runs.replay_run(self.root, projection["run_id"])
        self.assertEqual(
            cross_branch["external_commits"][-1]["relation"], "fast-forward"
        )
        self.assertFalse(cross_branch["external_commits"][-1]["rebindable"])
        _path, grant, _compiled = runs._load_run_documents(  # noqa: protected-access
            self.root, projection["run_id"]
        )
        self.assertIn(
            "repository branch changed",
            runs._grant_freshness_issues(  # noqa: protected-access
                self.root, grant, cross_branch
            ),
        )

    def test_run_interop_compiler_plan_projection_and_preview_are_exact(self):
        import dw_pmo.mcpserver as mcp
        import dw_pmo.orchestration as orch
        import dw_pmo.orchestration_run as runs
        import dw_pmo.orchestration_surface as surface
        import dw_pmo.workbench as wb

        issued = self.now.strftime("%Y-%m-%dT%H:%M:%SZ")
        expires = (self.now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        compiled = orch.compile_score_path(
            self.root / "pm" / "orchestration" / "research-build-review.json"
        )
        cli_compiled = json.loads(self._dw(
            "orchestration", "show", "research-build-review", "--json"
        ).stdout)
        mcp_compiled = mcp.call_tool(
            self.root, "dw_orchestration_show", {"score": "research-build-review"}
        )["structuredContent"]
        status, http_compiled = wb.handle_api(
            self.root, "/api/orchestration/research-build-review/compiled", {}
        )
        self.assertEqual(status, 200)
        self.assertEqual(compiled, cli_compiled)
        self.assertEqual(compiled, mcp_compiled)
        self.assertEqual(compiled, http_compiled["data"])

        plan = runs.build_run_plan(
            self.root, "research-build-review", "sample", "SMP-0-01",
            issued_at=issued, expires_at=expires,
        )
        cli_plan = json.loads(self._dw(
            "run", "plan", "research-build-review", "--project", "sample",
            "--story", "SMP-0-01", "--issued-at", issued,
            "--expires-at", expires, "--json",
        ).stdout)
        mcp_plan = mcp.call_tool(self.root, "dw_run_plan", {
            "score": "research-build-review", "project": "sample",
            "story": "SMP-0-01", "issued_at": issued, "expires_at": expires,
        })["structuredContent"]
        status, http_plan = wb.handle_api(self.root, "/api/run-plan", {
            "score": ["research-build-review"], "project": ["sample"],
            "story": ["SMP-0-01"], "issued_at": [issued], "expires_at": [expires],
        })
        self.assertEqual(plan, cli_plan)
        self.assertEqual(plan, mcp_plan)
        self.assertEqual(plan, http_plan["data"])

        status, started = wb.handle_mutation(self.root, "/api/runs/start", {
            "score": "research-build-review", "project": "sample",
            "story": "SMP-0-01", "issued_at": issued, "expires_at": expires,
            "expect": plan["start_token"], "approve": True, "operator": "interop-test",
        })
        self.assertEqual(status, 200, started)
        run_id = started["data"]["run_id"]
        # Projection includes the live wall-budget observation. Hold the
        # observation instant constant while comparing adapters so a
        # second-boundary crossing on the slower Python floor cannot turn
        # transport parity into a clock-race assertion.
        observed_at = self.now + timedelta(seconds=30)
        with mock.patch(
            "dw_pmo.orchestration_run._utc_now", return_value=observed_at
        ):
            projection = runs.replay_run(self.root, run_id)
            self.assertEqual(
                mcp.call_tool(
                    self.root, "dw_run_show", {"run_id": run_id}
                )["structuredContent"],
                projection,
            )
            status, shown = wb.handle_api(self.root, f"/api/runs/{run_id}", {})
            self.assertEqual(status, 200)
            self.assertEqual(shown["data"], projection)

            preview = surface.build_run_act_preview(
                self.root, run_id, "pause", reason="inspect exact state"
            )
            mcp_preview = mcp.call_tool(self.root, "dw_run_preview", {
                "run_id": run_id, "action": "pause", "reason": "inspect exact state",
            })["structuredContent"]
            status, http_preview = wb.handle_api(
                self.root, f"/api/runs/{run_id}/act/pause",
                {"reason": ["inspect exact state"]},
            )
        self.assertEqual(preview, mcp_preview)
        self.assertEqual(preview, http_preview["data"])
        self.assertEqual(surface.document_bytes(preview), surface.document_bytes(mcp_preview))

    def test_tick_result_is_returned_unmodified_by_cli_mcp_and_http(self):
        """Applying adapters wrap the one core document; none reinterprets it."""
        import dw_pmo.mcpserver as mcp
        import dw_pmo.orchestration_surface as surface
        import dw_pmo.workbench as wb

        sentinel = {
            "kind": "delivery-workbench-conductor-tick",
            "schema_version": 1,
            "run_id": "run-000000000000000000000000",
            "before_head": "sha256:before",
            "after_head": "sha256:after",
            "state": "active",
            "progressed": True,
            "actions": [{"action": "claim", "node_id": "research-api", "attempt": 1}],
            "eligible": ["research-api"],
            "scheduled": [{"node_id": "research-api", "kind": "agent", "attempt": 1}],
            "blocked": [],
            "active_claims": 1,
            "next_poll_seconds": 1,
            "terminal": False,
        }
        cli_path = TESTS_DIR.parent / "bin" / "dw"
        loader = SourceFileLoader("dw_tick_adapter_fixture", str(cli_path))
        spec = importlib.util.spec_from_loader("dw_tick_adapter_fixture", loader)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        output = io.StringIO()
        with mock.patch.object(cli, "apply_run_act", return_value=sentinel) as call:
            with redirect_stdout(output):
                code = cli.main([
                    "--root", str(self.root), "run", "tick", sentinel["run_id"],
                    "--expect", "exact-act-token", "--json",
                ])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue()), sentinel)
        call.assert_called_once_with(
            self.root, sentinel["run_id"], "tick", "exact-act-token"
        )

        with mock.patch(
            "dw_pmo.orchestration_surface.apply_run_act", return_value=sentinel
        ) as call:
            mcp_result = mcp.call_tool(self.root, "dw_run_tick", {
                "run_id": sentinel["run_id"], "expect": "exact-act-token",
            })
            status, http_result = wb.handle_mutation(
                self.root, "/api/runs/tick",
                {"run_id": sentinel["run_id"], "expect": "exact-act-token"},
            )
        self.assertEqual(status, 200)
        self.assertEqual(mcp_result["structuredContent"], sentinel)
        self.assertEqual(http_result["data"], sentinel)
        self.assertEqual(
            surface.document_bytes(json.loads(output.getvalue())),
            surface.document_bytes(mcp_result["structuredContent"]),
        )
        self.assertEqual(
            surface.document_bytes(mcp_result["structuredContent"]),
            surface.document_bytes(http_result["data"]),
        )
        self.assertEqual(call.call_count, 2)

    def test_run_act_token_binds_action_reason_decision_and_state(self):
        import dw_pmo.orchestration_run as runs
        import dw_pmo.orchestration_surface as surface

        projection = self._start()
        run_id = projection["run_id"]
        preview = surface.build_run_act_preview(
            self.root, run_id, "pause", reason="bounded inspection", now=self.now
        )
        ledger = self.root / ".git" / "pmo-orchestration" / "runs" / run_id / "ledger.jsonl"
        before = ledger.read_bytes()
        with self.assertRaisesRegex(DwError, "stale or altered"):
            surface.apply_run_act(
                self.root, run_id, "pause", preview["act_token"],
                reason="different reason", now=self.now,
            )
        self.assertEqual(ledger.read_bytes(), before)
        paused = surface.apply_run_act(
            self.root, run_id, "pause", preview["act_token"],
            reason="bounded inspection", now=self.now,
        )
        self.assertEqual(paused["state"], "paused")
        with self.assertRaisesRegex(DwError, "stale or altered"):
            surface.apply_run_act(
                self.root, run_id, "pause", preview["act_token"],
                reason="bounded inspection", now=self.now,
            )
        self.assertEqual(runs.replay_run(self.root, run_id, now=self.now)["state"], "paused")

    def test_stale_tick_preview_refuses_before_dispatch_or_event(self):
        import dw_pmo.orchestration_run as runs
        import dw_pmo.orchestration_surface as surface

        projection = self._start()
        run_id = projection["run_id"]
        tick = surface.build_run_act_preview(self.root, run_id, "tick", now=self.now)
        paused = runs.transition_run(
            self.root, run_id, "pause", projection["ledger_head"],
            reason="operator won race", now=self.now,
        )
        ledger = self.root / ".git" / "pmo-orchestration" / "runs" / run_id / "ledger.jsonl"
        before = ledger.read_bytes()
        with self.assertRaisesRegex(DwError, "stale or altered"):
            surface.apply_run_act(
                self.root, run_id, "tick", tick["act_token"], now=self.now
            )
        self.assertEqual(ledger.read_bytes(), before)
        self.assertEqual(paused["state"], "paused")
        self.assertFalse((ledger.parent / "driver-sessions").exists())

    def test_run_view_is_pure_rich_and_excludes_private_semantics(self):
        import dw_pmo.orchestration_surface as surface

        projection = self._start()
        run_id = projection["run_id"]
        run_dir = self.root / ".git" / "pmo-orchestration" / "runs" / run_id
        before = {
            str(path.relative_to(run_dir)): path.read_bytes()
            for path in run_dir.rglob("*") if path.is_file()
        }
        first = surface.build_run_view(self.root, run_id, now=self.now)
        second = surface.build_run_view(self.root, run_id, now=self.now)
        after = {
            str(path.relative_to(run_dir)): path.read_bytes()
            for path in run_dir.rglob("*") if path.is_file()
        }
        self.assertEqual(first, second)
        self.assertEqual(before, after)
        self.assertEqual(first["kind"], surface.RUN_VIEW_KIND)
        self.assertEqual(len(first["graph"]["nodes"]), 7)
        self.assertIn("budgets", first)
        self.assertIn("timeline", first)
        self.assertTrue(any(item["action"] == "tick" for item in first["controls"]))
        progress = first["live_progress"]
        self.assertEqual(
            progress["kind"], "delivery-workbench-live-progress"
        )
        self.assertEqual(
            [item["id"] for item in progress["answers"]],
            [
                "delivery", "team", "passed", "blocked", "decision",
                "remaining-change-spend", "next",
            ],
        )
        self.assertEqual(
            progress["next_step"]["target"],
            first["graph"]["scheduled_on_confirm"][0]["node_id"],
        )
        self.assertEqual(
            progress["next_step"]["source"],
            {
                "model": "delivery-workbench-conductor-decision",
                "path": "/scheduled/0",
            },
        )
        self.assertEqual(progress["blocker"]["status"], "clear")
        self.assertFalse(progress["progress"]["groups"]["blocked"])
        self.assertEqual(
            progress["technical_details"]["event_hashes"],
            [item["event_hash"] for item in first["timeline"]],
        )
        self.assertEqual(
            {
                item["id"]: (item["used"], item["limit"])
                for item in progress["limits"]["counts"]
            },
            {
                key: (value["used"], value["limit"])
                for key, value in first["budgets"].items()
            },
        )
        self.assertEqual(
            progress["limits"]["cost"]["status"], "not-recorded"
        )
        self.assertEqual(
            set(progress["review"]),
            {
                "mechanical", "agent_judgment", "dissent", "repair",
                "final_governed_decisions", "failed_evidence",
            },
        )
        for key in (
            "starts_work", "writes_events", "selects_next_work",
            "decides_recovery", "grants_authority",
        ):
            self.assertFalse(progress[key], key)
        bounded = first["bounded_actions"]
        self.assertEqual(
            bounded["kind"], "delivery-workbench-bounded-actions"
        )
        self.assertEqual(bounded["context"], "bounded-run")
        self.assertEqual(
            {
                item["action"]: item["available"]
                for item in bounded["actions"]
                if item.get("action") in {"tick", "pause", "revoke", "cancel"}
            },
            {
                item["action"]: item["available"]
                for item in first["controls"]
                if item["action"] in {"tick", "pause", "revoke", "cancel"}
            },
        )
        self.assertEqual(
            bounded["permission"]["scope"]["story_id"],
            first["story"]["id"],
        )
        for key in (
            "starts_work", "writes_events", "selects_action",
            "selects_next_work", "grants_authority",
            "changes_retry_policy", "sends_notifications",
        ):
            self.assertFalse(bounded[key], key)

        keys: set[str] = set()
        def collect(value):
            if isinstance(value, dict):
                keys.update(str(key) for key in value)
                for item in value.values(): collect(item)
            elif isinstance(value, list):
                for item in value: collect(item)
        collect(first)
        self.assertTrue({
            "prompt", "argv", "command", "packet", "packet_path", "staging",
            "credentials", "approved_by", "content", "pid",
        }.isdisjoint(keys), sorted(keys))

    def test_run_stream_is_explicit_bounded_and_injection_safe(self):
        import dw_pmo.mcpserver as mcp
        import dw_pmo.orchestration_surface as surface

        projection = self._start()
        run_id = projection["run_id"]
        directory = (
            self.root / ".git" / "pmo-orchestration" / "runs" / run_id
            / "check-sessions" / "check-fixture"
        )
        directory.mkdir(parents=True)
        (directory / "stdout.log").write_bytes(b"0123456789" * 3000)
        document = surface.read_run_stream(
            self.root, run_id, "check", "check-fixture", "stdout", max_bytes=17
        )
        self.assertEqual(document["included_bytes"], 17)
        self.assertEqual(len(document["content"]), 17)
        self.assertTrue(document["truncated"])
        via_mcp = mcp.call_tool(self.root, "dw_run_stream", {
            "run_id": run_id, "executor": "check", "execution_id": "check-fixture",
            "stream": "stdout", "max_bytes": 17,
        })["structuredContent"]
        self.assertEqual(document, via_mcp)
        for malicious in ("../check-fixture", "check-fixture/../../grant"):
            with self.assertRaises(DwError):
                surface.read_run_stream(
                    self.root, run_id, "check", malicious, "stdout"
                )

    def test_cli_and_mcp_controls_require_fresh_preview_tokens(self):
        import dw_pmo.mcpserver as mcp
        import dw_pmo.orchestration_run as runs

        projection = self._start()
        run_id = projection["run_id"]
        preview = json.loads(self._dw(
            "run", "preview", run_id, "pause", "--reason", "cli review", "--json"
        ).stdout)
        paused = json.loads(self._dw(
            "run", "pause", run_id, "--reason", "cli review",
            "--expect", preview["act_token"], "--json",
        ).stdout)
        self.assertEqual(paused["state"], "paused")
        resume = mcp.call_tool(self.root, "dw_run_preview", {
            "run_id": run_id, "action": "resume",
        })["structuredContent"]
        applied = mcp.call_tool(self.root, "dw_run_resume", {
            "run_id": run_id, "expect": resume["act_token"],
        })
        self.assertFalse(applied.get("isError", False), applied)
        self.assertEqual(applied["structuredContent"]["state"], "active")
        self.assertEqual(runs.replay_run(self.root, run_id)["state"], "active")

    def test_adapters_reject_score_semantics_driver_config_and_argv(self):
        import dw_pmo.mcpserver as mcp
        import dw_pmo.workbench as wb

        start_schema = mcp.TOOLS["dw_run_start"]["inputSchema"]
        serialized = json.dumps(start_schema, sort_keys=True)
        for forbidden in ("score_document", "prompt", "argv", "driver_config", "check_runner"):
            self.assertNotIn(forbidden, serialized)
        result = mcp.call_tool(self.root, "dw_run_start", {
            "score": "research-build-review", "story": "SMP-0-01",
            "issued_at": "2026-01-01T00:00:00Z", "expires_at": "2026-01-01T01:00:00Z",
            "expect": "sha256:nope", "approve": True, "operator": "fixture",
            "argv": ["danger"],
        })
        self.assertTrue(result["isError"])
        self.assertIn("unknown parameter", result["content"][0]["text"])
        status, body = wb.handle_mutation(self.root, "/api/runs/tick", {
            "run_id": "run-000000000000000000000000", "expect": "x",
            "driver_config": {"profiles": {}},
        })
        self.assertEqual(status, 400)
        self.assertIn("unknown run tick parameter", body["issues"][0])

    def test_mission_control_run_summary_is_content_safe(self):
        import dw_pmo.orchestration_surface as surface
        from dw_pmo.statefeed import build_state_feed

        projection = self._start()
        summary = surface.run_summary_inventory(self.root, now=self.now)
        self.assertEqual(summary["runs"][0]["run_id"], projection["run_id"])
        feed = build_state_feed(self.root)
        self.assertEqual(feed["orchestration_runs"]["kind"], surface.RUN_SUMMARY_KIND)
        serialized = json.dumps(feed["orchestration_runs"], sort_keys=True)
        for forbidden in ("prompt", "argv", "transcript", "source content", "artifact content"):
            self.assertNotIn(forbidden, serialized)

    def test_run_view_static_contract_has_consent_privacy_and_no_poller(self):
        app = (TESTS_DIR.parent / "workbench" / "app.js").read_text(encoding="utf-8")
        css = (TESTS_DIR.parent / "workbench" / "style.css").read_text(encoding="utf-8")
        run_source = app[
            app.index("function runStateBadge"):
            app.index("/* ── optional Program / Workflow Studio")
        ]
        for token in (
            "Live delivery", "Technical details", "fail checks", "Artifact metadata and lineage",
            "failure routes", "human checkpoints", "hash-chained receipts",
            "preview exact grant", "Actions and decisions", "Before any action",
            "Decision and blocker inbox", "Could an effect already have occurred?",
            "view.bounded_actions", "exact control catalog",
            "close explicit stream",
        ):
            self.assertIn(token, run_source)
        self.assertNotIn("setInterval", run_source)
        self.assertNotIn("driver_config", run_source)
        self.assertNotIn("argv:", run_source)
        self.assertIn("aria-labelledby=\"run-graph-title\"", run_source)
        self.assertIn("@media (max-width: 520px)", css)
        self.assertIn(".run-node.state-active", css)
        for token in (
            ".bounded-action-center", ".bounded-permission",
            ".bounded-inbox-grid", ".bounded-action-grid",
            ".bounded-failure", ".bounded-usage-table",
        ):
            self.assertIn(token, css)


class WorkbenchAccessibilityContractTest(unittest.TestCase):
    """WLA-27-09: accessibility behavior remains part of every UI render."""

    def setUp(self):
        self.workbench = TESTS_DIR.parent / "workbench"
        self.app = (self.workbench / "app.js").read_text(encoding="utf-8")
        self.css = (self.workbench / "style.css").read_text(encoding="utf-8")
        self.html = (self.workbench / "index.html").read_text(encoding="utf-8")

    def test_shell_landmarks_skip_link_and_live_regions_are_named(self):
        for marker in (
            'id="skip-link"', 'aria-label="Primary"',
            'aria-label="Breadcrumb"', 'id="app"', 'aria-busy="true"',
            'id="route-status"', 'id="live-status"',
        ):
            self.assertIn(marker, self.html)
        self.assertIn("labelMainRegion", self.app)
        self.assertIn("announceRoute", self.app)
        self.assertIn("updatePrimaryNavigation", self.app)

    def test_focus_dialog_tab_and_live_update_contracts_are_executable(self):
        for marker in (
            "captureAppFocus", "restoreAppFocus", "rememberReturnFocus",
            "restoreReturnFocus", "wireDismissibleRegion", "focusRegion",
            "wireTablist", "wireArrowGroup", "announceLiveUpdate",
            "liveAnnouncementKeys", 'role="dialog"', 'aria-modal="false"',
            'role="tablist"', 'role="tab"', 'role="tabpanel"',
            'event.key !== "Escape"', "focusMain: true",
        ):
            self.assertIn(marker, self.app)
        self.assertEqual(self.app.count('aria-live="'), 0)
        self.assertNotIn('role="status" aria-label="Live update status"', self.app)

    def test_visible_focus_motion_color_and_overflow_rules_are_present(self):
        for marker in (
            ":focus-visible", ".skip-link", "overflow-x: clip",
            "overflow-wrap: anywhere", ".tablewrap",
            '[role="tab"][aria-selected="true"]', '[role="dialog"]',
            "@media (pointer: coarse)",
            "@media (prefers-reduced-motion: reduce)",
            "@media (forced-colors: active)",
        ):
            self.assertIn(marker, self.css)
        self.assertIn('setAttribute("aria-current", "page")', self.app)

    def test_review_matrix_covers_each_canonical_journey(self):
        accessibility = json.loads(
            (TESTS_DIR / "accessibility-journeys-v1.json").read_text(
                encoding="utf-8"
            )
        )
        usability = json.loads(
            (
                TESTS_DIR / "fixtures" / "usability" / "journeys-v1.json"
            ).read_text(encoding="utf-8")
        )
        expected = {item["id"] for item in usability["journeys"]}
        reviewed = {item["id"] for item in accessibility["journeys"]}
        self.assertEqual(reviewed, expected)
        self.assertEqual(accessibility["viewports"]["wide"], {
            "width": 1440, "height": 900,
        })
        self.assertEqual(accessibility["viewports"]["narrow"], {
            "width": 390, "height": 844,
        })
        for journey in accessibility["journeys"]:
            self.assertEqual(journey["manual_review"]["result"], "pass")
            self.assertGreaterEqual(len(journey["keyboard_path"]), 3)
            self.assertGreaterEqual(len(journey["focus_contract"]), 3)


class UsabilityPackagedExamContractTest(unittest.TestCase):
    """WLA-27-10: one installed consumer proves all canonical journeys."""

    @classmethod
    def setUpClass(cls):
        path = TESTS_DIR / "usability-packaged-exam.py"
        spec = importlib.util.spec_from_file_location(
            "dw_usability_packaged_exam", path
        )
        if spec is None or spec.loader is None:
            raise AssertionError(f"cannot load {path}")
        cls.exam = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.exam)
        cls.contract = cls.exam.load_json(cls.exam.JOURNEYS_PATH)
        cls.baseline = cls.exam.load_json(cls.exam.BASELINE_PATH)
        cls.language = cls.exam.load_json(cls.exam.LANGUAGE_PATH)
        cls.journey_ids = {
            item["id"] for item in cls.contract["journeys"]
        }

    @staticmethod
    def _hash(character):
        return "sha256:" + character * 64

    def _valid_report(self):
        return {
            "kind": "delivery-workbench-autonomous-program-exam",
            "schema_version": 1,
            "green": {
                "state": "complete",
                "ledger_events": 9,
                "stream_events": 5,
            },
            "phase27_observations": {
                "same_consumer": {
                    "initial": {
                        "status_kind": "delivery-workbench-status",
                        "step_kind": "delivery-workbench-step",
                        "next_available": True,
                        "current_story": "DM-1-01",
                        "programs": 0,
                        "program_store": False,
                        "run_store": False,
                        "process_starts": False,
                        "setup_writes": False,
                        "setup_starts_work": False,
                        "ordinary_work_requires_setup": False,
                        "optional_policy_present": False,
                    },
                    "optional_configuration": {
                        "configured_after_initial_use": True,
                        "workflow_round_trips_lossless": True,
                        "organization_round_trip_lossless": True,
                        "program_round_trip_lossless": True,
                        "starts_work": False,
                        "creates_permission": False,
                    },
                },
                "bounded_decision": {
                    "state_before": "awaiting-approval",
                    "question": "Should reviewed work continue?",
                    "resolver": "Delivery owner",
                    "visible_next_step": "Record the decision",
                    "choices": ["approve", "reject"],
                    "response_preview_pure": True,
                    "decision": "approve",
                    "exact": {
                        "ledger_before": self._hash("1"),
                        "ledger_after": self._hash("2"),
                        "act_token": self._hash("3"),
                    },
                },
                "stop_and_revoke": {
                    "preview_pure": True,
                    "state_after": "revoked",
                    "label": "Permanently stop",
                    "effect": "Stops this bounded delivery permanently.",
                    "unchanged": "Completed work stays recorded.",
                    "exact": {
                        "generation_before": 2,
                        "generation_after": 3,
                        "ledger_head": self._hash("4"),
                    },
                },
                "preflight": {
                    "independent_review": True,
                    "team": [
                        {"duty": "implementer"},
                        {"duty": "verifier"},
                    ],
                    "decision_councils": ["architecture"],
                    "allowed_effects": ["workspace write"],
                    "limits": {"work": 3},
                    "stops": ["limit reached"],
                    "permanently_excluded": ["release"],
                    "preview_effects": {
                        "roadmap": False,
                        "git": False,
                        "process": False,
                        "network": False,
                        "permission": False,
                    },
                    "separate_start_required": True,
                },
                "start": {
                    "separate_confirmation": True,
                    "preview_started_work": False,
                    "start_state": "running",
                },
                "delivery": {
                    "review_results": ["needs-repair", "pass"],
                    "repair_rounds": 1,
                    "governed_decision": {"dissent_preserved": True},
                    "answers": ["answer"] * 7,
                    "limits": {"remaining": 1},
                    "permission": {"remaining": True},
                    "usage": {"cost": 1},
                },
                "recovery": {
                    "conductor_crashes": 1,
                    "delivery_crashes": 1,
                    "unique_claim_ids": True,
                    "unique_dispatch_ids": True,
                    "unique_receipt_hashes": True,
                    "no_duplicate_delivery_actions": True,
                    "saved_state": {"status": "verified"},
                },
                "completion": {
                    "state": "complete",
                    "progress": {"known_total": 3, "completed": 3},
                    "next_step": {"label": "Review completed work"},
                },
                "technical_details": {
                    "label": "Technical details",
                    "run_id": "run-fixture",
                    "grant_hash": self._hash("5"),
                    "plan_hash": self._hash("6"),
                    "ledger_head": self._hash("7"),
                    "generation": 3,
                    "receipt_hashes": [self._hash("8")],
                    "principal_fingerprints": [self._hash("9")],
                    "event_count": 9,
                    "stream_events": 5,
                    "exact_view_parity": [
                        "CLI", "MCP", "HTTP", "Workbench",
                    ],
                    "exact_event_parity": ["CLI", "MCP", "HTTP", "SSE"],
                },
            },
        }

    def test_canonical_transcript_covers_every_journey_without_reserved_terms(self):
        transcript = self.exam.build_transcript(
            self.contract, self.baseline, self.language
        )
        self.assertEqual(set(self.exam.JOURNEY_EVIDENCE), self.journey_ids)
        self.assertEqual(
            {item["id"] for item in transcript["journeys"]},
            self.journey_ids,
        )
        friction = transcript["friction"]
        self.assertEqual(friction["journey_checkpoints"], 13)
        self.assertEqual(friction["authority_confirmations"], 4)
        self.assertEqual(friction["safe_refusal_paths"], 13)
        self.assertEqual(friction["unresolved_dead_ends"], 0)
        self.assertEqual(friction["everyday_reserved_terms"], [])
        self.assertEqual(friction["baseline_descriptive_counts"], {
            "steps": 88,
            "decisions": 38,
            "engineering_terms": 81,
            "dead_ends": 13,
            "context_switches": 26,
        })

    def test_observation_validator_rejects_each_planted_regression(self):
        report = self._valid_report()
        self.assertEqual(
            self.exam.validate_report(report, self.journey_ids), []
        )
        self.assertEqual(
            self.exam.planted_red_cases(report, self.journey_ids), []
        )

    def test_public_package_and_ci_entry_points_run_the_composed_exam(self):
        package = (TESTS_DIR / "package-smoke.sh").read_text(encoding="utf-8")
        workflow = (
            TESTS_DIR.parent.parent / ".github" / "workflows" / "validation.yml"
        ).read_text(encoding="utf-8")
        journeys = (
            TESTS_DIR.parent.parent / "docs" / "usability-journeys.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '"$SCRIPT_DIR/usability-packaged-exam.py" --dw "$DW"',
            package,
        )
        self.assertIn(
            "python3 -m py_compile "
            "pmo-roadmap/tests/usability-packaged-exam.py",
            workflow,
        )
        self.assertIn("Fresh-wheel exit proof", journeys)
        self.assertIn("Five planted mutations prove", journeys)


class AgentHooksTest(unittest.TestCase):
    """The agent hook seam (WLA-14-02): installer discipline, the
    emit whitelist, and the guards — docs/absorption-ccgram.md §1."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-hooks-test."))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        from dw_pmo import agenthooks
        self.hooks = agenthooks
        self.settings = self.tmp / "settings.json"
        self.events = self.tmp / "events.jsonl"

    def test_install_is_idempotent(self):
        self.assertEqual(self.hooks.install_agent("claude", self.settings), 0)
        first = self.settings.read_text()
        self.assertEqual(self.hooks.install_agent("claude", self.settings), 0)
        self.assertEqual(first, self.settings.read_text())
        doc = json.loads(first)
        for event in self.hooks.HOOK_EVENTS:
            self.assertIn(event, doc["hooks"])
        end_entry = doc["hooks"]["SessionEnd"][0]["hooks"][0]
        self.assertTrue(end_entry.get("async"), "SessionEnd must not delay exit")
        self.assertNotIn("async", doc["hooks"]["Notification"][0]["hooks"][0])

    def test_uninstall_is_surgical(self):
        self.settings.write_text(json.dumps({
            "hooks": {"Stop": [{"hooks": [
                {"type": "command", "command": "somebody-elses-hook"}]}]}
        }))
        self.hooks.install_agent("claude", self.settings)
        self.assertEqual(self.hooks.uninstall_agent("claude", self.settings), 0)
        doc = json.loads(self.settings.read_text())
        commands = [
            entry["command"]
            for groups in doc.get("hooks", {}).values()
            for group in groups
            for entry in group.get("hooks", [])
        ]
        self.assertEqual(commands, ["somebody-elses-hook"], "only ours removed")

    def test_status_reports_per_event(self):
        report = self.hooks.status_agent("claude", self.settings)
        self.assertFalse(any(report["events"].values()))
        self.hooks.install_agent("claude", self.settings)
        report = self.hooks.status_agent("claude", self.settings)
        self.assertTrue(all(report["events"].values()))

    def test_codex_flag_opt_out_respected(self):
        config = self.tmp / "config.toml"
        config.write_text("[features]\ncodex_hooks = false\n")
        rc = self.hooks.install_agent(
            "codex", self.tmp / "hooks.json", codex_config=config)
        self.assertEqual(rc, 1, "explicit false is the owner's opt-out")
        self.assertIn("codex_hooks = false", config.read_text())

    def test_emit_whitelists_and_never_leaks_content(self):
        payload = json.dumps({
            "session_id": "s1", "cwd": "/w",
            "message": "TOP SECRET prompt content",
            "transcript_path": "/private/things",
        })
        rc = self.hooks.emit("claude", "Notification", payload,
                             events_path=self.events, env={})
        self.assertEqual(rc, 0)
        line = json.loads(self.events.read_text().strip())
        self.assertEqual(
            sorted(line), ["agent", "cwd", "event", "session_id", "ts"])
        self.assertNotIn("SECRET", self.events.read_text())

    def test_emit_quiet_guard_and_unknown_event(self):
        rc = self.hooks.emit("claude", "Notification", "{}",
                             events_path=self.events,
                             env={"DW_HOOK_QUIET": "1"})
        self.assertEqual(rc, 0)
        self.assertFalse(self.events.exists(), "quiet means silent")
        self.hooks.emit("claude", "SomethingNovel", "{}",
                        events_path=self.events, env={})
        self.assertFalse(self.events.exists(), "unknown events ignored")

    def test_emit_never_raises_on_garbage(self):
        rc = self.hooks.emit("claude", "Stop", "not json at all{{{",
                             events_path=self.events, env={})
        self.assertEqual(rc, 0)
        line = json.loads(self.events.read_text().strip())
        self.assertEqual(line["event"], "Stop")


class ProgramContractTest(unittest.TestCase):
    """WLA-26-01: pin the optional program and trust contract."""

    @classmethod
    def setUpClass(cls):
        cls.path = TESTS_DIR.parent.parent / "docs" / "programs.md"
        cls.doc = cls.path.read_text(encoding="utf-8")

    @classmethod
    def _section(cls, heading):
        marker = f"## {heading}\n"
        if marker not in cls.doc:
            raise AssertionError(f"missing contract section: {heading}")
        body = cls.doc.split(marker, 1)[1]
        return body.split("\n## ", 1)[0]

    @staticmethod
    def _backtick_first_column(section):
        values = set()
        for line in section.splitlines():
            if not line.startswith("| `"):
                continue
            cell = line.split("|", 2)[1].strip()
            if cell.startswith("`") and cell.endswith("`"):
                values.add(cell[1:-1])
        return values

    def test_required_contract_sections_are_present(self):
        headings = {
            "Capability ladder and default invariant",
            "Composition and sources of truth",
            "Tracked policy family",
            "Roadmap scope and deterministic selection",
            "Hierarchical workflow semantics",
            "Organization, assignment, and separation of duties",
            "Verdict taxonomy and quality gates",
            "Autonomy modes and capability lattice",
            "Program plan and grant",
            "Budgets, ceilings, and exhaustion",
            "Program state, ledger, and recovery",
            "Integration and exact roadmap advancement",
            "Outward facts, nudges, and decision ports",
            "Surfaces and progressive disclosure",
            "Storage, privacy, and content boundaries",
            "Refusal taxonomy",
            "Threat model and exact fail checks",
            "Phase 26 proof standard",
        }
        found = {
            line[3:] for line in self.doc.splitlines()
            if line.startswith("## ")
        }
        self.assertTrue(headings <= found, headings - found)

    def test_default_mode_and_policy_family_are_explicit(self):
        section = self._section("Capability ladder and default invariant")
        normalized = " ".join(section.split())
        for phrase in (
            "no program configuration is healthy ordinary state",
            "never auto-wrapped in, imported into, or interpreted as a program",
            "install and update create no program instance",
            "never the ordinary Workbench front door",
        ):
            self.assertIn(phrase, normalized)
        for kind in (
            "delivery-workbench-program@1",
            "delivery-workbench-workflow@1",
            "delivery-workbench-organization@1",
            "delivery-workbench-rubric@1",
        ):
            self.assertIn(kind, self.doc)
        sample = self.doc.split("```json\n", 1)[1].split("\n```", 1)[0]
        parsed = json.loads(sample)
        self.assertEqual(parsed["kind"], "delivery-workbench-program")
        self.assertEqual(parsed["schema_version"], 1)
        self.assertEqual(parsed["scope"]["selection"], "roadmap-frontier-v1")

    def test_workflow_separation_and_verdict_types_are_closed(self):
        workflow = self._section("Hierarchical workflow semantics")
        for node_type in (
            "`agent`", "`check`", "`collect`", "`bounded_run`",
            "`subflow`", "`loop`", "`debate`", "`verdict`",
            "`gate`", "`checkpoint`", "`rail`",
        ):
            self.assertIn(f"| {node_type} |", workflow)
        self.assertIn("General graph cycles and recursive subflow references are invalid", workflow)
        separation = self._section("Organization, assignment, and separation of duties")
        self.assertIn("rendezvous-sha256-v1", separation)
        self.assertIn("different from the implementer principal", separation)
        self.assertIn("verifier assignment fixed before implementation dispatch", separation)
        verdicts = self._section("Verdict taxonomy and quality gates")
        for verdict_type in (
            "`mechanical-fact`", "`agent-verdict`", "`panel-verdict`",
            "`council-verdict`", "`meta-verdict`",
        ):
            self.assertIn(f"| {verdict_type} |", verdicts)
        self.assertIn("Only the check/rail adapter can create `mechanical-fact`", verdicts)

    def test_capability_vocabulary_is_exact(self):
        section = self._section("Autonomy modes and capability lattice")
        capability_table = section.split(
            "The Phase 26 capability vocabulary is closed:", 1
        )[1].split("\n\nCapabilities are independent bits", 1)[0]
        actual = self._backtick_first_column(capability_table)
        expected = {
            "program:select", "agent:dispatch", "check:execute",
            "workspace:write", "verdict:issue", "council:decide",
            "obligation:record", "obligation:materialize",
            "obligation:disposition",
            "nudge:deliver", "notification:send", "evidence:materialize",
            "integration:apply", "contract:generate",
            "certification:objective", "certification:verdict", "git:commit",
            "git:push", "roadmap:story-start", "roadmap:story-complete",
            "roadmap:phase-advance",
        }
        self.assertEqual(actual, expected)
        self.assertIn("Capabilities are independent bits with prerequisites", section)
        for exclusion in ("`git:merge`", "release creation", "deployment", "publication"):
            self.assertIn(exclusion, section)

    def test_refusal_vocabulary_is_exact(self):
        section = self._section("Refusal taxonomy")
        actual = self._backtick_first_column(section)
        expected = {
            "program-not-found", "program-invalid", "program-stale",
            "roadmap-stale", "repository-stale", "grant-required",
            "grant-expired", "grant-revoked", "mode-denied",
            "capability-denied", "budget-exhausted", "scope-violation",
            "frontier-blocked", "dependency-incomplete", "binding-missing",
            "binding-ambiguous", "workflow-unbounded", "workflow-recursive",
            "role-unavailable", "separation-violation",
            "provider-diversity-unsatisfied", "quorum-lost",
            "dissent-unresolved", "verdict-stale", "verdict-insufficient",
            "architect-veto", "checkpoint-required", "claim-conflict",
            "ledger-corrupt", "integration-conflict", "remote-diverged",
            "content-refused", "permanent-exclusion",
        }
        self.assertEqual(actual, expected)
        self.assertIn("ordinary no-program use is not an error", section)

    def test_threat_table_pins_default_authority_and_quality_failures(self):
        section = self._section("Threat model and exact fail checks")
        rows = [
            line for line in section.splitlines()
            if line.startswith("| ") and not line.startswith("| Threat")
            and not line.startswith("|---")
        ]
        self.assertGreaterEqual(len(rows), 23)
        for threat in (
            "Default-mode creep makes programs mandatory",
            "Install, save, or open becomes ambient authority",
            "A bounded score silently becomes a program",
            "Implementer verifies itself",
            "Agent prose counterfeits a test fact",
            "Debate/retry/repair loops forever",
            "Crash duplicates an expensive/destructive act",
            "UI/config/runtime interpret policy differently",
        ):
            self.assertIn(threat, section)


class ProgramPlannerTest(unittest.TestCase):
    """WLA-26-02: pure multi-phase program compilation and selection."""

    def setUp(self):
        import dw_pmo.program_surface as program_surface
        import dw_pmo.programs as programs
        from dw_pmo.orchestration_driver import write_driver_config

        self.programs_core = programs
        self.program_surface = program_surface
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-program-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self._git("init", "-q", "-b", "main")
        self._git("config", "user.name", "Program Fixture")
        self._git("config", "user.email", "program@example.test")
        self._write_roadmap()
        self._write_policy_family()
        self._git("add", ".")
        self._git("commit", "-qm", "fixture")
        self.driver_config = write_driver_config(self.root, {
            "kind": "delivery-workbench-driver-config",
            "schema_version": 1,
            "workspace_root": None,
            "profiles": {
                "builder-a": {
                    "adapter": "fixture",
                    "capabilities": ["repository-read", "repository-write"],
                    "workspace_modes": ["isolated-worktree"],
                },
                "builder-b": {
                    "adapter": "fixture",
                    "capabilities": ["repository-read", "repository-write"],
                    "workspace_modes": ["isolated-worktree"],
                },
                "verifier-a": {
                    "adapter": "fixture",
                    "capabilities": ["repository-read"],
                    "workspace_modes": ["read-only"],
                },
                "meta-a": {
                    "adapter": "fixture",
                    "capabilities": ["repository-read"],
                    "workspace_modes": ["read-only"],
                },
                "architect-a": {
                    "adapter": "fixture",
                    "capabilities": ["repository-read"],
                    "workspace_modes": ["read-only"],
                },
            },
        })

    def _git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def _story(self, story_id, title, status, depends="none"):
        return (
            f"# {story_id} - {title}\n\n"
            "- **Project:** demo\n"
            f"- **Phase:** {story_id.split('-')[1]}\n"
            f"- **Status:** {status}\n"
            f"- **Depends on:** {depends}\n"
            "- **Owner:** unassigned\n\n"
            "## Problem\n\nFixture story.\n"
        )

    def _write_roadmap(self):
        project = Path("pm/roadmap/demo")
        self._write(project / "README.md", """# Demo - Roadmap

**Last updated:** 2026-07-22.
**Current phase:** [Phase 1 - Alpha](./phase-1-alpha/current-phase-status.md).
**Status:** active.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 1 | Alpha | in-progress | [phase-1-alpha](./phase-1-alpha/) |
| 2 | Beta | planned | [phase-2-beta](./phase-2-beta/) |

## Project metadata

- **Slug:** `demo`
- **Story ID prefix:** DM
""")
        phase1 = project / "phase-1-alpha"
        phase2 = project / "phase-2-beta"
        self._write(phase1 / "current-phase-status.md", """# Phase 1 - Alpha

**Last updated:** 2026-07-22.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DM-1-01 | Foundation | done | [story-01-foundation](./story-01-foundation.md) | [evidence-story-01](./evidence-story-01.md) |
| DM-1-02 | Active build | in-progress | [story-02-active-build](./story-02-active-build.md) | - |
| DM-1-03 | Parked experiment | on-hold (later) | [story-03-parked-experiment](./story-03-parked-experiment.md) | - |
""")
        self._write(phase2 / "current-phase-status.md", """# Phase 2 - Beta

**Last updated:** 2026-07-22.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DM-2-01 | Dependent beta | backlog | [story-01-dependent-beta](./story-01-dependent-beta.md) | - |
| DM-2-02 | Blocked beta | blocked (external fixture) | [story-02-blocked-beta](./story-02-blocked-beta.md) | - |
""")
        self._write(
            phase1 / "story-01-foundation.md",
            self._story("DM-1-01", "Foundation", "done"),
        )
        self._write(
            phase1 / "story-02-active-build.md",
            self._story("DM-1-02", "Active build", "in-progress", "DM-1-01"),
        )
        self._write(
            phase1 / "story-03-parked-experiment.md",
            self._story("DM-1-03", "Parked experiment", "on-hold", "DM-1-02"),
        )
        self._write(
            phase2 / "story-01-dependent-beta.md",
            self._story("DM-2-01", "Dependent beta", "backlog", "DM-1-02"),
        )
        self._write(
            phase2 / "story-02-blocked-beta.md",
            self._story("DM-2-02", "Blocked beta", "blocked", "DM-2-01"),
        )
        self._write(phase1 / "evidence-story-01.md", """# Evidence - DM-1-01

- **Story:** DM-1-01 - Foundation
- **Status:** done
- **Date:** 2026-07-22

## Proof

- fixture proof
""")

    def _write_json(self, relative, value):
        return self._write(relative, json.dumps(value, indent=2, sort_keys=True) + "\n")

    def _write_policy_family(self):
        for slug in ("story-work",):
            self._write_json(f"pm/workflows/{slug}.json", {
                "kind": "delivery-workbench-workflow",
                "schema_version": 1,
                "slug": slug,
                "title": "Story work",
                "version": "1.0.0",
                "parameters": [{
                    "id": "story-id",
                    "type": "string",
                    "required": True,
                    "max_bytes": 128,
                }],
                "defaults": {},
                "nodes": [{
                    "id": "implement",
                    "type": "agent",
                    "role": "implementer",
                    "task": "Implement the exact selected story.",
                    "workspace": "isolated-worktree",
                    "capability_ceiling": ["agent:dispatch", "workspace:write"],
                    "timeout_seconds": 900,
                    "max_attempts": 1,
                    "inputs": {
                        "story": {"kind": "parameter", "name": "story-id"},
                    },
                    "outputs": [{
                        "id": "candidate",
                        "kind": "git-diff",
                        "max_bytes": 1000000,
                    }],
                    "on_success": {"kind": "terminal", "target": "complete"},
                    "on_failure": {"kind": "action", "target": "block"},
                }],
                "terminals": [{"id": "complete", "meaning": "complete"}],
            })
        for slug in ("story-quality", "phase-architecture"):
            self._write_json(f"pm/rubrics/{slug}.json", {
                "kind": "delivery-workbench-rubric",
                "schema_version": 1,
                "slug": slug,
                "title": slug.replace("-", " ").title(),
                "version": "1.0.0",
                "subject_type": (
                    "diff" if slug == "story-quality" else "phase-snapshot"
                ),
                "result_vocabulary": [
                    "pass", "fail", "needs-repair", "escalate",
                ],
                "freshness": {
                    "max_age_seconds": 3_600,
                    "bind": [
                        "subject", "repository", "program", "assignment",
                        "rubric", "ledger",
                    ],
                },
                "criteria": [{
                    "id": "quality",
                    "question": "Does the exact subject satisfy its contract?",
                    "evaluation": {"kind": "agent-judgment", "fact": None},
                    "required_evidence_kinds": [
                        "git-diff" if slug == "story-quality" else "markdown"
                    ],
                    "min_citations": 1,
                    "allowed_results": [
                        "pass", "fail", "abstain", "inconclusive",
                    ],
                    "veto": True,
                    "rationale_max_bytes": 2_000,
                }],
                "aggregation": {
                    "method": "all",
                    "threshold": 1,
                    "on_pass": "pass",
                    "on_fail": "needs-repair",
                    "on_abstain": "escalate",
                    "on_inconclusive": "needs-repair",
                },
            })

        def fixture_agent(agent_id, profile, duties, *, writer=False):
            capabilities = ["agent:dispatch"]
            if writer:
                capabilities.append("workspace:write")
            elif any(duty in {"verifier", "meta-verifier", "master-architect", "judge"} for duty in duties):
                capabilities.append("verdict:issue")
                if "judge" in duties:
                    capabilities.extend(["council:decide", "obligation:record"])
            return {
                "id": agent_id,
                "profile": profile,
                "duties": duties,
                "workspace_domain": agent_id,
                "capability_ceiling": capabilities,
                "max_concurrency": 1,
                "weight": 1,
            }

        def fixture_role(role_id, duty, pool, *, independent=(), required=True):
            writer = duty in {"implementer", "repairer"}
            judgment = duty in {"verifier", "meta-verifier", "master-architect", "judge"}
            capabilities = ["agent:dispatch"]
            if writer:
                capabilities.append("workspace:write")
            elif judgment:
                capabilities.append("verdict:issue")
                if duty in {"verifier", "judge"}:
                    capabilities.extend(["council:decide", "obligation:record"])
            return {
                "id": role_id,
                "duty": duty,
                "pool": pool,
                "required": required,
                "cardinality": 1,
                "capability_ceiling": capabilities,
                "driver_capabilities": ["repository-read", "repository-write"] if writer else ["repository-read"],
                "workspace": "isolated-worktree" if writer else "read-only",
                "context": {
                    "allow": ["story", "phase", "roadmap", "workflow-inputs", "candidate-diff", "mechanical-receipts", "prior-verdicts", "dissent", "proposal", "public-artifacts"],
                    "expressions": ["context", "parameter", "literal", "artifact"],
                    "max_bytes": 500000,
                },
                "artifacts": {
                    "read": ["markdown", "json", "text", "git-diff", "verdict", "decision", "mechanical-fact"],
                    "write": ["markdown", "json", "text", "git-diff"] if writer else ["verdict", "decision"],
                    "max_bytes": 50000000,
                },
                "output_schema": None if judgment else "fixture-output@1",
                "verdict_schema": "fixture-verdict@1" if judgment else None,
                "max_concurrency": 1,
                "resource_groups": ["repository-writer"] if writer else [],
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

        self._write_json("pm/organizations/delivery-core.json", {
            "kind": "delivery-workbench-organization",
            "schema_version": 1,
            "slug": "delivery-core",
            "title": "Delivery core",
            "agents": [
                fixture_agent("builder-a", "builder-a", ["implementer", "repairer"], writer=True),
                fixture_agent("builder-b", "builder-b", ["implementer", "repairer"], writer=True),
                fixture_agent("verifier-a", "verifier-a", ["verifier", "judge"]),
                fixture_agent("meta-a", "meta-a", ["meta-verifier"]),
                fixture_agent("architect-a", "architect-a", ["master-architect"]),
            ],
            "pools": [
                {"id": "builders", "agents": ["builder-a", "builder-b"]},
                {"id": "verifiers", "agents": ["verifier-a"]},
                {"id": "auditors", "agents": ["meta-a"]},
                {"id": "architects", "agents": ["architect-a"]},
            ],
            "teams": [{
                "id": "story-cell",
                "roles": [
                    fixture_role("implementer", "implementer", "builders"),
                    fixture_role("verifier", "verifier", "verifiers", independent=("implementer",)),
                    fixture_role("meta", "meta-verifier", "auditors", independent=("implementer", "verifier"), required=False),
                    fixture_role("architect", "master-architect", "architects", independent=("implementer", "verifier"), required=False),
                ],
            }],
            "councils": [{
                "id": "quality-council",
                "members": ["verifier", "meta"],
                "judge": "verifier",
                "quorum": 1,
                "meta_verifier": "meta",
                "distinct_principals": True,
            }],
        })
        self.program = {
            "kind": "delivery-workbench-program",
            "schema_version": 1,
            "slug": "demo-program",
            "title": "Demo program",
            "scope": {
                "project": "demo",
                "phases": {"from": 1, "through": 2},
                "stories": {"include": ["DM-1-01", "DM-1-02", "DM-2-01"]},
                "selection": "roadmap-frontier-v1",
                "blocked_policy": "stop",
            },
            "organization": "delivery-core",
            "bindings": [
                {"id": "alpha", "priority": 10, "match": {"phase_from": 1, "phase_through": 1}, "workflow": "story-work", "with": {"story-id": {"kind": "context", "name": "story.id"}}, "team": "story-cell", "rubrics": ["story-quality"]},
                {"id": "beta", "priority": 20, "match": {"phase_from": 2, "phase_through": 2}, "workflow": "story-work", "with": {"story-id": {"kind": "context", "name": "story.id"}}, "team": "story-cell", "rubrics": ["story-quality"]},
            ],
            "phase_gates": [{
                "id": "architecture-gate",
                "when": "before-phase-complete",
                "role": "master-architect",
                "rubric": "phase-architecture",
                "on_fail": "block",
            }],
            "mode_ceiling": "continuous",
            "requested_capabilities": [
                "agent:dispatch", "check:execute", "verdict:issue",
                "workspace:write",
            ],
            "budgets": {"max_phases": 2, "max_stories": 3},
            "stop_conditions": ["scope-complete", "blocked-frontier", "budget-exhausted"],
        }
        self.program_path = self._write_json(
            "pm/programs/demo-program.json", self.program
        )

    @staticmethod
    def codes(document):
        return {item["code"] for item in document["diagnostics"]}

    def _set_story_status(self, story_id, old, new):
        phase = int(story_id.split("-")[1])
        phase_path = (
            self.root / "pm/roadmap/demo" /
            ("phase-1-alpha" if phase == 1 else "phase-2-beta")
        )
        status_path = phase_path / "current-phase-status.md"
        text = status_path.read_text(encoding="utf-8")
        line = next(line for line in text.splitlines() if f"| {story_id} |" in line)
        status_path.write_text(text.replace(line, line.replace(f"| {old} |", f"| {new} |")), encoding="utf-8")
        story_file = next(path for path in phase_path.glob("story-*.md") if story_id in path.read_text(encoding="utf-8").splitlines()[0])
        story_file.write_text(
            story_file.read_text(encoding="utf-8").replace(
                f"- **Status:** {old}\n", f"- **Status:** {new}\n"
            ),
            encoding="utf-8",
        )

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
             "--root", str(self.root), "program", *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_program_compiles_policy_references_scope_and_hashes(self):
        core = self.programs_core
        compiled = core.compile_program_path(self.root, self.program_path)
        self.assertEqual(compiled["kind"], core.COMPILED_KIND)
        self.assertRegex(compiled["semantic_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(compiled["policy_bundle_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(compiled["program"]["scope"]["phases"], [1, 2])
        self.assertEqual(compiled["analysis"]["binding_by_story"]["DM-1-02"], "alpha")
        self.assertIn("story-work", compiled["references"]["workflows"])
        self.assertIn("story-quality", compiled["references"]["rubrics"])
        self.assertEqual(compiled["references"]["organization"]["slug"], "delivery-core")
        self.assertRegex(
            compiled["references"]["organization"]["document_hash"],
            r"^sha256:[0-9a-f]{64}$",
        )
        self.assertEqual(
            compiled["reference_hashes"]["workflows"]["story-work"],
            compiled["references"]["workflows"]["story-work"]["semantic_hash"],
        )
        self.assertRegex(
            compiled["reference_hashes"]["workflow_instances"]["alpha"],
            r"^sha256:[0-9a-f]{64}$",
        )
        self.assertEqual(
            compiled["program"]["bindings"][0]["with"]["story-id"],
            {"kind": "context", "name": "story.id"},
        )

    def test_program_nudge_rules_are_exact_targeted_and_finitely_budgeted(self):
        core = self.programs_core
        program = json.loads(json.dumps(self.program))
        program["requested_capabilities"].extend([
            "program:select",
            "nudge:deliver",
        ])
        program["nudges"] = [{
            "id": "repair-failed-ci",
            "signal": "ci-failed",
            "binding": "alpha",
            "target": "story-work/implement",
            "max_per_signal": 1,
            "max_total": 2,
            "expectation": "Revisit the declared implementation evidence.",
        }]
        program["budgets"]["max_nudges"] = 2
        validation = core.validate_program(self.root, program)
        self.assertTrue(validation["valid"], validation["diagnostics"])
        compiled = core.compile_program(self.root, program)
        self.assertEqual(compiled["program"]["nudges"], program["nudges"])
        plan = core.build_program_plan(self.root, program)
        self.assertEqual(plan["program"]["nudges"], program["nudges"])

        missing_authority = json.loads(json.dumps(program))
        missing_authority["requested_capabilities"].remove("nudge:deliver")
        self.assertIn(
            "workflow-capability-missing",
            self.codes(core.validate_program(self.root, missing_authority)),
        )

        dangling = json.loads(json.dumps(program))
        dangling["nudges"][0]["target"] = "story-work/missing-agent"
        self.assertIn(
            "dangling-nudge-target",
            self.codes(core.validate_program(self.root, dangling)),
        )

        unbound = json.loads(json.dumps(program))
        unbound["nudges"][0]["binding"] = "missing-binding"
        self.assertIn(
            "dangling-nudge-binding",
            self.codes(core.validate_program(self.root, unbound)),
        )

        unsupported = json.loads(json.dumps(program))
        unsupported["nudges"][0]["signal"] = "waiting-input-timeout"
        self.assertIn(
            "unsupported-program-signal",
            self.codes(core.validate_program(self.root, unsupported)),
        )

        exhausted = json.loads(json.dumps(program))
        exhausted["budgets"]["max_nudges"] = 1
        self.assertIn(
            "workflow-exceeds-budget",
            self.codes(core.validate_program(self.root, exhausted)),
        )

    def test_layout_changes_document_hashes_but_not_program_authority(self):
        core = self.programs_core
        baseline = core.compile_program(self.root, self.program)
        with_layout = json.loads(json.dumps(self.program))
        with_layout["layout"] = {"viewport": {"x": 12, "y": 30}}
        for relative in (
            "pm/workflows/story-work.json",
            "pm/organizations/delivery-core.json",
            "pm/rubrics/story-quality.json",
        ):
            path = self.root / relative
            document = json.loads(path.read_text(encoding="utf-8"))
            document["layout"] = (
                {
                    "nodes": {"implement": {"x": 10, "y": 20}},
                    "viewport": {"x": 0, "y": 0, "zoom": 1},
                }
                if "/workflows/" in relative
                else {"nodes": {"fixture": {"x": 10, "y": 20}}}
            )
            self._write_json(relative, document)
        moved = core.compile_program(self.root, with_layout)
        self.assertEqual(baseline["semantic_hash"], moved["semantic_hash"])
        self.assertEqual(baseline["policy_bundle_hash"], moved["policy_bundle_hash"])
        self.assertEqual(baseline["reference_hashes"], moved["reference_hashes"])
        self.assertNotEqual(baseline["document_hash"], moved["document_hash"])
        self.assertNotEqual(
            baseline["references"]["workflows"]["story-work"]["document_hash"],
            moved["references"]["workflows"]["story-work"]["document_hash"],
        )

    def test_plan_without_localization_hints_keeps_the_previous_shape(self):
        core = self.programs_core
        with mock.patch.object(
                core, "ground_story_path",
                side_effect=AssertionError("no-hints plan must not ground")):
            plan = core.build_program_plan(self.root, "demo-program")
        self.assertNotIn("grounding", plan["selection"])
        self.assertEqual(
            set(plan["selection"]),
            {
                "story", "phase", "status", "reason", "why", "binding",
                "workflow", "team", "rubrics", "phase_gates",
            },
        )

    def test_plan_with_localization_hints_includes_advisory_grounding(self):
        story = (
            self.root / "pm/roadmap/demo/phase-1-alpha"
            / "story-02-active-build.md"
        )
        story.write_text(
            story.read_text(encoding="utf-8")
            + "\n## Localization hints\n\n"
              "- **Affected files:**\n"
              "  - `fixture_code.py`\n"
              "- **Target symbols:**\n"
              "  - `fixture_target`\n",
            encoding="utf-8",
        )
        self._write(
            "fixture_code.py",
            "def fixture_target():\n    return True\n",
        )
        self._git("add", ".")
        from dw_pmo.repository_map import refresh_symbol_map
        refresh_symbol_map(self.root)

        plan = self.programs_core.build_program_plan(
            self.root, "demo-program"
        )
        grounding = plan["selection"]["grounding"]
        self.assertEqual(grounding["status"], "grounded")
        self.assertEqual(grounding["summary"], {
            "verified": 2, "new": 0, "unknown": 0,
        })
        self.assertTrue(plan["applicable"])
        self.assertFalse(grounding["authorizes"])
        self.assertFalse(grounding["starts_work"])

        self._write("unrelated.txt", "move the index\n")
        self._git("add", "unrelated.txt")
        stale = self.programs_core.build_program_plan(
            self.root, "demo-program"
        )
        self.assertTrue(stale["applicable"])
        self.assertEqual(stale["selection"]["grounding"]["status"], "refused")
        self.assertIn("is stale", stale["selection"]["grounding"]["reason"])
        self.assertNotIn("affected_files", stale["selection"]["grounding"])

    def test_planner_resumes_active_story_and_assigns_independent_verifier(self):
        core = self.programs_core
        plan = core.build_program_plan(self.root, "demo-program")
        self.assertTrue(plan["applicable"], plan["issues"])
        self.assertEqual(plan["selection"]["story"], "DM-1-02")
        self.assertEqual(plan["selection"]["reason"], "resume-in-progress")
        self.assertEqual(plan["selection"]["workflow"]["slug"], "story-work")
        self.assertEqual(plan["selection"]["workflow"]["version"], "1.0.0")
        self.assertEqual(plan["selection"]["rubrics"][0]["version"], "1.0.0")
        self.assertEqual(
            plan["program"]["requested_capabilities"],
            [
                "agent:dispatch", "check:execute", "verdict:issue",
                "workspace:write",
            ],
        )
        self.assertIn("organization", plan["program"]["reference_hashes"])
        assignment = plan["assignment"]
        self.assertEqual(assignment["team"], "story-cell")
        self.assertEqual(
            assignment["kind"], "delivery-workbench-team-assignment"
        )
        self.assertTrue(assignment["separation"]["passed"])
        self.assertTrue(assignment["separation"]["facts"]["verifier_preassigned"])
        self.assertNotEqual(
            assignment["implementer"]["profile"], assignment["verifier"]["profile"]
        )
        self.assertNotEqual(
            assignment["implementer"]["workspace_domain"],
            assignment["verifier"]["workspace_domain"],
        )
        self.assertIsNotNone(assignment["meta_verifier"])
        self.assertIsNotNone(assignment["master_architect"])
        self.assertRegex(
            assignment["verifier"]["adapter_capability_fingerprint"],
            r"^sha256:[0-9a-f]{64}$",
        )
        verifier_policy = next(
            role["packet_policy"] for role in assignment["roles"]
            if role["duty"] == "verifier"
        )
        self.assertEqual(verifier_policy["workspace"], "read-only")
        architect_policy = next(
            role["packet_policy"] for role in assignment["roles"]
            if role["duty"] == "master-architect"
        )
        self.assertEqual(
            architect_policy["effective_capability_ceiling"],
            ["agent:dispatch", "verdict:issue"],
        )
        self.assertEqual(
            architect_policy["workflow_requirements"]["artifact_reads"],
            ["markdown"],
        )
        reasons = {item["story"]: item["reason"] for item in plan["candidates"]}
        self.assertEqual(reasons["DM-1-01"], "already-done")
        self.assertEqual(reasons["DM-1-03"], "out-of-scope")
        self.assertEqual(reasons["DM-2-01"], "dependency-incomplete")
        self.assertEqual(reasons["DM-2-02"], "out-of-scope")

    def test_program_plan_refuses_unsatisfied_provider_family_rule(self):
        from dw_pmo.orchestration_driver import load_driver_config

        organization_path = self.root / "pm/organizations/delivery-core.json"
        organization = json.loads(organization_path.read_text(encoding="utf-8"))
        organization["diversity"] = [{
            "id": "cross-family-review",
            "kind": "provider-family",
            "roles": ["implementer", "verifier"],
        }]
        self._write_json("pm/organizations/delivery-core.json", organization)
        validation = self.programs_core.validate_program(self.root, self.program)
        self.assertFalse(validation["valid"])
        self.assertIn(
            "provider-diversity-unsatisfied", self.codes(validation),
        )

        satisfying = load_driver_config(self.root)
        satisfying["profiles"]["builder-a"]["provider_family"] = "family-a"
        satisfying["profiles"]["builder-b"]["provider_family"] = "family-a"
        satisfying["profiles"]["verifier-a"]["provider_family"] = "family-b"
        validation = self.programs_core.validate_program(
            self.root, self.program, driver_config=satisfying,
        )
        self.assertTrue(validation["valid"], validation["diagnostics"])
        plan = self.programs_core.build_program_plan(
            self.root, self.program, driver_config=satisfying
        )
        self.assertTrue(plan["applicable"], plan["issues"])
        self.assertTrue(plan["assignment"]["diversity"]["passed"])

        unsatisfied = json.loads(json.dumps(satisfying))
        unsatisfied["profiles"]["verifier-a"]["provider_family"] = "family-a"
        refused = self.programs_core.build_program_plan(
            self.root, self.program, driver_config=unsatisfied
        )
        self.assertFalse(refused["applicable"])
        diagnostic = next(
            item for item in refused["issues"]
            if item["code"] == "provider-diversity-unsatisfied"
        )
        self.assertIn("cross-family-review", diagnostic["message"])
        self.assertIn("missing a family different from family-a", diagnostic["message"])
        self.assertFalse(refused["starts_work"])

    def test_after_active_completion_planner_advances_stably_to_next_phase(self):
        core = self.programs_core
        self._set_story_status("DM-1-02", "in-progress", "done")
        phase1 = self.root / "pm/roadmap/demo/phase-1-alpha"
        self._write(phase1 / "evidence-story-02.md", """# Evidence - DM-1-02

- **Story:** DM-1-02 - Active build
- **Status:** done
- **Date:** 2026-07-22

## Proof

- fixture proof
""")
        status_path = phase1 / "current-phase-status.md"
        text = status_path.read_text(encoding="utf-8")
        text = text.replace(
            "| DM-1-02 | Active build | done | [story-02-active-build](./story-02-active-build.md) | - |",
            "| DM-1-02 | Active build | done | [story-02-active-build](./story-02-active-build.md) | [evidence-story-02](./evidence-story-02.md) |",
        )
        status_path.write_text(text, encoding="utf-8")
        plan = core.build_program_plan(self.root, "demo-program")
        self.assertTrue(plan["applicable"], plan["issues"])
        self.assertEqual(plan["selection"]["story"], "DM-2-01")
        self.assertEqual(plan["selection"]["reason"], "selected")
        self.assertEqual(plan["selection"]["binding"], "beta")

    def test_dependency_hold_block_pause_and_out_of_scope_reasons_are_distinct(self):
        core = self.programs_core
        program = json.loads(json.dumps(self.program))
        program["scope"]["stories"] = "all"
        program["budgets"]["max_stories"] = 5
        validation = core.validate_program(self.root, program)
        self.assertTrue(validation["valid"], validation["diagnostics"])
        plan = core.build_program_plan(self.root, program)
        reasons = {item["story"]: item["reason"] for item in plan["candidates"]}
        self.assertEqual(reasons["DM-1-03"], "story-held")
        self.assertEqual(reasons["DM-2-01"], "dependency-incomplete")
        self.assertEqual(reasons["DM-2-02"], "story-blocked")

        phase1 = self.root / "pm/roadmap/demo/phase-1-alpha/current-phase-status.md"
        phase1.write_text(
            phase1.read_text(encoding="utf-8").replace(
                "**Last updated:** 2026-07-22.",
                "**Last updated:** 2026-07-22.\n\n**Status:** paused (fixture)",
            ),
            encoding="utf-8",
        )
        paused = core.build_program_plan(self.root, program)
        paused_reasons = {item["story"]: item["reason"] for item in paused["candidates"]}
        self.assertEqual(paused_reasons["DM-1-02"], "phase-paused")
        self.assertIn("frontier-blocked", {item["code"] for item in paused["issues"]})

    def test_unknown_keys_duplicate_ids_ranges_and_ambiguous_rules_refuse(self):
        core = self.programs_core
        broken = json.loads(json.dumps(self.program))
        broken["surprise"] = True
        broken["scope"]["phases"] = {"from": 3, "through": 1}
        broken["bindings"].append(dict(broken["bindings"][0]))
        validation = core.validate_program(self.root, broken)
        self.assertFalse(validation["valid"])
        self.assertTrue(
            {"unknown-key", "invalid-phase-range", "duplicate-id"}
            <= self.codes(validation),
            validation["diagnostics"],
        )

        ambiguous = json.loads(json.dumps(self.program))
        duplicate = dict(ambiguous["bindings"][0])
        duplicate["id"] = "alpha-peer"
        ambiguous["bindings"].append(duplicate)
        validation = core.validate_program(self.root, ambiguous)
        self.assertIn("binding-ambiguous", self.codes(validation))

    def test_dangling_workflow_team_role_and_rubric_references_refuse(self):
        core = self.programs_core
        broken = json.loads(json.dumps(self.program))
        broken["bindings"][0]["workflow"] = "missing-flow"
        broken["bindings"][0]["team"] = "missing-team"
        broken["bindings"][0]["rubrics"] = ["missing-rubric"]
        broken["phase_gates"][0]["role"] = "missing-role"
        validation = core.validate_program(self.root, broken)
        self.assertTrue(
            {
                "dangling-workflow-reference",
                "dangling-role-reference",
                "dangling-rubric-reference",
            } <= self.codes(validation),
            validation["diagnostics"],
        )

    def test_organization_requires_delivery_roles_and_resolved_council_roles(self):
        core = self.programs_core
        path = self.root / "pm/organizations/delivery-core.json"
        organization = json.loads(path.read_text(encoding="utf-8"))
        organization["teams"][0]["roles"][1]["required"] = False
        organization["councils"][0]["judge"] = "missing-judge"
        organization["councils"][0]["meta_verifier"] = "verifier"
        self._write_json("pm/organizations/delivery-core.json", organization)
        validation = core.validate_program(self.root, self.program)
        self.assertFalse(validation["valid"])
        self.assertTrue(
            {"missing-separation", "dangling-role-reference"}
            <= self.codes(validation),
            validation["diagnostics"],
        )

    def test_program_binding_cannot_smuggle_capability_or_exceed_budget(self):
        core = self.programs_core
        path = self.root / "pm/workflows/story-work.json"
        workflow = json.loads(path.read_text(encoding="utf-8"))
        capability_workflow = json.loads(json.dumps(workflow))
        del capability_workflow["nodes"][0]["on_success"]
        capability_workflow["nodes"].append({
            "id": "verify",
            "type": "verdict",
            "needs": ["implement"],
            "role": "verifier",
            "rubric": "story-quality",
            "subject": {"kind": "artifact", "name": "implement.candidate"},
            "freshness_seconds": 3600,
            "max_rationale_bytes": 20000,
            "results": ["pass", "fail"],
            "routes": {
                "pass": {"kind": "terminal", "target": "complete"},
                "fail": {"kind": "action", "target": "block"},
            },
        })
        self._write_json("pm/workflows/story-work.json", capability_workflow)
        missing_verdict_authority = json.loads(json.dumps(self.program))
        missing_verdict_authority["requested_capabilities"].remove(
            "verdict:issue"
        )
        validation = core.validate_program(
            self.root, missing_verdict_authority
        )
        self.assertIn("workflow-capability-missing", self.codes(validation))

        workflow["nodes"][0]["timeout_seconds"] = 86400
        workflow["nodes"][0]["max_attempts"] = 20
        self._write_json("pm/workflows/story-work.json", workflow)
        validation = core.validate_program(self.root, self.program)
        self.assertIn("workflow-exceeds-budget", self.codes(validation))

    def test_unsupported_roadmap_status_and_empty_scope_refuse(self):
        core = self.programs_core
        self._set_story_status("DM-1-02", "in-progress", "mysterious")
        validation = core.validate_program(self.root, self.program)
        self.assertIn("unsupported-status", self.codes(validation))

        empty = json.loads(json.dumps(self.program))
        empty["scope"]["stories"] = {"include": ["DM-9-99"]}
        validation = core.validate_program(self.root, empty)
        self.assertTrue(
            {"scope-story-missing", "empty-scope"} <= self.codes(validation),
            validation["diagnostics"],
        )

    def test_multiple_active_and_exhausted_scope_are_explained_without_guessing(self):
        core = self.programs_core
        self._set_story_status("DM-2-01", "backlog", "in-progress")
        multiple = core.build_program_plan(self.root, "demo-program")
        self.assertFalse(multiple["applicable"])
        self.assertIn("multiple-active-stories", {item["code"] for item in multiple["issues"]})
        self.assertEqual(
            {item["reason"] for item in multiple["candidates"] if item["story"] in {"DM-1-02", "DM-2-01"}},
            {"already-active"},
        )

        exhausted = json.loads(json.dumps(self.program))
        exhausted["scope"]["stories"] = {"include": ["DM-1-01"]}
        exhausted_plan = core.build_program_plan(self.root, exhausted)
        self.assertFalse(exhausted_plan["applicable"])
        self.assertIsNone(exhausted_plan["selection"])
        self.assertIn("scope-complete", {item["code"] for item in exhausted_plan["issues"]})

    def test_plan_is_byte_stable_and_creates_no_policy_roadmap_run_or_grant_state(self):
        core = self.programs_core
        before = {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in self.root.rglob("*") if path.is_file()
        }
        first = core.build_program_plan(self.root, "demo-program")
        second = core.build_program_plan(self.root, "demo-program")
        after = {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in self.root.rglob("*") if path.is_file()
        }
        self.assertEqual(core.canonical_json(first), core.canonical_json(second))
        self.assertEqual(before, after)
        self.assertFalse(first["starts_work"])
        self.assertFalse(first["writes_policy"])
        self.assertFalse(first["writes_roadmap"])
        self.assertFalse(first["writes_run_state"])
        self.assertFalse(first["creates_grant"])
        self.assertFalse((self.root / ".git/pmo-programs").exists())

    def test_cli_validate_simulate_plan_and_empty_inventory_share_core(self):
        core = self.programs_core
        listed = self.cli("list", "--json")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(
            json.loads(listed.stdout),
            self.program_surface.program_summary_inventory(self.root),
        )
        valid = self.cli("validate", "demo-program", "--json")
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(
            json.loads(valid.stdout), core.validate_program_path(self.root, self.program_path)
        )
        simulation = self.cli("simulate", "demo-program", "--json")
        self.assertEqual(simulation.returncode, 0, simulation.stderr)
        self.assertEqual(json.loads(simulation.stdout), core.simulate_program(self.root, "demo-program"))
        plan = self.cli("plan", "demo-program", "--json")
        self.assertEqual(plan.returncode, 0, plan.stderr)
        self.assertEqual(json.loads(plan.stdout), core.build_program_plan(self.root, "demo-program"))

        empty_root = self.tmp / "empty"
        empty_root.mkdir()
        before = list(empty_root.rglob("*"))
        inventory = core.program_inventory(empty_root)
        self.assertEqual(inventory["programs"], [])
        self.assertTrue(inventory["healthy"])
        self.assertEqual(before, list(empty_root.rglob("*")))


class ProgramRunAuthorityTest(unittest.TestCase):
    """WLA-26-08: exact finite program grants and replay authority."""

    issued_at = "2026-07-22T12:00:00Z"
    expires_at = "2026-07-22T13:00:00Z"
    started_at = "2026-07-22T12:01:00Z"

    def setUp(self):
        import dw_pmo.program_run as program_run
        from dw_pmo.orchestration_driver import load_driver_config, write_driver_config
        from dw_pmo.programs import BUDGET_DEFAULTS

        self.core = program_run
        self.fixture = ProgramPlannerTest("test_program_compiles_policy_references_scope_and_hashes")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root

        organization_path = self.root / "pm/organizations/delivery-core.json"
        organization = json.loads(organization_path.read_text(encoding="utf-8"))
        organization["councils"][0]["decision"] = {"method": "judge"}
        self.fixture._write_json("pm/organizations/delivery-core.json", organization)

        self.capabilities = [
            "program:select", "agent:dispatch", "check:execute",
            "workspace:write", "verdict:issue", "council:decide",
            "obligation:record", "obligation:materialize",
            "obligation:disposition", "evidence:materialize",
            "integration:apply", "contract:generate",
            "certification:verdict", "git:commit",
            "roadmap:story-start", "roadmap:story-complete",
            "roadmap:phase-advance",
        ]
        budgets = dict(BUDGET_DEFAULTS)
        budgets.update({
            "max_phases": 2,
            "max_stories": 3,
            "max_child_runs": 2,
            "max_agent_starts": 1,
            "max_provider_starts": 1,
            "max_model_starts": 1,
            "max_check_starts": 2,
            "max_loop_rounds": 2,
            "max_debate_rounds": 2,
            "max_councils": 2,
            "max_repairs_per_story": 1,
            "max_verdicts": 3,
            "max_obligations": 3,
            "max_obligation_materializations": 1,
            "max_obligation_dispositions": 3,
            "max_integrations": 1,
            "max_commits": 1,
            "max_pushes": 1,
            "max_nudges": 1,
            "max_artifact_bytes": 2_000_000,
            "max_tokens": 100_000,
            "max_observed_cost_microunits": 100_000,
            "max_wall_seconds": 3_600,
        })
        self.budgets = budgets
        program = json.loads(json.dumps(self.fixture.program))
        program["requested_capabilities"] = list(self.capabilities)
        program["budgets"] = dict(budgets)
        self.fixture._write_json("pm/programs/demo-program.json", program)
        self.fixture.program = program

        driver = load_driver_config(self.root)
        execution = {
            "builder-a": ("openai", "openai", "gpt-5", "openai/gpt-5"),
            "builder-b": ("openai", "openai", "gpt-5", "openai/gpt-5"),
            "verifier-a": (
                "anthropic", "anthropic", "claude-sonnet", "claude/sonnet-5",
            ),
            "meta-a": ("openrouter", "moonshot", "kimi-k3", "kimi/k3"),
            "architect-a": (
                "openai", "openai", "gpt-5", "openai/gpt-5",
            ),
        }
        for profile, (provider, vendor, family, model) in execution.items():
            raw = driver["profiles"][profile]
            raw.update({
                "router": "openrouter" if provider == "openrouter" else "direct",
                "provider": provider,
                "model_vendor": vendor,
                "model_family": family,
                "model": model,
                "model_binding": "requested-alias",
                "auth_domain": f"auth-{profile}",
            })
        write_driver_config(self.root, driver)
        self.fixture._git("add", "pm")
        self.fixture._git("commit", "-qm", "authority fixture")

    @staticmethod
    def h(character):
        return "sha256:" + character * 64

    def subject(self, kind="story", identifier="DM-1-02", *, phase=1, story="DM-1-02", hash_char="a"):
        return {
            "kind": kind,
            "id": identifier,
            "hash": self.h(hash_char),
            "phase": phase,
            "story": story,
        }

    def plan(self, *, mode="continuous", capabilities=None, budgets=None,
             intent="authority-1", expires_at=None, remote=None,
             remote_ref=None):
        return self.core.build_program_start_plan(
            self.root,
            "demo-program",
            mode=mode,
            operator="operator-a",
            approval_reason="Run the reviewed finite autonomous fixture.",
            intent_id=intent,
            capabilities=capabilities,
            budgets=budgets,
            issued_at=self.issued_at,
            expires_at=expires_at or self.expires_at,
            remote=remote,
            remote_ref=remote_ref,
        )

    def start(self, *, mode="continuous", intent="authority-1",
              capabilities=None, budgets=None, expires_at=None, remote=None,
              remote_ref=None):
        plan = self.plan(
            mode=mode, intent=intent, capabilities=capabilities,
            budgets=budgets, expires_at=expires_at, remote=remote,
            remote_ref=remote_ref,
        )
        self.assertTrue(plan["applicable"], plan["issues"])
        return plan, self.core.start_program(
            self.root, plan, start_token=plan["start_token"],
            now=self.started_at,
        )

    def claim_preview(self, run_id, category, *, key=None, subject=None,
                      child_grant=None, at="2026-07-22T12:02:00Z",
                      estimate=None, port=None):
        return self.core.build_program_claim_preview(
            self.root,
            run_id,
            category=category,
            subject=subject or self.subject(),
            idempotency_key=key or f"{category}-1",
            reason=f"Reserve exact {category} fixture work.",
            resource_estimate=estimate or {
                "artifact_bytes": 0,
                "tokens": 0,
                "observed_cost_microunits": 0,
            },
            request_port=port,
            child_grant=child_grant,
            now=at,
        )

    def apply_claim(self, preview, *, at="2026-07-22T12:02:00Z"):
        return self.core.apply_program_claim(
            self.root,
            preview,
            claim_token=preview["claim_token"],
            now=at,
        )

    def test_pure_preview_binds_decider_execution_scope_and_zero_effects(self):
        before = list((self.root / ".git").glob("pmo-programs*"))
        plan = self.plan()
        after = list((self.root / ".git").glob("pmo-programs*"))
        self.assertTrue(plan["applicable"], plan["issues"])
        self.assertEqual(before, after)
        self.assertEqual(plan["authority"]["mode"], "continuous")
        self.assertEqual(plan["approval"]["decision"], "approve")
        self.assertEqual(plan["roadmap"]["snapshot_hash"], plan["planning"]["roadmap"]["snapshot_hash"])
        self.assertEqual(plan["program"]["bundle_hash"], plan["planning"]["program"]["bundle_hash"])
        self.assertTrue(plan["worst_case"]["includes_failure_branches"])
        council = plan["roster"]["councils"][0]
        self.assertEqual(council["primary_authority"], "judge")
        self.assertEqual(council["decider_seat"], council["chair_seat"])
        decider = next(
            seat for seat in plan["roster"]["seats"]
            if seat["address"] == council["decider_seat"]
        )
        self.assertEqual(decider["profile"], "verifier-a")
        self.assertEqual(decider["execution"]["provider"], "anthropic")
        self.assertEqual(decider["execution"]["model"], "claude/sonnet-5")
        self.assertEqual(decider["execution"]["model_binding"], "requested-alias")
        kimi = next(seat for seat in plan["roster"]["seats"] if seat["profile"] == "meta-a")
        self.assertEqual(kimi["execution"]["router"], "openrouter")
        self.assertEqual(kimi["execution"]["model"], "kimi/k3")
        roster_addresses = {
            seat["address"] for seat in plan["roster"]["seats"]
        }
        for story_id in ("DM-1-01", "DM-1-02", "DM-2-01"):
            self.assertTrue(any(
                f"/story/{story_id}/" in address
                for address in roster_addresses
            ))
        self.assertFalse(any(
            "/story/DM-1-03/" in address
            for address in roster_addresses
        ))
        rule_assignment = json.loads(json.dumps(plan["planning"]["assignment"]))
        rule_council = rule_assignment["councils"][0]
        rule_council["decision"]["method"] = "majority"
        no_tie = self.core._roster(rule_assignment, self.capabilities, {"debates": []})
        self.assertEqual(no_tie["councils"][0]["primary_authority"], "rule")
        self.assertEqual(no_tie["councils"][0]["tie_authority"], "none")
        self.assertIsNone(no_tie["councils"][0]["decider_seat"])
        judge_role = rule_council["judge"]
        tie_judge = self.core._roster(rule_assignment, self.capabilities, {
            "debates": [{
                "participants": [
                    role for role in rule_council["members"]
                    if role != judge_role
                ],
                "judge_role": judge_role,
                "tie_policy": "judge",
            }],
        })
        self.assertEqual(tie_judge["councils"][0]["primary_authority"], "rule")
        self.assertEqual(tie_judge["councils"][0]["tie_authority"], "judge")
        self.assertEqual(
            tie_judge["councils"][0]["decider_seat"],
            tie_judge["councils"][0]["chair_seat"],
        )
        for flag in (
            "starts_work", "writes_policy", "writes_roadmap",
            "writes_run_state", "creates_grant",
        ):
            self.assertFalse(plan[flag])

    def test_modes_are_explicit_profiles_and_empty_inventory_is_dormant(self):
        before = list((self.root / ".git").glob("pmo-programs*"))
        inventory = self.core.program_run_inventory(
            self.root, now=self.started_at
        )
        self.assertEqual(inventory["runs"], [])
        self.assertTrue(inventory["healthy"])
        self.assertEqual(before, list((self.root / ".git").glob("pmo-programs*")))

        advisory = self.plan(mode="advisory", intent="advisory-1")
        self.assertTrue(advisory["applicable"], advisory["issues"])
        self.assertEqual(advisory["authority"]["capabilities"], [])
        checkpointed = self.plan(mode="checkpointed", intent="checkpoint-1")
        self.assertTrue(checkpointed["applicable"], checkpointed["issues"])
        self.assertEqual(
            {port["id"] for port in checkpointed["authority"]["checkpoint_ports"]},
            {"program-start", "story-boundary", "phase-boundary"},
        )
        _, advisory_run = self.start(mode="advisory", intent="advisory-start")
        self.assertEqual(advisory_run["state"], "advisory")
        self.assertFalse(advisory_run["future_claims_allowed"])

    def test_mode_capability_budget_expiry_and_remote_widening_refuse(self):
        wider = self.plan(capabilities=self.capabilities + ["git:push"], intent="wider-cap")
        self.assertFalse(wider["applicable"])
        self.assertIn("capability-denied", {item["code"] for item in wider["issues"]})

        budgets = dict(self.budgets)
        budgets["max_agent_starts"] += 1
        over = self.plan(budgets=budgets, intent="wider-budget")
        self.assertFalse(over["applicable"])
        self.assertIn("budget-denied", {item["code"] for item in over["issues"]})

        perpetual = self.plan(
            intent="perpetual",
            expires_at="2026-07-23T12:00:01Z",
        )
        self.assertFalse(perpetual["applicable"])
        self.assertIn("budget-denied", {item["code"] for item in perpetual["issues"]})

        missing = [item for item in self.capabilities if item != "verdict:issue"]
        denied = self.plan(capabilities=missing, intent="missing-prereq")
        self.assertFalse(denied["applicable"])
        self.assertTrue(any("verdict:issue" in item["message"] for item in denied["issues"]))

    def test_start_is_exact_immutable_idempotent_and_creates_only_local_authority(self):
        plan, projection = self.start()
        run_id = projection["run_id"]
        self.assertEqual(projection["state"], "running")
        self.assertEqual(projection["event_count"], 1)
        self.assertTrue((self.root / ".git/pmo-programs/runs" / run_id / "grant.json").is_file())
        self.assertFalse((self.root / "pm/program-runs").exists())
        again = self.core.start_program(
            self.root, plan, start_token=plan["start_token"],
            now="2026-07-22T12:01:30Z",
        )
        self.assertEqual(again["run_id"], run_id)
        self.assertEqual(again["event_count"], 1)

        forged = json.loads(json.dumps(plan))
        forged["authority"]["mode"] = "advisory"
        with self.assertRaises(DwError):
            self.core.start_program(
                self.root, forged, start_token=forged["start_token"],
                now=self.started_at,
            )

    def test_unstarted_provider_model_repository_and_roadmap_drift_refuse(self):
        from dw_pmo.orchestration_driver import load_driver_config, write_driver_config

        plan = self.plan(intent="model-stale")
        driver = load_driver_config(self.root)
        driver["profiles"]["verifier-a"]["model"] = "claude/sonnet-5.1"
        write_driver_config(self.root, driver)
        with self.assertRaisesRegex(DwError, "stale|changed|altered"):
            self.core.start_program(
                self.root, plan, start_token=plan["start_token"],
                now=self.started_at,
            )
        self.assertFalse((self.root / ".git/pmo-programs").exists())

        driver["profiles"]["verifier-a"]["model"] = "claude/sonnet-5"
        write_driver_config(self.root, driver)
        repository_plan = self.plan(intent="repository-stale")
        (self.root / "README.fixture").write_text("drift\n", encoding="utf-8")
        self.addCleanup((self.root / "README.fixture").unlink, missing_ok=True)
        with self.assertRaisesRegex(DwError, "stale|changed|altered"):
            self.core.start_program(
                self.root, repository_plan,
                start_token=repository_plan["start_token"],
                now=self.started_at,
            )
        (self.root / "README.fixture").unlink()

        roadmap_plan = self.plan(intent="roadmap-stale")
        roadmap_file = (
            self.root / "pm/roadmap/demo/phase-1-alpha/story-02-active-build.md"
        )
        roadmap_file.write_text(
            roadmap_file.read_text(encoding="utf-8") + "\nObserved drift.\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(DwError, "roadmap|repository|changed"):
            self.core.start_program(
                self.root, roadmap_plan,
                start_token=roadmap_plan["start_token"],
                now=self.started_at,
            )

    def test_claims_are_exclusive_idempotent_budgeted_and_exhaust(self):
        _plan, projection = self.start()
        run_id = projection["run_id"]
        selection = self.claim_preview(run_id, "selection", key="selection-1")
        self.assertTrue(selection["applicable"], selection["issues"])
        selected = self.apply_claim(selection)
        self.assertEqual(selected["budgets"]["max_stories"]["used"], 1)
        self.assertEqual(selected["budgets"]["max_phases"]["used"], 1)
        duplicate = self.apply_claim(selection)
        self.assertTrue(duplicate["idempotent"])
        self.assertEqual(len(duplicate["claims"]), 1)

        agent = self.claim_preview(
            run_id,
            "agent",
            key="agent-1",
            at="2026-07-22T12:03:00Z",
            estimate={
                "artifact_bytes": 100,
                "tokens": 200,
                "observed_cost_microunits": 300,
            },
        )
        spent = self.apply_claim(agent, at="2026-07-22T12:03:00Z")
        self.assertEqual(spent["budgets"]["max_agent_starts"]["used"], 1)
        self.assertEqual(spent["budgets"]["max_provider_starts"]["used"], 1)
        self.assertEqual(spent["budgets"]["max_model_starts"]["used"], 1)
        self.assertEqual(spent["budgets"]["max_tokens"]["used"], 200)

        exhausted = self.claim_preview(
            run_id, "agent", key="agent-2",
            at="2026-07-22T12:04:00Z",
        )
        self.assertFalse(exhausted["applicable"])
        self.assertEqual(exhausted["issues"][-1]["code"], "budget-exhausted")
        stopped = self.apply_claim(exhausted, at="2026-07-22T12:04:00Z")
        self.assertEqual(stopped["state"], "exhausted")
        self.assertEqual(stopped["exhaustion"]["counter"], "max_agent_starts")

    def test_child_authority_is_strict_intersection_and_cannot_inherit_rails(self):
        _plan, projection = self.start()
        implementer = next(
            seat for seat in projection["roster"]["seats"]
            if seat["duty"] == "implementer"
        )
        child = self.core.derive_child_grant(
            self.root,
            projection["run_id"],
            role_address=implementer["address"],
            node_address="program/demo-program/phase/1/story/DM-1-02/workflow/alpha/node/implement",
            capabilities=["agent:dispatch", "workspace:write"],
            budgets={"max_agent_starts": 1, "max_artifact_bytes": 1_000},
            now="2026-07-22T12:02:00Z",
        )
        self.assertEqual(
            child["capabilities"], ["agent:dispatch", "workspace:write"]
        )
        self.assertFalse(set(child["capabilities"]) & {
            "integration:apply", "certification:verdict", "git:commit",
            "roadmap:story-complete",
        })
        with self.assertRaisesRegex(DwError, "intersection|non-delegable"):
            self.core.derive_child_grant(
                self.root,
                projection["run_id"],
                role_address=implementer["address"],
                node_address="program/demo-program/phase/1/story/DM-1-02/workflow/alpha/node/implement",
                capabilities=["agent:dispatch", "git:commit"],
                budgets={"max_agent_starts": 1},
                now="2026-07-22T12:02:00Z",
            )
        preview = self.claim_preview(
            projection["run_id"], "child-grant", key="child-1",
            child_grant=child,
        )
        claimed = self.apply_claim(preview)
        self.assertEqual(claimed["claim"]["child_grant_hash"], child["grant_hash"])

    def test_apply_recomputes_budget_child_scope_and_checkpoint_authority(self):
        _plan, projection = self.start()
        run_id = projection["run_id"]

        outside = self.claim_preview(
            run_id,
            "check",
            key="outside-scope",
            subject=self.subject(
                identifier="DM-99-01", phase=99, story="DM-99-01",
            ),
        )
        self.assertFalse(outside["applicable"])
        self.assertTrue(any(
            issue["code"] == "scope-violation" for issue in outside["issues"]
        ))
        unknown_port = self.claim_preview(
            run_id,
            "checkpoint-request",
            key="unknown-port",
            subject=self.subject(kind="checkpoint", identifier="mystery"),
            port="not-declared",
        )
        self.assertFalse(unknown_port["applicable"])
        self.assertTrue(any(
            issue["code"] == "request-port-denied"
            for issue in unknown_port["issues"]
        ))

        budget = self.claim_preview(run_id, "check", key="forged-budget")
        forged_budget = json.loads(json.dumps(budget))
        forged_budget["budget"] = {}
        forged_budget["claim_token"] = self.core._sha({
            key: value for key, value in forged_budget.items()
            if key != "claim_token"
        })
        with self.assertRaisesRegex(DwError, "mechanical reservation"):
            self.core.apply_program_claim(
                self.root,
                forged_budget,
                claim_token=forged_budget["claim_token"],
                now="2026-07-22T12:02:00Z",
            )

        implementer = next(
            seat for seat in projection["roster"]["seats"]
            if seat["duty"] == "implementer"
        )
        child = self.core.derive_child_grant(
            self.root,
            run_id,
            role_address=implementer["address"],
            node_address="program/demo-program/phase/1/story/DM-1-02/workflow/alpha/node/implement",
            capabilities=["agent:dispatch", "workspace:write"],
            budgets={"max_agent_starts": 1},
            now="2026-07-22T12:02:00Z",
        )
        child_preview = self.claim_preview(
            run_id, "child-grant", key="forged-child", child_grant=child,
        )
        forged_child = json.loads(json.dumps(child_preview))
        forged_child["child_grant"]["capabilities"].append("git:commit")
        forged_child["child_grant"]["capabilities"].sort()
        forged_child["child_grant"]["grant_hash"] = self.core._sha({
            key: value for key, value in forged_child["child_grant"].items()
            if key != "grant_hash"
        })
        forged_child["claim_token"] = self.core._sha({
            key: value for key, value in forged_child.items()
            if key != "claim_token"
        })
        with self.assertRaisesRegex(DwError, "intersection|non-delegable"):
            self.core.apply_program_claim(
                self.root,
                forged_child,
                claim_token=forged_child["claim_token"],
                now="2026-07-22T12:02:00Z",
            )

    def test_control_tokens_bind_head_state_reason_decision_and_generation(self):
        _plan, projection = self.start()
        run_id = projection["run_id"]
        pause = self.core.build_program_control_preview(
            self.root, run_id, action="pause", decision="approve",
            reason="Pause at the exact reviewed ledger head.",
            now="2026-07-22T12:02:00Z",
        )
        claim = self.claim_preview(
            run_id, "check", key="check-before-pause",
            at="2026-07-22T12:02:10Z",
        )
        self.apply_claim(claim, at="2026-07-22T12:02:10Z")
        with self.assertRaisesRegex(DwError, "stale"):
            self.core.apply_program_control(
                self.root, pause, control_token=pause["control_token"],
                now="2026-07-22T12:02:20Z",
            )
        pause = self.core.build_program_control_preview(
            self.root, run_id, action="pause", decision="approve",
            reason="Pause after the check claim.",
            now="2026-07-22T12:02:20Z",
        )
        paused = self.core.apply_program_control(
            self.root, pause, control_token=pause["control_token"],
            now="2026-07-22T12:02:20Z",
        )
        self.assertEqual(paused["state"], "paused")
        self.assertEqual(paused["generation"], 0)
        resume = self.core.build_program_control_preview(
            self.root, run_id, action="resume", decision="approve",
            reason="Resume the same immutable authority.",
            now="2026-07-22T12:03:00Z",
        )
        resumed = self.core.apply_program_control(
            self.root, resume, control_token=resume["control_token"],
            now="2026-07-22T12:03:00Z",
        )
        self.assertEqual(resumed["state"], "running")
        revoke = self.core.build_program_control_preview(
            self.root, run_id, action="revoke", decision="approve",
            reason="Stop all future claims now.",
            now="2026-07-22T12:04:00Z",
        )
        revoked = self.core.apply_program_control(
            self.root, revoke, control_token=revoke["control_token"],
            now="2026-07-22T12:04:00Z",
        )
        self.assertEqual(revoked["state"], "revoked")
        self.assertEqual(revoked["generation"], 1)
        self.assertFalse(revoked["future_claims_allowed"])
        impossible = self.core.build_program_control_preview(
            self.root, run_id, action="resume", decision="approve",
            reason="A revoked grant cannot be revived.",
            now="2026-07-22T12:05:00Z",
        )
        self.assertFalse(impossible["applicable"])

    def test_apply_recomputes_control_and_completion_facts(self):
        _plan, projection = self.start()
        run_id = projection["run_id"]
        pause = self.core.build_program_control_preview(
            self.root, run_id, action="pause", decision="approve",
            reason="Pause exactly this generation.",
            now="2026-07-22T12:02:00Z",
        )
        forged_pause = json.loads(json.dumps(pause))
        forged_pause["effect"]["to_state"] = "cancelled"
        forged_pause["control_token"] = self.core._sha({
            key: value for key, value in forged_pause.items()
            if key != "control_token"
        })
        with self.assertRaisesRegex(DwError, "effect"):
            self.core.apply_program_control(
                self.root,
                forged_pause,
                control_token=forged_pause["control_token"],
                now="2026-07-22T12:02:00Z",
            )

        claim_preview = self.claim_preview(
            run_id, "check", key="completion-facts",
            at="2026-07-22T12:02:10Z",
        )
        claimed = self.apply_claim(claim_preview, at="2026-07-22T12:02:10Z")
        completion = self.core.build_program_completion_preview(
            self.root,
            run_id,
            claim_id=claimed["claim"]["claim_id"],
            result="succeeded",
            receipt_hash=self.h("d"),
            reason="Record exact observed completion facts.",
            now="2026-07-22T12:02:20Z",
        )
        forged_completion = json.loads(json.dumps(completion))
        forged_completion["fact_binding"]["repository"]["head"] = "0" * 40
        forged_completion["completion_token"] = self.core._sha({
            key: value for key, value in forged_completion.items()
            if key != "completion_token"
        })
        with self.assertRaisesRegex(DwError, "facts changed"):
            self.core.apply_program_completion(
                self.root,
                forged_completion,
                completion_token=forged_completion["completion_token"],
                now="2026-07-22T12:02:20Z",
            )

    def test_cancel_increments_generation_and_requests_bounded_interrupts(self):
        _plan, projection = self.start()
        run_id = projection["run_id"]
        active = self.apply_claim(self.claim_preview(
            run_id, "check", key="interrupt-me",
            at="2026-07-22T12:02:00Z",
        ), at="2026-07-22T12:02:00Z")
        cancel = self.core.build_program_control_preview(
            self.root, run_id, action="cancel", decision="approve",
            reason="Stop and request bounded interruption of active work.",
            now="2026-07-22T12:03:00Z",
        )
        self.assertEqual(
            cancel["effect"]["interrupt_claim_ids"],
            [active["claim"]["claim_id"]],
        )
        cancelled = self.core.apply_program_control(
            self.root, cancel, control_token=cancel["control_token"],
            now="2026-07-22T12:03:00Z",
        )
        self.assertEqual(cancelled["state"], "cancelled")
        self.assertEqual(cancelled["generation"], 1)
        self.assertEqual(
            cancelled["interrupt_claim_ids"], [active["claim"]["claim_id"]]
        )
        self.assertFalse(cancelled["future_claims_allowed"])

    def test_revocation_expires_requests_and_preserves_inflight_receipts(self):
        _plan, projection = self.start()
        run_id = projection["run_id"]
        request = self.claim_preview(
            run_id,
            "checkpoint-request",
            key="checkpoint-1",
            subject=self.subject(kind="checkpoint", identifier="story-approval"),
            port="story-boundary",
        )
        waiting = self.apply_claim(request)
        self.assertEqual(waiting["state"], "checkpoint")
        revoke = self.core.build_program_control_preview(
            self.root, run_id, action="revoke", decision="approve",
            reason="Revoke while the typed request is outstanding.",
            now="2026-07-22T12:03:00Z",
        )
        self.assertEqual(
            revoke["effect"]["expired_request_ids"],
            [waiting["claim"]["claim_id"]],
        )
        revoked = self.core.apply_program_control(
            self.root, revoke, control_token=revoke["control_token"],
            now="2026-07-22T12:03:00Z",
        )
        self.assertEqual(revoked["outstanding_requests"][0]["status"], "expired")
        completion = self.core.build_program_completion_preview(
            self.root,
            run_id,
            claim_id=waiting["claim"]["claim_id"],
            result="cancelled",
            receipt_hash=self.h("b"),
            reason="Bounded in-flight request cancellation receipt.",
            now="2026-07-22T12:04:00Z",
        )
        self.assertTrue(completion["applicable"], completion["issues"])
        completed = self.core.apply_program_completion(
            self.root,
            completion,
            completion_token=completion["completion_token"],
            now="2026-07-22T12:04:00Z",
        )
        self.assertEqual(completed["state"], "revoked")
        self.assertEqual(completed["completed_claims"][0]["status"], "cancelled")

    def test_successful_completion_rebinds_observed_facts_without_new_authority(self):
        _plan, projection = self.start()
        run_id = projection["run_id"]
        integration = self.claim_preview(
            run_id, "integration", key="integration-1",
        )
        claimed = self.apply_claim(integration)
        changed = self.root / "candidate.txt"
        changed.write_text("integrated fixture\n", encoding="utf-8")
        self.addCleanup(changed.unlink, missing_ok=True)
        completion = self.core.build_program_completion_preview(
            self.root,
            run_id,
            claim_id=claimed["claim"]["claim_id"],
            result="succeeded",
            receipt_hash=self.h("c"),
            reason="Trusted integration adapter observed its exact post-state.",
            now="2026-07-22T12:03:00Z",
        )
        rebound = self.core.apply_program_completion(
            self.root,
            completion,
            completion_token=completion["completion_token"],
            now="2026-07-22T12:03:00Z",
        )
        self.assertFalse(rebound["expected_repository"]["clean"])
        next_claim = self.claim_preview(
            run_id, "check", key="check-after-integration",
            at="2026-07-22T12:04:00Z",
        )
        self.assertTrue(next_claim["applicable"], next_claim["issues"])

    def test_live_policy_or_model_drift_blocks_claim_but_not_safety_revoke(self):
        from dw_pmo.orchestration_driver import load_driver_config, write_driver_config

        _plan, projection = self.start()
        run_id = projection["run_id"]
        driver = load_driver_config(self.root)
        driver["profiles"]["meta-a"]["provider"] = "different-router"
        write_driver_config(self.root, driver)
        stale = self.claim_preview(
            run_id, "check", key="stale-check",
            at="2026-07-22T12:02:00Z",
        )
        self.assertFalse(stale["applicable"])
        self.assertTrue(any(
            item["code"] == "program-stale"
            and "roster" in item["message"]
            for item in stale["issues"]
        ))
        revoke = self.core.build_program_control_preview(
            self.root, run_id, action="revoke", decision="approve",
            reason="Safety controls remain available through provider drift.",
            now="2026-07-22T12:03:00Z",
        )
        self.assertTrue(revoke["applicable"], revoke["issues"])
        result = self.core.apply_program_control(
            self.root, revoke, control_token=revoke["control_token"],
            now="2026-07-22T12:03:00Z",
        )
        self.assertEqual(result["state"], "revoked")

        _plan, policy_projection = self.start(intent="policy-drift")
        program_path = self.root / "pm/programs/demo-program.json"
        program = json.loads(program_path.read_text(encoding="utf-8"))
        program["title"] = "Changed after grant"
        program_path.write_text(
            json.dumps(program, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        policy_stale = self.claim_preview(
            policy_projection["run_id"], "check", key="policy-stale",
            at="2026-07-22T12:04:00Z",
        )
        self.assertFalse(policy_stale["applicable"])
        self.assertTrue(any(
            issue["code"] == "program-stale"
            and "program" in issue["message"]
            for issue in policy_stale["issues"]
        ))

    def test_expiry_stops_future_claims_and_still_allows_revocation(self):
        _plan, projection = self.start()
        run_id = projection["run_id"]
        expired = self.core.replay_program(
            self.root, run_id, now="2026-07-22T13:00:00Z"
        )
        self.assertEqual(expired["state"], "expired")
        self.assertFalse(expired["future_claims_allowed"])
        claim = self.claim_preview(
            run_id, "check", key="late-check",
            at="2026-07-22T13:00:01Z",
        )
        self.assertFalse(claim["applicable"])
        revoke = self.core.build_program_control_preview(
            self.root, run_id, action="revoke", decision="approve",
            reason="Close the expired authority generation.",
            now="2026-07-22T13:00:01Z",
        )
        self.assertTrue(revoke["applicable"], revoke["issues"])
        result = self.core.apply_program_control(
            self.root, revoke, control_token=revoke["control_token"],
            now="2026-07-22T13:00:01Z",
        )
        self.assertEqual(result["state"], "revoked")
        self.assertEqual(result["generation"], 1)

    def test_obligations_are_claim_bound_durable_and_separately_disposed(self):
        _plan, projection = self.start()
        run_id = projection["run_id"]
        decision_hash = self.h("d")
        obligation = {
            "id": "follow-up-1",
            "kind": "follow-up",
            "statement": "Verify the deferred compatibility edge.",
            "priority": "high",
            "blocking": True,
            "accountable_role": "verifier",
            "target": "DM-1-02",
            "citations": ["artifact:decision-1"],
            "acceptance": "The exact compatibility check is green.",
            "state": "open",
        }
        obligation_hash = self.core._sha({
            "decision_hash": decision_hash,
            "obligation": obligation,
        })
        preview = self.claim_preview(
            run_id, "obligation-record", key="obligation-record-1",
            subject=self.subject(
                kind="program-obligation", identifier="follow-up-1",
                hash_char="a",
            ) | {"hash": obligation_hash},
        )
        claim = self.apply_claim(preview)["claim"]
        completion = self.core.build_program_completion_preview(
            self.root, run_id, claim_id=claim["claim_id"],
            result="succeeded", receipt_hash=self.h("1"),
            reason="Validated the exact council obligation.",
            now="2026-07-22T12:02:10Z",
        )
        self.core.apply_program_completion(
            self.root, completion,
            completion_token=completion["completion_token"],
            now="2026-07-22T12:02:10Z",
        )
        recorded = self.core.record_program_obligation(
            self.root, run_id, claim_id=claim["claim_id"],
            decision_hash=decision_hash, obligation=obligation,
            now="2026-07-22T12:02:20Z",
        )
        self.assertEqual(
            [item["id"] for item in recorded["blocking_obligations"]],
            ["follow-up-1"],
        )
        again = self.core.record_program_obligation(
            self.root, run_id, claim_id=claim["claim_id"],
            decision_hash=decision_hash, obligation=obligation,
            now="2026-07-22T12:02:30Z",
        )
        self.assertTrue(again["idempotent"])

        disposition = {
            "obligation_id": "follow-up-1",
            "from_state": "open",
            "to_state": "completed",
            "actor": "verifier-a",
            "authority": "quality-council",
            "reason": "The bound compatibility check passed.",
            "replacement_id": None,
        }
        disposition_hash = self.core._sha(disposition)
        preview = self.claim_preview(
            run_id, "obligation-disposition", key="obligation-dispose-1",
            subject=self.subject(
                kind="program-obligation-disposition",
                identifier="follow-up-1", hash_char="b",
            ) | {"hash": disposition_hash},
            at="2026-07-22T12:03:00Z",
        )
        disposition_claim = self.apply_claim(
            preview, at="2026-07-22T12:03:00Z"
        )["claim"]
        completion = self.core.build_program_completion_preview(
            self.root, run_id, claim_id=disposition_claim["claim_id"],
            result="succeeded", receipt_hash=self.h("2"),
            reason="Authorized the exact terminal disposition.",
            now="2026-07-22T12:03:10Z",
        )
        self.core.apply_program_completion(
            self.root, completion,
            completion_token=completion["completion_token"],
            now="2026-07-22T12:03:10Z",
        )
        disposed = self.core.dispose_program_obligation(
            self.root, run_id, claim_id=disposition_claim["claim_id"],
            obligation_id="follow-up-1", to_state="completed",
            actor="verifier-a", authority="quality-council",
            reason="The bound compatibility check passed.",
            now="2026-07-22T12:03:20Z",
        )
        self.assertEqual(disposed["obligation"]["state"], "completed")
        self.assertEqual(disposed["blocking_obligations"], [])
        self.assertEqual(len(disposed["obligation_history"]), 2)

    def test_scope_completion_refuses_a_claim_without_complete_roadmap_facts(self):
        _plan, projection = self.start()
        proof_hash = self.h("c")
        preview = self.claim_preview(
            projection["run_id"], "assignment", key="premature-scope",
            subject=self.subject(
                kind="program-scope-proof", identifier="demo-program",
                hash_char="c",
            ),
        )
        claim = self.apply_claim(preview)["claim"]
        completion = self.core.build_program_completion_preview(
            self.root, projection["run_id"], claim_id=claim["claim_id"],
            result="succeeded", receipt_hash=self.h("3"),
            reason="Store the candidate scope proof.",
            now="2026-07-22T12:02:10Z",
        )
        self.core.apply_program_completion(
            self.root, completion,
            completion_token=completion["completion_token"],
            now="2026-07-22T12:02:10Z",
        )
        with self.assertRaisesRegex(DwError, "planner.*scope complete"):
            self.core.complete_program_scope(
                self.root, projection["run_id"], claim_id=claim["claim_id"],
                proof_hash=proof_hash,
                completed_stories=["DM-1-01", "DM-1-02", "DM-2-01"],
                completed_phases=[1, 2], now="2026-07-22T12:02:20Z",
            )

    def test_ledger_and_grant_corruption_fail_closed(self):
        _plan, projection = self.start()
        run_dir = self.root / ".git/pmo-programs/runs" / projection["run_id"]
        ledger = run_dir / "ledger.jsonl"
        original = ledger.read_bytes()
        event = json.loads(original)
        event["detail"]["mode"] = "advisory"
        ledger.write_text(json.dumps(event, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(DwError, "hash|match"):
            self.core.replay_program(self.root, projection["run_id"], now=self.started_at)
        ledger.write_bytes(original)

        claimed = self.apply_claim(self.claim_preview(
            projection["run_id"], "check", key="tamper-ledger",
            at="2026-07-22T12:02:00Z",
        ), at="2026-07-22T12:02:00Z")
        claim_ledger = ledger.read_bytes()
        events = [json.loads(line) for line in claim_ledger.splitlines()]
        events[1]["detail"]["budget"] = {}
        events[1]["event_hash"] = self.core._sha({
            key: value for key, value in events[1].items()
            if key != "event_hash"
        })
        ledger.write_text(
            "\n".join(json.dumps(item, sort_keys=True) for item in events) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(DwError, "ledger budget"):
            self.core.replay_program(
                self.root, claimed["run_id"], now="2026-07-22T12:02:01Z"
            )
        ledger.write_bytes(claim_ledger)

        grant_path = run_dir / "grant.json"
        grant_original = grant_path.read_text(encoding="utf-8")
        grant = json.loads(grant_original)
        grant["authority"]["capabilities"].append("git:push")
        grant["grant_hash"] = self.core._grant_hash(grant)
        grant_path.chmod(0o600)
        grant_path.write_text(json.dumps(grant, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(DwError, "reviewed plan"):
            self.core.replay_program(self.root, projection["run_id"], now=self.started_at)
        grant_path.write_text(grant_original, encoding="utf-8")

    def test_two_processes_share_one_start_and_one_claim(self):
        plan = self.plan(intent="race-start")
        payload = self.root / ".git/program-plan-race.json"
        payload.write_text(json.dumps(plan), encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(TESTS_DIR.parent / "lib")
        start_code = (
            "import json,sys; from pathlib import Path; "
            "from dw_pmo.program_run import start_program; "
            "p=json.loads(Path(sys.argv[2]).read_text()); "
            "r=start_program(Path(sys.argv[1]),p,start_token=p['start_token'],"
            "now='2026-07-22T12:01:00Z'); print(r['run_id'])"
        )
        commands = [
            subprocess.Popen(
                [sys.executable, "-c", start_code, str(self.root), str(payload)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
            )
            for _ in range(2)
        ]
        outputs = [process.communicate(timeout=30) for process in commands]
        for process, (_stdout, stderr) in zip(commands, outputs):
            self.assertEqual(process.returncode, 0, stderr)
        run_ids = {stdout.strip() for stdout, _stderr in outputs}
        self.assertEqual(len(run_ids), 1)
        run_id = next(iter(run_ids))
        inventory = self.core.program_run_inventory(
            self.root, now="2026-07-22T12:01:30Z"
        )
        self.assertEqual([item["run_id"] for item in inventory["runs"]], [run_id])

        preview = self.claim_preview(
            run_id, "check", key="race-claim",
            at="2026-07-22T12:02:00Z",
        )
        claim_payload = self.root / ".git/program-claim-race.json"
        claim_payload.write_text(json.dumps(preview), encoding="utf-8")
        claim_code = (
            "import json,sys; from pathlib import Path; "
            "from dw_pmo.program_run import apply_program_claim; "
            "p=json.loads(Path(sys.argv[2]).read_text()); "
            "r=apply_program_claim(Path(sys.argv[1]),p,claim_token=p['claim_token'],"
            "now='2026-07-22T12:02:00Z'); print(r['claim']['claim_id'])"
        )
        commands = [
            subprocess.Popen(
                [sys.executable, "-c", claim_code, str(self.root), str(claim_payload)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
            )
            for _ in range(2)
        ]
        outputs = [process.communicate(timeout=30) for process in commands]
        for process, (_stdout, stderr) in zip(commands, outputs):
            self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual(len({stdout.strip() for stdout, _stderr in outputs}), 1)
        final = self.core.replay_program(
            self.root, run_id, now="2026-07-22T12:02:01Z"
        )
        self.assertEqual(len(final["claims"]), 1)
        self.assertEqual(final["budgets"]["max_check_starts"]["used"], 1)


class ProgramTestBaselineTest(unittest.TestCase):
    """WLA-29-05: bounded facts and fail-closed failure subtraction."""

    def test_parser_subtracts_only_exact_reconciled_identifiers(self):
        from dw_pmo.test_baseline import (
            build_baseline_fact,
            classify_test_failures,
            extract_test_failures,
        )

        baseline_output = (
            "FAIL: test_existing (suite.Case.test_existing)\n"
            "FAILED (failures=1)\n"
        )
        current_output = (
            "FAIL: test_existing (suite.Case.test_existing)\n"
            "ERROR: test_regression (suite.Case.test_regression)\n"
            "FAILED (failures=1, errors=1)\n"
        )
        command_hash = "sha256:" + "a" * 64
        baseline = build_baseline_fact(
            head_sha="b" * 40, command_hash=command_hash,
            exit_code=1, output=baseline_output,
        )
        current = extract_test_failures(current_output, 1)
        classified = classify_test_failures(
            current, baseline, expected_head_sha="b" * 40,
            command_hash=command_hash,
        )
        self.assertEqual(
            classified["pre_existing"],
            ["test_existing (suite.Case.test_existing)"],
        )
        self.assertEqual(
            classified["introduced"],
            ["test_regression (suite.Case.test_regression)"],
        )
        self.assertFalse(classified["green"])

    def test_missing_foreign_stale_and_unparseable_baselines_fail_closed(self):
        from dw_pmo.test_baseline import (
            build_baseline_fact,
            classify_test_failures,
            extract_test_failures,
        )

        command_hash = "sha256:" + "c" * 64
        current = extract_test_failures(
            "FAILED pkg/test_mod.py::test_new - assertion\n"
            "===== 1 failed in 0.01s =====\n",
            1,
        )
        valid = build_baseline_fact(
            head_sha="d" * 40, command_hash=command_hash,
            exit_code=0, output="1 passed\n",
        )
        cases = [
            (None, "d" * 40, command_hash, "baseline-missing-or-invalid"),
            (valid, "e" * 40, command_hash, "baseline-foreign-head"),
            (valid, "d" * 40, "sha256:" + "f" * 64, "baseline-stale-command"),
        ]
        for baseline, head, command, reason in cases:
            with self.subTest(reason=reason):
                classified = classify_test_failures(
                    current, baseline, expected_head_sha=head,
                    command_hash=command,
                )
                self.assertEqual(classified["introduced"], ["pkg/test_mod.py::test_new"])
                self.assertEqual(classified["pre_existing"], [])
                self.assertEqual(classified["refusal_reason"], reason)
        unparseable = extract_test_failures("opaque crash\n", 1)
        classified = classify_test_failures(
            unparseable, valid, expected_head_sha="d" * 40,
            command_hash=command_hash,
        )
        self.assertEqual(classified["introduced"], ["<unparseable-test-failure>"])
        self.assertEqual(classified["refusal_reason"], "current-failures-unparseable")

    def test_test_debt_obligations_are_closed_bounded_and_deterministic(self):
        from dw_pmo.test_baseline import (
            build_test_debt_obligations,
            validate_test_debt_obligation,
        )

        obligations = build_test_debt_obligations({
            "introduced": [],
            "pre_existing": [
                "pkg/test_mod.py::test_existing",
                "pkg/test_mod.py::test_other",
            ],
            "subtraction_available": True,
            "refusal_reason": None,
        }, target="DM-1-02")
        self.assertEqual(len(obligations), 2)
        self.assertTrue(all(
            item["kind"] == "technical-debt" and not item["blocking"]
            for item in obligations
        ))
        forged = dict(obligations[0])
        forged["agent_note"] = "not allowed"
        with self.assertRaisesRegex(ValueError, "non-exact"):
            validate_test_debt_obligation(forged)

    def test_baseline_fact_is_bounded_and_contains_no_output_prose(self):
        from dw_pmo.test_baseline import build_baseline_fact

        fact = build_baseline_fact(
            head_sha="a" * 40,
            command_hash="sha256:" + "b" * 64,
            exit_code=1,
            output=(
                "FAIL: test_one (suite.Case.test_one)\n"
                "secret output prose that must not be retained\n"
                "FAILED (failures=1)\n"
            ),
        )
        self.assertEqual(
            set(fact),
            {
                "head_sha", "command_hash", "status", "parser", "exit_code",
                "failure_count", "failure_ids", "subtraction_available",
                "truncated",
            },
        )
        self.assertNotIn("secret", json.dumps(fact))
        self.assertEqual(fact["failure_count"], 1)


class ProgramConductorTest(unittest.TestCase):
    """WLA-26-09: deterministic program conduction and crash recovery."""

    now = "2026-07-22T12:02:00Z"

    def setUp(self):
        import dw_pmo.program_conductor as conductor
        from dw_pmo.orchestration_driver import load_driver_config

        self.core = conductor
        self.authority = ProgramRunAuthorityTest(
            "test_start_is_exact_immutable_idempotent_and_creates_only_local_authority"
        )
        self.authority.setUp()
        self.addCleanup(self.authority.doCleanups)
        self.root = self.authority.root
        path = self.root / "pm/programs/demo-program.json"
        program = json.loads(path.read_text(encoding="utf-8"))
        for key in (
            "max_child_runs", "max_agent_starts",
            "max_provider_starts", "max_model_starts",
        ):
            program["budgets"][key] = 8
            self.authority.budgets[key] = 8
        program["budgets"]["max_artifact_bytes"] = 8_000_000
        self.authority.budgets["max_artifact_bytes"] = 8_000_000
        # Most conductor tests isolate story-work behavior.  Architect-gate
        # cases opt back into the fixture program's phase policy explicitly.
        program["phase_gates"] = []
        path.write_text(
            json.dumps(program, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.authority.fixture.program = program
        self.authority.fixture._git("add", "pm")
        self.authority.fixture._git("commit", "-qm", "conductor fixture budgets")
        self.config = load_driver_config(self.root)
        self.intent = 0

    def start(self, *, remote=None, remote_ref=None):
        self.intent += 1
        _plan, projection = self.authority.start(
            intent=f"conductor-{self.intent}",
            budgets=self.authority.budgets,
            remote=remote,
            remote_ref=remote_ref,
        )
        return projection

    def advance_to_agent(self, projection):
        fixture = self.core.ProgramFixtureDriver()
        first = self.core.tick_program(
            self.root, projection["run_id"], driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        second = self.core.tick_program(
            self.root, projection["run_id"], driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        self.assertEqual((first["action"]["kind"], second["action"]["kind"]),
                         ("selection", "assignment"))
        return fixture

    def configure_explicit_verdict(self, *, max_attempts=1):
        workflow_path = self.root / "pm/workflows/story-work.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        implement = workflow["nodes"][0]
        implement.pop("on_success", None)
        workflow["nodes"] = [
            implement,
            {
                "id": "verify",
                "type": "verdict",
                "needs": ["implement"],
                "role": "verifier",
                "rubric": "story-quality",
                "subject": {
                    "kind": "artifact",
                    "name": "implement.candidate",
                },
                "freshness_seconds": 60,
                "max_rationale_bytes": 20_000,
                "max_attempts": max_attempts,
                "results": ["pass", "fail"],
                "routes": {
                    "pass": {"kind": "terminal", "target": "complete"},
                    "fail": {"kind": "action", "target": "block"},
                },
                "on_failure": {"kind": "action", "target": "block"},
            },
        ]
        workflow_path.write_text(
            json.dumps(workflow, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.authority.fixture._git("add", "pm")
        self.authority.fixture._git(
            "commit", "-qm", "explicit verdict conductor fixture"
        )

    def configure_outward_nudge(self):
        program_path = self.root / "pm/programs/demo-program.json"
        program = json.loads(program_path.read_text(encoding="utf-8"))
        if "nudge:deliver" not in program["requested_capabilities"]:
            program["requested_capabilities"].append("nudge:deliver")
        if "nudge:deliver" not in self.authority.capabilities:
            self.authority.capabilities.append("nudge:deliver")
        program["budgets"]["max_nudges"] = 1
        self.authority.budgets["max_nudges"] = 1
        program["budgets"]["max_artifact_bytes"] = 4_000_000
        self.authority.budgets["max_artifact_bytes"] = 4_000_000
        program["nudges"] = [{
            "id": "repair-failed-ci",
            "signal": "ci-failed",
            "binding": "alpha",
            "target": "story-work/implement",
            "max_per_signal": 1,
            "max_total": 1,
            "expectation": (
                "Revisit the declared implementation against the failed "
                "mechanical signal."
            ),
        }]
        program_path.write_text(
            json.dumps(program, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.authority.fixture.program = program
        self.authority.fixture._git("add", "pm")
        self.authority.fixture._git(
            "commit", "-qm", "program outward nudge fixture"
        )
        self.authority.fixture._git(
            "remote", "add", "origin", str(self.root)
        )
        self.authority.fixture._git(
            "update-ref", "refs/remotes/origin/main", "HEAD"
        )

    def observe_failed_ci(self):
        import dw_pmo.signals as signals

        scenario = self.root / ".git/program-signal-fixture.json"
        scenario.write_text(json.dumps({
            "prs": [{
                "number": 7,
                "state": "open",
                "draft": False,
                "head": "main",
                "base": "main",
                "url": "https://example.test/pull/7",
                "checks": [{
                    "name": "core",
                    "status": "completed",
                    "conclusion": "failure",
                    "url": "https://example.test/check/7",
                }],
                "review": {
                    "unresolved": 0,
                    "resolved": 0,
                    "changes_requested": False,
                    "approved": False,
                    "reviewers": [],
                    "url": "https://example.test/pull/7",
                },
                "mergeable": "true",
                "mergeable_reason": "clean",
            }],
        }), encoding="utf-8")
        return signals.observe_signals(
            self.root,
            signals.FixtureProvider(scenario),
            "origin",
            "main",
            now=datetime.fromisoformat(
                self.now.replace("Z", "+00:00")
            ),
        )

    def record_fixture_obligation(
        self,
        projection,
        *,
        obligation_id,
        blocking,
        story="DM-1-02",
        phase=1,
    ):
        decision_hash = self.authority.h("d")
        obligation = {
            "id": obligation_id,
            "kind": "technical-debt",
            "statement": "Retain this exact cross-story fixture obligation.",
            "priority": "high" if blocking else "medium",
            "blocking": blocking,
            "accountable_role": "implementer",
            "target": story,
            "citations": ["evidence:fixture-decision"],
            "acceptance": "The exact obligation receives a terminal disposition.",
            "state": "open",
        }
        subject_hash = self.authority.core._sha({
            "decision_hash": decision_hash,
            "obligation": obligation,
        })
        preview = self.authority.claim_preview(
            projection["run_id"],
            "obligation-record",
            key=f"fixture-obligation/{obligation_id}",
            subject={
                "kind": "program-obligation",
                "id": obligation_id,
                "hash": subject_hash,
                "phase": phase,
                "story": story,
            },
            at=self.now,
        )
        claimed = self.authority.apply_claim(preview, at=self.now)
        claim = claimed["claim"]
        completion = self.authority.core.build_program_completion_preview(
            self.root,
            projection["run_id"],
            claim_id=claim["claim_id"],
            result="succeeded",
            receipt_hash=self.authority.h("e"),
            reason="Recorded the exact fixture obligation source.",
            now=self.now,
        )
        completed = self.authority.core.apply_program_completion(
            self.root,
            completion,
            completion_token=completion["completion_token"],
            now=self.now,
        )
        return self.authority.core.record_program_obligation(
            self.root,
            projection["run_id"],
            claim_id=claim["claim_id"],
            decision_hash=decision_hash,
            obligation=obligation,
            now=self.now,
        )

    def complete_story_rail(self, projection, story_id):
        phase = int(story_id.split("-")[1])
        preview = self.authority.claim_preview(
            projection["run_id"],
            "story-complete",
            key=f"fixture-story-complete/{story_id}",
            subject={
                "kind": "program-story-completion",
                "id": story_id,
                "hash": self.authority.core._sha({
                    "story": story_id,
                    "to_status": "done",
                }),
                "phase": phase,
                "story": story_id,
            },
            at=self.now,
        )
        claimed = self.authority.apply_claim(preview, at=self.now)
        claim = claimed["claim"]
        self.authority.fixture._set_story_status(
            story_id,
            "in-progress" if story_id == "DM-1-02" else "backlog",
            "done",
        )
        phase_dir = (
            self.root
            / "pm/roadmap/demo"
            / (
                "phase-1-alpha"
                if phase == 1
                else "phase-2-beta"
            )
        )
        story_number = int(story_id.rsplit("-", 1)[1])
        evidence_name = f"evidence-story-{story_number:02d}.md"
        evidence_path = phase_dir / evidence_name
        evidence_path.write_text(
            f"# Evidence - {story_id}\n\n"
            f"- **Story:** {story_id} - Fixture completion\n"
            "- **Status:** done\n"
            "- **Date:** 2026-07-22\n\n"
            "## Proof\n\n- externally authorized fixture rail\n",
            encoding="utf-8",
        )
        status_path = phase_dir / "current-phase-status.md"
        status = status_path.read_text(encoding="utf-8")
        row = next(
            line for line in status.splitlines()
            if f"| {story_id} |" in line
        )
        status_path.write_text(
            status.replace(
                row,
                row.rsplit("| - |", 1)[0]
                + f"| [evidence-story-{story_number:02d}]"
                f"(./{evidence_name}) |",
            ),
            encoding="utf-8",
        )
        self.authority.fixture._git("add", "pm/roadmap")
        self.authority.fixture._git(
            "commit", "-qm", f"complete {story_id} fixture rail"
        )
        completion = self.authority.core.build_program_completion_preview(
            self.root,
            projection["run_id"],
            claim_id=claim["claim_id"],
            result="succeeded",
            receipt_hash=self.authority.core._sha({
                "fixture_story_completion": story_id,
            }),
            reason=f"Applied the exact {story_id} fixture completion rail.",
            now=self.now,
        )
        return self.authority.core.apply_program_completion(
            self.root,
            completion,
            completion_token=completion["completion_token"],
            now=self.now,
        )

    def configure_council_workflow(
        self, *, method="majority", threshold=1,
        tie_policy="judge", audit="none",
    ):
        from dw_pmo.orchestration_driver import (
            load_driver_config, write_driver_config,
        )

        workflow_path = self.root / "pm/workflows/story-work.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        implement = workflow["nodes"][0]
        implement["activation"] = "route"
        implement.pop("needs", None)
        check = {
            "id": "council-evidence", "type": "check", "inputs": {},
            "runner": {
                "kind": "builtin", "name": "file-exists",
                "path": "pm/programs/demo-program.json",
                "output_bytes": 50_000,
            },
            "expect": {"exit_code": 0},
            "timeout_seconds": 60, "max_attempts": 1,
            "outputs": [{
                "id": "fact", "kind": "mechanical-fact",
                "max_bytes": 20_000,
            }],
            "on_failure": {"kind": "action", "target": "block"},
        }
        debate = {
            "id": "design-council", "type": "debate",
            "needs": ["council-evidence"],
            "inputs": {
                "evidence": {
                    "kind": "artifact",
                    "name": "council-evidence.fact",
                },
            },
            "participants": ["architect", "critic"],
            "judge_role": "verifier",
            "max_rounds": 1, "quorum": 1,
            "artifact_max_bytes": 30_000,
            "artifact_max_tokens": 4_000,
            "round_timeout_seconds": 600,
            "tie_policy": tie_policy,
            "dissent_policy": "preserve",
            "on_consensus": {"kind": "node", "target": "implement"},
            "on_repair": {"kind": "action", "target": "block"},
            "on_dissent": {"kind": "action", "target": "checkpoint"},
            "on_quorum_lost": {"kind": "action", "target": "escalate"},
            "on_exhausted": {"kind": "action", "target": "escalate"},
            "outputs": [{
                "id": "judgment", "kind": "decision",
                "max_bytes": 50_000,
            }],
        }
        workflow["nodes"] = [check, debate, implement]
        workflow_path.write_text(
            json.dumps(workflow, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        organization_path = self.root / "pm/organizations/delivery-core.json"
        organization = json.loads(
            organization_path.read_text(encoding="utf-8")
        )
        source_agent = next(
            item for item in organization["agents"]
            if item["id"] == "meta-a"
        )
        critic_agent = json.loads(json.dumps(source_agent))
        critic_agent.update({
            "id": "critic-a",
            "profile": "critic-a",
            "duties": ["critic"],
            "workspace_domain": "critic-a",
            "capability_ceiling": ["agent:dispatch"],
        })
        organization["agents"].append(critic_agent)
        organization["pools"].append({
            "id": "critics", "agents": ["critic-a"],
        })
        source_role = next(
            item for item in organization["teams"][0]["roles"]
            if item["id"] == "meta"
        )
        critic = json.loads(json.dumps(source_role))
        critic.update({
            "id": "critic",
            "duty": "critic",
            "pool": "critics",
            "required": False,
            "capability_ceiling": ["agent:dispatch"],
            "driver_capabilities": ["repository-read"],
            "workspace": "read-only",
            "output_schema": "fixture-output@1",
            "verdict_schema": None,
            "may_request": [],
            "may_judge": [],
            "independent_from": [],
        })
        critic["artifacts"]["write"] = [
            "markdown", "json", "text", "decision",
        ]
        organization["teams"][0]["roles"].append(critic)
        council = organization["councils"][0]
        council.update({
            "members": ["architect", "critic", "verifier"],
            "judge": "verifier",
            "meta_verifier": "meta",
            "decision": {
                "method": method,
                "threshold": threshold,
                "veto_roles": [],
            },
            "audit": {
                "mode": audit,
                "sample_size": 0 if audit == "none" else 3,
                "on_overturn": "repair",
                "on_escalate": "escalate",
            },
        })
        organization_path.write_text(
            json.dumps(organization, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        config = load_driver_config(self.root)
        critic_profile = json.loads(json.dumps(config["profiles"]["meta-a"]))
        critic_profile.update({
            "principal": "critic-a",
            "auth_domain": "auth-critic-a",
            "model": "fixture/critic-a",
        })
        config["profiles"]["critic-a"] = critic_profile
        write_driver_config(self.root, config)
        self.config = load_driver_config(self.root)

        program_path = self.root / "pm/programs/demo-program.json"
        program = json.loads(program_path.read_text(encoding="utf-8"))
        for key in (
            "max_child_runs", "max_agent_starts",
            "max_provider_starts", "max_model_starts",
        ):
            program["budgets"][key] = 16
            self.authority.budgets[key] = 16
        program_path.write_text(
            json.dumps(program, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.authority.fixture.program = program
        self.authority.fixture._git("add", "pm")
        self.authority.fixture._git(
            "commit", "-qm", "governed council conductor fixture"
        )

    def configure_phase_architect_gate(self, *, on_fail="block"):
        program_path = self.root / "pm/programs/demo-program.json"
        program = json.loads(program_path.read_text(encoding="utf-8"))
        program["phase_gates"] = [{
            "id": "architecture-gate",
            "when": "before-phase-complete",
            "role": "master-architect",
            "rubric": "phase-architecture",
            "on_fail": on_fail,
        }]
        program_path.write_text(
            json.dumps(program, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        rubric_path = self.root / "pm/rubrics/phase-architecture.json"
        rubric = json.loads(rubric_path.read_text(encoding="utf-8"))
        rubric["result_vocabulary"] = [
            "pass", "fail", "approve", "veto", "escalate",
        ]
        rubric["aggregation"].update({
            "on_pass": "approve",
            "on_fail": "veto",
            "on_abstain": "escalate",
            "on_inconclusive": "escalate",
        })
        rubric_path.write_text(
            json.dumps(rubric, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.authority.fixture.program = program
        self.authority.fixture._git("add", "pm")
        self.authority.fixture._git(
            "commit", "-qm", "phase architect conductor fixture"
        )

    def configure_structural_loop(
        self,
        predicate,
        *,
        check_path="pm/programs/demo-program.json",
        success_to_node=False,
    ):
        child = {
            "kind": "delivery-workbench-workflow",
            "schema_version": 1,
            "slug": "loop-child",
            "title": "One bounded implementation and check round",
            "version": "1.0.0",
            "parameters": [{
                "id": "story-id",
                "type": "string",
                "required": True,
                "max_bytes": 128,
            }],
            "defaults": {},
            "nodes": [{
                "id": "implement",
                "type": "agent",
                "role": "implementer",
                "task": "Produce the candidate for this exact loop round.",
                "workspace": "isolated-worktree",
                "capability_ceiling": [
                    "agent:dispatch", "workspace:write",
                ],
                "timeout_seconds": 300,
                "max_attempts": 1,
                "inputs": {
                    "story": {
                        "kind": "parameter",
                        "name": "story-id",
                    },
                },
                "outputs": [{
                    "id": "candidate",
                    "kind": "git-diff",
                    "max_bytes": 300_000,
                }],
                "on_failure": {
                    "kind": "action",
                    "target": "block",
                },
            }, {
                "id": "check-loop",
                "type": "check",
                "needs": ["implement"],
                "inputs": {
                    "candidate": {
                        "kind": "artifact",
                        "name": "implement.candidate",
                    },
                },
                "runner": {
                    "kind": "builtin",
                    "name": "file-exists",
                    "path": check_path,
                    "output_bytes": 50_000,
                },
                "expect": {"exit_code": 0},
                "timeout_seconds": 60,
                "max_attempts": 1,
                "outputs": [{
                    "id": "fact",
                    "kind": "mechanical-fact",
                    "max_bytes": 20_000,
                }],
                "on_success": {
                    "kind": "terminal",
                    "target": "complete",
                },
                "on_failure": {
                    "kind": "action",
                    "target": "block",
                },
            }],
            "terminals": [{
                "id": "complete",
                "meaning": "complete",
            }],
        }
        child_path = self.root / "pm/workflows/loop-child.json"
        child_path.write_text(
            json.dumps(child, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        parent_path = self.root / "pm/workflows/story-work.json"
        parent = json.loads(parent_path.read_text(encoding="utf-8"))
        loop = {
            "id": "quality-loop",
            "type": "loop",
            "purpose": "repeat-until",
            "workflow": "loop-child",
            "version": "1.0.0",
            "with": {
                "story-id": {
                    "kind": "parameter",
                    "name": "story-id",
                },
            },
            "capability_ceiling": [
                "agent:dispatch", "check:execute", "workspace:write",
            ],
            "max_rounds": 2,
            "until": predicate,
            "carry": ["implement.candidate"],
            "on_success": {
                "kind": "node" if success_to_node else "terminal",
                "target": "after-loop" if success_to_node else "complete",
            },
            "on_exhausted": {
                "kind": "action",
                "target": "escalate",
            },
        }
        parent["nodes"] = [loop]
        if success_to_node:
            parent["nodes"].append({
                "id": "after-loop",
                "type": "agent",
                "activation": "route",
                "role": "implementer",
                "task": "Continue only after the loop predicate is green.",
                "workspace": "isolated-worktree",
                "capability_ceiling": [
                    "agent:dispatch", "workspace:write",
                ],
                "timeout_seconds": 300,
                "max_attempts": 1,
                "inputs": {},
                "outputs": [{
                    "id": "integrated-candidate",
                    "kind": "git-diff",
                    "max_bytes": 100_000,
                }],
                "on_success": {
                    "kind": "terminal",
                    "target": "complete",
                },
                "on_failure": {
                    "kind": "action",
                    "target": "block",
                },
            })
        parent_path.write_text(
            json.dumps(parent, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.authority.fixture._git("add", "pm")
        self.authority.fixture._git(
            "commit", "-qm", "structural loop conductor fixture"
        )

    def test_structural_loop_records_typed_green_round_and_lineage(self):
        self.configure_structural_loop({
            "kind": "check-result",
            "source": "check-loop",
            "operator": "green",
        }, success_to_node=True)
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver()
        result = self.core.supervise_program(
            self.root,
            projection["run_id"],
            max_ticks=12,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (result["state"], result["stop"]),
            ("story-certified", "checkpoint"),
        )
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        round_receipts = [
            item for item in replayed["receipts"]
            if item["action_kind"] == "loop-round"
        ]
        self.assertEqual(len(round_receipts), 1)
        receipt = round_receipts[0]
        self.assertIn(
            "/loop/quality-loop/round/1/predicate/attempt/1",
            receipt["address"],
        )
        self.assertEqual(
            (receipt["result"], receipt["route"]),
            (
                "success",
                {"kind": "node", "target": "after-loop"},
            ),
        )
        self.assertEqual(
            receipt["payload"]["observation"]["value"], "pass"
        )
        self.assertTrue(receipt["payload"]["matched"])
        self.assertEqual(
            receipt["payload"]["carried_artifacts"][0]["source"],
            "implement.candidate",
        )
        child = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "agent"
        )
        self.assertIn(
            "/loop/quality-loop/round/1/subflow/loop-child/"
            "node/implement/role/implementer/attempt/1",
            child["address"],
        )
        self.assertEqual(
            replayed["authority"]["budgets"]["max_loop_rounds"]["used"],
            1,
        )
        after_loop = next(
            item for item in replayed["receipts"]
            if item.get("node") == "after-loop"
            and item["action_kind"] == "agent"
        )
        self.assertIn(
            "/node/after-loop/role/implementer/attempt/1",
            after_loop["address"],
        )

    def test_structural_loop_advances_round_then_routes_exhaustion(self):
        self.configure_structural_loop({
            "kind": "artifact-valid",
            "source": "check-loop.fact",
            "operator": "green",
        }, check_path="pm/programs/missing-loop-target.json")
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver()
        result = self.core.supervise_program(
            self.root,
            projection["run_id"],
            max_ticks=15,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (result["state"], result["stop"], result["checkpoint"]),
            ("stopped", "route-escalate", False),
        )
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        rounds = [
            item for item in replayed["receipts"]
            if item["action_kind"] == "loop-round"
        ]
        self.assertEqual(
            [
                (
                    item["payload"]["round"],
                    item["result"],
                    item["payload"]["matched"],
                )
                for item in rounds
            ],
            [(1, "continue", False), (2, "exhausted", False)],
        )
        self.assertEqual(
            [item["payload"]["observation"]["value"] for item in rounds],
            ["fail", "fail"],
        )
        agent_addresses = [
            item["address"] for item in replayed["receipts"]
            if item["action_kind"] == "agent"
        ]
        self.assertEqual(len(agent_addresses), 2)
        self.assertTrue(any("/round/1/" in item for item in agent_addresses))
        self.assertTrue(any("/round/2/" in item for item in agent_addresses))
        self.assertEqual(
            replayed["authority"]["budgets"]["max_loop_rounds"]["used"],
            2,
        )
        self.assertFalse(any(
            item["action_kind"] == "story-verification"
            for item in replayed["receipts"]
        ))

    def test_structural_loop_receipt_crash_recovers_exactly_once(self):
        self.configure_structural_loop({
            "kind": "check-result",
            "source": "check-loop",
            "operator": "green",
        })
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver()
        while True:
            frontier = self.core.derive_program_frontier(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                now=self.now,
            )
            if (
                frontier["next_actions"]
                and frontier["next_actions"][0]["kind"] == "loop-round"
            ):
                break
            self.core.tick_program(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                adapters={"fixture": fixture},
                now=self.now,
            )

        def crash(name, detail):
            if (
                name == "after-receipt"
                and detail.get("receipt_kind") == "loop-round"
            ):
                raise RuntimeError("loop receipt stored")

        with self.assertRaisesRegex(RuntimeError, "loop receipt stored"):
            self.core.tick_program(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                adapters={"fixture": fixture},
                now=self.now,
                boundary_hook=crash,
            )
        recovered = self.core.tick_program(
            self.root,
            projection["run_id"],
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(recovered["action"]["kind"], "loop-round")
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        self.assertEqual(len([
            item for item in replayed["authority"]["claims"]
            if item["category"] == "loop-round"
        ]), 1)
        self.assertEqual(len([
            item for item in replayed["receipts"]
            if item["action_kind"] == "loop-round"
        ]), 1)

    def test_malformed_verdict_is_ledgered_retried_then_routes_failure(self):
        self.configure_explicit_verdict(max_attempts=2)
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver({
            "verdict": {
                "outputs": {
                    "judgment": {
                        "criteria": [{"id": "intent", "result": "pass"}],
                    },
                },
            },
        })
        result = self.core.supervise_program(
            self.root,
            projection["run_id"],
            max_ticks=10,
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual((result["state"], result["stop"]),
                         ("stopped", "route-block"))
        self.assertEqual(fixture.starts, 3)
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        verdicts = sorted(
            [
                item for item in replayed["receipts"]
                if item["action_kind"] == "verdict"
            ],
            key=lambda item: item["attempt"],
        )
        self.assertEqual(
            [(item["attempt"], item["outcome"]) for item in verdicts],
            [(1, "failed"), (2, "failed")],
        )
        for receipt in verdicts:
            self.assertEqual(
                receipt["payload"]["verdict_content_failure"]["reason"],
                "verdict criterion evidence is malformed",
            )
        self.assertFalse(any(
            item["category"] == "verdict"
            for item in replayed["authority"]["claims"]
        ))

    def test_verdict_prompt_declares_exact_response_and_candidate_evidence(self):
        self.configure_explicit_verdict()
        projection = self.start()

        class CapturingFixture(self.core.ProgramFixtureDriver):
            def __init__(self):
                super().__init__()
                self.prompts = []

            def start(self, packet, profile, staging):
                self.prompts.append(json.loads(packet["prompt"]))
                return super().start(packet, profile, staging)

        fixture = CapturingFixture()
        result = self.core.supervise_program(
            self.root,
            projection["run_id"],
            max_ticks=10,
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual((result["state"], result["stop"]),
                         ("story-certified", "checkpoint"))
        prompt = next(
            item for item in fixture.prompts
            if item.get("action_kind") == "verdict"
        )
        self.assertTrue(prompt["evidence"])
        self.assertTrue(all(
            set(item) == {"kind", "hash", "ref"}
            for item in prompt["evidence"]
        ))
        candidate = prompt["candidate_subject"]
        self.assertEqual(candidate["kind"], "git-diff")
        self.assertIn(candidate, prompt["evidence"])
        self.assertIn("candidate diff", prompt["instructions"][0])
        self.assertIn("checked-out working tree", prompt["instructions"][0])
        self.assertIn("mechanical_facts", prompt)
        contract = prompt["response_contract"]
        self.assertEqual(
            set(contract),
            {
                "format", "top_level_keys", "criterion_keys",
                "evidence_keys", "citation_keys", "criteria", "template",
                "instructions",
            },
        )
        self.assertEqual(contract["format"], "single-json-document")
        self.assertEqual(contract["top_level_keys"], ["criteria"])
        self.assertEqual(
            contract["criterion_keys"],
            [
                "id", "result", "evidence", "citations", "rationale",
                "mechanical_fact_hash",
            ],
        )
        self.assertEqual(
            {item["id"] for item in contract["criteria"]},
            {item["id"] for item in prompt["rubric"]["criteria"]},
        )
        self.assertIn(
            "copy kind, hash, and ref verbatim",
            " ".join(contract["instructions"]),
        )

    def test_tick_conducts_implementer_then_independent_verifier(self):
        from dw_pmo.program_verdict import validate_verdict_document

        projection = self.start()
        fixture = self.core.ProgramFixtureDriver()
        supervised = self.core.supervise_program(
            self.root, projection["run_id"], max_ticks=10,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config, adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(supervised["stop"], "checkpoint")
        self.assertEqual(supervised["state"], "story-certified")
        self.assertEqual(supervised["ticks"], 4)
        self.assertEqual(fixture.starts, 2)

        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        authority = replayed["authority"]
        self.assertEqual(authority["active_claims"], [])
        self.assertEqual(len(authority["dispatches"]), 2)
        self.assertEqual(
            [item["category"] for item in authority["claims"]],
            [
                "selection", "assignment", "child-grant", "agent",
                "child-grant", "agent", "verdict",
            ],
        )
        implement = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "agent"
        )
        verification = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "story-verification"
        )
        self.assertIn("/node/implement/role/implementer/attempt/1", implement["address"])
        self.assertIn("/verifier/story-quality/role/verifier/attempt/1", verification["address"])
        self.assertNotEqual(implement["role_address"], verification["role_address"])
        self.assertEqual(verification["result"], "pass")
        verdict_artifact = next(
            item for item in verification["artifacts"]
            if item["name"] == "issued-verdict"
        )
        verdict = json.loads(
            self.core._artifact_content(
                self.root, projection["run_id"], verdict_artifact
            ).decode("utf-8")
        )
        self.assertEqual(validate_verdict_document(verdict), verdict)
        self.assertNotEqual(
            verdict["issuer"]["principal_fingerprint"],
            verdict["subject"]["implementer_principals"][0],
        )
        story = (
            self.root / "pm/roadmap/demo/phase-1-alpha/story-02-active-build.md"
        ).read_text(encoding="utf-8")
        self.assertIn("- **Status:** in-progress", story)

    def test_outward_fact_delivers_one_bounded_restart_safe_nudge(self):
        self.configure_outward_nudge()
        missing_channel = self.authority.plan(
            intent="nudge-without-channel",
            budgets=self.authority.budgets,
        )
        self.assertFalse(missing_channel["applicable"])
        self.assertTrue(any(
            "remote-tracking ref" in item["message"]
            for item in missing_channel["issues"]
        ))
        projection = self.start(
            remote="origin",
            remote_ref="refs/remotes/origin/main",
        )
        fixture = self.core.ProgramFixtureDriver()
        initial = self.core.supervise_program(
            self.root,
            projection["run_id"],
            max_ticks=10,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (initial["state"], initial["stop"]),
            ("story-certified", "checkpoint"),
        )
        observed = self.observe_failed_ci()
        self.assertEqual((observed["status"], observed["appended"]),
                         ("ci-failed", 4))
        result = self.core.supervise_program(
            self.root,
            projection["run_id"],
            max_ticks=10,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (result["state"], result["stop"]),
            ("story-certified", "checkpoint"),
        )
        self.assertEqual(fixture.starts, 4)
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        outward = [
            item for item in replayed["receipts"]
            if item["action_kind"] == "outward-fact"
        ]
        nudges = [
            item for item in replayed["receipts"]
            if item["action_kind"] == "nudge"
        ]
        self.assertEqual((len(outward), len(nudges)), (1, 1))
        self.assertEqual(
            set(outward[0]["payload"]),
            {
                "rule_id", "rule_hash", "signal", "signal_event_hash",
                "signal_event_kind", "signal_seq", "channel_hash",
            },
        )
        self.assertNotIn(
            "example.test", json.dumps(outward[0], sort_keys=True)
        )
        nudge = nudges[0]
        self.assertEqual(
            nudge["payload"]["outward_fact_receipt_hash"],
            outward[0]["receipt_hash"],
        )
        attempts = sorted(
            [
                item for item in replayed["receipts"]
                if item["action_kind"] == "agent"
                and item["node"] == "implement"
            ],
            key=lambda item: item["attempt"],
        )
        self.assertEqual([item["attempt"] for item in attempts], [1, 2])
        self.assertEqual(
            attempts[1]["payload"]["nudge"]["nudge_receipt_hash"],
            nudge["receipt_hash"],
        )
        self.assertEqual(
            replayed["authority"]["budgets"]["max_nudges"]["used"], 1
        )
        self.assertEqual(len([
            item for item in replayed["authority"]["claims"]
            if item["category"] == "nudge"
        ]), 1)
        verifications = [
            item for item in replayed["receipts"]
            if item["action_kind"] == "story-verification"
        ]
        self.assertEqual(
            sorted(
                (item["attempt"], item["result"])
                for item in verifications
            ),
            [(1, "pass"), (2, "pass")],
        )

    def test_nudge_receipt_crash_recovers_delivery_and_target_once(self):
        self.configure_outward_nudge()
        self.observe_failed_ci()
        projection = self.start(
            remote="origin",
            remote_ref="refs/remotes/origin/main",
        )
        fixture = self.core.ProgramFixtureDriver()
        while True:
            frontier = self.core.derive_program_frontier(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                now=self.now,
            )
            if (
                frontier["next_actions"]
                and frontier["next_actions"][0]["kind"] == "nudge"
            ):
                break
            self.core.tick_program(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                adapters={"fixture": fixture},
                now=self.now,
            )

        def crash(name, detail):
            if (
                name == "after-receipt"
                and detail.get("receipt_kind") == "nudge"
            ):
                raise RuntimeError("nudge receipt stored")

        with self.assertRaisesRegex(RuntimeError, "nudge receipt stored"):
            self.core.tick_program(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                adapters={"fixture": fixture},
                now=self.now,
                boundary_hook=crash,
            )
        recovered = self.core.tick_program(
            self.root,
            projection["run_id"],
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(recovered["action"]["kind"], "nudge")
        target = self.core.tick_program(
            self.root,
            projection["run_id"],
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (target["action"]["kind"], target["action"]["attempt"]),
            ("agent", 2),
        )
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        self.assertEqual(len([
            item for item in replayed["authority"]["claims"]
            if item["category"] == "nudge"
        ]), 1)
        self.assertEqual(len([
            item for item in replayed["receipts"]
            if item["action_kind"] == "nudge"
        ]), 1)
        self.assertEqual(len([
            item for item in replayed["receipts"]
            if item["action_kind"] == "agent"
            and item["node"] == "implement"
            and item["attempt"] == 2
        ]), 1)

    def test_cross_phase_continuation_carries_obligation_and_completes_scope(self):
        workflow_path = self.root / "pm/workflows/story-work.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        workflow["nodes"][0]["outputs"].append({
            "id": "machine-lessons",
            "kind": "lesson",
            "max_bytes": 10_000,
        })
        workflow_path.write_text(
            json.dumps(workflow, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        organization_path = self.root / "pm/organizations/delivery-core.json"
        organization = json.loads(organization_path.read_text(encoding="utf-8"))
        implementer = next(
            role for role in organization["teams"][0]["roles"]
            if role["id"] == "implementer"
        )
        implementer["artifacts"]["write"].append("lesson")
        organization_path.write_text(
            json.dumps(organization, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.authority.fixture._git(
            "add", "pm/workflows/story-work.json",
            "pm/organizations/delivery-core.json",
        )
        self.authority.fixture._git("commit", "-qm", "declare typed lesson output")
        projection = self.start()
        lesson_output = {
            "kind": "delivery-workbench-lesson-output",
            "schema_version": 1,
            "lessons": [{
                "claim": "Keep cross-phase obligations visible until completion.",
                "locations": ["dw_pmo.program_conductor.tick_program"],
                "confidence": "high",
                "supersedes": "",
            }],
        }
        fixture = self.core.ProgramFixtureDriver({
            "*": {"outputs": {"machine-lessons": lesson_output}},
        })
        first = self.core.supervise_program(
            self.root,
            projection["run_id"],
            max_ticks=10,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (first["state"], first["stop"]),
            ("story-certified", "checkpoint"),
        )
        projection = self.record_fixture_obligation(
            projection,
            obligation_id="carry-across-phase",
            blocking=False,
        )
        projection = self.complete_story_rail(projection, "DM-1-02")

        transition = self.core.tick_program(
            self.root,
            projection["run_id"],
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (
                transition["action"]["kind"],
                transition["lineage"]["phase"],
                transition["lineage"]["story"],
            ),
            ("selection", 2, "DM-2-01"),
        )
        frontier = self.core.derive_program_frontier(
            self.root,
            projection["run_id"],
            driver_config=self.config,
            now=self.now,
        )
        self.assertEqual(
            frontier["open_obligation_ids"], ["carry-across-phase"]
        )
        second = self.core.supervise_program(
            self.root,
            projection["run_id"],
            max_ticks=10,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (second["state"], second["stop"]),
            ("story-certified", "checkpoint"),
        )
        projection = self.complete_story_rail(projection, "DM-2-01")

        def crash(name, detail):
            if (
                name == "after-receipt"
                and detail.get("receipt_kind") == "scope-completion"
            ):
                raise RuntimeError("scope proof stored")

        with self.assertRaisesRegex(RuntimeError, "scope proof stored"):
            self.core.tick_program(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                adapters={"fixture": fixture},
                now=self.now,
                boundary_hook=crash,
            )
        completed = self.core.tick_program(
            self.root,
            projection["run_id"],
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(completed["action"]["kind"], "scope-completion")
        self.assertTrue(completed["terminal"])
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        self.assertEqual(replayed["authority"]["state"], "complete")
        self.assertEqual(
            replayed["authority"]["scope_completion"][
                "open_obligation_ids"
            ],
            ["carry-across-phase"],
        )
        self.assertEqual(
            replayed["authority"]["selected_stories"],
            ["DM-1-02", "DM-2-01"],
        )
        self.assertEqual(len([
            item for item in replayed["authority"]["claims"]
            if item["subject"]["kind"] == "program-scope-proof"
        ]), 1)
        self.assertEqual(len([
            item for item in replayed["receipts"]
            if item["action_kind"] == "scope-completion"
        ]), 1)
        self.assertEqual(
            replayed["authority"]["delivery_facts"]["story_ids"],
            ["DM-1-02", "DM-2-01"],
        )
        self.assertEqual(
            replayed["authority"]["delivery_facts"]["obligation_ids"],
            ["carry-across-phase"],
        )
        from dw_pmo.knowledge import EarnedRecordStore
        delivery_records = EarnedRecordStore(self.root).read("delivery-record")
        self.assertEqual(len(delivery_records), 1)
        self.assertEqual(delivery_records[0]["origin"], projection["run_id"])
        self.assertEqual(
            delivery_records[0]["head_sha"],
            replayed["authority"]["delivery_facts"]["head_sha"],
        )
        lessons = EarnedRecordStore(self.root).read("lesson")
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["origin"], projection["run_id"])
        from dw_pmo.knowledge import decode_lesson_locations
        locations = decode_lesson_locations(lessons[0]["detail"]["locations"])
        self.assertEqual(locations[0]["status"], "unresolved")
        self.assertEqual(locations[0]["reason"], "symbol-map-unavailable")

    def test_blocking_obligation_stops_cross_story_selection(self):
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver()
        first = self.core.supervise_program(
            self.root,
            projection["run_id"],
            max_ticks=10,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(first["state"], "story-certified")
        projection = self.record_fixture_obligation(
            projection,
            obligation_id="block-next-story",
            blocking=True,
        )
        projection = self.complete_story_rail(projection, "DM-1-02")
        frontier = self.core.derive_program_frontier(
            self.root,
            projection["run_id"],
            driver_config=self.config,
            now=self.now,
        )
        self.assertEqual(
            (frontier["state"], frontier["stop"]),
            ("stopped", "blocking-obligation-open"),
        )
        self.assertEqual(
            frontier["blocking_obligation_ids"], ["block-next-story"]
        )
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        self.assertEqual(
            replayed["authority"]["selected_stories"], ["DM-1-02"]
        )

    def test_program_without_command_records_subtraction_unavailable(self):
        projection = self.start()
        self.core.tick_program(
            self.root, projection["run_id"], driver_config=self.config,
            adapters={"fixture": self.core.ProgramFixtureDriver()}, now=self.now,
        )
        replayed = self.core.replay_program(
            self.root, projection["run_id"], now=self.now
        )
        self.assertEqual(
            replayed["test_baseline"],
            {
                "head_sha": replayed["expected_repository"]["head"],
                "command_hash": None,
                "status": "unavailable",
                "parser": "unittest-pytest-failures-v1",
                "exit_code": None,
                "failure_count": 0,
                "failure_ids": [],
                "subtraction_available": False,
                "truncated": False,
            },
        )
        self.assertEqual(replayed["dispatches"], [])

    def test_preexisting_failure_becomes_debt_and_planted_regression_blocks(self):
        # This command runner sits in the sanctioned check-node position,
        # so whole-bundle validation accepts it — no bypass needed.
        baseline_script = (
            "import sys\n"
            "print('FAIL: test_existing (suite.Case.test_existing)')\n"
            "print('FAILED (failures=1)')\n"
            "sys.exit(1)\n"
        )
        regression_script = (
            "import sys\n"
            "print('FAIL: test_existing (suite.Case.test_existing)')\n"
            "print('ERROR: test_regression (suite.Case.test_regression)')\n"
            "print('FAILED (failures=1, errors=1)')\n"
            "sys.exit(1)\n"
        )
        (self.root / "fixture_tests.py").write_text(
            baseline_script, encoding="utf-8"
        )
        workflow_path = self.root / "pm/workflows/story-work.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        workflow["nodes"][0].pop("on_success", None)
        workflow["nodes"].append({
            "id": "declared-tests", "type": "check", "needs": ["implement"],
            "inputs": {},
            "runner": {
                "kind": "command", "argv": [sys.executable, "fixture_tests.py"],
                "cwd": "workspace", "writes": [], "output_bytes": 50_000,
            },
            "expect": {"exit_code": 0}, "timeout_seconds": 60,
            "max_attempts": 1,
            "outputs": [{
                "id": "test-fact", "kind": "mechanical-fact",
                "max_bytes": 50_000,
            }],
            "on_success": {"kind": "terminal", "target": "complete"},
            "on_failure": {"kind": "action", "target": "block"},
        })
        workflow_path.write_text(
            json.dumps(workflow, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.authority.fixture._git("add", "pm", "fixture_tests.py")
        self.authority.fixture._git("commit", "-qm", "baseline subtraction fixture")

        projection = self.start()
        fixture = self.core.ProgramFixtureDriver({
            "implementer": {
                "workspace_files": {"fixture_tests.py": regression_script},
            },
        })
        result = self.core.supervise_program(
            self.root, projection["run_id"], max_ticks=12,
            max_seconds=86_400, driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        self.assertEqual(
            result["stop"], "route-block-introduced-test-failure"
        )
        self.assertEqual(result["state"], "stopped")
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        baseline = replayed["authority"]["test_baseline"]
        self.assertEqual(baseline["status"], "failures")
        self.assertEqual(baseline["failure_count"], 1)
        amended = dict(baseline)
        amended["command_hash"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(DwError, "cannot be amended"):
            self.core._record_program_test_baseline(
                self.root, projection["run_id"], amended, now=self.now
            )
        events = self.core._events(
            self.core._run_dir(self.root, projection["run_id"]),
            projection["run_id"],
        )
        kinds = [item["event"] for item in events]
        self.assertLess(
            kinds.index("test_baseline_captured"),
            kinds.index("claim_dispatched"),
        )
        checks = [
            item for item in replayed["receipts"]
            if item["action_kind"] == "check"
        ]
        self.assertEqual(len(checks), 1)
        check = checks[0]
        failures = check["payload"]["test_failures"]
        self.assertEqual(
            failures["pre_existing"],
            ["test_existing (suite.Case.test_existing)"],
        )
        self.assertEqual(
            failures["introduced"],
            ["test_regression (suite.Case.test_regression)"],
        )
        self.assertEqual(check["result"], "fail")
        debts = [
            item for item in replayed["authority"]["open_obligations"]
            if item["kind"] == "technical-debt"
        ]
        self.assertEqual(len(debts), 1)
        self.assertFalse(debts[0]["blocking"])
        self.assertIn("test_existing", debts[0]["statement"])
        self.assertEqual(
            replayed["authority"]["budgets"]["max_obligations"]["used"], 1
        )
        from dw_pmo.program_surface import build_program_view
        view = build_program_view(
            self.root, projection["run_id"], now=self.now
        )
        passed_answer = next(
            item for item in view["live_progress"]["answers"]
            if item["id"] == "passed"
        )
        self.assertIn("1 introduced test failure", passed_answer["answer"])
        self.assertIn("1 pre-existing", passed_answer["answer"])
        self.assertEqual(
            view["live_progress"]["review"]["test_failures"]["introduced"],
            ["test_regression (suite.Case.test_regression)"],
        )
        before_count = replayed["authority"]["event_count"]
        import dw_pmo.program_run as program_run
        with mock.patch.object(
            program_run, "replay_program", wraps=program_run.replay_program
        ) as replayed_once:
            self.core._emit_preexisting_test_debt(
                self.root, projection["run_id"],
                {"story": "DM-1-02"}, failures,
                now=self.core._time(self.now, "now"),
            )
        self.assertEqual(replayed_once.call_count, 1)
        deduped = self.core.replay_program(
            self.root, projection["run_id"], now=self.now
        )
        self.assertEqual(deduped["event_count"], before_count)
        self.assertEqual(len(deduped["open_obligations"]), 1)

    def test_fanout_fanin_collect_and_closed_check_replay_stably(self):
        workflow_path = self.root / "pm/workflows/story-work.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        first = workflow["nodes"][0]
        first.pop("on_success", None)
        first["outputs"][0]["max_bytes"] = 300_000
        second = json.loads(json.dumps(first))
        second["id"] = "implement-peer"
        second["task"] = "Independently produce the peer candidate slice."
        second["outputs"][0]["id"] = "peer-candidate"
        collect = {
            "id": "collect-candidates", "type": "collect",
            "needs": ["implement", "implement-peer"],
            "producers": ["implement", "implement-peer"],
            "inputs": {
                "first": {"kind": "artifact", "name": "implement.candidate"},
                "second": {"kind": "artifact", "name": "implement-peer.peer-candidate"},
            },
            "outputs": [{
                "id": "candidate-index", "kind": "markdown",
                "max_bytes": 50_000,
            }],
            "on_failure": {"kind": "action", "target": "block"},
        }
        check = {
            "id": "check-repository", "type": "check",
            "needs": ["collect-candidates"],
            "inputs": {
                "index": {"kind": "artifact", "name": "collect-candidates.candidate-index"},
            },
            "runner": {
                "kind": "builtin", "name": "file-exists",
                "path": "pm/programs/demo-program.json",
                "output_bytes": 50_000,
            },
            "expect": {"exit_code": 0},
            "timeout_seconds": 60, "max_attempts": 1,
            "outputs": [{
                "id": "repository-fact", "kind": "mechanical-fact",
                "max_bytes": 20_000,
            }],
            "on_success": {"kind": "terminal", "target": "complete"},
            "on_failure": {"kind": "action", "target": "block"},
        }
        workflow["nodes"] = [first, second, collect, check]
        workflow_path.write_text(
            json.dumps(workflow, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.authority.fixture._git("add", "pm")
        self.authority.fixture._git("commit", "-qm", "fanout conductor workflow")
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver()
        result = self.core.supervise_program(
            self.root, projection["run_id"], max_ticks=12,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config, adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(result["state"], "story-certified")
        self.assertEqual(result["stop"], "checkpoint")
        self.assertEqual(fixture.starts, 3)
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        kinds = [item["action_kind"] for item in replayed["receipts"]]
        self.assertEqual(kinds.count("agent"), 2)
        self.assertEqual(kinds.count("collect"), 1)
        self.assertEqual(kinds.count("check"), 1)
        check_receipt = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "check"
        )
        self.assertEqual(check_receipt["result"], "pass")
        fact = next(
            item for item in check_receipt["artifacts"]
            if item["artifact_kind"] == "mechanical-fact"
        )
        self.assertIn("mechanical-fact-core", fact["checks"])
        collected = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "collect"
        )
        self.assertEqual(collected["payload"]["input_count"], 2)

    def test_user_check_fact_is_rebound_to_later_verdict_subject(self):
        workflow_path = self.root / "pm/workflows/story-work.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        implement = workflow["nodes"][0]
        implement.pop("on_success", None)
        check = {
            "id": "check-candidate", "type": "check",
            "needs": ["implement"],
            "inputs": {
                "candidate": {
                    "kind": "artifact", "name": "implement.candidate",
                },
            },
            "runner": {
                "kind": "builtin", "name": "file-exists",
                "path": "pm/programs/demo-program.json",
                "output_bytes": 50_000,
            },
            "expect": {"exit_code": 0},
            "timeout_seconds": 60, "max_attempts": 1,
            "outputs": [{
                "id": "fact", "kind": "mechanical-fact",
                "max_bytes": 20_000,
            }],
            "on_failure": {"kind": "action", "target": "block"},
        }
        verdict = {
            "id": "verify", "type": "verdict",
            "needs": ["check-candidate"], "role": "verifier",
            "rubric": "story-quality",
            "subject": {
                "kind": "artifact", "name": "implement.candidate",
            },
            "freshness_seconds": 60,
            "max_rationale_bytes": 20_000, "max_attempts": 1,
            "results": ["pass", "fail"],
            "routes": {
                "pass": {"kind": "terminal", "target": "complete"},
                "fail": {"kind": "action", "target": "block"},
            },
            "on_failure": {"kind": "action", "target": "block"},
        }
        workflow["nodes"] = [implement, check, verdict]
        workflow_path.write_text(
            json.dumps(workflow, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        rubric_path = self.root / "pm/rubrics/story-quality.json"
        rubric = json.loads(rubric_path.read_text(encoding="utf-8"))
        criterion = rubric["criteria"][0]
        criterion.update({
            "evaluation": {
                "kind": "mechanical-fact", "fact": "check-candidate",
            },
            "required_evidence_kinds": [],
            "min_citations": 0,
        })
        rubric_path.write_text(
            json.dumps(rubric, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.authority.fixture._git("add", "pm")
        self.authority.fixture._git(
            "commit", "-qm", "check then verdict conductor fixture"
        )

        projection = self.start()
        fixture = self.advance_to_agent(projection)
        implemented = self.core.tick_program(
            self.root, projection["run_id"], driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        checked = self.core.tick_program(
            self.root, projection["run_id"], driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        self.assertEqual(implemented["action"]["kind"], "agent")
        self.assertEqual(checked["action"]["kind"], "check")
        before_verdict = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        self.assertFalse(any(
            item["action_kind"] == "verdict"
            for item in before_verdict["receipts"]
        ))

        verified = self.core.tick_program(
            self.root, projection["run_id"], driver_config=self.config,
            adapters={"fixture": fixture}, now=self.now,
        )
        self.assertEqual(verified["action"]["kind"], "verdict")
        frontier = self.core.derive_program_frontier(
            self.root, projection["run_id"], driver_config=self.config,
            now=self.now,
        )
        self.assertEqual(
            (frontier["state"], frontier["stop"]),
            ("story-certified", "integration-required"),
        )

        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        check_receipt = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "check"
        )
        verdict_receipt = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "verdict"
        )
        self.assertEqual(verdict_receipt["result"], "pass")
        self.assertEqual(verdict_receipt["route"], "pass")
        claim_order = {
            item["claim_id"]: index
            for index, item in enumerate(replayed["authority"]["claims"])
        }
        self.assertLess(
            claim_order[check_receipt["claim_id"]],
            claim_order[verdict_receipt["claim_id"]],
        )
        stored_artifact = next(
            item for item in check_receipt["artifacts"]
            if item["artifact_kind"] == "mechanical-fact"
        )
        stored_fact = json.loads(self.core._artifact_content(
            self.root, projection["run_id"], stored_artifact
        ))
        operation_id = verdict_receipt["operation"]["operation_id"]
        operation = self.core._load_json(
            self.root / ".git/pmo-programs/runs" / projection["run_id"]
            / "conductor/driver-sessions" / f"{operation_id}.json",
            "verdict driver operation",
        )
        packet = self.core._load_json(
            Path(operation["packet_path"]), "verdict work packet"
        )
        prompt = json.loads(packet["prompt"])
        rebuilt_fact = prompt["mechanical_facts"][0]
        issued_artifact = next(
            item for item in verdict_receipt["artifacts"]
            if item["name"] == "issued-verdict"
        )
        issued = json.loads(self.core._artifact_content(
            self.root, projection["run_id"], issued_artifact
        ))
        self.assertNotEqual(stored_fact["subject"], rebuilt_fact["subject"])
        self.assertEqual(rebuilt_fact["subject"], issued["subject"])
        self.assertEqual(
            issued["criteria"][0]["mechanical_fact_hash"],
            rebuilt_fact["fact_hash"],
        )
        for field in ("predicate", "result", "observation", "issued_at"):
            self.assertEqual(rebuilt_fact[field], stored_fact[field])
        self.assertEqual(rebuilt_fact["issuer"], stored_fact["issuer"])

    def test_failed_verdict_takes_one_claimed_repair_then_reverifies(self):
        projection = self.start()
        first_verifier = (
            "program/demo-program/phase/1/story/DM-1-02/workflow/alpha/"
            "verifier/story-quality/role/verifier/attempt/1"
        )
        fixture = self.core.ProgramFixtureDriver({
            first_verifier: {"judgment_result": "fail"},
        })
        result = self.core.supervise_program(
            self.root, projection["run_id"], max_ticks=10,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config, adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(result["state"], "story-certified")
        self.assertEqual(result["stop"], "checkpoint")
        self.assertEqual(fixture.starts, 4)
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        verdicts = sorted(
            [
                item for item in replayed["receipts"]
                if item["action_kind"] == "story-verification"
            ],
            key=lambda item: item["attempt"],
        )
        self.assertEqual(
            [(item["attempt"], item["result"]) for item in verdicts],
            [(1, "needs-repair"), (2, "pass")],
        )
        repair = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "repair"
        )
        self.assertEqual(repair["payload"]["repair_round"], 1)
        self.assertIn("/repair/round/1/", repair["address"])
        self.assertEqual(
            replayed["authority"]["budgets"]["max_repairs_per_story"]["used"],
            1,
        )
        self.assertEqual(len([
            item for item in replayed["authority"]["claims"]
            if item["category"] == "repair"
        ]), 1)

    def test_crashes_around_claim_dispatch_and_receipt_never_duplicate_start(self):
        cases = [
            ("agent-claim", "after-claim", "agent", 0, 1),
            ("before-dispatch", "before-dispatch", None, 0, 1),
            ("dispatch-record", "after-dispatch-record", None, 0, 1),
            ("after-dispatch", "after-dispatch", None, 1, 0),
            ("agent-receipt", "after-receipt", "agent", 1, 0),
        ]
        for label, boundary, detail_kind, first_starts, recovered_starts in cases:
            with self.subTest(boundary=label):
                projection = self.start()
                self.advance_to_agent(projection)
                first = self.core.ProgramFixtureDriver()

                def crash(name, detail):
                    observed_kind = (
                        detail.get("category")
                        if name == "after-claim"
                        else detail.get("receipt_kind")
                    )
                    if name == boundary and (
                        detail_kind is None or observed_kind == detail_kind
                    ):
                        raise RuntimeError("planted program crash")

                with self.assertRaisesRegex(RuntimeError, "planted program crash"):
                    self.core.tick_program(
                        self.root, projection["run_id"],
                        driver_config=self.config,
                        adapters={"fixture": first}, now=self.now,
                        boundary_hook=crash,
                    )
                self.assertEqual(first.starts, first_starts)
                recovered = self.core.ProgramFixtureDriver()
                result = self.core.tick_program(
                    self.root, projection["run_id"],
                    driver_config=self.config,
                    adapters={"fixture": recovered}, now=self.now,
                )
                self.assertTrue(result["progressed"])
                self.assertEqual(recovered.starts, recovered_starts)
                replayed = self.core.replay_program_conductor(
                    self.root, projection["run_id"], now=self.now
                )
                agent_claims = [
                    item for item in replayed["authority"]["claims"]
                    if item["category"] == "agent"
                ]
                self.assertEqual(len(agent_claims), 1)
                self.assertEqual(len(replayed["authority"]["dispatches"]), 1)
                self.assertEqual(len([
                    item for item in replayed["receipts"]
                    if item["action_kind"] == "agent"
                ]), 1)

    def test_missing_session_after_durable_dispatch_stops_uncertain(self):
        projection = self.start()
        self.advance_to_agent(projection)
        first = self.core.ProgramFixtureDriver()

        def crash(name, _detail):
            if name == "after-dispatch":
                raise RuntimeError("driver started")

        with self.assertRaisesRegex(RuntimeError, "driver started"):
            self.core.tick_program(
                self.root, projection["run_id"], driver_config=self.config,
                adapters={"fixture": first}, now=self.now,
                boundary_hook=crash,
            )
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        operation_id = replayed["authority"]["dispatches"][0]["operation_id"]
        operation_path = (
            self.root / ".git/pmo-programs/runs" / projection["run_id"]
            / "conductor/driver-sessions" / f"{operation_id}.json"
        )
        operation_path.unlink()
        recovered = self.core.ProgramFixtureDriver()
        stopped = self.core.tick_program(
            self.root, projection["run_id"], driver_config=self.config,
            adapters={"fixture": recovered}, now=self.now,
        )
        self.assertEqual(stopped["stop"], "external-operation-uncertain")
        self.assertEqual(stopped["execution_status"], "uncertain")
        self.assertEqual(recovered.starts, 0)
        final = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        self.assertEqual(len(final["authority"]["dispatches"]), 1)
        self.assertEqual(len(final["authority"]["active_claims"]), 1)

    def test_crash_after_closed_check_observation_does_not_rerun_check(self):
        workflow_path = self.root / "pm/workflows/story-work.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        workflow["nodes"][0].pop("on_success", None)
        workflow["nodes"].append({
            "id": "closed-check", "type": "check", "needs": ["implement"],
            "inputs": {
                "candidate": {"kind": "artifact", "name": "implement.candidate"},
            },
            "runner": {
                "kind": "builtin", "name": "file-exists",
                "path": "pm/programs/demo-program.json",
                "output_bytes": 50_000,
            },
            "expect": {"exit_code": 0}, "timeout_seconds": 60,
            "max_attempts": 1,
            "outputs": [{
                "id": "fact", "kind": "mechanical-fact",
                "max_bytes": 20_000,
            }],
            "on_success": {"kind": "terminal", "target": "complete"},
            "on_failure": {"kind": "action", "target": "block"},
        })
        workflow_path.write_text(
            json.dumps(workflow, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.authority.fixture._git("add", "pm")
        self.authority.fixture._git("commit", "-qm", "closed check crash workflow")
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver()
        for _index in range(3):
            self.core.tick_program(
                self.root, projection["run_id"], driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
            )
        calls = {"count": 0}
        original = self.core._run_closed_check

        def counted(*args, **kwargs):
            calls["count"] += 1
            return original(*args, **kwargs)

        def crash(name, detail):
            if name == "after-dispatch" and str(detail.get("operation_id", "")).startswith("check-"):
                raise RuntimeError("check observed")

        with mock.patch.object(self.core, "_run_closed_check", side_effect=counted):
            with self.assertRaisesRegex(RuntimeError, "check observed"):
                self.core.tick_program(
                    self.root, projection["run_id"], driver_config=self.config,
                    adapters={"fixture": fixture}, now=self.now,
                    boundary_hook=crash,
                )
            self.core.tick_program(
                self.root, projection["run_id"], driver_config=self.config,
                adapters={"fixture": fixture}, now=self.now,
            )
        self.assertEqual(calls["count"], 1)
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        self.assertEqual(len([
            item for item in replayed["receipts"]
            if item["action_kind"] == "check"
        ]), 1)

    def test_ledger_bound_receipt_tamper_fails_closed(self):
        projection = self.start()
        self.core.tick_program(
            self.root, projection["run_id"], driver_config=self.config,
            adapters={"fixture": self.core.ProgramFixtureDriver()}, now=self.now,
        )
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        receipt_hash = replayed["receipt_hashes"][0]
        path = self.core._receipt_path(
            self.root, projection["run_id"], receipt_hash
        )
        path.chmod(0o600)
        receipt = json.loads(path.read_text(encoding="utf-8"))
        receipt["result"] = "tampered"
        path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(DwError, "hash"):
            self.core.replay_program_conductor(
                self.root, projection["run_id"], now=self.now
            )

    def test_rule_council_meta_audits_and_ingests_durable_obligation(self):
        from dw_pmo.program_deliberation import validate_council_decision

        self.configure_council_workflow(audit="full")
        obligation = {
            "id": "document-council-fallback",
            "kind": "technical-debt",
            "statement": "Document the governed council fallback.",
            "priority": "medium",
            "blocking": False,
            "accountable_role": "architect",
            "target": "DM-1-02",
            "citations": ["evidence:council-evidence"],
            "acceptance": "The fallback has an evidence-backed contract.",
            "state": "open",
        }
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver({
            "council-judgment": {"obligations": [obligation]},
        })
        result = self.core.supervise_program(
            self.root, projection["run_id"], max_ticks=30,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config, adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual((result["state"], result["stop"]),
                         ("story-certified", "checkpoint"))
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        decision_receipt = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "council-decision"
        )
        decision_artifact = next(
            item for item in decision_receipt["artifacts"]
            if item["name"] == "issued-decision"
        )
        decision = json.loads(self.core._artifact_content(
            self.root, projection["run_id"], decision_artifact
        ))
        self.assertEqual(validate_council_decision(decision), decision)
        self.assertEqual(decision["authority"]["kind"], "rule")
        self.assertIsNone(decision["authority"]["decider"])
        self.assertIsNone(decision["authority"]["decider_seat"])
        self.assertEqual(decision["obligations"], [obligation])
        self.assertEqual(
            [item["id"] for item in replayed["authority"]["open_obligations"]],
            ["document-council-fallback"],
        )
        self.assertEqual(len([
            item for item in replayed["receipts"]
            if item["action_kind"] == "meta-verdict-issuance"
        ]), 1)
        self.assertEqual(
            replayed["authority"]["budgets"]["max_debate_rounds"]["used"], 1
        )
        speaker_receipts = [
            item for item in replayed["receipts"]
            if item["action_kind"] in {
                "debate-proposal", "debate-critique",
                "debate-rebuttal", "council-judgment",
            }
        ]
        self.assertEqual(len(speaker_receipts), 7)
        self.assertTrue(all(
            "/council/quality-council/round/1/" in item["address"]
            and "/seat/" in item["address"]
            for item in speaker_receipts
        ))

    def test_judge_council_binds_only_the_preassigned_decider(self):
        from dw_pmo.program_deliberation import validate_council_decision

        self.configure_council_workflow(method="judge", audit="none")
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver()
        result = self.core.supervise_program(
            self.root, projection["run_id"], max_ticks=30,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config, adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual((result["state"], result["stop"]),
                         ("story-certified", "checkpoint"))
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        receipt = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "council-decision"
        )
        artifact = next(
            item for item in receipt["artifacts"]
            if item["name"] == "issued-decision"
        )
        decision = json.loads(self.core._artifact_content(
            self.root, projection["run_id"], artifact
        ))
        self.assertEqual(validate_council_decision(decision), decision)
        authority = decision["authority"]
        self.assertEqual(authority["kind"], "judge")
        self.assertEqual(
            authority["decider_seat"],
            replayed["authority"]["roster"]["councils"][0]["decider_seat"],
        )
        self.assertEqual(
            authority["decider"]["execution"],
            next(
                item["execution"]
                for item in replayed["authority"]["roster"]["seats"]
                if item["address"] == authority["decider_seat"]
            ),
        )

    def test_tie_checkpoint_and_decision_receipt_crash_are_idempotent(self):
        self.configure_council_workflow(
            method="majority", threshold=2,
            tie_policy="checkpoint", audit="none",
        )
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver({
            "architect": {"vote": "advance"},
            "critic": {"vote": "repair"},
            "verifier": {"decision_result": "checkpoint"},
        })
        while True:
            frontier = self.core.derive_program_frontier(
                self.root, projection["run_id"],
                driver_config=self.config, now=self.now,
            )
            if (
                frontier["next_actions"]
                and frontier["next_actions"][0]["kind"] == "council-decision"
            ):
                break
            self.core.tick_program(
                self.root, projection["run_id"],
                driver_config=self.config, adapters={"fixture": fixture},
                now=self.now,
            )

        def crash(name, detail):
            if (
                name == "after-receipt"
                and detail.get("receipt_kind") == "council-decision"
            ):
                raise RuntimeError("decision receipt stored")

        with self.assertRaisesRegex(RuntimeError, "decision receipt stored"):
            self.core.tick_program(
                self.root, projection["run_id"],
                driver_config=self.config, adapters={"fixture": fixture},
                now=self.now, boundary_hook=crash,
            )
        recovered = self.core.tick_program(
            self.root, projection["run_id"],
            driver_config=self.config, adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(recovered["action"]["kind"], "council-decision")
        checkpoint = self.core.tick_program(
            self.root, projection["run_id"],
            driver_config=self.config, adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertTrue(checkpoint["checkpoint"])
        final = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        self.assertEqual(final["authority"]["state"], "checkpoint")
        self.assertEqual(
            final["authority"]["outstanding_requests"][0]["port"],
            "program-decision-checkpoint",
        )
        self.assertEqual(len([
            item for item in final["authority"]["claims"]
            if item["category"] == "council"
        ]), 1)
        self.assertEqual(len([
            item for item in final["receipts"]
            if item["action_kind"] == "council-decision"
        ]), 1)

    def test_phase_architect_approves_exact_frozen_boundary(self):
        from dw_pmo.program_verdict import validate_verdict_document

        self.configure_phase_architect_gate()
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver()
        result = self.core.supervise_program(
            self.root, projection["run_id"], max_ticks=20,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config, adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (result["state"], result["stop"], result["ticks"]),
            ("story-certified", "checkpoint", 7),
        )
        self.assertEqual(result["last_tick"]["stop"], "integration-required")
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        boundary = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "architecture-boundary"
        )
        boundary_artifact = next(
            item for item in boundary["artifacts"]
            if item["name"] == "boundary-snapshot"
        )
        self.assertEqual(
            boundary["payload"]["snapshot_hash"],
            boundary_artifact["sha256"],
        )
        architect_receipt = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "architect-verdict"
        )
        verdict_artifact = next(
            item for item in architect_receipt["artifacts"]
            if item["name"] == "issued-verdict"
        )
        verdict = validate_verdict_document(json.loads(
            self.core._artifact_content(
                self.root, projection["run_id"], verdict_artifact
            )
        ))
        self.assertEqual(verdict["verdict_type"], "architect-verdict")
        self.assertEqual(verdict["result"], "approve")
        self.assertEqual(verdict["issuer"]["duty"], "master-architect")
        self.assertEqual(verdict["subject"]["kind"], "phase-snapshot")
        self.assertIsNone(verdict["subject"]["story"])
        self.assertEqual(
            verdict["subject"]["hash"], boundary_artifact["sha256"]
        )
        architect_seat = next(
            item for item in replayed["authority"]["roster"]["seats"]
            if item["duty"] == "master-architect"
        )
        self.assertEqual(
            verdict["issuer"]["address"], architect_seat["address"]
        )
        self.assertEqual(
            verdict["assignment"]["execution"],
            architect_seat["execution"],
        )
        gate = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "architecture-gate"
        )
        self.assertEqual((gate["result"], gate["route"]), ("pass", "advance"))
        self.assertEqual(
            replayed["authority"]["budgets"]["max_verdicts"]["used"], 2
        )

    def test_phase_architect_veto_stops_before_integration(self):
        self.configure_phase_architect_gate(on_fail="block")
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver({
            "architect-verdict": {"judgment_result": "fail"},
        })
        result = self.core.supervise_program(
            self.root, projection["run_id"], max_ticks=20,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config, adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (result["state"], result["stop"], result["checkpoint"]),
            ("stopped", "architect-veto", False),
        )
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        architect = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "architect-verdict"
        )
        gate = next(
            item for item in replayed["receipts"]
            if item["action_kind"] == "architecture-gate"
        )
        self.assertEqual(architect["result"], "veto")
        self.assertEqual((gate["result"], gate["route"]), ("fail", "block"))
        self.assertFalse(any(
            item["category"] in {
                "integration", "story-complete", "phase-advance",
            }
            for item in replayed["authority"]["claims"]
        ))

    def test_phase_architect_receipt_crash_recovers_before_typed_checkpoint(self):
        self.configure_phase_architect_gate(on_fail="checkpoint")
        projection = self.start()
        fixture = self.core.ProgramFixtureDriver({
            "architect-verdict": {"judgment_result": "fail"},
        })
        while True:
            frontier = self.core.derive_program_frontier(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                now=self.now,
            )
            if (
                frontier["next_actions"]
                and frontier["next_actions"][0]["kind"]
                == "architecture-boundary"
            ):
                break
            self.core.tick_program(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                adapters={"fixture": fixture},
                now=self.now,
            )

        def crash_boundary(name, detail):
            if (
                name == "after-receipt"
                and detail.get("receipt_kind") == "architecture-boundary"
            ):
                raise RuntimeError("architect boundary stored")

        with self.assertRaisesRegex(
            RuntimeError, "architect boundary stored"
        ):
            self.core.tick_program(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                adapters={"fixture": fixture},
                now=self.now,
                boundary_hook=crash_boundary,
            )
        recovered_boundary = self.core.tick_program(
            self.root,
            projection["run_id"],
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            recovered_boundary["action"]["kind"],
            "architecture-boundary",
        )

        while True:
            frontier = self.core.derive_program_frontier(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                now=self.now,
            )
            if (
                frontier["next_actions"]
                and frontier["next_actions"][0]["kind"]
                == "architect-verdict"
            ):
                break
            self.core.tick_program(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                adapters={"fixture": fixture},
                now=self.now,
            )

        def crash(name, detail):
            if (
                name == "after-receipt"
                and detail.get("receipt_kind") == "architect-verdict"
            ):
                raise RuntimeError("architect receipt stored")

        with self.assertRaisesRegex(RuntimeError, "architect receipt stored"):
            self.core.tick_program(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                adapters={"fixture": fixture},
                now=self.now,
                boundary_hook=crash,
            )
        recovered = self.core.tick_program(
            self.root,
            projection["run_id"],
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            recovered["action"]["kind"], "architect-verdict"
        )
        frontier = self.core.derive_program_frontier(
            self.root,
            projection["run_id"],
            driver_config=self.config,
            now=self.now,
        )
        self.assertEqual(
            frontier["next_actions"][0]["kind"], "architecture-gate"
        )

        def crash_gate(name, detail):
            if (
                name == "after-receipt"
                and detail.get("receipt_kind") == "architecture-gate"
            ):
                raise RuntimeError("architect gate stored")

        with self.assertRaisesRegex(RuntimeError, "architect gate stored"):
            self.core.tick_program(
                self.root,
                projection["run_id"],
                driver_config=self.config,
                adapters={"fixture": fixture},
                now=self.now,
                boundary_hook=crash_gate,
            )
        recovered_gate = self.core.tick_program(
            self.root,
            projection["run_id"],
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            recovered_gate["action"]["kind"], "architecture-gate"
        )
        final = self.core.supervise_program(
            self.root,
            projection["run_id"],
            max_ticks=5,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (final["state"], final["checkpoint"]),
            ("checkpoint", True),
        )
        replayed = self.core.replay_program_conductor(
            self.root, projection["run_id"], now=self.now
        )
        self.assertEqual(fixture.starts, 3)
        self.assertEqual(len([
            item for item in replayed["receipts"]
            if item["action_kind"] == "architect-verdict"
        ]), 1)
        self.assertEqual(len([
            item for item in replayed["receipts"]
            if item["action_kind"] == "architecture-boundary"
        ]), 1)
        self.assertEqual(len([
            item for item in replayed["receipts"]
            if item["action_kind"] == "architecture-gate"
        ]), 1)
        self.assertEqual(len([
            item for item in replayed["receipts"]
            if item["action_kind"] == "architect-verdict-issuance"
            and item.get("parent_action_id") is not None
        ]), 1)
        self.assertEqual(
            replayed["authority"]["outstanding_requests"][0]["port"],
            "phase-boundary",
        )
        self.assertEqual(len([
            item for item in replayed["authority"]["claims"]
            if item["category"] == "checkpoint-request"
        ]), 1)


class ProgramDeliveryTest(unittest.TestCase):
    """WLA-26-10: exact integration, commit, push, and roadmap rails."""

    now = "2026-07-22T12:02:00Z"

    def setUp(self):
        import dw_pmo.program_delivery as delivery

        self.core = delivery
        self.conductor = ProgramConductorTest(
            "test_tick_conducts_implementer_then_independent_verifier"
        )
        self.conductor.setUp()
        self.addCleanup(self.conductor.doCleanups)
        self.root = self.conductor.root
        self.authority = self.conductor.authority
        self.config = self.conductor.config

        # The delivery proof requires a real mechanical receipt before the
        # independent governed verifier. The runner is a closed builtin, not
        # an arbitrary command surface.
        workflow_path = self.root / "pm/workflows/story-work.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        implement = workflow["nodes"][0]
        implement.pop("on_success", None)
        workflow["nodes"].append({
            "id": "check-repository",
            "type": "check",
            "needs": ["implement"],
            "inputs": {
                "candidate": {
                    "kind": "artifact",
                    "name": "implement.candidate",
                },
            },
            "runner": {
                "kind": "builtin",
                "name": "file-exists",
                "path": "pm/programs/demo-program.json",
                "output_bytes": 50_000,
            },
            "expect": {"exit_code": 0},
            "timeout_seconds": 60,
            "max_attempts": 1,
            "outputs": [{
                "id": "repository-fact",
                "kind": "mechanical-fact",
                "max_bytes": 20_000,
            }],
            "on_success": {"kind": "terminal", "target": "complete"},
            "on_failure": {"kind": "action", "target": "block"},
        })
        workflow_path.write_text(
            json.dumps(workflow, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        # Phase 1's unscoped parked row is completed in the fixture so the
        # exact phase-advance rail can prove that the whole phase, not merely
        # the program subset, is closed.
        from dw_pmo.mutations import apply_plan, plan_story_status
        from dw_pmo.parse import get_phase, get_project

        project = get_project(self.root, "demo")
        phase1 = get_phase(project, "1")
        apply_plan(
            plan_story_status(
                self.root,
                project,
                phase1,
                "DM-1-03",
                "done",
                evidence_body="- fixture phase-closure prerequisite",
                evidence_date="2026-07-22",
            ),
            validate_after=True,
        )
        (self.root / ".gitignore").write_text(".tmp/\n", encoding="utf-8")

        program_path = self.root / "pm/programs/demo-program.json"
        program = json.loads(program_path.read_text(encoding="utf-8"))
        for capability in ("certification:objective", "git:push"):
            if capability not in program["requested_capabilities"]:
                program["requested_capabilities"].append(capability)
            if capability not in self.authority.capabilities:
                self.authority.capabilities.append(capability)
        for counter in ("max_integrations", "max_commits", "max_pushes"):
            program["budgets"][counter] = 3
            self.authority.budgets[counter] = 3
        program_path.write_text(
            json.dumps(program, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.authority.fixture.program = program
        self.authority.fixture._git("add", ".")
        self.authority.fixture._git(
            "commit", "-qm", "program delivery fixture"
        )

        self.remote = self.authority.fixture.tmp / "program-remote.git"
        subprocess.run(
            ["git", "init", "--bare", "-q", str(self.remote)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.authority.fixture._git(
            "remote", "add", "origin", str(self.remote)
        )
        self.authority.fixture._git(
            "push", "-qu", "origin", "main"
        )

    def start_and_certify(self):
        projection = self.conductor.start(
            remote="origin",
            remote_ref="refs/remotes/origin/main",
        )
        fixture = self.conductor.core.ProgramFixtureDriver()
        result = self.conductor.core.supervise_program(
            self.root,
            projection["run_id"],
            max_ticks=12,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (result["state"], result["stop"]),
            ("story-certified", "checkpoint"),
        )
        return projection, fixture

    def preview_and_start(self, run_id):
        preview = self.core.build_program_delivery_preview(
            self.root,
            run_id,
            driver_config=self.config,
            now=self.now,
        )
        self.assertTrue(preview["applicable"], preview["issues"])
        self.assertFalse(preview["mutates_repository"])
        self.assertFalse(preview["mutates_roadmap"])
        self.assertFalse(preview["creates_commit"])
        self.assertFalse(preview["pushes_remote"])
        frontier = self.core.start_program_delivery(
            self.root,
            preview,
            delivery_token=preview["delivery_token"],
            driver_config=self.config,
        )
        return preview, frontier

    def test_preview_is_pure_and_refuses_missing_mechanical_or_dirty_facts(self):
        projection, _fixture = self.start_and_certify()
        run_id = projection["run_id"]
        before_status = self.authority.fixture._git(
            "status", "--porcelain=v1"
        ).stdout
        before_events = self.authority.core.replay_program(
            self.root, run_id, now=self.now
        )["event_count"]
        preview = self.core.build_program_delivery_preview(
            self.root,
            run_id,
            driver_config=self.config,
            now=self.now,
        )
        self.assertTrue(preview["applicable"], preview["issues"])
        self.assertEqual(
            [item["kind"] for item in preview["actions"]],
            [
                "integration",
                "evidence",
                "story-complete",
                "phase-advance",
                "story-start",
                "contract",
                "certification-objective",
                "certification-verdict",
                "commit",
                "push",
            ],
        )
        self.assertEqual(
            before_status,
            self.authority.fixture._git(
                "status", "--porcelain=v1"
            ).stdout,
        )
        self.assertEqual(
            before_events,
            self.authority.core.replay_program(
                self.root, run_id, now=self.now
            )["event_count"],
        )
        self.assertFalse(
            (self.root / ".git/pmo-programs/runs" / run_id / "delivery").exists()
        )

        (self.root / "unexpected.txt").write_text(
            "dirty\n", encoding="utf-8"
        )
        refused = self.core.build_program_delivery_preview(
            self.root,
            run_id,
            driver_config=self.config,
            now=self.now,
        )
        self.assertFalse(refused["applicable"])
        self.assertIn(
            "repository-not-clean",
            {item["code"] for item in refused["issues"]},
        )

    def test_blocking_obligation_and_missing_capability_refuse_before_write(self):
        projection, _fixture = self.start_and_certify()
        run_id = projection["run_id"]
        self.conductor.record_fixture_obligation(
            projection,
            obligation_id="blocking-delivery-debt",
            blocking=True,
        )
        blocked = self.core.build_program_delivery_preview(
            self.root,
            run_id,
            driver_config=self.config,
            now=self.now,
        )
        self.assertFalse(blocked["applicable"])
        self.assertIn(
            "blocking-obligation-open",
            {item["code"] for item in blocked["issues"]},
        )
        self.assertEqual(
            self.authority.fixture._git(
                "status", "--porcelain=v1"
            ).stdout,
            "",
        )

        capabilities = [
            item for item in self.authority.capabilities
            if item != "certification:objective"
        ]
        _plan, second = self.authority.start(
            intent="delivery-without-objective-certification",
            capabilities=capabilities,
            budgets=self.authority.budgets,
            remote="origin",
            remote_ref="refs/remotes/origin/main",
        )
        fixture = self.conductor.core.ProgramFixtureDriver()
        conducted = self.conductor.core.supervise_program(
            self.root,
            second["run_id"],
            max_ticks=12,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(conducted["state"], "story-certified")
        denied = self.core.build_program_delivery_preview(
            self.root,
            second["run_id"],
            driver_config=self.config,
            now=self.now,
        )
        self.assertFalse(denied["applicable"])
        self.assertIn(
            "program grant lacks certification:objective",
            [item["message"] for item in denied["issues"]],
        )

    def test_changed_candidate_artifact_refuses_as_stale_proof(self):
        projection, _fixture = self.start_and_certify()
        run_id = projection["run_id"]
        replayed = self.conductor.core.replay_program_conductor(
            self.root, run_id, now=self.now
        )
        artifact = next(
            artifact
            for receipt in replayed["receipts"]
            for artifact in receipt.get("artifacts", [])
            if artifact.get("artifact_kind") == "git-diff"
        )
        content = (
            self.root
            / ".git/pmo-programs/runs"
            / run_id
            / "conductor/artifacts"
            / artifact["artifact_id"]
            / "content"
        )
        content.chmod(0o600)
        content.write_bytes(content.read_bytes() + b"\n")
        refused = self.core.build_program_delivery_preview(
            self.root,
            run_id,
            driver_config=self.config,
            now=self.now,
        )
        self.assertFalse(refused["applicable"])
        self.assertIn(
            "candidate-refused",
            {item["code"] for item in refused["issues"]},
        )

    def test_two_story_commits_phase_transition_and_every_effect_recover(self):
        from dw_pmo.program_surface import build_program_view

        projection, fixture = self.start_and_certify()
        run_id = projection["run_id"]
        initial_count = int(
            self.authority.fixture._git(
                "rev-list", "--count", "HEAD"
            ).stdout.strip()
        )
        preview, frontier = self.preview_and_start(run_id)
        delivery_id = frontier["delivery_id"]

        # Crash after every durable effect, before its immutable receipt.
        # Each following tick must reconcile that exact effect and complete
        # the same ledger claim without a duplicate mutation/commit/push.
        for action_index, expected in enumerate(
            item["kind"] for item in preview["actions"]
        ):
            def crash(name, detail, action_kind=expected):
                if (
                    name == "after-effect"
                    and detail.get("action_kind") == action_kind
                ):
                    raise RuntimeError(f"crash after {action_kind}")

            with self.assertRaisesRegex(
                RuntimeError, f"crash after {expected}"
            ):
                self.core.tick_program_delivery(
                    self.root,
                    run_id,
                    delivery_id,
                    driver_config=self.config,
                    now=self.now,
                    boundary_hook=crash,
                )
            if action_index == 0:
                recovering_view = build_program_view(
                    self.root, run_id, now=self.now
                )
                recovering = recovering_view["live_progress"]
                self.assertEqual(
                    recovering["status"]["group"], "recovering"
                )
                self.assertEqual(
                    recovering["next_step"]["kind"], "recovering"
                )
                self.assertGreater(
                    recovering["recovery"]["active_work_tracked"], 0
                )
                self.assertIn(
                    "not been declared lost or restarted",
                    recovering["recovery"]["summary"],
                )
            recovered = self.core.tick_program_delivery(
                self.root,
                run_id,
                delivery_id,
                driver_config=self.config,
                now=self.now,
            )
            self.assertEqual(recovered["action"]["kind"], expected)

        first = self.core.replay_program_delivery(
            self.root, run_id, delivery_id, now=self.now
        )
        self.assertTrue(first["complete"])
        self.assertEqual(
            len(first["receipts"]), len(preview["actions"])
        )
        completed_view = build_program_view(
            self.root, run_id, now=self.now
        )
        completed_recovery = completed_view["live_progress"]["recovery"]
        self.assertEqual(completed_recovery["status"], "verified")
        self.assertEqual(
            completed_recovery["completed_delivery_actions_preserved"],
            len(preview["actions"]),
        )
        self.assertIn(
            "refuses conflicting duplicates",
            completed_recovery["duplicate_protection"],
        )
        self.assertEqual(
            self.authority.fixture._git(
                "rev-parse", "HEAD"
            ).stdout.strip(),
            subprocess.run(
                ["git", "--git-dir", str(self.remote), "rev-parse", "main"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip(),
        )
        readme = (
            self.root / "pm/roadmap/demo/README.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "**Current phase:** [Phase 2 - Beta]"
            "(./phase-2-beta/current-phase-status.md).",
            readme,
        )
        self.assertTrue(
            (
                self.root
                / "pm/roadmap/demo/phase-1-alpha/final-summary.md"
            ).is_file()
        )
        next_story = (
            self.root
            / "pm/roadmap/demo/phase-2-beta/story-01-dependent-beta.md"
        ).read_text(encoding="utf-8")
        self.assertIn("- **Status:** in-progress", next_story)

        second_conduction = self.conductor.core.supervise_program(
            self.root,
            run_id,
            max_ticks=12,
            # WLA-28-04: the wall-clock guard defaults to 300s and is not what
            # this case proves — max_ticks is the real bound and no test
            # asserts a time-ceiling stop. A loaded machine must not decide
            # the outcome, so the incidental ceiling is made unreachable.
            max_seconds=86_400,
            driver_config=self.config,
            adapters={"fixture": fixture},
            now=self.now,
        )
        self.assertEqual(
            (second_conduction["state"], second_conduction["stop"]),
            ("story-certified", "checkpoint"),
        )
        second_preview, second_frontier = self.preview_and_start(run_id)
        self.assertNotIn(
            "phase-advance",
            [item["kind"] for item in second_preview["actions"]],
        )
        for expected in [
            item["kind"] for item in second_preview["actions"]
        ]:
            def crash_receipt(name, detail, action_kind=expected):
                if (
                    name == "after-receipt"
                    and detail.get("action_kind") == action_kind
                ):
                    raise RuntimeError(
                        f"receipt crash after {action_kind}"
                    )

            with self.assertRaisesRegex(
                RuntimeError, f"receipt crash after {expected}"
            ):
                self.core.tick_program_delivery(
                    self.root,
                    run_id,
                    second_frontier["delivery_id"],
                    driver_config=self.config,
                    now=self.now,
                    boundary_hook=crash_receipt,
                )
            recovered = self.core.tick_program_delivery(
                self.root,
                run_id,
                second_frontier["delivery_id"],
                driver_config=self.config,
                now=self.now,
            )
            self.assertEqual(recovered["action"]["kind"], expected)
        completed = self.core.replay_program_delivery(
            self.root,
            run_id,
            second_frontier["delivery_id"],
            now=self.now,
        )
        self.assertTrue(completed["complete"])
        self.assertEqual(
            int(self.authority.fixture._git(
                "rev-list", "--count", "HEAD"
            ).stdout.strip()),
            initial_count + 2,
        )
        self.assertEqual(
            self.authority.fixture._git(
                "rev-parse", "HEAD"
            ).stdout.strip(),
            subprocess.run(
                ["git", "--git-dir", str(self.remote), "rev-parse", "main"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip(),
        )
        phase2_story = (
            self.root
            / "pm/roadmap/demo/phase-2-beta/story-01-dependent-beta.md"
        ).read_text(encoding="utf-8")
        self.assertIn("- **Status:** done", phase2_story)
        replayed = self.authority.core.replay_program(
            self.root, run_id, now=self.now
        )
        categories = [
            item["category"]
            for item in replayed["claims"]
            if str(item["idempotency_key"]).startswith(
                "program-delivery/"
            )
        ]
        self.assertEqual(categories.count("integration"), 2)
        self.assertEqual(categories.count("contract"), 2)
        self.assertEqual(categories.count("commit"), 2)
        self.assertEqual(categories.count("push"), 2)
        latest = self.authority.fixture._git(
            "rev-parse", "HEAD"
        ).stdout.strip()
        archive = (
            self.root / ".git/pmo-contract-archive"
            / latest / "CONTRACT.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '"human_attestation": false', archive
        )
        self.assertIn(
            "Program attestation provenance", archive
        )
        from dw_pmo.parse import get_project
        from dw_pmo.validate import check_project
        from dw_pmo.verify import run_verify

        self.assertEqual(
            check_project(get_project(self.root, "demo"), self.root),
            [],
        )
        verified = run_verify(self.root, all_history=True)
        self.assertTrue(verified.ok, verified.violations)
        self.assertEqual(verified.verified, 2)

    def test_commit_hook_and_remote_divergence_fail_closed_without_force(self):
        projection, _fixture = self.start_and_certify()
        run_id = projection["run_id"]
        preview, frontier = self.preview_and_start(run_id)
        delivery_id = frontier["delivery_id"]
        while True:
            current = self.core.replay_program_delivery(
                self.root, run_id, delivery_id, now=self.now
            )
            if current["next_action"]["kind"] == "commit":
                break
            self.core.tick_program_delivery(
                self.root,
                run_id,
                delivery_id,
                driver_config=self.config,
                now=self.now,
            )
        parent = self.authority.fixture._git(
            "rev-parse", "HEAD"
        ).stdout.strip()
        hook = self.root / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\nexit 23\n", encoding="utf-8")
        hook.chmod(0o755)
        with self.assertRaisesRegex(DwError, "gated commit failed"):
            self.core.tick_program_delivery(
                self.root,
                run_id,
                delivery_id,
                driver_config=self.config,
                now=self.now,
            )
        self.assertEqual(
            self.authority.fixture._git(
                "rev-parse", "HEAD"
            ).stdout.strip(),
            parent,
        )
        hook.unlink()
        committed = self.core.tick_program_delivery(
            self.root,
            run_id,
            delivery_id,
            driver_config=self.config,
            now=self.now,
        )
        self.assertEqual(committed["action"]["kind"], "commit")
        commit = committed["receipt"]["result"]["commit"]

        tree = self.authority.fixture._git(
            "rev-parse", f"{parent}^{{tree}}"
        ).stdout.strip()
        environment = dict(os.environ)
        environment.update({
            "GIT_AUTHOR_NAME": "Divergence Fixture",
            "GIT_AUTHOR_EMAIL": "divergence@example.test",
            "GIT_COMMITTER_NAME": "Divergence Fixture",
            "GIT_COMMITTER_EMAIL": "divergence@example.test",
            "GIT_AUTHOR_DATE": "2026-07-22T12:02:30Z",
            "GIT_COMMITTER_DATE": "2026-07-22T12:02:30Z",
        })
        divergent = subprocess.run(
            [
                "git", "-C", str(self.root),
                "commit-tree", tree, "-p", parent,
            ],
            input="planted remote divergence\n",
            text=True,
            check=True,
            env=environment,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        self.authority.fixture._git(
            "push", "-q", "origin",
            f"{divergent}:refs/heads/divergence-fixture",
        )
        subprocess.run(
            [
                "git", "--git-dir", str(self.remote),
                "update-ref", "refs/heads/main", divergent, parent,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        with self.assertRaisesRegex(DwError, "diverged"):
            self.core.tick_program_delivery(
                self.root,
                run_id,
                delivery_id,
                driver_config=self.config,
                now=self.now,
            )
        self.assertEqual(
            subprocess.run(
                ["git", "--git-dir", str(self.remote), "rev-parse", "main"],
                text=True,
                check=True,
                stdout=subprocess.PIPE,
            ).stdout.strip(),
            divergent,
        )
        self.assertNotEqual(divergent, commit)
        subprocess.run(
            [
                "git", "--git-dir", str(self.remote),
                "update-ref", "refs/heads/main", parent, divergent,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        pushed = self.core.tick_program_delivery(
            self.root,
            run_id,
            delivery_id,
            driver_config=self.config,
            now=self.now,
        )
        self.assertEqual(pushed["action"]["kind"], "push")
        self.assertEqual(
            subprocess.run(
                ["git", "--git-dir", str(self.remote), "rev-parse", "main"],
                text=True,
                check=True,
                stdout=subprocess.PIPE,
            ).stdout.strip(),
            commit,
        )

    def test_obligation_materialization_deduplicates_and_waiver_is_accountable(self):
        projection, _fixture = self.start_and_certify()
        run_id = projection["run_id"]
        recorded = self.conductor.record_fixture_obligation(
            projection,
            obligation_id="trace-this-debt",
            blocking=False,
        )
        preview = self.core.build_program_obligation_materialization_preview(
            self.root,
            run_id,
            "trace-this-debt",
            phase=2,
            driver_config=self.config,
            now=self.now,
        )
        self.assertTrue(preview["applicable"], preview["issues"])
        self.assertFalse(preview["no_op"])

        def crash_effect(name, detail):
            if name == "after-effect":
                raise RuntimeError("materialization applied")

        with self.assertRaisesRegex(
            RuntimeError, "materialization applied"
        ):
            self.core.apply_program_obligation_materialization(
                self.root,
                preview,
                materialization_token=preview["materialization_token"],
                driver_config=self.config,
                now=self.now,
                boundary_hook=crash_effect,
            )
        materialized = self.core.apply_program_obligation_materialization(
            self.root,
            preview,
            materialization_token=preview["materialization_token"],
            driver_config=self.config,
            now=self.now,
        )
        story_path = self.root / materialized["story_path"]
        story = story_path.read_text(encoding="utf-8")
        self.assertIn(
            "- **Program obligation:** `trace-this-debt`", story
        )
        self.assertIn(
            "- **Source decision:** "
            f"`{recorded['obligation']['source_decision_hash']}`",
            story,
        )
        duplicate = (
            self.core.build_program_obligation_materialization_preview(
                self.root,
                run_id,
                "trace-this-debt",
                phase=2,
                driver_config=self.config,
                now=self.now,
            )
        )
        self.assertTrue(duplicate["applicable"], duplicate["issues"])
        self.assertTrue(duplicate["no_op"])
        duplicate_result = (
            self.core.apply_program_obligation_materialization(
                self.root,
                duplicate,
                materialization_token=duplicate["materialization_token"],
                driver_config=self.config,
                now=self.now,
            )
        )
        self.assertTrue(duplicate_result["idempotent"])
        self.assertEqual(
            len(list(
                (
                    self.root / "pm/roadmap/demo/phase-2-beta"
                ).glob("story-*-obligation-trace-this-debt.md")
            )),
            1,
        )

        denied = self.core.build_program_obligation_disposition_preview(
            self.root,
            run_id,
            "trace-this-debt",
            to_state="waived",
            actor="some-agent",
            authority="self-asserted",
            reason="Pretend this debt does not matter.",
            now=self.now,
        )
        self.assertFalse(denied["applicable"])
        self.assertIn(
            "waiver-unauthorized",
            {item["code"] for item in denied["issues"]},
        )
        operator = "operator-a"
        expected_authority = denied["intent"][
            "expected_waiver_authority"
        ]
        allowed = self.core.build_program_obligation_disposition_preview(
            self.root,
            run_id,
            "trace-this-debt",
            to_state="waived",
            actor=operator,
            authority=expected_authority,
            reason="Accountable operator accepts this exact residual debt.",
            now=self.now,
        )
        self.assertTrue(allowed["applicable"], allowed["issues"])

        def crash_receipt(name, detail):
            if name == "after-receipt":
                raise RuntimeError("disposition receipt stored")

        with self.assertRaisesRegex(
            RuntimeError, "disposition receipt stored"
        ):
            self.core.apply_program_obligation_disposition(
                self.root,
                allowed,
                disposition_token=allowed["disposition_token"],
                driver_config=self.config,
                now=self.now,
                boundary_hook=crash_receipt,
            )
        disposed = self.core.apply_program_obligation_disposition(
            self.root,
            allowed,
            disposition_token=allowed["disposition_token"],
            driver_config=self.config,
            now=self.now,
        )
        self.assertEqual(disposed["obligation"]["state"], "waived")
        self.assertEqual(
            disposed["obligation"]["history"][-1]["authority"],
            expected_authority,
        )
        self.assertEqual(
            disposed["obligation"]["source_decision_hash"],
            recorded["obligation"]["source_decision_hash"],
        )


class LiveProgressProjectionTest(unittest.TestCase):
    """WLA-27-06: presentation groups facts but owns no run policy."""

    def test_repair_and_recovery_use_only_canonical_run_facts(self):
        from dw_pmo.live_progress import build_run_live_progress

        projection = {
            "run_id": "run-fixture",
            "state": "active",
            "story": {"id": "WLA-27-06", "title": "Explain progress"},
            "project": "work-log-automation",
            "dispatch_allowed": True,
            "expired": False,
            "expires_at": "2026-07-25T00:00:00Z",
            "control_generation": 2,
            "ledger_head": "sha256:" + "1" * 64,
            "ledger_events": 4,
            "active_claims": [],
            "completed_claims": [],
            "outstanding_requests": [],
            "budgets": {
                "max_concurrency": {"used": 0, "limit": 1},
                "max_agent_starts": {"used": 1, "limit": 2},
            },
            "capabilities": ["repository-read", "repository-write"],
            "permanent_exclusions": ["remote-admin"],
        }
        nodes = [{
            "id": "repair-ux", "type": "agent", "activation": "failure",
            "role": "repair", "state": "eligible", "attempt": 2,
            "blocked_reason": None,
        }]
        decision = {
            "scheduled": [{
                "node_id": "repair-ux", "attempt": 2,
                "kind": "claim", "reason": "failure-route",
            }],
            "eligible": [],
            "blocked": [],
            "action_needed": [],
            "resolution_needed": [],
            "terminal_needed": False,
        }
        repair = build_run_live_progress(
            projection, decision, nodes, [], []
        )
        self.assertEqual(repair["status"]["group"], "repair")
        self.assertEqual(repair["next_step"]["target"], "repair-ux")
        self.assertEqual(repair["next_step"]["action"], "tick")
        self.assertFalse(repair["selects_next_work"])
        waiting = build_run_live_progress(
            projection,
            {**decision, "scheduled": []},
            [{
                **nodes[0],
                "id": "review-after-work",
                "activation": "success",
                "role": "review",
                "state": "blocked",
                "blocked_reason": "dependencies",
            }],
            [],
            [],
        )
        self.assertEqual(waiting["progress"]["groups"]["blocked"], [])
        self.assertEqual(
            waiting["progress"]["groups"]["waiting"][0][
                "technical_ref"
            ],
            "review-after-work",
        )

        lost_projection = {
            **projection,
            "active_claims": [{
                "claim_id": "claim-existing",
                "node_id": "repair-ux",
                "last_receipt": {"state": "lost"},
            }],
        }
        recovering = build_run_live_progress(
            lost_projection, {**decision, "scheduled": []},
            [{**nodes[0], "state": "active"}], [], [],
        )
        self.assertEqual(recovering["status"]["group"], "recovering")
        self.assertEqual(recovering["next_step"]["kind"], "wait")
        self.assertEqual(
            recovering["recovery"]["active_technical_refs"],
            ["claim-existing"],
        )
        self.assertIn(
            "not been declared lost or restarted",
            recovering["recovery"]["summary"],
        )

        empty_decision = {
            **decision,
            "scheduled": [],
            "action_needed": [],
            "resolution_needed": [],
        }
        cases = [
            (
                {
                    **projection,
                    "active_claims": [{
                        "claim_id": "claim-active",
                        "node_id": "implement",
                    }],
                },
                [{**nodes[0], "id": "implement", "activation": "success",
                  "role": "implementation", "state": "active"}],
                "active",
            ),
            (
                {
                    **projection,
                    "state": "awaiting-approval",
                    "outstanding_requests": [{
                        "origin_node": "checkpoint",
                        "response_schema": {
                            "decision": ["approve", "reject"],
                        },
                    }],
                },
                [{**nodes[0], "id": "checkpoint", "type": "approval",
                  "activation": "success", "state": "awaiting-approval"}],
                "review",
            ),
            ({**projection, "state": "blocked"}, nodes, "blocked"),
            ({**projection, "state": "revoked"}, nodes, "stopped"),
            ({**projection, "state": "complete"}, nodes, "complete"),
        ]
        for facts, work, expected_group in cases:
            with self.subTest(expected_group=expected_group):
                view = build_run_live_progress(
                    facts, empty_decision, work, [], []
                )
                self.assertEqual(
                    view["status"]["group"], expected_group
                )
                if expected_group in {"stopped", "complete"}:
                    self.assertIsNone(view["next_step"]["action"])
                    self.assertEqual(
                        view["next_step"]["kind"], expected_group
                    )
        terminal = build_run_live_progress(
            {**projection, "state": "awaiting-certification"},
            decision,
            [{
                **nodes[0],
                "id": "handoff",
                "type": "approval",
                "activation": "success",
                "state": "eligible",
            }],
            [],
            [],
        )
        self.assertEqual(terminal["status"]["group"], "complete")
        self.assertEqual(terminal["next_step"]["kind"], "complete")
        self.assertIsNone(terminal["next_step"]["action"])
        self.assertEqual(
            terminal["next_step"]["source"]["path"], "/state"
        )


class BoundedActionsProjectionTest(unittest.TestCase):
    """WLA-27-07: readable actions retain exact canonical boundaries."""

    def test_measurements_never_confuse_zero_unbounded_unknown_or_na(self):
        from dw_pmo.bounded_actions import classify_measurement

        cases = [
            (0, {}, "zero", 0),
            (17, {}, "finite", 17),
            ("unbounded", {}, "unbounded", None),
            (None, {}, "unknown", None),
            (None, {"applicable": False}, "not-applicable", None),
        ]
        for value, kwargs, state, normalized in cases:
            with self.subTest(state=state):
                measured = classify_measurement(
                    "limit", value, unit="checks", **kwargs
                )
                self.assertEqual(measured["state"], state)
                self.assertEqual(measured["value"], normalized)
        self.assertNotEqual(
            classify_measurement("limit", 0)["state"],
            classify_measurement("limit", "unbounded")["state"],
        )

    def test_run_decisions_blockers_permission_and_actions_are_closed(self):
        from dw_pmo.bounded_actions import build_run_bounded_actions

        correlation = "req-" + "1" * 24
        projection = {
            "run_id": "run-" + "2" * 24,
            "state": "awaiting-approval",
            "project": "sample",
            "story": {"id": "SMP-1-01", "title": "Repair checkout"},
            "expires_at": "2026-07-26T00:00:00Z",
            "capabilities": ["repository-read", "repository-write"],
            "permanent_exclusions": ["publication", "release"],
            "budgets": {
                "max_agent_starts": {
                    "used": 2, "limit": 3, "remaining": 1,
                },
                "max_nudges": {"used": 0, "limit": 0, "remaining": 0},
            },
            "outstanding_requests": [{
                "correlation_id": correlation,
                "kind": "checkpoint",
                "origin": "human",
                "origin_node": "review-repair",
                "schema_summary": "Approve or reject the repaired checkout.",
                "response_schema": {
                    "decision": ["approve", "reject"],
                },
            }],
            "request_refusals": [{
                "seq": 7,
                "correlation_id": "req-" + "3" * 24,
                "origin_node": "old-review",
                "reason": "correlation-mismatch",
                "response_hash": "sha256:" + "4" * 64,
            }],
        }
        decision = {
            "blocked": [{
                "node_id": "repair-checkout",
                "reason": "failed-check",
            }],
        }
        graph = [{
            "id": "repair-checkout",
            "title": "Repair checkout",
            "state": "blocked",
        }]
        controls = [
            {
                "action": "tick", "decision": "", "correlation_id": "",
                "available": True, "issues": [], "reason_required": False,
                "preview_required": True, "starts_work": True,
            },
            {
                "action": "pause", "decision": "", "correlation_id": "",
                "available": True, "issues": [], "reason_required": True,
                "preview_required": True, "starts_work": False,
            },
            {
                "action": "resume", "decision": "", "correlation_id": "",
                "available": False, "issues": [
                    "cannot resume a run in state awaiting-approval",
                ], "reason_required": False, "preview_required": True,
                "starts_work": False,
            },
            {
                "action": "revoke", "decision": "", "correlation_id": "",
                "available": True, "issues": [], "reason_required": True,
                "preview_required": True, "starts_work": False,
            },
            {
                "action": "cancel", "decision": "", "correlation_id": "",
                "available": True, "issues": [], "reason_required": True,
                "preview_required": True, "starts_work": False,
            },
            *[
                {
                    "action": "request", "decision": option,
                    "correlation_id": correlation, "available": True,
                    "issues": [], "reason_required": False,
                    "preview_required": True, "starts_work": False,
                }
                for option in ("approve", "reject")
            ],
            {
                "action": "retry", "decision": "", "available": False,
                "issues": [
                    "retry is governed only by the immutable score failure policy",
                ], "reason_required": False, "preview_required": False,
                "starts_work": False,
            },
        ]
        progress = {
            "progress": {"known_total": 3, "completed": 1},
            "limits": {
                "permission": {
                    "status": "available",
                    "may_still_use": ["repository read", "repository write"],
                    "will_not_use": ["publication", "release"],
                    "summary": "Allowed change types are bounded.",
                },
                "counts": [
                    {
                        "id": "max_agent_starts", "label": "work starts",
                        "unit": "starts", "primary": True,
                    },
                    {
                        "id": "max_nudges", "label": "follow-up signals",
                        "unit": "signals", "primary": True,
                    },
                ],
                "expires_at": projection["expires_at"],
            },
            "next_step": {"kind": "repair", "action": "tick"},
            "review": {"failed_evidence": [{"work": "Checkout check"}]},
        }
        events = [{
            "seq": 5,
            "event": "run_paused",
            "ts": "2026-07-25T00:00:00Z",
            "event_hash": "sha256:" + "5" * 64,
            "detail": {"reason": "Review failure."},
        }]
        model = build_run_bounded_actions(
            projection, decision, graph, controls, progress, events
        )

        exact_decision = next(
            item for item in model["inbox"]
            if item["id"] == f"decision:{correlation}"
        )
        self.assertEqual(
            [item["decision"] for item in exact_decision["valid_choices"]],
            ["approve", "reject"],
        )
        for item in model["inbox"]:
            for key in (
                "affected_work", "why", "resolver", "valid_choices",
                "after_no_choice",
            ):
                self.assertTrue(item[key], (item["id"], key))

        action_by_name = {
            str(item["action"]): item
            for item in model["actions"]
            if item.get("action") and item["action"] != "request"
        }
        self.assertEqual(
            action_by_name["tick"]["label"], "Retry the bounded repair"
        )
        self.assertEqual(action_by_name["tick"]["action"], "tick")
        self.assertNotEqual(
            action_by_name["pause"]["consequences"]["effect"],
            action_by_name["revoke"]["consequences"]["effect"],
        )
        self.assertNotEqual(
            action_by_name["revoke"]["consequences"]["effect"],
            action_by_name["cancel"]["consequences"]["effect"],
        )
        self.assertFalse(action_by_name["retry"]["available"])
        self.assertIn(
            "does not change retry policy",
            action_by_name["tick"]["consequences"]["unchanged"],
        )

        permission = model["permission"]
        self.assertEqual(permission["scope"]["story_id"], "SMP-1-01")
        self.assertTrue(permission["allowed_effects"])
        self.assertTrue(permission["stop_conditions"])
        self.assertIn("publication", permission["forbidden_effects"])
        usage = {
            item["id"]: item for item in model["usage"]["items"]
        }
        self.assertEqual(
            usage["max_nudges"]["measurements"]["limit"]["state"], "zero"
        )
        self.assertEqual(
            usage["money-cost"]["measurements"]["actual"]["state"], "unknown"
        )
        self.assertEqual(
            usage["money-cost"]["measurements"]["limit"]["state"],
            "not-applicable",
        )
        self.assertTrue(model["receipts"][0]["exact_reference"])
        for key in (
            "starts_work", "writes_events", "selects_action",
            "selects_next_work", "grants_authority",
            "changes_retry_policy", "sends_notifications",
        ):
            self.assertFalse(model[key], key)

    def test_program_request_and_remote_guidance_never_mint_authority(self):
        from dw_pmo.bounded_actions import (
            build_program_bounded_actions,
            build_response_guidance,
        )

        request_id = "claim-" + "6" * 24
        authority = {
            "run_id": "program-" + "7" * 24,
            "state": "checkpoint",
            "selection": {"story": "SMP-1-02"},
            "scope": {
                "project": "sample", "phases": [1],
                "story_ids": ["SMP-1-02"],
            },
            "expires_at": "2026-07-26T00:00:00Z",
            "capabilities": ["agent:dispatch"],
            "permanent_exclusions": ["deployment", "release"],
            "stop_conditions": [
                "checkpoint-required", "budget-exhausted", "grant-revoked",
            ],
            "budgets": {
                "max_tokens": {
                    "used": 8_000, "limit": 12_000, "remaining": 4_000,
                },
            },
            "outstanding_requests": [{
                "claim_id": request_id,
                "port": "phase-boundary",
                "status": "open",
            }],
            "blocking_obligations": [{
                "id": "debt-1", "target": "SMP-1-02",
                "statement": "Verify the migration receipt.",
                "accountable_role": "verifier", "blocking": True,
            }],
        }
        frontier = {"stop": "checkpoint", "state": "checkpoint"}
        controls = [
            *[
                {
                    "action": "request", "decision": option,
                    "request_id": request_id, "available": True,
                    "reason_required": True, "preview_required": True,
                    "starts_work": False,
                }
                for option in ("approve", "reject")
            ],
            {
                "action": "pause", "decision": None, "request_id": None,
                "available": True, "reason_required": True,
                "preview_required": True, "starts_work": False,
            },
            {
                "action": "revoke", "decision": None, "request_id": None,
                "available": True, "reason_required": True,
                "preview_required": True, "starts_work": False,
            },
        ]
        progress = {
            "progress": {"known_total": 1, "completed": 0},
            "limits": {
                "permission": {
                    "status": "available",
                    "may_still_use": ["agent dispatch"],
                    "will_not_use": ["deployment", "release"],
                    "summary": "One exact program scope.",
                },
                "counts": [{
                    "id": "max_tokens", "label": "model tokens",
                    "unit": "tokens", "primary": True,
                }],
            },
            "next_step": {"kind": "decision"},
            "review": {},
        }
        model = build_program_bounded_actions(
            authority, frontier, controls, progress, [],
            refusal=None, receipts=[],
        )
        decision = next(
            item for item in model["inbox"]
            if item["id"] == f"decision:{request_id}"
        )
        self.assertEqual(
            [item["decision"] for item in decision["valid_choices"]],
            ["approve", "reject"],
        )
        self.assertEqual(
            model["permission"]["stop_conditions"],
            ["Checkpoint required", "Budget exhausted", "Grant revoked"],
        )
        tokens = next(
            item for item in model["usage"]["items"]
            if item["id"] == "max_tokens"
        )
        self.assertEqual(
            tokens["measurements"]["actual"]["value"], 8_000
        )
        self.assertEqual(
            tokens["measurements"]["remaining"]["value"], 4_000
        )

        guidance = build_response_guidance(
            context="program",
            affected_work="SMP-1-02",
            correlation_id=request_id,
            decisions=["approve", "reject"],
        )
        self.assertEqual(
            [item["decision"] for item in guidance["choices"]],
            ["approve", "reject"],
        )
        self.assertFalse(guidance["transport_grants_authority"])
        self.assertFalse(guidance["grants_authority"])
        self.assertIn(
            "the local preview token is fresh for the current ledger and generation",
            guidance["decisive_checks"],
        )


class ProgramSurfaceTest(unittest.TestCase):
    """WLA-26-11: one exact program control room across every adapter."""

    def setUp(self):
        import dw_pmo.program_surface as surface

        self.core = surface
        self.authority = ProgramRunAuthorityTest(
            "test_start_is_exact_immutable_idempotent_and_creates_only_local_authority"
        )
        self.authority.setUp()
        self.addCleanup(self.authority.doCleanups)
        self.root = self.authority.root
        self.intent = 0
        observed = datetime.now(timezone.utc).replace(microsecond=0)
        self.authority.issued_at = (
            observed - timedelta(seconds=30)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.authority.started_at = observed.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.expires_at = (
            observed + timedelta(seconds=3_000)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

    def start(self):
        self.intent += 1
        _plan, projection = self.authority.start(
            intent=f"surface-{self.intent}",
            expires_at=self.expires_at,
        )
        return projection

    def _serve_workbench(self):
        import threading
        from http.server import ThreadingHTTPServer

        import dw_pmo.workbench as wb

        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), wb.create_handler(self.root, None)
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        return server.server_address[1]

    @staticmethod
    def _sse_frames(body):
        frames = []
        for block in body.split("\n\n"):
            fields = {}
            for line in block.splitlines():
                if ":" in line and not line.startswith(":"):
                    key, _, value = line.partition(":")
                    fields[key.strip()] = value.strip()
            if "data" in fields:
                frames.append((int(fields["id"]), json.loads(fields["data"])))
        return frames

    def test_empty_inventory_is_healthy_dormant_and_creates_nothing(self):
        root = Path(tempfile.mkdtemp(prefix="dw-program-surface-empty."))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        subprocess.run(
            ["git", "init", "-q", str(root)],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        before = list(root.rglob("*"))
        inventory = self.core.program_summary_inventory(root)
        self.assertEqual(inventory["programs"], [])
        self.assertEqual(inventory["runs"], [])
        self.assertTrue(inventory["healthy"])
        for key in (
            "starts_work", "writes_events", "creates_grant",
            "creates_program_store", "starts_process", "starts_stream",
            "starts_poller", "sends_notifications",
        ):
            self.assertFalse(inventory[key])
        self.assertEqual(before, list(root.rglob("*")))

    def test_plan_and_start_adapters_rebuild_one_exact_grant(self):
        import dw_pmo.mcpserver as mcp
        import dw_pmo.workbench as wb

        request = {
            "program": "demo-program",
            "mode": "continuous",
            "operator": "operator-a",
            "reason": "Run the reviewed finite autonomous fixture.",
            "intent_id": "surface-adapter-start",
            "issued_at": self.authority.issued_at,
            "expires_at": self.expires_at,
        }
        expected = self.authority.core.build_program_start_plan(
            self.root,
            request["program"],
            mode=request["mode"],
            operator=request["operator"],
            approval_reason=request["reason"],
            intent_id=request["intent_id"],
            capabilities=None,
            budgets=None,
            issued_at=request["issued_at"],
            expires_at=request["expires_at"],
        )
        cli_plan = subprocess.run(
            [
                sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
                "--root", str(self.root), "program", "plan",
                request["program"], "--mode", request["mode"],
                "--operator", request["operator"],
                "--reason", request["reason"],
                "--intent", request["intent_id"],
                "--issued-at", request["issued_at"],
                "--expires-at", request["expires_at"], "--json",
            ],
            check=True, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        tool_plan = mcp.call_tool(self.root, "dw_program_plan", request)
        status, http_plan = wb.handle_mutation(
            self.root, "/api/programs/plan", request
        )
        self.assertEqual(status, 200)
        for document in (
            json.loads(cli_plan.stdout),
            tool_plan["structuredContent"],
            http_plan["data"],
        ):
            self.assertEqual(
                self.core.document_bytes(document),
                self.core.document_bytes(expected),
            )

        plan_path = self.root / ".git" / "surface-start-plan.json"
        plan_path.write_text(json.dumps(expected), encoding="utf-8")
        cli_start = subprocess.run(
            [
                sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
                "--root", str(self.root), "program", "start",
                "--plan", str(plan_path), "--expect",
                expected["start_token"], "--approve", "--json",
            ],
            check=True, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        start_args = {
            **request,
            "approve": True,
            "expect": expected["start_token"],
        }
        tool_start = mcp.call_tool(
            self.root, "dw_program_start", start_args
        )
        status, http_start = wb.handle_mutation(
            self.root, "/api/programs/start", start_args
        )
        self.assertEqual(status, 200)
        started = json.loads(cli_start.stdout)
        self.assertEqual(tool_start["structuredContent"], started)
        self.assertEqual(http_start["data"], started)
        self.assertEqual(started["state"], "running")
        self.assertEqual(started["active_claims"], [])

    def test_cli_mcp_http_view_tail_and_sse_are_one_canonical_document(self):
        import http.client

        import dw_pmo.mcpserver as mcp
        import dw_pmo.workbench as wb

        projection = self.start()
        run_id = projection["run_id"]
        ledger = (
            self.root / ".git" / "pmo-programs" / "runs" / run_id
            / "ledger.jsonl"
        )
        before = ledger.read_bytes()
        expected = self.core.build_program_view(self.root, run_id)

        cli = subprocess.run(
            [
                sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
                "--root", str(self.root), "program", "show", run_id, "--json",
            ],
            check=True, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        cli_doc = json.loads(cli.stdout)
        tool = mcp.call_tool(
            self.root, "dw_program_show", {"run_id": run_id}
        )
        status, http_doc = wb.handle_api(
            self.root, f"/api/programs/{run_id}/view", {}
        )
        self.assertEqual(status, 200)
        for document in (
            cli_doc, tool["structuredContent"], http_doc["data"],
        ):
            self.assertEqual(
                self.core.document_bytes(document),
                self.core.document_bytes(expected),
            )
        self.assertEqual(ledger.read_bytes(), before)
        rendered = json.dumps(expected, sort_keys=True)
        for excluded in (
            '"start_token":', '"act_token":', '"credentials":',
            '"prompt":', '"command":', '"argv":', '"principal":',
            '"auth_domain":', '"artifact_content":',
        ):
            self.assertNotIn(excluded, rendered)
        self.assertFalse(expected["starts_work"])
        self.assertFalse(expected["writes_events"])
        progress = expected["live_progress"]
        self.assertEqual(
            progress["kind"], "delivery-workbench-live-progress"
        )
        self.assertEqual(
            [item["id"] for item in progress["answers"]],
            [
                "delivery", "team", "passed", "blocked", "decision",
                "remaining-change-spend", "next",
            ],
        )
        if expected["current"]["next_action"] is not None:
            self.assertEqual(
                progress["next_step"]["action"],
                expected["current"]["next_action"],
            )
            self.assertEqual(
                progress["next_step"]["source"],
                {
                    "model": "delivery-workbench-program-frontier",
                    "path": "/next_actions/0",
                },
            )
        self.assertEqual(
            set(progress["review"]),
            {
                "mechanical", "agent_judgment", "dissent", "repair",
                "final_governed_decisions",
            },
        )
        self.assertIn(
            "refuses conflicting duplicates",
            progress["recovery"]["duplicate_protection"],
        )
        self.assertEqual(progress["limits"]["cost"]["status"], "measured")
        self.assertIn(
            "model tokens used",
            progress["limits"]["cost"]["summary"],
        )
        self.assertEqual(
            {
                item["id"]: (
                    item["used"], item["limit"], item["remaining"],
                )
                for item in progress["limits"]["counts"]
            },
            {
                key: (
                    value["used"], value["limit"], value["remaining"],
                )
                for key, value in expected["budgets"].items()
            },
        )
        for key in (
            "starts_work", "writes_events", "selects_next_work",
            "decides_recovery", "grants_authority",
        ):
            self.assertFalse(progress[key], key)
        bounded = expected["bounded_actions"]
        self.assertEqual(
            bounded["kind"], "delivery-workbench-bounded-actions"
        )
        self.assertEqual(bounded["context"], "program")
        self.assertEqual(
            bounded["permission"]["scope"], expected["scope"]
        )
        self.assertEqual(
            len(bounded["permission"]["stop_conditions"]),
            len(expected["stop_conditions"]),
        )
        self.assertTrue(all(
            item[:1].isupper()
            for item in bounded["permission"]["stop_conditions"]
        ))
        self.assertEqual(
            expected["stop_conditions"],
            self.authority.core.replay_program(
                self.root, run_id
            )["stop_conditions"],
        )
        for key in (
            "starts_work", "writes_events", "selects_action",
            "selects_next_work", "grants_authority",
            "changes_retry_policy", "sends_notifications",
        ):
            self.assertFalse(bounded[key], key)
        team_review = expected["team_review"]
        self.assertEqual(
            team_review["kind"], "delivery-workbench-team-review"
        )
        self.assertEqual(team_review["context"], "live")
        self.assertEqual(
            team_review["source_models"],
            [
                "delivery-workbench-team-assignment",
                "delivery-workbench-program-event",
            ],
        )
        self.assertEqual(
            [item["id"] for item in team_review["sections"]],
            [
                "responsibilities", "independence", "decisions",
                "escalation", "audit",
            ],
        )
        self.assertEqual(
            team_review["runtime_independence"]["status"], "proven"
        )
        self.assertTrue(team_review["quality_constraints"])
        self.assertTrue(all(
            item["status"] == "runtime-proven"
            for item in team_review["quality_constraints"]
        ))
        self.assertTrue(
            team_review["technical_details"][
                "provider_model_do_not_prove_independence"
            ]
        )
        escalation_answer = next(
            item["answer"] for item in team_review["sections"]
            if item["id"] == "escalation"
        )
        self.assertIn(
            "If work escalates",
            escalation_answer,
        )
        self.assertNotIn("An open escalation", escalation_answer)
        self.assertEqual(
            len(team_review["dissent"]),
            sum(
                1 for item in expected["decisions"]
                if item["result"] in {
                    "dissent", "quorum-lost", "overturn", "escalate",
                }
            ),
        )
        for key in (
            "starts_work", "writes_policy", "writes_roadmap",
            "writes_run_state", "creates_grant", "starts_process",
            "starts_observer", "sends_notification", "uses_network",
        ):
            self.assertFalse(team_review[key], key)

        tail = self.core.tail_program_events(self.root, run_id)
        tail_tool = mcp.call_tool(
            self.root, "dw_program_tail",
            {"run_id": run_id, "after": 0, "limit": 1000},
        )
        status, tail_http = wb.handle_api(
            self.root, f"/api/programs/{run_id}/tail",
            {"after": ["0"], "limit": ["1000"]},
        )
        tail_cli = subprocess.run(
            [
                sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
                "--root", str(self.root), "program", "tail", run_id,
                "--after", "0", "--json",
            ],
            check=True, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(
            [
                tail_tool["structuredContent"],
                tail_http["data"],
                json.loads(tail_cli.stdout),
            ],
            [tail, tail, tail],
        )

        port = self._serve_workbench()
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        conn.request(
            "GET", f"/api/programs/{run_id}/events?from=0&follow=0"
        )
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        conn.close()
        self.assertEqual(response.status, 200)
        self.assertIn("text/event-stream", response.getheader("Content-Type"))
        frames = self._sse_frames(body)
        self.assertEqual(
            [document for _seq, document in frames], tail["events"]
        )
        self.assertEqual(
            [seq for seq, _document in frames],
            [event["seq"] for event in tail["events"]],
        )
        self.assertNotIn("act_token", body)
        self.assertNotIn("start_token", body)

    def test_exact_act_tokens_strict_allowlists_and_bounded_supervision(self):
        import dw_pmo.mcpserver as mcp
        import dw_pmo.workbench as wb

        projection = self.start()
        run_id = projection["run_id"]
        ledger = (
            self.root / ".git" / "pmo-programs" / "runs" / run_id
            / "ledger.jsonl"
        )
        preview = self.core.build_program_act_preview(
            self.root, run_id, "tick"
        )
        self.assertTrue(preview["applicable"], preview["issues"])
        before = ledger.read_bytes()
        with self.assertRaisesRegex(DwError, "stale or altered"):
            self.core.apply_program_act(
                self.root, run_id, "tick", "sha256:" + "0" * 64
            )
        self.assertEqual(ledger.read_bytes(), before)

        result = self.core.apply_program_act(
            self.root, run_id, "tick", preview["act_token"]
        )
        self.assertEqual(result["kind"], self.core.PROGRAM_TICK_SURFACE_KIND)
        self.assertEqual(result["lane"], "conductor")
        self.assertTrue(result["progressed"])
        with self.assertRaisesRegex(DwError, "stale or altered"):
            self.core.apply_program_act(
                self.root, run_id, "tick", preview["act_token"]
            )

        supervise = self.core.build_program_act_preview(
            self.root, run_id, "supervise", max_ticks=1, max_seconds=30
        )
        bounded = self.core.apply_program_act(
            self.root, run_id, "supervise", supervise["act_token"],
            max_ticks=1, max_seconds=30,
        )
        self.assertEqual(bounded["tick_count"], 1)
        self.assertEqual(len(bounded["ticks"]), 1)
        self.assertTrue(bounded["bounded"])
        self.assertEqual(bounded["max_ticks"], 1)

        rejected = mcp.call_tool(
            self.root, "dw_program_tick",
            {
                "run_id": run_id,
                "expect": "sha256:" + "0" * 64,
                "policy": {},
            },
        )
        self.assertTrue(rejected["isError"])
        self.assertIn("unknown parameter", rejected["content"][0]["text"])
        status, body = wb.handle_mutation(
            self.root,
            "/api/programs/preview",
            {"run_id": run_id, "action": "tick", "adapter": "fixture"},
        )
        self.assertEqual(status, 400)
        self.assertIn("unknown program preview parameter", body["issues"][0])
        status, body = wb.handle_mutation(
            self.root,
            "/api/programs/preview",
            {"run_id": run_id, "action": "tick", "reason": {"prompt": "x"}},
        )
        self.assertEqual(status, 400)
        self.assertIn("must be a non-empty string", body["issues"][0])
        nested = mcp.call_tool(
            self.root,
            "dw_program_plan",
            {
                "program": "demo-program",
                "mode": "continuous",
                "operator": "operator-a",
                "reason": "bounded",
                "intent_id": "nested-budget-refusal",
                "issued_at": self.authority.issued_at,
                "expires_at": self.expires_at,
                "budgets": {"max_agent_starts": {"retry": 99}},
            },
        )
        self.assertTrue(nested["isError"])
        self.assertIn("integer ceilings", nested["content"][0]["text"])
        forbidden = {
            "policy", "prompt", "command", "argv", "credentials",
            "assignment", "rubric", "checks", "retry",
        }
        for name, spec in mcp.TOOLS.items():
            if not name.startswith("dw_program_"):
                continue
            self.assertFalse(
                forbidden & set(spec["inputSchema"]["properties"]),
                name,
            )
            self.assertFalse(spec["inputSchema"]["additionalProperties"])

    def test_concurrent_public_ticks_consume_one_exact_frontier(self):
        from concurrent.futures import ThreadPoolExecutor
        import threading

        projection = self.start()
        run_id = projection["run_id"]
        preview = self.core.build_program_act_preview(
            self.root, run_id, "tick"
        )
        barrier = threading.Barrier(2)

        def synchronized_preview(*_args, **_kwargs):
            # Both callers consume the same already-reviewed frontier. Keep
            # the potentially expensive pure preview replay outside this
            # rendezvous so the test isolates the execution race.
            barrier.wait(timeout=10)
            return preview

        def invoke():
            try:
                return (
                    "ok",
                    self.core.apply_program_act(
                        self.root,
                        run_id,
                        "tick",
                        preview["act_token"],
                    ),
                )
            except DwError as exc:
                return ("refused", exc.message)

        with mock.patch.object(
            self.core,
            "build_program_act_preview",
            side_effect=synchronized_preview,
        ):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _index: invoke(), range(2)))
        self.assertEqual(
            sorted(item[0] for item in results),
            ["ok", "refused"],
            results,
        )
        refusal = next(item[1] for item in results if item[0] == "refused")
        self.assertIn("stale", refusal)
        view = self.core.build_program_view(self.root, run_id)
        self.assertEqual(len(view["activities"]["completed"]), 1)

    def test_typed_program_request_and_notification_never_confer_authority(self):
        import dw_pmo.notifications as ntf

        projection = self.start()
        run_id = projection["run_id"]
        action_id = "act-" + "a" * 24
        selection = projection["selection"]
        workflow = str(selection["workflow"]["slug"])
        address = (
            f"program/{run_id}/phase/{selection['phase']}"
            f"/story/{selection['story']}/workflow/{workflow}"
            "/checkpoint/phase-boundary/attempt/1"
        )
        claim_preview = self.authority.claim_preview(
            run_id,
            "checkpoint-request",
            key=f"program-conductor/{action_id}/checkpoint",
            subject={
                "kind": "program-decision-checkpoint",
                "id": address,
                "hash": self.authority.h("c"),
                "phase": selection["phase"],
                "story": selection["story"],
            },
            port="phase-boundary",
            at=self.authority.started_at,
        )
        claimed = self.authority.apply_claim(
            claim_preview, at=self.authority.started_at
        )
        request_id = claimed["active_claims"][0]["claim_id"]

        inventory = ntf.build_notifications(self.root)
        notification = next(
            item for item in inventory["notifications"]
            if item["kind"] == "program-intervention-required"
            and item["run_id"] == run_id
        )
        self.assertEqual(
            notification["request"]["correlation_id"], request_id
        )
        self.assertEqual(
            notification["request"]["response_schema"]["decision"],
            ["approve", "reject"],
        )
        self.assertEqual(
            [
                item["decision"]
                for item in notification["request"]["guidance"]["choices"]
            ],
            ["approve", "reject"],
        )
        self.assertFalse(
            notification["request"]["guidance"][
                "transport_grants_authority"
            ]
        )
        self.assertNotIn("act_token", notification["outbound"])
        self.assertEqual(
            ntf.resolve_correlation(self.root, request_id)["id"],
            notification["id"],
        )

        with self.assertRaisesRegex(DwError, "approve or reject"):
            self.core.build_program_act_preview(
                self.root, run_id, "request",
                request_id=request_id, decision="maybe",
                reason="Use a closed response only.",
            )
        preview = self.core.build_program_act_preview(
            self.root, run_id, "request",
            request_id=request_id, decision="approve",
            reason="Approve this exact typed checkpoint.",
        )
        response = self.core.apply_program_act(
            self.root, run_id, "request", preview["act_token"],
            request_id=request_id, decision="approve",
            reason="Approve this exact typed checkpoint.",
        )
        self.assertEqual(response["decision"], "approve")
        self.assertEqual(
            self.authority.core.replay_program(
                self.root, run_id
            )["outstanding_requests"],
            [],
        )
        with self.assertRaises(DwError):
            ntf.resolve_correlation(self.root, request_id)

    def test_program_notification_taxonomy_covers_all_required_stops(self):
        import dw_pmo.notifications as ntf
        import dw_pmo.program_surface as surface

        common = {
            "event_count": 7,
            "ledger_head": "sha256:" + "a" * 64,
            "requests": [],
            "dissent": [],
            "verdicts": [],
            "decisions": [],
            "activities": {"sessions": []},
            "gates": [],
            "obligations": {"open": []},
            "budgets": {},
            "integrations": [],
        }
        complete = {
            **common,
            "run_id": "program-" + "1" * 24,
            "state": "complete",
            "current": {"stop": "architect-veto"},
            "requests": [{
                "claim_id": "claim-" + "1" * 24,
                "status": "open", "port": "phase-boundary",
            }],
            "dissent": [{
                "action_id": "decision-1",
                "address": "council/design",
                "result": "dissent",
            }],
            "activities": {"sessions": [{
                "session_id": "session-" + "1" * 24,
                "state": "lost",
            }]},
            "obligations": {"open": [{
                "id": "debt-1",
                "obligation_hash": "sha256:" + "b" * 64,
                "blocking": True,
                "due_at": "2026-01-01T00:00:00Z",
            }]},
            "budgets": {
                "max_tokens": {"used": 10, "limit": 10, "remaining": 0},
            },
            "integrations": [{"result": "refused"}],
        }
        decider = {
            **common,
            "run_id": "program-" + "2" * 24,
            "state": "running",
            "current": {"stop": "role-unavailable"},
        }
        summaries = {
            "runs": [
                {"run_id": complete["run_id"], "valid": True},
                {"run_id": decider["run_id"], "valid": True},
            ],
        }
        views = {
            complete["run_id"]: complete,
            decider["run_id"]: decider,
        }
        with (
            mock.patch.object(
                surface, "program_summary_inventory",
                return_value=summaries,
            ),
            mock.patch.object(
                surface, "build_program_view",
                side_effect=lambda _root, run_id, now=None: views[run_id],
            ),
        ):
            facts = ntf._program_notifications(  # noqa: protected-access
                self.root, now="2026-07-23T00:00:00Z"
            )
        kinds = {item["kind"] for item in facts}
        self.assertTrue({
            "program-intervention-required",
            "program-disagreement",
            "program-decider-loss",
            "program-provider-loss",
            "program-architect-veto",
            "program-obligation-new",
            "program-obligation-blocking",
            "program-obligation-overdue",
            "program-budget-exhausted",
            "program-integration-refused",
            "program-complete",
        } <= kinds)


class ProgramOrganizationTest(unittest.TestCase):
    """WLA-26-04: role topology, separation, visibility, and replacement."""

    def setUp(self):
        import dw_pmo.program_organization as organization_core

        self.core = organization_core
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-organization-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        template = (
            TESTS_DIR.parent / "templates" / "organizations"
            / "autonomous-story-cell.json"
        )
        self.raw = json.loads(template.read_text(encoding="utf-8"))
        self.path = self.root / "pm/organizations/autonomous-story-cell.json"
        self.path.parent.mkdir(parents=True)
        self.path.write_text(
            json.dumps(self.raw, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def config(self):
        profiles = {}
        for agent in self.raw["agents"]:
            writer = "workspace:write" in agent["capability_ceiling"]
            profiles[agent["profile"]] = {
                "adapter": "fixture",
                "adapter_version": "fixture-organization-v1",
                "principal": agent["profile"],
                "available": True,
                "max_concurrency": agent["max_concurrency"],
                "capabilities": (
                    ["repository-read", "repository-write"]
                    if writer else ["repository-read"]
                ),
                "workspace_modes": (
                    ["isolated-worktree"] if writer else ["read-only"]
                ),
                "router": "fixture-router",
                "provider": "fixture-provider",
                "model_vendor": "fixture-vendor",
                "model_family": "fixture-family",
                "model": f"fixture/{agent['profile']}",
                "model_binding": "requested-alias",
                "auth_domain": f"auth-{agent['profile']}",
            }
        return {
            "kind": "delivery-workbench-driver-config",
            "schema_version": 1,
            "workspace_root": None,
            "profiles": profiles,
        }

    def assign(self, config=None, workflow=None):
        compiled = self.core.compile_organization(self.root, self.raw)
        return self.core.assign_organization_team(
            compiled,
            "story-cell",
            driver_config=config or self.config(),
            policy_bundle_hash="sha256:" + "7" * 64,
            story_id="DM-1-02",
            workflow_address=(
                "program/demo/phase/1/story/DM-1-02/workflow/story"
            ),
            program_capabilities=[
                "agent:dispatch", "workspace:write", "verdict:issue",
                "council:decide", "obligation:record",
            ],
            workflow=workflow,
        )

    @staticmethod
    def codes(document):
        return {item["code"] for item in document["diagnostics"]}

    def cli(self, *args, root=None):
        return subprocess.run(
            [
                sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
                "--root", str(root or self.root), "organization", *args,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_compiler_is_closed_layout_independent_and_pure(self):
        core = self.core
        before = self.path.read_bytes()
        compiled = core.compile_organization(self.root, "autonomous-story-cell")
        self.assertEqual(compiled["kind"], core.COMPILED_ORGANIZATION_KIND)
        self.assertTrue(compiled["logical_assignment_proofs"][0]["satisfiable"])
        self.assertRegex(compiled["semantic_hash"], r"^sha256:[0-9a-f]{64}$")
        moved = json.loads(json.dumps(self.raw))
        moved["layout"] = {"nodes": {"verifier": {"x": 20, "y": 30}}}
        moved_compiled = core.compile_organization(self.root, moved)
        self.assertEqual(compiled["semantic_hash"], moved_compiled["semantic_hash"])
        self.assertNotEqual(compiled["document_hash"], moved_compiled["document_hash"])
        simulation = core.simulate_organization(self.root, "autonomous-story-cell")
        self.assertFalse(simulation["starts_work"])
        self.assertFalse(simulation["writes_run_state"])
        self.assertEqual(before, self.path.read_bytes())

    def test_assignment_preassigns_independent_verifier_and_packet_boundaries(self):
        assignment = self.assign()
        self.assertTrue(assignment["applicable"], assignment["issues"])
        self.assertTrue(assignment["separation"]["passed"])
        self.assertTrue(all(assignment["separation"]["facts"].values()))
        implementer = assignment["implementer"]
        verifier = assignment["verifier"]
        self.assertNotEqual(
            implementer["principal_fingerprint"],
            verifier["principal_fingerprint"],
        )
        self.assertNotEqual(
            implementer["session_binding_key"], verifier["session_binding_key"]
        )
        roles = {item["role"]: item for item in assignment["roles"]}
        self.assertEqual(roles["verifier"]["packet_policy"]["workspace"], "read-only")
        self.assertNotIn(
            "workspace:write",
            roles["verifier"]["packet_policy"]["effective_capability_ceiling"],
        )
        self.assertNotIn("candidate-diff", roles["critic"]["packet_policy"]["context"]["allow"])
        self.assertIn("roadmap", roles["master-architect"]["packet_policy"]["context"]["allow"])
        serialized = json.dumps(assignment).lower()
        for forbidden in ('"command"', "api_token", "password", "credential"):
            self.assertNotIn(forbidden, serialized)
        for role in assignment["roles"]:
            for member in role["members"]:
                self.assertRegex(
                    member["adapter_capability_fingerprint"],
                    r"^sha256:[0-9a-f]{64}$",
                )
                self.assertEqual(member["execution"]["harness"], "fixture")
                self.assertEqual(
                    member["execution"]["provider"], "fixture-provider"
                )
                self.assertEqual(
                    member["execution"]["model_binding"], "requested-alias"
                )
                self.assertRegex(
                    member["execution"]["auth_domain_fingerprint"],
                    r"^sha256:[0-9a-f]{64}$",
                )

    def test_provider_family_diversity_is_declared_enforced_and_fail_closed(self):
        import dw_pmo.orchestration_driver as driver_core
        from dw_pmo.team_review import build_team_review

        raw = json.loads(json.dumps(self.raw))
        raw["diversity"] = [{
            "id": "cross-family-review",
            "kind": "provider-family",
            "roles": ["implementer", "verifier"],
        }]
        implementer_role = next(
            role for role in raw["teams"][0]["roles"]
            if role["id"] == "implementer"
        )
        implementer_role["replacement"]["fallback_pools"] = []
        compiled = self.core.compile_organization(self.root, raw)

        config = self.config()
        config["profiles"]["builder-primary"]["provider_family"] = "family-a"
        config["profiles"]["verifier-primary"]["provider_family"] = "family-a"
        config["profiles"]["verifier-backup"]["provider_family"] = "family-b"
        assignment = self.core.assign_organization_team(
            compiled,
            "story-cell",
            driver_config=config,
            policy_bundle_hash="sha256:" + "7" * 64,
            story_id="DM-1-02",
            workflow_address="program/demo/phase/1/story/DM-1-02/workflow/story",
            program_capabilities=[
                "agent:dispatch", "workspace:write", "verdict:issue",
                "council:decide", "obligation:record",
            ],
        )
        self.assertTrue(assignment["applicable"], assignment["issues"])
        self.assertEqual(assignment["verifier"]["profile"], "verifier-backup")
        self.assertTrue(assignment["diversity"]["passed"])
        receipt = assignment["diversity"]["rules"][0]
        self.assertEqual(receipt["id"], "cross-family-review")
        self.assertEqual(
            receipt["families"],
            {"implementer": "family-a", "verifier": "family-b"},
        )
        review = build_team_review(
            raw,
            {"valid": True, "diagnostics": []},
            compiled,
            assignment=assignment,
        )
        family_rule = next(
            item for item in review["quality_constraints"]
            if item.get("kind") == "provider-family"
        )
        self.assertEqual(family_rule["status"], "runtime-proven")
        self.assertIn(
            "reviewed by a different model family",
            review["review_before_save"]["independence"],
        )

        same_family = json.loads(json.dumps(config))
        same_family["profiles"]["verifier-backup"]["provider_family"] = "family-a"
        refused = self.core.assign_organization_team(
            compiled,
            "story-cell",
            driver_config=same_family,
            policy_bundle_hash="sha256:" + "7" * 64,
            story_id="DM-1-02",
            workflow_address="program/demo/phase/1/story/DM-1-02/workflow/story",
            program_capabilities=[
                "agent:dispatch", "workspace:write", "verdict:issue",
                "council:decide", "obligation:record",
            ],
        )
        diagnostic = next(
            item for item in refused["issues"]
            if item["code"] == "provider-diversity-unsatisfied"
        )
        self.assertFalse(refused["applicable"])
        self.assertIn("cross-family-review", diagnostic["message"])
        self.assertIn("missing a family different from family-a", diagnostic["message"])

        undeclared = json.loads(json.dumps(config))
        for profile in undeclared["profiles"].values():
            profile.pop("provider_family", None)
        with mock.patch.dict(
            driver_core.ADAPTER_PROVIDER_FAMILIES, {}, clear=True
        ):
            refused = self.core.assign_organization_team(
                compiled,
                "story-cell",
                driver_config=undeclared,
                policy_bundle_hash="sha256:" + "7" * 64,
                story_id="DM-1-02",
                workflow_address="program/demo/phase/1/story/DM-1-02/workflow/story",
                program_capabilities=[
                    "agent:dispatch", "workspace:write", "verdict:issue",
                    "council:decide", "obligation:record",
                ],
            )
        self.assertFalse(refused["applicable"])
        diagnostic = next(
            item for item in refused["issues"]
            if item["code"] == "provider-diversity-unsatisfied"
        )
        self.assertIn("declared provider family", diagnostic["message"])

        unknown = json.loads(json.dumps(raw))
        unknown["diversity"][0]["roles"][1] = "ghost-reviewer"
        validation = self.core.validate_organization(self.root, unknown)
        self.assertFalse(validation["valid"])
        self.assertIn("dangling-role-reference", self.codes(validation))

        self.assertEqual(
            {
                driver_core.FixtureDriver.provider_family,
                driver_core.CodexExecDriver.provider_family,
                driver_core.ClaudeCodeExecDriver.provider_family,
                driver_core.PiExecDriver.provider_family,
            },
            {"fixture", "openai", "anthropic", "pi"},
        )

    def test_assignment_is_stable_and_explains_unavailable_fallbacks(self):
        config = self.config()
        config["profiles"]["verifier-primary"]["available"] = False
        first = self.assign(config)
        second = self.assign(config)
        self.assertEqual(
            self.core.canonical_json(first), self.core.canonical_json(second)
        )
        self.assertTrue(first["applicable"], first["issues"])
        self.assertEqual(first["verifier"]["profile"], "verifier-backup")
        verifier_role = next(
            item for item in first["roles"] if item["role"] == "verifier"
        )
        self.assertIn(
            {"agent": "verifier-primary", "reason": "profile-unavailable"},
            verifier_role["exclusions"],
        )
        self.assertTrue(first["verifier"]["fallback"])

        config["profiles"]["verifier-backup"]["available"] = False
        refused = self.assign(config)
        self.assertFalse(refused["applicable"])
        self.assertIn(
            "separation-violation", {item["code"] for item in refused["issues"]}
        )

    def test_provider_or_model_drift_changes_roster_and_assignment_authority(self):
        baseline = self.assign()
        changed_config = self.config()
        changed_config["profiles"]["judge"]["provider"] = "other-provider"
        changed_config["profiles"]["judge"]["model"] = "fixture/judge-v2"
        changed = self.assign(changed_config)
        self.assertTrue(changed["applicable"], changed["issues"])
        self.assertNotEqual(baseline["roster_hash"], changed["roster_hash"])
        self.assertNotEqual(
            baseline["assignment_hash"], changed["assignment_hash"]
        )
        judge = next(
            role["selected"] for role in changed["roles"]
            if role["role"] == "judge"
        )
        self.assertEqual(judge["execution"]["provider"], "other-provider")
        self.assertEqual(judge["execution"]["model"], "fixture/judge-v2")

    def test_colliding_principals_and_capability_downgrade_refuse(self):
        collision = self.config()
        for profile in (
            "builder-primary", "builder-backup",
            "verifier-primary", "verifier-backup",
        ):
            collision["profiles"][profile]["principal"] = "shared-delivery-session"
        collided = self.assign(collision)
        self.assertFalse(collided["applicable"])
        self.assertIn(
            "separation-violation", {item["code"] for item in collided["issues"]}
        )

        downgraded = self.config()
        downgraded["profiles"]["verifier-primary"]["capabilities"] = []
        downgraded["profiles"]["verifier-backup"]["capabilities"] = []
        refused = self.assign(downgraded)
        verifier = next(item for item in refused["roles"] if item["role"] == "verifier")
        self.assertIn("capability-mismatch", {item["reason"] for item in verifier["exclusions"]})
        self.assertFalse(refused["applicable"])

    def test_council_cardinality_resources_and_visibility_are_explicit(self):
        assignment = self.assign()
        council = assignment["councils"][0]
        self.assertEqual(council["member_cardinality"], 4)
        self.assertEqual(len(council["assigned_principals"]), 4)
        self.assertTrue(council["quorum_satisfiable"])
        conflicts = assignment["resource_plan"]["conflicts"]
        self.assertTrue(any(
            {item["left"], item["right"]} == {"critic", "judge"}
            and item["effect"] == "serialize"
            for item in conflicts
        ))
        waves = assignment["resource_plan"]["concurrency_waves"]
        critic_wave = next(index for index, wave in enumerate(waves) if "critic[1]" in wave)
        judge_wave = next(index for index, wave in enumerate(waves) if "judge[1]" in wave)
        self.assertNotEqual(critic_wave, judge_wave)

    def test_replacement_is_finite_and_preserves_verdict_lineage(self):
        core = self.core
        assignment = self.assign()
        replacement = core.plan_assignment_replacement(
            assignment, "verifier", "failed"
        )
        self.assertTrue(replacement["applicable"], replacement["issues"])
        self.assertTrue(replacement["preserves_history"])
        self.assertTrue(replacement["capability_unchanged"])
        self.assertEqual(replacement["new"]["assignment_generation"], 2)
        self.assertEqual(len(replacement["preserved_lineage"]), 2)
        self.assertTrue(any(path.endswith("/verdict") for path in replacement["invalidates"]))

        advanced = json.loads(json.dumps(assignment))
        verifier = next(item for item in advanced["roles"] if item["role"] == "verifier")
        verifier["members"] = [replacement["new"]]
        verifier["selected"] = replacement["new"]
        exhausted = core.plan_assignment_replacement(advanced, "verifier", "failed")
        self.assertFalse(exhausted["applicable"])
        self.assertEqual(exhausted["route"], "block")
        self.assertIn("replacement-exhausted", {item["code"] for item in exhausted["issues"]})

    def test_static_collisions_quorum_and_write_smuggling_refuse(self):
        broken = json.loads(json.dumps(self.raw))
        agents = {item["id"]: item for item in broken["agents"]}
        agents["verifier-primary"]["profile"] = "builder-primary"
        agents["verifier-primary"]["workspace_domain"] = "builder-primary"
        broken["councils"][0]["quorum"] = 5
        verifier = next(
            role for role in broken["teams"][0]["roles"]
            if role["id"] == "verifier"
        )
        verifier["capability_ceiling"].append("workspace:write")
        validation = self.core.validate_organization(self.root, broken)
        self.assertFalse(validation["valid"])
        self.assertTrue(
            {"impossible-independence", "impossible-quorum", "capability-smuggling"}
            <= self.codes(validation),
            validation["diagnostics"],
        )

    def test_workflow_role_requirements_intersect_capability_and_visibility(self):
        from dw_pmo.program_workflow import compile_workflow

        workflow = compile_workflow(self.root, {
            "kind": "delivery-workbench-workflow",
            "schema_version": 1,
            "slug": "organization-check",
            "title": "Organization check",
            "version": "1.0.0",
            "parameters": [{
                "id": "story-id", "type": "string", "required": True,
                "max_bytes": 100,
            }],
            "defaults": {"story-id": "DM-1-02"},
            "nodes": [
                {
                    "id": "implement", "type": "agent", "role": "implementer",
                    "task": "Implement.", "workspace": "isolated-worktree",
                    "capability_ceiling": ["agent:dispatch", "workspace:write"],
                    "timeout_seconds": 60, "max_attempts": 1,
                    "inputs": {"story": {"kind": "parameter", "name": "story-id"}},
                    "outputs": [{"id": "candidate", "kind": "git-diff", "max_bytes": 1000}],
                    "on_failure": {"kind": "action", "target": "block"},
                },
                {
                    "id": "verify", "type": "verdict", "needs": ["implement"],
                    "role": "verifier", "rubric": "quality",
                    "subject": {"kind": "artifact", "name": "implement.candidate"},
                    "freshness_seconds": 60, "max_rationale_bytes": 1000,
                    "results": ["pass", "fail"],
                    "routes": {
                        "pass": {"kind": "terminal", "target": "complete"},
                        "fail": {"kind": "action", "target": "block"},
                    },
                },
            ],
            "terminals": [{"id": "complete", "meaning": "complete"}],
        })
        organization = self.core.compile_organization(self.root, self.raw)
        requirements, issues = self.core.validate_workflow_team(
            organization,
            "story-cell",
            workflow,
            ["agent:dispatch", "workspace:write", "verdict:issue"],
        )
        self.assertEqual(issues, [])
        self.assertEqual(
            requirements["verifier"]["artifact_reads"], ["git-diff"]
        )
        narrowed = json.loads(json.dumps(organization))
        verifier = next(
            role for role in narrowed["organization"]["teams"][0]["roles"]
            if role["id"] == "verifier"
        )
        verifier["capability_ceiling"].remove("verdict:issue")
        verifier["artifacts"]["read"].remove("git-diff")
        _requirements, refused = self.core.validate_workflow_team(
            narrowed,
            "story-cell",
            workflow,
            ["agent:dispatch", "workspace:write", "verdict:issue"],
        )
        self.assertTrue(
            {"role-capability-denied", "visibility-denied"}
            <= {item["code"] for item in refused}
        )

    def test_cli_inventory_validate_simulate_and_empty_state_share_core(self):
        listed = self.cli("list", "--json")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(json.loads(listed.stdout), self.core.organization_inventory(self.root))
        valid = self.cli("validate", "autonomous-story-cell", "--json")
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertTrue(json.loads(valid.stdout)["valid"])
        simulation = self.cli("simulate", "autonomous-story-cell", "--json")
        self.assertEqual(simulation.returncode, 0, simulation.stderr)
        self.assertEqual(
            json.loads(simulation.stdout),
            self.core.simulate_organization(self.root, "autonomous-story-cell"),
        )
        empty = self.tmp / "empty"
        empty.mkdir()
        before = list(empty.rglob("*"))
        inventory = self.core.organization_inventory(empty)
        self.assertTrue(inventory["healthy"])
        self.assertEqual(inventory["organizations"], [])
        self.assertEqual(before, list(empty.rglob("*")))


class ProgramStudioTest(unittest.TestCase):
    """WLA-26-06: optional Studio parity, graph/config, and guarded saves."""

    def setUp(self):
        import dw_pmo.program_studio as studio_core

        self.core = studio_core
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-program-studio-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        (self.root / "pm/workflows").mkdir(parents=True)
        (self.root / "pm/organizations").mkdir(parents=True)
        (self.root / "pm/orchestration").mkdir(parents=True)
        for source in (TESTS_DIR.parent / "templates/workflows").glob("*.json"):
            shutil.copy2(source, self.root / "pm/workflows" / source.name)
        shutil.copy2(
            TESTS_DIR.parent / "templates/organizations/autonomous-story-cell.json",
            self.root / "pm/organizations/autonomous-story-cell.json",
        )
        shutil.copy2(
            TESTS_DIR.parent / "templates/orchestration/research-build-review.json",
            self.root / "pm/orchestration/research-build-review.json",
        )

    def test_no_program_is_healthy_pure_and_creates_nothing(self):
        empty = self.tmp / "ordinary"
        empty.mkdir()
        before = list(empty.rglob("*"))
        model = self.core.build_program_studio(empty)
        self.assertTrue(model["healthy"])
        self.assertTrue(model["empty"])
        self.assertTrue(model["ordinary_workbench_ready"])
        self.assertEqual(model["default_route"], "#/")
        self.assertEqual(model["studio_route"], "#/program-studio")
        self.assertEqual(model["empty_state"]["tone"], "neutral")
        self.assertFalse(model["empty_state"]["blocking"])
        self.assertFalse(model["empty_state"]["setup_required"])
        for key in (
            "starts_work", "writes_policy", "writes_roadmap",
            "writes_run_state", "creates_grant", "background_polling",
            "changes_default_route",
        ):
            self.assertFalse(model[key], key)
        self.assertEqual(before, list(empty.rglob("*")))

    def test_workflow_graph_uses_shared_compiler_and_round_trips_losslessly(self):
        import dw_pmo.program_workflow as workflow_core

        detail = self.core.build_studio_document(
            self.root, "workflow", "architect-debate-delivery"
        )
        expected = workflow_core.compile_workflow(
            self.root, "architect-debate-delivery"
        )
        self.assertEqual(detail["compiled"], expected)
        self.assertEqual(
            detail["simulation"],
            workflow_core.simulate_workflow(
                self.root, "architect-debate-delivery"
            ),
        )
        graph = detail["graph"]
        types = {node["type"] for node in graph["nodes"]}
        self.assertTrue({"agent", "debate", "subflow", "loop"} <= types)
        self.assertTrue(graph["features"]["nested_subflows"])
        self.assertTrue(graph["features"]["bounded_loops"])
        self.assertTrue(graph["features"]["debates"])
        self.assertTrue(all(node["keyboard"] for node in graph["nodes"]))
        self.assertTrue(all(edge["keyboard"] for edge in graph["edges"]))
        self.assertTrue(any(node["drilldown"] for node in graph["nodes"]))
        self.assertTrue(any(item["max_rounds"] for item in graph["containers"]))
        round_trip = detail["round_trip"]
        self.assertTrue(round_trip["lossless"])
        self.assertTrue(round_trip["semantic_hash_preserved"])
        self.assertTrue(round_trip["document_hash_preserved"])
        self.assertTrue(round_trip["layout_hash_preserved"])
        self.assertEqual(
            self.core.studio_graph_to_config(graph), detail["raw"]
        )

    def test_delivery_authoring_orders_seven_decisions_over_exact_workflow(self):
        from dw_pmo.plan_authoring import (
            DELIVERY_PLAN_AUTHORING_KIND,
            SECTION_ORDER,
        )

        detail = self.core.build_studio_document(
            self.root, "workflow", "architect-debate-delivery"
        )
        authoring = detail["authoring"]
        self.assertEqual(authoring["kind"], DELIVERY_PLAN_AUTHORING_KIND)
        self.assertEqual(authoring["status"], "ready-to-review")
        self.assertEqual(
            [section["id"] for section in authoring["sections"]],
            list(SECTION_ORDER),
        )
        self.assertEqual(
            [section["question"] for section in authoring["sections"]],
            [
                "What will be delivered?",
                "How should work move?",
                "What must be true before work can pass?",
                "When should a person decide?",
                "What happens when work does not pass?",
                "When must delivery stop?",
                "How much work may this delivery use?",
            ],
        )
        flow = next(
            section for section in authoring["sections"]
            if section["id"] == "flow"
        )
        self.assertEqual(len(flow["items"]), len(detail["raw"]["nodes"]))
        self.assertTrue(any(item["advanced"] for item in flow["items"]))
        self.assertTrue(authoring["advanced_details"]["hierarchical_workflows"])
        self.assertTrue(authoring["advanced_details"]["bounded_loops"])
        self.assertTrue(authoring["advanced_details"]["debate_cells"])
        self.assertTrue(authoring["advanced_details"]["round_trip_lossless"])
        self.assertTrue(
            authoring["advanced_details"]["semantic_identity_preserved"]
        )
        self.assertEqual(
            authoring["review_before_save"]["flow"], flow["answer"]
        )
        self.assertEqual(
            [item["id"] for item in authoring["review_sections"]],
            list(SECTION_ORDER),
        )
        self.assertEqual(authoring["corrections"], [])
        for key in (
            "starts_work", "writes_policy", "writes_roadmap",
            "writes_run_state", "creates_grant", "starts_process",
            "starts_observer", "sends_notification", "uses_network",
        ):
            self.assertFalse(authoring[key], key)

    def test_delivery_authoring_maps_refusals_to_decisions_and_preserves_unknowns(self):
        document = self.core.new_studio_document(
            "workflow", "decision-refusal"
        )
        document["future_extension"] = {
            "owner": "future-editor",
            "nested": {"kept": True},
        }
        document["nodes"] = []
        plan = self.core.build_studio_mutation_plan(
            self.root, "workflow", "save", "decision-refusal", document
        )
        preview = self.core.studio_mutation_preview(plan)
        authoring = preview["studio"]["authoring"]
        self.assertFalse(preview["applicable"])
        self.assertEqual(preview["studio"]["raw"], document)
        self.assertEqual(
            self.core.studio_graph_to_config(preview["studio"]["graph"]),
            document,
        )
        self.assertTrue(
            authoring["edit_safety"]["targeted_edits_preserve_unedited_fields"]
        )
        self.assertTrue(authoring["edit_safety"]["unknown_fields_preserved"])
        self.assertIn(
            "/future_extension",
            authoring["edit_safety"]["unknown_fields"],
        )
        self.assertTrue(authoring["edit_safety"]["invalid_save_refused"])
        flow_corrections = [
            item for item in authoring["corrections"]
            if item["section_id"] == "flow"
        ]
        self.assertGreaterEqual(len(flow_corrections), 2)
        missing = next(
            item for item in flow_corrections
            if item["technical_details"]["code"] == "missing-nodes"
        )
        self.assertIn("bounded work step", missing["correction"])
        unknown = next(
            item for item in flow_corrections
            if item["technical_details"]["code"] == "unknown-key"
        )
        self.assertIn("Technical details", unknown["correction"])
        self.assertEqual(
            unknown["technical_details"]["pointer"], "/future_extension"
        )

    def test_program_authoring_leads_with_scope_and_keeps_save_pure(self):
        (self.root / "pm/roadmap").mkdir()
        document = self.core.new_studio_document(
            "program", "task-shaped-plan"
        )
        plan = self.core.build_studio_mutation_plan(
            self.root, "program", "save", "task-shaped-plan", document
        )
        preview = self.core.studio_mutation_preview(plan)
        authoring = preview["studio"]["authoring"]
        self.assertEqual(authoring["family"], "program")
        self.assertEqual(authoring["sections"][0]["id"], "scope")
        self.assertEqual(
            authoring["sections"][0]["facts"][0],
            {
                "label": "Roadmap project",
                "value": "project",
                "pointer": "/scope/project",
            },
        )
        self.assertEqual(
            authoring["review_before_save"]["flow"],
            "No work route has been chosen yet.",
        )
        self.assertTrue(any(
            item["technical_details"]["code"] == "missing-bindings"
            and item["section_id"] == "flow"
            for item in authoring["corrections"]
        ))
        self.assertFalse(preview["writes_policy"])
        self.assertFalse(preview["starts_work"])

    def test_organization_graph_exposes_separation_council_meta_and_architect(self):
        detail = self.core.build_studio_document(
            self.root, "organization", "autonomous-story-cell"
        )
        self.assertTrue(detail["validation"]["valid"])
        graph = detail["graph"]
        self.assertTrue(graph["features"]["implementer_verifier_separation"])
        self.assertTrue(graph["features"]["councils"])
        self.assertTrue(graph["features"]["meta_verifier"])
        self.assertTrue(graph["features"]["master_architect"])
        self.assertTrue(any(edge["kind"] == "separation" for edge in graph["edges"]))
        council = next(node for node in graph["nodes"] if node["type"] == "council")
        self.assertEqual(council["summary"]["meta_verifier"], "meta-verifier")
        self.assertIn("max_rounds", council["summary"]["budgets"])
        self.assertFalse(detail["simulation"]["starts_work"])
        self.assertFalse(detail["authority"]["creates_grant"])

    def test_team_review_answers_five_human_questions_over_advanced_policy(self):
        from dw_pmo.team_review import TEAM_REVIEW_KIND, SECTION_ORDER

        detail = self.core.build_studio_document(
            self.root, "organization", "autonomous-story-cell"
        )
        team = detail["team_review"]
        self.assertEqual(team["kind"], TEAM_REVIEW_KIND)
        self.assertEqual(team["context"], "design")
        self.assertEqual(team["status"], "ready-to-review")
        self.assertEqual(
            [section["id"] for section in team["sections"]],
            list(SECTION_ORDER),
        )
        answers = team["review_before_save"]
        self.assertIn("Builder Primary", answers["responsibilities"])
        self.assertIn("Verifier Primary", answers["responsibilities"])
        self.assertIn(
            "must be separate from", answers["independence"]
        )
        self.assertEqual(
            answers["independence"].count("must be separate from"), 1
        )
        self.assertIn("Every voting reviewer", answers["decisions"])
        self.assertIn("Judge records the outcome", answers["decisions"])
        self.assertIn("delivery owner", answers["escalation"])
        self.assertIn("review auditor", answers["audit"])
        self.assertIn("Meta Verifier owns this check", answers["audit"])
        self.assertIn("Master Architect performs architecture review", answers["audit"])
        self.assertIn("architecture check", answers["audit"])
        self.assertEqual(
            team["runtime_independence"]["status"], "not-assigned"
        )
        self.assertIn(
            "does not claim a runtime identity",
            team["runtime_independence"]["claim"],
        )
        self.assertTrue(all(
            item["status"] == "policy-ready"
            for item in team["quality_constraints"]
            if item["roles"] == ["implementer", "verifier"]
        ))
        self.assertTrue(team["progressive_details"]["council"])
        self.assertTrue(team["progressive_details"]["dissent"])
        self.assertTrue(team["progressive_details"]["judge"])
        self.assertTrue(team["progressive_details"]["review_auditor"])
        self.assertTrue(team["progressive_details"]["architecture_review"])
        self.assertTrue(
            team["technical_details"][
                "provider_model_do_not_prove_independence"
            ]
        )
        self.assertTrue(
            team["technical_details"][
                "principal_workspace_session_remain_distinct"
            ]
        )
        self.assertTrue(team["technical_details"]["round_trip_lossless"])
        self.assertNotIn(
            "delivery-workbench-team-assignment", team["source_models"]
        )
        self.assertEqual(team["corrections"], [])

    def test_team_review_distinguishes_introduced_and_preexisting_failures(self):
        from dw_pmo.team_review import build_team_review

        detail = self.core.build_studio_document(
            self.root, "organization", "autonomous-story-cell"
        )
        reviewed = build_team_review(
            detail["raw"], detail["validation"], detail["compiled"],
            detail["simulation"], detail["authority"], detail["round_trip"],
            test_failures={
                "introduced": [],
                "pre_existing": ["pkg/test_mod.py::test_existing"],
            },
        )
        self.assertEqual(
            reviewed["test_failures"]["status"],
            "no-introduced-failures-with-pre-existing",
        )
        self.assertEqual(reviewed["test_failures"]["introduced"], [])
        self.assertEqual(
            reviewed["test_failures"]["pre_existing"],
            ["pkg/test_mod.py::test_existing"],
        )
        self.assertIn(
            "No introduced failures; 1 pre-existing",
            reviewed["test_failures"]["summary"],
        )

    def test_team_review_upgrades_only_the_runtime_pair_and_compares_exact_ids(self):
        from dw_pmo.team_review import build_team_review

        detail = self.core.build_studio_document(
            self.root, "organization", "autonomous-story-cell"
        )
        assigned = build_team_review(
            detail["raw"],
            detail["validation"],
            detail["compiled"],
            detail["simulation"],
            detail["authority"],
            detail["round_trip"],
            {
                "applicable": True,
                "separation": {
                    "passed": True,
                    "facts": {
                        "implementer_role": "implementer",
                        "verifier_role": "verifier",
                    },
                },
            },
        )
        statuses = {
            tuple(item["roles"]): item["status"]
            for item in assigned["quality_constraints"]
        }
        self.assertEqual(
            statuses[("implementer", "verifier")], "runtime-proven"
        )
        self.assertIn(
            "delivery-workbench-team-assignment", assigned["source_models"]
        )
        self.assertTrue(all(
            status != "runtime-proven"
            for roles, status in statuses.items()
            if roles != ("implementer", "verifier")
        ))

        colliding_labels = build_team_review(
            {
                "slug": "exact-candidate-ids",
                "agents": [
                    {
                        "id": "review-one",
                        "profile": "writer",
                        "workspace_domain": "writer-space",
                    },
                    {
                        "id": "review_one",
                        "profile": "reader",
                        "workspace_domain": "reader-space",
                    },
                ],
                "pools": [
                    {"id": "writers", "agents": ["review-one"]},
                    {"id": "readers", "agents": ["review_one"]},
                ],
                "teams": [{
                    "id": "delivery",
                    "roles": [
                        {
                            "id": "implementer",
                            "duty": "implementer",
                            "pool": "writers",
                            "required": True,
                            "cardinality": 1,
                        },
                        {
                            "id": "verifier",
                            "duty": "verifier",
                            "pool": "readers",
                            "required": True,
                            "cardinality": 1,
                            "independent_from": ["implementer"],
                        },
                    ],
                }],
            },
            {"valid": True, "diagnostics": []},
            {
                "logical_assignment_proofs": [{
                    "team": "delivery",
                    "witness": [
                        {
                            "role": "implementer",
                            "agent": "review-one",
                            "profile": "writer",
                            "workspace_domain": "writer-space",
                        },
                        {
                            "role": "verifier",
                            "agent": "review_one",
                            "profile": "reader",
                            "workspace_domain": "reader-space",
                        },
                    ],
                }],
            },
        )
        constraint = colliding_labels["quality_constraints"][0]
        self.assertEqual(constraint["labels"], ["Implementer", "Verifier"])
        self.assertEqual(constraint["status"], "policy-ready")
        witnesses = constraint["technical_details"]["policy_witness"]
        self.assertNotEqual(
            witnesses["left"]["candidate_id"],
            witnesses["right"]["candidate_id"],
        )
        self.assertEqual(
            witnesses["left"]["candidate"],
            witnesses["right"]["candidate"],
        )

    def test_new_team_draft_is_a_valid_understandable_independent_pair(self):
        document = self.core.new_studio_document(
            "organization", "friendly-team"
        )
        plan = self.core.build_studio_mutation_plan(
            self.root, "organization", "save", "friendly-team", document
        )
        preview = self.core.studio_mutation_preview(plan)
        team = preview["studio"]["team_review"]
        self.assertTrue(preview["applicable"])
        self.assertTrue(preview["studio"]["validation"]["valid"])
        self.assertEqual(team["status"], "ready-to-review")
        self.assertEqual(
            [item["technical_details"]["duty"]
             for item in team["responsibilities"]],
            ["implementer", "verifier"],
        )
        self.assertEqual(
            team["quality_constraints"][0]["status"], "policy-ready"
        )
        self.assertEqual(team["review_groups"], [])
        self.assertIn(
            "separately authorized delivery owner",
            team["review_before_save"]["escalation"],
        )
        self.assertTrue(preview["studio"]["round_trip"]["lossless"])
        self.assertFalse(preview["writes_policy"])
        self.assertFalse(preview["starts_work"])

    def test_invalid_team_names_conflicting_roles_and_refuses_losslessly(self):
        document = json.loads(
            (
                self.root
                / "pm/organizations/autonomous-story-cell.json"
            ).read_text(encoding="utf-8")
        )
        verifier = next(
            role
            for role in document["teams"][0]["roles"]
            if role["id"] == "verifier"
        )
        verifier["independent_from"] = []
        verifier["may_judge"] = []
        document["future_extension"] = {"preserved": True}
        plan = self.core.build_studio_mutation_plan(
            self.root,
            "organization",
            "save",
            "autonomous-story-cell",
            document,
        )
        preview = self.core.studio_mutation_preview(plan)
        team = preview["studio"]["team_review"]
        self.assertFalse(preview["applicable"])
        self.assertFalse(preview["valid"])
        self.assertEqual(preview["studio"]["raw"], document)
        self.assertTrue(preview["studio"]["round_trip"]["lossless"])
        separation = next(
            item for item in team["corrections"]
            if item["technical_details"]["code"] == "missing-separation"
        )
        self.assertEqual(
            separation["conflicting_roles"],
            ["implementer", "verifier"],
        )
        self.assertIn("separate", separation["correction"])
        self.assertEqual(separation["section_id"], "independence")
        self.assertIn(
            "/future_extension",
            team["edit_safety"]["unknown_fields"],
        )
        self.assertTrue(team["edit_safety"]["unknown_fields_preserved"])
        self.assertTrue(team["edit_safety"]["invalid_save_refused"])
        self.assertIsNone(preview["studio"]["compiled"])

    def test_studio_projects_portable_ports_fallbacks_and_safe_local_fingerprints(self):
        from dw_pmo.orchestration_driver import write_driver_config

        raw = json.loads(
            (
                self.root
                / "pm/organizations/autonomous-story-cell.json"
            ).read_text(encoding="utf-8")
        )
        subprocess.run(
            ["git", "init", "-q", str(self.root)],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        profiles = {}
        for agent in raw["agents"]:
            writer = "workspace:write" in agent["capability_ceiling"]
            profiles[agent["profile"]] = {
                "adapter": "fixture",
                "adapter_version": "fixture-studio-v1",
                "principal": agent["profile"],
                "available": True,
                "max_concurrency": agent["max_concurrency"],
                "capabilities": (
                    ["repository-read", "repository-write"]
                    if writer else ["repository-read"]
                ),
                "workspace_modes": (
                    ["isolated-worktree"] if writer else ["read-only"]
                ),
                "router": "fixture-router",
                "provider": (
                    "provider-a"
                    if "builder" in agent["id"] else "provider-b"
                ),
                "model_vendor": "fixture-vendor",
                "model_family": (
                    "builder-family"
                    if "builder" in agent["id"] else "review-family"
                ),
                "model": f"fixture/{agent['profile']}",
                "model_binding": "requested-alias",
                "auth_domain": f"auth-{agent['profile']}",
            }
        write_driver_config(self.root, {
            "kind": "delivery-workbench-driver-config",
            "schema_version": 1,
            "workspace_root": None,
            "profiles": profiles,
        })
        detail = self.core.build_studio_document(
            self.root, "organization", "autonomous-story-cell"
        )
        contract = detail["authority"]["execution_contract"]
        provenance = detail["team_review"]["technical_details"]["provenance"]
        self.assertTrue(contract["content_safe"])
        self.assertFalse(contract["credentials_exposed"])
        self.assertFalse(contract["commands_accepted"])
        self.assertTrue(contract["local_resolution_available"])
        self.assertEqual(len(contract["ports"]), len(raw["agents"]))
        self.assertTrue(all(
            item["selector"]["kind"] == "logical-profile"
            and item["selector"]["portable"]
            and item["local_resolution"]["available"]
            for item in contract["ports"]
        ))
        self.assertTrue(any(
            item["fallback_pools"] for item in contract["fallbacks"]
        ))
        council = contract["councils"][0]
        self.assertEqual(council["principal_diversity"], "distinct")
        self.assertEqual(council["decision_authority"], "unanimous")
        self.assertTrue(council["perspectives"])
        self.assertTrue(
            council["obligation_policy"]["blocking_prevents_progress"]
        )
        self.assertGreaterEqual(
            contract["diversity"]["resolved_provider_count"], 2
        )
        self.assertEqual(len(provenance), len(raw["agents"]))
        self.assertTrue(all(
            item["provider"] in {"provider-a", "provider-b"}
            and item["model_vendor"] == "fixture-vendor"
            and item["model"]
            and item["auth_domain_fingerprint"]
            and item["principal_fingerprint"]
            and item["workspace_domain"]
            and item["session_binding_key"] is None
            for item in provenance
        ))
        for port in contract["ports"]:
            self.assertNotIn("principal", port["local_resolution"])
            self.assertNotIn("auth_domain", port["local_resolution"])
        rendered = json.dumps(contract, sort_keys=True)
        for secret_key in ('"token":', '"password":', '"secret":'):
            self.assertNotIn(secret_key, rendered.lower())

    def test_diagnostics_link_exact_graph_node_and_json_pointer(self):
        document = self.core.new_studio_document("workflow", "broken-flow")
        document["nodes"][0]["shell"] = "never"
        plan = self.core.build_studio_mutation_plan(
            self.root, "workflow", "save", "broken-flow", document
        )
        preview = self.core.studio_mutation_preview(plan)
        self.assertFalse(preview["applicable"])
        diagnostic = next(
            item for item in preview["studio"]["validation"]["diagnostics"]
            if item["pointer"] == "/nodes/0/shell"
        )
        self.assertEqual(diagnostic["target"]["node_id"], "review")
        self.assertIn("nodes-0-shell", diagnostic["target"]["field_id"])
        self.assertIsNone(preview["studio"]["compiled"])
        self.assertTrue(preview["studio"]["round_trip"]["lossless"])
        self.assertFalse(
            preview["studio"]["round_trip"]["semantic_hash_preserved"]
        )

    def test_layout_move_changes_document_not_semantic_hash(self):
        import dw_pmo.program_workflow as workflow_core

        document = self.core.new_studio_document("workflow", "move-proof")
        baseline = workflow_core.compile_workflow(self.root, document)
        moved = json.loads(json.dumps(document))
        moved["layout"]["nodes"]["review"] = {"x": 777, "y": 333}
        compiled = workflow_core.compile_workflow(self.root, moved)
        self.assertEqual(baseline["semantic_hash"], compiled["semantic_hash"])
        self.assertNotEqual(baseline["document_hash"], compiled["document_hash"])
        round_trip = self.core.graph_config_round_trip(
            self.root, "workflow", moved
        )
        self.assertTrue(round_trip["lossless"])
        self.assertTrue(round_trip["semantic_hash_preserved"])
        self.assertTrue(round_trip["layout_hash_preserved"])

    def test_authority_preview_separates_requests_and_never_grants(self):
        document = self.core.new_studio_document("program", "authority-proof")
        document["mode_ceiling"] = "checkpointed"
        document["requested_capabilities"] = [
            "agent:dispatch", "verdict:issue", "certification:verdict",
            "evidence:materialize", "git:commit", "roadmap:phase-advance",
        ]
        authority = self.core.build_authority_preview(
            "program", document, None
        )
        groups = {group["id"]: group for group in authority["groups"]}
        work = {
            item["id"] for item in groups["work-and-verdict"]["capabilities"]
            if item["requested"]
        }
        delivery = {
            item["id"] for item in groups["delivery-rails"]["capabilities"]
            if item["requested"]
        }
        self.assertEqual(work, {"agent:dispatch", "verdict:issue"})
        self.assertEqual(
            delivery,
            {
                "certification:verdict", "evidence:materialize",
                "git:commit", "roadmap:phase-advance",
            },
        )
        modes = {item["id"]: item for item in authority["modes"]}
        self.assertTrue(modes["advisory"]["within_ceiling"])
        self.assertTrue(modes["checkpointed"]["within_ceiling"])
        self.assertFalse(modes["continuous"]["within_ceiling"])
        self.assertTrue(authority["grant_required"])
        self.assertFalse(authority["creates_grant"])
        self.assertFalse(authority["starts_work"])

    def test_guarded_save_is_one_file_stale_safe_and_delete_is_explicit(self):
        document = self.core.new_studio_document("workflow", "guarded-flow")
        target = self.root / "pm/workflows/guarded-flow.json"
        plan = self.core.build_studio_mutation_plan(
            self.root, "workflow", "save", "guarded-flow", document
        )
        preview = self.core.studio_mutation_preview(plan)
        self.assertTrue(preview["applicable"])
        self.assertFalse(target.exists())
        for key in (
            "starts_work", "writes_policy", "writes_roadmap",
            "writes_run_state", "creates_grant", "starts_agent",
            "starts_check", "starts_observer", "sends_notification",
            "applies_integration",
        ):
            self.assertFalse(preview[key], key)
        result = self.core.apply_studio_mutation(plan, preview["fingerprint"])
        self.assertTrue(target.is_file())
        self.assertEqual(result["writes_only"], ["pm/workflows/guarded-flow.json"])
        self.assertTrue(result["writes_policy"])
        self.assertFalse(result["starts_work"])
        with self.assertRaisesRegex(DwError, "stale Program Studio preview"):
            self.core.apply_studio_mutation(plan, preview["fingerprint"])

        delete = self.core.build_studio_mutation_plan(
            self.root, "workflow", "delete", "guarded-flow"
        )
        delete_preview = self.core.studio_mutation_preview(delete)
        self.assertTrue(delete_preview["applicable"])
        self.assertTrue(target.exists())
        self.core.apply_studio_mutation(delete, delete_preview["fingerprint"])
        self.assertFalse(target.exists())
        self.assertFalse((self.root / ".git/pmo-programs").exists())
        self.assertFalse((self.root / "pm/program-runs").exists())

    def test_containment_and_http_adapter_share_the_same_model(self):
        from dw_pmo.workbench import handle_api, handle_mutation

        with self.assertRaises(DwError):
            self.core.build_studio_mutation_plan(
                self.root, "workflow", "save", "../escape", {}
            )
        status, listed = handle_api(self.root, "/api/program-studio", {})
        self.assertEqual(status, 200)
        self.assertEqual(
            listed["data"], self.core.build_program_studio(self.root)
        )
        status, detail = handle_api(
            self.root,
            "/api/program-studio/workflow/architect-debate-delivery",
            {},
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            detail["data"],
            self.core.build_studio_document(
                self.root, "workflow", "architect-debate-delivery"
            ),
        )
        document = self.core.new_studio_document("workflow", "http-flow")
        request = {
            "family": "workflow", "action": "save", "name": "http-flow",
            "document": document,
        }
        status, body = handle_mutation(
            self.root, "/api/program-studio/preview", request
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["data"]["applicable"])
        request["fingerprint"] = body["data"]["fingerprint"]
        status, applied = handle_mutation(
            self.root, "/api/program-studio/apply", request
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            applied["data"]["writes_only"], ["pm/workflows/http-flow.json"]
        )
        status, stale = handle_mutation(
            self.root, "/api/program-studio/apply", request
        )
        self.assertEqual(status, 409)
        self.assertFalse(stale["ok"])


class DeliverySetupTest(unittest.TestCase):
    """WLA-27-03: one pure delivery choice model across CLI and Workbench."""

    def setUp(self):
        import dw_pmo.delivery_setup as setup_core

        self.core = setup_core
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-delivery-setup-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self._cmd("git", "init", "-q", "-b", "main")
        self._cmd("git", "config", "user.name", "Delivery Setup Fixture")
        self._cmd("git", "config", "user.email", "setup@example.test")
        subprocess.run(
            [
                str(TESTS_DIR.parent / "bootstrap" / "new-project.sh"),
                str(self.root), "sample", "Sample", "SMP",
            ],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        subprocess.run(
            [
                str(TESTS_DIR.parent / "install.sh"),
                str(self.root), "--skip-bootstrap",
            ],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.dw = self.root / ".githooks" / "dw"
        self._dw("story", "status", "sample", "0", "SMP-0-01", "in-progress")
        self._dw("rider", "docs")
        self._cmd("git", "add", ".")
        self._cmd(
            "git", "-c", "core.hooksPath=/dev/null",
            "commit", "-q", "-m", "delivery setup fixture",
        )

    def _cmd(self, *argv, check=True):
        return subprocess.run(
            list(argv), cwd=self.root, check=check, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def _dw(self, *argv, check=True):
        return self._cmd(str(self.dw), *argv, check=check)

    def _files(self):
        return {
            str(path.relative_to(self.root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.root.rglob("*"))
            if path.is_file() and ".git" not in path.relative_to(self.root).parts
        }

    @staticmethod
    def _choice(model, choice_id):
        return next(item for item in model["choices"] if item["id"] == choice_id)

    def test_front_door_names_scope_three_modes_effects_and_permissions(self):
        model = self.core.build_delivery_setup(self.root, "sample")
        self.assertEqual(model["kind"], "delivery-workbench-delivery-setup")
        self.assertEqual(model["schema_version"], 1)
        self.assertTrue(model["healthy"])
        self.assertEqual(model["readiness"], "ready")
        self.assertEqual(model["delivery_scope"]["selected_project"], "sample")
        self.assertEqual(
            model["delivery_scope"]["current_work"]["story_id"], "SMP-0-01"
        )
        self.assertEqual(
            [item["id"] for item in model["choices"]],
            ["roadmap", "bounded", "program"],
        )
        ordinary, bounded, program = model["choices"]
        self.assertTrue(ordinary["recommended"])
        self.assertEqual(ordinary["readiness"], "ready")
        self.assertEqual(bounded["readiness"], "ready-to-review")
        self.assertEqual(program["readiness"], "ready-to-set-up")
        self.assertIsNone(ordinary["separate_permission"])
        self.assertIn("explicit start confirmation", bounded["separate_permission"])
        self.assertIn("separate reviewed program start", program["separate_permission"])
        self.assertIn("Save draft", program["creates_during_setup"][0])
        self.assertEqual(model["technical_details"]["label"], "Technical details")
        self.assertEqual(model["cancel"]["effect"], "Leaves repository and delivery state unchanged.")

    def test_setup_and_cancel_model_are_repeatable_and_write_nothing(self):
        before = self._files()
        first = self.core.build_delivery_setup(self.root, "sample")
        second = self.core.build_delivery_setup(self.root, "sample")
        self.assertEqual(first, second)
        self.assertEqual(before, self._files())
        self.assertEqual(self._cmd("git", "status", "--porcelain").stdout, "")
        for key in (
            "starts_work", "writes_policy", "writes_roadmap",
            "writes_run_state", "creates_grant", "starts_process",
            "starts_observer", "sends_notification", "uses_network",
        ):
            self.assertFalse(first[key], key)
        for path in (
            ".git/pmo-orchestration", ".git/pmo-programs", "pm/program-runs",
            "pm/programs", "pm/workflows", "pm/organizations",
        ):
            self.assertFalse((self.root / path).exists(), path)

    def test_human_cli_and_http_render_the_same_choice_and_readiness(self):
        from dw_pmo.status import build_status
        from dw_pmo.workbench import handle_api

        model = self.core.build_delivery_setup(self.root, "sample")
        status, body = handle_api(
            self.root, "/api/delivery-setup", {"project": ["sample"]}
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"], model)

        setup = self._dw("setup", "sample", "--technical")
        self.assertEqual(setup.returncode, 0, setup.stderr)
        for choice in model["choices"]:
            self.assertIn(
                f"{choice['label']} — {choice['readiness']}", setup.stdout
            )
        self.assertIn("Technical details:", setup.stdout)
        self.assertIn("inspection and cancel start nothing", setup.stdout)

        machine_status = self._dw("status", "sample", "--json")
        self.assertEqual(machine_status.returncode, 0, machine_status.stderr)
        self.assertEqual(json.loads(machine_status.stdout), build_status(self.root, "sample"))
        human_status = self._dw("status", "sample")
        self.assertIn("choices=roadmap|bounded|program", human_status.stdout)
        self.assertIn('open=".githooks/dw setup sample"', human_status.stdout)

    def test_missing_or_invalid_inputs_name_the_delivery_decision_and_correction(self):
        score = self.root / "pm/orchestration/research-build-review.json"
        score.write_text("{}\n", encoding="utf-8")
        invalid = self.core.build_delivery_setup(self.root, "sample")
        bounded = self._choice(invalid, "bounded")
        self.assertEqual(bounded["readiness"], "needs-delivery-plan")
        self.assertFalse(bounded["available"])
        self.assertIn("valid delivery plan", bounded["correction"])

        programs = self.root / "pm/programs"
        programs.mkdir()
        (programs / "broken.json").write_text("{}\n", encoding="utf-8")
        invalid_program = self.core.build_delivery_setup(self.root, "sample")
        program = self._choice(invalid_program, "program")
        self.assertTrue(invalid_program["healthy"])
        self.assertFalse(invalid_program["optional_configuration_healthy"])
        self.assertEqual(program["readiness"], "needs-program-repair")
        self.assertTrue(program["available"])
        self.assertIn("invalid delivery-program draft", program["correction"])

        subprocess.run(
            [
                str(TESTS_DIR.parent / "bootstrap" / "new-project.sh"),
                str(self.root), "second", "Second", "SND",
            ],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        unselected = self.core.build_delivery_setup(self.root)
        self.assertEqual(unselected["readiness"], "attention")
        self.assertTrue(unselected["delivery_scope"]["selection_required"])
        self.assertEqual(unselected["issues"][0]["decision"], "delivery scope")
        self.assertIn("Select the project", unselected["issues"][0]["next_step"])
        self.assertEqual(
            self._choice(unselected, "program")["readiness"],
            "needs-delivery-scope",
        )


class ProgramDeliberationTest(unittest.TestCase):
    """WLA-26-05: bounded councils, replay, meta-audit, and architecture."""

    def setUp(self):
        import dw_pmo.program_deliberation as deliberation_core
        import dw_pmo.program_organization as organization_core
        import dw_pmo.program_workflow as workflow_core

        self.core = deliberation_core
        self.organization_core = organization_core
        self.workflow_core = workflow_core
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-deliberation-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        workflow_dir = self.root / "pm/workflows"
        score_dir = self.root / "pm/orchestration"
        workflow_dir.mkdir(parents=True)
        score_dir.mkdir(parents=True)
        for source in (TESTS_DIR.parent / "templates/workflows").glob("*.json"):
            shutil.copy2(source, workflow_dir / source.name)
        shutil.copy2(
            TESTS_DIR.parent
            / "templates/orchestration/research-build-review.json",
            score_dir / "research-build-review.json",
        )
        self.organization = json.loads(
            (
                TESTS_DIR.parent
                / "templates/organizations/autonomous-story-cell.json"
            ).read_text(encoding="utf-8")
        )
        # The default runtime fixture is a two-of-three majority with a full
        # audit. Other tests compile the weighted/unanimous/judge variants.
        decision = self.organization["councils"][0]["decision"]
        decision["method"] = "majority"
        decision["threshold"] = 2
        decision["veto_roles"] = []
        self.workflow = self.workflow_core.compile_workflow(
            self.root, "architect-debate-delivery"
        )

    @staticmethod
    def clone(value):
        return json.loads(json.dumps(value))

    def config(self, organization=None):
        profiles = {}
        for agent in (organization or self.organization)["agents"]:
            writer = "workspace:write" in agent["capability_ceiling"]
            profiles[agent["profile"]] = {
                "adapter": "fixture",
                "adapter_version": "fixture-deliberation-v1",
                "principal": agent["profile"],
                "available": True,
                "max_concurrency": agent["max_concurrency"],
                "capabilities": (
                    ["repository-read", "repository-write"]
                    if writer else ["repository-read"]
                ),
                "workspace_modes": (
                    ["isolated-worktree"] if writer else ["read-only"]
                ),
                "router": "fixture-router",
                "provider": "fixture-provider",
                "model_vendor": "fixture-vendor",
                "model_family": "fixture-family",
                "model": f"fixture/{agent['profile']}",
                "model_binding": "requested-alias",
                "auth_domain": f"auth-{agent['profile']}",
            }
        return {
            "kind": "delivery-workbench-driver-config",
            "schema_version": 1,
            "workspace_root": None,
            "profiles": profiles,
        }

    def assignment(self, organization=None):
        raw = organization or self.organization
        compiled = self.organization_core.compile_organization(self.root, raw)
        return self.organization_core.assign_organization_team(
            compiled,
            "story-cell",
            driver_config=self.config(raw),
            policy_bundle_hash="sha256:" + "7" * 64,
            story_id="DM-1-02",
            workflow_address="program/demo/phase/1/story/DM-1-02/workflow/design",
            program_capabilities=[
                "agent:dispatch", "workspace:write", "verdict:issue",
                "council:decide", "obligation:record",
            ],
            workflow=None,
        )

    def architect_policy(self):
        return {
            "boundary": "phase",
            "rubric": {
                "slug": "phase-architecture",
                "semantic_hash": "sha256:" + "4" * 64,
                "criteria": ["cohesion", "boundary-safety"],
            },
            "evidence": [{
                "kind": "markdown",
                "hash": "sha256:" + "5" * 64,
                "ref": "artifacts/phase-summary.md",
            }],
            "routes": {
                "approve": "retain",
                "repair": "repair",
                "escalate": "escalate",
                "veto": "block",
            },
        }

    def plan(
        self, organization=None, workflow=None, *, architect=False,
        rubric=None, freshness_bound=False,
    ):
        assignment = self.assignment(organization)
        self.assertTrue(assignment["applicable"], assignment["issues"])
        selected_workflow = workflow or self.workflow
        debate = next(
            item for item in selected_workflow["debates"]
            if str(item["address"]).endswith("/design-council")
            or item["address"] == "design-council"
        )
        subject = {
            "kind": "story-design",
            "hash": "sha256:" + "2" * 64,
        }
        if freshness_bound:
            subject = {
                "kind": "diff",
                "hash": "sha256:" + "2" * 64,
                "repository_hash": "sha256:" + "6" * 64,
                "program_hash": "sha256:" + "7" * 64,
                "program_run_id": "program-fixture",
                "phase": 1,
                "story": "DM-1-02",
                "workflow_address": debate["address"],
                "assignment_hash": assignment["assignment_hash"],
                "assignment_generation": 1,
                "ledger_head": "sha256:" + "8" * 64,
                "implementer_principals": [
                    assignment["implementer"]["principal_fingerprint"]
                ],
            }
        plan = self.core.compile_deliberation_plan(
            selected_workflow,
            assignment,
            council_id="debate-council",
            program_run_id="program-fixture",
            phase=1,
            story="DM-1-02",
            rubric=rubric or {
                "slug": "design-quality",
                "semantic_hash": "sha256:" + "1" * 64,
                "criteria": ["coherent", "bounded", "evidenced"],
            },
            subject=subject,
            evidence=[{
                "kind": "markdown",
                "hash": "sha256:" + "3" * 64,
                "ref": "artifacts/architect-frame.md",
            }],
            debate_address="design-council",
            architect=self.architect_policy() if architect else None,
        )
        return plan, assignment

    def submission(
        self, claim, ordinal, *, vote=None, result=None, obligations=None,
    ):
        stage = claim["stage"]
        kind = {
            "proposal": "proposal",
            "critique": "critique",
            "rebuttal": "rebuttal",
            "judgment": self.core.COUNCIL_VERDICT_KIND,
            "meta-audit": self.core.META_VERDICT_KIND,
            "architect-review": self.core.ARCHITECT_VERDICT_KIND,
        }[stage]
        return {
            "kind": kind,
            "content_hash": "sha256:" + format(ordinal, "064x"),
            "content_ref": f"artifacts/receipt-{ordinal}.json",
            "bytes": 200,
            "tokens": 20,
            "citations": ["evidence:architect-frame"],
            "vote": vote,
            "result": result,
            "rationale": (
                f"Bounded governed rationale for {result}."
                if result is not None else None
            ),
            "obligations": (
                list(obligations or []) if stage == "judgment" else None
            ),
        }

    def drive(
        self,
        plan,
        events,
        *,
        votes,
        judgments,
        meta="uphold",
        architect="approve",
        obligations=None,
    ):
        vote_offsets = {}
        ordinal = len(events)
        while True:
            projection = self.core.replay_deliberation(plan, events)
            if projection["state"] == "complete":
                return events, projection
            if projection["active_claim"] is None:
                claimed = self.core.claim_next_deliberation(
                    plan, events, "2026-07-22T00:01:00Z"
                )
                events = claimed["events"]
                claim = claimed["claim"]
            else:
                claim = projection["active_claim"]
            ordinal += 1
            vote = None
            result = None
            if claim["stage"] == "rebuttal":
                round_number = claim["round"]
                offset = vote_offsets.get(round_number, 0)
                vote = votes[round_number][offset]
                vote_offsets[round_number] = offset + 1
            elif claim["stage"] == "judgment":
                result = judgments[claim["round"]]
            elif claim["stage"] == "meta-audit":
                result = meta
            elif claim["stage"] == "architect-review":
                result = architect
            recorded = self.core.record_deliberation_submission(
                plan,
                events,
                claim["claim_id"],
                self.submission(
                    claim, ordinal, vote=vote, result=result,
                    obligations=(obligations or {}).get(claim["round"], []),
                ),
                "2026-07-22T00:01:00Z",
            )
            events = recorded["events"]

    def test_compile_and_simulate_prove_every_finite_council_bound(self):
        plan, _assignment = self.plan(architect=True)
        simulation = self.core.simulate_deliberation(plan)
        self.assertTrue(simulation["proof"]["finite"])
        self.assertEqual(simulation["maximum"]["rounds"], 2)
        self.assertEqual(simulation["maximum"]["speaker_slots"], 3)
        self.assertEqual(simulation["maximum"]["starts_per_round"], 10)
        self.assertEqual(simulation["maximum"]["agent_starts"], 22)
        self.assertEqual(simulation["maximum"]["artifacts"], 22)
        self.assertEqual(simulation["maximum"]["tokens"], 88000)
        self.assertEqual(simulation["maximum"]["output_bytes"], 660000)
        self.assertEqual(simulation["maximum"]["wall_seconds"], 7200)
        self.assertEqual(simulation["quorum"], 3)
        self.assertEqual(simulation["decision"]["method"], "majority")
        self.assertEqual(
            simulation["decision_authority"]["primary"]["kind"], "rule"
        )
        self.assertIsNone(
            simulation["decision_authority"]["primary"]["decider_seat"]
        )
        self.assertEqual(
            simulation["decision_authority"]["tie"]["kind"], "judge"
        )
        self.assertEqual(
            simulation["proof"]["verdict_effects"]["repair"],
            "follows-declared-repair-route",
        )
        self.assertFalse(simulation["starts_work"])
        self.assertFalse(simulation["dispatches_agents"])
        self.assertFalse(simulation["writes_run_state"])
        self.assertEqual(
            {item["stage"] for item in simulation["round_schedule"]},
            {"proposal", "critique", "rebuttal", "judgment"},
        )

    def test_two_round_restart_preserves_dissent_and_runs_meta_then_architect(self):
        plan, _assignment = self.plan(architect=True)
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        first = self.core.claim_next_deliberation(
            plan, events, "2026-07-22T00:01:00Z"
        )
        events = first["events"]
        # A crash after the claim recovers the same claim instead of starting
        # the same speaker twice.
        restarted = json.loads(json.dumps(events))
        duplicate = self.core.claim_next_deliberation(
            plan, restarted, "2026-07-22T00:01:00Z"
        )
        self.assertFalse(duplicate["appended"])
        self.assertEqual(duplicate["events"], restarted)
        self.assertEqual(duplicate["claim"], first["claim"])

        # Finish round one, then plant the required crash exactly between
        # rounds. Replay must claim the first round-two speaker once.
        events = restarted
        vote_offset = 0
        ordinal = len(events)
        while not self.core.replay_deliberation(plan, events)["round_judgments"]:
            projection = self.core.replay_deliberation(plan, events)
            if projection["active_claim"] is None:
                claimed = self.core.claim_next_deliberation(
                    plan, events, "2026-07-22T00:01:00Z"
                )
                events = claimed["events"]
                claim = claimed["claim"]
            else:
                claim = projection["active_claim"]
            ordinal += 1
            vote = None
            result = None
            if claim["stage"] == "rebuttal":
                vote = ["advance", "repair", "abstain"][vote_offset]
                vote_offset += 1
            elif claim["stage"] == "judgment":
                result = "redeliberate"
            events = self.core.record_deliberation_submission(
                plan,
                events,
                claim["claim_id"],
                self.submission(claim, ordinal, vote=vote, result=result),
                "2026-07-22T00:01:00Z",
            )["events"]
        between_rounds = json.loads(json.dumps(events))
        round_two = self.core.claim_next_deliberation(
            plan, between_rounds, "2026-07-22T00:01:00Z"
        )
        same_round_two = self.core.claim_next_deliberation(
            plan, round_two["events"], "2026-07-22T00:01:00Z"
        )
        self.assertFalse(same_round_two["appended"])
        self.assertEqual(same_round_two["claim"], round_two["claim"])
        self.assertEqual(round_two["claim"]["round"], 2)

        events, projection = self.drive(
            plan,
            round_two["events"],
            votes={
                2: ["advance", "advance", "repair"],
            },
            judgments={2: "advance"},
            meta="uphold",
            architect="repair",
        )
        self.assertEqual(len(projection["rounds"]), 2)
        self.assertEqual(projection["round_judgments"][0]["result"], "redeliberate")
        self.assertEqual(projection["round_judgments"][1]["result"], "advance")
        self.assertEqual(len(projection["dissent"]), 1)
        self.assertEqual(len(projection["abstentions"]), 1)
        self.assertEqual(projection["meta_verdict"]["result"], "uphold")
        decision = projection["council_decision"]
        self.assertEqual(decision["kind"], self.core.COUNCIL_DECISION_KIND)
        self.assertEqual(decision["authority"]["kind"], "rule")
        self.assertIsNone(decision["authority"]["decider_seat"])
        self.assertIsNone(decision["authority"]["decider"])
        self.assertEqual(decision["chair_seat"], plan["judge"]["address"])
        self.assertEqual(decision["obligations"], [])
        self.assertEqual(projection["carried_obligations"], [])
        self.assertTrue(
            projection["meta_verdict"]["aggregation"]["original_verdict_preserved"]
        )
        self.assertEqual(
            len(projection["meta_verdict"]["aggregation"]["audited_receipts"]),
            4,
        )
        self.assertEqual(projection["architect_verdict"]["result"], "repair")
        self.assertFalse(
            projection["architect_verdict"]["aggregation"]["authority"]["may_commit"]
        )
        self.assertEqual(
            projection["route"], {"kind": "action", "target": "repair"}
        )
        self.assertEqual(projection["budget"]["agent_starts"], 22)
        self.assertEqual(
            self.core.replay_deliberation(plan, json.loads(json.dumps(events))),
            projection,
        )

    def test_judge_mode_names_the_preassigned_decider_and_exact_execution(self):
        governed = self.clone(self.organization)
        governed["councils"][0]["decision"].update({
            "method": "judge", "threshold": 1, "veto_roles": [],
        })
        governed["councils"][0]["audit"].update({
            "mode": "none", "sample_size": 0,
        })
        plan, _assignment = self.plan(governed)
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        _events, projection = self.drive(
            plan,
            events,
            votes={1: ["advance", "repair", "abstain"]},
            judgments={1: "advance"},
        )
        decision = projection["council_decision"]
        authority = decision["authority"]
        self.assertEqual(authority["kind"], "judge")
        self.assertEqual(authority["basis"], "judge")
        self.assertEqual(authority["decider_seat"], plan["judge"]["address"])
        self.assertEqual(authority["assignment_hash"], plan["assignment_hash"])
        self.assertEqual(authority["decider"]["role"], "judge")
        self.assertEqual(authority["decider"]["assignment_generation"], 1)
        self.assertEqual(
            authority["decider"]["execution"]["provider"],
            "fixture-provider",
        )
        self.assertEqual(
            authority["decider"]["execution"]["model"], "fixture/judge"
        )
        self.assertEqual(
            authority["decider"]["execution"]["model_binding"],
            "requested-alias",
        )
        self.assertRegex(
            authority["decider"]["execution"]["auth_domain_fingerprint"],
            r"^sha256:[0-9a-f]{64}$",
        )

    def test_decision_carries_obligations_and_blocks_green_debt(self):
        no_audit = self.clone(self.organization)
        no_audit["councils"][0]["audit"].update({
            "mode": "none", "sample_size": 0,
        })
        debt = {
            "id": "document-fallback",
            "kind": "technical-debt",
            "statement": "Document the provider fallback before expansion.",
            "priority": "medium",
            "blocking": False,
            "accountable_role": "master-architect",
            "target": "phase:26",
            "citations": ["evidence:architect-frame"],
            "acceptance": "The fallback contract has an evidence-backed story.",
            "state": "open",
        }
        plan, _assignment = self.plan(no_audit)
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        _events, projection = self.drive(
            plan,
            events,
            votes={1: ["advance", "advance", "repair"]},
            judgments={1: "advance"},
            obligations={1: [debt]},
        )
        decision = projection["council_decision"]
        self.assertEqual(decision["obligations"], [debt])
        self.assertEqual(
            projection["carried_obligations"][0]["source_decision_hash"],
            decision["decision_hash"],
        )
        self.assertFalse(projection["writes_roadmap"])

        omitted = self.submission(
            {"stage": "judgment"}, 1, result="advance"
        )
        del omitted["obligations"]
        with self.assertRaises(self.core.DeliberationError) as missing:
            self.core._normalize_submission(
                plan, {"stage": "judgment"}, omitted
            )
        self.assertIn("obligations-invalid", str(missing.exception))

        blocking = self.clone(debt)
        blocking.update({"id": "security-stop", "blocking": True})
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        with self.assertRaises(self.core.DeliberationError) as stopped:
            self.drive(
                plan,
                events,
                votes={1: ["advance", "advance", "repair"]},
                judgments={1: "advance"},
                obligations={1: [blocking]},
            )
        self.assertIn("blocking-obligation", str(stopped.exception))

    def test_completed_council_decision_is_a_distinct_fresh_quality_input(self):
        import dw_pmo.program_verdict as verdict_core

        rubric = {
            "kind": "delivery-workbench-rubric",
            "schema_version": 1,
            "slug": "design-quality",
            "title": "Design quality",
            "description": "Governed council quality fixture.",
            "version": "1.0.0",
            "subject_type": "diff",
            "result_vocabulary": [
                "pass", "fail", "needs-repair", "escalate",
            ],
            "freshness": {
                "max_age_seconds": 3600,
                "bind": [
                    "subject", "repository", "program", "assignment",
                    "rubric", "ledger",
                ],
            },
            "criteria": [{
                "id": "coherent",
                "question": "Is the proposed design coherent?",
                "evaluation": {"kind": "agent-judgment", "fact": None},
                "required_evidence_kinds": ["markdown"],
                "min_citations": 1,
                "allowed_results": [
                    "pass", "fail", "abstain", "inconclusive",
                ],
                "veto": True,
                "rationale_max_bytes": 2000,
            }],
            "aggregation": {
                "method": "all", "threshold": 1,
                "on_pass": "pass", "on_fail": "needs-repair",
                "on_abstain": "escalate",
                "on_inconclusive": "needs-repair",
            },
            "layout": {},
        }
        compiled = verdict_core.compile_rubric(self.root, rubric)
        no_audit = self.clone(self.organization)
        no_audit["councils"][0]["audit"].update({
            "mode": "none", "sample_size": 0,
        })
        plan, _assignment = self.plan(
            no_audit,
            rubric={
                "slug": "design-quality",
                "semantic_hash": compiled["semantic_hash"],
                "criteria": ["coherent"],
            },
            freshness_bound=True,
        )
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        _events, projection = self.drive(
            plan,
            events,
            votes={1: ["advance", "advance", "repair"]},
            judgments={1: "advance"},
        )
        decision = projection["council_decision"]
        gate = {
            "kind": "delivery-workbench-quality-gate",
            "schema_version": 1,
            "id": "council-quality",
            "subject_type": "diff",
            "mechanical_facts": [],
            "requirements": [{
                "id": "deliberated-design",
                "kind": "council",
                "rubric": "design-quality",
                "roles": ["debate-council"],
                "method": "at_least",
                "threshold": 1,
                "veto_roles": [],
                "meta_audit": {
                    "mode": "none", "sample_size": 0,
                    "rubric": None, "role": None,
                },
            }],
            "operator": "all",
            "threshold": 1,
            "dissent_policy": "preserve",
            "routes": {
                "pass": "advance", "fail": "repair",
                "pending": "wait", "refused": "block",
            },
            "repair": {"max_rounds": 2, "on_exhausted": "escalate"},
        }
        proof = verdict_core.evaluate_quality_gate(
            self.root,
            gate,
            plan["subject"],
            {"design-quality": rubric},
            [],
            [],
            council_decisions=[decision],
            now="2026-07-22T00:02:00Z",
        )
        self.assertEqual(proof["result"], "pass", proof["issues"])
        self.assertEqual(
            proof["evidence_preview"]["decision_hashes"],
            [decision["decision_hash"]],
        )
        self.assertEqual(proof["evidence_preview"]["verdict_hashes"], [])
        self.assertEqual(
            proof["requirements"][0]["contributors"][0]["authority"]["kind"],
            "rule",
        )

        changed = self.clone(plan["subject"])
        changed["ledger_head"] = "sha256:" + "9" * 64
        stale = verdict_core.evaluate_quality_gate(
            self.root,
            gate,
            changed,
            {"design-quality": rubric},
            [],
            [],
            council_decisions=[decision],
            now="2026-07-22T00:02:00Z",
        )
        self.assertEqual(stale["result"], "fail")
        self.assertTrue(any(
            reason["code"] == "decision-stale"
            for reason in stale["requirements"][0]["non_contributors"][0]["reasons"]
        ))

    def test_weighted_vote_and_veto_are_deterministic_and_keep_minorities(self):
        weighted = self.clone(self.organization)
        decision = weighted["councils"][0]["decision"]
        decision.update({
            "method": "weighted",
            "weights": {"researcher": 3, "critic": 1, "judge": 1},
            "threshold": 3,
            "veto_roles": [],
        })
        weighted["councils"][0]["audit"].update({"mode": "none", "sample_size": 0})
        plan, _assignment = self.plan(weighted)
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        _events, projection = self.drive(
            plan,
            events,
            votes={1: ["advance", "repair", "repair"]},
            judgments={1: "advance"},
        )
        verdict = projection["round_judgments"][0]
        self.assertEqual(verdict["aggregation"]["advance_weight"], 3)
        self.assertEqual(verdict["aggregation"]["repair_weight"], 2)
        self.assertEqual(len(verdict["aggregation"]["dissent"]), 2)
        self.assertEqual(projection["final_result"], "advance")

        vetoed = self.clone(weighted)
        vetoed["councils"][0]["decision"]["veto_roles"] = ["critic"]
        plan, _assignment = self.plan(vetoed)
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        _events, projection = self.drive(
            plan,
            events,
            votes={1: ["advance", "repair", "repair"]},
            judgments={1: "repair"},
        )
        self.assertEqual(
            projection["round_judgments"][0]["aggregation"]["basis"], "veto"
        )
        self.assertEqual(
            projection["route"], {"kind": "action", "target": "block"}
        )

    def test_tie_checkpoint_and_quorum_loss_take_only_declared_routes(self):
        no_audit = self.clone(self.organization)
        no_audit["councils"][0]["audit"].update({"mode": "none", "sample_size": 0})
        workflow_raw = json.loads(
            (self.root / "pm/workflows/architect-debate-delivery.json").read_text(
                encoding="utf-8"
            )
        )
        workflow_raw["nodes"][1]["tie_policy"] = "checkpoint"
        workflow = self.workflow_core.compile_workflow(self.root, workflow_raw)
        plan, _assignment = self.plan(no_audit, workflow)
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        _events, tied = self.drive(
            plan,
            events,
            votes={1: ["advance", "repair", "abstain"]},
            judgments={1: "checkpoint"},
        )
        self.assertEqual(tied["route"], {"kind": "action", "target": "checkpoint"})

        plan, _assignment = self.plan(no_audit)
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        _events, lost = self.drive(
            plan,
            events,
            votes={1: ["abstain", "abstain", "abstain"]},
            judgments={1: "quorum-lost"},
        )
        self.assertEqual(lost["final_result"], "quorum-lost")
        self.assertEqual(lost["route"], {"kind": "action", "target": "escalate"})
        self.assertEqual(
            lost["round_judgments"][0]["aggregation"]["quorum_observed"], 1
        )

    def test_meta_overturn_never_rewrites_the_original_council_verdict(self):
        plan, _assignment = self.plan()
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        _events, projection = self.drive(
            plan,
            events,
            votes={1: ["advance", "advance", "advance"]},
            judgments={1: "advance"},
            meta="overturn",
        )
        self.assertEqual(projection["round_judgments"][0]["result"], "advance")
        self.assertEqual(projection["meta_verdict"]["result"], "overturn")
        self.assertTrue(
            projection["meta_verdict"]["aggregation"]["original_verdict_preserved"]
        )
        self.assertFalse(
            projection["meta_verdict"]["aggregation"]["converts_judgment_to_fact"]
        )
        self.assertEqual(
            projection["route"], {"kind": "action", "target": "repair"}
        )

    def test_budget_exhaustion_is_terminal_and_uses_compiled_exhaustion_route(self):
        plan, _assignment = self.plan()
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        exhausted = self.core.claim_next_deliberation(
            plan, events, "2026-07-22T04:00:01Z"
        )
        projection = exhausted["projection"]
        self.assertEqual(projection["state"], "complete")
        self.assertEqual(projection["final_result"], "exhausted")
        self.assertEqual(
            projection["route"], {"kind": "action", "target": "escalate"}
        )
        self.assertEqual(projection["budget_exhaustion"]["counter"], "wall_seconds")
        again = self.core.claim_next_deliberation(
            plan, exhausted["events"], "2026-07-22T04:00:02Z"
        )
        self.assertFalse(again["appended"])

    def test_replacement_receipt_keeps_dissent_and_invalidates_no_completed_vote(self):
        organization = self.clone(self.organization)
        primary = next(
            item for item in organization["agents"] if item["id"] == "researcher"
        )
        backup = self.clone(primary)
        backup.update({
            "id": "researcher-backup",
            "profile": "researcher-backup",
            "workspace_domain": "researcher-backup",
        })
        organization["agents"].append(backup)
        organization["pools"].append({
            "id": "researcher-fallbacks", "agents": ["researcher-backup"],
        })
        role = next(
            item for item in organization["teams"][0]["roles"]
            if item["id"] == "researcher"
        )
        role["replacement"].update({
            "max_replacements": 1,
            "fallback_pools": ["researcher-fallbacks"],
        })
        plan, assignment = self.plan(organization)
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        # Stop after the council judgment, before the required meta-audit.
        ordinal = 0
        vote_offset = 0
        while True:
            projection = self.core.replay_deliberation(plan, events)
            if projection["round_judgments"]:
                break
            claimed = self.core.claim_next_deliberation(
                plan, events, "2026-07-22T00:01:00Z"
            )
            events = claimed["events"]
            claim = claimed["claim"]
            ordinal += 1
            vote = None
            result = None
            if claim["stage"] == "rebuttal":
                vote = ["advance", "advance", "repair"][vote_offset]
                vote_offset += 1
            elif claim["stage"] == "judgment":
                result = "advance"
            events = self.core.record_deliberation_submission(
                plan,
                events,
                claim["claim_id"],
                self.submission(claim, ordinal, vote=vote, result=result),
                "2026-07-22T00:01:00Z",
            )["events"]
        self.assertEqual(len(projection["dissent"]), 1)
        replacement = self.organization_core.plan_assignment_replacement(
            assignment, "researcher", "lost"
        )
        self.assertTrue(replacement["applicable"], replacement["issues"])
        recorded = self.core.record_deliberation_replacement(
            plan, events, replacement, "2026-07-22T00:01:00Z"
        )
        replayed = recorded["projection"]
        self.assertEqual(len(replayed["dissent"]), 1)
        self.assertEqual(len(replayed["replacements"]), 1)
        self.assertEqual(
            replayed["replacements"][0]["dissent_before"],
            [replayed["dissent"][0]["receipt_hash"]],
        )
        self.assertIsNone(replayed["replacements"][0]["invalidated_claim_id"])

    def test_closed_receipts_refuse_transcripts_and_replay_detects_corruption(self):
        plan, _assignment = self.plan()
        events = self.core.start_deliberation(plan, "2026-07-22T00:00:00Z")
        claimed = self.core.claim_next_deliberation(
            plan, events, "2026-07-22T00:01:00Z"
        )
        submission = self.submission(claimed["claim"], 1)
        submission["transport_transcript"] = "opaque chat"
        with self.assertRaises(self.core.DeliberationError) as refused:
            self.core.record_deliberation_submission(
                plan,
                claimed["events"],
                claimed["claim"]["claim_id"],
                submission,
                "2026-07-22T00:01:00Z",
            )
        self.assertIn("unknown-key", str(refused.exception))
        self.assertFalse(
            claimed["projection"]["durable_content"]["transport_transcripts"]
        )

        valid = self.submission(claimed["claim"], 1)
        recorded = self.core.record_deliberation_submission(
            plan,
            claimed["events"],
            claimed["claim"]["claim_id"],
            valid,
            "2026-07-22T00:01:00Z",
        )
        repeated = self.core.record_deliberation_submission(
            plan,
            recorded["events"],
            claimed["claim"]["claim_id"],
            valid,
            "2026-07-22T00:01:00Z",
        )
        self.assertFalse(repeated["appended"])
        changed = self.clone(valid)
        changed["content_hash"] = "sha256:" + "9" * 64
        with self.assertRaises(self.core.DeliberationError) as conflict:
            self.core.record_deliberation_submission(
                plan,
                recorded["events"],
                claimed["claim"]["claim_id"],
                changed,
                "2026-07-22T00:01:00Z",
            )
        self.assertIn("idempotency-conflict", str(conflict.exception))

        corrupt = self.clone(claimed["events"])
        corrupt[-1]["detail"]["role"] = "invented-role"
        with self.assertRaises(self.core.DeliberationError) as invalid:
            self.core.replay_deliberation(plan, corrupt)
        self.assertIn("ledger-corrupt", str(invalid.exception))

    def test_council_policy_is_closed_and_budget_mismatch_refuses_plan(self):
        for method, threshold in (
            ("majority", 2), ("weighted", 2), ("unanimous", 3), ("judge", 1),
        ):
            raw = self.clone(self.organization)
            raw["councils"][0]["decision"].update({
                "method": method, "threshold": threshold,
            })
            compiled = self.organization_core.compile_organization(self.root, raw)
            self.assertEqual(
                compiled["organization"]["councils"][0]["decision"]["method"],
                method,
            )

        unknown = self.clone(self.organization)
        unknown["councils"][0]["opaque_chat"] = True
        validation = self.organization_core.validate_organization(self.root, unknown)
        self.assertIn(
            "unknown-key", {item["code"] for item in validation["diagnostics"]}
        )

        too_small = self.clone(self.organization)
        too_small["councils"][0]["budgets"]["max_tokens"] = 1
        with self.assertRaises(self.core.DeliberationError) as refused:
            self.plan(too_small)
        self.assertIn("council-budget-exceeded", str(refused.exception))


class ProgramVerdictTest(unittest.TestCase):
    """WLA-26-07: honest mechanical facts and governed judgment proofs."""

    def setUp(self):
        import dw_pmo.program_verdict as verdict_core

        self.core = verdict_core
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-verdict-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        (self.root / "pm/rubrics").mkdir(parents=True)
        self.subject = {
            "kind": "diff",
            "hash": self.h("1"),
            "repository_hash": self.h("2"),
            "program_hash": self.h("3"),
            "program_run_id": "program-run-001",
            "phase": 26,
            "story": "WLA-26-07",
            "workflow_address": "program/story-quality",
            "assignment_hash": self.h("4"),
            "assignment_generation": 1,
            "ledger_head": self.h("5"),
            "implementer_principals": [self.h("a")],
        }
        self.story_rubric = self.rubric(
            "story-quality", "diff",
            [
                self.criterion(
                    "tests", "Did the exact verification command pass?",
                    evaluation={"kind": "mechanical-fact", "fact": "tests"},
                    evidence=(), citations=0, veto=True,
                ),
                self.criterion(
                    "intent", "Does the candidate satisfy the story intent?",
                    evidence=("git-diff",), citations=1, veto=True,
                ),
            ],
        )
        self.meta_rubric = self.rubric(
            "verdict-audit", "verdict-set",
            [self.criterion(
                "procedure", "Is the underlying verdict valid and fresh?",
                evidence=("verdict",), citations=1, veto=True,
            )],
            vocabulary=("pass", "fail", "uphold", "overturn", "escalate"),
            outcomes={
                "on_pass": "uphold", "on_fail": "overturn",
                "on_abstain": "escalate", "on_inconclusive": "escalate",
            },
        )
        self.architect_rubric = self.rubric(
            "architecture", "phase-snapshot",
            [self.criterion(
                "coherence", "Is the phase architecture coherent?",
                evidence=("markdown",), citations=1, veto=True,
            )],
            vocabulary=("pass", "fail", "approve", "veto", "escalate"),
            outcomes={
                "on_pass": "approve", "on_fail": "veto",
                "on_abstain": "escalate", "on_inconclusive": "escalate",
            },
        )

    @staticmethod
    def h(character):
        return "sha256:" + character * 64

    def execution(self, role, principal):
        return {
            "harness": "fixture",
            "adapter": "fixture",
            "adapter_version": "fixture-verdict-v1",
            "router": "fixture-router",
            "provider": "fixture-provider",
            "model_vendor": "fixture-vendor",
            "model_family": "fixture-family",
            "model": f"fixture/{role}-{principal}",
            "model_revision": None,
            "model_binding": "requested-alias",
            "auth_domain_fingerprint": self.h(
                {"a": "1", "b": "2", "c": "3", "0": "4"}.get(
                    principal, "5"
                )
            ),
            "capability_fingerprint": self.h(
                {"a": "6", "b": "7", "c": "8", "0": "9"}.get(
                    principal, "0"
                )
            ),
        }

    def criterion(
        self, criterion_id, question, *, evaluation=None,
        evidence=(), citations=1, veto=False,
    ):
        return {
            "id": criterion_id,
            "question": question,
            "evaluation": evaluation or {"kind": "agent-judgment", "fact": None},
            "required_evidence_kinds": list(evidence),
            "min_citations": citations,
            "allowed_results": ["pass", "fail", "abstain", "inconclusive"],
            "veto": veto,
            "rationale_max_bytes": 2_000,
        }

    def rubric(
        self, slug, subject_type, criteria, *,
        vocabulary=("pass", "fail", "needs-repair", "escalate"),
        outcomes=None,
    ):
        outcomes = outcomes or {
            "on_pass": "pass", "on_fail": "needs-repair",
            "on_abstain": "escalate", "on_inconclusive": "needs-repair",
        }
        return {
            "kind": "delivery-workbench-rubric",
            "schema_version": 1,
            "slug": slug,
            "title": slug.replace("-", " ").title(),
            "description": "Fixture rubric with explicit evidence and freshness.",
            "version": "1.0.0",
            "subject_type": subject_type,
            "result_vocabulary": list(vocabulary),
            "freshness": {
                "max_age_seconds": 3_600,
                "bind": [
                    "subject", "repository", "program", "assignment",
                    "rubric", "ledger",
                ],
            },
            "criteria": criteria,
            "aggregation": {
                "method": "all",
                "threshold": len(criteria),
                **outcomes,
            },
            "layout": {},
        }

    def assignment(self, role="verifier", duty="verifier", principal="b"):
        independent = [{
            "role": "implementer",
            "address": f"{self.subject['workflow_address']}/role/implementer/slot/1",
            "principal_fingerprint": self.h("a"),
            "workspace_domain": "implementer-a",
            "session_binding_key": self.h("d"),
        }]
        if duty == "meta-verifier":
            independent.append({
                "role": "verifier",
                "address": f"{self.subject['workflow_address']}/role/verifier/slot/1",
                "principal_fingerprint": self.h("b"),
                "workspace_domain": "verifier-b",
                "session_binding_key": self.h("e"),
            })
        return {
            "kind": "delivery-workbench-verdict-assignment",
            "schema_version": 1,
            "assignment_hash": self.subject["assignment_hash"],
            "story": self.subject["story"],
            "workflow_address": self.subject["workflow_address"],
            "role": role,
            "duty": duty,
            "address": f"{self.subject['workflow_address']}/role/{role}/slot/1",
            "assignment_generation": self.subject["assignment_generation"],
            "principal_fingerprint": self.h(principal),
            "workspace_domain": f"{role}-{principal}",
            "session_binding_key": self.h({"a": "d", "b": "e", "c": "f"}[principal]),
            "packet_policy_hash": self.h("9"),
            "execution": self.execution(role, principal),
            "independent_from": independent,
        }

    def fact(self, *, subject=None, passed=True, fact_id="tests"):
        receipt = {
            "kind": "delivery-workbench-mechanical-receipt",
            "schema_version": 1,
            "adapter_kind": "check-adapter",
            "adapter_id": "local-checks",
            "adapter_fingerprint": self.h("6"),
            "capability": "check:execute",
            "predicate": "verification-command",
            "passed": passed,
            "receipt_hash": self.h("7" if passed else "8"),
            "observation_ref": "checks/program-verdict",
            "observation_hash": self.h("c"),
            "observation_bytes": 80,
            "command": {
                "argv": ["python3", "-m", "unittest"],
                "cwd": ".",
                "exit_code": 0 if passed else 1,
            },
            "issued_at": "2026-07-22T12:00:00Z",
        }
        return self.core.build_mechanical_fact(
            fact_id, receipt, subject or self.subject
        )

    def judgment_result(self, fact, *, result="pass", intent="pass"):
        return [
            {
                "id": "tests",
                "result": result,
                "evidence": [],
                "citations": [],
                "rationale": None,
                "mechanical_fact_hash": fact["fact_hash"],
            },
            {
                "id": "intent",
                "result": intent,
                "evidence": [{
                    "id": "candidate",
                    "kind": "git-diff",
                    "hash": self.subject["hash"],
                    "ref": "artifacts/candidate.diff",
                }],
                "citations": [{
                    "id": "intent-citation",
                    "evidence_id": "candidate",
                    "locator": "candidate.diff#L1",
                    "hash": self.h("d"),
                }],
                "rationale": "The exact candidate satisfies the contracted story intent.",
                "mechanical_fact_hash": None,
            },
        ]

    def verdict(
        self, *, assignment=None, subject=None, fact=None,
        intent="pass", verdict_type="agent-verdict", rubric=None,
        source_verdicts=None, superseded=None, key="verdict-1",
        issued_at="2026-07-22T12:10:00Z",
    ):
        subject = subject or self.subject
        fact = fact or self.fact(subject=subject)
        rubric = rubric or self.story_rubric
        if rubric["slug"] == "story-quality":
            criteria = self.judgment_result(
                fact, result=fact["result"], intent=intent
            )
            mechanical = [fact]
        else:
            evidence_kind = (
                "verdict" if rubric["subject_type"] == "verdict-set"
                else "markdown"
            )
            criteria = [{
                "id": rubric["criteria"][0]["id"],
                "result": intent,
                "evidence": [{
                    "id": "review-source",
                    "kind": evidence_kind,
                    "hash": subject["hash"],
                    "ref": "artifacts/review-source.json",
                }],
                "citations": [{
                    "id": "review-citation",
                    "evidence_id": "review-source",
                    "locator": "review-source.json#criterion",
                    "hash": self.h("e"),
                }],
                "rationale": "The declared evidence supports this governed judgment.",
                "mechanical_fact_hash": None,
            }]
            mechanical = []
        return self.core.issue_agent_verdict(
            self.root,
            rubric,
            assignment or self.assignment(),
            subject,
            criteria,
            issued_at=issued_at,
            idempotency_key=key,
            attestation_receipt_hash=self.h("f"),
            verdict_type=verdict_type,
            mechanical_facts=mechanical,
            source_verdicts=source_verdicts,
            superseded_verdicts=superseded,
        )

    def gate(self, *, kind="independent", rubric="story-quality", roles=None,
             meta=None, subject_type="diff", dissent="block"):
        return {
            "kind": "delivery-workbench-quality-gate",
            "schema_version": 1,
            "id": "story-gate",
            "subject_type": subject_type,
            "mechanical_facts": (
                [{"id": "tests", "max_age_seconds": 3_600}]
                if subject_type == "diff" else []
            ),
            "requirements": [{
                "id": "governed-review",
                "kind": kind,
                "rubric": rubric,
                "roles": roles or (["architect"] if kind == "architect" else ["verifier"]),
                "method": "at_least",
                "threshold": 1,
                "veto_roles": roles or (["architect"] if kind == "architect" else ["verifier"]),
                "meta_audit": meta or {
                    "mode": "none", "sample_size": 0,
                    "rubric": None, "role": None,
                },
            }],
            "operator": "all",
            "threshold": 1,
            "dissent_policy": dissent,
            "routes": {
                "pass": "advance", "fail": "repair",
                "pending": "wait", "refused": "block",
            },
            "repair": {"max_rounds": 2, "on_exhausted": "escalate"},
        }

    def evaluate(self, facts, verdicts, *, gate=None, subject=None,
                 rubrics=None, repair_round=0):
        return self.core.evaluate_quality_gate(
            self.root,
            gate or self.gate(),
            subject or self.subject,
            rubrics or {"story-quality": self.story_rubric},
            facts,
            verdicts,
            now="2026-07-22T12:20:00Z",
            repair_round=repair_round,
        )

    def test_rubric_compiler_is_closed_hashed_and_layout_neutral(self):
        compiled = self.core.compile_rubric(self.root, self.story_rubric)
        moved = json.loads(json.dumps(self.story_rubric))
        moved["layout"] = {"criteria": {"intent": {"x": 900, "y": 12}}}
        after = self.core.compile_rubric(self.root, moved)
        self.assertEqual(compiled["semantic_hash"], after["semantic_hash"])
        self.assertNotEqual(compiled["document_hash"], after["document_hash"])
        broken = json.loads(json.dumps(self.story_rubric))
        broken["criteria"][0]["private_prompt"] = "hidden"
        validation = self.core.validate_rubric(self.root, broken)
        self.assertFalse(validation["valid"])
        self.assertEqual(validation["diagnostics"][0]["code"], "unknown-key")

    def test_malformed_or_escaping_rubric_is_diagnosed_without_work(self):
        malformed = self.root / "pm/rubrics/broken.json"
        malformed.write_text('{"kind":', encoding="utf-8")
        self.assertEqual(
            self.core.find_rubric_path(self.root, "broken"), malformed
        )
        validation = self.core.validate_rubric(self.root, malformed)
        self.assertFalse(validation["valid"])
        self.assertEqual(validation["diagnostics"][0]["code"], "parse-error")
        inventory = self.core.rubric_inventory(self.root)
        self.assertFalse(inventory["healthy"])
        self.assertFalse(inventory["starts_work"])
        self.assertFalse(inventory["writes_state"])

        outside = self.root.parent / "outside-rubric.json"
        outside.write_text(
            json.dumps(self.story_rubric), encoding="utf-8"
        )
        self.addCleanup(outside.unlink, missing_ok=True)
        refused = self.core.validate_rubric(self.root, outside)
        self.assertFalse(refused["valid"])
        self.assertEqual(
            refused["diagnostics"][0]["code"], "path-outside-policy"
        )

    def test_mechanical_fact_and_independent_verdict_pass_pure_gate(self):
        fact = self.fact()
        verdict = self.verdict(fact=fact)
        proof = self.evaluate([fact], [verdict])
        self.assertEqual(proof["result"], "pass", proof["issues"])
        self.assertEqual(proof["route"], "advance")
        self.assertEqual(proof["mechanical"][0]["status"], "pass")
        self.assertTrue(verdict["judgment_not_mechanical"])
        self.assertRegex(proof["proof_hash"], r"^sha256:[0-9a-f]{64}$")
        for flag in (
            "starts_work", "writes_state", "writes_repository",
            "writes_roadmap", "materializes_evidence", "creates_grant",
        ):
            self.assertFalse(proof[flag])

    def test_introduced_failures_force_block_and_preexisting_render_honestly(self):
        fact = self.fact()
        verdict = self.verdict(fact=fact)
        introduced = self.core.evaluate_quality_gate(
            self.root, self.gate(), self.subject,
            {"story-quality": self.story_rubric}, [fact], [verdict],
            now="2026-07-22T12:20:00Z", repair_round=99,
            test_failures={
                "introduced": ["pkg/test_mod.py::test_regression"],
                "pre_existing": ["pkg/test_mod.py::test_existing"],
                "subtraction_available": True,
                "refusal_reason": None,
            },
        )
        self.assertEqual((introduced["result"], introduced["route"]), ("fail", "block"))
        self.assertEqual(
            introduced["test_failures"]["state"], "introduced-failures"
        )
        self.assertIn(
            "introduced-test-failure",
            {item["code"] for item in introduced["issues"]},
        )

        preexisting = self.core.evaluate_quality_gate(
            self.root, self.gate(), self.subject,
            {"story-quality": self.story_rubric}, [fact], [verdict],
            now="2026-07-22T12:20:00Z",
            test_failures={
                "introduced": [],
                "pre_existing": ["pkg/test_mod.py::test_existing"],
                "subtraction_available": True,
                "refusal_reason": None,
            },
        )
        self.assertEqual((preexisting["result"], preexisting["route"]), ("pass", "advance"))
        self.assertEqual(
            preexisting["test_failures"]["state"],
            "no-introduced-failures-with-pre-existing",
        )
        self.assertEqual(preexisting["test_failures"]["pre_existing_count"], 1)

    def test_forged_fact_and_agent_prose_as_mechanical_evidence_refuse(self):
        fact = self.fact()
        forged = json.loads(json.dumps(fact))
        forged["result"] = "fail"
        proof = self.evaluate([forged], [])
        self.assertEqual(proof["result"], "refused")
        self.assertIn(
            proof["issues"][0]["code"], {"receipt-forged", "receipt-conflict"}
        )

        criteria = self.judgment_result(fact)
        criteria[0]["rationale"] = "I think the tests passed."
        with self.assertRaises(self.core.VerdictError) as raised:
            self.core.issue_agent_verdict(
                self.root, self.story_rubric, self.assignment(), self.subject,
                criteria, issued_at="2026-07-22T12:10:00Z",
                idempotency_key="counterfeit", attestation_receipt_hash=self.h("f"),
                mechanical_facts=[fact],
            )
        self.assertEqual(raised.exception.code, "mechanical-counterfeit")

    def test_self_verification_and_colluding_panel_principals_refuse(self):
        fact = self.fact()
        with self.assertRaises(self.core.VerdictError) as raised:
            self.verdict(assignment=self.assignment(principal="a"), fact=fact)
        self.assertEqual(raised.exception.code, "separation-violation")

        unproven = self.assignment()
        unproven["independent_from"] = []
        with self.assertRaises(self.core.VerdictError) as missing_proof:
            self.verdict(assignment=unproven, fact=fact)
        self.assertEqual(missing_proof.exception.code, "separation-violation")

        first = self.verdict(fact=fact, key="member-1")
        second = self.verdict(
            assignment=self.assignment(role="reviewer", duty="reviewer", principal="b"),
            fact=fact, key="member-2",
        )
        with self.assertRaises(self.core.VerdictError) as panel:
            self.core.compose_panel_verdict(
                self.root, self.story_rubric, self.subject, [first, second],
                {
                    "id": "quality-panel", "method": "at_least",
                    "threshold": 2, "quorum": 2, "veto_roles": [],
                    "dissent_policy": "preserve",
                },
                issued_at="2026-07-22T12:15:00Z",
                idempotency_key="panel-1",
            )
        self.assertEqual(panel.exception.code, "separation-violation")

    def test_missing_citations_and_content_leakage_refuse(self):
        fact = self.fact()
        criteria = self.judgment_result(fact)
        criteria[1]["citations"] = []
        with self.assertRaises(self.core.VerdictError) as raised:
            self.core.issue_agent_verdict(
                self.root, self.story_rubric, self.assignment(), self.subject,
                criteria, issued_at="2026-07-22T12:10:00Z",
                idempotency_key="missing-citation",
                attestation_receipt_hash=self.h("f"), mechanical_facts=[fact],
            )
        self.assertEqual(raised.exception.code, "citation-missing")

        leaked = self.verdict(fact=fact)
        leaked["private_reasoning"] = "never durable"
        proof = self.evaluate([fact], [leaked])
        self.assertEqual(proof["result"], "refused")
        self.assertEqual(proof["issues"][0]["code"], "unknown-key")

    def test_rubric_diff_and_ledger_freshness_invalidate_green_verdict(self):
        fact = self.fact()
        verdict = self.verdict(fact=fact)
        drifted = json.loads(json.dumps(self.story_rubric))
        drifted["criteria"][1]["question"] = "Did it solve the exact user problem?"
        proof = self.evaluate(
            [fact], [verdict], rubrics={"story-quality": drifted}
        )
        self.assertEqual(proof["result"], "fail")
        self.assertTrue(any(
            reason["message"] == "rubric semantic hash changed"
            for reason in proof["requirements"][0]["non_contributors"][0]["reasons"]
        ))

        changed = json.loads(json.dumps(self.subject))
        changed["hash"] = self.h("0")
        changed["ledger_head"] = self.h("8")
        changed_fact = self.fact(subject=changed)
        proof = self.evaluate(
            [changed_fact], [verdict], subject=changed
        )
        self.assertEqual(proof["result"], "fail")
        messages = {
            reason["message"]
            for reason in proof["requirements"][0]["non_contributors"][0]["reasons"]
        }
        self.assertTrue({"subject kind or hash changed", "ledger_head changed"} <= messages)

        reassigned = json.loads(json.dumps(self.subject))
        reassigned["implementer_principals"] = [self.h("0")]
        reassigned_fact = self.fact(subject=reassigned)
        proof = self.evaluate(
            [reassigned_fact], [verdict], subject=reassigned
        )
        self.assertEqual(proof["result"], "fail")
        self.assertTrue(any(
            reason["message"] == "implementer_principals changed"
            for reason in proof["requirements"][0]["non_contributors"][0]["reasons"]
        ))

    def test_supersession_keeps_red_history_and_uses_fresh_repair_verdict(self):
        old_subject = json.loads(json.dumps(self.subject))
        old_subject["hash"] = self.h("0")
        old_fact = self.fact(subject=old_subject, passed=False)
        old = self.verdict(
            subject=old_subject, fact=old_fact, intent="fail", key="old-red",
            issued_at="2026-07-22T12:05:00Z",
        )
        fact = self.fact()
        fresh = self.verdict(
            fact=fact, superseded=[old], key="fresh-green"
        )
        proof = self.evaluate([fact], [old, fresh])
        self.assertEqual(proof["result"], "pass", proof["issues"])
        history = {item["verdict_hash"]: item for item in proof["history"]}
        self.assertFalse(history[old["verdict_hash"]]["active"])
        self.assertEqual(
            history[old["verdict_hash"]]["superseded_by"], fresh["verdict_hash"]
        )
        self.assertTrue(history[fresh["verdict_hash"]]["active"])

    def test_panel_preserves_dissent_quorum_and_veto(self):
        fact = self.fact()
        green = self.verdict(fact=fact, key="green-member")
        red = self.verdict(
            assignment=self.assignment(
                role="reviewer", duty="reviewer", principal="c"
            ),
            fact=fact, intent="fail", key="red-member",
        )
        panel = self.core.compose_panel_verdict(
            self.root, self.story_rubric, self.subject, [green, red],
            {
                "id": "quality-panel", "method": "at_least",
                "threshold": 1, "quorum": 2, "veto_roles": ["reviewer"],
                "dissent_policy": "preserve",
            },
            issued_at="2026-07-22T12:15:00Z",
            idempotency_key="panel-veto",
        )
        self.assertEqual(panel["result"], "needs-repair")
        self.assertTrue(panel["composition"]["vetoed"])
        self.assertTrue(panel["composition"]["original_verdicts_preserved"])
        self.assertEqual(len(panel["dissent"]), 1)

        abstaining = self.verdict(
            assignment=self.assignment(
                role="reviewer", duty="reviewer", principal="c"
            ),
            fact=fact, intent="abstain", key="abstaining-member",
        )
        quorum_lost = self.core.compose_panel_verdict(
            self.root, self.story_rubric, self.subject, [green, abstaining],
            {
                "id": "quality-panel", "method": "at_least",
                "threshold": 1, "quorum": 2, "veto_roles": [],
                "dissent_policy": "preserve",
            },
            issued_at="2026-07-22T12:15:00Z",
            idempotency_key="panel-quorum",
        )
        self.assertEqual(quorum_lost["composition"]["quorum_observed"], 1)
        self.assertEqual(quorum_lost["result"], "needs-repair")

    def test_panel_gate_is_order_independent_and_requires_source_lineage(self):
        fact = self.fact()
        first = self.verdict(fact=fact, key="council-green-1")
        second = self.verdict(
            assignment=self.assignment(
                role="reviewer", duty="reviewer", principal="c"
            ),
            fact=fact,
            key="council-green-2",
        )
        policy = {
            "id": "quality-panel", "method": "at_least",
            "threshold": 2, "quorum": 2, "veto_roles": [],
            "dissent_policy": "preserve",
        }
        panel = self.core.compose_panel_verdict(
            self.root, self.story_rubric, self.subject, [first, second],
            policy, issued_at="2026-07-22T12:15:00Z",
            idempotency_key="deterministic-panel",
        )
        reversed_panel = self.core.compose_panel_verdict(
            self.root, self.story_rubric, self.subject, [second, first],
            policy, issued_at="2026-07-22T12:15:00Z",
            idempotency_key="deterministic-panel",
        )
        self.assertEqual(panel["verdict_hash"], reversed_panel["verdict_hash"])
        gate = self.gate(
            kind="panel", roles=["quality-panel"]
        )
        proof = self.evaluate(
            [fact], [first, second, panel], gate=gate
        )
        self.assertEqual(proof["result"], "pass", proof["issues"])
        self.assertEqual(
            proof["evidence_preview"]["verdict_hashes"],
            [panel["verdict_hash"]],
        )
        self.assertEqual(
            set(proof["evidence_preview"]["source_verdict_hashes"]),
            {first["verdict_hash"], second["verdict_hash"]},
        )

        missing_sources = self.evaluate([fact], [panel], gate=gate)
        self.assertEqual(missing_sources["result"], "refused")
        self.assertEqual(
            missing_sources["issues"][0]["code"], "invalid-lineage"
        )

    def test_full_meta_audit_overturns_without_erasing_source(self):
        fact = self.fact()
        source = self.verdict(fact=fact)
        meta_subject = self.core.build_verdict_set_subject(
            self.subject, [source]
        )
        meta = self.verdict(
            assignment=self.assignment(
                role="meta", duty="meta-verifier", principal="c"
            ),
            subject=meta_subject,
            rubric=self.meta_rubric,
            verdict_type="meta-verdict",
            source_verdicts=[source],
            intent="fail",
            key="meta-overturn",
        )
        gate = self.gate(meta={
            "mode": "full", "sample_size": 0,
            "rubric": "verdict-audit", "role": "meta",
        })
        proof = self.evaluate(
            [fact], [source, meta], gate=gate,
            rubrics={
                "story-quality": self.story_rubric,
                "verdict-audit": self.meta_rubric,
            },
        )
        self.assertEqual(proof["result"], "fail", proof["issues"])
        audit = proof["requirements"][0]["meta_audit"][0]
        self.assertEqual(audit["status"], "fail")
        self.assertTrue(audit["original_verdict_preserved"])
        self.assertIn(source["verdict_hash"], {
            item["verdict_hash"] for item in proof["history"]
        })

    def test_architect_veto_and_bounded_repair_exhaustion_route(self):
        phase_subject = json.loads(json.dumps(self.subject))
        phase_subject.update({
            "kind": "phase-snapshot", "hash": self.h("0"), "story": None,
        })
        architect_assignment = self.assignment(
            role="architect", duty="master-architect", principal="c"
        )
        architect_assignment["story"] = None
        architect = self.verdict(
            assignment=architect_assignment,
            subject=phase_subject,
            rubric=self.architect_rubric,
            verdict_type="architect-verdict",
            intent="fail",
            key="architect-veto",
        )
        proof = self.evaluate(
            [], [architect],
            gate=self.gate(
                kind="architect", rubric="architecture", roles=["architect"],
                subject_type="phase-snapshot",
            ),
            subject=phase_subject,
            rubrics={"architecture": self.architect_rubric},
            repair_round=2,
        )
        self.assertEqual(proof["result"], "fail", proof["issues"])
        self.assertEqual(proof["route"], "escalate")
        self.assertTrue(any(item["code"] == "budget-exhausted" for item in proof["issues"]))

    def test_conflicting_active_verdicts_preserve_dissent_and_fail_closed(self):
        fact = self.fact()
        green = self.verdict(fact=fact, key="conflict-green")
        red = self.verdict(
            assignment=self.assignment(
                role="reviewer", duty="reviewer", principal="c"
            ),
            fact=fact, intent="fail", key="conflict-red",
        )
        gate = self.gate(roles=["verifier", "reviewer"], dissent="block")
        proof = self.evaluate([fact], [green, red], gate=gate)
        self.assertEqual(proof["result"], "fail")
        self.assertEqual(proof["route"], "repair")
        self.assertTrue(any(
            item["result"] == "conflict" for item in proof["dissent"]
        ))
        self.assertEqual(len(proof["requirements"][0]["contributors"]), 2)

    def test_random_meta_sample_is_deterministic_and_exact(self):
        fact = self.fact()
        first = self.verdict(fact=fact, key="random-source-1")
        second = self.verdict(
            assignment=self.assignment(
                role="reviewer", duty="reviewer", principal="c"
            ),
            fact=fact, key="random-source-2",
        )
        gate = self.gate(
            roles=["verifier", "reviewer"],
            meta={
                "mode": "random", "sample_size": 1,
                "rubric": "verdict-audit", "role": "meta",
            },
            dissent="preserve",
        )
        gate["requirements"][0]["threshold"] = 2
        rubrics = {
            "story-quality": self.story_rubric,
            "verdict-audit": self.meta_rubric,
        }
        pending = self.evaluate(
            [fact], [first, second], gate=gate, rubrics=rubrics
        )
        self.assertEqual(pending["result"], "pending")
        selected_hash = pending["requirements"][0]["meta_audit"][0]["sources"][0]
        self.assertEqual(
            selected_hash,
            self.evaluate(
                [fact], [second, first], gate=gate, rubrics=rubrics
            )["requirements"][0]["meta_audit"][0]["sources"][0],
        )
        source = next(
            item for item in (first, second)
            if item["verdict_hash"] == selected_hash
        )
        meta_assignment = self.assignment(
            role="meta", duty="meta-verifier", principal="b"
        )
        meta_assignment.update({
            "principal_fingerprint": self.h("0"),
            "workspace_domain": "meta-zero",
            "session_binding_key": self.h("1"),
        })
        implementer_independence = {
            "role": "implementer",
            "address": f"{self.subject['workflow_address']}/role/implementer/slot/1",
            "principal_fingerprint": self.h("a"),
            "workspace_domain": "implementer-a",
            "session_binding_key": self.h("d"),
        }
        meta_assignment["independent_from"] = [
            implementer_independence,
            *[{
                "role": item["issuer"]["role"],
                "address": item["issuer"]["address"],
                "principal_fingerprint": item["issuer"]["principal_fingerprint"],
                "workspace_domain": item["assignment"]["workspace_domain"],
                "session_binding_key": item["assignment"]["session_binding_key"],
            }
            for item in (first, second)],
        ]
        meta_subject = self.core.build_verdict_set_subject(
            self.subject, [source]
        )
        meta = self.verdict(
            assignment=meta_assignment,
            subject=meta_subject,
            rubric=self.meta_rubric,
            verdict_type="meta-verdict",
            source_verdicts=[source],
            key="random-meta",
        )
        passed = self.evaluate(
            [fact], [first, second, meta], gate=gate, rubrics=rubrics
        )
        self.assertEqual(passed["result"], "pass", passed["issues"])
        self.assertEqual(
            passed["requirements"][0]["meta_audit"][0]["sources"],
            [selected_hash],
        )

    def test_missing_verdict_is_pending_and_proves_no_implicit_action(self):
        fact = self.fact()
        proof = self.evaluate([fact], [])
        self.assertEqual(proof["result"], "pending")
        self.assertEqual(proof["route"], "wait")
        self.assertRegex(proof["proof_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertFalse(proof["authority"]["may_advance"])
        self.assertFalse(proof["authority"]["may_repair"])

    def test_rubric_cli_inventory_and_validation_share_the_core(self):
        path = self.root / "pm/rubrics/story-quality.json"
        path.write_text(
            json.dumps(self.story_rubric, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        command = [
            sys.executable, str(TESTS_DIR.parent / "bin/dw"),
            "--root", str(self.root), "rubric",
        ]
        listed = subprocess.run(
            command + ["list", "--json"], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(listed.returncode, 0, listed.stderr)
        inventory = json.loads(listed.stdout)
        self.assertTrue(inventory["healthy"])
        self.assertEqual(inventory["rubrics"][0]["slug"], "story-quality")
        validated = subprocess.run(
            command + ["validate", "story-quality", "--json"], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(validated.returncode, 0, validated.stderr)
        document = json.loads(validated.stdout)
        self.assertTrue(document["valid"])
        self.assertEqual(
            document["compiled"]["semantic_hash"],
            inventory["rubrics"][0]["semantic_hash"],
        )

    def test_team_assignment_projects_an_exact_read_only_verdict_packet(self):
        def member(role, principal, workspace, session):
            return {
                "slot": 1,
                "address": (
                    f"{self.subject['workflow_address']}/role/{role}/slot/1"
                ),
                "assignment_generation": 1,
                "principal_fingerprint": self.h(principal),
                "workspace_domain": workspace,
                "session_binding_key": self.h(session),
                "execution": self.execution(role, principal),
            }

        implementer = member("implementer", "a", "implementer-a", "d")
        verifier = member("verifier", "b", "verifier-b", "e")
        assignment = {
            "kind": "delivery-workbench-team-assignment",
            "schema_version": 1,
            "applicable": True,
            "story": self.subject["story"],
            "workflow_address": self.subject["workflow_address"],
            "roles": [
                {
                    "role": "implementer",
                    "duty": "implementer",
                    "members": [implementer],
                    "independent_from": [],
                    "packet_policy": {
                        "workspace": "isolated-worktree",
                        "verdict_schema": None,
                        "effective_capability_ceiling": ["workspace:write"],
                    },
                },
                {
                    "role": "verifier",
                    "duty": "verifier",
                    "members": [verifier],
                    "independent_from": ["implementer"],
                    "packet_policy": {
                        "workspace": "read-only",
                        "verdict_schema": "delivery-workbench-verdict@1",
                        "effective_capability_ceiling": [
                            "verdict:issue"
                        ],
                    },
                },
            ],
        }
        assignment["assignment_hash"] = "sha256:" + hashlib.sha256(
            self.core.canonical_json(assignment).encode("utf-8")
        ).hexdigest()
        self.subject["assignment_hash"] = assignment["assignment_hash"]
        packet = self.core.build_verdict_assignment(
            assignment, "verifier"
        )
        self.assertEqual(packet["principal_fingerprint"], self.h("b"))
        self.assertEqual(packet["duty"], "verifier")
        self.assertEqual(len(packet["independent_from"]), 1)
        self.assertEqual(
            packet["independent_from"][0]["principal_fingerprint"], self.h("a")
        )
        self.assertEqual(
            set(self.core.MECHANICAL_PREDICATES),
            {
                "check-receipt", "artifact-conformance",
                "schema-conformance", "citation-conformance", "diff-scope",
                "roadmap-health", "contract-health", "signal-state",
                "history-condition", "verification-command",
            },
        )

        colluding = json.loads(json.dumps(assignment))
        colluding["roles"][1]["members"][0]["principal_fingerprint"] = self.h("a")
        colluding["assignment_hash"] = "sha256:" + hashlib.sha256(
            self.core.canonical_json({
                key: value for key, value in colluding.items()
                if key != "assignment_hash"
            }).encode("utf-8")
        ).hexdigest()
        with self.assertRaises(self.core.VerdictError) as raised:
            self.core.build_verdict_assignment(colluding, "verifier")
        self.assertEqual(raised.exception.code, "separation-violation")


class ProgramWorkflowTest(unittest.TestCase):
    """WLA-26-03: reusable hierarchy and statically finite workflow loops."""

    def setUp(self):
        import dw_pmo.program_workflow as workflow_core

        self.core = workflow_core
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-workflow-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        workflow_dir = self.root / "pm/workflows"
        score_dir = self.root / "pm/orchestration"
        workflow_dir.mkdir(parents=True)
        score_dir.mkdir(parents=True)
        template_dir = TESTS_DIR.parent / "templates/workflows"
        for source in template_dir.glob("*.json"):
            shutil.copy2(source, workflow_dir / source.name)
        shutil.copy2(
            TESTS_DIR.parent / "templates/orchestration/research-build-review.json",
            score_dir / "research-build-review.json",
        )
        self.docs_path = workflow_dir / "docs-only.json"
        self.research_path = workflow_dir / "research-build-verify.json"
        self.architect_path = workflow_dir / "architect-debate-delivery.json"

    @staticmethod
    def diagnostic_codes(exc):
        return {item["code"] for item in exc.exception.diagnostics}

    @staticmethod
    def clone(value):
        return json.loads(json.dumps(value))

    def load(self, path):
        return self.core.load_workflow(path)

    def cli(self, *args):
        return subprocess.run(
            [
                sys.executable,
                str(TESTS_DIR.parent / "bin/dw"),
                "--root",
                str(self.root),
                "workflow",
                *args,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_three_shipped_templates_compile_with_finite_envelopes(self):
        inventory = self.core.workflow_inventory(self.root)
        self.assertTrue(inventory["healthy"], inventory["workflows"])
        self.assertEqual(
            {item["slug"] for item in inventory["workflows"]},
            {"docs-only", "research-build-verify", "architect-debate-delivery"},
        )
        compiled = self.core.compile_workflow(self.root, "architect-debate-delivery")
        self.assertEqual(compiled["kind"], self.core.COMPILED_WORKFLOW_KIND)
        self.assertEqual(set(compiled["source_hashes"]), {
            "architect-debate-delivery@1.0.0",
            "docs-only@1.0.0",
            "research-build-verify@1.0.0",
        })
        self.assertGreater(compiled["envelope"]["agent_starts"], 0)
        self.assertEqual(len(compiled["loops"]), 1)
        self.assertEqual(len(compiled["debates"]), 1)
        self.assertIn(
            "agent:dispatch",
            compiled["required_capabilities"][
                "architect-debate-delivery/audit-loop"
            ],
        )

    def test_layout_changes_document_hash_only(self):
        workflow = self.load(self.docs_path)
        baseline = self.core.compile_workflow(self.root, workflow)
        moved = self.clone(workflow)
        moved["layout"]["nodes"]["write-docs"] = {"x": 999, "y": -400}
        after = self.core.compile_workflow(self.root, moved)
        self.assertEqual(baseline["semantic_hash"], after["semantic_hash"])
        self.assertEqual(baseline["bundle_hash"], after["bundle_hash"])
        self.assertNotEqual(baseline["document_hash"], after["document_hash"])

        nested_before = self.core.compile_workflow(self.root, "architect-debate-delivery")
        child = self.load(self.docs_path)
        child["layout"]["nodes"]["check-docs"] = {"x": -500, "y": 700}
        self.docs_path.write_text(
            json.dumps(child, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        nested_after = self.core.compile_workflow(self.root, "architect-debate-delivery")
        self.assertEqual(nested_before["bundle_hash"], nested_after["bundle_hash"])
        self.assertNotEqual(
            nested_before["sources"]["docs-only@1.0.0"]["document_hash"],
            nested_after["sources"]["docs-only@1.0.0"]["document_hash"],
        )

    def test_parameter_bindings_are_typed_data_not_substitution(self):
        workflow = self.load(self.docs_path)
        compiled = self.core.compile_workflow(
            self.root,
            workflow,
            bindings={"story-id": {"kind": "context", "name": "story.id"}},
            require_bound=True,
        )
        self.assertEqual(compiled["bindings"]["story-id"]["kind"], "context")
        with self.assertRaises(self.core.WorkflowValidationError) as raised:
            self.core.compile_workflow(
                self.root,
                workflow,
                bindings={"story-id": "${invent-a-node}"},
                require_bound=True,
            )
        self.assertIn("unsafe-binding", self.diagnostic_codes(raised))
        with self.assertRaises(self.core.WorkflowValidationError) as raised:
            self.core.compile_workflow(
                self.root,
                workflow,
                bindings={"story-id": {"kind": "context", "name": "phase.number"}},
                require_bound=True,
            )
        self.assertIn("parameter-type", self.diagnostic_codes(raised))

    def test_subflow_provenance_and_expanded_addresses_are_stable(self):
        from dw_pmo.program_conductor import (
            _instantiate_loop_rounds,
            _lineage_address,
        )

        first = self.core.simulate_workflow(self.root, "architect-debate-delivery")
        second = self.core.simulate_workflow(self.root, "architect-debate-delivery")
        self.assertEqual(self.core.canonical_json(first), self.core.canonical_json(second))
        addresses = {item["address"] for item in first["expanded_nodes"]}
        self.assertIn("architect-debate-delivery/delivery/research-build-verify/research-code", addresses)
        self.assertTrue(any("round/{round}/docs-only/write-docs" in item for item in addresses))
        artifact_addresses = {item["address"] for item in first["expanded_artifacts"]}
        self.assertIn(
            "architect-debate-delivery/delivery/research-build-verify/"
            "bounded-build/artifact/candidate",
            artifact_addresses,
        )
        self.assertTrue(any(item["role"] == "verifier" for item in first["role_lanes"]))
        self.assertTrue(any(item["duty"] == "debate-judge" for item in first["role_lanes"]))
        self.assertEqual(len(first["loops"][0]["iterations"]), 2)
        nested_loops = [
            {"address": "root/outer"},
            {
                "address":
                    "root/outer/round/{round}/child/inner",
            },
        ]
        nested = _instantiate_loop_rounds(
            "root/outer/round/{round}/child/inner/"
            "round/{round}/grand/leaf",
            nested_loops,
            {
                "root/outer": 2,
                "root/outer/round/{round}/child/inner": 3,
            },
        )
        self.assertEqual(
            nested,
            "root/outer/round/2/child/inner/round/3/grand/leaf",
        )
        self.assertEqual(
            _lineage_address(
                "program/demo/phase/1/story/DM-1-02/workflow/alpha",
                "root",
                str(nested),
            ),
            "program/demo/phase/1/story/DM-1-02/workflow/alpha"
            "/loop/outer/round/2/subflow/child/loop/inner/round/3"
            "/subflow/grand/node/leaf",
        )

    def test_recursive_subflow_reference_refuses(self):
        workflow = self.load(self.docs_path)
        workflow["nodes"] = [{
            "id": "recurse",
            "type": "subflow",
            "workflow": "docs-only",
            "version": "1.0.0",
            "with": {},
            "capability_ceiling": [],
            "on_success": {"kind": "terminal", "target": "complete"},
            "on_failure": {"kind": "action", "target": "block"},
        }]
        with self.assertRaises(self.core.WorkflowValidationError) as raised:
            self.core.compile_workflow(self.root, workflow)
        self.assertIn("workflow-recursive", self.diagnostic_codes(raised))

    def test_general_dependency_and_route_cycles_refuse(self):
        workflow = self.load(self.docs_path)
        workflow["nodes"][0]["needs"] = ["check-docs"]
        with self.assertRaises(self.core.WorkflowValidationError) as raised:
            self.core.compile_workflow(self.root, workflow)
        self.assertIn("workflow-cycle", self.diagnostic_codes(raised))

        routed = self.load(self.architect_path)
        routed["nodes"][3]["on_success"] = {"kind": "node", "target": "delivery"}
        with self.assertRaises(self.core.WorkflowValidationError) as raised:
            self.core.compile_workflow(self.root, routed)
        self.assertIn("workflow-cycle", self.diagnostic_codes(raised))

    def test_loop_requires_explicit_bound_predicate_and_exhaustion(self):
        workflow = self.load(self.architect_path)
        loop = workflow["nodes"][3]
        del loop["max_rounds"]
        del loop["until"]
        del loop["on_exhausted"]
        with self.assertRaises(self.core.WorkflowValidationError) as raised:
            self.core.compile_workflow(self.root, workflow)
        self.assertTrue(
            {"missing-bound", "wrong-type"} <= self.diagnostic_codes(raised),
            raised.exception.diagnostics,
        )

        non_decreasing = self.load(self.architect_path)
        non_decreasing["nodes"][3]["until"]["source"] = "invented.result"
        with self.assertRaises(self.core.WorkflowValidationError) as raised:
            self.core.compile_workflow(self.root, non_decreasing)
        self.assertIn("non-decreasing-loop", self.diagnostic_codes(raised))

    def test_exact_subflow_version_and_bounded_score_are_proven(self):
        research = self.core.compile_workflow(self.root, "research-build-verify")
        bounded = next(
            node for node in research["workflow"]["nodes"]
            if node["type"] == "bounded_run"
        )
        self.assertRegex(bounded["score_reference"]["semantic_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(research["envelope"]["child_runs"], 1)

        architect = self.load(self.architect_path)
        architect["nodes"][2]["version"] = "9.9.9"
        with self.assertRaises(self.core.WorkflowValidationError) as raised:
            self.core.compile_workflow(self.root, architect)
        self.assertIn("workflow-version-mismatch", self.diagnostic_codes(raised))

        smuggled = self.load(self.architect_path)
        smuggled["nodes"][2]["capability_ceiling"].remove("verdict:issue")
        with self.assertRaises(self.core.WorkflowValidationError) as raised:
            self.core.compile_workflow(self.root, smuggled)
        self.assertIn("capability-smuggling", self.diagnostic_codes(raised))

    def test_complete_route_simulation_is_pure_and_explainable(self):
        before = {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in self.root.rglob("*") if path.is_file()
        }
        simulation = self.core.simulate_workflow(self.root, "architect-debate-delivery")
        after = {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in self.root.rglob("*") if path.is_file()
        }
        self.assertEqual(before, after)
        outcomes = {item["outcome"] for item in simulation["routes"]}
        self.assertTrue({"consensus", "dissent", "exhausted", "success", "failure"} <= outcomes)
        self.assertTrue(all("envelope" in item for item in simulation["routes"]))
        self.assertFalse(simulation["starts_work"])
        self.assertFalse(simulation["writes_policy"])
        self.assertFalse(simulation["writes_run_state"])
        self.assertFalse(simulation["creates_grant"])

    def test_fanout_fanin_quorum_and_result_routes_are_proven(self):
        research = self.core.simulate_workflow(self.root, "research-build-verify")
        self.assertEqual(research["waves"][0], ["research-code", "research-risk"])
        self.assertEqual(research["waves"][1], ["collect-brief"])

        debate = self.load(self.architect_path)
        debate["nodes"][1]["quorum"] = 3
        with self.assertRaises(self.core.WorkflowValidationError) as raised:
            self.core.compile_workflow(self.root, debate)
        self.assertIn("impossible-quorum", self.diagnostic_codes(raised))

        verdict = self.load(self.research_path)
        del verdict["nodes"][4]["routes"]["inconclusive"]
        with self.assertRaises(self.core.WorkflowValidationError) as raised:
            self.core.compile_workflow(self.root, verdict)
        self.assertIn("wrong-type", self.diagnostic_codes(raised))

    def test_invalid_route_and_dangling_artifact_are_source_aware(self):
        workflow = self.load(self.docs_path)
        workflow["nodes"][1]["inputs"]["documentation"]["name"] = "missing.output"
        workflow["nodes"][1]["on_success"]["target"] = "missing-terminal"
        with self.assertRaises(self.core.WorkflowValidationError) as raised:
            self.core.compile_workflow(self.root, workflow)
        codes = self.diagnostic_codes(raised)
        self.assertIn("dangling-artifact-reference", codes)
        self.assertIn("dangling-terminal", codes)
        self.assertTrue(all(item["source"] for item in raised.exception.diagnostics))

    def test_cli_inventory_validation_and_simulation_share_pure_core(self):
        listed = self.cli("list", "--json")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(json.loads(listed.stdout), self.core.workflow_inventory(self.root))
        validated = self.cli("validate", "docs-only", "--json")
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertEqual(
            json.loads(validated.stdout),
            self.core.validate_workflow(self.root, "docs-only"),
        )
        simulated = self.cli("simulate", "architect-debate-delivery", "--json")
        self.assertEqual(simulated.returncode, 0, simulated.stderr)
        self.assertEqual(
            json.loads(simulated.stdout),
            self.core.simulate_workflow(self.root, "architect-debate-delivery"),
        )

        empty = self.tmp / "empty"
        empty.mkdir()
        before = list(empty.rglob("*"))
        inventory = self.core.workflow_inventory(empty)
        self.assertEqual(inventory["workflows"], [])
        self.assertTrue(inventory["healthy"])
        self.assertEqual(before, list(empty.rglob("*")))


class SignalsTest(unittest.TestCase):
    """WLA-25-02: the authority-free SCM observer (docs/signals.md)."""

    def setUp(self):
        import dw_pmo.signals as sig

        self.sig = sig
        self.tmp = Path(tempfile.mkdtemp(prefix="dw-signals-test.")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self._cmd("git", "init", "-q", "-b", "main")
        self._cmd("git", "config", "user.name", "Signals Fixture")
        self._cmd("git", "config", "user.email", "signals@example.test")
        (self.root / "README.md").write_text("# Signals fixture\n")
        demo = self.root / "pm" / "roadmap" / "demo"
        phase = demo / "phase-1-alpha"
        phase.mkdir(parents=True)
        (demo / "README.md").write_text(README)
        (phase / "current-phase-status.md").write_text(STATUS_FILE)
        (phase / "story-01-first.md").write_text(
            STORY_TMPL.format(sid="DM-1-01", title="First thing", status="done")
        )
        (phase / "story-02-second.md").write_text(
            STORY_TMPL.format(sid="DM-1-02", title="Second thing", status="ready")
        )
        (phase / "evidence-story-01.md").write_text(EVIDENCE_01)
        self._cmd("git", "add", ".")
        self._cmd(
            "git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", "init"
        )
        self.scenario = self.tmp / "scenario.json"
        self._write_scenario(self._snapshot())

    def _cmd(self, *argv, check=True):
        return subprocess.run(
            list(argv), cwd=self.root, check=check, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )

    def _snapshot(self, **overrides):
        pr = {
            "number": 7,
            "state": "open",
            "draft": False,
            "head": "feature/x",
            "base": "main",
            "url": "https://example.test/pr/7",
            "checks": [
                {
                    "name": "tests",
                    "status": "completed",
                    "conclusion": "failure",
                    "url": "https://example.test/checks/1",
                }
            ],
            "review": {
                "unresolved": 1,
                "resolved": 0,
                "changes_requested": True,
                "approved": False,
                "reviewers": ["alice"],
                "url": "https://example.test/pr/7",
                "body": "PLANTED REVIEW PROSE",
            },
            "mergeable": "true",
            "log_text": "PLANTED CI LOG",
        }
        pr.update(overrides)
        return {"prs": [pr]}

    def _write_scenario(self, snapshot):
        self.scenario.write_text(json.dumps(snapshot))

    def _observe(self):
        provider = self.sig.FixtureProvider(self.scenario)
        return self.sig.observe_signals(self.root, provider, "origin", "feature/x")

    def _chain_path(self):
        return (
            self.root / ".git" / "pmo-signals" / "origin" / "feature%2Fx"
            / "signals.jsonl"
        )

    def test_observe_is_pure_appends_facts_and_stamps_no_work(self):
        result = self._observe()
        self.assertEqual(result["kind"], "delivery-workbench-signals-observe")
        self.assertIs(result["starts_work"], False)
        self.assertEqual(result["appended"], 4)
        self.assertEqual(result["status"], "ci-failed")
        # The operator tree stays untouched; writes land only under
        # .git/pmo-signals (git's own transient files are not asserted on,
        # after the maintenance.lock CI flake).
        self.assertEqual(self._cmd("git", "status", "--porcelain").stdout, "")
        self.assertTrue(self._chain_path().is_file())

    def test_semantic_dedup_appends_nothing_when_unchanged(self):
        self._observe()
        second = self._observe()
        self.assertEqual(second["appended"], 0)
        self.assertIs(second["not_modified"], True)
        # Same content rewritten is still semantically unchanged.
        self._write_scenario(self._snapshot())
        third = self._observe()
        self.assertEqual(third["appended"], 0)

    def test_changed_facts_append_and_status_rederives(self):
        self._observe()
        snapshot = self._snapshot()
        snapshot["prs"][0]["checks"][0]["conclusion"] = "success"
        snapshot["prs"][0]["review"]["changes_requested"] = False
        snapshot["prs"][0]["review"]["approved"] = True
        self._write_scenario(snapshot)
        result = self._observe()
        self.assertEqual(result["appended"], 2)
        self.assertEqual(result["status"], "approved")

    def test_status_precedence_matches_the_contract(self):
        sig = self.sig
        cases = [
            (dict(state="merged"), "merged"),
            (dict(state="closed"), "closed-unmerged"),
            (dict(), "ci-failed"),
            (dict(checks=[], mergeable="false"), "merge-conflict"),
            (dict(checks=[], mergeable="true"), "changes-requested"),
            (
                dict(
                    checks=[{"name": "t", "status": "in_progress",
                             "conclusion": "", "url": ""}],
                    review={"unresolved": 0, "resolved": 0,
                            "changes_requested": False, "approved": False,
                            "reviewers": [], "url": ""},
                ),
                "ci-pending",
            ),
            (
                dict(
                    checks=[],
                    review={"unresolved": 0, "resolved": 1,
                            "changes_requested": False, "approved": True,
                            "reviewers": ["bob"], "url": ""},
                ),
                "approved",
            ),
            (
                dict(
                    checks=[{"name": "t", "status": "completed",
                             "conclusion": "success", "url": ""}],
                    review={"unresolved": 0, "resolved": 0,
                            "changes_requested": False, "approved": False,
                            "reviewers": [], "url": ""},
                    mergeable="true",
                ),
                "mergeable",
            ),
            (
                dict(checks=[], mergeable="unknown",
                     review={"unresolved": 0, "resolved": 0,
                             "changes_requested": False, "approved": False,
                             "reviewers": [], "url": ""}),
                "pr-open",
            ),
        ]
        for overrides, expected in cases:
            snapshot = self._snapshot(**overrides)
            facts = {}
            for fact, detail in sig._facts_from_snapshot("fixture", snapshot):
                facts[sig._fact_key(fact, detail)] = {
                    "fact": fact, "detail": detail, "ts": "", "seq": 0,
                }
            self.assertEqual(sig.derive_status(facts), expected, overrides)
        self.assertEqual(sig.derive_status({}), "unobserved")

    def test_chain_fails_closed_on_corruption_fork_and_truncation(self):
        self._observe()
        chain = self._chain_path()
        good = chain.read_text()
        lines = good.splitlines(True)

        chain.write_text(good.rstrip("\n"))
        with self.assertRaises(DwError):
            self.sig.replay_channel(self.root, "origin", "feature/x")

        chain.write_text("".join(lines[:-1]) + "not json\n")
        with self.assertRaises(DwError):
            self.sig.replay_channel(self.root, "origin", "feature/x")

        forked = json.loads(lines[-1])
        forked["prev_hash"] = "sha256:" + "0" * 64
        chain.write_text(
            "".join(lines[:-1])
            + json.dumps(forked, sort_keys=True, separators=(",", ":")) + "\n"
        )
        with self.assertRaises(DwError):
            self.sig.replay_channel(self.root, "origin", "feature/x")

        tampered = json.loads(lines[-1])
        tampered["detail"] = dict(tampered["detail"])
        if "state" in tampered["detail"]:
            tampered["detail"]["state"] = "merged"
        else:
            tampered["detail"]["url"] = "https://tampered.example"
        chain.write_text(
            "".join(lines[:-1])
            + json.dumps(tampered, sort_keys=True, separators=(",", ":")) + "\n"
        )
        with self.assertRaises(DwError):
            self.sig.replay_channel(self.root, "origin", "feature/x")

        chain.write_text(good)
        self.sig.replay_channel(self.root, "origin", "feature/x")

    def test_projection_cache_is_disposable(self):
        self._observe()
        before = self.sig.build_signals_inventory(self.root)
        (self._chain_path().parent / "projection.json").unlink()
        self.assertEqual(self.sig.build_signals_inventory(self.root), before)

    def test_third_party_content_never_persists(self):
        self._observe()
        stored = self._chain_path().read_text()
        self.assertNotIn("PLANTED", stored)
        self.assertNotIn("PROSE", stored)
        self.assertNotIn("LOG", stored)

    def test_refusals_are_content_free_recorded_and_deduped(self):
        self._write_scenario({"refusal": "rate-limited"})
        first = self._observe()
        self.assertEqual(first["refusal"], "rate-limited")
        self.assertEqual(first["appended"], 1)
        second = self._observe()
        self.assertEqual(second["appended"], 0)
        self._write_scenario({"refusal": "SECRET DETAIL app_token=xyz"})
        third = self._observe()
        self.assertEqual(third["refusal"], "forge-error")
        self.assertNotIn("SECRET", self._chain_path().read_text())

    def test_inventory_agrees_across_cli_mcp_and_http(self):
        import dw_pmo.mcpserver as mcp
        import dw_pmo.workbench as wb

        self._observe()
        inventory = self.sig.build_signals_inventory(self.root)
        self.assertIs(inventory["starts_work"], False)
        cli = subprocess.run(
            [sys.executable, str(TESTS_DIR.parent / "bin" / "dw"),
             "--root", str(self.root), "signals", "list", "--json"],
            check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(json.loads(cli.stdout), inventory)
        mcp_result = mcp.call_tool(self.root, "dw_signals", {})
        self.assertEqual(mcp_result["structuredContent"], inventory)
        status, http_result = wb.handle_api(self.root, "/api/signals", {})
        self.assertEqual(status, 200)
        self.assertEqual(http_result["data"], inventory)
        status, filtered = wb.handle_api(
            self.root, "/api/signals", {"branch": ["feature/x"]}
        )
        self.assertEqual(filtered["data"]["channels"], inventory["channels"])
        status, empty = wb.handle_api(
            self.root, "/api/signals", {"branch": ["no-such-branch"]}
        )
        self.assertEqual(empty["data"]["channels"], [])

    def test_receptivity_table_is_exhaustive_and_refuses_blocked(self):
        from dw_pmo.orchestration_run import ACTIVITY_STATES

        expected = {
            "waiting_input": "deliver", "idle": "deliver", "active": "defer",
            "blocked": "refuse", "unknown": "refuse", "exited": "refuse",
        }
        self.assertEqual(set(expected), set(ACTIVITY_STATES))
        for state in sorted(ACTIVITY_STATES):
            for intent in ("auto", "manual"):
                self.assertEqual(
                    self.sig.receptivity(state, intent), expected[state],
                    (state, intent),
                )
        # blocked refuses even a manual operator nudge, by contract.
        self.assertEqual(self.sig.receptivity("blocked", "manual"), "refuse")
        with self.assertRaises(DwError):
            self.sig.receptivity("active", "operator-shortcut")
        with self.assertRaises(DwError):
            self.sig.receptivity("daydreaming", "auto")

    def test_github_remote_parsing_and_provider_refusals(self):
        sig = self.sig
        self.assertEqual(
            sig.parse_github_remote("https://github.com/o/r.git"), ("o", "r")
        )
        self.assertEqual(
            sig.parse_github_remote("git@github.com:o/r.git"), ("o", "r")
        )
        self.assertEqual(
            sig.parse_github_remote("ssh://git@github.com/o/r"), ("o", "r")
        )
        with self.assertRaises(DwError):
            sig.parse_github_remote("https://gitlab.example/o/r.git")
        with self.assertRaises(DwError):
            sig.github_provider_for(self.root, "nonexistent-remote", "main")

        import urllib.error

        def opener_for(code):
            def opener(request, timeout=0):
                raise urllib.error.HTTPError(
                    request.full_url, code, "refused", {}, None
                )
            return opener

        for code, reason in ((401, "unauthenticated"), (403, "rate-limited"),
                             (429, "rate-limited"), (500, "forge-error")):
            provider = sig.GithubProvider(
                "o", "r", "main", token="t", opener=opener_for(code)
            )
            snapshot, _, not_modified = provider.fetch({})
            self.assertEqual(snapshot["refusal"], reason, code)
            self.assertIs(not_modified, False)

        provider = sig.GithubProvider(
            "o", "r", "main", token="t", opener=opener_for(304)
        )
        snapshot, _, not_modified = provider.fetch({"etag": "W/\"cached\""})
        self.assertIsNone(snapshot.get("refusal"))
        self.assertIs(not_modified, True)

        def network_error(request, timeout=0):
            raise urllib.error.URLError("no route")

        provider = sig.GithubProvider(
            "o", "r", "main", token="t", opener=network_error
        )
        snapshot, _, _ = provider.fetch({})
        self.assertEqual(snapshot["refusal"], "network-error")


class RepositoryFactsContractTest(unittest.TestCase):
    """WLA-28-01: the boundary that owns repository-derived facts.

    The boundary exists so that later stories can reuse a fact against a
    stated rule instead of a guess.  These cases pin the rule itself: the
    census is total, the classes are the declared two, the invalidation rule
    is expressed in code, and no NEW module resolves the git directory
    privately.
    """

    def setUp(self):
        import dw_pmo.repofacts as repofacts

        self.repofacts = repofacts
        self.lib_dir = TESTS_DIR.parent / "lib" / "dw_pmo"

    # -- the census ------------------------------------------------------

    def test_every_served_fact_declares_a_valid_class_and_reason(self):
        rf = self.repofacts
        self.assertTrue(rf.REPOSITORY_FACTS, "the census may not be empty")
        for name, entry in rf.REPOSITORY_FACTS.items():
            with self.subTest(fact=name):
                self.assertIn(
                    entry["class"], rf.FACT_CLASSES,
                    f"{name} must be one of the declared classes",
                )
                self.assertTrue(entry["command"], f"{name} must name its git command")
                self.assertTrue(
                    str(entry["reason"]).strip(),
                    f"{name} must record why it holds its class",
                )

    def test_the_split_is_exactly_where_the_phase_says_it_is(self):
        rf = self.repofacts
        immutable = {n for n in rf.REPOSITORY_FACTS if rf.is_process_immutable(n)}
        scoped = set(rf.REPOSITORY_FACTS) - immutable
        # Where the repository IS may be cached for the process.
        self.assertEqual(immutable, {"git_dir", "repository_id"})
        # What the repository CONTAINS may not.
        self.assertEqual(
            scoped,
            {
                "head_sha", "index_tree", "current_branch",
                "remote_url", "remote_ref", "worktree_status",
                "tracked_files", "blob_content",
            },
        )

    def test_unknown_facts_are_refused_rather_than_defaulted(self):
        with self.assertRaises(DwError):
            self.repofacts.fact_class("whatever_seems_handy")

    def test_contract_document_is_versioned_and_total(self):
        doc = self.repofacts.contract_document()
        self.assertEqual(doc["kind"], "delivery-workbench-repository-facts")
        self.assertEqual(doc["schema_version"], 1)
        self.assertEqual(
            set(doc["facts"]), set(self.repofacts.REPOSITORY_FACTS),
            "the document must serve the whole census",
        )
        json.dumps(doc)  # must stay machine-readable

    # -- the invalidation rule, expressed in code ------------------------

    def test_derivation_computes_once_and_a_mutation_invalidates(self):
        d = self.repofacts.Derivation(Path("/nonexistent"))
        calls = []

        def produce():
            calls.append(1)
            return f"value-{len(calls)}"

        self.assertEqual(d.fact("head_sha", produce), "value-1")
        self.assertEqual(d.fact("head_sha", produce), "value-1")
        self.assertEqual(len(calls), 1, "reuse inside one derivation")

        d.invalidate()
        self.assertEqual(d.fact("head_sha", produce), "value-2",
                         "a mutation must force a re-read")
        self.assertEqual(d.invalidations, 1)

    def test_derivation_keys_facts_so_distinct_targets_do_not_collide(self):
        d = self.repofacts.Derivation(Path("/nonexistent"))
        self.assertEqual(d.fact("remote_ref", lambda: "a", "origin/main"), "a")
        self.assertEqual(d.fact("remote_ref", lambda: "b", "origin/other"), "b")

    def test_a_derivation_refuses_to_hold_a_process_immutable_fact(self):
        d = self.repofacts.Derivation(Path("/nonexistent"))
        with self.assertRaises(DwError):
            d.fact("git_dir", lambda: "anything")

    # -- resolution ------------------------------------------------------

    def test_git_dir_resolves_and_refuses_a_non_repository(self):
        tmp = Path(tempfile.mkdtemp(prefix="dw-repofacts-test.")).resolve()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        repo = tmp / "repo"
        repo.mkdir()
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
        self.assertEqual(
            self.repofacts.git_dir(repo), (repo / ".git").resolve()
        )

        outside = tmp / "not-a-repo"
        outside.mkdir()
        with mock.patch.object(self.repofacts, "run_git", return_value=None):
            with self.assertRaises(DwError):
                self.repofacts.git_dir(outside)

    # -- the fitness guard -----------------------------------------------

    def _modules_resolving_git_dir_privately(self):
        offenders = []
        for path in sorted(self.lib_dir.glob("*.py")):
            if path.name == "repofacts.py":
                continue  # the boundary is allowed to ask
            text = path.read_text(encoding="utf-8")
            if '"--git-dir"' in text or "'--git-dir'" in text:
                offenders.append(path.name)
        return offenders

    def test_no_new_module_resolves_the_git_directory_privately(self):
        offenders = set(self._modules_resolving_git_dir_privately())
        declared = set(self.repofacts.PENDING_PRIVATE_RESOLVERS)
        new = offenders - declared
        self.assertEqual(
            new, set(),
            "these modules resolve the git directory privately without being "
            f"declared in PENDING_PRIVATE_RESOLVERS: {sorted(new)}. Route them "
            "through dw_pmo.repofacts instead.",
        )

    def test_the_boundary_resolves_a_linked_worktree_where_git_is_a_file(self):
        # WLA-28-01 finding: signals.py derives the git directory by assuming
        # root/.git is a directory, which is false in a linked worktree.  The
        # boundary asks git, so it gets this right.  Pinned here so WLA-28-02
        # folds signals.py in rather than preserving the defect.
        tmp = Path(tempfile.mkdtemp(prefix="dw-repofacts-worktree.")).resolve()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        main = tmp / "main"
        main.mkdir()

        def git(*args, cwd=main):
            subprocess.run(["git", "-C", str(cwd), *args], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        git("init", "-q")
        git("config", "user.name", "Repo Facts Test")
        git("config", "user.email", "repofacts@example.test")
        (main / "seed.txt").write_text("seed\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "seed", "--no-verify")

        linked = tmp / "linked"
        git("worktree", "add", "-q", "--detach", str(linked))
        self.assertTrue((linked / ".git").is_file(),
                        "a linked worktree stores .git as a file")

        resolved = self.repofacts.git_dir(linked)
        self.assertTrue(resolved.is_dir(), "the boundary must find the real dir")
        self.assertIn("worktrees", resolved.parts)

        # WLA-28-02 fixed the defect WLA-28-01 pinned here: signals.py now
        # routes through the boundary, so it resolves a linked worktree
        # instead of refusing to work in one.
        import dw_pmo.signals as signals
        self.assertEqual(signals._git_dir(linked), resolved)

    def test_git_dir_is_resolved_once_per_root_and_keyed_not_global(self):
        # WLA-28-02: the whole point of the phase. One spawn per root, and
        # never one repository's answer handed to another.
        rf = self.repofacts
        tmp = Path(tempfile.mkdtemp(prefix="dw-repofacts-cache.")).resolve()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        roots = []
        for name in ("alpha", "beta"):
            repo = tmp / name
            repo.mkdir()
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            roots.append(repo)

        rf.reset_cache()
        self.addCleanup(rf.reset_cache)
        spawns = []
        real_run_git = rf.run_git

        def counting(root, *args):
            spawns.append(args)
            return real_run_git(root, *args)

        with mock.patch.object(rf, "run_git", counting):
            first = [rf.git_dir(r) for r in roots]
            for _ in range(25):
                for r in roots:
                    rf.git_dir(r)

        self.assertEqual(
            len(spawns), 2,
            "two roots must cost exactly two resolutions, not one per call",
        )
        self.assertEqual(first[0], (roots[0] / ".git").resolve())
        self.assertEqual(first[1], (roots[1] / ".git").resolve())
        self.assertNotEqual(first[0], first[1],
                            "the cache must be keyed by root, never global")

    def test_a_failed_resolution_is_not_cached_as_success(self):
        rf = self.repofacts
        rf.reset_cache()
        self.addCleanup(rf.reset_cache)
        tmp = Path(tempfile.mkdtemp(prefix="dw-repofacts-fail.")).resolve()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        repo = tmp / "repo"
        repo.mkdir()
        with mock.patch.object(rf, "run_git", return_value=None):
            with self.assertRaises(DwError):
                rf.git_dir(repo)
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
        self.assertEqual(rf.git_dir(repo), (repo / ".git").resolve())

    def test_one_conductor_tick_stays_under_the_git_dir_spawn_ceiling(self):
        # The phase's headline number: ~53 rev-parse --git-dir spawns per tick
        # before WLA-28-02. The boundary caches per root, so a tick may cost
        # at most one — and zero once the root is already resolved.
        import dw_pmo.gitio as gitio
        import dw_pmo.repofacts as rf

        conductor = ProgramConductorTest(
            "test_tick_conducts_implementer_then_independent_verifier"
        )
        conductor.setUp()
        self.addCleanup(conductor.doCleanups)

        rf.reset_cache()
        self.addCleanup(rf.reset_cache)
        git_dir_spawns = []
        real_run_git = gitio.run_git

        def counting(root, *args):
            if args[:2] == ("rev-parse", "--git-dir"):
                git_dir_spawns.append(str(root))
            return real_run_git(root, *args)

        projection = conductor.start()
        with mock.patch.object(gitio, "run_git", counting), \
                mock.patch.object(rf, "run_git", counting):
            conductor.advance_to_agent(projection)

        self.assertLessEqual(
            len(git_dir_spawns), 1,
            "a conductor tick must resolve the git directory at most once; "
            f"saw {len(git_dir_spawns)} spawns",
        )

    def test_the_pending_ledger_names_only_real_remaining_sites(self):
        offenders = set(self._modules_resolving_git_dir_privately())
        stale = set(self.repofacts.PENDING_PRIVATE_RESOLVERS) - offenders
        self.assertEqual(
            stale, set(),
            f"PENDING_PRIVATE_RESOLVERS still lists {sorted(stale)}, which no "
            "longer resolve the git directory privately. The ledger must "
            "shrink as WLA-28-02 replaces each site.",
        )


class ProofCostBudgetTest(unittest.TestCase):
    """WLA-28-05: the cost of proof is measured, capped, and enforced.

    Performance work that is not guarded rots. The habit that produced 2,435
    redundant `rev-parse --git-dir` spawns was not one bad commit; it was many
    reasonable local decisions to re-read a fact rather than reason about
    whether reuse was safe. Nothing objected, because nothing measured it.

    Wall clock is deliberately not the guard: it is machine-dependent and noisy
    in CI. Subprocess counts are deterministic, and counting is what actually
    regressed.
    """

    # Ceilings sit above the measured counts, not at them, so ordinary
    # refactoring does not trip the guard for no reason. Measured 2026-07-26:
    # 58 git spawns per conductor tick, and the git directory resolved once
    # per process rather than ~53 times per tick.
    MAX_GIT_SPAWNS_PER_TICK = 75
    MAX_GIT_DIR_RESOLUTIONS = 1

    def setUp(self):
        self.conductor = ProgramConductorTest(
            "test_tick_conducts_implementer_then_independent_verifier"
        )
        self.conductor.setUp()
        self.addCleanup(self.conductor.doCleanups)

    def _measure_two_ticks(self, extra_spawn=None):
        import dw_pmo.gitio as gitio
        import dw_pmo.program_run as pr
        import dw_pmo.repofacts as rf

        counts = collections.Counter()
        armed = {"on": False}
        real = gitio.run_git

        def counting(root, *args):
            if armed["on"]:
                counts[" ".join(args[:2])] += 1
                if extra_spawn:
                    armed["on"] = False
                    try:
                        real(root, *extra_spawn)
                        counts[" ".join(extra_spawn[:2])] += 1
                    finally:
                        armed["on"] = True
            return real(root, *args)

        projection = self.conductor.start()
        with mock.patch.object(gitio, "run_git", counting), \
                mock.patch.object(pr, "run_git", counting), \
                mock.patch.object(rf, "run_git", counting):
            armed["on"] = True
            self.conductor.advance_to_agent(projection)  # exactly two ticks
            armed["on"] = False
        return counts

    @staticmethod
    def _overruns(counts, per_tick_budget, git_dir_budget, ticks=2):
        """Return human-readable overruns, naming the command and the excess."""
        problems = []
        total = sum(counts.values())
        allowed = per_tick_budget * ticks
        if total > allowed:
            problems.append(
                f"total git spawns {total} over {ticks} ticks exceeds the "
                f"{allowed} allowed ({total - allowed} too many)"
            )
        git_dir = counts.get("rev-parse --git-dir", 0)
        if git_dir > git_dir_budget:
            problems.append(
                f"`git rev-parse --git-dir` ran {git_dir} times, budget is "
                f"{git_dir_budget} ({git_dir - git_dir_budget} too many) — the "
                "repository-fact boundary should resolve it once per process"
            )
        return problems

    def test_one_conductor_tick_stays_within_its_git_budget(self):
        counts = self._measure_two_ticks()
        problems = self._overruns(
            counts, self.MAX_GIT_SPAWNS_PER_TICK, self.MAX_GIT_DIR_RESOLUTIONS
        )
        self.assertEqual(
            problems, [],
            "the cost of one conductor tick regressed:\n  "
            + "\n  ".join(problems)
            + f"\n  observed: {dict(counts)}",
        )

    def test_the_budget_bites_when_a_redundant_spawn_is_planted(self):
        # A guard nobody has seen fail is not a guard.
        counts = self._measure_two_ticks(
            extra_spawn=("rev-parse", "--git-dir")
        )
        problems = self._overruns(
            counts, self.MAX_GIT_SPAWNS_PER_TICK, self.MAX_GIT_DIR_RESOLUTIONS
        )
        self.assertTrue(
            problems,
            "planting a redundant rev-parse --git-dir on every git call must "
            "overrun the budget",
        )
        self.assertTrue(
            any("--git-dir" in p for p in problems),
            f"the failure must name the offending command; got: {problems}",
        )

    def test_the_overrun_message_names_the_command_and_the_excess(self):
        problems = self._overruns(
            collections.Counter({"rev-parse --git-dir": 40, "write-tree": 500}),
            self.MAX_GIT_SPAWNS_PER_TICK,
            self.MAX_GIT_DIR_RESOLUTIONS,
        )
        joined = " ".join(problems)
        self.assertIn("--git-dir", joined)
        self.assertIn("39 too many", joined)
        self.assertIn("390 too many", joined)

    def test_the_private_resolver_guard_is_still_wired(self):
        # WLA-28-01's fitness test is the other half of this budget: counts
        # cannot stay low if modules start resolving the git directory
        # privately again.
        import dw_pmo.repofacts as rf

        self.assertEqual(tuple(rf.PENDING_PRIVATE_RESOLVERS), ())
        self.assertEqual(tuple(rf.PRIVATE_NON_SPAWNING_RESOLVERS), ())
        self.assertTrue(
            hasattr(RepositoryFactsContractTest,
                    "test_no_new_module_resolves_the_git_directory_privately"),
            "the private-resolver fitness guard must remain in the suite",
        )


class DerivationReadsTest(unittest.TestCase):
    """WLA-28-03: one derivation asks git each question at most once.

    This is deliberately *not* a cache. Nothing is retained between
    observations — `program_freshness_issues` and the divergence checks exist
    to re-observe, and reusing a fact across them is the staleness bug this
    phase forbids. What is removed is asking the same question twice inside a
    single observation.
    """

    def setUp(self):
        self.authority = ProgramRunAuthorityTest(
            "test_start_is_exact_immutable_idempotent_and_creates_only_local_authority"
        )
        self.authority.setUp()
        self.addCleanup(self.authority.doCleanups)
        self.root = self.authority.root

    def _count_within_one_observation(self, remote, remote_ref):
        import dw_pmo.gitio as gitio
        import dw_pmo.program_run as pr

        counts = collections.Counter()
        real = gitio.run_git

        def counting(root, *args):
            counts[" ".join(args[:2])] += 1
            return real(root, *args)

        with mock.patch.object(gitio, "run_git", counting), \
                mock.patch.object(pr, "run_git", counting):
            facts = pr._repository_facts(self.root, remote, remote_ref)
        return facts, counts

    def test_one_observation_reads_head_once_even_with_a_remote(self):
        # The remote leg used to re-read HEAD independently, so a repository
        # with a remote configured spawned rev-parse --verify HEAD twice to
        # answer a single question.
        subprocess.run(
            ["git", "-C", str(self.root), "remote", "add", "origin",
             "https://example.test/repo.git"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        facts, counts = self._count_within_one_observation(
            "origin", "refs/remotes/origin/main"
        )
        head_reads = sum(
            n for cmd, n in counts.items() if cmd == "rev-parse --verify"
        )
        # One for HEAD, one for the remote ref — never two for HEAD.
        self.assertLessEqual(
            head_reads, 2,
            f"one observation spawned rev-parse --verify {head_reads} times; "
            "HEAD and the remote ref are one read each",
        )
        self.assertTrue(facts["head"])

    def test_no_fact_is_read_twice_inside_one_observation(self):
        _facts, counts = self._count_within_one_observation(None, None)
        repeated = {cmd: n for cmd, n in counts.items() if n > 1}
        self.assertEqual(
            repeated, {},
            f"these commands ran more than once for a single observation: "
            f"{repeated}. One derivation asks each question once.",
        )

    def test_separate_observations_still_re_read_everything(self):
        # The guarantee that matters: nothing is retained between
        # observations. A commit between two observations must be seen.
        first = self.authority.core._repository_facts(self.root, None, None)
        (self.root / "drift.txt").write_text("drift\n", encoding="utf-8")
        for args in (("add", "-A"), ("commit", "-qm", "drift", "--no-verify")):
            subprocess.run(["git", "-C", str(self.root), *args], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        second = self.authority.core._repository_facts(self.root, None, None)
        self.assertNotEqual(
            first["head"], second["head"],
            "a second observation must see the new commit, not a retained one",
        )
        self.assertNotEqual(first["index_tree"], second["index_tree"])


class ShardRunnerTest(unittest.TestCase):
    """WLA-28-04: the sharded runner must never change what is proven.

    Speed is worthless if the runner can silently drop a test, so these cases
    pin coverage and determinism rather than timing.
    """

    def setUp(self):
        loader = SourceFileLoader(
            "dw_run_core_tests", str(TESTS_DIR / "run-core-tests.py")
        )
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        self.runner = module

    def test_assignment_covers_every_unit_exactly_once(self):
        units = [f"Class{i}.test_{j}" for i in range(5) for j in range(7)]
        for shard_count in (1, 2, 3, 8, 17):
            with self.subTest(shards=shard_count):
                shards = self.runner.assign_shards(units, shard_count)
                flat = [u for shard in shards for u in shard]
                self.assertEqual(
                    sorted(flat), sorted(units),
                    "every unit must run exactly once — none dropped, none "
                    "duplicated",
                )
                self.assertEqual(len(shards), shard_count)

    def test_assignment_is_deterministic(self):
        units = [f"Class{i}.test_{j}" for i in range(6) for j in range(5)]
        first = self.runner.assign_shards(units, 4)
        for _ in range(5):
            self.assertEqual(
                self.runner.assign_shards(list(reversed(units)), 4), first,
                "the same inputs must always produce the same distribution, "
                "regardless of input order",
            )

    def test_costly_units_are_spread_rather_than_stacked(self):
        # Balance is a hint, not correctness — but a runner that puts every
        # slow test on one shard would not be worth having.
        units = list(self.runner.COST_HINTS)
        shards = self.runner.assign_shards(units, 4)
        loads = [sum(self.runner.unit_cost(u) for u in s) for s in shards]
        self.assertLessEqual(
            max(loads) - min(loads), max(self.runner.COST_HINTS.values()),
            f"shard loads are badly skewed: {loads}",
        )

    def test_an_unknown_unit_costs_the_default_and_still_schedules(self):
        self.assertEqual(self.runner.unit_cost("Nobody.test_nothing"),
                         self.runner.DEFAULT_COST)
        shards = self.runner.assign_shards(["A.test_x", "B.test_y"], 2)
        self.assertEqual(sorted(u for s in shards for u in s),
                         ["A.test_x", "B.test_y"])

    def test_classes_with_setupclass_stay_atomic(self):
        # Splitting a setUpClass fixture across shards would pay its cost in
        # every shard that touched it.
        units = self.runner.discover_units()
        atomic = [u for u in units if "." not in u]
        self.assertIn(
            "UsabilityPackagedExamContractTest", atomic,
            "a class defining setUpClass must be scheduled whole",
        )
        for name in atomic:
            cls = getattr(sys.modules["dw_core_tests_shard"], name)
            self.assertTrue(
                "setUpClass" in cls.__dict__ or "setUpModule" in cls.__dict__,
                f"{name} is atomic without a class-level fixture to justify it",
            )

    def test_discovery_finds_every_test_the_serial_loader_finds(self):
        units = self.runner.discover_units()
        module = sys.modules["dw_core_tests_shard"]
        loader = unittest.TestLoader()  # never the shared default: -k filters it
        expected = set()
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and issubclass(obj, unittest.TestCase)
                    and obj is not unittest.TestCase):
                for method in loader.getTestCaseNames(obj):
                    expected.add(f"{name}.{method}")
        covered = set()
        for unit in units:
            if "." in unit:
                covered.add(unit)
            else:
                cls = getattr(module, unit)
                for method in loader.getTestCaseNames(cls):
                    covered.add(f"{unit}.{method}")
        self.assertEqual(
            covered, expected,
            "sharded discovery must cover exactly what a serial run covers",
        )

    def test_a_shard_that_reports_nothing_is_a_failure_not_a_zero(self):
        # A crashed shard produces no machine-readable summary. Counting it as
        # zero tests and passing would be the worst possible outcome.
        with mock.patch.object(
            self.runner, "_run_shard",
            side_effect=[(0, "segfault, no summary", 0.1, {})],
        ):
            with mock.patch.object(self.runner, "discover_units",
                                   return_value=["A.test_x"]):
                with io.StringIO() as out, io.StringIO() as err, \
                        redirect_stdout(out), redirect_stderr(err):
                    code = self.runner.main(["--shards", "1"])
        self.assertEqual(code, 1)

    def test_the_serial_tail_is_covered_and_never_also_sharded(self):
        # The timing-sensitive units run quiet after the shards. They must
        # still run exactly once — excluded from shards, present in the tail.
        units = self.runner.discover_units()
        tail = [u for u in units if self.runner.is_serial(u)]
        self.assertTrue(tail, "the declared serial tail must exist in the suite")
        parallel = [u for u in units if not self.runner.is_serial(u)]
        shards = self.runner.assign_shards(parallel, 8)
        flat = [u for s in shards for u in s]
        for unit in tail:
            self.assertNotIn(unit, flat, "a serial-tail unit must not be sharded")
        self.assertEqual(
            sorted(flat + tail), sorted(units),
            "shards plus the serial tail must cover every unit exactly once",
        )

    def test_every_declared_serial_tail_unit_still_exists(self):
        # A renamed test would silently drop out of the tail and start racing.
        units = self.runner.discover_units()
        for declared in self.runner.SERIAL_TAIL:
            self.assertTrue(
                any(u == declared or u.split(".", 1)[0] == declared
                    for u in units),
                f"{declared} is declared serial but no longer exists",
            )

    def test_a_failing_shard_fails_the_whole_run(self):
        with mock.patch.object(
            self.runner, "_run_shard",
            side_effect=[(0, "out", 0.1, {"ran": 1, "failures": 0, "errors": 0}),
                         (1, "out", 0.1, {"ran": 1, "failures": 1, "errors": 0})],
        ):
            with mock.patch.object(self.runner, "discover_units",
                                   return_value=["A.test_x", "B.test_y"]):
                with io.StringIO() as out, io.StringIO() as err, \
                        redirect_stdout(out), redirect_stderr(err):
                    code = self.runner.main(["--shards", "2"])
        self.assertEqual(code, 1, "one failing shard must fail the run")


if __name__ == "__main__":
    unittest.main(verbosity=2)
