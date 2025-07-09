"""
Database connection management for Business Document PDF Parser

Provides database connectivity using SQLAlchemy with SQLite.
"""

import os
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Optional, Dict, Any

# Import centralized configuration
try:
    from ..config import DATABASE_PATH
except ImportError:
    # Fallback for when running as script
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config import DATABASE_PATH


# Global variables for database connection
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def get_database_url(db_path: Optional[str] = None) -> str:
    """Get database URL for SQLAlchemy"""
    if db_path is None:
        db_path = DATABASE_PATH  # Use centralized config instead of os.getcwd()
    
    # Ensure absolute path for SQLite
    db_path = os.path.abspath(db_path)
    
    return f"sqlite:///{db_path}"


def get_engine(db_path: Optional[str] = None, echo: bool = False) -> Engine:
    """Get SQLAlchemy engine for database operations"""
    global _engine
    
    if _engine is None:
        database_url = get_database_url(db_path)
        
        # SQLite-specific configuration
        _engine = create_engine(
            database_url,
            echo=echo,
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,  # Allow multi-threading
                "timeout": 30,  # Connection timeout
                "isolation_level": None  # Use autocommit mode
            }
        )
    
    return _engine


def get_session_factory(db_path: Optional[str] = None) -> sessionmaker:
    """Get SQLAlchemy session factory"""
    global _session_factory
    
    if _session_factory is None:
        engine = get_engine(db_path)
        _session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    
    return _session_factory


def get_session(db_path: Optional[str] = None) -> Session:
    """Get new SQLAlchemy session"""
    session_factory = get_session_factory(db_path)
    return session_factory()


def reset_connection():
    """Reset database connection (useful for testing)"""
    global _engine, _session_factory
    
    if _engine:
        _engine.dispose()
        _engine = None
    
    _session_factory = None


class DatabaseManager:
    """Database manager for handling connections and sessions"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.engine = get_engine(db_path)
        self.session_factory = get_session_factory(db_path)
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.session_factory()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Execute a raw SQL query"""
        with self.engine.connect() as conn:
            return conn.execute(text(query), params or {})
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()


# Context manager for database sessions
class DatabaseSession:
    """Context manager for database sessions with automatic cleanup"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.session = None
    
    def __enter__(self) -> Session:
        self.session = get_session(self.db_path)
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close() 