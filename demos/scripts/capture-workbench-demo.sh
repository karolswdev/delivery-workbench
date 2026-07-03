#!/usr/bin/env bash
# Regenerates the workbench visual assets from current sources:
#   demos/rendered/workbench-tour.gif   animated explore -> health -> trace
#                                       -> guarded-edit tour
#   assets/workbench-overview.png       README still: project overview
#   assets/workbench-trace.png          README still: intent-to-proof trace
#   assets/workbench-editor.png         README still: guarded editor preview
#
# The capture drives a throwaway fixture repo through bin/dw, serves it
# with bin/dw-workbench, and screenshots the live UI via headless Firefox
# (same harness as tests/workbench-ui-smoke.sh). With --smoke the full
# capture runs into a temp directory instead — CI-safe: committed assets
# are never touched, and missing Firefox/ImageMagick skip cleanly.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PMO_DIR="$REPO_ROOT/pmo-roadmap"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/dw-workbench-demo.XXXXXX")"
SERVER_PID=""

SMOKE=0
if [ "${1:-}" = "--smoke" ]; then
  SMOKE=1
fi

cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "capture-workbench-demo.sh: $1" >&2
  exit 1
}

skip_or_fail() {
  if [ "$SMOKE" -eq 1 ]; then
    echo "capture-workbench-demo.sh: SKIP ($1)"
    exit 0
  fi
  fail "$1"
}

FF=""
for candidate in \
  "/Applications/Firefox.app/Contents/MacOS/firefox" \
  "$(command -v firefox 2>/dev/null || true)"; do
  [ -n "$candidate" ] && [ -x "$candidate" ] && FF="$candidate" && break
done
[ -n "$FF" ] || skip_or_fail "no Firefox available for headless rendering"

MAGICK=""
for candidate in "$(command -v magick 2>/dev/null || true)" \
  "$(command -v convert 2>/dev/null || true)"; do
  [ -n "$candidate" ] && [ -x "$candidate" ] && MAGICK="$candidate" && break
done
[ -n "$MAGICK" ] || skip_or_fail "no ImageMagick available for GIF assembly"

if [ "$SMOKE" -eq 1 ]; then
  GIF_DIR="$TMP_ROOT/rendered"
  STILL_DIR="$TMP_ROOT/assets"
else
  GIF_DIR="$REPO_ROOT/demos/rendered"
  STILL_DIR="$REPO_ROOT/assets"
fi
mkdir -p "$GIF_DIR" "$STILL_DIR"

# ── fixture: a small but lifelike roadmap ────────────────────────────
FIXTURE="$TMP_ROOT/repo"
PROJECT="$FIXTURE/pm/roadmap/demo-app"
mkdir -p "$PROJECT"
cat > "$PROJECT/README.md" <<'EOF'
# Demo App - Roadmap

**Current phase:** n/a.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|

## Project metadata

- **Slug:** `demo-app`
- **Story ID prefix:** `DEMO`
EOF
DW="$PMO_DIR/bin/dw"
"$DW" --root "$FIXTURE" phase create demo-app 1 "Delivery Rails" \
  --goal "Wire the evidence-first commit gate into the demo app." >/dev/null
"$DW" --root "$FIXTURE" story create demo-app 1 "Wire the commit gate" >/dev/null
"$DW" --root "$FIXTURE" story status demo-app 1 DEMO-1-01 "done" \
  --evidence-body "- Gate refused the uncontracted commit, then passed with a certified contract (captured run)." >/dev/null
"$DW" --root "$FIXTURE" story create demo-app 1 "Capture evidence for the API" >/dev/null
"$DW" --root "$FIXTURE" story status demo-app 1 DEMO-1-02 in-progress >/dev/null

PORT=$(( (RANDOM % 2000) + 23000 ))
"$PMO_DIR/bin/dw-workbench" --root "$FIXTURE" --port "$PORT" --quiet &
SERVER_PID=$!
i=0
until curl -sf "http://127.0.0.1:$PORT/api/projects" >/dev/null 2>&1; do
  i=$((i + 1)); [ "$i" -lt 40 ] || fail "server did not start"; sleep 0.25
done
BASE="http://127.0.0.1:$PORT"

shot() { # out-path url
  out="$1"
  profile="$(mktemp -d)"
  "$FF" --headless --no-remote --profile "$profile" \
    --screenshot "$out" --window-size=1440,900 "$2" >/dev/null 2>&1 &
  ffpid=$!
  waited=0
  while [ ! -s "$out" ] && [ "$waited" -lt 30 ]; do sleep 1; waited=$((waited + 1)); done
  sleep 1
  kill "$ffpid" 2>/dev/null || true
  wait "$ffpid" 2>/dev/null || true
  rm -rf "$profile"
  [ -s "$out" ] || fail "no screenshot produced for $out"
  size=$(wc -c < "$out" | tr -d ' ')
  [ "$size" -gt 20000 ] || fail "$out appears unrendered (only $size bytes)"
}

# ── tour frames: explore -> health -> trace -> guarded edit ──────────
FRAMES="$TMP_ROOT/frames"
mkdir -p "$FRAMES"
shot "$FRAMES/1-overview.png" "$BASE/?snapshot=1#/"
shot "$FRAMES/2-project.png" "$BASE/?snapshot=1#/p/demo-app"
shot "$FRAMES/3-health.png" "$BASE/?snapshot=1#/health"
shot "$FRAMES/4-trace.png" "$BASE/?snapshot=1#/p/demo-app/t/DEMO-1-01"
shot "$FRAMES/5-editor.png" "$BASE/?snapshot=1#/edit/create_story"
shot "$FRAMES/6-preview.png" "$BASE/?snapshot=1&autopreview=1#/edit/attach_evidence"

"$MAGICK" -delay 250 -loop 0 \
  "$FRAMES/1-overview.png" "$FRAMES/2-project.png" "$FRAMES/3-health.png" \
  "$FRAMES/4-trace.png" "$FRAMES/5-editor.png" "$FRAMES/6-preview.png" \
  -resize 1100x -layers Optimize "$GIF_DIR/workbench-tour.gif"
[ -s "$GIF_DIR/workbench-tour.gif" ] || fail "GIF assembly produced nothing"

# ── curated README stills ────────────────────────────────────────────
cp "$FRAMES/2-project.png" "$STILL_DIR/workbench-overview.png"
cp "$FRAMES/4-trace.png" "$STILL_DIR/workbench-trace.png"
cp "$FRAMES/6-preview.png" "$STILL_DIR/workbench-editor.png"

echo "capture-workbench-demo.sh: ok"
echo "  $GIF_DIR/workbench-tour.gif"
echo "  $STILL_DIR/workbench-overview.png"
echo "  $STILL_DIR/workbench-trace.png"
echo "  $STILL_DIR/workbench-editor.png"
