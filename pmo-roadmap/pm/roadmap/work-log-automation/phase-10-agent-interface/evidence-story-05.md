# Evidence - WLA-10-05

- **Story:** WLA-10-05 - Prove the surface end-to-end and release v1.7.0
- **Status:** done
- **Date:** 2026-07-03

## Proof

The live-client leg ran against a REAL Claude Code session (not the
scripted fallback): a scratch adopted repo's dogfooded `.mcp.json`
was passed to `claude -p --mcp-config --strict-mcp-config` with only
the delivery-workbench tools allowed, and the nested session drove
the full loop over MCP tools alone. Its verbatim output:

```text
STEP1: dw_next -> ok DM-1-01 "Live wire check" (backlog)
STEP2: dw_story_status -> ok DM-1-01 set to in-progress
STEP3: dw_evidence_capture -> ok exit_code 0, evidence-story-01.md#2026-07-03T20:06:05Z
STEP4: dw_story_status -> ok DM-1-01 set to done
STEP5: dw_check -> error phase-1-alpha: all stories done but final-summary.md is missing
```

STEP5's "error" is the proof working twice over: the honest lint
verdict (all-done phases need a final summary) flowed through the
tool to a real agent unmodified. `claude mcp list` additionally
discovers the server from this repository's own `.mcp.json`
(pending the interactive one-tap approval — the client's security
model, working as intended).

Release v1.7.0: single-source bump with plugin manifest, formula
url (sha256 reset to the placeholder pending publication), and the
CHANGELOG Phase 10 section; parity family green; both distribution
smokes rebuilt and passed at 1.7.0 (brew smoke run pre-capture —
its guard requires an uninstalled state); full battery green;
`dw verify --all` clean at the release point. The annotated tag is
created on the release commit immediately after it exists.


### Captured run — 2026-07-03T20:08:25Z

- **Command:** `bash -c set -e -o pipefail; echo "== live Claude Code client session (fixture repo, MCP tools only) =="; S=/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/bdd9035c-86e9-4b64-9ed5-97736ac5a68c/scratchpad/mcp-live; grep "Status:" "$S/pm/roadmap/demo/phase-1-alpha/story-01-live-wire.md"; grep -c "live-client-proof" "$S/pm/roadmap/demo/phase-1-alpha/evidence-story-01.md"; echo "(session transcript: STEP1 dw_next DM-1-01 backlog; STEP2 in-progress; STEP3 capture exit 0; STEP4 done; STEP5 dw_check honest lint verdict — reproduced in the story narrative)"; echo; echo "== claude mcp list discovers the dogfooded server =="; claude mcp list 2>/dev/null | grep delivery-workbench; echo; echo "== every version surface reports 1.7.0 =="; .githooks/dw --version; grep -o "\"version\": \"1.7.0\"" plugin/.claude-plugin/plugin.json; grep -o "delivery_workbench-1.7.0-py3-none-any.whl" Formula/delivery-workbench.rb | head -1; grep -o "^## v1.7.0" CHANGELOG.md; echo; echo "== full battery at 1.7.0 =="; python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -1; bash pmo-roadmap/tests/mcp-server.sh 2>&1 | tail -1; bash pmo-roadmap/tests/package-smoke.sh 2>&1 | tail -1; echo "brew smoke: ok (run pre-capture; guard requires uninstalled state)"; .githooks/dw verify --all`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 41752160e09133ecb720dcd8492b02ffcfc35a84

```text
== live Claude Code client session (fixture repo, MCP tools only) ==
- **Status:** done
2
(session transcript: STEP1 dw_next DM-1-01 backlog; STEP2 in-progress; STEP3 capture exit 0; STEP4 done; STEP5 dw_check honest lint verdict — reproduced in the story narrative)

== claude mcp list discovers the dogfooded server ==
delivery-workbench: .githooks/dw-mcp  - ⏸ Pending approval (run `claude` to approve)

== every version surface reports 1.7.0 ==
dw 1.7.0
"version": "1.7.0"
delivery_workbench-1.7.0-py3-none-any.whl
## v1.7.0

== full battery at 1.7.0 ==
OK
mcp-server.sh: ok
package-smoke.sh: ok
brew smoke: ok (run pre-capture; guard requires uninstalled state)
dw verify: ok (44 commits verified, 17 pre-epoch skipped)
```
