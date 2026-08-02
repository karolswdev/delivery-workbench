"use strict";

/* ── Agent memory pane (WLA-35-06) ─────────────────────────────────────
 * Read-only view over the frozen memory documents saved for a bounded run
 * or program. Memory is advisory: seeing a record here never starts work,
 * permits an action, or replaces evidence.                              */

window.DW = window.DW || {};

(function () {
  const GROUP_LABELS = {
    "recalled": "Available to the agent",
    "used-as-basis": "Referenced by a decision",
    "written-back": "Written after completion",
    "superseded": "Superseded records",
  };

  const REFUSAL_COPY = {
    missing: {
      heading: "No saved memory was found",
      message: "This work has no saved memory to show. It may have been created before memory recording was available.",
    },
    stale: {
      heading: "Saved memory is out of date",
      message: "The saved memory no longer matches the frozen source. It is not shown because the source changed.",
    },
    tampered: {
      heading: "Saved memory did not pass its integrity check",
      message: "Nothing from this memory is shown because the saved record no longer matches its verified identity.",
    },
    malformed: {
      heading: "Saved memory could not be read safely",
      message: "The saved memory has an unsupported or incomplete shape, so no records are shown.",
    },
  };

  function unique(items, keyFor) {
    const seen = new Map();
    for (const item of items || []) {
      const key = keyFor(item);
      if (!seen.has(key)) {
        seen.set(key, { ...item, _audiences: item.audience ? [item.audience] : [] });
      } else if (item.audience) {
        const current = seen.get(key);
        if (!current._audiences.includes(item.audience)) current._audiences.push(item.audience);
      }
    }
    return [...seen.values()];
  }

  function itemKey(item) {
    return item.item_id || item.record_hash || item.writeback_id
      || `${item.source_kind || "record"}:${item.source_ref || JSON.stringify(item)}`;
  }

  function plainLabel(value) {
    return String(value || "record").replaceAll("_", " ").replaceAll("-", " ");
  }

  function capital(value) {
    const text = plainLabel(value);
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : "Unknown";
  }

  function sourceMix(items) {
    const counts = new Map();
    for (const item of items) {
      const label = plainLabel(item.source_kind || item.record_kind || item.origin_kind || "record");
      counts.set(label, (counts.get(label) || 0) + 1);
    }
    return [...counts.entries()].sort(([left], [right]) => left.localeCompare(right))
      .map(([label, count]) => `${label} ${count}`).join(", ") || "None";
  }

  function sourceText(item) {
    const coordinates = item.ledger_coordinates || {};
    return coordinates.receipt_path || coordinates.path || item.writeback_id
      || item.record_hash || item.source_ref || "Source unavailable";
  }

  function copyableIdentifierHtml(value, label = "identifier") {
    const text = String(value || "Source unavailable");
    return `<span class="copyable-id"><code title="${esc(text)}">${esc(text)}</code><button type="button" class="copy-id-action" data-copy-text="${esc(text)}" aria-label="Copy ${esc(label)}">Copy</button></span>`;
  }

  function technicalItem(item) {
    const { _audiences, ...saved } = item;
    return saved;
  }

  function supersessionText(item) {
    if (item.superseded_by) return "Superseded by a newer saved record";
    if (item.supersedes) return "Supersedes an earlier saved record";
    if (item.memory_state === "superseded" || item.delivery_state === "superseded") {
      return "Superseded";
    }
    return "Current";
  }

  function factualSummary(item, group) {
    if (item.summary) return item.summary;
    if (item.factual_summary) return item.factual_summary;
    const document = item.document || {};
    const stories = document.story_ids || item.story_ids || [];
    if (group === "written-back" || group === "superseded") {
      const subject = stories.length ? ` for ${stories.join(", ")}` : "";
      return `${capital(document.terminal_state || item.terminal_state || "completed")} outcome${subject}.`;
    }
    return "Saved memory record.";
  }

  function confidenceText(item) {
    if (item.confidence !== undefined && item.confidence !== null) {
      return capital(item.confidence);
    }
    if (item.memory_state === "confirmed") return "Confirmed";
    if (item.memory_state === "candidate") return "Candidate";
    return "Not recorded";
  }

  function reasonsFor(item, group) {
    if (Array.isArray(item.match_reasons) && item.match_reasons.length) {
      return item.match_reasons;
    }
    const decisionRefs = item.document?.decision_refs || item.decision_refs || [];
    if (group === "used-as-basis" && decisionRefs.length) {
      return decisionRefs.map((reference) => `Decision reference: ${reference}`);
    }
    if (group === "written-back" || group === "superseded") {
      return ["Saved only after the work reached a completed state"];
    }
    return ["No match reason was recorded"];
  }

  class MemoryPanel {
    constructor() {
      this._kind = "";
      this._id = "";
      this._document = null;
      this._loading = false;
      this._error = "";
      this._panel = null;
      this._content = null;
      this._controller = null;
      this._returnElement = null;
      this._returnSelector = "";
      this._route = "";
      this._selectedDecisionId = "";
      this._decisionByEventId = new Map();
      this._sse = null;
    }

    isOpen() {
      return Boolean(this._kind && this._id && this._panel && !this._panel.hidden);
    }

    open(kind, id, opener) {
      if (!['run', 'program'].includes(kind) || !id) return;
      const wasOpen = this.isOpen();
      if (!wasOpen) {
        const requestedTrigger = opener instanceof Element ? opener : document.activeElement;
        const trigger = requestedTrigger?.closest?.(".needs-you-dropdown")
          ? document.querySelector(".needs-you-pill") : requestedTrigger;
        this._returnElement = trigger instanceof Element ? trigger : null;
        this._returnSelector = typeof focusSelector === "function" ? focusSelector(trigger) : "";
        this._route = location.hash;
        if (typeof rememberReturnFocus === "function") {
          rememberReturnFocus("memory-panel", trigger);
        }
      }
      if (this._controller) this._controller.abort();
      this._kind = kind;
      this._id = id;
      this._document = null;
      this._loading = true;
      this._error = "";
      this._selectedDecisionId = "";
      this._decisionByEventId = new Map();
      this._ensurePanel();
      this._panel.hidden = false;
      this._panel.setAttribute("aria-hidden", "false");
      this._render();
      focusElement(this._panel.querySelector(".memory-close"));
      if (window.SNAPSHOT_MODE && SNAPSHOT_MEMORY_SCENARIO) this._loadSnapshot(SNAPSHOT_MEMORY_SCENARIO);
      else this._load();
    }

    close() {
      if (!this.isOpen()) return;
      if (this._controller) this._controller.abort();
      this._controller = null;
      if (this._sse) this._sse.close();
      this._sse = null;
      this._panel.hidden = true;
      this._panel.setAttribute("aria-hidden", "true");
      this._kind = "";
      this._id = "";
      this._document = null;
      this._loading = false;
      this._error = "";

      const returnElement = this._returnElement;
      const returnSelector = this._returnSelector;
      this._returnElement = null;
      this._returnSelector = "";
      this._route = "";
      if (returnSelector && typeof restoreReturnFocus === "function") {
        restoreReturnFocus("memory-panel", returnSelector);
      } else if (returnElement?.isConnected && typeof returnElement.focus === "function") {
        focusElement(returnElement);
      } else if (returnSelector) {
        focusElement(document.querySelector(returnSelector));
      }
    }

    _ensurePanel() {
      if (this._panel) return;
      const panel = document.createElement("dw-panel");
      panel.className = "memory-panel";
      panel.setAttribute("title", "Memory");
      panel.setAttribute("role", "dialog");
      panel.setAttribute("aria-modal", "false");
      panel.setAttribute("aria-label", "Agent memory");
      panel.setAttribute("aria-hidden", "true");
      panel.setAttribute("tabindex", "-1");
      panel.hidden = true;

      const content = document.createElement("div");
      content.className = "memory-panel-content";
      panel.appendChild(content);
      document.body.appendChild(panel);
      this._panel = panel;
      this._content = content;

      panel.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        event.preventDefault();
        this.close();
      });
    }

    _loadSnapshot(scenario) {
      this._loading = false;
      if (scenario === "error") {
        this._error = "The saved memory service is unavailable. Retry when the repository service is ready.";
        this._document = null;
        this._render();
        return;
      }
      this._error = "";
      const groups = {
        recalled: [], "used-as-basis": [], "written-back": [], superseded: [], excluded: [],
      };
      const decisions = [];
      if (scenario === "rich") {
        const recordHash = "9c7d4e8f1029384756abcdef0123456789abcdef0123456789abcdef01234567";
        const receipt = "receipt-run-2026-08-01-9c7d4e8f1029384756abcdef0123456789abcdef";
        groups.recalled.push({
          recall_id: "recall-fixture-001", source_kind: "lesson", record_hash: recordHash,
          summary: "A prior delivery found that narrow layouts need bounded provenance.",
          confidence: "confirmed", match_reasons: ["story term overlap", "shared file path"],
          ledger_coordinates: { receipt_path: `pm/knowledge/earned/${receipt}.json` },
          memory_state: "confirmed", audience: "implementer",
        });
        groups["used-as-basis"].push({ ...groups.recalled[0], audience: "verifier" });
        decisions.push({
          event_id: "event-fixture-001", decision_id: "decision-fixture-001",
          decision_kind: "quality gate", outcome: "continue with bounded layout",
          basis_type: "mechanical", reason_code: "viewport-contract-met",
          rule_ref: "workbench-no-horizontal-overflow", score_ref: "",
          memory_refs: ["recall-fixture-001"], dissent_refs: [],
          originating_receipt_ref: receipt, resulting_ledger_event: receipt,
          origin_kind: "run", origin: "run-fixture-memory-glass",
          ledger_coordinates: { result_seq: 7 },
        });
      }
      this._reconcileDocument({
        kind: "delivery-workbench-memory-view", schema_version: 1, status: "ok", groups, decisions,
      });
      this._render();
    }

    async _load() {
      const controller = new AbortController();
      this._controller = controller;
      const kind = this._kind;
      const id = this._id;
      const path = `/api/${kind === "program" ? "programs" : "runs"}/${encodeURIComponent(id)}/memory`;
      try {
        const response = await fetch(path, { cache: "no-store", signal: controller.signal });
        const envelope = await response.json();
        if (controller.signal.aborted || this._kind !== kind || this._id !== id) return;
        const document = envelope?.data || envelope;
        if (!document || (!response.ok && document.status !== "refused")) {
          const issue = envelope?.issues?.[0] || `Memory could not be read (${response.status})`;
          throw new Error(issue);
        }
        this._reconcileDocument(document);
        this._loading = false;
        this._error = "";
        this._startSse(kind, id);
      } catch (error) {
        if (error.name === "AbortError") return;
        this._document = null;
        this._loading = false;
        this._error = error.message || "Memory could not be read";
      } finally {
        if (this._controller === controller) this._controller = null;
        if (this._kind === kind && this._id === id) this._render();
      }
    }

    _reconcileDocument(document) {
      const decisions = Array.isArray(document?.decisions) ? document.decisions : [];
      for (const decision of decisions) {
        const eventId = decision.event_id || decision.decision_id;
        if (eventId) this._decisionByEventId.set(eventId, decision);
      }
      this._document = {
        ...document,
        decisions: [...this._decisionByEventId.values()].sort((left, right) => {
          const leftSeq = left.ledger_coordinates?.result_seq ?? 0;
          const rightSeq = right.ledger_coordinates?.result_seq ?? 0;
          return leftSeq - rightSeq || String(left.decision_id).localeCompare(String(right.decision_id));
        }),
      };
    }

    _startSse(kind, id) {
      if (typeof EventSource === "undefined" || window.SNAPSHOT_MODE || this._sse) return;
      const collection = kind === "program" ? "programs" : "runs";
      this._sse = new EventSource(`/api/${collection}/${encodeURIComponent(id)}/events`);
      const refresh = () => {
        if (this._controller || this._kind !== kind || this._id !== id) return;
        this._load();
      };
      this._sse.addEventListener("snapshot", refresh);
      this._sse.addEventListener("ledger", refresh);
      this._sse.addEventListener("program", refresh);
    }

    _render() {
      if (!this._content) return;
      const hadFocus = this._panel.contains(document.activeElement);
      this._content.innerHTML = `
        <div class="memory-context">
          <div>
            <span class="memory-eyebrow">${esc(this._kind === "program" ? "Multi-phase program" : "Bounded run")}</span>
            <h2 id="memory-panel-title">What the agent could know</h2>
            ${copyableIdentifierHtml(this._id, this._kind === "program" ? "program identifier" : "run identifier")}
          </div>
          <button type="button" class="memory-close" aria-label="Close memory pane">Close</button>
        </div>
        <p class="memory-boundary">Memory is advisory. A recalled record never caused or permitted an action, started work, or replaced evidence.</p>
        ${this._bodyHtml()}`;
      this._wire();
      if (hadFocus) {
        const selected = this._selectedDecisionId
          ? this._content.querySelector(
            `.decision-basis-select[data-decision-id="${CSS.escape(this._selectedDecisionId)}"]`,
          ) : null;
        focusElement(selected || this._content.querySelector(".memory-close"));
      }
    }

    _wire() {
      this._content.querySelector(".memory-close")?.addEventListener("click", () => this.close());
      this._content.querySelector(".memory-retry")?.addEventListener("click", () => {
        this._loading = true;
        this._error = "";
        this._render();
        this._load();
      });
      for (const button of this._content.querySelectorAll(".decision-basis-select")) {
        button.addEventListener("click", () => {
          this._selectedDecisionId = button.dataset.decisionId || "";
          this._render();
          focusElement(this._content.querySelector(
            `.decision-basis-select[data-decision-id="${CSS.escape(this._selectedDecisionId)}"]`,
          ));
        });
      }
    }

    _bodyHtml() {
      if (this._loading) {
        return '<div class="memory-loading" role="status"><dw-skeleton lines="7"></dw-skeleton><p>Reading saved memory...</p></div>';
      }
      if (this._error) {
        return `<div class="memory-load-error" role="alert"><strong>Memory could not be loaded.</strong><p>${esc(this._error)}</p><button type="button" class="memory-retry">Retry</button></div>`;
      }
      if (!this._document) return "";
      if (this._document.status === "refused") return this._refusalHtml(this._document);

      const groups = this._normalizedGroups(this._document.groups || {});
      const included = unique(
        [...groups.recalled, ...groups["used-as-basis"]], itemKey,
      );
      const total = included.length + groups["written-back"].length + groups.superseded.length;
      const summary = this._summaryHtml(groups, included);
      const meanings = this._meaningHtml();
      const timeline = this._decisionTimelineHtml(this._document.decisions || []);
      if (!total && !groups.excluded.length && !this._document.decisions?.length) {
        return `${summary}${meanings}${timeline}${this._emptyHtml()}`;
      }
      return `${summary}${meanings}${timeline}${this._groupsHtml(groups)}`;
    }

    _normalizedGroups(raw) {
      return {
        recalled: unique(raw.recalled || [], itemKey),
        "used-as-basis": unique(raw["used-as-basis"] || [], itemKey),
        "written-back": unique(raw["written-back"] || [], itemKey),
        superseded: unique(raw.superseded || [], itemKey),
        excluded: unique(raw.excluded || [], (item) => `${item.source_kind}:${item.source_ref}:${item.reason}`),
      };
    }

    _summaryHtml(groups, included) {
      const writebackState = groups["written-back"].length
        ? `${groups["written-back"].length} saved after completion`
        : groups.superseded.length ? "Only superseded records remain" : "Nothing written after completion";
      return `<section class="memory-summary" aria-labelledby="memory-summary-title">
        <div class="memory-section-head"><div><span>Summary</span><h3 id="memory-summary-title">Memory at a glance</h3></div><dw-badge variant="ok" count="Read-only"></dw-badge></div>
        <dl class="memory-summary-grid">
          <div><dt>Recall time</dt><dd>Before agent dispatch</dd></div>
          <div><dt>Freshness</dt><dd>Frozen source verified</dd></div>
          <div><dt>Included</dt><dd>${esc(included.length)}</dd></div>
          <div><dt>Excluded</dt><dd>${esc(groups.excluded.length)}</dd></div>
          <div><dt>Sources</dt><dd>${esc(sourceMix(included))}</dd></div>
          <div><dt>Writeback</dt><dd>${esc(writebackState)}</dd></div>
        </dl>
      </section>`;
    }

    _meaningHtml() {
      return `<section class="memory-meaning" aria-labelledby="memory-meaning-title">
        <div class="memory-section-head"><div><span>How to read this</span><h3 id="memory-meaning-title">Availability is not authority</h3></div></div>
        <div class="memory-meaning-grid">
          <article><strong>Available to the agent</strong><p>Present in frozen context before work began. This does not show that a decision used it.</p></article>
          <article><strong>Referenced by a decision</strong><p>Named in a saved decision record. This records a reference, not private reasoning or permission.</p></article>
          <article><strong>Written after completion</strong><p>Saved only after the work ended. It could not have affected the completed work.</p></article>
        </div>
      </section>`;
    }

    _decisionTimelineHtml(decisions) {
      const authorityMeaning = {
        "mechanical": "Computed from declared rules and saved checks",
        "agent-reported": "A model judgment recorded in a bounded verdict",
        "panel-derived": "Derived by the declared council protocol",
        "operator-supplied": "Supplied through a typed operator response",
      };
      if (!decisions.length) {
        return `<section class="decision-basis-timeline" aria-labelledby="decision-basis-title">
          <div class="memory-section-head"><div><span>Decision basis</span><h3 id="decision-basis-title">What affected the next step</h3></div><dw-badge count="0"></dw-badge></div>
          <p class="decision-basis-empty">No saved decision basis is available yet.</p>
        </section>`;
      }
      return `<section class="decision-basis-timeline" aria-labelledby="decision-basis-title">
        <div class="memory-section-head"><div><span>Decision basis</span><h3 id="decision-basis-title">What affected the next step</h3></div><dw-badge count="${esc(decisions.length)}"></dw-badge></div>
        <p class="decision-authority-note">Authority labels are intentionally distinct: mechanical checks are not model or council judgments.</p>
        <ol class="decision-basis-list">${decisions.map((decision) => {
          const selected = decision.decision_id === this._selectedDecisionId;
          const origin = decision.originating_receipt_ref || decision.resulting_ledger_event;
          const sourceRoute = decision.origin_kind === "program"
            ? `#/live/program/${encodeURIComponent(decision.origin)}/technical`
            : `#/live/run/${encodeURIComponent(decision.origin)}/technical`;
          return `<li class="decision-basis-item basis-${esc(decision.basis_type)}">
            <button type="button" class="decision-basis-select" data-decision-id="${esc(decision.decision_id)}" aria-pressed="${selected ? "true" : "false"}">
              <span class="decision-basis-kind">${esc(capital(decision.decision_kind))}</span>
              <strong>${esc(decision.outcome)}</strong>
              <span class="decision-authority-label">${esc(decision.basis_type)}</span>
              <small>${esc(authorityMeaning[decision.basis_type] || "Saved structured basis")}</small>
            </button>
            ${selected ? `<div class="decision-basis-detail" role="region" aria-label="Selected decision basis">
              <dl><div><dt>Reason code</dt><dd><code>${esc(decision.reason_code)}</code></dd></div>
              <div><dt>Rule or score</dt><dd><code>${esc(decision.rule_ref || decision.score_ref)}</code></dd></div>
              <div><dt>Recalled memory</dt><dd>${esc(decision.memory_refs.length ? decision.memory_refs.join(", ") : "None referenced")}</dd></div>
              <div><dt>Dissent</dt><dd>${esc(decision.dissent_refs.length ? decision.dissent_refs.join(", ") : "None recorded")}</dd></div>
              <div><dt>Saved record</dt><dd>${copyableIdentifierHtml(origin, "saved record identifier")}</dd></div></dl>
              <a class="decision-origin-link" href="${sourceRoute}" data-source-ref="${esc(origin)}">Open saved source</a>
            </div>` : ""}
          </li>`;
        }).join("")}</ol>
      </section>`;
    }

    _groupsHtml(groups) {
      let html = "";
      for (const name of ["recalled", "used-as-basis", "written-back", "superseded"]) {
        const items = groups[name];
        if (!items.length) continue;
        html += `<section class="memory-group" aria-labelledby="memory-group-${name}">
          <div class="memory-section-head"><div><span>Saved records</span><h3 id="memory-group-${name}">${esc(GROUP_LABELS[name])}</h3></div><dw-badge count="${esc(items.length)}"></dw-badge></div>
          <div class="memory-card-grid">${items.map((item) => this._cardHtml(item, name)).join("")}</div>
        </section>`;
      }
      if (groups.excluded.length) html += this._excludedHtml(groups.excluded);
      return html;
    }

    _cardHtml(item, group) {
      const reasons = reasonsFor(item, group);
      const audiences = item._audiences || [];
      const selected = (this._document?.decisions || []).find(
        (decision) => decision.decision_id === this._selectedDecisionId,
      );
      const highlighted = Boolean(
        selected && selected.memory_refs.includes(item.recall_id),
      );
      return `<dw-card class="memory-card${highlighted ? " decision-memory-highlight" : ""}" data-memory-group="${esc(group)}" data-recall-id="${esc(item.recall_id || "")}">
        <div class="memory-card-head">
          <dw-badge variant="default" count="${esc(capital(item.source_kind || item.origin_kind || "record"))}"></dw-badge>
          <span class="memory-confidence"><strong>Confidence</strong> ${esc(confidenceText(item))}</span>
        </div>
        <p class="memory-factual-summary">${esc(factualSummary(item, group))}</p>
        <dl class="memory-card-facts">
          <div><dt>Why recalled</dt><dd><ul>${reasons.map((reason) => `<li>${esc(plainLabel(reason))}</li>`).join("")}</ul></dd></div>
          <div><dt>Source</dt><dd>${copyableIdentifierHtml(sourceText(item), "source identifier")}</dd></div>
          <div><dt>Supersession</dt><dd>${esc(supersessionText(item))}</dd></div>
          ${audiences.length ? `<div><dt>Available to</dt><dd>${esc(audiences.map(plainLabel).join(", "))}</dd></div>` : ""}
        </dl>
        <dw-fold label="Technical details"><pre>${esc(JSON.stringify(technicalItem(item), null, 2))}</pre></dw-fold>
      </dw-card>`;
    }

    _excludedHtml(items) {
      return `<section class="memory-group memory-excluded" aria-labelledby="memory-excluded-title">
        <div class="memory-section-head"><div><span>Not sent to the agent</span><h3 id="memory-excluded-title">Excluded records</h3></div><dw-badge count="${esc(items.length)}"></dw-badge></div>
        <div class="memory-exclusion-list">${items.map((item) => `<article>
          <div><strong>${esc(capital(item.source_kind || "record"))}</strong><span>${esc(plainLabel(item.reason || "not selected"))}</span></div>
          ${copyableIdentifierHtml(item.source_ref || "Source unavailable", "source identifier")}
          <dw-fold label="Technical details"><pre>${esc(JSON.stringify(technicalItem(item), null, 2))}</pre></dw-fold>
        </article>`).join("")}</div>
      </section>`;
    }

    _refusalHtml(document) {
      const refusal = document.refusal || { reason: "malformed", message: "No typed refusal was returned." };
      const copy = REFUSAL_COPY[refusal.reason] || REFUSAL_COPY.malformed;
      return `<div class="memory-state memory-state-${esc(refusal.reason)}">
        <dw-empty-state heading="${esc(copy.heading)}" message="${esc(copy.message)}"></dw-empty-state>
        <dw-fold label="Technical details"><pre>${esc(JSON.stringify(refusal, null, 2))}</pre></dw-fold>
      </div>`;
    }

    _emptyHtml() {
      const technical = {
        kind: this._document.kind,
        schema_version: this._document.schema_version,
        status: this._document.status,
        refusal: this._document.refusal,
      };
      return `<div class="memory-state memory-state-empty">
        <dw-empty-state heading="No memory records yet" message="This work has a verified memory record, but it contains no included, excluded, decision, or completion entries."></dw-empty-state>
        <dw-fold label="Technical details"><pre>${esc(JSON.stringify(technical, null, 2))}</pre></dw-fold>
      </div>`;
    }
  }

  function panel() {
    if (!window.DW._memoryPanel) window.DW._memoryPanel = new MemoryPanel();
    return window.DW._memoryPanel;
  }

  function openMemoryPanel(kind, id, opener) {
    panel().open(kind, id, opener);
  }

  function openMemorySnapshot() {
    if (!window.SNAPSHOT_MODE || !SNAPSHOT_MEMORY_SCENARIO) return;
    panel().open(
      "run",
      "run-memory-glass-9c7d4e8f1029384756abcdef0123456789abcdef",
      document.querySelector("h1") || app,
    );
  }

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest?.("[data-memory-open]");
    if (!trigger || trigger.closest(".cp-overlay")) return;
    const kind = trigger.dataset.memoryKind;
    const id = trigger.dataset.memoryId;
    if (!kind || !id) return;
    event.preventDefault();
    openMemoryPanel(kind, id, trigger);
  });

  window.addEventListener("hashchange", () => {
    if (window.DW._memoryPanel?.isOpen()) window.DW._memoryPanel.close();
  });

  window.DW.MemoryPanel = MemoryPanel;
  window.DW.openMemoryPanel = openMemoryPanel;
  window.DW.openMemorySnapshot = openMemorySnapshot;
})();
