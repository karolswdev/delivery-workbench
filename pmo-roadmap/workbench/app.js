/* Delivery Workbench explorer — read-only, hash-routed, API-backed.
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

/* ── views ─────────────────────────────────────────────────────────── */

async function viewOverview() {
  setCrumbs([{ label: "overview" }]);
  const body = await api("/api/projects");
  const projects = body.data.projects;
  if (!projects.length) {
    app.innerHTML = stateHtml("No roadmap projects found under pm/roadmap/. Scaffold one with `dw phase create` or `dw adopt`.");
    return;
  }
  app.innerHTML = `<div class="grid">` + projects.map((p) => `
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
    <div class="section"><h2>Phases</h2>
      <div class="tblwrap"><table class="tbl">
        <tr><th>Phase</th><th>State</th><th>Stories</th><th>Evidence</th><th>Summary</th></tr>
        ${phases || '<tr><td colspan="5">no phases yet</td></tr>'}
      </table></div></div>
    ${p.issues.length ? `<div class="section"><h2>Validation issues</h2>
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
      ? ` · <a href="#/f/${encodeURIComponent(s.evidence_path)}"><code>evidence</code></a>` : ""}</td>
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
    ${ph.final_summary_content ? `<div class="section"><h2>Final summary</h2>
      <pre class="src">${esc(ph.final_summary_content)}</pre></div>` : ""}`;
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

/* ── router ─────────────────────────────────────────────────────────── */

async function route() {
  app.innerHTML = stateHtml("Loading…");
  const hash = decodeURIComponent(location.hash.replace(/^#/, "")) || "/";
  const parts = hash.split("/").filter(Boolean);
  try {
    if (!parts.length) return await viewOverview();
    if (parts[0] === "p" && parts.length === 2) return await viewProject(parts[1]);
    if (parts[0] === "p" && parts[2] === "ph") return await viewPhase(parts[1], parts[3]);
    if (parts[0] === "p" && parts[2] === "s") return await viewStory(parts[1], parts[3]);
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
