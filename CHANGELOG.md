# Changelog

Each release summarizes the roadmap phases that shipped it. Every
phase links its audit-style final summary — the roadmap under
[`pmo-roadmap/pm/roadmap/work-log-automation/`](./pmo-roadmap/pm/roadmap/work-log-automation/)
holds the full story-by-story evidence trail, and the version below is
single-sourced from `dw_pmo.__version__` (test-asserted against
`dw --version`, the plugin manifest, and this file).

## v1.5.0 — 2026-07-03

First public release: the framework, its workbench, its agent
surface, and the documentation pass that made it teachable — all
shipped through the framework's own gate.

### Phase 0 — Architecture ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-0-architecture/final-summary.md))

Established the architecture contract for work-log automation:
explicit consent, a two-step pre-commit capture / post-commit
finalize lifecycle, a deterministic Markdown entry schema, a deferred
summarizer boundary, and install/update plus git edge-case policies.
No model calls in the commit path — a rule everything later obeys.

### Phase 1 — MVP ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-1-mvp/final-summary.md))

Shipped the deterministic, opt-in MVP: PMO certification separated
from work-log consent, pre-commit capturing consented staged
payloads, post-commit appending local daily entries only after the
commit exists, and install/update distributing the canonical hooks
and helpers. Local by default.

### Phase 2 — Hardening ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-2-hardening/final-summary.md))

Hardened the automation: a deferred summarizer helper behind an
explicit opt-in command with timeout and output limits, deterministic
fallback behavior, and documented privacy controls around consent and
path exclusion. The source `*-work-summary.log` stays authoritative.

### Phase 3 — Rollout ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-3-rollout/final-summary.md))

Rolled the work-log extension out as opt-in and local-first, with
project exclusions (`PMO_WORK_LOG_EXCLUDE_REGEX`), documented privacy
limits, and temporary-repo regression coverage.

### Phase 4 — CLI maintenance tools ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-4-cli-maintenance-tools/final-summary.md))

Added the `dw` roadmap maintenance CLI: create phases and stories,
view trees, select the next actionable story, pair evidence, update
status, close phases, and report drift — Markdown stays the source of
truth, and a story cannot flip done without paired evidence.

### Phase 5 — Workbench interaction layer ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-5-pmo-workbench-interaction-layer/final-summary.md))

Delivered the workbench: a localhost read-only explorer, health/drift
console, intent-to-proof trace timeline, and a guarded editor routed
through core mutation plans — preview, diff, content-bound
fingerprints, stale/tamper 409s, rollback, revalidation. One core
(`dw_pmo`) now serves the CLI, the gate, and the workbench.

### Phase 6 — Agent rails hardening ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-6-agent-rails-hardening/final-summary.md))

Made the repo enforce itself end-to-end: the single-sourced gate
engine with parity-proven hooks, verified contract v2 (index-tree
freshness, gate-decided ceremony tiers), evidence-content lints with
captured runs, de-personalized canon under CI lint, and a full
lifecycle drivable from CLAUDE.md alone. CI runs ubuntu + macos,
shellcheck, and a python 3.9 floor job.

### Phase 7 — Documentation mastery ([phase folder](./pmo-roadmap/pm/roadmap/work-log-automation/phase-7-documentation-mastery/))

Audited every doc surface and rewrote to the audit's dispositions:
root README and architecture guide where every behavioral claim names
its proving test, canon accuracy with doc-parity tests, a Claude Code
plugin with parity against the managed agent-docs block, regenerated
demos/screenshots/social preview each naming its regeneration script,
docs CI (link/anchor/image lint plus quickstarts executed as
printed), and this release itself — contributing guide, code of
conduct, templates, changelog, tag.
