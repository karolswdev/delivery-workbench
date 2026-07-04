"""Chat rendering — the Delivery Workbench level of abstraction.

Phases, stories, gates, refusals; never raw terminal noise (the one
exception is the explicitly requested capture-pane preview, which
is verbatim by §4 ring 1). Plain text, no parse mode, truncated to
Telegram's message ceiling.
"""

from __future__ import annotations

MESSAGE_LIMIT = 3900  # Telegram caps at 4096; leave headroom


def clip(text: str, limit: int = MESSAGE_LIMIT) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 2] + " …"


def render_state(feed: dict) -> str:
    lines: list[str] = []
    for project in feed.get("projects") or []:
        lines.append(f"◆ {project.get('slug')}")
        current = project.get("current_phase")
        if current:
            lines.append(
                f"  phase {current.get('number')} — {current.get('title')} "
                f"[{current.get('status')}] "
                f"{current.get('stories_done')}/{current.get('stories_total')} done"
            )
        nxt = project.get("next_story")
        lines.append(
            f"  next: {nxt['story_id']} — {nxt['title']} [{nxt['status']}]"
            if nxt
            else "  next: nothing actionable"
        )
        warnings = project.get("warnings")
        if warnings:
            lines.append(f"  ⚠ {warnings} warning(s)")
    return clip("\n".join(lines) or "no projects on the rails here")


def render_events(events: list) -> str:
    if not events:
        return "no rail events yet"
    lines = []
    for entry in events:
        detail = entry.get("detail") or {}
        detail_part = " ".join(
            f"{key}={value}"
            for key, value in sorted(detail.items())
            if value is not None
        )
        lines.append(
            f"{entry.get('ts', '?')}  {entry.get('event', '?')}"
            + (f"  {entry.get('story')}" if entry.get("story") else "")
            + (f"  {detail_part}" if detail_part else "")
        )
    return clip("\n".join(lines))


def _session_line(session: dict) -> str:
    stories = session.get("stories") or []
    where = {
        "on_story": stories[0]["story_id"] if stories else "?",
        "ambiguous": "ambiguous: "
        + ", ".join(s["story_id"] for s in stories),
        "idle_on_rails": "idle on the rails",
        "off_rails": "off the rails",
        "unreadable": "roadmap unreadable",
    }.get(session.get("correlation"), str(session.get("correlation")))
    flags = []
    if session.get("awaiting_response"):
        flags.append("awaiting a response")
    if session.get("stale"):
        flags.append("stale")
    tmux = session.get("tmux") or {}
    return (
        f"{session.get('key')} — {session.get('agent')} — {where}"
        + (f" ({'; '.join(flags)})" if flags else "")
        + (f"  tmux:{tmux.get('session')}" if tmux.get("session") else "")
    )


def render_sessions(doc: dict) -> str:
    if doc.get("registry") != "ok":
        return f"sessions: registry {doc.get('registry')}"
    sessions = doc.get("sessions") or []
    if not sessions:
        return "no live agent sessions"
    return clip("\n".join(_session_line(s) for s in sessions))


def render_question(session: dict) -> str:
    stories = session.get("stories") or []
    story = stories[0]["story_id"] if stories else None
    agent = (session.get("agent") or "an agent").capitalize()
    heading = (
        f"{agent} on {story} is asking:" if story else f"{agent} is asking:"
    )
    question = str(session.get("last_assistant_text") or "").strip()
    return clip(
        f"{heading}\n\n{question}\n\n"
        f"Reply with: /reply {session.get('key')} <your answer>"
    )
