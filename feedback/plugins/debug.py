import asyncio
import contextlib
import html
import io
from typing import Any, Dict, Optional, Union

from aiohttp import ClientSession
from meval import meval
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import FORUM_CHAT_ID

eval_tasks: Dict[int, Any] = {}


@Client.on_message(filters.chat(FORUM_CHAT_ID) & filters.command("e"))
async def debug_handler(client: Client, message: Message) -> None:
    if len(message.text.split()) == 1:
        await message.reply_text("<b>No Code!</b>", quote=True)
        return

    reply_text = await message.reply_text(
        "...",
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancel", callback_data="Cancel")]]
        ),
    )

    async def eval_func() -> None:
        eval_code = message.text.split(maxsplit=1)[1]
        eval_vars = {
            "c": client,
            "m": message,
            "r": message.reply_to_message,
            "u": (message.reply_to_message or message).from_user,
            "db": client.db,
        }

        start_time = client.loop.time()

        file = io.StringIO()
        with contextlib.redirect_stdout(file):
            try:
                meval_out = await meval(eval_code, globals(), **eval_vars)
                print_out = file.getvalue().strip() or str(meval_out) or "None"
            except Exception as exception:
                print_out = repr(exception)

        elapsed_time = client.loop.time() - start_time

        converted_time = convert_seconds(elapsed_time)

        final_output = (
            f"<pre>{html.escape(print_out)}</pre>\n" f"<b>Elapsed:</b> {converted_time}"
        )
        if len(final_output) > 4096:
            paste_url = await paste_content(str(print_out))
            await reply_text.edit_text(
                f"<b>Elapsed:</b> {converted_time}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Output", url=paste_url)]]
                ),
                disable_web_page_preview=True,
            )
        else:
            await reply_text.edit_text(final_output)

    task_id = message.id
    _e_task = asyncio.create_task(eval_func())

    eval_tasks[task_id] = _e_task

    try:
        await _e_task
    except asyncio.CancelledError:
        await reply_text.edit_text("<b>Process Cancelled!</b>")
    finally:
        if task_id in eval_tasks:
            del eval_tasks[task_id]


@Client.on_callback_query(filters.regex(r"\bCancel\b"))
async def cancel_handler(_: Client, callback_query: CallbackQuery) -> None:
    reply_message_id = callback_query.message.reply_to_message_id
    if not reply_message_id:
        return

    def cancel_task(task_id) -> bool:
        task = eval_tasks.get(task_id, None)
        if task and not task.done():
            task.cancel()
            return True
        return False

    canceled = cancel_task(reply_message_id)
    if not canceled:
        return


async def paste_content(content: str) -> Optional[str]:
    service_url = "https://paste.rs"

    async with ClientSession() as session:
        async with session.post(service_url, data=content) as response:
            if response.status != 201:
                return None

            raw_url = await response.text()
            return raw_url.strip()

    return None


def convert_seconds(seconds: Union[int, float]) -> str:
    if seconds == 0:
        return "-"

    result_converted = []
    if seconds >= 1:
        result_converted.append(
            f"{int(seconds)} Second{'s' if int(seconds) > 1 else ''}"
        )
    elif seconds > 0:
        result_converted.append(
            f"{'{:.3f}'.format(seconds).rstrip('0').rstrip('.')} Seconds"
        )

    return ", ".join(result_converted)
