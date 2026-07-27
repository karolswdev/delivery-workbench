"""Deterministic, offline Python symbol and structure extraction.

This module is the pure half of the repository map.  It accepts tracked blob
metadata and a blob reader; it never asks Git, reads the worktree, consults a
clock, or performs network I/O.  ``repository_map`` owns the Git-facing half.
"""

from __future__ import annotations

import ast
from pathlib import PurePosixPath
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple


SYMBOL_MAP_KIND = "delivery-workbench-symbol-structure-map"
SYMBOL_MAP_SCHEMA_VERSION = 1
STRUCTURAL_LANGUAGE = "python"
GREP_FALLBACK = "out of structural coverage; use git grep"


def _module_name(path: str) -> str:
    parts = list(PurePosixPath(path).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts) or "__init__"


def _line_end(node: ast.AST, fallback: int) -> int:
    end = getattr(node, "end_lineno", None)
    if isinstance(end, int):
        return end
    lines = [getattr(child, "lineno", 0) for child in ast.walk(node)]
    return max(lines or [fallback])


def _imports(tree: ast.AST) -> List[str]:
    found = set()  # type: Set[str]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            for alias in node.names:
                separator = "" if not prefix or prefix.endswith(".") else "."
                found.add(prefix + separator + alias.name)
    return sorted(found)


def _references(tree: ast.AST) -> List[str]:
    """Return exact lexical identifiers used by a source file.

    Names and the terminal component of attributes are included.  Import
    aliases are naturally included when used in an expression; imported names
    are also included so a direct static import counts as a reference.
    """
    found = set()  # type: Set[str]
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.asname:
                    found.add(alias.asname)
                elif isinstance(node, ast.Import):
                    found.add(alias.name.split(".", 1)[0])
                else:
                    found.add(alias.name)
    return sorted(found)


def _symbols(tree: ast.Module, path: str, source_lines: int) -> List[dict]:
    module = _module_name(path)
    symbols = [{
        "kind": "module",
        "name": module.rsplit(".", 1)[-1],
        "qualified_name": module,
        "file": path,
        "line_start": 1,
        "line_end": max(1, source_lines),
    }]

    def visit(body: Iterable[ast.stmt], parents: Tuple[Tuple[str, str], ...]) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                qualified = ".".join([module] + [item[0] for item in parents]
                                     + [node.name])
                symbols.append({
                    "kind": "class",
                    "name": node.name,
                    "qualified_name": qualified,
                    "file": path,
                    "line_start": node.lineno,
                    "line_end": _line_end(node, node.lineno),
                })
                visit(node.body, parents + ((node.name, "class"),))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                kind = "method" if parents and parents[-1][1] == "class" else "function"
                qualified = ".".join([module] + [item[0] for item in parents]
                                     + [node.name])
                symbols.append({
                    "kind": kind,
                    "name": node.name,
                    "qualified_name": qualified,
                    "file": path,
                    "line_start": node.lineno,
                    "line_end": _line_end(node, node.lineno),
                })
                visit(node.body, parents + ((node.name, kind),))

    visit(tree.body, ())
    return sorted(symbols, key=lambda item: (
        item["file"], item["line_start"], item["qualified_name"], item["kind"]
    ))


def _source_line_count(source: bytes) -> int:
    if not source:
        return 1
    return len(source.splitlines())


def extract_python_file(path: str, blob: str, size: int, source: bytes) -> dict:
    """Extract one tracked Python blob, naming parse failures in its record."""
    record = {
        "file": path,
        "blob": blob,
        "size": size,
        "parse_status": "parsed",
        "imports": [],
        "references": [],
        "symbols": [],
    }
    try:
        tree = ast.parse(source, filename=path)
    except (SyntaxError, UnicodeDecodeError, ValueError):
        record["parse_status"] = "gap"
        return record
    record["imports"] = _imports(tree)
    record["references"] = _references(tree)
    record["symbols"] = _symbols(tree, path, _source_line_count(source))
    return record


def _is_test_file(path: str) -> bool:
    pure = PurePosixPath(path)
    name = pure.name
    return ("tests" in pure.parts or name.startswith("test_")
            or name.endswith("_test.py") or name.endswith("_tests.py"))


def _previous_modules(previous: Optional[dict]) -> Dict[str, dict]:
    if not isinstance(previous, dict):
        return {}
    if (previous.get("kind") != SYMBOL_MAP_KIND
            or previous.get("schema_version") != SYMBOL_MAP_SCHEMA_VERSION):
        return {}
    modules = previous.get("modules")
    if not isinstance(modules, list):
        return {}
    reusable = {}
    for module in modules:
        if not isinstance(module, dict):
            return {}
        path = module.get("file")
        blob = module.get("blob")
        if not isinstance(path, str) or not isinstance(blob, str):
            return {}
        reusable[path] = module
    return reusable


def build_symbol_map(
        index_tree: str,
        tracked_files: Iterable[dict],
        read_blob: Callable[[str], bytes],
        previous: Optional[dict] = None,
        on_parse: Optional[Callable[[str], None]] = None) -> dict:
    """Build a deterministic map, reusing only path-and-blob-identical parses."""
    tracked = sorted((dict(item) for item in tracked_files),
                     key=lambda item: item["path"])
    old_modules = _previous_modules(previous)
    modules = []
    gaps = []

    for item in tracked:
        path = item["path"]
        blob = item["blob"]
        size = item["size"]
        if not path.endswith(".py"):
            gaps.append({
                "file": path,
                "kind": "non-python",
                "reason": GREP_FALLBACK,
            })
            continue
        old = old_modules.get(path)
        if old is not None and old.get("blob") == blob:
            module = old
        else:
            if on_parse is not None:
                on_parse(path)
            module = extract_python_file(path, blob, size, read_blob(blob))
        modules.append(module)
        if module["parse_status"] != "parsed":
            gaps.append({
                "file": path,
                "kind": "unparseable-python",
                "reason": GREP_FALLBACK,
            })

    symbols = sorted(
        (symbol for module in modules for symbol in module["symbols"]),
        key=lambda item: (
            item["qualified_name"], item["file"], item["line_start"], item["kind"]
        ),
    )
    by_name = {}  # type: Dict[str, Set[str]]
    symbol_file = {}  # type: Dict[str, str]
    for symbol in symbols:
        by_name.setdefault(symbol["name"], set()).add(symbol["qualified_name"])
        symbol_file[symbol["qualified_name"]] = symbol["file"]

    tests = []
    for module in modules:
        if not _is_test_file(module["file"]) or module["parse_status"] != "parsed":
            continue
        referenced = set()  # type: Set[str]
        for name in module["references"]:
            referenced.update(by_name.get(name, ()))
        referenced = {
            qualified for qualified in referenced
            if symbol_file.get(qualified) != module["file"]
        }
        tests.append({
            "file": module["file"],
            "symbols": sorted(referenced),
        })

    parsed_count = sum(module["parse_status"] == "parsed" for module in modules)
    return {
        "kind": SYMBOL_MAP_KIND,
        "schema_version": SYMBOL_MAP_SCHEMA_VERSION,
        "index_tree": index_tree,
        "coverage": {
            "structural_language": STRUCTURAL_LANGUAGE,
            "fallback": GREP_FALLBACK,
            "tracked_file_count": len(tracked),
            "python_file_count": len(modules),
            "parsed_python_file_count": parsed_count,
            "gap_count": len(gaps),
        },
        "tracked_files": tracked,
        "modules": modules,
        "symbols": symbols,
        "tests": tests,
        "gaps": sorted(gaps, key=lambda item: (item["file"], item["kind"])),
        "test_resolution": {
            "rule": (
                "A test file references every symbol whose exact terminal name "
                "appears as an ast.Name, ast.Attribute, or imported name in that "
                "test; collisions intentionally retain every matching qualified "
                "symbol, and symbols defined by the same test file are excluded."
            ),
            "resolves_import_alias_targets": False,
        },
    }
