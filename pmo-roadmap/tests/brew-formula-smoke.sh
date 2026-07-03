#!/usr/bin/env bash
# Homebrew formula smoke (WLA-9-04).
#
# Proves Formula/delivery-workbench.rb against a locally built wheel:
# rewrites url/sha256 to a file:// artifact, brew-installs it, checks
# version truth and that the brew-installed dw bootstraps a fixture
# repo to doctor-green with the defer-to-repo rule intact, then
# uninstalls. Skips cleanly (exit 0) where brew is absent — CI's
# ubuntu leg must not fail. Style-checks the tracked formula when
# brew is available.

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PMO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT="$(cd "$PMO_DIR/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pmo-brew-smoke.XXXXXX")"
INSTALLED=0
TAPPED=0
TAP="pmo-smoke/local"

cleanup() {
  if [ "$INSTALLED" -eq 1 ]; then
    brew uninstall --formula "$TAP/delivery-workbench" >/dev/null 2>&1 || true
  fi
  if [ "$TAPPED" -eq 1 ]; then
    brew untap "$TAP" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
  echo "brew-formula-smoke.sh: $1" >&2
  exit 1
}

note() {
  echo "brew-formula-smoke.sh: $1"
}

if ! command -v brew >/dev/null 2>&1; then
  note "skip (brew not available)"
  exit 0
fi
if brew list --formula delivery-workbench >/dev/null 2>&1; then
  fail "delivery-workbench already installed; uninstall it before running the smoke"
fi

# ── build the wheel (same interpreter health probe as package-smoke) ─
PY=""
for cand in "${PMO_PACKAGE_PYTHON:-}" python3 /usr/bin/python3; do
  [ -n "$cand" ] || continue
  command -v "$cand" >/dev/null 2>&1 || continue
  probe="$TMP_ROOT/probe-venv"
  rm -rf "$probe"
  if "$cand" -c "import pyexpat" >/dev/null 2>&1 \
    && "$cand" -m venv "$probe" >/dev/null 2>&1 \
    && "$probe/bin/python" -m pip --version >/dev/null 2>&1; then
    PY="$cand"
    break
  fi
done
[ -n "$PY" ] || fail "no interpreter with working venv+pip found"

BUILD_VENV="$TMP_ROOT/buildenv"
"$PY" -m venv "$BUILD_VENV"
"$BUILD_VENV/bin/python" -m pip install --quiet --upgrade pip build
(cd "$ROOT" && "$BUILD_VENV/bin/python" -m build --wheel --outdir "$TMP_ROOT/dist") >/dev/null
WHEEL="$(ls "$TMP_ROOT"/dist/*.whl)"
SHA256="$(shasum -a 256 "$WHEEL" | awk '{print $1}')"
note "built $(basename "$WHEEL")"

# ── throwaway local tap with the rewritten formula ─────────────────
# Homebrew ≥6 refuses path installs: formulae must live in a tap.
if brew tap | grep -qx "$TAP"; then
  fail "tap $TAP already exists; remove it before running the smoke"
fi
brew tap-new --no-git "$TAP" >/dev/null 2>&1 || fail "brew tap-new failed"
TAPPED=1
TAP_DIR="$(brew --repository "$TAP")"
sed -e "s|url \".*\",|url \"file://$WHEEL\",|" \
    -e "s|sha256 \".*\"|sha256 \"$SHA256\"|" \
  "$ROOT/Formula/delivery-workbench.rb" > "$TAP_DIR/Formula/delivery-workbench.rb"
grep -q "file://$WHEEL" "$TAP_DIR/Formula/delivery-workbench.rb" \
  || fail "formula url rewrite failed"

if brew style "$TAP/delivery-workbench" >/dev/null 2>&1; then
  note "brew style: clean"
else
  note "brew style: findings (non-blocking; audit runs at tap publication)"
fi

# ── install from the local tap, prove, uninstall ───────────────────
brew install --formula --quiet "$TAP/delivery-workbench" >/dev/null 2>&1 \
  || fail "brew install from local tap failed"
INSTALLED=1
DW="$(brew --prefix)/bin/dw"
[ -x "$DW" ] || fail "brew did not link bin/dw"

EXPECTED_VERSION="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$PMO_DIR/lib/dw_pmo/__init__.py")"
(cd "$TMP_ROOT" && "$DW" --version) | grep -q "$EXPECTED_VERSION" \
  || fail "brew-installed dw --version does not report $EXPECTED_VERSION"

FIXTURE="$TMP_ROOT/fixture"
mkdir -p "$FIXTURE"
git -C "$FIXTURE" init -q -b main
git -C "$FIXTURE" config user.name "Brew Smoke"
git -C "$FIXTURE" config user.email "brew-smoke@example.test"
(cd "$TMP_ROOT" && "$DW" install "$FIXTURE" --skip-bootstrap) >/dev/null \
  || fail "brew-installed bootstrap failed"
(cd "$FIXTURE" && ./.githooks/dw doctor) >/dev/null \
  || fail "fixture doctor not green after brew-installed bootstrap"

printf '#!/usr/bin/env python3\nprint("VENDORED-RAILS-SPOKE")\n' > "$FIXTURE/.githooks/dw"
chmod +x "$FIXTURE/.githooks/dw"
(cd "$FIXTURE" && "$DW" --version 2>/dev/null) | grep -q "VENDORED-RAILS-SPOKE" \
  || fail "defer-to-repo rule broken under the brew install"

echo "brew-formula-smoke.sh: ok"
