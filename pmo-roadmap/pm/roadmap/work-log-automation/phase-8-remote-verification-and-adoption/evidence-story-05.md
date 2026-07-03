# Evidence - WLA-8-05

- **Story:** WLA-8-05 - Fold adoption friction back into the framework
- **Status:** done
- **Date:** 2026-07-03

## Proof

All five friction entries from [adoption-friction.md](./adoption-friction.md)
are triaged — verdicts and rationale live in that file's triage
table; counts match (5/5, nothing silently dropped). The fix-now
slice landed as:

- **Entry 1 (partial):** `adopt-project.sh` announces the discovery
  agent launch with expected duration and report location before the
  exec; `--timeout`/heartbeat deferred (phase status records it).
- **Entry 2:** README quickstart gained the "What to expect from
  step 2" paragraph (headless behavior, duration, auth).
- **Entry 3:** discovery prompt template now carries "How to deliver
  the report" (stdout IS the report; no preamble); wrapper-side
  stripping declined with rationale.
- **Entry 5:** `install.sh` skips the root canon scaffold on
  self-hosting refresh (physical-path containment check, `pwd -P`
  to match `git rev-parse`), with a two-direction regression case in
  `tests/adoption-discovery.sh`.
- **Entry 4:** deferred (per-CLI sandbox plumbing), mirrored in the
  phase status deferred decisions.

The captured run re-executes each original failing step against the
fixed framework and finishes with the relevant suites green
(adoption-discovery, docs-lint, full unit suite).

### Captured run — 2026-07-03T16:23:11Z

- **Command:** `bash -c set -e; echo "== entry 5 red-step re-run: self-hosted install no longer scaffolds pm/ =="; pmo-roadmap/install.sh . --skip-bootstrap 2>&1 | grep "self-hosting refresh"; test ! -e pm && echo "no stray pm/ tree"; echo; echo "== entry 3 re-run: rendered prompt carries delivery instruction =="; T=$(mktemp -d); git init -q "$T"; git -C "$T" config user.email t@t; git -C "$T" config user.name t; pmo-roadmap/bootstrap/adopt-project.sh "$T" --project-slug demo --project-prefix DM >/dev/null 2>&1; grep -c "stdout) IS the report" "$T/pm/roadmap/demo/adoption/adoption-discovery-prompt.md"; rm -rf "$T"; echo; echo "== entry 1: launch messaging precedes agent exec =="; grep -n "typically takes 5-15 minutes" pmo-roadmap/bootstrap/adopt-project.sh; echo; echo "== entry 2: README expectation note =="; grep -c "What to expect from step 2" README.md; echo; echo "== suites ==" ; bash pmo-roadmap/tests/adoption-discovery.sh 2>&1 | tail -1; bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1; python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5ff6471e6c78cbfcb80e5747b8f3a1a8f8a15ccb

```text
== entry 5 red-step re-run: self-hosted install no longer scaffolds pm/ ==
  · self-hosting refresh (source inside target); skipping pm/roadmap canon scaffold
no stray pm/ tree

== entry 3 re-run: rendered prompt carries delivery instruction ==
1

== entry 1: launch messaging precedes agent exec ==
173:echo "  This typically takes 5-15 minutes on a mid-size repository."

== entry 2: README expectation note ==
1

== suites ==
adoption-discovery.sh: ok
docs-lint.sh: ok (0s)
OK
```
