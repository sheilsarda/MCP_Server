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
    """Create SQLite database file if it doesn't exist"""
    if db_path is None:
        db_path = os.path.join(os.getcwd(), 'business_documents.db')
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create empty database file if it doesn't exist
    if not os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            conn.execute("SELECT 1")  # Create the file
            
    return db_path


def initialize_database(db_path: Optional[str] = None) -> str:
    """Initialize database with all tables and indexes"""
    if db_path is None:
        db_path = create_database()
    
    # Create engine and tables
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, echo=False)
    
    # Don't print to stdout as it interferes with MCP JSON-RPC protocol
    # print(f"Creating database tables in: {db_path}")
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create additional indexes for performance
    with engine.connect() as conn:
        # Business documents indexes
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
    
    # print(f"Database initialized successfully at: {db_path}")
    return db_path


def reset_database(db_path: Optional[str] = None) -> None:
    """Drop all tables and recreate them"""
    if db_path is None:
        db_path = create_database()
    
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url)
    
    # print(f"Resetting database: {db_path}")
    
    # Drop all tables
    Base.metadata.drop_all(engine)
    
    # Recreate all tables
    initialize_database(db_path)


def seed_sample_data(db_path: Optional[str] = None) -> None:
    """Add sample data for testing - DISABLED by default to keep database empty for real data"""
    # print("Sample data seeding is disabled. Database will remain empty for real data only.")
    return


def get_database_info(db_path: Optional[str] = None) -> dict:
    """Get information about the database"""
    if db_path is None:
        db_path = os.path.join(os.getcwd(), 'business_documents.db')
    
    if not os.path.exists(db_path):
        return {"error": "Database file does not exist"}
    
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Get table information
        tables = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)).fetchall()
        
        table_info = {}
        for table in tables:
            table_name = table[0]
            count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
            count = count_result[0] if count_result else 0
            table_info[table_name] = count
    
    return {
        "database_path": db_path,
        "file_size": os.path.getsize(db_path),
        "tables": table_info
    }


if __name__ == "__main__":
    # Initialize database when script is run directly
    db_path = initialize_database()
    seed_sample_data(db_path)
    
    # Show database info
    info = get_database_info(db_path)
    # Commented out to avoid interfering with MCP JSON-RPC protocol
    # print("\nDatabase Information:")
    # for key, value in info.items():
    #     print(f"  {key}: {value}") 