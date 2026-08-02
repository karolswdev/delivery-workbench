"use strict";

/* ── Ask-and-Resume controller (WLA-34-04) ────────────────────────────
 * Renders pending typed requests inline in the session transcript and
 * submits answers through the DW typed-request machinery.  Answers go
 * through POST /api/requests/respond which previews and applies the
 * request action atomically -- never a generic chat endpoint.  */

window.DW = window.DW || {};

class AskResumeController {
  constructor() {
    this._pending = new Map();   // correlation_id -> request object
    this._answered = new Map();  // correlation_id -> {decision, ts}
    this._submitting = new Set();
  }

  /* ── public API ──────────────────────────────────────────── */

  /** Build the full list of pending requests from notifications. */
  loadFromNotifications(notifications) {
    this._pending.clear();
    for (const notif of notifications || []) {
      const kind = notif.kind || "";
      if (
        kind !== "request-pending" &&
        kind !== "checkpoint-pending" &&
        kind !== "request-republished" &&
        kind !== "program-intervention-required"
      ) continue;
      const req = notif.request || {};
      const correlationId = req.correlation_id || "";
      if (!correlationId) continue;
      if (this._answered.has(correlationId)) continue;
      this._pending.set(correlationId, {
        correlationId: correlationId,
        notificationId: notif.id || "",
        kind: kind,
        runId: notif.run_id || "",
        node: notif.node || "",
        detail: notif.detail || "",
        responseSchema: req.response_schema || {},
        guidance: req.guidance || {},
        boundary: req.boundary || "",
        unread: notif.unread !== false,
      });
    }
  }

  /** Filter to only requests relevant to a given run_id. */
  requestsForRun(runId) {
    const result = [];
    for (const req of this._pending.values()) {
      if (req.runId === runId) result.push(req);
    }
    return result;
  }

  /** Filter to only requests relevant to a story (by checking notification node). */
  requestsForStory(storyId) {
    const result = [];
    for (const req of this._pending.values()) {
      if (req.node === storyId || this._pending.size > 0) result.push(req);
    }
    return result;
  }

  /** All pending requests. */
  allRequests() {
    return Array.from(this._pending.values());
  }

  /** Render inline HTML for one pending request. */
  renderRequest(request) {
    const schema = request.responseSchema || {};
    const decisions = schema.decision || [];
    const hasReason = Boolean(schema.reason);
    const guidance = request.guidance || {};
    const choices = guidance.choices || [];
    const correlationId = esc(request.correlationId);
    const isSubmitting = this._submitting.has(request.correlationId);

    const answered = this._answered.get(request.correlationId);
    if (answered) {
      return this._answeredHtml(request, answered);
    }

    const controlsHtml = this._buildControls(
      request.correlationId, decisions, choices, hasReason, isSubmitting
    );

    return [
      '<div class="ask-resume-card" data-correlation-id="' + correlationId + '">',
      '<dw-stream-line type="question">',
      '<strong>' + esc(request.kind.replace(/-/g, " ")) + '</strong> ',
      esc(request.detail),
      '</dw-stream-line>',
      '<div class="ask-resume-meta">',
      '<code>' + correlationId + '</code>',
      request.boundary ? ' <span class="ask-resume-boundary">' + esc(request.boundary) + '</span>' : '',
      request.node ? ' <span class="ask-resume-node">node: ' + esc(request.node) + '</span>' : '',
      '</div>',
      controlsHtml,
      '</div>',
    ].join("");
  }

  /** Render all pending requests as a block for the session transcript. */
  renderAllRequests(requests) {
    if (!requests || !requests.length) return "";
    return '<div class="ask-resume-block">' +
      '<span class="session-section-label ops-label">Pending decisions</span>' +
      requests.map(function (req) { return this.renderRequest(req); }.bind(this)).join("") +
      '</div>';
  }

  /** POST the answer to the typed-request machinery. */
  async submitAnswer(correlationId, decision, reason) {
    if (this._submitting.has(correlationId)) return null;
    this._submitting.add(correlationId);

    try {
      const payload = {
        correlation_id: correlationId,
        decision: decision,
      };
      if (reason) payload.reason = reason;

      const { status, body } = await postJson("/api/requests/respond", payload);

      if (status >= 400 || body.ok === false) {
        const msg = (body.issues && body.issues[0]) || "Request response failed (" + status + ")";
        throw new Error(msg);
      }

      this._answered.set(correlationId, {
        decision: decision,
        reason: reason || "",
        ts: new Date().toISOString(),
      });
      this._pending.delete(correlationId);

      // Emit event for global listeners (needs-you inbox, etc.)
      document.dispatchEvent(new CustomEvent("dw-request-resolved", {
        detail: {
          correlation_id: correlationId,
          decision: decision,
          type: "request_resolved",
        },
      }));

      return body.data;
    } finally {
      this._submitting.delete(correlationId);
    }
  }

  /** Attach event handlers to answer controls inside a container element. */
  wireAnswerControls(container) {
    if (!container) return;
    var self = this;

    // Approval buttons (accept / reject)
    container.querySelectorAll("[data-ask-decision]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var card = btn.closest(".ask-resume-card");
        if (!card) return;
        var correlationId = card.dataset.correlationId;
        var decision = btn.dataset.askDecision;
        var reasonInput = card.querySelector(".ask-resume-reason");
        var reason = reasonInput ? reasonInput.value.trim() : "";
        self._handleSubmit(card, correlationId, decision, reason);
      });
    });

    // Choice selects
    container.querySelectorAll(".ask-resume-choice-submit").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var card = btn.closest(".ask-resume-card");
        if (!card) return;
        var correlationId = card.dataset.correlationId;
        var select = card.querySelector(".ask-resume-choice-select");
        if (!select || !select.value) return;
        var decision = select.value;
        var reasonInput = card.querySelector(".ask-resume-reason");
        var reason = reasonInput ? reasonInput.value.trim() : "";
        self._handleSubmit(card, correlationId, decision, reason);
      });
    });
  }

  /* ── internal ────────────────────────────────────────────── */

  async _handleSubmit(card, correlationId, decision, reason) {
    var errorEl = card.querySelector(".ask-resume-error");
    if (errorEl) errorEl.textContent = "";

    // Disable buttons while submitting
    card.querySelectorAll("button").forEach(function (b) { b.disabled = true; });
    card.classList.add("ask-resume-submitting");

    try {
      await this.submitAnswer(correlationId, decision, reason);
      // Re-render the card as answered
      card.outerHTML = this.renderRequest({
        correlationId: correlationId,
        kind: "",
        detail: "",
        responseSchema: {},
        guidance: {},
        boundary: "",
        node: "",
        notificationId: "",
        runId: "",
        unread: false,
      });
    } catch (err) {
      card.classList.remove("ask-resume-submitting");
      card.querySelectorAll("button").forEach(function (b) { b.disabled = false; });
      if (errorEl) {
        errorEl.textContent = err.message || "Failed to submit answer.";
      } else {
        var el = document.createElement("p");
        el.className = "ask-resume-error";
        el.setAttribute("role", "alert");
        el.textContent = err.message || "Failed to submit answer.";
        card.appendChild(el);
      }
    }
  }

  _buildControls(correlationId, decisions, choices, hasReason, isSubmitting) {
    var parts = ['<div class="ask-resume-controls">'];

    if (decisions.length === 2 && this._isApprovalPair(decisions)) {
      // Approval: Accept / Reject buttons
      for (var i = 0; i < decisions.length; i++) {
        var d = decisions[i];
        var variant = this._isPositiveDecision(d) ? "primary" : "danger";
        var label = this._decisionLabel(d, choices);
        parts.push(
          '<button type="button" class="ask-resume-btn ask-resume-btn-' + esc(variant) + '"' +
          ' data-ask-decision="' + esc(d) + '"' +
          (isSubmitting ? " disabled" : "") +
          '>' + esc(label) + '</button>'
        );
      }
    } else if (decisions.length > 2) {
      // Choice: select dropdown
      parts.push('<select class="ask-resume-choice-select">');
      parts.push('<option value="">Choose a response...</option>');
      for (var j = 0; j < decisions.length; j++) {
        var opt = decisions[j];
        var optLabel = this._decisionLabel(opt, choices);
        parts.push('<option value="' + esc(opt) + '">' + esc(optLabel) + '</option>');
      }
      parts.push('</select>');
      parts.push(
        '<button type="button" class="ask-resume-btn ask-resume-btn-primary ask-resume-choice-submit"' +
        (isSubmitting ? " disabled" : "") +
        '>Submit choice</button>'
      );
    } else if (decisions.length === 1) {
      // Single decision button
      var single = decisions[0];
      var singleLabel = this._decisionLabel(single, choices);
      parts.push(
        '<button type="button" class="ask-resume-btn ask-resume-btn-primary"' +
        ' data-ask-decision="' + esc(single) + '"' +
        (isSubmitting ? " disabled" : "") +
        '>' + esc(singleLabel) + '</button>'
      );
    }

    if (hasReason) {
      parts.push(
        '<input type="text" class="ask-resume-reason" placeholder="Reason (optional)" maxlength="200">'
      );
    }

    parts.push('<p class="ask-resume-error" role="alert"></p>');
    parts.push('</div>');
    return parts.join("");
  }

  _answeredHtml(request, answered) {
    var correlationId = esc(request.correlationId);
    var ts = "";
    try { ts = new Date(answered.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); }
    catch (_) { ts = answered.ts; }
    return [
      '<div class="ask-resume-card ask-resume-answered" data-correlation-id="' + correlationId + '">',
      '<dw-stream-line type="status" timestamp="' + esc(answered.ts) + '">',
      '<strong>Answered:</strong> ' + esc(answered.decision),
      answered.reason ? ' <span class="ask-resume-answered-reason">(' + esc(answered.reason) + ')</span>' : '',
      '</dw-stream-line>',
      '</div>',
    ].join("");
  }

  _isApprovalPair(decisions) {
    var sorted = decisions.slice().sort();
    return (
      (sorted[0] === "approve" && sorted[1] === "reject") ||
      (sorted[0] === "accept" && sorted[1] === "reject") ||
      (sorted[0] === "accept" && sorted[1] === "deny") ||
      decisions.length === 2
    );
  }

  _isPositiveDecision(d) {
    return /^(approve|accept|yes|continue|allow|confirm)$/i.test(d);
  }

  _decisionLabel(decision, choices) {
    for (var i = 0; i < choices.length; i++) {
      if (choices[i].decision === decision && choices[i].label) {
        return choices[i].label;
      }
    }
    return decision.charAt(0).toUpperCase() + decision.slice(1);
  }
}

window.DW.AskResumeController = AskResumeController;
window.DW._askResume = new AskResumeController();
