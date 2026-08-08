import { useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { toast } from "react-hot-toast";
import { format } from "date-fns";
import {
  ArrowLeft,
  Edit3,
  Trash2,
  Wand2,
  Loader2,
  Clock,
  Calendar,
} from "lucide-react";
import { getNote, deleteNote, autoTagNote, updateNote } from "../api/client";
import type { Note } from "../api/types";
import SeverityBadge from "./SeverityBadge";
import TagChip from "./TagChip";

export default function NoteDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [note, setNote] = useState<Note | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [autoTagging, setAutoTagging] = useState(false);

  const loadNote = () => {
    if (!id) return;
    setLoading(true);
    getNote(Number(id))
      .then(setNote)
      .catch(() => {
        toast.error("Note not found");
        navigate("/");
      })
      .finally(() => setLoading(false));
  };

  useEffect(loadNote, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDelete = async () => {
    if (!note) return;
    if (!confirm(`Delete "${note.title}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await deleteNote(note.id);
      toast.success("Note deleted");
      navigate("/");
    } catch {
      toast.error("Delete failed");
      setDeleting(false);
    }
  };

  const handleAutoTag = async () => {
    if (!note) return;
    setAutoTagging(true);
    try {
      const res = await autoTagNote(note.id, true);
      if (res.suggested_tags.length === 0) {
        toast("No suggestions — check your OpenAI API key");
      } else {
        toast.success(`Applied tags: ${res.suggested_tags.join(", ")}`);
        loadNote(); // refresh to show new tags
      }
    } catch {
      toast.error("Auto-tag failed");
    } finally {
      setAutoTagging(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 size={28} className="animate-spin text-slate-700" />
      </div>
    );
  }

  if (!note) return null;

  return (
    <div className="max-w-3xl mx-auto">
      {/* Back */}
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="btn-ghost text-sm mb-5"
      >
        <ArrowLeft size={15} />
        Back
      </button>

      <div className="card">
        {/* Header */}
        <div className="flex items-start gap-3 mb-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <SeverityBadge severity={note.severity} />
              <div className="flex items-center gap-1 text-xs text-slate-600">
                <Calendar size={11} />
                {format(new Date(note.created_at), "dd MMM yyyy, HH:mm")}
              </div>
              {note.updated_at !== note.created_at && (
                <div className="flex items-center gap-1 text-xs text-slate-600">
                  <Clock size={11} />
                  edited {format(new Date(note.updated_at), "dd MMM, HH:mm")}
                </div>
              )}
            </div>
            <h1 className="text-2xl font-semibold text-slate-100 leading-tight">
              {note.title}
            </h1>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={handleAutoTag}
              disabled={autoTagging}
              className="btn-ghost text-xs"
              title="AI auto-tag"
            >
              {autoTagging ? (
                <Loader2 size={13} className="animate-spin" />
              ) : (
                <Wand2 size={13} />
              )}
              <span className="hidden sm:inline">Auto-tag</span>
            </button>
            <Link to={`/notes/${note.id}/edit`} className="btn-secondary text-xs">
              <Edit3 size={13} />
              <span className="hidden sm:inline">Edit</span>
            </Link>
            <button
              type="button"
              onClick={handleDelete}
              disabled={deleting}
              className="btn-danger text-xs"
            >
              {deleting ? (
                <Loader2 size={13} className="animate-spin" />
              ) : (
                <Trash2 size={13} />
              )}
              <span className="hidden sm:inline">Delete</span>
            </button>
          </div>
        </div>

        {/* Tags */}
        {note.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-5 pb-5 border-b border-slate-800">
            {note.tags.map((t) => (
              <TagChip key={t.id} name={t.name} />
            ))}
          </div>
        )}

        {/* Body */}
        <div className="prose prose-invert prose-sm max-w-none">
          <pre className="whitespace-pre-wrap font-mono text-sm text-slate-300 leading-relaxed bg-transparent p-0 m-0">
            {note.body}
          </pre>
        </div>
      </div>
    </div>
  );
}
