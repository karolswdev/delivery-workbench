# Contributing to Delivery Workbench

This repository ships through its own gate. Contributing here means
using the tool you are contributing to: work is planned as Markdown,
proven by captured command runs, and certified at commit time by a
contract the pre-commit hook re-verifies fact by fact. The fastest
way to learn the framework is to send one change through it.

Two rules are absolute:

- Never use `--no-verify`. When the gate blocks you, read the
  banner. It names the failed rule and the remediation, and includes
  the exact contract template you need.
- Certify honestly. `dw contract new` stamps machine-verified facts;
  the checkboxes are your assertions. Read each rule before flipping
  it. The gate catches mechanical lies (stale index trees, missing
  evidence); the honesty is on you.

## Setup

Clone the repo. The hooks and CLI are inside it under `.githooks/`;
one config command activates them:

<!-- snippet: contributor-setup prep=clone cwd=target -->
```bash
git config core.hooksPath .githooks
.githooks/dw doctor
.githooks/dw check work-log-automation
```

`git clone` does not carry hook configuration, so wiring
`core.hooksPath` is the one manual step. `dw doctor` proves the
wiring and `dw check` proves the roadmap is structurally sound. Both
must be green before you change anything. This block runs verbatim
in CI (`pmo-roadmap/tests/docs-snippet-smoke.sh`) so it cannot rot.

You do not need to install anything else. If you want the global
toolchain anyway (for adopting other repos), `pipx install
delivery-workbench` or `brew install karolswdev/tap/delivery-workbench`.
Agent contributors get the same operations as MCP tools through the
repo's `.mcp.json`; see [docs/mcp.md](./docs/mcp.md).

## A first gated commit

Make your change, then send it through the gate:

<!-- snippet: contributor-gated-commit prep=clone cwd=target -->
```bash
echo "- worked example line (delete me)" >> SECURITY.md
git add SECURITY.md
.githooks/dw contract new --consent no --reasons "worked example"
sed -i.bak 's/^- \[ \]/- [x]/' .tmp/CONTRACT.md && rm .tmp/CONTRACT.md.bak
git commit -m "docs: worked example of a gated commit"
git log -1 --format='contract digest: %(trailers:key=PMO-Contract-Digest,valueonly)'
```

Staging comes first, then `dw contract new`: the contract stamps the
staged index tree, so restaging afterwards invalidates it
(regenerate with `--force`). A commit that touches no roadmap files
gets the short tier, a single no-bypasses rule, which the `sed` line
flips. Do that only because you read the rule and it is true. For
full-tier commits (roadmap work), open `.tmp/CONTRACT.md` and
certify each rule by hand instead of scripting the flip. The passing
commit carries a `PMO-Contract-Digest` trailer, and the certified
contract is archived under `.git/pmo-contract-archive/<sha>`. This
block also runs verbatim in CI.

## Working a roadmap story

Feature-sized work is a story. The loop:

1. `.githooks/dw next work-log-automation` shows the next actionable
   story (exit 0 found, 2 nothing actionable, 1 error).
2. `.githooks/dw story status <project> <phase> <story> in-progress`
3. Do the work.
4. `.githooks/dw evidence capture <project> <phase> <story> -- <command>`
   records the real verification run (command, exit code, output)
   into the story's evidence file. Assets go under `assets/` next to
   it.
5. `.githooks/dw story status <project> <phase> <story> done`
   refuses without evidence.
6. Stage, `dw contract new`, certify, commit. One story flips done
   per commit, with its evidence in the same commit. The gate
   enforces both.

If you are changing framework behavior, the canon is
[`pmo-roadmap/templates/PMO-CONTRACT.md`](./pmo-roadmap/templates/PMO-CONTRACT.md)
(the rules, each with a stable id) and
[`pmo-roadmap/templates/roadmap-builder.md`](./pmo-roadmap/templates/roadmap-builder.md)
(the methodology). Rule logic lives once, in
[`pmo-roadmap/lib/dw_pmo/`](./pmo-roadmap/lib/dw_pmo/); the hooks
are shims, and `tests/gate-parity.sh` asserts the CLI and a real
`git commit` reach identical verdicts.

## The pull request

Branch from `main`, keep the PR to one story (the PR is the review
unit; the gate's one-flip-per-commit rule extends to it), and push.
Two things happen on the GitHub side:

- CI runs the full test matrix plus `dw verify` over your range.
  The verify check re-derives the gate's structural rules from your
  commits alone: story flips paired with evidence, trailers present
  and well formed, one flip per commit. It is a required check.
- The merge button is rebase only. Squash merges concatenate commit
  messages, which moves the PMO trailers out of the position where
  git parses them and can collapse several story flips into one
  commit. Both corruptions are demonstrated by
  `pmo-roadmap/tests/contributor-flow.sh`, so the buttons that cause
  them are disabled. Details in
  [docs/contribution-rails.md](./docs/contribution-rails.md).

What the green verify check proves and what it does not: it proves
your range's structural integrity. It does not prove your tests
passed (reviewers read the captured runs in your evidence files) and
it cannot prove you certified honestly. That part is review.

The [PR template](./.github/PULL_REQUEST_TEMPLATE.md) asks for the
story ID, the evidence file, and captured proof rather than
promises.

## House constraints

- Shell must pass shellcheck 0.9 with `-e SC2317` and run on
  bash 3.2 (the macOS default). No `A && B || C`.
- Python is stdlib only with a 3.9 floor. CI runs the suite on 3.9.
- Docs are code: internal links, anchors, and images are CI-linted;
  every image needs alt text; every rendered asset names the
  checked-in script that regenerates it; quickstart blocks marked
  `<!-- snippet: … -->` execute as printed in CI.
- Tests accompany behavior: parity-locked surfaces (managed block,
  plugin skill, command files, version) have tests that name exactly
  what disagrees.

## Bugs, conduct, security

Bugs and ideas go through the issue templates; the bug form asks for
the reproduction as verbatim commands and the failing banner,
because that is the shape a fix starts from. Participation is
covered by the [Code of Conduct](./CODE_OF_CONDUCT.md). Security
issues go through [SECURITY.md](./SECURITY.md) privately, never a
public issue.
