## What this changes

<!-- One paragraph: the problem and the shape of the fix. -->

## Story and evidence

<!-- For roadmap work: the story ID (e.g. WLA-11-02) and a link to
     its evidence-story-NN.md. For work outside the roadmap tree,
     write "not roadmap work". One story per PR; see
     docs/contribution-rails.md. -->

Story:
Evidence:

## Proof

<!-- This repo treats "done" claims as unproven until captured.
     Paste the relevant verification output, or point at the captured
     run inside the evidence file. -->

```text
(captured output of the verification that proves this change)
```

## Checklist

- [ ] Commits went through the gate (no `--no-verify`): each carries
      `PMO-Story`/`PMO-Contract-Digest` trailers where applicable and
      the contract was certified honestly.
- [ ] `dw verify main..HEAD` is green on this branch (CI re-runs it
      as a required check).
- [ ] The test suites in `pmo-roadmap/tests/` pass locally.
- [ ] If this PR works a roadmap story: exactly one story flips
      `done`, in its own commit, together with its
      `evidence-story-NN.md`.
- [ ] If this PR edits a `<!-- snippet: … -->`-marked quickstart
      block: `docs-snippet-smoke.sh` still proves it runs as printed.
- [ ] New shell is bash-3.2-safe and shellcheck-0.9-clean
      (`shellcheck -e SC2317`); new python is stdlib-only, 3.9 floor.

Merging is rebase-only: squash would move the PMO trailers out of
trailer position and can collapse story flips (see
[docs/contribution-rails.md](../docs/contribution-rails.md)).

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full loop.
