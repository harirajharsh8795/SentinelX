from typing import List, Optional
from pydantic import BaseModel

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    pages: int
    message: str

class MapItem(BaseModel):
    title: str
    department: str
    deadline: str
    severity: str
    source_section: str
    confidence: Optional[float] = None
    deadline_days: Optional[int] = None

class RiskItem(BaseModel):
    risk: str
    severity: str
    reason: str
    source_section: str

class SourceCitation(BaseModel):
    section_title: str
    snippet: str
    score: float

class AnalysisResponse(BaseModel):
    document_id: str
    summary: str
    compliance_score: int
    risk_score: int
    maps: List[MapItem]
    risks: List[RiskItem]
    departments: List[str]
    executive_insights: str
    agent_reasoning: List[str]
    sources: List[SourceCitation] = []

class DashboardResponse(BaseModel):
    compliance_score: int
    total_documents: int
    pending_actions: int
    risk_alerts: int
    recent_uploads: List[str]
    trend: List[int]
    severity_mix: Optional[dict] = None
    open_actions: Optional[int] = None
    completed_actions: Optional[int] = None

class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    severity: Optional[str] = None
    source_section: Optional[str] = None
    source_snippet: Optional[str] = None
    risk_score: Optional[float] = None
    propagation_level: Optional[int] = None
    color: Optional[str] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    label: str
    weight: Optional[float] = 1.0

class KnowledgeGraphResponse(BaseModel):
    document_id: str
    document_name: Optional[str] = None
    regulator: Optional[str] = None
    framework: Optional[str] = None
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    risk_summary: Optional[dict] = None

class TaskItem(BaseModel):
    id: str
    title: str
    department: str
    priority: str
    status: str
    deadline: str

class TaskListResponse(BaseModel):
    items: List[TaskItem]

class AlertItem(BaseModel):
    id: str
    title: str
    severity: str
    created_at: str

class AlertListResponse(BaseModel):
    items: List[AlertItem]

class AgentLog(BaseModel):
    id: str
    agent: str
    action: str
    timestamp: str

class AgentLogListResponse(BaseModel):
    items: List[AgentLog]

class AuditEvent(BaseModel):
    id: str
    event: str
    timestamp: str

class AuditTrailResponse(BaseModel):
    items: List[AuditEvent]

class ChatMessage(BaseModel):
    role: str
    content: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str

class CrossDocumentRequest(BaseModel):
    document_ids: List[str]
    query: str = ""

class CorpusIngestRequest(BaseModel):
    source_code: Optional[str] = None
    force: bool = False

class ScrapeRunRequest(BaseModel):
    regulators: Optional[List[str]] = None

class ChatRequest(BaseModel):
    document_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    sources: List[SourceCitation] = []
    grounded: Optional[bool] = True
    grounding_confidence: Optional[float] = None
    debug: Optional[dict] = None

class DocumentItem(BaseModel):
    id: str
    filename: str
    upload_date: str
    status: str
    regulator: Optional[str] = None
    framework: Optional[str] = None
    pages: int

class DocumentListResponse(BaseModel):
    documents: List[DocumentItem]
