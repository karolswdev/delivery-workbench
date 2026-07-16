#!/usr/bin/env bash
# Smoke coverage for mid-project adoption discovery prompt generation.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pmo-adoption-test.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "adoption-discovery.sh: $1" >&2
  exit 1
}

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init >/dev/null
git -C "$REPO" config user.name "PMO Test"
git -C "$REPO" config user.email "pmo-test@example.test"
printf '%s\n' '# Existing App' > "$REPO/README.md"
git -C "$REPO" add README.md
git -C "$REPO" commit -m "initial" >/dev/null

PRIORITIES="$(printf '%s\n%s' "- [x] Create a durable handoff" "- [x] Reduce delivery risk")"
DELIVERABLES="$(printf '%s\n%s' "- [x] Immediate session plan" "- [x] Validation command list")"

"$PMO_DIR/bootstrap/session-intake.sh" "$REPO" \
  --project-name "Existing App" \
  --project-slug existing-app \
  --project-prefix EA \
  --mode "Delivery slice: identify and execute the next valuable change" \
  --priorities "$PRIORITIES" \
  --risk "Read-only until the plan is explicit" \
  --depth "Standard: repo map, commands, risks, first stories" \
  --deliverables "$DELIVERABLES" \
  --handoff-audience "Future agent" \
  --goal "Turn repo discovery into a first actionable roadmap" \
  --direction "Preserve current product behavior while adding PMO discipline" \
  --handoff "A future agent can pick the first story without session history" \
  --success "Session intake and discovery prompt exist with user intent" \
  --constraints "Do not invent product goals" \
  --context "This is an already-running project" \
  --agent-style "Read-only discovery first" \
  --questions "Which tests prove health?" \
  --no-prompt \
  >/dev/null

"$PMO_DIR/bootstrap/adopt-project.sh" "$REPO" \
  --project-name "Existing App" \
  --project-slug existing-app \
  --project-prefix EA \
  --require-intake \
  >/dev/null

PROMPT="$REPO/pm/roadmap/existing-app/adoption/adoption-discovery-prompt.md"
INTAKE="$REPO/pm/roadmap/existing-app/adoption/session-intake.md"
RESOLVED_REPO="$(git -C "$REPO" rev-parse --show-toplevel)"
[ -f "$INTAKE" ] || fail "session intake was not written"
[ -f "$PROMPT" ] || fail "adoption prompt was not written"
grep -q 'Turn repo discovery into a first actionable roadmap' "$INTAKE" || fail "session goal missing from intake"
grep -q 'Delivery slice' "$INTAKE" || fail "session mode missing from intake"
grep -q 'Create a durable handoff' "$INTAKE" || fail "priority checklist missing from intake"
grep -q 'Reduce delivery risk' "$INTAKE" || fail "multi-line priority checklist missing from intake"
grep -q 'Validation command list' "$INTAKE" || fail "multi-line deliverables checklist missing from intake"
grep -q 'Future agent' "$INTAKE" || fail "handoff audience missing from intake"
grep -q 'Existing App' "$PROMPT" || fail "project name missing from prompt"
grep -q 'existing-app' "$PROMPT" || fail "project slug missing from prompt"
grep -q 'EA' "$PROMPT" || fail "project prefix missing from prompt"
grep -q 'pm/roadmap/existing-app/adoption/session-intake.md' "$PROMPT" \
  || fail "repo-relative intake path missing from prompt"
if grep -qF "$RESOLVED_REPO" "$PROMPT"; then
  fail "prompt must not embed absolute machine paths"
fi
if grep -qF "$RESOLVED_REPO" "$INTAKE"; then
  fail "intake must not embed absolute machine paths"
fi
if grep -q 'most core intake answers were not provided' "$INTAKE"; then
  fail "fully-answered intake must not carry the unanswered banner"
fi

# ── intake right-sizing ───────────────────────────────────────────────
CORE_COUNT="$("$PMO_DIR/bootstrap/session-intake.sh" --list-questions | sed -n '/^core/,/^extended/p' | grep -c '^  [0-9]')"
[ "$CORE_COUNT" = "4" ] || fail "core interview should ask 4 questions (got $CORE_COUNT)"
TOTAL_COUNT="$("$PMO_DIR/bootstrap/session-intake.sh" --list-questions | grep -c '^  [0-9]')"
[ "$TOTAL_COUNT" = "14" ] || fail "extended interview should preserve all 14 questions (got $TOTAL_COUNT)"

"$PMO_DIR/bootstrap/session-intake.sh" "$REPO" \
  --project-slug blank-app --project-prefix BA --no-prompt >/dev/null
grep -q 'most core intake answers were not provided' \
  "$REPO/pm/roadmap/blank-app/adoption/session-intake.md" \
  || fail "blank-heavy intake should carry the unanswered banner"

# ── three-command adoption: install → discovery → dw adopt ───────────
"$PMO_DIR/install.sh" "$REPO" --skip-bootstrap >/dev/null
REPORT="$REPO/pm/roadmap/existing-app/adoption/adoption-discovery.md"
cat > "$REPORT" <<'EOF'
# Existing App - PMO Adoption Discovery

## PMO Adoption Recommendation
- **Roadmap root:** `pm/roadmap/existing-app/`

## Proposed Phase Index
| Phase | Title | Goal | Why now |
|---|---|---|---|
| 0 | Stabilize Build | Get the build green | Broken today |
| 1 | First Slice | Ship the first valuable change | Next value |

## Proposed First Stories
| ID | Title | Acceptance evidence | Notes |
|---|---|---|---|
| EA-0-01 | Fix the flaky suite | CI run output | - |
| EA-1-01 | Ship the slice | demo capture | - |
EOF
cd "$REPO"
.githooks/dw adopt --from-report "$REPORT" > "$TMP_ROOT/adopt-preview.txt" 2>&1 \
  || fail "dw adopt preview failed"
grep -q 'EA-0-01' "$TMP_ROOT/adopt-preview.txt" || fail "preview should list the stories"
[ ! -d pm/roadmap/existing-app/phase-0-stabilize-build ] \
  || fail "preview must not create files"
.githooks/dw adopt --from-report "$REPORT" --apply >/dev/null 2>&1 \
  || fail "dw adopt --apply failed"
[ -f pm/roadmap/existing-app/phase-0-stabilize-build/story-01-fix-the-flaky-suite.md ] \
  || fail "apply should scaffold the stories"
.githooks/dw check existing-app >/dev/null || fail "adopted roadmap should pass dw check"
.githooks/dw doctor >/dev/null || fail "three-command adoption should end with a healthy doctor"

# Malformed report: line-numbered refusal, no partial scaffold.
sed 's/| EA-1-01 | Ship the slice | demo capture | - |/| EA-9-01 | Ship the slice | demo capture | - |/' \
  "$REPORT" > "$TMP_ROOT/bad-report.md"
if .githooks/dw adopt --from-report "$TMP_ROOT/bad-report.md" --project existing-app2 --apply \
  >/dev/null 2>"$TMP_ROOT/adopt-err.txt"; then
  fail "malformed report should be refused"
fi
grep -q 'line' "$TMP_ROOT/adopt-err.txt" || fail "malformed-report error should be line-numbered"
[ ! -d pm/roadmap/existing-app2 ] || fail "malformed report must not leave a partial scaffold"
cd "$TMP_ROOT"

# ── idempotent reruns ────────────────────────────────────────────────
"$PMO_DIR/install.sh" "$REPO" --skip-bootstrap >/dev/null 2>&1
[ "$(grep -cxF '.tmp/' "$REPO/.gitignore")" = "1" ] || fail "rerunning install must not duplicate .gitignore entries"
[ "$(grep -c 'BEGIN DELIVERY WORKBENCH' "$REPO/CLAUDE.md")" = "1" ] || fail "rerunning install must not duplicate the agent-docs block"

# ── hostile project name renders literally ───────────────────────────
HOSTILE="$TMP_ROOT/hostile"
mkdir -p "$HOSTILE"
git -C "$HOSTILE" init >/dev/null
git -C "$HOSTILE" config user.name t
git -C "$HOSTILE" config user.email t@example.test
"$PMO_DIR/install.sh" "$HOSTILE" --project-name 'A|B & C\D' --project-slug hostile --project-prefix HX >/dev/null
grep -qF 'A|B & C\D' "$HOSTILE/pm/roadmap/hostile/README.md" \
  || fail "hostile project name should render literally"
python3 "$PMO_DIR/bin/dw" --root "$HOSTILE" check hostile >/dev/null \
  || fail "hostile-name scaffold should pass dw check"
if grep -rqF "$TMP_ROOT" "$HOSTILE/pm/roadmap"; then
  fail "scaffolded artifacts must not embed absolute machine paths"
fi

# ── installer honesty ────────────────────────────────────────────────
FOREIGN="$TMP_ROOT/foreign"
mkdir -p "$FOREIGN"
git -C "$FOREIGN" init >/dev/null
git -C "$FOREIGN" config core.hooksPath .husky
if "$PMO_DIR/install.sh" "$FOREIGN" --skip-bootstrap >/dev/null 2>&1; then
  fail "install should refuse to take over a foreign core.hooksPath without --force"
fi
git -C "$FOREIGN" config user.name t
git -C "$FOREIGN" config user.email t@example.test
"$PMO_DIR/install.sh" "$FOREIGN" --skip-bootstrap --force >/dev/null 2>&1 \
  || fail "install --force should take over after the operator decides"

LOCALHOOKS="$TMP_ROOT/localhooks"
mkdir -p "$LOCALHOOKS"
git -C "$LOCALHOOKS" init >/dev/null
git -C "$LOCALHOOKS" config user.name t
git -C "$LOCALHOOKS" config user.email t@example.test
printf '#!/bin/sh\nexit 0\n' > "$LOCALHOOKS/.git/hooks/pre-commit"
chmod +x "$LOCALHOOKS/.git/hooks/pre-commit"
"$PMO_DIR/install.sh" "$LOCALHOOKS" --skip-bootstrap 2>"$TMP_ROOT/warn.txt" >/dev/null
grep -q 'will disable' "$TMP_ROOT/warn.txt" \
  || fail "install should warn about active .git/hooks it disables"

# Self-hosting refresh must not scaffold a stray root pm/ tree, while
# a normal external install still ships the canon (WLA-8-05, friction
# entry 5).
SELFHOST="$TMP_ROOT/selfhost"
mkdir -p "$SELFHOST"
git -C "$SELFHOST" init >/dev/null
git -C "$SELFHOST" config user.name t
git -C "$SELFHOST" config user.email t@example.test
cp -R "$PMO_DIR" "$SELFHOST/pmo-roadmap"
OUT="$("$SELFHOST/pmo-roadmap/install.sh" "$SELFHOST" --skip-bootstrap 2>&1)"
echo "$OUT" | grep -q 'self-hosting refresh' \
  || fail "self-hosted install should announce the canon-scaffold skip"
[ ! -e "$SELFHOST/pm" ] \
  || fail "self-hosted install must not create a root pm/ tree"
UPDATE_OUT="$("$SELFHOST/pmo-roadmap/update.sh" "$SELFHOST" 2>&1)"
echo "$UPDATE_OUT" | grep -q 'self-hosting refresh' \
  || fail "self-hosted update should announce the canon-scaffold skip"
[ ! -e "$SELFHOST/pm" ] \
  || fail "self-hosted update must not create a shadow root pm/ tree"
[ -e "$FOREIGN/pm/roadmap/PMO-CONTRACT.md" ] \
  || fail "external install must still scaffold pm/roadmap canon"

# .mcp.json seam: created fresh, appended without clobbering, and an
# unparseable file is refused, never guessed at (WLA-10-04).
SEAM="$TMP_ROOT/mcp-seam"
mkdir -p "$SEAM/b" "$SEAM/c"
git -C "$SEAM/b" init >/dev/null
git -C "$SEAM/b" config user.name t
git -C "$SEAM/b" config user.email t@example.test
printf %s '{"mcpServers": {"other": {"command": "foo"}}}' > "$SEAM/b/.mcp.json"
"$PMO_DIR/install.sh" "$SEAM/b" --skip-bootstrap >/dev/null 2>&1
grep -q '"other"' "$SEAM/b/.mcp.json" \
  || fail ".mcp.json seam clobbered an existing server entry"
grep -q '"delivery-workbench"' "$SEAM/b/.mcp.json" \
  || fail ".mcp.json seam did not append the delivery-workbench entry"
git -C "$SEAM/c" init >/dev/null
git -C "$SEAM/c" config user.name t
git -C "$SEAM/c" config user.email t@example.test
printf %s "NOT-JSON{{{" > "$SEAM/c/.mcp.json"
"$PMO_DIR/install.sh" "$SEAM/c" --skip-bootstrap >/dev/null 2>&1
[ "$(cat "$SEAM/c/.mcp.json")" = "NOT-JSON{{{" ] \
  || fail ".mcp.json seam modified an unparseable file"
[ -x "$SEAM/b/.githooks/dw-mcp" ] || fail "install did not vendor dw-mcp"

echo "adoption-discovery.sh: ok"
