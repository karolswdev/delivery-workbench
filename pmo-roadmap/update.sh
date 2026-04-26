#!/usr/bin/env bash
# pmo-roadmap update — re-pull methodology + hook into a project that
# previously installed. Never touches pm/roadmap/<slug>/ content (your
# phases and stories) or .githooks/pre-commit.local (your project rules).

set -eu

usage() {
  cat <<EOF
Usage: $0 <target-dir> [--force]

Always overwrites (these are framework-owned):
  - templates/roadmap-builder.md → pm/roadmap/roadmap-builder.md
  - hooks/pre-commit             → .githooks/pre-commit
  - hooks/post-commit            → .githooks/post-commit, unless a
                                    non-framework hook exists without --force
  - bin/work-log-summarize       → .githooks/work-log-summarize
  - bin/work-log-read            → .githooks/work-log-read

Refuses to overwrite WITHOUT --force (these may be project-customized):
  - templates/PMO-CONTRACT.md    → pm/roadmap/PMO-CONTRACT.md
  - non-framework .githooks/post-commit

Never touches:
  - pm/roadmap/<slug>/                   (your phases, stories, evidence)
  - .githooks/pre-commit.config          (your EXPECTED_BOXES override etc.)
  - .githooks/pre-commit.local           (your project-specific rule checks)
  - .gitignore                            (managed by install.sh, not this)

Use install.sh for first-time installs. Use --force only after manually
reconciling local PMO-CONTRACT.md changes against the canonical version.
EOF
}

FORCE=0
TARGET=""
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --force) FORCE=1; shift ;;
    *)
      if [ -z "$TARGET" ]; then TARGET="$1"; else echo "update.sh: unexpected arg $1" >&2; exit 1; fi
      shift ;;
  esac
done

[ -n "$TARGET" ] || { usage; exit 1; }
[ -d "$TARGET" ] || { echo "update.sh: not a dir: $TARGET" >&2; exit 1; }
TARGET="$(cd "$TARGET" && pwd)"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

git -C "$TARGET" rev-parse --show-toplevel >/dev/null 2>&1 \
  || { echo "update.sh: not a git repo: $TARGET" >&2; exit 1; }
TARGET="$(git -C "$TARGET" rev-parse --show-toplevel)"

echo "→ Updating pmo-roadmap in $TARGET"

mkdir -p "$TARGET/pm/roadmap" "$TARGET/.githooks"
cp "$SOURCE_DIR/templates/roadmap-builder.md" "$TARGET/pm/roadmap/roadmap-builder.md"
echo "  ✓ roadmap-builder.md updated"

cp "$SOURCE_DIR/hooks/pre-commit" "$TARGET/.githooks/pre-commit"
chmod +x "$TARGET/.githooks/pre-commit"
echo "  ✓ .githooks/pre-commit updated"

POST_COMMIT_DST="$TARGET/.githooks/post-commit"
POST_COMMIT_SRC="$SOURCE_DIR/hooks/post-commit"
if [ -e "$POST_COMMIT_DST" ] && ! cmp -s "$POST_COMMIT_DST" "$POST_COMMIT_SRC" && [ "$FORCE" -ne 1 ]; then
  echo "  ! .githooks/post-commit differs from canonical — NOT overwriting." >&2
  echo "    Preserve or compose the existing hook manually, or re-run with --force" >&2
  echo "    after confirming it is safe to replace." >&2
else
  cp "$POST_COMMIT_SRC" "$POST_COMMIT_DST"
  chmod +x "$POST_COMMIT_DST"
  echo "  ✓ .githooks/post-commit updated$([ "$FORCE" -eq 1 ] && echo ' (forced)')"
fi

cp "$SOURCE_DIR/bin/work-log-summarize" "$TARGET/.githooks/work-log-summarize"
chmod +x "$TARGET/.githooks/work-log-summarize"
echo "  ✓ .githooks/work-log-summarize updated"

cp "$SOURCE_DIR/bin/work-log-read" "$TARGET/.githooks/work-log-read"
chmod +x "$TARGET/.githooks/work-log-read"
echo "  ✓ .githooks/work-log-read updated"

# PMO-CONTRACT.md may carry project extensions appended after the canonical
# rules. Refuse to overwrite without --force; print a diff hint.
TARGET_CONTRACT="$TARGET/pm/roadmap/PMO-CONTRACT.md"
SOURCE_CONTRACT="$SOURCE_DIR/templates/PMO-CONTRACT.md"
if [ -f "$TARGET_CONTRACT" ] && [ "$FORCE" -ne 1 ]; then
  if cmp -s "$TARGET_CONTRACT" "$SOURCE_CONTRACT"; then
    echo "  · PMO-CONTRACT.md already matches canonical; no change."
  else
    echo "  ! PMO-CONTRACT.md differs from canonical — NOT overwriting." >&2
    echo "    This is normal if you have project-extension rules below" >&2
    echo "    the canonical 7. Reconcile manually:" >&2
    echo "      diff -u $TARGET_CONTRACT \\" >&2
    echo "             $SOURCE_CONTRACT" >&2
    echo "    Then re-run with --force to overwrite." >&2
  fi
else
  cp "$SOURCE_CONTRACT" "$TARGET_CONTRACT"
  echo "  ✓ PMO-CONTRACT.md updated$([ "$FORCE" -eq 1 ] && echo ' (forced)')"
fi

# Re-assert hooksPath in case it drifted.
git -C "$TARGET" config core.hooksPath .githooks

if [ -f "$TARGET/.githooks/pre-commit.config" ]; then
  echo "  · .githooks/pre-commit.config present — preserved (project-owned)."
fi
if [ -f "$TARGET/.githooks/pre-commit.local" ]; then
  echo "  · .githooks/pre-commit.local present — preserved (project-owned)."
fi

echo "✓ Done."
