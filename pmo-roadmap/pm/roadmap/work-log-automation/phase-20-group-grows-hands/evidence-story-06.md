# Evidence - WLA-20-06

- **Story:** WLA-20-06 - The exit exam — fitness, ledger, and the contract amended
- **Status:** done
- **Date:** 2026-07-11

## Proof

One captured run (the contract's `--tests-capture`) carrying the
whole exam:

1. **The full battery** — core 208 OK, telegram interface 147 OK
   (108 at phase open → 147 at close), fitness 10 OK (8 → 10:
   the quoted Bot API string census and the new-leaf planted
   self-test), docs-lint ok, plugin-validate ok.
2. **The census, greppable in the run** — the quoted API strings
   (`"sendPhoto"`, `"editMessageMedia"`, `"setMyCommands"`) exist
   in exactly one file: `transport.py`. The send-keys census is
   asserted inside the fitness run above, unchanged.
3. **The documents** — `docs/absorption-ccgram.md` gained "The
   second absorption — upstream v4.3.11" (rows 21–30: what was
   absorbed, transmuted, deferred again, and the refusals that
   stand); `docs/mission-control.md` §4 gained three amendments
   (the picture reads in ring 1, the owner-of-record in ring 1,
   the button surfaces in ring 3); the README's mission-control
   paragraph tells a stranger the new truth in three sentences.

Owed beyond the phase (recorded, not claimed): the live phone leg —
`/screen`, the image `/live`, a toolbar tap, and a two-account
group walk on the desk — lands as screenshots in these assets the
next time the bot serves; the machinery is test-proven above
either way.

### Captured run — 2026-07-11T20:41:01Z

- **Command:** `bash -c echo "== full battery =="
/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | grep -E "^(OK|FAILED|Ran)"
/usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | grep -E "^(OK|FAILED|Ran)"
/usr/bin/python3 pmo-roadmap/tests/telegram-fitness-tests.py 2>&1 | grep -E "^(OK|FAILED|Ran)"
bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1
bash pmo-roadmap/tests/plugin-validate.sh 2>&1 | tail -1
echo
echo "== the census, greppable =="
grep -c "sendPhoto\|editMessageMedia\|setMyCommands" integrations/telegram/dw_telegram/transport.py
grep -rl "\"sendPhoto\"\|\"editMessageMedia\"\|\"setMyCommands\"" integrations/telegram/dw_telegram/ | sort
echo
echo "== the ledger names the second absorption =="
grep -n "second absorption" docs/absorption-ccgram.md docs/mission-control.md README.md 2>/dev/null | head -3
grep -c "WLA-20-0" docs/absorption-ccgram.md`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a195cd8db42ec1977e20a750e1a9a0d3f2c2466c

```text
== full battery ==
Ran 208 tests in 13.904s
OK
Ran 147 tests in 9.026s
OK (skipped=10)
Ran 10 tests in 0.149s
OK
docs-lint.sh: ok (0s)
plugin-validate.sh: ok

== the census, greppable ==
3
integrations/telegram/dw_telegram/transport.py

== the ledger names the second absorption ==
docs/absorption-ccgram.md:147:## The second absorption — upstream v4.3.11 (phase 20)
7
```
