# Evidence - WLA-4-02

- **Story:** WLA-4-02 - Add agent-safe PMO mutation and drift context
- **Status:** done
- **Date:** 2026-07-01

## Proof

- `pmo-roadmap/bin/dw` reports JSON context with active phases, drift warnings,
  supplemental canon, hook snapshot compatibility, trace paths, optional recent
  commits, and work-log entries where available.
- `story status` refuses `done` without evidence and can create paired evidence
  while updating the story header and phase table in one command.
- `story evidence` and `phase close` write only under PMO-owned paths.
- Mutating commands compute the full PMO file change set before writing and use
  rollback restoration if a later write fails.
- `pmo-roadmap/tests/roadmap-cli.sh` covers canonical read/write flow,
  idempotent context output, idempotent same-status writes, missing-evidence
  refusal, evidence-backed done transition, standalone evidence attachment,
  phase-close refusal, phase close, work-log trace, intentional broken-link and
  evidence validation failures, stale current-phase pointer detection, multiple
  open phase warning, supplemental orchestrator discovery, and older hook
  snapshot reporting.

## Command Output

```text
$ python3 -m py_compile pmo-roadmap/bin/dw
```

```text
$ pmo-roadmap/tests/roadmap-cli.sh
roadmap-cli.sh: ok
```

```text
$ pmo-roadmap/bin/dw context work-log-automation --compact
{"kind":"delivery-workbench-roadmap-context","projects":[...],"schema_version":1,...}
```
