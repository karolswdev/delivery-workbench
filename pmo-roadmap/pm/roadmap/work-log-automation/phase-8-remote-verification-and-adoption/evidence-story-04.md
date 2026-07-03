# Evidence - WLA-8-04

- **Story:** WLA-8-04 - Adopt Delivery Workbench in an external repository
- **Status:** done
- **Date:** 2026-07-03

## Proof

Adoption target: a scratch clone of `~/dev/code/fridgr` (Pantrybot —
a real, post-launch Next.js + Express product with 133 commits, its
own `CLAUDE.md`, and pre-existing planning conventions), chosen over
the Phase 7 clone fixture because it exercises exactly what
self-hosting hides: foreign layout, existing agent docs, and history
that predates the rails. The original repository was never touched.

The documented three-command path ran verbatim:

1. `pmo-roadmap/install.sh <clone> --skip-bootstrap` — clean.
2. `pmo-roadmap/bootstrap/adopt-project.sh <clone> --project-slug
   fridgr --project-prefix FR --with-intake --agent claude` — worked
   end-to-end headlessly: placeholder intake, ~10-minute nested
   `claude -p` discovery producing a 166-line report proposing 3
   phases / 6 stories grounded in the repo's actual state (stale
   `EXP-SCANNING.md` header, build-error suppression debt, SCAN-005
   as the one open feature).
3. `.githooks/dw adopt --from-report … --apply` — preview matched
   the report; apply scaffolded `pm/roadmap/fridgr/`.

Then one real story end-to-end there: FR-1-01 (land the adoption
scaffold) — in-progress → `dw evidence capture` of doctor+check →
done → full contract → gated commit `764549e` with trailers and
contract archive, as the captured run below re-verifies. `dw verify
--all` passes over the external history with all 133 pre-adoption
commits skipped as pre-epoch — the epoch design working unmodified
on a foreign repository.

Friction: five severity-tagged entries in
[adoption-friction.md](./adoption-friction.md) (silent discovery,
headless-behavior docs gap, stdout-captured report preamble,
sandbox denying `dw` orientation to the discovery agent, installer
scaffolding a stray root `pm/` on self-hosting refresh). Triage is
WLA-8-05.

### Captured run — 2026-07-03T16:18:06Z

- **Command:** `bash -c set -e; F=/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/bdd9035c-86e9-4b64-9ed5-97736ac5a68c/scratchpad/fridgr-adopt; echo "== external repo: fridgr clone (133 pre-adoption commits) =="; cd "$F"; .githooks/dw doctor | tail -2; .githooks/dw check fridgr; echo; echo "== gated story shipped there =="; git log -1 --format="%h %s%n%(trailers)"; ls .git/pmo-contract-archive/; echo; echo "== dw verify over the external history =="; .githooks/dw verify --all`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bafcadcf4efc031fab2c16d7f11f96be5c1cff6a

```text
== external repo: fridgr clone (133 pre-adoption commits) ==

dw doctor: healthy. Canonical invocation: .githooks/dw <command>
dw check: ok

== gated story shipped there ==
764549e Complete FR-1-01: land Delivery Workbench adoption scaffold
PMO-Story: FR-1-01
PMO-Contract-Digest: sha256:5b948b3f2e12409d499ebeccbcd7b90d7aebf8b303e4bb30799942f6e37e3686

764549e4823efc5590e19def62d021c3a1d137b4

== dw verify over the external history ==
dw verify: ok (1 commits verified, 133 pre-epoch skipped)
```
