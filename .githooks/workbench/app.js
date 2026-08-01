/* Delivery Workbench — hash router and init.
 * All view functions, utilities, and state live in their respective modules:
 * core.js, board.js, views.js, editor.js, orchestration.js, runs.js, studio.js.
 * This file contains only the router dispatch and DOM event wiring. */

"use strict";

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
