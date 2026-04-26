# PMO Roadmap Adoption Discovery

You are adopting an existing software project into the `pmo-roadmap`
framework. Treat this as read-only discovery. Do not edit files. Do not
commit. Do not run destructive commands.

## Project metadata

- **Project name:** {{PROJECT_NAME}}
- **Project slug:** {{PROJECT_SLUG}}
- **Story prefix:** {{PROJECT_PREFIX}}
- **Target repo:** {{TARGET_DIR}}
- **Discovery output requested:** {{OUTPUT_PATH}}
- **Session intake path:** {{INTAKE_PATH}}

## Mission

Inspect the repository and produce a practical adoption report that can become
the seed for `pm/roadmap/{{PROJECT_SLUG}}/`.

Before proposing phases or stories, read the session intake at:

```text
{{INTAKE_PATH}}
```

If that file is missing or incomplete, say so in the report and treat user
intent as unresolved. Do not let repository discovery turn into generic
reconnaissance; anchor every recommendation to what the user wants to accomplish
and what handoff they asked for.

The report must help a future agent answer:

1. What is this project?
2. What is already built?
3. What is currently risky, broken, unfinished, or unclear?
4. What commands prove health?
5. What roadmap phases and first stories should be created?
6. What PMO contract extensions, if any, are needed for this project?
7. Given the user's session goal, what should happen next?

## Required inspection

Look for, and cite paths for:

- Product or domain canon: README, docs, PRDs, design briefs, `CLAUDE.md`,
  `AGENTS.md`, plans, backlog, changelog, architecture docs.
- Build/test/lint commands: package scripts, Makefiles, task runners, CI files,
  shell scripts, language-specific config.
- Application architecture: entry points, major modules, data stores, APIs,
  UI surfaces, background jobs, deployment/runtime assumptions.
- Existing project-management artifacts: issues, story files, TODO docs,
  implementation logs, release notes.
- Current state signals: git status, branch, recent commits, uncommitted files,
  test posture, obvious failing or missing docs.
- Sensitive/noisy paths that should probably be excluded from work logs.

## Required output format

Write concise markdown with these sections:

```markdown
# {{PROJECT_NAME}} - PMO Adoption Discovery

- **Generated:** YYYY-MM-DD HH:MM
- **Repo:** {{TARGET_DIR}}
- **Branch:** ...
- **Reviewed by:** {agent/model}

## Executive Summary
{5-10 bullets: what exists, what matters, recommended adoption posture.}

## User Intent And Handoff
{Summarize the session intake: goal, desired direction, success evidence,
handoff expectations, constraints, and unresolved questions.}

## Source Canon
| Path | Why it matters | Confidence |
|---|---|---|

## Current Architecture
{Describe the actual system shape. Cite paths.}

## Current Delivery State
{What appears shipped, in progress, broken, stale, or unknown.}

## Build And Verification Commands
| Command | Purpose | Evidence / caveat |
|---|---|---|

## PMO Adoption Recommendation
- **Greenfield or post-launch:** ...
- **Recommended current phase:** ...
- **Roadmap root:** `pm/roadmap/{{PROJECT_SLUG}}/`
- **First adoption commit should include:** ...
- **How this serves the user's session goal:** ...

## Proposed Phase Index
| Phase | Goal | Why now |
|---|---|---|

## Proposed First Stories
| ID | Title | Acceptance evidence | Notes |
|---|---|---|---|

## Proposed Immediate Session Plan
| Step | Action | Evidence / handoff artifact |
|---|---|---|

## Contract Extensions
{Project-specific rules to add, or "none". Include possible mechanical checks.}

## Work-log Policy Suggestions
{Recommended `PMO_WORK_LOG_*` config, excluded paths, and consent guidance.}

## Risks And Stop Signals
| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|

## Open Questions For The User
- ...

## Recommended Next Action
{One concrete next move that advances the user's requested session outcome.}
```

## Standards

- Prefer cited file paths over general claims.
- Do not invent product intent where source canon is absent; mark it unknown.
- Do not mark tests as healthy unless you ran or found current evidence.
- If you run commands, include the exact commands and a short result.
- Keep the proposed first stories atomic enough for the PMO hook rules.
