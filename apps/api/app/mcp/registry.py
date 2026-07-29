from dataclasses import dataclass
from typing import Any, Callable

from app.mcp.responses import McpResponse
from app.mcp.tools import drivers, eta, health, memory, orders, planning, recommendations

ToolFunction = Callable[..., McpResponse]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    function: ToolFunction


TOOL_SPECS: dict[str, ToolSpec] = {
    "health_check": ToolSpec("health_check", "Confirm the MCP server is healthy.", {}, health.health_check),
    "import_orders_csv": ToolSpec(
        "import_orders_csv",
        "Import orders from CSV text.",
        {"csv_text": "string", "file_name": "string", "session_id": "uuid|null"},
        orders.import_orders_csv,
    ),
    "load_orders": ToolSpec(
        "load_orders",
        "Load active orders.",
        {"limit": "integer"},
        orders.load_orders,
    ),
    "load_order_range": ToolSpec(
        "load_order_range",
        "Load orders by numeric external order range.",
        {"start": "integer", "end": "integer"},
        orders.load_order_range,
    ),
    "get_order": ToolSpec("get_order", "Fetch one order.", {"order_id": "uuid"}, orders.get_order),
    "update_order": ToolSpec(
        "update_order",
        "Update allowed order fields.",
        {"order_id": "uuid", "updates": "object", "session_id": "uuid|null"},
        orders.update_order,
    ),
    "cancel_order": ToolSpec(
        "cancel_order",
        "Cancel an order.",
        {"order_id": "uuid", "session_id": "uuid|null", "reason": "string|null"},
        orders.cancel_order,
    ),
    "optimize_routes": ToolSpec(
        "optimize_routes",
        "Build a proposed optimized dispatch plan.",
        {"session_id": "uuid", "route_date": "YYYY-MM-DD", "order_ids": "list[uuid]|null"},
        planning.optimize_routes,
    ),
    "rebuild_plan": ToolSpec(
        "rebuild_plan",
        "Rebuild a proposed plan after an operational change.",
        {"session_id": "uuid", "route_date": "YYYY-MM-DD", "order_ids": "list[uuid]|null"},
        planning.rebuild_plan,
    ),
    "summarize_plan": ToolSpec(
        "summarize_plan",
        "Summarize route count and metrics for a plan.",
        {"plan_id": "uuid"},
        planning.summarize_plan,
    ),
    "list_available_drivers": ToolSpec(
        "list_available_drivers",
        "List currently available drivers.",
        {},
        drivers.list_available_drivers,
    ),
    "get_driver_status": ToolSpec(
        "get_driver_status",
        "Fetch a driver's current status.",
        {"driver_id": "uuid"},
        drivers.get_driver_status,
    ),
    "assign_driver": ToolSpec(
        "assign_driver",
        "Assign or reassign an order to a driver in a plan.",
        {"plan_id": "uuid", "order_id": "uuid", "driver_id": "uuid", "vehicle_id": "uuid|null", "session_id": "uuid|null"},
        drivers.assign_driver,
    ),
    "calculate_eta": ToolSpec(
        "calculate_eta",
        "Calculate ETA for ordered coordinates.",
        {"coordinates": "list[{latitude:number, longitude:number}]", "dwell_seconds": "integer"},
        eta.calculate_eta,
    ),
    "generate_recommendations": ToolSpec(
        "generate_recommendations",
        "Generate recommendations by comparing current and proposed plans.",
        {"session_id": "uuid", "current_plan_id": "uuid", "proposed_plan_id": "uuid"},
        recommendations.generate_recommendations,
    ),
    "apply_recommendation": ToolSpec(
        "apply_recommendation",
        "Apply an accepted recommendation.",
        {"recommendation_id": "uuid", "session_id": "uuid"},
        recommendations.apply_recommendation,
    ),
    "accept_recommendation": ToolSpec(
        "accept_recommendation",
        "Accept a recommendation without applying it.",
        {"recommendation_id": "uuid", "session_id": "uuid|null"},
        recommendations.accept_recommendation,
    ),
    "reject_recommendation": ToolSpec(
        "reject_recommendation",
        "Reject a recommendation without changing the active plan.",
        {"recommendation_id": "uuid", "reason": "string|null"},
        recommendations.reject_recommendation,
    ),
    "undo_last_change": ToolSpec(
        "undo_last_change",
        "Undo the most recent applied recommendation for a session.",
        {"session_id": "uuid"},
        recommendations.undo_last_change,
    ),
    "get_dispatch_context": ToolSpec(
        "get_dispatch_context",
        "Load the latest backend dispatch memory snapshot.",
        {"session_id": "uuid"},
        memory.get_dispatch_context,
    ),
    "get_recent_conversation": ToolSpec(
        "get_recent_conversation",
        "Load recent conversation history.",
        {"session_id": "uuid", "limit": "integer"},
        memory.get_recent_conversation,
    ),
}


def available_tool_specs() -> list[dict[str, Any]]:
    """Return Gemini-readable tool metadata."""
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "parameters": spec.parameters,
        }
        for spec in TOOL_SPECS.values()
    ]


def execute_tool(tool_name: str, arguments: dict[str, Any]) -> McpResponse:
    """Execute an MCP tool by name."""
    spec = TOOL_SPECS.get(tool_name)
    if spec is None:
        return {"success": False, "error": f"Unknown MCP tool: {tool_name}"}
    return spec.function(**arguments)
