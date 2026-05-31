"""
Token Refresh Route
===================
POST /api/v1/auth/refresh  — exchange a valid refresh token for a new access token
"""

from fastapi import APIRouter, HTTPException, status
from core.security import decode_token, create_access_token
from core.config import settings
from schemas.user import TokenRefreshRequest, TokenRefreshResponse

router = APIRouter(prefix="/refresh", tags=["auth"])


@router.post("", response_model=TokenRefreshResponse)
async def refresh_access_token(body: TokenRefreshRequest):
    """
    Validate a refresh token and issue a new short-lived access token.

    The refresh token must have type == 'refresh' in its payload.
    """
    payload = decode_token(body.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token type mismatch. Expected a refresh token.",
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token payload is missing the user identity.",
        )

    new_access_token = create_access_token({"sub": user_id})
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # convert to seconds

    return TokenRefreshResponse(access_token=new_access_token, expires_in=expires_in)
