#!/usr/bin/env python3
"""Unit tests for the dw_pmo core package (WLA-5-02).

Covers parser fixtures, validation fixtures, mutation preview
idempotence (and that preview never writes), stale-target refusal at
apply time, roadmap-tree write containment, and work-log trace
fallback behavior. Stdlib only.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent / "lib"))

import dw_pmo as core
import dw_pmo.step as step_core
from dw_pmo import DwError


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
        # missioncontrol path, and the only POST routes are the two
        # guarded mutation endpoints — so no import or route edit can
        # quietly grow the belt a write path.
        import inspect

        import dw_pmo.workbench as wb
        mutation_src = inspect.getsource(wb.handle_mutation)
        self.assertNotIn("missioncontrol", mutation_src)
        post_routes = [
            line for line in mutation_src.splitlines()
            if "/api/" in line and "route ==" in line
        ]
        self.assertEqual(
            len(post_routes), 5,
            "exactly deliberate-step apply, two roadmap mutation routes, and two score-content routes may POST; "
            f"found: {post_routes}",
        )
        self.assertTrue(any('/api/step/apply' in line for line in post_routes))
        self.assertTrue(any('/api/mutations/preview' in line for line in post_routes))
        self.assertTrue(any('/api/mutations/apply' in line for line in post_routes))
        self.assertTrue(any('/api/orchestration/preview' in line for line in post_routes))
        self.assertTrue(any('/api/orchestration/apply' in line for line in post_routes))

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
            tokens.update(_re.findall(r'"([a-z]+)"', line))
        tokens.discard("api")  # the prefix, not a surface
        self.assertTrue(
            {"context", "projects", "board", "stories", "trace", "health"} <= tokens,
            tokens,
        )
        self.assertEqual(self._interop_missing(tokens, doc), [])
        # every POST route literal handle_mutation dispatches on
        mutation_source = inspect.getsource(wb.handle_mutation)
        post_routes = set(_re.findall(r'"(/api/[a-z/]+)"', mutation_source))
        self.assertEqual(
            post_routes,
            {
                "/api/step/apply",
                "/api/mutations/preview", "/api/mutations/apply",
                "/api/orchestration/preview", "/api/orchestration/apply",
            },
        )
        self.assertEqual(self._interop_missing(post_routes, doc), [])
        # the CLI's machine-readable verbs
        verbs = [
            "dw status", "dw step", "dw context", "dw state --json", "dw next", "dw board",
            "dw holds", "dw story show", "dw sessions --json", "dw events",
            "dw check", "dw gate --porcelain", "dw verify",
        ]
        self.assertEqual(self._interop_missing(verbs, doc), [])
        # the stamped models
        for stamp in ("delivery-workbench-status", "delivery-workbench-step",
                      "delivery-workbench-step-result",
                      "delivery-workbench-roadmap-context",
                      "delivery-workbench-workbench-response",
                      "delivery-workbench-board", "feed_schema"):
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
            "dw_status", "dw_step", "dw_step_apply", "dw_context", "dw_next",
            "dw_check", "dw_doctor",
            "dw_verify", "dw_gate", "dw_board", "dw_holds", "dw_story_show",
            "dw_story_status", "dw_evidence_capture", "dw_contract_new",
        ])
        for banned in ("certify", "commit", "bundle"):
            self.assertFalse(any(banned in n for n in names), names)
        for tool in tools:
            self.assertIn("inputSchema", tool)
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
        self.assertIn("status=attention", result["content"][0]["text"])

        import inspect
        source = inspect.getsource(self.mcp._tool_status)
        self.assertNotIn("verdict", source)
        self.assertNotIn("next_action", source)

    def test_step_tools_are_exact_core_adapters(self) -> None:
        preview_result = self.call("dw_step", {"project": "demo"})
        self.assertNotIn("isError", preview_result)
        preview = core.build_step(self.root, "demo")
        self.assertEqual(preview_result["structuredContent"], preview)
        self.assertIn("step=preview", preview_result["content"][0]["text"])

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

    def test_empty_roadmap_directory_is_attention_not_ready(self) -> None:
        shutil.rmtree(self.root / "pm" / "roadmap" / "demo")
        status = self.status()
        self.assertEqual(status["verdict"], "attention")
        self.assertFalse(status["roadmap"]["healthy"])
        self.assertEqual(status["next_action"]["id"], "repair-roadmap")

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
        self.assertTrue(lines[0].startswith("status=ready summary="))
        self.assertTrue(lines[1].startswith("next=start-story command="))


class StateFeedTest(unittest.TestCase):
    """WLA-13-02: the mission-control feed is schema-pinned. These
    frozen key sets ARE the stability promise — changing the shape
    without bumping FEED_SCHEMA must fail here."""

    REPO_ROOT = TESTS_DIR.parent.parent

    TOP_KEYS = ["feed_schema", "generated_at_tree", "projects"]
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
        paused = json.loads(self._dw(
            "run", "pause", projection["run_id"], "--expect",
            projection["ledger_head"], "--reason", "inspect", "--json",
        ).stdout)
        resumed = json.loads(self._dw(
            "run", "resume", projection["run_id"], "--expect",
            paused["ledger_head"], "--json",
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
