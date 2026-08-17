from typing import Dict
from fastapi import APIRouter, UploadFile, File
from app.schemas.road_condition import (
    RoadConditionUrlRequest,
    RoadConditionEstimateRequest,
    RoadConditionResponse,
    RoadLabelsResponse
)
from app.services.road_model_service import (
    road_model_service,
    ROAD_SCORES,
    get_category_for_score
)

router = APIRouter(prefix="/road-condition", tags=["Road Condition & Vision AI"])

@router.post("/analyze-url", response_model=RoadConditionResponse, summary="Analyze road condition from image URL")
def analyze_road_image_url(payload: RoadConditionUrlRequest):
    """
    Classify road surface condition and calculate road score (0-100) from a public image URL
    using the CLIP vision model.
    """
    result = road_model_service.analyze_from_url(payload.image_url)
    return RoadConditionResponse(**result)

@router.post("/analyze-upload", response_model=RoadConditionResponse, summary="Analyze road condition from uploaded file")
async def analyze_road_image_file(file: UploadFile = File(..., description="Road photo (JPG/PNG)")):
    """
    Upload an image file directly to evaluate road condition, potholes, cracks, or obstacles.
    """
    contents = await file.read()
    result = road_model_service.analyze_from_bytes(contents)
    return RoadConditionResponse(**result)

@router.post("/estimate", response_model=RoadConditionResponse, summary="Estimate road condition heuristically")
def estimate_road_condition(payload: RoadConditionEstimateRequest):
    """
    Heuristically estimate road condition based on weather severity and traffic congestion ratio
    when camera imagery is unavailable.
    """
    result = road_model_service.estimate_default_road_condition(
        weather_safety=payload.weather_safety or 90.0,
        congestion_ratio=payload.congestion_ratio or 1.0
    )
    return RoadConditionResponse(**result)

@router.get("/labels", response_model=RoadLabelsResponse, summary="Get list of all supported road labels and categories")
def get_road_labels():
    """
    Retrieve all benchmark road labels, categorized into Excellent, Good, Moderate, Poor, and Dangerous.
    """
    categories: Dict[str, Dict[str, int]] = {
        "Excellent": {},
        "Good": {},
        "Moderate": {},
        "Poor": {},
        "Dangerous": {}
    }
    for label, score in ROAD_SCORES.items():
        cat = get_category_for_score(score)
        categories[cat][label] = score

    return RoadLabelsResponse(
        total_labels=len(ROAD_SCORES),
        categories=categories
    )
