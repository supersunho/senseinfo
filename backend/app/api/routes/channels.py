# backend/app/api/routes/channels.py
"""
Channel management endpoints for CRUD operations.
Handles joining, leaving, and monitoring Telegram channels.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import InputChannel, Channel as TelegramChannel
from telethon.errors import (
    InviteHashInvalidError,
    ChannelsTooMuchError,
    FloodWaitError,
    UsernameInvalidError,
    UsernameNotOccupiedError
)
import logging
from datetime import datetime
from typing import List, Optional

from app.db.session import get_db
from app.api.dependencies import get_telegram_client, get_current_user  # ← 여기서 import
from app.core.rate_limiter import rate_limiter
from app.core.config import settings
from app.models.channel import Channel
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/channels", tags=["channels"])


class ChannelCreateRequest(BaseModel):
    """Request model for channel creation"""
    username: str = Field(..., pattern=r"^@?[a-zA-Z0-9_]{5,32}$", description="Channel username with or without @")


class ChannelResponse(BaseModel):
    """Response model for channel operations"""
    id: int
    username: str
    title: str
    is_active: bool
    joined_at: str
    message_count: int


class ChannelListResponse(BaseModel):
    """Response model for channel list"""
    channels: List[ChannelResponse]
    total: int


@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def add_channel(
    request: ChannelCreateRequest,
    background_tasks: BackgroundTasks,
    client: TelegramClient = Depends(get_telegram_client),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> ChannelResponse:
    """Join a new Telegram channel and start monitoring."""
    await rate_limiter.acquire(user.id)
    
    # Check channel limit
    channel_count_result = await db.execute(
        select(Channel).where(
            Channel.user_id == user.id,
            Channel.is_active == True
        )
    )
    active_channels = len(channel_count_result.scalars().all())
    
    if active_channels >= settings.max_channels_per_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum channels per account ({settings.max_channels_per_account}) reached"
        )
    
    # Clean username
    username = request.username.replace("@", "")
    
    try:
        # Check if already monitoring
        existing = await db.execute(
            select(Channel).where(
                Channel.username == username,
                Channel.user_id == user.id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already monitoring this channel"
            )
        
        # Get channel entity from Telegram
        entity = await client.get_entity(f"@{username}")
        
        if not isinstance(entity, TelegramChannel):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Entity is not a channel"
            )
        
        # Join channel
        await client(JoinChannelRequest(entity))
        
        # Create channel record
        channel = Channel(
            id=entity.id,
            username=username,
            title=entity.title,
            description=getattr(entity, 'about', None),
            user_id=user.id,
            is_active=True,
            is_monitoring=True,
            joined_at=datetime.utcnow(),
            last_message_id=0,
            message_count=0,
            total_messages_processed=0
        )
        
        db.add(channel)
        await db.commit()
        await db.refresh(channel)
        
        logger.info(f"User {user.id} joined channel @{username}")
        
        return ChannelResponse(
            id=channel.id,
            username=f"@{channel.username}",
            title=channel.title,
            is_active=channel.is_active,
            joined_at=channel.joined_at.isoformat(),
            message_count=channel.message_count
        )
        
    except UsernameInvalidError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid channel username format"
        )
    except UsernameNotOccupiedError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel does not exist"
        )
    except ChannelsTooMuchError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot has joined too many channels"
        )
    except FloodWaitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limited. Wait {e.seconds} seconds"
        )
    except Exception as e:
        logger.error(f"Channel join error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join channel"
        )


@router.get("", response_model=ChannelListResponse)
async def list_channels(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> ChannelListResponse:
    """List all monitored channels for the current user."""
    query = select(Channel).where(Channel.user_id == user.id)
    
    if not include_inactive:
        query = query.where(Channel.is_active == True)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    channels = result.scalars().all()
    
    channel_responses = [
        ChannelResponse(
            id=ch.id,
            username=f"@{ch.username}",
            title=ch.title,
            is_active=ch.is_active,
            joined_at=ch.joined_at.isoformat(),
            message_count=ch.message_count
        )
        for ch in channels
    ]
    
    # Get total count
    count_query = select(Channel).where(Channel.user_id == user.id)
    if not include_inactive:
        count_query = count_query.where(Channel.is_active == True)
    
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())
    
    return ChannelListResponse(
        channels=channel_responses,
        total=total
    )


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> ChannelResponse:
    """Get details of a specific channel."""
    result = await db.execute(
        select(Channel).where(
            Channel.id == channel_id,
            Channel.user_id == user.id
        )
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    return ChannelResponse(
        id=channel.id,
        username=f"@{channel.username}",
        title=channel.title,
        is_active=channel.is_active,
        joined_at=channel.joined_at.isoformat(),
        message_count=channel.message_count
    )


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: int,
    client: TelegramClient = Depends(get_telegram_client),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> None:
    """Stop monitoring and leave a Telegram channel."""
    await rate_limiter.acquire(user.id)
    
    result = await db.execute(
        select(Channel).where(
            Channel.id == channel_id,
            Channel.user_id == user.id
        )
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    try:
        # Leave channel
        entity = await client.get_entity(f"@{channel.username}")
        await client(LeaveChannelRequest(entity))
        
        # Mark as inactive
        channel.is_active = False
        
        await db.commit()
        
        logger.info(f"User {user.id} left channel @{channel.username}")
        
    except Exception as e:
        logger.error(f"Channel leave error: {e}")
        # Still mark as inactive in database even if leave fails
        channel.is_active = False
        await db.commit()


@router.put("/{channel_id}/toggle", response_model=ChannelResponse)
async def toggle_channel_monitoring(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
) -> ChannelResponse:
    """Toggle channel monitoring status (active/inactive)."""
    result = await db.execute(
        select(Channel).where(
            Channel.id == channel_id,
            Channel.user_id == user.id
        )
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )
    
    channel.is_monitoring = not channel.is_monitoring
    await db.commit()
    await db.refresh(channel)
    
    logger.info(f"User {user.id} toggled monitoring for channel @{channel.username} to {channel.is_monitoring}")
    
    return ChannelResponse(
        id=channel.id,
        username=f"@{channel.username}",
        title=channel.title,
        is_active=channel.is_active,
        joined_at=channel.joined_at.isoformat(),
        message_count=channel.message_count
    )
