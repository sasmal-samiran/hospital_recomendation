import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Hospital Route Finding API"
    PROJECT_DESCRIPTION: str = (
        "FastAPI service for finding hospitals and calculating optimal emergency routes "
        "factoring in road conditions, weather, traffic congestion, and road quality scores."
    )
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # API Keys (defaults from existing services, can be overridden with env variables)
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyCWu_AOIPvSm6DjvmpuIJTwNdQROPO-DrA")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "d0cc7592f738b79121a8dd0c4c53317b")

    # Defaults
    DEFAULT_HOSPITAL_RADIUS_METERS: float = 5000.0
    DEFAULT_MAX_HOSPITALS: int = 5
    
    # Recommendation weights (must sum to ~1.0)
    WEIGHT_DURATION: float = 0.40      # Faster arrival time is critical
    WEIGHT_CONGESTION: float = 0.25    # Less traffic congestion
    WEIGHT_ROAD_SCORE: float = 0.20    # Better road surface quality
    WEIGHT_WEATHER: float = 0.15       # Safer weather conditions

settings = Settings()
