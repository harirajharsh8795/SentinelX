import { NavLink, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

const links = [
  { to: "/dashboard", label: "Intelligence Overview", icon: "dashboard" },
  { to: "/upload", label: "Secure Document Ingestion", icon: "cloud_upload" },
  { to: "/analysis", label: "Executive Intelligence", icon: "insights" },
  { to: "/chat", label: "Intelligence Copilot", icon: "forum" },    
  { to: "/graph", label: "Knowledge Relationship Mapping", icon: "hub" },  
  { to: "/tasks", label: "Compliance Workflows", icon: "fact_check" },
  { to: "/risk", label: "Risk Intelligence Center", icon: "warning" },
  { to: "/analytics", label: "Predictive Risk Analytics", icon: "trending_up" },
  { to: "/voice", label: "Voice Intelligence", icon: "mic" },
  { to: "/audit", label: "Audit Trail Timeline", icon: "history" },
  { to: "/settings", label: "System Configuration", icon: "settings" }
];

export default function Sidebar() {
  const navigate = useNavigate();
  
  let user = { role: "Admin", username: "Guest" };
  try {
    const raw = localStorage.getItem("user");
    if (raw) user = JSON.parse(raw);
  } catch(e) {}

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <motion.aside 
      initial={{ x: -50, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="w-72 border-r border-white/5 bg-surface flex flex-col pt-8 pb-6 shadow-2xl relative z-40 overflow-hidden"
    >
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(59,130,246,0.05),transparent_50%)] pointer-events-none"></div>

      <div className="px-6 mb-10 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center font-display font-extrabold text-white text-xl shadow-[0_0_20px_rgba(59,130,246,0.3)]">
          X
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white font-display">Sentinel<span className="text-accent">X</span></h1>
          <p className="text-[10px] uppercase tracking-widest font-mono text-primary animate-pulse">Autonomous OS</p>
        </div>
      </div>

      <div className="px-6 mb-8">
        <p className="text-[10px] font-bold text-textSub uppercase tracking-widest mb-3 px-2">Access Level</p>
        <div className="bg-surfaceAlt border border-white/10 rounded-xl p-3 flex items-center gap-3">
           <div className="w-8 h-8 rounded-lg bg-primary/20 text-primary flex items-center justify-center font-bold">
             {user.username.charAt(0).toUpperCase()}
           </div>
           <div>
             <p className="text-sm font-bold text-white">{user.username}</p>
             <p className="text-[10px] text-accent uppercase tracking-wider">{user.role}</p>
           </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-4 custom-scrollbar">
        <p className="text-[10px] font-bold text-textSub uppercase tracking-widest mb-3 px-4 mt-2">Intelligence Modules</p>
        <ul className="space-y-1">
          {links.map((link) => (
            <li key={link.to}>
              <NavLink
                to={link.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isActive 
                    ? "bg-primary/20 text-primary shadow-[inset_0_0_10px_rgba(59,130,246,0.2)] border border-primary/20" 
                    : "text-textSub hover:bg-white/5 hover:text-white"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                     <span className={`material-symbols-outlined text-lg ${isActive ? "drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]" : ""}`}>{link.icon}</span>
                     {link.label}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="px-6 pt-6 border-t border-white/5 mt-auto">
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-bold text-alert hover:bg-alert/10 transition-colors border border-transparent hover:border-alert/20"
        >
          <span className="material-symbols-outlined text-lg">logout</span> Secure Logout
        </button>
      </div>
    </motion.aside>
  );
}