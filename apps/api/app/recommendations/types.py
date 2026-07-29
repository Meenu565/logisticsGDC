from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class PlanMetrics:
    plan_id: UUID | None
    total_distance_meters: int
    total_travel_seconds: int
    total_dwell_seconds: int

    @property
    def total_schedule_seconds(self) -> int:
        return self.total_travel_seconds + self.total_dwell_seconds


@dataclass(frozen=True)
class RecommendationDraft:
    title: str
    reason: str
    current_plan_id: UUID | None
    proposed_plan_id: UUID | None
    time_saved_seconds: int
    distance_saved_meters: int
    operational_benefits: list[str] = field(default_factory=list)
    affected_order_id: UUID | None = None
    from_driver_id: UUID | None = None
    to_driver_id: UUID | None = None
    rejection_fingerprint: str | None = None

