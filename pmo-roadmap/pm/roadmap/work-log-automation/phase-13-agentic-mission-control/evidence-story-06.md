# Evidence - WLA-13-06

- **Story:** WLA-13-06 - Prove mission control from Telegram
- **Status:** done
- **Date:** 2026-07-04

## Proof

### Captured run — 2026-07-04T15:37:02Z

- **Command:** `bash -c python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 && /usr/bin/python3 pmo-roadmap/tests/telegram-interface-tests.py 2>&1 | tail -3 && python3 pmo-roadmap/tests/dw-core-tests.py 2>&1 | tail -3 && { grep -rnE "[0-9]{6,}:[A-Za-z0-9_-]{30,}" integrations/telegram pmo-roadmap/tests/telegram-interface-tests.py && exit 1 || echo "credential grep-clean: ok"; }`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 338cef5648d9a2d0c2fecf8dc6a9048b4f29ed5e

```text
Ran 37 tests in 3.682s

OK
Ran 37 tests in 3.439s

OK
Ran 153 tests in 11.151s

OK
credential grep-clean: ok
```

### What the captured run proves

- **37 interface tests, twice** — on the dev Python and on
  `/usr/bin/python3` 3.9.6, the declared floor. Scripted Telegram
  transport and faked tmux; the rails legs are real: `/state`,
  `/events`, and `/sessions` run the real `dw` CLI against a
  fixture rails repo and a fixture registry (via the new
  `dw sessions --registry` seam, amended into the contract §2).
- **The crown case** (`CrownCaseTest`): an approved dishonest
  done-flip is refused by the rails and the banner — `refusing to
  mark story done without evidence` — is relayed into chat
  verbatim. The honest flip through the same seam executes.
- **Pairing** (`PairingTest`): wrong, expired, and reused tokens
  refused; re-pairing revokes the prior binding; unpaired chats get
  silence beyond the pairing prompt; runtime state lands chmod 600
  with the token hashed at rest.
- **Arming** (`QARelayTest`, `DriverTest`): an approved reply into
  an unarmed session produces zero tmux calls (the refusal lives in
  the driver); arming expires; the driver targets the registry's
  pane (`%7`) literally; all three harnesses (claude, codex, pi)
  launch detached and start unarmed.
- **Lifecycle** (`LifecycleTest`): create outside the allow-listed
  roots refused before any proposal exists; and
  `test_create_for_real_lands_on_the_rails` runs the full leg with
  no fakes — git init → install.sh → roadmap skeleton → doctor →
  first gated commit with live hooks (the bootstrap-certification
  decision, recorded in contract §4).
- **153 core tests** — the `--registry` CLI addition broke nothing.
- **Credential grep** — no bot-token-shaped string in the new code;
  the same check now gates CI (`telegram-interface` job in
  validation.yml) together with a tracked-`telegram.json` refusal.

### Owed (manual, not CI-provable)

- The live phone leg: `/pair` from the real device, a relayed
  question and answer against a live agent session, an approved
  flip, a gate refusal in chat, a `capture-pane` preview —
  screenshots to land under `assets/` here. Requires
  `python3 integrations/telegram/run.py serve` on the desk.
