from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from beanie import init_beanie
from app.models import TodoList

client = AsyncIOMotorClient(host=settings.mongo_url.get_secret_value())

db = client[settings.mongo_db]


async def init_db():
    await init_beanie(database=db, document_models=[TodoList])


def close_db():
    client.close()
