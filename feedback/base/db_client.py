import logging
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client

from config import MONGODB_URL

logger = logging.getLogger("db_client")


class Database:
    def __init__(self, tg_client) -> None:
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[Any] = None
        self.tg_client: Client = tg_client

    async def connect(self) -> None:
        logger.info("Connecting to mongo database...")
        try:
            self.client = AsyncIOMotorClient(MONGODB_URL)
            self.db = self.client["FEEDBACKTGBOT"][str(self.tg_client.me.id)]
            logger.info("Mongo database connected successfully.")
        except Exception as err:
            logger.error(str(err))

    async def close(self) -> None:
        if self.client:
            self.client.close()
        self.client, self.db = None, None

    async def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        return await self.db.find_one({"user_id": user_id})

    async def update_user_thread(self, user_id: int, topic_id: int) -> None:
        await self.db.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "topic_id": topic_id,
                    "message_data_ids": [],
                },
            },
            upsert=True,
        )

    async def add_message_data(
        self, user_id: int, user_message_id: int, topic_message_id: int
    ) -> None:
        await self.db.update_one(
            {"user_id": user_id},
            {
                "$addToSet": {
                    "message_data_ids": {
                        "user_message_id": user_message_id,
                        "topic_message_id": topic_message_id,
                    }
                }
            },
            upsert=True,
        )

    async def get_topic_message_id(
        self, user_id: int, user_message_id: int
    ) -> Optional[int]:
        doc = await self.db.find_one({"user_id": user_id})
        if doc and "message_data_ids" in doc:
            messages_dict = {
                msg["user_message_id"]: msg["topic_message_id"]
                for msg in doc["message_data_ids"]
            }
            return messages_dict.get(user_message_id)
        return None

    async def get_user_message_id(
        self, user_id: int, topic_message_id: int
    ) -> Optional[int]:
        doc = await self.db.find_one({"user_id": user_id})
        if doc and "message_data_ids" in doc:
            messages_dict = {
                msg["topic_message_id"]: msg["user_message_id"]
                for msg in doc["message_data_ids"]
            }
            return messages_dict.get(topic_message_id)
        return None

    async def get_user_id_by_thread(self, topic_id: int) -> Optional[int]:
        doc = await self.db.find_one({"topic_id": topic_id})
        if doc:
            return doc["user_id"]
        return None

    async def get_topic_id_by_user(self, user_id: int) -> Optional[int]:
        doc = await self.db.find_one({"user_id": user_id})
        if doc:
            return doc.get("topic_id")
        return None

    async def update_topic_message_data(
        self, user_id: int, user_message_id: int, new_topic_message_id: int
    ) -> None:
        await self.db.update_one(
            {"user_id": user_id, "message_data_ids.user_message_id": user_message_id},
            {"$set": {"message_data_ids.$.topic_message_id": new_topic_message_id}},
        )

    async def update_user_message_data(
        self, user_id: int, topic_message_id: int, new_user_message_id: int
    ) -> None:
        await self.db.update_one(
            {
                "user_id": user_id,
                "message_data_ids.topic_message_id": topic_message_id,
            },
            {"$set": {"message_data_ids.$.user_message_id": new_user_message_id}},
        )


#     async def add_blocked_user(self, user_id: int) -> None:
#         """
#         Adds a user ID to the blocked_user_ids list.
#
#         Args:
#             user_id (int): ID of the user to be blocked.
#
#         Returns:
#             None
#         """
#         await self.db.update_one(
#             {"_id": "blocked_user_ids"},
#             {"$addToSet": {"user_ids": user_id}},
#             upsert=True,
#         )
#
#     async def remove_blocked_user(self, user_id: int) -> None:
#         """
#         Removes a user ID from the blocked_user_ids list.
#
#         Args:
#             user_id (int): ID of the user to be removed from the block list.
#
#         Returns:
#             None
#         """
#         await self.db.update_one(
#             {"_id": "blocked_user_ids"}, {"$pull": {"user_ids": user_id}}
#         )
#
#     async def get_blocked_users(self) -> Optional[List[int]]:
#         """
#         Retrieves the list of all blocked user IDs.
#
#         Returns:
#             Optional[List[int]]: List of blocked user IDs if found, otherwise None.
#         """
#         doc = await self.db.find_one({"_id": "blocked_user_ids"})
#         if doc:
#             return doc.get("user_ids", [])
#         return []
#
#     async def get_all_user_ids_with_message_data(self) -> List[int]:
#         """
#         Retrieves a list of all unique user IDs that have message data.
#
#         Returns:
#             List[int]: List of user IDs with message data.
#         """
#         user_docs = await self.db.find({"message_data_ids": {"$exists": True}}).to_list(
#             length=None
#         )
#         return [doc["user_id"] for doc in user_docs]
#
#     async def delete_user_message_data(self, user_id: int) -> None:
#         """
#         Deletes a specific user's document from the message data collection.
#
#         Args:
#             user_id (int): The ID of the user whose message data should be deleted.
#
#         Returns:
#             None
#         """
#         await self.db.delete_one({"user_id": user_id})
