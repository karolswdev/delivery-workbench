# Deliberate step contract

**Status:** v1 preview and result contracts implemented across CLI, MCP, and
HTTP; the three adapters return byte-equal core documents.
**Scope:** local preview and explicit application of exactly one current,
allowlisted status recommendation.

## Purpose

`dw status` answers what should happen next without changing anything.
`dw step` is the separate act boundary:

```text
observe current status → preview one state-bound lease → explicitly apply
                       → run at most one child → stop and observe again
```

The split is intentional. Reading status is never consent to mutate, and
calling a convenience command is never consent to certify a contract or
create a commit.

## CLI flow

Preview first:

```bash
.githooks/dw step [project]
.githooks/dw step [project] --json
```

Human output names the underlying command, the state token, whether the
action is applicable, and the exact tokenized apply argv:

```text
step=preview action=start-story applicable=yes
command=.githooks/dw story status myapp 2 APP-2-01 in-progress
token=sha256:...
apply=.githooks/dw step myapp --apply --expect sha256:...
refusal=-
```

After reviewing that preview, invoke its exact `apply=` command. Apply
rebuilds the complete preview immediately before starting anything. A token
mismatch refuses with remediation and starts no child process. A successful
application runs the one already-present argv from the repository root,
mirrors its exit code, observes the next action, reports it, and stops.

`--expect` without `--apply` is a usage error. Apply without `--expect`
returns a non-started refusal. Add `--json` to apply to receive the stamped
result receipt without mixing child output into the protocol stream:

```bash
.githooks/dw step myapp --json --apply --expect sha256:...
```

## Preview model v1

The pure document has an exact, test-pinned key set:

```json
{
  "kind": "delivery-workbench-step",
  "schema_version": 1,
  "project": "myapp",
  "token": "sha256:0123456789abcdef...",
  "action": {
    "id": "start-story",
    "kind": "command",
    "blocking": false,
    "reason": "APP-2-01 is the next actionable story",
    "command": [
      ".githooks/dw", "story", "status", "myapp", "2",
      "APP-2-01", "in-progress"
    ]
  },
  "applicable": true,
  "refusal": null,
  "apply_command": [
    ".githooks/dw", "step", "myapp", "--apply", "--expect",
    "sha256:0123456789abcdef..."
  ]
}
```

`action` is the complete `next_action` from
`delivery-workbench-status@1`; clients do not reconstruct it.
`apply_command` is present only when the action is applicable. Preview exits
zero even for a prohibited/manual action because the refusal itself is a
valid answer.

## Transport bindings

All three transports call `step.build_step` and `step.apply_step` directly.
They add framing, never policy, argv, or a second token implementation:

| Transport | Preview | Explicit apply |
|---|---|---|
| CLI | `dw step [project] --json` | `dw step [project] --json --apply --expect <token>` |
| MCP | `dw_step {project?}` | `dw_step_apply {project?, expect}` |
| HTTP | `GET /api/step?project=<slug>` | `POST /api/step/apply` with `{project?, expect}` |

MCP returns the core document as `structuredContent`; HTTP returns it as the
workbench envelope's `data`; CLI prints it directly. Canonical serialization
of those core documents is byte-equal on identical repository state. The MCP
apply schema and HTTP body accept only `project` and `expect`: callers cannot
supply or modify the underlying command. An operational apply refusal remains
a normal MCP result carrying `delivery-workbench-step-result@1`; HTTP maps it
to 409 with that exact receipt in `data`. A started child result remains
truthful even when nonzero.

The HTTP route is localhost-only under the existing workbench host/origin
guards. It is distinct from the roadmap editor's content-fingerprint
preview/apply routes: a step token binds the complete status observation and
authorizes only the already-published closed argv.

The token is SHA-256 over the canonical, complete status document plus the
local lease-claim generation (sorted keys, compact separators, UTF-8). It
therefore binds rail health, roadmap selection and validation, Git
branch/HEAD/workspace, contract and gate facts, the exact action—not merely
its id—and prior step attempts. Any changed observed fact requires a new
preview, even if the recommendation remains `start-story`.

Apply atomically claims the token under `.git/pmo-step-claims/` before
starting a child. Claim files contain no command or output. Folding their
generation into the next token matters for read-only actions: after
`continue-story` displays a story, the underlying status can be identical,
but the old lease still cannot replay. Concurrent attempts at one token race
on an exclusive file create; at most one crosses the execution boundary.
The token is an opaque stale-intent lease, not a secret, identity credential,
or permission transferable to another repository.

## Result model v1

Every apply attempt that reaches the step core returns the same exact-key
shape. Expected operational refusals are data, so JSON clients do not need to
parse stderr:

```json
{
  "kind": "delivery-workbench-step-result",
  "schema_version": 1,
  "project": "myapp",
  "outcome": "succeeded",
  "started": true,
  "exit_code": 0,
  "reason": null,
  "action": {
    "id": "start-story",
    "kind": "command",
    "blocking": false,
    "reason": "APP-2-01 is the next actionable story",
    "command": [
      ".githooks/dw", "story", "status", "myapp", "2",
      "APP-2-01", "in-progress"
    ]
  },
  "before": {
    "token": "sha256:...",
    "action_id": "start-story"
  },
  "after": {
    "token": "sha256:...",
    "action_id": "continue-story"
  },
  "output": {
    "stdout": "APP-2-01 in-progress ...\n",
    "stderr": "",
    "truncated": {"stdout": false, "stderr": false}
  }
}
```

`outcome` is exactly `succeeded`, `failed`, `interrupted`, or `refused`:

- `succeeded`: one child started and returned zero;
- `failed`: a child returned nonzero, or process start failed;
- `interrupted`: the child boundary observed an interrupt and returns 130;
- `refused`: no child started because the token was absent, malformed,
  stale/already consumed, or the current action was prohibited.

`exit_code` is the truthful CLI exit (signals normalize to `128 + signal`;
interruption is 130). `started` distinguishes a child failure from a spawn
failure/refusal. `before` always describes the current preview used to make
the decision. `after` is a fresh observation after an attempted child and is
`null` when no child was attempted. Output streams are separate UTF-8 text,
each byte-capped at 20,000 by default; truncation is explicit. The human CLI
renders those same fields back to their original streams and stops after the
one action.

## Closed executable capability

Status remains the decision owner. Step adds a second execution-boundary
check: both the action id and the entire argv shape must match this closed
table.

| Action id | Allowed argv shape |
|---|---|
| `repair-rails` | exactly `.githooks/dw doctor` |
| `resolve-rewrite` | exactly `git status` |
| `review-unstaged`, `review-workspace` | exactly `git status --short` |
| `generate-contract` | `.githooks/dw contract new`, optionally exact `--force` |
| `repair-roadmap` | `.githooks/dw check [safe-project]` or exact phase-create help |
| `finish-story` | exact guarded `story status <safe-project> <phase> <story-id> done` |
| `start-story` | exact guarded `story status <safe-project> <phase> <story-id> in-progress` |
| `continue-story` | exact `story show <safe-project> <phase> <story-id>` |
| `review-holds` | exact `holds <safe-project>` |
| `plan-work` | exactly `.githooks/dw phase create --help` |

Selectors cannot begin with `-` or contain slash, backslash, or NUL;
phases are decimal digits and story ids must match the shared roadmap story
grammar. Unknown future action ids remain non-applicable until code, tests,
and this table deliberately grant their exact shape. There is no caller-
supplied argv, shell-string field, executable path override, or automatic
continuation.

The following are permanently outside this capability:

- `commit`, even when status correctly recommends `git commit`;
- contract certification or checkbox edits;
- project selection and other manual judgment;
- arbitrary repair, evidence, phase-content, or test commands; and
- loops that follow the newly observed action.

The underlying guarded command retains its own domain checks. Step does not
bypass evidence-before-done, mutation containment, contract freshness, gate
rules, or any existing refusal.

## Purity, failure, and proof

Preview performs the same local reads as status and writes no roadmap file,
event, contract, stage, or commit. Repeated previews over unchanged state are
byte-identical. A stale token or prohibited action refuses before the runner.
Once one child starts, its nonzero exit is returned unchanged; step does not
reinterpret a failed command as success and never starts a follow-up.

Each started child appends exactly one `step_execution` rail event in addition
to any domain event emitted by the underlying guarded command. It contains
only action id, outcome, exit code, before/after token hashes, and next action
id. Command argv, stdout/stderr, reasons, file content, and prompts are not in
the event allowlist. Preview, refusal, and process-start failure emit no step
event. Event telemetry remains best-effort; the atomic claim ledger—not the
event log—enforces replay safety.

The executable proof is:

- `StatusBriefingTest` in `pmo-roadmap/tests/dw-core-tests.py`: exact model,
  purity, state token, same-action staleness, closed-table red paths,
  commit/manual exclusion, runner count/root, and exit mirroring;
- `pmo-roadmap/tests/roadmap-cli.sh`: an installed repo previews
  `start-story`, returns JSON success/failure/refusal receipts, refuses an old
  token after only HEAD moves, consumes a read-only lease, and proves exactly
  one content-safe event per started child; and
- `pmo-roadmap/tests/package-smoke.sh`: the wheel must contain and import the
  deliberate-step core; and
- `pmo-roadmap/tests/step-interop.sh`: a freshly installed repo compares the
  CLI, MCP, and HTTP preview/result documents exactly, consumes one real
  `start-story` lease through each adapter, refuses replay and caller-supplied
  argv, and proves certification/commit remain non-applicable everywhere.

No adapter may expand the allowlist or consent boundary implicitly.
