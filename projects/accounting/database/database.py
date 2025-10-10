"""
Database Configuration and Session Management

This module handles SQLAlchemy database engine creation, session management,
and provides utilities for database operations.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from .models import Base

# Database configuration
DATABASE_DIR = Path(__file__).parent.parent / "data"
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_PATH = DATABASE_DIR / "accounting.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine with connection pooling for SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite with FastAPI
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """
    Initialize the database by creating all tables.
    This should be called on application startup.
    """
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized at: {DATABASE_PATH}")


def drop_database():
    """
    Drop all tables in the database.
    WARNING: This will delete all data!
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped!")


def reset_database():
    """
    Reset the database by dropping and recreating all tables.
    WARNING: This will delete all data!
    """
    print("🔄 Resetting database...")
    drop_database()
    init_database()
    print("✅ Database reset complete!")


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Ensures proper session cleanup and commit/rollback handling.

    Usage:
        with get_db() as db:
            # perform database operations
            db.add(obj)
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to inject database sessions.

    Usage in FastAPI:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db_session)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Utility functions for common operations

def get_or_create(db: Session, model, **kwargs):
    """
    Get an existing record or create a new one if it doesn't exist.

    Args:
        db: Database session
        model: SQLAlchemy model class
        **kwargs: Filter criteria

    Returns:
        Tuple of (instance, created) where created is True if new instance was created
    """
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        db.add(instance)
        db.flush()
        return instance, True


def bulk_insert(db: Session, instances: list):
    """
    Bulk insert multiple instances efficiently.

    Args:
        db: Database session
        instances: List of SQLAlchemy model instances
    """
    db.bulk_save_objects(instances)
    db.commit()


def count_records(db: Session, model, **filters):
    """
    Count records matching the given filters.

    Args:
        db: Database session
        model: SQLAlchemy model class
        **filters: Filter criteria

    Returns:
        Count of matching records
    """
    query = db.query(model)
    if filters:
        query = query.filter_by(**filters)
    return query.count()
