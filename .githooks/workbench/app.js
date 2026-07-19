/* Delivery Workbench — hash-routed, API-backed. Reads are live and pure;
 * mutations cross only the guarded editor or deliberate-step boundaries.
 * Every byte of state comes from /api/*, which derives live from the
 * Markdown roadmap through the dw_pmo core. No local persistence. */

"use strict";

const app = document.getElementById("app");
const crumbs = document.getElementById("crumbs");
const refreshTime = document.getElementById("refresh-time");
const footRoot = document.getElementById("foot-root");

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

/* ?snapshot=1 switches to synchronous XHR so headless screenshot tools
 * that capture at the window load event see fully rendered data. Not
 * for interactive use. */
const SNAPSHOT_MODE = new URLSearchParams(location.search).has("snapshot");

function syncGet(path) {
  const xhr = new XMLHttpRequest();
  xhr.open("GET", path, false);
  xhr.send();
  return { status: xhr.status, body: JSON.parse(xhr.responseText) };
}

async function postJson(path, payload) {
  if (SNAPSHOT_MODE) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", path, false);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify(payload));
    return { status: xhr.status, body: JSON.parse(xhr.responseText) };
  }
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return { status: res.status, body: await res.json() };
}

function diffHtml(diff) {
  return diff.split("\n").map((line) => {
    const cls = line.startsWith("+") ? "add" : line.startsWith("-") ? "del" : line.startsWith("@@") ? "hunk" : "";
    return cls ? `<span class="${cls}">${esc(line)}</span>` : esc(line);
  }).join("\n");
}

async function api(path) {
  let status;
  let body;
  if (SNAPSHOT_MODE) {
    ({ status, body } = syncGet(path));
  } else {
    const res = await fetch(path, { cache: "no-store" });
    status = res.status;
    body = await res.json();
  }
  if (status >= 400 || body.ok === false) {
    const msg = (body.issues && body.issues[0]) || `API error ${status}`;
    throw new Error(msg);
  }
  refreshTime.textContent = `refreshed ${new Date().toLocaleTimeString()}`;
  return body;
}

function setCrumbs(parts) {
  crumbs.innerHTML = parts
    .map((p, i) => (i < parts.length - 1 && p.href
      ? `<a href="${p.href}">${esc(p.label)}</a>`
      : `<span>${esc(p.label)}</span>`))
    .join(" / ");
}

function stateHtml(text, isError) {
  return `<div class="state${isError ? " error" : ""}">${esc(text)}</div>`;
}

function badge(text, cls) {
  return `<span class="badge ${cls || esc(String(text))}">${esc(text)}</span>`;
}

function statusCounts(counts) {
  const order = ["in-progress", "ready", "backlog", "blocked", "done"];
  const keys = Object.keys(counts).sort(
    (a, b) => (order.indexOf(a) + 99) - (order.indexOf(b) + 99) || a.localeCompare(b)
  );
  if (!keys.length) return '<span class="badge">no stories</span>';
  return keys.map((k) => badge(`${k} ${counts[k]}`, k)).join(" ");
}

function statusActionHtml(action) {
  const command = Array.isArray(action.command) ? action.command : null;
  const manual = action.kind === "manual" || !command;
  return `<div class="brief-action${manual ? " manual" : ""}" data-action="${esc(action.id)}">
    <div class="brief-action-head">
      <span>next safe action</span>
      <strong>${esc(action.id)}</strong>
      ${action.blocking ? '<span class="badge issue">blocking</span>' : ""}
    </div>
    <div class="brief-reason">${esc(action.reason)}</div>
    ${command ? `<div class="brief-argv" aria-label="command argument vector">
      <span class="brief-argv-label">argv</span>
      ${command.map((arg, index) => `<code data-argv-index="${index}">${esc(arg)}</code>`).join("")}
    </div>` : `<div class="brief-manual"><strong>manual act</strong><span>No command is synthesized for this decision.</span></div>`}
    <div class="brief-readonly">Recommendation only — review the separate deliberate-step boundary below before anything runs.</div>
  </div>`;
}

function stepArgvHtml(argv, label) {
  if (!Array.isArray(argv)) return "";
  return `<div class="brief-argv" aria-label="${esc(label)} argument vector">
    <span class="brief-argv-label">${esc(label)}</span>
    ${argv.map((arg, index) => `<code data-step-argv-index="${index}">${esc(arg)}</code>`).join("")}
  </div>`;
}

function stepControlHtml(step) {
  if (!step.applicable) {
    return `<div class="brief-step-unavailable" data-step-applicable="false">
      <div><strong>deliberate step unavailable</strong><span>No apply control is offered for this recommendation.</span></div>
      <p>${esc(step.refusal || "The current recommendation is not executable through the one-step handrail.")}</p>
    </div>`;
  }
  return `<div class="brief-step-control" data-step-applicable="true">
    <div class="brief-step-intro">
      <div><strong>separate act boundary</strong><span>Review the state-bound lease, then authorize only this one action.</span></div>
      <button type="button" id="step-review">review one deliberate step</button>
    </div>
    <div id="step-confirm" aria-live="polite"></div>
  </div>`;
}

function stepConfirmationHtml(step) {
  return `<div class="step-confirmation" data-step-token="${esc(step.token)}">
    <div class="step-confirm-head"><span>confirmation</span><strong>${esc(step.action.id)}</strong>${badge("one child maximum", "warn")}</div>
    <p>${esc(step.action.reason)}</p>
    <div class="step-token"><span>state token</span><code>${esc(step.token)}</code></div>
    ${stepArgvHtml(step.action.command, "authorized argv")}
    ${stepArgvHtml(step.apply_command, "CLI fallback")}
    <div class="step-confirm-actions">
      <button type="button" id="step-apply">apply this one step</button>
      <button type="button" id="step-cancel">cancel</button>
    </div>
    <div class="brief-readonly">One POST, at most one child, then a fresh briefing. No automatic continuation.</div>
  </div>`;
}

function stepNoticeHtml(notice) {
  if (!notice) return "";
  const result = notice.result;
  const after = result && result.after ? result.after.action_id : null;
  const streams = result && result.output
    ? [result.output.stdout, result.output.stderr].filter(Boolean).join("\n") : "";
  return `<div class="brief-step-notice ${esc(notice.kind)}" role="status">
    <strong>${esc(notice.title)}</strong><span>${esc(notice.detail)}</span>
    ${after ? `<span>Stopped. Fresh next action: <code>${esc(after)}</code>.</span>` : ""}
    ${streams ? `<pre>${esc(streams)}</pre>` : ""}
  </div>`;
}

async function applyReviewedStep(step, button) {
  button.disabled = true;
  button.textContent = "applying one step…";
  try {
    const { status, body } = await postJson("/api/step/apply", {
      project: step.project,
      expect: step.token,
    });
    const result = body.data && body.data.kind === "delivery-workbench-step-result"
      ? body.data : null;
    if (status === 409) {
      await viewOverview({
        kind: "stale",
        title: "stale confirmation refused — nothing started",
        detail: result ? result.reason : ((body.issues && body.issues[0]) || "Refresh and review the new lease."),
        result,
      });
      return;
    }
    if (status >= 400 || !result) {
      await viewOverview({
        kind: "failed",
        title: "step request failed — nothing else was attempted",
        detail: (body.issues && body.issues[0]) || `HTTP ${status}`,
        result,
      });
      return;
    }
    const succeeded = result.outcome === "succeeded";
    await viewOverview({
      kind: succeeded ? "succeeded" : "failed",
      title: succeeded ? "one deliberate step applied" : `step ${result.outcome}`,
      detail: result.reason || `Child exit ${result.exit_code}; started=${result.started}.`,
      result,
    });
  } catch (err) {
    await viewOverview({
      kind: "failed",
      title: "step request failed",
      detail: err.message,
      result: null,
    });
  }
}

function wireStepControl(step) {
  const review = document.getElementById("step-review");
  if (!review || !step.applicable) return;
  const openConfirmation = () => {
    const slot = document.getElementById("step-confirm");
    if (!slot) return;
    slot.innerHTML = stepConfirmationHtml(step);
    review.disabled = true;
    document.getElementById("step-apply").addEventListener("click", (event) => {
      applyReviewedStep(step, event.currentTarget);
    });
    document.getElementById("step-cancel").addEventListener("click", () => {
      slot.innerHTML = "";
      review.disabled = false;
      review.focus();
    });
  };
  review.addEventListener("click", openConfirmation);
  if (SNAPSHOT_MODE && new URLSearchParams(location.search).has("confirmstep")) {
    openConfirmation();
  }
}

function statusPanel(status, step, notice) {
  const repo = status.repository;
  const roadmap = status.roadmap;
  const changes = repo.changes;
  const action = step.action || status.next_action || {
    id: "none", kind: "manual", blocking: false,
    reason: "The briefing has no action to review.", command: null,
  };
  const manual = action.kind === "manual" || !action.command;
  const project = roadmap.selected_project || (roadmap.selection_required ? "selection required" : "none");
  const workspace = repo.clean
    ? "clean"
    : `${changes.staged.count} staged · ${changes.unstaged.count} unstaged · ${changes.untracked.count} untracked`;
  const projectLink = roadmap.selected_project
    ? `<a href="#/p/${encodeURIComponent(roadmap.selected_project)}">project</a>
       <a href="#/board/${encodeURIComponent(roadmap.selected_project)}">board</a>`
    : "";
  return `<section id="status-panel"
      class="status-panel verdict-${esc(status.verdict)}${manual ? " is-manual" : ""}${step.applicable ? "" : " is-prohibited"}"
      data-verdict="${esc(status.verdict)}" data-next-action="${esc(action.id)}"
      data-step-applicable="${step.applicable ? "true" : "false"}">
    <div class="brief-head">
      <div>
        <div class="brief-eyebrow">repository briefing</div>
        <div class="brief-verdict">${esc(status.verdict)}</div>
      </div>
      <div class="brief-summary">${esc(status.summary)}</div>
    </div>
    <div class="brief-facts">
      <div><span>project</span><strong>${esc(project)}</strong></div>
      <div><span>workspace</span><strong>${esc(workspace)}</strong></div>
      <div><span>contract</span><strong>${esc(repo.contract.state)}</strong></div>
      <div><span>gate</span><strong>${esc(repo.gate.state)}</strong></div>
    </div>
    ${stepNoticeHtml(notice)}
    ${statusActionHtml(action)}
    ${stepControlHtml(step)}
    <nav class="brief-specialists" aria-label="specialist Delivery Workbench views">
      <span>inspect deeper</span>${projectLink}<a href="#/health">health</a><a href="#/mc">mission control</a>
    </nav>
  </section>`;
}

/* ── mission control (WLA-15-01): the read-only belt ──────────────
 * The workbench is the fourth consumer of the mission-control
 * substrate (feed + sessions + events), read-only by charter — the
 * picture without the hands. A single-flight 10s poll keeps it live
 * while the view is open; leaving the view stops the poll. */

let mcPoll = null;
let mcInFlight = false;

function stopMcPoll() {
  if (mcPoll) { clearInterval(mcPoll); mcPoll = null; }
}

function mcPin(s) {
  return `<span class="mc-pin${s.awaiting_response ? " awaiting" : ""}${s.stale ? " stale" : ""}"
    title="${esc(s.key)}${s.awaiting_response ? " — awaiting a response" : ""}${s.stale ? " (stale)" : ""}">${s.awaiting_response ? "🙋" : "🤖"}${esc(s.agent)}</span>`;
}

function mcBelt(project, pins) {
  const current = project.current_phase;
  const beltStories = current
    ? project.stories.filter((s) => s.phase === current.number) : [];
  const nextId = project.next_story ? project.next_story.story_id : null;
  return `
    <div class="mc-project">
      <div class="mc-phases">
        <span class="mc-slug">${esc(project.slug)}</span>
        ${project.phases.map((ph) => `
          <span class="mc-phase${ph.status === "closed" ? " closed" : ""}${current && ph.number === current.number ? " current" : ""}"
                title="${esc(ph.title)} — ${ph.stories_done}/${ph.stories_total}">${ph.number}</span>`).join("")}
        ${project.warnings ? `<span class="mc-warn">⚠ ${project.warnings}</span>` : ""}
      </div>
      <div class="mc-belt">
        ${beltStories.map((s) => `
          <span class="mc-story st-${esc(s.status)}${s.story_id === nextId ? " next" : ""}"
                title="${esc(s.title)} [${esc(s.status)}]${s.evidence_exists ? " ·evidence" : ""}">
            <a href="#/p/${encodeURIComponent(project.slug)}/s/${encodeURIComponent(s.story_id)}">${esc(s.story_id)}</a>${s.evidence_exists ? " ✓" : ""}${(pins[s.story_id] || []).map(mcPin).join("")}
          </span>`).join("")}
      </div>
    </div>`;
}

function mcOffBelt(doc, offBelt) {
  if (!doc || doc.registry !== "ok") {
    return `<div class="sub">sessions: registry ${esc(doc ? String(doc.registry) : "unavailable")}</div>`;
  }
  if (!offBelt.length) return `<div class="sub">every live session is pinned to its story on the belt</div>`;
  return offBelt.map((s) => {
    const where = s.correlation === "ambiguous" && s.stories.length
      ? `ambiguous: ${s.stories.map((st) => st.story_id).join(", ")}`
      : s.correlation.replace(/_/g, " ");
    return `<div class="mc-session${s.awaiting_response ? " awaiting" : ""}${s.stale ? " stale" : ""}">
      <code>${esc(s.key)}</code> — ${esc(s.agent)} — ${esc(where)}
      ${s.awaiting_response ? badge("awaiting a response", "warn") : ""}
      ${s.stale ? badge("stale") : ""}
    </div>`;
  }).join("");
}

function mcEvents(events) {
  if (!events.length) return `<div class="sub">no rail events yet</div>`;
  return `<div class="mc-ticker">` + events.slice().reverse().map((e) => {
    const detail = Object.entries(e.detail || {})
      .filter(([, v]) => v !== null && v !== undefined)
      .map(([k, v]) => `${k}=${v}`).join(" ");
    const refusal = e.event === "gate_refusal";
    return `<div class="mc-event${refusal ? " refusal" : ""}">
      ${refusal ? "✕ " : ""}${esc(e.ts || "?")}  ${esc(e.event || "?")}${e.story ? `  ${esc(e.story)}` : ""}${detail ? `  ${esc(detail)}` : ""}
    </div>`;
  }).join("") + `</div>`;
}

async function loadMissionControl() {
  if (mcInFlight) return; // single-flight: a slow poll skips ticks
  mcInFlight = true;
  try {
    const body = await api("/api/missioncontrol");
    const data = body.data;
    const el = document.getElementById("mc-root");
    if (!el) { stopMcPoll(); return; } // view left; stop polling
    el.innerHTML = `
      <div class="section"><h2>the belt</h2>
        ${data.feed.projects.map((p) => mcBelt(p, data.pins || {})).join("") || stateHtml("no projects on the rails here")}
      </div>
      <div class="section"><h2>off the belt</h2>${mcOffBelt(data.sessions, data.off_belt || [])}</div>
      <div class="section"><h2>rail events</h2>${mcEvents(data.events)}</div>
      <div class="sub">read-only — the workbench never stages or commits; steering lives on the phone and the Desk.</div>`;
  } finally {
    mcInFlight = false;
  }
}

async function viewMissionControl() {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "mission control" }]);
  app.innerHTML = `<div id="mc-root">${stateHtml("Loading the belt…")}</div>`;
  await loadMissionControl();
  mcPoll = setInterval(() => { loadMissionControl().catch(() => {}); }, 10000);
}

/* ── views ─────────────────────────────────────────────────────────── */

async function viewOverview(notice = null) {
  setCrumbs([{ label: "overview" }]);
  const [statusBody, stepBody, body] = await Promise.all([
    api("/api/status"), api("/api/step"), api("/api/projects"),
  ]);
  const projects = body.data.projects;
  const step = stepBody.data;
  const briefing = statusPanel(statusBody.data, step, notice);
  if (!projects.length) {
    app.innerHTML = briefing + stateHtml("No roadmap projects found under pm/roadmap/. Scaffold one with `dw phase create` or `dw adopt`.");
    wireStepControl(step);
    return;
  }
  app.innerHTML = briefing + `<div class="grid">` + projects.map((p) => `
    <div class="card">
      <h3><a href="#/p/${encodeURIComponent(p.slug)}">${esc(p.slug)}</a>
        <span class="badge">${esc(p.prefix)}</span></h3>
      <div class="sub">${esc(p.path)}</div>
      <div class="stats">
        <span>phases <b>${p.phase_count}</b></span>
        <span>active <b>${p.active_phase_count}</b></span>
        <span>${p.issue_count ? badge(`${p.issue_count} issue${p.issue_count > 1 ? "s" : ""}`, "issue") : badge("checks ok", "ok")}</span>
        <span>${p.warning_count ? badge(`${p.warning_count} warning${p.warning_count > 1 ? "s" : ""}`, "warn") : ""}</span>
      </div>
      <div class="stats" style="margin-top:6px">${statusCounts(p.story_status_counts)}</div>
      ${p.next_story ? `
        <div class="next"><span class="lbl">next</span>
          <a href="#/p/${encodeURIComponent(p.slug)}/s/${encodeURIComponent(p.next_story.story_id)}">
            <code>${esc(p.next_story.story_id)}</code></a>
          ${esc(p.next_story.title)} ${badge(p.next_story.status)}
        </div>` : `<div class="next"><span class="lbl">next</span> nothing actionable</div>`}
    </div>`).join("") + `</div>`;
  wireStepControl(step);
}

async function viewProject(slug) {
  setCrumbs([{ label: "overview", href: "#/" }, { label: slug }]);
  const body = await api(`/api/projects/${encodeURIComponent(slug)}`);
  const p = body.data;
  const phases = p.phases.map((ph) => {
    const counts = {};
    ph.stories.forEach((s) => { counts[s.status] = (counts[s.status] || 0) + 1; });
    const evidenced = ph.stories.filter((s) => s.evidence_exists).length;
    return `<tr>
      <td><a href="#/p/${encodeURIComponent(slug)}/ph/${ph.number}"><code>${ph.number}</code> ${esc(ph.slug)}</a></td>
      <td>${ph.active ? badge("active", "in-progress") : badge("closed", "done")}</td>
      <td>${statusCounts(counts)}</td>
      <td>${evidenced}/${ph.stories.length}</td>
      <td>${ph.final_summary_exists
        ? `<a href="#/f/${encodeURIComponent(ph.final_summary)}">${badge("summary", "ok")}</a>` : "—"}</td>
    </tr>`;
  }).join("");
  app.innerHTML = `
    ${p.next_story ? `<div class="next"><span class="lbl">next</span>
      <a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(p.next_story.story_id)}">
        <code>${esc(p.next_story.story_id)}</code></a> ${esc(p.next_story.title)} ${badge(p.next_story.status)}</div>` : ""}
    <div class="section"><h2>Phases <a class="badge" href="#/board/${encodeURIComponent(slug)}">board view</a></h2>
      <div class="tblwrap"><table class="tbl">
        <tr><th>Phase</th><th>State</th><th>Stories</th><th>Evidence</th><th>Summary</th></tr>
        ${phases || '<tr><td colspan="5">no phases yet</td></tr>'}
      </table></div></div>
    ${p.issues.length ? `<div class="guard">mutations guarded — <a href="#/health">${p.issues.length} validation issue${p.issues.length === 1 ? "" : "s"}</a> must be resolved first</div>
    <div class="section"><h2>Validation issues (<a href="#/health">health console</a>)</h2>
      <ul class="plain">${p.issues.map((i) => `<li class="issue">${esc(i)}</li>`).join("")}</ul></div>` : ""}
    ${p.warnings.length ? `<div class="section"><h2>Warnings</h2>
      <ul class="plain">${p.warnings.map((w) => `<li class="warn">${esc(w)}</li>`).join("")}</ul></div>` : ""}
    <div class="section"><h2>Supplemental canon</h2>
      <ul class="plain">${p.supplemental_canon.length ? p.supplemental_canon.map((c) =>
        `<li><a href="#/f/${encodeURIComponent(c.path)}">${esc(c.path)}</a>
         <code>${esc(c.kind)} · ${esc(c.scope)}</code></li>`).join("")
        : "<li>none</li>"}</ul></div>`;
}

async function viewPhase(slug, number) {
  setCrumbs([{ label: "overview", href: "#/" },
    { label: slug, href: `#/p/${encodeURIComponent(slug)}` },
    { label: `phase ${number}` }]);
  const body = await api(`/api/projects/${encodeURIComponent(slug)}/phases/${encodeURIComponent(number)}`);
  const ph = body.data;
  const rows = ph.stories.map((s) => `<tr>
    <td><a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(s.story_id)}"><code>${esc(s.story_id)}</code></a></td>
    <td>${esc(s.title)}</td>
    <td>${badge(s.status)}${s.header_status && s.header_status !== s.status ? " " + badge("header: " + s.header_status, "issue") : ""}</td>
    <td>${s.evidence_exists ? badge("evidence", "ok") : badge("no evidence", s.status === "done" ? "issue" : "")}</td>
    <td><a href="#/f/${encodeURIComponent(s.story_path)}"><code>story</code></a>${s.evidence_exists
      ? ` · <a href="#/f/${encodeURIComponent(s.evidence_path)}"><code>evidence</code></a>` : ""}
      · <a href="#/p/${encodeURIComponent(slug)}/t/${encodeURIComponent(s.story_id)}"><code>trace</code></a></td>
  </tr>`).join("");
  app.innerHTML = `
    <div class="meta">
      <div class="kv"><div class="k">status file</div><div class="v"><a href="#/f/${encodeURIComponent(ph.status_file)}">${esc(ph.status_file)}</a></div></div>
      <div class="kv"><div class="k">state</div><div class="v">${ph.active ? "active" : "closed"}</div></div>
      <div class="kv"><div class="k">final summary</div><div class="v">${ph.final_summary_exists
        ? `<a href="#/f/${encodeURIComponent(ph.final_summary)}">${esc(ph.final_summary)}</a>` : "not written"}</div></div>
    </div>
    <div class="section"><h2>Stories (normalized from current-phase-status.md)</h2>
      <div class="tblwrap"><table class="tbl">
        <tr><th>ID</th><th>Story</th><th>Status</th><th>Evidence</th><th>Source</th></tr>
        ${rows || '<tr><td colspan="5">no stories yet</td></tr>'}
      </table></div></div>
    <div class="section"><h2>Recent commits (phase trace)</h2>
      <div id="phase-events" class="state">Loading…</div></div>
    ${ph.final_summary_content ? `<div class="section"><h2>Final summary</h2>
      <pre class="src">${esc(ph.final_summary_content)}</pre></div>` : ""}`;
  api(`/api/projects/${encodeURIComponent(slug)}/phases/${encodeURIComponent(number)}/events`).then((ev) => {
    const rows = ev.data.events.map((c) => `<tr>
      <td><code>${esc(c.date)}</code></td><td>${esc(c.subject)}
        ${c.pmo_story ? " " + badge(c.pmo_story, "ok") : ""}
        ${c.contract_digest ? ` <span class="badge" title="${esc(c.contract_digest)}">digest</span>` : ""}</td>
      <td><code>${esc(String(c.sha).slice(0, 9))}</code></td></tr>`).join("");
    document.getElementById("phase-events").outerHTML = rows
      ? `<div class="tblwrap"><table class="tbl"><tr><th>Date</th><th>Commit</th><th>SHA</th></tr>${rows}</table></div>`
      : `<div class="state">no commits touch this phase directory yet</div>`;
  }).catch(() => {
    const el = document.getElementById("phase-events");
    if (el) el.textContent = "phase commits unavailable (no git history)";
  });
}

async function viewStory(slug, storyId) {
  setCrumbs([{ label: "overview", href: "#/" },
    { label: slug, href: `#/p/${encodeURIComponent(slug)}` },
    { label: storyId }]);
  const body = await api(`/api/projects/${encodeURIComponent(slug)}/stories/${encodeURIComponent(storyId)}`);
  const s = body.data;
  app.innerHTML = `
    <div class="meta">
      <div class="kv"><div class="k">story</div><div class="v">${esc(s.story_id)} — ${esc(s.title)}</div></div>
      <div class="kv"><div class="k">status</div><div class="v">${badge(s.status)}${s.header_status && s.header_status !== s.status ? " " + badge("header: " + s.header_status, "issue") : ""}</div></div>
      <div class="kv"><div class="k">phase</div><div class="v"><a href="#/p/${encodeURIComponent(slug)}/ph/${s.phase_number}">phase ${s.phase_number}</a></div></div>
      <div class="kv"><div class="k">evidence</div><div class="v">${s.evidence_exists ? esc(s.evidence_path) : "none"}</div></div>
      <div class="kv"><div class="k">trace</div><div class="v"><a href="#/p/${encodeURIComponent(slug)}/t/${encodeURIComponent(s.story_id)}">intent → proof timeline</a></div></div>
    </div>
    <div class="section pair">
      <div><h2>story · <code>${esc(s.story_path)}</code></h2>
        <pre class="src">${esc(s.story_markdown || "(missing story file)")}</pre></div>
      <div><h2>evidence · <code>${esc(s.evidence_path || "—")}</code></h2>
        <pre class="src">${esc(s.evidence_markdown || "(no evidence file yet)")}</pre></div>
    </div>`;
}

async function viewFile(path) {
  setCrumbs([{ label: "overview", href: "#/" }, { label: path }]);
  const body = await api(`/api/file?path=${encodeURIComponent(path)}`);
  app.innerHTML = `
    <div class="section"><h2>source · <code>${esc(body.data.path)}</code> (read-only)</h2>
      <pre class="src">${esc(body.data.content)}</pre></div>`;
}


const CATEGORY_LABELS = {
  "project": "Project pointers",
  "phase": "Phases",
  "story-evidence": "Stories & evidence",
  "hook-runtime": "Hooks & runtime",
  "supplemental-canon": "Supplemental canon",
};

function healthItem(item) {
  const kindCls = item.kind === "stale-pointer" ? "issue" : (item.severity === "error" ? "issue" : "warn");
  const folders = item.phase_folders
    ? `<div class="why">phase folders: ${item.phase_folders.map((f) => `<code>${esc(f)}</code>`).join(", ")}</div>` : "";
  return `<div class="hitem">
    ${badge(item.severity, item.severity === "error" ? "issue" : "warn")}
    ${badge(item.kind, kindCls)}
    <span class="msg">${item.path ? `<a href="#/f/${encodeURIComponent(item.path)}"><code>${esc(item.path)}</code></a> — ` : ""}${esc(item.message)}</span>
    ${item.explanation ? `<div class="why">${esc(item.explanation)}</div>` : ""}
    ${folders}
  </div>`;
}

async function viewHealth() {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "health" }]);
  const body = await api("/api/health");
  const h = body.data;
  const sections = [];
  for (const proj of h.projects) {
    const byCat = {};
    proj.issues.concat(proj.warnings).forEach((item) => {
      (byCat[item.category] = byCat[item.category] || []).push(item);
    });
    const cats = Object.keys(byCat).map((cat) => `
      <div class="section"><h2>${esc(proj.slug)} · ${esc(CATEGORY_LABELS[cat] || cat)} (${byCat[cat].length})</h2>
        ${byCat[cat].map(healthItem).join("")}</div>`).join("");
    sections.push(cats || `<div class="section"><h2>${esc(proj.slug)}</h2>
      <div class="guard ok">no validation issues or warnings — mutations safe</div></div>`);
  }
  const hook = h.hook_snapshot;
  const hookRows = [
    ["pre-commit installed", hook.pre_commit_exists],
    ["post-commit installed", hook.post_commit_exists],
    ["config seam (pre-commit.config)", hook.has_config_seam],
    ["local rule seam (pre-commit.local)", hook.has_local_seam],
    ["work-log capture", hook.has_work_log_capture],
  ].map(([k, v]) => `<div class="hitem">${badge(v ? "ok" : "missing", v ? "ok" : "issue")}<span class="msg">${esc(k)}</span></div>`).join("");
  app.innerHTML = `
    <div class="guard ${h.mutation_safe ? "ok" : ""}">${h.mutation_safe
      ? "mutation-safe: no validation issues; editor operations (future) are unguarded"
      : `mutations guarded: ${h.total_issues} validation issue${h.total_issues === 1 ? "" : "s"} must be resolved in the source Markdown first`}</div>
    ${sections.join("")}
    <div class="section"><h2>Hook snapshot</h2>${hookRows}
      ${h.hook_explanations.length ? `<ul class="plain">${h.hook_explanations.map((e) => `<li class="warn">${esc(e)}</li>`).join("")}</ul>` : ""}</div>
    <div class="section"><h2>Work-log configuration (read-only)</h2>
      <div class="meta">
        <div class="kv"><div class="k">enabled</div><div class="v">${esc(h.work_log_config.enabled)}</div></div>
        <div class="kv"><div class="k">directory</div><div class="v">${esc(h.work_log_config.dir)}</div></div>
        <div class="kv"><div class="k">project slug</div><div class="v">${esc(h.work_log_config.project_slug)}</div></div>
        <div class="kv"><div class="k">exclude regex</div><div class="v">${esc(h.work_log_config.exclude_regex)}</div></div>
      </div></div>
    <div class="section"><h2>dw check (copyable)</h2>
      <div class="copybar"><button id="copy-check" type="button">copy</button></div>
      <pre class="src" id="check-output">${esc(h.check_output)}</pre></div>`;
  document.getElementById("copy-check").addEventListener("click", () => {
    navigator.clipboard.writeText(document.getElementById("check-output").textContent);
  });
}


const HOP_LABELS = {
  readme: "project README",
  phase_status: "phase status",
  story: "story",
  evidence: "evidence",
  final_summary: "final summary",
};

let traceSortAsc = false;

async function viewTrace(slug, storyId) {
  setCrumbs([{ label: "overview", href: "#/" },
    { label: slug, href: `#/p/${encodeURIComponent(slug)}` },
    { label: storyId, href: `#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(storyId)}` },
    { label: "trace" }]);
  const apiPath = `/api/projects/${encodeURIComponent(slug)}/trace/${encodeURIComponent(storyId)}`;
  const body = await api(apiPath);
  const tl = body.data;
  const chain = tl.chain.map((hop) => `
    <div class="hitem">
      ${badge(hop.exists ? "present" : "absent", hop.exists ? "ok" : "issue")}
      <span class="msg"><b>${esc(HOP_LABELS[hop.hop] || hop.hop)}</b> —
        ${hop.exists && hop.path
          ? `<a href="#/f/${encodeURIComponent(hop.path)}"><code>${esc(hop.path)}</code></a>`
          : hop.path ? `<code>${esc(hop.path)}</code> <span class="badge issue">not written yet</span>`
                     : '<span class="badge issue">no path</span>'}</span>
    </div>`).join("");
  const events = tl.events.slice();
  if (traceSortAsc) events.reverse();
  const eventRows = events.length ? events.map((ev) => `<tr>
      <td>${badge(ev.type, ev.type === "commit" ? "in-progress" : "ok")}</td>
      <td><code>${esc(ev.sort_key || ev.date)}</code></td>
      <td>${esc(ev.subject || "(no subject)")}
        ${ev.pmo_story ? " " + badge(ev.pmo_story, "ok") : ""}
        ${ev.contract_digest ? ` <span class="badge" title="${esc(ev.contract_digest)}">digest</span>` : ""}</td>
      <td>${ev.type === "commit"
        ? `<code>${esc(String(ev.sha).slice(0, 9))}</code>`
        : `<a href="#/wl/${encodeURIComponent(ev.source)}"><code>${esc(ev.source)}</code></a>`}</td>
    </tr>`).join("")
    : '<tr><td colspan="4">no commits found for this story\u2019s PMO files; no work-log entries (optional evidence \u2014 absent, not an error)</td></tr>';
  app.innerHTML = `
    <div class="guard ${tl.shipped ? "ok" : ""}">${tl.shipped
      ? `shipped: story is done and its evidence exists`
      : `not shipped: ${esc(tl.not_shipped_reason)}`}</div>
    <div class="section"><h2>Trace chain — intent to proof</h2>${chain}</div>
    <div class="section"><h2>Events (commits + work-log)
      <button id="trace-sort" type="button" class="badge" style="cursor:pointer">${traceSortAsc ? "oldest first ↑" : "newest first ↓"}</button>
      <a class="badge" href="${apiPath}" target="_blank" title="machine-readable timeline">export JSON</a></h2>
      <div class="tblwrap"><table class="tbl">
        <tr><th>Type</th><th>When</th><th>What</th><th>Source</th></tr>
        ${eventRows}
      </table></div>
      <p class="hint">work-log entries are supplementary evidence; evidence-story-NN.md
        remains the proof of record and is required before a story counts as shipped.</p></div>
    <div class="section"><h2>Agent handoff</h2>
      <div class="copybar"><button id="copy-handoff" type="button">copy</button></div>
      <pre class="src" id="handoff-text">Loading\u2026</pre></div>`;
  api(`/api/projects/${encodeURIComponent(slug)}/handoff/${encodeURIComponent(storyId)}`).then((h) => {
    document.getElementById("handoff-text").textContent = h.data.text;
  }).catch((err) => {
    document.getElementById("handoff-text").textContent = `handoff unavailable: ${err.message}`;
  });
  document.getElementById("copy-handoff").addEventListener("click", () => {
    navigator.clipboard.writeText(document.getElementById("handoff-text").textContent);
  });
  document.getElementById("trace-sort").addEventListener("click", () => {
    traceSortAsc = !traceSortAsc;
    route();
  });
}


async function viewWorklog(path) {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "work log" }]);
  const body = await api(`/api/worklog?path=${encodeURIComponent(path)}`);
  app.innerHTML = `
    <div class="guard ok">supplementary evidence \u2014 work logs never replace evidence-story-NN.md</div>
    <div class="section"><h2>work log \u00b7 <code>${esc(body.data.path)}</code> (read-only, verbatim \u2014
      excluded paths were omitted at capture time and stay omitted here)</h2>
      <pre class="src">${esc(body.data.content)}</pre></div>`;
}

/* ── the board (WLA-17-05/06) ───────────────────────────────────────
 * Kanban over the same read layer: swimlane per phase, six status
 * columns, paused lanes dimmed with their reason, closed lanes folded
 * behind a one-line receipt. Moves (WLA-17-06) construct the same
 * update_story_status intent as the editor and go through
 * /api/mutations preview → apply — the board is never a second write
 * path. Drops on paused or closed lanes refuse; a "⇄ move" affordance
 * covers keyboards and touch. */

const PARKED_COLUMNS = ["blocked", "on-hold"];

function boardCard(slug, lane, card) {
  const parked = card.status === "blocked" || card.status === "on-hold" || card.status === "paused";
  const movable = !lane.closed && !lane.paused;
  return `
    <div class="bcard st-${esc(card.status)}" ${movable ? 'draggable="true"' : ""}
         data-story="${esc(card.story_id)}" data-phase="${lane.number}"
         data-status="${esc(card.status)}" data-evidence="${card.evidence_exists ? 1 : 0}"
         title="${esc(card.title)} [${esc(card.status)}]">
      <a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(card.story_id)}"><code>${esc(card.story_id)}</code></a>${card.evidence_exists ? ' <span class="tick">✓</span>' : ""}
      ${movable ? `<button type="button" class="bmove" title="move to another column…">⇄</button>` : ""}
      <div class="bcard-title">${esc(card.title)}</div>
      ${parked ? `<div class="bcard-note">${esc(card.note || "no reason recorded")}</div>` : ""}
    </div>`;
}

function boardLane(slug, columns, lane) {
  const droppable = !lane.closed && !lane.paused;
  const cols = columns.map((col) => `
    <div class="bcol" data-col="${esc(col)}" data-phase="${lane.number}" data-droppable="${droppable ? 1 : 0}">
      <div class="bcol-head">${esc(col)} <span class="bcol-count">${lane.columns[col].length}</span></div>
      ${lane.columns[col].map((card) => boardCard(slug, lane, card)).join("")}
    </div>`).join("");
  const uncovered = lane.story_count === 0 && lane.uncovered_story_files
    ? `<span class="sub">no story table — ${lane.uncovered_story_files} story file${lane.uncovered_story_files === 1 ? "" : "s"} on disk, unlisted</span>` : "";
  const head = `
    ${lane.is_pointer ? "▶ " : ""}<a href="#/p/${encodeURIComponent(slug)}/ph/${lane.number}">phase ${lane.number} · ${esc(lane.slug)}</a>
    ${lane.paused ? `<span class="pause-banner">⏸ paused — ${esc(lane.pause_note || "no reason recorded")}</span>` : ""}
    ${lane.retired ? `<span class="sub">${lane.retired} retired row${lane.retired === 1 ? "" : "s"} not shown</span>` : ""}
    ${uncovered}`;
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

function boardNotice(text) {
  const out = document.getElementById("board-move");
  if (out) out.innerHTML = `<div class="guard">${esc(text)}</div>`;
}

/* The move panel: the same structured intent the editor builds,
 * pre-filled from a drop or the ⇄ affordance. Client mirrors of the
 * server rules gate the preview button; the server stays the
 * authority. */
function openMovePanel(slug, move) {
  const out = document.getElementById("board-move");
  if (!out) return;
  if (move.from === move.to) {
    out.innerHTML = "";
    return;
  }
  const needsReason = PARKED_COLUMNS.includes(move.to);
  const needsEvidence = move.to === "done" && !move.evidenceExists;
  out.innerHTML = `
    <form class="edit moveform" id="move-form">
      <h2>move <code>${esc(move.story)}</code>: ${esc(move.from)} → ${esc(move.to)}</h2>
      ${needsReason ? field("reason (required for a park — recorded in the status cell)",
        '<input type="text" name="reason" placeholder="why is this waiting?">') : ""}
      ${move.to === "done" ? field(
        `evidence body ${move.evidenceExists ? "(evidence exists — leave empty to keep it)" : "(required — no evidence exists yet)"}`,
        '<textarea name="evidence_body" placeholder="- proof line…"></textarea>') : ""}
      <button type="submit">preview — no files are written</button>
      <button type="button" id="move-cancel">cancel</button>
      <div class="hint">the move goes through the same preview → apply mutation flow as the editor; the fingerprint refuses stale previews.</div>
    </form>
    <div id="move-out"></div>`;
  document.getElementById("move-cancel").addEventListener("click", () => { out.innerHTML = ""; });
  const form = document.getElementById("move-form");
  const runMovePreview = async () => {
    const moveOut = document.getElementById("move-out");
    const reason = form.elements.reason ? form.elements.reason.value.trim() : "";
    const evidenceBody = form.elements.evidence_body ? form.elements.evidence_body.value.trim() : "";
    if (needsReason && !reason) {
      moveOut.innerHTML = `<div class="guard">refused client-side: a hold needs its why — fill the reason before previewing.</div>`;
      return;
    }
    if (needsEvidence && !evidenceBody) {
      moveOut.innerHTML = `<div class="guard">refused client-side: marking ${esc(move.story)} done requires evidence — none exists and no evidence body was provided.</div>`;
      return;
    }
    const body = {
      kind: "update_story_status", project: slug, phase: String(move.phase),
      story: move.story, status: move.to,
    };
    if (reason) body.reason = reason;
    if (evidenceBody) body.evidence_body = evidenceBody;
    moveOut.innerHTML = stateHtml("Previewing…");
    const { status, body: payload } = await postJson("/api/mutations/preview", body);
    if (status >= 400 || payload.ok === false) {
      const msg = (payload.data && payload.data.error) || (payload.issues && payload.issues[0]) || `error ${status}`;
      moveOut.innerHTML = `<div class="guard">${esc(msg)}</div>`;
      return;
    }
    const d = payload.data;
    moveOut.innerHTML = `
      <div class="section"><h2>Preview ${badge("nothing written yet", "ok")}</h2>
        ${d.files.filter((f) => f.changed || f.action === "create").map((f) => `
          <details class="filepreview" open>
            <summary>${badge(f.action === "create" ? "new file" : "changed", f.action === "create" ? "ok" : "in-progress")}
              <code>${esc(f.path)}</code></summary>
            ${f.action === "create" ? `<pre class="src">${esc(f.new_content || "")}</pre>`
              : `<pre class="diff">${diffHtml(f.diff || "")}</pre>`}
          </details>`).join("")}
        <button type="button" class="applybtn" id="move-apply">apply — writes the files above (no commit)</button>
      </div>`;
    document.getElementById("move-apply").addEventListener("click", async () => {
      document.getElementById("move-apply").disabled = true;
      const { status: st, body: applied } = await postJson("/api/mutations/apply", { ...body, fingerprint: d.fingerprint });
      if (st === 409) {
        moveOut.innerHTML = `<div class="guard">stale preview refused — the source files changed after this preview; nothing was written. Re-open the move for a fresh preview.</div>`;
        return;
      }
      if (st >= 400 || applied.ok === false) {
        const msg = (applied.data && applied.data.error) || `apply failed (${st})`;
        moveOut.innerHTML = `<div class="guard">${esc(msg)}${applied.data && applied.data.rolled_back ? " — all writes were rolled back" : ""}</div>`;
        return;
      }
      route(); // re-read the board from Markdown
    });
  };
  form.addEventListener("submit", (e) => { e.preventDefault(); runMovePreview(); });
  out.scrollIntoView({ block: "nearest" });
  if (SNAPSHOT_MODE && new URLSearchParams(location.search).has("autopreview")) {
    runMovePreview();
  }
}

function wireBoardMoves(slug) {
  const board = document.querySelector(".board");
  if (!board) return;
  let dragging = null;
  board.addEventListener("dragstart", (e) => {
    const card = e.target.closest && e.target.closest(".bcard[draggable]");
    if (!card) return;
    dragging = card.dataset;
    e.dataTransfer.setData("text/plain", card.dataset.story);
    e.dataTransfer.effectAllowed = "move";
  });
  board.addEventListener("dragover", (e) => {
    if (!dragging) return;
    const col = e.target.closest && e.target.closest(".bcol");
    if (col) e.preventDefault();
  });
  board.addEventListener("drop", (e) => {
    if (!dragging) return;
    const col = e.target.closest && e.target.closest(".bcol");
    if (!col) return;
    e.preventDefault();
    const from = dragging;
    dragging = null;
    if (col.dataset.droppable !== "1") {
      boardNotice("this lane refuses drops: it is paused or closed — resume the phase (dw phase resume / the edit view) before moving its stories.");
      return;
    }
    if (col.dataset.phase !== from.phase) {
      boardNotice("a story moves between columns of its own phase — the board never moves stories across phases.");
      return;
    }
    openMovePanel(slug, {
      story: from.story, phase: from.phase, from: from.status,
      to: col.dataset.col, evidenceExists: from.evidence === "1",
    });
  });
  board.addEventListener("click", (e) => {
    const btn = e.target.closest && e.target.closest(".bmove");
    if (!btn) return;
    const card = btn.closest(".bcard");
    const colNames = PARKED_COLUMNS.concat(["backlog", "ready", "in-progress", "done"]);
    const target = prompt(`move ${card.dataset.story} to which column?\n(${colNames.join(" | ")})`, "");
    if (!target) return;
    const to = target.trim().toLowerCase();
    if (!colNames.includes(to)) {
      boardNotice(`unknown column: ${to}`);
      return;
    }
    openMovePanel(slug, {
      story: card.dataset.story, phase: card.dataset.phase,
      from: card.dataset.status, to, evidenceExists: card.dataset.evidence === "1",
    });
  });
}

async function viewBoard(slug) {
  if (!slug) {
    const ctx = await api("/api/projects");
    const projects = ctx.data.projects;
    if (!projects.length) {
      app.innerHTML = stateHtml("No roadmap projects found under pm/roadmap/.");
      return;
    }
    slug = projects[0].slug;
    if (projects.length > 1) {
      location.hash = `#/board/${encodeURIComponent(slug)}`;
      return;
    }
  }
  setCrumbs([{ label: "overview", href: "#/" },
    { label: slug, href: `#/p/${encodeURIComponent(slug)}` },
    { label: "board" }]);
  const body = await api(`/api/projects/${encodeURIComponent(slug)}/board`);
  const model = body.data;
  const open = model.phases.filter((lane) => !lane.closed);
  const closed = model.phases.filter((lane) => lane.closed);
  app.innerHTML = `
    <div class="board">
      <div id="board-move"></div>
      ${open.map((lane) => boardLane(slug, model.columns, lane)).join("") || stateHtml("no open phases")}
      ${closed.length ? `<div class="section"><h2>closed phases (${closed.length})</h2>
        ${closed.map((lane) => boardLane(slug, model.columns, lane)).join("")}</div>` : ""}
    </div>`;
  wireBoardMoves(slug);
  // Screenshot affordance (mirrors the editor's autopreview): ?snapshot=1
  // &automove=<story>:<column> opens the move panel synchronously.
  if (SNAPSHOT_MODE) {
    const automove = new URLSearchParams(location.search).get("automove");
    if (automove) {
      const [story, to] = automove.split(":");
      const card = document.querySelector(`.bcard[data-story="${story}"]`);
      if (card && to) {
        openMovePanel(slug, {
          story, phase: card.dataset.phase, from: card.dataset.status,
          to, evidenceExists: card.dataset.evidence === "1",
        });
      }
    }
  }
}

/* ── structured editor (WLA-5-06) ───────────────────────────────────
 * The editor constructs structured intent and POSTs it to
 * /api/mutations/preview. It never applies: the apply/diff workflow
 * is WLA-5-07. Client-side checks catch the obvious before the
 * server's authoritative refusals. */

const EDIT_ACTIONS = {
  create_phase: "create phase",
  create_story: "create story",
  update_story_status: "update story status",
  attach_evidence: "attach evidence",
  close_phase: "close phase",
};

const STATUS_VOCAB = ["backlog", "ready", "in-progress", "blocked", "on-hold", "done"];

function field(label, inner, err) {
  return `<label><b>${esc(label)}</b>${inner}
    <span class="fielderr" data-err="${esc(label)}">${err ? esc(err) : ""}</span></label>`;
}

function selectHtml(name, options, selected) {
  return `<select name="${name}">` + options.map((o) =>
    `<option value="${esc(o)}"${o === selected ? " selected" : ""}>${esc(o)}</option>`).join("") + "</select>";
}

async function viewEdit(action) {
  action = action || "create_story";
  setCrumbs([{ label: "overview", href: "#/" }, { label: "edit" }, { label: EDIT_ACTIONS[action] || action }]);
  const ctx = await api("/api/projects");
  const projects = ctx.data.projects;
  if (!projects.length) {
    app.innerHTML = stateHtml("No projects to edit.");
    return;
  }
  const proj = projects[0];
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

  app.innerHTML = `
    <div class="tabs">${tabs}</div>
    ${guarded ? `<div class="guard">mutations guarded — <a href="#/health">${proj.issue_count} validation issue${proj.issue_count === 1 ? "" : "s"}</a>.
      Preview requires explicit acknowledgment below.</div>` : ""}
    <form class="edit" id="edit-form">
      ${field("project", selectHtml("project", projects.map((x) => x.slug), proj.slug))}
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
  runError: "", runPlan: null, runAct: null, runStream: null,
  grantDraft: { project: "", story: "", operator: "", minutes: 60 },
  controlReason: "",
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
  if (!p) return stateHtml("Waiting for the shared compiler…");
  const diagnostics = p.validation?.diagnostics || [];
  if (!p.valid) return `<div class="orch-validation invalid" aria-live="polite"><h2>Compiler refused this score ${badge(`${diagnostics.length} issue${diagnostics.length === 1 ? "" : "s"}`, "issue")}</h2>
    <ol class="orch-diagnostics">${diagnostics.map((d) => `<li data-pointer="${esc(d.pointer)}"><code>${esc(d.pointer)}</code><strong>${esc(d.code)}</strong><span>${esc(d.message)}</span><small>${esc(d.remediation)}</small></li>`).join("")}</ol></div>`;
  const c = p.compiled;
  const s = p.simulation;
  return `<div class="orch-validation valid" aria-live="polite">
    <div class="orch-hashes"><div><span>semantic hash</span><code>${esc(c.semantic_hash)}</code></div><div><span>document hash</span><code>${esc(c.document_hash)}</code></div></div>
    <div class="orch-validate-grid">
      <section><h3>capability request</h3>${c.analysis.capabilities.map((x) => badge(x, "warn")).join(" ") || "none"}<h3>logical profiles</h3>${c.analysis.profiles.map((x) => badge(x)).join(" ") || "none"}</section>
      <section><h3>finite budgets</h3>${Object.entries(s.budgets).map(([k, v]) => `<div class="kv"><div class="k">${esc(k)}</div><div class="v">${esc(v)}</div></div>`).join("")}</section>
    </div>
    <section><h3>scheduling simulation ${badge("pure — starts nothing", "ok")}</h3><div class="orch-waves">${s.waves.map((w) => `<div><strong>wave ${w.wave}</strong><span>${w.scheduled.map((x) => `<code>${esc(x)}</code>`).join(" ")}</span><small>eligible: ${esc(w.eligible.join(", "))}${w.resource_groups.length ? ` · locks: ${esc(w.resource_groups.join(", "))}` : ""}</small></div>`).join("")}</div></section>
    <section><h3>output lineage</h3><div class="tablewrap"><table><thead><tr><th>artifact</th><th>producer</th><th>format</th><th>consumers</th><th>conventions</th></tr></thead><tbody>${s.output_lineage.map((o) => `<tr><td><code>${esc(o.name)}</code></td><td>${esc(o.producer)}</td><td>${esc(o.format)}</td><td>${esc(o.consumers.join(", ") || "—")}</td><td>${o.citations === "required" ? "citations · " : ""}${o.required_sections.length ? esc(o.required_sections.join(", ")) : `${esc(o.max_bytes)} bytes`}</td></tr>`).join("") || '<tr><td colspan="5">no declared artifacts</td></tr>'}</tbody></table></div></section>
    <section><h3>failure routes and checkpoints</h3>${s.failure_branches.map((b) => `<div class="orch-branch"><code>${esc(b.source)}</code><strong>${esc(b.action)}</strong><span>${esc(b.node || b.checkpoint || "terminal policy")}</span></div>`).join("") || "none"}<div class="orch-terminals">${s.terminals.map((t) => `${badge(t.node)} → ${badge(t.meaning, "ok")}`).join(" ")}</div></section>
  </div>`;
}

function jsonView() {
  const text = orchState.jsonDraft || JSON.stringify(orchState.score, null, 2);
  return `<div class="orch-json"><div class="orch-json-actions"><label class="filebtn">import JSON<input type="file" id="orch-import" accept="application/json,.json"></label><button type="button" id="orch-json-to-graph">apply JSON to graph</button></div>
    <label><span>lossless score document</span><textarea id="orch-json-text" spellcheck="false">${esc(text)}</textarea></label>
    <div id="orch-json-error" class="guard" hidden></div><p class="hint">Unknown schema fields are preserved in this text and refused by the compiler; they are never silently dropped.</p></div>`;
}

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
  const available = (view.controls || []).filter((control) => control.available);
  const unavailable = (view.controls || []).filter((control) => !control.available);
  if (view.terminal) return `<section class="run-controls terminal"><div><span>terminal handoff</span><strong>${esc(view.state)}</strong></div><p>${esc(view.terminal_meaning)}</p><p class="guard">No certification, commit, elevation, retry, or apply control is exposed in this state.</p></section>`;
  return `<section class="run-controls"><div class="run-control-head"><div><span>separate act boundary</span><strong>Preview, inspect, then confirm exactly one control</strong></div>${badge("no automatic continuation", "warn")}</div>
    ${available.some((control) => control.reason_required) ? `<label class="run-reason">operator reason<input id="run-control-reason" value="${esc(orchState.controlReason)}" placeholder="bounded reason, required"></label>` : ""}
    <div class="run-control-buttons">${available.map((control) => `<button type="button" data-run-act="${esc(control.action)}" data-run-decision="${esc(control.decision)}" class="${control.action === "cancel" || control.decision === "reject" ? "danger" : control.starts_work ? "starts-work" : ""}">preview ${esc(control.action)}${control.decision ? ` · ${esc(control.decision)}` : ""}${control.starts_work ? " (may start work)" : ""}</button>`).join("") || '<span class="hint">No bounded control is applicable.</span>'}</div>
    <div class="run-unavailable">${unavailable.map((control) => `<div><strong>${esc(control.action)}${control.decision ? ` · ${esc(control.decision)}` : ""}</strong><span>${esc((control.issues || []).join("; "))}</span></div>`).join("")}</div>
  </section>`;
}

function runActPreviewHtml(preview) {
  if (!preview) return "";
  return `<section class="run-consent ${preview.applicable ? "" : "refused"}" aria-live="polite"><div class="run-consent-head"><div><span>exact control preview</span><strong>${esc(preview.action)}${preview.decision ? ` · ${esc(preview.decision)}` : ""}</strong></div>${badge(preview.starts_work ? "may start bounded work" : "one ledger act", preview.starts_work ? "warn" : "ok")}</div>
    <div class="run-token"><span>state + intent token</span><code>${esc(preview.act_token)}</code></div><p>Observed <code>${esc(preview.state)}</code> at generation ${esc(preview.control_generation)} and ledger <code>${esc(preview.ledger_head)}</code>.</p>
    ${preview.reason ? `<p><strong>bound reason:</strong> ${esc(preview.reason)}</p>` : ""}${(preview.issues || []).map((issue) => `<p class="guard">${esc(issue)}</p>`).join("")}
    <div class="run-consent-actions">${preview.applicable ? '<button type="button" id="run-act-confirm">confirm this exact act</button>' : ""}<button type="button" id="run-act-close">close preview</button></div>
    <small>Any ledger change, action change, decision change, or reason change invalidates this token.</small></section>`;
}

function runStreamHtml(stream) {
  if (!stream) return "";
  return `<section class="run-open-stream" aria-live="polite"><div><strong>${esc(stream.executor)} · ${esc(stream.execution_id)} · ${esc(stream.stream)}</strong><button type="button" id="run-stream-close">close explicit stream</button></div><small>${esc(stream.included_bytes)} / ${esc(stream.bytes)} bytes · ${stream.truncated ? "truncated" : "complete"} · ${esc(stream.sha256)}</small><pre>${esc(stream.content)}</pre></section>`;
}

function grantPreviewHtml(plan) {
  if (!plan) return "";
  return `<section class="run-consent ${plan.applicable ? "" : "refused"}" aria-live="polite"><div class="run-consent-head"><div><span>immutable grant preview</span><strong>${esc(plan.story.id)} · ${esc(plan.score.slug)}</strong></div>${badge("starts no work", "ok")}</div>
    <div class="run-token"><span>single-use start token</span><code>${esc(plan.start_token)}</code></div>
    <div class="run-grant-facts"><div><span>repository</span><code>${esc(plan.repository.branch)} · ${esc(plan.repository.head)}</code></div><div><span>expiry</span><strong>${esc(plan.request.expires_at)}</strong></div><div><span>capabilities</span><strong>${esc(plan.authority.capabilities.join(", ") || "none")}</strong></div><div><span>profiles / workspaces</span><strong>${esc(plan.authority.profiles.join(", ") || "none")} · ${esc(plan.authority.workspace_modes.join(", ") || "none")}</strong></div></div>
    ${runBudgetHtml(Object.fromEntries(Object.entries(plan.authority.budgets).map(([key, value]) => [key, { used: 0, limit: value }]))) }
    ${(plan.issues || []).map((issue) => `<p class="guard">${esc(issue)}</p>`).join("")}
    <div class="run-consent-actions">${plan.applicable ? '<button type="button" id="run-start-confirm">grant authority and create run — dispatch nothing</button>' : ""}<button type="button" id="run-plan-close">close preview</button></div></section>`;
}

function runEmptyHtml() {
  const draft = orchState.grantDraft;
  return `<div class="run-empty"><section><span class="orch-eyebrow">score ≠ authority</span><h2>No local run for this score</h2><p>Saving and validating this score starts nothing. Build a grant preview from current repository, story, score, capability, budget, and expiry facts; only a second explicit confirmation creates immutable local authority.</p>${badge("preview is pure", "ok")} ${badge("grant dispatches nothing", "warn")}</section>
    <form id="run-grant-form" class="run-grant-form"><label>project slug<input name="project" required value="${esc(draft.project || orchState.score.project || "")}"></label><label>in-progress story id<input name="story" required value="${esc(draft.story)}" placeholder="WLA-24-07"></label><label>operator identity<input name="operator" required value="${esc(draft.operator)}" placeholder="human or accountable agent"></label><label>grant minutes<input name="minutes" type="number" min="1" max="1440" value="${esc(draft.minutes || 60)}"></label><button type="submit">preview exact grant</button></form>${grantPreviewHtml(orchState.runPlan)}</div>`;
}

function runViewHtml() {
  if (orchState.runLoading) return `<div class="orch-run-shell">${stateHtml("Replaying the authoritative run ledger…")}</div>`;
  const error = orchState.runError ? `<div class="guard run-error" role="alert">${esc(orchState.runError)}</div>` : "";
  if (!orchState.runs.length || !orchState.runView) return `<div class="orch-run-shell">${error}${runEmptyHtml()}</div>`;
  const view = orchState.runView;
  return `<div class="orch-run-shell" data-run-id="${esc(view.run_id)}">${error}<header class="run-toolbar"><div><span class="orch-eyebrow">live run · ledger replay</span><h2>${esc(view.run_id)} ${runStateBadge(view.state)}</h2><p>${esc(view.story.id)} · ${esc(view.story.title)} · expires ${esc(view.expires_at)}</p></div><div><label>run<select id="run-select">${orchState.runs.map((item) => `<option value="${esc(item.run_id)}"${item.run_id === view.run_id ? " selected" : ""}>${esc(item.run_id)} · ${esc(item.run.state)}</option>`).join("")}</select></label><button type="button" id="run-refresh">refresh once</button></div></header>
    <div class="run-summary"><div><span>state</span><strong>${esc(view.state)}</strong><small>${esc(view.terminal_meaning)}</small></div><div><span>ledger</span><strong>${esc(view.ledger_events)} events</strong><code>${esc(view.ledger_head)}</code></div><div><span>attempts</span><strong>${esc(view.attempts.active.length)} active · ${esc(view.attempts.completed.length)} complete</strong><small>generation ${esc(view.control_generation)}</small></div><div><span>authority</span><strong>${view.dispatch_allowed ? "dispatch permitted" : "dispatch stopped"}</strong><small>${view.expired ? "grant expired" : "grant fresh by time"}</small></div></div>
    ${runBudgetHtml(view.budgets)}
    <section class="run-panel"><div class="run-panel-head"><div><span>authoritative graph state</span><strong>Why every node is waiting, eligible, active, failed, or complete</strong></div>${badge("inspection is pure", "ok")}</div>${liveRunGraph(view)}</section>
    <section class="run-panel"><div class="run-panel-head"><div><span>executors and fail checks</span><strong>Sessions expose receipts and bounded streams, never prompts or commands</strong></div></div>${runSessionsHtml(view)}${runStreamHtml(orchState.runStream)}</section>
    <section class="run-panel"><div class="run-panel-head"><div><span>declared output conventions</span><strong>Artifact metadata and lineage</strong></div></div>${runArtifactHtml(view)}</section>
    <section class="run-panel">${runRoutesHtml(view)}</section>
    ${runControlsHtml(view)}${runActPreviewHtml(orchState.runAct)}
    <section class="run-panel"><div class="run-panel-head"><div><span>hash-chained receipts</span><strong>Run ledger timeline</strong></div>${badge("content-safe metadata", "ok")}</div>${runTimelineHtml(view)}</section>
  </div>`;
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
  const current = orchState.name || orchState.score.slug;
  app.innerHTML = `<div class="orchestration" data-score="${esc(current)}">
    <header class="orch-toolbar"><div><span class="orch-eyebrow">visual orchestration score</span><h1>${esc(orchState.score.title || orchState.score.slug)}</h1><code>pm/orchestration/${esc(orchState.score.slug)}.json</code></div>
      <div class="orch-score-actions"><label>score<select id="orch-score-select"><option value="">new unsaved score</option>${orchState.inventory.map((s) => `<option value="${esc(s.name)}"${s.name === orchState.name ? " selected" : ""}>${esc(s.slug || s.name)}${s.valid ? "" : " (invalid)"}</option>`).join("")}</select></label><button type="button" id="orch-new">new</button><button type="button" id="orch-duplicate">duplicate</button><button type="button" id="orch-preview-save">preview save</button><button type="button" id="orch-preview-delete" class="danger"${orchState.exists ? "" : " disabled"}>preview delete</button></div>
    </header>
    <nav class="orch-tabs" aria-label="orchestration editor views">${[
      ["design", "Design"], ["validate", "Validate"], ["json", "JSON"], ["run", "Run"],
    ].map(([id, label]) => `<button type="button" data-orch-view="${id}" class="${orchState.view === id ? "active" : ""}">${label}${id === "validate" && orchState.preview && !orchState.preview.valid ? ` (${orchState.preview.validation.diagnostics.length})` : ""}</button>`).join("")}</nav>
    <div id="orch-save-panel" aria-live="polite"></div>
    <div id="orch-view">${orchestrationBody()}</div>
  </div>`;
  wireOrchestration();
}

async function refreshOrchValidation() {
  if (!orchState.score) return;
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
  panel.innerHTML = `<div class="orch-save-preview"><div class="orch-preview-head"><strong>${esc(preview.action)} preview</strong>${badge(preview.applicable ? "nothing written yet" : "compiler blocked apply", preview.applicable ? "ok" : "issue")}<code>${esc(preview.fingerprint)}</code></div>
    ${diagnostics.length ? `<ol class="orch-diagnostics">${diagnostics.map((d) => `<li><code>${esc(d.pointer)}</code><strong>${esc(d.code)}</strong><span>${esc(d.message)}</span><small>${esc(d.remediation)}</small></li>`).join("")}</ol>` : ""}
    ${preview.diff ? `<pre class="diff">${diffHtml(preview.diff)}</pre>` : `<p class="hint">${preview.no_op ? "No content change." : "No diff is available until the score compiles."}</p>`}
    <div class="orch-preview-actions">${preview.applicable ? `<button type="button" id="orch-apply-score">apply exact ${esc(preview.action)} — no run, stage, or commit</button>` : ""}<button type="button" id="orch-close-preview">close</button></div></div>`;
  document.getElementById("orch-close-preview").addEventListener("click", () => { panel.innerHTML = ""; });
  document.getElementById("orch-apply-score")?.addEventListener("click", async (e) => {
    e.currentTarget.disabled = true;
    const { status, body } = await postJson("/api/orchestration/apply", { ...request, fingerprint: preview.fingerprint });
    if (status === 409) { panel.innerHTML = '<div class="guard">stale score preview refused — nothing was written. Preview the current score again.</div>'; return; }
    if (status >= 400 || body.ok === false) { panel.innerHTML = `<div class="guard">${esc((body.issues && body.issues[0]) || `apply failed (${status})`)}</div>`; return; }
    if (request.action === "delete") { location.hash = "#/orchestration"; await viewOrchestration(); return; }
    orchState.exists = true; orchState.name = request.name; location.hash = `#/orchestration/${encodeURIComponent(request.name)}`; await viewOrchestration(request.name);
  });
}

async function previewScoreAction(action) {
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

function selectScoreRuns() {
  const slug = orchState.score?.slug;
  orchState.runs = (orchState.runInventory || []).filter((item) => item.valid && item.run?.score?.slug === slug);
  if (!orchState.runs.some((item) => item.run_id === orchState.runId)) {
    orchState.runId = orchState.runs.length ? orchState.runs[orchState.runs.length - 1].run_id : "";
    orchState.runView = null;
  }
}

async function refreshRunData() {
  orchState.runLoading = true; orchState.runError = ""; renderOrchestration();
  try {
    const inventory = await api("/api/runs");
    orchState.runInventory = inventory.data.runs || [];
    selectScoreRuns();
    orchState.runView = orchState.runId ? (await api(`/api/runs/${encodeURIComponent(orchState.runId)}/view`)).data : null;
  } catch (err) {
    orchState.runError = err.message; orchState.runView = null;
  } finally {
    orchState.runLoading = false; renderOrchestration();
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

function startRunLive() {
  stopRunLive();
  if (!orchState.runId || orchState.view !== "run" || typeof EventSource === "undefined") return;
  const runId = orchState.runId;
  runLive = new EventSource(`/api/runs/${encodeURIComponent(runId)}/events`);
  runLive.addEventListener("ledger", () => {
    if (runLiveTimer) return;
    runLiveTimer = setTimeout(async () => {
      runLiveTimer = null;
      if (orchState.runId !== runId || orchState.view !== "run") return;
      try {
        orchState.runView = (await api(`/api/runs/${encodeURIComponent(runId)}/view`)).data;
        renderOrchestration();
      } catch (err) { /* keep the last rendered view; refresh stays manual */ }
    }, 400);
  });
  runLive.onerror = () => { stopRunLive(); };
}

async function previewRunGrant(form) {
  const values = Object.fromEntries(new FormData(form).entries());
  const minutes = Math.max(1, Math.min(1440, Number(values.minutes) || 60));
  orchState.grantDraft = { project: String(values.project || "").trim(), story: String(values.story || "").trim(), operator: String(values.operator || "").trim(), minutes };
  orchState.runError = ""; orchState.runPlan = null; renderOrchestration();
  const issued = new Date(); const expires = new Date(issued.getTime() + minutes * 60_000);
  const params = new URLSearchParams({ score: orchState.score.slug, project: orchState.grantDraft.project, story: orchState.grantDraft.story, issued_at: issued.toISOString(), expires_at: expires.toISOString() });
  try { orchState.runPlan = (await api(`/api/run-plan?${params}`)).data; }
  catch (err) { orchState.runError = err.message; }
  renderOrchestration();
}

async function confirmRunGrant() {
  const plan = orchState.runPlan;
  if (!plan?.applicable) return;
  const request = {
    score: plan.request.score, project: plan.request.project, story: plan.request.story,
    issued_at: plan.request.issued_at, expires_at: plan.request.expires_at,
    expect: plan.start_token, approve: true, operator: orchState.grantDraft.operator,
  };
  orchState.runLoading = true; renderOrchestration();
  const { status, body } = await postJson("/api/runs/start", request);
  orchState.runLoading = false;
  if (status === 409) { orchState.runPlan = null; orchState.runError = "Stale grant preview refused. Repository, score, story, or time facts changed; build a fresh preview."; renderOrchestration(); return; }
  if (status >= 400 || body.ok === false) { orchState.runError = (body.issues && body.issues[0]) || `run start failed (${status})`; renderOrchestration(); return; }
  orchState.runId = body.data.run_id; orchState.runPlan = null; await refreshRunData();
}

async function previewRunAct(action, decision) {
  const control = (orchState.runView?.controls || []).find((item) => item.action === action && String(item.decision || "") === String(decision || ""));
  const reason = control?.reason_required ? orchState.controlReason.trim() : "";
  orchState.runAct = null; orchState.runError = ""; renderOrchestration();
  const { status, body } = await postJson("/api/runs/preview", { run_id: orchState.runId, action, ...(reason ? { reason } : {}), ...(decision ? { decision } : {}) });
  if (status >= 400 || body.ok === false) { orchState.runError = (body.issues && body.issues[0]) || `run preview failed (${status})`; }
  else orchState.runAct = body.data;
  renderOrchestration();
}

async function confirmRunAct() {
  const preview = orchState.runAct;
  if (!preview?.applicable) return;
  const request = { run_id: preview.run_id, expect: preview.act_token, ...(preview.reason ? { reason: preview.reason } : {}), ...(preview.decision ? { decision: preview.decision } : {}) };
  orchState.runLoading = true; renderOrchestration();
  const { status, body } = await postJson(`/api/runs/${encodeURIComponent(preview.action)}`, request);
  orchState.runLoading = false;
  if (status === 409) { orchState.runAct = null; orchState.runError = "Stale run act refused before work or ledger change. Refresh once and preview the current state."; renderOrchestration(); return; }
  if (status >= 400 || body.ok === false) { orchState.runError = (body.issues && body.issues[0]) || `run act failed (${status})`; renderOrchestration(); return; }
  orchState.runAct = null; orchState.controlReason = ""; await refreshRunData();
}

async function openRunStream(button) {
  orchState.runStream = null; renderOrchestration();
  const path = `/api/runs/${encodeURIComponent(orchState.runId)}/streams/${encodeURIComponent(button.dataset.executor)}/${encodeURIComponent(button.dataset.executionId)}/${encodeURIComponent(button.dataset.runStream)}?max_bytes=20000`;
  try { orchState.runStream = (await api(path)).data; }
  catch (err) { orchState.runError = err.message; }
  renderOrchestration();
}

function wireRunView() {
  document.getElementById("run-refresh")?.addEventListener("click", refreshRunData);
  document.getElementById("run-select")?.addEventListener("change", async (event) => { orchState.runId = event.target.value; orchState.runAct = null; orchState.runStream = null; await refreshRunData(); });
  document.getElementById("run-grant-form")?.addEventListener("submit", (event) => { event.preventDefault(); previewRunGrant(event.currentTarget); });
  document.getElementById("run-start-confirm")?.addEventListener("click", confirmRunGrant);
  document.getElementById("run-plan-close")?.addEventListener("click", () => { orchState.runPlan = null; renderOrchestration(); });
  document.getElementById("run-control-reason")?.addEventListener("input", (event) => { orchState.controlReason = event.target.value; });
  document.querySelectorAll("[data-run-act]").forEach((button) => button.addEventListener("click", () => previewRunAct(button.dataset.runAct, button.dataset.runDecision)));
  document.getElementById("run-act-confirm")?.addEventListener("click", confirmRunAct);
  document.getElementById("run-act-close")?.addEventListener("click", () => { orchState.runAct = null; renderOrchestration(); });
  document.querySelectorAll("[data-run-stream]").forEach((button) => button.addEventListener("click", () => openRunStream(button)));
  document.getElementById("run-stream-close")?.addEventListener("click", () => { orchState.runStream = null; renderOrchestration(); });
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
  selectScoreRuns();
  const requestedView = new URLSearchParams(location.search).get("orchview");
  if (["design", "validate", "json", "run"].includes(requestedView)) orchState.view = requestedView;
  if (orchState.view === "run" && orchState.runId) {
    try { orchState.runView = (await api(`/api/runs/${encodeURIComponent(orchState.runId)}/view`)).data; }
    catch (err) { orchState.runError = err.message; orchState.runView = null; }
    startRunLive();
  }
  renderOrchestration();
  await refreshOrchValidation();
}

/* ── router ─────────────────────────────────────────────────────────── */

async function route() {
  stopMcPoll(); // leaving mission control stops its poll
  stopRunLive(); // leaving the run view closes its live tail
  app.innerHTML = stateHtml("Loading…");
  const hash = decodeURIComponent(location.hash.replace(/^#/, "")) || "/";
  const parts = hash.split("/").filter(Boolean);
  try {
    if (!parts.length) return await viewOverview();
    if (parts[0] === "p" && parts.length === 2) return await viewProject(parts[1]);
    if (parts[0] === "p" && parts[2] === "ph") return await viewPhase(parts[1], parts[3]);
    if (parts[0] === "p" && parts[2] === "s") return await viewStory(parts[1], parts[3]);
    if (parts[0] === "p" && parts[2] === "t") return await viewTrace(parts[1], parts[3]);
    if (parts[0] === "wl") return await viewWorklog(parts.slice(1).join("/"));
    if (parts[0] === "board") return await viewBoard(parts[1]);
    if (parts[0] === "orchestration") return await viewOrchestration(parts[1]);
    if (parts[0] === "edit") return await viewEdit(parts[1]);
    if (parts[0] === "health") return await viewHealth();
    if (parts[0] === "mc") return await viewMissionControl();
    if (parts[0] === "f") return await viewFile(parts.slice(1).join("/"));
    app.innerHTML = stateHtml(`Unknown view: ${hash}`, true);
  } catch (err) {
    app.innerHTML = stateHtml(err.message, true);
  }
}

document.getElementById("refresh-btn").addEventListener("click", route);
window.addEventListener("hashchange", route);

api("/api/context").then((body) => {
  footRoot.textContent = body.data.root;
}).catch(() => {});
route();
