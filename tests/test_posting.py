import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas import PostingRequest
from app.services.posting_service import publish_to_all
from app.platforms.base import BasePlatform
from app.platforms.bluesky import BlueskyPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.reddit import RedditPlatform
from app.platforms.telegram import TelegramPlatform
from app.platforms.discord import DiscordPlatform


client = TestClient(app)


def test_valid_message_single_url():
    msg = "Check out our latest business platform and grow your online visibility. https://example.com"
    req = PostingRequest(message=msg)
    assert req.message == msg


def test_valid_message_with_url_trailing_punctuation():
    msg = "Visit our service at https://example.com/landing?ref=promo. It is fast!"
    req = PostingRequest(message=msg)
    assert "https://example.com" in req.message


def test_valid_message_exact_200_chars():
    prefix = "A" * (200 - len(" https://example.com"))
    msg = f"{prefix} https://example.com"
    assert len(msg) == 200
    req = PostingRequest(message=msg)
    assert len(req.message) == 200


def test_invalid_message_exceeding_200_chars():
    prefix = "A" * 200
    msg = f"{prefix} https://example.com"
    with pytest.raises(ValidationError) as exc_info:
        PostingRequest(message=msg)
    errors = str(exc_info.value)
    assert "String should have at most 200 characters" in errors or "200" in errors


def test_invalid_message_no_url():
    msg = "Check out our latest business platform and grow your online visibility."
    with pytest.raises(ValidationError) as exc_info:
        PostingRequest(message=msg)
    assert "needs to include a web link" in str(exc_info.value).lower()


def test_invalid_message_multiple_urls():
    msg = "Visit https://first.com and also check https://second.com for info!"
    with pytest.raises(ValidationError) as exc_info:
        PostingRequest(message=msg)
    assert "only one link is allowed" in str(exc_info.value).lower()


def test_invalid_message_malformed_url():
    msg = "Check out https://..invalid..domain for details"
    with pytest.raises(ValidationError) as exc_info:
        PostingRequest(message=msg)
    assert "valid web address" in str(exc_info.value).lower() or "link" in str(exc_info.value).lower()


def test_invalid_message_empty_or_whitespace():
    with pytest.raises(ValidationError):
        PostingRequest(message="")

    with pytest.raises(ValidationError):
        PostingRequest(message="    ")


@pytest.mark.asyncio
async def test_bluesky_missing_credentials():
    with patch("app.platforms.bluesky.BLUESKY_HANDLE", None), \
         patch("app.platforms.bluesky.BLUESKY_PASSWORD", None):
        platform = BlueskyPlatform()
        with pytest.raises(ValueError, match="Bluesky credentials"):
            await platform.post("Test message https://example.com")


@pytest.mark.asyncio
async def test_bluesky_successful_post():
    with patch("app.platforms.bluesky.BLUESKY_HANDLE", "user.bsky.social"), \
         patch("app.platforms.bluesky.BLUESKY_PASSWORD", "secret123"):
        platform = BlueskyPlatform()

        mock_login_resp = MagicMock()
        mock_login_resp.status_code = 200
        mock_login_resp.json.return_value = {
            "accessJwt": "jwt_token_123",
            "did": "did:plc:test12345"
        }

        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {
            "uri": "at://did:plc:test12345/app.bsky.feed.post/3lbtest789"
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=[mock_login_resp, mock_post_resp]):
            res = await platform.post("Hello Bluesky https://example.com")
            assert res["posted_url"] == "https://bsky.app/profile/user.bsky.social/post/3lbtest789"
            assert res["public_access"] is True


@pytest.mark.asyncio
async def test_mastodon_successful_post():
    with patch("app.platforms.mastodon.MASTODON_INSTANCE", "https://mastodon.social"), \
         patch("app.platforms.mastodon.MASTODON_ACCESS_TOKEN", "token_123"):
        platform = MastodonPlatform()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "url": "https://mastodon.social/@user/1234567890",
            "visibility": "public"
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            res = await platform.post("Hello Mastodon https://example.com")
            assert res["posted_url"] == "https://mastodon.social/@user/1234567890"
            assert res["public_access"] is True


@pytest.mark.asyncio
async def test_mastodon_missing_credentials():
    with patch("app.platforms.mastodon.MASTODON_INSTANCE", None):
        platform = MastodonPlatform()
        with pytest.raises(ValueError, match="Mastodon credentials"):
            await platform.post("Test https://example.com")


@pytest.mark.asyncio
async def test_reddit_successful_post():
    with patch("app.platforms.reddit.REDDIT_CLIENT_ID", "cid"), \
         patch("app.platforms.reddit.REDDIT_CLIENT_SECRET", "csec"), \
         patch("app.platforms.reddit.REDDIT_USERNAME", "testuser"), \
         patch("app.platforms.reddit.REDDIT_PASSWORD", "pwd"), \
         patch("app.platforms.reddit.REDDIT_SUBREDDIT", "test"):
        platform = RedditPlatform()

        mock_auth = MagicMock()
        mock_auth.status_code = 200
        mock_auth.json.return_value = {"access_token": "reddit_token"}

        mock_submit = MagicMock()
        mock_submit.status_code = 200
        mock_submit.json.return_value = {
            "json": {
                "errors": [],
                "data": {"url": "https://www.reddit.com/r/test/comments/abc123/post"}
            }
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=[mock_auth, mock_submit]):
            res = await platform.post("Hello Reddit https://example.com")
            assert res["posted_url"] == "https://www.reddit.com/r/test/comments/abc123/post"
            assert res["public_access"] is True


@pytest.mark.asyncio
async def test_reddit_missing_credentials():
    with patch("app.platforms.reddit.REDDIT_CLIENT_ID", None):
        platform = RedditPlatform()
        with pytest.raises(ValueError, match="Reddit credentials"):
            await platform.post("Test https://example.com")


@pytest.mark.asyncio
async def test_telegram_successful_post_public_channel():
    with patch("app.platforms.telegram.TELEGRAM_BOT_TOKEN", "123:ABC"), \
         patch("app.platforms.telegram.TELEGRAM_CHAT_ID", "@public_chan"):
        platform = TelegramPlatform()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "ok": True,
            "result": {
                "message_id": 42,
                "chat": {"username": "public_chan"}
            }
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            res = await platform.post("Hello Telegram https://example.com")
            assert res["posted_url"] == "https://t.me/public_chan/42"
            assert res["public_access"] is True


@pytest.mark.asyncio
async def test_telegram_private_chat():
    with patch("app.platforms.telegram.TELEGRAM_BOT_TOKEN", "123:ABC"), \
         patch("app.platforms.telegram.TELEGRAM_CHAT_ID", "-100123456"):
        platform = TelegramPlatform()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "ok": True,
            "result": {
                "message_id": 99,
                "chat": {"id": -100123456}
            }
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            res = await platform.post("Private update https://example.com")
            assert res["posted_url"] is None
            assert res["public_access"] is False


@pytest.mark.asyncio
async def test_discord_successful_post():
    with patch("app.platforms.discord.DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/123/token"):
        platform = DiscordPlatform()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "111222333",
            "channel_id": "444555666",
            "guild_id": "777888999"
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            res = await platform.post("Hello Discord https://example.com")
            assert res["posted_url"] == "https://discord.com/channels/777888999/444555666/111222333"
            assert res["public_access"] is False


class MockSuccessPlatform(BasePlatform):
    def __init__(self, name: str):
        self.name = name

    async def post(self, message: str):
        return {
            "posted_url": f"https://{self.name.lower()}.com/post/999",
            "public_access": True
        }


class MockFailingPlatform(BasePlatform):
    def __init__(self, name: str, error_msg: str = "Auth error"):
        self.name = name
        self.error_msg = error_msg

    async def post(self, message: str):
        raise RuntimeError(self.error_msg)


@pytest.mark.asyncio
async def test_publish_to_all_independent_failure_isolation():
    platforms = [
        MockSuccessPlatform("Platform1"),
        MockFailingPlatform("Platform2", "Connection refused"),
        MockSuccessPlatform("Platform3"),
        MockFailingPlatform("Platform4", "Rate limited"),
        MockSuccessPlatform("Platform5"),
    ]

    results = await publish_to_all("Test message https://example.com", platforms=platforms)

    assert len(results) == 5
    assert results[0]["platform"] == "Platform1"
    assert results[0]["status"] == "success"
    assert results[0]["posted_url"] == "https://platform1.com/post/999"
    assert results[0]["public_access"] is True
    assert results[0]["date"] is not None
    assert results[0]["time"] is not None
    assert results[0]["error"] is None

    assert results[1]["platform"] == "Platform2"
    assert results[1]["status"] == "failed"
    assert results[1]["posted_url"] is None
    assert results[1]["public_access"] is False
    assert results[1]["date"] is None
    assert results[1]["time"] is None
    assert "Connection refused" in results[1]["error"]

    assert results[2]["platform"] == "Platform3"
    assert results[2]["status"] == "success"


def test_health_check_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_api_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200


def test_post_posting_endpoint_success():
    mock_results = [
        {
            "platform": "Bluesky",
            "status": "success",
            "posted_url": "https://bsky.app/profile/user/post/123",
            "public_access": True,
            "date": "2026-11-17",
            "time": "14:00:00",
            "error": None
        },
        {
            "platform": "Discord",
            "status": "failed",
            "posted_url": None,
            "public_access": False,
            "date": None,
            "time": None,
            "error": "Discord webhook URL is missing."
        }
    ]

    with patch("app.main.publish_to_all", new=AsyncMock(return_value=mock_results)):
        payload = {
            "message": "Check out our latest business platform and grow your online visibility. https://example.com"
        }
        response = client.post("/posting", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_platforms"] == 2
        assert data["successful"] == 1
        assert data["failed"] == 1
        assert len(data["results"]) == 2
        assert data["results"][0]["platform"] == "Bluesky"
        assert data["results"][0]["status"] == "success"
        assert data["results"][1]["platform"] == "Discord"
        assert data["results"][1]["status"] == "failed"


def test_post_posting_validation_errors():
    long_msg = "A" * 210 + " https://example.com"
    resp = client.post("/posting", json={"message": long_msg})
    assert resp.status_code == 422

    no_url_msg = "Just a short message without any link."
    resp = client.post("/posting", json={"message": no_url_msg})
    assert resp.status_code == 422

    multi_url_msg = "Check https://first.com and also https://second.com"
    resp = client.post("/posting", json={"message": multi_url_msg})
    assert resp.status_code == 422

    resp = client.post("/posting", json={})
    assert resp.status_code == 422
