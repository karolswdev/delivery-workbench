# Evidence - WLA-36-03

- **Story:** WLA-36-03 - Board and cards
- **Status:** done
- **Date:** 2026-08-02

## Proof

Implemented by Sol (GPT-5.6) under orchestration; renders reviewed by the operator in both themes before the flip.

What shipped: the board rebuilt as the flagship surface. One card anatomy everywhere (flat and by-phase): semantic left rail in the story-01 signal colors (blue live, coral needs-you, amber blocked/on-hold, green done), quiet mono story ID, 500-weight title, one 13px phase-and-status metadata line, and at most ONE soft-wash attention badge — the badge zoo is gone and its absence is pinned by new assertions. The whole card is the click/keyboard target with quiet ghost actions on hover/focus. Dashed empty-column boxes replaced with one tertiary sentence over the quiet grid texture. Column headers standardized on the 11px mono overline with soft-wash count pills; the needs-you column trades its hard coral box for a soft coral wash with a glowing count pill. Primary actions (Create story, submit/apply) moved to accent blue — green is reserved for done. The project header band is clean (name 500, one metadata line, one soft-wash Ready pill, quiet next-action sentence) and the 'Ready. ready' duplication is fixed at its true source (board.js stripped only the attention prefix from /api/status and then prepended its own 'Ready.'). Board/Project-details tabs and Flat/By-phase now share one segmented-control design. Drag uses luminance lift + shadow-2; guarded create/move/park/refusal surfaces keep their semantics on the raised-surface treatment. Accessibility contract gained 10 board-card checks.

The authoritative run is the capture below: full browser exam (352 renders; 466 core + 152 program assertions), explorer suite, accessibility contract (13 journeys + 10 new board-card checks), and language lint, exit 0. Core suite 727/727 rerun independently by the operator in the same session.

### Captured run — 2026-08-02T19:03:08Z

- **Command:** `/bin/sh -c bash pmo-roadmap/tests/workbench-ui-smoke.sh && bash pmo-roadmap/tests/workbench-explorer.sh && /usr/bin/python3 pmo-roadmap/tests/workbench-accessibility-contract.py && /usr/bin/python3 pmo-roadmap/tests/workbench-language-lint.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 84baaa4b3b946014252c4e21b05f3d34dc538d90

```text
workbench-language-lint.py: ok (18 reserved terms; negative fixture refused: <negative-fixture>/app.js:1: forbidden term 'grant' in ordinary panel text: 'The grant is visible here.')
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 54943)
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 697, in process_request_thread
    self.finish_request(request, client_address)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 362, in finish_request
    self.RequestHandlerClass(request, client_address, self)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 766, in __init__
    self.handle()
    ~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 496, in handle
    self.handle_one_request()
    ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 484, in handle_one_request
    method()
    ~~~~~~^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2429, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2412, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
workbench-accessibility.py: ok (13 journeys, 32 wide/narrow audits, 10 journey-6-13 keyboard/focus exams, 8 recorded memory steps / 24 recorded memory assertions, 466 assertions, suite=core)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.4enAXy/repo
dw-workbench: http://127.0.0.1:22457/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 57291)
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 697, in process_request_thread
    self.finish_request(request, client_address)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 362, in finish_request
    self.RequestHandlerClass(request, client_address, self)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 766, in __init__
    self.handle()
    ~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 496, in handle
    self.handle_one_request()
    ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 484, in handle_one_request
    method()
    ~~~~~~^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2429, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2412, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 57297)
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 697, in process_request_thread
    self.finish_request(request, client_address)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 362, in finish_request
    self.RequestHandlerClass(request, client_address, self)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 766, in __init__
    self.handle()
    ~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 496, in handle
    self.handle_one_request()
    ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/http/server.py", line 484, in handle_one_request
    method()
    ~~~~~~^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2429, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2412, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
workbench-accessibility.py: ok (3 journeys, 6 wide/narrow audits, 6 journey-6-13 keyboard/focus exams, 0 recorded memory steps / 0 recorded memory assertions, 152 assertions, suite=program)
workbench-ui-smoke.sh: ok (firefox-version='Mozilla Firefox 152.0.5'; 352 viewport renders; desktop-light=88 desktop-dark=88 mobile-light=88 mobile-dark=88; board home, ideation, bounded-run consent, program consent, and eight-state Live matrix; 16 journey 6-13 wide/narrow keyboard/focus exams)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.4enAXy/dw-program-test.h2e0redz/repo
dw-workbench: http://127.0.0.1:24748/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.XUL54s/repo
dw-workbench: http://127.0.0.1:19896/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.XUL54s/installed
dw-workbench: http://127.0.0.1:19897/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.XUL54s/repo
dw-workbench: http://127.0.0.1:19896/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
workbench-accessibility-contract.py: ok (13 journeys, 2 viewports, 45 memory-pane checks, 20 slick-workbench checks, 10 board-card checks, keyboard/focus/semantics/manual evidence)
workbench-language-lint.py: ok (18 reserved terms; negative fixture refused: <negative-fixture>/app.js:1: forbidden term 'grant' in ordinary panel text: 'The grant is visible here.')
```
