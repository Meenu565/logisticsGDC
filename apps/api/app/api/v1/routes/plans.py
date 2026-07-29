from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import ServiceBundle, get_services
from app.mcp.serializers import serialize

router = APIRouter(prefix="/plans")


@router.post("/optimize")
def optimize_routes(
    session_id: UUID,
    route_date: date,
    order_ids: list[UUID] | None = None,
    services: ServiceBundle = Depends(get_services),
) -> dict:
    plan = services.planning.optimize_routes(session_id, route_date, order_ids)
    services.db.commit()
    return {"success": True, "data": {"plan": serialize(plan)}}


@router.get("/{plan_id}/summary")
def summarize_plan(plan_id: UUID, services: ServiceBundle = Depends(get_services)) -> dict:
    return {"success": True, "data": {"summary": serialize(services.routes.route_summary(plan_id))}}
