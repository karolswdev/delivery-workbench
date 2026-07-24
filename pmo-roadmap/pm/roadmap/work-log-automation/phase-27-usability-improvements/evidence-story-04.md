# Evidence - WLA-27-04

- **Story:** WLA-27-04 - Make plan and workflow authoring task-shaped
- **Status:** done
- **Date:** 2026-07-24

## Proof

The new pure
[`plan_authoring.py`](../../../../lib/dw_pmo/plan_authoring.py) projection
attaches `delivery-workbench-delivery-plan-authoring@1` to selected Program
Studio documents and mutation previews. It consumes only the existing exact
source document, graph, validation result, and graph/config round-trip result.
It owns no saved format, eligibility, authority, evidence, review outcome, or
runtime meaning.

Program and work-flow authoring now opens on seven delivery decisions in review
order:

1. delivery scope;
2. work flow;
3. quality and review;
4. decision points;
5. repair and escalation;
6. stop conditions;
7. limits.

Every section states the question it answers, its source-backed answer,
guidance, examples, and any correction. A persistent **Review before save**
summary covers all seven answers in that same order. Program controls edit
scope, work routes, phase decisions, stops, and finite limits. Work-flow
controls edit named inputs and ordinary work, check, review, and decision
steps. Renaming routes, inputs, or steps carries declared dependent references
instead of stranding the intended exact configuration.

## Progressive exactness and lossless refusal

The ordinary plan view does not require graph vocabulary. Hierarchical flows,
nested work, bounded repetition, discussion cells, exact conditions, portable
fields, and raw import/export remain editable under **Technical details** in
graph/field and lossless-configuration modes. The technical modes operate on
the same in-memory `studio.raw` object as the ordinary controls.

Valid advanced configurations round-trip with semantic and layout identity
preserved. Targeted edits preserve all unedited fields. A deliberately invalid
fixture with `future_extension` keeps that unknown object in both raw and graph
configuration, maps the refusal to **Work flow**, and disables save rather than
dropping or translating the extension. Exact diagnostic source, pointer, code,
message, remediation, node, and field remain adjacent under Technical details.

The canonical advanced example now uses ordinary title and purpose copy while
retaining its exact nested flow, bounded loop, discussion, inputs, routes, and
limits.

## No-side-effect boundary

The authoring view explicitly reports false for work start, policy write,
roadmap write, run-state write, permission creation, process/observer start,
notification, and network effects. Repeated selected-document and invalid
preview reads leave the repository checksum unchanged and create no program
store or run state.

Drafting, switching sections, simulation, validation, technical inspection,
import, export, and abandonment remain browser-local or read-only. **Review
this save** reuses the existing fingerprint-bound Program Studio preview. It
states that confirmation can change only one named file, starts no work,
changes no roadmap status, and provides no permission; exact path,
fingerprint, and diff remain under Technical details. Invalid previews expose
no apply control, and stale apply still refuses.

## Wide, narrow, and journey review

The browser harness rendered 68 canonical Workbench states at 1440x900 and
390x844, including:

- a valid advanced work flow in the default Plan view;
- a program plan with scope and work-route controls;
- an invalid unknown-preserving work flow;
- decision-shaped validation;
- simulation and permission details;
- exact technical graph and lossless-configuration modes.

Manual review confirmed that the seven-section rail, current question,
ordinary editor, and ordered review summary are visible together on wide
screens. At 390px, controls become one column, the decision rail scrolls
horizontally with the next decision visible, native fields remain usable, and
content stays inside the task viewport. Valid work flows enable separate save
review; invalid work flows show per-section correction counts and keep it
disabled.

The versioned usability fixtures now point plan design at the authoring model
and exact inspection at the technical configuration state. All thirteen
whole-task journeys, fifteen reachable states, six red fixtures, ten product
concepts, eighteen surfaces, and eighteen reserved terms pass their executable
contracts.

## Regression and distribution proof

- `python3 pmo-roadmap/tests/dw-core-tests.py` — 480 tests in 794.897 seconds,
  `OK`.
- `bash pmo-roadmap/tests/package-smoke.sh` — built and installed the wheel on
  Python 3.9, required the packaged authoring module/kind/section order and
  round-trip flags, then passed guided status, deliberate step, bounded
  orchestration, outward signals, and the autonomous multi-phase exam.
- The packaged autonomous exam completed three stories across two phases with
  203 replayed/streamed events, nine conductor and eighteen delivery-boundary
  crash recoveries, three commits/pushes, independent review,
  council/meta/architect proof, one repair round, and the full refusal matrix.
- Its separate vanilla consumer exposed the same three optional delivery
  choices while program/run/notification stores, ambient network,
  background polling, setup writes, and work starts remained absent.
- Program Studio unit tests, source/installed HTTP explorer parity, product
  language, usability journeys, docs/snippets/canon, source/vendor alignment,
  syntax, and the 68-render viewport suite passed independently.

The focused captured run below binds the completed story state to the final
model, parity, viewport, documentation, roadmap, and vendoring checks.

### Captured run — 2026-07-24T21:16:31Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py ProgramStudioTest
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/usability-journey-contract.py
bash pmo-roadmap/tests/workbench-explorer.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
node --check pmo-roadmap/workbench/app.js
python3 -m py_compile pmo-roadmap/lib/dw_pmo/plan_authoring.py pmo-roadmap/lib/dw_pmo/program_studio.py
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2dbe3b1f35d1e700561641e8a634316ad3e37a97

```text
test_authority_preview_separates_requests_and_never_grants (__main__.ProgramStudioTest.test_authority_preview_separates_requests_and_never_grants) ... ok
test_containment_and_http_adapter_share_the_same_model (__main__.ProgramStudioTest.test_containment_and_http_adapter_share_the_same_model) ... ok
test_delivery_authoring_maps_refusals_to_decisions_and_preserves_unknowns (__main__.ProgramStudioTest.test_delivery_authoring_maps_refusals_to_decisions_and_preserves_unknowns) ... ok
test_delivery_authoring_orders_seven_decisions_over_exact_workflow (__main__.ProgramStudioTest.test_delivery_authoring_orders_seven_decisions_over_exact_workflow) ... ok
test_diagnostics_link_exact_graph_node_and_json_pointer (__main__.ProgramStudioTest.test_diagnostics_link_exact_graph_node_and_json_pointer) ... ok
test_guarded_save_is_one_file_stale_safe_and_delete_is_explicit (__main__.ProgramStudioTest.test_guarded_save_is_one_file_stale_safe_and_delete_is_explicit) ... ok
test_layout_move_changes_document_not_semantic_hash (__main__.ProgramStudioTest.test_layout_move_changes_document_not_semantic_hash) ... ok
test_no_program_is_healthy_pure_and_creates_nothing (__main__.ProgramStudioTest.test_no_program_is_healthy_pure_and_creates_nothing) ... ok
test_organization_graph_exposes_separation_council_meta_and_architect (__main__.ProgramStudioTest.test_organization_graph_exposes_separation_council_meta_and_architect) ... ok
test_program_authoring_leads_with_scope_and_keeps_save_pure (__main__.ProgramStudioTest.test_program_authoring_leads_with_scope_and_keeps_save_pure) ... ok
test_studio_projects_portable_ports_fallbacks_and_safe_local_fingerprints (__main__.ProgramStudioTest.test_studio_projects_portable_ports_fallbacks_and_safe_local_fingerprints) ... ok
test_workflow_graph_uses_shared_compiler_and_round_trips_losslessly (__main__.ProgramStudioTest.test_workflow_graph_uses_shared_compiler_and_round_trips_losslessly) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.294s

OK
product-language-contract: ok (10 concepts, 18 surfaces, 18 reserved terms, 10 fixtures)
usability-journey-contract: ok (13 journeys, 15 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.y9glMS/repo
dw-workbench: http://127.0.0.1:18038/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.y9glMS/installed
dw-workbench: http://127.0.0.1:18039/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.y9glMS/repo
dw-workbench: http://127.0.0.1:18038/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.ZQq8pK/repo
dw-workbench: http://127.0.0.1:22397/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
workbench-ui-smoke.sh: ok (68 viewport renders: 26 data views + delivery setup/review + program planning/active/certified/revoked + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.ZQq8pK/dw-program-test.x4udsaiv/repo
dw-workbench: http://127.0.0.1:24674/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
docs-lint: ok (466 markdown files)
docs-lint.sh: ok (0s)
ok: CONTRIBUTING.md snippet 'contributor-setup' ran as printed
ok: CONTRIBUTING.md snippet 'contributor-gated-commit' ran as printed
ok: pmo-roadmap/README.md snippet 'install' ran as printed
ok: pmo-roadmap/README.md snippet 'update' ran as printed
ok: pmo-roadmap/README.md snippet 'new-project' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-three-step' ran as printed
ok: pmo-roadmap/README.md snippet 'intake-no-prompt' ran as printed
ok: pmo-roadmap/README.md snippet 'adopt-close-loop' ran as printed
docs-lint snippets: ok
docs-snippet-smoke.sh: ok
canon-lint.sh: ok
dw check: ok
dw rider docs: all rendered surfaces match canon
update.sh: up to date (vendored rails match source v1.14.0)
```
