#!/usr/bin/env bash
# Claude Code plugin validation (WLA-7-04): manifests parse and agree,
# declared files exist, the version single-sources from dw_pmo, and —
# when the claude CLI is available — its own validator passes too.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"

fail() {
  echo "plugin-validate.sh: $1" >&2
  exit 1
}

python3 - "$REPO" <<'PY' || fail "manifest checks failed"
import json, sys
from pathlib import Path

repo = Path(sys.argv[1])
sys.path.insert(0, str(repo / "pmo-roadmap" / "lib"))
import dw_pmo

manifest = json.loads((repo / "plugin/.claude-plugin/plugin.json").read_text())
assert manifest["name"] == "delivery-workbench", manifest
assert manifest["version"] == dw_pmo.__version__, (
    f"plugin version {manifest['version']} != dw_pmo {dw_pmo.__version__}")
assert manifest["license"] == "MIT"

marketplace = json.loads((repo / ".claude-plugin/marketplace.json").read_text())
entry = marketplace["plugins"][0]
assert entry["name"] == "delivery-workbench"
assert (repo / entry["source"]).is_dir(), entry["source"]

skill = repo / "plugin/skills/delivery-workbench/SKILL.md"
assert skill.is_file()
head = skill.read_text().split("---")[1]
assert "name: delivery-workbench" in head
assert "description:" in head

for name in ("dw-next", "dw-contract", "dw-story-done", "dw-adopt"):
    assert (repo / f"plugin/commands/{name}.md").is_file(), name

print("plugin manifests: ok (version", manifest["version"] + ", 4 commands, 1 skill)")
PY

if command -v claude >/dev/null 2>&1; then
  claude plugin validate "$REPO/plugin" >/dev/null || fail "claude plugin validate rejected the plugin"
  echo "claude plugin validate: ok"
else
  echo "claude CLI unavailable: manifest checks only (validator runs where claude exists)"
fi

echo "plugin-validate.sh: ok"
