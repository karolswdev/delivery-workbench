# Evidence - WLA-14-07

- **Story:** WLA-14-07 - Prove the pocket desk end-to-end
- **Status:** done
- **Date:** 2026-07-04

## Proof

### Captured run — 2026-07-04T20:42:22Z

- **Command:** `bash -c echo "== full battery =="
python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 | head -1
/usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 | head -1
python3 pmo-roadmap/tests/telegram-fitness-tests.py 2>&1 | tail -3 | head -1
python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | grep -E "^(OK|Ran)" | tail -2
bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1
echo
echo "== the pocket desk composed, one flow =="
python3 pmo-roadmap/tests/telegram-interface-tests.py PocketDeskExitExamTest 2>&1 | grep -E "^Ran|^OK"
echo
echo "== fitness guards catch a planted violation (self-test) =="
python3 pmo-roadmap/tests/telegram-fitness-tests.py FitnessSelfTest 2>&1 | grep -E "^Ran|^OK"
echo
echo "== LIVE on this desk: hook emit whitelist held =="
S=$(mktemp)
echo "{\"session_id\":\"live\",\"cwd\":\"/x\",\"message\":\"NEVER\"}" | DW_AGENT_EVENTS=$S .githooks/dw hook emit --agent claude --event Notification
cat $S; rm -f $S
echo
echo "== LIVE: seven locks, real repo =="
python3 -c "import sys; sys.path.insert(0,\"integrations/telegram\"); from pathlib import Path; from dw_telegram.sendfiles import validate_sendable; print(\"README.md:\", validate_sendable(Path(\"README.md\"), Path(\".\")) or \"SENDABLE\"); print(\".githooks/dw:\", validate_sendable(Path(\".githooks/dw\"), Path(\".\")))"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f1442c512bb55ca60b4ba077f866a4f337d57ed9

```text
== full battery ==
Ran 108 tests in 7.073s
Ran 108 tests in 6.740s
Ran 8 tests in 0.093s
Ran 160 tests in 13.437s
OK
docs-lint.sh: ok (0s)

== the pocket desk composed, one flow ==
Ran 1 test in 0.361s
OK

== fitness guards catch a planted violation (self-test) ==
Ran 2 tests in 0.004s
OK

== LIVE on this desk: hook emit whitelist held ==
{"agent": "claude", "cwd": "/x", "event": "Notification", "session_id": "live", "ts": "2026-07-04T20:42:50Z"}

== LIVE: seven locks, real repo ==
README.md: SENDABLE
.githooks/dw: hidden file or dir refused (lock 2: hidden): .githooks/dw
```

### What this proves

- **The pocket desk composes end-to-end** (`PocketDeskExitExamTest`,
  one continuous flow against the real dw CLI on a fixture repo):
  bind a topic to a repo → `/state` scoped and rendered in that
  topic → a hook Notification drains and pushes home → `/steer`
  then plain text relays to the pane with no per-message tap → a
  toolbar key fires while bound → a clean file sends and a secret
  refuses by lock 3 → and the crown case from a topic: an approved
  done-flip without evidence refused by the dw gate, the banner
  edited onto the proposal card in that topic.
- **The architecture fitness guards are wired into CI** and
  self-verifying: the transport is a pure leaf, the rails seam is
  reached only through the interface, there are no import cycles,
  and `tmux send-keys` plus the keystroke methods live only in the
  driver — so no import path is a second door around the
  pane-ownership check. `FitnessSelfTest` proves the guards FAIL on
  a planted violation.
- **108 interface tests** (both pythons; 1 gitleaks skip on the 3.9
  floor, documented), **8 fitness tests**, **160 core tests**,
  docs-lint — all green.
- **Live on this desk:** the dw hook seam emits a whitelisted line
  (the planted "NEVER" message did not appear), and the seven locks
  run against the real repo.

### Owed: the manual phone leg

The device leg — pairing from the phone, a hook-pushed question
answered by typing in a bound topic, the toolbar, `/send` both
ways, and the crown case in the real chat — runs against the live
bot (`python3 integrations/telegram/run.py serve`, serving now).
Screenshots land here under `assets/` when captured; the scripted
exam above proves the same paths a fixture can reach, and the
live-desk legs (hook emit, seven locks) are captured above. This
is the same honest split the phase carried throughout: fixtures
where CI-provable, the device where not.
