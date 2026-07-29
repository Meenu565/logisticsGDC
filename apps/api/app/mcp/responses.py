from typing import Any

McpResponse = dict[str, Any]


def ok(message: str, data: dict[str, Any] | None = None) -> McpResponse:
    return {
        "success": True,
        "message": message,
        "data": data or {},
    }


def fail(error: str) -> McpResponse:
    return {
        "success": False,
        "error": error,
    }

