"""One deterministic local briefing before a human or agent acts.

The status model composes the existing authorities -- doctor, roadmap
validation, state feed, holds, Git plumbing, and the commit gate.  It
does not parse a second roadmap dialect or implement a second rule.  The
contract is ``docs/status-briefing.md``.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from .api import next_story, parked_summary
from .contract import CONTRACT_REL, parse_contract_facts
from .doctor import run_doctor
from .gitio import current_branch, head_sha, in_rewrite_state, write_tree
from .model import DwError, normalize_status
from .parse import discover_projects, get_project
from .paths import read_text
from .riderdocs import rider_docs_issues
from .statefeed import build_state_feed
from .validate import check_project, project_warnings

STATUS_KIND = "delivery-workbench-status"
STATUS_SCHEMA_VERSION = 1
PATH_LIMIT = 50


def _git_status(root: Path) -> dict[str, dict[str, object]]:
    """Return bounded, path-safe change buckets from porcelain v1.

    Git's ``-z`` form is the only safe way to handle whitespace and
    newlines in paths.  Rename/copy records carry a second NUL token;
    both old and new names are reported so a briefing never hides half
    of the workspace transition.
    """
    try:
        raw = subprocess.check_output(
            [
                "git", "-C", str(root), "status", "--porcelain=v1",
                "-z", "--untracked-files=all",
            ],
            stdin=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        raw = b""

    found: dict[str, set[str]] = {
        "staged": set(),
        "unstaged": set(),
        "untracked": set(),
    }
    tokens = raw.split(b"\0")
    i = 0
    while i < len(tokens):
        token = tokens[i]
        i += 1
        if not token or len(token) < 3:
            continue
        code = token[:2].decode("ascii", "replace")
        path = os.fsdecode(token[3:])
        paths = [path]
        if (code[0] in {"R", "C"} or code[1] in {"R", "C"}) and i < len(tokens):
            old = os.fsdecode(tokens[i])
            i += 1
            if old:
                paths.append(old)
        if code == "??":
            found["untracked"].update(paths)
            continue
        if code[0] not in {" ", "?"}:
            found["staged"].update(paths)
        if code[1] not in {" ", "?"}:
            found["unstaged"].update(paths)

    result: dict[str, dict[str, object]] = {}
    for name in ("staged", "unstaged", "untracked"):
        paths = sorted(found[name])
        result[name] = {"count": len(paths), "paths": paths[:PATH_LIMIT]}
    return result


def _box_counts(text: str) -> tuple[int, int]:
    checked = 0
    total = 0
    for line in text.splitlines():
        if line.startswith("- [x] ") or line.startswith("- [X] "):
            checked += 1
            total += 1
        elif line.startswith("- [ ] "):
            total += 1
    return checked, total


def _gate_and_contract(root: Path, staged_count: int) -> tuple[dict[str, object], dict[str, object]]:
    path = root / CONTRACT_REL
    exists = path.is_file()
    text = read_text(path) if exists else ""
    facts = parse_contract_facts(text) if text else None
    checked, expected = _box_counts(text)
    facts_fresh: bool | None = None
    if facts is not None:
        facts_fresh = (
            facts["branch"] == current_branch(root)
            and facts["head"] == (head_sha(root) or "none")
            and facts["index_tree"] == (write_tree(root) or "unknown")
        )

    gate: dict[str, object] = {
        "state": "not-applicable",
        "ok": None,
        "failure": None,
        "checked_boxes": 0,
        "expected_boxes": 0,
        "declared_stories": [],
        "shipped_stories": [],
    }
    state = "absent"
    tier: str | None = None
    story_ids: list[str] = []
    if facts is None and exists:
        state = "invalid"
    elif facts is not None:
        tier = str(facts.get("tier") or "full")
        story_ids = [str(item) for item in facts.get("story_ids", [])]
        state = "stale" if not facts_fresh else "unchecked"

    if staged_count:
        # Side-effect-free inspection is load-bearing: a read must not
        # append gate_pass/gate_refusal to the rail event log.
        from .gate import run_gate

        result = run_gate(root, record_event=False)
        failure = None
        if result.failure is not None:
            failure = {
                "rule": result.failure.rule,
                "message": result.failure.message,
                "remediation": result.failure.remediation,
            }
        gate = {
            "state": "pass" if result.ok else "fail",
            "ok": result.ok,
            "failure": failure,
            "checked_boxes": result.checked_boxes,
            "expected_boxes": result.expected_boxes,
            "declared_stories": list(result.declared_stories),
            "shipped_stories": list(result.shipped_stories),
        }
        if result.ok:
            state = "passing"
        elif state not in {"absent", "invalid", "stale"}:
            rule = result.failure.rule if result.failure else ""
            state = "unchecked" if rule == "contract-unchecked" else "refused"

    contract = {
        "state": state,
        "path": CONTRACT_REL,
        "exists": exists,
        "facts_fresh": facts_fresh,
        "checked_boxes": checked,
        "expected_boxes": expected,
        "story_ids": story_ids,
        "tier": tier,
    }
    return gate, contract


def _status_counts(feed_project: dict[str, object]) -> dict[str, int]:
    current = feed_project.get("current_phase")
    current_number = current.get("number") if isinstance(current, dict) else None
    counts: dict[str, int] = {}
    for story in feed_project.get("stories", []):  # type: ignore[union-attr]
        if current_number is not None and story.get("phase") != current_number:
            continue
        token = normalize_status(str(story.get("status") or ""))
        if token:
            counts[token] = counts.get(token, 0) + 1
    return dict(sorted(counts.items()))


def _roadmap_state(root: Path, project_selector: str | None) -> tuple[dict[str, object], dict[str, object] | None]:
    """Build status's bounded roadmap summary from existing read models."""
    projects = discover_projects(root)
    selected = get_project(root, project_selector) if project_selector else (
        projects[0] if len(projects) == 1 else None
    )
    feed_by_slug = {
        str(item["slug"]): item
        for item in build_state_feed(root)["projects"]
    }

    issues: list[str] = [] if projects else ["no roadmap projects found"]
    warnings: list[str] = []
    project_items: list[dict[str, object]] = []
    for project in projects:
        project_issues = check_project(project, root)
        project_warnings_ = project_warnings(project, root)
        issues.extend(project_issues)
        warnings.extend(project_warnings_)
        feed_project = feed_by_slug[project.slug]
        project_items.append(
            {
                "slug": project.slug,
                "prefix": project.prefix,
                "current_phase": feed_project.get("current_phase"),
                "next_story": feed_project.get("next_story"),
                "parked_counts": parked_summary(project, root)["counts"],
                "status_counts": _status_counts(feed_project),
            }
        )
    issues.extend(rider_docs_issues(root))
    selected_item = next(
        (item for item in project_items if selected and item["slug"] == selected.slug),
        None,
    )
    if selected_item is not None and selected is not None:
        # Internal-only routing fact. The stable state-feed next_story
        # shape intentionally omits phase, but a command must target the
        # phase that actually owns the story (the README pointer can
        # legally name a different, even closed, phase).
        selected_item = dict(selected_item)
        actual_next = next_story(selected, root)
        selected_item["_next_phase"] = actual_next.get("phase") if actual_next else None
    return (
        {
            "healthy": not issues,
            "selected_project": selected.slug if selected else None,
            "selection_required": len(projects) > 1 and selected is None,
            "issues": issues,
            "warnings": warnings,
            "projects": project_items,
        },
        selected_item,
    )


def _action(
    action_id: str,
    reason: str,
    command: list[str] | None,
    *,
    blocking: bool = False,
) -> dict[str, object]:
    return {
        "id": action_id,
        "kind": "command" if command is not None else "manual",
        "blocking": blocking,
        "reason": reason,
        "command": command,
    }


_REGENERATE_RULES = {
    "contract-missing",
    "contract-facts-missing",
    "contract-index-tree-mismatch",
    "contract-head-mismatch",
    "contract-branch-mismatch",
    "contract-sample-mismatch",
    "contract-tier-mismatch",
    "contract-tests-capture-mismatch",
    "contract-unknown-box",
    "contract-missing-box",
    "contract-boxes",
}


def _choose_action(
    rails: dict[str, object],
    roadmap: dict[str, object],
    selected: dict[str, object] | None,
    repository: dict[str, object],
) -> dict[str, object]:
    if not rails["healthy"]:
        failed = next((c for c in rails["checks"] if not c["ok"]), None)  # type: ignore[union-attr]
        reason = str(failed["detail"]) if failed else "required clone wiring is unhealthy"
        return _action("repair-rails", reason, [".githooks/dw", "doctor"], blocking=True)
    if not roadmap["healthy"]:
        first = str(roadmap["issues"][0])  # type: ignore[index]
        command = (
            [".githooks/dw", "phase", "create", "--help"]
            if first == "no roadmap projects found"
            else [".githooks/dw", "check"]
        )
        if roadmap["selected_project"]:
            command.append(str(roadmap["selected_project"]))
        return _action("repair-roadmap", first, command, blocking=True)
    if repository["operation"] == "rewrite":
        return _action(
            "resolve-rewrite",
            "Git has a rebase, cherry-pick, or revert in progress",
            ["git", "status"],
            blocking=True,
        )
    if roadmap["selection_required"]:
        slugs = ", ".join(str(p["slug"]) for p in roadmap["projects"])  # type: ignore[union-attr]
        return _action("select-project", f"choose one roadmap project: {slugs}", None)

    changes = repository["changes"]
    staged = int(changes["staged"]["count"])  # type: ignore[index]
    unstaged = int(changes["unstaged"]["count"])  # type: ignore[index]
    untracked = int(changes["untracked"]["count"])  # type: ignore[index]
    if staged and (unstaged or untracked):
        return _action(
            "review-unstaged",
            f"{staged} staged path(s) coexist with {unstaged + untracked} unstaged/untracked path(s)",
            ["git", "status", "--short"],
        )
    if staged:
        contract = repository["contract"]
        gate = repository["gate"]
        if contract["state"] in {"absent", "invalid", "stale"}:  # type: ignore[union-attr]
            command = [".githooks/dw", "contract", "new"]
            if contract["exists"]:  # type: ignore[index]
                command.append("--force")
            return _action(
                "generate-contract",
                f"{staged} staged path(s); contract is {contract['state']}",  # type: ignore[index]
                command,
            )
        failure = gate.get("failure")  # type: ignore[union-attr]
        rule = str(failure.get("rule") or "") if isinstance(failure, dict) else ""
        if rule == "contract-unchecked":
            return _action(
                "certify-contract",
                "verify every rule, then deliberately check the remaining boxes in .tmp/CONTRACT.md",
                None,
            )
        if gate["ok"] is False:  # type: ignore[index]
            if rule in _REGENERATE_RULES:
                return _action(
                    "generate-contract",
                    str(failure.get("remediation") or "regenerate the staged contract"),  # type: ignore[union-attr]
                    [".githooks/dw", "contract", "new", "--force"],
                )
            return _action(
                "repair-gate",
                str(failure.get("remediation") or failure.get("message") or "the gate refuses"),  # type: ignore[union-attr]
                None,
            )
        if gate["ok"] is True:  # type: ignore[index]
            return _action(
                "commit",
                f"the live gate passes for {staged} staged path(s)",
                ["git", "commit"],
            )

    next_story = selected.get("next_story") if selected else None
    if isinstance(next_story, dict) and normalize_status(str(next_story.get("status"))) == "in-progress":
        phase = selected.get("current_phase") or {}
        phase_number = selected.get("_next_phase") or phase.get("number", "")
        return _action(
            "continue-story",
            f"{next_story['story_id']} is already in progress",
            [
                ".githooks/dw", "story", "show",
                str(roadmap["selected_project"]),
                str(phase_number),
                str(next_story["story_id"]),
            ],
        )
    if int(changes["unstaged"]["count"]) or int(changes["untracked"]["count"]):  # type: ignore[index]
        return _action(
            "review-workspace",
            "workspace changes exist but no story is in progress; align them before starting new work",
            ["git", "status", "--short"],
        )
    if isinstance(next_story, dict):
        phase = selected.get("current_phase") or {}
        phase_number = selected.get("_next_phase") or phase.get("number", "")
        return _action(
            "start-story",
            f"{next_story['story_id']} is the next {normalize_status(str(next_story.get('status')))} story",
            [
                ".githooks/dw", "story", "status",
                str(roadmap["selected_project"]),
                str(phase_number),
                str(next_story["story_id"]), "in-progress",
            ],
        )
    parked = selected.get("parked_counts") if selected else None
    if isinstance(parked, dict) and sum(int(v) for v in parked.values()):
        return _action(
            "review-holds",
            "nothing is actionable, but recorded work is parked",
            [".githooks/dw", "holds", str(roadmap["selected_project"])],
        )
    command = [".githooks/dw", "phase", "create", "--help"]
    return _action("plan-work", "no actionable or parked story exists", command)


def build_status(root: Path, project: str | None = None) -> dict[str, object]:
    root = root.resolve()
    checks = run_doctor(root)
    rails = {
        "healthy": all(check.ok for check in checks),
        "checks": [
            {"ok": check.ok, "name": check.name, "detail": check.detail}
            for check in checks
        ],
    }

    try:
        roadmap, selected = _roadmap_state(root, project)
    except DwError:
        # Doctor already carries the actionable missing-roadmap failure.
        # An explicitly invalid selector remains a caller error.
        if project:
            raise
        roadmap = {
            "healthy": False,
            "selected_project": None,
            "selection_required": False,
            "issues": ["no roadmap projects found"],
            "warnings": [],
            "projects": [],
        }
        selected = None

    changes = _git_status(root)
    staged = int(changes["staged"]["count"])
    gate, contract = _gate_and_contract(root, staged)
    repository = {
        "root": str(root),
        "branch": current_branch(root),
        "head": head_sha(root),
        "operation": "rewrite" if in_rewrite_state(root) else "normal",
        "clean": not any(int(bucket["count"]) for bucket in changes.values()),
        "changes": changes,
        "contract": contract,
        "gate": gate,
    }
    verdict = (
        "ready"
        if rails["healthy"] and roadmap["healthy"] and repository["operation"] == "normal"
        else "attention"
    )
    action = _choose_action(rails, roadmap, selected, repository)
    summary = f"{verdict} — {action['reason']}"
    return {
        "kind": STATUS_KIND,
        "schema_version": STATUS_SCHEMA_VERSION,
        "verdict": verdict,
        "summary": summary,
        "repository": repository,
        "rails": rails,
        "roadmap": roadmap,
        "actions": [action],
        "next_action": action,
    }


def render_status(status: dict[str, object]) -> str:
    action = status["next_action"]
    command = action["command"]  # type: ignore[index]
    shown = shlex.join(command) if command is not None else "(manual)"
    repository = status["repository"]
    changes = repository["changes"]  # type: ignore[index]
    roadmap = status["roadmap"]
    lines = [
        f"status={status['verdict']} summary={status['summary']}",
        f"next={action['id']} command={shown}",  # type: ignore[index]
        (
            f"repo branch={repository['branch']} operation={repository['operation']} "  # type: ignore[index]
            f"clean={'yes' if repository['clean'] else 'no'} "  # type: ignore[index]
            f"staged={changes['staged']['count']} unstaged={changes['unstaged']['count']} "  # type: ignore[index]
            f"untracked={changes['untracked']['count']} contract={repository['contract']['state']} "  # type: ignore[index]
            f"gate={repository['gate']['state']}"  # type: ignore[index]
        ),
        (
            f"rails healthy={'yes' if status['rails']['healthy'] else 'no'} "  # type: ignore[index]
            f"checks={len(status['rails']['checks'])}"  # type: ignore[index]
        ),
        (
            f"roadmap healthy={'yes' if roadmap['healthy'] else 'no'} "  # type: ignore[index]
            f"project={roadmap['selected_project'] or '-'} "  # type: ignore[index]
            f"issues={len(roadmap['issues'])} warnings={len(roadmap['warnings'])}"  # type: ignore[index]
        ),
    ]
    for warning in roadmap["warnings"]:  # type: ignore[union-attr]
        lines.append(f"warning={warning}")
    return "\n".join(lines) + "\n"
