from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import ServiceBundle, get_services
from app.mcp.serializers import serialize

router = APIRouter(prefix="/drivers")


@router.get("")
def list_drivers(services: ServiceBundle = Depends(get_services)) -> dict:
    return {"success": True, "data": {"drivers": serialize(services.drivers.list_drivers())}}


@router.get("/available")
def list_available_drivers(services: ServiceBundle = Depends(get_services)) -> dict:
    return {"success": True, "data": {"drivers": serialize(services.drivers.available_drivers())}}


@router.get("/{driver_id}/status")
def get_driver_status(driver_id: UUID, services: ServiceBundle = Depends(get_services)) -> dict:
    return {"success": True, "data": {"status": serialize(services.drivers.driver_status(driver_id))}}

