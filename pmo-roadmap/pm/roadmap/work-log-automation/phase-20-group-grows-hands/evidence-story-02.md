# Evidence - WLA-20-02

- **Story:** WLA-20-02 - The live view learns to show, not tell
- **Status:** done
- **Date:** 2026-07-11

## Proof

Two captured runs, both green:

1. **20:23:35Z — WITHOUT Pillow** (`/usr/bin/python3`, PIL absence
   proven in-run; the contract's `--tests-capture`): 122 interface
   tests OK, 10 skipped = 6 renderer legs + the 4 new
   ImageLiveViewTest legs. What RAN here is the point: the
   LiveViewTest class — the phase-14 text live view, assertions
   untouched, now with the probe forced off in setUp so it stays
   the no-Pillow pin forever — plus fitness 8 OK.
2. **20:23:53Z — WITH Pillow 11.3.0** (proof venv): 122 OK, one
   pre-existing skip. The image legs ran live: `/live` posts ONE
   photo (ANSI `-e` capture), an identical frame makes ZERO API
   calls (feed_stream length pinned before/after the tick), a
   changed frame makes exactly one `editMessageMedia` on the same
   message_id, `/live text` forces text mode despite the renderer,
   expiry and `/unlive` drop the view, and no tick ever emits a
   keystroke.

The hash gate sits on the captured text BEFORE the render, so an
unchanged pane costs neither a render nor an API call — absorption
row 11's "image later if wanted" is now closed with the same
economy the text view had.

### Captured run — 2026-07-11T20:23:35Z

- **Command:** `bash -c /usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3
/usr/bin/python3 pmo-roadmap/tests/telegram-fitness-tests.py 2>&1 | tail -3
echo "--- no Pillow here: the text pins and fallbacks just ran ---"
/usr/bin/python3 -c "import PIL" 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e83c5aeeab4c611fb36e5faa6f0abbea8dbf212e

```text
Ran 122 tests in 6.908s

OK (skipped=10)
Ran 8 tests in 0.125s

OK
--- no Pillow here: the text pins and fallbacks just ran ---
ModuleNotFoundError: No module named 'PIL'
```

### Captured run — 2026-07-11T20:23:53Z

- **Command:** `bash -c "/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/810a20d6-6a03-40b4-86b4-a69112bb7ad6/scratchpad/pilenv/bin/python" -c "import PIL; print('Pillow', PIL.__version__)"
"/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/810a20d6-6a03-40b4-86b4-a69112bb7ad6/scratchpad/pilenv/bin/python" pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e83c5aeeab4c611fb36e5faa6f0abbea8dbf212e

```text
Pillow 11.3.0
Ran 122 tests in 7.581s

OK (skipped=1)
```
