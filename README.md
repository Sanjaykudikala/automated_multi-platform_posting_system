# Multi-Platform Social Broadcaster

A lightweight Python service built with FastAPI that lets you push marketing announcements and updates out to multiple external networks in a single call.

---

## What It Does

Instead of writing custom scripts for each social network or forum, this service acts as a single gateway. Send a message to the endpoint, and it handles posting to five networks simultaneously:

- **Bluesky** (via AT Protocol)
- **Mastodon** (ActivityPub REST endpoint)
- **Reddit** (OAuth2 submit endpoint)
- **Telegram** (Bot API)
- **Discord** (Channel webhook)

Each network runs in its own isolated task. If one network is down, has bad credentials, or runs into rate limits, it fails gracefully on its own and lets the other networks finish cleanly.

---

## Content Rules

The system validates the submitted text before sending anything over the network:

- **Length**: Up to 200 characters total.
- **Single Link**: Every post must include exactly one web URL for the audience to follow. Posts without a link or with more than one link are rejected immediately.
- **URL Sanity Check**: Ensures the link points to a real web host and strips away any trailing sentence punctuation (like periods or commas) before validating.

---

## Project Layout

```
.
├── app/
│   ├── main.py                     # App factory and endpoint routing
│   ├── schemas.py                  # Request/response validation models
│   ├── config.py                   # Environment variable loader
│   ├── platforms/
│   │   ├── base.py                 # Common platform interface
│   │   ├── bluesky.py              # Bluesky session & record creation
│   │   ├── mastodon.py             # Mastodon status publishing
│   │   ├── reddit.py               # Reddit authentication & submit
│   │   ├── telegram.py             # Telegram bot dispatcher
│   │   └── discord.py              # Discord webhook sender
│   └── services/
│       └── posting_service.py      # Async multi-platform dispatcher
├── tests/
│   └── test_posting.py             # Automated unit and integration tests
├── .env.example                    # Environment template
├── .gitignore                      # Ignore rules
├── pytest.ini                      # Test runner config
├── requirements.txt                # Project dependencies
└── README.md
```

---

## Getting Started

### 1. Requirements
- Python 3.10 or newer
- Virtual environment (`venv`)

### 2. Setup

Clone the repository and jump into the directory:

```bash
git clone <your-repository-url>
cd "Automated Multi-Platform Posting System"
```

Create a virtual environment:

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Make a copy of `.env.example` named `.env`:

```bash
cp .env.example .env
```

Fill in the platform credentials you want to use:

```env
BLUESKY_HANDLE=your_handle.bsky.social
BLUESKY_PASSWORD=your_app_password

MASTODON_INSTANCE=https://mastodon.social
MASTODON_ACCESS_TOKEN=your_token

REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
REDDIT_SUBREDDIT=test

TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=@your_channel

DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

Any platform left blank will simply return a failed status noting missing credentials, without crashing the request or blocking other networks.

---

## Running the API

Start the server using Uvicorn on port 4000:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
```

- Live API docs (Swagger): [http://localhost:4000/docs](http://localhost:4000/docs)
- Health check: [http://localhost:4000/](http://localhost:4000/)

---

## Usage Examples

### Publishing a post

```bash
curl -X POST "http://localhost:4000/posting" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explore our updated platform and see how we help businesses grow: https://example.com"
  }'
```

#### Successful Response Sample

```json
{
  "success": true,
  "total_platforms": 5,
  "successful": 4,
  "failed": 1,
  "results": [
    {
      "platform": "Bluesky",
      "status": "success",
      "posted_url": "https://bsky.app/profile/user.bsky.social/post/3lbtest",
      "public_access": true,
      "date": "2026-11-17",
      "time": "14:20:00",
      "error": null
    },
    {
      "platform": "Mastodon",
      "status": "success",
      "posted_url": "https://mastodon.social/@user/113500000000",
      "public_access": true,
      "date": "2026-11-17",
      "time": "14:20:00",
      "error": null
    },
    {
      "platform": "Reddit",
      "status": "success",
      "posted_url": "https://www.reddit.com/r/test/comments/xyz123/update",
      "public_access": true,
      "date": "2026-11-17",
      "time": "14:20:01",
      "error": null
    },
    {
      "platform": "Telegram",
      "status": "success",
      "posted_url": "https://t.me/my_channel/101",
      "public_access": true,
      "date": "2026-11-17",
      "time": "14:20:01",
      "error": null
    },
    {
      "platform": "Discord",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Discord webhook URL is missing."
    }
  ]
}
```

---

## Testing

The project comes with a full test suite verifying message length boundaries, URL extraction, platform isolation, and HTTP status codes:

```bash
pytest
```

Output:
```
tests/test_posting.py ......................                             [100%]
============================== 22 passed in 2.80s ==============================
```
