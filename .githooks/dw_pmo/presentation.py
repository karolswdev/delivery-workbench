"""Shared everyday presentation over canonical Delivery Workbench facts.

The exact status, setup, run, program, notification, and roadmap documents
remain the machine contracts.  This module is the presentation boundary for
human adapters: it gives every product concept one name, groups already
derived facts into an ordinary task view, and keeps exact identifiers and
commands under the explicit ``Technical details`` label.

Nothing here decides eligibility, selects work, grants permission, measures
cost, evaluates review, recovers work, or performs an action.
"""

from __future__ import annotations

import json
import re
import shlex
from typing import Any


PRESENTATION_KIND = "delivery-workbench-presentation"
PRESENTATION_SCHEMA_VERSION = 1
TECHNICAL_DETAILS_LABEL = "Technical details"
DIFFERENT_MODEL_FAMILY_COPY = "reviewed by a different model family"

# BEGIN EVERYDAY PRESENTATION COPY
# The executable product-language checker compares this census and every
# preferred term with docs/product-language-contract-v1.json.
PRODUCT_CONCEPTS = {
    "delivery_plan": {
        "preferred": "delivery plan",
        "definition": (
            "The reviewed scope, route, quality points, decision points, "
            "limits, and stop conditions for a bounded delivery."
        ),
    },
    "team": {
        "preferred": "team",
        "definition": (
            "The named people or agents responsible for doing, reviewing, "
            "deciding, or auditing this delivery."
        ),
    },
    "work": {
        "preferred": "work",
        "definition": (
            "A concrete roadmap story or bounded task being prepared, "
            "performed, checked, repaired, or completed."
        ),
    },
    "review": {
        "preferred": "review",
        "definition": (
            "The independent checks and judgments required before work can "
            "pass its declared quality rules."
        ),
    },
    "decision": {
        "preferred": "decision",
        "definition": (
            "A closed, current choice that a named person, role, or governed "
            "review body must make before delivery can continue."
        ),
    },
    "blocker": {
        "preferred": "blocker",
        "definition": (
            "The concrete reason delivery cannot safely take its next step, "
            "plus who or what can resolve it."
        ),
    },
    "permission": {
        "preferred": "permission",
        "definition": (
            "The exact actions this delivery may still take, over which "
            "scope, within which limits and lifetime."
        ),
    },
    "progress": {
        "preferred": "progress",
        "definition": (
            "A source-backed account of completed, active, waiting, blocked, "
            "review, repair, and remaining work."
        ),
    },
    "cost": {
        "preferred": "cost",
        "definition": (
            "The declared limit, measured use, and remaining amount for time, "
            "model tokens, bytes, money, retries, or other finite delivery "
            "resources."
        ),
    },
    "next_step": {
        "preferred": "next step",
        "definition": (
            "The one source-backed action or named wait condition that "
            "follows from the current delivery state."
        ),
    },
}

SHARED_COPY = {
    "brand": "Delivery Workbench",
    "current_work": "Current work",
    "delivery_options": "Delivery options",
    "delivery_ready": "Delivery is ready",
    "delivery_attention": "Delivery needs attention",
    "technical_details": TECHNICAL_DETAILS_LABEL,
    "check_readiness": "Check readiness",
    "open_current_work": "Open current work",
    "review_delivery_options": "Review delivery options",
    "activity": "Activity",
    "progress": "Progress",
    "bounded_delivery": "Bounded delivery",
    "live_delivery": "Live delivery",
    "delivery_setup": "Delivery setup",
    "readiness": "Readiness",
    "roadmap_changes": "Roadmap changes",
    "refresh": "Check for updates",
    "unknown": "Unknown",
}

CLI_HELP = {
    "cli": (
        "Plan, do, review, and prove repository delivery. See current work, "
        "team, blockers, decisions, permission, progress, cost, and next "
        "step; --json keeps exact machine contracts."
    ),
    "status": (
        "show delivery readiness, current work, blockers, progress, and the "
        "next step"
    ),
    "knowledge": (
        "read or refresh advisory repository symbols, structure, tests, and "
        "named coverage gaps; starts and authorizes no work"
    ),
    "setup": (
        "compare delivery modes, or preview/apply one reviewed setup proposal "
        "under an exact atomic lease; setup never starts work"
    ),
    "step": (
        "review or apply only the current next step; exact confirmation "
        "details remain copyable"
    ),
    "notifications": (
        "show decisions, blockers, completed work, and the next step sent to "
        "the operator"
    ),
    "signals": (
        "check source-control facts that may change delivery progress; starts "
        "no work"
    ),
    "orchestration": (
        "design and check the technical work order for one bounded delivery; "
        "starts no work"
    ),
    "organization": (
        "design the team, responsibilities, independent review, and decision "
        "rules; starts no work"
    ),
    "rubric": (
        "define the checks and judgments required for work to pass review; "
        "starts no work"
    ),
    "workflow": (
        "design reusable work, review, decision, repair, and stop steps; "
        "starts no work"
    ),
    "program": (
        "set up, review, operate, and inspect an optional multi-phase "
        "delivery"
    ),
    "program_plan": (
        "review selected work, team, permission, cost limits, and stops before "
        "a separate start"
    ),
    "program_start": (
        "confirm the exact reviewed permission for this optional delivery; "
        "starts no work yet"
    ),
    "program_show": (
        "show live delivery progress, team and review, blockers, decisions, "
        "permission, cost, and next step"
    ),
    "program_preview": (
        "review one bounded delivery action and its consequence before "
        "confirmation"
    ),
    "program_tick": (
        "take the one already selected delivery step after exact confirmation"
    ),
    "program_supervise": (
        "repeat selected delivery steps only within the stated finite limits"
    ),
    "program_request": (
        "record one current decision from the listed response choices"
    ),
    "program_tail": "open the exact saved event history for technical inspection",
    "run": (
        "review, start, operate, and inspect one bounded delivery; a saved "
        "plan alone starts nothing"
    ),
    "run_plan": (
        "review the work, delivery plan, permission, cost limits, and expiry "
        "before a separate start"
    ),
    "run_start": (
        "confirm the exact reviewed permission for one bounded delivery"
    ),
    "run_list": "list local bounded deliveries and their current progress",
    "run_show": "show the saved state of one bounded delivery",
    "run_view": (
        "show live progress, team and review, blockers, decisions, permission, "
        "cost, and next step"
    ),
    "run_preview": (
        "review one bounded action and its consequence before confirmation"
    ),
    "run_tick": "take the one already selected delivery step after confirmation",
    "run_supervise": (
        "repeat selected delivery steps only within the stated finite limits"
    ),
    "run_checkpoint": "record one current approve-or-reject decision",
    "run_request": "record one response from the current listed choices",
    "run_tail": "open the exact saved event history for technical inspection",
    "board": "show work progress by phase and status",
    "holds": "show blocked or paused work and the recorded reason",
    "next": "show the current work or next safe work item",
    "doctor": "check whether this repository is ready for delivery work",
    "state": "open the exact roadmap state for technical inspection",
    "events": "open the exact rail event history for technical inspection",
    "sessions": "show which live agent is working on which work item",
    "check": "check roadmap structure, links, status, and proof",
    "gate": "check whether the staged delivery is ready to commit",
    "verify": "re-check delivered commit history against the delivery rules",
}

_ACTION_LABELS = {
    "repair-rails": "Repair delivery setup",
    "repair-roadmap": "Repair the roadmap",
    "resolve-rewrite": "Finish the current Git operation",
    "select-project": "Choose the delivery scope",
    "review-unstaged": "Review all current changes together",
    "generate-contract": "Prepare staged work for final review",
    "certify-contract": "Complete final delivery review",
    "repair-gate": "Resolve the final-review blocker",
    "commit": "Commit the reviewed delivery",
    "continue-story": "Continue current work",
    "review-workspace": "Match current changes to work",
    "start-story": "Start current work",
    "finish-story": "Finish the proven work",
    "review-holds": "Review blocked or paused work",
    "plan-work": "Plan the next work",
}

_ACTION_OUTCOMES = {
    "repair-rails": "Required repository setup needs attention before work can continue.",
    "repair-roadmap": "The roadmap needs a named correction before work can continue safely.",
    "resolve-rewrite": "Complete or stop the current Git operation before changing delivery state.",
    "select-project": "Choose which roadmap project this delivery covers.",
    "review-unstaged": "Review staged and unstaged changes as one delivery decision.",
    "generate-contract": "Record the staged delivery facts needed for final review.",
    "certify-contract": "Verify every final-review rule before committing.",
    "repair-gate": "Resolve the named final-review problem before committing.",
    "commit": "The reviewed staged work is ready for an explicit commit.",
    "continue-story": "The selected work is already active and can continue.",
    "review-workspace": "Current changes need an active work item before new work starts.",
    "start-story": "Move the next roadmap work item into active work.",
    "finish-story": "Recorded proof is present; complete the guarded work transition.",
    "review-holds": "No work is actionable; review the recorded blockers or pauses.",
    "plan-work": "No work is actionable or paused; define the next delivery work.",
}

_NOTIFICATION_COPY = {
    "checkpoint-pending": (
        "Decision needed",
        "Current work is waiting for a named decision.",
        "Choose one listed response or leave the work waiting.",
    ),
    "request-pending": (
        "Decision needed",
        "Current work is waiting for a named decision.",
        "Choose one listed response or leave the work waiting.",
    ),
    "request-republished": (
        "Decision still needed",
        "The same open decision was sent again after delivery resumed.",
        "Review the current choices before responding.",
    ),
    "request-expired": (
        "Decision expired",
        "The old response window closed and no new choice was recorded.",
        "Open current delivery state before deciding what to do next.",
    ),
    "awaiting-certification": (
        "Work ready for final review",
        "The bounded work finished and is waiting for final review and commit.",
        "Inspect the completed work and perform the separate final review.",
    ),
    "run-blocked": (
        "Delivery blocked",
        "The bounded delivery stopped at a recorded blocker.",
        "Open the affected work and follow its safe recovery step.",
    ),
    "nudge-budget-exhausted": (
        "Follow-up limit reached",
        "No additional automatic follow-up is permitted for this delivery.",
        "Review progress and choose a separate next step.",
    ),
    "branch-signal": (
        "Branch needs attention",
        "A source-control change may affect delivery progress.",
        "Open current delivery status before acting.",
    ),
    "program-intervention-required": (
        "Decision needed",
        "The optional delivery is waiting for a named person to decide.",
        "Review the current choices and affected work.",
    ),
    "program-disagreement": (
        "Review disagreement",
        "A review disagreement remains unresolved.",
        "Open the review and decide whether to repair, accept, or stop.",
    ),
    "program-decider-loss": (
        "Decision owner unavailable",
        "The required decision owner is unavailable and was not replaced.",
        "Restore the named responsibility or stop the delivery.",
    ),
    "program-provider-loss": (
        "Delivery worker unavailable",
        "A worker became unavailable and no replacement was assumed.",
        "Inspect the affected work before choosing recovery.",
    ),
    "program-architect-veto": (
        "Architecture review stopped delivery",
        "Architecture review refused the current progression.",
        "Review the stated concern and choose repair or stop.",
    ),
    "program-obligation-new": (
        "Follow-up recorded",
        "A decision created a durable follow-up.",
        "Assign and complete the follow-up under its stated acceptance rule.",
    ),
    "program-obligation-blocking": (
        "Delivery blocked by follow-up",
        "A required follow-up prevents more delivery progress.",
        "Complete or deliberately dispose of the named follow-up.",
    ),
    "program-obligation-overdue": (
        "Follow-up overdue",
        "A recorded follow-up passed its due time.",
        "Review its owner, consequence, and next step.",
    ),
    "program-budget-exhausted": (
        "Cost limit reached",
        "A finite delivery limit has no remaining amount.",
        "Stop or review a separately authorized change to the delivery plan.",
    ),
    "program-integration-refused": (
        "Completion could not be recorded",
        "A final delivery action was refused and saved work remains unchanged.",
        "Open the refusal and follow its safe recovery step.",
    ),
    "program-complete": (
        "Delivery complete",
        "All work in the reviewed delivery scope is complete.",
        "Review the delivered outcomes and any remaining follow-ups.",
    ),
}
# END EVERYDAY PRESENTATION COPY


def concept_name(concept_id: str) -> str:
    """Return one reviewed everyday name; unknown ids fail closed."""
    try:
        return str(PRODUCT_CONCEPTS[concept_id]["preferred"])
    except KeyError as exc:
        raise ValueError(f"unknown product concept: {concept_id}") from exc


def help_text(help_id: str) -> str:
    """Return shared human CLI help instead of adapter-local wording."""
    try:
        return CLI_HELP[help_id]
    except KeyError as exc:
        raise ValueError(f"unknown human help text: {help_id}") from exc


def _setup_provenance(value: dict[str, object]) -> dict[str, object]:
    labels = {
        "user-answer": "You supplied this during the setup conversation.",
        "repository-fact": "This comes from the repository as it exists now.",
        "recommendation": "This is a recommendation to review, not a settled fact.",
    }
    kind = str(value.get("kind", ""))
    note = str(value.get("source_note", ""))
    return {
        "sentence": "%s %s" % (labels.get(kind, "Its source is unknown."), note),
        "technical": {"kind": kind, "source_note": note},
    }


def setup_review_presentation(
    proposal: dict[str, object],
    plan_facts: dict[str, object],
    *,
    proposal_file: str,
    pending_preview: dict[str, object] | None = None,
) -> dict[str, object]:
    """Project an inert setup proposal into an everyday review model."""
    project = proposal["project"]
    intent = proposal["source_intent"]
    roadmap = proposal["tracked_content"]["roadmap"]
    policy = proposal["tracked_content"]["policy"]
    bindings = proposal["local_content"]["driver_bindings"]
    phases = []
    objection_items = []
    for phase in roadmap["phases"]:
        phase_id = "phase-%s" % phase["number"]
        stories = []
        objection_items.append({"id": phase_id, "label": "Phase %s: %s" % (
            phase["number"], phase["title"],
        )})
        for story in phase["stories"]:
            story_id = "story-%s" % story["id_sketch"]
            objection_items.append({"id": story_id, "label": "Story %s: %s" % (
                story["id_sketch"], story["title"],
            )})
            stories.append({
                "item_id": story_id,
                "id_sketch": story["id_sketch"],
                "title": story["title"],
                "purpose": story["problem"],
                "dependencies": [{
                    "id_sketch": item["id_sketch"],
                    "sentence": "This story follows %s." % item["id_sketch"],
                    "provenance": _setup_provenance(item["provenance"]),
                } for item in story["dependencies"]],
                "acceptance_criteria": [{
                    "text": item["text"],
                    "provenance": _setup_provenance(item["provenance"]),
                } for item in story["acceptance_criteria"]],
                "provenance": _setup_provenance(story["provenance"]),
            })
        phases.append({
            "item_id": phase_id,
            "number": phase["number"],
            "title": phase["title"],
            "accomplishes": phase["goal"],
            "stories": stories,
            "provenance": _setup_provenance(phase["provenance"]),
        })
    unresolved = []
    for index, question in enumerate(proposal["unresolved_questions"]):
        item_id = "question-%s" % (index + 1)
        objection_items.append({"id": item_id, "label": "Unresolved: %s" % question["question"]})
        unresolved.append({
            "item_id": item_id,
            "question": question["question"],
            "provenance": _setup_provenance(question["provenance"]),
        })
    changes = list(plan_facts["changes"])
    tracked_changes = [item for item in changes if item["scope"] == "tracked"]
    local_changes = [item for item in changes if item["scope"] == "git-local"]
    policy_documents = []
    if policy is not None:
        wrappers = [
            ("delivery plan", policy["program"]),
            ("team", policy["organization"]),
        ]
        wrappers.extend(("work flow", item) for item in policy["workflows"])
        wrappers.extend(("review criteria", item) for item in policy["rubrics"])
        for family, wrapper in wrappers:
            document = wrapper["document"]
            name = document.get("title") or document.get("slug") or "unnamed"
            policy_documents.append({
                "family": family,
                "name": str(name),
                "sentence": "%s: %s" % (family.capitalize(), name),
                "provenance": _setup_provenance(wrapper["provenance"]),
            })
    driver_rows = [{
        "profile": name,
        "sentence": "%s uses the %s adapter with %s from %s." % (
            name, item["adapter"], item["model"], item["provider"],
        ),
        "provenance": _setup_provenance(item["provenance"]),
    } for name, item in sorted(bindings.items())]
    command_file = proposal_file or "<proposal-file>"
    return {
        "kind": "delivery-workbench-setup-review",
        "schema_version": 1,
        "valid": True,
        "review_only": True,
        "marks_persist": "Review marks live only in this browser page and are lost when it closes or reloads.",
        "project": {
            "title": project["title"],
            "identity": "%s uses the %s story prefix." % (project["title"], project["prefix"]),
            "vision": intent["idea"],
            "vision_provenance": _setup_provenance(intent["provenance"]),
            "context": (
                "This adds to a project that already exists."
                if intent["mode"] == "maintain"
                else "This starts a new project roadmap."
            ),
            "provenance": _setup_provenance(project["provenance"]),
        },
        "phases": phases,
        "exit_criteria": [{
            "text": item["text"],
            "provenance": _setup_provenance(item["provenance"]),
        } for item in roadmap["exit_criteria"]],
        "unresolved_questions": {
            "summary": (
                "%s assumption%s still need an answer."
                % (len(unresolved), "" if len(unresolved) == 1 else "s")
                if unresolved else "No unresolved assumptions were recorded."
            ),
            "items": unresolved,
        },
        "configuration": {
            "label": "configuration, not permission",
            "explanation": (
                "These delivery policies and local driver bindings describe how later work could run. "
                "Saving them would not permit or start that work."
            ),
            "policy": {
                "present": policy is not None,
                "sentence": (
                    "The tracked delivery policy includes the complete linked bundle below."
                    if policy is not None else "No optional delivery policy will be saved."
                ),
                "documents": policy_documents,
                "provenance": _setup_provenance(policy["provenance"]) if policy is not None else None,
            },
            "driver_bindings": {
                "sentence": (
                    "%s non-secret local driver binding%s will be saved under .git."
                    % (len(driver_rows), "" if len(driver_rows) == 1 else "s")
                    if driver_rows else "No local driver bindings will be saved."
                ),
                "items": driver_rows,
            },
        },
        "changes": {
            "summary": "%s path%s are in this setup plan." % (
                len(changes), "" if len(changes) == 1 else "s",
            ),
            "paths": [item["path"] for item in changes],
            "tracked": tracked_changes,
            "git_local": local_changes,
        },
        "objection_items": objection_items,
        "terminal_handoff": {
            "sentence": "Review does not save anything. The next act belongs in the terminal.",
            "command": "dw setup preview %s" % shlex.quote(command_file),
        },
        "technical_details": {
            "label": TECHNICAL_DETAILS_LABEL,
            "proposal_file": proposal_file or None,
            "proposal_hash": plan_facts["proposal_hash"],
            "proposal": proposal,
            "changes": changes,
            "pending_preview": pending_preview,
        },
        "starts_work": False,
        "creates_grant": False,
        "certifies": False,
        "commits": False,
    }


def invalid_setup_review_presentation(
    refusal: str, *, proposal_file: str
) -> dict[str, object]:
    """Keep a setup-contract refusal verbatim inside the review workspace."""
    command_file = proposal_file or "<proposal-file>"
    return {
        "kind": "delivery-workbench-setup-review",
        "schema_version": 1,
        "valid": False,
        "review_only": True,
        "refusal": refusal,
        "unresolved_questions": {
            "summary": "The proposal could not be reviewed, so its unresolved assumptions are unknown.",
            "items": [],
        },
        "terminal_handoff": {
            "sentence": "Correct the proposal before asking the terminal for a preview.",
            "command": "dw setup preview %s" % shlex.quote(command_file),
        },
        "technical_details": {
            "label": TECHNICAL_DETAILS_LABEL,
            "proposal_file": proposal_file or None,
        },
        "starts_work": False,
        "creates_grant": False,
        "certifies": False,
        "commits": False,
    }


def build_presentation_catalog() -> dict[str, object]:
    """The copy/catalog document consumed by human adapters."""
    return {
        "kind": PRESENTATION_KIND,
        "schema_version": PRESENTATION_SCHEMA_VERSION,
        "surface": "catalog",
        "concepts": {
            key: dict(value) for key, value in PRODUCT_CONCEPTS.items()
        },
        "copy": dict(SHARED_COPY),
        "technical_details_label": TECHNICAL_DETAILS_LABEL,
        "starts_work": False,
        "writes_state": False,
        "selects_next_work": False,
        "grants_permission": False,
    }


def _section(
    section_id: str,
    concepts: list[str],
    label: str,
    value: str,
    status: str,
    source: dict[str, object],
) -> dict[str, object]:
    return {
        "id": section_id,
        "concepts": concepts,
        "label": label,
        "value": value,
        "status": status,
        "source": source,
    }


def _document(
    *,
    surface: str,
    source: dict[str, object],
    title: str,
    summary: str,
    sections: list[dict[str, object]],
    next_step: dict[str, object],
    technical_items: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "kind": PRESENTATION_KIND,
        "schema_version": PRESENTATION_SCHEMA_VERSION,
        "surface": surface,
        "source": source,
        "title": title,
        "summary": summary,
        "sections": sections,
        "next_step": next_step,
        "technical_details": {
            "label": TECHNICAL_DETAILS_LABEL,
            "items": technical_items,
        },
        "starts_work": False,
        "writes_state": False,
        "selects_next_work": False,
        "grants_permission": False,
    }


def _selected_status_project(
    status: dict[str, object],
) -> dict[str, object] | None:
    roadmap = status.get("roadmap")
    if not isinstance(roadmap, dict):
        return None
    selected = roadmap.get("selected_project")
    projects = roadmap.get("projects")
    if not selected or not isinstance(projects, list):
        return None
    return next(
        (
            item for item in projects
            if isinstance(item, dict) and item.get("slug") == selected
        ),
        None,
    )


def build_status_presentation(
    status: dict[str, object],
) -> dict[str, object]:
    """Present the exact status model as current work and one next step."""
    selected = _selected_status_project(status)
    work = selected.get("next_story") if isinstance(selected, dict) else None
    phase = selected.get("current_phase") if isinstance(selected, dict) else None
    action = status.get("next_action")
    action_doc = action if isinstance(action, dict) else {}
    action_id = str(action_doc.get("id") or "plan-work")
    ready = status.get("verdict") == "ready"
    sections: list[dict[str, object]] = []

    if isinstance(work, dict):
        story_id = str(work.get("story_id") or "Current work")
        story_title = str(work.get("title") or story_id)
        story_status = str(work.get("status") or "unknown")
        sections.append(_section(
            "work",
            ["work"],
            "Current work",
            f"{story_id}: {story_title}",
            story_status,
            {
                "model": "delivery-workbench-status",
                "path": "/roadmap/projects/*/next_story",
            },
        ))
    else:
        sections.append(_section(
            "work",
            ["work"],
            "Current work",
            "No roadmap work is currently actionable.",
            "none",
            {
                "model": "delivery-workbench-status",
                "path": "/roadmap/projects/*/next_story",
            },
        ))

    if isinstance(phase, dict):
        counts = (
            selected.get("status_counts")
            if isinstance(selected, dict)
            else None
        )
        count_doc = counts if isinstance(counts, dict) else {}
        done = int(
            phase.get("stories_done")
            or count_doc.get("done")
            or 0
        )
        total = int(
            phase.get("stories_total")
            or sum(
                int(value)
                for value in count_doc.values()
                if isinstance(value, int)
            )
            or 0
        )
        number = phase.get("number")
        sections.append(_section(
            "progress",
            ["progress"],
            "Progress",
            (
                f"{done} of {total} work items complete in phase {number}."
                if total
                else f"Progress totals are unavailable for phase {number}."
            ),
            "known" if total else "unknown",
            {
                "model": "delivery-workbench-status",
                "path": "/roadmap/projects/*/current_phase",
            },
        ))

    if not ready or bool(action_doc.get("blocking")):
        sections.append(_section(
            "blocker",
            ["blocker"],
            "Blocker",
            _ACTION_OUTCOMES.get(
                action_id,
                "Delivery needs a named correction before it can continue.",
            ),
            "blocking",
            {
                "model": "delivery-workbench-status",
                "path": "/next_action",
            },
        ))

    repository = status.get("repository")
    repository_doc = repository if isinstance(repository, dict) else {}
    changes = repository_doc.get("changes")
    change_doc = changes if isinstance(changes, dict) else {}
    contract = repository_doc.get("contract")
    contract_doc = contract if isinstance(contract, dict) else {}
    gate = repository_doc.get("gate")
    gate_doc = gate if isinstance(gate, dict) else {}
    rails = status.get("rails")
    rails_doc = rails if isinstance(rails, dict) else {}
    command = action_doc.get("command")
    technical_items = [
        {"label": "Exact action", "value": action_id},
        {"label": "Exact reason", "value": action_doc.get("reason")},
        {"label": "Command", "value": command},
        {"label": "Branch", "value": repository_doc.get("branch")},
        {
            "label": "Workspace",
            "value": {
                name: (
                    bucket.get("count")
                    if isinstance(bucket, dict)
                    else None
                )
                for name, bucket in change_doc.items()
            },
        },
        {"label": "Commit contract", "value": contract_doc.get("state")},
        {"label": "Commit gate", "value": gate_doc.get("state")},
        {
            "label": "Repository checks",
            "value": {
                "healthy": rails_doc.get("healthy"),
                "count": len(rails_doc.get("checks") or []),
            },
        },
    ]
    return _document(
        surface="status",
        source={
            "kind": status.get("kind"),
            "schema_version": status.get("schema_version"),
        },
        title=(
            SHARED_COPY["delivery_ready"]
            if ready
            else SHARED_COPY["delivery_attention"]
        ),
        summary=_ACTION_OUTCOMES.get(
            action_id,
            "Review the current delivery facts before choosing a next step.",
        ),
        sections=sections,
        next_step={
            "label": _ACTION_LABELS.get(action_id, "Review the next step"),
            "summary": _ACTION_OUTCOMES.get(
                action_id,
                "Review the current delivery facts before acting.",
            ),
            "action_id": action_id,
            "command": command,
            "manual": action_doc.get("kind") == "manual" or not command,
            "source": {
                "model": "delivery-workbench-status",
                "path": "/next_action",
            },
        },
        technical_items=technical_items,
    )


_ANSWER_CONCEPTS = {
    "delivery": ["delivery_plan", "work"],
    "team": ["team", "review"],
    "passed": ["review", "progress"],
    "blocked": ["blocker"],
    "decision": ["decision"],
    "remaining-change-spend": ["permission", "cost"],
    "next": ["next_step"],
}


def build_live_presentation(
    view: dict[str, object],
) -> dict[str, object]:
    """Present an existing run/program live-progress application view."""
    progress = view.get("live_progress")
    if not isinstance(progress, dict):
        raise ValueError("live delivery view has no live_progress document")
    status = progress.get("status")
    status_doc = status if isinstance(status, dict) else {}
    sections = []
    for answer in progress.get("answers") or []:
        if not isinstance(answer, dict):
            continue
        answer_id = str(answer.get("id") or "")
        source = answer.get("source")
        sections.append(_section(
            answer_id,
            list(_ANSWER_CONCEPTS.get(answer_id, [])),
            str(answer.get("question") or answer_id),
            str(answer.get("answer") or "Unknown."),
            str(answer.get("status") or "unknown"),
            dict(source) if isinstance(source, dict) else {},
        ))
    next_step = progress.get("next_step")
    next_doc = next_step if isinstance(next_step, dict) else {}
    technical = progress.get("technical_details")
    technical_doc = technical if isinstance(technical, dict) else {}
    outstanding_requests = view.get("outstanding_requests")
    request_items = (
        list(outstanding_requests)
        if isinstance(outstanding_requests, list)
        else []
    )
    context = str(progress.get("context") or "delivery")
    technical_items = [
        {"label": "Exact view", "value": view.get("kind")},
        {
            "label": "Exact identity",
            "value": view.get("run_id"),
        },
        {"label": "Exact state", "value": view.get("state")},
    ]
    if request_items:
        technical_items.append(
            {"label": "Pending requests", "value": request_items}
        )
    technical_items.append(
        {
            "label": "Source facts",
            "value": technical_doc,
        }
    )
    return _document(
        surface=(
            "program-live-delivery"
            if context == "program"
            else "bounded-live-delivery"
        ),
        source={
            "kind": view.get("kind"),
            "schema_version": view.get("schema_version"),
        },
        title=f"Live delivery — {progress.get('title') or 'Current work'}",
        summary=(
            f"{status_doc.get('label') or 'Unknown'}: "
            f"{status_doc.get('meaning') or 'Current progress is unavailable.'}"
        ),
        sections=sections,
        next_step={
            "label": str(next_doc.get("label") or "Check current progress"),
            "summary": str(
                next_doc.get("detail")
                or "No additional safe step is currently selected."
            ),
            "action_id": next_doc.get("action"),
            "command": None,
            "manual": next_doc.get("action") is None,
            "source": (
                dict(next_doc["source"])
                if isinstance(next_doc.get("source"), dict)
                else {}
            ),
        },
        technical_items=technical_items,
    )


def _story_from_start_plan(
    plan: dict[str, object],
) -> tuple[str, str]:
    story = plan.get("story")
    if isinstance(story, dict):
        story_id = str(story.get("id") or story.get("story_id") or "")
        return story_id, str(story.get("title") or story_id)
    selection = plan.get("selection")
    if isinstance(selection, dict):
        selected_story = selection.get("story")
        if isinstance(selected_story, dict):
            story_id = str(
                selected_story.get("id")
                or selected_story.get("story_id")
                or ""
            )
            return story_id, str(selected_story.get("title") or story_id)
        story_id = str(selected_story or "")
        return story_id, story_id
    return "", ""


def build_start_presentation(
    plan: dict[str, object],
) -> dict[str, object]:
    """Present one exact bounded/program start plan before confirmation."""
    kind = str(plan.get("kind") or "")
    program = "program" in kind
    request = plan.get("request")
    request_doc = request if isinstance(request, dict) else {}
    authority = plan.get("authority")
    authority_doc = authority if isinstance(authority, dict) else {}
    score = plan.get("score")
    score_doc = score if isinstance(score, dict) else {}
    program_doc = plan.get("program")
    program_facts = program_doc if isinstance(program_doc, dict) else {}
    story_id, story_title = _story_from_start_plan(plan)
    capabilities = authority_doc.get("capabilities")
    if not isinstance(capabilities, list):
        capabilities = request_doc.get("capabilities")
    capability_names = [
        str(item).replace("_", " ").replace("-", " ")
        for item in capabilities or []
    ]
    budgets = authority_doc.get("budgets")
    if not isinstance(budgets, dict):
        budgets = request_doc.get("budgets")
    budget_doc = budgets if isinstance(budgets, dict) else {}
    applicable = bool(plan.get("applicable"))
    delivery_title = str(
        program_facts.get("title")
        or program_facts.get("slug")
        or request_doc.get("program")
        or score_doc.get("title")
        or score_doc.get("slug")
        or "Reviewed delivery plan"
    )
    sections = [
        _section(
            "delivery-plan",
            ["delivery_plan"],
            "Delivery plan",
            delivery_title,
            "known",
            {"model": kind, "path": "/score" if not program else "/program"},
        ),
        _section(
            "work",
            ["work"],
            "Work",
            (
                f"{story_id}: {story_title}"
                if story_id
                else "The selected work is unavailable."
            ),
            "known" if story_id else "unknown",
            {"model": kind, "path": "/story" if not program else "/selection"},
        ),
        _section(
            "permission",
            ["permission"],
            "Permission",
            (
                "May use: " + ", ".join(capability_names) + "."
                if capability_names
                else "No additional action type is available."
            ),
            "review-required",
            {"model": kind, "path": "/authority/capabilities"},
        ),
        _section(
            "cost",
            ["cost"],
            "Cost limits",
            (
                "; ".join(
                    "{}: {}".format(
                        str(name).replace("_", " ").replace("-", " "),
                        value,
                    )
                    for name, value in budget_doc.items()
                )
                or "No counted cost limit is available."
            ),
            "bounded" if budget_doc else "unknown",
            {"model": kind, "path": "/authority/budgets"},
        ),
    ]
    return _document(
        surface=(
            "program-start-review" if program else "bounded-start-review"
        ),
        source={"kind": kind, "schema_version": plan.get("schema_version")},
        title=(
            "Review optional delivery permission"
            if program
            else "Review bounded delivery permission"
        ),
        summary=(
            "This delivery is ready for a separate start confirmation."
            if applicable
            else "This delivery cannot start until the named blocker is resolved."
        ),
        sections=sections,
        next_step={
            "label": (
                "Confirm this reviewed delivery"
                if applicable
                else "Resolve the start blocker"
            ),
            "summary": (
                "Starting remains a separate explicit action."
                if applicable
                else "Review the listed issue; no work has started."
            ),
            "action_id": "start",
            "command": None,
            "manual": True,
            "source": {"model": kind, "path": "/applicable"},
        },
        technical_items=[
            {"label": "Exact plan kind", "value": kind},
            {
                "label": "Exact start confirmation",
                "value": plan.get("start_token"),
            },
            {"label": "Exact request", "value": request_doc},
            {"label": "Exact issues", "value": plan.get("issues")},
        ],
    )


def build_step_presentation(
    preview: dict[str, object],
) -> dict[str, object]:
    """Present one roadmap next-step preview without changing its lease."""
    action = preview.get("action")
    action_doc = action if isinstance(action, dict) else {}
    action_id = str(action_doc.get("id") or "plan-work")
    command = action_doc.get("command")
    command_list = command if isinstance(command, list) else []
    story_id = next(
        (
            str(item)
            for item in command_list
            if isinstance(item, str)
            and re.fullmatch(r"[A-Z][A-Z0-9]*-\d+-\d+", item)
        ),
        "",
    )
    project = str(preview.get("project") or "the selected project")
    affected = (
        f"{story_id} in {project}"
        if story_id
        else project
    )
    applicable = bool(preview.get("applicable"))
    sections = [
        _section(
            "work",
            ["work"],
            "Affected work",
            affected,
            "known" if preview.get("project") else "unknown",
            {"model": str(preview.get("kind")), "path": "/action/command"},
        ),
        _section(
            "permission",
            ["permission"],
            "Permission",
            (
                "This preview may apply only the listed current step."
                if applicable
                else "This preview cannot apply a delivery step."
            ),
            "available" if applicable else "unavailable",
            {"model": str(preview.get("kind")), "path": "/applicable"},
        ),
    ]
    if not applicable:
        sections.append(_section(
            "blocker",
            ["blocker"],
            "Blocker",
            str(
                preview.get("refusal")
                or "The current next step requires a separate decision."
            ),
            "blocking",
            {"model": str(preview.get("kind")), "path": "/refusal"},
        ))
    return _document(
        surface="roadmap-action-review",
        source={
            "kind": preview.get("kind"),
            "schema_version": preview.get("schema_version"),
        },
        title=(
            "Review next step — "
            + _ACTION_LABELS.get(action_id, "Review the next step")
        ),
        summary=_ACTION_OUTCOMES.get(
            action_id,
            "Review the current delivery facts before acting.",
        ),
        sections=sections,
        next_step={
            "label": (
                "Confirm this step"
                if applicable
                else "Resolve the blocker"
            ),
            "summary": (
                "Use the exact confirmation only after reviewing this one step."
                if applicable
                else "Reload current delivery status after the named correction."
            ),
            "action_id": action_id,
            "command": preview.get("apply_command"),
            "manual": not applicable,
            "source": {
                "model": str(preview.get("kind")),
                "path": "/apply_command",
            },
        },
        technical_items=[
            {"label": "Exact action", "value": action_id},
            {"label": "Source command", "value": command},
            {"label": "Exact confirmation", "value": preview.get("token")},
            {"label": "Apply command", "value": preview.get("apply_command")},
            {"label": "Exact refusal", "value": preview.get("refusal")},
        ],
    )


def build_step_result_presentation(
    result: dict[str, object],
) -> dict[str, object]:
    """Present the recorded outcome of one deliberate roadmap step."""
    action = result.get("action")
    action_doc = action if isinstance(action, dict) else {}
    action_id = str(action_doc.get("id") or "unknown")
    project = str(result.get("project") or "the selected project")
    outcome = str(result.get("outcome") or "unknown")
    reason = str(result.get("reason") or "")
    after = result.get("after")
    after_doc = after if isinstance(after, dict) else {}
    next_id = str(after_doc.get("action_id") or "plan-work")
    titles = {
        "succeeded": "Delivery step complete",
        "refused": "Delivery step refused",
        "interrupted": "Delivery step interrupted",
        "failed": "Delivery step failed",
    }
    summaries = {
        "succeeded": (
            "The reviewed step finished. Reloaded delivery facts now decide "
            "what follows."
        ),
        "refused": (
            "No child action started and no new delivery effect occurred."
        ),
        "interrupted": (
            "The child action was interrupted; reload saved delivery state "
            "before deciding whether an effect occurred."
        ),
        "failed": (
            "The child action returned a failure; inspect its output and "
            "reload saved delivery state before acting again."
        ),
    }
    sections = [
        _section(
            "work",
            ["work"],
            "Affected work",
            project,
            "known" if result.get("project") else "unknown",
            {"model": str(result.get("kind")), "path": "/project"},
        ),
        _section(
            "progress",
            ["progress"],
            "Outcome",
            outcome,
            (
                "complete"
                if outcome == "succeeded"
                else "blocking"
                if outcome in {"failed", "interrupted", "refused"}
                else "unknown"
            ),
            {"model": str(result.get("kind")), "path": "/outcome"},
        ),
    ]
    if outcome != "succeeded":
        sections.append(_section(
            "blocker",
            ["blocker"],
            "Blocker",
            reason or "The exact failure is available in Technical details.",
            "blocking",
            {"model": str(result.get("kind")), "path": "/reason"},
        ))
    output = result.get("output")
    output_doc = output if isinstance(output, dict) else {}
    return _document(
        surface="roadmap-action-result",
        source={
            "kind": result.get("kind"),
            "schema_version": result.get("schema_version"),
        },
        title=titles.get(outcome, "Delivery step outcome"),
        summary=summaries.get(
            outcome,
            "Reload current delivery status before choosing a next step.",
        ),
        sections=sections,
        next_step={
            "label": _ACTION_LABELS.get(next_id, "Check current delivery"),
            "summary": _ACTION_OUTCOMES.get(
                next_id,
                "Reload current delivery status before acting.",
            ),
            "action_id": next_id,
            "command": None,
            "manual": True,
            "source": {
                "model": str(result.get("kind")),
                "path": "/after/action_id",
            },
        },
        technical_items=[
            {"label": "Exact action", "value": action_id},
            {"label": "Exact outcome", "value": outcome},
            {"label": "Exit code", "value": result.get("exit_code")},
            {"label": "Exact reason", "value": result.get("reason")},
            {"label": "Before", "value": result.get("before")},
            {"label": "After", "value": result.get("after")},
            {"label": "Output bounds", "value": output_doc.get("truncated")},
        ],
    )


def build_action_presentation(
    preview: dict[str, object],
    bounded_actions: dict[str, object] | None = None,
) -> dict[str, object]:
    """Present one exact action preview with canonical consequences first."""
    action = str(preview.get("action") or "inspect")
    decision = str(preview.get("decision") or "")
    request_id = str(
        preview.get("request_id")
        or preview.get("correlation_id")
        or ""
    )
    model = bounded_actions if isinstance(bounded_actions, dict) else {}
    matches = []
    for item in model.get("actions") or []:
        if not isinstance(item, dict) or str(item.get("action") or "") != action:
            continue
        if decision and str(item.get("decision") or "") != decision:
            continue
        correlation = str(
            item.get("request_id")
            or item.get("correlation_id")
            or ""
        )
        if request_id and correlation and correlation != request_id:
            continue
        matches.append(item)
    selected = matches[0] if matches else {}
    consequences = selected.get("consequences")
    consequence_doc = consequences if isinstance(consequences, dict) else {}
    label = str(
        selected.get("label")
        or (
            f"{action.replace('_', ' ').replace('-', ' ').title()} "
            f"{decision}".strip()
        )
        or "Review action"
    )
    applicable = bool(preview.get("applicable"))
    affected_work_value = (
        selected.get("affected_work")
        or model.get("affected_work")
    )
    if not affected_work_value:
        selected_id = selected.get("id")
        for inbox_item in model.get("inbox") or []:
            if not isinstance(inbox_item, dict):
                continue
            choices = inbox_item.get("choices")
            if not isinstance(choices, list):
                continue
            if any(
                isinstance(choice, dict)
                and choice.get("action_id") == selected_id
                for choice in choices
            ):
                affected_work_value = inbox_item.get("affected_work")
                break
    if not affected_work_value:
        permission = model.get("permission")
        permission_doc = permission if isinstance(permission, dict) else {}
        scope = permission_doc.get("scope")
        scope_doc = scope if isinstance(scope, dict) else {}
        story_id = scope_doc.get("story_id") or scope_doc.get("story")
        story_title = scope_doc.get("story_title")
        affected_work_value = (
            f"{story_id}: {story_title}"
            if story_id and story_title
            else story_id
        )
    affected_work = str(affected_work_value or "Current delivery")
    effect = str(
        consequence_doc.get("effect")
        or selected.get("effect")
        or "The exact effect is available in Technical details."
    )
    after = str(
        consequence_doc.get("after")
        or selected.get("after")
        or "Reload current delivery state after the action."
    )
    return _document(
        surface="delivery-action-review",
        source={
            "kind": preview.get("kind"),
            "schema_version": preview.get("schema_version"),
        },
        title=f"Review action — {label}",
        summary=(
            f"{effect} {after}"
            if applicable
            else "This action is unavailable. No new delivery effect occurred."
        ),
        sections=[
            _section(
                "work",
                ["work"],
                "Affected work",
                affected_work,
                "known",
                {
                    "model": str(model.get("kind") or preview.get("kind")),
                    "path": "/actions",
                },
            ),
            _section(
                "permission",
                ["permission"],
                "Permission",
                (
                    "The current saved delivery permits this reviewed action."
                    if applicable
                    else "The current saved delivery does not permit this action."
                ),
                "available" if applicable else "unavailable",
                {
                    "model": str(model.get("kind") or preview.get("kind")),
                    "path": "/actions",
                },
            ),
        ],
        next_step={
            "label": "Confirm this action" if applicable else "Reload current delivery",
            "summary": (
                "Use the exact confirmation only after reviewing the consequence."
                if applicable
                else "Review the current state and listed blocker before trying again."
            ),
            "action_id": action,
            "command": None,
            "manual": True,
            "source": {
                "model": str(preview.get("kind") or ""),
                "path": "/applicable",
            },
        },
        technical_items=[
            {"label": "Exact action", "value": action},
            {"label": "Exact decision", "value": decision},
            {
                "label": "Exact confirmation",
                "value": preview.get("act_token"),
            },
            {"label": "Exact state", "value": preview.get("state")},
            {"label": "Exact issues", "value": preview.get("issues")},
        ],
    )


def build_notification_presentation(
    notification: dict[str, object],
) -> dict[str, object]:
    """Present one exact notification without creating response authority."""
    kind = str(notification.get("kind") or "")
    title, summary, next_summary = _NOTIFICATION_COPY.get(
        kind,
        (
            "Delivery update",
            "A saved delivery fact changed.",
            "Open current delivery status before acting.",
        ),
    )
    request = notification.get("request")
    request_doc = request if isinstance(request, dict) else {}
    guidance = request_doc.get("guidance")
    guidance_doc = guidance if isinstance(guidance, dict) else {}
    affected = str(
        guidance_doc.get("affected_work")
        or notification.get("node")
        or "Current delivery"
    )
    sections = [
        _section(
            "work",
            ["work"],
            "Affected work",
            affected,
            "known",
            {
                "model": "delivery-workbench-notifications",
                "path": "/notifications/*",
            },
        )
    ]
    choices = [
        item for item in guidance_doc.get("choices") or []
        if isinstance(item, dict)
    ]
    if request_doc:
        choice_text = "; ".join(
            "{} — {}".format(
                item.get("decision"),
                item.get("after") or item.get("effect"),
            )
            for item in choices
        ) or "Review the current listed choices."
        sections.append(_section(
            "decision",
            ["decision"],
            "Decision",
            choice_text,
            "needed",
            {
                "model": "delivery-workbench-notifications",
                "path": "/notifications/*/request/response_schema",
            },
        ))
    elif "blocked" in kind or "exhausted" in kind or "refused" in kind:
        sections.append(_section(
            "blocker",
            ["blocker"],
            "Blocker",
            summary,
            "blocking",
            {
                "model": "delivery-workbench-notifications",
                "path": "/notifications/*/kind",
            },
        ))

    correlation = request_doc.get("correlation_id")
    decisions = request_doc.get("response_schema")
    decision_doc = decisions if isinstance(decisions, dict) else {}
    options = decision_doc.get("decision")
    option_list = options if isinstance(options, list) else []
    response_command = (
        ["/decision", str(correlation), "|".join(str(item) for item in option_list)]
        if correlation and option_list
        else None
    )
    return _document(
        surface="operator-notification",
        source={
            "kind": "delivery-workbench-notifications",
            "schema_version": 1,
        },
        title=title,
        summary=summary,
        sections=sections,
        next_step={
            "label": "Next step",
            "summary": next_summary,
            "action_id": "respond" if request_doc else "inspect",
            "command": response_command,
            "manual": True,
            "source": {
                "model": "delivery-workbench-notifications",
                "path": "/notifications/*",
            },
        },
        technical_items=[
            {"label": "Exact notification kind", "value": kind},
            {"label": "Run", "value": notification.get("run_id")},
            {"label": "Exact location", "value": notification.get("node")},
            {"label": "Request identity", "value": correlation},
            {"label": "Response command", "value": response_command},
            {
                "label": "Permission boundary",
                "value": (
                    "The response carrier supplies no permission. Current "
                    "local identity, request, response choices, and freshness "
                    "checks still decide."
                ),
            },
            {"label": "Acknowledge", "value": notification.get("id")},
        ],
    )


def _render_value(value: Any) -> str:
    if value is None or value == "":
        return "not available"
    if (
        isinstance(value, list)
        and all(isinstance(item, str) for item in value)
    ):
        return shlex.join(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def render_presentation(
    presentation: dict[str, object],
    *,
    technical: bool = True,
) -> str:
    """Render the shared projection for a human terminal or notification."""
    lines = [
        str(presentation.get("title") or "Delivery update"),
        str(presentation.get("summary") or ""),
    ]
    for section in presentation.get("sections") or []:
        if not isinstance(section, dict):
            continue
        lines.append(
            "{}: {}".format(
                section.get("label") or section.get("id") or "Update",
                section.get("value") or "Unknown.",
            )
        )
    next_step = presentation.get("next_step")
    if isinstance(next_step, dict):
        lines.append(
            "{}: {}".format(
                next_step.get("label") or "Next step",
                next_step.get("summary") or "Review current delivery status.",
            )
        )
    if technical:
        details = presentation.get("technical_details")
        details_doc = details if isinstance(details, dict) else {}
        lines.append(
            "{}:".format(
                details_doc.get("label") or TECHNICAL_DETAILS_LABEL
            )
        )
        for item in details_doc.get("items") or []:
            if not isinstance(item, dict):
                continue
            lines.append(
                "  {}: {}".format(
                    item.get("label") or "Fact",
                    _render_value(item.get("value")),
                )
            )
    return "\n".join(line for line in lines if line != "") + "\n"
