from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PlanningStop:
    order_id: UUID
    stop_id: UUID
    weight_kg: float
    volume_m3: float
    latitude: float
    longitude: float
    dwell_seconds: int
    priority: int = 0
    earliest_at: datetime | None = None
    latest_at: datetime | None = None


@dataclass(frozen=True)
class PlanningDriver:
    driver_id: UUID
    vehicle_id: UUID | None
    start_latitude: float
    start_longitude: float
    max_weight_kg: float | None = None
    max_volume_m3: float | None = None
    shift_start: datetime | None = None
    shift_end: datetime | None = None


@dataclass(frozen=True)
class PlannedRouteStop:
    stop_id: UUID
    order_id: UUID
    sequence_number: int
    travel_seconds_from_previous: int
    distance_meters_from_previous: int
    dwell_seconds: int


@dataclass(frozen=True)
class PlannedRoute:
    driver_id: UUID
    vehicle_id: UUID | None
    stops: list[PlannedRouteStop]
    distance_meters: int
    travel_seconds: int
    dwell_seconds: int


@dataclass(frozen=True)
class OptimizationResult:
    routes: list[PlannedRoute]
    total_distance_meters: int
    total_travel_seconds: int
    total_dwell_seconds: int
    unassigned_stop_ids: list[UUID] = field(default_factory=list)
    engine: str = "ortools"

