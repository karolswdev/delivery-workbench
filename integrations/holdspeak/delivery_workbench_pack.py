"""Delivery Workbench plugin pack for HoldSpeak.

One file, one synthesizer: given a delivery meeting's transcript
and a project that maps to a Delivery Workbench rails repo, ground
the meeting in the roadmap — decisions and action items mapped to
real story IDs, the next actionable story, and drift flags for
work discussed that no story covers. Read-only: this plugin never
proposes or performs a roadmap change (the story actuator is a
separate plugin, WLA-12-03).

Install
-------
Copy this file into HoldSpeak's user pack directory::

    mkdir -p ~/.holdspeak/plugin_packs
    cp delivery_workbench_pack.py ~/.holdspeak/plugin_packs/

HoldSpeak discovers it on startup (``MANIFEST`` + ``create_plugin``).
Proven against holdspeak 0.4.0 (re-certified 2026-07-05, commit
ad5cb91: all 23 pack tests pass unmodified — the plugin surface is
identical across 0.3.1, 0.4.0, and current main); the MANIFEST
version pin below is the range this pack was tested with.

Project resolution
------------------
HoldSpeak's plugin context does not carry a filesystem path, so
the pack resolves the rails repo itself, in order:

1. ``context["project_path"]`` — set by a context provider or a
   host integration (also the test seam).
2. ``~/.holdspeak/delivery_workbench.json`` — operator-owned map::

       {"projects": {"delivery-workbench": "/path/to/repo"},
        "default": "/path/to/repo"}

   The detected project name (``project_name``/``project`` in the
   context) is looked up in ``projects``; ``default`` applies when
   nothing matches or no project was detected.
3. Nothing resolvable → the honest failure shape (confidence 0.0,
   no invented alignment).

Test seam
---------
``create_plugin()`` must be zero-arg (pack loader contract), so the
LLM override for loader-path tests is an environment variable:
``DW_PACK_INTEL_FIXTURE=/path/to/canned-response.txt`` makes the
plugin return that file's content instead of calling the
configured intel provider. Unit tests construct the plugin
directly with ``intel_call=...``.
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

IntelChat = Callable[[list[dict[str, str]]], str]

PACK_VERSION = "0.1.1"

MANIFEST = validate_manifest(
    {
        "id": "delivery_workbench",
        "label": "Delivery Workbench roadmap alignment",
        "version": PACK_VERSION,
        "kind": "synthesizer",
        "required_capabilities": ["llm"],
        "execution_mode": "deferred",
        "intents": ["delivery"],
        "profiles": ["delivery"],
        "description": (
            "Grounds a delivery meeting in the project's Delivery "
            "Workbench roadmap: decisions and action items mapped to "
            "story IDs, the next actionable story, and drift flags. "
            "Read-only. Proven against holdspeak 0.4.0."
        ),
    }
)

_CONFIG_PATH = Path.home() / ".holdspeak" / "delivery_workbench.json"
_INTEL_FIXTURE_ENV = "DW_PACK_INTEL_FIXTURE"
_DW_TIMEOUT_SECONDS = 30

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

_SYSTEM_PROMPT = (
    "You align a delivery meeting with a project roadmap. You are "
    "given a meeting transcript and the roadmap: story IDs with "
    "titles and statuses, plus the next actionable story.\n"
    "Reply with a single fenced json block of this exact shape:\n"
    "```json\n"
    "{\n"
    '  "aligned": [{"item": "decision or action item, quoted or '
    'tightly paraphrased", "kind": "decision", "story_id": "ID from '
    'the roadmap list", "why": "one line"}],\n'
    '  "drift": [{"item": "work discussed that no listed story '
    'covers", "reason": "one line"}],\n'
    '  "meeting_note": "one or two sentences on what the meeting '
    'settled"\n'
    "}\n"
    "```\n"
    '"kind" is "decision" or "action_item". Use ONLY story IDs that '
    "appear in the roadmap list; if an item matches no listed story, "
    "it belongs in drift. Output only the JSON block - no prose, no "
    "extra fences."
)


def _parse_json_block(text: str) -> Optional[dict[str, Any]]:
    """Fenced-JSON first, brace-scan fallback, None when hopeless."""
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


class DeliveryWorkbenchAlignment:
    id = "delivery_workbench"
    version = PACK_VERSION
    kind = "synthesizer"
    execution_mode = "deferred"
    required_capabilities = ["llm"]

    def __init__(
        self,
        *,
        intel_call: Optional[IntelChat] = None,
        config_path: Optional[Path] = None,
    ) -> None:
        self._intel_call_override = intel_call
        self._config_path = config_path or _CONFIG_PATH
        self._cached_provider: Any = None

    # -- seams -----------------------------------------------------

    def _call_intel(self, messages: list[dict[str, str]]) -> str:
        if self._intel_call_override is not None:
            return self._intel_call_override(messages)
        if self._cached_provider is None:
            from holdspeak.intel import build_configured_meeting_intel

            self._cached_provider = build_configured_meeting_intel()
        return self._cached_provider._chat_completion_text(
            messages, temperature=0.2, max_tokens=900
        )

    # -- rails repo resolution --------------------------------------

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
            if mapped:
                path = Path(mapped)
                if path.is_dir():
                    return path, f"configured mapping for {name!r}"
                return None, f"configured path for {name!r} does not exist: {mapped}"
        default = str(config.get("default") or "").strip()
        if default:
            path = Path(default)
            if path.is_dir():
                return path, "configured default"
            return None, f"configured default does not exist: {default}"
        if name:
            return None, f"no rails repo configured for project {name!r}"
        return None, "no project detected and no default rails repo configured"

    def _read_roadmap(self, repo: Path) -> tuple[Optional[dict[str, Any]], str]:
        """Read the mission-control state feed (dw state --json,
        feed_schema 1 — docs/mission-control.md §1); digest or reason.
        Converted from private context scraping by WLA-13-02."""
        repo_dw = repo / ".githooks" / "dw"
        if repo_dw.is_file() and os.access(repo_dw, os.X_OK):
            argv = [str(repo_dw), "state", "--json"]
        else:
            path_dw = shutil.which("dw")
            if not path_dw:
                return None, f"no dw CLI in {repo}/.githooks or on PATH"
            argv = [path_dw, "--root", str(repo), "state", "--json"]
        try:
            completed = subprocess.run(
                argv,
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
            return None, (
                f"dw context exited {completed.returncode}: {detail[:200]}"
            )
        try:
            payload = json.loads(completed.stdout)
        except (json.JSONDecodeError, ValueError):
            return None, "dw state did not return JSON"
        if payload.get("feed_schema") != 1:
            return None, (
                f"feed_schema {payload.get('feed_schema')!r} is not the "
                "schema this pack was proven against (1)"
            )
        projects = payload.get("projects")
        if not isinstance(projects, list) or not projects:
            return None, "dw state returned no projects"
        stories: dict[str, dict[str, str]] = {}
        digests: list[dict[str, Any]] = []
        for project in projects:
            if not isinstance(project, dict):
                continue
            for story in project.get("stories") or []:
                story_id = str((story or {}).get("story_id") or "").strip()
                if story_id:
                    stories[story_id] = {
                        "title": str(story.get("title") or ""),
                        "status": str(story.get("status") or ""),
                    }
            digests.append(
                {
                    "slug": str(project.get("slug") or ""),
                    "next_story": project.get("next_story"),
                }
            )
        if not stories:
            return None, "the roadmap has no stories"
        return {"stories": stories, "projects": digests}, "ok"

    # -- run ---------------------------------------------------------

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        active_intents = [
            str(i).strip().lower()
            for i in (context.get("active_intents") or [])
            if str(i).strip()
        ]

        def _failure(reason: str) -> dict[str, Any]:
            return {
                "summary": f"delivery_workbench: {reason}",
                "confidence_hint": 0.0,
                "active_intents": active_intents,
            }

        transcript = str(context.get("transcript") or "").strip()
        if not transcript:
            return _failure("no transcript provided.")

        repo, how = self._resolve_rails_repo(context)
        if repo is None:
            return _failure(f"no roadmap resolvable — {how}.")
        roadmap, reason = self._read_roadmap(repo)
        if roadmap is None:
            return _failure(f"roadmap unreadable at {repo} — {reason}.")

        stories: dict[str, dict[str, str]] = roadmap["stories"]
        roadmap_lines = [
            f"- {sid}: {meta['title']} [{meta['status']}]"
            for sid, meta in sorted(stories.items())
        ]
        next_story = None
        for project in roadmap["projects"]:
            candidate = project.get("next_story")
            if isinstance(candidate, dict) and candidate.get("story_id"):
                next_story = {
                    "story_id": str(candidate.get("story_id")),
                    "title": str(candidate.get("title") or ""),
                    "status": str(candidate.get("status") or ""),
                }
                break

        user_prompt = (
            "Roadmap stories:\n"
            + "\n".join(roadmap_lines)
            + (
                f"\n\nNext actionable story: {next_story['story_id']} - "
                f"{next_story['title']}"
                if next_story
                else ""
            )
            + "\n\nTranscript:\n"
            + transcript
        )
        try:
            raw = self._call_intel(
                [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ]
            )
        except Exception as exc:  # never raise from run()
            return _failure(f"intel call failed: {exc}")

        parsed = _parse_json_block(raw or "")
        if parsed is None:
            return _failure("intel response did not contain a parseable JSON block.")

        aligned_raw = parsed.get("aligned")
        drift_raw = parsed.get("drift")
        aligned_in = aligned_raw if isinstance(aligned_raw, list) else []
        drift: list[dict[str, str]] = [
            {
                "item": str((d or {}).get("item") or "").strip(),
                "reason": str((d or {}).get("reason") or "").strip(),
            }
            for d in (drift_raw if isinstance(drift_raw, list) else [])
            if str((d or {}).get("item") or "").strip()
        ]

        # Grounding is enforced here, not trusted from the model: an
        # alignment naming a story ID that is not on the roadmap is
        # demoted to drift.
        aligned: list[dict[str, str]] = []
        for entry in aligned_in:
            if not isinstance(entry, dict):
                continue
            item = str(entry.get("item") or "").strip()
            story_id = str(entry.get("story_id") or "").strip()
            if not item:
                continue
            if story_id in stories:
                aligned.append(
                    {
                        "item": item,
                        "kind": str(entry.get("kind") or "decision").strip(),
                        "story_id": story_id,
                        "story_title": stories[story_id]["title"],
                        "story_status": stories[story_id]["status"],
                        "why": str(entry.get("why") or "").strip(),
                    }
                )
            else:
                drift.append(
                    {
                        "item": item,
                        "reason": (
                            f"model named {story_id or 'no story'}, which is "
                            "not on the roadmap"
                        ),
                    }
                )

        if not aligned and not drift:
            return _failure("nothing in the meeting aligned or drifted; no artifact.")

        meeting_note = str(parsed.get("meeting_note") or "").strip()
        summary_lines = []
        if meeting_note:
            summary_lines.append(meeting_note)
            summary_lines.append("")
        if aligned:
            summary_lines.append("**Grounded in the roadmap:**")
            for entry in aligned:
                summary_lines.append(
                    f"- `{entry['story_id']}` {entry['story_title']} "
                    f"[{entry['story_status']}] ← {entry['kind'].replace('_', ' ')}: "
                    f"{entry['item']}"
                )
            summary_lines.append("")
        if drift:
            summary_lines.append("**Drift (no story covers this):**")
            for entry in drift:
                reason = f" — {entry['reason']}" if entry["reason"] else ""
                summary_lines.append(f"- {entry['item']}{reason}")
            summary_lines.append("")
        if next_story:
            summary_lines.append(
                f"**Next actionable story:** `{next_story['story_id']}` "
                f"{next_story['title']} [{next_story['status']}]"
            )

        return {
            "summary": "\n".join(summary_lines).strip(),
            "roadmap_alignment": {
                "repo": str(repo),
                "resolved_via": how,
                "aligned": aligned,
                "drift": drift,
                "next_story": next_story,
                "grounded_story_ids": sorted({e["story_id"] for e in aligned}),
            },
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


def create_plugin() -> DeliveryWorkbenchAlignment:
    """Zero-arg factory (pack loader contract).

    ``DW_PACK_INTEL_FIXTURE`` points at a file whose content stands
    in for the intel response — the loader-path test seam and the
    offline demo mode. Unset, the plugin uses HoldSpeak's configured
    intel provider.
    """
    fixture = os.environ.get(_INTEL_FIXTURE_ENV, "").strip()
    if fixture:
        canned = Path(fixture).read_text(encoding="utf-8")
        return DeliveryWorkbenchAlignment(intel_call=lambda _messages: canned)
    return DeliveryWorkbenchAlignment()
