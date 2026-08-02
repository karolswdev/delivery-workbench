"use strict";

/* ── delivery-shaped front door (WLA-27-03) ────────────────────────
 * This is a renderer over /api/delivery-setup. Choosing, cancelling, and
 * opening Technical details are browser-local navigation only. A bounded
 * delivery still crosses the existing run-plan/start boundary; a program
 * draft still crosses Program Studio preview/apply and a later separate
 * program start. */

let deliverySetupState = {
  model: null, choice: "", project: "", phase: "", technical: false,
};
let pendingProgramSetup = null;

function setupEffectList(items, emptyText) {
  return items?.length
    ? `<ul>${items.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`
    : `<p>${esc(emptyText)}</p>`;
}

function deliveryChoiceCard(choice) {
  const selected = deliverySetupState.choice === choice.id;
  const titleId = `delivery-choice-${choice.id}-title`;
  const summaryId = `delivery-choice-${choice.id}-summary`;
  return `<article class="delivery-choice${selected ? " selected" : ""}" data-choice="${esc(choice.id)}">
    <div class="delivery-choice-head"><span>${esc(choice.tier === "vanilla" ? "ordinary roadmap" : choice.tier === "bounded-run" ? "one bounded delivery" : "optional delivery program")}</span>${badge(choice.readiness, choice.available ? "ok" : "warn")}</div>
    <h2 id="${titleId}">${esc(choice.label)}</h2><p id="${summaryId}">${esc(choice.summary)}</p>
    ${choice.recommended ? '<strong class="delivery-default">Ready now · no optional setup</strong>' : ""}
    ${choice.correction ? `<div class="delivery-correction"><strong>Affected decision</strong><span>${esc(choice.correction)}</span></div>` : ""}
    <button type="button" data-delivery-choice="${esc(choice.id)}" aria-pressed="${selected ? "true" : "false"}" aria-labelledby="${titleId}" aria-describedby="${summaryId}">Review this option</button>
  </article>`;
}

function deliveryChoiceReview(model, choice) {
  if (!choice) return `<section class="delivery-review empty"><h2>Choose how much coordination this delivery needs</h2><p>No option is selected for you. Ordinary roadmap work remains ready while you compare the optional paths.</p></section>`;
  const scope = model.delivery_scope || {};
  const project = deliverySetupState.project || scope.selected_project || "";
  const phase = deliverySetupState.phase;
  const actionLabel = choice.id === "roadmap"
    ? (choice.available ? "Continue with the roadmap" : "Resolve readiness first")
    : choice.id === "bounded"
      ? (choice.available ? "Review delivery readiness" : "Open delivery plans")
      : (choice.available ? "Continue to a delivery-plan draft" : "Choose a project first");
  const continueAllowed = choice.id === "bounded" || choice.available;
  return `<section class="delivery-review" id="delivery-review" role="dialog" aria-modal="false" tabindex="-1" aria-labelledby="delivery-review-title">
    <header><div><span>Review before continuing</span><h2 id="delivery-review-title">${esc(choice.label)}</h2></div>${badge("nothing started", "ok")}</header>
    <div class="delivery-effect-grid">
      <section><h3>What setup creates</h3>${setupEffectList(choice.creates_during_setup, "Nothing.")}</section>
      <section><h3>What could change later</h3>${setupEffectList(choice.may_change_after_confirmation, "Nothing through this option.")}</section>
      <section><h3>What stays off</h3>${setupEffectList(choice.remains_disabled, "No additional delivery mode.")}</section>
      <section><h3>Permission still needed</h3><p>${esc(choice.separate_permission || "No optional delivery permission is requested.")}</p></section>
    </div>
    ${choice.correction ? `<div class="delivery-next"><strong>Next step</strong><span>${esc(choice.correction)}</span></div>` : ""}
    <div class="delivery-review-actions">
      <button type="button" id="delivery-continue"${continueAllowed ? "" : " disabled"}>${esc(actionLabel)}</button>
      <button type="button" id="delivery-back">Compare options</button>
      <button type="button" id="delivery-cancel">Leave for now</button>
    </div>
    <p class="delivery-unchanged">Leaving, comparing, or opening details creates no delivery plan, permission, run, process, observer, notification, network activity, or roadmap change.</p>
    <span hidden data-delivery-project="${esc(project)}" data-delivery-phase="${esc(phase)}"></span>
  </section>`;
}

function deliveryTechnicalDetails(model) {
  const details = model.technical_details || {};
  return `<details class="delivery-technical"${deliverySetupState.technical ? " open" : ""}>
    <summary>${esc(details.label || "Technical details")}</summary>
    <p>Exact source models and inspection commands. These reads confer no authority.</p>
    <div class="delivery-source-list">${(details.sources || []).map((source) => `<div><code>${esc(source.kind)}@${esc(source.schema_version)}</code><span>${esc(source.route)}</span></div>`).join("")}</div>
    <div class="delivery-command-list">${Object.entries(details.commands || {}).map(([name, command]) => `<div><span>${esc(name.replaceAll("_", " "))}</span><code>${esc(command.join(" "))}</code></div>`).join("")}</div>
  </details>`;
}

function renderDeliverySetup() {
  const focus = captureAppFocus();
  const model = deliverySetupState.model;
  if (!model) {
    app.innerHTML = stateHtml("Checking delivery readiness…");
    finishDynamicRender(focus);
    return;
  }
  const scope = model.delivery_scope || {};
  const projects = scope.projects || [];
  const current = projects.find((item) => item.slug === deliverySetupState.project)
    || projects.find((item) => item.slug === scope.selected_project);
  const work = current?.next_work || scope.current_work;
  const phase = current?.current_phase || scope.current_phase;
  if (!deliverySetupState.project && scope.selected_project) deliverySetupState.project = scope.selected_project;
  if (!deliverySetupState.phase && phase?.number !== undefined) deliverySetupState.phase = String(phase.number);
  const choice = setupChoice(model, deliverySetupState.choice);
  app.innerHTML = `${destinationNav("plan", "#/program-studio")}<div class="delivery-setup" data-readiness="${esc(model.readiness)}">
    <header class="delivery-setup-hero"><div><span>Plan your delivery</span><h1>What are you delivering?</h1><p>${esc(model.summary)} Nothing starts until you review and confirm it.</p></div>${badge(model.readiness, model.readiness === "ready" ? "ok" : "issue")}</header>
    <section class="delivery-scope" aria-labelledby="delivery-scope-title"><div><span>Step 1</span><h2 id="delivery-scope-title">Choose the delivery scope</h2></div>
      <label>Roadmap project<select id="delivery-project"><option value="">Choose a project</option>${projects.map((item) => `<option value="${esc(item.slug)}"${item.slug === deliverySetupState.project ? " selected" : ""}>${esc(item.slug)}</option>`).join("")}</select></label>
      <label>Phase to review<input id="delivery-phase" type="number" min="0" value="${esc(deliverySetupState.phase)}" inputmode="numeric"></label>
      <div class="delivery-current-work"><span>Current work</span><strong>${esc(work?.title || "Choose a project to see current work")}</strong><small>${work ? `${esc(work.story_id)} · ${esc(work.status)}` : "No work is inferred."}</small></div>
    </section>
    ${(model.issues || []).map((issue) => `<div class="delivery-issue" role="status"><strong>${esc(issue.decision)}</strong><span>${esc(issue.summary)}</span><small>${esc(issue.next_step)}</small></div>`).join("")}
    <section class="delivery-choice-step" aria-labelledby="delivery-choice-title"><div><span>Step 2</span><h2 id="delivery-choice-title">Choose the operating mode</h2><p>Compare all three. A higher mode is never selected or started for you.</p></div>
      <div class="delivery-choice-grid" role="group" aria-labelledby="delivery-choice-title">${(model.choices || []).map(deliveryChoiceCard).join("")}</div>
    </section>
    ${deliveryChoiceReview(model, choice)}
    ${deliveryTechnicalDetails(model)}
  </div>`;
  wireDeliverySetup();
  finishDynamicRender(focus);
}

function wireDeliverySetup() {
  document.getElementById("delivery-project")?.addEventListener("change", async (event) => {
    deliverySetupState.project = event.target.value;
    if (deliverySetupState.project) rememberProject(deliverySetupState.project);
    deliverySetupState.phase = "";
    deliverySetupState.choice = "";
    const query = deliverySetupState.project
      ? `?project=${encodeURIComponent(deliverySetupState.project)}`
      : "";
    deliverySetupState.model = (await api(`/api/delivery-setup${query}`)).data;
    renderDeliverySetup();
  });
  document.getElementById("delivery-phase")?.addEventListener("input", (event) => {
    deliverySetupState.phase = event.target.value;
  });
  document.querySelectorAll("[data-delivery-choice]").forEach((button) => button.addEventListener("click", () => {
    rememberReturnFocus("delivery-review", button);
    deliverySetupState.choice = button.dataset.deliveryChoice;
    renderDeliverySetup();
    document.getElementById("delivery-review")?.focus();
  }));
  document.getElementById("delivery-back")?.addEventListener("click", () => {
    const selected = deliverySetupState.choice;
    deliverySetupState.choice = "";
    renderDeliverySetup();
    restoreReturnFocus(
      "delivery-review",
      `[data-delivery-choice="${selectorEscape(selected)}"]`,
    );
  });
  document.getElementById("delivery-cancel")?.addEventListener("click", () => {
    pendingProgramSetup = null;
    location.hash = "#/";
  });
  document.getElementById("delivery-continue")?.addEventListener("click", () => {
    const choice = setupChoice(deliverySetupState.model, deliverySetupState.choice);
    if (!choice) return;
    if (choice.id === "bounded") orchState.view = "validate";
    if (choice.id === "program") {
      pendingProgramSetup = {
        project: deliverySetupState.project,
        phase: deliverySetupState.phase,
      };
    }
    location.hash = choice.route;
  });
  document.querySelector(".delivery-technical")?.addEventListener("toggle", (event) => {
    deliverySetupState.technical = event.currentTarget.open;
  });
  const closeReview = () => {
    const selected = deliverySetupState.choice;
    deliverySetupState.choice = "";
    renderDeliverySetup();
    restoreReturnFocus(
      "delivery-review",
      `[data-delivery-choice="${selectorEscape(selected)}"]`,
    );
  };
  wireDismissibleRegion(
    "#delivery-review",
    closeReview,
    "delivery-review",
  );
  wireArrowGroup(".delivery-choice-grid", "[data-delivery-choice]");
}

async function viewDeliverySetup() {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "delivery setup" }]);
  const requested = new URLSearchParams(location.search);
  const queryProject = requested.get("setupproject") || selectedProject;
  const query = queryProject ? `?project=${encodeURIComponent(queryProject)}` : "";
  deliverySetupState.model = (await api(`/api/delivery-setup${query}`)).data;
  deliverySetupState.project = queryProject || deliverySetupState.model.delivery_scope.selected_project || "";
  deliverySetupState.phase = "";
  deliverySetupState.choice = requested.get("setupmode") || "";
  deliverySetupState.technical = requested.has("setuptechnical");
  renderDeliverySetup();
}

/* ── optional Program / Workflow Studio (WLA-26-06) ────────────────
 * This route is deliberately additive: the ordinary Workbench stays at #/.
 * The browser owns interaction and layout only. Raw policy, diagnostics,
 * graph projection, simulation, hashes, and authority explanation all arrive
 * from /api/program-studio, which delegates to the Phase-26 compilers. */

const STUDIO_FAMILIES = ["program", "workflow", "organization"];
const STUDIO_VIEWS = ["plan", "simulate", "validate", "technical", "authority"];
const STUDIO_NODE_TYPES = [
  "agent", "check", "collect", "bounded_run", "subflow", "loop",
  "debate", "verdict", "gate", "checkpoint", "rail",
];

let studioState = {
  inventory: null, family: "program", name: "", exists: false,
  document: null, model: null, compilePreview: null, view: "plan",
  selected: "", jsonDraft: "", validationTimer: null,
  scenario: "candidate-assignment", error: "", jsonPointer: "",
  setupContext: null, planSection: "scope", technicalMode: "graph",
  technicalExpanded: false,
};

function studioFamilyModel(family = studioState.family) {
  return (studioState.inventory?.families || []).find((item) => item.id === family);
}

function studioCssToken(value) {
  return String(value || "unknown").toLowerCase().replace(/[^a-z0-9_-]+/g, "-");
}

function studioFieldId(pointer) {
  return pointer ? `studio-field-${String(pointer).replace(/[^a-zA-Z0-9_-]+/g, "-").replace(/^-|-$/g, "")}` : "";
}

function studioInput(label, key, value, type = "text", attrs = "", pointer = "") {
  return `<label class="studio-field"><span>${esc(label)}</span><input ${pointer ? `id="${esc(studioFieldId(pointer))}"` : ""} data-studio-field="${esc(key)}" type="${type}" value="${esc(value ?? "")}" ${attrs}></label>`;
}

function studioArea(label, key, value, hint = "", pointer = "") {
  return `<label class="studio-field"><span>${esc(label)}</span><textarea ${pointer ? `id="${esc(studioFieldId(pointer))}"` : ""} data-studio-field="${esc(key)}">${esc(value ?? "")}</textarea>${hint ? `<small>${esc(hint)}</small>` : ""}</label>`;
}

function studioSelect(label, key, values, selected, pointer = "") {
  return `<label class="studio-field"><span>${esc(label)}</span><select ${pointer ? `id="${esc(studioFieldId(pointer))}"` : ""} data-studio-field="${esc(key)}">${values.map((value) => `<option value="${esc(value)}"${value === selected ? " selected" : ""}>${esc(value)}</option>`).join("")}</select></label>`;
}

function ensureStudioLayout() {
  const document = studioState.document;
  if (!document) return;
  document.layout ||= {};
  document.layout.nodes ||= {};
  document.layout.viewport ||= { x: 0, y: 0, zoom: 1 };
}

function studioGraphNode(id) {
  return (studioState.model?.graph?.nodes || []).find((node) => node.id === id);
}

function studioRawNode(graphNode) {
  if (!graphNode || studioState.family !== "workflow") return null;
  const match = String(graphNode.pointer || "").match(/^\/nodes\/(\d+)/);
  return match ? studioState.document.nodes?.[Number(match[1])] : null;
}

function studioGraphHtml() {
  const graph = studioState.model?.graph;
  if (!graph) return stateHtml("Waiting for the shared graph projection…");
  const nodes = graph.nodes || [];
  const byId = Object.fromEntries(nodes.map((node) => [node.id, node]));
  const maxX = Math.max(960, ...nodes.map((node) => Number(node.position?.x || 0) + 250));
  const maxY = Math.max(560, ...nodes.map((node) => Number(node.position?.y || 0) + 155));
  const diagnosticCounts = new Map();
  (studioState.model.validation?.diagnostics || []).forEach((diagnostic) => {
    const id = diagnostic.target?.node_id;
    if (id) diagnosticCounts.set(id, (diagnosticCounts.get(id) || 0) + 1);
  });
  const edges = (graph.edges || []).map((edge) => {
    const source = byId[edge.from]?.position;
    const target = byId[edge.to]?.position;
    if (!source || !target) return "";
    const failure = ["route", "separation"].includes(edge.kind);
    const x1 = Number(source.x) + 210; const y1 = Number(source.y) + 52;
    const x2 = Number(target.x); const y2 = Number(target.y) + 52;
    return `<path class="studio-edge kind-${studioCssToken(edge.kind)}" d="M ${x1} ${y1} C ${x1 + 40} ${y1}, ${x2 - 40} ${y2}, ${x2} ${y2}" marker-end="url(#studio-arrow-${failure ? "route" : "success"})"><title>${esc(edge.from)} → ${esc(edge.to)} · ${esc(edge.label || edge.kind)}</title></path>`;
  }).join("");
  return `<div class="studio-canvas-wrap" data-studio-scenario="${esc(studioState.scenario)}"><svg id="studio-canvas" class="studio-canvas" viewBox="0 0 ${maxX} ${maxY}" role="group" aria-labelledby="studio-canvas-title">
    <title id="studio-canvas-title">${esc(studioState.family)} policy graph. Nodes are keyboard selectable and movable; compiler diagnostics link back to exact nodes and fields.</title>
    <defs><marker id="studio-arrow-success" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z"></path></marker><marker id="studio-arrow-route" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z"></path></marker></defs>
    ${(graph.lanes || []).map((lane, index) => `<g class="studio-lane" data-lane="${esc(lane.id)}"><rect x="8" y="${36 + index * 175}" width="${maxX - 16}" height="152" rx="7"></rect><text x="22" y="${58 + index * 175}">${esc(lane.label)}</text></g>`).join("")}
    ${edges}
    ${nodes.map((node) => {
      const position = node.position || { x: 0, y: 0 };
      const count = diagnosticCounts.get(node.id) || 0;
      const summary = node.role || node.summary?.workflow || node.summary?.duty || node.lane || node.type;
      const bounds = Object.entries(node.bounds || {}).map(([key, value]) => `${key.replace(/^max_/, "≤ ")}: ${value}`).join(" · ");
      const drill = node.drilldown?.name ? ` · opens workflow ${node.drilldown.name}` : "";
      return `<g class="studio-node type-${studioCssToken(node.type)}${node.container ? " is-container" : ""}${studioState.selected === node.id ? " selected" : ""}${count ? " has-error" : ""}" data-studio-node="${esc(node.id)}" data-layout-key="${esc(node.layout_key || node.id)}" transform="translate(${Number(position.x)},${Number(position.y)})" tabindex="0" role="button" aria-label="${esc(node.label)}, ${esc(node.type)}, lane ${esc(node.lane)}${bounds ? `, bounded ${esc(bounds)}` : ""}${count ? `, ${count} compiler issues` : ""}${esc(drill)}">
        <title>${esc(node.label)} · ${esc(node.type)} · ${esc(summary)}${bounds ? ` · ${esc(bounds)}` : ""}${count ? ` · ${count} compiler issues` : ""}</title>
        <rect width="210" height="104" rx="${node.container ? 3 : 10}"></rect>
        <circle class="port input" cx="0" cy="52" r="5"></circle><circle class="port output" cx="210" cy="52" r="5"></circle>
        <text class="node-type" x="14" y="22">${esc(node.type)}${node.container ? " · bounded container" : ""}</text>
        <text class="node-label" x="14" y="49">${esc(String(node.label)).slice(0, 25)}</text>
        <text class="node-detail" x="14" y="72">${esc(String(summary || "")).slice(0, 31)}</text>
        <text class="node-bound" x="14" y="91">${esc(bounds || (node.fan_in > 1 ? `fan-in ${node.fan_in}` : node.fan_out > 1 ? `fan-out ${node.fan_out}` : node.drilldown?.name ? "drill down ↗" : "" )).slice(0, 36)}</text>
        ${count ? `<text class="node-error" x="194" y="22" text-anchor="end">${count}!</text>` : ""}
      </g>`;
    }).join("")}
  </svg></div>`;
}

function studioDocumentInspector() {
  const document = studioState.document || {};
  const common = `<div class="studio-inspector-head"><div><small>${esc(studioState.family)} policy</small><strong>${esc(document.slug || studioState.name)}</strong></div>${badge("tracked config", "ok")}</div>
    <form class="studio-inspector-form" id="studio-document-form">
      ${studioInput("slug / filename", "document.slug", document.slug, "text", 'pattern="[a-z][a-z0-9_-]*"', "/slug")}
      ${studioInput("title", "document.title", document.title, "text", "", "/title")}
      ${studioArea("description", "document.description", document.description || "", "reviewed tracked policy text; never provider credentials", "/description")}
      ${studioState.family === "workflow" ? studioInput("semantic version", "document.version", document.version || "1.0.0", "text", "", "/version") : ""}
    </form>`;
  if (studioState.family === "program") return common + studioProgramInspector();
  if (studioState.family === "organization") return common + studioOrganizationOverview();
  return common + `<p class="studio-help">Select a node to inspect its exact role, artifacts, bounds, routes, and shared-compiler diagnostics.</p>`;
}

function studioProgramInspector() {
  const document = studioState.document;
  const scope = document.scope || {};
  const phases = scope.phases || {};
  const stories = scope.stories === "all" ? "" : (scope.stories?.include || []).join("\n");
  const workCaps = ["agent:dispatch", "check:execute", "workspace:write", "nudge:deliver", "notification:send", "certification:verdict"];
  const deliveryCaps = ["evidence:materialize", "integration:apply", "contract:generate", "certification:objective", "git:commit", "git:push", "roadmap:story-start", "roadmap:story-complete", "roadmap:phase-advance"];
  const stops = ["scope-complete", "checkpoint-required", "unresolved-dissent", "architect-veto", "blocked-frontier", "budget-exhausted", "grant-expired", "grant-revoked"];
  return `<form id="studio-program-form" class="studio-inspector-form studio-program-form">
    <fieldset><legend>roadmap scope</legend>${studioInput("project", "program.project", scope.project || "", "text", "", "/scope/project")}${studioInput("phase from", "program.phase_from", phases.from ?? "", "number", 'min="0"', "/scope/phases/from")}${studioInput("phase through", "program.phase_through", phases.through ?? "", "number", 'min="0"', "/scope/phases/through")}${studioArea("exact story ids", "program.stories", stories, "empty means every story inside the phase scope", "/scope/stories")}</fieldset>
    <fieldset><legend>organization and autonomy ceiling</legend>${studioInput("organization", "program.organization", document.organization || "", "text", "", "/organization")}${studioSelect("mode ceiling", "program.mode_ceiling", ["advisory", "checkpointed", "continuous"], document.mode_ceiling || "advisory", "/mode_ceiling")}</fieldset>
    <fieldset><legend>work / verdict capability requests</legend><div class="studio-checkgrid">${workCaps.map((cap) => `<label><input type="checkbox" data-studio-capability="${cap}"${(document.requested_capabilities || []).includes(cap) ? " checked" : ""}>${cap}</label>`).join("")}</div></fieldset>
    <fieldset><legend>delivery rail requests</legend><div class="studio-checkgrid">${deliveryCaps.map((cap) => `<label><input type="checkbox" data-studio-capability="${cap}"${(document.requested_capabilities || []).includes(cap) ? " checked" : ""}>${cap}</label>`).join("")}</div></fieldset>
    <fieldset><legend>finite budgets</legend><div class="studio-budget-grid">${Object.entries(document.budgets || {}).map(([key, value]) => `<label><span>${esc(key)}</span><input type="number" min="1" data-studio-budget="${esc(key)}" value="${esc(value)}"></label>`).join("")}</div></fieldset>
    <fieldset><legend>stop and escalation policy</legend><div class="studio-checkgrid">${stops.map((stop) => `<label><input type="checkbox" data-studio-stop="${stop}"${(document.stop_conditions || []).includes(stop) ? " checked" : ""}>${stop}</label>`).join("")}</div></fieldset>
    <details><summary>binding rules and phase gates</summary><div class="studio-rule-list">${(document.bindings || []).map((rule, index) => `<button type="button" data-studio-select="binding:${esc(rule.id)}"><strong>${esc(rule.id)}</strong><span>priority ${esc(rule.priority)} · ${esc(rule.workflow)} · ${esc(rule.team)}</span><small>${esc(JSON.stringify(rule.match))}</small></button>`).join("") || '<p class="hint">No story binding rule yet; author one in lossless JSON.</p>'}${(document.phase_gates || []).map((gate) => `<button type="button" data-studio-select="gate:${esc(gate.id)}"><strong>${esc(gate.id)}</strong><span>${esc(gate.role)} · ${esc(gate.rubric)}</span><small>${esc(gate.when)} → ${esc(gate.on_fail)}</small></button>`).join("")}</div></details>
  </form>`;
}

function studioAuthoring() {
  return studioState.family === "organization"
    ? studioState.model?.team_review || null
    : studioState.model?.authoring || null;
}

function studioPlanSection(id = studioState.planSection) {
  return (studioAuthoring()?.sections || []).find((section) => section.id === id);
}

function studioPlanFactList(facts = []) {
  if (!facts.length) return "";
  return `<dl class="studio-plan-facts">${facts.map((fact) => `<div><dt>${esc(fact.label)}</dt><dd>${esc(fact.value ?? "Not chosen")}</dd></div>`).join("")}</dl>`;
}

function studioPlanItemList(items = [], editable = false) {
  if (!items.length) return '<p class="studio-plan-empty">Nothing has been defined here yet.</p>';
  return `<div class="studio-plan-items">${items.map((item) => {
    const action = editable && item.pointer?.startsWith("/nodes/")
      ? `<button type="button" data-plan-edit-step="${esc(item.id || "")}">Edit this step</button>`
      : "";
    const outcomes = (item.outcomes || []).length
      ? `<ul class="studio-plan-outcomes">${item.outcomes.map((outcome) => `<li><strong>${esc(outcome.outcome)}</strong><span>${esc(outcome.meaning)}</span></li>`).join("")}</ul>`
      : "";
    return `<article class="${item.advanced ? "advanced" : ""}">
      <div><span>${esc(item.advanced ? "Detailed flow" : "Delivery decision")}</span><strong>${esc(item.label)}</strong></div>
      <p>${esc(item.summary || "")}</p>${item.detail ? `<small>${esc(item.detail)}</small>` : ""}${outcomes}${action}
    </article>`;
  }).join("")}</div>`;
}

function studioPlanCorrections(sectionId) {
  const corrections = (studioAuthoring()?.corrections || []).filter((item) => item.section_id === sectionId);
  if (!corrections.length) return "";
  return `<div class="studio-plan-corrections" role="status"><h3>What needs attention</h3>${corrections.map((item) => `<article>
    <strong>${esc(item.affected_behavior)}</strong><p>${esc(item.correction)}</p>
    <button type="button" data-plan-correction="${esc(item.section_id)}" data-plan-node="${esc(item.target?.node_id || "")}" data-plan-field="${esc(item.target?.field_id || "")}">Go to this decision</button>
  </article>`).join("")}</div>`;
}

function studioPlanExamples() {
  const examples = studioAuthoring()?.examples || [];
  if (!examples.length) return "";
  return `<details class="studio-plan-examples"><summary>Examples</summary><div>${examples.map((example) => `<article><strong>${esc(example.label)}</strong><p>${esc(example.summary)}</p></article>`).join("")}</div></details>`;
}

function studioProgramPlanEditor(section) {
  const document = studioState.document || {};
  const scope = document.scope || {};
  const phases = scope.phases || {};
  const stories = scope.stories === "all" ? "" : (scope.stories?.include || []).join("\n");
  const bindings = document.bindings || [];
  const gates = document.phase_gates || [];
  const stopLabels = {
    "scope-complete": "All work in scope is complete",
    "checkpoint-required": "A named decision is required",
    "unresolved-dissent": "Review disagreement remains unresolved",
    "architect-veto": "The plan owner stops the delivery",
    "blocked-frontier": "The next work is blocked",
    "budget-exhausted": "A finite limit is reached",
    "grant-expired": "Permission expires",
    "grant-revoked": "Permission is withdrawn",
  };
  if (section.id === "scope") {
    return `<form class="studio-plan-form">
      ${studioInput("Plan name", "document.slug", document.slug, "text", 'pattern="[a-z][a-z0-9_-]*"', "/slug")}
      ${studioInput("Plan title", "document.title", document.title, "text", "", "/title")}
      ${studioArea("What is this delivery for?", "document.description", document.description || "", "A short purpose visible during review.", "/description")}
      <div class="studio-plan-form-grid">
        ${studioInput("Roadmap project", "program.project", scope.project || "", "text", "", "/scope/project")}
        ${studioInput("First phase", "program.phase_from", phases.from ?? "", "number", 'min="0"', "/scope/phases/from")}
        ${studioInput("Last phase", "program.phase_through", phases.through ?? "", "number", 'min="0"', "/scope/phases/through")}
      </div>
      ${studioArea("Only these story IDs", "program.stories", stories, "Leave empty to include every story in the selected phases.", "/scope/stories")}
    </form>`;
  }
  if (section.id === "flow") {
    return `<div class="studio-plan-editor-list">
      ${bindings.map((binding, index) => {
        const match = binding.match || {};
        return `<fieldset class="studio-plan-route"><legend>Work route ${index + 1}</legend>
          <div class="studio-plan-form-grid">
            <label><span>Route name</span><input data-plan-binding="${index}" data-plan-binding-field="id" value="${esc(binding.id || "")}"></label>
            <label><span>Order</span><input type="number" min="1" data-plan-binding="${index}" data-plan-binding-field="priority" value="${esc(binding.priority ?? "")}"></label>
            <label><span>First phase</span><input type="number" min="0" data-plan-binding="${index}" data-plan-binding-field="phase_from" value="${esc(match.phase_from ?? "")}"></label>
            <label><span>Last phase</span><input type="number" min="0" data-plan-binding="${index}" data-plan-binding-field="phase_through" value="${esc(match.phase_through ?? "")}"></label>
            <label><span>Saved work flow</span><input data-plan-binding="${index}" data-plan-binding-field="workflow" value="${esc(binding.workflow || "")}"></label>
            <label><span>Team</span><input data-plan-binding="${index}" data-plan-binding-field="team" value="${esc(binding.team || "")}"></label>
          </div>
          <label><span>Review criteria</span><textarea data-plan-binding="${index}" data-plan-binding-field="rubrics">${esc((binding.rubrics || []).join("\n"))}</textarea><small>One saved review-criteria name per line.</small></label>
          <div class="studio-plan-route-actions"><a href="#/program-studio/workflow/${encodeURIComponent(binding.workflow || "")}">Open this work flow</a><button type="button" class="danger" data-plan-remove-binding="${index}">Remove route</button></div>
        </fieldset>`;
      }).join("") || '<p class="studio-plan-empty">Add a route to connect scoped work to a saved work flow.</p>'}
      <button type="button" data-plan-add-binding>+ Add a work route</button>
      <p class="studio-plan-note">Exact input mappings remain unchanged and editable under Technical details.</p>
    </div>`;
  }
  if (section.id === "decisions") {
    return `<div class="studio-plan-editor-list">
      ${gates.map((gate, index) => `<fieldset class="studio-plan-route"><legend>Phase decision ${index + 1}</legend>
        <div class="studio-plan-form-grid">
          <label><span>Decision name</span><input data-plan-gate="${index}" data-plan-gate-field="id" value="${esc(gate.id || "")}"></label>
          <label><span>Decision owner</span><input data-plan-gate="${index}" data-plan-gate-field="role" value="${esc(gate.role || "")}"></label>
          <label><span>Review criteria</span><input data-plan-gate="${index}" data-plan-gate-field="rubric" value="${esc(gate.rubric || "")}"></label>
          <label><span>If review does not pass</span><select data-plan-gate="${index}" data-plan-gate-field="on_fail">${["block", "checkpoint", "abort"].map((value) => `<option value="${value}"${gate.on_fail === value ? " selected" : ""}>${value === "block" ? "Stop with a blocker" : value === "checkpoint" ? "Ask for a decision" : "End this delivery"}</option>`).join("")}</select></label>
        </div>
        <button type="button" class="danger" data-plan-remove-gate="${index}">Remove decision</button>
      </fieldset>`).join("") || '<p class="studio-plan-empty">No phase completion decision is defined.</p>'}
      <button type="button" data-plan-add-gate>+ Add a phase decision</button>
    </div>`;
  }
  if (section.id === "stops") {
    return `<fieldset class="studio-plan-checks"><legend>Stop whenever…</legend>${Object.entries(stopLabels).map(([stop, label]) => `<label><input type="checkbox" data-studio-stop="${stop}"${(document.stop_conditions || []).includes(stop) ? " checked" : ""}><span>${esc(label)}</span></label>`).join("")}</fieldset>`;
  }
  if (section.id === "limits") {
    return `<div class="studio-plan-limit-grid">${Object.entries(document.budgets || {}).map(([key, value]) => `<label><span>${esc(key.replace(/^max_/, "Maximum ").replaceAll("_", " "))}</span><input type="number" min="1" data-studio-budget="${esc(key)}" value="${esc(value)}"></label>`).join("")}</div><p class="studio-plan-note">Every saved finite limit remains exact. Technical details exposes the complete field names and compiled envelope.</p>`;
  }
  return `${studioPlanItemList(section.items)}${section.id === "recovery" ? '<p class="studio-plan-note">Detailed repair prompts and exact failure conditions remain available under Technical details.</p>' : ""}`;
}

function studioWorkflowStepEditor() {
  const graphNode = studioGraphNode(studioState.selected);
  const raw = studioRawNode(graphNode);
  if (!raw) return '<p class="studio-plan-empty">Choose a work step to edit it.</p>';
  return `<fieldset class="studio-plan-step-editor"><legend>Edit ${esc(graphNode?.label || raw.id)}</legend>
    ${studioInput("Step name", "node.id", raw.id, "text", "", `${graphNode.pointer}/id`)}
    ${studioInput("Step title", "node.title", raw.title || "", "text", "", `${graphNode.pointer}/title`)}
    ${studioArea("What happens here?", raw.prompt !== undefined ? "node.prompt" : raw.task !== undefined ? "node.task" : "node.description", raw.prompt ?? raw.task ?? raw.description ?? "", "", `${graphNode.pointer}/${raw.prompt !== undefined ? "prompt" : raw.task !== undefined ? "task" : "description"}`)}
    ${studioArea("After these steps", "node.needs", (raw.needs || []).join("\n"), "One earlier step name per line.", `${graphNode.pointer}/needs`)}
    ${raw.role !== undefined ? studioInput(raw.type === "verdict" ? "Review owner" : "Work owner", "node.role", raw.role || "", "text", "", `${graphNode.pointer}/role`) : ""}
    ${raw.rubric !== undefined ? studioInput("Review criteria", "node.rubric", raw.rubric || "", "text", "", `${graphNode.pointer}/rubric`) : ""}
    ${raw.workflow !== undefined ? studioInput("Saved detailed work flow", "node.workflow", raw.workflow || "", "text", "", `${graphNode.pointer}/workflow`) : ""}
    ${raw.max_rounds !== undefined ? studioInput("Maximum rounds", "node.max_rounds", raw.max_rounds, "number", 'min="1"', `${graphNode.pointer}/max_rounds`) : ""}
    ${raw.quorum !== undefined ? studioInput("Required reviewer agreement", "node.quorum", raw.quorum, "number", 'min="1"', `${graphNode.pointer}/quorum`) : ""}
    ${raw.expires_seconds !== undefined ? studioInput("Decision expires after seconds", "node.expires_seconds", raw.expires_seconds, "number", 'min="1"', `${graphNode.pointer}/expires_seconds`) : ""}
    <div class="studio-inspector-actions"><button type="button" id="studio-duplicate-node">Duplicate step</button><button type="button" class="danger" id="studio-delete-node">Remove step</button></div>
    <p class="studio-plan-note">Exact outcome conditions, inputs, outputs, allowed actions, and advanced bounds are preserved under Technical details.</p>
  </fieldset>`;
}

function studioWorkflowPlanEditor(section) {
  const document = studioState.document || {};
  if (section.id === "scope") {
    const parameters = document.parameters || [];
    return `<form class="studio-plan-form">
      ${studioInput("Flow name", "document.slug", document.slug, "text", 'pattern="[a-z][a-z0-9_-]*"', "/slug")}
      ${studioInput("Flow title", "document.title", document.title, "text", "", "/title")}
      ${studioArea("What delivery outcome does this flow produce?", "document.description", document.description || "", "", "/description")}
      <div class="studio-plan-editor-list">${parameters.map((parameter, index) => `<fieldset class="studio-plan-input"><legend>Work input ${index + 1}</legend>
        <div class="studio-plan-form-grid">
          <label><span>Input name</span><input data-plan-input="${index}" data-plan-input-field="id" value="${esc(parameter.id || "")}"></label>
          <label><span>Value type</span><select data-plan-input="${index}" data-plan-input-field="type">${["string", "integer", "boolean", "string-list"].map((value) => `<option value="${value}"${parameter.type === value ? " selected" : ""}>${esc(value.replace("-", " "))}</option>`).join("")}</select></label>
          <label class="studio-plan-toggle"><input type="checkbox" data-plan-input="${index}" data-plan-input-field="required"${parameter.required ? " checked" : ""}><span>Required before work starts</span></label>
          <label><span>Default value</span><input data-plan-input="${index}" data-plan-input-field="default" value="${esc(document.defaults?.[parameter.id] ?? "")}"></label>
        </div><button type="button" class="danger" data-plan-remove-input="${index}">Remove input</button>
      </fieldset>`).join("") || '<p class="studio-plan-empty">This flow needs no named work input.</p>'}</div>
      <button type="button" data-plan-add-input>+ Add a work input</button>
    </form>`;
  }
  if (section.id === "flow") {
    const ordinaryTypes = ["agent", "check", "verdict", "checkpoint"];
    const advancedTypes = STUDIO_NODE_TYPES.filter((type) => !ordinaryTypes.includes(type));
    return `<div class="studio-plan-flow-editor">
      <div class="studio-plan-add" aria-label="Add a delivery step">${ordinaryTypes.map((type) => `<button type="button" data-studio-add="${type}">+ ${esc({ agent: "Do work", check: "Run a check", verdict: "Review an outcome", checkpoint: "Ask for a decision" }[type])}</button>`).join("")}</div>
      <details class="studio-plan-advanced"><summary>Advanced flow building blocks</summary><p>Use these only when the delivery needs nested work, bounded repetition, multi-perspective discussion, or exact delivery actions.</p><div>${advancedTypes.map((type) => `<button type="button" data-studio-add="${type}">+ ${esc(type.replaceAll("_", " "))}</button>`).join("")}</div></details>
      ${studioPlanItemList(section.items, true)}
      ${studioWorkflowStepEditor()}
    </div>`;
  }
  return `${studioPlanItemList(section.items, true)}${section.id === "limits" ? studioPlanFactList(section.facts) : ""}`;
}

const TEAM_DUTY_LABELS = {
  implementer: "Implementation",
  verifier: "Independent review",
  "meta-verifier": "Review audit",
  "master-architect": "Architecture review",
  researcher: "Research",
  reviewer: "Review",
  repairer: "Repair",
  critic: "Critical perspective",
  judge: "Contested decision",
};

function studioOrganizationRoles() {
  return (studioState.document?.teams || []).flatMap((team, teamIndex) => (
    (team.roles || []).map((role, roleIndex) => ({
      team, teamIndex, role, roleIndex,
      model: (studioAuthoring()?.responsibilities || []).find((item) => item.id === role.id),
    }))
  ));
}

function studioTeamRoleLabel(role) {
  return TEAM_DUTY_LABELS[role?.duty] || String(role?.id || "Responsibility").replaceAll("-", " ");
}

function studioTeamRoleOptions(selected = "", includeBlank = false) {
  const values = studioOrganizationRoles();
  return `${includeBlank ? '<option value="">No separate responsibility</option>' : ""}${values.map(({ role }) => `<option value="${esc(role.id)}"${role.id === selected ? " selected" : ""}>${esc(studioTeamRoleLabel(role))}</option>`).join("")}`;
}

function studioTeamResponsibilitiesEditor() {
  const document = studioState.document || {};
  const pools = document.pools || [];
  const roles = studioOrganizationRoles();
  return `<div class="studio-team-editor" data-team-section="responsibilities">
    <form class="studio-plan-form studio-team-intro">
      ${studioInput("Team design name", "document.slug", document.slug, "text", 'pattern="[a-z][a-z0-9_-]*"', "/slug")}
      ${studioInput("Team design title", "document.title", document.title, "text", "", "/title")}
      ${studioArea("What is this team responsible for?", "document.description", document.description || "", "A short purpose visible during review.", "/description")}
    </form>
    <div class="studio-team-card-grid">${roles.map(({ team, teamIndex, role, roleIndex, model }) => {
      const pointer = `/teams/${teamIndex}/roles/${roleIndex}`;
      const primary = (model?.primary_candidates || []).map((item) => item.label);
      const backups = (model?.backup_candidates || []).map((item) => item.label);
      return `<fieldset class="studio-team-card"><legend>${esc(model?.label || studioTeamRoleLabel(role))}</legend>
        <div class="studio-team-card-head"><div><span>${esc(team.id)}</span><strong>${esc(model?.responsibility || "Performs the saved bounded responsibility.")}</strong></div>${badge(role.required ? "required" : "optional", role.required ? "ok" : "")}</div>
        <div class="studio-plan-form-grid">
          <label><span>Responsibility name</span><input id="${esc(studioFieldId(`${pointer}/id`))}" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="id" value="${esc(role.id || "")}"></label>
          <label><span>Kind of work</span><select id="${esc(studioFieldId(`${pointer}/duty`))}" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="duty">${Object.entries(TEAM_DUTY_LABELS).map(([value, label]) => `<option value="${esc(value)}"${role.duty === value ? " selected" : ""}>${esc(label)}</option>`).join("")}</select></label>
          <label><span>First-choice candidate group</span><select id="${esc(studioFieldId(`${pointer}/pool`))}" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="pool">${pools.map((pool) => `<option value="${esc(pool.id)}"${pool.id === role.pool ? " selected" : ""}>${esc(String(pool.id).replaceAll("-", " "))}</option>`).join("")}</select></label>
          <label><span>Number of places</span><input id="${esc(studioFieldId(`${pointer}/cardinality`))}" type="number" min="1" max="16" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="cardinality" value="${esc(role.cardinality ?? 1)}"></label>
          <label class="studio-plan-toggle"><input id="${esc(studioFieldId(`${pointer}/required`))}" type="checkbox" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="required"${role.required ? " checked" : ""}><span>This responsibility must be filled</span></label>
        </div>
        <dl class="studio-team-coverage"><div><dt>First in line</dt><dd>${esc(primary.join(", ") || "No compatible candidate")}</dd></div><div><dt>Backups</dt><dd>${esc(backups.join(", ") || "No backup candidate")}</dd></div></dl>
        <p>${esc(model?.when || "")}</p><small>${esc(model?.outcomes || "")}</small>
      </fieldset>`;
    }).join("") || '<p class="studio-plan-empty">Add implementation and independent-review responsibilities under Technical details.</p>'}</div>
    <p class="studio-plan-note">Candidate profiles, exact permissions, packet limits, schemas, and stable IDs remain visible and losslessly editable under Technical details.</p>
  </div>`;
}

function studioTeamIndependenceEditor() {
  const authoring = studioAuthoring() || {};
  const entries = studioOrganizationRoles();
  const constraints = authoring.quality_constraints || [];
  return `<div class="studio-team-editor" data-team-section="independence">
    <div class="studio-quality-constraints">${constraints.map((item) => `<article class="${item.status === "needs-attention" ? "issue" : "ready"}"><div><strong>${esc((item.labels || []).join(" ↔ "))}</strong>${badge(item.status === "runtime-proven" ? "proven in this assignment" : item.status === "policy-ready" ? "compatible candidates exist" : "must be checked at assignment", item.status === "needs-attention" ? "issue" : "ok")}</div><p>${esc(item.summary)}</p><small>${esc(item.runtime_claim)}</small>${item.status === "needs-attention" ? `<em>${esc(item.correction)}</em>` : ""}</article>`).join("") || '<p class="studio-plan-empty">No independent-review relationship has been declared.</p>'}</div>
    <div class="studio-plan-editor-list">${entries.map(({ team, teamIndex, role, roleIndex, model }) => {
      const peers = (team.roles || []).filter((item) => item !== role);
      const pointer = `/teams/${teamIndex}/roles/${roleIndex}`;
      return `<fieldset class="studio-team-rule"><legend>${esc(model?.label || studioTeamRoleLabel(role))}</legend>
        <p>${esc(model?.responsibility || "")}</p>
        <label><span>Work-area access</span><select id="${esc(studioFieldId(`${pointer}/workspace`))}" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="workspace"><option value="read-only"${role.workspace === "read-only" ? " selected" : ""}>Read only</option><option value="isolated-worktree"${role.workspace === "isolated-worktree" ? " selected" : ""}>Separate writable work area</option></select></label>
        <div class="studio-team-rule-grid"><fieldset><legend>Must be separate from</legend>${peers.map((peer) => `<label><input type="checkbox" data-team-role-link="${roleIndex}" data-team-team="${teamIndex}" data-team-role-link-field="independent_from" data-team-role-target="${esc(peer.id)}"${(role.independent_from || []).includes(peer.id) ? " checked" : ""}><span>${esc(studioTeamRoleLabel(peer))}</span></label>`).join("") || "<small>No other responsibility in this team.</small>"}</fieldset>
        <fieldset><legend>May review this work</legend>${peers.map((peer) => `<label><input type="checkbox" data-team-role-link="${roleIndex}" data-team-team="${teamIndex}" data-team-role-link-field="may_judge" data-team-role-target="${esc(peer.id)}"${(role.may_judge || []).includes(peer.id) ? " checked" : ""}><span>${esc(studioTeamRoleLabel(peer))}</span></label>`).join("") || "<small>No other responsibility in this team.</small>"}</fieldset></div>
      </fieldset>`;
    }).join("")}</div>
    <aside class="studio-team-honesty"><strong>Compatible policy is not a runtime proof</strong><p>A saved design can prove that different candidates, profiles, and work areas are available. Only a later assignment can prove separate execution identities and work sessions. Provider or model names never prove independence by themselves.</p></aside>
  </div>`;
}

function studioTeamDecisionsEditor() {
  const authoring = studioAuthoring() || {};
  const document = studioState.document || {};
  const roles = studioOrganizationRoles();
  const panels = roles.filter(({ role }) => Number(role.cardinality || 0) > 1);
  const groups = authoring.review_groups || [];
  return `<div class="studio-team-editor" data-team-section="decisions">
    ${panels.length ? `<section class="studio-team-panel"><h3>Review panels</h3>${panels.map(({ role, model }) => `<article><strong>${esc(model?.label || studioTeamRoleLabel(role))}</strong><p>${esc(role.cardinality)} separate places contribute to this responsibility. The saved agreement and decision rules still determine the outcome.</p></article>`).join("")}</section>` : ""}
    <div class="studio-plan-editor-list">${(document.councils || []).map((council, index) => {
      const model = groups.find((item) => item.id === council.id) || {};
      const decision = council.decision || {};
      return `<fieldset class="studio-team-council"><legend>Contested-decision group ${index + 1}</legend>
        <div class="studio-team-card-head"><div><span>Runs only when a saved work flow calls it</span><strong>${esc(model.description || "Declared perspectives discuss one matter before one governed outcome.")}</strong></div>${badge(`${council.quorum || 0} required`)}</div>
        <div class="studio-plan-form-grid">
          <label><span>Group name</span><input id="${esc(studioFieldId(`/councils/${index}/id`))}" data-team-council="${index}" data-team-council-field="id" value="${esc(council.id || "")}"></label>
          <label><span>Required reviewer agreement</span><input id="${esc(studioFieldId(`/councils/${index}/quorum`))}" type="number" min="1" data-team-council="${index}" data-team-council-field="quorum" value="${esc(council.quorum ?? 1)}"></label>
          <label><span>Decision owner</span><select id="${esc(studioFieldId(`/councils/${index}/judge`))}" data-team-council="${index}" data-team-council-field="judge">${studioTeamRoleOptions(council.judge, true)}</select></label>
          <label><span>How agreement is decided</span><select id="${esc(studioFieldId(`/councils/${index}/decision/method`))}" data-team-council="${index}" data-team-council-field="decision.method">${[["majority", "More than half agree"], ["weighted", "Saved perspective weights agree"], ["unanimous", "Every reviewer agrees"], ["judge", "Decision owner chooses"]].map(([value, label]) => `<option value="${value}"${decision.method === value ? " selected" : ""}>${label}</option>`).join("")}</select></label>
          <label class="studio-plan-toggle"><input id="${esc(studioFieldId(`/councils/${index}/distinct_principals`))}" type="checkbox" data-team-council="${index}" data-team-council-field="distinct_principals"${council.distinct_principals ? " checked" : ""}><span>Require different execution identities</span></label>
        </div>
        <fieldset class="studio-team-members"><legend>Participating responsibilities</legend>${roles.map(({ role }) => `<label><input type="checkbox" data-team-council-member="${index}" data-team-role-target="${esc(role.id)}"${(council.members || []).includes(role.id) ? " checked" : ""}><span>${esc(studioTeamRoleLabel(role))}</span></label>`).join("")}</fieldset>
        <p>${esc(model.decision_summary || "")} ${esc(model.decision_owner_summary || "")}</p>
        <details class="studio-plan-advanced"><summary>Objections, dissent, and bounded discussion</summary><p>${esc(model.dissent || "An objection remains visible and follows the saved route.")}</p><p>${esc(model.veto_summary || "")}</p><label><span>Responsibilities with a separate objection right</span><textarea data-team-council="${index}" data-team-council-field="decision.veto_roles">${esc((decision.veto_roles || []).join("\n"))}</textarea><small>One responsibility name per line.</small></label><p class="studio-plan-note">Speaker weights, thresholds, round bounds, artifact bounds, output bounds, token bounds, and time bounds remain exact under Technical details.</p></details>
      </fieldset>`;
    }).join("") || '<section class="studio-plan-empty"><strong>No contested-decision group is defined.</strong><p>Ordinary independent review remains decisive. Add an advanced group in Technical details only when multiple perspectives, a named decision owner, or preserved dissent are required.</p></section>'}</div>
  </div>`;
}

function studioTeamEscalationEditor() {
  const authoring = studioAuthoring() || {};
  return `<div class="studio-team-editor" data-team-section="escalation">
    <div class="studio-plan-editor-list">${studioOrganizationRoles().map(({ team, teamIndex, role, roleIndex, model }) => {
      const replacement = role.replacement || {};
      const route = (authoring.escalation_routes || []).find((item) => item.id === role.id);
      const pointer = `/teams/${teamIndex}/roles/${roleIndex}`;
      return `<fieldset class="studio-team-rule"><legend>${esc(model?.label || studioTeamRoleLabel(role))}</legend>
        <p>${esc(route?.summary || "Choose a finite replacement and handoff rule.")}</p>
        <div class="studio-plan-form-grid">
          <label><span>Maximum replacements</span><input id="${esc(studioFieldId(`${pointer}/replacement/max_replacements`))}" type="number" min="0" max="20" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="replacement.max_replacements" value="${esc(replacement.max_replacements ?? 0)}"></label>
          <label><span>When replacements are exhausted</span><select id="${esc(studioFieldId(`${pointer}/replacement/on_exhausted`))}" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="replacement.on_exhausted">${[["block", "Keep the work blocked"], ["escalate", "Ask the separately authorized delivery owner"], ["checkpoint", "Wait for a named person"], ["abort", "End this delivery"]].map(([value, label]) => `<option value="${value}"${replacement.on_exhausted === value ? " selected" : ""}>${label}</option>`).join("")}</select></label>
          <label><span>Backup candidate groups</span><textarea id="${esc(studioFieldId(`${pointer}/replacement/fallback_pools`))}" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="replacement.fallback_pools">${esc((replacement.fallback_pools || []).join("\n"))}</textarea><small>One saved group per line.</small></label>
          <label class="studio-plan-toggle"><input id="${esc(studioFieldId(`${pointer}/replacement/preserve_history`))}" type="checkbox" data-team-role="${roleIndex}" data-team-team="${teamIndex}" data-team-role-field="replacement.preserve_history"${replacement.preserve_history ? " checked" : ""}><span>Keep earlier work, review, and disagreement history</span></label>
        </div>
        <fieldset class="studio-team-members"><legend>May ask these responsibilities for bounded help</legend>${(team.roles || []).filter((item) => item !== role).map((peer) => `<label><input type="checkbox" data-team-role-link="${roleIndex}" data-team-team="${teamIndex}" data-team-role-link-field="may_request" data-team-role-target="${esc(peer.id)}"${(role.may_request || []).includes(peer.id) ? " checked" : ""}><span>${esc(studioTeamRoleLabel(peer))}</span></label>`).join("") || "<small>No other responsibility in this team.</small>"}</fieldset>
      </fieldset>`;
    }).join("")}</div>
    <aside class="studio-team-honesty"><strong>Escalation does not provide permission</strong><p>A delivery-owner escalation leaves this team and waits for separately authorized handling. The team design does not name, create, or impersonate that person.</p></aside>
  </div>`;
}

function studioTeamAuditEditor() {
  const authoring = studioAuthoring() || {};
  const document = studioState.document || {};
  const auditRoles = (authoring.responsibilities || []).filter((item) => ["meta-verifier", "master-architect"].includes(item.technical_details?.duty));
  const metaRoles = studioOrganizationRoles().filter(({ role }) => role.duty === "meta-verifier");
  return `<div class="studio-team-editor" data-team-section="audit">
    <div class="studio-team-audit-roles">${auditRoles.map((item) => `<article><div><strong>${esc(item.name)}</strong>${badge(item.technical_details?.duty === "master-architect" ? "architecture review · declared plan boundary only" : "review of review")}</div><p>${esc(item.responsibility)}</p><small>${esc(item.when)} ${esc(item.outcomes)}</small></article>`).join("") || '<p class="studio-plan-empty">No review auditor or architecture reviewer is enabled by this team design.</p>'}</div>
    <div class="studio-plan-editor-list">${(document.councils || []).map((council, index) => {
      const model = (authoring.review_groups || []).find((item) => item.id === council.id) || {};
      const audit = council.audit || {};
      return `<fieldset class="studio-team-rule"><legend>${esc(model.label || council.id)} review audit</legend>
        <p>${esc(model.audit?.summary || "No separate review audit runs.")}</p>
        <div class="studio-plan-form-grid">
          <label><span>Audit coverage</span><select id="${esc(studioFieldId(`/councils/${index}/audit/mode`))}" data-team-council="${index}" data-team-council-field="audit.mode"><option value="none"${audit.mode === "none" ? " selected" : ""}>No separate audit</option><option value="sample"${audit.mode === "sample" ? " selected" : ""}>Check a sample</option><option value="full"${audit.mode === "full" ? " selected" : ""}>Check every participant result</option></select></label>
          <label><span>Review auditor</span><select id="${esc(studioFieldId(`/councils/${index}/meta_verifier`))}" data-team-council="${index}" data-team-council-field="meta_verifier"><option value="">No review auditor</option>${metaRoles.map(({ role }) => `<option value="${esc(role.id)}"${council.meta_verifier === role.id ? " selected" : ""}>${esc(studioTeamRoleLabel(role))}</option>`).join("")}</select></label>
          <label><span>Results checked</span><input id="${esc(studioFieldId(`/councils/${index}/audit/sample_size`))}" type="number" min="0" data-team-council="${index}" data-team-council-field="audit.sample_size" value="${esc(audit.sample_size ?? 0)}"></label>
          <label><span>If the audit overturns a result</span><select data-team-council="${index}" data-team-council-field="audit.on_overturn">${["repair", "escalate", "block", "checkpoint", "abort"].map((value) => `<option value="${value}"${audit.on_overturn === value ? " selected" : ""}>${esc({ repair: "Request repair", escalate: "Escalate outside the team", block: "Keep work blocked", checkpoint: "Wait for a named person", abort: "End this delivery" }[value])}</option>`).join("")}</select></label>
        </div>
        <p class="studio-plan-note">Architecture review is activated only by a separately declared story or phase gate; defining an architecture responsibility here does not run it.</p>
      </fieldset>`;
    }).join("")}</div>
  </div>`;
}

function studioTeamReviewEditor(section) {
  if (section.id === "responsibilities") return studioTeamResponsibilitiesEditor();
  if (section.id === "independence") return studioTeamIndependenceEditor();
  if (section.id === "decisions") return studioTeamDecisionsEditor();
  if (section.id === "escalation") return studioTeamEscalationEditor();
  return studioTeamAuditEditor();
}

const STUDIO_PLAIN_SECTION_COPY = {
  scope: { label: "The delivery", question: "What will be delivered?", guidance: "Name the roadmap work and the boundary this delivery may cover." },
  flow: { label: "The team and work", question: "Who will do the work?", guidance: "Choose the team, work owners, inputs, and route from ready work to completion." },
  quality: { label: "Independent review", question: "Who will review the work independently?", guidance: "Choose what reviewers check and keep review separate from the work it judges." },
  decisions: { label: "Decision points", question: "When should a person decide?", guidance: "Name the closed choices that can pause, redirect, or stop work." },
  recovery: { label: "Repair path", question: "What happens when work does not pass?", guidance: "Make repair, help, and blocked-work routes visible before delivery." },
  stops: { label: "Stop conditions", question: "When must delivery stop?", guidance: "State completion and safety stops explicitly." },
  limits: { label: "Finite limits", question: "How much time, spending, and work may this delivery use?", guidance: "Keep time, attempts, work, and cost finite and reviewable." },
};

function studioPlainSection(section) {
  if (studioState.family === "organization") return section;
  return { ...section, ...(STUDIO_PLAIN_SECTION_COPY[section?.id] || {}) };
}

function studioReviewCriteriaHtml() {
  const references = studioState.model?.review_criteria || [];
  if (!references.length) return `<section class="studio-review-criteria empty"><header><span>Independent review</span><h3>No saved review criteria are referenced yet</h3></header><p>Choose readable review criteria for each work route that needs an independent judgment.</p></section>`;
  return `<section class="studio-review-criteria" aria-labelledby="studio-review-criteria-title"><header><span>Independent review</span><h3 id="studio-review-criteria-title">What reviewers will check</h3><p>These criteria are read only here. Their source stays in repository files.</p></header><div class="studio-review-criteria-list">${references.map((reference) => {
    if (reference.status !== "available") return `<article class="missing"><div><strong>${esc(reference.reference)}</strong>${badge("reference missing", "issue")}</div><p>${esc(reference.message)}</p><small>${esc(reference.next_step)}</small><details><summary>Technical details</summary><code>${esc(reference.path)}</code></details></article>`;
    return `<article class="available"><div><strong>${esc(reference.title)}</strong>${badge(`${reference.criteria?.length || 0} check${reference.criteria?.length === 1 ? "" : "s"}`, "ok")}</div>${reference.description ? `<p>${esc(reference.description)}</p>` : ""}<ol>${(reference.criteria || []).map((criterion) => `<li><strong>${esc(criterion.question)}</strong><dl><div><dt>Checked by</dt><dd>${esc(criterion.checked_by)}</dd></div><div><dt>Evidence</dt><dd>${esc(criterion.required_evidence?.join(", ") || "No separate evidence kind")}</dd></div><div><dt>Citations</dt><dd>${esc(criterion.minimum_citations || "None required")}</dd></div><div><dt>Must pass</dt><dd>${criterion.required_to_pass ? "Yes" : "Contributes to the full review"}</dd></div></dl></li>`).join("") || "<li>No individual review question was provided.</li>"}</ol><details><summary>Technical details</summary><code>${esc(reference.path)}</code><dl><div><dt>kind</dt><dd><code>${esc(reference.technical_details?.kind || "unknown")}</code></dd></div><div><dt>schema_version</dt><dd><code>${esc(reference.technical_details?.schema_version ?? "unknown")}</code></dd></div><div><dt>version</dt><dd><code>${esc(reference.technical_details?.version || "unknown")}</code></dd></div></dl></details></article>`;
  }).join("")}</div></section>`;
}

function studioTechnicalDisclosure(section) {
  const technical = studioState.technicalMode === "config"
    ? studioJsonView()
    : `<div class="studio-embedded-graph"><p>The exact graph keeps every saved step and route. Exact field editors remain available in the dedicated Technical details tab.</p>${studioGraphHtml()}</div>`;
  return `<details class="studio-form-technical"${studioState.technicalExpanded ? " open" : ""}><summary>Technical details</summary><div class="studio-form-technical-body"><p>The exact graph and lossless configuration edit this same draft. Closing these details returns to <strong>${esc(section.question)}</strong> without discarding edits.</p><div class="studio-technical-tabs" role="tablist" aria-label="Technical editor mode"><button type="button" id="studio-technical-tab-graph" role="tab" aria-controls="studio-technical-panel" aria-selected="${studioState.technicalMode === "graph"}" tabindex="${studioState.technicalMode === "graph" ? "0" : "-1"}" data-studio-technical="graph" class="${studioState.technicalMode === "graph" ? "active" : ""}">Exact graph</button><button type="button" id="studio-technical-tab-config" role="tab" aria-controls="studio-technical-panel" aria-selected="${studioState.technicalMode === "config"}" tabindex="${studioState.technicalMode === "config" ? "0" : "-1"}" data-studio-technical="config" class="${studioState.technicalMode === "config" ? "active" : ""}">Raw JSON</button></div><div id="studio-technical-panel" role="tabpanel" aria-labelledby="studio-technical-tab-${esc(studioState.technicalMode)}">${technical}</div><button type="button" data-studio-return-plain>Return to ${esc(section.label)}</button></div></details>`;
}

function studioPlanReview() {
  const authoring = studioAuthoring();
  const review = authoring?.review_sections || [];
  const team = studioState.family === "organization";
  return `<aside class="studio-plan-review" aria-label="${team ? "Readable team and review summary" : "Readable plan summary"}"><div><span>Review before save</span><strong>${esc(authoring?.status === "ready-to-review" ? "Ready to review" : "Needs attention")}</strong>${badge(authoring?.status === "ready-to-review" ? "nothing starts" : `${authoring?.corrections?.length || 0} corrections`, authoring?.status === "ready-to-review" ? "ok" : "issue")}</div>
    <dl>${review.map((item) => `<div><dt>${esc(studioPlainSection(item).label)}</dt><dd>${esc(item.answer)}</dd></div>`).join("")}</dl>
    ${team ? `<p>${esc(authoring?.runtime_independence?.claim || "")}</p>` : ""}
    <p>Drafting, checking, and leaving make no change. Saving still requires a separate review of the exact file change and starts no work.</p>
    <button type="button" id="studio-review-save"${authoring?.status === "ready-to-review" ? "" : " disabled"}>Review this save</button>
  </aside>`;
}

function studioPlanView() {
  const authoring = studioAuthoring();
  if (!authoring) return stateHtml("Checking the delivery decisions…");
  if (!authoring.applicable) return stateHtml("This delivery design has no ordinary authoring view.");
  const section = studioPlanSection() || authoring.sections[0];
  if (section) studioState.planSection = section.id;
  const plainSection = studioPlainSection(section);
  const editor = studioState.family === "program"
    ? studioProgramPlanEditor(section)
    : studioState.family === "workflow"
      ? studioWorkflowPlanEditor(section)
      : studioTeamReviewEditor(section);
  const team = studioState.family === "organization";
  return `<div class="studio-plan" data-plan-status="${esc(authoring.status)}">
    <header><div><span>${team ? "Team and review" : "Delivery decisions"}</span><h2>${team ? "Make ownership, independence, and decisions understandable" : "Build the plan in the order people review it"}</h2><p>${esc(authoring.summary)}</p></div>${badge(authoring.status === "ready-to-review" ? "ready to review" : "needs attention", authoring.status === "ready-to-review" ? "ok" : "issue")}</header>
    <div class="studio-plan-shell">
      <nav class="studio-plan-sections" aria-label="${team ? "Team and review sections" : "Delivery plan sections"}">${authoring.sections.map((item) => { const plainItem = studioPlainSection(item); return `<button type="button" data-plan-section="${esc(item.id)}" class="${item.id === section.id ? "active" : ""}" aria-current="${item.id === section.id ? "step" : "false"}"><span>${item.step}</span><strong>${esc(plainItem.label)}</strong>${item.correction_count ? `<small>${item.correction_count} to fix</small>` : "<small>ready</small>"}</button>`; }).join("")}</nav>
      <main class="studio-plan-section" id="studio-plan-section" tabindex="-1"><header><span>Step ${section.step} of ${authoring.sections.length}</span><h2>${esc(plainSection.question)}</h2><p>${esc(plainSection.guidance)}</p><strong>${esc(section.answer)}</strong></header>
        ${studioPlanCorrections(section.id)}${editor}${section.id !== "limits" ? studioPlanFactList(section.facts) : ""}${section.id === "quality" ? studioReviewCriteriaHtml() : ""}${studioPlanExamples()}${studioTechnicalDisclosure(plainSection)}
      </main>
      ${studioPlanReview()}
    </div>
  </div>`;
}

function studioTechnicalView() {
  const team = studioState.family === "organization";
  const section = studioPlainSection(studioPlanSection());
  return `<div class="studio-technical-view"><header><div><span class="orch-eyebrow">Technical details</span><h2>${team ? "Exact responsibilities, provenance, and configuration" : "Exact graph, fields, and configuration"}</h2><p>${team ? "Inspect stable role IDs, candidate profiles, provider and model resolution, auth and principal fingerprints, work areas, sessions, packet bounds, decision rules, and the lossless source." : "Use this view for hierarchical flows, bounded loops, discussion cells, exact conditions, raw import/export, and source-level diagnostics."}</p></div>${badge("same source document", "ok")}</header>
    <button type="button" class="studio-technical-return" data-studio-return-plain>Return to ${esc(section?.label || (team ? "team and review" : "plain plan"))}</button>
    <div class="studio-technical-tabs" role="tablist" aria-label="Technical editor mode"><button type="button" id="studio-technical-tab-graph" role="tab" aria-controls="studio-technical-panel" aria-selected="${studioState.technicalMode === "graph"}" tabindex="${studioState.technicalMode === "graph" ? "0" : "-1"}" data-studio-technical="graph" class="${studioState.technicalMode === "graph" ? "active" : ""}">Graph and fields</button><button type="button" id="studio-technical-tab-config" role="tab" aria-controls="studio-technical-panel" aria-selected="${studioState.technicalMode === "config"}" tabindex="${studioState.technicalMode === "config" ? "0" : "-1"}" data-studio-technical="config" class="${studioState.technicalMode === "config" ? "active" : ""}">Lossless configuration</button></div>
    <div id="studio-technical-panel" role="tabpanel" aria-labelledby="studio-technical-tab-${esc(studioState.technicalMode)}">${studioState.technicalMode === "config" ? studioJsonView() : studioDesignView()}</div>
  </div>`;
}

function studioExecutionContractHtml(contract, compact = false) {
  if (!contract) return '<p class="hint">No organization execution contract is reachable from this policy.</p>';
  const ports = contract.ports || [];
  const fallbacks = contract.fallbacks || [];
  const councils = contract.councils || [];
  const diversity = contract.diversity || {};
  return `<div class="studio-execution-contract${compact ? " compact" : ""}">
    <section><h3>portable execution ports / local resolution</h3>${ports.map((port) => { const local = port.local_resolution || {}; const constraints = port.constraints || {}; return `<article><div><strong>${esc(port.agent)}</strong>${badge(local.configured ? (local.available ? "available" : "unavailable") : "unconfigured", local.available ? "ok" : "warn")}</div><code>${esc(port.selector?.profile)}</code><span>${esc((constraints.duties || []).join(", "))} · ${esc(local.harness || "unresolved")} / ${esc(local.provider || "—")} / ${esc(local.model || local.model_family || "—")}</span><small>auth <code>${esc(local.auth_domain_fingerprint || "—")}</code> · principal <code>${esc(local.principal_fingerprint || "—")}</code></small><small>work area <code>${esc(constraints.workspace_domain || "—")}</code> · session binding not assigned before runtime</small></article>`; }).join("") || '<p class="hint">This policy family declares no logical execution profile.</p>'}${contract.local_resolution_issue ? `<p class="guard">${esc(contract.local_resolution_issue)}</p>` : ""}</section>
    <section><h3>fallback and replacement policy</h3>${fallbacks.map((item) => `<article><div><strong>${esc(item.team)} / ${esc(item.role)}</strong>${badge(`${esc(item.max_replacements)} replacement${Number(item.max_replacements) === 1 ? "" : "s"}`)}</div><span>${esc(item.primary_pool)} → ${esc((item.fallback_pools || []).join(", ") || "no fallback pool")}</span><small>${esc((item.reasons || []).join(", ") || "no eligible reason")} · exhausted → ${esc(item.on_exhausted)}</small></article>`).join("") || '<p class="hint">No replacement policy is reachable.</p>'}</section>
    <section><h3>council perspectives / authority / obligations</h3>${councils.map((item) => `<article><div><strong>${esc(item.id)}</strong>${badge(item.decision_authority === "judge" ? "agent judge" : `rule · ${item.decision_authority}`, item.decision_authority === "judge" ? "warn" : "ok")}</div><span>${(item.perspectives || []).map((perspective) => `${esc(perspective.role)}:${esc(perspective.perspective)}`).join(" · ")}</span><small>quorum ${esc(item.quorum)} · principals ${esc(item.principal_diversity)} · meta ${esc(item.meta_verifier || "none")} · veto ${esc((item.veto_roles || []).join(", ") || "none")}</small><small>obligations required · ${esc((item.obligation_policy?.allowed_kinds || []).join(", "))} · blocking stops progress</small></article>`).join("") || '<p class="hint">No council policy is reachable.</p>'}</section>
    <section><h3>diversity contract and observed roster</h3><dl class="studio-diversity"><div><dt>separation edges</dt><dd>${esc((diversity.independence || []).length)}</dd></div><div><dt>providers observed</dt><dd>${esc(diversity.resolved_provider_count || 0)}</dd></div><div><dt>model families observed</dt><dd>${esc(diversity.resolved_model_family_count || 0)}</dd></div><div><dt>principals observed</dt><dd>${esc(diversity.resolved_principal_count || 0)}</dd></div><div><dt>auth domains observed</dt><dd>${esc(diversity.resolved_auth_domain_count || 0)}</dd></div></dl><p class="hint">Provider/model counts are local observations. Exact logical profiles, principal separation, fallbacks, and council authority remain tracked policy; a later grant freezes resolved fingerprints.</p></section>
  </div>`;
}

function studioOrganizationOverview() {
  const document = studioState.document;
  return `<div class="studio-org-overview"><h3>team / verifier topology</h3>${(document.teams || []).map((team) => `<section><strong>${esc(team.id)}</strong><div>${(team.roles || []).map((role) => `${badge(`${role.duty} · ${role.cardinality}`, role.duty === "verifier" || role.duty === "meta-verifier" ? "ok" : "")} `).join("")}</div><small>${(team.roles || []).filter((role) => (role.independent_from || []).length).map((role) => `${role.id} independent from ${role.independent_from.join(", ")}`).join(" · ") || "No separation edge declared."}</small></section>`).join("") || '<p class="hint">No team policy yet; author agents, pools, teams, and councils in JSON.</p>'}<h3>councils / meta-verification</h3>${(document.councils || []).map((council) => `<section><strong>${esc(council.id)}</strong><span>${esc((council.members || []).join(" + "))}</span><small>judge ${esc(council.judge)} · quorum ${esc(council.quorum)} · meta ${esc(council.meta_verifier || "none")} · ${esc(council.decision?.method || "declared default")}</small></section>`).join("") || '<p class="hint">No council declared.</p>'}<h3>execution contract</h3>${studioExecutionContractHtml(studioState.model?.authority?.execution_contract, true)}<p class="studio-help">Use the lossless JSON view to author logical profiles, packet constraints, independence, fallbacks, council rules, and obligation authority. Local availability is inspection-only and never saved into portable policy.</p></div>`;
}

function studioNodeInspector(node) {
  if (!node) return studioDocumentInspector();
  const raw = studioRawNode(node);
  const diagnostics = (studioState.model.validation?.diagnostics || []).filter((item) => item.target?.node_id === node.id);
  const drilldown = node.drilldown?.name ? `<a class="studio-drilldown" href="#/program-studio/workflow/${encodeURIComponent(node.drilldown.name)}">open nested workflow ${esc(node.drilldown.name)} ↗</a>` : "";
  return `<div class="studio-inspector-head"><div><small>${esc(node.type)} · ${esc(node.lane)}</small><strong>${esc(node.label)}</strong></div>${badge(node.container ? "finite container" : "graph node", node.container ? "warn" : "")}</div>
    ${diagnostics.length ? `<div class="studio-node-errors">${diagnostics.map((item) => `<button type="button" data-studio-diagnostic="${esc(item.pointer)}" data-node-id="${esc(item.target?.node_id || "")}" data-field-id="${esc(item.target?.field_id || "")}"><code>${esc(item.pointer)}</code>${esc(item.message)}</button>`).join("")}</div>` : ""}
    ${raw ? `<form id="studio-node-form" class="studio-inspector-form">
      ${studioInput("node id", "node.id", raw.id, "text", "", `${node.pointer}/id`)}
      ${studioInput("title", "node.title", raw.title || "", "text", "", `${node.pointer}/title`)}
      ${studioArea("description", "node.description", raw.description || "", "", `${node.pointer}/description`)}
      ${raw.role !== undefined ? studioInput("assigned role", "node.role", raw.role || "", "text", "", `${node.pointer}/role`) : ""}
      ${raw.workflow !== undefined ? studioInput("nested workflow", "node.workflow", raw.workflow || "", "text", "", `${node.pointer}/workflow`) : ""}
      ${raw.max_rounds !== undefined ? studioInput("maximum rounds", "node.max_rounds", raw.max_rounds, "number", 'min="1"', `${node.pointer}/max_rounds`) : ""}
      ${raw.quorum !== undefined ? studioInput("quorum", "node.quorum", raw.quorum, "number", 'min="1"', `${node.pointer}/quorum`) : ""}
      ${raw.capability_ceiling !== undefined ? studioArea("capability ceiling", "node.capability_ceiling", (raw.capability_ceiling || []).join("\n"), "one exact capability per line", `${node.pointer}/capability_ceiling`) : ""}
      ${raw.participants !== undefined ? studioArea("debate speakers", "node.participants", (raw.participants || []).join("\n"), "judge remains a separate role", `${node.pointer}/participants`) : ""}
    </form><div class="studio-inspector-actions"><button type="button" id="studio-duplicate-node">duplicate node</button><button type="button" class="danger" id="studio-delete-node">delete node</button></div>` : ""}
    ${drilldown}
    <details open><summary>exact governed fields</summary><pre>${esc(JSON.stringify(raw || node.summary || node, null, 2))}</pre></details>`;
}

function studioDesignView() {
  const node = studioGraphNode(studioState.selected);
  const palette = studioState.family === "workflow" ? `<div class="studio-palette" aria-label="hierarchical workflow node palette"><button type="button" data-studio-settings>workflow settings</button>${STUDIO_NODE_TYPES.map((type) => `<button type="button" data-studio-add="${type}">+ ${type.replace("_", " ")}</button>`).join("")}</div>` : `<div class="studio-palette"><button type="button" data-studio-settings>${esc(studioState.family)} settings</button><span>Graph positions are document-only layout; every contract field remains available in JSON.</span></div>`;
  return `<div class="studio-design">${palette}<div class="studio-workarea">${studioGraphHtml()}</div><aside class="studio-inspector" aria-label="${esc(studioState.family)} policy inspector">${node ? studioNodeInspector(node) : studioDocumentInspector()}</aside></div>`;
}

function studioScenarioSummary(scenario) {
  const simulation = studioState.model?.simulation || {};
  const graph = studioState.model?.graph || {};
  if (scenario === "candidate-assignment") {
    const selection = simulation.selection || {};
    return `<div class="studio-scenario-summary"><strong>${esc(selection.story || "No eligible story selected")}</strong><span>${esc(selection.reason || "The shared planner explains every scoped candidate.")}</span>${simulation.assignment ? `<small>${esc(simulation.assignment.implementer?.profile || "implementer")} → independent verifier ${esc(simulation.assignment.verifier?.profile || "unresolved")}</small>` : ""}</div>`;
  }
  const active = (graph.nodes || []).filter((node) => {
    if (scenario === "debate-active") return node.type === "debate" || node.type === "council";
    if (scenario === "verifier-failed") return ["verdict", "verifier", "meta-verifier"].includes(node.type);
    if (scenario === "budget-exhausted") return node.container || node.type === "scope";
    if (scenario === "phase-transition") return node.type === "architect-gate" || node.type === "master-architect";
    if (scenario === "nested") return ["subflow", "loop"].includes(node.type);
    return false;
  });
  return `<div class="studio-scenario-summary"><strong>${esc(scenario.replaceAll("-", " "))}</strong><span>${active.length ? `${active.length} delivery step${active.length === 1 ? "" : "s"} involved` : "This route is not present in the plan."}</span><small>Inspection example only—nothing starts and no permission is created.</small></div>`;
}

function studioSimulationDetails() {
  const simulation = studioState.model?.simulation;
  if (!simulation) return `<p class="hint">Resolve compiler diagnostics to obtain a pure scheduling simulation.</p>`;
  if (studioState.family === "program") return `<div class="studio-sim-grid"><section><h3>roadmap candidates</h3>${(simulation.candidates || []).map((candidate) => `<div class="studio-candidate"><code>${esc(candidate.story)}</code>${badge(candidate.reason, candidate.eligible ? "ok" : "")}<span>${esc(candidate.phase)}</span></div>`).join("") || '<p class="hint">No scoped candidates.</p>'}</section><section><h3>preassigned organization</h3><pre>${esc(JSON.stringify(simulation.assignment || simulation.issues || {}, null, 2))}</pre></section></div>`;
  if (studioState.family === "workflow") return `<div class="studio-sim-grid"><section><h3>finite scheduling waves</h3>${(simulation.waves || []).map((wave, index) => `<div class="studio-wave"><strong>wave ${esc(wave.wave ?? index + 1)}</strong><span>${esc((wave.scheduled || wave).join?.(", ") || JSON.stringify(wave))}</span></div>`).join("")}</section><section><h3>worst-case envelope</h3>${Object.entries(simulation.envelopes?.worst_case || {}).map(([key, value]) => `<div class="kv"><div class="k">${esc(key)}</div><div class="v">${esc(value)}</div></div>`).join("")}</section><section><h3>loops / debate routes</h3><pre>${esc(JSON.stringify({ loops: simulation.loops || [], debates: simulation.debates || [], routes: simulation.routes || [] }, null, 2))}</pre></section></div>`;
  return `<div class="studio-sim-grid"><section><h3>team concurrency and separation</h3><pre>${esc(JSON.stringify(simulation.teams || [], null, 2))}</pre></section><section><h3>councils, quorum, meta-audit</h3><pre>${esc(JSON.stringify(simulation.councils || [], null, 2))}</pre></section></div>`;
}

function studioSimulateView() {
  const scenarios = studioState.model?.simulation_scenarios || [];
  const current = scenarios.find((item) => item.id === studioState.scenario) || scenarios.find((item) => item.available) || scenarios[0];
  if (current) studioState.scenario = current.id;
  return `<div class="studio-simulation" data-scenario="${esc(studioState.scenario)}"><header><div><span class="orch-eyebrow">Try the delivery flow</span><h2>See how work could move before saving or requesting permission</h2><p>This is an inspection-only example. It starts no work and changes no plan.</p></div>${badge("starts nothing", "ok")}</header><div class="studio-scenario-tabs" role="tablist" aria-label="Delivery examples">${scenarios.map((scenario) => `<button type="button" id="studio-scenario-tab-${esc(scenario.id)}" role="tab" aria-controls="studio-scenario-panel" data-studio-scenario="${esc(scenario.id)}" aria-selected="${scenario.id === studioState.scenario}" tabindex="${scenario.id === studioState.scenario ? "0" : "-1"}"${scenario.available ? "" : " disabled"}>${esc(scenario.label)}</button>`).join("")}</div><div id="studio-scenario-panel" role="tabpanel" aria-labelledby="studio-scenario-tab-${esc(studioState.scenario)}">${studioScenarioSummary(studioState.scenario)}${studioSimulationDetails()}</div></div>`;
}

function studioValidateView() {
  const model = studioState.model;
  if (!model) return stateHtml("Checking this delivery plan…");
  const validation = model.validation || { valid: false, diagnostics: [] };
  const diagnostics = validation.diagnostics || [];
  const corrections = studioAuthoring()?.corrections || [];
  const hashes = model.round_trip?.hashes_before || {};
  const team = studioState.family === "organization";
  const subject = team ? "team and review design" : "plan";
  return `<div class="studio-validation ${validation.valid ? "valid" : "invalid"}"><header><div><span class="orch-eyebrow">${team ? "Check responsibilities and independence" : "Check the delivery decisions"}</span><h2>${validation.valid ? `This ${subject} is ready to review` : `${corrections.length} ${team ? "team or review rule" : "delivery decision"}${corrections.length === 1 ? "" : "s"} need attention`}</h2><p>${validation.valid ? (team ? "Responsibilities, independent review, decisions, escalation, and audit rules agree." : "Scope, flow, review, decisions, recovery, stops, and limits agree.") : `Fix the affected ${team ? "responsibility or quality constraint" : "decision"} below; the saved ${subject} remains unchanged.`}</p></div>${badge(validation.valid ? "ready" : "needs attention", validation.valid ? "ok" : "issue")}</header>
    ${corrections.length ? `<ol class="studio-decision-diagnostics">${corrections.map((item) => `<li><div><span>${esc(item.decision)}</span><strong>${esc(item.affected_behavior)}</strong><p>${esc(item.correction)}</p></div><button type="button" data-plan-correction="${esc(item.section_id)}" data-plan-node="${esc(item.target?.node_id || "")}" data-plan-field="${esc(item.target?.field_id || "")}">Fix this decision</button></li>`).join("")}</ol>` : '<p class="studio-green">The exact source is valid, and reviewing this result starts no work.</p>'}
    <details class="studio-validation-technical"><summary>Technical details</summary>
      <div class="studio-hashes"><div><span>semantic</span><code>${esc(hashes.semantic || "unavailable until valid")}</code></div><div><span>document</span><code>${esc(hashes.document || "unavailable until valid")}</code></div><div><span>layout</span><code>${esc(hashes.layout)}</code></div></div>
      <section class="studio-roundtrip"><strong>graph ⇄ config</strong>${badge(model.round_trip?.lossless ? "lossless" : "mismatch", model.round_trip?.lossless ? "ok" : "issue")} ${badge(model.round_trip?.semantic_hash_preserved ? "semantic hash preserved" : "semantic unavailable", model.round_trip?.semantic_hash_preserved ? "ok" : "")} ${badge(model.round_trip?.layout_hash_preserved ? "layout hash preserved" : "layout mismatch", model.round_trip?.layout_hash_preserved ? "ok" : "issue")}</section>
      ${diagnostics.length ? `<ol class="studio-diagnostics">${diagnostics.map((item) => `<li><button type="button" data-studio-diagnostic="${esc(item.pointer)}" data-node-id="${esc(item.target?.node_id || "")}" data-field-id="${esc(item.target?.field_id || "")}"><code>${esc(item.pointer)}</code><strong>${esc(item.code)}</strong><span>${esc(item.message)}</span><small>${esc(item.remediation)}</small></button></li>`).join("")}</ol>` : '<p class="studio-green">The exact configuration passed the shared checker.</p>'}
    </details>
  </div>`;
}

function studioJsonView() {
  const value = studioState.jsonDraft || JSON.stringify(studioState.document, null, 2);
  return `<div class="studio-json"><header><div><span class="orch-eyebrow">lossless configuration</span><h2>Every contract field, portable and reviewable</h2></div>${badge("same compiler", "ok")}</header>${studioState.jsonPointer ? `<div class="studio-json-target"><span>compiler target</span><code>${esc(studioState.jsonPointer)}</code></div>` : ""}<div class="studio-json-actions"><button type="button" id="studio-json-apply">apply JSON to graph</button><label class="filebtn">import JSON<input type="file" id="studio-json-import" accept="application/json,.json"></label></div><div id="studio-json-error" class="guard" role="alert" hidden></div><label><span>${esc(studioState.family)} JSON</span><textarea id="studio-json-text" spellcheck="false" aria-describedby="studio-json-error">${esc(value)}</textarea></label></div>`;
}

function studioAuthorityView() {
  const authority = studioState.model?.authority;
  if (!authority) return stateHtml("Waiting for authority explanation…");
  return `<div class="studio-authority"><header><div><span class="orch-eyebrow">policy request ≠ runtime authority</span><h2>What a later exact grant could—and could not—authorize</h2></div>${badge("creates no grant", "ok")}</header><div class="studio-mode-grid">${authority.modes.map((mode) => `<article class="${mode.within_ceiling ? "within" : "denied"}"><span>${esc(mode.id)}</span><strong>${esc(mode.label)}</strong><p>${esc(mode.meaning)}</p><small>${mode.within_ceiling ? "within authored ceiling" : "above authored ceiling"} · ${mode.dispatch ? "bounded dispatch possible only after grant" : "no dispatch"}</small></article>`).join("")}</div><div class="studio-capability-groups">${authority.groups.map((group) => `<section><h3>${esc(group.label)}</h3>${group.capabilities.map((capability) => `<div class="studio-capability ${capability.requested ? "requested" : "absent"}"><code>${esc(capability.id)}</code>${badge(capability.requested ? "requested in policy" : "not requested", capability.requested ? "warn" : "")}</div>`).join("")}</section>`).join("")}</div>${studioExecutionContractHtml(authority.execution_contract)}<div class="studio-authority-foot"><section><h3>finite budgets</h3><pre>${esc(JSON.stringify(authority.budgets || {}, null, 2))}</pre></section><section><h3>declared stops</h3><p>${(authority.stop_conditions || []).map((stop) => badge(stop)).join(" ") || "None on this policy family."}</p></section></div><p class="studio-no-grant">This is an inspection-only preview. Save writes tracked policy only; neither view nor Save grants a capability, starts work, creates a run, or advances the roadmap. Resolved profiles expose fingerprints, never credentials or arbitrary commands.</p></div>`;
}

function studioBody() {
  if (studioState.view === "simulate") return studioSimulateView();
  if (studioState.view === "validate") return studioValidateView();
  if (studioState.view === "technical") return studioTechnicalView();
  if (studioState.view === "authority") return studioAuthorityView();
  return studioPlanView();
}

function renderProgramStudio() {
  const focus = captureAppFocus();
  const family = studioFamilyModel();
  const items = family?.items || [];
  const document = studioState.document || family?.draft || {};
  const validation = studioState.model?.validation;
  const empty = studioState.inventory?.empty;
  const familyLabels = {
    program: "Delivery plans",
    workflow: "Work flows",
    organization: "Teams and review",
  };
  const objectLabels = {
    program: "delivery plan",
    workflow: "work flow",
    organization: "team and review design",
  };
  const viewLabels = {
    plan: studioState.family === "organization" ? "Team & review" : "Plan",
    simulate: "Try the flow",
    validate: "Check",
    technical: "Technical details",
    authority: "Permission details",
  };
  const objectLabel = objectLabels[studioState.family] || "delivery design";
  app.innerHTML = `${destinationNav("plan", "#/program-studio")}<div class="program-studio" data-family="${esc(studioState.family)}" data-policy="${esc(studioState.name)}">
    ${studioState.setupContext ? `<section class="studio-setup-context"><div><span>Delivery scope from setup</span><strong>${esc(studioState.setupContext.project || "project not chosen")} · phase ${esc(studioState.setupContext.phase || "review needed")}</strong><p>This is an unsaved delivery-plan draft. Editing and checking it start nothing; Save draft still requires its own exact preview and confirmation.</p></div><div><a href="#/program-studio">Back to delivery choices</a><a href="#/">Leave for now</a></div></section>` : ""}
    ${empty ? `<section class="studio-empty-neutral"><div><span class="orch-eyebrow">Optional delivery design</span><h2>Nothing has been saved here yet</h2><p>Ordinary roadmap work is ready. Drafting a ${esc(objectLabel)} is optional and starts no work.</p></div><a href="#/">Return to current work</a></section>` : ""}
    <header class="studio-toolbar"><div><span class="orch-eyebrow">${esc(familyLabels[studioState.family])}</span><h1>${esc(document.title || document.slug || "Delivery plan")}</h1><p>Draft, check, and review before saving. Nothing here starts work or provides permission.</p><details><summary>Technical details</summary><code>pm/${esc(family?.plural || `${studioState.family}s`)}/${esc(document.slug || studioState.name)}.json</code></details></div><div class="studio-policy-actions"><label>Design area<select id="studio-family-select">${STUDIO_FAMILIES.map((id) => `<option value="${id}"${id === studioState.family ? " selected" : ""}>${esc(familyLabels[id])}</option>`).join("")}</select></label><label>Saved ${esc(objectLabel)}<select id="studio-policy-select"><option value="">New unsaved ${esc(objectLabel)}</option>${items.map((item) => `<option value="${esc(item.name)}"${item.name === studioState.name && studioState.exists ? " selected" : ""}>${esc(item.slug || item.name)}${item.valid ? "" : " · needs attention"}</option>`).join("")}</select></label><button type="button" id="studio-new">New</button><button type="button" id="studio-duplicate">Duplicate</button><button type="button" id="studio-preview-save">${studioState.setupContext && studioState.family === "program" ? "Review draft save" : `Review ${esc(objectLabel)} save`}</button><button type="button" id="studio-preview-delete" class="danger"${studioState.exists ? "" : " disabled"}>Review removal</button></div></header>
    <div class="studio-tabs" role="tablist" aria-label="${studioState.family === "organization" ? "Team and review authoring views" : "Delivery-plan authoring views"}">${STUDIO_VIEWS.map((id) => `<button type="button" id="studio-tab-${id}" role="tab" aria-controls="studio-view" aria-selected="${studioState.view === id}" tabindex="${studioState.view === id ? "0" : "-1"}" data-studio-view="${id}" class="${studioState.view === id ? "active" : ""}">${esc(viewLabels[id])}${id === "validate" && validation && !validation.valid ? ` (${validation.diagnostics.length})` : ""}</button>`).join("")}</div>
    ${studioState.error ? `<div class="studio-error" role="alert">${esc(studioState.error)}</div>` : ""}<div id="studio-save-panel"></div><div id="studio-view" role="tabpanel" aria-labelledby="studio-tab-${esc(studioState.view)}">${studioBody()}</div>
  </div>`;
  wireProgramStudio();
  wireTablist(".studio-tabs");
  wireTablist(".studio-technical-tabs");
  wireTablist(".studio-scenario-tabs");
  wireArrowGroup(".studio-plan-sections", "[data-plan-section]");
  finishDynamicRender(focus);
}

function queueStudioModel() {
  clearTimeout(studioState.validationTimer);
  studioState.validationTimer = setTimeout(() => refreshStudioModel(), SNAPSHOT_MODE ? 0 : 220);
}

async function refreshStudioModel() {
  if (!studioState.document) return;
  studioState.error = "";
  const request = { family: studioState.family, action: "save", name: studioState.document.slug || studioState.name, document: studioState.document };
  const { status, body } = await postJson("/api/program-studio/preview", request);
  if (status >= 400 || body.ok === false || !body.data?.studio) {
    studioState.error = (body.issues && body.issues[0]) || `compiler preview failed (${status})`;
  } else {
    studioState.compilePreview = body.data;
    studioState.model = body.data.studio;
    studioState.document = clone(body.data.studio.raw);
  }
  renderProgramStudio();
}

function setStudioField(key, value) {
  const document = studioState.document;
  if (key === "document.slug") { document.slug = value.trim(); if (!studioState.exists) studioState.name = document.slug; }
  else if (key === "document.title") document.title = value;
  else if (key === "document.description") setOptional(document, "description", value.trim());
  else if (key === "document.version") document.version = value.trim();
  else if (key.startsWith("program.")) {
    document.scope ||= {};
    document.scope.phases ||= { from: 1, through: 1 };
    if (key === "program.project") document.scope.project = value.trim();
    if (key === "program.phase_from") document.scope.phases.from = maybeNumber(value);
    if (key === "program.phase_through") document.scope.phases.through = maybeNumber(value);
    if (key === "program.stories") document.scope.stories = splitLines(value).length ? { include: splitLines(value) } : "all";
    if (key === "program.organization") document.organization = value.trim();
    if (key === "program.mode_ceiling") document.mode_ceiling = value;
  } else if (key.startsWith("node.")) {
    const graphNode = studioGraphNode(studioState.selected);
    const node = studioRawNode(graphNode);
    if (!node) return;
    const field = key.slice(5);
    if (field === "id") {
      const old = node.id; const next = value.trim(); node.id = next;
      (document.nodes || []).forEach((candidate) => {
        candidate.needs = (candidate.needs || []).map((need) => need === old ? next : need);
        if (Array.isArray(candidate.producers)) {
          candidate.producers = candidate.producers.map((producer) => producer === old ? next : producer);
        }
        for (const referenceKey of ["facts", "verdicts"]) {
          if (Array.isArray(candidate[referenceKey])) {
            candidate[referenceKey] = candidate[referenceKey].map((reference) => (
              reference === old || reference.startsWith(`${old}.`)
                ? `${next}${reference.slice(old.length)}`
                : reference
            ));
          }
        }
        Object.values(candidate.routes || {}).forEach((route) => { if (route?.kind === "node" && route.target === old) route.target = next; });
        ["on_success", "on_failure", "on_exhausted", "on_consensus", "on_repair", "on_dissent", "on_quorum_lost"].forEach((routeKey) => { if (candidate[routeKey]?.kind === "node" && candidate[routeKey].target === old) candidate[routeKey].target = next; });
      });
      visitStudioObjects(document.nodes || [], (item) => {
        if (
          item.kind === "artifact"
          && typeof item.name === "string"
          && item.name.startsWith(`${old}.`)
        ) item.name = `${next}${item.name.slice(old.length)}`;
      });
      ensureStudioLayout(); if (document.layout.nodes[old]) { document.layout.nodes[next] = document.layout.nodes[old]; delete document.layout.nodes[old]; }
      studioState.selected = next;
    } else if (["max_rounds", "quorum", "expires_seconds", "timeout_seconds", "max_attempts"].includes(field)) node[field] = maybeNumber(value);
    else if (["capability_ceiling", "participants", "needs"].includes(field)) node[field] = splitLines(value);
    else setOptional(node, field, value.trim());
  }
  studioState.jsonDraft = "";
  studioState.jsonPointer = "";
  queueStudioModel();
}

function nextStudioNodeId(type) {
  const base = type.replace("_", "-");
  const used = new Set((studioState.document.nodes || []).map((node) => node.id));
  let index = 1; while (used.has(`${base}-${index}`)) index += 1;
  return `${base}-${index}`;
}

function defaultStudioNode(type) {
  const id = nextStudioNodeId(type);
  const common = { id, type, needs: [], resource_groups: [], inputs: {}, outputs: [] };
  const action = { kind: "action", target: "block" };
  const complete = { kind: "terminal", target: "complete" };
  if (type === "agent") return { ...common, role: "implementer", task: "Perform the exact bounded role task.", workspace: "isolated-worktree", capability_ceiling: ["agent:dispatch", "workspace:write"], timeout_seconds: 900, max_attempts: 1, on_failure: action };
  if (type === "check") return { ...common, runner: { kind: "builtin", name: "file-exists", path: "README.md", output_bytes: 30000 }, expect: { exit_code: 0 }, timeout_seconds: 300, max_attempts: 1, on_failure: action };
  if (type === "collect") return { ...common, producers: [], on_failure: action };
  if (type === "bounded_run") return { ...common, score: "score", expected_terminal: "awaiting-certification", capability_ceiling: ["agent:dispatch", "check:execute", "workspace:write"], budgets: { max_agent_starts: 8, max_check_starts: 16, max_wall_seconds: 3600, max_artifact_bytes: 1000000 }, on_failure: action };
  if (type === "subflow") return { ...common, workflow: "workflow", version: "1.0.0", with: {}, capability_ceiling: ["agent:dispatch"], on_success: complete, on_failure: action };
  if (type === "loop") return { ...common, purpose: "repair", workflow: "workflow", version: "1.0.0", with: {}, capability_ceiling: ["agent:dispatch"], max_rounds: 2, until: { kind: "artifact-valid", source: "child.fact", operator: "green" }, carry: [], on_success: complete, on_exhausted: action };
  if (type === "debate") return { ...common, participants: ["proposer", "critic"], judge_role: "judge", max_rounds: 2, quorum: 2, artifact_max_bytes: 30000, artifact_max_tokens: 4000, round_timeout_seconds: 1800, tie_policy: "judge", dissent_policy: "preserve", on_consensus: complete, on_repair: action, on_dissent: { kind: "action", target: "checkpoint" }, on_quorum_lost: { kind: "action", target: "escalate" }, on_exhausted: { kind: "action", target: "escalate" } };
  if (type === "verdict") return { ...common, role: "verifier", rubric: "quality", subject: { kind: "literal", value: "subject" }, freshness_seconds: 3600, max_rationale_bytes: 30000, results: ["pass", "fail"], routes: { pass: complete, fail: action } };
  if (type === "gate") return { ...common, facts: ["check.fact"], verdicts: [], operator: "all", missing_policy: "block", dissent_policy: "preserve", routes: { pass: complete, fail: action, missing: action, dissent: { kind: "action", target: "checkpoint" } } };
  if (type === "checkpoint") return { ...common, prompt_id: id, prompt: "Review this declared decision port.", expires_seconds: 86400, options: [{ id: "approve", label: "Approve", route: complete }, { id: "block", label: "Block", route: action }] };
  if (type === "rail") return { ...common, action: "evidence-materialize", capability: "evidence:materialize", timeout_seconds: 300, on_failure: action };
  return common;
}

function addStudioNode(type) {
  const node = defaultStudioNode(type);
  studioState.document.nodes ||= [];
  studioState.document.nodes.push(node);
  ensureStudioLayout();
  const index = studioState.document.nodes.length - 1;
  studioState.document.layout.nodes[node.id] = { x: 80 + (index % 4) * 270, y: 90 + Math.floor(index / 4) * 160 };
  studioState.selected = node.id; studioState.jsonDraft = "";
  refreshStudioModel();
}

function removeStudioNode() {
  const graphNode = studioGraphNode(studioState.selected);
  const node = studioRawNode(graphNode); if (!node) return;
  studioState.document.nodes = studioState.document.nodes.filter((item) => item !== node);
  studioState.document.nodes.forEach((candidate) => { candidate.needs = (candidate.needs || []).filter((need) => need !== node.id); });
  ensureStudioLayout(); delete studioState.document.layout.nodes[node.id];
  studioState.selected = ""; studioState.jsonDraft = ""; refreshStudioModel();
}

function duplicateStudioNode() {
  const node = studioRawNode(studioGraphNode(studioState.selected)); if (!node) return;
  const copy = clone(node); copy.id = nextStudioNodeId(node.type);
  studioState.document.nodes.push(copy); ensureStudioLayout();
  const old = studioState.document.layout.nodes[node.id] || { x: 80, y: 80 };
  studioState.document.layout.nodes[copy.id] = { x: Number(old.x) + 35, y: Number(old.y) + 125 };
  studioState.selected = copy.id; studioState.jsonDraft = ""; refreshStudioModel();
}

function moveStudioNode(id, x, y) {
  const graphNode = studioGraphNode(id); if (!graphNode) return;
  ensureStudioLayout();
  const position = { x: Math.max(10, Math.round(x)), y: Math.max(10, Math.round(y)) };
  studioState.document.layout.nodes[graphNode.layout_key || id] = position;
  graphNode.position = position;
  studioState.jsonDraft = "";
}

function wireStudioCanvas() {
  const svg = document.getElementById("studio-canvas"); if (!svg) return;
  let drag = null;
  const point = (event) => { const p = svg.createSVGPoint(); p.x = event.clientX; p.y = event.clientY; return p.matrixTransform(svg.getScreenCTM().inverse()); };
  document.querySelectorAll("[data-studio-node]").forEach((group) => {
    group.addEventListener("click", () => { studioState.selected = group.dataset.studioNode; renderProgramStudio(); });
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); studioState.selected = group.dataset.studioNode; renderProgramStudio(); return; }
      if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
      event.preventDefault(); const node = studioGraphNode(group.dataset.studioNode); const step = event.shiftKey ? 20 : 5;
      const dx = event.key === "ArrowLeft" ? -step : event.key === "ArrowRight" ? step : 0;
      const dy = event.key === "ArrowUp" ? -step : event.key === "ArrowDown" ? step : 0;
      moveStudioNode(node.id, Number(node.position.x) + dx, Number(node.position.y) + dy); renderProgramStudio(); queueStudioModel();
    });
    group.addEventListener("pointerdown", (event) => { if (event.button !== 0) return; const node = studioGraphNode(group.dataset.studioNode); const p = point(event); drag = { group, node, dx: p.x - node.position.x, dy: p.y - node.position.y }; group.setPointerCapture(event.pointerId); });
    group.addEventListener("pointermove", (event) => { if (!drag || drag.group !== group) return; const p = point(event); moveStudioNode(drag.node.id, p.x - drag.dx, p.y - drag.dy); group.setAttribute("transform", `translate(${drag.node.position.x},${drag.node.position.y})`); });
    group.addEventListener("pointerup", () => { if (!drag) return; drag = null; queueStudioModel(); });
  });
}

function renderStudioSavePreview(preview, request) {
  const slot = document.getElementById("studio-save-panel"); if (!slot) return;
  const objectLabel = request.family === "program" ? "delivery plan" : request.family === "workflow" ? "work flow" : "team and review design";
  const applyLabel = request.action === "delete"
    ? `Remove this ${objectLabel}`
    : `Save this ${objectLabel}`;
  const actionSummary = request.action === "delete"
    ? `This would remove one saved ${objectLabel}.`
    : `This would write one reviewed ${objectLabel} file.`;
  slot.innerHTML = `<section class="studio-save-preview ${preview.applicable ? "" : "refused"}" role="dialog" aria-modal="false" aria-labelledby="studio-save-preview-title" tabindex="-1"><div class="studio-preview-head"><div><span>Review before ${request.action === "delete" ? "removal" : "save"}</span><strong id="studio-save-preview-title">${esc(actionSummary)}</strong></div>${badge(preview.applicable ? "ready for confirmation" : "needs attention", preview.applicable ? "ok" : "issue")}</div>
    <p>Reviewing this change writes nothing. Confirming it changes only the named file; it starts no work, changes no roadmap status, and provides no permission.</p>
    ${preview.no_op ? '<p class="hint">The saved file already matches this draft.</p>' : ""}
    <details class="studio-save-technical"><summary>Technical details</summary><code>${esc(preview.path)}</code><code>${esc(preview.fingerprint)}</code>${preview.diff ? `<pre class="diff">${diffHtml(preview.diff)}</pre>` : '<p class="hint">No byte change.</p>'}</details>
    <div class="studio-preview-actions">${preview.applicable ? `<button type="button" id="studio-confirm-apply">${esc(applyLabel)}</button>` : ""}<button type="button" id="studio-close-preview">Close review</button></div></section>`;
  const close = () => {
    slot.innerHTML = "";
    restoreReturnFocus("studio-save", "#studio-preview-save");
  };
  document.getElementById("studio-close-preview")?.addEventListener("click", close);
  document.getElementById("studio-confirm-apply")?.addEventListener("click", () => applyStudioAction(preview, request));
  enhanceSemantics(slot);
  wireDismissibleRegion(".studio-save-preview", close, "studio-save", "#studio-preview-save");
  focusRegion(".studio-save-preview");
}

async function previewStudioAction(action, trigger = document.activeElement) {
  rememberReturnFocus("studio-save", trigger);
  const request = { family: studioState.family, action, name: studioState.document.slug || studioState.name, ...(action === "save" ? { document: studioState.document } : {}) };
  const { status, body } = await postJson("/api/program-studio/preview", request);
  if (status >= 400 || body.ok === false) { studioState.error = (body.issues && body.issues[0]) || `preview failed (${status})`; renderProgramStudio(); return; }
  if (body.data.studio) { studioState.model = body.data.studio; studioState.compilePreview = body.data; }
  renderProgramStudio(); renderStudioSavePreview(body.data, request);
}

async function applyStudioAction(preview, request) {
  const button = document.getElementById("studio-confirm-apply"); if (button) { button.disabled = true; button.textContent = "applying exact policy…"; }
  const { status, body } = await postJson("/api/program-studio/apply", { ...request, fingerprint: preview.fingerprint });
  if (status === 409) { studioState.error = "This save review is no longer current. Nothing was written. Review the change again to get a fresh preview before saving."; renderProgramStudio(); return; }
  if (status >= 400 || body.ok === false) { studioState.error = (body.issues && body.issues[0]) || `apply failed (${status})`; renderProgramStudio(); return; }
  const family = studioState.family;
  if (request.action === "delete") { location.hash = `#/program-studio/${family}`; await viewProgramStudio(family); return; }
  studioState.exists = true; studioState.name = request.name;
  location.hash = `#/program-studio/${family}/${encodeURIComponent(request.name)}`;
  await viewProgramStudio(family, request.name);
}

function studioPlanChanged() {
  studioState.jsonDraft = "";
  studioState.jsonPointer = "";
  queueStudioModel();
}

function visitStudioObjects(value, visitor) {
  if (Array.isArray(value)) {
    value.forEach((item) => visitStudioObjects(item, visitor));
    return;
  }
  if (!value || typeof value !== "object") return;
  visitor(value);
  Object.values(value).forEach((item) => visitStudioObjects(item, visitor));
}

function updateProgramBinding(index, field, value) {
  const binding = studioState.document?.bindings?.[index];
  if (!binding) return;
  binding.match ||= {};
  if (field === "priority") binding.priority = maybeNumber(value);
  else if (field === "phase_from") binding.match.phase_from = maybeNumber(value);
  else if (field === "phase_through") binding.match.phase_through = maybeNumber(value);
  else if (field === "rubrics") binding.rubrics = splitLines(value);
  else if (field === "id") {
    const old = binding.id;
    const next = String(value).trim();
    binding.id = next;
    (studioState.document.nudges || []).forEach((nudge) => {
      if (nudge.binding === old) nudge.binding = next;
    });
  } else binding[field] = String(value).trim();
  studioPlanChanged();
}

function addProgramBinding() {
  const document = studioState.document;
  document.bindings ||= [];
  const used = new Set(document.bindings.map((item) => item.id));
  let index = document.bindings.length + 1;
  while (used.has(`work-route-${index}`)) index += 1;
  const phases = document.scope?.phases || { from: 1, through: 1 };
  const workflow = studioFamilyModel("workflow")?.items?.[0]?.name || "choose-work-flow";
  document.bindings.push({
    id: `work-route-${index}`,
    priority: index * 10,
    match: { phase_from: phases.from ?? 1, phase_through: phases.through ?? phases.from ?? 1 },
    workflow,
    with: {},
    team: "choose-team",
    rubrics: ["choose-review-criteria"],
  });
  studioPlanChanged();
}

function removeProgramBinding(index) {
  studioState.document.bindings?.splice(index, 1);
  studioPlanChanged();
}

function updateProgramGate(index, field, value) {
  const gate = studioState.document?.phase_gates?.[index];
  if (!gate) return;
  gate[field] = String(value).trim();
  studioPlanChanged();
}

function addProgramGate() {
  const document = studioState.document;
  document.phase_gates ||= [];
  const used = new Set(document.phase_gates.map((item) => item.id));
  let index = document.phase_gates.length + 1;
  while (used.has(`phase-review-${index}`)) index += 1;
  document.phase_gates.push({
    id: `phase-review-${index}`,
    when: "before-phase-complete",
    role: "choose-review-owner",
    rubric: "choose-review-criteria",
    on_fail: "block",
  });
  studioPlanChanged();
}

function removeProgramGate(index) {
  studioState.document.phase_gates?.splice(index, 1);
  studioPlanChanged();
}

function updateWorkflowInput(index, field, value, checked = false) {
  const document = studioState.document;
  const parameter = document?.parameters?.[index];
  if (!parameter) return;
  document.defaults ||= {};
  if (field === "required") parameter.required = checked;
  else if (field === "default") {
    if (value === "") delete document.defaults[parameter.id];
    else if (parameter.type === "integer") document.defaults[parameter.id] = maybeNumber(value);
    else if (parameter.type === "boolean") document.defaults[parameter.id] = ["true", "1", "yes"].includes(String(value).toLowerCase());
    else if (parameter.type === "string-list") document.defaults[parameter.id] = splitLines(value);
    else document.defaults[parameter.id] = value;
  } else if (field === "id") {
    const old = parameter.id;
    const next = String(value).trim();
    parameter.id = next;
    if (Object.prototype.hasOwnProperty.call(document.defaults, old)) {
      document.defaults[next] = document.defaults[old];
      delete document.defaults[old];
    }
    visitStudioObjects(document.nodes || [], (item) => {
      if (item.kind === "parameter" && item.name === old) item.name = next;
    });
  } else if (field === "type") {
    parameter.type = value;
  }
  studioPlanChanged();
}

function addWorkflowInput() {
  const document = studioState.document;
  document.parameters ||= [];
  const used = new Set(document.parameters.map((item) => item.id));
  let index = document.parameters.length + 1;
  while (used.has(`work-input-${index}`)) index += 1;
  document.parameters.push({
    id: `work-input-${index}`,
    type: "string",
    required: false,
    max_bytes: 1000,
  });
  studioPlanChanged();
}

function removeWorkflowInput(index) {
  const document = studioState.document;
  const parameter = document.parameters?.[index];
  if (parameter && document.defaults) delete document.defaults[parameter.id];
  document.parameters?.splice(index, 1);
  studioPlanChanged();
}

function studioTeamRoleAt(teamIndex, roleIndex) {
  return studioState.document?.teams?.[teamIndex]?.roles?.[roleIndex] || null;
}

function renameStudioTeamRole(teamIndex, roleIndex, nextValue) {
  const document = studioState.document;
  const role = studioTeamRoleAt(teamIndex, roleIndex);
  if (!document || !role) return;
  const old = role.id;
  const next = String(nextValue).trim();
  const collision = studioOrganizationRoles().some((item) => (
    (item.teamIndex !== teamIndex || item.roleIndex !== roleIndex)
    && item.role.id === next
  ));
  role.id = next;
  if (!next || next === old || collision) return;
  (document.teams || []).forEach((team) => (team.roles || []).forEach((item) => {
    ["may_request", "may_judge", "independent_from"].forEach((field) => {
      item[field] = (item[field] || []).map((value) => value === old ? next : value);
    });
  }));
  (document.councils || []).forEach((council) => {
    council.members = (council.members || []).map((value) => value === old ? next : value);
    if (council.judge === old) council.judge = next;
    if (council.meta_verifier === old) council.meta_verifier = next;
    if (council.decision) {
      council.decision.veto_roles = (council.decision.veto_roles || []).map((value) => value === old ? next : value);
      if (council.decision.weights && Object.prototype.hasOwnProperty.call(council.decision.weights, old)) {
        council.decision.weights[next] = council.decision.weights[old];
        delete council.decision.weights[old];
      }
    }
  });
  ensureStudioLayout();
  const teamId = document.teams?.[teamIndex]?.id;
  const oldKey = `${teamId}/${old}`;
  const nextKey = `${teamId}/${next}`;
  if (document.layout.nodes[oldKey]) {
    document.layout.nodes[nextKey] = document.layout.nodes[oldKey];
    delete document.layout.nodes[oldKey];
  }
}

function updateStudioTeamRole(teamIndex, roleIndex, field, value, checked = false) {
  const role = studioTeamRoleAt(teamIndex, roleIndex);
  if (!role) return;
  if (field === "id") renameStudioTeamRole(teamIndex, roleIndex, value);
  else if (field === "required") role.required = checked;
  else if (field === "cardinality") role.cardinality = maybeNumber(value);
  else if (field === "replacement.max_replacements") {
    role.replacement ||= {};
    role.replacement.max_replacements = maybeNumber(value);
    if (Number(role.replacement.max_replacements) > 0 && !(role.replacement.reasons || []).length) {
      role.replacement.reasons = ["unavailable", "lost", "failed", "refused", "conflicted"];
    }
  } else if (field.startsWith("replacement.")) {
    role.replacement ||= {};
    const key = field.slice("replacement.".length);
    if (key === "fallback_pools") role.replacement[key] = splitLines(value);
    else if (key === "preserve_history") role.replacement[key] = checked;
    else role.replacement[key] = String(value).trim();
  } else role[field] = String(value).trim();
  studioPlanChanged();
}

function updateStudioTeamRoleLink(teamIndex, roleIndex, field, target, checked) {
  const role = studioTeamRoleAt(teamIndex, roleIndex);
  if (!role) return;
  const current = new Set(role[field] || []);
  if (checked) current.add(target);
  else current.delete(target);
  const order = (studioState.document?.teams?.[teamIndex]?.roles || []).map((item) => item.id);
  role[field] = order.filter((id) => current.has(id));
  studioPlanChanged();
}

function studioCouncilVotingSlots(council) {
  const roleMap = new Map(studioOrganizationRoles().map(({ role }) => [role.id, role]));
  return (council.members || [])
    .filter((id) => id !== council.judge)
    .reduce((total, id) => total + Number(roleMap.get(id)?.cardinality || 0), 0);
}

function renameStudioCouncil(index, nextValue) {
  const document = studioState.document;
  const council = document?.councils?.[index];
  if (!document || !council) return;
  const old = council.id;
  const next = String(nextValue).trim();
  const collision = (document.councils || []).some((item, itemIndex) => (
    itemIndex !== index && item.id === next
  ));
  council.id = next;
  if (!next || next === old || collision) return;
  ensureStudioLayout();
  const oldKey = `council:${old}`;
  const nextKey = `council:${next}`;
  if (document.layout.nodes[oldKey]) {
    document.layout.nodes[nextKey] = document.layout.nodes[oldKey];
    delete document.layout.nodes[oldKey];
  }
}

function updateStudioCouncil(index, field, value, checked = false) {
  const council = studioState.document?.councils?.[index];
  if (!council) return;
  council.decision ||= {};
  council.audit ||= {};
  if (field === "quorum" || field === "audit.sample_size") {
    const [parent, child] = field.split(".");
    if (child) council[parent][child] = maybeNumber(value);
    else council[field] = maybeNumber(value);
  } else if (field === "distinct_principals") {
    council.distinct_principals = checked;
  } else if (field === "meta_verifier") {
    council.meta_verifier = String(value).trim() || null;
  } else if (field === "decision.veto_roles") {
    council.decision.veto_roles = splitLines(value);
  } else if (field === "decision.method") {
    council.decision.method = value;
    const votingSlots = Math.max(studioCouncilVotingSlots(council), 1);
    const totalWeight = (council.members || [])
      .filter((id) => id !== council.judge)
      .reduce((total, id) => {
        const role = studioOrganizationRoles().find((item) => item.role.id === id)?.role;
        return total + Number(role?.cardinality || 0) * Number(council.decision.weights?.[id] || 1);
      }, 0);
    council.decision.threshold = value === "unanimous"
      ? votingSlots
      : value === "weighted"
        ? Math.floor(totalWeight / 2) + 1
        : value === "majority"
          ? Math.floor(votingSlots / 2) + 1
          : 1;
  } else if (field === "audit.mode") {
    council.audit.mode = value;
    const memberSlots = (council.members || []).reduce((total, id) => {
      const role = studioOrganizationRoles().find((item) => item.role.id === id)?.role;
      return total + Number(role?.cardinality || 0);
    }, 0);
    council.audit.sample_size = value === "none" ? 0 : value === "full" ? memberSlots : 1;
  } else if (field === "id") {
    renameStudioCouncil(index, value);
  } else if (field.includes(".")) {
    const [parent, child] = field.split(".");
    council[parent][child] = String(value).trim();
  } else {
    council[field] = String(value).trim();
  }
  studioPlanChanged();
}

function updateStudioCouncilMember(index) {
  const council = studioState.document?.councils?.[index];
  if (!council) return;
  const selected = new Set(
    [...document.querySelectorAll(`[data-team-council-member="${index}"]:checked`)]
      .map((field) => field.dataset.teamRoleTarget)
  );
  council.members = studioOrganizationRoles()
    .map(({ role }) => role.id)
    .filter((id) => selected.has(id));
  if (council.decision?.weights) {
    Object.keys(council.decision.weights).forEach((id) => {
      if (!selected.has(id)) delete council.decision.weights[id];
    });
  }
  if (council.decision?.veto_roles) {
    council.decision.veto_roles = council.decision.veto_roles.filter((id) => selected.has(id));
  }
  studioPlanChanged();
}

function wireProgramStudio() {
  document.querySelectorAll("[data-studio-view]").forEach((button) => button.addEventListener("click", () => { studioState.view = button.dataset.studioView; renderProgramStudio(); }));
  document.querySelector(".studio-form-technical")?.addEventListener("toggle", (event) => { studioState.technicalExpanded = event.currentTarget.open; });
  document.querySelectorAll("[data-studio-technical]").forEach((button) => button.addEventListener("click", () => { studioState.technicalMode = button.dataset.studioTechnical; studioState.technicalExpanded = studioState.view === "plan"; renderProgramStudio(); }));
  document.querySelectorAll("[data-studio-return-plain]").forEach((button) => button.addEventListener("click", () => {
    studioState.view = "plan";
    studioState.technicalExpanded = false;
    renderProgramStudio();
    document.getElementById("studio-plan-section")?.focus();
  }));
  document.querySelectorAll("[data-plan-section]").forEach((button) => button.addEventListener("click", () => {
    studioState.planSection = button.dataset.planSection;
    studioState.selected = "";
    renderProgramStudio();
    document.getElementById("studio-plan-section")?.focus();
  }));
  document.getElementById("studio-review-save")?.addEventListener("click", () => previewStudioAction("save"));
  document.getElementById("studio-family-select")?.addEventListener("change", (event) => { location.hash = `#/program-studio/${event.target.value}`; });
  document.getElementById("studio-policy-select")?.addEventListener("change", (event) => { location.hash = event.target.value ? `#/program-studio/${studioState.family}/${encodeURIComponent(event.target.value)}` : `#/program-studio/${studioState.family}`; });
  document.getElementById("studio-new")?.addEventListener("click", () => {
    const family = studioFamilyModel(); const used = new Set((family.items || []).map((item) => item.name)); let slug = `new-${studioState.family}`; let index = 2; while (used.has(slug)) slug = `new-${studioState.family}-${index++}`;
    studioState.document = clone(family.draft); studioState.document.slug = slug; studioState.name = slug; studioState.exists = false; studioState.selected = ""; studioState.model = null; studioState.error = ""; refreshStudioModel();
  });
  document.getElementById("studio-duplicate")?.addEventListener("click", () => {
    const used = new Set((studioFamilyModel().items || []).map((item) => item.name)); let slug = `${studioState.document.slug}-copy`; let index = 2; while (used.has(slug)) slug = `${studioState.document.slug}-copy-${index++}`;
    studioState.document = clone(studioState.document); studioState.document.slug = slug; studioState.document.title = `${studioState.document.title} copy`; studioState.name = slug; studioState.exists = false; studioState.selected = ""; refreshStudioModel();
  });
  document.getElementById("studio-preview-save")?.addEventListener("click", () => previewStudioAction("save"));
  document.getElementById("studio-preview-delete")?.addEventListener("click", () => previewStudioAction("delete"));
  document.querySelectorAll("[data-studio-settings]").forEach((button) => button.addEventListener("click", () => { studioState.selected = ""; renderProgramStudio(); }));
  document.querySelectorAll("[data-studio-select]").forEach((button) => button.addEventListener("click", () => { studioState.selected = button.dataset.studioSelect; renderProgramStudio(); }));
  document.querySelectorAll("[data-studio-add]").forEach((button) => button.addEventListener("click", () => addStudioNode(button.dataset.studioAdd)));
  document.querySelectorAll("[data-studio-field]").forEach((field) => field.addEventListener("change", () => setStudioField(field.dataset.studioField, field.value)));
  document.querySelectorAll("[data-plan-binding-field]").forEach((field) => field.addEventListener("change", () => updateProgramBinding(Number(field.dataset.planBinding), field.dataset.planBindingField, field.value)));
  document.querySelector("[data-plan-add-binding]")?.addEventListener("click", addProgramBinding);
  document.querySelectorAll("[data-plan-remove-binding]").forEach((button) => button.addEventListener("click", () => removeProgramBinding(Number(button.dataset.planRemoveBinding))));
  document.querySelectorAll("[data-plan-gate-field]").forEach((field) => field.addEventListener("change", () => updateProgramGate(Number(field.dataset.planGate), field.dataset.planGateField, field.value)));
  document.querySelector("[data-plan-add-gate]")?.addEventListener("click", addProgramGate);
  document.querySelectorAll("[data-plan-remove-gate]").forEach((button) => button.addEventListener("click", () => removeProgramGate(Number(button.dataset.planRemoveGate))));
  document.querySelectorAll("[data-plan-input-field]").forEach((field) => field.addEventListener("change", () => updateWorkflowInput(Number(field.dataset.planInput), field.dataset.planInputField, field.value, field.checked)));
  document.querySelector("[data-plan-add-input]")?.addEventListener("click", addWorkflowInput);
  document.querySelectorAll("[data-plan-remove-input]").forEach((button) => button.addEventListener("click", () => removeWorkflowInput(Number(button.dataset.planRemoveInput))));
  document.querySelectorAll("[data-team-role-field]").forEach((field) => field.addEventListener("change", () => updateStudioTeamRole(Number(field.dataset.teamTeam), Number(field.dataset.teamRole), field.dataset.teamRoleField, field.value, field.checked)));
  document.querySelectorAll("[data-team-role-link]").forEach((field) => field.addEventListener("change", () => updateStudioTeamRoleLink(Number(field.dataset.teamTeam), Number(field.dataset.teamRoleLink), field.dataset.teamRoleLinkField, field.dataset.teamRoleTarget, field.checked)));
  document.querySelectorAll("[data-team-council-field]").forEach((field) => field.addEventListener("change", () => updateStudioCouncil(Number(field.dataset.teamCouncil), field.dataset.teamCouncilField, field.value, field.checked)));
  document.querySelectorAll("[data-team-council-member]").forEach((field) => field.addEventListener("change", () => updateStudioCouncilMember(Number(field.dataset.teamCouncilMember))));
  document.querySelectorAll("[data-plan-edit-step]").forEach((button) => button.addEventListener("click", () => {
    studioState.selected = button.dataset.planEditStep;
    studioState.planSection = "flow";
    renderProgramStudio();
    document.querySelector(".studio-plan-step-editor input")?.focus();
  }));
  document.querySelectorAll("[data-plan-correction]").forEach((button) => button.addEventListener("click", () => {
    studioState.planSection = button.dataset.planCorrection;
    studioState.selected = button.dataset.planNode || "";
    studioState.view = "plan";
    renderProgramStudio();
    const target = button.dataset.planField ? document.getElementById(button.dataset.planField) : null;
    (target || document.getElementById("studio-plan-section"))?.focus();
  }));
  document.querySelectorAll("[data-studio-capability]").forEach((field) => field.addEventListener("change", () => { const values = [...document.querySelectorAll("[data-studio-capability]:checked")].map((item) => item.dataset.studioCapability); studioState.document.requested_capabilities = values.sort(); studioState.jsonDraft = ""; queueStudioModel(); }));
  document.querySelectorAll("[data-studio-stop]").forEach((field) => field.addEventListener("change", () => { studioState.document.stop_conditions = [...document.querySelectorAll("[data-studio-stop]:checked")].map((item) => item.dataset.studioStop); studioState.jsonDraft = ""; queueStudioModel(); }));
  document.querySelectorAll("[data-studio-budget]").forEach((field) => field.addEventListener("change", () => { studioState.document.budgets[field.dataset.studioBudget] = maybeNumber(field.value); studioState.jsonDraft = ""; queueStudioModel(); }));
  document.getElementById("studio-delete-node")?.addEventListener("click", removeStudioNode);
  document.getElementById("studio-duplicate-node")?.addEventListener("click", duplicateStudioNode);
  document.querySelectorAll("[data-studio-diagnostic]").forEach((button) => button.addEventListener("click", () => {
    const diagnostic = (studioState.model.validation.diagnostics || []).find((item) => item.pointer === button.dataset.studioDiagnostic);
    const id = button.dataset.nodeId || diagnostic?.target?.node_id;
    const fieldId = button.dataset.fieldId || diagnostic?.target?.field_id;
    studioState.jsonPointer = button.dataset.studioDiagnostic;
    if (id) { studioState.selected = id; studioState.view = "technical"; studioState.technicalMode = "graph"; }
    else { studioState.view = "technical"; studioState.technicalMode = "config"; }
    renderProgramStudio();
    const direct = fieldId ? document.getElementById(fieldId) : null;
    if (direct) { direct.focus(); direct.scrollIntoView({ block: "center" }); return; }
    if (studioState.view !== "technical" || studioState.technicalMode !== "config") { studioState.view = "technical"; studioState.technicalMode = "config"; renderProgramStudio(); }
    const text = document.getElementById("studio-json-text");
    if (!text) return;
    const field = String(studioState.jsonPointer).split("/").filter(Boolean).pop();
    const offset = text.value.indexOf(`"${field}"`);
    if (offset >= 0) text.setSelectionRange(offset, offset + field.length + 2);
    text.focus(); text.scrollIntoView({ block: "center" });
  }));
  document.querySelectorAll("[data-studio-scenario]").forEach((button) => button.addEventListener("click", () => { studioState.scenario = button.dataset.studioScenario; renderProgramStudio(); }));
  wireStudioCanvas();
  const jsonText = document.getElementById("studio-json-text");
  jsonText?.addEventListener("input", () => { studioState.jsonDraft = jsonText.value; });
  document.getElementById("studio-json-apply")?.addEventListener("click", () => {
    const error = document.getElementById("studio-json-error");
    try { const parsed = JSON.parse(jsonText.value); studioState.document = parsed; studioState.name = parsed.slug || studioState.name; studioState.selected = ""; studioState.jsonDraft = ""; studioState.jsonPointer = ""; studioState.view = "technical"; studioState.technicalMode = "graph"; refreshStudioModel(); }
    catch (err) { error.hidden = false; error.textContent = `JSON refused: ${err.message}`; }
  });
  document.getElementById("studio-json-import")?.addEventListener("change", async (event) => { const file = event.target.files[0]; if (!file) return; jsonText.value = await file.text(); studioState.jsonDraft = jsonText.value; });
}

function bundleBadges(items, tone = "") {
  return (items || []).map((item) => badge(String(item), tone)).join(" ") || '<span class="hint">None declared.</span>';
}

function renderStudioBundle(model) {
  if (!model.valid && model.refusal) {
    app.innerHTML = `<div class="program-studio studio-bundle-review"><header class="bundle-hero refused"><div><span class="orch-eyebrow">Generated program review</span><h1>Bundle review refused</h1><p>${esc(model.refusal)}</p></div>${badge("needs attention", "issue")}</header><p class="studio-no-grant">This review is read-only. It accepted no lease or permission credential, wrote nothing, and started nothing.</p></div>`;
    return;
  }
  const scope = model.roadmap_scope || {};
  const workflow = model.workflow || {};
  const team = model.team || {};
  const diagnostics = model.diagnostics || [];
  const simulation = model.simulation || {};
  const driverProfiles = model.driver_resolution?.profiles || [];
  const criteria = (model.rubrics || []).flatMap((rubric) => (rubric.criteria || []).map((criterion) => ({ ...criterion, rubric: rubric.title })));
  app.innerHTML = `<div class="program-studio studio-bundle-review" data-bundle-valid="${model.valid ? "true" : "false"}">
    <header class="bundle-hero ${model.valid ? "ready" : "refused"}"><div><span class="orch-eyebrow">Program Studio · generated bundle</span><h1>${esc(model.title)}</h1><p>${esc(model.summary)}</p></div>${badge(model.valid ? "ready for setup review" : `${diagnostics.length} linked issue${diagnostics.length === 1 ? "" : "s"}`, model.valid ? "ok" : "issue")}</header>
    <section class="bundle-configuration" aria-labelledby="bundle-configuration-title"><div><span class="orch-eyebrow">Separate from authority</span><h2 id="bundle-configuration-title">${esc(model.configuration?.label)}</h2><p>These are two kinds of configuration. Neither saves itself, creates permission, or starts delivery.</p></div><div class="bundle-config-cards"><article class="tracked"><span>${esc(model.configuration?.tracked?.label)}</span><strong>Roadmap and program policy</strong><code>${esc(model.configuration?.tracked?.source)}</code><small>non-authorizing</small></article><article class="git-local"><span>${esc(model.configuration?.git_local?.label)}</span><strong>Local non-secret driver resolution</strong><code>${esc(model.configuration?.git_local?.source)}</code><small>non-authorizing</small></article></div></section>
    ${diagnostics.length ? `<section class="bundle-diagnostics" aria-labelledby="bundle-diagnostics-title"><header><div><span class="orch-eyebrow">Whole-bundle check</span><h2 id="bundle-diagnostics-title">Source decisions that need attention</h2><p>The shared program validator checked the embedded roadmap, policy documents, budgets, and local roster together.</p></div>${badge(`${diagnostics.length} issue${diagnostics.length === 1 ? "" : "s"}`, "issue")}</header><ol>${diagnostics.map((item) => `<li><a href="${esc(item.anchor_href)}" data-bundle-anchor="${esc(item.anchor_id)}"><span>${esc(item.code)}</span><strong>${esc(item.message)}</strong><code>${esc(item.source)}${esc(item.pointer)}</code><small>${esc(item.remediation)}</small></a></li>`).join("")}</ol></section>` : `<section class="bundle-diagnostics clear"><div><span class="orch-eyebrow">Whole-bundle check</span><h2>Every linked decision agrees</h2><p>The shared program validator found no roadmap, workflow, review, budget, team, diversity, or local-driver contradiction.</p></div>${badge("ready", "ok")}</section>`}
    <div class="bundle-overview-grid">
      <section id="${esc(model.sections.scope)}" class="bundle-section"><span class="orch-eyebrow">What will run</span><h2>${esc(scope.project_title)}</h2><p>The generated program selects work only inside this reviewed roadmap scope.</p><dl><div><dt>Project</dt><dd>${esc(scope.project)}</dd></div><div><dt>Phases</dt><dd>${bundleBadges(scope.phase_numbers)}</dd></div><div><dt>Stories</dt><dd>${bundleBadges(scope.story_ids)}</dd></div></dl></section>
      <section id="${esc(model.sections.workflow)}" class="bundle-section wide"><span class="orch-eyebrow">How work moves</span><h2>${esc(workflow.title)}</h2><p>${esc(workflow.summary)}</p><ol class="bundle-route">${(workflow.nodes || []).map((node) => `<li><span>${esc(node.type)}</span><strong>${esc(node.id)}</strong>${node.role ? `<small>${esc(node.role)}</small>` : ""}</li>`).join("")}${(workflow.terminals || []).map((terminal) => `<li class="terminal"><span>stop</span><strong>${esc(terminal.id)}</strong><small>${esc(terminal.description)}</small></li>`).join("")}</ol></section>
      <section id="${esc(model.sections.team)}" class="bundle-section wide"><span class="orch-eyebrow">Who implements and verifies</span><h2>${esc(team.title)}</h2><p>${esc(team.independence_explanation)}</p><div class="bundle-seat-grid">${(team.seats || []).map((seat) => `<article><span>${esc(seat.duty)}</span><strong>${esc(seat.profile)}</strong><p>${esc(seat.workspace)} · ${esc(seat.local?.provider_family)}</p>${seat.independent_from?.length ? `<small>independent from ${esc(seat.independent_from.join(", "))}</small>` : '<small>isolated implementation seat</small>'}${badge(seat.local?.available ? "available locally" : "missing locally", seat.local?.available ? "ok" : "issue")}</article>`).join("")}</div><p class="bundle-rules">${(team.independence_rules || []).map((rule) => `${esc(rule.kind)}: ${esc(rule.roles.join(" ↔ "))}`).join(" · ")}</p></section>
      <section id="${esc(model.sections.checks)}" class="bundle-section wide"><span class="orch-eyebrow">What the checks prove</span><h2>Review criteria are bound to producers</h2><div class="bundle-checks">${criteria.map((criterion) => `<article class="${criterion.producer_exists === false ? "missing" : ""}"><span>${esc(criterion.rubric)}</span><strong>${esc(criterion.question)}</strong><p>${criterion.producing_check ? `Produced by <code>${esc(criterion.producing_check)}</code>` : "Independent diff-cited judgment"}</p>${criterion.producing_check ? badge(criterion.producer_exists ? "producer found" : "producer missing", criterion.producer_exists ? "ok" : "issue") : badge("verifier judgment")}</article>`).join("")}</div></section>
      <section id="${esc(model.sections.capabilities)}" class="bundle-section"><span class="orch-eyebrow">What it may request later</span><h2>Bounded allowed work</h2><p>Policy requests are not permission. Separate approval may authorize only a reviewed subset.</p><div>${bundleBadges(model.requested_capabilities, "warn")}</div></section>
      <section id="${esc(model.sections.budgets)}" class="bundle-section"><span class="orch-eyebrow">What it can spend</span><h2>Finite budgets</h2><dl class="bundle-budgets">${Object.entries(model.budgets || {}).map(([name, value]) => `<div><dt>${esc(name.replace(/^max_/, "").replaceAll("_", " "))}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl></section>
      <section id="${esc(model.sections.stops)}" class="bundle-section"><span class="orch-eyebrow">When it stops</span><h2>Declared stop conditions</h2><div>${bundleBadges(model.stop_conditions)}</div><p>No stop provides permission to continue by itself.</p></section>
      <section id="${esc(model.sections.drivers)}" class="bundle-section"><span class="orch-eyebrow">Local driver resolution</span><h2>${esc(model.driver_resolution?.status || "not checked")}</h2><div class="bundle-drivers">${driverProfiles.map((profile) => `<article><strong>${esc(profile.profile)}</strong><span>${esc(profile.provider_family)} · ${esc(profile.adapter?.kind || "adapter unresolved")}</span><small>${esc(profile.model?.alias || "model unresolved")}</small>${badge(profile.available ? "available" : "unavailable", profile.available ? "ok" : "issue")}</article>`).join("") || '<p class="hint">No local profiles resolved.</p>'}</div><p>Local bindings disclose availability and non-secret metadata only.</p></section>
    </div>
    <section class="bundle-simulation"><header><div><span class="orch-eyebrow">Pure simulation</span><h2>One bounded route, before any work starts</h2><p>This is the same scaffold simulation core used by the terminal surface. It writes no state.</p></div>${badge(simulation.bounded ? "bounded" : "unavailable", simulation.bounded ? "ok" : "issue")}</header><ol class="bundle-route">${(simulation.green_route || []).map((step) => `<li><strong>${esc(step)}</strong></li>`).join("")}</ol><details><summary>Failure and repair routes</summary><p><strong>Repair:</strong> ${esc((simulation.repair_route || []).join(" → "))}</p><ul>${(simulation.failure_routes || []).map((route) => `<li><code>${esc(route.type)}</code> stops at <strong>${esc(route.target)}</strong></li>`).join("")}</ul></details></section>
    <section id="${esc(model.sections.handoff)}" class="bundle-handoff"><div><span class="orch-eyebrow">After dw setup apply</span><h2>${esc(model.handoff?.label)}</h2><p>Return to the terminal for a fresh, separate permission preview. The browser creates nothing and runs nothing.</p></div><code>${esc(model.handoff?.command)}</code><small>configuration only · creates permission: false</small></section>
  </div>`;
  document.querySelectorAll("[data-bundle-anchor]").forEach((link) => link.addEventListener("click", () => {
    // Scroll only after the link's default fragment navigation has updated layout;
    // this frame does not move or restore keyboard focus.
    requestAnimationFrame(() => document.getElementById(link.dataset.bundleAnchor)?.scrollIntoView({ block: "start" }));
  }));
}

async function viewStudioBundle(anchor = "") {
  const proposalFile = new URLSearchParams(location.search).get("proposal_file") || "";
  setCrumbs([{ label: "overview", href: "#/" }, { label: "delivery setup", href: "#/program-studio" }, { label: "generated bundle" }]);
  const response = await api(`/api/setup/bundle?proposal_file=${encodeURIComponent(proposalFile)}`);
  renderStudioBundle(response.data);
  // Defer scrolling until the newly rendered bundle has a layout box. This is
  // scroll-only and deliberately leaves keyboard focus unchanged.
  if (anchor) requestAnimationFrame(() => document.getElementById(anchor)?.scrollIntoView({ block: "start" }));
}

async function viewProgramStudio(family = "program", name) {
  family = STUDIO_FAMILIES.includes(family) ? family : "program";
  const familyLabel = family === "program" ? "delivery plans" : family === "workflow" ? "work flows" : "teams and review";
  setCrumbs([{ label: "overview", href: "#/" }, { label: "delivery setup", href: "#/program-studio" }, { label: familyLabel }, ...(name ? [{ label: name }] : [])]);
  studioState.inventory = (await api("/api/program-studio")).data;
  studioState.family = family; studioState.error = ""; studioState.selected = ""; studioState.jsonDraft = ""; studioState.jsonPointer = "";
  studioState.view = "plan";
  studioState.planSection = family === "organization" ? "responsibilities" : "scope";
  studioState.technicalMode = "graph";
  studioState.technicalExpanded = false;
  const familyModel = studioFamilyModel(family);
  const chosen = (!name && family === "program" && pendingProgramSetup)
    ? null
    : (name || familyModel.items?.[0]?.name);
  if (chosen) {
    const detail = (await api(`/api/program-studio/${encodeURIComponent(family)}/${encodeURIComponent(chosen)}`)).data;
    studioState.name = detail.name; studioState.document = clone(detail.raw); studioState.model = detail; studioState.exists = true;
  } else {
    studioState.document = clone(familyModel.draft); studioState.name = studioState.document.slug; studioState.model = null; studioState.exists = false;
    if (family === "program" && pendingProgramSetup) {
      const phase = Number(pendingProgramSetup.phase);
      studioState.document.scope ||= {};
      studioState.document.scope.project = pendingProgramSetup.project || "";
      if (Number.isInteger(phase) && phase >= 0) {
        studioState.document.scope.phases = { from: phase, through: phase };
      }
      studioState.setupContext = { ...pendingProgramSetup };
      pendingProgramSetup = null;
    } else {
      studioState.setupContext = null;
    }
  }
  if (chosen) studioState.setupContext = null;
  const studioParams = new URLSearchParams(location.search);
  const requestedView = studioParams.get("studioview");
  if (STUDIO_VIEWS.includes(requestedView)) studioState.view = requestedView;
  const requestedSection = studioParams.get("studiosection");
  if ((studioAuthoring()?.sections || []).some((section) => section.id === requestedSection)) studioState.planSection = requestedSection;
  studioState.technicalExpanded = studioParams.get("studiofold") === "1";
  const requestedTechnical = studioParams.get("studiotechnical");
  if (["graph", "config"].includes(requestedTechnical)) studioState.technicalMode = requestedTechnical;
  const requestedScenario = new URLSearchParams(location.search).get("studioscenario");
  if (requestedScenario) studioState.scenario = requestedScenario;
  if (studioState.model) renderProgramStudio(); else { renderProgramStudio(); await refreshStudioModel(); }
  if (studioParams.get("studiofocus") === "technical") {
    // Model refresh may render this fold twice; wait for both layouts before
    // scrolling, without deferring or changing keyboard focus.
    requestAnimationFrame(() => requestAnimationFrame(() => (
      document.querySelector(".studio-form-technical")?.scrollIntoView({ block: "start" })
    )));
  }
}
