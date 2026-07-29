from uuid import UUID

from app.models import DispatchEvent
from app.repositories.events import DispatchEventRepository


class DispatchEventService:
    def __init__(self, events: DispatchEventRepository) -> None:
        self.events = events

    def record(
        self,
        event_type: str,
        title: str,
        details: dict | None = None,
        session_id: UUID | None = None,
        plan_id: UUID | None = None,
        order_id: UUID | None = None,
        driver_id: UUID | None = None,
        vehicle_id: UUID | None = None,
        recommendation_id: UUID | None = None,
    ) -> DispatchEvent:
        return self.events.add(
            DispatchEvent(
                session_id=session_id,
                plan_id=plan_id,
                order_id=order_id,
                driver_id=driver_id,
                vehicle_id=vehicle_id,
                recommendation_id=recommendation_id,
                event_type=event_type,
                title=title,
                details=details or {},
            )
        )

