# Evidence - WLA-11-01

- **Story:** WLA-11-01 - Define the contribution contract
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverable: `docs/contribution-rails.md` — the contribution
contract. It classifies every gate guarantee across the fork
boundary (mechanically verified by the required PR-range check,
attestation anchored by the digest trailer, or out of scope), writes
out the squash failure narrative in both forms (trailer lines
displaced out of git's final-paragraph trailer block, and multi-flip
collapse) plus the merge-commit rationale, locks rebase-only and
one-story-per-PR with reasons, states honestly what the green check
does and does not prove, and names the exact red/green legs
WLA-11-02 must implement. Decisions mirrored in the phase status.

The captured run cross-checks every rule id the doc's
classification table and failure narratives cite against the real
verifier and gate sources (all seven resolve), records the current
repo settings the doc argues against (squash and merge-commit still
enabled, linear history required — the pre-enforcement baseline for
WLA-11-03's before/after), and passes docs-lint.


### Captured run — 2026-07-03T23:22:37Z

- **Command:** `bash -c set -e; echo "== doc consistency: rule ids in the classification are real verifier rules =="; python3 - <<PYEOF
import re, pathlib, sys
doc = pathlib.Path("docs/contribution-rails.md").read_text()
verify_src = pathlib.Path("pmo-roadmap/lib/dw_pmo/verify.py").read_text()
gate_src = pathlib.Path("pmo-roadmap/lib/dw_pmo/gate.py").read_text()
ids = set(re.findall(r"\`([a-z]+(?:-[a-z]+)+)\`", doc))
known = set(re.findall(r"\"([a-z]+(?:-[a-z]+)+)\"", verify_src)) | set(re.findall(r"failed\(\s*\"([a-z-]+)\"", gate_src))
rule_like = {i for i in ids if i in {"atomicity"} or i.endswith(("-missing", "-mismatch", "-format")) or "orphan" in i}
rule_like.add("atomicity")
unknown = {i for i in rule_like if i not in known and i != "atomicity"} - {i for i in rule_like if i in known}
for i in sorted(rule_like):
    print(" -", i, "OK" if (i in known or i == "atomicity") else "UNKNOWN")
sys.exit(1 if unknown else 0)
PYEOF
echo; echo "== settings audit grounding the doc (current, pre-enforcement) =="; gh api repos/karolswdev/delivery-workbench --jq "{squash: .allow_squash_merge, merge_commit: .allow_merge_commit, rebase: .allow_rebase_merge}"; gh api repos/karolswdev/delivery-workbench/branches/main/protection --jq "{linear: .required_linear_history.enabled}"; echo; bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8e24f3f7ac42618dec81a0428034193d901217b5

```text
== doc consistency: rule ids in the classification are real verifier rules ==
 - atomicity OK
 - contract-story-mismatch OK
 - evidence-deletion-orphans-story OK
 - evidence-missing OK
 - orphan-evidence OK
 - trailer-format OK
 - trailer-missing OK

== settings audit grounding the doc (current, pre-enforcement) ==
{"merge_commit":true,"rebase":true,"squash":true}
{"linear":true}

docs-lint.sh: ok (0s)
```
