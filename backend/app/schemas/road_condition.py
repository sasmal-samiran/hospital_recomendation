from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class RoadConditionUrlRequest(BaseModel):
    image_url: str = Field(..., description="Public image URL of the road segment", examples=["https://example.com/road.jpg"])

class RoadConditionEstimateRequest(BaseModel):
    weather_safety: Optional[float] = Field(90.0, description="Current weather safety score")
    congestion_ratio: Optional[float] = Field(1.0, description="Congestion ratio")
    is_highway: Optional[bool] = Field(True, description="Whether route is primarily highway")

class RoadConditionResponse(BaseModel):
    condition_label: str = Field(..., description="Classified road condition text", examples=["a smooth asphalt road"])
    road_score: int = Field(..., description="Road condition score from 0 to 100", examples=[98])
    confidence_percent: float = Field(..., description="Model classification confidence percentage", examples=[94.5])
    category: str = Field(..., description="Category (Excellent, Good, Moderate, Poor, Dangerous)")
    top_candidates: Optional[List[Dict[str, Any]]] = Field(None, description="Top predicted conditions with probabilities")

class RoadLabelsResponse(BaseModel):
    total_labels: int
    categories: Dict[str, Dict[str, int]]
