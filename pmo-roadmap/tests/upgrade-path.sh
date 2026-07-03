#!/usr/bin/env bash
# Consumer upgrade path (WLA-9-03).
#
# Adopts a fixture repo with the REAL v1.5.0 rails (git archive of the
# tag), ships gated commits there, then upgrades to the current source
# via update.sh and proves: staleness was visible before (--check exit
# 3) and gone after (exit 0); the rails gained dw verify and it passes
# over the mixed-version history; roadmap content, pre-commit.config,
# and pre-commit.local are byte-untouched; and the gate still ships a
# story after the refresh.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT="$(cd "$PMO_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pmo-upgrade-path.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "upgrade-path.sh: $1" >&2
  exit 1
}

unset PMO_WORK_LOG_DIR PMO_WORK_LOG_ENABLED PMO_GATE_PYTHON 2>/dev/null || true

git -C "$ROOT" rev-parse -q --verify "v1.5.0^{commit}" >/dev/null \
  || { echo "upgrade-path.sh: skip (no v1.5.0 tag in this clone)"; exit 0; }

# ── v1.5.0 rails from the real tag ─────────────────────────────────
OLD_SRC="$TMP_ROOT/old"
mkdir -p "$OLD_SRC"
git -C "$ROOT" archive v1.5.0 pmo-roadmap | tar -x -C "$OLD_SRC"
[ -x "$OLD_SRC/pmo-roadmap/install.sh" ] || fail "archived install.sh not executable"
[ ! -f "$OLD_SRC/pmo-roadmap/lib/dw_pmo/verify.py" ] \
  || fail "v1.5.0 unexpectedly ships verify.py — fixture premise broken"

REPO="$TMP_ROOT/consumer"
mkdir -p "$REPO"
git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Upgrade Path"
git -C "$REPO" config user.email "upgrade-path@example.test"
"$OLD_SRC/pmo-roadmap/install.sh" "$REPO" --skip-bootstrap >/dev/null
cd "$REPO"

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

gated_commit() { # message
  .githooks/dw contract new --force >/dev/null 2>&1 || fail "contract new failed"
  sed 's/^- \[ \]/- [x]/' .tmp/CONTRACT.md > .tmp/CONTRACT.md.new
  mv .tmp/CONTRACT.md.new .tmp/CONTRACT.md
  git commit -q -m "$1" || fail "gated commit failed: $1"
}

# Project seam customization that upgrades must never touch.
printf '# consumer rule seam — do not clobber\n' > .githooks/pre-commit.local
printf '\n# consumer marker\n' >> .githooks/pre-commit.config

# Two gated commits on the OLD rails (trailers from the v1.5.0 gate).
write_story 1 backlog
git add -A
gated_commit "Plan DM-1-01 on v1.5.0 rails"
write_story 1 "done"
cat > "$PHASE/evidence-story-01.md" <<EOF
# Evidence - DM-1-01

- **Status:** done
EOF
git add -A
gated_commit "Complete DM-1-01 on v1.5.0 rails"

# Old rails must not know dw verify; staleness must be visible.
if .githooks/dw verify --all >/dev/null 2>&1; then
  fail "v1.5.0 rails unexpectedly support dw verify"
fi
set +e
"$PMO_DIR/update.sh" "$REPO" --check >/dev/null
check_rc=$?
set -e
[ "$check_rc" = "3" ] || fail "expected --check exit 3 (stale), got $check_rc"

# ── snapshot protected content, then upgrade ───────────────────────
SNAP="$TMP_ROOT/snap"
mkdir -p "$SNAP"
cp -R "$REPO/pm/roadmap/demo" "$SNAP/demo"
cp .githooks/pre-commit.config "$SNAP/pre-commit.config"
cp .githooks/pre-commit.local "$SNAP/pre-commit.local"

"$PMO_DIR/update.sh" "$REPO" >/dev/null 2>&1 || fail "update.sh failed"

# ── refreshed rails, untouched project ─────────────────────────────
[ -f .githooks/dw_pmo/verify.py ] || fail "upgrade did not deliver verify.py"
[ -x .githooks/dw-mcp ] || fail "upgrade did not deliver dw-mcp"
"$PMO_DIR/update.sh" "$REPO" --check >/dev/null \
  || fail "expected --check exit 0 after upgrade"
diff -r "$SNAP/demo" "$REPO/pm/roadmap/demo" >/dev/null \
  || fail "upgrade touched pm/roadmap/demo content"
cmp -s "$SNAP/pre-commit.config" .githooks/pre-commit.config \
  || fail "upgrade touched pre-commit.config"
cmp -s "$SNAP/pre-commit.local" .githooks/pre-commit.local \
  || fail "upgrade touched pre-commit.local"

# Mixed-version history verifies clean with the new verifier.
.githooks/dw verify --all >/dev/null || fail "dw verify failed on mixed-version history"

# ── the gate still ships a story on the refreshed rails ────────────
write_story 2 backlog
git add -A
gated_commit "Plan DM-1-02 on refreshed rails"
write_story 2 "done"
cat > "$PHASE/evidence-story-02.md" <<EOF
# Evidence - DM-1-02

- **Status:** done
EOF
git add -A
gated_commit "Complete DM-1-02 on refreshed rails"

.githooks/dw verify --all >/dev/null || fail "dw verify failed after post-upgrade commits"
git log -1 --format=%B | grep -q "PMO-Contract-Digest:" \
  || fail "post-upgrade commit lacks digest trailer"

echo "upgrade-path.sh: ok"
