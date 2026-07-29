from typing import Protocol

from app.providers.types import Coordinate, RouteMatrix, RouteResult


class RoutingProvider(Protocol):
    def route(self, coordinates: list[Coordinate]) -> RouteResult:
        """Return route metrics and optional geometry for ordered coordinates."""

    def matrix(self, coordinates: list[Coordinate]) -> RouteMatrix:
        """Return all-pairs travel distance and duration."""

