import GlassCard from "../components/GlassCard.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import useFetch from "../hooks/useFetch.js";
import { useStore } from "../store/useStore.js";

export default function AgentLogs() {
  const selectedDocId = useStore((state) => state.selectedDocId);
  const { data, loading } = useFetch(selectedDocId ? `/agent-logs?document_id=${selectedDocId}` : "/agent-logs", { items: [] });
  const logs = data?.items || [];

  return (
    <GlassCard>
      <h3 className="text-xl font-display">Agent Activity Logs</h3>
      <div className="mt-6 space-y-4">
        {loading ? (
          <LoadingSkeleton />
        ) : logs.length ? (
          logs.map((log) => (
            <div key={log.id} className="rounded-2xl bg-white/5 p-5">
              <p className="text-base font-medium">{log.agent}</p>
              <p className="text-sm text-slate-200/70">{log.action}</p>
              <p className="text-sm text-mint">{log.time || log.timestamp}</p>
            </div>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-white/10 px-5 py-6 text-sm text-slate-200/60">
            No agent activity yet
          </div>
        )}
      </div>
    </GlassCard>
  );
}
