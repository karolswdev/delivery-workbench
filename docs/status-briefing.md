# Status briefing contract

**Status:** v1 contract frozen; core, CLI, MCP, and HTTP implemented in Phase
22; workbench/agent rendering rollout in progress.
**Scope:** local, read-only readiness and guided next action.

## Purpose

`dw status` is the one opening question for a Delivery Workbench repo:

> Are the local rails safe to use, what state is this workspace and its
> planned work in, and what is the next safe action?

It composes existing facts. It does not replace `doctor`, `check`,
`context`, `next`, `holds`, `gate`, `verify`, or the board; those remain
the specialist diagnostic and operating surfaces.

The same core object is exposed by:

- `dw status [project] --json`;
- MCP tool `dw_status` with optional `project`; and
- `GET /api/status?project=<slug>` inside the workbench envelope.

Human `dw status` output and the workbench panel are renderers of that
object. They do not add decisions.

## Readiness meaning

The top-level verdict is one of:

- `ready`: the required local rails are wired and the selected roadmap is
  structurally valid. The tree may be dirty, a story may be unfinished,
  or a contract may need attention; those are normal delivery states and
  the next action names the transition.
- `attention`: a blocking precondition makes ordinary story work unsafe:
  required clone wiring is broken, the roadmap has validation errors, or
  Git is in a rewrite operation. The first action is a repair/resolve act.

This is **local readiness**. It does not claim current CI, required GitHub
checks, network services, release publication, or latest available
package version.

Warnings never silently become blockers. They are returned verbatim and
the renderer makes them visible.

## Project selection

- An explicit valid `project` selects it.
- Exactly one discovered project is selected implicitly.
- With more than one project and no explicit selector, none is selected.
  `selection_required` is true and the next action is `select-project`.
- The briefing never picks the first project, the project with the lowest
  phase number, or a plausible in-progress project. Unknown beats guessed.

All discovered projects remain summarized so the caller can choose.

## Model v1

The core document is stamped:

```json
{
  "kind": "delivery-workbench-status",
  "schema_version": 1,
  "verdict": "ready",
  "summary": "ready — WLA-22-02 in progress; 3 unstaged paths",
  "repository": {
    "root": "/repo",
    "branch": "main",
    "head": "0123456789abcdef",
    "operation": "normal",
    "clean": false,
    "changes": {
      "staged": {"count": 0, "paths": []},
      "unstaged": {"count": 3, "paths": ["a", "b", "c"]},
      "untracked": {"count": 0, "paths": []}
    },
    "contract": {
      "state": "absent",
      "path": ".tmp/CONTRACT.md",
      "exists": false,
      "facts_fresh": null,
      "checked_boxes": 0,
      "expected_boxes": 0,
      "story_ids": [],
      "tier": null
    },
    "gate": {
      "state": "not-applicable",
      "ok": null,
      "failure": null,
      "checked_boxes": 0,
      "expected_boxes": 0,
      "declared_stories": [],
      "shipped_stories": []
    }
  },
  "rails": {
    "healthy": true,
    "checks": [{"ok": true, "name": "core.hooksPath", "detail": ".githooks"}]
  },
  "roadmap": {
    "healthy": true,
    "selected_project": "work-log-automation",
    "selection_required": false,
    "issues": [],
    "warnings": [],
    "projects": [{
      "slug": "work-log-automation",
      "prefix": "WLA",
      "current_phase": {"number": 22, "status": "open", "stories_done": 0, "stories_total": 5, "title": "agent-briefing"},
      "next_story": {"story_id": "WLA-22-02", "title": "dw status", "status": "in-progress"},
      "parked_counts": {"blocked": 0, "on_hold": 0, "paused_phases": 0},
      "status_counts": {"in-progress": 1, "ready": 2, "backlog": 2}
    }]
  },
  "actions": [{
    "id": "continue-story",
    "kind": "command",
    "blocking": false,
    "reason": "WLA-22-02 is already in progress",
    "command": [".githooks/dw", "story", "show", "work-log-automation", "22", "WLA-22-02"]
  }],
  "next_action": {
    "id": "continue-story",
    "kind": "command",
    "blocking": false,
    "reason": "WLA-22-02 is already in progress",
    "command": [".githooks/dw", "story", "show", "work-log-automation", "22", "WLA-22-02"]
  }
}
```

Exact key sets are test-pinned. Additive keys are not smuggled into v1:
changing a pinned key set requires an explicit schema decision and, when
incompatible, a version bump plus changelog entry.

### Repository state

Paths are repository-relative, deduplicated, lexically sorted, and capped
at 50 per change bucket. `count` is the complete count even when the list
is capped. Renames include both old and new repository-relative paths.
No file contents enter this model.

`operation` is `normal` or `rewrite` (rebase, cherry-pick, or revert in
progress). A rewrite is attention because starting unrelated roadmap work
inside it is unsafe.

Contract states are:

- `absent` — no `.tmp/CONTRACT.md`;
- `invalid` — present but its core stamped facts cannot be parsed;
- `stale` — branch, HEAD, or index tree no longer matches;
- `unchecked` — facts are fresh but at least one required box is unchecked;
- `refused` — facts/certification exist but the structural gate refuses;
- `passing` — a side-effect-free inspection of the live gate passes.

The `gate` state is `not-applicable` when nothing is staged, otherwise
`pass` or `fail`. Inspection must not append a rail event; reading status
is not a gate attempt.

### Rails and roadmap

`rails.checks` is the structured `run_doctor` result. Status does not
reimplement hook or rider wiring tests.

Roadmap issues come from the existing validators plus repository-level
rendered-rider drift checks. Project summaries reuse the state-feed/API
read model: current phase, next story, holds, and normalized status
counts. Status does not parse a second dialect or reinterpret statuses.

### Actions

Every action has exactly five keys:

- `id`: stable kebab-case decision identifier;
- `kind`: `command` or `manual`;
- `blocking`: whether this must be resolved before ordinary story work;
- `reason`: concise state-derived explanation; and
- `command`: an argv array for `command`, `null` for a deliberate manual
  act. It is never a shell string.

`next_action` is either `null` or exactly equal to `actions[0]` so simple
clients need not infer priority. Remaining actions are useful follow-ups,
not competing first choices.

## Action precedence

The first matching rule wins:

1. `repair-rails` — a required doctor check fails.
2. `repair-roadmap` — validation or generated-rider drift fails.
3. `resolve-rewrite` — Git reports a rebase/cherry-pick/revert state.
4. `select-project` — several projects exist and none was requested.
5. `review-unstaged` — staged work also has unstaged/untracked paths;
   prevent an accidental partial commit before contract generation.
6. `generate-contract` — work is staged and no valid/fresh contract exists
   (`--force` when replacing one).
7. `certify-contract` — the live gate says boxes remain unchecked. This is
   `kind: manual`, `command: null`; the reason names `.tmp/CONTRACT.md`.
8. `repair-gate` — the staged contract exists but another gate rule
   refuses; the reason carries the gate's remediation. Manual unless that
   remediation has a universally safe existing command.
9. `commit` — and only when staged work exists and side-effect-free gate
   inspection passes; argv is `git commit`.
10. `continue-story` — selected next story is already in progress.
11. `review-workspace` — dirty work exists but no story is in progress;
    ask the operator to align it before starting another story.
12. `start-story` — selected next story is ready or backlog.
13. `review-holds` — no actionable story exists and work is parked.
14. `plan-work` — no actionable or parked story exists.

Additional non-first actions may link to the selected story, warnings, or
holds, but may not contradict this order.

Status never invents an evidence command. When an in-progress story needs
proof, `continue-story` points to `dw story show`; the story's acceptance
criteria and test plan determine the real command.

## Human rendering and exit codes

Human output begins with two greppable lines:

```text
status=ready summary=...
next=continue-story command=.githooks/dw story show ...
```

It then shows compact repository, rails, roadmap, and warning lines.
Arguments are shell-quoted only for display; the structured source stays
argv.

- exit 0: verdict `ready` (including select-project and normal dirty/staged
  delivery states);
- exit 1: verdict `attention`;
- ordinary CLI usage/root errors retain the CLI's existing error handling.

MCP and HTTP return attention as a valid structured document, not a tool
or HTTP error. The document exists to explain recovery.

## Purity and security

Status is read-only:

- no roadmap or agent-doc writes;
- no staging or commit;
- no contract generation or checkbox edit;
- no `.git/pmo-events.jsonl` append;
- no network request;
- no work-log or transcript content; and
- no unbounded path/content payload.

Repeated calls over unchanged state produce byte-identical core JSON.
The HTTP envelope may carry its existing observation timestamp; its
`data` object must still equal the CLI/MCP core object.

The MCP exclusion remains load-bearing: `dw_status` may return a manual
certification action or recommend `git commit`, but it cannot perform
either operation.

## Compatibility

The status document is a new v1 model. Existing specialist commands,
schemas, and exit codes do not change. Consumers that need deeper detail
follow the selected project's identifiers into `dw context`, `dw board`,
`dw holds`, `dw story show`, or the corresponding MCP/HTTP surface.
