from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address", examples=["user@example.com"])
    password: str = Field(..., min_length=6, description="User password (min 6 characters)", examples=["SecurePassword123"])
    full_name: str = Field(..., min_length=2, description="Full Name", examples=["John Doe"])
    blood_group: Optional[str] = Field(None, description="Blood group (e.g. O+, A-, B+)", examples=["O+"])
    emergency_contact: Optional[str] = Field(None, description="Emergency contact phone/name", examples=["+1-555-911-0000"])
    phone_number: Optional[str] = Field(None, description="User primary phone number", examples=["+1-555-123-4567"])

class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address", examples=["user@emergency.com"])
    password: str = Field(..., description="User password", examples=["User@123"])

class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int = 1440
    user: UserProfileResponse

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, description="Full name")
    blood_group: Optional[str] = Field(None, description="Blood group (e.g. O+, A+, B-)")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact")
    phone_number: Optional[str] = Field(None, description="Phone number")

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password (min 6 characters)")
