#!/usr/bin/env python3
"""Firefox keyboard, semantic, focus, and viewport exam for Phase 27.

This intentionally uses Firefox's built-in Marionette endpoint and only the
Python standard library. The UI smoke harness already owns realistic fixture
servers; this exam drives those same pages as a keyboard user and audits their
rendered DOM at both required viewport sizes.
"""

from __future__ import annotations

import argparse
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
    "live-progress": {
        "suite": "core",
        "route": "/?orchview=run#/orchestration/research-build-review",
        "selector": ".orch-run-shell",
    },
    "failed-review-and-repair": {
        "suite": "core",
        "route": "/?orchview=run#/orchestration/repair-visual",
        "selector": ".orch-run-shell",
    },
    "blocked-human-decision": {
        "suite": "core",
        "route": "/?orchview=run#/orchestration/terminal-visual",
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
    ) -> None:
        self.driver = driver
        self.base = base.rstrip("/")
        self.project = project
        self.ids = {
            "program_active": program_active,
            "program_revoked": program_revoked,
            "program_certified": program_certified,
        }
        self.assertions = 0
        self.audits = 0

    def check(self, condition: bool, message: str) -> None:
        self.assertions += 1
        if not condition:
            raise ExamFailure(message)

    def wait(
        self,
        predicate: Callable[[], Any],
        description: str,
        timeout: float = 12,
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
            const element = document.querySelector(arguments[0]);
            if (!element) return false;
            element.focus();
            return document.activeElement === element;
            """,
            [selector],
        )
        self.check(bool(result), f"could not focus {selector}")

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

    def assert_dialog_round_trip(
        self,
        trigger: str,
        dialog: str,
        *,
        timeout: float = 12,
    ) -> None:
        self.focus(trigger)
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists(dialog)
            and self.active_matches(dialog),
            f"{dialog} to open and receive focus",
            timeout,
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
        self.driver.press("enter")
        self.wait(
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
        self.focus(create_trigger)
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists("#board-create-form")
            and self.active_matches(".board-action-panel"),
            "keyboard create panel",
        )
        self.focus('#board-create-form input[name="title"]')
        self.driver.type_text("Keyboard board task")
        self.focus('#board-create-form select[name="status"]')
        self.driver.press("down")
        self.focus('#board-create-form button[type="submit"]')
        self.driver.press("enter")
        self.wait(
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
        self.focus(move_trigger)
        self.driver.press("enter")
        self.wait(lambda: self.selector_exists("#move-form"), "keyboard move panel")
        self.focus('#move-form select[name="status"]')
        self.driver.press("home")
        self.focus('#move-form button[type="submit"]')
        self.driver.press("enter")
        self.wait(
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
        self.focus(park_trigger)
        self.driver.press("enter")
        self.wait(lambda: self.selector_exists("#move-form"), "keyboard park panel")
        self.focus('#move-form button[type="submit"]')
        self.driver.press("enter")
        self.wait(
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
        self.focus(move_trigger)
        self.driver.press("enter")
        self.wait(lambda: self.selector_exists("#move-form"), "done move panel")
        self.focus('#move-form select[name="status"]')
        self.driver.press("end")
        self.focus('#move-form button[type="submit"]')
        self.driver.press("enter")
        self.wait(
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
        self.focus(pause_trigger)
        self.driver.press("enter")
        self.wait(lambda: self.selector_exists("#board-phase-form"), "keyboard pause panel")
        self.focus('#board-phase-form input[name="reason"]')
        self.driver.type_text("Keyboard pause review")
        self.focus('#board-phase-form button[type="submit"]')
        self.driver.press("enter")
        self.wait(lambda: self.selector_exists(".board-preview"), "keyboard pause preview")
        self.focus("#board-apply")
        self.driver.press("enter")
        resume_trigger = '[data-board-phase-action="resume_phase"][data-phase="0"]'
        self.wait(
            lambda: self.selector_exists(resume_trigger),
            "applied pause to refresh as a paused lane",
        )
        self.focus(resume_trigger)
        self.driver.press("enter")
        self.wait(lambda: self.selector_exists("#board-phase-form"), "keyboard resume panel")
        self.focus('#board-phase-form button[type="submit"]')
        self.driver.press("enter")
        self.wait(lambda: self.selector_exists(".board-preview"), "keyboard resume preview")
        self.focus("#board-apply")
        self.driver.press("enter")
        self.wait(
            lambda: self.selector_exists(pause_trigger),
            "applied resume to restore the active lane",
        )
        self.assertions += 14

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
        if self.selector_exists("[data-run-act]"):
            self.assert_dialog_round_trip(
                "[data-run-act]",
                ".bounded-preview",
            )
        else:
            raise ExamFailure("active bounded run exposed no keyboard action")

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
        self.navigate(f"/#/programs/{active}", ".program-room")
        self.assert_focus_preserved("#program-refresh", "renderPrograms")
        if self.selector_exists('[data-program-act="pause"]'):
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
        elif self.selector_exists("[data-program-act]"):
            trigger = "[data-program-act]"
        else:
            raise ExamFailure("active program exposed no keyboard action")
        self.assert_dialog_round_trip(trigger, ".bounded-preview")

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
        if args.suite in {"core", "all"}:
            exam.test_core_interactions()
        if args.suite in {"program", "all"}:
            exam.test_program_interactions()
        print(
            "workbench-accessibility.py: ok "
            f"({len(selected)} journeys, {exam.audits} wide/narrow audits, "
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
