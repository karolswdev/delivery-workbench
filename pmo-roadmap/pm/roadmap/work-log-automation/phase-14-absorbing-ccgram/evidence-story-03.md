# Evidence - WLA-14-03

- **Story:** WLA-14-03 - The message layer grows up
- **Status:** done
- **Date:** 2026-07-04

## Proof

### Captured run — 2026-07-04T19:36:51Z

- **Command:** `bash -c echo "== batteries =="
python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 | head -1
/usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 | head -1
python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | grep -cE "^OK$"
bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1
echo
echo "== the layer, exercised inline =="
python3 - <<PYEOF
import sys
sys.path.insert(0, "integrations/telegram")
from dw_telegram.entities import to_entities
from dw_telegram.msgqueue import OutMessage, plan_batch
plain, ents = to_entities("🙋 **bold** and \`code\` with a_hostile*string")
print("plain:", plain)
print("entities:", ents)
actions = plan_batch([OutMessage(1, "a"), OutMessage(1, "b"),
                      OutMessage(1, "s1", kind="status"),
                      OutMessage(1, "s2", kind="status")])
print("plan:", [(a.op, a.text) for a in actions])
PYEOF`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 608342f87ae41de055732e3a4a88d2e46a151db8

```text
== batteries ==
Ran 66 tests in 5.109s
Ran 66 tests in 4.972s
1
docs-lint.sh: ok (0s)

== the layer, exercised inline ==
plain: 🙋 bold and code with a_hostile*string
entities: [{'type': 'bold', 'offset': 3, 'length': 4}, {'type': 'code', 'offset': 12, 'length': 4}]
plan: [('send', 'a\n\nb'), ('edit_status', 's2')]
```
