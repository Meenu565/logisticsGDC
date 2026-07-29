from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Optional API-key guard for production deployments."""

    public_prefixes = ("/docs", "/redoc", "/openapi.json")
    public_paths = ("/api/v1/health",)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.backend_api_key:
            return await call_next(request)
        if request.url.path in self.public_paths or request.url.path.startswith(self.public_prefixes):
            return await call_next(request)
        if request.headers.get("X-API-Key") != settings.backend_api_key:
            return Response(status_code=401, content="Invalid or missing API key.")
        return await call_next(request)
