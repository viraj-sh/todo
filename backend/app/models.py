from typing import Literal

from beanie import Document, PydanticObjectId
from pydantic import EmailStr
from datetime import datetime, UTC
from pydantic import Field
from app.schemas.list import ListSummary


class User(Document):
    username: str
    email: EmailStr
    password_hash: str | None = None
    oauth_provider: Literal["google", "github"] | None = None
    oauth_provider_id: str | None = None

    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)

    class Settings:
        name = "users"
        indexes = ["username", "email"]


class ResetToken(Document):
    token_hash: str
    user_id: PydanticObjectId
    created_at: datetime = datetime.now(UTC)
    expires_at: datetime

    class Settings:
        name = "reset_token"
        indexes = ["token_hash"]


class ApiKey(Document):
    name: str
    key_hash: str
    prefix: str
    user_id: PydanticObjectId
    last_used_at: datetime | None = None
    created_at: datetime = datetime.now(UTC)
    expires_at: datetime | None

    class Settings:
        name = "apikey"
        indexes = ["name", "prefix"]


class Workspace(Document):
    name: str
    user_id: PydanticObjectId
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)

    class Settings:
        name = "workspaces"
        indexes = ["name"]


class List(Document):
    name: str
    user_id: PydanticObjectId
    workspace_id: PydanticObjectId
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)

    class Settings:
        name = "lists"
        indexes = ["name"]

    @staticmethod
    async def get_workspace_lists_summary(
        workspace_id: PydanticObjectId,
    ) -> list[ListSummary]:
        pipeline = [
            {"$match": {"workspace_id": workspace_id}},
            {
                "$lookup": {
                    "from": "items",
                    "localField": "_id",
                    "foreignField": "list_id",
                    "as": "items",
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "name": 1,
                    "item_count": {"$size": "$items"},
                    "created_at": 1,
                    "updated_at": 1,
                }
            },
        ]

        results = await List.aggregate(pipeline).to_list()

        return [
            ListSummary(
                id=r["_id"],
                name=r["name"],
                item_count=r["item_count"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in results
        ]


class Item(Document):
    label: str
    checked: bool = Field(default=False)
    priority: int | None = Field(default=None)
    description: str | None = Field(default=None)
    deadline: datetime | None = Field(default=None)
    user_id: PydanticObjectId
    workspace_id: PydanticObjectId
    list_id: PydanticObjectId
    tag_ids: list[PydanticObjectId] = []
    parent_id: PydanticObjectId | None = Field(default=None)
    created_at: datetime = Field(default=datetime.now(UTC))
    updated_at: datetime = Field(default=datetime.now(UTC))

    class Settings:
        name = "items"
        indexes = [
            "label",
        ]


class Tag(Document):
    user_id: PydanticObjectId
    workspace_id: PydanticObjectId
    name: str

    class Settings:
        name = "tags"
        indexes = ["name"]
