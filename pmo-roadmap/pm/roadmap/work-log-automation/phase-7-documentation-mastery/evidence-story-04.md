# Evidence - WLA-7-04

- **Story:** WLA-7-04 - Package the Claude Code plugin
- **Status:** done
- **Date:** 2026-07-03

## What shipped

- **The plugin package:** `.claude-plugin/marketplace.json` (this repo
  is its own marketplace) and `plugin/` — manifest
  (`.claude-plugin/plugin.json`, MIT, keywords, version), the four
  slash commands, and the `delivery-workbench` **skill** teaching the
  complete operating loop: orient (`context`/`next`/`check` with the
  exit contracts), the story lifecycle with evidence capture, contract
  generation and honest certification, gate rules with refusal
  recovery ("read the banner — it names the rule id and remediation";
  never `--no-verify`), canon pointers, the workbench, and what to do
  when a repo lacks the rails.
- **Installed for real, not hypothetically:** `claude plugin validate`
  passes, `claude plugin marketplace add` + `claude plugin install
  delivery-workbench@delivery-workbench` succeed locally, and
  `claude plugin list` shows v1.5.0 enabled (captured below).
- **Parity is mechanical, not aspirational** (three new unit tests,
  86-test suite): every `.githooks/dw …` invocation the managed
  CLAUDE.md block teaches must appear in the skill; the canonical
  status vocabulary, gate invariants, and the no-bypass rule are
  asserted; the four command files are byte-identical between
  `pmo-roadmap/agent/` (installer source) and `plugin/commands/`; and
  `plugin.json`'s version must equal `dw_pmo.__version__` — one
  version source, test-enforced.
- **CI-safe validation:** `tests/plugin-validate.sh` checks manifests,
  declared files, and the version single-source with stdlib only, and
  additionally runs `claude plugin validate` where the CLI exists —
  wired into validation.yml on both OS legs and both README
  validation lists.
- **Docs:** the framework README's new "Claude Code plugin" section
  gives the two install commands and answers when-to-use-which: the
  plugin travels with Claude Code (skill + commands everywhere);
  `install.sh` wires the repository (hooks, gate, dw, workbench,
  managed block). A repo needs the rails either way — the plugin
  complements the install.

## Proof — captured runs (appended by `dw evidence capture`)

### Captured run — 2026-07-03T00:27:13Z

- **Command:** `sh -c 
claude plugin validate plugin 2>&1 | tail -1
claude plugin uninstall delivery-workbench@delivery-workbench >/dev/null 2>&1 || true
claude plugin install delivery-workbench@delivery-workbench 2>&1 | tail -1
claude plugin list 2>&1 | grep -A 3 "delivery-workbench@delivery-workbench" | head -4
pmo-roadmap/tests/plugin-validate.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ae818329d69fbab8dc07cb97c76aa3ae92abad02

```text
✔ Validation passed
Installing plugin "delivery-workbench@delivery-workbench"...✔ Successfully installed plugin: delivery-workbench@delivery-workbench (scope: user)
  ❯ delivery-workbench@delivery-workbench
    Version: 1.5.0
    Scope: user
    Status: ✔ enabled
plugin manifests: ok (version 1.5.0, 4 commands, 1 skill)
claude plugin validate: ok
plugin-validate.sh: ok
```

### Captured run — 2026-07-03T00:27:15Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ae818329d69fbab8dc07cb97c76aa3ae92abad02

```text
test_agent_docs_block_lifecycle (__main__.DwCoreTest.test_agent_docs_block_lifecycle) ... ok
test_apply_cycle_and_stale_refusal (__main__.DwCoreTest.test_apply_cycle_and_stale_refusal) ... ok
test_apply_refuses_tampered_intent (__main__.DwCoreTest.test_apply_refuses_tampered_intent) ... ok
test_appl
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
