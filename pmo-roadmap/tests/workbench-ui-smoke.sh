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
}

VIEWS="overview:#/ health:#/health trace:#/p/sample/t/SMP-0-01 editor:#/edit/create_story preview:#/edit/attach_evidence validation:#/p/sample"
for spec in $VIEWS; do
  name="${spec%%:*}"
  route="${spec#*:}"
  extra=""
  case "$name" in preview) extra="&autopreview=1" ;; esac
  shot "$name-desktop" 1440,900 "$BASE/?snapshot=1$extra$route"
  shot "$name-mobile" 390,844 "$BASE/?snapshot=1$extra$route"
done

echo "workbench-ui-smoke.sh: ok (12 viewport renders: 6 views x desktop+mobile)"
