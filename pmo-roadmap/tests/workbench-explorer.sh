#!/usr/bin/env bash
# Workbench explorer coverage (WLA-5-03): the documented local command
# serves the JSON API and static UI against an explicit repo root,
# read-only — repeated loads leave the roadmap tree checksum-identical,
# non-GET methods are rejected, and the file endpoint refuses traversal.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pmo-workbench-test.XXXXXX")"
SERVER_PID=""

cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "workbench-explorer.sh: $1" >&2
  exit 1
}

# ── fixture repo ─────────────────────────────────────────────────────
REPO="$TMP_ROOT/repo"
PROJECT="$REPO/pm/roadmap/sample"
mkdir -p "$PROJECT"
cat > "$PROJECT/README.md" <<'EOF'
# Sample - Roadmap

**Current phase:** n/a.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|

## Project metadata

- **Slug:** `sample`
- **Story ID prefix:** `SMP`
EOF
DW="$PMO_DIR/bin/dw"
"$DW" --root "$REPO" phase create sample 0 "Explorer Fixture" --goal "Serve me." >/dev/null
"$DW" --root "$REPO" story create sample 0 "First fixture story" >/dev/null
"$DW" --root "$REPO" story status sample 0 SMP-0-01 "done" \
  --evidence-body "- fixture evidence body." >/dev/null
"$DW" --root "$REPO" story create sample 0 "Second fixture story" >/dev/null

# ── start the documented command ─────────────────────────────────────
# Work-log root for the trace tests: exported before start, but the
# directory does not exist yet — traces must degrade cleanly until the
# fixture entry is written further down.
export PMO_WORK_LOG_DIR="$TMP_ROOT/worklog"
PORT=$(( (RANDOM % 2000) + 18000 ))
"$PMO_DIR/bin/dw-workbench" --root "$REPO" --port "$PORT" &
SERVER_PID=$!
i=0
until curl -sf "http://127.0.0.1:$PORT/api/projects" >/dev/null 2>&1; do
  i=$((i + 1))
  [ "$i" -lt 40 ] || fail "server did not come up on port $PORT"
  sleep 0.25
done

BASE="http://127.0.0.1:$PORT"
sum_tree() {
  find "$REPO/pm" -type f -print0 | sort -z | xargs -0 cksum
}
BEFORE="$(sum_tree)"

# ── API view models ──────────────────────────────────────────────────
curl -s "$BASE/api/projects" > "$TMP_ROOT/projects.json"
python3 - "$TMP_ROOT/projects.json" <<'PY' || fail "overview payload wrong"
import json, sys
body = json.load(open(sys.argv[1]))
assert body["kind"] == "delivery-workbench-workbench-response"
assert body["ok"] is True
p = body["data"]["projects"][0]
assert p["slug"] == "sample" and p["prefix"] == "SMP"
assert p["phase_count"] == 1 and p["active_phase_count"] == 1
assert p["story_status_counts"] == {"done": 1, "backlog": 1}
assert p["next_story"]["story_id"] == "SMP-0-02"
PY

curl -s "$BASE/api/projects/sample/phases/0" > "$TMP_ROOT/phase.json"
python3 - "$TMP_ROOT/phase.json" <<'PY' || fail "phase payload wrong"
import json, sys
d = json.load(open(sys.argv[1]))["data"]
assert d["number"] == 0
assert [s["story_id"] for s in d["stories"]] == ["SMP-0-01", "SMP-0-02"]
assert d["stories"][0]["evidence_exists"] is True
assert d["stories"][1]["evidence_exists"] is False
PY

curl -s "$BASE/api/projects/sample/stories/SMP-0-01" > "$TMP_ROOT/story.json"
python3 - "$TMP_ROOT/story.json" <<'PY' || fail "story payload wrong"
import json, sys
d = json.load(open(sys.argv[1]))["data"]
assert d["story_id"] == "SMP-0-01"
assert "First fixture story" in d["story_markdown"]
assert "fixture evidence body" in d["evidence_markdown"]
PY

# ── static shell + supplemental file reads ───────────────────────────
curl -s "$BASE/" | grep -q 'id="app"' || fail "index.html should serve the app shell"
curl -s "$BASE/app.js" | grep -q "read-only" || fail "app.js should be served"
curl -s "$BASE/api/file?path=pm/roadmap/sample/README.md" \
  | grep -q 'Sample - Roadmap' || fail "file endpoint should serve roadmap files"

# ── guards ───────────────────────────────────────────────────────────
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/file?path=../.gitignore")" = "403" ] 2>/dev/null \
  || [ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/file?path=../outside.txt")" = "403" ] \
  || fail "file endpoint should refuse paths outside the roadmap tree"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/context")" = "405" ] \
  || fail "non-GET methods should be rejected"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/../etc/passwd")" = "404" ] \
  || fail "static handler should refuse traversal"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/projects/ghost")" = "400" ] \
  || fail "unknown project should return an error envelope"

# ── read-only across repeated loads (checksums) ──────────────────────
for _ in 1 2 3; do
  curl -s "$BASE/api/context" >/dev/null
  curl -s "$BASE/api/projects" >/dev/null
  curl -s "$BASE/api/projects/sample" >/dev/null
  curl -s "$BASE/api/projects/sample/phases/0" >/dev/null
  curl -s "$BASE/api/projects/sample/stories/SMP-0-01" >/dev/null
done
AFTER="$(sum_tree)"
[ "$BEFORE" = "$AFTER" ] || fail "repeated API loads must not modify the roadmap tree"

# ── health console (WLA-5-04): drift fixture renders all issue kinds ──
DRIFT="$REPO/pm/roadmap/drifty"
mkdir -p "$DRIFT/phase-0-open-a" "$DRIFT/phase-1-open-b"
cat > "$DRIFT/README.md" <<'EOF'
# Drifty - Roadmap

**Current phase:** [phase-9-ghost](./phase-9-ghost/current-phase-status.md)

## Project metadata

- **Slug:** `drifty`
- **Story ID prefix:** `DR`
EOF
cat > "$DRIFT/phase-0-open-a/current-phase-status.md" <<'EOF'
## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DR-0-01 | Broken evidence link | done | [story-01-real](./story-01-real.md) | [evidence-story-01](./evidence-story-01.md) |
| DR-0-02 | No evidence | done | [story-02-real](./story-02-real.md) | - |
| DR-0-03 | Broken story link | done | [story-03-gone](./story-03-gone.md) | - |
| DR-0-04 | Still open here | backlog | [story-04-open](./story-04-open.md) | - |
EOF
printf '# DR-0-01 - Broken evidence link\n\n- **Status:** done\n' > "$DRIFT/phase-0-open-a/story-01-real.md"
printf '# DR-0-04 - Still open here\n\n- **Status:** backlog\n' > "$DRIFT/phase-0-open-a/story-04-open.md"
printf '# DR-0-02 - No evidence\n\n- **Status:** done\n' > "$DRIFT/phase-0-open-a/story-02-real.md"
printf '# stray\n' > "$DRIFT/phase-0-open-a/evidence-story-07.md"
cat > "$DRIFT/phase-1-open-b/current-phase-status.md" <<'EOF'
## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| DR-1-01 | Second open phase | backlog | [story-01-b](./story-01-b.md) | - |
EOF
printf '# DR-1-01 - Second open phase\n\n- **Status:** backlog\n' > "$DRIFT/phase-1-open-b/story-01-b.md"

curl -s "$BASE/api/health" > "$TMP_ROOT/health.json"
python3 - "$TMP_ROOT/health.json" <<'PY' || fail "health payload wrong"
import json, sys
d = json.load(open(sys.argv[1]))["data"]
assert d["mutation_safe"] is False
drifty = [p for p in d["projects"] if p["slug"] == "drifty"][0]
kinds = {i["kind"] for i in drifty["issues"]}
for expected in ("stale-pointer", "broken-story-link", "missing-evidence-link",
                 "broken-evidence-link", "orphan-evidence"):
    assert expected in kinds, f"missing issue kind {expected}: {kinds}"
warns = {w["kind"]: w for w in drifty["warnings"]}
assert "multiple-open-phases" in warns
assert warns["multiple-open-phases"]["phase_folders"] == ["phase-0-open-a", "phase-1-open-b"]
assert any(i["kind"] == "stale-pointer" and "explanation" in i for i in drifty["issues"])
assert "ERROR" in d["check_output"]
assert "hook_explanations" in d and "work_log_config" in d
sample = [p for p in d["projects"] if p["slug"] == "sample"][0]
assert sample["mutation_safe"] is True
PY
rm -rf "$DRIFT"

# ── traceability timeline (WLA-5-05) ─────────────────────────────────
curl -s "$BASE/api/projects/sample/trace/SMP-0-01" > "$TMP_ROOT/trace1.json"
python3 - "$TMP_ROOT/trace1.json" <<'PY' || fail "trace payload wrong (shipped story, no log root yet)"
import json, sys
d = json.load(open(sys.argv[1]))["data"]
assert d["shipped"] is True and d["not_shipped_reason"] == ""
hops = {h["hop"]: h for h in d["chain"]}
assert list(hops) == ["readme", "phase_status", "story", "evidence", "final_summary"]
assert all(hops[h]["exists"] for h in ("readme", "phase_status", "story", "evidence"))
assert hops["final_summary"]["exists"] is False and hops["final_summary"]["path"]
assert d["events"] == []  # no git repo, no work-log root: clean degrade
PY

mkdir -p "$PMO_WORK_LOG_DIR/2026-07-02"
cat > "$PMO_WORK_LOG_DIR/2026-07-02/sample-1-work-summary.log" <<'EOF'
---
kind: pmo-work-log-entry
timestamp: 2026-07-02T12:00:00Z
project: sample
commit: abc1234
---

## Commit

- **Subject:** SMP-0-01 First fixture story ships
EOF
curl -s "$BASE/api/projects/sample/trace/SMP-0-01" > "$TMP_ROOT/trace2.json"
python3 - "$TMP_ROOT/trace2.json" <<'PY' || fail "trace should pick up the work-log entry live"
import json, sys
d = json.load(open(sys.argv[1]))["data"]
assert len(d["events"]) == 1, d["events"]
ev = d["events"][0]
assert ev["type"] == "work-log" and ev["commit"] == "abc1234"
assert ev["sort_key"] == "2026-07-02T12:00:00Z"
PY

curl -s "$BASE/api/projects/sample/trace/SMP-0-02" > "$TMP_ROOT/trace3.json"
python3 - "$TMP_ROOT/trace3.json" <<'PY' || fail "unshipped story must not claim shipped"
import json, sys
d = json.load(open(sys.argv[1]))["data"]
assert d["shipped"] is False
assert "backlog" in d["not_shipped_reason"]
hops = {h["hop"]: h for h in d["chain"]}
assert hops["evidence"]["exists"] is False
PY

[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/projects/sample/trace/SMP-9-99")" = "404" ] \
  || fail "unknown story trace should 404"
curl -s "$BASE/api/projects/sample/phases/0/events" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['ok'] and d['data']['events'] == []" \
  || fail "phase events should degrade cleanly without git"

# ── structured editor: mutation preview (WLA-5-06) ───────────────────
PRE_EDIT="$(sum_tree)"
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"kind":"create_story","project":"sample","phase":"0","title":"Editor made me"}' \
  "$BASE/api/mutations/preview" > "$TMP_ROOT/preview.json"
python3 - "$TMP_ROOT/preview.json" <<'PY' || fail "preview payload wrong"
import json, sys
body = json.load(open(sys.argv[1]))
assert body["ok"] is True
d = body["data"]
assert d["kind"] == "story-create"
assert d["fingerprint"].startswith("sha256:")
assert any(f["action"] == "create" and "Editor made me" in f.get("new_content", "") for f in d["files"])
assert any(f["action"] == "update" and f["path"].endswith("current-phase-status.md") for f in d["files"])
PY
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' \
    -d '{"kind":"update_story_status","project":"sample","phase":"0","story":"SMP-0-02","status":"done"}' \
    "$BASE/api/mutations/preview")" = "400" ] \
  || fail "done-without-evidence must be refused server-side"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST -d 'not json' "$BASE/api/mutations/preview")" = "400" ] \
  || fail "malformed JSON body should 400"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' \
    "$BASE/api/mutations/apply")" = "405" ] \
  || fail "apply must not exist before WLA-5-07"
[ "$PRE_EDIT" = "$(sum_tree)" ] || fail "previews must never write files"

# guard: a project with validation issues refuses preview without acknowledgment
PHASE_DIR="$(find "$PROJECT" -maxdepth 1 -type d -name 'phase-0-*' | sed -n '1p')"
printf '# stray\n' > "$PHASE_DIR/evidence-story-09.md"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' \
    -d '{"kind":"create_story","project":"sample","phase":"0","title":"Guarded"}' \
    "$BASE/api/mutations/preview")" = "409" ] \
  || fail "preview should be guarded while validation issues exist"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' \
    -d '{"kind":"create_story","project":"sample","phase":"0","title":"Guarded","acknowledge_issues":true}' \
    "$BASE/api/mutations/preview")" = "200" ] \
  || fail "explicit acknowledgment should unlock the preview"
rm -f "$PHASE_DIR/evidence-story-09.md"

echo "workbench-explorer.sh: ok"
