from datetime import date
from uuid import UUID

from app.mcp.logging import log_tool_call
from app.mcp.responses import McpResponse, fail, ok
from app.mcp.serializers import serialize


@log_tool_call("optimize_routes")
def optimize_routes(session_id: str, route_date: str, order_ids: list[str] | None = None) -> McpResponse:
    """Build proposed optimization strategies without changing the active plan."""
    try:
        from app.mcp.dependencies import get_mcp_services

        parsed_order_ids = [UUID(order_id) for order_id in order_ids or []] or None
        parsed_session_id = UUID(session_id)
        with get_mcp_services() as services:
            current_plan = services.routes.current_plan(parsed_session_id)
            services.recommendations.expire_open(parsed_session_id)
            strategy_plans = services.planning.optimize_route_strategies(
                session_id=parsed_session_id,
                route_date=date.fromisoformat(route_date),
                order_ids=parsed_order_ids,
            )
            recommendations = []
            for strategy_plan in strategy_plans:
                if strategy_plan.orders_covered <= 0:
                    continue
                recommendations.append(
                    services.recommendations.create_strategy_recommendation(
                        session_id=parsed_session_id,
                        strategy=strategy_plan.strategy,
                        proposed_plan_id=strategy_plan.plan.id,
                        current_plan_id=current_plan.id if current_plan else None,
                        vehicles_used=strategy_plan.vehicles_used,
                        orders_covered=strategy_plan.orders_covered,
                        unassigned_orders=strategy_plan.unassigned_orders,
                        capacity_notes=strategy_plan.capacity_notes,
                        scheduling_notes=strategy_plan.scheduling_notes,
                        pros=strategy_plan.pros,
                        cons=strategy_plan.cons,
                        why_recommended=strategy_plan.why_recommended,
                    )
                )
            strategies = [
                {
                    "strategy": strategy_plan.strategy,
                    "plan": serialize(strategy_plan.plan),
                    "vehicles_used": strategy_plan.vehicles_used,
                    "orders_covered": strategy_plan.orders_covered,
                    "unassigned_orders": strategy_plan.unassigned_orders,
                    "capacity_notes": strategy_plan.capacity_notes,
                    "scheduling_notes": strategy_plan.scheduling_notes,
                    "pros": strategy_plan.pros,
                    "cons": strategy_plan.cons,
                    "why_recommended": strategy_plan.why_recommended,
                }
                for strategy_plan in strategy_plans
            ]
        message = "Optimization strategies generated." if recommendations else "No feasible assignments found."
        return ok(
            message,
            {"strategies": strategies, "recommendations": serialize(recommendations)},
        )
    except Exception as exc:
        return fail(str(exc))


@log_tool_call("rebuild_plan")
def rebuild_plan(session_id: str, route_date: str, order_ids: list[str] | None = None) -> McpResponse:
    """Rebuild a proposed plan after an operational change."""
    try:
        from app.mcp.dependencies import get_mcp_services

        parsed_order_ids = [UUID(order_id) for order_id in order_ids or []] or None
        with get_mcp_services() as services:
            plan = services.planning.optimize_routes(
                session_id=UUID(session_id),
                route_date=date.fromisoformat(route_date),
                order_ids=parsed_order_ids,
            )
        return ok("Plan rebuilt.", {"plan": serialize(plan)})
    except Exception as exc:
        return fail(str(exc))


@log_tool_call("summarize_plan")
def summarize_plan(plan_id: str) -> McpResponse:
    """Summarize route count and metrics for a plan."""
    try:
        from app.mcp.dependencies import get_mcp_services

        with get_mcp_services() as services:
            summary = services.routes.route_summary(UUID(plan_id))
        return ok("Plan summarized.", {"summary": serialize(summary)})
    except Exception as exc:
        return fail(str(exc))


def register(mcp) -> None:
    for tool in [optimize_routes, rebuild_plan, summarize_plan]:
        mcp.tool()(tool)
