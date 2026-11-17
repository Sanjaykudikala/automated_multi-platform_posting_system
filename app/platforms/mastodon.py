import httpx
from typing import Dict, Any

from app.platforms.base import BasePlatform
from app.config import MASTODON_INSTANCE, MASTODON_ACCESS_TOKEN


class MastodonPlatform(BasePlatform):
    name: str = "Mastodon"

    async def post(self, message: str) -> Dict[str, Any]:
        if not MASTODON_INSTANCE or not MASTODON_ACCESS_TOKEN:
            raise ValueError("Mastodon credentials (MASTODON_INSTANCE or MASTODON_ACCESS_TOKEN) are missing.")

        instance = MASTODON_INSTANCE.rstrip("/")
        if not instance.startswith("http://") and not instance.startswith("https://"):
            instance = f"https://{instance}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{instance}/api/v1/statuses",
                headers={
                    "Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}"
                },
                data={
                    "status": message,
                    "visibility": "public"
                }
            )

            if response.status_code >= 400:
                try:
                    err_msg = response.json().get("error") or response.text
                except Exception:
                    err_msg = response.text
                raise ValueError(f"Mastodon status update failed ({response.status_code}): {err_msg}")

            result = response.json()
            return {
                "posted_url": result.get("url"),
                "public_access": result.get("visibility") == "public"
            }
