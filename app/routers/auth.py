from fastapi import APIRouter, Depends, status
from app.db.database import db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
from app.core.exceptions import AppBaseException, InvalidInputError
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserProfileResponse,
    UserUpdateRequest,
    ChangePasswordRequest
)

router = APIRouter(prefix="/auth", tags=["Authentication & Profile"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="Register new user")
def register_user(payload: UserRegisterRequest):
    """
    Register a new user account with email, password, and emergency profile details.
    Returns the user profile and a JWT access token.
    """
    existing = db.get_user_by_email(payload.email)
    if existing:
        raise InvalidInputError(
            message=f"An account with email '{payload.email}' already exists.",
            details={"email": payload.email}
        )

    pw_hash = hash_password(payload.password)
    user = db.create_user(
        email=payload.email,
        password_hash=pw_hash,
        full_name=payload.full_name,
        role="user",
        blood_group=payload.blood_group,
        emergency_contact=payload.emergency_contact,
        phone_number=payload.phone_number
    )

    access_token = create_access_token(data={"sub": str(user["id"]), "email": user["email"], "role": user["role"]})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserProfileResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            blood_group=user.get("blood_group"),
            emergency_contact=user.get("emergency_contact"),
            phone_number=user.get("phone_number"),
            is_active=bool(user["is_active"]),
            created_at=user["created_at"]
        )
    )

@router.post("/login", response_model=TokenResponse, summary="User & Admin login")
def login_user(payload: UserLoginRequest):
    """
    Authenticate with email and password. Returns JWT access token and user info.
    """
    user = db.get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise AppBaseException(
            message="Invalid email address or password.",
            code="INVALID_CREDENTIALS",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    if not user.get("is_active", True):
        raise AppBaseException(
            message="Your account is inactive. Please contact support.",
            code="USER_INACTIVE",
            status_code=status.HTTP_403_FORBIDDEN
        )

    access_token = create_access_token(data={"sub": str(user["id"]), "email": user["email"], "role": user["role"]})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserProfileResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            blood_group=user.get("blood_group"),
            emergency_contact=user.get("emergency_contact"),
            phone_number=user.get("phone_number"),
            is_active=bool(user["is_active"]),
            created_at=user["created_at"]
        )
    )

@router.get("/me", response_model=UserProfileResponse, summary="Get current logged in user profile")
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Retrieve authenticated user profile and medical emergency details.
    """
    return UserProfileResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        blood_group=current_user.get("blood_group"),
        emergency_contact=current_user.get("emergency_contact"),
        phone_number=current_user.get("phone_number"),
        is_active=bool(current_user["is_active"]),
        created_at=current_user["created_at"]
    )

@router.put("/profile", response_model=UserProfileResponse, summary="Update user profile")
def update_profile(payload: UserUpdateRequest, current_user: dict = Depends(get_current_user)):
    """
    Update name, blood group, emergency contact phone, or primary phone.
    """
    updated_user = db.update_user_profile(
        user_id=current_user["id"],
        full_name=payload.full_name,
        blood_group=payload.blood_group,
        emergency_contact=payload.emergency_contact,
        phone_number=payload.phone_number
    )
    return UserProfileResponse(
        id=updated_user["id"],
        email=updated_user["email"],
        full_name=updated_user["full_name"],
        role=updated_user["role"],
        blood_group=updated_user.get("blood_group"),
        emergency_contact=updated_user.get("emergency_contact"),
        phone_number=updated_user.get("phone_number"),
        is_active=bool(updated_user["is_active"]),
        created_at=updated_user["created_at"]
    )

@router.post("/change-password", summary="Change user password")
def change_password(payload: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """
    Change account password after validating current password.
    """
    if not verify_password(payload.current_password, current_user["password_hash"]):
        raise InvalidInputError(message="Current password does not match.")

    new_hash = hash_password(payload.new_password)
    db.update_user_password(current_user["id"], new_hash)
    return {"success": True, "message": "Password updated successfully."}
