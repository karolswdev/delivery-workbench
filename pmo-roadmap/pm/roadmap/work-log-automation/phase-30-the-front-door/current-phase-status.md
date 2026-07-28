# Phase 30 - The front door

**Last updated:** 2026-07-27.

## Goal

Turn the proven autonomous engine into a reachable product. One command
boots an empty directory onto healthy rails; one guided conversation turns
a rough idea into a reviewable roadmap and a governed delivery program; one
guarded approval saves that setup; and the existing grant and certification
rails deliver the first real story. The phase closes only when a person can
start from an empty directory and a sentence, and end at a certified,
manually committed first story — with the whole journey captured as
evidence.

## Why now

Phase 29 proved the hard part: a live, cross-provider program grounded,
implemented, verified, and certified real work in this repository. What
remains between a user and that engine is not capability but access —
install refuses a directory that is not yet a git repository, roadmap
authoring is unguided prose, program configuration is four hand-written
policy files plus an undocumented driver roster, and the one real run
burned thirteen grants partly on contradictions that only surfaced at live
verdict time. The conversational intake was deferred in Phase 29 with an
explicit trigger — "after the engine proves itself on real work" — and that
trigger has fired. This phase is a front-door phase, not an
engine-expansion phase: make the existing capability reachable, prove it
from an empty directory, and prepare the landing.

## The promise

Empty directory to granted program: **one command, one conversation, three
approvals** — and each approval has a precise meaning:

1. **Setup approval** — save the roadmap, tracked program policy, and local
   non-secret driver configuration, atomically, under an exact lease.
2. **Grant approval** — issue finite runtime authority over that exact
   configuration, through the existing program plan/start surface.
3. **Certification approval** — hand-check the contract and run
   `git commit` manually, exactly as today.

Three surfaces carry the journey, and no fourth is built: the conversation
drafts, the workbench reviews, and the terminal lease consents.

## Scope

- **In:** a versioned setup-proposal contract covering idea, roadmap draft,
  optional program bundle, and local driver bindings; `dw init` as a façade
  over the existing bootstrap primitives so an empty directory becomes a
  rails-ready repository; a Scope-Chat drafting skill (build and maintain
  modes) that produces one inert typed proposal; a guarded atomic
  `dw setup preview`/`apply` surface with exact single-use leases; an
  adoption-review view inside the existing workbench routes; whole-bundle
  program validation (rubric facts vs. workflow checks, budgets vs. team
  shape, compiler/conductor node parity, driver-roster resolution);
  `dw program scaffold` as a deterministic compiler from interview choices
  to a complete checkpointed no-commit policy bundle; a generated-bundle
  review in Program Studio; lesson write-back for no-commit grants; and the
  end-to-end empty-directory exam on a release-candidate wheel with live
  cross-provider adapters.
- **Out:** any new top-level workbench pane or duplicate run cockpit;
  visual authoring of councils, nested workflows, or rubric internals
  (generated defaults plus JSON remain the expert path); browser-hosted
  chat, browser-side consent, or browser-side certification; hosted,
  shared, or multi-user workbench; new provider adapters; merge, release,
  deploy, publish, or conflict-resolution capability in any grant;
  automatic certification, project choice, or commit; cross-repository
  programs; embedding-based retrieval; guarded stranded-claim closure
  (deferred to a runtime-hardening phase unless the exam proves it blocks
  ordinary recovery).

## Hard constraint

The conversation may draft; it may never authorize. No proposal, preview,
scaffold, review, or chat transcript mints authority, writes canon, starts
a run, or substitutes for a lease. Every proposal and preview reports
`starts_work: false`; setup leases and program grant tokens are separately
minted, non-substitutable, and separately stale. Certification stays a
hand-checked contract and commit stays a human command — the front door
changes who reaches the rails, never what the rails require.

## Exit criteria (evidence required)

- [x] One documented, versioned setup-proposal contract owns the front-door
  journey — idea, roadmap draft, optional program bundle, local driver
  bindings — with closed fields, provenance, fail-closed refusals, and an
  explicit uninitialized → rails-ready → draft → reviewed → configured →
  grant-previewed state sequence (WLA-30-01).
- [x] `dw init` takes an empty directory to healthy vendored rails —
  git initialized, doctor green, status asking for project setup — as an
  idempotent façade over the existing install and bootstrap primitives,
  creating no roadmap, policy, grant, run, or commit (WLA-30-02).
- [x] A Scope-Chat skill holds one build-or-maintain conversation and
  produces one inert, schema-valid, provenance-traced proposal through
  read surfaces only, ending at a workbench review location and the exact
  next preview command (WLA-30-03).
- [x] Setup is one deliberate act: a canonical hash-bound preview with a
  single-use lease, an apply that revalidates every observed fact and
  lands the whole setup atomically or not at all, and the legacy roadmap
  mutation paths brought under the same discipline (WLA-30-04).
- [x] The workbench renders a setup proposal for human review — product
  language first, provenance and unresolved questions visible,
  configuration visibly separated from authority — under the existing
  roadmap-changes route, with review-only sessions provably writing
  nothing (WLA-30-05).
- [x] `dw program validate` preflights the complete linked bundle — rubric
  facts against reachable workflow checks, budgets against team and route
  envelopes, compiler nodes against conductor support, diversity against
  the local roster — rejecting before grant time what Phase 29 paid to
  discover at verdict time (WLA-30-06).
- [x] `dw program scaffold` deterministically compiles interview choices
  into a complete, validated, checkpointed no-commit policy bundle that
  stays inside the unsaved proposal until the one setup approval
  (WLA-30-07).
- [ ] Program Studio reviews the generated bundle as one linked object with
  whole-bundle diagnostics and a pure simulation, handing off to the
  existing exact grant preview — no new pane, no browser consent
  (WLA-30-08).
- [x] No-commit grants can request a narrow lesson-write-back capability so
  the safest runs still leave bounded, delivery-state-labeled lessons that
  later knowledge packets retrieve — with lessons still unable to satisfy
  any gate, verdict, or grant prerequisite (WLA-30-09).
- [ ] The empty-directory exam passes on a release-candidate wheel: one
  command, one conversation, three approvals, a live cross-provider
  program delivering a real first story to certified handoff within two
  grants, a lesson retrieved by a second pass, manual certification and
  commit, `dw verify` green, and a cold-install repetition — with the
  landing itself presented for the owner's release decision (WLA-30-10).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| WLA-30-01 | Contract the front-door journey | done | [story-01-contract-the-front-door-journey](./story-01-contract-the-front-door-journey.md) | [evidence-story-01](./evidence-story-01.md) |
| WLA-30-02 | Boot an empty directory | done | [story-02-boot-an-empty-directory](./story-02-boot-an-empty-directory.md) | [evidence-story-02](./evidence-story-02.md) |
| WLA-30-03 | Hold the scope conversation | done | [story-03-hold-the-scope-conversation](./story-03-hold-the-scope-conversation.md) | [evidence-story-03](./evidence-story-03.md) |
| WLA-30-04 | Make setup one deliberate act | done | [story-04-make-setup-one-deliberate-act](./story-04-make-setup-one-deliberate-act.md) | [evidence-story-04](./evidence-story-04.md) |
| WLA-30-05 | Review the adoption in the workbench | done | [story-05-review-the-adoption-in-the-workbench](./story-05-review-the-adoption-in-the-workbench.md) | [evidence-story-05](./evidence-story-05.md) |
| WLA-30-06 | Validate the whole bundle before runtime | done | [story-06-validate-the-whole-bundle-before-runtime](./story-06-validate-the-whole-bundle-before-runtime.md) | [evidence-story-06](./evidence-story-06.md) |
| WLA-30-07 | Scaffold a governed program | done | [story-07-scaffold-a-governed-program](./story-07-scaffold-a-governed-program.md) | [evidence-story-07](./evidence-story-07.md) |
| WLA-30-08 | Review the generated program in Studio | backlog | [story-08-review-the-generated-program-in-studio](./story-08-review-the-generated-program-in-studio.md) | - |
| WLA-30-09 | Let the safest runs leave lessons | done | [story-09-let-the-safest-runs-leave-lessons](./story-09-let-the-safest-runs-leave-lessons.md) | [evidence-story-09](./evidence-story-09.md) |
| WLA-30-10 | Pass the empty-directory exam | backlog | [story-10-pass-the-empty-directory-exam](./story-10-pass-the-empty-directory-exam.md) | - |

## Where we are

WLA-30-01 is delivered: `delivery-workbench-setup-proposal@1` exists as
`dw_pmo/setup_proposal.py` with its contract document
(`docs/setup-proposal.md`) and 16 unit tests wired into the core suite.
The journey state machine, inertness fields, provenance vocabulary,
tracked/local split, and refusal catalogue are now fixed vocabulary for
every later story. Implementation was executed by Sol (GPT-5.6) under
orchestration — the phase is itself an exercise of the cross-model cell
it is building the front door for.

WLA-30-02 is delivered: `dw init <path>` boots an empty directory to
healthy vendored rails as a launcher façade over `git init` +
`install.sh --skip-bootstrap`, with the nested-path refusal, idempotent
re-runs, byte-parity with plain install proven by test, and a status
surface that now reads "rails healthy, zero projects" as
`ready`/`setup-project` instead of an unhealthy roadmap. One desk
defect was found and fixed as a rider on the way: the doctor python3
check reported the PATH binary with the running interpreter's version,
breaking CLI/in-process status parity on split-interpreter desks.

WLA-30-06 is delivered: `dw program validate` preflights the complete
linked bundle — rubric facts against reachable producers, budgets
against team/diversity/fan-out and one complete green route,
compiler/conductor node parity (both sets code-derived), roster
diagnostics with a typed roster-absent finding, and tracked
execution-control refusals — with the Phase 29 defect classes encoded
as regression fixtures and CLI/MCP/HTTP sharing one canonical pure
core. Two orchestrator corrections on landing: the first cut
blanket-refused the command channel (the sanctioned check-runner shape
— exact tokenized argv, the form the phase-29 exam actually ran — is
now accepted; every deviation and every other position refuses), and it
raised bundle findings inside plain `compile_program`, breaking legacy
fixtures; the findings now live in their own channel — validate reports
all of them, grant planning refuses unconductable node types, compile
semantics are unchanged.

WLA-30-04 is delivered: `dw setup preview`/`apply` make setup one
deliberate act — a canonical change set with before/after hashes, one
single-use `setup-sha256:` lease bound to repository, branch, HEAD,
index, roadmap and policy trees, roster, and proposal; a journaled
atomic apply with planted-failure rollback; typed non-substitutable
setup vs. program tokens; public `dw adopt --apply` retired into the
flow; CLI/MCP/HTTP byte-parity. The first approval of the phase promise
now exists as machinery.

WLA-30-09 is delivered: `knowledge:lesson-writeback` — a narrow,
independently budgeted capability no-commit grants can request — makes
the safest runs epistemically productive. Lessons persist at exactly
the certified-handoff terminal, carry the closed
`certified-not-integrated` → `confirmed`/`superseded` delivery-state
vocabulary in append-only earned records, replay idempotently via
deterministic receipt ids, retrieve into knowledge packets with labels
preserved, and remain unable to satisfy any gate, verdict, or grant
prerequisite. Phase 29's named obligation is closed.

WLA-30-03 is delivered: `/dw-scope` holds one build-or-maintain
conversation and produces one inert proposal at
`.tmp/setup-proposal.json`, provenance-traced, read-surfaces-only by
skill-document fitness test, ending at the workbench review location
and the exact `dw setup preview` command with "nothing has been
saved". Two fixture conversations validate against the contract, and
the demo proved the chain end to end: fixture proposal → contract →
preview → minted setup lease. `dw init` now hands off to `/dw-scope` —
boot and conversation are one continuous journey.

WLA-30-07 is delivered: `dw program scaffold --answers` compiles a
closed typed answers object into a complete governed bundle inside an
unsaved proposal — five requested capabilities versus the hand-written
Phase 29 bundle's nine, checkpointed by default, budgets as formulas
over scope and size (12 of 24 respond to a size change in the demo),
rubric fact ids structurally bound to producing checks, same-family
seats refused over best-effort, and every emitted bundle passing
whole-bundle validation plus pure simulation as an internal
post-condition. Scaffolding writes nothing.

WLA-30-05 is delivered: the adoption review renders proposals (drafts
included — the reviewed-state gate stays with lease minting) under the
existing roadmap-changes workspace, product language first, provenance
and unresolved questions always visible, configuration separated from
authority under the exact label, marks ephemeral, sessions provably
read-only, HTTP/CLI plan facts shared. Landing it surfaced and fixed
the build-mode scaffold gap (`dw program scaffold --proposal`, rider
commit) — the composed front half now runs on a fresh `dw init` site
end to end: init → scaffold-from-draft → review → preview lease.

Next: the Studio bundle review (08), then the exam.

## Sequencing

The contract (01) gates everything. After it: `dw init` (02), the atomic
setup surface (04), whole-bundle validation (06), and lesson write-back
(09) can proceed in parallel. The setup surface precedes the
conversation (03), which submits proposals to it — corrected 2026-07-27:
the draft had the dependency reversed, but a skill cannot submit to a
surface that does not exist. The setup surface also feeds the adoption
review (05). Validation feeds the scaffold (07), which feeds the Studio
review (08). The exam (10) closes the phase and depends on everything. Rules learned the hard way: do not build the
interview before the proposal contract; do not generate policy before
validation catches the known runtime contradictions; run the exam against a
built wheel from the start, never a checkout-relative install.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The conversation quietly becomes authority | medium | Proposal is inert by contract (01); skill uses read surfaces only (03); apply requires a fresh exact lease (04); grant token is separate (08); tests assert chat and browser write nothing | Any path where a transcript, proposal, or review mutates canon or starts work without its lease |
| Visual policy authoring becomes a tarpit | high | Web scope is fixed: one adoption review under an existing route (05) plus a generated-bundle overview in Studio (08); council/rubric visual authoring is a stated non-goal | A story grows form-builders for rubric internals or workflow graphs |
| `dw init` forks a second bootstrap stack | medium | 02 is a façade over install.sh / new-project / intake with byte-identical vendored rails and defer-to-repo proven by test | Divergence between `dw init` output and `install.sh` output on the same target |
| Generated programs look valid but fail after live dispatch | medium | 06 lands before 07; every generated bundle must validate with a complete green route and pass pure simulation | A scaffolded bundle reaching a live run and refusing on a defect validation should have caught |
| Front-door work delays the overdue landing | medium | One narrow exit journey; anything not needed for "empty directory to certified first story" is deferred; 10 ends at the owner's release decision | Scope additions that do not shorten the exam |

## Decisions made (this phase)

- 2026-07-27 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-27 - Three approvals defined as setup / grant / certification;
  `dw init` is explicit consented bootstrap but not counted as an approval;
  program configuration saves under the setup approval, not a fourth -
  keeps the promise honest - design deliberation (Fable + Sol).
- 2026-07-27 - Scope-Chat produces one atomic proposal rather than mutating
  the roadmap incrementally during the conversation - partial approvals are
  worse than no approvals - design deliberation (Fable + Sol).
- 2026-07-27 - No new top-level workbench panes; extend roadmap-changes and
  Program Studio - three surfaces, three roles - design deliberation
  (Fable + Sol).

## Decisions deferred

- Whether the exam's passing result triggers immediate publication or the
  separate landing/trust ritual - trigger: WLA-30-10 exam passes - default
  is the owner decides at that moment; the recorded settling-period
  decision (f1dd337) stands until explicitly superseded.
- Guarded operator closure of stranded claims - trigger: the exam shows it
  blocking ordinary recovery - default is a dedicated runtime-hardening
  story next phase.
- Visual authoring of councils, rubrics, and nested workflows - trigger:
  observed pattern of users rejecting or hand-editing generated bundles -
  default is generated defaults plus JSON as the expert path.
