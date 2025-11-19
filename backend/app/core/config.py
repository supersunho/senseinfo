# backend/app/core/config.py
"""
Configuration management for InfoSense application.
Uses Pydantic Settings for environment-based configuration with validation.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All sensitive data should be provided via environment variables or .env file.
    """
    
    # Telegram API Credentials
    telegram_api_id: int
    telegram_api_hash: str
    
    # Database Configuration
    database_url: str = "postgresql://infosense:changeme@localhost:5432/infosense"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Session Management
    session_directory: str = "./sessions"
    session_name_prefix: str = "infosense_session_"
    
    # Application Limits
    max_channels_per_account: int = 500
    max_keywords_per_channel: int = 100
    message_process_interval: int = 5  # seconds
    
    # Rate Limiting
    rate_limit_per_minute: int = 30
    
    # Proxy Configuration
    proxy_list: Optional[str] = None  # Comma-separated list of proxies
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_proxy_list(self) -> List[str]:
        """
        Parse comma-separated proxy list into list of proxy URLs.
        
        Returns:
            List of proxy URLs or empty list if not configured
        """
        if not self.proxy_list:
            return []
        return [proxy.strip() for proxy in self.proxy_list.split(",") if proxy.strip()]


# Global settings instance
settings = Settings()
