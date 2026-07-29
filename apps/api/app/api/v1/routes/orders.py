from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.v1.dependencies import ServiceBundle, get_services
from app.mcp.serializers import serialize

router = APIRouter(prefix="/orders")


@router.get("")
def list_orders(services: ServiceBundle = Depends(get_services)) -> dict:
    return {"success": True, "data": {"orders": serialize(services.orders.list_active_orders())}}


@router.get("/{order_id}")
def get_order(order_id: UUID, services: ServiceBundle = Depends(get_services)) -> dict:
    return {"success": True, "data": {"order": serialize(services.orders.get_order(order_id))}}


@router.patch("/{order_id}")
def update_order(order_id: UUID, updates: dict, services: ServiceBundle = Depends(get_services)) -> dict:
    order = services.orders.update_order(order_id, updates)
    services.db.commit()
    return {"success": True, "data": {"order": serialize(order)}}


@router.post("/{order_id}/cancel")
def cancel_order(order_id: UUID, reason: str | None = None, services: ServiceBundle = Depends(get_services)) -> dict:
    order = services.orders.cancel_order(order_id, reason=reason)
    services.db.commit()
    return {"success": True, "data": {"order": serialize(order)}}


@router.post("/import")
async def import_orders(
    file: UploadFile = File(...),
    session_id: UUID | None = None,
    mode: str = "append",
    services: ServiceBundle = Depends(get_services),
) -> dict:
    content = await file.read()
    name = file.filename or "orders"
    import_mode = "replace" if mode == "replace" else "append"
    if import_mode == "replace" and session_id:
        services.sessions.clear_planning_state(session_id)
    if name.lower().endswith(".xlsx"):
        result = services.orders.import_orders_excel(content, file_name=name, session_id=session_id, mode=import_mode)
    else:
        result = services.orders.import_orders_csv(content.decode("utf-8-sig"), file_name=name, session_id=session_id, mode=import_mode)
    services.db.commit()
    return {"success": True, "data": result}
