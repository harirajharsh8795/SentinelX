import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const ROUTES = [
  { label: "Dashboard", path: "/dashboard", keys: "g d" },
  { label: "Upload Document", path: "/upload", keys: "g u" },
  { label: "Document Analysis", path: "/analysis", keys: "g a" },
  { label: "AI Chat Copilot", path: "/chat", keys: "g c" },
  { label: "Knowledge Graph", path: "/graph", keys: "g k" },
  { label: "Tasks", path: "/tasks", keys: "g t" },
  { label: "Analytics", path: "/analytics", keys: "g n" },
  { label: "Agent Logs", path: "/agent-logs", keys: "g l" },
  { label: "Audit Trail", path: "/audit", keys: "g r" },
];

export default function CommandPalette({ open = true, onClose }) {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const filtered = ROUTES.filter((r) =>
    r.label.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  const go = (path) => {
    navigate(path);
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] px-4">
      <div className="absolute inset-0 bg-black/85" onClick={onClose} />
      <div className="relative w-full max-w-lg bg-[#0d1117] border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
        <input
          autoFocus
          className="w-full px-5 py-4 bg-transparent text-white placeholder-slate-500 border-b border-white/10 focus:outline-none text-lg"
          placeholder="Type a command or search pages..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Escape") onClose();
            if (e.key === "Enter" && filtered[0]) go(filtered[0].path);
          }}
        />
        <ul className="max-h-72 overflow-y-auto py-2">
          {filtered.map((r) => (
            <li key={r.path}>
              <button
                type="button"
                onClick={() => go(r.path)}
                className="w-full px-5 py-3 flex justify-between items-center hover:bg-mint/10 text-left text-slate-200 hover:text-mint transition"
              >
                <span>{r.label}</span>
                <kbd className="text-xs text-slate-500 font-mono">{r.keys}</kbd>
              </button>
            </li>
          ))}
          {filtered.length === 0 && (
            <li className="px-5 py-4 text-slate-500 text-sm">No matching commands</li>
          )}
        </ul>
        <div className="px-5 py-2 border-t border-white/5 text-xs text-slate-500 flex gap-4">
          <span>↑↓ navigate</span>
          <span>↵ open</span>
          <span>esc close</span>
        </div>
      </div>
    </div>
  );
}
