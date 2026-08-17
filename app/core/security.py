import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
import jwt
from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.exceptions import AppBaseException

# Security settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hospital-emergency-super-secret-key-2026-secure-jwt")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

http_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    pw_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    try:
        pw_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hashed_bytes)
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT access token with expiration."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AppBaseException(
            message="Your session token has expired. Please log in again.",
            code="TOKEN_EXPIRED",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    except jwt.PyJWTError as e:
        raise AppBaseException(
            message=f"Invalid authentication token: {str(e)}",
            code="INVALID_TOKEN",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)
) -> Dict[str, Any]:
    """FastAPI dependency to extract and verify the current authenticated user."""
    if not credentials:
        raise AppBaseException(
            message="Authentication credentials (Bearer token) were not provided.",
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise AppBaseException(
            message="Authentication token missing user subject.",
            code="INVALID_TOKEN",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    from app.db.database import db
    user = db.get_user_by_id(int(user_id))
    if not user:
        raise AppBaseException(
            message="User associated with this token no longer exists.",
            code="USER_NOT_FOUND",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    if not user.get("is_active", True):
        raise AppBaseException(
            message="User account has been deactivated.",
            code="USER_INACTIVE",
            status_code=status.HTTP_403_FORBIDDEN
        )

    return user

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)
) -> Optional[Dict[str, Any]]:
    """Optional authentication dependency: returns user if token is provided and valid, else None."""
    if not credentials:
        return None
    try:
        return get_current_user(credentials)
    except Exception:
        return None

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """FastAPI dependency to restrict access to ADMIN role only."""
    if current_user.get("role") != "admin":
        raise AppBaseException(
            message="Access forbidden: You do not have administrator privileges.",
            code="FORBIDDEN_ADMIN_ONLY",
            status_code=status.HTTP_403_FORBIDDEN
        )
    return current_user
