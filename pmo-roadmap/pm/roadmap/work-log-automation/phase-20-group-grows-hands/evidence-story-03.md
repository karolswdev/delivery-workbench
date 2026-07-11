# Evidence - WLA-20-03

- **Story:** WLA-20-03 - Consent belongs to a person — groups get faces
- **Status:** done
- **Date:** 2026-07-11

## Proof

One captured run (the contract's `--tests-capture`), three legs
inside it:

1. **The suite** — 129 interface tests OK (122 → 129: the seven
   PerPersonConsentTest legs — pairing records the owner and it
   round-trips through persistence; `/arm` from a stranger refused
   with nothing armed, from the owner it arms; every tap class
   (approve, toolbar key, screenshot refresh) refused for the
   stranger with zero keystrokes reaching the terminal AND the
   proposal surviving for the owner's own tap; the steering relay
   refuses the stranger and flows for the owner; five read
   commands answer a stranger; `/status` warns on a legacy
   pairing and says "owner: recorded" otherwise).
2. **Fitness** — 8 OK, layering unchanged.
3. **The truth table, executed** — legacy → allow (chat
   granularity stands, and every pre-existing test whose fixtures
   carry no from.id pins it); owner → allow; stranger → refuse;
   and the strict corner: owner recorded + anonymous update
   (no from.id at all) → REFUSE. Identity unproven is not
   identity.

The row-15 transmutation is recorded in the phase decisions: no
allowlist file exists anywhere — `/pair` itself names the
owner-of-record, and re-pairing renames it.

### Captured run — 2026-07-11T20:28:33Z

- **Command:** `bash -c /usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3
/usr/bin/python3 pmo-roadmap/tests/telegram-fitness-tests.py 2>&1 | tail -3
echo "--- the guard in one truth table (owner / stranger / legacy) ---"
/usr/bin/python3 - <<PYEOF
import sys
sys.path.insert(0, "integrations/telegram")
from types import SimpleNamespace
from dw_telegram.interface import TelegramInterface
iface = SimpleNamespace(state=SimpleNamespace(owner_user_id=None), _sender_id=888)
print("legacy state, any sender  -> refused:", TelegramInterface._not_owner(iface))
iface = SimpleNamespace(state=SimpleNamespace(owner_user_id=777), _sender_id=777)
print("owner recorded, owner     -> refused:", TelegramInterface._not_owner(iface))
iface = SimpleNamespace(state=SimpleNamespace(owner_user_id=777), _sender_id=888)
print("owner recorded, stranger  -> refused:", TelegramInterface._not_owner(iface))
iface = SimpleNamespace(state=SimpleNamespace(owner_user_id=777), _sender_id=None)
print("owner recorded, anonymous -> refused:", TelegramInterface._not_owner(iface))
PYEOF`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** feba622dc428c213e18ba4e9151879a9d34c77f9

```text
Ran 129 tests in 8.207s

OK (skipped=10)
Ran 8 tests in 0.127s

OK
--- the guard in one truth table (owner / stranger / legacy) ---
legacy state, any sender  -> refused: False
owner recorded, owner     -> refused: False
owner recorded, stranger  -> refused: True
owner recorded, anonymous -> refused: True
```
