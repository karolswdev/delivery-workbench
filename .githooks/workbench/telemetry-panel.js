"use strict";

/**
 * TelemetryPanel — per-run session telemetry for the Delivery Workbench.
 *
 * Shows per-turn metrics derived from the run ledger: cost, tokens,
 * cache granularity, duration, and a cost-over-time bar chart.
 * All data is read-only from GET /api/telemetry?run=<run_id>.
 */

(function () {
  if (!window.DW) window.DW = {};

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /** Format microunits as $X.XX; null/undefined renders as dash. */
  function formatCost(microunits) {
    if (microunits == null) return "—";
    return "$" + (microunits / 1000000).toFixed(2);
  }

  /** Format token count; null/undefined renders as dash. */
  function formatTokens(n) {
    if (n == null) return "—";
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  /** Format seconds as Xm Ys or Xs; null renders as dash. */
  function formatDuration(seconds) {
    if (seconds == null) return "—";
    if (seconds < 60) return seconds + "s";
    var m = Math.floor(seconds / 60);
    var s = seconds % 60;
    return m + "m " + s + "s";
  }

  /** Duration between two ISO timestamps in seconds; null if unavailable. */
  function turnDuration(started, ended) {
    if (!started || !ended) return null;
    try {
      var t0 = new Date(started).getTime();
      var t1 = new Date(ended).getTime();
      if (isNaN(t0) || isNaN(t1)) return null;
      var sec = Math.max(0, Math.round((t1 - t0) / 1000));
      return sec;
    } catch (e) {
      return null;
    }
  }

  /** CSS class for state color coding. */
  function stateClass(state) {
    if (!state) return "";
    if (state === "succeeded") return "telem-state-ok";
    if (state === "failed") return "telem-state-fail";
    if (state === "cancelled") return "telem-state-cancel";
    return "";
  }

  function TelemetryPanel() {
    this._el = null;
    this._runId = "";
    this._data = null;
    this._loading = false;
    this._error = "";
  }

  TelemetryPanel.prototype.open = function open(runId) {
    this._runId = runId || "";
    this._data = null;
    this._error = "";
    this._loading = true;
    this.render();
    this._fetch();
  };

  TelemetryPanel.prototype.close = function close() {
    if (this._el && this._el.parentNode) {
      this._el.parentNode.removeChild(this._el);
    }
    this._el = null;
    this._data = null;
  };

  TelemetryPanel.prototype._fetch = function _fetch() {
    var self = this;
    var runId = this._runId;
    fetch("/api/telemetry?run=" + encodeURIComponent(runId), { cache: "no-store" })
      .then(function (res) { return res.json(); })
      .then(function (body) {
        if (self._runId !== runId) return; // stale
        if (!body.ok) {
          self._error = (body.issues && body.issues[0]) || "Failed to load telemetry";
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

  TelemetryPanel.prototype.render = function render() {
    if (!this._el) {
      this._el = document.createElement("div");
      this._el.className = "telemetry-panel";
      this._el.setAttribute("role", "region");
      this._el.setAttribute("aria-label", "Session telemetry");
    }

    // Loading state
    if (this._loading) {
      this._el.innerHTML =
        '<div class="telem-header">' +
          '<h2>Session Telemetry</h2>' +
          '<button class="telem-close" aria-label="Close telemetry" type="button">&times;</button>' +
        '</div>' +
        '<dw-skeleton lines="5"></dw-skeleton>';
      this._bindClose();
      return this._el;
    }

    // Error state
    if (this._error) {
      this._el.innerHTML =
        '<div class="telem-header">' +
          '<h2>Session Telemetry</h2>' +
          '<button class="telem-close" aria-label="Close telemetry" type="button">&times;</button>' +
        '</div>' +
        '<div class="state error">' + esc(this._error) + '</div>';
      this._bindClose();
      return this._el;
    }

    if (!this._data) {
      return this._el;
    }

    var data = this._data;
    var turns = data.turns || [];
    var summary = data.summary || {};
    var html = "";

    // Header
    html += '<div class="telem-header">';
    html += '<h2>Session Telemetry <span class="telem-run-id">' + esc(this._runId) + '</span></h2>';
    html += '<button class="telem-close" aria-label="Close telemetry" type="button">&times;</button>';
    html += '</div>';

    // Empty state for runs with no telemetry
    if (turns.length === 0) {
      html += '<div class="state empty">No telemetry available</div>';
      this._el.innerHTML = html;
      this._bindClose();
      return this._el;
    }

    // Summary cards
    html += '<div class="telem-summary">';
    html += this._statCard("Total Cost", formatCost(summary.total_cost_microunits), "cost");
    html += this._statCard("Total Tokens", formatTokens(summary.total_input_tokens), "tokens");
    html += this._statCard("Turns", summary.total_turns != null ? String(summary.total_turns) : "—", "turns");
    html += this._statCard("Duration", formatDuration(summary.duration_seconds), "duration");
    html += this._statCard("Models", (summary.models_used || []).join(", ") || "—", "models");
    html += '</div>';

    // Cost-over-time bar chart
    html += this._renderCostChart(turns);

    // Per-turn table
    html += this._renderTable(turns);

    this._el.innerHTML = html;
    this._bindClose();
    return this._el;
  };

  TelemetryPanel.prototype._statCard = function _statCard(label, value, cls) {
    return '<dw-card class="telem-stat ' + esc(cls) + '">' +
      '<div class="telem-stat-value">' + esc(value) + '</div>' +
      '<div class="telem-stat-label">' + esc(label) + '</div>' +
      '</dw-card>';
  };

  TelemetryPanel.prototype._renderCostChart = function _renderCostChart(turns) {
    // Filter turns that have cost data
    var costed = [];
    for (var i = 0; i < turns.length; i++) {
      costed.push({
        index: i + 1,
        cost: turns[i].cost_microunits,
        state: turns[i].state
      });
    }
    if (costed.length === 0) return "";

    var maxCost = 1;
    for (var j = 0; j < costed.length; j++) {
      if (costed[j].cost != null && costed[j].cost > maxCost) maxCost = costed[j].cost;
    }

    var html = '<dw-card class="telem-section">';
    html += '<div slot="header"><strong>Cost per turn</strong></div>';
    html += '<div class="telem-cost-chart">';
    for (var k = 0; k < costed.length; k++) {
      var c = costed[k];
      var barPct = c.cost != null ? Math.round((c.cost / maxCost) * 100) : 0;
      var cls = stateClass(c.state);
      var title = "Turn " + c.index + ": " + formatCost(c.cost);
      html += '<div class="telem-cost-bar-wrap" title="' + esc(title) + '">';
      if (c.cost != null) {
        html += '<div class="telem-cost-bar ' + cls + '" style="height:' + barPct + '%"></div>';
      } else {
        html += '<div class="telem-cost-bar telem-cost-bar-empty" style="height:2px"></div>';
      }
      html += '</div>';
    }
    html += '</div>';
    html += '<div class="telem-cost-legend">';
    html += '<span>Turn 1</span>';
    html += '<span>Turn ' + costed.length + '</span>';
    html += '</div>';
    html += '</dw-card>';
    return html;
  };

  TelemetryPanel.prototype._renderTable = function _renderTable(turns) {
    var html = '<dw-card class="telem-section">';
    html += '<div slot="header"><strong>Turn details</strong></div>';
    html += '<div class="telem-table-wrap">';
    html += '<table class="telem-table">';
    html += '<thead><tr>';
    html += '<th>#</th><th>Node</th><th>Attempt</th><th>Model</th>';
    html += '<th>In</th><th>Out</th><th>Cache R</th><th>Cache W</th>';
    html += '<th>Total</th><th>Cost</th><th>State</th><th>Duration</th>';
    html += '</tr></thead>';
    html += '<tbody>';

    for (var i = 0; i < turns.length; i++) {
      var t = turns[i];
      var cls = stateClass(t.state);
      var dur = turnDuration(t.started_at, t.ended_at);
      html += '<tr class="' + cls + '">';
      html += '<td>' + (i + 1) + '</td>';
      html += '<td class="telem-cell-node">' + esc(t.node_id) + '</td>';
      html += '<td>' + (t.attempt != null ? t.attempt : "—") + '</td>';
      html += '<td>' + esc(t.model || "—") + '</td>';
      html += '<td>' + formatTokens(t.input_tokens) + '</td>';
      html += '<td>' + formatTokens(t.output_tokens) + '</td>';
      html += '<td>' + formatTokens(t.cache_read_tokens) + '</td>';
      html += '<td>' + formatTokens(t.cache_creation_tokens) + '</td>';
      html += '<td>' + formatTokens(t.total_tokens) + '</td>';
      html += '<td>' + formatCost(t.cost_microunits) + '</td>';
      html += '<td><span class="badge ' + cls + '">' + esc(t.state || "—") + '</span></td>';
      html += '<td>' + formatDuration(dur) + '</td>';
      html += '</tr>';
    }

    html += '</tbody></table>';
    html += '</div>';
    html += '</dw-card>';
    return html;
  };

  TelemetryPanel.prototype._bindClose = function _bindClose() {
    var self = this;
    var btn = this._el.querySelector(".telem-close");
    if (btn) {
      btn.addEventListener("click", function () { self.close(); });
    }
  };

  window.DW.TelemetryPanel = TelemetryPanel;
})();
