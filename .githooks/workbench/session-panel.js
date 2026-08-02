"use strict";

/* ── Session panel (WLA-33-02) ─────────────────────────────────────────
 * Opens alongside the board when a story card is clicked. Shows live
 * agent activity when an agent session is pinned to the story, or the
 * story body and evidence summary when no agent is active. Streams
 * events from /api/missioncontrol (polling) and, when a pinned run
 * exists, tails its SSE ledger at /api/runs/{id}/events.  */

window.DW = window.DW || {};

class SessionPanel {
  constructor() {
    this._storyId = "";
    this._slug = "";
    this._detail = null;
    this._sessions = [];
    this._events = [];
    this._decisions = [];
    this._loading = true;
    this._error = "";
    this._needsYou = false;
    this._sse = null;
    this._pollTimer = null;
    this._container = null;
    this._maxEvents = 200;
  }

  /* ── public API ──────────────────────────────────────────── */

  open(storyId, slug) {
    this.close();
    this._storyId = storyId;
    this._slug = slug || selectedProject;
    this._detail = null;
    this._sessions = [];
    this._events = [];
    this._decisions = [];
    this._loading = true;
    this._error = "";
    this._needsYou = false;
    this._ensureContainer();
    this._mount();
    this._load();
  }

  close() {
    this._stopLive();
    this._storyId = "";
    this._slug = "";
    this._detail = null;
    this._sessions = [];
    this._events = [];
    this._decisions = [];
    this._loading = false;
    this._error = "";
    this._needsYou = false;
    if (this._container) {
      this._container.innerHTML = "";
    }
  }

  isOpen() {
    return Boolean(this._storyId);
  }

  storyId() {
    return this._storyId;
  }

  render() {
    if (!this._storyId) return "";

    if (this._loading && !this._detail) {
      return this._shell(`
        <dw-skeleton lines="5"></dw-skeleton>
        <p class="session-loading-hint">Loading story details...</p>
      `);
    }

    if (this._error) {
      return this._shell(`
        <div class="session-error" role="alert">
          <strong>Could not load session data.</strong>
          <p>${esc(this._error)}</p>
          <button type="button" class="session-retry">Retry</button>
        </div>
      `);
    }

    const detail = this._detail || {};
    const hasAgent = this._sessions.length > 0;
    const memoryRun = this._findPinnedRun();

    const header = `
      <div class="session-header">
        <div class="session-title-row">
          <code>${esc(this._storyId)}</code>
          <dw-status-pill status="${esc(detail.status || "backlog")}"></dw-status-pill>
          ${this._needsYou ? '<dw-badge variant="needs-you" count="Needs you"></dw-badge>' : ""}
        </div>
        <h3 class="session-story-title">${esc(detail.title || this._storyId)}</h3>
        <div class="session-controls">
          ${memoryRun ? `<button type="button" class="session-memory-btn" data-memory-open="run:${esc(memoryRun)}" data-memory-kind="run" data-memory-id="${esc(memoryRun)}">Memory</button>` : ""}
          <button type="button" class="session-close-btn" aria-label="Close session panel">Close</button>
        </div>
      </div>`;

    if (hasAgent) {
      return this._shell(`${header}${this._activeSessionHtml()}`);
    }
    return this._shell(`${header}${this._inactiveHtml()}`);
  }

  /* ── internal ────────────────────────────────────────────── */

  _shell(body) {
    return `<div class="session-panel" role="complementary" aria-label="Session panel for ${esc(this._storyId)}">${body}</div>`;
  }

  _ensureContainer() {
    let el = document.querySelector('[data-panel="session"] .session-panel-root');
    if (!el) {
      const panel = document.querySelector('[data-panel="session"]');
      if (panel) {
        el = document.createElement("div");
        el.className = "session-panel-root";
        panel.innerHTML = "";
        panel.appendChild(el);
      }
    }
    this._container = el || null;
  }

  _mount() {
    if (!this._container) return;
    this._container.innerHTML = this.render();
    this._wire();
  }

  _wire() {
    if (!this._container) return;
    const closeBtn = this._container.querySelector(".session-close-btn");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        this.close();
        if (window.DW._layout) window.DW._layout.close("session");
      });
    }
    const retryBtn = this._container.querySelector(".session-retry");
    if (retryBtn) {
      retryBtn.addEventListener("click", () => this._load());
    }
    // WLA-34-04: wire ask-resume answer controls
    if (window.DW._askResume) {
      window.DW._askResume.wireAnswerControls(this._container);
    }
  }

  async _load() {
    this._loading = true;
    this._error = "";
    this._mount();

    try {
      const [detailRes, mcRes] = await Promise.all([
        api(`/api/projects/${encodeURIComponent(this._slug)}/stories/${encodeURIComponent(this._storyId)}`),
        api("/api/missioncontrol?tail=40"),
      ]);

      this._detail = detailRes.data;

      const pins = mcRes.data.pins || {};
      const pinned = pins[this._storyId] || [];
      this._sessions = pinned;
      await this._refreshDecisions(this._findPinnedRun());

      const allEvents = mcRes.data.events || [];
      this._events = [...new Map(allEvents.filter(
        (ev) => ev.story_id === this._storyId || ev.detail?.story_id === this._storyId
      ).map((event) => [this._eventId(event), event])).values()];

      // WLA-34-04: load pending typed requests into ask-resume controller
      try {
        const ntfRes = await api("/api/notifications");
        if (window.DW._askResume) {
          window.DW._askResume.loadFromNotifications(
            (ntfRes.data || {}).notifications || []
          );
        }
      } catch (_ntfErr) {
        // Notification fetch failure is non-fatal
      }

      this._detectNeedsYou();
      this._loading = false;
      this._mount();

      // WLA-33-03: check for uncommitted changes and show a badge
      if (typeof checkDiffForStory === "function") {
        checkDiffForStory(this._storyId, this._slug);
      }

      this._startLive();
    } catch (err) {
      this._error = err.message || "Unknown error";
      this._loading = false;
      this._mount();
    }
  }

  _detectNeedsYou() {
    const wasNeeding = this._needsYou;
    this._needsYou = this._sessions.some(
      (s) => s.correlation === "on_story" && s.status === "awaiting_input"
    );
    if (this._needsYou && !wasNeeding) {
      this._updateBoardCard();
    }
  }

  _updateBoardCard() {
    const card = document.querySelector(
      `dw-card[data-story="${selectorEscape(this._storyId)}"]`
    );
    if (!card) return;
    if (!card.querySelector(".session-needs-you")) {
      const indicator = document.createElement("dw-badge");
      indicator.setAttribute("variant", "needs-you");
      indicator.setAttribute("count", "Needs you");
      indicator.className = "session-needs-you";
      const top = card.querySelector(".bcard-top");
      if (top) top.appendChild(indicator);
    }
  }

  _activeSessionHtml() {
    const sessions = this._sessions;
    const agentInfo = sessions.map((s) => `
      <div class="session-agent-info">
        <span class="session-agent-name">${esc(s.agent || s.adapter || "Agent")}</span>
        <dw-status-pill status="${esc(s.status === "active" ? "in-progress" : s.status || "backlog")}"></dw-status-pill>
        ${s.session_id ? `<code class="session-id">${esc(String(s.session_id).slice(0, 12))}...</code>` : ""}
      </div>
    `).join("");

    const transcript = this._transcriptHtml();

    return `
      <div class="session-active">
        <div class="session-agents">
          <span class="session-section-label ops-label">Active agents</span>
          ${agentInfo}
        </div>
        <div class="session-transcript" role="log" aria-label="Agent activity transcript">
          <span class="session-section-label ops-label">Live activity</span>
          ${transcript}
        </div>
      </div>`;
  }

  _transcriptHtml() {
    const eventLines = this._events.map((ev) => {
      const type = this._eventType(ev);
      const ts = ev.ts || ev.timestamp || "";
      const body = this._eventBody(ev);
      return `<dw-stream-line type="${esc(type)}" timestamp="${esc(ts)}">${body}</dw-stream-line>`;
    }).join("");
    const decisionLines = this._decisions.map((decision) => {
      const origin = decision.originating_receipt_ref || decision.resulting_ledger_event;
      return `<dw-stream-line type="decision" timestamp="">
        <strong>${esc(decision.decision_kind)} decision</strong>
        ${esc(decision.outcome)}
        <span class="session-decision-authority basis-${esc(decision.basis_type)}">${esc(decision.basis_type)}</span>
        <a href="#/live/run/${encodeURIComponent(decision.origin)}/technical" data-source-ref="${esc(origin)}">Open saved source</a>
      </dw-stream-line>`;
    }).join("");
    const lines = eventLines + decisionLines;

    // WLA-34-04: inline pending requests from the ask-resume controller
    const askResume = window.DW._askResume;
    let requestsHtml = "";
    if (askResume) {
      const pending = askResume.allRequests().filter(
        (req) => !this._storyId || req.node === this._storyId || req.runId
      );
      requestsHtml = askResume.renderAllRequests(pending);
    }

    if (!lines && !requestsHtml) {
      return '<p class="session-empty-transcript">No activity recorded yet. Waiting for events...</p>';
    }

    return lines + requestsHtml;
  }

  _eventType(ev) {
    const kind = ev.event || ev.kind || ev.type || "";
    if (kind === "evidence_capture") return "evidence";
    if (kind === "story_status") return "status";
    if (kind === "gate_pass" || kind === "gate_refusal") return "gate";
    if (kind === "contract_generated") return "contract";
    if (/question|input|await/i.test(kind)) return "question";
    if (/tool|call|execute/i.test(kind)) return "tool-call";
    if (/file|edit|write/i.test(kind)) return "file-edit";
    return "text";
  }

  _eventBody(ev) {
    const kind = ev.event || ev.kind || ev.type || "";
    const detail = ev.detail || {};

    if (kind === "story_status") {
      return `<strong>Status changed</strong> ${esc(detail.from || "?")} → ${esc(detail.to || "?")}`;
    }
    if (kind === "evidence_capture") {
      const exit = detail.exit_code !== undefined ? ` (exit ${esc(detail.exit_code)})` : "";
      return `<strong>Evidence captured</strong>${exit}`;
    }
    if (kind === "gate_pass") {
      return `<strong>Gate passed</strong> ${esc(detail.stories || "")}`;
    }
    if (kind === "gate_refusal") {
      return `<strong>Gate refused</strong> ${esc(detail.rule || "")}`;
    }
    if (kind === "contract_generated") {
      return `<strong>Contract generated</strong> ${esc(detail.stories || "")}`;
    }

    const summary = Object.entries(detail)
      .map(([k, v]) => `${esc(k)}: ${esc(v)}`)
      .join(", ");
    return `<strong>${esc(kind || "event")}</strong> ${summary}`;
  }

  _inactiveHtml() {
    const detail = this._detail || {};
    const markdown = detail.story_markdown || "";
    const evidence = detail.evidence_markdown || "";
    const runs = detail.captured_runs || [];

    return `
      <div class="session-inactive">
        <div class="session-no-agent">
          <dw-badge variant="default" count="No active agent"></dw-badge>
          <p>No agent session is running on this story.</p>
        </div>
        ${markdown ? `
          <details class="session-story-body" open>
            <summary>Story body</summary>
            <pre class="session-markdown">${esc(markdown)}</pre>
          </details>` : ""}
        ${evidence ? `
          <details class="session-evidence-summary">
            <summary>Evidence (${runs.length} captured run${runs.length === 1 ? "" : "s"})</summary>
            <pre class="session-markdown">${esc(evidence)}</pre>
          </details>` : `
          <div class="session-no-evidence">
            <p>No evidence has been captured for this story.</p>
          </div>`}
        ${runs.length ? `
          <div class="session-runs">
            <span class="session-section-label ops-label">Captured runs</span>
            ${runs.map((run) => `
              <div class="session-run-entry">
                <code>${esc(run.command || "unknown command")}</code>
                <span class="session-run-exit ${run.exit_code === 0 ? "ok" : "fail"}">exit ${esc(run.exit_code)}</span>
                ${run.timestamp ? `<time>${esc(run.timestamp)}</time>` : ""}
              </div>
            `).join("")}
          </div>` : ""}
      </div>`;
  }

  /* ── live updates ────────────────────────────────────────── */

  _startLive() {
    this._stopLive();
    if (!this._storyId) return;
    if (typeof EventSource === "undefined" || SNAPSHOT_MODE) return;

    // Try SSE on a pinned run if available
    const pinnedRun = this._findPinnedRun();
    if (pinnedRun) {
      this._startRunSSE(pinnedRun);
    }

    // Poll mission control for session and event updates
    this._poll();
  }

  _findPinnedRun() {
    for (const session of this._sessions) {
      if (session.run_id) return session.run_id;
    }
    return null;
  }

  _eventId(event) {
    return event.event_id || event.event_hash || event.decision_id
      || (event.seq !== undefined ? `seq:${event.seq}` : JSON.stringify(event));
  }

  async _refreshDecisions(runId) {
    if (!runId) { this._decisions = []; return; }
    try {
      const response = await api(`/api/runs/${encodeURIComponent(runId)}/memory`);
      const incoming = response.data?.decisions || [];
      const byEventId = new Map(
        this._decisions.map((decision) => [this._eventId(decision), decision]),
      );
      for (const decision of incoming) {
        byEventId.set(this._eventId(decision), decision);
      }
      this._decisions = [...byEventId.values()].sort((left, right) => {
        const leftSeq = left.ledger_coordinates?.result_seq ?? 0;
        const rightSeq = right.ledger_coordinates?.result_seq ?? 0;
        return leftSeq - rightSeq || String(left.decision_id).localeCompare(String(right.decision_id));
      });
    } catch (_err) {
      // Decision basis is additive; the activity stream remains usable without it.
    }
  }

  _startRunSSE(runId) {
    if (this._sse) { this._sse.close(); this._sse = null; }
    this._sseReconnecting = false;
    this._sseSeenEventIds = new Set();
    // Record existing event seqs so reconnect snapshots don't duplicate
    for (const event of [...this._events, ...this._decisions]) {
      this._sseSeenEventIds.add(this._eventId(event));
    }
    this._sse = new EventSource(`/api/runs/${encodeURIComponent(runId)}/events`);

    // Snapshot-then-tail reconnect (WLA-34-05): the server sends a
    // snapshot event on every connect.  On reconnect, show "catching
    // up" until the snapshot arrives, then refresh state.
    this._sse.addEventListener("snapshot", () => {
      if (this._sseReconnecting) {
        this._sseReconnecting = false;
        this._hideCatchingUp();
        // Refresh from mission control to rebuild state
        this._refreshFromMc();
      }
    });

    this._sse.addEventListener("ledger", (ev) => {
      // A new ledger event arrived; debounce a refresh
      if (this._refreshTimer) return;
      this._refreshTimer = setTimeout(() => {
        this._refreshTimer = null;
        this._refreshFromMc();
      }, 500);
    });
    this._sse.onopen = () => {
      // If we had events before, this is a reconnect
      if (this._sseSeenEventIds.size > 0) {
        this._sseReconnecting = true;
        this._showCatchingUp();
      }
    };
    this._sse.onerror = () => {
      // SSE failed; fall back to polling only
      if (this._sse) { this._sse.close(); this._sse = null; }
      this._hideCatchingUp();
    };
  }

  _showCatchingUp() {
    if (!this._container) return;
    if (this._container.querySelector(".session-catching-up")) return;
    const banner = document.createElement("div");
    banner.className = "session-catching-up dw-catching-up";
    banner.setAttribute("role", "status");
    banner.setAttribute("aria-live", "polite");
    banner.textContent = "Catching up...";
    this._container.prepend(banner);
  }

  _hideCatchingUp() {
    if (!this._container) return;
    const banner = this._container.querySelector(".session-catching-up");
    if (banner) banner.remove();
  }

  _poll() {
    if (this._pollTimer) { clearTimeout(this._pollTimer); this._pollTimer = null; }
    this._pollTimer = setTimeout(async () => {
      if (!this._storyId) return;
      await this._refreshFromMc();
      this._poll();
    }, 5000);
  }

  async _refreshFromMc() {
    if (!this._storyId) return;
    try {
      const mcRes = await api("/api/missioncontrol?tail=40");
      const pins = mcRes.data.pins || {};
      const pinned = pins[this._storyId] || [];

      const sessionsChanged = JSON.stringify(pinned) !== JSON.stringify(this._sessions);
      this._sessions = pinned;
      await this._refreshDecisions(this._findPinnedRun());

      const allEvents = mcRes.data.events || [];
      const storyEvents = allEvents.filter(
        (ev) => ev.story_id === this._storyId || ev.detail?.story_id === this._storyId
      );

      const seenEventIds = new Set(this._events.map((event) => this._eventId(event)));
      const newEvents = storyEvents.filter(
        (event) => !seenEventIds.has(this._eventId(event))
      );

      if (newEvents.length) {
        this._events = this._events.concat(newEvents);
        if (this._events.length > this._maxEvents) {
          this._events = this._events.slice(-this._maxEvents);
        }
      }

      // WLA-34-04: refresh pending requests on poll
      try {
        const ntfRes = await api("/api/notifications");
        if (window.DW._askResume) {
          window.DW._askResume.loadFromNotifications(
            (ntfRes.data || {}).notifications || []
          );
        }
      } catch (_ntfErr) {}

      this._detectNeedsYou();

      if (sessionsChanged || newEvents.length) {
        this._mount();

        // If a new run appeared, start SSE for it
        const currentRun = this._findPinnedRun();
        if (currentRun && !this._sse) {
          this._startRunSSE(currentRun);
        }
      }
    } catch (_err) {
      // Polling failure is silent; retry next interval
    }
  }

  _stopLive() {
    if (this._sse) { this._sse.close(); this._sse = null; }
    if (this._pollTimer) { clearTimeout(this._pollTimer); this._pollTimer = null; }
    if (this._refreshTimer) { clearTimeout(this._refreshTimer); this._refreshTimer = null; }
    this._sseReconnecting = false;
    this._sseSeenEventIds = null;
    this._hideCatchingUp();
  }
}

/* ── board integration ─────────────────────────────────────────────── */

function wireSessionPanelClicks() {
  const board = document.querySelector(".board");
  if (!board) return;

  board.addEventListener("click", (event) => {
    const link = event.target.closest && event.target.closest(".bcard-top a");
    if (!link) return;

    // Extract story ID and slug from the link href
    const href = link.getAttribute("href") || "";
    const match = href.match(/#\/p\/([^/]+)\/s\/([^/]+)/);
    if (!match) return;

    event.preventDefault();
    const slug = decodeURIComponent(match[1]);
    const storyId = decodeURIComponent(match[2]);

    if (!window.DW._sessionPanel) {
      window.DW._sessionPanel = new SessionPanel();
    }

    const panel = window.DW._sessionPanel;

    // Toggle: if clicking the same story, close; otherwise open the new one
    if (panel.isOpen() && panel.storyId() === storyId) {
      panel.close();
      if (window.DW._layout) window.DW._layout.close("session");
    } else {
      if (window.DW._layout) window.DW._layout.open("session");
      panel.open(storyId, slug);
    }
  });
}

window.DW.SessionPanel = SessionPanel;
window.DW.wireSessionPanelClicks = wireSessionPanelClicks;
