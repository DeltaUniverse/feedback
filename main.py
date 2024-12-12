import asyncio
import contextlib
import logging

import aiorun
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import RPCError, TopicNotModified
from pyrogram.types import BotCommand, BotCommandScopeChatAdministrators

from config import API_HASH, API_ID, BOT_TOKEN, FORUM_CHAT_ID
from feedback.base import Database

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logging.basicConfig(level=logging.INFO, format="%(name)s[%(levelname)s]: %(message)s")
logger = logging.getLogger("tg_client")

for lib in {"pyrogram", "pymongo"}:
    logging.getLogger(lib).setLevel(logging.ERROR)

app = Client(
    name="bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=32,
    workdir="./feedback/",
    plugins=dict(root="feedback.plugins"),
    parse_mode=ParseMode.HTML,
    sleep_threshold=900,
)


async def start_client() -> None:
    logger.info("Starting the bot...")
    try:
        await app.start()
        with contextlib.suppress(TopicNotModified):
            await app.reopen_general_topic(FORUM_CHAT_ID)
    except RPCError as rpc_error:
        logger.error(str(rpc_error.MESSAGE))

    setattr(app, "db", Database(app))
    await app.db.connect()

    await app.set_bot_commands(
        commands=[
            BotCommand("del", "Delete by Reply"),
            BotCommand("start", "Show User Info"),
        ],
        scope=BotCommandScopeChatAdministrators(chat_id=FORUM_CHAT_ID),
    )

    logger.info("Bot activated successfully.")


async def stop_client() -> None:
    logger.info("Stopping the bot...")
    with contextlib.suppress(Exception):
        await app.close_general_topic(FORUM_CHAT_ID)
        await app.stop()

    await app.db.close()
    logger.info("Bot stopped and database connection closed.")


if __name__ == "__main__":
    aiorun.logger.disabled = True
    aiorun.run(start_client(), loop=app.loop, shutdown_callback=stop_client())
