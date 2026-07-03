#!/usr/bin/env bash
# Range-verifier coverage (WLA-8-02).
#
# Builds fixture histories and asserts `dw verify` verdicts against
# the remote verification contract (docs/remote-verification.md):
# a clean gated history passes; a smuggled --no-verify flip fails
# with evidence-missing and trailer-missing; a double-flip without a
# PMO-Bundle trailer fails atomicity while the same flip with the
# trailer (via .tmp/BUNDLE-OK.md through the real commit-msg hook)
# passes; orphan evidence and evidence deletions are caught; a wrong
# PMO-Story trailer fails contract-story-mismatch; pre-epoch commits
# are skipped, never flagged; and a shallow clone exits 2.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pmo-verify-range.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "verify-range.sh: $1" >&2
  exit 1
}

unset PMO_WORK_LOG_DIR 2>/dev/null || true
unset PMO_WORK_LOG_ENABLED 2>/dev/null || true
unset PMO_GATE_PYTHON 2>/dev/null || true

REPO="$TMP_ROOT/repo"
mkdir -p "$REPO"
git -C "$REPO" init -b main >/dev/null
git -C "$REPO" config user.name "Verify Range"
git -C "$REPO" config user.email "verify-range@example.test"
"$PMO_DIR/install.sh" "$REPO" --skip-bootstrap >/dev/null
cd "$REPO"

DW=.githooks/dw
PHASE="pm/roadmap/demo/phase-1-alpha"
mkdir -p "$PHASE"

write_story() { # num status
  cat > "$PHASE/story-0$1-thing-$1.md" <<EOF
# DM-1-0$1 - Thing $1

- **Project:** demo
- **Phase:** 1
- **Status:** $2
EOF
}

write_evidence() { # num
  cat > "$PHASE/evidence-story-0$1.md" <<EOF
# Evidence - DM-1-0$1

- **Status:** done
EOF
}

gated_commit() { # message
  "$DW" contract new --force >/dev/null 2>&1 || fail "contract new failed"
  sed 's/^- \[ \]/- [x]/' .tmp/CONTRACT.md > .tmp/CONTRACT.md.new
  mv .tmp/CONTRACT.md.new .tmp/CONTRACT.md
  git commit -q -m "$1" || fail "gated commit failed: $1"
}

expect_verify() { # expected_exit label args...
  expected="$1"; label="$2"; shift 2
  set +e
  OUT="$("$DW" verify "$@" 2>&1)"
  code=$?
  set -e
  [ "$code" = "$expected" ] || fail "$label: expected exit $expected, got $code: $OUT"
}

expect_rule() { # rule label
  echo "$OUT" | grep -q "ERROR [0-9a-f]*: $1:" || fail "$2: expected rule $1 in: $OUT"
}

# ── Pre-epoch history: raw commits with no trailers at all ─────────
write_story 1 backlog
git add -A
git commit -q --no-verify -m "pre-epoch: scaffold without rails"
write_story 1 in-progress
git add -A
git commit -q --no-verify -m "pre-epoch: still without rails"

# ── Epoch begins: clean gated flip (real hooks stamp trailers) ─────
write_story 1 done
write_evidence 1
git add -A
gated_commit "Complete DM-1-01"

expect_verify 0 "clean history" --all
echo "$OUT" | grep -q "1 commits verified, 2 pre-epoch skipped" \
  || fail "epoch scoping: expected 1 verified / 2 skipped in: $OUT"

# ── Smuggled flip: --no-verify, no evidence, no trailers ───────────
write_story 2 backlog
git add -A
gated_commit "Plan DM-1-02"
write_story 2 done
git add -A
git commit -q --no-verify -m "smuggled: flip without gate"

expect_verify 1 "smuggled flip" --all
expect_rule "trailer-missing" "smuggled flip"
expect_rule "evidence-missing" "smuggled flip"
git reset -q --hard HEAD~1

# ── Double flip without bundle trailer ─────────────────────────────
write_story 3 backlog
write_story 4 backlog
git add -A
gated_commit "Plan DM-1-03 DM-1-04"
write_story 3 done
write_evidence 3
write_story 4 done
write_evidence 4
git add -A
git commit -q --no-verify -m "smuggled: double flip

PMO-Story: DM-1-03, DM-1-04
PMO-Contract-Digest: sha256:0000000000000000000000000000000000000000000000000000000000000000"

expect_verify 1 "double flip without bundle" --all
expect_rule "atomicity" "double flip without bundle"
git reset -q --hard HEAD~1

# ── Same double flip, bundled via BUNDLE-OK → PMO-Bundle trailer ───
write_story 3 done
write_evidence 3
write_story 4 done
write_evidence 4
git add -A
mkdir -p .tmp
echo "Bundling 03+04: twin stories proven by one run" > .tmp/BUNDLE-OK.md
gated_commit "Complete DM-1-03 and DM-1-04 (bundled)"
git log -1 --format=%B | grep -q "^PMO-Bundle: Bundling 03+04" \
  || fail "bundle trailer: commit-msg hook did not stamp PMO-Bundle"

expect_verify 0 "bundled double flip" --all

# ── Wrong PMO-Story trailer on a flip ──────────────────────────────
write_story 5 backlog
git add -A
gated_commit "Plan DM-1-05"
write_story 5 done
write_evidence 5
git add -A
git commit -q --no-verify -m "smuggled: flip declaring the wrong story

PMO-Story: DM-1-99
PMO-Contract-Digest: sha256:1111111111111111111111111111111111111111111111111111111111111111"

expect_verify 1 "story mismatch" --all
expect_rule "contract-story-mismatch" "story mismatch"
git reset -q --hard HEAD~1

# ── Orphan evidence: appears with no flip ──────────────────────────
write_evidence 6
git add -A
git commit -q --no-verify -m "smuggled: orphan evidence

PMO-Contract-Digest: sha256:2222222222222222222222222222222222222222222222222222222222222222"

expect_verify 1 "orphan evidence" --all
expect_rule "orphan-evidence" "orphan evidence"
git reset -q --hard HEAD~1

# ── Evidence deletion that orphans a done story ────────────────────
git rm -q "$PHASE/evidence-story-01.md"
git commit -q --no-verify -m "smuggled: delete evidence under a done story

PMO-Contract-Digest: sha256:3333333333333333333333333333333333333333333333333333333333333333"

expect_verify 1 "evidence deletion" --all
expect_rule "evidence-deletion-orphans-story" "evidence deletion"
git reset -q --hard HEAD~1

# ── Malformed trailer values ───────────────────────────────────────
write_story 5 in-progress
git add -A
git commit -q --no-verify -m "smuggled: bad digest format

PMO-Contract-Digest: sha256:tooshort"

expect_verify 1 "malformed digest" --all
expect_rule "trailer-format" "malformed digest"
git reset -q --hard HEAD~1

# ── Porcelain output ───────────────────────────────────────────────
"$DW" verify --all --porcelain | grep -q "^verify=pass" \
  || fail "porcelain: expected verify=pass"
"$DW" verify --all --porcelain | grep -q "^epoch=" \
  || fail "porcelain: expected epoch= line"

# ── Explicit range and usage errors ────────────────────────────────
expect_verify 0 "explicit range" "HEAD~1..HEAD"
expect_verify 2 "bad range" "no-such-rev..HEAD"
expect_verify 2 "range plus --all" "HEAD~1..HEAD" --all

# ── Pinned epoch overrides auto-detection ──────────────────────────
ROOT_SHA="$(git rev-list --max-parents=0 HEAD)"
set +e
OUT="$("$DW" verify --all --epoch "$ROOT_SHA" 2>&1)"
code=$?
set -e
[ "$code" = "1" ] || fail "pinned epoch: pre-epoch commits have no trailers, expected exit 1, got $code: $OUT"
echo "$OUT" | grep -q "trailer-missing" || fail "pinned epoch: expected trailer-missing in: $OUT"

# ── Shallow clone fails loudly ─────────────────────────────────────
SHALLOW="$TMP_ROOT/shallow"
git clone -q --depth 1 "file://$REPO" "$SHALLOW" 2>/dev/null
cp -R "$REPO/.githooks" "$SHALLOW/.githooks" 2>/dev/null || true
set +e
OUT="$(cd "$SHALLOW" && ./.githooks/dw verify --all 2>&1)"
code=$?
set -e
[ "$code" = "2" ] || fail "shallow clone: expected exit 2, got $code: $OUT"
echo "$OUT" | grep -qi "shallow" || fail "shallow clone: expected shallow message in: $OUT"

echo "verify-range.sh: ok"
