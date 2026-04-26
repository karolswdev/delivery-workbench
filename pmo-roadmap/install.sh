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
  - copies hooks/pre-commit               → .githooks/pre-commit (chmod +x)
  - copies hooks/post-commit              → .githooks/post-commit (chmod +x)
  - copies bin/work-log-summarize         → .githooks/work-log-summarize
  - copies bin/work-log-read              → .githooks/work-log-read
  - sets git config core.hooksPath .githooks
  - adds .tmp/ to .gitignore (if missing)
  - optionally scaffolds pm/roadmap/<slug>/ skeleton

Options:
  --project-name "Name"     Human project name (e.g. "Pantrybot")
  --project-slug slug       Kebab slug (e.g. "pantrybot")
  --project-prefix PFX      Story-ID prefix (e.g. "PB")
  --skip-bootstrap          Don't scaffold pm/roadmap/<slug>/
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
FORCE=0

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --project-name) PROJECT_NAME="$2"; shift 2 ;;
    --project-slug) PROJECT_SLUG="$2"; shift 2 ;;
    --project-prefix) PROJECT_PREFIX="$2"; shift 2 ;;
    --skip-bootstrap) SKIP_BOOTSTRAP=1; shift ;;
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
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

# Verify target is a git repo.
git -C "$TARGET" rev-parse --show-toplevel >/dev/null 2>&1 \
  || die "not a git repo: $TARGET"
TARGET="$(git -C "$TARGET" rev-parse --show-toplevel)"

echo "→ Installing pmo-roadmap into $TARGET"

# 1. Methodology + contract
mkdir -p "$TARGET/pm/roadmap"
copy_template() {
  src="$1"; dst="$2"
  if [ -e "$dst" ] && [ "$FORCE" -ne 1 ]; then
    echo "  · skip (exists, use --force to overwrite): ${dst#$TARGET/}"
  else
    cp "$src" "$dst"
    echo "  ✓ wrote ${dst#$TARGET/}"
  fi
}
copy_template "$SOURCE_DIR/templates/roadmap-builder.md" "$TARGET/pm/roadmap/roadmap-builder.md"
copy_template "$SOURCE_DIR/templates/PMO-CONTRACT.md"    "$TARGET/pm/roadmap/PMO-CONTRACT.md"

# 2. Hooks
mkdir -p "$TARGET/.githooks"
cp "$SOURCE_DIR/hooks/pre-commit" "$TARGET/.githooks/pre-commit"
chmod +x "$TARGET/.githooks/pre-commit"
echo "  ✓ wrote .githooks/pre-commit"

POST_COMMIT_DST="$TARGET/.githooks/post-commit"
POST_COMMIT_SRC="$SOURCE_DIR/hooks/post-commit"
if [ -e "$POST_COMMIT_DST" ] && ! cmp -s "$POST_COMMIT_DST" "$POST_COMMIT_SRC" && [ "$FORCE" -ne 1 ]; then
  die "existing .githooks/post-commit differs from pmo-roadmap; refusing to overwrite without --force"
fi
cp "$POST_COMMIT_SRC" "$POST_COMMIT_DST"
chmod +x "$POST_COMMIT_DST"
echo "  ✓ wrote .githooks/post-commit"

cp "$SOURCE_DIR/bin/work-log-summarize" "$TARGET/.githooks/work-log-summarize"
chmod +x "$TARGET/.githooks/work-log-summarize"
echo "  ✓ wrote .githooks/work-log-summarize"

cp "$SOURCE_DIR/bin/work-log-read" "$TARGET/.githooks/work-log-read"
chmod +x "$TARGET/.githooks/work-log-read"
echo "  ✓ wrote .githooks/work-log-read"

# 3. core.hooksPath
git -C "$TARGET" config core.hooksPath .githooks
echo "  ✓ git config core.hooksPath = .githooks"

# 4. .gitignore — add .tmp/
GITIGNORE="$TARGET/.gitignore"
touch "$GITIGNORE"
if grep -qxF '.tmp/' "$GITIGNORE" 2>/dev/null; then
  echo "  · .gitignore already has .tmp/"
else
  printf '\n# pmo-roadmap pre-commit contract scratch\n.tmp/\n' >> "$GITIGNORE"
  echo "  ✓ added .tmp/ to .gitignore"
fi

# 5. Optional bootstrap
if [ -n "$PROJECT_SLUG" ] && [ "$SKIP_BOOTSTRAP" -ne 1 ]; then
  bash "$SOURCE_DIR/bootstrap/new-project.sh" \
    "$TARGET" \
    "$PROJECT_SLUG" \
    "${PROJECT_NAME:-$PROJECT_SLUG}" \
    "${PROJECT_PREFIX:-PRJ}"
fi

# 6. Snippet for CLAUDE.md / AGENTS.md
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Add the following to $TARGET/CLAUDE.md (or AGENTS.md):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat "$SOURCE_DIR/templates/CLAUDE-snippet.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "✓ pmo-roadmap installed."
