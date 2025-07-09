#!/usr/bin/env python3

"""
Test script to verify MCP server can be imported and initialized without errors
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_server_import():
    """Test that the server can be imported without errors"""
    try:
        from src.mcp_server.server import mcp, pdf_parser
        print("✅ Server import successful", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ Server import failed: {e}", file=sys.stderr)
        return False

def test_pdf_parser():
    """Test that the PDF parser can be initialized"""
    try:
        from src.pdf_parser.parser import BusinessDocumentPDFParser
        parser = BusinessDocumentPDFParser()
        print("✅ PDF parser initialization successful", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ PDF parser initialization failed: {e}", file=sys.stderr)
        return False

def test_database_init():
    """Test that database can be initialized"""
    try:
        from src.database.queries import initialize_database
        db_path = initialize_database()
        print(f"✅ Database initialization successful: {db_path}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    print("🧪 Testing MCP Server Components...", file=sys.stderr)
    
    success = True
    success &= test_server_import()
    success &= test_pdf_parser()
    success &= test_database_init()
    
    if success:
        print("✅ All tests passed! MCP server should work without JSON protocol errors.", file=sys.stderr)
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.", file=sys.stderr)
        sys.exit(1)