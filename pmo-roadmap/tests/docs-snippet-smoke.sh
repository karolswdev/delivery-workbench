#!/usr/bin/env bash
# Docs snippet smoke (WLA-7-06): every quickstart block marked
# "<!-- snippet: name … -->" is extracted and executed as printed
# (placeholder paths substituted, throwaway fixture per snippet) and
# must exit 0. A quickstart that no longer runs verbatim fails CI with
# a greppable "ERROR <file>: snippet '<name>' …" line.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT="$(cd "$PMO_DIR/.." && pwd)"

PYTHONPATH="$PMO_DIR/lib" python3 -m dw_pmo.docslint --snippets --root "$ROOT"

echo "docs-snippet-smoke.sh: ok"
