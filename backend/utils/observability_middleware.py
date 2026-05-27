"""FastAPI middleware for request-level observability."""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from services.observability_service import TraceContext


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in ("/", "/docs", "/openapi.json"):
            return await call_next(request)
        op = f"http:{request.method}:{request.url.path}"
        with TraceContext(op, {"path": request.url.path}) as ctx:
            response = await call_next(request)
            ctx.add_tokens()
            return response
