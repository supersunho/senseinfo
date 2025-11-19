# backend/app/models/message.py
"""
Message model for storing forwarded/filtered Telegram messages.
"""

from sqlalchemy import Column, BigInteger, String, Text, BigInteger, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Message(Base):
    """
    Message model representing a stored Telegram message.
    Contains message content, metadata, and matching keyword information.
    """
    __tablename__ = "messages"
    
    id = Column(BigInteger, primary_key=True, index=True)
    telegram_message_id = Column(BigInteger, nullable=False, index=True)
    
    # Message content
    text = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    
    # Sender information
    sender_id = Column(BigInteger, nullable=True)
    sender_username = Column(String(100), nullable=True)
    sender_first_name = Column(String(100), nullable=True)
    sender_last_name = Column(String(100), nullable=True)
    
    # Media information
    media_type = Column(String(50), nullable=True)
    file_hash = Column(String(64), nullable=True)
    
    # Metadata
    message_date = Column(DateTime(timezone=True), nullable=False)
    edit_date = Column(DateTime(timezone=True), nullable=True)
    views = Column(BigInteger, default=0)
    forwards = Column(BigInteger, default=0)
    
    # Forwarding status
    is_forwarded = Column(Boolean, default=False)
    forwarded_at = Column(DateTime(timezone=True), nullable=True)
    forward_destination = Column(String(100), nullable=True)
    
    # Keywords that matched this message
    matched_keywords = Column(JSON, nullable=True)
    
    # Foreign keys
    channel_id = Column(BigInteger, ForeignKey("channels.id"), nullable=False)
    
    # Relationships
    channel = relationship("Channel", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, channel_id={self.channel_id}, date='{self.message_date}')>"
