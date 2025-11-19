# backend/app/api/dependencies.py
"""
Common dependencies for API routes.
Includes authentication, authorization, and database dependencies.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.core.telegram_client import client_manager
from app.utils.logger import logger


async def get_current_user(
    telegram_id: int = Depends(get_telegram_id_from_token),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from token.
    
    Args:
        telegram_id: Telegram ID from authentication token
        db: Database session
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If user not found or not authenticated
    """
    result = await db.execute(
        select(User).where(
            User.telegram_id == telegram_id,
            User.is_authenticated == True,
            User.is_active == True
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated or session expired"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (additional check on top of get_current_user).
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user


def get_telegram_id_from_token() -> int:
    """
    Extract Telegram ID from authentication token.
    In production, this would decode a JWT token.
    For now, using a simple implementation.
    
    Returns:
        Telegram ID as integer
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    # TODO: Implement proper JWT token decoding
    # For development, using a placeholder
    # In production, extract from Authorization header
    # token = request.headers.get("Authorization", "").replace("Bearer ", "")
    # payload = decode_jwt(token)
    # return payload.get("telegram_id")
    
    # Temporary implementation for development
    # Replace with actual token parsing logic
    return 12345  # Placeholder - replace with actual user ID extraction


async def check_admin_permission(
    current_user: User = Depends(get_current_user)
) -> bool:
    """
    Check if current user has admin permissions.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        True if user is admin
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    return True


async def get_telegram_client(
    user: User = Depends(get_current_user)
):
    """
    Get Telegram client for current user.
    
    Args:
        user: Current authenticated user
        
    Returns:
        TelegramClient instance
    """
    try:
        client = await client_manager.get_client(
            user_id=user.id,
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            session_string=user.session_string
        )
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize Telegram client"
            )
        
        return client
    
    except Exception as e:
        logger.error(f"Failed to get Telegram client for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram client initialization failed"
        )


# For routes that need database session
get_db_session = Depends(get_db)
