"""Git-facing orchestration for the derived symbol and structure map.

The pure extractor lives in :mod:`dw_pmo.symbol_map`.  This module is the
sanctioned repository-facts layer: it binds extraction to one index tree,
reads tracked blobs through Git plumbing, and stores the result through the
WLA-29-01 ``DerivedFactStore``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from . import repofacts
from .knowledge import DerivedFactStore
from .model import DwError
from .symbol_map import build_symbol_map


SYMBOL_MAP_FACT_KIND = "symbol-structure-map"


def _derivation(root: Path, supplied: Optional[repofacts.Derivation] = None
                ) -> repofacts.Derivation:
    return supplied if supplied is not None else repofacts.Derivation(root)


def read_symbol_map(root: Path,
                    derivation: Optional[repofacts.Derivation] = None) -> dict:
    """Return the cached map only when it matches the current index tree."""
    root = Path(root)
    facts = _derivation(root, derivation)
    tree = repofacts.index_tree(root, facts)
    return DerivedFactStore(root).read(SYMBOL_MAP_FACT_KIND, tree)


def refresh_symbol_map(
        root: Path,
        on_parse: Optional[Callable[[str], None]] = None,
        derivation: Optional[repofacts.Derivation] = None) -> dict:
    """Incrementally rebuild and store the map for one immutable index tree."""
    root = Path(root)
    facts = _derivation(root, derivation)
    tree = repofacts.index_tree(root, facts)
    tracked = repofacts.tracked_files(root, tree, facts)
    store = DerivedFactStore(root)

    def compute(previous_document):
        previous = (previous_document.get("value")
                    if previous_document is not None else None)
        value = build_symbol_map(
            tree,
            tracked,
            lambda blob: repofacts.blob_content(root, blob, facts),
            previous=previous,
            on_parse=on_parse,
        )
        # Re-read the changing fact in a fresh derivation before publishing. If
        # an index write raced extraction, the old-tree map is never stored or
        # served as current.
        current = repofacts.index_tree(root, repofacts.Derivation(root))
        if current != tree:
            raise DwError(
                "repository index changed during knowledge refresh; retry "
                "against the new index tree"
            )
        return value

    return store.refresh(SYMBOL_MAP_FACT_KIND, tree, compute)
