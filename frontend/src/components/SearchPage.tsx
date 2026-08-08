/**
 * SearchPage — unified smart search UI.
 *
 * Modes:
 *  - keyword (BM25, always works)
 *  - semantic (embedding cosine similarity, requires model)
 *  - auto (tries semantic + keyword merged)
 *
 * The search query is synced to the URL so it's shareable/bookmarkable.
 */

import { useEffect, useState, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { Loader2, Search, Zap, Hash, AlignLeft } from "lucide-react";
import { search as apiSearch, tagJump } from "../api/client";
import type { SearchResult, Note } from "../api/types";
import NoteCard from "./NoteCard";

type Mode = "auto" | "keyword" | "semantic";

const MODE_INFO: Record<Mode, { icon: React.ReactNode; label: string; desc: string }> = {
  auto:     { icon: <Zap size={13} />,      label: "Smart",    desc: "Semantic + keyword blend" },
  keyword:  { icon: <AlignLeft size={13} />, label: "Keyword",  desc: "BM25 full-text ranking" },
  semantic: { icon: <Zap size={13} />,      label: "Semantic", desc: "Embedding cosine similarity" },
};

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQ = searchParams.get("q") ?? "";
  const initialMode = (searchParams.get("mode") as Mode) ?? "auto";
  const initialTag = searchParams.get("tag") ?? "";

  const [query, setQuery] = useState(initialQ);
  const [mode, setMode] = useState<Mode>(initialMode);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [tagNotes, setTagNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [total, setTotal] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Run search when URL params change
  useEffect(() => {
    const q = searchParams.get("q") ?? "";
    const m = (searchParams.get("mode") as Mode) ?? "auto";
    const tag = searchParams.get("tag") ?? "";
    setQuery(q);
    setMode(m);

    if (tag) {
      runTagJump(tag);
    } else if (q) {
      runSearch(q, m);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const runSearch = async (q: string, m: Mode) => {
    setLoading(true);
    setTagNotes([]);
    setSearched(true);
    try {
      const res = await apiSearch(q, m);
      setResults(res.results);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const runTagJump = async (tag: string) => {
    setLoading(true);
    setResults([]);
    setSearched(true);
    try {
      const res = await tagJump(tag);
      setTagNotes(res.notes);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
      setTagNotes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearchParams({ q: query.trim(), mode });
  };

  const switchMode = (m: Mode) => {
    setMode(m);
    if (query.trim()) {
      setSearchParams({ q: query.trim(), mode: m });
    }
  };

  const isTagJump = Boolean(searchParams.get("tag"));

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-xl font-semibold text-slate-100 mb-5 flex items-center gap-2">
        <Zap size={20} className="text-brand-400" />
        Smart Search
      </h1>

      {/* Search form */}
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="relative">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none"
          />
          <input
            ref={inputRef}
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search across all notes…"
            className="input pl-10 pr-4 py-3 text-base"
            autoFocus
            aria-label="Search query"
          />
        </div>
      </form>

      {/* Mode selector */}
      <div className="flex gap-2 mb-6">
        {(Object.keys(MODE_INFO) as Mode[]).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => switchMode(m)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
              mode === m
                ? "bg-brand-500/20 border-brand-500/50 text-brand-400"
                : "bg-slate-900 border-slate-800 text-slate-500 hover:border-slate-700 hover:text-slate-300"
            }`}
            title={MODE_INFO[m].desc}
          >
            {MODE_INFO[m].icon}
            {MODE_INFO[m].label}
          </button>
        ))}

        {searched && !loading && (
          <span className="ml-auto text-xs text-slate-500 self-center">
            {total} result{total !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Tag jump notice */}
      {isTagJump && (
        <div className="flex items-center gap-2 mb-4 px-3 py-2 bg-slate-800 rounded-lg border border-slate-700 text-sm text-slate-300">
          <Hash size={14} className="text-brand-400" />
          Showing notes tagged{" "}
          <span className="font-mono text-brand-400">#{searchParams.get("tag")}</span>
        </div>
      )}

      {/* Results */}
      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 size={28} className="animate-spin text-slate-700" />
        </div>
      ) : !searched ? (
        <div className="text-center py-16 text-slate-600">
          <Search size={40} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Enter a query to search across your notes</p>
          <p className="text-xs mt-1 text-slate-700">
            Try tag:#payment, service names, error messages…
          </p>
        </div>
      ) : isTagJump ? (
        tagNotes.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-10">No notes with this tag.</p>
        ) : (
          <div className="space-y-3">
            {tagNotes.map((note) => (
              <NoteCard key={note.id} note={note} />
            ))}
          </div>
        )
      ) : results.length === 0 ? (
        <div className="text-center py-16 text-slate-600">
          <p className="text-sm">No results for "{searchParams.get("q")}"</p>
          {mode === "semantic" && (
            <p className="text-xs mt-2 text-slate-700">
              Semantic search needs notes with embeddings — try Keyword mode.
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {results.map((r) => (
            <NoteCard
              key={r.note.id}
              note={r.note}
              score={r.score}
              matchType={r.match_type}
            />
          ))}
        </div>
      )}
    </div>
  );
}
