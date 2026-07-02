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
git -C "$REPO" init -q
git -C "$REPO" config user.name "Workbench Test"
git -C "$REPO" config user.email "workbench@example.test"
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
"$PMO_DIR/bin/dw-workbench" --root "$REPO" --port "$PORT" 2>"$TMP_ROOT/access.log" &
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
    "$BASE/api/mutations/apply")" = "400" ] \
  || fail "apply without a preview fingerprint must be refused"
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

# ── preview → apply workflow (WLA-5-07) ──────────────────────────────
mut() { # json -> response file; echoes http code
  curl -s -o "$TMP_ROOT/mut.json" -w '%{http_code}' -X POST \
    -H 'Content-Type: application/json' -d "$1" "$BASE/api/mutations/$2"
}
fp_of() { python3 -c "import json;print(json.load(open('$TMP_ROOT/mut.json'))['data']['fingerprint'])"; }

# full cycle: create story
REQ='{"kind":"create_story","project":"sample","phase":"0","title":"Applied by workflow"}'
[ "$(mut "$REQ" preview)" = "200" ] || fail "workflow preview failed"
python3 - "$TMP_ROOT/mut.json" <<'PY' || fail "preview must carry diffs and validation projections"
import json, sys
d = json.load(open(sys.argv[1]))["data"]
assert d["no_op"] is False
assert d["issues_before"] == []
assert d["issues_after"] == []
assert any("diff" in f and f["action"] == "update" for f in d["files"])
assert all(("+" in f["diff"]) for f in d["files"] if f.get("diff") and f["changed"])
PY
FP="$(fp_of)"
[ "$(mut "${REQ%\}}, \"fingerprint\":\"$FP\"}" apply)" = "200" ] || fail "apply with fresh fingerprint failed"
python3 - "$TMP_ROOT/mut.json" <<'PY' || fail "apply result shape wrong"
import json, sys
d = json.load(open(sys.argv[1]))["data"]
assert d["applied"] is True and d["issues"] == []
assert any(p.endswith("story-03-applied-by-workflow.md") for p in d["changed"])
PY
[ -f "$PHASE_DIR/story-03-applied-by-workflow.md" ] || fail "applied story file missing"
"$DW" --root "$REPO" check sample >/dev/null || fail "post-apply dw check should pass"

# stale refusal: same fingerprint again (tree changed underneath it)
[ "$(mut "${REQ%\}}, \"fingerprint\":\"$FP\"}" apply)" = "409" ] || fail "stale fingerprint must be refused"
grep -q "stale preview" "$TMP_ROOT/mut.json" || fail "refusal should name staleness"

# done-with-evidence cycle
REQ='{"kind":"update_story_status","project":"sample","phase":"0","story":"SMP-0-02","status":"done","evidence_body":"- workflow proof."}'
[ "$(mut "$REQ" preview)" = "200" ] || fail "done preview failed"
FP="$(fp_of)"
[ "$(mut "${REQ%\}}, \"fingerprint\":\"$FP\"}" apply)" = "200" ] || fail "done apply failed"
"$DW" --root "$REPO" check sample >/dev/null || fail "check should pass after done-with-evidence"

# flip the workflow-created story done too (second done-with-evidence cycle)
REQ='{"kind":"update_story_status","project":"sample","phase":"0","story":"SMP-0-03","status":"done","evidence_body":"- workflow proof three."}'
[ "$(mut "$REQ" preview)" = "200" ] || fail "second done preview failed"
FP="$(fp_of)"
[ "$(mut "${REQ%\}}, \"fingerprint\":\"$FP\"}" apply)" = "200" ] || fail "second done apply failed"

# close phase cycle — all stories done, so dw check now flags the missing
# final summary; the guard must recognize close_phase as remediation and
# let it through WITHOUT acknowledge_issues.
REQ='{"kind":"close_phase","project":"sample","phase":"0","summary_body":"Closed by the workflow test."}'
[ "$(mut "$REQ" preview)" = "200" ] || fail "close preview failed"
FP="$(fp_of)"
[ "$(mut "${REQ%\}}, \"fingerprint\":\"$FP\"}" apply)" = "200" ] || fail "close apply failed"
[ -f "$PHASE_DIR/final-summary.md" ] || fail "final summary missing after close"
"$DW" --root "$REPO" check sample | grep -q 'dw check: ok' || fail "check should pass after close"

# no-op: re-attaching existing evidence without body is explicitly idempotent
REQ='{"kind":"attach_evidence","project":"sample","phase":"0","story":"SMP-0-01"}'
[ "$(mut "$REQ" preview)" = "200" ] || fail "no-op preview failed"
python3 -c "import json; d=json.load(open('$TMP_ROOT/mut.json'))['data']; assert d['no_op'] is True" \
  || fail "no-op preview should say so"
FP="$(fp_of)"
NOOP_BEFORE="$(sum_tree)"
[ "$(mut "${REQ%\}}, \"fingerprint\":\"$FP\"}" apply)" = "200" ] || fail "no-op apply failed"
[ "$NOOP_BEFORE" = "$(sum_tree)" ] || fail "no-op apply must leave the tree byte-identical"

# ── commit/work-log evidence views (WLA-5-08) ─────────────────────────
ENTRY="$PMO_WORK_LOG_DIR/2026-07-02/sample-1-work-summary.log"
curl -s "$BASE/api/worklog?path=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$ENTRY")" \
  > "$TMP_ROOT/wl.json"
python3 - "$TMP_ROOT/wl.json" <<'PY' || fail "worklog endpoint should serve the fixture entry"
import json, sys
body = json.load(open(sys.argv[1]))
assert body["ok"] is True
assert "SMP-0-01 First fixture story ships" in body["data"]["content"]
PY
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/worklog?path=pm/roadmap/sample/README.md")" = "403" ] \
  || fail "worklog endpoint must refuse non-log paths"

curl -s "$BASE/api/projects/sample/handoff/SMP-0-01" > "$TMP_ROOT/handoff.json"
python3 - "$TMP_ROOT/handoff.json" <<'PY' || fail "handoff summary wrong"
import json, sys
d = json.load(open(sys.argv[1]))["data"]
assert d["shipped"] is True
text = d["text"]
assert "handoff — SMP-0-01" in text
assert "evidence: pm/roadmap/sample/" in text
assert "sample-1-work-summary.log" in text
assert "never a substitute for evidence-story-NN.md" in text
PY

# ── runtime permission model (WLA-5-09) ───────────────────────────────
# no endpoint stages or commits: the git index stayed empty through
# every preview and apply above
[ -z "$(git -C "$REPO" ls-files)" ] || fail "the workbench must never stage files"

# default-deny methods and hosts
[ "$(curl -s -o /dev/null -w '%{http_code}' -X OPTIONS "$BASE/api/context")" = "405" ] \
  || fail "OPTIONS (CORS preflight) must fail closed"
[ "$(curl -s -o /dev/null -w '%{http_code}' -H 'Host: evil.example.com' "$BASE/api/projects")" = "403" ] \
  || fail "non-local Host header must be refused"
if curl -s -i "$BASE/api/projects" | grep -qi 'access-control-allow'; then
  fail "no CORS headers may ever be emitted"
fi

# startup refusals fail closed with clear messages
BARE="$TMP_ROOT/bare"; mkdir -p "$BARE"
if OUT=$("$PMO_DIR/bin/dw-workbench" --root "$BARE" --port 19999 2>&1); then
  fail "server must refuse a root without pm/roadmap"
fi
echo "$OUT" | grep -q "no pm/roadmap tree" || fail "roadmap refusal should name the problem"
if OUT=$("$PMO_DIR/bin/dw-workbench" --root "$TMP_ROOT/ghost" --port 19999 2>&1); then
  fail "server must refuse a nonexistent root"
fi

# port conflict: second server on the same port refuses with remediation
if OUT=$("$PMO_DIR/bin/dw-workbench" --root "$REPO" --port "$PORT" 2>&1); then
  fail "second server on a busy port must refuse"
fi
echo "$OUT" | grep -q "pass --port" || fail "port-conflict message should include remediation"

# request logging: the access log recorded the refusals above
grep -q 'GET /api/projects HTTP/1.1" 403' "$TMP_ROOT/access.log" \
  || fail "access log should record the refused evil-Host request"
grep -q 'POST /api/mutations/apply HTTP/1.1" 409' "$TMP_ROOT/access.log" \
  || fail "access log should record the stale-preview refusal"

# clean shutdown on SIGTERM frees the port
kill -TERM "$SERVER_PID" 2>/dev/null || true
wait "$SERVER_PID" 2>/dev/null || true
SERVER_PID=""
sleep 0.5
"$PMO_DIR/bin/dw-workbench" --root "$REPO" --port "$PORT" --quiet &
SERVER_PID=$!
i=0
until curl -sf "$BASE/api/projects" >/dev/null 2>&1; do
  i=$((i + 1)); [ "$i" -lt 40 ] || fail "port was not freed after SIGTERM"; sleep 0.25
done

# installed layout: install.sh distributes the workbench and the UI serves
INSTALL_REPO="$TMP_ROOT/installed"
mkdir -p "$INSTALL_REPO"
git -C "$INSTALL_REPO" init -q
git -C "$INSTALL_REPO" config user.name t
git -C "$INSTALL_REPO" config user.email t@t
"$PMO_DIR/install.sh" "$INSTALL_REPO" --project-name Demo --project-slug demo --project-prefix DEMO >/dev/null 2>&1
[ -x "$INSTALL_REPO/.githooks/dw-workbench" ] || fail "install should ship dw-workbench"
[ -f "$INSTALL_REPO/.githooks/workbench/index.html" ] || fail "install should ship the workbench UI"
IPORT=$(( PORT + 1 ))
"$INSTALL_REPO/.githooks/dw-workbench" --root "$INSTALL_REPO" --port "$IPORT" --quiet &
IPID=$!
i=0
until curl -sf "http://127.0.0.1:$IPORT/api/projects" >/dev/null 2>&1; do
  i=$((i + 1)); [ "$i" -lt 40 ] || { kill $IPID 2>/dev/null; fail "installed workbench did not start"; }; sleep 0.25
done
curl -s "http://127.0.0.1:$IPORT/" | grep -q 'id="app"' \
  || { kill $IPID 2>/dev/null; fail "installed workbench should serve the UI from .githooks/workbench"; }
kill $IPID 2>/dev/null; wait $IPID 2>/dev/null || true

echo "workbench-explorer.sh: ok"
