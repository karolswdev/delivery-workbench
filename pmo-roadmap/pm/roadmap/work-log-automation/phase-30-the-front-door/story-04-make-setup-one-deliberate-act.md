# WLA-30-04 - Make setup one deliberate act

- **Project:** work-log-automation
- **Phase:** 30
- **Status:** done
- **Depends on:** WLA-30-01
- **Unblocks:** WLA-30-03, WLA-30-05, WLA-30-10
- **Owner:** unassigned

## Problem

Everything else in Delivery Workbench mutates under the deliberate-step
discipline — a fresh hash-bound preview, an exact single-use token, an
apply that revalidates and refuses on drift. Roadmap setup does not:
`dw adopt --apply`, `dw phase create`, and `dw story create` write on
invocation. That was tolerable when only operators touched them; with a
conversational front door drafting multi-file setups, it is the gap
through which drafting becomes authorizing. Setup must become one guarded,
atomic act: the whole proposal lands, or none of it does.

## Scope

- **In:** `dw setup preview <proposal>` producing a canonical preview —
  every tracked and `.git`-local path affected, before/after hashes,
  diagnostics, one single-use `expect` token. `dw setup apply
  --proposal <id> --expect <token>` as the only public apply path for a
  multi-file setup: no replacement document, paths, policy, or behavioral
  flags at apply time. Apply-time revalidation of repository identity,
  branch, HEAD, index tree, roadmap hashes, policy hashes, and driver
  roster hash — any drift invalidates the token without writing. A
  recoverable transaction over roadmap README, phase files, story files,
  tracked policy, and local roster; a planted mid-transaction failure
  leaves the pre-apply state intact. The legacy mutation paths (`adopt`,
  `phase create`, `story create`) either adopt the same preview/expect
  protocol or become internal planning primitives invoked through it.
  CLI, MCP, and HTTP parity.
- **Out:** program grants (a separate token on the existing surface —
  never derivable from a setup token); certification and commit; any
  automatic chaining from apply into grant or run.

## Acceptance criteria

- [ ] Preview returns the complete canonical change set with hashes,
  diagnostics, and one single-use lease; previews are byte-equivalent for
  the same proposal and observation across CLI, MCP, and HTTP.
- [ ] Apply accepts only proposal identity plus token, revalidates every
  observed fact, and a mutation matrix (changed HEAD, index, roadmap,
  policy, roster, token reuse, malformed proposal) proves each case
  refuses without writing.
- [ ] The apply is atomic: a planted failure mid-transaction leaves the
  repository byte-identical to its pre-apply state.
- [ ] One apply creates no grant, run, certification, or commit, proven by
  test.
- [ ] The legacy setup mutations are brought under the protocol or
  demoted to internal primitives, with their documented flows updated.
- [ ] A setup token and a program start token are different types,
  non-substitutable, and separately stale, proven by test.

## Test plan

- **Unit:** token minting/expiry/single-use; canonical preview
  serialization; transaction rollback.
- **Integration:** happy-path and stale-token captures on all three
  transports; the full mutation matrix; planted-failure rollback proof;
  existing roadmap-mutation and package suites green.
- **Manual / device:** walk preview → review → apply once by hand and
  confirm the preview is genuinely readable before consenting.

## Notes / open questions

How far to demote `phase create`/`story create` is the main judgment
call: operators still deserve a quick single-file path, but it must not
remain a side door around the proposal discipline for multi-file setups.
Default: single-file creates keep a lightweight confirm, multi-file setups
require the full lease.
