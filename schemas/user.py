import pydantic
from pydantic import EmailStr, field_validator
from datetime import datetime
from typing import Optional


# ── Registration ─────────────────────────────────────────────────────────────

class UserRegisterRequest(pydantic.BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    first_name: str
    last_name: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info: pydantic.ValidationInfo) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


# ── Login ─────────────────────────────────────────────────────────────────────

class DeviceInfoSchema(pydantic.BaseModel):
    device_name: str
    platform: str
    version: Optional[str] = None


class UserLoginRequest(pydantic.BaseModel):
    email: EmailStr
    password: str
    device_info: Optional[DeviceInfoSchema] = None


# ── Token refresh ─────────────────────────────────────────────────────────────

class TokenRefreshRequest(pydantic.BaseModel):
    refresh_token: str


class TokenRefreshResponse(pydantic.BaseModel):
    access_token: str
    expires_in: int   # seconds


# ── Email verification ────────────────────────────────────────────────────────

class VerifyEmailRequest(pydantic.BaseModel):
    email: EmailStr
    code: str


class ResendVerificationRequest(pydantic.BaseModel):
    email: EmailStr


# ── Password reset ────────────────────────────────────────────────────────────

class PasswordResetRequestSchema(pydantic.BaseModel):
    email: EmailStr


class PasswordResetConfirmSchema(pydantic.BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info: pydantic.ValidationInfo) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


# ── Profile update ────────────────────────────────────────────────────────────

class UserProfileUpdateRequest(pydantic.BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None


# ── Responses ─────────────────────────────────────────────────────────────────

class UserResponse(pydantic.BaseModel):
    id: str
    username: str
    email: str
    token: str
    refresh_token: str
    needs_onboarding: bool = True
    created_at: datetime
    updated_at: datetime


class UserLogoutRequest(pydantic.BaseModel):
    id: str