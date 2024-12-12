import asyncio
import contextlib
import html

from pyrogram import Client, filters
from pyrogram.errors import ButtonUserPrivacyRestricted, RPCError
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    Message,
)

from config import FORUM_CHAT_ID


@Client.on_message(filters.chat(FORUM_CHAT_ID) & filters.command("del"))
async def del_message_handler(client: Client, message: Message) -> None:
    if message.reply_to_message:
        user_id = await client.db.get_user_id_by_thread(message.message_thread_id)
        if user_id:
            user_message_id = await client.db.get_user_message_id(
                user_id, message.reply_to_message_id
            )
        else:
            user_message_id = None

        if not (user_id or user_message_id):
            await message.reply_text("<b>User/Message not Found!</b>", quote=True)
            return

        with contextlib.suppress(RPCError):
            await asyncio.gather(
                client.delete_messages(user_id, user_message_id),
                message.reply_to_message.react("👎"),
            )

    await message.delete()


@Client.on_message(filters.chat(FORUM_CHAT_ID) & filters.command("start"))
async def user_profile_handler(client: Client, message: Message) -> None:
    user_id = await client.db.get_user_id_by_thread(message.message_thread_id)
    if not user_id:
        await message.reply_text("<b>User not Found!</b>", quote=True)
        return

    response = await message.reply_text("<b>Fetching...</b>", quote=True)

    user_details = await client.get_users(user_id)
    caption_text = (
        f"<pre language='Name'>{html.escape(user_details.full_name)}</pre>"
        if user_details.full_name
        else "<b>Deleted Account</b>"
    )
    user_buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Profile", user_id=user_id)]]
    )

    if getattr(user_details, "photo"):
        photo = await client.download_media(user_details.photo.big_file_id)
        try:
            await message.reply_photo(
                photo, quote=True, caption=caption_text, reply_markup=user_buttons
            )
        except ButtonUserPrivacyRestricted:
            await message.reply_photo(
                photo, quote=True, caption=caption_text, reply_markup=None
            )
        await response.delete(revoke=True)
    else:
        try:
            await response.edit_text(caption_text, reply_markup=user_buttons)
        except ButtonUserPrivacyRestricted:
            await response.edit_text(caption_text, reply_markup=None)


@Client.on_inline_query()
async def inline_query_handler(_: Client, inline_query: InlineQuery) -> None:
    await inline_query.answer(
        [], cache_time=900, switch_pm_text='"Hello, World!"', switch_pm_parameter="_"
    )
