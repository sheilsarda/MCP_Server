"""
Database setup and initialization script for Business Document PDF Parser

Creates SQLite database with all required tables.
"""

import os
import sqlite3
import sys
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

from .models import Base, DocumentType, normalize_vendor_name
from .connection import get_database_url, get_engine, get_session


def create_database(db_path: Optional[str] = None) -> str:
    """Create database file if it doesn't exist (SQLite only)
    
    For cloud databases, this function returns the database URL.
    For SQLite, it creates the file if needed.
    """
    # Use centralized database configuration
    database_url = get_database_url(db_path)
    
    # Only create file for SQLite databases
    if database_url.startswith('sqlite:///'):
        sqlite_path = database_url.replace('sqlite:///', '')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        
        # Create empty database file if it doesn't exist
        if not os.path.exists(sqlite_path):
            with sqlite3.connect(sqlite_path) as conn:
                conn.execute("SELECT 1")  # Create the file
                
        return sqlite_path
    else:
        # For cloud databases, return the URL
        return database_url


def initialize_database(db_path: Optional[str] = None) -> str:
    """Initialize database with all tables and indexes"""
    # Use centralized engine that supports both SQLite and PostgreSQL
    engine = get_engine(db_path)
    database_url = get_database_url(db_path)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create additional indexes for performance
    with engine.connect() as conn:
        # Business documents indexes (PostgreSQL and SQLite compatible)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_business_documents_vendor_date 
            ON business_documents(vendor, date)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_business_documents_type_date 
            ON business_documents(document_type, date)
        """))
        
        # Cross-reference indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_invoices_reference_po 
            ON invoices(reference_po)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_receipts_reference_po 
            ON receipts(reference_po)
        """))
        
        conn.commit()
    
    # Return appropriate identifier
    if database_url.startswith('sqlite:///'):
        return database_url.replace('sqlite:///', '')
    else:
        return database_url


def reset_database(db_path: Optional[str] = None) -> None:
    """Drop all tables and recreate them"""
    # Use centralized engine
    engine = get_engine(db_path)
    
    # Drop all tables
    Base.metadata.drop_all(engine)
    
    # Recreate all tables
    initialize_database(db_path)


def seed_sample_data(db_path: Optional[str] = None) -> None:
    """Add sample data for testing - DISABLED by default to keep database empty for real data"""
    return


def get_database_info(db_path: Optional[str] = None) -> dict:
    """Get information about the database"""
    database_url = get_database_url(db_path)
    engine = get_engine(db_path)
    
    try:
        with engine.connect() as conn:
            # Database-agnostic way to get table information
            if database_url.startswith('sqlite:///'):
                # SQLite-specific query
                tables = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)).fetchall()
                
                # Get file info for SQLite
                sqlite_path = database_url.replace('sqlite:///', '')
                file_size = os.path.getsize(sqlite_path) if os.path.exists(sqlite_path) else 0
                
            else:
                # PostgreSQL-specific query
                tables = conn.execute(text("""
                    SELECT table_name as name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)).fetchall()
                
                # For cloud databases, file size is not applicable
                file_size = None
            
            table_info = {}
            for table in tables:
                table_name = table[0]
                try:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
                    count = count_result[0] if count_result else 0
                    table_info[table_name] = count
                except Exception as e:
                    # If table doesn't exist or other error, mark as 0
                    table_info[table_name] = 0
        
        result = {
            "database_url": database_url[:50] + "..." if len(database_url) > 50 else database_url,
            "database_type": "SQLite" if database_url.startswith('sqlite:///') else "PostgreSQL",
            "tables": table_info
        }
        
        # Add file size for SQLite only
        if file_size is not None:
            result["file_size"] = file_size
            result["database_path"] = database_url.replace('sqlite:///', '')
        
        return result
        
    except Exception as e:
        return {"error": f"Could not connect to database: {str(e)}"}


if __name__ == "__main__":
    # Initialize database when script is run directly
    db_path = initialize_database()
    seed_sample_data(db_path)
    
    # Show database info
    info = get_database_info(db_path) 