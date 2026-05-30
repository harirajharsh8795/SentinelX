import { useState, useRef, useEffect } from "react";
import GlassCard from "../components/GlassCard.jsx";
import CitationCard from "../components/CitationCard.jsx";
import api from "../services/api.js";
import { useStore } from "../store/useStore.js";
import { Link } from "react-router-dom";

// Utility to render rich text with lists, bolding, and inline code
const formatText = (text) => {
  if (!text) return null;
  const lines = text.split("\n");
  
  return lines.map((line, lineIdx) => {
    const isBullet = line.trim().startsWith("•") || line.trim().startsWith("-");
    const cleanLine = isBullet ? line.trim().substring(1).trim() : line;

    const parts = cleanLine.split(/(\*\*.*?\*\*|`.*?`)/g);
    const lineContent = parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i} className="font-extrabold text-mint">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith("`") && part.endsWith("`")) {
        return <code key={i} className="font-mono bg-black/40 text-accent px-1.5 py-0.5 rounded text-xs">{part.slice(1, -1)}</code>;
      }
      return <span key={i}>{part}</span>;
    });

    if (isBullet) {
      return (
        <li key={lineIdx} className="ml-4 list-disc text-slate-100 mb-1">
          {lineContent}
        </li>
      );
    }

    return (
      <p key={lineIdx} className="mb-1.5 text-slate-100 leading-relaxed">
        {lineContent}
      </p>
    );
  });
};

export default function Chat() {
  const docId = useStore((state) => state.selectedDocId);
  const [messages, setMessages] = useState([
    { 
      role: "assistant", 
      content: "Hello! I am SentinelX, your Autonomous Regulatory Intelligence & Compliance Operating System. I am ready to answer complex compliance queries based on the active document.",
      sources: null,
      debug: null
    }
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [inspectSource, setInspectSource] = useState(null);
  const endRef = useRef(null);
  const [thinkingIndex, setThinkingIndex] = useState(0);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false);

  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // WebSocket reference to ensure only one connection exists
  const wsRef = useRef(null);
  
  // Mounted flag to guard all setState calls from background threads/promises
  const isMounted = useRef(true);

  // Safe wrappers for setState to prevent state changes on unmounted component
  const safeSetMessages = (val) => {
    if (isMounted.current) setMessages(val);
  };
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
      // Cleanup WebSocket on unmount
      if (wsRef.current) {
        console.log("Component unmounting. Closing WebSocket.");
        wsRef.current.intentionalClose = true;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

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

  const sendQuery = (queryText, isRetry = false, retryAttempt = 0) => {
    if (!queryText.trim() || !docId) return;
    
    if (!isRetry) {
      safeSetInput("");
      safeSetMessages(prev => [...prev, { role: "user", content: queryText }]);
      safeSetLoading(true);
    }

    const token = localStorage.getItem("token") || "";
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    
    // Map development Vite ports (5173, 5174, 5200, etc.) to backend FastAPI port (8000)
    let host = window.location.host;
    if ((host.includes("localhost") || host.includes("127.0.0.1")) && !host.includes(":8000")) {
      host = host.replace(/:\d+$/, "") + ":8000";
    }

    // Requirement 5: Ensure only ONE WebSocket instance exists at a time. Close previous first.
    if (wsRef.current) {
      console.log("Closing previous WebSocket connection before opening a new one.");
      try {
        wsRef.current.intentionalClose = true;
        wsRef.current.close();
      } catch (err) {
        console.warn("Error closing existing WebSocket instance:", err);
      }
      wsRef.current = null;
    }
    
    const wsUrl = `${protocol}://${host}/api/ws/ai/${docId}?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.intentionalClose = false;

    if (!isRetry) {
      // Add empty assistant message that will be populated
      safeSetMessages(prev => [...prev, { 
        role: "assistant", 
        content: "",
        sources: null,
        debug: null
      }]);
    } else {
      // Clear previous assistant message content so it streams fresh on reconnect retry
      safeSetMessages(prev => {
        if (prev.length === 0) return prev;
        const newMessages = [...prev];
        const lastIdx = newMessages.length - 1;
        newMessages[lastIdx] = {
          ...newMessages[lastIdx],
          content: "[Connection Replaced. Streaming fresh response...]\n",
          sources: null,
          debug: null
        };
        return newMessages;
      });
      safeSetLoading(true);
    }

    ws.onopen = () => {
      console.log("WebSocket connection established.");
      ws.send(JSON.stringify({ message: queryText }));
    };

    ws.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.type === "token") {
          safeSetLoading(false);
          safeSetMessages(prev => {
            if (prev.length === 0) return prev;
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            newMessages[lastIdx] = {
              ...newMessages[lastIdx],
              content: newMessages[lastIdx].content + payload.data
            };
            return newMessages;
          });
        } else if (payload.type === "done") {
          ws.intentionalClose = true;
          safeSetMessages(prev => {
            if (prev.length === 0) return prev;
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            newMessages[lastIdx] = {
              ...newMessages[lastIdx],
              sources: payload.sources,
              debug: payload.debug,
              grounding_confidence: payload.grounding_confidence,
              grounded: payload.grounded
            };
            return newMessages;
          });
          ws.close();
        } else if (payload.type === "error") {
          ws.intentionalClose = true;
          safeSetMessages(prev => {
            if (prev.length === 0) return prev;
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            newMessages[lastIdx] = {
              ...newMessages[lastIdx],
              content: "Error: " + payload.message
            };
            return newMessages;
          });
          safeSetLoading(false);
          ws.close();
        }
      } catch (err) {
        console.error("Failed to parse WS message", err);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket encountered an error:", err);
    };

    // Requirement 3 & 4: Handle server disconnects gracefully & implement reconnection attempts
    ws.onclose = (event) => {
      console.log(`WebSocket closed (code: ${event.code}, intentional: ${ws.intentionalClose})`);
      
      // If disconnect was unintentional, try to reconnect
      if (!ws.intentionalClose) {
        if (retryAttempt < 3) {
          const nextAttempt = retryAttempt + 1;
          console.warn(`Unexpected connection drop. Reconnecting in 2s (Attempt ${nextAttempt}/3)...`);
          
          safeSetMessages(prev => {
            if (prev.length === 0) return prev;
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            newMessages[lastIdx] = {
              ...newMessages[lastIdx],
              content: newMessages[lastIdx].content + `\n[Reconnecting... Attempt ${nextAttempt}/3]\n`
            };
            return newMessages;
          });

          setTimeout(() => {
            if (isMounted.current) {
              sendQuery(queryText, true, nextAttempt);
            }
          }, 2000);
        } else {
          // Max attempts exceeded
          console.error("Max reconnection attempts reached. Giving up.");
          safeSetMessages(prev => {
            if (prev.length === 0) return prev;
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            newMessages[lastIdx] = {
              ...newMessages[lastIdx],
              content: newMessages[lastIdx].content + "\n[System: Connection lost. Max reconnection attempts reached.]"
            };
            return newMessages;
          });
          safeSetLoading(false);
        }
      }
    };
  };

  const handleSend = () => sendQuery(input);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const thinkingMessages = [
    "Retrieving relevant clauses...",
    "Cross-referencing regulations...",
    "Analyzing compliance gaps...",
    "Synthesizing intelligence...",
    "Validating against document...",
    "Generating structured response..."
  ];

  const isJetsonMode = import.meta.env.VITE_JETSON_MODE === "true";

  useEffect(() => {
    let timerInterval;
    let msgInterval;
    let timeoutId;
    if (loading) {
      setTimerSeconds(0);
      setThinkingIndex(0);
      setShowTimeoutWarning(false);
      timerInterval = setInterval(() => {
        setTimerSeconds(prev => prev + 1);
      }, 1000);
      msgInterval = setInterval(() => {
        setThinkingIndex(prev => (prev + 1) % thinkingMessages.length);
      }, 3000);
      timeoutId = setTimeout(() => {
        setShowTimeoutWarning(true);
        safeSetLoading(false);
        safeSetMessages(prev => {
          if (prev.length === 0) return prev;
          const newMessages = [...prev];
          const lastIdx = newMessages.length - 1;
          newMessages[lastIdx] = {
            ...newMessages[lastIdx],
            content: "⏱️ Query is complex for current hardware. Showing partial results...",
            sources: [],
            debug: { reasoning_steps: ["Query timed out after 90 seconds."] }
          };
          return newMessages;
        });
        if (wsRef.current) {
          wsRef.current.intentionalClose = true;
          wsRef.current.close();
        }
      }, 90000);
    } else {
      setTimerSeconds(0);
      setThinkingIndex(0);
    }
    return () => {
      clearInterval(timerInterval);
      clearInterval(msgInterval);
      clearTimeout(timeoutId);
    };
  }, [loading]);

  const simplifyGraphQuery = (query) => {
    if (!query) return query;
    const q = query.trim();
    if (q.startsWith("Analyze regulatory details") || q.startsWith("Analyze the regulatory details")) {
      let entity = "";
      const quoteMatch = q.match(/"([^"]+)"/);
      if (quoteMatch) {
        entity = quoteMatch[1];
      } else {
        const lastPartMatch = q.match(/associated with (?:the )?(\w+ )?(.+)$/i);
        if (lastPartMatch) {
          entity = lastPartMatch[2].replace(/\.+$/, "").trim();
        }
      }
      
      if (entity) {
        const lowerQ = q.toLowerCase();
        if (lowerQ.includes("penalty") || lowerQ.includes("penalties")) {
          return `What are the penalties for ${entity}?`;
        } else if (lowerQ.includes("risk") || lowerQ.includes("mitigation")) {
          return `What are the risks associated with ${entity}?`;
        } else if (lowerQ.includes("registration") || entity.toLowerCase().includes("registration")) {
          let cleanEntity = entity;
          if (entity.toLowerCase().startsWith("registration of ")) {
            cleanEntity = entity.substring(16);
          }
          return `What are the registration requirements for ${cleanEntity}?`;
        } else if (lowerQ.includes("timeline") || lowerQ.includes("deadline")) {
          return `What are the compliance timelines for ${entity}?`;
        } else {
          return `What are the requirements for ${entity}?`;
        }
      }
    }
    return query;
  };

  useEffect(() => {
    const pendingQuery = localStorage.getItem("pending_copilot_query");
    if (pendingQuery && docId) {
      localStorage.removeItem("pending_copilot_query");
      const simplified = simplifyGraphQuery(pendingQuery);
      safeSetInput("");
      sendQuery(simplified);
    }
  }, [docId]);

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
                className={`max-w-[85%] p-5 rounded-2xl whitespace-pre-wrap shadow-lg ${
                  msg.role === "user" 
                    ? "bg-gradient-to-br from-mint to-teal-500 text-black rounded-tr-sm" 
                    : "bg-white/5 border border-white/10 text-slate-200 rounded-tl-sm"
                }`}
              >
                {formatText(msg.content)}
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

          {loading && (
             <div className="flex flex-col items-start space-y-2">
                <div className="bg-white/5 border border-white/10 text-mint p-5 rounded-2xl rounded-tl-sm flex items-center gap-3">
                  {!isJetsonMode && (
                    <>
                      <style>{`
                        @keyframes pulse {
                          0%, 100% { opacity: 1; }
                          50% { opacity: 0.3; }
                        }
                        .pulse-dot {
                          animation: pulse 1.4s infinite both;
                        }
                        .pulse-dot:nth-child(2) {
                          animation-delay: 0.2s;
                        }
                        .pulse-dot:nth-child(3) {
                          animation-delay: 0.4s;
                        }
                      `}</style>
                      <div className="w-2 h-2 bg-mint rounded-full pulse-dot"></div>
                      <div className="w-2 h-2 bg-mint rounded-full pulse-dot"></div>
                      <div className="w-2 h-2 bg-mint rounded-full pulse-dot"></div>
                    </>
                  )}
                  <span className="ml-2 text-sm text-slate-300">
                    {thinkingMessages[thinkingIndex]} (Processing... {Math.floor(timerSeconds / 60)}:{(timerSeconds % 60).toString().padStart(2, '0')})
                  </span>
                </div>
             </div>
          )}
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