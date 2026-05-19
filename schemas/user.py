# base model for registration

import pydantic
from datetime import datetime


class UserRegisterRequest(pydantic.BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str
    first_name: str
    last_name: str

class UserResponse(pydantic.BaseModel):
    id: str
    username: str
    email: str
    token: str
    refresh_token: str
    needs_onboarding: bool = True
    created_at: datetime
    updated_at: datetime

# base model for login
class UserLoginRequest(pydantic.BaseModel):
    email: str
    password: str

# base model for logout
class UserLogoutRequest(pydantic.BaseModel):
    id: str