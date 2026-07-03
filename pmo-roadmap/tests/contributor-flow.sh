#!/usr/bin/env bash
# Contributor flow (WLA-11-02).
#
# Proves docs/contribution-rails.md against real git behavior:
#
# Green: a contributor clone of an adopted upstream works one story
# through the gate on a branch, the PR-range verify (the required
# check) passes, a rebase merge lands it on a drifted upstream main,
# and full-history verification stays green with rewritten SHAs.
#
# Red 1: a two-flip branch squashed with GitHub-style message
# concatenation is refused by the maintainer's own local gate, and
# when forced with --no-verify the verifier names atomicity.
#
# Red 2: a single-flip branch with a fixup commit, squashed the same
# way, leaves the PMO trailers mid-body where git no longer parses
# them; the verifier names trailer-missing.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pmo-contrib-flow.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "contributor-flow.sh: $1" >&2
  exit 1
}

unset PMO_WORK_LOG_DIR PMO_WORK_LOG_ENABLED PMO_GATE_PYTHON 2>/dev/null || true

# ── upstream: adopted repo with a seeded roadmap ───────────────────
UP="$TMP_ROOT/upstream"
mkdir -p "$UP"
git -C "$UP" init -q -b main
git -C "$UP" config user.name "Maintainer"
git -C "$UP" config user.email "maintainer@example.test"
git -C "$UP" config receive.denyCurrentBranch ignore
"$PMO_DIR/install.sh" "$UP" --skip-bootstrap >/dev/null

PHASE_REL="pm/roadmap/demo/phase-1-alpha"
mkdir -p "$UP/$PHASE_REL"
cat > "$UP/pm/roadmap/demo/README.md" <<'EOF'
# Demo - Roadmap

**Last updated:** 2026-07-03.
**Current phase:** [phase-1-alpha](./phase-1-alpha/current-phase-status.md).
**Status:** active.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 1 | Ship the alpha | active | [phase-1-alpha](./phase-1-alpha/) |

## Project metadata

- **Slug:** `demo`
- **Story ID prefix:** DM
EOF
cat > "$UP/$PHASE_REL/current-phase-status.md" <<'EOF'
# Phase 1 - Alpha

**Last updated:** 2026-07-03.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DM-1-01 | Thing 1 | backlog | [story-01-thing-1](./story-01-thing-1.md) | - |
| DM-1-02 | Thing 2 | backlog | [story-02-thing-2](./story-02-thing-2.md) | - |
| DM-1-03 | Thing 3 | backlog | [story-03-thing-3](./story-03-thing-3.md) | - |
EOF
for n in 1 2 3; do
  cat > "$UP/$PHASE_REL/story-0$n-thing-$n.md" <<EOF
# DM-1-0$n - Thing $n

- **Project:** demo
- **Phase:** 1
- **Status:** backlog
EOF
done
git -C "$UP" add -A
git -C "$UP" commit -q --no-verify -m "fixture scaffold (pre-epoch)"

work_story() { # repo num
  local repo="$1" n="$2"
  (cd "$repo" \
    && ./.githooks/dw story status demo 1 "$n" in-progress >/dev/null \
    && ./.githooks/dw evidence capture demo 1 "$n" -- echo "proof-$n" >/dev/null \
    && ./.githooks/dw story status demo 1 "$n" "done" >/dev/null \
    && git add -A \
    && ./.githooks/dw contract new --force >/dev/null 2>&1 \
    && sed 's/^- \[ \]/- [x]/' .tmp/CONTRACT.md > .tmp/CONTRACT.md.new \
    && mv .tmp/CONTRACT.md.new .tmp/CONTRACT.md \
    && git commit -q -m "Complete DM-1-0$n: thing $n") \
    || fail "gated story $n failed in $repo"
}

# ── green: contributor clone, branch, gated story, PR verify ──────
CONTRIB="$TMP_ROOT/contributor"
git clone -q "$UP" "$CONTRIB"
git -C "$CONTRIB" config user.name "Contributor"
git -C "$CONTRIB" config user.email "contributor@example.test"
# Rails travel with the clone; pointing hooksPath at them is the one
# onboarding step (CONTRIBUTING documents it; dw doctor verifies it).
git -C "$CONTRIB" config core.hooksPath .githooks
(cd "$CONTRIB" && ./.githooks/dw doctor) >/dev/null || fail "contributor doctor not green"

git -C "$CONTRIB" switch -q -c feature/dm-1-01
work_story "$CONTRIB" 1
(cd "$CONTRIB" && ./.githooks/dw verify main..HEAD) >/dev/null \
  || fail "PR-range verify failed on the contributor branch"

# Upstream drifts while the PR is open (out-of-scope commit).
echo "drift" > "$UP/notes.txt"
git -C "$UP" add notes.txt
git -C "$UP" commit -q --no-verify -m "out-of-scope drift on main"

# Maintainer performs a rebase merge (replay + fast-forward, the
# same tree/message semantics as GitHub's rebase-and-merge button).
git -C "$UP" fetch -q "$CONTRIB" feature/dm-1-01:feature/dm-1-01
git -C "$UP" rebase -q main feature/dm-1-01 2>/dev/null || fail "rebase failed"
git -C "$UP" switch -q main
git -C "$UP" merge -q --ff-only feature/dm-1-01 || fail "ff merge failed"

(cd "$UP" && ./.githooks/dw verify --all) >/dev/null \
  || fail "main verify red after rebase merge (SHAs rewritten, trailers should survive)"
git -C "$UP" log -1 --format=%B | grep -q "^PMO-Contract-Digest:" \
  || fail "trailers lost in rebase merge"
echo "green path: ok (gated branch, PR-range verify, rebase merge, main verify green)"

# ── GitHub-style squash message: title + concatenated bodies ──────
github_squash() { # repo branch title
  local repo="$1" branch="$2" title="$3"
  local msg="$TMP_ROOT/squash-msg"
  {
    printf '%s (#1)\n\n' "$title"
    git -C "$repo" log --reverse --format='* %s%n%n%b' "main..$branch"
  } > "$msg"
  git -C "$repo" switch -q main
  git -C "$repo" merge -q --squash "$branch" >/dev/null
  echo "$msg"
}

# ── red 1: two flips squashed → local gate refuses; forced → atomicity ─
git -C "$UP" switch -q -c feature/two-flips
work_story "$UP" 2
work_story "$UP" 3
MSG="$(github_squash "$UP" feature/two-flips "Squash two stories")"
(cd "$UP" && ./.githooks/dw contract new --force >/dev/null 2>&1 \
  && sed 's/^- \[ \]/- [x]/' .tmp/CONTRACT.md > .tmp/CONTRACT.md.new \
  && mv .tmp/CONTRACT.md.new .tmp/CONTRACT.md)
if git -C "$UP" commit -q -F "$MSG" 2>/dev/null; then
  fail "the local gate accepted a two-flip squash commit"
fi
echo "red 1a: the maintainer's own gate refuses the two-flip squash"
git -C "$UP" commit -q --no-verify -F "$MSG"
set +e
OUT="$(cd "$UP" && ./.githooks/dw verify --all 2>&1)"
rc=$?
set -e
[ "$rc" = "1" ] || fail "verify should be red after forced squash, got $rc: $OUT"
echo "$OUT" | grep -q "atomicity" || fail "expected atomicity in: $OUT"
echo "red 1b: forced two-flip squash lands and dw verify names atomicity"
git -C "$UP" reset -q --hard HEAD~1
git -C "$UP" branch -q -D feature/two-flips

# ── red 2: one flip + fixup, squashed → trailers displaced mid-body ─
git -C "$UP" switch -q -c feature/one-flip-fixup
work_story "$UP" 2
echo "typo fix" >> "$UP/notes.txt"
git -C "$UP" add notes.txt
git -C "$UP" commit -q --no-verify -m "fixup: typo"
MSG="$(github_squash "$UP" feature/one-flip-fixup "Squash one story plus fixup")"
git -C "$UP" commit -q --no-verify -F "$MSG"
git -C "$UP" log -1 --format='%(trailers:key=PMO-Contract-Digest,valueonly)' | grep -q . \
  && fail "squash unexpectedly preserved a valid digest trailer"
set +e
OUT="$(cd "$UP" && ./.githooks/dw verify --all 2>&1)"
rc=$?
set -e
[ "$rc" = "1" ] || fail "verify should be red after fixup squash, got $rc: $OUT"
echo "$OUT" | grep -q "trailer-missing" || fail "expected trailer-missing in: $OUT"
echo "red 2: fixup squash displaces trailers mid-body and dw verify names trailer-missing"
git -C "$UP" reset -q --hard HEAD~1
git -C "$UP" branch -q -D feature/one-flip-fixup

(cd "$UP" && ./.githooks/dw verify --all) >/dev/null || fail "fixture not green after resets"

echo "contributor-flow.sh: ok"
