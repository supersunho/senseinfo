# backend/app/models/keyword.py
"""
Keyword model for storing filter keywords per channel.
"""

from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Keyword(Base):
    """
    Keyword model representing a filter keyword for a specific channel.
    Supports both inclusion and exclusion patterns.
    """
    __tablename__ = "keywords"
    
    id = Column(BigInteger, primary_key=True, index=True)
    word = Column(String(100), nullable=False, index=True)
    
    # Keyword type
    is_inclusion = Column(Boolean, default=True)  # True: include, False: exclude
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign key
    channel_id = Column(BigInteger, ForeignKey("channels.id"), nullable=False)
    
    # Relationships
    channel = relationship("Channel", back_populates="keywords")
    
    def __repr__(self) -> str:
        return f"<Keyword(id={self.id}, word='{self.word}', channel_id={self.channel_id})>"
