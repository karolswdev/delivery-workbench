#!/usr/bin/env bash
# Workbench viewport smoke (WLA-5-10): renders every UI view at desktop
# (1440x900) and mobile (390x844) via headless Firefox snapshot mode and
# asserts a rendered screenshot was produced for each. Skips cleanly
# (exit 0 with a SKIP notice) when no Firefox is available — CI covers
# the API/server layer; this harness proves viewport rendering locally.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pmo-ui-smoke.XXXXXX")"
SERVER_PID=""
CAPTURE_DIR="${DW_UI_CAPTURE_DIR:-}"
CAPTURE_PATTERN="${DW_UI_CAPTURE_PATTERN:-}"
FAST_A11Y="${DW_UI_FAST_A11Y:-}"

cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "workbench-ui-smoke.sh: $1" >&2
  exit 1
}

# Renderer contract runs even when no browser is installed. It keeps the
# recommendation separate from the deliberate act boundary: argv stays
# tokenized, apply has only project+token, and prohibited states get no button.
python3 - "$PMO_DIR/workbench/app.js" "$PMO_DIR/workbench/style.css" <<'PY' \
  || fail "status-panel renderer contract failed"
import sys

app = open(sys.argv[1], encoding="utf-8").read()
css = open(sys.argv[2], encoding="utf-8").read()
action = app[app.index("function statusActionHtml"):app.index("function stepArgvHtml")]
controls = app[app.index("function stepControlHtml"):app.index("function statusPanel")]
apply = app[app.index("async function applyReviewedStep"):app.index("function wireStepControl")]
panel = app[app.index("function statusPanel"):app.index("/* ── mission control")]
overview = app[app.index("async function viewOverview"):app.index("async function viewProject")]
preflight = app[app.index("function validateView"):app.index("function jsonView")]
run = app[app.index("function runStateBadge"):app.index("/* ── optional Program / Workflow Studio")]
program = app[app.index("/* ── autonomous program control room"):app.index("/* ── optional Program / Workflow Studio")]
setup = app[app.index("delivery-shaped front door"):app.index("optional Program / Workflow Studio")]
studio = app[app.index("optional Program / Workflow Studio"):app.index("/* ── router")]
assert "data-argv-index" in action and "manual act" in action
assert "<button" not in action and "JSON.stringify" not in action
for token in ("step-review", "step-confirm", "step-apply", "step-cancel",
              "step.applicable", "step.refusal", "No apply control"):
    assert token in controls, token
assert "<input" not in controls and "setInterval" not in controls
assert 'postJson("/api/step/apply"' in apply
assert "project: step.project" in apply and "expect: step.token" in apply
assert "status === 409" in apply and "nothing started" in apply
assert "viewOverview" in apply and "setInterval" not in apply
for forbidden in ('command:', 'argv:', 'git commit', 'certif'):
    assert forbidden not in apply, forbidden
for token in ("data-verdict", "project", "workspace", "contract", "gate"):
    assert token in panel, token
assert '/api/status' in overview and '/api/step' in overview
assert '/api/delivery-setup' in overview and "Promise.all" in overview
assert '/api/presentation/status' in overview
assert 'presentationBody.data' in overview
assert "overflow-wrap: anywhere" in css
assert ".step-confirmation" in css and ".brief-step-unavailable" in css
assert "@media (max-width: 430px)" in css
for token in ("Delivery readiness", "delivery decision", "Affected decision",
              "Next step", "Work and order", "Team", "Review", "Permission",
              "Limits and stops", "Review separate start", "Technical details",
              "semantic hash", "scheduling simulation", "failure routes and checkpoints"):
    assert token in preflight, token
assert "postJson" not in preflight and "creates permission" in preflight
for token in ("Live delivery", "What happens next?", "Scope and progress",
              "Team and review", "Evidence and decisions",
              "Remaining permission and cost", "Readable activity",
              "Recovery truth", "Technical details",
              "Live updates interrupted", "last verified view",
              "saved delivery state", "live_progress",
              "fail checks", "failure routes", "human checkpoints", "hash-chained receipts",
              "Actions and decisions", "Before any action",
              "Decision and blocker inbox", "Could an effect already have occurred?",
              "view.bounded_actions", "exact control catalog",
              "close explicit stream"):
    assert token in run, token
assert "setInterval" not in run and "driver_config" not in run and "argv:" not in run
assert 'aria-labelledby="run-graph-title"' in run
assert "@media (max-width: 520px)" in css and ".run-node.state-active" in css
for token in (".live-answers", ".live-next", ".live-work-groups",
              ".live-two-column", ".live-recovery", ".live-technical",
              ".bounded-action-center", ".bounded-permission",
              ".bounded-inbox-grid", ".bounded-action-grid",
              ".bounded-failure", ".bounded-usage-table"):
    assert token in css, token
for token in ("Optional multi-phase delivery", "delivery plan",
              "Review optional delivery permission",
              "Technical details", "liveProgressShell(view.live_progress",
              "Check for updates", "why this frontier", "team and review",
              "runtime independence proven", "decision groups / exact authority",
              "separation facts", "Technical details: exact seats",
              "nested execution", "quality, dissent, and gates",
              "obligations / debt", "phase progress", "permanently excluded",
              "operator notifications", "transport ≠ authority",
              "boundedActionCenterHtml(view.bounded_actions",
              "exact control catalog", "program-max-ticks",
              "program-act-confirm", "close explicit stream",
              "/api/programs", "program-ledger", "from=${cursor}"):
    assert token in program, token
assert "setInterval" not in program and "driver_config" not in program
assert "argv:" not in program and "command:" not in program
assert '"checkpointed"' in program and '"supervised"' not in program
assert "new EventSource" in program and "stopProgramLive" in program
assert "SNAPSHOT_MODE" in program  # viewport snapshots never open live SSE
for token in (".program-room-grid", ".program-role-table",
              ".program-quality-grid", ".program-controls",
              ".program-timeline", ".program-open-stream"):
    assert token in css, token
for token in ("/api/delivery-setup", "What are you delivering?",
              "Choose the delivery scope", "Choose the operating mode",
              "No option is selected for you", "Review this option",
              "What setup creates", "What could change later", "What stays off",
              "Permission still needed", "Leave for now", "Technical details",
              "aria-pressed", "requestAnimationFrame"):
    assert token in setup, token
for forbidden in ("postJson", "localStorage", "EventSource", "setInterval"):
    assert forbidden not in setup, forbidden
for token in (".delivery-choice-grid", ".delivery-effect-grid",
              "scroll-snap-type: x mandatory", ".delivery-review-actions button:focus"):
    assert token in css, token
for token in ("plan", "simulate", "validate", "technical", "authority",
              "/api/program-studio", "Review this save", "Review removal",
              "Review draft save", "Save this ${objectLabel}",
              "candidate-assignment", "debate-active", "verifier-failed",
              "budget-exhausted", "phase-transition", "complete",
              "Delivery decisions", "data-plan-section",
              "data-plan-correction", "Review before save",
              "Make ownership, independence, and decisions understandable",
              "Team & review", "Independent review",
              "Compatible policy is not a runtime proof",
              "Ask the separately authorized delivery owner",
              "Contested-decision group", "Review auditor",
              "session binding not assigned before runtime",
              "data-team-role-field", "data-team-council-field",
              "Advanced flow building blocks",
              "Technical details", "Lossless configuration",
              "starts no work"):
    assert token in studio, token
assert "setInterval" not in studio and "EventSource" not in studio
assert 'studioState.view = "design"' not in studio
assert 'default_route: "#/"' not in studio  # browser cannot redefine the API invariant
assert "STUDIO_NODE_TYPES" in studio and "data-studio-node" in studio
assert "semantic hash preserved" in studio and "layout hash preserved" in studio
assert "data-field-id" in studio and "scrollIntoView" in studio
for token in ("visitStudioObjects", 'item.kind === "parameter"',
              'item.kind === "artifact"', "nudge.binding === old"):
    assert token in studio, token
for token in ("renameStudioTeamRole", "renameStudioCouncil",
              "const collision", "council.members",
              "council.decision.weights", "document.layout.nodes"):
    assert token in studio, token
for token in (".studio-node.type-loop", ".studio-node.type-debate",
              ".studio-node.type-verifier", ".studio-node.type-meta-verifier",
              ".studio-node.type-master-architect", ".studio-lane",
              ".studio-plan-shell", ".studio-plan-sections",
              ".studio-plan-review", ".studio-technical-view",
              ".studio-team-card-grid", ".studio-quality-constraints",
              ".studio-team-honesty", ".program-team-answers",
              "@media (max-width: 600px)"):
    assert token in css, token
assert ".studio-workarea" in css and "overflow: auto" in css
for token in ("captureAppFocus", "restoreAppFocus", "wireDismissibleRegion",
              "enhanceSemantics", "announceLiveUpdate", "wireTablist",
              'role="dialog"', 'role="tablist"', "focusMain: true"):
    assert token in app, token
for token in (":focus-visible", ".skip-link", "overflow-x: clip",
              "@media (prefers-reduced-motion: reduce)",
              "@media (forced-colors: active)"):
    assert token in css, token
PY

FF=""
for candidate in \
  "/Applications/Firefox.app/Contents/MacOS/firefox" \
  "$(command -v firefox 2>/dev/null || true)"; do
  [ -n "$candidate" ] && [ -x "$candidate" ] && FF="$candidate" && break
done
if [ -z "$FF" ]; then
  echo "workbench-ui-smoke.sh: SKIP (no Firefox available for headless rendering)"
  exit 0
fi

# ── fixture with data for every view ─────────────────────────────────
REPO="$TMP_ROOT/repo"
PROJECT="$REPO/pm/roadmap/sample"
mkdir -p "$PROJECT"
git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "UI Smoke"
git -C "$REPO" config user.email "ui-smoke@example.test"
cat > "$PROJECT/README.md" <<'EOF'
# Sample - Roadmap

**Current phase:** n/a.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|

## Project metadata

- **Slug:** `sample`
- **Story ID prefix:** `SMP`
EOF
DW="$PMO_DIR/bin/dw"
"$DW" --root "$REPO" phase create sample 0 "Smoke Fixture" --goal "Render everything." >/dev/null
"$DW" --root "$REPO" story create sample 0 "Rendered story" >/dev/null
"$DW" --root "$REPO" story status sample 0 SMP-0-01 "done" --evidence-body "- rendered proof." >/dev/null
"$DW" --root "$REPO" story create sample 0 "Open story" >/dev/null
"$PMO_DIR/install.sh" "$REPO" --skip-bootstrap >/dev/null
DW="$REPO/.githooks/dw"
"$DW" --root "$REPO" story status sample 0 SMP-0-02 in-progress >/dev/null
python3 - "$REPO/pm/orchestration/repair-visual.json" "$REPO/pm/orchestration/terminal-visual.json" "$REPO/pm/orchestration/decision-visual.json" <<'PY'
import json
import sys

repair = {
    "kind": "delivery-workbench-orchestration", "schema_version": 1,
    "slug": "repair-visual", "title": "Fail check and repair", "project": "sample",
    "defaults": {
        "max_concurrency": 2, "max_wall_seconds": 3600,
        "max_agent_starts": 4, "max_check_starts": 4,
        "default_timeout_seconds": 60, "max_artifact_bytes": 100000,
    },
    "nodes": [
        {
            "id": "tests", "type": "check",
            "runner": {"kind": "builtin", "name": "file-exists", "path": "missing.fixture"},
            "on_failure": {"action": "route", "node": "repair", "max_visits": 1},
        },
        {
            "id": "repair", "type": "agent", "activation": "failure",
            "role": "repair", "profile": "worker-write",
            "capabilities": ["repository-read", "repository-write"],
            "workspace": "isolated-worktree", "on_failure": {"action": "abort"},
        },
        {
            "id": "handoff", "type": "approval", "needs": ["tests"],
            "prompt": "Review repaired check.", "terminal": "awaiting-certification",
        },
    ],
    "layout": {"nodes": {
        "tests": {"x": 40, "y": 90}, "repair": {"x": 320, "y": 250},
        "handoff": {"x": 600, "y": 90},
    }, "viewport": {"x": 0, "y": 0, "zoom": 1}},
}
terminal = {
    "kind": "delivery-workbench-orchestration", "schema_version": 1,
    "slug": "terminal-visual", "title": "Terminal handoff", "project": "sample",
    "nodes": [{
        "id": "handoff", "type": "approval", "prompt": "Inspect receipts.",
        "terminal": "awaiting-certification",
    }],
    "layout": {"nodes": {"handoff": {"x": 180, "y": 100}},
               "viewport": {"x": 0, "y": 0, "zoom": 1}},
}
decision = {
    "kind": "delivery-workbench-orchestration", "schema_version": 1,
    "slug": "decision-visual", "title": "Human decision", "project": "sample",
    "nodes": [{
        "id": "review", "type": "approval",
        "prompt": "Approve or reject the reviewed checkout repair.",
    }],
    "layout": {"nodes": {"review": {"x": 180, "y": 100}},
               "viewport": {"x": 0, "y": 0, "zoom": 1}},
}
for path, document in zip(sys.argv[1:], (repair, terminal, decision)):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2)
        handle.write("\n")
PY
git -C "$REPO" add .
git -C "$REPO" -c core.hooksPath=/dev/null commit -q -m "UI run fixtures"
PYTHONPATH="$REPO/.githooks" python3 - "$REPO" <<'PY'
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from dw_pmo import FixtureDriver, build_run_plan, start_run, tick_run

root = Path(sys.argv[1]).resolve()
now = datetime.now(timezone.utc).replace(microsecond=0)


def start(score, offset):
    issued = now + timedelta(seconds=offset)
    plan = build_run_plan(
        root, score, "sample", "SMP-0-02",
        issued_at=issued.isoformat(), expires_at=(issued + timedelta(hours=1)).isoformat(),
    )
    return start_run(
        root, plan, plan["start_token"], approved=True,
        approved_by="UI fixture", now=issued,
    )


start("research-build-review", 0)
repair = start("repair-visual", 1)
config = {
    "kind": "delivery-workbench-driver-config", "schema_version": 1,
    "workspace_root": None,
    "profiles": {"worker-write": {
        "adapter": "fixture",
        "capabilities": ["repository-read", "repository-write"],
        "workspace_modes": ["isolated-worktree"],
    }},
}
fixture = FixtureDriver({"repair": {"polls": 0, "state": "succeeded"}})
tick_run(root, repair["run_id"], driver_config=config,
         adapters={"fixture": fixture}, now=now + timedelta(seconds=1))
tick_run(root, repair["run_id"], driver_config=config,
         adapters={"fixture": fixture}, now=now + timedelta(seconds=1))
terminal = start("terminal-visual", 2)
tick_run(root, terminal["run_id"], now=now + timedelta(seconds=2))
decision = start("decision-visual", 3)
tick_run(root, decision["run_id"], now=now + timedelta(seconds=3))
PY

PORT=$(( (RANDOM % 2000) + 21000 ))
"$PMO_DIR/bin/dw-workbench" --root "$REPO" --port "$PORT" --quiet &
SERVER_PID=$!
i=0
until curl -sf "http://127.0.0.1:$PORT/api/projects" >/dev/null 2>&1; do
  i=$((i + 1)); [ "$i" -lt 40 ] || fail "server did not start"; sleep 0.25
done
BASE="http://127.0.0.1:$PORT"

shot() { # name geometry url
  if [ "$FAST_A11Y" = "1" ]; then
    return
  fi
  out="$TMP_ROOT/$1.png"
  profile="$(mktemp -d)"
  "$FF" --headless --no-remote --profile "$profile" \
    --screenshot "$out" --window-size="$2" "$3" >/dev/null 2>&1 &
  ffpid=$!
  waited=0
  while [ ! -s "$out" ] && [ "$waited" -lt 30 ]; do sleep 1; waited=$((waited + 1)); done
  sleep 1
  kill "$ffpid" 2>/dev/null || true
  wait "$ffpid" 2>/dev/null || true
  rm -rf "$profile"
  [ -s "$out" ] || fail "no screenshot produced for $1"
  # a data-bearing render is markedly larger than the empty shell
  size=$(wc -c < "$out" | tr -d ' ')
  [ "$size" -gt 20000 ] || fail "$1 appears unrendered (only $size bytes)"
  if [ -n "$CAPTURE_DIR" ] && [ -n "$CAPTURE_PATTERN" ]; then
    # CAPTURE_PATTERN is deliberately an operator-supplied glob such as
    # orchestration-run-*; quoting it would turn the capture filter literal.
    # shellcheck disable=SC2254
    case "$1" in
      $CAPTURE_PATTERN)
        mkdir -p "$CAPTURE_DIR"
        cp "$out" "$CAPTURE_DIR/$1.png"
        ;;
    esac
  fi
}

# Golden first-arrival state: before adopting any Phase-26 policy, delivery
# setup compares all three modes without preselecting or starting one.
shot "program-studio-empty-desktop" 1440,900 "$BASE/?snapshot=1#/program-studio"
shot "program-studio-empty-mobile" 390,844 "$BASE/?snapshot=1#/program-studio"
shot "delivery-setup-review-desktop" 1440,900 "$BASE/?snapshot=1&setupmode=program&setuptechnical=1#/program-studio"
shot "delivery-setup-review-mobile" 390,844 "$BASE/?snapshot=1&setupmode=program&setuptechnical=1#/program-studio"

# Explicitly adopt rich tracked fixtures only after the empty-state capture.
# The server reads policy live; authoring these files does not create a grant or
# runtime state and lets the remaining captures exercise every advanced view.
mkdir -p "$REPO/pm/workflows" "$REPO/pm/organizations" "$REPO/pm/programs" "$REPO/pm/rubrics"
cp "$PMO_DIR/templates/workflows/"*.json "$REPO/pm/workflows/"
cp "$PMO_DIR/templates/organizations/autonomous-story-cell.json" "$REPO/pm/organizations/"
python3 - "$REPO" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])

workflow = {
    "kind": "delivery-workbench-workflow", "schema_version": 1,
    "slug": "studio-story-flow", "title": "Implement and verify", "version": "1.0.0",
    "parameters": [{"id": "story-id", "type": "string", "required": True, "max_bytes": 128}],
    "defaults": {},
    "nodes": [
        {
            "id": "implement", "type": "agent", "role": "implementer",
            "task": "Implement the selected story.", "workspace": "isolated-worktree",
            "capability_ceiling": ["agent:dispatch", "workspace:write"],
            "timeout_seconds": 900, "max_attempts": 1,
            "inputs": {"story": {"kind": "parameter", "name": "story-id"}},
            "outputs": [{"id": "candidate", "kind": "git-diff", "max_bytes": 1000000}],
            "on_failure": {"kind": "action", "target": "block"},
        },
        {
            "id": "verify", "type": "verdict", "needs": ["implement"],
            "role": "verifier", "rubric": "story-quality",
            "subject": {"kind": "artifact", "name": "implement.candidate"},
            "freshness_seconds": 3600, "max_rationale_bytes": 30000,
            "results": ["pass", "fail", "abstain"],
            "routes": {
                "pass": {"kind": "terminal", "target": "complete"},
                "fail": {"kind": "action", "target": "block"},
                "abstain": {"kind": "action", "target": "checkpoint"},
            },
        },
    ],
    "terminals": [{"id": "complete", "meaning": "complete"}],
    "layout": {"nodes": {"implement": {"x": 90, "y": 110}, "verify": {"x": 430, "y": 110}},
               "viewport": {"x": 0, "y": 0, "zoom": 1}},
}
invalid_workflow = {
    "kind": "delivery-workbench-workflow", "schema_version": 1,
    "slug": "studio-invalid-flow", "title": "Incomplete delivery flow",
    "version": "1.0.0", "parameters": [], "defaults": {},
    "nodes": [], "terminals": [{"id": "complete", "meaning": "complete"}],
    "layout": {"nodes": {}, "viewport": {"x": 0, "y": 0, "zoom": 1}},
    "future_extension": {"preserved": True},
}
program = {
    "kind": "delivery-workbench-program", "schema_version": 1,
    "slug": "studio-program", "title": "Studio multi-phase organization",
    "scope": {
        "project": "sample", "phases": {"from": 0, "through": 0}, "stories": "all",
        "selection": "roadmap-frontier-v1", "blocked_policy": "stop",
    },
    "organization": "autonomous-story-cell",
    "bindings": [{
        "id": "all-stories", "priority": 10,
        "match": {"phase_from": 0, "phase_through": 0},
        "workflow": "studio-story-flow",
        "with": {"story-id": {"kind": "context", "name": "story.id"}},
        "team": "story-cell", "rubrics": ["story-quality"],
    }],
    "phase_gates": [{
        "id": "architecture", "when": "before-phase-complete",
        "role": "master-architect", "rubric": "phase-architecture", "on_fail": "block",
    }],
    "mode_ceiling": "continuous",
    "requested_capabilities": [
        "agent:dispatch", "workspace:write", "certification:verdict",
        "evidence:materialize", "integration:apply", "git:commit",
        "roadmap:story-start", "roadmap:story-complete", "roadmap:phase-advance",
    ],
    "budgets": {
        "max_phases": 1, "max_stories": 2, "max_child_runs": 8,
        "max_agent_starts": 16, "max_check_starts": 24, "max_loop_rounds": 6,
        "max_debate_rounds": 3, "max_repairs_per_story": 2, "max_verdicts": 8,
        "max_integrations": 2, "max_commits": 2, "max_pushes": 1,
        "max_nudges": 4, "max_artifact_bytes": 5000000, "max_wall_seconds": 7200,
    },
    "stop_conditions": [
        "scope-complete", "checkpoint-required", "unresolved-dissent",
        "architect-veto", "blocked-frontier", "budget-exhausted",
        "grant-expired", "grant-revoked",
    ],
    "layout": {"nodes": {
        "roadmap-scope": {"x": 70, "y": 90}, "binding:all-stories": {"x": 370, "y": 265},
        "gate:architecture": {"x": 700, "y": 440},
    }, "viewport": {"x": 0, "y": 0, "zoom": 1}},
}
rubrics = {
    "story-quality": "Story quality",
    "phase-architecture": "Phase architecture",
}
documents = {
    root / "pm/workflows/studio-story-flow.json": workflow,
    root / "pm/workflows/studio-invalid-flow.json": invalid_workflow,
    root / "pm/programs/studio-program.json": program,
}
for slug, title in rubrics.items():
    documents[root / f"pm/rubrics/{slug}.json"] = {
        "kind": "delivery-workbench-rubric", "schema_version": 1,
        "slug": slug, "title": title, "version": "1.0.0", "criteria": [],
    }
for path, document in documents.items():
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
PY

VIEWS="overview:#/ step-confirm:#/ health:#/health trace:#/p/sample/t/SMP-0-01 editor:#/edit/create_story preview:#/edit/attach_evidence validation:#/p/sample board:#/board/sample orchestration-design:#/orchestration/research-build-review orchestration-validate:#/orchestration/research-build-review orchestration-json:#/orchestration/research-build-review orchestration-run-active:#/orchestration/research-build-review orchestration-run-stale:#/orchestration/research-build-review orchestration-run-technical:#/orchestration/research-build-review orchestration-run-repair:#/orchestration/repair-visual orchestration-run-terminal:#/orchestration/terminal-visual studio-plan-workflow:#/program-studio/workflow/architect-debate-delivery studio-plan-program:#/program-studio/program/studio-program studio-plan-invalid:#/program-studio/workflow/studio-invalid-flow studio-team-review:#/program-studio/organization/autonomous-story-cell studio-debate-active:#/program-studio/workflow/architect-debate-delivery studio-budget-exhausted:#/program-studio/workflow/architect-debate-delivery studio-verifier-failed:#/program-studio/organization/autonomous-story-cell studio-phase-transition:#/program-studio/program/studio-program studio-complete:#/program-studio/program/studio-program studio-validate:#/program-studio/workflow/architect-debate-delivery studio-technical-graph:#/program-studio/workflow/architect-debate-delivery studio-technical-config:#/program-studio/workflow/architect-debate-delivery studio-team-technical:#/program-studio/organization/autonomous-story-cell"
for spec in $VIEWS; do
  name="${spec%%:*}"
  route="${spec#*:}"
  extra=""
  case "$name" in
    preview) extra="&autopreview=1" ;;
    step-confirm) extra="&confirmstep=1" ;;
    orchestration-validate) extra="&orchview=validate" ;;
    orchestration-json) extra="&orchview=json" ;;
    orchestration-run-stale) extra="&orchview=run&liveconnection=stale" ;;
    orchestration-run-technical) extra="&orchview=run&livetechnical=1" ;;
    orchestration-run-*) extra="&orchview=run" ;;
    studio-debate-active) extra="&studioview=simulate&studioscenario=debate-active" ;;
    studio-budget-exhausted) extra="&studioview=simulate&studioscenario=budget-exhausted" ;;
    studio-verifier-failed) extra="&studioview=simulate&studioscenario=verifier-failed" ;;
    studio-phase-transition) extra="&studioview=simulate&studioscenario=phase-transition" ;;
    studio-complete) extra="&studioview=simulate&studioscenario=complete" ;;
    studio-validate) extra="&studioview=validate" ;;
    studio-technical-graph) extra="&studioview=technical&studiotechnical=graph" ;;
    studio-technical-config) extra="&studioview=technical&studiotechnical=config" ;;
    studio-team-technical) extra="&studioview=technical&studiotechnical=graph" ;;
  esac
  shot "$name-desktop" 1440,900 "$BASE/?snapshot=1$extra$route"
  shot "$name-mobile" 390,844 "$BASE/?snapshot=1$extra$route"
done

# WLA-27-07 action journeys: focus the real canonical decision model, its
# exact pure preview, and the structured stale refusal without applying an
# action. Both viewport sizes start at the action context rather than the
# top-of-page delivery recap.
shot "run-decision-actions-desktop" 1440,900 "$BASE/?snapshot=1&orchview=run&boundedfocus=inbox#/orchestration/decision-visual"
shot "run-decision-actions-mobile" 390,844 "$BASE/?snapshot=1&orchview=run&boundedfocus=inbox#/orchestration/decision-visual"
shot "run-decision-preview-desktop" 1440,900 "$BASE/?snapshot=1&orchview=run&boundedpreview=decision&boundedfocus=preview#/orchestration/decision-visual"
shot "run-decision-preview-mobile" 390,844 "$BASE/?snapshot=1&orchview=run&boundedpreview=decision&boundedfocus=preview#/orchestration/decision-visual"
shot "run-action-refusal-desktop" 1440,900 "$BASE/?snapshot=1&orchview=run&boundederror=stale&boundedfocus=error#/orchestration/repair-visual"
shot "run-action-refusal-mobile" 390,844 "$BASE/?snapshot=1&orchview=run&boundederror=stale&boundedfocus=error#/orchestration/repair-visual"

# Program planning remains a deliberately entered optional workspace. These
# renders exercise the policy inventory and pure finite-grant form without
# creating local program authority.
shot "program-planning-desktop" 1440,900 "$BASE/?snapshot=1#/programs"
shot "program-planning-mobile" 390,844 "$BASE/?snapshot=1#/programs"

# Real keyboard/semantic exam over the canonical ordinary, setup, bounded,
# repair, decision, recovery, and technical-inspection journeys.
python3 "$SCRIPT_DIR/workbench-accessibility.py" \
  --firefox "$FF" --base "$BASE" --suite core \
  || fail "core accessibility journey exam failed"

# Red-path prominence: the same overview must render a broken rail as
# attention while keeping execution behind deliberate-step review.
mv "$REPO/.githooks/pre-commit" "$REPO/.githooks/pre-commit.off"
shot "overview-attention-desktop" 1440,900 "$BASE/?snapshot=1#/"
shot "overview-attention-mobile" 390,844 "$BASE/?snapshot=1#/"
mv "$REPO/.githooks/pre-commit.off" "$REPO/.githooks/pre-commit"

# Ambiguity prominence: two healthy projects yield the manual
# select-project action; the briefing must not guess one.
"$PMO_DIR/bootstrap/new-project.sh" "$REPO" other "Other" OTH >/dev/null
shot "overview-ambiguous-desktop" 1440,900 "$BASE/?snapshot=1#/"
shot "overview-ambiguous-mobile" 390,844 "$BASE/?snapshot=1#/"

# A second exact fixture exercises the live control-room projection in an
# active nested-program state, a council-certified checkpoint with preserved
# obligation and meta-audit, and a terminal authority stop. Reuse the conductor
# test builder so this browser proof cannot drift into a hand-written fake
# ledger.
kill "$SERVER_PID" 2>/dev/null || true
wait "$SERVER_PID" 2>/dev/null || true
SERVER_PID=""
PROGRAM_FIXTURE_INFO="$TMP_ROOT/program-fixture.txt"
TMPDIR="$TMP_ROOT" PYTHONPATH="$PMO_DIR/lib" python3 - \
  "$PMO_DIR/tests/dw-core-tests.py" "$PROGRAM_FIXTURE_INFO" <<'PY'
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys


spec = importlib.util.spec_from_file_location("dw_ui_tests", sys.argv[1])
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
conductor = module.ProgramConductorTest(
    "test_rule_council_meta_audits_and_ingests_durable_obligation"
)
conductor.setUp()
authority = conductor.authority
now = datetime.now(timezone.utc).replace(microsecond=0)
authority.issued_at = (now - timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
authority.started_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
authority.expires_at = (now + timedelta(seconds=3500)).strftime("%Y-%m-%dT%H:%M:%SZ")
conductor.now = (now + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
conductor.configure_council_workflow(audit="full")

obligation = {
    "id": "document-council-fallback",
    "kind": "technical-debt",
    "statement": "Document the governed council fallback.",
    "priority": "medium",
    "blocking": False,
    "accountable_role": "architect",
    "target": "DM-1-02",
    "citations": ["evidence:council-evidence"],
    "acceptance": "The fallback has an evidence-backed contract.",
    "state": "open",
}
certified = conductor.start()
driver = conductor.core.ProgramFixtureDriver({
    "council-judgment": {"obligations": [obligation]},
})
certified_result = conductor.core.supervise_program(
    conductor.root, certified["run_id"], max_ticks=30,
    driver_config=conductor.config, adapters={"fixture": driver},
    now=conductor.now,
)
assert (certified_result["state"], certified_result["stop"]) == (
    "story-certified", "checkpoint",
)

from dw_pmo.program_surface import (  # noqa: E402
    apply_program_act,
    build_program_act_preview,
)

active = conductor.start()
for _index in range(2):
    preview = build_program_act_preview(authority.root, active["run_id"], "tick")
    apply_program_act(
        authority.root, active["run_id"], "tick", preview["act_token"]
    )

stopped = conductor.start()
reason = "Viewport fixture revocation."
preview = build_program_act_preview(
    authority.root, stopped["run_id"], "revoke", reason=reason
)
apply_program_act(
    authority.root, stopped["run_id"], "revoke", preview["act_token"],
    reason=reason,
)
Path(sys.argv[2]).write_text(
    f"{authority.root}\n{active['run_id']}\n{stopped['run_id']}\n"
    f"{certified['run_id']}\n",
    encoding="utf-8",
)
PY
PROGRAM_REPO="$(sed -n '1p' "$PROGRAM_FIXTURE_INFO")"
PROGRAM_ACTIVE="$(sed -n '2p' "$PROGRAM_FIXTURE_INFO")"
PROGRAM_REVOKED="$(sed -n '3p' "$PROGRAM_FIXTURE_INFO")"
PROGRAM_CERTIFIED="$(sed -n '4p' "$PROGRAM_FIXTURE_INFO")"
PORT=$(( (RANDOM % 2000) + 23001 ))
"$PMO_DIR/bin/dw-workbench" --root "$PROGRAM_REPO" --port "$PORT" --quiet &
SERVER_PID=$!
i=0
until curl -sf "http://127.0.0.1:$PORT/api/programs" >/dev/null 2>&1; do
  i=$((i + 1)); [ "$i" -lt 40 ] || fail "program fixture server did not start"; sleep 0.25
done
BASE="http://127.0.0.1:$PORT"
shot "program-active-desktop" 1440,900 "$BASE/?snapshot=1#/programs/$PROGRAM_ACTIVE"
shot "program-active-mobile" 390,844 "$BASE/?snapshot=1#/programs/$PROGRAM_ACTIVE"
shot "program-technical-desktop" 1440,900 "$BASE/?snapshot=1&livetechnical=1#/programs/$PROGRAM_ACTIVE"
shot "program-technical-mobile" 390,844 "$BASE/?snapshot=1&livetechnical=1#/programs/$PROGRAM_ACTIVE"
shot "program-revoked-desktop" 1440,900 "$BASE/?snapshot=1#/programs/$PROGRAM_REVOKED"
shot "program-revoked-mobile" 390,844 "$BASE/?snapshot=1#/programs/$PROGRAM_REVOKED"
shot "program-certified-desktop" 1440,900 "$BASE/?snapshot=1#/programs/$PROGRAM_CERTIFIED"
shot "program-certified-mobile" 390,844 "$BASE/?snapshot=1#/programs/$PROGRAM_CERTIFIED"
shot "program-remaining-limits-desktop" 1440,900 "$BASE/?snapshot=1&boundedfocus=limits#/programs/$PROGRAM_ACTIVE"
shot "program-remaining-limits-mobile" 390,844 "$BASE/?snapshot=1&boundedfocus=limits#/programs/$PROGRAM_ACTIVE"
shot "program-pause-preview-desktop" 1440,900 "$BASE/?snapshot=1&boundedpreview=pause&boundedfocus=preview#/programs/$PROGRAM_ACTIVE"
shot "program-pause-preview-mobile" 390,844 "$BASE/?snapshot=1&boundedpreview=pause&boundedfocus=preview#/programs/$PROGRAM_ACTIVE"
shot "program-stop-receipt-desktop" 1440,900 "$BASE/?snapshot=1&boundedfocus=receipts#/programs/$PROGRAM_REVOKED"
shot "program-stop-receipt-mobile" 390,844 "$BASE/?snapshot=1&boundedfocus=receipts#/programs/$PROGRAM_REVOKED"

python3 "$SCRIPT_DIR/workbench-accessibility.py" \
  --firefox "$FF" --base "$BASE" --suite program \
  --program-active "$PROGRAM_ACTIVE" \
  --program-revoked "$PROGRAM_REVOKED" \
  --program-certified "$PROGRAM_CERTIFIED" \
  || fail "program accessibility journey exam failed"

echo "workbench-ui-smoke.sh: ok (88 viewport renders plus 13 keyboard, semantic, focus, and wide/narrow journey exams)"
