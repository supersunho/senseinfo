# backend/app/core/telegram_client.py
"""
Telegram client manager for handling multiple user sessions.
Provides connection pooling, session persistence, and error handling.
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    FloodWaitError,
    PhoneNumberInvalidError,
    ApiIdInvalidError,
    AuthKeyError,
    SessionPasswordNeededError,
    CodeInvalidError,
    PasswordHashInvalidError
)
from app.core.config import settings
from app.core.proxy_manager import proxy_manager

logger = logging.getLogger(__name__)


class TelegramClientManager:
    """
    Manages multiple TelegramClient instances for different users.
    Handles session persistence, reconnection, and cleanup.
    """
    
    def __init__(self, session_directory: str = settings.session_directory):
        self.session_directory = session_directory
        self.clients: Dict[int, TelegramClient] = {}
        self._lock = asyncio.Lock()
        self._proxy_iterator = None
        
        # Initialize proxy iterator if proxies are configured
        if settings.get_proxy_list():
            self._proxy_iterator = proxy_manager.get_proxy_iterator()
    
    async def get_client(self, user_id: int, api_id: int, api_hash: str, session_string: Optional[str] = None) -> TelegramClient:
        """
        Get or create a TelegramClient instance for a user.
        
        Args:
            user_id: User identifier
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_string: Optional session string for authentication
            
        Returns:
            Authenticated TelegramClient instance
            
        Raises:
            Exception: If authentication fails or client cannot be created
        """
        async with self._lock:
            # Return existing client if available and connected
            if user_id in self.clients:
                client = self.clients[user_id]
                if client.is_connected():
                    return client
                
                # Reconnect if disconnected
                try:
                    await client.connect()
                    if await client.is_user_authorized():
                        return client
                except Exception as e:
                    logger.warning(f"Failed to reconnect existing client for user {user_id}: {e}")
                    del self.clients[user_id]
            
            # Get next proxy from rotation
            proxy = next(self._proxy_iterator) if self._proxy_iterator else None
            
            # Create new client
            session_path = f"{self.session_directory}/user_{user_id}.session"
            
            try:
                client = TelegramClient(
                    session=session_path,
                    api_id=api_id,
                    api_hash=api_hash,
                    proxy=proxy,
                    base_logger=logger
                )
                
                await client.connect()
                
                # Check authorization
                if not await client.is_user_authorized():
                    if session_string:
                        # Try to authenticate using session string
                        session = StringSession(session_string)
                        client = TelegramClient(
                            session=session,
                            api_id=api_id,
                            api_hash=api_hash,
                            proxy=proxy
                        )
                        await client.connect()
                    else:
                        raise Exception("Client not authorized and no session string provided")
                
                # Verify connection
                me = await client.get_me()
                logger.info(f"Telegram client authenticated for user {user_id}: {me.id}")
                
                self.clients[user_id] = client
                return client
                
            except Exception as e:
                logger.error(f"Failed to create Telegram client for user {user_id}: {e}")
                raise
    
    async def disconnect_client(self, user_id: int) -> None:
        """
        Disconnect and remove a client from the manager.
        
        Args:
            user_id: User identifier to disconnect
        """
        async with self._lock:
            if user_id in self.clients:
                client = self.clients[user_id]
                try:
                    await client.disconnect()
                    logger.info(f"Disconnected Telegram client for user {user_id}")
                except Exception as e:
                    logger.warning(f"Error disconnecting client for user {user_id}: {e}")
                finally:
                    del self.clients[user_id]
    
    async def disconnect_all(self) -> None:
        """
        Disconnect all clients and clear the manager.
        """
        async with self._lock:
            user_ids = list(self.clients.keys())
            for user_id in user_ids:
                await self.disconnect_client(user_id)
            logger.info("All Telegram clients disconnected")
    
    async def get_session_string(self, user_id: int) -> Optional[str]:
        """
        Get session string for a user if client exists.
        
        Args:
            user_id: User identifier
            
        Returns:
            Session string or None if client not found
        """
        async with self._lock:
            if user_id in self.clients:
                client = self.clients[user_id]
                return StringSession.save(client.session)
            return None


# Global client manager instance
client_manager = TelegramClientManager()
