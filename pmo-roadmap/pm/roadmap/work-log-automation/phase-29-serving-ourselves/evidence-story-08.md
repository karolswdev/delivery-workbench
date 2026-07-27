# Evidence - WLA-29-08

- **Story:** WLA-29-08 - Serve ourselves for real
- **Status:** done
- **Date:** 2026-07-27

## Proof

### Captured run — 2026-07-27T08:06:10Z

- **Command:** `sh -c echo '=== FRICTION LEDGER (17 entries, accumulated across 13 attempts) ==='; cat /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/a2fee7a7-3967-4af9-9d32-b4c405c78f96/scratchpad/wla-29-08-friction-ledger.md; echo; echo '=== ALL PROGRAM RUNS (grants and outcomes) ==='; ls .git/pmo-programs/runs/; echo; echo '=== FINAL RUN LEDGER (program-a8b7131ba635a59ac3162dec) ==='; python3 -c "
import json
for line in open('.git/pmo-programs/runs/program-a8b7131ba635a59ac3162dec/ledger.jsonl'):
    det=(json.loads(line).get('detail') or {})
    keep={k:det.get(k) for k in ('claim_id','reason','result') if det.get(k)}
    print('-', str(keep)[:160])
"; echo; echo '=== RANGE VERIFICATION ==='; .githooks/dw verify 35101ee..HEAD`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4015aa3851bd5e2bae792dc6c352b9f63056a5b7

```text
=== FRICTION LEDGER (17 entries, accumulated across 13 attempts) ===
# WLA-29-08 friction ledger (draft, accumulated during phase 29 delivery)

Observed while operating the rails and landing stories 01-07. Each entry:
what happened, where, and the follow-up shape.

1. **Worktree creation absolutizes `core.hooksPath`.** Every `git worktree
   add` performed by agent tooling rewrote `core.hooksPath` from
   `.githooks` to an absolute path, which `dw doctor` treats as a FAIL and
   `dw step` escalates to a blocking `repair-rails` lease. Recurred 4+
   times in one session; each time cost a doctor lease + manual
   `git config core.hooksPath .githooks`. Follow-up: candidate target
   story for the real program run (small, real, code+tests: normalize or
   tolerate the absolute form, or re-pin on worktree events).

2. **Evidence capture truncates large proofs.** The packaged autonomous
   exam's output exceeded the evidence-capture bound and the recorded
   evidence cut off before the exam's summary JSON
   (`[PMO_EVIDENCE_OUTPUT_TRUNCATED]`), forcing a second focused captured
   run to make the evidence readable. Follow-up: an obligation — either a
   tail-preserving capture mode (keep head AND tail) or a documented
   convention that exam-scale proofs capture a focused sub-run.

3. **`dw knowledge refresh` argument shape.** `dw knowledge refresh
   <project>` errors (no project arg accepted) while sibling
   `dw knowledge ground <project> <story>` requires the project. Mild
   asymmetry; also `refresh` dumps the entire 2.6 MB map to stdout with no
   `--quiet`. Follow-up: obligation (UX polish).

4. **Localization-hint syntax is strict and self-documented only after
   failure.** Plain `- Affected files:` silently grounds to zero hints
   with per-line diagnostics; the required form is the bolded
   `**Affected files:**` label. The diagnostics were honest and the
   `hint_syntax` block in the output taught the fix — good — but the
   template comment should show the exact accepted syntax. Follow-up:
   template tweak obligation.

5. **First real grounded packet refused on a stale map** (recorded by the
   WLA-29-04 engineer): the stored symbol map lagged the index tree and
   packet assembly refused until an explicit `dw knowledge refresh`. The
   freshness rule worked exactly as contracted, but the operator loop
   ("refresh, then plan") wants a documented one-liner. Follow-up: docs
   obligation.

## Live adapter inventory (for the run design)

- claude: /Users/karol/.local/bin/claude (family: anthropic)
- codex: /Users/karol/.local/bin/codex (family: openai)
- pi: ~/.nvm/.../bin/pi (family: pi/openrouter per roster)
- Diversity rule satisfiable live: implementer=claude (anthropic),
  reviewer=codex (openai) or vice versa.

## Run-time friction (attempts 1-6, all ledgered)

6. **Write containment vs Python bytecode** (attempt 1): the declared test
   command wrote `__pycache__/*.pyc` outside declared paths; refused
   fail-closed with zero partial state. Fix shipped: `python3 -B`.
   Follow-up: docs note or a default-ignore for interpreter cache paths.
7. **Driver env allowlist drops `NODE_EXTRA_CA_CERTS` while keeping
   `HTTPS_PROXY`** (attempt 2): under a MITM-proxy sandbox the child claude
   fails SSL verification. Operational fix: proxy-free conductor launch.
   Follow-up obligation: add NODE_EXTRA_CA_CERTS (and lowercase proxy
   variants) to the driver allowlists.
8. **First-run workflows need attempt headroom** (attempt 2): agent-node
   `max_attempts: 1` turned one environmental failure into a permanent
   route-block. Fixed in config (2 attempts); authoring guidance follow-up.
9. **Machinery defect: user-workflow verdict nodes derived empty child
   grants** (attempt 3): compiler rejects `capability_ceiling` on verdict
   nodes while the runtime action builder read exactly that key; fixtures
   never hit it (built-in verdicts use a hardcoded path). Fixed in
   `program_conductor.py` with defaulting; shipped through the gate.
10. **Unledgered crash paths in the conductor** (attempts 3 and 6):
    child-grant refusals and verdict-content validation failures raised out
    of `supervise` (exit 1, no receipt, attempt not consumed) instead of
    recording a failed claim. Fix in flight for the verdict path; general
    sweep is a follow-up story.
11. **Grant/policy sizing: one child grant per dispatch** (attempts 4-5):
    `max_child_runs=1` starved the verifier; the policy ceiling then blocked
    the corrected grant. Both fixed; authoring guidance follow-up (size
    child runs to agent starts).
12. **Live verdicts had no response contract** (attempt 6): only the fixture
    adapter synthesizes conformant judgments; a live codex reviewer returned
    free-form citations and the strict validator refused ("verdict criterion
    evidence is malformed"). Fix in flight: explicit response_contract in
    the verdict prompt + malformed verdicts consume attempts as ledgered
    failures.
13. **Reviewer judged the wrong tree** (attempt 6): codex's substantive
    fail vote claimed docs/tests were missing, but the candidate diff
    contains all 8 files including them — the reviewer read the checked-out
    tree, not the supplied candidate. Fix in flight: explicit
    judge-the-candidate-diff instruction; longer-term: candidate-workspace
    checkout for reviewers.
14. **Pre-fix crashes strand claims; recovery refuses multiple** (attempt 6
    resume): correct fail-closed behavior, but it makes a run with two
    stranded claims unrecoverable. Follow-up: a guarded operator act to
    close stranded claims as failed, or single-claim-at-a-time recovery.
15. **Rubric fact-id vs check-node fact-id mismatch surfaces only at live
    verdict time** (attempt 7): `dw program validate` accepted a rubric
    whose mechanical criterion named a fact no workflow node publishes.
    Follow-up: validate should cross-check rubric mechanical facts against
    the bound workflow's check nodes.
16. **Structural: stored mechanical facts can never satisfy user-workflow
    verdicts** (attempt 8): check facts are subject-bound to an
    artifact-set at check-time ledger head; verdict validation requires
    facts bound to the verdict's subject (candidate kind/hash, later
    head) under strict equality. Every user-authored check→verdict pair
    refuses `verdict-stale`. Fix in flight: rebuild facts onto the verdict
    subject at issuance, preserving the original observation bindings.
    Positive note: both failed verdict attempts were properly ledgered and
    retried — the attempt-6 repair held.

=== ALL PROGRAM RUNS (grants and outcomes) ===
program-05330044ac9df7c9399a7c30
program-0dd7bc1cb68324df10010315
program-175d45be1277c25136f8b09d
program-20e09b363f0967cd75eee438
program-2cabee3f7e1c20de54b1fa10
program-7f1211f19e324a26e849b8ea
program-815b34db84542d0ded4ab325
program-a8b7131ba635a59ac3162dec
program-aec8e153d555f89a214e5151
program-c6f5c126632f0462f378dbc8
program-cc5796ef158c74687d77af3a
program-d2dd5d8433626071f4913419

=== FINAL RUN LEDGER (program-a8b7131ba635a59ac3162dec) ===
- {}
- {}
- {'claim_id': 'claim-87bc03cf373c1bb1e89c9f3a', 'reason': 'Conduct declared selection at its stable hierarchy address.'}
- {'claim_id': 'claim-87bc03cf373c1bb1e89c9f3a', 'reason': 'Recorded deterministic selection receipt.', 'result': 'succeeded'}
- {'claim_id': 'claim-74e45a1c87d41b3bf0d1d310', 'reason': 'Conduct declared assignment at its stable hierarchy address.'}
- {'claim_id': 'claim-74e45a1c87d41b3bf0d1d310', 'reason': 'Recorded deterministic assignment receipt.', 'result': 'succeeded'}
- {'claim_id': 'claim-dc2f2672ba4871ba83e7b74a', 'reason': 'Conduct declared agent at its stable hierarchy address.'}
- {'claim_id': 'claim-dc2f2672ba4871ba83e7b74a', 'reason': 'Recorded exact derived child authority.', 'result': 'succeeded'}
- {'claim_id': 'claim-f7ce165640e4b9711a0bc222', 'reason': 'Conduct declared agent at its stable hierarchy address.'}
- {'claim_id': 'claim-f7ce165640e4b9711a0bc222'}
- {'claim_id': 'claim-f7ce165640e4b9711a0bc222', 'reason': 'Validated and recorded the exact driver result.', 'result': 'succeeded'}
- {'claim_id': 'claim-ae3769f6898608af0d8f8fd1', 'reason': 'Conduct declared check at its stable hierarchy address.'}
- {'claim_id': 'claim-ae3769f6898608af0d8f8fd1', 'reason': 'Closed check returned pass.', 'result': 'succeeded'}
- {'claim_id': 'claim-26150e960cc2b3b8111bf6ad', 'reason': 'Conduct declared verdict at its stable hierarchy address.'}
- {'claim_id': 'claim-26150e960cc2b3b8111bf6ad', 'reason': 'Recorded exact derived child authority.', 'result': 'succeeded'}
- {'claim_id': 'claim-b794097066b5d8331033c8cf', 'reason': 'Conduct declared verdict at its stable hierarchy address.'}
- {'claim_id': 'claim-b794097066b5d8331033c8cf'}
- {'claim_id': 'claim-b794097066b5d8331033c8cf', 'reason': 'Verdict model output validation failed: unsafe-value at criteria/hook-path-contract/citations/0/locato
- {'claim_id': 'claim-93d1de2c32973b5c6f9019dc', 'reason': 'Conduct declared verdict at its stable hierarchy address.'}
- {'claim_id': 'claim-93d1de2c32973b5c6f9019dc', 'reason': 'Recorded exact derived child authority.', 'result': 'succeeded'}
- {'claim_id': 'claim-6fc06d13d78e0ed5ba05272e', 'reason': 'Conduct declared verdict at its stable hierarchy address.'}
- {'claim_id': 'claim-6fc06d13d78e0ed5ba05272e'}
- {'claim_id': 'claim-596c21927644fd98109b7a9b', 'reason': 'Conduct declared verdict at its stable hierarchy address.'}
- {'claim_id': 'claim-596c21927644fd98109b7a9b', 'reason': 'Issued one rubric-bound agent-verdict.', 'result': 'succeeded'}
- {'claim_id': 'claim-6fc06d13d78e0ed5ba05272e', 'reason': 'Validated and recorded the exact driver result.', 'result': 'succeeded'}

=== RANGE VERIFICATION ===
dw verify: ok (11 commits verified, 0 pre-epoch skipped)
```
