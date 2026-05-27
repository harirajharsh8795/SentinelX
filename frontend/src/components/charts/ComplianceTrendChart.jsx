import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function ComplianceTrendChart({ data, xKey = "period" }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-52 items-center justify-center rounded-2xl border border-dashed border-white/10 text-sm text-slate-200/60">
        No trend data yet
      </div>
    );
  }

  return (
    <div className="h-52">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey={xKey} stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" />
          <Tooltip
            contentStyle={{
              background: "rgba(15, 23, 42, 0.9)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 12
            }}
          />
          <Line type="monotone" dataKey="score" stroke="#4EF0C2" strokeWidth={3} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
