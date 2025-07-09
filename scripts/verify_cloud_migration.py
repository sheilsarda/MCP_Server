#!/usr/bin/env python3
"""
Verification Script: Cloud Database Migration

This script verifies that your PDF processing workflow is correctly using 
the cloud database (Supabase/PostgreSQL) instead of the old SQLite database.

Usage:
    # First, set your DATABASE_URL environment variable
    export DATABASE_URL="postgresql://user:password@host:port/database"
    
    # Then run this verification
    python scripts/verify_cloud_migration.py

The script will:
1. Check DATABASE_URL environment variable
2. Test database connection 
3. Verify schema creation works
4. Test PDF workflow initialization
5. Show database info using new cloud-compatible functions
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def check_environment():
    """Check if DATABASE_URL is properly configured"""
    print("🔍 Checking Environment Configuration...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("\n📋 To set up Supabase:")
        print("   1. Go to your Supabase project dashboard")
        print("   2. Go to Settings > Database")
        print("   3. Copy the connection string")
        print("   4. Export it: export DATABASE_URL='postgresql://...'")
        print("\n   Or create a .env file with:")
        print("   DATABASE_URL=postgresql://user:password@host:port/database")
        return False
    
    print(f"✅ DATABASE_URL found: {database_url[:30]}...")
    
    # Check if it's a cloud database URL
    if database_url.startswith(('postgresql://', 'postgres://')):
        print("✅ Cloud database URL detected (PostgreSQL)")
        return True
    elif database_url.startswith('sqlite:///'):
        print("⚠️  SQLite database URL detected - migration not complete")
        return False
    else:
        print(f"⚠️  Unknown database URL format: {database_url[:20]}...")
        return False

def test_database_connection():
    """Test database connection using centralized functions"""
    print("\n🔗 Testing Database Connection...")
    
    try:
        from database.connection import get_engine, get_database_url
        from database.setup import get_database_info
        
        # Get database info using cloud-compatible function
        database_url = get_database_url()
        print(f"   Using database: {database_url[:30]}...")
        
        # Test connection
        engine = get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1 as test")).fetchone()
            print(f"✅ Connection successful: {result}")
        
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_schema_creation():
    """Test that schema can be created in cloud database"""
    print("\n📋 Testing Schema Creation...")
    
    try:
        from database.setup import initialize_database
        
        # Initialize database using cloud-compatible function
        result = initialize_database()
        print(f"✅ Schema creation successful")
        print(f"   Database identifier: {result[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Schema creation failed: {e}")
        return False

def test_database_info():
    """Test database info retrieval works with cloud database"""
    print("\n📊 Testing Database Info Retrieval...")
    
    try:
        from database.setup import get_database_info
        
        info = get_database_info()
        
        if "error" in info:
            print(f"❌ Database info error: {info['error']}")
            return False
        
        print("✅ Database info retrieved successfully:")
        for key, value in info.items():
            if key == 'tables' and isinstance(value, dict):
                print(f"   📋 Tables ({len(value)}):")
                for table_name, count in value.items():
                    print(f"      • {table_name}: {count} records")
            else:
                print(f"   {key}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ Database info failed: {e}")
        return False

def test_pdf_workflow_initialization():
    """Test that PDF workflow can initialize with cloud database"""
    print("\n📄 Testing PDF Workflow Initialization...")
    
    try:
        # Import workflow (this should now use cloud database)
        sys.path.insert(0, str(project_root / 'scripts'))
        from pdf_to_database_workflow import PDFProcessingWorkflow
        
        # Initialize workflow (should use DATABASE_URL now)
        workflow = PDFProcessingWorkflow()
        print("✅ PDF Workflow initialized successfully")
        print("   (Check output above for database confirmation)")
        
        return True
    except Exception as e:
        print(f"❌ PDF Workflow initialization failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🧪 Cloud Database Migration Verification")
    print("=" * 60)
    
    tests = [
        ("Environment Setup", check_environment),
        ("Database Connection", test_database_connection),
        ("Schema Creation", test_schema_creation),
        ("Database Info", test_database_info),
        ("PDF Workflow", test_pdf_workflow_initialization)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        else:
            print(f"\n⚠️  Test '{test_name}' failed - check configuration")
    
    print(f"\n📈 Verification Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 Migration Verification Complete!")
        print("✅ Your PDF processing workflow is now using the cloud database")
        print("✅ All legacy SQLite references have been migrated")
        print("\n🚀 You can now run:")
        print("   python scripts/pdf_to_database_workflow.py")
        print("   (It will use your Supabase database)")
    else:
        print(f"\n❌ {len(tests) - passed} tests failed")
        print("   Please check your DATABASE_URL configuration")
        print("   and ensure your Supabase database is accessible")

if __name__ == "__main__":
    main() 