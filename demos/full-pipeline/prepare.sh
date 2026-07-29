#!/bin/bash
# Stage the full-pipeline ceremony demo in /tmp/dw-ceremony-demo.
#
# The tapes in this directory record against that stage. Requirements:
#   - `dw` on PATH (or DW_BIN pointing at one) with the front-door verbs
#   - a validated local driver roster in the framework repo's
#     .git/pmo-orchestration/drivers.json (desk-local, non-secret;
#     see docs/riders.md) — the stage copies it for the demo repo
#   - claude + codex CLIs authenticated (the live segment dispatches both)
set -euo pipefail

STAGE=/tmp/dw-ceremony-demo
HERE=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$HERE/../.." && pwd)
DW_BIN=${DW_BIN:-$(command -v dw || true)}
[ -n "$DW_BIN" ] || { echo "prepare.sh: dw not found on PATH (set DW_BIN)"; exit 1; }
ROSTER=${DW_ROSTER:-$REPO_ROOT/.git/pmo-orchestration/drivers.json}
[ -f "$ROSTER" ] || { echo "prepare.sh: no driver roster at $ROSTER (set DW_ROSTER)"; exit 1; }

rm -rf "$STAGE"
mkdir -p "$STAGE/assets"
cp "$HERE/assets/answers.json" "$STAGE/assets/answers.json"
cp "$HERE/assets/setup-proposal.json" "$STAGE/assets/setup-proposal.json"
cp "$ROSTER" "$STAGE/assets/drivers.json"

cat > "$STAGE/env.sh" <<EOF
export PATH="$(dirname "$DW_BIN"):\$PATH"
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NODE_EXTRA_CA_CERTS ALL_PROXY all_proxy 2>/dev/null || true
export PS1='\[\e[38;5;213m\]ceremony\[\e[0m\] \[\e[38;5;245m\]\W\[\e[0m\] \$ '
cd "$STAGE"
EOF

echo "staged $STAGE (dw: $DW_BIN)"
