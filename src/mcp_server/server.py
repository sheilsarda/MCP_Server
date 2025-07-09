"""
FastMCP Server for Business Document PDF Parser

This server provides MCP tools for parsing PDF documents and managing them in a database.

# COMPREHENSIVE AUDIT FEEDBACK - CRITICAL ARCHITECTURAL ISSUES:

## MAJOR ARCHITECTURAL PROBLEMS:
# 1. **MONOLITHIC DESIGN**: Single file handles server, parsing, database, serialization - violates SRP
# 2. **TIGHT COUPLING**: Direct database imports create circular dependency potential
# 3. **MISSING SERVICE LAYER**: Business logic mixed with API endpoints
# 4. **NO DEPENDENCY INJECTION**: Hard-coded dependencies make testing impossible
# 5. **ASYNC MISUSE**: Many "async" functions don't actually do async work
# 6. **NO ERROR BOUNDARIES**: Single failure can crash entire server

## CRITICAL BUGS & SECURITY ISSUES:
# 1. **PATH INJECTION**: file_path parameter not validated - arbitrary file system access
# 2. **RESOURCE EXHAUSTION**: No limits on PDF file size or processing time
# 3. **DATABASE INJECTION**: Search queries not properly parameterized
# 4. **MEMORY LEAKS**: Large PDF files loaded into memory without cleanup
# 5. **ERROR INFORMATION LEAKAGE**: Stack traces expose internal architecture
# 6. **NO AUTHENTICATION**: All endpoints publicly accessible

## CODE QUALITY VIOLATIONS:
# 1. **INCONSISTENT ERROR HANDLING**: Mix of exceptions, None returns, and error dicts
# 2. **DUPLICATE CODE**: Repeated try/catch blocks and logging patterns
# 3. **POOR LOGGING**: Logs go to stderr instead of proper logging framework
# 4. **MAGIC NUMBERS**: Hard-coded limits (20, etc.) scattered throughout
# 5. **INCONSISTENT RETURN TYPES**: Some functions return dicts, others Pydantic models
# 6. **MISSING TYPE VALIDATION**: Input parameters not validated against schemas

## PERFORMANCE CONCERNS:
# 1. **BLOCKING OPERATIONS**: File I/O and PDF parsing block the event loop
# 2. **NO CACHING**: Repeated database queries for same data
# 3. **INEFFICIENT SERIALIZATION**: Manual dict conversion instead of Pydantic
# 4. **NO PAGINATION**: Database queries could return unlimited results
# 5. **RESOURCE MANAGEMENT**: No connection pooling or resource limits

## RECOMMENDED ARCHITECTURAL FIXES:
# 1. Split into separate modules: routers/, services/, schemas/
# 2. Add proper dependency injection container
# 3. Implement service layer with business logic separation
# 4. Add comprehensive input validation and security middleware
# 5. Implement proper async patterns with background task processing
# 6. Add monitoring, metrics, and proper error handling
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

# Add the project root to the Python path to ensure imports work
# AUDIT: This path manipulation is brittle and indicates poor package structure
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from loguru import logger

# Configure loguru to use stderr instead of stdout for MCP compatibility
# AUDIT: Custom logging configuration should be in separate module
logger.remove()  # Remove default handler
logger.add(sys.stderr, format="{time} - {name} - {level} - {message}")

# Import database and parsing modules using absolute imports
# CIRCULAR DEPENDENCY RISK: These imports create tight coupling
from src.database.queries import (
    search_business_documents, get_document_by_id as db_get_document_by_id, 
    list_business_documents, get_database_summary, 
    search_by_document_number as db_search_by_document_number, 
    search_by_vendor as db_search_by_vendor, 
    get_purchase_orders as db_get_purchase_orders, 
    store_parsed_document, initialize_database, get_database_info
)
from src.database.models import DocumentType
from src.pdf_parser.parser import BusinessDocumentPDFParser

# Configure logging to stderr to avoid interfering with MCP JSON-RPC on stdout
# DUPLICATE: This duplicates loguru config above
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Ensure logs go to stderr, not stdout
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
# AUDIT: No configuration or error handling for server initialization
mcp = FastMCP("Business Document PDF Parser")

# Initialize PDF parser
# GLOBAL STATE: Parser should be injected, not global
pdf_parser = BusinessDocumentPDFParser()


class ParsePDFRequest(BaseModel):
    """Request model for PDF parsing
    
    # VALIDATION MISSING: No file path validation, size limits, or format checks
    """
    file_path: str = Field(..., description="Path to the PDF file to parse")
    store_in_db: bool = Field(default=True, description="Whether to store the parsed data in database")


class ParsePDFResponse(BaseModel):
    """Response model for PDF parsing
    
    # AUDIT ISSUES:
    # 1. **INCONSISTENT OPTIONAL FIELDS**: Some fields Optional, others not - unclear contract
    # 2. **TYPE CONFUSION**: extraction_confidence is float but could be Decimal
    # 3. **ERROR HANDLING**: Single error field for all error types
    """
    success: bool
    document_number: Optional[str] = None
    document_type: Optional[str] = None
    vendor: Optional[str] = None
    date: Optional[str] = None
    total_amount: Optional[float] = None
    line_items_count: int = 0
    extraction_confidence: float = 0.0
    extraction_method: Optional[str] = None
    database_id: Optional[int] = None
    error: Optional[str] = None


class SearchDocumentsRequest(BaseModel):
    """Request model for searching documents
    
    # SECURITY ISSUE: No query validation - potential injection attacks
    """
    query: str = Field(..., description="Search query")
    limit: int = Field(default=20, description="Maximum number of results")
    include_line_items: bool = Field(default=False, description="Whether to include line item details")


class SearchDocumentsResponse(BaseModel):
    """Response model for search results
    
    # AUDIT: No metadata about query performance, pagination, etc.
    """
    success: bool
    results: List[Dict[str, Any]]
    total_count: int
    error: Optional[str] = None


class DocumentSummaryResponse(BaseModel):
    """Response model for document summary statistics"""
    success: bool
    total_documents: int = 0
    document_counts: Dict[str, int] = {}
    total_value: float = 0.0
    unique_vendors: int = 0
    date_range: Optional[Dict[str, str]] = None
    top_vendors: List[Dict[str, Any]] = []
    error: Optional[str] = None


@mcp.tool()
async def parse_pdf_document(file_path: str, store_in_db: bool = True) -> ParsePDFResponse:
    """
    Parse a PDF document and extract structured data.
    
    Args:
        file_path: Path to the PDF file
        store_in_db: Whether to store the parsed data in the database
    
    Returns:
        ParsePDFResponse with parsed data and storage results
        
    # CRITICAL SECURITY ISSUES:
    # 1. **PATH INJECTION**: No validation of file_path - could access any file
    # 2. **RESOURCE EXHAUSTION**: No file size limits or processing timeouts  
    # 3. **ERROR INFORMATION LEAKAGE**: Full exception details exposed to client
    # 4. **NO RATE LIMITING**: Could be used for DoS attacks
    """
    try:
        # SECURITY ISSUE: No path validation
        logger.info(f"Parsing PDF document: {file_path}")
        
        # Validate file exists
        # INSUFFICIENT VALIDATION: Should check file extension, size, permissions
        if not Path(file_path).exists():
            return ParsePDFResponse(
                success=False,
                error=f"File not found: {file_path}"
            )
        
        # Parse the PDF
        # Now properly synchronous operation
        document_data = pdf_parser.parse_document(file_path)
        
        # Handle total_amount conversion safely
        # AUDIT: This manual conversion indicates poor type design
        total_amount_val = getattr(document_data, 'total_amount', None)
        total_amount = float(total_amount_val) if total_amount_val is not None else None
        
        response = ParsePDFResponse(
            success=True,
            document_number=document_data.document_number,
            document_type=document_data.document_type.value,
            vendor=document_data.vendor,
            date=document_data.date.isoformat() if document_data.date else None,
            total_amount=total_amount,
            line_items_count=len(document_data.line_items) if document_data.line_items else 0,
            extraction_confidence=document_data.extraction_confidence,
            extraction_method=document_data.extraction_method
        )
        
        # Store in database if requested
        if store_in_db:
            try:
                # BLOCKING OPERATION: Database operations should be truly async
                database_id = store_parsed_document(document_data, file_path)
                response.database_id = database_id
                logger.info(f"Stored document in database with ID: {database_id}")
            except Exception as e:
                # ERROR LEAKAGE: Internal error details exposed
                logger.error(f"Error storing document in database: {e}")
                response.error = f"Parsing successful but database storage failed: {str(e)}"
        
        return response
        
    except Exception as e:
        # SECURITY ISSUE: Full exception details exposed to client
        logger.error(f"Error parsing PDF {file_path}: {e}")
        return ParsePDFResponse(
            success=False,
            error=str(e)
        )


@mcp.tool()
async def search_documents(query: str, limit: int = 20, include_line_items: bool = False) -> SearchDocumentsResponse:
    """
    Search documents by document number, vendor, or other criteria.
    
    Args:
        query: Search query (document number, vendor name, etc.)
        limit: Maximum number of results to return
        include_line_items: Whether to include line item details
    
    Returns:
        SearchDocumentsResponse with matching documents
        
    # CRITICAL SECURITY ISSUES:
    # 1. **SQL INJECTION**: query parameter not properly validated/sanitized
    # 2. **NO RATE LIMITING**: Could be used for database DoS
    # 3. **RESOURCE EXHAUSTION**: No upper limit validation on limit parameter
    """
    try:
        # SECURITY ISSUE: No input validation on query parameter
        logger.info(f"Searching documents: {query}")
        
        # BLOCKING OPERATION: Database query should be truly async
        search_results = search_business_documents(
            query=query,
            limit=limit,
            include_line_items=include_line_items
        )
        
        return SearchDocumentsResponse(
            success=True,
            results=search_results,
            total_count=len(search_results)
        )
        
    except Exception as e:
        # ERROR LEAKAGE: Internal database errors exposed
        logger.error(f"Error searching documents: {e}")
        return SearchDocumentsResponse(
            success=False,
            results=[],
            total_count=0,
            error=str(e)
        )


@mcp.tool()
async def get_document_details(document_id: int, include_line_items: bool = True) -> Dict[str, Any]:
    """
    Get a specific document by database ID.
    
    Args:
        document_id: Database ID of the document
        include_line_items: Whether to include line item details
    
    Returns:
        Dictionary with document details
    """
    try:
        logger.info(f"Getting document by ID: {document_id}")
        
        document = db_get_document_by_id(document_id, include_line_items=include_line_items)
        
        if document:
            return {
                "success": True,
                **document
            }
        else:
            return {
                "success": False,
                "error": f"Document not found with ID: {document_id}"
            }
        
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def get_document_summary() -> DocumentSummaryResponse:
    """
    Get summary statistics for all documents.
    
    Returns:
        DocumentSummaryResponse with summary statistics
    """
    try:
        logger.info("Getting document summary")
        
        summary = get_database_summary()
        
        return DocumentSummaryResponse(
            success=True,
            total_documents=summary['total_documents'],
            document_counts=summary['document_counts'],
            total_value=summary['total_value'],
            unique_vendors=summary['unique_vendors'],
            date_range=summary['date_range'],
            top_vendors=summary['top_vendors']
        )
        
    except Exception as e:
        logger.error(f"Error getting document summary: {e}")
        return DocumentSummaryResponse(
            success=False,
            error=str(e)
        )


@mcp.tool()
async def list_documents(offset: int = 0, limit: int = 20, vendor: Optional[str] = None, document_type: Optional[str] = None) -> Dict[str, Any]:
    """
    List documents with pagination and optional filtering.
    
    Args:
        offset: Number of records to skip
        limit: Maximum number of records to return
        vendor: Optional vendor name filter
        document_type: Optional document type filter
    
    Returns:
        Dictionary with document list and pagination info
    """
    try:
        logger.info(f"Listing documents (offset: {offset}, limit: {limit}, vendor: {vendor}, type: {document_type})")
        
        # Convert document_type string to enum if provided
        doc_type_enum = None
        if document_type:
            try:
                doc_type_enum = DocumentType(document_type)
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid document type: {document_type}"
                }
        
        result = list_business_documents(
            limit=limit,
            offset=offset,
            vendor=vendor,
            document_type=doc_type_enum
        )
        
        return {
            "success": True,
            "documents": result["documents"],
            "total_count": result["total_count"],
            "offset": offset,
            "limit": limit,
            "has_more": result["has_more"]
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def validate_pdf_format(file_path: str) -> Dict[str, Any]:
    """
    Validate if a PDF file appears to contain business document data.
    
    Args:
        file_path: Path to the PDF file to validate
    
    Returns:
        Dictionary with validation results
    """
    try:
        logger.info(f"Validating PDF format: {file_path}")
        
        # Check if file exists
        if not Path(file_path).exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        # Use PDF parser to check if it's supported
        is_supported = pdf_parser.is_supported(file_path)
        
        # Get basic file info
        file_info = {
            "file_size": Path(file_path).stat().st_size,
            "file_name": Path(file_path).name,
            "file_extension": Path(file_path).suffix,
            "is_pdf": Path(file_path).suffix.lower() == ".pdf"
        }
        
        return {
            "success": True,
            "is_valid_pdf": file_info["is_pdf"],
            "is_supported": is_supported,
            "appears_to_be_business_doc": is_supported and file_info["is_pdf"],
            "file_info": file_info,
            "validation_confidence": 0.9 if is_supported else 0.1
        }
        
    except Exception as e:
        logger.error(f"Error validating PDF format: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def search_by_document_number(document_number: str, exact_match: bool = False) -> Dict[str, Any]:
    """
    Search for a document by its document number.
    
    Args:
        document_number: Document number to search for
        exact_match: Whether to do exact match or partial match
    
    Returns:
        Dictionary with document details or error
    """
    try:
        logger.info(f"Searching by document number: {document_number}")
        
        document = db_search_by_document_number(document_number, exact_match=exact_match)
        
        if document:
            return {
                "success": True,
                **document
            }
        else:
            return {
                "success": False,
                "error": f"Document not found with number: {document_number}"
            }
        
    except Exception as e:
        logger.error(f"Error searching by document number: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def search_by_vendor(vendor_name: str, limit: int = 20) -> Dict[str, Any]:
    """
    Search for documents by vendor name.
    
    Args:
        vendor_name: Vendor name to search for
        limit: Maximum number of results
    
    Returns:
        Dictionary with search results
    """
    try:
        logger.info(f"Searching by vendor: {vendor_name}")
        
        documents = db_search_by_vendor(vendor_name, limit=limit)
        
        return {
            "success": True,
            "documents": documents,
            "total_count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error searching by vendor: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def get_purchase_orders(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """
    Get purchase orders with their details.
    
    Args:
        limit: Maximum number of results
        offset: Number of results to skip
    
    Returns:
        Dictionary with purchase order list
    """
    try:
        logger.info(f"Getting purchase orders (limit: {limit}, offset: {offset})")
        
        purchase_orders = db_get_purchase_orders(limit=limit, offset=offset)
        
        return {
            "success": True,
            "purchase_orders": purchase_orders,
            "total_count": len(purchase_orders)
        }
        
    except Exception as e:
        logger.error(f"Error getting purchase orders: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def initialize_database_tables() -> Dict[str, Any]:
    """
    Initialize the database with all required tables.
    
    Returns:
        Dictionary with initialization results
    """
    try:
        logger.info("Initializing database tables")
        
        db_path = initialize_database()
        db_info = get_database_info(db_path)
        
        return {
            "success": True,
            "database_path": db_path,
            "database_info": db_info
        }
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Main function to run the MCP server"""
    try:
        logger.info("Starting Business Document PDF Parser MCP Server...")
        
        # Initialize database if needed
        try:
            initialize_database()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.warning(f"Database initialization warning: {e}")
        
        # Run the server - Note: FastMCP.run() is synchronous, not async
        mcp.run()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise


if __name__ == "__main__":
    main() 