"use strict";

/* ── structured editor (WLA-5-06) ───────────────────────────────────
 * The editor constructs structured intent and POSTs it to
 * /api/mutations/preview. It never applies: the apply/diff workflow
 * is WLA-5-07. Client-side checks catch the obvious before the
 * server's authoritative refusals. */

const EDIT_ACTIONS = {
  adoption_review: "review adoption",
  create_phase: "create phase",
  create_story: "create story",
  update_story_status: "update story status",
  pause_phase: "pause phase",
  resume_phase: "resume phase",
  attach_evidence: "attach evidence",
  close_phase: "close phase",
};

const adoptionReviewMarks = new Map();
const ADOPTION_TERMINAL_HANDOFF = "dw setup preview <proposal-file>";
const ADOPTION_TECHNICAL_LABEL = "Technical details";
const ADOPTION_MARK_STORAGE_PREFIX = "delivery-workbench.adoption-review.";
const IDEATION_STORAGE_KEY = "delivery-workbench.ideation-plan.v1";
const IDEATION_SNAPSHOT_STEP = new URLSearchParams(location.search).get("ideationstep") || "";
const IDEATION_STEPS = [
  ["idea", "Idea"], ["draft", "Draft"], ["review", "Review"],
  ["preview", "Preview"], ["apply", "Apply"],
];

function safeStoredJson(key) {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : null;
  } catch (_err) { return null; }
}

function storeJson(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); }
  catch (_err) {
    // A hardened browser can disable storage. The flow remains usable for the
    // current page and never falls back to repository files.
  }
}

function clearStoredJson(key) {
  try { localStorage.removeItem(key); }
  catch (_err) { /* The in-memory reset still succeeds. */ }
}

function provenanceHtml(provenance) {
  return `<p class="adoption-provenance"><strong>Source:</strong> ${esc(provenance?.sentence || "Unknown.")}</p>`;
}

function adoptionReviewTabs() {
  return `<div class="tabs adoption-workspace-tabs" aria-label="Roadmap changes workspace">${Object.keys(EDIT_ACTIONS).map((name) =>
    `<a href="#/edit/${name}" class="${name === "adoption_review" ? "active" : ""}">${esc(EDIT_ACTIONS[name])}</a>`).join("")}</div>`;
}

function normalizedReviewState(raw = {}) {
  return {
    decision: typeof raw.decision === "string" ? raw.decision : "",
    accepted_items: Array.isArray(raw.accepted_items) ? raw.accepted_items.filter((item) => typeof item === "string") : [],
    objections: Array.isArray(raw.objections) ? raw.objections.filter((item) => item && typeof item.item === "string" && typeof item.correction === "string") : [],
    overall_note: typeof raw.overall_note === "string" ? raw.overall_note : "",
  };
}

function adoptionMarkState(key) {
  if (!adoptionReviewMarks.has(key)) {
    const stored = safeStoredJson(`${ADOPTION_MARK_STORAGE_PREFIX}${key}`);
    adoptionReviewMarks.set(key, normalizedReviewState(stored || {}));
  }
  return adoptionReviewMarks.get(key);
}

function persistAdoptionMark(key, state, persist = null) {
  const normalized = normalizedReviewState(state);
  adoptionReviewMarks.set(key, normalized);
  storeJson(`${ADOPTION_MARK_STORAGE_PREFIX}${key}`, normalized);
  if (persist) persist(normalized);
  return normalized;
}

function correctionPacket(model, state) {
  return {
    kind: "delivery-workbench-setup-review-corrections",
    schema_version: 1,
    decision: "rejected-with-corrections",
    proposal_hash: model.technical_details.proposal_hash,
    objections: state.objections.map((item) => ({ item: item.item, correction: item.correction })),
    overall_note: state.overall_note,
    authorizes_setup: false,
    starts_work: false,
  };
}

function adoptionItemStatus(state, itemId) {
  if (state.objections.some((item) => item.item === itemId)) return ["Needs correction", "rejected"];
  if (state.accepted_items.includes(itemId)) return ["Accepted", "accepted"];
  return ["Not reviewed", "pending"];
}

function adoptionItemReviewHtml(state, itemId) {
  const [label, status] = adoptionItemStatus(state, itemId);
  return `<div class="adoption-item-review" data-review-state="${status}">
    <strong>${esc(label)}</strong>
    <span class="adoption-item-actions">
      <button type="button" data-adoption-item-accept="${esc(itemId)}"${status === "rejected" ? " disabled" : ""}>Accept item</button>
      <button type="button" data-adoption-item-reject="${esc(itemId)}">Request correction</button>
    </span>
  </div>`;
}

function renderAdoptionMarks(model, key, identity = null, options = {}) {
  const out = document.getElementById("adoption-marks");
  if (!out) return;
  const allItems = model.objection_items.map((item) => item.id);
  let state = adoptionMarkState(key);
  state.accepted_items = state.accepted_items.filter((item) => allItems.includes(item));
  state.objections = state.objections.filter((item) => allItems.includes(item.item));
  const rejected = new Set(state.objections.map((item) => item.item));
  const ready = allItems.length > 0
    && !state.objections.length
    && allItems.every((item) => state.accepted_items.includes(item));
  state.decision = ready ? "accepted" : state.objections.length ? "rejected" : "";
  state = persistAdoptionMark(key, state, options.persist);
  const optionsHtml = model.objection_items.map((item) =>
    `<option value="${esc(item.id)}">${esc(item.label)}</option>`).join("");
  const packet = state.objections.length ? correctionPacket(model, state) : null;
  out.innerHTML = `<section class="adoption-marks" aria-labelledby="adoption-marks-title">
    <h2 id="adoption-marks-title">Your review marks</h2>
    <p>Marks stay in this browser across steps and reloads. They save no project files and provide no permission.</p>
    <div class="adoption-mark-actions" role="group" aria-label="Review decision">
      <button type="button" data-adoption-mark="accept" aria-pressed="${ready}">Accepted for preview</button>
      <button type="button" data-adoption-mark="reject" aria-pressed="${state.objections.length > 0}">Reject with corrections</button>
      <button type="button" data-adoption-mark="abandon">Abandon these marks</button>
    </div>
    ${ready ? `<div class="adoption-mark-result" role="status"><strong>Accepted for preview.</strong> Nothing has been applied.</div>` : ""}
    ${state.objections.length ? `<div class="adoption-review-blocked" role="alert"><strong>Preview is blocked.</strong> Correct or remove every rejected item in the draft.</div>` : ""}
    ${state.decision === "rejected" || options.openCorrection ? `<form id="adoption-correction-form" class="adoption-correction-form">
      <h3>Correction packet</h3>
      <label><b>Proposal item</b><select name="item">${optionsHtml}</select></label>
      <label><b>What should change?</b><textarea name="correction" required></textarea></label>
      <button type="submit" data-adoption-objection="add">Add objection</button>
      <label><b>Overall note</b><textarea name="overall_note">${esc(state.overall_note)}</textarea></label>
      <ul class="adoption-objections">${state.objections.map((item) => `<li>
        <strong>${esc(model.objection_items.find((candidate) => candidate.id === item.item)?.label || item.item)}</strong>
        <span>${esc(item.correction)}</span>
        ${options.editDraft ? `<button type="button" data-edit-rejected="${esc(item.item)}">Correct in draft</button>` : `<button type="button" data-remove-objection="${esc(item.item)}">Withdraw objection</button>`}
      </li>`).join("") || "<li>No item-level objections yet.</li>"}</ul>
      ${packet ? `<details class="adoption-packet"><summary>Correction packet for the draft</summary><pre>${esc(JSON.stringify(packet, null, 2))}</pre></details>` : ""}
    </form>` : ""}
    ${options.onPreview ? `<div class="ideation-canonical-action">
      <button type="button" class="applybtn" id="ideation-preview-button"${ready ? "" : " disabled"}>Preview this setup</button>
      <p>${ready ? "This is the one next step. It creates a one-use setup preview; it does not save configuration." : "Accept every current item and correct or remove every rejection before preview."}</p>
    </div>` : ""}
  </section>`;

  const saveAndRender = (nextIdentity = null, extra = {}) => {
    persistAdoptionMark(key, state, options.persist);
    renderAdoptionMarks(model, key, nextIdentity, { ...options, ...extra });
    options.refreshStatuses?.();
  };
  out.querySelector('[data-adoption-mark="accept"]').addEventListener("click", (event) => {
    const focus = captureAppFocus() || { selector: focusSelector(event.currentTarget), index: -1, tag: "button" };
    const rejectedItems = new Set(state.objections.map((item) => item.item));
    state.accepted_items = allItems.filter((item) => !rejectedItems.has(item));
    saveAndRender(focus);
  });
  out.querySelector('[data-adoption-mark="reject"]').addEventListener("click", (event) => {
    const focus = captureAppFocus() || { selector: focusSelector(event.currentTarget), index: -1, tag: "button" };
    saveAndRender(focus, { openCorrection: true });
  });
  out.querySelector('[data-adoption-mark="abandon"]').addEventListener("click", (event) => {
    const focus = captureAppFocus() || { selector: focusSelector(event.currentTarget), index: -1, tag: "button" };
    state = normalizedReviewState();
    saveAndRender(focus, { openCorrection: false });
  });
  const form = out.querySelector("#adoption-correction-form");
  if (form) {
    form.elements.overall_note.addEventListener("input", () => {
      state.overall_note = form.elements.overall_note.value;
      persistAdoptionMark(key, state, options.persist);
    });
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const correction = form.elements.correction.value.trim();
      if (!correction) return;
      const item = form.elements.item.value;
      state.overall_note = form.elements.overall_note.value;
      state.accepted_items = state.accepted_items.filter((candidate) => candidate !== item);
      state.objections = state.objections.filter((candidate) => candidate.item !== item);
      state.objections.push({ item, correction });
      saveAndRender({ selector: '[data-adoption-objection="add"]', index: -1, tag: "button" });
    });
  }
  out.querySelectorAll("[data-remove-objection]").forEach((button) => button.addEventListener("click", () => {
    state.objections = state.objections.filter((item) => item.item !== button.dataset.removeObjection);
    saveAndRender({ selector: '[data-adoption-mark="reject"]', index: -1, tag: "button" });
  }));
  out.querySelectorAll("[data-edit-rejected]").forEach((button) => button.addEventListener("click", () => {
    options.editDraft?.(button.dataset.editRejected);
  }));
  document.querySelectorAll("[data-adoption-item-accept]").forEach((button) => button.addEventListener("click", () => {
    const item = button.dataset.adoptionItemAccept;
    if (rejected.has(item)) return;
    if (!state.accepted_items.includes(item)) state.accepted_items.push(item);
    saveAndRender({ selector: `[data-adoption-item-accept="${selectorEscape(item)}"]`, index: -1, tag: "button" });
  }));
  document.querySelectorAll("[data-adoption-item-reject]").forEach((button) => button.addEventListener("click", () => {
    const item = button.dataset.adoptionItemReject;
    state.accepted_items = state.accepted_items.filter((candidate) => candidate !== item);
    persistAdoptionMark(key, state, options.persist);
    renderAdoptionMarks(model, key, null, { ...options, openCorrection: true });
    const nextForm = document.getElementById("adoption-correction-form");
    nextForm.elements.item.value = item;
    focusElement(nextForm.elements.correction);
    options.refreshStatuses?.();
  }));
  document.getElementById("ideation-preview-button")?.addEventListener("click", options.onPreview);
  finishDynamicRender(identity);
}

function adoptionStoryHtml(story, state) {
  return `<article class="adoption-story" data-review-item="${esc(story.item_id)}">
    <h4><code>${esc(story.id_sketch)}</code> ${esc(story.title)}</h4>
    ${adoptionItemReviewHtml(state, story.item_id)}
    <p>${esc(story.purpose)}</p>
    ${provenanceHtml(story.provenance)}
    <div class="adoption-scope"><div><h5>Included</h5><ul>${story.scope_in.map((item) => `<li>${esc(item.text)}${provenanceHtml(item.provenance)}</li>`).join("") || "<li>Nothing extra is included.</li>"}</ul></div>
      <div><h5>Not included</h5><ul>${story.scope_out.map((item) => `<li>${esc(item.text)}${provenanceHtml(item.provenance)}</li>`).join("") || "<li>No exclusions were recorded.</li>"}</ul></div></div>
    <h5>What this story must prove</h5>
    <ul>${story.acceptance_criteria.map((criterion) => `<li data-review-item="${esc(criterion.item_id)}">${adoptionItemReviewHtml(state, criterion.item_id)}<span>${esc(criterion.text)}</span>${provenanceHtml(criterion.provenance)}</li>`).join("")}</ul>
    <h5>What it depends on</h5>
    ${story.dependencies.length ? `<ul>${story.dependencies.map((dependency) => `<li>${esc(dependency.sentence)}${provenanceHtml(dependency.provenance)}</li>`).join("")}</ul>` : "<p>Nothing else in this draft must finish first.</p>"}
  </article>`;
}

function adoptionReviewBody(model, key) {
  const state = adoptionMarkState(key);
  return `<header class="adoption-review-head"><p class="eyebrow ops-label">Roadmap changes · review only</p>
      <h1 tabindex="-1">Review ${esc(model.project.title)}</h1>
      <p class="adoption-vision">${esc(model.project.vision)}</p>
      <p>${esc(model.project.context)} ${esc(model.project.identity)}</p>
      ${provenanceHtml(model.project.vision_provenance)}
      ${provenanceHtml(model.project.provenance)}
      <div class="adoption-inert"><strong>Nothing is saved yet.</strong> Reviewing cannot save setup, provide permission, start work, approve proof, or commit.</div>
    </header>
    <section class="adoption-phases"><h2>What the phases accomplish</h2>
      ${model.phases.map((phase) => `<article class="adoption-phase" data-review-item="${esc(phase.item_id)}">
        <div class="adoption-phase-number ops-label">Phase ${esc(phase.number)}</div><h3>${esc(phase.title)}</h3>
        ${adoptionItemReviewHtml(state, phase.item_id)}
        <p>${esc(phase.accomplishes)}</p>${provenanceHtml(phase.provenance)}
        <div class="adoption-stories">${phase.stories.map((story) => adoptionStoryHtml(story, state)).join("")}</div>
      </article>`).join("")}
    </section>
    <section class="adoption-exit"><h2>What the roadmap must prove overall</h2><ul>
      ${model.exit_criteria.map((criterion) => `<li data-review-item="${esc(criterion.item_id)}">${adoptionItemReviewHtml(state, criterion.item_id)}<span>${esc(criterion.text)}</span>${provenanceHtml(criterion.provenance)}</li>`).join("")}
    </ul></section>
    <section class="adoption-unresolved"><h2>Unresolved assumptions</h2><p>${esc(model.unresolved_questions.summary)}</p>
      ${model.unresolved_questions.items.length ? `<ul>${model.unresolved_questions.items.map((item) => `<li data-review-item="${esc(item.item_id)}">${adoptionItemReviewHtml(state, item.item_id)}<strong>${esc(item.question)}</strong>${provenanceHtml(item.provenance)}</li>`).join("")}</ul>` : ""}
    </section>
    <section class="adoption-configuration"><div><p class="eyebrow ops-label">Separate from roadmap truth</p><h2>${esc(model.configuration.label)}</h2><p>${esc(model.configuration.explanation)}</p></div>
      <div class="adoption-config-grid"><article><h3>Tracked delivery policy</h3><p>${esc(model.configuration.policy.sentence)}</p>
        ${model.configuration.policy.documents.length ? `<ul>${model.configuration.policy.documents.map((item) => `<li><strong>${esc(item.sentence)}</strong>${provenanceHtml(item.provenance)}</li>`).join("")}</ul>` : ""}
        ${model.configuration.policy.provenance ? provenanceHtml(model.configuration.policy.provenance) : ""}${model.configuration.policy.present && ADOPTION_PROPOSAL_FILE ? '<a class="adoption-bundle-link" href="#/program-studio/bundle">Review the generated program as one linked bundle</a>' : ""}</article>
      <article><h3>Local driver bindings</h3><p>${esc(model.configuration.driver_bindings.sentence)}</p>
        <ul>${model.configuration.driver_bindings.items.map((item) => `<li><strong>${esc(item.profile)}</strong> — ${esc(item.sentence)}${provenanceHtml(item.provenance)}</li>`).join("")}</ul></article></div>
    </section>
    <section class="adoption-paths"><h2>Files this setup would save</h2><p>${esc(model.changes.summary)}</p>
      <div class="adoption-path-split"><article><h3>Tracked with the repository</h3><ul>${model.changes.tracked.map((item) => `<li>${badge(item.action, item.action === "unchanged" ? "warn" : "ok")}<code>${esc(item.path)}</code></li>`).join("")}</ul></article>
      <article><h3>Local to this checkout</h3><ul>${model.changes.git_local.map((item) => `<li>${badge(item.action, item.action === "unchanged" ? "warn" : "ok")}<code>${esc(item.path)}</code></li>`).join("")}</ul></article></div>
    </section>`;
}

function technicalDetailsHtml(model, returnLabel = "Return to review") {
  const proposal = model.technical_details.proposal;
  return `<details class="adoption-technical"><summary>${esc(model.technical_details.label || ADOPTION_TECHNICAL_LABEL)}</summary>
    <div class="adoption-technical-content"><h2>Exact proposal data</h2><pre>${esc(JSON.stringify(proposal, null, 2))}</pre>
      <h2>Terminal fallback</h2><p>If you need the terminal path, save the exact JSON above as a proposal file, then run:</p>
      <code>${esc(model.terminal_handoff.command || ADOPTION_TERMINAL_HANDOFF)}</code>
      <code>dw setup apply --proposal &lt;setup:id&gt; --expect &lt;setup-sha256:token&gt;</code>
      <button type="button" data-return-review>${esc(returnLabel)}</button></div>
  </details>`;
}

function wireTechnicalReturn() {
  document.querySelectorAll("[data-return-review]").forEach((button) => button.addEventListener("click", () => {
    const details = button.closest("details");
    details.open = false;
    focusElement(details.querySelector("summary"));
  }));
}

async function viewLegacyAdoptionReview() {
  const query = ADOPTION_PROPOSAL_FILE
    ? `proposal_file=${encodeURIComponent(ADOPTION_PROPOSAL_FILE)}`
    : ADOPTION_PROPOSAL_ID ? `proposal=${encodeURIComponent(ADOPTION_PROPOSAL_ID)}` : "";
  const model = (await api(`/api/setup/review${query ? `?${query}` : ""}`)).data;
  if (!model.valid) {
    app.innerHTML = `${destinationNav("plan", "#/edit")}${adoptionReviewTabs()}<div class="adoption-review invalid-adoption-review">
      <h1>Review adoption proposal</h1>
      <div class="guard" role="alert"><strong>Proposal refused.</strong><pre>${esc(model.refusal)}</pre></div>
      <section class="adoption-unresolved"><h2>Unresolved assumptions</h2><p>${esc(model.unresolved_questions.summary)}</p></section>
      <details class="adoption-technical"><summary>${esc(model.technical_details.label || ADOPTION_TECHNICAL_LABEL)}</summary><pre>${esc(JSON.stringify(model.technical_details, null, 2))}</pre></details>
      <section class="adoption-handoff"><h2>Next act</h2><p>${esc(model.terminal_handoff.sentence)}</p><code>${esc(model.terminal_handoff.command || ADOPTION_TERMINAL_HANDOFF)}</code></section>
    </div>`;
    return;
  }
  const key = model.technical_details.proposal_hash;
  app.innerHTML = `${destinationNav("plan", "#/edit")}${adoptionReviewTabs()}<div class="adoption-review">
    ${adoptionReviewBody(model, key)}
    <div id="adoption-marks"></div>
    ${technicalDetailsHtml(model)}
    <section class="adoption-handoff"><h2>Next act</h2><p>${esc(model.terminal_handoff.sentence)}</p><code>${esc(model.terminal_handoff.command || ADOPTION_TERMINAL_HANDOFF)}</code></section>
  </div>`;
  renderAdoptionMarks(model, key);
  wireTechnicalReturn();
}

function ideaTitle(idea) {
  const first = idea.trim().split(/[.!?\n]/)[0].trim();
  if (!first) return "New delivery idea";
  return first.length > 80 ? `${first.slice(0, 77).trim()}…` : first;
}

function ideaSlug(title) {
  const slug = title.toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 64).replace(/-$/g, "");
  return slug || "new-delivery-idea";
}

function ideaPrefix(title) {
  const words = title.toUpperCase().match(/[A-Z0-9]+/g) || [];
  const initials = words.slice(0, 5).map((word) => word[0]).join("");
  return (initials || "IDEA").slice(0, 16);
}

function source(kind, note) {
  return { kind, source_note: note };
}

function sourceText(text, note = "Suggested from the rough idea; edit this source note if needed.") {
  return { text, provenance: source("recommendation", note) };
}

function storyDraft(prefix, number, index, idea) {
  return {
    id_sketch: `${prefix}-${number}-${String(index).padStart(2, "0")}`,
    title: index === 1 ? "Deliver the first useful path" : `Prove useful path ${index}`,
    problem: idea,
    scope_in: [sourceText("Build one bounded, reviewable result from the idea.")],
    scope_out: [sourceText("Later expansion and unattended operation stay outside this first plan.")],
    acceptance_criteria: [
      sourceText("A person can complete the first useful path end to end."),
      sourceText("A focused check proves the result without starting later work."),
    ],
    dependencies: [],
    provenance: source("recommendation", "Suggested from the rough idea; rename or reshape this story during drafting."),
  };
}

function proposalFromIdea(idea) {
  const title = ideaTitle(idea);
  const slug = ideaSlug(title);
  const prefix = ideaPrefix(title);
  return {
    schema: "delivery-workbench-setup-proposal@1",
    state: "draft",
    project: {
      slug, prefix, title,
      provenance: source("recommendation", "Project identity suggested from the rough idea and left editable."),
    },
    source_intent: {
      idea: idea.trim(), mode: "build",
      provenance: source("user-answer", "Rough idea entered in the Workbench."),
    },
    tracked_content: {
      roadmap: {
        phases: [{
          number: 1,
          title: "First useful release",
          goal: "Turn the idea into one reviewable outcome.",
          provenance: source("recommendation", "A small first phase suggested for review."),
          stories: [storyDraft(prefix, 1, 1, idea.trim())],
        }],
        exit_criteria: [sourceText("The planned result is usable, checked, and ready for a separate work decision.")],
      },
      policy: null,
    },
    local_content: { driver_bindings: {} },
    unresolved_questions: [],
    starts_work: false,
    creates_grant: false,
    certifies: false,
    commits: false,
  };
}

function blankIdeationState() {
  return {
    step: "idea", rough_idea: "", proposal: null,
    review: normalizedReviewState(), review_model: null,
    preview: null, applied: null, refusal: "", draft_signature: "",
  };
}

function loadIdeationState() {
  const stored = safeStoredJson(IDEATION_STORAGE_KEY);
  if (!stored || typeof stored !== "object") return blankIdeationState();
  const state = { ...blankIdeationState(), ...stored };
  state.review = normalizedReviewState(stored.review || {});
  if (!IDEATION_STEPS.some(([id]) => id === state.step)) state.step = "idea";
  return state;
}

let ideationState = loadIdeationState();

function persistIdeation() {
  if (!SNAPSHOT_MODE) storeJson(IDEATION_STORAGE_KEY, ideationState);
}

function ideationStepIndicator(step) {
  const activeIndex = Math.max(0, IDEATION_STEPS.findIndex(([id]) => id === step));
  return `<nav class="ideation-steps" aria-label="Idea to phase plan progress"><ol>${IDEATION_STEPS.map(([id, label], index) => {
    const state = index < activeIndex ? "complete" : index === activeIndex ? "current" : "upcoming";
    return `<li data-step-state="${state}"${state === "current" ? ' aria-current="step"' : ""}><span>${index + 1}</span><strong>${esc(label)}</strong></li>`;
  }).join("")}</ol></nav>`;
}

function ideationShell(step, body) {
  return `${destinationNav("plan", "#/edit")}${adoptionReviewTabs()}<div class="ideation-flow">
    ${ideationStepIndicator(step)}${body}</div>`;
}

function moveIdeationStep(step, focus = true) {
  ideationState.step = step;
  persistIdeation();
  return viewIdeationFlow().then(() => {
    if (focus && !SNAPSHOT_MODE) focusRegion(".ideation-step h1, .ideation-step h2");
  });
}

function invalidateIdeationPreview(message = "") {
  const hadPreview = Boolean(ideationState.preview);
  ideationState.preview = null;
  ideationState.applied = null;
  ideationState.refusal = "";
  ideationState.draft_signature = "";
  if (ideationState.proposal) ideationState.proposal.state = "draft";
  if (hadPreview) announceLiveUpdate("ideation-preview", String(Date.now()), message || "Draft changed. The old preview is no longer usable; preview the revised setup again.");
}

function setProposalPath(path, value) {
  const parts = path.split(".");
  let target = ideationState.proposal;
  parts.slice(0, -1).forEach((part) => { target = target[Number.isInteger(Number(part)) && String(Number(part)) === part ? Number(part) : part]; });
  const leaf = parts.at(-1);
  target[Number.isInteger(Number(leaf)) && String(Number(leaf)) === leaf ? Number(leaf) : leaf] = value;
}

function resolveReviewItem(itemId) {
  if (!itemId) return;
  ideationState.review.accepted_items = ideationState.review.accepted_items.filter((item) => item !== itemId);
  ideationState.review.objections = ideationState.review.objections.filter((item) => item.item !== itemId);
}

function draftField(label, path, value, itemId, { multiline = false, type = "text", min = "" } = {}) {
  const control = multiline
    ? `<textarea data-draft-path="${esc(path)}" data-review-item="${esc(itemId)}" required>${esc(value)}</textarea>`
    : `<input type="${esc(type)}" data-draft-path="${esc(path)}" data-review-item="${esc(itemId)}" value="${esc(value)}"${min !== "" ? ` min="${esc(min)}"` : ""} required>`;
  return `<label><b>${esc(label)}</b>${control}</label>`;
}

function draftSourceField(path, value, itemId) {
  return draftField("Source note", `${path}.provenance.source_note`, value.provenance.source_note, itemId, { multiline: true });
}

function renderDraftStep() {
  const proposal = ideationState.proposal;
  const roadmap = proposal.tracked_content.roadmap;
  const objection = new Map(ideationState.review.objections.map((item) => [item.item, item.correction]));
  app.innerHTML = ideationShell("draft", `<section class="ideation-step ideation-draft" aria-labelledby="ideation-draft-title">
    <p class="eyebrow ops-label">Step 2 of 5 · shape the draft</p><h1 id="ideation-draft-title" tabindex="-1">Edit the phase plan</h1>
    <p>Everything below is a browser draft. Nothing is saved yet. Edit the plan in plain words before review.</p>
    <form id="ideation-draft-form">
      <fieldset class="ideation-project-fields"><legend>Project</legend>
        ${draftField("Project title", "project.title", proposal.project.title, "project")}
        ${draftField("Project slug", "project.slug", proposal.project.slug, "project")}
        ${draftField("Story prefix", "project.prefix", proposal.project.prefix, "project")}
        ${draftField("Source note", "project.provenance.source_note", proposal.project.provenance.source_note, "project", { multiline: true })}
      </fieldset>
      <div class="ideation-phase-list">${roadmap.phases.map((phase, phaseIndex) => {
        const phaseId = `phase-${phase.number}`;
        return `<fieldset class="ideation-phase-editor" data-draft-item="${esc(phaseId)}"><legend>Phase ${phaseIndex + 1}</legend>
          ${objection.has(phaseId) ? `<div class="ideation-correction" role="alert"><strong>Correction requested:</strong> ${esc(objection.get(phaseId))}</div>` : ""}
          <div class="ideation-field-grid">
            ${draftField("Phase number", `tracked_content.roadmap.phases.${phaseIndex}.number`, phase.number, phaseId, { type: "number", min: "0" })}
            ${draftField("Phase title", `tracked_content.roadmap.phases.${phaseIndex}.title`, phase.title, phaseId)}
          </div>
          ${draftField("Phase goal", `tracked_content.roadmap.phases.${phaseIndex}.goal`, phase.goal, phaseId, { multiline: true })}
          ${draftField("Source note", `tracked_content.roadmap.phases.${phaseIndex}.provenance.source_note`, phase.provenance.source_note, phaseId, { multiline: true })}
          <div class="ideation-story-list">${phase.stories.map((story, storyIndex) => {
            const storyId = `story-${story.id_sketch}`;
            return `<fieldset class="ideation-story-editor" data-draft-item="${esc(storyId)}"><legend>Story ${storyIndex + 1}</legend>
              ${objection.has(storyId) ? `<div class="ideation-correction" role="alert"><strong>Correction requested:</strong> ${esc(objection.get(storyId))}</div>` : ""}
              <div class="ideation-field-grid">${draftField("ID sketch", `tracked_content.roadmap.phases.${phaseIndex}.stories.${storyIndex}.id_sketch`, story.id_sketch, storyId)}
                ${draftField("Story title", `tracked_content.roadmap.phases.${phaseIndex}.stories.${storyIndex}.title`, story.title, storyId)}</div>
              ${draftField("Problem to solve", `tracked_content.roadmap.phases.${phaseIndex}.stories.${storyIndex}.problem`, story.problem, storyId, { multiline: true })}
              ${draftField("Story source note", `tracked_content.roadmap.phases.${phaseIndex}.stories.${storyIndex}.provenance.source_note`, story.provenance.source_note, storyId, { multiline: true })}
              <div class="ideation-scope-grid"><fieldset><legend>Included</legend>${story.scope_in.map((item, itemIndex) => `${draftField("Scope item", `tracked_content.roadmap.phases.${phaseIndex}.stories.${storyIndex}.scope_in.${itemIndex}.text`, item.text, storyId, { multiline: true })}${draftSourceField(`tracked_content.roadmap.phases.${phaseIndex}.stories.${storyIndex}.scope_in.${itemIndex}`, item, storyId)}`).join("")}</fieldset>
                <fieldset><legend>Not included</legend>${story.scope_out.map((item, itemIndex) => `${draftField("Scope item", `tracked_content.roadmap.phases.${phaseIndex}.stories.${storyIndex}.scope_out.${itemIndex}.text`, item.text, storyId, { multiline: true })}${draftSourceField(`tracked_content.roadmap.phases.${phaseIndex}.stories.${storyIndex}.scope_out.${itemIndex}`, item, storyId)}`).join("")}</fieldset></div>
              <fieldset class="ideation-criteria"><legend>Acceptance criteria</legend>${story.acceptance_criteria.map((criterion, criterionIndex) => {
                const criterionId = `${storyId}-criterion-${criterionIndex + 1}`;
                return `<div class="ideation-criterion" data-draft-item="${esc(criterionId)}">${objection.has(criterionId) ? `<div class="ideation-correction" role="alert"><strong>Correction requested:</strong> ${esc(objection.get(criterionId))}</div>` : ""}
                  ${draftField(`Criterion ${criterionIndex + 1}`, `tracked_content.roadmap.phases.${phaseIndex}.stories.${storyIndex}.acceptance_criteria.${criterionIndex}.text`, criterion.text, criterionId, { multiline: true })}
                  ${draftSourceField(`tracked_content.roadmap.phases.${phaseIndex}.stories.${storyIndex}.acceptance_criteria.${criterionIndex}`, criterion, criterionId)}
                  <button type="button" data-remove-criterion="${phaseIndex}:${storyIndex}:${criterionIndex}"${story.acceptance_criteria.length === 1 ? " disabled" : ""}>Remove criterion</button></div>`;
              }).join("")}<button type="button" data-add-criterion="${phaseIndex}:${storyIndex}">Add acceptance criterion</button></fieldset>
              <button type="button" class="danger" data-remove-story="${phaseIndex}:${storyIndex}"${phase.stories.length === 1 ? " disabled" : ""}>Remove story</button>
            </fieldset>`;
          }).join("")}<button type="button" data-add-story="${phaseIndex}">Add story</button></div>
          <button type="button" class="danger" data-remove-phase="${phaseIndex}"${roadmap.phases.length === 1 ? " disabled" : ""}>Remove phase</button>
        </fieldset>`;
      }).join("")}<button type="button" data-add-phase>Add phase</button></div>
      <fieldset class="ideation-exit-editor"><legend>Roadmap result</legend>${roadmap.exit_criteria.map((criterion, index) => {
        const itemId = `exit-criterion-${index + 1}`;
        return `<div data-draft-item="${itemId}">${objection.has(itemId) ? `<div class="ideation-correction" role="alert"><strong>Correction requested:</strong> ${esc(objection.get(itemId))}</div>` : ""}
          ${draftField("Result to prove", `tracked_content.roadmap.exit_criteria.${index}.text`, criterion.text, itemId, { multiline: true })}
          ${draftSourceField(`tracked_content.roadmap.exit_criteria.${index}`, criterion, itemId)}</div>`;
      }).join("")}</fieldset>
      <div class="ideation-actions"><button type="button" data-back-idea>Back to idea</button><button type="submit" class="applybtn">Review the whole plan</button></div>
    </form>
  </section>`);
  wireDraftStep();
}

function wireDraftStep() {
  const form = document.getElementById("ideation-draft-form");
  form.addEventListener("input", (event) => {
    const input = event.target.closest("[data-draft-path]");
    if (!input) return;
    const value = input.type === "number" ? Number(input.value) : input.value;
    setProposalPath(input.dataset.draftPath, value);
    resolveReviewItem(input.dataset.reviewItem);
    invalidateIdeationPreview();
    persistIdeation();
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    await moveIdeationStep("review");
  });
  form.querySelector("[data-back-idea]").addEventListener("click", () => moveIdeationStep("idea"));
  form.querySelectorAll("[data-add-criterion]").forEach((button) => button.addEventListener("click", () => {
    const [phaseIndex, storyIndex] = button.dataset.addCriterion.split(":").map(Number);
    ideationState.proposal.tracked_content.roadmap.phases[phaseIndex].stories[storyIndex].acceptance_criteria.push(sourceText("Describe one observable result."));
    invalidateIdeationPreview(); persistIdeation(); renderDraftStep();
    focusRegion(`[data-draft-item="story-${selectorEscape(ideationState.proposal.tracked_content.roadmap.phases[phaseIndex].stories[storyIndex].id_sketch)}-criterion-${ideationState.proposal.tracked_content.roadmap.phases[phaseIndex].stories[storyIndex].acceptance_criteria.length}"]`);
  }));
  form.querySelectorAll("[data-remove-criterion]").forEach((button) => button.addEventListener("click", () => {
    const [phaseIndex, storyIndex, criterionIndex] = button.dataset.removeCriterion.split(":").map(Number);
    const story = ideationState.proposal.tracked_content.roadmap.phases[phaseIndex].stories[storyIndex];
    resolveReviewItem(`story-${story.id_sketch}-criterion-${criterionIndex + 1}`);
    story.acceptance_criteria.splice(criterionIndex, 1);
    invalidateIdeationPreview(); persistIdeation(); renderDraftStep();
    focusRegion(`[data-draft-item="story-${selectorEscape(story.id_sketch)}"]`);
  }));
  form.querySelectorAll("[data-add-story]").forEach((button) => button.addEventListener("click", () => {
    const phaseIndex = Number(button.dataset.addStory);
    const phase = ideationState.proposal.tracked_content.roadmap.phases[phaseIndex];
    phase.stories.push(storyDraft(ideationState.proposal.project.prefix, phase.number, phase.stories.length + 1, ideationState.rough_idea));
    invalidateIdeationPreview(); persistIdeation(); renderDraftStep();
    focusRegion(`[data-draft-item="story-${selectorEscape(phase.stories.at(-1).id_sketch)}"]`);
  }));
  form.querySelectorAll("[data-remove-story]").forEach((button) => button.addEventListener("click", () => {
    const [phaseIndex, storyIndex] = button.dataset.removeStory.split(":").map(Number);
    const phase = ideationState.proposal.tracked_content.roadmap.phases[phaseIndex];
    resolveReviewItem(`story-${phase.stories[storyIndex].id_sketch}`);
    phase.stories.splice(storyIndex, 1);
    invalidateIdeationPreview(); persistIdeation(); renderDraftStep();
    focusRegion(`[data-draft-item="phase-${selectorEscape(phase.number)}"]`);
  }));
  form.querySelector("[data-add-phase]").addEventListener("click", () => {
    const phases = ideationState.proposal.tracked_content.roadmap.phases;
    const number = Math.max(...phases.map((phase) => Number(phase.number))) + 1;
    phases.push({ number, title: `Phase ${number}`, goal: "Describe the next reviewable outcome.", provenance: source("recommendation", "Added in the Workbench draft."), stories: [storyDraft(ideationState.proposal.project.prefix, number, 1, ideationState.rough_idea)] });
    invalidateIdeationPreview(); persistIdeation(); renderDraftStep();
    focusRegion(`[data-draft-item="phase-${number}"]`);
  });
  form.querySelectorAll("[data-remove-phase]").forEach((button) => button.addEventListener("click", () => {
    const phaseIndex = Number(button.dataset.removePhase);
    const phase = ideationState.proposal.tracked_content.roadmap.phases[phaseIndex];
    resolveReviewItem(`phase-${phase.number}`);
    phase.stories.forEach((story) => resolveReviewItem(`story-${story.id_sketch}`));
    ideationState.proposal.tracked_content.roadmap.phases.splice(phaseIndex, 1);
    invalidateIdeationPreview(); persistIdeation(); renderDraftStep();
    focusRegion(".ideation-phase-editor");
  }));
}

function renderIdeaStep() {
  app.innerHTML = ideationShell("idea", `<section class="ideation-step ideation-idea" aria-labelledby="ideation-idea-title">
    <p class="eyebrow ops-label">Step 1 of 5 · start with your words</p><h1 id="ideation-idea-title" tabindex="-1">Turn a rough idea into a phase plan</h1>
    <p class="ideation-lede">Write what you want to make or change. The Workbench will shape a small editable first draft. Nothing is saved yet.</p>
    <form id="ideation-idea-form"><label><b>Rough idea</b><textarea name="idea" required maxlength="20000" placeholder="For example: Help a small team capture customer requests and turn them into a weekly plan.">${esc(ideationState.rough_idea)}</textarea></label>
      <div class="ideation-inert"><strong>Drafting is safe.</strong><span>No project files, work, permission, or process are created.</span></div>
      <button type="submit" class="applybtn">Shape this idea</button></form>
    ${ideationState.proposal ? '<button type="button" class="quiet-link" data-resume-draft>Resume saved browser draft</button>' : ""}
  </section>`);
  const form = document.getElementById("ideation-idea-form");
  form.elements.idea.addEventListener("input", () => {
    ideationState.rough_idea = form.elements.idea.value;
    persistIdeation();
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    ideationState.rough_idea = form.elements.idea.value.trim();
    ideationState.proposal = proposalFromIdea(ideationState.rough_idea);
    ideationState.review = normalizedReviewState();
    ideationState.review_model = null;
    invalidateIdeationPreview();
    await moveIdeationStep("draft");
  });
  document.querySelector("[data-resume-draft]")?.addEventListener("click", () => moveIdeationStep("draft"));
}

function reviewStorageKey(model) {
  return `ideation-${model.technical_details.proposal_hash}`;
}

async function renderReviewStep() {
  const { status, body } = await postJson("/api/setup/review", { proposal: ideationState.proposal });
  const model = body.data;
  ideationState.review_model = model;
  if (status >= 400 || body.ok === false || !model?.valid) {
    const refusal = model?.refusal || boardMutationError(body, status);
    app.innerHTML = ideationShell("review", `<section class="ideation-step ideation-review" aria-labelledby="ideation-review-title">
      <p class="eyebrow ops-label">Step 3 of 5 · review</p><h1 id="ideation-review-title" tabindex="-1">The draft needs a correction</h1>
      <div class="guard" role="alert"><strong>Review refused. Nothing was saved.</strong> ${esc(refusal)}</div>
      <button type="button" data-edit-draft>Return to the draft</button></section>`);
    document.querySelector("[data-edit-draft]").addEventListener("click", () => moveIdeationStep("draft"));
    return;
  }
  const key = reviewStorageKey(model);
  adoptionReviewMarks.set(key, normalizedReviewState(ideationState.review));
  const refreshStatuses = () => {
    document.querySelectorAll("[data-review-item]").forEach((element) => {
      const status = adoptionItemStatus(adoptionMarkState(key), element.dataset.reviewItem);
      element.dataset.reviewState = status[1];
    });
  };
  app.innerHTML = ideationShell("review", `<section class="ideation-step ideation-review" aria-label="Review the proposed setup">
    ${adoptionReviewBody(model, key)}
    <div id="adoption-marks"></div>
    ${technicalDetailsHtml(model)}
    <button type="button" class="quiet-link" data-edit-draft>Edit the draft</button>
  </section>`);
  renderAdoptionMarks(model, key, null, {
    persist: (state) => { ideationState.review = normalizedReviewState(state); persistIdeation(); },
    editDraft: () => moveIdeationStep("draft"),
    onPreview: previewIdeationSetup,
    refreshStatuses,
  });
  wireTechnicalReturn();
  document.querySelector("[data-edit-draft]").addEventListener("click", () => moveIdeationStep("draft"));
  if (IDEATION_SNAPSHOT_STEP === "review" && !ideationState.review.accepted_items.length) {
    ideationState.review.accepted_items = model.objection_items.slice(0, Math.max(1, model.objection_items.length - 1)).map((item) => item.id);
    persistIdeation();
    adoptionReviewMarks.set(key, normalizedReviewState(ideationState.review));
    renderAdoptionMarks(model, key, null, { persist: (state) => { ideationState.review = state; }, editDraft: () => {}, onPreview: () => {}, refreshStatuses });
  }
}

function previewChangesHtml(preview) {
  return `<div class="ideation-preview-files">${preview.changes.map((change) => `<article>
    <div>${badge(change.action, change.action === "unchanged" ? "warn" : "ok")}<strong>${change.scope === "tracked" ? "Repository file" : "Local configuration"}</strong></div>
    <code>${esc(change.path)}</code>
    <dl><div><dt>Before</dt><dd><code>${esc(change.before_hash || "absent")}</code></dd></div><div><dt>After</dt><dd><code>${esc(change.after_hash)}</code></dd></div></dl>
  </article>`).join("")}</div>`;
}

async function previewIdeationSetup() {
  const proposal = JSON.parse(JSON.stringify(ideationState.proposal));
  proposal.state = "reviewed";
  const signature = JSON.stringify(proposal);
  const { status, body } = await postJson("/api/setup/preview", { proposal });
  if (status >= 400 || body.ok === false) {
    ideationState.refusal = boardMutationError(body, status);
    ideationState.preview = null;
    persistIdeation();
    await moveIdeationStep("preview");
    return;
  }
  ideationState.proposal = proposal;
  ideationState.preview = body.data;
  ideationState.draft_signature = signature;
  ideationState.refusal = "";
  persistIdeation();
  await moveIdeationStep("preview");
}

function plainSetupRefusal(message) {
  const lower = String(message || "").toLowerCase();
  if (lower.includes("already used")) return "That one-use preview was already applied. Create a fresh preview before trying again.";
  if (lower.includes("stale") || lower.includes("changed")) return "The repository changed after preview. Nothing was saved; review a fresh preview of the current files.";
  if (lower.includes("unknown") || lower.includes("requires proposal") || lower.includes("requires expect")) return "The matching setup preview is missing. Nothing was saved; return to review and create a fresh preview.";
  if (lower.includes("token") || lower.includes("match")) return "This preview no longer matches the setup plan. Nothing was saved; create a fresh preview.";
  return `Setup was refused and nothing was saved. ${message || "Create a fresh preview and try again."}`;
}

function renderPreviewStep() {
  const preview = ideationState.preview;
  const refusal = ideationState.refusal;
  app.innerHTML = ideationShell("preview", `<section class="ideation-step ideation-preview" aria-labelledby="ideation-preview-title">
    <p class="eyebrow ops-label">Step 4 of 5 · exact preview</p><h1 id="ideation-preview-title" tabindex="-1">${refusal ? "This setup was refused" : "Review the exact setup"}</h1>
    ${refusal ? `<div class="guard ideation-refusal" role="alert" tabindex="-1"><strong>Nothing changed.</strong> ${esc(plainSetupRefusal(refusal))}</div>` : `<p>These are the exact configuration files this one-use lease can create. No work, run, program, permission, proof approval, or commit is included.</p>
      ${previewChangesHtml(preview)}
      <details class="ideation-preview-technical"><summary>Technical details</summary><pre>${esc(JSON.stringify(preview, null, 2))}</pre></details>`}
    <div class="ideation-actions"><button type="button" data-edit-after-preview>Edit draft</button>
      ${preview ? '<button type="button" class="applybtn" id="ideation-apply">Apply this exact setup</button>' : '<button type="button" data-fresh-review>Return to review</button>'}</div>
  </section>`);
  document.querySelector("[data-edit-after-preview]").addEventListener("click", () => {
    invalidateIdeationPreview("Draft editing invalidated the old setup preview.");
    moveIdeationStep("draft");
  });
  document.querySelector("[data-fresh-review]")?.addEventListener("click", () => {
    ideationState.refusal = ""; persistIdeation(); moveIdeationStep("review");
  });
  document.getElementById("ideation-apply")?.addEventListener("click", applyIdeationSetup);
  if (refusal && !SNAPSHOT_MODE) focusRegion(".ideation-refusal");
}

async function applyIdeationSetup() {
  const button = document.getElementById("ideation-apply");
  button.disabled = true;
  button.textContent = "Applying configuration…";
  const preview = ideationState.preview;
  const { status, body } = await postJson("/api/setup/apply", {
    proposal: preview?.proposal_id || "",
    expect: preview?.expect || "",
  });
  if (status >= 400 || body.ok === false) {
    ideationState.refusal = boardMutationError(body, status);
    persistIdeation();
    renderPreviewStep();
    return;
  }
  ideationState.applied = body.data;
  ideationState.step = "apply";
  persistIdeation();
  await viewIdeationFlow();
  focusRegion(".ideation-applied h1");
}

function renderAppliedStep() {
  const applied = ideationState.applied || { changes: ideationState.preview?.changes || [] };
  app.innerHTML = ideationShell("apply", `<section class="ideation-step ideation-applied" aria-labelledby="ideation-applied-title">
    <p class="eyebrow ops-label">Step 5 of 5 · configuration saved</p><h1 id="ideation-applied-title" tabindex="-1">The phase plan is configured</h1>
    <div class="ideation-success"><strong>Configuration only.</strong><span>No story, run, program, permission, proof approval, or commit was started.</span></div>
    <p>${esc((applied.changes || []).length)} planned path${(applied.changes || []).length === 1 ? " was" : "s were"} applied through the one-use setup lease.</p>
    <details><summary>Technical details</summary><pre>${esc(JSON.stringify(applied, null, 2))}</pre></details>
    <div class="ideation-actions"><a class="canonical-primary" href="#/board/${encodeURIComponent(ideationState.proposal?.project?.slug || "")}">Open the configured board</a>
      <button type="button" data-new-idea>Plan another idea</button></div>
  </section>`);
  document.querySelector("[data-new-idea]").addEventListener("click", () => {
    ideationState = blankIdeationState();
    clearStoredJson(IDEATION_STORAGE_KEY);
    moveIdeationStep("idea");
  });
}

function snapshotIdeationState(step) {
  const state = blankIdeationState();
  state.rough_idea = "Help a small team turn customer requests into a calm weekly plan.";
  state.proposal = proposalFromIdea(state.rough_idea);
  state.step = step === "refusal" ? "preview" : step === "applied" ? "apply" : step;
  const fakeChanges = [{
    path: `pm/roadmap/${state.proposal.project.slug}/README.md`, scope: "tracked", action: "create",
    before_hash: null, after_hash: "sha256:6a9e5f2c9e3b7d1a",
  }, {
    path: ".git/pmo-orchestration/drivers.json", scope: "git-local", action: "create",
    before_hash: null, after_hash: "sha256:9d3c2a1b7f4e8a60",
  }];
  if (["preview", "refusal", "applied"].includes(step)) state.preview = {
    kind: "delivery-workbench-setup-preview", schema_version: 1,
    proposal_id: "setup:preview-example", expect: "setup-sha256:one-use-example",
    proposal_hash: "sha256:proposal-example", applicable: true, changes: fakeChanges,
    starts_work: false, creates_grant: false, certifies: false, commits: false,
  };
  if (step === "refusal") { state.preview = null; state.refusal = "setup lease was already used"; }
  if (step === "applied") state.applied = { kind: "delivery-workbench-setup-apply", changes: fakeChanges, starts_work: false, creates_grant: false };
  return state;
}

async function viewIdeationFlow() {
  if (SNAPSHOT_MODE && IDEATION_SNAPSHOT_STEP) ideationState = snapshotIdeationState(IDEATION_SNAPSHOT_STEP);
  if (!ideationState.proposal && ideationState.step !== "idea") ideationState.step = "idea";
  if (ideationState.step === "idea") renderIdeaStep();
  else if (ideationState.step === "draft") renderDraftStep();
  else if (ideationState.step === "review") await renderReviewStep();
  else if (ideationState.step === "preview") renderPreviewStep();
  else renderAppliedStep();
  enhanceSemantics(app);
}

async function viewAdoptionReview() {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "roadmap changes", href: "#/edit" }, { label: "idea to phase plan" }]);
  if (ADOPTION_PROPOSAL_FILE || ADOPTION_PROPOSAL_ID) await viewLegacyAdoptionReview();
  else await viewIdeationFlow();
}


const STATUS_VOCAB = ["backlog", "ready", "in-progress", "blocked", "on-hold", "done"];

function field(label, inner, err) {
  const fieldId = `edit-${label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "")}`;
  const errorId = `${fieldId}-error`;
  const describedControl = inner.replace(
    /^<(input|select|textarea)\b/,
    `<$1 id="${fieldId}" aria-describedby="${errorId}"${err ? ' aria-invalid="true"' : ""}`,
  );
  return `<label for="${fieldId}"><b>${esc(label)}</b>${describedControl}
    <span id="${errorId}" class="fielderr" data-err="${esc(label)}">${err ? esc(err) : ""}</span></label>`;
}

function selectHtml(name, options, selected) {
  return `<select name="${name}">` + options.map((o) =>
    `<option value="${esc(o)}"${o === selected ? " selected" : ""}>${esc(o)}</option>`).join("") + "</select>";
}

async function viewEdit(action) {
  action = action || "create_story";
  if (action === "adoption_review") {
    await viewAdoptionReview();
    return;
  }
  setCrumbs([{ label: "overview", href: "#/" }, { label: "edit" }, { label: EDIT_ACTIONS[action] || action }]);
  const ctx = await api("/api/projects");
  const projects = ctx.data.projects;
  if (!projects.length) {
    app.innerHTML = stateHtml("No projects to edit.");
    return;
  }
  const proj = projects.find((project) => project.slug === selectedProject);
  if (!proj) {
    viewUnavailableProject(selectedProject || "the chosen project");
    return;
  }
  const guarded = proj.issue_count > 0;
  const projDetail = await api(`/api/projects/${encodeURIComponent(proj.slug)}`);
  const phases = projDetail.data.phases;
  const phaseOpts = phases.map((ph) => String(ph.number));
  const stories = phases.flatMap((ph) => ph.stories.map((s) => s.story_id));

  const tabs = Object.keys(EDIT_ACTIONS).map((a) =>
    `<a href="#/edit/${a}" class="${a === action ? "active" : ""}">${esc(EDIT_ACTIONS[a])}</a>`).join("");

  let formFields = "";
  if (action === "create_phase") {
    formFields = [
      field("phase number", '<input type="number" name="number" min="0" step="1" required>'),
      field("title", '<input type="text" name="title" required>'),
      field("slug (optional)", '<input type="text" name="slug" pattern="[a-z0-9-]*" title="lowercase, digits, hyphens">'),
      field("goal (one line)", '<input type="text" name="goal">'),
    ].join("");
  } else if (action === "create_story") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("title", '<input type="text" name="title" required>'),
      field("initial status", selectHtml("status", STATUS_VOCAB.filter((s) => s !== "done"), "backlog")),
    ].join("");
  } else if (action === "update_story_status") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("story", selectHtml("story", stories)),
      field("new status", selectHtml("status", STATUS_VOCAB)),
      field("reason (required for blocked/on-hold parks — recorded in the status cell)",
        '<input type="text" name="reason" placeholder="why is this waiting?">'),
      field("evidence body (required for done when no evidence exists)",
        '<textarea name="evidence_body" placeholder="- proof line…"></textarea>'),
      `<div class="checkline"><input type="checkbox" name="force" id="f-force">
        <label for="f-force">force: replace existing evidence</label></div>`,
    ].join("");
  } else if (action === "pause_phase") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("reason (required)", '<input type="text" name="reason" required placeholder="why should this phase wait?">'),
    ].join("");
  } else if (action === "resume_phase") {
    formFields = [field("phase", selectHtml("phase", phaseOpts))].join("");
  } else if (action === "attach_evidence") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("story", selectHtml("story", stories)),
      field("evidence body", '<textarea name="body" placeholder="- proof line…"></textarea>'),
      `<div class="checkline"><input type="checkbox" name="force" id="f-force">
        <label for="f-force">force: replace existing evidence</label></div>`,
    ].join("");
  } else if (action === "close_phase") {
    formFields = [
      field("phase", selectHtml("phase", phaseOpts)),
      field("final summary body", '<textarea name="summary_body" placeholder="## Outcome vs exit criteria…"></textarea>'),
      `<div class="checkline"><input type="checkbox" name="force" id="f-force">
        <label for="f-force">force: close with open stories / replace an existing summary (core force semantics)</label></div>`,
    ].join("");
  }

  app.innerHTML = `${destinationNav("plan", "#/edit")}
    <header class="destination-hero"><span>Plan</span><h1>Review a roadmap change</h1><p>Choose one change, review exactly what it would affect, then decide whether to continue.</p></header>
    <div class="tabs">${tabs}</div>
    ${guarded ? `<div class="guard">Changes are paused — <a href="#/health">review ${proj.issue_count} health issue${proj.issue_count === 1 ? "" : "s"}</a> first.</div>` : ""}
    <form class="edit" id="edit-form">
      ${field("project", selectHtml("project", [proj.slug], proj.slug))}
      ${formFields}
      ${guarded ? `<div class="checkline"><input type="checkbox" name="acknowledge_issues" id="f-ack">
        <label for="f-ack">I acknowledge the validation issues and still want a preview</label></div>` : ""}
      <button type="submit">preview — no files are written</button>
      <div class="hint">Preview shows exact diffs, projected validation, and a fingerprint;
        apply refuses stale previews and never commits — committing stays with you.</div>
    </form>
    <div id="preview-out"></div>`;

  const editForm = document.getElementById("edit-form");
  async function runEditPreview(form) {
    const out = document.getElementById("preview-out");
    const body = { kind: action };
    for (const el of form.elements) {
      if (!el.name) continue;
      if (el.type === "checkbox") body[el.name] = el.checked;
      else body[el.name] = el.value.trim();
    }
    // client-side refusals before the server's authoritative ones
    if (action === "update_story_status" && body.status === "on-hold" && !body.reason) {
      out.innerHTML = `<div class="guard">refused client-side: a hold needs its why — fill the reason before previewing.</div>`;
      return;
    }
    if (action === "update_story_status" && body.status === "done" && !body.evidence_body) {
      const st = phases.flatMap((ph) => ph.stories).find((s) => s.story_id === body.story);
      if (st && !st.evidence_exists) {
        out.innerHTML = `<div class="guard">refused client-side: marking ${esc(body.story)} done requires
          evidence — none exists and no evidence body was provided.</div>`;
        return;
      }
    }
    out.innerHTML = stateHtml("Previewing…");
    try {
      const { status, body: payload } = await postJson("/api/mutations/preview", body);
      if (status >= 400 || payload.ok === false) {
        const msg = (payload.data && payload.data.error) || (payload.issues && payload.issues[0]) || `error ${status}`;
        out.innerHTML = `<div class="guard">${esc(msg)}</div>` +
          (payload.data && payload.data.issues
            ? `<ul class="plain">${payload.data.issues.map((i) => `<li class="issue">${esc(i)}</li>`).join("")}</ul>` : "");
        return;
      }
      const d = payload.data;
      out.innerHTML = `
        <div class="section"><h2>Preview — ${esc(d.kind)} ${badge("nothing written yet", "ok")}
          ${d.no_op ? badge("no-op: repeating this mutation changes nothing", "warn") : ""}</h2>
          <div class="meta">
            ${Object.entries(d.summary).map(([k, v]) =>
              `<div class="kv"><div class="k">${esc(k)}</div><div class="v">${esc(String(v))}</div></div>`).join("")}
            <div class="kv"><div class="k">fingerprint</div><div class="v">${esc(d.fingerprint.slice(0, 24))}…</div></div>
          </div>
          ${d.issues_before && d.issues_before.length ? `<div class="section"><h2>Validation before write</h2>
            <ul class="plain">${d.issues_before.map((i) => `<li class="issue">${esc(i)}</li>`).join("")}</ul></div>` : ""}
          ${d.issues_after === null ? `<p class="hint">projected post-write validation unavailable</p>`
            : d.issues_after.length ? `<div class="section"><h2>Projected validation after write</h2>
            <ul class="plain">${d.issues_after.map((i) => `<li class="warn">${esc(i)}</li>`).join("")}</ul></div>`
            : `<p class="hint">projected post-write validation: clean</p>`}
          ${d.create_dirs.length ? `<p class="hint">creates directory: <code>${d.create_dirs.map(esc).join(", ")}</code></p>` : ""}
          ${d.files.map((f) => `
            <details class="filepreview" ${f.changed ? "open" : ""}>
              <summary>${badge(f.action === "create" ? "new file" : f.changed ? "changed" : "unchanged (owned)",
                  f.action === "create" ? "ok" : f.changed ? "in-progress" : "warn")}
                <code>${esc(f.path)}</code>
                <span class="hint">${f.bytes_before} → ${f.bytes_after} bytes</span></summary>
              ${f.action === "create"
                ? `<pre class="src">${esc(f.new_content || "")}</pre>`
                : f.diff ? `<pre class="diff">${diffHtml(f.diff)}</pre>` : `<pre class="src">${esc(f.new_content || "")}</pre>`}
            </details>`).join("")}
          <button type="button" class="applybtn" id="apply-btn">apply — writes the files above (no commit)</button>
        </div>`;
      document.getElementById("apply-btn").addEventListener("click", async () => {
        out.querySelector("#apply-btn").disabled = true;
        const { status: st, body: applied } = await postJson("/api/mutations/apply", { ...body, fingerprint: d.fingerprint });
        const resultBox = document.createElement("div");
        if (st === 409) {
          resultBox.innerHTML = `<div class="guard">stale preview refused — the source files changed after this
            preview was taken; nothing was written. Re-run the preview for a fresh fingerprint.</div>`;
        } else if (st >= 400 || applied.ok === false) {
          const msg = (applied.data && applied.data.error) || `apply failed (${st})`;
          resultBox.innerHTML = `<div class="guard">${esc(msg)}${applied.data && applied.data.rolled_back
            ? " — all writes were rolled back" : ""}</div>`;
        } else {
          const r = applied.data;
          resultBox.innerHTML = `
            <div class="guard ok">applied: ${r.changed.length} file${r.changed.length === 1 ? "" : "s"} written (no commit made)</div>
            <div class="section"><h2>Post-apply revalidation</h2>
              ${r.issues.length ? `<ul class="plain">${r.issues.map((i) => `<li class="issue">${esc(i)}</li>`).join("")}</ul>`
                : `<p class="hint">dw check: clean — <a href="#/p/${encodeURIComponent(body.project)}">view the refreshed project</a></p>`}
              <ul class="plain">${r.changed.map((c) => `<li><a href="#/f/${encodeURIComponent(c)}"><code>${esc(c)}</code></a></li>`).join("")}</ul>
            </div>`;
        }
        out.appendChild(resultBox);
      });
    } catch (err) {
      out.innerHTML = `<div class="guard">${esc(err.message)}</div>`;
    }
  }

  editForm.addEventListener("submit", (e) => {
    e.preventDefault();
    runEditPreview(e.target);
  });
  // Screenshot affordance: ?snapshot=1&autopreview=1 runs the preview
  // with the form defaults inside this synchronous load chain so
  // headless capture sees the rendered result. Not for interactive use.
  if (SNAPSHOT_MODE && new URLSearchParams(location.search).has("autopreview")) {
    await runEditPreview(editForm);
  }
}
