import httpx
from typing import Dict, Any

from app.platforms.base import BasePlatform
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramPlatform(BasePlatform):
    name: str = "Telegram"

    async def post(self, message: str) -> Dict[str, Any]:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            raise ValueError("Telegram credentials (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID) are missing.")

        api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                api_url,
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message
                }
            )

            if response.status_code >= 400:
                try:
                    err_desc = response.json().get("description") or response.text
                except Exception:
                    err_desc = response.text
                raise ValueError(f"Telegram API request failed ({response.status_code}): {err_desc}")

            result = response.json()
            if not result.get("ok"):
                raise ValueError(result.get("description", "Telegram message dispatch failed."))

            sent_message = result.get("result", {})
            message_id = sent_message.get("message_id")
            chat = sent_message.get("chat", {})
            username = chat.get("username")

            if username and message_id:
                posted_url = f"https://t.me/{username}/{message_id}"
                public_access = True
            else:
                posted_url = None
                public_access = False

            return {
                "posted_url": posted_url,
                "public_access": public_access
            }
