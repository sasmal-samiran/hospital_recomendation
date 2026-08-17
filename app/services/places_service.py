import logging
from math import radians, sin, cos, sqrt, atan2
from typing import List, Dict, Any, Optional
import requests
from app.core.config import settings
from app.core.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in kilometers."""
    R = 6371.0  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(R * c, 3)

class PlacesService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        self.places_url = "https://places.googleapis.com/v1/places:searchNearby"

    def search_nearby_hospitals(
        self,
        lat: float,
        lon: float,
        radius_meters: float = 5000.0,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for nearby hospitals within a radius in meters using Google Places API."""
        if not self.api_key:
            raise ExternalAPIError(
                service_name="Google Places API",
                message="Google Maps API key is not configured.",
                status_code=500
            )

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.displayName,places.location,places.formattedAddress"
        }
        data = {
            "includedTypes": ["hospital"],
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lon
                    },
                    "radius": float(radius_meters)
                }
            }
        }

        try:
            response = requests.post(self.places_url, headers=headers, json=data, timeout=12)
        except requests.exceptions.Timeout:
            raise ExternalAPIError(
                service_name="Google Places API",
                message="Request timed out while connecting to Google Places API.",
                status_code=504
            )
        except requests.exceptions.RequestException as e:
            raise ExternalAPIError(
                service_name="Google Places API",
                message=f"Network error connecting to Google Places API: {str(e)}",
                status_code=502
            )

        if response.status_code != 200:
            err_msg = f"HTTP {response.status_code}"
            err_details = None
            try:
                err_json = response.json()
                err_msg = err_json.get("error", {}).get("message", response.text)
                err_details = err_json.get("error")
            except Exception:
                err_msg = response.text or f"HTTP {response.status_code}"

            logger.error(f"Google Places API error: {err_msg} (Status: {response.status_code})")
            raise ExternalAPIError(
                service_name="Google Places API",
                message=err_msg,
                status_code=502,
                upstream_status_code=response.status_code,
                details=err_details
            )

        places_data = response.json().get("places", [])
        result = []
        for item in places_data:
            display_name = item.get("displayName", {}).get("text", "Unknown Hospital")
            loc = item.get("location", {})
            dlat = loc.get("latitude")
            dlon = loc.get("longitude")
            address = item.get("formattedAddress")

            if dlat is not None and dlon is not None:
                dist = haversine(lat, lon, dlat, dlon)
                result.append({
                    "name": display_name,
                    "lat": dlat,
                    "lon": dlon,
                    "formatted_address": address,
                    "distance_km": dist
                })

        # Sort by proximity
        result = sorted(result, key=lambda x: x["distance_km"])
        return result[:limit]

places_service = PlacesService()
