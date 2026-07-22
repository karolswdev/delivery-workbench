"""Durable operator notifications (docs/signals.md).

Notification facts are DERIVED, never invented: each one is a pure
function of the hash-chained run ledgers and signal chains. Only two
small append-only stores exist under ``.git/pmo-notifications/`` — the
acknowledgement log and the delivery log — and deleting any cache
changes no derived answer. Outbound content carries facts, references,
and typed-response instructions only; never a token, an apply command,
or a third-party content body.
"""

import json
import os
from pathlib import Path

from .model import DwError
from .orchestration import canonical_json
from .orchestration_run import run_inventory
from .signals import _iter_channels, replay_channel
from .signals import _sha as _signal_sha

NOTIFICATIONS_KIND = "delivery-workbench-notifications"
NOTIFICATIONS_SCHEMA_VERSION = 1

NOTIFICATION_KINDS = (
    "checkpoint-pending",
    "request-pending",
    "request-republished",
    "request-expired",
    "awaiting-certification",
    "run-blocked",
    "nudge-budget-exhausted",
    "branch-signal",
)

_DELIVERY_CEILING = 3

_SIGNAL_STATUSES = {"ci-failed", "changes-requested", "merge-conflict"}


def _store_dir(root):
    git_dir = Path(root) / ".git"
    if not git_dir.is_dir():
        raise DwError("notifications need a repository with a .git directory")
    store = git_dir / "pmo-notifications"
    if store.is_symlink():
        raise DwError("refusing symlinked notification store")
    return store


def _read_jsonl(path):
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return []
    records = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            raise DwError(f"corrupt notification store line in {path.name}")
        if isinstance(record, dict):
            records.append(record)
    return records


def _append_jsonl(root, name, record):
    store = _store_dir(root)
    store.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = store / name
    data = (canonical_json(record) + "\n").encode("utf-8")
    with path.open("ab", buffering=0) as handle:
        if handle.write(data) != len(data):
            raise DwError("short write while appending the notification store")
        os.fsync(handle.fileno())
    os.chmod(path, 0o600)


def load_notification_config(root):
    """Operator-local delivery preferences; absent file means defaults."""
    path = _store_dir(root) / "config.json"
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        return {"branch_signals": False}
    except ValueError:
        raise DwError("notification config is not valid JSON")
    if not isinstance(config, dict):
        raise DwError("notification config must be a JSON object")
    return {"branch_signals": bool(config.get("branch_signals", False))}


def _notification_id(payload):
    return "ntf-" + _signal_sha(payload).split(":", 1)[1][:24]


def _run_notifications(root, now=None):
    facts = []
    for entry in run_inventory(root, now=now).get("runs", []):
        if not entry.get("valid"):
            continue
        run_id = str(entry["run_id"])
        projection = entry["run"]
        for request in projection.get("outstanding_requests", []):
            request_kind = str(request.get("kind") or "")
            kind = (
                "checkpoint-pending"
                if request_kind == "checkpoint"
                else "request-pending"
            )
            payload = {
                "kind": kind,
                "run_id": run_id,
                "correlation_id": request.get("correlation_id"),
                "seq": request.get("opened_seq"),
            }
            facts.append({
                "id": _notification_id(payload),
                "kind": kind,
                "run_id": run_id,
                "node": str(request.get("origin_node") or request.get("origin") or ""),
                "detail": (
                    "a named human checkpoint is waiting for a decision"
                    if request_kind == "checkpoint"
                    else "an uncovered nudge preview is waiting for a decision"
                ),
                "request": {
                    "correlation_id": request.get("correlation_id"),
                    "response_schema": request.get("response_schema"),
                    "boundary": "dw run request (fresh exact act token)",
                },
            })
            for republish in request.get("republished", []):
                republished_payload = {
                    "kind": "request-republished",
                    "run_id": run_id,
                    "correlation_id": request.get("correlation_id"),
                    "generation": republish.get("generation"),
                }
                facts.append({
                    "id": _notification_id(republished_payload),
                    "kind": "request-republished",
                    "run_id": run_id,
                    "node": str(request.get("origin_node") or request.get("origin") or ""),
                    "detail": "an outstanding request was republished after resume or restart",
                    "request": {
                        "correlation_id": request.get("correlation_id"),
                        "response_schema": request.get("response_schema"),
                        "boundary": "dw run request (fresh exact act token)",
                    },
                })
        for request in projection.get("request_history", []):
            if request.get("status") != "expired":
                continue
            payload = {
                "kind": "request-expired",
                "run_id": run_id,
                "correlation_id": request.get("correlation_id"),
                "seq": request.get("refusal_seq"),
            }
            facts.append({
                "id": _notification_id(payload),
                "kind": "request-expired",
                "run_id": run_id,
                "node": str(request.get("origin_node") or request.get("origin") or ""),
                "detail": "an outstanding request expired into a recorded refusal",
            })
        for item in projection.get("nudges", []):
            if not item.get("delivered") and item.get("reason") == "nudge-budget-exhausted":
                payload = {
                    "kind": "nudge-budget-exhausted", "run_id": run_id,
                    "seq": item["seq"],
                }
                facts.append({
                    "id": _notification_id(payload),
                    "kind": "nudge-budget-exhausted",
                    "run_id": run_id,
                    "node": str(item.get("rule") or ""),
                    "detail": "the run's nudge budget is exhausted; no further nudges will deliver",
                })
        state = str(projection["state"])
        if state == "awaiting-certification":
            payload = {
                "kind": "awaiting-certification", "run_id": run_id,
                "events": projection["ledger_events"],
            }
            facts.append({
                "id": _notification_id(payload),
                "kind": "awaiting-certification",
                "run_id": run_id,
                "node": "",
                "detail": "the run finished its granted work; certification and commit stay yours",
            })
        elif state == "blocked":
            payload = {"kind": "run-blocked", "run_id": run_id,
                       "events": projection["ledger_events"]}
            facts.append({
                "id": _notification_id(payload),
                "kind": "run-blocked",
                "run_id": run_id,
                "node": "",
                "detail": "the run stopped at a recorded blocked state; see dw run view",
            })
    return facts


def _branch_signal_notifications(root):
    config = load_notification_config(root)
    if not config.get("branch_signals"):
        return []
    facts = []
    bound_channels = set()
    for entry in run_inventory(root).get("runs", []):
        channel = str((entry.get("run") or {}).get("signal_channel") or "")
        if channel:
            bound_channels.add(channel)
    for remote, branch in _iter_channels(root):
        try:
            projection = replay_channel(root, remote, branch)
        except DwError:
            continue
        if projection["channel"] in bound_channels:
            continue
        status = str(projection["status"])
        if status not in _SIGNAL_STATUSES:
            continue
        payload = {
            "kind": "branch-signal", "channel": projection["channel"],
            "status": status, "head": projection["ledger_head"],
        }
        facts.append({
            "id": _notification_id(payload),
            "kind": "branch-signal",
            "run_id": "",
            "node": projection["channel"],
            "detail": f"observed branch is {status} with no run bound to it",
        })
    return facts


def build_notifications(root, now=None):
    """The read model shared byte-for-byte by CLI, MCP, and HTTP."""
    root = Path(root)
    derived = _run_notifications(root, now=now) + _branch_signal_notifications(root)
    store = _store_dir(root)
    acked = {
        str(record.get("id")) for record in _read_jsonl(store / "acks.jsonl")
    }
    deliveries = {}
    for record in _read_jsonl(store / "deliveries.jsonl"):
        entry = deliveries.setdefault(
            str(record.get("id")), {"attempts": 0, "delivered": False}
        )
        entry["attempts"] += 1
        if record.get("ok"):
            entry["delivered"] = True
    seen = set()
    notifications = []
    for fact in derived:
        if fact["id"] in seen:
            continue
        seen.add(fact["id"])
        delivery = deliveries.get(fact["id"], {"attempts": 0, "delivered": False})
        entry = dict(
            fact,
            unread=fact["id"] not in acked,
            delivered=bool(delivery["delivered"]),
            delivery_attempts=int(delivery["attempts"]),
        )
        entry["outbound"] = render_outbound(entry)
        notifications.append(entry)
    notifications.sort(key=lambda item: (item["kind"], item["id"]))
    return {
        "kind": NOTIFICATIONS_KIND,
        "schema_version": NOTIFICATIONS_SCHEMA_VERSION,
        "notifications": notifications,
        "unread": sum(1 for item in notifications if item["unread"]),
        "starts_work": False,
        "writes_events": False,
    }


def acknowledge_notification(root, notification_id, now_ts):
    """Idempotent, receipted acknowledgement of one derived notification."""
    root = Path(root)
    inventory = build_notifications(root)
    match = next(
        (item for item in inventory["notifications"]
         if item["id"] == notification_id),
        None,
    )
    if match is None:
        raise DwError(f"no current notification with id {notification_id!r}")
    if not match["unread"]:
        return {"id": notification_id, "acknowledged": True, "changed": False}
    _append_jsonl(root, "acks.jsonl", {"id": notification_id, "ts": now_ts})
    return {"id": notification_id, "acknowledged": True, "changed": True}


def render_outbound(notification):
    """The content-safe outbound message body for one notification.

    Facts, references, and the typed-response instruction only. Never a
    token, an apply command, or third-party content.
    """
    lines = [f"delivery-workbench: {notification['kind']}"]
    if notification.get("run_id"):
        lines.append(f"run: {notification['run_id']}")
    if notification.get("node"):
        lines.append(f"where: {notification['node']}")
    lines.append(notification.get("detail", ""))
    request = notification.get("request")
    if request:
        options = request.get("response_schema", {}).get(
            "decision", ["approve", "reject"]
        )
        lines.append(
            "to decide, reply: "
            f"/decision {request['correlation_id']} {'|'.join(options)}"
        )
        lines.append(
            "the decision applies only through the local exact-token "
            "request boundary"
        )
    lines.append(f"ack: {notification['id']}")
    return "\n".join(line for line in lines if line)


def pending_deliveries(root):
    """Unacknowledged, undelivered notifications inside the retry ceiling."""
    inventory = build_notifications(root)
    return [
        item for item in inventory["notifications"]
        if item["unread"]
        and not item["delivered"]
        and item["delivery_attempts"] < _DELIVERY_CEILING
    ]


def record_delivery(root, notification_id, channel, ok, reason, now_ts):
    _append_jsonl(root, "deliveries.jsonl", {
        "id": notification_id, "channel": str(channel), "ok": bool(ok),
        "reason": str(reason or "")[:200], "ts": now_ts,
    })


def resolve_correlation(root, correlation_id):
    """Map a typed response's correlation id back to its pending checkpoint.

    Refuses stale or unknown correlations: the id must match a currently
    pending checkpoint-pending notification derived from the ledger now.
    """
    inventory = build_notifications(root)
    match = next(
        (
            item for item in inventory["notifications"]
            if item["kind"] in {
                "checkpoint-pending", "request-pending", "request-republished",
            }
            and item.get("request", {}).get("correlation_id") == correlation_id
        ),
        None,
    )
    if match is None:
        raise DwError(
            "stale or unknown checkpoint correlation id; no decision was applied"
        )
    return match
