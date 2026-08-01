"use strict";

/**
 * Services/processes drawer — tracked process visibility (WLA-33-05).
 *
 * Shows managed dev/test processes started through the terminal panel
 * or dw evidence capture.  Each entry shows name, PID, status, port,
 * exit code, and a collapsible log tail.  Polls /api/services every
 * 5 seconds while the panel is open.
 */

window.DW = window.DW || {};

(function () {
  var POLL_INTERVAL = 5000;
  var STATUS_MAP = {
    running: "in-progress",
    stopped: "done",
    errored: "blocked",
  };

  function esc(text) {
    var d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
  }

  /**
   * ServicesPanel
   *
   * Usage:
   *   var svc = new ServicesPanel();
   *   svc.open();    // show the panel, start polling
   *   svc.close();   // hide the panel, stop polling
   *   svc.render();  // (re-)render into the DOM
   */
  function ServicesPanel() {
    this._visible = false;
    this._container = null;
    this._contentEl = null;
    this._services = [];
    this._loading = true;
    this._error = "";
    this._pollTimer = null;
  }

  ServicesPanel.prototype.open = function () {
    this._visible = true;
    this._loading = true;
    this._error = "";
    this.render();
    if (this._container) {
      this._container.style.display = "";
      this._container.removeAttribute("collapsed");
    }
    this._startPolling();
  };

  ServicesPanel.prototype.close = function () {
    this._visible = false;
    this._stopPolling();
    if (this._container) {
      this._container.style.display = "none";
    }
  };

  ServicesPanel.prototype.render = function () {
    if (!this._container) {
      var panel = document.createElement("dw-panel");
      panel.setAttribute("title", "Services");
      panel.setAttribute("collapsible", "");
      panel.classList.add("services-panel");

      var content = document.createElement("div");
      content.className = "services-content";
      panel.appendChild(content);
      this._contentEl = content;

      // Insert after the app element, like other panels
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

  ServicesPanel.prototype._renderContent = function () {
    if (!this._contentEl) return;

    if (this._loading && this._services.length === 0) {
      this._contentEl.innerHTML =
        '<dw-skeleton lines="3" variant="text"></dw-skeleton>';
      return;
    }

    if (this._error) {
      this._contentEl.innerHTML =
        '<div class="services-error">' + esc(this._error) + "</div>";
      return;
    }

    if (this._services.length === 0) {
      this._contentEl.innerHTML =
        '<div class="services-empty">' +
        "<p>No tracked processes.</p>" +
        "<p>Processes started through the terminal panel or " +
        "<code>dw evidence capture</code> will appear here.</p>" +
        "</div>";
      return;
    }

    var html = '<ul class="services-list">';
    for (var i = 0; i < this._services.length; i++) {
      html += this._renderService(this._services[i]);
    }
    html += "</ul>";

    this._contentEl.innerHTML = html;
    this._wireButtons();
  };

  ServicesPanel.prototype._renderService = function (svc) {
    var pillStatus = STATUS_MAP[svc.status] || "done";
    var portHtml = svc.port
      ? ' <span class="services-port">:' + esc(String(svc.port)) + "</span>"
      : "";
    var exitHtml =
      svc.exit_code !== null && svc.exit_code !== undefined
        ? ' <span class="services-exit">exit ' +
          esc(String(svc.exit_code)) +
          "</span>"
        : "";
    var pidHtml = svc.pid
      ? ' <span class="services-pid">PID ' +
        esc(String(svc.pid)) +
        "</span>"
      : "";

    var logTail = svc.log_tail || "";
    var logHtml = "";
    if (logTail) {
      logHtml =
        "<dw-fold>" +
        "<span>Log output (last 50 lines)</span>" +
        '<pre class="services-log">' +
        esc(logTail) +
        "</pre>" +
        "</dw-fold>";
    }

    var controls = "";
    if (svc.status === "running") {
      controls =
        '<div class="services-controls">' +
        '<dw-button variant="outline" data-action="stop" data-name="' +
        esc(svc.name) +
        '">Stop</dw-button>' +
        "</div>";
    } else {
      controls =
        '<div class="services-controls">' +
        '<dw-button variant="outline" data-action="restart" data-name="' +
        esc(svc.name) +
        '">Restart</dw-button>' +
        "</div>";
    }

    return (
      '<li class="services-entry services-status-' +
      esc(svc.status) +
      '">' +
      '<div class="services-entry-header">' +
      '<div class="services-entry-info">' +
      '<strong class="services-name">' +
      esc(svc.name) +
      "</strong>" +
      '<dw-status-pill status="' +
      esc(pillStatus) +
      '"></dw-status-pill>' +
      portHtml +
      pidHtml +
      exitHtml +
      "</div>" +
      controls +
      "</div>" +
      logHtml +
      "</li>"
    );
  };

  ServicesPanel.prototype._wireButtons = function () {
    if (!this._contentEl) return;
    var self = this;
    var buttons = this._contentEl.querySelectorAll("dw-button[data-action]");
    for (var i = 0; i < buttons.length; i++) {
      (function (btn) {
        btn.addEventListener("click", function () {
          var action = btn.getAttribute("data-action");
          var name = btn.getAttribute("data-name");
          if (action && name) {
            self._sendAction(name, action);
          }
        });
      })(buttons[i]);
    }
  };

  ServicesPanel.prototype._sendAction = function (name, action) {
    var self = this;
    fetch("/api/services/" + encodeURIComponent(name) + "/" + action, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    })
      .then(function () {
        // Refresh immediately after action
        self._fetch();
      })
      .catch(function (err) {
        self._error = "Action failed: " + err.message;
        self._renderContent();
      });
  };

  ServicesPanel.prototype._fetch = function () {
    var self = this;
    fetch("/api/services", { cache: "no-store" })
      .then(function (r) {
        return r.json();
      })
      .then(function (envelope) {
        self._loading = false;
        if (envelope && envelope.ok && envelope.data) {
          self._services = envelope.data.services || [];
          self._error = "";
        } else {
          self._error =
            (envelope && envelope.data && envelope.data.error) ||
            "Failed to load services";
          self._services = [];
        }
        self._renderContent();
      })
      .catch(function (err) {
        self._loading = false;
        self._error = "Failed to load services: " + err.message;
        self._services = [];
        self._renderContent();
      });
  };

  ServicesPanel.prototype._startPolling = function () {
    this._stopPolling();
    this._fetch();
    var self = this;
    this._pollTimer = setInterval(function () {
      if (self._visible) {
        self._fetch();
      }
    }, POLL_INTERVAL);
  };

  ServicesPanel.prototype._stopPolling = function () {
    if (this._pollTimer) {
      clearInterval(this._pollTimer);
      this._pollTimer = null;
    }
  };

  window.DW.ServicesPanel = ServicesPanel;
})();
