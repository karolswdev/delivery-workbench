#!/usr/bin/env bash
# Prepare a disposable repository for the commit-gate VHS demo.

set -eu

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO_REPO="${DELIVERY_WORKBENCH_COMMIT_DEMO:-/tmp/delivery-workbench-commit-demo}"
LOG_ROOT="${DELIVERY_WORKBENCH_LOG_DEMO:-/tmp/delivery-workbench-work-log}"

rm -rf "$DEMO_REPO" "$LOG_ROOT"
mkdir -p "$DEMO_REPO" "$LOG_ROOT"
git -C "$DEMO_REPO" init >/dev/null
git -C "$DEMO_REPO" config user.name "Delivery Workbench Demo"
git -C "$DEMO_REPO" config user.email "demo@example.test"

"$ROOT/pmo-roadmap/install.sh" "$DEMO_REPO" \
  --project-name "Demo" \
  --project-slug demo \
  --project-prefix DEMO \
  >/dev/null

cd "$DEMO_REPO"

mkdir -p .demo
cat > .demo/write-contract <<EOF
#!/usr/bin/env bash
exec "$ROOT/demos/scripts/write-demo-contract.sh" "\$@"
EOF
cat > .demo/show-log <<EOF
#!/usr/bin/env bash
set -eu
log_file=\$(find "$LOG_ROOT" -type f -name '*-work-summary.log' | head -1)
sed -n '1,44p' "\$log_file"
EOF
chmod +x .demo/write-contract .demo/show-log

cat > .githooks/pre-commit.config <<EOF
PMO_WORK_LOG_ENABLED=1
PMO_WORK_LOG_PROJECT_SLUG=demo
PMO_WORK_LOG_DIR='$LOG_ROOT'
EOF

git add .
"$ROOT/demos/scripts/write-demo-contract.sh" no "Initial framework setup is not logged." >/dev/null
git commit -m "install delivery workbench" >/dev/null 2>&1

echo "Prepared commit-gate demo repo:"
echo "  $DEMO_REPO"
echo "Work-log root:"
echo "  $LOG_ROOT"
