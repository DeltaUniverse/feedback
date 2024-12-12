import configparser
import os
from typing import Optional

CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE)


def get_env_var(
    key: str, section: str = "APP_CONFIG", default: Optional[str] = None
) -> str:
    value = os.getenv(key)
    if value:
        return value

    if config.has_option(section, key):
        value = config.get(section, key).strip()
        if value:
            return value

    if default is not None:
        return default

    raise ValueError(f"Missing required configuration: {key}")


API_ID = int(get_env_var("API_ID"))
API_HASH = get_env_var("API_HASH")
BOT_TOKEN = get_env_var("BOT_TOKEN")
FORUM_CHAT_ID = int(get_env_var("FORUM_CHAT_ID"))
MONGODB_URL = get_env_var("MONGODB_URL")
