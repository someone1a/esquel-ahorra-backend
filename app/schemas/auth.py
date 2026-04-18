from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    lastname: str
    password: str
    confirm_password: str
    rol: str

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

    class Config:
        from_attributes = True