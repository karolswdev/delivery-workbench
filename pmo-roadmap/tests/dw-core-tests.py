#!/usr/bin/env python3
"""Unit tests for the dw_pmo core package (WLA-5-02).

Covers parser fixtures, validation fixtures, mutation preview
idempotence (and that preview never writes), stale-target refusal at
apply time, roadmap-tree write containment, and work-log trace
fallback behavior. Stdlib only.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent / "lib"))

import dw_pmo as core
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
            wb.handle_api(self.root, "/api/context", {"trace": ["0"]})
            wb.handle_api(self.root, "/api/projects", {})
            wb.handle_api(self.root, "/api/projects/demo", {})
            wb.handle_api(self.root, "/api/projects/demo/phases/1", {})
            wb.handle_api(self.root, "/api/projects/demo/stories/DM-1-01", {})
        self.assertEqual(self._tree_checksums(), before,
                         "repeated API loads must not modify the roadmap tree")

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

        for ok in ("127.0.0.1:8377", "localhost:9000", "127.0.0.1", "localhost", "", "[::1]:8377"):
            self.assertTrue(host_allowed(ok), ok)
        for evil in ("evil.example.com", "evil.example.com:8377", "192.168.1.5:8377",
                     "attacker.test:80", "0.0.0.0:8377"):
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
            r"- \*\*Status:\*\* ([a-z| -]+)\n\s+\(the canonical story-status vocabulary[^)]*done-synonyms\n\s+accepted by tooling: ([a-z| ]+)\.",
            builder,
        )
        self.assertIsNotNone(m, "canonical vocabulary declaration missing from roadmap-builder §2.3")
        declared = {s.strip() for s in m.group(1).split("|")}
        synonyms = {s.strip() for s in m.group(2).split("|")}
        self.assertEqual(declared | synonyms, core.STORY_STATUSES,
                         "doc vocabulary and STORY_STATUSES constant have drifted")


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
        for expected in ("dw_context", "dw_next", "dw_check", "dw_doctor", "dw_verify", "dw_gate"):
            self.assertIn(expected, names)
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

    # -- error paths -----------------------------------------------------------

    def test_unknown_tool_and_unknown_params(self) -> None:
        result = self.call("dw_nonexistent")
        self.assertTrue(result["isError"])
        result = self.call("dw_check", {"projekt": "demo"})
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
        from dw_pmo import riderdocs

        agent_dir = self.REPO_ROOT / "pmo-roadmap" / "agent"
        for name in riderdocs.COMMAND_NAMES:
            self.assertEqual(
                riderdocs._EMBEDDED_COMMANDS[name],
                (agent_dir / f"{name}.md").read_text(encoding="utf-8"),
                f"embedded canon for {name} drifted from pmo-roadmap/agent",
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
