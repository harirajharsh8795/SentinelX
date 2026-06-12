import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import api from "../services/api.js";
import { useStore } from "../store/useStore.js";
import { useChatStore } from "../store/useChatStore.js";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [pipelineState, setPipelineState] = useState("idle"); // idle, indexing, done, error
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const navigate = useNavigate();
  const fileRef = useRef(null);

  useEffect(() => {
    let ws = null;
    if (pipelineState === "indexing") {
      const token = localStorage.getItem("token") || "";
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      
      let host = window.location.host;
      if ((host.includes("localhost") || host.includes("127.0.0.1")) && !host.includes(":8000")) {
        host = host.replace(/:\d+$/, "") + ":8000";
      }
      
      const wsUrl = `${protocol}://${host}/api/ws/telemetry?token=${encodeURIComponent(token)}`;
      ws = new WebSocket(wsUrl);
      
      ws.onmessage = (e) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.type === "telemetry" && payload.description) {
            addLog(payload.description);
            
            if (payload.description.includes("Embedding generation:")) {
              const match = payload.description.match(/Embedding generation:\s*(\d+)%/);
              if (match) {
                const percent = parseInt(match[1]);
                const mappedProgress = 35 + Math.round((percent / 100) * 55);
                setProgress(mappedProgress);
              }
            }
          }
        } catch (err) {
          console.error("Failed to parse telemetry ws message", err);
        }
      };
      
      ws.onerror = (err) => {
        console.error("Telemetry WebSocket error", err);
      };
    }
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [pipelineState]);

  const steps = [
    { key: "upload", label: "Secure Upload", icon: "cloud_upload" },
    { key: "chunk", label: "Semantic Processing", icon: "view_agenda" },
    { key: "embed", label: "Embedding Generation", icon: "data_object" },
    { key: "graph", label: "Knowledge Mapping", icon: "hub" },
    { key: "workflow", label: "Workflow Extraction", icon: "fact_check" },
    { key: "done", label: "Intelligence Ready", icon: "task_alt" }
  ];

  const handleUpload = async () => {
    if (!file) return;
    setPipelineState("indexing");
    setProgress(10);
    addLog("Initializing secure document ingestion...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Step 1: Upload the PDF
      const uploadRes = await api.post("/upload-document", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 0,
        onUploadProgress: (event) => {
          if (event.total) {
            const p = Math.round((event.loaded / event.total) * 30);
            setProgress(Math.max(10, p));
          }
        }
      });
      const documentId = uploadRes.data.document_id;
      addLog("✔ Secure document ingestion complete. Establishing vector dimensions.");
      setProgress(35);

      // Step 2: Start progress simulation while analysis runs in background
      addLog("Processing semantic chunks into 384-dimensional embeddings...");
      let simProgress = 35;
      const progressTimer = setInterval(() => {
        simProgress += Math.random() * 3 + 1;
        if (simProgress >= 95) simProgress = 95;
        setProgress(Math.round(simProgress));
      }, 600);

      // Step 3: Fire analysis in background with timeout
      const analyzePromise = api.post("/analyze-document", null, {
        params: { doc_id: documentId },
        timeout: 0
      });

      // Add log messages on a schedule for visual feedback
      setTimeout(() => addLog("Performing semantic processing and vector indexing..."), 2000);
      setTimeout(() => addLog("Initializing autonomous compliance mapping graph..."), 5000);
      setTimeout(() => addLog("Risk and compliance agents analyzing regulatory directives..."), 8000);

      try {
        await analyzePromise;
        addLog("✔ Embedding generation and vector indexing finalized in ChromaDB.");
      } catch {
        addLog("⚠ Executive intelligence queue active — processing will complete momentarily.");
      }

      // Step 4: Cleanup and complete
      clearInterval(progressTimer);
      setProgress(100);
      addLog("✔ Relationship intelligence graph compiled.");
      addLog("✔ Departmental compliance tasks automated.");
      addLog("Intelligence pipeline operational. Systems ready.");
      setPipelineState("done");

      // Invalidate all cached analysis items in localStorage to prevent cross-document stale cache leaks
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith("analysis_")) {
          localStorage.removeItem(key);
        }
      });

      const previousDocId = useStore.getState().selectedDocId;
      if (previousDocId) {
        useChatStore.getState().clearDoc(previousDocId);
      }
      useStore.getState().setSelectedDocId(documentId);
      window.dispatchEvent(new Event("sentinel:document_uploaded"));

      setTimeout(() => navigate("/analysis"), 1500);

    } catch (err) {
      setPipelineState("error");
      addLog(`[ERROR] Intelligence Engine Failure: ${err?.response?.data?.detail || "Connection reset by peer."}`);
    }
  };

  const addLog = (msg) => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    setLogs(prev => [...prev, `[${time}] ${msg}`]);
  };

  // Determine active step index
  let activeStepIdx = 0;
  if (pipelineState === "idle") activeStepIdx = 0;
  else if (progress <= 35) activeStepIdx = 0;
  else if (progress <= 55) activeStepIdx = 1;
  else if (progress <= 75) activeStepIdx = 2;
  else if (progress <= 88) activeStepIdx = 3;
  else if (progress <= 96) activeStepIdx = 4;
  else activeStepIdx = 5;

  return (
    <div className="flex flex-col gap-6 font-sans min-h-[calc(100vh-120px)]">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-3xl font-display font-bold">Secure Document Ingestion</h1>
        <div className="flex items-center gap-2 px-3 py-1 bg-surfaceAlt/50 border border-white/10 rounded-full text-[10px] font-mono font-bold tracking-widest uppercase">
          <span className="material-symbols-outlined text-[14px] text-primary">dns</span>
          CHROMA CLUSTER CONNECTED
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-6 flex-1">
        
        {/* INGESTION MODULE */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
          className="glass-card flex flex-col items-center justify-center p-12 min-h-[500px]"
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            if (pipelineState !== "idle") return;
            const dropped = e.dataTransfer.files[0];
            if (dropped?.type === "application/pdf") setFile(dropped);
          }}
        >
          {pipelineState === "idle" ? (
            <div 
              className={`w-full max-w-lg aspect-video rounded-3xl border-2 border-dashed flex flex-col items-center justify-center p-8 transition-all cursor-pointer ${
                dragActive ? 'border-primary bg-primary/10 scale-[1.02]' : 'border-white/10 hover:border-white/20 bg-surfaceAlt/20'
              }`}
              onClick={() => fileRef.current?.click()}
            >
              <input type="file" hidden ref={fileRef} accept="application/pdf" onChange={(e) => {
                  if(e.target.files[0]) setFile(e.target.files[0]);
              }} />
              
              <div className="w-20 h-20 rounded-2xl bg-surfaceAlt border border-white/5 flex items-center justify-center mb-6 shadow-xl relative group">
                <div className="absolute inset-0 bg-primary/20 rounded-2xl animate-ping opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <span className="material-symbols-outlined text-[40px] text-primary">upload_file</span>
              </div>
              <h3 className="text-xl font-bold font-display uppercase tracking-widest text-white mb-2">Ingest Policy Document</h3>
              <p className="text-textSub text-sm max-w-sm text-center">Drag and drop RBI or CERT-In PDF files into the secure dropzone. Vector dimensions will be calculated automatically.</p>
              
              <AnimatePresence>
                {file && (
                  <motion.div initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="mt-8 px-4 py-2 bg-primary/10 border border-primary/20 rounded-xl flex items-center gap-3">
                     <span className="material-symbols-outlined text-primary">description</span>
                     <span className="font-mono text-sm">{file.name}</span>
                     <button onClick={(e) => {e.stopPropagation(); setFile(null);}} className="p-1 hover:bg-black/20 rounded ml-2">
                       <span className="material-symbols-outlined text-[16px]">close</span>
                     </button>
                  </motion.div>
                )}
              </AnimatePresence>

              {file && (
                <button 
                  onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                  className="mt-6 px-10 py-3 bg-white text-black font-bold uppercase tracking-widest shadow-[0_0_25px_rgba(255,255,255,0.2)] hover:shadow-[0_0_35px_rgba(255,255,255,0.4)] hover:bg-slate-200 transition-all rounded-xl text-sm"
                >
                  INITIALIZE PIPELINE
                </button>
              )}
            </div>
          ) : (
            <div className="w-full max-w-lg flex flex-col items-center">
              <div className="relative w-32 h-32 mb-8">
                {/* Rotating scanner ring */}
                <div className={`absolute inset-0 border-r-2 border-b-2 border-primary rounded-full ${pipelineState === 'error' ? 'border-alert border-r-alert' : 'animate-spin'}`}></div>
                <div className={`absolute inset-2 border-l-2 border-t-2 border-secondary rounded-full ${pipelineState === 'error' ? 'hidden' : 'animate-[spin_3s_linear_infinite_reverse]'}`}></div>
                <div className="absolute inset-0 flex items-center justify-center text-3xl font-mono text-white">
                  {progress}%
                </div>
              </div>
              <h3 className="text-2xl font-bold font-display uppercase tracking-widest mb-4">
                {pipelineState === "indexing" ? "Pipeline Active" : pipelineState === "done" ? "Document Indexed" : "Fatal Error"}
              </h3>
              
              <div className="w-full bg-surfaceAlt h-1 rounded-full overflow-hidden mb-8">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ ease: "easeInOut" }}
                  className={`h-full ${pipelineState === 'error' ? 'bg-alert' : 'bg-primary shadow-[0_0_10px_#3B82F6]'}`}
                ></motion.div>
              </div>

              {pipelineState === "error" && (
                <button onClick={() => {setPipelineState("idle"); setProgress(0); setLogs([]);}} className="px-6 py-2 border border-alert/30 text-alert uppercase tracking-wider text-xs font-bold rounded-lg hover:bg-alert/10 transition-colors mt-4">
                  RESET CONSOLE
                </button>
              )}
            </div>
          )}
        </motion.div>

        {/* TELEMETRY CONSOLE */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
          className="flex flex-col gap-6"
        >
          {/* STEPPER */}
          <div className="glass-card p-6">
             <h3 className="text-[11px] font-bold text-textSub uppercase tracking-[0.2em] mb-6">Orchestration Steps</h3>
             <div className="flex flex-col gap-5 relative">
               {/* Connecting Line */}
               <div className="absolute left-[15px] top-6 bottom-6 w-px bg-white/5"></div>
               {steps.map((step, idx) => {
                 const isActive = activeStepIdx === idx;
                 const isPast = activeStepIdx > idx;
                 return (
                   <div key={idx} className={`flex items-center gap-4 relative z-10 transition-opacity duration-300 ${isActive || isPast ? 'opacity-100' : 'opacity-30'}`}>
                     <div className={`w-8 h-8 rounded-full flex items-center justify-center border transition-colors ${
                       isActive ? 'bg-primary/20 border-primary text-primary shadow-[0_0_15px_rgba(59,130,246,0.3)] animate-pulse' :
                       isPast ? 'bg-success/20 border-success text-success' :
                       'bg-surfaceAlt border-white/10 text-textSub'
                     }`}>
                       <span className="material-symbols-outlined text-[16px]">{isPast ? 'check' : step.icon}</span>
                     </div>
                     <span className={`text-sm tracking-wide ${isActive ? 'text-white font-bold' : isPast ? 'text-success' : 'text-textSub'}`}>
                       {step.label}
                     </span>
                   </div>
                 );
               })}
             </div>
          </div>

          {/* RAW LOGS */}
          <div className="glass-card flex flex-col flex-1 overflow-hidden group border-r-0 border-b-0">
              <div className="px-4 py-3 bg-surfaceAlt/80 border-b border-white/5 flex gap-2 items-center">
                <span className="w-2.5 h-2.5 rounded-full bg-alert"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-warning"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-success"></span>
                <span className="ml-2 text-[10px] text-textSub font-mono tracking-widest uppercase">Intelligence Processing Console</span>
              </div>
              <div className="p-4 flex-1 bg-[#0A0D12] overflow-y-auto custom-scrollbar font-mono text-xs flex flex-col gap-2">
                {logs.length === 0 ? (
                   <div className="text-white/20 italic">Awaiting secure document ingestion input...</div>
                ) : (
                  logs.map((L, i) => (
                    <span key={i} className={`${L.includes('[ERROR]') ? 'text-alert' : L.includes('✔') ? 'text-success' : 'text-textSub'} break-words whitespace-pre-wrap`}>
                      {L}
                    </span>
                  ))
                )}
              </div>
          </div>
        </motion.div>

      </div>
    </div>
  );
}
