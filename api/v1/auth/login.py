from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.session import get_db
from schemas.user import UserLoginRequest, UserResponse
from db.models.user import User
from core.security import verify_password, create_access_token, create_refresh_token
from datetime import datetime

router = APIRouter(prefix="/login", tags=["login"])


@router.post("", response_model=UserResponse)
async def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user and issue a JWT access + refresh token pair.

    Returns the full user profile with tokens. The JWT sub claim stores
    the user's UUID so downstream protected endpoints can identify the caller.
    """
    user = db.query(User).filter(User.email == request.email).first()

    # Check if user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Verify password
    if not verify_password(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in",
        )

    user.last_login = datetime.utcnow()

    # Generate JWT tokens — store the user's UUID in the sub claim
    token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    user.token = token
    user.refresh_token = refresh_token

    db.commit()
    db.refresh(user)

    return UserResponse(
        username=user.email,
        email=user.email,
        token=token,
        refresh_token=refresh_token,
        needs_onboarding=user.needs_onboarding,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )