/* global-events.js -- Global SSE event stream consumer (WLA-34-01, WLA-34-05).
 *
 * Connects to GET /api/events/global and dispatches typed DOM events on
 * `document` so panels share one connection. Reconnects rebuild from the
 * server snapshot before the workspace is called restored.
 */
(function () {
  "use strict";

  var DW = window.DW || (window.DW = {});
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
  var SNAPSHOT_STATES = {
    "global-disconnected": ["disconnected", "Live updates disconnected. The last saved view remains available."],
    "global-retrying": ["retrying", "Retrying live updates. The last saved view remains available."],
    "global-caught-up": ["caught-up", "Live updates caught up with saved repository facts."],
    "global-restored": ["restored", "Live updates restored."],
    "global-capacity": ["limited", "Live updates are at capacity. Retry in a moment; the last saved view remains available."]
  };

  function GlobalEventStream() {
    this._source = null;
    this._connected = false;
    this._hadConnection = false;
    this._recovering = false;
    this._capacityProbe = null;
    this._announcementSequence = 0;
    this.awaiting_count = 0;
  }

  GlobalEventStream.prototype.connect = function () {
    if (this._source) return;
    var snapshotState = typeof SNAPSHOT_LIVE_STATE === "string"
      ? SNAPSHOT_STATES[SNAPSHOT_LIVE_STATE] : null;
    if (window.SNAPSHOT_MODE) {
      if (snapshotState) this._announceState(snapshotState[0], snapshotState[1]);
      return;
    }

    var self = this;
    var url = "/api/events/global";
    var es = new EventSource(url);
    this._source = es;

    es.onopen = function () {
      self._connected = true;
      if (self._recovering || self._hadConnection) {
        self._announceState("retrying", "Connected again. Catching up with saved repository facts…");
      } else {
        self._setIndicator("connected");
      }
      self._hadConnection = true;
      document.dispatchEvent(new CustomEvent("dw-stream-connected"));
    };

    es.onerror = function () {
      self._connected = false;
      self._recovering = true;
      self._announceState("disconnected", "Live updates disconnected. The last saved view remains available.");
      document.dispatchEvent(new CustomEvent("dw-stream-disconnected"));
      window.setTimeout(function () {
        if (!self._connected && self._source === es) {
          self._announceState("retrying", "Retrying live updates. The last saved view remains available.");
        }
      }, 0);
      self._probeSubscriberCap();
    };

    es.addEventListener("snapshot", function (e) {
      var snap;
      try { snap = JSON.parse(e.data); } catch (_) { return; }
      self.awaiting_count = (snap.pending_requests || []).length;
      document.dispatchEvent(new CustomEvent("dw-snapshot", { detail: snap }));

      if (self._recovering) {
        self._announceState("caught-up", "Live updates caught up with saved repository facts.");
        window.setTimeout(function () {
          if (self._connected && self._recovering) {
            self._recovering = false;
            self._announceState("restored", "Live updates restored.");
          }
        }, 0);
      } else {
        self._setIndicator("connected");
        self._clearNotice();
      }
    });

    SSE_EVENT_NAMES.forEach(function (name) {
      es.addEventListener(name, function (e) {
        var payload;
        try { payload = JSON.parse(e.data); } catch (_) { return; }
        if (name === "request_pending") self.awaiting_count++;
        else if (name === "request_resolved") {
          self.awaiting_count = Math.max(0, self.awaiting_count - 1);
        }
        document.dispatchEvent(new CustomEvent(EVENT_MAP[name], { detail: payload }));
      });
    });
  };

  GlobalEventStream.prototype._probeSubscriberCap = function () {
    if (this._capacityProbe || typeof fetch !== "function") return;
    var self = this;
    var controller = new AbortController();
    this._capacityProbe = controller;
    fetch("/api/events/global?follow=0", {
      cache: "no-store",
      headers: { Accept: "text/event-stream" },
      signal: controller.signal
    }).then(function (response) {
      if (response.status === 503) {
        self._announceState(
          "limited",
          "Live updates are at capacity. Retry in a moment; the last saved view remains available.",
          true
        );
      }
    }).catch(function () {
      // The original disconnect announcement already gives the safe fallback.
    }).finally(function () {
      if (self._capacityProbe === controller) self._capacityProbe = null;
    });
  };

  GlobalEventStream.prototype.disconnect = function () {
    if (this._capacityProbe) this._capacityProbe.abort();
    this._capacityProbe = null;
    if (this._source) {
      this._source.close();
      this._source = null;
    }
    this._connected = false;
    this._recovering = false;
    this._announceState("disconnected", "Live updates disconnected. The last saved view remains available.");
  };

  GlobalEventStream.prototype.isConnected = function () {
    return this._connected;
  };

  GlobalEventStream.prototype._setIndicator = function (state) {
    var el = document.getElementById("dw-connection-status");
    if (!el) return;
    el.className = "dw-connection-status dw-connection-" + state;
    el.setAttribute("data-connection-state", state);
    el.setAttribute("title",
      state === "connected" || state === "restored" ? "Global event stream connected" :
      state === "retrying" ? "Retrying global event stream" :
      state === "caught-up" ? "Global event stream caught up" :
      state === "limited" ? "Global event stream at capacity" :
      "Global event stream disconnected"
    );
  };

  GlobalEventStream.prototype._announceState = function (state, message, urgent) {
    this._setIndicator(state);
    this._showNotice(state, message, urgent);
    if (typeof announceLiveUpdate === "function") {
      this._announcementSequence += 1;
      announceLiveUpdate("global-stream", this._announcementSequence, message);
    }
    document.dispatchEvent(new CustomEvent("dw-stream-state", {
      detail: { state: state, message: message }
    }));
  };

  GlobalEventStream.prototype._showNotice = function (state, message, urgent) {
    var banner = document.getElementById("dw-stream-notice");
    if (!banner) {
      banner = document.createElement("div");
      banner.id = "dw-stream-notice";
      banner.className = "dw-stream-notice";
      banner.setAttribute("role", urgent ? "alert" : "status");
      banner.setAttribute("aria-live", urgent ? "assertive" : "polite");
      banner.setAttribute("aria-atomic", "true");
      var app = document.getElementById("app");
      if (app && app.parentNode) app.parentNode.insertBefore(banner, app);
    }
    banner.className = "dw-stream-notice dw-stream-notice-" + state;
    banner.setAttribute("role", urgent ? "alert" : "status");
    banner.setAttribute("aria-live", urgent ? "assertive" : "polite");
    banner.textContent = message;
  };

  GlobalEventStream.prototype._clearNotice = function () {
    document.getElementById("dw-stream-notice")?.remove();
  };

  DW.globalEvents = new GlobalEventStream();
})();
