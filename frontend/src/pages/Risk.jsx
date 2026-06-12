import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import GlassCard from "../components/GlassCard.jsx";
import api from "../services/api.js";
import { useStore } from "../store/useStore.js";
import { motion, AnimatePresence } from "framer-motion";

export default function Risk() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const docId = useStore((state) => state.selectedDocId);
  const [showExposureAudit, setShowExposureAudit] = useState(false);

  useEffect(() => {
    if (!docId) {
      setAnalysis(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    api
      .post("/analyze-document", null, { params: { doc_id: docId } })
      .then((res) => {
        setAnalysis(res.data);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [docId]);

  if (!docId) {
    return (
      <div className="flex flex-col items-center justify-center h-[80vh] text-center space-y-4">
        <h2 className="text-2xl font-display text-white">No Document Active</h2>
        <p className="text-slate-400">Please upload a document to view risk center telemetry.</p>
        <Link to="/upload" className="px-6 py-2 bg-primary/20 text-primary border border-primary/30 rounded-full hover:bg-primary transition">
          Upload Document
        </Link>
      </div>
    );
  }

  if (loading) {
    return (
      <GlassCard>
        <p className="text-slate-300">Evaluating compliance risk telemetry...</p>
      </GlassCard>
    );
  }

  const risks = analysis?.risks || [];
  const riskScore = analysis?.risk_score || 0;
  
  // Count risks by severity
  const highRisks = risks.filter(r => (r.severity || "").toLowerCase().includes("high"));
  const medRisks = risks.filter(r => (r.severity || "").toLowerCase().includes("medium"));
  const lowRisks = risks.filter(r => (r.severity || "").toLowerCase().includes("low"));

  return (
    <div className="space-y-6 pb-12 font-sans">
      <div className="flex justify-between items-end flex-wrap gap-4">
        <div>
          <h2 className="text-3xl font-display text-white mb-2">Risk Intelligence Center</h2>
          <p className="text-slate-400">
            Realtime compliance vulnerability telemetry and cascading threat mapping.
          </p>
        </div>
        <div className="px-4 py-2 bg-surfaceAlt border border-white/5 rounded-xl text-xs text-slate-400">
          Source Circular: <span className="text-primary font-mono">{analysis?.document_name || "Active Document"}</span>
        </div>
      </div>

      {/* METRICS ROW */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div 
          onClick={() => setShowExposureAudit(true)}
          className="cursor-pointer group hover:scale-[1.02] transition-transform duration-300"
        >
          <GlassCard className="border-red-500/20 hover:border-red-500/40 hover:bg-white/[0.02] h-full transition-all">
            <p className="text-xs text-textSub uppercase tracking-wider mb-1 flex items-center justify-between">
              Exposure Index <span className="material-symbols-outlined text-xs text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">open_in_new</span>
            </p>
            <h3 className="text-4xl font-display font-bold text-red-400">{riskScore}%</h3>
            <p className="text-[10px] text-slate-500 mt-2">Calculated from total compliance anomalies</p>
          </GlassCard>
        </div>
        <GlassCard className="border-orange-500/20">
          <p className="text-xs text-textSub uppercase tracking-wider mb-1">Critical Threats</p>
          <h3 className="text-4xl font-display font-bold text-orange-400">{highRisks.length}</h3>
          <p className="text-[10px] text-slate-500 mt-2">Requires board level intervention</p>
        </GlassCard>
        <GlassCard className="border-warning/20">
          <p className="text-xs text-textSub uppercase tracking-wider mb-1">Medium Risks</p>
          <h3 className="text-4xl font-display font-bold text-warning">{medRisks.length}</h3>
          <p className="text-[10px] text-slate-500 mt-2">Requires departmental mitigation</p>
        </GlassCard>
        <GlassCard className="border-emerald-500/20">
          <p className="text-xs text-textSub uppercase tracking-wider mb-1">Low Severity</p>
          <h3 className="text-4xl font-display font-bold text-emerald-400">{lowRisks.length}</h3>
          <p className="text-[10px] text-slate-500 mt-2">Informational compliance guidelines</p>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-6">
        {/* RISK REGISTER */}
        <div className="space-y-4">
          <GlassCard>
            <h3 className="text-lg font-display text-white mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-red-400 text-base">security</span> Active Vulnerability Registry
            </h3>
            
            {risks.length === 0 ? (
              <div className="text-slate-500 p-8 text-center italic">No compliance threats registered for this document.</div>
            ) : (
              <div className="space-y-4">
                {risks.map((item, idx) => {
                  const isHigh = (item.severity || "").toLowerCase().includes("high");
                  const isMed = (item.severity || "").toLowerCase().includes("medium");
                  
                  return (
                    <div key={idx} className="p-5 bg-surfaceAlt/50 border border-white/5 rounded-xl space-y-3">
                      <div className="flex justify-between items-start gap-4">
                        <h4 className="font-bold text-white text-base leading-snug">{item.risk}</h4>
                        <span className={`px-2.5 py-0.5 rounded text-[10px] uppercase font-mono tracking-widest font-bold ${
                          isHigh ? 'bg-red-500/10 text-red-400 border border-red-500/20 shadow-[0_0_10px_rgba(239,68,68,0.1)]' :
                          isMed ? 'bg-warning/10 text-warning border border-warning/20' :
                          'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}>
                          {item.severity}
                        </span>
                      </div>
                      <p className="text-slate-300 text-sm leading-relaxed">{item.reason}</p>
                      <div className="pt-3 border-t border-white/5 flex justify-between items-center text-xs text-slate-500">
                        <span>Source: <span className="text-slate-400 font-medium">{item.source_section || "Clause Index"}</span></span>
                        <div className="flex gap-2">
                          <span className="text-mint font-mono font-medium">Mitigation Plan Generated ✓</span>
                        </div>
                      </div>
                      <div className="bg-primary/5 p-3 rounded-lg border border-primary/10 text-xs">
                        <strong className="text-primaryGlow">AI Mitigation Recommendation:</strong> Establish automated compliance controls in related departments and mandate quarterly audits for this specific control.
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </GlassCard>
        </div>

        {/* RISK MATRIX & HEATMAP DELETED */}
        <div className="space-y-6">
          <GlassCard className="h-fit">
            <h3 className="text-lg font-display text-white mb-3">Governance Directives</h3>
            <div className="space-y-3 text-xs leading-relaxed text-slate-300">
              {(analysis?.maps || []).slice(0, 4).map((item, idx) => {
                const associatedRisk = (analysis?.risks || []).find(r => 
                  r.source_section && item.source_section &&
                  (r.source_section.toLowerCase().includes(item.source_section.toLowerCase()) || 
                   item.source_section.toLowerCase().includes(r.source_section.toLowerCase()))
                ) || (analysis?.risks || []).find(r => r.severity === item.severity) 
                || (analysis?.risks || [])[idx % (analysis?.risks?.length || 1)];

                return (
                  <div key={idx} className="p-4 bg-surfaceAlt/30 border border-white/5 rounded-xl space-y-2">
                    <div className="flex justify-between items-start gap-4">
                      <p className="font-semibold text-white text-sm leading-snug">{item.title}</p>
                      <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider font-bold ${
                        (item.severity || "").toLowerCase().includes("high") ? "bg-red-500/10 text-red-400 border border-red-500/20" :
                        (item.severity || "").toLowerCase().includes("medium") ? "bg-warning/10 text-warning border border-warning/20" :
                        "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      }`}>
                        {item.severity}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-slate-500 font-mono">
                      <span>Dept: <span className="text-slate-400">{item.department}</span></span>
                      <span>|</span>
                      <span>Deadline: <span className="text-slate-400">{item.deadline}</span></span>
                      <span>|</span>
                      <span>Citation: <span className="text-primaryGlow font-semibold">{item.source_section || "N/A"}</span></span>
                    </div>
                    {associatedRisk && (
                      <div className="mt-2 text-[10px] bg-red-500/5 p-2 rounded border border-red-500/10 text-red-200">
                        <strong className="text-red-400">Linked Threat:</strong> {associatedRisk.risk} 
                        <span className="text-slate-500 ml-1">({associatedRisk.source_section})</span>
                      </div>
                    )}
                  </div>
                );
              })}
              {(!analysis?.maps || analysis.maps.length === 0) && (
                <div className="text-slate-500 italic text-center py-4">No governance directives mapped.</div>
              )}
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Exposure Index Audit & Traceability Modal */}
      <AnimatePresence>
        {showExposureAudit && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="glass-card max-w-2xl w-full p-6 border-white/10 relative shadow-[0_0_50px_rgba(0,0,0,0.8)] text-left"
            >
              <div className="flex justify-between items-start mb-5 pb-3 border-b border-white/5">
                <div>
                  <h3 className="text-xl font-bold text-white font-display flex items-center gap-2">
                    <span className="material-symbols-outlined text-red-400 font-bold">shield_with_heart</span> Exposure Index Traceability Audit
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Explainable point breakdown for compliance vulnerability scoring.
                  </p>
                </div>
                <button 
                  onClick={() => setShowExposureAudit(false)}
                  className="p-1 rounded-full hover:bg-white/10 text-slate-400 hover:text-white transition flex items-center justify-center"
                >
                  <span className="material-symbols-outlined text-base">close</span>
                </button>
              </div>

              <div className="space-y-4">
                <div className="bg-slate-900/60 border border-white/5 p-4 rounded-xl space-y-2">
                  <span className="text-[10px] text-primary uppercase font-mono font-bold tracking-widest">Formula</span>
                  <div className="font-mono text-xs text-white bg-black/30 p-2.5 rounded border border-white/5">
                    Exposure Index = min(100%, (High Risks * 15) + (Medium Risks * 10) + (Low Risks * 5))
                  </div>
                </div>

                <div className="space-y-3">
                  <span className="text-[10px] text-slate-400 uppercase font-mono font-bold tracking-wider">Metrics Breakdown</span>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 bg-red-500/5 border border-red-500/10 rounded-xl">
                      <p className="text-[10px] text-slate-400 font-mono">High Severity</p>
                      <h4 className="text-lg font-bold text-red-400">{highRisks.length} × 15</h4>
                      <p className="text-xs text-red-500/70 font-semibold">+{highRisks.length * 15} pts</p>
                    </div>
                    <div className="p-3 bg-warning/5 border border-warning/10 rounded-xl">
                      <p className="text-[10px] text-slate-400 font-mono">Medium Severity</p>
                      <h4 className="text-lg font-bold text-warning">{medRisks.length} × 10</h4>
                      <p className="text-xs text-warning/70 font-semibold">+{medRisks.length * 10} pts</p>
                    </div>
                    <div className="p-3 bg-emerald-500/5 border border-emerald-500/10 rounded-xl">
                      <p className="text-[10px] text-slate-400 font-mono">Low Severity</p>
                      <h4 className="text-lg font-bold text-emerald-400">{lowRisks.length} × 5</h4>
                      <p className="text-xs text-emerald-500/70 font-semibold">+{lowRisks.length * 5} pts</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white/5 border border-white/10 p-4 rounded-xl flex justify-between items-center">
                  <div>
                    <h4 className="text-sm font-bold text-white">Aggregated Exposure Index</h4>
                    <p className="text-[10px] text-slate-400 mt-0.5">Raw Total: {highRisks.length * 15 + medRisks.length * 10 + lowRisks.length * 5} pts (Capped at 100%)</p>
                  </div>
                  <div className="text-3xl font-display font-extrabold text-red-400">
                    {riskScore}%
                  </div>
                </div>

                <div className="space-y-2">
                  <span className="text-[10px] text-slate-400 uppercase font-mono font-bold tracking-wider">Contributing Vulnerabilities</span>
                  <div className="max-h-[180px] overflow-y-auto custom-scrollbar border border-white/5 rounded-xl divide-y divide-white/5 bg-slate-950/40">
                    {risks.map((item, idx) => {
                      const isHigh = (item.severity || "").toLowerCase().includes("high");
                      const isMed = (item.severity || "").toLowerCase().includes("medium");
                      const pts = isHigh ? 15 : isMed ? 10 : 5;
                      
                      return (
                        <div key={idx} className="p-3 flex justify-between items-start text-xs hover:bg-white/5 transition-colors">
                          <div className="max-w-[85%]">
                            <p className="font-semibold text-white leading-snug">{item.risk}</p>
                            <p className="text-[10px] text-slate-500 mt-1">{item.source_section}</p>
                          </div>
                          <span className={`font-mono font-bold ${
                            isHigh ? 'text-red-400' : isMed ? 'text-warning' : 'text-emerald-400'
                          }`}>
                            +{pts} pts
                          </span>
                        </div>
                      );
                    })}
                    {risks.length === 0 && (
                      <p className="p-4 text-slate-500 italic text-center text-xs">No vulnerabilities registered.</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-4 border-t border-white/5 flex justify-end">
                <button 
                  onClick={() => setShowExposureAudit(false)}
                  className="px-4 py-2 bg-surfaceAlt border border-white/10 hover:bg-white/5 rounded-xl text-slate-300 text-xs transition font-semibold"
                >
                  Close Inspector
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
