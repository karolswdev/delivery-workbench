# Evidence - WLA-9-03

- **Story:** WLA-9-03 - Prove the consumer upgrade path
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverables:

- `tests/upgrade-path.sh` — the end-to-end proof against the REAL
  v1.5.0 tag (`git archive`): adopt a fixture with genuine v1.5.0
  rails, ship two gated commits there, assert the old rails lack
  `dw verify` and that `update.sh --check` reports STALE (exit 3);
  upgrade via current `update.sh`; assert `verify.py` delivered,
  `--check` now exit 0, roadmap content / `pre-commit.config` /
  `pre-commit.local` byte-untouched, `dw verify --all` clean over
  the mixed-version history, and a story ships through the gate on
  the refreshed rails. Wired into the `verify-history` CI job (it
  needs the full clone for the tag).
- `update.sh --check` — the staleness command. Design correction
  discovered by the fixture: version-string comparison reported
  "fresh" for v1.5.0 rails against v1.5.0 source while `verify.py`
  was missing, because versions only move at releases. `--check` is
  therefore content-based (diffs vendored `dw_pmo`, `dw`, and
  `pre-commit` against the source) with versions printed as
  context; documented in `docs/distribution.md`.

Manual leg: the WLA-8-04 fridgr clone — adopted mid-release-cycle,
so its rails predated the launcher module at identical version
strings — reported STALE (exit 3), upgraded, now reports fresh, and
`dw verify --all` still passes there (captured below after the
refresh; the STALE-before output is in the session transcript and
reproduced by the fixture suite's identical scenario).

### Captured run — 2026-07-03T16:50:25Z

- **Command:** `bash -c set -e; bash pmo-roadmap/tests/upgrade-path.sh 2>&1 | tail -1; echo; echo "== manual leg: fridgr clone (adopted mid-release-cycle at WLA-8-04) =="; F=/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/bdd9035c-86e9-4b64-9ed5-97736ac5a68c/scratchpad/fridgr-adopt; pmo-roadmap/update.sh "$F" --check; (cd "$F" && .githooks/dw verify --all); echo; bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7818db3c86b6480a744f013aba4530b02531e288

```text
upgrade-path.sh: ok

== manual leg: fridgr clone (adopted mid-release-cycle at WLA-8-04) ==
update.sh: up to date (vendored rails match source v1.5.0)
dw verify: ok (1 commits verified, 133 pre-epoch skipped)

docs-lint.sh: ok (0s)
```
