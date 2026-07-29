from uuid import UUID

from app.mcp.logging import log_tool_call
from app.mcp.responses import McpResponse, fail, ok
from app.mcp.serializers import serialize


@log_tool_call("get_dispatch_context")
def get_dispatch_context(session_id: str) -> McpResponse:
    """Load the latest backend dispatch memory snapshot."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            context = services.memory.latest_dispatch_state(UUID(session_id))
        return ok("Dispatch context loaded.", {"context": serialize(context)})
    except Exception as exc:
        return fail(str(exc))


@log_tool_call("get_recent_conversation")
def get_recent_conversation(session_id: str, limit: int = 20) -> McpResponse:
    """Load recent conversation history from backend memory."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            messages = services.memory.conversation_history(UUID(session_id), limit=limit)
        return ok("Conversation loaded.", {"messages": serialize(messages)})
    except Exception as exc:
        return fail(str(exc))


def register(mcp) -> None:
    for tool in [get_dispatch_context, get_recent_conversation]:
        mcp.tool()(tool)
