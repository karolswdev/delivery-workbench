/* Workspace layout grid — CSS grid shell with named areas.
 * Loaded by index.html after components.js and interactions.js.
 * Manages panel visibility, panel state persistence, resizable
 * dividers, mobile tab bar, and keyboard shortcuts for panel toggling. */

"use strict";

window.DW = window.DW || {};

/* ── Panel registry ────────────────────────────────────── */

const PANELS = {
  board:    { key: "1", label: "Board",    icon: "☰", area: "board",    default: true },
  session:  { key: "2", label: "Session",  icon: "▶", area: "session",  default: false },
  diff:     { key: "3", label: "Diff",     icon: "±", area: "diff",     default: false },
  terminal: { key: "4", label: "Terminal", icon: ">_",     area: "terminal", default: false },
  services: { key: "5", label: "Services", icon: "⚙", area: "services", default: false },
  insights: { key: "6", label: "Insights", icon: "☆", area: "insights", default: false },
};

const PANEL_IDS = Object.keys(PANELS);

const STORAGE_KEY = "delivery-workbench.panels";
const SIZES_STORAGE_KEY = "delivery-workbench.panel-sizes";

function loadPanelState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (_) { /* storage unavailable */ }
  const state = {};
  for (const [id, cfg] of Object.entries(PANELS)) state[id] = cfg.default;
  return state;
}

function savePanelState(state) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
  catch (_) { /* ignore */ }
}

function loadPanelSizes() {
  try {
    const raw = localStorage.getItem(SIZES_STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (_) { /* storage unavailable */ }
  return {};
}

function savePanelSizes(sizes) {
  try { localStorage.setItem(SIZES_STORAGE_KEY, JSON.stringify(sizes)); }
  catch (_) { /* ignore */ }
}

/* ── Layout engine ─────────────────────────────────────── */

class WorkspaceLayout {
  constructor(container) {
    this.container = container;
    this.state = loadPanelState();
    this.sizes = loadPanelSizes();
    this._shortcuts = this._onKeydown.bind(this);
    this._resizeManager = null;
    this._resizeRegistrations = [];
    this._initialized = false;
    document.addEventListener("keydown", this._shortcuts);
  }

  /**
   * Initialize the workspace layout inside the container.
   * Renders toolbar, panel containers, dividers, mobile tab bar,
   * wires events, and applies the initial state.
   */
  init(container) {
    if (container) this.container = container;
    if (this._initialized) {
      this.apply();
      return;
    }

    // Render toolbar
    const toolbarHtml = this.renderToolbar();
    // Render mobile tab bar
    const mobileTabsHtml = this._renderMobileTabs();
    // Render panel containers with dividers between them
    const panelsHtml = this._renderPanelContainers();

    this.container.innerHTML = toolbarHtml + mobileTabsHtml +
      `<div class="workspace-panels" data-panels="" data-panel-count="0">${panelsHtml}</div>`;

    this._panelsContainer = this.container.querySelector(".workspace-panels");

    // Wire toolbar clicks
    this.wireToolbar();
    // Wire mobile tab clicks
    this._wireMobileTabs();
    // Set up resize dividers
    this._initDividers();
    // Apply saved sizes
    this._applySavedSizes();
    // Apply initial state
    this.apply();

    this._initialized = true;
  }

  /** Toggle a panel open or closed */
  toggle(panelId) {
    if (!(panelId in PANELS)) return;
    this.state[panelId] = !this.state[panelId];
    savePanelState(this.state);
    this.apply();
    this.container.dispatchEvent(new CustomEvent("dw-panel-change", {
      detail: { panel: panelId, open: this.state[panelId] },
    }));
  }

  /** Open a specific panel */
  open(panelId) {
    if (!(panelId in PANELS) || this.state[panelId]) return;
    this.state[panelId] = true;
    savePanelState(this.state);
    this.apply();
  }

  /** Close a specific panel */
  close(panelId) {
    if (!(panelId in PANELS) || !this.state[panelId]) return;
    this.state[panelId] = false;
    savePanelState(this.state);
    this.apply();
  }

  /** Check if a panel is open */
  isOpen(panelId) {
    return Boolean(this.state[panelId]);
  }

  /** Get the DOM element for a panel */
  panelElement(panelId) {
    if (!this.container) return null;
    return this.container.querySelector(`[data-panel="${panelId}"]`);
  }

  /** Apply current state to the DOM */
  apply() {
    const openPanels = Object.entries(this.state)
      .filter(([, open]) => open)
      .map(([id]) => id);

    const target = this._panelsContainer || this.container;
    target.dataset.panels = openPanels.join(",");
    target.dataset.panelCount = String(openPanels.length);

    for (const [id] of Object.entries(PANELS)) {
      const el = this.container.querySelector(`[data-panel="${id}"]`);
      if (!el) continue;
      el.hidden = !this.state[id];
      el.setAttribute("aria-hidden", String(!this.state[id]));
    }

    // Show/hide dividers based on adjacent panel visibility
    this._updateDividers();
    this._updateToolbar();
    this._updateMobileTabs();
  }

  /** Render the panel toggle toolbar */
  renderToolbar() {
    const buttons = Object.entries(PANELS).map(([id, cfg]) => {
      const active = this.state[id];
      return `<button type="button" class="panel-toggle${active ? " active" : ""}"
        data-panel-toggle="${id}" aria-pressed="${active}"
        title="${cfg.label} (Ctrl+${cfg.key})">
        ${cfg.label}
      </button>`;
    }).join("");

    return `<div class="panel-toolbar" role="toolbar" aria-label="Panel controls">${buttons}</div>`;
  }

  /** Wire toolbar button clicks */
  wireToolbar() {
    this.container.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-panel-toggle]");
      if (!btn) return;
      this.toggle(btn.dataset.panelToggle);
    });
  }

  /* ── Private: panel containers ───────────────────────── */

  _renderPanelContainers() {
    const parts = [];
    const ids = PANEL_IDS;
    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      const cfg = PANELS[id];
      // Add divider before each panel except the first
      if (i > 0) {
        parts.push(
          `<div class="workspace-divider" data-divider-before="${id}" ` +
          `role="separator" aria-orientation="vertical" aria-label="Resize between panels" ` +
          `tabindex="0" hidden></div>`
        );
      }
      parts.push(
        `<div class="workspace-panel" data-panel="${id}" ` +
        `role="tabpanel" aria-label="${cfg.label} panel" hidden ` +
        `aria-hidden="true" style="min-width: ${_minWidth(id)}px"></div>`
      );
    }
    return parts.join("");
  }

  _renderMobileTabs() {
    const tabs = Object.entries(PANELS).map(([id, cfg]) => {
      const active = this.state[id];
      return `<button type="button" class="mobile-panel-tab${active ? " active" : ""}"
        data-mobile-tab="${id}" aria-pressed="${active}">
        <span class="mobile-tab-icon" aria-hidden="true">${cfg.icon}</span>
        <span class="mobile-tab-label">${cfg.label}</span>
      </button>`;
    }).join("");
    return `<div class="mobile-panel-tabs" role="tablist" aria-label="Panel tabs">${tabs}</div>`;
  }

  _wireMobileTabs() {
    this.container.addEventListener("click", (e) => {
      const tab = e.target.closest("[data-mobile-tab]");
      if (!tab) return;
      this.toggle(tab.dataset.mobileTab);
    });
  }

  _updateMobileTabs() {
    for (const [id] of Object.entries(PANELS)) {
      const tab = this.container.querySelector(`[data-mobile-tab="${id}"]`);
      if (!tab) continue;
      const active = this.state[id];
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-pressed", String(active));
    }
  }

  /* ── Private: resize dividers ────────────────────────── */

  _initDividers() {
    if (!window.DW.ResizeManager) return;
    this._resizeManager = new window.DW.ResizeManager();

    const dividers = this.container.querySelectorAll(".workspace-divider");
    for (const divider of dividers) {
      const beforeId = divider.dataset.dividerBefore;
      const idx = PANEL_IDS.indexOf(beforeId);
      if (idx <= 0) continue;

      // The divider resizes the panel to its left
      const leftId = PANEL_IDS[idx - 1];
      const leftPanel = this.container.querySelector(`[data-panel="${leftId}"]`);
      if (!leftPanel) continue;

      const self = this;
      const reg = this._resizeManager.register(divider, {
        direction: "horizontal",
        target: leftPanel,
        minSize: _minWidth(leftId),
        maxSize: 1200,
      });

      // Save sizes on resize end
      divider.addEventListener("pointerup", () => {
        self.sizes[leftId] = leftPanel.offsetWidth;
        savePanelSizes(self.sizes);
      });

      this._resizeRegistrations.push(reg);
    }
  }

  _updateDividers() {
    const dividers = this.container.querySelectorAll(".workspace-divider");
    for (const divider of dividers) {
      const beforeId = divider.dataset.dividerBefore;
      const idx = PANEL_IDS.indexOf(beforeId);
      if (idx <= 0) { divider.hidden = true; continue; }

      // Show divider only if both adjacent panels are visible
      const leftId = PANEL_IDS[idx - 1];
      const leftOpen = this.state[leftId];
      const rightOpen = this.state[beforeId];
      // Actually: find the nearest open panel to the left
      let hasOpenLeft = false;
      for (let i = idx - 1; i >= 0; i--) {
        if (this.state[PANEL_IDS[i]]) { hasOpenLeft = true; break; }
      }
      divider.hidden = !(hasOpenLeft && rightOpen);
    }
  }

  _applySavedSizes() {
    for (const [id, width] of Object.entries(this.sizes)) {
      const panel = this.container.querySelector(`[data-panel="${id}"]`);
      if (panel && width) {
        panel.style.width = Math.max(_minWidth(id), width) + "px";
      }
    }
  }

  _updateToolbar() {
    for (const [id] of Object.entries(PANELS)) {
      const btn = this.container.querySelector(`[data-panel-toggle="${id}"]`);
      if (!btn) continue;
      const active = this.state[id];
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-pressed", String(active));
    }
  }

  _onKeydown(e) {
    if (!e.ctrlKey || e.shiftKey || e.altKey || e.metaKey) return;
    for (const [id, cfg] of Object.entries(PANELS)) {
      if (e.key === cfg.key) {
        e.preventDefault();
        this.toggle(id);
        return;
      }
    }
  }

  destroy() {
    document.removeEventListener("keydown", this._shortcuts);
    if (this._resizeManager) this._resizeManager.destroy();
    this._resizeRegistrations = [];
    this._initialized = false;
  }
}

/** Minimum width per panel type (px). */
function _minWidth(panelId) {
  switch (panelId) {
    case "board": return 320;
    case "session": return 280;
    case "terminal": return 240;
    default: return 240;
  }
}

window.DW.WorkspaceLayout = WorkspaceLayout;
window.DW.PANELS = PANELS;
