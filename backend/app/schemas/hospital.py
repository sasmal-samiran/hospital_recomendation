from typing import List, Optional
from pydantic import BaseModel, Field

class HospitalLocation(BaseModel):
    latitude: float = Field(..., description="Latitude of hospital")
    longitude: float = Field(..., description="Longitude of hospital")

class HospitalInfo(BaseModel):
    name: str = Field(..., description="Hospital Name")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    formatted_address: Optional[str] = Field(None, description="Formatted street address if available")
    distance_km: Optional[float] = Field(None, description="Straight line distance in km from search origin")

class HospitalSearchRequest(BaseModel):
    latitude: float = Field(..., description="Current latitude of user/origin", examples=[22.729189])
    longitude: float = Field(..., description="Current longitude of user/origin", examples=[88.496305])
    radius_meters: Optional[float] = Field(5000.0, description="Search radius in meters", examples=[5000.0])
    limit: Optional[int] = Field(5, ge=1, le=20, description="Maximum number of nearby hospitals to return", examples=[5])

class HospitalSearchResponse(BaseModel):
    origin: HospitalLocation
    total_found: int
    hospitals: List[HospitalInfo]
