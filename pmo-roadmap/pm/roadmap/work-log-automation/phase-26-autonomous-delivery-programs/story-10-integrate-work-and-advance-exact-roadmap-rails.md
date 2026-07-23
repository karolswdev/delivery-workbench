# WLA-26-10 — Integrate work and advance exact roadmap rails

- **Project:** work-log-automation
- **Phase:** 26
- **Status:** done
  <!-- status vocabulary: roadmap-builder.md §2.3 -->
- **Depends on:** WLA-26-07, WLA-26-08, WLA-26-09
- **Unblocks:** WLA-26-11, WLA-26-12
- **Owner:** unassigned

## Problem

Autonomous agents can produce and verify excellent work yet still leave the
roadmap stationary. The product promise requires governed integration: a green
proof packet must be able to materialize evidence, apply the exact validated
diff, certify only the assertions the grant authorizes, commit, push, complete
the story, close a completed phase, and start the next eligible work—without
turning “can write code” into ambient repository authority.

## Scope

- **In:** integration preview/claims/receipts; evidence materialization; exact
  isolated-diff apply; fresh mechanical + governed-verdict proof checks;
  machine attestation policy and audit identity; PMO contract generation/
  certification; gated commit with exact trailers; fast-forward push to bound
  remote/branch; observe/rebind; story done/next start; phase close/current
  pointer transition; idempotency/reconciliation; capability/budget/refusal
  boundaries; council-obligation disposition and separately authorized,
  deduplicated backlog/technical-debt story materialization.
- **Out:** merge, rebase/conflict auto-resolution, force push, release/deploy/
  publication, arbitrary commit messages, unsigned subjective attestation not
  authorized by policy, cross-repository transaction.

## Acceptance criteria

- [x] One pure preview binds exact program/ledger/proof/verdict/story/phase/
  repository/index/diff/remote facts and lists each separately authorized act;
  absent capability or failed/pending/dissenting/stale proof makes the plan
  non-applicable before any partial write.
- [x] Integration claims each step in dependency order, writes only the exact
  validated artifact/diff/evidence/roadmap/contract/message data, runs the real
  gate and range verification, and records content-safe result identities.
- [x] Machine certification is allowed only under an explicit capability and
  declared policy that maps every contract assertion to fresh mechanical or
  authorized governed-verdict evidence; the archive names program/grant/proof
  provenance and never pretends a human performed the attestation.
- [x] Commit and push are distinct finite capabilities; push requires the bound
  remote/branch and fast-forward relation, observes/rebinds the resulting fact,
  and refuses dirty/divergent/rewritten/cross-branch state without force.
- [x] Story completion, evidence link, next-story start, phase closure/current
  transition and subsequent planning use the canonical roadmap mutation/step
  cores with fresh leases and atomic validation—never direct ad-hoc Markdown
  edits.
- [x] An open blocking council obligation prevents story/phase advancement.
  Non-blocking obligations remain ledger-visible without forcing roadmap
  mutation; an exact preview may create/update one traced roadmap story only
  with separate `roadmap:write` authority, stable source-decision/obligation
  ids and deduplication. Completion, supersession, waiver or escalation retains
  the original obligation and accountable disposition receipt.
- [x] Crash/restart at every integration boundary reconciles existing evidence,
  status, contract archive, commit and remote ref before retry, producing zero
  duplicate evidence blocks, status flips, phase summaries, commits or pushes.
- [x] Red cases cover manual-only rubric, verifier dissent, missing meta-audit,
  stale proof, dirty tree, changed diff, gate refusal, hook failure, remote
  divergence, open blocking debt, duplicate obligation materialization,
  unauthorized waiver, capability/budget exhaustion, revocation and phase
  dependency.

## Test plan

- **Unit:** integration planning, capability, attestation mapping, idempotency,
  transition and refusal tests.
- **Integration:** clean fixture repo plus local bare remote performs two exact
  story commits and one phase transition, with crashes and divergent-remote red
  paths; `dw check` and `dw verify --all` finish green.
- **Manual / device:** inspect an autonomous contract archive/commit and verify
  its audit language names machine/program provenance accurately.

## Notes / open questions

This story deliberately crosses a previous boundary, but only through new
separate capabilities. It must update the canon that currently says
certification/commit are always manual; silent bypass or `--no-verify` is never
an implementation option.
