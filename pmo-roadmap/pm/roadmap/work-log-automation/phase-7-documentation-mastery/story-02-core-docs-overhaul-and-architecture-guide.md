# WLA-7-02 - Core docs overhaul and architecture guide

- **Project:** work-log-automation
- **Phase:** 7
- **Status:** done
- **Depends on:** WLA-7-01
- **Unblocks:** WLA-7-05, WLA-7-06, WLA-7-07
- **Owner:** unassigned

## Problem

The root README and framework README carry seven phases of accretion.
They must become deliberate: a root README that sells and orients in
one screen, per-audience quickstarts that a cold reader can follow
verbatim, and an architecture guide that explains the system (core,
gate, contracts, evidence, workbench, work logs) as designed rather
than as accumulated.

## Scope

- **In:** Root README rewrite (what/why/quickstart/proof links),
  framework README restructure per the audit IA, a new
  `docs/architecture.md` (dw_pmo core, gate engine, contract v2
  lifecycle, evidence capture, workbench runtime, work-log pipeline —
  with Mermaid diagrams), a troubleshooting/FAQ section fed by the
  Phase 6 friction log, and link-replacement of duplicated content.
- **Out:** Canon rule-document changes (WLA-7-03), rendered assets
  (WLA-7-05).

## Acceptance criteria

- [ ] The root README's first screen states what the framework is,
  who it is for, and the three-command adoption path.
- [ ] Each audience quickstart from WLA-7-01 exists and was executed
  verbatim in a fresh fixture with output captured.
- [ ] `docs/architecture.md` covers all six subsystems with at least
  one accurate Mermaid diagram each; every claim about behavior names
  the test or command that proves it.
- [ ] No topic is owned by two documents; cross-references are links.
- [ ] All commands shown in the rewritten docs run as printed
  (captured).

## Test plan

- **Unit:** n/a.
- **Integration:** captured verbatim runs of every quickstart;
  docs-lint/link pass once WLA-7-06 lands.
- **Manual / device:** cold read of each path; render check on GitHub.
