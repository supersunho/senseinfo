# backend/app/services/message_processor.py
"""
Message processing engine for monitoring channels and filtering messages.
Handles real-time message processing with keyword matching and forwarding.
"""

import asyncio
import logging
import re
from typing import List, Dict, Optional, Set
from datetime import datetime
from telethon import events
from telethon.errors import FloodWaitError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.telegram_client import client_manager
from app.core.rate_limiter import rate_limiter
from app.models.message import Message
from app.models.keyword import Keyword
from app.models.channel import Channel
from app.utils.logger import logger


class MessageProcessor:
    """
    Message processing engine that monitors channels and filters messages.
    Runs as a background task and processes messages in real-time.
    """
    
    def __init__(self, user_id: int, db_session: AsyncSession):
        self.user_id = user_id
        self.db = db_session
        self.client: Optional[TelegramClient] = None
        self.is_running = False
        self._event_handlers = []
        self._task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """
        Start the message processor.
        Initializes Telegram client and sets up event handlers.
        """
        if self.is_running:
            logger.warning(f"Message processor already running for user {self.user_id}")
            return
        
        try:
            # Get Telegram client
            self.client = await client_manager.get_client(
                user_id=self.user_id,
                api_id=settings.telegram_api_id,
                api_hash=settings.telegram_api_hash
            )
            
            # Get monitored channels
            result = await self.db.execute(
                select(Channel).where(
                    Channel.user_id == self.user_id,
                    Channel.is_active == True,
                    Channel.is_monitoring == True
                )
            )
            channels = result.scalars().all()
            
            if not channels:
                logger.info(f"No active channels to monitor for user {self.user_id}")
                return
            
            # Setup event handlers
            for channel in channels:
                await self._setup_channel_handler(channel)
            
            self.is_running = True
            self._task = asyncio.create_task(self._run())
            
            logger.info(f"Message processor started for user {self.user_id} with {len(channels)} channels")
            
        except Exception as e:
            logger.error(f"Failed to start message processor for user {self.user_id}: {e}")
            raise
    
    async def stop(self) -> None:
        """
        Stop the message processor.
        Removes event handlers and disconnects client.
        """
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel running task
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Remove event handlers
        for handler in self._event_handlers:
            self.client.remove_event_handler(handler)
        
        self._event_handlers.clear()
        logger.info(f"Message processor stopped for user {self.user_id}")
    
    async def _setup_channel_handler(self, channel: Channel) -> None:
        """
        Setup message handler for a specific channel.
        
        Args:
            channel: Channel model instance
        """
        # Get keywords for this channel
        result = await self.db.execute(
            select(Keyword).where(
                Keyword.channel_id == channel.id,
                Keyword.is_active == True
            )
        )
        keywords = result.scalars().all()
        
        if not keywords:
            logger.warning(f"No active keywords for channel {channel.username}, skipping")
            return
        
        inclusion_keywords = [kw.word for kw in keywords if kw.is_inclusion]
        exclusion_keywords = [kw.word for kw in keywords if not kw.is_inclusion]
        
        # Create handler function
        @events.register(events.NewMessage(chats=int(channel.id)))
        async def message_handler(event):
            await self._handle_message(
                event,
                channel,
                inclusion_keywords,
                exclusion_keywords
            )
        
        # Register handler
        self.client.add_event_handler(message_handler)
        self._event_handlers.append(message_handler)
        
        logger.debug(f"Setup handler for channel {channel.username} with {len(keywords)} keywords")
    
    async def _handle_message(
        self,
        event: events.NewMessage.Event,
        channel: Channel,
        inclusion_keywords: List[str],
        exclusion_keywords: List[str]
    ) -> None:
        """
        Handle incoming message from a channel.
        
        Args:
            event: New message event
            channel: Channel model instance
            inclusion_keywords: List of inclusion keywords
            exclusion_keywords: List of exclusion keywords
        """
        try:
            message = event.message
            
            # Skip empty messages
            if not message.text:
                return
            
            text = message.text.lower()
            
            # Check exclusion keywords first
            for keyword in exclusion_keywords:
                if keyword.lower() in text:
                    logger.debug(f"Message excluded by keyword '{keyword}'")
                    return
            
            # Check inclusion keywords
            matched_keywords = []
            for keyword in inclusion_keywords:
                if keyword.lower() in text:
                    matched_keywords.append(keyword)
            
            if not matched_keywords:
                logger.debug("No inclusion keywords matched")
                return
            
            # Create message record
            msg = Message(
                telegram_message_id=message.id,
                channel_id=channel.id,
                text=message.text,
                raw_text=message.text,
                sender_id=message.sender_id,
                sender_username=getattr(message.sender, 'username', None),
                sender_first_name=getattr(message.sender, 'first_name', None),
                sender_last_name=getattr(message.sender, 'last_name', None),
                message_date=message.date,
                edit_date=message.edit_date,
                views=message.views,
                forwards=message.forwards,
                media_type=str(type(message.media).__name__) if message.media else None,
                matched_keywords=matched_keywords,
                is_forwarded=False,
                forwarded_at=None,
                forward_destination=None
            )
            
            self.db.add(msg)
            
            # Update channel stats
            channel.message_count += 1
            channel.total_messages_processed += 1
            
            await self.db.commit()
            
            logger.info(
                f"Message {message.id} from channel {channel.username} "
                f"matched keywords: {matched_keywords}"
            )
            
            # Trigger forwarding if configured
            await self._forward_message(event, channel, matched_keywords)
            
        except Exception as e:
            logger.error(f"Error handling message from channel {channel.username}: {e}")
            await self.db.rollback()
    
    async def _forward_message(
        self,
        event: events.NewMessage.Event,
        channel: Channel,
        matched_keywords: List[str]
    ) -> None:
        """
        Forward message to configured destination if keywords match.
        
        Args:
            event: New message event
            channel: Channel model instance
            matched_keywords: List of matched keywords
        """
        # TODO: Implement forwarding logic
        # - Check forwarding rules for matched keywords
        # - Send message to destination
        # - Update message record with forwarding status
        pass
    
    async def _run(self) -> None:
        """
        Main processing loop.
        Keeps the client running and handles reconnections.
        """
        while self.is_running:
            try:
                if self.client and self.client.is_connected():
                    await asyncio.sleep(settings.message_process_interval)
                else:
                    logger.warning("Client disconnected, attempting reconnect")
                    await self.client.connect()
                    await asyncio.sleep(5)
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.error(f"Message processor error: {e}")
                await asyncio.sleep(10)
        
        logger.info(f"Message processor loop ended for user {self.user_id}")


# Message processor registry for managing multiple processors
class MessageProcessorRegistry:
    """
    Registry for managing multiple message processors (one per user).
    """
    
    def __init__(self):
        self.processors: Dict[int, MessageProcessor] = {}
        self._lock = asyncio.Lock()
    
    async def start_processor(self, user_id: int, db_session: AsyncSession) -> MessageProcessor:
        """
        Start a message processor for a user.
        
        Args:
            user_id: User identifier
            db_session: Database session
            
        Returns:
            Started message processor
        """
        async with self._lock:
            if user_id in self.processors:
                processor = self.processors[user_id]
                if not processor.is_running:
                    await processor.start()
                return processor
            
            processor = MessageProcessor(user_id, db_session)
            await processor.start()
            self.processors[user_id] = processor
            
            return processor
    
    async def stop_processor(self, user_id: int) -> None:
        """
        Stop a message processor for a user.
        
        Args:
            user_id: User identifier
        """
        async with self._lock:
            if user_id in self.processors:
                processor = self.processors[user_id]
                await processor.stop()
                del self.processors[user_id]
    
    async def stop_all(self) -> None:
        """Stop all message processors."""
        async with self._lock:
            user_ids = list(self.processors.keys())
            for user_id in user_ids:
                await self.stop_processor(user_id)


# Global registry instance
processor_registry = MessageProcessorRegistry()
