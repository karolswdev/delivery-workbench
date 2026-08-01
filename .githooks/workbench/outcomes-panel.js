"use strict";

/**
 * Session-to-outcome links panel (WLA-34-07).
 *
 * Shows which sessions produced which artifacts, evidence captures,
 * check results, and story transitions for a given orchestration run.
 * Read-only: derives from existing ledger data via /api/session-outcomes.
 */

window.DW = window.DW || {};

(function () {
  function esc(text) {
    var d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
  }

  function formatCost(microunits) {
    if (microunits === null || microunits === undefined) return "n/a";
    return "$" + (microunits / 1000000).toFixed(2);
  }

  function formatDuration(seconds) {
    if (seconds === null || seconds === undefined) return "n/a";
    if (seconds < 60) return seconds + "s";
    var m = Math.floor(seconds / 60);
    var s = seconds % 60;
    return m + "m " + s + "s";
  }

  function stateToStatus(state) {
    if (state === "succeeded") return "done";
    if (state === "failed" || state === "lost" || state === "refused") return "blocked";
    if (state === "cancelled") return "on-hold";
    return "in-progress";
  }

  /**
   * OutcomesPanel
   *
   * Usage:
   *   var panel = new OutcomesPanel();
   *   panel.open(runId);
   *   panel.close();
   *   panel.render();
   */
  function OutcomesPanel() {
    this._visible = false;
    this._container = null;
    this._contentEl = null;
    this._runId = null;
    this._sessions = [];
    this._summary = null;
    this._loading = true;
    this._error = "";
  }

  OutcomesPanel.prototype.open = function (runId) {
    this._runId = runId || null;
    this._visible = true;
    this._loading = true;
    this._error = "";
    this._sessions = [];
    this._summary = null;
    this.render();
    if (this._container) {
      this._container.style.display = "";
      this._container.removeAttribute("collapsed");
    }
    if (this._runId) {
      this._fetch();
    } else {
      this._loading = false;
      this._error = "No run ID provided";
      this._renderContent();
    }
  };

  OutcomesPanel.prototype.close = function () {
    this._visible = false;
    if (this._container) {
      this._container.style.display = "none";
    }
  };

  OutcomesPanel.prototype.render = function () {
    if (!this._container) {
      var panel = document.createElement("dw-panel");
      panel.setAttribute("title", "Session Outcomes");
      panel.setAttribute("collapsible", "");
      panel.classList.add("outcomes-panel");

      var content = document.createElement("div");
      content.className = "outcomes-content";
      panel.appendChild(content);
      this._contentEl = content;

      var appEl = document.getElementById("app");
      if (appEl) {
        appEl.parentNode.insertBefore(panel, appEl.nextSibling);
      } else {
        document.body.appendChild(panel);
      }

      this._container = panel;
      if (!this._visible) {
        panel.style.display = "none";
      }
    }

    this._renderContent();
  };

  OutcomesPanel.prototype._renderContent = function () {
    if (!this._contentEl) return;

    if (this._loading) {
      this._contentEl.innerHTML =
        '<dw-skeleton lines="4" variant="text"></dw-skeleton>';
      return;
    }

    if (this._error) {
      this._contentEl.innerHTML =
        '<div class="outcomes-error">' + esc(this._error) + "</div>";
      return;
    }

    if (this._sessions.length === 0) {
      this._contentEl.innerHTML =
        '<div class="outcomes-empty">' +
        "<p>No outcomes recorded.</p>" +
        "<p>Session outcomes appear once an orchestration run " +
        "has claimed and released nodes.</p>" +
        "</div>";
      return;
    }

    var html = this._renderSummary() + this._renderTable();
    this._contentEl.innerHTML = html;
  };

  OutcomesPanel.prototype._renderSummary = function () {
    var s = this._summary || {};
    var sessionCount = s.session_count || 0;
    var artifactCount = s.artifact_count || 0;
    var evidenceCount = s.evidence_count || 0;
    var cost = formatCost(s.total_cost_microunits);

    return (
      '<div class="outcomes-summary">' +
      '<span class="outcomes-stat">' +
      '<strong>' + sessionCount + "</strong> sessions" +
      "</span>" +
      '<span class="outcomes-stat">' +
      '<strong>' + artifactCount + "</strong> artifacts" +
      "</span>" +
      '<span class="outcomes-stat">' +
      '<strong>' + evidenceCount + "</strong> evidence captures" +
      "</span>" +
      '<span class="outcomes-stat">' +
      '<strong>' + esc(cost) + "</strong> total cost" +
      "</span>" +
      "</div>"
    );
  };

  OutcomesPanel.prototype._renderTable = function () {
    var html = '<ul class="outcomes-list">';
    for (var i = 0; i < this._sessions.length; i++) {
      html += this._renderSession(this._sessions[i]);
    }
    html += "</ul>";
    return html;
  };

  OutcomesPanel.prototype._renderSession = function (session) {
    var pillStatus = stateToStatus(session.state);
    var produced = session.produced || {};
    var artifacts = produced.artifacts || [];
    var evidence = produced.evidence_captures || [];
    var checks = produced.check_results || [];
    var transitions = produced.story_transitions || [];

    // Determine color class: evidence with exit 0 = green, failed = red
    var hasAcceptedEvidence = evidence.some(function (e) {
      return e.exit_code === 0;
    });
    var colorClass = "outcomes-session-neutral";
    if (session.state === "succeeded" && hasAcceptedEvidence) {
      colorClass = "outcomes-session-green";
    } else if (session.state === "failed" || session.state === "lost") {
      colorClass = "outcomes-session-red";
    } else if (session.state === "succeeded") {
      colorClass = "outcomes-session-green";
    }

    var sessionLabel = session.session_id
      ? esc(session.session_id)
      : '<span class="outcomes-no-session">(no session id)</span>';

    var detailHtml = this._renderProducedDetail(produced);

    var costStr = formatCost(session.cost_microunits);
    var durationStr = formatDuration(session.duration_seconds);

    var metaHtml =
      '<span class="outcomes-meta-item">' + esc(costStr) + "</span>" +
      '<span class="outcomes-meta-item">' + esc(durationStr) + "</span>";

    if (produced.files_changed !== null && produced.files_changed !== undefined) {
      metaHtml +=
        '<span class="outcomes-meta-item">' +
        esc(String(produced.files_changed)) + " files" +
        "</span>";
    }

    return (
      '<li class="outcomes-session ' + colorClass + '">' +
      '<div class="outcomes-session-header">' +
      '<div class="outcomes-session-info">' +
      '<strong class="outcomes-node">' + esc(session.node_id) + "</strong>" +
      '<dw-status-pill status="' + esc(pillStatus) + '"></dw-status-pill>' +
      '<span class="outcomes-attempt">attempt ' + esc(String(session.attempt)) + "</span>" +
      "</div>" +
      '<div class="outcomes-session-meta">' + metaHtml + "</div>" +
      "</div>" +
      '<div class="outcomes-session-id">' + sessionLabel + "</div>" +
      detailHtml +
      "</li>"
    );
  };

  OutcomesPanel.prototype._renderProducedDetail = function (produced) {
    var artifacts = produced.artifacts || [];
    var evidence = produced.evidence_captures || [];
    var checks = produced.check_results || [];
    var transitions = produced.story_transitions || [];

    var hasDetail = artifacts.length || evidence.length || checks.length || transitions.length;
    if (!hasDetail) return "";

    var inner = "";

    if (artifacts.length) {
      inner += '<div class="outcomes-detail-section">';
      inner += '<div class="outcomes-detail-label">Artifacts</div>';
      inner += '<ul class="outcomes-detail-list">';
      for (var i = 0; i < artifacts.length; i++) {
        var a = artifacts[i];
        inner +=
          "<li>" + esc(a.name || "unnamed") +
          (a.type ? ' <span class="outcomes-tag">' + esc(a.type) + "</span>" : "") +
          (a.hash ? ' <code class="outcomes-hash">' + esc(String(a.hash).slice(0, 16)) + "</code>" : "") +
          "</li>";
      }
      inner += "</ul></div>";
    }

    if (evidence.length) {
      inner += '<div class="outcomes-detail-section">';
      inner += '<div class="outcomes-detail-label">Evidence Captures</div>';
      inner += '<ul class="outcomes-detail-list">';
      for (var j = 0; j < evidence.length; j++) {
        var e = evidence[j];
        var exitClass = e.exit_code === 0 ? "outcomes-exit-pass" : "outcomes-exit-fail";
        inner +=
          "<li>" + esc(e.story_id || "") +
          " <code>" + esc(e.command || "") + "</code>" +
          ' <span class="' + exitClass + '">exit ' + esc(String(e.exit_code)) + "</span>" +
          "</li>";
      }
      inner += "</ul></div>";
    }

    if (checks.length) {
      inner += '<div class="outcomes-detail-section">';
      inner += '<div class="outcomes-detail-label">Check Results</div>';
      inner += '<ul class="outcomes-detail-list">';
      for (var k = 0; k < checks.length; k++) {
        var c = checks[k];
        var checkClass = c.passed ? "outcomes-check-pass" : "outcomes-check-fail";
        inner +=
          '<li class="' + checkClass + '">' +
          esc(c.check || "") +
          (c.passed ? " passed" : " failed") +
          "</li>";
      }
      inner += "</ul></div>";
    }

    if (transitions.length) {
      inner += '<div class="outcomes-detail-section">';
      inner += '<div class="outcomes-detail-label">Story Transitions</div>';
      inner += '<ul class="outcomes-detail-list">';
      for (var t = 0; t < transitions.length; t++) {
        var tr = transitions[t];
        inner +=
          "<li>" + esc(tr.story_id || "") +
          " " + esc(tr.from || "?") + " &rarr; " + esc(tr.to || "?") +
          "</li>";
      }
      inner += "</ul></div>";
    }

    return (
      "<dw-fold>" +
      "<span>Produced details</span>" +
      '<div class="outcomes-produced">' + inner + "</div>" +
      "</dw-fold>"
    );
  };

  OutcomesPanel.prototype._fetch = function () {
    var self = this;
    var url = "/api/session-outcomes?run=" + encodeURIComponent(this._runId);
    fetch(url, { cache: "no-store" })
      .then(function (r) {
        return r.json();
      })
      .then(function (envelope) {
        self._loading = false;
        if (envelope && envelope.ok && envelope.data) {
          self._sessions = envelope.data.sessions || [];
          self._summary = envelope.data.summary || null;
          self._error = "";
        } else {
          self._error =
            (envelope && envelope.data && envelope.data.error) ||
            "Failed to load session outcomes";
          self._sessions = [];
          self._summary = null;
        }
        self._renderContent();
      })
      .catch(function (err) {
        self._loading = false;
        self._error = "Failed to load session outcomes: " + err.message;
        self._sessions = [];
        self._summary = null;
        self._renderContent();
      });
  };

  window.DW.OutcomesPanel = OutcomesPanel;
})();
