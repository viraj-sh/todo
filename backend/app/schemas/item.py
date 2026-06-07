from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from datetime import datetime, UTC


class ItemBase(BaseModel):
    id: PydanticObjectId
    label: str
    checked: bool = Field(default=False)
    priority: int | None = Field(default=None)
    description: str | None = Field(default=None)
    deadline: datetime | None = Field(default=None)
    tag_ids: list[PydanticObjectId] = []
    parent_id: PydanticObjectId | None = Field(default=None)
    created_at: datetime
    updated_at: datetime


class ItemCreate(BaseModel):
    label: str = Field(min_length=1, max_length=250)
    checked: bool = Field(default=False)
    priority: int | None = Field(default=None, ge=1, le=3)
    description: str | None = Field(default=None, min_length=0, max_length=10000)
    deadline: datetime | None = Field(default=None)
    tag_ids: list[PydanticObjectId] = []
    parent_id: PydanticObjectId | None = Field(default=None)


class ItemUpdatePartial(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=250)
    checked: bool | None = Field(default=None)
    priority: int | None = Field(default=None, ge=1, le=3)
    description: str | None = Field(default=None, min_length=0, max_length=10000)
    deadline: datetime | None = Field(default=None)
    tag_ids: list[PydanticObjectId] = []


class ItemResponse(ItemBase):
    pass
