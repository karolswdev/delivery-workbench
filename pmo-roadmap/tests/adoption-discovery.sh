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

"$PMO_DIR/bootstrap/adopt-project.sh" "$REPO" \
  --project-name "Existing App" \
  --project-slug existing-app \
  --project-prefix EA \
  >/dev/null

PROMPT="$REPO/pm/roadmap/existing-app/adoption/adoption-discovery-prompt.md"
RESOLVED_REPO="$(git -C "$REPO" rev-parse --show-toplevel)"
[ -f "$PROMPT" ] || fail "adoption prompt was not written"
grep -q 'Existing App' "$PROMPT" || fail "project name missing from prompt"
grep -q 'existing-app' "$PROMPT" || fail "project slug missing from prompt"
grep -q 'EA' "$PROMPT" || fail "project prefix missing from prompt"
grep -q "$RESOLVED_REPO" "$PROMPT" || fail "target path missing from prompt"

echo "adoption-discovery.sh: ok"
