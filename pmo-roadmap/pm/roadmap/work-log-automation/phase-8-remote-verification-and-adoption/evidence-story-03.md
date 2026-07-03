# Evidence - WLA-8-03

- **Story:** WLA-8-03 - Wire remote verification into CI
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverables:

- `verify-history` job in `.github/workflows/validation.yml`: full
  checkout (`fetch-depth: 0` — the verifier exits 2 on shallow
  clones, so a truncated checkout can never pass silently) running
  `python3 pmo-roadmap/bin/dw verify --all` on every push to main
  and every pull request.
- Copyable adopter snippet and full-sweep rationale in
  `docs/remote-verification.md` §"CI enforcement" (docs-lint clean).
- README "What you get" now lists history verification.

The captured run below executes the job's exact command on both
paths: green on main (28 commits verified), red on a scratch branch
carrying a smuggled `--no-verify` story flip — blocked with three
named rules (`trailer-missing` ×2, `evidence-missing`), exit 1.
This is a faithful local execution of the one-command CI job; the
genuine Actions leg runs on the next push of main, and branch
protection (repo settings, out of scope per the design contract)
can make it required.

### Captured run — 2026-07-03T16:07:53Z

- **Command:** `bash -c set -e; SCRATCH=/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/bdd9035c-86e9-4b64-9ed5-97736ac5a68c/scratchpad/smuggle-worktree; echo "== green: CI command on main =="; python3 pmo-roadmap/bin/dw verify --all; echo; echo "== red: same command on scratch/red-path (smuggled --no-verify story flip) =="; if (cd "$SCRATCH" && python3 pmo-roadmap/bin/dw verify --all); then echo "UNEXPECTED PASS"; exit 1; else echo "exit=$? (blocked as designed)"; fi; echo; echo "== workflow wires the job =="; grep -n "verify-history" -A4 .github/workflows/validation.yml | head -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 407977fd99cbbcbf3d8fa4271c2238331cc8a23d

```text
== green: CI command on main ==
dw verify: ok (28 commits verified, 17 pre-epoch skipped)

== red: same command on scratch/red-path (smuggled --no-verify story flip) ==
ERROR c2f1fde: trailer-missing: in-scope commit carries no PMO-Contract-Digest trailer
ERROR c2f1fde: trailer-missing: story flip carries no PMO-Story trailer
ERROR c2f1fde: evidence-missing: story pmo-roadmap/pm/roadmap/work-log-automation/phase-8-remote-verification-and-adoption/story-04-adopt-delivery-workbench-in-an-external-repository.md flipped to done but evidence-story-04.md is not in this commit
dw verify: 3 violation(s) across 29 verified commit(s)
exit=1 (blocked as designed)

== workflow wires the job ==
16:  verify-history:
17-    runs-on: ubuntu-latest
18-    steps:
19-      - uses: actions/checkout@v5
20-        with:
```
