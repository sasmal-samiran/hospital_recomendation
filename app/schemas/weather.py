from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

class WeatherData(BaseModel):
    temperature_celsius: float = Field(..., description="Temperature in Celsius")
    humidity_percent: int = Field(..., description="Humidity percentage (0-100)")
    pressure_hpa: int = Field(..., description="Atmospheric pressure in hPa")
    wind_speed_mps: float = Field(..., description="Wind speed in meters/second")
    visibility_meters: int = Field(..., description="Visibility in meters")
    weather_main: str = Field(..., description="Main weather condition (e.g. Clear, Rain, Fog)")
    weather_description: str = Field(..., description="Detailed description")
    rain_1h_mm: Optional[float] = Field(None, description="Rain volume in last 1 hour in mm")
    safety_penalty_score: float = Field(
        100.0, description="Calculated weather safety score (100 = optimal/clear, lower = severe/unsafe weather)"
    )

class WeatherRequest(BaseModel):
    latitude: float = Field(..., examples=[22.729189])
    longitude: float = Field(..., examples=[88.496305])

class RouteWeatherRequest(BaseModel):
    waypoints: List[Tuple[float, float]] = Field(
        ..., description="List of (lat, lon) coordinates along the route to sample weather"
    )
    sample_count: Optional[int] = Field(5, ge=1, le=10, description="Number of evenly spaced points along route to check")

class RouteWeatherResponse(BaseModel):
    samples: List[WeatherData]
    average_temperature: float
    is_rainy: bool
    overall_weather_safety_score: float
