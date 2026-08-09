/**
 * script.js — Zomato Notes frontend.
 * Schema: User(id, name, email) · Note(id, title, content, tag, owner_id)
 * All API calls go to the real FastAPI backend at API_BASE.
 * Falls back to mock-data.js when backend is unreachable.
 */

"use strict";

const API_BASE = window.API_BASE || "http://localhost:8000";

const KNOWN_TAGS = ["work", "health", "recipes", "travel", "random"];

const TAG_COLORS = {
  work:    { bg: "rgba(59,130,246,.15)",  color: "#60a5fa", border: "rgba(59,130,246,.35)"  },
  health:  { bg: "rgba(34,197,94,.15)",   color: "#4ade80", border: "rgba(34,197,94,.35)"   },
  recipes: { bg: "rgba(245,158,11,.15)",  color: "#fbbf24", border: "rgba(245,158,11,.35)"  },
  travel:  { bg: "rgba(168,85,247,.15)",  color: "#c084fc", border: "rgba(168,85,247,.35)"  },
  random:  { bg: "rgba(100,116,139,.15)", color: "#94a3b8", border: "rgba(100,116,139,.35)" },
};

const state = {
  notes:       [],
  currentNote: null,
  searchMode:  "keyword",
  useMock:     false,
  editTag:     "work",
};

// ── API ───────────────────────────────────────────────────────────────────

async function api(method, path, body = null, timeout = 10000) {
  if (state.useMock) return mockApi(method, path, body);
  const ctrl = new AbortController();
  const tid  = setTimeout(() => ctrl.abort(), timeout);
  try {
    const opts = { method, headers: { "Content-Type": "application/json" }, signal: ctrl.signal };
    if (body !== null) opts.body = JSON.stringify(body);
    const res = await fetch(`${API_BASE}${path}`, opts);
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  } catch (err) {
    if ((err.name === "AbortError" || err.name === "TypeError") && !state.useMock) {
      console.warn("Backend unreachable — switching to mock mode.");
      state.useMock = true;
      return mockApi(method, path, body);
    }
    throw err;
  } finally {
    clearTimeout(tid);
  }
}

function mockApi(method, path, body) {
  const notes = window.MOCK_NOTES || [];
  if (path.includes("/report/stats")) return Promise.resolve(window.MOCK_STATS || {});
  if (path === "/notes/" || path === "/notes") {
    if (method === "GET")  return Promise.resolve([...notes]);
    if (method === "POST") {
      const n = { ...body, id: Date.now(), created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
      notes.unshift(n); return Promise.resolve(n);
    }
  }
  const idMatch = path.match(/^\/notes\/(\d+)$/);
  if (idMatch) {
    const id = +idMatch[1];
    if (method === "GET")    return Promise.resolve(notes.find(n => n.id === id) || null);
    if (method === "PUT")    return Promise.resolve({ ...notes.find(n => n.id === id), ...body });
    if (method === "DELETE") return Promise.resolve(null);
  }
  if (path.startsWith("/search")) {
    const q = new URL("http://x" + path).searchParams.get("q") || "";
    const matched = notes.filter(n =>
      n.title.toLowerCase().includes(q.toLowerCase()) ||
      n.content.toLowerCase().includes(q.toLowerCase())
    );
    return Promise.resolve({ query: q, results: matched.map(n => ({ note: n, score: 0.9, match_type: "keyword" })), total: matched.length });
  }
  if (path === "/tags")         return Promise.resolve(window.MOCK_STATS?.top_tags || []);
  if (path.match(/^\/ai\//))    return Promise.resolve({ answer: "AI unavailable in mock mode.", suggested_tag: "", summary: "Mock.", next_action: "Mock.", predicted_tag: "work", model_used: "mock" });
  return Promise.resolve(null);
}

// ── Toast ─────────────────────────────────────────────────────────────────

function toast(msg, type = "info") {
  const c  = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${{ success: "✓", error: "✗", warning: "⚠", info: "ℹ" }[type] || "ℹ"}</span><span>${msg}</span>`;
  c.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── View routing ──────────────────────────────────────────────────────────

function showView(id) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.getElementById(id)?.classList.add("active");
  document.querySelectorAll(".sidebar-link[data-view]").forEach(l =>
    l.classList.toggle("active", l.dataset.view === id)
  );
}

// ── Tag badge ─────────────────────────────────────────────────────────────

function tagBadge(tag) {
  if (!tag) return "";
  const c = TAG_COLORS[tag] || TAG_COLORS.random;
  return `<span class="tag-badge" style="background:${c.bg};color:${c.color};border:1px solid ${c.border}">${tag}</span>`;
}

// ── Time ──────────────────────────────────────────────────────────────────

function timeAgo(iso) {
  const m = Math.floor((Date.now() - new Date(iso)) / 60000);
  if (m < 1)  return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function escHtml(s) {
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ── Note card ─────────────────────────────────────────────────────────────

function noteCardHTML(note, score = null, matchType = null) {
  const preview = (note.content || "").slice(0, 160);
  const hasMore = (note.content || "").length > 160;
  const scoreHtml = score !== null
    ? `<span class="score-label">${(score * 100).toFixed(0)}%</span>` : "";
  const matchHtml = matchType
    ? `<span class="match-badge">${matchType}</span>` : "";

  return `
  <div class="card note-card" data-id="${note.id}">
    <div class="note-card-header">
      ${tagBadge(note.tag)}${matchHtml}${scoreHtml}
    </div>
    <div class="note-card-title">${escHtml(note.title)}</div>
    <div class="note-card-body">${escHtml(preview)}${hasMore ? "…" : ""}</div>
    <div class="note-card-footer">
      <span class="note-meta">${timeAgo(note.created_at)}</span>
    </div>
  </div>`;
}

function bindNoteCards(containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.querySelectorAll(".note-card").forEach(card => {
    card.addEventListener("click", () => openNote(+card.dataset.id));
  });
}

// ── Dashboard ─────────────────────────────────────────────────────────────

async function loadDashboard() {
  showView("view-dashboard");
  try {
    const [notes, stats] = await Promise.all([
      api("GET", "/notes/?limit=10"),
      api("GET", "/notes/report/stats"),
    ]);
    state.notes = notes || [];
    renderStats(stats);
    const el = document.getElementById("notes-list-main");
    if (el) {
      if (!notes.length) {
        el.innerHTML = `<div class="empty-state"><div class="empty-icon">📋</div><p>No notes yet. Create one!</p></div>`;
      } else {
        el.innerHTML = notes.map(n => noteCardHTML(n)).join("");
        bindNoteCards("notes-list-main");
      }
    }
  } catch (e) { toast("Dashboard load failed: " + e.message, "error"); }
}

function renderStats(stats) {
  if (!stats) return;
  document.getElementById("stat-total").textContent = stats.total ?? 0;

  // Tag breakdown pills in sidebar
  const tagEl = document.getElementById("sidebar-tags");
  if (tagEl && stats.top_tags) {
    tagEl.innerHTML = stats.top_tags.map(t => {
      const c = TAG_COLORS[t.tag] || TAG_COLORS.random;
      return `<button class="sidebar-link" data-tag="${t.tag}" style="justify-content:space-between">
        <span style="color:${c.color}"># ${t.tag}</span>
        <small style="opacity:.55">${t.count}</small>
      </button>`;
    }).join("");
    tagEl.querySelectorAll("[data-tag]").forEach(btn =>
      btn.addEventListener("click", () => loadNotesByTag(btn.dataset.tag))
    );
  }

  // Counts per tag in stat grid
  const byTagEl = document.getElementById("stat-by-tag");
  if (byTagEl && stats.by_tag) {
    byTagEl.innerHTML = stats.by_tag.map(t => {
      const c = TAG_COLORS[t.tag] || TAG_COLORS.random;
      return `<div class="tag-stat-item">
        <span class="tag-badge" style="background:${c.bg};color:${c.color};border:1px solid ${c.border}">${t.tag}</span>
        <span class="tag-stat-count">${t.count}</span>
      </div>`;
    }).join("");
  }
}

// ── Notes list view ───────────────────────────────────────────────────────

async function loadNotes(tag = "", ownerId = "") {
  showView("view-notes");
  const qs = new URLSearchParams({ limit: "100" });
  if (tag)     qs.set("tag", tag);
  if (ownerId) qs.set("owner_id", ownerId);
  document.getElementById("notes-view-title").textContent = tag ? `# ${tag}` : "All Notes";
  try {
    const notes = await api("GET", `/notes/?${qs}`);
    state.notes = notes || [];
    const el = document.getElementById("notes-list-view");
    if (!el) return;
    if (!notes.length) {
      el.innerHTML = `<div class="empty-state"><div class="empty-icon">📋</div><p>No notes found.</p></div>`;
      return;
    }
    el.innerHTML = notes.map(n => noteCardHTML(n)).join("");
    bindNoteCards("notes-list-view");
  } catch (e) { toast(e.message, "error"); }
}

function loadNotesByTag(tag) { loadNotes(tag); }

// ── Note detail ───────────────────────────────────────────────────────────

async function openNote(id) {
  try {
    const note = await api("GET", `/notes/${id}`);
    state.currentNote = note;
    renderNoteDetail(note);
    showView("view-detail");
  } catch (e) { toast("Could not load note: " + e.message, "error"); }
}

function renderNoteDetail(note) {
  const el = document.getElementById("view-detail");
  el.innerHTML = `
    <button class="btn btn-ghost btn-sm back-btn" id="btn-back">← Back</button>
    <div class="note-detail">
      <div class="note-detail-header">
        <div style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;margin-bottom:.4rem">
          ${tagBadge(note.tag)}
          <span class="note-meta">Created ${timeAgo(note.created_at)}</span>
          ${note.updated_at !== note.created_at ? `<span class="note-meta">· edited ${timeAgo(note.updated_at)}</span>` : ""}
        </div>
        <h1 class="note-detail-title">${escHtml(note.title)}</h1>
      </div>
      <div class="note-detail-body">${escHtml(note.content)}</div>
      <div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-top:1rem">
        <button class="btn btn-secondary btn-sm" id="btn-edit-note">✏ Edit</button>
        <button class="btn btn-secondary btn-sm" id="btn-ai-ask">🤖 Ask AI</button>
        <button class="btn btn-secondary btn-sm" id="btn-ai-autotag">✨ Auto-tag</button>
        <button class="btn btn-secondary btn-sm" id="btn-ai-summarise">📝 Summarise</button>
        <button class="btn btn-secondary btn-sm" id="btn-ai-action">🛠 Next Action</button>
        <button class="btn btn-danger btn-sm"    id="btn-delete-note">🗑 Delete</button>
      </div>
      <div id="ai-result-panel" class="ai-panel" style="display:none"></div>
    </div>`;

  el.querySelector("#btn-back").addEventListener("click", loadDashboard);
  el.querySelector("#btn-edit-note").addEventListener("click", () => openEditor(note));
  el.querySelector("#btn-delete-note").addEventListener("click", () => deleteNote(note.id));
  el.querySelector("#btn-ai-ask").addEventListener("click", () => {
    const q = prompt("Ask a question about this note:");
    if (q) runAi(`/ai/ask/${note.id}?question=${encodeURIComponent(q)}`, "POST", null, "AI Answer", r => r.answer);
  });
  el.querySelector("#btn-ai-autotag").addEventListener("click", () =>
    runAi(`/ai/autotag/${note.id}?apply=true`, "POST", null, "Auto-tag", r => {
      if (r.suggested_tag) {
        toast(`Tag applied: ${r.suggested_tag}`, "success");
        openNote(note.id);
        return `Tag set to: <strong>${escHtml(r.suggested_tag)}</strong>`;
      }
      return "No tag suggestion (check OPENAI_API_KEY).";
    })
  );
  el.querySelector("#btn-ai-summarise").addEventListener("click", () =>
    runAi(`/ai/summarise/${note.id}`, "POST", null, "Summary", r => r.summary)
  );
  el.querySelector("#btn-ai-action").addEventListener("click", () =>
    runAi(`/ai/runbook/${note.id}`, "POST", null, "Next Action", r => r.next_action)
  );
}

function showAiResult(html, title) {
  const panel = document.getElementById("ai-result-panel");
  if (!panel) return;
  panel.style.display = "block";
  panel.innerHTML = `<div class="ai-panel-title">${title}</div><div class="ai-result">${html}</div>`;
}

async function runAi(path, method, body, title, extract) {
  showAiResult('<span class="loading">Working…</span>', title);
  try {
    const res = await api(method, path, body);
    showAiResult(escHtml(extract(res) || "No response."), title);
  } catch (e) {
    showAiResult(`Error: ${escHtml(e.message)}`, title);
  }
}

async function deleteNote(id) {
  if (!confirm("Delete this note? This cannot be undone.")) return;
  try {
    await api("DELETE", `/notes/${id}`);
    toast("Note deleted", "success");
    loadDashboard();
  } catch (e) { toast("Delete failed: " + e.message, "error"); }
}

// ── Editor ────────────────────────────────────────────────────────────────

function openEditor(note = null) {
  state.editTag = note?.tag || "work";
  document.getElementById("editor-title-label").textContent = note ? "Edit Note" : "New Note";
  document.getElementById("editor-title").value    = note?.title   || "";
  document.getElementById("editor-content").value  = note?.content || "";
  document.getElementById("editor-note-id").value  = note?.id      || "";
  renderTagButtons();
  document.getElementById("modal-editor").classList.remove("hidden");
}

function closeEditor() {
  document.getElementById("modal-editor").classList.add("hidden");
}

function renderTagButtons() {
  document.querySelectorAll(".tag-btn").forEach(btn => {
    const active = btn.dataset.tag === state.editTag;
    btn.className = `tag-btn${active ? " active" : ""}`;
    if (active) {
      const c = TAG_COLORS[btn.dataset.tag] || TAG_COLORS.random;
      btn.style.cssText = `border-color:${c.color};color:${c.color};background:${c.bg}`;
    } else {
      btn.style.cssText = "";
    }
  });
}

async function saveNote() {
  const id      = document.getElementById("editor-note-id").value;
  const title   = document.getElementById("editor-title").value.trim();
  const content = document.getElementById("editor-content").value.trim();
  if (!title || !content) { toast("Title and content are required", "warning"); return; }
  const payload = { title, content, tag: state.editTag };
  try {
    if (id) {
      await api("PUT", `/notes/${id}`, payload);
      toast("Note updated", "success");
    } else {
      await api("POST", "/notes/", payload);
      toast("Note created", "success");
    }
    closeEditor();
    loadDashboard();
  } catch (e) { toast("Save failed: " + e.message, "error"); }
}

// ── Bulk import ───────────────────────────────────────────────────────────

function openBulkImport() {
  document.getElementById("bulk-text").value = "";
  document.getElementById("modal-bulk").classList.remove("hidden");
}

async function runBulkImport() {
  const text  = document.getElementById("bulk-text").value;
  const lines = text.split("\n").filter(l => l.trim());
  if (!lines.length) { toast("Paste at least one line", "warning"); return; }
  try {
    const res = await api("POST", "/notes/bulk-import/json", { lines, default_tag: "work" });
    toast(`Imported ${res.imported}, skipped ${res.skipped}`, "success");
    document.getElementById("modal-bulk").classList.add("hidden");
    loadDashboard();
  } catch (e) { toast("Import failed: " + e.message, "error"); }
}

// ── Search ────────────────────────────────────────────────────────────────

async function runSearch(query, mode = state.searchMode) {
  if (!query) return;
  showView("view-search");
  document.getElementById("search-status").textContent = "Searching…";
  document.getElementById("search-results-list").innerHTML = "";
  try {
    const res = await api("GET", `/search/?q=${encodeURIComponent(query)}&mode=${mode}&top_k=20`);
    const results = res.results || [];
    document.getElementById("search-status").textContent =
      `${results.length} result(s) for "${query}"`;
    const list = document.getElementById("search-results-list");
    if (!results.length) {
      list.innerHTML = `<div class="empty-state"><div class="empty-icon">🔍</div><p>No results found.</p></div>`;
      return;
    }
    list.innerHTML = results.map(r => noteCardHTML(r.note, r.score, r.match_type)).join("");
    list.querySelectorAll(".note-card").forEach(card =>
      card.addEventListener("click", () => openNote(+card.dataset.id))
    );
  } catch (e) {
    document.getElementById("search-status").textContent = "Search failed.";
    toast(e.message, "error");
  }
}

// ── AI classify ───────────────────────────────────────────────────────────

async function runClassify() {
  const title   = document.getElementById("classify-title").value.trim();
  const content = document.getElementById("classify-content").value.trim();
  if (!title || !content) { toast("Enter title and content first", "warning"); return; }
  document.getElementById("classify-result").textContent = "Classifying…";
  try {
    const res = await api("POST", "/ai/classify", { title, content });
    const c = TAG_COLORS[res.predicted_tag] || TAG_COLORS.random;
    document.getElementById("classify-result").innerHTML =
      `Predicted tag: <span class="tag-badge" style="background:${c.bg};color:${c.color};border:1px solid ${c.border}">${res.predicted_tag}</span>`;
  } catch (e) {
    document.getElementById("classify-result").textContent = "Error: " + e.message;
  }
}

// ── Boot ──────────────────────────────────────────────────────────────────

function boot() {
  // Sidebar nav
  document.querySelectorAll(".sidebar-link[data-view]").forEach(link => {
    link.addEventListener("click", () => {
      const v = link.dataset.view;
      if      (v === "view-dashboard") loadDashboard();
      else if (v === "view-notes")     loadNotes();
      else if (v === "view-search")    showView("view-search");
      else if (v === "view-ai")        showView("view-ai");
    });
  });

  // Navbar search
  const navSearch = document.getElementById("navbar-search");
  navSearch.addEventListener("keydown", e => {
    if (e.key === "Enter") runSearch(navSearch.value.trim());
  });

  // New note / bulk import
  document.getElementById("btn-new-note").addEventListener("click", () => openEditor());
  document.getElementById("btn-bulk-import").addEventListener("click", openBulkImport);
  document.getElementById("btn-bulk-run").addEventListener("click", runBulkImport);
  document.getElementById("btn-bulk-close").addEventListener("click", () =>
    document.getElementById("modal-bulk").classList.add("hidden")
  );

  // Editor
  document.getElementById("btn-editor-save").addEventListener("click", saveNote);
  document.getElementById("btn-editor-cancel").addEventListener("click", closeEditor);
  document.getElementById("modal-editor-close").addEventListener("click", closeEditor);

  // Tag buttons in editor
  document.querySelectorAll(".tag-btn").forEach(btn => {
    btn.addEventListener("click", () => { state.editTag = btn.dataset.tag; renderTagButtons(); });
  });

  // Search page
  const searchInput = document.getElementById("search-input");
  searchInput.addEventListener("keydown", e => {
    if (e.key === "Enter") runSearch(searchInput.value.trim(), state.searchMode);
  });
  document.getElementById("btn-search-go").addEventListener("click", () =>
    runSearch(searchInput.value.trim(), state.searchMode)
  );
  document.querySelectorAll(".mode-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".mode-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      state.searchMode = tab.dataset.mode;
      const q = searchInput.value.trim();
      if (q) runSearch(q, state.searchMode);
    });
  });

  // Tag filter on Notes view
  document.getElementById("filter-tag").addEventListener("change", e =>
    loadNotes(e.target.value)
  );

  // AI classify
  document.getElementById("btn-classify").addEventListener("click", runClassify);

  // Close modals on backdrop click
  ["modal-editor", "modal-bulk"].forEach(id => {
    document.getElementById(id).addEventListener("click", e => {
      if (e.target.id === id) e.target.classList.add("hidden");
    });
  });

  loadDashboard();
}

document.addEventListener("DOMContentLoaded", boot);
