/**
 * Controlled tag-input widget.
 * Type a tag name and press Enter or comma to add it.
 */

import { useState, KeyboardEvent } from "react";
import { Plus } from "lucide-react";
import TagChip from "./TagChip";

interface Props {
  value: string[];
  onChange: (tags: string[]) => void;
}

export default function TagInput({ value, onChange }: Props) {
  const [input, setInput] = useState("");

  const addTag = (raw: string) => {
    const tag = raw.trim().toLowerCase().replace(/\s+/g, "-");
    if (tag && !value.includes(tag)) {
      onChange([...value, tag]);
    }
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(input);
    } else if (e.key === "Backspace" && !input && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  };

  const removeTag = (tag: string) => {
    onChange(value.filter((t) => t !== tag));
  };

  return (
    <div className="input flex flex-wrap gap-1.5 min-h-[42px] cursor-text" onClick={() => {
      const el = document.getElementById("tag-input-field");
      el?.focus();
    }}>
      {value.map((t) => (
        <TagChip key={t} name={t} clickable={false} onRemove={() => removeTag(t)} />
      ))}
      <input
        id="tag-input-field"
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => input && addTag(input)}
        placeholder={value.length === 0 ? "Add tags… (Enter or comma)" : ""}
        className="bg-transparent outline-none text-sm text-slate-100 placeholder-slate-500 flex-1 min-w-[160px]"
        aria-label="Tag input"
      />
      {input && (
        <button
          type="button"
          onClick={() => addTag(input)}
          className="text-brand-400 hover:text-brand-300"
          aria-label="Add tag"
        >
          <Plus size={14} />
        </button>
      )}
    </div>
  );
}
