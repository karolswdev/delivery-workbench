"use strict";

/**
 * InsightsPanel — local analytics dashboard for the Delivery Workbench.
 *
 * Shows stories shipped, evidence captures, commit activity, phase progress
 * bars, and a compact activity timeline. All data is derived from local git
 * history and roadmap files — no external network calls.
 */

(function () {
  if (!window.DW) window.DW = {};

  const RANGES = [
    { key: "7d", label: "7 days", days: 7 },
    { key: "30d", label: "30 days", days: 30 },
    { key: "all", label: "All time", days: null },
  ];

  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function daysBetween(dateStr) {
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return Infinity;
    var now = new Date();
    return Math.floor((now - d) / 86400000);
  }

  function InsightsPanel() {
    this._el = null;
    this._slug = "";
    this._range = "all";
    this._data = null;
    this._loading = false;
    this._error = "";
  }

  InsightsPanel.prototype.open = function open(slug) {
    this._slug = slug || "";
    this._data = null;
    this._error = "";
    this._loading = true;
    this.render();
    this._fetch();
  };

  InsightsPanel.prototype.close = function close() {
    if (this._el && this._el.parentNode) {
      this._el.parentNode.removeChild(this._el);
    }
    this._el = null;
    this._data = null;
  };

  InsightsPanel.prototype._fetch = function _fetch() {
    var self = this;
    var slug = this._slug;
    fetch("/api/insights?project=" + encodeURIComponent(slug), { cache: "no-store" })
      .then(function (res) { return res.json(); })
      .then(function (body) {
        if (self._slug !== slug) return; // stale
        if (!body.ok) {
          self._error = (body.issues && body.issues[0]) || "Failed to load insights";
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

  InsightsPanel.prototype._filterCommits = function _filterCommits(commits, days) {
    if (!days) return commits;
    return commits.filter(function (c) { return daysBetween(c.date) <= days; });
  };

  InsightsPanel.prototype._filterTimeline = function _filterTimeline(timeline, days) {
    if (!days) return timeline;
    return timeline.filter(function (t) { return daysBetween(t.timestamp) <= days; });
  };

  InsightsPanel.prototype._totalCommits = function _totalCommits(commits) {
    var sum = 0;
    for (var i = 0; i < commits.length; i++) sum += commits[i].count;
    return sum;
  };

  InsightsPanel.prototype._totalDone = function _totalDone(phases) {
    var sum = 0;
    for (var i = 0; i < phases.length; i++) sum += phases[i].done;
    return sum;
  };

  InsightsPanel.prototype._totalStories = function _totalStories(phases) {
    var sum = 0;
    for (var i = 0; i < phases.length; i++) sum += phases[i].total;
    return sum;
  };

  InsightsPanel.prototype.render = function render() {
    if (!this._el) {
      this._el = document.createElement("div");
      this._el.className = "insights-panel";
      this._el.setAttribute("role", "region");
      this._el.setAttribute("aria-label", "Project insights");
    }

    if (this._loading) {
      this._el.innerHTML =
        '<div class="insights-header">' +
          '<h2>Insights</h2>' +
          '<button class="insights-close" aria-label="Close insights" type="button">&times;</button>' +
        '</div>' +
        '<dw-skeleton lines="5"></dw-skeleton>';
      this._bindClose();
      return this._el;
    }

    if (this._error) {
      this._el.innerHTML =
        '<div class="insights-header">' +
          '<h2>Insights</h2>' +
          '<button class="insights-close" aria-label="Close insights" type="button">&times;</button>' +
        '</div>' +
        '<div class="state error">' + esc(this._error) + '</div>';
      this._bindClose();
      return this._el;
    }

    if (!this._data) {
      return this._el;
    }

    var data = this._data;
    var rangeDef = RANGES.find(function (r) { return r.key === this._range; }.bind(this)) || RANGES[2];
    var commits = this._filterCommits(data.commits || [], rangeDef.days);
    var timeline = this._filterTimeline(data.timeline || [], rangeDef.days);
    var totalCommits = this._totalCommits(commits);
    var totalDone = this._totalDone(data.stories_by_phase || []);
    var totalStories = this._totalStories(data.stories_by_phase || []);

    var html = '';

    // Header
    html += '<div class="insights-header">';
    html += '<h2>Insights <span class="insights-project">' + esc(data.project) + '</span></h2>';
    html += '<button class="insights-close" aria-label="Close insights" type="button">&times;</button>';
    html += '</div>';

    // Range filter
    html += '<div class="insights-filters" role="group" aria-label="Time range">';
    for (var i = 0; i < RANGES.length; i++) {
      var r = RANGES[i];
      var active = r.key === this._range;
      html += '<button class="insights-range-btn' + (active ? ' active' : '') + '"';
      html += ' data-range="' + r.key + '"';
      html += active ? ' aria-pressed="true"' : ' aria-pressed="false"';
      html += ' type="button">' + esc(r.label) + '</button>';
    }
    html += '</div>';

    // Summary strip
    html += '<div class="insights-summary">';
    html += this._statCard("Stories shipped", totalDone + " / " + totalStories, "done");
    html += this._statCard("Evidence captures", String(data.evidence_count || 0), "evidence");
    html += this._statCard("Commits", String(totalCommits), "commits");
    html += '</div>';

    // Phase progress bars
    html += '<dw-card class="insights-section">';
    html += '<div slot="header"><strong>Phase progress</strong></div>';
    html += '<div class="insights-phase-bars">';
    var phases = data.stories_by_phase || [];
    for (var j = 0; j < phases.length; j++) {
      var p = phases[j];
      var pct = p.total > 0 ? Math.round((p.done / p.total) * 100) : 0;
      var ipPct = p.total > 0 ? Math.round((p.in_progress / p.total) * 100) : 0;
      html += '<div class="insights-phase-row">';
      html += '<span class="insights-phase-label">Phase ' + esc(p.phase) + '</span>';
      html += '<div class="insights-bar-track" title="' + p.done + ' done, ' + p.in_progress + ' in-progress of ' + p.total + '">';
      html += '<div class="insights-bar-done" style="width:' + pct + '%"></div>';
      html += '<div class="insights-bar-ip" style="width:' + ipPct + '%"></div>';
      html += '</div>';
      html += '<span class="insights-phase-count">' + p.done + '/' + p.total + '</span>';
      html += '</div>';
    }
    html += '</div>';
    html += '</dw-card>';

    // Commit activity chart
    if (commits.length > 0) {
      html += '<dw-card class="insights-section">';
      html += '<div slot="header"><strong>Commit activity</strong></div>';
      html += '<div class="insights-commit-chart">';
      var maxCount = 1;
      for (var k = 0; k < commits.length; k++) {
        if (commits[k].count > maxCount) maxCount = commits[k].count;
      }
      // Show last 30 bars max
      var shown = commits.slice(-30);
      for (var m = 0; m < shown.length; m++) {
        var c = shown[m];
        var barPct = Math.round((c.count / maxCount) * 100);
        html += '<div class="insights-commit-bar-wrap" title="' + esc(c.date) + ': ' + c.count + ' commits">';
        html += '<div class="insights-commit-bar" style="height:' + barPct + '%"></div>';
        html += '</div>';
      }
      html += '</div>';
      html += '<div class="insights-commit-legend">';
      if (shown.length > 0) {
        html += '<span>' + esc(shown[0].date) + '</span>';
        html += '<span>' + esc(shown[shown.length - 1].date) + '</span>';
      }
      html += '</div>';
      html += '</dw-card>';
    }

    // Timeline
    if (timeline.length > 0) {
      html += '<dw-card class="insights-section">';
      html += '<div slot="header"><strong>Activity timeline</strong></div>';
      html += '<div class="insights-timeline">';
      for (var n = 0; n < timeline.length; n++) {
        var ev = timeline[n];
        html += '<div class="insights-event">';
        html += '<span class="insights-event-time">' + esc((ev.timestamp || "").slice(0, 16).replace("T", " ")) + '</span>';
        html += '<span class="insights-event-type badge">' + esc(ev.event) + '</span>';
        html += '<span class="insights-event-detail">' + esc(ev.detail) + '</span>';
        html += '</div>';
      }
      html += '</div>';
      html += '</dw-card>';
    }

    this._el.innerHTML = html;
    this._bindClose();
    this._bindRangeButtons();
    return this._el;
  };

  InsightsPanel.prototype._statCard = function _statCard(label, value, cls) {
    return '<dw-card class="insights-stat ' + esc(cls) + '">' +
      '<div class="insights-stat-value">' + esc(value) + '</div>' +
      '<div class="insights-stat-label">' + esc(label) + '</div>' +
      '</dw-card>';
  };

  InsightsPanel.prototype._bindClose = function _bindClose() {
    var self = this;
    var btn = this._el.querySelector(".insights-close");
    if (btn) {
      btn.addEventListener("click", function () { self.close(); });
    }
  };

  InsightsPanel.prototype._bindRangeButtons = function _bindRangeButtons() {
    var self = this;
    var buttons = this._el.querySelectorAll(".insights-range-btn");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", function () {
        self._range = this.getAttribute("data-range");
        self.render();
      });
    }
  };

  window.DW.InsightsPanel = InsightsPanel;
})();
