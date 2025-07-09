#!/usr/bin/env python3
"""
Database Migration Script: SQLite to Cloud PostgreSQL

This script migrates all data from your local SQLite database to a cloud PostgreSQL database.
Designed for migrating to Supabase, Heroku Postgres, or any PostgreSQL service.

Usage:
    # Set your cloud database URL
    export DATABASE_URL="postgresql://user:password@host:port/database"
    
    # Run the migration
    python scripts/migrate_to_cloud.py

The script will:
1. Read all data from your local SQLite database
2. Create tables in the PostgreSQL database
3. Transfer all records while preserving relationships
4. Validate the migration was successful
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.models import Base, BusinessDocument, PurchaseOrder, Invoice, Receipt, DocumentLineItem, Vendor, ExtractionTemplate


class DatabaseMigrator:
    """Handles migration from SQLite to PostgreSQL"""
    
    def __init__(self, sqlite_path: str, postgres_url: str):
        """Initialize migrator with source and target database URLs"""
        self.sqlite_url = f"sqlite:///{sqlite_path}"
        self.postgres_url = postgres_url
        
        # Handle Supabase URL format
        if self.postgres_url.startswith('postgres://'):
            self.postgres_url = self.postgres_url.replace('postgres://', 'postgresql://', 1)
        
        # Create engines
        self.sqlite_engine = create_engine(self.sqlite_url)
        self.postgres_engine = create_engine(
            self.postgres_url,
            pool_pre_ping=True,
            connect_args={"sslmode": "require"}
        )
        
        # Create session makers
        self.sqlite_session = sessionmaker(bind=self.sqlite_engine)
        self.postgres_session = sessionmaker(bind=self.postgres_engine)
    
    def validate_connections(self) -> bool:
        """Test connections to both databases"""
        try:
            # Test SQLite connection
            with self.sqlite_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ SQLite connection successful")
            
            # Test PostgreSQL connection
            with self.postgres_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ PostgreSQL connection successful")
            
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def create_target_schema(self):
        """Create all tables in the target PostgreSQL database"""
        try:
            Base.metadata.create_all(self.postgres_engine)
            print("✅ PostgreSQL schema created successfully")
        except Exception as e:
            print(f"❌ Failed to create schema: {e}")
            raise
    
    def count_records(self, session_maker, model) -> int:
        """Count records in a table"""
        with session_maker() as session:
            return session.query(model).count()
    
    def migrate_table(self, model, table_name: str) -> Dict[str, int]:
        """Migrate a single table from SQLite to PostgreSQL"""
        print(f"📦 Migrating {table_name}...")
        
        with self.sqlite_session() as source_session:
            records = source_session.query(model).all()
            
        if not records:
            print(f"  ⚠️  No records found in {table_name}")
            return {"source": 0, "target": 0}
        
        # Convert to dictionaries and handle special cases
        record_dicts = []
        for record in records:
            record_dict = {}
            for column in model.__table__.columns:
                value = getattr(record, column.name)
                
                # Handle enum values
                if hasattr(value, 'value'):
                    value = value.value
                
                record_dict[column.name] = value
            
            record_dicts.append(record_dict)
        
        # Bulk insert into PostgreSQL
        with self.postgres_session() as target_session:
            try:
                target_session.bulk_insert_mappings(model, record_dicts)
                target_session.commit()
                print(f"  ✅ Migrated {len(record_dicts)} records to {table_name}")
            except Exception as e:
                target_session.rollback()
                print(f"  ❌ Failed to migrate {table_name}: {e}")
                raise
        
        # Verify counts
        source_count = len(records)
        target_count = self.count_records(self.postgres_session, model)
        
        return {"source": source_count, "target": target_count}
    
    def run_migration(self) -> Dict[str, Any]:
        """Run the complete migration process"""
        print("🚀 Starting database migration...")
        print(f"   Source: {self.sqlite_url}")
        print(f"   Target: {self.postgres_url}")
        print()
        
        # Validate connections
        if not self.validate_connections():
            raise Exception("Cannot connect to databases")
        
        # Create schema
        self.create_target_schema()
        
        # Migration order (respecting foreign key dependencies)
        migration_order = [
            (BusinessDocument, "business_documents"),
            (PurchaseOrder, "purchase_orders"),
            (Invoice, "invoices"),
            (Receipt, "receipts"),
            (DocumentLineItem, "document_line_items"),
            (Vendor, "vendors"),
            (ExtractionTemplate, "extraction_templates"),
        ]
        
        results = {}
        total_source = 0
        total_target = 0
        
        # Migrate each table
        for model, table_name in migration_order:
            try:
                counts = self.migrate_table(model, table_name)
                results[table_name] = counts
                total_source += counts["source"]
                total_target += counts["target"]
            except Exception as e:
                print(f"❌ Migration failed at table {table_name}: {e}")
                raise
        
        # Summary
        print("\n📊 Migration Summary:")
        print("=" * 50)
        for table_name, counts in results.items():
            status = "✅" if counts["source"] == counts["target"] else "❌"
            print(f"{status} {table_name}: {counts['source']} → {counts['target']}")
        
        print(f"\n📈 Total Records: {total_source} → {total_target}")
        
        if total_source == total_target:
            print("🎉 Migration completed successfully!")
        else:
            print("⚠️  Migration completed with discrepancies")
        
        return results


def main():
    """Main migration function"""
    # Get database paths
    sqlite_path = os.getenv('BUSINESS_DOCS_DB_PATH')
    if not sqlite_path:
        # Use default path
        default_path = project_root / 'data' / 'business_documents.db'
        sqlite_path = str(default_path)
    
    postgres_url = os.getenv('DATABASE_URL')
    if not postgres_url:
        print("❌ DATABASE_URL environment variable not set")
        print("   Please set it to your cloud database URL:")
        print("   export DATABASE_URL='postgresql://user:password@host:port/database'")
        sys.exit(1)
    
    # Check if SQLite database exists
    if not Path(sqlite_path).exists():
        print(f"❌ SQLite database not found: {sqlite_path}")
        print("   Run pdf_to_database_workflow.py first to create sample data")
        sys.exit(1)
    
    print(f"🔄 Migrating from: {sqlite_path}")
    print(f"🔄 Migrating to: {postgres_url}")
    print()
    
    # Confirm migration
    response = input("Do you want to proceed with the migration? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Migration cancelled")
        sys.exit(0)
    
    # Run migration
    migrator = DatabaseMigrator(sqlite_path, postgres_url)
    try:
        results = migrator.run_migration()
        print(f"\n✅ Migration completed at {datetime.now()}")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 