# backend/app/api/routes/messages.py
"""
Message management and retrieval endpoints.
Provides access to filtered and forwarded messages.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.db.session import get_db
from app.core.rate_limiter import rate_limiter
from app.models.message import Message
from app.models.channel import Channel
from app.models.user import User
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


class MessageResponse(BaseModel):
    """Response model for message operations"""
    id: int
    telegram_message_id: int
    text: Optional[str]
    sender_id: Optional[int]
    sender_username: Optional[str]
    message_date: str
    matched_keywords: List[str]
    is_forwarded: bool


class MessageListResponse(BaseModel):
    """Response model for message list"""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=MessageListResponse)
async def get_messages(
    channel_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    matched_keywords: Optional[str] = None,
    is_forwarded: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> MessageListResponse:
    """
    Get filtered messages for user's channels.
    
    Args:
        channel_id: Filter by specific channel
        start_date: Filter messages after this date
        end_date: Filter messages before this date
        matched_keywords: Comma-separated keywords to filter
        is_forwarded: Filter by forwarding status
        page: Page number for pagination
        page_size: Number of messages per page
        db: Database session
        user: Current authenticated user
        
    Returns:
        Paginated message list response
    """
    # Rate limiting
    await rate_limiter.acquire(user.id)
    
    # Base query
    query = (
        select(Message)
        .join(Channel, Message.channel_id == Channel.id)
        .where(Channel.user_id == user.id)
    )
    
    # Apply filters
    if channel_id:
        query = query.where(Message.channel_id == channel_id)
    
    if start_date:
        query = query.where(Message.message_date >= start_date)
    
    if end_date:
        query = query.where(Message.message_date <= end_date)
    
    if matched_keywords:
        keywords = matched_keywords.split(",")
        # This is a simplified implementation - in production use full-text search
        for keyword in keywords:
            query = query.where(Message.text.contains(keyword.strip()))
    
    if is_forwarded is not None:
        query = query.where(Message.is_forwarded == is_forwarded)
    
    # Order by date descending (newest first)
    query = query.order_by(desc(Message.message_date))
    
    # Get total count
    count_query = query.with_only_columns(func.count(Message.id))
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # Convert to response
    message_responses = [
        MessageResponse(
            id=msg.id,
            telegram_message_id=msg.telegram_message_id,
            text=msg.text,
            sender_id=msg.sender_id,
            sender_username=msg.sender_username,
            message_date=msg.message_date.isoformat(),
            matched_keywords=msg.matched_keywords or [],
            is_forwarded=msg.is_forwarded
        )
        for msg in messages
    ]
    
    return MessageListResponse(
        messages=message_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/stats", response_model=Dict[str, Any])
async def get_message_stats(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get message statistics for the last N days.
    
    Args:
        days: Number of days to analyze
        db: Database session
        user: Current authenticated user
        
    Returns:
        Statistics dictionary with counts and trends
    """
    await rate_limiter.acquire(user.id)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get message count
    count_query = (
        select(func.count(Message.id))
        .join(Channel, Message.channel_id == Channel.id)
        .where(
            Channel.user_id == user.id,
            Message.message_date >= start_date,
            Message.message_date <= end_date
        )
    )
    result = await db.execute(count_query)
    total_messages = result.scalar()
    
    # Get keyword match statistics
    keyword_query = (
        select(func.count(Message.id), func.array_agg(Message.matched_keywords))
        .join(Channel, Message.channel_id == Channel.id)
        .where(
            Channel.user_id == user.id,
            Message.matched_keywords.isnot(None),
            Message.message_date >= start_date,
            Message.message_date <= end_date
        )
    )
    kw_result = await db.execute(keyword_query)
    kw_data = kw_result.first()
    
    # Get channel statistics
    channel_query = (
        select(Channel.title, func.count(Message.id))
        .join(Message, Channel.id == Message.channel_id)
        .where(
            Channel.user_id == user.id,
            Message.message_date >= start_date,
            Message.message_date <= end_date
        )
        .group_by(Channel.id, Channel.title)
    )
    channel_result = await db.execute(channel_query)
    channel_stats = dict(channel_result.all())
    
    # Get forwarding statistics
    forward_query = (
        select(func.count(Message.id))
        .join(Channel, Message.channel_id == Channel.id)
        .where(
            Channel.user_id == user.id,
            Message.is_forwarded == True,
            Message.message_date >= start_date,
            Message.message_date <= end_date
        )
    )
    forward_result = await db.execute(forward_query)
    forwarded_count = forward_result.scalar()
    
    return {
        "period_days": days,
        "total_messages": total_messages,
        "forwarded_messages": forwarded_count,
        "keyword_matches": kw_data[0] if kw_data else 0,
        "channel_breakdown": channel_stats,
        "average_per_day": round(total_messages / days, 2) if days > 0 else 0
    }


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> None:
    """
    Delete a message from database.
    
    Args:
        message_id: Message ID to delete
        db: Database session
        user: Current authenticated user
        
    Raises:
        HTTPException: If message not found or not owned by user
    """
    result = await db.execute(
        select(Message)
        .join(Channel, Message.channel_id == Channel.id)
        .where(
            Message.id == message_id,
            Channel.user_id == user.id
        )
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    await db.delete(message)
    await db.commit()
    
    logger.info(f"User {user.id} deleted message {message_id}")


# Import required modules
from datetime import datetime, timedelta
from typing import Dict, Any, List
