import re
from typing import Literal, Optional, List
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    TypeAdapter
)


class PostingRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Post content up to 200 characters including a single web link.",
        json_schema_extra={
            "example": "Explore our updated platform and see how we help businesses grow: https://example.com"
        }
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, message: str) -> str:
        trimmed = message.strip()
        if not trimmed:
            raise ValueError("Message cannot be empty.")

        url_pattern = re.compile(
            r"(?:https?://|www\.)[^\s]+",
            re.IGNORECASE
        )
        urls = url_pattern.findall(message)

        if len(urls) == 0:
            raise ValueError("Your message needs to include a web link.")

        if len(urls) > 1:
            raise ValueError(
                f"Only one link is allowed per post, but {len(urls)} were detected."
            )

        raw_url = urls[0].rstrip(".,;:)]}!?\"'")
        test_url = f"https://{raw_url}" if raw_url.lower().startswith("www.") else raw_url

        try:
            parsed = TypeAdapter(HttpUrl).validate_python(test_url)
            if (
                not parsed.host
                or ".." in parsed.host
                or parsed.host.startswith(".")
                or parsed.host.endswith(".")
            ):
                raise ValueError("Invalid host.")
        except Exception:
            raise ValueError(f"The link '{raw_url}' does not appear to be a valid web address.")

        return message


class PlatformResult(BaseModel):
    platform: str
    status: Literal["success", "failed"]
    posted_url: Optional[str] = None
    public_access: bool = False
    date: Optional[str] = None
    time: Optional[str] = None
    error: Optional[str] = None


class PostingResponse(BaseModel):
    success: bool
    total_platforms: int
    successful: int
    failed: int
    results: List[PlatformResult]
