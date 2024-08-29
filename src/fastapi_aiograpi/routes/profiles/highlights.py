from fastapi import APIRouter, HTTPException, Depends, Query, Path
from aiograpi import Client
import logging
import sentry_sdk
from ...utils.rate_limiter import rate_limiter
from ...utils.dependencies import get_client
from ...models.models import HighlightMedia, HighlightMediaResponse, MediaMetadata
from aiograpi.exceptions import ClientError, ClientLoginRequired
from sqlmodel import Session, select
from ...database.postgresql_handler import get_session


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{username}/highlight_media", response_model=HighlightMediaResponse)
async def get_highlight_media(
    username: str = Path(...),
    client: Client = Depends(get_client),
    session: Session = Depends(get_session),
    limit: int = Query(5, ge=1, le=20),
):
    try:
        rate_limiter.check_rate_limit(username)
        user_info = await client.user_info_by_username(username)
        user_id = user_info.pk

        # Fetch all grabbed highlights for this profile
        statement = select(MediaMetadata).where(MediaMetadata.user_id == user_id)
        stored_media_metadata = session.exec(statement).all()
        stored_media_ids = {media.media_id for media in stored_media_metadata}

        highlights = await client.user_highlights(user_id)
        filtered_highlights = [
            highlight
            for highlight in highlights
            if highlight.id not in stored_media_ids
        ]

        end_index = min(limit, len(filtered_highlights))

        highlight_media = []
        for highlight in filtered_highlights[:end_index]:
            media_urls = []
            for item in highlight.items:
                if item.video_url:
                    media_urls.append(item.video_url)
                elif item.thumbnail_url:
                    media_urls.append(item.thumbnail_url)

                # Store media metadata in PostgreSQL
                media_metadata = MediaMetadata(
                    media_id=highlight.id,
                    media_pk=highlight.pk,
                    url=item.video_url or item.thumbnail_url,
                    media_type=highlight.media_type,
                    product_type=highlight.product_type,
                    user_id=user_id,
                    username=username,
                    caption_text=highlight.caption_text,
                    like_count=highlight.like_count,
                    comment_count=highlight.comment_count,
                )
                session.add(media_metadata)

            highlight_media.append(
                HighlightMedia(highlight_id=highlight.id, media_urls=media_urls)
            )

        next_cursor = str(end_index) if end_index < len(filtered_highlights) else None

        session.commit()

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
