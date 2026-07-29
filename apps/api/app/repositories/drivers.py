from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.models import Driver, DriverVehicleAssignment, Vehicle
from app.models.enums import DriverStatus, VehicleStatus
from app.repositories.base import Repository


class DriverRepository(Repository[Driver]):
    model = Driver

    def list_available(self) -> Sequence[Driver]:
        statement = select(Driver).where(Driver.status == DriverStatus.AVAILABLE)
        return self.db.scalars(statement).all()

    def list_eligible_for_planning(self) -> Sequence[Driver]:
        statement = (
            select(Driver)
            .where(
                Driver.status.notin_(
                    [
                        DriverStatus.OFF_SHIFT,
                        DriverStatus.UNAVAILABLE,
                    ]
                )
            )
            .order_by(Driver.display_name.asc())
        )
        return self.db.scalars(statement).all()

    def list_all(self) -> Sequence[Driver]:
        return self.db.scalars(select(Driver).order_by(Driver.display_name.asc())).all()

    def save(self, driver: Driver) -> Driver:
        self.db.add(driver)
        self.db.flush()
        return driver

    def current_vehicle_assignment(self, driver_id: UUID) -> DriverVehicleAssignment | None:
        statement = select(DriverVehicleAssignment).where(
            DriverVehicleAssignment.driver_id == driver_id,
            DriverVehicleAssignment.released_at.is_(None),
        )
        return self.db.scalars(statement).first()

    def assign_vehicle(self, driver_id: UUID, vehicle_id: UUID) -> DriverVehicleAssignment:
        existing = self.current_vehicle_assignment(driver_id)
        if existing:
            existing.released_at = datetime.utcnow()
        assignment = DriverVehicleAssignment(driver_id=driver_id, vehicle_id=vehicle_id)
        self.db.add(assignment)
        self.db.flush()
        return assignment


class VehicleRepository(Repository[Vehicle]):
    model = Vehicle

    def list_available(self) -> Sequence[Vehicle]:
        statement = select(Vehicle).where(Vehicle.status == VehicleStatus.AVAILABLE)
        return self.db.scalars(statement).all()
