import { Routes, Route, Navigate } from "react-router-dom";
import DashboardLayout from "../layout/DashboardLayout.jsx";
import Landing from "../pages/Landing.jsx";
import Login from "../pages/Login.jsx";
import Dashboard from "../pages/Dashboard.jsx";
import Upload from "../pages/Upload.jsx";
import DocumentAnalysis from "../pages/DocumentAnalysis.jsx";
import Chat from "../pages/Chat.jsx";
import KnowledgeGraph from "../pages/KnowledgeGraph.jsx";
import Tasks from "../pages/Tasks.jsx";
import AgentLogs from "../pages/AgentLogs.jsx";
import AuditTimeline from "../pages/AuditTimeline.jsx";
import Analytics from "../pages/Analytics.jsx";
import Risk from "../pages/Risk.jsx";
import Voice from "../pages/Voice.jsx";
import Settings from "../pages/Settings.jsx";

function PrivateRoute({ children }) {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/login" replace />;
}

export default function RoutesConfig() {
  return (
    <Routes>
      {/* Landing page restored for the Full Enterprise Experience */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route element={<PrivateRoute><DashboardLayout /></PrivateRoute>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/analysis" element={<DocumentAnalysis />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/graph" element={<KnowledgeGraph />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/risk" element={<Risk />} />
        <Route path="/voice" element={<Voice />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/agent-logs" element={<AgentLogs />} />
        <Route path="/audit" element={<AuditTimeline />} />
      </Route>
    </Routes>
  );
}
