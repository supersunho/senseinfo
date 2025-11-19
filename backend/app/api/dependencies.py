# backend/app/api/dependencies.py
"""
FastAPI dependency functions for authentication, database, and client management.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
import logging
from app.db.session import get_db
from app.core.telegram_client import client_manager
from app.models.user import User

logger = logging.getLogger(__name__)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    telegram_id: int = None  # In production, extract from JWT token
) -> User:
    """
    Get current authenticated user from database.
    In production, this should decode JWT token and validate.
    
    Args:
        db: Database session
        telegram_id: Telegram user ID (temporary for development)
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If user not found or not authenticated
    """
    # TODO: Implement JWT token validation
    # For now, we'll use a simple telegram_id check
    
    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )
    
    return user


async def get_telegram_client(
    user: User = Depends(get_current_user)
):
    """
    Get Telegram client for authenticated user.
    
    Args:
        user: Authenticated user
        
    Returns:
        TelegramClient instance
        
    Raises:
        HTTPException: If client cannot be created or authorized
    """
    try:
        client = await client_manager.get_client(
            user_id=user.id,
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            session_string=user.session_string
        )
        return client
    except Exception as e:
        logger.error(f"Failed to get Telegram client for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram client error"
        )


# Import select for user query
from sqlalchemy import select
from app.core.config import settings
