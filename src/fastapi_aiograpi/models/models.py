from typing import Optional, List
from pydantic import BaseModel
from sqlmodel import SQLModel, Field


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    session_id: str


class HighlightMedia(BaseModel):
    highlight_id: str
    media_urls: List[str]


class HighlightMediaResponse(BaseModel):
    highlights: List[HighlightMedia]
    next_cursor: Optional[str]


class ProfileStats(BaseModel):
    username: str
    posts_count: int
    reels_count: int
    highlights_count: int
    follower_count: int
    following_count: int


class HighlightMedia(BaseModel):
    highlight_id: str
    media_urls: List[str]


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    session: Optional[str]
    proxy: Optional[str]
    password: Optional[str]


class MediaMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    media_id: str
    media_pk: int
    url: str
    media_type: int
    product_type: str
    user_id: int
    username: str
    caption_text: Optional[str]
    like_count: Optional[int]
    comment_count: Optional[int]
