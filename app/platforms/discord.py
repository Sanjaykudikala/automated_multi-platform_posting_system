import httpx
from typing import Dict, Any

from app.platforms.base import BasePlatform
from app.config import DISCORD_WEBHOOK_URL


class DiscordPlatform(BasePlatform):
    name: str = "Discord"

    async def post(self, message: str) -> Dict[str, Any]:
        if not DISCORD_WEBHOOK_URL:
            raise ValueError("Discord webhook URL is missing.")

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                DISCORD_WEBHOOK_URL,
                params={"wait": "true"},
                json={
                    "content": message,
                    "allowed_mentions": {
                        "parse": []
                    }
                }
            )

            if response.status_code >= 400:
                try:
                    err_msg = response.json().get("message") or response.text
                except Exception:
                    err_msg = response.text
                raise ValueError(f"Discord webhook error ({response.status_code}): {err_msg}")

            result = response.json()
            guild_id = result.get("guild_id")
            channel_id = result.get("channel_id")
            message_id = result.get("id")

            if channel_id and message_id:
                guild_ref = guild_id if guild_id else "@me"
                posted_url = f"https://discord.com/channels/{guild_ref}/{channel_id}/{message_id}"
            else:
                posted_url = None

            return {
                "posted_url": posted_url,
                "public_access": False
            }
