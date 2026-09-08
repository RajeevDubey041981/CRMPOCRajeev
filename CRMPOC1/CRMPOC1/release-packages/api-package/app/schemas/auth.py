from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    phone: str | None = None
    is_active: bool

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()
