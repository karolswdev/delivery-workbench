# Evidence - WLA-35-06

- **Story:** WLA-35-06 - AgentGlass memory pane
- **Status:** done
- **Date:** 2026-08-01

## Proof

Implemented by Sol (GPT-5.6) under orchestration; reviewed and verified by the operator session.

What shipped: the AgentGlass memory pane — `memory-panel.js` (vanilla custom elements, phase-33 design system, no Shadow DOM, no dependencies), loaded through the hash-routed shell and byte-synced into `.githooks/workbench/`. Reachable from six surfaces: run toolbar, program toolbar, session panel (when a run is pinned), outcomes panel run summary, per-item needs-you actions, and generated command-palette entries. Open/close preserves the hash route and returns focus to the originating control. Summary-first layout (recall timing, freshness, included/excluded counts, source mix, writeback state), memory cards with factual summary, confidence, match reasons, source path, and supersession state, and three clearly separated groups: available to the agent / referenced by a decision / written after completion. Loading, populated, verified-empty, missing, stale, tampered, malformed, written-back, and superseded states all render plain-language explanations with the typed refusal under a technical-details fold, and the copy states that recall neither caused nor authorized anything.

The authoritative run is the first capture below: workbench-accessibility-contract.py — 13 journeys, 2 viewports (wide + 390px), 34 new memory-pane checks, keyboard/focus/semantics coverage, exit 0. The second capture: workbench-explorer.sh (15 new memory-pane shell/surface/installed-payload assertions) plus the product-language lint (18 reserved terms, negative fixture still refused), both exit 0.

### Captured run — 2026-08-01T20:09:56Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/workbench-accessibility-contract.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d3dd7b0e8120c9cc0c0d174d36b94a72f8f6b7d1

```text
workbench-accessibility-contract.py: ok (13 journeys, 2 viewports, 34 memory-pane checks, keyboard/focus/semantics/manual evidence)
```

### Captured run — 2026-08-01T20:09:56Z

- **Command:** `/bin/sh -c bash pmo-roadmap/tests/workbench-explorer.sh && /usr/bin/python3 pmo-roadmap/tests/workbench-language-lint.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d3dd7b0e8120c9cc0c0d174d36b94a72f8f6b7d1

```text
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.dLgvsJ/repo
dw-workbench: http://127.0.0.1:18867/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.dLgvsJ/installed
dw-workbench: http://127.0.0.1:18868/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.dLgvsJ/repo
dw-workbench: http://127.0.0.1:18867/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
workbench-language-lint.py: ok (18 reserved terms; negative fixture refused: <negative-fixture>/app.js:1: forbidden term 'grant' in ordinary panel text: 'The grant is visible here.')
```
