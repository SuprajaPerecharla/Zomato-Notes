import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "react-hot-toast";
import { Save, ArrowLeft, Wand2, Loader2 } from "lucide-react";
import { createNote, getNote, updateNote, autoTagNote } from "../api/client";
import type { Severity } from "../api/types";
import TagInput from "./TagInput";

const SEVERITIES: { value: Severity; label: string; color: string }[] = [
  { value: "low",      label: "Low",      color: "text-slate-400" },
  { value: "medium",   label: "Medium",   color: "text-blue-400"  },
  { value: "high",     label: "High",     color: "text-amber-400" },
  { value: "critical", label: "Critical", color: "text-red-400"   },
];

export default function NoteEditor() {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [severity, setSeverity] = useState<Severity>("medium");
  const [tags, setTags] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [autoTagging, setAutoTagging] = useState(false);
  const [loadingNote, setLoadingNote] = useState(isEdit);

  useEffect(() => {
    if (!isEdit || !id) return;
    getNote(Number(id))
      .then((note) => {
        setTitle(note.title);
        setBody(note.body);
        setSeverity(note.severity);
        setTags(note.tags.map((t) => t.name));
      })
      .catch(() => {
        toast.error("Could not load note");
        navigate("/");
      })
      .finally(() => setLoadingNote(false));
  }, [id, isEdit, navigate]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !body.trim()) {
      toast.error("Title and body are required");
      return;
    }
    setSaving(true);
    try {
      if (isEdit && id) {
        const updated = await updateNote(Number(id), { title, body, severity, tags });
        toast.success("Note updated");
        navigate(`/notes/${updated.id}`);
      } else {
        const created = await createNote({ title, body, severity, tags });
        toast.success("Note created");
        navigate(`/notes/${created.id}`);
      }
    } catch (err) {
      toast.error(String(err));
    } finally {
      setSaving(false);
    }
  };

  const handleAutoTag = async () => {
    if (!isEdit || !id) {
      toast("Save the note first to use auto-tag");
      return;
    }
    setAutoTagging(true);
    try {
      const res = await autoTagNote(Number(id), false);
      if (res.suggested_tags.length === 0) {
        toast("No tag suggestions — check your OpenAI API key");
      } else {
        // Merge without duplicates
        setTags((prev) => [
          ...prev,
          ...res.suggested_tags.filter((t) => !prev.includes(t)),
        ]);
        toast.success(`Suggested: ${res.suggested_tags.join(", ")}`);
      }
    } catch {
      toast.error("Auto-tag failed");
    } finally {
      setAutoTagging(false);
    }
  };

  if (loadingNote) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 size={28} className="animate-spin text-slate-700" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Back button */}
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="btn-ghost text-sm mb-5"
      >
        <ArrowLeft size={15} />
        Back
      </button>

      <h1 className="text-xl font-semibold text-slate-100 mb-6">
        {isEdit ? "Edit Note" : "New Incident Note"}
      </h1>

      <form onSubmit={handleSave} className="space-y-5">
        {/* Title */}
        <div>
          <label htmlFor="title" className="label">Title</label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Payment service latency spike — DB pool exhaustion"
            className="input"
            required
            maxLength={256}
          />
        </div>

        {/* Severity */}
        <div>
          <label className="label">Severity</label>
          <div className="flex gap-2">
            {SEVERITIES.map(({ value, label, color }) => (
              <button
                key={value}
                type="button"
                onClick={() => setSeverity(value)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-all ${
                  severity === value
                    ? `${color} bg-slate-800 border-current`
                    : "text-slate-500 bg-slate-900 border-slate-800 hover:border-slate-700"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Body */}
        <div>
          <label htmlFor="body" className="label">Body</label>
          <textarea
            id="body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Describe the incident, steps taken, resolution, links…"
            className="textarea"
            required
            rows={8}
          />
        </div>

        {/* Tags */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="label mb-0">Tags</label>
            <button
              type="button"
              onClick={handleAutoTag}
              disabled={autoTagging || !isEdit}
              className="btn-ghost text-xs"
              title={isEdit ? "Get AI tag suggestions" : "Save note first to use auto-tag"}
            >
              {autoTagging ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <Wand2 size={12} />
              )}
              AI Suggest
            </button>
          </div>
          <TagInput value={tags} onChange={setTags} />
          <p className="text-xs text-slate-600 mt-1">
            Leave empty to auto-tag on save (requires OpenAI key)
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
            {isEdit ? "Save Changes" : "Create Note"}
          </button>
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
