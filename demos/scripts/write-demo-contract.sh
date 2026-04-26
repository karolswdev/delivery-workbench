#!/usr/bin/env bash
# Write a valid demo .tmp/CONTRACT.md in the current Git repository.

set -eu

CONSENT="${1:-no}"
REASON="${2:-Demo commit for Delivery Workbench terminal recording.}"
BRANCH="$(git branch --show-current 2>/dev/null || echo demo)"
GENERATED="$(date '+%Y-%m-%d %H:%M')"

mkdir -p .tmp

{
  echo "# Commit Contract"
  echo
  echo "**Generated:** $GENERATED"
  echo "**Branch:** $BRANCH"
  echo "**Staged files (sample):**"
  git diff --cached --name-only | sed -n '1,5s/^/- /p'
  echo
  echo "I certify, for this commit:"
  echo
  echo "- [x] **Evidence, not vibes.** Demo evidence is the terminal run itself."
  echo "- [x] **Master docs updated.** No roadmap story ships in this demo commit."
  echo "- [x] **Tests ran.** Demo validation is the hook execution shown on screen."
  echo "- [x] **Greenfield discipline (if applicable).** No compatibility ceremony added."
  echo "- [x] **No bypasses.** The commit uses the installed hook, not --no-verify."
  echo "- [x] **Story -> evidence pairing.** No story status flips to done."
  echo "- [x] **One PR per story.** This is one atomic demo change."
  echo
  echo "Methodology: pm/roadmap/roadmap-builder.md"
  echo "Rules canon: pm/roadmap/PMO-CONTRACT.md"
  echo
  echo "## Work-log consent"
  echo
  echo "**Work-log consent:** $CONSENT"
  echo
  echo "**Work-log reasons:**"
  echo "- $REASON"
  echo
  echo "**Work-log exclusions:**"
  echo "- none"
} > .tmp/CONTRACT.md

echo "Wrote .tmp/CONTRACT.md with work-log consent: $CONSENT"
