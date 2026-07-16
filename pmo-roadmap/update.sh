#!/usr/bin/env bash
# pmo-roadmap update — re-pull methodology + hook into a project that
# previously installed. Never touches pm/roadmap/<slug>/ content (your
# phases and stories) or .githooks/pre-commit.local (your project rules).

set -eu

usage() {
  cat <<EOF
Usage: $0 <target-dir> [--force] [--check]

  --check   Report whether the target's vendored rails match this
            source's version (exit 0 fresh / 3 stale); writes nothing.

Always overwrites (these are framework-owned):
  - templates/roadmap-builder.md → pm/roadmap/roadmap-builder.md
  - hooks/pre-commit             → .githooks/pre-commit
  - hooks/commit-msg             → .githooks/commit-msg, unless a
                                    non-framework hook exists without --force
  - hooks/post-commit            → .githooks/post-commit, unless a
                                    non-framework hook exists without --force
  - bin/dw                       → .githooks/dw
  - lib/dw_pmo/                  → .githooks/dw_pmo/
  - bin/dw-workbench + workbench/ → .githooks/ (local UI)
  - bin/work-log-summarize       → .githooks/work-log-summarize
  - bin/work-log-read            → .githooks/work-log-read
  - bin/dw-mcp                   → .githooks/dw-mcp

When the target is this source checkout, update refreshes only the vendored
runtime surfaces and skips the pm/roadmap scaffold. The framework's canonical
roadmap lives under pmo-roadmap/pm/roadmap and must not be shadowed.

Refuses to overwrite WITHOUT --force (these may be project-customized):
  - templates/PMO-CONTRACT.md    → pm/roadmap/PMO-CONTRACT.md
  - non-framework .githooks/post-commit

Never touches:
  - pm/roadmap/<slug>/                   (your phases, stories, evidence)
  - .githooks/pre-commit.config          (your project config)
  - .githooks/pre-commit.local           (your project-specific rule checks)

Also keeps the .tmp/ and __pycache__/ entries present in .gitignore
(append-only; existing entries and spellings are respected).

Use install.sh for first-time installs. Use --force only after manually
reconciling local PMO-CONTRACT.md changes against the canonical version.
EOF
}

FORCE=0
CHECK=0
TARGET=""
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --force) FORCE=1; shift ;;
    --check) CHECK=1; shift ;;
    *)
      if [ -z "$TARGET" ]; then TARGET="$1"; else echo "update.sh: unexpected arg $1" >&2; exit 1; fi
      shift ;;
  esac
done

[ -n "$TARGET" ] || { usage; exit 1; }
[ -d "$TARGET" ] || { echo "update.sh: not a dir: $TARGET" >&2; exit 1; }
TARGET="$(cd "$TARGET" && pwd)"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd -P)"

git -C "$TARGET" rev-parse --show-toplevel >/dev/null 2>&1 \
  || { echo "update.sh: not a git repo: $TARGET" >&2; exit 1; }
TARGET="$(git -C "$TARGET" rev-parse --show-toplevel)"

# The framework repository keeps its canon under pmo-roadmap/.  When
# update.sh runs from a source directory inside the target, creating a
# second root pm/roadmap/ would shadow the real dogfood roadmap in every
# reader.  Refresh only the vendored rails in that layout, exactly like
# install.sh's self-hosted seam.
SELF_HOSTED=0
case "$SOURCE_DIR" in
  "$TARGET"/*) SELF_HOSTED=1 ;;
esac

vendored_version() { # dir
  sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$1/lib/dw_pmo/__init__.py" 2>/dev/null \
    || sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$1/dw_pmo/__init__.py" 2>/dev/null
}

if [ "$CHECK" -eq 1 ]; then
  # Staleness report only — never writes. Content is the signal
  # (version strings match between releases while code moves), so the
  # vendored core and CLI are diffed against this source; versions are
  # printed as context. Exit 0 fresh / 3 stale.
  SRC_VERSION="$(vendored_version "$SOURCE_DIR")"
  TGT_VERSION="$(vendored_version "$TARGET/.githooks")"
  [ -n "$SRC_VERSION" ] || { echo "update.sh: cannot read source version" >&2; exit 1; }
  [ -n "$TGT_VERSION" ] || { echo "update.sh: no vendored rails found in $TARGET/.githooks" >&2; exit 1; }
  STALE=0
  diff -r -q -x '__pycache__' -x '*.pyc'     "$SOURCE_DIR/lib/dw_pmo" "$TARGET/.githooks/dw_pmo" >/dev/null 2>&1 || STALE=1
  cmp -s "$SOURCE_DIR/bin/dw" "$TARGET/.githooks/dw" || STALE=1
  cmp -s "$SOURCE_DIR/hooks/pre-commit" "$TARGET/.githooks/pre-commit" || STALE=1
  if [ "$STALE" -eq 0 ]; then
    echo "update.sh: up to date (vendored rails match source v$SRC_VERSION)"
    exit 0
  fi
  echo "update.sh: STALE — vendored rails (v$TGT_VERSION) differ from source (v$SRC_VERSION). Refresh with: update.sh $TARGET"
  exit 3
fi

echo "→ Updating pmo-roadmap in $TARGET"

mkdir -p "$TARGET/.githooks"
if [ "$SELF_HOSTED" -eq 1 ]; then
  echo "  · self-hosting refresh (source inside target); skipping pm/roadmap canon scaffold"
else
  mkdir -p "$TARGET/pm/roadmap"
  cp "$SOURCE_DIR/templates/roadmap-builder.md" "$TARGET/pm/roadmap/roadmap-builder.md"
  echo "  ✓ roadmap-builder.md updated"
fi

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

COMMIT_MSG_DST="$TARGET/.githooks/commit-msg"
COMMIT_MSG_SRC="$SOURCE_DIR/hooks/commit-msg"
if [ -e "$COMMIT_MSG_DST" ] && ! cmp -s "$COMMIT_MSG_DST" "$COMMIT_MSG_SRC" && [ "$FORCE" -ne 1 ] \
  && ! grep -q "pmo-roadmap commit-msg shim" "$COMMIT_MSG_DST" 2>/dev/null; then
  echo "  ! .githooks/commit-msg differs from canonical — NOT overwriting." >&2
  echo "    Reconcile manually or re-run with --force." >&2
else
  cp "$COMMIT_MSG_SRC" "$COMMIT_MSG_DST"
  chmod +x "$COMMIT_MSG_DST"
  echo "  ✓ .githooks/commit-msg updated$([ "$FORCE" -eq 1 ] && echo ' (forced)')"
fi

cp "$SOURCE_DIR/bin/work-log-summarize" "$TARGET/.githooks/work-log-summarize"
chmod +x "$TARGET/.githooks/work-log-summarize"
echo "  ✓ .githooks/work-log-summarize updated"

cp "$SOURCE_DIR/bin/dw" "$TARGET/.githooks/dw"
chmod +x "$TARGET/.githooks/dw"
echo "  ✓ .githooks/dw updated"

rm -rf "$TARGET/.githooks/dw_pmo"
mkdir -p "$TARGET/.githooks/dw_pmo"
cp "$SOURCE_DIR/lib/dw_pmo/"*.py "$TARGET/.githooks/dw_pmo/"
echo "  ✓ .githooks/dw_pmo updated"
cp "$SOURCE_DIR/bin/dw-workbench" "$TARGET/.githooks/dw-workbench"
chmod +x "$TARGET/.githooks/dw-workbench"
rm -rf "$TARGET/.githooks/workbench"
mkdir -p "$TARGET/.githooks/workbench"
cp "$SOURCE_DIR/workbench/"* "$TARGET/.githooks/workbench/"
echo "  ✓ .githooks/dw-workbench + workbench UI updated"

cp "$SOURCE_DIR/bin/work-log-read" "$TARGET/.githooks/work-log-read"
chmod +x "$TARGET/.githooks/work-log-read"
cp "$SOURCE_DIR/bin/dw-mcp" "$TARGET/.githooks/dw-mcp"
chmod +x "$TARGET/.githooks/dw-mcp"
echo "  ✓ .githooks/dw-mcp updated"
echo "  ✓ .githooks/work-log-read updated"

mkdir -p "$TARGET/.claude/commands"
for cmd_file in "$SOURCE_DIR"/agent/dw-*.md; do
  cp "$cmd_file" "$TARGET/.claude/commands/$(basename "$cmd_file")"
done
echo "  ✓ .claude/commands/dw-*.md updated"

if command -v python3 >/dev/null 2>&1; then
  DOCS_RESULT="$(cd "$TARGET" && ./.githooks/dw agent-docs)" \
    && echo "  ✓ agent docs block ${DOCS_RESULT#*	} in ${DOCS_RESULT%%	*}" \
    || echo "  ! could not refresh the agent docs block; run .githooks/dw agent-docs manually" >&2
fi

# PMO-CONTRACT.md may carry project extensions appended after the canonical
# rules. Refuse to overwrite without --force; print a diff hint.
TARGET_CONTRACT="$TARGET/pm/roadmap/PMO-CONTRACT.md"
SOURCE_CONTRACT="$SOURCE_DIR/templates/PMO-CONTRACT.md"
if [ "$SELF_HOSTED" -eq 1 ]; then
  : # Canon is already $SOURCE_CONTRACT; never scaffold a shadow tree.
elif [ -f "$TARGET_CONTRACT" ] && [ "$FORCE" -ne 1 ]; then
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

# Keep framework scratch/runtime artifacts ignored (append-only).
GITIGNORE="$TARGET/.gitignore"
touch "$GITIGNORE"
if ! grep -qxE '/?\.tmp/?' "$GITIGNORE" 2>/dev/null; then
  printf '\n# pmo-roadmap pre-commit contract scratch\n.tmp/\n' >> "$GITIGNORE"
  echo "  ✓ added .tmp/ to .gitignore"
fi
if ! grep -qxE '/?__pycache__/?' "$GITIGNORE" 2>/dev/null; then
  printf '\n# Python runtime caches (including the vendored dw_pmo core)\n__pycache__/\n' >> "$GITIGNORE"
  echo "  ✓ added __pycache__/ to .gitignore"
fi

if [ -f "$TARGET/.githooks/pre-commit.config" ]; then
  echo "  · .githooks/pre-commit.config present — preserved (project-owned)."
fi
if [ -f "$TARGET/.githooks/pre-commit.local" ]; then
  echo "  · .githooks/pre-commit.local present — preserved (project-owned)."
fi

echo "✓ Done."
