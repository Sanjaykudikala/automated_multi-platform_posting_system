from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import PostingRequest, PostingResponse
from app.services.posting_service import publish_to_all

app = FastAPI(
    title="Multi-Platform Social Broadcaster",
    description="Unified API service to broadcast short social updates and announcements across connected networks.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "Social Broadcaster API",
        "docs": "/docs"
    }


@app.post("/posting", response_model=PostingResponse)
async def create_post(request: PostingRequest):
    results = await publish_to_all(request.message)

    successful = sum(1 for result in results if result["status"] == "success")
    failed = len(results) - successful

    return {
        "success": successful > 0,
        "total_platforms": len(results),
        "successful": successful,
        "failed": failed,
        "results": results
    }
