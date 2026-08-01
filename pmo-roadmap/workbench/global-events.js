/* global-events.js -- Global SSE event stream consumer (WLA-34-01, WLA-34-05).
 *
 * Connects to GET /api/events/global and dispatches typed DOM events
 * on `document` so any panel can listen without managing its own
 * connection.  Auto-reconnects via native EventSource behaviour.
 *
 * Snapshot-then-tail reconnect (WLA-34-05):
 * On every connect (including reconnect after a drop), the server
 * emits a `snapshot` event containing the full current state.  The
 * client resets its counters from the snapshot so reconnecting twice
 * produces the same state, not doubled entries.
 */
(function () {
  "use strict";

  var DW = window.DW || (window.DW = {});

  // ── event-type map: SSE event name -> DOM custom event name ──────
  var EVENT_MAP = {
    story_changed:      "dw-story-changed",
    run_changed:        "dw-run-changed",
    program_changed:    "dw-program-changed",
    request_pending:    "dw-request-pending",
    request_resolved:   "dw-request-resolved",
    evidence_captured:  "dw-evidence-captured",
    gate_result:        "dw-gate-result"
  };

  var SSE_EVENT_NAMES = Object.keys(EVENT_MAP);

  function GlobalEventStream() {
    this._source = null;
    this._connected = false;
    this._hadConnection = false;
    this.awaiting_count = 0;
  }

  GlobalEventStream.prototype.connect = function () {
    if (this._source) { return; }
    var self = this;
    var url = "/api/events/global";
    var es = new EventSource(url);
    this._source = es;

    es.onopen = function () {
      self._connected = true;
      // If this is a reconnect, show "catching up" until the snapshot
      // arrives and resets state.
      if (self._hadConnection) {
        self._setIndicator("reconnecting");
        self._showCatchingUp(true);
      } else {
        self._setIndicator("connected");
      }
      self._hadConnection = true;
      document.dispatchEvent(new CustomEvent("dw-stream-connected"));
    };

    es.onerror = function () {
      self._connected = false;
      self._setIndicator("reconnecting");
      document.dispatchEvent(new CustomEvent("dw-stream-disconnected"));
    };

    // ── snapshot handler (WLA-34-05) ──────────────────────────────
    // The server sends a snapshot event on every connect.  Reset
    // counters from it so reconnecting is idempotent.
    es.addEventListener("snapshot", function (e) {
      var snap;
      try { snap = JSON.parse(e.data); } catch (_) { return; }

      // Reset pending request count from snapshot
      self.awaiting_count = (snap.pending_requests || []).length;

      // Dispatch a snapshot event so other panels can rebuild
      document.dispatchEvent(new CustomEvent("dw-snapshot", {
        detail: snap
      }));

      // After snapshot is processed, we are fully caught up
      self._setIndicator("connected");
      self._showCatchingUp(false);
    });

    SSE_EVENT_NAMES.forEach(function (name) {
      es.addEventListener(name, function (e) {
        var payload;
        try { payload = JSON.parse(e.data); } catch (_) { return; }
        // Track pending request count
        if (name === "request_pending") {
          self.awaiting_count++;
        } else if (name === "request_resolved") {
          self.awaiting_count = Math.max(0, self.awaiting_count - 1);
        }
        document.dispatchEvent(new CustomEvent(EVENT_MAP[name], {
          detail: payload
        }));
      });
    });
  };

  GlobalEventStream.prototype.disconnect = function () {
    if (this._source) {
      this._source.close();
      this._source = null;
    }
    this._connected = false;
    this._setIndicator("disconnected");
    this._showCatchingUp(false);
  };

  GlobalEventStream.prototype.isConnected = function () {
    return this._connected;
  };

  GlobalEventStream.prototype._setIndicator = function (state) {
    var el = document.getElementById("dw-connection-status");
    if (!el) { return; }
    el.className = "dw-connection-status dw-connection-" + state;
    el.setAttribute("title",
      state === "connected"    ? "Global event stream connected" :
      state === "reconnecting" ? "Reconnecting to event stream..." :
                                 "Event stream disconnected"
    );
    el.textContent =
      state === "connected"    ? "" :
      state === "reconnecting" ? "" :
                                 "";
  };

  GlobalEventStream.prototype._showCatchingUp = function (show) {
    var existing = document.getElementById("dw-catching-up");
    if (show) {
      if (!existing) {
        var banner = document.createElement("div");
        banner.id = "dw-catching-up";
        banner.className = "dw-catching-up";
        banner.setAttribute("role", "status");
        banner.setAttribute("aria-live", "polite");
        banner.textContent = "Catching up...";
        var app = document.getElementById("app");
        if (app && app.parentNode) {
          app.parentNode.insertBefore(banner, app);
        }
      }
    } else if (existing) {
      existing.remove();
    }
  };

  DW.globalEvents = new GlobalEventStream();
})();
