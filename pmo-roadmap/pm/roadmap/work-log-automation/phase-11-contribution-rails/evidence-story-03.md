# Evidence - WLA-11-03

- **Story:** WLA-11-03 - Enforce merge policy and rewrite the contributor docs
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverables:

- Repository enforcement: squash and merge-commit methods disabled
  via the API, rebase left as the only merge method. The before
  state (all three enabled) is captured in evidence-story-01's run;
  the after state is in the run below.
- CONTRIBUTING.md rewritten in the plain register: setup (one
  config command activates the traveling rails), a first gated
  commit, the story loop, and a new pull-request section covering
  the one-story-per-PR convention, what the required verify check
  proves and does not prove, and why the merge button is rebase
  only. The two CI-executed snippet blocks survived byte-identical
  (snippet smoke green below). Zero em dashes in the rewritten
  files.
- PR template: asks for the story ID and evidence link, adds the
  `dw verify main..HEAD` checklist line, and states the rebase-only
  policy with its reason in one line.
- `docs/contribution-rails.md` linked from the README's docs list.


### Captured run — 2026-07-03T23:27:57Z

- **Command:** `bash -c set -e -o pipefail; echo "== merge methods now (was: squash true, merge_commit true at phase open — see evidence-story-01) =="; gh api repos/karolswdev/delivery-workbench --jq "{squash: .allow_squash_merge, merge_commit: .allow_merge_commit, rebase: .allow_rebase_merge}"; echo; echo "== contributor docs clean of em dashes =="; ! grep -c "—" CONTRIBUTING.md .github/PULL_REQUEST_TEMPLATE.md | grep -v ":0"; echo "both files: 0"; echo; echo "== template asks for story and evidence =="; grep -c "^Story:\|^Evidence:" .github/PULL_REQUEST_TEMPLATE.md; echo; echo "== doc suites =="; bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1; bash pmo-roadmap/tests/docs-snippet-smoke.sh 2>&1 | tail -1; bash pmo-roadmap/tests/agent-surface.sh 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9850b93e48f9e8023a5fae9504e18bff8b43b5de

```text
== merge methods now (was: squash true, merge_commit true at phase open — see evidence-story-01) ==
{"merge_commit":false,"rebase":true,"squash":false}

== contributor docs clean of em dashes ==
both files: 0

== template asks for story and evidence ==
2

== doc suites ==
docs-lint.sh: ok (0s)
docs-snippet-smoke.sh: ok
agent-surface.sh: ok
```
