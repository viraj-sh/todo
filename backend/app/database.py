from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from beanie import init_beanie
from app.models import List, User, Workspace

# Globals used to cache the client and initialization state so serverless
# invocations can reuse the same connection when the function instance
# is warm.
_client: Optional[AsyncIOMotorClient] = None
_db = None
_initialized = False


def _ensure_client():
    """Initialize the motor client and db object if not already done."""
    global _client, _db
    if _client is None:
        _client = AsyncIOMotorClient(host=settings.mongo_url.get_secret_value())
        _db = _client[settings.mongo_db]
    return _client


async def init_db():
    """Initialize Beanie only once per process.

    For serverless environments we avoid relying solely on FastAPI lifespan
    handlers because they may not run on every invocation. This function is
    safe to call multiple times; Beanie init will only run once per process.
    """
    global _initialized, _db
    if not _initialized:
        _ensure_client()
        await init_beanie(database=_db, document_models=[List, User, Workspace])
        _initialized = True


def get_db():
    """Return the Motor database instance, ensuring client exists."""
    global _db
    if _db is None:
        _ensure_client()
    return _db


def close_db():
    """Close the Motor client and reset initialization state."""
    global _client, _db, _initialized
    if _client:
        _client.close()
    _client = None
    _db = None
    _initialized = False


# Backwards-compatible `db` object used by existing modules that import
# `db` at module import time. This is a thin proxy that resolves the
# current motor database instance on attribute access so route modules can
# safely use `db.command(...)` even if the actual client was created
# lazily at runtime.
class _DBProxy:
    def __getattr__(self, item):
        real = get_db()
        return getattr(real, item)


db = _DBProxy()
