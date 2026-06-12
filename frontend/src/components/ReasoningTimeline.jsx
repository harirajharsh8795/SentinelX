import { useState, useEffect } from "react";
import { motion } from "framer-motion";

export default function ReasoningTimeline() {
  const [text, setText] = useState("Analyzing...");

  useEffect(() => {
    const texts = ["Analyzing...", "Thinking..."];
    let idx = 0;
    const timer = setInterval(() => {
      idx = (idx + 1) % texts.length;
      setText(texts[idx]);
    }, 2800);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex items-center gap-3 select-none font-sans py-0.5">
      {/* Option C: Modern rotating AI logo (custom curved 4-pointed star) */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 2.5, ease: "linear" }}
        className="w-5 h-5 text-mint flex items-center justify-center shrink-0"
      >
        <svg
          className="w-5 h-5 fill-current"
          viewBox="0 0 24 24"
        >
          <path d="M12 2c0 5.523 4.477 10 10 10-5.523 0-10 4.477-10 10C12 16.523 7.523 12 2 12c5.523 0 10-4.477 10-10z" />
        </svg>
      </motion.div>
      <span className="text-sm font-medium text-slate-400 tracking-wide font-sans animate-pulse">
        {text}
      </span>
    </div>
  );
}
