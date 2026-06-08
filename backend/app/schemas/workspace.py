from __future__ import annotations

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


class ExportItem(BaseModel):
    label: str
    checked: bool
    priority: int | None
    description: str | None
    deadline: datetime | None
    tags: list[str] = []
    subtasks: list[ExportItem] = []


class ExportList(BaseModel):
    name: str
    items: list[ExportItem] = []


class ExportWorkspace(BaseModel):
    name: str
    lists: list[ExportList] = []
    tags: list[str] = []


class ExportFile(BaseModel):
    version: str
    exported_at: datetime
    workspace: ExportWorkspace
