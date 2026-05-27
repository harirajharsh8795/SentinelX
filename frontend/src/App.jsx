import { MotionConfig } from "framer-motion";
import RoutesConfig from "./routes/index.jsx";

const isJetsonMode = import.meta.env.VITE_JETSON_MODE === "true";

if (isJetsonMode) {
  document.documentElement.classList.add("jetson-mode");
}

export default function App() {
  // Simple ease-out transitions with max 0.15s duration
  const transitionConfig = isJetsonMode
    ? { type: "tween", duration: 0 }
    : { type: "tween", ease: "easeOut", duration: 0.15 };

  return (
    <MotionConfig
      transition={transitionConfig}
      reducedMotion={isJetsonMode ? "always" : "user"}
    >
      <RoutesConfig />
    </MotionConfig>
  );
}
