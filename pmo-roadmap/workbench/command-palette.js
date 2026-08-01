/* Delivery Workbench — Command palette (Ctrl+K / Cmd+K).
 * Fuzzy-filters projects, stories, phases, runs, programs, and
 * orchestration scores into a single jump list. */

"use strict";

(function () {
  const RECENT_KEY = "delivery-workbench.recent-palette";
  const MAX_RECENT = 10;
  const CACHE_TTL = 60_000; // 1 minute session cache

  /* ── Category icons ─────────────────────────────────── */
  const ICONS = {
    project: "\u{1F4C1}",  // folder
    story: "\u{1F4DD}",    // memo
    phase: "\u{1F3AF}",    // target
    run: "\u{1F680}",      // rocket
    program: "\u{2699}",   // gear
    score: "\u{1F3BC}",    // musical score
    request: "\u{1F514}",  // bell
  };

  /* ── Recent items ───────────────────────────────────── */
  function loadRecent() {
    try {
      return JSON.parse(localStorage.getItem(RECENT_KEY)) || [];
    } catch (_err) { return []; }
  }
  function saveRecent(items) {
    try { localStorage.setItem(RECENT_KEY, JSON.stringify(items.slice(0, MAX_RECENT))); }
    catch (_err) { /* storage unavailable */ }
  }
  function pushRecent(item) {
    const recent = loadRecent().filter(
      (r) => !(r.category === item.category && r.id === item.id),
    );
    recent.unshift({ category: item.category, id: item.id, title: item.title, subtitle: item.subtitle, route: item.route, status: item.status });
    saveRecent(recent);
  }

  /* ── Data fetching + cache ──────────────────────────── */
  let cache = { projects: null, board: {}, runs: null, programs: null, scores: null, ts: 0 };

  function cacheValid() { return Date.now() - cache.ts < CACHE_TTL; }

  async function fetchAll() {
    if (cacheValid() && cache.projects) return;
    cache.ts = Date.now();
    const results = await Promise.allSettled([
      api("/api/projects"),
      selectedProject ? api(`/api/projects/${encodeURIComponent(selectedProject)}/board`) : Promise.resolve(null),
      api("/api/runs").catch(() => null),
      api("/api/programs").catch(() => null),
      api("/api/orchestration").catch(() => null),
    ]);
    cache.projects = results[0].status === "fulfilled" ? results[0].value : null;
    if (results[1].status === "fulfilled" && results[1].value && selectedProject) {
      cache.board[selectedProject] = results[1].value;
    }
    cache.runs = results[2].status === "fulfilled" ? results[2].value : null;
    cache.programs = results[3].status === "fulfilled" ? results[3].value : null;
    cache.scores = results[4].status === "fulfilled" ? results[4].value : null;
  }

  /* ── Build searchable items ─────────────────────────── */
  function buildItems() {
    const items = [];

    // Projects
    const projects = cache.projects?.data?.projects || [];
    for (const p of projects) {
      items.push({
        category: "project",
        id: p.slug,
        title: p.slug,
        subtitle: p.next_story ? p.next_story.title : "No next work",
        status: p.next_story ? p.next_story.status : "",
        route: `#/board/${encodeURIComponent(p.slug)}`,
        search: `${p.slug} ${p.next_story?.title || ""}`.toLowerCase(),
      });
    }

    // Stories + Phases from board
    const slug = selectedProject || (projects[0]?.slug ?? "");
    const board = cache.board[slug];
    if (board?.data?.phases) {
      for (const phase of board.data.phases) {
        items.push({
          category: "phase",
          id: `phase-${phase.number}`,
          title: `Phase ${phase.number}: ${phase.title || ""}`,
          subtitle: slug,
          status: phase.closed ? "closed" : "open",
          route: `#/p/${encodeURIComponent(slug)}/ph/${phase.number}`,
          search: `phase ${phase.number} ${phase.title || ""}`.toLowerCase(),
        });
        for (const story of (phase.stories || [])) {
          items.push({
            category: "story",
            id: story.story_id,
            title: story.title,
            subtitle: `${slug} / Phase ${phase.number}`,
            status: story.status,
            route: `#/p/${encodeURIComponent(slug)}/s/${encodeURIComponent(story.story_id)}`,
            search: `${story.story_id} ${story.title}`.toLowerCase(),
          });
        }
      }
    }

    // Runs
    const runs = cache.runs?.data?.runs || [];
    for (const r of runs) {
      const runStory = r.run?.story?.id || "";
      const runState = r.run?.state || r.operational_state || "";
      items.push({
        category: "run",
        id: r.run_id,
        title: runStory || r.run_id,
        subtitle: `Run ${r.run_id.slice(0, 12)}`,
        status: runState,
        route: `#/live/run/${encodeURIComponent(r.run_id)}`,
        search: `${r.run_id} ${runStory}`.toLowerCase(),
      });
    }

    // Programs
    const programsList = cache.programs?.data?.programs || [];
    for (const p of programsList) {
      items.push({
        category: "program",
        id: p.run_id,
        title: p.program || p.run_id,
        subtitle: `Program ${p.run_id.slice(0, 12)}`,
        status: p.operational_state || p.state || "",
        route: `#/programs/${encodeURIComponent(p.run_id)}`,
        search: `${p.program || ""} ${p.run_id}`.toLowerCase(),
      });
    }

    // Orchestration scores
    const scores = cache.scores?.data?.scores || [];
    for (const s of scores) {
      items.push({
        category: "score",
        id: s.name || s.slug,
        title: s.slug || s.name,
        subtitle: s.valid ? "Valid score" : "Invalid score",
        status: s.valid ? "ok" : "invalid",
        route: `#/orchestration/${encodeURIComponent(s.name || s.slug)}`,
        search: `${s.slug || ""} ${s.name || ""}`.toLowerCase(),
      });
    }

    // Pending requests from programs
    const programRuns = cache.programs?.data?.programs || [];
    for (const p of programRuns) {
      if (Number(p.outstanding_requests || 0) > 0) {
        items.push({
          category: "request",
          id: `req-${p.run_id}`,
          title: `${p.outstanding_requests} pending request${Number(p.outstanding_requests) === 1 ? "" : "s"}`,
          subtitle: p.program || p.run_id,
          status: "waiting",
          route: `#/programs/${encodeURIComponent(p.run_id)}`,
          search: `request ${p.program || ""} ${p.run_id} pending`.toLowerCase(),
        });
      }
    }

    return items;
  }

  function filterItems(items, query) {
    if (!query) {
      // Show recent items first, then all items
      const recent = loadRecent();
      const recentIds = new Set(recent.map((r) => `${r.category}:${r.id}`));
      const recentItems = recent.map((r) => {
        const found = items.find((i) => i.category === r.category && i.id === r.id);
        return found || { ...r, search: "", recent: true };
      }).filter(Boolean);
      const rest = items.filter((i) => !recentIds.has(`${i.category}:${i.id}`));
      return [...recentItems, ...rest];
    }
    const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    return items.filter((item) =>
      terms.every((term) => item.search.includes(term)),
    );
  }

  /* ── Category grouping ──────────────────────────────── */
  const CATEGORY_ORDER = ["project", "story", "phase", "run", "program", "score", "request"];
  const CATEGORY_LABELS = {
    project: "Projects",
    story: "Stories",
    phase: "Phases",
    run: "Runs",
    program: "Programs",
    score: "Scores",
    request: "Requests",
  };

  /* ── DOM rendering ──────────────────────────────────── */
  function renderResults(container, items, selectedIndex) {
    if (!items.length) {
      container.innerHTML = '<div class="cp-empty">No results found</div>';
      return;
    }
    // Group by category
    const groups = {};
    let flatIndex = 0;
    for (const item of items) {
      if (!groups[item.category]) groups[item.category] = [];
      groups[item.category].push({ ...item, flatIndex: flatIndex++ });
    }
    let html = "";
    for (const cat of CATEGORY_ORDER) {
      const group = groups[cat];
      if (!group?.length) continue;
      html += `<div class="cp-group" role="group" aria-label="${esc(CATEGORY_LABELS[cat])}">`;
      html += `<div class="cp-group-label">${esc(CATEGORY_LABELS[cat])}</div>`;
      for (const item of group) {
        const active = item.flatIndex === selectedIndex;
        html += `<div class="cp-item${active ? " cp-active" : ""}"
          role="option" id="cp-item-${item.flatIndex}"
          aria-selected="${active}"
          data-route="${esc(item.route)}"
          data-category="${esc(item.category)}"
          data-item-id="${esc(item.id)}"
          data-title="${esc(item.title)}"
          data-subtitle="${esc(item.subtitle)}"
          data-status="${esc(item.status)}">
          <span class="cp-icon" aria-hidden="true">${ICONS[item.category] || ""}</span>
          <div class="cp-item-text">
            <span class="cp-item-title">${esc(item.title)}</span>
            <span class="cp-item-sub">${esc(item.subtitle)}</span>
          </div>
          ${item.status ? `<dw-status-pill status="${esc(item.status)}"></dw-status-pill>` : ""}
        </div>`;
      }
      html += "</div>";
    }
    container.innerHTML = html;
    const activeEl = container.querySelector(".cp-active");
    if (activeEl) activeEl.scrollIntoView({ block: "nearest" });
  }

  /* ── CommandPalette class ───────────────────────────── */
  class CommandPalette {
    constructor() {
      this._overlay = null;
      this._input = null;
      this._results = null;
      this._items = [];
      this._filtered = [];
      this._selectedIndex = 0;
      this._open = false;
      this._loading = false;
      this._boundKeydown = this._onGlobalKeydown.bind(this);
      document.addEventListener("keydown", this._boundKeydown);
    }

    _onGlobalKeydown(e) {
      const isMod = e.metaKey || e.ctrlKey;
      if (isMod && e.key === "k") {
        e.preventDefault();
        e.stopPropagation();
        if (this._open) this.close();
        else this.open();
      }
    }

    async open() {
      if (this._open) return;
      this._open = true;
      this._selectedIndex = 0;

      // Build overlay
      const overlay = document.createElement("div");
      overlay.className = "cp-overlay";
      overlay.setAttribute("role", "dialog");
      overlay.setAttribute("aria-modal", "true");
      overlay.setAttribute("aria-label", "Command palette");
      overlay.innerHTML = `
        <div class="cp-dialog">
          <div class="cp-search">
            <input class="cp-input" type="text" placeholder="Jump to project, story, run..."
              role="combobox" aria-expanded="true" aria-controls="cp-listbox"
              aria-autocomplete="list" aria-activedescendant="">
          </div>
          <div class="cp-body" id="cp-listbox" role="listbox" aria-label="Results">
            <dw-skeleton lines="6"></dw-skeleton>
          </div>
          <div class="cp-footer">
            <kbd>&#8593;&#8595;</kbd> navigate
            <kbd>&#9166;</kbd> open
            <kbd>esc</kbd> close
          </div>
        </div>`;
      document.body.appendChild(overlay);
      this._overlay = overlay;
      this._input = overlay.querySelector(".cp-input");
      this._results = overlay.querySelector(".cp-body");

      // Close on backdrop click
      overlay.addEventListener("mousedown", (e) => {
        if (e.target === overlay) this.close();
      });

      // Wire input
      this._input.addEventListener("input", () => this._onInput());
      this._input.addEventListener("keydown", (e) => this._onInputKeydown(e));

      // Wire click on items (delegated)
      this._results.addEventListener("click", (e) => {
        const item = e.target.closest(".cp-item");
        if (item) this._navigate(item);
      });

      this._input.focus();

      // Fetch data
      this._loading = true;
      try {
        await fetchAll();
        this._items = buildItems();
      } catch (_err) {
        this._items = [];
      }
      this._loading = false;
      if (!this._open) return; // closed while loading
      this._onInput();
    }

    close() {
      if (!this._open) return;
      this._open = false;
      if (this._overlay) {
        this._overlay.remove();
        this._overlay = null;
      }
      this._input = null;
      this._results = null;
    }

    _onInput() {
      const query = this._input?.value || "";
      this._filtered = filterItems(this._items, query.trim());
      this._selectedIndex = 0;
      this._render();
    }

    _onInputKeydown(e) {
      if (e.key === "Escape") {
        e.preventDefault();
        this.close();
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        this._selectedIndex = Math.min(this._selectedIndex + 1, this._filtered.length - 1);
        this._render();
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        this._selectedIndex = Math.max(this._selectedIndex - 1, 0);
        this._render();
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        const active = this._results?.querySelector(".cp-active");
        if (active) this._navigate(active);
        return;
      }
    }

    _render() {
      if (!this._results) return;
      renderResults(this._results, this._filtered, this._selectedIndex);
      const activeId = `cp-item-${this._selectedIndex}`;
      if (this._input) this._input.setAttribute("aria-activedescendant", activeId);
    }

    _navigate(el) {
      const route = el.dataset.route;
      if (!route) return;
      pushRecent({
        category: el.dataset.category,
        id: el.dataset.itemId,
        title: el.dataset.title,
        subtitle: el.dataset.subtitle,
        route,
        status: el.dataset.status,
      });
      this.close();
      location.hash = route;
    }
  }

  // Attach to DW namespace
  window.DW = window.DW || {};
  window.DW.CommandPalette = CommandPalette;
  window.DW._commandPalette = new CommandPalette();
})();
