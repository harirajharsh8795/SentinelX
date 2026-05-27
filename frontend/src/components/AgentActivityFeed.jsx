import { motion } from "framer-motion";

export default function AgentActivityFeed({ items }) {
  if (!items.length) {
    return (
      <div className="rounded-2xl border border-dashed border-white/10 px-5 py-6 text-sm text-slate-200/60">
        Agent activity will appear here
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item, index) => (
        <motion.div
          key={`${item}-${index}`}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="rounded-2xl bg-white/5 px-5 py-4 text-sm"
        >
          {item}
        </motion.div>
      ))}
    </div>
  );
}
