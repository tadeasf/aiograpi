from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from aiograpi import Client
import logging
import sentry_sdk
from fastapi_aiograpi.routes.auth.auth import get_client

router = APIRouter()
logger = logging.getLogger(__name__)


class ProfileStats(BaseModel):
    posts_count: int
    reels_count: int
    highlights_count: int


@router.get("/{username}", response_model=ProfileStats)
async def get_profile_stats(username: str, client: Client = Depends(get_client)):
    try:
        user_info = await client.user_info_by_username(username)
        user_id = user_info.pk

        posts_count = user_info.media_count

        reels = await client.user_clips_v1(user_id, amount=1)
        reels_count = len(reels)

        highlights = await client.user_highlights(user_id)
        highlights_count = len(highlights)

        return ProfileStats(
            posts_count=posts_count,
            reels_count=reels_count,
            highlights_count=highlights_count,
        )
    except Exception as e:
        logger.exception(f"Error fetching profile stats for {username}: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching profile stats: {str(e)}",
        )
