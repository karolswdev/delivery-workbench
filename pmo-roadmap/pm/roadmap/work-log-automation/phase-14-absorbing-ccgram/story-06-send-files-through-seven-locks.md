# WLA-14-06 - Send files through seven locks

- **Project:** work-log-automation
- **Phase:** 14
- **Status:** backlog
- **Depends on:** WLA-14-01.
- **Unblocks:** WLA-14-07.
- **Owner:** unassigned

## Problem

The read ring has no file leg: you can see the belt from your
phone but not the diff, the screenshot, or the evidence file an
agent just produced. ccgram ships `/send` with the most rigorous
guard pipeline in their codebase — seven independent layers
between a request and a byte leaving the box. That pipeline is
pure absorb: it protects without adding a single tap to the happy
path — a clean file just sends.

## Scope

- **In:** `/send <glob|path|substring>` from a bound repo,
  owner-only, direct on a clean resolution (a pick-list only when
  the match is ambiguous). The pipeline, absorbed and extended:
  (1) path containment inside the repo/workspace roots —
  traversal dies; (2) hidden-file block; (3) secret-pattern
  blocks (keys, pems, env files, credentials); (4) size cap;
  (5) `git check-ignore` — what the repo hides, the bot hides;
  (6) gitleaks-style content rules where cheap; (7) the
  workbench's own state: the operator config, runtime state,
  contract scratch, and events files are unsendable by name,
  ever. Refusals name the lock that fired.
- **Out:** inbound file handling (phone→desk uploads — a separate
  consent surface, a story someday); sending from unbound paths.

## Acceptance criteria

- [ ] Each lock has a test that fires it and asserts the named
  refusal; a traversal attempt, a `.env`, an ignored build
  artifact, and `telegram.json` itself all refuse.
- [ ] A legitimate evidence file and a screenshot under `assets/`
  send directly, one command, no ceremony, with caption metadata
  (repo, path, size).
- [ ] Ambiguous matches offer a pick-list; exact matches send
  straight through.
- [ ] CI's credential grep extends to the new surface.

## Test plan

- **Unit:** every lock in isolation.
- **Integration:** scripted transport + fixture repo with planted
  hazards (secrets, ignored files, oversized file).
- **Manual / device:** rides WLA-14-07.
