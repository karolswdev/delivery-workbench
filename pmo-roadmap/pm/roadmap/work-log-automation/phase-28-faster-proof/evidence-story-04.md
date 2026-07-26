# Evidence - WLA-28-04

- **Story:** WLA-28-04 - Prove work in parallel
- **Status:** done
- **Date:** 2026-07-26

## The suite was already parallel and did not know it

Every test builds its own temporary repository under `mkdtemp` and cleans it
up, so there was never a shared fixture to contend over — only a runner
missing. [`tests/run-core-tests.py`](../../../../tests/run-core-tests.py)
spreads work across processes using the standard library alone, on the
declared 3.9 floor. `pytest-xdist` would have traded a dependency and a floor
change for the same speedup, which this phase's scope forbids.

Sharding is by **test method**, not by class: per-test `setUp` measured 0.32s
even for the deepest nested program fixture, so keeping classes whole would
have bought nothing and left one 330-cost shard as the bottleneck. The
exception is a class defining its own `setUpClass` — that cost is paid once
per process, so `ProgramContractTest` and `UsabilityPackagedExamContractTest`
stay atomic. Assignment is longest-processing-time-first over cost hints;
the hints affect balance only, never which tests run.

## Coverage is proven identical, not assumed

The captured run asserts that expanding the runner's 516 scheduling units
yields exactly the 523 test ids a serial `loadTestsFromModule` yields, with
zero duplicates. A serial run reports the same 523. Test count and assertions
are unchanged across the whole story.

## Stability, which is why this story was parked first

The story was parked mid-flight because repeated sharded runs were **not**
stable on a loaded desk, and the park was the right call. Two tests failed
across repeats, both on wall clock rather than isolation. The root cause was
smaller than it looked.

`supervise_program` carries two ceilings: `max_ticks`, which tests set
explicitly, and `max_seconds`, which defaults to **300** and which no test
passes. Eighteen call sites inherited that default, and **no test anywhere
asserts a `time-ceiling` stop** — verified in the capture. On a busy machine a
twelve-tick supervision simply ran out of seconds and returned
`('ready', 'time-ceiling')` instead of `('story-certified', 'checkpoint')`.

Those eighteen sites now pass an unreachable `max_seconds`, leaving `max_ticks`
as the only bound that decides an outcome. No assertion changed, nothing was
removed or skipped, and the tick bound is untouched. A loaded machine simply
stops being able to decide the result.

One case is genuinely load-sensitive and stays that way on purpose:
`test_cancellation_interrupts_a_live_contained_check` polls 100 x 20ms for a
live child process to publish a receipt. That budget *is* the assertion — it
proves cancellation is prompt — so it must not be relaxed. It runs alone in a
serial tail after the shards finish, and a test asserts the tail is covered
exactly once and never also sharded.

| Run | Tests | Wall clock | Result |
|---|---:|---:|---|
| sharded 1 | 523 | 118.6s | OK |
| sharded 2 | 523 | 129.4s | OK |
| sharded 3 | 523 | 122.5s | OK |
| sharded, 3 shards | 523 | 174.5s | OK |
| serial | 523 | — | OK |

Against **547.6s serial** that is **4.4x**; against the phase's **814s**
baseline, **6.5x**. The desk carried 15-minute load averages above 22 during
this capture and every run still passed, which is the evidence the earlier
failures were the wall-clock guard rather than the runner.

## Two runner bugs its own tests caught

Both were mine, and both were exactly the failure mode this story exists to
prevent — a runner that silently proves less than it claims:

1. Discovery used the shared `unittest.defaultTestLoader`, which carries
   `testNamePatterns` from any `-k` filter. Under `-k ShardRunnerTest`
   discovery silently shrank from 516 units to **1**. It now uses a private
   loader.
2. The parent parsed human test output for counts and matched a fixture
   string inside a mocked result, undercounting 513 tests as **456**. Shards
   now emit a machine-readable JSON summary, and a shard that reports no
   summary is a failure rather than a silent zero.

## Acceptance mapping

- Sharded across processes, stdlib only, on the floor -> runner + 3.9 checks.
- Deterministic assignment, full coverage exactly once -> coverage identity
  assertion plus determinism and cover-once unit cases.
- Any shard failure fails the run -> failing-shard and no-summary cases.
- No cross-shard temp state -> every test owns its `mkdtemp` repository.
- Order dependence ruled out -> three consecutive sharded runs plus a
  different shard count, all agreeing with serial at 523 tests.
- Count and assertions unchanged; serial mode available -> `--serial`, and
  the `python-floor` CI job stays serial as a control.
- Wall-clock improvement recorded -> table above.

## Proof

### Captured run — 2026-07-26T21:54:11Z

- **Command:** `bash -lc set -e
uptime
echo '=== sharded run 1 ==='
python3 pmo-roadmap/tests/run-core-tests.py
echo '=== sharded run 2 (stability) ==='
python3 pmo-roadmap/tests/run-core-tests.py
echo '=== sharded run 3 (stability) ==='
python3 pmo-roadmap/tests/run-core-tests.py
echo '=== different shard count (3) ==='
python3 pmo-roadmap/tests/run-core-tests.py --shards 3
echo '=== serial run (agreement) ==='
python3 pmo-roadmap/tests/run-core-tests.py --serial
echo '=== runner unit cases ==='
python3 -m unittest pmo-roadmap/tests/dw-core-tests.py -k ShardRunnerTest
echo '=== coverage identity: units vs module load ==='
python3 -c "
import importlib.util, sys, unittest
spec=importlib.util.spec_from_file_location('r','pmo-roadmap/tests/run-core-tests.py')
r=importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
units=r.discover_units(); m=sys.modules['dw_core_tests_shard']; loader=unittest.TestLoader()
def flat(s):
    for x in s:
        if isinstance(x, unittest.TestSuite): yield from flat(x)
        else: yield x.id()
ids=[]
for u in units: ids.extend(flat(loader.loadTestsFromNames([u], m)))
full=list(flat(loader.loadTestsFromModule(m)))
assert sorted(ids)==sorted(full), 'sharded discovery differs from a module load'
assert len(ids)==len(set(ids)), 'a test would run more than once'
print('coverage identical:', len(ids), 'tests from', len(units), 'units, no duplicates')
"
echo '=== no test asserts a time-ceiling stop ==='
test 0 -eq $(grep -c 'time-ceiling' pmo-roadmap/tests/dw-core-tests.py) && echo 'confirmed: no assertion depends on the wall-clock guard'
echo '=== floor 3.9 ==='
/usr/bin/python3 -m py_compile pmo-roadmap/tests/run-core-tests.py
/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py --list
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/update.sh . --check
pmo-roadmap/bin/dw check work-log-automation
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9a05668428ab250fbc40255dd56d0fbf77eb9bd3

```text
15:54  up 3 days,  5:19, 7 users, load averages: 6.20 10.64 22.70
=== sharded run 1 ===
run-core-tests: 516 units across 8 shards + 1 serial
  shard 0:  61 tests in  105.9s  ok
  shard 1:  67 tests in   97.1s  ok
  shard 2:  63 tests in  109.5s  ok
  shard 3:  67 tests in  109.1s  ok
  shard 4:  71 tests in  116.1s  ok
  shard 5:  68 tests in  112.1s  ok
  shard 6:  63 tests in  114.3s  ok
  shard 7:  62 tests in  116.8s  ok
  shard 8:   1 tests in    1.8s  ok
run-core-tests: 523 tests in 118.6s (OK)
=== sharded run 2 (stability) ===
run-core-tests: 516 units across 8 shards + 1 serial
  shard 0:  61 tests in  116.9s  ok
  shard 1:  67 tests in  109.3s  ok
  shard 2:  63 tests in  120.1s  ok
  shard 3:  67 tests in  120.9s  ok
  shard 4:  71 tests in  127.0s  ok
  shard 5:  68 tests in  123.0s  ok
  shard 6:  63 tests in  125.5s  ok
  shard 7:  62 tests in  127.4s  ok
  shard 8:   1 tests in    1.9s  ok
run-core-tests: 523 tests in 129.4s (OK)
=== sharded run 3 (stability) ===
run-core-tests: 516 units across 8 shards + 1 serial
  shard 0:  61 tests in  112.0s  ok
  shard 1:  67 tests in  104.1s  ok
  shard 2:  63 tests in  115.3s  ok
  shard 3:  67 tests in  115.3s  ok
  shard 4:  71 tests in  120.5s  ok
  shard 5:  68 tests in  117.3s  ok
  shard 6:  63 tests in  118.9s  ok
  shard 7:  62 tests in  120.9s  ok
  shard 8:   1 tests in    1.7s  ok
run-core-tests: 523 tests in 122.5s (OK)
=== different shard count (3) ===
run-core-tests: 516 units across 3 shards + 1 serial
  shard 0: 173 tests in  171.4s  ok
  shard 1: 171 tests in  171.5s  ok
  shard 2: 178 tests in  172.7s  ok
  shard 3:   1 tests in    1.7s  ok
run-core-tests: 523 tests in 174.5s (OK)
=== serial run (agreement) ===
dw hook: codex_hooks is explicitly false in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.kl0h00ps/config.toml; respecting the opt-out
................................................................................................................................................................................................................................................dw-workbench: 127.0.0.1 "GET /api/runs/run-5e7de4366679500e92b50069/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-5e7de4366679500e92b50069/events?follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "POST /api/runs/run-5e7de4366679500e92b50069/events HTTP/1.1" 405 -
dw-workbench: 127.0.0.1 "GET /api/signals/events?remote=origin&branch=sse-x&follow=0 HTTP/1.1" 200 -
dw-workbench: 127.0.0.1 "GET /api/runs/run-000000000000000000000000/events?follow=0 HTTP/1.1" 400 -
......................................................................................................................................................dw-workbench: 127.0.0.1 "GET /api/programs/program-25037f5b6c737cf49a6b9820/events?from=0&follow=0 HTTP/1.1" 200 -
.....................................................................................................................................
----------------------------------------------------------------------
Ran 523 tests in 472.221s

OK
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.8wi0_uo6/settings.json
dw hook: claude — 0 installed, 4 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.8wi0_uo6/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test._ykxq5f7/settings.json
dw hook: claude — 4 installed, 0 already present in /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.yawezzp2/settings.json
dw hook: claude — 4 removed from /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/dw-hooks-test.yawezzp2/settings.json
##shard-summary {"ran": 523, "failures": 0, "errors": 0, "skipped": 0}
=== runner unit cases ===
..........
----------------------------------------------------------------------
Ran 10 tests in 0.029s

OK
=== coverage identity: units vs module load ===
coverage identical: 523 tests from 516 units, no duplicates
=== no test asserts a time-ceiling stop ===
=== floor 3.9 ===
shard 0:  61 units, cost~134
shard 1:  67 units, cost~134
shard 2:  63 units, cost~134
shard 3:  67 units, cost~134
shard 4:  69 units, cost~134
shard 5:  63 units, cost~134
shard 6:  63 units, cost~134
shard 7:  62 units, cost~133
serial tail: 1 unit(s) run quiet after the shards
docs-lint: ok (485 markdown files)
docs-lint.sh: ok (0s)
canon-lint.sh: ok
update.sh: up to date (vendored rails match source v1.14.0)
dw check: ok
```
