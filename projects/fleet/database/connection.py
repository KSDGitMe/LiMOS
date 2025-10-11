"""
Database Connection Management for Fleet Management API

Provides SQLite database connection and session management.
"""

import sqlite3
from typing import Generator
from pathlib import Path


# Database file path
DB_PATH = Path(__file__).parent.parent / "fleet_management.db"


def get_db_connection() -> sqlite3.Connection:
    """
    Get a database connection with proper configuration.

    Returns:
        sqlite3.Connection: Configured database connection
    """
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)  # Allow multi-threading for FastAPI
    conn.row_factory = sqlite3.Row  # Enable column access by name
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Dependency for FastAPI to get database connections.

    Yields:
        sqlite3.Connection: Database connection that will be automatically closed
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
