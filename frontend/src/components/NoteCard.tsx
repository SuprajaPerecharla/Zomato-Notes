import { Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import { Clock, ChevronRight } from "lucide-react";
import type { Note } from "../api/types";
import SeverityBadge from "./SeverityBadge";
import TagChip from "./TagChip";

interface Props {
  note: Note;
  /** Optional relevance score (0-1) shown in search results */
  score?: number;
  matchType?: string;
}

export default function NoteCard({ note, score, matchType }: Props) {
  const preview = note.body.slice(0, 140).trim();
  const hasMore = note.body.length > 140;

  return (
    <Link
      to={`/notes/${note.id}`}
      className="card group block hover:border-slate-700 transition-all hover:shadow-lg hover:shadow-black/30"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {/* Header row */}
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <SeverityBadge severity={note.severity} />
            {matchType && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-800 text-slate-500 font-mono">
                {matchType}
              </span>
            )}
            {score !== undefined && (
              <span className="text-xs text-slate-600 font-mono ml-auto">
                {(score * 100).toFixed(0)}% match
              </span>
            )}
          </div>

          {/* Title */}
          <h3 className="font-semibold text-slate-100 text-base leading-tight truncate group-hover:text-brand-400 transition-colors">
            {note.title}
          </h3>

          {/* Body preview */}
          <p className="mt-1.5 text-sm text-slate-400 font-mono leading-relaxed line-clamp-2">
            {preview}
            {hasMore && <span className="text-slate-600">…</span>}
          </p>

          {/* Footer row */}
          <div className="mt-3 flex items-center gap-3 flex-wrap">
            {/* Tags */}
            {note.tags.length > 0 && (
              <div className="flex gap-1.5 flex-wrap">
                {note.tags.slice(0, 5).map((t) => (
                  <TagChip key={t.id} name={t.name} clickable={false} />
                ))}
                {note.tags.length > 5 && (
                  <span className="text-xs text-slate-600">
                    +{note.tags.length - 5}
                  </span>
                )}
              </div>
            )}

            <div className="flex items-center gap-1 text-xs text-slate-600 ml-auto">
              <Clock size={11} />
              {formatDistanceToNow(new Date(note.created_at), {
                addSuffix: true,
              })}
            </div>
          </div>
        </div>

        <ChevronRight
          size={16}
          className="text-slate-700 group-hover:text-brand-400 shrink-0 mt-1 transition-colors"
        />
      </div>
    </Link>
  );
}
