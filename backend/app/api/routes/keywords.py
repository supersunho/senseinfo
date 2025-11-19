# backend/app/api/routes/keywords.py
"""
Keyword management endpoints for channel filtering.
Handles CRUD operations for keywords and exclusion patterns.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from typing import List, Optional  
import logging
from datetime import datetime

from app.db.session import get_db
from app.core.rate_limiter import rate_limiter
from app.core.config import settings
from app.models.keyword import Keyword
from app.models.channel import Channel
from app.models.user import User
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/keywords", tags=["keywords"])


class KeywordCreateRequest(BaseModel):
    """Request model for keyword creation"""
    channel_id: int = Field(..., gt=0)
    word: str = Field(..., min_length=1, max_length=100)
    is_inclusion: bool = Field(default=True, description="True: inclusion, False: exclusion")


class KeywordResponse(BaseModel):
    """Response model for keyword operations"""
    id: int
    word: str
    is_inclusion: bool
    is_active: bool
    created_at: str


class KeywordListResponse(BaseModel):
    """Response model for keyword list"""
    keywords: List[KeywordResponse]
    total: int


@router.post("", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
async def add_keyword(
    request: KeywordCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> KeywordResponse:
    """Add a new keyword filter to a channel."""
    await rate_limiter.acquire(user.id)
    
    # Verify channel ownership
    result = await db.execute(
        select(Channel).where(
            Channel.id == request.channel_id,
            Channel.user_id == user.id,
            Channel.is_active == True
        )
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found or not owned by user"
        )
    
    # Check keyword limit
    keyword_count = await db.execute(
        select(Keyword).where(
            Keyword.channel_id == request.channel_id,
            Keyword.is_active == True
        )
    )
    active_keywords = len(keyword_count.scalars().all())
    
    if active_keywords >= settings.max_keywords_per_channel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum keywords per channel ({settings.max_keywords_per_channel}) reached"
        )
    
    # Check duplicate
    duplicate = await db.execute(
        select(Keyword).where(
            Keyword.channel_id == request.channel_id,
            Keyword.word == request.word,
            Keyword.is_inclusion == request.is_inclusion
        )
    )
    if duplicate.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Keyword already exists for this channel"
        )
    
    # Create keyword
    keyword = Keyword(
        channel_id=request.channel_id,
        word=request.word,
        is_inclusion=request.is_inclusion,
        is_active=True
    )
    
    db.add(keyword)
    await db.commit()
    await db.refresh(keyword)
    
    logger.info(f"User {user.id} added keyword '{request.word}' to channel {channel.id}")
    
    return KeywordResponse(
        id=keyword.id,
        word=keyword.word,
        is_inclusion=keyword.is_inclusion,
        is_active=keyword.is_active,
        created_at=keyword.created_at.isoformat()
    )


@router.get("", response_model=KeywordListResponse)
async def list_keywords(
    channel_id: Optional[int] = None,
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> KeywordListResponse:
    """List keywords for user's channels."""
    query = (
        select(Keyword)
        .join(Channel, Keyword.channel_id == Channel.id)
        .where(Channel.user_id == user.id)
    )
    
    if channel_id:
        query = query.where(Keyword.channel_id == channel_id)
    
    if not include_inactive:
        query = query.where(Keyword.is_active == True)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    keywords = result.scalars().all()
    
    keyword_responses = [
        KeywordResponse(
            id=kw.id,
            word=kw.word,
            is_inclusion=kw.is_inclusion,
            is_active=kw.is_active,
            created_at=kw.created_at.isoformat()
        )
        for kw in keywords
    ]
    
    # Get total count
    count_query = (
        select(Keyword)
        .join(Channel, Keyword.channel_id == Channel.id)
        .where(Channel.user_id == user.id)
    )
    if channel_id:
        count_query = count_query.where(Keyword.channel_id == channel_id)
    if not include_inactive:
        count_query = count_query.where(Keyword.is_active == True)
    
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())
    
    return KeywordListResponse(
        keywords=keyword_responses,
        total=total
    )


@router.delete("/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword(
    keyword_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> None:
    """Delete (deactivate) a keyword."""
    result = await db.execute(
        select(Keyword)
        .join(Channel, Keyword.channel_id == Channel.id)
        .where(
            Keyword.id == keyword_id,
            Channel.user_id == user.id
        )
    )
    keyword = result.scalar_one_or_none()
    
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found"
        )
    
    # Soft delete (deactivate)
    keyword.is_active = False
    await db.commit()
    
    logger.info(f"User {user.id} deactivated keyword {keyword.id}")


@router.put("/{keyword_id}/toggle", response_model=KeywordResponse)
async def toggle_keyword(
    keyword_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> KeywordResponse:
    """Toggle keyword active status."""
    result = await db.execute(
        select(Keyword)
        .join(Channel, Keyword.channel_id == Channel.id)
        .where(
            Keyword.id == keyword_id,
            Channel.user_id == user.id
        )
    )
    keyword = result.scalar_one_or_none()
    
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found"
        )
    
    keyword.is_active = not keyword.is_active
    await db.commit()
    await db.refresh(keyword)
    
    logger.info(f"User {user.id} toggled keyword {keyword.id} to {keyword.is_active}")
    
    return KeywordResponse(
        id=keyword.id,
        word=keyword.word,
        is_inclusion=keyword.is_inclusion,
        is_active=keyword.is_active,
        created_at=keyword.created_at.isoformat()
    )
