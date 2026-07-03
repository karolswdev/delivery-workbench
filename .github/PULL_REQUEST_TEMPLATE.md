## What this changes

<!-- One paragraph: the problem and the shape of the fix. -->

## Proof

<!-- This repo treats "done" claims as unproven until captured.
     Paste the relevant verification output, or point at the evidence
     file if this PR works a roadmap story. -->

```text
(captured output of the verification that proves this change)
```

## Checklist

- [ ] Commits went through the gate (no `--no-verify`): each carries
      `PMO-Story`/`PMO-Contract-Digest` trailers where applicable and
      the contract was certified honestly.
- [ ] The validation matrix in the root README passes locally
      (`dw-core-tests.py`, the shell suites, `docs-lint.sh`,
      `docs-snippet-smoke.sh`, shellcheck).
- [ ] If this PR works a roadmap story: the story flips `done` in its
      own commit together with its `evidence-story-NN.md`.
- [ ] If this PR edits a `<!-- snippet: … -->`-marked quickstart
      block: `docs-snippet-smoke.sh` still proves it runs as printed.
- [ ] New shell is bash-3.2-safe and shellcheck-0.9-clean
      (`shellcheck -e SC2317`); new python is stdlib-only, 3.9 floor.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full loop.
