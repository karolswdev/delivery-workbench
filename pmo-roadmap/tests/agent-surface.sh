#!/usr/bin/env bash
# Agent-surface coverage (WLA-6-05): shipped slash commands, the managed
# CLAUDE.md/AGENTS.md block lifecycle (install/update/re-run), dw next
# exit contract, status vocabulary validation, dw doctor detections, the
# inline contract template in the blocked banner, work-log-read paging,
# and — the acceptance proof — a full story lifecycle driven headlessly
# with only the commands the agent docs name.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pmo-agent-surface.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "agent-surface.sh: $1" >&2
  exit 1
}

unset PMO_WORK_LOG_DIR 2>/dev/null || true
unset PMO_WORK_LOG_ENABLED 2>/dev/null || true

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init >/dev/null
git -C "$REPO" config user.name "Agent Surface"
git -C "$REPO" config user.email "agent-surface@example.test"

# Pre-existing user content must survive the managed block.
cat > "$REPO/CLAUDE.md" <<'EOF'
# My project notes

User content above the managed block.
EOF

"$PMO_DIR/install.sh" "$REPO" \
  --project-name "Demo" --project-slug demo --project-prefix DEMO >/dev/null
cd "$REPO"

# ── shipped commands + managed block (install) ───────────────────────
for cmd in dw-next dw-contract dw-story-done dw-adopt; do
  [ -f ".claude/commands/$cmd.md" ] || fail "install should ship .claude/commands/$cmd.md"
done
grep -q 'BEGIN DELIVERY WORKBENCH' CLAUDE.md || fail "install should write the managed block"
grep -q 'User content above the managed block.' CLAUDE.md || fail "install must not clobber user content"
[ "$(grep -c 'BEGIN DELIVERY WORKBENCH' CLAUDE.md)" = "1" ] || fail "exactly one managed block after install"

echo "User content below the managed block." >> CLAUDE.md
"$PMO_DIR/install.sh" "$REPO" --skip-bootstrap >/dev/null 2>&1 || true
[ "$(grep -c 'BEGIN DELIVERY WORKBENCH' CLAUDE.md)" = "1" ] || fail "re-running install must not duplicate the block"

# Corrupt the block; update.sh must restore it and keep user content.
sed 's/evidence-first commit gate/CORRUPTED LINE/' CLAUDE.md > CLAUDE.md.new && mv CLAUDE.md.new CLAUDE.md
.githooks/dw doctor 2>/dev/null | grep -q 'agent-docs.*stale' || fail "doctor should report a stale agent-docs block"
"$PMO_DIR/update.sh" "$REPO" >/dev/null 2>&1
grep -q 'evidence-first commit gate' CLAUDE.md || fail "update should restore the canonical block"
grep -q 'User content above the managed block.' CLAUDE.md || fail "update must keep user content above"
grep -q 'User content below the managed block.' CLAUDE.md || fail "update must keep user content below"
[ "$(grep -c 'BEGIN DELIVERY WORKBENCH' CLAUDE.md)" = "1" ] || fail "update must not duplicate the block"

# ── dw doctor detections ─────────────────────────────────────────────
.githooks/dw doctor >/dev/null || fail "doctor should be healthy after install"
git config --unset core.hooksPath
.githooks/dw doctor 2>/dev/null | grep -q 'FAIL  core.hooksPath' || fail "doctor should flag unset hooksPath"
if .githooks/dw doctor >/dev/null 2>&1; then fail "doctor should exit 1 when unhealthy"; fi
git config core.hooksPath .githooks
mv .githooks/commit-msg "$TMP_ROOT/commit-msg.bak"
.githooks/dw doctor 2>/dev/null | grep -q 'FAIL  hook:commit-msg' || fail "doctor should flag a missing hook"
mv "$TMP_ROOT/commit-msg.bak" .githooks/commit-msg
.githooks/dw doctor >/dev/null || fail "doctor should be healthy again"

# ── blocked banner contains the copy-pasteable template ──────────────
echo seed > seed.txt
git add seed.txt
BANNER="$TMP_ROOT/banner.txt"
if git commit -q -m "no contract" >/dev/null 2>"$BANNER"; then
  fail "commit without a contract should be blocked"
fi
# The docs-only staging makes auto-tier pick the short form, so the
# inline template carries the no-bypass box; the facts are still live.
grep -q -- '- \[ \] \*\*No bypasses\.\*\*' "$BANNER" \
  || fail "blocked banner should include the inline contract template boxes"
grep -q '\*\*Index-tree:\*\*' "$BANNER" \
  || fail "inline template should carry live stamped facts"

# ── full lifecycle, headless, commands-from-the-docs only ────────────
# (Acceptance: everything below appears in the managed CLAUDE.md block
# or the shipped slash commands; no framework source consulted.)
write_and_certify_contract() {
  .githooks/dw contract new --force "$@" >/dev/null 2>&1 || fail "contract new failed"
  sed 's/^- \[ \]/- [x]/' .tmp/CONTRACT.md > .tmp/CONTRACT.md.new
  mv .tmp/CONTRACT.md.new .tmp/CONTRACT.md
}

git add -A
write_and_certify_contract
git commit -q -m "seed repo" >/dev/null 2>&1 || fail "seed commit should pass the gate"

.githooks/dw story create demo phase-0-setup "Agent lifecycle story" >/dev/null \
  || fail "story create failed"
.githooks/dw next demo --json > "$TMP_ROOT/next.json" || fail "next should find the new story"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d['story_id']" "$TMP_ROOT/next.json" \
  || fail "next --json should emit a parseable story object"
STORY_ID="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['story_id'])" "$TMP_ROOT/next.json")"
.githooks/dw story status demo phase-0-setup "$STORY_ID" in-progress >/dev/null
if .githooks/dw story status demo phase-0-setup "$STORY_ID" done-ish >/dev/null 2>"$TMP_ROOT/status-err"; then
  fail "unknown status should be rejected"
fi
grep -q 'allowed: backlog, blocked' "$TMP_ROOT/status-err" \
  || fail "status rejection should name the allowed vocabulary"
.githooks/dw evidence capture demo phase-0-setup "$STORY_ID" -- sh -c 'echo lifecycle-verified' >/dev/null \
  || fail "evidence capture failed"
.githooks/dw story status demo phase-0-setup "$STORY_ID" done >/dev/null || fail "flip to done failed"
git add -A
write_and_certify_contract --tests-capture "$(find pm/roadmap/demo -name 'evidence-story-*.md' | sed -n '1p')"
git commit -q -m "ship agent lifecycle story" >/dev/null 2>&1 || fail "gated ship commit failed"
git log -1 --format='%(trailers:key=PMO-Story,valueonly)' | grep -q "$STORY_ID" \
  || fail "shipped commit should carry the PMO-Story trailer"
.githooks/dw check demo >/dev/null || fail "check should pass after the lifecycle"

# Exercise the exit-2 contract: flip every remaining actionable story
# to blocked (a valid open status that next does not schedule).
while .githooks/dw next demo --json > "$TMP_ROOT/drain.json" 2>/dev/null; do
  REMAINING="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['story_id'])" "$TMP_ROOT/drain.json")"
  .githooks/dw story status demo phase-0-setup "$REMAINING" blocked >/dev/null
done
if .githooks/dw next demo >/dev/null 2>&1; then
  fail "next should exit nonzero when nothing is actionable"
fi
set +e
.githooks/dw next demo >/dev/null 2>&1
NEXT_EXIT=$?
set -e
[ "$NEXT_EXIT" = "2" ] || fail "next should exit 2 when nothing is actionable (got $NEXT_EXIT)"
.githooks/dw next demo --json | grep -q '"next_story": null' \
  || fail "next --json should emit an explicit null when nothing is actionable"

# ── work-log-read paging ──────────────────────────────────────────────
LOG_FIXTURE="$TMP_ROOT/long.log"
i=0
while [ $i -lt 30 ]; do echo "line-$i" >> "$LOG_FIXTURE"; i=$((i+1)); done
.githooks/dw >/dev/null 2>&1 || true
[ "$(.githooks/work-log-read --log-file "$LOG_FIXTURE" | wc -l | tr -d ' ')" = "30" ] \
  || fail "work-log-read should print full files by default"
.githooks/work-log-read --log-file "$LOG_FIXTURE" --max-lines 5 | grep -q 'PMO_WORK_LOG_READ_TRUNCATED' \
  || fail "work-log-read --max-lines should mark truncation explicitly"

echo "agent-surface.sh: ok"
