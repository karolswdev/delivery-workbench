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

if "$DW" --root "$REPO" story status sample 0 SMP-0-01 "done" >/dev/null 2>&1; then
  fail "story status done should require paired evidence"
fi
"$DW" --root "$REPO" story status sample 0 SMP-0-01 "done" \
  --evidence-body "- CLI integration evidence." >/dev/null
grep -Fq -- '- **Status:** done' "$PROJECT/phase-0-setup-cli/story-01-create-first-story.md" \
  || fail "story status should update story header"
grep -Fq 'SMP-0-01 | Create first story | done' "$PROJECT/phase-0-setup-cli/current-phase-status.md" \
  || fail "story status should update phase table"
[ -f "$PROJECT/phase-0-setup-cli/evidence-story-01.md" ] \
  || fail "story status done should create paired evidence when body is provided"
before="$(cksum "$PROJECT/phase-0-setup-cli/story-01-create-first-story.md" "$PROJECT/phase-0-setup-cli/current-phase-status.md" "$PROJECT/phase-0-setup-cli/evidence-story-01.md")"
"$DW" --root "$REPO" story status sample 0 SMP-0-01 "done" >/dev/null
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
"$DW" --root "$REPO" story status sample 1 SMP-1-01 "done" >/dev/null
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
# shellcheck disable=SC2016  # the $i belongs to the captured sh -c script
"$DW" --root "$REPO" evidence capture sample 2 SMP-2-01 --max-output-bytes 16 \
  -- sh -c 'i=0; while [ $i -lt 40 ]; do echo oversized; i=$((i+1)); done' >/dev/null
grep -q 'PMO_EVIDENCE_OUTPUT_TRUNCATED' "$EV" || fail "oversized output should carry the truncation marker"
"$DW" --root "$REPO" story status sample 2 SMP-2-01 "done" >/dev/null
"$DW" --root "$REPO" phase close sample 2 --summary "Capture phase closed." >/dev/null
"$DW" --root "$REPO" check sample | grep -q 'dw check: ok' || fail "captured evidence should lint clean"

"$DW" --root "$REPO" phase create sample 3 "Lint" \
  --goal "Exercise evidence content lints." >/dev/null
"$DW" --root "$REPO" story create sample 3 "Placeholder story" >/dev/null
"$DW" --root "$REPO" story evidence sample 3 SMP-3-01 >/dev/null
"$DW" --root "$REPO" story status sample 3 SMP-3-01 "done" >/dev/null
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

# ── One-answer status briefing (WLA-22-02) ──────────────────────────

STATUS_REPO="$TMP_ROOT/status-repo"
mkdir -p "$STATUS_REPO"
git -C "$STATUS_REPO" init -q -b main
git -C "$STATUS_REPO" config user.name "Status Integration"
git -C "$STATUS_REPO" config user.email "status@example.test"
"$PMO_DIR/install.sh" "$STATUS_REPO" \
  --project-name "Status Demo" --project-slug status-demo \
  --project-prefix SD >/dev/null
git -C "$STATUS_REPO" add -A
git -C "$STATUS_REPO" commit -q --no-verify -m "fixture scaffold"
STATUS_DW="$STATUS_REPO/.githooks/dw"

"$STATUS_DW" --root "$STATUS_REPO" status status-demo --json > "$TMP_ROOT/status-a.json"
"$STATUS_DW" --root "$STATUS_REPO" status status-demo --json > "$TMP_ROOT/status-b.json"
cmp "$TMP_ROOT/status-a.json" "$TMP_ROOT/status-b.json" \
  || fail "status JSON should be byte-stable over unchanged state"
python3 - "$TMP_ROOT/status-a.json" <<'PY' || fail "status should guide a clean installed repo"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    status = json.load(f)
assert status["kind"] == "delivery-workbench-status"
assert status["schema_version"] == 1
assert status["verdict"] == "ready"
assert status["repository"]["clean"] is True
assert status["rails"]["healthy"] is True
assert status["roadmap"]["selected_project"] == "status-demo"
assert status["next_action"]["id"] == "start-story"
assert status["next_action"]["command"] == [
    ".githooks/dw", "story", "status", "status-demo", "0",
    "SD-0-01", "in-progress",
]
assert status["actions"] == [status["next_action"]]
PY
"$STATUS_DW" --root "$STATUS_REPO" status status-demo > "$TMP_ROOT/status-human.txt"
grep -q '^Delivery is ready$' "$TMP_ROOT/status-human.txt" \
  || fail "human status should lead with delivery readiness"
grep -q '^Start current work:' "$TMP_ROOT/status-human.txt" \
  || fail "human status should explain the same next action"
grep -q '^Technical details:$' "$TMP_ROOT/status-human.txt" \
  || fail "human status should preserve an explicit technical boundary"
grep -q '^  Command: .githooks/dw story status status-demo 0 SD-0-01 in-progress$' \
  "$TMP_ROOT/status-human.txt" \
  || fail "human status should keep the exact command copyable"

# Attention is a valid JSON briefing with exit 1, not an empty failure.
mv "$STATUS_REPO/.githooks/pre-commit" "$STATUS_REPO/.githooks/pre-commit.off"
if "$STATUS_DW" --root "$STATUS_REPO" status status-demo --json > "$TMP_ROOT/status-attention.json"; then
  fail "broken required wiring should make status exit 1"
fi
python3 - "$TMP_ROOT/status-attention.json" <<'PY' || fail "attention briefing should name repair"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    status = json.load(f)
assert status["verdict"] == "attention"
assert status["next_action"]["id"] == "repair-rails"
assert status["next_action"]["blocking"] is True
PY
"$STATUS_DW" --root "$STATUS_REPO" step status-demo --json > "$TMP_ROOT/repair-step.json"
REPAIR_TOKEN="$(python3 - "$TMP_ROOT/repair-step.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    step = json.load(f)
assert step["action"]["id"] == "repair-rails"
assert step["applicable"] is True
print(step["token"])
PY
)"
if "$STATUS_DW" --root "$STATUS_REPO" step status-demo --json \
  --apply --expect "$REPAIR_TOKEN" >"$TMP_ROOT/repair-result.json"; then
  fail "step should mirror a failing allowlisted child"
fi
python3 - "$TMP_ROOT/repair-result.json" <<'PY' \
  || fail "failed JSON step should return a truthful bounded receipt"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    result = json.load(f)
assert result["kind"] == "delivery-workbench-step-result"
assert result["schema_version"] == 1
assert result["outcome"] == "failed"
assert result["started"] is True
assert result["exit_code"] == 1
assert result["action"]["id"] == "repair-rails"
assert result["before"]["action_id"] == "repair-rails"
assert result["after"]["action_id"] == "repair-rails"
assert result["before"]["token"] != result["after"]["token"]
assert result["output"]["truncated"] == {"stdout": False, "stderr": False}
assert "FAIL" in result["output"]["stdout"]
PY
mv "$STATUS_REPO/.githooks/pre-commit.off" "$STATUS_REPO/.githooks/pre-commit"

# ── Deliberate one-step handrail (WLA-23-01) ────────────────────────

git -C "$STATUS_REPO" status --porcelain=v1 -z > "$TMP_ROOT/step-state-before"
"$STATUS_DW" --root "$STATUS_REPO" step status-demo --json > "$TMP_ROOT/step-a.json"
"$STATUS_DW" --root "$STATUS_REPO" step status-demo --json > "$TMP_ROOT/step-b.json"
git -C "$STATUS_REPO" status --porcelain=v1 -z > "$TMP_ROOT/step-state-after"
cmp "$TMP_ROOT/step-a.json" "$TMP_ROOT/step-b.json" \
  || fail "step preview JSON should be byte-stable over unchanged state"
cmp "$TMP_ROOT/step-state-before" "$TMP_ROOT/step-state-after" \
  || fail "step preview should not mutate the installed repository"
python3 - "$TMP_ROOT/step-a.json" <<'PY' || fail "step should preview the exact installed action"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    step = json.load(f)
assert sorted(step) == [
    "action", "applicable", "apply_command", "kind", "project",
    "refusal", "schema_version", "token",
]
assert step["kind"] == "delivery-workbench-step"
assert step["schema_version"] == 1
assert step["project"] == "status-demo"
assert step["action"]["id"] == "start-story"
assert step["action"]["command"] == [
    ".githooks/dw", "story", "status", "status-demo", "0",
    "SD-0-01", "in-progress",
]
assert step["applicable"] is True
assert step["refusal"] is None
assert step["token"].startswith("sha256:") and len(step["token"]) == 71
assert step["apply_command"] == [
    ".githooks/dw", "step", "status-demo", "--apply", "--expect",
    step["token"],
]
PY
STEP_TOKEN="$(python3 - "$TMP_ROOT/step-a.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f)["token"])
PY
)"
if "$STATUS_DW" --root "$STATUS_REPO" step status-demo --json \
  --apply > "$TMP_ROOT/missing-token-result.json"; then
  fail "step apply should require an expected preview token"
fi
python3 - "$TMP_ROOT/missing-token-result.json" <<'PY' \
  || fail "missing-token apply should be a pinned non-started refusal"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    result = json.load(f)
assert result["outcome"] == "refused"
assert result["started"] is False
assert result["exit_code"] == 1
assert result["after"] is None
assert result["output"] == {
    "stdout": "", "stderr": "",
    "truncated": {"stdout": False, "stderr": False},
}
assert "requires --expect" in result["reason"]
PY
if "$STATUS_DW" --root "$STATUS_REPO" step status-demo --expect "$STEP_TOKEN" >/dev/null 2>&1; then
  fail "step expect should only be accepted with apply"
fi

# Moving only HEAD leaves the same recommendation, but invalidates the lease.
git -C "$STATUS_REPO" commit -q --allow-empty --no-verify -m "move step fixture head"
if "$STATUS_DW" --root "$STATUS_REPO" step status-demo --json \
  --apply --expect "$STEP_TOKEN" >"$TMP_ROOT/stale-result.json"; then
  fail "step should refuse a stale token even when the action id is unchanged"
fi
python3 - "$TMP_ROOT/stale-result.json" <<'PY' \
  || fail "stale step refusal should explain recovery without starting"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    result = json.load(f)
assert result["outcome"] == "refused"
assert result["started"] is False
assert result["after"] is None
assert "step token is stale" in result["reason"]
PY
"$STATUS_DW" --root "$STATUS_REPO" status status-demo --json > "$TMP_ROOT/status-after-stale.json"
python3 - "$TMP_ROOT/status-after-stale.json" <<'PY' \
  || fail "stale refusal should happen before the child action"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    status = json.load(f)
assert status["next_action"]["id"] == "start-story"
PY

"$STATUS_DW" --root "$STATUS_REPO" step status-demo --json > "$TMP_ROOT/step-fresh.json"
STEP_TOKEN="$(python3 - "$TMP_ROOT/step-fresh.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f)["token"])
PY
)"
"$STATUS_DW" --root "$STATUS_REPO" step status-demo --json \
  --apply --expect "$STEP_TOKEN" > "$TMP_ROOT/step-success.json"
python3 - "$TMP_ROOT/step-success.json" <<'PY' \
  || fail "successful JSON step should return the shared result receipt"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    result = json.load(f)
assert sorted(result) == [
    "action", "after", "before", "exit_code", "kind", "outcome",
    "output", "project", "reason", "schema_version", "started",
]
assert result["outcome"] == "succeeded"
assert result["started"] is True
assert result["exit_code"] == 0
assert result["reason"] is None
assert result["before"]["action_id"] == "start-story"
assert result["after"]["action_id"] == "continue-story"
assert result["before"]["token"] != result["after"]["token"]
assert "SD-0-01" in result["output"]["stdout"]
assert result["output"]["stderr"] == ""
PY
"$STATUS_DW" --root "$STATUS_REPO" status status-demo --json > "$TMP_ROOT/status-after-step.json"
python3 - "$TMP_ROOT/status-after-step.json" <<'PY' \
  || fail "applied step should perform exactly the previewed transition"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    status = json.load(f)
assert status["next_action"]["id"] == "continue-story"
assert status["roadmap"]["projects"][0]["next_story"]["status"] == "in-progress"
PY

# A read-only action still consumes its lease: a new preview is required.
"$STATUS_DW" --root "$STATUS_REPO" step status-demo --json > "$TMP_ROOT/read-step.json"
READ_TOKEN="$(python3 - "$TMP_ROOT/read-step.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f)["token"])
PY
)"
"$STATUS_DW" --root "$STATUS_REPO" step status-demo \
  --apply --expect "$READ_TOKEN" > "$TMP_ROOT/read-step.out"
grep -q '^Delivery step complete$' "$TMP_ROOT/read-step.out" \
  || fail "human apply should report the delivery outcome"
grep -q '^Continue current work:' "$TMP_ROOT/read-step.out" \
  || fail "human apply should name the reloaded next step"
grep -q '^Technical details:$' "$TMP_ROOT/read-step.out" \
  || fail "human apply should stop after one read-only child"
if "$STATUS_DW" --root "$STATUS_REPO" step status-demo --json \
  --apply --expect "$READ_TOKEN" > "$TMP_ROOT/replay-result.json"; then
  fail "an already consumed read-only lease should not replay"
fi
python3 - "$TMP_ROOT/replay-result.json" "$STATUS_REPO/.git/pmo-events.jsonl" <<'PY' \
  || fail "replay refusal should emit no additional step event"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    result = json.load(f)
with open(sys.argv[2], encoding="utf-8") as f:
    events = [json.loads(line) for line in f if line.strip()]
step_events = [event for event in events if event["event"] == "step_execution"]
assert result["outcome"] == "refused"
assert result["started"] is False
assert "token is stale" in result["reason"]
assert len(step_events) == 3  # failing doctor, start story, read-only story show
for event in step_events:
    assert sorted(event["detail"]) == [
        "action", "after", "before", "exit_code", "next_action", "outcome",
    ]
event_text = open(sys.argv[2], encoding="utf-8").read()
assert "Status Demo" not in event_text
assert "### story" not in event_text
PY

echo "roadmap-cli.sh: ok"
