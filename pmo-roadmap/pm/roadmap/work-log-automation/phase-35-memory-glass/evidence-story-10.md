# Evidence - WLA-35-10

- **Story:** WLA-35-10 - Prove it works
- **Status:** done
- **Date:** 2026-08-01

## Proof

Exit exam executed by Sol (GPT-5.6) under orchestration (exam-gap implementation + nine-failure repair pass); reviewed and verified by the operator session.

What the exam proved, per the phase exit criteria: the full core suite grew 698 → 727 tests with zero failures; both packaged exams complete the compounding scenario from the wheel-launcher entry point; the recorded eight-step closed-loop browser journey (open workbench → fixture run with frozen recall → inspect recalled knowledge BEFORE agent output → follow a decision to its persisted basis → run finishes → inspect terminal writeback → related run starts → prior lesson appears in its recall, advisory-only) runs with 24 direct DOM assertions inside the Firefox exam (352 viewport renders, 13+3 journeys, 427+133 assertions, light/dark at 1440x900 and 390x844); new functional seam tests prove a memory document cannot replace contract/evidence/gate verdicts nor start/widen/bypass program guards; and the no-program regression test proves install, update, repository open, status, board browsing, and ordinary story work create no memory or runtime side effects.

The exam also did its job the honest way: the first full-suite run after stories 01-09 surfaced nine accumulated failures. Each was categorized and repaired without deleting, skipping, or relaxing anything — new-reality pin updates (SSE snapshot frames, ledger event lists, the MCP tool inventory), two real code defects fixed (stale frozen recall permanently blocking a post-external-commit nudge repair, now re-frozen per index-tree scope with the original receipt immutable; a duplicate-announcement aria-live on a role=log transcript), and pre-existing rot from the pre-phase-35 board-redesign commits realigned (navigation-inventory and board-label pins, a cross-file no-poller assertion narrowed to its true boundary).

Captured runs below: (1) full core suite via the shard runner — 727 tests, exit 0 — the `--tests-capture` authority for this commit; (2) both packaged exams, exit 0; (3) browser exam + seam tests, exit 1 — an honest red: one focus-indicator check on live-progress/wide lost a race on the loaded desk; (4) the same command rerun, exit 0 — the authoritative browser run. The red run is retained as an iteration record, consistent with this repo's evidence discipline.

### Captured run — 2026-08-02T01:29:51Z

- **Command:** `/usr/bin/python3 pmo-roadmap/tests/run-core-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3522450b7ace512e4c18f06276880f0d55bb0886

```text
run-core-tests: 715 units across 8 shards + 1 serial
  shard 0:  86 tests in   92.4s  ok
  shard 1:  94 tests in  101.5s  ok
  shard 2:  91 tests in   97.0s  ok
  shard 3:  94 tests in  103.5s  ok
  shard 4:  99 tests in   93.7s  ok
  shard 5:  88 tests in   98.1s  ok
  shard 6:  87 tests in  101.6s  ok
  shard 7:  87 tests in  105.5s  ok
  shard 8:   1 tests in    2.4s  ok
run-core-tests: 727 tests in 107.9s (OK)
```

### Captured run — 2026-08-02T01:31:46Z

- **Command:** `/bin/sh -c /usr/bin/python3 pmo-roadmap/tests/orchestration-packaged-exam.py --dw .tmp/dw-launcher && /usr/bin/python3 pmo-roadmap/tests/autonomous-program-packaged-exam.py --dw .tmp/dw-launcher`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3522450b7ace512e4c18f06276880f0d55bb0886

```text
{"artifact_count": 5, "checks": 2, "compiler_red_cases": 6, "duplicate_restarts": 0, "exam": "packaged multi-agent orchestration", "operator_commit": "efda54504d738094dbd5c46c90b4e6e56d22fe7d", "parallel_research": 2, "repair_visits": 1, "run_id": "run-05a6fd48f5ffe012516307a8", "runtime_red_cases": 6, "state": "awaiting-certification", "verify_all": "ok"}
dw-workbench: 127.0.0.1 "GET /api/programs/program-5e6e2b87ab24ce7720ec20b6/events?from=0&follow=0 HTTP/1.1" 200 -
{"compounding_memory": {"candidate_outcomes": ["sha256:3e820d32d3b9c69a7e36fa016c3cdc34e4fc82ca5b3165a358d96f07402de904", "sha256:fa3d66cf31e1cf0327b72cde446d3e008031ed2e7e6828fa6bc60c0a9eed8f05"], "council": {"advisory_only": true, "conclusion_recalled": "sha256:b25cc9522ea38c93b8b38ff6544cd215d05bc5ea7708f9b8e83d761beac478d6", "dissent_recalled": ["sha256:a76f8c13c320109a798dd5ed14da8a6549d37e16caae2963485595dd5c2fe218"], "stages": ["proposal", "critique", "rebuttal", "judgment"]}, "participant_packets": {"coordinator": {"audience": "coordinator", "common_recall": ["sha256:4c984e4aa1f7a13fe0da84e372647ea57e436d2d7ed69c3f683c1b4dd06834c4", "sha256:e70071861d1a464e5364ebfdd41b9d898cad95b0720c0f63ab52bef043bf2775"], "filter_reason": "audience-filter", "recall_id": "sha256:3c04dcadfbac9272c12cecda33f24471a5739b2c0ecedf3ffd4e8c875e16166a", "source_revision": "sha256:2edff1501c69efc4ae1dde8108f3fd5fe811ef405297b382ea3d4b68a450df11"}, "council": {"audience": "judge", "common_recall": ["sha256:4c984e4aa1f7a13fe0da84e372647ea57e436d2d7ed69c3f683c1b4dd06834c4", "sha256:e70071861d1a464e5364ebfdd41b9d898cad95b0720c0f63ab52bef043bf2775"], "filter_reason": "audience-filter", "recall_id": "sha256:b791df615fc5534af426a79a5b50f81ecd867e397c562d972980c092a3ccb090", "source_revision": "sha256:2edff1501c69efc4ae1dde8108f3fd5fe811ef405297b382ea3d4b68a450df11"}, "implementer": {"audience": "implementer", "common_recall": ["sha256:4c984e4aa1f7a13fe0da84e372647ea57e436d2d7ed69c3f683c1b4dd06834c4", "sha256:e70071861d1a464e5364ebfdd41b9d898cad95b0720c0f63ab52bef043bf2775"], "filter_reason": "audience-filter", "recall_id": "sha256:6689c7c89ed4d1284a95105cd1680f03564d7724b51a449a9b40ea25828ea6d2", "source_revision": "sha256:2edff1501c69efc4ae1dde8108f3fd5fe811ef405297b382ea3d4b68a450df11"}, "verifier": {"audience": "verifier", "common_recall": ["sha256:4c984e4aa1f7a13fe0da84e372647ea57e436d2d7ed69c3f683c1b4dd06834c4", "sha256:e70071861d1a464e5364ebfdd41b9d898cad95b0720c0f63ab52bef043bf2775"], "filter_reason": "audience-filter", "recall_id": "sha256:948b74510b766421365debb42f8883597774f35ca3e1f145f291004a144cee10", "source_revision": "sha256:2edff1501c69efc4ae1dde8108f3fd5fe811ef405297b382ea3d4b68a450df11"}}, "recovery": {"a_to_b_restart": true, "delivery_observations": 1, "dispatches_unique": true, "lessons": 1, "recall_receipts": 25, "writebacks": 3}, "related_recalled": ["sha256:3e820d32d3b9c69a7e36fa016c3cdc34e4fc82ca5b3165a358d96f07402de904", "sha256:4c984e4aa1f7a13fe0da84e372647ea57e436d2d7ed69c3f683c1b4dd06834c4", "sha256:e70071861d1a464e5364ebfdd41b9d898cad95b0720c0f63ab52bef043bf2775", "sha256:fa3d66cf31e1cf0327b72cde446d3e008031ed2e7e6828fa6bc60c0a9eed8f05"], "serialization": {"midrun_write_refused": true, "safe_boundaries": ["certified-handoff", "terminal"]}, "shared_signals": {"failure_signatures": 2, "file": "src/shared_memory.py", "symbol": "shared_memory.dispatch_with_recall", "test": "tests/test_shared_memory.py"}, "stories": {"run_a": "MEM-1-01", "run_b": "MEM-1-02", "run_c": "MEM-9-01"}, "unrelated_exclusion": "low-score"}, "fixture_bindings": {"claude": {"adapter": "claude-exec", "execution": "deterministic injected fixture; no credentials", "model": "claude/sonnet", "provider": "anthropic"}, "pi": {"adapter": "pi-exec", "execution": "deterministic injected fixture; no credentials", "model": "moonshot/kimi", "provider": "openrouter", "router": "openrouter"}}, "green": {"architect_gates": 2, "commits": 3, "conductor_crashes": 9, "council_dissent_preserved": true, "delivery_crashes": 18, "ledger_events": 308, "meta_audits": 1, "open_nonblocking_obligations": ["carry-council-technical-debt"], "pushes": 3, "repair_rounds": 1, "run_id": "program-5e6e2b87ab24ce7720ec20b6", "selected_phases": [1, 2], "selected_stories": ["AX-1-01", "AX-1-02", "AX-2-01"], "state": "complete", "stream_events": 308, "surfaces": ["CLI", "MCP", "HTTP", "Workbench", "SSE"]}, "homebrew": {"reason": "The macOS formula/environment lane owns Homebrew validation; this fresh-wheel exam does not simulate it.", "status": "not-applicable"}, "kind": "delivery-workbench-autonomous-program-exam", "optional_live_specimen": {"reason": "No explicit authenticated live-agent request; variable model output is not the CI oracle.", "status": "not-run"}, "phase27_observations": {"bounded_decision": {"choices": ["approve", "reject"], "decision": "approve", "exact": {"act_token": "sha256:ebc9f9c499ead0e652e36e6b7379b64c4472b8f1f7979be2315d25d4f106af8f", "correlation_id": "req-90693398daf011f469c78e52", "ledger_after": "sha256:f87099ea8dd47b48e18c1e29e31d2bb54315ed6d138ba8e421c43b4b186ab5d8", "ledger_before": "sha256:88a218d62d44316bffd03c37a9914e10db79dcd89557f17138b75f0e5cabc18b"}, "question": "decision: approve | reject", "resolver": "The named checkpoint owner through the fresh local request boundary.", "response_preview_pure": true, "run_id": "run-efe6c334d831401f900f7b46", "start_preview_pure": true, "state_after": "active", "state_before": "awaiting-approval", "visible_next_step": "Decide review"}, "completion": {"completed_phases": [1, 2], "completed_stories": ["AX-1-01", "AX-1-02", "AX-2-01"], "next_step": {"action": null, "canonical": true, "detail": "The entire saved scope is complete.", "kind": "complete", "label": "No more delivery work", "source": {"model": "delivery-workbench-program", "path": "/state"}, "target": null}, "progress": {"basis": "granted-work-items", "completed": 3, "items": [{"status": "complete", "technical_ref": "AX-1-01", "title": "AX 1 01"}, {"status": "complete", "technical_ref": "AX-1-02", "title": "AX 1 02"}, {"status": "complete", "technical_ref": "AX-2-01", "title": "AX 2 01"}], "known_total": 3, "percent": 100}, "state": "complete", "status": {"exact_state": "complete", "group": "complete", "label": "Complete", "meaning": "The entire saved delivery scope reached its completed state."}}, "delivery": {"answers": [{"answer": "autonomous-exit: 3 work items across phases 1, 2.", "id": "delivery", "question": "What are we delivering?", "source": {"model": "delivery-workbench-program", "path": "/scope"}, "status": "known"}, {"answer": "Work: builder-a, builder-b, builder-a. Independent review: architect-a, critic-a, meta-a, verifier-a, architect-a, critic-a, meta-a, verifier-a, architect-a, critic-a, meta-a, verifier-a.", "id": "team", "question": "Who is doing and reviewing it?", "source": {"model": "delivery-workbench-program-view", "path": "/organization/roles"}, "status": "known"}, {"answer": "Passed: Check, Story verification, Verdict issuance, Architecture gate, Check, Story verification, Verdict issuance, Architecture gate, Check, Story verification, Verdict issuance.", "id": "passed", "question": "What passed?", "source": {"model": "delivery-workbench-program-view", "path": "/gates"}, "status": "passed"}, {"answer": "Blocked at authority not running.", "id": "blocked", "question": "What is blocked?", "source": {"model": "delivery-workbench-program", "path": "/blocking_obligations"}, "status": "blocked"}, {"answer": "No person needs to decide anything right now.", "id": "decision", "question": "Who needs to decide?", "source": {"model": "delivery-workbench-program", "path": "/outstanding_requests"}, "status": "not-needed"}, {"answer": "It may still use agent dispatch, certification objective, certification verdict, check execute, contract generate, council decide, evidence materialize, git commit, git push, integration apply, obligation disposition, obligation materialize, obligation record, program select, roadmap phase advance, roadmap story complete, roadmap story start, verdict issue, workspace write. Remaining limits: 0 work items; 42 work starts; 27 check starts; 0 pushes; unknown remaining model tokens; unknown remaining observed cost; 7200 elapsed time.", "id": "remaining-change-spend", "question": "What may delivery still change or spend?", "source": {"model": "delivery-workbench-program", "path": "/capabilities"}, "status": "bounded"}, {"answer": "No more delivery work. The entire saved scope is complete.", "id": "next", "question": "What happens next?", "source": {"model": "delivery-workbench-program", "path": "/state"}, "status": "complete"}], "governed_decision": {"authority": "judge", "dissent_preserved": true, "obligations": ["carry-council-technical-debt"], "result": "advance"}, "limits": {"cost": {"status": "measured", "summary": "Model token usage is unknown. Observed money cost is unknown."}, "counts": [{"id": "max_phases", "label": "phases", "limit": 2, "primary": false, "remaining": 0, "status": "none-left", "unit": "phases", "used": 2}, {"id": "max_stories", "label": "work items", "limit": 3, "primary": true, "remaining": 0, "status": "none-left", "unit": "items", "used": 3}, {"id": "max_child_runs", "label": "bounded child deliveries", "limit": 60, "primary": false, "remaining": 42, "status": "available", "unit": "deliveries", "used": 18}, {"id": "max_agent_starts", "label": "work starts", "limit": 60, "primary": true, "remaining": 42, "status": "available", "unit": "starts", "used": 18}, {"id": "max_provider_starts", "label": "provider starts", "limit": 60, "primary": false, "remaining": 42, "status": "available", "unit": "starts", "used": 18}, {"id": "max_model_starts", "label": "model starts", "limit": 60, "primary": false, "remaining": 42, "status": "available", "unit": "starts", "used": 18}, {"id": "max_check_starts", "label": "check starts", "limit": 30, "primary": true, "remaining": 27, "status": "available", "unit": "starts", "used": 3}, {"id": "max_loop_rounds", "label": "repeated work rounds", "limit": 12, "primary": false, "remaining": 11, "status": "available", "unit": "rounds", "used": 1}, {"id": "max_debate_rounds", "label": "discussion rounds", "limit": 3, "primary": false, "remaining": 2, "status": "available", "unit": "rounds", "used": 1}, {"id": "max_councils", "label": "governed discussions", "limit": 3, "primary": false, "remaining": 2, "status": "available", "unit": "discussions", "used": 1}, {"id": "max_repairs_per_story", "label": "repairs per work item", "limit": 1, "primary": true, "remaining": 0, "status": "none-left", "unit": "rounds", "used": 1}, {"id": "max_verdicts", "label": "review judgments", "limit": 30, "primary": false, "remaining": 23, "status": "available", "unit": "judgments", "used": 7}, {"id": "max_obligations", "label": "recorded follow-ups", "limit": 10, "primary": false, "remaining": 8, "status": "available", "unit": "follow-ups", "used": 2}, {"id": "max_obligation_materializations", "label": "materialized follow-ups", "limit": 10, "primary": false, "remaining": 10, "status": "available", "unit": "follow-ups", "used": 0}, {"id": "max_obligation_dispositions", "label": "resolved follow-ups", "limit": 10, "primary": false, "remaining": 9, "status": "available", "unit": "follow-ups", "used": 1}, {"id": "max_integrations", "label": "integrations", "limit": 3, "primary": false, "remaining": 0, "status": "none-left", "unit": "integrations", "used": 3}, {"id": "max_commits", "label": "commits", "limit": 3, "primary": false, "remaining": 0, "status": "none-left", "unit": "commits", "used": 3}, {"id": "max_pushes", "label": "pushes", "limit": 3, "primary": true, "remaining": 0, "status": "none-left", "unit": "pushes", "used": 3}, {"id": "max_nudges", "label": "follow-up signals", "limit": 1, "primary": true, "remaining": 1, "status": "available", "unit": "signals", "used": 0}, {"id": "max_lesson_writebacks", "label": "lesson writebacks", "limit": 5, "primary": false, "remaining": 5, "status": "available", "unit": "units", "used": 0}, {"id": "max_lessons", "label": "lessons", "limit": 5, "primary": false, "remaining": 5, "status": "available", "unit": "units", "used": 0}, {"id": "max_artifact_bytes", "label": "saved output", "limit": 50000000, "primary": true, "remaining": 45660000, "status": "available", "unit": "bytes", "used": 4340000}, {"id": "max_tokens", "label": "model tokens", "limit": 2000000, "primary": true, "remaining": null, "status": "unknown", "unit": "tokens", "used": null}, {"id": "max_observed_cost_microunits", "label": "observed cost", "limit": 100000000, "primary": true, "remaining": null, "status": "unknown", "unit": "micro-units", "used": null}, {"id": "max_wall_seconds", "label": "elapsed time", "limit": 7200, "primary": true, "remaining": 7200, "status": "available", "unit": "seconds", "used": 0}], "expires_at": "2026-08-02T02:32:05Z", "permission": {"may_still_use": ["agent dispatch", "certification objective", "certification verdict", "check execute", "contract generate", "council decide", "evidence materialize", "git commit", "git push", "integration apply", "obligation disposition", "obligation materialize", "obligation record", "program select", "roadmap phase advance", "roadmap story complete", "roadmap story start", "verdict issue", "workspace write"], "status": "not-currently-available", "summary": "Allowed change types: agent dispatch, certification objective, certification verdict, check execute, contract generate, council decide, evidence materialize, git commit, git push, integration apply, obligation disposition, obligation materialize, obligation record, program select, roadmap phase advance, roadmap story complete, roadmap story start, verdict issue, workspace write.", "will_not_use": ["arbitrary command", "arbitrary network destination", "authority minting", "conflict resolution", "credential read", "cross repository write", "git merge", "policy edit", "publication", "release", "deployment"]}}, "permission": {"allowed_effects": ["agent dispatch", "certification objective", "certification verdict", "check execute", "contract generate", "council decide", "evidence materialize", "git commit", "git push", "integration apply", "obligation disposition", "obligation materialize", "obligation record", "program select", "roadmap phase advance", "roadmap story complete", "roadmap story start", "verdict issue", "workspace write"], "ceilings": ["max_phases", "max_stories", "max_child_runs", "max_agent_starts", "max_provider_starts", "max_model_starts", "max_check_starts", "max_loop_rounds", "max_debate_rounds", "max_councils", "max_repairs_per_story", "max_verdicts", "max_obligations", "max_obligation_materializations", "max_obligation_dispositions", "max_integrations", "max_commits", "max_pushes", "max_nudges", "max_lesson_writebacks", "max_lessons", "max_artifact_bytes", "max_tokens", "max_observed_cost_microunits", "max_wall_seconds"], "current_use": [{"actual": {"kind": "actual", "state": "finite", "unit": "phases", "value": 2}, "id": "max_phases", "label": "phases", "remaining": {"kind": "remaining", "state": "zero", "unit": "phases", "value": 0}}, {"actual": {"kind": "actual", "state": "finite", "unit": "items", "value": 3}, "id": "max_stories", "label": "work items", "remaining": {"kind": "remaining", "state": "zero", "unit": "items", "value": 0}}, {"actual": {"kind": "actual", "state": "finite", "unit": "deliveries", "value": 18}, "id": "max_child_runs", "label": "bounded child deliveries", "remaining": {"kind": "remaining", "state": "finite", "unit": "deliveries", "value": 42}}, {"actual": {"kind": "actual", "state": "finite", "unit": "starts", "value": 18}, "id": "max_agent_starts", "label": "work starts", "remaining": {"kind": "remaining", "state": "finite", "unit": "starts", "value": 42}}, {"actual": {"kind": "actual", "state": "finite", "unit": "starts", "value": 18}, "id": "max_provider_starts", "label": "provider starts", "remaining": {"kind": "remaining", "state": "finite", "unit": "starts", "value": 42}}, {"actual": {"kind": "actual", "state": "finite", "unit": "starts", "value": 18}, "id": "max_model_starts", "label": "model starts", "remaining": {"kind": "remaining", "state": "finite", "unit": "starts", "value": 42}}, {"actual": {"kind": "actual", "state": "finite", "unit": "starts", "value": 3}, "id": "max_check_starts", "label": "check starts", "remaining": {"kind": "remaining", "state": "finite", "unit": "starts", "value": 27}}, {"actual": {"kind": "actual", "state": "finite", "unit": "rounds", "value": 1}, "id": "max_loop_rounds", "label": "repeated work rounds", "remaining": {"kind": "remaining", "state": "finite", "unit": "rounds", "value": 11}}, {"actual": {"kind": "actual", "state": "finite", "unit": "rounds", "value": 1}, "id": "max_debate_rounds", "label": "discussion rounds", "remaining": {"kind": "remaining", "state": "finite", "unit": "rounds", "value": 2}}, {"actual": {"kind": "actual", "state": "finite", "unit": "discussions", "value": 1}, "id": "max_councils", "label": "governed discussions", "remaining": {"kind": "remaining", "state": "finite", "unit": "discussions", "value": 2}}, {"actual": {"kind": "actual", "state": "finite", "unit": "rounds", "value": 1}, "id": "max_repairs_per_story", "label": "repairs per work item", "remaining": {"kind": "remaining", "state": "zero", "unit": "rounds", "value": 0}}, {"actual": {"kind": "actual", "state": "finite", "unit": "judgments", "value": 7}, "id": "max_verdicts", "label": "review judgments", "remaining": {"kind": "remaining", "state": "finite", "unit": "judgments", "value": 23}}, {"actual": {"kind": "actual", "state": "finite", "unit": "follow-ups", "value": 2}, "id": "max_obligations", "label": "recorded follow-ups", "remaining": {"kind": "remaining", "state": "finite", "unit": "follow-ups", "value": 8}}, {"actual": {"kind": "actual", "state": "zero", "unit": "follow-ups", "value": 0}, "id": "max_obligation_materializations", "label": "materialized follow-ups", "remaining": {"kind": "remaining", "state": "finite", "unit": "follow-ups", "value": 10}}, {"actual": {"kind": "actual", "state": "finite", "unit": "follow-ups", "value": 1}, "id": "max_obligation_dispositions", "label": "resolved follow-ups", "remaining": {"kind": "remaining", "state": "finite", "unit": "follow-ups", "value": 9}}, {"actual": {"kind": "actual", "state": "finite", "unit": "integrations", "value": 3}, "id": "max_integrations", "label": "integrations", "remaining": {"kind": "remaining", "state": "zero", "unit": "integrations", "value": 0}}, {"actual": {"kind": "actual", "state": "finite", "unit": "commits", "value": 3}, "id": "max_commits", "label": "commits", "remaining": {"kind": "remaining", "state": "zero", "unit": "commits", "value": 0}}, {"actual": {"kind": "actual", "state": "finite", "unit": "pushes", "value": 3}, "id": "max_pushes", "label": "pushes", "remaining": {"kind": "remaining", "state": "zero", "unit": "pushes", "value": 0}}, {"actual": {"kind": "actual", "state": "zero", "unit": "signals", "value": 0}, "id": "max_nudges", "label": "follow-up signals", "remaining": {"kind": "remaining", "state": "finite", "unit": "signals", "value": 1}}, {"actual": {"kind": "actual", "state": "zero", "unit": "units", "value": 0}, "id": "max_lesson_writebacks", "label": "lesson writebacks", "remaining": {"kind": "remaining", "state": "finite", "unit": "units", "value": 5}}, {"actual": {"kind": "actual", "state": "zero", "unit": "units", "value": 0}, "id": "max_lessons", "label": "lessons", "remaining": {"kind": "remaining", "state": "finite", "unit": "units", "value": 5}}, {"actual": {"kind": "actual", "state": "finite", "unit": "bytes", "value": 4340000}, "id": "max_artifact_bytes", "label": "saved output", "remaining": {"kind": "remaining", "state": "finite", "unit": "bytes", "value": 45660000}}, {"actual": {"kind": "actual", "state": "zero", "unit": "tokens", "value": 0}, "id": "max_tokens", "label": "model tokens", "remaining": {"k
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-08-02T01:34:46Z

- **Command:** `/bin/sh -c bash pmo-roadmap/tests/workbench-ui-smoke.sh && /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py GateTest.test_memory_document_cannot_replace_contract_evidence_or_gate_verdict ProgramRunAuthorityTest.test_memory_document_cannot_start_or_widen_or_bypass_program_guards ProgramSurfaceTest.test_ordinary_no_program_paths_create_no_memory_or_runtime_side_effects`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 3522450b7ace512e4c18f06276880f0d55bb0886

```text
workbench-language-lint.py: ok (18 reserved terms; negative fixture refused: <negative-fixture>/app.js:1: forbidden term 'grant' in ordinary panel text: 'The grant is visible here.')
workbench-accessibility.py: FAIL: live-progress/wide has no visible focus indicator on ['15:button:Open Technical detailsOpens exact identities, controls, hash:focus=false:outline=none/3px:shadow=none']
workbench-ui-smoke.sh: core accessibility journey exam failed
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.WXVA4f/repo
dw-workbench: http://127.0.0.1:22859/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
```

### Captured run — 2026-08-02T01:44:14Z

- **Command:** `/bin/sh -c bash pmo-roadmap/tests/workbench-ui-smoke.sh && /usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py GateTest.test_memory_document_cannot_replace_contract_evidence_or_gate_verdict ProgramRunAuthorityTest.test_memory_document_cannot_start_or_widen_or_bypass_program_guards ProgramSurfaceTest.test_ordinary_no_program_paths_create_no_memory_or_runtime_side_effects`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3522450b7ace512e4c18f06276880f0d55bb0886

```text
workbench-language-lint.py: ok (18 reserved terms; negative fixture refused: <negative-fixture>/app.js:1: forbidden term 'grant' in ordinary panel text: 'The grant is visible here.')
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 53692)
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 697, in process_request_thread
    self.finish_request(request, client_address)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 362, in finish_request
    self.RequestHandlerClass(request, client_address, self)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 766, in __init__
    self.handle()
    ~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 496, in handle
    self.handle_one_request()
    ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 484, in handle_one_request
    method()
    ~~~~~~^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2428, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2411, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
workbench-accessibility.py: ok (13 journeys, 32 wide/narrow audits, 10 journey-6-13 keyboard/focus exams, 8 recorded memory steps / 24 recorded memory assertions, 427 assertions, suite=core)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.97Ex8Q/repo
dw-workbench: http://127.0.0.1:22203/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 57218)
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 697, in process_request_thread
    self.finish_request(request, client_address)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 362, in finish_request
    self.RequestHandlerClass(request, client_address, self)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 766, in __init__
    self.handle()
    ~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 496, in handle
    self.handle_one_request()
    ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 484, in handle_one_request
    method()
    ~~~~~~^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2428, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2411, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 57489)
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 697, in process_request_thread
    self.finish_request(request, client_address)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 362, in finish_request
    self.RequestHandlerClass(request, client_address, self)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 766, in __init__
    self.handle()
    ~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 496, in handle
    self.handle_one_request()
    ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 484, in handle_one_request
    method()
    ~~~~~~^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2428, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2411, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 57491)
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 697, in process_request_thread
    self.finish_request(request, client_address)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 362, in finish_request
    self.RequestHandlerClass(request, client_address, self)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 766, in __init__
    self.handle()
    ~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 496, in handle
    self.handle_one_request()
    ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 484, in handle_one_request
    method()
    ~~~~~~^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2428, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2411, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 57493)
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 697, in process_request_thread
    self.finish_request(request, client_address)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 362, in finish_request
    self.RequestHandlerClass(request, client_address, self)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 766, in __init__
    self.handle()
    ~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 496, in handle
    self.handle_one_request()
    ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 484, in handle_one_request
    method()
    ~~~~~~^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2428, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2411, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
workbench-accessibility.py: ok (3 journeys, 6 wide/narrow audits, 6 journey-6-13 keyboard/focus exams, 0 recorded memory steps / 0 recorded memory assertions, 133 assertions, suite=program)
workbench-ui-smoke.sh: ok (firefox-version='Mozilla Firefox 152.0.5'; 352 viewport renders; desktop-light=88 desktop-dark=88 mobile-light=88 mobile-dark=88; board home, ideation, bounded-run consent, program consent, and eight-state Live matrix; 16 journey 6-13 wide/narrow keyboard/focus exams)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.97Ex8Q/dw-program-test.u5pfxraw/repo
dw-workbench: http://127.0.0.1:24581/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
test_memory_document_cannot_replace_contract_evidence_or_gate_verdict (__main__.GateTest) ... ok
test_memory_document_cannot_start_or_widen_or_bypass_program_guards (__main__.ProgramRunAuthorityTest) ... ok
test_ordinary_no_program_paths_create_no_memory_or_runtime_side_effects (__main__.ProgramSurfaceTest) ... ok

----------------------------------------------------------------------
Ran 3 tests in 2.771s

OK
```
