#!/usr/bin/env bash
# Integration coverage for the Delivery Workbench roadmap CLI.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/dw-cli-test.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "roadmap-cli.sh: $1" >&2
  exit 1
}

REPO="$TMP_ROOT/repo"
PROJECT="$REPO/pm/roadmap/sample"
mkdir -p "$PROJECT"

cat > "$PROJECT/README.md" <<'EOF'
# Sample - Roadmap

**Last updated:** 2026-07-01.
**Current phase:** n/a.
**Status:** planning.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|

## Project metadata

- **Slug:** `sample`
- **Story ID prefix:** `SMP`
EOF

DW="$PMO_DIR/bin/dw"
python3 -m py_compile "$DW"

"$DW" --root "$REPO" projects | grep -q $'sample\tSMP' || fail "projects should list sample project"

"$DW" --root "$REPO" phase create sample 0 "Setup CLI" \
  --goal "Prepare CLI-managed roadmap." >/dev/null
[ -f "$PROJECT/phase-0-setup-cli/current-phase-status.md" ] || fail "phase create should write status file"
grep -q 'phase-0-setup-cli' "$PROJECT/README.md" || fail "phase create should update project phase index"

"$DW" --root "$REPO" story create sample 0 "Create first story" >/dev/null
[ -f "$PROJECT/phase-0-setup-cli/story-01-create-first-story.md" ] || fail "story create should write story file"
grep -q 'SMP-0-01' "$PROJECT/phase-0-setup-cli/current-phase-status.md" || fail "story create should update story table"

"$DW" --root "$REPO" tree sample | grep -q 'SMP-0-01 \[backlog\] evidence:no Create first story' \
  || fail "tree should show story status and evidence presence"
"$DW" --root "$REPO" story list sample --phase 0 | grep -q $'SMP-0-01\tbacklog' \
  || fail "story list should include created story"
"$DW" --root "$REPO" next sample | grep -q $'SMP-0-01\tbacklog' \
  || fail "next should select first backlog story"
"$DW" --root "$REPO" check sample | grep -q 'dw check: ok' || fail "check should pass generated roadmap"
"$DW" --root "$REPO" context sample > "$TMP_ROOT/context.json"
python3 - "$TMP_ROOT/context.json" <<'PY' || fail "context should expose machine-readable roadmap state"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    payload = json.load(f)

project = payload["projects"][0]
story = project["phases"][0]["stories"][0]
assert payload["kind"] == "delivery-workbench-roadmap-context"
assert project["slug"] == "sample"
assert project["issues"] == []
assert project["next_story"]["story_id"] == "SMP-0-01"
assert story["story_id"] == "SMP-0-01"
assert story["status"] == "backlog"
assert story["evidence_exists"] is False
assert story["trace"]["story"].endswith("story-01-create-first-story.md")
PY
"$DW" --root "$REPO" context sample --trace > "$TMP_ROOT/context-trace-a.json"
"$DW" --root "$REPO" context sample --trace > "$TMP_ROOT/context-trace-b.json"
cmp "$TMP_ROOT/context-trace-a.json" "$TMP_ROOT/context-trace-b.json" \
  || fail "read-only context should be idempotent"

if "$DW" --root "$REPO" story status sample 0 SMP-0-01 done >/dev/null 2>&1; then
  fail "story status done should require paired evidence"
fi
"$DW" --root "$REPO" story status sample 0 SMP-0-01 done \
  --evidence-body "- CLI integration evidence." >/dev/null
grep -Fq -- '- **Status:** done' "$PROJECT/phase-0-setup-cli/story-01-create-first-story.md" \
  || fail "story status should update story header"
grep -Fq 'SMP-0-01 | Create first story | done' "$PROJECT/phase-0-setup-cli/current-phase-status.md" \
  || fail "story status should update phase table"
[ -f "$PROJECT/phase-0-setup-cli/evidence-story-01.md" ] \
  || fail "story status done should create paired evidence when body is provided"
before="$(cksum "$PROJECT/phase-0-setup-cli/story-01-create-first-story.md" "$PROJECT/phase-0-setup-cli/current-phase-status.md" "$PROJECT/phase-0-setup-cli/evidence-story-01.md")"
"$DW" --root "$REPO" story status sample 0 SMP-0-01 done >/dev/null
after="$(cksum "$PROJECT/phase-0-setup-cli/story-01-create-first-story.md" "$PROJECT/phase-0-setup-cli/current-phase-status.md" "$PROJECT/phase-0-setup-cli/evidence-story-01.md")"
[ "$before" = "$after" ] || fail "same-status write should be idempotent"
if "$DW" --root "$REPO" check sample >/dev/null 2>&1; then
  fail "check should require final summary when all stories are done"
fi
"$DW" --root "$REPO" phase close sample 0 --summary "Closed by roadmap-cli.sh." >/dev/null
"$DW" --root "$REPO" check sample | grep -q 'dw check: ok' || fail "check should pass after phase close"

"$DW" --root "$REPO" phase create sample 1 "Evidence attach" \
  --goal "Exercise standalone evidence and phase close invariants." >/dev/null
"$DW" --root "$REPO" story create sample 1 "Attach evidence separately" >/dev/null
if "$DW" --root "$REPO" phase close sample 1 --summary "Should not close." >/dev/null 2>&1; then
  fail "phase close should refuse open stories"
fi
"$DW" --root "$REPO" story evidence sample 1 SMP-1-01 \
  --body "- Standalone evidence detail." >/dev/null
[ -f "$PROJECT/phase-1-evidence-attach/evidence-story-01.md" ] \
  || fail "story evidence should create paired evidence"
if "$DW" --root "$REPO" check sample >/dev/null 2>&1; then
  fail "check should catch evidence attached before story is done"
fi
"$DW" --root "$REPO" story status sample 1 SMP-1-01 done >/dev/null
if "$DW" --root "$REPO" check sample >/dev/null 2>&1; then
  fail "check should require final summary for second complete phase"
fi
"$DW" --root "$REPO" phase close sample 1 --summary "Closed second test phase." >/dev/null
"$DW" --root "$REPO" check sample | grep -q 'dw check: ok' || fail "check should pass after second phase close"

mkdir -p "$TMP_ROOT/work-log/2026-07-01"
cat > "$TMP_ROOT/work-log/2026-07-01/sample-123-work-summary.log" <<'EOF'
---
kind: pmo-work-log-entry
schema_version: 1
timestamp: 2026-07-01T00:00:00Z
project: sample
commit: abc123
---

## Commit

- **Subject:** SMP-0-01 Create first story
EOF
PMO_WORK_LOG_DIR="$TMP_ROOT/work-log" "$DW" --root "$REPO" context sample --trace > "$TMP_ROOT/context-worklog.json"
python3 - "$TMP_ROOT/context-worklog.json" <<'PY' || fail "trace context should include work-log entries where available"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    payload = json.load(f)
project = payload["projects"][0]
story = project["phases"][0]["stories"][0]
assert project["work_logs"]
assert story["work_log_entries"]
assert story["work_log_entries"][0]["commit"] == "abc123"
assert project["phases"][0]["active"] is False
PY

DRIFT="$REPO/pm/roadmap/drift"
mkdir -p "$DRIFT/phase-0-one" "$DRIFT/phase-1-two" "$REPO/.githooks"
cat > "$REPO/.githooks/pre-commit" <<'EOF'
#!/usr/bin/env bash
# older hook snapshot without config/local/work-log seams
echo old
EOF
cat > "$DRIFT/README.md" <<'EOF'
# Drift - Roadmap

**Last updated:** 2026-07-01.
**Current phase:** [phase-9-missing](./phase-9-missing/current-phase-status.md)
**Status:** active.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 0 | First open phase | in-progress | [phase-0-one](./phase-0-one/) |
| 1 | Second open phase | in-progress | [phase-1-two](./phase-1-two/) |

## Project metadata

- **Slug:** `drift`
- **Story ID prefix:** `DRF`
EOF
cat > "$DRIFT/MASTER-EXECUTION.md" <<'EOF'
# Master Execution

Supplemental orchestrator file.
EOF
for n in 0 1; do
  cat > "$DRIFT/phase-$n-$( [ "$n" = 0 ] && echo one || echo two )/current-phase-status.md" <<EOF
# Phase $n

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DRF-$n-01 | Drift story $n | backlog | [story-01-drift](./story-01-drift.md) | - |
EOF
  cat > "$DRIFT/phase-$n-$( [ "$n" = 0 ] && echo one || echo two )/story-01-drift.md" <<EOF
# DRF-$n-01 - Drift story $n

- **Project:** drift
- **Phase:** $n
- **Status:** backlog
EOF
done
"$DW" --root "$REPO" context drift > "$TMP_ROOT/drift-context.json"
python3 - "$TMP_ROOT/drift-context.json" <<'PY' || fail "context should report real-world drift"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    payload = json.load(f)
project = payload["projects"][0]
assert any("current phase pointer is stale" in issue for issue in project["issues"])
assert any("multiple open phases" in warning for warning in project["warnings"])
assert project["hook_snapshot"]["appears_older_snapshot"] is True
assert any(item["kind"] == "orchestrator" for item in project["supplemental_canon"])
PY
if "$DW" --root "$REPO" check drift >/dev/null 2>&1; then
  fail "check should fail stale current phase pointer"
fi

BROKEN="$REPO/pm/roadmap/broken"
mkdir -p "$BROKEN/phase-0-broken"
cat > "$BROKEN/README.md" <<'EOF'
# Broken - Roadmap

**Last updated:** 2026-07-01.
**Current phase:** n/a.
**Status:** active.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 0 | Broken fixture | in-progress | [phase-0-broken](./phase-0-broken/) |

## Project metadata

- **Slug:** `broken`
- **Story ID prefix:** `BKN`
EOF
cat > "$BROKEN/phase-0-broken/current-phase-status.md" <<'EOF'
# Phase 0

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| BKN-0-01 | Broken evidence link | done | [story-01-broken-evidence-link](./story-01-broken-evidence-link.md) | [evidence-story-01](./evidence-story-01.md) |
| BKN-0-02 | Missing evidence link | done | [story-02-missing-evidence-link](./story-02-missing-evidence-link.md) | - |
| BKN-0-04 | Broken story link | backlog | [story-04-missing](./story-04-missing.md) | - |
EOF
cat > "$BROKEN/phase-0-broken/story-01-broken-evidence-link.md" <<'EOF'
# BKN-0-01 - Broken evidence link

- **Project:** broken
- **Phase:** 0
- **Status:** done
EOF
cat > "$BROKEN/phase-0-broken/story-02-missing-evidence-link.md" <<'EOF'
# BKN-0-02 - Missing evidence link

- **Project:** broken
- **Phase:** 0
- **Status:** done
EOF
cat > "$BROKEN/phase-0-broken/evidence-story-03.md" <<'EOF'
# Evidence - BKN-0-03
EOF
if "$DW" --root "$REPO" check broken > "$TMP_ROOT/broken-check.txt" 2>&1; then
  fail "check should fail broken validation fixture"
fi
grep -Fq 'broken evidence link for BKN-0-01' "$TMP_ROOT/broken-check.txt" \
  || fail "check should report broken evidence links"
grep -Fq 'done story BKN-0-02 has no evidence link' "$TMP_ROOT/broken-check.txt" \
  || fail "check should report done stories without evidence links"
grep -Fq 'broken story link for BKN-0-04' "$TMP_ROOT/broken-check.txt" \
  || fail "check should report broken story links"
grep -Fq 'orphan evidence has no matching story row' "$TMP_ROOT/broken-check.txt" \
  || fail "check should report orphan evidence"

sed -i.bak 's/- \*\*Status:\*\* done/- **Status:** backlog/' \
  "$PROJECT/phase-0-setup-cli/story-01-create-first-story.md"
rm -f "$PROJECT/phase-0-setup-cli/story-01-create-first-story.md.bak"
if "$DW" --root "$REPO" check sample >/dev/null 2>&1; then
  fail "check should catch header/table status mismatch"
fi

# ── Evidence capture and content lints (WLA-6-04) ────────────────────

# Undo the deliberate header/table mismatch from the previous assertion.
sed -i.bak 's/- \*\*Status:\*\* backlog/- **Status:** done/' \
  "$PROJECT/phase-0-setup-cli/story-01-create-first-story.md"
rm -f "$PROJECT/phase-0-setup-cli/story-01-create-first-story.md.bak"

"$DW" --root "$REPO" phase create sample 2 "Capture" \
  --goal "Exercise evidence capture." >/dev/null
"$DW" --root "$REPO" story create sample 2 "Capture a run" >/dev/null
"$DW" --root "$REPO" evidence capture sample 2 SMP-2-01 -- sh -c 'echo captured-ok' >/dev/null
EV="$PROJECT/phase-2-capture/evidence-story-01.md"
grep -q '^### Captured run — ' "$EV" || fail "capture should append a captured-run block"
grep -q '\*\*Exit code:\*\* 0' "$EV" || fail "capture should record exit code 0"
grep -q 'captured-ok' "$EV" || fail "capture should record command output"
if "$DW" --root "$REPO" evidence capture sample 2 SMP-2-01 -- sh -c 'exit 7' >/dev/null; then
  fail "capture should mirror the command's nonzero exit code"
fi
grep -q '\*\*Exit code:\*\* 7' "$EV" || fail "nonzero exit should be recorded honestly"
"$DW" --root "$REPO" evidence capture sample 2 SMP-2-01 --max-output-bytes 16 \
  -- sh -c 'i=0; while [ $i -lt 40 ]; do echo oversized; i=$((i+1)); done' >/dev/null
grep -q 'PMO_EVIDENCE_OUTPUT_TRUNCATED' "$EV" || fail "oversized output should carry the truncation marker"
"$DW" --root "$REPO" story status sample 2 SMP-2-01 done >/dev/null
"$DW" --root "$REPO" phase close sample 2 --summary "Capture phase closed." >/dev/null
"$DW" --root "$REPO" check sample | grep -q 'dw check: ok' || fail "captured evidence should lint clean"

"$DW" --root "$REPO" phase create sample 3 "Lint" \
  --goal "Exercise evidence content lints." >/dev/null
"$DW" --root "$REPO" story create sample 3 "Placeholder story" >/dev/null
"$DW" --root "$REPO" story evidence sample 3 SMP-3-01 >/dev/null
"$DW" --root "$REPO" story status sample 3 SMP-3-01 done >/dev/null
if "$DW" --root "$REPO" check sample >/dev/null 2>&1; then
  fail "check should reject placeholder evidence for a done story"
fi
"$DW" --root "$REPO" check sample 2>/dev/null | grep -q 'generator placeholder' \
  || fail "check should name the placeholder lint"
cat > "$PROJECT/phase-3-lint/evidence-story-01.md" <<'EOF'
# Evidence - SMP-3-01

- **Story:** SMP-3-01 - Placeholder story
- **Status:** done
- **Date:** 2026-07-01

## Proof

- proof line with a screenshot: ![shot](./assets/shot.png)
EOF
"$DW" --root "$REPO" check sample 2>/dev/null | grep -q 'broken asset reference' \
  || fail "check should flag missing asset references"
mkdir -p "$PROJECT/phase-3-lint/assets"
printf 'png' > "$PROJECT/phase-3-lint/assets/shot.png"
"$DW" --root "$REPO" phase close sample 3 --summary "Lint phase closed." >/dev/null
"$DW" --root "$REPO" check sample | grep -q 'dw check: ok' || fail "check should pass once the asset exists"

echo "roadmap-cli.sh: ok"
