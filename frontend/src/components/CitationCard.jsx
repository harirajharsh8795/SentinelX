export default function CitationCard({ source, index, onInspect }) {
  const score = source.score != null ? (source.score * 100).toFixed(1) : null;
  return (
    <button
      type="button"
      onClick={() => onInspect?.(source, index)}
      className="w-full text-left bg-white/5 hover:bg-mint/10 border border-white/10 hover:border-mint/30 rounded-xl p-4 transition-all group"
    >
      <div className="flex justify-between items-start gap-2 mb-2">
        <span className="text-gold font-bold text-xs uppercase tracking-wide">
          Source {index + 1}: {source.section_title || "Section"}
        </span>
        {score && (
          <span className="text-mint text-xs font-mono shrink-0">{score}% match</span>
        )}
      </div>
      <p className="text-slate-400 text-sm leading-relaxed line-clamp-3 group-hover:text-slate-200">
        "{source.snippet}"
      </p>
      {onInspect && (
        <span className="text-xs text-mint/70 mt-2 inline-block group-hover:text-mint">
          Click to inspect full clause →
        </span>
      )}
    </button>
  );
}
