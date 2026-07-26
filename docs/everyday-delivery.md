# Everyday delivery

This guide follows one repository delivery from arrival to completion. It uses
the same words and source-backed facts in the command line and Workbench.

<!-- BEGIN EVERYDAY DELIVERY JOURNEY -->
## 1. Arrive and find the current work

Run:

```bash
.githooks/dw status
```

The answer starts with delivery readiness, current work, progress, any blocker,
and the next step. Open Workbench for the same orientation in a browser:

```bash
.githooks/dw-workbench
```

Reading these views starts no work and changes no delivery state.

## 2. Choose the delivery shape

Run `.githooks/dw setup <project>`. Compare:

- ordinary roadmap work for the usual one-story loop;
- one bounded delivery when a reviewed delivery plan and finite permission
  should coordinate several steps;
- an optional multi-phase delivery when several stories need one reviewed
  plan, team, decisions, limits, and stop conditions.

Setup saves nothing and starts nothing. Choose only the smallest shape that
fits the work.

## 3. Review the delivery plan

Before a bounded or multi-phase delivery starts, review:

- selected work and excluded work;
- the team and independent review responsibilities;
- decision owners and response choices;
- permission, cost limits, expiry, and material exclusions;
- completion rules, blockers, repair routes, and stop conditions.

Saving a draft does not start work. Starting is a separate confirmation over
the reviewed facts.

## 4. Follow live progress

The live view answers:

- What delivery is this?
- Who is doing the work and who is reviewing it?
- What has passed?
- What is blocked?
- Is a decision needed?
- What permission and cost remain?
- What is the next step?

Progress comes from saved delivery facts. Activity volume alone never counts as
completed work, and a missing fact stays unknown.

## 5. Resolve a blocker or decision

A blocker names affected work, what prevented the next step, and the safe
recovery. A decision shows only the current saved choices. Review the
consequence before confirming an action.

If a response is stale or refused, no new effect occurred. Reload current
delivery state, check what stayed unchanged, and use a fresh listed choice.
A chat message or readable summary never creates permission by itself.

## 6. Complete and prove the work

For ordinary work, capture the declared check:

```bash
.githooks/dw evidence capture <project> <phase> <story> -- <check command>
.githooks/dw story status <project> <phase> <story> done
```

Completion refuses when proof is missing. Then stage the intended files,
prepare the final commit review, verify its statements, and commit:

```bash
git add -A
.githooks/dw contract new
git commit
```

If files change after review, prepare and review the commit facts again.

## 7. Open exact records when needed

Every everyday view keeps exact identifiers, commands, paths, and source facts
under **Technical details**. Use that section for debugging, implementation,
or audit work. Machine JSON, saved event history, and architecture documents
keep their exact vocabulary and formats.
<!-- END EVERYDAY DELIVERY JOURNEY -->

For exact models and adapter behavior, see [Interop](./interop.md). For the
language boundary itself, see [Product language](./product-language.md). For
keyboard paths, focus behavior, assistive semantics, and narrow/wide support,
see [Workbench accessibility](./accessibility.md).
