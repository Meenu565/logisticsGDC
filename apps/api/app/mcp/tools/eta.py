from app.mcp.logging import log_tool_call
from app.mcp.responses import McpResponse, fail, ok
from app.mcp.serializers import serialize
from app.providers.types import Coordinate


@log_tool_call("calculate_eta")
def calculate_eta(coordinates: list[dict], dwell_seconds: int = 0) -> McpResponse:
    """Calculate ETA for ordered coordinates."""
    try:
        from app.mcp.dependencies import get_mcp_services

        parsed = [
            Coordinate(latitude=float(item["latitude"]), longitude=float(item["longitude"]))
            for item in coordinates
        ]
        with get_mcp_services() as services:
            eta = services.eta.calculate_eta(parsed, dwell_seconds=dwell_seconds)
        return ok("ETA calculated.", serialize(eta))
    except Exception as exc:
        return fail(str(exc))


def register(mcp) -> None:
    mcp.tool()(calculate_eta)
