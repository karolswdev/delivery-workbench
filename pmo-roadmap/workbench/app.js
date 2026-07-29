/* Delivery Workbench — hash-routed, API-backed. Reads are live and pure;
 * mutations cross only the guarded editor or deliberate-step boundaries.
 * Every byte of state comes from /api/*, which derives live from the
 * Markdown roadmap through the dw_pmo core. No local persistence. */

"use strict";

const app = document.getElementById("app");
const crumbs = document.getElementById("crumbs");
const refreshTime = document.getElementById("refresh-time");
const footRoot = document.getElementById("foot-root");
const routeStatus = document.getElementById("route-status");
const liveStatus = document.getElementById("live-status");
let presentationCatalog = null;
let semanticId = 0;
const returnFocus = new Map();
const liveAnnouncementKeys = new Map();
const PROJECT_STORAGE_KEY = "delivery-workbench.selected-project";
let projectInventory = null;
let selectedProject = "";
let projectReturnHash = "#/board";

function storedProject() {
  try { return localStorage.getItem(PROJECT_STORAGE_KEY) || ""; }
  catch (_err) { return ""; }
}

function rememberProject(slug) {
  selectedProject = slug || "";
  try {
    if (selectedProject) localStorage.setItem(PROJECT_STORAGE_KEY, selectedProject);
    else localStorage.removeItem(PROJECT_STORAGE_KEY);
  } catch (_err) {
    // Storage can be unavailable in hardened browsers; selection still lasts
    // for this page without changing any repository state.
  }
  const switcher = document.getElementById("project-switcher");
  if (switcher) switcher.textContent = selectedProject
    ? `Project: ${selectedProject}` : "Choose project";
}

async function loadProjects() {
  projectInventory = (await api("/api/projects")).data.projects || [];
  return projectInventory;
}

function projectBySlug(slug) {
  return (projectInventory || []).find((project) => project.slug === slug);
}

function routeProject(parts) {
  if (parts[0] === "p" && parts[1]) return parts[1];
  if (parts[0] === "board" && parts[1]) return parts[1];
  return "";
}

function destinationNav(active, current = "") {
  const groups = {
    work: [["Board", `#/board/${encodeURIComponent(selectedProject)}`], ["Project details", `#/p/${encodeURIComponent(selectedProject)}`]],
    plan: [["Delivery options", "#/program-studio"], ["Roadmap changes", "#/edit"]],
    delivery: [["Delivery plans", "#/orchestration"]],
    live: [["Live delivery", "#/programs"], ["Activity", "#/mc"]],
    health: [["Repository health", "#/health"]],
  };
  const links = groups[active] || [];
  if (links.length < 2) return "";
  return `<nav class="destination-nav" aria-label="${esc(active)} views">${links.map(([label, href], index) => {
    const isCurrent = current ? href.startsWith(current) : index === 0;
    return `<a href="${href}"${isCurrent ? ' aria-current="page"' : ""}>${esc(label)}</a>`;
  }).join("")}</nav>`;
}

function projectSelectorHtml(projects, unavailable = "") {
  const explanation = unavailable
    ? `<p class="project-unavailable"><strong>${esc(unavailable)}</strong> is not available in this repository. Choose an available project; nothing was changed.</p>`
    : "<p>Choose the work you want to see. The choice stays with you as you move around or reload.</p>";
  return `<section class="project-selector" aria-labelledby="project-selector-title">
    <span class="selector-eyebrow">First, choose your work</span>
    <h1 id="project-selector-title">Choose a project</h1>
    ${explanation}
    <form id="project-selector-form">
      <fieldset><legend>Available projects</legend>
        <div class="project-options">${projects.map((project) => `<label>
          <input type="radio" name="project" value="${esc(project.slug)}"${project.slug === selectedProject ? " checked" : ""}>
          <span><strong>${esc(project.slug)}</strong><small>${project.next_story ? `${esc(project.next_story.title)} is next` : "No next work is available"}</small></span>
        </label>`).join("")}</div>
      </fieldset>
      <button class="primary" type="submit">Open this project</button>
    </form>
    <details><summary>Technical details</summary><p>The exact project slug is kept only in this browser. Choosing a project starts no work and changes no files.</p></details>
  </section>`;
}

function wireProjectSelector(returnHash) {
  const form = document.getElementById("project-selector-form");
  if (!form) return;
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const choice = new FormData(form).get("project");
    if (!choice) {
      form.querySelector("fieldset")?.setAttribute("aria-invalid", "true");
      form.querySelector("input")?.focus();
      return;
    }
    rememberProject(String(choice));
    const target = returnHash && !["#/projects", "#/board"].includes(returnHash)
      ? returnHash : `#/board/${encodeURIComponent(selectedProject)}`;
    if (location.hash === target) route({ focusMain: true });
    else location.hash = target;
  });
}

function viewProjectSelector(returnHash = "#/board", unavailable = "") {
  setCrumbs([{ label: "choose project" }]);
  app.innerHTML = projectSelectorHtml(projectInventory || [], unavailable);
  wireProjectSelector(returnHash);
}

function viewUnavailableProject(slug) {
  setCrumbs([{ label: "project unavailable" }]);
  app.innerHTML = `<section class="project-missing"><h1>That project is not available</h1>
    <p><strong>${esc(slug)}</strong> is not in this repository. We did not open another project. Nothing changed.</p>
    <a class="primary" href="#/projects">Choose an available project</a>
    <details><summary>Technical details</summary><p>Requested project slug: <code>${esc(slug)}</code>.</p></details>
  </section>`;
}

const FOCUSABLE_SELECTOR = [
  "a[href]", "button:not([disabled])", "input:not([disabled])",
  "select:not([disabled])", "textarea:not([disabled])",
  "summary", "[tabindex]:not([tabindex='-1'])",
].join(",");
const FOCUS_IDENTITY_ATTRIBUTES = [
  "data-delivery-choice", "data-orch-view", "data-studio-view",
  "data-studio-technical", "data-plan-section", "data-run-act",
  "data-program-act", "data-bounded-read", "data-studio-scenario",
  "data-studio-node", "data-node-id", "data-adoption-mark",
  "data-adoption-objection", "name", "href",
];

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function selectorEscape(value) {
  if (globalThis.CSS?.escape) return CSS.escape(String(value));
  return String(value).replace(/["\\]/g, "\\$&");
}

function focusSelector(element) {
  if (!(element instanceof Element)) return "";
  if (element.id) return `#${selectorEscape(element.id)}`;
  for (const attribute of FOCUS_IDENTITY_ATTRIBUTES) {
    const value = element.getAttribute(attribute);
    if (value !== null && value !== "") {
      return `${element.localName}[${attribute}="${selectorEscape(value)}"]`;
    }
  }
  return "";
}

function captureAppFocus() {
  const active = document.activeElement;
  if (!active || !app.contains(active)) return null;
  const focusable = [...app.querySelectorAll(FOCUSABLE_SELECTOR)];
  return {
    selector: focusSelector(active),
    index: focusable.indexOf(active),
    tag: active.localName,
  };
}

function restoreAppFocus(identity) {
  if (!identity) return false;
  let target = identity.selector
    ? app.querySelector(identity.selector)
    : null;
  if (!target && identity.index >= 0) {
    const focusable = [...app.querySelectorAll(FOCUSABLE_SELECTOR)];
    const candidate = focusable[identity.index];
    if (candidate?.localName === identity.tag) target = candidate;
  }
  if (!target || typeof target.focus !== "function") return false;
  target.focus({ preventScroll: true });
  return document.activeElement === target;
}

function rememberReturnFocus(key, element = document.activeElement) {
  const selector = focusSelector(element);
  if (selector) returnFocus.set(key, selector);
}

function restoreReturnFocus(key, fallback = "") {
  const selector = returnFocus.get(key) || fallback;
  returnFocus.delete(key);
  requestAnimationFrame(() => {
    document.querySelector(selector)?.focus({ preventScroll: true });
  });
}

function focusRegion(selector) {
  requestAnimationFrame(() => {
    const region = document.querySelector(selector);
    if (!region) return;
    if (!region.hasAttribute("tabindex")) region.setAttribute("tabindex", "-1");
    region.focus({ preventScroll: true });
    region.scrollIntoView({ block: "nearest" });
  });
}

function wireDismissibleRegion(selector, close, returnKey, fallback = "") {
  const region = document.querySelector(selector);
  if (!region) return;
  region.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    event.preventDefault();
    close();
    if (returnFocus.has(returnKey)) {
      restoreReturnFocus(returnKey, fallback);
    }
  });
}

function semanticLabel(root, selector, prefix) {
  root.querySelectorAll(selector).forEach((element) => {
    if (element.hasAttribute("aria-label")
        || element.hasAttribute("aria-labelledby")) return;
    const heading = element.querySelector("h1, h2, h3, h4, h5, h6");
    if (heading) {
      if (!heading.id) heading.id = `${prefix}-${++semanticId}`;
      element.setAttribute("aria-labelledby", heading.id);
    }
  });
}

function wireTechnicalFolds(root = app) {
  root.querySelectorAll("details > summary").forEach((summary) => {
    if (!summary.textContent.trim().startsWith("Technical details")
        || summary.dataset.technicalFoldWired === "true") return;
    summary.dataset.technicalFoldWired = "true";
    const details = summary.parentElement;
    details.addEventListener("keydown", (event) => {
      if (event.key !== "Escape" || !details.open) return;
      event.preventDefault();
      details.open = false;
      summary.focus({ preventScroll: true });
    });
    details.addEventListener("toggle", () => {
      if (!details.open && details.contains(document.activeElement)) {
        summary.focus({ preventScroll: true });
      }
    });
  });
}

function enhanceSemantics(root = app) {
  semanticLabel(root, "section", "section-title");
  wireTechnicalFolds(root);
  semanticLabel(root, "form", "form-title");
  root.querySelectorAll("form:not([aria-label]):not([aria-labelledby])").forEach((form) => {
    form.setAttribute(
      "aria-label",
      (form.id || "delivery form").replaceAll("-", " "),
    );
  });
  root.querySelectorAll("table").forEach((table) => {
    if (table.querySelector("caption")
        || table.hasAttribute("aria-label")
        || table.hasAttribute("aria-labelledby")) return;
    const heading = table.closest("section, article, .section, .card")
      ?.querySelector("h1, h2, h3, h4, h5, h6, strong");
    if (heading) {
      if (!heading.id) heading.id = `table-title-${++semanticId}`;
      table.setAttribute("aria-labelledby", heading.id);
    } else {
      table.setAttribute("aria-label", "Delivery details");
    }
  });
  root.querySelectorAll("[role='progressbar']").forEach((meter) => {
    if (!meter.hasAttribute("aria-label")
        && !meter.hasAttribute("aria-labelledby")) {
      meter.setAttribute("aria-label", "Delivery progress");
    }
    if (!meter.hasAttribute("aria-valuetext")) {
      meter.setAttribute(
        "aria-valuetext",
        `${meter.getAttribute("aria-valuenow") || "0"} percent complete`,
      );
    }
  });
  root.querySelectorAll(".guard:not([role]), .state.error:not([role])")
    .forEach((error) => error.setAttribute("role", "alert"));
}

function finishDynamicRender(identity = null) {
  enhanceSemantics(app);
  labelMainRegion();
  restoreAppFocus(identity);
}

function labelMainRegion() {
  const heading = app.querySelector("h1");
  const title = heading?.textContent?.trim() || "Delivery Workbench view";
  if (heading) {
    if (!heading.id) heading.id = `page-title-${++semanticId}`;
    app.setAttribute("aria-labelledby", heading.id);
    app.removeAttribute("aria-label");
  } else {
    app.removeAttribute("aria-labelledby");
    app.setAttribute("aria-label", title);
  }
  return title;
}

function announceRoute() {
  const title = labelMainRegion();
  routeStatus.textContent = `${title} loaded`;
}

function announceLiveUpdate(surface, version, message) {
  const key = String(version || "");
  if (!key || liveAnnouncementKeys.get(surface) === key) return false;
  liveAnnouncementKeys.set(surface, key);
  liveStatus.textContent = message;
  return true;
}

function wireTablist(selector) {
  const tablist = document.querySelector(selector);
  if (!tablist) return;
  const tabs = [...tablist.querySelectorAll("[role='tab']:not([disabled])")];
  tablist.addEventListener("keydown", (event) => {
    const current = event.target.closest?.("[role='tab']");
    const index = tabs.indexOf(current);
    if (index < 0) return;
    const key = event.key;
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(key)) return;
    event.preventDefault();
    const nextIndex = key === "Home" ? 0
      : key === "End" ? tabs.length - 1
        : (index + (key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    const nextSelector = focusSelector(tabs[nextIndex]);
    tabs[nextIndex].click();
    requestAnimationFrame(() => {
      document.querySelector(nextSelector)?.focus({ preventScroll: true });
    });
  });
}

function wireArrowGroup(selector, itemSelector = "button:not([disabled])") {
  const group = document.querySelector(selector);
  if (!group) return;
  group.addEventListener("keydown", (event) => {
    const items = [...group.querySelectorAll(itemSelector)];
    const current = event.target.closest?.(itemSelector);
    const index = items.indexOf(current);
    if (index < 0
        || !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) {
      return;
    }
    event.preventDefault();
    const backwards = event.key === "ArrowLeft" || event.key === "ArrowUp";
    const nextIndex = event.key === "Home" ? 0
      : event.key === "End" ? items.length - 1
        : (index + (backwards ? -1 : 1) + items.length) % items.length;
    items[nextIndex]?.focus();
  });
}

function updatePrimaryNavigation(hash) {
  const surface = hash.split("/").filter(Boolean)[0] || "";
  const activeId = !surface || surface === "board" || surface === "p" ? "work-link"
    : surface === "program-studio" || surface === "edit" ? "plan-link"
      : surface === "orchestration" ? "delivery-link"
        : surface === "programs" || surface === "mc" ? "live-link"
          : surface === "health" ? "health-link" : "";
  document.querySelectorAll(".primary-nav a").forEach((link) => {
    if (link.id === activeId) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  const projectSwitcher = document.getElementById("project-switcher");
  if (surface === "projects") projectSwitcher?.setAttribute("aria-current", "page");
  else projectSwitcher?.removeAttribute("aria-current");
  if (hash === "/") document.querySelector(".brand")?.setAttribute("aria-current", "page");
  else document.querySelector(".brand")?.removeAttribute("aria-current");
}

/* ?snapshot=1 switches to synchronous XHR so headless screenshot tools
 * that capture at the window load event see fully rendered data. Not
 * for interactive use. */
const SNAPSHOT_MODE = new URLSearchParams(location.search).has("snapshot");
const SNAPSHOT_LIVE_STATE = new URLSearchParams(location.search).get("liveconnection");
const LIVE_TECHNICAL_OPEN = new URLSearchParams(location.search).has("livetechnical");
const SNAPSHOT_BOUNDED_FOCUS = new URLSearchParams(location.search).get("boundedfocus");
const SNAPSHOT_BOUNDED_PREVIEW = new URLSearchParams(location.search).get("boundedpreview");
const SNAPSHOT_BOUNDED_ERROR = new URLSearchParams(location.search).get("boundederror");
const ADOPTION_PROPOSAL_FILE = new URLSearchParams(location.search).get("proposal") || "";
const ADOPTION_PROPOSAL_ID = new URLSearchParams(location.search).get("setuppreview") || "";

function syncGet(path) {
  const xhr = new XMLHttpRequest();
  xhr.open("GET", path, false);
  xhr.send();
  return { status: xhr.status, body: JSON.parse(xhr.responseText) };
}

async function postJson(path, payload) {
  if (SNAPSHOT_MODE) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", path, false);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify(payload));
    return { status: xhr.status, body: JSON.parse(xhr.responseText) };
  }
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return { status: res.status, body: await res.json() };
}

function diffHtml(diff) {
  return diff.split("\n").map((line) => {
    const cls = line.startsWith("+") ? "add" : line.startsWith("-") ? "del" : line.startsWith("@@") ? "hunk" : "";
    return cls ? `<span class="${cls}">${esc(line)}</span>` : esc(line);
  }).join("\n");
}

async function api(path) {
  let status;
  let body;
  if (SNAPSHOT_MODE) {
    ({ status, body } = syncGet(path));
  } else {
    const res = await fetch(path, { cache: "no-store" });
    status = res.status;
    body = await res.json();
  }
  if (status >= 400 || body.ok === false) {
    const msg = (body.issues && body.issues[0]) || `API error ${status}`;
    throw new Error(msg);
  }
  refreshTime.textContent = `refreshed ${new Date().toLocaleTimeString()}`;
  return body;
}

async function loadPresentationCatalog() {
  if (presentationCatalog) return presentationCatalog;
  presentationCatalog = (await api("/api/presentation")).data;
  document.querySelectorAll("[data-presentation-copy]").forEach((element) => {
    const key = element.dataset.presentationCopy;
    element.textContent = presentationCatalog.copy?.[key] || key.replaceAll("_", " ");
  });
  return presentationCatalog;
}

function presentationCopy(key) {
  return presentationCatalog?.copy?.[key] || key.replaceAll("_", " ");
}

function productTerm(key) {
  return presentationCatalog?.concepts?.[key]?.preferred || key.replaceAll("_", " ");
}

function setCrumbs(parts) {
  crumbs.innerHTML = parts
    .map((p, i) => (i < parts.length - 1 && p.href
      ? `<a href="${p.href}">${esc(p.label)}</a>`
      : `<span>${esc(p.label)}</span>`))
    .join(" / ");
}

function stateHtml(text, isError) {
  return `<div class="state${isError ? " error" : ""}" role="${isError ? "alert" : "status"}">${esc(text)}</div>`;
}

function badge(text, cls) {
  return `<span class="badge ${cls || esc(String(text))}">${esc(text)}</span>`;
}

function statusCounts(counts) {
  const order = ["in-progress", "ready", "backlog", "blocked", "done"];
  const keys = Object.keys(counts).sort(
    (a, b) => (order.indexOf(a) + 99) - (order.indexOf(b) + 99) || a.localeCompare(b)
  );
  if (!keys.length) return '<span class="badge">no stories</span>';
  return keys.map((k) => badge(`${k} ${counts[k]}`, k)).join(" ");
}

function statusActionHtml(action) {
  const command = Array.isArray(action.command) ? action.command : null;
  const manual = action.kind === "manual" || !command;
  return `<div class="brief-action${manual ? " manual" : ""}" data-action="${esc(action.id)}">
    <div class="brief-action-head">
      <span>next safe action</span>
      <strong>${esc(action.id)}</strong>
      ${action.blocking ? '<span class="badge issue">blocking</span>' : ""}
    </div>
    <div class="brief-reason">${esc(action.reason)}</div>
    ${command ? `<div class="brief-argv" aria-label="command argument vector">
      <span class="brief-argv-label">argv</span>
      ${command.map((arg, index) => `<code data-argv-index="${index}">${esc(arg)}</code>`).join("")}
    </div>` : `<div class="brief-manual"><strong>manual act</strong><span>No command is synthesized for this decision.</span></div>`}
    <div class="brief-readonly">Recommendation only — review the separate deliberate-step boundary below before anything runs.</div>
  </div>`;
}

function stepArgvHtml(argv, label) {
  if (!Array.isArray(argv)) return "";
  return `<div class="brief-argv" aria-label="${esc(label)} argument vector">
    <span class="brief-argv-label">${esc(label)}</span>
    ${argv.map((arg, index) => `<code data-step-argv-index="${index}">${esc(arg)}</code>`).join("")}
  </div>`;
}

function stepControlHtml(step) {
  if (!step.applicable) {
    return `<div class="brief-step-unavailable" data-step-applicable="false">
      <div><strong>deliberate step unavailable</strong><span>No apply control is offered for this recommendation.</span></div>
      <p>${esc(step.refusal || "The current recommendation is not executable through the one-step handrail.")}</p>
    </div>`;
  }
  return `<div class="brief-step-control" data-step-applicable="true">
    <div class="brief-step-intro">
      <div><strong>separate act boundary</strong><span>Review the state-bound lease, then authorize only this one action.</span></div>
      <button type="button" id="step-review">review one deliberate step</button>
    </div>
    <div id="step-confirm"></div>
  </div>`;
}

function stepConfirmationHtml(step) {
  return `<section class="step-confirmation" data-step-token="${esc(step.token)}"
      role="dialog" aria-modal="false" aria-labelledby="step-confirm-title" tabindex="-1">
    <div class="step-confirm-head"><span>confirmation</span><strong id="step-confirm-title">${esc(step.action.id)}</strong>${badge("one child maximum", "warn")}</div>
    <p>${esc(step.action.reason)}</p>
    <div class="step-token"><span>state token</span><code>${esc(step.token)}</code></div>
    ${stepArgvHtml(step.action.command, "authorized argv")}
    ${stepArgvHtml(step.apply_command, "CLI fallback")}
    <div class="step-confirm-actions">
      <button type="button" id="step-apply">apply this one step</button>
      <button type="button" id="step-cancel">cancel</button>
    </div>
    <div class="brief-readonly">One POST, at most one child, then a fresh briefing. No automatic continuation.</div>
  </section>`;
}

function stepNoticeHtml(notice) {
  if (!notice) return "";
  const result = notice.result;
  const after = result && result.after ? result.after.action_id : null;
  const streams = result && result.output
    ? [result.output.stdout, result.output.stderr].filter(Boolean).join("\n") : "";
  return `<div class="brief-step-notice ${esc(notice.kind)}" role="status">
    <strong>${esc(notice.title)}</strong><span>${esc(notice.detail)}</span>
    ${after ? `<span>Stopped. Fresh next action: <code>${esc(after)}</code>.</span>` : ""}
    ${streams ? `<pre>${esc(streams)}</pre>` : ""}
  </div>`;
}

async function applyReviewedStep(step, button) {
  button.disabled = true;
  button.textContent = "applying one step…";
  try {
    const { status, body } = await postJson("/api/step/apply", {
      project: step.project,
      expect: step.token,
    });
    const result = body.data && body.data.kind === "delivery-workbench-step-result"
      ? body.data : null;
    if (status === 409) {
      await viewBoard(selectedProject, {
        kind: "stale",
        title: "stale confirmation refused — nothing started",
        detail: result ? result.reason : ((body.issues && body.issues[0]) || "Refresh and review the new lease."),
        result,
      });
      return;
    }
    if (status >= 400 || !result) {
      await viewBoard(selectedProject, {
        kind: "failed",
        title: "step request failed — nothing else was attempted",
        detail: (body.issues && body.issues[0]) || `HTTP ${status}`,
        result,
      });
      return;
    }
    const succeeded = result.outcome === "succeeded";
    await viewBoard(selectedProject, {
      kind: succeeded ? "succeeded" : "failed",
      title: succeeded ? "one deliberate step applied" : `step ${result.outcome}`,
      detail: result.reason || `Child exit ${result.exit_code}; started=${result.started}.`,
      result,
    });
  } catch (err) {
    await viewBoard(selectedProject, {
      kind: "failed",
      title: "step request failed",
      detail: err.message,
      result: null,
    });
  }
}

function wireStepControl(step) {
  const review = document.getElementById("step-review");
  if (!review || !step.applicable) return;
  const openConfirmation = () => {
    const slot = document.getElementById("step-confirm");
    if (!slot) return;
    rememberReturnFocus("step-confirm", review);
    slot.innerHTML = stepConfirmationHtml(step);
    review.disabled = true;
    enhanceSemantics(slot);
    document.getElementById("step-apply").addEventListener("click", (event) => {
      applyReviewedStep(step, event.currentTarget);
    });
    const close = () => {
      slot.innerHTML = "";
      review.disabled = false;
      restoreReturnFocus("step-confirm", "#step-review");
    };
    document.getElementById("step-cancel").addEventListener("click", close);
    wireDismissibleRegion(".step-confirmation", close, "step-confirm", "#step-review");
    focusRegion(".step-confirmation");
  };
  review.addEventListener("click", openConfirmation);
  if (SNAPSHOT_MODE && new URLSearchParams(location.search).has("confirmstep")) {
    openConfirmation();
  }
}

function statusPanel(status, step, notice) {
  const repo = status.repository;
  const roadmap = status.roadmap;
  const changes = repo.changes;
  const action = step.action || status.next_action || {
    id: "none", kind: "manual", blocking: false,
    reason: "The briefing has no action to review.", command: null,
  };
  const manual = action.kind === "manual" || !action.command;
  const project = roadmap.selected_project || (roadmap.selection_required ? "selection required" : "none");
  const workspace = repo.clean
    ? "clean"
    : `${changes.staged.count} staged · ${changes.unstaged.count} unstaged · ${changes.untracked.count} untracked`;
  const projectLink = roadmap.selected_project
    ? `<a href="#/p/${encodeURIComponent(roadmap.selected_project)}">project</a>
       <a href="#/board/${encodeURIComponent(roadmap.selected_project)}">board</a>`
    : "";
  return `<section id="status-panel"
      class="status-panel verdict-${esc(status.verdict)}${manual ? " is-manual" : ""}${step.applicable ? "" : " is-prohibited"}"
      data-verdict="${esc(status.verdict)}" data-next-action="${esc(action.id)}"
      data-step-applicable="${step.applicable ? "true" : "false"}">
    <div class="brief-head">
      <div>
        <div class="brief-eyebrow">repository briefing</div>
        <div class="brief-verdict">${esc(status.verdict)}</div>
      </div>
      <div class="brief-summary">${esc(status.summary)}</div>
    </div>
    <div class="brief-facts">
      <div><span>project</span><strong>${esc(project)}</strong></div>
      <div><span>workspace</span><strong>${esc(workspace)}</strong></div>
      <div><span>contract</span><strong>${esc(repo.contract.state)}</strong></div>
      <div><span>gate</span><strong>${esc(repo.gate.state)}</strong></div>
    </div>
    ${stepNoticeHtml(notice)}
    ${statusActionHtml(action)}
    ${stepControlHtml(step)}
    <nav class="brief-specialists" aria-label="specialist Delivery Workbench views">
      <span>inspect deeper</span>${projectLink}<a href="#/health">health</a><a href="#/mc">mission control</a>
    </nav>
  </section>`;
}

function setupChoice(setup, id) {
  return (setup.choices || []).find((choice) => choice.id === id);
}

function arrivalPanel(setup, status, step, notice, presentation) {
  const scope = setup.delivery_scope || {};
  const work = scope.current_work;
  const ordinary = setupChoice(setup, "roadmap");
  const presentedWork = (presentation.sections || []).find((section) => section.id === "work");
  const nextStep = presentation.next_step || {};
  const technicalOpen = Boolean(
    notice || (SNAPSHOT_MODE && new URLSearchParams(location.search).has("confirmstep"))
  );
  const workLine = work
    ? `<div class="arrival-work"><span>${esc(presentationCopy("current_work"))}</span><div><strong>${esc(work.title)}</strong><small>${esc(work.story_id)} · ${esc(work.status)}</small></div></div>`
    : `<div class="arrival-work"><span>${esc(presentationCopy("current_work"))}</span><div><strong>${esc(presentedWork?.value || "No work is currently actionable")}</strong><small>${esc(presentationCopy("check_readiness"))} for the affected ${esc(productTerm("decision"))}.</small></div></div>`;
  return `<section class="arrival-panel readiness-${esc(setup.readiness)}" aria-labelledby="arrival-title">
    <div class="arrival-hero">
      <div><span class="arrival-eyebrow">${setup.healthy ? "healthy ordinary delivery" : "delivery needs attention"}</span>
        <h1 id="arrival-title">${esc(presentation.title)}</h1><p>${esc(presentation.summary)}</p></div>
      ${badge(setup.readiness, setup.readiness === "ready" ? "ok" : "issue")}
    </div>
    ${workLine}
    <div class="arrival-next"><span>${esc(productTerm("next_step"))}</span><strong>${esc(nextStep.label || presentationCopy("check_readiness"))}</strong><p>${esc(nextStep.summary || "")}</p></div>
    <div class="arrival-actions">
      ${ordinary?.available && work ? `<a class="primary" href="${esc(ordinary.route)}">${esc(presentationCopy("open_current_work"))}</a>` : `<a class="primary" href="#/health">${esc(presentationCopy("check_readiness"))}</a>`}
      <a href="#/program-studio">${esc(presentationCopy("review_delivery_options"))}</a>
      <span>Optional coordination is not required.</span>
    </div>
    <details class="arrival-technical"${technicalOpen ? " open" : ""}>
      <summary>${esc(presentationCopy("technical_details"))}</summary>
      <p>Exact repository, contract, gate, command, and one-step facts remain available here.</p>
      ${statusPanel(status, step, notice)}
    </details>
  </section>`;
}

/* ── mission control (WLA-15-01): the read-only belt ──────────────
 * The workbench is the fourth consumer of the mission-control
 * substrate (feed + sessions + events), read-only by charter — the
 * picture without the hands. A single-flight 10s poll keeps it live
 * while the view is open; leaving the view stops the poll. */

let mcPoll = null;
let mcInFlight = false;

function stopMcPoll() {
  if (mcPoll) { clearInterval(mcPoll); mcPoll = null; }
}

function mcPin(s) {
  return `<span class="mc-pin${s.awaiting_response ? " awaiting" : ""}${s.stale ? " stale" : ""}"
    title="${s.awaiting_response ? "A decision is waiting" : "Team activity"}${s.stale ? " (update may be stale)" : ""}">${s.awaiting_response ? "🙋" : "🤖"}${esc(s.agent)}</span>`;
}

function mcBelt(project, pins) {
  const current = project.current_phase;
  const beltStories = current
    ? project.stories.filter((s) => s.phase === current.number) : [];
  const nextId = project.next_story ? project.next_story.story_id : null;
  return `
    <div class="mc-project">
      <div class="mc-phases">
        <span class="mc-slug">${esc(project.slug)}</span>
        ${project.phases.map((ph) => `
          <span class="mc-phase${ph.status === "closed" ? " closed" : ""}${current && ph.number === current.number ? " current" : ""}"
                title="${esc(ph.title)} — ${ph.stories_done}/${ph.stories_total}">${ph.number}</span>`).join("")}
        ${project.warnings ? `<span class="mc-warn">⚠ ${project.warnings}</span>` : ""}
      </div>
      <div class="mc-belt">
        ${beltStories.map((s) => `
          <span class="mc-story st-${esc(s.status)}${s.story_id === nextId ? " next" : ""}"
                title="${esc(s.title)} [${esc(s.status)}]${s.evidence_exists ? " ·evidence" : ""}">
            <a href="#/p/${encodeURIComponent(project.slug)}/s/${encodeURIComponent(s.story_id)}">${esc(s.story_id)}</a>${s.evidence_exists ? " ✓" : ""}${(pins[s.story_id] || []).map(mcPin).join("")}
          </span>`).join("")}
      </div>
    </div>`;
}

function mcOffBelt(doc, offBelt) {
  if (!doc || doc.registry !== "ok") {
    return `<div class="sub">Team activity is unavailable.</div>`;
  }
  if (!offBelt.length) return `<div class="sub">Every live team activity is matched to current work.</div>`;
  return offBelt.map((s) => {
    const where = s.correlation === "ambiguous" && s.stories.length
      ? `ambiguous: ${s.stories.map((st) => st.story_id).join(", ")}`
      : s.correlation.replace(/_/g, " ");
    return `<div class="mc-session${s.awaiting_response ? " awaiting" : ""}${s.stale ? " stale" : ""}">
      <strong>${esc(s.agent)}</strong> — ${esc(where)}
      ${s.awaiting_response ? badge("awaiting a response", "warn") : ""}
      ${s.stale ? badge("stale") : ""}
      <details><summary>Technical details</summary><code>${esc(s.key)}</code></details>
    </div>`;
  }).join("");
}

function mcEvents(events) {
  if (!events.length) return `<div class="sub">no rail events yet</div>`;
  return `<div class="mc-ticker">` + events.slice().reverse().map((e) => {
    const detail = Object.entries(e.detail || {})
      .filter(([, v]) => v !== null && v !== undefined)
      .map(([k, v]) => `${k}=${v}`).join(" ");
    const refusal = e.event === "gate_refusal";
    return `<div class="mc-event${refusal ? " refusal" : ""}">
      ${refusal ? "✕ " : ""}${esc(e.ts || "?")}  ${esc(e.event || "?")}${e.story ? `  ${esc(e.story)}` : ""}${detail ? `  ${esc(detail)}` : ""}
    </div>`;
  }).join("") + `</div>`;
}

async function loadMissionControl() {
  if (mcInFlight) return; // single-flight: a slow poll skips ticks
  mcInFlight = true;
  const focus = captureAppFocus();
  try {
    const body = await api("/api/missioncontrol");
    const data = body.data;
    const el = document.getElementById("mc-root");
    if (!el) { stopMcPoll(); return; } // view left; stop polling
    el.innerHTML = `${destinationNav("live", "#/mc")}
      <div class="section"><h1>Current activity</h1><p>See what people and deliveries are doing now. Reading this page starts nothing.</p><p class="canonical-next"><strong>Next step:</strong> Open the current work that needs your attention.</p><h2>Current phase work</h2>
        ${data.feed.projects.filter((project) => !selectedProject || project.slug === selectedProject).map((p) => mcBelt(p, data.pins || {})).join("") || stateHtml("No current work is available.")}
      </div>
      <div class="section"><h2>Team activity not matched to work</h2>${mcOffBelt(data.sessions, data.off_belt || [])}</div>
      <details class="section"><summary>Technical details</summary><h2>Exact saved events</h2>${mcEvents(data.events)}</details>
      <div class="sub">Reading activity starts no work and changes no files.</div>`;
    enhanceSemantics(el);
    restoreAppFocus(focus);
    const latest = data.events?.[data.events.length - 1];
    const version = `${data.events?.length || 0}:${latest?.ts || ""}:${latest?.event || ""}`;
    if (liveAnnouncementKeys.has("mission-control")) {
      announceLiveUpdate(
        "mission-control",
        version,
        "Activity changed. Use Check for updates or review Current activity.",
      );
    } else {
      liveAnnouncementKeys.set("mission-control", version);
    }
  } finally {
    mcInFlight = false;
  }
}

async function viewMissionControl() {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "activity" }]);
  app.innerHTML = `<div id="mc-root">${stateHtml("Loading current activity…")}</div>`;
  await loadMissionControl();
  mcPoll = setInterval(() => { loadMissionControl().catch(() => {}); }, 10000);
}

/* ── views ─────────────────────────────────────────────────────────── */

async function viewOverview(notice = null) {
  setCrumbs([{ label: "overview" }]);
  const projectQuery = selectedProject
    ? `?project=${encodeURIComponent(selectedProject)}` : "";
  const [statusBody, stepBody, body, setupBody, presentationBody] = await Promise.all([
    api(`/api/status${projectQuery}`), api(`/api/step${projectQuery}`), api("/api/projects"),
    api(`/api/delivery-setup${projectQuery}`), api(`/api/presentation/status${projectQuery}`),
  ]);
  const projects = body.data.projects;
  const step = stepBody.data;
  const briefing = arrivalPanel(
    setupBody.data, statusBody.data, step, notice, presentationBody.data,
  );
  if (!projects.length) {
    app.innerHTML = briefing + stateHtml("No roadmap projects found under pm/roadmap/. Scaffold one with `dw phase create` or `dw adopt`.");
    wireStepControl(step);
    return;
  }
  app.innerHTML = briefing + `<div class="grid">` + projects.map((p) => `
    <div class="card">
      <h3><a href="#/p/${encodeURIComponent(p.slug)}">${esc(p.slug)}</a>
        <span class="badge">${esc(p.prefix)}</span></h3>
      <div class="sub">${esc(p.path)}</div>
      <div class="stats">
        <span>phases <b>${p.phase_count}</b></span>
        <span>active <b>${p.active_phase_count}</b></span>
        <span>${p.issue_count ? badge(`${p.issue_count} issue${p.issue_count > 1 ? "s" : ""}`, "issue") : badge("checks ok", "ok")}</span>
        <span>${p.warning_count ? badge(`${p.warning_count} warning${p.warning_count > 1 ? "s" : ""}`, "warn") : ""}</span>
      </div>
      <div class="stats" style="margin-top:6px">${statusCounts(p.story_status_counts)}</div>
      ${p.next_story ? `
        <div class="next"><span class="lbl">next</span>
          <a href="#/p/${encodeURIComponent(p.slug)}/s/${encodeURIComponent(p.next_story.story_id)}">
            <code>${esc(p.next_story.story_id)}</code></a>
          ${esc(p.next_story.title)} ${badge(p.next_story.status)}
        </div>` : `<div class="next"><span class="lbl">next</span> nothing actionable</div>`}
    </div>`).join("") + `</div>`;
  wireStepControl(step);
}

async function viewProject(slug) {
  setCrumbs([{ label: "overview", href: "#/" }, { label: slug }]);
  const body = await api(`/api/projects/${encodeURIComponent(slug)}`);
  const p = body.data;
  const phases = p.phases.map((ph) => {
    const counts = {};
    ph.stories.forEach((s) => { counts[s.status] = (counts[s.status] || 0) + 1; });
    const evidenced = ph.stories.filter((s) => s.evidence_exists).length;
    return `<tr>
      <td><a href="#/p/${encodeURIComponent(slug)}/ph/${ph.number}"><code>${ph.number}</code> ${esc(ph.slug)}</a></td>
      <td>${ph.active ? badge("active", "in-progress") : badge("closed", "done")}</td>
      <td>${statusCounts(counts)}</td>
      <td>${evidenced}/${ph.stories.length}</td>
      <td>${ph.final_summary_exists
        ? `<a href="#/f/${encodeURIComponent(ph.final_summary)}">${badge("summary", "ok")}</a>` : "—"}</td>
    </tr>`;
  }).join("");
  app.innerHTML = `${destinationNav("work", "#/p")}
    <header class="destination-hero"><span>Project</span><h1>${esc(slug)}</h1><p>Review the next work and the plan around it.</p></header>
    ${p.next_story ? `<div class="next"><span class="lbl">next</span>
      <a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(p.next_story.story_id)}">
        <code>${esc(p.next_story.story_id)}</code></a> ${esc(p.next_story.title)} ${badge(p.next_story.status)}</div>` : ""}
    <div class="section"><h2>Phases <a class="badge" href="#/board/${encodeURIComponent(slug)}">board view</a></h2>
      <div class="tblwrap"><table class="tbl">
        <tr><th>Phase</th><th>State</th><th>Stories</th><th>Evidence</th><th>Summary</th></tr>
        ${phases || '<tr><td colspan="5">no phases yet</td></tr>'}
      </table></div></div>
    ${p.issues.length ? `<div class="guard">Roadmap changes are blocked — <a href="#/health">${p.issues.length} readiness issue${p.issues.length === 1 ? "" : "s"}</a> must be resolved first.</div>
    <div class="section"><h2>Readiness blockers (<a href="#/health">open readiness</a>)</h2>
      <ul class="plain">${p.issues.map((i) => `<li class="issue">${esc(i)}</li>`).join("")}</ul></div>` : ""}
    ${p.warnings.length ? `<div class="section"><h2>Warnings</h2>
      <ul class="plain">${p.warnings.map((w) => `<li class="warn">${esc(w)}</li>`).join("")}</ul></div>` : ""}
    <div class="section"><h2>Supplemental canon</h2>
      <ul class="plain">${p.supplemental_canon.length ? p.supplemental_canon.map((c) =>
        `<li><a href="#/f/${encodeURIComponent(c.path)}">${esc(c.path)}</a>
         <code>${esc(c.kind)} · ${esc(c.scope)}</code></li>`).join("")
        : "<li>none</li>"}</ul></div>`;
}

async function viewPhase(slug, number) {
  setCrumbs([{ label: "overview", href: "#/" },
    { label: slug, href: `#/p/${encodeURIComponent(slug)}` },
    { label: `phase ${number}` }]);
  const body = await api(`/api/projects/${encodeURIComponent(slug)}/phases/${encodeURIComponent(number)}`);
  const ph = body.data;
  const rows = ph.stories.map((s) => `<tr>
    <td><a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(s.story_id)}"><code>${esc(s.story_id)}</code></a></td>
    <td>${esc(s.title)}</td>
    <td>${badge(s.status)}${s.header_status && s.header_status !== s.status ? " " + badge("header: " + s.header_status, "issue") : ""}</td>
    <td>${s.evidence_exists ? badge("evidence", "ok") : badge("no evidence", s.status === "done" ? "issue" : "")}</td>
    <td><a href="#/f/${encodeURIComponent(s.story_path)}"><code>story</code></a>${s.evidence_exists
      ? ` · <a href="#/f/${encodeURIComponent(s.evidence_path)}"><code>evidence</code></a>` : ""}
      · <a href="#/p/${encodeURIComponent(slug)}/t/${encodeURIComponent(s.story_id)}"><code>trace</code></a></td>
  </tr>`).join("");
  app.innerHTML = `
    <div class="meta">
      <div class="kv"><div class="k">status file</div><div class="v"><a href="#/f/${encodeURIComponent(ph.status_file)}">${esc(ph.status_file)}</a></div></div>
      <div class="kv"><div class="k">state</div><div class="v">${ph.active ? "active" : "closed"}</div></div>
      <div class="kv"><div class="k">final summary</div><div class="v">${ph.final_summary_exists
        ? `<a href="#/f/${encodeURIComponent(ph.final_summary)}">${esc(ph.final_summary)}</a>` : "not written"}</div></div>
    </div>
    <div class="section"><h2>Stories (normalized from current-phase-status.md)</h2>
      <div class="tblwrap"><table class="tbl">
        <tr><th>ID</th><th>Story</th><th>Status</th><th>Evidence</th><th>Source</th></tr>
        ${rows || '<tr><td colspan="5">no stories yet</td></tr>'}
      </table></div></div>
    <div class="section"><h2>Recent commits (phase trace)</h2>
      <div id="phase-events" class="state">Loading…</div></div>
    ${ph.final_summary_content ? `<div class="section"><h2>Final summary</h2>
      <pre class="src">${esc(ph.final_summary_content)}</pre></div>` : ""}`;
  api(`/api/projects/${encodeURIComponent(slug)}/phases/${encodeURIComponent(number)}/events`).then((ev) => {
    const rows = ev.data.events.map((c) => `<tr>
      <td><code>${esc(c.date)}</code></td><td>${esc(c.subject)}
        ${c.pmo_story ? " " + badge(c.pmo_story, "ok") : ""}
        ${c.contract_digest ? ` <span class="badge" title="${esc(c.contract_digest)}">digest</span>` : ""}</td>
      <td><code>${esc(String(c.sha).slice(0, 9))}</code></td></tr>`).join("");
    document.getElementById("phase-events").outerHTML = rows
      ? `<div class="tblwrap"><table class="tbl"><tr><th>Date</th><th>Commit</th><th>SHA</th></tr>${rows}</table></div>`
      : `<div class="state">no commits touch this phase directory yet</div>`;
  }).catch(() => {
    const el = document.getElementById("phase-events");
    if (el) el.textContent = "phase commits unavailable (no git history)";
  });
}

async function viewStory(slug, storyId) {
  setCrumbs([{ label: "overview", href: "#/" },
    { label: slug, href: `#/p/${encodeURIComponent(slug)}` },
    { label: storyId }]);
  const body = await api(`/api/projects/${encodeURIComponent(slug)}/stories/${encodeURIComponent(storyId)}`);
  const s = body.data;
  app.innerHTML = `
    <div class="meta">
      <div class="kv"><div class="k">story</div><div class="v">${esc(s.story_id)} — ${esc(s.title)}</div></div>
      <div class="kv"><div class="k">status</div><div class="v">${badge(s.status)}${s.header_status && s.header_status !== s.status ? " " + badge("header: " + s.header_status, "issue") : ""}</div></div>
      <div class="kv"><div class="k">phase</div><div class="v"><a href="#/p/${encodeURIComponent(slug)}/ph/${s.phase_number}">phase ${s.phase_number}</a></div></div>
      <div class="kv"><div class="k">evidence</div><div class="v">${s.evidence_exists ? esc(s.evidence_path) : "none"}</div></div>
      <div class="kv"><div class="k">trace</div><div class="v"><a href="#/p/${encodeURIComponent(slug)}/t/${encodeURIComponent(s.story_id)}">intent → proof timeline</a></div></div>
    </div>
    <div class="section pair">
      <div><h2>story · <code>${esc(s.story_path)}</code></h2>
        <pre class="src">${esc(s.story_markdown || "(missing story file)")}</pre></div>
      <div><h2>evidence · <code>${esc(s.evidence_path || "—")}</code></h2>
        <pre class="src">${esc(s.evidence_markdown || "(no evidence file yet)")}</pre></div>
    </div>`;
}

async function viewFile(path) {
  setCrumbs([{ label: "overview", href: "#/" }, { label: path }]);
  const body = await api(`/api/file?path=${encodeURIComponent(path)}`);
  app.innerHTML = `
    <div class="section"><h2>source · <code>${esc(body.data.path)}</code> (read-only)</h2>
      <pre class="src">${esc(body.data.content)}</pre></div>`;
}


const CATEGORY_LABELS = {
  "project": "Project pointers",
  "phase": "Phases",
  "story-evidence": "Stories & evidence",
  "hook-runtime": "Hooks & runtime",
  "supplemental-canon": "Supplemental canon",
};

function healthItem(item) {
  const kindCls = item.kind === "stale-pointer" ? "issue" : (item.severity === "error" ? "issue" : "warn");
  const folders = item.phase_folders
    ? `<div class="why">phase folders: ${item.phase_folders.map((f) => `<code>${esc(f)}</code>`).join(", ")}</div>` : "";
  return `<div class="hitem">
    ${badge(item.severity === "error" ? "blocker" : "attention", item.severity === "error" ? "issue" : "warn")}
    <span class="msg">${esc(item.message)}</span>
    ${item.explanation ? `<div class="why">${esc(item.explanation)}</div>` : ""}
    <details><summary>Technical details</summary>${badge(item.kind, kindCls)}
      ${item.path ? `<a href="#/f/${encodeURIComponent(item.path)}"><code>${esc(item.path)}</code></a>` : ""}
      ${folders}</details>
  </div>`;
}

async function viewHealth() {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "health" }]);
  const body = await api("/api/health");
  const h = body.data;
  const sections = [];
  const shownProjects = selectedProject
    ? h.projects.filter((project) => project.slug === selectedProject)
    : h.projects;
  for (const proj of shownProjects) {
    const byCat = {};
    proj.issues.concat(proj.warnings).forEach((item) => {
      (byCat[item.category] = byCat[item.category] || []).push(item);
    });
    const cats = Object.keys(byCat).map((cat) => `
      <div class="section"><h2>${esc(proj.slug)} · ${esc(CATEGORY_LABELS[cat] || cat)} (${byCat[cat].length})</h2>
        ${byCat[cat].map(healthItem).join("")}</div>`).join("");
    sections.push(cats || `<div class="section"><h2>${esc(proj.slug)}</h2>
      <div class="guard ok">Delivery is ready; no readiness blocker was found.</div></div>`);
  }
  const hook = h.hook_snapshot;
  const hookRows = [
    ["pre-commit installed", hook.pre_commit_exists],
    ["post-commit installed", hook.post_commit_exists],
    ["config seam (pre-commit.config)", hook.has_config_seam],
    ["local rule seam (pre-commit.local)", hook.has_local_seam],
    ["work-log capture", hook.has_work_log_capture],
  ].map(([k, v]) => `<div class="hitem">${badge(v ? "ok" : "missing", v ? "ok" : "issue")}<span class="msg">${esc(k)}</span></div>`).join("");
  const issueCount = shownProjects.reduce((total, project) => total + project.issues.length, 0);
  app.innerHTML = `${destinationNav("health", "#/health")}
    <header class="destination-hero"><span>Health</span><h1>Is this project ready?</h1><p>See what is ready and what needs attention before you change the plan.</p></header>
    <div class="guard ${issueCount === 0 ? "ok" : ""}">${issueCount === 0
      ? "This project is ready. Your next step is to return to current work."
      : `Resolve ${issueCount} health issue${issueCount === 1 ? "" : "s"} in this project before changing its plan.`}</div>
    <a class="primary canonical-primary" href="#/board/${encodeURIComponent(selectedProject)}">Return to current work</a>
    ${sections.join("")}
    <details class="section"><summary>Technical details</summary>
      <h2>Repository setup checks</h2>${hookRows}
      ${h.hook_explanations.length ? `<ul class="plain">${h.hook_explanations.map((e) => `<li class="warn">${esc(e)}</li>`).join("")}</ul>` : ""}
      <h2>Work-log configuration (read-only)</h2>
        <div class="meta">
          <div class="kv"><div class="k">enabled</div><div class="v">${esc(h.work_log_config.enabled)}</div></div>
          <div class="kv"><div class="k">directory</div><div class="v">${esc(h.work_log_config.dir)}</div></div>
          <div class="kv"><div class="k">project slug</div><div class="v">${esc(h.work_log_config.project_slug)}</div></div>
          <div class="kv"><div class="k">exclude regex</div><div class="v">${esc(h.work_log_config.exclude_regex)}</div></div>
        </div>
      <h2>Exact readiness check (copyable)</h2>
        <div class="copybar"><button id="copy-check" type="button">copy</button></div>
        <pre class="src" id="check-output">${esc(h.check_output)}</pre>
    </details>`;
  document.getElementById("copy-check").addEventListener("click", () => {
    navigator.clipboard.writeText(document.getElementById("check-output").textContent);
  });
}


const HOP_LABELS = {
  readme: "project README",
  phase_status: "phase status",
  story: "story",
  evidence: "evidence",
  final_summary: "final summary",
};

let traceSortAsc = false;

async function viewTrace(slug, storyId) {
  setCrumbs([{ label: "overview", href: "#/" },
    { label: slug, href: `#/p/${encodeURIComponent(slug)}` },
    { label: storyId, href: `#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(storyId)}` },
    { label: "trace" }]);
  const apiPath = `/api/projects/${encodeURIComponent(slug)}/trace/${encodeURIComponent(storyId)}`;
  const body = await api(apiPath);
  const tl = body.data;
  const chain = tl.chain.map((hop) => `
    <div class="hitem">
      ${badge(hop.exists ? "present" : "absent", hop.exists ? "ok" : "issue")}
      <span class="msg"><b>${esc(HOP_LABELS[hop.hop] || hop.hop)}</b> —
        ${hop.exists && hop.path
          ? `<a href="#/f/${encodeURIComponent(hop.path)}"><code>${esc(hop.path)}</code></a>`
          : hop.path ? `<code>${esc(hop.path)}</code> <span class="badge issue">not written yet</span>`
                     : '<span class="badge issue">no path</span>'}</span>
    </div>`).join("");
  const events = tl.events.slice();
  if (traceSortAsc) events.reverse();
  const eventRows = events.length ? events.map((ev) => `<tr>
      <td>${badge(ev.type, ev.type === "commit" ? "in-progress" : "ok")}</td>
      <td><code>${esc(ev.sort_key || ev.date)}</code></td>
      <td>${esc(ev.subject || "(no subject)")}
        ${ev.pmo_story ? " " + badge(ev.pmo_story, "ok") : ""}
        ${ev.contract_digest ? ` <span class="badge" title="${esc(ev.contract_digest)}">digest</span>` : ""}</td>
      <td>${ev.type === "commit"
        ? `<code>${esc(String(ev.sha).slice(0, 9))}</code>`
        : `<a href="#/wl/${encodeURIComponent(ev.source)}"><code>${esc(ev.source)}</code></a>`}</td>
    </tr>`).join("")
    : '<tr><td colspan="4">no commits found for this story\u2019s PMO files; no work-log entries (optional evidence \u2014 absent, not an error)</td></tr>';
  app.innerHTML = `
    <div class="guard ${tl.shipped ? "ok" : ""}">${tl.shipped
      ? `shipped: story is done and its evidence exists`
      : `not shipped: ${esc(tl.not_shipped_reason)}`}</div>
    <div class="section"><h2>Trace chain — intent to proof</h2>${chain}</div>
    <div class="section"><h2>Events (commits + work-log)
      <button id="trace-sort" type="button" class="badge" style="cursor:pointer">${traceSortAsc ? "oldest first ↑" : "newest first ↓"}</button>
      <a class="badge" href="${apiPath}" target="_blank" title="machine-readable timeline">export JSON</a></h2>
      <div class="tblwrap"><table class="tbl">
        <tr><th>Type</th><th>When</th><th>What</th><th>Source</th></tr>
        ${eventRows}
      </table></div>
      <p class="hint">work-log entries are supplementary evidence; evidence-story-NN.md
        remains the proof of record and is required before a story counts as shipped.</p></div>
    <div class="section"><h2>Agent handoff</h2>
      <div class="copybar"><button id="copy-handoff" type="button">copy</button></div>
      <pre class="src" id="handoff-text">Loading\u2026</pre></div>`;
  api(`/api/projects/${encodeURIComponent(slug)}/handoff/${encodeURIComponent(storyId)}`).then((h) => {
    document.getElementById("handoff-text").textContent = h.data.text;
  }).catch((err) => {
    document.getElementById("handoff-text").textContent = `handoff unavailable: ${err.message}`;
  });
  document.getElementById("copy-handoff").addEventListener("click", () => {
    navigator.clipboard.writeText(document.getElementById("handoff-text").textContent);
  });
  document.getElementById("trace-sort").addEventListener("click", () => {
    traceSortAsc = !traceSortAsc;
    route();
  });
}


async function viewWorklog(path) {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "work log" }]);
  const body = await api(`/api/worklog?path=${encodeURIComponent(path)}`);
  app.innerHTML = `
    <div class="guard ok">supplementary evidence \u2014 work logs never replace evidence-story-NN.md</div>
    <div class="section"><h2>work log \u00b7 <code>${esc(body.data.path)}</code> (read-only, verbatim \u2014
      excluded paths were omitted at capture time and stay omitted here)</h2>
      <pre class="src">${esc(body.data.content)}</pre></div>`;
}

/* ── the board (WLA-17-05/06) ───────────────────────────────────────
 * Kanban over the same read layer: swimlane per phase, six status
 * columns, paused lanes dimmed with their reason, closed lanes folded
 * behind a one-line receipt. Moves (WLA-17-06) construct the same
 * update_story_status intent as the editor and go through
 * /api/mutations preview → apply — the board is never a second write
 * path. Drops on paused or closed lanes refuse; a "⇄ move" affordance
 * covers keyboards and touch. */

const BOARD_STATUSES = ["backlog", "ready", "in-progress", "blocked", "on-hold", "done"];
const PARKED_COLUMNS = ["blocked", "on-hold"];
const HOLD_COLUMNS = ["on-hold"];

function boardCard(slug, lane, card) {
  const parked = PARKED_COLUMNS.includes(card.status) || card.status === "paused";
  const movable = !lane.closed && !lane.paused;
  return `
    <article class="bcard st-${esc(card.status)}" ${movable ? 'draggable="true"' : ""}
         data-story="${esc(card.story_id)}" data-phase="${lane.number}"
         data-status="${esc(card.status)}" data-evidence="${card.evidence_exists ? 1 : 0}"
         aria-label="${esc(card.story_id)}: ${esc(card.title)}. Status ${esc(card.status)}.">
      <div class="bcard-top"><a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(card.story_id)}"><code>${esc(card.story_id)}</code></a>
        <span class="bcard-status">${esc(card.status)}${card.evidence_exists ? ' · <span class="tick">proof saved</span>' : ""}</span></div>
      <div class="bcard-title">${esc(card.title)}</div>
      ${parked ? `<div class="bcard-note"><strong>Waiting:</strong> ${esc(card.note || "no reason recorded")}</div>` : ""}
      ${movable ? `<div class="bcard-actions" role="group" aria-label="Actions for ${esc(card.story_id)}">
        <button type="button" class="bmove" id="board-move-${esc(card.story_id)}" data-board-move>Move</button>
        <button type="button" class="bmove" id="board-park-${esc(card.story_id)}" data-board-park>Park</button>
      </div>` : ""}
    </article>`;
}

function boardLane(slug, columns, lane) {
  const droppable = !lane.closed && !lane.paused;
  const cols = columns.map((col) => `
    <div class="bcol" data-col="${esc(col)}" data-phase="${lane.number}" data-droppable="${droppable ? 1 : 0}">
      <div class="bcol-head">${esc(col)} <span class="bcol-count">${lane.columns[col].length}</span></div>
      ${lane.columns[col].map((card) => boardCard(slug, lane, card)).join("")}
    </div>`).join("");
  const uncovered = lane.story_count === 0 && lane.uncovered_story_files
    ? `<span class="sub">no story table — ${lane.uncovered_story_files} story file${lane.uncovered_story_files === 1 ? "" : "s"} on disk, unlisted</span>` : "";
  const head = `
    <div class="blane-title">
      <div>${lane.is_pointer ? '<span aria-label="current phase">Current · </span>' : ""}<a href="#/p/${encodeURIComponent(slug)}/ph/${lane.number}">Phase ${lane.number} · ${esc(lane.slug)}</a>
        ${lane.paused ? `<span class="pause-banner"><strong>Paused.</strong> ${esc(lane.pause_note || "No reason recorded")}</span>` : ""}
        ${lane.retired ? `<span class="sub">${lane.retired} retired row${lane.retired === 1 ? "" : "s"} not shown</span>` : ""}
        ${uncovered}</div>
      <div class="blane-actions" role="group" aria-label="Actions for phase ${lane.number}">
        <button type="button" id="board-create-${lane.number}" data-board-create data-phase="${lane.number}" data-phase-name="${esc(lane.slug)}"${lane.paused ? " disabled" : ""}>Create story</button>
        <button type="button" id="board-phase-${lane.number}" data-board-phase-action="${lane.paused ? "resume_phase" : "pause_phase"}" data-phase="${lane.number}" data-phase-name="${esc(lane.slug)}">${lane.paused ? "Resume phase" : "Pause phase"}</button>
      </div>
    </div>`;
  if (lane.closed) {
    return `
      <details class="blane closed" data-phase="${lane.number}">
        <summary>phase ${lane.number} · ${esc(lane.slug)} — closed, ${lane.done_count}/${lane.story_count} done</summary>
        <div class="bcols">${cols}</div>
      </details>`;
  }
  return `
    <div class="blane${lane.paused ? " paused" : ""}" data-phase="${lane.number}" data-paused="${lane.paused ? 1 : 0}">
      <div class="blane-head">${head}</div>
      <div class="bcols">${cols}</div>
    </div>`;
}

function focusBoardRegion(selector) {
  if (!SNAPSHOT_MODE) focusRegion(selector);
}

function boardNotice(text) {
  const out = document.getElementById("board-move");
  if (!out) return;
  out.innerHTML = `<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Nothing changed.</strong> ${esc(text)}</div>`;
  focusBoardRegion("#board-move .board-refusal");
}

function boardMutationError(payload, status) {
  return (payload.data && payload.data.error)
    || (payload.issues && payload.issues[0])
    || `request refused (${status})`;
}

function boardPreviewFiles(files) {
  return files.filter((file) => file.changed || file.action === "create").map((file) => `
    <details class="filepreview" open>
      <summary>${badge(file.action === "create" ? "new file" : "changed", file.action === "create" ? "ok" : "in-progress")}
        <code>${esc(file.path)}</code></summary>
      ${file.action === "create" ? `<pre class="src">${esc(file.new_content || "")}</pre>`
        : `<pre class="diff">${diffHtml(file.diff || "")}</pre>`}
    </details>`).join("");
}

async function previewBoardMutation(out, intent, sentence) {
  out.innerHTML = stateHtml("Preparing the exact change…");
  try {
    const { status, body: payload } = await postJson("/api/mutations/preview", intent);
    if (status >= 400 || payload.ok === false) {
      out.innerHTML = `<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Preview refused. Nothing changed.</strong> ${esc(boardMutationError(payload, status))}</div>`;
      focusBoardRegion(`#${out.id} .board-refusal`);
      return;
    }
    const preview = payload.data;
    const reviewedIntent = { ...intent };
    out.innerHTML = `<section class="board-preview" aria-labelledby="board-preview-title" tabindex="-1">
      <div class="board-preview-head"><span>Review before applying</span><h2 id="board-preview-title">${esc(sentence)}</h2>
        ${badge("nothing written yet", "ok")}</div>
      <p>These are the exact saved-file changes this action would make.</p>
      ${boardPreviewFiles(preview.files)}
      <details class="board-preview-technical"><summary>Technical details</summary>
        <dl><div><dt>Mutation</dt><dd><code>${esc(intent.kind)}</code></dd></div>
          <div><dt>Single-use preview fingerprint</dt><dd><code>${esc(preview.fingerprint)}</code></dd></div></dl>
      </details>
      <div class="board-preview-actions">
        <button type="button" class="applybtn" id="board-apply">Apply this exact change</button>
        <button type="button" id="board-preview-cancel">Cancel</button>
      </div>
      <div id="board-apply-result"></div>
    </section>`;
    enhanceSemantics(out);
    focusBoardRegion(".board-preview");
    document.getElementById("board-preview-cancel").addEventListener("click", () => {
      out.closest("#board-move").innerHTML = "";
      restoreReturnFocus("board-action");
    });
    document.getElementById("board-apply").addEventListener("click", async (event) => {
      const button = event.currentTarget;
      const result = document.getElementById("board-apply-result");
      button.disabled = true;
      button.textContent = "Applying…";
      try {
        const { status: applyStatus, body: applied } = await postJson(
          "/api/mutations/apply",
          { ...reviewedIntent, fingerprint: preview.fingerprint },
        );
        if (applyStatus >= 400 || applied.ok === false) {
          const stale = applyStatus === 409;
          result.innerHTML = `<div class="guard board-refusal" role="alert" tabindex="-1"><strong>${stale ? "Preview refused" : "Apply refused"}. Nothing changed.</strong> ${esc(boardMutationError(applied, applyStatus))}${applied.data && applied.data.rolled_back ? " All writes were rolled back." : ""}</div>`;
          focusBoardRegion("#board-apply-result .board-refusal");
          return;
        }
        await route();
      } catch (error) {
        result.innerHTML = `<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Apply failed. Nothing changed.</strong> ${esc(error.message)}</div>`;
        focusBoardRegion("#board-apply-result .board-refusal");
      }
    });
  } catch (error) {
    out.innerHTML = `<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Preview failed. Nothing changed.</strong> ${esc(error.message)}</div>`;
    focusBoardRegion(`#${out.id} .board-refusal`);
  }
}

/* The move panel: the same structured intent the editor builds,
 * pre-filled from a drop or the ⇄ affordance. Client mirrors of the
 * server rules gate the preview button; the server stays the
 * authority. */
function openMovePanel(slug, move, trigger = document.activeElement) {
  const out = document.getElementById("board-move");
  if (!out) return;
  rememberReturnFocus("board-action", trigger);
  const fixedTarget = move.to || "";
  const options = BOARD_STATUSES.filter((status) => status !== move.from);
  out.innerHTML = `<section class="board-action-panel" aria-labelledby="move-panel-title" tabindex="-1">
    <div class="board-action-heading"><span>Story action · Phase ${esc(move.phase)}</span>
      <h2 id="move-panel-title">Move <code>${esc(move.story)}</code></h2>
      <p>Current status: <strong>${esc(move.from)}</strong>. The card stays put until you review and apply an exact preview.</p></div>
    <form class="edit moveform" id="move-form">
      ${fixedTarget
        ? `<div class="board-choice"><span>New status</span><strong>${esc(fixedTarget)}</strong></div>`
        : field("new status", selectHtml("status", options, options[0]))}
      ${field("reason (required when parking on-hold)", '<input type="text" name="reason" placeholder="why is this waiting?">')}
      <details><summary>Technical details</summary>
        <p>Proof is only used when marking done. Existing proof is kept when this is blank.</p>
        ${field(`evidence body ${move.evidenceExists ? "(proof already exists)" : "(required for done when proof is missing)"}`,
          '<textarea name="evidence_body" placeholder="- proof line…"></textarea>')}
        <p><a href="#/edit/update_story_status">Open the full roadmap editor</a></p>
      </details>
      <div class="board-form-actions"><button type="submit">Preview this move</button>
        <button type="button" id="move-cancel">Cancel</button></div>
    </form>
    <div id="move-out"></div>
  </section>`;
  enhanceSemantics(out);
  const close = () => {
    out.innerHTML = "";
    restoreReturnFocus("board-action");
  };
  document.getElementById("move-cancel").addEventListener("click", close);
  wireDismissibleRegion(".board-action-panel", close, "board-action");
  const form = document.getElementById("move-form");
  const runMovePreview = async () => {
    const moveOut = document.getElementById("move-out");
    const target = fixedTarget || form.elements.status.value;
    const reason = form.elements.reason.value.trim();
    const evidenceBody = form.elements.evidence_body.value.trim();
    if (target === move.from) {
      moveOut.innerHTML = "";
      return;
    }
    if (HOLD_COLUMNS.includes(target) && !reason) {
      moveOut.innerHTML = '<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Preview refused. Nothing changed.</strong> Parking on-hold requires a reason. Add why this work is waiting, then preview.</div>';
      focusBoardRegion("#move-out .board-refusal");
      return;
    }
    const intent = {
      kind: "update_story_status", project: slug, phase: String(move.phase),
      story: move.story, status: target,
    };
    if (reason) intent.reason = reason;
    if (evidenceBody) intent.evidence_body = evidenceBody;
    await previewBoardMutation(
      moveOut,
      intent,
      `Move ${move.story} in phase ${move.phase} from ${move.from} to ${target}.`,
    );
  };
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    runMovePreview();
  });
  focusBoardRegion(".board-action-panel");
  if (SNAPSHOT_MODE && new URLSearchParams(location.search).has("autopreview")) {
    runMovePreview();
  }
}

function openCreatePanel(slug, phase, phaseName, trigger = document.activeElement) {
  const out = document.getElementById("board-move");
  if (!out) return;
  rememberReturnFocus("board-action", trigger);
  out.innerHTML = `<section class="board-action-panel" aria-labelledby="create-panel-title" tabindex="-1">
    <div class="board-action-heading"><span>New story · Phase ${esc(phase)}</span>
      <h2 id="create-panel-title">Create a board task</h2>
      <p>It will start in <strong>Phase ${esc(phase)} · ${esc(phaseName)}</strong>. Nothing is added until you review and apply the preview.</p></div>
    <form class="edit" id="board-create-form">
      ${field("title", '<input type="text" name="title" required autocomplete="off" placeholder="What needs to be done?">')}
      ${field("starting status", selectHtml("status", ["backlog", "ready", "in-progress"], "backlog"))}
      <details><summary>Technical details</summary>
        ${field("story slug (optional)", '<input type="text" name="slug" pattern="[a-z0-9-]*" title="lowercase letters, digits, and hyphens">')}
        <p><a href="#/edit/create_story">Open the full roadmap editor</a> for the complete planning surface.</p>
      </details>
      <div class="board-form-actions"><button type="submit">Preview this story</button>
        <button type="button" id="create-cancel">Cancel</button></div>
    </form>
    <div id="create-out"></div>
  </section>`;
  enhanceSemantics(out);
  const close = () => {
    out.innerHTML = "";
    restoreReturnFocus("board-action");
  };
  document.getElementById("create-cancel").addEventListener("click", close);
  wireDismissibleRegion(".board-action-panel", close, "board-action");
  const form = document.getElementById("board-create-form");
  const runCreatePreview = async () => {
    const previewOut = document.getElementById("create-out");
    const title = form.elements.title.value.trim();
    const status = form.elements.status.value;
    const storySlug = form.elements.slug.value.trim();
    if (!title) {
      previewOut.innerHTML = '<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Preview refused. Nothing changed.</strong> Give the story a short title first.</div>';
      focusBoardRegion("#create-out .board-refusal");
      return;
    }
    const intent = {
      kind: "create_story", project: slug, phase: String(phase), title, status,
    };
    if (storySlug) intent.slug = storySlug;
    await previewBoardMutation(
      previewOut,
      intent,
      `Create “${title}” in phase ${phase} with status ${status}.`,
    );
  };
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    runCreatePreview();
  });
  focusBoardRegion(".board-action-panel");
  if (SNAPSHOT_MODE) {
    const params = new URLSearchParams(location.search);
    if (params.has("autocreate")) {
      form.elements.title.value = params.get("autocreate") || "A short board task";
      if (params.get("createstatus")) form.elements.status.value = params.get("createstatus");
      if (params.has("autopreview")) runCreatePreview();
    }
  }
}

function openPhasePanel(slug, phase, phaseName, kind, trigger = document.activeElement) {
  const out = document.getElementById("board-move");
  if (!out) return;
  const pausing = kind === "pause_phase";
  const action = pausing ? "Pause" : "Resume";
  rememberReturnFocus("board-action", trigger);
  out.innerHTML = `<section class="board-action-panel" aria-labelledby="phase-panel-title" tabindex="-1">
    <div class="board-action-heading"><span>Phase action</span>
      <h2 id="phase-panel-title">${action} Phase ${esc(phase)} · ${esc(phaseName)}</h2>
      <p>The lane stays ${pausing ? "active" : "paused"} until you review and apply the exact preview.</p></div>
    <form class="edit" id="board-phase-form">
      ${pausing ? field("reason (required)", '<input type="text" name="reason" required placeholder="why should this phase wait?">') : ""}
      <div class="board-form-actions"><button type="submit">Preview ${action.toLowerCase()}</button>
        <button type="button" id="phase-cancel">Cancel</button></div>
    </form>
    <div id="phase-out"></div>
  </section>`;
  enhanceSemantics(out);
  const close = () => {
    out.innerHTML = "";
    restoreReturnFocus("board-action");
  };
  document.getElementById("phase-cancel").addEventListener("click", close);
  wireDismissibleRegion(".board-action-panel", close, "board-action");
  const form = document.getElementById("board-phase-form");
  const runPhasePreview = async () => {
    const previewOut = document.getElementById("phase-out");
    const reason = pausing ? form.elements.reason.value.trim() : "";
    if (pausing && !reason) {
      previewOut.innerHTML = '<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Preview refused. Nothing changed.</strong> Pausing a phase requires a reason.</div>';
      focusBoardRegion("#phase-out .board-refusal");
      return;
    }
    const intent = { kind, project: slug, phase: String(phase) };
    if (reason) intent.reason = reason;
    await previewBoardMutation(previewOut, intent, `${action} phase ${phase} · ${phaseName}.`);
  };
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    runPhasePreview();
  });
  focusBoardRegion(".board-action-panel");
}

function wireBoardMoves(slug) {
  const board = document.querySelector(".board");
  if (!board) return;
  let dragging = null;
  board.addEventListener("dragstart", (event) => {
    const card = event.target.closest && event.target.closest(".bcard[draggable]");
    if (!card) return;
    dragging = { ...card.dataset };
    event.dataTransfer.setData("text/plain", card.dataset.story);
    event.dataTransfer.effectAllowed = "move";
  });
  board.addEventListener("dragend", () => { dragging = null; });
  board.addEventListener("dragover", (event) => {
    if (!dragging) return;
    const column = event.target.closest && event.target.closest(".bcol");
    if (column) event.preventDefault();
  });
  board.addEventListener("drop", (event) => {
    if (!dragging) return;
    const column = event.target.closest && event.target.closest(".bcol");
    if (!column) return;
    event.preventDefault();
    const from = dragging;
    dragging = null;
    if (column.dataset.phase !== from.phase) {
      boardNotice("Cross-phase moves are not supported. The story stays in its original lane.");
      return;
    }
    if (column.dataset.droppable !== "1") {
      boardNotice("This phase is paused or closed. Resume it before moving its stories.");
      return;
    }
    openMovePanel(slug, {
      story: from.story, phase: from.phase, from: from.status,
      to: column.dataset.col, evidenceExists: from.evidence === "1",
    });
  });
  board.addEventListener("click", (event) => {
    const create = event.target.closest && event.target.closest("[data-board-create]");
    if (create) {
      openCreatePanel(slug, create.dataset.phase, create.dataset.phaseName, create);
      return;
    }
    const phaseAction = event.target.closest && event.target.closest("[data-board-phase-action]");
    if (phaseAction) {
      openPhasePanel(
        slug,
        phaseAction.dataset.phase,
        phaseAction.dataset.phaseName,
        phaseAction.dataset.boardPhaseAction,
        phaseAction,
      );
      return;
    }
    const button = event.target.closest && event.target.closest("[data-board-move], [data-board-park]");
    if (!button) return;
    const card = button.closest(".bcard");
    openMovePanel(slug, {
      story: card.dataset.story,
      phase: card.dataset.phase,
      from: card.dataset.status,
      to: button.hasAttribute("data-board-park") ? "on-hold" : "",
      evidenceExists: card.dataset.evidence === "1",
    }, button);
  });
}

function boardOverviewStrip(slug, setup, status, step, presentation, notice) {
  const next = presentation.next_step || {};
  const work = setup.delivery_scope?.current_work;
  const needsAttention = setup.readiness !== "ready";
  const technicalOpen = Boolean(
    notice || (SNAPSHOT_MODE && new URLSearchParams(location.search).has("confirmstep")),
  );
  return `<section class="board-overview readiness-${esc(setup.readiness)}" aria-labelledby="board-title">
    <div class="board-overview-head"><div><span>Work · ${esc(slug)}</span>
      <h1 id="board-title">${esc(slug)} board</h1></div>
      ${badge(needsAttention ? "Needs attention" : "Ready", needsAttention ? "issue" : "ok")}</div>
    <div class="board-overview-strip">
      <div class="board-attention"><span>${needsAttention ? "Needs attention" : "Repository ready"}</span>
        <strong>${esc(status.summary)}</strong></div>
      <div class="board-next-step"><span>Next step</span>
        <strong>${esc(next.label || presentationCopy("check_readiness"))}</strong>
        <p>${esc(next.summary || "Review the current work before acting.")}</p></div>
      ${work ? `<div class="board-current-work"><span>Current work</span>
        <a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(work.story_id)}"><code>${esc(work.story_id)}</code> ${esc(work.title)}</a>
        <small>${esc(work.status)}</small></div>` : ""}
    </div>
    <details class="board-technical"${technicalOpen ? " open" : ""}><summary>Technical details</summary>
      <p>Exact repository, contract, gate, command, and one-step facts.</p>
      ${statusPanel(status, step, notice)}
    </details>
  </section>`;
}

async function viewBoard(slug, notice = null) {
  slug = slug || selectedProject;
  if (!slug) {
    viewProjectSelector("#/board");
    return;
  }
  setCrumbs([{ label: "work", href: "#/" }, { label: slug }]);
  const projectQuery = `?project=${encodeURIComponent(slug)}`;
  const [boardBody, statusBody, stepBody, setupBody, presentationBody] = await Promise.all([
    api(`/api/projects/${encodeURIComponent(slug)}/board`),
    api(`/api/status${projectQuery}`),
    api(`/api/step${projectQuery}`),
    api(`/api/delivery-setup${projectQuery}`),
    api(`/api/presentation/status${projectQuery}`),
  ]);
  const model = boardBody.data;
  const step = stepBody.data;
  const open = model.phases.filter((lane) => !lane.closed);
  const closed = model.phases.filter((lane) => lane.closed);
  app.innerHTML = `${destinationNav("work", "#/board")}
    ${boardOverviewStrip(slug, setupBody.data, statusBody.data, step, presentationBody.data, notice)}
    <div class="board" aria-labelledby="phase-lanes-title">
      <div class="board-lanes-head"><div><span>Roadmap</span><h2 id="phase-lanes-title">Phase lanes</h2></div>
        <p>Create and move work here. Every saved change stops for an exact preview.</p></div>
      <div id="board-move"></div>
      ${open.map((lane) => boardLane(slug, model.columns, lane)).join("") || stateHtml("No open phases")}
      ${closed.length ? `<details class="board-closed"><summary>Closed phases (${closed.length})</summary>
        ${closed.map((lane) => boardLane(slug, model.columns, lane)).join("")}</details>` : ""}
    </div>`;
  wireStepControl(step);
  wireBoardMoves(slug);
  // Deterministic screenshot affordances for board action and refusal states.
  if (SNAPSHOT_MODE) {
    const params = new URLSearchParams(location.search);
    const automove = params.get("automove");
    const autocreate = params.get("autocreate");
    if (automove) {
      app.classList.add("board-action-snapshot");
      const [story, to] = automove.split(":");
      const card = document.querySelector(`.bcard[data-story="${selectorEscape(story)}"]`);
      if (card && to) {
        openMovePanel(slug, {
          story, phase: card.dataset.phase, from: card.dataset.status,
          to, evidenceExists: card.dataset.evidence === "1",
        });
      }
    } else if (autocreate !== null) {
      app.classList.add("board-action-snapshot");
      const phase = params.get("createphase");
      const button = phase
        ? document.querySelector(`[data-board-create][data-phase="${selectorEscape(phase)}"]`)
        : document.querySelector("[data-board-create]:not([disabled])");
      if (button) openCreatePanel(slug, button.dataset.phase, button.dataset.phaseName, button);
    }
  }
}

/* ── structured editor (WLA-5-06) ───────────────────────────────────
 * The editor constructs structured intent and POSTs it to
 * /api/mutations/preview. It never applies: the apply/diff workflow
 * is WLA-5-07. Client-side checks catch the obvious before the
 * server's authoritative refusals. */

const EDIT_ACTIONS = {
  adoption_review: "review adoption",
  create_phase: "create phase",
  create_story: "create story",
  update_story_status: "update story status",
  pause_phase: "pause phase",
  resume_phase: "resume phase",
  attach_evidence: "attach evidence",
  close_phase: "close phase",
};

const adoptionReviewMarks = new Map();
const ADOPTION_TERMINAL_HANDOFF = "dw setup preview <proposal-file>";
const ADOPTION_TECHNICAL_LABEL = "Technical details";

function provenanceHtml(provenance) {
  return `<p class="adoption-provenance"><strong>Source:</strong> ${esc(provenance?.sentence || "Unknown.")}</p>`;
}

function adoptionReviewTabs() {
  return `<div class="tabs adoption-workspace-tabs" aria-label="Roadmap changes workspace">${Object.keys(EDIT_ACTIONS).map((name) =>
    `<a href="#/edit/${name}" class="${name === "adoption_review" ? "active" : ""}">${esc(EDIT_ACTIONS[name])}</a>`).join("")}</div>`;
}

function adoptionMarkState(key) {
  if (!adoptionReviewMarks.has(key)) {
    adoptionReviewMarks.set(key, { decision: "", objections: [], overall_note: "" });
  }
  return adoptionReviewMarks.get(key);
}

function correctionPacket(model, state) {
  return {
    kind: "delivery-workbench-setup-review-corrections",
    schema_version: 1,
    decision: "rejected-with-corrections",
    proposal_hash: model.technical_details.proposal_hash,
    objections: state.objections.map((item) => ({ item: item.item, correction: item.correction })),
    overall_note: state.overall_note,
    authorizes_setup: false,
    starts_work: false,
  };
}

function renderAdoptionMarks(model, key, identity = null) {
  const out = document.getElementById("adoption-marks");
  if (!out) return;
  const state = adoptionMarkState(key);
  const options = model.objection_items.map((item) =>
    `<option value="${esc(item.id)}">${esc(item.label)}</option>`).join("");
  const packet = state.decision === "rejected"
    ? correctionPacket(model, state) : null;
  out.innerHTML = `<section class="adoption-marks" aria-labelledby="adoption-marks-title">
    <h2 id="adoption-marks-title">Your review mark</h2>
    <p>Marks stay in this browser page only. They do not save files, create a confirmation, or grant permission.</p>
    <div class="adoption-mark-actions" role="group" aria-label="Review decision">
      <button type="button" data-adoption-mark="accept" aria-pressed="${state.decision === "accepted"}">Accepted for preview</button>
      <button type="button" data-adoption-mark="reject" aria-pressed="${state.decision === "rejected"}">Reject with corrections</button>
      <button type="button" data-adoption-mark="abandon">Abandon this mark</button>
    </div>
    ${state.decision === "accepted" ? `<div class="adoption-mark-result" role="status">
      <strong>Accepted for preview.</strong> Nothing has been applied and no terminal confirmation exists yet.
    </div>` : ""}
    ${state.decision === "rejected" ? `<form id="adoption-correction-form" class="adoption-correction-form">
      <h3>Correction packet</h3>
      <label><b>Proposal item</b><select name="item">${options}</select></label>
      <label><b>What should change?</b><textarea name="correction" required></textarea></label>
      <button type="submit" data-adoption-objection="add">Add objection</button>
      <label><b>Overall note</b><textarea name="overall_note">${esc(state.overall_note)}</textarea></label>
      <ul class="adoption-objections">${state.objections.map((item, index) => `<li>
        <strong>${esc(model.objection_items.find((candidate) => candidate.id === item.item)?.label || item.item)}</strong>
        <span>${esc(item.correction)}</span>
        <button type="button" data-adoption-objection="remove-${index}" data-remove-objection="${index}">Remove</button>
      </li>`).join("") || "<li>No item-level objections yet.</li>"}</ul>
      <details class="adoption-packet"><summary>Correction packet for the setup conversation</summary>
        <pre>${esc(JSON.stringify(packet, null, 2))}</pre>
      </details>
    </form>` : ""}
  </section>`;
  out.querySelector('[data-adoption-mark="accept"]').addEventListener("click", (event) => {
    const focus = captureAppFocus() || { selector: focusSelector(event.currentTarget), index: -1, tag: "button" };
    state.decision = "accepted";
    state.objections = [];
    renderAdoptionMarks(model, key, focus);
  });
  out.querySelector('[data-adoption-mark="reject"]').addEventListener("click", (event) => {
    const focus = captureAppFocus() || { selector: focusSelector(event.currentTarget), index: -1, tag: "button" };
    state.decision = "rejected";
    renderAdoptionMarks(model, key, focus);
  });
  out.querySelector('[data-adoption-mark="abandon"]').addEventListener("click", (event) => {
    const focus = captureAppFocus() || { selector: focusSelector(event.currentTarget), index: -1, tag: "button" };
    adoptionReviewMarks.set(key, { decision: "", objections: [], overall_note: "" });
    renderAdoptionMarks(model, key, focus);
  });
  const form = out.querySelector("#adoption-correction-form");
  if (form) {
    form.elements.overall_note.addEventListener("input", () => {
      state.overall_note = form.elements.overall_note.value;
    });
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const correction = form.elements.correction.value.trim();
      if (!correction) return;
      state.overall_note = form.elements.overall_note.value;
      state.objections.push({ item: form.elements.item.value, correction });
      renderAdoptionMarks(model, key, {
        selector: '[data-adoption-objection="add"]', index: -1, tag: "button",
      });
    });
    out.querySelectorAll("[data-remove-objection]").forEach((button) => button.addEventListener("click", () => {
      const index = Number(button.dataset.removeObjection);
      state.objections.splice(index, 1);
      renderAdoptionMarks(model, key, {
        selector: '[data-adoption-mark="reject"]', index: -1, tag: "button",
      });
    }));
  }
  finishDynamicRender(identity);
}

function adoptionStoryHtml(story) {
  return `<article class="adoption-story" data-review-item="${esc(story.item_id)}">
    <h4><code>${esc(story.id_sketch)}</code> ${esc(story.title)}</h4>
    <p>${esc(story.purpose)}</p>
    ${provenanceHtml(story.provenance)}
    <h5>What this story must prove</h5>
    <ul>${story.acceptance_criteria.map((criterion) => `<li>${esc(criterion.text)}${provenanceHtml(criterion.provenance)}</li>`).join("")}</ul>
    <h5>What it depends on</h5>
    ${story.dependencies.length ? `<ul>${story.dependencies.map((dependency) => `<li>${esc(dependency.sentence)}${provenanceHtml(dependency.provenance)}</li>`).join("")}</ul>` : "<p>Nothing else in this draft must finish first.</p>"}
  </article>`;
}

async function viewAdoptionReview() {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "roadmap changes", href: "#/edit" }, { label: "review adoption" }]);
  const query = ADOPTION_PROPOSAL_FILE
    ? `proposal_file=${encodeURIComponent(ADOPTION_PROPOSAL_FILE)}`
    : ADOPTION_PROPOSAL_ID ? `proposal=${encodeURIComponent(ADOPTION_PROPOSAL_ID)}` : "";
  const model = (await api(`/api/setup/review${query ? `?${query}` : ""}`)).data;
  if (!model.valid) {
    app.innerHTML = `${destinationNav("plan", "#/edit")}${adoptionReviewTabs()}<div class="adoption-review invalid-adoption-review">
      <h1>Review adoption proposal</h1>
      <div class="guard" role="alert"><strong>Proposal refused.</strong><pre>${esc(model.refusal)}</pre></div>
      <section class="adoption-unresolved"><h2>Unresolved assumptions</h2><p>${esc(model.unresolved_questions.summary)}</p></section>
      <details class="adoption-technical"><summary>${esc(model.technical_details.label || ADOPTION_TECHNICAL_LABEL)}</summary><pre>${esc(JSON.stringify(model.technical_details, null, 2))}</pre></details>
      <section class="adoption-handoff"><h2>Next act</h2><p>${esc(model.terminal_handoff.sentence)}</p><code>${esc(model.terminal_handoff.command || ADOPTION_TERMINAL_HANDOFF)}</code></section>
    </div>`;
    return;
  }
  const key = model.technical_details.proposal_hash;
  app.innerHTML = `${destinationNav("plan", "#/edit")}${adoptionReviewTabs()}<div class="adoption-review">
    <header class="adoption-review-head"><p class="eyebrow">Roadmap changes · review only</p>
      <h1>Review ${esc(model.project.title)}</h1>
      <p class="adoption-vision">${esc(model.project.vision)}</p>
      <p>${esc(model.project.context)} ${esc(model.project.identity)}</p>
      ${provenanceHtml(model.project.vision_provenance)}
      ${provenanceHtml(model.project.provenance)}
      <div class="adoption-inert"><strong>Review only.</strong> This page cannot save setup, create permission, start work, certify, or commit.</div>
    </header>
    <section class="adoption-phases"><h2>What the phases accomplish</h2>
      ${model.phases.map((phase) => `<article class="adoption-phase" data-review-item="${esc(phase.item_id)}">
        <div class="adoption-phase-number">Phase ${esc(phase.number)}</div><h3>${esc(phase.title)}</h3>
        <p>${esc(phase.accomplishes)}</p>${provenanceHtml(phase.provenance)}
        <div class="adoption-stories">${phase.stories.map(adoptionStoryHtml).join("")}</div>
      </article>`).join("")}
    </section>
    <section class="adoption-exit"><h2>What the roadmap must prove overall</h2><ul>
      ${model.exit_criteria.map((criterion) => `<li>${esc(criterion.text)}${provenanceHtml(criterion.provenance)}</li>`).join("")}
    </ul></section>
    <section class="adoption-unresolved"><h2>Unresolved assumptions</h2><p>${esc(model.unresolved_questions.summary)}</p>
      ${model.unresolved_questions.items.length ? `<ul>${model.unresolved_questions.items.map((item) => `<li data-review-item="${esc(item.item_id)}"><strong>${esc(item.question)}</strong>${provenanceHtml(item.provenance)}</li>`).join("")}</ul>` : ""}
    </section>
    <section class="adoption-configuration"><div><p class="eyebrow">Separate from roadmap truth</p><h2>${esc(model.configuration.label)}</h2><p>${esc(model.configuration.explanation)}</p></div>
      <div class="adoption-config-grid"><article><h3>Tracked delivery policy</h3><p>${esc(model.configuration.policy.sentence)}</p>
        ${model.configuration.policy.documents.length ? `<ul>${model.configuration.policy.documents.map((item) => `<li><strong>${esc(item.sentence)}</strong>${provenanceHtml(item.provenance)}</li>`).join("")}</ul>` : ""}
        ${model.configuration.policy.provenance ? provenanceHtml(model.configuration.policy.provenance) : ""}${model.configuration.policy.present && ADOPTION_PROPOSAL_FILE ? '<a class="adoption-bundle-link" href="#/program-studio/bundle">Review the generated program as one linked bundle</a>' : ""}</article>
        <article><h3>Local driver bindings</h3><p>${esc(model.configuration.driver_bindings.sentence)}</p>
          <ul>${model.configuration.driver_bindings.items.map((item) => `<li><strong>${esc(item.profile)}</strong> — ${esc(item.sentence)}${provenanceHtml(item.provenance)}</li>`).join("")}</ul></article></div>
    </section>
    <section class="adoption-paths"><h2>Files this setup would save</h2><p>${esc(model.changes.summary)}</p>
      <div class="adoption-path-split"><article><h3>Tracked with the repository</h3><ul>${model.changes.tracked.map((item) => `<li>${badge(item.action, item.action === "unchanged" ? "warn" : "ok")}<code>${esc(item.path)}</code></li>`).join("")}</ul></article>
      <article><h3>Local to this checkout</h3><ul>${model.changes.git_local.map((item) => `<li>${badge(item.action, item.action === "unchanged" ? "warn" : "ok")}<code>${esc(item.path)}</code></li>`).join("")}</ul></article></div>
    </section>
    <div id="adoption-marks"></div>
    <details class="adoption-technical"><summary>${esc(model.technical_details.label || ADOPTION_TECHNICAL_LABEL)}</summary><pre>${esc(JSON.stringify(model.technical_details, null, 2))}</pre></details>
    <section class="adoption-handoff"><h2>Next act</h2><p>${esc(model.terminal_handoff.sentence)}</p><code>${esc(model.terminal_handoff.command || ADOPTION_TERMINAL_HANDOFF)}</code></section>
  </div>`;
  renderAdoptionMarks(model, key);
}

const STATUS_VOCAB = ["backlog", "ready", "in-progress", "blocked", "on-hold", "done"];

function field(label, inner, err) {
  return `<label><b>${esc(label)}</b>${inner}
    <span class="fielderr" data-err="${esc(label)}">${err ? esc(err) : ""}</span></label>`;
}

function selectHtml(name, options, selected) {
  return `<select name="${name}">` + options.map((o) =>
    `<option value="${esc(o)}"${o === selected ? " selected" : ""}>${esc(o)}</option>`).join("") + "</select>";
}

async function viewEdit(action) {
  action = action || "create_story";
  if (action === "adoption_review") {
    await viewAdoptionReview();
    return;
  }
  setCrumbs([{ label: "overview", href: "#/" }, { label: "edit" }, { label: EDIT_ACTIONS[action] || action }]);
  const ctx = await api("/api/projects");
  const projects = ctx.data.projects;
  if (!projects.length) {
    app.innerHTML = stateHtml("No projects to edit.");
    return;
  }
  const proj = projects.find((project) => project.slug === selectedProject);
  if (!proj) {
    viewUnavailableProject(selectedProject || "the chosen project");
    return;
  }
  const guarded = proj.issue_count > 0;
  const projDetail = await api(`/api/projects/${encodeURIComponent(proj.slug)}`);
  const phases = projDetail.data.phases;
  const phaseOpts = phases.map((ph) => String(ph.number));
  const stories = phases.flatMap((ph) => ph.stories.map((s) => s.story_id));

  const tabs = Object.keys(EDIT_ACTIONS).map((a) =>
    `<a href="#/edit/${a}" class="${a === action ? "active" : ""}">${esc(EDIT_ACTIONS[a])}</a>`).join("");

  let formFields = "";
  if (action === "create_phase") {
    formFields = [
      field("phase number", '<input type="number" name="number" min="0" step="1" required>'),
      field("title", '<input type="text" name="title" required>'),
      field("slug (optional)", '<input type="text" name="slug" pattern="[a-z0-9-]*" title="lowercase, digits, hyphens">'),
      field("goal (one line)", '<input type="text" name="goal">'),
    ].join("");
  } else if (action === "create_story") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("title", '<input type="text" name="title" required>'),
      field("initial status", selectHtml("status", STATUS_VOCAB.filter((s) => s !== "done"), "backlog")),
    ].join("");
  } else if (action === "update_story_status") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("story", selectHtml("story", stories)),
      field("new status", selectHtml("status", STATUS_VOCAB)),
      field("reason (required for blocked/on-hold parks — recorded in the status cell)",
        '<input type="text" name="reason" placeholder="why is this waiting?">'),
      field("evidence body (required for done when no evidence exists)",
        '<textarea name="evidence_body" placeholder="- proof line…"></textarea>'),
      `<div class="checkline"><input type="checkbox" name="force" id="f-force">
        <label for="f-force">force: replace existing evidence</label></div>`,
    ].join("");
  } else if (action === "pause_phase") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("reason (required)", '<input type="text" name="reason" required placeholder="why should this phase wait?">'),
    ].join("");
  } else if (action === "resume_phase") {
    formFields = [field("phase", selectHtml("phase", phaseOpts))].join("");
  } else if (action === "attach_evidence") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("story", selectHtml("story", stories)),
      field("evidence body", '<textarea name="body" placeholder="- proof line…"></textarea>'),
      `<div class="checkline"><input type="checkbox" name="force" id="f-force">
        <label for="f-force">force: replace existing evidence</label></div>`,
    ].join("");
  } else if (action === "close_phase") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("final summary body", '<textarea name="summary_body" placeholder="## Outcome vs exit criteria…"></textarea>'),
      `<div class="checkline"><input type="checkbox" name="force" id="f-force">
        <label for="f-force">force: close with open stories / replace an existing summary (core force semantics)</label></div>`,
    ].join("");
  }

  app.innerHTML = `${destinationNav("plan", "#/edit")}
    <header class="destination-hero"><span>Plan</span><h1>Review a roadmap change</h1><p>Choose one change, review exactly what it would affect, then decide whether to continue.</p></header>
    <div class="tabs">${tabs}</div>
    ${guarded ? `<div class="guard">Changes are paused — <a href="#/health">review ${proj.issue_count} health issue${proj.issue_count === 1 ? "" : "s"}</a> first.</div>` : ""}
    <form class="edit" id="edit-form">
      ${field("project", selectHtml("project", [proj.slug], proj.slug))}
      ${formFields}
      ${guarded ? `<div class="checkline"><input type="checkbox" name="acknowledge_issues" id="f-ack">
        <label for="f-ack">I acknowledge the validation issues and still want a preview</label></div>` : ""}
      <button type="submit">preview — no files are written</button>
      <div class="hint">Preview shows exact diffs, projected validation, and a fingerprint;
        apply refuses stale previews and never commits — committing stays with you.</div>
    </form>
    <div id="preview-out"></div>`;

  const editForm = document.getElementById("edit-form");
  async function runEditPreview(form) {
    const out = document.getElementById("preview-out");
    const body = { kind: action };
    for (const el of form.elements) {
      if (!el.name) continue;
      if (el.type === "checkbox") body[el.name] = el.checked;
      else body[el.name] = el.value.trim();
    }
    // client-side refusals before the server's authoritative ones
    if (action === "update_story_status" && body.status === "on-hold" && !body.reason) {
      out.innerHTML = `<div class="guard">refused client-side: a hold needs its why — fill the reason before previewing.</div>`;
      return;
    }
    if (action === "update_story_status" && body.status === "done" && !body.evidence_body) {
      const st = phases.flatMap((ph) => ph.stories).find((s) => s.story_id === body.story);
      if (st && !st.evidence_exists) {
        out.innerHTML = `<div class="guard">refused client-side: marking ${esc(body.story)} done requires
          evidence — none exists and no evidence body was provided.</div>`;
        return;
      }
    }
    out.innerHTML = stateHtml("Previewing…");
    try {
      const { status, body: payload } = await postJson("/api/mutations/preview", body);
      if (status >= 400 || payload.ok === false) {
        const msg = (payload.data && payload.data.error) || (payload.issues && payload.issues[0]) || `error ${status}`;
        out.innerHTML = `<div class="guard">${esc(msg)}</div>` +
          (payload.data && payload.data.issues
            ? `<ul class="plain">${payload.data.issues.map((i) => `<li class="issue">${esc(i)}</li>`).join("")}</ul>` : "");
        return;
      }
      const d = payload.data;
      out.innerHTML = `
        <div class="section"><h2>Preview — ${esc(d.kind)} ${badge("nothing written yet", "ok")}
          ${d.no_op ? badge("no-op: repeating this mutation changes nothing", "warn") : ""}</h2>
          <div class="meta">
            ${Object.entries(d.summary).map(([k, v]) =>
              `<div class="kv"><div class="k">${esc(k)}</div><div class="v">${esc(String(v))}</div></div>`).join("")}
            <div class="kv"><div class="k">fingerprint</div><div class="v">${esc(d.fingerprint.slice(0, 24))}…</div></div>
          </div>
          ${d.issues_before && d.issues_before.length ? `<div class="section"><h2>Validation before write</h2>
            <ul class="plain">${d.issues_before.map((i) => `<li class="issue">${esc(i)}</li>`).join("")}</ul></div>` : ""}
          ${d.issues_after === null ? `<p class="hint">projected post-write validation unavailable</p>`
            : d.issues_after.length ? `<div class="section"><h2>Projected validation after write</h2>
            <ul class="plain">${d.issues_after.map((i) => `<li class="warn">${esc(i)}</li>`).join("")}</ul></div>`
            : `<p class="hint">projected post-write validation: clean</p>`}
          ${d.create_dirs.length ? `<p class="hint">creates directory: <code>${d.create_dirs.map(esc).join(", ")}</code></p>` : ""}
          ${d.files.map((f) => `
            <details class="filepreview" ${f.changed ? "open" : ""}>
              <summary>${badge(f.action === "create" ? "new file" : f.changed ? "changed" : "unchanged (owned)",
                  f.action === "create" ? "ok" : f.changed ? "in-progress" : "warn")}
                <code>${esc(f.path)}</code>
                <span class="hint">${f.bytes_before} → ${f.bytes_after} bytes</span></summary>
              ${f.action === "create"
                ? `<pre class="src">${esc(f.new_content || "")}</pre>`
                : f.diff ? `<pre class="diff">${diffHtml(f.diff)}</pre>` : `<pre class="src">${esc(f.new_content || "")}</pre>`}
            </details>`).join("")}
          <button type="button" class="applybtn" id="apply-btn">apply — writes the files above (no commit)</button>
        </div>`;
      document.getElementById("apply-btn").addEventListener("click", async () => {
        out.querySelector("#apply-btn").disabled = true;
        const { status: st, body: applied } = await postJson("/api/mutations/apply", { ...body, fingerprint: d.fingerprint });
        const resultBox = document.createElement("div");
        if (st === 409) {
          resultBox.innerHTML = `<div class="guard">stale preview refused — the source files changed after this
            preview was taken; nothing was written. Re-run the preview for a fresh fingerprint.</div>`;
        } else if (st >= 400 || applied.ok === false) {
          const msg = (applied.data && applied.data.error) || `apply failed (${st})`;
          resultBox.innerHTML = `<div class="guard">${esc(msg)}${applied.data && applied.data.rolled_back
            ? " — all writes were rolled back" : ""}</div>`;
        } else {
          const r = applied.data;
          resultBox.innerHTML = `
            <div class="guard ok">applied: ${r.changed.length} file${r.changed.length === 1 ? "" : "s"} written (no commit made)</div>
            <div class="section"><h2>Post-apply revalidation</h2>
              ${r.issues.length ? `<ul class="plain">${r.issues.map((i) => `<li class="issue">${esc(i)}</li>`).join("")}</ul>`
                : `<p class="hint">dw check: clean — <a href="#/p/${encodeURIComponent(body.project)}">view the refreshed project</a></p>`}
              <ul class="plain">${r.changed.map((c) => `<li><a href="#/f/${encodeURIComponent(c)}"><code>${esc(c)}</code></a></li>`).join("")}</ul>
            </div>`;
        }
        out.appendChild(resultBox);
      });
    } catch (err) {
      out.innerHTML = `<div class="guard">${esc(err.message)}</div>`;
    }
  }

  editForm.addEventListener("submit", (e) => {
    e.preventDefault();
    runEditPreview(e.target);
  });
  // Screenshot affordance: ?snapshot=1&autopreview=1 runs the preview
  // with the form defaults inside this synchronous load chain so
  // headless capture sees the rendered result. Not for interactive use.
  if (SNAPSHOT_MODE && new URLSearchParams(location.search).has("autopreview")) {
    await runEditPreview(editForm);
  }
}

/* ── visual orchestration editor (WLA-24-03) ─────────────────────────
 * The browser authors a complete score but owns no semantics. Every live
 * verdict and scheduling trace comes from the shared Python compiler through
 * the pure preview endpoint. Saving and deleting are separate, stale-safe
 * preview → diff → apply acts; neither endpoint can create run state. */

const ORCH_NODE_TYPES = ["agent", "check", "rail", "approval", "collect"];
const ORCH_ROLES = ["research", "synthesis", "implementation", "review", "verification", "documentation", "repair"];
const ORCH_CAPABILITIES = ["repository-read", "repository-write", "network", "tools-read", "tools-write"];
const ORCH_FORMATS = ["markdown", "json", "text", "git-diff", "directory"];
const ORCH_TERMINALS = ["", "complete", "blocked", "cancelled", "awaiting-certification"];

let orchState = {
  name: "", score: null, exists: false, selected: null, view: "design",
  preview: null, inventory: [], validationTimer: null, jsonDraft: "",
  runInventory: [], runs: [], runId: "", runView: null, runLoading: false,
  runError: "", runPlan: null, runAct: null, runResult: null, runStream: null,
  runConnection: { status: SNAPSHOT_LIVE_STATE === "stale" ? "stale" : "checking" },
  grantDraft: { project: "", story: "", operator: "", minutes: 60 },
  controlReason: "",
};

function clone(value) { return JSON.parse(JSON.stringify(value)); }
function splitLines(value) { return String(value || "").split(/\n|,/).map((x) => x.trim()).filter(Boolean); }
function maybeNumber(value) { const n = Number(value); return value === "" || !Number.isFinite(n) ? null : Math.trunc(n); }
function setOptional(target, key, value) { if (value === "" || value === null || value === undefined) delete target[key]; else target[key] = value; }

function minimalScore(slug = "new-orchestration") {
  return {
    kind: "delivery-workbench-orchestration", schema_version: 1,
    slug, title: "New orchestration",
    defaults: {
      max_concurrency: 2, max_wall_seconds: 3600, max_agent_starts: 8,
      max_check_starts: 16, default_timeout_seconds: 900,
      max_artifact_bytes: 1000000,
    },
    nodes: [{
      id: "human-handoff", type: "approval", activation: "success", needs: [],
      resource_groups: [], prompt: "Review the run before certification.",
      options: ["approve", "reject"], terminal: "awaiting-certification",
    }],
    layout: { nodes: { "human-handoff": { x: 80, y: 120 } }, viewport: { x: 0, y: 0, zoom: 1 } },
  };
}

function ensureOrchShape(score) {
  score.defaults ||= {};
  score.nodes = Array.isArray(score.nodes) ? score.nodes : [];
  score.layout ||= {};
  score.layout.nodes ||= {};
  score.layout.viewport ||= { x: 0, y: 0, zoom: 1 };
  score.nodes.forEach((node, i) => {
    node.needs = Array.isArray(node.needs) ? node.needs : [];
    node.resource_groups = Array.isArray(node.resource_groups) ? node.resource_groups : [];
    if (!score.layout.nodes[node.id]) score.layout.nodes[node.id] = { x: 70 + (i % 4) * 240, y: 70 + Math.floor(i / 4) * 170 };
  });
  return score;
}

function nextNodeId(type) {
  const base = type === "approval" ? "checkpoint" : type;
  const used = new Set(orchState.score.nodes.map((n) => n.id));
  let i = 1;
  while (used.has(`${base}-${i}`)) i += 1;
  return `${base}-${i}`;
}

function defaultOrchNode(type) {
  const id = nextNodeId(type);
  const common = { id, type, activation: "success", needs: [], resource_groups: [] };
  if (type === "agent") return { ...common, role: "research", profile: "research-readonly", prompt: "", context: [], capabilities: ["repository-read"], workspace: "read-only", inputs: [], outputs: [], timeout_seconds: 900, on_failure: { action: "pause" } };
  if (type === "check") return { ...common, runner: { kind: "command", argv: ["python3", "-m", "pytest", "-q"], cwd: "workspace", timeout_seconds: 900, output_bytes: 30000, writes: [] }, expect: { exit_code: 0 }, on_failure: { action: "pause" } };
  if (type === "rail") return { ...common, action: "continue-story", timeout_seconds: 120, on_failure: { action: "pause" } };
  if (type === "approval") return { ...common, prompt: "Review this checkpoint.", options: ["approve", "reject"] };
  return { ...common, inputs: [], outputs: [], timeout_seconds: 120, on_failure: { action: "abort" } };
}

function orchField(label, name, value, type = "text", attrs = "") {
  return `<label class="orch-field"><span>${esc(label)}</span><input type="${type}" name="${esc(name)}" value="${esc(value ?? "")}" ${attrs}></label>`;
}
function orchArea(label, name, value, hint = "") {
  return `<label class="orch-field"><span>${esc(label)}</span><textarea name="${esc(name)}">${esc(value ?? "")}</textarea>${hint ? `<small>${esc(hint)}</small>` : ""}</label>`;
}
function orchSelect(label, name, options, selected) {
  return `<label class="orch-field"><span>${esc(label)}</span><select name="${esc(name)}">${options.map((o) => {
    const value = typeof o === "string" ? o : o.value;
    const text = typeof o === "string" ? o : o.label;
    return `<option value="${esc(value)}"${value === selected ? " selected" : ""}>${esc(text)}</option>`;
  }).join("")}</select></label>`;
}
function orchDatalist(label, name, options, value) {
  const id = `orch-list-${name}`;
  return `<label class="orch-field"><span>${esc(label)}</span><input type="text" name="${esc(name)}" value="${esc(value || "")}" list="${id}"><datalist id="${id}">${options.map((o) => `<option value="${esc(o)}"></option>`).join("")}</datalist></label>`;
}

function inputLines(inputs) {
  return (inputs || []).map((item) => typeof item === "string"
    ? item : `artifact:${item.artifact}:${item.format}`).join("\n");
}

function parseInputLines(raw) {
  return splitLines(raw).map((line) => {
    const match = line.match(/^artifact:([a-z0-9-]+):([a-z-]+)$/);
    return match ? { artifact: match[1], format: match[2] } : line;
  });
}

function outputEditor(outputs) {
  return `<div class="orch-outputs"><div class="orch-subhead"><strong>typed outputs</strong><button type="button" data-orch-add-output>+ output</button></div>
    ${(outputs || []).map((out, i) => `<fieldset class="orch-output" data-output-index="${i}">
      <legend>output ${i + 1} <button type="button" data-orch-remove-output="${i}" aria-label="remove output ${i + 1}">remove</button></legend>
      ${orchField("name", "output_name", out.name)}
      ${orchSelect("format", "output_format", ORCH_FORMATS, out.format)}
      ${orchField("path", "output_path", out.path)}
      ${orchField("schema path", "output_schema", out.schema || "")}
      ${orchArea("required headings", "output_sections", (out.required_sections || []).join("\n"), "one heading per line")}
      ${orchSelect("citations", "output_citations", ["none", "optional", "required"], out.citations || "none")}
      ${orchField("maximum bytes", "output_max_bytes", out.max_bytes || "", "number", 'min="1"')}
      ${orchArea("allowed paths", "output_allowed_paths", (out.allowed_paths || []).join("\n"), "required for git-diff outputs")}
    </fieldset>`).join("")}</div>`;
}

function failureEditor(node) {
  const f = node.on_failure || {};
  return `<fieldset class="orch-failure"><legend>failure route</legend>
    ${orchSelect("action", "failure_action", ["", "retry", "route", "approval", "pause", "abort"], f.action || "")}
    ${orchField("max attempts", "failure_max_attempts", f.max_attempts || "", "number", 'min="1" max="20"')}
    ${orchSelect("route node", "failure_node", [""].concat(orchState.score.nodes.filter((n) => n.id !== node.id).map((n) => n.id)), f.node || "")}
    ${orchField("max visits", "failure_max_visits", f.max_visits || "", "number", 'min="1" max="20"')}
    ${orchField("approval checkpoint", "failure_checkpoint", f.checkpoint || "")}
  </fieldset>`;
}

function nodeInspector(node) {
  const others = orchState.score.nodes.filter((n) => n.id !== node.id);
  const relevant = ((orchState.preview && orchState.preview.validation && orchState.preview.validation.diagnostics) || [])
    .filter((d) => d.pointer.startsWith(`/nodes/${orchState.score.nodes.indexOf(node)}`));
  let specific = "";
  if (node.type === "agent") {
    specific = `
      ${orchDatalist("role", "role", ORCH_ROLES, node.role)}
      ${orchField("logical profile", "profile", node.profile)}
      ${orchArea("prompt template", "prompt", node.prompt || "", "bounded text; never a provider command")}
      ${orchArea("context selectors", "context", (node.context || []).join("\n"), "one contained selector per line")}
      <fieldset><legend>requested capabilities</legend><div class="orch-checkgrid">${ORCH_CAPABILITIES.map((cap) => `<label><input type="checkbox" name="capability" value="${cap}"${(node.capabilities || []).includes(cap) ? " checked" : ""}>${cap}</label>`).join("")}</div></fieldset>
      ${orchSelect("workspace", "workspace", ["none", "read-only", "isolated-worktree"], node.workspace || "read-only")}
      ${orchArea("inputs", "inputs", inputLines(node.inputs), "selector or artifact:name:format, one per line")}
      ${outputEditor(node.outputs)}`;
  } else if (node.type === "check") {
    const r = node.runner || { kind: "command" };
    specific = `
      ${orchSelect("runner kind", "runner_kind", ["command", "builtin"], r.kind || "command")}
      ${orchArea("command argv tokens", "runner_argv", (r.argv || []).join("\n"), "one literal token per line; no command string or interpolation")}
      ${orchField("working directory", "runner_cwd", r.cwd || ".")}
      ${orchSelect("built-in check", "runner_name", ["", "file-exists", "json-schema", "diff-scope", "rail-status"], r.name || "")}
      ${orchField("built-in path", "runner_path", r.path || "")}
      ${orchField("schema path", "runner_schema", r.schema || "")}
      ${orchArea("allowed paths", "runner_allowed_paths", (r.allowed_paths || []).join("\n"))}
      ${orchField("timeout seconds", "runner_timeout", r.timeout_seconds || "", "number", 'min="1"')}
      ${orchField("output bytes", "runner_output_bytes", r.output_bytes || "", "number", 'min="1"')}
      ${orchArea("declared writes", "runner_writes", (r.writes || []).join("\n"), "command checks only; empty means read-only")}
      ${orchField("expected exit code", "expect_exit_code", (node.expect || {}).exit_code ?? 0, "number", 'min="0" max="255"')}`;
  } else if (node.type === "rail") {
    specific = `${orchField("dw step action id", "action", node.action || "")}`;
  } else if (node.type === "approval") {
    specific = `${orchArea("checkpoint prompt", "prompt", node.prompt || "")}
      ${orchArea("decision options", "options", (node.options || []).join("\n"), "one explicit option per line")}
      ${orchSelect("terminal meaning", "terminal", ORCH_TERMINALS, node.terminal || "")}`;
  } else if (node.type === "collect") {
    specific = `${orchArea("artifact inputs", "inputs", inputLines(node.inputs), "artifact:name:format, one per line")}${outputEditor(node.outputs)}`;
  }
  return `<div class="orch-inspector-head"><div><small>selected node</small><strong>${esc(node.id)}</strong></div>
      <div><button type="button" data-orch-duplicate-node>duplicate</button><button type="button" class="danger" data-orch-delete-node>delete</button></div></div>
    <div class="orch-node-errors"${relevant.length ? "" : " hidden"}>${relevant.map((d) => `<div><code>${esc(d.pointer)}</code> ${esc(d.message)}</div>`).join("")}</div>
    <form id="orch-node-form" class="orch-inspector-form">
      ${orchField("node id", "id", node.id, "text", 'pattern="[a-z][a-z0-9-]*"')}
      ${orchSelect("node type", "type", ORCH_NODE_TYPES, node.type)}
      ${orchField("title", "title", node.title || "")}
      ${orchArea("description", "description", node.description || "")}
      ${orchSelect("activation", "activation", ["success", "failure"], node.activation || "success")}
      <fieldset><legend>success dependencies</legend><div class="orch-checkgrid">${others.map((other) => `<label><input type="checkbox" name="need" value="${esc(other.id)}"${(node.needs || []).includes(other.id) ? " checked" : ""}>${esc(other.id)}</label>`).join("") || "<small>no other nodes yet</small>"}</div></fieldset>
      ${orchArea("resource locks", "resource_groups", (node.resource_groups || []).join("\n"), "one resource group per line")}
      ${node.type !== "check" && node.type !== "approval" ? orchField("timeout seconds", "timeout_seconds", node.timeout_seconds || "", "number", 'min="1"') : ""}
      ${specific}
      ${node.type !== "approval" ? failureEditor(node) : ""}
    </form>`;
}

function scoreInspector() {
  const score = orchState.score;
  const d = score.defaults || {};
  const v = (score.layout || {}).viewport || {};
  return `<div class="orch-inspector-head"><div><small>score settings</small><strong>${esc(score.slug)}</strong></div></div>
    <form id="orch-score-form" class="orch-inspector-form">
      ${orchField("slug / filename", "slug", score.slug, "text", 'pattern="[a-z][a-z0-9-]*"')}
      ${orchField("title", "title", score.title)}
      ${orchArea("description", "description", score.description || "")}
      ${orchField("roadmap project", "project", score.project || "")}
      <fieldset><legend>finite run defaults</legend>
        ${orchField("maximum concurrency", "max_concurrency", d.max_concurrency || "", "number", 'min="1" max="64"')}
        ${orchField("maximum wall seconds", "max_wall_seconds", d.max_wall_seconds || "", "number", 'min="1"')}
        ${orchField("maximum agent starts", "max_agent_starts", d.max_agent_starts || "", "number", 'min="1"')}
        ${orchField("maximum check starts", "max_check_starts", d.max_check_starts || "", "number", 'min="1"')}
        ${orchField("default timeout seconds", "default_timeout_seconds", d.default_timeout_seconds || "", "number", 'min="1"')}
        ${orchField("maximum artifact bytes", "max_artifact_bytes", d.max_artifact_bytes || "", "number", 'min="1"')}
      </fieldset>
      <fieldset><legend>canvas viewport (document hash only)</legend>
        ${orchField("viewport x", "viewport_x", v.x ?? 0, "number")}
        ${orchField("viewport y", "viewport_y", v.y ?? 0, "number")}
        ${orchField("zoom", "viewport_zoom", v.zoom ?? 1, "number", 'min="0.1" step="0.1"')}
      </fieldset>
    </form>`;
}

function diagnosticMap() {
  const map = new Map();
  const diagnostics = orchState.preview?.validation?.diagnostics || [];
  diagnostics.forEach((d) => {
    const match = d.pointer.match(/^\/nodes\/(\d+)/);
    if (!match) return;
    const node = orchState.score.nodes[Number(match[1])];
    if (!node) return;
    if (!map.has(node.id)) map.set(node.id, []);
    map.get(node.id).push(d);
  });
  return map;
}

function orchGraph() {
  const score = ensureOrchShape(orchState.score);
  const positions = score.layout.nodes;
  const byId = Object.fromEntries(score.nodes.map((n) => [n.id, n]));
  const errors = diagnosticMap();
  const maxX = Math.max(900, ...Object.values(positions).map((p) => Number(p.x || 0) + 240));
  const maxY = Math.max(500, ...Object.values(positions).map((p) => Number(p.y || 0) + 150));
  const edges = [];
  score.nodes.forEach((node) => {
    const target = positions[node.id] || { x: 0, y: 0 };
    (node.needs || []).forEach((need) => {
      const source = positions[need];
      if (source) edges.push(`<path class="orch-edge success" d="M ${Number(source.x) + 190} ${Number(source.y) + 48} C ${Number(source.x) + 220} ${Number(source.y) + 48}, ${Number(target.x) - 30} ${Number(target.y) + 48}, ${Number(target.x)} ${Number(target.y) + 48}" marker-end="url(#arrow-success)"><title>${esc(need)} succeeds before ${esc(node.id)}</title></path>`);
    });
    if (node.on_failure?.action === "route" && positions[node.on_failure.node]) {
      const failure = positions[node.on_failure.node];
      edges.push(`<path class="orch-edge failure" d="M ${Number(target.x) + 95} ${Number(target.y) + 96} C ${Number(target.x) + 95} ${Number(target.y) + 130}, ${Number(failure.x) + 95} ${Number(failure.y) - 30}, ${Number(failure.x) + 95} ${Number(failure.y)}" marker-end="url(#arrow-failure)"><title>${esc(node.id)} failure routes to ${esc(node.on_failure.node)}</title></path>`);
    }
  });
  return `<div class="orch-canvas-wrap"><svg id="orch-canvas" class="orch-canvas" viewBox="0 0 ${maxX} ${maxY}" role="group" aria-labelledby="orch-canvas-title">
    <title id="orch-canvas-title">Orchestration graph. Select a node to edit its exact rules.</title>
    <defs>
      <marker id="arrow-success" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="arrow-success"></path></marker>
      <marker id="arrow-failure" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="arrow-failure"></path></marker>
    </defs>
    ${edges.join("")}
    ${score.nodes.map((node) => {
      const pos = positions[node.id];
      const detail = node.type === "agent" ? `${node.role || "agent"} · ${node.profile || "profile?"}`
        : node.type === "check" ? `${node.runner?.kind || "runner?"} check`
        : node.type === "approval" ? (node.terminal || "checkpoint") : node.type;
      const count = (errors.get(node.id) || []).length;
      return `<g class="orch-node type-${esc(node.type)}${node.activation === "failure" ? " failure-only" : ""}${orchState.selected === node.id ? " selected" : ""}${count ? " has-error" : ""}"
          data-node-id="${esc(node.id)}" transform="translate(${Number(pos.x)},${Number(pos.y)})" tabindex="0" role="button" aria-label="${esc(node.id)}, ${esc(detail)}${count ? `, ${count} errors` : ""}">
        <title>${esc(node.id)} — ${esc(detail)}${count ? ` — ${count} compiler errors` : ""}</title>
        <rect width="190" height="96" rx="9"></rect>
        <circle class="port input" cx="0" cy="48" r="5"></circle><circle class="port output" cx="190" cy="48" r="5"></circle><circle class="port fail" cx="95" cy="96" r="5"></circle>
        <text class="node-type" x="14" y="21">${esc(node.type)}${node.activation === "failure" ? " · failure" : ""}</text>
        <text class="node-id" x="14" y="48">${esc(node.id)}</text>
        <text class="node-detail" x="14" y="72">${esc(detail).slice(0, 27)}</text>
        ${count ? `<text class="node-error" x="174" y="21" text-anchor="end">${count}!</text>` : ""}
      </g>`;
    }).join("")}
  </svg></div>`;
}

function validateView() {
  const p = orchState.preview;
  if (!p) return stateHtml("Checking delivery readiness…");
  const diagnostics = p.validation?.diagnostics || [];
  const technicalOpen = new URLSearchParams(location.search).has("orchtechnical");
  if (!p.valid) return `<div class="orch-validation invalid delivery-preflight" role="region" aria-label="Delivery readiness results">
    <header class="preflight-head"><div><span>Delivery readiness</span><h2>${diagnostics.length} delivery decision${diagnostics.length === 1 ? "" : "s"} need attention</h2><p>Nothing was saved or started. Correct the affected part of the delivery plan, then check readiness again.</p></div>${badge("not ready", "issue")}</header>
    <ol class="preflight-corrections">${diagnostics.map((d) => `<li data-pointer="${esc(d.pointer)}"><strong>Affected decision</strong><span>${esc(d.message)}</span><small>Next step: ${esc(d.remediation)}</small></li>`).join("")}</ol>
    <div class="preflight-actions"><a href="#/program-studio">Return to delivery choices</a></div>
    <details class="preflight-technical"${technicalOpen ? " open" : ""}><summary>Technical details</summary>
      <p>Exact compiler targets and identifiers:</p>
      <ol class="orch-diagnostics">${diagnostics.map((d) => `<li data-pointer="${esc(d.pointer)}"><code>${esc(d.pointer)}</code><strong>${esc(d.code)}</strong><span>${esc(d.message)}</span><small>${esc(d.remediation)}</small></li>`).join("")}</ol>
    </details>
  </div>`;
  const c = p.compiled;
  const s = p.simulation;
  const nodeCount = c.score?.nodes?.length || orchState.score.nodes?.length || 0;
  const profiles = c.analysis.profiles || [];
  return `<div class="orch-validation valid delivery-preflight" role="region" aria-label="Delivery readiness results">
    <header class="preflight-head"><div><span>Delivery readiness</span><h2>This delivery plan is ready to review</h2><p>The work order, checks, decisions, limits, and stops are internally valid. This inspection starts nothing.</p></div>${badge("ready to review", "ok")}</header>
    <div class="preflight-facts">
      <section><span>Work and order</span><strong>${esc(nodeCount)} planned step${nodeCount === 1 ? "" : "s"} in ${esc(s.waves.length)} group${s.waves.length === 1 ? "" : "s"}</strong><small>The displayed order comes from the shared delivery-plan simulation.</small></section>
      <section><span>Team</span><strong>${profiles.length ? `${esc(profiles.length)} named responsibility profile${profiles.length === 1 ? "" : "s"}` : "No agent profile requested"}</strong><small>${profiles.length ? esc(profiles.join(", ")) : "Checks and human decisions may still be present."}</small></section>
      <section><span>Review</span><strong>${esc(s.failure_branches.length)} repair or stop route${s.failure_branches.length === 1 ? "" : "s"} · ${esc(s.checkpoints.length)} decision point${s.checkpoints.length === 1 ? "" : "s"}</strong><small>Failed work follows the reviewed route; no route is improvised at start.</small></section>
      <section><span>Permission</span><strong>Still off</strong><small>A separate start review must name the current work, accountable operator, limits, and expiry.</small></section>
    </div>
    <section class="preflight-limits"><div><span>Limits and stops</span><strong>Finite before start</strong></div><div>${Object.entries(s.budgets).map(([k, v]) => `<div class="kv"><div class="k">${esc(k.replace(/^max_/, "").replaceAll("_", " "))}</div><div class="v">${esc(v)}</div></div>`).join("")}</div></section>
    <div class="preflight-next"><div><span>Next step</span><strong>Review the separate delivery start</strong><p>Confirming that later review creates permission for this delivery; it does not continue automatically.</p></div><div><button type="button" id="preflight-open-start">Review separate start</button><a href="#/program-studio">Return to delivery choices</a><a href="#/">Leave for now</a></div></div>
    <details class="preflight-technical"${technicalOpen ? " open" : ""}><summary>Technical details</summary>
      <div class="orch-hashes"><div><span>semantic hash</span><code>${esc(c.semantic_hash)}</code></div><div><span>document hash</span><code>${esc(c.document_hash)}</code></div></div>
      <div class="orch-validate-grid">
        <section><h3>capability request</h3>${c.analysis.capabilities.map((x) => badge(x, "warn")).join(" ") || "none"}<h3>logical profiles</h3>${profiles.map((x) => badge(x)).join(" ") || "none"}</section>
        <section><h3>finite budgets</h3>${Object.entries(s.budgets).map(([k, v]) => `<div class="kv"><div class="k">${esc(k)}</div><div class="v">${esc(v)}</div></div>`).join("")}</section>
      </div>
      <section><h3>scheduling simulation ${badge("pure — starts nothing", "ok")}</h3><div class="orch-waves">${s.waves.map((w) => `<div><strong>wave ${w.wave}</strong><span>${w.scheduled.map((x) => `<code>${esc(x)}</code>`).join(" ")}</span><small>eligible: ${esc(w.eligible.join(", "))}${w.resource_groups.length ? ` · locks: ${esc(w.resource_groups.join(", "))}` : ""}</small></div>`).join("")}</div></section>
      <section><h3>output lineage</h3><div class="tablewrap"><table><thead><tr><th>artifact</th><th>producer</th><th>format</th><th>consumers</th><th>conventions</th></tr></thead><tbody>${s.output_lineage.map((o) => `<tr><td><code>${esc(o.name)}</code></td><td>${esc(o.producer)}</td><td>${esc(o.format)}</td><td>${esc(o.consumers.join(", ") || "—")}</td><td>${o.citations === "required" ? "citations · " : ""}${o.required_sections.length ? esc(o.required_sections.join(", ")) : `${esc(o.max_bytes)} bytes`}</td></tr>`).join("") || '<tr><td colspan="5">no declared artifacts</td></tr>'}</tbody></table></div></section>
      <section><h3>failure routes and checkpoints</h3>${s.failure_branches.map((b) => `<div class="orch-branch"><code>${esc(b.source)}</code><strong>${esc(b.action)}</strong><span>${esc(b.node || b.checkpoint || "terminal policy")}</span></div>`).join("") || "none"}<div class="orch-terminals">${s.terminals.map((t) => `${badge(t.node)} → ${badge(t.meaning, "ok")}`).join(" ")}</div></section>
    </details>
  </div>`;
}

function jsonView() {
  const text = orchState.jsonDraft || JSON.stringify(orchState.score, null, 2);
  return `<div class="orch-json"><div class="orch-json-actions"><label class="filebtn">import JSON<input type="file" id="orch-import" accept="application/json,.json"></label><button type="button" id="orch-json-to-graph">apply JSON to graph</button></div>
    <label><span>lossless score document</span><textarea id="orch-json-text" spellcheck="false">${esc(text)}</textarea></label>
    <div id="orch-json-error" class="guard" hidden></div><p class="hint">Unknown schema fields are preserved in this text and refused by the compiler; they are never silently dropped.</p></div>`;
}

function runStateBadge(state) {
  const cls = ["active", "succeeded", "complete"].includes(state) ? "ok"
    : ["failed", "blocked", "cancelled", "revoked"].includes(state) ? "issue"
      : ["awaiting-approval", "awaiting-certification", "paused"].includes(state) ? "warn" : "";
  return badge(state, cls);
}

function liveRunGraph(view) {
  const nodes = view.graph.nodes || [];
  const positions = view.graph.layout?.nodes || {};
  const maxX = Math.max(820, ...nodes.map((n) => Number(positions[n.id]?.x || 0) + 225));
  const maxY = Math.max(430, ...nodes.map((n) => Number(positions[n.id]?.y || 0) + 145));
  const edges = [];
  nodes.forEach((node) => {
    const target = positions[node.id] || { x: 0, y: 0 };
    (node.needs || []).forEach((need) => {
      const source = positions[need];
      if (source) edges.push(`<path class="orch-edge success" d="M ${Number(source.x) + 190} ${Number(source.y) + 48} C ${Number(source.x) + 220} ${Number(source.y) + 48}, ${Number(target.x) - 30} ${Number(target.y) + 48}, ${Number(target.x)} ${Number(target.y) + 48}" marker-end="url(#run-arrow)"></path>`);
    });
    if (node.on_failure?.action === "route" && positions[node.on_failure.node]) {
      const failure = positions[node.on_failure.node];
      edges.push(`<path class="orch-edge failure" d="M ${Number(target.x) + 95} ${Number(target.y) + 96} C ${Number(target.x) + 95} ${Number(target.y) + 130}, ${Number(failure.x) + 95} ${Number(failure.y) - 30}, ${Number(failure.x) + 95} ${Number(failure.y)}" marker-end="url(#run-fail-arrow)"></path>`);
    }
  });
  return `<div class="run-graph-wrap"><svg class="orch-canvas run-graph" viewBox="0 0 ${maxX} ${maxY}" role="img" aria-labelledby="run-graph-title">
    <title id="run-graph-title">Live orchestration graph. Nodes show authoritative replayed state and attempt.</title>
    <defs><marker id="run-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="arrow-success"></path></marker><marker id="run-fail-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="arrow-failure"></path></marker></defs>
    ${edges.join("")}
    ${nodes.map((node) => {
      const pos = positions[node.id] || { x: 0, y: 0 };
      return `<g class="orch-node run-node state-${esc(node.state)} type-${esc(node.type)}" transform="translate(${Number(pos.x)},${Number(pos.y)})" tabindex="0" role="group" aria-label="${esc(node.id)}, ${esc(node.state)}, attempt ${esc(node.attempt)}">
        <title>${esc(node.id)} — ${esc(node.state)} — attempt ${esc(node.attempt)}${node.blocked_reason ? ` — ${esc(node.blocked_reason)}` : ""}</title><rect width="190" height="96" rx="9"></rect>
        <circle class="port input" cx="0" cy="48" r="5"></circle><circle class="port output" cx="190" cy="48" r="5"></circle>
        <text class="node-type" x="14" y="20">${esc(node.type)} · attempt ${esc(node.attempt)}</text><text class="node-id" x="14" y="46">${esc(node.id)}</text><text class="node-detail" x="14" y="70">${esc(node.state)}</text>
        ${node.blocked_reason ? `<text class="run-node-reason" x="14" y="87">${esc(node.blocked_reason).slice(0, 28)}</text>` : ""}
      </g>`;
    }).join("")}
  </svg></div>`;
}

function runBudgetHtml(budgets) {
  return `<div class="run-budgets">${Object.entries(budgets || {}).map(([name, budget]) => {
    const used = Number(budget.used || 0); const limit = Number(budget.limit || 0);
    const percent = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0;
    return `<div class="run-budget"><span>${esc(name.replace(/^max_/, "").replaceAll("_", " "))}</span><strong>${esc(used)} / ${esc(limit)}</strong><div><i style="width:${percent}%"></i></div></div>`;
  }).join("")}</div>`;
}

function runArtifactHtml(view) {
  const actual = new Map((view.artifacts || []).map((item) => [item.name, item]));
  const declared = [];
  (view.graph.nodes || []).forEach((node) => (node.outputs || []).forEach((output) => declared.push({ ...output, producer: node.id })));
  return `<div class="tablewrap"><table class="run-table"><thead><tr><th>artifact</th><th>producer</th><th>format</th><th>lineage / conventions</th><th>receipt</th></tr></thead><tbody>${declared.map((item) => {
    const receipt = actual.get(item.name);
    const conventions = [item.citations === "required" ? "citations" : "", ...(item.required_sections || [])].filter(Boolean).join(" · ") || `${item.max_bytes || "?"} byte ceiling`;
    return `<tr><td><code>${esc(item.name)}</code></td><td>${esc(item.producer)}</td><td>${esc(item.format)}</td><td>${esc(conventions)}</td><td>${receipt ? `${badge("validated", "ok")} ${esc(receipt.bytes)} B · <code>${esc(receipt.sha256).slice(0, 24)}…</code>` : badge("declared · not produced", "warn")}</td></tr>`;
  }).join("") || '<tr><td colspan="5">No declared artifacts.</td></tr>'}</tbody></table></div>`;
}

function streamButtons(executor, session) {
  const id = session.session_id || session.execution_id;
  if (!id) return "";
  return ["stdout", "stderr"].map((stream) => Number(session[`${stream}_bytes`] || 0) > 0
    ? `<button type="button" data-run-stream="${stream}" data-executor="${executor}" data-execution-id="${esc(id)}">open ${stream} · ${esc(session[`${stream}_bytes`])} B</button>` : "").join("");
}

function runSessionsHtml(view) {
  const agents = view.sessions?.agents || [];
  const checks = view.sessions?.checks || [];
  return `<div class="run-session-columns"><section><h3>research / work agents ${badge(agents.length)}</h3>${agents.map((session) => `<article class="run-session"><div><strong>${esc(session.node_id)}</strong>${runStateBadge(session.state)}</div><small>${esc(session.profile)} · ${esc(session.adapter)} · attempt ${esc(session.attempt)}</small><code>${esc(session.session_id || "no session")}</code><p>${esc(session.reason)}</p><div class="run-stream-buttons">${streamButtons("agent", session)}</div></article>`).join("") || '<p class="hint">No agent session has crossed the driver boundary.</p>'}</section>
    <section><h3>fail checks ${badge(checks.length)}</h3>${checks.map((session) => `<article class="run-session"><div><strong>${esc(session.node_id)}</strong>${runStateBadge(session.state)}</div><small>${esc(session.runner_kind)} · attempt ${esc(session.attempt)} · exit ${esc(session.actual_exit_code ?? "—")}/${esc(session.expected_exit_code)}</small><code>${esc(session.runner_hash)}</code><p>${esc(session.reason)}${(session.changed_paths || []).length ? ` · changed: ${esc(session.changed_paths.join(", "))}` : ""}</p><div class="run-stream-buttons">${streamButtons("check", session)}</div></article>`).join("") || '<p class="hint">No check session has executed.</p>'}</section></div>`;
}

function runRoutesHtml(view) {
  return `<div class="run-route-grid"><section><h3>failure routes</h3>${(view.routes || []).map((route) => `<div class="run-route"><code>${esc(route.node_id)} #${esc(route.attempt)}</code><strong>${esc(route.action)}</strong><span>${esc(route.target)}${route.target_attempt ? ` #${esc(route.target_attempt)}` : ""}</span>${route.resolved ? badge(`resolved · ${route.outcome}`, "ok") : badge("open", "warn")}</div>`).join("") || '<p class="hint">No failure route has fired.</p>'}</section><section><h3>human checkpoints</h3>${(view.checkpoints || []).map((point) => `<div class="run-route"><code>${esc(point.checkpoint)}</code><strong>${esc(point.mode)}</strong><span>${esc(point.reason)}</span>${point.decision ? badge(point.decision, point.decision === "approve" ? "ok" : "issue") : badge("waiting", "warn")}</div>`).join("") || '<p class="hint">No checkpoint has been reached.</p>'}</section></div>`;
}

function runTimelineHtml(view) {
  return `<ol class="run-timeline">${(view.timeline || []).map((event) => `<li><div><strong>${esc(event.event)}</strong><time>${esc(event.ts)}</time>${badge(`#${event.seq}`)}</div><p>${Object.entries(event.detail || {}).map(([key, value]) => `<span><b>${esc(key)}</b> ${esc(value)}</span>`).join("")}</p><code>${esc(event.event_hash)}</code></li>`).join("")}</ol>`;
}

function runControlsHtml(view) {
  return `<section class="run-controls exact-control-audit"><div class="run-control-head"><div><span>exact control catalog</span><strong>Applicability copied from the current saved run</strong></div>${badge("inspection only", "ok")}</div>
    <div class="run-unavailable">${(view.controls || []).map((control, index) => `<div><strong>${esc(control.action)}${control.decision ? ` · ${esc(control.decision)}` : ""}</strong><span>${control.available ? "available through the ordinary action review above" : esc((control.issues || []).join("; ") || "not applicable in the current state")}</span><code>/controls/${esc(index)}</code></div>`).join("")}</div>
  </section>`;
}

function runActPreviewHtml(preview) {
  if (!preview) return "";
  return `<details class="bounded-exact-preview"><summary>Exact run preview</summary><div class="run-token"><span>state + intent token</span><code>${esc(preview.act_token)}</code></div><p>Observed <code>${esc(preview.state)}</code> at generation ${esc(preview.control_generation)} and ledger <code>${esc(preview.ledger_head)}</code>.</p>
    ${preview.correlation_id ? `<p><strong>bound request:</strong> <code>${esc(preview.correlation_id)}</code> · ${esc(preview.response_outcome)}</p>` : ""}${preview.reason ? `<p><strong>bound reason:</strong> ${esc(preview.reason)}</p>` : ""}${(preview.issues || []).map((issue) => `<p class="guard">${esc(issue)}</p>`).join("")}</details>`;
}

function runStreamHtml(stream) {
  if (!stream) return "";
  return `<section class="run-open-stream" role="dialog" aria-modal="false" aria-labelledby="run-stream-title" tabindex="-1"><div><strong id="run-stream-title">${esc(stream.executor)} · ${esc(stream.execution_id)} · ${esc(stream.stream)}</strong><button type="button" id="run-stream-close">close explicit stream</button></div><small>${esc(stream.included_bytes)} / ${esc(stream.bytes)} bytes · ${stream.truncated ? "truncated" : "complete"} · ${esc(stream.sha256)}</small><pre>${esc(stream.content)}</pre></section>`;
}

function runRequestsHtml(view) {
  const outstanding = view.outstanding_requests || [];
  const tree = view.decision_tree || { roots: [], nodes: [] };
  const nodes = new Map((tree.nodes || []).map((item) => [item.correlation_id, item]));
  const renderDecision = (id, depth = 0) => {
    const item = nodes.get(id); if (!item) return "";
    const preview = item.preview || {};
    return `<li style="--decision-depth:${depth}"><div><code>${esc(item.correlation_id)}</code>${badge(item.status, item.status === "approved" || item.status === "applied" ? "ok" : item.status === "pending" ? "warn" : "issue")}</div><strong>${esc(item.kind)} · ${esc(item.origin_node || item.origin)}</strong><small>opened at ledger #${esc(item.opened_seq)} · parent ${esc(item.parent_correlation_id || "root")}</small><details><summary>inspect exact decision preview</summary><dl>${Object.entries(preview).map(([key, value]) => `<div><dt>${esc(key)}</dt><dd><code>${esc(value)}</code></dd></div>`).join("")}</dl></details>${(item.children || []).length ? `<ol>${item.children.map((child) => renderDecision(child, depth + 1)).join("")}</ol>` : ""}</li>`;
  };
  return `<div class="run-request-grid"><section><h3>outstanding requests</h3>${outstanding.map((request) => `<article class="run-request"><div><code>${esc(request.correlation_id)}</code>${badge(`${esc(request.age_seconds)}s old`, "warn")}</div><strong>${esc(request.kind)} · ${esc(request.origin_node || request.origin)}</strong><span>${esc(request.schema_summary)}</span><small>opened #${esc(request.opened_seq)} · expires ${esc(request.expires_at)} · republished generations ${(request.republished_generations || []).map(esc).join(", ") || "none"}</small></article>`).join("") || '<p class="hint">No human decision is outstanding.</p>'}</section><section><h3>checkpoint lineage · inspect only</h3><ol class="run-decision-tree">${(tree.roots || []).map((id) => renderDecision(id)).join("")}</ol>${!tree.roots?.length ? '<p class="hint">No decision point has been recorded.</p>' : ""}</section></div>`;
}

function grantPreviewHtml(plan) {
  if (!plan) return "";
  return `<section class="run-consent ${plan.applicable ? "" : "refused"}" role="dialog" aria-modal="false" aria-labelledby="run-plan-title" tabindex="-1"><div class="run-consent-head"><div><span>immutable grant preview</span><strong id="run-plan-title">${esc(plan.story.id)} · ${esc(plan.score.slug)}</strong></div>${badge("starts no work", "ok")}</div>
    <div class="run-token"><span>single-use start token</span><code>${esc(plan.start_token)}</code></div>
    <div class="run-grant-facts"><div><span>repository</span><code>${esc(plan.repository.branch)} · ${esc(plan.repository.head)}</code></div><div><span>expiry</span><strong>${esc(plan.request.expires_at)}</strong></div><div><span>capabilities</span><strong>${esc(plan.authority.capabilities.join(", ") || "none")}</strong></div><div><span>profiles / workspaces</span><strong>${esc(plan.authority.profiles.join(", ") || "none")} · ${esc(plan.authority.workspace_modes.join(", ") || "none")}</strong></div></div>
    ${runBudgetHtml(Object.fromEntries(Object.entries(plan.authority.budgets).map(([key, value]) => [key, { used: 0, limit: value }]))) }
    ${(plan.issues || []).map((issue) => `<p class="guard">${esc(issue)}</p>`).join("")}
    <div class="run-consent-actions">${plan.applicable ? '<button type="button" id="run-start-confirm">grant authority and create run — dispatch nothing</button>' : ""}<button type="button" id="run-plan-close">close preview</button></div></section>`;
}

function runEmptyHtml() {
  const draft = orchState.grantDraft;
  return `<div class="run-empty"><section><span class="orch-eyebrow">score ≠ authority</span><h2>No local run for this score</h2><p>Saving and validating this score starts nothing. Build a grant preview from current repository, story, score, capability, budget, and expiry facts; only a second explicit confirmation creates immutable local authority.</p>${badge("preview is pure", "ok")} ${badge("grant dispatches nothing", "warn")}</section>
    <form id="run-grant-form" class="run-grant-form"><label>project slug<input name="project" required value="${esc(draft.project || orchState.score.project || "")}"></label><label>in-progress story id<input name="story" required value="${esc(draft.story)}" placeholder="WLA-24-07"></label><label>operator identity<input name="operator" required value="${esc(draft.operator)}" placeholder="human or accountable agent"></label><label>grant minutes<input name="minutes" type="number" min="1" max="1440" value="${esc(draft.minutes || 60)}"></label><button type="submit">preview exact grant</button></form>${grantPreviewHtml(orchState.runPlan)}</div>`;
}

function liveConnectionHtml(connection, recovery) {
  const state = connection?.status || "checking";
  if (state === "stale") {
    return `<div class="live-connection stale" role="group" aria-label="Live update status"><strong>Live updates interrupted</strong><p>This is the last verified view. Completed work remains recorded; “Check for updates” replays the saved history before showing anything newer. No work is declared lost or repeated.</p></div>`;
  }
  const copy = state === "live" ? "Live updates on"
    : state === "verified" ? "Saved history checked"
      : state === "manual" ? "Check for updates manually"
        : "Checking for updates";
  return `<div class="live-connection ${esc(state)}" role="group" aria-label="Live update status">${badge(copy, state === "live" || state === "verified" ? "ok" : "")}<span>${esc(recovery?.summary || "The saved history was checked before this view was built.")}</span></div>`;
}

function liveStateBadge(progress) {
  const group = progress?.status?.group || "waiting";
  const cls = ["active", "complete"].includes(group) ? "ok"
    : ["blocked", "stopped"].includes(group) ? "issue"
      : ["review", "repair", "recovering", "waiting"].includes(group) ? "warn" : "";
  return badge(progress?.status?.label || group, cls);
}

function liveAnswerGrid(progress) {
  return `<section class="live-answers" aria-label="Delivery questions">${(progress.answers || []).map((item) => `<article data-answer="${esc(item.id)}" class="status-${esc(item.status)}"><span>${esc(item.question)}</span><p>${esc(item.answer)}</p></article>`).join("")}</section>`;
}

function liveProgressGroups(progress) {
  const model = progress.progress || {};
  const groups = model.groups || {};
  const items = Array.isArray(model.items) ? model.items : Object.entries(groups).flatMap(([status, values]) => (values || []).map((item) => ({ ...item, status })));
  const ordered = ["active", "review", "repair", "recovering", "blocked", "waiting", "complete"];
  return `<section class="live-panel live-scope"><div class="live-panel-head"><div><span>Scope and progress</span><strong>${esc(model.completed || 0)} of ${esc(model.known_total || 0)} declared work items complete</strong></div><b>${esc(model.percent || 0)}%</b></div>
    <div class="live-progress-meter" role="progressbar" aria-label="Delivery progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${esc(model.percent || 0)}" aria-valuetext="${esc(model.completed || 0)} of ${esc(model.known_total || 0)} work items complete"><i style="width:${Math.max(0, Math.min(100, Number(model.percent || 0)))}%"></i></div>
    <div class="live-work-groups">${ordered.map((status) => {
      const matching = items.filter((item) => item.status === status);
      if (!matching.length) return "";
      return `<section class="state-${esc(status)}"><h3>${esc(status)} <small>${esc(matching.length)}</small></h3><ul>${matching.map((item) => `<li><strong>${esc(item.title)}</strong>${item.summary ? `<span>${esc(item.summary)}</span>` : ""}</li>`).join("")}</ul></section>`;
    }).join("")}</div>
  </section>`;
}

function livePeopleHtml(progress) {
  const team = progress.team || {};
  const people = (title, items, empty) => `<section><h3>${esc(title)}</h3>${(items || []).map((item) => `<article><strong>${esc(item.name)}</strong><span>${esc(item.responsibility || item.assignment || "")}</span>${item.status ? badge(item.status, item.status === "active" ? "ok" : "") : ""}</article>`).join("") || `<p>${esc(empty)}</p>`}</section>`;
  return `<section class="live-panel live-team"><div class="live-panel-head"><div><span>Team and review</span><strong>Doing, checking, and deciding stay separate</strong></div></div><p>${esc(team.summary || "")}</p><div>${people("Doing the work", team.owners, "No work owner is assigned.")}${people("Independent review", team.reviewers, "No independent reviewer is assigned.")}${(team.decision_owners || []).length ? people("Decision owners", team.decision_owners, "") : ""}</div>${team.identity_note ? `<small>${esc(team.identity_note)}</small>` : ""}</section>`;
}

function liveReviewHtml(progress) {
  const review = progress.review || {};
  const sections = [
    ["Mechanical checks", review.mechanical],
    ["Agent judgment", review.agent_judgment],
    ["Dissent", review.dissent],
    ["Repair", review.repair],
    ["Final governed decisions", review.final_governed_decisions],
  ];
  return `<section class="live-panel live-review"><div class="live-panel-head"><div><span>Evidence and decisions</span><strong>Different kinds of proof are shown separately</strong></div></div><div>${sections.map(([title, items]) => `<section><h3>${esc(title)}</h3>${(items || []).map((item) => `<article><strong>${esc(item.title)}</strong>${badge(item.status || item.exact_state || "recorded", ["passed", "pass", "succeeded", "approved", "complete"].includes(String(item.status || item.exact_state)) ? "ok" : "")}</article>`).join("") || '<p>None recorded.</p>'}</section>`).join("")}</div></section>`;
}

function liveNextHtml(progress) {
  const next = progress.next_step || {};
  const blocker = progress.blocker || {};
  const decision = progress.decision || {};
  return `<section class="live-next state-${esc(next.kind || "wait")}"><div><span>What happens next?</span><h2>${esc(next.label || "Wait")}</h2><p>${esc(next.detail || "")}</p></div><div class="live-next-facts"><article class="${blocker.status === "blocked" ? "issue" : "clear"}"><span>Blocked</span><strong>${esc(blocker.status === "blocked" ? "Yes" : "No")}</strong><p>${esc(blocker.summary || "")}</p></article><article class="${decision.status === "needed" ? "warn" : "clear"}"><span>Decision needed</span><strong>${esc(decision.status === "needed" ? "Yes" : "No")}</strong><p>${esc(decision.summary || "")}</p></article></div><small>The next step is copied from the saved delivery state. This page does not choose another one.</small></section>`;
}

function liveLimitsHtml(progress) {
  const limits = progress.limits || {};
  const permission = limits.permission || {};
  const cost = limits.cost || {};
  const primaryCounts = (limits.counts || []).filter((item) => item.primary !== false);
  return `<section class="live-panel live-limits"><div class="live-panel-head"><div><span>Remaining permission and cost</span><strong>What this delivery may still use</strong></div></div><div class="live-limit-summary"><article><span>Change permission</span><strong>${esc(permission.status || "unknown")}</strong><p>${esc(permission.summary || "")}</p>${(permission.will_not_use || []).length ? `<small>Will not use: ${esc(permission.will_not_use.join(", "))}</small>` : ""}</article><article><span>Money cost</span><strong>${esc(cost.status || "unknown")}</strong><p>${esc(cost.summary || "")}</p></article></div><div class="live-limit-counts">${primaryCounts.map((item) => `<article class="${item.status === "none-left" ? "empty" : ""}"><span>${esc(item.label)}</span><strong>${esc(item.remaining)} ${esc(item.unit)} left</strong><small>${esc(item.used)} used of ${esc(item.limit)}</small></article>`).join("")}</div>${limits.expires_at ? `<p class="live-expiry">Permission ends ${esc(limits.expires_at)}.</p>` : ""}</section>`;
}

function boundedScopeText(scope) {
  if (!scope || typeof scope !== "object") return String(scope || "No scope is recorded.");
  return Object.entries(scope)
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .map(([key, value]) => `${key.replaceAll("_", " ")}: ${Array.isArray(value) ? value.join(", ") : typeof value === "object" ? JSON.stringify(value) : value}`)
    .join(" · ") || "No scope is recorded.";
}

function boundedMeasurementHtml(measurement) {
  const item = measurement || { state: "unknown", unit: "units" };
  if (item.state === "finite" || item.state === "zero") return `<strong>${esc(item.value)} ${esc(item.unit)}</strong><small>${esc(item.state)}</small>`;
  const label = item.state === "not-applicable" ? "Not applicable"
    : item.state === "unbounded" ? "Unbounded"
      : "Unknown";
  return `<strong>${label}</strong><small>${esc(item.state)}</small>`;
}

function boundedMeasurementText(measurement) {
  const item = measurement || { state: "unknown", unit: "units" };
  if (item.state === "finite" || item.state === "zero") return `${item.value} ${item.unit}`;
  return item.state === "not-applicable" ? "not applicable"
    : item.state === "unbounded" ? "unbounded" : "unknown";
}

function boundedUsageTable(model, all = false) {
  const items = (model?.usage?.items || []).filter((item) => all || item.primary !== false);
  return `<div class="tablewrap bounded-usage-table"><table><thead><tr><th>Measure</th><th>Limit</th><th>Estimate</th><th>Actual</th><th>Remaining</th></tr></thead><tbody>${items.map((item) => `<tr><td><strong>${esc(item.label)}</strong><small>${esc(item.category)}</small></td>${["limit", "estimate", "actual", "remaining"].map((kind) => `<td>${boundedMeasurementHtml(item.measurements?.[kind])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

function boundedPermissionHtml(model) {
  const permission = model?.permission || {};
  const allowed = permission.allowed_effects || [];
  const forbidden = permission.forbidden_effects || [];
  const current = permission.current_use || [];
  return `<section class="bounded-permission" data-bounded-section="limits"><div class="bounded-section-head"><div><span>Before any action</span><h3>Permission, scope, limits, and cost</h3></div>${badge(permission.status || "unknown", permission.status === "available" ? "ok" : "warn")}</div>
    <div class="bounded-permission-grid"><article><span>Allowed effects</span><p>${allowed.map((item) => badge(String(item).replace(/[_:.-]/g, " "), "ok")).join(" ") || "No change effect is currently available."}</p></article><article><span>Affected scope</span><p>${esc(boundedScopeText(permission.scope))}</p></article><article><span>Expiry and stops</span><p>${permission.expires_at ? `Permission ends ${esc(permission.expires_at)}.` : "No expiry value is recorded."}</p><ul>${(permission.stop_conditions || []).map((item) => `<li>${esc(item)}</li>`).join("")}</ul></article><article><span>Still forbidden</span><p>${forbidden.map((item) => badge(String(item).replace(/[_:.-]/g, " "), "issue")).join(" ") || "No explicit exclusion is recorded."}</p></article></div>
    <p class="bounded-current-use"><strong>Current consumption:</strong> ${current.slice(0, 8).map((item) => `${esc(item.label)} — ${esc(boundedMeasurementText(item.actual))} used, ${esc(boundedMeasurementText(item.remaining))} remaining`).join(" · ") || "No counted consumption is recorded."}</p>
    ${boundedUsageTable(model)}
    <details class="bounded-all-usage"><summary>Every limit and measurement</summary>${boundedUsageTable(model, true)}<p>${esc(model?.usage?.legend?.zero || "")} ${esc(model?.usage?.legend?.unbounded || "")} Unknown and not applicable remain separate.</p></details>
  </section>`;
}

function boundedInboxHtml(model) {
  const inbox = model?.inbox || [];
  return `<section class="bounded-inbox" data-bounded-section="failure"><div class="bounded-section-head"><div><span>Decision and blocker inbox</span><h3>${inbox.length ? `${esc(inbox.length)} item${inbox.length === 1 ? "" : "s"} need attention` : "Nothing needs a decision right now"}</h3></div>${badge(inbox.length ? "attention" : "clear", inbox.length ? "warn" : "ok")}</div>
    <div class="bounded-inbox-grid">${inbox.map((item) => `<article class="bounded-inbox-item kind-${esc(item.kind)}"><div><span>${esc(item.kind)}</span>${badge(item.status, item.kind === "refusal" ? "issue" : "warn")}</div><h4>${esc(item.affected_work)}</h4><dl><div><dt>Why it cannot proceed</dt><dd>${esc(item.why)}</dd></div><div><dt>Who or what resolves it</dt><dd>${esc(item.resolver)}</dd></div></dl><h5>Valid choices and what follows</h5><ul>${(item.valid_choices || []).map((choice) => `<li><strong>${esc(choice.label)}${choice.available ? "" : " — unavailable"}</strong><span>${esc(choice.effect)} ${esc(choice.after)}</span></li>`).join("") || "<li><strong>Inspect only</strong><span>No state-changing choice is currently valid; review exact evidence.</span></li>"}</ul><p><strong>If you do nothing:</strong> ${esc(item.after_no_choice)}</p>${item.explanation ? boundedFailureDetailsHtml(item.explanation, "Recorded refusal") : ""}<details><summary>Technical details</summary><code>${esc(item.technical_reference || "no exact reference")}</code></details></article>`).join("") || '<p class="hint">The saved state has no blocker, pending decision, or refusal.</p>'}</div>
  </section>`;
}

function boundedFailureDetailsHtml(explanation, label = "Action could not be completed") {
  const item = explanation || {};
  const effect = item.effect_answer === "no" || item.effect_may_have_occurred === false
    ? "No — this refusal records no effect."
    : item.effect_answer === "yes" || item.effect_may_have_occurred === true
      ? "Yes — inspect the saved receipt before another action."
      : "Unknown — reload the saved history before another action.";
  return `<section class="bounded-failure" role="alert"><h4>${esc(label)}</h4><dl><div><dt>What happened</dt><dd>${esc(item.what_happened || "The action was refused.")}</dd></div><div><dt>What stayed unchanged</dt><dd>${esc(item.what_stayed_unchanged || "The last verified delivery state remains visible.")}</dd></div><div><dt>Could an effect already have occurred?</dt><dd>${esc(effect)}</dd></div><div><dt>Safe next step</dt><dd>${esc(item.safe_next_step || "Reload the saved state before acting again.")}</dd></div></dl><details><summary>Technical details</summary><pre>${esc(JSON.stringify(item.technical_evidence || {}, null, 2))}</pre></details></section>`;
}

function boundedErrorHtml(message) {
  if (!message) return "";
  const refusedBeforeEffect = /before work|no event was appended|no decision was applied|no grant was created/i.test(message);
  return boundedFailureDetailsHtml({
    what_happened: message,
    what_stayed_unchanged: refusedBeforeEffect
      ? "No work or saved event changed at this refusal boundary."
      : "The last verified view remains visible; no alternative action was inferred.",
    effect_may_have_occurred: refusedBeforeEffect ? false : null,
    safe_next_step: "Reload the saved state, inspect the exact history, and preview only a currently available action.",
    technical_evidence: { message },
  });
}

function boundedActionMatch(model, preview, target) {
  if (!preview) return null;
  return (model?.actions || []).find((item) => item.action === preview.action
    && String(item.decision || "") === String(preview.decision || "")
    && String(item.correlation_id || "") === String(target === "program" ? preview.request_id || "" : preview.correlation_id || ""));
}

function boundedPreviewHtml(model, preview, target) {
  if (!preview) return "";
  const action = boundedActionMatch(model, preview, target);
  const consequences = action?.consequences || {};
  const applicable = Boolean(preview.applicable);
  const exact = target === "run" ? runActPreviewHtml(preview) : `<details class="bounded-exact-preview"><summary>Exact program preview</summary><div class="run-token"><span>state + ledger + parameter token</span><code>${esc(preview.act_token)}</code></div><p>Observed <code>${esc(preview.state)}</code> at generation ${esc(preview.generation)} and ledger <code>${esc(preview.ledger_head)}</code>.</p><p><strong>lane:</strong> ${esc(preview.operation?.lane || "—")} · <strong>next:</strong> ${esc(programScalar(preview.operation?.next_action))}</p>${(preview.issues || []).map((issue) => `<p class="guard">${esc(issue)}</p>`).join("")}</details>`;
  const refusal = applicable ? "" : boundedFailureDetailsHtml({
    what_happened: (preview.issues || []).join("; ") || "The current saved state refused this preview.",
    what_stayed_unchanged: "Previewing changed no work, permission, cost, or saved event.",
    effect_may_have_occurred: false,
    safe_next_step: "Close this preview and choose only a currently available action.",
    technical_evidence: { action: preview.action, issues: preview.issues || [] },
  }, "Preview refused");
  const titleId = `${target}-act-preview-title`;
  return `<section class="bounded-preview ${applicable ? "" : "refused"}" role="dialog" aria-modal="false" aria-labelledby="${titleId}" tabindex="-1"><div class="bounded-section-head"><div><span>Review before confirmation</span><h3 id="${titleId}">${esc(action?.label || preview.action)}</h3></div>${badge(preview.starts_work ? "may start bounded work" : "one saved action", preview.starts_work ? "warn" : "ok")}</div><dl class="bounded-consequence"><div><dt>What this will do</dt><dd>${esc(consequences.effect || "Apply only this exact reviewed operation.")}</dd></div><div><dt>What it will not do</dt><dd>${esc(consequences.unchanged || "It will not broaden permission or select a different action.")}</dd></div><div><dt>What follows</dt><dd>${esc(consequences.after || "The saved state and receipt will be reloaded.")}</dd></div></dl>${refusal}${exact}<div class="run-consent-actions">${applicable ? `<button type="button" id="${target === "run" ? "run" : "program"}-act-confirm" class="${action?.severity === "danger" ? "danger" : action?.may_start_work ? "starts-work" : ""}">Confirm ${esc(String(action?.label || preview.action).toLowerCase())}</button>` : ""}<button type="button" id="${target === "run" ? "run" : "program"}-act-close">Return without applying</button></div></section>`;
}

function boundedReceiptsHtml(model, result) {
  const receipts = model?.receipts || [];
  const resultHtml = result ? `<article class="bounded-result"><div><span>Just completed</span>${badge("recorded", "ok")}</div><h4>${esc(result.kind || "Bounded action completed")}</h4><p>${esc(result.stop || result.state || result.result || result.decision || "The saved operation completed.")}</p><details><summary>Exact receipt</summary><pre>${esc(JSON.stringify(result, null, 2))}</pre></details></article>` : "";
  return `<section class="bounded-receipts"><div class="bounded-section-head"><div><span>After completion</span><h3>Readable receipts</h3></div>${badge(`${receipts.length + (result ? 1 : 0)} shown`, "ok")}</div><div class="bounded-receipt-grid">${resultHtml}${receipts.map((item) => `<article><div><span>${esc(item.action)}</span>${badge(item.outcome || "recorded", "ok")}</div><h4>${esc(item.label)}</h4><p>${esc(item.at || "time recorded in exact history")}</p><details><summary>Exact receipt</summary><code>${esc(item.exact_reference || "see ordered history")}</code></details></article>`).join("") || (!result ? '<p class="hint">No bounded action receipt has been recorded yet.</p>' : "")}</div></section>`;
}

function boundedActionButtonsHtml(model, target) {
  const actions = model?.actions || [];
  const read = actions.filter((item) => item.kind === "read");
  const controls = actions.filter((item) => item.kind !== "read");
  const controlButton = (item) => {
    const attrs = target === "run"
      ? `data-run-act="${esc(item.action)}" data-run-decision="${esc(item.decision || "")}" data-run-correlation="${esc(item.correlation_id || "")}"`
      : `data-program-act="${esc(item.action)}" data-program-decision="${esc(item.decision || "")}" data-program-request="${esc(item.correlation_id || "")}"`;
    return `<article class="bounded-action-card severity-${esc(item.severity)} ${item.available ? "" : "unavailable"}"><div><span>${esc(item.kind)}</span>${badge(item.available ? "available" : "unavailable", item.available ? "ok" : "warn")}</div><h4>${esc(item.label)}</h4><p>${esc(item.consequences?.effect)}</p><small><strong>Then:</strong> ${esc(item.consequences?.after)}</small>${item.available ? `<button type="button" ${attrs} class="${item.severity === "danger" ? "danger" : item.may_start_work ? "starts-work" : ""}">Review ${esc(item.label.toLowerCase())}</button>` : `<p class="bounded-action-issue">${esc(item.issue)}</p>`}</article>`;
  };
  return `<div class="bounded-read-actions">${read.map((item) => `<button type="button" data-bounded-read="${esc(item.read_action)}"><strong>${esc(item.label)}</strong><span>${esc(item.consequences?.effect)}</span></button>`).join("")}</div><div class="bounded-action-grid">${controls.map(controlButton).join("")}</div>`;
}

function boundedActionCenterHtml(model, preview, error, result, target) {
  if (!model) return "";
  const available = (model.actions || []).filter((item) => item.available);
  const needsReason = available.some((item) => item.reason_required);
  const hasSupervise = available.some((item) => item.action === "supervise");
  const reason = target === "run" ? orchState.controlReason : programState.reason;
  return `<section class="bounded-action-center" aria-labelledby="${esc(target)}-bounded-actions"><div class="bounded-action-hero"><div><span>Actions and decisions</span><h2 id="${esc(target)}-bounded-actions">Understand the consequence, then review one exact action</h2><p>${esc(model.summary)}</p></div>${badge("nothing applies without confirmation", "warn")}</div>
    ${boundedInboxHtml(model)}
    ${boundedPermissionHtml(model)}
    <section class="bounded-choices"><div class="bounded-section-head"><div><span>Available choices</span><h3>Pause, resume, stop, cancel, reject, and continue stay distinct</h3></div></div>${needsReason ? `<label class="run-reason">Why are you taking this action?<input id="${target === "run" ? "run" : "program"}-control-reason" maxlength="${target === "run" ? "200" : "1000"}" value="${esc(reason)}" placeholder="Required for stop and decision actions"></label>` : ""}${hasSupervise ? `<div class="program-ceilings"><label>maximum steps in this pass<input id="program-max-ticks" type="number" min="1" max="10000" value="${esc(programState.maxTicks)}"></label><label>maximum duration (seconds)<input id="program-max-seconds" type="number" min="1" max="86400" value="${esc(programState.maxSeconds)}"></label></div>` : ""}${boundedActionButtonsHtml(model, target)}</section>
    ${boundedErrorHtml(error)}
    ${boundedPreviewHtml(model, preview, target)}
    ${boundedReceiptsHtml(model, result)}
  </section>`;
}

function liveActivityHtml(progress) {
  const activity = progress.activity || [];
  return `<section class="live-panel live-activity"><div class="live-panel-head"><div><span>Readable activity</span><strong>Related work and outcomes grouped together</strong></div>${badge(`${activity.length} groups`)}</div><ol>${activity.map((item) => `<li class="state-${esc(item.status)}"><div><strong>${esc(item.title)}</strong>${badge(item.status, ["active", "complete"].includes(item.status) ? "ok" : ["blocked"].includes(item.status) ? "issue" : "warn")}</div><p>${esc(item.summary || "")}</p>${(item.outcomes || []).length ? `<small>Outcomes: ${esc(item.outcomes.join(", "))}</small>` : ""}</li>`).join("") || "<li><p>No delivery activity has been recorded yet.</p></li>"}</ol></section>`;
}

function liveProgressShell(
  progress,
  connection,
  toolbar,
  actionHtml,
  technicalHtml,
  technicalOpen = false,
  headingLevel = "h2",
) {
  const heading = headingLevel === "h1" ? "h1" : "h2";
  const ordinary = `<section class="live-state-summary state-${esc(progress.status?.group)}"><div><span>Delivery state</span><strong>${esc(progress.status?.label)}</strong><p>${esc(progress.status?.meaning)}</p></div><div><span>Current scope</span><strong>${esc(progress.delivery?.scope || "")}</strong><p>${esc(progress.delivery?.current_story || progress.delivery?.work_id || "")}</p></div></section>
    ${liveAnswerGrid(progress)}
    ${liveNextHtml(progress)}
    ${actionHtml}
    ${liveProgressGroups(progress)}
    <div class="live-two-column">${livePeopleHtml(progress)}${liveReviewHtml(progress)}</div>
    ${liveLimitsHtml(progress)}
    ${liveActivityHtml(progress)}
    <section class="live-recovery state-${esc(progress.recovery?.status)}"><div><span>Recovery truth</span><strong>${esc(progress.recovery?.status === "recovering" ? "Reconciliation in progress" : "Saved history verified")}</strong></div><p>${esc(progress.recovery?.summary || "")}</p><small>${esc(progress.recovery?.duplicate_protection || "")}</small></section>`;
  const technical = `<details class="live-technical"${technicalOpen || LIVE_TECHNICAL_OPEN ? " open" : ""}><summary>Technical details</summary><p class="live-technical-intro">Exact identities, ordered history, hashes, controls, and provenance remain available here.</p>${technicalHtml}</details>`;
  return `<div class="live-delivery" data-live-context="${esc(progress.context)}">
    <header class="live-header"><div><span class="orch-eyebrow">Live delivery</span><${heading}>${esc(progress.title)} ${liveStateBadge(progress)}</${heading}><p>${esc(progress.subtitle)}</p></div>${toolbar}</header>
    ${liveConnectionHtml(connection, progress.recovery)}
    ${LIVE_TECHNICAL_OPEN ? `${technical}${ordinary}` : `${ordinary}${technical}`}
  </div>`;
}

function openLiveTechnical() {
  const details = document.querySelector(".live-technical");
  if (!details) return;
  details.open = true;
  details.scrollIntoView({
    behavior: SNAPSHOT_MODE || matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto" : "smooth",
    block: "start",
  });
  details.querySelector("summary")?.focus();
}

async function handleBoundedRead(action, target) {
  if (action === "reload") {
    if (target === "run") await refreshRunData();
    else await refreshProgramView();
    return;
  }
  if (action === "technical") {
    openLiveTechnical();
    return;
  }
  if (action === "leave") {
    if (target === "run") {
      orchState.runAct = null; orchState.runError = "";
      renderOrchestration();
    } else {
      programState.act = null; programState.error = "";
      renderPrograms();
    }
    return;
  }
  const selector = action === "limits"
    ? '[data-bounded-section="limits"]'
    : '[data-bounded-section="failure"]';
  const section = document.querySelector(selector);
  section?.scrollIntoView({
    behavior: SNAPSHOT_MODE || matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto" : "smooth",
    block: "start",
  });
  section?.querySelector("h3, h4")?.setAttribute("tabindex", "-1");
  section?.querySelector("h3, h4")?.focus();
}

function focusBoundedSnapshot() {
  if (!SNAPSHOT_MODE || !SNAPSHOT_BOUNDED_FOCUS) return;
  const selectors = {
    actions: ".bounded-action-center",
    inbox: ".bounded-inbox",
    limits: ".bounded-permission",
    preview: ".bounded-preview",
    error: ".bounded-failure",
    receipts: ".bounded-receipts",
  };
  const focus = () => {
    const target = document.querySelector(
      selectors[SNAPSHOT_BOUNDED_FOCUS] || ".bounded-action-center"
    );
    if (!target) return;
    const center = target.closest(".bounded-action-center");
    const live = center?.closest(".live-delivery");
    const hero = center?.querySelector(".bounded-action-hero");
    if (center && target !== center && hero) hero.after(target);
    const header = live?.querySelector(".live-header");
    if (center && header) header.after(center);
    const top = target.getBoundingClientRect().top + window.scrollY - 8;
    window.scrollTo({ top: Math.max(0, top), behavior: "auto" });
  };
  focus();
  requestAnimationFrame(() => requestAnimationFrame(focus));
  setTimeout(focus, 100);
}

function runViewHtml() {
  if (orchState.runLoading) return `<div class="orch-run-shell">${stateHtml("Replaying the authoritative run ledger…")}</div>`;
  const error = orchState.runError ? `<div class="guard run-error" role="alert">${esc(orchState.runError)}</div>` : "";
  if (!orchState.runs.length || !orchState.runView) return `<div class="orch-run-shell">${error}${runEmptyHtml()}</div>`;
  const view = orchState.runView;
  const actions = boundedActionCenterHtml(view.bounded_actions, orchState.runAct, orchState.runError, orchState.runResult, "run");
  const toolbar = `<div class="live-toolbar"><label>delivery run<select id="run-select">${orchState.runs.map((item) => `<option value="${esc(item.run_id)}"${item.run_id === view.run_id ? " selected" : ""}>${esc(item.run.story?.id || item.run_id)} · ${esc(item.run.state)}</option>`).join("")}</select></label><button type="button" id="run-refresh">Check for updates</button><button type="button" data-live-technical>Technical details</button></div>`;
  const technical = `<div class="run-summary"><div><span>exact state</span><strong>${esc(view.state)}</strong><small>${esc(view.terminal_meaning)}</small></div><div><span>ledger</span><strong>${esc(view.ledger_events)} events</strong><code>${esc(view.ledger_head)}</code></div><div><span>attempts</span><strong>${esc(view.attempts.active.length)} active · ${esc(view.attempts.completed.length)} complete</strong><small>generation ${esc(view.control_generation)}</small></div><div><span>authority</span><strong>${view.dispatch_allowed ? "dispatch permitted" : "dispatch stopped"}</strong><small>${view.expired ? "grant expired" : "grant fresh by time"}</small></div></div>
    ${runBudgetHtml(view.budgets)}
    <section class="run-panel"><div class="run-panel-head"><div><span>authoritative graph state</span><strong>Why every node is waiting, eligible, active, failed, or complete</strong></div>${badge("inspection is pure", "ok")}</div>${liveRunGraph(view)}</section>
    <section class="run-panel"><div class="run-panel-head"><div><span>executors and fail checks</span><strong>Sessions expose receipts and bounded streams, never prompts or commands</strong></div></div>${runSessionsHtml(view)}${runStreamHtml(orchState.runStream)}</section>
    <section class="run-panel"><div class="run-panel-head"><div><span>declared output conventions</span><strong>Artifact metadata and lineage</strong></div></div>${runArtifactHtml(view)}</section>
    <section class="run-panel"><div class="run-panel-head"><div><span>typed human request ports</span><strong>Outstanding requests, age, origin, schemas, and checkpoint lineage</strong></div>${badge("inspect-only history", "ok")}</div>${runRequestsHtml(view)}</section>
    <section class="run-panel">${runRoutesHtml(view)}</section>
    ${runControlsHtml(view)}
    <section class="run-panel"><div class="run-panel-head"><div><span>operator notifications</span><strong>Derived from the ledger and signal chains; ack is receipted</strong></div>${badge("previews, never tokens", "ok")}</div>${runNotificationsHtml(view)}</section>
    <section class="run-panel"><div class="run-panel-head"><div><span>hash-chained receipts</span><strong>Run ledger timeline</strong></div>${badge("content-safe metadata", "ok")}</div>${runTimelineHtml(view)}</section>`;
  return `<div class="orch-run-shell" data-run-id="${esc(view.run_id)}">${liveProgressShell(view.live_progress, orchState.runConnection, toolbar, actions, technical, Boolean(orchState.runStream))}</div>`;
}

function runNotificationsHtml(view) {
  const items = (orchState.notifications || []).filter(
    (item) => !item.run_id || item.run_id === view.run_id,
  );
  if (!items.length) return `<p class="orch-muted">No derived notifications for this run.</p>`;
  return `<ul class="run-notifications">${items.map((item) => `
    <li>
      <code>${esc(item.kind)}</code> ${item.unread ? badge("unread", "warn") : badge("acked", "ok")}
      ${item.delivered ? badge("delivered", "ok") : badge(`attempts ${esc(item.delivery_attempts)}`, "")}
      <span>${esc(item.detail)}</span>
      ${item.request ? `<small>typed response · correlation <code>${esc(item.request.correlation_id)}</code> · applied only through the local exact-token request boundary</small>` : ""}
      ${item.unread ? `<button type="button" data-ntf-ack="${esc(item.id)}">ack</button>` : ""}
    </li>`).join("")}</ul>`;
}

async function ackNotification(id) {
  const { status, body } = await postJson("/api/notifications/ack", { id });
  if (status === 200) {
    try { orchState.notifications = (await api("/api/notifications")).data.notifications; } catch (err) {}
    renderOrchestration();
  }
}

function orchestrationBody() {
  if (orchState.view === "validate") return validateView();
  if (orchState.view === "json") return jsonView();
  if (orchState.view === "run") return runViewHtml();
  return `<div class="orch-design"><div class="orch-palette" aria-label="node palette">
      <button type="button" data-orch-settings>score settings</button>${ORCH_NODE_TYPES.map((type) => `<button type="button" data-orch-add="${type}">+ ${type}</button>`).join("")}
    </div><div class="orch-workarea">${orchGraph()}</div><aside class="orch-inspector" aria-label="rule inspector">${orchState.selected ? nodeInspector(orchState.score.nodes.find((n) => n.id === orchState.selected)) : scoreInspector()}</aside></div>`;
}

function renderOrchestration() {
  const focus = captureAppFocus();
  const current = orchState.name || orchState.score.slug;
  app.innerHTML = `${destinationNav("delivery", "#/orchestration")}<div class="orchestration" data-score="${esc(current)}">
    <header class="orch-toolbar"><div><span class="orch-eyebrow">Delivery</span><h1>${esc(orchState.score.title || orchState.score.slug)}</h1><p>Review the work and its order before you continue.</p><details><summary>Technical details</summary><span>visual orchestration score</span><code>pm/orchestration/${esc(orchState.score.slug)}.json</code></details></div>
      <div class="orch-score-actions"><label>score<select id="orch-score-select"><option value="">new unsaved score</option>${orchState.inventory.map((s) => `<option value="${esc(s.name)}"${s.name === orchState.name ? " selected" : ""}>${esc(s.slug || s.name)}${s.valid ? "" : " (invalid)"}</option>`).join("")}</select></label><button type="button" id="orch-new">new</button><button type="button" id="orch-duplicate">duplicate</button><button type="button" id="orch-preview-save">preview save</button><button type="button" id="orch-preview-delete" class="danger"${orchState.exists ? "" : " disabled"}>preview delete</button></div>
    </header>
    <div class="orch-tabs" role="tablist" aria-label="Orchestration editor views">${[
      ["design", "Design"], ["validate", "Validate"], ["json", "JSON"], ["run", "Run"],
    ].map(([id, label]) => `<button type="button" id="orch-tab-${id}" role="tab" aria-controls="orch-view" aria-selected="${orchState.view === id}" tabindex="${orchState.view === id ? "0" : "-1"}" data-orch-view="${id}" class="${orchState.view === id ? "active" : ""}">${label}${id === "validate" && orchState.preview && !orchState.preview.valid ? ` (${orchState.preview.validation.diagnostics.length})` : ""}</button>`).join("")}</div>
    <div id="orch-save-panel"></div>
    <div id="orch-view" role="tabpanel" aria-labelledby="orch-tab-${esc(orchState.view)}">${orchestrationBody()}</div>
  </div>`;
  wireOrchestration();
  wireTablist(".orch-tabs");
  finishDynamicRender(focus);
}

async function refreshOrchValidation() {
  if (!orchState.score) return;
  const focus = captureAppFocus();
  const name = orchState.score.slug || orchState.name;
  try {
    const { status, body } = await postJson("/api/orchestration/preview", { action: "save", name, score: orchState.score });
    if (status >= 400 || body.ok === false) throw new Error((body.issues && body.issues[0]) || `compiler preview ${status}`);
    orchState.preview = body.data;
  } catch (err) {
    orchState.preview = { valid: false, validation: { diagnostics: [{ pointer: "/", code: "preview-error", message: err.message, remediation: "repair the score identity or reload" }] } };
  }
  const view = document.getElementById("orch-view");
  if (view && (orchState.view === "validate" || orchState.view === "design")) {
    if (orchState.view === "validate") view.innerHTML = validateView();
    else {
      const errors = diagnosticMap();
      view.querySelectorAll(".orch-node").forEach((group) => {
        group.classList.toggle("has-error", errors.has(group.dataset.nodeId));
      });
      const slot = view.querySelector(".orch-node-errors");
      const selectedErrors = errors.get(orchState.selected) || [];
      if (slot) {
        slot.hidden = !selectedErrors.length;
        slot.innerHTML = selectedErrors.map((d) => `<div><code>${esc(d.pointer)}</code> ${esc(d.message)}</div>`).join("");
      }
    }
    const tab = document.querySelector('[data-orch-view="validate"]');
    if (tab) tab.textContent = `Validate${orchState.preview.valid ? "" : ` (${orchState.preview.validation.diagnostics.length})`}`;
    if (orchState.view === "validate") wireOrchPreflight();
    finishDynamicRender(focus);
  }
}

function queueOrchValidation() {
  clearTimeout(orchState.validationTimer);
  orchState.validationTimer = setTimeout(() => { refreshOrchValidation(); }, SNAPSHOT_MODE ? 0 : 180);
}

function updateOutputFromField(field) {
  const set = field.closest(".orch-output");
  if (!set) return false;
  const node = orchState.score.nodes.find((n) => n.id === orchState.selected);
  const index = Number(set.dataset.outputIndex);
  if (!node || !node.outputs || !node.outputs[index]) return true;
  const out = node.outputs[index];
  const map = {
    output_name: "name", output_format: "format", output_path: "path",
    output_schema: "schema", output_citations: "citations",
  };
  if (map[field.name]) setOptional(out, map[field.name], field.value.trim());
  if (field.name === "output_sections") out.required_sections = splitLines(field.value);
  if (field.name === "output_allowed_paths") out.allowed_paths = splitLines(field.value);
  if (field.name === "output_max_bytes") setOptional(out, "max_bytes", maybeNumber(field.value));
  return true;
}

function updateNodeFromForm(form, changed) {
  let node = orchState.score.nodes.find((n) => n.id === orchState.selected);
  if (!node) return;
  if (updateOutputFromField(changed)) { orchState.jsonDraft = ""; queueOrchValidation(); return; }
  if (changed.name === "type" && changed.value !== node.type) {
    const replacement = defaultOrchNode(changed.value);
    replacement.id = node.id; replacement.needs = node.needs || []; replacement.resource_groups = node.resource_groups || [];
    orchState.score.nodes[orchState.score.nodes.indexOf(node)] = replacement;
    node = replacement; renderOrchestration(); queueOrchValidation(); return;
  }
  if (changed.name === "id") {
    const old = node.id; const next = changed.value.trim();
    node.id = next;
    orchState.score.nodes.forEach((n) => { n.needs = (n.needs || []).map((x) => x === old ? next : x); if (n.on_failure?.node === old) n.on_failure.node = next; });
    if (orchState.score.layout.nodes[old]) { orchState.score.layout.nodes[next] = orchState.score.layout.nodes[old]; delete orchState.score.layout.nodes[old]; }
    orchState.selected = next;
  }
  const direct = ["title", "description", "role", "profile", "prompt", "workspace", "action"];
  if (direct.includes(changed.name)) setOptional(node, changed.name, changed.value.trim());
  if (changed.name === "activation") node.activation = changed.value;
  node.needs = [...form.querySelectorAll('input[name="need"]:checked')].map((x) => x.value);
  if (changed.name === "resource_groups") node.resource_groups = splitLines(changed.value);
  if (changed.name === "timeout_seconds") setOptional(node, "timeout_seconds", maybeNumber(changed.value));
  if (node.type === "agent") {
    node.capabilities = [...form.querySelectorAll('input[name="capability"]:checked')].map((x) => x.value);
    if (changed.name === "context") node.context = splitLines(changed.value);
    if (changed.name === "inputs") node.inputs = parseInputLines(changed.value);
  }
  if (node.type === "collect" && changed.name === "inputs") node.inputs = parseInputLines(changed.value);
  if (node.type === "check") {
    node.runner ||= { kind: "command" };
    const r = node.runner;
    if (changed.name === "runner_kind") { node.runner = { kind: changed.value, timeout_seconds: r.timeout_seconds || 900, output_bytes: r.output_bytes || 30000 }; }
    else if (changed.name === "runner_argv") r.argv = splitLines(changed.value);
    else if (changed.name === "runner_cwd") setOptional(r, "cwd", changed.value.trim());
    else if (changed.name === "runner_name") setOptional(r, "name", changed.value);
    else if (changed.name === "runner_path") setOptional(r, "path", changed.value.trim());
    else if (changed.name === "runner_schema") setOptional(r, "schema", changed.value.trim());
    else if (changed.name === "runner_allowed_paths") r.allowed_paths = splitLines(changed.value);
    else if (changed.name === "runner_timeout") setOptional(r, "timeout_seconds", maybeNumber(changed.value));
    else if (changed.name === "runner_output_bytes") setOptional(r, "output_bytes", maybeNumber(changed.value));
    else if (changed.name === "runner_writes") r.writes = splitLines(changed.value);
    else if (changed.name === "expect_exit_code") node.expect = { exit_code: maybeNumber(changed.value) ?? 0 };
  }
  if (node.type === "approval") {
    if (changed.name === "options") node.options = splitLines(changed.value);
    if (changed.name === "terminal") setOptional(node, "terminal", changed.value);
  }
  if (node.type !== "approval") {
    const action = form.elements.failure_action?.value || "";
    if (!action) delete node.on_failure;
    else {
      const f = { action };
      if (action === "retry") f.max_attempts = maybeNumber(form.elements.failure_max_attempts.value);
      if (action === "route") { f.node = form.elements.failure_node.value; f.max_visits = maybeNumber(form.elements.failure_max_visits.value) || 1; }
      if (action === "approval") f.checkpoint = form.elements.failure_checkpoint.value.trim();
      node.on_failure = f;
    }
  }
  orchState.jsonDraft = ""; queueOrchValidation();
}

function updateScoreFromForm(form, changed) {
  const score = orchState.score;
  if (["slug", "title", "description", "project"].includes(changed.name)) setOptional(score, changed.name, changed.value.trim());
  score.defaults ||= {};
  const defaultNames = ["max_concurrency", "max_wall_seconds", "max_agent_starts", "max_check_starts", "default_timeout_seconds", "max_artifact_bytes"];
  if (defaultNames.includes(changed.name)) setOptional(score.defaults, changed.name, maybeNumber(changed.value));
  score.layout.viewport ||= {};
  if (changed.name.startsWith("viewport_")) score.layout.viewport[changed.name.replace("viewport_", "")] = Number(changed.value);
  if (changed.name === "slug") {
    orchState.name = changed.value.trim();
    orchState.exists = orchState.inventory.some((item) => item.name === orchState.name);
  }
  orchState.jsonDraft = ""; queueOrchValidation();
}

function wireOrchDesign() {
  const form = document.getElementById("orch-node-form");
  if (form) form.addEventListener("input", (e) => updateNodeFromForm(form, e.target));
  const scoreForm = document.getElementById("orch-score-form");
  if (scoreForm) scoreForm.addEventListener("input", (e) => updateScoreFromForm(scoreForm, e.target));
  document.querySelectorAll("[data-orch-add]").forEach((button) => button.addEventListener("click", () => {
    const node = defaultOrchNode(button.dataset.orchAdd); orchState.score.nodes.push(node);
    const count = orchState.score.nodes.length - 1; orchState.score.layout.nodes[node.id] = { x: 70 + (count % 4) * 240, y: 70 + Math.floor(count / 4) * 170 };
    orchState.selected = node.id; renderOrchestration(); queueOrchValidation();
  }));
  document.querySelector("[data-orch-settings]")?.addEventListener("click", () => { orchState.selected = null; renderOrchestration(); });
  document.querySelector("[data-orch-add-output]")?.addEventListener("click", () => {
    const node = orchState.score.nodes.find((n) => n.id === orchState.selected); node.outputs ||= [];
    node.outputs.push({ name: `${node.id}-output-${node.outputs.length + 1}`, format: "markdown", path: `artifacts/${node.id}-${node.outputs.length + 1}.md`, required_sections: [], citations: "none", max_bytes: 30000, allowed_paths: [] });
    renderOrchestration(); queueOrchValidation();
  });
  document.querySelectorAll("[data-orch-remove-output]").forEach((button) => button.addEventListener("click", () => {
    const node = orchState.score.nodes.find((n) => n.id === orchState.selected); node.outputs.splice(Number(button.dataset.orchRemoveOutput), 1); renderOrchestration(); queueOrchValidation();
  }));
  document.querySelector("[data-orch-delete-node]")?.addEventListener("click", () => {
    const id = orchState.selected; orchState.score.nodes = orchState.score.nodes.filter((n) => n.id !== id);
    orchState.score.nodes.forEach((n) => { n.needs = (n.needs || []).filter((x) => x !== id); if (n.on_failure?.node === id) delete n.on_failure; });
    delete orchState.score.layout.nodes[id]; orchState.selected = null; renderOrchestration(); queueOrchValidation();
  });
  document.querySelector("[data-orch-duplicate-node]")?.addEventListener("click", () => {
    const source = orchState.score.nodes.find((n) => n.id === orchState.selected); const copy = clone(source); copy.id = nextNodeId(source.type);
    (copy.outputs || []).forEach((out, i) => { out.name = `${copy.id}-output-${i + 1}`; });
    orchState.score.nodes.push(copy); const pos = orchState.score.layout.nodes[source.id] || { x: 0, y: 0 }; orchState.score.layout.nodes[copy.id] = { x: Number(pos.x) + 40, y: Number(pos.y) + 130 };
    orchState.selected = copy.id; renderOrchestration(); queueOrchValidation();
  });
  const svg = document.getElementById("orch-canvas");
  if (!svg) return;
  svg.querySelectorAll(".orch-node").forEach((group) => {
    group.addEventListener("click", () => { orchState.selected = group.dataset.nodeId; renderOrchestration(); });
    group.addEventListener("keydown", (e) => {
      if (["Enter", " "].includes(e.key)) { e.preventDefault(); orchState.selected = group.dataset.nodeId; renderOrchestration(); return; }
      const delta = { ArrowLeft: [-10, 0], ArrowRight: [10, 0], ArrowUp: [0, -10], ArrowDown: [0, 10] }[e.key];
      if (delta) { e.preventDefault(); const p = orchState.score.layout.nodes[group.dataset.nodeId]; p.x = Number(p.x) + delta[0]; p.y = Number(p.y) + delta[1]; renderOrchestration(); queueOrchValidation(); }
    });
  });
  let drag = null;
  svg.addEventListener("pointerdown", (e) => { const group = e.target.closest?.(".orch-node"); if (!group) return; const p = orchState.score.layout.nodes[group.dataset.nodeId]; drag = { id: group.dataset.nodeId, x: e.clientX, y: e.clientY, px: Number(p.x), py: Number(p.y), group }; svg.setPointerCapture(e.pointerId); });
  svg.addEventListener("pointermove", (e) => { if (!drag) return; const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width || 1; const p = orchState.score.layout.nodes[drag.id]; p.x = Math.max(0, Math.round(drag.px + (e.clientX - drag.x) / scale)); p.y = Math.max(0, Math.round(drag.py + (e.clientY - drag.y) / scale)); drag.group.setAttribute("transform", `translate(${p.x},${p.y})`); });
  svg.addEventListener("pointerup", () => { if (!drag) return; drag = null; renderOrchestration(); queueOrchValidation(); });
}

function renderSavePreview(preview, request) {
  const panel = document.getElementById("orch-save-panel");
  const diagnostics = preview.validation?.diagnostics || [];
  panel.innerHTML = `<section class="orch-save-preview" role="dialog" aria-modal="false" aria-labelledby="orch-preview-title" tabindex="-1"><div class="orch-preview-head"><strong id="orch-preview-title">${esc(preview.action)} preview</strong>${badge(preview.applicable ? "nothing written yet" : "compiler blocked apply", preview.applicable ? "ok" : "issue")}<code>${esc(preview.fingerprint)}</code></div>
    ${diagnostics.length ? `<ol class="orch-diagnostics">${diagnostics.map((d) => `<li><code>${esc(d.pointer)}</code><strong>${esc(d.code)}</strong><span>${esc(d.message)}</span><small>${esc(d.remediation)}</small></li>`).join("")}</ol>` : ""}
    ${preview.diff ? `<pre class="diff">${diffHtml(preview.diff)}</pre>` : `<p class="hint">${preview.no_op ? "No content change." : "No diff is available until the score compiles."}</p>`}
    <div class="orch-preview-actions">${preview.applicable ? `<button type="button" id="orch-apply-score">apply exact ${esc(preview.action)} — no run, stage, or commit</button>` : ""}<button type="button" id="orch-close-preview">close</button></div></section>`;
  const close = () => {
    panel.innerHTML = "";
    restoreReturnFocus("orch-save", "#orch-preview-save");
  };
  document.getElementById("orch-close-preview").addEventListener("click", close);
  document.getElementById("orch-apply-score")?.addEventListener("click", async (e) => {
    e.currentTarget.disabled = true;
    const { status, body } = await postJson("/api/orchestration/apply", { ...request, fingerprint: preview.fingerprint });
    if (status === 409) { panel.innerHTML = '<div class="guard">stale score preview refused — nothing was written. Preview the current score again.</div>'; return; }
    if (status >= 400 || body.ok === false) { panel.innerHTML = `<div class="guard">${esc((body.issues && body.issues[0]) || `apply failed (${status})`)}</div>`; return; }
    if (request.action === "delete") { location.hash = "#/orchestration"; await viewOrchestration(); return; }
    orchState.exists = true; orchState.name = request.name; location.hash = `#/orchestration/${encodeURIComponent(request.name)}`; await viewOrchestration(request.name);
  });
  enhanceSemantics(panel);
  wireDismissibleRegion(".orch-save-preview", close, "orch-save", "#orch-preview-save");
  focusRegion(".orch-save-preview");
}

async function previewScoreAction(action, trigger = document.activeElement) {
  rememberReturnFocus("orch-save", trigger);
  const request = action === "delete" ? { action, name: orchState.name } : { action, name: orchState.score.slug, score: orchState.score };
  const panel = document.getElementById("orch-save-panel"); panel.innerHTML = stateHtml(`Building exact ${action} preview…`);
  const { status, body } = await postJson("/api/orchestration/preview", request);
  if (status >= 400 || body.ok === false) { panel.innerHTML = `<div class="guard">${esc((body.issues && body.issues[0]) || `preview failed (${status})`)}</div>`; return; }
  renderSavePreview(body.data, request);
}

function wireJsonView() {
  const text = document.getElementById("orch-json-text");
  text?.addEventListener("input", () => { orchState.jsonDraft = text.value; });
  document.getElementById("orch-json-to-graph")?.addEventListener("click", async () => {
    const error = document.getElementById("orch-json-error");
    try { const parsed = JSON.parse(text.value); orchState.score = ensureOrchShape(parsed); orchState.name = parsed.slug || ""; orchState.selected = null; orchState.jsonDraft = ""; orchState.view = "design"; renderOrchestration(); await refreshOrchValidation(); }
    catch (err) { error.hidden = false; error.textContent = `JSON refused: ${err.message}`; }
  });
  document.getElementById("orch-import")?.addEventListener("change", async (e) => {
    const file = e.target.files[0]; if (!file) return; text.value = await file.text(); orchState.jsonDraft = text.value;
  });
}

function selectScoreRuns() {
  const slug = orchState.score?.slug;
  orchState.runs = (orchState.runInventory || []).filter((item) => item.valid && item.run?.score?.slug === slug);
  if (!orchState.runs.some((item) => item.run_id === orchState.runId)) {
    orchState.runId = orchState.runs.length ? orchState.runs[orchState.runs.length - 1].run_id : "";
    orchState.runView = null;
  }
}

async function refreshRunData() {
  const previousView = orchState.runView;
  const focus = captureAppFocus();
  orchState.runLoading = true;
  orchState.runError = "";
  orchState.runConnection.status = "checking";
  if (!previousView) renderOrchestration();
  try {
    const inventory = await api("/api/runs");
    orchState.runInventory = inventory.data.runs || [];
    selectScoreRuns();
    orchState.runView = orchState.runId ? (await api(`/api/runs/${encodeURIComponent(orchState.runId)}/view`)).data : null;
    orchState.runConnection.status = SNAPSHOT_LIVE_STATE === "stale" ? "stale" : SNAPSHOT_MODE ? "verified" : "checking";
    try { orchState.notifications = (await api("/api/notifications")).data.notifications; }
    catch (err) { orchState.notifications = []; }
  } catch (err) {
    orchState.runError = err.message;
    orchState.runView = previousView;
    orchState.runConnection.status = previousView ? "stale" : "manual";
  } finally {
    orchState.runLoading = false;
    renderOrchestration();
    restoreAppFocus(focus);
  }
  const version = String(orchState.runView?.ledger_head || "");
  if (liveAnnouncementKeys.has("run")) {
    announceLiveUpdate(
      "run",
      version,
      "Delivery progress changed. Review What happens next or check the saved history.",
    );
  } else if (version) {
    liveAnnouncementKeys.set("run", version);
  }
  startRunLive();
}

/* Live ledger tail (SSE, read-only). Any arriving ledger event triggers
   one debounced re-read of the same run-view read model; if the stream
   is unavailable the explicit refresh button remains the fallback. */
let runLive = null;
let runLiveTimer = null;

function stopRunLive() {
  if (runLive) { runLive.close(); runLive = null; }
  if (runLiveTimer) { clearTimeout(runLiveTimer); runLiveTimer = null; }
}

function startRunLive() {
  stopRunLive();
  if (!orchState.runId || orchState.view !== "run") return;
  if (SNAPSHOT_MODE || typeof EventSource === "undefined") {
    if (SNAPSHOT_LIVE_STATE !== "stale") orchState.runConnection.status = SNAPSHOT_MODE ? "verified" : "manual";
    renderOrchestration();
    return;
  }
  const runId = orchState.runId;
  runLive = new EventSource(`/api/runs/${encodeURIComponent(runId)}/events`);
  runLive.onopen = () => {
    if (orchState.runId !== runId || orchState.view !== "run") return;
    orchState.runConnection.status = "live";
    renderOrchestration();
  };
  runLive.addEventListener("ledger", () => {
    if (runLiveTimer) return;
    runLiveTimer = setTimeout(async () => {
      runLiveTimer = null;
      if (orchState.runId !== runId || orchState.view !== "run") return;
      try {
        orchState.runView = (await api(`/api/runs/${encodeURIComponent(runId)}/view`)).data;
        orchState.runConnection.status = "live";
        try { orchState.notifications = (await api("/api/notifications")).data.notifications; }
        catch (err) { /* notifications stay stale until the next refresh */ }
        announceLiveUpdate(
          "run",
          orchState.runView?.ledger_head,
          "Delivery progress changed. Review What happens next or check the saved history.",
        );
        renderOrchestration();
      } catch (err) {
        orchState.runConnection.status = "stale";
        announceLiveUpdate(
          "run-connection",
          `stale:${runId}:${orchState.runView?.ledger_head || ""}`,
          "Live delivery updates were interrupted. The last verified view remains available.",
        );
        renderOrchestration();
      }
    }, 400);
  });
  runLive.onerror = () => {
    orchState.runConnection.status = "stale";
    stopRunLive();
    announceLiveUpdate(
      "run-connection",
      `stale:${runId}:${orchState.runView?.ledger_head || ""}`,
      "Live delivery updates were interrupted. The last verified view remains available.",
    );
    renderOrchestration();
  };
}

async function previewRunGrant(form) {
  rememberReturnFocus("run-plan");
  const values = Object.fromEntries(new FormData(form).entries());
  const minutes = Math.max(1, Math.min(1440, Number(values.minutes) || 60));
  orchState.grantDraft = { project: String(values.project || "").trim(), story: String(values.story || "").trim(), operator: String(values.operator || "").trim(), minutes };
  orchState.runError = ""; orchState.runPlan = null; renderOrchestration();
  const issued = new Date(); const expires = new Date(issued.getTime() + minutes * 60_000);
  const params = new URLSearchParams({ score: orchState.score.slug, project: orchState.grantDraft.project, story: orchState.grantDraft.story, issued_at: issued.toISOString(), expires_at: expires.toISOString() });
  try { orchState.runPlan = (await api(`/api/run-plan?${params}`)).data; }
  catch (err) { orchState.runError = err.message; }
  renderOrchestration();
  if (orchState.runPlan) focusRegion(".run-consent");
}

async function confirmRunGrant() {
  const plan = orchState.runPlan;
  if (!plan?.applicable) return;
  const request = {
    score: plan.request.score, project: plan.request.project, story: plan.request.story,
    issued_at: plan.request.issued_at, expires_at: plan.request.expires_at,
    expect: plan.start_token, approve: true, operator: orchState.grantDraft.operator,
  };
  orchState.runLoading = true; renderOrchestration();
  const { status, body } = await postJson("/api/runs/start", request);
  orchState.runLoading = false;
  if (status === 409) { orchState.runPlan = null; orchState.runError = "Stale grant preview refused. Repository, score, story, or time facts changed; build a fresh preview."; renderOrchestration(); return; }
  if (status >= 400 || body.ok === false) { orchState.runError = (body.issues && body.issues[0]) || `run start failed (${status})`; renderOrchestration(); return; }
  orchState.runId = body.data.run_id; orchState.runPlan = null; await refreshRunData();
}

async function previewRunAct(action, decision, correlation, trigger = document.activeElement) {
  rememberReturnFocus("run-act", trigger);
  const control = (orchState.runView?.controls || []).find((item) => item.action === action && String(item.decision || "") === String(decision || "") && String(item.correlation_id || "") === String(correlation || ""));
  const reason = control?.reason_required ? orchState.controlReason.trim() : "";
  orchState.runAct = null; orchState.runError = ""; orchState.runResult = null; renderOrchestration();
  const { status, body } = await postJson("/api/runs/preview", { run_id: orchState.runId, action, ...(reason ? { reason } : {}), ...(decision ? { decision } : {}), ...(correlation ? { correlation_id: correlation } : {}) });
  if (status >= 400 || body.ok === false) { orchState.runError = (body.issues && body.issues[0]) || `run preview failed (${status})`; }
  else orchState.runAct = body.data;
  renderOrchestration();
  if (orchState.runAct) focusRegion(".bounded-preview");
}

async function confirmRunAct() {
  const preview = orchState.runAct;
  if (!preview?.applicable) return;
  const request = { run_id: preview.run_id, expect: preview.act_token, ...(preview.reason ? { reason: preview.reason } : {}), ...(preview.decision ? { decision: preview.decision } : {}), ...(preview.correlation_id ? { correlation_id: preview.correlation_id } : {}) };
  orchState.runLoading = true; renderOrchestration();
  const { status, body } = await postJson(`/api/runs/${encodeURIComponent(preview.action)}`, request);
  orchState.runLoading = false;
  if (status === 409) { orchState.runAct = null; orchState.runError = "Stale run act refused before work or ledger change. Refresh once and preview the current state."; renderOrchestration(); return; }
  if (status >= 400 || body.ok === false) { orchState.runError = (body.issues && body.issues[0]) || `run act failed (${status})`; renderOrchestration(); return; }
  orchState.runResult = body.data; orchState.runAct = null; orchState.controlReason = ""; await refreshRunData();
}

async function openRunStream(button) {
  rememberReturnFocus("run-stream", button);
  orchState.runStream = null; renderOrchestration();
  const path = `/api/runs/${encodeURIComponent(orchState.runId)}/streams/${encodeURIComponent(button.dataset.executor)}/${encodeURIComponent(button.dataset.executionId)}/${encodeURIComponent(button.dataset.runStream)}?max_bytes=20000`;
  try { orchState.runStream = (await api(path)).data; }
  catch (err) { orchState.runError = err.message; }
  renderOrchestration();
  if (orchState.runStream) focusRegion(".run-open-stream");
}

function wireRunView() {
  document.getElementById("run-refresh")?.addEventListener("click", refreshRunData);
  document.querySelector("[data-live-technical]")?.addEventListener("click", openLiveTechnical);
  document.getElementById("run-select")?.addEventListener("change", async (event) => { orchState.runId = event.target.value; orchState.runAct = null; orchState.runResult = null; orchState.runStream = null; await refreshRunData(); });
  document.getElementById("run-grant-form")?.addEventListener("submit", (event) => { event.preventDefault(); previewRunGrant(event.currentTarget); });
  document.getElementById("run-start-confirm")?.addEventListener("click", confirmRunGrant);
  const closePlan = () => {
    orchState.runPlan = null;
    renderOrchestration();
    restoreReturnFocus("run-plan", "#run-grant-form button[type='submit']");
  };
  document.getElementById("run-plan-close")?.addEventListener("click", closePlan);
  document.getElementById("run-control-reason")?.addEventListener("input", (event) => { orchState.controlReason = event.target.value; });
  document.querySelectorAll("[data-run-act]").forEach((button) => button.addEventListener("click", () => previewRunAct(button.dataset.runAct, button.dataset.runDecision, button.dataset.runCorrelation, button)));
  document.getElementById("run-act-confirm")?.addEventListener("click", confirmRunAct);
  const closeAct = () => {
    orchState.runAct = null;
    renderOrchestration();
    restoreReturnFocus("run-act");
  };
  document.getElementById("run-act-close")?.addEventListener("click", closeAct);
  document.querySelectorAll("[data-bounded-read]").forEach((button) => button.addEventListener("click", () => handleBoundedRead(button.dataset.boundedRead, "run")));
  document.querySelectorAll("[data-run-stream]").forEach((button) => button.addEventListener("click", () => openRunStream(button)));
  document.querySelectorAll("[data-ntf-ack]").forEach((button) => button.addEventListener("click", () => ackNotification(button.dataset.ntfAck)));
  const closeStream = () => {
    orchState.runStream = null;
    renderOrchestration();
    restoreReturnFocus("run-stream");
  };
  document.getElementById("run-stream-close")?.addEventListener("click", closeStream);
  wireDismissibleRegion(".run-consent", closePlan, "run-plan", "#run-grant-form button[type='submit']");
  wireDismissibleRegion(".bounded-preview", closeAct, "run-act");
  wireDismissibleRegion(".run-open-stream", closeStream, "run-stream");
}

function wireOrchPreflight() {
  document.getElementById("preflight-open-start")?.addEventListener("click", async () => {
    orchState.view = "run";
    orchState.runError = "";
    renderOrchestration();
    if (!orchState.runView) await refreshRunData();
  });
}

function wireOrchestration() {
  document.querySelectorAll("[data-orch-view]").forEach((button) => button.addEventListener("click", async () => {
    orchState.view = button.dataset.orchView; orchState.runError = ""; renderOrchestration();
    if (orchState.view === "run" && !orchState.runView) await refreshRunData();
  }));
  document.getElementById("orch-score-select")?.addEventListener("change", (e) => { location.hash = e.target.value ? `#/orchestration/${encodeURIComponent(e.target.value)}` : "#/orchestration"; });
  document.getElementById("orch-new")?.addEventListener("click", () => { orchState.score = minimalScore(); orchState.name = orchState.score.slug; orchState.exists = false; orchState.selected = null; orchState.preview = null; renderOrchestration(); queueOrchValidation(); });
  document.getElementById("orch-duplicate")?.addEventListener("click", () => { const used = new Set(orchState.inventory.map((s) => s.name)); let slug = `${orchState.score.slug}-copy`; let i = 2; while (used.has(slug)) slug = `${orchState.score.slug}-copy-${i++}`; orchState.score = clone(orchState.score); orchState.score.slug = slug; orchState.score.title = `${orchState.score.title} copy`; orchState.name = slug; orchState.exists = false; orchState.selected = null; renderOrchestration(); queueOrchValidation(); });
  document.getElementById("orch-preview-save")?.addEventListener("click", () => previewScoreAction("save"));
  document.getElementById("orch-preview-delete")?.addEventListener("click", () => previewScoreAction("delete"));
  if (orchState.view === "design") wireOrchDesign();
  if (orchState.view === "json") wireJsonView();
  if (orchState.view === "run") wireRunView();
  if (orchState.view === "validate") wireOrchPreflight();
  document.querySelectorAll(".orch-diagnostics [data-pointer], .orch-diagnostics li[data-pointer]").forEach((item) => item.addEventListener("click", () => { const match = item.dataset.pointer?.match(/^\/nodes\/(\d+)/); if (match && orchState.score.nodes[Number(match[1])]) { orchState.selected = orchState.score.nodes[Number(match[1])].id; orchState.view = "design"; renderOrchestration(); } }));
}

async function viewOrchestration(name) {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "orchestration" }, ...(name ? [{ label: name }] : [])]);
  const [inventoryBody, runInventoryBody] = await Promise.all([api("/api/orchestration"), api("/api/runs")]);
  orchState.inventory = inventoryBody.data.scores;
  orchState.runInventory = runInventoryBody.data.runs || [];
  if (name) {
    const body = await api(`/api/orchestration/${encodeURIComponent(name)}`);
    orchState.name = body.data.name; orchState.score = ensureOrchShape(clone(body.data.raw)); orchState.exists = true; orchState.preview = {
      valid: body.data.validation.valid, validation: body.data.validation,
      compiled: body.data.compiled, simulation: body.data.simulation,
    };
  } else if (orchState.inventory.length) {
    const first = orchState.inventory[0].name; const body = await api(`/api/orchestration/${encodeURIComponent(first)}`);
    orchState.name = body.data.name; orchState.score = ensureOrchShape(clone(body.data.raw)); orchState.exists = true; orchState.preview = { valid: body.data.validation.valid, validation: body.data.validation, compiled: body.data.compiled, simulation: body.data.simulation };
  } else {
    orchState.score = minimalScore(); orchState.name = orchState.score.slug; orchState.exists = false; orchState.preview = null;
  }
  orchState.selected = null; orchState.jsonDraft = "";
  orchState.runAct = null; orchState.runResult = null; orchState.runError = "";
  selectScoreRuns();
  const requestedView = new URLSearchParams(location.search).get("orchview");
  if (["design", "validate", "json", "run"].includes(requestedView)) orchState.view = requestedView;
  if (orchState.view === "run" && orchState.runId) {
    try {
      orchState.runView = (await api(`/api/runs/${encodeURIComponent(orchState.runId)}/view`)).data;
      orchState.runConnection.status = SNAPSHOT_LIVE_STATE === "stale" ? "stale" : SNAPSHOT_MODE ? "verified" : "checking";
      if (SNAPSHOT_MODE && SNAPSHOT_BOUNDED_PREVIEW) {
        const control = (orchState.runView.controls || []).find((item) => item.available && (
          SNAPSHOT_BOUNDED_PREVIEW === "decision"
            ? item.action === "request" && item.decision === "approve"
            : item.action === SNAPSHOT_BOUNDED_PREVIEW
        ));
        if (control) {
          orchState.controlReason = control.reason_required
            ? "Review this deterministic viewport action."
            : "";
          const response = await postJson("/api/runs/preview", {
            run_id: orchState.runId,
            action: control.action,
            ...(orchState.controlReason ? { reason: orchState.controlReason } : {}),
            ...(control.decision ? { decision: control.decision } : {}),
            ...(control.correlation_id ? { correlation_id: control.correlation_id } : {}),
          });
          if (response.status < 400 && response.body.ok !== false) {
            orchState.runAct = response.body.data;
          }
        }
      }
      if (SNAPSHOT_MODE && SNAPSHOT_BOUNDED_ERROR) {
        orchState.runError = SNAPSHOT_BOUNDED_ERROR === "stale"
          ? "Stale run action refused before work or saved event change. Reload once and review the current action."
          : "The action response ended without a confirmed receipt.";
      }
    }
    catch (err) { orchState.runError = err.message; orchState.runView = null; }
    startRunLive();
  }
  renderOrchestration();
  focusBoundedSnapshot();
  await refreshOrchValidation();
  focusBoundedSnapshot();
}

/* ── autonomous program control room (WLA-26-11) ─────────────────
 * This browser view renders the canonical /api/programs documents. It does
 * not infer scheduling or authority. A live tail is opened only while one
 * explicit run route is active, and every act crosses preview + exact-token
 * confirmation before the server delegates to the shared program surface. */

let programState = {
  inventory: null, runId: "", view: null, plan: null, planRequest: null,
  act: null, stream: null, result: null, error: "", loading: false,
  reason: "", maxTicks: 100, maxSeconds: 300, notifications: [],
  connection: { status: SNAPSHOT_LIVE_STATE === "stale" ? "stale" : "checking" },
};
let programLive = null;
let programLiveTimer = null;

function stopProgramLive() {
  if (programLive) { programLive.close(); programLive = null; }
  if (programLiveTimer) { clearTimeout(programLiveTimer); programLiveTimer = null; }
}

function programScalar(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function programStateBadge(state) {
  const token = String(state || "unknown");
  const cls = ["running", "ready", "complete", "succeeded"].includes(token) ? "ok"
    : ["revoked", "cancelled", "exhausted", "stopped", "failed", "corrupt"].includes(token) ? "issue"
      : ["checkpoint", "paused", "expired", "waiting"].includes(token) ? "warn" : "";
  return badge(token, cls);
}

function programInventoryHtml() {
  const inventory = programState.inventory || { programs: [], runs: [], healthy: true };
  const programs = inventory.programs || [];
  const runs = inventory.runs || [];
  return `<div class="program-inventory" data-healthy="${inventory.healthy ? "true" : "false"}">
    <header class="program-room-toolbar"><div><span class="orch-eyebrow">delivery options · review first</span><h1>Optional multi-phase delivery</h1><p>Review saved delivery plans and live progress. Opening this view starts no work and changes no saved delivery state.</p></div>${badge(inventory.healthy ? "ready" : "needs attention", inventory.healthy ? "ok" : "issue")}</header>
    <section class="program-room-grid" aria-label="delivery plans">${programs.map((item) => `<article class="program-card"><div><span>delivery plan</span>${item.valid ? badge("ready to review", "ok") : badge("needs repair", "issue")}</div><h2>${esc(item.title || item.slug || item.name)}</h2><p>${item.valid ? "This plan can be reviewed for a separate start." : "Resolve the listed plan issue before starting a delivery."}</p><details><summary>Technical details</summary><code>${esc(item.path)}</code><p>${item.valid ? `Exact fingerprint: <code>${esc(item.semantic_hash)}</code>` : esc((item.diagnostics || []).map((d) => d.message).join("; "))}</p></details></article>`).join("") || '<article class="program-empty"><h2>No optional delivery plan</h2><p>Ordinary roadmap work remains available. Nothing is running or waiting here.</p></article>'}</section>
    ${programs.length ? programStartHtml(programs) : ""}
    <section class="program-panel"><div class="program-panel-head"><div><span>live delivery</span><strong>${runs.length} saved deliver${runs.length === 1 ? "y" : "ies"}</strong></div>${badge("read only", "ok")}</div>
      <div class="program-room-grid">${runs.map((item) => `<article class="program-card"><div><span>progress</span>${programStateBadge(item.operational_state)}</div><h2>${esc(item.program || "Optional delivery")}</h2><p>${item.stop ? `Blocker: ${esc(item.stop)}.` : `${esc(item.outstanding_requests || 0)} decision${Number(item.outstanding_requests || 0) === 1 ? "" : "s"} waiting; ${esc(item.blocking_obligations || 0)} blocking follow-up${Number(item.blocking_obligations || 0) === 1 ? "" : "s"}.`}</p><a href="#/programs/${encodeURIComponent(item.run_id)}">Open live delivery</a><details><summary>Technical details</summary><code>${esc(item.run_id)}</code><p>Exact state: ${esc(item.state)} · mode: ${esc(item.mode || "—")} · expiry: ${esc(item.expires_at || "—")}</p></details></article>`).join("") || '<article class="program-empty"><h2>No live optional delivery</h2><p>Reviewing this page does not create one.</p></article>'}</div>
    </section>
  </div>`;
}

function programStartHtml(programs) {
  const plan = programState.plan;
  const request = programState.planRequest || {};
  const modeLabels = { continuous: "Continue within limits", checkpointed: "Pause at decisions", advisory: "Advice only" };
  return `<section class="program-start"><div><span class="orch-eyebrow">review before start</span><h2>Review optional delivery permission</h2><p>Choose the delivery plan, accountable operator, pace, lifetime, and reason. This review starts no work; confirmation remains separate.</p></div>
    <form id="program-plan-form" class="program-plan-form">
      <label>delivery plan<select name="program">${programs.filter((item) => item.valid).map((item) => `<option value="${esc(item.name)}"${request.program === item.name ? " selected" : ""}>${esc(item.title || item.slug || item.name)}</option>`).join("")}</select></label>
      <label>delivery pace<select name="mode">${["continuous", "checkpointed", "advisory"].map((mode) => `<option value="${mode}"${request.mode === mode ? " selected" : ""}>${esc(modeLabels[mode])}</option>`).join("")}</select></label>
      <label>accountable operator<input name="operator" required maxlength="200" value="${esc(request.operator || "")}" placeholder="accountable person or agent"></label>
      <label>permission lifetime in minutes<input name="minutes" type="number" min="1" max="1440" value="${esc(request.minutes || 60)}"></label>
      <label class="program-plan-reason">delivery reason<input name="reason" required maxlength="1000" value="${esc(request.reason || "")}" placeholder="one-line reviewed intent"></label>
      <button type="submit">Review this delivery</button>
    </form>
    ${plan ? `<section class="program-consent ${plan.applicable ? "" : "refused"}" role="dialog" aria-modal="false" aria-labelledby="program-plan-title" tabindex="-1"><div class="program-consent-head"><div><span>start review</span><strong id="program-plan-title">${esc(plan.program?.title || plan.program?.slug || request.program)}</strong></div>${badge(plan.applicable ? "ready for confirmation" : "blocked", plan.applicable ? "ok" : "issue")}</div>
      <div class="program-facts"><div><span>work</span><strong>${esc(plan.selection?.story?.id || plan.selection?.story || "—")}</strong></div><div><span>team</span><strong>${esc(plan.roster?.team || "—")}</strong></div><div><span>permission ends</span><strong>${esc(plan.request?.expires_at || request.expires_at)}</strong></div><div><span>allowed action types</span><strong>${esc((plan.authority?.capabilities || []).length)}</strong></div></div>
      ${(plan.issues || []).map((issue) => `<p class="guard">${esc(typeof issue === "object" ? issue.message || issue.code : issue)}</p>`).join("")}
      <details><summary>Technical details</summary><div class="run-token"><span>Exact start confirmation</span><code>${esc(plan.start_token)}</code></div><pre>${esc(JSON.stringify({ kind: plan.kind, mode: plan.mode, authority: plan.authority, request: plan.request }, null, 2))}</pre></details>
      <div class="run-consent-actions">${plan.applicable ? '<button type="button" id="program-start-confirm">Confirm this reviewed delivery</button>' : ""}<button type="button" id="program-plan-close">Cancel review</button></div>
    </section>` : ""}
  </section>`;
}

function programWhyHtml(view) {
  return `<section class="program-panel program-why"><div class="program-panel-head"><div><span>why this frontier</span><strong>Selection, workflow, team, and next derivable act</strong></div>${badge("ledger-derived", "ok")}</div>
    <div class="program-why-grid"><article><span>story</span><strong>${esc(programScalar(view.current?.selection?.story || view.current?.lineage?.story))}</strong><p>${esc(programScalar(view.why?.story))}</p></article><article><span>phase</span><strong>${esc(programScalar(view.current?.selection?.phase || view.current?.lineage?.phase))}</strong><p>${esc(programScalar(view.why?.phase))}</p></article><article><span>workflow / team</span><strong>${esc(programScalar(view.why?.workflow))} · ${esc(programScalar(view.why?.team))}</strong><p>${esc(programScalar(view.current?.lineage))}</p></article><article><span>next or refusal</span><strong>${esc(programScalar(view.current?.next_action?.kind || view.current?.stop || view.state))}</strong><p>${esc(programScalar(view.why?.next))}</p></article></div>
  </section>`;
}

function programOrganizationHtml(view) {
  const org = view.organization || { roles: [], councils: [] };
  const team = view.team_review || { sections: [], responsibilities: [], quality_constraints: [] };
  const proven = team.runtime_independence?.status === "proven";
  return `<section class="program-panel program-team-review" data-team-review-context="${esc(team.context || "legacy")}"><div class="program-panel-head"><div><span>team and review</span><strong>${esc(team.title || `${org.slug} · ${org.team}`)}</strong></div>${badge(proven ? "runtime independence proven" : "needs attention", proven ? "ok" : "issue")}</div>
    <p class="program-team-summary">${esc(team.summary || "Live team ownership and review.")}</p>
    <div class="program-team-answers">${(team.sections || []).map((section) => `<article><span>${esc(section.question)}</span><strong>${esc(section.label)}</strong><p>${esc(section.answer)}</p></article>`).join("")}</div>
    <div class="program-team-responsibilities">${(team.responsibilities || []).map((role) => `<article><div><strong>${esc(role.label)}</strong>${programStateBadge(role.assigned?.activity || "waiting")}</div><p>${esc(role.responsibility)}</p><span>${esc(role.coverage)}</span><small>${esc(role.outcomes)}</small></article>`).join("")}</div>
    <div class="program-team-constraints">${(team.quality_constraints || []).map((item) => `<article class="${item.status === "runtime-proven" ? "ready" : "issue"}"><div><strong>${esc((item.labels || []).join(" ↔ "))}</strong>${badge(item.status === "runtime-proven" ? "separate now" : "not proven", item.status === "runtime-proven" ? "ok" : "issue")}</div><p>${esc(item.runtime_claim)}</p></article>`).join("")}</div>
    <details class="program-team-technical"><summary>Technical details: exact seats, providers, models, identities, work areas, and sessions</summary>
      <p>Provider or model diversity is not identity independence. Principal, profile, work area, session binding, and read-only review remain separate exact facts.</p>
      <div class="tablewrap"><table class="run-table program-role-table"><thead><tr><th>seat / duty</th><th>agent</th><th>execution port</th><th>identity boundary</th><th>work area / session</th><th>activity</th></tr></thead><tbody>${(org.roles || []).map((seat) => { const x = seat.execution || {}; return `<tr><td><code>${esc(seat.address)}</code><br>${esc(seat.role)} · ${esc(seat.duty)}</td><td>${esc(seat.agent)}<br><small>${esc(seat.profile)}</small></td><td><strong>${esc(x.harness || "—")} / ${esc(x.adapter || "—")}</strong><br><small>${esc(x.provider || "—")} · ${esc(x.model || x.model_family || "—")}</small></td><td><code>${esc(x.auth_domain_fingerprint || "—")}</code><br><small>principal ${esc(seat.principal_fingerprint)}</small></td><td><code>${esc(seat.workspace_domain || "—")}</code><br><small>${esc(seat.session_binding_key || "—")}</small></td><td>${programStateBadge(seat.activity)}<br><small>${esc(programScalar(seat.last_result))}</small></td></tr>`; }).join("")}</tbody></table></div>
      <div class="program-councils"><section><h3>decision groups / exact authority</h3>${(org.councils || []).map((council) => `<article><div><strong>${esc(council.id)}</strong>${badge(council.primary_authority || council.method, council.primary_authority === "judge" ? "warn" : "ok")}</div><p>${esc((council.members || []).join(", "))} · required agreement ${esc(council.quorum)} · tie ${esc(council.tie_authority)}</p><small>chair ${esc(council.chair_seat || "rule")} · decider ${esc(council.decider_seat || "deterministic rule")}</small></article>`).join("") || '<p class="hint">No decision group is assigned to this scope.</p>'}</section><section><h3>separation facts</h3><pre>${esc(JSON.stringify(org.separation || {}, null, 2))}</pre></section></div>
    </details>
  </section>`;
}

function programActivityHtml(view) {
  const nodes = view.graph?.nodes || [];
  const sessions = view.activities?.sessions || [];
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const depth = (node) => { let value = 0; let parent = node.parent; const seen = new Set(); while (parent && byId.has(parent) && !seen.has(parent)) { seen.add(parent); value += 1; parent = byId.get(parent).parent; } return value; };
  return `<section class="program-panel"><div class="program-panel-head"><div><span>nested execution</span><strong>Compiled activity lineage and live session receipts</strong></div>${badge(`${nodes.length} activities`)}</div>
    <div class="tablewrap"><table class="run-table"><thead><tr><th>address</th><th>kind / role</th><th>state</th><th>result</th></tr></thead><tbody>${nodes.map((node) => `<tr><td style="padding-left:${10 + depth(node) * 18}px"><code>${esc(node.address || node.id)}</code></td><td>${esc(node.kind)} · ${esc(node.role || "system")}</td><td>${programStateBadge(node.state)}</td><td>${esc(programScalar(node.result))}</td></tr>`).join("") || '<tr><td colspan="4">No conductor activity has completed. The first tick remains an explicit act.</td></tr>'}</tbody></table></div>
    <div class="program-sessions">${sessions.map((session) => `<article><div><strong>${esc(session.profile)} · ${esc(session.adapter)}</strong>${programStateBadge(session.state)}</div><code>${esc(session.session_id || session.operation_id)}</code><p>${esc(programScalar(session.activity))}</p><div>${["stdout", "stderr"].filter((stream) => Number(session[`${stream}_bytes`] || 0) > 0).map((stream) => `<button type="button" data-program-stream="${stream}" data-session-id="${esc(session.session_id)}">open ${stream} · ${esc(session[`${stream}_bytes`])} B</button>`).join("")}</div></article>`).join("") || '<p class="hint">No driver session has crossed an execution port.</p>'}</div>
    ${programStreamHtml(programState.stream)}
  </section>`;
}

function programStreamHtml(stream) {
  if (!stream) return "";
  return `<section class="program-open-stream" role="dialog" aria-modal="false" aria-labelledby="program-stream-title" tabindex="-1"><div><strong id="program-stream-title">${esc(stream.session_id)} · ${esc(stream.stream)}</strong><button type="button" id="program-stream-close">close explicit stream</button></div><small>${esc(stream.included_bytes)} / ${esc(stream.bytes)} bytes · ${stream.truncated ? "truncated" : "complete"} · ${esc(stream.sha256)}</small><pre>${esc(stream.content)}</pre></section>`;
}

function programQualityHtml(view) {
  const artifactRows = (view.artifacts || []).map((item) => `<tr><td><code>${esc(item.name || item.artifact_id)}</code></td><td>${esc(item.artifact_kind || "artifact")}</td><td>${esc(item.bytes || 0)} B</td><td><code>${esc(item.sha256 || item.ref || "—")}</code></td></tr>`).join("");
  const resultItems = (items, empty) => items.map((item) => `<li><div><strong>${esc(item.address || item.action_id)}</strong>${programStateBadge(item.result || item.outcome || item.action_kind)}</div><p>${esc(programScalar(item.verdict || item.decision || item.payload || item.result))}</p></li>`).join("") || `<li class="hint">${esc(empty)}</li>`;
  return `<section class="program-panel"><div class="program-panel-head"><div><span>quality, dissent, and gates</span><strong>Evidence metadata, verdicts, councils, obligations, and delivery handoffs</strong></div></div>
    <div class="program-quality-grid">
      <section><h3>verdicts / gates</h3><ul>${resultItems([...(view.verdicts || []), ...(view.gates || [])], "No quality verdict or gate receipt yet.")}</ul></section>
      <section><h3>decisions / dissent / rounds</h3><ul>${resultItems([...(view.decisions || []), ...(view.dissent || []), ...(view.rounds || [])], "No deliberation receipt yet.")}</ul></section>
      <section><h3>obligations / debt</h3><ul>${(view.obligations?.all || []).map((item) => `<li><div><strong>${esc(item.id)}</strong>${programStateBadge(item.state)}${item.blocking ? badge("blocking", "issue") : ""}</div><p>${esc(item.statement || item.reason || programScalar(item))}</p></li>`).join("") || '<li class="hint">No decision obligation is recorded.</li>'}</ul></section>
      <section><h3>deliveries / integrations</h3><ul>${[...(view.deliveries || []), ...(view.integrations || [])].map((item) => `<li><div><strong>${esc(item.delivery_id || item.action_kind || item.action_id)}</strong>${programStateBadge(item.state || item.result || (item.complete ? "complete" : "active"))}</div><p>${esc(programScalar(item.next_action || item.story || item.receipt_hash))}</p></li>`).join("") || '<li class="hint">No certified delivery handoff has started.</li>'}</ul></section>
    </div>
    <div class="tablewrap"><table class="run-table"><thead><tr><th>artifact</th><th>kind</th><th>size</th><th>digest / ref</th></tr></thead><tbody>${artifactRows || '<tr><td colspan="4">No content-safe artifact metadata yet.</td></tr>'}</tbody></table></div>
  </section>`;
}

function programControlsHtml(view) {
  return `<section class="program-controls exact-control-audit"><div class="program-panel-head"><div><span>exact control catalog</span><strong>Applicability copied from the current saved program</strong></div>${badge("inspection only", "ok")}</div>
    <div class="run-unavailable">${(view.controls || []).map((item, index) => `<div><strong>${esc(item.action)}${item.decision ? ` · ${esc(item.decision)}` : ""}</strong><span>${item.available ? "available through the ordinary action review above" : esc(item.issue || "not applicable in the current authority state")}</span><code>/controls/${esc(index)}</code></div>`).join("")}</div>
  </section>`;
}

function programActHtml(preview) {
  if (!preview) return "";
  return `<details class="bounded-exact-preview"><summary>Exact program preview</summary><div class="run-token"><span>state + ledger + parameter token</span><code>${esc(preview.act_token)}</code></div><p>Observed <code>${esc(preview.state)}</code> at generation ${esc(preview.generation)} and ledger <code>${esc(preview.ledger_head)}</code>.</p><p><strong>lane:</strong> ${esc(preview.operation?.lane || "—")} · <strong>next:</strong> ${esc(programScalar(preview.operation?.next_action))}</p>${(preview.issues || []).map((issue) => `<p class="guard">${esc(issue)}</p>`).join("")}</details>`;
}

function programTimelineHtml(view) {
  return `<ol class="program-timeline">${(view.timeline || []).map((event) => `<li><div><strong>${esc(event.event)}</strong><time>${esc(event.at || event.ts)}</time>${badge(`#${event.seq}`)}</div><p>${Object.entries(event.detail || {}).map(([key, value]) => `<span><b>${esc(key)}</b> ${esc(programScalar(value))}</span>`).join("")}</p><code>${esc(event.event_hash)}</code></li>`).join("")}</ol>`;
}

function programNotificationsHtml(view) {
  const items = (programState.notifications || []).filter(
    (item) => item.run_id === view.run_id && item.kind.startsWith("program-"),
  );
  return `<section class="program-panel"><div class="program-panel-head"><div><span>operator notifications</span><strong>Derived facts and typed request documents</strong></div>${badge("transport ≠ authority", "ok")}</div>
    <ul class="run-notifications">${items.map((item) => `<li><code>${esc(item.kind)}</code> ${item.unread ? badge("unread", "warn") : badge("acked", "ok")}<span>${esc(item.detail)}</span>${item.request ? `<small>typed response · <code>${esc(item.request.correlation_id)}</code> · ${esc((item.request.response_schema?.decision || []).join("|"))} · fresh local act token still required</small>` : ""}${item.unread ? `<button type="button" data-program-ntf-ack="${esc(item.id)}">ack</button>` : ""}</li>`).join("") || '<li class="hint">No derived program notification at this ledger head.</li>'}</ul>
  </section>`;
}

function programRunHtml(view) {
  const runs = programState.inventory?.runs || [];
  const progress = view.phase_progress || {};
  const actions = boundedActionCenterHtml(view.bounded_actions, programState.act, programState.error, programState.result, "program");
  const toolbar = `<div class="live-toolbar"><label>delivery run<select id="program-run-select">${runs.map((item) => `<option value="${esc(item.run_id)}"${item.run_id === view.run_id ? " selected" : ""}>${esc(view.program?.title || item.program || "program")} · ${esc(item.state)}</option>`).join("")}</select></label><button type="button" id="program-refresh">Check for updates</button><button type="button" data-live-technical>Technical details</button></div>`;
  const technical = `${programState.result ? `<div class="program-result" role="status"><strong>bounded operation completed</strong><span>${esc(programState.result.kind)} · ${esc(programState.result.stop || programState.result.state || programState.result.result || "recorded")}</span></div>` : ""}
    <div class="program-summary"><div><span>authority</span><strong>${esc(view.state)}</strong><small>${esc(view.terminal_meaning)}</small></div><div><span>operational frontier</span><strong>${esc(view.operational_state)}</strong><small>${esc(view.current?.stop || "ready")}</small></div><div><span>ledger</span><strong>${esc(view.event_count)} events</strong><code>${esc(view.ledger_head)}</code></div><div><span>scope progress</span><strong>${esc((progress.selected_stories || []).length)} selected</strong><small>${esc(programScalar(progress.scope_completion))}</small></div></div>
    ${programWhyHtml(view)}
    ${runBudgetHtml(view.budgets)}
    ${programOrganizationHtml(view)}
    ${programActivityHtml(view)}
    ${programQualityHtml(view)}
    ${programNotificationsHtml(view)}
    ${programControlsHtml(view)}
    <section class="program-panel"><div class="program-panel-head"><div><span>phase and authority boundary</span><strong>Granted scope, selected progress, capabilities, and permanent exclusions</strong></div></div><div class="program-boundary"><section><h3>phase progress</h3><pre>${esc(JSON.stringify(progress, null, 2))}</pre></section><section><h3>capabilities</h3><p>${(view.capabilities || []).map((item) => badge(item, "ok")).join(" ") || "none"}</p><h3>permanently excluded</h3><p>${(view.permanent_exclusions || []).map((item) => badge(item, "warn")).join(" ") || "none"}</p></section></div></section>
    <section class="program-panel"><div class="program-panel-head"><div><span>hash-chained receipts</span><strong>Program authority timeline</strong></div>${badge("content-safe metadata", "ok")}</div>${programTimelineHtml(view)}</section>`;
  return `<div class="program-room" data-program-run="${esc(view.run_id)}">${liveProgressShell(view.live_progress, programState.connection, toolbar, actions, technical, Boolean(programState.stream), "h1")}</div>`;
}

function renderPrograms() {
  const focus = captureAppFocus();
  if (programState.loading) {
    app.innerHTML = stateHtml("Replaying the authoritative program ledger…");
    finishDynamicRender(focus);
    return;
  }
  if (programState.error && !programState.inventory) {
    app.innerHTML = stateHtml(programState.error, true);
    finishDynamicRender(focus);
    return;
  }
  app.innerHTML = destinationNav("live", "#/programs")
    + (programState.view ? programRunHtml(programState.view) : programInventoryHtml());
  wirePrograms();
  finishDynamicRender(focus);
}

async function refreshProgramView() {
  if (!programState.runId) return;
  const previousView = programState.view;
  const focus = captureAppFocus();
  programState.loading = true;
  programState.error = "";
  programState.connection.status = "checking";
  if (!previousView) renderPrograms();
  try {
    const [inventory, view, notifications] = await Promise.all([
      api("/api/programs"),
      api(`/api/programs/${encodeURIComponent(programState.runId)}/view`),
      api("/api/notifications"),
    ]);
    programState.inventory = inventory.data;
    programState.view = view.data;
    programState.notifications = notifications.data.notifications || [];
    programState.connection.status = SNAPSHOT_LIVE_STATE === "stale" ? "stale" : SNAPSHOT_MODE ? "verified" : "checking";
  } catch (err) {
    programState.error = err.message;
    programState.view = previousView;
    programState.connection.status = previousView ? "stale" : "manual";
  }
  programState.loading = false;
  renderPrograms();
  restoreAppFocus(focus);
  const version = String(
    programState.view?.ledger_head || programState.view?.event_count || "",
  );
  if (liveAnnouncementKeys.has("program")) {
    announceLiveUpdate(
      "program",
      version,
      "Delivery progress changed. Review What happens next or check the saved history.",
    );
  } else if (version) {
    liveAnnouncementKeys.set("program", version);
  }
  startProgramLive();
}

function startProgramLive() {
  stopProgramLive();
  if (!programState.runId || !programState.view) return;
  if (SNAPSHOT_MODE || typeof EventSource === "undefined") {
    if (SNAPSHOT_LIVE_STATE !== "stale") programState.connection.status = SNAPSHOT_MODE ? "verified" : "manual";
    renderPrograms();
    return;
  }
  const runId = programState.runId;
  const cursor = Number(programState.view.event_count || 0);
  programLive = new EventSource(`/api/programs/${encodeURIComponent(runId)}/events?from=${cursor}&follow=1`);
  programLive.onopen = () => {
    if (programState.runId !== runId) return;
    programState.connection.status = "live";
    renderPrograms();
  };
  programLive.addEventListener("program-ledger", () => {
    if (programLiveTimer) return;
    programLiveTimer = setTimeout(async () => {
      programLiveTimer = null;
      if (programState.runId !== runId) return;
      try {
        programState.view = (await api(`/api/programs/${encodeURIComponent(runId)}/view`)).data;
        programState.connection.status = "live";
        programState.inventory = (await api("/api/programs")).data;
        programState.notifications = (await api("/api/notifications")).data.notifications || [];
        announceLiveUpdate(
          "program",
          programState.view?.ledger_head || programState.view?.event_count,
          "Delivery progress changed. Review What happens next or check the saved history.",
        );
        renderPrograms();
      } catch (err) {
        programState.connection.status = "stale";
        announceLiveUpdate(
          "program-connection",
          `stale:${runId}:${programState.view?.event_count || ""}`,
          "Live delivery updates were interrupted. The last verified view remains available.",
        );
        renderPrograms();
      }
    }, 350);
  });
  programLive.onerror = () => {
    programState.connection.status = "stale";
    stopProgramLive();
    announceLiveUpdate(
      "program-connection",
      `stale:${runId}:${programState.view?.event_count || ""}`,
      "Live delivery updates were interrupted. The last verified view remains available.",
    );
    renderPrograms();
  };
}

async function previewProgramStart(form) {
  rememberReturnFocus("program-plan");
  const values = Object.fromEntries(new FormData(form).entries());
  const minutes = Math.max(1, Math.min(1440, Number(values.minutes) || 60));
  const issued = new Date();
  const request = {
    program: String(values.program || ""), mode: String(values.mode || "continuous"),
    operator: String(values.operator || "").trim(), reason: String(values.reason || "").trim(),
    intent_id: `workbench-${issued.getTime()}`, issued_at: issued.toISOString(),
    expires_at: new Date(issued.getTime() + minutes * 60_000).toISOString(),
  };
  programState.planRequest = { ...request, minutes }; programState.plan = null; programState.error = ""; renderPrograms();
  const { status, body } = await postJson("/api/programs/plan", request);
  if (status >= 400 || body.ok === false) programState.error = (body.issues && body.issues[0]) || `program plan failed (${status})`;
  else programState.plan = body.data;
  renderPrograms();
  if (programState.plan) focusRegion(".program-consent");
}

async function confirmProgramStart() {
  if (!programState.plan?.applicable || !programState.planRequest) return;
  const request = { ...programState.planRequest, approve: true, expect: programState.plan.start_token };
  delete request.minutes;
  const { status, body } = await postJson("/api/programs/start", request);
  if (status >= 400 || body.ok === false) {
    programState.plan = null;
    programState.error = (body.issues && body.issues[0]) || `program start failed (${status})`;
    renderPrograms(); return;
  }
  programState.plan = null; programState.planRequest = null;
  location.hash = `#/programs/${encodeURIComponent(body.data.run_id)}`;
}

async function previewProgramAct(button) {
  rememberReturnFocus("program-act", button);
  const action = button.dataset.programAct;
  const reasonRequired = ["request", "pause", "resume", "revoke", "cancel"].includes(action);
  const request = {
    run_id: programState.runId, action,
    ...(reasonRequired ? { reason: programState.reason.trim() } : {}),
    ...(button.dataset.programDecision ? { decision: button.dataset.programDecision } : {}),
    ...(button.dataset.programRequest ? { request_id: button.dataset.programRequest } : {}),
    ...(["tick", "supervise"].includes(action) ? {
      max_ticks: action === "tick" ? 100 : Number(programState.maxTicks),
      max_seconds: action === "tick" ? 300 : Number(programState.maxSeconds),
    } : {}),
  };
  programState.act = null; programState.error = ""; programState.result = null; renderPrograms();
  const { status, body } = await postJson("/api/programs/preview", request);
  if (status >= 400 || body.ok === false) programState.error = (body.issues && body.issues[0]) || `program preview failed (${status})`;
  else programState.act = body.data;
  renderPrograms();
  if (programState.act) focusRegion(".bounded-preview");
}

async function confirmProgramAct() {
  const preview = programState.act;
  if (!preview?.applicable) return;
  const request = {
    run_id: preview.run_id, expect: preview.act_token,
    ...(preview.reason ? { reason: preview.reason } : {}),
    ...(preview.decision ? { decision: preview.decision } : {}),
    ...(preview.request_id ? { request_id: preview.request_id } : {}),
    ...(preview.action === "supervise" ? { max_ticks: preview.max_ticks, max_seconds: preview.max_seconds } : {}),
  };
  const { status, body } = await postJson(`/api/programs/${encodeURIComponent(preview.action)}`, request);
  if (status >= 400 || body.ok === false) {
    programState.act = null;
    programState.error = status === 409
      ? "Stale program action refused before work or saved event change. Reload once and review the current action."
      : (body.issues && body.issues[0]) || `program act failed (${status})`;
    renderPrograms(); return;
  }
  programState.result = body.data; programState.act = null; programState.reason = "";
  await refreshProgramView();
}

async function openProgramStream(button) {
  rememberReturnFocus("program-stream", button);
  programState.stream = null; programState.error = ""; renderPrograms();
  try {
    programState.stream = (await api(`/api/programs/${encodeURIComponent(programState.runId)}/streams/${encodeURIComponent(button.dataset.sessionId)}/${encodeURIComponent(button.dataset.programStream)}?max_bytes=20000`)).data;
  } catch (err) { programState.error = err.message; }
  renderPrograms();
  if (programState.stream) focusRegion(".program-open-stream");
}

async function ackProgramNotification(id) {
  const { status, body } = await postJson("/api/notifications/ack", { id });
  if (status >= 400 || body.ok === false) {
    programState.error = (body.issues && body.issues[0]) || `notification acknowledgement failed (${status})`;
    renderPrograms(); return;
  }
  programState.notifications = (await api("/api/notifications")).data.notifications || [];
  renderPrograms();
}

function wirePrograms() {
  document.getElementById("program-plan-form")?.addEventListener("submit", (event) => { event.preventDefault(); previewProgramStart(event.currentTarget); });
  document.getElementById("program-start-confirm")?.addEventListener("click", confirmProgramStart);
  const closePlan = () => {
    programState.plan = null;
    renderPrograms();
    restoreReturnFocus("program-plan", "#program-plan-form button[type='submit']");
  };
  document.getElementById("program-plan-close")?.addEventListener("click", closePlan);
  document.getElementById("program-refresh")?.addEventListener("click", refreshProgramView);
  document.querySelector("[data-live-technical]")?.addEventListener("click", openLiveTechnical);
  document.getElementById("program-run-select")?.addEventListener("change", (event) => { location.hash = `#/programs/${encodeURIComponent(event.target.value)}`; });
  document.getElementById("program-control-reason")?.addEventListener("input", (event) => { programState.reason = event.target.value; });
  document.getElementById("program-max-ticks")?.addEventListener("input", (event) => { programState.maxTicks = Number(event.target.value); });
  document.getElementById("program-max-seconds")?.addEventListener("input", (event) => { programState.maxSeconds = Number(event.target.value); });
  document.querySelectorAll("[data-program-act]").forEach((button) => button.addEventListener("click", () => previewProgramAct(button)));
  document.getElementById("program-act-confirm")?.addEventListener("click", confirmProgramAct);
  const closeAct = () => {
    programState.act = null;
    renderPrograms();
    restoreReturnFocus("program-act");
  };
  document.getElementById("program-act-close")?.addEventListener("click", closeAct);
  document.querySelectorAll("[data-bounded-read]").forEach((button) => button.addEventListener("click", () => handleBoundedRead(button.dataset.boundedRead, "program")));
  document.querySelectorAll("[data-program-stream]").forEach((button) => button.addEventListener("click", () => openProgramStream(button)));
  document.querySelectorAll("[data-program-ntf-ack]").forEach((button) => button.addEventListener("click", () => ackProgramNotification(button.dataset.programNtfAck)));
  const closeStream = () => {
    programState.stream = null;
    renderPrograms();
    restoreReturnFocus("program-stream");
  };
  document.getElementById("program-stream-close")?.addEventListener("click", closeStream);
  wireDismissibleRegion(".program-consent", closePlan, "program-plan", "#program-plan-form button[type='submit']");
  wireDismissibleRegion(".bounded-preview", closeAct, "program-act");
  wireDismissibleRegion(".program-open-stream", closeStream, "program-stream");
}

async function viewPrograms(runId = "") {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "program control", href: "#/programs" }, ...(runId ? [{ label: runId }] : [])]);
  programState.runId = runId; programState.view = null; programState.act = null;
  programState.stream = null; programState.result = null; programState.error = "";
  const [inventory, notifications] = await Promise.all([
    api("/api/programs"), api("/api/notifications"),
  ]);
  programState.inventory = inventory.data;
  programState.notifications = notifications.data.notifications || [];
  if (runId) {
    programState.view = (await api(`/api/programs/${encodeURIComponent(runId)}/view`)).data;
    programState.connection.status = SNAPSHOT_LIVE_STATE === "stale" ? "stale" : SNAPSHOT_MODE ? "verified" : "checking";
    if (SNAPSHOT_MODE && SNAPSHOT_BOUNDED_PREVIEW) {
      const control = (programState.view.controls || []).find((item) => item.available && (
        SNAPSHOT_BOUNDED_PREVIEW === "decision"
          ? item.action === "request" && item.decision === "approve"
          : item.action === SNAPSHOT_BOUNDED_PREVIEW
      ));
      if (control) {
        programState.reason = control.reason_required
          ? "Review this deterministic viewport action."
          : "";
        const response = await postJson("/api/programs/preview", {
          run_id: programState.runId,
          action: control.action,
          ...(programState.reason ? { reason: programState.reason } : {}),
          ...(control.decision ? { decision: control.decision } : {}),
          ...(control.request_id ? { request_id: control.request_id } : {}),
          ...(["tick", "supervise"].includes(control.action) ? {
            max_ticks: 100, max_seconds: 300,
          } : {}),
        });
        if (response.status < 400 && response.body.ok !== false) {
          programState.act = response.body.data;
        }
      }
    }
    if (SNAPSHOT_MODE && SNAPSHOT_BOUNDED_ERROR) {
      programState.error = SNAPSHOT_BOUNDED_ERROR === "stale"
        ? "Stale program action refused before work or saved event change. Reload once and review the current action."
        : "The action response ended without a confirmed receipt.";
    }
    startProgramLive();
  }
  renderPrograms();
  focusBoundedSnapshot();
}

/* ── delivery-shaped front door (WLA-27-03) ────────────────────────
 * This is a renderer over /api/delivery-setup. Choosing, cancelling, and
 * opening Technical details are browser-local navigation only. A bounded
 * delivery still crosses the existing run-plan/start boundary; a program
 * draft still crosses Program Studio preview/apply and a later separate
 * program start. */

let deliverySetupState = {
  model: null, choice: "", project: "", phase: "", technical: false,
};
let pendingProgramSetup = null;

function setupEffectList(items, emptyText) {
  return items?.length
    ? `<ul>${items.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`
    : `<p>${esc(emptyText)}</p>`;
}

function deliveryChoiceCard(choice) {
  const selected = deliverySetupState.choice === choice.id;
  const titleId = `delivery-choice-${choice.id}-title`;
  const summaryId = `delivery-choice-${choice.id}-summary`;
  return `<article class="delivery-choice${selected ? " selected" : ""}" data-choice="${esc(choice.id)}">
    <div class="delivery-choice-head"><span>${esc(choice.tier === "vanilla" ? "ordinary roadmap" : choice.tier === "bounded-run" ? "one bounded delivery" : "optional delivery program")}</span>${badge(choice.readiness, choice.available ? "ok" : "warn")}</div>
    <h2 id="${titleId}">${esc(choice.label)}</h2><p id="${summaryId}">${esc(choice.summary)}</p>
    ${choice.recommended ? '<strong class="delivery-default">Ready now · no optional setup</strong>' : ""}
    ${choice.correction ? `<div class="delivery-correction"><strong>Affected decision</strong><span>${esc(choice.correction)}</span></div>` : ""}
    <button type="button" data-delivery-choice="${esc(choice.id)}" aria-pressed="${selected ? "true" : "false"}" aria-labelledby="${titleId}" aria-describedby="${summaryId}">Review this option</button>
  </article>`;
}

function deliveryChoiceReview(model, choice) {
  if (!choice) return `<section class="delivery-review empty"><h2>Choose how much coordination this delivery needs</h2><p>No option is selected for you. Ordinary roadmap work remains ready while you compare the optional paths.</p></section>`;
  const scope = model.delivery_scope || {};
  const project = deliverySetupState.project || scope.selected_project || "";
  const phase = deliverySetupState.phase;
  const actionLabel = choice.id === "roadmap"
    ? (choice.available ? "Continue with the roadmap" : "Resolve readiness first")
    : choice.id === "bounded"
      ? (choice.available ? "Review delivery readiness" : "Open delivery plans")
      : (choice.available ? "Continue to a delivery-plan draft" : "Choose a project first");
  const continueAllowed = choice.id === "bounded" || choice.available;
  return `<section class="delivery-review" id="delivery-review" role="dialog" aria-modal="false" tabindex="-1" aria-labelledby="delivery-review-title">
    <header><div><span>Review before continuing</span><h2 id="delivery-review-title">${esc(choice.label)}</h2></div>${badge("nothing started", "ok")}</header>
    <div class="delivery-effect-grid">
      <section><h3>What setup creates</h3>${setupEffectList(choice.creates_during_setup, "Nothing.")}</section>
      <section><h3>What could change later</h3>${setupEffectList(choice.may_change_after_confirmation, "Nothing through this option.")}</section>
      <section><h3>What stays off</h3>${setupEffectList(choice.remains_disabled, "No additional delivery mode.")}</section>
      <section><h3>Permission still needed</h3><p>${esc(choice.separate_permission || "No optional delivery permission is requested.")}</p></section>
    </div>
    ${choice.correction ? `<div class="delivery-next"><strong>Next step</strong><span>${esc(choice.correction)}</span></div>` : ""}
    <div class="delivery-review-actions">
      <button type="button" id="delivery-continue"${continueAllowed ? "" : " disabled"}>${esc(actionLabel)}</button>
      <button type="button" id="delivery-back">Compare options</button>
      <button type="button" id="delivery-cancel">Leave for now</button>
    </div>
    <p class="delivery-unchanged">Leaving, comparing, or opening details creates no delivery plan, permission, run, process, observer, notification, network activity, or roadmap change.</p>
    <span hidden data-delivery-project="${esc(project)}" data-delivery-phase="${esc(phase)}"></span>
  </section>`;
}

function deliveryTechnicalDetails(model) {
  const details = model.technical_details || {};
  return `<details class="delivery-technical"${deliverySetupState.technical ? " open" : ""}>
    <summary>${esc(details.label || "Technical details")}</summary>
    <p>Exact source models and inspection commands. These reads confer no authority.</p>
    <div class="delivery-source-list">${(details.sources || []).map((source) => `<div><code>${esc(source.kind)}@${esc(source.schema_version)}</code><span>${esc(source.route)}</span></div>`).join("")}</div>
    <div class="delivery-command-list">${Object.entries(details.commands || {}).map(([name, command]) => `<div><span>${esc(name.replaceAll("_", " "))}</span><code>${esc(command.join(" "))}</code></div>`).join("")}</div>
  </details>`;
}

function renderDeliverySetup() {
  const focus = captureAppFocus();
  const model = deliverySetupState.model;
  if (!model) {
    app.innerHTML = stateHtml("Checking delivery readiness…");
    finishDynamicRender(focus);
    return;
  }
  const scope = model.delivery_scope || {};
  const projects = scope.projects || [];
  const current = projects.find((item) => item.slug === deliverySetupState.project)
    || projects.find((item) => item.slug === scope.selected_project);
  const work = current?.next_work || scope.current_work;
  const phase = current?.current_phase || scope.current_phase;
  if (!deliverySetupState.project && scope.selected_project) deliverySetupState.project = scope.selected_project;
  if (!deliverySetupState.phase && phase?.number !== undefined) deliverySetupState.phase = String(phase.number);
  const choice = setupChoice(model, deliverySetupState.choice);
  app.innerHTML = `${destinationNav("plan", "#/program-studio")}<div class="delivery-setup" data-readiness="${esc(model.readiness)}">
    <header class="delivery-setup-hero"><div><span>Plan your delivery</span><h1>What are you delivering?</h1><p>${esc(model.summary)} Nothing starts until you review and confirm it.</p></div>${badge(model.readiness, model.readiness === "ready" ? "ok" : "issue")}</header>
    <section class="delivery-scope" aria-labelledby="delivery-scope-title"><div><span>Step 1</span><h2 id="delivery-scope-title">Choose the delivery scope</h2></div>
      <label>Roadmap project<select id="delivery-project"><option value="">Choose a project</option>${projects.map((item) => `<option value="${esc(item.slug)}"${item.slug === deliverySetupState.project ? " selected" : ""}>${esc(item.slug)}</option>`).join("")}</select></label>
      <label>Phase to review<input id="delivery-phase" type="number" min="0" value="${esc(deliverySetupState.phase)}" inputmode="numeric"></label>
      <div class="delivery-current-work"><span>Current work</span><strong>${esc(work?.title || "Choose a project to see current work")}</strong><small>${work ? `${esc(work.story_id)} · ${esc(work.status)}` : "No work is inferred."}</small></div>
    </section>
    ${(model.issues || []).map((issue) => `<div class="delivery-issue" role="status"><strong>${esc(issue.decision)}</strong><span>${esc(issue.summary)}</span><small>${esc(issue.next_step)}</small></div>`).join("")}
    <section class="delivery-choice-step" aria-labelledby="delivery-choice-title"><div><span>Step 2</span><h2 id="delivery-choice-title">Choose the operating mode</h2><p>Compare all three. A higher mode is never selected or started for you.</p></div>
      <div class="delivery-choice-grid" role="group" aria-labelledby="delivery-choice-title">${(model.choices || []).map(deliveryChoiceCard).join("")}</div>
    </section>
    ${deliveryChoiceReview(model, choice)}
    ${deliveryTechnicalDetails(model)}
  </div>`;
  wireDeliverySetup();
  finishDynamicRender(focus);
}

function wireDeliverySetup() {
  document.getElementById("delivery-project")?.addEventListener("change", async (event) => {
    deliverySetupState.project = event.target.value;
    if (deliverySetupState.project) rememberProject(deliverySetupState.project);
    deliverySetupState.phase = "";
    deliverySetupState.choice = "";
    const query = deliverySetupState.project
      ? `?project=${encodeURIComponent(deliverySetupState.project)}`
      : "";
    deliverySetupState.model = (await api(`/api/delivery-setup${query}`)).data;
    renderDeliverySetup();
  });
  document.getElementById("delivery-phase")?.addEventListener("input", (event) => {
    deliverySetupState.phase = event.target.value;
  });
  document.querySelectorAll("[data-delivery-choice]").forEach((button) => button.addEventListener("click", () => {
    rememberReturnFocus("delivery-review", button);
    deliverySetupState.choice = button.dataset.deliveryChoice;
    renderDeliverySetup();
    requestAnimationFrame(() => document.getElementById("delivery-review")?.focus());
  }));
  document.getElementById("delivery-back")?.addEventListener("click", () => {
    const selected = deliverySetupState.choice;
    deliverySetupState.choice = "";
    renderDeliverySetup();
    restoreReturnFocus(
      "delivery-review",
      `[data-delivery-choice="${selectorEscape(selected)}"]`,
    );
  });
  document.getElementById("delivery-cancel")?.addEventListener("click", () => {
    pendingProgramSetup = null;
    location.hash = "#/";
  });
  document.getElementById("delivery-continue")?.addEventListener("click", () => {
    const choice = setupChoice(deliverySetupState.model, deliverySetupState.choice);
    if (!choice) return;
    if (choice.id === "bounded") orchState.view = "validate";
    if (choice.id === "program") {
      pendingProgramSetup = {
        project: deliverySetupState.project,
        phase: deliverySetupState.phase,
      };
    }
    location.hash = choice.route;
  });
  document.querySelector(".delivery-technical")?.addEventListener("toggle", (event) => {
    deliverySetupState.technical = event.currentTarget.open;
  });
  const closeReview = () => {
    const selected = deliverySetupState.choice;
    deliverySetupState.choice = "";
    renderDeliverySetup();
    restoreReturnFocus(
      "delivery-review",
      `[data-delivery-choice="${selectorEscape(selected)}"]`,
    );
  };
  wireDismissibleRegion(
    "#delivery-review",
    closeReview,
    "delivery-review",
  );
  wireArrowGroup(".delivery-choice-grid", "[data-delivery-choice]");
}

async function viewDeliverySetup() {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "delivery setup" }]);
  const requested = new URLSearchParams(location.search);
  const queryProject = requested.get("setupproject") || selectedProject;
  const query = queryProject ? `?project=${encodeURIComponent(queryProject)}` : "";
  deliverySetupState.model = (await api(`/api/delivery-setup${query}`)).data;
  deliverySetupState.project = queryProject || deliverySetupState.model.delivery_scope.selected_project || "";
  deliverySetupState.phase = "";
  deliverySetupState.choice = requested.get("setupmode") || "";
  deliverySetupState.technical = requested.has("setuptechnical");
  renderDeliverySetup();
}

/* ── optional Program / Workflow Studio (WLA-26-06) ────────────────
 * This route is deliberately additive: the ordinary Workbench stays at #/.
 * The browser owns interaction and layout only. Raw policy, diagnostics,
 * graph projection, simulation, hashes, and authority explanation all arrive
 * from /api/program-studio, which delegates to the Phase-26 compilers. */

const STUDIO_FAMILIES = ["program", "workflow", "organization"];
const STUDIO_VIEWS = ["plan", "simulate", "validate", "technical", "authority"];
const STUDIO_NODE_TYPES = [
  "agent", "check", "collect", "bounded_run", "subflow", "loop",
  "debate", "verdict", "gate", "checkpoint", "rail",
];

let studioState = {
  inventory: null, family: "program", name: "", exists: false,
  document: null, model: null, compilePreview: null, view: "plan",
  selected: "", jsonDraft: "", validationTimer: null,
  scenario: "candidate-assignment", error: "", jsonPointer: "",
  setupContext: null, planSection: "scope", technicalMode: "graph",
};

function studioFamilyModel(family = studioState.family) {
  return (studioState.inventory?.families || []).find((item) => item.id === family);
}

function studioCssToken(value) {
  return String(value || "unknown").toLowerCase().replace(/[^a-z0-9_-]+/g, "-");
}

function studioFieldId(pointer) {
  return pointer ? `studio-field-${String(pointer).replace(/[^a-zA-Z0-9_-]+/g, "-").replace(/^-|-$/g, "")}` : "";
}

function studioInput(label, key, value, type = "text", attrs = "", pointer = "") {
  return `<label class="studio-field"><span>${esc(label)}</span><input ${pointer ? `id="${esc(studioFieldId(pointer))}"` : ""} data-studio-field="${esc(key)}" type="${type}" value="${esc(value ?? "")}" ${attrs}></label>`;
}

function studioArea(label, key, value, hint = "", pointer = "") {
  return `<label class="studio-field"><span>${esc(label)}</span><textarea ${pointer ? `id="${esc(studioFieldId(pointer))}"` : ""} data-studio-field="${esc(key)}">${esc(value ?? "")}</textarea>${hint ? `<small>${esc(hint)}</small>` : ""}</label>`;
}

function studioSelect(label, key, values, selected, pointer = "") {
  return `<label class="studio-field"><span>${esc(label)}</span><select ${pointer ? `id="${esc(studioFieldId(pointer))}"` : ""} data-studio-field="${esc(key)}">${values.map((value) => `<option value="${esc(value)}"${value === selected ? " selected" : ""}>${esc(value)}</option>`).join("")}</select></label>`;
}

function ensureStudioLayout() {
  const document = studioState.document;
  if (!document) return;
  document.layout ||= {};
  document.layout.nodes ||= {};
  document.layout.viewport ||= { x: 0, y: 0, zoom: 1 };
}

function studioGraphNode(id) {
  return (studioState.model?.graph?.nodes || []).find((node) => node.id === id);
}

function studioRawNode(graphNode) {
  if (!graphNode || studioState.family !== "workflow") return null;
  const match = String(graphNode.pointer || "").match(/^\/nodes\/(\d+)/);
  return match ? studioState.document.nodes?.[Number(match[1])] : null;
}

function studioGraphHtml() {
  const graph = studioState.model?.graph;
  if (!graph) return stateHtml("Waiting for the shared graph projection…");
  const nodes = graph.nodes || [];
  const byId = Object.fromEntries(nodes.map((node) => [node.id, node]));
  const maxX = Math.max(960, ...nodes.map((node) => Number(node.position?.x || 0) + 250));
  const maxY = Math.max(560, ...nodes.map((node) => Number(node.position?.y || 0) + 155));
  const diagnosticCounts = new Map();
  (studioState.model.validation?.diagnostics || []).forEach((diagnostic) => {
    const id = diagnostic.target?.node_id;
    if (id) diagnosticCounts.set(id, (diagnosticCounts.get(id) || 0) + 1);
  });
  const edges = (graph.edges || []).map((edge) => {
    const source = byId[edge.from]?.position;
    const target = byId[edge.to]?.position;
    if (!source || !target) return "";
    const failure = ["route", "separation"].includes(edge.kind);
    const x1 = Number(source.x) + 210; const y1 = Number(source.y) + 52;
    const x2 = Number(target.x); const y2 = Number(target.y) + 52;
    return `<path class="studio-edge kind-${studioCssToken(edge.kind)}" d="M ${x1} ${y1} C ${x1 + 40} ${y1}, ${x2 - 40} ${y2}, ${x2} ${y2}" marker-end="url(#studio-arrow-${failure ? "route" : "success"})"><title>${esc(edge.from)} → ${esc(edge.to)} · ${esc(edge.label || edge.kind)}</title></path>`;
  }).join("");
  return `<div class="studio-canvas-wrap" data-studio-scenario="${esc(studioState.scenario)}"><svg id="studio-canvas" class="studio-canvas" viewBox="0 0 ${maxX} ${maxY}" role="group" aria-labelledby="studio-canvas-title">
    <title id="studio-canvas-title">${esc(studioState.family)} policy graph. Nodes are keyboard selectable and movable; compiler diagnostics link back to exact nodes and fields.</title>
    <defs><marker id="studio-arrow-success" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z"></path></marker><marker id="studio-arrow-route" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z"></path></marker></defs>
    ${(graph.lanes || []).map((lane, index) => `<g class="studio-lane" data-lane="${esc(lane.id)}"><rect x="8" y="${36 + index * 175}" width="${maxX - 16}" height="152" rx="7"></rect><text x="22" y="${58 + index * 175}">${esc(lane.label)}</text></g>`).join("")}
    ${edges}
    ${nodes.map((node) => {
      const position = node.position || { x: 0, y: 0 };
      const count = diagnosticCounts.get(node.id) || 0;
      const summary = node.role || node.summary?.workflow || node.summary?.duty || node.lane || node.type;
      const bounds = Object.entries(node.bounds || {}).map(([key, value]) => `${key.replace(/^max_/, "≤ ")}: ${value}`).join(" · ");
      const drill = node.drilldown?.name ? ` · opens workflow ${node.drilldown.name}` : "";
      return `<g class="studio-node type-${studioCssToken(node.type)}${node.container ? " is-container" : ""}${studioState.selected === node.id ? " selected" : ""}${count ? " has-error" : ""}" data-studio-node="${esc(node.id)}" data-layout-key="${esc(node.layout_key || node.id)}" transform="translate(${Number(position.x)},${Number(position.y)})" tabindex="0" role="button" aria-label="${esc(node.label)}, ${esc(node.type)}, lane ${esc(node.lane)}${bounds ? `, bounded ${esc(bounds)}` : ""}${count ? `, ${count} compiler issues` : ""}${esc(drill)}">
        <title>${esc(node.label)} · ${esc(node.type)} · ${esc(summary)}${bounds ? ` · ${esc(bounds)}` : ""}${count ? ` · ${count} compiler issues` : ""}</title>
        <rect width="210" height="104" rx="${node.container ? 3 : 10}"></rect>
        <circle class="port input" cx="0" cy="52" r="5"></circle><circle class="port output" cx="210" cy="52" r="5"></circle>
        <text class="node-type" x="14" y="22">${esc(node.type)}${node.container ? " · bounded container" : ""}</text>
        <text class="node-label" x="14" y="49">${esc(String(node.label)).slice(0, 25)}</text>
        <text class="node-detail" x="14" y="72">${esc(String(summary || "")).slice(0, 31)}</text>
        <text class="node-bound" x="14" y="91">${esc(bounds || (node.fan_in > 1 ? `fan-in ${node.fan_in}` : node.fan_out > 1 ? `fan-out ${node.fan_out}` : node.drilldown?.name ? "drill down ↗" : "" )).slice(0, 36)}</text>
        ${count ? `<text class="node-error" x="194" y="22" text-anchor="end">${count}!</text>` : ""}
      </g>`;
    }).join("")}
  </svg></div>`;
}

function studioDocumentInspector() {
  const document = studioState.document || {};
  const common = `<div class="studio-inspector-head"><div><small>${esc(studioState.family)} policy</small><strong>${esc(document.slug || studioState.name)}</strong></div>${badge("tracked config", "ok")}</div>
    <form class="studio-inspector-form" id="studio-document-form">
      ${studioInput("slug / filename", "document.slug", document.slug, "text", 'pattern="[a-z][a-z0-9_-]*"', "/slug")}
      ${studioInput("title", "document.title", document.title, "text", "", "/title")}
      ${studioArea("description", "document.description", document.description || "", "reviewed tracked policy text; never provider credentials", "/description")}
      ${studioState.family === "workflow" ? studioInput("semantic version", "document.version", document.version || "1.0.0", "text", "", "/version") : ""}
    </form>`;
  if (studioState.family === "program") return common + studioProgramInspector();
  if (studioState.family === "organization") return common + studioOrganizationOverview();
  return common + `<p class="studio-help">Select a node to inspect its exact role, artifacts, bounds, routes, and shared-compiler diagnostics.</p>`;
}

function studioProgramInspector() {
  const document = studioState.document;
  const scope = document.scope || {};
  const phases = scope.phases || {};
  const stories = scope.stories === "all" ? "" : (scope.stories?.include || []).join("\n");
  const workCaps = ["agent:dispatch", "check:execute", "workspace:write", "nudge:deliver", "notification:send", "certification:verdict"];
  const deliveryCaps = ["evidence:materialize", "integration:apply", "contract:generate", "certification:objective", "git:commit", "git:push", "roadmap:story-start", "roadmap:story-complete", "roadmap:phase-advance"];
  const stops = ["scope-complete", "checkpoint-required", "unresolved-dissent", "architect-veto", "blocked-frontier", "budget-exhausted", "grant-expired", "grant-revoked"];
  return `<form id="studio-program-form" class="studio-inspector-form studio-program-form">
    <fieldset><legend>roadmap scope</legend>${studioInput("project", "program.project", scope.project || "", "text", "", "/scope/project")}${studioInput("phase from", "program.phase_from", phases.from ?? "", "number", 'min="0"', "/scope/phases/from")}${studioInput("phase through", "program.phase_through", phases.through ?? "", "number", 'min="0"', "/scope/phases/through")}${studioArea("exact story ids", "program.stories", stories, "empty means every story inside the phase scope", "/scope/stories")}</fieldset>
    <fieldset><legend>organization and autonomy ceiling</legend>${studioInput("organization", "program.organization", document.organization || "", "text", "", "/organization")}${studioSelect("mode ceiling", "program.mode_ceiling", ["advisory", "checkpointed", "continuous"], document.mode_ceiling || "advisory", "/mode_ceiling")}</fieldset>
    <fieldset><legend>work / verdict capability requests</legend><div class="studio-checkgrid">${workCaps.map((cap) => `<label><input type="checkbox" data-studio-capability="${cap}"${(document.requested_capabilities || []).includes(cap) ? " checked" : ""}>${cap}</label>`).join("")}</div></fieldset>
    <fieldset><legend>delivery rail requests</legend><div class="studio-checkgrid">${deliveryCaps.map((cap) => `<label><input type="checkbox" data-studio-capability="${cap}"${(document.requested_capabilities || []).includes(cap) ? " checked" : ""}>${cap}</label>`).join("")}</div></fieldset>
    <fieldset><legend>finite budgets</legend><div class="studio-budget-grid">${Object.entries(document.budgets || {}).map(([key, value]) => `<label><span>${esc(key)}</span><input type="number" min="1" data-studio-budget="${esc(key)}" value="${esc(value)}"></label>`).join("")}</div></fieldset>
    <fieldset><legend>stop and escalation policy</legend><div class="studio-checkgrid">${stops.map((stop) => `<label><input type="checkbox" data-studio-stop="${stop}"${(document.stop_conditions || []).includes(stop) ? " checked" : ""}>${stop}</label>`).join("")}</div></fieldset>
    <details><summary>binding rules and phase gates</summary><div class="studio-rule-list">${(document.bindings || []).map((rule, index) => `<button type="button" data-studio-select="binding:${esc(rule.id)}"><strong>${esc(rule.id)}</strong><span>priority ${esc(rule.priority)} · ${esc(rule.workflow)} · ${esc(rule.team)}</span><small>${esc(JSON.stringify(rule.match))}</small></button>`).join("") || '<p class="hint">No story binding rule yet; author one in lossless JSON.</p>'}${(document.phase_gates || []).map((gate) => `<button type="button" data-studio-select="gate:${esc(gate.id)}"><strong>${esc(gate.id)}</strong><span>${esc(gate.role)} · ${esc(gate.rubric)}</span><small>${esc(gate.when)} → ${esc(gate.on_fail)}</small></button>`).join("")}</div></details>
  </form>`;
}

function studioAuthoring() {
  return studioState.family === "organization"
    ? studioState.model?.team_review || null
    : studioState.model?.authoring || null;
}

function studioPlanSection(id = studioState.planSection) {
  return (studioAuthoring()?.sections || []).find((section) => section.id === id);
}

function studioPlanFactList(facts = []) {
  if (!facts.length) return "";
  return `<dl class="studio-plan-facts">${facts.map((fact) => `<div><dt>${esc(fact.label)}</dt><dd>${esc(fact.value ?? "Not chosen")}</dd></div>`).join("")}</dl>`;
}

function studioPlanItemList(items = [], editable = false) {
  if (!items.length) return '<p class="studio-plan-empty">Nothing has been defined here yet.</p>';
  return `<div class="studio-plan-items">${items.map((item) => {
    const action = editable && item.pointer?.startsWith("/nodes/")
      ? `<button type="button" data-plan-edit-step="${esc(item.id || "")}">Edit this step</button>`
      : "";
    const outcomes = (item.outcomes || []).length
      ? `<ul class="studio-plan-outcomes">${item.outcomes.map((outcome) => `<li><strong>${esc(outcome.outcome)}</strong><span>${esc(outcome.meaning)}</span></li>`).join("")}</ul>`
      : "";
    return `<article class="${item.advanced ? "advanced" : ""}">
      <div><span>${esc(item.advanced ? "Detailed flow" : "Delivery decision")}</span><strong>${esc(item.label)}</strong></div>
      <p>${esc(item.summary || "")}</p>${item.detail ? `<small>${esc(item.detail)}</small>` : ""}${outcomes}${action}
    </article>`;
  }).join("")}</div>`;
}

function studioPlanCorrections(sectionId) {
  const corrections = (studioAuthoring()?.corrections || []).filter((item) => item.section_id === sectionId);
  if (!corrections.length) return "";
  return `<div class="studio-plan-corrections" role="status"><h3>What needs attention</h3>${corrections.map((item) => `<article>
    <strong>${esc(item.affected_behavior)}</strong><p>${esc(item.correction)}</p>
    <button type="button" data-plan-correction="${esc(item.section_id)}" data-plan-node="${esc(item.target?.node_id || "")}" data-plan-field="${esc(item.target?.field_id || "")}">Go to this decision</button>
  </article>`).join("")}</div>`;
}

function studioPlanExamples() {
  const examples = studioAuthoring()?.examples || [];
  if (!examples.length) return "";
  return `<details class="studio-plan-examples"><summary>Examples</summary><div>${examples.map((example) => `<article><strong>${esc(example.label)}</strong><p>${esc(example.summary)}</p></article>`).join("")}</div></details>`;
}

function studioProgramPlanEditor(section) {
  const document = studioState.document || {};
  const scope = document.scope || {};
  const phases = scope.phases || {};
  const stories = scope.stories === "all" ? "" : (scope.stories?.include || []).join("\n");
  const bindings = document.bindings || [];
  const gates = document.phase_gates || [];
  const stopLabels = {
    "scope-complete": "All work in scope is complete",
    "checkpoint-required": "A named decision is required",
    "unresolved-dissent": "Review disagreement remains unresolved",
    "architect-veto": "The plan owner stops the delivery",
    "blocked-frontier": "The next work is blocked",
    "budget-exhausted": "A finite limit is reached",
    "grant-expired": "Permission expires",
    "grant-revoked": "Permission is withdrawn",
  };
  if (section.id === "scope") {
    return `<form class="studio-plan-form">
      ${studioInput("Plan name", "document.slug", document.slug, "text", 'pattern="[a-z][a-z0-9_-]*"', "/slug")}
      ${studioInput("Plan title", "document.title", document.title, "text", "", "/title")}
      ${studioArea("What is this delivery for?", "document.description", document.description || "", "A short purpose visible during review.", "/description")}
      <div class="studio-plan-form-grid">
        ${studioInput("Roadmap project", "program.project", scope.project || "", "text", "", "/scope/project")}
        ${studioInput("First phase", "program.phase_from", phases.from ?? "", "number", 'min="0"', "/scope/phases/from")}
        ${studioInput("Last phase", "program.phase_through", phases.through ?? "", "number", 'min="0"', "/scope/phases/through")}
      </div>
      ${studioArea("Only these story IDs", "program.stories", stories, "Leave empty to include every story in the selected phases.", "/scope/stories")}
    </form>`;
  }
  if (section.id === "flow") {
    return `<div class="studio-plan-editor-list">
      ${bindings.map((binding, index) => {
        const match = binding.match || {};
        return `<fieldset class="studio-plan-route"><legend>Work route ${index + 1}</legend>
          <div class="studio-plan-form-grid">
            <label><span>Route name</span><input data-plan-binding="${index}" data-plan-binding-field="id" value="${esc(binding.id || "")}"></label>
            <label><span>Order</span><input type="number" min="1" data-plan-binding="${index}" data-plan-binding-field="priority" value="${esc(binding.priority ?? "")}"></label>
            <label><span>First phase</span><input type="number" min="0" data-plan-binding="${index}" data-plan-binding-field="phase_from" value="${esc(match.phase_from ?? "")}"></label>
            <label><span>Last phase</span><input type="number" min="0" data-plan-binding="${index}" data-plan-binding-field="phase_through" value="${esc(match.phase_through ?? "")}"></label>
            <label><span>Saved work flow</span><input data-plan-binding="${index}" data-plan-binding-field="workflow" value="${esc(binding.workflow || "")}"></label>
            <label><span>Team</span><input data-plan-binding="${index}" data-plan-binding-field="team" value="${esc(binding.team || "")}"></label>
          </div>
          <label><span>Review criteria</span><textarea data-plan-binding="${index}" data-plan-binding-field="rubrics">${esc((binding.rubrics || []).join("\n"))}</textarea><small>One saved review-criteria name per line.</small></label>
          <div class="studio-plan-route-actions"><a href="#/program-studio/workflow/${encodeURIComponent(binding.workflow || "")}">Open this work flow</a><button type="button" class="danger" data-plan-remove-binding="${index}">Remove route</button></div>
        </fieldset>`;
      }).join("") || '<p class="studio-plan-empty">Add a route to connect scoped work to a saved work flow.</p>'}
      <button type="button" data-plan-add-binding>+ Add a work route</button>
      <p class="studio-plan-note">Exact input mappings remain unchanged and editable under Technical details.</p>
    </div>`;
  }
  if (section.id === "decisions") {
    return `<div class="studio-plan-editor-list">
      ${gates.map((gate, index) => `<fieldset class="studio-plan-route"><legend>Phase decision ${index + 1}</legend>
        <div class="studio-plan-form-grid">
          <label><span>Decision name</span><input data-plan-gate="${index}" data-plan-gate-field="id" value="${esc(gate.id || "")}"></label>
          <label><span>Decision owner</span><input data-plan-gate="${index}" data-plan-gate-field="role" value="${esc(gate.role || "")}"></label>
          <label><span>Review criteria</span><input data-plan-gate="${index}" data-plan-gate-field="rubric" value="${esc(gate.rubric || "")}"></label>
          <label><span>If review does not pass</span><select data-plan-gate="${index}" data-plan-gate-field="on_fail">${["block", "checkpoint", "abort"].map((value) => `<option value="${value}"${gate.on_fail === value ? " selected" : ""}>${value === "block" ? "Stop with a blocker" : value === "checkpoint" ? "Ask for a decision" : "End this delivery"}</option>`).join("")}</select></label>
        </div>
        <button type="button" class="danger" data-plan-remove-gate="${index}">Remove decision</button>
      </fieldset>`).join("") || '<p class="studio-plan-empty">No phase completion decision is defined.</p>'}
      <button type="button" data-plan-add-gate>+ Add a phase decision</button>
    </div>`;
  }
  if (section.id === "stops") {
    return `<fieldset class="studio-plan-checks"><legend>Stop whenever…</legend>${Object.entries(stopLabels).map(([stop, label]) => `<label><input type="checkbox" data-studio-stop="${stop}"${(document.stop_conditions || []).includes(stop) ? " checked" : ""}><span>${esc(label)}</span></label>`).join("")}</fieldset>`;
  }
  if (section.id === "limits") {
    return `<div class="studio-plan-limit-grid">${Object.entries(document.budgets || {}).map(([key, value]) => `<label><span>${esc(key.replace(/^max_/, "Maximum ").replaceAll("_", " "))}</span><input type="number" min="1" data-studio-budget="${esc(key)}" value="${esc(value)}"></label>`).join("")}</div><p class="studio-plan-note">Every saved finite limit remains exact. Technical details exposes the complete field names and compiled envelope.</p>`;
  }
  return `${studioPlanItemList(section.items)}${section.id === "recovery" ? '<p class="studio-plan-note">Detailed repair prompts and exact failure conditions remain available under Technical details.</p>' : ""}`;
}

function studioWorkflowStepEditor() {
  const graphNode = studioGraphNode(studioState.selected);
  const raw = studioRawNode(graphNode);
  if (!raw) return '<p class="studio-plan-empty">Choose a work step to edit it.</p>';
  return `<fieldset class="studio-plan-step-editor"><legend>Edit ${esc(graphNode?.label || raw.id)}</legend>
    ${studioInput("Step name", "node.id", raw.id, "text", "", `${graphNode.pointer}/id`)}
    ${studioInput("Step title", "node.title", raw.title || "", "text", "", `${graphNode.pointer}/title`)}
    ${studioArea("What happens here?", raw.prompt !== undefined ? "node.prompt" : raw.task !== undefined ? "node.task" : "node.description", raw.prompt ?? raw.task ?? raw.description ?? "", "", `${graphNode.pointer}/${raw.prompt !== undefined ? "prompt" : raw.task !== undefined ? "task" : "description"}`)}
    ${studioArea("After these steps", "node.needs", (raw.needs || []).join("\n"), "One earlier step name per line.", `${graphNode.pointer}/needs`)}
    ${raw.role !== undefined ? studioInput(raw.type === "verdict" ? "Review owner" : "Work owner", "node.role", raw.role || "", "text", "", `${graphNode.pointer}/role`) : ""}
    ${raw.rubric !== undefined ? studioInput("Review criteria", "node.rubric", raw.rubric || "", "text", "", `${graphNode.pointer}/rubric`) : ""}
    ${raw.workflow !== undefined ? studioInput("Saved detailed work flow", "node.workflow", raw.workflow || "", "text", "", `${graphNode.pointer}/workflow`) : ""}
    ${raw.max_rounds !== undefined ? studioInput("Maximum rounds", "node.max_rounds", raw.max_rounds, "number", 'min="1"', `${graphNode.pointer}/max_rounds`) : ""}
    ${raw.quorum !== undefined ? studioInput("Required reviewer agreement", "node.quorum", raw.quorum, "number", 'min="1"', `${graphNode.pointer}/quorum`) : ""}
    ${raw.expires_seconds !== undefined ? studioInput("Decision expires after seconds", "node.expires_seconds", raw.expires_seconds, "number", 'min="1"', `${graphNode.pointer}/expires_seconds`) : ""}
    <div class="studio-inspector-actions"><button type="button" id="studio-duplicate-node">Duplicate step</button><button type="button" class="danger" id="studio-delete-node">Remove step</button></div>
    <p class="studio-plan-note">Exact outcome conditions, inputs, outputs, allowed actions, and advanced bounds are preserved under Technical details.</p>
  </fieldset>`;
}

function studioWorkflowPlanEditor(section) {
  const document = studioState.document || {};
  if (section.id === "scope") {
    const parameters = document.parameters || [];
    return `<form class="studio-plan-form">
      ${studioInput("Flow name", "document.slug", document.slug, "text", 'pattern="[a-z][a-z0-9_-]*"', "/slug")}
      ${studioInput("Flow title", "document.title", document.title, "text", "", "/title")}
      ${studioArea("What delivery outcome does this flow produce?", "document.description", document.description || "", "", "/description")}
      <div class="studio-plan-editor-list">${parameters.map((parameter, index) => `<fieldset class="studio-plan-input"><legend>Work input ${index + 1}</legend>
        <div class="studio-plan-form-grid">
          <label><span>Input name</span><input data-plan-input="${index}" data-plan-input-field="id" value="${esc(parameter.id || "")}"></label>
          <label><span>Value type</span><select data-plan-input="${index}" data-plan-input-field="type">${["string", "integer", "boolean", "string-list"].map((value) => `<option value="${value}"${parameter.type === value ? " selected" : ""}>${esc(value.replace("-", " "))}</option>`).join("")}</select></label>
          <label class="studio-plan-toggle"><input type="checkbox" data-plan-input="${index}" data-plan-input-field="required"${parameter.required ? " checked" : ""}><span>Required before work starts</span></label>
          <label><span>Default value</span><input data-plan-input="${index}" data-plan-input-field="default" value="${esc(document.defaults?.[parameter.id] ?? "")}"></label>
        </div><button type="button" class="danger" data-plan-remove-input="${index}">Remove input</button>
      </fieldset>`).join("") || '<p class="studio-plan-empty">This flow needs no named work input.</p>'}</div>
      <button type="button" data-plan-add-input>+ Add a work input</button>
    </form>`;
  }
  if (section.id === "flow") {
    const ordinaryTypes = ["agent", "check", "verdict", "checkpoint"];
    const advancedTypes = STUDIO_NODE_TYPES.filter((type) => !ordinaryTypes.includes(type));
    return `<div class="studio-plan-flow-editor">
      <div class="studio-plan-add" aria-label="Add a delivery step">${ordinaryTypes.map((type) => `<button type="button" data-studio-add="${type}">+ ${esc({ agent: "Do work", check: "Run a check", verdict: "Review an outcome", checkpoint: "Ask for a decision" }[type])}</button>`).join("")}</div>
      <details class="studio-plan-advanced"><summary>Advanced flow building blocks</summary><p>Use these only when the delivery needs nested work, bounded repetition, multi-perspective discussion, or exact delivery actions.</p><div>${advancedTypes.map((type) => `<button type="button" data-studio-add="${type}">+ ${esc(type.replaceAll("_", " "))}</button>`).join("")}</div></details>
      ${studioPlanItemList(section.items, true)}
      ${studioWorkflowStepEditor()}
    </div>`;
  }
  return `${studioPlanItemList(section.items, true)}${section.id === "limits" ? studioPlanFactList(section.facts) : ""}`;
}

const TEAM_DUTY_LABELS = {
  implementer: "Implementation",
  verifier: "Independent review",
  "meta-verifier": "Review audit",
  "master-architect": "Architecture review",
  researcher: "Research",
  reviewer: "Review",
  repairer: "Repair",
  critic: "Critical perspective",
  judge: "Contested decision",
};

function studioOrganizationRoles() {
  return (studioState.document?.teams || []).flatMap((team, teamIndex) => (
    (team.roles || []).map((role, roleIndex) => ({
      team, teamIndex, role, roleIndex,
      model: (studioAuthoring()?.responsibilities || []).find((item) => item.id === role.id),
    }))
  ));
}

function studioTeamRoleLabel(role) {
  return TEAM_DUTY_LABELS[role?.duty] || String(role?.id || "Responsibility").replaceAll("-", " ");
}

function studioTeamRoleOptions(selected = "", includeBlank = false) {
  const values = studioOrganizationRoles();
  return `${includeBlank ? '<option value="">No separate responsibility</option>' : ""}${values.map(({ role }) => `<option value="${esc(role.id)}"${role.id === selected ? " selected" : ""}>${esc(studioTeamRoleLabel(role))}</option>`).join("")}`;
}

function studioTeamResponsibilitiesEditor() {
  const document = studioState.document || {};
  const pools = document.pools || [];
  const roles = studioOrganizationRoles();
  return `<div class="studio-team-editor" data-team-section="responsibilities">
    <form class="studio-plan-form studio-team-intro">
      ${studioInput("Team design name", "document.slug", document.slug, "text", 'pattern="[a-z][a-z0-9_-]*"', "/slug")}
      ${studioInput("Team design title", "document.title", document.title, "text", "", "/title")}
      ${studioArea("What is this team responsible for?", "document.description", document.description || "", "A short purpose visible during review.", "/description")}
    </form>
    <div class="studio-team-card-grid">${roles.map(({ team, teamIndex, role, roleIndex, model }) => {
      const pointer = `/teams/${teamIndex}/roles/${roleIndex}`;
      const primary = (model?.primary_candidates || []).map((item) => item.label);
      const backups = (model?.backup_candidates || []).map((item) => item.label);
      return `<fieldset class="studio-team-card"><legend>${esc(model?.label || studioTeamRoleLabel(role))}</legend>
        <div class="studio-team-card-head"><div><span>${esc(team.id)}</span><strong>${esc(model?.responsibility || "Performs the saved bounded responsibility.")}</strong></div>${badge(role.required ? "required" : "optional", role.required ? "ok" : "")}</div>
        <div class="studio-plan-form-grid">
          <label><span>Responsibility name</span><input id="${esc(studioFieldId(`${pointer}/id`))}" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="id" value="${esc(role.id || "")}"></label>
          <label><span>Kind of work</span><select id="${esc(studioFieldId(`${pointer}/duty`))}" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="duty">${Object.entries(TEAM_DUTY_LABELS).map(([value, label]) => `<option value="${esc(value)}"${role.duty === value ? " selected" : ""}>${esc(label)}</option>`).join("")}</select></label>
          <label><span>First-choice candidate group</span><select id="${esc(studioFieldId(`${pointer}/pool`))}" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="pool">${pools.map((pool) => `<option value="${esc(pool.id)}"${pool.id === role.pool ? " selected" : ""}>${esc(String(pool.id).replaceAll("-", " "))}</option>`).join("")}</select></label>
          <label><span>Number of places</span><input id="${esc(studioFieldId(`${pointer}/cardinality`))}" type="number" min="1" max="16" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="cardinality" value="${esc(role.cardinality ?? 1)}"></label>
          <label class="studio-plan-toggle"><input id="${esc(studioFieldId(`${pointer}/required`))}" type="checkbox" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="required"${role.required ? " checked" : ""}><span>This responsibility must be filled</span></label>
        </div>
        <dl class="studio-team-coverage"><div><dt>First in line</dt><dd>${esc(primary.join(", ") || "No compatible candidate")}</dd></div><div><dt>Backups</dt><dd>${esc(backups.join(", ") || "No backup candidate")}</dd></div></dl>
        <p>${esc(model?.when || "")}</p><small>${esc(model?.outcomes || "")}</small>
      </fieldset>`;
    }).join("") || '<p class="studio-plan-empty">Add implementation and independent-review responsibilities under Technical details.</p>'}</div>
    <p class="studio-plan-note">Candidate profiles, exact permissions, packet limits, schemas, and stable IDs remain visible and losslessly editable under Technical details.</p>
  </div>`;
}

function studioTeamIndependenceEditor() {
  const authoring = studioAuthoring() || {};
  const entries = studioOrganizationRoles();
  const constraints = authoring.quality_constraints || [];
  return `<div class="studio-team-editor" data-team-section="independence">
    <div class="studio-quality-constraints">${constraints.map((item) => `<article class="${item.status === "needs-attention" ? "issue" : "ready"}"><div><strong>${esc((item.labels || []).join(" ↔ "))}</strong>${badge(item.status === "runtime-proven" ? "proven in this assignment" : item.status === "policy-ready" ? "compatible candidates exist" : "must be checked at assignment", item.status === "needs-attention" ? "issue" : "ok")}</div><p>${esc(item.summary)}</p><small>${esc(item.runtime_claim)}</small>${item.status === "needs-attention" ? `<em>${esc(item.correction)}</em>` : ""}</article>`).join("") || '<p class="studio-plan-empty">No independent-review relationship has been declared.</p>'}</div>
    <div class="studio-plan-editor-list">${entries.map(({ team, teamIndex, role, roleIndex, model }) => {
      const peers = (team.roles || []).filter((item) => item !== role);
      const pointer = `/teams/${teamIndex}/roles/${roleIndex}`;
      return `<fieldset class="studio-team-rule"><legend>${esc(model?.label || studioTeamRoleLabel(role))}</legend>
        <p>${esc(model?.responsibility || "")}</p>
        <label><span>Work-area access</span><select id="${esc(studioFieldId(`${pointer}/workspace`))}" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="workspace"><option value="read-only"${role.workspace === "read-only" ? " selected" : ""}>Read only</option><option value="isolated-worktree"${role.workspace === "isolated-worktree" ? " selected" : ""}>Separate writable work area</option></select></label>
        <div class="studio-team-rule-grid"><fieldset><legend>Must be separate from</legend>${peers.map((peer) => `<label><input type="checkbox" data-team-role-link="${roleIndex}" data-team-team="${teamIndex}" data-team-role-link-field="independent_from" data-team-role-target="${esc(peer.id)}"${(role.independent_from || []).includes(peer.id) ? " checked" : ""}><span>${esc(studioTeamRoleLabel(peer))}</span></label>`).join("") || "<small>No other responsibility in this team.</small>"}</fieldset>
        <fieldset><legend>May review this work</legend>${peers.map((peer) => `<label><input type="checkbox" data-team-role-link="${roleIndex}" data-team-team="${teamIndex}" data-team-role-link-field="may_judge" data-team-role-target="${esc(peer.id)}"${(role.may_judge || []).includes(peer.id) ? " checked" : ""}><span>${esc(studioTeamRoleLabel(peer))}</span></label>`).join("") || "<small>No other responsibility in this team.</small>"}</fieldset></div>
      </fieldset>`;
    }).join("")}</div>
    <aside class="studio-team-honesty"><strong>Compatible policy is not a runtime proof</strong><p>A saved design can prove that different candidates, profiles, and work areas are available. Only a later assignment can prove separate execution identities and work sessions. Provider or model names never prove independence by themselves.</p></aside>
  </div>`;
}

function studioTeamDecisionsEditor() {
  const authoring = studioAuthoring() || {};
  const document = studioState.document || {};
  const roles = studioOrganizationRoles();
  const panels = roles.filter(({ role }) => Number(role.cardinality || 0) > 1);
  const groups = authoring.review_groups || [];
  return `<div class="studio-team-editor" data-team-section="decisions">
    ${panels.length ? `<section class="studio-team-panel"><h3>Review panels</h3>${panels.map(({ role, model }) => `<article><strong>${esc(model?.label || studioTeamRoleLabel(role))}</strong><p>${esc(role.cardinality)} separate places contribute to this responsibility. The saved agreement and decision rules still determine the outcome.</p></article>`).join("")}</section>` : ""}
    <div class="studio-plan-editor-list">${(document.councils || []).map((council, index) => {
      const model = groups.find((item) => item.id === council.id) || {};
      const decision = council.decision || {};
      return `<fieldset class="studio-team-council"><legend>Contested-decision group ${index + 1}</legend>
        <div class="studio-team-card-head"><div><span>Runs only when a saved work flow calls it</span><strong>${esc(model.description || "Declared perspectives discuss one matter before one governed outcome.")}</strong></div>${badge(`${council.quorum || 0} required`)}</div>
        <div class="studio-plan-form-grid">
          <label><span>Group name</span><input id="${esc(studioFieldId(`/councils/${index}/id`))}" data-team-council="${index}" data-team-council-field="id" value="${esc(council.id || "")}"></label>
          <label><span>Required reviewer agreement</span><input id="${esc(studioFieldId(`/councils/${index}/quorum`))}" type="number" min="1" data-team-council="${index}" data-team-council-field="quorum" value="${esc(council.quorum ?? 1)}"></label>
          <label><span>Decision owner</span><select id="${esc(studioFieldId(`/councils/${index}/judge`))}" data-team-council="${index}" data-team-council-field="judge">${studioTeamRoleOptions(council.judge, true)}</select></label>
          <label><span>How agreement is decided</span><select id="${esc(studioFieldId(`/councils/${index}/decision/method`))}" data-team-council="${index}" data-team-council-field="decision.method">${[["majority", "More than half agree"], ["weighted", "Saved perspective weights agree"], ["unanimous", "Every reviewer agrees"], ["judge", "Decision owner chooses"]].map(([value, label]) => `<option value="${value}"${decision.method === value ? " selected" : ""}>${label}</option>`).join("")}</select></label>
          <label class="studio-plan-toggle"><input id="${esc(studioFieldId(`/councils/${index}/distinct_principals`))}" type="checkbox" data-team-council="${index}" data-team-council-field="distinct_principals"${council.distinct_principals ? " checked" : ""}><span>Require different execution identities</span></label>
        </div>
        <fieldset class="studio-team-members"><legend>Participating responsibilities</legend>${roles.map(({ role }) => `<label><input type="checkbox" data-team-council-member="${index}" data-team-role-target="${esc(role.id)}"${(council.members || []).includes(role.id) ? " checked" : ""}><span>${esc(studioTeamRoleLabel(role))}</span></label>`).join("")}</fieldset>
        <p>${esc(model.decision_summary || "")} ${esc(model.decision_owner_summary || "")}</p>
        <details class="studio-plan-advanced"><summary>Objections, dissent, and bounded discussion</summary><p>${esc(model.dissent || "An objection remains visible and follows the saved route.")}</p><p>${esc(model.veto_summary || "")}</p><label><span>Responsibilities with a separate objection right</span><textarea data-team-council="${index}" data-team-council-field="decision.veto_roles">${esc((decision.veto_roles || []).join("\n"))}</textarea><small>One responsibility name per line.</small></label><p class="studio-plan-note">Speaker weights, thresholds, round bounds, artifact bounds, output bounds, token bounds, and time bounds remain exact under Technical details.</p></details>
      </fieldset>`;
    }).join("") || '<section class="studio-plan-empty"><strong>No contested-decision group is defined.</strong><p>Ordinary independent review remains decisive. Add an advanced group in Technical details only when multiple perspectives, a named decision owner, or preserved dissent are required.</p></section>'}</div>
  </div>`;
}

function studioTeamEscalationEditor() {
  const authoring = studioAuthoring() || {};
  return `<div class="studio-team-editor" data-team-section="escalation">
    <div class="studio-plan-editor-list">${studioOrganizationRoles().map(({ team, teamIndex, role, roleIndex, model }) => {
      const replacement = role.replacement || {};
      const route = (authoring.escalation_routes || []).find((item) => item.id === role.id);
      const pointer = `/teams/${teamIndex}/roles/${roleIndex}`;
      return `<fieldset class="studio-team-rule"><legend>${esc(model?.label || studioTeamRoleLabel(role))}</legend>
        <p>${esc(route?.summary || "Choose a finite replacement and handoff rule.")}</p>
        <div class="studio-plan-form-grid">
          <label><span>Maximum replacements</span><input id="${esc(studioFieldId(`${pointer}/replacement/max_replacements`))}" type="number" min="0" max="20" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="replacement.max_replacements" value="${esc(replacement.max_replacements ?? 0)}"></label>
          <label><span>When replacements are exhausted</span><select id="${esc(studioFieldId(`${pointer}/replacement/on_exhausted`))}" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="replacement.on_exhausted">${[["block", "Keep the work blocked"], ["escalate", "Ask the separately authorized delivery owner"], ["checkpoint", "Wait for a named person"], ["abort", "End this delivery"]].map(([value, label]) => `<option value="${value}"${replacement.on_exhausted === value ? " selected" : ""}>${label}</option>`).join("")}</select></label>
          <label><span>Backup candidate groups</span><textarea id="${esc(studioFieldId(`${pointer}/replacement/fallback_pools`))}" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="replacement.fallback_pools">${esc((replacement.fallback_pools || []).join("\n"))}</textarea><small>One saved group per line.</small></label>
          <label class="studio-plan-toggle"><input id="${esc(studioFieldId(`${pointer}/replacement/preserve_history`))}" type="checkbox" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="replacement.preserve_history"${replacement.preserve_history ? " checked" : ""}><span>Keep earlier work, review, and disagreement history</span></label>
        </div>
        <fieldset class="studio-team-members"><legend>May ask these responsibilities for bounded help</legend>${(team.roles || []).filter((item) => item !== role).map((peer) => `<label><input type="checkbox" data-team-role-link="${roleIndex}" data-team-team="${teamIndex}" data-team-role-link-field="may_request" data-team-role-target="${esc(peer.id)}"${(role.may_request || []).includes(peer.id) ? " checked" : ""}><span>${esc(studioTeamRoleLabel(peer))}</span></label>`).join("") || "<small>No other responsibility in this team.</small>"}</fieldset>
      </fieldset>`;
    }).join("")}</div>
    <aside class="studio-team-honesty"><strong>Escalation does not grant authority</strong><p>A delivery-owner escalation leaves this team and waits for separately authorized handling. The team design does not name, create, or impersonate that person.</p></aside>
  </div>`;
}

function studioTeamAuditEditor() {
  const authoring = studioAuthoring() || {};
  const document = studioState.document || {};
  const auditRoles = (authoring.responsibilities || []).filter((item) => ["meta-verifier", "master-architect"].includes(item.technical_details?.duty));
  const metaRoles = studioOrganizationRoles().filter(({ role }) => role.duty === "meta-verifier");
  return `<div class="studio-team-editor" data-team-section="audit">
    <div class="studio-team-audit-roles">${auditRoles.map((item) => `<article><div><strong>${esc(item.name)}</strong>${badge(item.technical_details?.duty === "master-architect" ? "architecture review · declared plan boundary only" : "review of review")}</div><p>${esc(item.responsibility)}</p><small>${esc(item.when)} ${esc(item.outcomes)}</small></article>`).join("") || '<p class="studio-plan-empty">No review auditor or architecture reviewer is enabled by this team design.</p>'}</div>
    <div class="studio-plan-editor-list">${(document.councils || []).map((council, index) => {
      const model = (authoring.review_groups || []).find((item) => item.id === council.id) || {};
      const audit = council.audit || {};
      return `<fieldset class="studio-team-rule"><legend>${esc(model.label || council.id)} review audit</legend>
        <p>${esc(model.audit?.summary || "No separate review audit runs.")}</p>
        <div class="studio-plan-form-grid">
          <label><span>Audit coverage</span><select id="${esc(studioFieldId(`/councils/${index}/audit/mode`))}" data-team-council="${index}" data-team-council-field="audit.mode"><option value="none"${audit.mode === "none" ? " selected" : ""}>No separate audit</option><option value="sample"${audit.mode === "sample" ? " selected" : ""}>Check a sample</option><option value="full"${audit.mode === "full" ? " selected" : ""}>Check every participant result</option></select></label>
          <label><span>Review auditor</span><select id="${esc(studioFieldId(`/councils/${index}/meta_verifier`))}" data-team-council="${index}" data-team-council-field="meta_verifier"><option value="">No review auditor</option>${metaRoles.map(({ role }) => `<option value="${esc(role.id)}"${council.meta_verifier === role.id ? " selected" : ""}>${esc(studioTeamRoleLabel(role))}</option>`).join("")}</select></label>
          <label><span>Results checked</span><input id="${esc(studioFieldId(`/councils/${index}/audit/sample_size`))}" type="number" min="0" data-team-council="${index}" data-team-council-field="audit.sample_size" value="${esc(audit.sample_size ?? 0)}"></label>
          <label><span>If the audit overturns a result</span><select data-team-council="${index}" data-team-council-field="audit.on_overturn">${["repair", "escalate", "block", "checkpoint", "abort"].map((value) => `<option value="${value}"${audit.on_overturn === value ? " selected" : ""}>${esc({ repair: "Request repair", escalate: "Escalate outside the team", block: "Keep work blocked", checkpoint: "Wait for a named person", abort: "End this delivery" }[value])}</option>`).join("")}</select></label>
        </div>
        <p class="studio-plan-note">Architecture review is activated only by a separately declared story or phase gate; defining an architecture responsibility here does not run it.</p>
      </fieldset>`;
    }).join("")}</div>
  </div>`;
}

function studioTeamReviewEditor(section) {
  if (section.id === "responsibilities") return studioTeamResponsibilitiesEditor();
  if (section.id === "independence") return studioTeamIndependenceEditor();
  if (section.id === "decisions") return studioTeamDecisionsEditor();
  if (section.id === "escalation") return studioTeamEscalationEditor();
  return studioTeamAuditEditor();
}

function studioPlanReview() {
  const authoring = studioAuthoring();
  const review = authoring?.review_sections || [];
  const team = studioState.family === "organization";
  return `<aside class="studio-plan-review" aria-label="${team ? "Readable team and review summary" : "Readable plan summary"}"><div><span>Review before save</span><strong>${esc(authoring?.status === "ready-to-review" ? "Ready to review" : "Needs attention")}</strong>${badge(authoring?.status === "ready-to-review" ? "nothing starts" : `${authoring?.corrections?.length || 0} corrections`, authoring?.status === "ready-to-review" ? "ok" : "issue")}</div>
    <dl>${review.map((item) => `<div><dt>${esc(item.label)}</dt><dd>${esc(item.answer)}</dd></div>`).join("")}</dl>
    ${team ? `<p>${esc(authoring?.runtime_independence?.claim || "")}</p>` : ""}
    <p>Drafting, checking, and leaving make no change. Saving still requires a separate review of the exact file change and starts no work.</p>
    <button type="button" id="studio-review-save"${authoring?.status === "ready-to-review" ? "" : " disabled"}>Review this save</button>
  </aside>`;
}

function studioPlanView() {
  const authoring = studioAuthoring();
  if (!authoring) return stateHtml("Checking the delivery decisions…");
  if (!authoring.applicable) return stateHtml("This delivery design has no ordinary authoring view.");
  const section = studioPlanSection() || authoring.sections[0];
  if (section) studioState.planSection = section.id;
  const editor = studioState.family === "program"
    ? studioProgramPlanEditor(section)
    : studioState.family === "workflow"
      ? studioWorkflowPlanEditor(section)
      : studioTeamReviewEditor(section);
  const team = studioState.family === "organization";
  return `<div class="studio-plan" data-plan-status="${esc(authoring.status)}">
    <header><div><span>${team ? "Team and review" : "Delivery decisions"}</span><h2>${team ? "Make ownership, independence, and decisions understandable" : "Build the plan in the order people review it"}</h2><p>${esc(authoring.summary)}</p></div>${badge(authoring.status === "ready-to-review" ? "ready to review" : "needs attention", authoring.status === "ready-to-review" ? "ok" : "issue")}</header>
    <div class="studio-plan-shell">
      <nav class="studio-plan-sections" aria-label="${team ? "Team and review sections" : "Delivery plan sections"}">${authoring.sections.map((item) => `<button type="button" data-plan-section="${esc(item.id)}" class="${item.id === section.id ? "active" : ""}" aria-current="${item.id === section.id ? "step" : "false"}"><span>${item.step}</span><strong>${esc(item.label)}</strong>${item.correction_count ? `<small>${item.correction_count} to fix</small>` : "<small>ready</small>"}</button>`).join("")}</nav>
      <main class="studio-plan-section" id="studio-plan-section" tabindex="-1"><header><span>Step ${section.step} of ${authoring.sections.length}</span><h2>${esc(section.question)}</h2><p>${esc(section.guidance)}</p><strong>${esc(section.answer)}</strong></header>
        ${studioPlanCorrections(section.id)}${editor}${section.id !== "limits" ? studioPlanFactList(section.facts) : ""}${studioPlanExamples()}
      </main>
      ${studioPlanReview()}
    </div>
  </div>`;
}

function studioTechnicalView() {
  const team = studioState.family === "organization";
  return `<div class="studio-technical-view"><header><div><span class="orch-eyebrow">Technical details</span><h2>${team ? "Exact responsibilities, provenance, and configuration" : "Exact graph, fields, and configuration"}</h2><p>${team ? "Inspect stable role IDs, candidate profiles, provider and model resolution, auth and principal fingerprints, work areas, sessions, packet bounds, decision rules, and the lossless source." : "Use this view for hierarchical flows, bounded loops, discussion cells, exact conditions, raw import/export, and source-level diagnostics."}</p></div>${badge("same source document", "ok")}</header>
    <div class="studio-technical-tabs" role="tablist" aria-label="Technical editor mode"><button type="button" id="studio-technical-tab-graph" role="tab" aria-controls="studio-technical-panel" aria-selected="${studioState.technicalMode === "graph"}" tabindex="${studioState.technicalMode === "graph" ? "0" : "-1"}" data-studio-technical="graph" class="${studioState.technicalMode === "graph" ? "active" : ""}">Graph and fields</button><button type="button" id="studio-technical-tab-config" role="tab" aria-controls="studio-technical-panel" aria-selected="${studioState.technicalMode === "config"}" tabindex="${studioState.technicalMode === "config" ? "0" : "-1"}" data-studio-technical="config" class="${studioState.technicalMode === "config" ? "active" : ""}">Lossless configuration</button></div>
    <div id="studio-technical-panel" role="tabpanel" aria-labelledby="studio-technical-tab-${esc(studioState.technicalMode)}">${studioState.technicalMode === "config" ? studioJsonView() : studioDesignView()}</div>
  </div>`;
}

function studioExecutionContractHtml(contract, compact = false) {
  if (!contract) return '<p class="hint">No organization execution contract is reachable from this policy.</p>';
  const ports = contract.ports || [];
  const fallbacks = contract.fallbacks || [];
  const councils = contract.councils || [];
  const diversity = contract.diversity || {};
  return `<div class="studio-execution-contract${compact ? " compact" : ""}">
    <section><h3>portable execution ports / local resolution</h3>${ports.map((port) => { const local = port.local_resolution || {}; const constraints = port.constraints || {}; return `<article><div><strong>${esc(port.agent)}</strong>${badge(local.configured ? (local.available ? "available" : "unavailable") : "unconfigured", local.available ? "ok" : "warn")}</div><code>${esc(port.selector?.profile)}</code><span>${esc((constraints.duties || []).join(", "))} · ${esc(local.harness || "unresolved")} / ${esc(local.provider || "—")} / ${esc(local.model || local.model_family || "—")}</span><small>auth <code>${esc(local.auth_domain_fingerprint || "—")}</code> · principal <code>${esc(local.principal_fingerprint || "—")}</code></small><small>work area <code>${esc(constraints.workspace_domain || "—")}</code> · session binding not assigned before runtime</small></article>`; }).join("") || '<p class="hint">This policy family declares no logical execution profile.</p>'}${contract.local_resolution_issue ? `<p class="guard">${esc(contract.local_resolution_issue)}</p>` : ""}</section>
    <section><h3>fallback and replacement policy</h3>${fallbacks.map((item) => `<article><div><strong>${esc(item.team)} / ${esc(item.role)}</strong>${badge(`${esc(item.max_replacements)} replacement${Number(item.max_replacements) === 1 ? "" : "s"}`)}</div><span>${esc(item.primary_pool)} → ${esc((item.fallback_pools || []).join(", ") || "no fallback pool")}</span><small>${esc((item.reasons || []).join(", ") || "no eligible reason")} · exhausted → ${esc(item.on_exhausted)}</small></article>`).join("") || '<p class="hint">No replacement policy is reachable.</p>'}</section>
    <section><h3>council perspectives / authority / obligations</h3>${councils.map((item) => `<article><div><strong>${esc(item.id)}</strong>${badge(item.decision_authority === "judge" ? "agent judge" : `rule · ${item.decision_authority}`, item.decision_authority === "judge" ? "warn" : "ok")}</div><span>${(item.perspectives || []).map((perspective) => `${esc(perspective.role)}:${esc(perspective.perspective)}`).join(" · ")}</span><small>quorum ${esc(item.quorum)} · principals ${esc(item.principal_diversity)} · meta ${esc(item.meta_verifier || "none")} · veto ${esc((item.veto_roles || []).join(", ") || "none")}</small><small>obligations required · ${esc((item.obligation_policy?.allowed_kinds || []).join(", "))} · blocking stops progress</small></article>`).join("") || '<p class="hint">No council policy is reachable.</p>'}</section>
    <section><h3>diversity contract and observed roster</h3><dl class="studio-diversity"><div><dt>separation edges</dt><dd>${esc((diversity.independence || []).length)}</dd></div><div><dt>providers observed</dt><dd>${esc(diversity.resolved_provider_count || 0)}</dd></div><div><dt>model families observed</dt><dd>${esc(diversity.resolved_model_family_count || 0)}</dd></div><div><dt>principals observed</dt><dd>${esc(diversity.resolved_principal_count || 0)}</dd></div><div><dt>auth domains observed</dt><dd>${esc(diversity.resolved_auth_domain_count || 0)}</dd></div></dl><p class="hint">Provider/model counts are local observations. Exact logical profiles, principal separation, fallbacks, and council authority remain tracked policy; a later grant freezes resolved fingerprints.</p></section>
  </div>`;
}

function studioOrganizationOverview() {
  const document = studioState.document;
  return `<div class="studio-org-overview"><h3>team / verifier topology</h3>${(document.teams || []).map((team) => `<section><strong>${esc(team.id)}</strong><div>${(team.roles || []).map((role) => `${badge(`${role.duty} · ${role.cardinality}`, role.duty === "verifier" || role.duty === "meta-verifier" ? "ok" : "")} `).join("")}</div><small>${(team.roles || []).filter((role) => (role.independent_from || []).length).map((role) => `${role.id} independent from ${role.independent_from.join(", ")}`).join(" · ") || "No separation edge declared."}</small></section>`).join("") || '<p class="hint">No team policy yet; author agents, pools, teams, and councils in JSON.</p>'}<h3>councils / meta-verification</h3>${(document.councils || []).map((council) => `<section><strong>${esc(council.id)}</strong><span>${esc((council.members || []).join(" + "))}</span><small>judge ${esc(council.judge)} · quorum ${esc(council.quorum)} · meta ${esc(council.meta_verifier || "none")} · ${esc(council.decision?.method || "declared default")}</small></section>`).join("") || '<p class="hint">No council declared.</p>'}<h3>execution contract</h3>${studioExecutionContractHtml(studioState.model?.authority?.execution_contract, true)}<p class="studio-help">Use the lossless JSON view to author logical profiles, packet constraints, independence, fallbacks, council rules, and obligation authority. Local availability is inspection-only and never saved into portable policy.</p></div>`;
}

function studioNodeInspector(node) {
  if (!node) return studioDocumentInspector();
  const raw = studioRawNode(node);
  const diagnostics = (studioState.model.validation?.diagnostics || []).filter((item) => item.target?.node_id === node.id);
  const drilldown = node.drilldown?.name ? `<a class="studio-drilldown" href="#/program-studio/workflow/${encodeURIComponent(node.drilldown.name)}">open nested workflow ${esc(node.drilldown.name)} ↗</a>` : "";
  return `<div class="studio-inspector-head"><div><small>${esc(node.type)} · ${esc(node.lane)}</small><strong>${esc(node.label)}</strong></div>${badge(node.container ? "finite container" : "graph node", node.container ? "warn" : "")}</div>
    ${diagnostics.length ? `<div class="studio-node-errors">${diagnostics.map((item) => `<button type="button" data-studio-diagnostic="${esc(item.pointer)}" data-node-id="${esc(item.target?.node_id || "")}" data-field-id="${esc(item.target?.field_id || "")}"><code>${esc(item.pointer)}</code>${esc(item.message)}</button>`).join("")}</div>` : ""}
    ${raw ? `<form id="studio-node-form" class="studio-inspector-form">
      ${studioInput("node id", "node.id", raw.id, "text", "", `${node.pointer}/id`)}
      ${studioInput("title", "node.title", raw.title || "", "text", "", `${node.pointer}/title`)}
      ${studioArea("description", "node.description", raw.description || "", "", `${node.pointer}/description`)}
      ${raw.role !== undefined ? studioInput("assigned role", "node.role", raw.role || "", "text", "", `${node.pointer}/role`) : ""}
      ${raw.workflow !== undefined ? studioInput("nested workflow", "node.workflow", raw.workflow || "", "text", "", `${node.pointer}/workflow`) : ""}
      ${raw.max_rounds !== undefined ? studioInput("maximum rounds", "node.max_rounds", raw.max_rounds, "number", 'min="1"', `${node.pointer}/max_rounds`) : ""}
      ${raw.quorum !== undefined ? studioInput("quorum", "node.quorum", raw.quorum, "number", 'min="1"', `${node.pointer}/quorum`) : ""}
      ${raw.capability_ceiling !== undefined ? studioArea("capability ceiling", "node.capability_ceiling", (raw.capability_ceiling || []).join("\n"), "one exact capability per line", `${node.pointer}/capability_ceiling`) : ""}
      ${raw.participants !== undefined ? studioArea("debate speakers", "node.participants", (raw.participants || []).join("\n"), "judge remains a separate role", `${node.pointer}/participants`) : ""}
    </form><div class="studio-inspector-actions"><button type="button" id="studio-duplicate-node">duplicate node</button><button type="button" class="danger" id="studio-delete-node">delete node</button></div>` : ""}
    ${drilldown}
    <details open><summary>exact governed fields</summary><pre>${esc(JSON.stringify(raw || node.summary || node, null, 2))}</pre></details>`;
}

function studioDesignView() {
  const node = studioGraphNode(studioState.selected);
  const palette = studioState.family === "workflow" ? `<div class="studio-palette" aria-label="hierarchical workflow node palette"><button type="button" data-studio-settings>workflow settings</button>${STUDIO_NODE_TYPES.map((type) => `<button type="button" data-studio-add="${type}">+ ${type.replace("_", " ")}</button>`).join("")}</div>` : `<div class="studio-palette"><button type="button" data-studio-settings>${esc(studioState.family)} settings</button><span>Graph positions are document-only layout; every contract field remains available in JSON.</span></div>`;
  return `<div class="studio-design">${palette}<div class="studio-workarea">${studioGraphHtml()}</div><aside class="studio-inspector" aria-label="${esc(studioState.family)} policy inspector">${node ? studioNodeInspector(node) : studioDocumentInspector()}</aside></div>`;
}

function studioScenarioSummary(scenario) {
  const simulation = studioState.model?.simulation || {};
  const graph = studioState.model?.graph || {};
  if (scenario === "candidate-assignment") {
    const selection = simulation.selection || {};
    return `<div class="studio-scenario-summary"><strong>${esc(selection.story || "No eligible story selected")}</strong><span>${esc(selection.reason || "The shared planner explains every scoped candidate.")}</span>${simulation.assignment ? `<small>${esc(simulation.assignment.implementer?.profile || "implementer")} → independent verifier ${esc(simulation.assignment.verifier?.profile || "unresolved")}</small>` : ""}</div>`;
  }
  const active = (graph.nodes || []).filter((node) => {
    if (scenario === "debate-active") return node.type === "debate" || node.type === "council";
    if (scenario === "verifier-failed") return ["verdict", "verifier", "meta-verifier"].includes(node.type);
    if (scenario === "budget-exhausted") return node.container || node.type === "scope";
    if (scenario === "phase-transition") return node.type === "architect-gate" || node.type === "master-architect";
    if (scenario === "nested") return ["subflow", "loop"].includes(node.type);
    return false;
  });
  return `<div class="studio-scenario-summary"><strong>${esc(scenario.replaceAll("-", " "))}</strong><span>${active.length ? `${active.length} delivery step${active.length === 1 ? "" : "s"} involved` : "This route is not present in the plan."}</span><small>Inspection example only—nothing starts and no permission is created.</small></div>`;
}

function studioSimulationDetails() {
  const simulation = studioState.model?.simulation;
  if (!simulation) return `<p class="hint">Resolve compiler diagnostics to obtain a pure scheduling simulation.</p>`;
  if (studioState.family === "program") return `<div class="studio-sim-grid"><section><h3>roadmap candidates</h3>${(simulation.candidates || []).map((candidate) => `<div class="studio-candidate"><code>${esc(candidate.story)}</code>${badge(candidate.reason, candidate.eligible ? "ok" : "")}<span>${esc(candidate.phase)}</span></div>`).join("") || '<p class="hint">No scoped candidates.</p>'}</section><section><h3>preassigned organization</h3><pre>${esc(JSON.stringify(simulation.assignment || simulation.issues || {}, null, 2))}</pre></section></div>`;
  if (studioState.family === "workflow") return `<div class="studio-sim-grid"><section><h3>finite scheduling waves</h3>${(simulation.waves || []).map((wave, index) => `<div class="studio-wave"><strong>wave ${esc(wave.wave ?? index + 1)}</strong><span>${esc((wave.scheduled || wave).join?.(", ") || JSON.stringify(wave))}</span></div>`).join("")}</section><section><h3>worst-case envelope</h3>${Object.entries(simulation.envelopes?.worst_case || {}).map(([key, value]) => `<div class="kv"><div class="k">${esc(key)}</div><div class="v">${esc(value)}</div></div>`).join("")}</section><section><h3>loops / debate routes</h3><pre>${esc(JSON.stringify({ loops: simulation.loops || [], debates: simulation.debates || [], routes: simulation.routes || [] }, null, 2))}</pre></section></div>`;
  return `<div class="studio-sim-grid"><section><h3>team concurrency and separation</h3><pre>${esc(JSON.stringify(simulation.teams || [], null, 2))}</pre></section><section><h3>councils, quorum, meta-audit</h3><pre>${esc(JSON.stringify(simulation.councils || [], null, 2))}</pre></section></div>`;
}

function studioSimulateView() {
  const scenarios = studioState.model?.simulation_scenarios || [];
  const current = scenarios.find((item) => item.id === studioState.scenario) || scenarios.find((item) => item.available) || scenarios[0];
  if (current) studioState.scenario = current.id;
  return `<div class="studio-simulation" data-scenario="${esc(studioState.scenario)}"><header><div><span class="orch-eyebrow">Try the delivery flow</span><h2>See how work could move before saving or requesting permission</h2><p>This is an inspection-only example. It starts no work and changes no plan.</p></div>${badge("starts nothing", "ok")}</header><div class="studio-scenario-tabs" role="tablist" aria-label="Delivery examples">${scenarios.map((scenario) => `<button type="button" id="studio-scenario-tab-${esc(scenario.id)}" role="tab" aria-controls="studio-scenario-panel" data-studio-scenario="${esc(scenario.id)}" aria-selected="${scenario.id === studioState.scenario}" tabindex="${scenario.id === studioState.scenario ? "0" : "-1"}"${scenario.available ? "" : " disabled"}>${esc(scenario.label)}</button>`).join("")}</div><div id="studio-scenario-panel" role="tabpanel" aria-labelledby="studio-scenario-tab-${esc(studioState.scenario)}">${studioScenarioSummary(studioState.scenario)}${studioSimulationDetails()}</div></div>`;
}

function studioValidateView() {
  const model = studioState.model;
  if (!model) return stateHtml("Checking this delivery plan…");
  const validation = model.validation || { valid: false, diagnostics: [] };
  const diagnostics = validation.diagnostics || [];
  const corrections = studioAuthoring()?.corrections || [];
  const hashes = model.round_trip?.hashes_before || {};
  const team = studioState.family === "organization";
  const subject = team ? "team and review design" : "plan";
  return `<div class="studio-validation ${validation.valid ? "valid" : "invalid"}"><header><div><span class="orch-eyebrow">${team ? "Check responsibilities and independence" : "Check the delivery decisions"}</span><h2>${validation.valid ? `This ${subject} is ready to review` : `${corrections.length} ${team ? "team or review rule" : "delivery decision"}${corrections.length === 1 ? "" : "s"} need attention`}</h2><p>${validation.valid ? (team ? "Responsibilities, independent review, decisions, escalation, and audit rules agree." : "Scope, flow, review, decisions, recovery, stops, and limits agree.") : `Fix the affected ${team ? "responsibility or quality constraint" : "decision"} below; the saved ${subject} remains unchanged.`}</p></div>${badge(validation.valid ? "ready" : "needs attention", validation.valid ? "ok" : "issue")}</header>
    ${corrections.length ? `<ol class="studio-decision-diagnostics">${corrections.map((item) => `<li><div><span>${esc(item.decision)}</span><strong>${esc(item.affected_behavior)}</strong><p>${esc(item.correction)}</p></div><button type="button" data-plan-correction="${esc(item.section_id)}" data-plan-node="${esc(item.target?.node_id || "")}" data-plan-field="${esc(item.target?.field_id || "")}">Fix this decision</button></li>`).join("")}</ol>` : '<p class="studio-green">The exact source is valid, and reviewing this result starts no work.</p>'}
    <details class="studio-validation-technical"><summary>Technical details</summary>
      <div class="studio-hashes"><div><span>semantic</span><code>${esc(hashes.semantic || "unavailable until valid")}</code></div><div><span>document</span><code>${esc(hashes.document || "unavailable until valid")}</code></div><div><span>layout</span><code>${esc(hashes.layout)}</code></div></div>
      <section class="studio-roundtrip"><strong>graph ⇄ config</strong>${badge(model.round_trip?.lossless ? "lossless" : "mismatch", model.round_trip?.lossless ? "ok" : "issue")} ${badge(model.round_trip?.semantic_hash_preserved ? "semantic hash preserved" : "semantic unavailable", model.round_trip?.semantic_hash_preserved ? "ok" : "")} ${badge(model.round_trip?.layout_hash_preserved ? "layout hash preserved" : "layout mismatch", model.round_trip?.layout_hash_preserved ? "ok" : "issue")}</section>
      ${diagnostics.length ? `<ol class="studio-diagnostics">${diagnostics.map((item) => `<li><button type="button" data-studio-diagnostic="${esc(item.pointer)}" data-node-id="${esc(item.target?.node_id || "")}" data-field-id="${esc(item.target?.field_id || "")}"><code>${esc(item.pointer)}</code><strong>${esc(item.code)}</strong><span>${esc(item.message)}</span><small>${esc(item.remediation)}</small></button></li>`).join("")}</ol>` : '<p class="studio-green">The exact configuration passed the shared checker.</p>'}
    </details>
  </div>`;
}

function studioJsonView() {
  const value = studioState.jsonDraft || JSON.stringify(studioState.document, null, 2);
  return `<div class="studio-json"><header><div><span class="orch-eyebrow">lossless configuration</span><h2>Every contract field, portable and reviewable</h2></div>${badge("same compiler", "ok")}</header>${studioState.jsonPointer ? `<div class="studio-json-target"><span>compiler target</span><code>${esc(studioState.jsonPointer)}</code></div>` : ""}<div class="studio-json-actions"><button type="button" id="studio-json-apply">apply JSON to graph</button><label class="filebtn">import JSON<input type="file" id="studio-json-import" accept="application/json,.json"></label></div><div id="studio-json-error" class="guard" role="alert" hidden></div><label><span>${esc(studioState.family)} JSON</span><textarea id="studio-json-text" spellcheck="false" aria-describedby="studio-json-error">${esc(value)}</textarea></label></div>`;
}

function studioAuthorityView() {
  const authority = studioState.model?.authority;
  if (!authority) return stateHtml("Waiting for authority explanation…");
  return `<div class="studio-authority"><header><div><span class="orch-eyebrow">policy request ≠ runtime authority</span><h2>What a later exact grant could—and could not—authorize</h2></div>${badge("creates no grant", "ok")}</header><div class="studio-mode-grid">${authority.modes.map((mode) => `<article class="${mode.within_ceiling ? "within" : "denied"}"><span>${esc(mode.id)}</span><strong>${esc(mode.label)}</strong><p>${esc(mode.meaning)}</p><small>${mode.within_ceiling ? "within authored ceiling" : "above authored ceiling"} · ${mode.dispatch ? "bounded dispatch possible only after grant" : "no dispatch"}</small></article>`).join("")}</div><div class="studio-capability-groups">${authority.groups.map((group) => `<section><h3>${esc(group.label)}</h3>${group.capabilities.map((capability) => `<div class="studio-capability ${capability.requested ? "requested" : "absent"}"><code>${esc(capability.id)}</code>${badge(capability.requested ? "requested in policy" : "not requested", capability.requested ? "warn" : "")}</div>`).join("")}</section>`).join("")}</div>${studioExecutionContractHtml(authority.execution_contract)}<div class="studio-authority-foot"><section><h3>finite budgets</h3><pre>${esc(JSON.stringify(authority.budgets || {}, null, 2))}</pre></section><section><h3>declared stops</h3><p>${(authority.stop_conditions || []).map((stop) => badge(stop)).join(" ") || "None on this policy family."}</p></section></div><p class="studio-no-grant">This is an inspection-only preview. Save writes tracked policy only; neither view nor Save grants a capability, starts work, creates a run, or advances the roadmap. Resolved profiles expose fingerprints, never credentials or arbitrary commands.</p></div>`;
}

function studioBody() {
  if (studioState.view === "simulate") return studioSimulateView();
  if (studioState.view === "validate") return studioValidateView();
  if (studioState.view === "technical") return studioTechnicalView();
  if (studioState.view === "authority") return studioAuthorityView();
  return studioPlanView();
}

function renderProgramStudio() {
  const focus = captureAppFocus();
  const family = studioFamilyModel();
  const items = family?.items || [];
  const document = studioState.document || family?.draft || {};
  const validation = studioState.model?.validation;
  const empty = studioState.inventory?.empty;
  const familyLabels = {
    program: "Delivery plans",
    workflow: "Work flows",
    organization: "Teams and review",
  };
  const objectLabels = {
    program: "delivery plan",
    workflow: "work flow",
    organization: "team and review design",
  };
  const viewLabels = {
    plan: studioState.family === "organization" ? "Team & review" : "Plan",
    simulate: "Try the flow",
    validate: "Check",
    technical: "Technical details",
    authority: "Permission details",
  };
  const objectLabel = objectLabels[studioState.family] || "delivery design";
  app.innerHTML = `${destinationNav("plan", "#/program-studio")}<div class="program-studio" data-family="${esc(studioState.family)}" data-policy="${esc(studioState.name)}">
    ${studioState.setupContext ? `<section class="studio-setup-context"><div><span>Delivery scope from setup</span><strong>${esc(studioState.setupContext.project || "project not chosen")} · phase ${esc(studioState.setupContext.phase || "review needed")}</strong><p>This is an unsaved delivery-plan draft. Editing and checking it start nothing; Save draft still requires its own exact preview and confirmation.</p></div><div><a href="#/program-studio">Back to delivery choices</a><a href="#/">Leave for now</a></div></section>` : ""}
    ${empty ? `<section class="studio-empty-neutral"><div><span class="orch-eyebrow">Optional delivery design</span><h2>Nothing has been saved here yet</h2><p>Ordinary roadmap work is ready. Drafting a ${esc(objectLabel)} is optional and starts no work.</p></div><a href="#/">Return to current work</a></section>` : ""}
    <header class="studio-toolbar"><div><span class="orch-eyebrow">${esc(familyLabels[studioState.family])}</span><h1>${esc(document.title || document.slug || "Delivery plan")}</h1><p>Draft, check, and review before saving. Nothing here starts work or provides permission.</p><details><summary>Technical details</summary><code>pm/${esc(family?.plural || `${studioState.family}s`)}/${esc(document.slug || studioState.name)}.json</code></details></div><div class="studio-policy-actions"><label>Design area<select id="studio-family-select">${STUDIO_FAMILIES.map((id) => `<option value="${id}"${id === studioState.family ? " selected" : ""}>${esc(familyLabels[id])}</option>`).join("")}</select></label><label>Saved ${esc(objectLabel)}<select id="studio-policy-select"><option value="">New unsaved ${esc(objectLabel)}</option>${items.map((item) => `<option value="${esc(item.name)}"${item.name === studioState.name && studioState.exists ? " selected" : ""}>${esc(item.slug || item.name)}${item.valid ? "" : " · needs attention"}</option>`).join("")}</select></label><button type="button" id="studio-new">New</button><button type="button" id="studio-duplicate">Duplicate</button><button type="button" id="studio-preview-save">${studioState.setupContext && studioState.family === "program" ? "Review draft save" : `Review ${esc(objectLabel)} save`}</button><button type="button" id="studio-preview-delete" class="danger"${studioState.exists ? "" : " disabled"}>Review removal</button></div></header>
    <div class="studio-tabs" role="tablist" aria-label="${studioState.family === "organization" ? "Team and review authoring views" : "Delivery-plan authoring views"}">${STUDIO_VIEWS.map((id) => `<button type="button" id="studio-tab-${id}" role="tab" aria-controls="studio-view" aria-selected="${studioState.view === id}" tabindex="${studioState.view === id ? "0" : "-1"}" data-studio-view="${id}" class="${studioState.view === id ? "active" : ""}">${esc(viewLabels[id])}${id === "validate" && validation && !validation.valid ? ` (${validation.diagnostics.length})` : ""}</button>`).join("")}</div>
    ${studioState.error ? `<div class="studio-error" role="alert">${esc(studioState.error)}</div>` : ""}<div id="studio-save-panel"></div><div id="studio-view" role="tabpanel" aria-labelledby="studio-tab-${esc(studioState.view)}">${studioBody()}</div>
  </div>`;
  wireProgramStudio();
  wireTablist(".studio-tabs");
  wireTablist(".studio-technical-tabs");
  wireTablist(".studio-scenario-tabs");
  wireArrowGroup(".studio-plan-sections", "[data-plan-section]");
  finishDynamicRender(focus);
}

function queueStudioModel() {
  clearTimeout(studioState.validationTimer);
  studioState.validationTimer = setTimeout(() => refreshStudioModel(), SNAPSHOT_MODE ? 0 : 220);
}

async function refreshStudioModel() {
  if (!studioState.document) return;
  studioState.error = "";
  const request = { family: studioState.family, action: "save", name: studioState.document.slug || studioState.name, document: studioState.document };
  const { status, body } = await postJson("/api/program-studio/preview", request);
  if (status >= 400 || body.ok === false || !body.data?.studio) {
    studioState.error = (body.issues && body.issues[0]) || `compiler preview failed (${status})`;
  } else {
    studioState.compilePreview = body.data;
    studioState.model = body.data.studio;
    studioState.document = clone(body.data.studio.raw);
  }
  renderProgramStudio();
}

function setStudioField(key, value) {
  const document = studioState.document;
  if (key === "document.slug") { document.slug = value.trim(); if (!studioState.exists) studioState.name = document.slug; }
  else if (key === "document.title") document.title = value;
  else if (key === "document.description") setOptional(document, "description", value.trim());
  else if (key === "document.version") document.version = value.trim();
  else if (key.startsWith("program.")) {
    document.scope ||= {};
    document.scope.phases ||= { from: 1, through: 1 };
    if (key === "program.project") document.scope.project = value.trim();
    if (key === "program.phase_from") document.scope.phases.from = maybeNumber(value);
    if (key === "program.phase_through") document.scope.phases.through = maybeNumber(value);
    if (key === "program.stories") document.scope.stories = splitLines(value).length ? { include: splitLines(value) } : "all";
    if (key === "program.organization") document.organization = value.trim();
    if (key === "program.mode_ceiling") document.mode_ceiling = value;
  } else if (key.startsWith("node.")) {
    const graphNode = studioGraphNode(studioState.selected);
    const node = studioRawNode(graphNode);
    if (!node) return;
    const field = key.slice(5);
    if (field === "id") {
      const old = node.id; const next = value.trim(); node.id = next;
      (document.nodes || []).forEach((candidate) => {
        candidate.needs = (candidate.needs || []).map((need) => need === old ? next : need);
        if (Array.isArray(candidate.producers)) {
          candidate.producers = candidate.producers.map((producer) => producer === old ? next : producer);
        }
        for (const referenceKey of ["facts", "verdicts"]) {
          if (Array.isArray(candidate[referenceKey])) {
            candidate[referenceKey] = candidate[referenceKey].map((reference) => (
              reference === old || reference.startsWith(`${old}.`)
                ? `${next}${reference.slice(old.length)}`
                : reference
            ));
          }
        }
        Object.values(candidate.routes || {}).forEach((route) => { if (route?.kind === "node" && route.target === old) route.target = next; });
        ["on_success", "on_failure", "on_exhausted", "on_consensus", "on_repair", "on_dissent", "on_quorum_lost"].forEach((routeKey) => { if (candidate[routeKey]?.kind === "node" && candidate[routeKey].target === old) candidate[routeKey].target = next; });
      });
      visitStudioObjects(document.nodes || [], (item) => {
        if (
          item.kind === "artifact"
          && typeof item.name === "string"
          && item.name.startsWith(`${old}.`)
        ) item.name = `${next}${item.name.slice(old.length)}`;
      });
      ensureStudioLayout(); if (document.layout.nodes[old]) { document.layout.nodes[next] = document.layout.nodes[old]; delete document.layout.nodes[old]; }
      studioState.selected = next;
    } else if (["max_rounds", "quorum", "expires_seconds", "timeout_seconds", "max_attempts"].includes(field)) node[field] = maybeNumber(value);
    else if (["capability_ceiling", "participants", "needs"].includes(field)) node[field] = splitLines(value);
    else setOptional(node, field, value.trim());
  }
  studioState.jsonDraft = "";
  studioState.jsonPointer = "";
  queueStudioModel();
}

function nextStudioNodeId(type) {
  const base = type.replace("_", "-");
  const used = new Set((studioState.document.nodes || []).map((node) => node.id));
  let index = 1; while (used.has(`${base}-${index}`)) index += 1;
  return `${base}-${index}`;
}

function defaultStudioNode(type) {
  const id = nextStudioNodeId(type);
  const common = { id, type, needs: [], resource_groups: [], inputs: {}, outputs: [] };
  const action = { kind: "action", target: "block" };
  const complete = { kind: "terminal", target: "complete" };
  if (type === "agent") return { ...common, role: "implementer", task: "Perform the exact bounded role task.", workspace: "isolated-worktree", capability_ceiling: ["agent:dispatch", "workspace:write"], timeout_seconds: 900, max_attempts: 1, on_failure: action };
  if (type === "check") return { ...common, runner: { kind: "builtin", name: "file-exists", path: "README.md", output_bytes: 30000 }, expect: { exit_code: 0 }, timeout_seconds: 300, max_attempts: 1, on_failure: action };
  if (type === "collect") return { ...common, producers: [], on_failure: action };
  if (type === "bounded_run") return { ...common, score: "score", expected_terminal: "awaiting-certification", capability_ceiling: ["agent:dispatch", "check:execute", "workspace:write"], budgets: { max_agent_starts: 8, max_check_starts: 16, max_wall_seconds: 3600, max_artifact_bytes: 1000000 }, on_failure: action };
  if (type === "subflow") return { ...common, workflow: "workflow", version: "1.0.0", with: {}, capability_ceiling: ["agent:dispatch"], on_success: complete, on_failure: action };
  if (type === "loop") return { ...common, purpose: "repair", workflow: "workflow", version: "1.0.0", with: {}, capability_ceiling: ["agent:dispatch"], max_rounds: 2, until: { kind: "artifact-valid", source: "child.fact", operator: "green" }, carry: [], on_success: complete, on_exhausted: action };
  if (type === "debate") return { ...common, participants: ["proposer", "critic"], judge_role: "judge", max_rounds: 2, quorum: 2, artifact_max_bytes: 30000, artifact_max_tokens: 4000, round_timeout_seconds: 1800, tie_policy: "judge", dissent_policy: "preserve", on_consensus: complete, on_repair: action, on_dissent: { kind: "action", target: "checkpoint" }, on_quorum_lost: { kind: "action", target: "escalate" }, on_exhausted: { kind: "action", target: "escalate" } };
  if (type === "verdict") return { ...common, role: "verifier", rubric: "quality", subject: { kind: "literal", value: "subject" }, freshness_seconds: 3600, max_rationale_bytes: 30000, results: ["pass", "fail"], routes: { pass: complete, fail: action } };
  if (type === "gate") return { ...common, facts: ["check.fact"], verdicts: [], operator: "all", missing_policy: "block", dissent_policy: "preserve", routes: { pass: complete, fail: action, missing: action, dissent: { kind: "action", target: "checkpoint" } } };
  if (type === "checkpoint") return { ...common, prompt_id: id, prompt: "Review this declared decision port.", expires_seconds: 86400, options: [{ id: "approve", label: "Approve", route: complete }, { id: "block", label: "Block", route: action }] };
  if (type === "rail") return { ...common, action: "evidence-materialize", capability: "evidence:materialize", timeout_seconds: 300, on_failure: action };
  return common;
}

function addStudioNode(type) {
  const node = defaultStudioNode(type);
  studioState.document.nodes ||= [];
  studioState.document.nodes.push(node);
  ensureStudioLayout();
  const index = studioState.document.nodes.length - 1;
  studioState.document.layout.nodes[node.id] = { x: 80 + (index % 4) * 270, y: 90 + Math.floor(index / 4) * 160 };
  studioState.selected = node.id; studioState.jsonDraft = "";
  refreshStudioModel();
}

function removeStudioNode() {
  const graphNode = studioGraphNode(studioState.selected);
  const node = studioRawNode(graphNode); if (!node) return;
  studioState.document.nodes = studioState.document.nodes.filter((item) => item !== node);
  studioState.document.nodes.forEach((candidate) => { candidate.needs = (candidate.needs || []).filter((need) => need !== node.id); });
  ensureStudioLayout(); delete studioState.document.layout.nodes[node.id];
  studioState.selected = ""; studioState.jsonDraft = ""; refreshStudioModel();
}

function duplicateStudioNode() {
  const node = studioRawNode(studioGraphNode(studioState.selected)); if (!node) return;
  const copy = clone(node); copy.id = nextStudioNodeId(node.type);
  studioState.document.nodes.push(copy); ensureStudioLayout();
  const old = studioState.document.layout.nodes[node.id] || { x: 80, y: 80 };
  studioState.document.layout.nodes[copy.id] = { x: Number(old.x) + 35, y: Number(old.y) + 125 };
  studioState.selected = copy.id; studioState.jsonDraft = ""; refreshStudioModel();
}

function moveStudioNode(id, x, y) {
  const graphNode = studioGraphNode(id); if (!graphNode) return;
  ensureStudioLayout();
  const position = { x: Math.max(10, Math.round(x)), y: Math.max(10, Math.round(y)) };
  studioState.document.layout.nodes[graphNode.layout_key || id] = position;
  graphNode.position = position;
  studioState.jsonDraft = "";
}

function wireStudioCanvas() {
  const svg = document.getElementById("studio-canvas"); if (!svg) return;
  let drag = null;
  const point = (event) => { const p = svg.createSVGPoint(); p.x = event.clientX; p.y = event.clientY; return p.matrixTransform(svg.getScreenCTM().inverse()); };
  document.querySelectorAll("[data-studio-node]").forEach((group) => {
    group.addEventListener("click", () => { studioState.selected = group.dataset.studioNode; renderProgramStudio(); });
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); studioState.selected = group.dataset.studioNode; renderProgramStudio(); return; }
      if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
      event.preventDefault(); const node = studioGraphNode(group.dataset.studioNode); const step = event.shiftKey ? 20 : 5;
      const dx = event.key === "ArrowLeft" ? -step : event.key === "ArrowRight" ? step : 0;
      const dy = event.key === "ArrowUp" ? -step : event.key === "ArrowDown" ? step : 0;
      moveStudioNode(node.id, Number(node.position.x) + dx, Number(node.position.y) + dy); renderProgramStudio(); queueStudioModel();
    });
    group.addEventListener("pointerdown", (event) => { if (event.button !== 0) return; const node = studioGraphNode(group.dataset.studioNode); const p = point(event); drag = { group, node, dx: p.x - node.position.x, dy: p.y - node.position.y }; group.setPointerCapture(event.pointerId); });
    group.addEventListener("pointermove", (event) => { if (!drag || drag.group !== group) return; const p = point(event); moveStudioNode(drag.node.id, p.x - drag.dx, p.y - drag.dy); group.setAttribute("transform", `translate(${drag.node.position.x},${drag.node.position.y})`); });
    group.addEventListener("pointerup", () => { if (!drag) return; drag = null; queueStudioModel(); });
  });
}

function renderStudioSavePreview(preview, request) {
  const slot = document.getElementById("studio-save-panel"); if (!slot) return;
  const objectLabel = request.family === "program" ? "delivery plan" : request.family === "workflow" ? "work flow" : "team and review design";
  const applyLabel = request.action === "delete"
    ? `Remove this ${objectLabel}`
    : `Save this ${objectLabel}`;
  const actionSummary = request.action === "delete"
    ? `This would remove one saved ${objectLabel}.`
    : `This would write one reviewed ${objectLabel} file.`;
  slot.innerHTML = `<section class="studio-save-preview ${preview.applicable ? "" : "refused"}" role="dialog" aria-modal="false" aria-labelledby="studio-save-preview-title" tabindex="-1"><div class="studio-preview-head"><div><span>Review before ${request.action === "delete" ? "removal" : "save"}</span><strong id="studio-save-preview-title">${esc(actionSummary)}</strong></div>${badge(preview.applicable ? "ready for confirmation" : "needs attention", preview.applicable ? "ok" : "issue")}</div>
    <p>Reviewing this change writes nothing. Confirming it changes only the named file; it starts no work, changes no roadmap status, and provides no permission.</p>
    ${preview.no_op ? '<p class="hint">The saved file already matches this draft.</p>' : ""}
    <details class="studio-save-technical"><summary>Technical details</summary><code>${esc(preview.path)}</code><code>${esc(preview.fingerprint)}</code>${preview.diff ? `<pre class="diff">${diffHtml(preview.diff)}</pre>` : '<p class="hint">No byte change.</p>'}</details>
    <div class="studio-preview-actions">${preview.applicable ? `<button type="button" id="studio-confirm-apply">${esc(applyLabel)}</button>` : ""}<button type="button" id="studio-close-preview">Close review</button></div></section>`;
  const close = () => {
    slot.innerHTML = "";
    restoreReturnFocus("studio-save", "#studio-preview-save");
  };
  document.getElementById("studio-close-preview")?.addEventListener("click", close);
  document.getElementById("studio-confirm-apply")?.addEventListener("click", () => applyStudioAction(preview, request));
  enhanceSemantics(slot);
  wireDismissibleRegion(".studio-save-preview", close, "studio-save", "#studio-preview-save");
  focusRegion(".studio-save-preview");
}

async function previewStudioAction(action, trigger = document.activeElement) {
  rememberReturnFocus("studio-save", trigger);
  const request = { family: studioState.family, action, name: studioState.document.slug || studioState.name, ...(action === "save" ? { document: studioState.document } : {}) };
  const { status, body } = await postJson("/api/program-studio/preview", request);
  if (status >= 400 || body.ok === false) { studioState.error = (body.issues && body.issues[0]) || `preview failed (${status})`; renderProgramStudio(); return; }
  if (body.data.studio) { studioState.model = body.data.studio; studioState.compilePreview = body.data; }
  renderProgramStudio(); renderStudioSavePreview(body.data, request);
}

async function applyStudioAction(preview, request) {
  const button = document.getElementById("studio-confirm-apply"); if (button) { button.disabled = true; button.textContent = "applying exact policy…"; }
  const { status, body } = await postJson("/api/program-studio/apply", { ...request, fingerprint: preview.fingerprint });
  if (status === 409) { studioState.error = "Stale Program Studio preview refused; policy bytes or desired content changed. Nothing was written."; renderProgramStudio(); return; }
  if (status >= 400 || body.ok === false) { studioState.error = (body.issues && body.issues[0]) || `apply failed (${status})`; renderProgramStudio(); return; }
  const family = studioState.family;
  if (request.action === "delete") { location.hash = `#/program-studio/${family}`; await viewProgramStudio(family); return; }
  studioState.exists = true; studioState.name = request.name;
  location.hash = `#/program-studio/${family}/${encodeURIComponent(request.name)}`;
  await viewProgramStudio(family, request.name);
}

function studioPlanChanged() {
  studioState.jsonDraft = "";
  studioState.jsonPointer = "";
  queueStudioModel();
}

function visitStudioObjects(value, visitor) {
  if (Array.isArray(value)) {
    value.forEach((item) => visitStudioObjects(item, visitor));
    return;
  }
  if (!value || typeof value !== "object") return;
  visitor(value);
  Object.values(value).forEach((item) => visitStudioObjects(item, visitor));
}

function updateProgramBinding(index, field, value) {
  const binding = studioState.document?.bindings?.[index];
  if (!binding) return;
  binding.match ||= {};
  if (field === "priority") binding.priority = maybeNumber(value);
  else if (field === "phase_from") binding.match.phase_from = maybeNumber(value);
  else if (field === "phase_through") binding.match.phase_through = maybeNumber(value);
  else if (field === "rubrics") binding.rubrics = splitLines(value);
  else if (field === "id") {
    const old = binding.id;
    const next = String(value).trim();
    binding.id = next;
    (studioState.document.nudges || []).forEach((nudge) => {
      if (nudge.binding === old) nudge.binding = next;
    });
  } else binding[field] = String(value).trim();
  studioPlanChanged();
}

function addProgramBinding() {
  const document = studioState.document;
  document.bindings ||= [];
  const used = new Set(document.bindings.map((item) => item.id));
  let index = document.bindings.length + 1;
  while (used.has(`work-route-${index}`)) index += 1;
  const phases = document.scope?.phases || { from: 1, through: 1 };
  const workflow = studioFamilyModel("workflow")?.items?.[0]?.name || "choose-work-flow";
  document.bindings.push({
    id: `work-route-${index}`,
    priority: index * 10,
    match: { phase_from: phases.from ?? 1, phase_through: phases.through ?? phases.from ?? 1 },
    workflow,
    with: {},
    team: "choose-team",
    rubrics: ["choose-review-criteria"],
  });
  studioPlanChanged();
}

function removeProgramBinding(index) {
  studioState.document.bindings?.splice(index, 1);
  studioPlanChanged();
}

function updateProgramGate(index, field, value) {
  const gate = studioState.document?.phase_gates?.[index];
  if (!gate) return;
  gate[field] = String(value).trim();
  studioPlanChanged();
}

function addProgramGate() {
  const document = studioState.document;
  document.phase_gates ||= [];
  const used = new Set(document.phase_gates.map((item) => item.id));
  let index = document.phase_gates.length + 1;
  while (used.has(`phase-review-${index}`)) index += 1;
  document.phase_gates.push({
    id: `phase-review-${index}`,
    when: "before-phase-complete",
    role: "choose-review-owner",
    rubric: "choose-review-criteria",
    on_fail: "block",
  });
  studioPlanChanged();
}

function removeProgramGate(index) {
  studioState.document.phase_gates?.splice(index, 1);
  studioPlanChanged();
}

function updateWorkflowInput(index, field, value, checked = false) {
  const document = studioState.document;
  const parameter = document?.parameters?.[index];
  if (!parameter) return;
  document.defaults ||= {};
  if (field === "required") parameter.required = checked;
  else if (field === "default") {
    if (value === "") delete document.defaults[parameter.id];
    else if (parameter.type === "integer") document.defaults[parameter.id] = maybeNumber(value);
    else if (parameter.type === "boolean") document.defaults[parameter.id] = ["true", "1", "yes"].includes(String(value).toLowerCase());
    else if (parameter.type === "string-list") document.defaults[parameter.id] = splitLines(value);
    else document.defaults[parameter.id] = value;
  } else if (field === "id") {
    const old = parameter.id;
    const next = String(value).trim();
    parameter.id = next;
    if (Object.prototype.hasOwnProperty.call(document.defaults, old)) {
      document.defaults[next] = document.defaults[old];
      delete document.defaults[old];
    }
    visitStudioObjects(document.nodes || [], (item) => {
      if (item.kind === "parameter" && item.name === old) item.name = next;
    });
  } else if (field === "type") {
    parameter.type = value;
  }
  studioPlanChanged();
}

function addWorkflowInput() {
  const document = studioState.document;
  document.parameters ||= [];
  const used = new Set(document.parameters.map((item) => item.id));
  let index = document.parameters.length + 1;
  while (used.has(`work-input-${index}`)) index += 1;
  document.parameters.push({
    id: `work-input-${index}`,
    type: "string",
    required: false,
    max_bytes: 1000,
  });
  studioPlanChanged();
}

function removeWorkflowInput(index) {
  const document = studioState.document;
  const parameter = document.parameters?.[index];
  if (parameter && document.defaults) delete document.defaults[parameter.id];
  document.parameters?.splice(index, 1);
  studioPlanChanged();
}

function studioTeamRoleAt(teamIndex, roleIndex) {
  return studioState.document?.teams?.[teamIndex]?.roles?.[roleIndex] || null;
}

function renameStudioTeamRole(teamIndex, roleIndex, nextValue) {
  const document = studioState.document;
  const role = studioTeamRoleAt(teamIndex, roleIndex);
  if (!document || !role) return;
  const old = role.id;
  const next = String(nextValue).trim();
  const collision = studioOrganizationRoles().some((item) => (
    (item.teamIndex !== teamIndex || item.roleIndex !== roleIndex)
    && item.role.id === next
  ));
  role.id = next;
  if (!next || next === old || collision) return;
  (document.teams || []).forEach((team) => (team.roles || []).forEach((item) => {
    ["may_request", "may_judge", "independent_from"].forEach((field) => {
      item[field] = (item[field] || []).map((value) => value === old ? next : value);
    });
  }));
  (document.councils || []).forEach((council) => {
    council.members = (council.members || []).map((value) => value === old ? next : value);
    if (council.judge === old) council.judge = next;
    if (council.meta_verifier === old) council.meta_verifier = next;
    if (council.decision) {
      council.decision.veto_roles = (council.decision.veto_roles || []).map((value) => value === old ? next : value);
      if (council.decision.weights && Object.prototype.hasOwnProperty.call(council.decision.weights, old)) {
        council.decision.weights[next] = council.decision.weights[old];
        delete council.decision.weights[old];
      }
    }
  });
  ensureStudioLayout();
  const teamId = document.teams?.[teamIndex]?.id;
  const oldKey = `${teamId}/${old}`;
  const nextKey = `${teamId}/${next}`;
  if (document.layout.nodes[oldKey]) {
    document.layout.nodes[nextKey] = document.layout.nodes[oldKey];
    delete document.layout.nodes[oldKey];
  }
}

function updateStudioTeamRole(teamIndex, roleIndex, field, value, checked = false) {
  const role = studioTeamRoleAt(teamIndex, roleIndex);
  if (!role) return;
  if (field === "id") renameStudioTeamRole(teamIndex, roleIndex, value);
  else if (field === "required") role.required = checked;
  else if (field === "cardinality") role.cardinality = maybeNumber(value);
  else if (field === "replacement.max_replacements") {
    role.replacement ||= {};
    role.replacement.max_replacements = maybeNumber(value);
    if (Number(role.replacement.max_replacements) > 0 && !(role.replacement.reasons || []).length) {
      role.replacement.reasons = ["unavailable", "lost", "failed", "refused", "conflicted"];
    }
  } else if (field.startsWith("replacement.")) {
    role.replacement ||= {};
    const key = field.slice("replacement.".length);
    if (key === "fallback_pools") role.replacement[key] = splitLines(value);
    else if (key === "preserve_history") role.replacement[key] = checked;
    else role.replacement[key] = String(value).trim();
  } else role[field] = String(value).trim();
  studioPlanChanged();
}

function updateStudioTeamRoleLink(teamIndex, roleIndex, field, target, checked) {
  const role = studioTeamRoleAt(teamIndex, roleIndex);
  if (!role) return;
  const current = new Set(role[field] || []);
  if (checked) current.add(target);
  else current.delete(target);
  const order = (studioState.document?.teams?.[teamIndex]?.roles || []).map((item) => item.id);
  role[field] = order.filter((id) => current.has(id));
  studioPlanChanged();
}

function studioCouncilVotingSlots(council) {
  const roleMap = new Map(studioOrganizationRoles().map(({ role }) => [role.id, role]));
  return (council.members || [])
    .filter((id) => id !== council.judge)
    .reduce((total, id) => total + Number(roleMap.get(id)?.cardinality || 0), 0);
}

function renameStudioCouncil(index, nextValue) {
  const document = studioState.document;
  const council = document?.councils?.[index];
  if (!document || !council) return;
  const old = council.id;
  const next = String(nextValue).trim();
  const collision = (document.councils || []).some((item, itemIndex) => (
    itemIndex !== index && item.id === next
  ));
  council.id = next;
  if (!next || next === old || collision) return;
  ensureStudioLayout();
  const oldKey = `council:${old}`;
  const nextKey = `council:${next}`;
  if (document.layout.nodes[oldKey]) {
    document.layout.nodes[nextKey] = document.layout.nodes[oldKey];
    delete document.layout.nodes[oldKey];
  }
}

function updateStudioCouncil(index, field, value, checked = false) {
  const council = studioState.document?.councils?.[index];
  if (!council) return;
  council.decision ||= {};
  council.audit ||= {};
  if (field === "quorum" || field === "audit.sample_size") {
    const [parent, child] = field.split(".");
    if (child) council[parent][child] = maybeNumber(value);
    else council[field] = maybeNumber(value);
  } else if (field === "distinct_principals") {
    council.distinct_principals = checked;
  } else if (field === "meta_verifier") {
    council.meta_verifier = String(value).trim() || null;
  } else if (field === "decision.veto_roles") {
    council.decision.veto_roles = splitLines(value);
  } else if (field === "decision.method") {
    council.decision.method = value;
    const votingSlots = Math.max(studioCouncilVotingSlots(council), 1);
    const totalWeight = (council.members || [])
      .filter((id) => id !== council.judge)
      .reduce((total, id) => {
        const role = studioOrganizationRoles().find((item) => item.role.id === id)?.role;
        return total + Number(role?.cardinality || 0) * Number(council.decision.weights?.[id] || 1);
      }, 0);
    council.decision.threshold = value === "unanimous"
      ? votingSlots
      : value === "weighted"
        ? Math.floor(totalWeight / 2) + 1
        : value === "majority"
          ? Math.floor(votingSlots / 2) + 1
          : 1;
  } else if (field === "audit.mode") {
    council.audit.mode = value;
    const memberSlots = (council.members || []).reduce((total, id) => {
      const role = studioOrganizationRoles().find((item) => item.role.id === id)?.role;
      return total + Number(role?.cardinality || 0);
    }, 0);
    council.audit.sample_size = value === "none" ? 0 : value === "full" ? memberSlots : 1;
  } else if (field === "id") {
    renameStudioCouncil(index, value);
  } else if (field.includes(".")) {
    const [parent, child] = field.split(".");
    council[parent][child] = String(value).trim();
  } else {
    council[field] = String(value).trim();
  }
  studioPlanChanged();
}

function updateStudioCouncilMember(index) {
  const council = studioState.document?.councils?.[index];
  if (!council) return;
  const selected = new Set(
    [...document.querySelectorAll(`[data-team-council-member="${index}"]:checked`)]
      .map((field) => field.dataset.teamRoleTarget)
  );
  council.members = studioOrganizationRoles()
    .map(({ role }) => role.id)
    .filter((id) => selected.has(id));
  if (council.decision?.weights) {
    Object.keys(council.decision.weights).forEach((id) => {
      if (!selected.has(id)) delete council.decision.weights[id];
    });
  }
  if (council.decision?.veto_roles) {
    council.decision.veto_roles = council.decision.veto_roles.filter((id) => selected.has(id));
  }
  studioPlanChanged();
}

function wireProgramStudio() {
  document.querySelectorAll("[data-studio-view]").forEach((button) => button.addEventListener("click", () => { studioState.view = button.dataset.studioView; renderProgramStudio(); }));
  document.querySelectorAll("[data-studio-technical]").forEach((button) => button.addEventListener("click", () => { studioState.technicalMode = button.dataset.studioTechnical; renderProgramStudio(); }));
  document.querySelectorAll("[data-plan-section]").forEach((button) => button.addEventListener("click", () => {
    studioState.planSection = button.dataset.planSection;
    studioState.selected = "";
    renderProgramStudio();
    requestAnimationFrame(() => document.getElementById("studio-plan-section")?.focus());
  }));
  document.getElementById("studio-review-save")?.addEventListener("click", () => previewStudioAction("save"));
  document.getElementById("studio-family-select")?.addEventListener("change", (event) => { location.hash = `#/program-studio/${event.target.value}`; });
  document.getElementById("studio-policy-select")?.addEventListener("change", (event) => { location.hash = event.target.value ? `#/program-studio/${studioState.family}/${encodeURIComponent(event.target.value)}` : `#/program-studio/${studioState.family}`; });
  document.getElementById("studio-new")?.addEventListener("click", () => {
    const family = studioFamilyModel(); const used = new Set((family.items || []).map((item) => item.name)); let slug = `new-${studioState.family}`; let index = 2; while (used.has(slug)) slug = `new-${studioState.family}-${index++}`;
    studioState.document = clone(family.draft); studioState.document.slug = slug; studioState.name = slug; studioState.exists = false; studioState.selected = ""; studioState.model = null; studioState.error = ""; refreshStudioModel();
  });
  document.getElementById("studio-duplicate")?.addEventListener("click", () => {
    const used = new Set((studioFamilyModel().items || []).map((item) => item.name)); let slug = `${studioState.document.slug}-copy`; let index = 2; while (used.has(slug)) slug = `${studioState.document.slug}-copy-${index++}`;
    studioState.document = clone(studioState.document); studioState.document.slug = slug; studioState.document.title = `${studioState.document.title} copy`; studioState.name = slug; studioState.exists = false; studioState.selected = ""; refreshStudioModel();
  });
  document.getElementById("studio-preview-save")?.addEventListener("click", () => previewStudioAction("save"));
  document.getElementById("studio-preview-delete")?.addEventListener("click", () => previewStudioAction("delete"));
  document.querySelectorAll("[data-studio-settings]").forEach((button) => button.addEventListener("click", () => { studioState.selected = ""; renderProgramStudio(); }));
  document.querySelectorAll("[data-studio-select]").forEach((button) => button.addEventListener("click", () => { studioState.selected = button.dataset.studioSelect; renderProgramStudio(); }));
  document.querySelectorAll("[data-studio-add]").forEach((button) => button.addEventListener("click", () => addStudioNode(button.dataset.studioAdd)));
  document.querySelectorAll("[data-studio-field]").forEach((field) => field.addEventListener("change", () => setStudioField(field.dataset.studioField, field.value)));
  document.querySelectorAll("[data-plan-binding-field]").forEach((field) => field.addEventListener("change", () => updateProgramBinding(Number(field.dataset.planBinding), field.dataset.planBindingField, field.value)));
  document.querySelector("[data-plan-add-binding]")?.addEventListener("click", addProgramBinding);
  document.querySelectorAll("[data-plan-remove-binding]").forEach((button) => button.addEventListener("click", () => removeProgramBinding(Number(button.dataset.planRemoveBinding))));
  document.querySelectorAll("[data-plan-gate-field]").forEach((field) => field.addEventListener("change", () => updateProgramGate(Number(field.dataset.planGate), field.dataset.planGateField, field.value)));
  document.querySelector("[data-plan-add-gate]")?.addEventListener("click", addProgramGate);
  document.querySelectorAll("[data-plan-remove-gate]").forEach((button) => button.addEventListener("click", () => removeProgramGate(Number(button.dataset.planRemoveGate))));
  document.querySelectorAll("[data-plan-input-field]").forEach((field) => field.addEventListener("change", () => updateWorkflowInput(Number(field.dataset.planInput), field.dataset.planInputField, field.value, field.checked)));
  document.querySelector("[data-plan-add-input]")?.addEventListener("click", addWorkflowInput);
  document.querySelectorAll("[data-plan-remove-input]").forEach((button) => button.addEventListener("click", () => removeWorkflowInput(Number(button.dataset.planRemoveInput))));
  document.querySelectorAll("[data-team-role-field]").forEach((field) => field.addEventListener("change", () => updateStudioTeamRole(Number(field.dataset.teamTeam), Number(field.dataset.teamRole), field.dataset.teamRoleField, field.value, field.checked)));
  document.querySelectorAll("[data-team-role-link]").forEach((field) => field.addEventListener("change", () => updateStudioTeamRoleLink(Number(field.dataset.teamTeam), Number(field.dataset.teamRoleLink), field.dataset.teamRoleLinkField, field.dataset.teamRoleTarget, field.checked)));
  document.querySelectorAll("[data-team-council-field]").forEach((field) => field.addEventListener("change", () => updateStudioCouncil(Number(field.dataset.teamCouncil), field.dataset.teamCouncilField, field.value, field.checked)));
  document.querySelectorAll("[data-team-council-member]").forEach((field) => field.addEventListener("change", () => updateStudioCouncilMember(Number(field.dataset.teamCouncilMember))));
  document.querySelectorAll("[data-plan-edit-step]").forEach((button) => button.addEventListener("click", () => {
    studioState.selected = button.dataset.planEditStep;
    studioState.planSection = "flow";
    renderProgramStudio();
    requestAnimationFrame(() => document.querySelector(".studio-plan-step-editor input")?.focus());
  }));
  document.querySelectorAll("[data-plan-correction]").forEach((button) => button.addEventListener("click", () => {
    studioState.planSection = button.dataset.planCorrection;
    studioState.selected = button.dataset.planNode || "";
    studioState.view = "plan";
    renderProgramStudio();
    requestAnimationFrame(() => {
      const target = button.dataset.planField ? document.getElementById(button.dataset.planField) : null;
      (target || document.getElementById("studio-plan-section"))?.focus();
    });
  }));
  document.querySelectorAll("[data-studio-capability]").forEach((field) => field.addEventListener("change", () => { const values = [...document.querySelectorAll("[data-studio-capability]:checked")].map((item) => item.dataset.studioCapability); studioState.document.requested_capabilities = values.sort(); studioState.jsonDraft = ""; queueStudioModel(); }));
  document.querySelectorAll("[data-studio-stop]").forEach((field) => field.addEventListener("change", () => { studioState.document.stop_conditions = [...document.querySelectorAll("[data-studio-stop]:checked")].map((item) => item.dataset.studioStop); studioState.jsonDraft = ""; queueStudioModel(); }));
  document.querySelectorAll("[data-studio-budget]").forEach((field) => field.addEventListener("change", () => { studioState.document.budgets[field.dataset.studioBudget] = maybeNumber(field.value); studioState.jsonDraft = ""; queueStudioModel(); }));
  document.getElementById("studio-delete-node")?.addEventListener("click", removeStudioNode);
  document.getElementById("studio-duplicate-node")?.addEventListener("click", duplicateStudioNode);
  document.querySelectorAll("[data-studio-diagnostic]").forEach((button) => button.addEventListener("click", () => {
    const diagnostic = (studioState.model.validation.diagnostics || []).find((item) => item.pointer === button.dataset.studioDiagnostic);
    const id = button.dataset.nodeId || diagnostic?.target?.node_id;
    const fieldId = button.dataset.fieldId || diagnostic?.target?.field_id;
    studioState.jsonPointer = button.dataset.studioDiagnostic;
    if (id) { studioState.selected = id; studioState.view = "technical"; studioState.technicalMode = "graph"; }
    else { studioState.view = "technical"; studioState.technicalMode = "config"; }
    renderProgramStudio();
    requestAnimationFrame(() => {
      const direct = fieldId ? document.getElementById(fieldId) : null;
      if (direct) { direct.focus(); direct.scrollIntoView({ block: "center" }); return; }
      if (studioState.view !== "technical" || studioState.technicalMode !== "config") { studioState.view = "technical"; studioState.technicalMode = "config"; renderProgramStudio(); }
      const text = document.getElementById("studio-json-text");
      if (!text) return;
      const field = String(studioState.jsonPointer).split("/").filter(Boolean).pop();
      const offset = text.value.indexOf(`"${field}"`);
      if (offset >= 0) text.setSelectionRange(offset, offset + field.length + 2);
      text.focus(); text.scrollIntoView({ block: "center" });
    });
  }));
  document.querySelectorAll("[data-studio-scenario]").forEach((button) => button.addEventListener("click", () => { studioState.scenario = button.dataset.studioScenario; renderProgramStudio(); }));
  wireStudioCanvas();
  const jsonText = document.getElementById("studio-json-text");
  jsonText?.addEventListener("input", () => { studioState.jsonDraft = jsonText.value; });
  document.getElementById("studio-json-apply")?.addEventListener("click", () => {
    const error = document.getElementById("studio-json-error");
    try { const parsed = JSON.parse(jsonText.value); studioState.document = parsed; studioState.name = parsed.slug || studioState.name; studioState.selected = ""; studioState.jsonDraft = ""; studioState.jsonPointer = ""; studioState.view = "technical"; studioState.technicalMode = "graph"; refreshStudioModel(); }
    catch (err) { error.hidden = false; error.textContent = `JSON refused: ${err.message}`; }
  });
  document.getElementById("studio-json-import")?.addEventListener("change", async (event) => { const file = event.target.files[0]; if (!file) return; jsonText.value = await file.text(); studioState.jsonDraft = jsonText.value; });
}

function bundleBadges(items, tone = "") {
  return (items || []).map((item) => badge(String(item), tone)).join(" ") || '<span class="hint">None declared.</span>';
}

function renderStudioBundle(model) {
  if (!model.valid && model.refusal) {
    app.innerHTML = `<div class="program-studio studio-bundle-review"><header class="bundle-hero refused"><div><span class="orch-eyebrow">Generated program review</span><h1>Bundle review refused</h1><p>${esc(model.refusal)}</p></div>${badge("needs attention", "issue")}</header><p class="studio-no-grant">This review is read-only. It accepted no lease or grant credential, wrote nothing, and started nothing.</p></div>`;
    return;
  }
  const scope = model.roadmap_scope || {};
  const workflow = model.workflow || {};
  const team = model.team || {};
  const diagnostics = model.diagnostics || [];
  const simulation = model.simulation || {};
  const driverProfiles = model.driver_resolution?.profiles || [];
  const criteria = (model.rubrics || []).flatMap((rubric) => (rubric.criteria || []).map((criterion) => ({ ...criterion, rubric: rubric.title })));
  app.innerHTML = `<div class="program-studio studio-bundle-review" data-bundle-valid="${model.valid ? "true" : "false"}">
    <header class="bundle-hero ${model.valid ? "ready" : "refused"}"><div><span class="orch-eyebrow">Program Studio · generated bundle</span><h1>${esc(model.title)}</h1><p>${esc(model.summary)}</p></div>${badge(model.valid ? "ready for setup review" : `${diagnostics.length} linked issue${diagnostics.length === 1 ? "" : "s"}`, model.valid ? "ok" : "issue")}</header>
    <section class="bundle-configuration" aria-labelledby="bundle-configuration-title"><div><span class="orch-eyebrow">Separate from authority</span><h2 id="bundle-configuration-title">${esc(model.configuration?.label)}</h2><p>These are two kinds of configuration. Neither saves itself, creates permission, or starts delivery.</p></div><div class="bundle-config-cards"><article class="tracked"><span>${esc(model.configuration?.tracked?.label)}</span><strong>Roadmap and program policy</strong><code>${esc(model.configuration?.tracked?.source)}</code><small>non-authorizing</small></article><article class="git-local"><span>${esc(model.configuration?.git_local?.label)}</span><strong>Local non-secret driver resolution</strong><code>${esc(model.configuration?.git_local?.source)}</code><small>non-authorizing</small></article></div></section>
    ${diagnostics.length ? `<section class="bundle-diagnostics" aria-labelledby="bundle-diagnostics-title"><header><div><span class="orch-eyebrow">Whole-bundle check</span><h2 id="bundle-diagnostics-title">Source decisions that need attention</h2><p>The shared program validator checked the embedded roadmap, policy documents, budgets, and local roster together.</p></div>${badge(`${diagnostics.length} issue${diagnostics.length === 1 ? "" : "s"}`, "issue")}</header><ol>${diagnostics.map((item) => `<li><a href="${esc(item.anchor_href)}" data-bundle-anchor="${esc(item.anchor_id)}"><span>${esc(item.code)}</span><strong>${esc(item.message)}</strong><code>${esc(item.source)}${esc(item.pointer)}</code><small>${esc(item.remediation)}</small></a></li>`).join("")}</ol></section>` : `<section class="bundle-diagnostics clear"><div><span class="orch-eyebrow">Whole-bundle check</span><h2>Every linked decision agrees</h2><p>The shared program validator found no roadmap, workflow, rubric, budget, team, diversity, or local-driver contradiction.</p></div>${badge("ready", "ok")}</section>`}
    <div class="bundle-overview-grid">
      <section id="${esc(model.sections.scope)}" class="bundle-section"><span class="orch-eyebrow">What will run</span><h2>${esc(scope.project_title)}</h2><p>The generated program selects the roadmap frontier only inside this reviewed scope.</p><dl><div><dt>Project</dt><dd>${esc(scope.project)}</dd></div><div><dt>Phases</dt><dd>${bundleBadges(scope.phase_numbers)}</dd></div><div><dt>Stories</dt><dd>${bundleBadges(scope.story_ids)}</dd></div></dl></section>
      <section id="${esc(model.sections.workflow)}" class="bundle-section wide"><span class="orch-eyebrow">How work moves</span><h2>${esc(workflow.title)}</h2><p>${esc(workflow.summary)}</p><ol class="bundle-route">${(workflow.nodes || []).map((node) => `<li><span>${esc(node.type)}</span><strong>${esc(node.id)}</strong>${node.role ? `<small>${esc(node.role)}</small>` : ""}</li>`).join("")}${(workflow.terminals || []).map((terminal) => `<li class="terminal"><span>stop</span><strong>${esc(terminal.id)}</strong><small>${esc(terminal.description)}</small></li>`).join("")}</ol></section>
      <section id="${esc(model.sections.team)}" class="bundle-section wide"><span class="orch-eyebrow">Who implements and verifies</span><h2>${esc(team.title)}</h2><p>${esc(team.independence_explanation)}</p><div class="bundle-seat-grid">${(team.seats || []).map((seat) => `<article><span>${esc(seat.duty)}</span><strong>${esc(seat.profile)}</strong><p>${esc(seat.workspace)} · ${esc(seat.local?.provider_family)}</p>${seat.independent_from?.length ? `<small>independent from ${esc(seat.independent_from.join(", "))}</small>` : '<small>isolated implementation seat</small>'}${badge(seat.local?.available ? "available locally" : "missing locally", seat.local?.available ? "ok" : "issue")}</article>`).join("")}</div><p class="bundle-rules">${(team.independence_rules || []).map((rule) => `${esc(rule.kind)}: ${esc(rule.roles.join(" ↔ "))}`).join(" · ")}</p></section>
      <section id="${esc(model.sections.checks)}" class="bundle-section wide"><span class="orch-eyebrow">What the checks prove</span><h2>Rubric criteria are bound to producers</h2><div class="bundle-checks">${criteria.map((criterion) => `<article class="${criterion.producer_exists === false ? "missing" : ""}"><span>${esc(criterion.rubric)}</span><strong>${esc(criterion.question)}</strong><p>${criterion.producing_check ? `Produced by <code>${esc(criterion.producing_check)}</code>` : "Independent diff-cited judgment"}</p>${criterion.producing_check ? badge(criterion.producer_exists ? "producer found" : "producer missing", criterion.producer_exists ? "ok" : "issue") : badge("verifier judgment")}</article>`).join("")}</div></section>
      <section id="${esc(model.sections.capabilities)}" class="bundle-section"><span class="orch-eyebrow">What it may request later</span><h2>Bounded capabilities</h2><p>Policy requests are not permission. A separate grant may authorize only a reviewed subset.</p><div>${bundleBadges(model.requested_capabilities, "warn")}</div></section>
      <section id="${esc(model.sections.budgets)}" class="bundle-section"><span class="orch-eyebrow">What it can spend</span><h2>Finite budgets</h2><dl class="bundle-budgets">${Object.entries(model.budgets || {}).map(([name, value]) => `<div><dt>${esc(name.replace(/^max_/, "").replaceAll("_", " "))}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl></section>
      <section id="${esc(model.sections.stops)}" class="bundle-section"><span class="orch-eyebrow">When it stops</span><h2>Declared stop conditions</h2><div>${bundleBadges(model.stop_conditions)}</div><p>No stop grants authority to continue by itself.</p></section>
      <section id="${esc(model.sections.drivers)}" class="bundle-section"><span class="orch-eyebrow">Local driver resolution</span><h2>${esc(model.driver_resolution?.status || "not checked")}</h2><div class="bundle-drivers">${driverProfiles.map((profile) => `<article><strong>${esc(profile.profile)}</strong><span>${esc(profile.provider_family)} · ${esc(profile.adapter?.kind || "adapter unresolved")}</span><small>${esc(profile.model?.alias || "model unresolved")}</small>${badge(profile.available ? "available" : "unavailable", profile.available ? "ok" : "issue")}</article>`).join("") || '<p class="hint">No local profiles resolved.</p>'}</div><p>Local bindings disclose availability and non-secret metadata only.</p></section>
    </div>
    <section class="bundle-simulation"><header><div><span class="orch-eyebrow">Pure simulation</span><h2>One bounded route, before any work starts</h2><p>This is the same scaffold simulation core used by the terminal surface. It writes no state.</p></div>${badge(simulation.bounded ? "bounded" : "unavailable", simulation.bounded ? "ok" : "issue")}</header><ol class="bundle-route">${(simulation.green_route || []).map((step) => `<li><strong>${esc(step)}</strong></li>`).join("")}</ol><details><summary>Failure and repair routes</summary><p><strong>Repair:</strong> ${esc((simulation.repair_route || []).join(" → "))}</p><ul>${(simulation.failure_routes || []).map((route) => `<li><code>${esc(route.type)}</code> stops at <strong>${esc(route.target)}</strong></li>`).join("")}</ul></details></section>
    <section id="${esc(model.sections.handoff)}" class="bundle-handoff"><div><span class="orch-eyebrow">After dw setup apply</span><h2>${esc(model.handoff?.label)}</h2><p>Return to the terminal for a fresh, separate grant preview. The browser mints nothing and runs nothing.</p></div><code>${esc(model.handoff?.command)}</code><small>configuration, not permission · creates grant: false</small></section>
  </div>`;
  document.querySelectorAll("[data-bundle-anchor]").forEach((link) => link.addEventListener("click", () => {
    requestAnimationFrame(() => document.getElementById(link.dataset.bundleAnchor)?.scrollIntoView({ block: "start" }));
  }));
}

async function viewStudioBundle(anchor = "") {
  const proposalFile = new URLSearchParams(location.search).get("proposal_file") || "";
  setCrumbs([{ label: "overview", href: "#/" }, { label: "delivery setup", href: "#/program-studio" }, { label: "generated bundle" }]);
  const response = await api(`/api/setup/bundle?proposal_file=${encodeURIComponent(proposalFile)}`);
  renderStudioBundle(response.data);
  if (anchor) requestAnimationFrame(() => document.getElementById(anchor)?.scrollIntoView({ block: "start" }));
}

async function viewProgramStudio(family = "program", name) {
  family = STUDIO_FAMILIES.includes(family) ? family : "program";
  const familyLabel = family === "program" ? "delivery plans" : family === "workflow" ? "work flows" : "teams and review";
  setCrumbs([{ label: "overview", href: "#/" }, { label: "delivery setup", href: "#/program-studio" }, { label: familyLabel }, ...(name ? [{ label: name }] : [])]);
  studioState.inventory = (await api("/api/program-studio")).data;
  studioState.family = family; studioState.error = ""; studioState.selected = ""; studioState.jsonDraft = ""; studioState.jsonPointer = "";
  studioState.view = "plan";
  studioState.planSection = family === "organization" ? "responsibilities" : "scope";
  studioState.technicalMode = "graph";
  const familyModel = studioFamilyModel(family);
  const chosen = (!name && family === "program" && pendingProgramSetup)
    ? null
    : (name || familyModel.items?.[0]?.name);
  if (chosen) {
    const detail = (await api(`/api/program-studio/${encodeURIComponent(family)}/${encodeURIComponent(chosen)}`)).data;
    studioState.name = detail.name; studioState.document = clone(detail.raw); studioState.model = detail; studioState.exists = true;
  } else {
    studioState.document = clone(familyModel.draft); studioState.name = studioState.document.slug; studioState.model = null; studioState.exists = false;
    if (family === "program" && pendingProgramSetup) {
      const phase = Number(pendingProgramSetup.phase);
      studioState.document.scope ||= {};
      studioState.document.scope.project = pendingProgramSetup.project || "";
      if (Number.isInteger(phase) && phase >= 0) {
        studioState.document.scope.phases = { from: phase, through: phase };
      }
      studioState.setupContext = { ...pendingProgramSetup };
      pendingProgramSetup = null;
    } else {
      studioState.setupContext = null;
    }
  }
  if (chosen) studioState.setupContext = null;
  const requestedView = new URLSearchParams(location.search).get("studioview");
  if (STUDIO_VIEWS.includes(requestedView)) studioState.view = requestedView;
  const requestedTechnical = new URLSearchParams(location.search).get("studiotechnical");
  if (["graph", "config"].includes(requestedTechnical)) studioState.technicalMode = requestedTechnical;
  const requestedScenario = new URLSearchParams(location.search).get("studioscenario");
  if (requestedScenario) studioState.scenario = requestedScenario;
  if (studioState.model) renderProgramStudio(); else { renderProgramStudio(); await refreshStudioModel(); }
}

/* ── router ─────────────────────────────────────────────────────────── */

async function route({ focusMain = false } = {}) {
  const routeFocus = focusMain ? null : captureAppFocus();
  stopMcPoll(); // leaving mission control stops its poll
  stopRunLive(); // leaving the run view closes its live tail
  stopProgramLive(); // leaving an explicit program run closes its live tail
  app.setAttribute("aria-busy", "true");
  app.classList.remove("board-action-snapshot");
  app.innerHTML = stateHtml("Loading…");
  const hash = decodeURIComponent(location.hash.replace(/^#/, "")) || "/";
  const parts = hash.split("/").filter(Boolean);
  try {
    await loadPresentationCatalog();
    const projects = await loadProjects();
    const requestedProject = new URLSearchParams(location.search).get("project")
      || routeProject(parts);
    let blockedByProjectChoice = false;
    if (requestedProject) {
      if (projectBySlug(requestedProject)) rememberProject(requestedProject);
      else {
        viewUnavailableProject(requestedProject);
        blockedByProjectChoice = true;
      }
    } else if (!selectedProject) {
      selectedProject = storedProject();
    }
    if (!blockedByProjectChoice && selectedProject && !projectBySlug(selectedProject)) {
      viewUnavailableProject(selectedProject);
      blockedByProjectChoice = true;
    }
    if (!blockedByProjectChoice && parts[0] === "projects") {
      viewProjectSelector(projectReturnHash);
      blockedByProjectChoice = true;
    }
    if (!blockedByProjectChoice && projects.length > 1 && !selectedProject) {
      projectReturnHash = `#${hash}`;
      viewProjectSelector(projectReturnHash);
      blockedByProjectChoice = true;
    }
    if (!blockedByProjectChoice && projects.length === 1 && !selectedProject) {
      rememberProject(projects[0].slug);
    }
    let handled = true;
    if (blockedByProjectChoice) handled = true;
    else if (!parts.length) await viewBoard(selectedProject);
    else if (parts[0] === "p" && parts.length === 2) await viewProject(parts[1]);
    else if (parts[0] === "p" && parts[2] === "ph") await viewPhase(parts[1], parts[3]);
    else if (parts[0] === "p" && parts[2] === "s") await viewStory(parts[1], parts[3]);
    else if (parts[0] === "p" && parts[2] === "t") await viewTrace(parts[1], parts[3]);
    else if (parts[0] === "wl") await viewWorklog(parts.slice(1).join("/"));
    else if (parts[0] === "board") await viewBoard(parts[1]);
    else if (parts[0] === "orchestration") await viewOrchestration(parts[1]);
    else if (parts[0] === "programs") await viewPrograms(parts[1]);
    else if (parts[0] === "program-studio" && parts.length === 1) await viewDeliverySetup();
    else if (parts[0] === "program-studio" && parts[1] === "bundle") await viewStudioBundle(parts[2]);
    else if (parts[0] === "program-studio") await viewProgramStudio(parts[1], parts[2]);
    else if (parts[0] === "edit") await viewEdit(parts[1]);
    else if (parts[0] === "health") await viewHealth();
    else if (parts[0] === "mc") await viewMissionControl();
    else if (parts[0] === "f") await viewFile(parts.slice(1).join("/"));
    else handled = false;
    if (!handled) app.innerHTML = stateHtml(`Unknown view: ${hash}`, true);
  } catch (err) {
    app.innerHTML = stateHtml(err.message, true);
  } finally {
    enhanceSemantics(app);
    updatePrimaryNavigation(hash);
    announceRoute();
    app.setAttribute("aria-busy", "false");
    if (focusMain) {
      requestAnimationFrame(() => {
        const target = app.querySelector("h1") || app;
        if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
        target.focus();
        target.scrollIntoView({ block: "start" });
      });
    } else {
      requestAnimationFrame(() => restoreAppFocus(routeFocus));
    }
  }
}

document.getElementById("skip-link").addEventListener("click", () => {
  const target = app.querySelector("h1") || app;
  if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
  target.focus();
  target.scrollIntoView({ block: "start" });
});
document.getElementById("refresh-btn").addEventListener("click", () => route());
document.getElementById("project-switcher").addEventListener("click", () => {
  projectReturnHash = location.hash && location.hash !== "#/projects"
    ? location.hash : `#/board/${encodeURIComponent(selectedProject)}`;
});
window.addEventListener("hashchange", () => route({ focusMain: true }));

api("/api/context").then((body) => {
  footRoot.textContent = body.data.root;
}).catch(() => {});
route();
