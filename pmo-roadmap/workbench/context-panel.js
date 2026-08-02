"use strict";

/**
 * ContextPanel — revisioned project context viewer and editor (WLA-34-09).
 *
 * Shows the current project context with revision number and hash,
 * provides a text editor for drafting new context, accept/reject
 * controls for pending drafts, and a revision history viewer.
 */

(function () {
  if (!window.DW) window.DW = {};

  function esc(s) {
    return String(s != null ? s : "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function truncHash(h) {
    if (!h) return "";
    var prefix = h.indexOf(":") >= 0 ? h.slice(h.indexOf(":") + 1) : h;
    return prefix.slice(0, 12);
  }

  function ContextPanel() {
    this._el = null;
    this._slug = "";
    this._current = null;
    this._history = null;
    this._loading = false;
    this._error = "";
    this._tab = "current"; // current | draft | history
    this._draftContent = "";
    this._draftPending = null; // result from POST /draft
    this._accepting = false;
    this._drafting = false;
  }

  ContextPanel.prototype.open = function open(slug) {
    this._slug = slug || "";
    this._current = null;
    this._history = null;
    this._error = "";
    this._loading = true;
    this._tab = "current";
    this._draftContent = "";
    this._draftPending = null;
    this._accepting = false;
    this._drafting = false;
    this.render();
    this._fetchAll();
  };

  ContextPanel.prototype.close = function close() {
    if (this._el && this._el.parentNode) {
      this._el.parentNode.removeChild(this._el);
    }
    this._el = null;
    this._current = null;
    this._history = null;
  };

  ContextPanel.prototype._fetchAll = function _fetchAll() {
    var self = this;
    var slug = this._slug;
    Promise.all([
      fetch("/api/context/" + encodeURIComponent(slug) + "/current", { cache: "no-store" }).then(function (r) { return r.json(); }),
      fetch("/api/context/" + encodeURIComponent(slug) + "/history", { cache: "no-store" }).then(function (r) { return r.json(); }),
    ])
      .then(function (results) {
        if (self._slug !== slug) return;
        if (!results[0].ok) {
          self._error = (results[0].issues && results[0].issues[0]) || "Failed to load context";
          self._loading = false;
          self.render();
          return;
        }
        self._current = results[0].data;
        self._history = results[1].ok ? results[1].data : null;
        self._loading = false;
        self.render();
      })
      .catch(function (err) {
        self._error = err.message || "Network error";
        self._loading = false;
        self.render();
      });
  };

  ContextPanel.prototype._submitDraft = function _submitDraft() {
    var self = this;
    var slug = this._slug;
    var content = this._draftContent;
    if (!content.trim()) return;
    this._drafting = true;
    this.render();
    fetch("/api/context/" + encodeURIComponent(slug) + "/draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: content }),
    })
      .then(function (r) { return r.json(); })
      .then(function (body) {
        if (self._slug !== slug) return;
        self._drafting = false;
        if (!body.ok) {
          self._error = (body.issues && body.issues[0]) || "Draft failed";
          self.render();
          return;
        }
        self._draftPending = body.data;
        self._error = "";
        self.render();
      })
      .catch(function (err) {
        self._drafting = false;
        self._error = err.message || "Network error";
        self.render();
      });
  };

  ContextPanel.prototype._acceptDraft = function _acceptDraft() {
    var self = this;
    var slug = this._slug;
    var pending = this._draftPending;
    if (!pending) return;
    this._accepting = true;
    this.render();
    fetch("/api/context/" + encodeURIComponent(slug) + "/accept", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        revision: pending.revision,
        fingerprint: pending.fingerprint || "",
      }),
    })
      .then(function (r) { return r.json(); })
      .then(function (body) {
        if (self._slug !== slug) return;
        self._accepting = false;
        if (!body.ok) {
          self._error = (body.issues && body.issues[0]) || "Accept failed";
          self.render();
          return;
        }
        // Refresh everything
        self._draftPending = null;
        self._draftContent = "";
        self._tab = "current";
        self._fetchAll();
      })
      .catch(function (err) {
        self._accepting = false;
        self._error = err.message || "Network error";
        self.render();
      });
  };

  ContextPanel.prototype._rejectDraft = function _rejectDraft() {
    this._draftPending = null;
    this._draftContent = "";
    this.render();
  };

  ContextPanel.prototype.render = function render() {
    if (!this._el) {
      this._el = document.createElement("div");
      this._el.className = "context-panel";
      this._el.setAttribute("role", "region");
      this._el.setAttribute("aria-label", "Project context");
    }

    if (this._loading) {
      this._el.innerHTML =
        '<div class="context-header">' +
          '<h2>Project context</h2>' +
          '<button class="context-close" aria-label="Close context panel" type="button">&times;</button>' +
        '</div>' +
        '<dw-skeleton lines="5"></dw-skeleton>';
      this._bindClose();
      return this._el;
    }

    if (this._error) {
      this._el.innerHTML =
        '<div class="context-header">' +
          '<h2>Project context</h2>' +
          '<button class="context-close" aria-label="Close context panel" type="button">&times;</button>' +
        '</div>' +
        '<div class="state error">' + esc(this._error) + '</div>';
      this._bindClose();
      return this._el;
    }

    var html = '';

    // Header
    html += '<div class="context-header">';
    html += '<h2>Project context <span class="context-project">' + esc(this._slug) + '</span></h2>';
    html += '<button class="context-close" aria-label="Close context panel" type="button">&times;</button>';
    html += '</div>';

    // Tabs
    html += '<div class="context-tabs" role="tablist">';
    var tabs = [
      { key: "current", label: "Current" },
      { key: "draft", label: "Draft" },
      { key: "history", label: "History" },
    ];
    for (var i = 0; i < tabs.length; i++) {
      var t = tabs[i];
      var active = t.key === this._tab;
      html += '<button class="context-tab' + (active ? ' active' : '') + '"';
      html += ' data-tab="' + t.key + '" role="tab"';
      html += ' aria-selected="' + (active ? 'true' : 'false') + '"';
      html += ' type="button">' + esc(t.label) + '</button>';
    }
    html += '</div>';

    // Tab content
    if (this._tab === "current") {
      html += this._renderCurrent();
    } else if (this._tab === "draft") {
      html += this._renderDraft();
    } else if (this._tab === "history") {
      html += this._renderHistory();
    }

    this._el.innerHTML = html;
    this._bindClose();
    this._bindTabs();
    this._bindDraftActions();
    return this._el;
  };

  ContextPanel.prototype._renderCurrent = function _renderCurrent() {
    var cur = this._current;
    if (!cur || !cur.exists) {
      return '<dw-card class="context-section">' +
        '<div class="context-empty">No context has been set for this project yet. ' +
        'Use the Draft tab to create one.</div>' +
        '</dw-card>';
    }

    var html = '<dw-card class="context-section">';
    html += '<div class="context-meta">';
    html += '<span class="context-meta-item"><strong>Revision:</strong> ' + esc(cur.revision) + '</span>';
    html += '<span class="context-meta-item"><strong>Hash:</strong> <code>' + esc(truncHash(cur.content_hash)) + '</code></span>';
    html += '<span class="context-meta-item"><strong>Author:</strong> ' + esc(cur.author) + '</span>';
    html += '<span class="context-meta-item"><strong>Accepted:</strong> ' + esc((cur.accepted_at || "").replace("T", " ").replace("Z", "")) + '</span>';
    html += '</div>';
    html += '<div class="context-content"><pre class="context-markdown">' + esc(cur.content) + '</pre></div>';
    html += '</dw-card>';
    return html;
  };

  ContextPanel.prototype._renderDraft = function _renderDraft() {
    var html = '';

    if (this._draftPending) {
      // Show pending draft with accept/reject
      html += '<dw-card class="context-section context-draft-pending">';
      html += '<div class="context-draft-banner">Draft revision ' + esc(this._draftPending.revision) + ' is pending review</div>';
      html += '<div class="context-meta">';
      html += '<span class="context-meta-item"><strong>Hash:</strong> <code>' + esc(truncHash(this._draftPending.content_hash)) + '</code></span>';
      html += '<span class="context-meta-item"><strong>Drafted:</strong> ' + esc((this._draftPending.drafted_at || "").replace("T", " ").replace("Z", "")) + '</span>';
      html += '</div>';
      html += '<div class="context-content"><pre class="context-markdown">' + esc(this._draftContent) + '</pre></div>';
      html += '<div class="context-draft-actions">';
      html += '<button class="context-accept-btn" type="button"' + (this._accepting ? ' disabled' : '') + '>';
      html += this._accepting ? 'Accepting...' : 'Accept draft';
      html += '</button>';
      html += '<button class="context-reject-btn" type="button"' + (this._accepting ? ' disabled' : '') + '>Reject</button>';
      html += '</div>';
      html += '</dw-card>';
      return html;
    }

    // Editor
    html += '<dw-card class="context-section">';
    html += '<div class="context-draft-label ops-label">Draft new context (Markdown)</div>';
    html += '<textarea class="context-editor" rows="12" placeholder="Write project context here...">';
    html += esc(this._draftContent);
    html += '</textarea>';
    html += '<div class="context-draft-actions">';
    html += '<button class="context-submit-btn" type="button"' + (this._drafting ? ' disabled' : '') + '>';
    html += this._drafting ? 'Submitting...' : 'Submit draft';
    html += '</button>';
    html += '</div>';
    html += '</dw-card>';
    return html;
  };

  ContextPanel.prototype._renderHistory = function _renderHistory() {
    var hist = this._history;
    if (!hist || (hist.revisions.length === 0 && hist.drafts.length === 0)) {
      return '<dw-card class="context-section">' +
        '<div class="context-empty">No revision history yet.</div>' +
        '</dw-card>';
    }

    var html = '';

    // Accepted revisions
    if (hist.revisions.length > 0) {
      html += '<dw-card class="context-section">';
      html += '<div slot="header"><strong>Accepted revisions</strong></div>';
      html += '<div class="context-history-list">';
      for (var i = hist.revisions.length - 1; i >= 0; i--) {
        var rev = hist.revisions[i];
        html += '<div class="context-history-item' + (rev.is_current ? ' current' : '') + '">';
        html += '<span class="context-rev-num">r' + esc(rev.revision) + '</span>';
        html += '<code class="context-rev-hash">' + esc(truncHash(rev.content_hash)) + '</code>';
        if (rev.is_current) {
          html += '<span class="badge context-current-badge">current</span>';
        }
        if (rev.content_preview) {
          html += '<span class="context-rev-preview">' + esc(rev.content_preview) + '</span>';
        }
        html += '</div>';
      }
      html += '</div>';
      html += '</dw-card>';
    }

    // Pending drafts
    var pendingDrafts = hist.drafts.filter(function (d) { return !d.accepted; });
    if (pendingDrafts.length > 0) {
      html += '<dw-card class="context-section">';
      html += '<div slot="header"><strong>Pending drafts</strong></div>';
      html += '<div class="context-history-list">';
      for (var j = 0; j < pendingDrafts.length; j++) {
        var d = pendingDrafts[j];
        html += '<div class="context-history-item draft">';
        html += '<span class="context-rev-num">draft-' + esc(d.revision) + '</span>';
        html += '<code class="context-rev-hash">' + esc(truncHash(d.content_hash)) + '</code>';
        html += '<span class="context-draft-time">' + esc((d.drafted_at || "").replace("T", " ").replace("Z", "")) + '</span>';
        html += '</div>';
      }
      html += '</div>';
      html += '</dw-card>';
    }

    return html;
  };

  ContextPanel.prototype._bindClose = function _bindClose() {
    var self = this;
    var btn = this._el.querySelector(".context-close");
    if (btn) {
      btn.addEventListener("click", function () { self.close(); });
    }
  };

  ContextPanel.prototype._bindTabs = function _bindTabs() {
    var self = this;
    var buttons = this._el.querySelectorAll(".context-tab");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", function () {
        self._tab = this.getAttribute("data-tab");
        self.render();
      });
    }
  };

  ContextPanel.prototype._bindDraftActions = function _bindDraftActions() {
    var self = this;

    // Draft editor textarea sync
    var editor = this._el.querySelector(".context-editor");
    if (editor) {
      editor.addEventListener("input", function () {
        self._draftContent = this.value;
      });
    }

    // Submit draft
    var submitBtn = this._el.querySelector(".context-submit-btn");
    if (submitBtn) {
      submitBtn.addEventListener("click", function () {
        self._submitDraft();
      });
    }

    // Accept
    var acceptBtn = this._el.querySelector(".context-accept-btn");
    if (acceptBtn) {
      acceptBtn.addEventListener("click", function () {
        self._acceptDraft();
      });
    }

    // Reject
    var rejectBtn = this._el.querySelector(".context-reject-btn");
    if (rejectBtn) {
      rejectBtn.addEventListener("click", function () {
        self._rejectDraft();
      });
    }
  };

  window.DW.ContextPanel = ContextPanel;
})();
