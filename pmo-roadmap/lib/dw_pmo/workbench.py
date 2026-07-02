"""The local workbench server: JSON API + static explorer shell.

Read-only in this slice (WLA-5-03): every response is derived live from
the Markdown roadmap through the same ``dw_pmo`` functions the CLI
uses — no second parser, no cache, no database, and no writes. The
server binds 127.0.0.1 only and serves exactly the repo root it was
started against. Non-GET methods are rejected; the file endpoint is
contained to the roadmap tree; static assets are contained to the
workbench directory.

Route logic lives in :func:`handle_api` (pure: path + query in,
status + envelope out) so view models are unit-testable without
sockets. Mutation endpoints arrive with WLA-5-06/07.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .api import build_context_payload, next_story, project_context
from .model import DwError, OPEN_STATUSES
from .parse import discover_phases, discover_projects, get_project, parse_story_rows
from .paths import read_text, rel, roadmap_dir
from .validate import check_project, project_warnings

SCHEMA_KIND = "delivery-workbench-workbench-response"
SCHEMA_VERSION = 1

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
}


def workbench_dir() -> Path | None:
    """The static UI directory (source layout: pmo-roadmap/workbench)."""
    candidate = Path(__file__).resolve().parents[2] / "workbench"
    return candidate if candidate.is_dir() else None


def envelope(data: object, ok: bool = True, issues: list[str] | None = None, warnings: list[str] | None = None) -> dict[str, object]:
    return {
        "kind": SCHEMA_KIND,
        "schema_version": SCHEMA_VERSION,
        "ok": ok,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": data,
        "issues": issues or [],
        "warnings": warnings or [],
    }


def _error(status: int, message: str) -> tuple[int, dict[str, object]]:
    return status, envelope({"error": message}, ok=False, issues=[message])


def _project_summary(project, root: Path) -> dict[str, object]:
    phases = discover_phases(project)
    active = 0
    status_counts: dict[str, int] = {}
    for phase in phases:
        rows = parse_story_rows(phase.path / "current-phase-status.md")
        if any(row.status in OPEN_STATUSES for row in rows):
            active += 1
        for row in rows:
            status_counts[row.status] = status_counts.get(row.status, 0) + 1
    issues = check_project(project, root)
    warnings = project_warnings(project, root)
    return {
        "slug": project.slug,
        "prefix": project.prefix,
        "path": rel(project.path, root),
        "phase_count": len(phases),
        "active_phase_count": active,
        "story_status_counts": status_counts,
        "issue_count": len(issues),
        "warning_count": len(warnings),
        "next_story": next_story(project, root),
    }


def _contained_read(root: Path, raw_path: str) -> tuple[int, dict[str, object]]:
    """Read a file strictly inside the roadmap tree (traversal-proof)."""
    if not raw_path:
        return _error(400, "missing path parameter")
    allowed = roadmap_dir(root).resolve()
    target = (root / raw_path).resolve()
    if target != allowed and allowed not in target.parents:
        return _error(403, f"path is outside the roadmap tree: {raw_path}")
    if not target.is_file():
        return _error(404, f"no such file: {raw_path}")
    return 200, envelope({"path": rel(target, root), "content": read_text(target)})


def handle_api(root: Path, path: str, query: dict[str, list[str]]) -> tuple[int, dict[str, object]]:
    parts = [part for part in path.strip("/").split("/") if part]
    try:
        if parts == ["api", "context"]:
            include_trace = query.get("trace", ["0"])[0] in {"1", "true"}
            payload = build_context_payload(root, discover_projects(root), include_trace=include_trace)
            return 200, envelope(payload)

        if parts == ["api", "projects"]:
            summaries = [_project_summary(p, root) for p in discover_projects(root)]
            return 200, envelope({"projects": summaries})

        if len(parts) == 3 and parts[:2] == ["api", "projects"]:
            project = get_project(root, parts[2])
            return 200, envelope(project_context(project, root))

        if len(parts) == 5 and parts[:2] == ["api", "projects"] and parts[3] == "phases":
            project = get_project(root, parts[2])
            context = project_context(project, root, phase_selector=parts[4])
            phase = context["phases"][0]  # type: ignore[index]
            summary_path = root / str(phase["final_summary"])  # type: ignore[index]
            detail = dict(phase)
            detail["final_summary_content"] = (
                read_text(summary_path) if summary_path.is_file() else ""
            )
            return 200, envelope(detail)

        if len(parts) == 5 and parts[:2] == ["api", "projects"] and parts[3] == "stories":
            project = get_project(root, parts[2])
            context = project_context(project, root)
            for phase in context["phases"]:  # type: ignore[union-attr]
                for story in phase["stories"]:
                    if story["story_id"] == parts[4]:
                        detail = dict(story)
                        story_path = root / str(story["story_path"])
                        detail["story_markdown"] = read_text(story_path) if story_path.is_file() else ""
                        evidence_rel = str(story["evidence_path"])
                        evidence_path = root / evidence_rel if evidence_rel else None
                        detail["evidence_markdown"] = (
                            read_text(evidence_path) if evidence_path and evidence_path.is_file() else ""
                        )
                        detail["phase_number"] = phase["number"]
                        return 200, envelope(detail)
            return _error(404, f"story not found: {parts[4]}")

        if parts == ["api", "file"]:
            return _contained_read(root, query.get("path", [""])[0])

        return _error(404, f"unknown API route: {path}")
    except DwError as err:
        return _error(400, err.message)


def create_handler(root: Path, static_dir: Path | None):
    class WorkbenchHandler(BaseHTTPRequestHandler):
        server_version = "dw-workbench"

        def log_message(self, fmt: str, *args: object) -> None:  # quiet
            pass

        def _send_json(self, status: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api"):
                status, payload = handle_api(root, parsed.path, parse_qs(parsed.query))
                self._send_json(status, payload)
                return
            self._send_static(parsed.path)

        def _send_static(self, raw_path: str) -> None:
            if static_dir is None:
                self._send_json(503, envelope({"error": "workbench UI not available; API only"}, ok=False))
                return
            name = raw_path.lstrip("/") or "index.html"
            target = (static_dir / name).resolve()
            allowed = static_dir.resolve()
            if allowed not in target.parents or not target.is_file():
                self._send_json(404, envelope({"error": f"no such asset: {raw_path}"}, ok=False))
                return
            body = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", _CONTENT_TYPES.get(target.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _reject(self) -> None:
            self._send_json(405, envelope({"error": "the workbench explorer is read-only (GET only)"}, ok=False))

        do_POST = _reject  # noqa: N815
        do_PUT = _reject  # noqa: N815
        do_DELETE = _reject  # noqa: N815
        do_PATCH = _reject  # noqa: N815

    return WorkbenchHandler


def serve(root: Path, port: int = 8377) -> None:
    """Run the workbench bound to localhost until interrupted."""
    handler = create_handler(root, workbench_dir())
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"dw-workbench: serving {root}")
    print(f"dw-workbench: http://127.0.0.1:{port}/ (read-only; Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
