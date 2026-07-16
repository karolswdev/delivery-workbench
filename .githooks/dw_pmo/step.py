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
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Union

from .model import STORY_ID_RE
from .status import build_status

STEP_KIND = "delivery-workbench-step"
STEP_SCHEMA_VERSION = 1
STEP_RESULT_KIND = "delivery-workbench-step-result"
STEP_RESULT_SCHEMA_VERSION = 1
DEFAULT_STEP_OUTPUT_BYTES = 20_000
STEP_CLAIMS_REL = Path(".git") / "pmo-step-claims"


@dataclass(frozen=True)
class StepChild:
    """One child-process outcome, injectable for deterministic adapters/tests."""

    exit_code: int
    stdout: str | bytes = ""
    stderr: str | bytes = ""
    started: bool = True
    interrupted: bool = False
    reason: str | None = None


Runner = Callable[[list[str], Path], Union[StepChild, int]]


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


def _claims_generation(root: Path) -> str:
    """Hash claimed lease names so read-only actions mint a new next token."""
    claims = root / STEP_CLAIMS_REL
    try:
        names = sorted(
            item.name for item in claims.iterdir()
            if item.is_file() and item.name.endswith(".claim")
        )
    except FileNotFoundError:
        names = []
    except OSError as exc:
        # A deterministic sentinel keeps preview available. Apply still fails
        # closed when it cannot atomically claim the token.
        names = [f"unreadable:{exc.errno}"]
    joined = "\n".join(names).encode("utf-8")
    return "sha256:" + hashlib.sha256(joined).hexdigest()


def _status_token(status: dict[str, object], claims_generation: str) -> str:
    canonical = json.dumps(
        {"claims_generation": claims_generation, "status": status},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def build_step(root: Path, project: str | None = None) -> dict[str, object]:
    """Return the deterministic one-step preview for the current briefing."""
    root = root.resolve()
    status = build_status(root, project)
    action = status["next_action"]
    selected = status["roadmap"]["selected_project"]  # type: ignore[index]
    token = _status_token(status, _claims_generation(root))

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


def _observation(preview: dict[str, object]) -> dict[str, object]:
    action = preview.get("action")
    return {
        "token": preview.get("token"),
        "action_id": action.get("id") if isinstance(action, dict) else None,
    }


def _bounded(value: str | bytes, limit: int) -> tuple[str, bool]:
    limit = max(0, int(limit))
    raw = value if isinstance(value, bytes) else value.encode("utf-8")
    truncated = len(raw) > limit
    if truncated:
        raw = raw[:limit]
    return raw.decode("utf-8", errors="replace"), truncated


def _output(child: StepChild, limit: int) -> dict[str, object]:
    stdout, stdout_truncated = _bounded(child.stdout, limit)
    stderr, stderr_truncated = _bounded(child.stderr, limit)
    return {
        "stdout": stdout,
        "stderr": stderr,
        "truncated": {
            "stdout": stdout_truncated,
            "stderr": stderr_truncated,
        },
    }


def _result(
    preview: dict[str, object],
    *,
    outcome: str,
    started: bool,
    exit_code: int,
    reason: str | None,
    after: dict[str, object] | None = None,
    child: StepChild | None = None,
    max_output_bytes: int = DEFAULT_STEP_OUTPUT_BYTES,
) -> dict[str, object]:
    empty = StepChild(exit_code=exit_code, started=started)
    return {
        "kind": STEP_RESULT_KIND,
        "schema_version": STEP_RESULT_SCHEMA_VERSION,
        "project": preview.get("project"),
        "outcome": outcome,
        "started": started,
        "exit_code": exit_code,
        "reason": reason,
        "action": preview.get("action"),
        "before": _observation(preview),
        "after": _observation(after) if after is not None else None,
        "output": _output(child or empty, max_output_bytes),
    }


def _refusal(
    preview: dict[str, object],
    reason: str,
) -> tuple[dict[str, object], int]:
    return (
        _result(
            preview,
            outcome="refused",
            started=False,
            exit_code=1,
            reason=reason,
        ),
        1,
    )


def _claim_token(root: Path, token: str) -> str | None:
    """Atomically consume one lease. Return a refusal reason on failure."""
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", token):
        return "step token is malformed; run dw step again"
    if not (root / ".git").is_dir():
        return "step token cannot be claimed: repository Git metadata is unavailable"
    claims = root / STEP_CLAIMS_REL
    try:
        claims.mkdir(mode=0o700, parents=True, exist_ok=True)
        claim = claims / f"{token.removeprefix('sha256:')}.claim"
        with claim.open("x", encoding="utf-8") as handle:
            handle.write("claimed\n")
    except FileExistsError:
        return "step token was already applied; run dw step again"
    except OSError as exc:
        return f"step token could not be claimed safely: {exc}"
    return None


def _exit_code(code: int) -> int:
    if code < 0:
        return min(255, 128 + abs(code))
    return min(255, code)


def _run_child(argv: list[str], cwd: Path) -> StepChild:
    try:
        process = subprocess.Popen(
            argv,
            cwd=str(cwd),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return StepChild(
            exit_code=127,
            stderr=f"could not start step action: {exc}\n",
            started=False,
            reason=f"could not start step action: {exc}",
        )
    try:
        stdout, stderr = process.communicate()
        return StepChild(
            exit_code=_exit_code(process.returncode),
            stdout=stdout,
            stderr=stderr,
        )
    except KeyboardInterrupt:
        try:
            process.send_signal(signal.SIGINT)
        except OSError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except OSError:
                pass
            stdout, stderr = process.communicate()
        return StepChild(
            exit_code=130,
            stdout=stdout,
            stderr=stderr,
            interrupted=True,
            reason="step child was interrupted",
        )


def _story_id(action: object) -> str | None:
    if not isinstance(action, dict):
        return None
    command = action.get("command")
    if (
        isinstance(command, list)
        and len(command) >= 6
        and command[:2] == [".githooks/dw", "story"]
        and isinstance(command[5], str)
        and STORY_ID_RE.fullmatch(command[5])
    ):
        return command[5]
    return None


def apply_step(
    root: Path,
    project: str | None,
    expected_token: str,
    *,
    runner: Runner | None = None,
    max_output_bytes: int = DEFAULT_STEP_OUTPUT_BYTES,
) -> tuple[dict[str, object], int]:
    """Authorize one lease and return its pinned, bounded execution receipt."""
    root = root.resolve()
    preview = build_step(root, project)
    if not expected_token:
        return _refusal(
            preview,
            "dw step --apply requires --expect <token> from a fresh preview",
        )
    if expected_token != preview["token"]:
        return _refusal(
            preview,
            "step token is stale; run dw step again and review the new preview",
        )
    if not preview["applicable"]:
        return _refusal(preview, f"step is not applicable: {preview['refusal']}")

    action = preview["action"]
    command = action["command"]  # type: ignore[index]
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        return _refusal(preview, "step action lost its validated argv before execution")

    claim_refusal = _claim_token(root, expected_token)
    if claim_refusal:
        return _refusal(preview, claim_refusal)

    try:
        raw_child = (runner or _run_child)(list(command), root)
        child = raw_child if isinstance(raw_child, StepChild) else StepChild(raw_child)
    except KeyboardInterrupt:
        child = StepChild(
            130,
            started=True,
            interrupted=True,
            reason="step child was interrupted",
        )
    except OSError as exc:
        child = StepChild(
            127,
            stderr=f"could not start step action: {exc}\n",
            started=False,
            reason=f"could not start step action: {exc}",
        )
    code = _exit_code(child.exit_code)
    if child.interrupted:
        outcome = "interrupted"
        reason = child.reason or "step child was interrupted"
        code = 130
    elif not child.started:
        outcome = "failed"
        reason = child.reason or "step child could not be started"
    elif code == 0:
        outcome = "succeeded"
        reason = child.reason
    else:
        outcome = "failed"
        reason = child.reason or f"step action exited {code}"

    try:
        after = build_step(root, project)
    except Exception as exc:  # keep a started child's truthful result returnable
        after = None
        reason = reason or f"post-step observation failed: {exc}"

    result = _result(
        preview,
        outcome=outcome,
        started=child.started,
        exit_code=code,
        reason=reason,
        after=after,
        child=child,
        max_output_bytes=max_output_bytes,
    )
    if child.started:
        from .events import emit

        before_obs = result["before"]
        after_obs = result["after"]
        emit(
            root,
            "step_execution",
            project=str(result["project"] or "") or None,
            story=_story_id(action),
            detail={
                "action": before_obs["action_id"],  # type: ignore[index]
                "outcome": outcome,
                "exit_code": code,
                "before": before_obs["token"],  # type: ignore[index]
                "after": after_obs["token"] if after_obs else None,  # type: ignore[index]
                "next_action": after_obs["action_id"] if after_obs else None,  # type: ignore[index]
            },
        )
    return result, code


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
