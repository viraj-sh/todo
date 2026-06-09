from __future__ import annotations
from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from datetime import datetime, UTC
from enum import StrEnum


class ListColor(StrEnum):
    BLUE = "blue"
    GREEN = "green"
    RED = "red"
    YELLOW = "yellow"
    PURPLE = "purple"


class ListBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: ListColor = ListColor.BLUE


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
    color: ListColor = ListColor.BLUE


class ListSummary(BaseModel):
    id: PydanticObjectId
    name: str
    color: ListColor = ListColor.BLUE
    item_count: int
    created_at: datetime
    updated_at: datetime
