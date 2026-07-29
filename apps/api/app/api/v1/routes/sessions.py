from fastapi import APIRouter, Depends
from uuid import UUID

from app.api.v1.dependencies import ServiceBundle, get_services
from app.mcp.serializers import serialize

router = APIRouter(prefix="/sessions")


@router.post("")
def create_session(
    title: str = "Dispatch Session",
    services: ServiceBundle = Depends(get_services),
) -> dict:
    session = services.sessions.create_session(title)
    services.db.commit()
    return {"success": True, "data": {"session": serialize(session)}}


@router.post("/{session_id}/reset")
def reset_workspace(session_id: UUID, services: ServiceBundle = Depends(get_services)) -> dict:
    session = services.sessions.reset_workspace(session_id)
    services.db.commit()
    return {
        "success": True,
        "message": "Workspace reset.",
        "data": {
            "session": serialize(session),
            "dashboard": serialize(services.dashboard.state(session_id)),
        },
    }
