import { useNavigate } from "react-router-dom";
import { Hash } from "lucide-react";

interface Props {
  name: string;
  /** If true, clicking navigates to search by tag */
  clickable?: boolean;
  onRemove?: () => void;
}

export default function TagChip({ name, clickable = true, onRemove }: Props) {
  const navigate = useNavigate();

  const handleClick = () => {
    if (clickable) {
      navigate(`/search?q=${encodeURIComponent(name)}&mode=keyword&tag=${encodeURIComponent(name)}`);
    }
  };

  return (
    <span
      className="tag-chip"
      onClick={clickable ? handleClick : undefined}
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
      onKeyDown={
        clickable
          ? (e) => e.key === "Enter" && handleClick()
          : undefined
      }
      aria-label={`Tag: ${name}`}
    >
      <Hash size={10} className="opacity-60" />
      {name}
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-0.5 hover:text-red-400 transition-colors"
          aria-label={`Remove tag ${name}`}
        >
          ×
        </button>
      )}
    </span>
  );
}
