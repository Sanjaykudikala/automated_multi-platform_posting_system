import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def _get_env(key: str) -> Optional[str]:
    value = os.getenv(key)
    if value is not None:
        value = value.strip()
        if value:
            return value
    return None


BLUESKY_HANDLE = _get_env("BLUESKY_HANDLE")
BLUESKY_PASSWORD = _get_env("BLUESKY_PASSWORD")

MASTODON_INSTANCE = _get_env("MASTODON_INSTANCE")
MASTODON_ACCESS_TOKEN = _get_env("MASTODON_ACCESS_TOKEN")

REDDIT_CLIENT_ID = _get_env("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = _get_env("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = _get_env("REDDIT_USERNAME")
REDDIT_PASSWORD = _get_env("REDDIT_PASSWORD")
REDDIT_SUBREDDIT = _get_env("REDDIT_SUBREDDIT")

TELEGRAM_BOT_TOKEN = _get_env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _get_env("TELEGRAM_CHAT_ID")

DISCORD_WEBHOOK_URL = _get_env("DISCORD_WEBHOOK_URL")
