from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.db.database import db
from app.core.security import require_admin
from app.core.exceptions import ResourceNotFoundError, InvalidInputError
from app.schemas.admin import (
    AdminStatsResponse,
    AdminUsersResponse,
    AdminLogsResponse,
    AdminLogItem,
    UpdateUserRoleRequest
)
from app.schemas.auth import UserProfileResponse

router = APIRouter(prefix="/admin", tags=["Admin Dashboard & System Monitoring"])

@router.get("/stats", response_model=AdminStatsResponse, summary="Get system metrics & performance stats")
def get_admin_stats(admin_user: dict = Depends(require_admin)):
    """
    Retrieve real-time metrics: total users, total recommendations, average duration,
    average score, and database status. (ADMIN ONLY)
    """
    metrics = db.get_admin_metrics()
    return AdminStatsResponse(**metrics)

@router.get("/users", response_model=AdminUsersResponse, summary="List all system users")
def get_all_users(admin_user: dict = Depends(require_admin)):
    """
    List all registered users, roles, account status, and timestamps. (ADMIN ONLY)
    """
    users = db.list_all_users()
    return AdminUsersResponse(
        total_count=len(users),
        users=[
            UserProfileResponse(
                id=u["id"],
                email=u["email"],
                full_name=u["full_name"],
                role=u["role"],
                blood_group=u.get("blood_group"),
                emergency_contact=u.get("emergency_contact"),
                phone_number=u.get("phone_number"),
                is_active=bool(u["is_active"]),
                created_at=u["created_at"]
            )
            for u in users
        ]
    )

@router.put("/users/{user_id}/role", response_model=UserProfileResponse, summary="Update user role (user/admin)")
def change_user_role(
    user_id: int,
    payload: UpdateUserRoleRequest,
    admin_user: dict = Depends(require_admin)
):
    """
    Promote a user to 'admin' or demote to 'user'. (ADMIN ONLY)
    """
    if payload.role not in ["user", "admin"]:
        raise InvalidInputError(
            message="Invalid role. Must be 'user' or 'admin'.",
            details={"role": payload.role}
        )

    target_user = db.get_user_by_id(user_id)
    if not target_user:
        raise ResourceNotFoundError(
            resource_name="User",
            message=f"User with ID {user_id} does not exist."
        )

    updated = db.update_user_role(user_id, payload.role)
    return UserProfileResponse(
        id=updated["id"],
        email=updated["email"],
        full_name=updated["full_name"],
        role=updated["role"],
        blood_group=updated.get("blood_group"),
        emergency_contact=updated.get("emergency_contact"),
        phone_number=updated.get("phone_number"),
        is_active=bool(updated["is_active"]),
        created_at=updated["created_at"]
    )

@router.get("/logs", response_model=AdminLogsResponse, summary="Get emergency recommendation query logs")
def get_system_logs(
    limit: Optional[int] = Query(100, ge=1, le=500, description="Max log items"),
    admin_user: dict = Depends(require_admin)
):
    """
    View all historical hospital recommendation queries triggered across the system with user metadata. (ADMIN ONLY)
    """
    logs = db.get_all_history_logs(limit=limit or 100)
    return AdminLogsResponse(
        total_count=len(logs),
        logs=[AdminLogItem(**l) for l in logs]
    )
