#!/usr/bin/env bash
# Regenerates assets/social-preview.png (1280x640, GitHub's recommended
# social-preview geometry): composes a self-contained HTML card — the
# repo icon, name, tagline, and the delivery loop — and screenshots it
# with headless Firefox (same harness as the workbench captures). With
# --smoke the render goes to a temp directory instead — CI-safe: the
# committed asset is never touched, and a missing Firefox skips cleanly.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/dw-social-preview.XXXXXX")"

SMOKE=0
if [ "${1:-}" = "--smoke" ]; then
  SMOKE=1
fi

cleanup() { rm -rf "$TMP_ROOT"; }
trap cleanup EXIT

fail() {
  echo "render-social-preview.sh: $1" >&2
  exit 1
}

FF=""
for candidate in \
  "/Applications/Firefox.app/Contents/MacOS/firefox" \
  "$(command -v firefox 2>/dev/null || true)"; do
  [ -n "$candidate" ] && [ -x "$candidate" ] && FF="$candidate" && break
done
if [ -z "$FF" ]; then
  if [ "$SMOKE" -eq 1 ]; then
    echo "render-social-preview.sh: SKIP (no Firefox available for headless rendering)"
    exit 0
  fi
  fail "no Firefox available for headless rendering"
fi

if [ "$SMOKE" -eq 1 ]; then
  OUT_DIR="$TMP_ROOT/assets"
else
  OUT_DIR="$REPO_ROOT/assets"
fi
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/social-preview.png"

ICON_B64="$(base64 < "$REPO_ROOT/pmo-roadmap/assets/delivery-workbench-icon.png" | tr -d '\n')"

PAGE="$TMP_ROOT/card.html"
cat > "$PAGE" <<EOF
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { width: 1280px; height: 640px; overflow: hidden; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background:
      radial-gradient(ellipse 900px 600px at 85% -10%, #1e3a5f 0%, transparent 60%),
      radial-gradient(ellipse 700px 500px at -5% 110%, #14352b 0%, transparent 55%),
      #0d1117;
    color: #e6edf3;
    display: flex;
    align-items: center;
    padding: 0 88px;
  }
  .card { display: flex; align-items: center; gap: 64px; width: 100%; }
  .icon img { width: 240px; height: 240px; border-radius: 44px;
    box-shadow: 0 24px 64px rgba(0,0,0,.55); display: block; }
  h1 { font-size: 74px; font-weight: 700; letter-spacing: -1.5px; }
  .tagline { font-size: 30px; color: #9db4c9; margin-top: 14px;
    font-weight: 400; }
  .loop { margin-top: 34px; font-family: "SF Mono", Menlo, Consolas, monospace;
    font-size: 23px; color: #7ee2a8; }
  .loop .dim { color: #58708a; }
</style>
</head>
<body>
  <div class="card">
    <div class="icon"><img src="data:image/png;base64,${ICON_B64}" alt=""></div>
    <div>
      <h1>Delivery Workbench</h1>
      <div class="tagline">Evidence-first rails for agentic software delivery.</div>
      <div class="loop">plan <span class="dim">&rarr;</span> prove <span class="dim">&rarr;</span> contract <span class="dim">&rarr;</span> commit <span class="dim">&rarr;</span> trace</div>
    </div>
  </div>
</body>
</html>
EOF

profile="$(mktemp -d)"
"$FF" --headless --no-remote --profile "$profile" \
  --screenshot "$OUT" --window-size=1280,640 "file://$PAGE" >/dev/null 2>&1 &
ffpid=$!
waited=0
while [ ! -s "$OUT" ] && [ "$waited" -lt 30 ]; do sleep 1; waited=$((waited + 1)); done
sleep 1
kill "$ffpid" 2>/dev/null || true
wait "$ffpid" 2>/dev/null || true
rm -rf "$profile"

[ -s "$OUT" ] || fail "no screenshot produced"
size=$(wc -c < "$OUT" | tr -d ' ')
[ "$size" -gt 20000 ] || fail "render appears empty (only $size bytes)"

echo "render-social-preview.sh: ok"
echo "  $OUT"
