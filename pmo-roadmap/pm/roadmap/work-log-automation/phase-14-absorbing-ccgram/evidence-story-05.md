# Evidence - WLA-14-05

- **Story:** WLA-14-05 - The driver learns the desk's manners
- **Status:** done
- **Date:** 2026-07-04

## Proof

### Captured run — 2026-07-04T20:18:51Z

- **Command:** `bash -c echo "== batteries =="
python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 | head -1
/usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 | head -1
python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | grep -E "^(OK|Ran)" | tail -2
bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1
echo
echo "== the four organs, named tests =="
python3 pmo-roadmap/tests/telegram-interface-tests.py DriverMannersTest LiveViewTest ToolbarTest RecoveryTest 2>&1 | grep -E "^Ran|^OK"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 736c147815d7d8c9ba820319da7db102a912fa84

```text
== batteries ==
Ran 92 tests in 6.229s
Ran 92 tests in 5.788s
Ran 160 tests in 13.017s
OK
docs-lint.sh: ok (0s)

== the four organs, named tests ==
Ran 13 tests in 0.455s
OK
```
