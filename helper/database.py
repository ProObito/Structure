from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from datetime import datetime
import pytz

class CodeflixBots:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client["file_sequence_bot"]
        self.users = self.db["users"]
        self.settings = self.db["settings"]

    async def add_user(self, client, message):
        user_id = message.from_user.id
        user_data = {
            "_id": user_id,
            "first_name": message.from_user.first_name,
            "username": message.from_user.username or "N/A",
            "is_premium": False,
            "banned": False,
            "joined_at": datetime.now(pytz.UTC)
        }
        await self.users.update_one(
            {"_id": user_id},
            {"$setOnInsert": user_data},
            upsert=True
        )

codeflixbots = CodeflixBots()
