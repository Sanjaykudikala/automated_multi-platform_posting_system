import httpx
from typing import Dict, Any

from app.platforms.base import BasePlatform
from app.config import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USERNAME,
    REDDIT_PASSWORD,
    REDDIT_SUBREDDIT
)


class RedditPlatform(BasePlatform):
    name: str = "Reddit"

    async def post(self, message: str) -> Dict[str, Any]:
        if not all([
            REDDIT_CLIENT_ID,
            REDDIT_CLIENT_SECRET,
            REDDIT_USERNAME,
            REDDIT_PASSWORD,
            REDDIT_SUBREDDIT
        ]):
            raise ValueError("Reddit credentials or subreddit name are missing.")

        user_agent = f"AutomatedPostingSystem/1.0 by u/{REDDIT_USERNAME}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            auth_response = await client.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET),
                data={
                    "grant_type": "password",
                    "username": REDDIT_USERNAME,
                    "password": REDDIT_PASSWORD
                },
                headers={
                    "User-Agent": user_agent
                }
            )

            if auth_response.status_code >= 400:
                raise ValueError(f"Reddit authentication failed ({auth_response.status_code}): {auth_response.text}")

            auth_data = auth_response.json()
            if "error" in auth_data:
                raise ValueError(f"Reddit authentication error: {auth_data.get('error')}")

            token = auth_data.get("access_token")
            if not token:
                raise ValueError("Reddit authentication did not return an access token.")

            subreddit = REDDIT_SUBREDDIT.strip().lstrip("/").replace("r/", "")

            post_response = await client.post(
                "https://oauth.reddit.com/api/submit",
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": user_agent
                },
                data={
                    "api_type": "json",
                    "kind": "self",
                    "sr": subreddit,
                    "title": "Business Update & Opportunity",
                    "text": message
                }
            )

            if post_response.status_code >= 400:
                raise ValueError(f"Reddit post submission failed ({post_response.status_code}): {post_response.text}")

            result = post_response.json()
            errors = result.get("json", {}).get("errors", [])
            if errors:
                raise ValueError(f"Reddit rejected post submission: {errors}")

            post_url = result.get("json", {}).get("data", {}).get("url")
            if not post_url:
                raise ValueError("Reddit did not return a valid post URL.")

            return {
                "posted_url": post_url,
                "public_access": True
            }
