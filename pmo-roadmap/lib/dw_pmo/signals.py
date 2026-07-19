"""Outward signal observation (docs/signals.md).

Authority-free by construction: every function here either reads the forge
through a provider port or writes append-only facts under
``.git/pmo-signals/``. Nothing in this module starts work, mutates the
forge, the operator tree, a run, or an agent; every surface document is
stamped ``starts_work: False``.
"""

import fcntl
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .gitio import current_branch, run_git
from .model import DwError
from .orchestration import canonical_json

SIGNAL_EVENT_KIND = "delivery-workbench-signal-event"
SIGNAL_SCHEMA_VERSION = 1
SIGNALS_KIND = "delivery-workbench-signals"
SIGNALS_OBSERVE_KIND = "delivery-workbench-signals-observe"

FACT_KINDS = (
    "pr",
    "pr-check",
    "pr-review-thread",
    "pr-mergeability",
    "observe-refusal",
)

_EVENT_KEYS = {
    "kind",
    "schema_version",
    "channel",
    "seq",
    "fact",
    "ts",
    "detail",
    "prev_hash",
    "event_hash",
}

# Per-fact exact detail keys. Values are scalars only; third-party prose
# (review bodies, CI log text) never has a key here, which is the
# content-exclusion rule enforced at append and re-verified at replay.
_FACT_DETAIL_KEYS = {
    "pr": {"number", "state", "draft", "head", "base", "url"},
    "pr-check": {"number", "name", "status", "conclusion", "url"},
    "pr-review-thread": {
        "number",
        "unresolved",
        "resolved",
        "changes_requested",
        "approved",
        "reviewers",
        "url",
    },
    "pr-mergeability": {"number", "mergeable", "reason"},
    "observe-refusal": {"provider", "reason"},
}

_REFUSAL_REASONS = {
    "unauthenticated",
    "rate-limited",
    "forge-error",
    "network-error",
}

_CHECK_FAILED = {"failure", "timed_out", "startup_failure"}

STATUS_PRECEDENCE = (
    "merged",
    "closed-unmerged",
    "ci-failed",
    "merge-conflict",
    "changes-requested",
    "ci-pending",
    "approved",
    "mergeable",
    "pr-open",
    "unobserved",
)


def _sha(value):
    return "sha256:" + hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def _format_time(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _parse_time(value, field):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        raise DwError("signal event %s is not a valid timestamp" % field)
    if parsed.tzinfo is None:
        raise DwError("signal event %s must carry a timezone" % field)
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _git_dir(root):
    root = Path(root)
    candidate = root / ".git"
    if candidate.is_dir():
        return candidate
    raise DwError("signals need a repository with a .git directory")


def signal_store_dir(root):
    store = _git_dir(root) / "pmo-signals"
    if store.is_symlink():
        raise DwError("refusing symlinked signal store")
    return store


@contextmanager
def _store_lock(root):
    store = signal_store_dir(root)
    store.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(store, 0o700)
    lock_path = store / ".signals.lock"
    with lock_path.open("a+", encoding="utf-8") as handle:
        os.chmod(lock_path, 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield store
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _channel_name(remote, branch):
    return "%s/%s" % (remote, branch)


def _channel_dir(root, remote, branch):
    store = signal_store_dir(root)
    encoded_remote = urllib.parse.quote(str(remote), safe="")
    encoded_branch = urllib.parse.quote(str(branch), safe="")
    channel = store / encoded_remote / encoded_branch
    if channel.is_symlink() or (
        channel.exists() and not channel.is_dir()
    ):
        raise DwError("refusing non-directory signal channel path")
    return channel


def _write_json(path, value):
    fd, temp_name = tempfile.mkstemp(
        prefix=".%s." % path.name, dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    except OSError:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _write_cache(channel_dir, projection):
    """The chain is authoritative; a disposable cache can always vanish."""
    try:
        _write_json(channel_dir / "projection.json", projection)
    except OSError:
        return


def _validate_detail(fact, detail):
    allowed = _FACT_DETAIL_KEYS.get(fact)
    if allowed is None:
        raise DwError("unknown signal fact kind %r" % fact)
    if not isinstance(detail, dict) or set(detail) != allowed:
        raise DwError("signal fact %s has non-exact detail keys" % fact)
    for key, value in detail.items():
        if isinstance(value, bool) or isinstance(value, int):
            continue
        if not isinstance(value, str):
            raise DwError(
                "signal fact %s detail %s must be a scalar" % (fact, key)
            )
        if len(value) > 200 or "\n" in value or "\x00" in value:
            raise DwError(
                "signal fact %s detail %s is unbounded or unsafe"
                % (fact, key)
            )
    if fact == "observe-refusal" and detail["reason"] not in _REFUSAL_REASONS:
        raise DwError("observe refusal reason must be content-free")


def _event_document(channel, seq, fact, detail, prev_hash, now):
    _validate_detail(fact, detail)
    unsigned = {
        "kind": SIGNAL_EVENT_KIND,
        "schema_version": SIGNAL_SCHEMA_VERSION,
        "channel": channel,
        "seq": seq,
        "fact": fact,
        "ts": _format_time(now),
        "detail": detail,
        "prev_hash": prev_hash,
    }
    return dict(unsigned, event_hash=_sha(unsigned))


def _read_events(path, channel):
    try:
        raw = path.read_bytes()
    except OSError:
        raise DwError("signal chain is unreadable")
    if not raw or not raw.endswith(b"\n"):
        raise DwError("signal chain is empty or truncated")
    events = []
    previous = None
    previous_time = None
    for offset, line in enumerate(raw.splitlines()):
        try:
            event = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise DwError("signal chain line %d is corrupt" % (offset + 1))
        if not isinstance(event, dict) or set(event) != _EVENT_KEYS:
            raise DwError(
                "signal chain line %d has non-exact keys" % (offset + 1)
            )
        if (
            event["kind"] != SIGNAL_EVENT_KIND
            or event["schema_version"] != SIGNAL_SCHEMA_VERSION
            or event["channel"] != channel
            or event["seq"] != offset
            or event["prev_hash"] != previous
        ):
            raise DwError(
                "signal chain line %d breaks sequence or chain identity"
                % (offset + 1)
            )
        unsigned = {
            key: value
            for key, value in event.items()
            if key != "event_hash"
        }
        if event["event_hash"] != _sha(unsigned):
            raise DwError(
                "signal chain line %d hash check failed" % (offset + 1)
            )
        _validate_detail(event["fact"], event["detail"])
        timestamp = _parse_time(event["ts"], "ts")
        if previous_time is not None and timestamp < previous_time:
            raise DwError(
                "signal chain line %d moves time backwards" % (offset + 1)
            )
        previous = str(event["event_hash"])
        previous_time = timestamp
        events.append(event)
    return events


def _fact_key(fact, detail):
    if fact == "pr":
        return canonical_json(["pr", detail["number"]])
    if fact == "pr-check":
        return canonical_json(["pr-check", detail["number"], detail["name"]])
    if fact == "pr-review-thread":
        return canonical_json(["pr-review-thread", detail["number"]])
    if fact == "pr-mergeability":
        return canonical_json(["pr-mergeability", detail["number"]])
    return canonical_json(["observe-refusal"])


def replay_channel(root, remote, branch):
    """Replay the authoritative chain; projection.json is never trusted."""
    channel_dir = _channel_dir(root, remote, branch)
    chain = channel_dir / "signals.jsonl"
    channel = _channel_name(remote, branch)
    events = _read_events(chain, channel)
    facts = {}
    for event in events:
        facts[_fact_key(event["fact"], event["detail"])] = {
            "fact": event["fact"],
            "detail": event["detail"],
            "ts": event["ts"],
            "seq": event["seq"],
            "event_hash": event["event_hash"],
        }
    projection = {
        "channel": channel,
        "remote": remote,
        "branch": branch,
        "ledger_events": len(events),
        "ledger_head": str(events[-1]["event_hash"]),
        "last_observed": events[-1]["ts"],
        "facts": facts,
    }
    projection["prs"] = _pr_read_model(facts)
    projection["status"] = derive_status(facts)
    return projection


def _facts_for_pr(facts, number):
    selected = {}
    for record in facts.values():
        detail = record["detail"]
        if record["fact"] != "observe-refusal" and detail["number"] == number:
            selected.setdefault(record["fact"], []).append(detail)
    return selected


def _pr_numbers(facts):
    numbers = set()
    for record in facts.values():
        if record["fact"] != "observe-refusal":
            numbers.add(record["detail"]["number"])
    return sorted(numbers)


def _derive_pr_status(facts, number):
    """The docs/signals.md precedence, top match wins, for one PR."""
    selected = _facts_for_pr(facts, number)
    pr = selected.get("pr", [{}])[0]
    checks = selected.get("pr-check", [])
    review = selected.get("pr-review-thread", [{}])[0]
    merge = selected.get("pr-mergeability", [{}])[0]
    state = pr.get("state", "")
    if state == "merged":
        return "merged"
    if state == "closed":
        return "closed-unmerged"
    if any(check.get("conclusion") in _CHECK_FAILED for check in checks):
        return "ci-failed"
    if merge.get("mergeable") == "false":
        return "merge-conflict"
    if review.get("changes_requested") is True:
        return "changes-requested"
    if any(check.get("status") != "completed" for check in checks):
        return "ci-pending"
    if review.get("approved") is True:
        return "approved"
    if checks and merge.get("mergeable") == "true":
        return "mergeable"
    return "pr-open"


def _primary_pr(facts):
    numbers = _pr_numbers(facts)
    if not numbers:
        return None
    open_numbers = []
    for number in numbers:
        selected = _facts_for_pr(facts, number)
        pr = selected.get("pr", [{}])[0]
        if pr.get("state") == "open":
            open_numbers.append(number)
    if open_numbers:
        return max(open_numbers)
    return max(numbers)


def derive_status(facts):
    """Derived at read time, never stored (docs/signals.md precedence)."""
    number = _primary_pr(facts)
    if number is None:
        return "unobserved"
    return _derive_pr_status(facts, number)


def _pr_read_model(facts):
    prs = []
    for number in _pr_numbers(facts):
        selected = _facts_for_pr(facts, number)
        pr = selected.get("pr", [{}])[0]
        prs.append(
            {
                "number": number,
                "state": pr.get("state", ""),
                "draft": pr.get("draft", False),
                "url": pr.get("url", ""),
                "status": _derive_pr_status(facts, number),
            }
        )
    return prs


def _facts_from_snapshot(provider_name, snapshot):
    """Normalize a provider snapshot into allowlisted facts.

    Both providers pass through here, so any prose field a provider
    surfaces (review bodies, log text) is dropped by construction: only
    the exact allowlisted detail keys are ever read.
    """
    if snapshot.get("refusal") is not None:
        reason = str(snapshot["refusal"])
        if reason not in _REFUSAL_REASONS:
            reason = "forge-error"
        return [
            (
                "observe-refusal",
                {"provider": provider_name, "reason": reason},
            )
        ]
    facts = []
    for pr in snapshot.get("prs", []):
        number = int(pr["number"])
        facts.append(
            (
                "pr",
                {
                    "number": number,
                    "state": str(pr.get("state", "open")),
                    "draft": bool(pr.get("draft", False)),
                    "head": str(pr.get("head", "")),
                    "base": str(pr.get("base", "")),
                    "url": str(pr.get("url", "")),
                },
            )
        )
        for check in pr.get("checks", []):
            facts.append(
                (
                    "pr-check",
                    {
                        "number": number,
                        "name": str(check.get("name", "")),
                        "status": str(check.get("status", "completed")),
                        "conclusion": str(check.get("conclusion", "")),
                        "url": str(check.get("url", "")),
                    },
                )
            )
        review = pr.get("review", {})
        if review:
            reviewers = review.get("reviewers", [])
            facts.append(
                (
                    "pr-review-thread",
                    {
                        "number": number,
                        "unresolved": int(review.get("unresolved", 0)),
                        "resolved": int(review.get("resolved", 0)),
                        "changes_requested": bool(
                            review.get("changes_requested", False)
                        ),
                        "approved": bool(review.get("approved", False)),
                        "reviewers": ",".join(
                            str(login) for login in reviewers
                        )[:200],
                        "url": str(review.get("url", "")),
                    },
                )
            )
        if "mergeable" in pr:
            mergeable = pr["mergeable"]
            if mergeable not in ("true", "false", "unknown"):
                mergeable = "unknown"
            facts.append(
                (
                    "pr-mergeability",
                    {
                        "number": number,
                        "mergeable": mergeable,
                        "reason": str(pr.get("mergeable_reason", "")),
                    },
                )
            )
    return facts


class FixtureProvider(object):
    """Deterministic oracle: a snapshot JSON document on disk."""

    name = "fixture"

    def __init__(self, path):
        self._path = Path(path)

    def fetch(self, state):
        try:
            snapshot = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"refusal": "forge-error"}, state, False
        token = _sha(snapshot)
        if state.get("etag") == token:
            return snapshot, state, True
        return snapshot, {"etag": token}, False


class GithubProvider(object):
    """Thin GitHub REST adapter. Live use is smoke-only; the fixture
    provider is the CI oracle. Tokens come from the operator environment
    and are never stored."""

    name = "github"

    def __init__(self, owner, repo, branch, token=None, opener=None):
        self._owner = owner
        self._repo = repo
        self._branch = branch
        self._token = token or os.environ.get(
            "GITHUB_TOKEN", os.environ.get("GH_TOKEN", "")
        )
        self._opener = opener or urllib.request.urlopen

    def _get(self, url, etag=None):
        request = urllib.request.Request(url)
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("User-Agent", "delivery-workbench-signals")
        if self._token:
            request.add_header("Authorization", "Bearer %s" % self._token)
        if etag:
            request.add_header("If-None-Match", etag)
        response = self._opener(request, timeout=30)
        body = json.loads(response.read().decode("utf-8"))
        headers = getattr(response, "headers", {}) or {}
        return body, headers.get("ETag")

    def fetch(self, state):
        base = "https://api.github.com/repos/%s/%s" % (
            self._owner,
            self._repo,
        )
        try:
            listing, etag = self._get(
                "%s/pulls?state=all&head=%s:%s"
                % (base, self._owner, urllib.parse.quote(self._branch)),
                etag=state.get("etag"),
            )
        except urllib.error.HTTPError as error:
            if error.code == 304:
                return {"prs": []}, state, True
            if error.code in (401,):
                return {"refusal": "unauthenticated"}, state, False
            if error.code in (403, 429):
                return {"refusal": "rate-limited"}, state, False
            return {"refusal": "forge-error"}, state, False
        except (urllib.error.URLError, OSError, ValueError):
            return {"refusal": "network-error"}, state, False
        prs = []
        for item in listing:
            merged = bool(item.get("merged_at"))
            pr_state = item.get("state", "open")
            if pr_state == "closed" and merged:
                pr_state = "merged"
            entry = {
                "number": item.get("number"),
                "state": pr_state,
                "draft": bool(item.get("draft", False)),
                "head": (item.get("head") or {}).get("ref", ""),
                "base": (item.get("base") or {}).get("ref", ""),
                "url": item.get("html_url", ""),
                "checks": [],
            }
            try:
                sha = (item.get("head") or {}).get("sha", "")
                if sha:
                    runs, _ = self._get(
                        "%s/commits/%s/check-runs" % (base, sha)
                    )
                    for run in runs.get("check_runs", []):
                        entry["checks"].append(
                            {
                                "name": run.get("name", ""),
                                "status": run.get("status", ""),
                                "conclusion": run.get("conclusion") or "",
                                "url": run.get("html_url", ""),
                            }
                        )
                detail, _ = self._get(
                    "%s/pulls/%s" % (base, item.get("number"))
                )
                mergeable = detail.get("mergeable")
                if mergeable is True:
                    entry["mergeable"] = "true"
                elif mergeable is False:
                    entry["mergeable"] = "false"
                else:
                    entry["mergeable"] = "unknown"
                entry["mergeable_reason"] = str(
                    detail.get("mergeable_state", "")
                )
                reviews, _ = self._get(
                    "%s/pulls/%s/reviews" % (base, item.get("number"))
                )
                latest = {}
                for review in reviews:
                    login = (review.get("user") or {}).get("login", "")
                    review_state = review.get("state", "")
                    if login and review_state in (
                        "APPROVED",
                        "CHANGES_REQUESTED",
                    ):
                        latest[login] = review_state
                entry["review"] = {
                    "unresolved": sum(
                        1
                        for value in latest.values()
                        if value == "CHANGES_REQUESTED"
                    ),
                    "resolved": 0,
                    "changes_requested": "CHANGES_REQUESTED"
                    in latest.values(),
                    "approved": bool(latest)
                    and set(latest.values()) == {"APPROVED"},
                    "reviewers": sorted(latest),
                    "url": item.get("html_url", ""),
                }
            except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError):
                return {"refusal": "forge-error"}, state, False
            prs.append(entry)
        new_state = dict(state)
        if etag:
            new_state["etag"] = etag
        return {"prs": prs}, new_state, False


def _load_provider_state(channel_dir):
    path = channel_dir / "provider-state.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return state if isinstance(state, dict) else {}


def observe_signals(root, provider, remote, branch, now=None):
    """One bounded observe pass: poll, diff semantically, append changes.

    Pure toward everything except ``.git/pmo-signals/``: stamps
    ``starts_work: False`` and can never mutate the forge, the operator
    tree, a run, or an agent.
    """
    now = now or _utc_now()
    channel = _channel_name(remote, branch)
    with _store_lock(root):
        channel_dir = _channel_dir(root, remote, branch)
        channel_dir.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        channel_dir.mkdir(exist_ok=True, mode=0o700)
        chain = channel_dir / "signals.jsonl"
        if chain.exists():
            projection = replay_channel(root, remote, branch)
            prev_hash = projection["ledger_head"]
            seq = projection["ledger_events"]
            known = projection["facts"]
        else:
            prev_hash = None
            seq = 0
            known = {}
            _write_json(
                channel_dir / "channel.json",
                {
                    "kind": "delivery-workbench-signal-channel",
                    "schema_version": SIGNAL_SCHEMA_VERSION,
                    "remote": remote,
                    "branch": branch,
                    "created": _format_time(now),
                },
            )
        state = _load_provider_state(channel_dir)
        snapshot, new_state, not_modified = provider.fetch(state)
        appended = 0
        refusal = None
        if not not_modified:
            facts = _facts_from_snapshot(provider.name, snapshot)
            for fact, detail in facts:
                if fact == "observe-refusal":
                    refusal = detail["reason"]
                key = _fact_key(fact, detail)
                current = known.get(key)
                if current is not None and current["detail"] == detail:
                    continue
                document = _event_document(
                    channel, seq, fact, detail, prev_hash, now
                )
                data = (canonical_json(document) + "\n").encode("utf-8")
                with chain.open("ab", buffering=0) as handle:
                    written = handle.write(data)
                    if written != len(data):
                        raise DwError(
                            "short write while appending the signal chain"
                        )
                    os.fsync(handle.fileno())
                prev_hash = document["event_hash"]
                seq += 1
                appended += 1
                known[key] = {
                    "fact": fact,
                    "detail": detail,
                    "ts": document["ts"],
                    "seq": document["seq"],
                }
        _write_json(channel_dir / "provider-state.json", new_state)
        if chain.exists():
            projection = replay_channel(root, remote, branch)
            _write_cache(channel_dir, projection)
            status = projection["status"]
            head = projection["ledger_head"]
            events = projection["ledger_events"]
        else:
            status = "unobserved"
            head = None
            events = 0
        return {
            "kind": SIGNALS_OBSERVE_KIND,
            "schema_version": SIGNAL_SCHEMA_VERSION,
            "channel": channel,
            "remote": remote,
            "branch": branch,
            "provider": provider.name,
            "observed": _format_time(now),
            "not_modified": bool(not_modified),
            "appended": appended,
            "refusal": refusal,
            "status": status,
            "ledger_events": events,
            "ledger_head": head,
            "starts_work": False,
            "writes_events": appended > 0,
        }


def _iter_channels(root):
    store = signal_store_dir(root)
    if not store.is_dir():
        return
    for remote_dir in sorted(store.iterdir()):
        if not remote_dir.is_dir():
            continue
        for branch_dir in sorted(remote_dir.iterdir()):
            if not branch_dir.is_dir():
                continue
            meta_path = branch_dir / "channel.json"
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            yield meta.get("remote", ""), meta.get("branch", "")


def build_signals_inventory(root, remote=None, branch=None):
    """The read model shared byte-for-byte by CLI, MCP, and HTTP."""
    channels = []
    for known_remote, known_branch in _iter_channels(root):
        if remote is not None and known_remote != remote:
            continue
        if branch is not None and known_branch != branch:
            continue
        projection = replay_channel(root, known_remote, known_branch)
        channels.append(
            {
                "channel": projection["channel"],
                "remote": projection["remote"],
                "branch": projection["branch"],
                "status": projection["status"],
                "prs": projection["prs"],
                "ledger_events": projection["ledger_events"],
                "ledger_head": projection["ledger_head"],
                "last_observed": projection["last_observed"],
            }
        )
    return {
        "kind": SIGNALS_KIND,
        "schema_version": SIGNAL_SCHEMA_VERSION,
        "channels": channels,
        "starts_work": False,
        "writes_events": False,
    }


NUDGE_INTENTS = ("auto", "manual")

_RECEPTIVITY = {
    "waiting_input": "deliver",
    "idle": "deliver",
    "active": "defer",
    "blocked": "refuse",
    "unknown": "refuse",
    "exited": "refuse",
}


def receptivity(activity, intent):
    """The pure receptivity table from docs/signals.md.

    Maps (activity state, nudge intent) to deliver | defer | refuse.
    `blocked` and `unknown` refuse under every intent, including a
    manual operator nudge: a session stopped on a permission decision
    is awaiting a ring-4 approval, and honesty about an unobservable
    state outranks convenience.
    """
    if intent not in NUDGE_INTENTS:
        raise DwError("unsupported nudge intent %r" % (intent,))
    verdict = _RECEPTIVITY.get(activity)
    if verdict is None:
        raise DwError("unsupported activity state %r" % (activity,))
    return verdict


def resolve_signal_channel(root, remote=None, branch=None):
    remote = remote or "origin"
    branch = branch or current_branch(Path(root))
    if branch == "detached":
        raise DwError("signals need a named branch; HEAD is detached")
    return remote, branch


def github_provider_for(root, remote, branch):
    url = run_git(Path(root), "config", "--get", "remote.%s.url" % remote)
    if not url or not url.strip():
        raise DwError("remote %r has no configured URL" % remote)
    owner, repo = parse_github_remote(url.strip())
    return GithubProvider(owner, repo, branch)


def parse_github_remote(url):
    """Parse owner/repo out of an https or ssh GitHub remote URL."""
    value = str(url).strip()
    if value.startswith("git@github.com:"):
        path = value[len("git@github.com:"):]
    elif value.startswith("ssh://git@github.com/"):
        path = value[len("ssh://git@github.com/"):]
    elif value.startswith("https://github.com/"):
        path = value[len("https://github.com/"):]
    else:
        raise DwError("only GitHub remotes are supported in this phase")
    if path.endswith(".git"):
        path = path[: -len(".git")]
    parts = [part for part in path.split("/") if part]
    if len(parts) != 2:
        raise DwError("cannot parse owner/repo from remote URL")
    return parts[0], parts[1]
