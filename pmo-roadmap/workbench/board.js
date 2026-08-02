"use strict";

/* ── board view ───────────────────────────────────────────────────────
 * Operator-style flat board with "Backlog", "In progress", "Needs you",
 * and "Done" columns, plus a toggle to fall back to the legacy
 * phase-lane layout.  Cards are enriched with execution state,
 * attention badges, evidence indicators, and relative timestamps.
 * Clicking a card title opens a slide-over session panel alongside
 * the board instead of navigating away. */

const BOARD_STATUSES = ["backlog", "ready", "in-progress", "blocked", "on-hold", "done"];
const HOLD_COLUMNS   = ["on-hold"];

/* ── time helpers ───────────────────────────────────────── */

function _relativeTime(ts) {
  if (!ts) return "";
  const then = new Date(ts);
  if (isNaN(then)) return "";
  const diff = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (diff < 60)   return "just now";
  if (diff < 3600) return Math.floor(diff / 60) + "m ago";
  if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
  return Math.floor(diff / 86400) + "d ago";
}

/* ── flat column assignment ─────────────────────────────── */

const FLAT_BACKLOG    = "flat-backlog";
const FLAT_INPROGRESS = "flat-inprogress";
const FLAT_NEEDSYOU   = "flat-needsyou";
const FLAT_DONE       = "flat-done";

function flatColumn(card, ortho) {
  const attn = (ortho && ortho.attention) || "none";
  if (attn !== "none") return FLAT_NEEDSYOU;
  const st = card.status;
  if (st === "done" || st === "complete" || st === "closed" || st === "shipped") return FLAT_DONE;
  if (st === "in-progress" || st === "blocked" || st === "on-hold" || st === "paused") return FLAT_INPROGRESS;
  return FLAT_BACKLOG;
}

/* ── card rendering (shared between flat and phase views) ─ */

function _boardStatusLabel(status) {
  const labels = {
    backlog: "Backlog", ready: "Ready", "in-progress": "In progress",
    blocked: "Blocked", "on-hold": "On hold", paused: "On hold",
    done: "Done", complete: "Done", closed: "Done", shipped: "Done",
  };
  return labels[status] || status;
}

function boardCard(slug, lane, card, orthoState) {
  const parked  = PARKED_COLUMNS.includes(card.status) || card.status === "paused";
  const movable = !lane.closed && !lane.paused;
  const ortho   = orthoState || {};
  const exec    = ortho.execution || "stopped";
  const attn    = ortho.attention || "none";
  const auth    = ortho.authority || "none";
  const lastTs  = ortho.last_activity || ortho.updated_at || "";
  const statusLabel = _boardStatusLabel(card.status);
  const attnLabel = attn === "waiting-for-input" ? "Input needed"
    : attn === "decision-pending" ? "Decision needed"
    : attn !== "none" ? "Needs attention" : "";
  const attnBadge = attn !== "none"
    ? `<span class="bcard-attention">${esc(attnLabel)}</span>`
    : "";
  const context = (attn !== "none" && ortho.question)
    ? ortho.question
    : parked ? `Waiting: ${card.note || "no reason recorded"}` : "";
  const timeLabel = _relativeTime(lastTs);
  const detailLabel = [
    `Execution ${exec}`,
    auth !== "none" ? `authority ${auth}` : "",
    card.evidence_exists ? "proof saved" : "",
    timeLabel,
  ].filter(Boolean).join(", ");

  return `
    <dw-card class="bcard st-${esc(card.status)}" ${movable ? 'draggable="true"' : ""}
         data-story="${esc(card.story_id)}" data-phase="${lane.number}"
         data-status="${esc(card.status)}" data-evidence="${card.evidence_exists ? 1 : 0}"
         data-execution="${esc(exec)}" data-attention="${esc(attn)}" data-authority="${esc(auth)}"
         aria-label="${esc(card.story_id)}: ${esc(card.title)}. Status ${esc(statusLabel)}. ${esc(detailLabel)}${attn !== "none" ? ". Attention: " + esc(attn) : ""}">
      <a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(card.story_id)}" class="bcard-link">
        <div class="bcard-top">
          <span class="bcard-id ops-label">${esc(card.story_id)}</span>
          ${attnBadge}
        </div>
        <div class="bcard-title">${esc(card.title)}</div>
        <div class="bcard-meta">Phase ${esc(String(lane.number))} · ${esc(statusLabel)}</div>
        ${context ? `<p class="bcard-context">${esc(context)}</p>` : ""}
      </a>
      ${movable ? `<div slot="footer" class="bcard-actions" role="group" aria-label="Actions for ${esc(card.story_id)}">
        <dw-button variant="ghost" class="bmove" data-board-move>Move</dw-button>
        <dw-button variant="ghost" class="bmove" data-board-park>Park</dw-button>
      </div>` : ""}
    </dw-card>`;
}

/* ── flat board rendering ─────────────────────────────────── */

function flatBoardCards(slug, model, orthoMap) {
  const buckets = {
    [FLAT_BACKLOG]:    [],
    [FLAT_INPROGRESS]: [],
    [FLAT_NEEDSYOU]:   [],
    [FLAT_DONE]:       [],
  };

  for (const lane of model.phases) {
    for (const col of model.columns) {
      for (const card of (lane.columns[col] || [])) {
        const ortho  = orthoMap[card.story_id] || {};
        const bucket = flatColumn(card, ortho);
        buckets[bucket].push({ card, lane, ortho });
      }
    }
  }
  return buckets;
}

function flatColumnHtml(slug, id, label, items, orthoMap, opts) {
  const collapsed   = opts && opts.collapsed;
  const collapseMax = opts && opts.collapseMax;
  const count       = items.length;
  const droppable   = 1;
  const activeClass = (opts && opts.activeWhenNonEmpty && count > 0) ? " flat-col-active" : "";

  let cardsHtml = "";
  let displayItems = items;
  let hiddenCount = 0;

  if (collapsed && collapseMax && count > collapseMax) {
    // Show last N items (most recent)
    displayItems = items.slice(-collapseMax);
    hiddenCount = count - collapseMax;
  }

  if (hiddenCount > 0) {
    cardsHtml += `<div class="flat-collapsed-count">${hiddenCount} more stor${hiddenCount === 1 ? "y" : "ies"} not shown</div>`;
  }

  cardsHtml += displayItems.map((entry) =>
    boardCard(slug, entry.lane, entry.card, orthoMap[entry.card.story_id])
  ).join("");

  const emptyLabel = id === FLAT_INPROGRESS ? "No stories in progress"
    : id === FLAT_NEEDSYOU ? "No stories need your attention"
    : id === FLAT_DONE ? "No completed stories yet" : "No stories waiting";
  return `
    <div class="bcol flat-col flat-col-${esc(id)}${count === 0 ? " bcol-empty flat-col-empty" : ""}${activeClass}" data-flat-col="${esc(id)}" data-droppable="${droppable}">
      <div class="bcol-head"><span class="bcol-label ops-label">${esc(label)}</span><span class="bcol-count ops-label">${count}</span></div>
      ${cardsHtml}
      ${count === 0 ? `<p class="bcol-empty-copy">${esc(emptyLabel)}</p>` : ""}
    </div>`;
}

function flatBoardHtml(slug, model, orthoMap) {
  const buckets = flatBoardCards(slug, model, orthoMap);
  const totalStories = Object.values(buckets).reduce((s, b) => s + b.length, 0);
  const inProgressCount = buckets[FLAT_INPROGRESS].length;
  const needsYouCount   = buckets[FLAT_NEEDSYOU].length;

  const cols = [
    flatColumnHtml(slug, FLAT_BACKLOG,    "Backlog",     buckets[FLAT_BACKLOG],    orthoMap, { collapsed: true, collapseMax: 5 }),
    flatColumnHtml(slug, FLAT_INPROGRESS, "In progress", buckets[FLAT_INPROGRESS], orthoMap, {}),
    flatColumnHtml(slug, FLAT_NEEDSYOU,   "Needs you",   buckets[FLAT_NEEDSYOU],   orthoMap, { activeWhenNonEmpty: true }),
    flatColumnHtml(slug, FLAT_DONE,       "Done",        buckets[FLAT_DONE],       orthoMap, { collapsed: true, collapseMax: 3 }),
  ];

  return { html: cols.join(""), totalStories, inProgressCount, needsYouCount };
}

/* ── legacy phase-lane rendering (unchanged logic) ──────── */

function boardLane(slug, columns, lane, orthoMap) {
  const droppable = !lane.closed && !lane.paused;
  const cols = columns.map((col) => {
    const count = lane.columns[col].length;
    return `
    <div class="bcol${count === 0 ? " bcol-empty" : ""}" data-col="${esc(col)}" data-phase="${lane.number}" data-droppable="${droppable ? 1 : 0}">
      <div class="bcol-head"><span class="bcol-label ops-label">${esc(col.replaceAll("-", " "))}</span><span class="bcol-count ops-label">${count}</span></div>
      ${lane.columns[col].map((card) => boardCard(slug, lane, card, orthoMap[card.story_id])).join("")}
      ${count === 0 ? '<p class="bcol-empty-copy">No stories here</p>' : ""}
    </div>`;
  }).join("");
  const uncovered = lane.story_count === 0 && lane.uncovered_story_files
    ? `<span class="sub">no story table — ${lane.uncovered_story_files} story file${lane.uncovered_story_files === 1 ? "" : "s"} on disk, unlisted</span>` : "";
  const head = `
    <div class="blane-title">
      <div>${lane.is_pointer ? '<span aria-label="current phase">Current · </span>' : ""}<a href="#/p/${encodeURIComponent(slug)}/ph/${lane.number}">Phase ${lane.number} · ${esc(lane.slug)}</a>
        ${lane.paused ? `<span class="pause-banner"><strong>Paused.</strong> ${esc(lane.pause_note || "No reason recorded")}</span>` : ""}
        ${lane.retired ? `<span class="sub">${lane.retired} retired row${lane.retired === 1 ? "" : "s"} not shown</span>` : ""}
        ${uncovered}</div>
      <div class="blane-actions" role="group" aria-label="Actions for phase ${lane.number}">
        <dw-button variant="primary" id="board-create-${lane.number}" data-board-create data-phase="${lane.number}" data-phase-name="${esc(lane.slug)}"${lane.paused ? " disabled" : ""}>Create story</dw-button>
        <dw-button variant="secondary" id="board-phase-${lane.number}" data-board-phase-action="${lane.paused ? "resume_phase" : "pause_phase"}" data-phase="${lane.number}" data-phase-name="${esc(lane.slug)}">${lane.paused ? "Resume phase" : "Pause phase"}</dw-button>
      </div>
    </div>`;
  if (lane.closed) {
    const allDone = lane.story_count > 0 && lane.done_count === lane.story_count;
    const summaryText = allDone
      ? `Phase ${lane.number} · ${esc(lane.slug)} — ${lane.story_count} stor${lane.story_count === 1 ? "y" : "ies"}, all done`
      : `Phase ${lane.number} · ${esc(lane.slug)} — closed, ${lane.done_count}/${lane.story_count} done`;
    return `
      <details class="blane closed" data-phase="${lane.number}">
        <summary>${summaryText}</summary>
        <div class="bcols">${cols}</div>
      </details>`;
  }
  return `
    <div class="blane${lane.paused ? " paused" : ""}" data-phase="${lane.number}" data-paused="${lane.paused ? 1 : 0}">
      <div class="blane-head">${head}</div>
      <div class="bcols">${cols}</div>
    </div>`;
}

/* ── helpers ──────────────────────────────────────────────── */

function focusBoardRegion(selector) {
  if (!SNAPSHOT_MODE) focusRegion(selector);
}

function boardNotice(text) {
  const out = document.getElementById("board-move");
  if (!out) return;
  out.innerHTML = `<dw-toast variant="error" dismissible duration="0"><strong>Nothing changed.</strong> ${esc(text)}</dw-toast>`;
  focusBoardRegion("#board-move dw-toast");
}

function boardMutationError(payload, status) {
  return (payload.data && payload.data.error)
    || (payload.issues && payload.issues[0])
    || `request refused (${status})`;
}

function boardPreviewFiles(files) {
  return files.filter((file) => file.changed || file.action === "create").map((file) => `
    <details class="filepreview" open>
      <summary>${badge(file.action === "create" ? "new file" : "changed", file.action === "create" ? "ok" : "in-progress")}
        <code>${esc(file.path)}</code></summary>
      ${file.action === "create" ? `<pre class="src">${esc(file.new_content || "")}</pre>`
        : `<pre class="diff">${diffHtml(file.diff || "")}</pre>`}
    </details>`).join("");
}

async function previewBoardMutation(out, intent, sentence) {
  out.innerHTML = stateHtml("Preparing the exact change…");
  try {
    const { status, body: payload } = await postJson("/api/mutations/preview", intent);
    if (status >= 400 || payload.ok === false) {
      out.innerHTML = `<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Preview refused. Nothing changed.</strong> ${esc(boardMutationError(payload, status))}</div>`;
      focusBoardRegion(`#${out.id} .board-refusal`);
      return;
    }
    const preview = payload.data;
    const reviewedIntent = { ...intent };
    out.innerHTML = `<section class="board-preview" aria-labelledby="board-preview-title" tabindex="-1">
      <div class="board-preview-head"><span>Review before applying</span><h2 id="board-preview-title">${esc(sentence)}</h2>
        ${badge("nothing written yet", "ok")}</div>
      <p>These are the exact saved-file changes this action would make.</p>
      ${boardPreviewFiles(preview.files)}
      <details class="board-preview-technical"><summary>Technical details</summary>
        <dl><div><dt>Mutation</dt><dd><code>${esc(intent.kind)}</code></dd></div>
          <div><dt>Single-use preview fingerprint</dt><dd><code>${esc(preview.fingerprint)}</code></dd></div></dl>
      </details>
      <div class="board-preview-actions">
        <button type="button" class="applybtn" id="board-apply">Apply this exact change</button>
        <button type="button" id="board-preview-cancel">Cancel</button>
      </div>
      <div id="board-apply-result"></div>
    </section>`;
    enhanceSemantics(out);
    focusBoardRegion(".board-preview");
    document.getElementById("board-preview-cancel").addEventListener("click", () => {
      out.closest("#board-move").innerHTML = "";
      restoreReturnFocus("board-action");
    });
    document.getElementById("board-apply").addEventListener("click", async (event) => {
      const button = event.currentTarget;
      const result = document.getElementById("board-apply-result");
      button.disabled = true;
      button.textContent = "Applying…";
      try {
        const { status: applyStatus, body: applied } = await postJson(
          "/api/mutations/apply",
          { ...reviewedIntent, fingerprint: preview.fingerprint },
        );
        if (applyStatus >= 400 || applied.ok === false) {
          const stale = applyStatus === 409;
          result.innerHTML = `<div class="guard board-refusal" role="alert" tabindex="-1"><strong>${stale ? "Preview refused" : "Apply refused"}. Nothing changed.</strong> ${esc(boardMutationError(applied, applyStatus))}${applied.data && applied.data.rolled_back ? " All writes were rolled back." : ""}</div>`;
          focusBoardRegion("#board-apply-result .board-refusal");
          return;
        }
        await route();
      } catch (error) {
        result.innerHTML = `<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Apply failed. Nothing changed.</strong> ${esc(error.message)}</div>`;
        focusBoardRegion("#board-apply-result .board-refusal");
      }
    });
  } catch (error) {
    out.innerHTML = `<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Preview failed. Nothing changed.</strong> ${esc(error.message)}</div>`;
    focusBoardRegion(`#${out.id} .board-refusal`);
  }
}

/* The move panel: the same structured intent the editor builds,
 * pre-filled from a drop or the Move affordance. Client mirrors of the
 * server rules gate the preview button; the server stays the
 * authority. */
function openMovePanel(slug, move, trigger = document.activeElement) {
  const out = document.getElementById("board-move");
  if (!out) return;
  rememberReturnFocus("board-action", trigger);
  const fixedTarget = move.to || "";
  const options = BOARD_STATUSES.filter((status) => status !== move.from);
  out.innerHTML = `<section class="board-action-panel" aria-labelledby="move-panel-title" tabindex="-1">
    <div class="board-action-heading"><span>Story action · Phase ${esc(move.phase)}</span>
      <h2 id="move-panel-title">Move <code>${esc(move.story)}</code></h2>
      <p>Current status: <strong>${esc(move.from)}</strong>. The card stays put until you review and apply an exact preview.</p></div>
    <form class="edit moveform" id="move-form">
      ${fixedTarget
        ? `<div class="board-choice"><span>New status</span><strong>${esc(fixedTarget)}</strong></div>`
        : field("new status", selectHtml("status", options, options[0]))}
      ${field("reason (required when parking on-hold)", '<input type="text" name="reason" placeholder="why is this waiting?">')}
      <details><summary>Technical details</summary>
        <p>Proof is only used when marking done. Existing proof is kept when this is blank.</p>
        ${field(`evidence body ${move.evidenceExists ? "(proof already exists)" : "(required for done when proof is missing)"}`,
          '<textarea name="evidence_body" placeholder="- proof line…"></textarea>')}
        <p><a href="#/edit/update_story_status">Open the full roadmap editor</a></p>
      </details>
      <div class="board-form-actions"><button type="submit">Preview this move</button>
        <button type="button" id="move-cancel">Cancel</button></div>
    </form>
    <div id="move-out"></div>
  </section>`;
  enhanceSemantics(out);
  const close = () => {
    out.innerHTML = "";
    restoreReturnFocus("board-action");
  };
  document.getElementById("move-cancel").addEventListener("click", close);
  wireDismissibleRegion(".board-action-panel", close, "board-action");
  const form = document.getElementById("move-form");
  const runMovePreview = async () => {
    const moveOut = document.getElementById("move-out");
    const target = fixedTarget || form.elements.status.value;
    const reason = form.elements.reason.value.trim();
    const evidenceBody = form.elements.evidence_body.value.trim();
    if (target === move.from) {
      moveOut.innerHTML = "";
      return;
    }
    if (HOLD_COLUMNS.includes(target) && !reason) {
      moveOut.innerHTML = '<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Preview refused. Nothing changed.</strong> Parking on-hold requires a reason. Add why this work is waiting, then preview.</div>';
      focusBoardRegion("#move-out .board-refusal");
      return;
    }
    const intent = {
      kind: "update_story_status", project: slug, phase: String(move.phase),
      story: move.story, status: target,
    };
    if (reason) intent.reason = reason;
    if (evidenceBody) intent.evidence_body = evidenceBody;
    await previewBoardMutation(
      moveOut,
      intent,
      `Move ${move.story} in phase ${move.phase} from ${move.from} to ${target}.`,
    );
  };
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    runMovePreview();
  });
  focusBoardRegion(".board-action-panel");
  if (SNAPSHOT_MODE && new URLSearchParams(location.search).has("autopreview")) {
    runMovePreview();
  }
}

function openCreatePanel(slug, phase, phaseName, trigger = document.activeElement) {
  const out = document.getElementById("board-move");
  if (!out) return;
  rememberReturnFocus("board-action", trigger);
  out.innerHTML = `<section class="board-action-panel" aria-labelledby="create-panel-title" tabindex="-1">
    <div class="board-action-heading"><span>New story · Phase ${esc(phase)}</span>
      <h2 id="create-panel-title">Create a board task</h2>
      <p>It will start in <strong>Phase ${esc(phase)} · ${esc(phaseName)}</strong>. Nothing is added until you review and apply the preview.</p></div>
    <form class="edit" id="board-create-form">
      ${field("title", '<input type="text" name="title" required autocomplete="off" placeholder="What needs to be done?">')}
      ${field("starting status", selectHtml("status", ["backlog", "ready", "in-progress"], "backlog"))}
      <details><summary>Technical details</summary>
        ${field("story slug (optional)", '<input type="text" name="slug" pattern="[a-z0-9-]*" title="lowercase letters, digits, and hyphens">')}
        <p><a href="#/edit/create_story">Open the full roadmap editor</a> for the complete planning surface.</p>
      </details>
      <div class="board-form-actions"><button type="submit">Preview this story</button>
        <button type="button" id="create-cancel">Cancel</button></div>
    </form>
    <div id="create-out"></div>
  </section>`;
  enhanceSemantics(out);
  const close = () => {
    out.innerHTML = "";
    restoreReturnFocus("board-action");
  };
  document.getElementById("create-cancel").addEventListener("click", close);
  wireDismissibleRegion(".board-action-panel", close, "board-action");
  const form = document.getElementById("board-create-form");
  const runCreatePreview = async () => {
    const previewOut = document.getElementById("create-out");
    const title = form.elements.title.value.trim();
    const status = form.elements.status.value;
    const storySlug = form.elements.slug.value.trim();
    if (!title) {
      previewOut.innerHTML = '<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Preview refused. Nothing changed.</strong> Give the story a short title first.</div>';
      focusBoardRegion("#create-out .board-refusal");
      return;
    }
    const intent = {
      kind: "create_story", project: slug, phase: String(phase), title, status,
    };
    if (storySlug) intent.slug = storySlug;
    await previewBoardMutation(
      previewOut,
      intent,
      `Create "${title}" in phase ${phase} with status ${status}.`,
    );
  };
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    runCreatePreview();
  });
  focusBoardRegion(".board-action-panel");
  if (SNAPSHOT_MODE) {
    const params = new URLSearchParams(location.search);
    if (params.has("autocreate")) {
      form.elements.title.value = params.get("autocreate") || "A short board task";
      if (params.get("createstatus")) form.elements.status.value = params.get("createstatus");
      if (params.has("autopreview")) runCreatePreview();
    }
  }
}

function openPhasePanel(slug, phase, phaseName, kind, trigger = document.activeElement) {
  const out = document.getElementById("board-move");
  if (!out) return;
  const pausing = kind === "pause_phase";
  const action = pausing ? "Pause" : "Resume";
  rememberReturnFocus("board-action", trigger);
  out.innerHTML = `<section class="board-action-panel" aria-labelledby="phase-panel-title" tabindex="-1">
    <div class="board-action-heading"><span>Phase action</span>
      <h2 id="phase-panel-title">${action} Phase ${esc(phase)} · ${esc(phaseName)}</h2>
      <p>The lane stays ${pausing ? "active" : "paused"} until you review and apply the exact preview.</p></div>
    <form class="edit" id="board-phase-form">
      ${pausing ? field("reason (required)", '<input type="text" name="reason" required placeholder="why should this phase wait?">') : ""}
      <div class="board-form-actions"><button type="submit">Preview ${action.toLowerCase()}</button>
        <button type="button" id="phase-cancel">Cancel</button></div>
    </form>
    <div id="phase-out"></div>
  </section>`;
  enhanceSemantics(out);
  const close = () => {
    out.innerHTML = "";
    restoreReturnFocus("board-action");
  };
  document.getElementById("phase-cancel").addEventListener("click", close);
  wireDismissibleRegion(".board-action-panel", close, "board-action");
  const form = document.getElementById("board-phase-form");
  const runPhasePreview = async () => {
    const previewOut = document.getElementById("phase-out");
    const reason = pausing ? form.elements.reason.value.trim() : "";
    if (pausing && !reason) {
      previewOut.innerHTML = '<div class="guard board-refusal" role="alert" tabindex="-1"><strong>Preview refused. Nothing changed.</strong> Pausing a phase requires a reason.</div>';
      focusBoardRegion("#phase-out .board-refusal");
      return;
    }
    const intent = { kind, project: slug, phase: String(phase) };
    if (reason) intent.reason = reason;
    await previewBoardMutation(previewOut, intent, `${action} phase ${phase} · ${phaseName}.`);
  };
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    runPhasePreview();
  });
  focusBoardRegion(".board-action-panel");
}

function wireBoardMoves(slug) {
  const board = document.querySelector(".board");
  if (!board) return;
  let dragging = null;
  let dragSource = null;
  let dragColumn = null;
  const clearDragState = () => {
    if (dragSource) dragSource.classList.remove("bcard-dragging");
    if (dragColumn) dragColumn.classList.remove("bcol-drag-over");
    dragSource = null;
    dragColumn = null;
  };
  board.addEventListener("dragstart", (event) => {
    const card = event.target.closest && event.target.closest(".bcard[draggable]");
    if (!card) return;
    dragging = { ...card.dataset };
    dragSource = card;
    card.classList.add("bcard-dragging");
    event.dataTransfer.setData("text/plain", card.dataset.story);
    event.dataTransfer.effectAllowed = "move";
  });
  board.addEventListener("dragend", () => {
    dragging = null;
    clearDragState();
  });
  board.addEventListener("dragover", (event) => {
    if (!dragging) return;
    const column = event.target.closest && event.target.closest(".bcol");
    if (!column) return;
    event.preventDefault();
    if (dragColumn !== column) {
      if (dragColumn) dragColumn.classList.remove("bcol-drag-over");
      dragColumn = column;
      dragColumn.classList.add("bcol-drag-over");
    }
  });
  board.addEventListener("drop", (event) => {
    if (!dragging) return;
    const column = event.target.closest && event.target.closest(".bcol");
    if (!column) return;
    event.preventDefault();
    const from = dragging;
    dragging = null;
    clearDragState();
    if (column.dataset.phase && column.dataset.phase !== from.phase) {
      boardNotice("Cross-phase moves are not supported. The story stays in its original lane.");
      return;
    }
    if (column.dataset.droppable !== "1") {
      boardNotice("This phase is paused or closed. Resume it before moving its stories.");
      return;
    }
    openMovePanel(slug, {
      story: from.story, phase: from.phase, from: from.status,
      to: column.dataset.col || "", evidenceExists: from.evidence === "1",
    });
  });
  board.addEventListener("click", (event) => {
    const create = event.target.closest && event.target.closest("[data-board-create]");
    if (create) {
      openCreatePanel(slug, create.dataset.phase, create.dataset.phaseName, create);
      return;
    }
    const phaseAction = event.target.closest && event.target.closest("[data-board-phase-action]");
    if (phaseAction) {
      openPhasePanel(
        slug,
        phaseAction.dataset.phase,
        phaseAction.dataset.phaseName,
        phaseAction.dataset.boardPhaseAction,
        phaseAction,
      );
      return;
    }
    const button = event.target.closest && event.target.closest("[data-board-move], [data-board-park]");
    if (!button) return;
    const card = button.closest(".bcard");
    openMovePanel(slug, {
      story: card.dataset.story,
      phase: card.dataset.phase,
      from: card.dataset.status,
      to: button.hasAttribute("data-board-park") ? "on-hold" : "",
      evidenceExists: card.dataset.evidence === "1",
    }, button);
  });
}

/* ── slide-over session panel (inline) ────────────────────── */

function _openSlideOver(storyId, slug) {
  // Use the existing SessionPanel if available
  if (!window.DW._sessionPanel) {
    if (window.DW.SessionPanel) {
      window.DW._sessionPanel = new window.DW.SessionPanel();
    } else {
      // Fallback: navigate
      location.hash = `#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(storyId)}`;
      return;
    }
  }
  const panel = window.DW._sessionPanel;
  const slideOver = document.getElementById("board-slide-over");
  if (!slideOver) return;

  // Toggle: same card closes
  if (panel.isOpen() && panel.storyId() === storyId) {
    _closeSlideOver();
    return;
  }

  // Open
  slideOver.hidden = false;
  slideOver.classList.add("open");
  document.querySelector(".board")?.classList.add("board-has-slide-over");

  // Ensure session panel root exists in slide-over
  let root = slideOver.querySelector(".session-panel-root");
  if (!root) {
    root = document.createElement("div");
    root.className = "session-panel-root";
    const content = slideOver.querySelector(".slide-over-content");
    if (content) { content.innerHTML = ""; content.appendChild(root); }
  }

  // Open the layout panel if workspace layout is available
  if (window.DW._layout) window.DW._layout.open("session");

  panel.open(storyId, slug);
}

function _closeSlideOver() {
  const panel = window.DW._sessionPanel;
  if (panel) panel.close();
  const slideOver = document.getElementById("board-slide-over");
  if (slideOver) {
    slideOver.classList.remove("open");
    slideOver.hidden = true;
  }
  document.querySelector(".board")?.classList.remove("board-has-slide-over");
  if (window.DW._layout) window.DW._layout.close("session");
}

function wireSlideOverPanel(slug) {
  const board = document.querySelector(".board");
  if (!board) return;

  board.addEventListener("click", (event) => {
    const link = event.target.closest && event.target.closest(".bcard-link");
    if (!link) return;

    const href = link.getAttribute("href") || "";
    const match = href.match(/#\/p\/([^/]+)\/s\/([^/]+)/);
    if (!match) return;

    event.preventDefault();
    const linkSlug = decodeURIComponent(match[1]);
    const storyId  = decodeURIComponent(match[2]);
    _openSlideOver(storyId, linkSlug);
  });

  // Escape closes
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      const slideOver = document.getElementById("board-slide-over");
      if (slideOver && slideOver.classList.contains("open")) {
        event.preventDefault();
        _closeSlideOver();
      }
    }
  });
}

/* ── SSE live updates ─────────────────────────────────────── */

function wireBoardLiveUpdates() {
  if (SNAPSHOT_MODE || typeof document === "undefined") return;

  document.addEventListener("dw-story-changed", (event) => {
    const detail = event.detail || {};
    const card = document.querySelector(`dw-card[data-story="${selectorEscape(detail.story_id || "")}"]`);
    if (!card) return;
    card.classList.add("bcard-transitioning");
    setTimeout(() => {
      card.dataset.status = detail.status || card.dataset.status;
      card.classList.remove("bcard-transitioning");
      // A full re-render is more reliable than DOM surgery for column moves
    }, 300);
  });

  document.addEventListener("dw-request-pending", (event) => {
    const detail = event.detail || {};
    const card = document.querySelector(`dw-card[data-story="${selectorEscape(detail.story_id || "")}"]`);
    if (!card) return;
    card.dataset.attention = detail.type || "waiting-for-input";
    if (!card.querySelector(".bcard-attention")) {
      const badge = document.createElement("span");
      badge.className = "bcard-attention";
      badge.textContent = "Needs attention";
      const top = card.querySelector(".bcard-top");
      if (top) top.appendChild(badge);
    }
  });

  document.addEventListener("dw-request-resolved", (event) => {
    const detail = event.detail || {};
    const card = document.querySelector(`dw-card[data-story="${selectorEscape(detail.story_id || "")}"]`);
    if (!card) return;
    card.dataset.attention = "none";
    const needsBadge = card.querySelector(".bcard-attention");
    if (needsBadge) needsBadge.remove();
  });
}

/* ── overview strip ───────────────────────────────────────── */

/* Status summaries come from the roadmap engine as machine-flavored
 * strings, e.g. "attention — pmo-roadmap/pm/roadmap/<project>/phase-33-
 * operator-grade-workbench: all stories are done but final-summary.md is
 * missing". Strip the path noise and repeated "attention" jargon so the
 * overview strip reads like a sentence, not a log line. */
function _cleanStatusSummary(summary) {
  if (!summary) return "";
  let text = String(summary).replace(/^(?:attention|ready)\s*[—-]\s*/i, "").trim();
  const phaseMatch = text.match(/phase-(\d+)[^:]*:\s*(.*)$/i);
  if (phaseMatch) {
    let msg = phaseMatch[2].trim();
    msg = msg.replace(/\bfinal-summary\.md\b/gi, "final summary");
    msg = msg.replace(/\ball stories are done\b/gi, "all stories done");
    msg = msg.replace(/done but final summary is missing/i, "done, final summary missing");
    text = `Phase ${phaseMatch[1]}: ${msg}`;
  }
  return text;
}

function boardOverviewStrip(slug, setup, status, step, presentation, notice, flatStats) {
  const next = presentation.next_step || {};
  const work = setup.delivery_scope?.current_work;
  const needsAttention = setup.readiness !== "ready";
  const technicalOpen = Boolean(
    notice || (SNAPSHOT_MODE && new URLSearchParams(location.search).has("confirmstep")),
  );

  const statusSentence = _cleanStatusSummary(status.summary);

  const statsLine = flatStats
    ? `${flatStats.totalStories} stor${flatStats.totalStories === 1 ? "y" : "ies"}, ${flatStats.inProgressCount} in progress, ${flatStats.needsYouCount} need you`
    : "";

  return `<section class="board-overview board-overview-flat readiness-${esc(setup.readiness)}" aria-labelledby="board-title">
    <div class="board-overview-head-flat">
      <div class="board-overview-name">
        <h1 id="board-title">${esc(slug)}</h1>
        ${statsLine ? `<span class="board-stats-line">${esc(statsLine)}</span>` : ""}
      </div>
      <div class="board-overview-status-line">
        <span class="board-readiness-pill ops-label ${needsAttention ? "attention" : "ready"}" role="status">${esc(needsAttention ? "Needs attention" : "Ready")}</span>
        ${statusSentence ? `<span class="board-status-sentence">${esc(statusSentence)}</span>` : ""}
      </div>
    </div>
    <dw-fold class="board-technical" label="Technical details"${technicalOpen ? " open" : ""}>
      <p>Exact repository, contract, gate, command, and one-step facts.</p>
      ${statusPanel(status, step, notice)}
    </dw-fold>
  </section>`;
}

/* ── view toggle persistence ──────────────────────────────── */

const BOARD_VIEW_KEY = "delivery-workbench.board-view";

function _savedBoardView() {
  try { return localStorage.getItem(BOARD_VIEW_KEY) || "flat"; }
  catch (_) { return "flat"; }
}

function _saveBoardView(view) {
  try { localStorage.setItem(BOARD_VIEW_KEY, view); }
  catch (_) { /* ignore */ }
}

/* ── main view function ───────────────────────────────────── */

async function viewBoard(slug, notice = null) {
  slug = slug || selectedProject;
  if (!slug) {
    viewProjectSelector("#/board");
    return;
  }
  setCrumbs([{ label: "work", href: "#/" }, { label: slug }]);
  const projectQuery = `?project=${encodeURIComponent(slug)}`;
  const [boardBody, statusBody, stepBody, setupBody, presentationBody, stateBody] = await Promise.all([
    api(`/api/projects/${encodeURIComponent(slug)}/board`),
    api(`/api/status${projectQuery}`),
    api(`/api/step${projectQuery}`),
    api(`/api/delivery-setup${projectQuery}`),
    api(`/api/presentation/status${projectQuery}`),
    api(`/api/projects/${encodeURIComponent(slug)}/state`).catch(() => ({ data: { stories: [] } })),
  ]);
  const model = boardBody.data;
  const step  = stepBody.data;
  const orthoMap = {};
  (stateBody.data.stories || []).forEach((s) => { orthoMap[s.story_id] = s; });

  const currentView = _savedBoardView();
  const flatResult  = flatBoardHtml(slug, model, orthoMap);

  const open   = model.phases.filter((lane) => !lane.closed);
  const closed = model.phases.filter((lane) => lane.closed);

  // Find the first open phase for the "Create story" button in flat view
  const firstOpenPhase = open[0] || null;

  const phaseLanesHtml = `
    ${open.map((lane) => boardLane(slug, model.columns, lane, orthoMap)).join("") || stateHtml("No open phases")}
    ${closed.length ? `<details class="board-closed"><summary>Closed phases (${closed.length})</summary>
      ${closed.map((lane) => boardLane(slug, model.columns, lane, orthoMap)).join("")}</details>` : ""}`;

  app.innerHTML = `${destinationNav("work", "#/board")}
    ${boardOverviewStrip(slug, setupBody.data, statusBody.data, step, presentationBody.data, notice, flatResult)}
    <div class="board board-redesigned" aria-labelledby="board-columns-title">
      <div class="board-toolbar">
        <div class="board-toolbar-left">
          <h2 id="board-columns-title">Stories</h2>
          ${firstOpenPhase ? `<dw-button variant="primary" id="board-create-flat" data-board-create data-phase="${firstOpenPhase.number}" data-phase-name="${esc(firstOpenPhase.slug)}">Create story</dw-button>` : ""}
        </div>
        <div class="board-toolbar-right">
          <div class="board-view-toggle" role="group" aria-label="Board view">
            <button type="button" class="board-view-btn${currentView === "flat" ? " active" : ""}" data-board-view="flat" aria-pressed="${currentView === "flat"}">Flat</button>
            <button type="button" class="board-view-btn${currentView === "phase" ? " active" : ""}" data-board-view="phase" aria-pressed="${currentView === "phase"}">By phase</button>
          </div>
        </div>
      </div>
      <div id="board-move"></div>
      <div class="board-flat-view${currentView === "flat" ? "" : " hidden"}" data-board-layout="flat">
        <div class="bcols flat-cols">${flatResult.html}</div>
      </div>
      <div class="board-phase-view${currentView === "phase" ? "" : " hidden"}" data-board-layout="phase">
        <div class="board-lanes-head"><div><span>Roadmap</span><h2>Phase lanes</h2></div>
          <p>Create and move work here. Every saved change stops for an exact preview.</p></div>
        ${phaseLanesHtml}
      </div>
      <div id="board-slide-over" class="slide-over" hidden aria-label="Story session panel">
        <div class="slide-over-header">
          <button type="button" class="slide-over-close" aria-label="Close panel">Close</button>
        </div>
        <div class="slide-over-content" data-panel="session"></div>
      </div>
    </div>`;

  // Wire view toggle
  const toggleGroup = document.querySelector(".board-view-toggle");
  if (toggleGroup) {
    toggleGroup.addEventListener("click", (event) => {
      const btn = event.target.closest("[data-board-view]");
      if (!btn) return;
      const view = btn.dataset.boardView;
      _saveBoardView(view);
      document.querySelectorAll("[data-board-layout]").forEach((el) => {
        el.classList.toggle("hidden", el.dataset.boardLayout !== view);
      });
      document.querySelectorAll(".board-view-btn").forEach((b) => {
        b.classList.toggle("active", b.dataset.boardView === view);
        b.setAttribute("aria-pressed", String(b.dataset.boardView === view));
      });
    });
  }

  // Wire slide-over close button
  const slideCloseBtn = document.querySelector(".slide-over-close");
  if (slideCloseBtn) {
    slideCloseBtn.addEventListener("click", _closeSlideOver);
  }

  wireStepControl(step);
  wireBoardMoves(slug);
  wireSlideOverPanel(slug);
  wireBoardLiveUpdates();

  // Deterministic screenshot affordances for board action and refusal states.
  if (SNAPSHOT_MODE) {
    const params = new URLSearchParams(location.search);
    const automove = params.get("automove");
    const autocreate = params.get("autocreate");
    if (automove) {
      app.classList.add("board-action-snapshot");
      const [story, to] = automove.split(":");
      const card = document.querySelector(`.bcard[data-story="${selectorEscape(story)}"]`);
      if (card && to) {
        openMovePanel(slug, {
          story, phase: card.dataset.phase, from: card.dataset.status,
          to, evidenceExists: card.dataset.evidence === "1",
        });
      }
    } else if (autocreate !== null) {
      app.classList.add("board-action-snapshot");
      const phase = params.get("createphase");
      const button = phase
        ? document.querySelector(`[data-board-create][data-phase="${selectorEscape(phase)}"]`)
        : document.querySelector("[data-board-create]:not([disabled])");
      if (button) openCreatePanel(slug, button.dataset.phase, button.dataset.phaseName, button);
    }
  }
}
