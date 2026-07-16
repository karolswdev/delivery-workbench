"""One explicit, state-bound application of a status recommendation.

``dw status`` remains a pure briefing.  This module adds a separate handrail:
preview the current action as a deterministic lease, then apply at most that
one action if the caller presents the exact token and the action matches a
closed argv-shape table.  Certification, commit, arbitrary commands, and
automatic continuation are deliberately outside the capability.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Callable

from .model import STORY_ID_RE, die
from .status import build_status

STEP_KIND = "delivery-workbench-step"
STEP_SCHEMA_VERSION = 1

Runner = Callable[[list[str], Path], int]


def _safe_selector(value: object) -> bool:
    token = str(value or "")
    return bool(
        token
        and not token.startswith("-")
        and "/" not in token
        and "\\" not in token
        and "\0" not in token
    )


def _story_command(
    command: list[str],
    *,
    verb: str,
    final: str | None = None,
) -> bool:
    expected_length = 7 if final is not None else 6
    if len(command) != expected_length:
        return False
    if command[:3] != [".githooks/dw", "story", verb]:
        return False
    if not _safe_selector(command[3]) or not re.fullmatch(r"\d+", command[4]):
        return False
    if not STORY_ID_RE.fullmatch(command[5]):
        return False
    return final is None or command[6] == final


def _command_is_allowlisted(action: dict[str, object]) -> bool:
    """Validate both the action id and its entire argv shape.

    The status core is trusted, but this second closed table is the execution
    boundary.  A future status action is non-applicable until this table and
    its tests deliberately grant it a shape.
    """
    action_id = str(action.get("id") or "")
    raw = action.get("command")
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        return False
    command = list(raw)

    exact: dict[str, list[list[str]]] = {
        "repair-rails": [[".githooks/dw", "doctor"]],
        "resolve-rewrite": [["git", "status"]],
        "review-unstaged": [["git", "status", "--short"]],
        "review-workspace": [["git", "status", "--short"]],
        "generate-contract": [
            [".githooks/dw", "contract", "new"],
            [".githooks/dw", "contract", "new", "--force"],
        ],
        "plan-work": [[".githooks/dw", "phase", "create", "--help"]],
    }
    if action_id in exact:
        return command in exact[action_id]
    if action_id == "repair-roadmap":
        return (
            command == [".githooks/dw", "phase", "create", "--help"]
            or (
                command[:2] == [".githooks/dw", "check"]
                and len(command) in {2, 3}
                and (len(command) == 2 or _safe_selector(command[2]))
            )
        )
    if action_id == "finish-story":
        return _story_command(command, verb="status", final="done")
    if action_id == "start-story":
        return _story_command(command, verb="status", final="in-progress")
    if action_id == "continue-story":
        return _story_command(command, verb="show")
    if action_id == "review-holds":
        return (
            len(command) == 3
            and command[:2] == [".githooks/dw", "holds"]
            and _safe_selector(command[2])
        )
    return False


def _status_token(status: dict[str, object]) -> str:
    canonical = json.dumps(
        status,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def build_step(root: Path, project: str | None = None) -> dict[str, object]:
    """Return the deterministic one-step preview for the current briefing."""
    status = build_status(root.resolve(), project)
    action = status["next_action"]
    selected = status["roadmap"]["selected_project"]  # type: ignore[index]
    token = _status_token(status)

    applicable = False
    refusal: str | None = None
    if not isinstance(action, dict):
        refusal = "the briefing has no action to apply"
    elif action.get("kind") == "manual" or action.get("command") is None:
        refusal = "this recommendation requires a deliberate manual decision"
    elif action.get("id") == "commit":
        refusal = "commit remains a deliberate operator action and is never applied by dw step"
    elif not _command_is_allowlisted(action):
        refusal = "the recommendation is not in dw step's closed action/argv table"
    else:
        applicable = True

    apply_command: list[str] | None = None
    if applicable:
        apply_command = [".githooks/dw", "step"]
        if selected:
            apply_command.append(str(selected))
        apply_command.extend(["--apply", "--expect", token])

    return {
        "kind": STEP_KIND,
        "schema_version": STEP_SCHEMA_VERSION,
        "project": selected,
        "token": token,
        "action": action,
        "applicable": applicable,
        "refusal": refusal,
        "apply_command": apply_command,
    }


def apply_step(
    root: Path,
    project: str | None,
    expected_token: str,
    *,
    runner: Runner | None = None,
) -> tuple[dict[str, object], int]:
    """Re-read, authorize, and start at most one current recommendation."""
    preview = build_step(root, project)
    if not expected_token:
        die("dw step --apply requires --expect <token> from a fresh preview")
    if expected_token != preview["token"]:
        die("step token is stale; run dw step again and review the new preview")
    if not preview["applicable"]:
        die(f"step is not applicable: {preview['refusal']}")

    action = preview["action"]
    command = action["command"]  # type: ignore[index]
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        die("step action lost its validated argv before execution")

    if runner is None:
        def run_child(argv: list[str], cwd: Path) -> int:
            try:
                return subprocess.run(argv, cwd=str(cwd), check=False).returncode
            except OSError as exc:
                die(f"could not start step action: {exc}", code=127)
        runner = run_child
    return preview, runner(list(command), root.resolve())


def render_step(preview: dict[str, object]) -> str:
    action = preview["action"]
    command = action.get("command") if isinstance(action, dict) else None
    shown = shlex.join(command) if isinstance(command, list) else "(manual)"
    apply_command = preview["apply_command"]
    apply_shown = shlex.join(apply_command) if isinstance(apply_command, list) else "(not applicable)"
    return "\n".join(
        [
            (
                f"step=preview action={action.get('id') if isinstance(action, dict) else 'none'} "
                f"applicable={'yes' if preview['applicable'] else 'no'}"
            ),
            f"command={shown}",
            f"token={preview['token']}",
            f"apply={apply_shown}",
            f"refusal={preview['refusal'] or '-'}",
        ]
    ) + "\n"
