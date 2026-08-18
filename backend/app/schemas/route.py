from typing import List, Tuple, Optional
from pydantic import BaseModel, Field

class Coordinates(BaseModel):
    latitude: float = Field(..., examples=[22.729189])
    longitude: float = Field(..., examples=[88.496305])

class RouteRequest(BaseModel):
    origin_lat: float = Field(..., description="Origin latitude", examples=[22.729189])
    origin_lon: float = Field(..., description="Origin longitude", examples=[88.496305])
    dest_lat: float = Field(..., description="Destination latitude (e.g. hospital)", examples=[22.74001])
    dest_lon: float = Field(..., description="Destination longitude", examples=[88.51002])
    travel_mode: Optional[str] = Field("DRIVE", description="Travel mode (e.g. DRIVE, TWO_WHEELER)")
    include_polyline_points: Optional[bool] = Field(True, description="Whether to include decoded coordinate points")

class RouteResponse(BaseModel):
    distance_meters: float = Field(..., description="Route distance in meters")
    distance_km: float = Field(..., description="Route distance in kilometers")
    static_duration_minutes: float = Field(..., description="Duration in minutes without traffic")
    duration_minutes: float = Field(..., description="Real-time duration in minutes with traffic")
    congestion_ratio: float = Field(..., description="Ratio of duration to static duration (1.0 = normal, >1.3 = congested)")
    encoded_polyline: Optional[str] = Field(None, description="Google encoded polyline string")
    lane_coordinates: Optional[List[Tuple[float, float]]] = Field(
        None, description="Decoded list of (latitude, longitude) waypoints along the route"
    )
