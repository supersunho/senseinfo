# backend/app/services/telegram_service.py
"""
Telegram service layer for business logic.
Handles complex operations involving multiple Telegram API calls.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import Channel, Message as TelegramMessage
from telethon.errors import (
    FloodWaitError,
    ChannelPrivateError,
    ChannelInvalidError,
    UsernameInvalidError
)
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.rate_limiter import rate_limiter
from app.utils.logger import logger

class TelegramService:
    """
    Service class for Telegram-related business logic.
    Provides high-level operations for channel and message management.
    """
    
    def __init__(self, client: TelegramClient, user_id: int):
        self.client = client
        self.user_id = user_id
    
    async def get_channel_info(self, username: str) -> Dict[str, Any]:
        """
        Get detailed information about a channel.
        
        Args:
            username: Channel username without @
            
        Returns:
            Dictionary with channel information
            
        Raises:
            Exception: If channel cannot be accessed
        """
        await rate_limiter.acquire(self.user_id)
        
        try:
            entity = await self.client.get_entity(f"@{username}")
            
            if not isinstance(entity, Channel):
                raise ValueError("Entity is not a channel")
            
            full_channel = await self.client(GetFullChannelRequest(entity))
            
            channel_info = {
                "id": entity.id,
                "username": username,
                "title": entity.title,
                "description": full_channel.full_chat.about,
                "participants_count": full_channel.full_chat.participants_count,
                "is_verified": entity.verified,
                "is_mega_group": entity.megagroup,
                "is_broadcast": entity.broadcast,
                "date_created": entity.date,
                "is_active": True
            }
            
            return channel_info
            
        except Exception as e:
            logger.error(f"Failed to get channel info for @{username}: {e}")
            raise
    
    async def get_recent_messages(
        self,
        channel_id: int,
        limit: int = 100,
        offset_id: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages from a channel.
        
        Args:
            channel_id: Channel ID
            limit: Number of messages to retrieve
            offset_id: Message ID to start from
            
        Returns:
            List of message dictionaries
            
        Raises:
            Exception: If messages cannot be fetched
        """
        await rate_limiter.acquire(self.user_id)
        
        try:
            entity = await self.client.get_entity(channel_id)
            
            # Get message history
            history = await self.client(GetHistoryRequest(
                peer=entity,
                limit=limit,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                max_id=0,
                min_id=0,
                hash=0
            ))
            
            messages = []
            for message in history.messages:
                if isinstance(message, TelegramMessage):
                    msg_dict = {
                        "id": message.id,
                        "text": message.message,
                        "date": message.date,
                        "sender_id": message.sender_id,
                        "views": message.views,
                        "forwards": message.forwards,
                        "reply_to_msg_id": message.reply_to_msg_id,
                        "media": message.media is not None,
                        "edit_date": message.edit_date
                    }
                    messages.append(msg_dict)
            
            return messages
            
        except ChannelPrivateError:
            raise HTTPException(status_code=403, detail="Channel is private")
        except ChannelInvalidError:
            raise HTTPException(status_code=404, detail="Channel not found")
        except Exception as e:
            logger.error(f"Failed to get messages for channel {channel_id}: {e}")
            raise
    
    async def search_messages(
        self,
        channel_id: int,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search messages in a channel for specific keywords.
        
        Args:
            channel_id: Channel ID
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching messages
        """
        # Note: Telegram API doesn't support server-side search in channels
        # This method fetches recent messages and filters locally
        messages = await self.get_recent_messages(channel_id, limit=200)
        
        filtered_messages = [
            msg for msg in messages
            if query.lower() in (msg.get("text") or "").lower()
        ]
        
        return filtered_messages[:limit]
    
    async def get_channel_stats(
        self,
        channel_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get statistics for a channel over past N days.
        
        Args:
            channel_id: Channel ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with channel statistics
        """
        await rate_limiter.acquire(self.user_id)
        
        try:
            messages = await self.get_recent_messages(
                channel_id,
                limit=1000
            )
            
            # Filter messages by date
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_messages = [
                msg for msg in messages
                if msg["date"] >= cutoff_date
            ]
            
            # Calculate statistics
            total_messages = len(recent_messages)
            total_views = sum(msg.get("views", 0) for msg in recent_messages)
            total_forwards = sum(msg.get("forwards", 0) for msg in recent_messages)
            
            # Get unique senders
            unique_senders = len(set(
                msg.get("sender_id") for msg in recent_messages
                if msg.get("sender_id")
            ))
            
            stats = {
                "channel_id": channel_id,
                "period_days": days,
                "total_messages": total_messages,
                "total_views": total_views,
                "total_forwards": total_forwards,
                "unique_senders": unique_senders,
                "average_views_per_message": round(total_views / max(total_messages, 1), 2),
                "average_forwards_per_message": round(total_forwards / max(total_messages, 1), 2)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats for channel {channel_id}: {e}")
            raise
    
    async def join_channels_batch(
        self,
        usernames: List[str],
        delay: float = 2.0
    ) -> Dict[str, Any]:
        """
        Join multiple channels with delay between each join.
        
        Args:
            usernames: List of channel usernames (without @)
            delay: Delay in seconds between joins
            
        Returns:
            Dictionary with success/failure counts
        """
        results = {
            "total": len(usernames),
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for username in usernames:
            try:
                await rate_limiter.acquire(self.user_id)
                
                entity = await self.client.get_entity(f"@{username}")
                await self.client(JoinChannelRequest(entity))
                
                results["success"] += 1
                logger.info(f"Successfully joined @{username}")
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "username": username,
                    "error": str(e)
                })
                logger.error(f"Failed to join @{username}: {e}")
            
            # Delay between joins
            if delay > 0:
                await asyncio.sleep(delay)
        
        return results


# Import required modules
from app.db.session import AsyncSession
from fastapi import HTTPException
