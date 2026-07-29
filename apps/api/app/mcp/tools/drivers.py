from uuid import UUID

from app.mcp.logging import log_tool_call
from app.mcp.responses import McpResponse, fail, ok
from app.mcp.serializers import serialize


@log_tool_call("list_available_drivers")
def list_available_drivers() -> McpResponse:
    """List currently available drivers."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            drivers = services.drivers.available_drivers()
            payload = serialize(drivers)

        return ok(
           "Available drivers loaded.",
                    {"drivers": payload},)

    except Exception as exc:
        return fail(str(exc))


@log_tool_call("get_driver_status")
def get_driver_status(driver_id: str) -> McpResponse:
    """Fetch a driver's current status."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            status = services.drivers.driver_status(UUID(driver_id))
        return ok("Driver status loaded.", {"status": serialize(status)})
    except Exception as exc:
        return fail(str(exc))


@log_tool_call("assign_driver")
def assign_driver(
    plan_id: str,
    order_id: str,
    driver_id: str,
    vehicle_id: str | None = None,
    session_id: str | None = None,
) -> McpResponse:
    """Assign or reassign an order to a driver in a plan."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            assignment = services.assignments.assign_driver(
                plan_id=UUID(plan_id),
                order_id=UUID(order_id),
                driver_id=UUID(driver_id),
                vehicle_id=UUID(vehicle_id) if vehicle_id else None,
                session_id=UUID(session_id) if session_id else None,
            )
            payload = serialize(assignment)

        return ok("Driver assigned.", {"assignment":payload},)
    except Exception as exc:
        return fail(str(exc))


def register(mcp) -> None:
    for tool in [list_available_drivers, get_driver_status, assign_driver]:
        mcp.tool()(tool)
