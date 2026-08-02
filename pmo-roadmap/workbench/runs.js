"use strict";

function runStateBadge(state) {
  const cls = ["active", "succeeded", "complete"].includes(state) ? "ok"
    : ["failed", "blocked", "cancelled", "revoked"].includes(state) ? "issue"
      : ["awaiting-approval", "awaiting-certification", "paused"].includes(state) ? "warn" : "";
  return badge(state, cls);
}

function liveRunGraph(view) {
  const nodes = view.graph.nodes || [];
  const positions = view.graph.layout?.nodes || {};
  const maxX = Math.max(820, ...nodes.map((n) => Number(positions[n.id]?.x || 0) + 225));
  const maxY = Math.max(430, ...nodes.map((n) => Number(positions[n.id]?.y || 0) + 145));
  const edges = [];
  nodes.forEach((node) => {
    const target = positions[node.id] || { x: 0, y: 0 };
    (node.needs || []).forEach((need) => {
      const source = positions[need];
      if (source) edges.push(`<path class="orch-edge success" d="M ${Number(source.x) + 190} ${Number(source.y) + 48} C ${Number(source.x) + 220} ${Number(source.y) + 48}, ${Number(target.x) - 30} ${Number(target.y) + 48}, ${Number(target.x)} ${Number(target.y) + 48}" marker-end="url(#run-arrow)"></path>`);
    });
    if (node.on_failure?.action === "route" && positions[node.on_failure.node]) {
      const failure = positions[node.on_failure.node];
      edges.push(`<path class="orch-edge failure" d="M ${Number(target.x) + 95} ${Number(target.y) + 96} C ${Number(target.x) + 95} ${Number(target.y) + 130}, ${Number(failure.x) + 95} ${Number(failure.y) - 30}, ${Number(failure.x) + 95} ${Number(failure.y)}" marker-end="url(#run-fail-arrow)"></path>`);
    }
  });
  return `<div class="run-graph-wrap"><svg class="orch-canvas run-graph" viewBox="0 0 ${maxX} ${maxY}" role="img" aria-labelledby="run-graph-title">
    <title id="run-graph-title">Live orchestration graph. Nodes show authoritative replayed state and attempt.</title>
    <defs><marker id="run-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="arrow-success"></path></marker><marker id="run-fail-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="arrow-failure"></path></marker></defs>
    ${edges.join("")}
    ${nodes.map((node) => {
      const pos = positions[node.id] || { x: 0, y: 0 };
      return `<g class="orch-node run-node state-${esc(node.state)} type-${esc(node.type)}" transform="translate(${Number(pos.x)},${Number(pos.y)})" tabindex="0" role="group" aria-label="${esc(node.id)}, ${esc(node.state)}, attempt ${esc(node.attempt)}">
        <title>${esc(node.id)} — ${esc(node.state)} — attempt ${esc(node.attempt)}${node.blocked_reason ? ` — ${esc(node.blocked_reason)}` : ""}</title><rect width="190" height="96" rx="9"></rect>
        <circle class="port input" cx="0" cy="48" r="5"></circle><circle class="port output" cx="190" cy="48" r="5"></circle>
        <text class="node-type" x="14" y="20">${esc(node.type)} · attempt ${esc(node.attempt)}</text><text class="node-id" x="14" y="46">${esc(node.id)}</text><text class="node-detail" x="14" y="70">${esc(node.state)}</text>
        ${node.blocked_reason ? `<text class="run-node-reason" x="14" y="87">${esc(node.blocked_reason).slice(0, 28)}</text>` : ""}
      </g>`;
    }).join("")}
  </svg></div>`;
}

function runBudgetHtml(budgets) {
  return `<div class="run-budgets">${Object.entries(budgets || {}).map(([name, budget]) => {
    const used = Number(budget.used || 0); const limit = Number(budget.limit || 0);
    const percent = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0;
    return `<div class="run-budget"><span>${esc(name.replace(/^max_/, "").replaceAll("_", " "))}</span><strong>${esc(used)} / ${esc(limit)}</strong><div><i style="width:${percent}%"></i></div></div>`;
  }).join("")}</div>`;
}

function runArtifactHtml(view) {
  const actual = new Map((view.artifacts || []).map((item) => [item.name, item]));
  const declared = [];
  (view.graph.nodes || []).forEach((node) => (node.outputs || []).forEach((output) => declared.push({ ...output, producer: node.id })));
  return `<div class="tablewrap"><table class="run-table"><thead><tr><th>artifact</th><th>producer</th><th>format</th><th>lineage / conventions</th><th>receipt</th></tr></thead><tbody>${declared.map((item) => {
    const receipt = actual.get(item.name);
    const conventions = [item.citations === "required" ? "citations" : "", ...(item.required_sections || [])].filter(Boolean).join(" · ") || `${item.max_bytes || "?"} byte ceiling`;
    return `<tr><td><code>${esc(item.name)}</code></td><td>${esc(item.producer)}</td><td>${esc(item.format)}</td><td>${esc(conventions)}</td><td>${receipt ? `${badge("validated", "ok")} ${esc(receipt.bytes)} B · <code>${esc(receipt.sha256).slice(0, 24)}…</code>` : badge("declared · not produced", "warn")}</td></tr>`;
  }).join("") || '<tr><td colspan="5">No declared artifacts.</td></tr>'}</tbody></table></div>`;
}

function streamButtons(executor, session) {
  const id = session.session_id || session.execution_id;
  if (!id) return "";
  return ["stdout", "stderr"].map((stream) => Number(session[`${stream}_bytes`] || 0) > 0
    ? `<button type="button" data-run-stream="${stream}" data-executor="${executor}" data-execution-id="${esc(id)}">open ${stream} · ${esc(session[`${stream}_bytes`])} B</button>` : "").join("");
}

function runSessionsHtml(view) {
  const agents = view.sessions?.agents || [];
  const checks = view.sessions?.checks || [];
  return `<div class="run-session-columns"><section><h3>research / work agents ${badge(agents.length)}</h3>${agents.map((session) => `<article class="run-session"><div><strong>${esc(session.node_id)}</strong>${runStateBadge(session.state)}</div><small>${esc(session.profile)} · ${esc(session.adapter)} · attempt ${esc(session.attempt)}</small><code>${esc(session.session_id || "no session")}</code><p>${esc(session.reason)}</p><div class="run-stream-buttons">${streamButtons("agent", session)}</div></article>`).join("") || '<p class="hint">No agent session has crossed the driver boundary.</p>'}</section>
    <section><h3>fail checks ${badge(checks.length)}</h3>${checks.map((session) => `<article class="run-session"><div><strong>${esc(session.node_id)}</strong>${runStateBadge(session.state)}</div><small>${esc(session.runner_kind)} · attempt ${esc(session.attempt)} · exit ${esc(session.actual_exit_code ?? "—")}/${esc(session.expected_exit_code)}</small><code>${esc(session.runner_hash)}</code><p>${esc(session.reason)}${(session.changed_paths || []).length ? ` · changed: ${esc(session.changed_paths.join(", "))}` : ""}</p><div class="run-stream-buttons">${streamButtons("check", session)}</div></article>`).join("") || '<p class="hint">No check session has executed.</p>'}</section></div>`;
}

function runRoutesHtml(view) {
  return `<div class="run-route-grid"><section><h3>failure routes</h3>${(view.routes || []).map((route) => `<div class="run-route"><code>${esc(route.node_id)} #${esc(route.attempt)}</code><strong>${esc(route.action)}</strong><span>${esc(route.target)}${route.target_attempt ? ` #${esc(route.target_attempt)}` : ""}</span>${route.resolved ? badge(`resolved · ${route.outcome}`, "ok") : badge("open", "warn")}</div>`).join("") || '<p class="hint">No failure route has fired.</p>'}</section><section><h3>human checkpoints</h3>${(view.checkpoints || []).map((point) => `<div class="run-route"><code>${esc(point.checkpoint)}</code><strong>${esc(point.mode)}</strong><span>${esc(point.reason)}</span>${point.decision ? badge(point.decision, point.decision === "approve" ? "ok" : "issue") : badge("waiting", "warn")}</div>`).join("") || '<p class="hint">No checkpoint has been reached.</p>'}</section></div>`;
}

function runTimelineHtml(view) {
  return `<ol class="run-timeline">${(view.timeline || []).map((event) => `<li><div><strong>${esc(event.event)}</strong><time>${esc(event.ts)}</time>${badge(`#${event.seq}`)}</div><p>${Object.entries(event.detail || {}).map(([key, value]) => `<span><b>${esc(key)}</b> ${esc(value)}</span>`).join("")}</p><code>${esc(event.event_hash)}</code></li>`).join("")}</ol>`;
}

function runControlsHtml(view) {
  return `<section class="run-controls exact-control-audit"><div class="run-control-head"><div><span>exact control catalog</span><strong>Applicability copied from the current saved run</strong></div>${badge("inspection only", "ok")}</div>
    <div class="run-unavailable">${(view.controls || []).map((control, index) => `<div><strong>${esc(control.action)}${control.decision ? ` · ${esc(control.decision)}` : ""}</strong><span>${control.available ? "available through the ordinary action review above" : esc((control.issues || []).join("; ") || "not applicable in the current state")}</span><code>/controls/${esc(index)}</code></div>`).join("")}</div>
  </section>`;
}

function runActPreviewHtml(preview) {
  if (!preview) return "";
  return `<details class="bounded-exact-preview"><summary>Exact run preview</summary><div class="run-token"><span>state + intent token</span><code>${esc(preview.act_token)}</code></div><p>Observed <code>${esc(preview.state)}</code> at generation ${esc(preview.control_generation)} and ledger <code>${esc(preview.ledger_head)}</code>.</p>
    ${preview.action === "supervise" ? `<p><strong>Bound supervision:</strong> at most ${esc(preview.max_ticks)} steps and ${esc(preview.max_seconds)} seconds. It stops sooner at a checkpoint, terminal state, or no-progress result.</p>` : ""}${preview.correlation_id ? `<p><strong>bound request:</strong> <code>${esc(preview.correlation_id)}</code> · ${esc(preview.response_outcome)}</p>` : ""}${preview.reason ? `<p><strong>bound reason:</strong> ${esc(preview.reason)}</p>` : ""}${(preview.issues || []).map((issue) => `<p class="guard">${esc(issue)}</p>`).join("")}</details>`;
}

function runStreamHtml(stream) {
  if (!stream) return "";
  return `<section class="run-open-stream" role="dialog" aria-modal="false" aria-labelledby="run-stream-title" tabindex="-1"><div><strong id="run-stream-title">${esc(stream.executor)} · ${esc(stream.execution_id)} · ${esc(stream.stream)}</strong><button type="button" id="run-stream-close">close explicit stream</button></div><small>${esc(stream.included_bytes)} / ${esc(stream.bytes)} bytes · ${stream.truncated ? "truncated" : "complete"} · ${esc(stream.sha256)}</small><pre>${esc(stream.content)}</pre></section>`;
}

function runRequestsHtml(view) {
  const outstanding = view.outstanding_requests || [];
  const tree = view.decision_tree || { roots: [], nodes: [] };
  const nodes = new Map((tree.nodes || []).map((item) => [item.correlation_id, item]));
  const renderDecision = (id, depth = 0) => {
    const item = nodes.get(id); if (!item) return "";
    const preview = item.preview || {};
    return `<li style="--decision-depth:${depth}"><div><code>${esc(item.correlation_id)}</code>${badge(item.status, item.status === "approved" || item.status === "applied" ? "ok" : item.status === "pending" ? "warn" : "issue")}</div><strong>${esc(item.kind)} · ${esc(item.origin_node || item.origin)}</strong><small>opened at ledger #${esc(item.opened_seq)} · parent ${esc(item.parent_correlation_id || "root")}</small><details><summary>inspect exact decision preview</summary><dl>${Object.entries(preview).map(([key, value]) => `<div><dt>${esc(key)}</dt><dd><code>${esc(value)}</code></dd></div>`).join("")}</dl></details>${(item.children || []).length ? `<ol>${item.children.map((child) => renderDecision(child, depth + 1)).join("")}</ol>` : ""}</li>`;
  };
  return `<div class="run-request-grid"><section><h3>outstanding requests</h3>${outstanding.map((request) => `<article class="run-request"><div><code>${esc(request.correlation_id)}</code>${badge(`${esc(request.age_seconds)}s old`, "warn")}</div><strong>${esc(request.kind)} · ${esc(request.origin_node || request.origin)}</strong><span>${esc(request.schema_summary)}</span><small>opened #${esc(request.opened_seq)} · expires ${esc(request.expires_at)} · republished generations ${(request.republished_generations || []).map(esc).join(", ") || "none"}</small></article>`).join("") || '<p class="hint">No human decision is outstanding.</p>'}</section><section><h3>checkpoint lineage · inspect only</h3><ol class="run-decision-tree">${(tree.roots || []).map((id) => renderDecision(id)).join("")}</ol>${!tree.roots?.length ? '<p class="hint">No decision point has been recorded.</p>' : ""}</section></div>`;
}

const CONSENT_NEVER = [
  "Merge branches",
  "Force-push",
  "Release",
  "Deploy",
  "Run arbitrary commands",
  "Raise its own authority",
];

const PROGRAM_CAPABILITY_LABELS = {
  "program:select": "Choose work only from the planned roadmap scope",
  "agent:dispatch": "Start assigned work agents",
  "check:execute": "Run declared checks",
  "workspace:write": "Write only in assigned work areas",
  "verdict:issue": "Record review verdicts",
  "council:decide": "Use the planned decision group",
  "obligation:record": "Record follow-up obligations",
  "obligation:materialize": "Save approved obligation material",
  "obligation:disposition": "Close or defer recorded obligations",
  "nudge:deliver": "Deliver declared standing nudges",
  "notification:send": "Send declared notifications",
  "evidence:materialize": "Save evidence for the selected work",
  "knowledge:lesson-writeback": "Write reviewed delivery lessons",
  "integration:apply": "Apply a reviewed integration",
  "contract:generate": "Generate a delivery contract",
  "certification:objective": "Record objective certification",
  "certification:verdict": "Record a certification verdict",
  "git:commit": "Create a contract-bound commit",
  "git:push": "Push only to the exact destination shown here",
  "roadmap:story-start": "Start the selected roadmap story",
  "roadmap:story-complete": "Complete the selected roadmap story after proof",
  "roadmap:phase-advance": "Advance the planned phase after its gates pass",
};

const PROGRAM_MODE_RANK = { advisory: 0, checkpointed: 1, continuous: 2 };
const PROGRAM_MODE_LABELS = {
  advisory: "Advice only",
  checkpointed: "Pause at decisions",
  continuous: "Continue within limits",
};

function consentBudgetLabel(name) {
  const labels = {
    max_phases: "phases", max_stories: "stories", max_child_runs: "bounded runs",
    max_agent_starts: "agent starts", max_provider_starts: "provider starts",
    max_model_starts: "model starts", max_check_starts: "check starts",
    max_loop_rounds: "loop rounds", max_debate_rounds: "review rounds",
    max_councils: "decision groups", max_repairs_per_story: "repairs per story",
    max_verdicts: "verdicts", max_obligations: "follow-up obligations",
    max_integrations: "integrations", max_commits: "commits", max_pushes: "pushes",
    max_nudges: "nudges", max_artifact_bytes: "artifact bytes",
    max_wall_seconds: "wall-clock seconds", max_concurrency: "concurrent tasks",
  };
  return labels[name] || name.replace(/^max_/, "").replaceAll("_", " ");
}

function consentBudgetListHtml(budgets, compact = false) {
  const entries = Object.entries(budgets || {});
  const primary = new Set([
    "max_phases", "max_stories", "max_agent_starts", "max_check_starts",
    "max_commits", "max_pushes", "max_tokens", "max_observed_cost_microunits",
    "max_artifact_bytes", "max_wall_seconds",
  ]);
  const shown = compact ? entries.filter(([name]) => primary.has(name)) : entries;
  return `<ul class="consent-budget-list">${shown.map(([name, value]) => `<li><strong>${esc(value)}</strong> ${esc(consentBudgetLabel(name))}</li>`).join("")}${compact && shown.length < entries.length ? `<li><strong>+${esc(entries.length - shown.length)}</strong> other finite counters below</li>` : ""}</ul>`;
}

function programAllowedWorkSummary(capabilities) {
  const allowed = new Set(capabilities || []);
  const parts = [];
  if (allowed.has("program:select")) parts.push("Choose work only from the planned roadmap scope");
  if (allowed.has("agent:dispatch")) parts.push(allowed.has("workspace:write") ? "Assigned agents may work in their own areas" : "Assigned agents may inspect work");
  if (allowed.has("check:execute")) parts.push("Declared checks may run");
  if (allowed.has("verdict:issue") || allowed.has("certification:verdict")) parts.push("Independent review may record a verdict");
  if (allowed.has("evidence:materialize")) parts.push("Evidence may be saved");
  if (allowed.has("git:commit")) parts.push("A contract-bound commit is possible after its gates pass");
  if (allowed.has("git:push")) parts.push("A gated push is possible only to the destination shown here");
  if (allowed.has("roadmap:story-start") || allowed.has("roadmap:story-complete") || allowed.has("roadmap:phase-advance")) parts.push("Roadmap changes remain limited to the selected work and its gates");
  return parts.join(". ") || "No dispatch or mutation is allowed";
}

function consentNeverHtml() {
  return `<section class="consent-never"><strong>Never allowed</strong><ul>${CONSENT_NEVER.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></section>`;
}

function responseIssueText(body) {
  return (body?.issues || []).map((issue) => typeof issue === "object" ? issue.message || issue.code || "" : String(issue)).join(" ");
}

function startTokenWasRefused(status, body) {
  return status === 409 || /stale|reuse|used|mismatch|token|exact preview/i.test(responseIssueText(body));
}

function grantPreviewHtml(plan) {
  if (!plan) return "";
  const minutes = Number(orchState.grantDraft.minutes || 60);
  const narrowed = minutes < 60;
  const work = `${plan.story.id}: ${plan.story.title || "the selected story"}, following ${plan.score.title || "the reviewed score"}`;
  const stopCopy = "It stops when a finite budget is used, permission expires, a required decision blocks progress, the score finishes, or you pause, revoke, or cancel it.";
  return `<section class="run-consent ${plan.applicable ? "" : "refused"}" role="dialog" aria-modal="false" aria-labelledby="run-plan-title" tabindex="-1">
    <header class="consent-head"><div><span>Permission</span><h2 id="run-plan-title">Approve this bounded run</h2><p>This preview starts nothing. Opening the page and receiving live updates also start nothing.</p></div>${badge(plan.applicable ? "ready to approve" : "refused", plan.applicable ? "ok" : "issue")}</header>
    <section id="run-consent-summary" class="consent-summary" tabindex="-1">
      <div class="consent-fact-grid">
        <article><span>Allowed work</span><strong>${esc(work)}</strong><p>Only declared agent, check, and approval steps may run in their planned work areas.</p></article>
        <article><span>Spend ceiling</span>${consentBudgetListHtml(plan.authority.budgets)}</article>
        <article><span>Permission ends</span><strong>${esc(plan.request.expires_at)}</strong><p>${narrowed ? `You reduced the lifetime to ${esc(minutes)} minute${minutes === 1 ? "" : "s"}.` : "No limits were reduced. This preview keeps the planned permission."}</p></article>
        <article><span>What makes it stop</span><strong>Budget, expiry, decision, completion, or your stop action</strong><p>${stopCopy}</p></article>
        <article><span>Push destination</span><strong>Nowhere</strong><p>A bounded run has no push permission.</p></article>
        <article><span>Delivery is not automatic</span><strong>The browser adds no authority of its own</strong><p>Only a browser-confirmed program action may use pre-granted delivery permission.</p></article>
      </div>
      ${consentNeverHtml()}
    </section>
    ${(plan.issues || []).map((issue) => `<p class="guard consent-refusal">${esc(issue)} Review a fresh preview before trying again.</p>`).join("")}
    <details class="consent-technical"><summary>Technical details</summary><p>Exact capability names, repository binding, token, and full grant document.</p><div class="run-token"><span>single-use start token</span><code>${esc(plan.start_token)}</code></div><pre>${esc(JSON.stringify(plan, null, 2))}</pre><button type="button" data-consent-summary="run">Back to permission summary</button></details>
    <div class="run-consent-actions">${plan.applicable ? '<button type="button" id="run-start-confirm">Approve this permission</button>' : ""}<button type="button" id="run-plan-close">Return without starting</button></div>
  </section>`;
}

function runEmptyHtml() {
  const draft = orchState.grantDraft;
  const consentSnapshot = SNAPSHOT_MODE ? new URLSearchParams(location.search).get("consentpreview") : "";
  if (consentSnapshot?.startsWith("run-") && orchState.runPlan) {
    return `<div class="run-empty consent-snapshot-only">${grantPreviewHtml(orchState.runPlan)}</div>`;
  }
  return `<div class="run-empty"><section><span class="orch-eyebrow">permission before work</span><h2>No bounded run is active</h2><p>Review who may do the selected work and how long permission lasts. The delivery plan fixes allowed work and spend ceilings, so this panel cannot raise or replace them.</p>${badge("preview starts nothing", "ok")} ${badge("approval creates permission only", "warn")}</section>
    <form id="run-grant-form" class="run-grant-form"><label>project slug<input name="project" required value="${esc(draft.project || orchState.score.project || "")}"></label><label>in-progress story id<input name="story" required value="${esc(draft.story)}" placeholder="WLA-24-07"></label><label>accountable operator<input name="operator" required value="${esc(draft.operator)}" placeholder="person responsible for this permission"></label><label>permission lifetime, up to 60 minutes<input name="minutes" type="number" min="1" max="60" value="${esc(Math.min(60, Number(draft.minutes) || 60))}"></label><button type="submit">Preview permission</button></form>${grantPreviewHtml(orchState.runPlan)}</div>`;
}

function liveConnectionHtml(connection, recovery) {
  const state = connection?.status || "checking";
  if (state === "stale") {
    return `<div class="live-connection stale" role="group" aria-label="Live update status"><strong>Live updates interrupted</strong><p>This is the last verified view. Completed work remains recorded; “Check for updates” replays the saved history before showing anything newer. No work is declared lost or repeated.</p></div>`;
  }
  const copy = state === "live" ? "Live updates on"
    : state === "verified" ? "Saved history checked"
      : state === "reconnecting" ? "Reconnecting..."
        : state === "manual" ? "Check for updates manually"
          : "Checking for updates";
  return `<div class="live-connection ${esc(state)}" role="group" aria-label="Live update status">${badge(copy, state === "live" || state === "verified" ? "ok" : "")}<span>${esc(recovery?.summary || "The saved history was checked before this view was built.")}</span></div>`;
}

function liveStateBadge(progress) {
  const group = progress?.status?.group || "waiting";
  const cls = ["active", "complete"].includes(group) ? "ok"
    : ["blocked", "stopped"].includes(group) ? "issue"
      : ["review", "repair", "recovering", "waiting"].includes(group) ? "warn" : "";
  return badge(progress?.status?.label || group, cls);
}

function liveAnswerGrid(progress) {
  return `<section class="live-answers" aria-label="Delivery questions">${(progress.answers || []).map((item) => `<article data-answer="${esc(item.id)}" class="status-${esc(item.status)}"><span>${esc(item.question)}</span><p>${esc(item.answer)}</p></article>`).join("")}</section>`;
}

function liveProgressGroups(progress) {
  const model = progress.progress || {};
  const groups = model.groups || {};
  const items = Array.isArray(model.items) ? model.items : Object.entries(groups).flatMap(([status, values]) => (values || []).map((item) => ({ ...item, status })));
  const ordered = ["active", "review", "repair", "recovering", "blocked", "waiting", "complete"];
  return `<section class="live-panel live-scope"><div class="live-panel-head"><div><span>Scope and progress</span><strong>${esc(model.completed || 0)} of ${esc(model.known_total || 0)} declared work items complete</strong></div><b>${esc(model.percent || 0)}%</b></div>
    <div class="live-progress-meter" role="progressbar" aria-label="Delivery progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${esc(model.percent || 0)}" aria-valuetext="${esc(model.completed || 0)} of ${esc(model.known_total || 0)} work items complete"><i style="width:${Math.max(0, Math.min(100, Number(model.percent || 0)))}%"></i></div>
    <div class="live-work-groups">${ordered.map((status) => {
      const matching = items.filter((item) => item.status === status);
      if (!matching.length) return "";
      return `<section class="state-${esc(status)}"><h3>${esc(status)} <small>${esc(matching.length)}</small></h3><ul>${matching.map((item) => `<li><strong>${esc(item.title)}</strong>${item.summary ? `<span>${esc(item.summary)}</span>` : ""}</li>`).join("")}</ul></section>`;
    }).join("")}</div>
  </section>`;
}

function livePeopleHtml(progress) {
  const team = progress.team || {};
  const people = (title, items, empty) => `<section><h3>${esc(title)}</h3>${(items || []).map((item) => `<article><strong>${esc(item.name)}</strong><span>${esc(item.responsibility || item.assignment || "")}</span>${item.status ? badge(item.status, item.status === "active" ? "ok" : "") : ""}</article>`).join("") || `<p>${esc(empty)}</p>`}</section>`;
  return `<section class="live-panel live-team"><div class="live-panel-head"><div><span>Team and review</span><strong>Doing, checking, and deciding stay separate</strong></div></div><p>${esc(team.summary || "")}</p><div>${people("Doing the work", team.owners, "No work owner is assigned.")}${people("Independent review", team.reviewers, "No independent reviewer is assigned.")}${(team.decision_owners || []).length ? people("Decision owners", team.decision_owners, "") : ""}</div>${team.identity_note ? `<small>${esc(team.identity_note)}</small>` : ""}</section>`;
}

function liveReviewHtml(progress) {
  const review = progress.review || {};
  const sections = [
    ["Mechanical checks", review.mechanical],
    ["Agent judgment", review.agent_judgment],
    ["Dissent", review.dissent],
    ["Repair", review.repair],
    ["Final governed decisions", review.final_governed_decisions],
  ];
  return `<section class="live-panel live-review"><div class="live-panel-head"><div><span>Evidence and decisions</span><strong>Different kinds of proof are shown separately</strong></div></div><div>${sections.map(([title, items]) => `<section><h3>${esc(title)}</h3>${(items || []).map((item) => `<article><strong>${esc(item.title)}</strong>${badge(item.status || item.exact_state || "recorded", ["passed", "pass", "succeeded", "approved", "complete"].includes(String(item.status || item.exact_state)) ? "ok" : "")}</article>`).join("") || '<p>None recorded.</p>'}</section>`).join("")}</div></section>`;
}

function liveNextHtml(progress) {
  const next = progress.next_step || {};
  const blocker = progress.blocker || {};
  const decision = progress.decision || {};
  return `<section class="live-next state-${esc(next.kind || "wait")}"><div><span>What happens next?</span><h2>${esc(next.label || "Wait")}</h2><p>${esc(next.detail || "")}</p></div><div class="live-next-facts"><article class="${blocker.status === "blocked" ? "issue" : "clear"}"><span>Blocked</span><strong>${esc(blocker.status === "blocked" ? "Yes" : "No")}</strong><p>${esc(blocker.summary || "")}</p></article><article class="${decision.status === "needed" ? "warn" : "clear"}"><span>Decision needed</span><strong>${esc(decision.status === "needed" ? "Yes" : "No")}</strong><p>${esc(decision.summary || "")}</p></article></div><small>The next step is copied from the saved delivery state. This page does not choose another one.</small></section>`;
}

function liveLimitsHtml(progress) {
  const limits = progress.limits || {};
  const permission = limits.permission || {};
  const cost = limits.cost || {};
  const primaryCounts = (limits.counts || []).filter((item) => item.primary !== false);
  return `<section class="live-panel live-limits"><div class="live-panel-head"><div><span>Remaining permission and cost</span><strong>What this delivery may still use</strong></div></div><div class="live-limit-summary"><article><span>Change permission</span><strong>${esc(permission.status || "unknown")}</strong><p>${esc(permission.summary || "")}</p>${(permission.will_not_use || []).length ? `<small>Will not use: ${esc(permission.will_not_use.join(", "))}</small>` : ""}</article><article><span>Money cost</span><strong>${esc(cost.status || "unknown")}</strong><p>${esc(cost.summary || "")}</p></article></div><div class="live-limit-counts">${primaryCounts.map((item) => `<article class="${item.status === "none-left" ? "empty" : ""}"><span>${esc(item.label)}</span><strong>${esc(item.remaining)} ${esc(item.unit)} left</strong><small>${esc(item.used)} used of ${esc(item.limit)}</small></article>`).join("")}</div>${limits.expires_at ? `<p class="live-expiry">Permission ends ${esc(limits.expires_at)}.</p>` : ""}</section>`;
}

function boundedScopeText(scope) {
  if (!scope || typeof scope !== "object") return String(scope || "No scope is recorded.");
  return Object.entries(scope)
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .map(([key, value]) => `${key.replaceAll("_", " ")}: ${Array.isArray(value) ? value.join(", ") : typeof value === "object" ? JSON.stringify(value) : value}`)
    .join(" · ") || "No scope is recorded.";
}

function boundedMeasurementHtml(measurement) {
  const item = measurement || { state: "unknown", unit: "units" };
  if (item.state === "finite" || item.state === "zero") return `<strong>${esc(item.value)} ${esc(item.unit)}</strong><small>${esc(item.state)}</small>`;
  const label = item.state === "not-applicable" ? "Not applicable"
    : item.state === "unbounded" ? "Unbounded"
      : "Unknown";
  return `<strong>${label}</strong><small>${esc(item.state)}</small>`;
}

function boundedMeasurementText(measurement) {
  const item = measurement || { state: "unknown", unit: "units" };
  if (item.state === "finite" || item.state === "zero") return `${item.value} ${item.unit}`;
  return item.state === "not-applicable" ? "not applicable"
    : item.state === "unbounded" ? "unbounded" : "unknown";
}

function boundedUsageTable(model, all = false) {
  const items = (model?.usage?.items || []).filter((item) => all || item.primary !== false);
  return `<div class="tablewrap bounded-usage-table"><table><thead><tr><th>Measure</th><th>Limit</th><th>Estimate</th><th>Actual</th><th>Remaining</th></tr></thead><tbody>${items.map((item) => `<tr><td><strong>${esc(item.label)}</strong><small>${esc(item.category)}</small></td>${["limit", "estimate", "actual", "remaining"].map((kind) => `<td>${boundedMeasurementHtml(item.measurements?.[kind])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

function boundedPermissionHtml(model) {
  const permission = model?.permission || {};
  const allowed = permission.allowed_effects || [];
  const forbidden = permission.forbidden_effects || [];
  const current = permission.current_use || [];
  return `<section class="bounded-permission" data-bounded-section="limits"><div class="bounded-section-head"><div><span>Before any action</span><h3>Permission, scope, limits, and cost</h3></div>${badge(permission.status || "unknown", permission.status === "available" ? "ok" : "warn")}</div>
    <div class="bounded-permission-grid"><article><span>Allowed effects</span><p>${allowed.map((item) => badge(String(item).replace(/[_:.-]/g, " "), "ok")).join(" ") || "No change effect is currently available."}</p></article><article><span>Affected scope</span><p>${esc(boundedScopeText(permission.scope))}</p></article><article><span>Expiry and stops</span><p>${permission.expires_at ? `Permission ends ${esc(permission.expires_at)}.` : "No expiry value is recorded."}</p><ul>${(permission.stop_conditions || []).map((item) => `<li>${esc(item)}</li>`).join("")}</ul></article><article><span>Still forbidden</span><p>${forbidden.map((item) => badge(String(item).replace(/[_:.-]/g, " "), "issue")).join(" ") || "No explicit exclusion is recorded."}</p></article></div>
    <p class="bounded-current-use"><strong>Current consumption:</strong> ${current.slice(0, 8).map((item) => `${esc(item.label)} — ${esc(boundedMeasurementText(item.actual))} used, ${esc(boundedMeasurementText(item.remaining))} remaining`).join(" · ") || "No counted consumption is recorded."}</p>
    ${boundedUsageTable(model)}
    <details class="bounded-all-usage"><summary>Every limit and measurement</summary>${boundedUsageTable(model, true)}<p>${esc(model?.usage?.legend?.zero || "")} ${esc(model?.usage?.legend?.unbounded || "")} Unknown and not applicable remain separate.</p></details>
  </section>`;
}

function boundedInboxHtml(model) {
  const inbox = model?.inbox || [];
  return `<section class="bounded-inbox" data-bounded-section="failure"><div class="bounded-section-head"><div><span>Decision and blocker inbox</span><h3>${inbox.length ? `${esc(inbox.length)} item${inbox.length === 1 ? "" : "s"} need attention` : "Nothing needs a decision right now"}</h3></div>${badge(inbox.length ? "attention" : "clear", inbox.length ? "warn" : "ok")}</div>
    <div class="bounded-inbox-grid">${inbox.map((item) => `<article class="bounded-inbox-item kind-${esc(item.kind)}"><div><span>${esc(item.kind)}</span>${badge(item.status, item.kind === "refusal" ? "issue" : "warn")}</div><h4>${esc(item.affected_work)}</h4><dl><div><dt>Why it cannot proceed</dt><dd>${esc(item.why)}</dd></div><div><dt>Who or what resolves it</dt><dd>${esc(item.resolver)}</dd></div></dl><h5>Valid choices and what follows</h5><ul>${(item.valid_choices || []).map((choice) => `<li><strong>${esc(choice.label)}${choice.available ? "" : " — unavailable"}</strong><span>${esc(choice.effect)} ${esc(choice.after)}</span></li>`).join("") || "<li><strong>Inspect only</strong><span>No state-changing choice is currently valid; review exact evidence.</span></li>"}</ul><p><strong>If you do nothing:</strong> ${esc(item.after_no_choice)}</p>${item.explanation ? boundedFailureDetailsHtml(item.explanation, "Recorded refusal") : ""}<details><summary>Technical details</summary><code>${esc(item.technical_reference || "no exact reference")}</code></details></article>`).join("") || '<p class="hint">The saved state has no blocker, pending decision, or refusal.</p>'}</div>
  </section>`;
}

function boundedFailureDetailsHtml(explanation, label = "Action could not be completed") {
  const item = explanation || {};
  const effect = item.effect_answer === "no" || item.effect_may_have_occurred === false
    ? "No — this refusal records no effect."
    : item.effect_answer === "yes" || item.effect_may_have_occurred === true
      ? "Yes — inspect the saved receipt before another action."
      : "Unknown — reload the saved history before another action.";
  return `<section class="bounded-failure" role="alert"><h4>${esc(label)}</h4><dl><div><dt>What happened</dt><dd>${esc(item.what_happened || "The action was refused.")}</dd></div><div><dt>What stayed unchanged</dt><dd>${esc(item.what_stayed_unchanged || "The last verified delivery state remains visible.")}</dd></div><div><dt>Could an effect already have occurred?</dt><dd>${esc(effect)}</dd></div><div><dt>Safe next step</dt><dd>${esc(item.safe_next_step || "Reload the saved state before acting again.")}</dd></div></dl><details><summary>Technical details</summary><pre>${esc(JSON.stringify(item.technical_evidence || {}, null, 2))}</pre></details></section>`;
}

function boundedErrorHtml(message) {
  if (!message) return "";
  const refusedBeforeEffect = /before work|no event was appended|no decision was applied|no grant was created/i.test(message);
  return boundedFailureDetailsHtml({
    what_happened: message,
    what_stayed_unchanged: refusedBeforeEffect
      ? "No work or saved event changed at this refusal boundary."
      : "The last verified view remains visible; no alternative action was inferred.",
    effect_may_have_occurred: refusedBeforeEffect ? false : null,
    safe_next_step: "Reload the saved state, inspect the exact history, and preview only a currently available action.",
    technical_evidence: { message },
  });
}

function boundedActionMatch(model, preview, target) {
  if (!preview) return null;
  return (model?.actions || []).find((item) => item.action === preview.action
    && String(item.decision || "") === String(preview.decision || "")
    && String(item.correlation_id || "") === String(target === "program" ? preview.request_id || "" : preview.correlation_id || ""));
}

function boundedPreviewHtml(model, preview, target) {
  if (!preview) return "";
  const action = boundedActionMatch(model, preview, target);
  const consequences = action?.consequences || {};
  const applicable = Boolean(preview.applicable);
  const exact = target === "run" ? runActPreviewHtml(preview) : `<details class="bounded-exact-preview"><summary>Technical details</summary><div class="run-token"><span>state + ledger + parameter token</span><code>${esc(preview.act_token)}</code></div><p>Observed <code>${esc(preview.state)}</code> at generation ${esc(preview.generation)} and ledger <code>${esc(preview.ledger_head)}</code>.</p><p><strong>lane:</strong> ${esc(preview.operation?.lane || "—")} · <strong>next:</strong> ${esc(programScalar(preview.operation?.next_action))}</p>${preview.action === "supervise" ? `<p><strong>Bound supervision:</strong> at most ${esc(preview.max_ticks)} steps and ${esc(preview.max_seconds)} seconds. It stops sooner at a checkpoint, terminal state, or no-progress result.</p>` : ""}${(preview.issues || []).map((issue) => `<p class="guard">${esc(issue)}</p>`).join("")}</details>`;
  const refusal = applicable ? "" : boundedFailureDetailsHtml({
    what_happened: (preview.issues || []).join("; ") || "The current saved state refused this preview.",
    what_stayed_unchanged: "Previewing changed no work, permission, cost, or saved event.",
    effect_may_have_occurred: false,
    safe_next_step: "Close this preview and choose only a currently available action.",
    technical_evidence: { action: preview.action, issues: preview.issues || [] },
  }, "Preview refused");
  const titleId = `${target}-act-preview-title`;
  return `<section class="bounded-preview ${applicable ? "" : "refused"}" role="dialog" aria-modal="false" aria-labelledby="${titleId}" tabindex="-1"><div class="bounded-section-head"><div><span>Review before confirmation</span><h3 id="${titleId}">${esc(action?.label || preview.action)}</h3></div>${badge(preview.starts_work ? "may start bounded work" : "one saved action", preview.starts_work ? "warn" : "ok")}</div><dl class="bounded-consequence"><div><dt>What this will do</dt><dd>${esc(consequences.effect || "Apply only this exact reviewed operation.")}</dd></div><div><dt>What it will not do</dt><dd>${esc(consequences.unchanged || "It will not broaden permission or select a different action.")}</dd></div><div><dt>What follows</dt><dd>${esc(consequences.after || "The saved state and receipt will be reloaded.")}</dd></div></dl>${refusal}${exact}<div class="run-consent-actions">${applicable ? `<button type="button" id="${target === "run" ? "run" : "program"}-act-confirm" class="${action?.severity === "danger" ? "danger" : action?.may_start_work ? "starts-work" : ""}">Confirm ${esc(String(action?.label || preview.action).toLowerCase())}</button>` : ""}<button type="button" id="${target === "run" ? "run" : "program"}-act-close">Return without applying</button></div></section>`;
}

function boundedReceiptsHtml(model, result) {
  const receipts = model?.receipts || [];
  const resultHtml = result ? `<article class="bounded-result"><div><span>Just completed</span>${badge("recorded", "ok")}</div><h4>${esc(result.kind || "Bounded action completed")}</h4><p>${esc(result.stop || result.state || result.result || result.decision || "The saved operation completed.")}</p><details><summary>Technical details</summary><pre>${esc(JSON.stringify(result, null, 2))}</pre></details></article>` : "";
  return `<section class="bounded-receipts"><div class="bounded-section-head"><div><span>After completion</span><h3>Readable results</h3></div>${badge(`${receipts.length + (result ? 1 : 0)} shown`, "ok")}</div><div class="bounded-receipt-grid">${resultHtml}${receipts.map((item) => `<article><div><span>${esc(item.action)}</span>${badge(item.outcome || "recorded", "ok")}</div><h4>${esc(item.label)}</h4><p>${esc(item.at || "time recorded in exact history")}</p><details><summary>Technical details</summary><code>${esc(item.exact_reference || "see ordered history")}</code></details></article>`).join("") || (!result ? '<p class="hint">No bounded action result has been recorded yet.</p>' : "")}</div></section>`;
}

function boundedActionButtonsHtml(model, target) {
  const actions = model?.actions || [];
  const read = actions.filter((item) => item.kind === "read");
  const controls = actions.filter((item) => item.kind !== "read");
  const controlButton = (item) => {
    const attrs = target === "run"
      ? `data-run-act="${esc(item.action)}" data-run-decision="${esc(item.decision || "")}" data-run-correlation="${esc(item.correlation_id || "")}"`
      : `data-program-act="${esc(item.action)}" data-program-decision="${esc(item.decision || "")}" data-program-request="${esc(item.correlation_id || "")}"`;
    return `<article class="bounded-action-card severity-${esc(item.severity)} action-${esc(item.action)} ${item.available ? "" : "unavailable"}" data-control-action="${esc(item.action)}"><div><span>${esc(item.kind)}</span>${badge(item.available ? "available" : "unavailable", item.available ? "ok" : "warn")}</div><h4><span class="control-icon" aria-hidden="true"></span>${esc(item.label)}</h4><p>${esc(item.consequences?.effect)}</p><small><strong>Then:</strong> ${esc(item.consequences?.after)}</small>${item.available ? `<button type="button" ${attrs} class="${item.severity === "danger" ? "danger" : item.may_start_work ? "starts-work" : ""}">Review ${esc(item.label.toLowerCase())}</button>` : `<p class="bounded-action-issue"><strong>Unavailable now.</strong> ${esc(item.issue)}</p>`}</article>`;
  };
  return `<div class="bounded-read-actions">${read.map((item) => `<button type="button" data-bounded-read="${esc(item.read_action)}"><strong>${esc(item.label)}</strong><span>${esc(item.consequences?.effect)}</span></button>`).join("")}</div><div class="bounded-action-grid">${controls.map(controlButton).join("")}</div>`;
}

function boundedActionCenterHtml(model, preview, error, result, target) {
  if (!model) return "";
  const available = (model.actions || []).filter((item) => item.available);
  const needsReason = available.some((item) => item.reason_required);
  const hasSupervise = available.some((item) => item.action === "supervise");
  const reason = target === "run" ? orchState.controlReason : programState.reason;
  return `<section class="bounded-action-center" aria-labelledby="${esc(target)}-bounded-actions"><div class="bounded-action-hero"><div><span>Actions and decisions</span><h2 id="${esc(target)}-bounded-actions">Understand the consequence, then review one exact action</h2><p>${esc(model.summary)}</p></div>${badge("nothing applies without confirmation", "warn")}</div>
    ${boundedInboxHtml(model)}
    ${boundedPermissionHtml(model)}
    <section class="bounded-choices"><div class="bounded-section-head"><div><span>Available choices</span><h3>Pause, resume, stop, cancel, reject, and continue stay distinct</h3></div></div>${needsReason ? `<label class="run-reason">Why are you taking this action?<input id="${target === "run" ? "run" : "program"}-control-reason" maxlength="${target === "run" ? "200" : "1000"}" value="${esc(reason)}" placeholder="Required for stop and decision actions"></label>` : ""}${hasSupervise ? `<div class="program-ceilings"><label>maximum steps in this pass<input id="${target}-max-ticks" type="number" min="1" max="10000" value="${esc(target === "run" ? orchState.maxTicks : programState.maxTicks)}"></label><label>maximum duration (seconds)<input id="${target}-max-seconds" type="number" min="1" max="86400" value="${esc(target === "run" ? orchState.maxSeconds : programState.maxSeconds)}"></label><p>Supervision stops at these finite ceilings, a checkpoint, a terminal state, or the first no-progress result.</p></div>` : ""}${boundedActionButtonsHtml(model, target)}</section>
    ${boundedErrorHtml(error)}
    ${boundedPreviewHtml(model, preview, target)}
    ${boundedReceiptsHtml(model, result)}
  </section>`;
}

function liveActivityHtml(progress) {
  const activity = progress.activity || [];
  return `<section class="live-panel live-activity"><div class="live-panel-head"><div><span>Readable activity</span><strong>Related work and outcomes grouped together</strong></div>${badge(`${activity.length} groups`)}</div><ol>${activity.map((item) => `<li class="state-${esc(item.status)}"><div><strong>${esc(item.title)}</strong>${badge(item.status, ["active", "complete"].includes(item.status) ? "ok" : ["blocked"].includes(item.status) ? "issue" : "warn")}</div><p>${esc(item.summary || "")}</p>${(item.outcomes || []).length ? `<small>Outcomes: ${esc(item.outcomes.join(", "))}</small>` : ""}</li>`).join("") || "<li><p>No delivery activity has been recorded yet.</p></li>"}</ol></section>`;
}

function liveProgressShell(
  progress,
  connection,
  toolbar,
  actionHtml,
  technicalHtml,
  technicalOpen = false,
  headingLevel = "h2",
) {
  const heading = headingLevel === "h1" ? "h1" : "h2";
  const ordinary = `<section class="live-state-summary state-${esc(progress.status?.group)}"><div><span>Delivery state</span><strong>${esc(progress.status?.label)}</strong><p>${esc(progress.status?.meaning)}</p></div><div><span>Current scope</span><strong>${esc(progress.delivery?.scope || "")}</strong><p>${esc(progress.delivery?.current_story || progress.delivery?.work_id || "")}</p></div></section>
    ${liveAnswerGrid(progress)}
    ${liveNextHtml(progress)}
    ${actionHtml}
    ${liveProgressGroups(progress)}
    <div class="live-two-column">${livePeopleHtml(progress)}${liveReviewHtml(progress)}</div>
    ${liveLimitsHtml(progress)}
    ${liveActivityHtml(progress)}
    <section class="live-recovery state-${esc(progress.recovery?.status)}"><div><span>Recovery truth</span><strong>${esc(progress.recovery?.status === "recovering" ? "Reconciliation in progress" : "Saved history verified")}</strong></div><p>${esc(progress.recovery?.summary || "")}</p><small>${esc(progress.recovery?.duplicate_protection || "")}</small></section>`;
  const technical = `<details class="live-technical"${technicalOpen || LIVE_TECHNICAL_OPEN ? " open" : ""}><summary>Technical details</summary><p class="live-technical-intro">Exact identities, ordered history, hashes, controls, and provenance remain available here.</p>${technicalHtml}</details>`;
  return `<div class="live-delivery" data-live-context="${esc(progress.context)}">
    <header class="live-header"><div><span class="orch-eyebrow">Live delivery</span><${heading}>${esc(progress.title)} ${liveStateBadge(progress)}</${heading}><p>${esc(progress.subtitle)}</p></div>${toolbar}</header>
    ${liveConnectionHtml(connection, progress.recovery)}
    ${LIVE_TECHNICAL_OPEN ? `${technical}${ordinary}` : `${ordinary}${technical}`}
  </div>`;
}

function openLiveTechnical() {
  const details = document.querySelector(".live-technical");
  if (!details) return;
  details.open = true;
  details.scrollIntoView({
    behavior: SNAPSHOT_MODE || matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto" : "smooth",
    block: "start",
  });
  focusElement(details.querySelector("summary"));
}

async function handleBoundedRead(action, target) {
  if (action === "reload") {
    if (target === "run") await refreshRunData();
    else await refreshProgramView();
    return;
  }
  if (action === "technical") {
    openLiveTechnical();
    return;
  }
  if (action === "leave") {
    if (target === "run") {
      orchState.runAct = null; orchState.runError = "";
      renderOrchestration();
    } else {
      programState.act = null; programState.error = "";
      renderPrograms();
    }
    return;
  }
  const selector = action === "limits"
    ? '[data-bounded-section="limits"]'
    : '[data-bounded-section="failure"]';
  const section = document.querySelector(selector);
  section?.scrollIntoView({
    behavior: SNAPSHOT_MODE || matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto" : "smooth",
    block: "start",
  });
  section?.querySelector("h3, h4")?.setAttribute("tabindex", "-1");
  focusElement(section?.querySelector("h3, h4"));
}

function focusBoundedSnapshot() {
  if (!SNAPSHOT_MODE || !SNAPSHOT_BOUNDED_FOCUS) return;
  const selectors = {
    actions: ".bounded-action-center",
    inbox: ".bounded-inbox",
    limits: ".bounded-permission",
    preview: ".bounded-preview",
    error: ".bounded-failure",
    receipts: ".bounded-receipts",
  };
  const focus = () => {
    const target = document.querySelector(
      selectors[SNAPSHOT_BOUNDED_FOCUS] || ".bounded-action-center"
    );
    if (!target) return;
    const center = target.closest(".bounded-action-center");
    const live = center?.closest(".live-delivery");
    const hero = center?.querySelector(".bounded-action-hero");
    if (center && target !== center && hero) hero.after(target);
    const header = live?.querySelector(".live-header");
    if (center && header) header.after(center);
    window.scrollTo({ top: 0, behavior: "auto" });
  };
  focus();
}

function liveDetailRoute() {
  const parts = decodeURIComponent(location.hash.replace(/^#\/?/, "")).split("/").filter(Boolean);
  if (parts[0] !== "live" || !["run", "program"].includes(parts[1]) || !parts[2]) return null;
  return { kind: parts[1], id: parts[2], section: parts[3] || "" };
}

function runViewHtml() {
  if (orchState.runLoading) return `<div class="orch-run-shell">${stateHtml("Replaying the authoritative run ledger…")}</div>`;
  const error = orchState.runError ? `<div class="guard run-error" role="alert">${esc(orchState.runError)}</div>` : "";
  if (!orchState.runs.length || !orchState.runView) return `<div class="orch-run-shell">${error}${runEmptyHtml()}</div>`;
  const view = orchState.runView;
  const actions = boundedActionCenterHtml(view.bounded_actions, orchState.runAct, orchState.runError, orchState.runResult, "run");
  const liveRoute = liveDetailRoute();
  const toolbar = liveRoute?.kind === "run"
    ? `<div class="live-toolbar"><a href="#/live">Back to all live work</a><button type="button" id="run-refresh">Check for updates</button><button type="button" data-memory-open="run:${esc(view.run_id)}" data-memory-kind="run" data-memory-id="${esc(view.run_id)}">Memory</button><a href="#/live/run/${encodeURIComponent(view.run_id)}/technical">Technical details</a></div>`
    : `<div class="live-toolbar"><label>delivery run<select id="run-select">${orchState.runs.map((item) => `<option value="${esc(item.run_id)}"${item.run_id === view.run_id ? " selected" : ""}>${esc(item.run.story?.id || item.run_id)} · ${esc(item.run.state)}</option>`).join("")}</select></label><button type="button" id="run-refresh">Check for updates</button><button type="button" data-memory-open="run:${esc(view.run_id)}" data-memory-kind="run" data-memory-id="${esc(view.run_id)}">Memory</button><button type="button" data-live-technical>Technical details</button></div>`;
  const technical = `${liveRoute?.kind === "run" ? `<p class="live-technical-return"><a href="#/live/run/${encodeURIComponent(view.run_id)}">Return to the ordinary view</a></p>` : ""}<div class="run-summary"><div><span>exact state</span><strong>${esc(view.state)}</strong><small>${esc(view.terminal_meaning)}</small></div><div><span>ledger</span><strong>${esc(view.ledger_events)} events</strong><code>${esc(view.ledger_head)}</code></div><div><span>attempts</span><strong>${esc(view.attempts.active.length)} active · ${esc(view.attempts.completed.length)} complete</strong><small>generation ${esc(view.control_generation)}</small></div><div><span>authority</span><strong>${view.dispatch_allowed ? "dispatch permitted" : "dispatch stopped"}</strong><small>${view.expired ? "grant expired" : "grant fresh by time"}</small></div></div>
    ${runBudgetHtml(view.budgets)}
    <section class="run-panel"><div class="run-panel-head"><div><span>authoritative graph state</span><strong>Why every node is waiting, eligible, active, failed, or complete</strong></div>${badge("inspection is pure", "ok")}</div>${liveRunGraph(view)}</section>
    <section class="run-panel"><div class="run-panel-head"><div><span>executors and fail checks</span><strong>Sessions expose receipts and bounded streams, never prompts or commands</strong></div></div>${runSessionsHtml(view)}${runStreamHtml(orchState.runStream)}</section>
    <section class="run-panel"><div class="run-panel-head"><div><span>declared output conventions</span><strong>Artifact metadata and lineage</strong></div></div>${runArtifactHtml(view)}</section>
    <section class="run-panel"><div class="run-panel-head"><div><span>typed human request ports</span><strong>Outstanding requests, age, origin, schemas, and checkpoint lineage</strong></div>${badge("inspect-only history", "ok")}</div>${runRequestsHtml(view)}</section>
    <section class="run-panel">${runRoutesHtml(view)}</section>
    ${runControlsHtml(view)}
    <section class="run-panel"><div class="run-panel-head"><div><span>operator notifications</span><strong>Derived from the ledger and signal chains; ack is receipted</strong></div>${badge("previews, never tokens", "ok")}</div>${runNotificationsHtml(view)}</section>
    <section class="run-panel"><div class="run-panel-head"><div><span>hash-chained receipts</span><strong>Run ledger timeline</strong></div>${badge("content-safe metadata", "ok")}</div>${runTimelineHtml(view)}</section>`;
  return `<div class="orch-run-shell" data-run-id="${esc(view.run_id)}">${liveProgressShell(view.live_progress, orchState.runConnection, toolbar, actions, technical, Boolean(orchState.runStream) || ["technical", "notifications"].includes(liveRoute?.section), liveRoute?.kind === "run" ? "h1" : "h2")}</div>`;
}

function runNotificationsHtml(view) {
  const items = (orchState.notifications || []).filter(
    (item) => !item.run_id || item.run_id === view.run_id,
  );
  if (!items.length) return `<p class="orch-muted">No derived notifications for this run.</p>`;
  return `<ul class="run-notifications">${items.map((item) => `
    <li>
      <code>${esc(item.kind)}</code> ${item.unread ? badge("unread", "warn") : badge("acked", "ok")}
      ${item.delivered ? badge("delivered", "ok") : badge(`attempts ${esc(item.delivery_attempts)}`, "")}
      <span>${esc(item.detail)}</span>
      ${item.request ? `<small>typed response · correlation <code>${esc(item.request.correlation_id)}</code> · applied only through the local exact-token request boundary</small>` : ""}
      ${item.unread ? `<button type="button" data-ntf-ack="${esc(item.id)}">ack</button>` : ""}
    </li>`).join("")}</ul>`;
}

async function ackNotification(id) {
  const { status, body } = await postJson("/api/notifications/ack", { id });
  if (status === 200) {
    try { orchState.notifications = (await api("/api/notifications")).data.notifications; } catch (err) {}
    renderOrchestration();
  }
}


function selectScoreRuns() {
  const slug = orchState.score?.slug;
  orchState.runs = (orchState.runInventory || []).filter((item) => item.valid && item.run?.score?.slug === slug);
  if (!orchState.runs.some((item) => item.run_id === orchState.runId)) {
    orchState.runId = orchState.runs.length ? orchState.runs[orchState.runs.length - 1].run_id : "";
    orchState.runView = null;
  }
}

async function refreshRunData() {
  const previousView = orchState.runView;
  const focus = captureAppFocus();
  orchState.runLoading = true;
  orchState.runError = "";
  orchState.runConnection.status = "checking";
  if (!previousView) renderOrchestration();
  try {
    const inventory = await api("/api/runs");
    orchState.runInventory = inventory.data.runs || [];
    if (liveDetailRoute()?.kind === "run") orchState.runs = orchState.runInventory.filter((item) => item.valid !== false);
    else selectScoreRuns();
    orchState.runView = orchState.runId ? (await api(`/api/runs/${encodeURIComponent(orchState.runId)}/view`)).data : null;
    orchState.runConnection.status = SNAPSHOT_LIVE_STATE === "stale" ? "stale" : SNAPSHOT_MODE ? "verified" : "checking";
    try { orchState.notifications = (await api("/api/notifications")).data.notifications; }
    catch (err) { orchState.notifications = []; }
  } catch (err) {
    orchState.runError = err.message;
    orchState.runView = previousView;
    orchState.runConnection.status = previousView ? "stale" : "manual";
  } finally {
    orchState.runLoading = false;
    renderOrchestration();
    restoreAppFocus(focus);
  }
  const version = String(orchState.runView?.ledger_head || "");
  if (liveAnnouncementKeys.has("run")) {
    announceLiveUpdate(
      "run",
      version,
      "Delivery progress changed. Review What happens next or check the saved history.",
    );
  } else if (version) {
    liveAnnouncementKeys.set("run", version);
  }
  startRunLive();
}

/* Live ledger tail (SSE, read-only). Any arriving ledger event triggers
   one debounced re-read of the same run-view read model; if the stream
   is unavailable the explicit refresh button remains the fallback. */
let runLive = null;
let runLiveTimer = null;

function stopRunLive() {
  if (runLive) { runLive.close(); runLive = null; }
  if (runLiveTimer) { clearTimeout(runLiveTimer); runLiveTimer = null; }
}

let runLiveHadConnection = false;

function startRunLive() {
  stopRunLive();
  runLiveHadConnection = false;
  if (!orchState.runId || orchState.view !== "run") return;
  if (SNAPSHOT_MODE || typeof EventSource === "undefined") {
    if (SNAPSHOT_LIVE_STATE !== "stale") orchState.runConnection.status = SNAPSHOT_MODE ? "verified" : "manual";
    renderPreservingAppFocus(renderOrchestration);
    return;
  }
  const runId = orchState.runId;
  runLive = new EventSource(`/api/runs/${encodeURIComponent(runId)}/events`);
  runLive.onopen = () => {
    if (orchState.runId !== runId || orchState.view !== "run") return;
    if (runLiveHadConnection) {
      // Reconnect: show catching-up until snapshot arrives
      orchState.runConnection.status = "reconnecting";
      showRunCatchingUp(true);
    } else {
      orchState.runConnection.status = "live";
    }
    runLiveHadConnection = true;
    renderPreservingAppFocus(renderOrchestration);
  };
  // Snapshot-then-tail (WLA-34-05): the server sends a snapshot on
  // every connect.  On reconnect the snapshot lets us verify we are
  // current before re-entering the "live" state.
  runLive.addEventListener("snapshot", async () => {
    if (orchState.runId !== runId || orchState.view !== "run") return;
    try {
      orchState.runView = (await api(`/api/runs/${encodeURIComponent(runId)}/view`)).data;
      orchState.runConnection.status = "live";
      try { orchState.notifications = (await api("/api/notifications")).data.notifications; }
      catch (_err) { /* notifications stay stale until the next refresh */ }
      renderPreservingAppFocus(renderOrchestration);
    } catch (_err) { /* view stays as-is */ }
    showRunCatchingUp(false);
  });
  runLive.addEventListener("ledger", () => {
    if (runLiveTimer) return;
    runLiveTimer = setTimeout(async () => {
      runLiveTimer = null;
      if (orchState.runId !== runId || orchState.view !== "run") return;
      try {
        orchState.runView = (await api(`/api/runs/${encodeURIComponent(runId)}/view`)).data;
        orchState.runConnection.status = "live";
        try { orchState.notifications = (await api("/api/notifications")).data.notifications; }
        catch (err) { /* notifications stay stale until the next refresh */ }
        announceLiveUpdate(
          "run",
          orchState.runView?.ledger_head,
          "Delivery progress changed. Review What happens next or check the saved history.",
        );
        renderPreservingAppFocus(renderOrchestration);
      } catch (err) {
        orchState.runConnection.status = "stale";
        announceLiveUpdate(
          "run-connection",
          `stale:${runId}:${orchState.runView?.ledger_head || ""}`,
          "Live delivery updates were interrupted. The last verified view remains available.",
        );
        renderPreservingAppFocus(renderOrchestration);
      }
    }, 400);
  });
  runLive.onerror = () => {
    orchState.runConnection.status = "stale";
    stopRunLive();
    showRunCatchingUp(false);
    announceLiveUpdate(
      "run-connection",
      `stale:${runId}:${orchState.runView?.ledger_head || ""}`,
      "Live delivery updates were interrupted. The last verified view remains available.",
    );
    renderPreservingAppFocus(renderOrchestration);
  };
}

function showRunCatchingUp(show) {
  const existing = document.querySelector(".orch-run-shell > .dw-catching-up");
  if (show) {
    if (!existing) {
      const shell = document.querySelector(".orch-run-shell");
      if (shell) {
        const banner = document.createElement("div");
        banner.className = "dw-catching-up";
        banner.setAttribute("role", "status");
        banner.setAttribute("aria-live", "polite");
        banner.textContent = "Catching up...";
        shell.prepend(banner);
      }
    }
  } else if (existing) {
    existing.remove();
  }
}

async function previewRunGrant(form) {
  rememberReturnFocus("run-plan");
  const values = Object.fromEntries(new FormData(form).entries());
  const minutes = Math.max(1, Math.min(60, Number(values.minutes) || 60));
  orchState.grantDraft = { project: String(values.project || "").trim(), story: String(values.story || "").trim(), operator: String(values.operator || "").trim(), minutes };
  orchState.runError = ""; orchState.runPlan = null; renderOrchestration();
  const issued = new Date(); const expires = new Date(issued.getTime() + minutes * 60_000);
  const params = new URLSearchParams({ score: orchState.score.slug, project: orchState.grantDraft.project, story: orchState.grantDraft.story, issued_at: issued.toISOString(), expires_at: expires.toISOString() });
  try { orchState.runPlan = (await api(`/api/run-plan?${params}`)).data; }
  catch (err) { orchState.runError = err.message; }
  renderOrchestration();
  if (orchState.runPlan) focusRegion(".run-consent");
}

async function confirmRunGrant() {
  const plan = orchState.runPlan;
  if (!plan?.applicable) return;
  const request = {
    score: plan.request.score, project: plan.request.project, story: plan.request.story,
    issued_at: plan.request.issued_at, expires_at: plan.request.expires_at,
    standing_nudges: plan.request.standing_nudges || [],
    signal_channel: plan.request.signal_channel || "",
    expect: plan.start_token, approve: true, operator: orchState.grantDraft.operator,
  };
  orchState.runLoading = true; renderOrchestration();
  const { status, body } = await postJson("/api/runs/start", request);
  orchState.runLoading = false;
  if (startTokenWasRefused(status, body)) { orchState.runPlan = null; orchState.runError = "This start token is stale, reused, or does not match. Nothing started. Review a fresh permission preview."; renderOrchestration(); return; }
  if (status >= 400 || body.ok === false) { orchState.runError = responseIssueText(body) || `run start failed (${status})`; renderOrchestration(); return; }
  orchState.runId = body.data.run_id; orchState.runPlan = null; await refreshRunData();
}

async function previewRunAct(action, decision, correlation, trigger = document.activeElement) {
  rememberReturnFocus("run-act", trigger);
  const control = (orchState.runView?.controls || []).find((item) => item.action === action && String(item.decision || "") === String(decision || "") && String(item.correlation_id || "") === String(correlation || ""));
  const reason = control?.reason_required ? orchState.controlReason.trim() : "";
  orchState.runAct = null; orchState.runError = ""; orchState.runResult = null; renderOrchestration();
  const { status, body } = await postJson("/api/runs/preview", { run_id: orchState.runId, action, ...(reason ? { reason } : {}), ...(decision ? { decision } : {}), ...(correlation ? { correlation_id: correlation } : {}), ...(action === "supervise" ? { max_ticks: Number(orchState.maxTicks), max_seconds: Number(orchState.maxSeconds) } : {}) });
  if (status >= 400 || body.ok === false) { orchState.runError = (body.issues && body.issues[0]) || `run preview failed (${status})`; }
  else orchState.runAct = body.data;
  renderOrchestration();
  if (orchState.runAct) focusRegion(".bounded-preview");
}

async function confirmRunAct() {
  const preview = orchState.runAct;
  if (!preview?.applicable) return;
  const request = { run_id: preview.run_id, expect: preview.act_token, ...(preview.reason ? { reason: preview.reason } : {}), ...(preview.decision ? { decision: preview.decision } : {}), ...(preview.correlation_id ? { correlation_id: preview.correlation_id } : {}), ...(preview.action === "supervise" ? { max_ticks: preview.max_ticks, max_seconds: preview.max_seconds } : {}) };
  orchState.runLoading = true; renderOrchestration();
  let response;
  try {
    response = await postJson(`/api/runs/${encodeURIComponent(preview.action)}`, request);
  } catch (_err) {
    orchState.runLoading = false; orchState.runAct = null;
    orchState.runError = "The transport ended without a confirmed receipt. An effect may have occurred. Reload saved history before another action; this view will not retry automatically.";
    renderOrchestration(); return;
  }
  const { status, body } = response;
  orchState.runLoading = false;
  if (status === 409) { orchState.runAct = null; orchState.runError = "Stale run act refused before work or ledger change. Refresh once and preview the current state."; renderOrchestration(); return; }
  if (status >= 400 || body.ok === false) { orchState.runError = (body.issues && body.issues[0]) || `run act failed (${status})`; renderOrchestration(); return; }
  orchState.runResult = body.data; orchState.runAct = null; orchState.controlReason = ""; await refreshRunData();
}

async function openRunStream(button) {
  rememberReturnFocus("run-stream", button);
  orchState.runStream = null; renderOrchestration();
  const path = `/api/runs/${encodeURIComponent(orchState.runId)}/streams/${encodeURIComponent(button.dataset.executor)}/${encodeURIComponent(button.dataset.executionId)}/${encodeURIComponent(button.dataset.runStream)}?max_bytes=20000`;
  try { orchState.runStream = (await api(path)).data; }
  catch (err) { orchState.runError = err.message; }
  renderOrchestration();
  if (orchState.runStream) focusRegion(".run-open-stream");
}

function wireRunView() {
  document.getElementById("run-refresh")?.addEventListener("click", refreshRunData);
  document.querySelector("[data-live-technical]")?.addEventListener("click", openLiveTechnical);
  document.getElementById("run-select")?.addEventListener("change", async (event) => { orchState.runId = event.target.value; orchState.runAct = null; orchState.runResult = null; orchState.runStream = null; await refreshRunData(); });
  document.getElementById("run-grant-form")?.addEventListener("submit", (event) => { event.preventDefault(); previewRunGrant(event.currentTarget); });
  document.getElementById("run-start-confirm")?.addEventListener("click", confirmRunGrant);
  document.querySelector('[data-consent-summary="run"]')?.addEventListener("click", () => focusRegion("#run-consent-summary"));
  const closePlan = () => {
    orchState.runPlan = null;
    renderOrchestration();
    restoreReturnFocus("run-plan", "#run-grant-form button[type='submit']");
  };
  document.getElementById("run-plan-close")?.addEventListener("click", closePlan);
  document.getElementById("run-control-reason")?.addEventListener("input", (event) => { orchState.controlReason = event.target.value; });
  document.getElementById("run-max-ticks")?.addEventListener("input", (event) => { orchState.maxTicks = Number(event.target.value); });
  document.getElementById("run-max-seconds")?.addEventListener("input", (event) => { orchState.maxSeconds = Number(event.target.value); });
  document.querySelectorAll("[data-run-act]").forEach((button) => button.addEventListener("click", () => previewRunAct(button.dataset.runAct, button.dataset.runDecision, button.dataset.runCorrelation, button)));
  document.getElementById("run-act-confirm")?.addEventListener("click", confirmRunAct);
  const closeAct = () => {
    orchState.runAct = null;
    renderOrchestration();
    restoreReturnFocus("run-act");
  };
  document.getElementById("run-act-close")?.addEventListener("click", closeAct);
  document.querySelectorAll("[data-bounded-read]").forEach((button) => button.addEventListener("click", () => handleBoundedRead(button.dataset.boundedRead, "run")));
  document.querySelectorAll("[data-run-stream]").forEach((button) => button.addEventListener("click", () => openRunStream(button)));
  document.querySelectorAll("[data-ntf-ack]").forEach((button) => button.addEventListener("click", () => ackNotification(button.dataset.ntfAck)));
  const closeStream = () => {
    orchState.runStream = null;
    renderOrchestration();
    restoreReturnFocus("run-stream");
  };
  document.getElementById("run-stream-close")?.addEventListener("click", closeStream);
  wireDismissibleRegion(".run-consent", closePlan, "run-plan", "#run-grant-form button[type='submit']");
  wireDismissibleRegion(".bounded-preview", closeAct, "run-act");
  wireDismissibleRegion(".run-open-stream", closeStream, "run-stream");
}

/* ── autonomous program control room (WLA-26-11) ─────────────────
 * This browser view renders the canonical /api/programs documents. It does
 * not infer scheduling or authority. A live tail is opened only while one
 * explicit run route is active, and every act crosses preview + exact-token
 * confirmation before the server delegates to the shared program surface. */

let programState = {
  inventory: null, runId: "", view: null, plan: null, planRequest: null, envelope: null,
  act: null, stream: null, result: null, error: "", loading: false,
  reason: "", maxTicks: 100, maxSeconds: 300, notifications: [],
  connection: { status: SNAPSHOT_LIVE_STATE === "stale" ? "stale" : "checking" },
};
let programLive = null;
let programLiveTimer = null;

function stopProgramLive() {
  if (programLive) { programLive.close(); programLive = null; }
  if (programLiveTimer) { clearTimeout(programLiveTimer); programLiveTimer = null; }
}

function programScalar(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function programStateBadge(state) {
  const token = String(state || "unknown");
  const cls = ["running", "ready", "complete", "succeeded"].includes(token) ? "ok"
    : ["revoked", "cancelled", "exhausted", "stopped", "failed", "corrupt"].includes(token) ? "issue"
      : ["checkpoint", "paused", "expired", "waiting"].includes(token) ? "warn" : "";
  return badge(token, cls);
}

function programInventoryHtml() {
  const inventory = programState.inventory || { programs: [], runs: [], healthy: true };
  const programs = inventory.programs || [];
  const runs = inventory.runs || [];
  const consentSnapshot = SNAPSHOT_MODE ? new URLSearchParams(location.search).get("consentpreview") : "";
  if (consentSnapshot?.startsWith("program-") && (programState.plan || programState.error)) {
    return `<div class="program-inventory"><section class="program-start consent-snapshot-only">${programState.error && !programState.plan ? `<p class="guard consent-start-error" role="alert">${esc(programState.error)}</p>` : programConsentHtml(programState.plan)}</section></div>`;
  }
  return `<div class="program-inventory" data-healthy="${inventory.healthy ? "true" : "false"}">
    <header class="program-room-toolbar"><div><span class="orch-eyebrow">delivery options · review first</span><h1>Optional multi-phase delivery</h1><p>Review saved delivery plans and live progress. Opening this view starts no work and changes no saved delivery state.</p></div>${badge(inventory.healthy ? "ready" : "needs attention", inventory.healthy ? "ok" : "issue")}</header>
    <section class="program-room-grid" aria-label="delivery plans">${programs.map((item) => `<article class="program-card"><div><span>delivery plan</span>${item.valid ? badge("ready to review", "ok") : badge("needs repair", "issue")}</div><h2>${esc(item.title || item.slug || item.name)}</h2><p>${item.valid ? "This plan can be reviewed for a separate start." : "Resolve the listed plan issue before starting a delivery."}</p><details><summary>Technical details</summary><code>${esc(item.path)}</code><p>${item.valid ? `Exact fingerprint: <code>${esc(item.semantic_hash)}</code>` : esc((item.diagnostics || []).map((d) => d.message).join("; "))}</p></details></article>`).join("") || '<article class="program-empty"><h2>No optional delivery plan</h2><p>Ordinary roadmap work remains available. Nothing is running or waiting here.</p></article>'}</section>
    ${programs.length ? programStartHtml(programs) : ""}
    <section class="program-panel"><div class="program-panel-head"><div><span>live delivery</span><strong>${runs.length} saved deliver${runs.length === 1 ? "y" : "ies"}</strong></div>${badge("read only", "ok")}</div>
      <div class="program-room-grid">${runs.map((item) => `<article class="program-card"><div><span>progress</span>${programStateBadge(item.operational_state)}</div><h2>${esc(item.program || "Optional delivery")}</h2><p>${item.stop ? `Blocker: ${esc(item.stop)}.` : `${esc(item.outstanding_requests || 0)} decision${Number(item.outstanding_requests || 0) === 1 ? "" : "s"} waiting; ${esc(item.blocking_obligations || 0)} blocking follow-up${Number(item.blocking_obligations || 0) === 1 ? "" : "s"}.`}</p><a href="#/programs/${encodeURIComponent(item.run_id)}">Open live delivery</a><details><summary>Technical details</summary><code>${esc(item.run_id)}</code><p>Exact state: ${esc(item.state)} · mode: ${esc(item.mode || "—")} · expiry: ${esc(item.expires_at || "—")}</p></details></article>`).join("") || '<article class="program-empty"><h2>No live optional delivery</h2><p>Reviewing this page does not create one.</p></article>'}</div>
    </section>
  </div>`;
}

function programNarrowingSummary(plan, envelope) {
  if (!plan || !envelope) return { reduced: false, items: [] };
  const items = [];
  if (PROGRAM_MODE_RANK[plan.authority.mode] < PROGRAM_MODE_RANK[envelope.mode]) items.push("delivery pace");
  if ((plan.authority.capabilities || []).length < envelope.capabilities.length) items.push("allowed work");
  if (Object.entries(envelope.budgets).some(([key, value]) => Number(plan.authority.budgets?.[key]) < Number(value))) items.push("spend ceilings");
  const lifetime = Math.max(0, Math.round((Date.parse(plan.request.expires_at) - Date.parse(plan.request.issued_at)) / 1000));
  if (lifetime < envelope.lifetimeSeconds) items.push("lifetime");
  return { reduced: items.length > 0, items };
}

function programNarrowingHtml(plan, envelope) {
  if (!envelope) return "";
  const selected = new Set(plan.authority.capabilities || []);
  const modes = Object.keys(PROGRAM_MODE_RANK).filter((mode) => PROGRAM_MODE_RANK[mode] <= PROGRAM_MODE_RANK[envelope.mode]);
  const lifetime = Math.max(1, Math.round((Date.parse(plan.request.expires_at) - Date.parse(plan.request.issued_at)) / 1000));
  const pushPlanned = envelope.capabilities.includes("git:push");
  return `<form id="program-narrow-form" class="program-narrow-form">
    <header><div><span>Narrow permission</span><strong>You may lower these limits. You cannot raise them.</strong></div>${badge("server checks the ceiling", "ok")}</header>
    <div class="program-narrow-grid">
      <fieldset><legend>Delivery pace</legend>${modes.reverse().map((mode) => `<label><input type="radio" name="mode" value="${mode}"${plan.authority.mode === mode ? " checked" : ""}> ${esc(PROGRAM_MODE_LABELS[mode])}</label>`).join("")}</fieldset>
      <fieldset class="program-capability-choices"><legend>Allowed work</legend>${envelope.capabilities.map((capability, index) => `<label><input type="checkbox" name="capability" value="${esc(capability)}"${selected.has(capability) ? " checked" : ""}> ${esc(PROGRAM_CAPABILITY_LABELS[capability] || `Planned action type ${index + 1}`)}</label>`).join("") || "<p>This is advice-only permission. It cannot dispatch or change work.</p>"}</fieldset>
      <fieldset class="program-budget-choices"><legend>Spend ceilings</legend>${Object.entries(envelope.budgets).map(([name, maximum]) => `<label>${esc(consentBudgetLabel(name))}<input type="number" name="budget:${esc(name)}" min="1" max="${esc(maximum)}" value="${esc(plan.authority.budgets?.[name] || maximum)}"></label>`).join("")}</fieldset>
      <fieldset><legend>Lifetime</legend><label>permission seconds<input type="number" name="lifetime" min="1" max="${esc(envelope.lifetimeSeconds)}" value="${esc(lifetime)}"></label><small>The maximum is the planned lifetime. Lowering the wall-clock budget lowers this again.</small></fieldset>
      ${pushPlanned ? `<fieldset class="program-push-destination"><legend>Exact push destination</legend><label>remote name<input name="remote" value="${esc(plan.request.remote || "")}" placeholder="origin"></label><label>remote-tracking ref<input name="remote_ref" value="${esc(plan.request.remote_ref || "")}" placeholder="refs/remotes/origin/main"></label><small>A push remains impossible unless the plan permits it and the server verifies this exact destination.</small></fieldset>` : ""}
    </div>
    <button type="submit">Preview the reduced permission</button>
  </form>`;
}

function programConsentHtml(plan) {
  if (!plan) return "";
  const request = programState.planRequest || {};
  const heading = SNAPSHOT_MODE && new URLSearchParams(location.search).get("consentpreview")?.startsWith("program-") ? "h1" : "h2";
  const envelope = programState.envelope;
  const narrowing = programNarrowingSummary(plan, envelope);
  const story = plan.selection?.story;
  const work = story?.id ? `${story.id}: ${story.title || "selected roadmap work"}` : story || "the current planned roadmap selection";
  const stops = (plan.authority?.stop_conditions || []).map((stop) => stop.replaceAll("-", " ")).join(", ") || "scope completion, a required decision, a used budget, expiry, revocation, or cancellation";
  const mayPush = (plan.authority?.capabilities || []).includes("git:push");
  const destination = mayPush && plan.request.remote && plan.request.remote_ref ? `${plan.request.remote} · ${plan.request.remote_ref}` : "Nowhere";
  const destinationNote = mayPush ? "A push is possible only after the server verifies this exact destination and all earlier delivery gates pass." : "This reviewed permission does not include pushing.";
  return `<section class="program-consent ${plan.applicable ? "" : "refused"}" role="dialog" aria-modal="false" aria-labelledby="program-plan-title" tabindex="-1">
    <header class="consent-head"><div><span>Permission</span><${heading} id="program-plan-title">Approve optional delivery</${heading}><p>This is possible delivery authority, not automatic delivery. Previewing, opening this page, and receiving live updates start nothing.</p></div>${badge(plan.applicable ? "ready to approve" : "refused", plan.applicable ? "ok" : "issue")}</header>
    <section id="program-consent-summary" class="consent-summary" tabindex="-1">
      <div class="consent-fact-grid">
        <article><span>Allowed work</span><strong>${esc(work)}</strong><p>${esc(PROGRAM_MODE_LABELS[plan.authority.mode] || plan.authority.mode)} for the planned team. ${esc(programAllowedWorkSummary(plan.authority.capabilities))}.</p></article>
        <article><span>Spend ceiling</span>${consentBudgetListHtml(plan.authority.budgets, true)}</article>
        <article><span>Permission ends</span><strong>${esc(plan.request.expires_at)}</strong><p>${narrowing.reduced ? `You reduced ${esc(narrowing.items.join(", "))}.` : "No limits were reduced. This preview keeps the planned permission."}</p></article>
        <article><span>What makes it stop</span><strong>Declared stops always win</strong><p>${esc(stops)}.</p></article>
        <article><span>Push destination</span><strong>${esc(destination)}</strong><p>${esc(destinationNote)}</p></article>
        <article><span>Delivery is not automatic</span><strong>The browser adds no authority of its own</strong><p>Only a browser-confirmed program action may use pre-granted delivery permission. Later work still follows its own gates.</p></article>
      </div>
      ${consentNeverHtml()}
    </section>
    ${programNarrowingHtml(plan, envelope)}
    ${(plan.issues || []).map((issue) => `<p class="guard consent-refusal">${esc(typeof issue === "object" ? issue.message || issue.code : issue)} Review the permission again after fixing it.</p>`).join("")}
    <details class="consent-technical"><summary>Technical details</summary><p>Exact capability names, policy envelope, repository binding, token, and full grant document.</p><div class="run-token"><span>single-use start token</span><code>${esc(plan.start_token)}</code></div><pre>${esc(JSON.stringify(plan, null, 2))}</pre><button type="button" data-consent-summary="program">Back to permission summary</button></details>
    <div class="run-consent-actions">${plan.applicable ? '<button type="button" id="program-start-confirm">Approve this permission</button>' : ""}<button type="button" id="program-plan-close">Return without starting</button></div>
  </section>`;
}

function programStartHtml(programs) {
  const request = programState.planRequest || {};
  return `<section class="program-start"><div><span class="orch-eyebrow">permission before delivery</span><h2>Review optional delivery permission</h2><p>Choose a plan, name the accountable operator, and state the reason. The first preview loads the planned envelope. You can then reduce it before one approval.</p></div>
    <form id="program-plan-form" class="program-plan-form">
      <label>delivery plan<select name="program">${programs.filter((item) => item.valid).map((item) => `<option value="${esc(item.name)}"${request.program === item.name ? " selected" : ""}>${esc(item.title || item.slug || item.name)}</option>`).join("")}</select></label>
      <label>accountable operator ID<input name="operator" required maxlength="200" value="${esc(request.operator?.id || request.operator || "")}" placeholder="accountable-id"></label>
      <label class="program-plan-reason">reason for this permission<input name="reason" required maxlength="1000" value="${esc(request.reason || "")}" placeholder="one-line reviewed intent"></label>
      <button type="submit">Preview planned permission</button>
    </form>
    ${programState.error ? `<p class="guard consent-start-error" role="alert">${esc(programState.error)}</p>` : ""}
    ${programConsentHtml(programState.plan)}
  </section>`;
}

function programWhyHtml(view) {
  return `<section class="program-panel program-why"><div class="program-panel-head"><div><span>why this frontier</span><strong>Selection, workflow, team, and next derivable act</strong></div>${badge("ledger-derived", "ok")}</div>
    <div class="program-why-grid"><article><span>story</span><strong>${esc(programScalar(view.current?.selection?.story || view.current?.lineage?.story))}</strong><p>${esc(programScalar(view.why?.story))}</p></article><article><span>phase</span><strong>${esc(programScalar(view.current?.selection?.phase || view.current?.lineage?.phase))}</strong><p>${esc(programScalar(view.why?.phase))}</p></article><article><span>workflow / team</span><strong>${esc(programScalar(view.why?.workflow))} · ${esc(programScalar(view.why?.team))}</strong><p>${esc(programScalar(view.current?.lineage))}</p></article><article><span>next or refusal</span><strong>${esc(programScalar(view.current?.next_action?.kind || view.current?.stop || view.state))}</strong><p>${esc(programScalar(view.why?.next))}</p></article></div>
  </section>`;
}

function programOrganizationHtml(view) {
  const org = view.organization || { roles: [], councils: [] };
  const team = view.team_review || { sections: [], responsibilities: [], quality_constraints: [] };
  const proven = team.runtime_independence?.status === "proven";
  return `<section class="program-panel program-team-review" data-team-review-context="${esc(team.context || "legacy")}"><div class="program-panel-head"><div><span>team and review</span><strong>${esc(team.title || `${org.slug} · ${org.team}`)}</strong></div>${badge(proven ? "runtime independence proven" : "needs attention", proven ? "ok" : "issue")}</div>
    <p class="program-team-summary">${esc(team.summary || "Live team ownership and review.")}</p>
    <div class="program-team-answers">${(team.sections || []).map((section) => `<article><span>${esc(section.question)}</span><strong>${esc(section.label)}</strong><p>${esc(section.answer)}</p></article>`).join("")}</div>
    <div class="program-team-responsibilities">${(team.responsibilities || []).map((role) => `<article><div><strong>${esc(role.label)}</strong>${programStateBadge(role.assigned?.activity || "waiting")}</div><p>${esc(role.responsibility)}</p><span>${esc(role.coverage)}</span><small>${esc(role.outcomes)}</small></article>`).join("")}</div>
    <div class="program-team-constraints">${(team.quality_constraints || []).map((item) => `<article class="${item.status === "runtime-proven" ? "ready" : "issue"}"><div><strong>${esc((item.labels || []).join(" ↔ "))}</strong>${badge(item.status === "runtime-proven" ? "separate now" : "not proven", item.status === "runtime-proven" ? "ok" : "issue")}</div><p>${esc(item.runtime_claim)}</p></article>`).join("")}</div>
    <details class="program-team-technical"><summary>Technical details: exact seats, providers, models, identities, work areas, and sessions</summary>
      <p>Provider or model diversity is not identity independence. Principal, profile, work area, session binding, and read-only review remain separate exact facts.</p>
      <div class="tablewrap"><table class="run-table program-role-table"><thead><tr><th>seat / duty</th><th>agent</th><th>execution port</th><th>identity boundary</th><th>work area / session</th><th>activity</th></tr></thead><tbody>${(org.roles || []).map((seat) => { const x = seat.execution || {}; return `<tr><td><code>${esc(seat.address)}</code><br>${esc(seat.role)} · ${esc(seat.duty)}</td><td>${esc(seat.agent)}<br><small>${esc(seat.profile)}</small></td><td><strong>${esc(x.harness || "—")} / ${esc(x.adapter || "—")}</strong><br><small>${esc(x.provider || "—")} · ${esc(x.model || x.model_family || "—")}</small></td><td><code>${esc(x.auth_domain_fingerprint || "—")}</code><br><small>principal ${esc(seat.principal_fingerprint)}</small></td><td><code>${esc(seat.workspace_domain || "—")}</code><br><small>${esc(seat.session_binding_key || "—")}</small></td><td>${programStateBadge(seat.activity)}<br><small>${esc(programScalar(seat.last_result))}</small></td></tr>`; }).join("")}</tbody></table></div>
      <div class="program-councils"><section><h3>decision groups / exact authority</h3>${(org.councils || []).map((council) => `<article><div><strong>${esc(council.id)}</strong>${badge(council.primary_authority || council.method, council.primary_authority === "judge" ? "warn" : "ok")}</div><p>${esc((council.members || []).join(", "))} · required agreement ${esc(council.quorum)} · tie ${esc(council.tie_authority)}</p><small>chair ${esc(council.chair_seat || "rule")} · decider ${esc(council.decider_seat || "deterministic rule")}</small></article>`).join("") || '<p class="hint">No decision group is assigned to this scope.</p>'}</section><section><h3>separation facts</h3><pre>${esc(JSON.stringify(org.separation || {}, null, 2))}</pre></section></div>
    </details>
  </section>`;
}

function programActivityHtml(view) {
  const nodes = view.graph?.nodes || [];
  const sessions = view.activities?.sessions || [];
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const depth = (node) => { let value = 0; let parent = node.parent; const seen = new Set(); while (parent && byId.has(parent) && !seen.has(parent)) { seen.add(parent); value += 1; parent = byId.get(parent).parent; } return value; };
  return `<section class="program-panel"><div class="program-panel-head"><div><span>nested execution</span><strong>Compiled activity lineage and live session receipts</strong></div>${badge(`${nodes.length} activities`)}</div>
    <div class="tablewrap"><table class="run-table"><thead><tr><th>address</th><th>kind / role</th><th>state</th><th>result</th></tr></thead><tbody>${nodes.map((node) => `<tr><td style="padding-left:${10 + depth(node) * 18}px"><code>${esc(node.address || node.id)}</code></td><td>${esc(node.kind)} · ${esc(node.role || "system")}</td><td>${programStateBadge(node.state)}</td><td>${esc(programScalar(node.result))}</td></tr>`).join("") || '<tr><td colspan="4">No conductor activity has completed. The first tick remains an explicit act.</td></tr>'}</tbody></table></div>
    <div class="program-sessions">${sessions.map((session) => `<article><div><strong>${esc(session.profile)} · ${esc(session.adapter)}</strong>${programStateBadge(session.state)}</div><code>${esc(session.session_id || session.operation_id)}</code><p>${esc(programScalar(session.activity))}</p><div>${["stdout", "stderr"].filter((stream) => Number(session[`${stream}_bytes`] || 0) > 0).map((stream) => `<button type="button" data-program-stream="${stream}" data-session-id="${esc(session.session_id)}">open ${stream} · ${esc(session[`${stream}_bytes`])} B</button>`).join("")}</div></article>`).join("") || '<p class="hint">No driver session has crossed an execution port.</p>'}</div>
    ${programStreamHtml(programState.stream)}
  </section>`;
}

function programStreamHtml(stream) {
  if (!stream) return "";
  return `<section class="program-open-stream" role="dialog" aria-modal="false" aria-labelledby="program-stream-title" tabindex="-1"><div><strong id="program-stream-title">${esc(stream.session_id)} · ${esc(stream.stream)}</strong><button type="button" id="program-stream-close">close explicit stream</button></div><small>${esc(stream.included_bytes)} / ${esc(stream.bytes)} bytes · ${stream.truncated ? "truncated" : "complete"} · ${esc(stream.sha256)}</small><pre>${esc(stream.content)}</pre></section>`;
}

function programQualityHtml(view) {
  const artifactRows = (view.artifacts || []).map((item) => `<tr><td><code>${esc(item.name || item.artifact_id)}</code></td><td>${esc(item.artifact_kind || "artifact")}</td><td>${esc(item.bytes || 0)} B</td><td><code>${esc(item.sha256 || item.ref || "—")}</code></td></tr>`).join("");
  const resultItems = (items, empty) => items.map((item) => `<li><div><strong>${esc(item.address || item.action_id)}</strong>${programStateBadge(item.result || item.outcome || item.action_kind)}</div><p>${esc(programScalar(item.verdict || item.decision || item.payload || item.result))}</p></li>`).join("") || `<li class="hint">${esc(empty)}</li>`;
  return `<section class="program-panel"><div class="program-panel-head"><div><span>quality, dissent, and gates</span><strong>Evidence metadata, verdicts, councils, obligations, and delivery handoffs</strong></div></div>
    <div class="program-quality-grid">
      <section><h3>verdicts / gates</h3><ul>${resultItems([...(view.verdicts || []), ...(view.gates || [])], "No quality verdict or gate receipt yet.")}</ul></section>
      <section><h3>decisions / dissent / rounds</h3><ul>${resultItems([...(view.decisions || []), ...(view.dissent || []), ...(view.rounds || [])], "No deliberation receipt yet.")}</ul></section>
      <section><h3>obligations / debt</h3><ul>${(view.obligations?.all || []).map((item) => `<li><div><strong>${esc(item.id)}</strong>${programStateBadge(item.state)}${item.blocking ? badge("blocking", "issue") : ""}</div><p>${esc(item.statement || item.reason || programScalar(item))}</p></li>`).join("") || '<li class="hint">No decision obligation is recorded.</li>'}</ul></section>
      <section><h3>deliveries / integrations</h3><ul>${[...(view.deliveries || []), ...(view.integrations || [])].map((item) => `<li><div><strong>${esc(item.delivery_id || item.action_kind || item.action_id)}</strong>${programStateBadge(item.state || item.result || (item.complete ? "complete" : "active"))}</div><p>${esc(programScalar(item.next_action || item.story || item.receipt_hash))}</p></li>`).join("") || '<li class="hint">No certified delivery handoff has started.</li>'}</ul></section>
    </div>
    <div class="tablewrap"><table class="run-table"><thead><tr><th>artifact</th><th>kind</th><th>size</th><th>digest / ref</th></tr></thead><tbody>${artifactRows || '<tr><td colspan="4">No content-safe artifact metadata yet.</td></tr>'}</tbody></table></div>
  </section>`;
}

function programControlsHtml(view) {
  return `<section class="program-controls exact-control-audit"><div class="program-panel-head"><div><span>exact control catalog</span><strong>Applicability copied from the current saved program</strong></div>${badge("inspection only", "ok")}</div>
    <div class="run-unavailable">${(view.controls || []).map((item, index) => `<div><strong>${esc(item.action)}${item.decision ? ` · ${esc(item.decision)}` : ""}</strong><span>${item.available ? "available through the ordinary action review above" : esc(item.issue || "not applicable in the current authority state")}</span><code>/controls/${esc(index)}</code></div>`).join("")}</div>
  </section>`;
}

function programActHtml(preview) {
  if (!preview) return "";
  return `<details class="bounded-exact-preview"><summary>Technical details</summary><div class="run-token"><span>state + ledger + parameter token</span><code>${esc(preview.act_token)}</code></div><p>Observed <code>${esc(preview.state)}</code> at generation ${esc(preview.generation)} and ledger <code>${esc(preview.ledger_head)}</code>.</p><p><strong>lane:</strong> ${esc(preview.operation?.lane || "—")} · <strong>next:</strong> ${esc(programScalar(preview.operation?.next_action))}</p>${preview.action === "supervise" ? `<p><strong>Bound supervision:</strong> at most ${esc(preview.max_ticks)} steps and ${esc(preview.max_seconds)} seconds. It stops sooner at a checkpoint, terminal state, or no-progress result.</p>` : ""}${(preview.issues || []).map((issue) => `<p class="guard">${esc(issue)}</p>`).join("")}</details>`;
}

function programTimelineHtml(view) {
  return `<ol class="program-timeline">${(view.timeline || []).map((event) => `<li><div><strong>${esc(event.event)}</strong><time>${esc(event.at || event.ts)}</time>${badge(`#${event.seq}`)}</div><p>${Object.entries(event.detail || {}).map(([key, value]) => `<span><b>${esc(key)}</b> ${esc(programScalar(value))}</span>`).join("")}</p><code>${esc(event.event_hash)}</code></li>`).join("")}</ol>`;
}

function programNotificationsHtml(view) {
  const items = (programState.notifications || []).filter(
    (item) => item.run_id === view.run_id && item.kind.startsWith("program-"),
  );
  return `<section class="program-panel"><div class="program-panel-head"><div><span>operator notifications</span><strong>Derived facts and typed request documents</strong></div>${badge("transport ≠ authority", "ok")}</div>
    <ul class="run-notifications">${items.map((item) => `<li><code>${esc(item.kind)}</code> ${item.unread ? badge("unread", "warn") : badge("acked", "ok")}<span>${esc(item.detail)}</span>${item.request ? `<small>typed response · <code>${esc(item.request.correlation_id)}</code> · ${esc((item.request.response_schema?.decision || []).join("|"))} · fresh local act token still required</small>` : ""}${item.unread ? `<button type="button" data-program-ntf-ack="${esc(item.id)}">ack</button>` : ""}</li>`).join("") || '<li class="hint">No derived program notification at this ledger head.</li>'}</ul>
  </section>`;
}

function programRunHtml(view) {
  const runs = programState.inventory?.runs || [];
  const progress = view.phase_progress || {};
  const actions = boundedActionCenterHtml(view.bounded_actions, programState.act, programState.error, programState.result, "program");
  const liveRoute = liveDetailRoute();
  const toolbar = liveRoute?.kind === "program"
    ? `<div class="live-toolbar"><a href="#/live">Back to all live work</a><button type="button" id="program-refresh">Check for updates</button><button type="button" data-memory-open="program:${esc(view.run_id)}" data-memory-kind="program" data-memory-id="${esc(view.run_id)}">Memory</button><a href="#/live/program/${encodeURIComponent(view.run_id)}/technical">Technical details</a></div>`
    : `<div class="live-toolbar"><label>delivery run<select id="program-run-select">${runs.map((item) => `<option value="${esc(item.run_id)}"${item.run_id === view.run_id ? " selected" : ""}>${esc(view.program?.title || item.program || "program")} · ${esc(item.state)}</option>`).join("")}</select></label><button type="button" id="program-refresh">Check for updates</button><button type="button" data-memory-open="program:${esc(view.run_id)}" data-memory-kind="program" data-memory-id="${esc(view.run_id)}">Memory</button><button type="button" data-live-technical>Technical details</button></div>`;
  const technical = `${liveRoute?.kind === "program" ? `<p class="live-technical-return"><a href="#/live/program/${encodeURIComponent(view.run_id)}">Return to the ordinary view</a></p>` : ""}${programState.result ? `<div class="program-result" role="status"><strong>bounded operation completed</strong><span>${esc(programState.result.kind)} · ${esc(programState.result.stop || programState.result.state || programState.result.result || "recorded")}</span></div>` : ""}
    <div class="program-summary"><div><span>authority</span><strong>${esc(view.state)}</strong><small>${esc(view.terminal_meaning)}</small></div><div><span>operational frontier</span><strong>${esc(view.operational_state)}</strong><small>${esc(view.current?.stop || "ready")}</small></div><div><span>ledger</span><strong>${esc(view.event_count)} events</strong><code>${esc(view.ledger_head)}</code></div><div><span>scope progress</span><strong>${esc((progress.selected_stories || []).length)} selected</strong><small>${esc(programScalar(progress.scope_completion))}</small></div></div>
    ${programWhyHtml(view)}
    ${runBudgetHtml(view.budgets)}
    ${programOrganizationHtml(view)}
    ${programActivityHtml(view)}
    ${programQualityHtml(view)}
    ${programNotificationsHtml(view)}
    ${programControlsHtml(view)}
    <section class="program-panel"><div class="program-panel-head"><div><span>phase and authority boundary</span><strong>Granted scope, selected progress, capabilities, and permanent exclusions</strong></div></div><div class="program-boundary"><section><h3>phase progress</h3><pre>${esc(JSON.stringify(progress, null, 2))}</pre></section><section><h3>capabilities</h3><p>${(view.capabilities || []).map((item) => badge(item, "ok")).join(" ") || "none"}</p><h3>permanently excluded</h3><p>${(view.permanent_exclusions || []).map((item) => badge(item, "warn")).join(" ") || "none"}</p></section></div></section>
    <section class="program-panel"><div class="program-panel-head"><div><span>hash-chained receipts</span><strong>Program authority timeline</strong></div>${badge("content-safe metadata", "ok")}</div>${programTimelineHtml(view)}</section>`;
  return `<div class="program-room" data-program-run="${esc(view.run_id)}">${liveProgressShell(view.live_progress, programState.connection, toolbar, actions, technical, Boolean(programState.stream) || ["technical", "notifications"].includes(liveRoute?.section), "h1")}</div>`;
}

function renderPrograms() {
  if (liveDetailRoute()?.kind === "program") { renderLiveMission(); return; }
  const focus = captureAppFocus();
  if (programState.loading) {
    app.innerHTML = stateHtml("Replaying the authoritative program ledger…");
    finishDynamicRender(focus);
    return;
  }
  if (programState.error && !programState.inventory) {
    app.innerHTML = stateHtml(programState.error, true);
    finishDynamicRender(focus);
    return;
  }
  app.innerHTML = destinationNav("live", "#/programs")
    + (programState.view ? programRunHtml(programState.view) : programInventoryHtml());
  wirePrograms();
  finishDynamicRender(focus);
}

async function refreshProgramView() {
  if (!programState.runId) return;
  const previousView = programState.view;
  const focus = captureAppFocus();
  programState.loading = true;
  programState.error = "";
  programState.connection.status = "checking";
  if (!previousView) renderPrograms();
  try {
    const [inventory, view, notifications] = await Promise.all([
      api("/api/programs"),
      api(`/api/programs/${encodeURIComponent(programState.runId)}/view`),
      api("/api/notifications"),
    ]);
    programState.inventory = inventory.data;
    programState.view = view.data;
    programState.notifications = notifications.data.notifications || [];
    programState.connection.status = SNAPSHOT_LIVE_STATE === "stale" ? "stale" : SNAPSHOT_MODE ? "verified" : "checking";
  } catch (err) {
    programState.error = err.message;
    programState.view = previousView;
    programState.connection.status = previousView ? "stale" : "manual";
  }
  programState.loading = false;
  renderPrograms();
  restoreAppFocus(focus);
  const version = String(
    programState.view?.ledger_head || programState.view?.event_count || "",
  );
  if (liveAnnouncementKeys.has("program")) {
    announceLiveUpdate(
      "program",
      version,
      "Delivery progress changed. Review What happens next or check the saved history.",
    );
  } else if (version) {
    liveAnnouncementKeys.set("program", version);
  }
  startProgramLive();
}

let programLiveHadConnection = false;

function startProgramLive() {
  stopProgramLive();
  programLiveHadConnection = false;
  if (!programState.runId || !programState.view) return;
  if (SNAPSHOT_MODE || typeof EventSource === "undefined") {
    if (SNAPSHOT_LIVE_STATE !== "stale") programState.connection.status = SNAPSHOT_MODE ? "verified" : "manual";
    renderPreservingAppFocus(renderPrograms);
    return;
  }
  const runId = programState.runId;
  const cursor = Number(programState.view.event_count || 0);
  programLive = new EventSource(`/api/programs/${encodeURIComponent(runId)}/events?from=${cursor}&follow=1`);
  programLive.onopen = () => {
    if (programState.runId !== runId) return;
    if (programLiveHadConnection) {
      programState.connection.status = "reconnecting";
      showProgramCatchingUp(true);
    } else {
      programState.connection.status = "live";
    }
    programLiveHadConnection = true;
    renderPreservingAppFocus(renderPrograms);
  };
  // Snapshot-then-tail (WLA-34-05): refresh state from snapshot on reconnect
  programLive.addEventListener("snapshot", async () => {
    if (programState.runId !== runId) return;
    try {
      programState.view = (await api(`/api/programs/${encodeURIComponent(runId)}/view`)).data;
      programState.connection.status = "live";
      programState.inventory = (await api("/api/programs")).data;
      programState.notifications = (await api("/api/notifications")).data.notifications || [];
      renderPreservingAppFocus(renderPrograms);
    } catch (_err) { /* view stays as-is */ }
    showProgramCatchingUp(false);
  });
  programLive.addEventListener("program-ledger", () => {
    if (programLiveTimer) return;
    programLiveTimer = setTimeout(async () => {
      programLiveTimer = null;
      if (programState.runId !== runId) return;
      try {
        programState.view = (await api(`/api/programs/${encodeURIComponent(runId)}/view`)).data;
        programState.connection.status = "live";
        programState.inventory = (await api("/api/programs")).data;
        programState.notifications = (await api("/api/notifications")).data.notifications || [];
        announceLiveUpdate(
          "program",
          programState.view?.ledger_head || programState.view?.event_count,
          "Delivery progress changed. Review What happens next or check the saved history.",
        );
        renderPreservingAppFocus(renderPrograms);
      } catch (err) {
        programState.connection.status = "stale";
        announceLiveUpdate(
          "program-connection",
          `stale:${runId}:${programState.view?.event_count || ""}`,
          "Live delivery updates were interrupted. The last verified view remains available.",
        );
        renderPreservingAppFocus(renderPrograms);
      }
    }, 350);
  });
  programLive.onerror = () => {
    programState.connection.status = "stale";
    stopProgramLive();
    showProgramCatchingUp(false);
    announceLiveUpdate(
      "program-connection",
      `stale:${runId}:${programState.view?.event_count || ""}`,
      "Live delivery updates were interrupted. The last verified view remains available.",
    );
    renderPreservingAppFocus(renderPrograms);
  };
}

function showProgramCatchingUp(show) {
  const existing = document.querySelector(".program-room > .dw-catching-up");
  if (show) {
    if (!existing) {
      const room = document.querySelector(".program-room");
      if (room) {
        const banner = document.createElement("div");
        banner.className = "dw-catching-up";
        banner.setAttribute("role", "status");
        banner.setAttribute("aria-live", "polite");
        banner.textContent = "Catching up...";
        room.prepend(banner);
      }
    }
  } else if (existing) {
    existing.remove();
  }
}

async function requestProgramPermission(request) {
  const { status, body } = await postJson("/api/programs/plan", request);
  if (status >= 400 || body.ok === false) {
    programState.error = responseIssueText(body) || `program plan failed (${status})`;
    return null;
  }
  return body.data;
}

async function loadInitialProgramPermission(base) {
  const issued = new Date(base.issued_at);
  // Advice-only discovery is always at or below the tracked mode ceiling. It
  // reads the planned capabilities and budgets, then a second pure preview
  // binds the full envelope that the person may narrow.
  const discovery = await requestProgramPermission({
    ...base,
    mode: "advisory",
    capabilities: [],
    expires_at: new Date(issued.getTime() + 1_000).toISOString(),
  });
  if (!discovery) return;
  const mode = discovery.program.mode_ceiling;
  const capabilities = mode === "advisory" ? [] : [...(discovery.program.requested_capabilities || [])];
  const budgets = { ...(discovery.program.budgets || {}) };
  const lifetimeSeconds = Math.max(1, Math.min(3_600, Number(budgets.max_wall_seconds || 3_600)));
  programState.envelope = { mode, capabilities, budgets, lifetimeSeconds };
  programState.planRequest = {
    ...base, mode, capabilities, budgets,
    expires_at: new Date(issued.getTime() + lifetimeSeconds * 1_000).toISOString(),
  };
  programState.plan = await requestProgramPermission(programState.planRequest);
}

async function loadNarrowedProgramPermission({ mode, capabilities, budgets, lifetimeSeconds, remote = "", remoteRef = "" }) {
  const base = programState.planRequest;
  if (!programState.envelope || !base) return;
  const issued = new Date(base.issued_at);
  programState.planRequest = {
    program: base.program, operator: base.operator, reason: base.reason,
    intent_id: base.intent_id, issued_at: base.issued_at,
    mode, capabilities, budgets,
    expires_at: new Date(issued.getTime() + lifetimeSeconds * 1_000).toISOString(),
    ...(capabilities.includes("git:push") && remote ? { remote } : {}),
    ...(capabilities.includes("git:push") && remoteRef ? { remote_ref: remoteRef } : {}),
  };
  programState.plan = await requestProgramPermission(programState.planRequest);
}

async function previewProgramStart(form) {
  rememberReturnFocus("program-plan");
  const values = Object.fromEntries(new FormData(form).entries());
  const issued = new Date();
  const base = {
    program: String(values.program || ""),
    operator: String(values.operator || "").trim(),
    reason: String(values.reason || "").trim(),
    intent_id: `workbench-${issued.getTime()}`,
    issued_at: issued.toISOString(),
  };
  programState.planRequest = base;
  programState.plan = null;
  programState.envelope = null;
  programState.error = "";
  renderPrograms();
  await loadInitialProgramPermission(base);
  renderPrograms();
  if (programState.plan) focusRegion(".program-consent");
}

async function previewProgramNarrowing(form) {
  const envelope = programState.envelope;
  if (!envelope || !programState.planRequest) return;
  rememberReturnFocus("program-plan", form.querySelector("button[type='submit']"));
  const data = new FormData(form);
  const mode = String(data.get("mode") || envelope.mode);
  const capabilities = mode === "advisory" ? [] : data.getAll("capability").map(String).filter((item) => envelope.capabilities.includes(item));
  const budgets = {};
  Object.entries(envelope.budgets).forEach(([name, maximum]) => {
    const value = Number(data.get(`budget:${name}`));
    budgets[name] = Math.max(1, Math.min(Number(maximum), Number.isFinite(value) ? Math.floor(value) : Number(maximum)));
  });
  const requestedLifetime = Number(data.get("lifetime"));
  const lifetimeSeconds = Math.max(1, Math.min(
    envelope.lifetimeSeconds,
    Number(budgets.max_wall_seconds || envelope.lifetimeSeconds),
    Number.isFinite(requestedLifetime) ? Math.floor(requestedLifetime) : envelope.lifetimeSeconds,
  ));
  programState.plan = null;
  programState.error = "";
  renderPrograms();
  await loadNarrowedProgramPermission({
    mode, capabilities, budgets, lifetimeSeconds,
    remote: String(data.get("remote") || "").trim(),
    remoteRef: String(data.get("remote_ref") || "").trim(),
  });
  renderPrograms();
  if (programState.plan) focusRegion(".program-consent");
}

async function confirmProgramStart() {
  if (!programState.plan?.applicable || !programState.planRequest) return;
  const request = { ...programState.planRequest, approve: true, expect: programState.plan.start_token };
  const { status, body } = await postJson("/api/programs/start", request);
  if (status >= 400 || body.ok === false) {
    programState.plan = null;
    programState.error = startTokenWasRefused(status, body)
      ? "This start token is stale, reused, or does not match. Nothing started. Review a fresh permission preview."
      : responseIssueText(body) || `program start failed (${status})`;
    renderPrograms(); return;
  }
  programState.plan = null; programState.planRequest = null; programState.envelope = null;
  location.hash = `#/programs/${encodeURIComponent(body.data.run_id)}`;
}

async function previewProgramAct(button) {
  rememberReturnFocus("program-act", button);
  const action = button.dataset.programAct;
  const reasonRequired = ["request", "pause", "resume", "revoke", "cancel"].includes(action);
  const request = {
    run_id: programState.runId, action,
    ...(reasonRequired ? { reason: programState.reason.trim() } : {}),
    ...(button.dataset.programDecision ? { decision: button.dataset.programDecision } : {}),
    ...(button.dataset.programRequest ? { request_id: button.dataset.programRequest } : {}),
    ...(["tick", "supervise"].includes(action) ? {
      max_ticks: action === "tick" ? 100 : Number(programState.maxTicks),
      max_seconds: action === "tick" ? 300 : Number(programState.maxSeconds),
    } : {}),
  };
  programState.act = null; programState.error = ""; programState.result = null; renderPrograms();
  const { status, body } = await postJson("/api/programs/preview", request);
  if (status >= 400 || body.ok === false) programState.error = (body.issues && body.issues[0]) || `program preview failed (${status})`;
  else programState.act = body.data;
  renderPrograms();
  if (programState.act) focusRegion(".bounded-preview");
}

async function confirmProgramAct() {
  const preview = programState.act;
  if (!preview?.applicable) return;
  const request = {
    run_id: preview.run_id, expect: preview.act_token,
    ...(preview.reason ? { reason: preview.reason } : {}),
    ...(preview.decision ? { decision: preview.decision } : {}),
    ...(preview.request_id ? { request_id: preview.request_id } : {}),
    ...(preview.action === "supervise" ? { max_ticks: preview.max_ticks, max_seconds: preview.max_seconds } : {}),
  };
  let response;
  try {
    response = await postJson(`/api/programs/${encodeURIComponent(preview.action)}`, request);
  } catch (_err) {
    programState.act = null;
    programState.error = "The transport ended without a confirmed receipt. An effect may have occurred. Reload saved history before another action; this view will not retry automatically.";
    renderPrograms(); return;
  }
  const { status, body } = response;
  if (status >= 400 || body.ok === false) {
    programState.act = null;
    programState.error = status === 409
      ? "Stale program action refused before work or saved event change. Reload once and review the current action."
      : (body.issues && body.issues[0]) || `program act failed (${status})`;
    renderPrograms(); return;
  }
  programState.result = body.data; programState.act = null; programState.reason = "";
  await refreshProgramView();
}

async function openProgramStream(button) {
  rememberReturnFocus("program-stream", button);
  programState.stream = null; programState.error = ""; renderPrograms();
  try {
    programState.stream = (await api(`/api/programs/${encodeURIComponent(programState.runId)}/streams/${encodeURIComponent(button.dataset.sessionId)}/${encodeURIComponent(button.dataset.programStream)}?max_bytes=20000`)).data;
  } catch (err) { programState.error = err.message; }
  renderPrograms();
  if (programState.stream) focusRegion(".program-open-stream");
}

async function ackProgramNotification(id) {
  const { status, body } = await postJson("/api/notifications/ack", { id });
  if (status >= 400 || body.ok === false) {
    programState.error = (body.issues && body.issues[0]) || `notification acknowledgement failed (${status})`;
    renderPrograms(); return;
  }
  programState.notifications = (await api("/api/notifications")).data.notifications || [];
  renderPrograms();
}

function wirePrograms() {
  document.getElementById("program-plan-form")?.addEventListener("submit", (event) => { event.preventDefault(); previewProgramStart(event.currentTarget); });
  document.getElementById("program-narrow-form")?.addEventListener("submit", (event) => { event.preventDefault(); previewProgramNarrowing(event.currentTarget); });
  document.getElementById("program-start-confirm")?.addEventListener("click", confirmProgramStart);
  document.querySelector('[data-consent-summary="program"]')?.addEventListener("click", () => focusRegion("#program-consent-summary"));
  const closePlan = () => {
    programState.plan = null;
    renderPrograms();
    restoreReturnFocus("program-plan", "#program-plan-form button[type='submit']");
  };
  document.getElementById("program-plan-close")?.addEventListener("click", closePlan);
  document.getElementById("program-refresh")?.addEventListener("click", refreshProgramView);
  document.querySelector("[data-live-technical]")?.addEventListener("click", openLiveTechnical);
  document.getElementById("program-run-select")?.addEventListener("change", (event) => { location.hash = `#/programs/${encodeURIComponent(event.target.value)}`; });
  document.getElementById("program-control-reason")?.addEventListener("input", (event) => { programState.reason = event.target.value; });
  document.getElementById("program-max-ticks")?.addEventListener("input", (event) => { programState.maxTicks = Number(event.target.value); });
  document.getElementById("program-max-seconds")?.addEventListener("input", (event) => { programState.maxSeconds = Number(event.target.value); });
  document.querySelectorAll("[data-program-act]").forEach((button) => button.addEventListener("click", () => previewProgramAct(button)));
  document.getElementById("program-act-confirm")?.addEventListener("click", confirmProgramAct);
  const closeAct = () => {
    programState.act = null;
    renderPrograms();
    restoreReturnFocus("program-act");
  };
  document.getElementById("program-act-close")?.addEventListener("click", closeAct);
  document.querySelectorAll("[data-bounded-read]").forEach((button) => button.addEventListener("click", () => handleBoundedRead(button.dataset.boundedRead, "program")));
  document.querySelectorAll("[data-program-stream]").forEach((button) => button.addEventListener("click", () => openProgramStream(button)));
  document.querySelectorAll("[data-program-ntf-ack]").forEach((button) => button.addEventListener("click", () => ackProgramNotification(button.dataset.programNtfAck)));
  const closeStream = () => {
    programState.stream = null;
    renderPrograms();
    restoreReturnFocus("program-stream");
  };
  document.getElementById("program-stream-close")?.addEventListener("click", closeStream);
  wireDismissibleRegion(".program-consent", closePlan, "program-plan", "#program-plan-form button[type='submit']");
  wireDismissibleRegion(".bounded-preview", closeAct, "program-act");
  wireDismissibleRegion(".program-open-stream", closeStream, "program-stream");
}

async function viewPrograms(runId = "") {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "program control", href: "#/programs" }, ...(runId ? [{ label: runId }] : [])]);
  programState.runId = runId; programState.view = null; programState.act = null;
  programState.stream = null; programState.result = null; programState.error = "";
  const [inventory, notifications] = await Promise.all([
    api("/api/programs"), api("/api/notifications"),
  ]);
  programState.inventory = inventory.data;
  programState.notifications = notifications.data.notifications || [];
  if (runId) {
    programState.view = (await api(`/api/programs/${encodeURIComponent(runId)}/view`)).data;
    programState.connection.status = SNAPSHOT_LIVE_STATE === "stale" ? "stale" : SNAPSHOT_MODE ? "verified" : "checking";
    if (SNAPSHOT_MODE && SNAPSHOT_BOUNDED_PREVIEW) {
      const control = (programState.view.controls || []).find((item) => item.available && (
        SNAPSHOT_BOUNDED_PREVIEW === "decision"
          ? item.action === "request" && item.decision === "approve"
          : item.action === SNAPSHOT_BOUNDED_PREVIEW
      ));
      if (control) {
        programState.reason = control.reason_required
          ? "Review this deterministic viewport action."
          : "";
        const response = await postJson("/api/programs/preview", {
          run_id: programState.runId,
          action: control.action,
          ...(programState.reason ? { reason: programState.reason } : {}),
          ...(control.decision ? { decision: control.decision } : {}),
          ...(control.request_id ? { request_id: control.request_id } : {}),
          ...(["tick", "supervise"].includes(control.action) ? {
            max_ticks: 100, max_seconds: 300,
          } : {}),
        });
        if (response.status < 400 && response.body.ok !== false) {
          programState.act = response.body.data;
        }
      }
    }
    if (SNAPSHOT_MODE && SNAPSHOT_BOUNDED_ERROR) {
      programState.error = SNAPSHOT_BOUNDED_ERROR === "stale"
        ? "Stale program action refused before work or saved event change. Reload once and review the current action."
        : "The action response ended without a confirmed receipt.";
    }
    startProgramLive();
  }
  const consentSnapshot = SNAPSHOT_MODE ? new URLSearchParams(location.search).get("consentpreview") : "";
  if (!runId && consentSnapshot?.startsWith("program-") && programState.inventory?.programs?.some((item) => item.valid)) {
    const program = programState.inventory.programs.find((item) => item.valid);
    const issued = new Date();
    const base = {
      program: program.name, operator: "ui-consent-reviewer",
      reason: "Review the exact optional delivery permission.",
      intent_id: `workbench-${issued.getTime()}`, issued_at: issued.toISOString(),
    };
    programState.planRequest = base;
    programState.plan = null;
    programState.envelope = null;
    programState.error = "";
    await loadInitialProgramPermission(base);
    if (consentSnapshot === "program-narrowed" && programState.plan && programState.envelope) {
      const envelope = programState.envelope;
      const capabilities = envelope.capabilities.includes("roadmap:phase-advance")
        ? envelope.capabilities.filter((item) => item !== "roadmap:phase-advance")
        : envelope.capabilities.length > 2 ? envelope.capabilities.slice(0, -1) : [...envelope.capabilities];
      const budgets = Object.fromEntries(Object.entries(envelope.budgets).map(([name, maximum]) => [name, Math.max(1, Math.floor(Number(maximum) / 2))]));
      const lifetimeSeconds = Math.max(1, Math.min(Math.floor(envelope.lifetimeSeconds / 2), Number(budgets.max_wall_seconds || envelope.lifetimeSeconds)));
      programState.plan = null;
      await loadNarrowedProgramPermission({ mode: envelope.mode, capabilities, budgets, lifetimeSeconds });
    }
    if (consentSnapshot === "program-refusal") {
      programState.plan = null;
      programState.error = "This start token is stale, reused, or does not match. Nothing started. Review a fresh permission preview.";
    }
  }
  renderPrograms();
  if (consentSnapshot?.startsWith("program-") && programState.plan) focusConsentSnapshot(".program-consent");
  if (consentSnapshot === "program-refusal") focusConsentSnapshot(".consent-start-error");
  focusBoundedSnapshot();
}

/* ── Live mission control (WLA-32-07) ───────────────────────────────
 * The combined inventory is a read-only composition of the canonical run and
 * program views. Its groups are presentation only; exact ledger states remain
 * visible and every act stays on the existing preview/confirm boundary. */

let liveMissionState = {
  runs: [], programs: [], notifications: [], error: "", loading: false,
  detail: null,
  connection: { status: SNAPSHOT_LIVE_STATE === "stale" ? "stale" : "manual" },
};

function liveAttentionItems(kind, view) {
  const inbox = view?.bounded_actions?.inbox || [];
  const notificationPrefix = kind === "program" ? "program-" : "";
  const unread = liveMissionState.notifications.filter((item) => (
    item.run_id === view.run_id && item.unread
    && (kind === "program" ? String(item.kind || "").startsWith(notificationPrefix) : !String(item.kind || "").startsWith("program-"))
  ));
  return [
    ...inbox.map((item) => ({
      kind: item.kind === "decision" ? "Decision" : item.kind === "refusal" ? "Refusal" : "Blocker",
      label: item.affected_work || item.why || "Saved work needs attention",
      detail: item.why || item.after_no_choice || "Review the canonical saved state.",
      href: `#/live/${kind}/${encodeURIComponent(view.run_id)}/attention`,
    })),
    ...unread.map((item) => ({
      kind: "Unread notification",
      label: item.detail || item.kind,
      detail: "Acknowledge it from this delivery's notification history.",
      href: `#/live/${kind}/${encodeURIComponent(view.run_id)}/notifications`,
    })),
  ];
}

function liveMissionItem(kind, view) {
  const progress = view.live_progress || {};
  const exactState = String(view.state || view.operational_state || "unknown");
  const attention = liveAttentionItems(kind, view);
  const statusGroup = String(progress.status?.group || "waiting");
  const group = attention.length ? "attention"
    : statusGroup === "complete" || ["complete", "cancelled", "revoked"].includes(exactState) ? "finished"
      : ["paused", "blocked", "stopped"].includes(exactState) ? "paused"
        : "moving";
  return {
    kind, view, exactState, attention, group,
    statusLabel: progress.status?.label || exactState,
    statusMeaning: progress.status?.meaning || view.terminal_meaning || "Saved ledger state.",
    next: progress.next_step || { label: "Inspect saved state", detail: "Open the canonical control room." },
    title: progress.title || (kind === "program" ? view.program?.title : view.story?.title) || view.run_id,
  };
}

function liveMissionCard(item) {
  const view = item.view;
  const detailHref = `#/live/${item.kind}/${encodeURIComponent(view.run_id)}`;
  const kindLabel = item.kind === "run" ? "Bounded run" : "Multi-phase program";
  return `<article class="live-mission-card group-${esc(item.group)}" data-live-kind="${esc(item.kind)}" data-live-state="${esc(item.exactState)}">
    <header><div><span class="live-kind">${esc(kindLabel)}</span><h3><a href="${detailHref}">${esc(item.title)}</a></h3></div>${liveStateBadge(view.live_progress)}</header>
    <dl class="live-mission-facts"><div><dt>Current status</dt><dd><strong>${esc(item.statusLabel)}</strong><span>Exact state: ${esc(item.exactState)}</span><small>${esc(item.statusMeaning)}</small></dd></div><div><dt>Canonical next step</dt><dd><strong>${esc(item.next.label || "Wait")}</strong><small>${esc(item.next.detail || "")}</small></dd></div><div><dt>Needs attention</dt><dd><strong>${item.attention.length ? `${esc(item.attention.length)} item${item.attention.length === 1 ? "" : "s"}` : "No"}</strong><small>${item.attention.length ? "Decision, blocker, refusal, or unread notice." : "No decision, blocker, refusal, or unread notice is visible."}</small></dd></div></dl>
    ${item.attention.length ? `<ul class="live-mission-attention">${item.attention.map((attention) => `<li><span>${esc(attention.kind)}</span><a href="${attention.href}">${esc(attention.label)}</a><small>${esc(attention.detail)}</small></li>`).join("")}</ul>` : ""}
    <a class="live-open" href="${detailHref}">Open exact control room</a>
  </article>`;
}

function liveMissionInventoryHtml() {
  let items = [
    ...liveMissionState.runs.map((view) => liveMissionItem("run", view)),
    ...liveMissionState.programs.map((view) => liveMissionItem("program", view)),
  ];
  if (SNAPSHOT_MODE && SNAPSHOT_LIVE_SCENARIO) {
    const matches = {
      active: (item) => item.exactState === "active" || item.exactState === "running",
      "awaiting-decision": (item) => item.exactState === "awaiting-approval" || item.attention.some((attention) => attention.kind === "Decision"),
      paused: (item) => item.exactState === "paused",
      revoked: (item) => item.exactState === "revoked",
      cancelled: (item) => item.exactState === "cancelled",
      complete: (item) => item.exactState === "complete" || item.exactState === "awaiting-certification" || item.view.live_progress?.status?.group === "complete",
      stale: () => true,
      empty: () => false,
    }[SNAPSHOT_LIVE_SCENARIO];
    if (matches) items = items.filter(matches);
  }
  const groups = [
    ["attention", "Needs you", "A decision, blocker, refusal, or unread notification is visible."],
    ["moving", "Moving or ready", "Canonical state says this work can move or is waiting for its next reviewed act."],
    ["paused", "Paused or blocked", "These exact states are not moving. Paused permission is resumable; blocked work needs recovery."],
    ["finished", "Finished or permanently stopped", "Complete work is done. Revoked and cancelled permission cannot resume."],
  ];
  return `<section class="live-mission" aria-labelledby="live-mission-title">
    <header class="live-mission-head"><div><span class="orch-eyebrow">Mission control</span><h1 id="live-mission-title">Live work</h1><p>One glance shows what is running, what happens next, and where you need to act. Opening this view starts no work.</p></div><button type="button" id="live-mission-refresh">Refresh all saved history</button></header>
    ${liveMissionState.connection.status === "stale" ? liveConnectionHtml(liveMissionState.connection, {}) : ""}
    <section class="live-mission-summary" aria-label="Live work summary"><article><strong>${esc(items.length)}</strong><span>saved runs and programs</span></article><article><strong>${esc(items.filter((item) => item.group === "attention").length)}</strong><span>need attention</span></article><article><strong>${esc(items.filter((item) => item.group === "moving").length)}</strong><span>moving or ready</span></article></section>
    ${liveMissionState.error ? boundedErrorHtml(liveMissionState.error) : ""}
    ${groups.map(([id, title, description]) => { const matching = items.filter((item) => item.group === id); return matching.length ? `<section class="live-mission-group group-${id}" aria-labelledby="live-group-${id}"><header><h2 id="live-group-${id}">${title} <small>${matching.length}</small></h2><p>${description}</p></header><div class="live-mission-grid">${matching.map(liveMissionCard).join("")}</div></section>` : ""; }).join("") || stateHtml("No bounded runs or programs have been saved. Opening Live does not create one.")}
  </section>`;
}

function focusLiveDetailSection(section) {
  if (!section) return;
  const selector = section === "attention" ? ".bounded-inbox"
    : section === "notifications" ? ".run-notifications"
      : section === "technical" ? ".live-technical" : "";
  if (!selector) return;
  const target = document.querySelector(selector);
  if (!target) return;
  if (section === "notifications") target.closest(".live-technical")?.setAttribute("open", "");
  target.setAttribute("tabindex", "-1");
  focusElement(target);
  target.scrollIntoView({ block: "start" });
}

function renderLiveMission() {
  const focus = captureAppFocus();
  if (liveMissionState.loading && !liveMissionState.detail) {
    app.innerHTML = `${destinationNav("live", "#/live")}${stateHtml("Replaying saved run and program history…")}`;
  } else if (liveMissionState.detail?.kind === "run") {
    app.innerHTML = `${destinationNav("live", "#/live")}${runViewHtml()}`;
    wireRunView();
  } else if (liveMissionState.detail?.kind === "program") {
    app.innerHTML = `${destinationNav("live", "#/live")}${programRunHtml(programState.view)}`;
    wirePrograms();
  } else {
    app.innerHTML = `${destinationNav("live", "#/live")}${liveMissionInventoryHtml()}`;
    document.getElementById("live-mission-refresh")?.addEventListener("click", () => viewLive());
  }
  finishDynamicRender(focus);
  focusLiveDetailSection(liveMissionState.detail?.section || "");
}

async function loadCanonicalLiveViews(inventory) {
  const runIds = (inventory.runs || []).filter((item) => item.valid !== false).map((item) => item.run_id);
  const programIds = (inventory.programs?.runs || []).map((item) => item.run_id);
  const [runResults, programResults] = await Promise.all([
    Promise.allSettled(runIds.map((id) => api(`/api/runs/${encodeURIComponent(id)}/view`))),
    Promise.allSettled(programIds.map((id) => api(`/api/programs/${encodeURIComponent(id)}/view`))),
  ]);
  liveMissionState.runs = runResults.filter((result) => result.status === "fulfilled").map((result) => result.value.data);
  liveMissionState.programs = programResults.filter((result) => result.status === "fulfilled").map((result) => result.value.data);
  const refused = [...runResults, ...programResults].filter((result) => result.status === "rejected");
  liveMissionState.error = refused.length ? `${refused.length} saved item${refused.length === 1 ? "" : "s"} could not be replayed. Refresh after inspecting repository health.` : "";
}

async function viewLive(kind = "", runId = "", section = "") {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "live", href: "#/live" }, ...(kind && runId ? [{ label: `${kind} ${runId}` }] : [])]);
  liveMissionState.loading = true;
  liveMissionState.detail = kind && runId ? { kind, id: runId, section } : null;
  let runsBody;
  let programsBody;
  let notificationsBody;
  try {
    [runsBody, programsBody, notificationsBody] = await Promise.all([
      api("/api/runs"), api("/api/programs"), api("/api/notifications"),
    ]);
  } catch (err) {
    liveMissionState.loading = false;
    liveMissionState.error = `Saved history could not be refreshed. ${err.message}`;
    liveMissionState.connection.status = "stale";
    renderLiveMission();
    announceLiveUpdate(
      "mission-control",
      `stale:${Date.now()}`,
      "Live work could not be refreshed. The last verified list remains visible; use Refresh all saved history when you are ready.",
    );
    return;
  }
  liveMissionState.connection.status = SNAPSHOT_LIVE_STATE === "stale" ? "stale" : "verified";
  liveMissionState.error = "";
  const inventory = { runs: runsBody.data.runs || [], programs: programsBody.data };
  liveMissionState.notifications = notificationsBody.data.notifications || [];
  orchState.runInventory = inventory.runs;
  orchState.runs = inventory.runs.filter((item) => item.valid !== false);
  programState.inventory = inventory.programs;
  orchState.notifications = liveMissionState.notifications;
  programState.notifications = liveMissionState.notifications;
  if (kind === "run" && runId) {
    orchState.view = "run"; orchState.runId = runId; orchState.runAct = null; orchState.runResult = null; orchState.runError = ""; orchState.runStream = null;
    orchState.runView = (await api(`/api/runs/${encodeURIComponent(runId)}/view`)).data;
    orchState.runConnection.status = SNAPSHOT_LIVE_STATE === "stale" ? "stale" : SNAPSHOT_MODE ? "verified" : "checking";
  } else if (kind === "program" && runId) {
    programState.runId = runId; programState.act = null; programState.result = null; programState.error = ""; programState.stream = null;
    programState.view = (await api(`/api/programs/${encodeURIComponent(runId)}/view`)).data;
    programState.connection.status = SNAPSHOT_LIVE_STATE === "stale" ? "stale" : SNAPSHOT_MODE ? "verified" : "checking";
  } else {
    await loadCanonicalLiveViews(inventory);
  }
  liveMissionState.loading = false;
  renderLiveMission();
  if (kind === "run") startRunLive();
  if (kind === "program") startProgramLive();
}
