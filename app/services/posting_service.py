import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.platforms.base import BasePlatform
from app.platforms.bluesky import BlueskyPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.reddit import RedditPlatform
from app.platforms.telegram import TelegramPlatform
from app.platforms.discord import DiscordPlatform


def get_default_platforms() -> List[BasePlatform]:
    return [
        BlueskyPlatform(),
        MastodonPlatform(),
        RedditPlatform(),
        TelegramPlatform(),
        DiscordPlatform()
    ]


async def publish_to_all(
    message: str,
    platforms: Optional[List[BasePlatform]] = None
) -> List[Dict[str, Any]]:
    if platforms is None:
        platforms = get_default_platforms()

    async def publish_one(platform: BasePlatform) -> Dict[str, Any]:
        platform_name = getattr(platform, "name", platform.__class__.__name__.replace("Platform", ""))
        try:
            result = await platform.post(message)
            now = datetime.now().astimezone()

            return {
                "platform": platform_name,
                "status": "success",
                "posted_url": result.get("posted_url"),
                "public_access": bool(result.get("public_access", False)),
                "date": now.date().isoformat(),
                "time": now.strftime("%H:%M:%S"),
                "error": None
            }
        except Exception as error:
            return {
                "platform": platform_name,
                "status": "failed",
                "posted_url": None,
                "public_access": False,
                "date": None,
                "time": None,
                "error": str(error)
            }

    results = await asyncio.gather(
        *[publish_one(p) for p in platforms]
    )

    return list(results)
