import { useEffect, useState } from "react";
import GlassCard from "../components/GlassCard.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import api from "../services/api.js";
import { Link } from "react-router-dom";
import { useStore } from "../store/useStore.js";

export default function DocumentAnalysis() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const docId = useStore((state) => state.selectedDocId);

  const fetchAnalysis = (targetDocId, isRetry = false) => {
    setLoading(true);
    setError("");
    api
      .post("/analyze-document", null, { params: { doc_id: targetDocId } })
      .then((response) => {
        setAnalysis(response.data);
        setLoading(false);
      })
      .catch((err) => {
        if (!isRetry) {
          console.warn("Analysis failed, auto-retrying once...");
          fetchAnalysis(targetDocId, true);
        } else {
          setAnalysis(null);
          setError(err?.response?.data?.detail || "Analysis failed. Please retry.");
          setLoading(false);
        }
      });
  };

  useEffect(() => {
    if (!docId) {
      setAnalysis(null);
      setLoading(false);
      setError("");
      return;
    }

    fetchAnalysis(docId, false);
  }, [docId]);

  if (!docId) {
    return (
      <div className="flex flex-col items-center justify-center h-[80vh] text-center space-y-4">
        <h2 className="text-2xl font-display text-white">No Document Active</h2>
        <p className="text-slate-400">Please upload a document to view executive intelligence summary & insights.</p>
        <Link to="/upload" className="px-6 py-2 bg-primary/20 text-primary border border-primary/30 rounded-full hover:bg-primary transition">
          Upload Document
        </Link>
      </div>
    );
  }

  const maps = analysis?.maps || [];
  const risks = analysis?.risks || [];

  const getConfidence = (item) => {
    if (item.confidence !== undefined && item.confidence !== null) {
      return parseFloat(item.confidence).toFixed(2);
    }
    const key = (item.severity || "").toLowerCase();
    if (key.includes("high")) return "0.85";
    if (key.includes("medium")) return "0.70";
    if (key.includes("low")) return "0.55";
    return "0.60";
  };

  const confidenceBadgeColor = (score) => {
    const num = parseFloat(score);
    if (num >= 0.8) return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
    if (num >= 0.6) return "bg-blue-500/20 text-blue-300 border-blue-500/30";
    return "bg-amber-500/20 text-amber-300 border-amber-500/30";
  };

  let execIntel = null;
  if (analysis?.executive_insights) {
    try {
      execIntel = JSON.parse(analysis.executive_insights);
    } catch (e) {
      console.warn("Failed to parse executive insights as JSON", e);
    }
  }

  const renderExecutiveIntelligence = (intel) => {
    const summary = intel.executive_summary || {};
    const posture = intel.compliance_posture || {};
    const findings = intel.critical_findings || [];
    const obligations = intel.regulatory_obligations || [];
    const board = intel.board_responsibilities || [];
    const ops = intel.operational_responsibilities || [];
    const heatmap = intel.risk_heatmap || [];
    const roadmap = intel.remediation_roadmap || [];
    const score = intel.compliance_score || {};
    const recs = intel.strategic_recommendations || [];
    const citations = intel.source_citations || [];

    const getRatingColor = (rating) => {
      const r = (rating || "").toLowerCase();
      if (r.includes("critical") || r.includes("poor")) return "bg-red-950/30 border-red-500/25 text-red-400";
      if (r.includes("need") || r.includes("attention") || r.includes("action")) return "bg-amber-950/30 border-amber-500/25 text-amber-300";
      return "bg-emerald-950/30 border-emerald-500/25 text-emerald-400";
    };

    const getBadgeColor = (val) => {
      const v = (val || "").toLowerCase();
      if (v.includes("high") || v.includes("immediate") || v.includes("critical") || v.includes("p1")) return "bg-red-500/10 text-red-400 border border-red-500/20";
      if (v.includes("medium") || v.includes("strategic") || v.includes("needs") || v.includes("p2")) return "bg-warning/10 text-warning border border-warning/20";
      return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
    };

    const getCellBg = (l, imp) => {
      const sum = l + imp;
      if (sum >= 8) return "bg-red-950/30 border-red-500/20";
      if (sum >= 6) return "bg-amber-950/30 border-amber-500/20";
      if (sum >= 4) return "bg-yellow-950/10 border-yellow-500/15";
      return "bg-emerald-950/10 border-emerald-500/15";
    };

    const cells = [];
    for (let imp = 5; imp >= 1; imp--) {
      for (let l = 1; l <= 5; l++) {
        const cellRisks = heatmap.filter(r => Math.max(1, Math.min(5, r.likelihood)) === l && Math.max(1, Math.min(5, r.impact)) === imp);
        cells.push({ l, imp, cellRisks });
      }
    }

    return (
      <div className="space-y-8 font-sans">
        
        {/* 1. EXECUTIVE SUMMARY & KEY METRICS */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
          <div className="lg:col-span-2 bg-surfaceAlt/20 border border-white/5 p-6 rounded-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-white/5 pb-3">
              <h4 className="text-sm font-bold uppercase tracking-wider font-display text-white flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-lg">summarize</span>
                Strategic Brief & Overview
              </h4>
              <div className="flex gap-2">
                <span className="px-2.5 py-0.5 rounded text-[10px] font-semibold bg-primary/10 border border-primary/20 text-primary">
                  Regulator: {summary.regulator || "RBI"}
                </span>
                <span className="px-2.5 py-0.5 rounded text-[10px] font-semibold bg-white/5 border border-white/10 text-slate-300 font-mono">
                  Ref: {summary.circular_reference || "N/A"}
                </span>
              </div>
            </div>
            <div className="border-l-4 border-primary pl-4 py-2 italic text-slate-300 text-sm font-serif leading-relaxed">
              "{summary.overview}"
            </div>
          </div>

          <div className="bg-surfaceAlt/20 border border-white/5 p-6 rounded-2xl space-y-4">
            <h4 className="text-sm font-bold uppercase tracking-wider font-display text-white flex items-center gap-2 border-b border-white/5 pb-3">
              <span className="material-symbols-outlined text-mint text-lg">assessment</span>
              Key Performance Indicators
            </h4>
            <div className="grid grid-cols-1 gap-3">
              {(summary.key_metrics || [
                { metric: "Active Risks", value: String(risks.length), context: "Threat vectors" },
                { metric: "Directives", value: String(maps.length), context: "Assigned MAP items" },
                { metric: "Due Date", value: summary.effective_date || "90 Days", context: "Timeline" }
              ]).map((m, idx) => (
                <div key={idx} className="flex justify-between items-center p-2.5 bg-white/5 border border-white/5 rounded-xl">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block">{m.metric}</span>
                    <span className="text-[10px] text-slate-400 font-mono">{m.context}</span>
                  </div>
                  <span className="text-sm font-bold text-white font-mono bg-black/20 px-2 py-1 rounded border border-white/5">{m.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 2. COMPLIANCE POSTURE */}
        <div className={`p-6 border rounded-2xl space-y-4 animate-fadeIn ${getRatingColor(posture.rating)}`}>
          <div className="flex justify-between items-center border-b border-white/10 pb-3">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-xl">security</span>
              <h4 className="text-sm font-bold uppercase tracking-wider font-display">Compliance Posture Assessment</h4>
            </div>
            <div className="flex gap-2">
              <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider font-bold ${getBadgeColor(posture.rating)}`}>
                Rating: {posture.rating || "N/A"}
              </span>
              <span className="px-2 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider font-bold bg-white/10 text-white">
                Exposure: {posture.exposure_level || "Medium"}
              </span>
              <span className="px-2 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider font-bold bg-white/10 text-white">
                Governance: {posture.governance_health || "Needs Restructuring"}
              </span>
            </div>
          </div>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300">
            {(posture.assessment_bullets || []).map((bullet, idx) => (
              <li key={idx} className="flex gap-2 items-start bg-black/10 p-3 rounded-xl border border-white/5">
                <span className="text-primary font-bold text-base leading-none">▪</span>
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 3. CRITICAL FINDINGS */}
        <div className="bg-surfaceAlt/20 border border-white/5 rounded-2xl p-6 space-y-4 animate-fadeIn">
          <h4 className="text-base font-display text-white flex items-center gap-2 border-b border-white/5 pb-3">
            <span className="material-symbols-outlined text-red-400 text-lg">report_problem</span>
            Critical Regulatory Findings
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-slate-500 uppercase tracking-wider text-[9px] font-mono">
                  <th className="py-3 px-4 font-semibold w-1/4">Finding Context</th>
                  <th className="py-3 px-4 font-semibold w-1/3">Corporate Impact</th>
                  <th className="py-3 px-4 font-semibold w-1/3">Proposed Remediation Action</th>
                  <th className="py-3 px-4 font-semibold text-right">Severity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-300">
                {findings.map((item, idx) => (
                  <tr key={idx} className="hover:bg-white/[0.01] transition">
                    <td className="py-3 px-4 font-medium text-white leading-snug">{item.finding}</td>
                    <td className="py-3 px-4 leading-normal text-slate-400">{item.impact}</td>
                    <td className="py-3 px-4 leading-normal text-slate-400 italic">{item.reremediation || item.remediation || "Review controls"}</td>
                    <td className="py-3 px-4 text-right">
                      <span className={`px-2 py-0.5 rounded text-[8px] uppercase font-mono tracking-wider font-bold ${getBadgeColor(item.severity)}`}>
                        {item.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 4. REGULATORY OBLIGATIONS */}
        <div className="bg-surfaceAlt/20 border border-white/5 rounded-2xl p-6 space-y-4 animate-fadeIn">
          <h4 className="text-base font-display text-white flex items-center gap-2 border-b border-white/5 pb-3">
            <span className="material-symbols-outlined text-mint text-lg">fact_check</span>
            Regulatory Obligations Registry
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-slate-500 uppercase tracking-wider text-[9px] font-mono">
                  <th className="py-3 px-4 font-semibold w-2/5">Directive Obligation</th>
                  <th className="py-3 px-4 font-semibold">Owner</th>
                  <th className="py-3 px-4 font-semibold">Timeline</th>
                  <th className="py-3 px-4 font-semibold">Priority</th>
                  <th className="py-3 px-4 font-semibold text-right">Citation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-300">
                {obligations.map((item, idx) => (
                  <tr key={idx} className="hover:bg-white/[0.01] transition">
                    <td className="py-3 px-4 font-medium text-white leading-snug">{item.obligation}</td>
                    <td className="py-3 px-4 text-slate-400 font-mono">{item.department}</td>
                    <td className="py-3 px-4 font-medium">{item.deadline}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[8px] uppercase font-mono tracking-wider font-bold ${getBadgeColor(item.priority)}`}>
                        {item.priority}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-primaryGlow font-semibold font-mono">{item.source_section || "General"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 5. BOARD RESPONSIBILITIES TABLE */}
        <div className="bg-surfaceAlt/20 border border-white/5 rounded-2xl p-6 space-y-4 animate-fadeIn">
          <h4 className="text-base font-display text-white flex items-center gap-2 border-b border-white/5 pb-3">
            <span className="material-symbols-outlined text-warning text-lg">gavel</span>
            Board of Directors Responsibilities & Governance Oversight
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-slate-500 uppercase tracking-wider text-[9px] font-mono">
                  <th className="py-3 px-4 font-semibold w-1/2">Governance Action & Oversight Policy</th>
                  <th className="py-3 px-4 font-semibold">Oversight Focus</th>
                  <th className="py-3 px-4 font-semibold">Board Committee</th>
                  <th className="py-3 px-4 font-semibold text-right">Milestone</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-300">
                {board.map((item, idx) => {
                  const row = typeof item === 'object' ? item : {
                    responsibility: item,
                    focus: "Compliance Oversight",
                    committee: "Risk Committee",
                    milestone: "Quarterly Board Review"
                  };
                  return (
                    <tr key={idx} className="hover:bg-white/[0.01] transition">
                      <td className="py-3 px-4 font-medium text-white leading-snug">{row.responsibility}</td>
                      <td className="py-3 px-4 text-slate-400 font-mono text-[10px]">{row.focus}</td>
                      <td className="py-3 px-4 text-warning font-semibold text-[10px]">{row.committee}</td>
                      <td className="py-3 px-4 text-right font-medium text-[10px]">{row.milestone}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* 6. OPERATIONAL RESPONSIBILITIES TABLE */}
        <div className="bg-surfaceAlt/20 border border-white/5 rounded-2xl p-6 space-y-4 animate-fadeIn">
          <h4 className="text-base font-display text-white flex items-center gap-2 border-b border-white/5 pb-3">
            <span className="material-symbols-outlined text-mint text-lg">settings_suggest</span>
            Operational Execution & System Parameter Controls
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-slate-500 uppercase tracking-wider text-[9px] font-mono">
                  <th className="py-3 px-4 font-semibold w-1/2">Operational Ingestion & Action Item</th>
                  <th className="py-3 px-4 font-semibold">Target Department</th>
                  <th className="py-3 px-4 font-semibold">Deployment Parameters</th>
                  <th className="py-3 px-4 font-semibold text-right">Verification Protocol</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-300">
                {ops.map((item, idx) => {
                  const row = typeof item === 'object' ? item : {
                    action: item,
                    department: "Operations",
                    parameter: "Process integration & validation",
                    verification: "System testing & audit trails sign-off"
                  };
                  return (
                    <tr key={idx} className="hover:bg-white/[0.01] transition">
                      <td className="py-3 px-4 font-medium text-white leading-snug">{row.action}</td>
                      <td className="py-3 px-4 text-mint font-semibold text-[10px]">{row.department}</td>
                      <td className="py-3 px-4 text-slate-400 text-[10px]">{row.parameter}</td>
                      <td className="py-3 px-4 text-right font-medium text-[10px]">{row.verification}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* 7. RISK HEATMAP (Palantir Foundry Matrix) */}
        <div className="bg-surfaceAlt/20 border border-white/5 rounded-2xl p-6 space-y-4 animate-fadeIn">
          <h4 className="text-base font-display text-white flex items-center gap-2 border-b border-white/5 pb-3">
            <span className="material-symbols-outlined text-orange-400 text-lg">grid_on</span>
            Systemic Threat Heatmap (Palantir Foundry Matrix)
          </h4>
          
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-6 flex flex-col items-center">
              <div className="flex gap-4 items-center">
                <div className="text-[9px] text-slate-500 uppercase tracking-widest font-mono -rotate-90 origin-center whitespace-nowrap py-4 shrink-0">
                  Impact (1-5)
                </div>
                
                <div className="space-y-1">
                  <div className="flex gap-2">
                    <div className="flex flex-col justify-between text-[10px] font-mono text-slate-500 py-1 font-bold shrink-0">
                      <span>5</span>
                      <span>4</span>
                      <span>3</span>
                      <span>2</span>
                      <span>1</span>
                    </div>
                    
                    <div className="grid grid-cols-5 gap-1.5 w-64 h-64 border-l border-b border-white/20 p-1 bg-black/30 rounded-lg">
                      {cells.map((cell, idx) => (
                        <div 
                          key={idx} 
                          className={`relative border rounded flex flex-wrap gap-1 items-center justify-center p-0.5 ${getCellBg(cell.l, cell.imp)}`}
                          title={`L:${cell.l}, I:${cell.imp}`}
                        >
                          {cell.cellRisks.map((item, cellRiskIdx) => {
                            const rIndex = heatmap.indexOf(item) + 1;
                            return (
                              <span 
                                key={cellRiskIdx} 
                                className="w-4.5 h-4.5 rounded-full flex items-center justify-center text-[8px] font-bold text-white bg-primary shadow-lg border border-white/30 cursor-pointer transform hover:scale-125 transition"
                                title={`${item.risk}`}
                              >
                                {rIndex}
                              </span>
                            );
                          })}
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="flex gap-2 pl-4">
                    <div className="grid grid-cols-5 gap-1.5 w-64 text-[10px] font-mono text-slate-500 text-center font-bold">
                      <span>1</span>
                      <span>2</span>
                      <span>3</span>
                      <span>4</span>
                      <span>5</span>
                    </div>
                  </div>
                  
                  <div className="text-[9px] text-slate-500 uppercase tracking-widest font-mono text-center pt-2">
                    Likelihood (1-5)
                  </div>
                </div>
              </div>
            </div>
            
            <div className="lg:col-span-6 flex flex-col justify-center">
              <div className="space-y-2 max-h-[260px] overflow-y-auto pr-2">
                {heatmap.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center p-2.5 bg-white/5 border border-white/5 rounded-xl text-xs">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="w-5 h-5 shrink-0 rounded-full flex items-center justify-center text-[10px] font-bold text-white bg-primary border border-white/10">
                        {idx + 1}
                      </span>
                      <span className="text-slate-300 font-medium truncate leading-tight">{item.risk}</span>
                    </div>
                    <div className="flex gap-2 items-center shrink-0 ml-4 font-mono text-[10px]">
                      <span className="text-slate-500">L:{item.likelihood}</span>
                      <span className="text-slate-500">I:{item.impact}</span>
                      <span className="px-1.5 py-0.5 rounded bg-white/5 text-slate-400 text-[8px]">
                        {item.category || "General"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 8. REMEDIATION ROADMAP */}
        <div className="bg-surfaceAlt/20 border border-white/5 rounded-2xl p-6 space-y-6 animate-fadeIn">
          <h4 className="text-base font-display text-white flex items-center gap-2 border-b border-white/5 pb-3">
            <span className="material-symbols-outlined text-primaryGlow text-lg font-bold">timeline</span>
            Strategic Remediation Roadmap
          </h4>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative">
            {roadmap.map((phase, idx) => (
              <div key={idx} className="relative bg-white/[0.02] border border-white/5 p-5 rounded-2xl space-y-3">
                <div className="flex justify-between items-center border-b border-white/5 pb-2">
                  <span className="text-xs font-bold text-primaryGlow uppercase tracking-wider block font-mono">
                    {phase.phase}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[8px] font-semibold bg-primary/20 border border-primary/30 text-primary uppercase font-mono">
                    Phase {idx + 1}
                  </span>
                </div>
                <div className="space-y-2.5">
                  {(phase.actions || []).map((actionObj, actionIdx) => {
                    const act = typeof actionObj === 'object' ? actionObj : {
                      action: actionObj,
                      owner: "Compliance",
                      priority: "Medium"
                    };
                    return (
                      <div key={actionIdx} className="p-3 bg-black/20 border border-white/5 rounded-xl space-y-1.5">
                        <p className="text-xs text-slate-200 leading-snug font-medium">{act.action}</p>
                        <div className="flex justify-between items-center text-[10px]">
                          <span className="text-slate-500 font-mono">Owner: <span className="text-mint font-semibold">{act.owner}</span></span>
                          <span className={`px-1.5 py-0.2 rounded text-[7px] uppercase font-mono tracking-wider font-bold ${getBadgeColor(act.priority)}`}>
                            {act.priority}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 9. COMPLIANCE SCORE & DEDUCTIONS CARD */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
          <div className="bg-surfaceAlt/20 border border-white/5 p-6 rounded-2xl flex flex-col justify-between items-center text-center space-y-4">
            <div className="space-y-1 w-full">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block font-mono">Corporate Compliance Index</span>
              <span className="text-[9px] text-slate-500 font-mono block">SentinelX Internal Assessment Rating</span>
            </div>
            
            <div className="relative inline-flex items-center justify-center">
              <svg className="w-36 h-36 transform -rotate-90">
                <circle
                  cx="72"
                  cy="72"
                  r="60"
                  className="stroke-white/5"
                  strokeWidth="10"
                  fill="transparent"
                />
                <circle
                  cx="72"
                  cy="72"
                  r="60"
                  className={(score.score || 100) >= 80 ? "stroke-emerald-500" : (score.score || 100) >= 50 ? "stroke-warning" : "stroke-red-500"}
                  strokeWidth="10"
                  fill="transparent"
                  strokeDasharray={2 * Math.PI * 60}
                  strokeDashoffset={2 * Math.PI * 60 * (1 - (score.score || 100) / 100)}
                  strokeLinecap="round"
                  style={{ transition: "stroke-dashoffset 1s ease" }}
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className={`text-3xl font-display font-bold ${
                  (score.score || 100) >= 80 ? "text-emerald-400" :
                  (score.score || 100) >= 50 ? "text-warning" :
                  "text-red-400"
                }`}>
                  {score.score}%
                </span>
                <span className="text-[8px] text-slate-400 uppercase tracking-widest font-mono font-bold mt-1">
                  {(score.score || 100) >= 80 ? "Resilient" : (score.score || 100) >= 50 ? "Needs Review" : "Deficient"}
                </span>
              </div>
            </div>
            
            <div className="text-[11px] text-slate-400 leading-normal border-t border-white/5 pt-3 w-full">
              <strong className="text-white block mb-1 uppercase tracking-wider text-[9px] font-mono">Score Rationale</strong>
              {score.rationale}
            </div>
          </div>

          <div className="lg:col-span-2 bg-surfaceAlt/20 border border-white/5 p-6 rounded-2xl space-y-4">
            <h4 className="text-sm font-bold uppercase tracking-wider font-display text-white flex items-center gap-2 border-b border-white/5 pb-3">
              <span className="material-symbols-outlined text-red-400 text-lg">money_off</span>
              Deductions Scorecard Breakdown
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/10 text-slate-500 uppercase tracking-wider text-[9px] font-mono">
                    <th className="py-2 px-2 font-semibold">Identified Vulnerability</th>
                    <th className="py-2 px-2 font-semibold text-right">Deduction Points</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-300">
                  {(score.deductions || []).length > 0 ? (
                    (score.deductions || []).map((d, idx) => (
                      <tr key={idx} className="hover:bg-white/[0.01]">
                        <td className="py-2.5 px-2 text-slate-300 leading-snug">{d.finding}</td>
                        <td className="py-2.5 px-2 text-right">
                          <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-red-500/10 text-red-400 border border-red-500/20">
                            -{d.points} pts
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td className="py-3 px-2 text-slate-400 italic">No deductions applied. Base compliance standard met.</td>
                      <td className="py-3 px-2 text-right">
                        <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          -0 pts
                        </span>
                      </td>
                    </tr>
                  )}
                  <tr className="font-bold border-t-2 border-white/10 text-white bg-white/[0.02]">
                    <td className="py-3 px-2 uppercase text-[9px] tracking-wider font-mono">Final Corporate Index Score</td>
                    <td className="py-3 px-2 text-right font-mono">{score.score || 100}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* 10. STRATEGIC RECOMMENDATIONS */}
        <div className="bg-surfaceAlt/20 border border-white/5 rounded-2xl p-6 space-y-4 animate-fadeIn">
          <h4 className="text-base font-display text-white flex items-center gap-2 border-b border-white/5 pb-3">
            <span className="material-symbols-outlined text-warning text-lg">lightbulb</span>
            Strategic Compliance Recommendations
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recs.map((item, idx) => (
              <div key={idx} className="p-4 bg-white/5 border border-white/5 rounded-xl space-y-3 flex flex-col justify-between">
                <div className="space-y-1">
                  <div className="flex justify-between items-start gap-4">
                    <span className={`px-2 py-0.5 rounded text-[7px] uppercase font-mono tracking-widest font-bold ${getBadgeColor(item.priority_label)}`}>
                      {item.priority_label}
                    </span>
                    <div className="flex gap-1.5 shrink-0">
                      <span className="px-1.5 py-0.5 rounded text-[8px] bg-white/10 text-slate-300 font-mono">
                        Diff: {item.difficulty || "Medium"}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[8px] bg-white/10 text-slate-300 font-mono">
                        Payoff: {item.payoff || "High"}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs font-semibold text-white leading-relaxed pt-1.5">{item.recommendation}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 11. SOURCE CITATIONS */}
        <div className="bg-surfaceAlt/20 border border-white/5 rounded-2xl p-6 space-y-4 animate-fadeIn">
          <h4 className="text-base font-display text-white flex items-center gap-2 border-b border-white/5 pb-3">
            <span className="material-symbols-outlined text-mint text-lg">library_books</span>
            Grounded Regulatory Source Citations
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {citations.map((item, idx) => (
              <div key={idx} className="p-4 bg-black/20 rounded-xl space-y-2 border-l-4 border-mint flex flex-col justify-between">
                <p className="text-[10px] italic text-slate-300 font-mono leading-relaxed">
                  "{item.text}"
                </p>
                <div className="flex justify-between items-center text-[9px] text-slate-500 font-mono border-t border-white/5 pt-2 mt-2">
                  <span>Citation Clause: <span className="text-mint font-semibold">{item.citation}</span></span>
                  <span className="px-2 py-0.5 bg-white/5 rounded">Relevance: {item.relevance || "High"}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    );
  };

  return (
    <div className="grid gap-8">
      {execIntel ? (
        <GlassCard>
          <div className="flex justify-between items-center border-b border-white/5 pb-4 mb-6">
            <h3 className="text-xl font-display text-white">Executive Compliance & Risk Brief</h3>
            <span className="px-3 py-1 bg-primary/10 border border-primary/20 text-primary text-xs rounded-full uppercase tracking-wider font-semibold">
              Deloitte & McKinsey Compliant
            </span>
          </div>
          {renderExecutiveIntelligence(execIntel)}
        </GlassCard>
      ) : (
        <>
          <GlassCard>
            <h3 className="text-xl font-display text-white">Executive Intelligence Summary</h3>
            {loading ? (
              <div className="mt-3 space-y-4">
                <div className="text-sm text-mint animate-pulse font-medium">
                  AI processing on Jetson hardware...
                </div>
                <LoadingSkeleton />
              </div>
            ) : error ? (
              <div className="mt-4 space-y-4">
                <p className="text-gold text-base">{error}</p>
                <button
                  onClick={() => fetchAnalysis(docId, false)}
                  className="px-4 py-2 bg-primary/20 text-primary border border-primary/30 rounded-full hover:bg-primary transition text-sm font-medium"
                >
                  Retry Analysis
                </button>
              </div>
            ) : (
              <p className="mt-4 text-base text-slate-200/80 whitespace-pre-wrap leading-relaxed font-sans">
                {analysis?.summary || "Summary unavailable"}
              </p>
            )}
          </GlassCard>

          <GlassCard>
            <h3 className="text-xl font-display text-white">Strategic Compliance Insights</h3>
            {loading ? (
              <div className="mt-3 space-y-4">
                <div className="text-sm text-mint animate-pulse font-medium">
                  AI processing on Jetson hardware...
                </div>
                <LoadingSkeleton />
              </div>
            ) : (
              <p className="mt-4 text-base text-slate-200/80 whitespace-pre-wrap leading-relaxed font-sans">
                {analysis?.executive_insights || "Strategic insights will appear after analysis."}
              </p>
            )}
          </GlassCard>

          <div className="grid gap-8 xl:grid-cols-2">
            <GlassCard>
              <h3 className="text-xl font-display">Extracted MAPs</h3>
              <div className="mt-6 space-y-4">
                {maps.length ? (
                  maps.map((item) => (
                    <div key={item.title} className="rounded-2xl bg-white/5 p-5">
                      <p className="text-base font-medium">{item.title}</p>
                      <p className="text-sm text-slate-200/60">
                        {item.department} • {item.deadline} • {item.severity}
                      </p>
                      <p className="text-sm text-mint">
                        Source: {item.source || item.source_section}
                      </p>
                      <div className="mt-2">
                        <span className={`inline-block rounded-md px-2.5 py-1 text-xs font-semibold shadow-sm border ${confidenceBadgeColor(getConfidence(item))}`}>
                          Confidence: {getConfidence(item)}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-white/10 px-5 py-6 text-sm text-slate-200/60">
                    No MAPs generated yet
                  </div>
                )}
              </div>
            </GlassCard>

            <GlassCard>
              <h3 className="text-xl font-display">Risk Analysis</h3>
              <div className="mt-6 space-y-4">
                {risks.length ? (
                  risks.map((item) => (
                    <div key={item.risk} className="rounded-2xl bg-white/5 p-5">
                      <p className="text-base font-medium">{item.risk}</p>
                      <p className="text-sm text-slate-200/60">{item.reason}</p>
                      <p className="text-sm text-gold">
                        {item.severity} • {item.source || item.source_section}
                      </p>
                      <div className="mt-2">
                        <span className={`inline-block rounded-md px-2.5 py-1 text-xs font-semibold shadow-sm border ${confidenceBadgeColor(getConfidence(item))}`}>
                          Confidence: {getConfidence(item)}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-white/10 px-5 py-6 text-sm text-slate-200/60">
                    No risks generated yet
                  </div>
                )}
              </div>
            </GlassCard>
          </div>

          <GlassCard>
            <h3 className="text-xl font-display">Why AI flagged this</h3>
            {loading ? (
              <div className="mt-3">
                <LoadingSkeleton />
              </div>
            ) : analysis?.agent_reasoning?.length ? (
              <div className="mt-6 space-y-3">
                {analysis.agent_reasoning.map((item, index) => (
                  <div key={`${item}-${index}`} className="rounded-2xl bg-white/5 p-4 text-sm">
                    {item}
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-base text-slate-200/70">
                AI reasoning will appear after analysis completes.
              </p>
            )}
          </GlassCard>

          <GlassCard>
            <h3 className="text-xl font-display">Source Citations (RAG Retrieval)</h3>
            {loading ? (
              <div className="mt-3">
                <LoadingSkeleton />
              </div>
            ) : analysis?.sources?.length ? (
              <div className="mt-6 space-y-4">
                {analysis.sources.map((item, index) => (
                  <div key={`${item.section_title}-${index}`} className="rounded-2xl bg-white/5 p-5 border-l-4 border-mint">
                    <p className="text-base font-semibold text-mint">{item.section_title}</p>
                    <p className="text-sm font-mono mt-2 text-slate-200/80 bg-black/20 p-3 rounded">
                      "{item.snippet}"
                    </p>
                    <div className="mt-3 flex justify-between items-center text-xs text-slate-200/50">
                      <span>Semantic Relevance Score: {item.score ? item.score.toFixed(3) : "0.500"}</span>
                      <span className="px-2 py-1 bg-white/10 rounded-full">Cited Source</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-base text-slate-200/70">
                No source citations available for this document.
              </p>
            )}
          </GlassCard>
        </>
      )}
    </div>
  );
}
