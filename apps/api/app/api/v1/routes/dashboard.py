from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import ServiceBundle, get_services
from app.mcp.serializers import serialize

router = APIRouter(prefix="/dashboard")


@router.get("/{session_id}")
def dashboard_state(session_id: UUID, services: ServiceBundle = Depends(get_services)) -> dict:
    return {"success": True, "data": serialize(services.dashboard.state(session_id))}

