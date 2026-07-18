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
run = app[app.index("function runStateBadge"):app.index("/* ── router")]
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
assert '/api/status' in overview and '/api/step' in overview and "Promise.all" in overview
assert "overflow-wrap: anywhere" in css
assert ".step-confirmation" in css and ".brief-step-unavailable" in css
assert "@media (max-width: 430px)" in css
for token in ("live run · ledger replay", "fail checks", "failure routes",
              "human checkpoints", "hash-chained receipts",
              "confirm this exact act", "no automatic continuation",
              "close explicit stream"):
    assert token in run, token
assert "setInterval" not in run and "driver_config" not in run and "argv:" not in run
assert 'aria-labelledby="run-graph-title"' in run
assert "@media (max-width: 520px)" in css and ".run-node.state-active" in css
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
python3 - "$REPO/pm/orchestration/repair-visual.json" "$REPO/pm/orchestration/terminal-visual.json" <<'PY'
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
for path, document in zip(sys.argv[1:], (repair, terminal)):
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

VIEWS="overview:#/ step-confirm:#/ health:#/health trace:#/p/sample/t/SMP-0-01 editor:#/edit/create_story preview:#/edit/attach_evidence validation:#/p/sample board:#/board/sample orchestration-design:#/orchestration/research-build-review orchestration-validate:#/orchestration/research-build-review orchestration-json:#/orchestration/research-build-review orchestration-run-active:#/orchestration/research-build-review orchestration-run-repair:#/orchestration/repair-visual orchestration-run-terminal:#/orchestration/terminal-visual"
for spec in $VIEWS; do
  name="${spec%%:*}"
  route="${spec#*:}"
  extra=""
  case "$name" in
    preview) extra="&autopreview=1" ;;
    step-confirm) extra="&confirmstep=1" ;;
    orchestration-validate) extra="&orchview=validate" ;;
    orchestration-json) extra="&orchview=json" ;;
    orchestration-run-*) extra="&orchview=run" ;;
  esac
  shot "$name-desktop" 1440,900 "$BASE/?snapshot=1$extra$route"
  shot "$name-mobile" 390,844 "$BASE/?snapshot=1$extra$route"
done

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

echo "workbench-ui-smoke.sh: ok (32 viewport renders: 14 views + attention + ambiguity, desktop+mobile)"
