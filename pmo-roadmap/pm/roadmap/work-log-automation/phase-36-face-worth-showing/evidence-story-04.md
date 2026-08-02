# Evidence - WLA-36-04

- **Story:** WLA-36-04 - Panels and detail surfaces
- **Status:** done
- **Date:** 2026-08-02

## Proof

Implemented by Sol (GPT-5.6) under orchestration; renders reviewed by the operator in both themes before the flip.

What shipped: every non-board surface joined the system, restyled at the component level first (dw-panel gained the shared header grid — 500-weight title, quiet 13px meta, right-aligned ghost actions; dw-card/dw-fold/dw-toast/dialogs/skeletons unified on raised surfaces and the shared shadow stack; dw-status-pill and all badges converted to semantic soft-wash/ink with no outline pills; skeleton widths made deterministic) so run/program control rooms, live and orchestration views, session transcripts, the memory pane and decision timeline, outcomes, insights, guarded editor and ideation flows, terminal, services, diff review, Program Studio, and the health/story/trace pages inherit it. Key-value facts align on one two-column grid; tables use quiet hairlines with ops-label headers; terminal/transcripts/code/diffs stay mono inside designed code-frames with the operator diff washes; orchestration graphs recolored onto tokens; every empty/error/refusal state is one quiet line with the typed refusal under a fold. Authority labels are designed badges — MECHANICAL in accent wash, agent-reported in amber, panel-derived in green, operator-supplied in the attention wash — visually distinct as the contract demands; match reasons are quiet chips; the advisory boundary is an amber callout. Eight new panel-system checks pin the pattern.

The authoritative run is the capture below: full browser exam (352 renders; 468 core + 152 program assertions), explorer suite, accessibility contract (45 memory + 20 slick + 8 panel-system + 10 board-card checks), and language lint, exit 0. Core suite 727/727 rerun independently by the operator. An earlier identical capture was externally stopped mid-run and left no partial record; this capture is the complete authoritative rerun.

### Captured run — 2026-08-02T20:05:40Z

- **Command:** `/bin/sh -c bash pmo-roadmap/tests/workbench-ui-smoke.sh && bash pmo-roadmap/tests/workbench-explorer.sh && /usr/bin/python3 pmo-roadmap/tests/workbench-accessibility-contract.py && /usr/bin/python3 pmo-roadmap/tests/workbench-language-lint.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** dfceb9d0c450ccd8bfe45576d0633c823afce33e

```text
workbench-language-lint.py: ok (18 reserved terms; negative fixture refused: <negative-fixture>/app.js:1: forbidden term 'grant' in ordinary panel text: 'The grant is visible here.')
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 54209)
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
Exception occurred during processing of request from ('127.0.0.1', 54931)
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
workbench-accessibility.py: ok (13 journeys, 32 wide/narrow audits, 10 journey-6-13 keyboard/focus exams, 8 recorded memory steps / 24 recorded memory assertions, 467 assertions, suite=core)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.GCQLCJ/repo
dw-workbench: http://127.0.0.1:21045/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 57120)
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
Exception occurred during processing of request from ('127.0.0.1', 57284)
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
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.GCQLCJ/dw-program-test.fawa07vv/repo
dw-workbench: http://127.0.0.1:24292/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.cICalV/repo
dw-workbench: http://127.0.0.1:19687/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.cICalV/installed
dw-workbench: http://127.0.0.1:19688/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
workbench-explorer.sh: ok
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-workbench-test.cICalV/repo
dw-workbench: http://127.0.0.1:19687/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
workbench-accessibility-contract.py: ok (13 journeys, 2 viewports, 45 memory-pane checks, 20 slick-workbench checks, 8 panel-system checks, 10 board-card checks, keyboard/focus/semantics/manual evidence)
workbench-language-lint.py: ok (18 reserved terms; negative fixture refused: <negative-fixture>/app.js:1: forbidden term 'grant' in ordinary panel text: 'The grant is visible here.')
```
