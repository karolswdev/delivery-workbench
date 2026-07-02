# WLA-3-02 - Polish operator and agent documentation

- **Project:** work-log-automation
- **Phase:** 3
- **Status:** done
- **Depends on:** WLA-3-01
- **Unblocks:** WLA-3-03
- **Owner:** unassigned

## Problem

The feature touches human intent, local filesystem paths, and model-assisted
summaries. Operators and agents need crisp instructions so consent remains
honest and logs remain useful.

## Scope

- **In:** README examples, CLAUDE/AGENTS snippet, troubleshooting, config table,
  and examples of consent yes/no/exclusions.
- **Out:** Marketing copy or external docs site.

## Acceptance criteria

- [x] README has an enablement recipe that starts from a fresh installed repo.
- [x] Agent snippet explains when to consent, deny, and list exclusions.
- [x] README has a read-flow recipe for today's log and a note on multi-day
  review.
- [x] Troubleshooting covers no log entry, stale pending payload, summarizer
  failure, and unexpected log path.
- [x] Examples match actual output from the pilot.

## Test plan

- **Unit:** n/a.
- **Integration / Cypress:** n/a.
- **Manual / device:** Follow docs in a temporary repo without reading source
  code and verify the feature can be enabled.

## Notes / open questions

The docs should stay operational. Avoid turning the work log into a performance
review narrative; it is technical memory.
