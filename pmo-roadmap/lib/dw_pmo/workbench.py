"""The local workbench server: JSON API + static explorer shell.

Every response is derived live from the Markdown roadmap through the same
``dw_pmo`` functions the CLI uses — no second parser, cache, or database.
Writes have only two explicit boundaries: the roadmap editor's guarded
preview/apply pair and the deliberate step's exact-token apply route. Neither
stages, certifies, or commits. The server binds 127.0.0.1 only and serves
exactly the repo root it was started against; file and static endpoints are
contained to their respective trees.

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

from .api import build_context_payload, handoff_summary, next_story, phase_events, project_context, story_timeline
from .model import DwError, OPEN_STATUSES, normalize_status
from .parse import discover_phases, discover_projects, get_phase, get_project, parse_story_rows, phase_is_paused
from .paths import read_text, rel, roadmap_dir, work_log_root
from .mutations import (
    apply_plan,
    plan_fingerprint,
    plan_phase_close,
    plan_phase_create,
    plan_phase_pause,
    plan_phase_resume,
    plan_story_create,
    plan_story_evidence,
    plan_story_status,
    preview_plan,
    projected_issues,
)
from .validate import check_project, health_report, project_warnings

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
    """The static UI directory.

    Source layout: pmo-roadmap/lib/dw_pmo -> pmo-roadmap/workbench.
    Installed layout: .githooks/dw_pmo -> .githooks/workbench.
    """
    here = Path(__file__).resolve()
    for candidate in (here.parents[1] / "workbench", here.parents[2] / "workbench"):
        if (candidate / "index.html").is_file():
            return candidate
    return None


def host_allowed(host_header: str) -> bool:
    """Default-deny for non-local Host headers (DNS-rebinding guard).

    A ``*.ts.net`` host (Tailscale's MagicDNS suffix) is also allowed:
    unlike an arbitrary attacker-chosen domain, a ``.ts.net`` name can
    only resolve and route to this process through the requester's
    own authenticated tailnet (WireGuard-encrypted, node-identified)
    via ``tailscale serve`` proxying to this same loopback port — the
    DNS-rebinding threat this guard exists to stop (a hostile page
    tricking a browser into sending a forged Host header at a
    public IP) has no way to reach this branch at all. Owner
    decision: the workbench is "localhost or your own tailnet,"
    not "localhost only."
    """
    raw = (host_header or "").strip().lower()
    if raw.startswith("["):  # bracketed IPv6, e.g. [::1]:8377
        host = raw.split("]")[0].lstrip("[")
    else:
        host = raw.split(":")[0]
    return host in {"127.0.0.1", "localhost", "::1", ""} or host.endswith(".ts.net")


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


def _run_error(err: DwError) -> tuple[int, dict[str, object]]:
    conflict = any(
        token in err.message
        for token in ("stale", "altered", "already consumed", "not applicable")
    )
    return _error(409 if conflict else 400, err.message)


def _project_summary(project, root: Path) -> dict[str, object]:
    phases = discover_phases(project)
    active = 0
    paused = 0
    status_counts: dict[str, int] = {}
    for phase in phases:
        rows = parse_story_rows(phase.path / "current-phase-status.md")
        if any(normalize_status(row.status) in OPEN_STATUSES for row in rows):
            active += 1
        if phase_is_paused(phase.path):
            paused += 1
        for row in rows:
            token = normalize_status(row.status)
            status_counts[token] = status_counts.get(token, 0) + 1
    issues = check_project(project, root)
    warnings = project_warnings(project, root)
    return {
        "slug": project.slug,
        "prefix": project.prefix,
        "path": rel(project.path, root),
        "phase_count": len(phases),
        "active_phase_count": active,
        "paused_phase_count": paused,
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



def _worklog_read(root: Path, raw_path: str) -> tuple[int, dict[str, object]]:
    """Read a work-log artifact strictly inside the resolved log root.

    Only the capture/digest naming patterns are served; the log content
    is returned verbatim — omitted paths stay omitted because capture
    never wrote their content in the first place."""
    if not raw_path:
        return _error(400, "missing path parameter")
    log_root = work_log_root(root).resolve()
    if not log_root.is_dir():
        return _error(404, "no work-log root exists (work logs are optional evidence)")
    # Hash routers drop the leading slash of absolute paths; accept the
    # path as given, rooted at /, or relative to the log root — but only
    # ever serve from inside the log root.
    candidates = [Path(raw_path)] if Path(raw_path).is_absolute() else [
        Path("/" + raw_path),
        log_root / raw_path,
    ]
    target = None
    for candidate in candidates:
        resolved = candidate.resolve()
        if log_root in resolved.parents:
            target = resolved
            if resolved.is_file():
                break
    if target is None:
        return _error(403, f"path is outside the work-log root: {raw_path}")
    if not (target.name.endswith("-work-summary.log") or target.name.endswith("-deferred-summary.md")):
        return _error(403, f"not a work-log artifact: {target.name}")
    if not target.is_file():
        return _error(404, f"no such work-log entry: {raw_path}")
    return 200, envelope({"path": str(target), "content": read_text(target)})

def _setup_review(root: Path, query: dict[str, list[str]]) -> dict[str, object]:
    """Load one proposal or pending preview without creating review authority."""
    from .presentation import (
        invalid_setup_review_presentation,
        setup_review_presentation,
    )
    from .repofacts import git_dir
    from .setup_lease import build_setup_plan, setup_plan_facts
    from .setup_proposal import load_proposal, validate_proposal

    raw_file = query.get("proposal_file", [""])[0].strip()
    proposal_id = query.get("proposal", [""])[0].strip()
    pending_preview = None
    display_file = raw_file
    try:
        if raw_file and proposal_id:
            raise DwError("choose either proposal_file or proposal, not both")
        if raw_file:
            candidate = Path(raw_file)
            target = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
            allowed = root.resolve()
            if target != allowed and allowed not in target.parents:
                raise DwError("setup proposal is outside the served repository: %s" % raw_file)
            try:
                proposal = load_proposal(target.read_bytes())
            except OSError as exc:
                raise DwError("setup proposal cannot be read: %s" % exc) from exc
            display_file = rel(target, root)
            facts = setup_plan_facts(
                proposal,
                build_setup_plan(root, proposal, require_reviewed=False),
            )
        else:
            pending_dir = git_dir(root) / "pmo-setup-leases" / "pending"
            if proposal_id:
                digest = proposal_id.removeprefix("setup:")
                if (
                    not proposal_id.startswith("setup:")
                    or len(digest) != 64
                    or any(character not in "0123456789abcdef" for character in digest)
                ):
                    raise DwError("setup proposal id must be an exact setup:<sha256> identifier")
                records = [pending_dir / (digest + ".json")]
            else:
                records = sorted(pending_dir.glob("*.json")) if pending_dir.is_dir() else []
                if len(records) > 1:
                    raise DwError("multiple setup previews are pending; choose one with ?proposal=setup:<sha256>")
            if not records or not records[0].is_file():
                raise DwError(
                    "no setup proposal selected; use ?proposal_file=<repository-relative-file> "
                    "or choose a pending setup preview"
                )
            try:
                record = json.loads(records[0].read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise DwError("pending setup preview cannot be read: %s" % exc) from exc
            if not isinstance(record, dict) or not isinstance(record.get("preview"), dict):
                raise DwError("pending setup preview record is malformed")
            proposal = validate_proposal(record.get("proposal"))
            pending_preview = record["preview"]
            change_rows = pending_preview.get("changes")
            if (
                pending_preview.get("kind") != "delivery-workbench-setup-preview"
                or not isinstance(change_rows, list)
                or not isinstance(pending_preview.get("proposal_hash"), str)
                or any(pending_preview.get(field) is not False for field in (
                    "starts_work", "creates_grant", "certifies", "commits",
                ))
                or any(
                    not isinstance(item, dict)
                    or not isinstance(item.get("path"), str)
                    or item.get("scope") not in {"tracked", "git-local"}
                    or item.get("action") not in {"create", "update", "unchanged"}
                    or item.get("before_hash") is not None
                    and not isinstance(item.get("before_hash"), str)
                    or not isinstance(item.get("after_hash"), str)
                    for item in change_rows
                )
            ):
                raise DwError("pending setup preview record is malformed")
            facts = {
                "proposal_hash": pending_preview["proposal_hash"],
                "changes": pending_preview["changes"],
            }
        return setup_review_presentation(
            proposal,
            facts,
            proposal_file=display_file,
            pending_preview=pending_preview,
        )
    except DwError as err:
        return invalid_setup_review_presentation(err.message, proposal_file=display_file)


def mission_control_live_layer(sessions_doc: dict) -> tuple[dict, list]:
    """The belt's live-layer decision kernel (WLA-15-02), server-side
    so it is testable here: `on_story` sessions pin to their story
    ids; every other correlation outcome stays off the belt in its
    honest bucket — ambiguous never guesses a pin (unknown beats
    guessed, the §2 rule). Returns (pins: story_id -> [session],
    off_belt: [session])."""
    pins: dict[str, list] = {}
    off_belt: list = []
    for session in sessions_doc.get("sessions") or []:
        stories = session.get("stories") or []
        if session.get("correlation") == "on_story" and stories:
            for story in stories:
                pins.setdefault(str(story.get("story_id")), []).append(session)
        else:
            off_belt.append(session)
    return pins, off_belt


def handle_api(root: Path, path: str, query: dict[str, list[str]]) -> tuple[int, dict[str, object]]:
    parts = [part for part in path.strip("/").split("/") if part]
    try:
        if parts == ["api", "presentation"]:
            from .presentation import build_presentation_catalog

            return 200, envelope(build_presentation_catalog())

        if parts == ["api", "presentation", "status"]:
            from .presentation import build_status_presentation
            from .status import build_status

            project = query.get("project", [""])[0].strip() or None
            return 200, envelope(
                build_status_presentation(build_status(root, project))
            )

        if parts == ["api", "status"]:
            from .status import build_status

            project = query.get("project", [""])[0].strip() or None
            return 200, envelope(build_status(root, project))

        if parts == ["api", "step"]:
            from .step import build_step

            project = query.get("project", [""])[0].strip() or None
            return 200, envelope(build_step(root, project))

        if parts == ["api", "orchestration"]:
            from .orchestration import score_inventory

            return 200, envelope(score_inventory(root))

        if parts == ["api", "delivery-setup"]:
            from .delivery_setup import build_delivery_setup

            project = query.get("project", [""])[0].strip() or None
            return 200, envelope(build_delivery_setup(root, project))

        if parts == ["api", "setup", "review"]:
            return 200, envelope(_setup_review(root, query))

        if parts == ["api", "program-studio"]:
            from .program_studio import build_program_studio

            return 200, envelope(build_program_studio(root))

        if parts == ["api", "programs"]:
            from .program_surface import program_summary_inventory

            return 200, envelope(program_summary_inventory(root))

        if (
            len(parts) == 4
            and parts[:2] == ["api", "programs"]
            and parts[3] == "validate"
        ):
            from .programs import find_program_path, validate_program_path

            return 200, envelope(validate_program_path(
                root, find_program_path(root, parts[2]),
            ))

        if (
            len(parts) in {3, 4}
            and parts[:2] == ["api", "programs"]
            and (len(parts) == 3 or parts[3] == "view")
        ):
            from .program_surface import build_program_view

            return 200, envelope(build_program_view(root, parts[2]))

        if (
            len(parts) == 5
            and parts[:2] == ["api", "programs"]
            and parts[3] == "act"
        ):
            from .program_surface import build_program_act_preview

            try:
                max_ticks = int(query.get("max_ticks", ["100"])[0])
                max_seconds = int(query.get("max_seconds", ["300"])[0])
            except ValueError as exc:
                raise DwError(
                    "program preview ceilings must be integers"
                ) from exc
            return 200, envelope(build_program_act_preview(
                root,
                parts[2],
                parts[4],
                reason=query.get("reason", [""])[0],
                decision=query.get("decision", [""])[0],
                request_id=query.get("request_id", [""])[0],
                max_ticks=max_ticks,
                max_seconds=max_seconds,
            ))

        if (
            len(parts) == 4
            and parts[:2] == ["api", "programs"]
            and parts[3] == "tail"
        ):
            from .program_surface import tail_program_events

            try:
                after = int(query.get("after", ["0"])[0])
                limit = int(query.get("limit", ["1000"])[0])
            except ValueError as exc:
                raise DwError(
                    "program tail cursor and limit must be integers"
                ) from exc
            return 200, envelope(tail_program_events(
                root, parts[2], after_seq=after, limit=limit
            ))

        if (
            len(parts) == 6
            and parts[:2] == ["api", "programs"]
            and parts[3] == "streams"
        ):
            from .program_surface import read_program_stream

            try:
                max_bytes = int(query.get("max_bytes", ["20000"])[0])
            except ValueError as exc:
                raise DwError("stream max_bytes must be an integer") from exc
            return 200, envelope(read_program_stream(
                root,
                parts[2],
                parts[4],
                parts[5],
                max_bytes=max_bytes,
            ))

        if len(parts) == 4 and parts[:2] == ["api", "program-studio"]:
            from .program_studio import build_studio_document

            return 200, envelope(build_studio_document(root, parts[2], parts[3]))

        if parts == ["api", "notifications"]:
            from .notifications import build_notifications

            return 200, envelope(build_notifications(root))

        if parts == ["api", "signals"]:
            from .signals import build_signals_inventory

            remote = query.get("remote", [""])[0].strip() or None
            branch = query.get("branch", [""])[0].strip() or None
            return 200, envelope(
                build_signals_inventory(root, remote=remote, branch=branch)
            )

        if (
            len(parts) == 4
            and parts[:2] == ["api", "orchestration"]
            and parts[3] in {"compiled", "simulation"}
        ):
            from .orchestration import (
                compile_score_path,
                find_score_path,
                load_score,
                simulate_score,
            )

            score_path = find_score_path(root, parts[2])
            if parts[3] == "compiled":
                return 200, envelope(compile_score_path(score_path))
            return 200, envelope(simulate_score(load_score(score_path)))

        if parts == ["api", "run-plan"]:
            from .orchestration_run import build_run_plan

            score = query.get("score", [""])[0].strip()
            story = query.get("story", [""])[0].strip()
            if not score or not story:
                raise DwError("run plan requires score and story identifiers")
            project = query.get("project", [""])[0].strip() or None
            issued_at = query.get("issued_at", [""])[0].strip() or None
            expires_at = query.get("expires_at", [""])[0].strip() or None
            standing = [
                item for item in query.get("standing_nudge", [])
                if item.strip()
            ]
            channel = query.get("signal_channel", [""])[0].strip() or None
            return 200, envelope(build_run_plan(
                root,
                score,
                project,
                story,
                issued_at=issued_at,
                expires_at=expires_at,
                standing_nudges=standing,
                signal_channel=channel,
            ))

        if parts == ["api", "runs"]:
            from .orchestration_run import run_inventory

            return 200, envelope(run_inventory(root))

        if len(parts) == 3 and parts[:2] == ["api", "runs"]:
            from .orchestration_run import replay_run

            return 200, envelope(replay_run(root, parts[2]))

        if len(parts) == 4 and parts[:2] == ["api", "runs"] and parts[3] == "view":
            from .orchestration_surface import build_run_view

            return 200, envelope(build_run_view(root, parts[2]))

        if (
            len(parts) == 5
            and parts[:2] == ["api", "runs"]
            and parts[3] == "act"
        ):
            from .orchestration_surface import build_run_act_preview

            return 200, envelope(build_run_act_preview(
                root,
                parts[2],
                parts[4],
                reason=query.get("reason", [""])[0],
                decision=query.get("decision", [""])[0],
                correlation_id=query.get("correlation_id", [""])[0],
            ))

        if (
            len(parts) == 7
            and parts[:2] == ["api", "runs"]
            and parts[3] == "streams"
        ):
            from .orchestration_surface import read_run_stream

            raw_max = query.get("max_bytes", ["20000"])[0]
            try:
                max_bytes = int(raw_max)
            except ValueError as exc:
                raise DwError("stream max_bytes must be an integer") from exc
            return 200, envelope(read_run_stream(
                root,
                parts[2],
                parts[4],
                parts[5],
                parts[6],
                max_bytes=max_bytes,
            ))

        if len(parts) == 3 and parts[:2] == ["api", "orchestration"]:
            from .orchestration import (
                compile_score,
                find_score_path,
                load_score,
                simulate_score,
                validate_score,
            )

            score_path = find_score_path(root, parts[2])
            raw = load_score(score_path)
            validation = validate_score(raw)
            compiled = compile_score(raw) if validation["valid"] else None
            simulation = simulate_score(compiled) if compiled is not None else None
            return 200, envelope({
                "name": score_path.stem,
                "path": rel(score_path, root),
                "raw": raw,
                "validation": validation,
                "compiled": compiled,
                "simulation": simulation,
                "starts_work": False,
                "writes_events": False,
            })

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

        if len(parts) == 4 and parts[:2] == ["api", "projects"] and parts[3] == "board":
            from .board import board_model

            project = get_project(root, parts[2])
            return 200, envelope(board_model(project, root))

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
            # One core (api.story_detail) serves this route, the CLI's
            # `dw story show`, and the MCP browse tool (WLA-18-02).
            from .api import story_detail

            project = get_project(root, parts[2])
            for phase in discover_phases(project):
                for row in parse_story_rows(phase.path / "current-phase-status.md"):
                    if row.story_id == parts[4]:
                        return 200, envelope(story_detail(project, phase, parts[4], root))
            return _error(404, f"story not found: {parts[4]}")

        if len(parts) == 5 and parts[:2] == ["api", "projects"] and parts[3] == "trace":
            project = get_project(root, parts[2])
            for phase in discover_phases(project):
                for row in parse_story_rows(phase.path / "current-phase-status.md"):
                    if row.story_id == parts[4]:
                        return 200, envelope(story_timeline(row, phase, project, root))
            return _error(404, f"story not found: {parts[4]}")

        if len(parts) == 6 and parts[:2] == ["api", "projects"] and parts[3] == "phases" and parts[5] == "events":
            project = get_project(root, parts[2])
            phase = get_phase(project, parts[4])
            return 200, envelope({"phase": phase.number, "events": phase_events(phase, root)})

        if parts == ["api", "worklog"]:
            return _worklog_read(root, query.get("path", [""])[0])

        if len(parts) == 5 and parts[:2] == ["api", "projects"] and parts[3] == "handoff":
            project = get_project(root, parts[2])
            for phase in discover_phases(project):
                for row in parse_story_rows(phase.path / "current-phase-status.md"):
                    if row.story_id == parts[4]:
                        return 200, envelope(handoff_summary(row, phase, project, root))
            return _error(404, f"story not found: {parts[4]}")

        if parts == ["api", "health"]:
            return 200, envelope(health_report(root, discover_projects(root)))

        if parts == ["api", "missioncontrol"]:
            # WLA-15-01: the read-only belt — the workbench is the
            # fourth consumer of the mission-control substrate, via
            # the in-process API (never re-parsing pm/roadmap here).
            # GET-only by construction; the web view never mutates.
            from .events import read_events
            from .sessions import correlate_sessions
            from .statefeed import build_state_feed

            try:
                tail = max(1, min(int(query.get("tail", ["20"])[0]), 100))
            except ValueError:
                tail = 20
            sessions_doc = correlate_sessions()
            pins, off_belt = mission_control_live_layer(sessions_doc)
            return 200, envelope(
                {
                    "feed": build_state_feed(root),
                    "sessions": sessions_doc,
                    "pins": pins,
                    "off_belt": off_belt,
                    "events": read_events(root, tail=tail),
                }
            )

        if parts == ["api", "file"]:
            return _contained_read(root, query.get("path", [""])[0])

        return _error(404, f"unknown API route: {path}")
    except DwError as err:
        return _error(400, err.message)



# ── mutation intent (WLA-5-06) ───────────────────────────────────────
#
# The editor constructs structured intent; this dispatcher maps each
# request kind one-to-one onto a core plan builder. Preview is pure:
# plan builders only read, so the read-only tree guarantee holds across
# any number of previews. Apply arrives with WLA-5-07.

MUTATION_KINDS = (
    "create_phase",
    "create_story",
    "update_story_status",
    "pause_phase",
    "resume_phase",
    "attach_evidence",
    "close_phase",
)


def _require(body: dict[str, object], *names: str) -> list[str]:
    values = []
    for name in names:
        value = str(body.get(name, "") or "").strip()
        if not value:
            raise DwError(f"missing required field: {name}")
        values.append(value)
    return values


def build_mutation_plan(root: Path, body: dict[str, object]):
    kind = str(body.get("kind", "") or "")
    if kind not in MUTATION_KINDS:
        allowed = ", ".join(MUTATION_KINDS)
        raise DwError(f"unknown mutation kind {kind!r}; allowed: {allowed}")
    (project_slug,) = _require(body, "project")
    project = get_project(root, project_slug)
    force = bool(body.get("force", False))

    if kind == "create_phase":
        number_raw, title = _require(body, "number", "title")
        try:
            number = int(number_raw)
        except ValueError:
            raise DwError(f"phase number must be an integer, got {number_raw!r}")
        if number < 0:
            raise DwError("phase number must not be negative")
        return plan_phase_create(
            root, project, number, title,
            slug=str(body.get("slug", "") or "") or None,
            goal=str(body.get("goal", "") or "") or None,
        )
    if kind == "create_story":
        phase_sel, title = _require(body, "phase", "title")
        phase = get_phase(project, phase_sel)
        return plan_story_create(
            root, project, phase, title,
            slug=str(body.get("slug", "") or "") or None,
            status=str(body.get("status", "") or "backlog"),
        )
    if kind == "update_story_status":
        phase_sel, story, status = _require(body, "phase", "story", "status")
        phase = get_phase(project, phase_sel)
        return plan_story_status(
            root, project, phase, story, status,
            evidence_body=str(body.get("evidence_body", "") or ""),
            force=force,
            reason=str(body.get("reason", "") or ""),
        )
    if kind == "attach_evidence":
        phase_sel, story = _require(body, "phase", "story")
        phase = get_phase(project, phase_sel)
        return plan_story_evidence(
            root, project, phase, story,
            body=str(body.get("body", "") or ""),
            force=force,
        )
    if kind == "pause_phase":
        (phase_sel,) = _require(body, "phase")
        phase = get_phase(project, phase_sel)
        return plan_phase_pause(
            root, project, phase,
            reason=str(body.get("reason", "") or ""),
        )
    if kind == "resume_phase":
        (phase_sel,) = _require(body, "phase")
        phase = get_phase(project, phase_sel)
        return plan_phase_resume(root, project, phase)
    # close_phase
    (phase_sel,) = _require(body, "phase")
    phase = get_phase(project, phase_sel)
    return plan_phase_close(
        root, project, phase,
        summary_body=str(body.get("summary_body", "") or ""),
        status=str(body.get("status", "") or "done"),
        force=force,
    )


def _issues_guard(root: Path, body: dict[str, object], plan) -> tuple[int, dict[str, object]] | None:
    """Refuse mutations while the project has validation issues — unless
    the plan remediates (its projected issue set is a strict subset of
    the current one; a fix is never ambiguous) or the request
    explicitly acknowledges the issues."""
    project_slug = str(body.get("project", "") or "")
    if not project_slug:
        return None
    project = get_project(root, project_slug)
    issues = check_project(project, root)
    if not issues or bool(body.get("acknowledge_issues", False)):
        return None
    projected = projected_issues(plan)
    if projected is not None and set(projected) < set(issues):
        return None  # this mutation strictly reduces drift; let the fix through
    return 409, envelope(
        {
            "error": "project has validation issues; mutations are guarded",
            "issues": issues,
            "hint": "resolve them in the source Markdown (see /api/health), apply a mutation that fixes them, or resend with acknowledge_issues: true",
        },
        ok=False,
        issues=issues,
    )


def _program_http_string(
    body: dict[str, object],
    key: str,
    *,
    required: bool = False,
) -> str:
    value = body.get(key, "")
    if not isinstance(value, str) or (required and not value):
        raise DwError(f"program {key} must be a non-empty string")
    return value


def _program_http_budgets(value: object) -> dict[str, int] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise DwError("program budgets must be an object")
    budgets: dict[str, int] = {}
    for key, amount in value.items():
        if (
            not isinstance(key, str)
            or not key
            or not isinstance(amount, int)
            or isinstance(amount, bool)
        ):
            raise DwError(
                "program budgets must map string names to integer ceilings"
            )
        budgets[key] = amount
    return budgets


def _program_http_capabilities(value: object) -> list[str] | None:
    if value is None:
        return None
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise DwError("program capabilities must be an array of strings")
    return list(value)


def _program_http_integer(
    body: dict[str, object],
    key: str,
    default: int,
) -> int:
    value = body.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool):
        raise DwError(f"program {key} must be an integer")
    return value


def handle_mutation(root: Path, path: str, body: dict[str, object]) -> tuple[int, dict[str, object]]:
    """POST routes: deliberate step, roadmap edits, and score content edits."""
    route = path.rstrip("/")
    if route == "/api/setup/preview":
        unknown = sorted(set(body) - {"proposal_file"})
        if unknown:
            return _error(400, "unknown setup preview parameter(s): %s" % ", ".join(unknown))
        try:
            proposal_file = body.get("proposal_file")
            if not isinstance(proposal_file, str) or not proposal_file:
                raise DwError("setup preview requires proposal_file")
            from .setup_lease import preview_setup

            return 200, envelope(preview_setup(root, Path(proposal_file)))
        except DwError as err:
            return _run_error(err)

    if route == "/api/setup/apply":
        unknown = sorted(set(body) - {"proposal", "expect"})
        if unknown:
            return _error(400, "unknown setup apply parameter(s): %s" % ", ".join(unknown))
        try:
            proposal = body.get("proposal")
            expect = body.get("expect")
            if not isinstance(proposal, str) or not proposal:
                raise DwError("setup apply requires proposal")
            if not isinstance(expect, str) or not expect:
                raise DwError("setup apply requires expect")
            from .setup_lease import apply_setup

            return 200, envelope(apply_setup(root, proposal, expect))
        except DwError as err:
            return _run_error(err)

    if route == "/api/notifications/ack":
        from datetime import datetime, timezone as _tz

        from .notifications import acknowledge_notification

        try:
            notification_id = str(body.get("id", "") or "")
            if not notification_id:
                raise DwError("notification ack requires an id")
            now_ts = datetime.now(_tz.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
            return 200, envelope(
                acknowledge_notification(root, notification_id, now_ts)
            )
        except DwError as err:
            return _run_error(err)

    if route == "/api/programs/plan":
        allowed = {
            "program", "mode", "operator", "reason", "intent_id",
            "capabilities", "budgets", "issued_at", "expires_at",
            "remote", "remote_ref",
        }
        unknown = sorted(set(body) - allowed)
        if unknown:
            return _error(
                400,
                f"unknown program plan parameter(s): {', '.join(unknown)}",
            )
        try:
            program = _program_http_string(body, "program", required=True)
            mode = _program_http_string(body, "mode", required=True)
            operator = _program_http_string(body, "operator", required=True)
            reason = _program_http_string(body, "reason", required=True)
            intent_id = _program_http_string(body, "intent_id", required=True)
            issued_at = _program_http_string(body, "issued_at", required=True)
            expires_at = _program_http_string(
                body, "expires_at", required=True
            )
            capabilities = _program_http_capabilities(
                body.get("capabilities")
            )
            budgets = _program_http_budgets(body.get("budgets"))
            remote = _program_http_string(body, "remote")
            remote_ref = _program_http_string(body, "remote_ref")
            from .program_run import build_program_start_plan

            return 200, envelope(build_program_start_plan(
                root,
                program,
                mode=mode,
                operator=operator,
                approval_reason=reason,
                intent_id=intent_id,
                capabilities=capabilities,
                budgets=budgets,
                issued_at=issued_at,
                expires_at=expires_at,
                remote=remote or None,
                remote_ref=remote_ref or None,
            ))
        except DwError as err:
            return _run_error(err)

    if route == "/api/programs/start":
        allowed = {
            "program", "mode", "operator", "reason", "intent_id",
            "capabilities", "budgets", "issued_at", "expires_at",
            "remote", "remote_ref", "approve", "expect",
        }
        unknown = sorted(set(body) - allowed)
        if unknown:
            return _error(
                400,
                f"unknown program start parameter(s): {', '.join(unknown)}",
            )
        try:
            program = _program_http_string(body, "program", required=True)
            mode = _program_http_string(body, "mode", required=True)
            operator = _program_http_string(body, "operator", required=True)
            reason = _program_http_string(body, "reason", required=True)
            intent_id = _program_http_string(body, "intent_id", required=True)
            issued_at = _program_http_string(body, "issued_at", required=True)
            expires_at = _program_http_string(
                body, "expires_at", required=True
            )
            expect = _program_http_string(body, "expect", required=True)
            if body.get("approve") is not True:
                raise DwError(
                    "program start requires approve=true for the exact preview"
                )
            capabilities = _program_http_capabilities(
                body.get("capabilities")
            )
            budgets = _program_http_budgets(body.get("budgets"))
            remote = _program_http_string(body, "remote")
            remote_ref = _program_http_string(body, "remote_ref")
            from .program_surface import start_program_by_id

            return 200, envelope(start_program_by_id(
                root,
                program,
                mode=mode,
                operator=operator,
                approval_reason=reason,
                intent_id=intent_id,
                capabilities=capabilities,
                budgets=budgets,
                issued_at=issued_at,
                expires_at=expires_at,
                remote=remote or None,
                remote_ref=remote_ref or None,
                expect=expect,
            ))
        except DwError as err:
            return _run_error(err)

    if route == "/api/programs/preview":
        allowed = {
            "run_id", "action", "reason", "decision", "request_id",
            "max_ticks", "max_seconds",
        }
        unknown = sorted(set(body) - allowed)
        if unknown:
            return _error(
                400,
                f"unknown program preview parameter(s): {', '.join(unknown)}",
            )
        try:
            run_id = _program_http_string(body, "run_id", required=True)
            action = _program_http_string(body, "action", required=True)
            from .program_surface import build_program_act_preview

            return 200, envelope(build_program_act_preview(
                root,
                run_id,
                action,
                reason=_program_http_string(body, "reason"),
                decision=_program_http_string(body, "decision"),
                request_id=_program_http_string(body, "request_id"),
                max_ticks=_program_http_integer(body, "max_ticks", 100),
                max_seconds=_program_http_integer(
                    body, "max_seconds", 300
                ),
            ))
        except DwError as err:
            return _run_error(err)

    if route in {
        "/api/programs/tick", "/api/programs/supervise",
        "/api/programs/request", "/api/programs/pause",
        "/api/programs/resume", "/api/programs/revoke",
        "/api/programs/cancel",
    }:
        action = route.rsplit("/", 1)[-1]
        allowed = {"run_id", "expect"}
        if action in {"pause", "resume", "revoke", "cancel", "request"}:
            allowed.add("reason")
        if action == "request":
            allowed.update({"decision", "request_id"})
        if action == "supervise":
            allowed.update({"max_ticks", "max_seconds"})
        unknown = sorted(set(body) - allowed)
        if unknown:
            return _error(
                400,
                f"unknown program {action} parameter(s): {', '.join(unknown)}",
            )
        try:
            run_id = _program_http_string(body, "run_id", required=True)
            expect = _program_http_string(body, "expect", required=True)
            from .program_surface import apply_program_act

            return 200, envelope(apply_program_act(
                root,
                run_id,
                action,
                expect,
                reason=_program_http_string(body, "reason"),
                decision=_program_http_string(body, "decision"),
                request_id=_program_http_string(body, "request_id"),
                max_ticks=_program_http_integer(body, "max_ticks", 100),
                max_seconds=_program_http_integer(
                    body, "max_seconds", 300
                ),
            ))
        except DwError as err:
            return _run_error(err)

    if route == "/api/runs/preview":
        unknown = sorted(set(body) - {
            "run_id", "action", "reason", "decision", "correlation_id",
        })
        if unknown:
            return _error(400, f"unknown run preview parameter(s): {', '.join(unknown)}")
        try:
            run_id, action = _require(body, "run_id", "action")
            from .orchestration_surface import build_run_act_preview

            return 200, envelope(build_run_act_preview(
                root,
                run_id,
                action,
                reason=str(body.get("reason", "") or ""),
                decision=str(body.get("decision", "") or ""),
                correlation_id=str(body.get("correlation_id", "") or ""),
            ))
        except DwError as err:
            return _run_error(err)

    if route == "/api/runs/start":
        allowed = {
            "score", "project", "story", "issued_at", "expires_at",
            "expect", "approve", "operator",
        }
        unknown = sorted(set(body) - allowed)
        if unknown:
            return _error(400, f"unknown run start parameter(s): {', '.join(unknown)}")
        try:
            score, story, issued_at, expires_at, expect, operator = _require(
                body, "score", "story", "issued_at", "expires_at", "expect", "operator"
            )
            if body.get("approve") is not True:
                raise DwError("run start requires approve=true for the exact preview")
            from .orchestration_surface import start_run_by_id

            return 200, envelope(start_run_by_id(
                root,
                score,
                str(body.get("project", "") or "") or None,
                story,
                issued_at,
                expires_at,
                expect,
                approved=True,
                approved_by=operator,
                standing_nudges=body.get("standing_nudges"),
                signal_channel=str(body.get("signal_channel", "") or "") or None,
            ))
        except DwError as err:
            return _run_error(err)

    if route in {
        "/api/runs/tick", "/api/runs/pause", "/api/runs/resume",
        "/api/runs/revoke", "/api/runs/cancel", "/api/runs/checkpoint",
        "/api/runs/request",
    }:
        action = route.rsplit("/", 1)[-1]
        allowed = {"run_id", "expect"}
        if action in {"pause", "revoke", "cancel"}:
            allowed.add("reason")
        if action in {"checkpoint", "request"}:
            allowed.update({"decision", "correlation_id"})
        unknown = sorted(set(body) - allowed)
        if unknown:
            return _error(400, f"unknown run {action} parameter(s): {', '.join(unknown)}")
        try:
            run_id, expect = _require(body, "run_id", "expect")
            from .orchestration_surface import apply_run_act

            return 200, envelope(apply_run_act(
                root,
                run_id,
                action,
                expect,
                reason=str(body.get("reason", "") or ""),
                decision=str(body.get("decision", "") or ""),
                correlation_id=str(body.get("correlation_id", "") or ""),
            ))
        except DwError as err:
            return _run_error(err)

    if route == "/api/step/apply":
        unknown = sorted(set(body) - {"project", "expect"})
        if unknown:
            return _error(400, f"unknown step parameter(s): {', '.join(unknown)}")
        expected = str(body.get("expect", "") or "")
        if not expected:
            return _error(400, "step apply requires expect from a fresh preview")
        try:
            from .step import apply_step

            result, _exit_code = apply_step(
                root,
                str(body.get("project", "") or "") or None,
                expected,
            )
            if result["outcome"] == "refused":
                reason = str(result["reason"] or "step refused")
                return 409, envelope(result, ok=False, issues=[reason])
            issues = [str(result["reason"])] if result["reason"] else []
            return 200, envelope(
                result,
                ok=result["outcome"] == "succeeded",
                issues=issues,
            )
        except DwError as err:
            return _error(400, err.message)

    if route == "/api/orchestration/preview":
        unknown = sorted(set(body) - {"action", "name", "score"})
        if unknown:
            return _error(400, f"unknown orchestration preview parameter(s): {', '.join(unknown)}")
        action = str(body.get("action", "") or "")
        name = str(body.get("name", "") or "")
        if action == "delete" and "score" in body:
            return _error(400, "delete preview does not accept score content")
        try:
            from .orchestration_edit import build_score_mutation_plan, score_mutation_preview

            plan = build_score_mutation_plan(root, action, name, body.get("score"))
            return 200, envelope(score_mutation_preview(plan))
        except DwError as err:
            return _error(400, err.message)

    if route == "/api/orchestration/apply":
        unknown = sorted(set(body) - {"action", "name", "score", "fingerprint"})
        if unknown:
            return _error(400, f"unknown orchestration apply parameter(s): {', '.join(unknown)}")
        supplied = str(body.get("fingerprint", "") or "")
        if not supplied:
            return _error(400, "orchestration apply requires a preview fingerprint")
        action = str(body.get("action", "") or "")
        name = str(body.get("name", "") or "")
        if action == "delete" and "score" in body:
            return _error(400, "delete apply does not accept score content")
        try:
            from .orchestration_edit import (
                apply_score_mutation,
                build_score_mutation_plan,
                score_mutation_preview,
            )

            plan = build_score_mutation_plan(root, action, name, body.get("score"))
            if supplied != plan.fingerprint:
                return 409, envelope(
                    {
                        "error": "stale orchestration preview: score bytes or desired content changed",
                        "supplied_fingerprint": supplied,
                        "current_fingerprint": plan.fingerprint,
                        "preview": score_mutation_preview(plan),
                    },
                    ok=False,
                    issues=["stale orchestration preview refused; nothing was written"],
                )
            if not score_mutation_preview(plan)["applicable"]:
                return 400, envelope(
                    {
                        "error": "invalid orchestration scores cannot be applied",
                        "preview": score_mutation_preview(plan),
                    },
                    ok=False,
                    issues=["compiler diagnostics must be resolved before apply"],
                )
            return 200, envelope(apply_score_mutation(plan, supplied))
        except DwError as err:
            if "rolled back" in err.message:
                return 500, envelope(
                    {"error": err.message, "rolled_back": True},
                    ok=False,
                    issues=[err.message],
                )
            return _error(400, err.message)

    if route == "/api/program-studio/preview":
        unknown = sorted(set(body) - {"family", "action", "name", "document"})
        if unknown:
            return _error(
                400,
                f"unknown Program Studio preview parameter(s): {', '.join(unknown)}",
            )
        family = str(body.get("family", "") or "")
        action = str(body.get("action", "") or "")
        name = str(body.get("name", "") or "")
        if action == "delete" and "document" in body:
            return _error(400, "Program Studio delete preview does not accept document content")
        try:
            from .program_studio import (
                build_studio_mutation_plan,
                studio_mutation_preview,
            )

            plan = build_studio_mutation_plan(
                root, family, action, name, body.get("document")
            )
            return 200, envelope(studio_mutation_preview(plan))
        except DwError as err:
            return _error(400, err.message)

    if route == "/api/program-studio/apply":
        unknown = sorted(
            set(body) - {"family", "action", "name", "document", "fingerprint"}
        )
        if unknown:
            return _error(
                400,
                f"unknown Program Studio apply parameter(s): {', '.join(unknown)}",
            )
        supplied = str(body.get("fingerprint", "") or "")
        if not supplied:
            return _error(400, "Program Studio apply requires a preview fingerprint")
        family = str(body.get("family", "") or "")
        action = str(body.get("action", "") or "")
        name = str(body.get("name", "") or "")
        if action == "delete" and "document" in body:
            return _error(400, "Program Studio delete apply does not accept document content")
        try:
            from .program_studio import (
                apply_studio_mutation,
                build_studio_mutation_plan,
                studio_mutation_preview,
            )

            plan = build_studio_mutation_plan(
                root, family, action, name, body.get("document")
            )
            preview = studio_mutation_preview(plan)
            if supplied != plan.fingerprint:
                return 409, envelope(
                    {
                        "error": "stale Program Studio preview: policy bytes or desired content changed",
                        "supplied_fingerprint": supplied,
                        "current_fingerprint": plan.fingerprint,
                        "preview": preview,
                    },
                    ok=False,
                    issues=["stale Program Studio preview refused; nothing was written"],
                )
            if not preview["applicable"]:
                return 400, envelope(
                    {
                        "error": "invalid Program Studio policies cannot be applied",
                        "preview": preview,
                    },
                    ok=False,
                    issues=["shared compiler diagnostics must be resolved before apply"],
                )
            return 200, envelope(apply_studio_mutation(plan, supplied))
        except DwError as err:
            if "rolled back" in err.message:
                return 500, envelope(
                    {"error": err.message, "rolled_back": True},
                    ok=False,
                    issues=[err.message],
                )
            return _error(400, err.message)

    if route == "/api/mutations/preview":
        try:
            plan = build_mutation_plan(root, body)
            guarded = _issues_guard(root, body, plan)
            if guarded:
                return guarded
            payload = preview_plan(plan, include_content=True, include_diff=True)
            project = get_project(root, str(body["project"]))
            payload["issues_before"] = check_project(project, root)
            payload["issues_after"] = projected_issues(plan)
            return 200, envelope(payload)
        except DwError as err:
            return _error(400, err.message)

    if route == "/api/mutations/apply":
        try:
            supplied = str(body.get("fingerprint", "") or "")
            if not supplied:
                return _error(400, "apply requires the fingerprint from a preview response")
            plan = build_mutation_plan(root, body)
            guarded = _issues_guard(root, body, plan)
            if guarded:
                return guarded
            current = plan_fingerprint(plan)
            if current != supplied:
                return 409, envelope(
                    {
                        "error": "stale preview: source files changed after the preview was taken",
                        "supplied_fingerprint": supplied,
                        "current_fingerprint": current,
                        "hint": "re-run the preview and apply with the fresh fingerprint",
                    },
                    ok=False,
                    issues=["stale preview refused; nothing was written"],
                )
            result = apply_plan(plan, validate_after=True)
            result["applied"] = True
            return 200, envelope(result)
        except DwError as err:
            return _error(400, err.message)
        except Exception as err:  # core writes roll back before raising
            return 500, envelope(
                {
                    "error": f"apply failed and was rolled back: {err}",
                    "rolled_back": True,
                },
                ok=False,
                issues=[f"apply failed and was rolled back: {err}"],
            )

    return _error(
        405,
        "unsupported method or route; use /api/step/apply, guarded roadmap "
        "/api/mutations/preview|apply, or guarded score "
        "/api/orchestration/preview|apply, /api/program-studio/preview|apply, "
        "or exact-token /api/runs/* and /api/programs/* routes",
    )

def create_handler(root: Path, static_dir: Path | None):
    class WorkbenchHandler(BaseHTTPRequestHandler):
        server_version = "dw-workbench"
        quiet = False

        def log_message(self, fmt: str, *args: object) -> None:
            # Concise access log on stderr; --quiet silences it.
            if not self.quiet:
                import sys

                print(f"dw-workbench: {self.address_string()} {fmt % args}", file=sys.stderr)

        def _send_json(self, status: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _host_guard(self) -> bool:
            if host_allowed(self.headers.get("Host", "")):
                return True
            self._send_json(403, envelope(
                {"error": "non-local Host header refused (localhost or a .ts.net tailnet host only)"}, ok=False))
            return False

        def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
            if not self._host_guard():
                return
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api"):
                if self._maybe_stream(parsed):
                    return
                status, payload = handle_api(root, parsed.path, parse_qs(parsed.query))
                self._send_json(status, payload)
                return
            self._send_static(parsed.path)

        def _sse_frame(self, event: str, seq: object, data: dict[str, object]) -> bool:
            frame = (
                f"id: {seq}\nevent: {event}\n"
                f"data: {json.dumps(data, sort_keys=True)}\n\n"
            ).encode("utf-8")
            try:
                self.wfile.write(frame)
                self.wfile.flush()
                return True
            except OSError:
                return False

        def _maybe_stream(self, parsed) -> bool:
            """Serve the read-only SSE ledger/signal tail (docs/signals.md).

            The stream carries the same canonical hash-chained event
            documents the read surfaces return and nothing else: no
            token, apply route, or mutation is reachable from it.
            """
            parts = parsed.path.strip("/").split("/")
            query = parse_qs(parsed.query)
            if (
                len(parts) == 4
                and parts[:2] == ["api", "runs"]
                and parts[3] == "events"
            ):
                from .orchestration_surface import tail_run_events

                run_id = parts[2]
                event_name = "ledger"

                def fetch(cursor: int) -> dict[str, object]:
                    return tail_run_events(root, run_id, cursor)
                default_cursor = "-1"
            elif (
                len(parts) == 4
                and parts[:2] == ["api", "programs"]
                and parts[3] == "events"
            ):
                from .program_surface import tail_program_events

                run_id = parts[2]
                event_name = "program-ledger"

                def fetch(cursor: int) -> dict[str, object]:
                    return tail_program_events(root, run_id, cursor)
                default_cursor = "0"
            elif parts == ["api", "signals", "events"]:
                from .orchestration_surface import tail_signal_events

                remote = query.get("remote", [""])[0].strip()
                branch = query.get("branch", [""])[0].strip()
                event_name = "signal"

                def fetch(cursor: int) -> dict[str, object]:
                    return tail_signal_events(root, remote, branch, cursor)
                default_cursor = "-1"
            else:
                return False
            raw_cursor = (
                self.headers.get("Last-Event-ID", "").strip()
                or query.get("from", [""])[0].strip()
                or default_cursor
            )
            try:
                cursor = int(raw_cursor)
            except ValueError:
                self._send_json(400, envelope(
                    {"error": "stream cursor must be an integer sequence"},
                    ok=False,
                ))
                return True
            follow = query.get("follow", ["1"])[0] != "0"
            try:
                first = fetch(cursor)
            except DwError as err:
                self._send_json(400, envelope({"error": err.message}, ok=False))
                return True
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            for event in first["events"]:
                if not self._sse_frame(event_name, event["seq"], event):
                    return True
                cursor = int(event["seq"])
            if not follow:
                return True
            import time as _time

            quiet_beats = 0
            while True:
                _time.sleep(1)
                try:
                    batch = fetch(cursor)
                except DwError:
                    return True
                if batch["events"]:
                    quiet_beats = 0
                    for event in batch["events"]:
                        if not self._sse_frame(event_name, event["seq"], event):
                            return True
                        cursor = int(event["seq"])
                else:
                    quiet_beats += 1
                    if quiet_beats >= 15:
                        quiet_beats = 0
                        try:
                            self.wfile.write(b": keepalive\n\n")
                            self.wfile.flush()
                        except OSError:
                            return True

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

        def do_OPTIONS(self) -> None:  # noqa: N802 (stdlib naming)
            # No CORS headers are ever emitted; preflights fail closed.
            self._reject()

        def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
            if not self._host_guard():
                return
            parsed = urlparse(self.path)
            try:
                length = int(self.headers.get("Content-Length", "0") or "0")
                raw = self.rfile.read(length) if length else b"{}"
                body = json.loads(raw.decode("utf-8"))
                if not isinstance(body, dict):
                    raise ValueError("body must be a JSON object")
            except (ValueError, UnicodeDecodeError) as err:
                self._send_json(400, envelope({"error": f"invalid JSON body: {err}"}, ok=False))
                return
            status, payload = handle_mutation(root, parsed.path, body)
            self._send_json(status, payload)

        do_PUT = _reject  # noqa: N815
        do_DELETE = _reject  # noqa: N815
        do_PATCH = _reject  # noqa: N815

    return WorkbenchHandler


def serve(root: Path, port: int = 8377, quiet: bool = False) -> None:
    """Run the workbench bound to localhost until interrupted.

    Fails closed: refuses roots without a pm/roadmap tree, refuses
    ports already in use (with remediation), and shuts down cleanly on
    SIGINT/SIGTERM. Never binds beyond 127.0.0.1.
    """
    import signal
    import sys

    if not root.is_dir():
        raise DwError(f"repo root does not exist: {root}")
    try:
        has_roadmap = roadmap_dir(root).is_dir()
    except DwError:
        has_roadmap = False
    if not has_roadmap:
        raise DwError(
            f"no pm/roadmap tree under {root} — the workbench serves exactly one "
            "roadmap-bearing repo root; pass --root or run dw adopt / new-project first"
        )
    handler = create_handler(root, workbench_dir())
    handler.quiet = quiet
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError as err:
        raise DwError(
            f"cannot bind 127.0.0.1:{port} ({err.strerror or err}); "
            "the port is likely in use — stop the other process or pass --port <n>"
        )
    print(f"dw-workbench: serving {root}")
    print(f"dw-workbench: http://127.0.0.1:{port}/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)")
    print(
        "dw-workbench: writes require a guarded preview→apply content boundary "
        "or an exact step/run/program token; never stages, certifies, or commits"
    )

    def _term(_sig, _frame):  # graceful SIGTERM
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _term)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("dw-workbench: shutting down", file=sys.stderr)
    finally:
        httpd.server_close()
