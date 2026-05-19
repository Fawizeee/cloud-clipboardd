from fastapi import APIRouter,Depends,Request,HTTPException
from db.session import get_db
from schemas.user import UserLoginRequest,UserResponse

router = APIRouter(prefix="/login",tags=["login"])

@router.post("",response_model=UserResponse)
async def login(request:Request,db:Session = Depends(get_db)):
    user_login = UserLoginRequest.model_validate(await request.json())
    user = await User.get_by_email(user_login.email)

    #check if user exists
    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    #verify password
    if not await verify_password(user_login.password,user.password):
        raise HTTPException(status_code=401,detail="Invalid password")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )
    
    user.last_login = datetime.utcnow()
    
    #generate jwt token
    token = create_access_token(user.email)
    refresh_token = create_refresh_token(user.email)

    user.token = token
    user.refresh_token = refresh_token

    db.commit()
    db.refresh(user)
    
    return UserResponse(token=token,refresh_token=refresh_token)