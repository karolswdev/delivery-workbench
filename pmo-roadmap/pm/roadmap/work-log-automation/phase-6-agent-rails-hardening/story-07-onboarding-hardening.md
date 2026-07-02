# WLA-6-07 - Harden onboarding and adoption bridge

- **Project:** work-log-automation
- **Phase:** 6
- **Status:** backlog
- **Depends on:** WLA-6-01
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Adoption is a six-step manual affair whose two most load-bearing steps —
pasting the agent snippet and setting `core.hooksPath` per clone — fail
silently when skipped. The highest-value hop in the flow is entirely
manual: adoption discovery produces machine-parseable tables (proposed
phase index, first stories), and the README then says "use that report to
decide," leaving the human to hand-scaffold what the report already
specifies. The path also has sharp edges: every documented adoption example
passes `--dangerous` (mapping to `--dangerously-skip-permissions` /
`--dangerously-bypass-approvals-and-sandbox`) even though safe modes exist;
`new-project.sh` and `adopt-project.sh` render templates with
`sed "s|{{X}}|$VAL|g"`, which breaks on `|`, `&`, or `\` in a project name;
`install.sh` silently clobbers an existing `.githooks/pre-commit` and
silently disables husky/lefthook by re-pointing hooksPath; the `.gitignore`
idempotency check misses `/.tmp/` variants; the rendered discovery prompt
embeds absolute machine paths into a committed artifact; and the
13-question intake invites Enter-through, producing "not provided" files
that degrade the discovery prompt downstream.

## Scope

- **In:** `dw adopt --from-report <adoption-discovery.md>`: parse the
  report's proposed phase and story tables into `dw phase create` /
  `dw story create` mutation plans with a preview-then-apply flow, closing
  the discovery-to-scaffold gap. Safety defaults: documented examples use
  read-only/sandboxed agent flags; `--dangerous` stays available but is
  framed as the exception with its risk stated. Rendering fixes: replace
  sed substitution with the safe bash substitution `session-intake.sh`
  already uses; stop persisting absolute paths into committed artifacts
  (render repo-relative). Installer honesty: warn and require confirmation
  (or `--force`) when overwriting an existing `pre-commit`, when hooksPath
  already points elsewhere, or when `.git/hooks` contains active
  non-sample hooks; extend the `.gitignore` check to common `.tmp`
  spellings; make `update.sh` manage the `.gitignore` entry too. Intake
  right-sizing: a 4-question core interview (goal, direction, constraints,
  handoff) with `--extended` restoring the full set; blank-heavy intakes
  get a visible "mostly unanswered" banner in the rendered file so the
  discovery prompt can weigh it. Per-clone protection comes from
  `dw doctor` (WLA-6-05); this story wires it into the adoption docs as the
  final verification step.
- **Out:** GUI onboarding (Phase 5); multi-repo orchestration; changing the
  discovery report format itself beyond making its tables parseable-stable.

## Acceptance criteria

- [ ] From a bare existing repo, adoption to working rails is three
  commands (install, intake+discovery, `dw adopt --from-report`) and ends
  with `dw doctor` reporting healthy — demonstrated in evidence on a temp
  clone.
- [ ] `dw adopt --from-report` previews the exact files it will create and
  applies only after confirmation; a hand-edited report with a malformed
  table fails with a line-numbered error, not a partial scaffold.
- [ ] A project named `A|B & C\D` installs, scaffolds, and renders
  correctly (injection regression test).
- [ ] `install.sh` run against a repo with husky-managed hooks warns before
  changing hook behavior; rerunning install/update never duplicates
  `.gitignore` entries or the agent-docs block.
- [ ] No committed artifact rendered by the bootstrap scripts contains an
  absolute local path (asserted by test).
- [ ] The intake core-mode interview asks at most 4 questions and the
  extended mode preserves today's full coverage;
  `pmo-roadmap/tests/adoption-discovery.sh` covers both.

## Test plan

- **Unit:** Report-table parser fixtures (well-formed, malformed, hostile
  strings) in the `dw_pmo` suite.
- **Integration / Cypress:** Extended
  `pmo-roadmap/tests/adoption-discovery.sh`: full three-command adoption on
  a temp repo, injection case, installer-warning cases, idempotent reruns.
- **Manual / device:** One real adoption run against a scratch clone of an
  unrelated project, recorded in evidence.

## Notes / open questions

The intake TTY interview remains untested by automation today; decide
during implementation whether to add an `expect`-style test or accept the
`--no-prompt` path as the tested surface and keep the interactive path
thin. The demo tapes hardcode the question sequence — update
`demos/onboarding.vhs` in the same change that reorders questions.
