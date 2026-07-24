# Evidence - WLA-27-05

- **Story:** WLA-27-05 - Make teams and review rules understandable
- **Status:** done
- **Date:** 2026-07-24

## Shared source-backed view

The new pure
[`team_review.py`](../../../../lib/dw_pmo/team_review.py) projection attaches
`delivery-workbench-team-review@1` to organization documents and mutation
previews in Program Studio. The live program view uses the same builder family
and section order over its exact assigned roster.

Both contexts answer five ordinary questions:

1. who does each kind of work;
2. who reviews it independently;
3. who decides when reviewers disagree;
4. who receives help or an escalation; and
5. who checks reviewers and phase-level design.

The view groups only canonical organization, validation, compilation,
simulation, assignment, Studio authority-preview, round-trip, and program-view
facts. It does not assign a candidate, issue a review or decision, route an
escalation, create permission, or start work.

## Understandable team and review design

Program Studio organization routes now open on **Team & review**, not the
technical graph. Responsibility cards explain purpose, trigger, allowed
outcome, required coverage, first-choice candidates, and backups. Targeted
ordinary controls edit responsibility names and duties, required places,
candidate groups, independent-review and help relationships, work-area access,
finite replacement, escalation, decision-group membership and agreement,
decision ownership, objections, review-audit coverage, and audit outcomes.

Renaming a responsibility carries every same-document reference through
independence, help, judgment, decision-group membership, decision ownership,
review-audit ownership, objection weights, and layout. Unedited fields remain
on the cloned exact source document.

Panels, governed decision groups, preserved disagreement, named decision
owners, review auditors, and architecture reviewers appear only when declared.
Their ordinary descriptions say when they run, how agreement is reached, and
what an outcome may change. Stable IDs, weights, thresholds, packet bounds,
schemas, resource groups, finite discussion bounds, graph fields, and the
lossless source remain under **Technical details**.

## Independence without overclaiming

The design view reports `policy-ready` only when the compiler supplies an exact
witness for different candidate IDs, profiles, and work areas. Display-label
collisions cannot counterfeit that proof. A later assignment upgrades only its
declared implementer/reviewer pair to `runtime-proven`; it cannot upgrade
unrelated specialist constraints.

Runtime proof still requires different candidates, profiles, principal
fingerprints, work areas, and session bindings plus read-only review. Provider
or model diversity is never treated as identity independence. The technical
view keeps provider, model vendor/family/revision/binding, auth-domain
fingerprint, principal fingerprint, capability fingerprint, work area, and
session state distinct. Before assignment it says that no session binding
exists; the live view shows the exact assigned session.

## Correction, refusal, and purity

Organization diagnostics now map to the affected ordinary question. An
independence refusal names the exact conflicting responsibilities, explains
the unsafe behavior, and offers a corrective path; the adjacent technical
record retains source, pointer, code, message, and remediation.

The canonical advanced organization, including decision groups, disagreement,
review auditing, and architecture responsibilities, preserves semantic,
document, and layout identity. An invalid organization preserves its unknown
extension and refuses save. A new organization draft is a valid minimal
implementation/reviewer pair instead of an empty invalid shell.

Every design and live projection reports false for work start, policy and
roadmap writes, run-state writes, permission creation, process/observer start,
notifications, and network effects. Saving still uses Program Studio's
existing one-file, fingerprint-bound preview and confirmation.

## Live reuse and device review

The program control room now leads its team panel with the same five readable
sections, assigned responsibility cards, and runtime independence result.
Exact seats, adapters, providers, models, auth and principal fingerprints,
work areas, sessions, decision authority, and separation facts remain in an
explicit technical disclosure. A potential escalation is described
conditionally and never presented as active without evidence.

The browser harness renders 70 canonical states at 1440x900 and 390x844. The
new captures cover both the ordinary team/review route and its exact technical
route. Manual review confirmed that the five-step rail, current question,
responsibility editor, and pre-save summary remain legible on desktop; at
390px the controls form one column, the step rail scrolls horizontally, and
the technical graph retains its own bounded work area.

The journey inventory now contains sixteen reachable states, including the
ordinary team/review state and its technical inspection state. All thirteen
journeys, six red fixtures, ten product concepts, eighteen surfaces, eighteen
reserved terms, and eleven language fixtures pass their executable contracts.

## Regression and distribution proof

- `python3 pmo-roadmap/tests/dw-core-tests.py` — 484 tests in 809.843
  seconds, `OK`.
- `python3 pmo-roadmap/tests/dw-core-tests.py ProgramStudioTest` — 16 focused
  Program Studio tests, `OK`.
- The focused live surface test proves byte-identical CLI, MCP, HTTP, and SSE
  reuse, runtime separation, exact technical provenance, and no side effects.
- `bash pmo-roadmap/tests/package-smoke.sh` builds and installs the wheel on
  Python 3.9, requires the packaged team-review module and export, then passes
  guided status, deliberate step, bounded orchestration, outward signals, and
  the autonomous multi-phase exam.
- The packaged autonomous exam completes three stories across two phases with
  203 replayed/streamed events, nine conductor and eighteen delivery-boundary
  crash recoveries, three commits/pushes, independent review,
  council/meta/architect proof, one repair round, and the full refusal matrix.
- Its separate vanilla consumer keeps program, run, and notification stores,
  ambient network, background polling, setup writes, and work starts absent.
- Product-language, usability-journey, source/installed HTTP explorer,
  70-viewport browser, docs/snippets/canon, rider-doc, source/vendor,
  syntax, and update-alignment checks pass.

The complete certification command and output are captured below against the
final staged tree.

### Captured run — 2026-07-24T23:01:14Z

- **Command:** `bash -o pipefail -c set -e
python3 pmo-roadmap/tests/dw-core-tests.py ProgramStudioTest ProgramSurfaceTest.test_cli_mcp_http_view_tail_and_sse_are_one_canonical_document
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/usability-journey-contract.py
bash pmo-roadmap/tests/workbench-explorer.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
bash pmo-roadmap/tests/docs-lint.sh
bash pmo-roadmap/tests/docs-snippet-smoke.sh
bash pmo-roadmap/tests/canon-lint.sh
node --check pmo-roadmap/workbench/app.js
python3 -m py_compile pmo-roadmap/lib/dw_pmo/team_review.py pmo-roadmap/lib/dw_pmo/program_studio.py pmo-roadmap/lib/dw_pmo/program_surface.py
cmp pmo-roadmap/lib/dw_pmo/team_review.py .githooks/dw_pmo/team_review.py
cmp pmo-roadmap/workbench/app.js .githooks/workbench/app.js
cmp pmo-roadmap/workbench/style.css .githooks/workbench/style.css
.githooks/dw check work-log-automation
.githooks/dw rider docs --check
bash pmo-roadmap/update.sh . --check
git diff --check
git diff --cached --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ecbc95caf968d10087205f794362eaff00eb54bc

```text
test_authority_preview_separates_requests_and_never_grants (__main__.ProgramStudioTest.test_authority_preview_separates_requests_and_never_grants) ... ok
test_containment_and_http_adapter_share_the_same_model (__main__.ProgramStudioTest.test_containment_and_http_adapter_share_the_same_model) ... ok
test_delivery_authoring_maps_refusals_to_decisions_and_preserves_unknowns (__main__.ProgramStudioTest.test_delivery_authoring_maps_refusals_to_decisions_and_preserves_unknowns) ... ok
test_delivery_authoring_orders_seven_decisions_over_exact_workflow (__main__.ProgramStudioTest.test_delivery_authoring_orders_seven_decisions_over_exact_workflow) ... ok
test_diagnostics_link_exact_graph_node_and_json_pointer (__main__.ProgramStudioTest.test_diagnostics_link_exact_graph_node_and_json_pointer) ... ok
test_guarded_save_is_one_file_stale_safe_and_delete_is_explicit (__main__.ProgramStudioTest.test_guarded_save_is_one_file_stale_safe_and_delete_is_explicit) ... ok
test_invalid_team_names_conflicting_roles_and_refuses_losslessly (__main__.ProgramStudioTest.test_invalid_team_names_conflicting_roles_and_refuses_losslessly) ... ok
test_layout_move_changes_document_not_semantic_hash (__main__.ProgramStudioTest.test_layout_move_changes_document_not_semantic_hash) ... ok
test_new_team_draft_is_a_valid_understandable_independent_pair (__main__.ProgramStudioTest.test_new_team_draft_is_a_valid_understandable_independent_pair) ... ok
test_no_program_is_healthy_pure_and_creates_nothing (__main__.ProgramStudioTest.test_no_program_is_healthy_pure_and_creates_nothing) ... ok
test_organization_graph_exposes_separation_council_meta_and_architect (__main__.ProgramStudioTest.test_organization_graph_exposes_separation_council_meta_and_architect) ... ok
test_program_authoring_leads_with_scope_and_keeps_save_pure (__main__.ProgramStudioTest.test_program_authoring_leads_with_scope_and_keeps_save_pure) ... ok
test_studio_projects_portable_ports_fallbacks_and_safe_local_fingerprints (__main__.ProgramStudioTest.test_studio_projects_portable_ports_fallbacks_and_safe_local_fingerprints) ... ok
test_team_review_answers_five_human_questions_over_advanced_policy (__main__.ProgramStudioTest.test_team_review_answers_five_human_questions_over_advanced_policy) ... ok
test_team_review_upgrades_only_the_runtime_pair_and_compares_exact_ids (__main__.ProgramStudioTest.test_team_review_upgrades_only_the_runtime_pair_and_compares_exact_ids) ... ok
test_workflow_graph_uses_shared_compiler_and_round_trips_losslessly (__main__.ProgramStudioTest.test_workflow_graph_uses_shared_compiler_and_round_trips_losslessly) ... ok
test_cli_mcp_http_view_tail_and_sse_are_one_canonical_document (__main__.ProgramSurfaceTest.test_cli_mcp_http_view_tail_and_sse_are_one_canonical_document) ... dw-workbench: 127.0.0.1 "GET /api/programs/program-c77cea3764b302094f0c9dd8/events?from=0&follow=0 HTTP/1.1" 200 -
ok

----------------------------------------------------------------------
Ran 17 tests in 2.963s

OK
product-language-contract: ok (10 concepts, 18 surfaces, 18 reserved terms, 11 fixtures)
usability-journey-contract: ok (13 journeys, 16 reachable states, 6 red fixtures; baseline 88 steps, 38 decisions, 81 engineering terms, 13 dead ends, 26 context switches)
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.ZNS7o5/repo
dw-workbench: http://127.0.0.1:18358/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.ZNS7o5/installed
dw-workbench: http://127.0.0.1:18359/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.ZNS7o5/repo
dw-workbench: http://127.0.0.1:18358/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.ML6hKo/repo
dw-workbench: http://127.0.0.1:22528/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
workbench-ui-smoke.sh: ok (70 viewport renders: 27 data views + delivery setup/review + program planning/active/certified/revoked + attention + ambiguity, desktop+mobile)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.ML6hKo/dw-program-test.bb1zbeea/repo
dw-workbench: http://127.0.0.1:23932/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require a guarded preview→apply content boundary or an exact step/run/program token; never stages, certifies, or commits
docs-lint: ok (468 markdown files)
docs-lint.sh: ok (1s)
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
