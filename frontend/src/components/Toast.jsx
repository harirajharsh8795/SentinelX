import { motion } from "framer-motion";

export default function Toast({ type = "info", message }) {
  const styles = {
    success: "border-emerald-500/30 bg-emerald-950/90 text-emerald-200 shadow-[0_0_20px_rgba(16,185,129,0.2)]",
    warning: "border-amber-500/30 bg-amber-950/90 text-amber-200 shadow-[0_0_20px_rgba(245,158,11,0.2)]",
    error: "border-red-500/30 bg-red-950/90 text-red-200 shadow-[0_0_20px_rgba(239,68,68,0.2)]",
    info: "border-blue-500/30 bg-blue-950/90 text-blue-200 shadow-[0_0_20px_rgba(59,130,246,0.2)]",
  };

  const icons = {
    success: "check_circle",
    warning: "warning",
    error: "error",
    info: "info",
  };

  const themeClass = styles[type] || styles.info;
  const iconName = icons[type] || icons.info;

  return (
    <motion.div
      initial={{ opacity: 0, y: 15, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9, y: -10 }}
      className={`glass-card flex items-center gap-3 px-5 py-3.5 rounded-2xl border text-sm max-w-sm font-sans ${themeClass}`}
    >
      <span className="material-symbols-outlined text-[18px] shrink-0">{iconName}</span>
      <span className="leading-tight font-medium">{message}</span>
    </motion.div>
  );
}
