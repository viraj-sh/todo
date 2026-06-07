from pydantic import BaseModel, Field, EmailStr


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshToken(BaseModel):
    refresh_token: str


class ForgotPassword(BaseModel):
    email: EmailStr = Field(max_length=254)


class ResetPassword(BaseModel):
    reset_token: str
    new_password: str = Field(min_length=6)


class OAuthProfile(BaseModel):
    name: str
    email: EmailStr
    provider_id: str
