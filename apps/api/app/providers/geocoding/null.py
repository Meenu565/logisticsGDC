from app.providers.geocoding.base import GeocodingProvider
from app.providers.types import GeocodeResult


class NullGeocodingProvider(GeocodingProvider):
    def geocode(self, address: str) -> GeocodeResult | None:
        return None

