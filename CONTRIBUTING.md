# Contributing to Delivery Workbench

This repository ships through its own gate. Contributing here means
using the rails you are contributing to: work is planned as Markdown,
proven by captured command runs, and certified at commit time by a
contract the pre-commit hook re-verifies fact by fact. The fastest way
to learn the framework is to send one change through it.

Two rules are absolute:

- **Never `--no-verify`.** When the gate blocks you, read the banner —
  it names the failed rule id and the remediation, and includes the
  exact contract template you need.
- **Certify honestly.** `dw contract new` stamps machine-verified
  facts; the checkboxes are *your* assertions. Read each rule before
  flipping it. The gate catches mechanical lies (stale index trees,
  missing evidence); the honesty is on you.

## From clone to a healthy workbench

<!-- snippet: contributor-setup prep=clone cwd=target -->
```bash
git config core.hooksPath .githooks
.githooks/dw doctor
.githooks/dw check work-log-automation
```

`git clone` does not carry hook configuration, so wiring
`core.hooksPath` is the one manual step. `dw doctor` proves the
wiring (hooks, CLI, managed agent-docs block); `dw check` proves the
dogfood roadmap — the framework's own delivery history under
[`pmo-roadmap/pm/roadmap/work-log-automation/`](./pmo-roadmap/pm/roadmap/work-log-automation/)
— is structurally sound. Both must be green before you change
anything, and the block above runs verbatim in CI
(`pmo-roadmap/tests/docs-snippet-smoke.sh`) so it cannot rot.

## Validate before and after

The full matrix is the Validation block in the
[root README](./README.md#validation) — unit suite, eight shell
suites, plugin validation, docs lint, snippet smoke, shellcheck, and
`dw check`. CI runs all of it on ubuntu and macos plus a python 3.9
floor job, but run it locally first; it takes about two minutes and
failures name their file and rule.

## How a change ships

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

What happened there: staging first, *then* `dw contract new` — the
contract stamps the staged index tree, so restaging afterwards
invalidates it (regenerate with `--force`). A commit that touches no
roadmap files gets the **short tier**: a single no-bypasses rule,
which the `sed` line flips — do that only because you have read the
rule and it is true; for **full-tier** commits (roadmap work), open
`.tmp/CONTRACT.md` and certify each rule by hand instead of scripting
the flip. The passing commit carries a `PMO-Contract-Digest` trailer
and the certified contract is archived under
`.git/pmo-contract-archive/<sha>`. This block also runs verbatim in
CI — the gate accepting it is part of the test suite.

## Working a roadmap story

Feature-sized work is a story. The loop (taught to agents by the
managed block in [`CLAUDE.md`](./CLAUDE.md), and identically by the
Claude Code plugin skill):

1. `.githooks/dw next work-log-automation` — the next actionable
   story (exit 0 found, 2 nothing actionable, 1 error).
2. `.githooks/dw story status <project> <phase> <story> in-progress`
3. Do the work.
4. `.githooks/dw evidence capture <project> <phase> <story> -- <command>`
   — records the real verification run (command, exit code, output)
   into the story's evidence file. Assets go under `assets/` next to
   it.
5. `.githooks/dw story status <project> <phase> <story> done` —
   refuses without evidence.
6. Stage, `dw contract new`, certify, commit. One story flips done
   per commit, and its evidence ships in the same commit — the gate
   enforces both.

Canon, if you are changing framework behavior:
[`pmo-roadmap/templates/PMO-CONTRACT.md`](./pmo-roadmap/templates/PMO-CONTRACT.md)
(the rules, each with a stable id) and
[`pmo-roadmap/templates/roadmap-builder.md`](./pmo-roadmap/templates/roadmap-builder.md)
(the methodology). Rule logic lives once in
[`pmo-roadmap/lib/dw_pmo/`](./pmo-roadmap/lib/dw_pmo/) — the hooks
are shims, and `tests/gate-parity.sh` asserts the CLI and a real
`git commit` reach identical verdicts.

## House constraints

- **Shell** must pass shellcheck 0.9 with `-e SC2317` and run on
  bash 3.2 (macOS default): no `A && B || C`, and parameter-expansion
  replacements stay unquoted with the `patsub_replacement` guard the
  bootstraps carry.
- **Python** is stdlib-only with a 3.9 floor (CI runs the suite on
  3.9).
- **Docs are code**: internal links, anchors, and images are
  CI-linted; every image needs alt text; every rendered asset names
  the checked-in script that regenerates it; quickstart blocks marked
  `<!-- snippet: … -->` execute as printed in CI — if you edit one,
  the smoke is your proof.
- **Tests accompany behavior**: parity-locked surfaces (managed
  block, plugin skill, command files, version) have tests that name
  exactly what disagrees.

## Sending the PR

The [PR template](./.github/PULL_REQUEST_TEMPLATE.md) asks for the
proof, not promises: captured verification output, gate-passed
commits, and the story/evidence pair when roadmap work is involved.
CI must be green on both OS legs.

Bugs and ideas: use the issue templates — the bug form asks for the
reproduction as verbatim commands and the failing banner, because
that is the shape a fix starts from.

## Conduct and security

Participation is covered by the
[Code of Conduct](./CODE_OF_CONDUCT.md). Security issues go through
[SECURITY.md](./SECURITY.md) privately, never a public issue.
