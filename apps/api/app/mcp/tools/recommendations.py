from uuid import UUID

from app.mcp.logging import log_tool_call
from app.mcp.responses import McpResponse, fail, ok
from app.mcp.serializers import serialize


@log_tool_call("generate_recommendations")
def generate_recommendations(session_id: str, current_plan_id: str, proposed_plan_id: str) -> McpResponse:
    """Generate recommendations by comparing current and proposed plans."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            recommendation = services.recommendations.generate_for_plans(
                session_id=UUID(session_id),
                current_plan_id=UUID(current_plan_id),
                proposed_plan_id=UUID(proposed_plan_id),
            )
        if recommendation is None:
            return ok("No better recommendation found.", {"recommendation": None})
        return ok("Recommendation generated.", {"recommendation": serialize(recommendation)})
    except Exception as exc:
        return fail(str(exc))


@log_tool_call("apply_recommendation")
def apply_recommendation(recommendation_id: str, session_id: str) -> McpResponse:
    """Apply an accepted recommendation."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            recommendation = services.recommendations.apply(
                recommendation_id=UUID(recommendation_id),
                session_id=UUID(session_id),
            )
        return ok("Recommendation applied.", {"recommendation": serialize(recommendation)})
    except Exception as exc:
        return fail(str(exc))


@log_tool_call("accept_recommendation")
def accept_recommendation(recommendation_id: str, session_id: str | None = None) -> McpResponse:
    """Accept a recommendation without applying it."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            recommendation = services.recommendations.accept(
                recommendation_id=UUID(recommendation_id),
                session_id=UUID(session_id) if session_id else None,
            )
        return ok("Recommendation accepted.", {"recommendation": serialize(recommendation)})
    except Exception as exc:
        return fail(str(exc))


@log_tool_call("reject_recommendation")
def reject_recommendation(recommendation_id: str, reason: str | None = None) -> McpResponse:
    """Reject a recommendation without changing the active plan."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            recommendation = services.recommendations.reject(UUID(recommendation_id), reason=reason)
        return ok("Recommendation rejected.", {"recommendation": serialize(recommendation)})
    except Exception as exc:
        return fail(str(exc))


@log_tool_call("undo_last_change")
def undo_last_change(session_id: str) -> McpResponse:
    """Undo the most recent applied recommendation for a session."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            recommendation = services.recommendations.undo_last_applied(UUID(session_id))
        return ok("Last applied recommendation undone.", {"recommendation": serialize(recommendation)})
    except Exception as exc:
        return fail(str(exc))


def register(mcp) -> None:
    for tool in [
        generate_recommendations,
        accept_recommendation,
        apply_recommendation,
        reject_recommendation,
        undo_last_change,
    ]:
        mcp.tool()(tool)
