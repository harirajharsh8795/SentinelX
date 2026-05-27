import { useState, useEffect } from "react";
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard>
          <h3 className="text-lg font-display text-white mb-4">Risk Anomalies (Monthly Trend)</h3>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.monthly_trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" />
                <XAxis dataKey="month" stroke="#cbd5e1" />
                <YAxis stroke="#cbd5e1" />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #334155" }} />
                <Legend />
                <Line type="monotone" dataKey="risk_anomalies" stroke="#f87171" strokeWidth={3} name="Detected Anomalies" />
                <Line type="monotone" dataKey="resolved" stroke="#34d399" strokeWidth={3} name="Resolved" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard>
          <h3 className="text-lg font-display text-white mb-4">SLA Breach Rate by Department</h3>
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
    </div>
  );
}