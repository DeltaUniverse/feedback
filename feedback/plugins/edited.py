import asyncio

from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.types import (
    InputMediaAnimation,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from config import FORUM_CHAT_ID


@Client.on_edited_message(filters.private & ~filters.me)
async def edited_private_handler(client: Client, message: Message) -> None:
    user_id = message.from_user.id

    topic_id, topic_message_id = await asyncio.gather(
        client.db.get_topic_id_by_user(user_id),
        client.db.get_topic_message_id(user_id, message.id),
    )

    if not (topic_id or topic_message_id):
        return

    new_topic_message = await message.copy(
        FORUM_CHAT_ID,
        message_thread_id=topic_id,
        reply_to_message_id=topic_message_id,
    )

    await asyncio.gather(
        new_topic_message.react("✍"),
        client.db.update_topic_message_data(user_id, message.id, new_topic_message.id),
    )


@Client.on_edited_message(filters.chat(FORUM_CHAT_ID))
async def edited_forum_handler(client: Client, message: Message) -> None:
    topic_id = message.message_thread_id

    user_id = await client.db.get_user_id_by_thread(topic_id)
    if not user_id:
        return

    user_message_id = await client.db.get_user_message_id(user_id, message.id)
    if not user_message_id:
        return

    try:
        user_message = await client.get_messages(user_id, user_message_id)

        if message.text:
            await user_message.edit_text(message.text, entities=message.entities)

        elif message.voice:
            await user_message.edit_caption(
                message.caption,
                caption_entities=(
                    message.caption_entities if message.caption else None
                ),
            )

        elif message.media:
            await handle_media_edit(client, user_message, message)

        else:
            await message.reply_text("<b>Message Can't Be Edited!</b>", quote=True)
            return

        await asyncio.gather(user_message.react("✍"), message.react("✍"))

    except RPCError as rpc_error:
        await message.reply_text(f"<b>{rpc_error.MESSAGE}!</b>", quote=True)


async def handle_media_edit(
    client: Client, user_message: Message, message: Message
) -> None:
    media_type = getattr(message, message.media.value)
    media_path = await client.download_media(media_type.file_id)

    thumb_path = None
    if hasattr(media_type, "thumbs") and media_type.thumbs:
        thumb_path = await client.download_media(media_type.thumbs[0].file_id)

    caption = message.caption
    caption_entities = message.caption_entities if caption else None

    if hasattr(message, "photo") and message.photo:
        await user_message.edit_media(
            InputMediaPhoto(
                media_path, caption=caption, caption_entities=caption_entities
            )
        )
    elif hasattr(message, "video") and message.video:
        await user_message.edit_media(
            InputMediaVideo(
                media_path,
                thumb=thumb_path,
                caption=caption,
                caption_entities=caption_entities,
                width=media_type.width,
                height=media_type.height,
                duration=media_type.duration,
                supports_streaming=media_type.supports_streaming,
            )
        )
    elif hasattr(message, "audio") and message.audio:
        await user_message.edit_media(
            InputMediaAudio(
                media_path,
                thumb=thumb_path,
                caption=caption,
                caption_entities=caption_entities,
                duration=media_type.duration,
                performer=media_type.performer,
                title=media_type.title,
            )
        )
    elif hasattr(message, "document") and message.document:
        await user_message.edit_media(
            InputMediaDocument(
                media_path,
                thumb=thumb_path,
                caption=caption,
                caption_entities=caption_entities,
            )
        )
    elif hasattr(message, "animation") and message.animation:
        await user_message.edit_media(
            InputMediaAnimation(
                media_path,
                thumb=thumb_path,
                caption=caption,
                caption_entities=caption_entities,
                width=media_type.width,
                height=media_type.height,
                duration=media_type.duration,
            )
        )
    else:
        raise ValueError("Unsupported Media Type!")
