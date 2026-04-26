#!/usr/bin/env bash
# Prepare a disposable repository for the onboarding VHS demo.

set -eu

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO_REPO="${DELIVERY_WORKBENCH_ONBOARDING_DEMO:-/tmp/delivery-workbench-onboarding-demo}"

rm -rf "$DEMO_REPO"
mkdir -p "$DEMO_REPO"
git -C "$DEMO_REPO" init >/dev/null
git -C "$DEMO_REPO" config user.name "Delivery Workbench Demo"
git -C "$DEMO_REPO" config user.email "demo@example.test"

cat > "$DEMO_REPO/README.md" <<'EOF'
# Demo App

An existing project that is about to adopt Delivery Workbench.
EOF

git -C "$DEMO_REPO" add README.md
git -C "$DEMO_REPO" commit -m "initial app" >/dev/null

"$ROOT/pmo-roadmap/install.sh" "$DEMO_REPO" --skip-bootstrap >/dev/null

mkdir -p "$DEMO_REPO/.demo"
cat > "$DEMO_REPO/.demo/session-intake" <<EOF
#!/usr/bin/env bash
exec "$ROOT/pmo-roadmap/bootstrap/session-intake.sh" "\$@"
EOF
cat > "$DEMO_REPO/.demo/adopt-project" <<EOF
#!/usr/bin/env bash
exec "$ROOT/pmo-roadmap/bootstrap/adopt-project.sh" "\$@"
EOF
chmod +x "$DEMO_REPO/.demo/session-intake" "$DEMO_REPO/.demo/adopt-project"

echo "Prepared onboarding demo repo:"
echo "  $DEMO_REPO"
