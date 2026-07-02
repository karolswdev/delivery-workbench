"""Domain model, shared constants, and the core error type."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


PHASE_RE = re.compile(r"^phase-(\d+)-(.+)$")
STORY_RE = re.compile(r"^story-(\d+)-(.+)\.md$")
STORY_ID_RE = re.compile(r"^([A-Z][A-Z0-9]*)-(\d+)-(\d+)$")
DONE_STATUSES = {"done", "complete", "closed", "shipped"}
# The single story-status vocabulary (declared for humans in
# roadmap-builder §2.3; a unit test asserts doc/constant parity).
# Write commands reject anything else so a typo can never strand a
# story outside every view.
STORY_OPEN_STATUSES = {"backlog", "ready", "in-progress", "blocked"}
STORY_STATUSES = DONE_STATUSES | STORY_OPEN_STATUSES
# Phase-activity detection tolerates the looser phase-index vocabulary
# (planned/not-started) that may appear in legacy story tables.
OPEN_STATUSES = STORY_OPEN_STATUSES | {"planned", "not-started"}

# The generator's stand-in body for evidence created without content.
# dw check treats a done story whose evidence still carries this line
# as unproven.
EVIDENCE_PLACEHOLDER = (
    "Evidence body intentionally left for the operator to complete before commit."
)


class DwError(Exception):
    """A refusal or failure the caller can handle.

    The CLI adapter converts this to the historical ``dw: <message>``
    stderr line and exit code; library consumers (workbench server, gate
    engine) catch it instead of dying.
    """

    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def die(message: str, code: int = 1) -> None:
    raise DwError(message, code)


@dataclass
class Project:
    slug: str
    path: Path
    prefix: str


@dataclass
class Phase:
    number: int
    slug: str
    path: Path


@dataclass
class StoryRow:
    story_id: str
    title: str
    status: str
    story_file: str
    evidence: str
