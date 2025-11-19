# backend/app/api/routes/system.py
"""
System status and health check endpoints.
Provides monitoring information about the application state.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis import Redis
import logging
from app.db.session import get_db
from app.core.config import settings
from app.core.telegram_client import client_manager
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status", response_model=Dict[str, Any])
async def get_system_status(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """
    Get comprehensive system status including database, Redis, and Telegram.
    
    Returns:
        Dictionary containing status of all system components
    """
    status_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "version": "1.0.0"
    }
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        await db.commit()
        status_data["database"] = {
            "status": "healthy",
            "latency_ms": 0  # Could measure actual query time
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        status_data["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Redis
    try:
        redis.ping()
        status_data["redis"] = {
            "status": "healthy",
            "info": redis.info("server")
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        status_data["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Telegram API credentials
    if settings.telegram_api_id and settings.telegram_api_hash:
        status_data["telegram"] = {
            "status": "configured",
            "api_id_configured": True,
            "api_hash_configured": True
        }
    else:
        status_data["telegram"] = {
            "status": "
