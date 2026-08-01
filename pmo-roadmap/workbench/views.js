"use strict";


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
    title="${s.awaiting_response ? "A decision is waiting" : "Team activity"}${s.stale ? " (update may be stale)" : ""}">${s.awaiting_response ? "🙋" : "🤖"}${esc(s.agent)}</span>`;
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
    return `<div class="sub">Team activity is unavailable.</div>`;
  }
  if (!offBelt.length) return `<div class="sub">Every live team activity is matched to current work.</div>`;
  return offBelt.map((s) => {
    const where = s.correlation === "ambiguous" && s.stories.length
      ? `ambiguous: ${s.stories.map((st) => st.story_id).join(", ")}`
      : s.correlation.replace(/_/g, " ");
    return `<div class="mc-session${s.awaiting_response ? " awaiting" : ""}${s.stale ? " stale" : ""}">
      <strong>${esc(s.agent)}</strong> — ${esc(where)}
      ${s.awaiting_response ? badge("awaiting a response", "warn") : ""}
      ${s.stale ? badge("stale") : ""}
      <details><summary>Technical details</summary><code>${esc(s.key)}</code></details>
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
  const focus = captureAppFocus();
  try {
    const body = await api("/api/missioncontrol");
    const data = body.data;
    const el = document.getElementById("mc-root");
    if (!el) { stopMcPoll(); return; } // view left; stop polling
    el.innerHTML = `${destinationNav("live", "#/mc")}
      <div class="section"><h1>Current activity</h1><p>See what people and deliveries are doing now. Reading this page starts nothing.</p><p class="canonical-next"><strong>Next step:</strong> Open the current work that needs your attention.</p><h2>Current phase work</h2>
        ${data.feed.projects.filter((project) => !selectedProject || project.slug === selectedProject).map((p) => mcBelt(p, data.pins || {})).join("") || stateHtml("No current work is available.")}
      </div>
      <div class="section"><h2>Team activity not matched to work</h2>${mcOffBelt(data.sessions, data.off_belt || [])}</div>
      <details class="section"><summary>Technical details</summary><h2>Exact saved events</h2>${mcEvents(data.events)}</details>
      <div class="sub">Reading activity starts no work and changes no files.</div>`;
    enhanceSemantics(el);
    restoreAppFocus(focus);
    const latest = data.events?.[data.events.length - 1];
    const version = `${data.events?.length || 0}:${latest?.ts || ""}:${latest?.event || ""}`;
    if (liveAnnouncementKeys.has("mission-control")) {
      announceLiveUpdate(
        "mission-control",
        version,
        "Activity changed. Use Check for updates or review Current activity.",
      );
    } else {
      liveAnnouncementKeys.set("mission-control", version);
    }
  } finally {
    mcInFlight = false;
  }
}

async function viewMissionControl() {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "activity" }]);
  app.innerHTML = `<div id="mc-root">${stateHtml("Loading current activity…")}</div>`;
  await loadMissionControl();
  mcPoll = setInterval(() => { loadMissionControl().catch(() => {}); }, 10000);
}

/* ── views ─────────────────────────────────────────────────────────── */

async function viewOverview(notice = null) {
  setCrumbs([{ label: "overview" }]);
  const projectQuery = selectedProject
    ? `?project=${encodeURIComponent(selectedProject)}` : "";
  const [statusBody, stepBody, body, setupBody, presentationBody] = await Promise.all([
    api(`/api/status${projectQuery}`), api(`/api/step${projectQuery}`), api("/api/projects"),
    api(`/api/delivery-setup${projectQuery}`), api(`/api/presentation/status${projectQuery}`),
  ]);
  const projects = body.data.projects;
  const step = stepBody.data;
  const briefing = arrivalPanel(
    setupBody.data, statusBody.data, step, notice, presentationBody.data,
  );
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
  app.innerHTML = `${destinationNav("work", "#/p")}
    <header class="destination-hero"><span>Project</span><h1>${esc(slug)}</h1><p>Review the next work and the plan around it.</p></header>
    ${p.next_story ? `<div class="next"><span class="lbl">next</span>
      <a href="#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(p.next_story.story_id)}">
        <code>${esc(p.next_story.story_id)}</code></a> ${esc(p.next_story.title)} ${badge(p.next_story.status)}</div>` : ""}
    <div class="section"><h2>Phases <a class="badge" href="#/board/${encodeURIComponent(slug)}">board view</a></h2>
      <div class="tblwrap"><table class="tbl">
        <tr><th>Phase</th><th>State</th><th>Stories</th><th>Evidence</th><th>Summary</th></tr>
        ${phases || '<tr><td colspan="5">no phases yet</td></tr>'}
      </table></div></div>
    ${p.issues.length ? `<div class="guard">Roadmap changes are blocked — <a href="#/health">${p.issues.length} readiness issue${p.issues.length === 1 ? "" : "s"}</a> must be resolved first.</div>
    <div class="section"><h2>Readiness blockers (<a href="#/health">open readiness</a>)</h2>
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
    ${badge(item.severity === "error" ? "blocker" : "attention", item.severity === "error" ? "issue" : "warn")}
    <span class="msg">${esc(item.message)}</span>
    ${item.explanation ? `<div class="why">${esc(item.explanation)}</div>` : ""}
    <details><summary>Technical details</summary>${badge(item.kind, kindCls)}
      ${item.path ? `<a href="#/f/${encodeURIComponent(item.path)}"><code>${esc(item.path)}</code></a>` : ""}
      ${folders}</details>
  </div>`;
}

async function viewHealth() {
  setCrumbs([{ label: "overview", href: "#/" }, { label: "health" }]);
  const body = await api("/api/health");
  const h = body.data;
  const sections = [];
  const shownProjects = selectedProject
    ? h.projects.filter((project) => project.slug === selectedProject)
    : h.projects;
  for (const proj of shownProjects) {
    const byCat = {};
    proj.issues.concat(proj.warnings).forEach((item) => {
      (byCat[item.category] = byCat[item.category] || []).push(item);
    });
    const cats = Object.keys(byCat).map((cat) => `
      <div class="section"><h2>${esc(proj.slug)} · ${esc(CATEGORY_LABELS[cat] || cat)} (${byCat[cat].length})</h2>
        ${byCat[cat].map(healthItem).join("")}</div>`).join("");
    sections.push(cats || `<div class="section"><h2>${esc(proj.slug)}</h2>
      <div class="guard ok">Delivery is ready; no readiness blocker was found.</div></div>`);
  }
  const hook = h.hook_snapshot;
  const hookRows = [
    ["pre-commit installed", hook.pre_commit_exists],
    ["post-commit installed", hook.post_commit_exists],
    ["config seam (pre-commit.config)", hook.has_config_seam],
    ["local rule seam (pre-commit.local)", hook.has_local_seam],
    ["work-log capture", hook.has_work_log_capture],
  ].map(([k, v]) => `<div class="hitem">${badge(v ? "ok" : "missing", v ? "ok" : "issue")}<span class="msg">${esc(k)}</span></div>`).join("");
  const issueCount = shownProjects.reduce((total, project) => total + project.issues.length, 0);
  app.innerHTML = `${destinationNav("health", "#/health")}
    <header class="destination-hero"><span>Health</span><h1>Is this project ready?</h1><p>See what is ready and what needs attention before you change the plan.</p></header>
    <div class="guard ${issueCount === 0 ? "ok" : ""}">${issueCount === 0
      ? "This project is ready. Your next step is to return to current work."
      : `Resolve ${issueCount} health issue${issueCount === 1 ? "" : "s"} in this project before changing its plan.`}</div>
    <a class="primary canonical-primary" href="#/board/${encodeURIComponent(selectedProject)}">Return to current work</a>
    ${sections.join("")}
    <details class="section"><summary>Technical details</summary>
      <h2>Repository setup checks</h2>${hookRows}
      ${h.hook_explanations.length ? `<ul class="plain">${h.hook_explanations.map((e) => `<li class="warn">${esc(e)}</li>`).join("")}</ul>` : ""}
      <h2>Work-log configuration (read-only)</h2>
        <div class="meta">
          <div class="kv"><div class="k">enabled</div><div class="v">${esc(h.work_log_config.enabled)}</div></div>
          <div class="kv"><div class="k">directory</div><div class="v">${esc(h.work_log_config.dir)}</div></div>
          <div class="kv"><div class="k">project slug</div><div class="v">${esc(h.work_log_config.project_slug)}</div></div>
          <div class="kv"><div class="k">exclude regex</div><div class="v">${esc(h.work_log_config.exclude_regex)}</div></div>
        </div>
      <h2>Exact readiness check (copyable)</h2>
        <div class="copybar"><button id="copy-check" type="button">copy</button></div>
        <pre class="src" id="check-output">${esc(h.check_output)}</pre>
    </details>`;
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
    : '<tr><td colspan="4">no commits found for this story’s PMO files; no work-log entries (optional evidence — absent, not an error)</td></tr>';
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
      <pre class="src" id="handoff-text">Loading…</pre></div>`;
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
    <div class="guard ok">supplementary evidence — work logs never replace evidence-story-NN.md</div>
    <div class="section"><h2>work log · <code>${esc(body.data.path)}</code> (read-only, verbatim —
      excluded paths were omitted at capture time and stay omitted here)</h2>
      <pre class="src">${esc(body.data.content)}</pre></div>`;
}
