import { useEffect, useRef } from "react";

export default function useWebsocket(onMessage, options = {}) {
  const wsRef = useRef(null);
  const onMessageRef = useRef(onMessage);
  const reconnectTimeoutRef = useRef(null);
  const retryCountRef = useRef(0);

  // Sync the latest onMessage callback reference without triggering socket re-creation
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const { path = "/api/ws/stream", token = null } = options;

  useEffect(() => {
    let isMounted = true;
    
    function connect() {
      if (!isMounted) return;
      
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      
      // Map development Vite ports (5173, 5174, 5176, etc.) to backend FastAPI port (8000)
      let host = window.location.host;
      if (host.startsWith("localhost:") && !host.includes(":8000")) {
        host = "localhost:8000";
      }

      const sep = path.includes("?") ? "&" : "?";
      const url = token 
        ? `${protocol}://${host}${path}${sep}token=${encodeURIComponent(token)}` 
        : `${protocol}://${host}${path}`;
        
      console.log("Initiating WebSocket connection to", url);
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log("WebSocket connected successfully", url);
        retryCountRef.current = 0; // reset retry count on success
      };
      
      ws.onmessage = (e) => {
        try {
          const payload = JSON.parse(e.data);
          if (onMessageRef.current) onMessageRef.current(payload);
        } catch (err) {
          if (onMessageRef.current) onMessageRef.current({ type: "message", data: e.data });
        }
      };
      
      ws.onclose = (event) => {
        console.log("WebSocket closed. Event code:", event.code, "reason:", event.reason);
        // Do not reconnect if it was closed by the client intentionally
        if (isMounted) {
          // Calculate exponential backoff delay (starting at 1s, doubling up to 16s)
          const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 16000);
          console.log(`Scheduling WebSocket reconnect in ${delay}ms...`);
          retryCountRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }
      };
      
      ws.onerror = (err) => {
        console.warn("WebSocket encountered an error:", err);
      };

      wsRef.current = ws;
    }

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch (e) {}
      }
    };
  }, [path, token]);

  return wsRef;
}
