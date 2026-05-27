import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import GlassCard from "../components/GlassCard.jsx";
import api from "../services/api.js";
import { useStore } from "../store/useStore.js";

export default function Risk() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const docId = useStore((state) => state.selectedDocId);

  useEffect(() => {
    if (!docId) {
      setAnalysis(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    const stored = localStorage.getItem(`analysis_${docId}`);
    if (stored) {
      setAnalysis(JSON.parse(stored));
      setLoading(false);
    } else {
      api
        .post("/analyze-document", null, { params: { doc_id: docId } })
        .then((res) => {
          setAnalysis(res.data);
          localStorage.setItem(`analysis_${docId}`, JSON.stringify(res.data));
        })
        .catch((err) => console.error(err))
        .finally(() => setLoading(false));
    }
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
        <GlassCard className="border-red-500/20">
          <p className="text-xs text-textSub uppercase tracking-wider mb-1">Exposure Index</p>
          <h3 className="text-4xl font-display font-bold text-red-400">{riskScore}%</h3>
          <p className="text-[10px] text-slate-500 mt-2">Calculated from total compliance anomalies</p>
        </GlassCard>
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

        {/* RISK MATRIX & HEATMAP */}
        <div className="space-y-6">
          <GlassCard className="h-fit">
            <h3 className="text-lg font-display text-white mb-4">Risk Heat Matrix</h3>
            
            {/* Grid 3x3 Likelihood vs Impact */}
            <div className="grid grid-cols-4 gap-2 text-center text-[10px] font-mono mb-4">
              {/* Labels & Grid */}
              <span className="text-slate-500 flex items-center justify-center">Likelihood</span>
              <span className="bg-red-500/20 text-red-300 border border-red-500/30 p-4 rounded flex flex-col justify-center font-bold">
                High
                <span className="text-[14px] mt-1">{highRisks.length}</span>
              </span>
              <span className="bg-warning/20 text-warning border border-warning/30 p-4 rounded flex flex-col justify-center font-bold">
                Med
                <span className="text-[14px] mt-1">{medRisks.length}</span>
              </span>
              <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 p-4 rounded flex flex-col justify-center font-bold">
                Low
                <span className="text-[14px] mt-1">{lowRisks.length}</span>
              </span>
              
              {/* Side headers */}
              <span className="text-slate-500 flex items-center justify-center">Impact</span>
              <span className="text-slate-400 py-1 bg-surfaceAlt border border-white/5 rounded">Severe</span>
              <span className="text-slate-400 py-1 bg-surfaceAlt border border-white/5 rounded">Moderate</span>
              <span className="text-slate-400 py-1 bg-surfaceAlt border border-white/5 rounded">Minor</span>
            </div>
            
            <p className="text-xs text-textSub leading-relaxed">
              This matrix correlates the severity of identified policy deviations with their likelihood of regulatory infraction. High-severity threats require immediate execution updates on the Kanban boards.
            </p>
          </GlassCard>

          <GlassCard className="h-fit">
            <h3 className="text-lg font-display text-white mb-3">Governance Directives</h3>
            <div className="space-y-3 text-xs leading-relaxed text-slate-300">
              <div className="flex gap-2.5">
                <span className="text-orange-400">⚡</span>
                <p>Ensure that IT Security teams review the firewall access rules outlined in cybersecurity controls.</p>
              </div>
              <div className="flex gap-2.5">
                <span className="text-orange-400">⚡</span>
                <p>Legal officers must confirm the compliance penalties with FIU-IND timelines.</p>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
