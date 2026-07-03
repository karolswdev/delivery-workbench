#!/usr/bin/env python3
"""Doc-parity check for the remote verification contract.

Every rule id the gate engine can emit must be classified in
docs/remote-verification.md (WLA-8-01 acceptance criterion; the
classification table is the specification dw verify is tested
against). Greppable failures, exit 1 on any gap.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / ".githooks" / "dw_pmo" / "gate.py"
DOC = ROOT / "docs" / "remote-verification.md"

REMOTE_ONLY_IDS = ["trailer-missing", "trailer-format"]


def main() -> int:
    gate_src = GATE.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    gate_ids = sorted(set(re.findall(r'failed\(\s*"([a-z-]+)"', gate_src)))
    if not gate_ids:
        print(f"ERROR {GATE}: no rule ids found (extraction regex drifted?)")
        return 1

    ok = True
    for rule_id in gate_ids + REMOTE_ONLY_IDS:
        if f"`{rule_id}`" not in doc:
            print(f"ERROR {DOC}: rule id `{rule_id}` is not classified")
            ok = False

    if ok:
        print(
            f"remote-verification-doc-check: ok "
            f"({len(gate_ids)} gate rule ids + {len(REMOTE_ONLY_IDS)} "
            f"remote-only ids classified in {DOC.relative_to(ROOT)})"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
