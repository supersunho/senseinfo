# backend/tests/conftest.py
"""
Pytest configuration and fixtures for testing.
"""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.main import app
from app.db.base import Base
from app.core.config import settings


# Test database URL
TEST_DATABASE_URL = settings.database_url.replace(
    "infosense",
    "infosense_test"
).replace("postgresql://", "postgresql+asyncpg://")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Create test database tables before tests, drop after."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session() -> AsyncSession:
    """Create a fresh database session for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create session factory
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    
    # Create session
    session = async_session()
    
    try:
        yield session
    finally:
        await session.close()
    
    await engine.dispose()


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_telegram_client():
    """Mock TelegramClient for testing."""
    with patch('telethon.TelegramClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Configure mock methods
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.get_me = AsyncMock(return_value=Mock(id=12345, username="testuser"))
        mock_client.get_entity = AsyncMock(return_value=Mock(
            id=67890,
            username="testchannel",
            title="Test Channel",
            about="Test description"
        ))
        mock_client(JoinChannelRequest=AsyncMock())
        mock_client.run_until_disconnected = AsyncMock()
        
        yield mock_client


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('app.core.config.settings') as mock_settings:
        mock_settings.max_channels_per_account = 500
        mock_settings.max_keywords_per_channel = 100
        mock_settings.rate_limit_per_minute = 30
        mock_settings.get_proxy_list.return_value = []
        yield mock_settings


@pytest.fixture
def test_user_data():
    """Test user data fixture."""
    return {
        "telegram_id": 12345,
        "phone_number": "+821012345678",
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser"
    }


@pytest.fixture
def test_channel_data():
    """Test channel data fixture."""
    return {
        "id": 67890,
        "username": "testchannel",
        "title": "Test Channel",
        "description": "Test description"
    }


@pytest.fixture
def test_keyword_data():
    """Test keyword data fixture."""
    return {
        "word": "test_keyword",
        "is_inclusion": True,
        "is_active": True
    }
