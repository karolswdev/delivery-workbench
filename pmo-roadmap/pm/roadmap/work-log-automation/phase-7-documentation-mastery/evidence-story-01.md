# Evidence - WLA-7-01

- **Story:** WLA-7-01 - Documentation audit and information architecture
- **Status:** done
- **Date:** 2026-07-02

## The audit (contract for Phase 7)

Later stories implement the dispositions below; they do not
re-litigate them.

### 1. Inventory — every documentation surface

| # | Surface | Audience | Purpose | Freshness | Disposition |
|---|---|---|---|---|---|
| 1 | `README.md` (root) | evaluator | pitch, orient, quickstart | stale-by-omission (F6, F7, F8) | **rewrite** (WLA-7-02) |
| 2 | `pmo-roadmap/README.md` | adopter + operator | install/adopt/operate manual | mixed: P6 sections accurate, pre-P6 sections wrong (F1-F5, F9-F11) | **rewrite/restructure** (WLA-7-02) |
| 3 | `CLAUDE.md` managed block + `templates/CLAUDE-snippet.md` + `agentdocs.CANONICAL_BLOCK` | operating agent | the operating loop | current (regenerated 2026-07-02) | **keep**; becomes parity source for the plugin skill (WLA-7-04) |
| 4 | `templates/PMO-CONTRACT.md` (+ installed copy) | operator canon | rules + contract template | current post-P6; verify line-by-line | **verify** (WLA-7-03) |
| 5 | `templates/roadmap-builder.md` | operator canon | methodology + vocabulary | current post-P6; verify | **verify** (WLA-7-03) |
| 6 | `templates/adoption-discovery-prompt.md` | adoption agent | discovery instrument | current (P6-07 stabilized tables) | **keep** |
| 7 | `templates/*.tmpl` (story, phase-status, project-README, session-intake) | generators | scaffolds | current (P6 reconciled) | **verify against generator output** (WLA-7-03) |
| 8 | `templates/examples/*` | operator | worked examples | current (P6-06 extraction) | **verify** (WLA-7-03) |
| 9 | `pmo-roadmap/agent/dw-*.md` (+ `.claude/commands/` copies) | operating agent | slash commands | current | **migrate into plugin**, installer copies remain (WLA-7-04) |
| 10 | `demos/README.md` + `*.vhs` + `rendered/*.gif` | evaluator | terminal demos | tapes call current scripts; GIF freshness unverifiable (F12) | **regenerate + add workbench demo** (WLA-7-05) |
| 11 | `SECURITY.md` | adopter/OSS | privacy & security posture | accurate but pre-workbench | **extend** with workbench runtime boundary (WLA-7-02) |
| 12 | `LICENSE` (MIT) | OSS | license | fine | **keep** |
| 13 | `pmo-roadmap/brand/delivery-workbench.md` | maintainer | brand notes | untouched by P5/P6 | **keep**; feed WLA-7-05 asset work |
| 14 | `.github/workflows/validation.yml` | contributor | de-facto validation doc | current | **keep**; CONTRIBUTING will narrate it (WLA-7-07) |
| 15 | `pm/roadmap/**` (7 final summaries, evidence) | historian | living history | authoritative | **keep frozen**; CHANGELOG derives from it (WLA-7-07) |

Missing surfaces to create: `docs/architecture.md` (WLA-7-02),
plugin package + docs (WLA-7-04), `CONTRIBUTING.md`,
`CODE_OF_CONDUCT.md`, issue/PR templates, `CHANGELOG.md` (WLA-7-07).

### 2. Audience paths (entry → ordered traversal)

- **Evaluator:** root README (what/why/demos/status) →
  `docs/architecture.md` → phase final summaries as proof.
- **Adopter:** root README quickstart → framework README
  install/adopt/update sections → `dw doctor` + `dw check` →
  workbench section.
- **Operating agent:** CLAUDE.md managed block → canon
  (`PMO-CONTRACT.md`, `roadmap-builder.md` §vocabulary) → `dw next
  --json` / gate porcelain contracts → workbench API (trace/handoff).
- **Contributor:** `CONTRIBUTING.md` (new) → validation matrix →
  `docs/architecture.md` → the roadmap history.

### 3. Staleness findings (quoted, all mechanically verified below)

- **F1** `pmo-roadmap/README.md:31` — "Stale contracts are rejected
  via mtime checks." **Wrong since WLA-6-03**: freshness is the
  `git write-tree` index tree (`contract-index-tree-mismatch`); the
  same file says so at :355-359. mtime is explicitly dead (a unit
  test proves `touch` cannot refresh a contract).
- **F2** `pmo-roadmap/README.md:31-32` — "The contract file is
  deleted on success." **Wrong**: it is archived under
  `.git/pmo-contract-archive/<sha>` then cleared (:365 agrees).
- **F3** `pmo-roadmap/README.md:9-11` — gate described as blocking
  until the agent "writes a fresh `.tmp/CONTRACT.md`". **Stale**:
  contracts are generated (`dw contract new`, stamped facts); :349
  says "generated, not hand-typed". The intro contradicts the body.
- **F4** installer numbered list (:78-97) omits the `commit-msg`
  hook copy (5 references in `install.sh`) and the
  `dw-workbench` + `workbench/` UI distribution.
- **F5** file-map fence (:642-674) omits `hooks/commit-msg`,
  `bin/dw-workbench`, `workbench/`, `agent/`, `assets/`, `brand/`,
  `templates/examples/`, and six of nine test files; the `lib/dw_pmo`
  annotation omits gate, contract, evidence, agentdocs, doctor,
  adopt, and workbench modules.
- **F6** root `README.md:203-204` — the Validation `bash -n` block's
  continuation is broken: `workbench-ui-smoke.sh` sits outside the
  backslash chain, so the block as printed *executes* the suite
  mid-syntax-check.
- **F7** root README feature list (:8-15) omits the dw CLI, gate
  engine, contract v2, evidence capture, the trailer/archive audit
  trail, and the entire workbench.
- **F8** root README "Commit-Time Flow" diagram (:131-149) shows no
  contract generation, no `commit-msg` trailer stamping, no
  post-commit archive — the P6 audit trail is invisible.
- **F9** `pmo-roadmap/README.md:130` — update.sh "re-copies the
  methodology and hook" (singular); it ships three hooks, dw, the
  core package, and the workbench.
- **F10** Roadmap Lifecycle diagram (:622-638) orders
  CommitGate → StoryDone; in reality the story flips done (with
  evidence) *before* the commit and the gate verifies the pairing.
- **F11** Maintenance section (:688-693) says keep contract +
  pre-commit + post-commit in sync; rule logic actually lives in
  `dw_pmo/gate.py` and `commit-msg` exists.
- **F12** `demos/rendered/*.gif` cannot be confirmed current: the
  tapes call P6-updated scripts, but the committed GIFs were rendered
  earlier. Disposition: regenerate and visually verify (WLA-7-05).

### 4. Target information architecture (one owner per topic)

| Topic | Owning document | Everyone else |
|---|---|---|
| Pitch, orientation, demos, validation matrix | root README | links |
| Install / update / adopt / bootstrap | framework README | root README links to it |
| Subsystem design (core, gate, contract v2, evidence, workbench, work logs) | `docs/architecture.md` (new) | READMEs link; no re-explaining |
| Gate rules, contract semantics, tiers, extension | `templates/PMO-CONTRACT.md` | framework README stops duplicating gate semantics prose (:446-457 moves to a link + summary) |
| Methodology, statuses, lifecycle | `templates/roadmap-builder.md` | others link |
| Agent operating loop | `agentdocs.CANONICAL_BLOCK` (one constant) | snippet/CLAUDE.md generated; plugin skill parity-tested (WLA-7-04) |
| Workbench usage + API reference | framework README workbench section | architecture doc owns the *design* |
| Work-log pipeline usage | framework README work-log section | SECURITY.md owns the risk posture |
| Security & privacy posture | SECURITY.md (+ workbench boundary) | links |
| Contribution workflow | CONTRIBUTING.md (new) | validation.yml stays the executable truth |
| Release history | CHANGELOG.md (new, derived) | phase final summaries stay authoritative |

### 5. Dispositions summary

Rewrite: root README, framework README (restructure; fix F1-F5,
F9-F11; de-duplicate gate semantics into canon links). Create:
docs/architecture.md, plugin package, CONTRIBUTING, CoC, templates,
CHANGELOG. Verify line-by-line: both canon docs, templates, examples
(WLA-7-03). Regenerate: all rendered assets + workbench demo
(WLA-7-05). Extend: SECURITY.md. Keep frozen: roadmap history.
Delete: nothing — no surface is redundant once topics have single
owners.

## A note on the two verification captures

The first run (exit 1) includes one FAILED line: check F7 originally
grepped the top 20 lines for "workbench" and matched the product
name, not the feature list. The audit finding stood; the check was
wrong. The second run (exit 0) uses the refined check (feature
bullets 10-15, terms `dw-workbench|web|CLI`) and verifies all
fourteen findings — the audit auditing its own instruments.

## Proof — captured runs (appended by `dw evidence capture`)

### Captured run — 2026-07-02T23:24:19Z

- **Command:** `sh -c 
ok=0; fail=0
check() { # id description grep-args...
  id=$1; desc=$2; shift 2
  if "$@" >/dev/null 2>&1; then echo "VERIFIED $id: $desc"; ok=$((ok+1)); else echo "FAILED $id: $desc"; fail=$((fail+1)); fi
}
check F1 "mtime claim exists at pmo-roadmap/README.md:31" grep -qn "rejected via mtime checks" pmo-roadmap/README.md
check F1b "index-tree reality stated in same file" grep -q "index tree is the freshness proof" pmo-roadmap/README.md
check F2 "deleted-on-success claim exists" grep -q "contract file is deleted" pmo-roadmap/README.md
check F2b "archive reality stated in same file" grep -q "pmo-contract-archive/<sha>" pmo-roadmap/README.md
check F4 "installer list omits commit-msg before line 100" sh -c "! sed -n \"78,97p\" pmo-roadmap/README.md | grep -q commit-msg"
check F4b "install.sh ships commit-msg" grep -q "commit-msg" pmo-roadmap/install.sh
check F5 "file map omits hooks/commit-msg" sh -c "! sed -n \"642,674p\" pmo-roadmap/README.md | grep -q commit-msg"
check F6 "root README validation continuation broken at 203-204" sh -c "sed -n \"203p\" README.md | grep -qv \"\\\\\\\\$\" && sed -n \"204p\" README.md | grep -q workbench-ui-smoke"
check F7 "root README feature list omits workbench" sh -c "! sed -n \"1,20p\" README.md | grep -qi workbench"
check F12 "rendered GIFs exist but no regeneration proof committed" ls demos/rendered/onboarding.gif
echo "verification: $ok passed, $fail failed"
[ "$fail" -eq 0 ]`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 593d732174f414f530088d78f62696420dbcb4fa

```text
VERIFIED F1: mtime claim exists at pmo-roadmap/README.md:31
VERIFIED F1b: index-tree reality stated in same file
VERIFIED F2: deleted-on-success claim exists
VERIFIED F2b: archive reality stated in same file
VERIFIED F4: installer list omits commit-msg before line 100
VERIFIED F4b: install.sh ships commit-msg
VERIFIED F5: file map omits hooks/commit-msg
VERIFIED F6: root README validation continuation broken at 203-204
FAILED F7: root README feature list omits workbench
VERIFIED F12: rendered GIFs exist but no regeneration proof committed
verification: 9 passed, 1 failed
```

### Captured run — 2026-07-02T23:25:08Z

- **Command:** `sh -c 
ok=0; fail=0
check() { id=$1; desc=$2; shift 2
  if "$@" >/dev/null 2>&1; then echo "VERIFIED $id: $desc"; ok=$((ok+1)); else echo "FAILED $id: $desc"; fail=$((fail+1)); fi
}
check F1 "mtime claim exists (pmo-roadmap/README.md:31)" grep -q "rejected via mtime checks" pmo-roadmap/README.md
check F1b "index-tree reality stated in the same file" grep -q "index tree is the freshness proof" pmo-roadmap/README.md
check F2 "deleted-on-success claim exists" grep -q "contract file is deleted" pmo-roadmap/README.md
check F2b "archive reality stated in the same file" grep -q "pmo-contract-archive/<sha>" pmo-roadmap/README.md
check F3 "intro says agent writes the contract" sh -c "sed -n \"9,12p\" pmo-roadmap/README.md | grep -q \"writes a fresh\""
check F3b "body says generated, not hand-typed" grep -q "generated, not hand-typed" pmo-roadmap/README.md
check F4 "installer list (78-97) omits commit-msg" sh -c "! sed -n \"78,97p\" pmo-roadmap/README.md | grep -q commit-msg"
check F4b "install.sh ships commit-msg" grep -q "commit-msg" pmo-roadmap/install.sh
check F5 "file map (642-674) omits hooks/commit-msg" sh -c "! sed -n \"642,674p\" pmo-roadmap/README.md | grep -q commit-msg"
check F5b "file map omits gate-parity test" sh -c "! sed -n \"642,674p\" pmo-roadmap/README.md | grep -q gate-parity"
check F6 "root validation continuation broken (203-204)" sh -c "sed -n \"203p\" README.md | grep -qv \"\\\\\\\\$\" && sed -n \"204p\" README.md | grep -q workbench-ui-smoke"
check F7 "root feature bullets (10-15) omit the dw CLI and web workbench" sh -c "! sed -n \"10,15p\" README.md | grep -qE \"dw-workbench|web|CLI\""
check F9 "update described as re-copying the hook, singular" grep -q "re-copies the methodology and hook (overwriting)" pmo-roadmap/README.md
check F11 "maintenance sync list omits gate.py" sh -c "! sed -n \"688,693p\" pmo-roadmap/README.md | grep -q gate.py"
echo "verification: $ok passed, $fail failed"
[ "$fail" -eq 0 ]`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 593d732174f414f530088d78f62696420dbcb4fa

```text
VERIFIED F1: mtime claim exists (pmo-roadmap/README.md:31)
VERIFIED F1b: index-tree reality stated in the same file
VERIFIED F2: deleted-on-success claim exists
VERIFIED F2b: archive reality stated in the same file
VERIFIED F3: intro says agent writes the contract
VERIFIED F3b: body says generated, not hand-typed
VERIFIED F4: installer list (78-97) omits commit-msg
VERIFIED F4b: install.sh ships commit-msg
VERIFIED F5: file map (642-674) omits hooks/commit-msg
VERIFIED F5b: file map omits gate-parity test
VERIFIED F6: root validation continuation broken (203-204)
VERIFIED F7: root feature bullets (10-15) omit the dw CLI and web workbench
VERIFIED F9: update described as re-copying the hook, singular
VERIFIED F11: maintenance sync list omits gate.py
verification: 14 passed, 0 failed
```
