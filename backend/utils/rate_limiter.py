import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

# Phase 12: Rate limiting & DDoS protection
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    A simple in-memory rate limiter to protect FastAPI endpoints from basic DDoS attacks.
    Limits clients to a specific number of requests per minute based on IP.
    """
    def __init__(self, app, requests_per_minute: int = 150):
        super().__init__(app)
        self.rate_limit = requests_per_minute
        self.clients = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        if client_ip not in self.clients:
            self.clients[client_ip] = []
            
        # Clean up timestamps older than 60 seconds (1 minute rolling window)
        self.clients[client_ip] = [t for t in self.clients[client_ip] if current_time - t < 60]
        
        # Check against limit
        if len(self.clients[client_ip]) >= self.rate_limit:
            return JSONResponse(
                status_code=429, 
                content={"detail": "Rate limit exceeded. Too many requests. DDoS Protection active."}
            )
            
        self.clients[client_ip].append(current_time)
        return await call_next(request)
