from app.providers.routing import RoutingProvider
from app.providers.types import Coordinate


class EtaService:
    def __init__(self, routing: RoutingProvider) -> None:
        self.routing = routing

    def calculate_eta(self, coordinates: list[Coordinate], dwell_seconds: int = 0) -> dict:
        route = self.routing.route(coordinates)
        return {
            "distance_meters": route.distance_meters,
            "travel_seconds": route.travel_seconds,
            "dwell_seconds": dwell_seconds,
            "schedule_seconds": route.travel_seconds + dwell_seconds,
            "geometry": route.geometry,
        }

