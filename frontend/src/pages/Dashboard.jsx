import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState, useCallback } from "react";
import useFetch from "../hooks/useFetch.js";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useStore } from "../store/useStore.js";
import useWebsocket from "../hooks/useWebsocket.js";

export default function Dashboard() {
  const selectedDocId = useStore((state) => state.selectedDocId);
  const [drillDownData, setDrillDownData] = useState(null);
  
  const handleCardClick = (index) => {
    if (!dashboard) return;
    if (index === 0) { // Compliance Score
      setDrillDownData({
        title: "Compliance Score Audit",
        explanation: dashboard.compliance_score_details?.explanation || "Compliance Score is calculated dynamically based on pending tasks and priority metrics.",
        formula: dashboard.compliance_score_details?.formula || "max(0, 100 - (High Pending * 10 + Other Pending * 2))",
        type: "tasks",
        items: dashboard.tasks_list || []
      });
    } else if (index === 1) { // Indexed Documents
      setDrillDownData({
        title: "Indexed Documents Registry",
        explanation: "Database records of all compliance circulars ingested and indexed within the SentinelX workspace.",
        type: "documents",
        items: dashboard.documents_list || []
      });
    } else if (index === 2) { // Unresolved MAPs
      setDrillDownData({
        title: "Unresolved Governance Directives (MAPs)",
        explanation: "Pending compliance tasks and regulatory directives mapped to department owners.",
        type: "tasks",
        items: (dashboard.tasks_list || []).filter(t => t.status.toLowerCase() === "pending")
      });
    } else if (index === 3) { // Active Risks
      setDrillDownData({
        title: "Active Risk Alerts",
        explanation: "Vulnerabilities and compliance exposure warnings flagged from circular obligations.",
        type: "alerts",
        items: dashboard.alerts_list || []
      });
    }
  };
  const { data: dashboard, loading: dashboardLoading } = useFetch(selectedDocId ? `/dashboard?document_id=${selectedDocId}` : "/dashboard", null);
  const { data: tasksResponse, loading: tasksLoading } = useFetch(selectedDocId ? `/tasks?document_id=${selectedDocId}` : "/tasks", { items: [] });
  
  const loading = dashboardLoading || tasksLoading;
  
  // Realtime activity simulation pulse
  const [pulse, setPulse] = useState(false);
  useEffect(() => {
    const interval = setInterval(() => setPulse(p => !p), 2000);
    return () => clearInterval(interval);
  }, []);

  const token = localStorage.getItem("token");
  const [events, setEvents] = useState([]);

  // Fetch initial telemetry events from backend
  const { data: telemetryResponse } = useFetch("/telemetry", { events: [] });

  useEffect(() => {
    if (telemetryResponse && telemetryResponse.events) {
      setEvents(telemetryResponse.events);
    }
  }, [telemetryResponse]);

  // Real-time telemetry WebSocket message receiver
  const handleTelemetryMessage = useCallback((payload) => {
    if (payload && payload.type === "telemetry") {
      setEvents((prev) => {
        // Prevent duplicate events
        const isDuplicate = prev.some(
          (evt) => evt.timestamp === payload.timestamp && evt.description === payload.description
        );
        if (isDuplicate) return prev;
        return [payload, ...prev].slice(0, 50);
      });
    }
  }, []);

  // Connect to the telemetry WebSocket endpoint
  useWebsocket(handleTelemetryMessage, { path: "/api/ws/telemetry", token });

  const stats = [
    { title: "Compliance Score", value: dashboard?.compliance_score !== undefined ? `${dashboard.compliance_score}%` : "100%", change: "+2.4%", icon: "verified_user", color: "text-success", bg: "bg-success/10", border: "border-success/20" },
    { title: "Indexed Documents", value: dashboard?.total_documents ?? 0, change: "Live Sync", icon: "database", color: "text-primary", bg: "bg-primary/10", border: "border-primary/20" },
    { title: "Unresolved MAPs", value: dashboard?.pending_actions ?? 0, change: "Live Update", icon: "gavel", color: "text-warning", bg: "bg-warning/10", border: "border-warning/20" },
    { title: "Active Risks", value: dashboard?.risk_alerts ?? 0, change: "Realtime", icon: "warning", color: "text-alert", bg: "bg-alert/10", border: "border-alert/20" }
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 animate-pulse">
         {[...Array(4)].map((_, i) => <div key={i} className="h-32 bg-surfaceAlt/50 rounded-2xl border border-white/5"></div>)}
         <div className="col-span-full h-[400px] bg-surfaceAlt/50 rounded-2xl border border-white/5"></div>
      </div>
    );
  }

  // Dynamic trend data calculated from backend trend history
  const trendData = dashboard?.trend?.map((score, index) => {
    const d = new Date();
    d.setMonth(d.getMonth() - (5 - index));
    return { 
      name: d.toLocaleDateString("en-US", { month: "short" }), 
      score 
    };
  }) || [];

  return (
    <div className="flex flex-col gap-6 font-sans pb-12">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-3xl font-display font-bold">Enterprise Intelligence</h1>
        <div className="flex items-center gap-2 px-3 py-1 bg-success/10 border border-success/20 rounded-full text-success text-xs font-mono font-bold tracking-widest uppercase shadow-[0_0_15px_rgba(16,185,129,0.2)]">
          <span className={`w-2 h-2 rounded-full bg-success flex-shrink-0 ${pulse ? 'opacity-100 scale-110 shadow-[0_0_8px_rgba(16,185,129,0.8)]' : 'opacity-40'}`}></span>
          SYSTEM ONLINE
        </div>
      </div>

      {/* STATS ROW */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ scale: 1.02, y: -2 }}
            onClick={() => handleCardClick(i)}
            className={`glass-card p-6 border ${stat.border} cursor-pointer hover:bg-white/[0.02] hover:border-white/20 transition-all duration-300 shadow-lg shadow-black/20 hover:shadow-black/40`}
          >
            <div className="flex justify-between items-start mb-4">
              <div className={`p-2 rounded-xl ${stat.bg} ${stat.color}`}>
                <span className="material-symbols-outlined">{stat.icon}</span>
              </div>
              <span className="text-xs font-bold text-textSub bg-surfaceAlt px-2 py-1 rounded-full border border-white/5">
                {stat.change}
              </span>
            </div>
            <div>
              <p className="text-[10px] text-textSub font-bold uppercase tracking-wider mb-1 flex items-center gap-1">
                {stat.title} <span className="material-symbols-outlined text-[10px] opacity-0 group-hover:opacity-100 transition-opacity">open_in_new</span>
              </p>
              <h3 className="text-4xl font-display font-bold shadow-sm">{stat.value}</h3>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-4">
        
        {/* COMPLIANCE TREND CHART */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
          className="lg:col-span-2 glass-card p-6 min-h-[400px] flex flex-col"
        >
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-lg font-bold font-display tracking-wide flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">ssid_chart</span> System Exposure Trend
              </h3>
              <p className="text-[10px] text-slate-500 mt-1">Data Origin: Compliance task deadlines queried from SQLite database</p>
            </div>
            <button className="text-xs font-mono px-3 py-1 bg-surfaceAlt border border-white/10 rounded hover:bg-white/5">Last 7 Days</button>
          </div>
          <div className="flex-1 w-full h-full relative min-h-[250px] flex items-center justify-center">
            {dashboard?.historical_data_available && trendData.length > 0 ? (
              <>
                {/* Ambient chart glow */}
                <div className="absolute inset-0 bg-gradient-to-t from-primary/5 to-transparent pointer-events-none"></div>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="name" stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="#94A3B8" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0B1120', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px' }}
                      itemStyle={{ color: '#60A5FA' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="score" 
                      stroke="#3B82F6" 
                      strokeWidth={3}
                      dot={{ r: 4, fill: '#0B1120', stroke: '#3B82F6', strokeWidth: 2 }}
                      activeDot={{ r: 6, fill: '#60A5FA', stroke: 'white' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </>
            ) : (
              <div className="text-slate-400 font-medium text-sm flex flex-col items-center gap-2">
                <span className="material-symbols-outlined text-slate-500 text-3xl">history_toggle_off</span>
                <span>Insufficient historical data</span>
              </div>
            )}
          </div>
        </motion.div>

        {/* AI ACTIVITY FEED */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
          className="glass-card p-6 flex flex-col h-[400px]"
        >
          <div className="flex justify-between items-center mb-6 pb-4 border-b border-white/5">
            <h3 className="text-lg font-bold font-display tracking-wide flex items-center gap-2">
              <span className="material-symbols-outlined text-secondary">memory</span> AI Telemetry
            </h3>
            <span className="flex items-center gap-1 text-[10px] text-primary uppercase font-mono"><span className="w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span> Live</span>
          </div>
          
          <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-4">
             {events && events.length > 0 ? (
               events.map((evt, idx) => (
                 <ActivityItem 
                   key={`${evt.timestamp}-${idx}`}
                   type={evt.event_type || "info"}
                   title={evt.title || evt.badge || "System Event"}
                   desc={evt.description}
                   time={evt.relative_time || "Just now"}
                   icon={evt.icon || "info"}
                   timestamp={evt.timestamp}
                 />
               ))
             ) : (
               <div className="text-center text-textSub text-xs py-12">
                 No system activity recorded yet.
               </div>
             )}
          </div>
        </motion.div>
      </div>

      {/* Dynamic Drilldown Modal */}
      <AnimatePresence>
        {drillDownData && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="glass-card max-w-4xl w-full max-h-[85vh] flex flex-col p-6 border-white/10 overflow-hidden relative shadow-[0_0_50px_rgba(0,0,0,0.8)]"
            >
              <div className="flex justify-between items-start mb-5 pb-3 border-b border-white/5">
                <div>
                  <h3 className="text-xl font-bold text-white font-display flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary">analytics</span> {drillDownData.title}
                  </h3>
                  {drillDownData.explanation && (
                    <p className="text-xs text-slate-400 mt-1">{drillDownData.explanation}</p>
                  )}
                  {drillDownData.formula && (
                    <div className="mt-2 bg-slate-900/60 border border-white/5 px-3 py-1.5 rounded-lg font-mono text-[10px] text-primary inline-block">
                      Calculation: {drillDownData.formula}
                    </div>
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
                  <div className="text-slate-500 text-center py-12 italic">No source records found in database.</div>
                ) : (
                  <div className="overflow-x-auto">
                    {drillDownData.type === "tasks" && (
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-white/10 text-slate-400 uppercase tracking-wider font-mono text-[9px]">
                            <th className="py-2.5 px-3">Title</th>
                            <th className="py-2.5 px-3">Department</th>
                            <th className="py-2.5 px-3">Priority</th>
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

                    {drillDownData.type === "alerts" && (
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-white/10 text-slate-400 uppercase tracking-wider font-mono text-[9px]">
                            <th className="py-2.5 px-3">Alert Title</th>
                            <th className="py-2.5 px-3">Severity</th>
                            <th className="py-2.5 px-3">Created At</th>
                          </tr>
                        </thead>
                        <tbody>
                          {drillDownData.items.map((a, idx) => (
                            <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                              <td className="py-3 px-3 text-white font-medium leading-relaxed">{a.title}</td>
                              <td className="py-3 px-3">
                                <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider font-bold ${
                                  a.severity.toLowerCase() === 'high' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                                  a.severity.toLowerCase() === 'medium' ? 'bg-warning/10 text-warning border border-warning/20' :
                                  'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                }`}>
                                  {a.severity}
                                </span>
                              </td>
                              <td className="py-3 px-3 text-slate-400 font-mono text-[10px]">{a.created_at}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}

                    {drillDownData.type === "documents" && (
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-white/10 text-slate-400 uppercase tracking-wider font-mono text-[9px]">
                            <th className="py-2.5 px-3">Filename</th>
                            <th className="py-2.5 px-3">Regulator</th>
                            <th className="py-2.5 px-3">Framework</th>
                            <th className="py-2.5 px-3">Status</th>
                            <th className="py-2.5 px-3">Upload Date</th>
                          </tr>
                        </thead>
                        <tbody>
                          {drillDownData.items.map((d, idx) => (
                            <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                              <td className="py-3 px-3 text-white font-medium max-w-xs truncate">{d.filename}</td>
                              <td className="py-3 px-3">
                                <span className="px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20 text-[9px] uppercase font-mono tracking-wider font-bold">
                                  {d.regulator || "N/A"}
                                </span>
                              </td>
                              <td className="py-3 px-3 text-slate-300 font-mono text-[10px]">{d.framework || "N/A"}</td>
                              <td className="py-3 px-3">
                                <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-mono tracking-wider font-bold ${
                                  d.status.toLowerCase() === 'processed' || d.status.toLowerCase() === 'indexed' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                                  d.status.toLowerCase() === 'failed' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                                  'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                                }`}>
                                  {d.status}
                                </span>
                              </td>
                              <td className="py-3 px-3 text-slate-400 font-mono text-[10px]">{d.upload_date.replace("T", " ").substring(0, 19)}</td>
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

function ActivityItem({ type, title, desc, time, icon, timestamp }) {
  const colors = {
    primary: "text-primary bg-primary/10 border-primary/20",
    success: "text-success bg-success/10 border-success/20",
    warning: "text-warning bg-warning/10 border-warning/20",
    alert: "text-alert bg-alert/10 border-alert/20",
    info: "text-accent bg-accent/10 border-accent/20"
  };

  const typeLabels = {
    primary: "AGENT",
    success: "SUCCESS",
    warning: "WARNING",
    alert: "ALERT",
    info: "INFO"
  };

  const cleanTime = timestamp ? timestamp.replace(" UTC", "") : "";

  return (
    <div className="flex flex-col gap-2 p-3.5 bg-surfaceAlt/30 border border-white/5 rounded-xl hover:bg-white/5 transition-all duration-200">
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg border flex-shrink-0 ${colors[type] || colors.info}`}>
          <span className="material-symbols-outlined text-[16px] flex items-center justify-center">{icon}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h4 className="text-sm font-bold text-white leading-tight">{title}</h4>
            <span className={`text-[9px] font-mono font-extrabold px-1.5 py-0.5 rounded border leading-none tracking-wider ${colors[type] || colors.info}`}>
              {typeLabels[type] || "EVENT"}
            </span>
          </div>
          <p className="text-xs text-textSub leading-relaxed whitespace-pre-wrap break-words">{desc}</p>
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <span className="text-[10px] font-mono text-textSub font-bold">{time}</span>
        </div>
      </div>
      {timestamp && (
        <div className="text-[9px] font-mono text-textSub/55 border-t border-white/5 pt-1.5 flex justify-between items-center">
          <span>EVENT TIMELINE</span>
          <span>{cleanTime}</span>
        </div>
      )}
    </div>
  );
}