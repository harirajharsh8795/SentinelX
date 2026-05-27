import { motion } from "framer-motion";

const defaultSteps = [
  "Parsing PDF...",
  "Chunking regulation...",
  "Retrieving relevant clauses...",
  "Running Compliance Agent...",
  "Running Risk Agent...",
  "Generating MAPs...",
  "Calculating Compliance Score...",
  "Finalizing executive insights..."
];

export default function ProcessingSteps({ activeIndex, steps = defaultSteps }) {
  return (
    <div className="space-y-3">
      {steps.map((step, index) => (
        <motion.div
          key={step}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm ${
            index <= activeIndex ? "bg-white/10 text-white" : "bg-white/5 text-slate-200/60"
          }`}
        >
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-mint/20 text-mint">
            {index + 1}
          </span>
          <span>{step}</span>
        </motion.div>
      ))}
    </div>
  );
}
