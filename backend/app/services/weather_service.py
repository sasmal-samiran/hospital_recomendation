import logging
from typing import Dict, Any, Optional, List, Tuple
import requests
from app.core.config import settings
from app.core.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)

def calculate_weather_safety_score(weather_data: Dict[str, Any]) -> float:
    """
    Calculate safety score (0-100) based on weather hazards.
    100 = Clear, dry, high visibility.
    Lower score = Poor visibility, heavy rain, extreme winds, etc.
    """
    score = 100.0
    main_condition = str(weather_data.get("weather_main", "")).lower()
    rain = weather_data.get("rain_1h_mm")
    visibility = weather_data.get("visibility_meters", 10000)
    wind_speed = weather_data.get("wind_speed_mps", 0)

    # Condition penalties
    if "thunderstorm" in main_condition or "storm" in main_condition:
        score -= 40.0
    elif "snow" in main_condition or "ice" in main_condition:
        score -= 35.0
    elif "rain" in main_condition or "drizzle" in main_condition:
        score -= 20.0
    elif "fog" in main_condition or "mist" in main_condition or "haze" in main_condition:
        score -= 15.0

    # Rain volume penalty
    if rain is not None:
        if rain > 10.0:
            score -= 25.0
        elif rain > 2.5:
            score -= 10.0

    # Visibility penalty (meters)
    if visibility < 1000:
        score -= 25.0
    elif visibility < 3000:
        score -= 10.0

    # Wind speed penalty (m/s)
    if wind_speed > 15.0:
        score -= 15.0
    elif wind_speed > 8.0:
        score -= 5.0

    return max(0.0, min(100.0, round(score, 1)))

class WeatherService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENWEATHER_API_KEY
        self.weather_url = "https://api.openweathermap.org/data/2.5/weather"

    def get_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch current weather data at specific coordinates from OpenWeatherMap API."""
        if not self.api_key:
            raise ExternalAPIError(
                service_name="OpenWeatherMap API",
                message="OpenWeather API key is not configured.",
                status_code=500
            )

        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }
        try:
            response = requests.get(self.weather_url, params=params, timeout=10)
        except requests.exceptions.Timeout:
            raise ExternalAPIError(
                service_name="OpenWeatherMap API",
                message="Request timed out while connecting to OpenWeatherMap API.",
                status_code=504
            )
        except requests.exceptions.RequestException as e:
            raise ExternalAPIError(
                service_name="OpenWeatherMap API",
                message=f"Network error connecting to OpenWeatherMap API: {str(e)}",
                status_code=502
            )

        if response.status_code != 200:
            err_msg = f"HTTP {response.status_code}"
            err_details = None
            try:
                err_json = response.json()
                err_msg = err_json.get("message", response.text)
                err_details = err_json
            except Exception:
                err_msg = response.text or f"HTTP {response.status_code}"

            logger.error(f"OpenWeather API error: {err_msg} (Status: {response.status_code})")
            raise ExternalAPIError(
                service_name="OpenWeatherMap API",
                message=err_msg,
                status_code=502,
                upstream_status_code=response.status_code,
                details=err_details
            )

        data = response.json()
        rain_dict = data.get("rain", {})
        rain_1h = rain_dict.get("1h") if isinstance(rain_dict, dict) else None

        weather_list = data.get("weather", [])
        weather_main = weather_list[0].get("main", "Clear") if weather_list else "Clear"
        weather_desc = weather_list[0].get("description", "clear sky") if weather_list else "clear sky"

        result = {
            "temperature_celsius": round(float(data.get("main", {}).get("temp", 25.0)), 1),
            "humidity_percent": int(data.get("main", {}).get("humidity", 50)),
            "pressure_hpa": int(data.get("main", {}).get("pressure", 1013)),
            "wind_speed_mps": round(float(data.get("wind", {}).get("speed", 2.0)), 1),
            "visibility_meters": int(data.get("visibility", 10000)),
            "weather_main": weather_main,
            "weather_description": weather_desc,
            "rain_1h_mm": rain_1h
        }
        result["safety_penalty_score"] = calculate_weather_safety_score(result)
        return result

    def get_weather_along_route(
        self,
        waypoints: List[Tuple[float, float]],
        sample_count: int = 3
    ) -> Dict[str, Any]:
        """Sample weather at several points along a route polyline."""
        if not waypoints:
            raise ExternalAPIError(
                service_name="Weather Service",
                message="No route coordinates provided for route weather sampling.",
                status_code=400
            )

        total = len(waypoints)
        count = min(sample_count, total)
        step = max(1, total // count)
        sampled_points = [waypoints[i * step] for i in range(count)]
        if waypoints[-1] not in sampled_points:
            sampled_points.append(waypoints[-1])

        samples = []
        for lat, lon in sampled_points:
            w = self.get_weather(lat, lon)
            samples.append(w)

        avg_temp = round(sum(s["temperature_celsius"] for s in samples) / len(samples), 1)
        rain_values = [s["rain_1h_mm"] for s in samples if s["rain_1h_mm"] is not None]
        is_rainy = round(sum(rain_values) / len(rain_values), 2) if rain_values else 0.0
        avg_safety = round(sum(s["safety_penalty_score"] for s in samples) / len(samples), 1)

        return {
            "samples": samples,
            "average_temperature": avg_temp,
            "is_rainy": is_rainy,
            "overall_weather_safety_score": avg_safety
        }

weather_service = WeatherService()
