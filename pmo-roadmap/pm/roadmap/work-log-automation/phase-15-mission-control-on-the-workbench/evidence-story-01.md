# Evidence - WLA-15-01

- **Story:** WLA-15-01 - Design and the belt panel
- **Status:** done
- **Date:** 2026-07-04

## Proof

### Captured run — 2026-07-04T23:36:00Z

- **Command:** `bash -c echo "== core suite with the new route tests =="
python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | grep -E "^(OK|Ran)" | tail -2
bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1
node --check pmo-roadmap/workbench/app.js && echo "app.js parses"
echo
echo "== the route, LIVE against this repo =="
curl -s "http://127.0.0.1:8391/api/missioncontrol?tail=5" | python3 -c "
import json,sys
d=json.load(sys.stdin)[\"data\"]
print(\"feed_schema:\", d[\"feed\"][\"feed_schema\"], \"| projects:\", [p[\"slug\"] for p in d[\"feed\"][\"projects\"]])
print(\"sessions registry:\", d[\"sessions\"][\"registry\"], \"| count:\", len(d[\"sessions\"][\"sessions\"]))
print(\"events:\", [(e[\"event\"], e.get(\"story\")) for e in d[\"events\"]])"
echo
echo "== read-only at the API layer =="
curl -s -X POST "http://127.0.0.1:8391/api/missioncontrol" -H "Content-Type: application/json" -d "{}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(\"mutation attempt →\", d[\"issues\"][0][:80])"
echo
echo "screenshot: assets/workbench-belt-live.png (the belt, live in the browser)"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2b3eb462fd5bff7780257f8577381e13591d02e4

```text
== core suite with the new route tests ==
Ran 163 tests in 12.913s
OK
docs-lint.sh: ok (0s)
app.js parses

== the route, LIVE against this repo ==
feed_schema: 1 | projects: ['work-log-automation']
sessions registry: ok | count: 11
events: [('story_status', 'WLA-15-02'), ('story_status', 'WLA-15-03'), ('contract_generated', None), ('gate_pass', None), ('story_status', 'WLA-15-01')]

== read-only at the API layer ==
mutation attempt → unsupported method or route; mutations go through /api/mutations/preview and /ap

screenshot: assets/workbench-belt-live.png (the belt, live in the browser)
```
