from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from datetime import datetime


class WorkspaceBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class WorkspaceResponse(WorkspaceBase):
    id: PydanticObjectId
    user_id: PydanticObjectId
    created_at: datetime
    updated_at: datetime


class WorkspaceSimpleResponse(WorkspaceBase):
    id: PydanticObjectId
    user_id: PydanticObjectId
    created_at: datetime
    updated_at: datetime
