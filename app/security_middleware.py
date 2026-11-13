from collections import defaultdict
from time import monotonic

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        now = monotonic()
        client = request.client.host if request.client else "unknown"
        recent = [stamp for stamp in self.requests[client] if now - stamp < self.window_seconds]
        if len(recent) >= self.limit:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        recent.append(now)
        self.requests[client] = recent
        return await call_next(request)
