# backend/app/models/user.py
"""
User model for storing Telegram authentication and account information.
"""

from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func 
from app.db.base import Base


class User(Base):
    """
    User model representing a Telegram user account.
    Stores authentication state and account metadata.
    """
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    username = Column(String(100), unique=True, nullable=True)
    
    # Authentication
    is_authenticated = Column(Boolean, default=False)
    session_string = Column(Text, nullable=True)
    last_auth_date = Column(DateTime(timezone=True), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Rate limiting
    message_count_today = Column(BigInteger, default=0)
    last_message_date = Column(Date, nullable=True)
    
    # Relationships
    channels = relationship("Channel", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, phone='{self.phone_number}')>"
