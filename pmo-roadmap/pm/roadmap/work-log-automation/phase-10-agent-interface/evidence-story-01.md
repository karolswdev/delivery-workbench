# Evidence - WLA-10-01

- **Story:** WLA-10-01 - Define the MCP surface contract
- **Status:** done
- **Date:** 2026-07-03

## Proof

Deliverable: `docs/mcp.md` — the MCP surface contract. Nine tools
(orientation: context/next/check/doctor; verification: verify/gate;
guarded mutations: story_status/evidence_capture/contract_new),
each a thin adapter naming the exact `dw_pmo` core function it
calls — the Phase 6 no-second-implementation invariant restated as
a tested property. The load-bearing section is the exclusions: no
certification tool, no commit tool, no bundle-consent writer, with
the rationale that attestation loses its meaning the moment it can
be mechanized. Protocol subset pinned (stdio, newline-delimited
JSON-RPC 2.0, version 2025-06-18, tools-only capability, serial
loop, stdlib-only), repository binding and outside-repo behavior
specified, decisions mirrored in the phase status.

The first captured run failed on its own shell quoting (single
quotes inside a bash -c wrapper — a recurring class this session);
the second is authoritative: all 9 documented tool→core mappings
resolve to real functions, the exclusion list is absent from the
inventory, docs-lint clean.


### Captured run — 2026-07-03T19:50:24Z

- **Command:** `bash -c set -e; echo "== every documented tool names a real core function =="; python3 - <<PYEOF
import re, sys
doc = open("docs/mcp.md").read()
pairs = re.findall(r"\`(dw_[a-z_]+)\` \| \`([a-z]+)\.([a-z_]+)", doc)
assert len(pairs) >= 9, pairs
import importlib.util, pathlib
sys.path.insert(0, "pmo-roadmap/lib")
ok = True
for tool, mod, fn in pairs:
    src = pathlib.Path(f"pmo-roadmap/lib/dw_pmo/{mod}.py").read_text()
    hit = f"def {fn}(" in src
    print(f" - {tool} -> dw_pmo.{mod}.{fn}: {OK if hit else MISSING}")
    ok = ok and hit
extra = re.findall(r"dw_(?:certify|commit|bundle)", doc.split("## Tool inventory")[1].split("## Protocol")[0])
assert not extra, f"excluded tool leaked into inventory: {extra}"
print(f"{len(pairs)} tools mapped; certify/commit/bundle absent from inventory")
sys.exit(0 if ok else 1)
PYEOF
echo; bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** eeebfa30761d61c43de912ca33911dbbf7537757

```text
== every documented tool names a real core function ==
Traceback (most recent call last):
  File "<stdin>", line 11, in <module>
NameError: name 'OK' is not defined. Did you mean: 'ok'?
```

### Captured run — 2026-07-03T19:50:47Z

- **Command:** `bash -c set -e; echo "== every documented tool names a real core function =="; python3 - <<PYEOF
import re, sys, pathlib
doc = open("docs/mcp.md").read()
pairs = re.findall(r"\`(dw_[a-z_]+)\` \| \`([a-z]+)\.([a-z_]+)", doc)
assert len(pairs) >= 9, pairs
ok = True
for tool, mod, fn in pairs:
    src = pathlib.Path("pmo-roadmap/lib/dw_pmo/" + mod + ".py").read_text()
    hit = ("def " + fn + "(") in src
    print(" - " + tool + " -> dw_pmo." + mod + "." + fn + ": " + ("OK" if hit else "MISSING"))
    ok = ok and hit
inventory = doc.split("## Tool inventory")[1].split("## Protocol")[0]
leaked = re.findall(r"dw_(?:certify|commit|bundle)", inventory)
assert not leaked, leaked
print(str(len(pairs)) + " tools mapped; certify/commit/bundle absent from the inventory")
sys.exit(0 if ok else 1)
PYEOF
echo; bash pmo-roadmap/tests/docs-lint.sh 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eeebfa30761d61c43de912ca33911dbbf7537757

```text
== every documented tool names a real core function ==
 - dw_context -> dw_pmo.api.build_context_payload: OK
 - dw_next -> dw_pmo.api.next_story: OK
 - dw_check -> dw_pmo.validate.check_project: OK
 - dw_doctor -> dw_pmo.doctor.run_doctor: OK
 - dw_verify -> dw_pmo.verify.run_verify: OK
 - dw_gate -> dw_pmo.gate.run_gate: OK
 - dw_story_status -> dw_pmo.mutations.plan_story_status: OK
 - dw_evidence_capture -> dw_pmo.evidence.run_capture: OK
 - dw_contract_new -> dw_pmo.contract.build_contract: OK
9 tools mapped; certify/commit/bundle absent from the inventory

docs-lint.sh: ok (0s)
```
