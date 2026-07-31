/* Workspace layout grid — CSS grid shell with named areas.
 * Loaded by index.html after components.js and interactions.js.
 * Manages panel visibility, panel state persistence, and
 * keyboard shortcuts for panel toggling. */

"use strict";

window.DW = window.DW || {};

/* ── Panel registry ────────────────────────────────────── */

const PANELS = {
  board:    { key: "1", label: "Board",    area: "board",    default: true },
  session:  { key: "2", label: "Session",  area: "session",  default: false },
  diff:     { key: "3", label: "Diff",     area: "diff",     default: false },
  terminal: { key: "4", label: "Terminal", area: "terminal", default: false },
  services: { key: "5", label: "Services", area: "services", default: false },
  insights: { key: "6", label: "Insights", area: "insights", default: false },
};

const STORAGE_KEY = "delivery-workbench.panels";

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

/* ── Layout engine ─────────────────────────────────────── */

class WorkspaceLayout {
  constructor(container) {
    this.container = container;
    this.state = loadPanelState();
    this._shortcuts = this._onKeydown.bind(this);
    document.addEventListener("keydown", this._shortcuts);
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

  /** Apply current state to the DOM */
  apply() {
    const openPanels = Object.entries(this.state)
      .filter(([, open]) => open)
      .map(([id]) => id);

    this.container.dataset.panels = openPanels.join(",");
    this.container.dataset.panelCount = String(openPanels.length);

    for (const [id] of Object.entries(PANELS)) {
      const el = this.container.querySelector(`[data-panel="${id}"]`);
      if (!el) continue;
      el.hidden = !this.state[id];
      el.setAttribute("aria-hidden", String(!this.state[id]));
    }

    this._updateToolbar();
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
  }
}

window.DW.WorkspaceLayout = WorkspaceLayout;
window.DW.PANELS = PANELS;
