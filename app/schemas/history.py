from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SaveHistoryRequest(BaseModel):
    origin_lat: float = Field(..., description="Origin latitude", examples=[22.729189])
    origin_lon: float = Field(..., description="Origin longitude", examples=[88.496305])
    radius_meters: float = Field(..., description="Radius in meters", examples=[5000.0])
    recommended_hospital_name: str = Field(..., description="Name of recommended hospital")
    recommended_hospital_distance_km: float = Field(..., description="Distance in km")
    recommended_hospital_duration_min: float = Field(..., description="Duration in minutes")
    composite_score: float = Field(..., description="Composite score (0-100)")
    weather_condition: str = Field(..., description="Weather condition (e.g. Clear, Rain)")
    road_condition_label: str = Field(..., description="Road surface condition label")
    total_evaluated: int = Field(..., description="Number of hospitals evaluated")
    raw_result: Dict[str, Any] = Field(..., description="Full recommendation result object")

class HistoryItemResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    timestamp: str
    origin_lat: float
    origin_lon: float
    radius_meters: float
    recommended_hospital_name: str
    recommended_hospital_distance_km: Optional[float] = None
    recommended_hospital_duration_min: Optional[float] = None
    composite_score: float
    weather_condition: Optional[str] = None
    road_condition_label: Optional[str] = None
    total_evaluated: int
    raw_result: Optional[Dict[str, Any]] = None

class HistoryListResponse(BaseModel):
    total_count: int
    items: List[HistoryItemResponse]
