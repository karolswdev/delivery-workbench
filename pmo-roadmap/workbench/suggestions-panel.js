"use strict";

/**
 * SuggestionsPanel — agent suggestion inbox for the Delivery Workbench.
 *
 * Displays a tray of task suggestions proposed by agent sessions.  Each
 * suggestion shows provenance (session, run, rationale), priority, and
 * action buttons to accept (creating a roadmap story) or dismiss.
 * Dismissed suggestions are kept for audit, not deleted.
 */

(function () {
  if (!window.DW) window.DW = {};

  function esc(s) {
    return String(s != null ? s : "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function relativeTime(isoStr) {
    if (!isoStr) return "";
    var d = new Date(isoStr);
    if (isNaN(d.getTime())) return isoStr;
    var now = new Date();
    var diffMs = now - d;
    var diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return "just now";
    if (diffMin < 60) return diffMin + "m ago";
    var diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return diffHr + "h ago";
    var diffDay = Math.floor(diffHr / 24);
    return diffDay + "d ago";
  }

  function SuggestionsPanel() {
    this._el = null;
    this._slug = "";
    this._data = null;
    this._loading = false;
    this._error = "";
    this._filter = "suggested"; // default: show pending
  }

  SuggestionsPanel.prototype.open = function open(slug) {
    this._slug = slug || "";
    this._data = null;
    this._error = "";
    this._loading = true;
    this.render();
    this._fetch();
  };

  SuggestionsPanel.prototype.close = function close() {
    if (this._el && this._el.parentNode) {
      this._el.parentNode.removeChild(this._el);
    }
    this._el = null;
    this._data = null;
  };

  SuggestionsPanel.prototype._fetch = function _fetch() {
    var self = this;
    var slug = this._slug;
    var url = "/api/suggestions?project=" + encodeURIComponent(slug);
    fetch(url, { cache: "no-store" })
      .then(function (res) { return res.json(); })
      .then(function (body) {
        if (self._slug !== slug) return;
        if (!body.ok) {
          self._error = (body.issues && body.issues[0]) || "Failed to load suggestions";
          self._loading = false;
          self.render();
          return;
        }
        self._data = body.data;
        self._loading = false;
        self.render();
      })
      .catch(function (err) {
        self._error = err.message || "Network error";
        self._loading = false;
        self.render();
      });
  };

  SuggestionsPanel.prototype._filteredSuggestions = function _filteredSuggestions() {
    if (!this._data || !this._data.suggestions) return [];
    var filter = this._filter;
    if (!filter || filter === "all") return this._data.suggestions;
    return this._data.suggestions.filter(function (s) { return s.state === filter; });
  };

  SuggestionsPanel.prototype.render = function render() {
    if (!this._el) {
      this._el = document.createElement("div");
      this._el.className = "suggestions-panel";
      this._el.setAttribute("role", "region");
      this._el.setAttribute("aria-label", "Agent suggestions");
    }

    if (this._loading) {
      this._el.innerHTML =
        '<div class="suggestions-header">' +
          '<h2>Suggestions</h2>' +
          '<button class="suggestions-close" aria-label="Close suggestions" type="button">&times;</button>' +
        '</div>' +
        '<dw-skeleton lines="4"></dw-skeleton>';
      this._bindClose();
      return this._el;
    }

    if (this._error) {
      this._el.innerHTML =
        '<div class="suggestions-header">' +
          '<h2>Suggestions</h2>' +
          '<button class="suggestions-close" aria-label="Close suggestions" type="button">&times;</button>' +
        '</div>' +
        '<div class="state error">' + esc(this._error) + '</div>';
      this._bindClose();
      return this._el;
    }

    if (!this._data) return this._el;

    var data = this._data;
    var suggestions = this._filteredSuggestions();
    var pendingCount = data.pending_count || 0;
    var html = '';

    // Header
    html += '<div class="suggestions-header">';
    html += '<h2>Suggestions';
    if (pendingCount > 0) {
      html += ' <span class="suggestions-badge">' + pendingCount + '</span>';
    }
    html += ' <span class="suggestions-project">' + esc(data.project) + '</span></h2>';
    html += '<button class="suggestions-close" aria-label="Close suggestions" type="button">&times;</button>';
    html += '</div>';

    // Filter tabs
    html += '<div class="suggestions-filters" role="group" aria-label="Suggestion state filter">';
    var filters = [
      { key: "suggested", label: "Pending" },
      { key: "accepted", label: "Accepted" },
      { key: "dismissed", label: "Dismissed" },
      { key: "all", label: "All" },
    ];
    for (var i = 0; i < filters.length; i++) {
      var f = filters[i];
      var active = f.key === this._filter;
      html += '<button class="suggestions-filter-btn' + (active ? ' active' : '') + '"';
      html += ' data-filter="' + f.key + '"';
      html += active ? ' aria-pressed="true"' : ' aria-pressed="false"';
      html += ' type="button">' + esc(f.label) + '</button>';
    }
    html += '</div>';

    // Suggestion list
    if (suggestions.length === 0) {
      html += '<div class="suggestions-empty">';
      if (this._filter === "suggested") {
        html += 'No pending suggestions. Agents can propose tasks via the <code>suggest_task</code> tool.';
      } else {
        html += 'No ' + esc(this._filter) + ' suggestions.';
      }
      html += '</div>';
    } else {
      html += '<div class="suggestions-list">';
      for (var j = 0; j < suggestions.length; j++) {
        html += this._renderCard(suggestions[j]);
      }
      html += '</div>';
    }

    this._el.innerHTML = html;
    this._bindClose();
    this._bindFilters();
    this._bindActions();
    return this._el;
  };

  SuggestionsPanel.prototype._renderCard = function _renderCard(s) {
    var isPending = s.state === "suggested";
    var html = '<dw-card class="suggestion-card st-' + esc(s.state) + (s.priority === "high" ? ' priority-high' : '') + '">';

    // Card header
    html += '<div slot="header" class="suggestion-card-top">';
    html += '<span class="suggestion-title">' + esc(s.title) + '</span>';
    html += '<dw-status-pill status="' + esc(s.state) + '"></dw-status-pill>';
    if (s.priority === "high") {
      html += ' <span class="suggestion-priority-badge">high</span>';
    }
    html += '</div>';

    // Description
    if (s.description) {
      html += '<div class="suggestion-desc">' + esc(s.description) + '</div>';
    }

    // Rationale
    if (s.rationale) {
      html += '<div class="suggestion-rationale"><strong>Rationale:</strong> ' + esc(s.rationale) + '</div>';
    }

    // Provenance
    html += '<div class="suggestion-provenance">';
    html += '<span class="suggestion-time" title="' + esc(s.proposed_at) + '">' + relativeTime(s.proposed_at) + '</span>';
    if (s.proposed_by_session) {
      html += ' <span class="suggestion-session" title="Session: ' + esc(s.proposed_by_session) + '">session ' + esc(s.proposed_by_session.slice(0, 8)) + '</span>';
    }
    if (s.proposed_by_run) {
      html += ' <span class="suggestion-run" title="Run: ' + esc(s.proposed_by_run) + '">run ' + esc(s.proposed_by_run.slice(0, 8)) + '</span>';
    }
    html += '</div>';

    // Decision info (for accepted/dismissed)
    if (s.decided_at) {
      html += '<div class="suggestion-decision">';
      html += esc(s.state) + ' by ' + esc(s.decided_by || "operator") + ' ' + relativeTime(s.decided_at);
      if (s.materialized_story_id) {
        html += ' &rarr; <code>' + esc(s.materialized_story_id) + '</code>';
      }
      html += '</div>';
    }

    // Action buttons (only for pending)
    if (isPending) {
      html += '<div slot="footer" class="suggestion-actions">';
      html += '<dw-button variant="primary" class="suggestion-accept" data-suggestion-id="' + esc(s.id) + '">Accept</dw-button>';
      html += '<dw-button variant="ghost" class="suggestion-dismiss" data-suggestion-id="' + esc(s.id) + '">Dismiss</dw-button>';
      html += '</div>';
    }

    html += '</dw-card>';
    return html;
  };

  SuggestionsPanel.prototype._bindClose = function _bindClose() {
    var self = this;
    var btn = this._el.querySelector(".suggestions-close");
    if (btn) {
      btn.addEventListener("click", function () { self.close(); });
    }
  };

  SuggestionsPanel.prototype._bindFilters = function _bindFilters() {
    var self = this;
    var buttons = this._el.querySelectorAll(".suggestions-filter-btn");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", function () {
        self._filter = this.getAttribute("data-filter");
        self.render();
      });
    }
  };

  SuggestionsPanel.prototype._bindActions = function _bindActions() {
    var self = this;

    // Accept buttons
    var acceptBtns = this._el.querySelectorAll(".suggestion-accept");
    for (var i = 0; i < acceptBtns.length; i++) {
      acceptBtns[i].addEventListener("click", function () {
        var id = this.getAttribute("data-suggestion-id");
        self._acceptSuggestion(id);
      });
    }

    // Dismiss buttons
    var dismissBtns = this._el.querySelectorAll(".suggestion-dismiss");
    for (var j = 0; j < dismissBtns.length; j++) {
      dismissBtns[j].addEventListener("click", function () {
        var id = this.getAttribute("data-suggestion-id");
        self._dismissSuggestion(id);
      });
    }
  };

  SuggestionsPanel.prototype._acceptSuggestion = function _acceptSuggestion(id) {
    var self = this;
    var slug = this._slug;

    // Find the suggestion to get its title for the story
    var suggestion = null;
    if (this._data && this._data.suggestions) {
      for (var i = 0; i < this._data.suggestions.length; i++) {
        if (this._data.suggestions[i].id === id) {
          suggestion = this._data.suggestions[i];
          break;
        }
      }
    }

    if (!confirm("Accept this suggestion" + (suggestion ? ': "' + suggestion.title + '"' : '') + "? This will mark it as accepted.")) {
      return;
    }

    fetch("/api/suggestions/" + encodeURIComponent(id) + "/accept", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project: slug }),
    })
      .then(function (res) { return res.json(); })
      .then(function (body) {
        if (!body.ok) {
          alert("Accept failed: " + ((body.issues && body.issues[0]) || "unknown error"));
          return;
        }
        self._fetch(); // refresh
      })
      .catch(function (err) {
        alert("Accept failed: " + err.message);
      });
  };

  SuggestionsPanel.prototype._dismissSuggestion = function _dismissSuggestion(id) {
    var self = this;
    var slug = this._slug;

    if (!confirm("Dismiss this suggestion? It will be kept for audit but marked as dismissed.")) {
      return;
    }

    fetch("/api/suggestions/" + encodeURIComponent(id) + "/dismiss", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project: slug }),
    })
      .then(function (res) { return res.json(); })
      .then(function (body) {
        if (!body.ok) {
          alert("Dismiss failed: " + ((body.issues && body.issues[0]) || "unknown error"));
          return;
        }
        self._fetch(); // refresh
      })
      .catch(function (err) {
        alert("Dismiss failed: " + err.message);
      });
  };

  /**
   * Render a small badge showing the pending suggestion count.
   * Suitable for embedding in the board header or nav.
   */
  SuggestionsPanel.prototype.renderBadge = function renderBadge(slug, targetEl) {
    if (!targetEl) return;
    fetch("/api/suggestions?project=" + encodeURIComponent(slug) + "&state=suggested", { cache: "no-store" })
      .then(function (res) { return res.json(); })
      .then(function (body) {
        if (!body.ok || !body.data) return;
        var count = body.data.pending_count || 0;
        if (count > 0) {
          targetEl.innerHTML = '<button class="suggestions-trigger" type="button" aria-label="' + count + ' pending suggestions">' +
            'Suggestions <span class="suggestions-badge">' + count + '</span></button>';
        } else {
          targetEl.innerHTML = '<button class="suggestions-trigger suggestions-trigger-empty" type="button" aria-label="No pending suggestions">Suggestions</button>';
        }
      })
      .catch(function () {
        // Silently fail — badge is non-critical
      });
  };

  window.DW.SuggestionsPanel = SuggestionsPanel;
})();
