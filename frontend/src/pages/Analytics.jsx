import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar
} from "recharts";
import GlassCard from "../components/GlassCard.jsx";
import api from "../services/api.js";
import { useStore } from "../store/useStore.js";

// Phase 13: Advanced Analytics & Predictive Modeling
export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const selectedDocId = useStore((state) => state.selectedDocId);
  const [drillDownData, setDrillDownData] = useState(null);

  const handleCardClick = (type) => {
    if (!data) return;
    if (type === "completion_rate") {
      setDrillDownData({
        title: "Compliance Completion Matrix",
        explanation: "Overview of all tasks and their current resolution status in the SQLite database.",
        type: "tasks",
        items: data.all_tasks_list || []
      });
    } else if (type === "overdue_tasks") {
      setDrillDownData({
        title: "Overdue Compliance Obligations",
        explanation: "Obligations that have breached their deadline relative to their creation time.",
        type: "tasks",
        items: data.overdue_tasks_list || []
      });
    } else if (type === "tasks_at_risk") {
      setDrillDownData({
        title: "SLA Risk Exposure (Breach Probability >= 60%)",
        explanation: "Pending obligations nearing their SLA thresholds, modeled based on priority and deadline proximity.",
        type: "tasks",
        items: data.tasks_at_risk_list || []
      });
    } else if (type === "total_mapped") {
      setDrillDownData({
        title: "Total Mapped Obligations",
        explanation: "Comprehensive list of all compliance actions generated from the document text.",
        type: "tasks",
        items: data.all_tasks_list || []
      });
    }
  };

  useEffect(() => {
    async function fetchAnalytics() {
      setLoading(true);
      try {
        const url = selectedDocId ? `/analytics?document_id=${selectedDocId}` : "/analytics";
        const res = await api.get(url);
        setData(res.data);
      } catch (err) {
        console.error("Failed to load analytics", err);
      } finally {
        setLoading(false);
      }
    }
    fetchAnalytics();
  }, [selectedDocId]);

  if (loading) {
    return (
      <GlassCard>
        <p className="text-slate-300">Loading AI Predictive Analytics...</p>
      </GlassCard>
    );
  }

  if (!data) return <p className="text-red-400">Failed to load predictive models.</p>;

  return (
    <div className="space-y-6 overflow-y-auto pb-8">
      <GlassCard>
        <h3 className="text-xl font-display text-white mb-2">Predictive AI Insights</h3>
        <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-4 text-red-200 shadow-[0_0_15px_rgba(239,68,68,0.2)]">
          <strong>⚠️ Alert:</strong> {data.prediction_alert}
        </div>
      </GlassCard>

      {/* SLA METRICS ROW */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          onClick={() => handleCardClick("completion_rate")}
          className="cursor-pointer group hover:scale-[1.02] transition-transform duration-300"
        >
          <GlassCard className="border-emerald-500/20 hover:border-emerald-500/40 hover:bg-white/[0.02] h-full transition-all">
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">
              Completion Rate <span className="material-symbols-outlined text-xs text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity">open_in_new</span>
            </p>
            <h3 className="text-3xl font-display font-bold text-emerald-400">{data.completion_rate}%</h3>
            <p className="text-[10px] text-slate-500 mt-2">Real compliance actions completed</p>
          </GlassCard>
        </div>
        
        <div 
          onClick={() => handleCardClick("overdue_tasks")}
          className="cursor-pointer group hover:scale-[1.02] transition-transform duration-300"
        >
          <GlassCard className="border-red-500/20 hover:border-red-500/40 hover:bg-white/[0.02] h-full transition-all">
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">
              Overdue Tasks <span className="material-symbols-outlined text-xs text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">open_in_new</span>
            </p>
            <h3 className="text-3xl font-display font-bold text-red-400">{data.overdue_tasks}</h3>
            <p className="text-[10px] text-slate-500 mt-2">Tasks past deadline in SQLite</p>
          </GlassCard>
        </div>

        <div 
          onClick={() => handleCardClick("tasks_at_risk")}
          className="cursor-pointer group hover:scale-[1.02] transition-transform duration-300"
        >
          <GlassCard className="border-orange-500/20 hover:border-orange-500/40 hover:bg-white/[0.02] h-full transition-all">
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">
              Tasks At Risk <span className="material-symbols-outlined text-xs text-orange-400 opacity-0 group-hover:opacity-100 transition-opacity">open_in_new</span>
            </p>
            <h3 className="text-3xl font-display font-bold text-orange-400">{data.tasks_at_risk_count}</h3>
            <p className="text-[10px] text-slate-500 mt-2">Pending tasks with breach risk &gt;= 60%</p>
          </GlassCard>
        </div>

        <div 
          onClick={() => handleCardClick("total_mapped")}
          className="cursor-pointer group hover:scale-[1.02] transition-transform duration-300"
        >
          <GlassCard className="border-sky-500/20 hover:border-sky-500/40 hover:bg-white/[0.02] h-full transition-all">
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">
              Total Mapped Actions <span className="material-symbols-outlined text-xs text-sky-400 opacity-0 group-hover:opacity-100 transition-opacity">open_in_new</span>
            </p>
            <h3 className="text-3xl font-display font-bold text-sky-400">{data.total_tasks}</h3>
            <p className="text-[10px] text-slate-500 mt-2">Total tasks derived from document</p>
          </GlassCard>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard>
          <div>
            <h3 className="text-lg font-display text-white">Risk Anomalies (Monthly Trend)</h3>
            <p className="text-[10px] text-slate-500 mt-1 mb-4">Data Origin: High-priority compliance tasks and system alerts history queried from SQLite</p>
          </div>
          <div className="h-72 w-full flex items-center justify-center">
            {data.historical_data_available && data.monthly_trends && data.monthly_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.monthly_trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" />
                  <XAxis dataKey="month" stroke="#cbd5e1" />
                  <YAxis stroke="#cbd5e1" />
                  <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #334155" }} />
                  <Legend />
                  <Line type="monotone" dataKey="risk_anomalies" stroke="#f87171" strokeWidth={3} name="Detected Anomalies" />
                  <Line type="monotone" dataKey="resolved" stroke="#34d399" strokeWidth={3} name="Resolved Compliance Tasks" />
                  <Line type="monotone" dataKey="risk_records" stroke="#fb923c" strokeWidth={2} name="Real Risk Records" />
                  <Line type="monotone" dataKey="alerts" stroke="#f472b6" strokeWidth={2} name="Real Alerts" />
                  <Line type="monotone" dataKey="workflow_tasks" stroke="#60a5fa" strokeWidth={2} name="Workflow Tasks" />
                  <Line type="monotone" dataKey="compliance_findings" stroke="#a78bfa" strokeWidth={2} name="Compliance Findings" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-slate-400 font-medium text-sm flex flex-col items-center gap-2">
                <span className="material-symbols-outlined text-slate-500 text-3xl">history_toggle_off</span>
                <span>Insufficient historical data</span>
              </div>
            )}
          </div>
        </GlassCard>

        <GlassCard>
          <div>
            <h3 className="text-lg font-display text-white">SLA Breach Rate by Department</h3>
            <p className="text-[10px] text-slate-500 mt-1 mb-4">Data Origin: Calculated from departmental task SLA status from SQLite database</p>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.department_performance}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" />
                <XAxis dataKey="department" stroke="#cbd5e1" />
                <YAxis stroke="#cbd5e1" />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #334155" }} />
                <Legend />
                <Bar dataKey="sla_breach_rate" fill="#fbbf24" name="SLA Breach Rate (%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>

      {/* Dynamic Drilldown Modal */}
      <AnimatePresence>
        {drillDownData && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="glass-card max-w-4xl w-full max-h-[85vh] flex flex-col p-6 border-white/10 overflow-hidden relative shadow-[0_0_50px_rgba(0,0,0,0.8)] text-left"
            >
              <div className="flex justify-between items-start mb-5 pb-3 border-b border-white/5">
                <div>
                  <h3 className="text-xl font-bold text-white font-display flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary font-bold">query_stats</span> {drillDownData.title}
                  </h3>
                  {drillDownData.explanation && (
                    <p className="text-xs text-slate-400 mt-1">{drillDownData.explanation}</p>
                  )}
                </div>
                <button 
                  onClick={() => setDrillDownData(null)}
                  className="p-1 rounded-full hover:bg-white/10 text-slate-400 hover:text-white transition flex items-center justify-center"
                >
                  <span className="material-symbols-outlined text-base">close</span>
                </button>
              </div>

              <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
                {drillDownData.items.length === 0 ? (
                  <div className="text-slate-500 text-center py-12 italic">No matching records found in database.</div>
                ) : (
                  <div className="overflow-x-auto">
                    {drillDownData.type === "tasks" && (
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-white/10 text-slate-400 uppercase tracking-wider font-mono text-[9px]">
                            <th className="py-2.5 px-3">Title</th>
                            <th className="py-2.5 px-3">Department</th>
                            <th className="py-2.5 px-3">Priority</th>
                            <th className="py-2.5 px-3">SLA Risk</th>
                            <th className="py-2.5 px-3">Status</th>
                            <th className="py-2.5 px-3">Deadline</th>
                          </tr>
                        </thead>
                        <tbody>
                          {drillDownData.items.map((t, idx) => (
                            <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                              <td className="py-3 px-3 text-white font-medium max-w-sm whitespace-normal leading-relaxed">{t.title}</td>
                              <td className="py-3 px-3 text-slate-300 font-mono text-[10px]">{t.department}</td>
                              <td className="py-3 px-3">
                                <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider font-bold ${
                                  t.priority.toLowerCase() === 'high' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                                  t.priority.toLowerCase() === 'medium' ? 'bg-warning/10 text-warning border border-warning/20' :
                                  'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                }`}>
                                  {t.priority}
                                </span>
                              </td>
                              <td className="py-3 px-3 font-mono text-[10px]">
                                {t.status.toLowerCase() === 'completed' ? (
                                  <span className="text-slate-500">—</span>
                                ) : (
                                  <span className={`font-bold ${
                                    t.breach_probability >= 80 ? 'text-red-400' :
                                    t.breach_probability >= 60 ? 'text-orange-400' :
                                    t.breach_probability >= 30 ? 'text-warning' :
                                    'text-emerald-400'
                                  }`}>
                                    {t.breach_probability}%
                                  </span>
                                )}
                              </td>
                              <td className="py-3 px-3">
                                <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider font-bold ${
                                  t.status.toLowerCase() === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                                  'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                                }`}>
                                  {t.status}
                                </span>
                              </td>
                              <td className="py-3 px-3 text-slate-400">{t.deadline}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </div>
              
              <div className="mt-5 pt-4 border-t border-white/5 flex justify-end">
                <button 
                  onClick={() => setDrillDownData(null)}
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