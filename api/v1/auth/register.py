#register api
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.user import UserRegisterRequest, UserResponse
from db.session import get_db
from db.models.user import User
from core.security import hash_password, create_access_token, create_refresh_token, generate_verification_token

router = APIRouter(prefix="/register", tags=["register"])

@router.post("",response_model=UserResponse)
async def register(request: Request, db: Session = Depends(get_db)):
    new_user = UserRegisterRequest.model_validate(await request.json())

        #check if user already exists

    existing = db.query(User).filter(User.email == new_user.email).first()
    if existing:
        raise HTTPException(status_code=400,detail="User already exists")

    #hashing the password
    verification_token = generate_verification_token()
    new_user.password = hash_password(new_user.password)

    #create user
    user_record = User(
        email=new_user.email,
        password=new_user.password,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        verification_token=verification_token,
    )
    db.add(user_record)
    db.commit()
    db.refresh(user_record)

    # Generate JWT tokens — store the user's UUID in the sub claim
    # so protected endpoints can identify the caller without needing user_id in the body
    token = create_access_token({"sub": str(user_record.id)})
    refresh_token = create_refresh_token({"sub": str(user_record.id)})

    user_record.token = token
    user_record.refresh_token = refresh_token

    db.commit()
    db.refresh(user_record)
    
    return UserResponse(
        username=user_record.email,
        email=user_record.email,
        token=token,
        refresh_token=refresh_token,
        needs_onboarding=user_record.needs_onboarding,
        created_at=user_record.created_at,
        updated_at=user_record.updated_at,
    )


    
