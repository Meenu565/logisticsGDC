from math import asin, cos, radians, sin, sqrt

from app.providers.routing.base import RoutingProvider
from app.providers.types import Coordinate, RouteLeg, RouteMatrix, RouteResult


class OsrmRoutingProvider(RoutingProvider):
    """OSRM adapter boundary.

    The HTTP integration is intentionally deferred until infrastructure setup.
    For now, this class provides deterministic distance estimates so business
    services can be developed and tested without network access.
    """

    average_speed_kph = 45

    def route(self, coordinates: list[Coordinate]) -> RouteResult:
        if len(coordinates) < 2:
            return RouteResult(distance_meters=0, travel_seconds=0)

        legs: list[RouteLeg] = []
        distance_meters = 0
        travel_seconds = 0
        for start, end in zip(coordinates, coordinates[1:]):
            leg_distance = self._distance_meters(start, end)
            leg_seconds = self._travel_seconds(leg_distance)
            legs.append(
                RouteLeg(
                    start=start,
                    end=end,
                    distance_meters=leg_distance,
                    travel_seconds=leg_seconds,
                )
            )
            distance_meters += leg_distance
            travel_seconds += leg_seconds

        return RouteResult(
            distance_meters=distance_meters,
            travel_seconds=travel_seconds,
            geometry={"type": "LineString", "coordinates": [[c.longitude, c.latitude] for c in coordinates]},
            legs=legs,
        )

    def matrix(self, coordinates: list[Coordinate]) -> RouteMatrix:
        distances: list[list[int]] = []
        durations: list[list[int]] = []
        for origin in coordinates:
            distance_row: list[int] = []
            duration_row: list[int] = []
            for destination in coordinates:
                distance = self._distance_meters(origin, destination)
                distance_row.append(distance)
                duration_row.append(self._travel_seconds(distance))
            distances.append(distance_row)
            durations.append(duration_row)
        return RouteMatrix(distances_meters=distances, durations_seconds=durations)

    def _travel_seconds(self, distance_meters: int) -> int:
        meters_per_second = (self.average_speed_kph * 1000) / 3600
        return round(distance_meters / meters_per_second)

    def _distance_meters(self, start: Coordinate, end: Coordinate) -> int:
        radius_meters = 6_371_000
        lat1 = radians(start.latitude)
        lat2 = radians(end.latitude)
        delta_lat = radians(end.latitude - start.latitude)
        delta_lon = radians(end.longitude - start.longitude)
        haversine = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        return round(radius_meters * 2 * asin(sqrt(haversine)))

