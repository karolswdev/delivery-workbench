# WLA-17-01 - on-hold enters the write vocabulary; every park carries a reason

- **Project:** work-log-automation
- **Phase:** 17
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** WLA-17-02, WLA-17-03, WLA-17-04, WLA-17-05, WLA-17-06
- **Owner:** unassigned

## Problem

Teams park work deliberately — a pivot, a deprioritization — and the
vocabulary can only say `blocked`, which means something else (an
impediment, not a choice). Worse, neither carries a *why*: the
flagship tree holds ten stories `in-progress` because "waiting behind
phase 91" has no spelling. The reader learned to see through
decorated statuses in phase 16 (`normalize_status`); the writer can
now use that same convention to record honest holds.

## Scope

- **In:** `model.py` — `HOLD_STATUSES = {"on-hold", "paused"}`
  (canonical `on-hold`; `paused` gates identically, mirroring the
  done-synonym pattern), folded into `STORY_OPEN_STATUSES`;
  `normalize_status` keywords gain `on-hold`/`on hold` (canonical
  mapping). `mutations.py` — `plan_story_status` accepts
  `reason: str`; a park (`on-hold`/`paused`) without a reason is
  refused; when a reason is given the table cell and story header
  are written as `<status> (<reason> — since <YYYY-MM-DD>)`.
  `parse.py` — `status_note(raw)` extracts the decoration tail so
  read surfaces can show the why. `api.py` — `story_context` gains
  `status_note` + normalized `status_token`. CLI `dw story status`
  gains `--reason`; MCP `dw_story_status` gains the `reason` param
  and the enum description names on-hold. Docs: roadmap-builder
  §2.3 vocabulary line; agent docs block ("statuses: … | on-hold |
  …"); the §2.3 parity test updated alongside.
- **Out:** phase-level pause (WLA-17-02); `next`/`holds` behavior
  (WLA-17-03); any gate/verify/contract change — on-hold is an
  open status, so the done-flip rules never see it.

## Acceptance criteria

- [ ] `dw story status <p> <ph> <s> on-hold --reason "pivot to X"`
  writes table cell + header as
  `on-hold (pivot to X — since <date>)`; `normalize_status` of that
  cell is `on-hold`; `status_note` recovers `pivot to X — since <date>`.
- [ ] `dw story status … on-hold` (no reason) is refused with a
  message naming `--reason`; `paused` behaves identically to
  `on-hold` at the gate of `validate_story_status`.
- [ ] `--reason` composes with every status (a blocked reason is
  recorded the same way); statuses without a reason write plain
  tokens exactly as today (byte-identical — existing fixtures pass
  unmodified).
- [ ] The §2.3 doc-parity test passes with the new vocabulary; MCP
  schema text and agent docs name on-hold.
- [ ] `/usr/bin/python3 pmo-roadmap/tests/dw-core-tests.py` green.

## Test plan

- **Unit:** new `dw-core-tests.py` cases: hold vocabulary accepted /
  bare park refused / reason decoration round-trip
  (write → parse → normalize → note) / plain writes byte-identical.
- **Integration:** `pmo-roadmap/tests/gate-parity.sh` untouched and
  green (no gate diff).
- **Manual / device:** n/a.

## Notes / open questions

- The decoration delimiter set is `normalize_status`'s: the reason
  opens with `(` so the head-only rule (WLA-16 hardening) keeps
  narrative tails from faking keywords.
- `since` is stamped from the local date at write time; it is
  display prose, never parsed back into logic.
