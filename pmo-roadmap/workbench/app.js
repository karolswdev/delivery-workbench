/* Delivery Workbench — hash router and init.
 * All view functions, utilities, and state live in their respective modules:
 * core.js, board.js, views.js, editor.js, orchestration.js, runs.js, studio.js.
 * This file contains only the router dispatch and DOM event wiring. */

"use strict";

/* ── Workspace layout singleton ────────────────────────── */

let _workspaceLayout = null;
let _lastBoardContent = "";

/** Routes that render inside the multi-panel workspace. */
function isWorkspaceRoute(parts) {
  if (!parts.length) return true;                   // root = board
  if (parts[0] === "board") return true;            // #/board, #/board/<slug>
  if (parts[0] === "p") return true;                // project / phase / story / trace
  if (parts[0] === "wl") return true;               // worklog
  return false;
}

/** Routes that populate the board panel (vs session panel). */
function isBoardRoute(parts) {
  if (!parts.length) return true;
  if (parts[0] === "board") return true;
  return false;
}

/**
 * Mount the workspace layout into the app element.
 * Returns the WorkspaceLayout instance.
 */
function mountWorkspace() {
  app.innerHTML = "";
  app.classList.add("workspace-active");
  const wrapper = document.createElement("div");
  wrapper.className = "workspace";
  app.appendChild(wrapper);

  if (_workspaceLayout) _workspaceLayout.destroy();
  _workspaceLayout = new window.DW.WorkspaceLayout(wrapper);
  _workspaceLayout.init(wrapper);
  return _workspaceLayout;
}

/** Tear down the workspace and return to full-page mode. */
function teardownWorkspace() {
  app.classList.remove("workspace-active");
  if (_workspaceLayout) {
    _workspaceLayout.destroy();
    _workspaceLayout = null;
  }
}

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
    else if (isWorkspaceRoute(parts)) {
      /* ── Workspace route: render view, then wrap in panels ── */
      if (isBoardRoute(parts)) {
        await viewBoard(parts[1] || selectedProject);
        /* Capture what viewBoard wrote to app */
        const boardContent = app.innerHTML;
        _lastBoardContent = boardContent;
        /* Mount workspace and place content */
        const ws = mountWorkspace();
        ws.open("board");
        const boardEl = ws.panelElement("board");
        if (boardEl) boardEl.innerHTML = boardContent;
      } else {
        /* Detail view (project, phase, story, trace, worklog) */
        if (parts[0] === "p" && parts.length === 2) await viewProject(parts[1]);
        else if (parts[0] === "p" && parts[2] === "ph") await viewPhase(parts[1], parts[3]);
        else if (parts[0] === "p" && parts[2] === "s") await viewStory(parts[1], parts[3]);
        else if (parts[0] === "p" && parts[2] === "t") await viewTrace(parts[1], parts[3]);
        else if (parts[0] === "wl") await viewWorklog(parts.slice(1).join("/"));
        else handled = false;

        if (handled) {
          const sessionContent = app.innerHTML;
          const ws = mountWorkspace();
          ws.open("session");
          const sessionEl = ws.panelElement("session");
          if (sessionEl) sessionEl.innerHTML = sessionContent;
          /* Restore last board content if board panel is open */
          if (ws.isOpen("board") && _lastBoardContent) {
            const boardEl = ws.panelElement("board");
            if (boardEl) boardEl.innerHTML = _lastBoardContent;
          }
        }
      }
    }
    else if (parts[0] === "orchestration") { teardownWorkspace(); await viewOrchestration(parts[1]); }
    else if (parts[0] === "live") { teardownWorkspace(); await viewLive(parts[1], parts[2], parts[3]); }
    else if (parts[0] === "programs") { teardownWorkspace(); await viewPrograms(parts[1]); }
    else if (parts[0] === "program-studio" && parts.length === 1) { teardownWorkspace(); await viewDeliverySetup(); }
    else if (parts[0] === "program-studio" && parts[1] === "bundle") { teardownWorkspace(); await viewStudioBundle(parts[2]); }
    else if (parts[0] === "program-studio") { teardownWorkspace(); await viewProgramStudio(parts[1], parts[2]); }
    else if (parts[0] === "edit") { teardownWorkspace(); await viewEdit(parts[1]); }
    else if (parts[0] === "health") { teardownWorkspace(); await viewHealth(); }
    else if (parts[0] === "mc") { teardownWorkspace(); await viewMissionControl(); }
    else if (parts[0] === "f") { teardownWorkspace(); await viewFile(parts.slice(1).join("/")); }
    else if (parts[0] === "design") { teardownWorkspace(); app.innerHTML = window.DW.designReferencePage(); }
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

/* === Progressive disclosure: Advanced dropdown === */
(function wireAdvancedDropdown() {
  const toggle = document.getElementById("advanced-toggle");
  const dropdown = document.getElementById("advanced-dropdown");
  if (!toggle || !dropdown) return;

  function openDropdown() {
    toggle.setAttribute("aria-expanded", "true");
    dropdown.classList.add("open");
    const first = dropdown.querySelector("a");
    if (first) first.focus();
  }
  function closeDropdown(returnFocus) {
    toggle.setAttribute("aria-expanded", "false");
    dropdown.classList.remove("open");
    if (returnFocus) toggle.focus();
  }
  function isOpen() { return dropdown.classList.contains("open"); }

  toggle.addEventListener("click", () => {
    if (isOpen()) closeDropdown(true);
    else openDropdown();
  });

  /* Close on click outside */
  document.addEventListener("click", (e) => {
    if (isOpen() && !toggle.contains(e.target) && !dropdown.contains(e.target)) {
      closeDropdown(false);
    }
  });

  /* Keyboard: Escape closes, Tab traps within dropdown items */
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

  /* Close when navigating to a route from the dropdown */
  dropdown.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => closeDropdown(false));
  });
})();

api("/api/context").then((body) => {
  footRoot.textContent = body.data.root;
}).catch(() => {});
route();
