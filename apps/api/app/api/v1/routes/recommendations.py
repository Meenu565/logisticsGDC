from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import ServiceBundle, get_services
from app.mcp.serializers import serialize

router = APIRouter(prefix="/recommendations")


@router.get("/session/{session_id}")
def list_recommendations(session_id: UUID, services: ServiceBundle = Depends(get_services)) -> dict:
    return {"success": True, "data": {"recommendations": serialize(services.recommendations.list_for_session(session_id))}}


@router.post("/generate")
def generate_recommendation(
    session_id: UUID,
    current_plan_id: UUID,
    proposed_plan_id: UUID,
    services: ServiceBundle = Depends(get_services),
) -> dict:
    recommendation = services.recommendations.generate_for_plans(session_id, current_plan_id, proposed_plan_id)
    services.db.commit()
    return {"success": True, "data": {"recommendation": serialize(recommendation)}}


@router.post("/{recommendation_id}/accept")
def accept_recommendation(
    recommendation_id: UUID,
    session_id: UUID | None = None,
    services: ServiceBundle = Depends(get_services),
) -> dict:
    recommendation = services.recommendations.accept(recommendation_id, session_id=session_id)
    services.db.commit()
    return {"success": True, "data": {"recommendation": serialize(recommendation)}}


@router.post("/{recommendation_id}/apply")
def apply_recommendation(
    recommendation_id: UUID,
    session_id: UUID,
    services: ServiceBundle = Depends(get_services),
) -> dict:
    recommendation = services.recommendations.apply(recommendation_id, session_id)
    services.db.commit()
    return {
        "success": True,
        "data": {
            "recommendation": serialize(recommendation),
            "dashboard": serialize(services.dashboard.state(session_id)),
        },
    }


@router.post("/{recommendation_id}/reject")
def reject_recommendation(
    recommendation_id: UUID,
    reason: str | None = None,
    services: ServiceBundle = Depends(get_services),
) -> dict:
    recommendation = services.recommendations.reject(recommendation_id, reason=reason)
    services.db.commit()
    return {"success": True, "data": {"recommendation": serialize(recommendation)}}


@router.post("/session/{session_id}/undo")
def undo_last_change(session_id: UUID, services: ServiceBundle = Depends(get_services)) -> dict:
    recommendation = services.recommendations.undo_last_applied(session_id)
    services.db.commit()
    return {
        "success": True,
        "data": {
            "recommendation": serialize(recommendation),
            "dashboard": serialize(services.dashboard.state(session_id)),
        },
    }

