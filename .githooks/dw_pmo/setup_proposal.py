"""Pure front-door setup proposal contract.

A setup proposal records what a conversation may draft: project identity,
roadmap and optional tracked policy, plus local non-secret driver bindings.  It
never chooses a project for the operator, writes canon, creates a grant, starts
work, certifies a contract, or commits.  Previewing the same document does not
change those exclusions.

The contract is ``delivery-workbench-setup-proposal@1`` and is documented in
``docs/setup-proposal.md``.  Parsing, validation, canonical serialization, and
journey-state transitions are deterministic, standard-library-only, and have
no filesystem, process, clock, random, or network input.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Set

from .model import DwError


SCHEMA = "delivery-workbench-setup-proposal@1"
JOURNEY_STATES = (
    "uninitialized",
    "rails-ready",
    "draft",
    "reviewed",
    "configured",
    "grant-previewed",
)
PROVENANCE_KINDS = ("user-answer", "repository-fact", "recommendation")
SOURCE_MODES = ("build", "maintain")

MAX_PROPOSAL_BYTES = 1_000_000
MAX_ID = 128
MAX_PREFIX = 16
MAX_TITLE = 300
MAX_NOTE = 2_000
MAX_IDEA = 20_000
MAX_TEXT = 5_000
MAX_PHASES = 100
MAX_STORIES_PER_PHASE = 200
MAX_SCOPE_ITEMS = 100
MAX_CRITERIA = 100
MAX_DEPENDENCIES = 100
MAX_UNRESOLVED_QUESTIONS = 100
MAX_DRIVER_BINDINGS = 100
MAX_POLICY_DOCUMENTS = 100
MAX_OPAQUE_DOCUMENT_BYTES = 262_144
MAX_OPAQUE_DEPTH = 20
MAX_OPAQUE_LIST_ITEMS = 2_000
MAX_OPAQUE_OBJECT_FIELDS = 2_000
MAX_OPAQUE_STRING = 32_768

_SAFE_SLUG_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_SAFE_PREFIX_RE = re.compile(r"^[A-Z][A-Z0-9]{0,15}$")
_SAFE_PROFILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SECRET_KEY_RE = re.compile(
    r"(?:secret|token|credential|password|api[_-]?key)", re.I
)

_INERTNESS_KEYS = {"starts_work", "creates_grant", "certifies", "commits"}
_PROPOSAL_KEYS = {
    "schema",
    "state",
    "project",
    "source_intent",
    "tracked_content",
    "local_content",
    "unresolved_questions",
} | _INERTNESS_KEYS
_PROJECT_KEYS = {"slug", "prefix", "title", "provenance"}
_SOURCE_INTENT_KEYS = {"idea", "mode", "provenance"}
_TRACKED_KEYS = {"roadmap", "policy"}
_LOCAL_KEYS = {"driver_bindings"}
_ROADMAP_KEYS = {"phases", "exit_criteria"}
_PHASE_KEYS = {"number", "title", "goal", "provenance", "stories"}
_STORY_KEYS = {
    "id_sketch",
    "title",
    "problem",
    "scope_in",
    "scope_out",
    "acceptance_criteria",
    "dependencies",
    "provenance",
}
_TEXT_ITEM_KEYS = {"text", "provenance"}
_DEPENDENCY_KEYS = {"id_sketch", "provenance"}
_PROVENANCE_KEYS = {"kind", "source_note"}
_POLICY_KEYS = {"program", "workflows", "organization", "rubrics", "provenance"}
_POLICY_DOCUMENT_KEYS = {"document", "provenance"}
_DRIVER_KEYS = {"adapter", "model", "provider", "provenance"}
_QUESTION_KEYS = {"question", "provenance"}


class _DuplicateJSONKey(ValueError):
    pass


def _pointer(parent: str, item: object) -> str:
    token = str(item).replace("~", "~0").replace("/", "~1")
    return (parent + "/" + token) if parent else ("/" + token)


def _refuse(pointer: str, message: str) -> None:
    raise DwError("%s: %s" % (pointer or "/", message))


def _exact_object(value: object, keys: Set[str], pointer: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        _refuse(pointer, "must be an object")
    if any(not isinstance(key, str) for key in value):
        _refuse(_pointer(pointer, "<key>"), "object keys must be strings")
    unknown = sorted(set(value) - keys)
    missing = sorted(keys - set(value))
    if unknown:
        _refuse(_pointer(pointer, unknown[0]), "unknown field")
    if missing:
        _refuse(_pointer(pointer, missing[0]), "field is required")
    return value


def _bounded_string(
    value: object,
    pointer: str,
    maximum: int,
    pattern: re.Pattern = None,
    allow_empty: bool = False,
) -> str:
    if (
        not isinstance(value, str)
        or (not value and not allow_empty)
        or len(value) > maximum
        or "\x00" in value
    ):
        _refuse(pointer, "must be a bounded string (maximum %d characters)" % maximum)
    if pattern is not None and not pattern.fullmatch(value):
        _refuse(pointer, "must use the contracted identifier form")
    return value


def _bounded_list(
    value: object,
    pointer: str,
    maximum: int,
    allow_empty: bool = True,
) -> List[Any]:
    if (
        not isinstance(value, list)
        or len(value) > maximum
        or (not allow_empty and not value)
    ):
        minimum = "1" if not allow_empty else "0"
        _refuse(
            pointer,
            "must be a bounded list (%s through %d items)" % (minimum, maximum),
        )
    return value


def _validate_provenance(value: object, pointer: str) -> None:
    raw = _exact_object(value, _PROVENANCE_KEYS, pointer)
    if raw["kind"] not in PROVENANCE_KINDS:
        _refuse(
            _pointer(pointer, "kind"),
            "must be user-answer, repository-fact, or recommendation",
        )
    _bounded_string(raw["source_note"], _pointer(pointer, "source_note"), MAX_NOTE)


def _validate_text_item(value: object, pointer: str) -> None:
    raw = _exact_object(value, _TEXT_ITEM_KEYS, pointer)
    _bounded_string(raw["text"], _pointer(pointer, "text"), MAX_TEXT)
    _validate_provenance(raw["provenance"], _pointer(pointer, "provenance"))


def _validate_text_items(
    value: object,
    pointer: str,
    maximum: int,
    allow_empty: bool = True,
) -> None:
    items = _bounded_list(value, pointer, maximum, allow_empty=allow_empty)
    for index, item in enumerate(items):
        _validate_text_item(item, _pointer(pointer, index))


def _validate_story(value: object, pointer: str) -> None:
    raw = _exact_object(value, _STORY_KEYS, pointer)
    _bounded_string(raw["id_sketch"], _pointer(pointer, "id_sketch"), MAX_ID)
    _bounded_string(raw["title"], _pointer(pointer, "title"), MAX_TITLE)
    _bounded_string(raw["problem"], _pointer(pointer, "problem"), MAX_TEXT)
    _validate_text_items(raw["scope_in"], _pointer(pointer, "scope_in"), MAX_SCOPE_ITEMS)
    _validate_text_items(raw["scope_out"], _pointer(pointer, "scope_out"), MAX_SCOPE_ITEMS)
    _validate_text_items(
        raw["acceptance_criteria"],
        _pointer(pointer, "acceptance_criteria"),
        MAX_CRITERIA,
        allow_empty=False,
    )
    dependencies = _bounded_list(
        raw["dependencies"], _pointer(pointer, "dependencies"), MAX_DEPENDENCIES
    )
    for index, dependency in enumerate(dependencies):
        dependency_pointer = _pointer(_pointer(pointer, "dependencies"), index)
        item = _exact_object(dependency, _DEPENDENCY_KEYS, dependency_pointer)
        _bounded_string(
            item["id_sketch"], _pointer(dependency_pointer, "id_sketch"), MAX_ID
        )
        _validate_provenance(
            item["provenance"], _pointer(dependency_pointer, "provenance")
        )
    _validate_provenance(raw["provenance"], _pointer(pointer, "provenance"))


def _validate_roadmap(value: object, pointer: str) -> None:
    raw = _exact_object(value, _ROADMAP_KEYS, pointer)
    phases = _bounded_list(
        raw["phases"], _pointer(pointer, "phases"), MAX_PHASES, allow_empty=False
    )
    seen_numbers = set()
    for index, phase in enumerate(phases):
        phase_pointer = _pointer(_pointer(pointer, "phases"), index)
        item = _exact_object(phase, _PHASE_KEYS, phase_pointer)
        number = item["number"]
        if isinstance(number, bool) or not isinstance(number, int) or not 0 <= number <= 9999:
            _refuse(_pointer(phase_pointer, "number"), "must be an integer from 0 through 9999")
        if number in seen_numbers:
            _refuse(_pointer(phase_pointer, "number"), "must be unique in the roadmap draft")
        seen_numbers.add(number)
        _bounded_string(item["title"], _pointer(phase_pointer, "title"), MAX_TITLE)
        _bounded_string(item["goal"], _pointer(phase_pointer, "goal"), MAX_TEXT)
        _validate_provenance(item["provenance"], _pointer(phase_pointer, "provenance"))
        stories = _bounded_list(
            item["stories"],
            _pointer(phase_pointer, "stories"),
            MAX_STORIES_PER_PHASE,
            allow_empty=False,
        )
        for story_index, story in enumerate(stories):
            _validate_story(
                story, _pointer(_pointer(phase_pointer, "stories"), story_index)
            )
    _validate_text_items(
        raw["exit_criteria"],
        _pointer(pointer, "exit_criteria"),
        MAX_CRITERIA,
        allow_empty=False,
    )


def _opaque_json_size(value: object) -> int:
    try:
        return len(
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        )
    except (TypeError, ValueError, OverflowError):
        return MAX_OPAQUE_DOCUMENT_BYTES + 1


def _validate_opaque_json(value: object, pointer: str, depth: int = 0) -> None:
    if depth > MAX_OPAQUE_DEPTH:
        _refuse(pointer, "exceeds the opaque document depth bound")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        _refuse(pointer, "must not contain floating-point values")
    if isinstance(value, str):
        _bounded_string(value, pointer, MAX_OPAQUE_STRING, allow_empty=True)
        return
    if isinstance(value, list):
        items = _bounded_list(value, pointer, MAX_OPAQUE_LIST_ITEMS)
        for index, item in enumerate(items):
            _validate_opaque_json(item, _pointer(pointer, index), depth + 1)
        return
    if isinstance(value, dict):
        if len(value) > MAX_OPAQUE_OBJECT_FIELDS:
            _refuse(pointer, "exceeds the opaque object field bound")
        for key, item in value.items():
            _bounded_string(key, _pointer(pointer, "<key>"), MAX_ID, allow_empty=False)
            _validate_opaque_json(item, _pointer(pointer, key), depth + 1)
        return
    _refuse(pointer, "must contain JSON values only")


def _validate_policy_document(value: object, pointer: str) -> None:
    raw = _exact_object(value, _POLICY_DOCUMENT_KEYS, pointer)
    document = raw["document"]
    if not isinstance(document, dict):
        _refuse(_pointer(pointer, "document"), "must be an opaque JSON object")
    _validate_opaque_json(document, _pointer(pointer, "document"))
    if _opaque_json_size(document) > MAX_OPAQUE_DOCUMENT_BYTES:
        _refuse(
            _pointer(pointer, "document"),
            "must be at most %d canonical JSON bytes" % MAX_OPAQUE_DOCUMENT_BYTES,
        )
    _validate_provenance(raw["provenance"], _pointer(pointer, "provenance"))


def _validate_policy(value: object, pointer: str) -> None:
    if value is None:
        return
    raw = _exact_object(value, _POLICY_KEYS, pointer)
    _validate_policy_document(raw["program"], _pointer(pointer, "program"))
    workflows = _bounded_list(
        raw["workflows"],
        _pointer(pointer, "workflows"),
        MAX_POLICY_DOCUMENTS,
        allow_empty=False,
    )
    for index, document in enumerate(workflows):
        _validate_policy_document(document, _pointer(_pointer(pointer, "workflows"), index))
    _validate_policy_document(raw["organization"], _pointer(pointer, "organization"))
    rubrics = _bounded_list(
        raw["rubrics"],
        _pointer(pointer, "rubrics"),
        MAX_POLICY_DOCUMENTS,
        allow_empty=False,
    )
    for index, document in enumerate(rubrics):
        _validate_policy_document(document, _pointer(_pointer(pointer, "rubrics"), index))
    _validate_provenance(raw["provenance"], _pointer(pointer, "provenance"))


def _contains_secret_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _SECRET_KEY_RE.search(str(key)) or _contains_secret_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_secret_key(item) for item in value)
    return False


def _validate_local_content(value: object, pointer: str) -> None:
    raw = _exact_object(value, _LOCAL_KEYS, pointer)
    bindings = raw["driver_bindings"]
    if not isinstance(bindings, dict) or len(bindings) > MAX_DRIVER_BINDINGS:
        _refuse(
            _pointer(pointer, "driver_bindings"),
            "must be an object with at most %d profiles" % MAX_DRIVER_BINDINGS,
        )
    if any(not isinstance(name, str) for name in bindings):
        _refuse(
            _pointer(_pointer(pointer, "driver_bindings"), "<key>"),
            "profile names must be strings",
        )
    for name in sorted(bindings):
        profile_pointer = _pointer(_pointer(pointer, "driver_bindings"), name)
        _bounded_string(name, profile_pointer, MAX_ID, pattern=_SAFE_PROFILE_RE)
        if _SECRET_KEY_RE.search(name):
            _refuse(
                profile_pointer,
                "profile names may not match credential, token, password, secret, or API-key patterns",
            )
        if _contains_secret_key(bindings[name]):
            _refuse(
                profile_pointer,
                "may not contain credential, token, password, secret, or API-key fields",
            )
        item = _exact_object(bindings[name], _DRIVER_KEYS, profile_pointer)
        _bounded_string(item["adapter"], _pointer(profile_pointer, "adapter"), MAX_ID)
        _bounded_string(item["model"], _pointer(profile_pointer, "model"), MAX_ID)
        _bounded_string(
            item["provider"], _pointer(profile_pointer, "provider"), MAX_ID
        )
        _validate_provenance(
            item["provenance"], _pointer(profile_pointer, "provenance")
        )


def _validate_inertness(value: Dict[str, Any], pointer: str = "") -> None:
    for field in sorted(_INERTNESS_KEYS):
        if field not in value:
            _refuse(_pointer(pointer, field), "field is required and must be false")
        if value[field] is not False:
            _refuse(_pointer(pointer, field), "must be false")


def _raw_canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise DwError("/: must contain deterministic JSON values") from exc


def validate_proposal(proposal: object) -> Dict[str, Any]:
    """Validate one closed, bounded, inert setup proposal and return it."""
    raw = _exact_object(proposal, _PROPOSAL_KEYS, "")
    if raw["schema"] != SCHEMA:
        _refuse("/schema", "unsupported setup proposal schema")
    if raw["state"] not in JOURNEY_STATES:
        _refuse("/state", "must be a contracted journey state")
    _validate_inertness(raw)

    project = _exact_object(raw["project"], _PROJECT_KEYS, "/project")
    _bounded_string(project["slug"], "/project/slug", MAX_ID, pattern=_SAFE_SLUG_RE)
    if project["slug"] in {"preview", "apply"}:
        _refuse("/project/slug", "preview and apply are reserved setup subverbs")
    _bounded_string(
        project["prefix"], "/project/prefix", MAX_PREFIX, pattern=_SAFE_PREFIX_RE
    )
    _bounded_string(project["title"], "/project/title", MAX_TITLE)
    _validate_provenance(project["provenance"], "/project/provenance")

    intent = _exact_object(raw["source_intent"], _SOURCE_INTENT_KEYS, "/source_intent")
    _bounded_string(intent["idea"], "/source_intent/idea", MAX_IDEA)
    if intent["mode"] not in SOURCE_MODES:
        _refuse("/source_intent/mode", "must be build or maintain")
    _validate_provenance(intent["provenance"], "/source_intent/provenance")

    tracked = _exact_object(raw["tracked_content"], _TRACKED_KEYS, "/tracked_content")
    _validate_roadmap(tracked["roadmap"], "/tracked_content/roadmap")
    _validate_policy(tracked["policy"], "/tracked_content/policy")
    _validate_local_content(raw["local_content"], "/local_content")

    questions = _bounded_list(
        raw["unresolved_questions"],
        "/unresolved_questions",
        MAX_UNRESOLVED_QUESTIONS,
    )
    for index, question in enumerate(questions):
        pointer = _pointer("/unresolved_questions", index)
        item = _exact_object(question, _QUESTION_KEYS, pointer)
        _bounded_string(item["question"], _pointer(pointer, "question"), MAX_TEXT)
        _validate_provenance(item["provenance"], _pointer(pointer, "provenance"))

    canonical = _raw_canonical_json(raw)
    if len(canonical.encode("utf-8")) > MAX_PROPOSAL_BYTES:
        _refuse("/", "must be at most %d canonical JSON bytes" % MAX_PROPOSAL_BYTES)
    # This is also a fitness assertion for every accepted value: canonical JSON
    # must reproduce the exact validated JSON data without coercion.
    if json.loads(canonical) != raw:
        _refuse("/", "must round-trip through canonical JSON")
    return raw


def validate_preview(preview: object) -> Dict[str, Any]:
    """Validate a proposal-shaped preview under the same inert contract."""
    return validate_proposal(preview)


def canonical_json(proposal: object) -> str:
    """Return byte-stable canonical JSON after full proposal validation."""
    return _raw_canonical_json(validate_proposal(proposal))


def _object_without_duplicates(pairs: List[Any]) -> Dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey("duplicate JSON object key: %s" % key)
        result[key] = value
    return result


def load_proposal(text: object) -> Dict[str, Any]:
    """Parse and validate proposal JSON without consulting ambient state."""
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except UnicodeError as exc:
            raise DwError("/: setup proposal must be UTF-8 JSON") from exc
    if not isinstance(text, str) or len(text) > MAX_PROPOSAL_BYTES:
        _refuse("/", "setup proposal JSON must be a bounded string or bytes")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError("non-finite JSON number: %s" % token)
            ),
        )
    except (_DuplicateJSONKey, ValueError, json.JSONDecodeError) as exc:
        raise DwError("/: cannot parse setup proposal JSON: %s" % exc) from exc
    return validate_proposal(value)


def transition_state(current: object, target: object) -> str:
    """Return one explicit allowed journey transition; refuse every other pair."""
    if current not in JOURNEY_STATES:
        _refuse("/state/from", "must be a contracted journey state")
    if target not in JOURNEY_STATES:
        _refuse("/state/to", "must be a contracted journey state")
    current_index = JOURNEY_STATES.index(current)
    allowed = (
        target == JOURNEY_STATES[current_index + 1]
        if current_index + 1 < len(JOURNEY_STATES)
        else False
    )
    if current == "reviewed" and target == "draft":
        allowed = True
    if not allowed:
        _refuse(
            "/state",
            "transition from %s to %s is not permitted" % (current, target),
        )
    return target
