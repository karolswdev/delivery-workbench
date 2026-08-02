/* Delivery Workbench — hash router and init.
 * All view functions, utilities, and state live in their respective modules:
 * core.js, board.js, views.js, editor.js, orchestration.js, runs.js, studio.js.
 * This file contains only the router dispatch and DOM event wiring. */

"use strict";

async function route({ focusMain = false } = {}) {
  const routeFocus = focusMain ? null : captureAppFocus();
  const hash = decodeURIComponent(location.hash.replace(/^#/, "")) || "/";
  const parts = hash.split("/").filter(Boolean);
  stopMcPoll();
  stopRunLive();
  stopProgramLive();
  app.setAttribute("aria-busy", "true");
  app.classList.remove("board-action-snapshot", "route-ready");
  app.innerHTML = routeSkeletonHtml(`Loading ${parts[0] || "work"}`);
  try {
    let projects;
    if (SNAPSHOT_MODE) {
      // Preserve the deterministic screenshot path: each synchronous read
      // completes before the next starts, matching the load-event harness.
      await loadPresentationCatalog();
      projects = await loadProjects();
    } else {
      const presentationPromise = loadPresentationCatalog();
      const projectsPromise = loadProjects();
      await presentationPromise;
      updateRouteSkeleton("Presentation ready. Loading project facts…");
      projects = await projectsPromise;
      updateRouteSkeleton("Project facts ready. Opening view…");
    }
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
    else if (parts[0] === "live") await viewLive(parts[1], parts[2], parts[3]);
    else if (parts[0] === "programs") await viewPrograms(parts[1]);
    else if (parts[0] === "program-studio" && parts.length === 1) await viewDeliverySetup();
    else if (parts[0] === "program-studio" && parts[1] === "bundle") await viewStudioBundle(parts[2]);
    else if (parts[0] === "program-studio") await viewProgramStudio(parts[1], parts[2]);
    else if (parts[0] === "edit") await viewEdit(parts[1]);
    else if (parts[0] === "health") await viewHealth();
    else if (parts[0] === "mc") await viewMissionControl();
    else if (parts[0] === "f") await viewFile(parts.slice(1).join("/"));
    else if (parts[0] === "design") { app.innerHTML = window.DW.designReferencePage(); }
    else handled = false;
    if (!handled) app.innerHTML = stateHtml(`Unknown view: ${hash}`, true);
    else if (SNAPSHOT_MODE && SNAPSHOT_MEMORY_SCENARIO) window.DW.openMemorySnapshot();
  } catch (err) {
    app.innerHTML = stateHtml(err.message, true);
  } finally {
    enhanceSemantics(app);
    app.classList.add("route-ready");
    if (SNAPSHOT_MODE && SNAPSHOT_DESIGN_FOCUS && parts[0] === "design") {
      focusElement(app.querySelector("button, dw-button"));
    }
    updatePrimaryNavigation(hash);
    announceRoute();
    app.setAttribute("aria-busy", "false");
    if (focusMain) {
      const target = app.querySelector("h1") || app;
      if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
      focusElement(target);
      target.scrollIntoView({ block: "start" });
    } else {
      restoreAppFocus(routeFocus);
    }
  }
}

document.getElementById("skip-link").addEventListener("click", () => {
  const target = app.querySelector("h1") || app;
  if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
  focusElement(target);
  target.scrollIntoView({ block: "start" });
});
document.getElementById("refresh-btn").addEventListener("click", () => route());
document.getElementById("density-toggle").addEventListener("click", () => {
  const current = document.documentElement.dataset.density || "comfortable";
  applyDensity(current === "compact" ? "comfortable" : "compact");
});
document.addEventListener("click", (event) => {
  const copy = event.target.closest?.("[data-copy-text]");
  if (!copy) return;
  event.preventDefault();
  copyToClipboard(copy.dataset.copyText || "", copy);
});
document.getElementById("project-switcher").addEventListener("click", () => {
  projectReturnHash = location.hash && location.hash !== "#/projects"
    ? location.hash : `#/board/${encodeURIComponent(selectedProject)}`;
});
window.addEventListener("hashchange", () => route({ focusMain: true }));

/* === Progressive disclosure: Advanced dropdown === */
(function wireAdvancedDropdown() {
  const toggle = document.getElementById("advanced-toggle");
  const dropdown = document.getElementById("advanced-dropdown");
  if (!toggle || !dropdown) return;

  function openDropdown() {
    toggle.setAttribute("aria-expanded", "true");
    dropdown.classList.add("open");
    const first = dropdown.querySelector("a");
    focusElement(first);
  }
  function closeDropdown(returnFocus) {
    toggle.setAttribute("aria-expanded", "false");
    dropdown.classList.remove("open");
    if (returnFocus) focusElement(toggle);
  }
  function isOpen() { return dropdown.classList.contains("open"); }

  toggle.addEventListener("click", () => {
    if (isOpen()) closeDropdown(true);
    else openDropdown();
  });

  document.addEventListener("click", (e) => {
    if (isOpen() && !toggle.contains(e.target) && !dropdown.contains(e.target)) {
      closeDropdown(false);
    }
  });

  dropdown.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      e.preventDefault();
      closeDropdown(true);
    }
  });
  toggle.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && isOpen()) {
      e.preventDefault();
      closeDropdown(true);
    }
  });

  dropdown.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => closeDropdown(false));
  });
})();

applyDensity(SNAPSHOT_MODE && DENSITIES.has(SNAPSHOT_DENSITY) ? SNAPSHOT_DENSITY : storedDensity(), false);
api("/api/context").then((body) => {
  footRoot.textContent = body.data.root;
}).catch(() => {});
route();
