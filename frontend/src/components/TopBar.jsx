import { useEffect, useCallback, useState, useRef } from "react";
import api from "../services/api.js";
import { useStore } from "../store/useStore.js";

export default function TopBar() {
  const setDocuments = useStore((state) => state.setDocuments);
  const documents = useStore((state) => state.documents);
  const selectedDocId = useStore((state) => state.selectedDocId);
  const setSelectedDocId = useStore((state) => state.setSelectedDocId);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

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

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const activeDoc = documents.find((d) => d.id === selectedDocId) || documents[0];

  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between py-4 px-8 border-b border-white/5 bg-surface sticky top-0 z-30 font-sans">
      <div className="flex items-center gap-4">
        <div className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.8)]"></div>
        <h2 className="text-xl font-display font-medium text-white tracking-wide">
          COMMAND <span className="text-primary opacity-60">CENTER</span>
        </h2>
      </div>

      {/* Modern, custom glassmorphic active document selector (prevents browser/extension input overlay issues) */}
      {documents.length > 0 && (
        <div ref={dropdownRef} className="relative">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-1.5 shadow-[inset_0_0_8px_rgba(255,255,255,0.05)] text-xs text-white hover:bg-white/10 transition-all focus:outline-none cursor-pointer"
          >
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Active Dossier:</span>
            <span className="max-w-[200px] truncate font-medium">
              {activeDoc ? `${activeDoc.filename} ${activeDoc.regulator ? `[${activeDoc.regulator}]` : ""}` : "Select Dossier..."}
            </span>
            <span 
              className="material-symbols-outlined text-[14px] text-slate-400 transition-transform duration-200" 
              style={{ transform: isOpen ? "rotate(180deg)" : "none" }}
            >
              expand_more
            </span>
          </button>
          
          {isOpen && (
            <div className="absolute left-0 mt-2 w-80 bg-slate-900 border border-white/10 rounded-xl shadow-2xl py-1.5 z-50 backdrop-blur-xl max-h-60 overflow-y-auto custom-scrollbar">
              {documents.map((doc) => (
                <button
                  key={doc.id}
                  onClick={() => {
                    setSelectedDocId(doc.id);
                    setIsOpen(false);
                  }}
                  className={`w-full px-4 py-2.5 text-left text-xs transition-colors hover:bg-white/5 flex flex-col gap-0.5 border-none bg-transparent cursor-pointer ${
                    doc.id === selectedDocId ? "text-primary bg-primary/10 font-medium" : "text-slate-300"
                  }`}
                >
                  <span className="truncate">{doc.filename}</span>
                  {doc.regulator && (
                    <span className="text-[9px] uppercase tracking-wider text-slate-500 font-mono">
                      {doc.regulator} {doc.framework ? `• ${doc.framework}` : ""}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
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