from uuid import UUID

from app.models import Assignment
from app.repositories.routes import AssignmentRepository
from app.services.business.events import DispatchEventService


class DriverAssignmentService:
    def __init__(
        self,
        assignments: AssignmentRepository,
        events: DispatchEventService | None = None,
    ) -> None:
        self.assignments = assignments
        self.events = events

    def assign_driver(
        self,
        plan_id: UUID,
        order_id: UUID,
        driver_id: UUID,
        vehicle_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> Assignment:
        assignment = self.assignments.get_for_plan_order(plan_id, order_id)
        if assignment is None:
            assignment = Assignment(plan_id=plan_id, order_id=order_id)
        assignment.driver_id = driver_id
        assignment.vehicle_id = vehicle_id
        self.assignments.add(assignment)
        if self.events:
            self.events.record(
                event_type="driver_assigned",
                title="Driver assigned to order",
                details={"assignment_id": str(assignment.id)},
                session_id=session_id,
                plan_id=plan_id,
                order_id=order_id,
                driver_id=driver_id,
                vehicle_id=vehicle_id,
            )
        return assignment

