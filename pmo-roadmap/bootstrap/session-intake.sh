#!/usr/bin/env bash
# pmo-roadmap session intake — capture user direction before discovery/roadmap.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$PMO_DIR/templates/session-intake.md.tmpl"

usage() {
  cat <<EOF
Usage: $0 <target-dir> [options]

Captures what the user wants from this session before adoption discovery or
roadmap generation. Writes:
  pm/roadmap/<slug>/adoption/session-intake.md

Options:
  --project-name "Name"       Human project name
  --project-slug slug         Kebab slug for pm/roadmap/<slug>
  --project-prefix PFX        Story-ID prefix
  --goal TEXT                 User goal for this session
  --direction TEXT            Desired technical/product direction
  --handoff TEXT              What a good handoff should contain
  --success TEXT              Success criteria / evidence
  --constraints TEXT          Constraints and non-goals
  --context TEXT              Known user-provided context
  --agent-style TEXT          Preferred agent / execution style
  --questions TEXT            Open questions to resolve
  --output FILE               Override output path
  --force                     Overwrite existing intake
  --no-prompt                 Do not ask interactive questions for blanks
  -h, --help                  Show this help

If stdin is a TTY and --no-prompt is not set, blank fields are prompted
interactively. In automation, pass fields as flags or accept placeholders.
EOF
}

die() {
  echo "session-intake.sh: $1" >&2
  exit 1
}

prompt_if_blank() {
  label="$1"
  current="$2"
  placeholder="$3"
  if [ -n "$current" ]; then
    printf '%s\n' "$current"
    return
  fi
  if [ "$NO_PROMPT" -eq 0 ] && [ -t 0 ]; then
    printf '%s\n> ' "$label" >&2
    IFS= read -r answer || answer=""
    if [ -n "$answer" ]; then
      printf '%s\n' "$answer"
      return
    fi
  fi
  printf '%s\n' "$placeholder"
}

render_block() {
  value="$1"
  if [ -n "$value" ]; then
    printf '%s\n' "$value"
  else
    printf '%s\n' "- not provided"
  fi
}

TARGET=""
PROJECT_NAME=""
PROJECT_SLUG=""
PROJECT_PREFIX=""
SESSION_GOAL=""
DIRECTION=""
HANDOFF=""
SUCCESS_CRITERIA=""
CONSTRAINTS=""
KNOWN_CONTEXT=""
AGENT_STYLE=""
OPEN_QUESTIONS=""
OUTPUT=""
FORCE=0
NO_PROMPT=0

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --project-name) PROJECT_NAME="$2"; shift 2 ;;
    --project-slug) PROJECT_SLUG="$2"; shift 2 ;;
    --project-prefix) PROJECT_PREFIX="$2"; shift 2 ;;
    --goal) SESSION_GOAL="$2"; shift 2 ;;
    --direction) DIRECTION="$2"; shift 2 ;;
    --handoff) HANDOFF="$2"; shift 2 ;;
    --success) SUCCESS_CRITERIA="$2"; shift 2 ;;
    --constraints) CONSTRAINTS="$2"; shift 2 ;;
    --context) KNOWN_CONTEXT="$2"; shift 2 ;;
    --agent-style) AGENT_STYLE="$2"; shift 2 ;;
    --questions) OPEN_QUESTIONS="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --no-prompt) NO_PROMPT=1; shift ;;
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
[ -f "$TEMPLATE" ] || die "template missing: $TEMPLATE"
TARGET="$(cd "$TARGET" && pwd)"
git -C "$TARGET" rev-parse --show-toplevel >/dev/null 2>&1 || die "not a git repo: $TARGET"
TARGET="$(git -C "$TARGET" rev-parse --show-toplevel)"

[ -n "$PROJECT_SLUG" ] || PROJECT_SLUG="$(basename "$TARGET" | sed -E 's/[^A-Za-z0-9._-]+/-/g; s/^-+//; s/-+$//')"
[ -n "$PROJECT_NAME" ] || PROJECT_NAME="$PROJECT_SLUG"
[ -n "$PROJECT_PREFIX" ] || PROJECT_PREFIX="PRJ"

PROJECT_DIR="$TARGET/pm/roadmap/$PROJECT_SLUG"
DISCOVERY_DIR="$PROJECT_DIR/adoption"
if [ -z "$OUTPUT" ]; then
  OUTPUT="$DISCOVERY_DIR/session-intake.md"
fi

if [ -e "$OUTPUT" ] && [ "$FORCE" -ne 1 ]; then
  die "intake exists, use --force to overwrite: $OUTPUT"
fi

SESSION_GOAL=$(prompt_if_blank "What do you want done in this session?" "$SESSION_GOAL" "- not provided")
DIRECTION=$(prompt_if_blank "What direction should the roadmap steer toward?" "$DIRECTION" "- not provided")
HANDOFF=$(prompt_if_blank "What should a good handoff include?" "$HANDOFF" "- not provided")
SUCCESS_CRITERIA=$(prompt_if_blank "What evidence would make this session successful?" "$SUCCESS_CRITERIA" "- not provided")
CONSTRAINTS=$(prompt_if_blank "Any constraints or non-goals?" "$CONSTRAINTS" "- not provided")
KNOWN_CONTEXT=$(prompt_if_blank "Any context the agent must not miss?" "$KNOWN_CONTEXT" "- not provided")
AGENT_STYLE=$(prompt_if_blank "Preferred agent/execution style?" "$AGENT_STYLE" "- not provided")
OPEN_QUESTIONS=$(prompt_if_blank "Questions to resolve before roadmapping?" "$OPEN_QUESTIONS" "- not provided")

mkdir -p "$DISCOVERY_DIR"
DATE="$(date +%Y-%m-%d)"

awk \
  -v PROJECT_NAME="$PROJECT_NAME" \
  -v DATE="$DATE" \
  -v PROJECT_SLUG="$PROJECT_SLUG" \
  -v PROJECT_PREFIX="$PROJECT_PREFIX" \
  -v TARGET_DIR="$TARGET" \
  -v SESSION_GOAL="$(render_block "$SESSION_GOAL")" \
  -v DIRECTION="$(render_block "$DIRECTION")" \
  -v HANDOFF="$(render_block "$HANDOFF")" \
  -v SUCCESS_CRITERIA="$(render_block "$SUCCESS_CRITERIA")" \
  -v CONSTRAINTS="$(render_block "$CONSTRAINTS")" \
  -v KNOWN_CONTEXT="$(render_block "$KNOWN_CONTEXT")" \
  -v AGENT_STYLE="$(render_block "$AGENT_STYLE")" \
  -v OPEN_QUESTIONS="$(render_block "$OPEN_QUESTIONS")" \
  '
  function repl(value) {
    gsub(/\\/, "\\\\", value)
    gsub(/&/, "\\\\&", value)
    return value
  }
  BEGIN {
    project_name = repl(PROJECT_NAME)
    date = repl(DATE)
    project_slug = repl(PROJECT_SLUG)
    project_prefix = repl(PROJECT_PREFIX)
    target_dir = repl(TARGET_DIR)
    session_goal = repl(SESSION_GOAL)
    direction = repl(DIRECTION)
    handoff = repl(HANDOFF)
    success_criteria = repl(SUCCESS_CRITERIA)
    constraints = repl(CONSTRAINTS)
    known_context = repl(KNOWN_CONTEXT)
    agent_style = repl(AGENT_STYLE)
    open_questions = repl(OPEN_QUESTIONS)
  }
  {
    gsub(/\{\{PROJECT_NAME\}\}/, project_name)
    gsub(/\{\{DATE\}\}/, date)
    gsub(/\{\{PROJECT_SLUG\}\}/, project_slug)
    gsub(/\{\{PROJECT_PREFIX\}\}/, project_prefix)
    gsub(/\{\{TARGET_DIR\}\}/, target_dir)
    gsub(/\{\{SESSION_GOAL\}\}/, session_goal)
    gsub(/\{\{DIRECTION\}\}/, direction)
    gsub(/\{\{HANDOFF\}\}/, handoff)
    gsub(/\{\{SUCCESS_CRITERIA\}\}/, success_criteria)
    gsub(/\{\{CONSTRAINTS\}\}/, constraints)
    gsub(/\{\{KNOWN_CONTEXT\}\}/, known_context)
    gsub(/\{\{AGENT_STYLE\}\}/, agent_style)
    gsub(/\{\{OPEN_QUESTIONS\}\}/, open_questions)
    print
  }
  ' "$TEMPLATE" > "$OUTPUT"

echo "✓ wrote ${OUTPUT#$TARGET/}"
