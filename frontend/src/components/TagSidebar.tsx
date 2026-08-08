import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Hash, ChevronRight, Loader2 } from "lucide-react";
import { getTags } from "../api/client";
import type { Tag } from "../api/types";

export default function TagSidebar() {
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const activeTag = searchParams.get("tag") ?? "";

  useEffect(() => {
    getTags()
      .then(setTags)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleTagClick = (name: string) => {
    // Tag quick-jump: navigate to search page with tag filter
    navigate(`/?tag=${encodeURIComponent(name)}`);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-6">
        <Loader2 size={16} className="animate-spin text-slate-600" />
      </div>
    );
  }

  if (tags.length === 0) {
    return (
      <p className="text-xs text-slate-600 px-1">No tags yet. Create a note to get started.</p>
    );
  }

  return (
    <ul className="space-y-0.5">
      {tags.map((tag) => (
        <li key={tag.id}>
          <button
            type="button"
            onClick={() => handleTagClick(tag.name)}
            className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-colors text-left ${
              activeTag === tag.name
                ? "bg-brand-500/20 text-brand-400"
                : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
            }`}
          >
            <Hash size={12} className="shrink-0 opacity-60" />
            <span className="truncate flex-1">{tag.name}</span>
            <ChevronRight size={12} className="opacity-40 shrink-0" />
          </button>
        </li>
      ))}
    </ul>
  );
}
