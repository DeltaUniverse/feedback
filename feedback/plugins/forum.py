import asyncio
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import Message

from config import FORUM_CHAT_ID


@Client.on_message(
    (filters.chat(FORUM_CHAT_ID) & ~filters.me)
    & (~filters.service & ~filters.command(["e", "del", "start"]))
)
async def forum_handler(client: Client, message: Message) -> None:
    topic_id = message.message_thread_id
    user_id = await client.db.get_user_id_by_thread(topic_id)

    if not user_id:
        return

    user_message_id = (
        await fetch_user_message_id(client, user_id, message.reply_to_message_id)
        if message.reply_to_message_id
        else None
    )

    user_message = await forward_or_copy_message(message, user_id, user_message_id)

    if user_message:
        await asyncio.gather(
            message.react("👍"),
            client.db.add_message_data(user_id, user_message.id, message.id),
        )


async def fetch_user_message_id(
    client: Client, user_id: int, reply_to_message_id: Optional[int]
) -> Optional[int]:
    return (
        await client.db.get_user_message_id(user_id, reply_to_message_id)
        if reply_to_message_id
        else None
    )


async def forward_or_copy_message(
    message: Message, user_id: int, reply_to_message_id: Optional[int] = None
) -> Optional[Message]:
    if any([message.forward_from, message.forward_from_chat, message.story]):
        return await message.forward(user_id)

    return await message.copy(
        user_id,
        reply_to_message_id=reply_to_message_id,
        quote_text=message.quote_text,
        quote_entities=message.quote_entities,
    )
