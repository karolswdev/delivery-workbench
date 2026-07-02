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


if __name__ == "__main__":
    unittest.main(verbosity=2)
