import { useEffect, useState, useRef, useCallback } from "react";
import GlassCard from "../components/GlassCard.jsx";
import api from "../services/api.js";
import { Link, useNavigate } from "react-router-dom";
import ForceGraph2D from "react-force-graph-2d";
import { useStore } from "../store/useStore.js";

export default function KnowledgeGraph() {
  const navigate = useNavigate();
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [meta, setMeta] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [nodeDetail, setNodeDetail] = useState(null);
  const [showRiskFlow, setShowRiskFlow] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);
  const graphRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const docId = useStore((state) => state.selectedDocId);

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight || 600,
        });
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    const fetchGraph = async () => {
      if (!docId) {
        setLoading(false);
        return;
      }
      try {
        const res = await api.get(`/knowledge-graph/${docId}`, { timeout: 120000 });
        const nodes = res.data.nodes.map((n) => ({
          ...n,
          val: 3 + (n.risk_score || 0) * 8,
        }));
        setGraphData({
          nodes,
          links: res.data.edges.map((e) => ({
            source: e.source,
            target: e.target,
            label: e.label,
            weight: e.weight,
          })),
        });
        setMeta({
          document_name: res.data.document_name,
          regulator: res.data.regulator,
          framework: res.data.framework,
          risk_summary: res.data.risk_summary,
        });
      } catch (err) {
        console.error(err);
        setError("Failed to generate Knowledge Graph from document.");
      } finally {
        setLoading(false);
      }
    };

    fetchGraph();
  }, [docId]);

  // Calibration of D3 Force Directed Spacing to prevent node overlaps
  useEffect(() => {
    if (graphRef.current) {
      graphRef.current.d3Force("charge").strength(-250);
      graphRef.current.d3Force("link").distance(120);
    }
  }, [graphData]);

  const handleNodeClick = useCallback(async (node) => {
    setSelectedNode(node);
    try {
      const res = await api.get(`/knowledge-graph/${docId}/node/${node.id}`, { timeout: 120000 });
      setNodeDetail(res.data);
    } catch {
      setNodeDetail({ node, connections: [] });
    }
  }, [docId]);

  const getNodeColor = (node) => {
    if (showRiskFlow && node.risk_score > 0.5) {
      const intensity = Math.min(1, node.risk_score);
      return `rgba(255, 75, 75, ${0.5 + intensity * 0.5})`;
    }
    return node.color || "#FFFFFF";
  };

  if (!docId) {
    return (
      <div className="flex flex-col items-center justify-center h-[80vh] text-center space-y-4">
        <h2 className="text-2xl font-display text-white">No Document Active</h2>
        <p className="text-slate-400">Please upload a document to generate its entity graph.</p>
        <Link to="/upload" className="px-6 py-2 bg-gold/10 text-gold border border-gold/20 rounded-full hover:bg-gold hover:text-black transition">
          Upload Document
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[85vh] gap-4">
      <div className="flex justify-between items-end flex-wrap gap-4">
        <div>
          <h2 className="text-3xl font-display text-white mb-2">Knowledge Relationship Mapping</h2>
          <p className="text-slate-400 max-w-2xl">
            {meta?.document_name || "Document"} — click nodes for source-linked intelligence.
            {meta?.regulator && <span className="text-mint ml-2">[{meta.regulator}]</span>}
          </p>
          {meta?.risk_summary && (
            <p className="text-sm text-orange-400 mt-1">
              Risk propagation: {meta.risk_summary.high_risk_nodes} high-risk nodes • depth {meta.risk_summary.max_propagation}
            </p>
          )}
        </div>
        <div className="flex gap-3 items-center">
          <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={showRiskFlow}
              onChange={(e) => setShowRiskFlow(e.target.checked)}
              className="accent-mint"
            />
            Risk propagation heatmap
          </label>
          {["Document", "Department", "Rule", "Action", "Penalty", "Risk"].map((type) => (
            <div key={type} className="flex items-center gap-1 text-xs text-slate-400">
              <div className="w-2 h-2 rounded-full" style={{
                backgroundColor: { Document: "#A49970", Department: "#00E5FF", Rule: "#7C3AED", Action: "#F6D365", Penalty: "#FF4B4B", Risk: "#FF6B35" }[type],
              }} />
              {type}
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-1 gap-4 min-h-0">
        <GlassCard className="flex-1 overflow-hidden p-0 relative" ref={containerRef}>
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-8 h-8 border-4 border-mint border-t-transparent rounded-full animate-spin" />
            </div>
          ) : error ? (
            <div className="absolute inset-0 flex items-center justify-center text-red-400">{error}</div>
          ) : (
            <>
              <ForceGraph2D
                ref={graphRef}
                width={dimensions.width}
                height={dimensions.height}
                graphData={graphData}
                onNodeClick={handleNodeClick}
                onNodeDoubleClick={handleNodeClick}
                onNodeHover={(node) => setHoveredNode(node)}
                nodeLabel={() => ""} // Suppress standard browser tooltip
                nodeColor={getNodeColor}
                nodeVal="val"
                linkColor={() => (showRiskFlow ? "rgba(255,100,80,0.25)" : "rgba(255,255,255,0.15)")}
                linkWidth={(link) => (link.weight || 1) * 1.5}
                linkDirectionalArrowLength={4}
                linkDirectionalArrowRelPos={1}
                linkLabel="label"
                backgroundColor="transparent"
                cooldownTicks={80}
                nodeCanvasObject={(node, ctx, globalScale) => {
                  const label = node.label?.slice(0, 24) || "";
                  const fontSize = 11 / globalScale;
                  ctx.fillStyle = getNodeColor(node);
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, node.val || 5, 0, 2 * Math.PI);
                  ctx.fill();
                  ctx.font = `${fontSize}px sans-serif`;
                  ctx.textAlign = "center";
                  ctx.fillStyle = "rgba(255,255,255,0.85)";
                  ctx.fillText(label, node.x, node.y + (node.val || 5) + 10);
                }}
              />
              
              {/* Glassmorphic interactive hover card */}
              {hoveredNode && (
                <div
                  className="absolute z-40 pointer-events-none glass-card p-3.5 rounded-xl border border-slate-700/50 bg-slate-900/90 text-white shadow-2xl text-xs"
                  style={{
                    left: "20px",
                    bottom: "20px",
                    maxWidth: "280px"
                  }}
                >
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <span className="h-2 w-2 rounded-full animate-pulse" style={{
                      backgroundColor: { Document: "#A49970", Department: "#00E5FF", Rule: "#7C3AED", Action: "#F6D365", Penalty: "#FF4B4B", Risk: "#FF6B35" }[hoveredNode.type] || "#FFF"
                    }} />
                    <span className="font-bold uppercase tracking-wider text-[10px] text-slate-300">{hoveredNode.type}</span>
                    {hoveredNode.severity && (
                      <span className="ml-auto text-[9px] px-1.5 py-0.5 bg-red-500/20 text-red-300 rounded font-bold">{hoveredNode.severity}</span>
                    )}
                  </div>
                  <div className="font-bold text-slate-100 mb-1 text-sm leading-snug">{hoveredNode.label}</div>
                  {hoveredNode.risk_score > 0 && (
                    <div className="text-orange-400 font-semibold mb-1">Risk Score: {(hoveredNode.risk_score * 100).toFixed(0)}%</div>
                  )}
                  {hoveredNode.source_section && (
                    <div className="text-slate-400 mt-1 italic line-clamp-3 leading-relaxed">"{hoveredNode.source_section}"</div>
                  )}
                  <div className="text-[10px] text-slate-500 mt-2 border-t border-white/5 pt-1.5">Click node to lock detail and trace relationships</div>
                </div>
              )}
            </>
          )}
        </GlassCard>

        {selectedNode && (
          <GlassCard className="w-80 shrink-0 overflow-y-auto p-5 space-y-4">
            <div className="flex justify-between items-start">
              <h3 className="text-mint font-bold text-lg">{selectedNode.label}</h3>
              <button type="button" onClick={() => { setSelectedNode(null); setNodeDetail(null); }} className="text-slate-500 hover:text-white">✕</button>
            </div>
            <div className="flex gap-2 flex-wrap">
              <span className="text-xs px-2 py-1 bg-white/10 rounded-full">{selectedNode.type}</span>
              {selectedNode.severity && (
                <span className="text-xs px-2 py-1 bg-red-500/20 text-red-300 rounded-full">{selectedNode.severity}</span>
              )}
              {selectedNode.risk_score > 0 && (
                <span className="text-xs px-2 py-1 bg-orange-500/20 text-orange-300 rounded-full">
                  Risk {(selectedNode.risk_score * 100).toFixed(0)}%
                </span>
              )}
            </div>
            {selectedNode.source_section && (
              <div>
                <h4 className="text-xs text-gold font-bold uppercase mb-1">Source Clause</h4>
                <p className="text-sm text-slate-300">{selectedNode.source_section}</p>
                {selectedNode.source_snippet && (
                  <p className="text-xs text-slate-500 mt-2 italic leading-relaxed">
                    "{selectedNode.source_snippet.slice(0, 280)}..."
                  </p>
                )}
              </div>
            )}
            {nodeDetail?.connections?.length > 0 && (
              <div>
                <h4 className="text-xs text-mint font-bold uppercase mb-2">Relationships</h4>
                <ul className="space-y-2 text-sm">
                  {nodeDetail.connections.slice(0, 6).map((c, i) => (
                    <li key={i} className="text-slate-400">
                      <span className="text-slate-500">{c.edge}</span> → {c.node?.label}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <button
              onClick={() => {
                const queryText = `Analyze the regulatory details, implications, and actions associated with the ${selectedNode.type} "${selectedNode.label}".`;
                localStorage.setItem("pending_copilot_query", queryText);
                navigate("/chat");
              }}
              className="w-full block text-center text-sm py-2 bg-mint/10 hover:bg-mint/25 text-mint border border-mint/30 rounded-lg transition-all font-bold font-sans"
            >
              Ask Intelligence Copilot →
            </button>
          </GlassCard>
        )}
      </div>
    </div>
  );
}
