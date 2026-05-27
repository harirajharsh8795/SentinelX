import { useEffect } from "react";

export default function useKeyboardShortcuts({ onCommandPalette, navigate }) {
  useEffect(() => {
    let gPressed = false;
    let gTimer = null;

    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        onCommandPalette?.();
        return;
      }

      if (e.key === "g" && !e.metaKey && !e.ctrlKey) {
        gPressed = true;
        clearTimeout(gTimer);
        gTimer = setTimeout(() => { gPressed = false; }, 800);
        return;
      }

      if (gPressed && navigate && !e.metaKey && !e.ctrlKey) {
        const map = {
          d: "/dashboard",
          u: "/upload",
          a: "/analysis",
          c: "/chat",
          k: "/graph",
          t: "/tasks",
          n: "/analytics",
          l: "/agent-logs",
          r: "/audit",
        };
        if (map[e.key]) {
          e.preventDefault();
          navigate(map[e.key]);
          gPressed = false;
        }
      }
    };

    window.addEventListener("keydown", handler);
    return () => {
      window.removeEventListener("keydown", handler);
      clearTimeout(gTimer);
    };
  }, [onCommandPalette, navigate]);
}
