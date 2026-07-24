# Team and review design

Program Studio's organization route opens on five questions:

1. Who does each kind of work?
2. Who reviews the work independently?
3. Who decides when reviewers disagree?
4. Who receives a request for help or an escalation?
5. Who checks reviewers and phase-level design?

These questions are an application view over the existing organization
compiler and assignment engine. They do not introduce a second organization
format, relax a separation rule, choose a provider, or start work.

## Shared application view

`delivery-workbench-team-review` schema version 1 is built in two contexts:

- `team_review.build_team_review` explains a tracked or unsaved organization
  design in Program Studio; and
- `team_review.build_live_team_review` explains an assigned team in the
  program control room.

Both contexts use the same section order, responsibility vocabulary,
independence states, decision-group explanations, and technical-detail
boundary. Program Studio attaches the design form as `team_review`; the live
program view attaches the assigned form under the same key.

The projection consumes canonical facts only:

| Canonical input | What the readable view uses |
|---|---|
| exact organization document | responsibilities, candidate groups, help, replacement, decision groups, audit, and source pointers |
| organization validation | affected responsibility, unsafe behavior, correction, and exact diagnostic |
| compiled organization | logical assignment witnesses and policy feasibility |
| organization simulation | finite scheduling and decision-group facts |
| Studio authority preview | content-safe local provider/model/auth/principal resolution |
| graph/config round trip | semantic and layout preservation |
| assigned roster | exact live seats, activity, identity, work area, session, and separation proof |

It groups and explains those inputs. Eligibility, assignment, review outcomes,
decision outcomes, escalation handling, and permission remain owned by their
existing exact cores.

## Policy-ready is not runtime-proven

A valid organization can prove that compatible separate candidates exist.
That is `policy-ready`: the candidate groups can supply different logical
candidates, profiles, and work areas.

It cannot claim that a runtime reviewer is independent before assignment.
`runtime-proven` requires the assignment engine to verify all of these exact
facts:

- different logical candidates;
- different profiles;
- different principal fingerprints;
- different work areas;
- different session bindings; and
- read-only review without a smuggled write permission.

Provider or model diversity is an observation, not proof of independence. Two
models may share a principal or session; one provider may expose genuinely
separate principals. The ordinary summary therefore states the responsibility
and proof status, while **Technical details** retains provider, model vendor,
model family/revision/binding, auth-domain fingerprint, principal fingerprint,
capability fingerprint, work area, and session binding as distinct fields.
Credentials and arbitrary commands are never exposed.

## Ordinary authoring

The default **Team & review** view edits the cloned exact source document.
Its sections own these targeted fields:

- **Work responsibilities:** team purpose, responsibility name and duty,
  required coverage, cardinality, and first-choice candidate group.
- **Independent review:** read-only or isolated work area, the responsibilities
  that must remain separate, and the exact work a reviewer may judge.
- **Contested decisions:** participating responsibilities, required reviewer
  agreement, distinct identities, decision owner, decision method, objections,
  and preserved dissent.
- **Help and escalation:** bounded help relationships, finite replacement,
  backup groups, history preservation, and the route after exhaustion.
- **Review of review:** review-audit coverage and owner, overturn route, and
  architecture responsibilities that run only at separately declared plan
  boundaries.

Renaming a responsibility carries same-document references through help,
judgment, independence, decision-group membership, decision owner,
review-auditor, objection weights, and layout keys. Other exact fields remain
untouched. The browser never rebuilds an organization from the summary.

Panels, multi-perspective decision groups, dissent, named decision owners,
review auditing, and architecture review appear only when declared. Their
plain descriptions say when they run and what their outcomes may change.
Weights, thresholds, packet bounds, schemas, resource groups, finite
discussion budgets, stable IDs, and raw configuration remain under
**Technical details**.

## Understandable refusal

An invalid design still uses the existing organization validator. The
ordinary correction names:

- the affected team/review question;
- the exact conflicting responsibility names;
- the behavior that cannot be proven safely; and
- a corrective choice.

The adjacent technical disclosure keeps the original source, JSON pointer,
diagnostic code, message, and remediation. Unknown fields remain in the draft
and make save refuse; no field is silently dropped. A valid advanced
organization, including decision groups, dissent, review audit, and
architecture roles, round-trips with the same semantic and layout identity.

## Escalation and authority

Internal help can target only declared team responsibilities. An exhaustion
route may block, wait for a named person, end the delivery, or ask the
separately authorized delivery owner. The organization document does not name
or impersonate that external owner and cannot grant itself handling
authority.

Drafting, checking, simulating, switching sections, opening technical detail,
and abandoning a draft write nothing and start nothing. **Review this save**
continues to use Program Studio's exact preview and fresh-fingerprint apply
boundary. Confirmation can write only the named tracked organization file; it
creates no permission, run, process, observer, notification, or roadmap
change.

## Verification

Run:

```sh
python3 pmo-roadmap/tests/dw-core-tests.py ProgramStudioTest ProgramSurfaceTest
bash pmo-roadmap/tests/workbench-explorer.sh
bash pmo-roadmap/tests/workbench-ui-smoke.sh
python3 pmo-roadmap/tests/product-language-contract.py
python3 pmo-roadmap/tests/usability-journey-contract.py
```

The focused tests cover the simple independent pair, the advanced canonical
organization, readable decision/agreement/dissent/audit explanations, exact
local provenance, invalid separation and unknown-field refusal, live
runtime-proven reuse, package export, and wide/narrow Program Studio renders.
