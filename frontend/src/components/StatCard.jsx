import GlassCard from "./GlassCard.jsx";

export default function StatCard({ title, value, hint, icon }) {
  return (
    <GlassCard className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-[11px] uppercase tracking-[0.35em] text-slate-200/80">{title}</p>
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/10 text-mint">
          {icon}
        </div>
      </div>
      <h3 className="text-4xl font-display text-white md:text-5xl">{value}</h3>
      <p className="text-sm text-slate-200/60">{hint}</p>
    </GlassCard>
  );
}
