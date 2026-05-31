"""
Password Reset Routes
=====================
POST /api/v1/auth/password-reset/request  — generate a reset token
POST /api/v1/auth/password-reset/confirm  — consume token, set new password
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from db.models.user import User
from core.security import generate_password_reset_token, hash_password
from schemas.user import PasswordResetRequestSchema, PasswordResetConfirmSchema

router = APIRouter(prefix="/password-reset", tags=["password-reset"])


@router.post("/request")
async def request_password_reset(
    body: PasswordResetRequestSchema,
    db: Session = Depends(get_db),
):
    """
    Generate a password-reset token for the given email address.

    In production this token would be emailed to the user.
    Here it is returned in the response body for development convenience.
    """
    user = db.query(User).filter(User.email == body.email).first()

    # Always return 200 to avoid user-enumeration attacks
    if not user:
        return {
            "success": True,
            "message": "If that email is registered, a reset token has been sent.",
        }

    reset_token = generate_password_reset_token()
    user.verification_token = reset_token   # reuse the verification_token column
    db.commit()

    # NOTE: In production, send this token via email. For now, return it directly.
    return {
        "success": True,
        "message": "Password reset token generated.",
        "reset_token": reset_token,   # remove in production
    }


@router.post("/confirm")
async def confirm_password_reset(
    body: PasswordResetConfirmSchema,
    db: Session = Depends(get_db),
):
    """
    Validate the reset token and update the user's password.
    """
    user = (
        db.query(User)
        .filter(
            User.verification_token == body.token,
            User.is_deleted == False,  # noqa: E712
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    user.password = hash_password(body.new_password)
    user.verification_token = None   # invalidate the token
    db.commit()

    return {"success": True, "message": "Password has been reset successfully. Please log in."}
