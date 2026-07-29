from app.mcp.logging import log_tool_call
from app.mcp.responses import McpResponse, ok


@log_tool_call("health_check")
def health_check() -> McpResponse:
    """Confirm the MCP server is reachable."""
    return ok("MCP server is healthy.", {"service": "Smart Dispatcher MCP"})


def register(mcp) -> None:
    mcp.tool()(health_check)

