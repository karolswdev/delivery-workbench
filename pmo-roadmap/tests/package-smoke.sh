#!/usr/bin/env bash
# Package smoke (WLA-9-02).
#
# Proves the distribution contract end-to-end: build sdist + wheel,
# install the wheel into an isolated environment (pipx when it works,
# plain venv+pip otherwise — same artifact, same entry point), then
# from OUTSIDE the checkout bootstrap a fixture repo with the packaged
# payload, reach doctor-green there, complete the packaged guided-status and
# deliberate-step exit exams, and prove the defer-to-repo rule (a global dw inside an
# adopted repo runs the vendored copy).
#
# Interpreter health is probed first: a broken pyexpat or venv pip
# (observed on this machine's brew python 3.14) disqualifies a
# candidate; /usr/bin/python3 (3.9, the package floor) is the
# fallback. Override with PMO_PACKAGE_PYTHON.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT="$(cd "$PMO_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pmo-package-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "package-smoke.sh: $1" >&2
  exit 1
}

note() {
  echo "package-smoke.sh: $1"
}

# ── pick a healthy interpreter ─────────────────────────────────────
PY=""
for cand in "${PMO_PACKAGE_PYTHON:-}" python3 /usr/bin/python3; do
  [ -n "$cand" ] || continue
  command -v "$cand" >/dev/null 2>&1 || continue
  probe="$TMP_ROOT/probe-venv"
  rm -rf "$probe"
  if "$cand" -c "import pyexpat" >/dev/null 2>&1 \
    && "$cand" -m venv "$probe" >/dev/null 2>&1 \
    && "$probe/bin/python" -m pip --version >/dev/null 2>&1; then
    PY="$cand"
    break
  fi
  note "skipping unhealthy interpreter: $cand"
done
[ -n "$PY" ] || fail "no interpreter with working venv+pip found (set PMO_PACKAGE_PYTHON)"
note "building with: $PY ($("$PY" --version 2>&1))"

EXPECTED_VERSION="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$PMO_DIR/lib/dw_pmo/__init__.py")"
[ -n "$EXPECTED_VERSION" ] || fail "cannot read dw_pmo.__version__"

# ── build sdist + wheel ────────────────────────────────────────────
BUILD_VENV="$TMP_ROOT/buildenv"
"$PY" -m venv "$BUILD_VENV"
"$BUILD_VENV/bin/python" -m pip install --quiet --upgrade pip build \
  || fail "pip install build failed"
(cd "$ROOT" && "$BUILD_VENV/bin/python" -m build --outdir "$TMP_ROOT/dist") >/dev/null \
  || fail "python -m build failed"
WHEEL="$(ls "$TMP_ROOT"/dist/*.whl)"
SDIST="$(ls "$TMP_ROOT"/dist/*.tar.gz)"
[ -f "$WHEEL" ] || fail "expected a wheel in dist/"
[ -f "$SDIST" ] || fail "expected an sdist in dist/"
note "built $(basename "$WHEEL") and $(basename "$SDIST")"
WHEEL_TREE="$TMP_ROOT/wheel-tree"
"$PY" -m zipfile -e "$WHEEL" "$WHEEL_TREE" \
  || fail "could not inspect the built wheel payload"
PAYLOAD_WORKFLOWS="$WHEEL_TREE/dw_pmo/_payload/templates/workflows"
[ "$(find "$PAYLOAD_WORKFLOWS" -maxdepth 1 -type f -name '*.json' | wc -l | tr -d ' ')" -eq 3 ] \
  || fail "wheel did not ship the three reusable workflow templates"
PAYLOAD_ORGANIZATIONS="$WHEEL_TREE/dw_pmo/_payload/templates/organizations"
[ "$(find "$PAYLOAD_ORGANIZATIONS" -maxdepth 1 -type f -name '*.json' | wc -l | tr -d ' ')" -eq 1 ] \
  || fail "wheel did not ship the optional autonomous organization template"

# ── install the wheel: pipx preferred, venv+pip fallback ───────────
DW=""
if command -v pipx >/dev/null 2>&1; then
  if PIPX_HOME="$TMP_ROOT/pipx" PIPX_BIN_DIR="$TMP_ROOT/bin" \
    pipx install --quiet "$WHEEL" >/dev/null 2>&1; then
    DW="$TMP_ROOT/bin/dw"
    note "installed via pipx"
  else
    note "pipx cannot create environments here; falling back to venv+pip"
  fi
fi
if [ -z "$DW" ]; then
  APP_VENV="$TMP_ROOT/appenv"
  "$PY" -m venv "$APP_VENV"
  "$APP_VENV/bin/python" -m pip install --quiet "$WHEEL" \
    || fail "pip install wheel failed"
  DW="$APP_VENV/bin/dw"
  note "installed via venv+pip"
fi
[ -x "$DW" ] || fail "no dw entry point at $DW"

# ── version truth ──────────────────────────────────────────────────
GOT="$(cd "$TMP_ROOT" && "$DW" --version)"
echo "$GOT" | grep -q "$EXPECTED_VERSION" \
  || fail "dw --version reports '$GOT', expected $EXPECTED_VERSION"

# ── bootstrap a fixture repo from outside the checkout ─────────────
FIXTURE="$TMP_ROOT/fixture"
mkdir -p "$FIXTURE"
git -C "$FIXTURE" init -q -b main
git -C "$FIXTURE" config user.name "Package Smoke"
git -C "$FIXTURE" config user.email "package-smoke@example.test"
(cd "$TMP_ROOT" && "$DW" install "$FIXTURE" --skip-bootstrap) >/dev/null \
  || fail "packaged bootstrap install failed"
[ -f "$FIXTURE/.githooks/dw" ] || fail "install did not vendor .githooks/dw"
[ -f "$FIXTURE/.githooks/dw_pmo/verify.py" ] || fail "vendored dw_pmo incomplete"
[ -f "$FIXTURE/.githooks/dw_pmo/status.py" ] || fail "wheel omitted the status core"
[ -f "$FIXTURE/.githooks/dw_pmo/step.py" ] || fail "wheel omitted the deliberate-step core"
[ -f "$FIXTURE/.githooks/dw_pmo/orchestration.py" ] || fail "wheel omitted the orchestration compiler"
[ -f "$FIXTURE/.githooks/dw_pmo/orchestration_edit.py" ] || fail "wheel omitted the orchestration editor core"
[ -f "$FIXTURE/.githooks/dw_pmo/orchestration_run.py" ] || fail "wheel omitted the orchestration run-authority core"
[ -f "$FIXTURE/.githooks/dw_pmo/orchestration_driver.py" ] || fail "wheel omitted the provider-neutral orchestration driver core"
[ -f "$FIXTURE/.githooks/dw_pmo/orchestration_conductor.py" ] || fail "wheel omitted the deterministic orchestration conductor core"
[ -f "$FIXTURE/.githooks/dw_pmo/orchestration_surface.py" ] || fail "wheel omitted the shared orchestration interop surface"
[ -f "$FIXTURE/.githooks/dw_pmo/programs.py" ] || fail "wheel omitted the pure program compiler/planner"
[ -f "$FIXTURE/.githooks/dw_pmo/program_workflow.py" ] || fail "wheel omitted the finite hierarchical workflow compiler"
[ -f "$FIXTURE/.githooks/dw_pmo/program_organization.py" ] || fail "wheel omitted the pure organization and assignment compiler"
[ -f "$FIXTURE/.githooks/dw_pmo/program_deliberation.py" ] || fail "wheel omitted the replayable deliberation protocol core"
[ -f "$FIXTURE/.githooks/dw_pmo/program_studio.py" ] || fail "wheel omitted the pure Program Studio model/edit core"
[ -f "$FIXTURE/pm/orchestration/research-build-review.json" ] \
  || fail "install did not seed the ordinary orchestration preset"
[ -x "$FIXTURE/.githooks/dw-mcp" ] || fail "install did not vendor .githooks/dw-mcp"
[ -x "$FIXTURE/.githooks/dw-workbench" ] || fail "install did not vendor .githooks/dw-workbench"
[ -f "$FIXTURE/.mcp.json" ] || fail "install did not write the .mcp.json seam"
(cd "$FIXTURE" && ./.githooks/dw doctor) >/dev/null \
  || fail "fixture doctor not green after packaged install"
PYTHONPATH="$FIXTURE/.githooks" "$PY" -c \
  'from dw_pmo import CONDUCTOR_TICK_KIND, DRIVER_CAPABILITY_KIND, PROGRAM_KIND, PROGRAM_ORGANIZATION_KIND, PROGRAM_WORKFLOW_KIND, RUN_ACT_PREVIEW_KIND, RUN_PLAN_KIND, RUN_STREAM_KIND, RUN_SUMMARY_KIND, RUN_VIEW_KIND, SCORE_KIND, STEP_RESULT_KIND, WORK_PACKET_KIND, DriverManager, FixtureDriver, StepChild, apply_run_act, assign_organization_team, build_program_plan, build_run_act_preview, build_run_plan, build_run_view, build_step, build_work_packet, compile_organization, compile_program, compile_score_path, compile_workflow, decide_outstanding_request, maintain_outstanding_requests, organization_inventory, plan_assignment_replacement, program_inventory, read_run_stream, replay_run, run_summary_inventory, schedule_decision, simulate_organization, simulate_program, simulate_workflow, start_run, start_run_by_id, supervise_run, tick_run, validate_organization, validate_program, validate_workflow, workflow_inventory; from dw_pmo.mcpserver import TOOLS; from dw_pmo.workbench import handle_api, handle_mutation; assert callable(build_step); assert callable(build_program_plan) and callable(compile_program) and callable(validate_program) and callable(simulate_program) and callable(program_inventory); assert callable(compile_workflow) and callable(validate_workflow) and callable(simulate_workflow) and callable(workflow_inventory); assert callable(compile_organization) and callable(validate_organization) and callable(simulate_organization) and callable(organization_inventory) and callable(assign_organization_team) and callable(plan_assignment_replacement); assert callable(build_run_plan) and callable(start_run) and callable(replay_run); assert callable(build_work_packet) and DriverManager and FixtureDriver; assert callable(schedule_decision) and callable(tick_run) and callable(supervise_run); assert callable(build_run_act_preview) and callable(apply_run_act) and callable(build_run_view); assert callable(decide_outstanding_request) and callable(maintain_outstanding_requests); assert callable(start_run_by_id) and callable(read_run_stream) and callable(run_summary_inventory); assert CONDUCTOR_TICK_KIND == "delivery-workbench-conductor-tick"; assert DRIVER_CAPABILITY_KIND == "delivery-workbench-driver-capability"; assert PROGRAM_KIND == "delivery-workbench-program"; assert PROGRAM_ORGANIZATION_KIND == "delivery-workbench-organization"; assert PROGRAM_WORKFLOW_KIND == "delivery-workbench-workflow"; assert RUN_ACT_PREVIEW_KIND == "delivery-workbench-run-act-preview"; assert RUN_VIEW_KIND == "delivery-workbench-run-view"; assert RUN_STREAM_KIND == "delivery-workbench-run-stream"; assert RUN_SUMMARY_KIND == "delivery-workbench-run-summary-list"; assert WORK_PACKET_KIND == "delivery-workbench-work-packet"; assert RUN_PLAN_KIND == "delivery-workbench-run-plan"; assert SCORE_KIND == "delivery-workbench-orchestration"; assert STEP_RESULT_KIND == "delivery-workbench-step-result"; assert StepChild(0).started; assert {"dw_status", "dw_step", "dw_step_apply", "dw_run_plan", "dw_run_view", "dw_run_preview", "dw_run_start", "dw_run_tick", "dw_run_pause", "dw_run_resume", "dw_run_revoke", "dw_run_cancel", "dw_run_request", "dw_run_checkpoint", "dw_run_stream"} <= set(TOOLS); assert callable(handle_api) and callable(handle_mutation)' \
  || fail "packaged core and MCP/HTTP adapters do not expose the guided operations"
PYTHONPATH="$FIXTURE/.githooks" "$PY" -c \
  'from dw_pmo import DELIBERATION_PLAN_KIND, claim_next_deliberation, compile_deliberation_plan, record_deliberation_replacement, record_deliberation_submission, replay_deliberation, simulate_deliberation, start_deliberation; assert DELIBERATION_PLAN_KIND == "delivery-workbench-deliberation-plan"; assert all(callable(item) for item in (compile_deliberation_plan, simulate_deliberation, start_deliberation, claim_next_deliberation, record_deliberation_submission, record_deliberation_replacement, replay_deliberation))' \
  || fail "packaged core does not expose the bounded deliberation protocol"
PYTHONPATH="$FIXTURE/.githooks" "$PY" -c \
  'from pathlib import Path; from dw_pmo import STUDIO_KIND, apply_studio_mutation, build_program_studio, build_studio_document, build_studio_graph, build_studio_mutation_plan, graph_config_round_trip, new_studio_document, studio_graph_to_config, studio_mutation_preview; from dw_pmo.workbench import handle_api, handle_mutation; root=Path("'$FIXTURE'"); model=build_program_studio(root); assert STUDIO_KIND == "delivery-workbench-program-studio" and model["empty"] and model["healthy"] and model["ordinary_workbench_ready"] and model["default_route"] == "#/" and not model["starts_work"] and not model["creates_grant"] and not model["background_polling"]; draft=new_studio_document("workflow", "packaged-studio"); rt=graph_config_round_trip(root, "workflow", draft); assert rt["lossless"] and rt["semantic_hash_preserved"] and rt["layout_hash_preserved"]; plan=build_studio_mutation_plan(root, "workflow", "save", "packaged-studio", draft); preview=studio_mutation_preview(plan); assert preview["applicable"] and preview["studio"]["graph"]["nodes"][0]["keyboard"] and not preview["writes_policy"] and not preview["starts_work"] and not preview["creates_grant"]; assert handle_api(root, "/api/program-studio", {})[1]["data"] == model; assert all(callable(item) for item in (apply_studio_mutation, build_studio_document, build_studio_graph, studio_graph_to_config, handle_mutation))' \
  || fail "packaged core does not expose pure optional Program Studio parity"
(cd "$FIXTURE" && ./.githooks/dw orchestration validate research-build-review --json) \
  | grep -q '"valid": true' \
  || fail "packaged orchestration preset did not validate"
(cd "$FIXTURE" && ./.githooks/dw orchestration simulate research-build-review --json) \
  | grep -q '"starts_work": false' \
  || fail "packaged orchestration simulation was not pure"
[ ! -e "$FIXTURE/pm/workflows" ] \
  || fail "packaged install created optional workflow policy without an explicit user act"
[ ! -e "$FIXTURE/pm/organizations" ] \
  || fail "packaged install created optional organization policy without an explicit user act"
[ ! -e "$FIXTURE/pm/programs" ] \
  || fail "packaged install created optional program policy without an explicit user act"
(cd "$FIXTURE" && ./.githooks/dw organization list --json) \
  | grep -q '"healthy": true.*"organizations": \[\].*"starts_work": false' \
  || fail "packaged no-organization inventory was not healthy and pure"
mkdir -p "$FIXTURE/pm/organizations"
cp "$PAYLOAD_ORGANIZATIONS"/*.json "$FIXTURE/pm/organizations/"
(cd "$FIXTURE" && ./.githooks/dw organization validate autonomous-story-cell --json) \
  | grep -q '"valid": true' \
  || fail "packaged autonomous organization template did not validate"
(cd "$FIXTURE" && ./.githooks/dw organization simulate autonomous-story-cell --json) \
  | grep -q '"audit":.*"decision":.*"creates_grant": false.*"starts_work": false.*"writes_run_state": false' \
  || fail "packaged organization simulation was not pure"
(cd "$FIXTURE" && ./.githooks/dw organization --help) \
  | grep -q 'list,validate,simulate' \
  || fail "packaged pure organization CLI is incomplete"
(cd "$FIXTURE" && ./.githooks/dw workflow list --json) \
  | grep -q '"healthy": true.*"starts_work": false.*"workflows": \[\]' \
  || fail "packaged no-workflow inventory was not healthy and pure"
mkdir -p "$FIXTURE/pm/workflows"
cp "$PAYLOAD_WORKFLOWS"/*.json "$FIXTURE/pm/workflows/"
for template in docs-only research-build-verify architect-debate-delivery; do
  (cd "$FIXTURE" && ./.githooks/dw workflow validate "$template" --json) \
    | grep -q '"valid": true' \
    || fail "packaged workflow template did not validate: $template"
done
(cd "$FIXTURE" && ./.githooks/dw workflow simulate architect-debate-delivery --json) \
  | grep -q '"creates_grant": false.*"artifact_max_tokens":.*"verdict_routes":.*"loops":.*"starts_work": false' \
  || fail "packaged hierarchical workflow simulation was not finite and pure"
(cd "$FIXTURE" && ./.githooks/dw workflow --help) \
  | grep -q 'list,validate,simulate' \
  || fail "packaged pure workflow CLI is incomplete"
(cd "$FIXTURE" && ./.githooks/dw program list --json) \
  | grep -q '"healthy": true.*"programs": \[\].*"starts_work": false' \
  || fail "packaged no-program inventory was not healthy and pure"
(cd "$FIXTURE" && ./.githooks/dw program --help) \
  | grep -q 'list,validate,simulate,plan' \
  || fail "packaged pure program CLI is incomplete"
(cd "$FIXTURE" && ./.githooks/dw run --help) | grep -q 'plan,start,list,show,view,preview,pause,resume,revoke,cancel,tick,supervise,checkpoint,request,stream' \
  || fail "packaged run authority CLI is incomplete"
set +e
(cd "$FIXTURE" && ./.githooks/dw status --json) > "$TMP_ROOT/status.json"
STATUS_CODE=$?
set -e
[ "$STATUS_CODE" -eq 1 ] || fail "empty packaged consumer should return attention"
grep -q '"kind": "delivery-workbench-status"' "$TMP_ROOT/status.json" \
  || fail "packaged status CLI did not return the stamped model"

# ── guided status loop ─────────────────────────────────────────────
# Reuse this exact installed wheel entry point. The exam creates its own
# consumer and proves every CLI/MCP/HTTP recommendation through a gated
# evidence-backed commit, so package smoke cannot pass on mere imports.
DW_GUIDED_CLI="$DW" "$SCRIPT_DIR/guided-status-loop.sh" \
  || fail "packaged guided status loop failed"

# The Phase-23 exam consumes the same installed wheel but never reconstructs
# a status action argv: each child crosses a separately reviewed token lease;
# stale/manual/commit attempts start nothing on CLI, MCP, and HTTP.
DW_STEP_CLI="$DW" "$SCRIPT_DIR/deliberate-step-loop.sh" \
  || fail "packaged deliberate-step loop failed"

# Phase-24 exit exam: the same wheel installs a second fresh consumer and
# proves visual-score parity, crash-safe parallel research, typed fan-in,
# isolated implementation, check→repair→recheck, runtime red paths, all four
# interop surfaces, terminal human handoff, and an operator-only gated commit.
"$PY" "$SCRIPT_DIR/orchestration-packaged-exam.py" --dw "$DW" \
  || fail "packaged multi-agent orchestration exam failed"

# Phase-25 exit exam: a third wheel-installed consumer crosses the operator
# push boundary, records outward CI/review facts, wakes bounded repairs under
# standing rules, survives planted crashes and request restarts, and proves
# notification/SSE parity plus every new refusal without mutating its forge.
"$PY" "$SCRIPT_DIR/outward-loop-packaged-exam.py" --dw "$DW" \
  || fail "packaged outward-loop orchestration exam failed"

# ── defer-to-repo rule ─────────────────────────────────────────────
# Replace the vendored CLI with a marker; the global dw run inside the
# repo must produce the marker (i.e. it exec'd the vendored copy).
printf '#!/usr/bin/env python3\nprint("VENDORED-RAILS-SPOKE")\n' > "$FIXTURE/.githooks/dw"
chmod +x "$FIXTURE/.githooks/dw"
OUT="$(cd "$FIXTURE" && "$DW" --version 2>/dev/null)"
echo "$OUT" | grep -q "VENDORED-RAILS-SPOKE" \
  || fail "defer-to-repo rule broken: global dw answered instead of the vendored copy ($OUT)"

# ── global dw still answers outside repos ──────────────────────────
(cd "$TMP_ROOT" && "$DW" --version) | grep -q "$EXPECTED_VERSION" \
  || fail "global dw broken outside repos after defer test"

echo "package-smoke.sh: ok"
