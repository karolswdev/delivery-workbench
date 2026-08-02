# Evidence - WLA-36-01

- **Story:** WLA-36-01 - Design tokens and type
- **Status:** done
- **Date:** 2026-08-02

## Proof

Implemented by Sol (GPT-5.6) under orchestration; renders reviewed by the operator in both themes before the flip.

What shipped: the design foundation, adopted from the owner-designated references. Course-corrected mid-story on the owner's directive: operator-oss's own mission-control skin (its `app/globals.css`) is the visual source of truth — cool near-black surfaces (#080a0e / #0a0d12 / #0c1119 / #0e141d), blue-tinted hairline tiers, electric-blue #4d8cff accent with soft/ink/glow companions, semantic signals (coral needs-you, amber blocked, green done, blue live) each with fill/soft/ink/glow roles, Operator's radius (2/4/7/10/14/18/9999) and shadow stacks, a translucent blurred topbar token, and the warm-paper light theme (#f4f1ea canvas, #fffdf8 panels, AA-adjusted inks) — while the Linear reference supplies the discipline: a real type scale, 400/500/700 weight system, 8px spacing grid, mono confined to code/hashes/IDs/transcripts/terminal plus a sanctioned 11px `.ops-label` mono overline. 126 role-named tokens; zero downstream color literals. Dark is now the native default with light as the complete prefers-color-scheme override; the two pinned color-scheme core tests flipped deliberately per the phase decision. Space Grotesk and JetBrains Mono are vendored (SIL OFL 1.1, notice in workbench/fonts/, 54 KB total), served locally by dw-workbench with correct MIME — no runtime font fetching; install/update payload copying and the package smoke now carry and assert the fonts. WCAG AA verified on all representative pairings in both themes (worst pairing 4.78:1 at its usage size). Mirrors byte-identical including the fonts dir.

The authoritative run is the capture below: the full browser exam (352 renders, 88 per theme/viewport bucket), the accessibility contract, and the language lint, exit 0. The full core suite (727/727, including the flipped theme pins) and the packaged wheel/sdist smoke (fonts + OFL notice asserted in the installed payload) ran green in the same session; fresh render pairs for board-home, memory-rich, and needs-you in both themes were reviewed by the operator.

### Captured run — 2026-08-02T16:54:49Z

- **Command:** `/bin/sh -c bash pmo-roadmap/tests/workbench-ui-smoke.sh && /usr/bin/python3 pmo-roadmap/tests/workbench-accessibility-contract.py && /usr/bin/python3 pmo-roadmap/tests/workbench-language-lint.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 056d13babe5a2c08092e0a015561ebad206e21af

```text
workbench-language-lint.py: ok (18 reserved terms; negative fixture refused: <negative-fixture>/app.js:1: forbidden term 'grant' in ordinary panel text: 'The grant is visible here.')
workbench-accessibility.py: ok (13 journeys, 32 wide/narrow audits, 10 journey-6-13 keyboard/focus exams, 8 recorded memory steps / 24 recorded memory assertions, 454 assertions, suite=core)
dw-workbench: shutting down
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.PD6Imk/repo
dw-workbench: http://127.0.0.1:22543/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
----------------------------------------
Exception occurred during processing of request from ('127.0.0.1', 49786)
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
Exception occurred during processing of request from ('127.0.0.1', 49788)
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
Exception occurred during processing of request from ('127.0.0.1', 49789)
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
dw-workbench: serving /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pmo-ui-smoke.PD6Imk/dw-program-test.sft59si8/repo
dw-workbench: http://127.0.0.1:24902/ (localhost or your own .ts.net tailnet; Ctrl-C to stop)
dw-workbench: writes require guarded preview→apply or an exact single-use token; only a browser-confirmed program action may use pre-granted delivery permission, and the browser adds no authority of its own
workbench-accessibility-contract.py: ok (13 journeys, 2 viewports, 45 memory-pane checks, 20 slick-workbench checks, keyboard/focus/semantics/manual evidence)
workbench-language-lint.py: ok (18 reserved terms; negative fixture refused: <negative-fixture>/app.js:1: forbidden term 'grant' in ordinary panel text: 'The grant is visible here.')
```
