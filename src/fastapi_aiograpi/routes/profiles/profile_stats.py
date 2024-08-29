import asyncio
from fastapi import APIRouter, Depends, Path, HTTPException
from aiograpi import Client
from aiograpi.exceptions import ClientLoginRequired, ClientError
from ...models.models import ProfileStats
from ...utils.dependencies import get_client
from ...utils.rate_limiter import rate_limiter
import sentry_sdk
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


async def retry_with_backoff(func, max_retries=3, initial_delay=5):
    for attempt in range(max_retries):
        try:
            return await func()
        except ClientError as e:  # noqa: F841
            if attempt == max_retries - 1:
                raise
            delay = initial_delay * (2**attempt)
            logger.warning(f"API error. Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
    raise HTTPException(
        status_code=429, detail="Too many requests. Please try again later."
    )


@router.get("/{username}", response_model=ProfileStats)
async def get_profile_stats(
    username: str = Path(...), client: Client = Depends(get_client)
):
    try:
        # Check rate limit before processing the request
        rate_limiter.check_rate_limit(username)

        async def fetch_user_info():
            return await client.user_info_by_username(username)

        user_info = await retry_with_backoff(fetch_user_info)
        user_id = user_info.pk

        posts_count = user_info.media_count
        follower_count = user_info.follower_count
        following_count = user_info.following_count

        async def fetch_user_medias():
            return await client.user_medias(user_id, amount=1)

        user_medias = await retry_with_backoff(fetch_user_medias)
        reels_count = sum(
            1
            for media in user_medias
            if media.media_type == 2 and media.product_type == "clips"
        )

        return ProfileStats(
            username=username,
            posts_count=posts_count,
            reels_count=reels_count,
            highlights_count=0,  # We'll need to implement this separately if needed
            follower_count=follower_count,
            following_count=following_count,
        )
    except HTTPException as e:
        # This will catch the rate limit exception from our RateLimiter
        logger.warning(f"Rate limit reached for {username}: {str(e)}")
        raise
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
            detail="Unable to fetch profile stats. The profile might be private or not exist.",
        )
    except Exception as e:
        logger.exception(f"Error fetching profile stats for {username}: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching profile stats. Please try again later.",
        )
