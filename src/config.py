"""
Configuration management for Business Document PDF Parser

Centralized configuration using environment variables with sensible defaults.

# AUDIT FEEDBACK - MAJOR IMPROVEMENTS NEEDED:
# 1. **SECURITY ISSUE**: No validation of environment variables - could lead to path injection
# 2. **CODE SMELL**: File path determination logic is overly complex and brittle  
# 3. **MAINTAINABILITY**: Hard-coded defaults scattered throughout - should use dataclass/Pydantic
# 4. **ERROR HANDLING**: No graceful handling of permission/filesystem errors
# 5. **CONSISTENCY**: Mixed naming conventions (CAPS vs snake_case)
# 6. **ARCHITECTURE**: Configuration logic mixed with filesystem operations
# 7. **TESTING**: No configuration validation or environment-specific configs
"""

import os
from pathlib import Path
from typing import Optional
# TODO: Add proper configuration validation with Pydantic
# from pydantic import BaseSettings, validator
# from enum import Enum

# IMPROVEMENT: Use dataclass or Pydantic for type safety and validation
# @dataclass
# class DatabaseConfig:
#     path: Path
#     url: str
#     max_size: int = 50 * 1024 * 1024  # 50MB

# Get the project root directory (where this file's parent's parent is)
# Handle case where this file might be imported from different locations
# AUDIT: This logic is overly complex and fragile - use a simpler approach
CONFIG_FILE_PATH = Path(__file__).resolve()
if CONFIG_FILE_PATH.name == 'config.py':
    PROJECT_ROOT = CONFIG_FILE_PATH.parent.parent.resolve()
else:
    # Fallback: find the project root by looking for known files
    # BUG POTENTIAL: This could fail silently or find wrong directory
    current = CONFIG_FILE_PATH.parent
    while current.parent != current:
        if (current / 'requirements.txt').exists() and (current / 'src').exists():
            PROJECT_ROOT = current
            break
        current = current.parent
    else:
        # IMPROVEMENT: Should raise explicit error instead of defaulting to cwd
        PROJECT_ROOT = Path.cwd()

# IMPROVEMENT: Replace complex logic with simple approach:
# PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def get_database_path() -> str:
    """
    Get the canonical database path.
    
    Priority:
    1. DATABASE_URL environment variable (for cloud databases like PostgreSQL)
    2. BUSINESS_DOCS_DB_PATH environment variable (absolute path for SQLite)
    3. Default: PROJECT_ROOT/data/business_documents.db (SQLite)
    
    Returns:
        Database URL string (either postgres:// or sqlite:/// format)
        
    # AUDIT ISSUES:
    # 1. No validation of env var (could be malicious path)
    # 2. Silent directory creation could mask permission issues  
    # 3. No error handling for filesystem operations
    # 4. Return type should be Path, not str for type safety
    """
    # Check for cloud database URL first (Supabase, Heroku, etc.)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Handle Supabase/Heroku format: postgres://... -> postgresql://...
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    
    # Check environment variable for local SQLite path
    # SECURITY ISSUE: No validation of environment variable
    env_path = os.getenv('BUSINESS_DOCS_DB_PATH')
    if env_path:
        # TODO: Validate path is safe and accessible
        # TODO: Check if parent directories exist and are writable
        return f"sqlite:///{os.path.abspath(env_path)}"
    
    # Default: use data directory in project root
    data_dir = PROJECT_ROOT / 'data'
    # IMPROVEMENT: Handle permission errors explicitly
    try:
        data_dir.mkdir(exist_ok=True)  # Create data directory if it doesn't exist
    except PermissionError as e:
        # TODO: Add proper error handling and logging
        raise RuntimeError(f"Cannot create data directory: {e}")
    
    sqlite_path = str(data_dir / 'business_documents.db')
    return f"sqlite:///{sqlite_path}"

def get_database_url() -> str:
    """
    Get the database URL for SQLAlchemy.
    
    Returns:
        Complete database URL string
    """
    return get_database_path()

def get_sample_data_path() -> str:
    """Get the path to sample data directory
    
    # IMPROVEMENT: Should validate directory exists and return Path object
    """
    return str(PROJECT_ROOT / 'sample_data')

def get_logs_path() -> str:
    """Get the path for log files
    
    # AUDIT: Same issues as get_database_path - no error handling
    """
    logs_dir = PROJECT_ROOT / 'logs'
    # IMPROVEMENT: Add proper error handling
    try:
        logs_dir.mkdir(exist_ok=True)
    except PermissionError as e:
        raise RuntimeError(f"Cannot create logs directory: {e}")
    return str(logs_dir)

# Database configuration
# IMPROVEMENT: Use proper configuration class instead of global variables
DATABASE_URL = get_database_url()
# Keep DATABASE_PATH for backward compatibility (SQLite only)
if DATABASE_URL.startswith('sqlite:///'):
    DATABASE_PATH = DATABASE_URL.replace('sqlite:///', '')
else:
    DATABASE_PATH = None  # Not applicable for cloud databases

# PDF Parser configuration
# AUDIT ISSUES: Magic numbers, no validation, inconsistent env var names
MAX_PDF_SIZE = int(os.getenv('PO_PARSER_MAX_PDF_SIZE', '52428800'))  # 50MB default
PARSING_TIMEOUT = int(os.getenv('PO_PARSER_PARSING_TIMEOUT', '120'))  # 120s default
EXTRACTION_CONFIDENCE_THRESHOLD = float(os.getenv('PO_PARSER_EXTRACTION_CONFIDENCE_THRESHOLD', '0.5'))

# IMPROVEMENT: Add validation for these values
# if MAX_PDF_SIZE <= 0 or MAX_PDF_SIZE > 100 * 1024 * 1024:  # Max 100MB
#     raise ValueError(f"Invalid MAX_PDF_SIZE: {MAX_PDF_SIZE}")

# Debug configuration
# IMPROVEMENT: Use enum for debug levels instead of boolean
DEBUG_MODE = os.getenv('PO_PARSER_DEBUG', 'False').lower() in ('true', '1', 'yes', 'on')

# MCP Server configuration  
# AUDIT: No validation of host/port values
MCP_SERVER_HOST = os.getenv('MCP_SERVER_HOST', 'localhost')
MCP_SERVER_PORT = int(os.getenv('MCP_SERVER_PORT', '8000'))

# TODO: Add port range validation (1024-65535)
# TODO: Add host format validation

def print_config_summary():
    """Print current configuration for debugging
    
    # IMPROVEMENT: Use proper logging instead of print statements
    # SECURITY: Don't log sensitive configuration values in production
    """
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

# IMPROVEMENT: Add configuration validation function
def validate_config():
    """Validate all configuration values"""
    errors = []
    
    if not Path(PROJECT_ROOT).exists():
        errors.append(f"Project root does not exist: {PROJECT_ROOT}")
    
    if PARSING_TIMEOUT <= 0:
        errors.append(f"Invalid parsing timeout: {PARSING_TIMEOUT}")
        
    if not 0 <= EXTRACTION_CONFIDENCE_THRESHOLD <= 1:
        errors.append(f"Invalid confidence threshold: {EXTRACTION_CONFIDENCE_THRESHOLD}")
        
    if errors:
        raise ValueError("Configuration validation failed: " + "; ".join(errors))

if __name__ == "__main__":
    # TODO: Add configuration validation before printing
    validate_config()
    print_config_summary() 