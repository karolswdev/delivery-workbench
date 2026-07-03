# Project-extension worked example (illustrative)

> Extracted from PMO-CONTRACT.md §Extending (WLA-6-06). A real
> project's rule #8, kept as a concrete reference for the extension
> mechanism. Names, paths, and commands are that project's own.

### Worked example: Pantrybot's "design handoff" rule

Pantrybot adds a rule #8: every UI-facing change must update the
design handoff inputs that feed `design.pantrybot.app`, OR the
agent writes `.tmp/DESIGN-HANDOFF-OK.md` to explain the exception.

The implementation:

**`pm/roadmap/PMO-CONTRACT.md`** — adds, after the canonical 7:

```markdown
<!-- Project extensions (Pantrybot) -->

### 8. Design handoff for UI-facing changes (project-specific)

If this commit changes anything a user or designer can see, it also
updates the graphic-design handoff infrastructure in the same commit
(`docs/user-journeys/`, `graphic-design-handoff/`,
`frontend/public/handoff-data.json` from `npm run handoff:build`,
etc.). If the UI-facing path genuinely doesn't need new artifacts,
write `.tmp/DESIGN-HANDOFF-OK.md` with a one-line rationale.
```

**Contract template** — adds an 8th checkbox after the canonical 7:

```markdown
- [ ] **Design handoff updated.** UI-facing changes update the
  design handoff inputs, or `.tmp/DESIGN-HANDOFF-OK.md` explains why not.
```

**`.githooks/pre-commit.config`** — nothing to change: since contract
v2 the gate derives the required box set from the `PMO-CONTRACT.md`
template fence, so adding the checkbox above is authoritative.
(`EXPECTED_BOXES` remains only as a legacy fallback for repos without
a rules document.)

**`.githooks/pre-commit.local`** — the structural check:

```bash
DESIGN_HANDOFF_OK_FILE="$REPO_ROOT/.tmp/DESIGN-HANDOFF-OK.md"
UI_FACING_REGEX='^frontend/(app|components|lib/(brand|icons)|public/|.*\.css$)'
DESIGN_HANDOFF_REGEX='^(docs/user-journeys/|graphic-design-handoff/|frontend/public/handoff-data\.json$)'

STAGED_UI=$(printf '%s\n' "$STAGED" | grep -E "$UI_FACING_REGEX" || true)
STAGED_HANDOFF=$(printf '%s\n' "$STAGED" | grep -E "$DESIGN_HANDOFF_REGEX" || true)

if [ -n "$STAGED_UI" ] && [ -z "$STAGED_HANDOFF" ] && [ ! -f "$DESIGN_HANDOFF_OK_FILE" ]; then
  bar
  echo "✗ Design handoff missing — UI-facing files staged but no handoff updates." >&2
  echo "  Update docs/user-journeys/ + run npm run handoff:build, OR write" >&2
  echo "  .tmp/DESIGN-HANDOFF-OK.md with a one-line rationale." >&2
  bar
  exit 1
fi

EXTRA_CLEANUP_FILES="$EXTRA_CLEANUP_FILES $DESIGN_HANDOFF_OK_FILE"
```

The result: the canonical framework is unchanged; the project gets
its rule mechanically enforced; `update.sh` can refresh the canonical
files freely without clobbering the local extension.

