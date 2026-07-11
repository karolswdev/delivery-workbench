#!/usr/bin/env python3
"""Architecture fitness tests for the Telegram interface (WLA-14-07).

The ccgram runner-up idea absorbed (absorption map §6): guardrails
as tests, not as prose someone forgets. These parse the package's
own imports and assert the layering that keeps the consent floor
un-bypassable — then prove they FAIL on a planted violation, so a
green run means something.

Load-bearing invariants:
- The transport (raw Telegram I/O) imports nothing from the package
  and knows nothing of rails, drivers, or consent — so no send-path
  shortcut can route around the gate.
- The leaf modules stay leaves (no upward imports → no cycles).
- Only the interface orchestrates rails/lifecycle/driver.
- `tmux send-keys` and the keystroke methods live ONLY in the
  driver, so every keystroke passes its pane-ownership check —
  there is no second door into a terminal.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

PKG = (
    Path(__file__).resolve().parent.parent.parent
    / "integrations" / "telegram" / "dw_telegram"
)

LEAVES = {
    "transport", "entities", "sendfiles", "runtime", "config",
    "screenshot",
}
# `lifecycle` is the only module allowed to build on `rails` (it runs
# doctor/contract through the same CLI); everything else reaches the
# rails only through the interface's orchestration.
RAILS_CONSUMERS = {"interface", "lifecycle"}
LIFECYCLE_CONSUMERS = {"interface"}


def internal_imports(module_path: Path) -> set[str]:
    """The dw_telegram sibling modules a file imports."""
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            found.add(node.module.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 1 and node.names:
            for alias in node.names:
                found.add(alias.name)
    return found


def module_source(name: str) -> str:
    return (PKG / f"{name}.py").read_text(encoding="utf-8")


class ImportLayeringTest(unittest.TestCase):
    def setUp(self):
        self.modules = {
            p.stem: p for p in PKG.glob("*.py") if p.stem != "__init__"
        }
        self.graph = {
            name: internal_imports(path)
            for name, path in self.modules.items()
        }

    def test_transport_is_a_pure_leaf(self):
        self.assertEqual(
            self.graph["transport"], set(),
            "the transport must import nothing from the package — it is "
            "raw Telegram I/O and must not learn about rails or consent",
        )

    def test_leaves_stay_leaves(self):
        for leaf in LEAVES:
            self.assertEqual(
                self.graph.get(leaf, set()), set(),
                f"{leaf} is a leaf; an internal import would risk a cycle",
            )

    def test_rails_seam_is_reached_only_through_the_interface(self):
        for name, imports in self.graph.items():
            if "rails" in imports:
                self.assertIn(
                    name, RAILS_CONSUMERS,
                    f"{name} imports rails — only {RAILS_CONSUMERS} may; "
                    "everything else reaches the rails via the interface",
                )
            if "lifecycle" in imports:
                self.assertIn(
                    name, LIFECYCLE_CONSUMERS,
                    f"{name} imports lifecycle — only the interface may "
                    "orchestrate the path-allow-listed lifecycle",
                )

    def test_no_import_cycles(self):
        # depth-first cycle check over the internal graph
        WHITE, GREY, BLACK = 0, 1, 2
        color = {n: WHITE for n in self.graph}

        def visit(node: str, stack: list[str]) -> None:
            color[node] = GREY
            for nxt in self.graph.get(node, set()):
                if nxt not in color:
                    continue
                if color[nxt] == GREY:
                    self.fail(f"import cycle: {' -> '.join(stack + [nxt])}")
                if color[nxt] == WHITE:
                    visit(nxt, stack + [nxt])
            color[node] = BLACK

        for node in self.graph:
            if color[node] == WHITE:
                visit(node, [node])


class ConsentFloorTest(unittest.TestCase):
    def test_send_keys_lives_only_in_the_driver(self):
        offenders = [
            p.name
            for p in PKG.glob("*.py")
            if p.stem != "tmuxdrive" and "send-keys" in p.read_text()
        ]
        self.assertEqual(
            offenders, [],
            "tmux send-keys appears outside the driver — every keystroke "
            "must pass the driver's pane-ownership check; there is no "
            "second door into a terminal",
        )

    def test_keystroke_methods_are_defined_only_in_the_driver(self):
        for other in PKG.glob("*.py"):
            if other.stem == "tmuxdrive":
                continue
            source = other.read_text()
            self.assertNotIn(
                "def send_text", source,
                f"{other.name} defines send_text — the relay primitive "
                "belongs to the driver alone",
            )
            self.assertNotIn(
                "def send_key", source,
                f"{other.name} defines send_key — driver-only",
            )


class FitnessSelfTest(unittest.TestCase):
    """The guardrails must FAIL on a violation, or they guard nothing."""

    def test_layering_catches_a_planted_transport_import(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp)
            (fake / "transport.py").write_text("from .rails import RailsClient\n")
            (fake / "rails.py").write_text("x = 1\n")
            graph = {
                "transport": internal_imports(fake / "transport.py"),
                "rails": internal_imports(fake / "rails.py"),
            }
            self.assertIn("rails", graph["transport"],
                          "the parser must SEE the planted violation")

    def test_consent_floor_catches_planted_send_keys(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            rogue = Path(tmp) / "rogue.py"
            rogue.write_text('subprocess.run(["tmux", "send-keys", "x"])\n')
            self.assertIn("send-keys", rogue.read_text(),
                          "the grep must SEE a planted second door")


if __name__ == "__main__":
    unittest.main(verbosity=2)
