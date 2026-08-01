"use strict";

/* ── visual orchestration editor (WLA-24-03) ─────────────────────────
 * The browser authors a complete score but owns no semantics. Every live
 * verdict and scheduling trace comes from the shared Python compiler through
 * the pure preview endpoint. Saving and deleting are separate, stale-safe
 * preview → diff → apply acts; neither endpoint can create run state. */

const ORCH_NODE_TYPES = ["agent", "check", "rail", "approval", "collect"];
const ORCH_ROLES = ["research", "synthesis", "implementation", "review", "verification", "documentation", "repair"];
const ORCH_CAPABILITIES = ["repository-read", "repository-write", "network", "tools-read", "tools-write"];
const ORCH_FORMATS = ["markdown", "json", "text", "git-diff", "directory"];
const ORCH_TERMINALS = ["", "complete", "blocked", "cancelled", "awaiting-certification"];

let orchState = {
  name: "", score: null, exists: false, selected: null, view: "design",
  preview: null, inventory: [], validationTimer: null, jsonDraft: "",
  runInventory: [], runs: [], runId: "", runView: null, runLoading: false,
  runError: "", runPlan: null, runAct: null, runResult: null, runStream: null,
  runConnection: { status: SNAPSHOT_LIVE_STATE === "stale" ? "stale" : "checking" },
  grantDraft: { project: "", story: "", operator: "", minutes: 60 },
  controlReason: "", maxTicks: 100, maxSeconds: 300,
};

function clone(value) { return JSON.parse(JSON.stringify(value)); }
function splitLines(value) { return String(value || "").split(/\n|,/).map((x) => x.trim()).filter(Boolean); }
function maybeNumber(value) { const n = Number(value); return value === "" || !Number.isFinite(n) ? null : Math.trunc(n); }
function setOptional(target, key, value) { if (value === "" || value === null || value === undefined) delete target[key]; else target[key] = value; }

function minimalScore(slug = "new-orchestration") {
  return {
    kind: "delivery-workbench-orchestration", schema_version: 1,
    slug, title: "New orchestration",
    defaults: {
      max_concurrency: 2, max_wall_seconds: 3600, max_agent_starts: 8,
      max_check_starts: 16, default_timeout_seconds: 900,
      max_artifact_bytes: 1000000,
    },
    nodes: [{
      id: "human-handoff", type: "approval", activation: "success", needs: [],
      resource_groups: [], prompt: "Review the run before certification.",
      options: ["approve", "reject"], terminal: "awaiting-certification",
    }],
    layout: { nodes: { "human-handoff": { x: 80, y: 120 } }, viewport: { x: 0, y: 0, zoom: 1 } },
  };
}

function ensureOrchShape(score) {
  score.defaults ||= {};
  score.nodes = Array.isArray(score.nodes) ? score.nodes : [];
  score.layout ||= {};
  score.layout.nodes ||= {};
  score.layout.viewport ||= { x: 0, y: 0, zoom: 1 };
  score.nodes.forEach((node, i) => {
    node.needs = Array.isArray(node.needs) ? node.needs : [];
    node.resource_groups = Array.isArray(node.resource_groups) ? node.resource_groups : [];
    if (!score.layout.nodes[node.id]) score.layout.nodes[node.id] = { x: 70 + (i % 4) * 240, y: 70 + Math.floor(i / 4) * 170 };
  });
  return score;
}

function nextNodeId(type) {
  const base = type === "approval" ? "checkpoint" : type;
  const used = new Set(orchState.score.nodes.map((n) => n.id));
  let i = 1;
  while (used.has(`${base}-${i}`)) i += 1;
  return `${base}-${i}`;
}

function defaultOrchNode(type) {
  const id = nextNodeId(type);
  const common = { id, type, activation: "success", needs: [], resource_groups: [] };
  if (type === "agent") return { ...common, role: "research", profile: "research-readonly", prompt: "", context: [], capabilities: ["repository-read"], workspace: "read-only", inputs: [], outputs: [], timeout_seconds: 900, on_failure: { action: "pause" } };
  if (type === "check") return { ...common, runner: { kind: "command", argv: ["python3", "-m", "pytest", "-q"], cwd: "workspace", timeout_seconds: 900, output_bytes: 30000, writes: [] }, expect: { exit_code: 0 }, on_failure: { action: "pause" } };
  if (type === "rail") return { ...common, action: "continue-story", timeout_seconds: 120, on_failure: { action: "pause" } };
  if (type === "approval") return { ...common, prompt: "Review this checkpoint.", options: ["approve", "reject"] };
  return { ...common, inputs: [], outputs: [], timeout_seconds: 120, on_failure: { action: "abort" } };
}

function orchField(label, name, value, type = "text", attrs = "") {
  return `<label class="orch-field"><span>${esc(label)}</span><input type="${type}" name="${esc(name)}" value="${esc(value ?? "")}" ${attrs}></label>`;
}
function orchArea(label, name, value, hint = "") {
  return `<label class="orch-field"><span>${esc(label)}</span><textarea name="${esc(name)}">${esc(value ?? "")}</textarea>${hint ? `<small>${esc(hint)}</small>` : ""}</label>`;
}
function orchSelect(label, name, options, selected) {
  return `<label class="orch-field"><span>${esc(label)}</span><select name="${esc(name)}">${options.map((o) => {
    const value = typeof o === "string" ? o : o.value;
    const text = typeof o === "string" ? o : o.label;
    return `<option value="${esc(value)}"${value === selected ? " selected" : ""}>${esc(text)}</option>`;
  }).join("")}</select></label>`;
}
function orchDatalist(label, name, options, value) {
  const id = `orch-list-${name}`;
  return `<label class="orch-field"><span>${esc(label)}</span><input type="text" name="${esc(name)}" value="${esc(value || "")}" list="${id}"><datalist id="${id}">${options.map((o) => `<option value="${esc(o)}"></option>`).join("")}</datalist></label>`;
}

function inputLines(inputs) {
  return (inputs || []).map((item) => typeof item === "string"
    ? item : `artifact:${item.artifact}:${item.format}`).join("\n");
}

function parseInputLines(raw) {
  return splitLines(raw).map((line) => {
    const match = line.match(/^artifact:([a-z0-9-]+):([a-z-]+)$/);
    return match ? { artifact: match[1], format: match[2] } : line;
  });
}

function outputEditor(outputs) {
  return `<div class="orch-outputs"><div class="orch-subhead"><strong>typed outputs</strong><button type="button" data-orch-add-output>+ output</button></div>
    ${(outputs || []).map((out, i) => `<fieldset class="orch-output" data-output-index="${i}">
      <legend>output ${i + 1} <button type="button" data-orch-remove-output="${i}" aria-label="remove output ${i + 1}">remove</button></legend>
      ${orchField("name", "output_name", out.name)}
      ${orchSelect("format", "output_format", ORCH_FORMATS, out.format)}
      ${orchField("path", "output_path", out.path)}
      ${orchField("schema path", "output_schema", out.schema || "")}
      ${orchArea("required headings", "output_sections", (out.required_sections || []).join("\n"), "one heading per line")}
      ${orchSelect("citations", "output_citations", ["none", "optional", "required"], out.citations || "none")}
      ${orchField("maximum bytes", "output_max_bytes", out.max_bytes || "", "number", 'min="1"')}
      ${orchArea("allowed paths", "output_allowed_paths", (out.allowed_paths || []).join("\n"), "required for git-diff outputs")}
    </fieldset>`).join("")}</div>`;
}

function failureEditor(node) {
  const f = node.on_failure || {};
  return `<fieldset class="orch-failure"><legend>failure route</legend>
    ${orchSelect("action", "failure_action", ["", "retry", "route", "approval", "pause", "abort"], f.action || "")}
    ${orchField("max attempts", "failure_max_attempts", f.max_attempts || "", "number", 'min="1" max="20"')}
    ${orchSelect("route node", "failure_node", [""].concat(orchState.score.nodes.filter((n) => n.id !== node.id).map((n) => n.id)), f.node || "")}
    ${orchField("max visits", "failure_max_visits", f.max_visits || "", "number", 'min="1" max="20"')}
    ${orchField("approval checkpoint", "failure_checkpoint", f.checkpoint || "")}
  </fieldset>`;
}

function nodeInspector(node) {
  const others = orchState.score.nodes.filter((n) => n.id !== node.id);
  const relevant = ((orchState.preview && orchState.preview.validation && orchState.preview.validation.diagnostics) || [])
    .filter((d) => d.pointer.startsWith(`/nodes/${orchState.score.nodes.indexOf(node)}`));
  let specific = "";
  if (node.type === "agent") {
    specific = `
      ${orchDatalist("role", "role", ORCH_ROLES, node.role)}
      ${orchField("logical profile", "profile", node.profile)}
      ${orchArea("prompt template", "prompt", node.prompt || "", "bounded text; never a provider command")}
      ${orchArea("context selectors", "context", (node.context || []).join("\n"), "one contained selector per line")}
      <fieldset><legend>requested capabilities</legend><div class="orch-checkgrid">${ORCH_CAPABILITIES.map((cap) => `<label><input type="checkbox" name="capability" value="${cap}"${(node.capabilities || []).includes(cap) ? " checked" : ""}>${cap}</label>`).join("")}</div></fieldset>
      ${orchSelect("workspace", "workspace", ["none", "read-only", "isolated-worktree"], node.workspace || "read-only")}
      ${orchArea("inputs", "inputs", inputLines(node.inputs), "selector or artifact:name:format, one per line")}
      ${outputEditor(node.outputs)}`;
  } else if (node.type === "check") {
    const r = node.runner || { kind: "command" };
    specific = `
      ${orchSelect("runner kind", "runner_kind", ["command", "builtin"], r.kind || "command")}
      ${orchArea("command argv tokens", "runner_argv", (r.argv || []).join("\n"), "one literal token per line; no command string or interpolation")}
      ${orchField("working directory", "runner_cwd", r.cwd || ".")}
      ${orchSelect("built-in check", "runner_name", ["", "file-exists", "json-schema", "diff-scope", "rail-status"], r.name || "")}
      ${orchField("built-in path", "runner_path", r.path || "")}
      ${orchField("schema path", "runner_schema", r.schema || "")}
      ${orchArea("allowed paths", "runner_allowed_paths", (r.allowed_paths || []).join("\n"))}
      ${orchField("timeout seconds", "runner_timeout", r.timeout_seconds || "", "number", 'min="1"')}
      ${orchField("output bytes", "runner_output_bytes", r.output_bytes || "", "number", 'min="1"')}
      ${orchArea("declared writes", "runner_writes", (r.writes || []).join("\n"), "command checks only; empty means read-only")}
      ${orchField("expected exit code", "expect_exit_code", (node.expect || {}).exit_code ?? 0, "number", 'min="0" max="255"')}`;
  } else if (node.type === "rail") {
    specific = `${orchField("dw step action id", "action", node.action || "")}`;
  } else if (node.type === "approval") {
    specific = `${orchArea("checkpoint prompt", "prompt", node.prompt || "")}
      ${orchArea("decision options", "options", (node.options || []).join("\n"), "one explicit option per line")}
      ${orchSelect("terminal meaning", "terminal", ORCH_TERMINALS, node.terminal || "")}`;
  } else if (node.type === "collect") {
    specific = `${orchArea("artifact inputs", "inputs", inputLines(node.inputs), "artifact:name:format, one per line")}${outputEditor(node.outputs)}`;
  }
  return `<div class="orch-inspector-head"><div><small>selected node</small><strong>${esc(node.id)}</strong></div>
      <div><button type="button" data-orch-duplicate-node>duplicate</button><button type="button" class="danger" data-orch-delete-node>delete</button></div></div>
    <div class="orch-node-errors"${relevant.length ? "" : " hidden"}>${relevant.map((d) => `<div><code>${esc(d.pointer)}</code> ${esc(d.message)}</div>`).join("")}</div>
    <form id="orch-node-form" class="orch-inspector-form">
      ${orchField("node id", "id", node.id, "text", 'pattern="[a-z][a-z0-9-]*"')}
      ${orchSelect("node type", "type", ORCH_NODE_TYPES, node.type)}
      ${orchField("title", "title", node.title || "")}
      ${orchArea("description", "description", node.description || "")}
      ${orchSelect("activation", "activation", ["success", "failure"], node.activation || "success")}
      <fieldset><legend>success dependencies</legend><div class="orch-checkgrid">${others.map((other) => `<label><input type="checkbox" name="need" value="${esc(other.id)}"${(node.needs || []).includes(other.id) ? " checked" : ""}>${esc(other.id)}</label>`).join("") || "<small>no other nodes yet</small>"}</div></fieldset>
      ${orchArea("resource locks", "resource_groups", (node.resource_groups || []).join("\n"), "one resource group per line")}
      ${node.type !== "check" && node.type !== "approval" ? orchField("timeout seconds", "timeout_seconds", node.timeout_seconds || "", "number", 'min="1"') : ""}
      ${specific}
      ${node.type !== "approval" ? failureEditor(node) : ""}
    </form>`;
}

function scoreInspector() {
  const score = orchState.score;
  const d = score.defaults || {};
  const v = (score.layout || {}).viewport || {};
  return `<div class="orch-inspector-head"><div><small>score settings</small><strong>${esc(score.slug)}</strong></div></div>
    <form id="orch-score-form" class="orch-inspector-form">
      ${orchField("slug / filename", "slug", score.slug, "text", 'pattern="[a-z][a-z0-9-]*"')}
      ${orchField("title", "title", score.title)}
      ${orchArea("description", "description", score.description || "")}
      ${orchField("roadmap project", "project", score.project || "")}
      <fieldset><legend>finite run defaults</legend>
        ${orchField("maximum concurrency", "max_concurrency", d.max_concurrency || "", "number", 'min="1" max="64"')}
        ${orchField("maximum wall seconds", "max_wall_seconds", d.max_wall_seconds || "", "number", 'min="1"')}
        ${orchField("maximum agent starts", "max_agent_starts", d.max_agent_starts || "", "number", 'min="1"')}
        ${orchField("maximum check starts", "max_check_starts", d.max_check_starts || "", "number", 'min="1"')}
        ${orchField("default timeout seconds", "default_timeout_seconds", d.default_timeout_seconds || "", "number", 'min="1"')}
        ${orchField("maximum artifact bytes", "max_artifact_bytes", d.max_artifact_bytes || "", "number", 'min="1"')}
      </fieldset>
      <fieldset><legend>canvas viewport (document hash only)</legend>
        ${orchField("viewport x", "viewport_x", v.x ?? 0, "number")}
        ${orchField("viewport y", "viewport_y", v.y ?? 0, "number")}
        ${orchField("zoom", "viewport_zoom", v.zoom ?? 1, "number", 'min="0.1" step="0.1"')}
      </fieldset>
    </form>`;
}

function diagnosticMap() {
  const map = new Map();
  const diagnostics = orchState.preview?.validation?.diagnostics || [];
  diagnostics.forEach((d) => {
    const match = d.pointer.match(/^\/nodes\/(\d+)/);
    if (!match) return;
    const node = orchState.score.nodes[Number(match[1])];
    if (!node) return;
    if (!map.has(node.id)) map.set(node.id, []);
    map.get(node.id).push(d);
  });
  return map;
}

function orchGraph() {
  const score = ensureOrchShape(orchState.score);
  const positions = score.layout.nodes;
  const byId = Object.fromEntries(score.nodes.map((n) => [n.id, n]));
  const errors = diagnosticMap();
  const maxX = Math.max(900, ...Object.values(positions).map((p) => Number(p.x || 0) + 240));
  const maxY = Math.max(500, ...Object.values(positions).map((p) => Number(p.y || 0) + 150));
  const edges = [];
  score.nodes.forEach((node) => {
    const target = positions[node.id] || { x: 0, y: 0 };
    (node.needs || []).forEach((need) => {
      const source = positions[need];
      if (source) edges.push(`<path class="orch-edge success" d="M ${Number(source.x) + 190} ${Number(source.y) + 48} C ${Number(source.x) + 220} ${Number(source.y) + 48}, ${Number(target.x) - 30} ${Number(target.y) + 48}, ${Number(target.x)} ${Number(target.y) + 48}" marker-end="url(#arrow-success)"><title>${esc(need)} succeeds before ${esc(node.id)}</title></path>`);
    });
    if (node.on_failure?.action === "route" && positions[node.on_failure.node]) {
      const failure = positions[node.on_failure.node];
      edges.push(`<path class="orch-edge failure" d="M ${Number(target.x) + 95} ${Number(target.y) + 96} C ${Number(target.x) + 95} ${Number(target.y) + 130}, ${Number(failure.x) + 95} ${Number(failure.y) - 30}, ${Number(failure.x) + 95} ${Number(failure.y)}" marker-end="url(#arrow-failure)"><title>${esc(node.id)} failure routes to ${esc(node.on_failure.node)}</title></path>`);
    }
  });
  return `<div class="orch-canvas-wrap"><svg id="orch-canvas" class="orch-canvas" viewBox="0 0 ${maxX} ${maxY}" role="group" aria-labelledby="orch-canvas-title">
    <title id="orch-canvas-title">Orchestration graph. Select a node to edit its exact rules.</title>
    <defs>
      <marker id="arrow-success" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="arrow-success"></path></marker>
      <marker id="arrow-failure" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="arrow-failure"></path></marker>
    </defs>
    ${edges.join("")}
    ${score.nodes.map((node) => {
      const pos = positions[node.id];
      const detail = node.type === "agent" ? `${node.role || "agent"} · ${node.profile || "profile?"}`
        : node.type === "check" ? `${node.runner?.kind || "runner?"} check`
        : node.type === "approval" ? (node.terminal || "checkpoint") : node.type;
      const count = (errors.get(node.id) || []).length;
      return `<g class="orch-node type-${esc(node.type)}${node.activation === "failure" ? " failure-only" : ""}${orchState.selected === node.id ? " selected" : ""}${count ? " has-error" : ""}"
          data-node-id="${esc(node.id)}" transform="translate(${Number(pos.x)},${Number(pos.y)})" tabindex="0" role="button" aria-label="${esc(node.id)}, ${esc(detail)}${count ? `, ${count} errors` : ""}">
        <title>${esc(node.id)} — ${esc(detail)}${count ? ` — ${count} compiler errors` : ""}</title>
        <rect width="190" height="96" rx="9"></rect>
        <circle class="port input" cx="0" cy="48" r="5"></circle><circle class="port output" cx="190" cy="48" r="5"></circle><circle class="port fail" cx="95" cy="96" r="5"></circle>
        <text class="node-type" x="14" y="21">${esc(node.type)}${node.activation === "failure" ? " · failure" : ""}</text>
        <text class="node-id" x="14" y="48">${esc(node.id)}</text>
        <text class="node-detail" x="14" y="72">${esc(detail).slice(0, 27)}</text>
        ${count ? `<text class="node-error" x="174" y="21" text-anchor="end">${count}!</text>` : ""}
      </g>`;
    }).join("")}
  </svg></div>`;
}

function validateView() {
  const p = orchState.preview;
  if (!p) return stateHtml("Checking delivery readiness…");
  const diagnostics = p.validation?.diagnostics || [];
  const technicalOpen = new URLSearchParams(location.search).has("orchtechnical");
  if (!p.valid) return `<div class="orch-validation invalid delivery-preflight" role="region" aria-label="Delivery readiness results">
    <header class="preflight-head"><div><span>Delivery readiness</span><h2>${diagnostics.length} delivery decision${diagnostics.length === 1 ? "" : "s"} need attention</h2><p>Nothing was saved or started. Correct the affected part of the delivery plan, then check readiness again.</p></div>${badge("not ready", "issue")}</header>
    <ol class="preflight-corrections">${diagnostics.map((d) => `<li data-pointer="${esc(d.pointer)}"><strong>Affected decision</strong><span>${esc(d.message)}</span><small>Next step: ${esc(d.remediation)}</small></li>`).join("")}</ol>
    <div class="preflight-actions"><a href="#/program-studio">Return to delivery choices</a></div>
    <details class="preflight-technical"${technicalOpen ? " open" : ""}><summary>Technical details</summary>
      <p>Exact compiler targets and identifiers:</p>
      <ol class="orch-diagnostics">${diagnostics.map((d) => `<li data-pointer="${esc(d.pointer)}"><code>${esc(d.pointer)}</code><strong>${esc(d.code)}</strong><span>${esc(d.message)}</span><small>${esc(d.remediation)}</small></li>`).join("")}</ol>
    </details>
  </div>`;
  const c = p.compiled;
  const s = p.simulation;
  const nodeCount = c.score?.nodes?.length || orchState.score.nodes?.length || 0;
  const profiles = c.analysis.profiles || [];
  return `<div class="orch-validation valid delivery-preflight" role="region" aria-label="Delivery readiness results">
    <header class="preflight-head"><div><span>Delivery readiness</span><h2>This delivery plan is ready to review</h2><p>The work order, checks, decisions, limits, and stops are internally valid. This inspection starts nothing.</p></div>${badge("ready to review", "ok")}</header>
    <div class="preflight-facts">
      <section><span>Work and order</span><strong>${esc(nodeCount)} planned step${nodeCount === 1 ? "" : "s"} in ${esc(s.waves.length)} group${s.waves.length === 1 ? "" : "s"}</strong><small>The displayed order comes from the shared delivery-plan simulation.</small></section>
      <section><span>Team</span><strong>${profiles.length ? `${esc(profiles.length)} named responsibility profile${profiles.length === 1 ? "" : "s"}` : "No agent profile requested"}</strong><small>${profiles.length ? esc(profiles.join(", ")) : "Checks and human decisions may still be present."}</small></section>
      <section><span>Review</span><strong>${esc(s.failure_branches.length)} repair or stop route${s.failure_branches.length === 1 ? "" : "s"} · ${esc(s.checkpoints.length)} decision point${s.checkpoints.length === 1 ? "" : "s"}</strong><small>Failed work follows the reviewed route; no route is improvised at start.</small></section>
      <section><span>Permission</span><strong>Still off</strong><small>A separate start review must name the current work, accountable operator, limits, and expiry.</small></section>
    </div>
    <section class="preflight-limits"><div><span>Limits and stops</span><strong>Finite before start</strong></div><div>${Object.entries(s.budgets).map(([k, v]) => `<div class="kv"><div class="k">${esc(k.replace(/^max_/, "").replaceAll("_", " "))}</div><div class="v">${esc(v)}</div></div>`).join("")}</div></section>
    <div class="preflight-next"><div><span>Next step</span><strong>Review the separate delivery start</strong><p>Confirming that later review creates permission for this delivery; it does not continue automatically.</p></div><div><button type="button" id="preflight-open-start">Review separate start</button><a href="#/program-studio">Return to delivery choices</a><a href="#/">Leave for now</a></div></div>
    <details class="preflight-technical"${technicalOpen ? " open" : ""}><summary>Technical details</summary>
      <div class="orch-hashes"><div><span>semantic hash</span><code>${esc(c.semantic_hash)}</code></div><div><span>document hash</span><code>${esc(c.document_hash)}</code></div></div>
      <div class="orch-validate-grid">
        <section><h3>capability request</h3>${c.analysis.capabilities.map((x) => badge(x, "warn")).join(" ") || "none"}<h3>logical profiles</h3>${profiles.map((x) => badge(x)).join(" ") || "none"}</section>
        <section><h3>finite budgets</h3>${Object.entries(s.budgets).map(([k, v]) => `<div class="kv"><div class="k">${esc(k)}</div><div class="v">${esc(v)}</div></div>`).join("")}</section>
      </div>
      <section><h3>scheduling simulation ${badge("pure — starts nothing", "ok")}</h3><div class="orch-waves">${s.waves.map((w) => `<div><strong>wave ${w.wave}</strong><span>${w.scheduled.map((x) => `<code>${esc(x)}</code>`).join(" ")}</span><small>eligible: ${esc(w.eligible.join(", "))}${w.resource_groups.length ? ` · locks: ${esc(w.resource_groups.join(", "))}` : ""}</small></div>`).join("")}</div></section>
      <section><h3>output lineage</h3><div class="tablewrap"><table><thead><tr><th>artifact</th><th>producer</th><th>format</th><th>consumers</th><th>conventions</th></tr></thead><tbody>${s.output_lineage.map((o) => `<tr><td><code>${esc(o.name)}</code></td><td>${esc(o.producer)}</td><td>${esc(o.format)}</td><td>${esc(o.consumers.join(", ") || "—")}</td><td>${o.citations === "required" ? "citations · " : ""}${o.required_sections.length ? esc(o.required_sections.join(", ")) : `${esc(o.max_bytes)} bytes`}</td></tr>`).join("") || '<tr><td colspan="5">no declared artifacts</td></tr>'}</tbody></table></div></section>
      <section><h3>failure routes and checkpoints</h3>${s.failure_branches.map((b) => `<div class="orch-branch"><code>${esc(b.source)}</code><strong>${esc(b.action)}</strong><span>${esc(b.node || b.checkpoint || "terminal policy")}</span></div>`).join("") || "none"}<div class="orch-terminals">${s.terminals.map((t) => `${badge(t.node)} → ${badge(t.meaning, "ok")}`).join(" ")}</div></section>
    </details>
  </div>`;
}

function jsonView() {
  const text = orchState.jsonDraft || JSON.stringify(orchState.score, null, 2);
  return `<div class="orch-json"><div class="orch-json-actions"><label class="filebtn">import JSON<input type="file" id="orch-import" accept="application/json,.json"></label><button type="button" id="orch-json-to-graph">apply JSON to graph</button></div>
    <label><span>lossless score document</span><textarea id="orch-json-text" spellcheck="false">${esc(text)}</textarea></label>
    <div id="orch-json-error" class="guard" hidden></div><p class="hint">Unknown schema fields are preserved in this text and refused by the compiler; they are never silently dropped.</p></div>`;
}

function orchestrationBody() {
  if (orchState.view === "validate") return validateView();
  if (orchState.view === "json") return jsonView();
  if (orchState.view === "run") return runViewHtml();
  return `<div class="orch-design"><div class="orch-palette" aria-label="node palette">
      <button type="button" data-orch-settings>score settings</button>${ORCH_NODE_TYPES.map((type) => `<button type="button" data-orch-add="${type}">+ ${type}</button>`).join("")}
    </div><div class="orch-workarea">${orchGraph()}</div><aside class="orch-inspector" aria-label="rule inspector">${orchState.selected ? nodeInspector(orchState.score.nodes.find((n) => n.id === orchState.selected)) : scoreInspector()}</aside></div>`;
}

function renderOrchestration() {
  if (liveDetailRoute()?.kind === "run") { renderLiveMission(); return; }
  const focus = captureAppFocus();
  const current = orchState.name || orchState.score.slug;
  app.innerHTML = `${destinationNav("delivery", "#/orchestration")}<div class="orchestration" data-score="${esc(current)}">
    <header class="orch-toolbar"><div><span class="orch-eyebrow">Delivery</span><h1>${esc(orchState.score.title || orchState.score.slug)}</h1><p>Review the work and its order before you continue.</p><details><summary>Technical details</summary><span>visual orchestration score</span><code>pm/orchestration/${esc(orchState.score.slug)}.json</code></details></div>
      <div class="orch-score-actions"><label>score<select id="orch-score-select"><option value="">new unsaved score</option>${orchState.inventory.map((s) => `<option value="${esc(s.name)}"${s.name === orchState.name ? " selected" : ""}>${esc(s.slug || s.name)}${s.valid ? "" : " (invalid)"}</option>`).join("")}</select></label><button type="button" id="orch-new">new</button><button type="button" id="orch-duplicate">duplicate</button><button type="button" id="orch-preview-save">preview save</button><button type="button" id="orch-preview-delete" class="danger"${orchState.exists ? "" : " disabled"}>preview delete</button></div>
    </header>
    <div class="orch-tabs" role="tablist" aria-label="Orchestration editor views">${[
      ["design", "Design"], ["validate", "Validate"], ["json", "JSON"], ["run", "Run"],
    ].map(([id, label]) => `<button type="button" id="orch-tab-${id}" role="tab" aria-controls="orch-view" aria-selected="${orchState.view === id}" tabindex="${orchState.view === id ? "0" : "-1"}" data-orch-view="${id}" class="${orchState.view === id ? "active" : ""}">${label}${id === "validate" && orchState.preview && !orchState.preview.valid ? ` (${orchState.preview.validation.diagnostics.length})` : ""}</button>`).join("")}</div>
    <div id="orch-save-panel"></div>
    <div id="orch-view" role="tabpanel" aria-labelledby="orch-tab-${esc(orchState.view)}">${orchestrationBody()}</div>
  </div>`;
  wireOrchestration();
  wireTablist(".orch-tabs");
  finishDynamicRender(focus);
}

async function refreshOrchValidation() {
  if (!orchState.score) return;
  const focus = captureAppFocus();
  const name = orchState.score.slug || orchState.name;
  try {
    const { status, body } = await postJson("/api/orchestration/preview", { action: "save", name, score: orchState.score });
    if (status >= 400 || body.ok === false) throw new Error((body.issues && body.issues[0]) || `compiler preview ${status}`);
    orchState.preview = body.data;
  } catch (err) {
    orchState.preview = { valid: false, validation: { diagnostics: [{ pointer: "/", code: "preview-error", message: err.message, remediation: "repair the score identity or reload" }] } };
  }
  const view = document.getElementById("orch-view");
  if (view && (orchState.view === "validate" || orchState.view === "design")) {
    if (orchState.view === "validate") view.innerHTML = validateView();
    else {
      const errors = diagnosticMap();
      view.querySelectorAll(".orch-node").forEach((group) => {
        group.classList.toggle("has-error", errors.has(group.dataset.nodeId));
      });
      const slot = view.querySelector(".orch-node-errors");
      const selectedErrors = errors.get(orchState.selected) || [];
      if (slot) {
        slot.hidden = !selectedErrors.length;
        slot.innerHTML = selectedErrors.map((d) => `<div><code>${esc(d.pointer)}</code> ${esc(d.message)}</div>`).join("");
      }
    }
    const tab = document.querySelector('[data-orch-view="validate"]');
    if (tab) tab.textContent = `Validate${orchState.preview.valid ? "" : ` (${orchState.preview.validation.diagnostics.length})`}`;
    if (orchState.view === "validate") wireOrchPreflight();
    finishDynamicRender(focus);
  }
}

function queueOrchValidation() {
  clearTimeout(orchState.validationTimer);
  orchState.validationTimer = setTimeout(() => { refreshOrchValidation(); }, SNAPSHOT_MODE ? 0 : 180);
}

function updateOutputFromField(field) {
  const set = field.closest(".orch-output");
  if (!set) return false;
  const node = orchState.score.nodes.find((n) => n.id === orchState.selected);
  const index = Number(set.dataset.outputIndex);
  if (!node || !node.outputs || !node.outputs[index]) return true;
  const out = node.outputs[index];
  const map = {
    output_name: "name", output_format: "format", output_path: "path",
    output_schema: "schema", output_citations: "citations",
  };
  if (map[field.name]) setOptional(out, map[field.name], field.value.trim());
  if (field.name === "output_sections") out.required_sections = splitLines(field.value);
  if (field.name === "output_allowed_paths") out.allowed_paths = splitLines(field.value);
  if (field.name === "output_max_bytes") setOptional(out, "max_bytes", maybeNumber(field.value));
  return true;
}

function updateNodeFromForm(form, changed) {
  let node = orchState.score.nodes.find((n) => n.id === orchState.selected);
  if (!node) return;
  if (updateOutputFromField(changed)) { orchState.jsonDraft = ""; queueOrchValidation(); return; }
  if (changed.name === "type" && changed.value !== node.type) {
    const replacement = defaultOrchNode(changed.value);
    replacement.id = node.id; replacement.needs = node.needs || []; replacement.resource_groups = node.resource_groups || [];
    orchState.score.nodes[orchState.score.nodes.indexOf(node)] = replacement;
    node = replacement; renderOrchestration(); queueOrchValidation(); return;
  }
  if (changed.name === "id") {
    const old = node.id; const next = changed.value.trim();
    node.id = next;
    orchState.score.nodes.forEach((n) => { n.needs = (n.needs || []).map((x) => x === old ? next : x); if (n.on_failure?.node === old) n.on_failure.node = next; });
    if (orchState.score.layout.nodes[old]) { orchState.score.layout.nodes[next] = orchState.score.layout.nodes[old]; delete orchState.score.layout.nodes[old]; }
    orchState.selected = next;
  }
  const direct = ["title", "description", "role", "profile", "prompt", "workspace", "action"];
  if (direct.includes(changed.name)) setOptional(node, changed.name, changed.value.trim());
  if (changed.name === "activation") node.activation = changed.value;
  node.needs = [...form.querySelectorAll('input[name="need"]:checked')].map((x) => x.value);
  if (changed.name === "resource_groups") node.resource_groups = splitLines(changed.value);
  if (changed.name === "timeout_seconds") setOptional(node, "timeout_seconds", maybeNumber(changed.value));
  if (node.type === "agent") {
    node.capabilities = [...form.querySelectorAll('input[name="capability"]:checked')].map((x) => x.value);
    if (changed.name === "context") node.context = splitLines(changed.value);
    if (changed.name === "inputs") node.inputs = parseInputLines(changed.value);
  }
  if (node.type === "collect" && changed.name === "inputs") node.inputs = parseInputLines(changed.value);
  if (node.type === "check") {
    node.runner ||= { kind: "command" };
    const r = node.runner;
    if (changed.name === "runner_kind") { node.runner = { kind: changed.value, timeout_seconds: r.timeout_seconds || 900, output_bytes: r.output_bytes || 30000 }; }
    else if (changed.name === "runner_argv") r.argv = splitLines(changed.value);
    else if (changed.name === "runner_cwd") setOptional(r, "cwd", changed.value.trim());
    else if (changed.name === "runner_name") setOptional(r, "name", changed.value);
    else if (changed.name === "runner_path") setOptional(r, "path", changed.value.trim());
    else if (changed.name === "runner_schema") setOptional(r, "schema", changed.value.trim());
    else if (changed.name === "runner_allowed_paths") r.allowed_paths = splitLines(changed.value);
    else if (changed.name === "runner_timeout") setOptional(r, "timeout_seconds", maybeNumber(changed.value));
    else if (changed.name === "runner_output_bytes") setOptional(r, "output_bytes", maybeNumber(changed.value));
    else if (changed.name === "runner_writes") r.writes = splitLines(changed.value);
    else if (changed.name === "expect_exit_code") node.expect = { exit_code: maybeNumber(changed.value) ?? 0 };
  }
  if (node.type === "approval") {
    if (changed.name === "options") node.options = splitLines(changed.value);
    if (changed.name === "terminal") setOptional(node, "terminal", changed.value);
  }
  if (node.type !== "approval") {
    const action = form.elements.failure_action?.value || "";
    if (!action) delete node.on_failure;
    else {
      const f = { action };
      if (action === "retry") f.max_attempts = maybeNumber(form.elements.failure_max_attempts.value);
      if (action === "route") { f.node = form.elements.failure_node.value; f.max_visits = maybeNumber(form.elements.failure_max_visits.value) || 1; }
      if (action === "approval") f.checkpoint = form.elements.failure_checkpoint.value.trim();
      node.on_failure = f;
    }
  }
  orchState.jsonDraft = ""; queueOrchValidation();
}

function updateScoreFromForm(form, changed) {
  const score = orchState.score;
  if (["slug", "title", "description", "project"].includes(changed.name)) setOptional(score, changed.name, changed.value.trim());
  score.defaults ||= {};
  const defaultNames = ["max_concurrency", "max_wall_seconds", "max_agent_starts", "max_check_starts", "default_timeout_seconds", "max_artifact_bytes"];
  if (defaultNames.includes(changed.name)) setOptional(score.defaults, changed.name, maybeNumber(changed.value));
  score.layout.viewport ||= {};
  if (changed.name.startsWith("viewport_")) score.layout.viewport[changed.name.replace("viewport_", "")] = Number(changed.value);
  if (changed.name === "slug") {
    orchState.name = changed.value.trim();
    orchState.exists = orchState.inventory.some((item) => item.name === orchState.name);
  }
  orchState.jsonDraft = ""; queueOrchValidation();
}

function wireOrchDesign() {
  const form = document.getElementById("orch-node-form");
  if (form) form.addEventListener("input", (e) => updateNodeFromForm(form, e.target));
  const scoreForm = document.getElementById("orch-score-form");
  if (scoreForm) scoreForm.addEventListener("input", (e) => updateScoreFromForm(scoreForm, e.target));
  document.querySelectorAll("[data-orch-add]").forEach((button) => button.addEventListener("click", () => {
    const node = defaultOrchNode(button.dataset.orchAdd); orchState.score.nodes.push(node);
    const count = orchState.score.nodes.length - 1; orchState.score.layout.nodes[node.id] = { x: 70 + (count % 4) * 240, y: 70 + Math.floor(count / 4) * 170 };
    orchState.selected = node.id; renderOrchestration(); queueOrchValidation();
  }));
  document.querySelector("[data-orch-settings]")?.addEventListener("click", () => { orchState.selected = null; renderOrchestration(); });
  document.querySelector("[data-orch-add-output]")?.addEventListener("click", () => {
    const node = orchState.score.nodes.find((n) => n.id === orchState.selected); node.outputs ||= [];
    node.outputs.push({ name: `${node.id}-output-${node.outputs.length + 1}`, format: "markdown", path: `artifacts/${node.id}-${node.outputs.length + 1}.md`, required_sections: [], citations: "none", max_bytes: 30000, allowed_paths: [] });
    renderOrchestration(); queueOrchValidation();
  });
  document.querySelectorAll("[data-orch-remove-output]").forEach((button) => button.addEventListener("click", () => {
    const node = orchState.score.nodes.find((n) => n.id === orchState.selected); node.outputs.splice(Number(button.dataset.orchRemoveOutput), 1); renderOrchestration(); queueOrchValidation();
  }));
  document.querySelector("[data-orch-delete-node]")?.addEventListener("click", () => {
    const id = orchState.selected; orchState.score.nodes = orchState.score.nodes.filter((n) => n.id !== id);
    orchState.score.nodes.forEach((n) => { n.needs = (n.needs || []).filter((x) => x !== id); if (n.on_failure?.node === id) delete n.on_failure; });
    delete orchState.score.layout.nodes[id]; orchState.selected = null; renderOrchestration(); queueOrchValidation();
  });
  document.querySelector("[data-orch-duplicate-node]")?.addEventListener("click", () => {
    const source = orchState.score.nodes.find((n) => n.id === orchState.selected); const copy = clone(source); copy.id = nextNodeId(source.type);
    (copy.outputs || []).forEach((out, i) => { out.name = `${copy.id}-output-${i + 1}`; });
    orchState.score.nodes.push(copy); const pos = orchState.score.layout.nodes[source.id] || { x: 0, y: 0 }; orchState.score.layout.nodes[copy.id] = { x: Number(pos.x) + 40, y: Number(pos.y) + 130 };
    orchState.selected = copy.id; renderOrchestration(); queueOrchValidation();
  });
  const svg = document.getElementById("orch-canvas");
  if (!svg) return;
  svg.querySelectorAll(".orch-node").forEach((group) => {
    group.addEventListener("click", () => { orchState.selected = group.dataset.nodeId; renderOrchestration(); });
    group.addEventListener("keydown", (e) => {
      if (["Enter", " "].includes(e.key)) { e.preventDefault(); orchState.selected = group.dataset.nodeId; renderOrchestration(); return; }
      const delta = { ArrowLeft: [-10, 0], ArrowRight: [10, 0], ArrowUp: [0, -10], ArrowDown: [0, 10] }[e.key];
      if (delta) { e.preventDefault(); const p = orchState.score.layout.nodes[group.dataset.nodeId]; p.x = Number(p.x) + delta[0]; p.y = Number(p.y) + delta[1]; renderOrchestration(); queueOrchValidation(); }
    });
  });
  let drag = null;
  svg.addEventListener("pointerdown", (e) => { const group = e.target.closest?.(".orch-node"); if (!group) return; const p = orchState.score.layout.nodes[group.dataset.nodeId]; drag = { id: group.dataset.nodeId, x: e.clientX, y: e.clientY, px: Number(p.x), py: Number(p.y), group }; svg.setPointerCapture(e.pointerId); });
  svg.addEventListener("pointermove", (e) => { if (!drag) return; const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width || 1; const p = orchState.score.layout.nodes[drag.id]; p.x = Math.max(0, Math.round(drag.px + (e.clientX - drag.x) / scale)); p.y = Math.max(0, Math.round(drag.py + (e.clientY - drag.y) / scale)); drag.group.setAttribute("transform", `translate(${p.x},${p.y})`); });
  svg.addEventListener("pointerup", () => { if (!drag) return; drag = null; renderOrchestration(); queueOrchValidation(); });
}

function renderSavePreview(preview, request) {
  const panel = document.getElementById("orch-save-panel");
  const diagnostics = preview.validation?.diagnostics || [];
  panel.innerHTML = `<section class="orch-save-preview" role="dialog" aria-modal="false" aria-labelledby="orch-preview-title" tabindex="-1"><div class="orch-preview-head"><strong id="orch-preview-title">${esc(preview.action)} preview</strong>${badge(preview.applicable ? "nothing written yet" : "compiler blocked apply", preview.applicable ? "ok" : "issue")}<code>${esc(preview.fingerprint)}</code></div>
    ${diagnostics.length ? `<ol class="orch-diagnostics">${diagnostics.map((d) => `<li><code>${esc(d.pointer)}</code><strong>${esc(d.code)}</strong><span>${esc(d.message)}</span><small>${esc(d.remediation)}</small></li>`).join("")}</ol>` : ""}
    ${preview.diff ? `<pre class="diff">${diffHtml(preview.diff)}</pre>` : `<p class="hint">${preview.no_op ? "No content change." : "No diff is available until the score compiles."}</p>`}
    <div class="orch-preview-actions">${preview.applicable ? `<button type="button" id="orch-apply-score">apply exact ${esc(preview.action)} — no run, stage, or commit</button>` : ""}<button type="button" id="orch-close-preview">close</button></div></section>`;
  const close = () => {
    panel.innerHTML = "";
    restoreReturnFocus("orch-save", "#orch-preview-save");
  };
  document.getElementById("orch-close-preview").addEventListener("click", close);
  document.getElementById("orch-apply-score")?.addEventListener("click", async (e) => {
    e.currentTarget.disabled = true;
    const { status, body } = await postJson("/api/orchestration/apply", { ...request, fingerprint: preview.fingerprint });
    if (status === 409) { panel.innerHTML = '<div class="guard">stale score preview refused — nothing was written. Preview the current score again.</div>'; return; }
    if (status >= 400 || body.ok === false) { panel.innerHTML = `<div class="guard">${esc((body.issues && body.issues[0]) || `apply failed (${status})`)}</div>`; return; }
    if (request.action === "delete") { location.hash = "#/orchestration"; await viewOrchestration(); return; }
    orchState.exists = true; orchState.name = request.name; location.hash = `#/orchestration/${encodeURIComponent(request.name)}`; await viewOrchestration(request.name);
  });
  enhanceSemantics(panel);
  wireDismissibleRegion(".orch-save-preview", close, "orch-save", "#orch-preview-save");
  focusRegion(".orch-save-preview");
}

async function previewScoreAction(action, trigger = document.activeElement) {
  rememberReturnFocus("orch-save", trigger);
  const request = action === "delete" ? { action, name: orchState.name } : { action, name: orchState.score.slug, score: orchState.score };
  const panel = document.getElementById("orch-save-panel"); panel.innerHTML = stateHtml(`Building exact ${action} preview…`);
  const { status, body } = await postJson("/api/orchestration/preview", request);
  if (status >= 400 || body.ok === false) { panel.innerHTML = `<div class="guard">${esc((body.issues && body.issues[0]) || `preview failed (${status})`)}</div>`; return; }
  renderSavePreview(body.data, request);
}

function wireJsonView() {
  const text = document.getElementById("orch-json-text");
  text?.addEventListener("input", () => { orchState.jsonDraft = text.value; });
  document.getElementById("orch-json-to-graph")?.addEventListener("click", async () => {
    const error = document.getElementById("orch-json-error");
    try { const parsed = JSON.parse(text.value); orchState.score = ensureOrchShape(parsed); orchState.name = parsed.slug || ""; orchState.selected = null; orchState.jsonDraft = ""; orchState.view = "design"; renderOrchestration(); await refreshOrchValidation(); }
    catch (err) { error.hidden = false; error.textContent = `JSON refused: ${err.message}`; }
  });
  document.getElementById("orch-import")?.addEventListener("change", async (e) => {
    const file = e.target.files[0]; if (!file) return; text.value = await file.text(); orchState.jsonDraft = text.value;
  });
}

function wireOrchPreflight() {
  document.getElementById("preflight-open-start")?.addEventListener("click", async () => {
    orchState.view = "run";
    orchState.runError = "";
    renderOrchestration();
    if (!orchState.runView) await refreshRunData();
  });
}

function wireOrchestration() {
  document.querySelectorAll("[data-orch-view]").forEach((button) => button.addEventListener("click", async () => {
    orchState.view = button.dataset.orchView; orchState.runError = ""; renderOrchestration();
    if (orchState.view === "run" && !orchState.runView) await refreshRunData();
  }));
  document.getElementById("orch-score-select")?.addEventListener("change", (e) => { location.hash = e.target.value ? `#/orchestration/${encodeURIComponent(e.target.value)}` : "#/orchestration"; });
  document.getElementById("orch-new")?.addEventListener("click", () => { orchState.score = minimalScore(); orchState.name = orchState.score.slug; orchState.exists = false; orchState.selected = null; orchState.preview = null; renderOrchestration(); queueOrchValidation(); });
  document.getElementById("orch-duplicate")?.addEventListener("click", () => { const used = new Set(orchState.inventory.map((s) => s.name)); let slug = `${orchState.score.slug}-copy`; let i = 2; while (used.has(slug)) slug = `${orchState.score.slug}-copy-${i++}`; orchState.score = clone(orchState.score); orchState.score.slug = slug; orchState.score.title = `${orchState.score.title} copy`; orchState.name = slug; orchState.exists = false; orchState.selected = null; renderOrchestration(); queueOrchValidation(); });
  document.getElementById("orch-preview-save")?.addEventListener("click", () => previewScoreAction("save"));
  document.getElementById("orch-preview-delete")?.addEventListener("click", () => previewScoreAction("delete"));
  if (orchState.view === "design") wireOrchDesign();
  if (orchState.view === "json") wireJsonView();
  if (orchState.view === "run") wireRunView();
  if (orchState.view === "validate") wireOrchPreflight();
  document.querySelectorAll(".orch-diagnostics [data-pointer], .orch-diagnostics li[data-pointer]").forEach((item) => item.addEventListener("click", () => { const match = item.dataset.pointer?.match(/^\/nodes\/(\d+)/); if (match && orchState.score.nodes[Number(match[1])]) { orchState.selected = orchState.score.nodes[Number(match[1])].id; orchState.view = "design"; renderOrchestration(); } }));
}

async function viewOrchestration(name) {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "orchestration" }, ...(name ? [{ label: name }] : [])]);
  const [inventoryBody, runInventoryBody] = await Promise.all([api("/api/orchestration"), api("/api/runs")]);
  orchState.inventory = inventoryBody.data.scores;
  orchState.runInventory = runInventoryBody.data.runs || [];
  if (name) {
    const body = await api(`/api/orchestration/${encodeURIComponent(name)}`);
    orchState.name = body.data.name; orchState.score = ensureOrchShape(clone(body.data.raw)); orchState.exists = true; orchState.preview = {
      valid: body.data.validation.valid, validation: body.data.validation,
      compiled: body.data.compiled, simulation: body.data.simulation,
    };
  } else if (orchState.inventory.length) {
    const first = orchState.inventory[0].name; const body = await api(`/api/orchestration/${encodeURIComponent(first)}`);
    orchState.name = body.data.name; orchState.score = ensureOrchShape(clone(body.data.raw)); orchState.exists = true; orchState.preview = { valid: body.data.validation.valid, validation: body.data.validation, compiled: body.data.compiled, simulation: body.data.simulation };
  } else {
    orchState.score = minimalScore(); orchState.name = orchState.score.slug; orchState.exists = false; orchState.preview = null;
  }
  orchState.selected = null; orchState.jsonDraft = "";
  orchState.runAct = null; orchState.runResult = null; orchState.runError = "";
  selectScoreRuns();
  const requestedView = new URLSearchParams(location.search).get("orchview");
  if (["design", "validate", "json", "run"].includes(requestedView)) orchState.view = requestedView;
  if (orchState.view === "run" && orchState.runId) {
    try {
      orchState.runView = (await api(`/api/runs/${encodeURIComponent(orchState.runId)}/view`)).data;
      orchState.runConnection.status = SNAPSHOT_LIVE_STATE === "stale" ? "stale" : SNAPSHOT_MODE ? "verified" : "checking";
      if (SNAPSHOT_MODE && SNAPSHOT_BOUNDED_PREVIEW) {
        const control = (orchState.runView.controls || []).find((item) => item.available && (
          SNAPSHOT_BOUNDED_PREVIEW === "decision"
            ? item.action === "request" && item.decision === "approve"
            : item.action === SNAPSHOT_BOUNDED_PREVIEW
        ));
        if (control) {
          orchState.controlReason = control.reason_required
            ? "Review this deterministic viewport action."
            : "";
          const response = await postJson("/api/runs/preview", {
            run_id: orchState.runId,
            action: control.action,
            ...(orchState.controlReason ? { reason: orchState.controlReason } : {}),
            ...(control.decision ? { decision: control.decision } : {}),
            ...(control.correlation_id ? { correlation_id: control.correlation_id } : {}),
          });
          if (response.status < 400 && response.body.ok !== false) {
            orchState.runAct = response.body.data;
          }
        }
      }
      if (SNAPSHOT_MODE && SNAPSHOT_BOUNDED_ERROR) {
        orchState.runError = SNAPSHOT_BOUNDED_ERROR === "stale"
          ? "Stale run action refused before work or saved event change. Reload once and review the current action."
          : "The action response ended without a confirmed receipt.";
      }
    }
    catch (err) { orchState.runError = err.message; orchState.runView = null; }
    startRunLive();
  }
  const consentSnapshot = SNAPSHOT_MODE ? new URLSearchParams(location.search).get("consentpreview") : "";
  if (orchState.view === "run" && !orchState.runId && consentSnapshot?.startsWith("run-")) {
    orchState.grantDraft = {
      project: orchState.score.project || "sample", story: "SMP-0-02",
      operator: "UI consent reviewer", minutes: consentSnapshot === "run-narrowed" ? 20 : 60,
    };
    if (consentSnapshot === "run-refusal") {
      orchState.runPlan = null;
      orchState.runError = "This start token is stale, reused, or does not match. Nothing started. Review a fresh permission preview.";
    } else {
      const issued = new Date();
      const expires = new Date(issued.getTime() + orchState.grantDraft.minutes * 60_000);
      const params = new URLSearchParams({
        score: orchState.score.slug, project: orchState.grantDraft.project,
        story: orchState.grantDraft.story, issued_at: issued.toISOString(),
        expires_at: expires.toISOString(),
      });
      try { orchState.runPlan = (await api(`/api/run-plan?${params}`)).data; }
      catch (err) { orchState.runError = err.message; }
    }
  }
  renderOrchestration();
  if (consentSnapshot?.startsWith("run-") && orchState.runPlan) focusConsentSnapshot(".run-consent");
  if (consentSnapshot === "run-refusal") focusConsentSnapshot(".run-error");
  focusBoundedSnapshot();
  await refreshOrchValidation();
  if (consentSnapshot?.startsWith("run-") && orchState.runPlan) focusConsentSnapshot(".run-consent");
  if (consentSnapshot === "run-refusal") focusConsentSnapshot(".run-error");
  focusBoundedSnapshot();
}
