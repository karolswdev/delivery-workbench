# Evidence - WLA-14-06

- **Story:** WLA-14-06 - Send files through seven locks
- **Status:** done
- **Date:** 2026-07-04

## Proof

### Captured run — 2026-07-04T20:35:00Z

- **Command:** `bash -c echo "== batteries =="
python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 | head -1
/usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 | head -1
python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | grep -E "^(OK|Ran)" | tail -2
bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1
echo
echo "== the seven locks, each fired =="
python3 pmo-roadmap/tests/telegram-interface-tests.py SendLocksTest SendCommandTest 2>&1 | grep -E "^Ran|^OK"
echo
echo "== CI credential grep passes on the new surface =="
git ls-files | grep -E "(^|/)(telegram-state\.json|agent-events\.jsonl|\.env|.*\.pem|id_rsa)$" && echo HIT || echo "grep-clean: ok"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6c426cb7136a1840c4cca26157a14b6fe273fa9c

```text
== batteries ==
Ran 107 tests in 6.699s
Ran 107 tests in 6.254s
Ran 160 tests in 13.035s
OK
docs-lint.sh: ok (1s)

== the seven locks, each fired ==
Ran 15 tests in 0.417s
OK

== CI credential grep passes on the new surface ==
grep-clean: ok
```
