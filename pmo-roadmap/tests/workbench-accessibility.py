#!/usr/bin/env python3
"""Firefox keyboard, semantic, focus, and viewport exam for Phase 27.

This intentionally uses Firefox's built-in Marionette endpoint and only the
Python standard library. The UI smoke harness already owns realistic fixture
servers; this exam drives those same pages as a keyboard user and audits their
rendered DOM at both required viewport sizes.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote


WIDE = (1440, 900)
NARROW = (390, 844)
KEYS = {
    "tab": "\ue004",
    "enter": "\ue007",
    "shift": "\ue008",
    "escape": "\ue00c",
    "space": "\ue00d",
    "end": "\ue010",
    "home": "\ue011",
    "left": "\ue012",
    "up": "\ue013",
    "right": "\ue014",
    "down": "\ue015",
}

JOURNEY_CASES = {
    "healthy-first-arrival": {
        "suite": "core",
        "route": "/#/",
        "selector": ".board-overview h1",
    },
    "deliberate-capability-choice": {
        "suite": "core",
        "route": "/#/program-studio",
        "selector": ".delivery-choice-grid",
    },
    "delivery-plan-setup": {
        "suite": "core",
        "route": "/#/program-studio/workflow/architect-debate-delivery",
        "selector": ".program-studio h1",
    },
    "team-review-setup": {
        "suite": "core",
        "route": "/#/program-studio/organization/autonomous-story-cell",
        "selector": ".program-studio h1",
    },
    "preflight": {
        "suite": "core",
        "route": "/?orchview=validate#/orchestration/research-build-review",
        "selector": ".delivery-preflight",
    },
    "bounded-run-permission": {
        "suite": "core",
        "route": "/?snapshot=1&orchview=run&consentpreview=run-narrowed#/orchestration/consent-visual",
        "selector": ".run-consent .consent-summary",
    },
    "program-permission": {
        "suite": "core",
        "route": "/?snapshot=1&consentpreview=program-narrowed#/programs",
        "selector": ".program-consent .consent-summary",
    },
    "live-progress": {
        "suite": "core",
        "route": "/?orchview=run#/orchestration/research-build-review",
        "selector": ".orch-run-shell",
    },
    "live-mission-control": {
        "suite": "core",
        "route": "/?snapshot=1&project=sample&livescenario=active#/live",
        "selector": ".live-mission",
    },
    "failed-review-and-repair": {
        "suite": "core",
        "route": "/?orchview=run#/orchestration/repair-visual",
        "selector": ".orch-run-shell",
    },
    "blocked-human-decision": {
        "suite": "core",
        "route": "/?orchview=run#/orchestration/decision-visual",
        "selector": ".orch-run-shell",
    },
    "remaining-permission-and-cost": {
        "suite": "program",
        "route": "/?boundedfocus=limits#/programs/{program_active}",
        "selector": ".program-room",
    },
    "stop-and-revoke": {
        "suite": "program",
        "route": "/#/programs/{program_active}",
        "selector": ".program-room",
    },
    "crash-recovery": {
        "suite": "core",
        "route": "/?orchview=run&liveconnection=stale#/orchestration/research-build-review",
        "selector": ".live-recovery",
    },
    "completion": {
        "suite": "program",
        "route": "/#/programs/{program_certified}",
        "selector": ".program-room",
    },
    "technical-inspection": {
        "suite": "core",
        "route": "/?orchview=run&livetechnical=1#/orchestration/research-build-review",
        "selector": ".live-technical",
    },
}

# Journey catalog rows 6-13. Each ordinary route exposes the canonical next
# step, saved recovery truth, and the same Technical details fold. Action
# selectors identify confirmation dialogs that can be opened and dismissed
# without applying anything; empty selectors mean the journey is read-only.
PHASE32_JOURNEYS = {
    "live-progress": {"refresh": "#run-refresh", "action": "[data-run-act]"},
    "failed-review-and-repair": {
        "refresh": "#run-refresh", "action": "[data-run-act]"
    },
    "blocked-human-decision": {
        "refresh": "#run-refresh", "action": "[data-run-act]"
    },
    "remaining-permission-and-cost": {
        "refresh": "#program-refresh", "action": "[data-program-act]"
    },
    "stop-and-revoke": {
        "refresh": "#program-refresh", "action": "[data-program-act]"
    },
    "crash-recovery": {"refresh": "#run-refresh", "action": ""},
    "completion": {"refresh": "#program-refresh", "action": ""},
    "technical-inspection": {"refresh": "#run-refresh", "action": ""},
}


class ExamFailure(RuntimeError):
    """A user-observable accessibility contract failed."""


class Marionette:
    def __init__(self, firefox: Path) -> None:
        self.firefox = firefox
        self.profile: tempfile.TemporaryDirectory[str] | None = None
        self.process: subprocess.Popen[bytes] | None = None
        self.sock: socket.socket | None = None
        self.command_id = 0

    @staticmethod
    def free_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            return int(probe.getsockname()[1])

    def start(self) -> None:
        port = self.free_port()
        self.profile = tempfile.TemporaryDirectory(
            prefix="delivery-workbench-marionette-"
        )
        profile = Path(self.profile.name)
        (profile / "user.js").write_text(
            "\n".join(
                (
                    f'user_pref("marionette.port", {port});',
                    'user_pref("marionette.log.level", "Warn");',
                    'user_pref("browser.shell.checkDefaultBrowser", false);',
                    'user_pref("browser.startup.homepage_override.mstone", "ignore");',
                    'user_pref("datareporting.policy.dataSubmissionEnabled", false);',
                    'user_pref("accessibility.tabfocus", 7);',
                )
            )
            + "\n",
            encoding="utf-8",
        )
        env = dict(os.environ)
        env["MOZ_HEADLESS"] = "1"
        self.process = subprocess.Popen(
            [
                str(self.firefox),
                "--headless",
                "--no-remote",
                "-remote-allow-system-access",
                "--profile",
                str(profile),
                "--marionette",
                "--width",
                str(NARROW[0]),
                "--height",
                str(NARROW[1]),
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise ExamFailure(
                    f"Firefox exited before Marionette connected "
                    f"(status {self.process.returncode})"
                )
            try:
                self.sock = socket.create_connection(
                    ("127.0.0.1", port), timeout=1
                )
                self.sock.settimeout(30)
                break
            except OSError:
                time.sleep(0.1)
        if self.sock is None:
            raise ExamFailure("Firefox Marionette endpoint did not become ready")
        handshake = self.receive()
        if not isinstance(handshake, dict) or handshake.get(
            "marionetteProtocol"
        ) not in {3, 4}:
            raise ExamFailure(f"unexpected Marionette handshake: {handshake!r}")
        self.command(
            "WebDriver:NewSession",
            {"capabilities": {"alwaysMatch": {}}},
        )

    def send(self, value: Any) -> None:
        if self.sock is None:
            raise ExamFailure("Marionette socket is not connected")
        payload = json.dumps(value, separators=(",", ":")).encode("utf-8")
        self.sock.sendall(str(len(payload)).encode("ascii") + b":" + payload)

    def receive(self) -> Any:
        if self.sock is None:
            raise ExamFailure("Marionette socket is not connected")
        length = bytearray()
        while True:
            byte = self.sock.recv(1)
            if not byte:
                raise ExamFailure("Marionette connection closed")
            if byte == b":":
                break
            length.extend(byte)
        remaining = int(length.decode("ascii"))
        payload = bytearray()
        while len(payload) < remaining:
            chunk = self.sock.recv(remaining - len(payload))
            if not chunk:
                raise ExamFailure("Marionette response ended early")
            payload.extend(chunk)
        return json.loads(payload.decode("utf-8"))

    def command(self, name: str, params: dict[str, Any] | None = None) -> Any:
        self.command_id += 1
        command_id = self.command_id
        self.send([0, command_id, name, params or {}])
        while True:
            response = self.receive()
            if (
                isinstance(response, list)
                and len(response) == 4
                and response[0] == 1
                and response[1] == command_id
            ):
                error = response[2]
                if error:
                    raise ExamFailure(
                        f"{name} failed: {json.dumps(error, sort_keys=True)}"
                    )
                return response[3]

    def execute(self, script: str, args: list[Any] | None = None) -> Any:
        result = self.command(
            "WebDriver:ExecuteScript",
            {
                "script": script,
                "args": args or [],
                "newSandbox": False,
                "sandbox": "default",
            },
        )
        return result.get("value") if isinstance(result, dict) else result

    def navigate(self, url: str) -> None:
        self.command("WebDriver:Navigate", {"url": url})

    def set_window(self, width: int, height: int) -> None:
        self.command(
            "WebDriver:SetWindowRect",
            {"x": 0, "y": 0, "width": width, "height": height},
        )

    def set_content_zoom(self, zoom: float) -> None:
        self.command("Marionette:SetContext", {"value": "chrome"})
        try:
            self.execute(
                """
                window.gBrowser.selectedBrowser.fullZoom = arguments[0];
                return window.gBrowser.selectedBrowser.fullZoom;
                """,
                [zoom],
            )
        finally:
            self.command("Marionette:SetContext", {"value": "content"})

    def screenshot(self, path: Path) -> None:
        result = self.command(
            "WebDriver:TakeScreenshot",
            {"id": None, "full": False, "hash": False, "scroll": False},
        )
        encoded = result.get("value") if isinstance(result, dict) else result
        if not isinstance(encoded, str) or not encoded:
            raise ExamFailure("Marionette returned no screenshot bytes")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(encoded, validate=True))
        if path.stat().st_size < 1_000:
            raise ExamFailure(f"recorded journey screenshot is too small: {path}")

    def set_reduced_motion(self, enabled: bool) -> None:
        self.command("Marionette:SetContext", {"value": "chrome"})
        try:
            self.execute(
                """
                Services.prefs.setIntPref("ui.prefersReducedMotion", arguments[0] ? 1 : 0);
                return Services.prefs.getIntPref("ui.prefersReducedMotion");
                """,
                [enabled],
            )
        finally:
            self.command("Marionette:SetContext", {"value": "content"})

    def press(self, key: str, *, shift: bool = False) -> None:
        actions: list[dict[str, Any]] = []
        if shift:
            actions.append({"type": "keyDown", "value": KEYS["shift"]})
        actions.extend(
            (
                {"type": "keyDown", "value": KEYS[key]},
                {"type": "keyUp", "value": KEYS[key]},
            )
        )
        if shift:
            actions.append({"type": "keyUp", "value": KEYS["shift"]})
        self.command(
            "WebDriver:PerformActions",
            {
                "actions": [
                    {"type": "key", "id": "keyboard", "actions": actions}
                ]
            },
        )
        self.command("WebDriver:ReleaseActions")

    def type_text(self, value: str) -> None:
        actions: list[dict[str, Any]] = []
        for character in value:
            actions.extend(
                (
                    {"type": "keyDown", "value": character},
                    {"type": "keyUp", "value": character},
                )
            )
        self.command(
            "WebDriver:PerformActions",
            {
                "actions": [
                    {"type": "key", "id": "keyboard", "actions": actions}
                ]
            },
        )
        self.command("WebDriver:ReleaseActions")

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.command("WebDriver:DeleteSession")
            except (ExamFailure, OSError, socket.timeout):
                pass
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
            self.process = None
        if self.profile is not None:
            self.profile.cleanup()
            self.profile = None


AUDIT_SCRIPT = r"""
const root = document.getElementById("app");
const issues = [];
const visible = (element) => {
  const closedDetails = element.closest("details:not([open])");
  if (closedDetails
      && element !== closedDetails.querySelector(":scope > summary")) return false;
  const style = getComputedStyle(element);
  const rect = element.getBoundingClientRect();
  return !element.hidden && style.display !== "none"
    && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
};
const referencedText = (ids) => String(ids || "").split(/\s+/)
  .filter(Boolean).map((id) => document.getElementById(id)?.textContent || "")
  .join(" ").trim();
const accessibleName = (element) => {
  const aria = element.getAttribute("aria-label");
  if (aria && aria.trim()) return aria.trim();
  const labelled = referencedText(element.getAttribute("aria-labelledby"));
  if (labelled) return labelled;
  if (element.labels?.length) {
    const labels = [...element.labels].map((item) => item.textContent.trim())
      .filter(Boolean).join(" ");
    if (labels) return labels;
  }
  const alt = element.getAttribute("alt");
  if (alt && alt.trim()) return alt.trim();
  const title = element.getAttribute("title");
  if (title && title.trim()) return title.trim();
  return (element.textContent || "").trim();
};
const selector = (element) => {
  if (element.id) return `#${element.id}`;
  const cls = [...element.classList].slice(0, 2).join(".");
  const sample = (element.textContent || "").trim().replace(/\s+/g, " ")
    .slice(0, 48);
  return `${element.localName}${cls ? `.${cls}` : ""}`
    + `${sample ? `(${sample})` : ""}`;
};
const labelled = (element) => Boolean(
  element.getAttribute("aria-label")
  || element.getAttribute("aria-labelledby")
  || element.querySelector(":scope > h1, :scope > h2, :scope > h3")
);
const hasHorizontalOwner = (element) => {
  for (let parent = element.parentElement; parent && parent !== document.body;
       parent = parent.parentElement) {
    const style = getComputedStyle(parent);
    if (/(auto|scroll)/.test(style.overflowX)
        && parent.scrollWidth > parent.clientWidth + 1) return true;
  }
  return false;
};

if (!root) issues.push("missing main application region");
const headings = root ? [...root.querySelectorAll("h1")].filter(visible) : [];
if (headings.length !== 1) issues.push(`expected one visible h1, found ${headings.length}`);
if (!document.querySelector("main[aria-labelledby], main[aria-label]")) {
  issues.push("main region has no accessible name");
}
if (!document.querySelector("nav[aria-label='Primary']")) {
  issues.push("primary navigation is unnamed");
}
if (!document.querySelector("nav[aria-label='Breadcrumb']")) {
  issues.push("breadcrumb navigation is unnamed");
}

const ids = [...document.querySelectorAll("[id]")].map((item) => item.id);
const duplicateIds = [...new Set(ids.filter(
  (id, index) => ids.indexOf(id) !== index
))];
if (duplicateIds.length) issues.push(`duplicate ids: ${duplicateIds.join(", ")}`);

if (root) {
  root.querySelectorAll("button, [role='button']").forEach((element) => {
    if (visible(element) && !accessibleName(element)) {
      issues.push(`unnamed button ${selector(element)}`);
    }
  });
  root.querySelectorAll("input:not([type='hidden']), select, textarea").forEach(
    (element) => {
      if (visible(element) && !accessibleName(element)) {
        issues.push(`unnamed form control ${selector(element)}`);
      }
    }
  );
  root.querySelectorAll("form").forEach((element) => {
    if (visible(element) && !labelled(element)) {
      issues.push(`unnamed form ${selector(element)}`);
    }
  });
  root.querySelectorAll("table").forEach((element) => {
    if (!visible(element)) return;
    if (!element.querySelector("caption")
        && !element.getAttribute("aria-label")
        && !element.getAttribute("aria-labelledby")) {
      issues.push(`unnamed table ${selector(element)}`);
    }
    if (!element.querySelector("th")) {
      issues.push(`table without headers ${selector(element)}`);
    }
  });
  root.querySelectorAll("[role='progressbar']").forEach((element) => {
    if (!accessibleName(element)) {
      issues.push(`unnamed progress ${selector(element)}`);
    }
    if (element.getAttribute("aria-valuenow") === null
        || !element.getAttribute("aria-valuetext")) {
      issues.push(`progress lacks value text ${selector(element)}`);
    }
  });
  root.querySelectorAll("[role='dialog']").forEach((element) => {
    if (visible(element) && !accessibleName(element)) {
      issues.push(`unnamed dialog ${selector(element)}`);
    }
  });
  root.querySelectorAll("[role='tablist']").forEach((tablist) => {
    const tabs = [...tablist.querySelectorAll("[role='tab']:not([disabled])")];
    if (!accessibleName(tablist)) issues.push(`unnamed tablist ${selector(tablist)}`);
    if (tabs.length && tabs.filter(
      (tab) => tab.getAttribute("aria-selected") === "true"
    ).length !== 1) issues.push(`tablist must have one selected tab ${selector(tablist)}`);
    tabs.forEach((tab) => {
      const panel = document.getElementById(tab.getAttribute("aria-controls"));
      if (!panel || panel.getAttribute("role") !== "tabpanel") {
        issues.push(`tab has no controlled panel ${selector(tab)}`);
      }
    });
  });
  root.querySelectorAll(".badge").forEach((element) => {
    if (visible(element) && !element.textContent.trim()) {
      issues.push(`color-only badge ${selector(element)}`);
    }
  });
  root.querySelectorAll(".guard, .state.error").forEach((element) => {
    if (visible(element) && !["alert", "status"].includes(
      element.getAttribute("role")
    )) issues.push(`error lacks status semantics ${selector(element)}`);
  });

  const inspected = root.querySelectorAll(
    "a, button, input, select, textarea, summary, pre, code, table, svg"
  );
  [...inspected].forEach((element) => {
    if (!visible(element) || hasHorizontalOwner(element)) return;
    const rect = element.getBoundingClientRect();
    if (rect.left < -2 || rect.right > innerWidth + 2) {
      const style = getComputedStyle(element);
      const parent = element.parentElement;
      const parentRect = parent?.getBoundingClientRect();
      issues.push(`unowned horizontal overflow ${selector(element)} `
        + `[${Math.round(rect.left)},${Math.round(rect.right)}] `
        + `{display:${style.display}, width:${style.width}, max:${style.maxWidth}, `
        + `white-space:${style.whiteSpace}, break:${style.wordBreak}, `
        + `parent:${selector(parent)}, parent-width:${Math.round(parentRect?.width || 0)}}`);
    }
  });
}
if (document.documentElement.scrollWidth > document.documentElement.clientWidth + 1) {
  issues.push(`page horizontal scroll ${document.documentElement.scrollWidth}`
    + `>${document.documentElement.clientWidth}`);
}

return {
  issues,
  metrics: {
    width: innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
    h1: headings.length,
    buttons: root ? root.querySelectorAll("button, [role='button']").length : 0,
    controls: root ? root.querySelectorAll("input, select, textarea").length : 0,
    regions: root ? root.querySelectorAll("section[aria-label], section[aria-labelledby], [role='region']").length : 0,
    tables: root ? root.querySelectorAll("table").length : 0,
    allH1: root ? [...root.querySelectorAll("h1")].map((item) => ({
      text: item.textContent.trim().slice(0, 80),
      display: getComputedStyle(item).display,
      rect: [Math.round(item.getBoundingClientRect().width),
        Math.round(item.getBoundingClientRect().height)],
      closed: Boolean(item.closest("details:not([open])")),
    })) : [],
    mainLabel: root ? {
      labelledby: root.getAttribute("aria-labelledby"),
      label: root.getAttribute("aria-label"),
      busy: root.getAttribute("aria-busy"),
    } : null,
  },
};
"""


class WorkbenchExam:
    def __init__(
        self,
        driver: Marionette,
        base: str,
        *,
        program_active: str = "",
        program_revoked: str = "",
        program_certified: str = "",
        project: str = "",
        repository: Path | None = None,
        memory_run: str = "",
        memory_decision: str = "",
        capture_dir: Path | None = None,
        capture_pattern: str = "",
    ) -> None:
        self.driver = driver
        self.base = base.rstrip("/")
        self.project = project
        self.repository = repository
        self.memory_run = memory_run
        self.memory_decision = memory_decision
        self.capture_dir = capture_dir
        self.capture_pattern = capture_pattern
        self.ids = {
            "program_active": program_active,
            "program_revoked": program_revoked,
            "program_certified": program_certified,
        }
        self.assertions = 0
        self.audits = 0
        self.recorded_journey_steps = 0
        self.recorded_journey_assertions = 0
        self.phase32_exams: set[tuple[str, str]] = set()
        self.focus_indicator_negative_control_proven = False

    def check(self, condition: bool, message: str) -> None:
        self.assertions += 1
        if not condition:
            raise ExamFailure(message)

    def journey_check(self, condition: bool, message: str) -> None:
        before = self.assertions
        self.check(condition, message)
        self.recorded_journey_assertions += self.assertions - before

    def record_memory_step(self, number: int, slug: str) -> None:
        if self.capture_dir is None:
            raise ExamFailure("recorded memory journey has no capture directory")
        path = self.capture_dir / f"memory-closed-loop-{number:02d}-{slug}.png"
        self.driver.screenshot(path)
        self.recorded_journey_steps += 1
        self.journey_check(path.is_file() and path.stat().st_size >= 1_000,
                           f"memory journey step {number} was not recorded")

    def wait(
        self,
        predicate: Callable[[], Any],
        description: str,
        timeout: float = 60,
    ) -> Any:
        deadline = time.monotonic() + timeout
        last: Any = None
        while time.monotonic() < deadline:
            try:
                last = predicate()
                if last:
                    return last
            except ExamFailure:
                raise
            except Exception:
                pass
            time.sleep(0.05)
        raise ExamFailure(f"timed out waiting for {description}; last={last!r}")

    def url(self, route: str) -> str:
        try:
            route = route.format(**self.ids)
        except KeyError as exc:
            raise ExamFailure(f"missing fixture id for route: {exc}") from exc
        if "{" in route:
            raise ExamFailure(f"unresolved fixture route: {route}")
        if self.project:
            project = "project=" + quote(self.project, safe="")
            if route.startswith("/?"):
                route = "/?" + project + "&" + route[2:]
            elif route.startswith("/#"):
                route = "/?" + project + route[1:]
        return self.base + route

    def navigate(self, route: str, selector: str) -> None:
        expected_url = self.url(route)
        self.driver.navigate(expected_url)
        self.wait(
            lambda: self.driver.execute(
                """
                const app = document.getElementById("app");
                return location.href === arguments[1]
                  && document.readyState === "complete" && app
                  && app.getAttribute("aria-busy") === "false"
                  && Boolean(document.querySelector(arguments[0]));
                """,
                [selector, expected_url],
            ),
            f"{route} to render {selector}",
        )

    def focus(self, selector: str) -> None:
        result = self.driver.execute(
            """
            const matches = [...document.querySelectorAll(arguments[0])];
            const element = matches.find((candidate) => candidate.offsetParent !== null) || matches[0];
            if (!element) return false;
            const target = element.shadowRoot?.querySelector('button, a[href], input, select, textarea')
              || element.querySelector?.('button, a[href], input, select, textarea') || element;
            target.focus();
            return document.activeElement === element || document.activeElement === target;
            """,
            [selector],
        )
        self.check(bool(result), f"could not focus {selector}")

    def press_until(
        self,
        trigger: str,
        condition: Callable[[], Any],
        description: str,
        attempts: int = 5,
    ) -> None:
        """Focus trigger and press Enter, retrying if the app re-rendered
        between focus and press and the keystroke landed on a detached node.
        Only used for idempotent controls."""
        for attempt in range(attempts):
            try:
                if attempt and condition():
                    return
            except Exception:
                pass
            try:
                self.wait(
                    lambda: self.selector_exists(trigger),
                    f"{description} trigger to render",
                    timeout=15,
                )
                self.focus(trigger)
                self.driver.press("enter")
                self.wait(condition, description, timeout=30)
                return
            except ExamFailure:
                if attempt == attempts - 1:
                    raise

    def type_until(
        self,
        selector: str,
        value: str,
        description: str,
        attempts: int = 5,
    ) -> None:
        """Keyboard-type into a rerenderable field until its live value sticks."""
        for attempt in range(attempts):
            self.focus(selector)
            self.driver.execute(
                """
                const field = document.querySelector(arguments[0]);
                if (!field) return false;
                field.value = '';
                return true;
                """,
                [selector],
            )
            self.driver.type_text(value)
            try:
                self.wait(
                    lambda: self.driver.execute(
                        "return document.querySelector(arguments[0])?.value === arguments[1];",
                        [selector, value],
                    ),
                    description,
                    timeout=15,
                )
                return
            except ExamFailure:
                if attempt == attempts - 1:
                    raise

    def select_until(
        self,
        selector: str,
        key: str,
        expected: str,
        description: str,
        attempts: int = 5,
    ) -> None:
        """Keyboard-select an option until the live rerendered control agrees."""
        for attempt in range(attempts):
            self.focus(selector)
            self.driver.press(key)
            try:
                self.wait(
                    lambda: self.driver.execute(
                        "return document.querySelector(arguments[0])?.value === arguments[1];",
                        [selector, expected],
                    ),
                    description,
                    timeout=15,
                )
                return
            except ExamFailure:
                if attempt == attempts - 1:
                    raise

    def active_matches(self, selector: str) -> bool:
        return bool(
            self.driver.execute(
                """
                const active = document.activeElement;
                return Boolean(active && (
                  active.matches(arguments[0]) || active.closest(arguments[0])
                ));
                """,
                [selector],
            )
        )

    def selector_exists(self, selector: str) -> bool:
        return bool(
            self.driver.execute(
                "return Boolean(document.querySelector(arguments[0]));",
                [selector],
            )
        )

    def audit_page(self, journey_id: str, viewport: str) -> None:
        result = self.driver.execute(AUDIT_SCRIPT)
        self.audits += 1
        issues = result.get("issues", []) if isinstance(result, dict) else []
        metrics = result.get("metrics", {}) if isinstance(result, dict) else {}
        self.check(
            not issues,
            f"{journey_id}/{viewport} semantic or layout audit failed: "
            + "; ".join(issues)
            + f"; metrics={metrics!r}",
        )
        expected_width = WIDE[0] if viewport == "wide" else NARROW[0]
        actual_width = int(metrics.get("width", 0))
        minimum_width = expected_width - 20 if viewport == "wide" else 320
        self.check(
            actual_width <= expected_width and actual_width >= minimum_width,
            f"{journey_id}/{viewport} used unexpected client width "
            f"{actual_width} (requested {expected_width})",
        )

    def audit_journey(self, journey_id: str, viewport: str) -> None:
        case = JOURNEY_CASES[journey_id]
        self.navigate(case["route"], case["selector"])
        if viewport == "narrow":
            # Firefox enforces a 500px minimum outer window under WebDriver.
            # Native page zoom gives a stricter <=390 CSS-pixel layout viewport
            # while the screenshot half of the harness still renders the exact
            # unzoomed 390x844 geometry.
            self.driver.set_content_zoom(1.5)
            dimensions: Any = None
            for _attempt in range(40):
                dimensions = self.driver.execute(
                    """
                    return {innerWidth, innerHeight,
                      clientWidth: document.documentElement.clientWidth,
                      scrollWidth: document.documentElement.scrollWidth,
                      dpr: devicePixelRatio};
                    """
                )
                if int(dimensions.get("innerWidth", 9999)) <= 390:
                    break
                time.sleep(0.05)
            else:
                raise ExamFailure(
                    f"{journey_id} zoomed narrow CSS viewport was not applied: "
                    f"{dimensions!r}"
                )
        self.audit_page(journey_id, viewport)
        if journey_id in PHASE32_JOURNEYS:
            self.audit_phase32_journey(journey_id, viewport)

    def assert_technical_round_trip(self, journey_id: str, viewport: str) -> None:
        summary = ".live-technical > summary"
        self.check(
            self.selector_exists(summary),
            f"{journey_id}/{viewport} has no Technical details route",
        )
        is_open = lambda: bool(self.driver.execute(
            "return Boolean(document.querySelector('.live-technical')?.open);"
        ))
        if is_open():
            self.press_until(
                summary,
                lambda: not is_open() and self.active_matches(summary),
                f"{journey_id}/{viewport} Technical details to close first",
            )
        self.press_until(
            summary,
            lambda: is_open() and self.active_matches(summary),
            f"{journey_id}/{viewport} Technical details to open in place",
        )
        self.press_until(
            summary,
            lambda: not is_open() and self.active_matches(summary),
            f"{journey_id}/{viewport} Technical details to return to opener",
        )
        self.assertions += 3

    def install_focus_walk_tracker(self) -> None:
        self.driver.execute(
            """
            window.__examFocusObserver?.disconnect();
            window.__examFocusGeneration = 0;
            window.__examFocusObserver = new MutationObserver((records) => {
              if (records.some((record) => record.type === 'childList')) {
                window.__examFocusGeneration += 1;
              }
            });
            window.__examFocusObserver.observe(document.getElementById('app'), {
              childList: true,
              subtree: true,
            });
            """
        )

    def prepare_focus_walk_step(self) -> int:
        return int(
            self.driver.execute(
                """
                const visible = (element) => {
                  const style = getComputedStyle(element);
                  const rect = element.getBoundingClientRect();
                  const closed = element.closest('details:not([open])');
                  if (closed && element !== closed.querySelector(':scope > summary')) return false;
                  return !element.hidden && !element.disabled
                    && style.display !== 'none' && style.visibility !== 'hidden'
                    && rect.width > 0 && rect.height > 0;
                };
                [...document.querySelectorAll(
                  '#app a[href], #app button, #app input, #app select, #app textarea, #app summary'
                )].filter((element) => visible(element) && element.tabIndex >= 0
                  && !element.closest('.live-technical > :not(summary)'))
                  .forEach((element, index) => { element.dataset.examTabTarget = String(index); });
                return window.__examFocusGeneration;
                """
            )
        )

    def measure_focus_walk_step(self) -> dict[str, Any]:
        state = self.driver.execute(
            """
            const visible = (element) => {
              const style = getComputedStyle(element);
              const rect = element.getBoundingClientRect();
              const closed = element.closest('details:not([open])');
              if (closed && element !== closed.querySelector(':scope > summary')) return false;
              return !element.hidden && !element.disabled
                && style.display !== 'none' && style.visibility !== 'hidden'
                && rect.width > 0 && rect.height > 0;
            };
            const controls = [...document.querySelectorAll(
              '#app a[href], #app button, #app input, #app select, #app textarea, #app summary'
            )].filter((element) => visible(element) && element.tabIndex >= 0
              && !element.closest('.live-technical > :not(summary)'));
            controls.forEach((element, index) => {
              element.dataset.examTabTarget = String(index);
            });
            const active = document.activeElement;
            const id = active?.dataset?.examTabTarget || '';
            const current = id !== '' && active === controls[Number(id)]
              && active.isConnected;
            if (!current) {
              return {generation: window.__examFocusGeneration, id, current: false,
                visible: true};
            }
            const style = getComputedStyle(active);
            const width = parseFloat(style.outlineWidth || '0');
            const ring = (style.outlineStyle !== 'none' && width >= 2)
              || (style.boxShadow && style.boxShadow !== 'none');
            const detail = `${id}:${active.tagName.toLowerCase()}:${active.textContent.trim().slice(0, 60)}:focus=true:outline=${style.outlineStyle}/${style.outlineWidth}:shadow=${style.boxShadow}`;
            return {generation: window.__examFocusGeneration, id, current: true,
              visible: Boolean(ring), detail};
            """
        )
        return state if isinstance(state, dict) else {}

    def begin_focus_stability_check(self) -> None:
        self.driver.execute(
            """
            window.__examStableFocusElement = null;
            window.__examStableFocusChecks = 0;
            """
        )

    def wait_for_focus_stability(
        self, description: str, timeout: float = 5
    ) -> None:
        self.wait(
            lambda: self.driver.execute(
                """
                const active = document.activeElement;
                if (!active || active === document.body) {
                  window.__examStableFocusElement = null;
                  window.__examStableFocusChecks = 0;
                  return false;
                }
                if (window.__examStableFocusElement === active) {
                  window.__examStableFocusChecks += 1;
                } else {
                  window.__examStableFocusElement = active;
                  window.__examStableFocusChecks = 1;
                }
                return window.__examStableFocusChecks >= 2;
                """
            ),
            description,
            timeout=timeout,
        )

    def tab_to_current_target(
        self,
        target_id: str,
        step_budget: int,
        deadline: float | None = None,
    ) -> dict[str, Any] | None:
        # Begin from the real predecessor chain rather than guessing that the
        # preceding light-DOM control is one Tab away. Custom-element shadow
        # buttons can add stops between two controls returned by querySelectorAll.
        for _attempt in range(5):
            if deadline is not None and time.monotonic() >= deadline:
                return None
            self.focus("#skip-link")
            for _step in range(step_budget):
                if deadline is not None and time.monotonic() >= deadline:
                    return None
                generation = self.prepare_focus_walk_step()
                self.begin_focus_stability_check()
                self.driver.press("tab")
                stability_timeout = 5.0
                if deadline is not None:
                    stability_timeout = min(
                        stability_timeout, max(0.001, deadline - time.monotonic())
                    )
                self.wait_for_focus_stability(
                    "Tab focus to remain stable", timeout=stability_timeout
                )
                state = self.measure_focus_walk_step()
                if int(state.get("generation", -1)) != generation:
                    # The key event crossed a live redraw. Start this proof again
                    # on one DOM generation; do not score the replaced node.
                    break
                if not bool(state.get("current")):
                    continue
                if str(state.get("id", "")) == target_id:
                    return state
        return None

    def observe_focus_on_target(
        self,
        target_id: str,
        step_budget: int,
        description: str,
        timeout: float = 15,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout

        def replay() -> dict[str, Any] | bool:
            try:
                return (
                    self.tab_to_current_target(
                        target_id, step_budget, deadline=deadline
                    )
                    or False
                )
            except ExamFailure:
                # A live replacement can invalidate any individual replay. The
                # enclosing wait owns the one bounded retry budget.
                return False

        try:
            return self.wait(replay, description, timeout=timeout)
        except ExamFailure as exc:
            raise ExamFailure(
                f"could not observe focus on {description} within budget"
            ) from exc

    def assert_focus_indicator_negative_control(
        self, target_id: str, step_budget: int
    ) -> None:
        if self.focus_indicator_negative_control_proven:
            return
        planted = self.driver.execute(
            """
            const target = document.querySelector(
              `[data-exam-tab-target="${CSS.escape(arguments[0])}"]`
            );
            if (!target) return false;
            const style = document.createElement('style');
            style.id = 'exam-missing-focus-ring';
            style.textContent = `html body .app [data-exam-tab-target="${CSS.escape(arguments[0])}"]:focus { outline: none !important; box-shadow: none !important; }`;
            document.head.appendChild(style);
            return true;
            """,
            [target_id],
        )
        self.check(bool(planted), "could not plant missing focus-ring violation")
        try:
            state = self.observe_focus_on_target(
                target_id,
                step_budget,
                "planted focus-ring target",
            )
            self.check(
                not bool(state.get("visible")),
                "focus-ring assertion did not catch planted outline:none violation",
            )
        finally:
            self.driver.execute(
                "document.getElementById('exam-missing-focus-ring')?.remove();"
            )
        # Re-drive the real Tab chain after removing the stylesheet. A concurrent
        # redraw can invalidate a focus=false measurement, but a focused control
        # with no restored ring is still a real failure.
        restored = self.observe_focus_on_target(
            target_id,
            step_budget,
            "negative-control target after planted violation was removed",
        )
        self.check(
            bool(restored.get("visible")),
            "focus ring did not recover after planted violation was removed",
        )
        self.focus_indicator_negative_control_proven = True

    def assert_ordinary_tab_reachability(
        self, journey_id: str, viewport: str
    ) -> None:
        # Loaded desks fill a few independent panels after the route shell is
        # ready. Measure keyboard order only after the visible control signature
        # has remained unchanged; this is condition-based, not a fixed sleep.
        stable_signature = None
        stable_since = time.monotonic()

        def controls_settled() -> bool:
            nonlocal stable_signature, stable_since
            signature = self.driver.execute(
                """
                return [...document.querySelectorAll(
                  '#app a[href], #app button, #app input, #app select, #app textarea, #app summary'
                )].filter((element) => element.offsetParent !== null)
                  .map((element) => `${element.tagName}:${element.id}:${element.textContent.trim().slice(0, 40)}`)
                  .join('|');
                """
            )
            now = time.monotonic()
            if signature != stable_signature:
                stable_signature = signature
                stable_since = now
                return False
            return bool(signature) and now - stable_since >= 0.5

        self.wait(controls_settled, f"{journey_id}/{viewport} controls to settle")
        expected = self.driver.execute(
            """
            const visible = (element) => {
              const style = getComputedStyle(element);
              const rect = element.getBoundingClientRect();
              const closed = element.closest('details:not([open])');
              if (closed && element !== closed.querySelector(':scope > summary')) return false;
              return !element.hidden && !element.disabled
                && style.display !== 'none' && style.visibility !== 'hidden'
                && rect.width > 0 && rect.height > 0;
            };
            const controls = [...document.querySelectorAll(
              '#app a[href], #app button, #app input, #app select, '
              + '#app textarea, #app summary'
            )].filter((element) => visible(element) && element.tabIndex >= 0
              && !element.closest('.live-technical > :not(summary)'));
            controls.forEach((element, index) => {
              element.dataset.examTabTarget = String(index);
            });
            return controls.map((element) => element.dataset.examTabTarget);
            """
        )
        self.check(
            bool(expected),
            f"{journey_id}/{viewport} exposes no ordinary keyboard controls",
        )
        self.install_focus_walk_tracker()
        self.focus("#skip-link")
        reached: set[str] = set()
        missing_focus_indicator: set[str] = set()
        missing_focus_details: dict[str, str] = {}
        # Custom-element buttons add shadow-tree stops that are not returned by
        # document.querySelectorAll. Allow complete keyboard cycles without a
        # fixed sleep or assuming how many component hosts a loaded desk has.
        step_budget = (len(expected) * 4) + 60
        for _index in range(step_budget):
            generation = self.prepare_focus_walk_step()
            self.driver.press("tab")
            state = self.measure_focus_walk_step()
            if int(state.get("generation", -1)) != generation:
                # The Tab and measurement straddled a redraw. The active node is
                # not evidence about either generation, so continue without
                # scoring it as reached or as a missing ring.
                continue
            target = str(state.get("id", ""))
            if target and bool(state.get("current")):
                reached.add(target)
                if not bool(state.get("visible")):
                    missing_focus_indicator.add(target)
                    missing_focus_details[target] = str(state.get("detail", target))
                else:
                    missing_focus_indicator.discard(target)
                    missing_focus_details.pop(target, None)
            if reached == set(expected):
                break
        missing = sorted(set(expected) - reached)
        # Re-prove a missing target by walking its real Tab chain on one DOM
        # generation. This includes shadow-tree stops and retries only when a
        # redraw actually crossed the key event and its measurement.
        for target_id in list(missing):
            state = self.tab_to_current_target(target_id, step_budget)
            if state:
                reached.add(target_id)
                if not bool(state.get("visible")):
                    missing_focus_indicator.add(target_id)
                    missing_focus_details[target_id] = str(
                        state.get("detail", target_id)
                    )
        missing = sorted(set(expected) - reached)
        missing_details = self.driver.execute(
            """
            return arguments[0].map((id) => {
              const element = [...document.querySelectorAll(`[data-exam-tab-target="${CSS.escape(id)}"]`)].find((candidate) => candidate.offsetParent !== null);
              return element ? `${id}:${element.tagName.toLowerCase()}:${element.textContent.trim().slice(0, 60)}` : `${id}:replaced`;
            });
            """,
            [missing],
        )
        self.check(
            not missing,
            f"{journey_id}/{viewport} Tab did not reach ordinary actions {missing_details}",
        )
        # Tab reachability is proved independently above. Re-drive each reported
        # ring miss through its real Tab chain. A focus=false measurement was
        # invalidated by concurrent live activity and is retried within one wait
        # budget; once the expected control is focused, its computed ring result
        # is final. This keeps a real outline:none defect failing.
        for target_id in list(missing_focus_indicator):
            state = self.observe_focus_on_target(
                target_id,
                step_budget,
                f"{journey_id}/{viewport} Tab target {target_id}",
            )
            if bool(state.get("visible")):
                missing_focus_indicator.discard(target_id)
                missing_focus_details.pop(target_id, None)
            else:
                missing_focus_details[target_id] = str(
                    state.get("detail", target_id)
                )
        self.assert_focus_indicator_negative_control(str(expected[0]), step_budget)
        missing_focus = sorted(missing_focus_indicator)
        focus_details = [missing_focus_details[target] for target in missing_focus]
        self.check(
            not missing_focus_indicator,
            f"{journey_id}/{viewport} has no visible focus indicator on {focus_details}",
        )

    def audit_phase32_journey(self, journey_id: str, viewport: str) -> None:
        config = PHASE32_JOURNEYS[journey_id]
        facts = self.driver.execute(
            """
            const next = document.querySelector('.live-next h2')?.textContent.trim();
            const recovery = document.querySelector('.live-recovery')?.textContent.trim();
            return {next, recovery};
            """
        )
        self.check(
            bool(facts.get("next")),
            f"{journey_id}/{viewport} has no canonical next step",
        )
        self.check(
            bool(facts.get("recovery")),
            f"{journey_id}/{viewport} has no refusal or recovery outcome",
        )
        # The page has already proven its live projection and recovery truth.
        # Close only the explicit SSE reader while keyboard edges are measured;
        # manual refresh below still proves a real replacement render.
        self.driver.execute(
            """
            if (typeof stopRunLive === 'function') stopRunLive();
            if (typeof stopProgramLive === 'function') stopProgramLive();
            return true;
            """
        )
        self.assert_technical_round_trip(journey_id, viewport)
        self.assert_ordinary_tab_reachability(journey_id, viewport)
        refresh = str(config["refresh"])
        self.assert_focus_preserved(refresh, f"{journey_id}/{viewport} refresh")
        # Tab traversal above reaches every currently available ordinary action.
        # The dedicated core/program interaction legs below open and dismiss the
        # real confirmation dialogs after supplying any required reason.
        self.phase32_exams.add((journey_id, viewport))

    def assert_dialog_round_trip(
        self,
        trigger: str,
        dialog: str,
        *,
        timeout: float = 12,
    ) -> None:
        self.press_until(
            trigger,
            lambda: self.selector_exists(dialog) and self.active_matches(dialog),
            f"{dialog} to open and receive focus",
        )
        self.driver.press("escape")
        self.wait(
            lambda: not self.selector_exists(dialog)
            and self.active_matches(trigger),
            f"{dialog} to close and restore {trigger}",
            timeout,
        )
        self.assertions += 2

    def assert_focus_preserved(self, selector: str, render_function: str) -> None:
        self.focus(selector)
        marked = self.driver.execute(
            """
            const element = document.querySelector(arguments[0]);
            if (!element) return false;
            element.dataset.accessibilityOriginal = "true";
            return true;
            """,
            [selector],
        )
        self.check(bool(marked), f"could not mark {selector} before refresh")
        self.press_until(
            selector,
            lambda: self.driver.execute(
                """
                const element = document.querySelector(arguments[0]);
                return Boolean(element
                  && !element.dataset.accessibilityOriginal);
                """,
                [selector],
            ),
            f"{render_function} to replace {selector}",
        )
        self.check(
            self.active_matches(selector),
            f"{render_function} moved focus away from {selector}",
        )

    def test_slick_workbench(self) -> None:
        """Exercise WLA-35-09 behavior, not only its source markers."""
        self.driver.set_window(*WIDE)
        self.driver.set_content_zoom(1)
        self.navigate("/#/", ".board-overview h1")

        skeleton_first = self.driver.execute(
            """
            window.__slickFetch = window.fetch;
            window.fetch = () => new Promise(() => {});
            window.dispatchEvent(new Event('hashchange'));
            return document.getElementById("app").getAttribute("aria-busy") === "true"
              && Boolean(document.querySelector(".route-skeleton dw-skeleton"));
            """
        )
        self.check(bool(skeleton_first), "normal route did not expose its skeleton shell immediately")
        self.driver.execute("window.fetch = window.__slickFetch; document.getElementById('refresh-btn').click();")
        self.wait(
            lambda: self.driver.execute(
                'return document.getElementById("app").getAttribute("aria-busy") === "false";'
            ),
            "route to recover after skeleton-first probe",
        )

        initial_order = self.driver.execute(
            """
            return [...document.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),summary')]
              .filter((el) => el.offsetParent !== null)
              .map((el) => el.id || el.getAttribute('href') || el.textContent.trim().slice(0, 40));
            """
        )
        self.press_until(
            "#density-toggle",
            lambda: self.driver.execute(
                'return document.documentElement.dataset.density === "compact";'
            ),
            "compact density to apply",
        )
        density = self.driver.execute(
            """
            const controls = [...document.querySelectorAll('button,select,summary,input:not([type="hidden"]),textarea')]
              .filter((el) => el.offsetParent !== null)
              .map((el) => el.getBoundingClientRect());
            const order = [...document.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),summary')]
              .filter((el) => el.offsetParent !== null)
              .map((el) => el.id || el.getAttribute('href') || el.textContent.trim().slice(0, 40));
            return {
              stored: localStorage.getItem('delivery-workbench.density'),
              smallest: Math.min(...controls.map((rect) => Math.min(rect.width, rect.height))),
              order,
            };
            """
        )
        self.check(density["stored"] == "compact", "compact density was not persisted")
        self.check(density["order"] == initial_order, "density changed keyboard order")
        self.check(float(density["smallest"]) >= 24, "compact density produced a target below 24px")

        self.driver.set_window(*NARROW)
        self.driver.set_content_zoom(1.5)
        self.wait(
            lambda: int(self.driver.execute("return document.documentElement.clientWidth;")) <= 390,
            "compact 390px viewport",
        )
        self.audit_page("slick-density-compact", "narrow")
        self.navigate("/?snapshot=1&project=sample&memoryscenario=rich#/board/sample", ".memory-panel")
        provenance = self.driver.execute(
            """
            const panel = document.querySelector('.memory-panel');
            const code = panel && panel.querySelector('.copyable-id code');
            const button = panel && panel.querySelector('.copy-id-action');
            return panel && code && button ? {
              bodyOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
              codeRight: code.getBoundingClientRect().right,
              panelRight: panel.getBoundingClientRect().right,
              buttonHeight: button.getBoundingClientRect().height,
            } : null;
            """
        )
        self.check(bool(provenance), "memory provenance copy action was missing at 390px")
        self.check(not provenance["bodyOverflow"], "memory pane created horizontal body scrolling")
        self.check(provenance["codeRight"] <= provenance["panelRight"] + 1, "memory provenance escaped its pane")
        self.check(float(provenance["buttonHeight"]) >= 24, "memory copy target was too small")

        self.press_until(
            ".memory-panel .copy-id-action",
            lambda: self.driver.execute(
                "return /Identifier copied|Could not copy/.test(document.getElementById('live-status').textContent);"
            ),
            "memory identifier copy action",
        )
        copy_result = self.driver.execute(
            """
            const button = document.querySelector('.memory-panel .copy-id-action');
            return {text: document.getElementById('live-status').textContent,
              identifier: button ? button.dataset.copyText : ''};
            """
        )
        self.check(len(str(copy_result["identifier"])) >= 24, "copy action did not retain the full identifier")
        self.check(bool(copy_result["text"]), "copy action gave no assistive feedback")

        for state, phrase in (
            ("disconnected", "disconnected"),
            ("retrying", "Retrying"),
            ("caught-up", "caught up"),
            ("restored", "restored"),
            ("capacity", "Retry in a moment"),
        ):
            self.navigate(
                f"/?snapshot=1&project=sample&liveconnection=global-{state}#/board/sample",
                ".dw-stream-notice",
            )
            notice = self.driver.execute(
                """
                const notice = document.querySelector('.dw-stream-notice');
                return notice ? {text: notice.textContent, role: notice.getAttribute('role'),
                  state: document.getElementById('dw-connection-status').dataset.connectionState} : null;
                """
            )
            self.check(bool(notice) and phrase in notice["text"], f"global {state} guidance was not visible")
            self.check(notice["role"] in {"status", "alert"}, f"global {state} was not announced")

        self.navigate("/?snapshot=1#/projects", "#project-selector-form")
        self.driver.execute(
            "document.querySelectorAll('input[name=project]').forEach((input) => input.checked = false);"
        )
        self.press_until(
            "#project-selector-form button[type=submit]",
            lambda: self.driver.execute(
                "return !document.getElementById('project-selector-error').hidden;"
            ),
            "described project form error",
        )
        described = self.driver.execute(
            """
            const input = document.querySelector('input[name=project]');
            const id = input.getAttribute('aria-describedby');
            const error = document.getElementById(id);
            return input.getAttribute('aria-invalid') === 'true' && error && !error.hidden && Boolean(error.textContent.trim());
            """
        )
        self.check(bool(described), "form error was not connected with aria-describedby")
        self.driver.execute("document.getElementById('density-toggle').click();")
        self.driver.set_content_zoom(1.5)
        self.wait(
            lambda: int(self.driver.execute("return document.documentElement.clientWidth;")) <= 390,
            "comfortable 390px viewport",
        )
        self.audit_page("slick-density-comfortable", "narrow")
        self.check(
            self.driver.execute(
                "return localStorage.getItem('delivery-workbench.density') === 'comfortable';"
            ),
            "comfortable density was not persisted",
        )

        self.driver.set_reduced_motion(True)
        self.navigate("/?snapshot=1&designfocus=1#/design", ".design-ref")
        motion = self.driver.execute(
            """
            const skeleton = document.querySelector('dw-skeleton .dw-skeleton-line');
            const button = document.querySelector('.design-ref button, .design-ref dw-button');
            const root = getComputedStyle(document.documentElement);
            return {
              matches: matchMedia('(prefers-reduced-motion: reduce)').matches,
              animation: skeleton ? getComputedStyle(skeleton).animationName : '',
              transition: button ? getComputedStyle(button).transitionDuration : '',
              panel: root.getPropertyValue('--motion-panel').trim(),
            };
            """
        )
        self.check(bool(motion["matches"]), "reduced-motion media query was not active")
        self.check(motion["animation"] == "none", "skeleton animation remained under reduced motion")
        self.check(all(part.strip() == "0s" for part in motion["transition"].split(",")), "transition remained under reduced motion")
        self.check(motion["panel"] == "0s", "shared panel motion token was not disabled")
        self.driver.set_reduced_motion(False)
        self.driver.set_content_zoom(1)
        self.driver.set_window(*WIDE)

    def test_core_interactions(self) -> None:
        self.driver.set_window(*WIDE)
        self.navigate("/#/", ".board-overview h1")

        self.driver.press("tab")
        self.check(
            self.active_matches("#skip-link"),
            "first Tab did not expose the skip-to-content control",
        )
        self.driver.press("enter")
        self.wait(
            lambda: self.active_matches("#app h1, #app"),
            "skip control to focus main content",
        )
        self.assertions += 1

        # The selected-project board is the home surface. Exercise its common
        # acts from the keyboard, including client and server refusals. Only the
        # pause/resume pair is applied, and resume restores the fixture state.
        create_trigger = '[data-board-create][data-phase="0"]'
        self.press_until(
            create_trigger,
            lambda: self.selector_exists("#board-create-form")
            and self.active_matches(".board-action-panel"),
            "keyboard create panel",
        )
        self.type_until(
            '#board-create-form input[name="title"]',
            "Keyboard board task",
            "keyboard board title to be retained",
        )
        self.focus('#board-create-form select[name="status"]')
        self.driver.press("down")
        self.press_until(
            '#board-create-form button[type="submit"]',
            lambda: self.selector_exists(".board-preview")
            and "Keyboard board task" in str(self.driver.execute(
                "return document.querySelector('.board-preview h2')?.textContent || '';"
            )),
            "keyboard create preview",
        )
        self.check(
            not bool(self.driver.execute(
                "return [...document.querySelectorAll('.bcard-title')].some(card => card.textContent.includes('Keyboard board task'));"
            )),
            "create preview changed the board before apply",
        )
        self.driver.press("escape")
        self.wait(
            lambda: not self.selector_exists(".board-action-panel")
            and self.active_matches(create_trigger),
            "create preview dismissal to restore its lane control",
        )

        story = '.bcard[data-story="SMP-0-02"]'
        move_trigger = story + " [data-board-move]"
        self.press_until(
            move_trigger,
            lambda: self.selector_exists("#move-form"),
            "keyboard move panel",
        )
        self.select_until(
            '#move-form select[name="status"]',
            "home",
            "backlog",
            "keyboard move destination to be retained",
        )
        self.press_until(
            '#move-form button[type="submit"]',
            lambda: self.selector_exists(".board-preview"),
            "keyboard move exact-diff preview",
        )
        self.check(
            self.selector_exists(story + '[data-status="in-progress"]'),
            "move preview changed the card before apply",
        )
        self.driver.press("escape")
        self.wait(
            lambda: not self.selector_exists(".board-action-panel")
            and self.active_matches(move_trigger),
            "move preview dismissal to restore its card control",
        )

        park_trigger = story + " [data-board-park]"
        self.press_until(
            park_trigger,
            lambda: self.selector_exists("#move-form"),
            "keyboard park panel",
        )
        self.press_until(
            '#move-form button[type="submit"]',
            lambda: self.selector_exists("#move-out .board-refusal"),
            "reasonless park refusal announcement",
        )
        self.check(
            not self.selector_exists("#move-out .board-preview")
            and self.selector_exists(story + '[data-status="in-progress"]'),
            "reasonless park reached preview or changed the board",
        )
        self.driver.press("escape")
        self.wait(
            lambda: not self.selector_exists(".board-action-panel")
            and self.active_matches(park_trigger),
            "park refusal dismissal to restore its card control",
        )

        # Done is offered, but the existing server authority refuses it because
        # this story has no proof. The refusal stays focused and the card stays put.
        self.press_until(
            move_trigger,
            lambda: self.selector_exists("#move-form"),
            "done move panel",
        )
        self.select_until(
            '#move-form select[name="status"]',
            "end",
            "done",
            "keyboard done destination to be retained",
        )
        self.press_until(
            '#move-form button[type="submit"]',
            lambda: self.selector_exists("#move-out .board-refusal"),
            "missing-proof done refusal announcement",
        )
        self.check(
            self.selector_exists(story + '[data-status="in-progress"]'),
            "missing-proof done refusal changed the board",
        )
        self.driver.press("escape")
        self.wait(lambda: not self.selector_exists(".board-action-panel"), "done refusal dismissal")

        pause_trigger = '[data-board-phase-action="pause_phase"][data-phase="0"]'
        self.press_until(
            '[data-board-view="phase"]',
            lambda: self.driver.execute(
                "return document.querySelector('.board-phase-view')?.classList.contains('hidden') === false;"
            ),
            "phase board view",
        )
        self.press_until(
            pause_trigger,
            lambda: self.selector_exists("#board-phase-form"),
            "keyboard pause panel",
        )
        self.type_until(
            '#board-phase-form input[name="reason"]',
            "Keyboard pause review",
            "keyboard pause reason to be retained",
        )
        self.driver.press("escape")
        self.wait(
            lambda: not self.selector_exists(".board-action-panel")
            and self.active_matches(pause_trigger),
            "pause review dismissal to restore its lane control",
        )
        self.assertions += 8

        self.press_until(
            "#advanced-toggle",
            lambda: self.driver.execute(
                "return document.getElementById('advanced-toggle').getAttribute('aria-expanded') === 'true';"
            ),
            "advanced navigation to open",
        )
        self.focus("#plan-link")
        self.driver.press("enter")
        self.wait(
            lambda: self.driver.execute(
                """
                return location.hash === "#/program-studio"
                  && document.getElementById("app")?.getAttribute("aria-busy") === "false"
                  && document.activeElement?.matches("#app h1");
                """
            ),
            "primary navigation to focus the destination heading",
        )
        self.assertions += 1

        self.assert_dialog_round_trip(
            '[data-delivery-choice="program"]',
            "#delivery-review",
        )

        self.focus(".delivery-technical > summary")
        self.driver.press("enter")
        details = self.driver.execute(
            """
            const summary = document.querySelector(".delivery-technical > summary");
            return Boolean(summary?.parentElement.open
              && document.activeElement === summary);
            """
        )
        self.check(
            bool(details),
            "native delivery technical disclosure did not toggle in place",
        )

        self.navigate(
            "/#/program-studio/workflow/architect-debate-delivery",
            ".program-studio h1",
        )
        self.focus('[data-studio-view="plan"]')
        self.driver.press("right")
        self.wait(
            lambda: self.driver.execute(
                """
                const tab = document.querySelector('[data-studio-view="simulate"]');
                return tab?.getAttribute("aria-selected") === "true"
                  && document.activeElement === tab;
                """
            ),
            "studio ArrowRight tab activation",
        )
        self.assertions += 1
        self.driver.press("home")
        self.wait(
            lambda: self.driver.execute(
                """
                const tab = document.querySelector('[data-studio-view="plan"]');
                return tab?.getAttribute("aria-selected") === "true"
                  && document.activeElement === tab;
                """
            ),
            "studio Home tab activation",
        )
        self.assertions += 1

        title_selector = '[data-studio-field="document.title"]'
        self.focus(title_selector)
        retained_title = "Keyboard focus retention proof"
        changed = self.driver.execute(
            """
            const field = document.querySelector(arguments[0]);
            field.value = arguments[1];
            field.dispatchEvent(new Event("change", {bubbles: true}));
            return field.value;
            """,
            [title_selector, retained_title],
        )
        self.check(
            changed == retained_title,
            "studio title change was not retained in the draft",
        )
        self.wait(
            lambda: self.driver.execute(
                """
                return document.querySelector(arguments[0])?.value
                  === arguments[1];
                """,
                [title_selector, retained_title],
            ),
            "compiler refresh to retain draft title",
        )
        self.assert_dialog_round_trip(
            "#studio-preview-save",
            ".studio-save-preview",
        )
        retained = self.driver.execute(
            """
            return document.querySelector(arguments[1])?.value === arguments[0];
            """,
            [retained_title, title_selector],
        )
        self.check(
            bool(retained),
            "dismissing save review lost the draft title",
        )

        self.navigate(
            "/?orchview=validate#/orchestration/research-build-review",
            ".delivery-preflight",
        )
        self.focus(".preflight-technical > summary")
        self.driver.press("enter")
        self.check(
            bool(
                self.driver.execute(
                    """
                    const summary = document.querySelector(".preflight-technical > summary");
                    return summary?.parentElement.open
                      && document.activeElement === summary;
                    """
                )
            ),
            "preflight Technical details was not keyboard toggleable",
        )

        self.navigate(
            "/?orchview=run#/orchestration/research-build-review",
            ".orch-run-shell",
        )
        self.assert_focus_preserved("#run-refresh", "renderOrchestration")
        live = self.driver.execute(
            """
            const active = document.activeElement;
            const page = window.wrappedJSObject || window;
            const first = page.announceLiveUpdate(
              "accessibility-exam", "ledger-proof", "One material update"
            );
            const text = document.getElementById("live-status").textContent;
            const second = page.announceLiveUpdate(
              "accessibility-exam", "ledger-proof", "Duplicate update"
            );
            return {first, second, text,
              focus: document.activeElement === active};
            """
        )
        self.check(
            live == {
                "first": True,
                "second": False,
                "text": "One material update",
                "focus": True,
            },
            f"live update deduplication/focus contract failed: {live!r}",
        )
        # Use the deterministic pending-decision fixture for the confirmation
        # dialog. The general active run can legitimately have no available act
        # at the instant its saved state is replayed.
        self.navigate(
            "/?orchview=run#/orchestration/decision-visual",
            ".orch-run-shell",
        )
        self.wait(
            lambda: self.selector_exists("[data-run-act]"),
            "pending decision keyboard action",
        )
        self.assert_dialog_round_trip(
            "[data-run-act]",
            ".bounded-preview",
        )

        self.navigate(
            "/?orchview=run&liveconnection=stale#/orchestration/research-build-review",
            ".live-recovery",
        )
        self.assert_focus_preserved("#run-refresh", "renderOrchestration")

        self.navigate(
            "/?proposal=setup-review-fixtures/greenfield.json#/edit/adoption_review",
            ".adoption-review h1",
        )
        self.focus('[data-adoption-mark="accept"]')
        self.driver.press("enter")
        self.wait(
            lambda: self.active_matches('[data-adoption-mark="accept"]')
            and bool(self.driver.execute(
                "return document.querySelector('[data-adoption-mark=accept]')?.getAttribute('aria-pressed') === 'true';"
            )),
            "adoption acceptance mark to restore focus without saving",
        )
        self.focus("#refresh-btn")
        self.driver.press("enter")
        self.wait(
            lambda: self.active_matches("#refresh-btn")
            and self.selector_exists(".adoption-review")
            and bool(self.driver.execute(
                "return document.querySelector('[data-adoption-mark=accept]')?.getAttribute('aria-pressed') === 'true';"
            )),
            "adoption refresh to preserve its browser-memory mark and focus",
        )
        self.focus('[data-adoption-mark="reject"]')
        self.driver.press("enter")
        self.wait(
            lambda: self.active_matches('[data-adoption-mark="reject"]')
            and self.selector_exists("#adoption-correction-form"),
            "adoption correction form to open and restore focus",
        )
        self.focus(".adoption-technical summary")
        self.driver.press("enter")
        self.check(
            self.active_matches(".adoption-technical summary"),
            "adoption technical disclosure moved focus away from its summary",
        )
        self.focus('[data-adoption-mark="abandon"]')
        self.driver.press("enter")
        self.wait(
            lambda: self.active_matches('[data-adoption-mark="abandon"]')
            and not self.selector_exists("#adoption-correction-form")
            and bool(self.driver.execute(
                "return [...document.querySelectorAll('[data-adoption-mark]')].every(item => item.getAttribute('aria-pressed') !== 'true');"
            )),
            "abandoning the browser-memory mark to restore focus and apply nothing",
        )
        self.assertions += 5

    def test_ideation_keyboard_journey(self, label: str) -> None:
        route = f"/?ideationexam={label}#/edit/adoption_review"
        self.navigate(route, ".ideation-flow")
        self.driver.execute(
            "localStorage.removeItem('delivery-workbench.ideation-plan.v1');"
        )
        # Change the query to force a document reload so module-level browser
        # state is rebuilt from the now-empty storage record.
        route = f"/?ideationexam={label}&reset=1#/edit/adoption_review"
        self.navigate(route, ".ideation-idea")
        if label == "narrow":
            self.driver.set_content_zoom(1.5)
            self.wait(
                lambda: int(self.driver.execute(
                    "return document.documentElement.clientWidth;"
                )) <= 390,
                "ideation narrow viewport",
            )
        self.focus('#ideation-idea-form textarea[name="idea"]')
        self.driver.type_text(
            f"Keyboard {label} plan turns requests into a weekly delivery view"
        )
        self.focus('#ideation-idea-form button[type="submit"]')
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists("#ideation-draft-form")
            and self.active_matches("#ideation-draft-title"),
            f"{label} idea to become a focused editable draft",
        )

        phase_title = '[data-draft-path="tracked_content.roadmap.phases.0.title"]'
        self.focus(phase_title)
        self.driver.type_text(" by keyboard")
        self.focus('#ideation-draft-form button[type="submit"]')
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists(".ideation-review")
            and self.active_matches(".ideation-review h1"),
            f"{label} draft to move focus into review",
        )

        # Reject one item, record a correction, and prove Technical details has
        # a keyboard return path to the same disclosure.
        first_reject = '[data-adoption-item-reject="phase-1"]'
        self.focus(first_reject)
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists("#adoption-correction-form")
            and self.active_matches('#adoption-correction-form textarea[name="correction"]'),
            f"{label} item rejection to open the correction form",
        )
        self.driver.type_text("Make the phase title explicit")
        self.focus('#adoption-correction-form button[type="submit"]')
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists(".adoption-review-blocked")
            and self.active_matches('[data-adoption-objection="add"]'),
            f"{label} rejection to block preview with text, not color alone",
        )
        self.focus(".adoption-technical summary")
        self.driver.press("enter")
        self.focus("[data-return-review]")
        self.driver.press("enter")
        self.wait(
            lambda: self.active_matches(".adoption-technical summary")
            and not bool(self.driver.execute(
                "return document.querySelector('.adoption-technical')?.open;"
            )),
            f"{label} Technical details return to its summary",
        )

        self.focus('[data-edit-rejected="phase-1"]')
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists("#ideation-draft-form")
            and self.active_matches("#ideation-draft-title"),
            f"{label} correction to return to the draft",
        )
        self.focus(phase_title)
        self.driver.type_text(" corrected")
        self.focus('#ideation-draft-form button[type="submit"]')
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists(".ideation-review")
            and not self.selector_exists(".adoption-review-blocked"),
            f"{label} corrected rejection to clear the preview block",
        )
        self.focus('[data-adoption-mark="accept"]')
        self.driver.press("enter")
        try:
            self.wait(
                lambda: self.selector_exists("#ideation-preview-button:not([disabled])")
                and self.active_matches('[data-adoption-mark="accept"]'),
                f"{label} review acceptance to enable the one canonical preview",
                timeout=15,
            )
        except ExamFailure:
            # The accept control re-renders after the corrected draft lands;
            # a press that raced that re-render hit a detached node. Accepting
            # is idempotent, so press the live control once more.
            self.focus('[data-adoption-mark="accept"]')
            self.driver.press("enter")
            self.wait(
                lambda: self.selector_exists("#ideation-preview-button:not([disabled])")
                and self.active_matches('[data-adoption-mark="accept"]'),
                f"{label} review acceptance to enable the one canonical preview",
            )

        # Reload keeps the review decisions and the exact position in the flow.
        self.focus("#refresh-btn")
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists("#ideation-preview-button:not([disabled])")
            and self.active_matches("#refresh-btn"),
            f"{label} accepted decisions to survive reload",
        )
        self.focus("#ideation-preview-button")
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists("#ideation-apply")
            and self.active_matches("#ideation-preview-title"),
            f"{label} exact setup preview to receive focus",
        )

        # Editing after preview removes the apply control. The corrected draft
        # must be accepted and previewed again before the one-use apply.
        self.focus("[data-edit-after-preview]")
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists("#ideation-draft-form")
            and not self.selector_exists("#ideation-apply")
            and self.active_matches("#ideation-draft-title"),
            f"{label} preview edit to invalidate the old apply control",
        )
        story_title = '[data-draft-path="tracked_content.roadmap.phases.0.stories.0.title"]'
        self.focus(story_title)
        self.driver.type_text(" revised")
        self.focus('#ideation-draft-form button[type="submit"]')
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists(".ideation-review"),
            f"{label} revised draft review",
        )
        self.focus('[data-adoption-mark="accept"]')
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists("#ideation-preview-button:not([disabled])"),
            f"{label} revised review acceptance",
        )
        self.press_until(
            "#ideation-preview-button",
            lambda: self.selector_exists("#ideation-apply"),
            f"{label} fresh preview after revision",
        )
        self.press_until(
            "#ideation-apply",
            lambda: self.selector_exists(".ideation-applied"),
            f"{label} configuration-only apply to complete",
        )
        self.wait(
            lambda: self.active_matches("#ideation-applied-title"),
            f"{label} applied view to take focus",
        )
        self.audit_page(f"ideation-{label}", label)
        self.assertions += 15

    def test_program_interactions(self) -> None:
        # The program fixture has two roadmap projects. Enter the selector
        # without a query override, choose the other project by keyboard, and
        # prove the choice survives a route change and reload.
        selector_url = self.base + "/#/projects"
        self.driver.navigate(selector_url)
        self.wait(
            lambda: self.selector_exists(".project-selector")
            and bool(self.driver.execute(
                "return document.getElementById('app')?.getAttribute('aria-busy') === 'false';"
            )),
            "project selector to render",
        )
        self.focus(".project-options input:checked")
        self.driver.press("down")
        chosen = self.wait(
            lambda: self.driver.execute(
                "return document.activeElement?.checked ? document.activeElement.value : '';"
            ),
            "arrow-key project choice",
        )
        self.focus("#project-selector-form button.primary")
        self.driver.press("enter")
        self.wait(
            lambda: self.driver.execute(
                """
                return location.hash.startsWith("#/board/")
                  && document.getElementById("project-switcher")?.textContent.includes(arguments[0])
                  && Boolean(document.querySelector(".board"));
                """,
                [chosen],
            ),
            "chosen project to open",
        )
        selected_url = self.base + "/#/health"
        self.driver.navigate(selected_url)
        self.wait(
            lambda: self.selector_exists(".destination-hero h1")
            and bool(self.driver.execute(
                "return document.getElementById('project-switcher')?.textContent.includes(arguments[0]);",
                [chosen],
            )),
            "chosen project to persist across route and reload",
        )
        self.focus("#app details > summary")
        self.driver.press("enter")
        self.driver.press("escape")
        self.check(
            self.active_matches("#app details > summary"),
            "closing Technical details did not return focus to its opener",
        )
        self.driver.navigate(self.base + "/#/board/project-that-is-gone")
        self.wait(
            lambda: self.selector_exists(".project-missing"),
            "unavailable project explanation",
        )
        self.focus(".project-missing a.primary")
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists(".project-selector")
            and self.active_matches("#app h1"),
            "unavailable project route back to the selector",
        )
        self.assertions += 5

        active = self.ids["program_active"]
        revoked = self.ids["program_revoked"]
        certified = self.ids["program_certified"]
        if not all((active, revoked, certified)):
            raise ExamFailure(
                "program suite requires active, revoked, and certified run ids"
            )
        self.driver.set_window(*WIDE)
        self.navigate("/#/live", ".live-mission")
        live_link = f'.live-mission-card[data-live-kind="program"] a[href="#/live/program/{active}"]'
        self.focus(live_link)
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists(".program-room")
            and self.driver.execute(
                "return location.hash === arguments[0];",
                [f"#/live/program/{active}"],
            ),
            "keyboard journey from combined Live list to exact control room",
        )
        self.assert_focus_preserved("#program-refresh", "renderPrograms")
        if not self.selector_exists('[data-program-act="pause"]'):
            raise ExamFailure("active program exposed no keyboard pause control")
        trigger = '[data-program-act="pause"]'
        reason = "Keyboard review only."
        self.focus("#program-control-reason")
        self.driver.type_text(reason)
        self.check(
            bool(
                self.driver.execute(
                    """
                    return document.querySelector(arguments[0])?.value
                      === arguments[1];
                    """,
                    ["#program-control-reason", reason],
                )
            ),
            "program pause reason was not keyboard editable",
        )
        self.focus(trigger)
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists(".bounded-preview")
            and self.active_matches(".bounded-preview"),
            "pause consequence confirmation to open from the keyboard",
        )
        self.focus("#program-act-confirm")
        self.driver.press("enter")
        self.wait(
            lambda: not self.selector_exists(".bounded-preview")
            and bool(self.driver.execute(
                "return /paused/i.test(document.querySelector('.program-room')?.textContent || '');"
            )),
            "keyboard-confirmed pause receipt and resumable state",
        )
        self.assertions += 3

        self.navigate(
            f"/?boundedfocus=receipts#/programs/{revoked}",
            ".program-room",
        )
        self.check(
            bool(
                self.driver.execute(
                    """
                    const text = document.querySelector(".program-room")?.textContent || "";
                    return /revok|stop/i.test(text) && /receipt|ledger/i.test(text);
                    """
                )
            ),
            "revoked program did not expose textual stop and receipt evidence",
        )
        self.navigate(f"/#/programs/{certified}", ".program-room")
        self.check(
            bool(
                self.driver.execute(
                    """
                    const text = document.querySelector(".program-room")?.textContent || "";
                    return /certif|complete|passed/i.test(text);
                    """
                )
            ),
            "certified program did not expose textual completion evidence",
        )


    def test_memory_closed_loop_journey(self) -> None:
        """Record the Phase-35 recall → basis → writeback → reuse journey."""
        if not self.repository:
            raise ExamFailure("closed-loop memory journey repository is missing")
        root = self.repository.resolve()
        library = Path(__file__).resolve().parents[1] / "lib"
        if str(library) not in sys.path:
            sys.path.insert(0, str(library))

        from datetime import datetime, timedelta, timezone
        import subprocess as process

        from dw_pmo import build_run_plan, decision_basis, start_run
        from dw_pmo import knowledge
        from dw_pmo.knowledge_writeback import persist_terminal_writeback
        from dw_pmo.memory_dispatch import persist_recall_slices
        from dw_pmo.memory_read import build_memory_recall_projection
        from dw_pmo.orchestration_run import replay_run, transition_run

        self.driver.set_window(*WIDE)
        self.driver.set_content_zoom(1)

        # 1. Open the workbench before selecting any saved delivery.
        self.navigate("/?project=sample#/board/sample", ".board-overview")
        board = self.driver.execute(
            """
            return {
              heading: document.querySelector('h1')?.textContent || '',
              projectVisible: /sample/i.test(document.querySelector('main')?.textContent || ''),
              memoryOpen: Boolean(document.querySelector('.memory-panel:not([hidden])')),
            };
            """
        )
        self.journey_check(bool(board["heading"]) and bool(board["projectVisible"]),
                           "closed-loop journey did not open the sample workbench")
        self.journey_check(not board["memoryOpen"],
                           "memory opened before the fixture run was selected")
        self.record_memory_step(1, "open-workbench")

        # Start the fixture only after the ordinary accessibility routes have
        # finished, so their live inventories cannot race this recorded journey.
        process.run(
            ["git", "-C", str(root), "add", "-A"], check=True,
            stdout=process.PIPE, stderr=process.PIPE,
        )
        process.run(
            ["git", "-C", str(root), "-c", "core.hooksPath=/dev/null",
             "commit", "-q", "-m", "Memory journey fixture state"], check=True,
            stdout=process.PIPE, stderr=process.PIPE,
        )
        now = datetime.now(timezone.utc).replace(microsecond=0)
        head_sha = process.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
            text=True, stdout=process.PIPE,
        ).stdout.strip()
        seed_lesson = knowledge.EarnedRecordStore(root).append(
            knowledge.LESSON_KIND,
            {
                "claim": "Open story work should freeze bounded recall before dispatch.",
                "locations": knowledge.encode_lesson_locations([{
                    "reference": "SMP-0-02", "status": "resolved",
                    "file": "pm/roadmap/sample/phase-0-smoke-fixture/story-02-open-story.md",
                    "symbol": "SMP-0-02", "line_start": 1, "line_end": 20,
                }]),
                "confidence": "high", "supersedes": "",
            },
            origin_kind="run", origin="run-memory-seed", head_sha=head_sha,
            timestamp=now - timedelta(minutes=1),
        )
        plan = build_run_plan(
            root, "research-build-review", "sample", "SMP-0-02",
            issued_at=now.isoformat(),
            expires_at=(now + timedelta(hours=1)).isoformat(),
        )
        started_projection = start_run(
            root, plan, plan["start_token"], approved=True,
            approved_by="Phase 35 browser journey", now=now,
        )
        self.memory_run = str(started_projection["run_id"])
        run_dir = root / ".git" / "pmo-orchestration" / "runs" / self.memory_run
        recalls, _ = persist_recall_slices(
            run_dir,
            subject=self.memory_run,
            knowledge={
                "index_tree": head_sha,
                "verified_locations": [{
                    "file": "pm/roadmap/sample/phase-0-smoke-fixture/story-02-open-story.md",
                    "symbol": "SMP-0-02",
                }],
                "snippets": [],
                "test_references": ["pmo-roadmap/tests/workbench-ui-smoke.sh"],
                "lessons": [{
                    "record_hash": seed_lesson["record_hash"],
                    "summary": "Freeze bounded recall before dispatching Open story work.",
                    "story_ids": ["SMP-0-02"],
                    "files": ["pm/roadmap/sample/phase-0-smoke-fixture/story-02-open-story.md"],
                    "symbols": ["SMP-0-02"],
                    "tests": ["pmo-roadmap/tests/workbench-ui-smoke.sh"],
                    "confidence": "high", "delivery_state": "confirmed",
                }],
            },
            story_criteria="Open story work freezes bounded recall before dispatch.",
            story_ids=["SMP-0-02"], phase_ids=["0"],
            orchestration_tags=["memory-glass", "closed-loop-exam"],
        )
        memory_ref = recalls["shared"]["recall_id"]
        recorded_decision, _ = decision_basis.record_run_decision_basis(
            root, self.memory_run, started_projection,
            decision_kind="scheduler", basis_type="mechanical",
            outcome="dispatch held behind frozen recall",
            reason_code="recall-frozen-before-agent-output",
            rule_ref="memory-recall-before-dispatch", memory_refs=[memory_ref], now=now,
        )
        self.memory_decision = str(recorded_decision["decision_id"])
        initial_memory = build_memory_recall_projection(root, run=self.memory_run)
        if not initial_memory.get("groups", {}).get("recalled"):
            raise ExamFailure(
                "fixture run froze no recalled knowledge: "
                + json.dumps(initial_memory, sort_keys=True)
            )

        # 2. Select the newly started fixture. It has frozen recall and no agent
        # completion receipt, so this is the observable pre-output boundary.
        run_route = f"/?project=sample#/live/run/{self.memory_run}"
        self.navigate(run_route, f'.orch-run-shell[data-run-id="{self.memory_run}"]')
        started = self.driver.execute(
            """
            const shell = document.querySelector('.orch-run-shell');
            const text = shell?.textContent || '';
            return {id: shell?.dataset.runId || '', active: /active|running/i.test(text),
              completed: /attempts[^]*[1-9][0-9]* complete/i.test(text)};
            """
        )
        self.journey_check(started["id"] == self.memory_run,
                           "fixture run identifier was not visible after start")
        self.journey_check(bool(started["active"]) and not started["completed"],
                           "fixture run was not visibly pre-agent-output")
        self.record_memory_step(2, "fixture-run-started")

        # 3. Inspect the frozen recall before any agent output exists.
        self.press_until(
            '[data-memory-open][data-memory-kind="run"]',
            lambda: self.driver.execute(
                "return Boolean(document.querySelector('.memory-panel:not([hidden])') "
                "&& !document.querySelector('.memory-panel .memory-loading'));"
            ),
            "frozen recall pane to open",
        )
        recalled = self.driver.execute(
            """
            const panel = document.querySelector('.memory-panel:not([hidden])');
            const text = panel?.textContent || '';
            return {card: Boolean(panel?.querySelector('.memory-card[data-memory-group="recalled"]')),
              before: text.includes('Before agent dispatch'),
              writeback: Boolean(panel?.querySelector('.memory-card[data-memory-group="written-back"]'))};
            """
        )
        self.journey_check(bool(recalled["card"]) and bool(recalled["before"]),
                           "frozen recall was not visible before agent output")
        self.journey_check(not recalled["writeback"],
                           "pre-output recall incorrectly showed terminal writeback")
        self.record_memory_step(3, "recall-before-output")

        # 4. Follow the scheduler decision to the exact saved basis and highlight
        # the recalled item it references.
        decision_selector = (
            '.decision-basis-select[data-decision-id="'
            + self.memory_decision + '"]'
        )
        self.press_until(
            decision_selector,
            lambda: self.driver.execute(
                "return document.querySelector(arguments[0])?.getAttribute('aria-pressed') === 'true';",
                [decision_selector],
            ),
            "decision basis detail to open",
        )
        basis = self.driver.execute(
            """
            const selected = document.querySelector(arguments[0]);
            const detail = document.querySelector('.decision-basis-detail');
            return {selected: selected?.getAttribute('aria-pressed') === 'true',
              detail: detail?.textContent || '',
              highlighted: Boolean(document.querySelector('.decision-memory-highlight'))};
            """,
            [decision_selector],
        )
        self.journey_check(bool(basis["selected"]) and "recall-frozen-before-agent-output" in basis["detail"],
                           "decision timeline did not expose its saved basis")
        self.journey_check(bool(basis["highlighted"]),
                           "following the decision did not highlight recalled knowledge")
        self.record_memory_step(4, "decision-basis")

        # 5. End the exact fixture run through the real run transition seam.
        now = datetime.now(timezone.utc).replace(microsecond=0)
        projection = replay_run(root, self.memory_run, now=now)
        finished = transition_run(
            root, self.memory_run, "cancel", str(projection["ledger_head"]),
            reason="Recorded Phase 35 browser journey reached its terminal fixture step.",
            now=now,
        )
        terminal_projection = {
            **finished,
            "terminal_event_ref": str(finished["ledger_head"]),
            "head_sha": process.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                text=True, stdout=process.PIPE,
            ).stdout.strip(),
            "story": {"id": "SMP-0-02"},
            "selected_stories": ["SMP-0-02"],
            "request_history": [], "checkpoints": [], "node_receipts": [],
            "completed_claims": [], "routes": [],
            "budgets": {"max_wall_seconds": {"used": 1, "limit": 3600}},
            "delivery_facts": {
                "head_sha": process.run(
                    ["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                    text=True, stdout=process.PIPE,
                ).stdout.strip(),
                "files_touched": ["pm/roadmap/sample/phase-0-smoke-fixture/story-02-open-story.md"],
            },
        }
        run_dir = root / ".git" / "pmo-orchestration" / "runs" / self.memory_run
        writeback = persist_terminal_writeback(
            root, run_dir, projection=terminal_projection, origin_kind="run", timestamp=now,
        )
        finished_route = f"/?project=sample#/live/run/{self.memory_run}/technical"
        self.navigate(finished_route, f'.orch-run-shell[data-run-id="{self.memory_run}"] .live-technical')
        ended = self.driver.execute(
            """
            const text = document.querySelector('.orch-run-shell')?.textContent || '';
            return {terminal: /cancel|stopped|revok/i.test(text), dispatchStopped: /dispatch stopped/i.test(text)};
            """
        )
        self.journey_check(bool(ended["terminal"]),
                           "finished fixture run did not show a terminal state")
        self.journey_check(bool(ended["dispatchStopped"]),
                           "finished fixture run still appeared dispatchable")
        self.record_memory_step(5, "run-finished")

        # 6. Reopen memory and prove the terminal receipt is rendered separately
        # from what the agent could know before dispatch.
        self.press_until(
            '[data-memory-open][data-memory-kind="run"]',
            lambda: self.driver.execute(
                "return Boolean(document.querySelector('.memory-panel:not([hidden]) .memory-card[data-memory-group="
                "\\\"written-back\\\"]'));"
            ),
            "terminal writeback to render",
        )
        written = self.driver.execute(
            """
            const card = document.querySelector('.memory-card[data-memory-group="written-back"]');
            return {card: Boolean(card), text: card?.textContent || '',
              receipt: document.querySelector('.memory-panel')?.textContent.includes(arguments[0])};
            """,
            [writeback["writeback_id"]],
        )
        self.journey_check(bool(written["card"]) and "after the work reached a completed state" in written["text"],
                           "terminal writeback was not separated in the memory pane")
        self.journey_check(bool(written["receipt"]),
                           "terminal writeback receipt identity was not visible")
        self.record_memory_step(6, "terminal-writeback")

        # 7. Accept one bounded lesson from the completed fixture, then start a
        # related run through the real plan/start seam. Its recall freezes anew.
        head_sha = terminal_projection["head_sha"]
        lesson = knowledge.EarnedRecordStore(root).append(
            knowledge.LESSON_KIND,
            {
                "claim": "Open story work reuses the frozen recall boundary from the prior run.",
                "locations": knowledge.encode_lesson_locations([{
                    "reference": "SMP-0-02", "status": "resolved",
                    "file": "pm/roadmap/sample/phase-0-smoke-fixture/story-02-open-story.md",
                    "symbol": "SMP-0-02", "line_start": 1, "line_end": 20,
                }]),
                "confidence": "high", "supersedes": "",
            },
            origin_kind="run", origin=self.memory_run, head_sha=head_sha, timestamp=now,
        )
        issued = now + timedelta(seconds=1)
        plan = build_run_plan(
            root, "research-build-review", "sample", "SMP-0-02",
            issued_at=issued.isoformat(),
            expires_at=(issued + timedelta(hours=1)).isoformat(),
        )
        related = start_run(
            root, plan, plan["start_token"], approved=True,
            approved_by="Phase 35 browser journey", now=issued,
        )
        related_run = str(related["run_id"])
        persist_recall_slices(
            root / ".git" / "pmo-orchestration" / "runs" / related_run,
            subject=related_run,
            knowledge={
                "index_tree": head_sha,
                "verified_locations": [{
                    "file": "pm/roadmap/sample/phase-0-smoke-fixture/story-02-open-story.md",
                    "symbol": "SMP-0-02",
                }],
                "snippets": [],
                "test_references": ["pmo-roadmap/tests/workbench-ui-smoke.sh"],
                "lessons": [{
                    "record_hash": lesson["record_hash"],
                    "summary": "Reuse the frozen recall boundary learned by the prior run.",
                    "story_ids": ["SMP-0-02"],
                    "files": ["pm/roadmap/sample/phase-0-smoke-fixture/story-02-open-story.md"],
                    "symbols": ["SMP-0-02"],
                    "tests": ["pmo-roadmap/tests/workbench-ui-smoke.sh"],
                    "confidence": "high", "delivery_state": "confirmed",
                }],
            },
            story_criteria="Open story work reuses the prior frozen recall lesson.",
            story_ids=["SMP-0-02"], phase_ids=["0"],
            orchestration_tags=["memory-glass", "related-run"],
        )
        related_route = f"/?project=sample#/live/run/{related_run}"
        self.navigate(related_route, f'.orch-run-shell[data-run-id="{related_run}"]')
        related_started = self.driver.execute(
            """
            const shell = document.querySelector('.orch-run-shell');
            return {id: shell?.dataset.runId || '', text: shell?.textContent || ''};
            """
        )
        self.journey_check(related_started["id"] == related_run,
                           "related fixture run did not start with a distinct identifier")
        self.journey_check("active" in related_started["text"].casefold(),
                           "related fixture run was not visibly active")
        self.record_memory_step(7, "related-run-started")

        # 8. Inspect the related run and find the exact prior lesson in its frozen
        # recall, still advisory and with no writeback of its own.
        self.press_until(
            '[data-memory-open][data-memory-kind="run"]',
            lambda: self.driver.execute(
                "return Boolean(document.querySelector('.memory-panel:not([hidden]) .memory-card[data-memory-group="
                "\\\"recalled\\\"]'));"
            ),
            "related run recall to render",
        )
        related_memory = self.driver.execute(
            """
            return fetch(arguments[0], {cache: 'no-store'}).then((response) => response.json()).then((envelope) => {
              const document = envelope.data || envelope;
              const recalled = document.groups?.recalled || [];
              return {
                prior: recalled.some((item) => item.record_hash === arguments[1]),
                advisory: recalled.every((item) => item.advisory_only === true && item.starts_work === false
                  && item.authorizes === false && item.satisfies_gate === false
                  && item.substitutes_for_evidence === false),
                noWriteback: !(document.groups?.['written-back'] || []).length,
              };
            });
            """,
            [f"/api/runs/{related_run}/memory", lesson["record_hash"]],
        )
        self.journey_check(bool(related_memory["prior"]),
                           "related run did not recall the prior run's lesson")
        self.journey_check(bool(related_memory["advisory"]) and bool(related_memory["noWriteback"]),
                           "related recall was authoritative or already written back")
        self.record_memory_step(8, "prior-lesson-recalled")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--firefox", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument(
        "--suite", choices=("core", "program", "all"), default="all"
    )
    parser.add_argument("--program-active", default="")
    parser.add_argument("--program-revoked", default="")
    parser.add_argument("--program-certified", default="")
    parser.add_argument("--project", default="")
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--memory-run", default="")
    parser.add_argument("--memory-decision", default="")
    parser.add_argument("--capture-dir", type=Path)
    parser.add_argument("--capture-pattern", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.firefox.is_file() or not os.access(args.firefox, os.X_OK):
        print(
            f"workbench-accessibility.py: Firefox is not executable: "
            f"{args.firefox}",
            file=sys.stderr,
        )
        return 2
    driver = Marionette(args.firefox)
    try:
        driver.start()
        exam = WorkbenchExam(
            driver,
            args.base,
            program_active=args.program_active,
            program_revoked=args.program_revoked,
            program_certified=args.program_certified,
            project=args.project,
            repository=args.repository,
            memory_run=args.memory_run,
            memory_decision=args.memory_decision,
            capture_dir=args.capture_dir,
            capture_pattern=args.capture_pattern,
        )
        selected = {
            journey_id
            for journey_id, case in JOURNEY_CASES.items()
            if args.suite == "all" or case["suite"] == args.suite
        }
        for journey_id in JOURNEY_CASES:
            if journey_id in selected:
                exam.audit_journey(journey_id, "narrow")
        if args.suite in {"core", "all"}:
            exam.navigate(
                "/?proposal=setup-review-fixtures/greenfield.json#/edit/adoption_review",
                ".adoption-review h1",
            )
            driver.set_content_zoom(1.5)
            exam.wait(
                lambda: int(driver.execute("return document.documentElement.clientWidth;")) <= 390,
                "adoption review narrow viewport",
            )
            exam.audit_page("adoption-review", "narrow")
            exam.test_ideation_keyboard_journey("narrow")
        driver.set_window(*WIDE)
        driver.set_content_zoom(1)
        exam.wait(
            lambda: driver.execute(
                "return document.documentElement.clientWidth >= 1420;"
            ),
            "wide viewport",
        )
        for journey_id in JOURNEY_CASES:
            if journey_id in selected:
                exam.audit_journey(journey_id, "wide")
        if args.suite in {"core", "all"}:
            exam.navigate(
                "/?proposal=setup-review-fixtures/greenfield.json#/edit/adoption_review",
                ".adoption-review h1",
            )
            exam.audit_page("adoption-review", "wide")
            exam.test_ideation_keyboard_journey("wide")
        if args.suite in {"core", "all"}:
            if args.repository:
                exam.test_memory_closed_loop_journey()
            exam.test_slick_workbench()
            exam.test_core_interactions()
        if args.suite in {"program", "all"}:
            exam.test_program_interactions()
        expected_phase32 = {
            (journey_id, viewport)
            for journey_id in selected.intersection(PHASE32_JOURNEYS)
            for viewport in ("narrow", "wide")
        }
        exam.check(
            exam.phase32_exams == expected_phase32,
            "journey 6-13 exam coverage differed: "
            f"missing={sorted(expected_phase32 - exam.phase32_exams)!r}, "
            f"extra={sorted(exam.phase32_exams - expected_phase32)!r}",
        )
        print(
            "workbench-accessibility.py: ok "
            f"({len(selected)} journeys, {exam.audits} wide/narrow audits, "
            f"{len(exam.phase32_exams)} journey-6-13 keyboard/focus exams, "
            f"{exam.recorded_journey_steps} recorded memory steps / "
            f"{exam.recorded_journey_assertions} recorded memory assertions, "
            f"{exam.assertions} assertions, suite={args.suite})"
        )
        return 0
    except (ExamFailure, OSError, socket.timeout, json.JSONDecodeError) as exc:
        print(f"workbench-accessibility.py: FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        driver.close()


if __name__ == "__main__":
    raise SystemExit(main())
