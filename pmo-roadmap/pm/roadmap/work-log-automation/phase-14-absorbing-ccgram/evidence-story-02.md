# Evidence - WLA-14-02

- **Story:** WLA-14-02 - The rails speak first: hook-driven push
- **Status:** done
- **Date:** 2026-07-04

## Proof

### Captured run — 2026-07-04T19:23:39Z

- **Command:** `bash -c echo "== batteries =="
python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | grep -E "^(OK|Ran)" | tail -2
python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 | head -1
/usr/bin/python3 --version
/usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 | head -1
bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1
echo
echo "== the seam, live on this desk =="
.githooks/dw hook status --agent claude
echo
echo "== a real emit through the real CLI, whitelist held =="
SCRATCH=$(mktemp -d)
echo "{\"session_id\": \"live-proof\", \"cwd\": \"/tmp\", \"message\": \"CONTENT MUST NOT LAND\"}" | DW_AGENT_EVENTS=$SCRATCH/e.jsonl .githooks/dw hook emit --agent claude --event Notification
cat $SCRATCH/e.jsonl
rm -rf $SCRATCH`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 852ab8a3fbfcfa810c31d882daea469a5af65d8b

```text
== batteries ==
Ran 160 tests in 13.211s
OK
Ran 53 tests in 8.186s
Python 3.9.6
Ran 53 tests in 8.452s
docs-lint.sh: ok (0s)

== the seam, live on this desk ==
claude	SessionStart:on Notification:on Stop:on SessionEnd:on	/Users/karol/.claude/settings.json

== a real emit through the real CLI, whitelist held ==
{"agent": "claude", "cwd": "/tmp", "event": "Notification", "session_id": "live-proof", "ts": "2026-07-04T19:24:10Z"}
```
