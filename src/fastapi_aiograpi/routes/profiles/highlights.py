from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel
from aiograpi import Client
import logging
import sentry_sdk
from typing import List, Optional
from ...utils.rate_limiter import rate_limiter
from ...utils.dependencies import get_client
import redis
import json
import os
from aiograpi.exceptions import ClientError, ClientLoginRequired

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Redis client
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=redis_host, port=6379, db=0)


class HighlightMedia(BaseModel):
    highlight_id: str
    media_urls: List[str]


class HighlightMediaResponse(BaseModel):
    highlights: List[HighlightMedia]
    next_cursor: Optional[str]


@router.get("/{username}/highlight_media", response_model=HighlightMediaResponse)
async def get_highlight_media(
    username: str = Path(...),
    client: Client = Depends(get_client),
    limit: int = Query(5, ge=1, le=20),
):
    try:
        rate_limiter.check_rate_limit(username)
        user_info = await client.user_info_by_username(username)
        user_id = user_info.pk

        # Check if we have stored progress for this user
        progress_key = f"highlight_progress:{username}"
        stored_progress = redis_client.get(progress_key)

        if stored_progress:
            progress = json.loads(stored_progress)
            start_index = progress["index"]
            highlights = progress["highlights"]
        else:
            start_index = 0
            highlights = await client.user_highlights(user_id)

        end_index = min(start_index + limit, len(highlights))

        highlight_media = []
        for highlight in highlights[start_index:end_index]:
            media_urls = []
            for item in highlight.items:
                if item.video_url:
                    media_urls.append(item.video_url)
                elif item.thumbnail_url:
                    media_urls.append(item.thumbnail_url)
            highlight_media.append(
                HighlightMedia(highlight_id=highlight.id, media_urls=media_urls)
            )

        next_cursor = str(end_index) if end_index < len(highlights) else None

        # Store progress in Redis
        progress = {"index": end_index, "highlights": highlights}
        redis_client.set(
            progress_key, json.dumps(progress), ex=3600
        )  # Expire after 1 hour

        return HighlightMediaResponse(
            highlights=highlight_media, next_cursor=next_cursor
        )
    except ClientLoginRequired:
        logger.error(f"Client not logged in for {username}")
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in.",
        )
    except ClientError as e:
        logger.error(f"Client error for {username}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Unable to fetch highlight media. The profile might be private or not exist.",
        )
    except Exception as e:
        logger.exception(f"Error fetching highlight media for {username}: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching highlight media: {str(e)}",
        )
