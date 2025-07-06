#!/usr/bin/env python3
"""
Simple script to clear the database using existing functions
"""
import os
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.setup import reset_database, get_database_info

def main():
    """Clear the database and show info"""
    print("🗑️  Clearing database...")
    
    # Reset database (drops all tables and recreates them)
    reset_database()
    
    print("✅ Database cleared successfully!")
    
    # Show database info to confirm it's empty
    print("\n📊 Database status after clearing:")
    info = get_database_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main() 