from app.providers.traffic.base import TrafficProvider
from app.providers.types import Coordinate, TrafficEstimate


class NullTrafficProvider(TrafficProvider):
    def estimate(self, origin: Coordinate, destination: Coordinate) -> TrafficEstimate:
        return TrafficEstimate(multiplier=1.0, reason="No traffic provider configured.")

