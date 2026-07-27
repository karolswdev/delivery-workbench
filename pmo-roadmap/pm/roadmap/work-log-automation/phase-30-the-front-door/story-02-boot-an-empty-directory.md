# WLA-30-02 - Boot an empty directory

- **Project:** work-log-automation
- **Phase:** 30
- **Status:** backlog
- **Depends on:** WLA-30-01
- **Unblocks:** WLA-30-10
- **Owner:** unassigned

## Problem

The very first step of the journey is the only one with no support at all:
`install.sh` and `adopt-project.sh` both hard-fail on a directory that is
not a git repository, and nothing in the framework runs `git init`. A user
with an empty directory and an idea meets a refusal before they meet the
product. The fix is a single explicit command — `dw init <path>` — that
takes emptiness to healthy vendored rails and stops, leaving the next move
(the conversation) clearly signposted.

The danger is equally clear: a convenient boot command that reimplements
bootstrap becomes a second stack that drifts. `dw init` must be a façade
over the primitives that already exist — the packaged installer, the
launcher's bootstrap verbs, `new-project.sh`, session intake — composing
them, not replacing them.

## Scope

- **In:** a global `dw init <path>` verb in the launcher: initialize git if
  absent, install the vendored rails from the packaged payload (no
  framework checkout required), report what happened and what to do next.
  Idempotent re-runs that report what was already present. Refusal of a
  path nested inside an unrelated repository unless the target root is
  explicit. A status/doctor experience where "no roadmap project yet" reads
  as "setup required," not corruption.
- **Out:** creating any roadmap project, program policy, driver roster,
  grant, run, remote, branch beyond git's defaults, or commit; the
  conversation itself (WLA-30-03); changing what `install.sh` vendors;
  network installs beyond what the packaged payload already supports.

## Acceptance criteria

- [ ] `dw init <empty-directory>` yields a git repository with healthy
  vendored rails: `dw doctor` green, `dw status --json` reporting that
  project setup is required rather than an error.
- [ ] It also works in an existing empty git repository, and refuses a
  nested path inside an unrelated repository without an explicit root.
- [ ] A filesystem and `.git` assertion proves no roadmap, policy, roster,
  program state, grant, run, commit, or background process is created.
- [ ] Re-running is idempotent and reports already-present components.
- [ ] Inside the initialized repository, the global launcher defers to the
  vendored `.githooks/dw` unconditionally.
- [ ] The vendored rails are byte-identical to what `install.sh` produces
  on the same target, proven by test — the façade forks no behavior.

## Test plan

- **Unit:** path classification (empty dir, empty repo, nested path,
  already-initialized); idempotency reporting.
- **Integration:** package smoke from a genuinely empty temporary
  directory: init → `git rev-parse` → `dw doctor` → `dw status --json`,
  all captured; byte-parity check against a plain `install.sh` run;
  second-run idempotency capture.
- **Manual / device:** run `dw init` in a fresh directory and confirm the
  closing message tells a newcomer exactly what to do next.

## Notes / open questions

Whether `dw init` should end by offering to launch the intake conversation
directly (versus printing the command) is open; the default is print-only,
because starting an agent is a consent boundary this command should not
cross.
