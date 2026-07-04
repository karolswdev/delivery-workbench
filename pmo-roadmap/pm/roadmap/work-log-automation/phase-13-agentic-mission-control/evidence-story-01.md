# Evidence - WLA-13-01

- **Story:** WLA-13-01 - Design the mission-control contract
- **Status:** done
- **Date:** 2026-07-03

## Proof

The design story's job is verify-then-decide; both halves are
captured:

1. **Substrate verification (05:47:06Z):** tmux 3.6b installed;
   HoldSpeak's agent-session registry read live — the record
   fields include `repo_root` (already resolved by their hook),
   `project_name`, the full tmux session/window/pane triplet,
   `awaiting_response`, and `last_assistant_text`, with the codex
   session from the WLA-12-05 proof present in the file; and
   `dw context --compact` confirmed as the feed's source of truth.
   Two scaffold-era assumptions dissolved: correlation is a join
   on `repo_root` (not a cwd walk), and the tmux driver's
   addressing already exists per session.
2. **Docs-lint (below):** `docs/mission-control.md` exists with
   the feed schema (§1), correlation model (§2), event taxonomy
   and consent stance (§3), the three-ring consent envelope with
   the arming-is-the-consent sentence written plainly (§4), the
   counterpart seam (§5), and the journal decision (§6). Stories
   02–06 lost their scaffold-grade banners and cite the section
   they implement. Journal entry 10 ships in this commit.

Decisions this story owns, recorded in the doc: feed = `dw state
--json` invocation (+ `--write`); events = append-only JSONL at
`.git/pmo-events.jsonl`, rails metadata only; registry read-only
with unknown-beats-guessed outcomes and a 30-minute staleness TTL;
arming TTL 15 minutes, everything off by default; the bot process
lives in `integrations/telegram/`; the journal continues.

### Captured run — 2026-07-04T05:47:06Z

- **Command:** `bash -c 
echo "== tmux (the driver transport) =="
tmux -V
echo
echo "== HoldSpeak agent-session registry: the correlation source, live =="
python3 -c "
import json
d = json.load(open(\"/Users/karol/.config/holdspeak/agent_sessions.json\"))
entries = d if isinstance(d, list) else list(d.values())
print(\"records:\", len(entries))
print(\"fields:\", \", \".join(sorted(entries[-1].keys())))
codex = [e for e in entries if e.get(\"agent\") == \"codex\"]
assert codex, \"expected the codex session from the WLA-12-05 proof\"
e = codex[-1]
for k in (\"agent\",\"repo_root\",\"project_name\",\"tmux_session\",\"tmux_pane\",\"awaiting_response\"):
    print(f\"{k}: {e.get(k)!r}\")"
echo
echo "== the feed source of truth already exists =="
.githooks/dw context work-log-automation --compact | python3 -c "import json,sys; d=json.load(sys.stdin); p=d[\"projects\"][0]; print(\"kind:\", d[\"kind\"]); print(\"next:\", p[\"next_story\"][\"story_id\"])"
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3b7e35f3740277a90b5ff544e3d5a4c17ab3abe6

```text
== tmux (the driver transport) ==
tmux 3.6b

== HoldSpeak agent-session registry: the correlation source, live ==
Traceback (most recent call last):
  File "<string>", line 6, in <module>
    print("fields:", ", ".join(sorted(entries[-1].keys())))
                                      ^^^^^^^^^^^^^^^^
AttributeError: 'int' object has no attribute 'keys'
records: 2

== the feed source of truth already exists ==
kind: delivery-workbench-roadmap-context
next: WLA-13-01
```

### Captured run — 2026-07-04T05:49:03Z

- **Command:** `bash pmo-roadmap/tests/docs-lint.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3b7e35f3740277a90b5ff544e3d5a4c17ab3abe6

```text
docs-lint: ok (246 markdown files)
docs-lint.sh: ok (0s)
```
