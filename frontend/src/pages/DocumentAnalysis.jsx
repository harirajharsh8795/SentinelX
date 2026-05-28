import { useEffect, useState } from "react";
import GlassCard from "../components/GlassCard.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import api from "../services/api.js";
import { Link } from "react-router-dom";
import { useStore } from "../store/useStore.js";

export default function DocumentAnalysis() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const docId = useStore((state) => state.selectedDocId);

  const fetchAnalysis = (targetDocId, isRetry = false) => {
    setLoading(true);
    setError("");
    api
      .post("/analyze-document", null, { params: { doc_id: targetDocId } })
      .then((response) => {
        setAnalysis(response.data);
        localStorage.setItem(`analysis_${targetDocId}`, JSON.stringify(response.data));
        setLoading(false);
      })
      .catch((err) => {
        if (!isRetry) {
          console.warn("Analysis failed, auto-retrying once...");
          fetchAnalysis(targetDocId, true);
        } else {
          setAnalysis(null);
          setError(err?.response?.data?.detail || "Analysis failed. Please retry.");
          setLoading(false);
        }
      });
  };

  useEffect(() => {
    if (!docId) {
      setAnalysis(null);
      setLoading(false);
      setError("");
      return;
    }

    const stored = localStorage.getItem(`analysis_${docId}`);
    if (stored) {
      setAnalysis(JSON.parse(stored));
      setLoading(false);
      setError("");
      return;
    }

    fetchAnalysis(docId, false);
  }, [docId]);

  if (!docId) {
    return (
      <div className="flex flex-col items-center justify-center h-[80vh] text-center space-y-4">
        <h2 className="text-2xl font-display text-white">No Document Active</h2>
        <p className="text-slate-400">Please upload a document to view executive intelligence summary & insights.</p>
        <Link to="/upload" className="px-6 py-2 bg-primary/20 text-primary border border-primary/30 rounded-full hover:bg-primary transition">
          Upload Document
        </Link>
      </div>
    );
  }

  const maps = analysis?.maps || [];
  const risks = analysis?.risks || [];

  // Phase 4: Dynamic confidence - use actual backend score, fallback to heuristic only if missing
  const getConfidence = (item) => {
    if (item.confidence !== undefined && item.confidence !== null) {
      return parseFloat(item.confidence).toFixed(2);
    }
    // Heuristic fallback only when backend doesn't provide a score
    const key = (item.severity || "").toLowerCase();
    if (key.includes("high")) return "0.85";
    if (key.includes("medium")) return "0.70";
    if (key.includes("low")) return "0.55";
    return "0.60";
  };

  const confidenceBadgeColor = (score) => {
    const num = parseFloat(score);
    if (num >= 0.8) return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
    if (num >= 0.6) return "bg-blue-500/20 text-blue-300 border-blue-500/30";
    return "bg-amber-500/20 text-amber-300 border-amber-500/30";
  };

  return (
    <div className="grid gap-8">
      <GlassCard>
        <h3 className="text-xl font-display text-white">Executive Intelligence Summary</h3>
        {loading ? (
          <div className="mt-3 space-y-4">
            <div className="text-sm text-mint animate-pulse font-medium">
              AI processing on Jetson hardware...
            </div>
            <LoadingSkeleton />
          </div>
        ) : error ? (
          <div className="mt-4 space-y-4">
            <p className="text-gold text-base">{error}</p>
            <button
              onClick={() => fetchAnalysis(docId, false)}
              className="px-4 py-2 bg-primary/20 text-primary border border-primary/30 rounded-full hover:bg-primary transition text-sm font-medium"
            >
              Retry Analysis
            </button>
          </div>
        ) : (
          <p className="mt-4 text-base text-slate-200/80 whitespace-pre-wrap leading-relaxed font-sans">
            {analysis?.summary || "Summary unavailable"}
          </p>
        )}
      </GlassCard>

      <GlassCard>
        <h3 className="text-xl font-display text-white">Strategic Compliance Insights</h3>
        {loading ? (
          <div className="mt-3 space-y-4">
            <div className="text-sm text-mint animate-pulse font-medium">
              AI processing on Jetson hardware...
            </div>
            <LoadingSkeleton />
          </div>
        ) : (
          <p className="mt-4 text-base text-slate-200/80 whitespace-pre-wrap leading-relaxed font-sans">
            {analysis?.executive_insights || "Strategic insights will appear after analysis."}
          </p>
        )}
      </GlassCard>

      <div className="grid gap-8 xl:grid-cols-2">
        <GlassCard>
          <h3 className="text-xl font-display">Extracted MAPs</h3>
          <div className="mt-6 space-y-4">
            {maps.length ? (
              maps.map((item) => (
                <div key={item.title} className="rounded-2xl bg-white/5 p-5">
                  <p className="text-base font-medium">{item.title}</p>
                  <p className="text-sm text-slate-200/60">
                    {item.department} • {item.deadline} • {item.severity}
                  </p>
                  <p className="text-sm text-mint">
                    Source: {item.source || item.source_section}
                  </p>
                  <div className="mt-2">
                    <span className={`inline-block rounded-md px-2.5 py-1 text-xs font-semibold shadow-sm border ${confidenceBadgeColor(getConfidence(item))}`}>
                      Confidence: {getConfidence(item)}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-white/10 px-5 py-6 text-sm text-slate-200/60">
                No MAPs generated yet
              </div>
            )}
          </div>
        </GlassCard>

        <GlassCard>
          <h3 className="text-xl font-display">Risk Analysis</h3>
          <div className="mt-6 space-y-4">
            {risks.length ? (
              risks.map((item) => (
                <div key={item.risk} className="rounded-2xl bg-white/5 p-5">
                  <p className="text-base font-medium">{item.risk}</p>
                  <p className="text-sm text-slate-200/60">{item.reason}</p>
                  <p className="text-sm text-gold">
                    {item.severity} • {item.source || item.source_section}
                  </p>
                  <div className="mt-2">
                    <span className={`inline-block rounded-md px-2.5 py-1 text-xs font-semibold shadow-sm border ${confidenceBadgeColor(getConfidence(item))}`}>
                      Confidence: {getConfidence(item)}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-white/10 px-5 py-6 text-sm text-slate-200/60">
                No risks generated yet
              </div>
            )}
          </div>
        </GlassCard>
      </div>

      <GlassCard>
        <h3 className="text-xl font-display">Why AI flagged this</h3>
        {loading ? (
          <div className="mt-3">
            <LoadingSkeleton />
          </div>
        ) : analysis?.agent_reasoning?.length ? (
          <div className="mt-6 space-y-3">
            {analysis.agent_reasoning.map((item, index) => (
              <div key={`${item}-${index}`} className="rounded-2xl bg-white/5 p-4 text-sm">
                {item}
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-base text-slate-200/70">
            AI reasoning will appear after analysis completes.
          </p>
        )}
      </GlassCard>

      <GlassCard>
        <h3 className="text-xl font-display">Source Citations (RAG Retrieval)</h3>
        {loading ? (
          <div className="mt-3">
            <LoadingSkeleton />
          </div>
        ) : analysis?.sources?.length ? (
          <div className="mt-6 space-y-4">
            {analysis.sources.map((item, index) => (
              <div key={`${item.section_title}-${index}`} className="rounded-2xl bg-white/5 p-5 border-l-4 border-mint">
                <p className="text-base font-semibold text-mint">{item.section_title}</p>
                <p className="text-sm font-mono mt-2 text-slate-200/80 bg-black/20 p-3 rounded">
                  "{item.snippet}"
                </p>
                <div className="mt-3 flex justify-between items-center text-xs text-slate-200/50">
                  <span>Semantic Relevance Score: {item.score ? item.score.toFixed(3) : "0.500"}</span>
                  <span className="px-2 py-1 bg-white/10 rounded-full">Cited Source</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-base text-slate-200/70">
            No source citations available for this document.
          </p>
        )}
      </GlassCard>
    </div>
  );
}
