# Evidence - WLA-0-04

- **Story:** WLA-0-04 - Plan installer, update, and project configuration rollout
- **Status:** done
- **Date:** 2026-07-01

## Proof

- `install.sh` installs `pre-commit`, `post-commit`, `dw`,
  `work-log-summarize`, and `work-log-read`.
- `update.sh` refreshes framework-owned files and preserves
  `.githooks/pre-commit.config` and `.githooks/pre-commit.local`.
- Existing non-framework `post-commit` hooks are refused or preserved unless
  the operator explicitly forces replacement.

## Command Output

```text
$ rg -n "post-commit|work-log-summarize|work-log-read|bin/dw|pre-commit.config|pre-commit.local|refusing" \
  pmo-roadmap/install.sh pmo-roadmap/update.sh pmo-roadmap/tests/work-log-mvp.sh
pmo-roadmap/install.sh:15:  - copies hooks/post-commit              -> .githooks/post-commit (chmod +x)
pmo-roadmap/install.sh:16:  - copies bin/dw                         -> .githooks/dw
pmo-roadmap/update.sh:16:  - bin/dw                       -> .githooks/dw
pmo-roadmap/update.sh:109:if [ -f "$TARGET/.githooks/pre-commit.config" ]; then
pmo-roadmap/update.sh:112:if [ -f "$TARGET/.githooks/pre-commit.local" ]; then
pmo-roadmap/tests/work-log-mvp.sh:82:[ -x .githooks/dw ] || fail "install should write dw helper"
pmo-roadmap/tests/work-log-mvp.sh:196:grep -q 'custom update hook' .githooks/post-commit || fail "update should preserve existing non-framework post-commit without --force"
pmo-roadmap/tests/work-log-mvp.sh:205:  fail "install should refuse to overwrite existing non-framework post-commit"
```

```text
$ pmo-roadmap/tests/work-log-mvp.sh
work-log-mvp.sh: ok
```
