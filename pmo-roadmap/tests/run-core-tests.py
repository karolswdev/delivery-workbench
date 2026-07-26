#!/usr/bin/env python3
"""Run the dw core suite sharded across processes (WLA-28-04).

The suite is embarrassingly parallel and did not know it: every test builds
its own temporary repository under ``mkdtemp`` and cleans it up, so there is
no shared fixture to contend over. What was missing was a runner that spreads
work across processes.

Standard library only, on the declared 3.9 floor — this repository proves
itself without test dependencies, so ``pytest-xdist`` is not an option.

Usage:
    run-core-tests.py                  # sharded, auto shard count
    run-core-tests.py --shards 4       # explicit
    run-core-tests.py --serial         # one process, for debugging
    run-core-tests.py --list           # print the assignment and exit

Sharding is by test method, because per-test setUp is cheap (~0.3s even for
the deepest nested program fixture). The exception is a class defining its own
``setUpClass``: that cost is paid once per process, so such classes stay whole
rather than paying it in every shard they would touch.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SUITE = TESTS_DIR / "dw-core-tests.py"

SHARD_SUMMARY_PREFIX = "##shard-summary "

# Relative cost hints in seconds, used only to balance shards. Correctness
# never depends on them: a missing or stale hint changes how work is
# distributed, never which tests run. Measured on the desk 2026-07-26.
COST_HINTS = {
    "ProgramDeliveryTest.test_two_story_commits_phase_transition_and_every_effect_recover": 68,
    "ProgramConductorTest.test_rule_council_meta_audits_and_ingests_durable_obligation": 54,
    "ProgramConductorTest.test_tie_checkpoint_and_decision_receipt_crash_are_idempotent": 40,
    "ProgramConductorTest.test_judge_council_binds_only_the_preassigned_decider": 38,
    "ProgramConductorTest.test_crashes_around_claim_dispatch_and_receipt_never_duplicate_start": 32,
    "ProgramDeliveryTest.test_commit_hook_and_remote_divergence_fail_closed_without_force": 32,
    "ProgramDeliveryTest.test_blocking_obligation_and_missing_capability_refuse_before_write": 29,
    "ProgramConductorTest.test_cross_phase_continuation_carries_obligation_and_completes_scope": 25,
    "ProgramConductorTest.test_outward_fact_delivers_one_bounded_restart_safe_nudge": 22,
    "ProgramConductorTest.test_phase_architect_receipt_crash_recovers_before_typed_checkpoint": 22,
    "ProgramDeliveryTest.test_obligation_materialization_deduplicates_and_waiver_is_accountable": 20,
    "ProgramConductorTest.test_phase_architect_veto_stops_before_integration": 18,
    "ProgramDeliveryTest.test_preview_is_pure_and_refuses_missing_mechanical_or_dirty_facts": 17,
    "ProgramConductorTest.test_failed_verdict_takes_one_claimed_repair_then_reverifies": 17,
    "ProgramConductorTest.test_phase_architect_approves_exact_frozen_boundary": 17,
    "ProgramDeliveryTest.test_changed_candidate_artifact_refuses_as_stale_proof": 16,
    "ProgramConductorTest.test_fanout_fanin_collect_and_closed_check_replay_stably": 16,
    "ProgramConductorTest.test_nudge_receipt_crash_recovers_delivery_and_target_once": 16,
    "ProgramConductorTest.test_structural_loop_records_typed_green_round_and_lineage": 15,
    "ProgramConductorTest.test_structural_loop_advances_round_then_routes_exhaustion": 15,
    "ProgramConductorTest.test_blocking_obligation_stops_cross_story_selection": 11,
    "ProgramConductorTest.test_structural_loop_receipt_crash_recovers_exactly_once": 11,
    "ProgramConductorTest.test_tick_conducts_implementer_then_independent_verifier": 9,
    "ProgramConductorTest.test_crash_after_closed_check_observation_does_not_rerun_check": 8,
    "ProgramSurfaceTest.test_exact_act_tokens_strict_allowlists_and_bounded_supervision": 7,
    "ProgramConductorTest.test_missing_session_after_durable_dispatch_stops_uncertain": 7,
}
DEFAULT_COST = 1

# Units that must not run while the machine is saturated. These spawn real
# child processes and assert on wall-clock responsiveness, so a busy box makes
# them fail for reasons that have nothing to do with the code under test.
# They are run in one quiet process after the shards finish rather than being
# weakened — a test that proves live cancellation has to be allowed to observe
# a live process. Coverage is asserted: shards + tail == every unit.
# An entry may name a whole class or a single "Class.method".
SERIAL_TAIL = (
    # Spawns real check processes and asserts they respond within tight
    # wall-clock budgets — one case polls 100 x 20ms for a fresh interpreter to
    # publish a receipt. On a loaded machine that budget expires for reasons
    # unrelated to the code under test. Observed failing under load in
    # test_cancellation_interrupts_a_live_contained_check and
    # test_builtin_file_schema_diff_and_rail_checks_share_receipts, so the
    # whole class runs quiet rather than weakening its timing assertions.
    "OrchestrationConductorTest",
)


def is_serial(unit: str) -> bool:
    """True when a unit is declared timing-sensitive, by class or by method."""
    return unit in SERIAL_TAIL or unit.split(".", 1)[0] in SERIAL_TAIL


def _load_suite_module():
    spec = importlib.util.spec_from_file_location("dw_core_tests_shard", SUITE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["dw_core_tests_shard"] = module
    spec.loader.exec_module(module)
    return module


def discover_units() -> "list[str]":
    """Return the schedulable units: test ids, or whole classes when atomic.

    A class defining its own ``setUpClass`` pays that cost once per process,
    so it is scheduled as one unit instead of being split across shards.
    """
    module = _load_suite_module()
    # A private loader, never unittest.defaultTestLoader: the shared default
    # carries testNamePatterns from a -k filter, which would silently shrink
    # discovery to whatever the caller happened to be filtering for.
    loader = unittest.TestLoader()
    units: "list[str]" = []
    for name in dir(module):
        obj = getattr(module, name)
        if not (isinstance(obj, type) and issubclass(obj, unittest.TestCase)):
            continue
        if obj is unittest.TestCase:
            continue
        methods = loader.getTestCaseNames(obj)
        if not methods:
            continue
        if "setUpClass" in obj.__dict__ or "setUpModule" in obj.__dict__:
            units.append(name)  # atomic: keep the shared fixture in one process
        else:
            units.extend(f"{name}.{m}" for m in methods)
    return sorted(units)


def unit_cost(unit: str) -> int:
    if unit in COST_HINTS:
        return COST_HINTS[unit]
    # An atomic class carries the cost of all its hinted methods.
    prefix = unit + "."
    total = sum(cost for name, cost in COST_HINTS.items()
                if name.startswith(prefix))
    return total or DEFAULT_COST


def assign_shards(units: "list[str]", shard_count: int) -> "list[list[str]]":
    """Distribute units across shards, deterministically.

    Longest-processing-time-first: order by cost descending, then by name so
    equal costs never depend on dict or filesystem ordering, and greedily place
    each unit on the currently lightest shard. Same inputs, same assignment.
    """
    if shard_count < 1:
        raise ValueError("shard count must be at least 1")
    shards: "list[list[str]]" = [[] for _ in range(shard_count)]
    loads = [0] * shard_count
    for unit in sorted(units, key=lambda u: (-unit_cost(u), u)):
        lightest = loads.index(min(loads))
        shards[lightest].append(unit)
        loads[lightest] += unit_cost(unit)
    return [sorted(shard) for shard in shards]


def default_shard_count() -> int:
    cpus = os.cpu_count() or 2
    return max(1, min(8, cpus - 2))


def _shard_worker(names: "list[str]") -> int:
    """Run the named units in this process and report counts as JSON.

    The parent must not parse human test output to learn what ran: test
    output can itself contain lines like "Ran 1 test in 0.0s" (a mocked runner
    result, a nested suite), and an earlier version of this runner undercounted
    513 tests as 456 by matching one of those. A machine-readable summary
    removes the guesswork.
    """
    module = _load_suite_module()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(names, module)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(suite)
    summary = {
        "ran": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
    }
    print(SHARD_SUMMARY_PREFIX + json.dumps(summary))
    return 0 if result.wasSuccessful() else 1


def _run_shard(names: "list[str]") -> "tuple[int, str, float, dict]":
    started = time.time()
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--shard-worker", *names],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    summary = {}
    for line in proc.stdout.splitlines():
        if line.startswith(SHARD_SUMMARY_PREFIX):
            summary = json.loads(line[len(SHARD_SUMMARY_PREFIX):])
    return proc.returncode, proc.stdout, time.time() - started, summary


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description="Run the dw core suite sharded.")
    parser.add_argument("--shards", type=int, default=None)
    parser.add_argument("--serial", action="store_true",
                        help="run everything in one process (debugging)")
    parser.add_argument("--list", action="store_true",
                        help="print the shard assignment and exit")
    parser.add_argument("--shard-worker", nargs="+", metavar="UNIT",
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.shard_worker:
        return _shard_worker(args.shard_worker)

    if args.serial:
        # One process, compact output: the verbose per-test stream is fine
        # interactively but overruns evidence-capture output budgets, which
        # once truncated away the only copy of a real failure.
        units = discover_units()
        return _shard_worker(units)

    units = discover_units()
    if not units:
        print("run-core-tests: found no tests", file=sys.stderr)
        return 1

    tail = [u for u in units if is_serial(u)]
    parallel_units = [u for u in units if not is_serial(u)]
    shard_count = max(1, min(args.shards or default_shard_count(),
                             len(parallel_units) or 1))
    shards = assign_shards(parallel_units, shard_count)

    if args.list:
        for i, names in enumerate(shards):
            cost = sum(unit_cost(n) for n in names)
            print(f"shard {i}: {len(names):3d} units, cost~{cost}")
        if tail:
            print(f"serial tail: {len(tail)} unit(s) run quiet after the shards")
        return 0

    print(f"run-core-tests: {len(units)} units across {shard_count} shards"
          + (f" + {len(tail)} serial" if tail else ""))
    started = time.time()

    # Threads only supervise subprocesses; the work happens in the children,
    # so the GIL is irrelevant here.
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=shard_count) as pool:
        futures = [pool.submit(_run_shard, names) for names in shards]
        results = [f.result() for f in futures]

    # The machine is quiet again; now the timing-sensitive units may run.
    if tail:
        results.append(_run_shard(tail))

    total_tests = 0
    failed = []
    for index, (code, output, seconds, summary) in enumerate(results):
        if not summary:
            # A shard that produced no machine-readable summary crashed before
            # reporting. Never silently count it as zero and pass.
            failed.append((index, output))
            print(f"  shard {index}: NO SUMMARY in {seconds:6.1f}s  FAIL")
            continue
        ran = summary["ran"]
        total_tests += ran
        print(f"  shard {index}: {ran:3d} tests in {seconds:6.1f}s  "
              f"{'ok' if code == 0 else 'FAIL'}")
        if code != 0:
            failed.append((index, output))

    elapsed = time.time() - started
    print(f"run-core-tests: {total_tests} tests in {elapsed:.1f}s "
          f"({'FAILED' if failed else 'OK'})")

    for index, output in failed:
        print(f"\n{'=' * 70}\nshard {index} output\n{'=' * 70}\n{output}",
              file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
