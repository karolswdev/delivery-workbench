"""The kanban board (WLA-17-04): one view of what's where.

``board_model`` derives, per phase, the six status columns from the
same read layer everything else uses — normalized statuses, hold
notes, evidence receipts. ``render_board`` draws it for a terminal.
Read-only by construction: the board never writes.

Bucketing is honest about legacy trees: decorated statuses normalize
before bucketing, loose phase-index vocabulary (planned, scaffolded,
not-started…) lands in backlog, retired rows (struck/cut) are history
— excluded from the columns but counted, never silently dropped.
"""

from __future__ import annotations

from pathlib import Path

from .model import (
    CUT_STATUSES,
    DONE_STATUSES,
    HOLD_STATUSES,
    Project,
    normalize_status,
    row_is_retired,
    status_note,
)
from .parse import (
    discover_phases,
    link_target,
    parse_current_phase_dirname,
    parse_story_rows,
    phase_header_status,
    phase_story_files,
    story_num_from_file,
)
from .paths import rel

BOARD_COLUMNS = ("backlog", "ready", "in-progress", "blocked", "on-hold", "done")

BOARD_KIND = "delivery-workbench-board"
BOARD_SCHEMA_VERSION = 1


# The one place link shapes are minted (WLA-18-01): every consumer —
# the board, the holds ledger, story detail — derives its workbench
# routes here, so a route rename cannot strand a stale link shape in
# one surface. A test resolves every emitted link against handle_api.
def story_links(slug: str, story_id: str) -> dict[str, str]:
    return {
        "story": f"/api/projects/{slug}/stories/{story_id}",
        "trace": f"/api/projects/{slug}/trace/{story_id}",
    }


def phase_links(slug: str, number: int) -> dict[str, str]:
    return {"phase": f"/api/projects/{slug}/phases/{number}"}


def story_paths(phase_path, story_file_cell: str, story_num: int | None, root) -> dict[str, str]:
    """Repo-relative receipts for one story row. The evidence path is
    emitted even before the file exists — the address is stable, the
    paired ``evidence_exists`` flag tells the truth about occupancy."""
    story_target = link_target(story_file_cell)
    return {
        "story": rel((phase_path / story_target).resolve(), root),
        "evidence": (
            rel(phase_path / f"evidence-story-{story_num:02d}.md", root)
            if story_num is not None else ""
        ),
        "phase_status": rel(phase_path / "current-phase-status.md", root),
    }

# How many cards a rendered column shows before folding into "+N more".
_MAX_ROWS = 8


def board_bucket(token: str) -> str | None:
    """Map a normalized status token to its board column.

    Returns None for retired history (cut/cancelled/superseded) —
    callers count those separately. Anything open and unrecognized
    (planned, scaffolded, a typo'd legacy status) is backlog: visible
    beats lost.
    """
    if token in DONE_STATUSES:
        return "done"
    if token in CUT_STATUSES:
        return None
    if token == "blocked":
        return "blocked"
    if token in HOLD_STATUSES:
        return "on-hold"
    if token in ("in-progress", "ready"):
        return token
    return "backlog"


def board_model(project: Project, root: Path) -> dict[str, object]:
    """The whole project as swimlanes × status columns.

    Phase order: open lanes first (the README pointer's lane leading),
    closed lanes after — a 90-phase legacy tree stays scannable.
    """
    pointer = parse_current_phase_dirname(project)
    lanes: list[dict[str, object]] = []
    for phase in discover_phases(project):
        status_file = phase.path / "current-phase-status.md"
        header = phase_header_status(status_file)
        paused = normalize_status(header) == "paused"
        closed = (phase.path / "final-summary.md").exists()
        columns: dict[str, list[dict[str, object]]] = {c: [] for c in BOARD_COLUMNS}
        retired = 0
        for row in parse_story_rows(status_file):
            if row_is_retired(row):
                retired += 1
                continue
            token = normalize_status(row.status)
            bucket = board_bucket(token)
            if bucket is None:
                retired += 1
                continue
            num = story_num_from_file(row.story_file)
            evidence_exists = (
                num is not None and (phase.path / f"evidence-story-{num:02d}.md").exists()
            )
            columns[bucket].append(
                {
                    "story_id": row.story_id,
                    "title": row.title,
                    "status": token,
                    "note": status_note(row.status),
                    "evidence_exists": evidence_exists,
                    "paths": story_paths(phase.path, row.story_file, num, root),
                    "links": story_links(project.slug, row.story_id),
                }
            )
        story_count = sum(len(cards) for cards in columns.values())
        # Honesty about table-less legacy phases: story FILES on disk
        # that no table row covers are named, never silently absent.
        covered = {story_num_from_file(row.story_file) for row in parse_story_rows(status_file)}
        uncovered_files = [num for num in phase_story_files(phase.path) if num not in covered]
        lanes.append(
            {
                "number": phase.number,
                "slug": phase.slug,
                "path": phase.path.name,
                "closed": closed,
                "paused": paused,
                "pause_note": status_note(header) if paused else "",
                "is_pointer": phase.path.name == pointer,
                "retired": retired,
                "uncovered_story_files": len(uncovered_files),
                "done_count": len(columns["done"]),
                "story_count": story_count,
                "paths": {"phase_status": rel(status_file, root)},
                "links": phase_links(project.slug, phase.number),
                "columns": columns,
            }
        )
    lanes.sort(key=lambda lane: (lane["closed"], not lane["is_pointer"], lane["number"]))
    return {
        "kind": BOARD_KIND,
        "schema_version": BOARD_SCHEMA_VERSION,
        "project": project.slug,
        "prefix": project.prefix,
        "columns": list(BOARD_COLUMNS),
        "phases": lanes,
    }


def _card_label(card: dict[str, object]) -> str:
    return f"{card['story_id']}{' ✓' if card['evidence_exists'] else ''}"


def _render_lane(lane: dict[str, object], max_rows: int) -> list[str]:
    columns: dict[str, list[dict[str, object]]] = lane["columns"]  # type: ignore[assignment]
    head = f"phase {lane['number']} · {lane['slug']}"
    if lane["is_pointer"]:
        head = "▶ " + head
    if lane["paused"]:
        head += f"   ⏸ paused ({lane['pause_note']})"
    if lane["retired"]:
        head += f"   ({lane['retired']} retired row{'s' if lane['retired'] != 1 else ''} not shown)"
    lines = [head]

    cells: dict[str, list[str]] = {}
    for column in BOARD_COLUMNS:
        cards = columns[column]
        labels = [_card_label(card) for card in cards[:max_rows]]
        if len(cards) > max_rows:
            labels.append(f"+{len(cards) - max_rows} more")
        cells[column] = labels
    width = {
        column: max([len(column)] + [len(label) for label in cells[column]]) + 2
        for column in BOARD_COLUMNS
    }
    lines.append("  " + "".join(column.ljust(width[column]) for column in BOARD_COLUMNS))
    height = max((len(labels) for labels in cells.values()), default=0)
    if height == 0:
        uncovered = lane.get("uncovered_story_files", 0)
        if uncovered:
            lines.append(f"  (no story table — {uncovered} story file{'s' if uncovered != 1 else ''} on disk, unlisted; see dw check)")
        else:
            lines.append("  (no stories yet)")
    for i in range(height):
        lines.append(
            "  "
            + "".join(
                (cells[column][i] if i < len(cells[column]) else "").ljust(width[column])
                for column in BOARD_COLUMNS
            ).rstrip()
        )
    notes = [
        f"  · {card['story_id']} [{card['status']}]: {card['note'] or '(no reason recorded)'}"
        for column in ("blocked", "on-hold")
        for card in columns[column]
    ]
    lines.extend(notes)
    return lines


def render_board(model: dict[str, object], expand_closed: bool = False, max_rows: int = _MAX_ROWS) -> str:
    """Draw the board. Open lanes get the full grid; closed lanes fold
    to one line each unless expand_closed — nothing is ever silently
    dropped, a fold always says what it holds."""
    lines: list[str] = [f"{model['project']} — the board"]
    closed_folded: list[str] = []
    for lane in model["phases"]:  # type: ignore[union-attr]
        if lane["closed"] and not expand_closed:
            closed_folded.append(
                f"  phase {lane['number']} · {lane['slug']} — closed, {lane['done_count']}/{lane['story_count']} done"
            )
            continue
        lines.append("")
        lines.extend(_render_lane(lane, max_rows))
    if closed_folded:
        lines.append("")
        lines.append(f"closed phases ({len(closed_folded)}) — dw board --all to expand:")
        lines.extend(closed_folded)
    return "\n".join(lines)
