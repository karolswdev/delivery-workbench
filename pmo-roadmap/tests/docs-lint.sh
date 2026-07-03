#!/usr/bin/env bash
# Docs lint (WLA-7-06): every internal link, anchor, and image in every
# Markdown file (roadmap tree included) must resolve, and every image
# must carry alt text. Findings are greppable "ERROR <file>:<line>: …"
# lines; external URLs are deliberately unchecked (flaky in CI). Also
# self-checks the checker: a fixture with one of each defect class must
# produce exactly the expected errors, and the clean run must finish
# inside the 30-second budget the story promises.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT="$(cd "$PMO_DIR/.." && pwd)"

fail() {
  echo "docs-lint.sh: $1" >&2
  exit 1
}

# ── self-check: the linter must bite on a broken fixture ─────────────
TMP="$(mktemp -d "${TMPDIR:-/tmp}/dw-docs-lint.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
cat > "$TMP/broken.md" <<'EOF'
# Fixture

[broken](./missing.md)
[bad anchor](#no-such-heading)
![](./present.md)
![gone](./missing.png)
EOF
printf '# Present\n' > "$TMP/present.md"
out="$(PYTHONPATH="$PMO_DIR/lib" python3 -m dw_pmo.docslint --root "$TMP" 2>&1)" && \
  fail "linter passed a fixture with four planted defects"
for needle in "broken link: ./missing.md" "broken anchor: #no-such-heading" \
  "image missing alt text" "missing image: ./missing.png"; do
  printf '%s\n' "$out" | grep -qF "$needle" || fail "self-check missed: $needle"
done

# ── the real run over the repository ─────────────────────────────────
start=$(date +%s)
PYTHONPATH="$PMO_DIR/lib" python3 -m dw_pmo.docslint --root "$ROOT"
elapsed=$(( $(date +%s) - start ))
if [ "$elapsed" -gt 30 ]; then
  fail "lint took ${elapsed}s (budget is 30s)"
fi

echo "docs-lint.sh: ok (${elapsed}s)"
