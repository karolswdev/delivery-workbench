#!/usr/bin/env bash
# Canon lint (WLA-6-06): no canonical framework surface may carry
# author-personal content — private memory paths, machine paths, the
# extracted worked-example project, or placeholder links. The
# templates/examples/ directory is the designated quarantine for
# illustrative material and is excluded; the dogfood roadmap under
# pm/roadmap/ is grandfathered history, not canon.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT="$(cd "$PMO_DIR/.." && pwd)"

fail=0

SURFACES="
$PMO_DIR/README.md
$ROOT/README.md
$PMO_DIR/install.sh
$PMO_DIR/update.sh
$PMO_DIR/hooks
$PMO_DIR/bin
$PMO_DIR/lib
$PMO_DIR/agent
$PMO_DIR/bootstrap
"

TEMPLATE_FILES="$(find "$PMO_DIR/templates" -maxdepth 1 -type f 2>/dev/null)"

# shellcheck disable=SC2088  # literal grep pattern, not a path expansion
PATTERNS='~/.claude
reusable-processes
[Pp]antrybot
pantry-life
feedback_
MEMORY\.md
\]\(https://github\.com/\)'

check() {
  target="$1"
  [ -e "$target" ] || return 0
  while IFS= read -r pattern; do
    [ -n "$pattern" ] || continue
    if matches="$(grep -rn -E -e "$pattern" "$target" 2>/dev/null)"; then
      echo "canon-lint: forbidden pattern '$pattern' in canonical surface:" >&2
      printf '%s\n' "$matches" | sed 's/^/  /' >&2
      fail=1
    fi
  done <<EOF
$PATTERNS
EOF
}

for surface in $SURFACES; do
  check "$surface"
done
for file in $TEMPLATE_FILES; do
  check "$file"
done

if [ "$fail" -ne 0 ]; then
  echo "canon-lint.sh: FAILED — personal or placeholder content in canonical surfaces." >&2
  exit 1
fi

echo "canon-lint.sh: ok"
