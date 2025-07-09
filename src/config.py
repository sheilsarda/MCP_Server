"""
Configuration management for Business Document PDF Parser

Centralized configuration using environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional

# Get the project root directory (where this file's parent's parent is)
# Handle case where this file might be imported from different locations
CONFIG_FILE_PATH = Path(__file__).resolve()
if CONFIG_FILE_PATH.name == 'config.py':
    PROJECT_ROOT = CONFIG_FILE_PATH.parent.parent.resolve()
else:
    # Fallback: find the project root by looking for known files
    current = CONFIG_FILE_PATH.parent
    while current.parent != current:
        if (current / 'requirements.txt').exists() and (current / 'src').exists():
            PROJECT_ROOT = current
            break
        current = current.parent
    else:
        PROJECT_ROOT = Path.cwd()

def get_database_path() -> str:
    """
    Get the canonical database path.
    
    Priority:
    1. BUSINESS_DOCS_DB_PATH environment variable (absolute path)
    2. Default: PROJECT_ROOT/data/business_documents.db
    
    Returns:
        Absolute path to the database file
    """
    # Check environment variable first
    env_path = os.getenv('BUSINESS_DOCS_DB_PATH')
    if env_path:
        return os.path.abspath(env_path)
    
    # Default: use data directory in project root
    data_dir = PROJECT_ROOT / 'data'
    data_dir.mkdir(exist_ok=True)  # Create data directory if it doesn't exist
    
    return str(data_dir / 'business_documents.db')

def get_sample_data_path() -> str:
    """Get the path to sample data directory"""
    return str(PROJECT_ROOT / 'sample_data')

def get_logs_path() -> str:
    """Get the path for log files"""
    logs_dir = PROJECT_ROOT / 'logs'
    logs_dir.mkdir(exist_ok=True)
    return str(logs_dir)

# Database configuration
DATABASE_PATH = get_database_path()
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# PDF Parser configuration
MAX_PDF_SIZE = int(os.getenv('PO_PARSER_MAX_PDF_SIZE', '52428800'))  # 50MB default
PARSING_TIMEOUT = int(os.getenv('PO_PARSER_PARSING_TIMEOUT', '120'))  # 120s default
EXTRACTION_CONFIDENCE_THRESHOLD = float(os.getenv('PO_PARSER_EXTRACTION_CONFIDENCE_THRESHOLD', '0.5'))

# Debug configuration
DEBUG_MODE = os.getenv('PO_PARSER_DEBUG', 'False').lower() in ('true', '1', 'yes', 'on')

# MCP Server configuration
MCP_SERVER_HOST = os.getenv('MCP_SERVER_HOST', 'localhost')
MCP_SERVER_PORT = int(os.getenv('MCP_SERVER_PORT', '8000'))

def print_config_summary():
    """Print current configuration for debugging"""
    print("Business Document Parser Configuration")
    print("=" * 50)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Database Path: {DATABASE_PATH}")
    print(f"Sample Data: {get_sample_data_path()}")
    print(f"Logs Path: {get_logs_path()}")
    print(f"Debug Mode: {DEBUG_MODE}")
    print(f"Max PDF Size: {MAX_PDF_SIZE} bytes")
    print(f"Parsing Timeout: {PARSING_TIMEOUT}s")
    print(f"Confidence Threshold: {EXTRACTION_CONFIDENCE_THRESHOLD}")

if __name__ == "__main__":
    print_config_summary() 