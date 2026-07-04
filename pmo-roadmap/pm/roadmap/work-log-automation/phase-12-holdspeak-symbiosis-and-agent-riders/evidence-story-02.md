# Evidence - WLA-12-02

- **Story:** WLA-12-02 - Build the HoldSpeak roadmap-alignment synthesizer
- **Status:** done
- **Date:** 2026-07-03

## Proof

The pack (`integrations/holdspeak/delivery_workbench_pack.py`) went
through four captured proofs, in order:

1. **The crown run (03:56:56Z):** real HoldSpeak discovery from a
   pack directory, real `PluginHost` with the `llm` capability, and
   the desk's **real configured LLM** — no canned responses. Against
   the webshop transcript fixture and a rails fixture repo it
   grounded both story IDs correctly (`WSH-1-01` decision,
   `WSH-1-02` action item), demoted dark mode to drift, took the
   next-actionable story from `dw context` (not the model), and the
   synthesized artifact body carries all of it.
2. **The suite (03:57:44Z):** all 10 tests — grounding,
   hallucinated-ID demotion, unparseable-response / no-roadmap /
   broken-dw / empty-transcript failure shapes, discovery,
   blocked-without-llm, deferred queue-and-drain, synthesis.
   Also proven to pass with zero holdspeak runtime deps installed,
   which is what makes the `--no-deps` CI install honest.
3. **Two failed captures (03:57:59Z, 03:58:15Z), kept in per the
   charter:** the desk install succeeded but my discovery
   verification used a wrong signature, then wrong unpacking —
   `discover_user_packs(directory)` returns a plain
   `(packs, errors)` tuple.
4. **Desk discovery (03:58:33Z):** the pack installed to
   `~/.holdspeak/plugin_packs/` with the project map at
   `~/.holdspeak/delivery_workbench.json` is discovered by the real
   desk loader, no errors.

Reality deltas vs the story text, recorded here and in
`docs/riders.md`: packs cannot register renderers or artifact
types on holdspeak 0.3.1 (private registries, no public API), so
the "typed `roadmap_alignment` artifact" is realized as the typed
`roadmap_alignment` payload in the plugin-run output plus a
default-rendered `plugin_output` artifact whose body is our rich
markdown summary (whitespace-collapsed by the 0.3.1 composer).
holdspeak is not on PyPI — CI installs the pinned `v0.3.1` git tag
with `--no-deps`. The live-desk meeting screenshot (test plan's
manual item) lands with the next real delivery meeting now that
the pack is installed on the desk; recorded as pending, not done.

### Captured run — 2026-07-04T03:56:56Z

- **Command:** `/Users/karol/dev/tools/HoldSpeak/.venv/bin/python /private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/fdc6877b-9071-406e-94f9-c2020d111439/scratchpad/pack-real-llm-proof.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e08ab7e5fd17738f95c437c7261e173884dadd25

```text
discovery: registered=['delivery_workbench'] errors=[]
host result: status=success duration_ms=3881
grounded story IDs (real LLM): ['WSH-1-01', 'WSH-1-02']
drift items: ['Dark mode for the storefront']

artifact: type=plugin_output status=draft confidence=1.0
---- rendered body_markdown ----
### Delivery Workbench

The team agreed to complete the cart API before starting payment work, with the developer to pick up the payment provider integration once the cart merges, and noted that dark mode remains an unplanned request without a story. **Grounded in the roadmap:** - `WSH-1-01` Build the cart API [in-progress] ← decision: Finish the cart API before starting any payment work - `WSH-1-02` Add payment provider [backlog] ← action item: Dev to pick up the payment provider integration once the cart merges **Drift (no story covers this):** - Dark mode for the storefront — Requested by support but explicitly stated there is no ticket or story for it yet. **Next actionable story:** `WSH-1-01` Build the cart API [in-progress]

- Source windows: w-1
- Source plugin runs: run-proof
---- end ----
PASS: real host, real LLM, grounded artifact
```

### Captured run — 2026-07-04T03:57:44Z

- **Command:** `/Users/karol/dev/tools/HoldSpeak/.venv/bin/python pmo-roadmap/tests/holdspeak-pack-tests.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e08ab7e5fd17738f95c437c7261e173884dadd25

```text
test_blocked_without_llm_capability (__main__.PackHostIntegrationTest.test_blocked_without_llm_capability) ... ok
test_deferred_queue_then_drain_produces_alignment (__main__.PackHostIntegrationTest.test_deferred_queue_then_drain_produces_alignment) ... ok
test_discovery_registers_the_pack (__main__.PackHostIntegrationTest.test_discovery_registers_the_pack) ... ok
test_synthesized_artifact_carries_the_summary (__main__.PackHostIntegrationTest.test_synthesized_artifact_carries_the_summary) ... ok
test_broken_dw_is_failure_shape (__main__.PackUnitTest.test_broken_dw_is_failure_shape) ... ok
test_empty_transcript_is_failure_shape (__main__.PackUnitTest.test_empty_transcript_is_failure_shape) ... ok
test_hallucinated_story_id_is_demoted_to_drift (__main__.PackUnitTest.test_hallucinated_story_id_is_demoted_to_drift) ... ok
test_no_roadmap_resolvable_fails_before_llm (__main__.PackUnitTest.test_no_roadmap_resolvable_fails_before_llm) ... ok
test_success_grounds_real_story_ids (__main__.PackUnitTest.test_success_grounds_real_story_ids) ... ok
test_unparseable_response_is_failure_shape (__main__.PackUnitTest.test_unparseable_response_is_failure_shape) ... ok

----------------------------------------------------------------------
Ran 10 tests in 3.402s

OK
```

### Captured run — 2026-07-04T03:57:59Z

- **Command:** `bash -c mkdir -p ~/.holdspeak/plugin_packs && cp integrations/holdspeak/delivery_workbench_pack.py ~/.holdspeak/plugin_packs/ && printf "%s\n" "{\"projects\": {\"delivery-workbench\": \"/Users/karol/dev/code/delivery-workbench\"}, \"default\": \"/Users/karol/dev/code/delivery-workbench\"}" > ~/.holdspeak/delivery_workbench.json && echo "installed:" && ls -la ~/.holdspeak/plugin_packs/ && cat ~/.holdspeak/delivery_workbench.json && /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -c "
from pathlib import Path
from holdspeak.plugin_pack_loader import discover_user_packs
result = discover_user_packs()
print(\"desk discovery:\", [p.manifest.id for p in result.packs], \"errors:\", result.errors)"`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** e08ab7e5fd17738f95c437c7261e173884dadd25

```text
installed:
total 40
drwxr-xr-x  3 karol  staff     96 Jul  3 21:57 .
drwxr-xr-x  4 karol  staff    128 Jul  3 21:57 ..
-rw-r--r--  1 karol  staff  16595 Jul  3 21:57 delivery_workbench_pack.py
{"projects": {"delivery-workbench": "/Users/karol/dev/code/delivery-workbench"}, "default": "/Users/karol/dev/code/delivery-workbench"}
Traceback (most recent call last):
  File "<string>", line 4, in <module>
    result = discover_user_packs()
TypeError: discover_user_packs() missing 1 required positional argument: 'directory'
```

### Captured run — 2026-07-04T03:58:15Z

- **Command:** `/Users/karol/dev/tools/HoldSpeak/.venv/bin/python -c 
from holdspeak.plugin_pack_loader import DEFAULT_USER_PACK_DIR, discover_user_packs
result = discover_user_packs(DEFAULT_USER_PACK_DIR)
packs = [(p.manifest.id, p.manifest.version) for p in result.packs]
print('desk discovery from', DEFAULT_USER_PACK_DIR)
print('packs:', packs, 'errors:', result.errors)
assert packs == [('delivery_workbench', '0.1.0')] and not result.errors
print('PASS: the desk discovers the installed pack')`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** e08ab7e5fd17738f95c437c7261e173884dadd25

```text
Traceback (most recent call last):
  File "<string>", line 4, in <module>
    packs = [(p.manifest.id, p.manifest.version) for p in result.packs]
                                                          ^^^^^^^^^^^^
AttributeError: 'tuple' object has no attribute 'packs'
```

### Captured run — 2026-07-04T03:58:33Z

- **Command:** `/Users/karol/dev/tools/HoldSpeak/.venv/bin/python -c 
from holdspeak.plugin_pack_loader import DEFAULT_USER_PACK_DIR, discover_user_packs
packs, errors = discover_user_packs(DEFAULT_USER_PACK_DIR)
found = [(p.manifest.id, p.manifest.version) for p in packs]
print('desk discovery from', DEFAULT_USER_PACK_DIR)
print('packs:', found, 'errors:', list(errors))
assert found == [('delivery_workbench', '0.1.0')] and not errors
print('PASS: the desk discovers the installed pack')`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e08ab7e5fd17738f95c437c7261e173884dadd25

```text
desk discovery from /Users/karol/.holdspeak/plugin_packs
packs: [('delivery_workbench', '0.1.0')] errors: []
PASS: the desk discovers the installed pack
```
