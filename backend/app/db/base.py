# backend/app/db/base.py
"""
SQLAlchemy base class and declarative base for all database models.
"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    Provides common functionality and metadata for all database tables.
    """
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )
