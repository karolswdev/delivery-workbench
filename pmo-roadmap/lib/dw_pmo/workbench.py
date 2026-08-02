"""The local workbench server: JSON API + static explorer shell.

Every response is derived live from the Markdown roadmap through the same
``dw_pmo`` functions the CLI uses — no second parser, cache, or database.
Writes cross guarded preview/apply boundaries or an exact single-use token.
Only a browser-confirmed program action may use pre-granted delivery permission;
the browser adds no authority of its own. The server binds 127.0.0.1 only and
serves exactly the repo root it was started against; file and static endpoints
are contained to their respective trees.

Route logic lives in :func:`handle_api` (pure: path + query in,
status + envelope out) so view models are unit-testable without
sockets. Mutation endpoints arrive with WLA-5-06/07.
"""

from __future__ import annotations

import json
import subprocess
import threading
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

# ── tracked services (WLA-33-05) ──────────────────────────────────────
#
# In-memory registry of child processes started through the terminal
# panel or dw evidence capture.  Keyed by service name.  For now this
# starts empty; actual tracking hooks arrive when the terminal runner
# and evidence-capture paths register their subprocesses here.

_tracked_services: dict[str, dict[str, object]] = {}

# ── global event stream (WLA-34-01) ─────────────────────────────────
#
# Thread-safe subscriber count for the /api/events/global SSE endpoint.
# Capped at _MAX_GLOBAL_SUBSCRIBERS to bound resource usage.

_MAX_GLOBAL_SUBSCRIBERS = 10
_global_stream_lock = threading.Lock()
_global_stream_count = 0

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".woff2": "font/woff2",
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
        for token in (
            "stale", "altered", "already consumed", "already used",
            "does not match", "changed", "not applicable",
        )
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


def _setup_review_proposal(
    root: Path, proposal: object
) -> dict[str, object]:
    """Project an in-browser draft for review without saving or minting a lease."""
    from .presentation import (
        invalid_setup_review_presentation,
        setup_review_presentation,
    )
    from .setup_lease import build_setup_plan, setup_plan_facts
    from .setup_proposal import validate_proposal

    try:
        validated = validate_proposal(proposal)
        facts = setup_plan_facts(
            validated,
            build_setup_plan(root, validated, require_reviewed=False),
        )
        return setup_review_presentation(
            validated,
            facts,
            proposal_file="",
        )
    except DwError as err:
        return invalid_setup_review_presentation(err.message, proposal_file="")


def _studio_bundle_review(root: Path, query: dict[str, list[str]]) -> dict[str, object]:
    """Open one proposal-embedded bundle without accepting runtime authority."""
    from .program_studio import (
        build_studio_bundle_review,
        invalid_studio_bundle_review,
    )
    from .setup_proposal import load_proposal

    raw_file = query.get("proposal_file", [""])[0].strip()
    try:
        if set(query) != {"proposal_file"} or len(query.get("proposal_file", [])) != 1:
            raise DwError(
                "Program Studio bundle review accepts only one proposal_file; "
                "leases and grant credentials are not accepted"
            )
        if not raw_file:
            raise DwError("Program Studio bundle review requires proposal_file")
        candidate = Path(raw_file)
        target = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
        allowed = root.resolve()
        if target != allowed and allowed not in target.parents:
            raise DwError("setup proposal is outside the served repository: %s" % raw_file)
        try:
            proposal = load_proposal(target.read_bytes())
        except OSError as exc:
            raise DwError("setup proposal cannot be read: %s" % exc) from exc
        return build_studio_bundle_review(
            root, proposal, proposal_file=rel(target, root),
        )
    except (DwError, AssertionError) as err:
        message = err.message if isinstance(err, DwError) else str(err)
        return invalid_studio_bundle_review(message, proposal_file=raw_file)


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


def _insights(root: Path, query: dict[str, list[str]]) -> tuple[int, dict[str, object]]:
    """GET /api/insights — local analytics: stories, evidence, commits, timeline."""
    from .evidence import parse_captured_runs
    from .events import read_events

    slug = query.get("project", [""])[0].strip()
    if not slug:
        return _error(400, "insights requires a project parameter")
    project = get_project(root, slug)
    phases = discover_phases(project)

    # Stories by phase
    stories_by_phase: list[dict[str, object]] = []
    total_evidence = 0
    for phase in phases:
        rows = parse_story_rows(phase.path / "current-phase-status.md")
        done = 0
        in_progress = 0
        for row in rows:
            token = normalize_status(row.status)
            if token in {"done", "complete", "closed", "shipped"}:
                done += 1
            elif token == "in-progress":
                in_progress += 1
        stories_by_phase.append({
            "phase": phase.number,
            "title": phase.slug,
            "total": len(rows),
            "done": done,
            "in_progress": in_progress,
        })
        # Count evidence captures in this phase
        for row in rows:
            sid = row.story_id or ""
            # Extract the story number from the id (e.g. WLA-04-03 -> 3)
            parts_id = sid.split("-")
            if len(parts_id) >= 3:
                try:
                    story_num = int(parts_id[-1])
                except ValueError:
                    continue
                evidence_file = phase.path / f"evidence-story-{story_num:02d}.md"
                if not evidence_file.is_file():
                    evidence_file = phase.path / f"evidence-story-{story_num}.md"
                if evidence_file.is_file():
                    text = read_text(evidence_file)
                    total_evidence += len(parse_captured_runs(text))

    # Commit activity from git log (last 90 days)
    commits: list[dict[str, object]] = []
    try:
        result = subprocess.run(
            ["git", "log", "--format=%aI", "--since=90 days ago"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            day_counts: dict[str, int] = {}
            for line in result.stdout.strip().splitlines():
                if not line:
                    continue
                day = line[:10]  # YYYY-MM-DD
                day_counts[day] = day_counts.get(day, 0) + 1
            for day in sorted(day_counts):
                commits.append({"date": day, "count": day_counts[day]})
    except (OSError, subprocess.TimeoutExpired):
        pass

    # Timeline: last 20 roadmap events from the events log
    raw_events = read_events(root, tail=50)
    timeline: list[dict[str, object]] = []
    for ev in reversed(raw_events):
        if len(timeline) >= 20:
            break
        timeline.append({
            "timestamp": ev.get("timestamp", ev.get("ts", "")),
            "event": ev.get("event", ev.get("type", "")),
            "detail": ev.get("detail", ev.get("message", ev.get("subject", ""))),
        })

    return 200, envelope({
        "project": slug,
        "stories_by_phase": stories_by_phase,
        "evidence_count": total_evidence,
        "commits": commits,
        "timeline": timeline,
    })


def _telemetry(root: Path, query: dict[str, list[str]]) -> tuple[int, dict[str, object]]:
    """GET /api/telemetry — per-turn session metrics derived from the run ledger."""
    from .orchestration_run import _load_run_documents, _read_events

    run_id = query.get("run", [""])[0].strip()
    if not run_id:
        return _error(400, "telemetry requires a run parameter")

    try:
        run_dir, grant, compiled = _load_run_documents(root, run_id)
    except DwError as err:
        return _error(404, err.message)

    events = _read_events(run_dir, run_id)

    # Build node profile lookup from the compiled score.
    node_profiles: dict[str, str] = {}
    for node in compiled.get("score", {}).get("nodes", []):
        node_profiles[str(node["id"])] = str(node.get("profile") or "")

    # Walk events to collect claims, receipts, activity observations,
    # and their timestamps.
    claims: dict[str, dict[str, object]] = {}       # claim_id -> claim detail + ts
    claim_receipts: dict[str, list[dict[str, object]]] = {}
    claim_sessions: dict[str, str] = {}              # claim_id -> last session_id
    event_times: dict[int, str] = {}                 # seq -> ts

    for offset, event in enumerate(events):
        kind = str(event["event"])
        detail = event["detail"]
        ts = str(event["ts"])
        event_times[offset] = ts

        if kind == "node_claimed":
            cid = str(detail["claim_id"])
            claims[cid] = {**dict(detail), "claimed_ts": ts}
            claim_receipts[cid] = []
        elif kind == "node_receipt":
            cid = str(detail["claim_id"])
            claim_receipts.setdefault(cid, []).append({
                "seq": offset,
                "ts": ts,
                **dict(detail),
            })
        elif kind == "activity_observed":
            cid = str(detail["claim_id"])
            sid = str(detail.get("session_id") or "")
            if sid:
                claim_sessions[cid] = sid

    # Build per-turn rows from receipts.
    turns: list[dict[str, object]] = []
    total_cost: int = 0
    total_input: int = 0
    has_cost: bool = False
    has_tokens: bool = False
    models_seen: set[str] = set()
    first_ts: str | None = None
    last_ts: str | None = None

    for cid, recs in claim_receipts.items():
        claim = claims.get(cid)
        if not claim:
            continue
        node_id = str(claim.get("node_id", ""))
        attempt = claim.get("attempt")
        profile = node_profiles.get(node_id, "")

        for rec in recs:
            rec_ts = str(rec.get("ts", ""))
            claimed_ts = str(claim.get("claimed_ts", ""))

            # Extract token/cost fields, keeping null when absent.
            usage_status = rec.get("usage_status")
            raw_total = rec.get("total_tokens")
            raw_cost = rec.get("cost_microunits")

            total_tokens = int(raw_total) if raw_total is not None else None
            cost_micro = int(raw_cost) if raw_cost is not None else None

            measurement = (
                str(usage_status) if usage_status is not None else "unknown"
            )

            # These granular fields do not exist in the current receipt schema.
            input_tokens = None
            output_tokens = None
            cache_read_tokens = None
            cache_creation_tokens = None

            state = str(rec.get("state", ""))

            if cost_micro is not None:
                total_cost += cost_micro
                has_cost = True
            if total_tokens is not None:
                total_input += total_tokens  # best approximation — no split available
                has_tokens = True

            if profile:
                models_seen.add(profile)

            if first_ts is None or rec_ts < first_ts:
                first_ts = rec_ts
            if last_ts is None or rec_ts > last_ts:
                last_ts = rec_ts

            turns.append({
                "node_id": node_id,
                "attempt": attempt,
                "session_id": claim_sessions.get(cid) or None,
                "provider": profile or None,
                "model": profile or None,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_tokens": cache_read_tokens,
                "cache_creation_tokens": cache_creation_tokens,
                "total_tokens": total_tokens,
                "cost_microunits": cost_micro,
                "measurement_status": measurement,
                "started_at": claimed_ts or None,
                "ended_at": rec_ts or None,
                "state": state or None,
            })

    # Sort turns chronologically by receipt timestamp.
    turns.sort(key=lambda t: str(t.get("ended_at") or ""))

    # Compute duration.
    duration: int | None = None
    if first_ts and last_ts:
        try:
            from datetime import datetime as _dt, timezone as _tz
            t0 = _dt.fromisoformat(first_ts.replace("Z", "+00:00"))
            t1 = _dt.fromisoformat(last_ts.replace("Z", "+00:00"))
            duration = max(0, int((t1 - t0).total_seconds()))
        except (ValueError, TypeError):
            pass

    summary: dict[str, object] = {
        "total_cost_microunits": total_cost if has_cost else None,
        "total_input_tokens": total_input if has_tokens else None,
        "total_output_tokens": None,  # not available at receipt granularity
        "total_turns": len(turns),
        "models_used": sorted(models_seen) if models_seen else [],
        "duration_seconds": duration,
    }

    return 200, envelope({"turns": turns, "summary": summary})


def _session_outcomes(root: Path, query: dict[str, list[str]]) -> tuple[int, dict[str, object]]:
    """GET /api/session-outcomes — per-session outcome projection from the run ledger."""
    from .orchestration_run import _load_run_documents, _read_events, replay_run

    run_id = query.get("run", [""])[0].strip()
    if not run_id:
        return _error(400, "session-outcomes requires a run parameter")

    try:
        run_dir, grant, compiled = _load_run_documents(root, run_id)
    except DwError as err:
        return _error(404, err.message)

    events = _read_events(run_dir, run_id)

    # Build node profile lookup from the compiled score.
    node_profiles: dict[str, str] = {}
    for node in compiled.get("score", {}).get("nodes", []):
        node_profiles[str(node["id"])] = str(node.get("profile") or "")

    # Walk events to collect claims, receipts, activity observations,
    # releases, rail advances, and external commits.
    claims: dict[str, dict[str, object]] = {}       # claim_id -> claim detail + ts
    claim_receipts: dict[str, list[dict[str, object]]] = {}
    claim_sessions: dict[str, str] = {}              # claim_id -> last session_id
    claim_releases: dict[str, dict[str, object]] = {}
    rail_advances: list[dict[str, object]] = []
    external_commits: list[dict[str, object]] = []
    checkpoints: list[dict[str, object]] = []

    for offset, event in enumerate(events):
        kind = str(event["event"])
        detail = event["detail"]
        ts = str(event["ts"])

        if kind == "node_claimed":
            cid = str(detail["claim_id"])
            claims[cid] = {**dict(detail), "claimed_ts": ts, "claimed_seq": offset}
            claim_receipts[cid] = []
        elif kind == "node_receipt":
            cid = str(detail["claim_id"])
            claim_receipts.setdefault(cid, []).append({
                "seq": offset, "ts": ts, **dict(detail),
            })
        elif kind == "activity_observed":
            cid = str(detail["claim_id"])
            sid = str(detail.get("session_id") or "")
            if sid:
                claim_sessions[cid] = sid
        elif kind == "node_released":
            cid = str(detail["claim_id"])
            claim_releases[cid] = {
                "seq": offset, "ts": ts, **dict(detail),
            }
        elif kind == "rail_advanced":
            rail_advances.append({"seq": offset, "ts": ts, **dict(detail)})
        elif kind == "external_commit_observed":
            external_commits.append({"seq": offset, "ts": ts, **dict(detail)})
        elif kind == "checkpoint_reached":
            checkpoints.append({"seq": offset, "ts": ts, **dict(detail)})

    # Build per-session rows.
    sessions: list[dict[str, object]] = []
    total_cost: int = 0
    total_artifacts: int = 0
    total_evidence: int = 0

    for cid, claim in claims.items():
        node_id = str(claim.get("node_id", ""))
        attempt = claim.get("attempt")
        session_id = claim_sessions.get(cid)

        # Determine outcome state from release or receipts.
        release = claim_releases.get(cid)
        if release:
            state = str(release.get("outcome", "unknown"))
        else:
            # Still active — check last receipt.
            recs = claim_receipts.get(cid, [])
            last = recs[-1] if recs else None
            state = str(last.get("state", "running")) if last else "running"

        # Aggregate cost and tokens from receipts.
        cost_micro = 0
        for rec in claim_receipts.get(cid, []):
            raw_cost = rec.get("cost_microunits")
            if raw_cost is not None:
                cost_micro += int(raw_cost)

        # Compute duration from claim to release (or last receipt).
        duration: int | None = None
        claimed_ts = str(claim.get("claimed_ts", ""))
        end_ts = ""
        if release:
            end_ts = str(release.get("ts", ""))
        else:
            recs = claim_receipts.get(cid, [])
            if recs:
                end_ts = str(recs[-1].get("ts", ""))
        if claimed_ts and end_ts:
            try:
                t0 = datetime.fromisoformat(claimed_ts.replace("Z", "+00:00"))
                t1 = datetime.fromisoformat(end_ts.replace("Z", "+00:00"))
                duration = max(0, int((t1 - t0).total_seconds()))
            except (ValueError, TypeError):
                pass

        # Artifacts: derive from release artifact_bytes.
        artifacts: list[dict[str, object]] = []
        artifact_bytes = 0
        if release:
            artifact_bytes = int(release.get("artifact_bytes", 0))
            if artifact_bytes > 0:
                artifacts.append({
                    "name": f"{node_id}-output",
                    "hash": None,
                    "type": node_profiles.get(node_id) or "unknown",
                })
                total_artifacts += 1

        # Evidence captures, check results, story transitions, and
        # file-change stats are not available in the ledger — return
        # empty arrays rather than fabricated data.
        evidence_captures: list[dict[str, object]] = []
        check_results: list[dict[str, object]] = []
        story_transitions: list[dict[str, object]] = []

        # Check results: for check-type nodes, derive from outcome.
        node_type = str(claim.get("node_type", ""))
        if node_type == "check" and release:
            outcome = str(release.get("outcome", ""))
            check_results.append({
                "check": node_id,
                "passed": outcome == "succeeded",
            })

        if cost_micro:
            total_cost += cost_micro

        sessions.append({
            "session_id": session_id,
            "node_id": node_id,
            "attempt": attempt,
            "state": state,
            "produced": {
                "artifacts": artifacts,
                "evidence_captures": evidence_captures,
                "check_results": check_results,
                "story_transitions": story_transitions,
                "files_changed": None,
                "lines_added": None,
                "lines_deleted": None,
            },
            "cost_microunits": cost_micro if cost_micro else None,
            "duration_seconds": duration,
        })

    # Sort by claim sequence (order of node claims).
    sessions.sort(key=lambda s: str(s.get("session_id") or ""))

    return 200, envelope({
        "run_id": run_id,
        "sessions": sessions,
        "summary": {
            "session_count": len(sessions),
            "artifact_count": total_artifacts,
            "evidence_count": total_evidence,
            "total_cost_microunits": total_cost if total_cost else None,
        },
    })


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

        if parts == ["api", "setup", "bundle"]:
            return 200, envelope(_studio_bundle_review(root, query))

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
            len(parts) == 4
            and parts[:2] == ["api", "programs"]
            and parts[3] == "memory"
        ):
            from .memory_read import (
                build_memory_recall_projection,
                memory_http_status,
            )

            document = build_memory_recall_projection(root, program=parts[2])
            status = memory_http_status(document)
            issues = (
                [document["refusal"]["message"]]
                if status != 200 else []
            )
            return status, envelope(
                document, ok=status == 200, issues=issues
            )

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

        if (
            len(parts) == 4
            and parts[:2] == ["api", "runs"]
            and parts[3] == "memory"
        ):
            from .memory_read import (
                build_memory_recall_projection,
                memory_http_status,
            )

            document = build_memory_recall_projection(root, run=parts[2])
            status = memory_http_status(document)
            issues = (
                [document["refusal"]["message"]]
                if status != 200 else []
            )
            return status, envelope(
                document, ok=status == 200, issues=issues
            )

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

            try:
                max_ticks = int(query.get("max_ticks", ["100"])[0])
                max_seconds = int(query.get("max_seconds", ["300"])[0])
            except ValueError as exc:
                raise DwError("run preview ceilings must be integers") from exc
            return 200, envelope(build_run_act_preview(
                root,
                parts[2],
                parts[4],
                reason=query.get("reason", [""])[0],
                decision=query.get("decision", [""])[0],
                correlation_id=query.get("correlation_id", [""])[0],
                max_ticks=max_ticks,
                max_seconds=max_seconds,
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

        if (
            len(parts) == 4
            and parts[:2] == ["api", "context"]
            and parts[3] == "current"
        ):
            from .project_context import ProjectContext

            ctx = ProjectContext(root)
            return 200, envelope(ctx.current(parts[2]))

        if (
            len(parts) == 4
            and parts[:2] == ["api", "context"]
            and parts[3] == "history"
        ):
            from .project_context import ProjectContext

            ctx = ProjectContext(root)
            return 200, envelope(ctx.history(parts[2]))

        if parts == ["api", "projects"]:
            summaries = [_project_summary(p, root) for p in discover_projects(root)]
            return 200, envelope({
                "projects": summaries,
                "project_count": len(summaries),
                "selection_required": len(summaries) > 1,
            })

        if len(parts) == 3 and parts[:2] == ["api", "projects"]:
            project = get_project(root, parts[2])
            return 200, envelope(project_context(project, root))

        if len(parts) == 4 and parts[:2] == ["api", "projects"] and parts[3] == "board":
            from .board import board_model

            project = get_project(root, parts[2])
            return 200, envelope(board_model(project, root))

        if len(parts) == 4 and parts[:2] == ["api", "projects"] and parts[3] == "state":
            from .orthogonal_state import build_orthogonal_state

            return 200, envelope(build_orthogonal_state(root, parts[2]))

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

        if parts == ["api", "diff"]:
            # WLA-33-03: read-only diff of uncommitted changes (working
            # tree + index) for the repository root. No mutation guard.
            import subprocess

            project_slug = query.get("project", [""])[0].strip()
            try:
                # Combined working-tree and staged changes
                result = subprocess.run(
                    ["git", "diff", "HEAD"],
                    cwd=str(root),
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                raw_diff = result.stdout or ""

                # Also get a name-status summary
                ns_result = subprocess.run(
                    ["git", "diff", "HEAD", "--name-status"],
                    cwd=str(root),
                    capture_output=True,
                    text=True,
                    timeout=15,
                )

                # Parse name-status lines into {path: status}
                status_map: dict[str, str] = {}
                for line in (ns_result.stdout or "").strip().splitlines():
                    parts_ns = line.split("\t", 1)
                    if len(parts_ns) == 2:
                        status_map[parts_ns[1]] = parts_ns[0]

                # Split raw diff into per-file chunks
                files: list[dict[str, str]] = []
                current_path = ""
                current_lines: list[str] = []

                for line in raw_diff.splitlines(True):
                    if line.startswith("diff --git "):
                        if current_path:
                            files.append({
                                "path": current_path,
                                "status": status_map.get(current_path, "M"),
                                "diff": "".join(current_lines),
                            })
                        # Extract b-side path: "diff --git a/foo b/foo"
                        b_idx = line.find(" b/")
                        current_path = line[b_idx + 3:].rstrip() if b_idx >= 0 else ""
                        current_lines = [line]
                    else:
                        current_lines.append(line)

                if current_path:
                    files.append({
                        "path": current_path,
                        "status": status_map.get(current_path, "M"),
                        "diff": "".join(current_lines),
                    })

                return 200, envelope({"files": files})
            except subprocess.TimeoutExpired:
                return _error(504, "git diff timed out")
            except Exception as exc:
                return _error(500, f"git diff failed: {exc}")

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

        if parts == ["api", "insights"]:
            return _insights(root, query)

        if parts == ["api", "suggestions"]:
            from .suggestions import SuggestionStore

            slug = query.get("project", [""])[0].strip()
            if not slug:
                return _error(400, "suggestions requires a project parameter")
            state_filter = query.get("state", [""])[0].strip() or None
            store = SuggestionStore(root)
            return 200, envelope({
                "project": slug,
                "suggestions": store.list(slug, state=state_filter),
                "pending_count": store.pending_count(slug),
            })

        if parts == ["api", "services"]:
            return 200, envelope({"services": list(_tracked_services.values())})

        if parts == ["api", "file"]:
            return _contained_read(root, query.get("path", [""])[0])

        if parts == ["api", "telemetry"]:
            return _telemetry(root, query)

        if parts == ["api", "session-outcomes"]:
            return _session_outcomes(root, query)

        if (
            len(parts) == 4
            and parts[:3] == ["api", "memory", "records"]
        ):
            from .memory_read import (
                build_memory_record_projection,
                memory_http_status,
            )

            document = build_memory_record_projection(root, parts[3])
            status = memory_http_status(document)
            issues = (
                [document["refusal"]["message"]]
                if status != 200 else []
            )
            return status, envelope(
                document, ok=status == 200, issues=issues
            )

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


def _run_http_integer(
    body: dict[str, object],
    key: str,
    default: int,
) -> int:
    value = body.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool):
        raise DwError(f"run {key} must be an integer")
    return value


def handle_mutation(root: Path, path: str, body: dict[str, object]) -> tuple[int, dict[str, object]]:
    """POST routes: deliberate step, roadmap edits, and score content edits."""
    route = path.rstrip("/")
    if route == "/api/setup/review":
        unknown = sorted(set(body) - {"proposal"})
        if unknown:
            return _error(400, "unknown setup review parameter(s): %s" % ", ".join(unknown))
        if set(body) != {"proposal"}:
            return _error(400, "setup review requires proposal")
        # This adapter is deliberately read-only. It validates and projects the
        # browser draft, but cannot create the pending record used by apply.
        return 200, envelope(_setup_review_proposal(root, body["proposal"]))

    if route == "/api/setup/preview":
        unknown = sorted(set(body) - {"proposal_file", "proposal"})
        if unknown:
            return _error(400, "unknown setup preview parameter(s): %s" % ", ".join(unknown))
        try:
            proposal_file = body.get("proposal_file")
            proposal = body.get("proposal")
            if bool(proposal_file) == (proposal is not None):
                raise DwError("setup preview requires exactly one of proposal_file or proposal")
            if proposal_file:
                if not isinstance(proposal_file, str):
                    raise DwError("setup preview proposal_file must be a string")
                from .setup_lease import preview_setup

                result = preview_setup(root, Path(proposal_file))
            else:
                if not isinstance(proposal, dict):
                    raise DwError("setup preview proposal must be an object")
                from .setup_lease import preview_setup_proposal

                result = preview_setup_proposal(root, proposal)
            return 200, envelope(result)
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

    if route == "/api/requests/respond":
        # WLA-34-04: inline ask-and-resume convenience endpoint.
        # Resolves a correlation id to its run or program, previews the
        # request action, and applies it in one atomic step.  The browser
        # session panel uses this so the operator can answer a typed
        # question without manually navigating to the control room.
        allowed = {"correlation_id", "decision", "reason"}
        unknown = sorted(set(body) - allowed)
        if unknown:
            return _error(
                400,
                f"unknown request respond parameter(s): {', '.join(unknown)}",
            )
        try:
            correlation_id = str(body.get("correlation_id", "") or "")
            decision = str(body.get("decision", "") or "")
            reason = str(body.get("reason", "") or "")
            if not correlation_id:
                raise DwError("request respond requires a correlation_id")
            if not decision:
                raise DwError("request respond requires a decision")

            from .notifications import resolve_correlation

            match = resolve_correlation(root, correlation_id)
            kind = str(match.get("kind", ""))
            run_id = str(match.get("run_id", ""))

            if kind == "program-intervention-required":
                from .program_surface import (
                    apply_program_act,
                    build_program_act_preview,
                )

                preview = build_program_act_preview(
                    root, run_id, "request",
                    reason=reason, decision=decision,
                    request_id=correlation_id,
                )
                if not preview.get("applicable"):
                    issues = preview.get("issues", ["preview refused"])
                    return 409, envelope(
                        preview, ok=False,
                        issues=[str(i) for i in issues],
                    )
                result = apply_program_act(
                    root, run_id, "request",
                    str(preview["act_token"]),
                    reason=reason, decision=decision,
                    request_id=correlation_id,
                )
            else:
                from .orchestration_surface import (
                    apply_run_act,
                    build_run_act_preview,
                )

                preview = build_run_act_preview(
                    root, run_id, "request",
                    reason=reason, decision=decision,
                    correlation_id=correlation_id,
                )
                if not preview.get("applicable"):
                    issues = preview.get("issues", ["preview refused"])
                    return 409, envelope(
                        preview, ok=False,
                        issues=[str(i) for i in issues],
                    )
                result = apply_run_act(
                    root, run_id, "request",
                    str(preview["act_token"]),
                    reason=reason, decision=decision,
                    correlation_id=correlation_id,
                )
            return 200, envelope(result)
        except DwError as err:
            return _run_error(err)

    if route == "/api/runs/preview":
        unknown = sorted(set(body) - {
            "run_id", "action", "reason", "decision", "correlation_id",
            "max_ticks", "max_seconds",
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
                max_ticks=_run_http_integer(body, "max_ticks", 100),
                max_seconds=_run_http_integer(body, "max_seconds", 300),
            ))
        except DwError as err:
            return _run_error(err)

    if route == "/api/runs/start":
        allowed = {
            "score", "project", "story", "issued_at", "expires_at",
            "expect", "approve", "operator", "standing_nudges",
            "signal_channel",
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

    if route == "/api/runs/supervise":
        unknown = sorted(set(body) - {
            "run_id", "expect", "max_ticks", "max_seconds",
        })
        if unknown:
            return _error(
                400,
                f"unknown run supervise parameter(s): {', '.join(unknown)}",
            )
        try:
            run_id, expect = _require(body, "run_id", "expect")
            from .orchestration_surface import apply_run_act

            return 200, envelope(apply_run_act(
                root,
                run_id,
                "supervise",
                expect,
                max_ticks=_run_http_integer(body, "max_ticks", 100),
                max_seconds=_run_http_integer(body, "max_seconds", 300),
            ))
        except DwError as err:
            return _run_error(err)

    if route in {
        "/api/runs/tick", "/api/runs/pause", "/api/runs/resume",
        "/api/runs/revoke", "/api/runs/cancel",
        "/api/runs/checkpoint", "/api/runs/request",
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
                max_ticks=_run_http_integer(body, "max_ticks", 100),
                max_seconds=_run_http_integer(body, "max_seconds", 300),
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

    if route == "/api/suggestions":
        from .suggestions import SuggestionStore

        allowed = {"project", "title", "description", "priority", "session_id", "run_id", "rationale"}
        unknown = sorted(set(body) - allowed)
        if unknown:
            return _error(400, f"unknown suggestion parameter(s): {', '.join(unknown)}")
        try:
            project, title = _require(body, "project", "title")
            store = SuggestionStore(root)
            result = store.suggest(
                project,
                title,
                str(body.get("description", "") or ""),
                priority=str(body.get("priority", "normal") or "normal"),
                session_id=str(body.get("session_id", "") or "") or None,
                run_id=str(body.get("run_id", "") or "") or None,
                rationale=str(body.get("rationale", "") or ""),
            )
            return 200, envelope(result)
        except DwError as err:
            return _run_error(err)

    parts = [part for part in route.strip("/").split("/") if part]
    if (
        len(parts) == 4
        and parts[:2] == ["api", "suggestions"]
        and parts[3] == "accept"
    ):
        from .suggestions import SuggestionStore

        try:
            store = SuggestionStore(root)
            project = str(body.get("project", "") or "")
            if not project:
                return _error(400, "accept requires a project parameter")
            decided_by = str(body.get("decided_by", "operator") or "operator")
            materialized = str(body.get("materialized_story_id", "") or "") or None
            result = store.accept(project, parts[2], decided_by=decided_by, materialized_story_id=materialized)
            return 200, envelope(result)
        except DwError as err:
            return _run_error(err)

    if (
        len(parts) == 4
        and parts[:2] == ["api", "suggestions"]
        and parts[3] == "dismiss"
    ):
        from .suggestions import SuggestionStore

        try:
            store = SuggestionStore(root)
            project = str(body.get("project", "") or "")
            if not project:
                return _error(400, "dismiss requires a project parameter")
            decided_by = str(body.get("decided_by", "operator") or "operator")
            result = store.dismiss(project, parts[2], decided_by=decided_by)
            return 200, envelope(result)
        except DwError as err:
            return _run_error(err)

    # ── revisioned project context (WLA-34-09) ──────────────────────────
    if (
        len(parts) == 4
        and parts[:2] == ["api", "context"]
        and parts[3] == "draft"
    ):
        from .project_context import ProjectContext

        allowed = {"content", "session_id", "based_on_index_tree"}
        unknown = sorted(set(body) - allowed)
        if unknown:
            return _error(400, f"unknown context draft parameter(s): {', '.join(unknown)}")
        try:
            content = str(body.get("content", "") or "")
            if not content.strip():
                raise DwError("context draft content must be non-empty Markdown")
            ctx = ProjectContext(root)
            result = ctx.draft(
                parts[2],
                content,
                session_id=str(body.get("session_id", "") or ""),
                based_on_index_tree=str(body.get("based_on_index_tree", "") or ""),
            )
            return 200, envelope(result)
        except DwError as err:
            return _run_error(err)

    if (
        len(parts) == 4
        and parts[:2] == ["api", "context"]
        and parts[3] == "accept"
    ):
        from .project_context import ProjectContext

        allowed = {"revision", "fingerprint"}
        unknown = sorted(set(body) - allowed)
        if unknown:
            return _error(400, f"unknown context accept parameter(s): {', '.join(unknown)}")
        try:
            revision = body.get("revision")
            if not isinstance(revision, int) or isinstance(revision, bool):
                raise DwError("context accept requires an integer revision")
            fingerprint = str(body.get("fingerprint", "") or "")
            ctx = ProjectContext(root)
            result = ctx.accept(parts[2], revision, fingerprint=fingerprint)
            return 200, envelope(result)
        except DwError as err:
            return _run_error(err)

    return _error(
        405,
        "unsupported method or route; use /api/step/apply, guarded roadmap "
        "/api/mutations/preview|apply, or guarded score "
        "/api/orchestration/preview|apply, /api/program-studio/preview|apply, "
        "or exact-token /api/runs/* and /api/programs/* routes",
    )

# ── terminal command runner (WLA-33-04) ────────────────────────────────
#
# Command-runner fallback: a full PTY requires WebSocket support the
# stdlib HTTP server does not provide.  This route runs individual
# commands scoped to dw and git only, with a 30-second timeout, bound
# to localhost.

_TERMINAL_ALLOWED_PREFIXES = (".githooks/dw", "dw", "git")
_TERMINAL_TIMEOUT = 30


def handle_terminal_exec(root: Path, body: dict[str, object]) -> tuple[int, dict[str, object]]:
    """POST /api/terminal/exec — run a dw or git command in the repo root."""
    command = str(body.get("command", "") or "").strip()
    if not command:
        return _error(400, "missing command")

    # Security: only dw and git commands are allowed
    allowed = False
    for prefix in _TERMINAL_ALLOWED_PREFIXES:
        if command == prefix or command.startswith(prefix + " "):
            allowed = True
            break
    if not allowed:
        return 403, envelope(
            {"error": "Only dw and git commands are allowed"},
            ok=False,
            issues=["Only dw and git commands are allowed"],
        )

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=_TERMINAL_TIMEOUT,
        )
        return 200, envelope({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        })
    except subprocess.TimeoutExpired:
        return 200, envelope({
            "stdout": "",
            "stderr": f"command timed out after {_TERMINAL_TIMEOUT} seconds",
            "exit_code": 124,
        })
    except OSError as err:
        return 500, envelope(
            {"error": f"command execution failed: {err}"},
            ok=False,
            issues=[f"command execution failed: {err}"],
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
            elif parts == ["api", "events", "global"]:
                return self._global_stream(root, query)
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

            # ── snapshot-then-tail for per-run/program streams (WLA-34-05)
            # Emit a snapshot of the current state so reconnecting clients
            # can rebuild without duplicating incremental events.
            if event_name == "ledger":
                try:
                    snap = self._run_snapshot(root, run_id)
                    if not self._sse_frame("snapshot", 0, snap):
                        return True
                except Exception:
                    pass
            elif event_name == "program-ledger":
                try:
                    snap = self._program_snapshot(root, run_id)
                    if not self._sse_frame("snapshot", 0, snap):
                        return True
                except Exception:
                    pass

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

        def _global_stream(self, repo_root: Path, query: dict[str, list[str]]) -> bool:
            """Read-only SSE endpoint for coarse lifecycle events (WLA-34-01).

            Synthesises a unified stream from the rail event log and the
            current run/program/notification inventories. Each event
            carries a minimal JSON payload and a monotonic sequence id
            suitable for Last-Event-ID replay.
            """
            global _global_stream_count
            with _global_stream_lock:
                if _global_stream_count >= _MAX_GLOBAL_SUBSCRIBERS:
                    self._send_json(503, envelope(
                        {"error": "global event stream subscriber limit reached"},
                        ok=False,
                    ))
                    return True
                _global_stream_count += 1
            try:
                return self._global_stream_body(repo_root, query)
            finally:
                with _global_stream_lock:
                    _global_stream_count -= 1

        def _run_snapshot(self, repo_root: Path, run_id: str) -> dict[str, object]:
            """Build a snapshot of a single run's current state (WLA-34-05).

            Derived entirely from the existing replay projection and
            view -- no new persistence.  The snapshot is idempotent:
            connecting twice produces the same state.
            """
            from .orchestration_surface import build_run_view

            view = build_run_view(repo_root, run_id)
            nodes = []
            for node in (view.get("graph", {}).get("nodes") or []):
                nodes.append({
                    "id": str(node.get("id", "")),
                    "state": str(node.get("state", "")),
                    "attempt": node.get("attempt", 0),
                })
            return {
                "run_id": run_id,
                "state": str(view.get("state", "")),
                "ledger_events": view.get("ledger_events", 0),
                "ledger_head": str(view.get("ledger_head", "")),
                "nodes": nodes,
                "outstanding_requests": [
                    {
                        "correlation_id": str(r.get("correlation_id", "")),
                        "kind": str(r.get("kind", "")),
                    }
                    for r in (view.get("outstanding_requests") or [])
                ],
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

        def _program_snapshot(self, repo_root: Path, run_id: str) -> dict[str, object]:
            """Build a snapshot of a single program run's current state (WLA-34-05)."""
            from .program_surface import build_program_view

            view = build_program_view(repo_root, run_id)
            return {
                "run_id": run_id,
                "state": str(view.get("state", "")),
                "operational_state": str(view.get("operational_state", "")),
                "event_count": view.get("event_count", 0),
                "ledger_head": str(view.get("ledger_head", "")),
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

        def _global_snapshot(self, repo_root: Path) -> dict[str, object]:
            """Build a full state snapshot from existing data sources.

            The snapshot is idempotent -- connecting twice produces the same
            state, not doubled entries.  It is derivable entirely from the
            rail event log, run/program inventories, and notification store.
            """
            from .events import read_events
            from .notifications import build_notifications
            from .orchestration_run import run_inventory

            def _now_ts() -> str:
                return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            snapshot: dict[str, object] = {
                "timestamp": _now_ts(),
                "pending_requests": [],
                "active_runs": [],
                "programs": [],
                "story_statuses": {},
            }

            # Story statuses from the rail event log (last status wins)
            try:
                all_events = read_events(repo_root)
                for raw in all_events:
                    event_type = str(raw.get("event", ""))
                    if event_type == "story_status":
                        story_id = str(raw.get("story") or "")
                        detail = raw.get("detail") or {}
                        if story_id:
                            snapshot["story_statuses"][story_id] = {
                                "status": str(detail.get("to") or ""),
                                "project": str(raw.get("project") or ""),
                            }
            except Exception:
                pass

            # Active runs with their state and outstanding requests
            try:
                inventory = run_inventory(repo_root)
                for entry in inventory.get("runs", []):
                    if not entry.get("valid"):
                        continue
                    run = entry.get("run") or {}
                    run_summary: dict[str, object] = {
                        "id": str(entry.get("run_id", "")),
                        "project": str(run.get("story", {}).get("project", "")),
                        "story_id": str(run.get("story", {}).get("id", "")),
                        "state": str(run.get("state", "")),
                    }
                    snapshot["active_runs"].append(run_summary)
                    for req in run.get("outstanding_requests", []):
                        snapshot["pending_requests"].append({
                            "id": str(req.get("correlation_id", "")),
                            "run_id": str(entry.get("run_id", "")),
                            "project": str(run.get("story", {}).get("project", "")),
                            "kind": str(req.get("kind", "")),
                        })
            except Exception:
                pass

            # Program states
            try:
                from .program_surface import program_summary_inventory

                prog_inv = program_summary_inventory(repo_root)
                for summary in prog_inv.get("runs", []):
                    if not summary.get("valid"):
                        continue
                    snapshot["programs"].append({
                        "id": str(summary.get("run_id", "")),
                        "state": str(summary.get("state", "")),
                        "operational_state": str(summary.get("operational_state", "")),
                    })
            except Exception:
                pass

            # Notification-derived pending requests
            try:
                notifs = build_notifications(repo_root)
                for notif in notifs.get("notifications", []):
                    kind = str(notif.get("kind", ""))
                    if kind in {
                        "request-pending", "checkpoint-pending",
                        "request-republished",
                        "program-intervention-required",
                    }:
                        snapshot["pending_requests"].append({
                            "id": str(notif.get("id", "")),
                            "run_id": str(notif.get("run_id", "")),
                            "kind": kind,
                        })
            except Exception:
                pass

            return snapshot

        def _global_stream_body(self, repo_root: Path, query: dict[str, list[str]]) -> bool:
            import time as _time

            from .events import read_events
            from .notifications import build_notifications
            from .orchestration_run import run_inventory

            raw_cursor = (
                self.headers.get("Last-Event-ID", "").strip()
                or query.get("from", [""])[0].strip()
                or "0"
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

            # ── map rail event types to global stream event names ────
            _EVENT_MAP = {
                "story_status": "story_changed",
                "evidence_capture": "evidence_captured",
                "gate_pass": "gate_result",
                "gate_refusal": "gate_result",
                "contract_generated": "gate_result",
                "step_execution": "run_changed",
            }

            def _now_ts() -> str:
                return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            def _synthesise(after_seq: int) -> tuple[list[dict[str, object]], int]:
                """Build coarse events from the rail log + live inventories."""
                events: list[dict[str, object]] = []
                seq = after_seq

                # 1. Rail event log lines as coarse events
                all_events = read_events(repo_root)
                for idx, raw in enumerate(all_events):
                    event_seq = idx + 1
                    if event_seq <= after_seq:
                        continue
                    mapped = _EVENT_MAP.get(str(raw.get("event", "")))
                    if mapped is None:
                        continue
                    payload: dict[str, object] = {
                        "type": mapped,
                        "id": str(raw.get("story") or ""),
                        "project": str(raw.get("project") or ""),
                        "timestamp": str(raw.get("ts") or _now_ts()),
                    }
                    if mapped == "story_changed":
                        payload["status"] = str(
                            (raw.get("detail") or {}).get("to") or ""
                        )
                    elif mapped == "gate_result":
                        event_type = str(raw.get("event", ""))
                        payload["outcome"] = (
                            "pass" if event_type == "gate_pass"
                            else "refusal" if event_type == "gate_refusal"
                            else "contract"
                        )
                    elif mapped == "evidence_captured":
                        payload["exit_code"] = (
                            raw.get("detail") or {}
                        ).get("exit_code")
                    events.append({"seq": event_seq, "event": mapped, "data": payload})
                    seq = event_seq

                # 2. Live run states (additive, idempotent)
                try:
                    inventory = run_inventory(repo_root)
                    for entry in inventory.get("runs", []):
                        if not entry.get("valid"):
                            continue
                        run = entry.get("run") or {}
                        run_seq = seq + 1
                        seq = run_seq
                        events.append({"seq": run_seq, "event": "run_changed", "data": {
                            "type": "run_changed",
                            "id": str(entry.get("run_id", "")),
                            "project": str(run.get("story", {}).get("project", "")),
                            "status": str(run.get("state", "")),
                            "timestamp": _now_ts(),
                        }})
                        for req in run.get("outstanding_requests", []):
                            req_seq = seq + 1
                            seq = req_seq
                            events.append({"seq": req_seq, "event": "request_pending", "data": {
                                "type": "request_pending",
                                "id": str(req.get("correlation_id", "")),
                                "project": str(run.get("story", {}).get("project", "")),
                                "kind": str(req.get("kind", "")),
                                "timestamp": _now_ts(),
                            }})
                except Exception:
                    pass

                # 3. Program states
                try:
                    from .program_surface import program_summary_inventory

                    prog_inv = program_summary_inventory(repo_root)
                    for summary in prog_inv.get("runs", []):
                        if not summary.get("valid"):
                            continue
                        prog_seq = seq + 1
                        seq = prog_seq
                        events.append({"seq": prog_seq, "event": "program_changed", "data": {
                            "type": "program_changed",
                            "id": str(summary.get("run_id", "")),
                            "status": str(summary.get("state", "")),
                            "timestamp": _now_ts(),
                        }})
                except Exception:
                    pass

                # 4. Notification-derived request events
                try:
                    notifs = build_notifications(repo_root)
                    for notif in notifs.get("notifications", []):
                        kind = str(notif.get("kind", ""))
                        if kind in {
                            "request-pending", "checkpoint-pending",
                            "request-republished",
                            "program-intervention-required",
                        }:
                            n_seq = seq + 1
                            seq = n_seq
                            events.append({"seq": n_seq, "event": "request_pending", "data": {
                                "type": "request_pending",
                                "id": str(notif.get("id", "")),
                                "run_id": str(notif.get("run_id", "")),
                                "kind": kind,
                                "timestamp": _now_ts(),
                            }})
                except Exception:
                    pass

                return events, seq

            # Initial fetch
            try:
                events, high_water = _synthesise(cursor)
            except Exception:
                events, high_water = [], cursor

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()

            # ── snapshot-then-tail (WLA-34-05) ───────────────────────
            # On every connect (including reconnect), emit a snapshot
            # event first so the client can rebuild correct state from
            # it without duplicating incremental events.
            try:
                snap = self._global_snapshot(repo_root)
                if not self._sse_frame("snapshot", 0, snap):
                    return True
            except Exception:
                pass

            for ev in events:
                if not self._sse_frame(ev["event"], ev["seq"], ev["data"]):
                    return True
            if not follow:
                return True

            quiet_beats = 0
            prev_water = high_water
            while True:
                _time.sleep(2)
                try:
                    batch, high_water = _synthesise(0)
                except Exception:
                    batch, high_water = [], prev_water

                # Only emit events with seq > prev_water
                new_events = [ev for ev in batch if ev["seq"] > prev_water]
                if new_events:
                    quiet_beats = 0
                    for ev in new_events:
                        if not self._sse_frame(ev["event"], ev["seq"], ev["data"]):
                            return True
                    prev_water = high_water
                else:
                    quiet_beats += 1
                    if quiet_beats >= 7:  # ~14s at 2s intervals -> keepalive every ~15s
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
            if parsed.path.rstrip("/") == "/api/terminal/exec":
                status, payload = handle_terminal_exec(root, body)
                self._send_json(status, payload)
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
        "dw-workbench: writes require guarded preview→apply or an exact "
        "single-use token; only a browser-confirmed program action may use "
        "pre-granted delivery permission, and the browser adds no authority "
        "of its own"
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
