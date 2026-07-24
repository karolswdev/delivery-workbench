"""Read-only application view for Delivery Workbench's delivery front door.

This module is presentation policy, not delivery policy.  It groups facts from
the existing status, orchestration-inventory, and Program Studio models into
the three choices a person can make on first arrival:

* continue ordinary roadmap work;
* review one bounded delivery; or
* set up an optional delivery program.

The projection deliberately owns no eligibility, authority, compiler, start,
or persistence semantics.  Workbench and the human CLI render this same model;
the existing machine-facing source models remain unchanged.
"""

from __future__ import annotations

from pathlib import Path

from .orchestration import score_inventory
from .program_studio import build_program_studio
from .status import build_status

DELIVERY_SETUP_KIND = "delivery-workbench-delivery-setup"
DELIVERY_SETUP_SCHEMA_VERSION = 1
TECHNICAL_DETAILS_LABEL = "Technical details"


def _selected_project(status: dict[str, object]) -> dict[str, object] | None:
    roadmap = status["roadmap"]
    slug = roadmap["selected_project"]  # type: ignore[index]
    if not slug:
        return None
    return next(
        (
            item
            for item in roadmap["projects"]  # type: ignore[index]
            if item["slug"] == slug
        ),
        None,
    )


def _work_route(project: str | None, work: dict[str, object] | None) -> str:
    if not project or work is None:
        return "#/"
    return "#/p/{}/s/{}".format(project, work["story_id"])


def _choice(
    *,
    choice_id: str,
    tier: str,
    label: str,
    summary: str,
    readiness: str,
    available: bool,
    recommended: bool,
    route: str,
    creates_during_setup: list[str],
    may_change_after_confirmation: list[str],
    remains_disabled: list[str],
    separate_permission: str | None,
    correction: str | None,
) -> dict[str, object]:
    return {
        "id": choice_id,
        "tier": tier,
        "label": label,
        "summary": summary,
        "readiness": readiness,
        "available": available,
        "recommended": recommended,
        "route": route,
        "creates_during_setup": creates_during_setup,
        "may_change_after_confirmation": may_change_after_confirmation,
        "remains_disabled": remains_disabled,
        "separate_permission": separate_permission,
        "correction": correction,
    }


def build_delivery_setup(
    root: Path,
    project: str | None = None,
) -> dict[str, object]:
    """Build the pure, source-traceable first-arrival/setup application view."""
    root = root.resolve()
    status = build_status(root, project)
    studio = build_program_studio(root)
    orchestration = score_inventory(root)

    roadmap = status["roadmap"]
    selected = _selected_project(status)
    selected_slug = (
        str(roadmap["selected_project"])  # type: ignore[index]
        if roadmap["selected_project"]  # type: ignore[index]
        else None
    )
    work = (
        selected.get("next_story")
        if isinstance(selected, dict)
        and isinstance(selected.get("next_story"), dict)
        else None
    )
    current_phase = (
        selected.get("current_phase")
        if isinstance(selected, dict)
        and isinstance(selected.get("current_phase"), dict)
        else None
    )
    ordinary_ready = bool(
        status["verdict"] == "ready"
        and roadmap["healthy"]  # type: ignore[index]
        and selected_slug
    )

    valid_scores = [
        item
        for item in orchestration["scores"]  # type: ignore[index]
        if item.get("valid")
    ]
    bounded_route = (
        "#/orchestration/{}".format(valid_scores[0]["name"])
        if valid_scores
        else "#/orchestration"
    )
    if not selected_slug:
        bounded_readiness = "needs-delivery-scope"
        bounded_correction = "Choose which roadmap project this delivery covers."
    elif not valid_scores:
        bounded_readiness = "needs-delivery-plan"
        bounded_correction = (
            "Create or choose a valid delivery plan, then return to readiness review."
        )
    elif work is None:
        bounded_readiness = "needs-current-work"
        bounded_correction = (
            "Choose current roadmap work before reviewing a bounded delivery."
        )
    else:
        bounded_readiness = "ready-to-review"
        bounded_correction = None

    program_family = next(
        item
        for item in studio["families"]  # type: ignore[index]
        if item["id"] == "program"
    )
    configured_programs = [
        item for item in program_family["items"] if item.get("valid")
    ]
    invalid_programs = [
        item for item in program_family["items"] if not item.get("valid")
    ]
    if selected_slug:
        if configured_programs:
            program_readiness = "configured-for-review"
            program_correction = None
        elif invalid_programs:
            program_readiness = "needs-program-repair"
            program_correction = (
                "Repair or replace the invalid delivery-program draft, or "
                "start a new draft for this scope."
            )
        else:
            program_readiness = "ready-to-set-up"
            program_correction = None
    else:
        program_readiness = "needs-delivery-scope"
        program_correction = "Choose which roadmap project this program covers."

    work_route = _work_route(selected_slug, work)
    choices = [
        _choice(
            choice_id="roadmap",
            tier="vanilla",
            label="Continue with the roadmap",
            summary=(
                "Use ordinary roadmap work now. Optional coordination is not "
                "required."
            ),
            readiness="ready" if ordinary_ready else "needs-attention",
            available=ordinary_ready,
            recommended=True,
            route=work_route,
            creates_during_setup=[],
            may_change_after_confirmation=[],
            remains_disabled=[
                "bounded delivery",
                "optional delivery program",
                "background work",
            ],
            separate_permission=None,
            correction=(
                None
                if ordinary_ready
                else "Resolve the repository or roadmap issue named by status."
            ),
        ),
        _choice(
            choice_id="bounded",
            tier="bounded-run",
            label="Review one bounded delivery",
            summary=(
                "Review one delivery plan for the selected work, its checks, "
                "limits, and stop conditions."
            ),
            readiness=bounded_readiness,
            available=bool(valid_scores and selected_slug),
            recommended=False,
            route=bounded_route,
            creates_during_setup=[],
            may_change_after_confirmation=[
                "only the reviewed work within the reviewed limits",
            ],
            remains_disabled=[
                "optional delivery program",
                "automatic continuation",
                "unreviewed work",
            ],
            separate_permission=(
                "A fresh, explicit start confirmation is still required before "
                "a run or process exists."
            ),
            correction=bounded_correction,
        ),
        _choice(
            choice_id="program",
            tier="program",
            label="Set up an optional delivery program",
            summary=(
                "Draft a reusable delivery scope, team, review, limits, and "
                "stop conditions."
            ),
            readiness=program_readiness,
            available=bool(selected_slug),
            recommended=False,
            route="#/program-studio/program",
            creates_during_setup=[
                "one tracked delivery-plan draft only if Save draft is confirmed",
            ],
            may_change_after_confirmation=[
                "the reviewed roadmap and repository scope only after a later start",
            ],
            remains_disabled=[
                "runtime permission",
                "work and processes",
                "network activity",
                "automatic continuation",
            ],
            separate_permission=(
                "Saving a draft starts nothing. A separate reviewed program "
                "start is still required before any work begins."
            ),
            correction=program_correction,
        ),
    ]

    projects = [
        {
            "slug": item["slug"],
            "prefix": item["prefix"],
            "current_phase": item["current_phase"],
            "next_work": item["next_story"],
        }
        for item in roadmap["projects"]  # type: ignore[index]
    ]
    issues = []
    if roadmap["selection_required"]:  # type: ignore[index]
        issues.append(
            {
                "decision": "delivery scope",
                "summary": "Choose one roadmap project before optional setup.",
                "next_step": "Select the project whose work will be delivered.",
            }
        )
    elif not roadmap["healthy"]:  # type: ignore[index]
        issues.append(
            {
                "decision": "repository readiness",
                "summary": str(roadmap["issues"][0]),  # type: ignore[index]
                "next_step": "Resolve the named roadmap issue, then check readiness again.",
            }
        )

    return {
        "kind": DELIVERY_SETUP_KIND,
        "schema_version": DELIVERY_SETUP_SCHEMA_VERSION,
        "healthy": ordinary_ready,
        "optional_configuration_healthy": bool(studio["healthy"]),
        "readiness": "ready" if ordinary_ready else "attention",
        "title": (
            "Your roadmap is ready"
            if ordinary_ready
            else "Choose or repair the delivery scope"
        ),
        "summary": (
            "Continue ordinary work now, or deliberately review optional "
            "coordination. Nothing optional is required."
        ),
        "delivery_scope": {
            "selected_project": selected_slug,
            "selection_required": bool(roadmap["selection_required"]),  # type: ignore[index]
            "projects": projects,
            "current_phase": current_phase,
            "current_work": work,
        },
        "choices": choices,
        "issues": issues,
        "technical_details": {
            "label": TECHNICAL_DETAILS_LABEL,
            "sources": [
                {
                    "kind": status["kind"],
                    "schema_version": status["schema_version"],
                    "route": "/api/status",
                },
                {
                    "kind": orchestration["kind"],
                    "schema_version": orchestration["schema_version"],
                    "route": "/api/orchestration",
                },
                {
                    "kind": studio["kind"],
                    "schema_version": studio["schema_version"],
                    "route": "/api/program-studio",
                },
            ],
            "commands": {
                "status": [".githooks/dw", "status"],
                "bounded_plans": [".githooks/dw", "orchestration", "list"],
                "programs": [".githooks/dw", "program", "list"],
            },
        },
        "cancel": {
            "label": "Leave for now",
            "route": "#/",
            "effect": "Leaves repository and delivery state unchanged.",
        },
        "starts_work": False,
        "writes_policy": False,
        "writes_roadmap": False,
        "writes_run_state": False,
        "creates_grant": False,
        "starts_process": False,
        "starts_observer": False,
        "sends_notification": False,
        "uses_network": False,
    }


def render_delivery_setup(
    setup: dict[str, object],
    *,
    technical: bool = False,
) -> str:
    """Render the shared model for a human terminal without changing it."""
    scope = setup["delivery_scope"]
    work = scope["current_work"]  # type: ignore[index]
    lines = [
        "delivery={} — {}".format(setup["readiness"], setup["title"]),
        str(setup["summary"]),
    ]
    if scope["selected_project"]:  # type: ignore[index]
        lines.append("scope={}".format(scope["selected_project"]))  # type: ignore[index]
    else:
        lines.append("scope=choose-one-project")
    if isinstance(work, dict):
        lines.append(
            "work={} [{}] — {}".format(
                work["story_id"], work["status"], work["title"]
            )
        )
    else:
        lines.append("work=none-currently-actionable")
    lines.append("choices (inspection and cancel start nothing):")
    for index, choice in enumerate(setup["choices"], 1):  # type: ignore[index]
        suffix = " · recommended ordinary default" if choice["recommended"] else ""
        lines.append(
            "  {}. {} — {}{}".format(
                index, choice["label"], choice["readiness"], suffix
            )
        )
        lines.append("     {}".format(choice["summary"]))
        if choice["correction"]:
            lines.append("     next step: {}".format(choice["correction"]))
        if choice["separate_permission"]:
            lines.append("     permission: {}".format(choice["separate_permission"]))
    lines.append(
        "Workbench: open #/program-studio to choose; Leave for now changes nothing."
    )
    if technical:
        details = setup["technical_details"]
        lines.append("{}:".format(details["label"]))  # type: ignore[index]
        for source in details["sources"]:  # type: ignore[index]
            lines.append(
                "  source={}@{} {}".format(
                    source["kind"], source["schema_version"], source["route"]
                )
            )
        for name, command in details["commands"].items():  # type: ignore[index]
            lines.append("  {}={}".format(name, " ".join(command)))
    return "\n".join(lines) + "\n"


def render_delivery_setup_pointer(setup: dict[str, object]) -> str:
    """One compact status/help pointer to the same readiness outcome."""
    scope = setup["delivery_scope"]
    project = scope["selected_project"] or "choose-project"  # type: ignore[index]
    return (
        "delivery={} scope={} choices=roadmap|bounded|program "
        "open=\".githooks/dw setup{}\"\n"
    ).format(
        setup["readiness"],
        project,
        " {}".format(project) if project != "choose-project" else "",
    )
