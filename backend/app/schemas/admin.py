from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.auth import UserProfileResponse

class AdminStatsResponse(BaseModel):
    total_users: int
    total_admins: int
    total_recommendations: int
    average_composite_score: float
    average_arrival_duration_min: float
    database_engine: str
    system_status: str

class UpdateUserRoleRequest(BaseModel):
    role: str = Field(..., description="Role ('user' or 'admin')", examples=["admin"])

class AdminLogItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
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

class AdminLogsResponse(BaseModel):
    total_count: int
    logs: List[AdminLogItem]

class AdminUsersResponse(BaseModel):
    total_count: int
    users: List[UserProfileResponse]
