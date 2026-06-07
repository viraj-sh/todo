from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from beanie import init_beanie
from app.models import User, Workspace, ResetToken, ApiKey, List, Item, Tag

client = AsyncIOMotorClient(host=settings.mongo_url.get_secret_value())

db = client[settings.mongo_db]


async def init_db():
    await init_beanie(
        database=db,
        document_models=[User, Workspace, ResetToken, ApiKey, List, Item, Tag],
    )


def close_db():
    client.close()
