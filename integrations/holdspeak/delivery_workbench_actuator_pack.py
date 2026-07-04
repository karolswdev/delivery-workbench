"""Delivery Workbench story actuator pack for HoldSpeak.

The write half of the integration (WLA-12-03), stacked on the
read-only synthesizer pack. This plugin only ever *proposes* — a
human approves in HoldSpeak, an allow-listed gated connector
executes, and even then the Delivery Workbench gate still refuses
anything the rails consider dishonest (a done-flip without
evidence, above all). An approved proposal refused by the dw gate
is the stack working, not a bug.

Exactly two actions can be proposed, and the connector's manifest
admits exactly two argv shapes:

    dw story status <project> <phase> <story> <status>
    dw story create <project> <phase> <title>

The LLM (when used) produces *fields*, never argv: fields are
validated against the live roadmap (``dw context --compact``), and
argv is built by code from the stored payload at egress time. A
deterministic path exists too: ``context["dw_action"]`` carries
explicit fields (the desk/relay seam Phase 13 builds on) and skips
the LLM entirely.

Install (both pack files ride together)::

    mkdir -p ~/.holdspeak/plugin_packs
    cp delivery_workbench_pack.py delivery_workbench_actuator_pack.py \\
       ~/.holdspeak/plugin_packs/

One plugin per pack file is the 0.3.1 loader contract (module
exports one ``MANIFEST`` + ``create_plugin``), which is why the
actuator lives beside, not inside, the synthesizer pack. Project
resolution and the roadmap reader are duplicated from the
synthesizer pack for the same reason: pack files are standalone.
Proven against holdspeak 0.3.1.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Optional

from holdspeak.plugin_sdk import validate_manifest
from holdspeak.plugins.gated_connector import (
    GatedOperation,
    WriteConnectorManifest,
    build_gated_connector,
)

IntelChat = Callable[[list[dict[str, str]]], str]

PACK_VERSION = "0.1.0"

MANIFEST = validate_manifest(
    {
        "id": "delivery_workbench_actuator",
        "label": "Delivery Workbench story actuator",
        "version": PACK_VERSION,
        "kind": "actuator",
        "required_capabilities": ["llm", "actuator"],
        "execution_mode": "inline",
        "intents": ["delivery"],
        "profiles": ["delivery"],
        "description": (
            "Proposes exactly two rails actions from a delivery "
            "meeting - a story status flip or a story create - for "
            "human approval and allow-listed execution. The dw gate "
            "keeps final say. Proven against holdspeak 0.3.1."
        ),
    }
)

_CONFIG_PATH = Path.home() / ".holdspeak" / "delivery_workbench.json"
_INTEL_FIXTURE_ENV = "DW_ACTUATOR_INTEL_FIXTURE"
_DW_TIMEOUT_SECONDS = 60

_ALLOWED_STATUSES = ("backlog", "ready", "in-progress", "blocked", "done")

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

_SYSTEM_PROMPT = (
    "You extract the single most explicit roadmap action from a "
    "delivery meeting. You are given the roadmap (projects, story "
    "IDs with titles and statuses) and a transcript.\n"
    "Reply with a single fenced json block of this exact shape:\n"
    "```json\n"
    '{"kind": "status", "project": "slug from the roadmap", '
    '"story_id": "ID from the roadmap", "status": "backlog|ready|'
    'in-progress|blocked|done", "title": null, '
    '"why": "one line quoting the meeting"}\n'
    "```\n"
    'For a new story use "kind": "create" with "title" set and '
    '"story_id": null. If the meeting contains no explicit, '
    'unambiguous action, use "kind": "none". Propose only what was '
    "actually said - never infer ambitions. Use ONLY project slugs "
    "and story IDs from the roadmap. Output only the JSON block."
)


def _parse_json_block(text: str) -> Optional[dict[str, Any]]:
    candidate = ""
    match = _JSON_FENCE_RE.search(text)
    if match:
        candidate = match.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            candidate = text[start : end + 1]
    if not candidate.strip():
        return None
    try:
        parsed = json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _load_project_map(config_path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _dw_argv_base(repo: Path) -> Optional[list[str]]:
    """The repo's own rails first, installed dw second — recorded
    decision for the story's open question."""
    repo_dw = repo / ".githooks" / "dw"
    if repo_dw.is_file() and os.access(repo_dw, os.X_OK):
        return [str(repo_dw)]
    path_dw = shutil.which("dw")
    if path_dw:
        return [path_dw, "--root", str(repo)]
    return None


def _read_roadmap(repo: Path) -> tuple[Optional[dict[str, Any]], str]:
    base = _dw_argv_base(repo)
    if base is None:
        return None, f"no dw CLI in {repo}/.githooks or on PATH"
    try:
        completed = subprocess.run(
            [*base, "context", "--compact"],
            cwd=str(repo),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=_DW_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"dw context failed to run: {exc}"
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        return None, f"dw context exited {completed.returncode}: {detail[:200]}"
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, ValueError):
        return None, "dw context did not return JSON"
    projects: dict[str, dict[str, Any]] = {}
    for project in payload.get("projects") or []:
        if not isinstance(project, dict):
            continue
        slug = str(project.get("slug") or "").strip()
        if not slug:
            continue
        stories: dict[str, dict[str, str]] = {}
        phases: dict[str, int] = {}
        for phase in project.get("phases") or []:
            number = (phase or {}).get("number")
            for story in (phase or {}).get("stories") or []:
                story_id = str((story or {}).get("story_id") or "").strip()
                if story_id:
                    stories[story_id] = {
                        "title": str(story.get("title") or ""),
                        "status": str(story.get("status") or ""),
                        "phase": str(number),
                    }
            if number is not None:
                phases[str(number)] = number
        projects[slug] = {"stories": stories, "phases": phases}
    if not projects:
        return None, "dw context returned no projects"
    return {"projects": projects}, "ok"


class DeliveryWorkbenchStoryActuator:
    id = "delivery_workbench_actuator"
    version = PACK_VERSION
    kind = "actuator"
    execution_mode = "inline"
    required_capabilities = ["llm", "actuator"]

    def __init__(
        self,
        *,
        intel_call: Optional[IntelChat] = None,
        config_path: Optional[Path] = None,
    ) -> None:
        self._intel_call_override = intel_call
        self._config_path = config_path or _CONFIG_PATH
        self._cached_provider: Any = None

    def _call_intel(self, messages: list[dict[str, str]]) -> str:
        if self._intel_call_override is not None:
            return self._intel_call_override(messages)
        if self._cached_provider is None:
            from holdspeak.intel import build_configured_meeting_intel

            self._cached_provider = build_configured_meeting_intel()
        return self._cached_provider._chat_completion_text(
            messages, temperature=0.1, max_tokens=400
        )

    def _resolve_rails_repo(self, context: dict[str, Any]) -> tuple[Optional[Path], str]:
        explicit = str(context.get("project_path") or "").strip()
        if explicit:
            path = Path(explicit)
            if path.is_dir():
                return path, "context project_path"
            return None, f"context project_path does not exist: {explicit}"
        config = _load_project_map(self._config_path)
        projects = config.get("projects")
        name = str(
            context.get("project_name") or context.get("project") or ""
        ).strip()
        if name and isinstance(projects, dict):
            mapped = str(projects.get(name) or "").strip()
            if mapped and Path(mapped).is_dir():
                return Path(mapped), f"configured mapping for {name!r}"
        default = str(config.get("default") or "").strip()
        if default and Path(default).is_dir():
            return Path(default), "configured default"
        return None, "no rails repo resolvable for this meeting"

    # ------------------------------------------------------------------

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Return exactly one proposal dict, or raise ValueError when
        there is nothing honest to propose (the host records a plain
        error; no half-formed proposal ever exists)."""
        repo, _how = self._resolve_rails_repo(context)
        if repo is None:
            raise ValueError(
                "delivery_workbench_actuator: no rails repo resolvable"
            )
        roadmap, reason = _read_roadmap(repo)
        if roadmap is None:
            raise ValueError(
                f"delivery_workbench_actuator: roadmap unreadable — {reason}"
            )

        action = context.get("dw_action")
        if not isinstance(action, dict):
            action = self._extract_action_via_llm(context, roadmap)
        return self._build_proposal(repo, roadmap, action)

    def _extract_action_via_llm(
        self, context: dict[str, Any], roadmap: dict[str, Any]
    ) -> dict[str, Any]:
        transcript = str(context.get("transcript") or "").strip()
        if not transcript:
            raise ValueError("delivery_workbench_actuator: no transcript provided")
        lines: list[str] = []
        for slug, project in sorted(roadmap["projects"].items()):
            lines.append(f"project {slug}:")
            for sid, meta in sorted(project["stories"].items()):
                lines.append(
                    f"- {sid} (phase {meta['phase']}): {meta['title']} "
                    f"[{meta['status']}]"
                )
        raw = self._call_intel(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "Roadmap:\n"
                    + "\n".join(lines)
                    + "\n\nTranscript:\n"
                    + transcript,
                },
            ]
        )
        parsed = _parse_json_block(raw or "")
        if parsed is None:
            raise ValueError(
                "delivery_workbench_actuator: intel response was not parseable JSON"
            )
        return parsed

    def _build_proposal(
        self, repo: Path, roadmap: dict[str, Any], action: dict[str, Any]
    ) -> dict[str, Any]:
        kind = str(action.get("kind") or "").strip().lower()
        if kind == "none":
            raise ValueError(
                "delivery_workbench_actuator: the meeting contains no "
                "explicit roadmap action"
            )
        project = str(action.get("project") or "").strip()
        projects = roadmap["projects"]
        if project not in projects:
            raise ValueError(
                f"delivery_workbench_actuator: project {project!r} is not "
                "on the roadmap"
            )
        why = str(action.get("why") or "").strip()

        if kind == "status":
            story_id = str(action.get("story_id") or "").strip()
            status = str(action.get("status") or "").strip().lower()
            stories = projects[project]["stories"]
            if story_id not in stories:
                raise ValueError(
                    f"delivery_workbench_actuator: story {story_id!r} is "
                    f"not on the {project!r} roadmap"
                )
            if status not in _ALLOWED_STATUSES:
                raise ValueError(
                    f"delivery_workbench_actuator: status {status!r} is not "
                    f"one of {', '.join(_ALLOWED_STATUSES)}"
                )
            meta = stories[story_id]
            preview = (
                f"Flip {story_id} ({meta['title']}) from "
                f"[{meta['status']}] to [{status}] in {project} at {repo}. "
                f"Reversal: flip the status back with the same command. "
                f"The dw gate still applies (a done-flip without evidence "
                f"will be refused)."
                + (f" Meeting basis: {why}" if why else "")
            )
            payload = {
                "repo": str(repo),
                "verb": "status",
                "project": project,
                "phase": meta["phase"],
                "story": story_id,
                "status": status,
            }
            action_name = "dw_story_status"
        elif kind == "create":
            title = str(action.get("title") or "").strip()
            phase = str(action.get("phase") or "").strip()
            phases = projects[project]["phases"]
            if not phase:
                phase = max(phases, key=lambda k: phases[k]) if phases else ""
            if phase not in phases:
                raise ValueError(
                    f"delivery_workbench_actuator: phase {phase!r} is not "
                    f"on the {project!r} roadmap"
                )
            if not title:
                raise ValueError(
                    "delivery_workbench_actuator: a story create needs a title"
                )
            preview = (
                f"Create a new story {title!r} in {project} phase {phase} "
                f"at {repo}. Reversal: the story file is deletable before "
                f"anything commits it."
                + (f" Meeting basis: {why}" if why else "")
            )
            payload = {
                "repo": str(repo),
                "verb": "create",
                "project": project,
                "phase": phase,
                "title": title,
            }
            action_name = "dw_story_create"
        else:
            raise ValueError(
                f"delivery_workbench_actuator: unknown action kind {kind!r}"
            )

        return {
            "target": "delivery-workbench",
            "action": action_name,
            "preview": preview,
            "payload": payload,
            "reversible": True,
            "required_capabilities": ["actuator"],
        }


def create_plugin() -> DeliveryWorkbenchStoryActuator:
    """Zero-arg factory (pack loader contract); same env test seam
    idea as the synthesizer pack, distinct variable."""
    fixture = os.environ.get(_INTEL_FIXTURE_ENV, "").strip()
    if fixture:
        canned = Path(fixture).read_text(encoding="utf-8")
        return DeliveryWorkbenchStoryActuator(
            intel_call=lambda _messages: canned
        )
    return DeliveryWorkbenchStoryActuator()


# ---------------------------------------------------------------------
# The connector half: the only egress, allow-listed to two argv shapes.


def build_dw_connector(repo: Path, *, runner=None):
    """A gated shell connector for one rails repo.

    The manifest pins argv[0] to the repo's own ``.githooks/dw``
    (or the installed ``dw`` with ``--root``) and admits exactly the
    two ``dw story`` verbs. argv is built here from the *stored*
    payload — never from model output — and a payload naming a
    different repo is refused before planning completes.
    """
    base = _dw_argv_base(repo)
    if base is None:
        raise ValueError(f"no dw CLI for {repo}")
    manifest = WriteConnectorManifest(
        connector_id="dw_story_writer",
        permission="shell:exec",
        label="Delivery Workbench story writer",
        description="Runs the two allow-listed dw story verbs.",
        allowed_argv_prefixes=(
            (*base, "story", "status"),
            (*base, "story", "create"),
        ),
    )

    def plan(proposal) -> GatedOperation:
        payload = dict(proposal.payload or {})
        if str(payload.get("repo") or "") != str(repo):
            raise ValueError(
                f"proposal targets repo {payload.get('repo')!r}, connector "
                f"is bound to {repo}"
            )
        verb = str(payload.get("verb") or "")
        if verb == "status":
            argv = [
                *base, "story", "status",
                str(payload["project"]), str(payload["phase"]),
                str(payload["story"]), str(payload["status"]),
            ]
        elif verb == "create":
            argv = [
                *base, "story", "create",
                str(payload["project"]), str(payload["phase"]),
                str(payload["title"]),
            ]
        else:
            # An unknown verb plans an argv the manifest cannot admit,
            # so refusal happens at the gate rather than silently here.
            argv = [*base, "story", verb]
        return GatedOperation.subprocess(
            argv,
            capture_output=True,
            text=True,
            timeout=_DW_TIMEOUT_SECONDS,
            cwd=str(repo),
        )

    def interpret(raw, op) -> dict[str, Any]:
        returncode = getattr(raw, "returncode", None)
        stdout = (getattr(raw, "stdout", "") or "").strip()
        stderr = (getattr(raw, "stderr", "") or "").strip()
        if returncode != 0:
            # The dw refusal banner rides stdout/stderr; keep it
            # verbatim so the failed proposal's error field shows
            # exactly what the rails said.
            raise RuntimeError(
                f"dw exited {returncode}: {stdout}\n{stderr}".strip()
            )
        return {"argv": list(op.argv), "stdout": stdout}

    return build_gated_connector(
        manifest,
        plan=plan,
        interpret=interpret,
        gate=manifest.build_gate(),
        runner=runner,
    )
