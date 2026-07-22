# Evidence - WLA-26-07

- **Story:** WLA-26-07 - Turn quality and evidence into governed verdicts
- **Status:** done
- **Date:** 2026-07-22

## Proof

### Implementation and review

- `program_verdict.py` defines closed, hash-bound rubric, mechanical-fact,
  verifier-verdict, independent-panel, meta-verdict, architecture-verdict, and
  quality-proof contracts. Mechanical facts can only be derived from exact
  typed adapter receipts; prose and model confidence cannot satisfy them.
- Verdict assignment is fixed before review and binds the exact subject,
  repository/program/run/workflow/ledger state, rubric semantic hash,
  implementer principals, verifier seat and generation, workspace/session, and
  resolved harness/adapter/router/provider/model/auth-domain execution stack.
  Any changed binding makes the verdict stale rather than silently reusable.
- Independent non-deliberating judgments compose as `panel-verdict`, never as a
  council. Deterministic threshold/quorum/veto composition preserves every
  contributing and non-contributing verdict, dissent, abstention, source hash,
  and principal-independence proof.
- `program_deliberation.py` now derives a distinct immutable
  `delivery-workbench-decision@1` from completed replay. Its authority is one of
  a closed rule with no agent decider, one preassigned judge `decider_seat`, or
  one external checkpoint port. Judge identity includes stable seat address,
  role/slot, assignment generation, principal, workspace/session, and the full
  resolved execution binding; the judge remains limited to mechanically
  permitted outcomes.
- Every council decision includes rationale, citations, alternatives, accepted
  risks, dissent, route, source receipts, and an explicit bounded obligations
  array. Backlog, technical-debt, risk, research, and follow-up items carry
  priority, blocking state, accountable role, target, citations, and acceptance
  metadata. An open blocking obligation refuses advancement; carried
  non-blocking work is stamped with its source decision hash.
- The pure quality gate accepts only fresh, validated facts, verdicts, panels,
  council decisions, meta-audits, and architect judgments required by policy.
  It emits pass/fail/pending/refused proof with exact history, dissent,
  remediation, evidence preview, and decision/obligation lineage while every
  work, state, repository, roadmap, evidence, and grant effect remains false.
- Driver capability fingerprints now include router, provider, model vendor,
  family, identifier, revision or honest alias, model-binding mode, and
  auth-domain fingerprint. Organization roster and assignment hashes therefore
  change when the locally resolved provider/model stack changes.
- The wheel ships an optional `autonomous-story-quality` rubric template and
  pure `dw rubric list|validate` discovery. Install/update keeps an absent
  rubric/program inventory healthy and creates no policy, program state,
  process, grant, or default-mode detour. Source, vendored, and installed
  verdict/decision exports pass fresh-wheel parity.

### Acceptance mapping

- Evidence honesty: forged or conflicting receipts, agent prose as a fact,
  missing citations, content leakage, and stale subject/rubric/ledger bindings
  all fail closed.
- Independence and composition: self-verification, colliding principals,
  panel/council substitution, quorum loss, veto, abstention, conflicting active
  verdicts, and architect veto have deterministic covered refusals/routes.
- Audit and repair: random/full meta-audit, overturn without source erasure,
  superseding repair verdicts, bounded repair exhaustion, and immutable red
  history are proven.
- Decision authority: rule mode proves there is no ultimate agent; judge mode
  proves the exact preassigned decider and execution assignment; checkpoint
  mode proves the external port. Provider/model drift changes old authority.
- Decision debt: omission and malformed obligations refuse, blocking debt
  prevents green, and non-blocking obligations retain source-decision lineage.
- Surface boundary: this story supplies the shared pure core, rubric CLI, and
  packaged exports. Byte-equivalent live program CLI/MCP/HTTP/Workbench views,
  SSE, and device rendering are deliberately owned by WLA-26-11.

### Verification summary

- Core suite: 416/416 on Python 3.14 and 416/416 on the Python 3.9 floor.
- Focused organization/deliberation/verdict/driver slice: 40/40 on both floors.
- Fresh-wheel package smoke: passed on Python 3.9, including source/vendored/
  installed quality and council-decision exports and no ambient program setup.
- Canon, documentation, snippets, roadmap health, rider parity, update parity,
  syntax, and diff checks passed.

### Captured run — 2026-07-22T23:40:48Z

- **Command:** `bash -o pipefail -c set -e
PYTHONPATH=pmo-roadmap/lib python3 pmo-roadmap/tests/dw-core-tests.py -q
PYTHONPATH=pmo-roadmap/lib /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q
PYTHONPATH=pmo-roadmap/lib python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramOrganizationTest ProgramDeliberationTest ProgramVerdictTest OrchestrationDriverTest.test_config_and_capability_documents_are_closed_and_credential_free
PYTHONPATH=pmo-roadmap/lib /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py -q ProgramOrganizationTest ProgramDeliberationTest ProgramVerdictTest OrchestrationDriverTest.test_config_and_capability_documents_are_closed_and_credential_free
bash pmo-roadmap/tests/package-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
./.githooks/dw check work-log-automation
./.githooks/dw rider docs --check
pmo-roadmap/update.sh . --check
git diff --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f35af2f59a109604b493d8aeb4c33de0de5a730a

```text
----------------------------------------------------------------------
Ran 416 tests in 198.765s

OK
----------------------------------------------------------------------
Ran 416 tests in 199.171s

OK
----------------------------------------------------------------------
Ran 40 tests in 2.933s

OK
----------------------------------------------------------------------
Ran 40 tests in 3.062s

OK
package-smoke.sh: built delivery_workbench-1.14.0-py3-none-any.whl and delivery_workbench-1.14.0.tar.gz
package-smoke.sh: installed via venv+pip
package-smoke.sh: ok
canon-lint.sh: ok
docs-lint: ok (440 markdown files)
docs-lint.sh: ok (1s)
docs-lint snippets: ok
docs-snippet-smoke.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
