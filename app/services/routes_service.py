import logging
from typing import Dict, Any, Optional, List, Tuple
import requests
import polyline
from app.core.config import settings
from app.core.exceptions import ExternalAPIError, ResourceNotFoundError

logger = logging.getLogger(__name__)

def decode_polyline(encoded_polyline: str) -> List[Tuple[float, float]]:
    """Decode a Google encoded polyline string into a list of (lat, lon) tuples."""
    try:
        return polyline.decode(encoded_polyline)
    except Exception as e:
        logger.error(f"Failed to decode polyline: {e}")
        return []

class RoutesService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        self.routes_url = "https://routes.googleapis.com/directions/v2:computeRoutes"

    def compute_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        travel_mode: str = "DRIVE",
        include_polyline_points: bool = True
    ) -> Dict[str, Any]:
        """Compute directions and real-time traffic duration between two coordinates using Google Routes API."""
        if not self.api_key:
            raise ExternalAPIError(
                service_name="Google Routes API",
                message="Google Maps API key is not configured.",
                status_code=500
            )

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "routes.duration,routes.staticDuration,routes.distanceMeters,routes.polyline.encodedPolyline"
            )
        }
        data = {
            "origin": {
                "location": {
                    "latLng": {
                        "latitude": origin_lat,
                        "longitude": origin_lon
                    }
                }
            },
            "destination": {
                "location": {
                    "latLng": {
                        "latitude": dest_lat,
                        "longitude": dest_lon
                    }
                }
            },
            "travelMode": travel_mode,
            "routingPreference": "TRAFFIC_AWARE",
            "computeAlternativeRoutes": False
        }

        try:
            response = requests.post(self.routes_url, headers=headers, json=data, timeout=12)
        except requests.exceptions.Timeout:
            raise ExternalAPIError(
                service_name="Google Routes API",
                message="Request timed out while connecting to Google Routes API.",
                status_code=504
            )
        except requests.exceptions.RequestException as e:
            raise ExternalAPIError(
                service_name="Google Routes API",
                message=f"Network error connecting to Google Routes API: {str(e)}",
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

            logger.error(f"Google Routes API error: {err_msg} (Status: {response.status_code})")
            raise ExternalAPIError(
                service_name="Google Routes API",
                message=err_msg,
                status_code=502,
                upstream_status_code=response.status_code,
                details=err_details
            )

        routes = response.json().get("routes", [])
        if not routes:
            raise ResourceNotFoundError(
                resource_name="Route",
                message=f"No driving route found between coordinates ({origin_lat}, {origin_lon}) and ({dest_lat}, {dest_lon})."
            )

        sorted_routes = sorted(routes, key=lambda x: x.get("distanceMeters", float("inf")))
        best_route = sorted_routes[0]
        distance_meters = float(best_route.get("distanceMeters", 0))

        # duration strings formatted like "600s"
        static_raw = best_route.get("staticDuration", "0s").rstrip("s")
        dur_raw = best_route.get("duration", "0s").rstrip("s")

        static_duration = round(float(static_raw) / 60.0, 2)
        duration = round(float(dur_raw) / 60.0, 2)

        congestion_ratio = round(duration / static_duration, 2) if static_duration > 0 else 1.0
        encoded_polyline = best_route.get("polyline", {}).get("encodedPolyline", "")

        lane_coords = decode_polyline(encoded_polyline) if (include_polyline_points and encoded_polyline) else []

        return {
            "distance_meters": distance_meters,
            "distance_km": round(distance_meters / 1000.0, 2),
            "static_duration_minutes": static_duration,
            "duration_minutes": duration,
            "congestion_ratio": congestion_ratio,
            "encoded_polyline": encoded_polyline,
            "lane_coordinates": lane_coords if include_polyline_points else None
        }

routes_service = RoutesService()
