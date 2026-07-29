from dataclasses import dataclass, field


@dataclass(frozen=True)
class Coordinate:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class RouteLeg:
    start: Coordinate
    end: Coordinate
    distance_meters: int
    travel_seconds: int


@dataclass(frozen=True)
class RouteMatrix:
    distances_meters: list[list[int]]
    durations_seconds: list[list[int]]


@dataclass(frozen=True)
class RouteResult:
    distance_meters: int
    travel_seconds: int
    geometry: dict = field(default_factory=dict)
    legs: list[RouteLeg] = field(default_factory=list)


@dataclass(frozen=True)
class GeocodeResult:
    query: str
    coordinate: Coordinate
    provider: str
    confidence: float | None = None


@dataclass(frozen=True)
class TrafficEstimate:
    multiplier: float
    reason: str

