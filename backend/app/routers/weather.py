from fastapi import APIRouter, Query
from app.schemas.weather import (
    WeatherData,
    RouteWeatherRequest,
    RouteWeatherResponse
)
from app.services.weather_service import weather_service

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/current", response_model=WeatherData, summary="Get current weather at location")
def get_current_weather(
    lat: float = Query(..., description="Latitude", examples=[22.729189], ge=-90.0, le=90.0),
    lon: float = Query(..., description="Longitude", examples=[88.496305], ge=-180.0, le=180.0)
):
    """
    Retrieve real-time weather parameters (temperature, rain, humidity, wind, visibility, pressure)
    and computed weather safety penalty score at the given coordinates.
    """
    weather_data = weather_service.get_weather(lat=lat, lon=lon)
    return WeatherData(**weather_data)

@router.post("/along-route", response_model=RouteWeatherResponse, summary="Get weather along route waypoints")
def get_weather_along_route(payload: RouteWeatherRequest):
    """
    Sample weather conditions at multiple coordinates along a route polyline
    to determine if any section of the journey is impacted by storms or rain.
    """
    result = weather_service.get_weather_along_route(
        waypoints=payload.waypoints,
        sample_count=payload.sample_count or 3
    )
    return RouteWeatherResponse(
        samples=[WeatherData(**s) for s in result["samples"]],
        average_temperature=result["average_temperature"],
        is_rainy=result["is_rainy"],
        overall_weather_safety_score=result["overall_weather_safety_score"]
    )
