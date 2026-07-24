# Phase 26 closeout handover

**Snapshot:** 2026-07-23, after WLA-26-12
**Branch:** `agent/wla-26-09-conductor`
**Roadmap state:** Phase 26 complete, 12/12
**Delivery state:** the full Phase 26 sequence is on the draft-PR branch; no
merge, release, deployment, or publication has been performed

This is the closeout snapshot. The authoritative outcome is
[final-summary](./final-summary.md); exact exit proof is
[evidence-story-12](./evidence-story-12.md).

## What is complete

Phase 26 adds an explicitly configured autonomous-program layer without
changing vanilla Delivery Workbench or Phase 24/25 bounded orchestration.
Across WLA-26-01 through WLA-26-11 the branch delivered:

- pure multi-phase scope planning and deterministic assignment;
- finite reusable hierarchical workflows and structural loops;
- organizations with exact seat, provider/model/auth/principal/workspace/
  session provenance and enforced separation;
- governed rubrics, mechanical facts, independent verdicts, panels, councils,
  dissent, meta-audits, architect gates, and carried obligations;
- lossless Program Studio authoring;
- one immutable finite revocable program grant and hash-chained ledger;
- a replay-first conductor over child runs, outward facts/nudges, selection,
  story/phase continuation, and exact scope completion;
- separately claimed evidence, integration, contract, certification, commit,
  fast-forward push, obligation, story, and phase delivery rails; and
- one canonical CLI/MCP/HTTP/Workbench/SSE/notification/stream surface.

WLA-26-12 composes those slices from an installed wheel. One continuous grant
delivers three stories across two phases with an independent reject/repair/
pass, a dissent-preserving council, one carried non-blocking obligation, a full
meta-audit, two architect gates, three commits and pushes, and crash recovery
at conductor and delivery effect/receipt boundaries. The final ledger and SSE
stream contain the same 203 events.

## Default invariant

A separate fresh installed-wheel consumer proves that no program policy is
normal healthy state. It creates no program or notification store, grant, run,
process, observer, poller, stream, notification, network activity, required
setup, or Workbench front-door detour. Ordinary status, next, step, gate,
roadmap, Workbench, and optional bounded-orchestration reads remain available.

Do not weaken this invariant when changing installation, startup, Workbench
routing, or public adapters.

## Exam and regression entry points

- `pmo-roadmap/tests/autonomous-program-packaged-exam.py` — fresh-wheel green,
  red, surface-parity, recovery, and no-program proof.
- `pmo-roadmap/tests/package-smoke.sh` — mandatory distribution entry point;
  runs the Phase 26 exam after the earlier guided/bounded/outward exams.
- `pmo-roadmap/tests/workbench-ui-smoke.sh` — 60 desktop/mobile renders,
  including real active, council-certified, and revoked program ledgers.
- `OrchestrationDriverTest.
  test_git_diff_artifact_keeps_exact_nested_untracked_paths` — regression for
  the exact nested untracked path defect found by the full exam.

The exam's adapter roster uses deterministic injected fixtures behind exact
Claude/Sonnet-like and pi/OpenRouter/Kimi-like shipped adapter contracts. This
is the CI oracle. It uses no credentials and makes no claim about live model
quality. The optional authenticated live-agent specimen is recorded as
`not-run`.

## Boundaries that remain

- Merge, release, tag, PyPI upload, Homebrew publication, deploy, and public
  hosting remain outside the program grant and outside this phase.
- Automatic conflict resolution and force push remain forbidden.
- Cross-repository portfolios and hosted/cross-machine authority remain
  deferred.
- Homebrew local validation may abstain when the operator formula is installed;
  the clean-machine macOS CI lane owns that proof.

## Next phase direction

Open Phase 27 around plain-language product and information design for the
application layer. Keep exact protocol names in code, machine contracts,
architecture, and an explicit audit/technical view, but stop exposing them as
the normal way to use the tool.

The phase should cover Program Studio, delivery-plan setup, teams and councils,
the live run screen, help, errors, onboarding, and everyday docs. A person
should be able to answer, in ordinary terms: What are we delivering? Who is
doing and reviewing it? What passed? What is blocked? Who needs to decide?
What can the run still spend or change? What happens next? One concept should
have one stable product name across every surface.

This must be a coherent task and information-architecture redesign, not a
find-and-replace alias layer over the same confusing screens. Landing and
release remain separate owner decisions; do not infer merge, version, tag,
publication, formula, or deployment authority from Phase 26 completion.
