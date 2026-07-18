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
    case "$1" in
      $CAPTURE_PATTERN)
        mkdir -p "$CAPTURE_DIR"
        cp "$out" "$CAPTURE_DIR/$1.png"
        ;;
    esac
  fi
}

VIEWS="overview:#/ step-confirm:#/ health:#/health trace:#/p/sample/t/SMP-0-01 editor:#/edit/create_story preview:#/edit/attach_evidence validation:#/p/sample board:#/board/sample orchestration-design:#/orchestration/research-build-review orchestration-validate:#/orchestration/research-build-review orchestration-json:#/orchestration/research-build-review"
for spec in $VIEWS; do
  name="${spec%%:*}"
  route="${spec#*:}"
  extra=""
  case "$name" in
    preview) extra="&autopreview=1" ;;
    step-confirm) extra="&confirmstep=1" ;;
    orchestration-validate) extra="&orchview=validate" ;;
    orchestration-json) extra="&orchview=json" ;;
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

echo "workbench-ui-smoke.sh: ok (26 viewport renders: 11 views + attention + ambiguity, desktop+mobile)"
