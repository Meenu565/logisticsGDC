from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import ServiceBundle, get_services
from app.mcp.serializers import serialize

router = APIRouter(prefix="/timeline")


@router.get("/{session_id}")
def timeline(session_id: UUID, services: ServiceBundle = Depends(get_services)) -> dict:
    return {"success": True, "data": {"events": serialize(services.events.timeline(session_id))}}

