from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    lastname: str
    password: str
    confirm_password: str
    rol: str
    referral_code: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    rol: str

class UserProfile(BaseModel):
    id: int
    email: str
    name: str
    lastname: str
    rol: str
    points: int
    corrections_count: int
    referral_code: Optional[str] = None

    class Config:
        from_attributes = True