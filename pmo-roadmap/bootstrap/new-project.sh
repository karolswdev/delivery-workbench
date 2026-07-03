#!/usr/bin/env bash
# pmo-roadmap bootstrap — scaffold pm/roadmap/<slug>/ skeleton in a
# target repo that already has the framework installed.
#
# Usage: new-project.sh <target-dir> <slug> <name> <prefix>

set -eu

# bash >= 5.2 expands & in ${var//pat/repl} replacements by default
# (patsub_replacement); quoting the replacement breaks bash 3.2, so
# disable the option where it exists and keep replacements unquoted.
shopt -u patsub_replacement 2>/dev/null || true

usage() {
  cat <<EOF
Usage: $0 <target-dir> <project-slug> <project-name> <project-prefix>

Examples:
  $0 /path/to/myproject myproject "My Project" MP
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

# Render a template file with literal {{KEY}} substitution (bash
# pattern replacement, not sed — hostile characters like | & \ in
# project names must not corrupt the output).
render() {
  src="$1"; dst="$2"
  if [ -e "$dst" ]; then
    echo "  · skip (exists): ${dst#"$TARGET"/}"
    return 0
  fi
  text="$(cat "$src")"
  text="${text//\{\{PROJECT_NAME\}\}/$NAME}"
  text="${text//\{\{PROJECT_SLUG\}\}/$SLUG}"
  text="${text//\{\{PROJECT_PREFIX\}\}/$PREFIX}"
  text="${text//\{\{DATE\}\}/$DATE}"
  text="${text//\{\{PHASE_N\}\}/0}"
  text="${text//\{\{PHASE_TITLE\}\}/Setup}"
  text="${text//\{\{STORY_ID\}\}/$PREFIX-0-01}"
  text="${text//\{\{STORY_TITLE\}\}/Bootstrap roadmap project}"
  text="${text//\{\{STATUS\}\}/backlog}"
  placeholder_row="| $PREFIX-0-01 | … | backlog | [story-01-…](./story-01-….md) | — |"
  bootstrap_row="| $PREFIX-0-01 | Bootstrap roadmap project | backlog | [story-01-bootstrap](./story-01-bootstrap.md) | - |"
  text="${text/"$placeholder_row"/$bootstrap_row}"
  printf '%s\n' "$text" > "$dst"
  echo "  ✓ wrote ${dst#"$TARGET"/}"
}

echo "→ Scaffolding pm/roadmap/$SLUG/"
render "$TEMPLATES/project-README.md.tmpl" "$PROJECT_DIR/README.md"
render "$TEMPLATES/phase-status.md.tmpl"   "$PHASE_DIR/current-phase-status.md"
render "$TEMPLATES/story.md.tmpl"          "$PHASE_DIR/story-01-bootstrap.md"

echo "✓ Scaffold complete. Edit pm/roadmap/$SLUG/README.md to fill in vision + phase index."
