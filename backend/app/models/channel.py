# backend/app/models/channel.py
"""
Channel model for storing monitored Telegram channels.
"""

from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Channel(Base):
    """
    Channel model representing a monitored Telegram channel.
    Stores channel metadata and monitoring configuration.
    """
    __tablename__ = "channels"
    
    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Monitoring status
    is_active = Column(Boolean, default=True)
    is_monitoring = Column(Boolean, default=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Message tracking
    last_message_id = Column(BigInteger, default=0)
    message_count = Column(Integer, default=0)
    total_messages_processed = Column(BigInteger, default=0)
    
    # Foreign key
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="channels")
    keywords = relationship("Keyword", back_populates="channel", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="channel", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, username='{self.username}', active={self.is_active})>"
