"""The MCP stdio server: a thin JSON adapter over the dw core.

Implements the surface contract (docs/mcp.md): newline-delimited
JSON-RPC 2.0 over stdio, protocol version pinned, tools-only
capability, strictly serial loop, python stdlib only. Every tool
calls the same ``dw_pmo`` core function the CLI calls — there is no
rule logic here, and any conditional that consults roadmap semantics
instead of the core is a defect (Phase 6 invariant).

Deliberately absent, by contract: certification, commits, and bundle
consent. Attestation is not a tool call.

``DwError`` from the core becomes a tool-level error carrying the
same refusal text the CLI prints; malformed input becomes a JSON-RPC
error and never kills the loop.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .model import DwError

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "delivery-workbench"

# JSON-RPC error codes.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def _missing_rails_message(root: Path) -> str:
    return (
        f"no Delivery Workbench rails at {root} (missing pm/roadmap or .githooks/dw). "
        "Adopt the repository first: dw install <repo> --skip-bootstrap "
        "(see docs/distribution.md)."
    )


def _has_rails(root: Path) -> bool:
    from .paths import roadmap_dir

    try:
        roadmap_dir(root)
    except DwError:
        return False
    return True


# ── tool implementations (thin adapters; core does the thinking) ────

def _tool_context(root: Path, args: dict) -> tuple[str, dict]:
    from .api import build_context_payload
    from .parse import discover_projects, get_project

    project = args.get("project")
    projects = [get_project(root, project)] if project else discover_projects(root)
    payload = build_context_payload(root, projects)
    if args.get("compact"):
        text = json.dumps(payload, sort_keys=True)
    else:
        text = json.dumps(payload, indent=2, sort_keys=True)
    return text, payload


def _tool_next(root: Path, args: dict) -> tuple[str, dict]:
    from .api import next_story
    from .parse import get_project

    project = get_project(root, args.get("project"))
    found = next_story(project, root)
    if found is None:
        return (
            "dw next: nothing actionable (no in-progress, ready, or backlog stories)",
            {"next_story": None},
        )
    text = f"{found['story_id']}\t{found['status']}\t{found['phase_path']}\t{found['title']}"
    return text, {"next_story": found}


def _tool_check(root: Path, args: dict) -> tuple[str, dict]:
    from .parse import discover_projects, get_project
    from .validate import check_project

    project = args.get("project")
    projects = [get_project(root, project)] if project else discover_projects(root)
    issues: list[str] = []
    for proj in projects:
        issues.extend(check_project(proj, root))
    if issues:
        text = "\n".join(f"ERROR {issue}" for issue in issues)
    else:
        text = "dw check: ok"
    return text, {"ok": not issues, "issues": issues}


def _tool_doctor(root: Path, args: dict) -> tuple[str, dict]:
    from .doctor import render_doctor, run_doctor

    checks = run_doctor(root)
    structured = {
        "healthy": all(check.ok for check in checks),
        "checks": [
            {"ok": check.ok, "name": check.name, "detail": check.detail}
            for check in checks
        ],
    }
    return render_doctor(checks).rstrip("\n"), structured


def _tool_verify(root: Path, args: dict) -> tuple[str, dict]:
    from .verify import render_verify, run_verify

    result = run_verify(
        root,
        range_spec=args.get("range"),
        all_history=bool(args.get("all")),
        epoch=args.get("epoch"),
    )
    structured = {
        "ok": result.ok,
        "verified": result.verified,
        "pre_epoch_skipped": result.pre_epoch_skipped,
        "out_of_scope": result.out_of_scope,
        "epoch": result.epoch,
        "error": result.error,
        "violations": [
            {"sha": v.sha, "rule": v.rule, "message": v.message}
            for v in result.violations
        ],
    }
    if result.error:
        raise DwError(f"dw verify: error: {result.error}", 2)
    return render_verify(result).rstrip("\n"), structured


def _tool_gate(root: Path, args: dict) -> tuple[str, dict]:
    from .gate import render_gate_failure, render_gate_porcelain, run_gate

    result = run_gate(root)
    structured = {
        "ok": result.ok,
        "tier": result.tier,
        "expected_boxes": result.expected_boxes,
        "checked_boxes": result.checked_boxes,
        "declared_stories": list(result.declared_stories),
        "shipped_stories": list(result.shipped_stories),
        "contract_digest": result.contract_digest,
        "failure": None
        if result.ok
        else {
            "rule": result.failure.rule,
            "message": result.failure.message,
            "remediation": result.failure.remediation,
        },
    }
    if result.ok:
        text = (
            f"dw gate: pass ({result.checked_boxes}/{result.expected_boxes} checkboxes, "
            f"{len(result.shipped_stories)} story flip(s))"
        )
    else:
        text = render_gate_failure(result).rstrip("\n")
    _ = render_gate_porcelain  # parity partner; text mirrors the CLI renderers
    return text, structured


_PROJECT_PROP = {"type": "string", "description": "Project slug (optional when the repo has exactly one project)"}

TOOLS: dict[str, dict] = {
    "dw_context": {
        "description": (
            "Machine-readable roadmap context: issues, warnings, next story, "
            "per-story trace paths. Adapter over dw_pmo.api.build_context_payload."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": _PROJECT_PROP,
                "compact": {"type": "boolean", "description": "Single-line JSON text output"},
            },
            "additionalProperties": False,
        },
        "handler": _tool_context,
    },
    "dw_next": {
        "description": (
            "The next actionable story (in-progress, then ready, then backlog). "
            "Adapter over dw_pmo.api.next_story."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"project": _PROJECT_PROP},
            "additionalProperties": False,
        },
        "handler": _tool_next,
    },
    "dw_check": {
        "description": (
            "Structural and evidence-content lint over the roadmap. "
            "Adapter over dw_pmo.validate.check_project."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"project": _PROJECT_PROP},
            "additionalProperties": False,
        },
        "handler": _tool_check,
    },
    "dw_doctor": {
        "description": (
            "Verify the rails are wired in this clone (hooksPath, hooks, core, "
            "agent docs). Adapter over dw_pmo.doctor.run_doctor."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "handler": _tool_doctor,
    },
    "dw_verify": {
        "description": (
            "Re-derive the gate's structural rules over pushed history "
            "(docs/remote-verification.md). Adapter over dw_pmo.verify.run_verify."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "range": {"type": "string", "description": "Commit range <base>..<head>"},
                "all": {"type": "boolean", "description": "Full epoch-to-HEAD sweep"},
                "epoch": {"type": "string", "description": "Rev where remote rules begin"},
            },
            "additionalProperties": False,
        },
        "handler": _tool_verify,
    },
    "dw_gate": {
        "description": (
            "Preflight the commit gate against the current stage; never consumes "
            "the contract. Adapter over dw_pmo.gate.run_gate."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "handler": _tool_gate,
    },
}


def tool_definitions() -> list[dict]:
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in TOOLS.items()
    ]


def _validate_args(schema: dict, args: dict) -> str | None:
    """Minimal schema check: unknown keys and required fields."""
    props = schema.get("properties", {})
    if not schema.get("additionalProperties", True):
        unknown = [key for key in args if key not in props]
        if unknown:
            return f"unknown parameter(s): {', '.join(sorted(unknown))}"
    missing = [key for key in schema.get("required", []) if key not in args]
    if missing:
        return f"missing required parameter(s): {', '.join(missing)}"
    return None


def call_tool(root: Path, name: str, args: dict) -> dict:
    """Dispatch one tools/call; returns the MCP result object."""
    spec = TOOLS.get(name)
    if spec is None:
        return {
            "content": [{"type": "text", "text": f"unknown tool: {name}"}],
            "isError": True,
        }
    problem = _validate_args(spec["inputSchema"], args)
    if problem is not None:
        return {
            "content": [{"type": "text", "text": f"{name}: {problem}"}],
            "isError": True,
        }
    if not _has_rails(root):
        return {
            "content": [{"type": "text", "text": _missing_rails_message(root)}],
            "isError": True,
        }
    try:
        text, structured = spec["handler"](root, args)
    except DwError as exc:
        return {
            "content": [{"type": "text", "text": f"dw: {exc.args[0]}"}],
            "isError": True,
        }
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured,
    }


# ── JSON-RPC loop ────────────────────────────────────────────────────

def _response(req_id, result=None, error=None) -> dict:
    msg: dict = {"jsonrpc": "2.0", "id": req_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    return msg


def handle_message(root: Path, message: dict) -> dict | None:
    """One request → one response dict; notifications → None."""
    req_id = message.get("id")
    method = message.get("method")

    if method is None or message.get("jsonrpc") != "2.0":
        if req_id is None:
            return None
        return _response(req_id, error={"code": INVALID_REQUEST, "message": "invalid request"})

    if method.startswith("notifications/"):
        return None  # accepted, ignored (tools-only server)

    if method == "initialize":
        requested = (message.get("params") or {}).get("protocolVersion")
        version = requested if requested == PROTOCOL_VERSION else PROTOCOL_VERSION
        from dw_pmo import __version__

        return _response(
            req_id,
            result={
                "protocolVersion": version,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": __version__},
            },
        )

    if method == "ping":
        return _response(req_id, result={})

    if method == "tools/list":
        return _response(req_id, result={"tools": tool_definitions()})

    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        if not isinstance(name, str):
            return _response(
                req_id, error={"code": INVALID_PARAMS, "message": "tools/call requires a tool name"}
            )
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            return _response(
                req_id, error={"code": INVALID_PARAMS, "message": "arguments must be an object"}
            )
        return _response(req_id, result=call_tool(root, name, args))

    return _response(req_id, error={"code": METHOD_NOT_FOUND, "message": f"method not found: {method}"})


def serve(root: Path, stdin=None, stdout=None) -> int:
    """Serial ndjson loop; returns when stdin closes."""
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            reply = _response(None, error={"code": PARSE_ERROR, "message": "parse error"})
            print(json.dumps(reply), file=stdout, flush=True)
            continue
        try:
            reply = handle_message(root, message)
        except Exception as exc:  # the loop must survive anything
            reply = _response(
                message.get("id"),
                error={"code": INTERNAL_ERROR, "message": f"internal error: {exc}"},
            )
        if reply is not None:
            print(json.dumps(reply), file=stdout, flush=True)
    return 0
