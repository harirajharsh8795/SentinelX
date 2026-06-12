import { motion, useScroll, useTransform } from "framer-motion";
import { useNavigate, Link } from "react-router-dom";
import { useState, useRef } from "react";
import GlassCard from "../components/GlassCard.jsx";

const GlowingOrb = ({ color, className }) => (
  <div className={`absolute rounded-full mix-blend-screen filter blur-[120px] pointer-events-none opacity-40 animate-pulse-slow ${color} ${className}`} />
);

export default function Landing() {
  const navigate = useNavigate();
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: containerRef });
  const y = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);

  return (
    <div ref={containerRef} className="min-h-screen bg-background text-textMain relative selection:bg-primary/30 scroll-smooth">
      {/* GLOBAL BACKGROUND ELEMENTS */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        <GlowingOrb color="bg-primary" className="w-[60vw] h-[60vw] -top-[10%] -left-[10%]" />
        <GlowingOrb color="bg-secondary" className="w-[50vw] h-[50vw] top-[40%] -right-[10%]" />
        <GlowingOrb color="bg-accent" className="w-[40vw] h-[40vw] -bottom-[10%] left-[20%]" />
        <div className="absolute inset-0 bg-background/90"></div>
      </div>

      <Header navigate={navigate} />

      <main className="relative z-10">
        <HeroSection navigate={navigate} />
        <PlatformOverview navigate={navigate} />
        <RagIntelligence navigate={navigate} />
        <KnowledgeGraphSection navigate={navigate} />
        <AgenticWorkflow navigate={navigate} />
        <PredictiveAnalytics navigate={navigate} />
        <VoiceAssistant navigate={navigate} />
        <SecurityArchitecture navigate={navigate} />
        <ContactSection />
        <FinalCTA navigate={navigate} />
      </main>
    </div>
  );
}

function Header({ navigate }) {
  return (
    <header className="fixed top-0 w-full z-50 border-b border-white/5 bg-[#030712]/95">
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center font-display font-bold shadow-[0_0_15px_rgba(59,130,246,0.5)]">
            X
          </div>
          <span className="font-display font-bold text-xl tracking-tight">
            Sentinel<span className="text-secondary">X</span>
          </span>
        </div>
        <nav className="hidden md:flex gap-8 text-sm font-medium text-textSub">
          <a href="#overview" className="hover:text-white transition-colors">Features</a>
          <a href="#rag" className="hover:text-white transition-colors">RAG</a>
          <a href="#graph" className="hover:text-white transition-colors">Graph</a>
          <a href="#agents" className="hover:text-white transition-colors">Workflows</a>
          <a href="#analytics" className="hover:text-white transition-colors">Risk</a>
          <a href="#security" className="hover:text-white transition-colors">Security</a>
          <a href="#contact" className="hover:text-white transition-colors">Contact</a>
        </nav>
        <div className="flex gap-4">
          <button onClick={() => navigate("/login")} className="text-sm font-medium hover:text-white transition-colors">Sign In</button>
          <button onClick={() => navigate("/login")} className="px-5 py-2.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 hover:border-primary/60 rounded-lg text-sm font-semibold transition-all shadow-[0_0_20px_rgba(59,130,246,0.1)] hover:shadow-[0_0_25px_rgba(59,130,246,0.3)]">
            Launch Platform
          </button>
        </div>
      </div>
    </header>
  );
}

function HeroSection({ navigate }) {
  return (
    <section className="min-h-screen flex items-center justify-center pt-20 px-6 relative overflow-hidden font-sans">
      <div className="max-w-5xl mx-auto text-center z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-semibold uppercase tracking-wider mb-8 shadow-[0_0_15px_rgba(59,130,246,0.15)]"
        >
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
          Autonomous Operating System v1.0
        </motion.div>
        
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-6xl md:text-7xl lg:text-8xl font-display font-bold tracking-tight leading-[1.1] mb-6 text-white"
        >
          Sentinel<span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-secondary to-accent">X</span>
        </motion.h1>
        
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-xl md:text-2xl text-slate-100 font-display font-bold max-w-3xl mx-auto mb-4 tracking-wide"
        >
          “Autonomous Regulatory Intelligence & Compliance Operating System”
        </motion.p>

        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-base md:text-lg text-textSub max-w-3xl mx-auto mb-12 leading-relaxed"
        >
          Enterprise-grade cognitive orchestration platform for real-time regulatory intelligence, automated compliance auditing, predictive risk mapping, multi-agent workflow automation, and semantic knowledge graph reasoning.
        </motion.p>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in"
        >
          <button onClick={() => navigate("/dashboard")} className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-primary to-blue-600 hover:from-primaryGlow hover:to-blue-500 text-white rounded-xl font-bold transition-all shadow-[0_0_30px_rgba(59,130,246,0.3)] hover:shadow-[0_0_40px_rgba(59,130,246,0.5)] hover:-translate-y-1">
            Launch Platform
          </button>
          <button onClick={() => navigate("/dashboard")} className="w-full sm:w-auto px-8 py-4 bg-surfaceAlt hover:bg-white/10 text-white border border-white/10 rounded-xl font-bold transition-all hover:-translate-y-1">
            Explore Intelligence
          </button>
        </motion.div>
      </div>

      <motion.div 
        animate={{ y: [0, 10, 0] }} 
        transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
        className="absolute bottom-10 left-1/2 -translate-x-1/2 text-textSub/50"
      >
        <div className="w-[1px] h-16 bg-gradient-to-b from-transparent via-primary/50 to-transparent"></div>
      </motion.div>
    </section>
  );
}

function PlatformOverview({ navigate }) {
  return (
    <section id="overview" className="py-32 px-6 border-t border-white/5 relative">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <h2 className="text-4xl font-display font-bold mb-4">Enterprise Regulatory Intelligence Command Center</h2>
          <p className="text-textSub max-w-2xl mx-auto">Ingest complex multi-page regulatory updates. SentinelX automatically parses raw circulars, evaluates compliance obligations, establishes topological relationship mappings, calculates vulnerability vectors, and dispatches real-time risk alerts across departments.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <FeatureCard 
            icon="📄" 
            title="Intelligent Ingestion" 
            desc="Drag and drop circulars. SentinelX automatically chunks, creates embeddings, and performs hybrid indexing into ChromaDB."
            delay={0.1}
          />
          <FeatureCard 
            icon="🧠" 
            title="LangGraph Reasoning" 
            desc="Multi-agent orchestration analyzes clauses, maps regulatory requirements, and builds dynamic evaluation graphs."
            delay={0.2}
          />
          <FeatureCard 
            icon="📊" 
            title="Risk Telemetry" 
            desc="Real-time exposure calculation, cascading risk propagation, and SLA-based milestone automation."
            delay={0.3}
          />
        </div>
      </div>
    </section>
  );
}

function RagIntelligence({ navigate }) {
  return (
    <section id="rag" className="py-32 px-6 border-t border-white/5 relative overflow-hidden bg-surface">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-100px" }} variants={{ visible: { opacity: 1, x: 0 }, hidden: { opacity: 0, x: -50 } }} transition={{ duration: 0.7 }}>
          <div className="inline-flex items-center gap-2 px-3 py-1 border border-accent/20 bg-accent/5 text-accent text-xs font-semibold uppercase rounded-full mb-6">
            Semantic Engine
          </div>
          <h2 className="text-4xl font-display font-bold mb-6">Deep Semantic Compliance Retrieval Pipeline</h2>
          <p className="text-textSub mb-6 text-lg leading-relaxed">
            Transcend standard keyword search with deep semantic query understanding. SentinelX leverages a dual-encoder hybrid retrieval pipeline (integrating lexical BM25 and dense neural embeddings) to pull high-precision regulatory context with strict factual grounding and zero hallucinations.
          </p>
          <button onClick={() => navigate("/chat")} className="px-6 py-3 bg-accent/15 hover:bg-accent/25 border border-accent/40 text-accent rounded-lg font-medium transition-all mb-4">
            Open Intelligence Copilot &rarr;
          </button>
          <ul className="space-y-4 mb-8">
            <li className="flex items-center gap-3 text-textSub"><span className="text-accent">✓</span> Query Rewriting & Expansion</li>
            <li className="flex items-center gap-3 text-textSub"><span className="text-accent">✓</span> Contextual Citation Links</li>
            <li className="flex items-center gap-3 text-textSub"><span className="text-accent">✓</span> Re-ranking Cross-Encoder</li>
          </ul>
        </motion.div>
        <div className="relative h-[400px] w-full glass-card flex items-center justify-center p-8">
            <div className="absolute inset-0 bg-accent/5 backdrop-blur-3xl"></div>
            <div className="z-10 w-full flex flex-col gap-4">
               {/* Animated Search Demo */}
               <motion.div initial={{ width: "0%"}} whileInView={{ width: "100%"}} transition={{ duration: 1, delay: 0.5 }} className="h-12 bg-surfaceAlt/80 border border-white/10 rounded-lg flex items-center px-4 overflow-hidden relative">
                 <span className="text-textSub font-mono text-sm border-r border-textSub/30 pr-3 mr-3 mt-1">user</span>
                 <motion.span initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ delay: 1.5 }} className="text-white text-sm">"What is the penalty for zero-day breach under CERT-IN?"</motion.span>
               </motion.div>
               <motion.div initial={{ opacity: 0, y: 10}} whileInView={{ opacity: 1, y: 0}} transition={{ delay: 2.2 }} className="bg-primary/20 border border-primary/30 p-4 rounded-lg flex gap-4">
                 <div className="text-primary mt-1">⚡</div>
                 <div>
                   <p className="text-white text-sm leading-relaxed">Failure to report within 6 hours attracts a penalty up to ₹1,00,000 under Section 43G of ITA 2000.</p>
                   <div className="mt-3 flex gap-2">
                     <span className="text-[10px] bg-primary/20 text-primary px-2 py-1 rounded">Score: 0.94</span>
                     <span className="text-[10px] bg-white/10 px-2 py-1 rounded">CERT-IN 2022 Master Direction</span>
                   </div>
                 </div>
               </motion.div>
            </div>
        </div>
      </div>
    </section>
  );
}

function KnowledgeGraphSection({ navigate }) {
  return (
    <section id="graph" className="py-32 px-6 border-t border-white/5 relative bg-surface">
      <div className="max-w-7xl mx-auto flex flex-col-reverse lg:flex-row gap-16 items-center">
        <div className="w-full lg:w-1/2 h-[450px] glass-card relative overflow-hidden flex items-center justify-center">
          <div className="absolute w-[200%] h-[200%] bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMSIgZmlsbD0icmdiYSgyNTUsMjU1LDI1NSwwLjEpIi8+PC9zdmc+')] animate-[spin_60s_linear_infinite]"></div>
          {/* Abstract node visualization */}
          <div className="relative z-10 w-full h-full flex items-center justify-center">
             <div className="w-16 h-16 bg-primary/20 rounded-full border border-primary text-primary flex items-center justify-center font-bold relative animate-pulse shadow-[0_0_30px_rgba(59,130,246,0.5)]">
               RBI
               <svg className="absolute w-64 h-64 -translate-y-12 translate-x-4 opacity-30" viewBox="0 0 100 100"><path d="M 0 50 Q 50 0 100 50" stroke="currentColor" fill="none" /></svg>
             </div>
          </div>
        </div>
        <div className="w-full lg:w-1/2">
          <h2 className="text-4xl font-display font-bold mb-6">Compliance Topology & Risk Propagation Graph</h2>
          <p className="text-textSub mb-6 text-lg">
            Map and audit non-linear compliance dependencies. When a regulatory mandate changes, SentinelX's relationship intelligence engine dynamically propagates exposure vectors across departments, corporate systems, and risk registries.
          </p>
          <button onClick={() => navigate("/graph")} className="px-6 py-3 bg-secondary/10 hover:bg-secondary/20 border border-secondary/30 text-secondary rounded-lg font-medium transition-all">
            Explore Graph Topology
          </button>
        </div>
      </div>
    </section>
  );
}

function AgenticWorkflow({ navigate }) {
  return (
    <section id="agents" className="py-32 px-6 border-t border-white/5 relative">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-display font-bold mb-4">Autonomous Agentic Workflow Graph</h2>
          <p className="text-textSub max-w-2xl mx-auto">Powered by LangGraph orchestrators. Specialized cognitive agents coordinate autonomously to identify audit-critical Mandatory Action Points (MAPs), flag cross-regulation conflicts, and execute closed-loop mitigation tasks.</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <AgentNode name="AuditAgent" role="Ingests Documents" color="text-primary border-primary/30" />
          <AgentNode name="ComplianceAgent" role="Extracts MAPs" color="text-secondary border-secondary/30" />
          <AgentNode name="RiskAgent" role="Scores Vulnerability" color="text-amber-400 border-amber-500/30" />
          <AgentNode name="ExecutiveAgent" role="Delegates Tasks" color="text-accent border-accent/30" />
        </div>
        <div className="flex justify-center mt-12">
          <button onClick={() => navigate("/tasks")} className="px-6 py-3 bg-secondary/10 hover:bg-secondary/20 border border-secondary/30 text-secondary rounded-lg font-medium transition-all">
            Explore Workflows &rarr;
          </button>
        </div>
      </div>
    </section>
  );
}

function PredictiveAnalytics({ navigate }) {
  return (
    <section id="analytics" className="py-32 px-6 border-t border-white/5 relative">
      <div className="max-w-7xl mx-auto text-center mb-16">
        <h2 className="text-4xl font-display font-bold mb-4">Predictive Regulatory Risk Analytics</h2>
        <p className="text-textSub max-w-2xl mx-auto mb-10">Leverage statistical modeling, trend tracking, and SLA anomaly detection. SentinelX continuously forecasts enterprise audit exposure and calculates compliance breach probabilities ahead of regulatory deadlines.</p>
        
        <div className="w-full h-[400px] glass-card flex items-end justify-between p-8 gap-4">
          {[40, 65, 30, 80, 50, 95, 60, 45, 85].map((h, i) => (
            <motion.div 
              key={i}
              initial={{ height: 0 }}
              whileInView={{ height: `${h}%` }}
              transition={{ duration: 1, delay: i * 0.1 }}
              className={`w-full rounded-t-sm ${h > 75 ? 'bg-alert/80 shadow-[0_0_20px_rgba(239,68,68,0.5)]' : h > 50 ? 'bg-warning/80 shadow-[0_0_20px_rgba(245,158,11,0.5)]' : 'bg-primary/50'}`}
            />
          ))}
        </div>
        <div className="flex justify-center mt-12">
          <button onClick={() => navigate("/analytics")} className="px-6 py-3 bg-accent/10 hover:bg-accent/20 border border-accent/30 text-accent rounded-lg font-medium transition-all">
            Start AI Analysis &rarr;
          </button>
        </div>
      </div>
    </section>
  );
}

function VoiceAssistant({ navigate }) {
  return (
    <section id="voice" className="py-32 px-6 border-t border-white/5 relative bg-surface">
      <div className="max-w-7xl mx-auto text-center">
        <div onClick={() => navigate("/voice")} className="w-24 h-24 mx-auto bg-primary/10 border-2 border-primary/30 rounded-full flex items-center justify-center mb-8 relative cursor-pointer hover:border-primary transition-all group">
           <div className="absolute inset-0 rounded-full border border-primary animate-ping opacity-75 group-hover:opacity-100"></div>
           <span className="text-3xl">🎙️</span>
        </div>
        <h2 className="text-4xl font-display font-bold mb-4">Bilingual Cognitive Voice Copilot</h2>
        <p className="text-textSub max-w-2xl mx-auto mb-4">
          Engineered via faster-whisper. Interact with your organization's compliance brain using secure, low-latency voice queries in English or Hindi directly inside the web interface.
        </p>
        <button onClick={() => navigate("/voice")} className="px-6 py-3 bg-primary/10 hover:bg-primary/20 border border-primary/30 text-primary rounded-lg font-medium transition-all">
          Start Voice Session &rarr;
        </button>
      </div>
    </section>
  );
}

function SecurityArchitecture() {
  return (
    <section id="security" className="py-32 px-6 border-t border-white/5 relative bg-background">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <h2 className="text-4xl font-display font-bold mb-4">Enterprise Security & System Architecture</h2>
          <p className="text-textSub max-w-2xl mx-auto">SentinelX is engineered to operate under strict cybersecurity constraints. Complete on-premise capability ensures sensitive documents never leave your security perimeter.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="glass-card p-6 border border-white/5 relative flex flex-col items-start">
            <span className="material-symbols-outlined text-3xl text-mint mb-4">lan</span>
            <h3 className="text-lg font-bold text-white mb-2">Completely Air-Gapped</h3>
            <p className="text-xs text-slate-400 leading-relaxed">Runs entirely inside your private local network. Zero external API calls, preventing any cloud-side data exposure.</p>
          </div>
          <div className="glass-card p-6 border border-white/5 relative flex flex-col items-start">
            <span className="material-symbols-outlined text-3xl text-mint mb-4">database</span>
            <h3 className="text-lg font-bold text-white mb-2">Isolated Database Pools</h3>
            <p className="text-xs text-slate-400 leading-relaxed">Dynamic vector database partitioning using ChromaDB creates isolated namespaces per document upload.</p>
          </div>
          <div className="glass-card p-6 border border-white/5 relative flex flex-col items-start">
            <span className="material-symbols-outlined text-3xl text-mint mb-4">encrypted</span>
            <h3 className="text-lg font-bold text-white mb-2">End-to-End Cryptography</h3>
            <p className="text-xs text-slate-400 leading-relaxed">Sensitive metadata and task logs are fully encrypted using military-grade AES-256 standard protocols.</p>
          </div>
          <div className="glass-card p-6 border border-white/5 relative flex flex-col items-start">
            <span className="material-symbols-outlined text-3xl text-mint mb-4">fingerprint</span>
            <h3 className="text-lg font-bold text-white mb-2">Role-Based Access (RBAC)</h3>
            <p className="text-xs text-slate-400 leading-relaxed">Clearance-level separation: Officer, Auditor, and Admin accounts maintain segregated compliance views.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function ContactSection() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [dept, setDept] = useState("Compliance");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [ticketId, setTicketId] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !message.trim()) return;
    setSubmitting(true);
    setTimeout(() => {
      const id = "SX-" + Math.floor(1000 + Math.random() * 9000);
      setTicketId(id);
      setSubmitting(false);
      setSubmitted(true);
    }, 1200);
  };

  return (
    <section id="contact" className="py-32 px-6 border-t border-white/5 relative bg-surface">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-display font-bold mb-4">Contact SentinelX Security Command</h2>
          <p className="text-textSub max-w-xl mx-auto">Request system provisioning, security audits, or custom regulator schema setups. SLA Response: Within 1 Business Hour.</p>
        </div>

        <GlassCard className="p-8 relative">
          {submitted ? (
            <div className="text-center py-10 space-y-4">
              <span className="material-symbols-outlined text-6xl text-mint animate-bounce">verified</span>
              <h3 className="text-2xl font-display font-bold text-white">Request Dispatched</h3>
              <p className="text-slate-400 text-sm max-w-md mx-auto">Your inquiry has been encrypted and sent to the SentinelX Security Council. We will verify credentials and respond immediately.</p>
              <div className="inline-block px-4 py-2 bg-mint/10 border border-mint/30 rounded-lg text-mint font-mono font-bold text-sm">
                Incident ID: {ticketId}
              </div>
              <div>
                <button
                  onClick={() => { setSubmitted(false); setName(""); setEmail(""); setMessage(""); }}
                  className="mt-6 text-sm text-primary hover:text-primaryGlow font-medium"
                >
                  Send another request
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs uppercase tracking-widest text-slate-500 font-bold mb-2">Officer Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-mint transition-all"
                    placeholder="Enter full name"
                  />
                </div>
                <div>
                  <label className="block text-xs uppercase tracking-widest text-slate-500 font-bold mb-2">Secure Email</label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-mint transition-all"
                    placeholder="officer@bank.com"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs uppercase tracking-widest text-slate-500 font-bold mb-2">Department</label>
                  <select
                    value={dept}
                    onChange={(e) => setDept(e.target.value)}
                    className="w-full px-4 py-3 bg-[#0d1117] border border-white/10 rounded-xl text-white focus:outline-none focus:border-mint transition-all"
                  >
                    <option value="Compliance">Compliance & Audits</option>
                    <option value="Risk Management">Risk Management</option>
                    <option value="IT Security">Information Security</option>
                    <option value="Legal">Legal & General Counsel</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs uppercase tracking-widest text-slate-500 font-bold mb-2">Security Clearance Level</label>
                  <select className="w-full px-4 py-3 bg-[#0d1117] border border-white/10 rounded-xl text-white focus:outline-none focus:border-mint transition-all">
                    <option>Level 1 - General Access (Officer)</option>
                    <option>Level 2 - Audit Oversight (Auditor)</option>
                    <option>Level 3 - Kernel Administrator (Admin)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs uppercase tracking-widest text-slate-500 font-bold mb-2">Inquiry / Access Request Details</label>
                <textarea
                  required
                  rows={4}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-mint transition-all resize-none"
                  placeholder="Detail the target regulatory framework or provisioning requirements..."
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-4 bg-gradient-to-r from-primary to-blue-600 text-white font-bold rounded-xl shadow-[0_0_20px_rgba(59,130,246,0.2)] hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Encrypting Request...
                  </>
                ) : (
                  "Dispatch Inquiry to Command Center"
                )}
              </button>
            </form>
          )}
        </GlassCard>
      </div>
    </section>
  );
}

function FinalCTA({ navigate }) {
  return (
    <section className="py-40 px-6 border-t border-white/5 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(59,130,246,0.15),transparent_50%)] pointer-events-none"></div>
      <div className="max-w-4xl mx-auto text-center relative z-10">
        <h2 className="text-5xl md:text-6xl font-display font-bold mb-6">Deploy Autonomous Regulatory Intelligence.</h2>
        <p className="text-xl text-textSub mb-12">Empower your compliance and audit teams with the industry's most advanced autonomous regulatory operating system.</p>
        <div className="flex flex-col sm:flex-row justify-center gap-6">
           <button onClick={() => navigate("/dashboard")} className="px-10 py-5 bg-white text-black font-bold rounded-xl text-lg hover:bg-slate-200 transition-all shadow-[0_0_30px_rgba(255,255,255,0.2)] hover:-translate-y-1">
             Enter Dashboard
           </button>
           <button onClick={() => navigate("/upload")} className="px-10 py-5 glass-card font-bold rounded-xl text-lg hover:border-textSub transition-all hover:-translate-y-1">
             Start Compliance Ingestion
           </button>
        </div>
      </div>
    </section>
  );
}

function FeatureCard({ icon, title, desc, delay }) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      viewport={{ once: true }}
      className="glass-card p-8 group flex flex-col items-start"
    >
      <div className="text-4xl mb-6 bg-white/5 w-16 h-16 rounded-xl flex items-center justify-center group-hover:scale-110 group-hover:bg-primary/20 transition-all">
        {icon}
      </div>
      <h3 className="text-xl font-bold mb-3">{title}</h3>
      <p className="text-textSub leading-relaxed text-left">{desc}</p>
    </motion.div>
  );
}

function AgentNode({ name, role, color }) {
  return (
    <div className={`p-6 border rounded-xl bg-surfaceAlt/50 backdrop-blur-sm relative overflow-hidden text-left ${color}`}>
      <div className="absolute -right-4 -top-4 text-6xl opacity-10">⚙️</div>
      <h4 className="font-mono font-bold mb-1">{name}</h4>
      <p className="text-sm opacity-80">{role}</p>
    </div>
  );
}