import { useEffect, useState } from "react";

export default function useProcessingSteps(isRunning) {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (!isRunning) {
      setActiveIndex(0);
      return;
    }

    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev < 7 ? prev + 1 : prev));
    }, 900);

    return () => clearInterval(interval);
  }, [isRunning]);

  return activeIndex;
}
