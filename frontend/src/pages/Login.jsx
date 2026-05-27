import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import api from "../services/api.js";

const GlowingOrb = ({ color, className }) => (
  <div className={`absolute rounded-full mix-blend-screen filter blur-[100px] pointer-events-none opacity-40 animate-pulse-slow ${color} ${className}`} />
);

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("Officer");
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      if (isRegister) {
        await api.post("/auth/register", {
          username: username.trim(),
          password: password,
          role: role
        });
        setSuccess("Account provisioned. Initialize session via login.");
        setIsRegister(false);
        setPassword("");
      } else {
        const formData = new URLSearchParams();
        formData.append("username", username.trim());
        formData.append("password", password);

        const response = await api.post("/auth/token", formData, {
          headers: {
            "Content-Type": "application/x-www-form-urlencoded"
          }
        });
        
        localStorage.setItem("token", response.data.access_token);
        
        const userRes = await api.get("/auth/users/me");
        localStorage.setItem("user", JSON.stringify(userRes.data));

        navigate("/dashboard");
      }
    } catch (err) {
      console.error("Auth Error:", err);
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Network error. Synchronization failed.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-background text-textMain items-center justify-center p-6 font-sans relative overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
      <GlowingOrb color="bg-primary" className="w-[40vw] h-[40vw] -bottom-20 -left-20" />
      <GlowingOrb color="bg-accent" className="w-[30vw] h-[30vw] -top-20 -right-20" />
      
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-[440px] p-10 glass-card z-10"
      >
        <div className="mb-8 text-center flex flex-col items-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center font-display font-extrabold text-white text-3xl shadow-[0_0_25px_rgba(59,130,246,0.5)] mb-4 cursor-pointer" onClick={() => navigate("/")}>
            X
          </div>
          <h1 className="text-3xl font-display font-bold tracking-tight mb-2 text-white">
            {isRegister ? "Initialize Access" : "Secure Authentication"}
          </h1>
          <p className="text-textSub font-sans text-sm">
            {isRegister ? "Provision a new operator profile." : "Enter Sentinel management console credentials."}
          </p>
        </div>

        {error && <div className="mb-6 p-4 rounded-xl bg-alert/10 text-alert text-sm border border-alert/20 flex items-center gap-3"><span className="text-lg">⚠️</span> {error}</div>}
        {success && <div className="mb-6 p-4 rounded-xl bg-success/10 text-success text-sm border border-success/20 flex items-center gap-3"><span className="text-lg">✅</span> {success}</div>}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-textSub mb-2 uppercase tracking-widest text-[10px]">Operator ID</label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 input-futuristic"
              placeholder="operator@sentinel.ai"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-textSub mb-2 uppercase tracking-widest text-[10px]">Passkey</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 input-futuristic"
              placeholder="••••••••"
            />
          </div>

          {isRegister && (
            <div>
              <label className="block text-sm font-medium text-textSub mb-2 uppercase tracking-widest text-[10px]">Clearance Level</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full px-4 py-3 input-futuristic bg-surfaceAlt"
              >
                <option value="Officer">Officer</option>
                <option value="Auditor">Auditor</option>
                <option value="Admin">Admin</option>
              </select>
            </div>
          )}

          <div className="flex items-center justify-between pb-2">
             {!isRegister && (
               <label className="flex items-center gap-2 text-xs text-textSub cursor-pointer">
                 <input type="checkbox" className="rounded bg-surfaceAlt border-white/10 text-primary focus:ring-primary/50" />
                 Maintain Session
               </label>
             )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r from-primary to-blue-600 hover:from-primaryGlow hover:to-blue-500 text-white font-bold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(59,130,246,0.3)] hover:shadow-[0_0_30px_rgba(59,130,246,0.5)] flex items-center justify-center gap-2"
          >
            {loading ? <span className="animate-spin text-xl">⏳</span> : (isRegister ? "Provision Clearance" : "Authenticate")}
          </button>
        </form>

        <div className="mt-8 text-center text-sm text-textSub">
          <button
            onClick={() => { setIsRegister(!isRegister); setError(""); setSuccess(""); }}
            className="text-primary font-medium hover:text-primaryGlow transition-colors focus:outline-none uppercase tracking-wider text-[11px]"
          >
            {isRegister ? "Return to Login" : "Request Access Clearance"}
          </button>
        </div>
      </motion.div>
    </div>
  );
}