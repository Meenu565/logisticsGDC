from typing import Protocol

from app.providers.types import Coordinate, TrafficEstimate


class TrafficProvider(Protocol):
    def estimate(self, origin: Coordinate, destination: Coordinate) -> TrafficEstimate:
        """Return traffic multiplier for a route leg."""

