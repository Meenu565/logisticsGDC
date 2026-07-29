from uuid import UUID

from app.mcp.logging import log_tool_call
from app.mcp.responses import McpResponse, fail, ok
from app.mcp.serializers import serialize


@log_tool_call("import_orders_csv")
def import_orders_csv(csv_text: str, file_name: str, session_id: str | None = None, mode: str = "append") -> McpResponse:
    """Import orders from CSV text."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            parsed_session_id = UUID(session_id) if session_id else None
            import_mode = "replace" if mode == "replace" else "append"
            if import_mode == "replace" and parsed_session_id:
                services.sessions.clear_planning_state(parsed_session_id)
            result = services.orders.import_orders_csv(
                csv_text=csv_text,
                file_name=file_name,
                session_id=parsed_session_id,
                mode=import_mode,
            )
        return ok("Orders imported.", result)
    except Exception as exc:
        return fail(str(exc))


@log_tool_call("load_orders")
def load_orders(limit: int = 50) -> McpResponse:
    """Load active orders."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            orders = services.orders.list_active_orders()[:limit]

            # Serialize BEFORE leaving the session
            payload = serialize(orders)

        return ok("Orders loaded.", {"orders": payload})

    except Exception as exc:
        return fail(str(exc))

@log_tool_call("load_order_range")
def load_order_range(start: int, end: int) -> McpResponse:
    """Load orders by external numeric order range."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            orders = services.orders.load_order_range(start, end)
        return ok("Order range loaded.", {"orders": serialize(orders)})
    except Exception as exc:
        return fail(str(exc))


@log_tool_call("get_order")
def get_order(order_id: str) -> McpResponse:
    """Fetch one order."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            order = services.orders.get_order(UUID(order_id))
        return ok("Order loaded.", {"order": serialize(order)})
    except Exception as exc:
        return fail(str(exc))


@log_tool_call("update_order")
def update_order(order_id: str, updates: dict, session_id: str | None = None) -> McpResponse:
    """Update allowed order fields."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            order = services.orders.update_order(
                order_id=UUID(order_id),
                updates=updates,
                session_id=UUID(session_id) if session_id else None,
            )
        return ok("Order updated.", {"order": serialize(order)})
    except Exception as exc:
        return fail(str(exc))


@log_tool_call("cancel_order")
def cancel_order(order_id: str, session_id: str | None = None, reason: str | None = None) -> McpResponse:
    """Cancel an order."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            order = services.orders.cancel_order(
                order_id=UUID(order_id),
                session_id=UUID(session_id) if session_id else None,
                reason=reason,
            )
        return ok("Order cancelled.", {"order": serialize(order)})
    except Exception as exc:
        return fail(str(exc))


def register(mcp) -> None:
    for tool in [import_orders_csv, load_orders, load_order_range, get_order, update_order, cancel_order]:
        mcp.tool()(tool)
