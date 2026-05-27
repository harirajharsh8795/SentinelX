import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const colors = ["#F5C45E", "#1AB6FF", "#4EF0C2", "#94a3b8"];

export default function RiskDonut({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-52 items-center justify-center rounded-2xl border border-dashed border-white/10 text-sm text-slate-200/60">
        No risk mix yet
      </div>
    );
  }

  return (
    <div className="h-52">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" innerRadius={55} outerRadius={80}>
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "rgba(15, 23, 42, 0.9)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 12
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
