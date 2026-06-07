from __future__ import annotations
from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from datetime import datetime, UTC


class ListBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ListResponse(ListBase):
    id: PydanticObjectId
    created_at: datetime
    updated_at: datetime


class ListDetailedResponse(ListBase):
    id: PydanticObjectId
    created_at: datetime
    updated_at: datetime


class ListCreate(ListBase):
    pass


class ListUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    updated_at: datetime = datetime.now(UTC)


class ListSummary(BaseModel):
    id: PydanticObjectId
    name: str
    item_count: int
    created_at: datetime
    updated_at: datetime
