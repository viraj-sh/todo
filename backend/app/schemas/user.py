from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from pydantic import EmailStr
from datetime import datetime

from app.schemas.workspace import WorkspaceSimpleResponse


class ApiKeyBase(BaseModel):
    id: PydanticObjectId
    name: str
    prefix: str
    last_used_at: datetime | None = None
    created_at: datetime
    expires_at: datetime | None


class ApiKeyFullResponse(ApiKeyBase):
    key: str


class ApiKeyResponse(ApiKeyBase):
    pass


class ApiKeySimpleResponse(ApiKeyBase):
    pass


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=3, max_length=64)
    expire_in: int | None = Field(default=None, ge=1, le=90)


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr = Field(max_length=254)


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserResponse(UserBase):
    id: PydanticObjectId
    created_at: datetime
    updated_at: datetime


class UserPrivateResponse(BaseModel):
    id: PydanticObjectId
    username: str
    email: EmailStr
    workspaces: list[WorkspaceSimpleResponse] = []
    api_keys: list[ApiKeySimpleResponse] = []
    created_at: datetime
    updated_at: datetime


class UserSecureResponse(BaseModel):
    id: PydanticObjectId
    username: str
    email: EmailStr
    is_verified: bool
    password_hash: str
    created_at: datetime
    updated_at: datetime


class UserPublicResponse(BaseModel):
    id: PydanticObjectId
    username: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=30)
    email: EmailStr | None = Field(default=None, max_length=254)


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class UserTag(BaseModel):
    name: str


class VerifyUser(BaseModel):
    verify_token: str
