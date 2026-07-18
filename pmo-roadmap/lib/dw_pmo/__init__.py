"""Delivery Workbench PMO core.

Deterministic parser, validator, trace, and mutation primitives over the
Markdown roadmap under ``pm/roadmap/**``. This package is the single
source of behavior for ``bin/dw`` and any future adapter (workbench
server, gate engine). Markdown stays authoritative: nothing here caches
state outside the roadmap tree.
"""

from __future__ import annotations

from .model import (
    CUT_STATUSES,
    DONE_STATUSES,
    HOLD_STATUSES,
    OPEN_STATUSES,
    PARKED_STATUSES,
    PHASE_RE,
    STORY_ID_RE,
    STORY_RE,
    DwError,
    Phase,
    Project,
    StoryRow,
    die,
    normalize_status,
    status_note,
)
from .paths import (
    ensure_under,
    find_root,
    read_text,
    rel,
    roadmap_dir,
    slugify,
    strip_code,
    template_dir,
    work_log_root,
    write_text,
)
from .parse import (
    current_phase_status_path,
    discover_phases,
    discover_projects,
    find_story,
    get_phase,
    get_project,
    header_status,
    hook_snapshot,
    infer_prefix,
    link_target,
    parse_current_phase_target,
    parse_story_rows,
    phase_header_status,
    phase_is_paused,
    split_table_row,
    story_num_from_file,
    story_title,
    supplemental_canon,
)
from .trace import parse_work_log_entry, recent_commits, work_log_entries
from .render import (
    evidence_link_for,
    render_evidence,
    render_final_summary,
    render_phase_template,
    render_story_template,
    replace_phase_index_content,
    replace_story_table_content,
    update_phase_index_status_content,
    update_story_header_status_content,
    update_story_table_row_content,
)
from .validate import check_project, project_warnings
from .mutations import (
    FileChange,
    MutationPlan,
    apply_plan,
    plan_fingerprint,
    plan_phase_close,
    plan_phase_create,
    plan_phase_pause,
    plan_phase_resume,
    plan_story_create,
    plan_story_evidence,
    plan_story_status,
    preview_plan,
    projected_issues,
    write_changes,
)
from .board import BOARD_COLUMNS, board_bucket, board_model, render_board
from .api import (
    build_context_payload,
    handoff_summary,
    next_story,
    parked_headline,
    parked_lines,
    parked_summary,
    phase_events,
    project_context,
    story_context,
    story_detail,
    story_timeline,
)
from .contract import (
    append_trailers,
    build_contract,
    contract_box_lines,
    contract_digest,
    contract_rule_titles,
    detect_story_ids,
    parse_contract_facts,
    rules_doc_path,
    write_contract,
)
from .evidence import (
    CAPTURE_HEADING_RE,
    TRUNCATION_MARKER,
    find_captured_run,
    latest_passing_capture,
    parse_captured_runs,
    render_capture_block,
    run_capture,
)
from .gate import (
    GateFailure,
    GateResult,
    render_gate_failure,
    render_gate_porcelain,
    run_gate,
)
from .verify import (
    VerifyResult,
    Violation,
    render_verify,
    render_verify_porcelain,
    run_verify,
)
from .model import EVIDENCE_PLACEHOLDER, STORY_STATUSES
from .validate import classify_issue, classify_warning, evidence_content_issues, health_report, hook_seam_explanations
from .agentdocs import (
    BEGIN_MARKER,
    END_MARKER,
    agent_docs_status,
    canonical_block,
    render_block,
    write_agent_docs,
)
from .doctor import DoctorCheck, render_doctor, run_doctor
from .adopt import AdoptionReport, parse_adoption_report, run_adoption
from .status import (
    STATUS_KIND,
    STATUS_SCHEMA_VERSION,
    build_status,
    render_status,
)
from .step import (
    DEFAULT_STEP_OUTPUT_BYTES,
    STEP_KIND,
    STEP_RESULT_KIND,
    STEP_RESULT_SCHEMA_VERSION,
    STEP_SCHEMA_VERSION,
    StepChild,
    apply_step,
    build_step,
    render_step,
)
from .orchestration import (
    BUILTIN_CHECKS,
    CAPABILITIES,
    COMPILED_SCORE_KIND,
    NODE_TYPES,
    OUTPUT_FORMATS,
    ROLE_PRESETS,
    SCORE_KIND,
    SCORE_SCHEMA_VERSION,
    SIMULATION_KIND,
    TERMINALS,
    VALIDATION_KIND,
    WORKSPACE_MODES,
    OrchestrationValidationError,
    canonical_json,
    compile_score,
    compile_score_path,
    discover_score_paths,
    find_score_path,
    load_score,
    orchestration_dir,
    parse_score_text,
    score_inventory,
    simulate_score,
    validate_score,
)
from .orchestration_edit import (
    SCORE_MUTATION_PREVIEW_KIND,
    SCORE_MUTATION_RESULT_KIND,
    SCORE_MUTATION_SCHEMA_VERSION,
    ScoreMutationPlan,
    apply_score_mutation,
    build_score_mutation_plan,
    score_mutation_preview,
)
from .orchestration_run import (
    MAX_GRANT_SECONDS,
    PERMANENT_EXCLUSIONS,
    RUN_EVENT_KIND,
    RUN_GRANT_KIND,
    RUN_KIND,
    RUN_PLAN_KIND,
    RUN_SCHEMA_VERSION,
    build_run_plan,
    claim_node,
    release_node_claim,
    replay_run,
    run_inventory,
    run_store_dir,
    start_run,
    transition_run,
)

__version__ = "1.14.0"
