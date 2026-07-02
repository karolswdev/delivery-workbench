# Evidence - WLA-1-01

- **Story:** WLA-1-01 - Add work-log consent to the canonical contract
- **Status:** done
- **Date:** 2026-07-01

## Proof

- The canonical contract contains `**Work-log consent:** yes|no`, reasons, and
  exclusions outside the seven PMO checkboxes.
- The contract states that explicit `yes` is required and that consent is not
  counted by `EXPECTED_BOXES`.
- The agent snippet tells agents when to consent, deny, and list exclusions.

## Command Output

```text
$ rg -n "Work-log consent|EXPECTED_BOXES|Use `yes`|Use `no`|PMO_WORK_LOG_EXCLUDE_REGEX" \
  pmo-roadmap/templates/PMO-CONTRACT.md pmo-roadmap/templates/CLAUDE-snippet.md
pmo-roadmap/templates/PMO-CONTRACT.md:140:## Work-log consent
pmo-roadmap/templates/PMO-CONTRACT.md:142:**Work-log consent:** no
pmo-roadmap/templates/PMO-CONTRACT.md:158:The work-log consent block is not an eighth PMO checkbox and is not
pmo-roadmap/templates/PMO-CONTRACT.md:159:counted by `EXPECTED_BOXES`.
pmo-roadmap/templates/CLAUDE-snippet.md:16:**Work-log consent:** yes | no
pmo-roadmap/templates/CLAUDE-snippet.md:30:If the project config defines `PMO_WORK_LOG_EXCLUDE_REGEX`, matching staged
```
