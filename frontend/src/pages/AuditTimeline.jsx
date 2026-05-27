import GlassCard from "../components/GlassCard.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import useFetch from "../hooks/useFetch.js";
import { useStore } from "../store/useStore.js";

export default function AuditTimeline() {
  const selectedDocId = useStore((state) => state.selectedDocId);
  const { data, loading } = useFetch(selectedDocId ? `/audit-trail?document_id=${selectedDocId}` : "/audit-trail", { items: [] });
  const events = data?.items || [];

  return (
    <GlassCard>
      <h3 className="text-xl font-display">Audit Timeline</h3>
      <div className="mt-6 space-y-5">
        {loading ? (
          <LoadingSkeleton />
        ) : events.length ? (
          events.map((item) => (
            <div key={item.id} className="flex items-center gap-4">
              <div className="h-4 w-4 rounded-full bg-mint" />
              <div>
                <p className="text-base font-medium">{item.event}</p>
                <p className="text-sm text-slate-200/70">{item.time || item.timestamp}</p>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-white/10 px-5 py-6 text-sm text-slate-200/60">
            No audit events yet
          </div>
        )}
      </div>
    </GlassCard>
  );
}
