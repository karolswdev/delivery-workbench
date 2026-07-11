# Evidence - WLA-20-01

- **Story:** WLA-20-01 - The pane becomes a picture — the screenshot engine
- **Status:** done
- **Date:** 2026-07-11

## Proof

Two captured runs, both green, plus a rendered artifact:

1. **20:19:23Z — the suites WITHOUT Pillow** (the contract's
   `--tests-capture` run, `/usr/bin/python3`, which has no PIL —
   the run itself proves it with a ModuleNotFoundError probe):
   interface suite 118 tests OK with exactly the 6 renderer legs
   skipped, fitness suite 8 OK with `screenshot` now pinned in
   LEAVES. This run IS the fallback path: `/screen` tests that
   force text mode, the usage refusal, and the read-only guarantee
   all executed here.
2. **20:19:43Z — the suite WITH Pillow** (proof venv, Pillow
   11.3.0): 118 OK, only the one pre-existing skip remains — the
   ANSI-matrix render (16/256/RGB/bold/reverse → valid PNG), the
   live-mode weight check, garbage-SGR tolerance, the photo flow
   (one photo, refresh button `ss:%7`, `-e` ANSI capture), and the
   refresh-edits-in-place leg (one media edit, zero new messages)
   all ran live. The run also verifies
   `assets/screen-demo.png` carries the PNG magic.
3. **`assets/screen-demo.png`** — rendered by this engine from an
   ANSI fixture: 16-color, 256-color, RGB, reverse video, and
   box-drawing all render true on the dark canvas with the bundled
   JetBrains Mono (OFL license file ships beside the font).

One upstream defect found and fixed during transmutation: ccgram's
non-SGR regex half-strips three-byte charset designators
(`ESC ( B` — common in tmux output), leaving a stray letter in the
render; our regex handles them whole, with a test pinning it.
CI's telegram job now installs Pillow as a TEST amenity (comment in
the workflow says so); the runtime keeps zero dependencies.

### Captured run — 2026-07-11T20:19:23Z

- **Command:** `bash -c /usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3
/usr/bin/python3 pmo-roadmap/tests/telegram-fitness-tests.py 2>&1 | tail -3
echo "--- interpreter has no Pillow (the fallback path is what just ran) ---"
/usr/bin/python3 -c "import PIL" 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 454e0f313c14b5be742ad5a58ebea1887a2ea888

```text
Ran 118 tests in 7.382s

OK (skipped=6)
Ran 8 tests in 0.126s

OK
--- interpreter has no Pillow (the fallback path is what just ran) ---
ModuleNotFoundError: No module named 'PIL'
```

### Captured run — 2026-07-11T20:19:43Z

- **Command:** `bash -c "/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/810a20d6-6a03-40b4-86b4-a69112bb7ad6/scratchpad/pilenv/bin/python" -c "import PIL; print('Pillow', PIL.__version__)"
"/private/tmp/claude-501/-Users-karol-dev-code-delivery-workbench/810a20d6-6a03-40b4-86b4-a69112bb7ad6/scratchpad/pilenv/bin/python" pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3
echo "--- demo asset rendered by this engine ---"
ls -la pmo-roadmap/pm/roadmap/work-log-automation/phase-20-group-grows-hands/assets/
/usr/bin/python3 -c "h=open('pmo-roadmap/pm/roadmap/work-log-automation/phase-20-group-grows-hands/assets/screen-demo.png','rb').read(8); print('PNG magic:', h == b'\x89PNG\r\n\x1a\n')"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 454e0f313c14b5be742ad5a58ebea1887a2ea888

```text
Pillow 11.3.0
Ran 118 tests in 7.442s

OK (skipped=1)
--- demo asset rendered by this engine ---
total 64
drwxr-xr-x   3 karol  staff     96 Jul 11 14:19 .
drwxr-xr-x  11 karol  staff    352 Jul 11 14:19 ..
-rw-r--r--   1 karol  staff  29922 Jul 11 14:19 screen-demo.png
PNG magic: True
```
