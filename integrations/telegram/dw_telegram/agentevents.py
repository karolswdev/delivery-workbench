"""The agent-events drain (WLA-14-02).

The dw hook seam appends whitelisted lines to an append-only JSONL
stream; this module drains it by persisted byte offset — the
ccgram-proven shape (docs/absorption-ccgram.md §1): truncation
resets honestly, partial trailing lines wait for their newline,
malformed lines are skipped, and the offset only ever moves past
complete lines so a restart never re-pushes.

`decide_pushes` is a pure decision kernel (§2's pattern, arriving
one story early because this is where it earns its keep): events
in, push directives out, no I/O — tested without mocks.
"""

from __future__ import annotations

import json
from pathlib import Path


def read_new_events(path: Path, offset: int) -> tuple[list[dict], int]:
    """(events, new_offset). Never raises; a missing file is empty."""
    try:
        size = path.stat().st_size
    except OSError:
        return [], 0
    if size < offset:
        offset = 0  # truncated or rotated: start honest, not silent
    if size == offset:
        return [], offset
    try:
        with path.open("rb") as handle:
            handle.seek(offset)
            chunk = handle.read()
    except OSError:
        return [], offset
    # Only consume complete lines; a partial tail waits for its writer.
    last_newline = chunk.rfind(b"\n")
    if last_newline < 0:
        return [], offset
    consumed = chunk[: last_newline + 1]
    events: list[dict] = []
    for raw in consumed.split(b"\n"):
        if not raw.strip():
            continue
        try:
            parsed = json.loads(raw.decode("utf-8", "replace"))
        except (json.JSONDecodeError, ValueError):
            continue  # a torn or foreign line is skipped, not fatal
        if isinstance(parsed, dict):
            events.append(parsed)
    return events, offset + len(consumed)


def decide_pushes(events: list[dict]) -> list[dict]:
    """Which drained events become chat pushes, coalesced.

    v1 policy (absorption map §1): only `Notification` pushes — it
    is the blocked-agent signal. Everything else is recorded truth
    the poll reconciles. Multiple Notifications from one session in
    one drain coalesce to the latest (the stale-status principle).
    """
    latest: dict[str, dict] = {}
    order: list[str] = []
    for event in events:
        if event.get("event") != "Notification":
            continue
        key = str(event.get("session_id") or event.get("ts") or "")
        if key not in latest:
            order.append(key)
        latest[key] = event
    return [latest[key] for key in order]


def render_push(event: dict) -> str:
    agent = str(event.get("agent") or "an agent").capitalize()
    session = str(event.get("session_id") or "")[:12]
    cwd = str(event.get("cwd") or "")
    return (
        f"⚡ {agent} session {session}… needs attention"
        + (f" (in {cwd})" if cwd else "")
        + "\n/questions shows what it's asking; /sessions to correlate."
    )
