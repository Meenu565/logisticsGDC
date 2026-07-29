from typing import Protocol

from app.providers.types import GeocodeResult


class GeocodingProvider(Protocol):
    def geocode(self, address: str) -> GeocodeResult | None:
        """Return coordinates for an address, or None when not found."""

