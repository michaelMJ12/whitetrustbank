/**
 * VAULTRA — frontend runtime
 * ---------------------------------------------------------------
 * Everything here talks to the Django backend over fetch(). There is no
 * localStorage data layer anymore — accounts/, banking/ own the data;
 * this file is UI plumbing only:
 *   - Vaultra.api        thin fetch() wrapper (CSRF header, JSON/form body)
 *   - Vaultra.ui.mountRemoteTable   a smart table whose search/sort/filter/
 *                                   page state is sent to the server on
 *                                   every change — the server (see
 *                                   banking/utils.py smart_table_response)
 *                                   does the actual filtering.
 *   - Vaultra.createLiveGraph       the animated heartbeat canvas, reading
 *                                   whatever state object you hand it.
 * ---------------------------------------------------------------
 */
(function (global) {
  function getCookie(name) {
    const match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return match ? decodeURIComponent(match[2]) : null;
  }

  const api = {
    async getJSON(url) {
      const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
      if (!res.ok) throw new Error("Request failed: " + res.status);
      return res.json();
    },
    async postForm(url, data) {
      const body = new URLSearchParams(data || {});
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest",
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body,
      });
      const json = await res.json().catch(() => ({ ok: false, error: "Unexpected server response." }));
      if (!res.ok && !json.error) json.error = "Something went wrong (HTTP " + res.status + ").";
      return json;
    },
  };

  const fmt = (n) => "$" + Number(n).toLocaleString("en-NG", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  global.Vaultra = { api, formatCurrency: fmt, categories: {}, stages: {} };

  // Populate categories/stages once; every page loads this before using
  // colours so admin + customer dashboards and the landing page agree.
  global.Vaultra.loadMeta = async function () {
    try {
      const meta = await api.getJSON("/api/meta/");
      global.Vaultra.categories = meta.categories;
      global.Vaultra.stages = meta.stages;
    } catch (e) {
      console.error("Could not load /api/meta/", e);
    }
    return global.Vaultra;
  };

  // ---------------------------------------------------------------------
  // REMOTE SMART TABLE — search / sort / filter / paginate against a JSON
  // endpoint that follows the {results, total, page, pages} contract from
  // banking/utils.py smart_table_response().
  // ---------------------------------------------------------------------
  function mountRemoteTable(opts) {
    const {
      container, columns, endpoint, renderRow, extraParams = {},
      filters = [], emptyText = "No results.", defaultSort = null,
      pageSize = 8, searchPlaceholder = "Search…",
    } = opts;

    const state = {
      search: "", sortKey: defaultSort ? defaultSort.key : null,
      sortDir: defaultSort ? defaultSort.dir : "desc", page: 1, filters: {},
    };
    filters.forEach((f) => { state.filters[f.key] = "all"; });

    const toolbar = document.createElement("div");
    toolbar.className = "flex flex-wrap items-center gap-2.5 px-6 lg:px-8 py-4 border-b border-mist bg-paper/50";
    toolbar.innerHTML = `
      <div class="relative flex-1 min-w-[160px] max-w-xs">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-450 pointer-events-none" width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2"/><path d="M21 21l-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        <input type="text" placeholder="${searchPlaceholder}" class="st-search w-full pl-8 pr-3 py-2 text-xs sm:text-sm rounded-lg border border-mist bg-white outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal" />
      </div>
      ${filters.map((f) => `
        <select data-filter-key="${f.key}" class="st-filter text-xs sm:text-sm rounded-lg border border-mist bg-white px-2.5 py-2 text-ink outline-none focus:ring-2 focus:ring-teal/30">
          <option value="all">${f.label}: All</option>
          ${f.options.map((o) => `<option value="${o.value}">${o.label}</option>`).join("")}
        </select>
      `).join("")}
      <span class="st-count text-xs text-slate-450 ml-auto whitespace-nowrap"></span>
    `;

    const tableWrap = document.createElement("div");
    tableWrap.className = "overflow-x-auto";
    const table = document.createElement("table");
    table.className = "w-full text-sm";
    const thead = document.createElement("thead");
    thead.innerHTML = `<tr class="text-left text-xs text-slate-450 border-b border-mist">
      ${columns.map((c) => `<th data-key="${c.key || ""}" class="st-th ${c.sortable !== false && c.key ? "cursor-pointer select-none hover:text-ink" : ""} px-4 first:pl-6 lg:first:pl-8 last:pr-6 lg:last:pr-8 py-3 font-medium whitespace-nowrap ${c.align === "right" ? "text-right" : ""}">${c.label}${c.sortable !== false && c.key ? ' <span class="st-arrow text-[10px] opacity-40">↕</span>' : ""}</th>`).join("")}
    </tr>`;
    const tbody = document.createElement("tbody");
    tbody.className = "divide-y divide-mist";
    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrap.appendChild(table);

    const footer = document.createElement("div");
    footer.className = "st-footer hidden items-center justify-between px-6 lg:px-8 py-3 text-xs text-slate-450 border-t border-mist";
    footer.innerHTML = `<button type="button" class="st-prev hover:text-ink transition-colors">← Prev</button><span class="st-page"></span><button type="button" class="st-next hover:text-ink transition-colors">Next →</button>`;

    container.innerHTML = "";
    container.appendChild(toolbar);
    container.appendChild(tableWrap);
    container.appendChild(footer);

    let loadToken = 0;

    async function paint() {
      const myToken = ++loadToken;
      const params = new URLSearchParams({ ...extraParams, page: state.page, page_size: pageSize });
      if (state.search) params.set("search", state.search);
      if (state.sortKey) { params.set("sort", state.sortKey); params.set("dir", state.sortDir); }
      Object.entries(state.filters).forEach(([k, v]) => { if (v && v !== "all") params.set(k, v); });

      let data;
      try {
        data = await Vaultra.api.getJSON(endpoint + "?" + params.toString());
      } catch (e) {
        if (myToken !== loadToken) return;
        tbody.innerHTML = `<tr><td colspan="${columns.length}" class="px-6 lg:px-8 py-10 text-center text-red-600">Couldn't load data.</td></tr>`;
        return;
      }
      if (myToken !== loadToken) return; // a newer request already landed

      const rows = data.results || [];
      tbody.innerHTML = rows.length
        ? rows.map(renderRow).join("")
        : `<tr><td colspan="${columns.length}" class="px-6 lg:px-8 py-10 text-center text-slate-450">${emptyText}</td></tr>`;

      toolbar.querySelector(".st-count").textContent = data.total + (data.total === 1 ? " result" : " results");
      const showFooter = data.pages > 1;
      footer.classList.toggle("hidden", !showFooter);
      footer.classList.toggle("flex", showFooter);
      footer.querySelector(".st-page").textContent = `Page ${data.page} of ${data.pages}`;

      thead.querySelectorAll(".st-th").forEach((th) => {
        const arrow = th.querySelector(".st-arrow");
        if (!arrow) return;
        if (th.dataset.key === state.sortKey) {
          arrow.textContent = state.sortDir === "asc" ? "↑" : "↓";
          arrow.classList.remove("opacity-40");
        } else {
          arrow.textContent = "↕";
          arrow.classList.add("opacity-40");
        }
      });
    }

    let searchDebounce = null;
    toolbar.querySelector(".st-search").addEventListener("input", (e) => {
      clearTimeout(searchDebounce);
      searchDebounce = setTimeout(() => { state.search = e.target.value; state.page = 1; paint(); }, 250);
    });
    toolbar.querySelectorAll(".st-filter").forEach((sel) => {
      sel.addEventListener("change", (e) => { state.filters[e.target.dataset.filterKey] = e.target.value; state.page = 1; paint(); });
    });
    thead.querySelectorAll(".st-th[data-key]").forEach((th) => {
      if (!th.dataset.key) return;
      th.addEventListener("click", () => {
        if (state.sortKey === th.dataset.key) state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
        else { state.sortKey = th.dataset.key; state.sortDir = "asc"; }
        paint();
      });
    });
    footer.querySelector(".st-prev").addEventListener("click", () => { if (state.page > 1) { state.page--; paint(); } });
    footer.querySelector(".st-next").addEventListener("click", () => { state.page++; paint(); });

    paint();
    return { refresh: paint };
  }

  global.Vaultra.ui = { mountRemoteTable };

  // ---------------------------------------------------------------------
  // LIVE "HEARTBEAT" GRAPH — identical animation engine to the prototype;
  // only the state now comes from a `getState()` callback the page wires
  // up to fetch("/api/live-status/") or the admin's cached per-user map.
  // ---------------------------------------------------------------------
  function ecgSample(phase, jitter) {
    let v = 0;
    v += 0.16 * Math.exp(-Math.pow((phase - 0.14) * 34, 2));
    v += 1.0 * Math.exp(-Math.pow((phase - 0.4) * 90, 2));
    v -= 0.32 * Math.exp(-Math.pow((phase - 0.365) * 160, 2));
    v -= 0.18 * Math.exp(-Math.pow((phase - 0.44) * 160, 2));
    v += 0.26 * Math.exp(-Math.pow((phase - 0.66) * 22, 2));
    if (jitter) v += (Math.random() - 0.5) * 0.18;
    return v;
  }

  const TONE_COLOR = { teal: "#0F5C4E", gold: "#C9A227", red: "#DC2626" };

  function colorForState(state) {
    if (state.status === "issue" || state.status === "flagged") return TONE_COLOR.red;
    const cat = (global.Vaultra.categories && global.Vaultra.categories[state.category]) || { color: TONE_COLOR.teal };
    return cat.color;
  }

  global.Vaultra.createLiveGraph = function (canvas, getState) {
    const ctx = canvas.getContext("2d");
    let raf = null;
    let w = 0, h = 0, dpr = 1;
    const N = 160;
    const buf = new Array(N).fill(0);
    let phase = 0;
    let lastT = null;

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth || canvas.parentElement.clientWidth;
      h = canvas.clientHeight || canvas.parentElement.clientHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    window.addEventListener("resize", resize);
    resize();

    function paramsForTone(tone, status) {
      if (status === "completed") return { period: 2200, amp: 0.12, jitter: false, flat: true };
      if (tone === "red") return { period: 620, amp: 0.9, jitter: true, flat: false };
      if (tone === "gold") return { period: 1900, amp: 0.8, jitter: false, flat: false };
      return { period: 1300, amp: 0.85, jitter: false, flat: false };
    }

    function frame(t) {
      if (lastT == null) lastT = t;
      const dt = t - lastT;
      lastT = t;
      const state = getState() || { tone: "teal", status: "completed" };
      const p = paramsForTone(state.tone, state.status);
      phase += dt / p.period;
      if (phase > 1) phase -= 1;

      const raw = p.flat
        ? Math.sin(t / 900) * p.amp + (Math.random() - 0.5) * 0.05
        : ecgSample(phase, p.jitter) * p.amp;

      buf.shift();
      buf.push(raw);

      ctx.clearRect(0, 0, w, h);
      const midY = h / 2;
      ctx.strokeStyle = "rgba(11,18,32,0.06)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, midY);
      ctx.lineTo(w, midY);
      ctx.stroke();

      const color = colorForState(state);
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.shadowColor = color;
      ctx.shadowBlur = 6;
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      const stepX = w / (N - 1);
      buf.forEach((v, i) => {
        const x = i * stepX;
        const y = midY - v * (h * 0.36);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.shadowBlur = 0;

      const lastX = (N - 1) * stepX;
      const lastY = midY - buf[buf.length - 1] * (h * 0.36);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
      ctx.fill();

      raf = requestAnimationFrame(frame);
    }

    return {
      start() { if (!raf) raf = requestAnimationFrame(frame); },
      stop() {
        if (raf) cancelAnimationFrame(raf);
        raf = null;
        window.removeEventListener("resize", resize);
      },
    };
  };
})(window);
