import { useEffect, useState, useCallback } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Loader2, PlusCircle, Filter, X, RefreshCw } from "lucide-react";
import { getNotes } from "../api/client";
import type { Note, Severity } from "../api/types";
import NoteCard from "./NoteCard";
import TagSidebar from "./TagSidebar";

const SEVERITIES: Severity[] = ["low", "medium", "high", "critical"];
const PAGE_SIZE = 20;

export default function Dashboard() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const [searchParams, setSearchParams] = useSearchParams();
  const activeTag = searchParams.get("tag") ?? "";
  const activeSeverity = (searchParams.get("severity") ?? "") as Severity | "";

  const fetchNotes = useCallback(
    async (reset = false) => {
      setLoading(true);
      try {
        const skip = reset ? 0 : page * PAGE_SIZE;
        const data = await getNotes({
          skip,
          limit: PAGE_SIZE,
          tag: activeTag || undefined,
          severity: activeSeverity || undefined,
        });
        setNotes((prev) => (reset ? data : [...prev, ...data]));
        setHasMore(data.length === PAGE_SIZE);
        if (reset) setPage(0);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    },
    [activeTag, activeSeverity, page]
  );

  // Refetch when filters change
  useEffect(() => {
    fetchNotes(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTag, activeSeverity]);

  const clearFilter = (key: string) => {
    setSearchParams((p) => {
      p.delete(key);
      return p;
    });
  };

  const setSeverityFilter = (s: Severity | "") => {
    setSearchParams((p) => {
      if (s) p.set("severity", s);
      else p.delete("severity");
      return p;
    });
  };

  return (
    <div className="flex gap-6">
      {/* Sidebar */}
      <aside className="w-52 shrink-0 hidden lg:block">
        <div className="sticky top-20">
          <h2 className="label mb-3">Quick Jump — Tags</h2>
          <TagSidebar />
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 min-w-0">
        {/* Filter bar */}
        <div className="flex items-center gap-3 mb-5 flex-wrap">
          <div className="flex items-center gap-1.5 flex-wrap">
            <Filter size={13} className="text-slate-600" />
            <span className="text-xs text-slate-500 font-medium">Severity:</span>
            {SEVERITIES.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSeverityFilter(activeSeverity === s ? "" : s)}
                className={`text-xs px-2.5 py-1 rounded-full border transition-all ${
                  activeSeverity === s
                    ? "bg-brand-500 border-brand-600 text-white"
                    : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600"
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Active filter chips */}
          {activeTag && (
            <span className="tag-chip">
              #{activeTag}
              <button type="button" onClick={() => clearFilter("tag")} aria-label="Remove tag filter">
                <X size={11} />
              </button>
            </span>
          )}

          <button
            type="button"
            onClick={() => fetchNotes(true)}
            className="btn-ghost text-xs ml-auto"
            aria-label="Refresh notes"
          >
            <RefreshCw size={13} />
          </button>

          <Link to="/notes/new" className="btn-primary text-xs">
            <PlusCircle size={13} />
            New Note
          </Link>
        </div>

        {/* Notes list */}
        {loading && notes.length === 0 ? (
          <div className="flex justify-center py-20">
            <Loader2 size={28} className="animate-spin text-slate-700" />
          </div>
        ) : notes.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-slate-500 text-sm mb-4">No notes found.</p>
            <Link to="/notes/new" className="btn-primary text-sm">
              <PlusCircle size={16} />
              Create your first note
            </Link>
          </div>
        ) : (
          <>
            <div className="space-y-3">
              {notes.map((note) => (
                <NoteCard key={note.id} note={note} />
              ))}
            </div>

            {/* Load more */}
            {hasMore && (
              <div className="mt-6 flex justify-center">
                <button
                  type="button"
                  onClick={() => {
                    setPage((p) => p + 1);
                    fetchNotes();
                  }}
                  disabled={loading}
                  className="btn-secondary text-sm"
                >
                  {loading ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : null}
                  Load more
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
