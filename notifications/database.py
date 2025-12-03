"""
MongoDB database connection and utilities.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

# MongoDB connection settings
MONGODB_HOST = os.getenv("MONGODB_HOST", "localhost")
MONGODB_PORT = os.getenv("MONGODB_PORT", "27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "notifications_db")

MONGODB_URL = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}"


class Database:
    """MongoDB database connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB."""
        cls.client = AsyncIOMotorClient(MONGODB_URL)
        # Verify connection
        await cls.client.admin.command('ping')
        print(f"✅ Connected to MongoDB at {MONGODB_URL}")
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB."""
        if cls.client:
            cls.client.close()
            print("❌ Disconnected from MongoDB")
    
    @classmethod
    def get_database(cls):
        """Get the database instance."""
        if cls.client is None:
            raise RuntimeError("Database client is not connected. Call Database.connect() before using the database.")
        return cls.client[MONGODB_DATABASE]
    
    @classmethod
    def get_users_collection(cls):
        """Get the users collection."""
        return cls.get_database()["users"]


# Convenience function
def get_users_collection():
    """Get users collection (shortcut)."""
    return Database.get_users_collection()
