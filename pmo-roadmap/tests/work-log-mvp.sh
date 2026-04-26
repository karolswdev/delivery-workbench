#!/usr/bin/env bash
# Integration coverage for pmo-roadmap work-log MVP hooks.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pmo-work-log-test.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "work-log-mvp.sh: $1" >&2
  exit 1
}

assert_eq() {
  actual="$1"
  expected="$2"
  msg="$3"
  if [ "$actual" != "$expected" ]; then
    fail "$msg (expected $expected, got $actual)"
  fi
}

entry_count() {
  if [ -f "$LOG_FILE" ]; then
    grep -c '^kind: pmo-work-log-entry$' "$LOG_FILE" 2>/dev/null || true
  else
    echo 0
  fi
}

write_contract() {
  consent="$1"
  mkdir -p .tmp
  cat > .tmp/CONTRACT.md <<EOF
# Commit Contract

**Generated:** 2026-04-25 00:00
**Branch:** test
**Staged files (sample):**
- app.txt

I certify, for this commit:

- [x] **Evidence, not vibes.** Test harness evidence.
- [x] **Master docs updated.** n/a - harness commit.
- [x] **Tests ran.** work-log-mvp.sh is the test.
- [x] **Greenfield discipline (if applicable).** n/a - harness repo.
- [x] **No bypasses.** No bypass.
- [x] **Story → evidence pairing.** n/a - no story done flip.
- [x] **One PR per story.** n/a - harness commit.

Methodology: pm/roadmap/roadmap-builder.md
Rules canon: pm/roadmap/PMO-CONTRACT.md

## Work-log consent

**Work-log consent:** $consent

**Work-log reasons:**
- Harness commit with consent $consent.

**Work-log exclusions:**
- none
EOF
}

REPO="$TMP_ROOT/repo"
LOG_ROOT="$TMP_ROOT/work-log"
mkdir -p "$REPO"
git -C "$REPO" init >/dev/null
git -C "$REPO" config user.name "PMO Test"
git -C "$REPO" config user.email "pmo-test@example.test"

"$PMO_DIR/install.sh" "$REPO" --project-name "Demo" --project-slug demo --project-prefix DEMO >/dev/null
cd "$REPO"
[ -x .githooks/work-log-summarize ] || fail "install should write work-log-summarize helper"
[ -x .githooks/work-log-read ] || fail "install should write work-log-read helper"

cat > .githooks/pre-commit.config <<EOF
PMO_WORK_LOG_ENABLED=1
PMO_WORK_LOG_PROJECT_SLUG=demo
PMO_WORK_LOG_DIR='$LOG_ROOT'
PMO_WORK_LOG_EXCLUDE_REGEX='^secrets/'
EOF

git add .
write_contract no
git commit -m "initial framework" >/dev/null
assert_eq "$(find "$LOG_ROOT" -type f 2>/dev/null | wc -l | tr -d ' ')" "0" "denied initial consent should not write logs"

echo "one" > app.txt
git add app.txt
write_contract yes
git commit -m "add app file" >/dev/null

LOG_FILE="$(find "$LOG_ROOT/$(date +%F)" -type f -name '*-work-summary.log' | sed -n '1p')"
[ -n "$LOG_FILE" ] || fail "consented commit did not write a work log"
assert_eq "$(entry_count)" "1" "first consented commit should write one entry"
[ ! -f .git/pmo-work-log/pending ] || fail "pending payload should be removed after post-commit"
grep -q '^summary_mode: deterministic$' "$LOG_FILE" || fail "log entry should be deterministic"
grep -q 'Harness commit with consent yes' "$LOG_FILE" || fail "consent reasons should be preserved"
.githooks/work-log-read --log-file "$LOG_FILE" | grep -q '^kind: pmo-work-log-entry$' || fail "reader should print log content"
.githooks/work-log-read --date "$(date +%F)" --log-dir "$LOG_ROOT" --list | grep -q "$(basename "$LOG_FILE")" || fail "reader should list daily log"

.githooks/work-log-summarize --log-file "$LOG_FILE" --command "awk '/^Source log:/ {print \"Deferred summary for \" \$0; exit}'" >/dev/null
DIGEST_FILE="${LOG_FILE%-work-summary.log}-deferred-summary.md"
[ -f "$DIGEST_FILE" ] || fail "deferred summarizer should write companion digest"
grep -q '^kind: pmo-work-log-deferred-summary$' "$DIGEST_FILE" || fail "digest should have schema marker"
grep -q '^Deferred summary for Source log:' "$DIGEST_FILE" || fail "digest should include fake summarizer output"
if .githooks/work-log-summarize --log-file "$LOG_FILE" --command "cat" >/dev/null 2>&1; then
  :
fi
grep -q '^Deferred summary for Source log:' "$DIGEST_FILE" || fail "existing digest should not be overwritten without --force"
if .githooks/work-log-summarize --log-file "$LOG_FILE" --force --timeout-seconds 1 --command "sleep 3" >/dev/null 2>&1; then
  fail "deferred summarizer should fail on timeout"
fi
grep -q '^Deferred summary for Source log:' "$DIGEST_FILE" || fail "timeout should not replace existing digest"

mkdir -p secrets
echo "not-for-log" > secrets/token.txt
echo "public two" >> app.txt
git add app.txt secrets/token.txt
write_contract yes
git commit -m "excluded secret path" >/dev/null
assert_eq "$(entry_count)" "2" "excluded-path commit should append one entry"
grep -q 'Omitted Paths' "$LOG_FILE" || fail "log should include omitted paths section"
grep -q '`secrets/token.txt`' "$LOG_FILE" || fail "log should name omitted path"
if grep -q 'not-for-log' "$LOG_FILE"; then
  fail "excluded file content should not appear in final log"
fi
if grep -q '| A | `secrets/token.txt` |' "$LOG_FILE"; then
  fail "excluded path should not appear in files changed table"
fi

echo "two" >> app.txt
git add app.txt
write_contract no
git commit -m "denied work log" >/dev/null
assert_eq "$(entry_count)" "2" "denied consent should not append"

.githooks/post-commit >/dev/null
assert_eq "$(entry_count)" "2" "manual post-commit rerun should not duplicate without pending"

echo "abort" >> app.txt
git add app.txt
write_contract yes
if GIT_EDITOR=false git commit >/dev/null 2>&1; then
  fail "editor-aborted commit unexpectedly succeeded"
fi
assert_eq "$(entry_count)" "2" "aborted commit should not append"
[ -f .git/pmo-work-log/pending ] || fail "aborted commit should leave pending payload for overwrite"

echo "after abort" >> app.txt
git add app.txt
write_contract yes
git commit -m "commit after abort" >/dev/null
assert_eq "$(entry_count)" "3" "commit after aborted attempt should append one new entry"
[ ! -f .git/pmo-work-log/pending ] || fail "pending payload should be cleaned after overwrite/finalize"

echo "amend" >> app.txt
git add app.txt
write_contract yes
git commit --amend -m "commit after abort amended" >/dev/null
assert_eq "$(entry_count)" "4" "amend should append according to MVP policy"

printf '%s\n' '#!/usr/bin/env bash' 'echo custom update hook' > .githooks/post-commit
chmod +x .githooks/post-commit
"$PMO_DIR/update.sh" "$REPO" >/dev/null 2>&1
grep -q 'custom update hook' .githooks/post-commit || fail "update should preserve existing non-framework post-commit without --force"

COLLISION_REPO="$TMP_ROOT/collision"
mkdir -p "$COLLISION_REPO/.githooks"
git -C "$COLLISION_REPO" init >/dev/null
printf '%s\n' '#!/usr/bin/env bash' 'echo custom' > "$COLLISION_REPO/.githooks/post-commit"
chmod +x "$COLLISION_REPO/.githooks/post-commit"
if "$PMO_DIR/install.sh" "$COLLISION_REPO" >/dev/null 2>&1; then
  fail "install should refuse to overwrite existing non-framework post-commit"
fi

echo "work-log-mvp.sh: ok"
