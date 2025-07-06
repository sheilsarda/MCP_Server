"""
Configuration settings for Purchase Order PDF Parser

Manages all configuration settings using Pydantic BaseSettings.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from decimal import Decimal

from pydantic import BaseSettings, Field, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Main configuration settings for the PO parser"""
    
    # Application settings
    app_name: str = Field(default="Purchase Order PDF Parser", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Database settings
    database_url: str = Field(default="sqlite:///./purchase_orders.db", description="Database connection URL")
    database_echo: bool = Field(default=False, description="Enable SQL query logging")
    
    # PDF parsing settings
    max_pdf_size: int = Field(default=50 * 1024 * 1024, description="Maximum PDF file size in bytes (50MB)")
    parsing_timeout: int = Field(default=120, description="PDF parsing timeout in seconds")
    extraction_confidence_threshold: float = Field(default=0.5, description="Minimum confidence for extraction")
    
    # Supported file types
    supported_extensions: List[str] = Field(
        default_factory=lambda: [".pdf"],
        description="List of supported file extensions"
    )
    
    # Storage settings
    storage_directory: str = Field(default="./storage", description="Directory for storing uploaded PDFs")
    backup_directory: str = Field(default="./backups", description="Directory for database backups")
    sample_data_directory: str = Field(default="./sample_data", description="Directory for sample data")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path (console only if None)")
    log_format: str = Field(default="{time} | {level} | {message}", description="Log format")
    
    # MCP server settings
    server_name: str = Field(default="Purchase Order PDF Parser", description="MCP server name")
    server_description: str = Field(default="Parse PDF purchase orders and store in database", description="MCP server description")
    
    # Parsing configuration
    enable_multiple_parsers: bool = Field(default=True, description="Try multiple PDF parsing libraries")
    prefer_accuracy_over_speed: bool = Field(default=True, description="Prefer accuracy over parsing speed")
    
    # Data validation settings
    min_po_amount: Decimal = Field(default=Decimal("0.01"), description="Minimum valid PO amount")
    max_po_amount: Decimal = Field(default=Decimal("1000000.00"), description="Maximum valid PO amount")
    
    # Search settings
    default_search_limit: int = Field(default=20, description="Default search result limit")
    max_search_limit: int = Field(default=100, description="Maximum search result limit")
    
    # Performance settings
    max_concurrent_parsers: int = Field(default=3, description="Maximum concurrent PDF parsers")
    database_connection_timeout: int = Field(default=30, description="Database connection timeout")
    
    # Regex patterns for PO extraction
    po_number_patterns: List[str] = Field(
        default_factory=lambda: [
            r'PO[-\s]?Number:?\s*([A-Z0-9-]+)',
            r'Purchase\s+Order:?\s*([A-Z0-9-]+)',
            r'P\.O\.?\s*:?\s*([A-Z0-9-]+)',
            r'Order\s+Number:?\s*([A-Z0-9-]+)'
        ],
        description="Regex patterns for extracting PO numbers"
    )
    
    vendor_patterns: List[str] = Field(
        default_factory=lambda: [
            r'Vendor:?\s*([A-Za-z\s&.,\'-]+?)(?:\n|$)',
            r'Supplier:?\s*([A-Za-z\s&.,\'-]+?)(?:\n|$)',
            r'Company:?\s*([A-Za-z\s&.,\'-]+?)(?:\n|$)'
        ],
        description="Regex patterns for extracting vendor names"
    )
    
    # Environment-specific settings
    environment: str = Field(default="development", description="Environment (development, production, test)")
    
    class Config:
        env_file = ".env"
        env_prefix = "PO_PARSER_"
        case_sensitive = False
        
    @validator('storage_directory', 'backup_directory', 'sample_data_directory')
    def create_directories(cls, v):
        """Create directories if they don't exist"""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    @validator('max_pdf_size')
    def validate_max_pdf_size(cls, v):
        """Validate maximum PDF file size"""
        if v <= 0:
            raise ValueError("Maximum PDF size must be positive")
        if v > 500 * 1024 * 1024:  # 500MB
            raise ValueError("Maximum PDF size too large (>500MB)")
        return v
    
    @validator('extraction_confidence_threshold')
    def validate_confidence_threshold(cls, v):
        """Validate confidence threshold"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        return v
    
    @validator('min_po_amount', 'max_po_amount')
    def validate_po_amounts(cls, v):
        """Validate PO amount limits"""
        if v <= 0:
            raise ValueError("PO amount must be positive")
        return v
    
    @validator('max_po_amount')
    def validate_max_po_amount(cls, v, values):
        """Validate max PO amount is greater than min"""
        if 'min_po_amount' in values and v <= values['min_po_amount']:
            raise ValueError("Maximum PO amount must be greater than minimum")
        return v


class DatabaseConfig:
    """Database-specific configuration"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    @property
    def connection_args(self) -> Dict[str, Any]:
        """Get database connection arguments"""
        if self.settings.database_url.startswith('sqlite'):
            return {
                "check_same_thread": False,
                "timeout": self.settings.database_connection_timeout
            }
        return {}
    
    @property
    def engine_args(self) -> Dict[str, Any]:
        """Get database engine arguments"""
        return {
            "echo": self.settings.database_echo,
            "connect_args": self.connection_args
        }


class ParsingConfig:
    """PDF parsing configuration"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    @property
    def extraction_patterns(self) -> Dict[str, List[str]]:
        """Get extraction patterns for different fields"""
        return {
            "po_number": self.settings.po_number_patterns,
            "vendor": self.settings.vendor_patterns,
            "date": [
                r'Date:?\s*(\d{4}-\d{2}-\d{2})',
                r'Date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Order\s+Date:?\s*(\d{4}-\d{2}-\d{2})',
                r'Order\s+Date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            "total": [
                r'Total:?\s*\$?([0-9,]+\.?\d{0,2})',
                r'Grand\s+Total:?\s*\$?([0-9,]+\.?\d{0,2})',
                r'Amount:?\s*\$?([0-9,]+\.?\d{0,2})'
            ],
            "item": [
                r'Item:?\s*([A-Za-z\s\-&.,]+)',
                r'Description:?\s*([A-Za-z\s\-&.,]+)',
                r'Product:?\s*([A-Za-z\s\-&.,]+)'
            ],
            "quantity": [
                r'Quantity:?\s*(\d+)',
                r'Qty:?\s*(\d+)',
                r'(\d+)\s*(?:EA|Each|Units?)'
            ],
            "unit_price": [
                r'Unit\s+Price:?\s*\$?([0-9,]+\.?\d{0,2})',
                r'Price:?\s*\$?([0-9,]+\.?\d{0,2})',
                r'Rate:?\s*\$?([0-9,]+\.?\d{0,2})'
            ]
        }
    
    @property
    def parser_priority(self) -> List[str]:
        """Get parser priority order"""
        if self.settings.prefer_accuracy_over_speed:
            return ["pdfplumber", "pymupdf", "pypdf2"]
        else:
            return ["pypdf2", "pdfplumber", "pymupdf"]


# Global settings instance
settings = Settings()
database_config = DatabaseConfig(settings)
parsing_config = ParsingConfig(settings)


def get_settings() -> Settings:
    """Get the current settings instance"""
    return settings


def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return database_config


def get_parsing_config() -> ParsingConfig:
    """Get parsing configuration"""
    return parsing_config


def load_config_from_file(config_file: str) -> Settings:
    """Load configuration from a file"""
    # TODO: Implement configuration file loading
    # Support for JSON, YAML, TOML formats
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    # For now, just return default settings
    return Settings()


def validate_configuration() -> bool:
    """Validate the current configuration"""
    try:
        # Check storage directories
        for directory in [settings.storage_directory, settings.backup_directory, settings.sample_data_directory]:
            dir_path = Path(directory)
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    print(f"Cannot create directory {directory}: {e}")
                    return False
        
        # Check database URL format
        if not settings.database_url.startswith(('sqlite:', 'postgresql:', 'mysql:')):
            print(f"Unsupported database URL format: {settings.database_url}")
            return False
        
        # Check file size limits
        if settings.max_pdf_size <= 0:
            print("Invalid maximum PDF size")
            return False
        
        # Check confidence threshold
        if not 0.0 <= settings.extraction_confidence_threshold <= 1.0:
            print("Invalid confidence threshold")
            return False
        
        return True
        
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False


def print_configuration_summary():
    """Print a summary of current configuration"""
    print("=" * 50)
    print("Purchase Order PDF Parser Configuration")
    print("=" * 50)
    print(f"App Name: {settings.app_name}")
    print(f"Version: {settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Database URL: {settings.database_url}")
    print(f"Storage Directory: {settings.storage_directory}")
    print(f"Max PDF Size: {settings.max_pdf_size / (1024*1024):.1f} MB")
    print(f"Parsing Timeout: {settings.parsing_timeout} seconds")
    print(f"Confidence Threshold: {settings.extraction_confidence_threshold}")
    print(f"Supported Extensions: {', '.join(settings.supported_extensions)}")
    print(f"Log Level: {settings.log_level}")
    print("=" * 50)


def create_sample_env_file():
    """Create a sample .env file"""
    sample_env = """# Purchase Order PDF Parser Configuration
# Copy this file to .env and customize the values

# Application Settings
PO_PARSER_APP_NAME="Purchase Order PDF Parser"
PO_PARSER_APP_VERSION="1.0.0"
PO_PARSER_DEBUG=False
PO_PARSER_ENVIRONMENT="development"

# Database Settings
PO_PARSER_DATABASE_URL="sqlite:///./purchase_orders.db"
PO_PARSER_DATABASE_ECHO=False

# PDF Parsing Settings
PO_PARSER_MAX_PDF_SIZE=52428800  # 50MB
PO_PARSER_PARSING_TIMEOUT=120
PO_PARSER_EXTRACTION_CONFIDENCE_THRESHOLD=0.5

# Storage Settings
PO_PARSER_STORAGE_DIRECTORY="./storage"
PO_PARSER_BACKUP_DIRECTORY="./backups"
PO_PARSER_SAMPLE_DATA_DIRECTORY="./sample_data"

# Logging Settings
PO_PARSER_LOG_LEVEL="INFO"
PO_PARSER_LOG_FILE=""  # Empty for console only

# MCP Server Settings
PO_PARSER_SERVER_NAME="Purchase Order PDF Parser"

# Performance Settings
PO_PARSER_MAX_CONCURRENT_PARSERS=3
PO_PARSER_DATABASE_CONNECTION_TIMEOUT=30

# Data Validation Settings
PO_PARSER_MIN_PO_AMOUNT=0.01
PO_PARSER_MAX_PO_AMOUNT=1000000.00

# Search Settings
PO_PARSER_DEFAULT_SEARCH_LIMIT=20
PO_PARSER_MAX_SEARCH_LIMIT=100
"""
    
    with open(".env.example", "w") as f:
        f.write(sample_env)
    
    print("Sample .env file created as .env.example")
    print("Copy it to .env and customize the values as needed")


if __name__ == "__main__":
    # Print configuration summary when run as script
    print_configuration_summary()
    
    # Validate configuration
    if validate_configuration():
        print("✓ Configuration is valid")
    else:
        print("✗ Configuration validation failed")
    
    # Create sample .env file
    create_sample_env_file() 