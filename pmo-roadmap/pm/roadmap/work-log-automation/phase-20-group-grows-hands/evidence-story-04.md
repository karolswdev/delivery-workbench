# Evidence - WLA-20-04

- **Story:** WLA-20-04 - The toolbar grows up — grids, builtins, and the command menu
- **Status:** done
- **Date:** 2026-07-11

## Proof

One captured run (the contract's `--tests-capture`), three legs:

1. **The suite** — 140 interface tests OK (129 → 140: five
   ToolbarConfigTest legs — per-harness defaults with the claude
   fallback, kb:/tb: routing split, a config reshaping one grid
   while untouched harnesses keep theirs, the closed-table refusal,
   and a twelve-shape garbage fuzz where every input warns and the
   grid survives — plus six ToolbarUpgradeTest legs: /toolbar
   renders the harness grid, a config text action types through
   the driver's literal-then-Enter door, builtin `screen` produces
   the story-01 flow, `dismiss` edits the card in place, an
   unknown action and an unbound tap are refused, and
   `register_command_menu` records exactly one setMyCommands with
   the opt-out making it zero).
2. **Fitness** — 8 OK with `toolbarcfg` now pinned in LEAVES.
3. **The closed table, executed** — a config defining
   `{"type": "builtin", "payload": "run_shell"}` yields NO action
   and the warning says why: capability is never config.

Design note: key actions ride the existing `kb:` channel (the one
door, unchanged); text/builtin actions resolve through `tb:<id>`
AT TAP TIME against the current config, so an edited config never
leaves a stale payload armed inside an old message. Taps inherit
the story-03 owner check before any dispatch.

### Captured run — 2026-07-11T20:33:55Z

- **Command:** `bash -c /usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3
/usr/bin/python3 pmo-roadmap/tests/telegram-fitness-tests.py 2>&1 | tail -3
echo "--- the closed table, live: a config trying to mint a builtin ---"
/usr/bin/python3 - <<PYEOF
import sys
sys.path.insert(0, "integrations/telegram")
from dw_telegram.toolbarcfg import load_toolbar
cfg, warnings = load_toolbar({"actions": {"shell": {"type": "builtin", "payload": "run_shell"}}})
print("minted action present:", cfg.action("shell") is not None)
print("warning:", warnings[0])
PYEOF`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4b915561a93dc55b930e655dff59f1b03d588abd

```text
Ran 140 tests in 8.134s

OK (skipped=10)
Ran 8 tests in 0.137s

OK
--- the closed table, live: a config trying to mint a builtin ---
minted action present: False
warning: action 'shell' names builtin 'run_shell' which does not exist; the builtin table is closed — skipped
```
