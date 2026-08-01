"use strict";

/* ── Diff review panel (WLA-33-03) ────────────────────────────────────
 * Shows uncommitted changes (working tree + staged) for the current
 * project. Opens from the session panel header when changes exist, or
 * from the layout panel toggle (key 3). Uses the read-only
 * GET /api/diff?project=<slug> route and renders unified diffs via
 * the global diffHtml() helper from core.js.                          */

window.DW = window.DW || {};

class DiffPanel {
  constructor() {
    this._storyId = "";
    this._slug = "";
    this._files = [];
    this._loading = true;
    this._error = "";
    this._container = null;
    this._pollTimer = null;
  }

  /* ── public API ──────────────────────────────────────────── */

  open(storyId, slug) {
    this.close();
    this._storyId = storyId || "";
    this._slug = slug || selectedProject;
    this._files = [];
    this._loading = true;
    this._error = "";
    this._ensureContainer();
    this._mount();
    this._load();
  }

  close() {
    this._stopPoll();
    this._storyId = "";
    this._slug = "";
    this._files = [];
    this._loading = false;
    this._error = "";
    if (this._container) {
      this._container.innerHTML = "";
    }
  }

  isOpen() {
    return Boolean(this._slug);
  }

  render() {
    if (!this._slug) return "";

    if (this._loading && !this._files.length) {
      return this._shell(`
        <dw-skeleton lines="6"></dw-skeleton>
        <p class="diff-loading-hint">Loading diff...</p>
      `);
    }

    if (this._error) {
      return this._shell(`
        <div class="diff-error" role="alert">
          <strong>Could not load diff.</strong>
          <p>${esc(this._error)}</p>
          <button type="button" class="diff-retry">Retry</button>
        </div>
      `);
    }

    if (!this._files.length) {
      return this._shell(`
        ${this._headerHtml(0, 0, 0, 0)}
        <div class="diff-empty">
          <p>No uncommitted changes.</p>
        </div>
      `);
    }

    const counts = this._counts();
    const header = this._headerHtml(
      this._files.length, counts.added, counts.modified, counts.deleted
    );
    const fileList = this._fileListHtml();

    return this._shell(`${header}${fileList}`);
  }

  /* ── internal ────────────────────────────────────────────── */

  _shell(body) {
    return `<div class="diff-panel" role="complementary" aria-label="Diff panel for ${esc(this._slug)}">${body}</div>`;
  }

  _headerHtml(total, added, modified, deleted) {
    const badges = [];
    if (added) badges.push(`<dw-badge variant="ok" count="${added} added"></dw-badge>`);
    if (modified) badges.push(`<dw-badge variant="in-progress" count="${modified} modified"></dw-badge>`);
    if (deleted) badges.push(`<dw-badge variant="danger" count="${deleted} deleted"></dw-badge>`);
    const storyLabel = this._storyId
      ? `<code>${esc(this._storyId)}</code>`
      : `<code>${esc(this._slug)}</code>`;

    return `
      <div class="diff-header">
        <div class="diff-title-row">
          ${storyLabel}
          <dw-badge variant="default" count="${total} file${total === 1 ? "" : "s"} changed"></dw-badge>
        </div>
        <div class="diff-badges">${badges.join("")}</div>
        <div class="diff-controls">
          <button type="button" class="diff-refresh-btn" aria-label="Refresh diff">Refresh</button>
          <button type="button" class="diff-close-btn" aria-label="Close diff panel">Close</button>
        </div>
      </div>`;
  }

  _fileListHtml() {
    return `<div class="diff-file-list">${this._files.map((file, idx) => {
      const statusLabel = file.status === "A" ? "added"
        : file.status === "D" ? "deleted"
        : "modified";
      const variant = file.status === "A" ? "ok"
        : file.status === "D" ? "danger"
        : "in-progress";
      return `
        <dw-fold class="diff-file-fold" data-diff-idx="${idx}">
          <div slot="summary" class="diff-file-summary">
            <dw-badge variant="${variant}" count="${statusLabel}"></dw-badge>
            <code class="diff-file-path">${esc(file.path)}</code>
          </div>
          <pre class="diff diff-file-content">${diffHtml(file.diff || "")}</pre>
        </dw-fold>`;
    }).join("")}</div>`;
  }

  _counts() {
    let added = 0, modified = 0, deleted = 0;
    for (const file of this._files) {
      if (file.status === "A") added++;
      else if (file.status === "D") deleted++;
      else modified++;
    }
    return { added, modified, deleted };
  }

  _ensureContainer() {
    let el = document.querySelector('[data-panel="diff"] .diff-panel-root');
    if (!el) {
      const panel = document.querySelector('[data-panel="diff"]');
      if (panel) {
        el = document.createElement("div");
        el.className = "diff-panel-root";
        panel.innerHTML = "";
        panel.appendChild(el);
      }
    }
    this._container = el || null;
  }

  _mount() {
    if (!this._container) return;
    this._container.innerHTML = this.render();
    this._wire();
  }

  _wire() {
    if (!this._container) return;
    const closeBtn = this._container.querySelector(".diff-close-btn");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        this.close();
        if (window.DW._layout) window.DW._layout.close("diff");
      });
    }
    const refreshBtn = this._container.querySelector(".diff-refresh-btn");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => this._load());
    }
    const retryBtn = this._container.querySelector(".diff-retry");
    if (retryBtn) {
      retryBtn.addEventListener("click", () => this._load());
    }
  }

  async _load() {
    this._loading = true;
    this._error = "";
    this._mount();

    try {
      const res = await api(
        `/api/diff?project=${encodeURIComponent(this._slug)}`
      );
      this._files = res.data.files || [];
      this._loading = false;
      this._mount();
      this._updateSessionBadge();
      this._startPoll();
    } catch (err) {
      this._error = err.message || "Unknown error";
      this._loading = false;
      this._mount();
    }
  }

  _updateSessionBadge() {
    // Update the session panel header with a changes badge if there are
    // uncommitted changes and the session panel is open for the same story.
    const sessionPanel = window.DW._sessionPanel;
    if (!sessionPanel || !sessionPanel.isOpen()) return;

    const header = document.querySelector(".session-header .session-title-row");
    if (!header) return;

    // Remove any existing diff badge
    const existing = header.querySelector(".diff-changes-badge");
    if (existing) existing.remove();

    if (this._files.length > 0) {
      const badge = document.createElement("dw-badge");
      badge.setAttribute("variant", "in-progress");
      badge.setAttribute("count", `${this._files.length} changes`);
      badge.className = "diff-changes-badge diff-changes-clickable";
      badge.title = "Open diff panel";
      badge.addEventListener("click", () => {
        if (window.DW._layout) window.DW._layout.open("diff");
      });
      header.appendChild(badge);
    }
  }

  _startPoll() {
    this._stopPoll();
    if (SNAPSHOT_MODE) return;
    this._pollTimer = setTimeout(async () => {
      if (!this._slug) return;
      try {
        const res = await api(
          `/api/diff?project=${encodeURIComponent(this._slug)}`
        );
        const newFiles = res.data.files || [];
        const changed = JSON.stringify(newFiles) !== JSON.stringify(this._files);
        if (changed) {
          this._files = newFiles;
          this._mount();
          this._updateSessionBadge();
        }
      } catch (_err) {
        // Polling failure is silent; retry next interval
      }
      this._startPoll();
    }, 10000);
  }

  _stopPoll() {
    if (this._pollTimer) {
      clearTimeout(this._pollTimer);
      this._pollTimer = null;
    }
  }
}

/* ── session panel integration ────────────────────────────────────── */

/**
 * Called from the session panel after it loads a story to check for
 * uncommitted changes and show a badge. Opens the diff panel in the
 * layout when clicked.
 */
function checkDiffForStory(storyId, slug) {
  if (!window.DW._diffPanel) {
    window.DW._diffPanel = new DiffPanel();
  }
  const panel = window.DW._diffPanel;

  // Fetch the diff count asynchronously and update the session badge
  api(`/api/diff?project=${encodeURIComponent(slug || selectedProject)}`)
    .then(function (res) {
      const files = res.data.files || [];
      const header = document.querySelector(".session-header .session-title-row");
      if (!header) return;

      // Remove any existing diff badge
      const existing = header.querySelector(".diff-changes-badge");
      if (existing) existing.remove();

      if (files.length > 0) {
        const badge = document.createElement("dw-badge");
        badge.setAttribute("variant", "in-progress");
        badge.setAttribute("count", `${files.length} changes`);
        badge.className = "diff-changes-badge diff-changes-clickable";
        badge.title = "Open diff panel";
        badge.addEventListener("click", function () {
          if (!panel.isOpen()) {
            panel.open(storyId, slug || selectedProject);
          }
          if (window.DW._layout) window.DW._layout.open("diff");
        });
        header.appendChild(badge);
      }
    })
    .catch(function () {
      // Silently ignore diff check failures
    });
}

window.DW.DiffPanel = DiffPanel;
window.DW.checkDiffForStory = checkDiffForStory;
