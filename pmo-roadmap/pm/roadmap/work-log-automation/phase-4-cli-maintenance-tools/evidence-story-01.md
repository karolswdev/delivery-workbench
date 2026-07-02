# Evidence - WLA-4-01

- **Story:** WLA-4-01 - Add roadmap maintenance CLI
- **Status:** done
- **Date:** 2026-07-01

## Proof

- `pmo-roadmap/bin/dw` implements project listing, tree views, JSON context
  snapshots, phase list/show/create, story list/create, next-story selection,
  and structural checks.
- `phase create` reads `templates/phase-status.md.tmpl` when available and
  falls back to an embedded scaffold only for installed layouts without
  templates.
- `install.sh` and `update.sh` copy the helper into installed projects as
  `.githooks/dw`.
- `pmo-roadmap/tests/roadmap-cli.sh` covers project listing, phase creation,
  README phase-index update, story creation, tree output, story listing,
  next-story selection, passing check, and mismatch detection.

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

```text
$ pmo-roadmap/bin/dw tree work-log-automation --done
work-log-automation (WLA)
  phase 4: phase-4-cli-maintenance-tools
    WLA-4-01 [done] evidence:yes Add roadmap maintenance CLI
```
