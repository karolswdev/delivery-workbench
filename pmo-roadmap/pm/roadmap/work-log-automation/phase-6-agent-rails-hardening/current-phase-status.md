# Phase 6 - Agent Rails Hardening

**Last updated:** 2026-07-02.

## Goal

Convert the framework from choreography rails into verification rails:
single-sourced machine-checked gates, a durable audit trail, a first-class
agent surface, and proportionate ceremony — proven by running this
repository through its own gate.

## Why this phase exists

The 2026-07-02 architecture review found the framework strong at shaping
the sequence of agentic work (story -> evidence -> gated commit) but weak
at verifying it: five of seven contract rules are self-certified and the
whole checkbox block is one Write call for an agent; the two hard checks
have real bypasses caused by triple-implemented gate logic drifting across
bash and Python; the contract and bundle rationale are destroyed on
success, leaving zero durable trace in the default configuration; evidence
content is never inspected, and the dogfood roadmap's own evidence layer
was backfilled months after the work; the entire agent integration depends
on a manually pasted snippet that never mentions `dw`; and this repository
has never once passed through its own gate — every evidence file, `bin/dw`
itself, and phases 4-5 sit uncommitted. Phase 6 closes the gap between
what the framework claims and what it verifies.

## Operating principles

- **Verify, don't certify:** every rule that can be machine-checked gets
  machine-checked; the honor-system surface shrinks to what is genuinely
  unverifiable.
- **One gate implementation:** structural rules live once, in the `dw_pmo`
  core; hooks are shims.
- **Audit trail survives success:** contracts, bundle rationales, and
  story linkage outlive the commit that consumed them.
- **The agent is the primary user:** every failure message is a
  remediation instruction; every tool has machine-readable output and
  honest exit codes; discoverability does not depend on a human pasting a
  snippet.
- **Ceremony proportional to blast radius:** a docs typo and a shipped
  story do not pay the same tax.
- **Dogfood first:** every Phase 6 story ships through the rails it
  improves, on this repository.

## Scope

- **In:** Installing and enforcing the framework on this repo and landing
  the uncommitted phase 0-5 proof layer (WLA-6-01); a single `dw gate`
  engine replacing the triplicated checks, with the known bypass/bug
  family fixed (WLA-6-02); contract v2 with stamped machine-verified
  facts, index-tree freshness, commit trailers, and a contract archive
  (WLA-6-03); `dw evidence capture` and evidence-content linting
  (WLA-6-04); shipped agent commands, managed CLAUDE.md/AGENTS.md blocks,
  `dw doctor`, and agent-honest CLI ergonomics (WLA-6-05); tiered
  contracts, one status vocabulary, de-personalized templates, lighter
  closure artifacts (WLA-6-06); a discovery-report-to-scaffold bridge,
  safe-by-default adoption, injection and installer fixes, slimmer intake
  (WLA-6-07); negative-path gate tests, macOS + shellcheck CI matrix, and
  workflow hygiene (WLA-6-08).
- **Out:** The workbench UI and server (Phase 5 owns WLA-5-03..10);
  hosted/multi-repo modes; default-on work logging; log retention policy;
  Windows support; rewriting pre-Phase-6 git history.

## Exit criteria (evidence required)

- [ ] `git config core.hooksPath` is `.githooks` in this repo,
  `git status --porcelain` is empty, and every Phase 6 commit carries
  `PMO-Story:` and `PMO-Contract-Digest:` trailers.
- [x] `dw context work-log-automation --trace` resolves at least one story
  through the full chain: story -> evidence -> commit -> contract digest ->
  work-log entry (WLA-6-03 via faa7de6; evidence-story-03).
- [x] `hooks/pre-commit` contains no structural rule logic;
  `pmo-roadmap/tests/gate-parity.sh` proves shim and `dw gate` agree on
  the drift-bug fixture set (synonyms, padding, deletions, renames,
  spaces, capital-X) (evidence-story-02).
- [x] Reusing a contract after restaging is blocked by index-tree mismatch;
  `touch .tmp/CONTRACT.md` no longer refreshes staleness (CI-run: parity
  S17 + unit tamper matrix; evidence-story-03).
- [x] `dw check` errors on placeholder/empty evidence for done stories, and
  `dw evidence capture` output appears in at least two real Phase 6
  evidence files (evidence-story-04 + evidence-story-05, both carrying
  the tool's own captured runs; lints CI-run in roadmap-cli.sh).
- [x] A fresh temp-repo install yields an agent-completable story lifecycle
  using only `CLAUDE.md` guidance and shipped commands; `dw doctor` exits
  0 there and here (agent-surface.sh, CI-run; evidence-story-05).
- [x] A docs-only commit passes with the short-form contract; a
  story-flipping commit with a short-form contract is blocked (both in
  CI: parity S24/S25 + unit tier tests; evidence-story-06).
- [x] No canonical template contains personal paths, private memory
  references, Pantrybot content, or dead links (canon-lint.sh green in
  CI; evidence-story-06).
- [x] Three-command adoption on a temp clone ends with `dw doctor` healthy;
  the hostile-name injection test passes (adoption-discovery.sh, CI-run;
  evidence-story-07).
- [ ] `.github/workflows/validation.yml` runs the full suite green on
  ubuntu and macos with least-privilege permissions, shellcheck, and
  `dw check work-log-automation`.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-6-01 | Restore dogfood integrity and land the working tree through the rails | done | [story-01-dogfood-integrity](./story-01-dogfood-integrity.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-6-02 | Unify the commit gate into a single dw gate engine | done | [story-02-single-gate-engine](./story-02-single-gate-engine.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-6-03 | Ship verified contract v2 with durable audit trail | done | [story-03-verified-contract-v2](./story-03-verified-contract-v2.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-6-04 | Add evidence capture tooling and content linting | done | [story-04-evidence-capture](./story-04-evidence-capture.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-6-05 | Ship the first-class agent surface | done | [story-05-agent-surface](./story-05-agent-surface.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-6-06 | Right-size ceremony and unify template canon | done | [story-06-ceremony-proportionality](./story-06-ceremony-proportionality.md) | [evidence-story-06](./evidence-story-06.md) |
| WLA-6-07 | Harden onboarding and adoption bridge | done | [story-07-onboarding-hardening](./story-07-onboarding-hardening.md) | [evidence-story-07](./evidence-story-07.md) |
| WLA-6-08 | Harden CI, parity, and portability testing | backlog | [story-08-ci-parity-hardening](./story-08-ci-parity-hardening.md) | - |

## Execution sequence

1. WLA-6-01 lands the uncommitted working tree through installed rails —
   nothing else ships until the repo obeys its own gate, and the friction
   log it produces is input to WLA-6-02.
2. WLA-6-02 unifies the gate into the `dw_pmo` core (coordinate with
   WLA-5-02, which extracts that core) and fixes the bypass/bug family.
3. WLA-6-03 and WLA-6-04 build on the unified gate: verified contracts
   with a durable trail, then evidence capture and linting.
4. WLA-6-05 ships the agent surface once the contract and evidence
   commands exist to surface.
5. WLA-6-06 right-sizes ceremony last among the semantic changes, because
   tier boundaries depend on contract v2 and the agent commands.
6. WLA-6-07 and WLA-6-08 can run in parallel with 03-06 after their
   dependencies land; WLA-6-08 keeps the CI matrix growing as each story
   adds tests.

## Where we are

WLA-6-07 is done with evidence: adoption is three commands ending in
`dw doctor` healthy — `dw adopt --from-report` turns the discovery
report's stabilized tables into the roadmap scaffold with
preview-then-apply and line-numbered refusals; rendering is
injection-proof and repo-relative; the installer refuses foreign hook
managers without `--force` and warns about hooks it disables; the
intake asks 4 core questions (full set behind `--extended`) and flags
Enter-through intakes. One story remains: WLA-6-08 (CI, parity, and
portability hardening) closes the phase — macOS matrix, shellcheck,
workflow hygiene, and the checkout action bump.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Two open phases (5 and 6) fork attention and the roadmap loses a single "current phase" | high | Sequence explicitly: WLA-6-01 first, then WLA-5-02, then WLA-6-02; phase 5 UI stories stay untouched until the gate work lands | A commit ships UI code while any WLA-6-02/03 acceptance box is unchecked |
| Landing the working tree (WLA-6-01) hits the known gate bugs and stalls | medium | Known escape hatches documented per commit; frictions recorded as WLA-6-02 input, not fixed inline | More than one `--no-verify` is proposed to complete the landing |
| Contract v2 fact-checking gets gamed the same way checkboxes were | medium | Stamp only facts the gate can re-derive (index tree, branch, staged list); treat unverifiable additions as out of scope | A stamped fact is added that the gate cannot independently recompute |
| Gate rewrite breaks consumer projects mid-update | medium | Parity suite runs old shim vs new engine on shared fixtures before the shim flips; update.sh keeps config/local seams | Any parity fixture verdict differs between old and new gate |
| python3 hard dependency blocks a consumer environment | low | Fail-closed shim message names the dependency and the one-line install; docs updated | A consumer reports a blocked commit with no actionable message |
| Ceremony tiering becomes a bypass lane | medium | Tier is chosen by the gate from staged paths, not self-declared; story-flipping commits always require the full contract | A story flips done in a commit that passed on the short form |

## Decisions made (this phase)

- 2026-07-02 - Phase 6 exists and precedes further Phase 5 UI work -
  building an interaction layer over a gameable gate multiplies the wrong
  thing - 2026-07-02 architecture review, user direction to dogfood the
  fix as its own phase.
- 2026-07-02 - The gate becomes a `dw_pmo` consumer, python3 becomes a
  hard dependency of enforcement, and the "pure bash" claim is retired -
  three drifting implementations are the root cause of the known bypasses -
  review findings.
- 2026-07-02 - Contract freshness moves from file mtime to index-tree
  identity - mtime is defeated by `touch` and clock skew; the index tree
  is what the contract actually certifies - review findings.
- 2026-07-02 - This repo's work log lives in the framework default
  `~/.work/log` - hooks (config-driven) and dw/work-log-read
  (env-or-default) agree without per-shell setup - WLA-6-01 execution.
- 2026-07-02 - `.githooks/` copies are committed, consumer-style, with
  source of truth in `pmo-roadmap/hooks` and `bin`; refresh via
  `update.sh` - WLA-6-01 execution.
- 2026-07-02 - The pre-Phase-6 landing commits keep their non-parsing
  `PMO-Story:` body lines (a blank line separated them from the trailer
  block) - rewriting would dangle the work-log entries' recorded SHAs;
  the defect is preserved as WLA-6-03 evidence - WLA-6-01 execution.

## Decisions deferred

- Whether the contract archive is mirrored into a committed append-only
  audit file - revisit after WLA-6-03 dogfooding - default is local
  `.git/pmo-contract-archive/` plus digest trailers only.
- Whether `dw` gets a PATH launcher or stays `.githooks/dw` - decide in
  WLA-6-05 - default is documented canonical invocation plus `dw doctor`
  guidance.
- Where this repo's work log lives (default `~/.work/log` vs
  repo-adjacent) - decide during WLA-6-01 - default is the framework
  default.
- Whether the interactive intake gets an expect-style test - decide in
  WLA-6-07 - default is the `--no-prompt` path as the tested surface.
