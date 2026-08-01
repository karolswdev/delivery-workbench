"""Revisioned reusable project context (WLA-34-09).

Each project can carry a revisioned context document under
``pm/context/{project-slug}/``.  Revisions are numbered Markdown files;
``current.json`` records the accepted head.  Drafts sit alongside current
as ``draft-{N}.md`` / ``draft-{N}.json`` until explicitly accepted.

Context is advisory.  It carries no authority, satisfies no gate rule,
and substitutes for nothing.  It is injected into agent sessions as
bounded working knowledge, hash-bound to a specific revision so sessions
can declare exactly which context they received.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .model import DwError


CONTEXT_MANIFEST_VERSION = 1


def _context_dir(root: Path, project_slug: str) -> Path:
    """Return the context directory for a project, never creating it."""
    if not project_slug or "/" in project_slug or "\x00" in project_slug:
        raise DwError("invalid project slug for context: %s" % project_slug)
    return root / "pm" / "context" / project_slug


def _sha256(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DwError("context manifest is unreadable: %s" % exc) from exc


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=".%s." % path.name, dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except OSError:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _atomic_write_json(path: Path, value: dict) -> None:
    _atomic_write_text(
        path, json.dumps(value, sort_keys=True, indent=2) + "\n"
    )


def _next_revision(ctx_dir: Path) -> int:
    """Determine the next revision number by scanning existing files."""
    highest = 0
    if ctx_dir.is_dir():
        for child in ctx_dir.iterdir():
            name = child.name
            for prefix in ("revision-", "draft-"):
                if name.startswith(prefix) and name.endswith(".md"):
                    try:
                        num = int(name[len(prefix) : -3])
                        if num > highest:
                            highest = num
                    except ValueError:
                        pass
    return highest + 1


class ProjectContext:
    """Manage revisioned context per project.

    Storage layout under ``pm/context/{slug}/``::

        current.json          -- accepted head manifest
        revision-1.md         -- accepted revision content
        revision-2.md
        draft-3.md            -- pending draft content
        draft-3.json          -- draft metadata
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def current(self, project_slug: str) -> dict:
        """Return the current accepted revision content and metadata.

        Returns a dict with ``revision``, ``content``, ``content_hash``,
        ``author``, ``accepted_at``, and ``based_on_index_tree``.
        When no context exists, returns an empty-state dict.
        """
        ctx_dir = _context_dir(self.root, project_slug)
        manifest = _read_json(ctx_dir / "current.json")
        if manifest is None:
            return {
                "revision": 0,
                "content": "",
                "content_hash": "",
                "author": "",
                "accepted_at": "",
                "based_on_index_tree": "",
                "exists": False,
            }
        revision = manifest.get("revision", 0)
        rev_file = ctx_dir / ("revision-%d.md" % revision)
        content = ""
        if rev_file.is_file():
            try:
                content = rev_file.read_text(encoding="utf-8")
            except OSError:
                pass
        return {
            "revision": revision,
            "content": content,
            "content_hash": manifest.get("content_hash", ""),
            "author": manifest.get("author", ""),
            "accepted_at": manifest.get("accepted_at", ""),
            "based_on_index_tree": manifest.get("based_on_index_tree", ""),
            "exists": True,
        }

    def draft(
        self,
        project_slug: str,
        content: str,
        *,
        session_id: str | None = None,
        based_on_index_tree: str = "",
    ) -> dict:
        """Create a draft revision (not yet accepted).

        Returns draft metadata including the draft revision number
        and a preview fingerprint for the accept step.
        """
        if not isinstance(content, str) or not content.strip():
            raise DwError("context draft content must be non-empty Markdown")
        ctx_dir = _context_dir(self.root, project_slug)
        revision = _next_revision(ctx_dir)
        content_hash = _sha256(content)
        now = _utc_now()

        draft_meta = {
            "schema_version": CONTEXT_MANIFEST_VERSION,
            "revision": revision,
            "content_hash": content_hash,
            "author": "agent-draft",
            "drafted_at": now,
            "session_id": session_id or "",
            "based_on_index_tree": based_on_index_tree,
            "accepted": False,
        }
        # Fingerprint covers the content hash and revision for staleness
        fingerprint = _sha256(
            json.dumps(
                {"revision": revision, "content_hash": content_hash},
                sort_keys=True,
            )
        )
        draft_meta["fingerprint"] = fingerprint

        _atomic_write_text(ctx_dir / ("draft-%d.md" % revision), content)
        _atomic_write_json(ctx_dir / ("draft-%d.json" % revision), draft_meta)

        return {
            "revision": revision,
            "content_hash": content_hash,
            "fingerprint": fingerprint,
            "drafted_at": now,
            "author": "agent-draft",
            "applicable": True,
            "starts_work": False,
            "creates_grant": False,
            "certifies": False,
            "commits": False,
        }

    def accept(self, project_slug: str, revision: int, fingerprint: str = "") -> dict:
        """Promote a draft to the current accepted revision.

        When ``fingerprint`` is supplied, it must match the draft's stored
        fingerprint (staleness guard).
        """
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            raise DwError("context revision must be a positive integer")
        ctx_dir = _context_dir(self.root, project_slug)
        draft_md = ctx_dir / ("draft-%d.md" % revision)
        draft_json = ctx_dir / ("draft-%d.json" % revision)

        if not draft_md.is_file() or not draft_json.is_file():
            raise DwError(
                "no pending draft at revision %d for project %s"
                % (revision, project_slug)
            )

        draft_meta = _read_json(draft_json)
        if draft_meta is None:
            raise DwError("draft metadata is unreadable")
        if draft_meta.get("accepted"):
            raise DwError("draft %d is already accepted" % revision)
        if fingerprint and draft_meta.get("fingerprint") != fingerprint:
            raise DwError(
                "stale context accept: draft fingerprint does not match"
            )

        content = draft_md.read_text(encoding="utf-8")
        content_hash = _sha256(content)
        now = _utc_now()

        # Move draft to revision
        rev_file = ctx_dir / ("revision-%d.md" % revision)
        _atomic_write_text(rev_file, content)

        # Update current.json
        manifest = {
            "schema_version": CONTEXT_MANIFEST_VERSION,
            "revision": revision,
            "content_hash": content_hash,
            "author": draft_meta.get("author", "agent-draft"),
            "accepted_at": now,
            "based_on_index_tree": draft_meta.get("based_on_index_tree", ""),
        }
        _atomic_write_json(ctx_dir / "current.json", manifest)

        # Mark draft as accepted
        draft_meta["accepted"] = True
        draft_meta["accepted_at"] = now
        _atomic_write_json(draft_json, draft_meta)

        return {
            "revision": revision,
            "content_hash": content_hash,
            "accepted_at": now,
            "author": manifest["author"],
            "outcome": "accepted",
        }

    def history(self, project_slug: str) -> dict:
        """Return all revisions with metadata."""
        ctx_dir = _context_dir(self.root, project_slug)
        revisions: list[dict] = []
        drafts: list[dict] = []

        if not ctx_dir.is_dir():
            return {"revisions": revisions, "drafts": drafts, "count": 0}

        current = _read_json(ctx_dir / "current.json")
        current_rev = current.get("revision", 0) if current else 0

        for child in sorted(ctx_dir.iterdir()):
            name = child.name
            if name.startswith("revision-") and name.endswith(".md"):
                try:
                    num = int(name[len("revision-") : -3])
                except ValueError:
                    continue
                try:
                    content = child.read_text(encoding="utf-8")
                except OSError:
                    content = ""
                revisions.append({
                    "revision": num,
                    "content_hash": _sha256(content),
                    "is_current": num == current_rev,
                    "content_preview": content[:200] if content else "",
                })
            elif name.startswith("draft-") and name.endswith(".json"):
                meta = _read_json(child)
                if meta:
                    drafts.append({
                        "revision": meta.get("revision", 0),
                        "content_hash": meta.get("content_hash", ""),
                        "fingerprint": meta.get("fingerprint", ""),
                        "drafted_at": meta.get("drafted_at", ""),
                        "accepted": meta.get("accepted", False),
                        "author": meta.get("author", ""),
                    })

        revisions.sort(key=lambda r: r["revision"])
        drafts.sort(key=lambda d: d["revision"])

        return {
            "revisions": revisions,
            "drafts": drafts,
            "count": len(revisions),
            "current_revision": current_rev,
        }

    def revision_hash(self, project_slug: str) -> str:
        """Return the hash of the current revision (for session binding)."""
        cur = self.current(project_slug)
        return cur.get("content_hash", "")
