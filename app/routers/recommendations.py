import logging
from typing import List
from fastapi import APIRouter
from app.schemas.recommendation import (
    HospitalRecommendationRequest,
    HospitalRecommendationResponse,
    ScoredHospitalRoute,
    ScoreBreakdown
)
from app.schemas.hospital import HospitalInfo
from app.schemas.route import RouteResponse
from app.schemas.weather import WeatherData
from app.schemas.road_condition import RoadConditionResponse
from app.core.exceptions import ResourceNotFoundError

from app.services.places_service import places_service
from app.services.routes_service import routes_service
from app.services.weather_service import weather_service
from app.services.road_model_service import road_model_service
from app.services.scoring_service import scoring_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Hospital Route Recommendations"])

@router.post("/best-hospitals", response_model=HospitalRecommendationResponse, summary="Find & rank best hospital routes")
def recommend_best_hospitals(payload: HospitalRecommendationRequest):
    """
    Comprehensive hospital route recommendation engine:
    1. Discovers nearby hospitals within the search radius.
    2. Computes driving route, distance, static duration, and traffic congestion for each hospital.
    3. Fetches live weather conditions to assess environmental hazards.
    4. Evaluates road surface quality using AI vision analysis (if image URL is provided) or intelligent context estimation.
    5. Calculates a weighted composite suitability score and ranks hospitals from best to worst.
    """
    origin_lat = payload.latitude
    origin_lon = payload.longitude
    radius = payload.radius_meters or 5000.0
    limit = payload.max_hospitals_to_evaluate or 5

    # Step 1: Discover nearby hospitals
    raw_hospitals = places_service.search_nearby_hospitals(
        lat=origin_lat,
        lon=origin_lon,
        radius_meters=radius,
        limit=limit
    )

    if not raw_hospitals:
        raise ResourceNotFoundError(
            resource_name="Hospital",
            message=f"No hospitals found within {radius} meters of coordinates ({origin_lat}, {origin_lon})."
        )

    # Step 2: Fetch current weather at origin
    current_weather_dict = weather_service.get_weather(origin_lat, origin_lon)
    weather_obj = WeatherData(**current_weather_dict)

    # Step 3: Road condition assessment (from image URL if supplied, else intelligent heuristic)
    if payload.road_image_url:
        road_cond_dict = road_model_service.analyze_from_url(payload.road_image_url)
    else:
        road_cond_dict = road_model_service.estimate_default_road_condition(
            weather_safety=weather_obj.safety_penalty_score,
            congestion_ratio=1.1
        )
    road_cond_obj = RoadConditionResponse(**road_cond_dict)

    # Step 4: Evaluate routes and score each hospital
    evaluated_candidates = []
    routes_data = []

    for h in raw_hospitals:
        r = routes_service.compute_route(
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            dest_lat=h["lat"],
            dest_lon=h["lon"],
            travel_mode="DRIVE",
            include_polyline_points=True
        )
        routes_data.append((h, r))

    max_dur = max([r["duration_minutes"] for _, r in routes_data] + [15.0])

    for h, r in routes_data:
        scores_dict = scoring_service.compute_composite_score(
            duration_minutes=r["duration_minutes"],
            congestion_ratio=r["congestion_ratio"],
            road_condition_score=road_cond_obj.road_score,
            weather_safety_score=weather_obj.safety_penalty_score,
            max_duration_in_group=max_dur
        )

        notes = scoring_service.generate_recommendation_notes(
            scores=scores_dict,
            duration_minutes=r["duration_minutes"],
            congestion_ratio=r["congestion_ratio"],
            weather_main=weather_obj.weather_main,
            road_label=road_cond_obj.condition_label
        )

        evaluated_candidates.append({
            "hospital": HospitalInfo(**h),
            "route": RouteResponse(**r),
            "weather": weather_obj,
            "road_condition": road_cond_obj,
            "scores": ScoreBreakdown(**scores_dict),
            "recommendation_notes": notes,
            "final_score": scores_dict["final_composite_score"]
        })

    # Step 5: Rank by final composite score descending
    sorted_candidates = sorted(evaluated_candidates, key=lambda x: x["final_score"], reverse=True)

    ranked_list: List[ScoredHospitalRoute] = []
    for rank_idx, cand in enumerate(sorted_candidates, start=1):
        ranked_list.append(
            ScoredHospitalRoute(
                rank=rank_idx,
                hospital=cand["hospital"],
                route=cand["route"],
                weather=cand["weather"],
                road_condition=cand["road_condition"],
                scores=cand["scores"],
                recommendation_notes=cand["recommendation_notes"]
            )
        )

    return HospitalRecommendationResponse(
        origin={"latitude": origin_lat, "longitude": origin_lon},
        total_evaluated=len(ranked_list),
        recommended_hospital=ranked_list[0],
        ranked_hospitals=ranked_list
    )
