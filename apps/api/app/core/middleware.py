import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("smart_dispatcher.agent_log")


class AgentRequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        started_at = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)

        logger.info(
            "\n".join(
                [
                    "================================================",
                    "NEW REQUEST",
                    f"Method: {request.method}",
                    f"Path: {request.url.path}",
                    f"Status Code: {response.status_code}",
                    f"Elapsed MS: {elapsed_ms}",
                    "Detected Intent: NOT_EVALUATED",
                    "Gemini Called: NO",
                    "Reason: Backend skeleton request",
                    "Conversation Memory: NOT_LOADED",
                    "Dispatch Memory: NOT_LOADED",
                    "Selected MCP Tools: []",
                    "Tool Arguments: {}",
                    "Tool Results: {}",
                    "Recommendation Generated: NO",
                    "Recommendation Applied: NO",
                    "Final Response: handled by route",
                    "================================================",
                ]
            )
        )

        return response

