/* Delivery Workbench — hash-routed, API-backed. Canonical reads come live
 * from /api/* and mutations cross only guarded boundaries. Browser storage
 * keeps project choice and inert review drafts; Markdown remains authoritative. */

"use strict";

const app = document.getElementById("app");
const refreshButton = document.getElementById("refresh-btn");
const footRoot = document.getElementById("foot-root");
const routeStatus = document.getElementById("route-status");
const liveStatus = document.getElementById("live-status");
let presentationCatalog = null;
let semanticId = 0;
const returnFocus = new Map();
const liveAnnouncementKeys = new Map();
const PROJECT_STORAGE_KEY = "delivery-workbench.selected-project";
const DENSITY_STORAGE_KEY = "delivery-workbench.density";
const DENSITIES = new Set(["comfortable", "compact"]);
let projectInventory = null;
let selectedProject = "";
let projectReturnHash = "#/board";
let currentCrumbParts = [];

function storedProject() {
  try { return localStorage.getItem(PROJECT_STORAGE_KEY) || ""; }
  catch (_err) { return ""; }
}

function storedDensity() {
  try {
    const value = localStorage.getItem(DENSITY_STORAGE_KEY) || "comfortable";
    return DENSITIES.has(value) ? value : "comfortable";
  } catch (_err) {
    return "comfortable";
  }
}

function applyDensity(value, persist = true) {
  const density = DENSITIES.has(value) ? value : "comfortable";
  document.documentElement.dataset.density = density;
  const toggle = document.getElementById("density-toggle");
  if (toggle) {
    const compact = density === "compact";
    const state = toggle.querySelector("#density-state");
    if (state) state.textContent = compact ? "Compact" : "Comfortable";
    toggle.setAttribute("aria-pressed", String(compact));
    toggle.setAttribute("aria-label", compact
      ? "Use comfortable density" : "Use compact density");
    toggle.setAttribute("title", compact
      ? "Density: compact. Switch to comfortable."
      : "Density: comfortable. Switch to compact.");
  }
  if (persist) {
    try { localStorage.setItem(DENSITY_STORAGE_KEY, density); }
    catch (_err) {
      // A hardened browser may block storage. The visible setting still works
      // for this page and never changes repository data.
    }
  }
  return density;
}

function updateProjectCrumb() {
  const zone = document.querySelector("#project-switcher .crumb-zone");
  const project = document.querySelector("#project-switcher .crumb-project");
  if (!zone || !project) return;
  const routePart = currentCrumbParts.find((part) => {
    const label = String(part?.label || "").toLowerCase();
    return label && label !== "overview" && label !== selectedProject.toLowerCase();
  });
  zone.textContent = routePart?.label || "work";
  project.textContent = selectedProject || "Choose project";
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
  updateProjectCrumb();
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
    live: [["Mission control", "#/live"], ["Activity", "#/mc"]],
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
    <span class="selector-eyebrow ops-label">First, choose your work</span>
    <h1 id="project-selector-title">Choose a project</h1>
    ${explanation}
    <form id="project-selector-form">
      <fieldset aria-describedby="project-selector-error"><legend>Available projects</legend>
        <div class="project-options">${projects.map((project) => `<label>
          <input type="radio" name="project" value="${esc(project.slug)}" aria-describedby="project-selector-error"${project.slug === selectedProject ? " checked" : ""}>
          <span><strong>${esc(project.slug)}</strong><small>${project.next_story ? `${esc(project.next_story.title)} is next` : "No next work is available"}</small></span>
        </label>`).join("")}</div>
      </fieldset>
      <p id="project-selector-error" class="fielderr" role="alert" hidden>Choose a project before continuing.</p>
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
      form.querySelectorAll("input[name='project']").forEach((input) => input.setAttribute("aria-invalid", "true"));
      const error = form.querySelector("#project-selector-error");
      if (error) error.hidden = false;
      focusElement(form.querySelector("input"));
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
  "data-adoption-objection", "data-memory-open", "data-board-create",
  "data-board-move", "data-board-park", "name", "href",
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

function focusPathSegment(element) {
  const classes = [...element.classList]
    .filter((name) => name !== "focus-restored"
      && !name.startsWith("is-") && !name.startsWith("state-"));
  return `${element.localName}${classes.map((name) => `.${selectorEscape(name)}`).join("")}`;
}

function focusSelector(element) {
  if (!(element instanceof Element)) return "";
  if (element.id) return `#${selectorEscape(element.id)}`;
  for (const attribute of FOCUS_IDENTITY_ATTRIBUTES) {
    const value = element.getAttribute(attribute);
    if (value === null) continue;
    const selector = value === ""
      ? `${element.localName}[${attribute}]`
      : `${element.localName}[${attribute}="${selectorEscape(value)}"]`;
    if (app.querySelectorAll(selector).length === 1) return selector;
    if (value === "" && attribute.startsWith("data-board-")) {
      const story = element.closest("[data-story]")?.getAttribute("data-story");
      if (story) {
        return `[data-story="${selectorEscape(story)}"] ${selector}`;
      }
      const phase = element.getAttribute("data-phase");
      if (phase !== null) return `${selector}[data-phase="${selectorEscape(phase)}"]`;
    }
  }

  // Controls such as native disclosure summaries have no explicit identifier.
  // Build a unique selector from stable ancestor classes so a redraw can restore
  // the same semantic control even when live banners change its numeric index.
  let path = focusPathSegment(element);
  let parent = element.parentElement;
  while (parent && parent !== app) {
    path = `${focusPathSegment(parent)} > ${path}`;
    if (app.querySelectorAll(path).length === 1) return path;
    parent = parent.parentElement;
  }
  return app.querySelectorAll(path).length === 1 ? path : "";
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

function focusElement(element) {
  if (!(element instanceof Element)) return false;
  const target = element.matches(FOCUSABLE_SELECTOR) || element.hasAttribute("tabindex")
    ? element : element.querySelector(FOCUSABLE_SELECTOR);
  if (!target || typeof target.focus !== "function") return false;
  target.focus({ preventScroll: true, focusVisible: true });
  const focused = document.activeElement === target || document.activeElement === element;
  if (!focused) return false;
  target.classList.add("focus-restored");
  target.addEventListener("blur", () => {
    target.classList.remove("focus-restored");
  }, { once: true });
  return true;
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
  return focusElement(target);
}

function renderPreservingAppFocus(render) {
  const focus = captureAppFocus();
  render();
  restoreAppFocus(focus);
}

function rememberReturnFocus(key, element = document.activeElement) {
  const selector = focusSelector(element);
  if (selector) returnFocus.set(key, selector);
}

function restoreReturnFocus(key, fallback = "") {
  const selector = returnFocus.get(key) || fallback;
  returnFocus.delete(key);
  const candidates = [...document.querySelectorAll(selector)];
  focusElement(candidates.find((element) => element.offsetParent !== null) || candidates[0]);
}

function focusRegion(selector) {
  const region = document.querySelector(selector);
  if (!region) return;
  if (!region.hasAttribute("tabindex")) region.setAttribute("tabindex", "-1");
  focusElement(region);
  region.scrollIntoView({ block: "nearest" });
}

function focusConsentSnapshot(selector) {
  const region = document.querySelector(selector);
  if (!region) return;
  focusElement(region);
  region.scrollIntoView({ block: "start" });
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
      focusElement(summary);
    });
    details.addEventListener("toggle", () => {
      if (!details.open && details.contains(document.activeElement)) {
        focusElement(summary);
      }
    });
  });
}

function looksCopyableIdentifier(value) {
  const text = String(value || "").trim();
  return text.length >= 24 && !/\s/.test(text)
    && (/^[a-f0-9]{24,}$/i.test(text) || /(?:receipt|run|program|session|correlation|digest|hash|token)[-_:/]/i.test(text));
}

function enhanceCopyableIdentifiers(root = app) {
  root.querySelectorAll("code").forEach((code) => {
    if (code.closest("pre, button, a, .copyable-id") || !looksCopyableIdentifier(code.textContent)) return;
    const wrapper = document.createElement("span");
    wrapper.className = "copyable-id";
    code.parentNode.insertBefore(wrapper, code);
    wrapper.appendChild(code);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-id-action";
    button.dataset.copyText = code.textContent.trim();
    button.setAttribute("aria-label", "Copy identifier");
    button.textContent = "Copy";
    wrapper.appendChild(button);
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
  enhanceCopyableIdentifiers(root);
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
    focusElement(document.querySelector(nextSelector));
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
    focusElement(items[nextIndex]);
  });
}

function updatePrimaryNavigation(hash) {
  const surface = hash.split("/").filter(Boolean)[0] || "";
  const isAdvanced = surface === "program-studio" || surface === "edit"
    || surface === "orchestration"
    || surface === "live" || surface === "programs" || surface === "mc";
  const activeId = !surface || surface === "board" || surface === "p" ? "work-link"
    : surface === "health" ? "health-link" : "";
  document.querySelectorAll(".primary-nav > a.navlink").forEach((link) => {
    if (link.id === activeId) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  /* Highlight the Advanced toggle when an advanced route is active */
  const advToggle = document.getElementById("advanced-toggle");
  if (advToggle) {
    if (isAdvanced) advToggle.setAttribute("aria-current", "page");
    else advToggle.removeAttribute("aria-current");
  }
  /* Highlight the specific item inside the dropdown */
  document.querySelectorAll(".advanced-dropdown a").forEach((link) => {
    const href = link.getAttribute("href") || "";
    const linkSurface = href.replace("#/", "").split("/")[0];
    if (linkSurface === surface) link.setAttribute("aria-current", "page");
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
window.SNAPSHOT_MODE = SNAPSHOT_MODE;
const SNAPSHOT_LIVE_STATE = new URLSearchParams(location.search).get("liveconnection");
const SNAPSHOT_MEMORY_SCENARIO = new URLSearchParams(location.search).get("memoryscenario") || "";
const SNAPSHOT_DENSITY = new URLSearchParams(location.search).get("density") || "";
const SNAPSHOT_DESIGN_FOCUS = new URLSearchParams(location.search).has("designfocus");
const LIVE_TECHNICAL_OPEN = new URLSearchParams(location.search).has("livetechnical");
const SNAPSHOT_BOUNDED_FOCUS = new URLSearchParams(location.search).get("boundedfocus");
const SNAPSHOT_BOUNDED_PREVIEW = new URLSearchParams(location.search).get("boundedpreview");
const SNAPSHOT_BOUNDED_ERROR = new URLSearchParams(location.search).get("boundederror");
const SNAPSHOT_LIVE_SCENARIO = new URLSearchParams(location.search).get("livescenario") || "";
const ADOPTION_PROPOSAL_FILE = new URLSearchParams(location.search).get("proposal") || "";
const ADOPTION_PROPOSAL_ID = new URLSearchParams(location.search).get("setuppreview") || "";

function syncGet(path) {
  if (!SNAPSHOT_MODE) throw new Error("Synchronous reads are limited to deterministic snapshots");
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
  const refreshed = new Date().toLocaleTimeString();
  if (refreshButton) {
    const label = `Refresh saved repository facts. Last refreshed ${refreshed}.`;
    refreshButton.setAttribute("title", label);
    refreshButton.setAttribute("aria-label", label);
  }
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
  currentCrumbParts = parts || [];
  updateProjectCrumb();
}

function stateHtml(text, isError) {
  return `<div class="state${isError ? " error" : ""}" role="${isError ? "alert" : "status"}">${esc(text)}</div>`;
}

function routeSkeletonHtml(label = "Loading view") {
  return `<section class="route-skeleton" aria-label="${esc(label)}">
    <div class="route-skeleton-head"><dw-skeleton lines="2" variant="text"></dw-skeleton></div>
    <div class="route-skeleton-grid">
      <dw-skeleton lines="5" variant="card"></dw-skeleton>
      <dw-skeleton lines="5" variant="card"></dw-skeleton>
    </div>
    <span class="visually-hidden" data-route-loading>Loading saved repository facts…</span>
  </section>`;
}

function updateRouteSkeleton(message) {
  const status = app.querySelector("[data-route-loading]");
  if (status) status.textContent = message;
}

async function copyToClipboard(text, button) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      const helper = document.createElement("textarea");
      helper.value = text;
      helper.setAttribute("readonly", "");
      helper.className = "copy-helper";
      document.body.appendChild(helper);
      helper.select();
      const copied = document.execCommand("copy");
      helper.remove();
      if (!copied) throw new Error("copy unavailable");
    }
    const previous = button.textContent;
    button.textContent = "Copied";
    announceLiveUpdate("copy-identifier", Date.now(), "Identifier copied.");
    window.setTimeout(() => { if (button.isConnected) button.textContent = previous; }, 1600);
  } catch (_err) {
    announceLiveUpdate("copy-identifier-error", Date.now(), "Could not copy the identifier. Select it and copy it manually.");
  }
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
      <span class="brief-argv-label ops-label">argv</span>
      ${command.map((arg, index) => `<code data-argv-index="${index}">${esc(arg)}</code>`).join("")}
    </div>` : `<div class="brief-manual"><strong>manual act</strong><span>No command is synthesized for this decision.</span></div>`}
    <div class="brief-readonly">Recommendation only — review the separate deliberate-step boundary below before anything runs.</div>
  </div>`;
}

function stepArgvHtml(argv, label) {
  if (!Array.isArray(argv)) return "";
  return `<div class="brief-argv" aria-label="${esc(label)} argument vector">
    <span class="brief-argv-label ops-label">${esc(label)}</span>
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
    if (!SNAPSHOT_MODE) focusRegion(".step-confirmation");
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
        <div class="brief-eyebrow ops-label">repository briefing</div>
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
    ? `<div class="arrival-work"><span class="ops-label">${esc(presentationCopy("current_work"))}</span><div><strong>${esc(work.title)}</strong><small>${esc(work.story_id)} · ${esc(work.status)}</small></div></div>`
    : `<div class="arrival-work"><span class="ops-label">${esc(presentationCopy("current_work"))}</span><div><strong>${esc(presentedWork?.value || "No work is currently actionable")}</strong><small>${esc(presentationCopy("check_readiness"))} for the affected ${esc(productTerm("decision"))}.</small></div></div>`;
  return `<section class="arrival-panel readiness-${esc(setup.readiness)}" aria-labelledby="arrival-title">
    <div class="arrival-hero">
      <div><span class="arrival-eyebrow ops-label">${setup.healthy ? "healthy ordinary delivery" : "delivery needs attention"}</span>
        <h1 id="arrival-title">${esc(presentation.title)}</h1><p>${esc(presentation.summary)}</p></div>
      ${badge(setup.readiness, setup.readiness === "ready" ? "ok" : "issue")}
    </div>
    ${workLine}
    <div class="arrival-next"><span class="ops-label">${esc(productTerm("next_step"))}</span><strong>${esc(nextStep.label || presentationCopy("check_readiness"))}</strong><p>${esc(nextStep.summary || "")}</p></div>
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

const PARKED_COLUMNS = ["blocked", "on-hold"];
