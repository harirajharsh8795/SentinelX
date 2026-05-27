import { useState, useEffect } from "react";
import GlassCard from "../components/GlassCard.jsx";
import api from "../services/api.js";
import { useStore } from "../store/useStore.js";
import { Link } from "react-router-dom";

const KANBAN_COLUMNS = ["pending", "in-progress", "completed"];

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const docId = useStore((state) => state.selectedDocId);

  const fetchTasks = async () => {
    if (!docId) {
      setTasks([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const res = await api.get("/tasks");
      setTasks(res.data.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [docId]);

  const moveTask = async (taskId, newStatus) => {
    // Optimistic update
    setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: newStatus } : t));
    try {
      await api.put(`/tasks/${taskId}`, { status: newStatus });
    } catch {
      fetchTasks(); // Revert on failure
    }
  };

  if (!docId) {
    return (
      <div className="flex flex-col items-center justify-center h-[80vh] text-center space-y-4">
        <h2 className="text-2xl font-display text-white">No Document Active</h2>
        <p className="text-slate-400">Please upload a document to view compliance workflows.</p>
        <Link to="/upload" className="px-6 py-2 bg-primary/20 text-primary border border-primary/30 rounded-full hover:bg-primary transition">
          Upload Document
        </Link>
      </div>
    );
  }

  if (loading) {
    return (
      <GlassCard>
        <p className="text-slate-300">Loading Kanban board...</p>
      </GlassCard>
    );
  }

  return (
    <div className="h-full flex flex-col font-sans">
      <h3 className="text-xl font-display text-white mb-6">Compliance Workflows</h3>
      <div className="flex flex-1 gap-6 overflow-x-auto pb-4">
        {KANBAN_COLUMNS.map((col) => {
          const colTasks = tasks.filter(t => {
            const s = (t.status || "pending").toLowerCase().replace("_", "-");
            return s === col;
          });
          
          return (
            <div key={col} className="w-80 flex-shrink-0 flex flex-col bg-white/5 rounded-2xl border border-white/10 p-4">
              <div className="flex justify-between items-center mb-4">
                <h4 className="font-semibold text-slate-200 capitalize">
                  {col.replace("-", " ")}
                </h4>
                <span className="text-xs bg-white/10 px-2 py-1 rounded-full text-slate-300">
                  {colTasks.length}
                </span>
              </div>

              <div className="flex-1 flex flex-col gap-3 overflow-y-auto">
                {colTasks.map((task) => (
                  <div key={task.id} className="bg-white/5 border border-white/10 p-4 rounded-xl shadow-lg hover:bg-white/10 transition-colors">
                    <div className="text-sm font-medium text-white mb-2">{task.title}</div>
                    <div className="flex justify-between items-center text-xs mb-3">
                      <span className="text-slate-300 bg-white/5 px-2 py-1 rounded">Dept: {task.department}</span>
                      <span className={`px-2 py-1 rounded ${
                        task.priority === "High" ? "bg-red-500/20 text-red-300" :
                        task.priority === "Medium" ? "bg-gold/20 text-gold" : "bg-mint/20 text-mint"
                      }`}>
                        {task.priority || "Low"}
                      </span>
                    </div>

                    <div className="flex gap-2 mt-4 pt-3 w-full border-t border-white/10">
                      {KANBAN_COLUMNS.map(targetCol => (
                        targetCol !== col && (
                          <button
                            key={targetCol}
                            onClick={() => moveTask(task.id, targetCol)}
                            className="flex-1 text-[11px] py-1 rounded bg-accent/80 hover:bg-accent text-black font-bold capitalize transition"
                          >
                            Move to {targetCol.replace("-", " ")}
                          </button>
                        )
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
