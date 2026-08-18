from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.hospital import HospitalInfo
from app.schemas.route import RouteResponse
from app.schemas.weather import WeatherData
from app.schemas.road_condition import RoadConditionResponse

class HospitalRecommendationRequest(BaseModel):
    latitude: float = Field(..., description="Current latitude of the patient/caller", examples=[22.729189])
    longitude: float = Field(..., description="Current longitude of the patient/caller", examples=[88.496305])
    radius_meters: Optional[float] = Field(5000.0, description="Hospital search radius in meters", examples=[5000.0])
    max_hospitals_to_evaluate: Optional[int] = Field(5, ge=1, le=10, description="Number of hospitals to evaluate and rank", examples=[5])
    road_image_url: Optional[str] = Field(None, description="Optional current road image URL for visual road scoring")

class ScoreBreakdown(BaseModel):
    duration_score: float = Field(..., description="Normalized score based on travel time (higher is faster)")
    congestion_score: float = Field(..., description="Traffic congestion score (100 = free flow, lower = severe traffic)")
    road_condition_score: float = Field(..., description="Road condition score (0-100)")
    weather_safety_score: float = Field(..., description="Weather safety score (0-100)")
    final_composite_score: float = Field(..., description="Overall composite score (0-100, highest recommended)")

class ScoredHospitalRoute(BaseModel):
    rank: int = Field(..., description="Recommendation ranking (1 = best recommended hospital)")
    hospital: HospitalInfo
    route: RouteResponse
    weather: WeatherData
    road_condition: Optional[RoadConditionResponse] = None
    scores: ScoreBreakdown
    recommendation_notes: str = Field(..., description="Summary reasoning for the recommendation")

class HospitalRecommendationResponse(BaseModel):
    origin: dict
    total_evaluated: int
    recommended_hospital: ScoredHospitalRoute
    ranked_hospitals: List[ScoredHospitalRoute]
