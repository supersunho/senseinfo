# backend/app/main.py
"""
FastAPI main application entry point.
Configures middleware, routers, and startup/shutdown events.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import sys
import os
import time
from datetime import datetime
# Add parent directory to path
sys.path.append(os.path.dirname(__file__))

from app.core.config import settings
from app.db.session import init_db
from app.api.routes import auth, system, channels, keywords, messages

# Import logger from utils, not core
from app.utils.logger import logger

# Create FastAPI app
app = FastAPI(
    title="InfoSense API",
    description="Telegram Channel Surveillance and Forwarding System",
    version="1.0.0",
    docs_url="/api/docs" if settings.environment == "development" else None,
    redoc_url="/api/redoc" if settings.environment == "development" else None,
    openapi_url="/api/openapi.json" if settings.environment == "development" else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(",") if hasattr(settings, 'allowed_origins') else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    logger.info(
        f"Incoming request: {request.method} {request.url.path} "
        f"from {request.client.host}"
    )
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Completed request: {request.method} {request.url.path} "
        f"status_code={response.status_code} duration={process_time:.3f}s"
    )
    
    return response

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        f"Unhandled exception: {exc} "
        f"path={request.url.path} method={request.method}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.environment == "development" else "An unexpected error occurred"
        }
    )

# Include routers
app.include_router(auth.router, prefix="/api/auth")
app.include_router(system.router, prefix="/api/system")
app.include_router(channels.router, prefix="/api")
app.include_router(keywords.router, prefix="/api")
app.include_router(messages.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting InfoSense application...")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")
        
        # Start message processors for authenticated users
        # This would typically be done per-user when they authenticate
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down InfoSense application...")
    
    try:
        # Stop all message processors
        from app.services.message_processor import processor_registry
        await processor_registry.stop_all()
        
        # Disconnect all Telegram clients
        from app.core.telegram_client import client_manager
        await client_manager.disconnect_all()
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
