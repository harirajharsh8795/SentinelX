import { useState, useRef, useEffect } from "react";
import GlassCard from "../components/GlassCard.jsx";
import api from "../services/api.js";
import { useStore } from "../store/useStore.js";
import { Link } from "react-router-dom";

export default function Voice() {
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [aiResponse, setAiResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const docId = useStore((state) => state.selectedDocId);

  if (!docId) {
    return (
      <div className="flex flex-col items-center justify-center h-[80vh] text-center space-y-4 font-sans">
        <h2 className="text-2xl font-display text-white">No Document Active</h2>
        <p className="text-slate-400">Please upload a document to view voice copilot controls.</p>
        <Link to="/upload" className="px-6 py-2 bg-primary/20 text-primary border border-primary/30 rounded-full hover:bg-primary transition">
          Upload Document
        </Link>
      </div>
    );
  }

  const addLog = (msg) => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    setLogs(prev => [...prev, `[${time}] ${msg}`]);
  };

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
      setRecording(true);
      addLog("Microphone active. Capturing audio stream (English/Hindi)...");
    } catch (err) {
      console.error("Microphone access failed", err);
      alert("Microphone access is required to use voice features.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
      addLog("Audio capture ended. Preparing package.");
    }
  };

  const sendAudioToBackend = async (blob) => {
    setTranscribing(true);
    addLog("Transcribing offline audio via faster-whisper (CPU Optimized)...");
    const formData = new FormData();
    formData.append("file", blob, "voice_query.webm");
    
    try {
      const response = await api.post("/voice/transcribe", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      if (response.data && response.data.text) {
        const txt = response.data.text;
        setTranscript(txt);
        addLog(`✓ Audio transcribed: "${txt}"`);
        await sendQueryToChat(txt);
      } else {
        addLog("[WARN] Audio processed but returned empty transcript.");
      }
    } catch (err) {
      console.error("Failed to transcribe audio", err);
      addLog("[ERROR] Audio transcription failed. Check backend Whisper packages.");
    } finally {
      setTranscribing(false);
    }
  };

  const sendQueryToChat = async (queryText) => {
    if (!queryText.trim() || !docId) return;
    setLoading(true);
    setAiResponse("");
    addLog("Initiating semantic query rewriting and vector search...");

    try {
      // Query the API directly via HTTP POST for voice assistant
      const response = await api.post("/chat", {
        document_id: docId,
        message: queryText
      });
      
      if (response.data && response.data.reply) {
        setAiResponse(response.data.reply);
        addLog("✓ RAG response generated successfully. Outputting text.");
        if (response.data.grounded) {
          addLog(`✓ Grounding Score: ${(response.data.grounding_confidence * 100).toFixed(0)}% (Verified Grounded)`);
        } else {
          addLog("⚠️ Answer validation flagged potential hallucination risk.");
        }
      }
    } catch (err) {
      console.error("Failed to get RAG answer", err);
      addLog("[ERROR] Failed to retrieve response from AI engine.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 font-sans">
      <div className="flex justify-between items-end flex-wrap gap-4">
        <div>
          <h2 className="text-3xl font-display text-white mb-2">Bilingual Voice Copilot</h2>
          <p className="text-slate-400">
            Interact with regulatory guidelines using natural voice commands in English and Hindi.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-6">
        
        {/* CONTROL PANEL */}
        <div className="space-y-6">
          <GlassCard className="flex flex-col items-center justify-center p-8 min-h-[320px] text-center">
            {recording ? (
              <div className="flex flex-col items-center space-y-6 w-full">
                {/* Waveform Animation */}
                <div className="flex items-center gap-1.5 h-16 w-full justify-center">
                  {[...Array(8)].map((_, i) => (
                    <div 
                      key={i} 
                      className="w-1.5 bg-red-400 rounded-full animate-bounce"
                      style={{ 
                        height: '100%', 
                        animationDelay: `${i * 0.15}s`,
                        animationDuration: '0.8s'
                      }}
                    ></div>
                  ))}
                </div>
                <div>
                  <h4 className="text-red-400 font-bold uppercase tracking-widest text-xs animate-pulse">Capturing Audio...</h4>
                  <p className="text-slate-500 text-xs mt-1">Listening for Hindi/English input</p>
                </div>
                <button
                  onClick={stopRecording}
                  className="px-8 py-3 bg-red-500 hover:bg-red-600 text-white font-bold rounded-xl text-sm transition-all shadow-[0_0_20px_rgba(239,68,68,0.3)]"
                >
                  STOP RECORDING
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center space-y-6">
                <div 
                  onClick={startRecording}
                  className="w-24 h-24 rounded-full bg-primary/10 border-2 border-primary/30 hover:border-primary flex items-center justify-center cursor-pointer transition-all shadow-[0_0_30px_rgba(59,130,246,0.15)] group relative"
                >
                  <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  <span className="material-symbols-outlined text-[40px] text-primary">mic</span>
                </div>
                <div>
                  <h4 className="text-white font-bold uppercase tracking-widest text-xs">Press to Speak</h4>
                  <p className="text-slate-400 text-xs mt-1">Speak compliance queries naturally</p>
                </div>
              </div>
            )}
          </GlassCard>

          {/* TELEMETRY LOGGER */}
          <GlassCard className="flex flex-col h-[280px]">
             <div className="px-4 py-2.5 bg-surfaceAlt/80 border-b border-white/5 flex gap-1.5 items-center">
               <span className="w-2 h-2 rounded-full bg-success"></span>
               <span className="text-[10px] text-textSub font-mono tracking-widest uppercase">Voice Telemetry Log</span>
             </div>
             <div className="p-4 flex-1 bg-[#0A0D12] overflow-y-auto custom-scrollbar font-mono text-xs flex flex-col gap-2">
               {logs.length === 0 ? (
                  <div className="text-white/20 italic">Awaiting microphone signal...</div>
               ) : (
                 logs.map((L, i) => (
                   <span key={i} className={`${L.includes('[ERROR]') ? 'text-red-400' : L.includes('✓') ? 'text-success' : 'text-textSub'} break-words whitespace-pre-wrap`}>
                     {L}
                   </span>
                 ))
               )}
             </div>
          </GlassCard>
        </div>

        {/* TRANSCRIPT & RESPONSE */}
        <div className="space-y-6">
          <GlassCard className="p-6">
            <h3 className="text-lg font-display text-white mb-4">Live Transcription</h3>
            <div className="p-4 bg-surfaceAlt/40 border border-white/5 rounded-xl text-slate-200 min-h-[80px]">
              {transcribing ? (
                <div className="flex items-center gap-2 text-primary">
                  <span className="animate-spin text-lg">⏳</span> Transcribing offline audio...
                </div>
              ) : transcript ? (
                <p className="text-white font-medium">"{transcript}"</p>
              ) : (
                <span className="text-slate-500 italic text-sm">Transcription will appear here...</span>
              )}
            </div>
          </GlassCard>

          <GlassCard className="p-6 flex-1 min-h-[300px] flex flex-col">
            <h3 className="text-lg font-display text-white mb-4">AI Copilot Response</h3>
            <div className="flex-1 p-5 bg-surfaceAlt/20 border border-white/5 rounded-xl text-slate-200 overflow-y-auto custom-scrollbar whitespace-pre-wrap leading-relaxed">
              {loading ? (
                <div className="flex items-center gap-3 text-mint animate-pulse">
                  <div className="w-2 h-2 bg-mint rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-mint rounded-full animate-bounce delay-75"></div>
                  <div className="w-2 h-2 bg-mint rounded-full animate-bounce delay-150"></div>
                  <span className="text-slate-300 text-sm">Formulating regulatory response...</span>
                </div>
              ) : aiResponse ? (
                <p className="text-slate-200 text-sm">{aiResponse}</p>
              ) : (
                <span className="text-slate-500 italic text-sm">Awaiting query resolution...</span>
              )}
            </div>
          </GlassCard>
        </div>

      </div>
    </div>
  );
}
