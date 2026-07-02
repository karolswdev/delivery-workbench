#!/usr/bin/env bash
# Gate parity coverage (WLA-6-02).
#
# Runs the same staged fixtures through the installed pre-commit shim
# (via real `git commit`) and through `dw gate` directly, asserting the
# verdicts match and equal the expected outcome — including the fixed
# drift-bug family: synonym statuses, unpadded numbering, evidence
# deletions, renames of done stories, paths with spaces, and capital-X
# checkboxes. Also proves the pre-commit.config / pre-commit.local
# seams keep working, the python3 fail-closed path, and the unified
# PMO_WORK_LOG_DIR precedence (config > environment > default).

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pmo-gate-parity.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "gate-parity.sh: $1" >&2
  exit 1
}

unset PMO_WORK_LOG_DIR 2>/dev/null || true
unset PMO_WORK_LOG_ENABLED 2>/dev/null || true
unset EXPECTED_BOXES 2>/dev/null || true
unset PMO_GATE_PYTHON 2>/dev/null || true

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init >/dev/null
git -C "$REPO" config user.name "Gate Parity"
git -C "$REPO" config user.email "gate-parity@example.test"
"$PMO_DIR/install.sh" "$REPO" --skip-bootstrap >/dev/null
cd "$REPO"

PHASE="pm/roadmap/demo/phase-1-alpha"
mkdir -p "$PHASE"

write_contract() { # [boxes] [mark] [consent]
  boxes="${1:-7}"
  mark="${2:-x}"
  consent="${3:-no}"
  mkdir -p .tmp
  {
    echo "# Commit Contract"
    echo
    i=1
    while [ "$i" -le "$boxes" ]; do
      echo "- [$mark] rule $i"
      i=$((i + 1))
    done
    echo
    echo "**Work-log consent:** $consent"
    echo
    echo "**Work-log reasons:**"
    echo "- parity harness"
    echo
    echo "**Work-log exclusions:**"
    echo "- none"
  } > .tmp/CONTRACT.md
}

write_story() { # path status
  printf '# Story\n\n- **Status:** %s\n' "$2" > "$1"
}

tweak() {
  echo "tweak $1" >> README.md
  git add README.md
}

reset_state() {
  git reset --hard HEAD >/dev/null 2>&1 || true
  git clean -fdq pm >/dev/null 2>&1 || true
  rm -rf .tmp
}

check_parity() { # expected(pass|fail) name
  expected="$1"
  name="$2"
  if .githooks/dw gate --porcelain >/dev/null 2>&1; then GATE=pass; else GATE=fail; fi
  if git commit -q -m "$name" >/dev/null 2>&1; then SHIM=pass; else SHIM=fail; fi
  [ "$GATE" = "$SHIM" ] || fail "$name: verdict mismatch (gate=$GATE, shim=$SHIM)"
  [ "$GATE" = "$expected" ] || fail "$name: expected $expected, got $GATE"
}

# S0 — base commit through the gate (no flips).
echo "seed" > README.md
write_story "$PHASE/story-01-first.md" "ready"
write_story "$PHASE/story-02-second.md" "ready"
git add -A
write_contract
check_parity pass "base"

# S1 — happy single flip with paired evidence.
write_story "$PHASE/story-01-first.md" "done"
echo "# proof" > "$PHASE/evidence-story-01.md"
git add -A
write_contract
check_parity pass "single flip"

# S2 — synonym status flip without evidence is blocked (bypass fixed).
write_story "$PHASE/story-02-second.md" "complete"
git add -A
write_contract
check_parity fail "synonym flip without evidence"
reset_state

# S3a — unpadded story number pairs with padded evidence.
write_story "$PHASE/story-3-unpadded.md" "done"
echo "# proof" > "$PHASE/evidence-story-03.md"
git add -A
write_contract
check_parity pass "unpadded story, padded evidence"

# S3b — unpadded evidence pairs with the story number.
write_story "$PHASE/story-4-also-unpadded.md" "done"
echo "# proof" > "$PHASE/evidence-story-4.md"
git add -A
write_contract
check_parity pass "unpadded evidence"

# S4 — rename of an already-done story is not a flip.
git mv "$PHASE/story-01-first.md" "$PHASE/story-01-renamed.md"
write_contract
check_parity pass "rename of done story"

# S5 — story path containing a space.
write_story "$PHASE/story-05-has space.md" "done"
echo "# proof" > "$PHASE/evidence-story-05.md"
git add -A
write_contract
check_parity pass "path with spaces"

# S6 — capital-X checkboxes count as checked.
tweak capital-x
write_contract 7 X
check_parity pass "capital-X checkboxes"

# S7 — unchecked box blocks.
tweak unchecked
write_contract 7 " "
check_parity fail "unchecked boxes"
reset_state

# S8 — missing contract blocks.
tweak no-contract
rm -rf .tmp
check_parity fail "missing contract"
reset_state

# S9 — multi-flip requires BUNDLE-OK.
write_story "$PHASE/story-06-bundle-a.md" "done"
write_story "$PHASE/story-07-bundle-b.md" "done"
echo "# proof" > "$PHASE/evidence-story-06.md"
echo "# proof" > "$PHASE/evidence-story-07.md"
git add -A
write_contract
check_parity fail "multi-flip without bundle"
write_contract
echo "intentional bundle for parity harness" > .tmp/BUNDLE-OK.md
check_parity pass "multi-flip with BUNDLE-OK"

# S10 — deleting evidence that orphans a done story is blocked.
git rm -q "$PHASE/evidence-story-01.md"
write_contract
check_parity fail "evidence deletion orphaning done story"
reset_state

# S11 — deleting evidence while regressing the story passes.
git rm -q "$PHASE/evidence-story-01.md"
write_story "$PHASE/story-01-renamed.md" "in-progress"
git add "$PHASE/story-01-renamed.md"
write_contract
check_parity pass "evidence deletion with regressed story"

# S12 — added orphan evidence is blocked.
echo "# stray" > "$PHASE/evidence-story-09.md"
git add "$PHASE/evidence-story-09.md"
write_contract
check_parity fail "added orphan evidence"
reset_state

# S13 — pre-commit.config seam: EXPECTED_BOXES=8 applies to shim AND gate.
cat > .githooks/pre-commit.config <<'EOF'
EXPECTED_BOXES=8
EOF
tweak config-seam-under
write_contract 7
check_parity fail "config seam: 7 boxes under EXPECTED_BOXES=8"
write_contract 8
check_parity pass "config seam: 8 boxes"
rm -f .githooks/pre-commit.config

# S14 — pre-commit.local seam: local rules still block and see gate context.
cat > .githooks/pre-commit.local <<'EOF'
if [ -f "$REPO_ROOT/block-me" ]; then
  fail "local rule blocked this commit"
fi
printf '%s\n' "$SHIPPED_COUNT" > "$REPO_ROOT/.local-seam-observed"
EOF
touch block-me
tweak local-seam-blocked
write_contract
if git commit -q -m "local seam blocked" >/dev/null 2>&1; then
  fail "pre-commit.local rule should block the commit"
fi
rm -f block-me
write_contract
git commit -q -m "local seam passes" >/dev/null 2>&1 || fail "commit should pass once local rule is satisfied"
[ -f .local-seam-observed ] || fail "pre-commit.local should see gate context variables"
grep -Eq '^[0-9]+$' .local-seam-observed || fail "SHIPPED_COUNT should be numeric in the local seam"
rm -f .local-seam-observed .githooks/pre-commit.local

# S15 — python3 missing: the shim fails closed with a clear message.
tweak fail-closed
write_contract
if PMO_GATE_PYTHON=/nonexistent/python3 git commit -q -m "no python" >/dev/null 2>"$TMP_ROOT/py-err"; then
  fail "commit should fail closed when python3 is unavailable"
fi
grep -q "python3 is required" "$TMP_ROOT/py-err" || fail "fail-closed message should name the python3 dependency"
reset_state

# S16 — PMO_WORK_LOG_DIR from the environment reaches hooks and readers alike.
cat > .githooks/pre-commit.config <<'EOF'
PMO_WORK_LOG_ENABLED=1
PMO_WORK_LOG_PROJECT_SLUG=demo
EOF
ENV_LOG="$TMP_ROOT/env-log"
tweak env-log-dir
write_contract 7 x yes
PMO_WORK_LOG_DIR="$ENV_LOG" git commit -q -m "env log dir" >/dev/null 2>&1 \
  || fail "consented commit with env log dir should pass"
LOG_FILE="$(find "$ENV_LOG/$(date +%F)" -type f -name '*-work-summary.log' 2>/dev/null | sed -n '1p')"
[ -n "$LOG_FILE" ] || fail "post-commit should write the log under the env PMO_WORK_LOG_DIR"
PMO_WORK_LOG_DIR="$ENV_LOG" .githooks/work-log-read --date "$(date +%F)" --list \
  | grep -q "$(basename "$LOG_FILE")" || fail "work-log-read should list logs from the env PMO_WORK_LOG_DIR"
PMO_WORK_LOG_DIR="$ENV_LOG" .githooks/dw context --compact 2>/dev/null \
  | grep -q "env-log" || fail "dw context should read work logs from the env PMO_WORK_LOG_DIR"
rm -f .githooks/pre-commit.config

echo "gate-parity.sh: ok"
