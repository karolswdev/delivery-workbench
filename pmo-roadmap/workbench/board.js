"use strict";

/* ── board view ───────────────────────────────────────────────────────
 * Kanban-style phase lanes with drag-and-drop, story creation,
 * and phase pause/resume.  Extracted from app.js. */

const BOARD_STATUSES = ["backlog", "ready", "in-progress", "blocked", "on-hold", "done"];
const HOLD_COLUMNS = ["on-hold"];

function boardCard(slug, lane, card, orthoState) {
  const parked = PARKED_COLUMNS.includes(card.status) || card.status === "paused";
  const movable = !lane.closed && !lane.paused;
  const ortho = orthoState || {};
  const exec = ortho.execution || "stopped";
  const attn = ortho.attention || "none";
  const auth = ortho.authority || "none";
  const execDot = exec === "running"
    ? '<span class="bcard-exec bcard-exec-running" title="Running" aria-label="Execution: running"></span>'
    : exec === "idle"
    ? '<span class="bcard-exec bcard-exec-idle" title="Idle" aria-label="Execution: idle"></span>'
    : "";
  const attnBadge = attn !== "none"
    ? `<dw-badge variant="needs-you" count="${esc(attn === "waiting-for-input" ? "Input needed" : attn === "decision-pending" ? "Decision" : "Blocked")}"></dw-badge>`
    : "";
  const authRing = auth !== "none" ? ` bcard-auth-${esc(auth)}` : "";
  return `
    <dw-card class="bcard st-${esc(card.status)}${authRing}" ${movable ? 'draggable="true"' : ""}
         data-story="${esc(card.story_id)}" data-phase="${lane.number}"
         data-status="${esc(card.status)}" data-evidence="${card.evidence_exists ? 1 : 0}"
         data-execution="${esc(exec)}" data-attention="${esc(attn)}" data-authority="${esc(auth)}"
         aria-label="${esc(card.story_id)}: ${esc(card.title)}. Status ${esc(card.status)}. Execution ${esc(exec)}.${attn !== "none" ? " Attention: " + esc(attn) + "." : ""}">
      <div slot="header" class="bcard-top"><a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(card.story_id)}"><code>${esc(card.story_id)}</code></a>${execDot}
        <dw-status-pill status="${esc(card.status)}"></dw-status-pill>${attnBadge}${card.evidence_exists ? ' <span class="tick">proof saved</span>' : ""}</div>
      <div class="bcard-title">${esc(card.title)}</div>
      ${parked ? `<div class="bcard-note"><strong>Waiting:</strong> ${esc(card.note || "no reason recorded")}</div>` : ""}
      ${movable ? `<div slot="footer" class="bcard-actions" role="group" aria-label="Actions for ${esc(card.story_id)}">
        <dw-button variant="ghost" class="bmove" id="board-move-${esc(card.story_id)}" data-board-move>Move</dw-button>
        <dw-button variant="ghost" class="bmove" id="board-park-${esc(card.story_id)}" data-board-park>Park</dw-button>
      </div>` : ""}
    </dw-card>`;
}

function boardLane(slug, columns, lane, orthoMap) {
  const droppable = !lane.closed && !lane.paused;
  const cols = columns.map((col) => `
    <div class="bcol" data-col="${esc(col)}" data-phase="${lane.number}" data-droppable="${droppable ? 1 : 0}">
      <div class="bcol-head">${esc(col)} <span class="bcol-count">${lane.columns[col].length}</span></div>
      ${lane.columns[col].map((card) => boardCard(slug, lane, card, orthoMap[card.story_id])).join("")}
    </div>`).join("");
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
    return `
      <details class="blane closed" data-phase="${lane.number}">
        <summary>phase ${lane.number} · ${esc(lane.slug)} — closed, ${lane.done_count}/${lane.story_count} done</summary>
        <div class="bcols">${cols}</div>
      </details>`;
  }
  return `
    <div class="blane${lane.paused ? " paused" : ""}" data-phase="${lane.number}" data-paused="${lane.paused ? 1 : 0}">
      <div class="blane-head">${head}</div>
      <div class="bcols">${cols}</div>
    </div>`;
}

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
 * pre-filled from a drop or the ⇄ affordance. Client mirrors of the
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
  board.addEventListener("dragstart", (event) => {
    const card = event.target.closest && event.target.closest(".bcard[draggable]");
    if (!card) return;
    dragging = { ...card.dataset };
    event.dataTransfer.setData("text/plain", card.dataset.story);
    event.dataTransfer.effectAllowed = "move";
  });
  board.addEventListener("dragend", () => { dragging = null; });
  board.addEventListener("dragover", (event) => {
    if (!dragging) return;
    const column = event.target.closest && event.target.closest(".bcol");
    if (column) event.preventDefault();
  });
  board.addEventListener("drop", (event) => {
    if (!dragging) return;
    const column = event.target.closest && event.target.closest(".bcol");
    if (!column) return;
    event.preventDefault();
    const from = dragging;
    dragging = null;
    if (column.dataset.phase !== from.phase) {
      boardNotice("Cross-phase moves are not supported. The story stays in its original lane.");
      return;
    }
    if (column.dataset.droppable !== "1") {
      boardNotice("This phase is paused or closed. Resume it before moving its stories.");
      return;
    }
    openMovePanel(slug, {
      story: from.story, phase: from.phase, from: from.status,
      to: column.dataset.col, evidenceExists: from.evidence === "1",
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

function boardOverviewStrip(slug, setup, status, step, presentation, notice) {
  const next = presentation.next_step || {};
  const work = setup.delivery_scope?.current_work;
  const needsAttention = setup.readiness !== "ready";
  const technicalOpen = Boolean(
    notice || (SNAPSHOT_MODE && new URLSearchParams(location.search).has("confirmstep")),
  );
  return `<section class="board-overview readiness-${esc(setup.readiness)}" aria-labelledby="board-title">
    <div class="board-overview-head"><div><span>Work · ${esc(slug)}</span>
      <h1 id="board-title">${esc(slug)} board</h1></div>
      <dw-badge variant="${needsAttention ? "alert" : "default"}" count="${esc(needsAttention ? "Needs attention" : "Ready")}"></dw-badge></div>
    <div class="board-overview-strip">
      <div class="board-attention"><span>${needsAttention ? "Needs attention" : "Repository ready"}</span>
        <strong>${esc(status.summary)}</strong></div>
      <div class="board-next-step"><span>Next step</span>
        <strong>${esc(next.label || presentationCopy("check_readiness"))}</strong>
        <p>${esc(next.summary || "Review the current work before acting.")}</p></div>
      ${work ? `<div class="board-current-work"><span>Current work</span>
        <a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(work.story_id)}"><code>${esc(work.story_id)}</code> ${esc(work.title)}</a>
        <dw-status-pill status="${esc(work.status)}"></dw-status-pill></div>` : ""}
    </div>
    <dw-fold class="board-technical" label="Technical details"${technicalOpen ? " open" : ""}>
      <p>Exact repository, contract, gate, command, and one-step facts.</p>
      ${statusPanel(status, step, notice)}
    </dw-fold>
  </section>`;
}

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
  const step = stepBody.data;
  const orthoMap = {};
  (stateBody.data.stories || []).forEach((s) => { orthoMap[s.story_id] = s; });
  const open = model.phases.filter((lane) => !lane.closed);
  const closed = model.phases.filter((lane) => lane.closed);
  app.innerHTML = `${destinationNav("work", "#/board")}
    ${boardOverviewStrip(slug, setupBody.data, statusBody.data, step, presentationBody.data, notice)}
    <div class="board" aria-labelledby="phase-lanes-title">
      <div class="board-lanes-head"><div><span>Roadmap</span><h2 id="phase-lanes-title">Phase lanes</h2></div>
        <p>Create and move work here. Every saved change stops for an exact preview.</p></div>
      <div id="board-move"></div>
      ${open.map((lane) => boardLane(slug, model.columns, lane, orthoMap)).join("") || stateHtml("No open phases")}
      ${closed.length ? `<details class="board-closed"><summary>Closed phases (${closed.length})</summary>
        ${closed.map((lane) => boardLane(slug, model.columns, lane, orthoMap)).join("")}</details>` : ""}
    </div>`;
  wireStepControl(step);
  wireBoardMoves(slug);
  if (window.DW.wireSessionPanelClicks) wireSessionPanelClicks();
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
