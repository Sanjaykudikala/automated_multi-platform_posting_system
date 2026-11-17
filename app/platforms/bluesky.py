import httpx
from datetime import datetime, timezone
from typing import Dict, Any

from app.platforms.base import BasePlatform
from app.config import BLUESKY_HANDLE, BLUESKY_PASSWORD


class BlueskyPlatform(BasePlatform):
    name: str = "Bluesky"

    async def post(self, message: str) -> Dict[str, Any]:
        if not BLUESKY_HANDLE or not BLUESKY_PASSWORD:
            raise ValueError("Bluesky credentials (BLUESKY_HANDLE or BLUESKY_PASSWORD) are missing.")

        async with httpx.AsyncClient(timeout=20.0) as client:
            login_response = await client.post(
                "https://bsky.social/xrpc/com.atproto.server.createSession",
                json={
                    "identifier": BLUESKY_HANDLE,
                    "password": BLUESKY_PASSWORD
                }
            )

            if login_response.status_code >= 400:
                try:
                    err_msg = login_response.json().get("message") or login_response.text
                except Exception:
                    err_msg = login_response.text
                raise ValueError(f"Bluesky authentication failed ({login_response.status_code}): {err_msg}")

            session = login_response.json()
            access_jwt = session.get("accessJwt")
            did = session.get("did")

            if not access_jwt or not did:
                raise ValueError("Bluesky session tokens missing in response.")

            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            post_response = await client.post(
                "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                headers={
                    "Authorization": f"Bearer {access_jwt}"
                },
                json={
                    "repo": did,
                    "collection": "app.bsky.feed.post",
                    "record": {
                        "$type": "app.bsky.feed.post",
                        "text": message,
                        "createdAt": now_iso
                    }
                }
            )

            if post_response.status_code >= 400:
                try:
                    err_msg = post_response.json().get("message") or post_response.text
                except Exception:
                    err_msg = post_response.text
                raise ValueError(f"Bluesky post creation failed ({post_response.status_code}): {err_msg}")

            result = post_response.json()
            uri = result.get("uri", "")
            record_key = uri.split("/")[-1] if uri else ""

            if not record_key:
                raise ValueError("Bluesky response did not contain a valid record URI.")

            return {
                "posted_url": f"https://bsky.app/profile/{BLUESKY_HANDLE}/post/{record_key}",
                "public_access": True
            }
