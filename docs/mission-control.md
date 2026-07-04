# Mission control: the contract

**Scope:** the design contract for Phase 13 (WLA-13-01). One
substrate — a state feed, a correlation model, an event log, and a
consent envelope — consumed by every mission-control client: the
HoldSpeak Desk conveyor (counterpart phase, their repo), the
Telegram interface (WLA-13-06), and whatever surface comes after.
Stories WLA-13-02 through 13-06 implement against this document;
when reality disagrees, the story amends this document in the same
commit. Claim marks as in [riders.md](./riders.md):
**verified-live** (run on this machine, date recorded), **cited**
(file pinned), **decided** (a choice this document makes and owns).

Verification date: 2026-07-04.

## The verified substrate

Phase 12 left more on the table than the scaffold specs assumed:

- **HoldSpeak's agent-session registry is richer than "cwd and a
  flag."** Verified-live at
  `~/.config/holdspeak/agent_sessions.json`: each record carries
  `agent`, `session_id`, `model`, **`repo_root`** (already
  resolved by their hook — no cwd-walking needed), `repo_anchor`,
  `project_name`, **`tmux_session` / `tmux_window` / `tmux_pane` /
  `tmux_pane_current_path`** (the driver's addressing, already
  solved), `awaiting_response`, `last_assistant_text`,
  `last_prompt`, `last_tool_name`, `transcript_path`,
  `created_at` / `updated_at`. The codex session from the
  WLA-12-05 proof is in it.
- **The feed's source of truth exists**: `dw context --compact`
  already computes projects, phases, stories, statuses, evidence
  trace, and next actionable story (`dw_pmo.api`).
- **The write path exists**: the Phase 12 actuator plugin and
  gated connector (two `dw story` verbs, allow-listed argv,
  payload-hash parity), with the dw gate keeping final say —
  crown-proven in WLA-12-03's evidence.
- **tmux 3.6b** is installed (verified-live); `send-keys` and
  `capture-pane` are the driver and preview primitives.

## 1. The state feed (implemented by WLA-13-02)

**Decided: the feed is a CLI invocation, `dw state --json`,** not
a served endpoint — the cheapest thing a consumer can poll, no
daemon, no port, works in every repo the rails are installed in.
`dw state --json --write <path>` additionally drops the same
document to a file for consumers that prefer watching one.

The feed is a *versioned, stable subset* of the context payload —
`dw context --compact` remains the CLI-facing view and may change
shape; the feed may not, without a version bump:

```json
{
  "feed_schema": 1,
  "generated_at_tree": "<git index tree at render>",
  "projects": [{
    "slug": "…", "prefix": "…",
    "current_phase": {"number": 12, "title": "…", "status": "…"},
    "next_story": {"story_id": "…", "title": "…", "status": "…"} ,
    "phases": [{"number": 12, "title": "…", "status": "open|closed",
                 "stories_done": 5, "stories_total": 8}],
    "stories": [{"story_id": "…", "title": "…", "status": "…",
                  "phase": 12, "evidence_exists": true}],
    "warnings": 2
  }]
}
```

*(Amended by WLA-13-02 in its own commit, per this document's
rule: a per-project `phases` array joined the schema before
freezing — the Desk conveyor renders phases as the belt, and the
actuator pack validates create-targets against phases that may
hold no stories yet; neither works from `current_phase` alone.
`current_phase` uses the same phase shape.)*

Schema-pinning tests fail on unannounced shape changes. Consumers
declare the `feed_schema` they were proven against, the way the
HoldSpeak pack MANIFEST declares its version range.

## 2. The correlation model (implemented by WLA-13-03)

**Decided: the correlator reads HoldSpeak's registry file
read-only** (no API dependency, no writes, ever) and joins on the
field their hook already resolves:

1. For each registry record: `repo_root` names a directory that is
   a rails repo (has `pm/roadmap/` and `.githooks/dw`) → join to
   that repo's in-progress stories from the feed.
2. Exactly one in-progress story → the session is *on* it. More
   than one → all listed, `ambiguous: true` (unknown beats
   guessed). None → `idle_on_rails`. `repo_root` not a rails repo
   → `off_rails`.
3. A record whose `updated_at` is older than a staleness TTL
   (decided: 30 minutes) is reported `stale: true`, never dropped
   silently.
4. `awaiting_response` and `last_assistant_text` ride the
   correlation verbatim — they are the Q&A relay payload the
   Telegram interface forwards.

The registry is desk-runtime state on a 0.x project: the
correlator reads every field defensively with the observed field
list pinned in its tests, and a shape change is a documented
compatibility note, not a silent break — the pack precedent.

## 3. The event log (implemented by WLA-13-04)

**Decided: an append-only JSONL file at `.git/pmo-events.jsonl`**
— beside the contract archive, surviving aborted commits, never
itself committed (events are local telemetry about the repo, not
repo content). One line per event:

```json
{"ts": "…Z", "event": "gate_refusal", "project": "…",
 "story": "…", "detail": {"rule": "…"}, "tree": "<index tree>"}
```

Taxonomy v1 — exactly the moments the machinery already observes:
`story_status` (with from/to), `evidence_capture` (with exit
code), `gate_pass`, `gate_refusal` (with rule id),
`contract_generated`, `phase_created`, `phase_closed`.

**The consent stance, binding:** events carry rails metadata only —
story IDs, statuses, rule ids, exit codes, tree hashes. Never
diff content, never transcript or prompt text, never file paths
outside `pm/roadmap`. A content-audit test enforces this. The
event log answers "what happened on the rails," not "what did the
human type."

## 4. The consent envelope for remote drivers (WLA-13-06 and after)

Three rings, strictest last:

1. **Read** (state, events, correlation, `capture-pane` previews):
   owner-identity allow-list only; previews are verbatim and
   read-only.
2. **Rails verbs** (story flips, story/project creation): every
   act is proposal → preview → in-chat approval, executed through
   the Phase 12 actuator/connector seam where it exists; project
   creation is additionally path-allow-listed to `workspace_roots`
   declared in the operator config
   (`~/.config/delivery-workbench/telegram.json`), lands only as
   rails-installed + doctor-green + first gated commit, and is
   refused outside the roots.
3. **The tmux driver** — the sharpest edge, named honestly: once a
   tmux session is **armed**, `send-keys` relays free text, and no
   allow-list can bound free text into a terminal. Therefore the
   arming *is* the consent boundary, and it is engineered, not
   promised: per-session explicit grant from the owner, default
   TTL 15 minutes, auto-expiry, visible at any time via a status
   command, revocable in one message, everything off by default.
   An unarmed session refuses (test-proven). The registry's
   `tmux_session`/`tmux_pane` fields give precise addressing —
   the driver targets the agent's own pane, never "whatever is
   focused." The dw gate below remains the last word regardless
   of who typed.

## 5. The counterpart seam

The Desk conveyor (HoldSpeak repo) and any other client consume
exactly three things: the feed (§1), the event log (§3), and the
correlation output (§2). No private scraping of `pm/roadmap`, no
reading dw internals. Each client declares its proven
`feed_schema` and the registry field list it was tested against.
Drift between a client and the substrate is a compatibility note
on the client, not a silent break.

## 6. The journal

**Decided: the journal continues into Phase 13** under the same
charter (docs/journal/README.md) — same voice, same cadence, same
honesty bar. The worked example gets richer, entry 10 onward.

## Re-pins for stories 02–06

- **WLA-13-02** implements §1 exactly: the verb is `dw state
  --json` (+ `--write`), the schema above is the contract,
  `dw context` stays independent, one real consumer converts.
- **WLA-13-03** implements §2: registry file read-only, the four
  correlation outcomes, the 30-minute staleness TTL, tests pinning
  the observed field list.
- **WLA-13-04** implements §3: the seven-event taxonomy, the
  `.git/pmo-events.jsonl` location, the content-audit test.
- **WLA-13-05** consumes §1+§3 from the Desk; its approval leg
  rides ring 2 of §4.
- **WLA-13-06** implements §4 in full; its tmux addressing comes
  from the registry fields verified above; the bot process lives
  in this repo under `integrations/telegram/` (decided — the
  HoldSpeak relay seam can join later without moving it).
