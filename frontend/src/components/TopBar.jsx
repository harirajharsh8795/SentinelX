import { useEffect, useCallback } from "react";
import api from "../services/api.js";
import { useStore } from "../store/useStore.js";

export default function TopBar() {
  const setDocuments = useStore((state) => state.setDocuments);
  const documents = useStore((state) => state.documents);
  const selectedDocId = useStore((state) => state.selectedDocId);
  const setSelectedDocId = useStore((state) => state.setSelectedDocId);

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

  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between py-4 px-8 border-b border-white/5 bg-surface sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <div className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.8)]"></div>
        <h2 className="text-xl font-display font-medium text-white tracking-wide">
          COMMAND <span className="text-primary opacity-60">CENTER</span>
        </h2>
      </div>

      {/* Modern, glassmorphic active document selector */}
      {documents.length > 0 && (
        <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-1.5 shadow-[inset_0_0_8px_rgba(255,255,255,0.05)]">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Active Dossier:</span>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="bg-transparent border-none text-xs text-white focus:outline-none focus:ring-0 max-w-[280px] truncate cursor-pointer font-medium font-sans pr-2"
          >
            {documents.map((doc) => (
              <option key={doc.id} value={doc.id} className="bg-slate-900 text-white py-1">
                {doc.filename} {doc.regulator ? `[${doc.regulator}]` : ""}
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