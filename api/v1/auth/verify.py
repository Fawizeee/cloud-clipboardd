"""
Email Verification Routes
=========================
POST /api/v1/auth/verify          — verify email with the 6-digit code
POST /api/v1/auth/resend-verify   — resend a new verification code
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from db.models.user import User
from core.security import generate_verification_token
from schemas.user import VerifyEmailRequest, ResendVerificationRequest

router = APIRouter(tags=["auth"])


@router.post("/verify")
async def verify_email(body: VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Confirm the user's email address using the 6-digit code generated at registration.
    On success the user's account becomes active and is_verified is set to True.
    """
    user = db.query(User).filter(User.email == body.email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_verified:
        return {"success": True, "message": "Email already verified. You can log in."}

    if user.verification_token != body.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code.",
        )

    user.is_verified = True
    user.is_active = True
    user.verification_token = None  # invalidate the code
    db.commit()

    return {"success": True, "message": "Email verified successfully. You can now log in."}


@router.post("/resend-verify")
async def resend_verification(body: ResendVerificationRequest, db: Session = Depends(get_db)):
    """
    Generate and persist a new 6-digit verification code.

    In production this would be emailed to the user; here it is returned
    directly for development convenience.
    """
    user = db.query(User).filter(User.email == body.email).first()

    # Avoid enumeration — always return 200
    if not user or user.is_verified:
        return {
            "success": True,
            "message": "If that email exists and is unverified, a new code has been sent.",
        }

    new_code = generate_verification_token()
    user.verification_token = new_code
    db.commit()

    # NOTE: email the code in production
    return {
        "success": True,
        "message": "New verification code generated.",
        "verification_code": new_code,  # remove in production
    }
