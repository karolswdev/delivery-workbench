# Evidence - WLA-0-05

- **Story:** WLA-0-05 - Prove the roadmap against the framework's own constraints
- **Status:** done
- **Date:** 2026-07-01

## Proof

- Every story in the roadmap has acceptance criteria and a test plan.
- The phase status files name risks with stop signals and completed evidence.
- The completed roadmap can be rendered by the CLI and checked structurally.

## Command Output

```text
$ pmo-roadmap/bin/dw tree work-log-automation --done
work-log-automation (WLA)
  phase 0: phase-0-architecture
    WLA-0-01 [done] evidence:yes Define the consent and log-entry contract
    WLA-0-02 [done] evidence:yes Design the capture/finalize hook lifecycle
  ...
  phase 4: phase-4-cli-maintenance-tools
    WLA-4-01 [done] evidence:yes Add roadmap maintenance CLI
```

```text
$ pmo-roadmap/bin/dw check work-log-automation
dw check: ok
```
