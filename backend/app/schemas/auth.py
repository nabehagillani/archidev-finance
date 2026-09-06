from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    company_name: str
    full_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    company_id: str
    full_name: str
