import { useEffect, useCallback } from "react";
import api from "../services/api.js";
import { useStore } from "../store/useStore.js";

export default function TopBar() {
  const setDocuments = useStore((state) => state.setDocuments);
  const documents = useStore((state) => state.documents);
  const selectedDocId = useStore((state) => state.selectedDocId);

  const fetchDocuments = useCallback(() => {
    api.get("/documents")
      .then((res) => {
        const docs = res.data.documents || [];
        setDocuments(docs);
      })
      .catch((err) => console.error("Error loading documents:", err));
  }, [setDocuments]);

  useEffect(() => {
    fetchDocuments();
    window.addEventListener("sentinel:document_uploaded", fetchDocuments);
    return () => window.removeEventListener("sentinel:document_uploaded", fetchDocuments);
  }, [fetchDocuments]);

  const activeDoc = documents.find((d) => d.id === selectedDocId) || documents[0];

  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between py-4 px-8 border-b border-white/5 bg-surface sticky top-0 z-30 font-sans">
      <div className="flex items-center gap-4">
        <div className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.8)]"></div>
        <h2 className="text-xl font-display font-medium text-white tracking-wide">
          COMMAND <span className="text-primary opacity-60">CENTER</span>
        </h2>
      </div>

      {documents.length > 0 && (
        <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-1.5 shadow-[inset_0_0_8px_rgba(255,255,255,0.05)] text-xs text-white">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Active Dossier:</span>
          <select
            value={selectedDocId}
            onChange={(e) => useStore.getState().setSelectedDocId(e.target.value)}
            className="bg-transparent text-white border-none focus:outline-none cursor-pointer max-w-[200px] truncate font-medium"
          >
            {documents.map((d) => (
              <option key={d.id} value={d.id} className="bg-[#1e293b] text-white">
                {d.filename} {d.regulator ? `[${d.regulator}]` : ""}
              </option>
            ))}
          </select>
        </div>
      )}
      
      <div className="flex items-center gap-4">
        <div className="bg-primary/10 border border-primary/30 text-primary rounded-full px-4 py-1.5 text-[10px] font-mono uppercase tracking-wider flex items-center gap-2">
          <span className="material-symbols-outlined text-[14px]">public</span> Network Secure
        </div>
      </div>
    </div>
  );
}