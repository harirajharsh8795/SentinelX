"""
SentinelX Event Broadcasting Service — Real-Time Telemetry

Yeh module backend ke har real event ko WebSocket se frontend tak broadcast karta hai.
Fake hardcoded logs replace karta hai with actual system events.

Usage:
    from services.event_broadcaster import event_bus
    event_bus.emit("document_uploaded", "RBI_Circular_2026.pdf indexed with 240 chunks", doc_id="abc-123")
"""
import asyncio
import time
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """
    Centralized event bus — broadcasts real-time system events to all
    connected WebSocket clients via the ConnectionManager in stream.py.

    Event Types:
        - document_uploaded: PDF successfully ingested
        - embedding_started / embedding_completed: ChromaDB vector indexing
        - agent_node_executed: LangGraph node ran (document_analyzer, compliance_checker, etc.)
        - compliance_result: Compliance score calculated
        - task_generated: MAP tasks created in database
        - risk_detected: High-severity risk identified
        - knowledge_graph_built: KG nodes/edges updated
        - user_login: Authentication event
        - system_info: Generic system status
    """

    # Maps event types to display metadata
    EVENT_METADATA = {
        "document_uploaded":    {"type": "success", "icon": "upload_file",    "badge": "UPLOAD"},
        "embedding_started":    {"type": "info",    "icon": "memory",         "badge": "EMBED"},
        "embedding_completed":  {"type": "success", "icon": "check_circle",   "badge": "EMBED"},
        "agent_node_executed":  {"type": "primary", "icon": "smart_toy",      "badge": "AGENT"},
        "compliance_result":    {"type": "success", "icon": "verified_user",  "badge": "COMPLIANCE"},
        "task_generated":       {"type": "info",    "icon": "task_alt",       "badge": "TASK"},
        "risk_detected":        {"type": "warning", "icon": "warning",        "badge": "RISK"},
        "knowledge_graph_built":{"type": "success", "icon": "hub",            "badge": "KG"},
        "user_login":           {"type": "info",    "icon": "login",          "badge": "AUTH"},
        "system_info":          {"type": "info",    "icon": "info",           "badge": "SYSTEM"},
        "sanitizer_alert":      {"type": "warning", "icon": "shield",         "badge": "SECURITY"},
        "self_correction":      {"type": "warning", "icon": "autorenew",      "badge": "CORRECT"},
        "analysis_started":     {"type": "info",    "icon": "play_circle",    "badge": "ANALYSIS"},
        "analysis_completed":   {"type": "success", "icon": "check_circle",   "badge": "ANALYSIS"},
    }

    def __init__(self):
        # In-memory event log (last 50 events for REST API fallback)
        self._event_history: List[Dict[str, Any]] = []
        self._max_history = 50
        self._manager = None  # Lazy-loaded ConnectionManager

    def _get_manager(self):
        """Lazy import to avoid circular import with stream.py"""
        if self._manager is None:
            from api.stream import manager
            self._manager = manager
        return self._manager

    def emit(
        self,
        event_name: str,
        description: str,
        doc_id: Optional[str] = None,
        extra: Optional[dict] = None
    ):
        """
        Fire-and-forget event emission.
        Works from both sync and async contexts.

        Args:
            event_name: Key from EVENT_METADATA (e.g. "document_uploaded")
            description: Human-readable event description
            doc_id: Optional document ID to scope broadcast to a room
            extra: Optional extra payload data
        """
        meta = self.EVENT_METADATA.get(event_name, {
            "type": "info", "icon": "info", "badge": "EVENT"
        })

        event = {
            "type": "telemetry",
            "event_name": event_name,
            "event_type": meta["type"],
            "icon": meta["icon"],
            "badge": meta["badge"],
            "title": meta["badge"],
            "description": description,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "relative_time": "Just now",
            "document_id": doc_id,
        }
        if extra:
            event["extra"] = extra

        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        # Broadcast via WebSocket (non-blocking)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._broadcast(event, doc_id))
        except RuntimeError:
            # No event loop running (e.g. during startup/seeding) — skip broadcast
            logger.debug(f"[EventBus] No loop for broadcast: {event_name}")

        logger.info(f"[TELEMETRY] [{meta['badge']}] {description}")

    async def _broadcast(self, event: dict, doc_id: Optional[str]):
        """Broadcast to connected WebSocket clients."""
        mgr = self._get_manager()
        if doc_id:
            await mgr.broadcast_to_room(doc_id, event)
        # Always broadcast to global channel for Dashboard
        await mgr.broadcast_to_room("GLOBAL", event)

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """REST API fallback — returns recent events for initial page load."""
        events = list(reversed(self._event_history[-limit:]))
        # Calculate relative timestamps
        now = time.time()
        for evt in events:
            try:
                evt_time = datetime.strptime(evt["timestamp"], "%Y-%m-%d %H:%M:%S UTC")
                evt_time = evt_time.replace(tzinfo=timezone.utc)
                delta = now - evt_time.timestamp()
                if delta < 60:
                    evt["relative_time"] = "Just now"
                elif delta < 3600:
                    evt["relative_time"] = f"{int(delta // 60)}m ago"
                elif delta < 86400:
                    evt["relative_time"] = f"{int(delta // 3600)}h ago"
                else:
                    evt["relative_time"] = f"{int(delta // 86400)}d ago"
            except Exception:
                evt["relative_time"] = "—"
        return events


# Global singleton — import this everywhere
event_bus = EventBroadcaster()


class EventLogger:
    """
    Structured event logger that maps to specific system events
    and broadcasts them via the event_bus singleton.
    """

    @staticmethod
    def log_document_uploaded(doc_id: str, filename: str, details: str):
        """Logs when a document has been fully uploaded and metadata parsed."""
        event_bus.emit(
            event_name="document_uploaded",
            description=f"Document uploaded: {filename} ({details})",
            doc_id=doc_id
        )

    @staticmethod
    def log_embedding_started(doc_id: str, filename: str, chunk_count: int):
        """Logs when vector database indexing starts."""
        event_bus.emit(
            event_name="embedding_started",
            description=f"Vector embedding started for {filename} ({chunk_count} chunks)",
            doc_id=doc_id
        )

    @staticmethod
    def log_embedding_completed(doc_id: str, filename: str):
        """Logs when vector database indexing finishes successfully."""
        event_bus.emit(
            event_name="embedding_completed",
            description=f"Vector embedding completed for {filename}",
            doc_id=doc_id
        )

    @staticmethod
    def log_agent_node_executed(doc_id: str, node_name: str, status_detail: str):
        """Logs when a LangGraph node executes."""
        event_bus.emit(
            event_name="agent_node_executed",
            description=f"Node [{node_name}] executed: {status_detail}",
            doc_id=doc_id
        )

    @staticmethod
    def log_compliance_result(doc_id: str, compliance_score: float, risk_score: float, grounding_score: float):
        """Logs the final compliance check score and status."""
        event_bus.emit(
            event_name="compliance_result",
            description=f"Compliance check result: Score={compliance_score}%, Risk={risk_score}%, Grounding={grounding_score}%",
            doc_id=doc_id
        )

    @staticmethod
    def log_task_generated(doc_id: str, task_count: int, alert_count: int):
        """Logs when actionable tasks and alerts are successfully created."""
        event_bus.emit(
            event_name="task_generated",
            description=f"Generated {task_count} Actionable Tasks and {alert_count} Compliance Alerts",
            doc_id=doc_id
        )

