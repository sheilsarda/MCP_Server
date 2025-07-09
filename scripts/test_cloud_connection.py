#!/usr/bin/env python3
"""
Cloud Database Connection Test

Test script to verify your cloud database setup is working correctly.

Usage:
    export DATABASE_URL="postgresql://user:password@host:port/database"
    python scripts/test_cloud_connection.py
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from database.connection import get_engine, DatabaseSession
from database.models import Base, BusinessDocument, DocumentType
from datetime import datetime


def test_connection():
    """Test basic database connectivity"""
    print("🔗 Testing database connection...")
    
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute("SELECT 1 as test")
            print(f"✅ Connection successful: {result.fetchone()}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_schema_creation():
    """Test schema creation"""
    print("📋 Testing schema creation...")
    
    try:
        engine = get_engine()
        Base.metadata.create_all(engine)
        print("✅ Schema created successfully")
        return True
    except Exception as e:
        print(f"❌ Schema creation failed: {e}")
        return False


def test_basic_operations():
    """Test basic CRUD operations"""
    print("🔄 Testing basic database operations...")
    
    try:
        with DatabaseSession() as session:
            # Create a test document
            test_doc = BusinessDocument(
                document_type=DocumentType.INVOICE,
                document_number="TEST-001",
                vendor="Test Vendor",
                date=datetime.now(),
                pdf_filename="test.pdf",
                pdf_path="/tmp/test.pdf",
                status="test"
            )
            
            session.add(test_doc)
            session.commit()
            
            # Read it back
            found_doc = session.query(BusinessDocument).filter_by(document_number="TEST-001").first()
            if found_doc:
                print(f"✅ CRUD operations successful: Document {found_doc.id} created")
                
                # Clean up
                session.delete(found_doc)
                session.commit()
                print("✅ Test data cleaned up")
                return True
            else:
                print("❌ Could not read back test document")
                return False
                
    except Exception as e:
        print(f"❌ CRUD operations failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Cloud Database Test Suite")
    print("=" * 40)
    
    # Check environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        print("   Set it with: export DATABASE_URL='your_database_url'")
        return False
    
    print(f"🎯 Testing database: {database_url[:50]}...")
    print()
    
    # Run tests
    tests = [
        ("Connection", test_connection),
        ("Schema Creation", test_schema_creation),
        ("Basic Operations", test_basic_operations)
    ]
    
    passed = 0
    for name, test_func in tests:
        if test_func():
            passed += 1
        print()
    
    # Summary
    print("📊 Test Results:")
    print(f"   Passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All tests passed! Your cloud database is ready to use.")
        return True
    else:
        print("❌ Some tests failed. Please check your configuration.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 