"""Exact, separately authorized delivery rails for Phase-26 programs.

The conductor deliberately stops at ``integration-required``.  This module
turns that certified frontier into one immutable delivery plan and advances it
one claimed effect at a time:

* exact candidate integration;
* canonical evidence and roadmap mutation plans;
* contract generation plus objective/governed certification;
* one gated commit and, when granted, one fast-forward push.

The program-run ledger remains the sole authority.  Files below
``.git/pmo-programs/runs/<run>/delivery`` are immutable intent and receipt
objects used for reconciliation; deleting or editing them cannot mint an act.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Callable

from .contract import (
    CONTRACT_REL,
    apply_contract_certification,
    archive_contract,
    box_title,
    build_contract,
    certify_contract_boxes,
    contract_digest,
    write_contract,
)
from . import repofacts
from .gate import run_gate
from .gitio import head_sha, write_tree
from .model import DwError
from .mutations import (
    FileChange,
    MutationPlan,
    apply_plan,
    plan_fingerprint,
    plan_phase_advance,
    plan_story_create,
    plan_story_evidence,
    plan_story_status,
    preview_plan,
)
from .orchestration import canonical_json
from .orchestration_driver import load_driver_config
from .parse import get_phase, get_project
from .paths import read_text, rel, slugify
from .program_conductor import (
    GREEN_RESULTS,
    _artifact_content,
    _file_lock,
    _load_json,
    _write_json_atomic,
    derive_program_frontier,
    replay_program_conductor,
)
from .program_run import (
    _difference_paths,
    _format_time,
    _load_documents,
    _remote_observation,
    _repository_facts,
    _run_dir,
    _sha,
    _time,
    apply_program_claim,
    apply_program_completion,
    build_program_claim_preview,
    build_program_completion_preview,
    dispose_program_obligation,
    program_freshness_issues,
    replay_program,
)
from .programs import build_program_plan
from .verify import run_verify


PROGRAM_DELIVERY_SCHEMA_VERSION = 1
PROGRAM_DELIVERY_PREVIEW_KIND = "delivery-workbench-program-delivery-preview"
PROGRAM_DELIVERY_PLAN_KIND = "delivery-workbench-program-delivery-plan"
PROGRAM_DELIVERY_RECEIPT_KIND = "delivery-workbench-program-delivery-receipt"
PROGRAM_DELIVERY_FRONTIER_KIND = "delivery-workbench-program-delivery-frontier"
PROGRAM_DELIVERY_TICK_KIND = "delivery-workbench-program-delivery-tick"

MAX_PLAN_BYTES = 20_000_000
MAX_RECEIPT_BYTES = 2_000_000
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40,64}$")
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,511}$")

BoundaryHook = Callable[[str, dict[str, object]], None]

OBJECTIVE_CONTRACT_TITLES = [
    "Evidence, not vibes.",
    "Master docs updated.",
    "Tests ran.",
    "Story → evidence pairing.",
    "One PR per story.",
]
GOVERNED_CONTRACT_TITLES = [
    "Greenfield discipline (if applicable).",
    "No bypasses.",
]

_ACTION_CAPABILITIES = {
    "integration": ("integration", "integration:apply"),
    "evidence": ("evidence", "evidence:materialize"),
    "story-complete": ("story-complete", "roadmap:story-complete"),
    "phase-advance": ("phase-advance", "roadmap:phase-advance"),
    "story-start": ("story-start", "roadmap:story-start"),
    "contract": ("contract", "contract:generate"),
    "certification-objective": (
        "certification-objective",
        "certification:objective",
    ),
    "certification-verdict": (
        "certification-verdict",
        "certification:verdict",
    ),
    "commit": ("commit", "git:commit"),
    "push": ("push", "git:push"),
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DwError(message)


def _boundary(
    hook: BoundaryHook | None,
    name: str,
    detail: dict[str, object],
) -> None:
    if hook is not None:
        hook(name, dict(detail))


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _git(
    root: Path,
    *args: str,
    input_data: bytes | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    input_options: dict[str, object] = (
        {"input": input_data}
        if input_data is not None
        else {"stdin": subprocess.DEVNULL}
    )
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
        **input_options,
    )
    if check and completed.returncode:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise DwError(
            f"Git {' '.join(args[:2])} refused"
            + (f": {detail}" if detail else "")
        )
    return completed


def _git_text(
    root: Path,
    *args: str,
    env: dict[str, str] | None = None,
) -> str:
    return _git(root, *args, env=env).stdout.decode("utf-8", "replace").strip()


def _index_tree(root: Path) -> str:
    value = write_tree(root)
    _require(bool(value), "cannot observe the Git index tree")
    return str(value)


def _head_tree(root: Path, commit: str = "HEAD") -> str:
    value = _git_text(root, "rev-parse", f"{commit}^{{tree}}")
    _require(bool(_COMMIT_RE.fullmatch(value)), "cannot resolve commit tree")
    return value


def _nul_paths(data: bytes) -> list[str]:
    return sorted({
        os.fsdecode(item)
        for item in data.split(b"\0")
        if item
    })


def _staged_paths(root: Path) -> list[str]:
    return _nul_paths(
        _git(root, "diff", "--cached", "--name-only", "-z").stdout
    )


def _unstaged_paths(root: Path) -> list[str]:
    tracked = _nul_paths(_git(root, "diff", "--name-only", "-z").stdout)
    untracked = _nul_paths(
        _git(root, "ls-files", "--others", "--exclude-standard", "-z").stdout
    )
    return sorted(set(tracked + untracked))


def _safe_relative_path(value: str) -> str:
    path = Path(value)
    _require(
        value
        and not path.is_absolute()
        and ".." not in path.parts
        and ".git" not in path.parts
        and "\x00" not in value,
        f"candidate path is unsafe: {value!r}",
    )
    return path.as_posix()


def _temporary_patch_tree(
    root: Path,
    base_commit: str,
    patch: bytes,
) -> tuple[str, list[str]]:
    """Apply a patch to an isolated object/index store and return its tree."""
    object_path = Path(
        _git_text(root, "rev-parse", "--git-path", "objects")
    )
    if not object_path.is_absolute():
        object_path = (root / object_path).resolve()
    with tempfile.TemporaryDirectory(prefix="dw-program-patch.") as raw:
        temporary = Path(raw)
        object_store = temporary / "objects"
        object_store.mkdir()
        index = temporary / "index"
        environment = dict(os.environ)
        environment.update({
            "GIT_INDEX_FILE": str(index),
            "GIT_OBJECT_DIRECTORY": str(object_store),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(object_path),
        })
        _git(root, "read-tree", base_commit, env=environment)
        applied = _git(
            root,
            "apply",
            "--cached",
            "--binary",
            "--whitespace=nowarn",
            "-",
            input_data=patch,
            env=environment,
            check=False,
        )
        if applied.returncode:
            detail = applied.stderr.decode("utf-8", "replace").strip()
            raise DwError(
                "candidate diff does not apply exactly to the bound base"
                + (f": {detail}" if detail else "")
            )
        tree = _git_text(root, "write-tree", env=environment)
        changed = _nul_paths(_git(
            root,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            base_commit,
            tree,
            env=environment,
        ).stdout)
        if changed:
            listing = _git(
                root,
                "ls-tree",
                "-r",
                "-z",
                tree,
                "--",
                *changed,
                env=environment,
            ).stdout
            for entry in listing.split(b"\0"):
                if not entry:
                    continue
                metadata, _separator, _path = entry.partition(b"\t")
                mode = metadata.split(b" ", 1)[0]
                _require(
                    mode not in {b"120000", b"160000"},
                    "candidate diff may not introduce symlinks or gitlinks",
                )
        return tree, changed


def _artifact_declared_paths(artifact: dict[str, object]) -> list[str]:
    declarations = [
        str(item)[len("paths:"):]
        for item in artifact.get("checks", [])
        if isinstance(item, str) and item.startswith("paths:")
    ]
    _require(len(declarations) == 1, "candidate artifact has no exact path receipt")
    raw = declarations[0]
    _require(raw and ",," not in raw, "candidate artifact path receipt is malformed")
    paths = [_safe_relative_path(item) for item in raw.split(",")]
    _require(
        len(paths) == len(set(paths)) and all("," not in item for item in paths),
        "candidate artifact paths are ambiguous",
    )
    return sorted(paths)


def _candidate_proof(
    root: Path,
    run_id: str,
    conductor: dict[str, object],
    *,
    story: str,
) -> dict[str, object]:
    authority = conductor["authority"]
    claims = authority["claims"]  # type: ignore[index]
    order = {
        str(claim["claim_id"]): index
        for index, claim in enumerate(claims)
        if isinstance(claim, dict)
    }
    receipts = [
        item
        for item in conductor["receipts"]  # type: ignore[index]
        if isinstance(item, dict) and item.get("story") == story
    ]
    candidates: list[tuple[int, dict[str, object], dict[str, object]]] = []
    for receipt in receipts:
        if receipt.get("outcome") != "succeeded":
            continue
        for artifact in receipt.get("artifacts", []):
            if (
                isinstance(artifact, dict)
                and artifact.get("artifact_kind") == "git-diff"
            ):
                candidates.append((
                    order.get(str(receipt.get("claim_id")), -1),
                    receipt,
                    artifact,
                ))
    _require(candidates, "certified story has no exact candidate diff")
    highest = max(item[0] for item in candidates)
    latest = [item for item in candidates if item[0] == highest]
    _require(
        len(latest) == 1,
        "certified story has multiple ambiguous latest candidate diffs",
    )
    _candidate_order, candidate_receipt, artifact = latest[0]

    checks = [
        receipt
        for receipt in receipts
        if receipt.get("action_kind") == "check"
    ]
    _require(checks, "objective certification requires a mechanical check receipt")
    _require(
        all(
            receipt.get("outcome") == "succeeded"
            and receipt.get("result") in GREEN_RESULTS
            for receipt in checks
        ),
        "one or more required mechanical checks are not green",
    )
    verdicts = [
        receipt
        for receipt in receipts
        if receipt.get("action_kind") in {"story-verification", "verdict"}
        and receipt.get("outcome") == "succeeded"
        and receipt.get("result") in GREEN_RESULTS
        and isinstance(receipt.get("verdict"), dict)
    ]
    _require(verdicts, "certified story has no fresh independent green verdict")
    verifier = max(
        verdicts,
        key=lambda item: order.get(str(item.get("claim_id")), -1),
    )
    governed = [
        receipt
        for receipt in receipts
        if receipt.get("action_kind") in {
            "story-verification",
            "verdict",
            "meta-verdict-issuance",
            "architect-verdict-issuance",
            "architecture-gate",
            "council-decision",
        }
        and receipt.get("outcome") == "succeeded"
    ]
    receipt_hashes = sorted(
        str(item["receipt_hash"])
        for item in receipts
        if isinstance(item.get("receipt_hash"), str)
    )
    proof = {
        "candidate_receipt_hash": candidate_receipt["receipt_hash"],
        "candidate_artifact": {
            "artifact_id": artifact["artifact_id"],
            "sha256": artifact["sha256"],
            "bytes": artifact["bytes"],
            "checks": artifact["checks"],
        },
        "mechanical_receipt_hashes": sorted(
            str(item["receipt_hash"]) for item in checks
        ),
        "verifier_receipt_hash": verifier["receipt_hash"],
        "verifier": verifier.get("verdict"),
        "governed_receipt_hashes": sorted(
            str(item["receipt_hash"]) for item in governed
        ),
        "all_story_receipt_hashes": receipt_hashes,
    }
    return {
        **proof,
        "proof_hash": _sha(proof),
        "artifact": artifact,
    }


def _evidence_body(
    run_id: str,
    grant_hash: str,
    story: str,
    proof: dict[str, object],
    *,
    observed_at: str,
) -> str:
    checks = "\n".join(
        f"- `{value}`"
        for value in proof["mechanical_receipt_hashes"]  # type: ignore[index]
    )
    governed = "\n".join(
        f"- `{value}`"
        for value in proof["governed_receipt_hashes"]  # type: ignore[index]
    )
    artifact = proof["candidate_artifact"]
    assert isinstance(artifact, dict)
    return (
        "### Autonomous program delivery proof\n\n"
        f"- **Program run:** `{run_id}`\n"
        f"- **Program grant:** `{grant_hash}`\n"
        f"- **Story:** `{story}`\n"
        f"- **Observed:** `{observed_at}`\n"
        f"- **Certified proof:** `{proof['proof_hash']}`\n"
        f"- **Candidate diff:** `{artifact['sha256']}` "
        f"({artifact['bytes']} bytes)\n"
        f"- **Independent verifier receipt:** "
        f"`{proof['verifier_receipt_hash']}`\n\n"
        "#### Mechanical receipts\n\n"
        f"{checks}\n\n"
        "#### Governed receipts\n\n"
        f"{governed}\n\n"
        "The delivery rail revalidated the exact patch, canonical roadmap "
        "mutations, contract, gate, and commit. This evidence records machine "
        "and program provenance; it does not claim a human performed the "
        "attestation."
    )


def _serialize_mutation(
    plan: MutationPlan,
    *,
    before_tree: str,
    after_tree: str,
) -> dict[str, object]:
    rendered = preview_plan(plan)
    return {
        "kind": plan.kind,
        "project": plan.project_slug,
        "fingerprint": plan_fingerprint(plan),
        "before_index_tree": before_tree,
        "after_index_tree": after_tree,
        "create_dirs": [rel(path, plan.root) for path in plan.create_dirs],
        "changes": [
            {
                "path": rel(change.path, plan.root),
                "existed": change.existed,
                "old_content": change.old_content,
                "new_content": change.new_content,
                "old_hash": _sha({"content": change.old_content}),
                "new_hash": _sha({"content": change.new_content}),
            }
            for change in plan.changes
        ],
        "summary": plan.summary,
        "preview": rendered,
    }


def _apply_scratch_mutation(
    scratch: Path,
    plan: MutationPlan,
) -> dict[str, object]:
    before = _index_tree(scratch)
    result = apply_plan(plan, validate_after=True)
    issues = list(result["issues"])
    if plan.kind == "story-evidence":
        issues = [
            item for item in issues
            if "evidence exists but matching story is not done" not in str(item)
        ]
    if (
        plan.kind == "story-status"
        and plan.summary.get("status") == "done"
    ):
        issues = [
            item for item in issues
            if "all stories are done but final-summary.md is missing"
            not in str(item)
        ]
    _require(
        not issues,
        "canonical roadmap mutation would leave an unhealthy project: "
        + "; ".join(str(item) for item in issues),
    )
    paths = [rel(change.path, scratch) for change in plan.changes]
    if paths:
        _git(scratch, "add", "--", *paths)
    after = _index_tree(scratch)
    return _serialize_mutation(
        plan,
        before_tree=before,
        after_tree=after,
    )


def _action(
    sequence: int,
    kind: str,
    *,
    phase: int,
    story: str,
    detail: dict[str, object],
) -> dict[str, object]:
    category, capability = _ACTION_CAPABILITIES[kind]
    unsigned = {
        "action_id": f"{sequence:02d}-{kind}",
        "kind": kind,
        "category": category,
        "capability": capability,
        "phase": phase,
        "story": story,
        "detail": detail,
    }
    return {**unsigned, "subject_hash": _sha(unsigned)}


def _clone_for_preview(root: Path, destination: Path) -> None:
    completed = subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            "--no-local",
            "--no-hardlinks",
            str(root),
            str(destination),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise DwError(
            "cannot create isolated delivery preview: "
            + completed.stderr.decode("utf-8", "replace").strip()
        )


def _preview_unsigned(
    run_id: str,
    *,
    applicable: bool,
    issues: list[dict[str, str]],
    observed_at: str,
    binding: dict[str, object],
    actions: list[dict[str, object]],
    final: dict[str, object],
) -> dict[str, object]:
    return {
        "kind": PROGRAM_DELIVERY_PREVIEW_KIND,
        "schema_version": PROGRAM_DELIVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "applicable": applicable,
        "issues": issues,
        "observed_at": observed_at,
        "binding": binding,
        "actions": actions,
        "final": final,
        "starts_work": False,
        "writes_state": False,
        "mutates_repository": False,
        "mutates_roadmap": False,
        "creates_commit": False,
        "pushes_remote": False,
    }


def build_program_delivery_preview(
    root: Path,
    run_id: str,
    *,
    driver_config: object | None = None,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Build one zero-effect plan over the exact certified story frontier."""
    root = root.resolve()
    observed = _time(now, "now")
    observed_at = _format_time(observed)
    config = load_driver_config(root, driver_config)
    _path, grant, _starting_plan = _load_documents(root, run_id)
    issues: list[dict[str, str]] = []
    try:
        conductor = replay_program_conductor(root, run_id, now=observed)
        authority = conductor["authority"]
    except DwError as exc:
        authority = replay_program(root, run_id, now=observed)
        conductor = {
            "authority": authority,
            "active_conductor_claims": [],
            "receipts": [],
            "receipt_hashes": [],
        }
        issues.append(_issue(
            "proof-stale",
            f"conductor proof cannot be replayed: {exc.message}",
        ))
    try:
        frontier = derive_program_frontier(
            root,
            run_id,
            driver_config=config,
            now=observed,
        )
    except DwError as exc:
        frontier = {
            "state": "stopped",
            "stop": "frontier-invalid",
            "lineage": None,
        }
        issues.append(_issue("frontier-invalid", exc.message))

    lineage = frontier.get("lineage")
    story = (
        str(lineage["story"])
        if isinstance(lineage, dict) and lineage.get("story")
        else ""
    )
    phase = (
        int(lineage["phase"])
        if isinstance(lineage, dict)
        and isinstance(lineage.get("phase"), int)
        else 0
    )
    binding: dict[str, object] = {
        "program": grant["program_selector"],
        "run_id": run_id,
        "grant_hash": grant["grant_hash"],
        "ledger_head": authority["ledger_head"],
        "generation": authority["generation"],
        "conductor_receipt_hashes": conductor["receipt_hashes"],
        "frontier": {
            "state": frontier.get("state"),
            "stop": frontier.get("stop"),
            "lineage": lineage,
        },
        "story": story or None,
        "phase": phase or None,
        "repository": authority["expected_repository"],
        "roadmap": authority["expected_roadmap"],
        "proof": None,
        "candidate": None,
        "remote": {
            "remote": authority["expected_repository"].get("remote"),  # type: ignore[union-attr]
            "remote_ref": authority["expected_repository"].get("remote_ref"),  # type: ignore[union-attr]
            "remote_url_hash": authority["expected_repository"].get("remote_url_hash"),  # type: ignore[union-attr]
            "remote_head": authority["expected_repository"].get("remote_head"),  # type: ignore[union-attr]
            "fast_forward_observed": authority["expected_repository"].get("fast_forward_observed"),  # type: ignore[union-attr]
        },
    }
    if authority["state"] != "running":
        issues.append(_issue(
            "grant-inactive",
            f"program authority is {authority['state']}, not running",
        ))
    if conductor["active_conductor_claims"]:
        issues.append(_issue(
            "conductor-claim-active",
            "conductor has an unresolved claim",
        ))
    if (
        frontier.get("state") != "story-certified"
        or frontier.get("stop") != "integration-required"
        or not story
        or not phase
    ):
        issues.append(_issue(
            "proof-not-certified",
            "program frontier is not the exact story-certified integration checkpoint",
        ))
    blocking = list(frontier.get("blocking_obligation_ids", []))
    if blocking:
        issues.append(_issue(
            "blocking-obligation-open",
            "blocking obligations prevent story advancement: "
            + ", ".join(str(item) for item in blocking),
        ))
    expected_repository = authority["expected_repository"]
    if (
        not expected_repository.get("clean")
        or expected_repository.get("operation") != "normal"
        or expected_repository.get("head") != head_sha(root)
        or expected_repository.get("index_tree") != _index_tree(root)
        or _unstaged_paths(root)
        or _staged_paths(root)
    ):
        issues.append(_issue(
            "repository-not-clean",
            "delivery requires the exact clean, normal repository granted to the program",
        ))
    ignored = _git(
        root,
        "check-ignore",
        "-q",
        "--",
        CONTRACT_REL,
        check=False,
    )
    if ignored.returncode != 0:
        issues.append(_issue(
            "contract-path-not-ignored",
            f"{CONTRACT_REL} must be ignored before autonomous contract generation",
        ))
    if (root / CONTRACT_REL).exists():
        issues.append(_issue(
            "contract-conflict",
            f"{CONTRACT_REL} already exists",
        ))

    required = {
        "integration:apply",
        "evidence:materialize",
        "roadmap:story-complete",
        "contract:generate",
        "certification:objective",
        "certification:verdict",
        "git:commit",
    }
    capabilities = set(authority["capabilities"])
    missing = sorted(required - capabilities)
    for capability in missing:
        issues.append(_issue(
            "capability-denied",
            f"program grant lacks {capability}",
        ))

    proof: dict[str, object] | None = None
    patch = b""
    candidate_paths: list[str] = []
    patch_tree = ""
    if story and phase and not issues:
        try:
            proof = _candidate_proof(
                root,
                run_id,
                conductor,
                story=story,
            )
            artifact = proof["artifact"]
            assert isinstance(artifact, dict)
            patch = _artifact_content(root, run_id, artifact)
            candidate_paths = _artifact_declared_paths(artifact)
            patch_tree, observed_paths = _temporary_patch_tree(
                root,
                str(expected_repository["head"]),
                patch,
            )
            _require(
                observed_paths == candidate_paths,
                "candidate diff paths differ from its immutable artifact receipt",
            )
            binding["proof"] = {
                key: value
                for key, value in proof.items()
                if key != "artifact"
            }
            binding["candidate"] = {
                "artifact_id": artifact["artifact_id"],
                "sha256": artifact["sha256"],
                "bytes": artifact["bytes"],
                "paths": candidate_paths,
                "base_head": expected_repository["head"],
                "base_tree": _head_tree(root),
                "result_tree": patch_tree,
            }
        except DwError as exc:
            issues.append(_issue("candidate-refused", exc.message))

    actions: list[dict[str, object]] = []
    final: dict[str, object] = {
        "story": story or None,
        "phase": phase or None,
        "next_story": None,
        "next_phase": None,
        "index_tree": None,
        "staged_paths": [],
        "contract_digest": None,
        "commit_subject": None,
        "push_required": "git:push" in capabilities,
    }
    if not issues and proof is not None:
        try:
            with tempfile.TemporaryDirectory(
                prefix="dw-program-delivery-preview."
            ) as raw:
                scratch = Path(raw) / "repo"
                _clone_for_preview(root, scratch)
                scratch = scratch.resolve()
                applied = _git(
                    scratch,
                    "apply",
                    "--index",
                    "--binary",
                    "--whitespace=nowarn",
                    "-",
                    input_data=patch,
                    check=False,
                )
                _require(
                    applied.returncode == 0,
                    "candidate diff failed in the isolated integration preview",
                )
                _require(
                    _index_tree(scratch) == patch_tree,
                    "isolated candidate integration produced a different tree",
                )
                sequence = 1
                actions.append(_action(
                    sequence,
                    "integration",
                    phase=phase,
                    story=story,
                    detail={
                        "base_head": expected_repository["head"],
                        "base_tree": _head_tree(root),
                        "before_index_tree": expected_repository["index_tree"],
                        "after_index_tree": patch_tree,
                        "patch_sha256": "sha256:" + hashlib.sha256(patch).hexdigest(),
                        "patch_bytes": len(patch),
                        "artifact_id": proof["candidate_artifact"]["artifact_id"],  # type: ignore[index]
                        "paths": candidate_paths,
                    },
                ))
                sequence += 1

                project = get_project(
                    scratch,
                    str(authority["expected_roadmap"]["project"]),  # type: ignore[index]
                )
                current_phase = get_phase(project, str(phase))
                evidence = plan_story_evidence(
                    scratch,
                    project,
                    current_phase,
                    story,
                    body=_evidence_body(
                        run_id,
                        str(grant["grant_hash"]),
                        story,
                        proof,
                        observed_at=observed_at,
                    ),
                    evidence_date=observed.date().isoformat(),
                )
                evidence_intent = _apply_scratch_mutation(scratch, evidence)
                actions.append(_action(
                    sequence,
                    "evidence",
                    phase=phase,
                    story=story,
                    detail={"mutation": evidence_intent},
                ))
                evidence_path = str(evidence.summary["evidence_path"])
                sequence += 1

                complete = plan_story_status(
                    scratch,
                    project,
                    current_phase,
                    story,
                    "done",
                )
                complete_intent = _apply_scratch_mutation(scratch, complete)
                actions.append(_action(
                    sequence,
                    "story-complete",
                    phase=phase,
                    story=story,
                    detail={"mutation": complete_intent},
                ))
                sequence += 1

                next_plan = build_program_plan(
                    scratch,
                    str(grant["program_selector"]),
                    driver_config=config,
                )
                next_selection = next_plan.get("selection")
                next_story: str | None = None
                next_phase_number: int | None = None
                if isinstance(next_selection, dict):
                    next_story = str(next_selection["story"])
                    next_phase_number = int(next_selection["phase"])
                else:
                    issue_codes = {
                        str(item.get("code"))
                        for item in next_plan.get("issues", [])
                        if isinstance(item, dict)
                    }
                    _require(
                        issue_codes == {"scope-complete"},
                        "roadmap cannot select the next exact scoped story: "
                        + ", ".join(sorted(issue_codes)),
                    )

                if (
                    next_phase_number is not None
                    and next_phase_number != phase
                ):
                    _require(
                        "roadmap:phase-advance" in capabilities,
                        "program grant lacks roadmap:phase-advance",
                    )
                    next_phase = get_phase(project, str(next_phase_number))
                    phase_plan = plan_phase_advance(
                        scratch,
                        project,
                        current_phase,
                        next_phase,
                        summary_date=observed.date().isoformat(),
                    )
                    phase_intent = _apply_scratch_mutation(
                        scratch,
                        phase_plan,
                    )
                    actions.append(_action(
                        sequence,
                        "phase-advance",
                        phase=phase,
                        story=story,
                        detail={"mutation": phase_intent},
                    ))
                    sequence += 1

                if next_story is not None and next_phase_number is not None:
                    _require(
                        "roadmap:story-start" in capabilities,
                        "program grant lacks roadmap:story-start",
                    )
                    selected_phase = get_phase(
                        project,
                        str(next_phase_number),
                    )
                    start = plan_story_status(
                        scratch,
                        project,
                        selected_phase,
                        next_story,
                        "in-progress",
                    )
                    start_intent = _apply_scratch_mutation(scratch, start)
                    actions.append(_action(
                        sequence,
                        "story-start",
                        phase=next_phase_number,
                        story=next_story,
                        detail={"mutation": start_intent},
                    ))
                    sequence += 1

                final_tree = _index_tree(scratch)
                staged_paths = _staged_paths(scratch)
                final.update({
                    "next_story": next_story,
                    "next_phase": next_phase_number,
                    "index_tree": final_tree,
                    "staged_paths": staged_paths,
                    "evidence_path": evidence_path,
                })
                provenance = {
                    "kind": "delivery-workbench-program-attestation",
                    "schema_version": PROGRAM_DELIVERY_SCHEMA_VERSION,
                    "program": grant["program_selector"],
                    "run_id": run_id,
                    "grant_hash": grant["grant_hash"],
                    "story": story,
                    "phase": phase,
                    "proof_hash": proof["proof_hash"],
                    "candidate_diff_hash": proof["candidate_artifact"]["sha256"],  # type: ignore[index]
                    "mechanical_receipt_hashes": proof["mechanical_receipt_hashes"],
                    "governed_receipt_hashes": proof["governed_receipt_hashes"],
                    "observed_at": observed_at,
                    "human_attestation": False,
                }
                contract_content = build_contract(
                    scratch,
                    [story],
                    consent="no",
                    reasons=[
                        "Autonomous program delivery; no external work-log export.",
                    ],
                    tier="full",
                    generated_at=observed_at,
                    program_provenance=provenance,
                )
                titles = {
                    title
                    for line in contract_content.splitlines()
                    if (title := box_title(line)) is not None
                }
                expected_titles = set(
                    OBJECTIVE_CONTRACT_TITLES
                    + GOVERNED_CONTRACT_TITLES
                )
                _require(
                    titles == expected_titles,
                    "contract assertions lack a complete objective/governed certification map",
                )
                objective_proof = _sha({
                    "kind": "objective-contract-certification",
                    "story": story,
                    "index_tree": final_tree,
                    "evidence_path": evidence_path,
                    "mechanical_receipts": proof["mechanical_receipt_hashes"],
                    "candidate_diff": proof["candidate_artifact"]["sha256"],  # type: ignore[index]
                })
                objective_content = certify_contract_boxes(
                    contract_content,
                    OBJECTIVE_CONTRACT_TITLES,
                    attestor=f"program:{run_id}/objective-certifier",
                    proof_hash=objective_proof,
                )
                governed_proof = _sha({
                    "kind": "governed-contract-certification",
                    "story": story,
                    "proof_hash": proof["proof_hash"],
                    "verifier_receipt": proof["verifier_receipt_hash"],
                    "governed_receipts": proof["governed_receipt_hashes"],
                })
                certified_content = certify_contract_boxes(
                    objective_content,
                    GOVERNED_CONTRACT_TITLES,
                    attestor=(
                        f"program:{run_id}/verdict:"
                        f"{proof['verifier_receipt_hash']}"
                    ),
                    proof_hash=governed_proof,
                )
                actions.append(_action(
                    sequence,
                    "contract",
                    phase=phase,
                    story=story,
                    detail={
                        "content": contract_content,
                        "content_hash": contract_digest(contract_content),
                        "story_ids": [story],
                        "generated_at": observed_at,
                        "provenance": provenance,
                        "expected_index_tree": final_tree,
                    },
                ))
                sequence += 1
                actions.append(_action(
                    sequence,
                    "certification-objective",
                    phase=phase,
                    story=story,
                    detail={
                        "before": contract_content,
                        "after": objective_content,
                        "before_hash": contract_digest(contract_content),
                        "after_hash": contract_digest(objective_content),
                        "titles": OBJECTIVE_CONTRACT_TITLES,
                        "proof_hash": objective_proof,
                        "mechanical_receipt_hashes": proof["mechanical_receipt_hashes"],
                        "evidence_path": evidence_path,
                        "expected_index_tree": final_tree,
                    },
                ))
                sequence += 1
                actions.append(_action(
                    sequence,
                    "certification-verdict",
                    phase=phase,
                    story=story,
                    detail={
                        "before": objective_content,
                        "after": certified_content,
                        "before_hash": contract_digest(objective_content),
                        "after_hash": contract_digest(certified_content),
                        "titles": GOVERNED_CONTRACT_TITLES,
                        "proof_hash": governed_proof,
                        "governed_receipt_hashes": proof["governed_receipt_hashes"],
                        "verifier_receipt_hash": proof["verifier_receipt_hash"],
                        "expected_index_tree": final_tree,
                    },
                ))
                sequence += 1
                digest = contract_digest(certified_content)
                subject = f"Complete {story}: autonomous program delivery"
                message = (
                    f"{subject}\n\n"
                    f"PMO-Story: {story}\n"
                    f"PMO-Contract-Digest: {digest}\n"
                )
                actions.append(_action(
                    sequence,
                    "commit",
                    phase=phase,
                    story=story,
                    detail={
                        "parent": expected_repository["head"],
                        "tree": final_tree,
                        "subject": subject,
                        "message": message,
                        "story_ids": [story],
                        "contract_digest": digest,
                        "contract_content": certified_content,
                        "proof_hash": proof["proof_hash"],
                        "staged_paths": staged_paths,
                    },
                ))
                sequence += 1
                final.update({
                    "contract_digest": digest,
                    "commit_subject": subject,
                })

                if "git:push" in capabilities:
                    remote = expected_repository.get("remote")
                    remote_ref = expected_repository.get("remote_ref")
                    _require(
                        isinstance(remote, str)
                        and isinstance(remote_ref, str),
                        "git:push grant has no exact remote/ref binding",
                    )
                    target_ref = _push_target_ref(remote, remote_ref)
                    _require(
                        expected_repository.get("fast_forward_observed")
                        is True,
                        "push remote was not observed as a fast-forward lease",
                    )
                    actions.append(_action(
                        sequence,
                        "push",
                        phase=phase,
                        story=story,
                        detail={
                            "remote": remote,
                            "remote_ref": remote_ref,
                            "target_ref": target_ref,
                            "remote_url_hash": expected_repository["remote_url_hash"],
                            "expected_remote_head": expected_repository["remote_head"],
                            "commit_from_action": f"{sequence - 1:02d}-commit",
                        },
                    ))
        except DwError as exc:
            issues.append(_issue("delivery-plan-refused", exc.message))
            actions = []

    for index, action in enumerate(actions, start=1):
        _require(
            action["action_id"].startswith(f"{index:02d}-"),
            "delivery action sequence is not contiguous",
        )
        if action["capability"] not in capabilities:
            issues.append(_issue(
                "capability-denied",
                f"program grant lacks {action['capability']}",
            ))

    unsigned = _preview_unsigned(
        run_id,
        applicable=not issues and bool(actions),
        issues=issues,
        observed_at=observed_at,
        binding=binding,
        actions=actions,
        final=final,
    )
    _require(
        len(canonical_json(unsigned).encode("utf-8")) <= MAX_PLAN_BYTES,
        "program delivery preview exceeds its byte ceiling",
    )
    return {**unsigned, "delivery_token": _sha(unsigned)}


def _validate_preview(value: object) -> dict[str, object]:
    _require(isinstance(value, dict), "program delivery preview must be an object")
    preview = dict(value)
    _require(
        preview.get("kind") == PROGRAM_DELIVERY_PREVIEW_KIND
        and preview.get("schema_version") == PROGRAM_DELIVERY_SCHEMA_VERSION,
        "unsupported program delivery preview",
    )
    _require(
        isinstance(preview.get("run_id"), str)
        and isinstance(preview.get("actions"), list)
        and isinstance(preview.get("issues"), list)
        and isinstance(preview.get("binding"), dict)
        and isinstance(preview.get("final"), dict)
        and isinstance(preview.get("applicable"), bool),
        "program delivery preview shape is invalid",
    )
    for effect in (
        "starts_work",
        "writes_state",
        "mutates_repository",
        "mutates_roadmap",
        "creates_commit",
        "pushes_remote",
    ):
        _require(preview.get(effect) is False, f"preview {effect} must be false")
    token = preview.get("delivery_token")
    _require(
        isinstance(token, str) and bool(_HASH_RE.fullmatch(token)),
        "program delivery token is invalid",
    )
    unsigned = {
        key: item
        for key, item in preview.items()
        if key != "delivery_token"
    }
    _require(_sha(unsigned) == token, "program delivery token hash is invalid")
    return preview


def _delivery_base(root: Path, run_id: str) -> Path:
    base = _run_dir(root.resolve(), run_id) / "delivery"
    if base.is_symlink():
        raise DwError("refusing symlinked program delivery store")
    return base


def _delivery_dir(root: Path, run_id: str, delivery_id: str) -> Path:
    _require(
        re.fullmatch(r"delivery-[0-9a-f]{24}", delivery_id) is not None,
        "program delivery id is invalid",
    )
    base = _delivery_base(root, run_id)
    path = base / delivery_id
    _require(path.parent == base, "program delivery path escapes its run")
    return path


def start_program_delivery(
    root: Path,
    preview: object,
    *,
    delivery_token: str,
    driver_config: object | None = None,
) -> dict[str, object]:
    """Persist one exact intent after rebuilding its zero-effect preview."""
    submitted = _validate_preview(preview)
    _require(
        delivery_token == submitted["delivery_token"],
        "delivery token does not match preview",
    )
    _require(submitted["applicable"], "program delivery preview is not applicable")
    root = root.resolve()
    current = build_program_delivery_preview(
        root,
        str(submitted["run_id"]),
        driver_config=driver_config,
        now=str(submitted["observed_at"]),
    )
    _require(
        current == submitted,
        "program delivery preview is stale: "
        + ", ".join(_difference_paths(submitted, current)[:12]),
    )
    delivery_id = "delivery-" + str(delivery_token).split(":", 1)[1][:24]
    directory = _delivery_dir(root, str(submitted["run_id"]), delivery_id)
    plan_unsigned = {
        "kind": PROGRAM_DELIVERY_PLAN_KIND,
        "schema_version": PROGRAM_DELIVERY_SCHEMA_VERSION,
        "run_id": submitted["run_id"],
        "delivery_id": delivery_id,
        "preview": submitted,
        "delivery_token": delivery_token,
    }
    plan = {**plan_unsigned, "plan_hash": _sha(plan_unsigned)}
    _require(
        len(canonical_json(plan).encode("utf-8")) <= MAX_PLAN_BYTES,
        "program delivery plan exceeds its byte ceiling",
    )
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    _write_json_atomic(directory / "plan.json", plan, immutable=True)
    return replay_program_delivery(
        root,
        str(submitted["run_id"]),
        delivery_id,
        now=str(submitted["observed_at"]),
    )


def _load_plan(
    root: Path,
    run_id: str,
    delivery_id: str,
) -> dict[str, object]:
    path = _delivery_dir(root, run_id, delivery_id) / "plan.json"
    plan = _load_json(path, "program delivery plan")
    _require(
        plan.get("kind") == PROGRAM_DELIVERY_PLAN_KIND
        and plan.get("schema_version") == PROGRAM_DELIVERY_SCHEMA_VERSION
        and plan.get("run_id") == run_id
        and plan.get("delivery_id") == delivery_id,
        "program delivery plan identity is invalid",
    )
    unsigned = {key: item for key, item in plan.items() if key != "plan_hash"}
    _require(plan.get("plan_hash") == _sha(unsigned), "program delivery plan hash is invalid")
    _validate_preview(plan.get("preview"))
    return plan


def _receipt_path(
    root: Path,
    run_id: str,
    delivery_id: str,
    receipt_hash: str,
) -> Path:
    _require(bool(_HASH_RE.fullmatch(receipt_hash)), "delivery receipt hash is invalid")
    return (
        _delivery_dir(root, run_id, delivery_id)
        / "receipts"
        / f"{receipt_hash.split(':', 1)[1]}.json"
    )


def _store_receipt(
    root: Path,
    run_id: str,
    delivery_id: str,
    payload: dict[str, object],
) -> dict[str, object]:
    unsigned = {
        "kind": PROGRAM_DELIVERY_RECEIPT_KIND,
        "schema_version": PROGRAM_DELIVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "delivery_id": delivery_id,
        **payload,
    }
    _require(
        len(canonical_json(unsigned).encode("utf-8")) <= MAX_RECEIPT_BYTES,
        "program delivery receipt exceeds its byte ceiling",
    )
    receipt = {**unsigned, "receipt_hash": _sha(unsigned)}
    _write_json_atomic(
        _receipt_path(
            root,
            run_id,
            delivery_id,
            str(receipt["receipt_hash"]),
        ),
        receipt,
        immutable=True,
    )
    return receipt


def _load_receipt(
    root: Path,
    run_id: str,
    delivery_id: str,
    receipt_hash: str,
) -> dict[str, object]:
    receipt = _load_json(
        _receipt_path(root, run_id, delivery_id, receipt_hash),
        "program delivery receipt",
    )
    _require(
        receipt.get("kind") == PROGRAM_DELIVERY_RECEIPT_KIND
        and receipt.get("schema_version") == PROGRAM_DELIVERY_SCHEMA_VERSION
        and receipt.get("run_id") == run_id
        and receipt.get("delivery_id") == delivery_id,
        "program delivery receipt identity is invalid",
    )
    unsigned = {
        key: item for key, item in receipt.items() if key != "receipt_hash"
    }
    _require(
        receipt.get("receipt_hash") == receipt_hash
        and _sha(unsigned) == receipt_hash,
        "program delivery receipt hash is invalid",
    )
    return receipt


def _is_delivery_claim(
    claim: dict[str, object],
    delivery_id: str,
) -> bool:
    return str(claim.get("idempotency_key", "")).startswith(
        f"program-delivery/{delivery_id}/"
    )


def replay_program_delivery(
    root: Path,
    run_id: str,
    delivery_id: str,
    *,
    now: str | datetime | None = None,
) -> dict[str, object]:
    plan = _load_plan(root.resolve(), run_id, delivery_id)
    projection = replay_program(root.resolve(), run_id, now=now)
    receipts: list[dict[str, object]] = []
    active: list[dict[str, object]] = []
    for claim in projection["claims"]:
        if not isinstance(claim, dict) or not _is_delivery_claim(
            claim, delivery_id
        ):
            continue
        if claim["status"] == "active":
            active.append(claim)
            continue
        receipt_hash = claim.get("receipt_hash")
        _require(
            isinstance(receipt_hash, str),
            "completed delivery claim has no receipt hash",
        )
        receipt = _load_receipt(
            root.resolve(),
            run_id,
            delivery_id,
            receipt_hash,
        )
        _require(
            receipt.get("claim_id") == claim["claim_id"]
            and receipt.get("request_hash") == claim["request_hash"],
            "delivery receipt ledger binding changed",
        )
        receipts.append(receipt)
    actions = plan["preview"]["actions"]  # type: ignore[index]
    by_action = {
        str(receipt["action_id"]): receipt
        for receipt in receipts
    }
    _require(
        len(by_action) == len(receipts),
        "program delivery has duplicate action receipts",
    )
    completed = [
        str(action["action_id"])
        for action in actions
        if str(action["action_id"]) in by_action
    ]
    next_action = next(
        (
            action
            for action in actions
            if str(action["action_id"]) not in by_action
        ),
        None,
    )
    return {
        "kind": PROGRAM_DELIVERY_FRONTIER_KIND,
        "schema_version": PROGRAM_DELIVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "delivery_id": delivery_id,
        "plan_hash": plan["plan_hash"],
        "authority": projection,
        "state": "complete" if next_action is None else (
            "reconciling" if active else "ready"
        ),
        "complete": next_action is None,
        "completed_action_ids": completed,
        "active_claims": active,
        "receipts": receipts,
        "receipt_hashes": [
            receipt["receipt_hash"] for receipt in receipts
        ],
        "next_action": next_action,
        "starts_work": False,
        "writes_state": False,
    }


def _pending_receipt_for_claim(
    root: Path,
    run_id: str,
    delivery_id: str,
    claim_id: str,
    action_id: str,
) -> dict[str, object] | None:
    directory = _delivery_dir(root, run_id, delivery_id) / "receipts"
    if not directory.is_dir():
        return None
    matches: list[dict[str, object]] = []
    for path in sorted(directory.glob("*.json")):
        candidate = _load_receipt(
            root,
            run_id,
            delivery_id,
            "sha256:" + path.stem,
        )
        if (
            candidate.get("claim_id") == claim_id
            and candidate.get("action_id") == action_id
        ):
            matches.append(candidate)
    _require(len(matches) <= 1, "duplicate pending delivery receipts")
    return matches[0] if matches else None


def _mutation_from_intent(
    root: Path,
    intent: dict[str, object],
) -> MutationPlan:
    changes: list[FileChange] = []
    for raw in intent["changes"]:  # type: ignore[index]
        _require(isinstance(raw, dict), "mutation change intent is invalid")
        relative = _safe_relative_path(str(raw["path"]))
        path = (root / relative).resolve()
        _require(
            path == root or root in path.parents,
            "mutation target escapes repository",
        )
        old = raw["old_content"]
        new = raw["new_content"]
        _require(
            old is None or isinstance(old, str),
            "mutation old content is invalid",
        )
        _require(isinstance(new, str), "mutation new content is invalid")
        _require(
            raw["old_hash"] == _sha({"content": old})
            and raw["new_hash"] == _sha({"content": new}),
            "mutation content hash is invalid",
        )
        changes.append(FileChange(
            path=path,
            new_content=new,
            existed=bool(raw["existed"]),
            old_content=old,
        ))
    plan = MutationPlan(
        kind=str(intent["kind"]),
        root=root,
        project_slug=str(intent["project"]),
        changes=changes,
        create_dirs=[
            (root / _safe_relative_path(str(path))).resolve()
            for path in intent["create_dirs"]  # type: ignore[index]
        ],
        summary=dict(intent["summary"]),  # type: ignore[arg-type]
    )
    _require(
        plan_fingerprint(plan) == intent["fingerprint"],
        "mutation intent fingerprint is invalid",
    )
    return plan


def _content_state(change: FileChange) -> str:
    if not change.path.exists():
        return "old" if not change.existed else "other"
    if not change.path.is_file() or change.path.is_symlink():
        return "other"
    current = read_text(change.path)
    if current == change.new_content:
        return "new"
    if change.existed and current == (change.old_content or ""):
        return "old"
    return "other"


def _execute_mutation(
    root: Path,
    action: dict[str, object],
) -> dict[str, object]:
    detail = action["detail"]
    _require(isinstance(detail, dict), "delivery action detail is invalid")
    intent = detail["mutation"]
    _require(isinstance(intent, dict), "delivery mutation intent is absent")
    plan = _mutation_from_intent(root, intent)
    states = [_content_state(change) for change in plan.changes]
    _require("other" not in states, "roadmap mutation target changed unexpectedly")
    if all(state == "old" for state in states):
        _require(
            _index_tree(root) == intent["before_index_tree"],
            "roadmap mutation index lease changed",
        )
        result = apply_plan(plan, validate_after=True)
        issues = list(result["issues"])
        if plan.kind == "story-evidence":
            issues = [
                item for item in issues
                if "evidence exists but matching story is not done"
                not in str(item)
            ]
        if (
            plan.kind == "story-status"
            and plan.summary.get("status") == "done"
        ):
            issues = [
                item for item in issues
                if "all stories are done but final-summary.md is missing"
                not in str(item)
            ]
        _require(
            not issues,
            "roadmap mutation validation failed: "
            + "; ".join(str(item) for item in issues),
        )
    elif not all(state == "new" for state in states):
        raise DwError("roadmap mutation is partially applied; refusing to guess")
    paths = [rel(change.path, root) for change in plan.changes]
    if paths:
        _git(root, "add", "--", *paths)
    _require(
        _index_tree(root) == intent["after_index_tree"],
        "roadmap mutation produced a different staged tree",
    )
    return {
        "mutation_fingerprint": intent["fingerprint"],
        "index_tree": intent["after_index_tree"],
        "paths": paths,
        "reconciled": all(state == "new" for state in states),
    }


def _execute_integration(
    root: Path,
    run_id: str,
    action: dict[str, object],
) -> dict[str, object]:
    detail = action["detail"]
    assert isinstance(detail, dict)
    _require(
        head_sha(root) == detail["base_head"]
        and _head_tree(root) == detail["base_tree"],
        "integration base commit changed",
    )
    before = str(detail["before_index_tree"])
    after = str(detail["after_index_tree"])
    current = _index_tree(root)
    paths = list(detail["paths"])
    if current == after:
        _require(
            _staged_paths(root) == sorted(paths)
            and not _unstaged_paths(root),
            "integrated tree has unexpected staged or worktree paths",
        )
        return {
            "index_tree": after,
            "paths": paths,
            "patch_sha256": detail["patch_sha256"],
            "reconciled": True,
        }
    _require(
        current == before
        and not _staged_paths(root)
        and not _unstaged_paths(root),
        "integration lane is dirty or divergent",
    )
    conductor = replay_program_conductor(root, run_id)
    artifact = next(
        (
            item
            for receipt in conductor["receipts"]
            for item in receipt.get("artifacts", [])
            if isinstance(item, dict)
            and item.get("artifact_id") == detail["artifact_id"]
        ),
        None,
    )
    _require(isinstance(artifact, dict), "candidate artifact disappeared")
    patch = _artifact_content(root, run_id, artifact)
    _require(
        "sha256:" + hashlib.sha256(patch).hexdigest()
        == detail["patch_sha256"]
        and len(patch) == detail["patch_bytes"],
        "candidate diff bytes changed",
    )
    check = _git(
        root,
        "apply",
        "--check",
        "--index",
        "--binary",
        "--whitespace=nowarn",
        "-",
        input_data=patch,
        check=False,
    )
    _require(check.returncode == 0, "candidate diff no longer applies exactly")
    _git(
        root,
        "apply",
        "--index",
        "--binary",
        "--whitespace=nowarn",
        "-",
        input_data=patch,
    )
    _require(
        _index_tree(root) == after
        and _staged_paths(root) == sorted(paths)
        and not _unstaged_paths(root),
        "candidate integration produced a different tree or path set",
    )
    return {
        "index_tree": after,
        "paths": paths,
        "patch_sha256": detail["patch_sha256"],
        "reconciled": False,
    }


def _execute_contract(
    root: Path,
    action: dict[str, object],
) -> dict[str, object]:
    detail = action["detail"]
    assert isinstance(detail, dict)
    _require(
        _index_tree(root) == detail["expected_index_tree"],
        "contract generation staged-tree lease changed",
    )
    path = root / CONTRACT_REL
    expected = str(detail["content"])
    if path.exists():
        _require(
            path.is_file() and not path.is_symlink()
            and read_text(path) == expected,
            "program contract conflicts with existing content",
        )
        reconciled = True
    else:
        write_contract(
            root,
            list(detail["story_ids"]),
            consent="no",
            reasons=[
                "Autonomous program delivery; no external work-log export.",
            ],
            tier="full",
            generated_at=str(detail["generated_at"]),
            program_provenance=dict(detail["provenance"]),
        )
        _require(read_text(path) == expected, "generated contract differs from preview")
        reconciled = False
    return {
        "contract_digest": detail["content_hash"],
        "index_tree": detail["expected_index_tree"],
        "reconciled": reconciled,
    }


def _current_conductor_receipts(
    root: Path,
    run_id: str,
) -> dict[str, dict[str, object]]:
    replayed = replay_program_conductor(root, run_id)
    return {
        str(item["receipt_hash"]): item
        for item in replayed["receipts"]
    }


def _execute_certification(
    root: Path,
    run_id: str,
    action: dict[str, object],
) -> dict[str, object]:
    detail = action["detail"]
    assert isinstance(detail, dict)
    _require(
        _index_tree(root) == detail["expected_index_tree"],
        "certification staged-tree lease changed",
    )
    receipts = _current_conductor_receipts(root, run_id)
    if action["kind"] == "certification-objective":
        required = list(detail["mechanical_receipt_hashes"])
        _require(required, "objective certification has no mechanical proof")
        for receipt_hash in required:
            receipt = receipts.get(str(receipt_hash))
            _require(
                receipt is not None
                and receipt.get("action_kind") == "check"
                and receipt.get("outcome") == "succeeded"
                and receipt.get("result") in GREEN_RESULTS,
                "objective certification mechanical proof is stale or red",
            )
        evidence_path = _safe_relative_path(str(detail["evidence_path"]))
        staged = _git(root, "show", f":{evidence_path}", check=False)
        _require(
            staged.returncode == 0,
            "objective certification evidence is not in the staged index",
        )
    else:
        required = list(detail["governed_receipt_hashes"])
        _require(required, "governed certification has no verdict proof")
        for receipt_hash in required:
            _require(
                str(receipt_hash) in receipts,
                "governed certification receipt is stale or absent",
            )
        verifier = receipts.get(str(detail["verifier_receipt_hash"]))
        _require(
            verifier is not None
            and verifier.get("outcome") == "succeeded"
            and verifier.get("result") in GREEN_RESULTS
            and isinstance(verifier.get("verdict"), dict),
            "governed certification verifier is not green",
        )
    before = str(detail["before"])
    after = str(detail["after"])
    path = root / CONTRACT_REL
    current = read_text(path) if path.is_file() else ""
    reconciled = current == after
    apply_contract_certification(
        root,
        expected_before=before,
        certified_content=after,
    )
    _require(
        contract_digest(read_text(path)) == detail["after_hash"],
        "certified contract digest differs from preview",
    )
    return {
        "contract_digest": detail["after_hash"],
        "proof_hash": detail["proof_hash"],
        "titles": detail["titles"],
        "reconciled": reconciled,
    }


def _commit_facts(root: Path, commit: str) -> dict[str, str | None]:
    parent = _git_text(root, "rev-parse", f"{commit}^")
    tree = _head_tree(root, commit)
    message = _git_text(root, "show", "-s", "--format=%B", commit)
    return {"commit": commit, "parent": parent, "tree": tree, "message": message}


def _execute_commit(
    root: Path,
    action: dict[str, object],
) -> dict[str, object]:
    detail = action["detail"]
    assert isinstance(detail, dict)
    parent = str(detail["parent"])
    expected_tree = str(detail["tree"])
    expected_message = str(detail["message"]).strip()
    current_head = head_sha(root)
    reconciled = current_head != parent
    if current_head == parent:
        _require(
            _index_tree(root) == expected_tree
            and _staged_paths(root) == sorted(detail["staged_paths"]),
            "commit staged tree or paths changed",
        )
        contract_path = root / CONTRACT_REL
        _require(
            contract_path.is_file()
            and read_text(contract_path) == detail["contract_content"],
            "certified contract changed before commit",
        )
        gate = run_gate(root, record_event=False)
        if not gate.ok:
            failure = gate.failure
            raise DwError(
                "real commit gate refused"
                + (
                    f" ({failure.rule}): {failure.message}"
                    if failure is not None
                    else ""
                )
            )
        completed = _git(
            root,
            "commit",
            "-m",
            str(detail["message"]),
            check=False,
        )
        if completed.returncode and head_sha(root) == parent:
            message = completed.stderr.decode("utf-8", "replace").strip()
            raise DwError(
                "gated commit failed" + (f": {message}" if message else "")
            )
        current_head = head_sha(root)
    _require(
        isinstance(current_head, str)
        and bool(_COMMIT_RE.fullmatch(current_head)),
        "commit effect produced no exact commit",
    )
    facts = _commit_facts(root, current_head)
    _require(
        facts["parent"] == parent
        and facts["tree"] == expected_tree
        and str(facts["message"]).strip() == expected_message,
        "existing commit differs from the exact delivery intent",
    )
    archive = archive_contract(
        root,
        current_head,
        expected_content=str(detail["contract_content"]),
    )
    _require(
        read_text(archive) == detail["contract_content"],
        "contract archive differs from certified content",
    )
    _require(
        _index_tree(root) == expected_tree
        and not _staged_paths(root)
        and not _unstaged_paths(root),
        "repository is not clean at the exact delivery commit",
    )
    verified = run_verify(root, f"{parent}..{current_head}")
    _require(
        verified.ok and verified.verified == 1,
        "exact committed range failed PMO verification: "
        + (
            verified.error
            or "; ".join(item.message for item in verified.violations)
        ),
    )
    return {
        "commit": current_head,
        "parent": parent,
        "tree": expected_tree,
        "message_hash": _sha({"message": expected_message}),
        "contract_digest": detail["contract_digest"],
        # WLA-28-02: one resolution through the repository-fact boundary. This
        # expression previously spawned rev-parse --git-dir three times, twice
        # redundantly, to answer the same question.
        "archive": str(archive.relative_to(repofacts.git_dir(root))),
        "gate": "pass",
        "verify": "pass",
        "reconciled": reconciled,
    }


def _push_target_ref(remote: str, remote_ref: str) -> str:
    prefixes = (f"refs/remotes/{remote}/", f"{remote}/")
    for prefix in prefixes:
        if remote_ref.startswith(prefix):
            branch = remote_ref[len(prefix):]
            _require(branch and branch != "HEAD", "push branch is ambiguous")
            return f"refs/heads/{branch}"
    raise DwError("push requires an exact remote-tracking ref")


def _tracking_ref(remote: str, remote_ref: str) -> str:
    if remote_ref.startswith("refs/remotes/"):
        return remote_ref
    prefix = f"{remote}/"
    _require(remote_ref.startswith(prefix), "remote tracking ref is invalid")
    return f"refs/remotes/{remote}/{remote_ref[len(prefix):]}"


def _ls_remote(root: Path, remote: str, target_ref: str) -> str | None:
    completed = _git(
        root,
        "ls-remote",
        "--refs",
        remote,
        target_ref,
        check=False,
    )
    if completed.returncode:
        raise DwError(
            "cannot observe bound push remote: "
            + completed.stderr.decode("utf-8", "replace").strip()
        )
    lines = completed.stdout.decode("utf-8", "replace").splitlines()
    _require(len(lines) <= 1, "push remote returned an ambiguous ref")
    if not lines:
        return None
    sha, _separator, ref = lines[0].partition("\t")
    _require(
        ref == target_ref and bool(_COMMIT_RE.fullmatch(sha)),
        "push remote observation is malformed",
    )
    return sha


def _execute_push(
    root: Path,
    action: dict[str, object],
    commit_receipt: dict[str, object],
) -> dict[str, object]:
    detail = action["detail"]
    assert isinstance(detail, dict)
    result = commit_receipt["result"]
    _require(isinstance(result, dict), "commit receipt result is invalid")
    commit = str(result["commit"])
    _require(head_sha(root) == commit, "push commit is no longer HEAD")
    remote = str(detail["remote"])
    remote_ref = str(detail["remote_ref"])
    target_ref = str(detail["target_ref"])
    observation = _remote_observation(root, remote, remote_ref)
    _require(
        observation["remote_url_hash"] == detail["remote_url_hash"],
        "push remote URL changed",
    )
    actual = _ls_remote(root, remote, target_ref)
    expected_old = detail["expected_remote_head"]
    reconciled = actual == commit
    if not reconciled:
        _require(
            actual == expected_old,
            "bound remote ref diverged before push",
        )
        if actual is not None:
            ancestor = _git(
                root,
                "merge-base",
                "--is-ancestor",
                actual,
                commit,
                check=False,
            )
            _require(
                ancestor.returncode == 0,
                "push would not be a fast-forward",
            )
        pushed = _git(
            root,
            "push",
            remote,
            f"{commit}:{target_ref}",
            check=False,
        )
        if pushed.returncode:
            after_failure = _ls_remote(root, remote, target_ref)
            if after_failure != commit:
                message = pushed.stderr.decode("utf-8", "replace").strip()
                raise DwError(
                    "fast-forward push failed"
                    + (f": {message}" if message else "")
                )
        actual = _ls_remote(root, remote, target_ref)
    _require(actual == commit, "remote ref did not reach the exact commit")
    tracking = _tracking_ref(remote, remote_ref)
    local = _git_text(
        root,
        "rev-parse",
        "--verify",
        tracking,
    )
    if local != commit:
        _git(root, "update-ref", tracking, commit, local)
    rebound = _remote_observation(root, remote, remote_ref)
    _require(
        rebound["remote_head"] == commit
        and rebound["remote_url_hash"] == detail["remote_url_hash"],
        "pushed remote fact did not rebind exactly",
    )
    return {
        "commit": commit,
        "remote": remote,
        "remote_ref": remote_ref,
        "target_ref": target_ref,
        "remote_url_hash": detail["remote_url_hash"],
        "previous_head": expected_old,
        "observed_head": commit,
        "fast_forward": True,
        "reconciled": reconciled,
    }


def _execute_action(
    root: Path,
    run_id: str,
    action: dict[str, object],
    prior_receipts: list[dict[str, object]],
) -> dict[str, object]:
    kind = str(action["kind"])
    if kind == "integration":
        return _execute_integration(root, run_id, action)
    if kind in {
        "evidence",
        "story-complete",
        "phase-advance",
        "story-start",
    }:
        return _execute_mutation(root, action)
    if kind == "contract":
        return _execute_contract(root, action)
    if kind in {"certification-objective", "certification-verdict"}:
        return _execute_certification(root, run_id, action)
    if kind == "commit":
        return _execute_commit(root, action)
    if kind == "push":
        detail = action["detail"]
        assert isinstance(detail, dict)
        commit_receipt = next(
            (
                item
                for item in prior_receipts
                if item.get("action_id") == detail["commit_from_action"]
            ),
            None,
        )
        _require(
            isinstance(commit_receipt, dict),
            "push has no exact commit receipt",
        )
        return _execute_push(root, action, commit_receipt)
    raise DwError(f"unsupported delivery action: {kind}")


def _resolved_subject_hash(
    action: dict[str, object],
    receipts: list[dict[str, object]],
) -> str:
    if action["kind"] != "push":
        return str(action["subject_hash"])
    detail = action["detail"]
    assert isinstance(detail, dict)
    commit_receipt = next(
        (
            item for item in receipts
            if item.get("action_id") == detail["commit_from_action"]
        ),
        None,
    )
    _require(isinstance(commit_receipt, dict), "push subject lacks commit receipt")
    result = commit_receipt["result"]
    _require(isinstance(result, dict), "commit receipt result is invalid")
    return _sha({
        "planned_subject_hash": action["subject_hash"],
        "commit": result["commit"],
        "remote": detail["remote"],
        "target_ref": detail["target_ref"],
        "expected_remote_head": detail["expected_remote_head"],
    })


def tick_program_delivery(
    root: Path,
    run_id: str,
    delivery_id: str,
    *,
    driver_config: object | None = None,
    now: str | datetime | None = None,
    boundary_hook: BoundaryHook | None = None,
    _expected_binding: dict[str, object] | None = None,
) -> dict[str, object]:
    """Perform at most one claimed delivery effect or reconciliation."""
    root = root.resolve()
    observed = _time(now, "now")
    config = load_driver_config(root, driver_config)
    lock = _run_dir(root, run_id) / ".program-delivery.lock"
    with _file_lock(lock):
        if _expected_binding is not None:
            authority = replay_program(root, run_id, now=observed)
            _require(
                all(
                    authority.get(key) == _expected_binding.get(key)
                    for key in (
                        "grant_hash", "ledger_head", "generation", "state",
                    )
                ),
                "program act token is stale at the delivery lock",
            )
        before = replay_program_delivery(
            root,
            run_id,
            delivery_id,
            now=observed,
        )
        if before["complete"]:
            return {
                "kind": PROGRAM_DELIVERY_TICK_KIND,
                "schema_version": PROGRAM_DELIVERY_SCHEMA_VERSION,
                "run_id": run_id,
                "delivery_id": delivery_id,
                "state": "complete",
                "progressed": False,
                "action": None,
                "receipt": None,
                "remaining": 0,
                "content_safe": True,
            }
        action = before["next_action"]
        _require(isinstance(action, dict), "delivery frontier has no next action")
        active = before["active_claims"]
        _require(len(active) <= 1, "delivery has multiple unresolved claims")
        expected_key = (
            f"program-delivery/{delivery_id}/{action['action_id']}"
        )
        if active:
            claim = active[0]
            _require(
                claim["idempotency_key"] == expected_key,
                "active delivery claim is outside the rebuilt frontier",
            )
        else:
            subject_hash = _resolved_subject_hash(
                action,
                list(before["receipts"]),
            )
            claim_preview = build_program_claim_preview(
                root,
                run_id,
                category=str(action["category"]),
                subject={
                    "kind": f"program-delivery-{action['kind']}",
                    "id": f"{delivery_id}/{action['action_id']}",
                    "hash": subject_hash,
                    "phase": action["phase"],
                    "story": action["story"],
                },
                idempotency_key=expected_key,
                reason=(
                    f"Perform exact delivery action "
                    f"{action['action_id']} for {action['story']}."
                ),
                now=observed,
                driver_config=config,
            )
            _require(
                claim_preview["applicable"],
                "delivery claim is not applicable: "
                + "; ".join(
                    str(item.get("message"))
                    for item in claim_preview["issues"]
                    if isinstance(item, dict)
                ),
            )
            claimed = apply_program_claim(
                root,
                claim_preview,
                claim_token=str(claim_preview["claim_token"]),
                now=observed,
                driver_config=config,
            )
            claim = claimed["claim"]
            _require(isinstance(claim, dict), "delivery claim was not reserved")
        _boundary(boundary_hook, "after-claim", {
            "delivery_id": delivery_id,
            "action_id": action["action_id"],
            "action_kind": action["kind"],
            "claim_id": claim["claim_id"],
        })

        receipt = _pending_receipt_for_claim(
            root,
            run_id,
            delivery_id,
            str(claim["claim_id"]),
            str(action["action_id"]),
        )
        if receipt is None:
            result = _execute_action(
                root,
                run_id,
                action,
                list(before["receipts"]),
            )
            _boundary(boundary_hook, "after-effect", {
                "delivery_id": delivery_id,
                "action_id": action["action_id"],
                "action_kind": action["kind"],
                "claim_id": claim["claim_id"],
            })
            receipt = _store_receipt(
                root,
                run_id,
                delivery_id,
                {
                    "action_id": action["action_id"],
                    "action_kind": action["kind"],
                    "category": action["category"],
                    "capability": action["capability"],
                    "phase": action["phase"],
                    "story": action["story"],
                    "subject_hash": _resolved_subject_hash(
                        action,
                        list(before["receipts"]),
                    ),
                    "claim_id": claim["claim_id"],
                    "request_hash": claim["request_hash"],
                    "result": result,
                    "issued_at": claim["reserved_at"],
                    "content_safe": True,
                },
            )
        _boundary(boundary_hook, "after-receipt", {
            "delivery_id": delivery_id,
            "action_id": action["action_id"],
            "action_kind": action["kind"],
            "claim_id": claim["claim_id"],
            "receipt_hash": receipt["receipt_hash"],
        })

        current = replay_program(root, run_id, now=observed)
        still_active = next(
            (
                item
                for item in current["active_claims"]
                if item["claim_id"] == claim["claim_id"]
            ),
            None,
        )
        if still_active is not None:
            completion = build_program_completion_preview(
                root,
                run_id,
                claim_id=str(claim["claim_id"]),
                result="succeeded",
                receipt_hash=str(receipt["receipt_hash"]),
                reason=(
                    f"Completed exact delivery action "
                    f"{action['action_id']}."
                ),
                now=observed,
            )
            _require(
                completion["applicable"],
                "delivery completion facts cannot be observed",
            )
            apply_program_completion(
                root,
                completion,
                completion_token=str(completion["completion_token"]),
                now=observed,
            )
        _boundary(boundary_hook, "after-completion", {
            "delivery_id": delivery_id,
            "action_id": action["action_id"],
            "action_kind": action["kind"],
            "claim_id": claim["claim_id"],
            "receipt_hash": receipt["receipt_hash"],
        })
        after = replay_program_delivery(
            root,
            run_id,
            delivery_id,
            now=observed,
        )
        return {
            "kind": PROGRAM_DELIVERY_TICK_KIND,
            "schema_version": PROGRAM_DELIVERY_SCHEMA_VERSION,
            "run_id": run_id,
            "delivery_id": delivery_id,
            "state": after["state"],
            "progressed": True,
            "action": {
                "action_id": action["action_id"],
                "kind": action["kind"],
                "phase": action["phase"],
                "story": action["story"],
            },
            "receipt": {
                "receipt_hash": receipt["receipt_hash"],
                "result": receipt["result"],
            },
            "remaining": (
                len(_load_plan(root, run_id, delivery_id)["preview"]["actions"])  # type: ignore[index]
                - len(after["receipts"])
            ),
            "content_safe": True,
        }


def supervise_program_delivery(
    root: Path,
    run_id: str,
    delivery_id: str,
    *,
    max_ticks: int = 32,
    driver_config: object | None = None,
    now: str | datetime | None = None,
    boundary_hook: BoundaryHook | None = None,
) -> dict[str, object]:
    _require(
        isinstance(max_ticks, int)
        and not isinstance(max_ticks, bool)
        and 1 <= max_ticks <= 1_000,
        "delivery supervisor max_ticks must be between 1 and 1000",
    )
    ticks: list[dict[str, object]] = []
    for _index in range(max_ticks):
        tick = tick_program_delivery(
            root,
            run_id,
            delivery_id,
            driver_config=driver_config,
            now=now,
            boundary_hook=boundary_hook,
        )
        ticks.append(tick)
        if tick["state"] == "complete":
            break
    frontier = replay_program_delivery(
        root,
        run_id,
        delivery_id,
        now=now,
    )
    return {
        "kind": "delivery-workbench-program-delivery-supervision",
        "schema_version": PROGRAM_DELIVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "delivery_id": delivery_id,
        "ticks": len(ticks),
        "complete": frontier["complete"],
        "state": frontier["state"],
        "remaining": (
            len(_load_plan(root, run_id, delivery_id)["preview"]["actions"])  # type: ignore[index]
            - len(frontier["receipts"])
        ),
        "last_tick": ticks[-1] if ticks else None,
        "content_safe": True,
    }


# ---------------------------------------------------------------------------
# Separately authorized obligation rails

PROGRAM_OBLIGATION_MATERIALIZATION_PREVIEW_KIND = (
    "delivery-workbench-program-obligation-materialization-preview"
)
PROGRAM_OBLIGATION_DISPOSITION_PREVIEW_KIND = (
    "delivery-workbench-program-obligation-disposition-preview"
)
PROGRAM_OBLIGATION_RAIL_RECEIPT_KIND = (
    "delivery-workbench-program-obligation-rail-receipt"
)


def _obligation_operation_id(
    run_id: str,
    action: str,
    obligation_id: str,
    intent_hash: str,
) -> str:
    digest = hashlib.sha256(
        f"{run_id}|{action}|{obligation_id}|{intent_hash}".encode("utf-8")
    ).hexdigest()[:24]
    return f"obligation-{digest}"


def _obligation_operation_dir(
    root: Path,
    run_id: str,
    operation_id: str,
) -> Path:
    _require(
        re.fullmatch(r"obligation-[0-9a-f]{24}", operation_id) is not None,
        "obligation rail operation id is invalid",
    )
    base = _delivery_base(root.resolve(), run_id) / "obligations"
    if base.is_symlink():
        raise DwError("refusing symlinked obligation rail store")
    path = base / operation_id
    _require(path.parent == base, "obligation operation escapes its run")
    return path


def _obligation_by_id(
    projection: dict[str, object],
    obligation_id: str,
) -> dict[str, object] | None:
    return next(
        (
            item
            for item in projection["obligations"]  # type: ignore[index]
            if isinstance(item, dict) and item.get("id") == obligation_id
        ),
        None,
    )


def _materialization_marker(
    run_id: str,
    obligation: dict[str, object],
) -> str:
    acceptance = " ".join(str(obligation["acceptance"]).split())
    acceptance = acceptance.replace("`", "'").replace("|", "-")
    return (
        "## Program obligation provenance\n\n"
        f"- **Program run:** `{run_id}`\n"
        f"- **Program obligation:** `{obligation['id']}`\n"
        f"- **Source decision:** `{obligation['source_decision_hash']}`\n"
        f"- **Obligation hash:** `{obligation['obligation_hash']}`\n"
        f"- **Accountable role:** `{obligation['accountable_role']}`\n"
        f"- **Acceptance:** {acceptance}\n\n"
        "This traced roadmap item does not replace or erase the original "
        "program-ledger obligation.\n"
    )


def _find_materialized_obligation(
    root: Path,
    run_id: str,
    obligation: dict[str, object],
) -> dict[str, str] | None:
    marker = f"- **Program obligation:** `{obligation['id']}`"
    source = f"- **Source decision:** `{obligation['source_decision_hash']}`"
    matches: list[Path] = []
    roadmap = root / "pm/roadmap"
    if not roadmap.is_dir():
        roadmap = root / "pmo-roadmap/pm/roadmap"
    for path in sorted(roadmap.glob("*/phase-*/story-*.md")):
        if not path.is_file() or path.is_symlink():
            continue
        content = read_text(path)
        if marker in content:
            _require(
                source in content,
                "obligation id is already materialized from another decision",
            )
            matches.append(path)
    _require(
        len(matches) <= 1,
        "obligation is materialized in multiple roadmap stories",
    )
    if not matches:
        return None
    heading = read_text(matches[0]).splitlines()[0]
    story_id = heading.removeprefix("# ").split(" ", 1)[0]
    return {"story": story_id, "path": rel(matches[0], root)}


def build_program_obligation_materialization_preview(
    root: Path,
    run_id: str,
    obligation_id: str,
    *,
    phase: int,
    driver_config: object | None = None,
    now: str | datetime | None = None,
) -> dict[str, object]:
    """Preview one deduplicated obligation-to-roadmap transformation."""
    root = root.resolve()
    observed = _time(now, "now")
    config = load_driver_config(root, driver_config)
    _path, grant, _plan = _load_documents(root, run_id)
    projection = replay_program(root, run_id, now=observed)
    issues: list[dict[str, str]] = []
    for message in program_freshness_issues(
        root,
        grant,
        projection,
        driver_config=config,
    ):
        issues.append(_issue("program-stale", message))
    obligation = _obligation_by_id(projection, obligation_id)
    if obligation is None:
        issues.append(_issue(
            "obligation-not-found",
            "materialization names no durable program obligation",
        ))
    elif obligation["state"] != "open":
        issues.append(_issue(
            "obligation-not-open",
            f"obligation is already {obligation['state']}",
        ))
    if "obligation:materialize" not in projection["capabilities"]:
        issues.append(_issue(
            "capability-denied",
            "program grant lacks obligation:materialize",
        ))
    if (
        phase not in grant["scope"]["phases"]  # type: ignore[index]
        or isinstance(phase, bool)
    ):
        issues.append(_issue(
            "scope-violation",
            f"phase {phase} is outside the granted program scope",
        ))
    current_repository = _repository_facts(
        root,
        projection["expected_repository"].get("remote"),  # type: ignore[union-attr]
        projection["expected_repository"].get("remote_ref"),  # type: ignore[union-attr]
    )
    if (
        current_repository != projection["expected_repository"]
        or not current_repository["clean"]
        or current_repository["operation"] != "normal"
    ):
        issues.append(_issue(
            "repository-not-clean",
            "obligation materialization requires the exact clean integration lane",
        ))

    existing: dict[str, str] | None = None
    if obligation is not None:
        try:
            existing = _find_materialized_obligation(
                root, run_id, obligation
            )
        except DwError as exc:
            issues.append(_issue("materialization-conflict", exc.message))
    if existing is not None:
        # A retry after the exact story has been staged or committed is a
        # content-verified no-op. The materialization itself may be why the
        # integration lane is no longer clean.
        issues = [
            item
            for item in issues
            if item["code"] != "repository-not-clean"
        ]

    mutation: dict[str, object] | None = None
    story: str | None = existing["story"] if existing else None
    story_path: str | None = existing["path"] if existing else None
    if not issues and obligation is not None and existing is None:
        try:
            with tempfile.TemporaryDirectory(
                prefix="dw-obligation-materialization-preview."
            ) as raw:
                scratch = Path(raw) / "repo"
                _clone_for_preview(root, scratch)
                scratch = scratch.resolve()
                project = get_project(
                    scratch,
                    str(projection["expected_roadmap"]["project"]),  # type: ignore[index]
                )
                selected_phase = get_phase(project, str(phase))
                statement = " ".join(str(obligation["statement"]).split())
                title = re.sub(
                    r"[\[\]<>|`#*_]+",
                    " ",
                    statement,
                )
                title = " ".join(title.split())[:96].rstrip()
                if not title:
                    title = f"Program obligation {obligation['id']}"
                plan = plan_story_create(
                    scratch,
                    project,
                    selected_phase,
                    title,
                    slug=(
                        "obligation-"
                        + slugify(str(obligation["id"]))[:64]
                    ),
                    status="backlog",
                )
                story_relative = str(plan.summary["story_path"])
                story_change = next(
                    change
                    for change in plan.changes
                    if rel(change.path, scratch) == story_relative
                )
                story_change.new_content = (
                    story_change.new_content.rstrip()
                    + "\n\n"
                    + _materialization_marker(run_id, obligation)
                )
                mutation = _apply_scratch_mutation(scratch, plan)
                story = str(plan.summary["story_id"])
                story_path = story_relative
        except DwError as exc:
            issues.append(_issue("materialization-refused", exc.message))

    intent = {
        "action": "materialize",
        "obligation_id": obligation_id,
        "obligation_hash": (
            obligation.get("obligation_hash")
            if obligation is not None else None
        ),
        "source_decision_hash": (
            obligation.get("source_decision_hash")
            if obligation is not None else None
        ),
        "phase": phase,
        "story": story,
        "story_path": story_path,
        "mutation": mutation,
        "existing": existing,
    }
    unsigned = {
        "kind": PROGRAM_OBLIGATION_MATERIALIZATION_PREVIEW_KIND,
        "schema_version": PROGRAM_DELIVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "applicable": not issues,
        "issues": issues,
        "observed_at": _format_time(observed),
        "binding": {
            "grant_hash": projection["grant_hash"],
            "ledger_head": projection["ledger_head"],
            "generation": projection["generation"],
            "repository": projection["expected_repository"],
            "roadmap": projection["expected_roadmap"],
        },
        "intent": intent,
        "no_op": existing is not None,
        "starts_work": False,
        "writes_state": False,
        "mutates_repository": False,
        "mutates_roadmap": False,
    }
    return {**unsigned, "materialization_token": _sha(unsigned)}


def _validate_obligation_preview(
    value: object,
    *,
    kind: str,
    token_key: str,
) -> dict[str, object]:
    _require(isinstance(value, dict), "obligation preview must be an object")
    preview = dict(value)
    _require(
        preview.get("kind") == kind
        and preview.get("schema_version") == PROGRAM_DELIVERY_SCHEMA_VERSION,
        "unsupported obligation rail preview",
    )
    token = preview.get(token_key)
    _require(
        isinstance(token, str) and bool(_HASH_RE.fullmatch(token)),
        "obligation rail token is invalid",
    )
    unsigned = {key: item for key, item in preview.items() if key != token_key}
    _require(_sha(unsigned) == token, "obligation rail token hash is invalid")
    for effect in (
        "starts_work",
        "writes_state",
        "mutates_repository",
        "mutates_roadmap",
    ):
        _require(preview.get(effect) is False, f"obligation preview {effect} must be false")
    return preview


def _store_obligation_plan(
    directory: Path,
    preview: dict[str, object],
    token: str,
) -> dict[str, object]:
    unsigned = {
        "kind": "delivery-workbench-program-obligation-rail-plan",
        "schema_version": PROGRAM_DELIVERY_SCHEMA_VERSION,
        "run_id": preview["run_id"],
        "preview": preview,
        "token": token,
    }
    plan = {**unsigned, "plan_hash": _sha(unsigned)}
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    _write_json_atomic(directory / "plan.json", plan, immutable=True)
    return plan


def _store_obligation_receipt(
    directory: Path,
    payload: dict[str, object],
) -> dict[str, object]:
    unsigned = {
        "kind": PROGRAM_OBLIGATION_RAIL_RECEIPT_KIND,
        "schema_version": PROGRAM_DELIVERY_SCHEMA_VERSION,
        **payload,
    }
    receipt = {**unsigned, "receipt_hash": _sha(unsigned)}
    _write_json_atomic(
        directory / "receipt.json",
        receipt,
        immutable=True,
    )
    return receipt


def _load_obligation_receipt(directory: Path) -> dict[str, object] | None:
    path = directory / "receipt.json"
    if not path.is_file():
        return None
    receipt = _load_json(path, "program obligation rail receipt")
    _require(
        receipt.get("kind") == PROGRAM_OBLIGATION_RAIL_RECEIPT_KIND
        and receipt.get("schema_version") == PROGRAM_DELIVERY_SCHEMA_VERSION,
        "obligation rail receipt identity is invalid",
    )
    unsigned = {
        key: item for key, item in receipt.items() if key != "receipt_hash"
    }
    _require(
        receipt.get("receipt_hash") == _sha(unsigned),
        "obligation rail receipt hash is invalid",
    )
    return receipt


def apply_program_obligation_materialization(
    root: Path,
    preview: object,
    *,
    materialization_token: str,
    driver_config: object | None = None,
    now: str | datetime | None = None,
    boundary_hook: BoundaryHook | None = None,
) -> dict[str, object]:
    submitted = _validate_obligation_preview(
        preview,
        kind=PROGRAM_OBLIGATION_MATERIALIZATION_PREVIEW_KIND,
        token_key="materialization_token",
    )
    _require(
        materialization_token == submitted["materialization_token"],
        "materialization token does not match preview",
    )
    _require(submitted["applicable"], "obligation materialization is not applicable")
    if submitted["no_op"]:
        return {
            "run_id": submitted["run_id"],
            "operation_id": None,
            "story": submitted["intent"]["story"],  # type: ignore[index]
            "story_path": submitted["intent"]["story_path"],  # type: ignore[index]
            "receipt": None,
            "idempotent": True,
        }
    root = root.resolve()
    observed = _time(now or str(submitted["observed_at"]), "now")
    config = load_driver_config(root, driver_config)
    intent_hash = _sha(submitted["intent"])
    obligation_id = str(submitted["intent"]["obligation_id"])  # type: ignore[index]
    operation_id = _obligation_operation_id(
        str(submitted["run_id"]),
        "materialize",
        obligation_id,
        intent_hash,
    )
    directory = _obligation_operation_dir(
        root,
        str(submitted["run_id"]),
        operation_id,
    )
    with _file_lock(directory.parent / ".lock"):
        plan_path = directory / "plan.json"
        if plan_path.is_file():
            stored = _load_json(plan_path, "obligation materialization plan")
            _require(
                stored.get("preview") == submitted
                and stored.get("token") == materialization_token,
                "stored materialization intent conflicts",
            )
        else:
            current = build_program_obligation_materialization_preview(
                root,
                str(submitted["run_id"]),
                obligation_id,
                phase=int(submitted["intent"]["phase"]),  # type: ignore[index]
                driver_config=config,
                now=str(submitted["observed_at"]),
            )
            _require(current == submitted, "obligation materialization preview is stale")
            _store_obligation_plan(directory, submitted, materialization_token)

        projection = replay_program(
            root, str(submitted["run_id"]), now=observed
        )
        key = f"program-obligation-materialization/{operation_id}"
        claim = next(
            (
                item for item in projection["claims"]
                if item["idempotency_key"] == key
            ),
            None,
        )
        if claim is None:
            claim_preview = build_program_claim_preview(
                root,
                str(submitted["run_id"]),
                category="obligation-materialize",
                subject={
                    "kind": "program-obligation-materialization",
                    "id": obligation_id,
                    "hash": intent_hash,
                    "phase": int(submitted["intent"]["phase"]),  # type: ignore[index]
                    "story": None,
                },
                idempotency_key=key,
                reason=(
                    f"Materialize durable obligation {obligation_id} "
                    "on its exact roadmap rail."
                ),
                now=observed,
                driver_config=config,
            )
            _require(claim_preview["applicable"], "materialization claim is not applicable")
            claimed = apply_program_claim(
                root,
                claim_preview,
                claim_token=str(claim_preview["claim_token"]),
                now=observed,
                driver_config=config,
            )
            claim = claimed["claim"]
        _require(isinstance(claim, dict), "materialization claim is absent")
        _boundary(boundary_hook, "after-claim", {
            "operation_id": operation_id,
            "action_kind": "obligation-materialize",
            "claim_id": claim["claim_id"],
        })
        receipt = _load_obligation_receipt(directory)
        if receipt is None:
            mutation = submitted["intent"]["mutation"]  # type: ignore[index]
            _require(isinstance(mutation, dict), "materialization mutation is absent")
            result = _execute_mutation(root, {
                "detail": {"mutation": mutation},
            })
            _boundary(boundary_hook, "after-effect", {
                "operation_id": operation_id,
                "action_kind": "obligation-materialize",
                "claim_id": claim["claim_id"],
            })
            receipt = _store_obligation_receipt(directory, {
                "run_id": submitted["run_id"],
                "operation_id": operation_id,
                "action": "materialize",
                "claim_id": claim["claim_id"],
                "request_hash": claim["request_hash"],
                "obligation_id": obligation_id,
                "obligation_hash": submitted["intent"]["obligation_hash"],  # type: ignore[index]
                "source_decision_hash": submitted["intent"]["source_decision_hash"],  # type: ignore[index]
                "story": submitted["intent"]["story"],  # type: ignore[index]
                "story_path": submitted["intent"]["story_path"],  # type: ignore[index]
                "mutation_fingerprint": result["mutation_fingerprint"],
                "issued_at": claim["reserved_at"],
                "content_safe": True,
            })
        _boundary(boundary_hook, "after-receipt", {
            "operation_id": operation_id,
            "action_kind": "obligation-materialize",
            "claim_id": claim["claim_id"],
            "receipt_hash": receipt["receipt_hash"],
        })
        current = replay_program(
            root, str(submitted["run_id"]), now=observed
        )
        if any(
            item["claim_id"] == claim["claim_id"]
            for item in current["active_claims"]
        ):
            completion = build_program_completion_preview(
                root,
                str(submitted["run_id"]),
                claim_id=str(claim["claim_id"]),
                result="succeeded",
                receipt_hash=str(receipt["receipt_hash"]),
                reason=(
                    f"Materialized obligation {obligation_id} as one "
                    "traced roadmap story."
                ),
                now=observed,
            )
            apply_program_completion(
                root,
                completion,
                completion_token=str(completion["completion_token"]),
                now=observed,
            )
        _boundary(boundary_hook, "after-completion", {
            "operation_id": operation_id,
            "action_kind": "obligation-materialize",
            "claim_id": claim["claim_id"],
            "receipt_hash": receipt["receipt_hash"],
        })
        return {
            "run_id": submitted["run_id"],
            "operation_id": operation_id,
            "story": submitted["intent"]["story"],  # type: ignore[index]
            "story_path": submitted["intent"]["story_path"],  # type: ignore[index]
            "receipt": receipt,
            "idempotent": claim["status"] != "active",
        }


def build_program_obligation_disposition_preview(
    root: Path,
    run_id: str,
    obligation_id: str,
    *,
    to_state: str,
    actor: str,
    authority: str,
    reason: str,
    replacement_id: str | None = None,
    now: str | datetime | None = None,
) -> dict[str, object]:
    root = root.resolve()
    observed = _time(now, "now")
    _path, grant, _plan = _load_documents(root, run_id)
    projection = replay_program(root, run_id, now=observed)
    issues: list[dict[str, str]] = []
    for message in program_freshness_issues(root, grant, projection):
        issues.append(_issue("program-stale", message))
    obligation = _obligation_by_id(projection, obligation_id)
    if obligation is None:
        issues.append(_issue(
            "obligation-not-found",
            "disposition names no durable obligation",
        ))
    elif obligation["state"] != "open":
        issues.append(_issue(
            "obligation-not-open",
            f"obligation is already {obligation['state']}",
        ))
    if "obligation:disposition" not in projection["capabilities"]:
        issues.append(_issue(
            "capability-denied",
            "program grant lacks obligation:disposition",
        ))
    terminal = {"completed", "superseded", "waived", "escalated"}
    if to_state not in terminal:
        issues.append(_issue(
            "disposition-invalid",
            f"unsupported obligation disposition {to_state!r}",
        ))
    if (to_state == "superseded") != (replacement_id is not None):
        issues.append(_issue(
            "replacement-invalid",
            "supersession must name exactly one replacement obligation",
        ))
    if not isinstance(actor, str) or not _SAFE_ID_RE.fullmatch(actor):
        issues.append(_issue(
            "actor-invalid",
            "obligation disposition actor is unsafe",
        ))
    if not isinstance(authority, str) or not _SAFE_ID_RE.fullmatch(authority):
        issues.append(_issue(
            "authority-invalid",
            "obligation disposition authority is unsafe",
        ))
    if (
        replacement_id is not None
        and (
            not isinstance(replacement_id, str)
            or not _SAFE_ID_RE.fullmatch(replacement_id)
        )
    ):
        issues.append(_issue(
            "replacement-invalid",
            "replacement obligation id is unsafe",
        ))
    operator = grant["approval"]["operator"]  # type: ignore[index]
    expected_waiver = (
        f"program-grant:{grant['grant_hash']}/"
        f"operator:{operator['id']}"
    )
    if to_state == "waived" and (
        actor != operator["id"] or authority != expected_waiver
    ):
        issues.append(_issue(
            "waiver-unauthorized",
            "waiver requires the grant's accountable operator and exact grant authority",
        ))
    normalized_reason = (
        " ".join(reason.split()) if isinstance(reason, str) else ""
    )
    intent = {
        "action": "dispose",
        "obligation_id": obligation_id,
        "from_state": obligation["state"] if obligation else None,
        "to_state": to_state,
        "actor": actor,
        "authority": authority,
        "reason": normalized_reason,
        "replacement_id": replacement_id,
        "expected_waiver_authority": (
            expected_waiver if to_state == "waived" else None
        ),
    }
    if (
        not intent["reason"]
        or len(str(intent["reason"]).encode("utf-8")) > 1_000
        or "\x00" in str(intent["reason"])
    ):
        issues.append(_issue(
            "reason-required",
            "obligation disposition requires a bounded accountable reason",
        ))
    unsigned = {
        "kind": PROGRAM_OBLIGATION_DISPOSITION_PREVIEW_KIND,
        "schema_version": PROGRAM_DELIVERY_SCHEMA_VERSION,
        "run_id": run_id,
        "applicable": not issues,
        "issues": issues,
        "observed_at": _format_time(observed),
        "binding": {
            "grant_hash": projection["grant_hash"],
            "ledger_head": projection["ledger_head"],
            "generation": projection["generation"],
            "obligation_hash": (
                obligation["obligation_hash"] if obligation else None
            ),
        },
        "intent": intent,
        "starts_work": False,
        "writes_state": False,
        "mutates_repository": False,
        "mutates_roadmap": False,
    }
    return {**unsigned, "disposition_token": _sha(unsigned)}


def apply_program_obligation_disposition(
    root: Path,
    preview: object,
    *,
    disposition_token: str,
    driver_config: object | None = None,
    now: str | datetime | None = None,
    boundary_hook: BoundaryHook | None = None,
) -> dict[str, object]:
    submitted = _validate_obligation_preview(
        preview,
        kind=PROGRAM_OBLIGATION_DISPOSITION_PREVIEW_KIND,
        token_key="disposition_token",
    )
    _require(
        disposition_token == submitted["disposition_token"],
        "disposition token does not match preview",
    )
    _require(submitted["applicable"], "obligation disposition is not applicable")
    root = root.resolve()
    observed = _time(now or str(submitted["observed_at"]), "now")
    config = load_driver_config(root, driver_config)
    intent = submitted["intent"]
    assert isinstance(intent, dict)
    intent_hash = _sha(intent)
    obligation_id = str(intent["obligation_id"])
    operation_id = _obligation_operation_id(
        str(submitted["run_id"]),
        "dispose",
        obligation_id,
        intent_hash,
    )
    directory = _obligation_operation_dir(
        root,
        str(submitted["run_id"]),
        operation_id,
    )
    with _file_lock(directory.parent / ".lock"):
        plan_path = directory / "plan.json"
        if plan_path.is_file():
            stored = _load_json(plan_path, "obligation disposition plan")
            _require(
                stored.get("preview") == submitted
                and stored.get("token") == disposition_token,
                "stored disposition intent conflicts",
            )
        else:
            current = build_program_obligation_disposition_preview(
                root,
                str(submitted["run_id"]),
                obligation_id,
                to_state=str(intent["to_state"]),
                actor=str(intent["actor"]),
                authority=str(intent["authority"]),
                reason=str(intent["reason"]),
                replacement_id=(
                    str(intent["replacement_id"])
                    if intent["replacement_id"] is not None else None
                ),
                now=str(submitted["observed_at"]),
            )
            _require(current == submitted, "obligation disposition preview is stale")
            _store_obligation_plan(directory, submitted, disposition_token)

        projection = replay_program(
            root, str(submitted["run_id"]), now=observed
        )
        key = f"program-obligation-disposition/{operation_id}"
        claim = next(
            (
                item for item in projection["claims"]
                if item["idempotency_key"] == key
            ),
            None,
        )
        if claim is None:
            claim_preview = build_program_claim_preview(
                root,
                str(submitted["run_id"]),
                category="obligation-disposition",
                subject={
                    "kind": "program-obligation-disposition",
                    "id": obligation_id,
                    "hash": _sha({
                        "obligation_id": obligation_id,
                        "from_state": intent["from_state"],
                        "to_state": intent["to_state"],
                        "actor": intent["actor"],
                        "authority": intent["authority"],
                        "reason": intent["reason"],
                        "replacement_id": intent["replacement_id"],
                    }),
                    "phase": None,
                    "story": None,
                },
                idempotency_key=key,
                reason=(
                    f"Record exact {intent['to_state']} disposition for "
                    f"obligation {obligation_id}."
                ),
                now=observed,
                driver_config=config,
            )
            _require(claim_preview["applicable"], "disposition claim is not applicable")
            claimed = apply_program_claim(
                root,
                claim_preview,
                claim_token=str(claim_preview["claim_token"]),
                now=observed,
                driver_config=config,
            )
            claim = claimed["claim"]
        _require(isinstance(claim, dict), "disposition claim is absent")
        _boundary(boundary_hook, "after-claim", {
            "operation_id": operation_id,
            "action_kind": "obligation-disposition",
            "claim_id": claim["claim_id"],
        })
        receipt = _load_obligation_receipt(directory)
        if receipt is None:
            receipt = _store_obligation_receipt(directory, {
                "run_id": submitted["run_id"],
                "operation_id": operation_id,
                "action": "dispose",
                "claim_id": claim["claim_id"],
                "request_hash": claim["request_hash"],
                "obligation_id": obligation_id,
                "from_state": intent["from_state"],
                "to_state": intent["to_state"],
                "actor": intent["actor"],
                "authority": intent["authority"],
                "reason": intent["reason"],
                "replacement_id": intent["replacement_id"],
                "issued_at": claim["reserved_at"],
                "content_safe": True,
            })
        _boundary(boundary_hook, "after-receipt", {
            "operation_id": operation_id,
            "action_kind": "obligation-disposition",
            "claim_id": claim["claim_id"],
            "receipt_hash": receipt["receipt_hash"],
        })
        current = replay_program(
            root, str(submitted["run_id"]), now=observed
        )
        if any(
            item["claim_id"] == claim["claim_id"]
            for item in current["active_claims"]
        ):
            completion = build_program_completion_preview(
                root,
                str(submitted["run_id"]),
                claim_id=str(claim["claim_id"]),
                result="succeeded",
                receipt_hash=str(receipt["receipt_hash"]),
                reason=(
                    f"Recorded exact {intent['to_state']} obligation "
                    "disposition receipt."
                ),
                now=observed,
            )
            apply_program_completion(
                root,
                completion,
                completion_token=str(completion["completion_token"]),
                now=observed,
            )
        disposed = dispose_program_obligation(
            root,
            str(submitted["run_id"]),
            claim_id=str(claim["claim_id"]),
            obligation_id=obligation_id,
            to_state=str(intent["to_state"]),
            actor=str(intent["actor"]),
            authority=str(intent["authority"]),
            reason=str(intent["reason"]),
            replacement_id=(
                str(intent["replacement_id"])
                if intent["replacement_id"] is not None else None
            ),
            now=observed,
        )
        _boundary(boundary_hook, "after-completion", {
            "operation_id": operation_id,
            "action_kind": "obligation-disposition",
            "claim_id": claim["claim_id"],
            "receipt_hash": receipt["receipt_hash"],
        })
        return {
            "run_id": submitted["run_id"],
            "operation_id": operation_id,
            "obligation": disposed["obligation"],
            "receipt": receipt,
            "idempotent": bool(disposed.get("idempotent")),
        }
