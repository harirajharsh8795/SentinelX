import { useState, useCallback, useEffect } from "react";
import useWebsocket from "../hooks/useWebsocket.js";

export default function Notifications() {
  const [items, setItems] = useState([]);

  const token = localStorage.getItem("token");
  const activeDocId = localStorage.getItem("document_id") || "NO_DOC";

  const handleMessage = useCallback((payload) => {
    if (!payload) return;
    
    if (payload.type === "alert" || payload.type === "notification") {
      const msgText = payload.message || payload.title || "Alert received";

      setItems((prevItems) => {
        // Deduplicate: ignore if we already have the same message in the list
        const isDuplicate = prevItems.some(
          (it) => (it.message === msgText || it.title === msgText) && Date.now() - it.id < 10000
        );
        if (isDuplicate) return prevItems;

        const newId = Date.now();
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
          setItems((s) => s.filter((item) => item.id !== newId));
        }, 5000);

        const newAlert = {
          id: newId,
          title: payload.title || "Alert",
          severity: payload.severity || "Medium",
          message: msgText,
        };

        const event = new CustomEvent("sentinel:toast", {
          detail: { message: msgText, type: "info" },
        });
        window.dispatchEvent(event);

        return [newAlert, ...prevItems].slice(0, 6);
      });
    }
  }, []);

  useWebsocket(handleMessage, { path: `/api/ws/alerts/${activeDocId}`, token });

  const handleClose = (id) => {
    setItems((s) => s.filter((item) => item.id !== id));
  };

  if (items.length === 0) return null;

  return (
    <div className="fixed right-6 top-20 z-50 flex w-80 flex-col gap-3">
      {items.map((it) => {
        const severityColors = {
          High: "border-red-500/30 bg-red-950/80 text-red-200",
          Medium: "border-amber-500/30 bg-amber-950/80 text-amber-200",
          Low: "border-blue-500/30 bg-blue-950/80 text-blue-200",
        };
        const colorClass = severityColors[it.severity] || "border-white/10 bg-slate-900/80 text-white";

        return (
          <div
            key={it.id}
            className={`glass-card p-3.5 rounded-xl border text-sm flex items-start justify-between shadow-2xl transition-all duration-300 ${colorClass}`}
          >
            <div className="flex-1 pr-3">
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-current animate-ping" />
                <span className="font-semibold text-[10px] tracking-wider uppercase opacity-80">{it.severity || "INFO"}</span>
              </div>
              <div className="font-semibold mt-1 text-slate-100 text-sm leading-tight">{it.title}</div>
              <div className="text-xs text-slate-300 mt-1 leading-relaxed">{it.message}</div>
            </div>
            <button
              onClick={() => handleClose(it.id)}
              className="text-slate-400 hover:text-slate-200 text-lg font-bold leading-none p-1 rounded hover:bg-white/10 transition-colors cursor-pointer"
              title="Dismiss"
            >
              &times;
            </button>
          </div>
        );
      })}
    </div>
  );
}
