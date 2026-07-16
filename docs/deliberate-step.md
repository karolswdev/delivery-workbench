# Deliberate step contract

**Status:** v1 core and CLI contract implemented; receipts and transport
adapters are planned in Phase 23.
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

`--expect` without `--apply` and `--apply` without `--expect` are errors.
JSON apply results arrive with the receipt contract in WLA-23-02; in v1 of
this first slice, `--json --apply` is refused rather than emitting an
unstamped ad-hoc shape.

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

The token is SHA-256 over the canonical, complete status document (sorted
keys, compact separators, UTF-8). It therefore binds rail health, roadmap
selection and validation, Git branch/HEAD/workspace, contract and gate
facts, and the exact action—not merely its id. Any changed observed fact
requires a new preview, even if the recommendation remains `start-story`.
The token is an opaque stale-intent lease, not a secret, identity credential,
or permission transferable to another repository.

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

The executable proof is:

- `StatusBriefingTest` in `pmo-roadmap/tests/dw-core-tests.py`: exact model,
  purity, state token, same-action staleness, closed-table red paths,
  commit/manual exclusion, runner count/root, and exit mirroring;
- `pmo-roadmap/tests/roadmap-cli.sh`: an installed repo previews
  `start-story`, refuses an old token after only HEAD moves, then applies a
  fresh token and stops at `continue-story`; and
- `pmo-roadmap/tests/package-smoke.sh`: the wheel must contain and import the
  deliberate-step core.

WLA-23-02 will add a bounded, versioned result receipt and one correlated
event for a started child. WLA-23-03 then carries those same core documents
through MCP and HTTP; neither future story expands the allowlist or consent
boundary implicitly.
