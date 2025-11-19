# backend/app/api/dependencies.py
"""
Common dependencies for API routes.
Includes authentication, authorization, and database dependencies.
"""

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.core.telegram_client import client_manager
from app.core.config import settings
from app.utils.logger import logger


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from session token.
    In production, this should validate JWT from Authorization header.
    For development, using a simple token-based approach.
    
    Args:
        request: FastAPI Request object
        db: Database session
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If user not found or not authenticated
    """
    # Get token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.replace("Bearer ", "")
    
    # For development, using a simple user_id token
    # In production, decode JWT token here
    try:
        user_id = int(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )
    
    # Get user from database
    result = await db.execute(
        select(User).where(
            User.id == user_id,
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
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user


async def check_admin_permission(
    current_user: User = Depends(get_current_user)
) -> bool:
    """
    Check if current user has admin permissions.
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
    """
    try:
        if not user.session_string:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No active Telegram session. Please re-authenticate."
            )
        
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
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Telegram client for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram client initialization failed"
        )


# Simple dependency for database session
get_db_session = Depends(get_db)
