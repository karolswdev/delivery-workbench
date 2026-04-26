#!/usr/bin/env bash
# pmo-roadmap adoption discovery — prepare or run a read-only PMO onboarding
# mission for an existing project.

set -eu

usage() {
  cat <<EOF
Usage: $0 <target-dir> [options]

Creates a PMO adoption discovery prompt/report location for an existing repo,
and optionally invokes an agent to inspect the repo read-only.

Options:
  --project-name "Name"       Human project name
  --project-slug slug         Kebab slug for pm/roadmap/<slug>
  --project-prefix PFX        Story-ID prefix
  --agent none|codex|claude   Agent to run (default: none)
  --model MODEL               Agent model override
  --with-intake               Run session-intake.sh before rendering discovery
  --intake-file FILE          Override session intake path
  --require-intake            Refuse discovery if intake file is missing
  --dangerous                 Give the chosen agent full local repo access
  --output FILE               Override report output path
  --force                     Overwrite existing prompt/report
  -h, --help                  Show this help

Examples:
  $0 ~/dev/project --project-name "My App" --project-slug myapp --project-prefix MA
  $0 . --project-slug api --project-prefix API --agent codex --model gpt-5.5 --dangerous
  $0 . --project-slug api --project-prefix API --agent claude --model opus --dangerous
EOF
}

die() {
  echo "adopt-project.sh: $1" >&2
  exit 1
}

TARGET=""
PROJECT_NAME=""
PROJECT_SLUG=""
PROJECT_PREFIX=""
AGENT="none"
MODEL=""
DANGEROUS=0
OUTPUT=""
INTAKE_FILE=""
WITH_INTAKE=0
REQUIRE_INTAKE=0
FORCE=0

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --project-name) PROJECT_NAME="$2"; shift 2 ;;
    --project-slug) PROJECT_SLUG="$2"; shift 2 ;;
    --project-prefix) PROJECT_PREFIX="$2"; shift 2 ;;
    --agent) AGENT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --with-intake) WITH_INTAKE=1; shift ;;
    --intake-file) INTAKE_FILE="$2"; shift 2 ;;
    --require-intake) REQUIRE_INTAKE=1; shift ;;
    --dangerous) DANGEROUS=1; shift ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --) shift; break ;;
    -*) die "unknown option: $1" ;;
    *)
      if [ -z "$TARGET" ]; then TARGET="$1"; else die "unexpected arg: $1"; fi
      shift
      ;;
  esac
done

[ -n "$TARGET" ] || { usage; exit 1; }
[ -d "$TARGET" ] || die "target directory does not exist: $TARGET"
TARGET="$(cd "$TARGET" && pwd)"
git -C "$TARGET" rev-parse --show-toplevel >/dev/null 2>&1 || die "not a git repo: $TARGET"
TARGET="$(git -C "$TARGET" rev-parse --show-toplevel)"

[ -n "$PROJECT_SLUG" ] || PROJECT_SLUG="$(basename "$TARGET" | sed -E 's/[^A-Za-z0-9._-]+/-/g; s/^-+//; s/-+$//')"
[ -n "$PROJECT_NAME" ] || PROJECT_NAME="$PROJECT_SLUG"
[ -n "$PROJECT_PREFIX" ] || PROJECT_PREFIX="PRJ"

case "$AGENT" in
  none|codex|claude) ;;
  *) die "--agent must be one of: none, codex, claude" ;;
esac

SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$SOURCE_DIR/templates/adoption-discovery-prompt.md"
[ -f "$TEMPLATE" ] || die "missing template: $TEMPLATE"

PROJECT_DIR="$TARGET/pm/roadmap/$PROJECT_SLUG"
DISCOVERY_DIR="$PROJECT_DIR/adoption"
PROMPT_FILE="$DISCOVERY_DIR/adoption-discovery-prompt.md"
if [ -z "$OUTPUT" ]; then
  OUTPUT="$DISCOVERY_DIR/adoption-discovery.md"
fi
if [ -z "$INTAKE_FILE" ]; then
  INTAKE_FILE="$DISCOVERY_DIR/session-intake.md"
fi

mkdir -p "$DISCOVERY_DIR"

if [ "$WITH_INTAKE" -eq 1 ]; then
  intake_args=(
    "$TARGET"
    --project-name "$PROJECT_NAME"
    --project-slug "$PROJECT_SLUG"
    --project-prefix "$PROJECT_PREFIX"
    --output "$INTAKE_FILE"
  )
  if [ "$FORCE" -eq 1 ]; then
    intake_args+=(--force)
  fi
  "$SOURCE_DIR/bootstrap/session-intake.sh" "${intake_args[@]}"
fi

if [ ! -f "$INTAKE_FILE" ]; then
  if [ "$REQUIRE_INTAKE" -eq 1 ]; then
    die "session intake missing, run bootstrap/session-intake.sh first: $INTAKE_FILE"
  fi
  echo "  ! session intake missing: ${INTAKE_FILE#$TARGET/}" >&2
  echo "    Discovery prompt will require the agent to flag unresolved user intent." >&2
fi

render_prompt() {
  sed \
    -e "s|{{PROJECT_NAME}}|$PROJECT_NAME|g" \
    -e "s|{{PROJECT_SLUG}}|$PROJECT_SLUG|g" \
    -e "s|{{PROJECT_PREFIX}}|$PROJECT_PREFIX|g" \
    -e "s|{{TARGET_DIR}}|$TARGET|g" \
    -e "s|{{OUTPUT_PATH}}|$OUTPUT|g" \
    -e "s|{{INTAKE_PATH}}|$INTAKE_FILE|g" \
    "$TEMPLATE"
}

if [ -e "$PROMPT_FILE" ] && [ "$FORCE" -ne 1 ]; then
  echo "  · prompt exists: ${PROMPT_FILE#$TARGET/}"
else
  render_prompt > "$PROMPT_FILE"
  echo "  ✓ wrote ${PROMPT_FILE#$TARGET/}"
fi

if [ "$AGENT" = "none" ]; then
  echo "✓ Adoption prompt ready."
  echo "  Prompt: ${PROMPT_FILE#$TARGET/}"
  echo "  Intake: ${INTAKE_FILE#$TARGET/}"
  echo "  Report target: ${OUTPUT#$TARGET/}"
  exit 0
fi

if [ -e "$OUTPUT" ] && [ "$FORCE" -ne 1 ]; then
  die "output exists, use --force to overwrite: $OUTPUT"
fi

case "$AGENT" in
  codex)
    command -v codex >/dev/null 2>&1 || die "codex CLI not found"
    cmd_args="exec -C \"$TARGET\" -a never"
    if [ -n "$MODEL" ]; then cmd_args="$cmd_args -m \"$MODEL\""; fi
    if [ "$DANGEROUS" -eq 1 ]; then
      cmd_args="$cmd_args --dangerously-bypass-approvals-and-sandbox"
    else
      cmd_args="$cmd_args -s read-only"
    fi
    # shellcheck disable=SC2086
    sh -c "codex $cmd_args -o \"$OUTPUT\" -" < "$PROMPT_FILE"
    ;;
  claude)
    command -v claude >/dev/null 2>&1 || die "claude CLI not found"
    claude_args="-p"
    if [ -n "$MODEL" ]; then claude_args="$claude_args --model \"$MODEL\""; fi
    if [ "$DANGEROUS" -eq 1 ]; then
      claude_args="$claude_args --dangerously-skip-permissions"
    else
      claude_args="$claude_args --permission-mode dontAsk"
    fi
    # shellcheck disable=SC2086
    (cd "$TARGET" && sh -c "claude $claude_args" < "$PROMPT_FILE" > "$OUTPUT")
    ;;
esac

echo "✓ Adoption discovery complete: ${OUTPUT#$TARGET/}"
