from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.db.database import db
from app.core.security import get_current_user
from app.core.exceptions import ResourceNotFoundError
from app.schemas.history import (
    SaveHistoryRequest,
    HistoryItemResponse,
    HistoryListResponse
)

router = APIRouter(prefix="/history", tags=["Recommendation History"])

@router.post("/save", response_model=HistoryItemResponse, status_code=status.HTTP_201_CREATED, summary="Save recommendation to user history")
def save_history(payload: SaveHistoryRequest, current_user: dict = Depends(get_current_user)):
    """
    Save an emergency hospital recommendation result to the user's persistent search history.
    """
    record = db.save_history_record(
        user_id=current_user["id"],
        origin_lat=payload.origin_lat,
        origin_lon=payload.origin_lon,
        radius_meters=payload.radius_meters,
        recommended_hospital_name=payload.recommended_hospital_name,
        recommended_hospital_distance_km=payload.recommended_hospital_distance_km,
        recommended_hospital_duration_min=payload.recommended_hospital_duration_min,
        composite_score=payload.composite_score,
        weather_condition=payload.weather_condition,
        road_condition_label=payload.road_condition_label,
        total_evaluated=payload.total_evaluated,
        raw_result=payload.raw_result
    )
    return HistoryItemResponse(**record)

@router.get("/my-history", response_model=HistoryListResponse, summary="Get user recommendation history")
def get_my_history(
    limit: Optional[int] = Query(50, ge=1, le=100, description="Max history items"),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch the list of historical emergency queries and calculated routes for the logged-in user.
    """
    records = db.get_user_history(user_id=current_user["id"], limit=limit or 50)
    return HistoryListResponse(
        total_count=len(records),
        items=[HistoryItemResponse(**r) for r in records]
    )

@router.get("/{history_id}", response_model=HistoryItemResponse, summary="Get specific history record details")
def get_history_detail(history_id: int, current_user: dict = Depends(get_current_user)):
    """
    Fetch the full JSON details and route breakdown for a past recommendation.
    """
    record = db.get_history_record_by_id(history_id)
    if not record or (record.get("user_id") != current_user["id"] and current_user.get("role") != "admin"):
        raise ResourceNotFoundError(
            resource_name="HistoryRecord",
            message=f"History record with ID {history_id} not found."
        )
    return HistoryItemResponse(**record)

@router.delete("/{history_id}", summary="Delete history record")
def delete_history(history_id: int, current_user: dict = Depends(get_current_user)):
    """
    Delete a history record from the user's account.
    """
    success = db.delete_user_history_record(history_id, current_user["id"])
    if not success:
        raise ResourceNotFoundError(
            resource_name="HistoryRecord",
            message=f"History record with ID {history_id} not found or could not be deleted."
        )
    return {"success": True, "message": "Record deleted successfully."}
