/* needs-you.js -- "Needs you" inbox: topbar pill + dropdown (WLA-34-03).
 *
 * Listens to dw-request-pending / dw-request-resolved DOM events from
 * the global event stream and maintains an inbox of outstanding requests.
 * Read-only -- answering is a separate concern (story 04).
 */
(function () {
  "use strict";

  var DW = window.DW || (window.DW = {});

  // ── helpers ────────────────────────────────────────────────────────

  function ago(ts) {
    if (!ts) { return ""; }
    var then = typeof ts === "number" ? ts : new Date(ts).getTime();
    var diff = Math.max(0, Date.now() - then);
    if (diff < 60000) { return Math.floor(diff / 1000) + "s ago"; }
    if (diff < 3600000) { return Math.floor(diff / 60000) + "m ago"; }
    if (diff < 86400000) { return Math.floor(diff / 3600000) + "h ago"; }
    return Math.floor(diff / 86400000) + "d ago";
  }

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  /** Kind label for display. */
  function kindLabel(kind) {
    switch (kind) {
      case "checkpoint-pending":            return "Checkpoint";
      case "request-pending":               return "Decision";
      case "request-republished":           return "Republished";
      case "program-intervention-required": return "Intervention";
      default:                              return "Request";
    }
  }

  /** Hash route for a pending item. */
  function routeFor(item) {
    if (item.run_id && item.kind === "program-intervention-required") {
      return "#/program/" + encodeURIComponent(item.run_id);
    }
    if (item.run_id) {
      return "#/run/" + encodeURIComponent(item.run_id);
    }
    return "#/board";
  }

  // ── NeedsYouInbox ──────────────────────────────────────────────────

  function NeedsYouInbox() {
    /** @type {Map<string, object>} keyed by notification id */
    this._items = new Map();
    this._pillEl = null;
    this._badgeEl = null;
    this._dropdownEl = null;
    this._wrapperEl = null;
    this._open = false;
    this._notifPermAsked = false;
    this._agoTimer = null;
  }

  /** Inject DOM and start listening. Call once after DOMContentLoaded. */
  NeedsYouInbox.prototype.mount = function () {
    this._buildDOM();
    this._listen();
    if (window.SNAPSHOT_MODE && new URLSearchParams(location.search).has("needsyouopen")) {
      this._items.set("request-memory-glass", {
        id: "request-memory-glass",
        run_id: "run-memory-glass-9c7d4e8f1029384756abcdef0123456789abcdef",
        project: "sample",
        kind: "request-pending",
        node: "independent-review",
        detail: "Choose whether the saved review is enough to continue.",
        timestamp: new Date().toISOString()
      });
      this._sync();
      this._openDropdown();
    } else {
      this._fetchInitial();
    }
    // Refresh "ago" labels every 30 s
    var self = this;
    this._agoTimer = setInterval(function () { self._renderList(); }, 30000);
  };

  NeedsYouInbox.prototype._buildDOM = function () {
    var wrapper = document.createElement("div");
    wrapper.className = "needs-you-wrapper";

    // Pill (button + badge)
    var pill = document.createElement("button");
    pill.className = "needs-you-pill";
    pill.setAttribute("type", "button");
    pill.setAttribute("aria-expanded", "false");
    pill.setAttribute("aria-controls", "needs-you-dropdown");
    pill.setAttribute("title", "Needs your attention");
    pill.style.display = "none";

    var label = document.createElement("span");
    label.className = "needs-you-label";
    label.textContent = "Needs you";
    pill.appendChild(label);

    var badge = document.createElement("dw-badge");
    badge.setAttribute("variant", "needs-you");
    badge.setAttribute("count", "0");
    pill.appendChild(badge);

    wrapper.appendChild(pill);

    // Dropdown
    var dropdown = document.createElement("div");
    dropdown.className = "needs-you-dropdown";
    dropdown.id = "needs-you-dropdown";
    dropdown.setAttribute("role", "menu");
    dropdown.setAttribute("aria-label", "Needs you");
    wrapper.appendChild(dropdown);

    this._wrapperEl = wrapper;
    this._pillEl = pill;
    this._badgeEl = badge;
    this._dropdownEl = dropdown;

    // Attention stays ahead of the demoted display and refresh tools.
    var tools = document.querySelector(".topbar .topbar-tools");
    if (tools) {
      tools.parentNode.insertBefore(wrapper, tools);
    } else {
      var topbar = document.querySelector(".topbar");
      if (topbar) { topbar.appendChild(wrapper); }
    }

    // Wire interactions
    var self = this;
    pill.addEventListener("click", function (e) {
      e.stopPropagation();
      if (self._open) { self._close(true); } else { self._openDropdown(); }
    });

    document.addEventListener("click", function (e) {
      if (self._open && !wrapper.contains(e.target)) {
        self._close(false);
      }
    });

    dropdown.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        e.preventDefault();
        self._close(true);
      }
    });
    pill.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && self._open) {
        e.preventDefault();
        self._close(true);
      }
    });
  };

  NeedsYouInbox.prototype._openDropdown = function () {
    this._open = true;
    this._pillEl.setAttribute("aria-expanded", "true");
    this._dropdownEl.classList.add("open");
    this._renderList();
    var first = this._dropdownEl.querySelector("a");
    focusElement(first);
  };

  NeedsYouInbox.prototype._close = function (returnFocus) {
    this._open = false;
    this._pillEl.setAttribute("aria-expanded", "false");
    this._dropdownEl.classList.remove("open");
    if (returnFocus) { focusElement(this._pillEl); }
  };

  NeedsYouInbox.prototype._listen = function () {
    var self = this;

    document.addEventListener("dw-request-pending", function (e) {
      var d = e.detail || {};
      if (!d.id) { return; }
      self._items.set(d.id, {
        id:        d.id,
        run_id:    d.run_id || "",
        project:   d.project || "",
        kind:      d.kind || "request-pending",
        node:      d.node || "",
        detail:    d.detail || "",
        timestamp: d.timestamp || new Date().toISOString()
      });
      self._sync();
      self._maybeNotify(d);
    });

    document.addEventListener("dw-request-resolved", function (e) {
      var d = e.detail || {};
      if (d.id) { self._items.delete(d.id); }
      self._sync();
    });

    // Re-fetch after reconnect in case we missed events
    document.addEventListener("dw-stream-connected", function () {
      self._fetchInitial();
    });
  };

  NeedsYouInbox.prototype._fetchInitial = function () {
    var self = this;
    fetch("/api/notifications")
      .then(function (r) { return r.json(); })
      .then(function (envelope) {
        var data = envelope.data || envelope;
        var notifications = data.notifications || [];
        var pendingKinds = {
          "request-pending": true,
          "checkpoint-pending": true,
          "request-republished": true,
          "program-intervention-required": true
        };
        self._items.clear();
        notifications.forEach(function (n) {
          if (pendingKinds[n.kind]) {
            self._items.set(n.id, {
              id:        n.id,
              run_id:    n.run_id || "",
              project:   n.project || "",
              kind:      n.kind,
              node:      n.node || "",
              detail:    n.detail || "",
              timestamp: n.timestamp || ""
            });
          }
        });
        self._sync();
      })
      .catch(function () {
        // Non-fatal; the SSE stream will populate as events arrive
      });
  };

  NeedsYouInbox.prototype._sync = function () {
    var count = this._items.size;

    // Keep the count inside one attention control for sighted and screen-reader users.
    this._badgeEl.setAttribute("count", String(count));
    this._pillEl.setAttribute("aria-label", "Needs you, " + count + (count === 1 ? " item" : " items"));

    // Show/hide pill
    this._pillEl.style.display = count > 0 ? "" : "none";

    // Close dropdown if empty
    if (count === 0 && this._open) {
      // Keep open to show empty state
    }

    // Re-render list if open
    if (this._open) {
      this._renderList();
    }
  };

  NeedsYouInbox.prototype._renderList = function () {
    var dd = this._dropdownEl;

    if (this._items.size === 0) {
      dd.innerHTML =
        '<div class="needs-you-empty" role="menuitem">' +
        "Nothing waiting" +
        "</div>";
      return;
    }

    // Sort oldest first
    var sorted = Array.from(this._items.values()).sort(function (a, b) {
      return (a.timestamp || "").localeCompare(b.timestamp || "");
    });

    var html = sorted.map(function (item) {
      var href = routeFor(item);
      var context = item.node || item.run_id || "";
      var project = item.project ? esc(item.project) : "";
      var detail = item.detail
        ? esc(item.detail)
        : esc(kindLabel(item.kind));
      var timeAgo = ago(item.timestamp);
      var meta = [esc(kindLabel(item.kind)), project, context ? esc(context) : ""]
        .filter(Boolean).join(" · ");
      var memoryKind = item.kind === "program-intervention-required" ? "program" : "run";
      var memoryAction = item.run_id
        ? '<button type="button" class="needs-you-memory" role="menuitem" data-memory-open="' + esc(memoryKind + ":" + item.run_id) + '" data-memory-kind="' + esc(memoryKind) + '" data-memory-id="' + esc(item.run_id) + '">Memory</button>'
        : "";
      return (
        '<div class="needs-you-row" role="none">' +
          '<a class="needs-you-item" href="' + esc(href) + '" role="menuitem" data-id="' + esc(item.id) + '">' +
            '<span class="needs-you-item-main">' +
              '<span class="needs-you-item-detail">' + detail + "</span>" +
              '<span class="needs-you-item-meta"><span class="needs-you-item-kind">' + meta + "</span></span>" +
            "</span>" +
            (timeAgo
              ? '<time class="needs-you-item-ago" datetime="' + esc(item.timestamp || "") + '">' + esc(timeAgo) + "</time>"
              : "") +
          "</a>" + memoryAction +
        "</div>"
      );
    }).join("");

    dd.innerHTML = html;

    // Close after navigation or opening the related memory pane.
    var self = this;
    var actions = dd.querySelectorAll("a, .needs-you-memory");
    for (var i = 0; i < actions.length; i++) {
      actions[i].addEventListener("click", function () {
        self._close(false);
      });
    }
  };

  // ── Browser notifications ──────────────────────────────────────────

  NeedsYouInbox.prototype._maybeNotify = function (data) {
    // Only notify when the document is not focused
    if (document.hasFocus()) { return; }
    if (!("Notification" in window)) { return; }

    var self = this;

    if (Notification.permission === "granted") {
      self._showNotification(data);
    } else if (Notification.permission !== "denied" && !self._notifPermAsked) {
      self._notifPermAsked = true;
      Notification.requestPermission().then(function (perm) {
        if (perm === "granted") {
          self._showNotification(data);
        }
      });
    }
  };

  NeedsYouInbox.prototype._showNotification = function (data) {
    var title = "Delivery Workbench needs you";
    var body = kindLabel(data.kind || "request-pending");
    if (data.project) { body += " in " + data.project; }
    if (data.node) { body += " (" + data.node + ")"; }

    var n = new Notification(title, {
      body: body,
      tag: "dw-needs-you-" + (data.id || ""),
      renotify: true
    });

    n.onclick = function () {
      window.focus();
      var route = routeFor(data);
      if (route) { location.hash = route; }
      n.close();
    };
  };

  DW.needsYou = new NeedsYouInbox();

  // Auto-mount: the script loads after the DOM is ready (end of body).
  // Also ensure the global event stream is connected so we receive events.
  DW.needsYou.mount();
  if (DW.globalEvents && typeof DW.globalEvents.connect === "function") {
    DW.globalEvents.connect();
  }
})();
