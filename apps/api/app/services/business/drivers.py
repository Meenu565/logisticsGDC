from uuid import UUID

from app.models import Driver, DriverVehicleAssignment, Vehicle
from app.models.enums import DriverStatus
from app.repositories.drivers import DriverRepository, VehicleRepository
from app.services.business.events import DispatchEventService


class DriverService:
    def __init__(
        self,
        drivers: DriverRepository,
        vehicles: VehicleRepository,
        events: DispatchEventService | None = None,
    ) -> None:
        self.drivers = drivers
        self.vehicles = vehicles
        self.events = events

    def list_drivers(self) -> list[Driver]:
        return list(self.drivers.list_all())

    def available_drivers(self) -> list[Driver]:
        return list(self.drivers.list_eligible_for_planning())

    def driver_status(self, driver_id: UUID) -> DriverStatus:
        driver = self.drivers.get(driver_id)
        if driver is None:
            raise ValueError(f"Driver not found: {driver_id}")
        return driver.status

    def assign_vehicle(
        self,
        driver_id: UUID,
        vehicle_id: UUID,
        session_id: UUID | None = None,
    ) -> DriverVehicleAssignment:
        assignment = self.drivers.assign_vehicle(driver_id, vehicle_id)
        if self.events:
            self.events.record(
                event_type="vehicle_assigned",
                title="Vehicle assigned to driver",
                details={"assignment_id": str(assignment.id)},
                session_id=session_id,
                driver_id=driver_id,
                vehicle_id=vehicle_id,
            )
        return assignment

    def list_available_vehicles(self) -> list[Vehicle]:
        return list(self.vehicles.list_available())
