import { useState, useRef, useEffect } from "react";
import GlassCard from "../components/GlassCard.jsx";
import CitationCard from "../components/CitationCard.jsx";
import ChatMessage from "../components/ChatMessage.jsx";
import api from "../services/api.js";
import { useStore } from "../store/useStore.js";
import { useChatStore } from "../store/useChatStore.js";
import { requestManager } from "../services/globalRequestManager.js";
import { Link } from "react-router-dom";
import ReasoningTimeline from "../components/ReasoningTimeline.jsx";


const THINKING_MESSAGES = [
  "Retrieving relevant clauses...",
  "Cross-referencing regulations...",
  "Analyzing compliance gaps...",
  "Synthesizing intelligence...",
  "Validating against document...",
  "Generating structured response..."
];

const formatTime = (s) => 
  `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

export default function Chat() {
  const docId = useStore((state) => state.selectedDocId);
  
  const {
    getMessages,
    addMessage,
    updateLastMessage,
    pendingGraphQuery,
    clearPendingGraphQuery,
    setRequestStatus,
    getRequestStatus,
    setPayload,
    clearPayload
  } = useChatStore();

  const messages = getMessages(docId);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [inspectSource, setInspectSource] = useState(null);
  const endRef = useRef(null);
  const [thinkingIndex, setThinkingIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false);
  const [fullCoverage, setFullCoverage] = useState(false);

  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Mounted flag to guard all setState calls from background threads/promises
  const isMounted = useRef(true);

  // Safe wrappers for setState to prevent state changes on unmounted component
  const safeSetInput = (val) => {
    if (isMounted.current) setInput(val);
  };
  const safeSetLoading = (val) => {
    if (isMounted.current) setLoading(val);
  };
  const safeSetInspectSource = (val) => {
    if (isMounted.current) setInspectSource(val);
  };
  const safeSetRecording = (val) => {
    if (isMounted.current) setRecording(val);
  };
  const safeSetTranscribing = (val) => {
    if (isMounted.current) setTranscribing(val);
  };

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    const status = getRequestStatus(docId);
    if (status === "processing") {
      setLoading(true);

      // Restore active background request if browser was refreshed
      if (requestManager.getStatus(docId) !== "processing") {
        const payload = useChatStore.getState().activePayloads[docId];
        if (payload) {
          console.log("Restoring background request after refresh for document:", docId);
          const apiCall = () => api.post("/chat", payload, { timeout: 90000 });
          requestManager.startRequest(docId, apiCall)
            .then((response) => {
              updateLastMessage(docId, response.data.reply, {
                sources: response.data.sources,
                debug: response.data.debug,
                grounded: response.data.grounded,
                grounding_confidence: response.data.grounding_confidence
              });
              setRequestStatus(docId, "complete");
              clearPayload(docId);
              if (isMounted.current) {
                setLoading(false);
              }
            })
            .catch((error) => {
              const errMsg = error?.response?.data?.detail || error?.message || "Request failed";
              updateLastMessage(docId, `Error: ${errMsg}`);
              setRequestStatus(docId, "error");
              clearPayload(docId);
              if (isMounted.current) {
                setLoading(false);
              }
            });
        } else {
          // Fallback if payload isn't found to avoid infinite loading state
          setRequestStatus(docId, "idle");
          setLoading(false);
        }
      }

      requestManager.setOnComplete(docId, (response) => {
        updateLastMessage(docId, response.data.reply, {
          sources: response.data.sources,
          debug: response.data.debug,
          grounded: response.data.grounded,
          grounding_confidence: response.data.grounding_confidence
        });
        setRequestStatus(docId, "complete");
        clearPayload(docId);
        if (isMounted.current) {
          setLoading(false);
        }
      });
      requestManager.setOnError(docId, (error) => {
        const errMsg = error?.response?.data?.detail || error?.message || "Request failed";
        updateLastMessage(docId, `Error: ${errMsg}`);
        setRequestStatus(docId, "error");
        clearPayload(docId);
        if (isMounted.current) {
          setLoading(false);
        }
      });
    } else {
      setLoading(false);
    }
  }, [docId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendAudioToBackend(audioBlob);
        stream.getTracks().forEach(track => track.stop()); // release mic
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      safeSetRecording(true);
    } catch (err) {
      console.error("Microphone access failed", err);
      alert("Microphone access is required to use voice features.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      safeSetRecording(false);
    }
  };

  const sendAudioToBackend = async (blob) => {
    safeSetTranscribing(true);
    const formData = new FormData();
    formData.append("file", blob, "voice_query.webm");
    
    try {
      const response = await api.post("/voice/transcribe", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      if (response.data && response.data.text) {
        const transcription = response.data.text;
        safeSetInput(transcription);
        // Fire search query directly
        sendQuery(transcription);
      }
    } catch (err) {
      console.error("Failed to transcribe audio", err);
    } finally {
      safeSetTranscribing(false);
    }
  };

  const sendQuery = (queryText) => {
    if (!queryText.trim() || !docId) return;

    safeSetInput("");
    
    // Add user and assistant placeholder messages
    addMessage(docId, {
      id: Date.now(),
      role: "user",
      content: queryText,
      timestamp: new Date().toISOString()
    });

    addMessage(docId, {
      id: Date.now() + 1,
      role: "assistant",
      content: "",
      isStreaming: true,
      timestamp: new Date().toISOString()
    });

    const payload = {
      document_id: docId,
      message: queryText,
      full_coverage_mode: fullCoverage
    };

    if (pendingGraphQuery && pendingGraphQuery.query === queryText) {
      payload.chunk_ids = pendingGraphQuery.chunk_ids || [];
      payload.source_section = pendingGraphQuery.source_section || "";
      payload.source_text = pendingGraphQuery.source_text || "";
      payload.graph_context_mode = pendingGraphQuery.graph_context_mode || false;
    }

    setRequestStatus(docId, "processing");
    setPayload(docId, payload);
    safeSetLoading(true);

    const apiCall = () => api.post(
      "/chat",
      payload,
      { timeout: 90000 }
    );

    // Clear any previous request state for this doc in manager to ensure a fresh request starts
    requestManager.clear(docId);

    requestManager.startRequest(docId, apiCall)
      .then((response) => {
        updateLastMessage(docId, response.data.reply, {
          sources: response.data.sources,
          debug: response.data.debug,
          grounded: response.data.grounded,
          grounding_confidence: response.data.grounding_confidence
        });
        setRequestStatus(docId, "complete");
        clearPayload(docId);
        if (isMounted.current) {
          setLoading(false);
        }
      })
      .catch((error) => {
        const errMsg = error?.response?.data?.detail || error?.message || "Request failed";
        updateLastMessage(docId, `Error: ${errMsg}`);
        setRequestStatus(docId, "error");
        clearPayload(docId);
        if (isMounted.current) {
          setLoading(false);
        }
      });
  };

  const handleSend = () => sendQuery(input);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isJetson = import.meta.env.VITE_JETSON_MODE === "true";

  useEffect(() => {
    if (!loading) return;
    const interval = setInterval(() => {
      setThinkingIndex(i => (i + 1) % THINKING_MESSAGES.length);
    }, 2500);
    return () => clearInterval(interval);
  }, [loading]);

  useEffect(() => {
    if (!loading) {
      setElapsed(0); return;
    }
    const timer = setInterval(() => {
      setElapsed(e => e + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [loading]);

  useEffect(() => {
    if (!pendingGraphQuery) return;
    
    const age = Date.now() - pendingGraphQuery.timestamp;
    if (age > 5 * 60 * 1000) {
      clearPendingGraphQuery();
      return;
    }
    
    setInput(pendingGraphQuery.query);
    
    const timer = setTimeout(() => {
      sendQuery(pendingGraphQuery.query);
      clearPendingGraphQuery();
    }, 500);

    return () => clearTimeout(timer);
  }, [pendingGraphQuery, docId]);

  if (!docId) {
    return (
      <div className="flex flex-col items-center justify-center h-[80vh] text-center space-y-4 font-sans">
        <h2 className="text-2xl font-display text-white">No Document Active</h2>
        <p className="text-slate-400">Please upload a document to initialize the Intelligence Copilot.</p>
        <Link to="/upload" className="px-6 py-2 bg-primary/20 text-primary border border-primary/30 rounded-full hover:bg-primary transition">
          Upload Document
        </Link>
      </div>
    );
  }

  return (
    <div className="grid h-[85vh] gap-8">
      <GlassCard className="flex flex-col h-full overflow-hidden p-0 relative">
        {/* Header */}
        <div className="px-8 py-5 border-b border-white/10 bg-gradient-to-r from-black/40 to-black/10">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-display text-mint">Intelligence Copilot</h3>
              <p className="text-sm text-slate-200/60 mt-1">Multi-turn RAG Chat • MMR Retrieval • Dynamic Prompts</p>
            </div>
            {docId ? (
              <span className="px-3 py-1 bg-mint/20 text-mint text-xs rounded-full border border-mint/30">
                Document Indexed & Active
              </span>
            ) : (
              <span className="px-3 py-1 bg-red-500/20 text-red-400 text-xs rounded-full border border-red-500/30">
                Awaiting Document
              </span>
            )}
          </div>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
              {/* Message Bubble */}
              <div 
                className={`max-w-[85%] p-5 rounded-2xl shadow-lg ${
                  msg.role === "user" 
                    ? "bg-gradient-to-br from-mint to-teal-500 text-black rounded-tr-sm whitespace-pre-wrap" 
                    : "bg-white/5 border border-white/10 text-slate-200 rounded-tl-sm"
                }`}
              >
                {msg.role === "user" ? (
                  msg.content
                ) : msg.isStreaming && !msg.content ? (
                  <ReasoningTimeline />
                ) : (
                  <ChatMessage content={msg.content} isNew={idx === messages.length - 1 && !msg.isStreaming && (Date.now() - new Date(msg.timestamp || 0).getTime() < 8000)} />
                )}
              </div>

              {msg.role === "assistant" && (msg.grounding_confidence != null || msg.sources?.length > 0) && (
                <div className="mt-2 flex items-center gap-2 text-xs">
                  <span className={`px-2 py-0.5 rounded-full border ${
                    msg.grounded ? "bg-mint/10 text-mint border-mint/30" : "bg-red-500/10 text-red-400 border-red-500/30"
                  }`}>
                    {msg.grounded ? "✓ Grounded" : "⚠ Ungrounded"}
                  </span>
                  {msg.grounding_confidence != null && (
                    <span className="text-slate-500">Confidence: {(msg.grounding_confidence * 100).toFixed(0)}%</span>
                  )}
                </div>
              )}

              {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 max-w-[85%] w-full space-y-3">
                  <details className="group bg-black/30 border border-white/5 rounded-xl overflow-hidden text-sm" open>
                    <summary className="cursor-pointer p-3 font-semibold text-slate-400 hover:text-mint transition-colors select-none flex items-center justify-between">
                      <span>Sources & AI Reasoning</span>
                      <span className="group-open:rotate-180 transition-transform">▼</span>
                    </summary>
                    <div className="p-4 border-t border-white/5 space-y-4">
                      {msg.debug?.reasoning_steps && (
                        <div className="bg-blue-900/10 p-3 rounded-lg border border-blue-500/20">
                          <h4 className="text-blue-400 font-bold mb-2">Reasoning transparency</h4>
                          <ol className="list-decimal list-inside text-slate-300 space-y-1 text-xs">
                            {msg.debug.reasoning_steps.map((step, i) => (
                              <li key={i}>{step}</li>
                            ))}
                          </ol>
                        </div>
                      )}
                      <div className="grid gap-2">
                        {msg.sources.map((src, sIdx) => (
                          <CitationCard
                            key={sIdx}
                            source={src}
                            index={sIdx}
                            onInspect={(s) => safeSetInspectSource(s)}
                          />
                        ))}
                      </div>
                    </div>
                  </details>
                </div>
              )}
            </div>
          ))}
          <div ref={endRef} />
        </div>

        {/* Suggested Follow-ups */}
        {showTimeoutWarning && (
          <div className="px-8 pb-3 text-yellow-400 text-xs flex items-center gap-3">
            <span>⏱️ Query is complex for current hardware. Showing partial results...</span>
            <button 
              onClick={() => {
                const lastUserMsg = [...messages].reverse().find(m => m.role === "user");
                if (lastUserMsg) {
                  sendQuery(lastUserMsg.content);
                }
              }}
              className="px-3 py-1 bg-yellow-500/20 hover:bg-yellow-500/30 border border-yellow-500/40 rounded transition-colors text-xs font-bold"
            >
              Retry
            </button>
          </div>
        )}
        {!loading && messages.length > 1 && messages[messages.length-1].role === "assistant" && (
          <div className="px-8 pb-3 flex gap-2 flex-wrap">
            {["What are the exact penalties?", "Summarize the audit timelines", "Show me governance requirements"].map((suggestion, i) => (
              <button 
                key={i}
                onClick={() => sendQuery(suggestion)}
                className="text-xs bg-white/5 hover:bg-mint/20 hover:text-mint hover:border-mint/50 border border-white/10 text-slate-300 px-3 py-1.5 rounded-full transition-all"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div className="p-6 border-t border-white/10 bg-[#0B1120]">
          {recording && (
            <div className="mb-3 flex items-center gap-3 text-xs text-red-400 animate-pulse">
              <span className="h-2.5 w-2.5 rounded-full bg-red-500 animate-ping"></span>
              Recording audio query (Hindi + English supported)... Speak now
            </div>
          )}
          {transcribing && (
            <div className="mb-3 flex items-center gap-3 text-xs text-mint animate-pulse">
              <span className="h-2.5 w-2.5 rounded-full bg-mint animate-ping"></span>
              Transcribing offline audio via faster-whisper...
            </div>
          )}
          
          <div className="mb-4 flex items-center justify-between">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setFullCoverage(prev => !prev)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                  fullCoverage
                    ? "bg-mint/20 text-mint border-mint/40 shadow-[0_0_10px_rgba(45,212,191,0.15)]"
                    : "bg-white/5 text-slate-400 border-white/10 hover:bg-white/10 hover:text-white"
                }`}
              >
                <span className="material-symbols-outlined text-[14px]">
                  {fullCoverage ? "verified_user" : "manage_search"}
                </span>
                {fullCoverage ? "Full Document Coverage Mode" : "Standard Context Mode"}
              </button>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              {fullCoverage ? "Retrieves complete document evidence chronologically" : "Retrieves targeted compliance semantic blocks"}
            </span>
          </div>

          <div className="flex gap-4 items-end">
            <textarea
              className="flex-1 bg-white/5 border border-white/10 rounded-2xl p-4 text-white placeholder-slate-400 focus:outline-none focus:border-mint focus:border-mint/30 focus:bg-white/10 resize-none transition-all"
              rows={2}
              placeholder={
                transcribing
                  ? "Transcribing audio..."
                  : docId
                    ? "Ask about compliance obligations, timelines, risks, or penalties..."
                    : "Awaiting document processing..."
              }
              value={input}
              onChange={(e) => safeSetInput(e.target.value)}
              onKeyDown={handleKey}
              disabled={!docId || loading || transcribing}
            />

            {recording ? (
              <button
                type="button"
                onClick={stopRecording}
                className="bg-red-500/20 border border-red-500/40 text-red-400 p-4 rounded-2xl h-[56px] w-[56px] flex items-center justify-center animate-pulse hover:bg-red-500/30 transition-all"
                title="Stop recording and transcribe"
              >
                <svg viewBox="0 0 24 24" className="h-6 w-6 fill-current">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
              </button>
            ) : (
              <button
                type="button"
                onClick={startRecording}
                disabled={!docId || loading || transcribing}
                className="bg-white/5 border border-white/10 hover:bg-mint/20 hover:text-mint hover:border-mint/30 text-white p-4 rounded-2xl h-[56px] w-[56px] flex items-center justify-center disabled:opacity-30 transition-all"
                title="Record voice query"
              >
                <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" />
                </svg>
              </button>
            )}

            <button
              onClick={handleSend}
              disabled={!input.trim() || !docId || loading || transcribing}
              className="bg-gradient-to-r from-mint to-teal-600 text-black px-8 py-4 rounded-2xl font-bold disabled:opacity-50 hover:opacity-90 transition-opacity shadow-lg shadow-mint/20 h-[56px] flex items-center"
            >
              Analyze
            </button>
          </div>
        </div>
      </GlassCard>

      {inspectSource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70" onClick={() => safeSetInspectSource(null)}>
          <div className="bg-[#0d1117] border border-mint/30 rounded-2xl p-6 max-w-lg w-full" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-mint font-bold mb-2">{inspectSource.section_title}</h3>
            <p className="text-slate-300 text-sm leading-relaxed">{inspectSource.snippet}</p>
            <button type="button" onClick={() => safeSetInspectSource(null)} className="mt-4 text-sm text-slate-500 hover:text-white">Close</button>
          </div>
        </div>
      )}
    </div>
  );
}