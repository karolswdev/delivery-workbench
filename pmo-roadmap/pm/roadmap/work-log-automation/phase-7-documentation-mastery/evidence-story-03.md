# Evidence - WLA-7-03

- **Story:** WLA-7-03 - Canon and template accuracy pass
- **Status:** done
- **Date:** 2026-07-03

## What shipped

- **PMO-CONTRACT.md accuracy fixes:** rule 6's mechanics now describe
  the gate as it works (HEAD-vs-index header comparison, done-synonyms,
  integer evidence pairing, deletion-orphan protection) instead of the
  pre-v2 literal diff-line scan; rule 7 says archived-then-cleared
  instead of "auto-deletes"; and every mechanically-enforced statement
  now names its rule id — `contract-index-tree-mismatch`,
  `contract-unknown-box`/`contract-missing-box`,
  `contract-tests-capture-mismatch`, `atomicity`, `evidence-missing`,
  `orphan-evidence`, `evidence-deletion-orphans-story` — each verified
  against the gate source by a new doc-parity test.
- **roadmap-builder.md fixes:** the legacy personal-project reference
  in §2.3 is gone (and `pantry-life` joined canon-lint's forbidden
  patterns so it cannot return); §2.5's final-summary header now
  documents the generator's actual output (the previous spec described
  a header no shipped phase ever used); §5 names the mechanical
  scaffolders; and §9's maintenance log honestly records the Phase 6
  and Phase 7 canon changes.
- **A real template divergence found and killed:** `dw story create`
  rendered an embedded story shape while the bootstrap rendered
  `story.md.tmpl` — two generators, two scaffolds. `render_story_template`
  now reads the documented template (with a new `{{STATUS}}`
  placeholder, substituted by the bootstrap too), so the CLI, the
  bootstrap, and the documentation produce byte-identical scaffolds —
  proven by capture and locked by
  `test_story_scaffold_matches_documented_template`.
- **Worked example modernized:** the extension example no longer tells
  projects to bump the legacy `EXPECTED_BOXES` count — the fence is
  authoritative since contract v2.
- **Four new doc-parity tests** (83-test suite): cited rule ids exist
  in the gate source; the canon fence boxes equal the generator's
  canonical fallback (and `CONTRACT.md.tmpl` single-sources via
  `{{BOXES}}`); the builder's final-summary spec matches
  `render_final_summary`; and the story scaffold matches the
  documented template byte-for-byte.

## Proof — captured runs (appended by `dw evidence capture`)

### Captured run — 2026-07-03T00:10:30Z

- **Command:** `sh -c 
python3 -c "
import sys; sys.path.insert(0,\"pmo-roadmap/lib\")
from pathlib import Path
from dw_pmo.render import render_story_template
from dw_pmo.model import Project, Phase
proj = Project(\"demo\", Path(\"/tmp/x/pm/roadmap/demo\"), \"DM\")
phase = Phase(number=1, slug=\"alpha\", path=Path(\"/tmp/x/pm/roadmap/demo/phase-1-alpha\"))
rendered = render_story_template(proj, phase, 3, \"Sample Story\", \"backlog\")
tmpl = Path(\"pmo-roadmap/templates/story.md.tmpl\").read_text()
for s, v in {\"{{STORY_ID}}\":\"DM-1-03\",\"{{STORY_TITLE}}\":\"Sample Story\",\"{{PROJECT_SLUG}}\":\"demo\",\"{{PHASE_N}}\":\"1\",\"{{STATUS}}\":\"backlog\"}.items():
    tmpl = tmpl.replace(s, v)
assert rendered == tmpl
print(\"scaffold vs documented template: BYTE-IDENTICAL\")"
echo "── rule-id citations in canon, verified against gate.py:"
grep -oE "\`(contract-[a-z-]+|atomicity|evidence-missing|orphan-evidence|evidence-deletion-orphans-story)\`" pmo-roadmap/templates/PMO-CONTRACT.md | sort -u | tr -d "\`" | while read -r id; do grep -q "\"$id\"" pmo-roadmap/lib/dw_pmo/gate.py pmo-roadmap/lib/dw_pmo/contract.py && echo "  cited+enforced: $id"; done`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c8d35d88939b9931da3e6e8e175c89ff3e3fe9be

```text
scaffold vs documented template: BYTE-IDENTICAL
── rule-id citations in canon, verified against gate.py:
  cited+enforced: atomicity
  cited+enforced: contract-index-tree-mismatch
  cited+enforced: contract-missing-box
  cited+enforced: contract-tests-capture-mismatch
  cited+enforced: contract-tier-mismatch
  cited+enforced: contract-unknown-box
  cited+enforced: evidence-deletion-orphans-story
  cited+enforced: evidence-missing
  cited+enforced: orphan-evidence
```

### Captured run — 2026-07-03T00:10:30Z

- **Command:** `python3 pmo-roadmap/tests/dw-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c8d35d88939b9931da3e6e8e175c89ff3e3fe9be

```text
test_agent_docs_block_lifecycle (__main__.DwCoreTest.test_agent_docs_block_lifecycle) ... ok
test_apply_cycle_and_stale_refusal (__main__.DwCoreTest.test_apply_cycle_and_stale_refusal) ... ok
test_apply_refuses_tampered_intent (__main__.DwCoreTest.test_apply_refuses_tampered_intent) ... ok
test_appl
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```
