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
from datetime import datetime
from typing import Dict, Any

from app.db.session import get_db
from app.core.config import settings
from app.core.redis import get_redis
from app.api.dependencies import check_admin_permission

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
            "status": "healthy"
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
            "status": "healthy"
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
            "status": "not_configured",
            "api_id_configured": bool(settings.telegram_api_id),
            "api_hash_configured": bool(settings.telegram_api_hash)
        }
    
    # Overall status
    components = ["database", "redis", "telegram"]
    healthy_count = sum(
        1 for comp in components
        if status_data.get(comp, {}).get("status") == "healthy" or status_data.get(comp, {}).get("status") == "configured"
    )
    
    status_data["overall"] = {
        "status": "healthy" if healthy_count == len(components) else "degraded",
        "healthy_components": healthy_count,
        "total_components": len(components)
    }
    
    return status_data


@router.post("/init-db", status_code=status.HTTP_201_CREATED)
async def initialize_database(
    db: AsyncSession = Depends(get_db),
    authorized: bool = Depends(check_admin_permission)
) -> Dict[str, str]:
    """
    Initialize database by creating all tables.
    Requires admin permission.
    
    Returns:
        Success message with initialization timestamp
    """
    try:
        from app.db.base import Base
        from app.db.session import engine
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
        return {
            "status": "success",
            "message": "Database tables created",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database initialization failed: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Simple health check endpoint for load balancers.
    
    Returns:
        OK status if service is running
    """
    return {"status": "ok"}


@router.get("/metrics")
async def get_metrics(
    authorized: bool = Depends(check_admin_permission)
) -> Dict[str, Any]:
    """
    Get application metrics for monitoring.
    Requires admin permission.
    
    Returns:
        Dictionary containing various metrics
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "active_clients": 0,  # This would be populated from actual data
            # Add more metrics here
        }
    }
