from __future__ import annotations
from pydantic import BaseModel, Field
from beanie import PydanticObjectId
import uuid


class ListBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class ListResponse(ListBase):
    id: PydanticObjectId
    items: list[ListItemResponse]


class ListDetailedResponse(ListBase):
    id: PydanticObjectId
    items: list[ListItemResponse]


class ListCreate(ListBase):
    pass


class ListUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)


class ListSummary(BaseModel):
    id: PydanticObjectId
    name: str = Field(min_length=1, max_length=50)
    item_count: int = Field()


class ListItemBase(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    label: str = Field(min_length=1, max_length=50)
    checked: bool = Field(default=False)


class ListItemCreate(BaseModel):
    label: str = Field(min_length=1, max_length=50)
    checked: bool = Field(default=False)


class ListItemUpdatePartial(BaseModel):
    item_id: str
    checked: bool | None = Field(default=None)
    # label: str | None = Field(default=None, min_length=1, max_length=50)


class ListItemResponse(ListItemBase):
    pass
