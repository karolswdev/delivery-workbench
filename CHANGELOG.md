# Changelog

Each release summarizes the roadmap phases that shipped it. Every
phase links its audit-style final summary — the roadmap under
[`pmo-roadmap/pm/roadmap/work-log-automation/`](./pmo-roadmap/pm/roadmap/work-log-automation/)
holds the full story-by-story evidence trail, and the version below is
single-sourced from `dw_pmo.__version__` (test-asserted against
`dw --version`, the plugin manifest, and this file).

## Unreleased

`/dw-scope` now holds one build-or-maintain scope conversation and writes one
inert, provenance-traced draft to `.tmp/setup-proposal.json`. Build mode starts
with a rails-ready repository and an idea; maintain mode reads the codebase and
roadmap first. Ambiguity stays visible as unresolved questions, revisions keep
unchanged sections byte-stable, and the command ends at Workbench review plus
the separate `dw setup preview .tmp/setup-proposal.json` handoff. It cannot
write canon, apply setup, start work, grant authority, certify, or commit.

Setup is now one deliberate act. `dw setup preview <proposal-file>` returns a
canonical complete write set and an exact `setup-sha256:` lease bound to the
repository, branch, HEAD, index, roadmap, policy, driver roster, proposal, and
every before/after hash. `dw setup apply --proposal <id> --expect <token>`
revalidates those facts, consumes the token once, and lands roadmap, program
policy, and local driver bindings through a journaled transaction that rolls
back every byte on failure. MCP and localhost HTTP expose the same core preview
and apply documents. Setup still starts no work and creates no grant,
certification, or commit; setup and program tokens are typed separately.
Public `dw adopt --apply` is retired as the old unleased multi-file side door,
while the existing read-only `dw setup [project]` view and single-file
phase/story conveniences remain.

Program validation now preflights the complete linked bundle before grant
planning. It cross-checks rubric mechanical facts against reachable workflow
producers, team and verifier requirements against finite budgets, compiler node
kinds against conductor support, complete green routes through the existing
workflow simulation graph, and provider diversity against the local driver
roster. Roster-absent hosts receive a typed unverifiable-local finding; present
rosters expose only closed non-secret capability diagnostics. Tracked
executables, argv, environment, and driver flags refuse with source JSON
pointers. CLI, MCP, and localhost HTTP validation share one pure canonical core.

`dw init <path>` now takes an empty directory or empty Git repository to
healthy vendored rails. It composes `git init` with the packaged
`install.sh --skip-bootstrap`, refuses accidental nested repositories, and
leaves project creation to the intake conversation. Re-running reports the
components already present without changing them. Repositories with healthy
rails but no roadmap project now receive a `setup-project` next action from
`dw status` instead of treating that state as corruption.

Checkpointed no-commit programs may now request the narrow
`knowledge:lesson-writeback` capability. At the exact certified handoff it
spends one finite `max_lesson_writebacks` unit and appends bounded lessons labeled
`certified-not-integrated`, with run, story, candidate, adapter/profile, verdict,
and deterministic receipt provenance. Replay neither duplicates a record nor
spends another unit. A later exact delivery commit appends `confirmed`; a
superseding integration appends `superseded`. Knowledge packets keep the label
visible, and authority paths still cannot use any lesson as proof.

One answer before agents act: Phase 22 adds the stamped, deterministic
`delivery-workbench-status@1` briefing across `dw status`, MCP
`dw_status`, `GET /api/status`, the workbench overview, and every generated
agent rider. The object composes the existing doctor, roadmap, Git,
contract, gate, current-work, and holds authorities; adapters carry no
decision logic, reads emit no events, ambiguous projects are never guessed,
manual certification stays manual, and `commit` appears only when a live
side-effect-free gate inspection passes. A packaged fresh-consumer exit exam
now asserts byte-equal CLI/MCP/HTTP recommendations through install, update,
evidence, the specialized guarded `finish-story` transition, staging,
contract staleness, certification, trailers, archived contract, verified
commit, and the next clean story. Full detail: [Phase 22](./pmo-roadmap/pm/roadmap/work-log-automation/phase-22-agent-briefing/current-phase-status.md).

Phase 23 closes the read→act gap: `dw step` keeps `dw status` pure while
turning one reviewed recommendation into a state-bound act. Its stamped
`delivery-workbench-step@1` preview hashes the complete current briefing;
apply requires that token, re-reads state, admits only an action id plus
entire argv shape from a second closed table, starts at most one child, and
stops. Same-action stale state, unknown or modified argv, manual choices,
certification, and commit all refuse before process start. That core/CLI slice
is the foundation of the completed
[Phase 23](./pmo-roadmap/pm/roadmap/work-log-automation/phase-23-deliberate-step/final-summary.md).
Apply now returns a bounded `delivery-workbench-step-result@1` for success,
failure, interruption, spawn failure, and non-started refusal. Atomic local
claims prevent replay even for read-only actions, and exactly one content-
safe `step_execution` event correlates every started child without recording
argv or output.
The handrail is now transport-complete: MCP adds pure `dw_step` and exact-token
`dw_step_apply`; the local HTTP API adds `GET /api/step` and
`POST /api/step/apply`. All three adapters return byte-equal preview/result
core documents, accept no caller-supplied argv, refuse replay without another
child, and keep certification and commit outside the capability. A freshly
installed fixture proves the contract end to end and CI pins the new tool and
route inventories.
The browser now makes that trust boundary visible: an applicable overview
action opens a separate review panel with the state token, authorized argv,
and exact CLI fallback; a second control applies one lease, refreshes, and
stops. Stale confirmation says nothing started; prohibited/manual,
certification, and commit states have no apply control. The canonical rider
brief and generated Claude/Codex/pi/plugin copies teach the same fresh-token,
exact-command, stop-after-one discipline and mechanically drift-check it.
The packaged closeout now proves the whole handrail rather than its imports:
a wheel-installed consumer compares CLI/MCP/HTTP before every authorization,
rotates seven one-step applies without reconstructing the underlying argv,
and reaches an evidence-backed, trailered, contract-archived, history-verified
commit. A workspace change leaves `continue-story` as the action but expires
the old token; all three adapters report `started: false` and add zero step
events. Certification and both commits refuse through every step surface and
are performed only by the fixture operator.
The closeout matrix passes on Python 3.9 and the local interpreter, renders 20
browser viewports, exercises every agent and distribution surface, and runs
the provisioned Telegram and pinned HoldSpeak hosts. Homebrew remains an
explicit local abstention because its smoke will not uninstall the operator's
existing formula; clean-machine macOS CI owns that proof.

Phase 24 now has its orchestration architecture, pure compiler, and rich
authoring surface. Delivery Workbench **can coordinate** from an exact, visually authored
score: research/synthesis/implementation/review/repair agents, dependencies
and concurrency, prompts/context, typed output conventions, deterministic
checks, fail routes, retries, budgets, approvals, and terminal meanings. The
stdlib-only `dw_pmo.orchestration` core owns the closed schema, normalization,
JSON-pointer diagnostics, semantic/document hashes, graph/capability/path/
bound checks, and a pure scheduling simulation. `dw orchestration
list|show|validate|simulate` and an ordinary installed reference preset prove
the same behavior from a wheel while starting no work and writing no events.
The delivered Workbench editor renders the whole typed score as an accessible
SVG graph with a complete property inspector, live compiler diagnostics,
capability/output lineage and scheduling simulation, plus lossless JSON. Save
and delete use a contained, stale-safe preview→diff→atomic-apply boundary with
rollback; Firefox desktop/mobile and the installed server exercise it. A
tracked score starts nothing—a separate, expiring and revocable grant over
its compiled hash is now the delivered authority boundary. `dw run plan` is a
pure binding over the exact compiled score, local repository/HEAD/status/story
facts, profiles/capabilities/workspaces, every finite budget, expiry, and
permanent exclusions. `dw run start` requires that complete fresh plan, its
single-use token, explicit approval, and an operator identity before atomically
publishing immutable plan/score/grant documents and the first hash-chained
ledger event. Ledger replay ignores its disposable projection cache and fails
closed on truncation, corruption, or forks; cross-process locks, ledger-head
tokens, node-attempt/idempotency claims, budget counters, and immediate
pause/resume/revoke/cancel transitions prevent replay or dispatch after
authority changes. No provider work is dispatched by this authorization slice.
The provider-neutral driver slice now turns an active node claim into a closed,
hash-bound work packet with bounded prompt/context, validated artifact inputs,
exact output conventions, a capability request, workspace identity, deadline,
and permanent exclusions—never provider argv or credentials. Operator-local
profiles truthfully advertise adapter-owned sandbox/network/interrupt support;
unsupported requests refuse before launch. The deterministic fixture driver
proves concurrent read-only research, schema/citation/section validation,
synthesis fan-in, restart-safe idempotency, timeout/nonzero/lost/cancel/oversize
states, separate writer worktrees, resource locks, diff-scope refusal, and no
implicit integration. An authenticated installed `codex exec` smoke separately
proves the real read-only adapter with explicit sandbox/no-approval/ephemeral/
bounded-stream controls and records only a receipt plus artifact hash. The
deterministic conductor now makes those components an orchestration runtime.
One pure scheduling decision and one idempotent `dw run tick` reconcile
existing claims before dispatch, order eligible nodes by the immutable score,
enforce concurrency/resource/start/time/artifact budgets, and record every
receipt and finite retry/repair/approval/pause/abort route. Exact command
checks run without a shell or host-secret environment in contained check or
writer worktrees with timeout, stream and write-snapshot bounds; file/schema/
diff/rail built-ins use the same persistent receipt seam. Restart after claim,
driver start, artifact collection, or check completion polls persisted work
instead of duplicating it. Cancellation lands before interruption, stale rail
leases never start, external commits are observed without a shipped claim,
and all green paths stop at `awaiting-certification`. Bounded `run supervise`
is only repetition over the same tick, while exact checkpoint decisions remain
fresh-ledger-head acts.

The run is now a first-class interoperable product surface. CLI JSON, MCP
`structuredContent`, and HTTP `data` carry byte-equivalent plans, projections,
views, previews, receipts, and bounded streams. Applying adapters accept only
identifiers, bounded decisions/reasons, and fresh tokens—not prompts, score
semantics, provider configuration, or check argv. The Workbench Run tab
replays the authoritative graph with attempts, parallel agent/check sessions,
typed artifact lineage, budgets, fail/repair routes, checkpoints, hash-chain
timeline, and explicit pause/resume/revoke/cancel controls. It refreshes and
opens streams only on request and exposes no generic terminal, retry override,
elevation, certification, or commit shortcut.

The packaged closeout proves the entire framework from a Python-3.9-built
wheel in a fresh consumer. Two research agents start concurrently; a planted
crash recovers with zero duplicate dispatch; typed and citation-bound outputs
fan into synthesis; implementation runs in its own worktree; a planted check
failure follows exactly one configured repair route and passes recheck; six
compiler and five runtime red cases refuse; CLI/MCP/HTTP/Run-view documents
stay equal; and the conductor stops at `awaiting-certification`. Only the
fixture operator reviews, certifies, and commits, after which `dw verify --all`
and `dw check` pass. A separately provisioned authenticated Codex specimen
proves the real driver seam without turning model output into the CI oracle.
The full 297-test dual-Python, 32-render browser, distribution, optional-host,
agent, docs, and history matrix is recorded in the
[Phase 24 final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-24-bounded-orchestration/final-summary.md).

Phase 25 closes the outward loop without widening authority. Content-excluded,
hash-chained SCM facts, honest driver activity, score-and-grant-bounded
at-most-once nudges, cursor-replay ledger/signal streams, durable operator
notifications, typed checkpoint survival, and a least-privilege Claude Code
adapter all compose over the same run ledger. The wheel-installed exit exam
walks red CI through repair, review, restart, checkpoint, notification, and
operator-only certification while the no-authority observer and every refusal
remain explicit. Full detail:
[Phase 25](./pmo-roadmap/pm/roadmap/work-log-automation/phase-25-outward-signals/final-summary.md).

Phase 26 is complete and remains separately opt-in. Its delivered slices compile
multi-phase scope, finite hierarchical workflows, separated delivery
organizations, bounded councils, governed verdicts, lossless Program Studio
policy, and an exact finite program grant over the resolved
provider/model/auth roster. WLA-26-09 adds an embedded replay-first conductor:
one tick reconciles before retry, claims at most one exact act, and conducts
implementer/check/repair, independent verification, council/meta/obligation,
typed structural loops, and final-story master-architect boundaries with
crash-safe immutable receipts. It also consumes already-observed Phase 25 SCM
facts through content-safe hashes, delivers finite program-declared nudges only
to an already-run agent, reruns causally stale verification, freezes every
scope-reachable seat/port, carries non-blocking obligations across exact
story/phase selection, blocks on blocking obligations, and completes only
through one claim-bound proof of the pure planner's full-scope result.
WLA-26-10 adds the separate exact delivery adapter: a pure preview over the
certified patch/proof/repository/roadmap/remote facts; independent claims and
receipts for integration, evidence, canonical story/phase transitions,
contract generation, objective and governed machine attestation, gated commit,
range verification, and optional no-force fast-forward push; all-old/exact-new
crash reconciliation; and deduplicated obligation materialization plus
accountable disposition. A two-story bare-remote fixture plants crashes after
every effect and receipt while proving one phase transition and zero duplicate
commits or pushes. WLA-26-11 adds the canonical content-safe program surface:
byte-equivalent CLI/MCP/HTTP/Workbench inventory and control-room views,
verified ledger tail and explicit bounded streams, read-only SSE cursor replay,
preview-bound grant/tick/supervision/request/control acts, resolved
organization/execution/diversity projections, and typed intervention,
disagreement, loss, obligation, budget, integration, and completion
notifications. Supervision is an explicit finite invocation returning every
tick; no read, Workbench open, or SSE connection starts a program or confers
authority. The Python-floor fresh-wheel exit exam now runs three stories over
two phases after one continuous grant, including independent fail/repair/pass,
a dissent-preserving council, meta-audit, architect gates, exact
evidence/integration/certification/commit/push rails, planted crash recovery,
ledger/SSE parity, and the complete refusal matrix. A separate fresh consumer
proves ordinary and bounded-run behavior with no ambient program machinery.
The deterministic Claude/Sonnet-like and pi/OpenRouter/Kimi-like fixtures use
no credentials; the optional live-agent specimen remains honestly not run.
Full detail:
[Phase 26](./pmo-roadmap/pm/roadmap/work-log-automation/phase-26-autonomous-delivery-programs/final-summary.md)
and the [program contract](./docs/programs.md).

Phase 30 starts by fixing the front-door vocabulary before adding a producer or
apply surface. `delivery-workbench-setup-proposal@1` is a closed, bounded,
canonical contract for project intent, a provenance-traced roadmap draft,
optional opaque program policy, local non-secret driver bindings, and explicit
unresolved questions. Its six journey states permit only named adjacent moves
plus reviewed-to-draft revision; every proposal and proposal-shaped preview
refuses unless all four authority exclusions are false. Parsing, validation,
serialization, and transition checks are pure and create no file, process,
grant, certification, or commit. Full detail: [setup proposal
contract](./docs/setup-proposal.md).

This section is release-ready input, not a publication claim: the package
remains v1.14.0 and no version bump, tag, release, PyPI upload, or formula
change has been performed.

## v1.14.0 — 2026-07-11

The group grows hands: the second ccgram absorption (upstream
v4.3.11, MIT). The Telegram interface becomes a first-class group
surface — the pane arrives as a PICTURE (`/screen` renders ANSI
color to PNG with an in-place refresh button; `/live` serves an
auto-refreshing photo behind the same content-hash gate the text
view always had, `/live text` on purpose; rendering is an optional
Pillow capability with an honest text fallback — the published
package still has zero dependencies); the buttons grow up (the
toolbar is per-harness configuration with key/text/builtin action
types and a CLOSED builtin table a config can never extend; pushed
agent questions carry arrow/Enter/Esc/📸 keyboards that drive the
actual TUI prompt — bound + armed only, and a nav tap never arms;
the slash menu registers with Telegram); and consent in a group
belongs to a person, not a room — pairing records the
owner-of-record, and consent-bearing commands, every button tap,
and the steering relay answer to that one identity, closing the
gap where any member of a paired group held full owner power.
Every keystroke still enters through the driver's one door;
108 → 147 interface tests. Full detail:
[phase 20](./pmo-roadmap/pm/roadmap/work-log-automation/phase-20-group-grows-hands/current-phase-status.md),
and the ledger's second-absorption section in
[docs/absorption-ccgram.md](./docs/absorption-ccgram.md).

## v1.13.0 — 2026-07-11

The front door: open-source readiness. An audit of everything a
stranger meets (no blockers found) drove the fixes that ship here —
PyPI metadata completed (Repository/Changelog/Issues links, the
license as an SPDX expression `License-Expression: MIT`, author
contact), the LICENSE holder normalized, badges on the README, and
the README caught up with the shipped surface: twelve MCP tools,
the `dw board` / `dw holds` / `dw story show` verbs, parked work
and the receipts-and-links walk in prose, and the interop contract
linked. Full detail:
[phase 19](./pmo-roadmap/pm/roadmap/work-log-automation/phase-19-front-door/current-phase-status.md).

Earlier in this release — every element answers: the interop layer. The board's elements are
browsable by machines — every card, lane, and holds-ledger entry
carries `paths` (repo-relative story/evidence/phase-status
receipts) and `links` (workbench story/trace routes), minted by one
helper and pinned by a no-rot test that resolves each emitted link
through the API; the board model is stamped
(`delivery-workbench-board`, schema_version 1). `dw story show
[--json]` browses one story whole (bodies, parsed captured runs,
receipts) from the same `story_detail` core the workbench story
route now serves; MCP gains the read surface — `dw_board`,
`dw_holds`, `dw_story_show` — byte-equal with the CLI's `--json`
verbs and census-pinned read-only; and `docs/interop.md` is the one
versioned contract over all three transports, with a parity test
deriving the inventories from code so a new surface cannot ship
undocumented. Full detail:
[phase 18](./pmo-roadmap/pm/roadmap/work-log-automation/phase-18-interop-layer/current-phase-status.md).

Earlier in this release — work that waits: holds, pivots, and the board. Parked work becomes
first-class — `on-hold` (synonym `paused`) joins the write
vocabulary as an open status distinct from `blocked`, and every
park carries a mandatory `--reason` written into the status cell as
decoration the reader sees through (`status_note` recovers the
why). Whole phases pause and resume (`dw phase pause --reason` /
`resume`) with the state in the phase header and README index row;
`dw next` skips parked work but names the counts; the new
`dw holds` is the greppable ledger of everything waiting; and the
new `dw board` + the workbench's `#/board` draw the kanban — a
swimlane per phase, six status columns, evidence ticks, paused
lanes dimmed behind their reason, closed lanes folded, and drag
moves that ride the existing guarded preview→apply mutation flow
(a park demands its reason; done still demands evidence; no new
write path). The gate is untouched. Proven per story by captured
suite runs plus live walks; the flagship tree served as specimen
and proof — `dw holds` surfaced a hold forgotten for 68 phases.
Full detail:
[phase 17](./pmo-roadmap/pm/roadmap/work-log-automation/phase-17-work-that-waits/current-phase-status.md).

Earlier in this release — the flagship tree: receipts-first reading. The read layer meets a
decade-shaped legacy roadmap where it is — story tables are
recognized by their header cells (the Evidence column optional),
decorated statuses (`**done** (2026-07-07 — …)`, `CLOSED ✅ (6/6)`)
normalize to comparable tokens at word boundaries (`host-complete`
never reads as complete), evidence pairs against the
`evidence-story-NN.md` receipts on disk rather than table prose,
struck-through rows are retired history with no demands, table-less
phases read file-derived under one legible warning, the README's
Current-phase pointer names `current_phase` in the state feed, and
`dw next` never proposes work from a phase holding a final-summary.
The write gate is untouched and exactly as strict. Proven against
the flagship consumer's real 86-phase tree: 397 reported errors
fall to 31, every survivor a real desync.
Full detail:
[phase 16](./pmo-roadmap/pm/roadmap/work-log-automation/phase-16-flagship-tree/current-phase-status.md).

## v1.12.0 — 2026-07-05

The fifth window: the local `dw-workbench` browser gains a
read-only mission-control belt (`#/mc`, `GET /api/missioncontrol`)
— phases as segments, stories as chips with the next actionable in
accent, live agent sessions pinned to their stories by a
server-side decision kernel, honest off-belt buckets, and a
refusal-first rail-events ticker. Read-only under a fitness guard:
the mutation dispatcher can never learn the mission-control path.
One substrate now renders on the CLI, the phone, the HoldSpeak
Desk, the workbench browser, and (contract landed) the iPhone.
Full detail:
[phase 15 final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-15-mission-control-on-the-workbench/final-summary.md).

## v1.11.0 — 2026-07-04

The Absorption: the pocket desk grows up. Phase 14 studied
[alexei-led/ccgram](https://github.com/alexei-led/ccgram) (MIT,
lineage six-ddc) in full and re-interpreted its operational
excellence under the workbench's consent spine — twenty ideas
mapped absorb/transmute/refuse in
[docs/absorption-ccgram.md](./docs/absorption-ccgram.md). The
Telegram interface gains: a **dw-native hook seam** (`dw hook
install`) so a blocked agent reaches the phone in ~1 s;
**entity-based message formatting** with nothing left to escape, a
FIFO send queue, and edit-in-place cards; **topics-as-projects** —
one forum topic per rails repo, and inside a `/steer`-bound
session, **conversation flows** with no per-message tap (consent
gates entry, not every utterance); the **driver's TUI manners**
(settle-then-Enter, capability-flag harnesses, `/live` view,
`/toolbar`); and **`/send` behind seven locks** (secrets,
gitignore, gitleaks, and the workbench's own state files all
refuse). Architecture fitness tests guard the consent floor in CI.
ccgram's thesis — sit on the multiplexer, never wrap the SDK — is
kept; its user-ID auth is refused (pairing stands). Full detail:
[phase 14 final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-14-absorbing-ccgram/final-summary.md).

## v1.10.0 — 2026-07-04

Mission control, whole: Phase 13 gave the rails one substrate — a
frozen state feed (`dw state --json`, `feed_schema` 1), a
session↔story correlation document (`dw sessions --json`, with
`--registry` for fixtures and nonstandard desks), and an
append-only event log (`dw events`, seven types, rails metadata
only, consent enforced in code) — and three surfaces consuming it
with the same gate above all of them. The Telegram interface
(`integrations/telegram/`) steers from a pocket: pairing-based
owner binding (single-use short-TTL tokens, hashed at rest),
proposal→approval for every act, one-tap arming for replies into
tmux sessions with pane-ownership verified before a single
keystroke, project lifecycle path-allow-listed to workspace roots,
and a credential grep in CI. The HoldSpeak Desk conveyor (their
Phase 82) renders phases as the belt and steers through the same
two allow-listed story verbs. The crown case held on every
surface: an approved done-flip without evidence is refused, banner
verbatim. Full detail:
[phase 13 final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-13-agentic-mission-control/final-summary.md).

## v1.9.0 — 2026-07-04

One canonical agent brief, every surface: Phase 12 made Delivery
Workbench a plug-n-play rider for Claude Code, Codex, and pi — the
full story loop proven end-to-end under all three, from `dw next`
to a gated commit — and gave HoldSpeak its first real plugin packs:
a roadmap-alignment synthesizer that grounds meetings in story IDs
(hallucinations demoted to drift by code, not trust) and a story
actuator stacking HoldSpeak's propose→approve→execute consent on
top of the dw gate, which keeps final say. `dw rider install
codex|pi|holdspeak` wires each surface from one canon;
hand-edited drift in any rendered copy is a `dw check` ERROR;
`dw doctor` reports per-rider wiring honestly. Evidence capture
under `dw-mcp` no longer wedges the server (stdin bug found by
dogfooding, fixed same session). The whole phase was journaled in
the moment — refusals, dead ends, and failed captures included —
as the worked example ([docs/journal/](./docs/journal/README.md)).
Phase 12 final summary: [phase-12-holdspeak-symbiosis-and-agent-riders](./pmo-roadmap/pm/roadmap/work-log-automation/phase-12-holdspeak-symbiosis-and-agent-riders/final-summary.md).

## v1.8.0 — 2026-07-03

The gate's guarantees now survive the pull-request boundary: what a
fork can carry, what a merge can corrupt, and what the repository
now refuses to let happen.

### Phase 11 — Contribution Rails ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-11-contribution-rails/final-summary.md))

`docs/contribution-rails.md` classifies every guarantee across the
fork boundary: structural rules stay mechanically verified by the
required PR-range check, contract facts and certification remain
attestations anchored by the digest trailer. The
`contributor-flow.sh` suite proves the green path (gated branch,
PR-range verify, rebase merge, main verification green with
rewritten SHAs) and demonstrates both squash corruption modes with
exact rule ids — including the finding that the local gate itself
refuses a two-flip squash before the verifier ever sees it. The
repository is now rebase-merge only, CONTRIBUTING walks the whole
fork-to-merged loop in plain language, and the PR template asks for
the story, the evidence, and a green range verify.

## v1.7.0 — 2026-07-03

Agents get a first-class programmatic surface: the rails now speak
MCP natively, with the same guardrails the CLI enforces — and the
same deliberate refusals.

### Phase 10 — Agent Interface ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-10-agent-interface/final-summary.md))

A stdlib-only MCP stdio server (`dw-mcp`, pinned protocol
2025-06-18) exposes nine tools as thin adapters over the exact core
functions the CLI calls: orientation (`dw_context`, `dw_next`,
`dw_check`, `dw_doctor`), verification (`dw_verify`, `dw_gate`),
and guarded mutations (`dw_story_status`, `dw_evidence_capture`,
`dw_contract_new`) with CLI-identical refusals proven by parity
tests. Deliberately absent, enforced by test: no certification tool,
no commit tool — attestation cannot be mechanized without hollowing
it out. Vendored by install/update, carried by the package and
formula, wired through an append-only `.mcp.json` seam, and proven
by a live Claude Code session driving a story from backlog to done
over MCP tools alone.

## v1.6.0 — 2026-07-03

The gate's guarantees now hold beyond the local clone, and the
framework installs without cloning its repository: remote history
verification enforced in CI, a first real external adoption with its
friction paid back, pip/pipx packaging, and a Homebrew formula —
all shipped through the gate they extend.

### Phase 8 — Remote Verification and Adoption ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-8-remote-verification-and-adoption/final-summary.md))

Extended trust past `core.hooksPath`: `docs/remote-verification.md`
classifies every gate rule as remotely re-derivable or
attested-only; `dw verify` re-checks pushed history with the gate's
own rule ids under an epoch policy (no per-sha exceptions); the
`verify-history` CI job enforces the full sweep on every push and
PR, red-path proven against a smuggled `--no-verify` flip; bundle
rationales became `PMO-Bundle:` trailers, making atomicity fully
re-derivable. A real external repository (133 commits) adopted the
rails headlessly, shipped a gated story, and its five friction
findings were triaged with four fixes landed.

### Phase 9 — Distribution and Installability ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-9-distribution-and-installability/final-summary.md))

Made the bootstrap the unit of distribution while per-repo vendored
rails stay the only gating authority: `pyproject.toml` packaging
with the full vendorable payload inside the wheel and a global `dw`
that defers unconditionally to `.githooks/dw` in adopted repos; a
proven upgrade path from real v1.5.0 rails (content byte-untouched,
`update.sh --check` reporting content-based staleness); a Homebrew
formula proven from a local tap with a pip-free, venv-free install;
and this release, with version parity test-enforced across every
surface. PyPI and public-tap publication remain deliberate
one-command follow-ups.

## v1.5.0 — 2026-07-03

First public release: the framework, its workbench, its agent
surface, and the documentation pass that made it teachable — all
shipped through the framework's own gate.

### Phase 0 — Architecture ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-0-architecture/final-summary.md))

Established the architecture contract for work-log automation:
explicit consent, a two-step pre-commit capture / post-commit
finalize lifecycle, a deterministic Markdown entry schema, a deferred
summarizer boundary, and install/update plus git edge-case policies.
No model calls in the commit path — a rule everything later obeys.

### Phase 1 — MVP ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-1-mvp/final-summary.md))

Shipped the deterministic, opt-in MVP: PMO certification separated
from work-log consent, pre-commit capturing consented staged
payloads, post-commit appending local daily entries only after the
commit exists, and install/update distributing the canonical hooks
and helpers. Local by default.

### Phase 2 — Hardening ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-2-hardening/final-summary.md))

Hardened the automation: a deferred summarizer helper behind an
explicit opt-in command with timeout and output limits, deterministic
fallback behavior, and documented privacy controls around consent and
path exclusion. The source `*-work-summary.log` stays authoritative.

### Phase 3 — Rollout ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-3-rollout/final-summary.md))

Rolled the work-log extension out as opt-in and local-first, with
project exclusions (`PMO_WORK_LOG_EXCLUDE_REGEX`), documented privacy
limits, and temporary-repo regression coverage.

### Phase 4 — CLI maintenance tools ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-4-cli-maintenance-tools/final-summary.md))

Added the `dw` roadmap maintenance CLI: create phases and stories,
view trees, select the next actionable story, pair evidence, update
status, close phases, and report drift — Markdown stays the source of
truth, and a story cannot flip done without paired evidence.

### Phase 5 — Workbench interaction layer ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-5-pmo-workbench-interaction-layer/final-summary.md))

Delivered the workbench: a localhost read-only explorer, health/drift
console, intent-to-proof trace timeline, and a guarded editor routed
through core mutation plans — preview, diff, content-bound
fingerprints, stale/tamper 409s, rollback, revalidation. One core
(`dw_pmo`) now serves the CLI, the gate, and the workbench.

### Phase 6 — Agent rails hardening ([final summary](./pmo-roadmap/pm/roadmap/work-log-automation/phase-6-agent-rails-hardening/final-summary.md))

Made the repo enforce itself end-to-end: the single-sourced gate
engine with parity-proven hooks, verified contract v2 (index-tree
freshness, gate-decided ceremony tiers), evidence-content lints with
captured runs, de-personalized canon under CI lint, and a full
lifecycle drivable from CLAUDE.md alone. CI runs ubuntu + macos,
shellcheck, and a python 3.9 floor job.

### Phase 7 — Documentation mastery ([phase folder](./pmo-roadmap/pm/roadmap/work-log-automation/phase-7-documentation-mastery/))

Audited every doc surface and rewrote to the audit's dispositions:
root README and architecture guide where every behavioral claim names
its proving test, canon accuracy with doc-parity tests, a Claude Code
plugin with parity against the managed agent-docs block, regenerated
demos/screenshots/social preview each naming its regeneration script,
docs CI (link/anchor/image lint plus quickstarts executed as
printed), and this release itself — contributing guide, code of
conduct, templates, changelog, tag.
