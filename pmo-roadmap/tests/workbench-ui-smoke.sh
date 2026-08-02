#!/usr/bin/env bash
# Workbench viewport smoke (WLA-5-10, WLA-32-01): renders every UI view at
# desktop (1440x900) and mobile (390x844), in light and dark themes, via
# headless Firefox snapshot mode and asserts each screenshot was produced. Skips cleanly
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
REQUIRE_FIREFOX="${DW_UI_REQUIRE_FIREFOX:-0}"
EXPECTED_RENDER_COUNT=352
RENDER_DESKTOP_LIGHT=0
RENDER_DESKTOP_DARK=0
RENDER_MOBILE_LIGHT=0
RENDER_MOBILE_DARK=0

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

case "$REQUIRE_FIREFOX" in
  0|1) ;;
  *) fail "DW_UI_REQUIRE_FIREFOX must be 0 or 1" ;;
esac
if [ "$REQUIRE_FIREFOX" = "1" ] && [ "$FAST_A11Y" = "1" ]; then
  fail "strict Firefox exam cannot skip required viewport renders"
fi

# Ordinary panel copy is checked before browser discovery, so a CI-less host
# still enforces the explicit Technical details language boundary.
/usr/bin/python3 "$SCRIPT_DIR/workbench-language-lint.py" \
  || fail "ordinary-panel language lint failed"

# Renderer contract runs even when no browser is installed. It keeps the
# recommendation separate from the deliberate act boundary: argv stays
# tokenized, apply has only project+token, and prohibited states get no button.
python3 - "$PMO_DIR/workbench" <<'PY' \
  || fail "status-panel renderer contract failed"
import sys
from pathlib import Path

workbench = Path(sys.argv[1])
source = {path.name: path.read_text(encoding="utf-8") for path in workbench.glob("*.js")}
app = "\n".join(source.values())
css = (workbench / "style.css").read_text(encoding="utf-8")
index = (workbench / "index.html").read_text(encoding="utf-8")
core = source["core.js"]
views = source["views.js"]
board = source["board.js"]
router = source["app.js"]
orch = source["orchestration.js"]
runs = source["runs.js"]
studio_source = source["studio.js"]
editor = source["editor.js"]
interactions = source["interactions.js"]
global_events = source["global-events.js"]
memory = source["memory-panel.js"]
action = core[core.index("function statusActionHtml"):core.index("function stepArgvHtml")]
controls = core[core.index("function stepControlHtml"):core.index("async function applyReviewedStep")]
apply = core[core.index("async function applyReviewedStep"):core.index("function wireStepControl")]
panel = core[core.index("function statusPanel"):]
overview = views[views.index("async function viewOverview"):views.index("async function viewProject")]
board_card = board[board.index("function boardCard"):board.index("/* ── flat board rendering")]
board_wiring = board[board.index("function wireBoardMoves"):]
view_board = board[board.index("async function viewBoard"):]
preflight = orch[orch.index("function validateView"):orch.index("function jsonView")]
program_start = runs.index("/* ── autonomous program control room")
run = runs[:program_start]
program = runs[program_start:]
studio_start = studio_source.index("optional Program / Workflow Studio")
setup = studio_source[:studio_start]
studio = studio_source[studio_start:]
adoption = editor[editor.index("const adoptionReviewMarks"):editor.index("const STATUS_VOCAB")]
assert index.count('class="navlink"') == 2
assert 'class="navlink advanced-toggle"' in index
for label in ("Work", "Health"):
    assert f">{label}</a>" in index, label
for destination in ("plan-link", "delivery-link", "live-link"):
    assert f'id="{destination}"' in index, destination
assert index.count('id="project-switcher"') == 1
assert 'class="project-switcher ops-label"' in index
assert 'id="command-palette-trigger"' in index and 'aria-keyshortcuts="Meta+K Control+K"' in index
assert 'id="refresh-time"' not in index and 'class="topbar-tools"' in index
assert 'id="foot-root" class="visually-hidden"' in index
assert "Project: ${selectedProject}" not in core
assert 'getElementById("command-palette-trigger")' in source["command-palette.js"]
assert 'aria-label", "Needs you, " + count' in source["needs-you.js"]
for token in (".topbar-omni", ".shell-icon-btn", ".needs-you-dropdown",
              "background: var(--surface-elevated)", "box-shadow: var(--shadow-2)",
              ".cp-dialog", "box-shadow: var(--shadow-3)", ".footbar"):
    assert token in css, token
assert "The browser adds no authority" in app
assert "browser-confirmed program action may use pre-granted delivery permission" in app
for token in ("project-switcher", "PROJECT_STORAGE_KEY", "viewProjectSelector",
              "viewUnavailableProject", "wireTechnicalFolds", "destinationNav"):
    assert token in index + app, token
assert "projects.length > 1 && !selectedProject" in app
assert "projects[0].slug" not in view_board
assert "data-argv-index" in action and "manual act" in action
assert "<button" not in action and "JSON.stringify" not in action
for token in ("step-review", "step-confirm", "step-apply", "step-cancel",
              "step.applicable", "step.refusal", "No apply control"):
    assert token in controls, token
assert "<input" not in controls and "setInterval" not in controls
assert 'postJson("/api/step/apply"' in apply
assert "project: step.project" in apply and "expect: step.token" in apply
assert "status === 409" in apply and "nothing started" in apply
assert "viewBoard" in apply and "setInterval" not in apply
for forbidden in ('command:', 'argv:', 'git commit', 'certif'):
    assert forbidden not in apply, forbidden
for token in ("data-verdict", "project", "workspace", "contract", "gate"):
    assert token in panel, token
assert '/api/status' in overview and '/api/step' in overview
assert '/api/delivery-setup' in overview and "Promise.all" in overview
assert '/api/presentation/status' in overview
assert 'presentationBody.data' in overview
assert "else if (!parts.length) await viewBoard(selectedProject)" in router
for token in ("boardOverviewStrip", "Needs attention", "Stories", "Phase lanes",
              "openCreatePanel", "openMovePanel", "openPhasePanel",
              'kind: "create_story"', 'kind: "update_story_status"',
              '"pause_phase"', '"resume_phase"',
              "Cross-phase moves are not supported",
              'postJson("/api/mutations/preview"',
              '"/api/mutations/apply"'):
    assert token in board, token
assert board_wiring.index("column.dataset.phase !== from.phase") < board_wiring.index("openMovePanel(slug")
assert "Parking on-hold requires a reason" in board
assert "Preview refused. Nothing changed." in board
for token in ('class="bcard-id ops-label"', 'class="bcard-title"',
              'class="bcard-meta"', 'class="bcard-link"',
              'class="bcol-empty-copy"'):
    assert token in board, token
assert "<dw-status-pill" not in board_card
assert "<dw-badge" not in board_card
assert board_card.count("${attnBadge}") == 1
assert board_card.index('class="bcard-link"') < board_card.index('class="bcard-title"') < board_card.index('class="bcard-meta"')
for token in (".board-overview-flat", ".board-action-panel", ".board-preview",
              ".bcard-meta", ".bcard-attention", ".bcol-empty-copy",
              ".bcard-dragging", ".bcol-drag-over", "@media (max-width: 700px)"):
    assert token in css, token
assert "background: var(--accent-interactive)" in css
assert "content: none" in css
assert "overflow-wrap: anywhere" in css
for token in ("--font-sans", "--font-mono", "--weight-medium", "--type-body",
              "--space-4", "--surface-canvas", "--surface-elevated",
              "--surface-topbar", "--text-body", "--accent-interactive",
              "--border-standard", "--status-needs-you", "--status-blocked",
              "--status-done", "--status-live", "--radius-7", "--radius-18",
              "--shadow-1", "--shadow-2", "--shadow-3"):
    assert token in css, token
for literal in ("#080a0e", "#0c1119", "#0e141d", "#4d8cff", "#ff6a45",
                "#f5a623", "#38d39f", "#f4f1ea", "#fffdf8"):
    assert literal in css, literal
for name in ("space-grotesk-latin.woff2", "jetbrains-mono-latin.woff2"):
    font = workbench / "fonts" / name
    assert font.is_file() and font.stat().st_size > 10_000, name
assert (workbench / "fonts" / "OFL-NOTICE.txt").is_file()
assert "@font-face" in css and "https://" not in css and "'cv01'" not in css
assert "color-scheme: dark" in css
assert '@media (prefers-color-scheme: light)' in css
assert ':root[data-theme="light"]' in css and ':root[data-theme="dark"]' in css
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
              "Approve this bounded run", "Allowed work", "Spend ceiling",
              "Permission ends", "What makes it stop", "Push destination",
              "Never allowed", "Raise its own authority",
              "No limits were reduced", "Review a fresh permission preview",
              "standing_nudges", "signal_channel", "close explicit stream"):
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
              "program-act-confirm", "Approve optional delivery",
              "Narrow permission", "Preview the reduced permission",
              "You may lower these limits", "Delivery is not automatic",
              "browser adds no authority", "Back to permission summary",
              "close explicit stream",
              "/api/programs", "program-ledger", "from=${cursor}"):
    assert token in program, token
assert "setInterval" not in program and "driver_config" not in program
assert "argv:" not in program and "command:" not in program
assert "checkpointed: 1" in app and '"supervised"' not in program
assert "new EventSource" in program and "stopProgramLive" in program
assert "SNAPSHOT_MODE" in program  # viewport snapshots never open live SSE
for token in (".program-room-grid", ".program-role-table",
              ".program-quality-grid", ".program-controls",
              ".program-timeline", ".program-open-stream",
              ".consent-fact-grid", ".consent-never",
              ".program-narrow-form", ".program-budget-choices"):
    assert token in css, token
for token in ("/api/delivery-setup", "What are you delivering?",
              "Choose the delivery scope", "Choose the operating mode",
              "No option is selected for you", "Review this option",
              "What setup creates", "What could change later", "What stays off",
              "Permission still needed", "Leave for now", "Technical details",
              "aria-pressed", 'focusElement(document.getElementById("delivery-review"))'):
    assert token in setup, token
for forbidden in ("postJson", "localStorage", "EventSource", "setInterval"):
    assert forbidden not in setup, forbidden
for token in ("Turn a rough idea into a phase plan", "Unresolved assumptions",
              "model.configuration.label", "Files this setup would save",
              "Accepted for preview", "Reject with corrections", "Correction packet",
              "dw setup preview", "/api/setup/review", "/api/setup/preview",
              "/api/setup/apply", "Technical details", "Nothing is saved yet",
              "adoptionReviewMarks", "IDEATION_STORAGE_KEY", "captureAppFocus",
              "invalidateIdeationPreview", "one-use setup lease"):
    assert token in adoption, token
for forbidden in ("sessionStorage", "indexedDB", "EventSource", "setInterval", 'aria-live="'):
    assert forbidden not in adoption, forbidden
for token in (".adoption-review", ".adoption-unresolved", ".adoption-configuration",
              ".adoption-path-split", ".adoption-correction-form", ".ideation-flow",
              ".ideation-steps", ".ideation-draft", ".ideation-preview-files",
              "@media (prefers-color-scheme: light)", "@media (max-width: 600px)"):
    assert token in css, token
for token in (".delivery-choice-grid", ".delivery-effect-grid",
              "scroll-snap-type: x mandatory", ".delivery-review-actions button:focus"):
    assert token in css, token
for token in ("plan", "simulate", "validate", "technical", "authority",
              "/api/program-studio", "Review this save", "Review removal",
              "Review draft save", "Save this ${objectLabel}",
              "candidate-assignment", "debate-active", "verifier-failed",
              "budget-exhausted", "phase-transition", "complete",
              "Delivery decisions", "data-plan-section",
              "What will be delivered?", "Who will do the work?",
              "Who will review the work independently?", "Repair path",
              "How much time, spending, and work may this delivery use?",
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
              "What reviewers will check", "data-studio-return-plain",
              "Review the change again to get a fresh preview",
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
              ".studio-form-technical", ".studio-review-criteria",
              ".studio-team-card-grid", ".studio-quality-constraints",
              ".studio-team-honesty", ".program-team-answers",
              "@media (max-width: 600px)"):
    assert token in css, token
assert ".studio-workarea" in css and "overflow: auto" in css
for token in ("captureAppFocus", "restoreAppFocus", "wireDismissibleRegion",
              "enhanceSemantics", "announceLiveUpdate", "wireTablist",
              'role="dialog"', 'role="tablist"', "focusMain: true"):
    assert token in app, token
for token in (":where(a, button, input, select, textarea, summary, [tabindex]):focus",
              ".skip-link:focus", "overflow-x: clip",
              "@media (prefers-reduced-motion: reduce)",
              "@media (forced-colors: active)"):
    assert token in css, token
assert "outline: none" not in css
assert "outline:none" not in css
# WLA-35-09: fast shell, shared motion, persisted density, recovery, and IDs.
for token in ("routeSkeletonHtml", "updateRouteSkeleton", "presentationPromise", "projectsPromise"):
    assert token in router, token
assert "if (!SNAPSHOT_MODE)" in core
assert 'xhr.open("GET", path, false)' in core  # deterministic snapshot path only
for token in ('id="density-toggle"', 'aria-label="Use compact density"'):
    assert token in index, token
for token in ("DENSITY_STORAGE_KEY", "storedDensity", "applyDensity", "localStorage.setItem"):
    assert token in core, token
for token in ("--motion-short", "--motion-panel", "--motion-route", "--motion-ease",
              ':root[data-density="compact"]', "--target-min"):
    assert token in css, token
assert "motionDuration" in interactions and "--motion-panel" in interactions
assert 'classList.add("reduced-motion")' in index
assert ":root.reduced-motion" in css and ".reduced-motion *" in css
assert 'classList.contains("reduced-motion")' in interactions
reduced = css[css.index("@media (prefers-reduced-motion: reduce)"):]

for token in ("animation: none !important", "transition-duration: 0s !important",
              "transition-delay: 0s !important"):
    assert token in reduced, token
for token in ("disconnected", "retrying", "caught-up", "restored",
              "response.status === 503", "Retry in a moment", "dw-stream-state"):
    assert token in global_events, token
for token in ("copyToClipboard", "dataset.copyText", "Identifier copied."):
    assert token in core, token
assert "copyableIdentifierHtml" in memory and "originating_receipt_ref" in memory
assert "aria-describedby" in editor and "aria-invalid" in editor
assert ".copyable-id" in css and ".slide-over[hidden]" in css
PY

FF=""
for candidate in \
  "/Applications/Firefox.app/Contents/MacOS/firefox" \
  "$(command -v firefox 2>/dev/null || true)"; do
  [ -n "$candidate" ] && [ -x "$candidate" ] && FF="$candidate" && break
done
if [ -z "$FF" ]; then
  if [ "$REQUIRE_FIREFOX" = "1" ]; then
    fail "strict Firefox exam requires an executable Firefox"
  fi
  echo "workbench-ui-smoke.sh: SKIP (no Firefox available for headless rendering; set DW_UI_REQUIRE_FIREFOX=1 to refuse this skip)"
  exit 0
fi
FF_VERSION="$($FF --version 2>&1)" || fail "Firefox version check could not launch $FF"
[ -n "$FF_VERSION" ] || fail "Firefox version check returned no version"

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
python3 - "$REPO/pm/orchestration/repair-visual.json" "$REPO/pm/orchestration/terminal-visual.json" "$REPO/pm/orchestration/decision-visual.json" "$REPO/pm/orchestration/consent-visual.json" <<'PY'
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
consent = {
    "kind": "delivery-workbench-orchestration", "schema_version": 1,
    "slug": "consent-visual", "title": "Consent review", "project": "sample",
    "defaults": {
        "max_concurrency": 1, "max_wall_seconds": 3600,
        "max_agent_starts": 2, "max_check_starts": 2,
        "default_timeout_seconds": 60, "max_artifact_bytes": 100000,
    },
    "nodes": [{
        "id": "review", "type": "approval", "prompt": "Review bounded work.",
        "terminal": "awaiting-certification",
    }],
    "layout": {"nodes": {"review": {"x": 180, "y": 100}},
               "viewport": {"x": 0, "y": 0, "zoom": 1}},
}
for path, document in zip(sys.argv[1:], (repair, terminal, decision, consent)):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2)
        handle.write("\n")
PY
python3 - "$REPO" <<'PY'
import copy
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
provenance = lambda kind, note: {"kind": kind, "source_note": note}
text = lambda value, kind="user-answer": {
    "text": value, "provenance": provenance(kind, "Recorded during setup review."),
}

def proposal(slug, prefix, title, mode="build"):
    return {
        "schema": "delivery-workbench-setup-proposal@1", "state": "reviewed",
        "project": {"slug": slug, "prefix": prefix, "title": title,
                    "provenance": provenance("user-answer", "The operator named the project.")},
        "source_intent": {"idea": "Make setup understandable before any files are saved.",
                          "mode": mode,
                          "provenance": provenance("user-answer", "The opening setup answer.")},
        "tracked_content": {"roadmap": {"phases": [{
            "number": 2, "title": "First proof", "goal": "Prove one useful path end to end.",
            "provenance": provenance("recommendation", "Suggested as the smallest useful phase."),
            "stories": [{"id_sketch": f"{prefix}-2-01", "title": "Prove the first path",
                "problem": "The useful path has not been proven yet.",
                "scope_in": [text("Build the bounded first path.")],
                "scope_out": [text("Hosted operation stays out.", "recommendation")],
                "acceptance_criteria": [text("A focused check proves the path.")],
                "dependencies": [],
                "provenance": provenance("recommendation", "Suggested first proof.")}]
        }], "exit_criteria": [text("The first path is reviewable.", "recommendation")]},
        "policy": None},
        "local_content": {"driver_bindings": {"implementer": {
            "adapter": "fixture", "model": "fixture-model", "provider": "fixture",
            "provenance": provenance("repository-fact", "The local fixture profile is available.")}}},
        "unresolved_questions": [], "starts_work": False, "creates_grant": False,
        "certifies": False, "commits": False,
    }

fixtures = root / "setup-review-fixtures"
fixtures.mkdir()
green = proposal("green-review", "GR", "Greenfield review")
wrapper = lambda slug: {"document": {"slug": slug, "kind": "fixture-policy", "schema_version": 1},
                        "provenance": provenance("recommendation", "Generated for review.")}
green["tracked_content"]["policy"] = {
    "program": wrapper("green-program"), "workflows": [wrapper("green-workflow")],
    "organization": wrapper("green-team"), "rubrics": [wrapper("green-review")],
    "provenance": provenance("recommendation", "Optional bounded delivery was requested."),
}
existing = proposal("sample", "SMP", "Sample", "maintain")
unresolved = proposal("questions-review", "QR", "Questions review")
unresolved["unresolved_questions"] = [
    {"question": "Who owns the first review?", "provenance": provenance("user-answer", "No owner was named.")},
    {"question": "Which deployment target comes later?", "provenance": provenance("recommendation", "The idea did not choose one.")},
    {"question": "What is the first cost ceiling?", "provenance": provenance("repository-fact", "No budget policy exists yet.")},
]
invalid = copy.deepcopy(green)
del invalid["project"]["title"]
for name, value in (("greenfield", green), ("existing", existing),
                    ("unresolved-heavy", unresolved), ("invalid", invalid)):
    (fixtures / f"{name}.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
PY
git -C "$REPO" add .
git -C "$REPO" -c core.hooksPath=/dev/null commit -q -m "UI run fixtures"
PYTHONPATH="$REPO/.githooks" python3 - "$REPO" <<'PY'
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from dw_pmo import FixtureDriver, build_run_plan, start_run, tick_run
from dw_pmo.orchestration_run import transition_run

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
paused = start("research-build-review", 10)
transition_run(
    root, paused["run_id"], "pause", paused["ledger_head"],
    reason="Viewport fixture pause is resumable.", now=now + timedelta(seconds=10),
)
revoked = start("research-build-review", 11)
transition_run(
    root, revoked["run_id"], "revoke", revoked["ledger_head"],
    reason="Viewport fixture permission permanently revoked.",
    now=now + timedelta(seconds=11),
)
cancelled = start("research-build-review", 12)
transition_run(
    root, cancelled["run_id"], "cancel", cancelled["ledger_head"],
    reason="Viewport fixture cancellation revokes and interrupts bounded work.",
    now=now + timedelta(seconds=12),
)
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
FONT_TYPE="$(curl -sfD - -o /dev/null "$BASE/fonts/space-grotesk-latin.woff2" \
  | tr -d '\r' | grep -i '^Content-Type:' | cut -d' ' -f2-)"
[ "$FONT_TYPE" = "font/woff2" ] || fail "vendored fonts are not served as font/woff2"

shot() { # name geometry url
  if [ "$FAST_A11Y" = "1" ]; then
    return
  fi
  for theme in light dark; do
    out="$TMP_ROOT/$1-$theme.png"
    profile="$(mktemp -d "$TMP_ROOT/firefox-$theme.XXXXXX")"
    if [ "$theme" = "dark" ]; then
      system_theme=1
      content_theme=0
    else
      system_theme=0
      content_theme=1
    fi
    cat > "$profile/user.js" <<EOF
user_pref("ui.systemUsesDarkTheme", $system_theme);
user_pref("layout.css.prefers-color-scheme.content-override", $content_theme);
user_pref("browser.shell.checkDefaultBrowser", false);
EOF
    "$FF" --headless --no-remote --profile "$profile" \
      --screenshot "$out" --window-size="$2" "$3" >/dev/null 2>&1 &
    ffpid=$!
    waited=0
    while [ ! -s "$out" ] && [ "$waited" -lt 30 ]; do sleep 1; waited=$((waited + 1)); done
    # The file is already non-empty; allow Firefox one short flush interval
    # before terminating the one-shot profile instead of adding a full second
    # to every matrix cell.
    sleep 0.2
    kill "$ffpid" 2>/dev/null || true
    wait "$ffpid" 2>/dev/null || true
    rm -rf "$profile"
    [ -s "$out" ] || fail "no $theme screenshot produced for $1"
    if [ -n "$CAPTURE_DIR" ] && [ -n "$CAPTURE_PATTERN" ]; then
      # Preserve requested captures even when a later render assertion fails.
      # shellcheck disable=SC2254
      case "$1" in
        $CAPTURE_PATTERN)
          mkdir -p "$CAPTURE_DIR"
          cp "$out" "$CAPTURE_DIR/$1-$theme.png"
          ;;
      esac
    fi
    # A data-bearing render is normally markedly larger than the empty shell.
    # PNG compression varies by Firefox build, so a smaller file must prove
    # real visual detail instead of passing on byte count alone. Representative
    # desktop shots also prove the content region has full-strength contrast;
    # this catches both transparent routes and captures taken mid fade-in.
    size=$(wc -c < "$out" | tr -d ' ')
    check_content=0
    case "$1" in
      board-home-desktop|memory-rich-desktop|adoption-review-existing-desktop) check_content=1 ;;
    esac
    if [ "$size" -le 20000 ] || [ "$check_content" = "1" ]; then
      /usr/bin/python3 - "$out" "$check_content" <<'PYPNG' \
        || fail "$1-$theme appears unrendered ($size bytes; content detail check failed)"
import math
import struct
import sys
import zlib

raw = open(sys.argv[1], "rb").read()
check_content = sys.argv[2] == "1"
assert raw.startswith(b"\x89PNG\r\n\x1a\n")
pos = 8
idat = bytearray()
width = height = color_type = bit_depth = None
while pos < len(raw):
    length = struct.unpack(">I", raw[pos:pos + 4])[0]
    kind = raw[pos + 4:pos + 8]
    data = raw[pos + 8:pos + 8 + length]
    pos += 12 + length
    if kind == b"IHDR":
        width, height, bit_depth, color_type = struct.unpack(">IIBB", data[:10])
    elif kind == b"IDAT":
        idat.extend(data)
    elif kind == b"IEND":
        break
assert bit_depth == 8 and color_type in (2, 6)
channels = 3 if color_type == 2 else 4
stride = width * channels
stream = zlib.decompress(bytes(idat))
previous = bytearray(stride)
colors = set()
content_luminance = []
offset = 0
for y in range(height):
    filter_type = stream[offset]
    offset += 1
    encoded = stream[offset:offset + stride]
    offset += stride
    row = bytearray(stride)
    for x, value in enumerate(encoded):
        left = row[x - channels] if x >= channels else 0
        up = previous[x]
        upper_left = previous[x - channels] if x >= channels else 0
        if filter_type == 0:
            decoded = value
        elif filter_type == 1:
            decoded = value + left
        elif filter_type == 2:
            decoded = value + up
        elif filter_type == 3:
            decoded = value + ((left + up) // 2)
        elif filter_type == 4:
            estimate = left + up - upper_left
            pa, pb, pc = abs(estimate - left), abs(estimate - up), abs(estimate - upper_left)
            decoded = value + (left if pa <= pb and pa <= pc else up if pb <= pc else upper_left)
        else:
            raise AssertionError(f"unsupported PNG filter {filter_type}")
        row[x] = decoded & 0xFF
    if y % 4 == 0:
        for x in range(0, width, 4):
            start = x * channels
            colors.add(bytes(row[start:start + 3]))
            if check_content and 80 <= y < min(520, height) and 20 <= x < width - 20:
                red, green, blue = row[start:start + 3]
                content_luminance.append((299 * red + 587 * green + 114 * blue) / 1000)
    previous = row
assert width > 0 and height > 0 and len(colors) >= 32
if check_content:
    mean = sum(content_luminance) / len(content_luminance)
    variance = sum((value - mean) ** 2 for value in content_luminance) / len(content_luminance)
    assert math.sqrt(variance) >= 10
PYPNG
    fi
    case "$1-$theme" in
      *-desktop-light) RENDER_DESKTOP_LIGHT=$((RENDER_DESKTOP_LIGHT + 1)) ;;
      *-desktop-dark) RENDER_DESKTOP_DARK=$((RENDER_DESKTOP_DARK + 1)) ;;
      *-mobile-light) RENDER_MOBILE_LIGHT=$((RENDER_MOBILE_LIGHT + 1)) ;;
      *-mobile-dark) RENDER_MOBILE_DARK=$((RENDER_MOBILE_DARK + 1)) ;;
      *) fail "screenshot name must identify desktop or mobile viewport: $1-$theme" ;;
    esac
  done
}

# Golden first-arrival state: before adopting any Phase-26 policy, delivery
# setup compares all three modes without preselecting or starting one.
shot "program-studio-empty-desktop" 1440,900 "$BASE/?snapshot=1#/program-studio"
shot "program-studio-empty-mobile" 390,844 "$BASE/?snapshot=1#/program-studio"
shot "delivery-setup-review-desktop" 1440,900 "$BASE/?snapshot=1&setupmode=program&setuptechnical=1#/program-studio"
shot "delivery-setup-review-mobile" 390,844 "$BASE/?snapshot=1&setupmode=program&setuptechnical=1#/program-studio"
for state in greenfield existing unresolved-heavy invalid; do
  shot "adoption-review-$state-desktop" 1440,900 "$BASE/?snapshot=1&proposal=setup-review-fixtures/$state.json#/edit/adoption_review"
  shot "adoption-review-$state-mobile" 390,844 "$BASE/?snapshot=1&proposal=setup-review-fixtures/$state.json#/edit/adoption_review"
done
for state in idea draft review preview refusal applied; do
  capture_state="$state"
  [ "$state" = "idea" ] && capture_state="empty"
  shot "ideation-$capture_state-desktop" 1440,900 "$BASE/?snapshot=1&project=sample&ideationstep=$state#/edit/adoption_review"
  shot "ideation-$capture_state-mobile" 390,844 "$BASE/?snapshot=1&project=sample&ideationstep=$state#/edit/adoption_review"
done

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
        "program:select", "agent:dispatch", "workspace:write", "verdict:issue",
        "certification:verdict", "evidence:materialize", "integration:apply",
        "contract:generate", "git:commit", "roadmap:story-start",
        "roadmap:story-complete", "roadmap:phase-advance",
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
        "slug": slug, "title": title,
        "description": "Calm, source-backed questions for independent review.",
        "version": "1.0.0", "subject_type": "diff",
        "result_vocabulary": ["pass", "fail", "needs-repair", "escalate"],
        "aggregation": {
            "method": "all", "threshold": 1, "on_pass": "pass",
            "on_fail": "needs-repair", "on_abstain": "escalate",
            "on_inconclusive": "needs-repair",
        },
        "freshness": {
            "max_age_seconds": 3600,
            "bind": ["subject", "repository", "program", "assignment", "rubric", "ledger"],
        },
        "layout": {},
        "criteria": [{
            "id": "intent-and-evidence",
            "question": "Does the delivered change match the plan and include trustworthy evidence?",
            "evaluation": {"kind": "agent-judgment", "fact": None},
            "required_evidence_kinds": ["git-diff"], "min_citations": 2,
            "allowed_results": ["pass", "fail", "abstain", "inconclusive"],
            "rationale_max_bytes": 2000, "veto": True,
        }],
    }
for path, document in documents.items():
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
PY
PYTHONPATH="$PMO_DIR/lib" python3 - "$REPO" <<'PY'
import json
from pathlib import Path
import sys

from dw_pmo.orchestration_driver import write_driver_config

root = Path(sys.argv[1])
organization = json.loads(
    (root / "pm/organizations/autonomous-story-cell.json").read_text()
)
profiles = {}
for agent in organization["agents"]:
    writable = "workspace:write" in agent["capability_ceiling"]
    profiles[agent["profile"]] = {
        "adapter": "fixture",
        "capabilities": ["repository-read", *(["repository-write"] if writable else [])],
        "workspace_modes": ["isolated-worktree" if writable else "read-only"],
    }
write_driver_config(root, {
    "kind": "delivery-workbench-driver-config", "schema_version": 1,
    "workspace_root": None, "profiles": profiles,
})
PY

VIEWS="board-home:#/ step-confirm:#/ health:#/health trace:#/p/sample/t/SMP-0-01 editor:#/edit/create_story preview:#/edit/attach_evidence validation:#/p/sample board-route:#/board/sample board-create:#/board/sample board-park-refusal:#/board/sample board-done-refusal:#/board/sample orchestration-design:#/orchestration/research-build-review orchestration-validate:#/orchestration/research-build-review orchestration-json:#/orchestration/research-build-review orchestration-run-active:#/orchestration/research-build-review orchestration-run-stale:#/orchestration/research-build-review orchestration-run-technical:#/orchestration/research-build-review orchestration-run-repair:#/orchestration/repair-visual orchestration-run-terminal:#/orchestration/terminal-visual studio-plan-workflow:#/program-studio/workflow/architect-debate-delivery studio-plan-program:#/program-studio/program/studio-program program-studio-plain-delivery:#/program-studio/program/studio-program program-studio-plain-review:#/program-studio/program/studio-program program-studio-plain-technical:#/program-studio/workflow/studio-story-flow studio-plan-invalid:#/program-studio/workflow/studio-invalid-flow studio-team-review:#/program-studio/organization/autonomous-story-cell studio-debate-active:#/program-studio/workflow/architect-debate-delivery studio-budget-exhausted:#/program-studio/workflow/architect-debate-delivery studio-verifier-failed:#/program-studio/organization/autonomous-story-cell studio-phase-transition:#/program-studio/program/studio-program studio-complete:#/program-studio/program/studio-program studio-validate:#/program-studio/workflow/architect-debate-delivery studio-technical-graph:#/program-studio/workflow/architect-debate-delivery studio-technical-config:#/program-studio/workflow/architect-debate-delivery studio-team-technical:#/program-studio/organization/autonomous-story-cell"
for spec in $VIEWS; do
  name="${spec%%:*}"
  route="${spec#*:}"
  extra=""
  case "$name" in
    preview) extra="&autopreview=1" ;;
    step-confirm) extra="&confirmstep=1" ;;
    board-create) extra="&autocreate=Draft%20board%20task&createstatus=ready" ;;
    board-park-refusal) extra="&automove=SMP-0-02:on-hold&autopreview=1" ;;
    board-done-refusal) extra="&automove=SMP-0-02:done&autopreview=1" ;;
    orchestration-validate) extra="&orchview=validate" ;;
    orchestration-json) extra="&orchview=json" ;;
    orchestration-run-stale) extra="&orchview=run&liveconnection=stale" ;;
    orchestration-run-technical) extra="&orchview=run&livetechnical=1" ;;
    orchestration-run-*) extra="&orchview=run" ;;
    program-studio-plain-delivery) extra="&studiosection=scope" ;;
    program-studio-plain-review) extra="&studiosection=quality" ;;
    program-studio-plain-technical) extra="&studiosection=decisions&studiofold=1&studiotechnical=config&studiofocus=technical" ;;
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

# WLA-32-07 mission control: one combined inventory at both widths and themes
# for every authority state a person must distinguish at a glance.
for state in empty active awaiting-decision paused revoked cancelled complete; do
  shot "live-$state-desktop" 1440,900 "$BASE/?snapshot=1&project=sample&livescenario=$state#/live"
  shot "live-$state-mobile" 390,844 "$BASE/?snapshot=1&project=sample&livescenario=$state#/live"
done
shot "live-stale-disconnected-desktop" 1440,900 "$BASE/?snapshot=1&project=sample&livescenario=stale&liveconnection=stale#/live"
shot "live-stale-disconnected-mobile" 390,844 "$BASE/?snapshot=1&project=sample&livescenario=stale&liveconnection=stale#/live"

# WLA-35-09 dark-mode journeys: each call renders light and dark. Together
# these cover the memory pane and decision timeline, its empty and error
# states, Needs you, focus rings, status pills, skeletons, both densities,
# and every global reconnect announcement at wide and 390px viewports.
for state in rich empty error; do
  shot "memory-$state-desktop" 1440,900 "$BASE/?snapshot=1&project=sample&memoryscenario=$state#/board/sample"
  shot "memory-$state-mobile" 390,844 "$BASE/?snapshot=1&project=sample&memoryscenario=$state#/board/sample"
done
shot "needs-you-desktop" 1440,900 "$BASE/?snapshot=1&project=sample&needsyouopen=1#/board/sample"
shot "needs-you-mobile" 390,844 "$BASE/?snapshot=1&project=sample&needsyouopen=1#/board/sample"
shot "design-focus-desktop" 1440,900 "$BASE/?snapshot=1&designfocus=1#/design"
shot "design-focus-mobile" 390,844 "$BASE/?snapshot=1&designfocus=1#/design"
for state in disconnected retrying caught-up restored capacity; do
  shot "global-$state-desktop" 1440,900 "$BASE/?snapshot=1&project=sample&liveconnection=global-$state#/board/sample"
  shot "global-$state-mobile" 390,844 "$BASE/?snapshot=1&project=sample&liveconnection=global-$state#/board/sample"
done
for density in comfortable compact; do
  shot "density-$density-desktop" 1440,900 "$BASE/?snapshot=1&project=sample&density=$density#/board/sample"
  shot "density-$density-mobile" 390,844 "$BASE/?snapshot=1&project=sample&density=$density#/board/sample"
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

# WLA-32-06 consent slips: both start surfaces, their unchanged and narrowed
# permission previews, and the plain stale-token refusal at both widths/themes.
shot "consent-run-unchanged-desktop" 1440,900 "$BASE/?snapshot=1&orchview=run&consentpreview=run-unchanged#/orchestration/consent-visual"
shot "consent-run-unchanged-mobile" 390,844 "$BASE/?snapshot=1&orchview=run&consentpreview=run-unchanged#/orchestration/consent-visual"
shot "consent-run-narrowed-desktop" 1440,900 "$BASE/?snapshot=1&orchview=run&consentpreview=run-narrowed#/orchestration/consent-visual"
shot "consent-run-narrowed-mobile" 390,844 "$BASE/?snapshot=1&orchview=run&consentpreview=run-narrowed#/orchestration/consent-visual"
shot "consent-run-refusal-desktop" 1440,900 "$BASE/?snapshot=1&orchview=run&consentpreview=run-refusal#/orchestration/consent-visual"
shot "consent-run-refusal-mobile" 390,844 "$BASE/?snapshot=1&orchview=run&consentpreview=run-refusal#/orchestration/consent-visual"
shot "consent-program-unchanged-desktop" 1440,900 "$BASE/?snapshot=1&consentpreview=program-unchanged#/programs"
shot "consent-program-unchanged-mobile" 390,844 "$BASE/?snapshot=1&consentpreview=program-unchanged#/programs"
shot "consent-program-narrowed-desktop" 1440,900 "$BASE/?snapshot=1&consentpreview=program-narrowed#/programs"
shot "consent-program-narrowed-mobile" 390,844 "$BASE/?snapshot=1&consentpreview=program-narrowed#/programs"
shot "consent-program-refusal-desktop" 1440,900 "$BASE/?snapshot=1&consentpreview=program-refusal#/programs"
shot "consent-program-refusal-mobile" 390,844 "$BASE/?snapshot=1&consentpreview=program-refusal#/programs"

# Real keyboard/semantic exam over the canonical ordinary, setup, bounded,
# repair, decision, recovery, and technical-inspection journeys.
python3 "$SCRIPT_DIR/workbench-accessibility.py" \
  --firefox "$FF" --base "$BASE" --suite core \
  --repository "$REPO" --capture-dir "${CAPTURE_DIR:-$TMP_ROOT}" \
  --capture-pattern "$CAPTURE_PATTERN" \
  || fail "core accessibility journey exam failed"

# Red-path prominence: the same overview must render a broken rail as
# attention while keeping execution behind deliberate-step review.
mv "$REPO/.githooks/pre-commit" "$REPO/.githooks/pre-commit.off"
shot "board-attention-desktop" 1440,900 "$BASE/?snapshot=1#/"
shot "board-attention-mobile" 390,844 "$BASE/?snapshot=1#/"
mv "$REPO/.githooks/pre-commit.off" "$REPO/.githooks/pre-commit"

# Ambiguity prominence: two healthy projects yield the manual
# select-project action; the briefing must not guess one.
"$PMO_DIR/bootstrap/new-project.sh" "$REPO" other "Other" OTH >/dev/null
shot "project-ambiguous-desktop" 1440,900 "$BASE/?snapshot=1#/"
shot "project-ambiguous-mobile" 390,844 "$BASE/?snapshot=1#/"
shot "project-selected-desktop" 1440,900 "$BASE/?snapshot=1&project=other#/board"
shot "project-selected-mobile" 390,844 "$BASE/?snapshot=1&project=other#/board"
# The newly selected project has no phases or cards, so keep an explicitly
# named board-home empty-state pair in the Phase-32 route/state matrix.
shot "board-empty-desktop" 1440,900 "$BASE/?snapshot=1&project=other#/board"
shot "board-empty-mobile" 390,844 "$BASE/?snapshot=1&project=other#/board"

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
"$PMO_DIR/bootstrap/new-project.sh" "$PROGRAM_REPO" selector-fixture "Selector fixture" SEL >/dev/null
PORT=$(( (RANDOM % 2000) + 23001 ))
"$PMO_DIR/bin/dw-workbench" --root "$PROGRAM_REPO" --port "$PORT" --quiet &
SERVER_PID=$!
i=0
until curl -sf "http://127.0.0.1:$PORT/api/programs" >/dev/null 2>&1; do
  i=$((i + 1)); [ "$i" -lt 40 ] || fail "program fixture server did not start"; sleep 0.25
done
BASE="http://127.0.0.1:$PORT"
PROGRAM_PROJECT="$(curl -s "$BASE/api/projects" | python3 -c 'import json,sys; print(next(p["slug"] for p in json.load(sys.stdin)["data"]["projects"] if p["slug"] != "selector-fixture"))')"
shot "program-active-desktop" 1440,900 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT#/programs/$PROGRAM_ACTIVE"
shot "program-active-mobile" 390,844 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT#/programs/$PROGRAM_ACTIVE"
shot "program-technical-desktop" 1440,900 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT&livetechnical=1#/programs/$PROGRAM_ACTIVE"
shot "program-technical-mobile" 390,844 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT&livetechnical=1#/programs/$PROGRAM_ACTIVE"
shot "program-revoked-desktop" 1440,900 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT#/programs/$PROGRAM_REVOKED"
shot "program-revoked-mobile" 390,844 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT#/programs/$PROGRAM_REVOKED"
shot "program-certified-desktop" 1440,900 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT#/programs/$PROGRAM_CERTIFIED"
shot "program-certified-mobile" 390,844 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT#/programs/$PROGRAM_CERTIFIED"
shot "program-remaining-limits-desktop" 1440,900 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT&boundedfocus=limits#/programs/$PROGRAM_ACTIVE"
shot "program-remaining-limits-mobile" 390,844 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT&boundedfocus=limits#/programs/$PROGRAM_ACTIVE"
shot "program-pause-preview-desktop" 1440,900 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT&boundedpreview=pause&boundedfocus=preview#/programs/$PROGRAM_ACTIVE"
shot "program-pause-preview-mobile" 390,844 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT&boundedpreview=pause&boundedfocus=preview#/programs/$PROGRAM_ACTIVE"
shot "program-stop-receipt-desktop" 1440,900 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT&boundedfocus=receipts#/programs/$PROGRAM_REVOKED"
shot "program-stop-receipt-mobile" 390,844 "$BASE/?snapshot=1&project=$PROGRAM_PROJECT&boundedfocus=receipts#/programs/$PROGRAM_REVOKED"

python3 "$SCRIPT_DIR/workbench-accessibility.py" \
  --firefox "$FF" --base "$BASE" --suite program \
  --program-active "$PROGRAM_ACTIVE" \
  --program-revoked "$PROGRAM_REVOKED" \
  --program-certified "$PROGRAM_CERTIFIED" \
  --project "$PROGRAM_PROJECT" \
  || fail "program accessibility journey exam failed"

RENDER_TOTAL=$((RENDER_DESKTOP_LIGHT + RENDER_DESKTOP_DARK + RENDER_MOBILE_LIGHT + RENDER_MOBILE_DARK))
if [ "$FAST_A11Y" = "1" ]; then
  echo "workbench-ui-smoke.sh: ok (fast accessibility-only mode; firefox-version='$FF_VERSION'; screenshots skipped by request)"
else
  [ "$RENDER_TOTAL" -eq "$EXPECTED_RENDER_COUNT" ] \
    || fail "required route/state matrix incomplete: expected $EXPECTED_RENDER_COUNT screenshots, produced $RENDER_TOTAL"
  for count in "$RENDER_DESKTOP_LIGHT" "$RENDER_DESKTOP_DARK" "$RENDER_MOBILE_LIGHT" "$RENDER_MOBILE_DARK"; do
    [ "$count" -gt 0 ] || fail "required viewport/theme screenshot bucket is empty"
  done
  echo "workbench-ui-smoke.sh: ok (firefox-version='$FF_VERSION'; $RENDER_TOTAL viewport renders; desktop-light=$RENDER_DESKTOP_LIGHT desktop-dark=$RENDER_DESKTOP_DARK mobile-light=$RENDER_MOBILE_LIGHT mobile-dark=$RENDER_MOBILE_DARK; board home, ideation, bounded-run consent, program consent, and eight-state Live matrix; 16 journey 6-13 wide/narrow keyboard/focus exams)"
fi
