# Delivery Workbench

![Delivery Workbench icon](./pmo-roadmap/assets/delivery-workbench-icon.png)

Delivery Workbench is an evidence-first operating framework for agentic
software delivery.

It gives an existing or new Git project:

- roadmap structure for phases, stories, and evidence
- commit-time PMO contracts
- mechanical story/evidence pairing checks
- optional local daily work logs
- deferred work-log summarization
- mid-project adoption discovery with Codex or Claude

The framework currently lives in [`pmo-roadmap/`](./pmo-roadmap/).

## Status

Experimental but usable. The project is intentionally opinionated and designed
for builders who want agent-assisted software work to leave a durable evidence
trail.

## Quick Start

Install into an existing Git project:

```bash
cd pmo-roadmap
./install.sh /path/to/project --skip-bootstrap
```

Run adoption discovery for an existing project:

```bash
./bootstrap/adopt-project.sh /path/to/project \
  --project-name "My Project" \
  --project-slug myproject \
  --project-prefix MP
```

Bootstrap a new roadmap:

```bash
./bootstrap/new-project.sh /path/to/project myproject "My Project" MP
```

## Why

Agentic coding work can move fast enough that project memory becomes the
bottleneck. Delivery Workbench treats planning, verification, and commit-time
intent as first-class artifacts.

The goal is not ceremony. The goal is recoverable delivery: a future human or
agent should be able to inspect the repository and understand what shipped,
why it mattered, what proved it, and where the next responsible move begins.

## Documentation

- [Framework README](./pmo-roadmap/README.md)
- [PMO contract](./pmo-roadmap/templates/PMO-CONTRACT.md)
- [Roadmap builder methodology](./pmo-roadmap/templates/roadmap-builder.md)
- [Brand notes](./pmo-roadmap/brand/delivery-workbench.md)

## Validation

```bash
bash -n pmo-roadmap/bin/work-log-read \
  pmo-roadmap/bin/work-log-summarize \
  pmo-roadmap/bootstrap/adopt-project.sh \
  pmo-roadmap/bootstrap/new-project.sh \
  pmo-roadmap/hooks/pre-commit \
  pmo-roadmap/hooks/post-commit \
  pmo-roadmap/install.sh \
  pmo-roadmap/update.sh \
  pmo-roadmap/tests/adoption-discovery.sh \
  pmo-roadmap/tests/work-log-mvp.sh

pmo-roadmap/tests/adoption-discovery.sh
pmo-roadmap/tests/work-log-mvp.sh
```

## License

MIT.
