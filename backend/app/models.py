from typing import Literal

from beanie import Document, PydanticObjectId
from pydantic import EmailStr
from datetime import datetime, UTC
from pydantic import Field
from app.schemas.list import ListSummary, ListColor
from app.schemas.workspace import ExportWorkspace, ExportItem, ExportList


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

    @staticmethod
    async def get_export_data(workspace_id: PydanticObjectId):
        pipeline = [
            {"$match": {"_id": workspace_id}},
            {
                "$lookup": {
                    "from": "tags",
                    "localField": "_id",
                    "foreignField": "workspace_id",
                    "as": "tags",
                }
            },
            {
                "$lookup": {
                    "from": "lists",
                    "localField": "_id",
                    "foreignField": "workspace_id",
                    "as": "lists",
                }
            },
            {
                "$lookup": {
                    "from": "items",
                    "localField": "_id",
                    "foreignField": "workspace_id",
                    "as": "all_items",
                }
            },
        ]

        results = await Workspace.aggregate(pipeline).to_list()
        if not results:
            return None

        r = results[0]

        tag_map = {tag["_id"]: tag["name"] for tag in r.get("tags", [])}
        tag_names = list(tag_map.values())

        all_items = r.get("all_items", [])
        parent_items = [i for i in all_items if i.get("parent_id") is None]
        subtask_map: dict = {}
        for item in all_items:
            if item.get("parent_id") is not None:
                subtask_map.setdefault(item["parent_id"], []).append(item)

        def build_export_item(item: dict) -> ExportItem:
            return ExportItem(
                label=item["label"],
                description=item.get("description"),
                priority=item.get("priority"),
                deadline=item.get("deadline"),
                checked=item.get("checked", False),
                tags=[
                    tag_map[tid] for tid in item.get("tag_ids", []) if tid in tag_map
                ],
                subtasks=[
                    build_export_item(sub) for sub in subtask_map.get(item["_id"], [])
                ],
            )

        export_lists = []
        for lst in r.get("lists", []):
            list_parent_items = [i for i in parent_items if i["list_id"] == lst["_id"]]
            export_lists.append(
                ExportList(
                    name=lst["name"],
                    items=[build_export_item(i) for i in list_parent_items],
                )
            )

        return ExportWorkspace(
            name=r["name"],
            tags=tag_names,
            lists=export_lists,
        )


class List(Document):
    name: str
    user_id: PydanticObjectId
    workspace_id: PydanticObjectId
    color: str = ListColor.BLUE
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
