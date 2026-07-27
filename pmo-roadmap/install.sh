#!/usr/bin/env bash
# pmo-roadmap install — drop the framework into a target git project.
# Idempotent. Refuses to overwrite methodology/contract without --force.

set -eu

usage() {
  cat <<EOF
Usage: $0 <target-dir> [options]

Installs the pmo-roadmap framework into <target-dir>:
  - copies templates/roadmap-builder.md   → pm/roadmap/roadmap-builder.md
  - copies templates/PMO-CONTRACT.md      → pm/roadmap/PMO-CONTRACT.md
  - seeds ordinary orchestration presets  → pm/orchestration/*.json
  - copies hooks/pre-commit               → .githooks/pre-commit (chmod +x)
  - copies hooks/commit-msg               → .githooks/commit-msg (chmod +x)
  - copies hooks/post-commit              → .githooks/post-commit (chmod +x)
  - copies bin/dw                         → .githooks/dw
  - copies lib/dw_pmo/                    → .githooks/dw_pmo/
  - copies bin/dw-workbench + workbench/  → .githooks/ (local web UI)
  - copies bin/work-log-summarize         → .githooks/work-log-summarize
  - copies bin/work-log-read              → .githooks/work-log-read
  - copies bin/dw-mcp                     → .githooks/dw-mcp (MCP stdio server)
  - adds a delivery-workbench entry to .mcp.json (append-only)
  - copies agent/dw-*.md                  → .claude/commands/ (slash commands)
  - writes the managed Delivery Workbench block into CLAUDE.md/AGENTS.md
  - sets git config core.hooksPath .githooks
  - adds .tmp/ and Python runtime caches to .gitignore (if missing)
  - optionally scaffolds pm/roadmap/<slug>/ skeleton

Options:
  --project-name "Name"     Human project name (e.g. "My Project")
  --project-slug slug       Kebab slug (e.g. "myproject")
  --project-prefix PFX      Story-ID prefix (e.g. "MP")
  --skip-bootstrap          Don't scaffold pm/roadmap/<slug>/
  --no-agent-docs           Don't write the managed CLAUDE.md/AGENTS.md block
  --force                   Overwrite existing methodology/contract and
                            framework-owned hook collisions

If --project-slug is given, scaffolds pm/roadmap/<slug>/ with a project
README and phase-0-setup/ skeleton. Without --project-slug, only the
framework files are installed.
EOF
}

die() { echo "install.sh: $1" >&2; exit 1; }

TARGET=""
PROJECT_NAME=""
PROJECT_SLUG=""
PROJECT_PREFIX=""
SKIP_BOOTSTRAP=0
AGENT_DOCS=1
FORCE=0

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --project-name) PROJECT_NAME="$2"; shift 2 ;;
    --project-slug) PROJECT_SLUG="$2"; shift 2 ;;
    --project-prefix) PROJECT_PREFIX="$2"; shift 2 ;;
    --skip-bootstrap) SKIP_BOOTSTRAP=1; shift ;;
    --no-agent-docs) AGENT_DOCS=0; shift ;;
    --force) FORCE=1; shift ;;
    --) shift; break ;;
    -*) die "unknown option: $1" ;;
    *)
      if [ -z "$TARGET" ]; then TARGET="$1"; else die "unexpected arg: $1"; fi
      shift ;;
  esac
done

[ -n "$TARGET" ] || { usage; exit 1; }
[ -d "$TARGET" ] || die "target directory does not exist: $TARGET"

# Resolve to absolute path, portably.
TARGET="$(cd "$TARGET" && pwd)"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd -P)"

# Verify target is a git repo.
git -C "$TARGET" rev-parse --show-toplevel >/dev/null 2>&1 \
  || die "not a git repo: $TARGET"
TARGET="$(git -C "$TARGET" rev-parse --show-toplevel)"

echo "→ Installing pmo-roadmap into $TARGET"

# Self-hosting refresh: when the framework source lives inside the
# target repo (this repository refreshing its own .githooks snapshot),
# the canon already lives under the source tree — scaffolding a second
# pm/roadmap/ at the target root would just leave a stray tree to
# delete by hand (adoption friction entry 5, WLA-8-05).
SELF_HOSTED=0
case "$SOURCE_DIR" in
  "$TARGET"/*) SELF_HOSTED=1 ;;
esac

# 1. Methodology + contract
copy_template() {
  src="$1"; dst="$2"
  if [ -e "$dst" ] && [ "$FORCE" -ne 1 ]; then
    echo "  · skip (exists, use --force to overwrite): ${dst#"$TARGET"/}"
  else
    cp "$src" "$dst"
    echo "  ✓ wrote ${dst#"$TARGET"/}"
  fi
}
if [ "$SELF_HOSTED" -eq 1 ]; then
  echo "  · self-hosting refresh (source inside target); skipping pm/roadmap canon scaffold"
else
  mkdir -p "$TARGET/pm/roadmap"
  copy_template "$SOURCE_DIR/templates/roadmap-builder.md" "$TARGET/pm/roadmap/roadmap-builder.md"
  copy_template "$SOURCE_DIR/templates/PMO-CONTRACT.md"    "$TARGET/pm/roadmap/PMO-CONTRACT.md"
  mkdir -p "$TARGET/pm/orchestration"
  for preset in "$SOURCE_DIR"/templates/orchestration/*.json; do
    [ -f "$preset" ] || continue
    copy_template "$preset" "$TARGET/pm/orchestration/$(basename "$preset")"
  done
fi

# 2. Hooks — refuse to clobber a foreign hook manager silently.
EXISTING_HOOKS_PATH="$(git -C "$TARGET" config core.hooksPath 2>/dev/null || true)"
if [ -n "$EXISTING_HOOKS_PATH" ] && [ "$EXISTING_HOOKS_PATH" != ".githooks" ] && [ "$FORCE" -ne 1 ]; then
  die "core.hooksPath is already '$EXISTING_HOOKS_PATH' (another hook manager?); re-run with --force to take over, after deciding how to preserve that behavior"
fi
ACTIVE_LOCAL_HOOKS="$(find "$TARGET/.git/hooks" -maxdepth 1 -type f ! -name '*.sample' 2>/dev/null | sed "s|^$TARGET/||" || true)"
if [ -n "$ACTIVE_LOCAL_HOOKS" ]; then
  echo "  ! note: .git/hooks contains active hooks that core.hooksPath=.githooks will disable:" >&2
  printf '%s\n' "$ACTIVE_LOCAL_HOOKS" | sed 's/^/      /' >&2
fi

mkdir -p "$TARGET/.githooks"
PRE_COMMIT_DST="$TARGET/.githooks/pre-commit"
PRE_COMMIT_SRC="$SOURCE_DIR/hooks/pre-commit"
if [ -e "$PRE_COMMIT_DST" ] && ! cmp -s "$PRE_COMMIT_DST" "$PRE_COMMIT_SRC" && [ "$FORCE" -ne 1 ] \
  && ! grep -q "pmo-roadmap pre-commit" "$PRE_COMMIT_DST" 2>/dev/null; then
  die "existing .githooks/pre-commit is not a pmo-roadmap hook; refusing to overwrite without --force"
fi
cp "$PRE_COMMIT_SRC" "$PRE_COMMIT_DST"
chmod +x "$PRE_COMMIT_DST"
echo "  ✓ wrote .githooks/pre-commit"

POST_COMMIT_DST="$TARGET/.githooks/post-commit"
POST_COMMIT_SRC="$SOURCE_DIR/hooks/post-commit"
if [ -e "$POST_COMMIT_DST" ] && ! cmp -s "$POST_COMMIT_DST" "$POST_COMMIT_SRC" && [ "$FORCE" -ne 1 ]; then
  die "existing .githooks/post-commit differs from pmo-roadmap; refusing to overwrite without --force"
fi
cp "$POST_COMMIT_SRC" "$POST_COMMIT_DST"
chmod +x "$POST_COMMIT_DST"
echo "  ✓ wrote .githooks/post-commit"

COMMIT_MSG_DST="$TARGET/.githooks/commit-msg"
COMMIT_MSG_SRC="$SOURCE_DIR/hooks/commit-msg"
if [ -e "$COMMIT_MSG_DST" ] && ! cmp -s "$COMMIT_MSG_DST" "$COMMIT_MSG_SRC" && [ "$FORCE" -ne 1 ]; then
  die "existing .githooks/commit-msg differs from pmo-roadmap; refusing to overwrite without --force"
fi
cp "$COMMIT_MSG_SRC" "$COMMIT_MSG_DST"
chmod +x "$COMMIT_MSG_DST"
echo "  ✓ wrote .githooks/commit-msg"

cp "$SOURCE_DIR/bin/dw" "$TARGET/.githooks/dw"
chmod +x "$TARGET/.githooks/dw"
echo "  ✓ wrote .githooks/dw"

rm -rf "$TARGET/.githooks/dw_pmo"
mkdir -p "$TARGET/.githooks/dw_pmo"
cp "$SOURCE_DIR/lib/dw_pmo/"*.py "$TARGET/.githooks/dw_pmo/"
echo "  ✓ wrote .githooks/dw_pmo/"
cp "$SOURCE_DIR/bin/dw-workbench" "$TARGET/.githooks/dw-workbench"
chmod +x "$TARGET/.githooks/dw-workbench"
rm -rf "$TARGET/.githooks/workbench"
mkdir -p "$TARGET/.githooks/workbench"
cp "$SOURCE_DIR/workbench/"* "$TARGET/.githooks/workbench/"
echo "  ✓ wrote .githooks/dw-workbench + .githooks/workbench/ (local explorer UI)"

cp "$SOURCE_DIR/bin/work-log-summarize" "$TARGET/.githooks/work-log-summarize"
chmod +x "$TARGET/.githooks/work-log-summarize"
echo "  ✓ wrote .githooks/work-log-summarize"

cp "$SOURCE_DIR/bin/work-log-read" "$TARGET/.githooks/work-log-read"
chmod +x "$TARGET/.githooks/work-log-read"
echo "  ✓ wrote .githooks/work-log-read"

cp "$SOURCE_DIR/bin/dw-mcp" "$TARGET/.githooks/dw-mcp"
chmod +x "$TARGET/.githooks/dw-mcp"
echo "  ✓ wrote .githooks/dw-mcp (MCP stdio server; see docs/mcp.md)"

# .mcp.json seam: append-only, never clobbering existing servers, and
# refusing to guess at an unparseable file.
if command -v python3 >/dev/null 2>&1; then
  MCP_RESULT="$(python3 - "$TARGET" <<'MCPSEAM'
import json
import sys
from pathlib import Path

target = Path(sys.argv[1])
path = target / ".mcp.json"
entry = {"type": "stdio", "command": ".githooks/dw-mcp", "args": []}
if not path.exists():
    path.write_text(
        json.dumps({"mcpServers": {"delivery-workbench": entry}}, indent=2) + "\n",
        encoding="utf-8",
    )
    print("created")
    raise SystemExit(0)
try:
    config = json.loads(path.read_text(encoding="utf-8"))
except ValueError:
    print("unparseable")
    raise SystemExit(0)
servers = config.setdefault("mcpServers", {})
if "delivery-workbench" in servers:
    print("present")
    raise SystemExit(0)
servers["delivery-workbench"] = entry
path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
print("added")
MCPSEAM
)"
  case "$MCP_RESULT" in
    created) echo "  ✓ wrote .mcp.json (delivery-workbench MCP server entry)" ;;
    added) echo "  ✓ added delivery-workbench entry to existing .mcp.json" ;;
    present) echo "  · .mcp.json already has a delivery-workbench entry" ;;
    unparseable) echo "  ! .mcp.json is not valid JSON — NOT touching it; add the delivery-workbench entry manually" >&2 ;;
  esac
fi

# 3. core.hooksPath
git -C "$TARGET" config core.hooksPath .githooks
echo "  ✓ git config core.hooksPath = .githooks"

# 4. .gitignore — add framework scratch/runtime artifacts (append-only)
GITIGNORE="$TARGET/.gitignore"
touch "$GITIGNORE"
if grep -qxE '/?\.tmp/?' "$GITIGNORE" 2>/dev/null; then
  echo "  · .gitignore already covers .tmp/"
else
  printf '\n# pmo-roadmap pre-commit contract scratch\n.tmp/\n' >> "$GITIGNORE"
  echo "  ✓ added .tmp/ to .gitignore"
fi
if grep -qxE '/?__pycache__/?' "$GITIGNORE" 2>/dev/null; then
  echo "  · .gitignore already covers __pycache__/"
else
  printf '\n# Python runtime caches (including the vendored dw_pmo core)\n__pycache__/\n' >> "$GITIGNORE"
  echo "  ✓ added __pycache__/ to .gitignore"
fi

# 5. Agent slash commands (Claude Code) + mirrored guidance
mkdir -p "$TARGET/.claude/commands"
for cmd_file in "$SOURCE_DIR"/agent/dw-*.md; do
  cp "$cmd_file" "$TARGET/.claude/commands/$(basename "$cmd_file")"
done
echo "  ✓ wrote .claude/commands/dw-*.md"

# 6. Managed agent-docs block in CLAUDE.md / AGENTS.md
if [ "$AGENT_DOCS" -eq 1 ]; then
  if command -v python3 >/dev/null 2>&1; then
    DOCS_RESULT="$(cd "$TARGET" && PYTHONDONTWRITEBYTECODE=1 ./.githooks/dw agent-docs)" \
      && echo "  ✓ agent docs block ${DOCS_RESULT#*	} in ${DOCS_RESULT%%	*}" \
      || echo "  ! could not write the agent docs block; run .githooks/dw agent-docs manually" >&2
  else
    echo "  ! python3 not found; skipped the agent docs block (the gate needs python3 anyway)" >&2
  fi
else
  echo "  · agent docs block skipped (--no-agent-docs)"
fi

# 7. Optional bootstrap
if [ -n "$PROJECT_SLUG" ] && [ "$SKIP_BOOTSTRAP" -ne 1 ]; then
  bash "$SOURCE_DIR/bootstrap/new-project.sh" \
    "$TARGET" \
    "$PROJECT_SLUG" \
    "${PROJECT_NAME:-$PROJECT_SLUG}" \
    "${PROJECT_PREFIX:-PRJ}"
fi

echo
echo "✓ pmo-roadmap installed. Verify the wiring any time with: .githooks/dw doctor"
