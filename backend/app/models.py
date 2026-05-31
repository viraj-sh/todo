from beanie import Document
from app.schemas import ListItemBase
from app.schemas import ListSummary


class TodoList(Document):
    name: str
    items: list[ListItemBase] = []

    @staticmethod
    async def list_summaries() -> list[ListSummary]:
        pipeline = [
            {"$project": {"id": "$_id", "name": 1, "item_count": {"$size": "$items"}}}
        ]
        return await TodoList.aggregate(
            pipeline, projection_model=ListSummary
        ).to_list()

    class Settings:
        name = "todo_list"
