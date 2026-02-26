"""
MongoDB async connection using Motor + Beanie ODM.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.config import settings
from app.models.user import User
from app.models.analysis import AnalysisRecord

_client: AsyncIOMotorClient | None = None


async def connect_to_database():
    """Initialize MongoDB connection and Beanie ODM."""
    global _client
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = _client[settings.DATABASE_NAME]

    await init_beanie(
        database=database,
        document_models=[User, AnalysisRecord],
    )
    print(f"✅  Connected to MongoDB: {settings.DATABASE_NAME}")


async def close_database_connection():
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        print("🔌  MongoDB connection closed.")


def get_database():
    """Get the database instance."""
    if _client is None:
        raise RuntimeError("Database not initialized. Call connect_to_database() first.")
    return _client[settings.DATABASE_NAME]
