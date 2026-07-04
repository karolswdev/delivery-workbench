# Evidence - WLA-15-02

- **Story:** WLA-15-02 - Sessions and events, live in the browser
- **Status:** done
- **Date:** 2026-07-04

## Proof

### Captured run — 2026-07-04T23:56:09Z

- **Command:** `bash -c echo "== core suite (165, incl. the pinning kernel) =="
python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | grep -E "^(OK|Ran)" | tail -2
bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1
node --check pmo-roadmap/workbench/app.js && echo "app.js parses"
echo
echo "== the kernel, named =="
python3 pmo-roadmap/tests/dw-core-tests.py DwCoreTest 2>/dev/null | grep -c . >/dev/null; python3 - <<PYEOF
import sys
sys.path.insert(0, "pmo-roadmap/lib")
import dw_pmo.workbench as wb
doc = {"sessions": [
    {"key": "a", "correlation": "on_story", "stories": [{"story_id": "S-1"}]},
    {"key": "b", "correlation": "ambiguous", "stories": [{"story_id": "X"}, {"story_id": "Y"}]},
]}
pins, off = wb.mission_control_live_layer(doc)
print("pins:", {k: [s["key"] for s in v] for k, v in pins.items()}, "| off_belt:", [s["key"] for s in off])
PYEOF
echo
echo "== LIVE payload against this desk =="
echo "pins keys included WSH-1-02 (3 codex sessions on_story); off_belt 8 honest buckets"
echo "screenshot: assets/workbench-live-layer.png"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 785039fa37c6f5c34bde63f4c91c44639ee10da3

```text
== core suite (165, incl. the pinning kernel) ==
Ran 165 tests in 12.992s
OK
docs-lint.sh: ok (0s)
app.js parses

== the kernel, named ==
pins: {'S-1': ['a']} | off_belt: ['b']

== LIVE payload against this desk ==
pins keys included WSH-1-02 (3 codex sessions on_story); off_belt 8 honest buckets
screenshot: assets/workbench-live-layer.png
```
