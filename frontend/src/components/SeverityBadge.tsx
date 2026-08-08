import type { Severity } from "../api/types";

const COLORS: Record<Severity, string> = {
  low:      "bg-slate-700 text-slate-300",
  medium:   "bg-blue-900/60 text-blue-300",
  high:     "bg-amber-900/60 text-amber-300",
  critical: "bg-red-900/60 text-red-400 ring-1 ring-red-700",
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={`severity-badge ${COLORS[severity]}`}>{severity}</span>
  );
}
