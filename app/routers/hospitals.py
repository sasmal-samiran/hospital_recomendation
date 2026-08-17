from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.hospital import (
    HospitalSearchRequest,
    HospitalSearchResponse,
    HospitalInfo,
    HospitalLocation
)
from app.services.places_service import places_service

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])

@router.get("/nearby", response_model=HospitalSearchResponse, summary="Find nearby hospitals by coordinates")
def get_nearby_hospitals(
    lat: float = Query(..., description="Latitude of user/patient location", examples=[22.729189], ge=-90.0, le=90.0),
    lon: float = Query(..., description="Longitude of user/patient location", examples=[88.496305], ge=-180.0, le=180.0),
    radius: Optional[float] = Query(5000.0, description="Search radius in meters", examples=[5000.0], gt=0),
    limit: Optional[int] = Query(5, ge=1, le=20, description="Max hospitals to return", examples=[5])
):
    """
    Search for hospitals within a specified radius (in meters) from the user's current GPS location.
    Results are sorted by distance from the coordinates.
    """
    hospitals_data = places_service.search_nearby_hospitals(
        lat=lat,
        lon=lon,
        radius_meters=radius or 5000.0,
        limit=limit or 5
    )
    return HospitalSearchResponse(
        origin=HospitalLocation(latitude=lat, longitude=lon),
        total_found=len(hospitals_data),
        hospitals=[HospitalInfo(**h) for h in hospitals_data]
    )

@router.post("/search", response_model=HospitalSearchResponse, summary="Search hospitals using request body")
def search_hospitals(payload: HospitalSearchRequest):
    """
    Search nearby hospitals by sending latitude and longitude in a JSON payload.
    """
    hospitals_data = places_service.search_nearby_hospitals(
        lat=payload.latitude,
        lon=payload.longitude,
        radius_meters=payload.radius_meters or 5000.0,
        limit=payload.limit or 5
    )
    return HospitalSearchResponse(
        origin=HospitalLocation(latitude=payload.latitude, longitude=payload.longitude),
        total_found=len(hospitals_data),
        hospitals=[HospitalInfo(**h) for h in hospitals_data]
    )
