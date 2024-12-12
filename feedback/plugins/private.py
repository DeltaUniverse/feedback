import asyncio
from typing import Optional

from pyrogram import Client, filters
from pyrogram.errors import RPCError, TopicDeleted
from pyrogram.raw import base, types
from pyrogram.types import Chat, Message, User

from config import FORUM_CHAT_ID


@Client.on_raw_update(group=1)
async def event_handler(client: Client, event: base.Update, _: User, __: Chat) -> None:
    if isinstance(event, types.UpdateBotStopped):
        user_id: int = event.user_id
        topic_id: Optional[int] = await client.db.get_topic_id_by_user(user_id)

        if not topic_id:
            return

        topic_title = "Forbidden!" if event.stopped else str(user_id)
        await client.edit_forum_topic(FORUM_CHAT_ID, topic_id, title=topic_title)


@Client.on_message(filters.private & ~filters.me)
async def private_handler(client: Client, message: Message) -> None:
    if text := message.text:
        if text.startswith("/start"):
            await message.reply_text('<b>"Hello, World!"</b>', quote=True)

    user_id: int = message.from_user.id
    topic_id = await client.db.get_topic_id_by_user(user_id) or await create_topic(
        client, user_id
    )

    topic_message_id = await get_topic_message_id(
        client, user_id, message.reply_to_message_id
    )

    try:
        topic_message = await forward_or_copy_message(
            message, topic_id, topic_message_id
        )
    except TopicDeleted:
        topic_id = await create_topic(client, user_id)
        topic_message = await forward_or_copy_message(
            message, topic_id, topic_message_id
        )
    except RPCError as rpc_error:
        await message.reply_text(f"<b>{str(rpc_error.NAME)}!</b>", quote=True)
        return

    await asyncio.gather(
        message.react("👍"),
        client.db.add_message_data(user_id, message.id, topic_message.id),
    )


async def create_topic(client: Client, user_id: int) -> int:
    topic = await client.create_forum_topic(FORUM_CHAT_ID, str(user_id))
    await client.db.update_user_thread(user_id, topic.id)
    return topic.id


async def get_topic_message_id(
    client: Client, user_id: int, reply_to_message_id: Optional[int]
) -> Optional[int]:
    if reply_to_message_id:
        return await client.db.get_topic_message_id(user_id, reply_to_message_id)
    return None


async def forward_or_copy_message(
    message: Message, topic_id: int, reply_to_message_id: Optional[int] = None
) -> Message:
    if any([message.forward_from, message.forward_from_chat, message.story]):
        return await message.forward(FORUM_CHAT_ID, message_thread_id=topic_id)

    reply_to_chat_id = None
    if not reply_to_message_id:
        reply_to_message = message.reply_to_message
        if (
            reply_to_message
            and reply_to_message.chat
            and getattr(reply_to_message.chat, "username", None)
        ):
            reply_to_chat_id = reply_to_message.chat.username
            reply_to_message_id = message.reply_to_message_id

    return await message.copy(
        FORUM_CHAT_ID,
        message_thread_id=topic_id,
        reply_to_chat_id=reply_to_chat_id,
        reply_to_message_id=reply_to_message_id,
        quote_text=message.quote_text,
        quote_entities=message.quote_entities,
    )
