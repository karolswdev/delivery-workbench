"""The boundary that owns repository-derived facts.

Every fact in this module comes from asking ``git`` something about the
checkout.  Some of those answers cannot change while the process runs; most
of them change the moment anything writes.  Before this module existed the
distinction was never stated, so no caller could safely reuse an answer and
the only safe habit was to spawn ``git`` again — roughly fifty-three
``rev-parse --git-dir`` spawns per program conductor tick, for a value fixed
for the life of the process.

This module states the distinction and owns the resolution.  Nothing here
decides eligibility, grants permission, evaluates review, or performs an
action; it answers questions about the repository and nothing else.

The rule this boundary exists to enforce:

* ``PROCESS_IMMUTABLE`` facts describe where the repository *is*.  They may be
  resolved once per root and reused for the life of the process.
* ``DERIVATION_SCOPED`` facts describe what the repository *contains*.  They
  may be reused only inside one derivation — one frontier computation, one
  freshness check, one plan build — and any mutation invalidates them.

Speed may never buy itself with staleness.  A derivation-scoped fact that
outlives a write would silently defeat the freshness, divergence, and
dirty-tree refusals that exist to fail closed.
"""

from __future__ import annotations

from pathlib import Path

from .gitio import run_git
from .model import DwError


REPOSITORY_FACTS_KIND = "delivery-workbench-repository-facts"
REPOSITORY_FACTS_SCHEMA_VERSION = 1

PROCESS_IMMUTABLE = "process-immutable"
DERIVATION_SCOPED = "derivation-scoped"

FACT_CLASSES = (PROCESS_IMMUTABLE, DERIVATION_SCOPED)

# The complete census of repository-derived facts this boundary serves.  Every
# entry names the git command behind it, its class, and why it holds that
# class.  The executable contract test asserts this census is total: a fact
# served without a class here is a bug, not an omission.
REPOSITORY_FACTS = {
    "git_dir": {
        "class": PROCESS_IMMUTABLE,
        "command": ("rev-parse", "--git-dir"),
        "reason": (
            "The git directory of a checkout is fixed for the life of the "
            "process; a worktree does not move its own .git while running."
        ),
    },
    "repository_id": {
        "class": PROCESS_IMMUTABLE,
        "command": ("rev-parse", "--git-dir"),
        "reason": (
            "Derived from the resolved root and git directory, both of which "
            "are fixed for the process."
        ),
    },
    "head_sha": {
        "class": DERIVATION_SCOPED,
        "command": ("rev-parse", "--verify", "HEAD"),
        "reason": "Every commit moves HEAD.",
    },
    "index_tree": {
        "class": DERIVATION_SCOPED,
        "command": ("write-tree",),
        "reason": "Every stage or restage writes a different tree.",
    },
    "current_branch": {
        "class": DERIVATION_SCOPED,
        "command": ("symbolic-ref", "--quiet", "--short", "HEAD"),
        "reason": "Checkout moves the branch under a running process.",
    },
    "remote_url": {
        "class": DERIVATION_SCOPED,
        "command": ("remote", "get-url"),
        "reason": (
            "Remote configuration is edited far less often than it is read, "
            "but it is configuration a user can change mid-session."
        ),
    },
    "remote_ref": {
        "class": DERIVATION_SCOPED,
        "command": ("rev-parse", "--verify"),
        "reason": "Fetch moves remote refs; divergence checks depend on it.",
    },
    "worktree_status": {
        "class": DERIVATION_SCOPED,
        "command": ("status", "--porcelain=v1", "-z"),
        "reason": "Any edit changes it; the dirty-tree refusal depends on it.",
    },
}

# Modules that still resolve the git directory privately.  WLA-28-01 opened
# this ledger with five spawning sites plus one non-spawning one; WLA-28-02
# emptied both.  They stay here, asserted empty in both directions, so a future
# private resolver has to be added deliberately and visibly rather than
# appearing by habit.
PENDING_PRIVATE_RESOLVERS: "tuple[str, ...]" = ()
PRIVATE_NON_SPAWNING_RESOLVERS: "tuple[str, ...]" = ()


def fact_class(name: str) -> str:
    """Return the declared class of ``name``, refusing unknown facts."""
    entry = REPOSITORY_FACTS.get(name)
    if entry is None:
        raise DwError(f"unknown repository fact: {name}")
    return str(entry["class"])


def is_process_immutable(name: str) -> bool:
    return fact_class(name) == PROCESS_IMMUTABLE


# Resolved git directories, keyed by resolved repository root.  Keyed rather
# than global because one process routinely serves several repositories — the
# test suite builds a fresh fixture repository per test — so a single slot
# would hand one repository another's store.  Only successful resolutions are
# cached; a failure must stay a failure.
_GIT_DIR_CACHE: "dict[str, Path]" = {}


def reset_cache() -> None:
    """Drop memoized process-immutable facts.

    Correctness never depends on this: the cached facts cannot change while
    the process runs. It exists so tests can prove the cache is doing the work
    rather than being shadowed by something else.
    """
    _GIT_DIR_CACHE.clear()


def git_dir(root: Path) -> Path:
    """Resolve the repository's git directory, at most once per root.

    ``git_dir`` is ``PROCESS_IMMUTABLE``: where a repository lives cannot
    change under a running process, so the first answer stands. This is the
    one place that asks; every other module routes through here.
    """
    root = Path(root)
    key = str(root.resolve())
    cached = _GIT_DIR_CACHE.get(key)
    if cached is not None:
        return cached
    raw = (run_git(root, "rev-parse", "--git-dir") or "").strip()
    if not raw:
        raise DwError("repository facts require a Git repository")
    path = Path(raw)
    if not path.is_absolute():
        path = root.resolve() / path
    resolved = path.resolve()
    _GIT_DIR_CACHE[key] = resolved
    return resolved


class Derivation:
    """One derivation's view of the facts that change on write.

    Reuse inside a derivation is safe; reuse across a write is not.  Callers
    that mutate the repository must call :meth:`invalidate`, which is the
    invalidation rule expressed in code rather than only in prose.

    WLA-28-01 ships this structure without adopting it in callers; WLA-28-03
    adopts it and proves every fail-closed refusal still fires.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self._facts: dict[tuple[str, tuple[str, ...]], object] = {}
        self.invalidations = 0

    def fact(self, name: str, produce, *key: str):
        """Return a derivation-scoped fact, computing it at most once.

        ``produce`` is the callable that actually asks git.  Process-immutable
        facts are refused here: they belong to the process-level resolver, not
        to a derivation.
        """
        if is_process_immutable(name):
            raise DwError(
                f"{name} is {PROCESS_IMMUTABLE}; resolve it at process level, "
                "not inside a derivation"
            )
        cache_key = (name, tuple(key))
        if cache_key not in self._facts:
            self._facts[cache_key] = produce()
        return self._facts[cache_key]

    def invalidate(self) -> None:
        """Drop every derivation-scoped fact after a mutation."""
        self._facts.clear()
        self.invalidations += 1

    def __len__(self) -> int:
        return len(self._facts)


def contract_document() -> dict:
    """The versioned, machine-readable statement of this boundary."""
    return {
        "kind": REPOSITORY_FACTS_KIND,
        "schema_version": REPOSITORY_FACTS_SCHEMA_VERSION,
        "classes": list(FACT_CLASSES),
        "facts": {
            name: {
                "class": entry["class"],
                "command": list(entry["command"]),
                "reason": entry["reason"],
            }
            for name, entry in sorted(REPOSITORY_FACTS.items())
        },
        "pending_private_resolvers": list(PENDING_PRIVATE_RESOLVERS),
        "private_non_spawning_resolvers": list(PRIVATE_NON_SPAWNING_RESOLVERS),
    }
