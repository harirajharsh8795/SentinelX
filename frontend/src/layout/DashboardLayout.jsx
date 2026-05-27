import { useEffect, useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import CommandPalette from "../components/CommandPalette.jsx";
import useKeyboardShortcuts from "../hooks/useKeyboardShortcuts.js";
import { motion, AnimatePresence } from "framer-motion";
import Sidebar from "../components/Sidebar.jsx";
import TopBar from "../components/TopBar.jsx";
import Toast from "../components/Toast.jsx";
import Notifications from "../components/Notifications.jsx";
import { useStore } from "../store/useStore.js";

export default function DashboardLayout() {
  const toasts = useStore((state) => state.toasts);
  const pushToast = useStore((state) => state.pushToast);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useKeyboardShortcuts({
    onCommandPalette: () => setPaletteOpen(true),
    navigate,
  });

  useEffect(() => {
    const handleToastEvent = (e) => {
      if (e.detail && e.detail.message) {
        pushToast(e.detail.message, e.detail.type || "info");
      }
    };
    window.addEventListener("sentinel:toast", handleToastEvent);
    return () => window.removeEventListener("sentinel:toast", handleToastEvent);
  }, [pushToast]);

  return (
    <div className="flex h-screen bg-background text-textMain overflow-hidden font-sans relative selection:bg-primary/30">
      {/* Background glow effects */}
      <div className="fixed inset-0 z-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none"></div>
      <div className="fixed -top-[20vw] -right-[10vw] w-[50vw] h-[50vw] rounded-full bg-primary mix-blend-screen filter blur-[100px] pointer-events-none opacity-[0.15]"></div>
      
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0 relative z-10">
        {location.pathname !== "/upload" && <TopBar />}
        
        <div className="flex-1 overflow-auto custom-scrollbar p-6">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-7xl mx-auto"
          >
            <Outlet />
          </motion.div>
        </div>
      </main>

      <AnimatePresence>
        {paletteOpen && <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />}
      </AnimatePresence>

      <Notifications />

      <div className="fixed bottom-4 right-4 z-[999] flex flex-col gap-2">
        <AnimatePresence>
          {toasts.map((t) => (
            <Toast key={t.id} type={t.type} message={t.message} />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}