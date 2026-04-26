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
  --mode TEXT                 Session posture / working mode
  --priorities TEXT           Priority checklist
  --risk TEXT                 Risk posture
  --depth TEXT                Discovery depth
  --deliverables TEXT         Expected deliverables checklist
  --handoff-audience TEXT     Who the handoff is for
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
  --yes                       Skip interactive confirmation
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

interactive() {
  [ "$NO_PROMPT" -eq 0 ] && [ -t 0 ]
}

print_banner() {
  interactive || return 0
  cat >&2 <<'EOF'

+------------------------------------------------------------+
| DELIVERY WORKBENCH :: SESSION INTAKE                       |
| Aim the work before the repo archaeology starts.            |
+------------------------------------------------------------+

EOF
}

prompt_choice() {
  label="$1"
  current="$2"
  placeholder="$3"
  shift 3

  if [ -n "$current" ]; then
    printf '%s\n' "$current"
    return
  fi

  if interactive; then
    printf '\n%s\n' "$label" >&2
    index=1
    for option in "$@"; do
      printf '  %d. %s\n' "$index" "$option" >&2
      index=$((index + 1))
    done
    printf '> ' >&2
    IFS= read -r answer || answer=""
    if [ -n "$answer" ]; then
      case "$answer" in
        ''|*[!0-9]*)
          printf '%s\n' "$answer"
          return
          ;;
        *)
          index=1
          for option in "$@"; do
            if [ "$answer" -eq "$index" ]; then
              printf '%s\n' "$option"
              return
            fi
            index=$((index + 1))
          done
          printf '%s\n' "$answer"
          return
          ;;
      esac
    fi
  fi

  printf '%s\n' "$placeholder"
}

prompt_checkboxes() {
  label="$1"
  current="$2"
  placeholder="$3"
  shift 3

  if [ -n "$current" ]; then
    printf '%s\n' "$current"
    return
  fi

  if interactive; then
    printf '\n%s\n' "$label" >&2
    printf 'Select numbers separated by spaces or commas. Press Enter to skip.\n' >&2
    index=1
    for option in "$@"; do
      printf '  [ ] %d. %s\n' "$index" "$option" >&2
      index=$((index + 1))
    done
    printf '> ' >&2
    IFS= read -r answer || answer=""
    if [ -n "$answer" ]; then
      selected=""
      normalized="$(printf '%s\n' "$answer" | tr ',' ' ')"
      case "$normalized" in
        *[!0-9[:space:]]*)
          printf -- '- [x] %s\n' "$answer"
          return
          ;;
      esac
      for token in $normalized; do
        index=1
        for option in "$@"; do
          if [ "$token" -eq "$index" ]; then
            selected="${selected}- [x] $option
"
            break
          fi
          index=$((index + 1))
        done
      done
      if [ -n "$selected" ]; then
        printf '%s' "$selected"
        return
      fi
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

render_template() {
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      "{{SESSION_MODE}}") render_block "$SESSION_MODE" ;;
      "{{SESSION_PRIORITIES}}") render_block "$SESSION_PRIORITIES" ;;
      "{{RISK_POSTURE}}") render_block "$RISK_POSTURE" ;;
      "{{DISCOVERY_DEPTH}}") render_block "$DISCOVERY_DEPTH" ;;
      "{{EXPECTED_DELIVERABLES}}") render_block "$EXPECTED_DELIVERABLES" ;;
      "{{SESSION_GOAL}}") render_block "$SESSION_GOAL" ;;
      "{{DIRECTION}}") render_block "$DIRECTION" ;;
      "{{HANDOFF}}") render_block "$HANDOFF" ;;
      "{{SUCCESS_CRITERIA}}") render_block "$SUCCESS_CRITERIA" ;;
      "{{CONSTRAINTS}}") render_block "$CONSTRAINTS" ;;
      "{{KNOWN_CONTEXT}}") render_block "$KNOWN_CONTEXT" ;;
      "{{AGENT_STYLE}}") render_block "$AGENT_STYLE" ;;
      "{{OPEN_QUESTIONS}}") render_block "$OPEN_QUESTIONS" ;;
      *)
        line="${line//\{\{PROJECT_NAME\}\}/$PROJECT_NAME}"
        line="${line//\{\{DATE\}\}/$DATE}"
        line="${line//\{\{PROJECT_SLUG\}\}/$PROJECT_SLUG}"
        line="${line//\{\{PROJECT_PREFIX\}\}/$PROJECT_PREFIX}"
        line="${line//\{\{TARGET_DIR\}\}/$TARGET}"
        line="${line//\{\{HANDOFF_AUDIENCE\}\}/$HANDOFF_AUDIENCE}"
        printf '%s\n' "$line"
        ;;
    esac
  done < "$TEMPLATE"
}

confirm_intake() {
  interactive || return 0
  [ "$YES" -eq 0 ] || return 0

  cat >&2 <<EOF

Review
------
Mode:        $SESSION_MODE
Risk:        $RISK_POSTURE
Depth:       $DISCOVERY_DEPTH
Handoff to:  $HANDOFF_AUDIENCE
Goal:        $SESSION_GOAL

Write this intake to:
  $OUTPUT

EOF
  printf 'Continue? [Y/n] ' >&2
  IFS= read -r answer || answer=""
  case "$answer" in
    n|N|no|NO|No)
      echo "session-intake.sh: cancelled" >&2
      exit 2
      ;;
  esac
}

TARGET=""
PROJECT_NAME=""
PROJECT_SLUG=""
PROJECT_PREFIX=""
SESSION_MODE=""
SESSION_PRIORITIES=""
RISK_POSTURE=""
DISCOVERY_DEPTH=""
EXPECTED_DELIVERABLES=""
HANDOFF_AUDIENCE=""
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
YES=0
NO_PROMPT=0

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --project-name) PROJECT_NAME="$2"; shift 2 ;;
    --project-slug) PROJECT_SLUG="$2"; shift 2 ;;
    --project-prefix) PROJECT_PREFIX="$2"; shift 2 ;;
    --mode) SESSION_MODE="$2"; shift 2 ;;
    --priorities) SESSION_PRIORITIES="$2"; shift 2 ;;
    --risk) RISK_POSTURE="$2"; shift 2 ;;
    --depth) DISCOVERY_DEPTH="$2"; shift 2 ;;
    --deliverables) EXPECTED_DELIVERABLES="$2"; shift 2 ;;
    --handoff-audience) HANDOFF_AUDIENCE="$2"; shift 2 ;;
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
    --yes) YES=1; shift ;;
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

print_banner
if interactive; then
  printf 'Project: %s  |  slug: %s  |  prefix: %s\n' "$PROJECT_NAME" "$PROJECT_SLUG" "$PROJECT_PREFIX" >&2
fi

SESSION_MODE=$(prompt_choice "What kind of session is this?" "$SESSION_MODE" "- not provided" \
  "Discovery first: understand the repo before changing direction" \
  "Roadmap first: turn known intent into phases and first stories" \
  "Delivery slice: identify and execute the next valuable change" \
  "Handoff/rescue: make the current state legible for the next agent")
SESSION_PRIORITIES=$(prompt_checkboxes "What should this session optimize for?" "$SESSION_PRIORITIES" "- not provided" \
  "Preserve existing behavior" \
  "Find the highest-value next slice" \
  "Create a durable handoff" \
  "Clarify architecture and source canon" \
  "Reduce operational or delivery risk" \
  "Prepare an open-source presentation")
RISK_POSTURE=$(prompt_choice "How cautious should the agent be?" "$RISK_POSTURE" "- not provided" \
  "Read-only until the plan is explicit" \
  "Small edits are fine after discovery" \
  "Move decisively, but keep validation tight" \
  "Ask before any file changes")
DISCOVERY_DEPTH=$(prompt_choice "How deep should discovery go before proposing work?" "$DISCOVERY_DEPTH" "- not provided" \
  "Fast scan: enough to pick the next step" \
  "Standard: repo map, commands, risks, first stories" \
  "Deep: architecture, workflows, tests, roadmap, contracts")
EXPECTED_DELIVERABLES=$(prompt_checkboxes "What handoff artifacts should exist by the end?" "$EXPECTED_DELIVERABLES" "- not provided" \
  "Adoption report" \
  "Immediate session plan" \
  "Phase index" \
  "First story backlog" \
  "Validation command list" \
  "Contract extension recommendations")
SESSION_GOAL=$(prompt_if_blank "What do you want done in this session?" "$SESSION_GOAL" "- not provided")
DIRECTION=$(prompt_if_blank "What direction should the roadmap steer toward?" "$DIRECTION" "- not provided")
HANDOFF_AUDIENCE=$(prompt_choice "Who is the handoff primarily for?" "$HANDOFF_AUDIENCE" "- not provided" \
  "Future agent" \
  "Human maintainer" \
  "Architect / tech lead" \
  "Open-source reader" \
  "Mixed audience")
HANDOFF=$(prompt_if_blank "What should a good handoff include?" "$HANDOFF" "- not provided")
SUCCESS_CRITERIA=$(prompt_if_blank "What evidence would make this session successful?" "$SUCCESS_CRITERIA" "- not provided")
CONSTRAINTS=$(prompt_if_blank "Any constraints or non-goals?" "$CONSTRAINTS" "- not provided")
KNOWN_CONTEXT=$(prompt_if_blank "Any context the agent must not miss?" "$KNOWN_CONTEXT" "- not provided")
AGENT_STYLE=$(prompt_if_blank "Preferred agent/execution style?" "$AGENT_STYLE" "- not provided")
OPEN_QUESTIONS=$(prompt_if_blank "Questions to resolve before roadmapping?" "$OPEN_QUESTIONS" "- not provided")

confirm_intake

mkdir -p "$DISCOVERY_DIR"
DATE="$(date +%Y-%m-%d)"

render_template > "$OUTPUT"

echo "✓ wrote ${OUTPUT#$TARGET/}"
