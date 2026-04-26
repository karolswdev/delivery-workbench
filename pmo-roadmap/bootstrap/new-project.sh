#!/usr/bin/env bash
# pmo-roadmap bootstrap — scaffold pm/roadmap/<slug>/ skeleton in a
# target repo that already has the framework installed.
#
# Usage: new-project.sh <target-dir> <slug> <name> <prefix>

set -eu

usage() {
  cat <<EOF
Usage: $0 <target-dir> <project-slug> <project-name> <project-prefix>

Examples:
  $0 ~/dev/projects/pantrybot pantrybot "Pantrybot" PB
  $0 . myapp "My App" MA

Creates:
  pm/roadmap/<slug>/README.md                       (from project-README.md.tmpl)
  pm/roadmap/<slug>/phase-0-setup/current-phase-status.md   (from phase-status.md.tmpl)
  pm/roadmap/<slug>/phase-0-setup/story-01-bootstrap.md     (from story.md.tmpl)

Idempotent: existing files are skipped (never overwritten).
EOF
}

[ $# -eq 4 ] || { usage; exit 1; }

TARGET="$1"; SLUG="$2"; NAME="$3"; PREFIX="$4"
[ -d "$TARGET" ] || { echo "bootstrap: not a dir: $TARGET" >&2; exit 1; }
TARGET="$(cd "$TARGET" && pwd)"
SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES="$SOURCE_DIR/templates"

DATE="$(date +%Y-%m-%d)"
PROJECT_DIR="$TARGET/pm/roadmap/$SLUG"
PHASE_DIR="$PROJECT_DIR/phase-0-setup"

mkdir -p "$PHASE_DIR"

# Render a template file with simple {{KEY}} substitution.
render() {
  src="$1"; dst="$2"
  if [ -e "$dst" ]; then
    echo "  · skip (exists): ${dst#$TARGET/}"
    return 0
  fi
  sed \
    -e "s|{{PROJECT_NAME}}|$NAME|g" \
    -e "s|{{PROJECT_SLUG}}|$SLUG|g" \
    -e "s|{{PROJECT_PREFIX}}|$PREFIX|g" \
    -e "s|{{DATE}}|$DATE|g" \
    -e "s|{{PHASE_N}}|0|g" \
    -e "s|{{PHASE_TITLE}}|Setup|g" \
    -e "s|{{STORY_ID}}|$PREFIX-0-01|g" \
    -e "s|{{STORY_TITLE}}|Bootstrap roadmap project|g" \
    "$src" > "$dst"
  echo "  ✓ wrote ${dst#$TARGET/}"
}

echo "→ Scaffolding pm/roadmap/$SLUG/"
render "$TEMPLATES/project-README.md.tmpl" "$PROJECT_DIR/README.md"
render "$TEMPLATES/phase-status.md.tmpl"   "$PHASE_DIR/current-phase-status.md"
render "$TEMPLATES/story.md.tmpl"          "$PHASE_DIR/story-01-bootstrap.md"

echo "✓ Scaffold complete. Edit pm/roadmap/$SLUG/README.md to fill in vision + phase index."
