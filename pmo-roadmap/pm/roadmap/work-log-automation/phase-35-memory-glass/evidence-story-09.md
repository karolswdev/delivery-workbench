# Evidence - WLA-35-09

- **Story:** WLA-35-09 - Slick workbench
- **Status:** done
- **Date:** 2026-08-01

## Proof

Implemented by Sol (GPT-5.6) under orchestration; reviewed and verified by the operator session.

What shipped: the whole-workbench polish pass, judged from the actual code. Skeleton-first routing (stable shell + `dw-skeleton` immediately, panels fill asynchronously; synchronous XHR restricted to the deterministic snapshot mode); shared motion tokens for panel/route/disclosure transitions with `prefers-reduced-motion: reduce` disabling every nonessential animation; a keyboard-accessible Comfortable/Compact density toggle persisted under `delivery-workbench.density` preserving tab order and target sizes; explicit global-SSE reconnect announcements (disconnected / retrying / caught-up / restored) and 503 subscriber-cap retry guidance instead of silent staleness; bounded layouts with copy actions and announcements for long hashes, run IDs, and receipt IDs; `aria-describedby`/`aria-invalid` on editor and project-selection errors; no horizontal body scrolling. The pass also fixed real board accessibility defects it uncovered (duplicate action IDs between flat and phase views, flat-card actions hidden from keyboard order, focus restoration into light-DOM custom buttons, story-specific return-focus selectors, focus rings after live redraws) and removed a timer-based snapshot repositioning that produced blank narrow screenshots — no unconditional sleeps added. Eleven front-end files changed, `.githooks/workbench/` byte-synced.

The authoritative run is the first capture below: workbench-ui-smoke.sh — Firefox 152.0.5, 352 viewport renders (up from 304; 88 per theme/viewport bucket including the new dark-mode memory-pane, decision-timeline, needs-you, density, and reconnect journeys), core 13 journeys / 32 audits / 398 assertions plus program 3 journeys / 133 assertions, exit 0. The second capture: the accessibility contract (13 journeys, 45 memory-pane checks, 20 new slick-workbench checks) and the product-language lint, both green.

### Captured run — 2026-08-01T23:40:52Z

- **Command:** `/bin/sh -c bash pmo-roadmap/tests/workbench-ui-smoke.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 91a2e6eade2b93e2b3f118057a73da23eeb4ddb9

```text
workbench-language-lint.py: ok (18 reserved terms; negative fixture refused: <negative-fixture>/app.js:1: forbidden term 'grant' in ordinary panel text: 'The grant is visible here.')
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 62970)
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
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2428, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2411, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
workbench-accessibility.py: ok (13 journeys, 32 wide/narrow audits, 10 journey-6-13 keyboard/focus exams, 398 assertions, suite=core)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.4EwSNt/repo
dw-workbench: http://127.0.0.1:21226/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 49663)
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
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2428, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2411, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 49766)
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
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2428, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2411, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 49924)
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
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2428, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2411, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 49928)
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
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2428, in do_GET
    self._send_json(status, payload)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/code/delivery-workbench/pmo-roadmap/lib/dw_pmo/workbench.py", line 2411, in _send_json
    self.wfile.write(body)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/socketserver.py", line 845, in write
    self._sock.sendall(b)
    ~~~~~~~~~~~~~~~~~~^^^
BrokenPipeError: [Errno 32] Broken pipe
----------------------------------------
workbench-accessibility.py: ok (3 journeys, 6 wide/narrow audits, 6 journey-6-13 keyboard/focus exams, 133 assertions, suite=program)
workbench-ui-smoke.sh: ok (firefox-version='Mozilla Firefox 152.0.5'; 352 viewport renders; desktop-light=88 desktop-dark=88 mobile-light=88 mobile-dark=88; board home, ideation, bounded-run consent, program consent, and eight-state Live matrix; 16 journey 6-13 wide/narrow keyboard/focus exams)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.4EwSNt/dw-program-test.cswkgbbp/repo
dw-workbench: http://127.0.0.1:23356/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
```

### Captured run — 2026-08-01T23:53:25Z

- **Command:** `/bin/sh -c /usr/bin/python3 pmo-roadmap/tests/workbench-accessibility-contract.py && /usr/bin/python3 pmo-roadmap/tests/workbench-language-lint.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 91a2e6eade2b93e2b3f118057a73da23eeb4ddb9

```text
workbench-accessibility-contract.py: ok (13 journeys, 2 viewports, 45 memory-pane checks, 20 slick-workbench checks, keyboard/focus/semantics/manual evidence)
workbench-language-lint.py: ok (18 reserved terms; negative fixture refused: <negative-fixture>/app.js:1: forbidden term 'grant' in ordinary panel text: 'The grant is visible here.')
```
