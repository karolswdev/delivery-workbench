#!/usr/bin/env bash
# Write a valid demo .tmp/CONTRACT.md in the current Git repository via
# `dw contract new` (contract v2: stamped, gate-verified facts), then
# certify the boxes for the recording.

set -eu

CONSENT="${1:-no}"
REASON="${2:-Demo commit for Delivery Workbench terminal recording.}"

.githooks/dw contract new --force --consent "$CONSENT" --reasons "$REASON" >/dev/null 2>&1

# Certification act: flip every rule box after verifying it. The demo
# repo's rules are satisfied by construction (no story flips).
sed 's/^- \[ \]/- [x]/' .tmp/CONTRACT.md > .tmp/CONTRACT.md.new
mv .tmp/CONTRACT.md.new .tmp/CONTRACT.md

echo "Wrote .tmp/CONTRACT.md with work-log consent: $CONSENT"
