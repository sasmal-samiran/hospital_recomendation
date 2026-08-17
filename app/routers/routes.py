from fastapi import APIRouter
from app.schemas.route import RouteRequest, RouteResponse
from app.services.routes_service import routes_service

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.post("/calculate", response_model=RouteResponse, summary="Calculate driving route & congestion")
def calculate_route(payload: RouteRequest):
    """
    Compute driving directions, distance (km & meters), duration with live traffic,
    static duration (free flow), congestion ratio, and decoded coordinates.
    """
    route_data = routes_service.compute_route(
        origin_lat=payload.origin_lat,
        origin_lon=payload.origin_lon,
        dest_lat=payload.dest_lat,
        dest_lon=payload.dest_lon,
        travel_mode=payload.travel_mode or "DRIVE",
        include_polyline_points=payload.include_polyline_points if payload.include_polyline_points is not None else True
    )
    return RouteResponse(**route_data)
