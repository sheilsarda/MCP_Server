"""
FastMCP Server for Purchase Order PDF Parser

This server provides MCP tools for parsing PDF purchase orders and managing them in a database.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from loguru import logger

# TODO: Import modules when implementations are complete
# from ..database.connection import get_db_session, init_database, search_purchase_orders
# from ..database.models import PurchaseOrder, PurchaseOrderItem, PurchaseOrderCreate, PurchaseOrderItemCreate
# from ..pdf_parser.parser import PurchaseOrderPDFParser, PurchaseOrderData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Purchase Order PDF Parser")

# Initialize PDF parser
# pdf_parser = PurchaseOrderPDFParser()


class ParsePDFRequest(BaseModel):
    """Request model for PDF parsing"""
    file_path: str = Field(..., description="Path to the PDF file to parse")
    store_in_db: bool = Field(default=True, description="Whether to store the parsed data in database")


class ParsePDFResponse(BaseModel):
    """Response model for PDF parsing"""
    success: bool
    po_number: Optional[str] = None
    vendor: Optional[str] = None
    date: Optional[str] = None
    total_amount: Optional[float] = None
    line_items_count: int = 0
    extraction_confidence: float = 0.0
    extraction_method: Optional[str] = None
    database_id: Optional[int] = None
    error: Optional[str] = None


class SearchPORequest(BaseModel):
    """Request model for searching purchase orders"""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=20, description="Maximum number of results")
    include_line_items: bool = Field(default=False, description="Whether to include line item details")


class SearchPOResponse(BaseModel):
    """Response model for search results"""
    success: bool
    results: List[Dict[str, Any]]
    total_count: int
    error: Optional[str] = None


class POSummaryResponse(BaseModel):
    """Response model for PO summary statistics"""
    success: bool
    total_pos: int = 0
    total_value: float = 0.0
    unique_vendors: int = 0
    date_range: Optional[Dict[str, str]] = None
    top_vendors: List[Dict[str, Any]] = []
    error: Optional[str] = None


@mcp.tool()
async def parse_pdf_purchase_order(file_path: str, store_in_db: bool = True) -> ParsePDFResponse:
    """
    Parse a PDF purchase order and extract structured data.
    
    Args:
        file_path: Path to the PDF file
        store_in_db: Whether to store the parsed data in the database
    
    Returns:
        ParsePDFResponse with parsed data and storage results
    """
    try:
        logger.info(f"Parsing PDF purchase order: {file_path}")
        
        # Validate file exists
        if not Path(file_path).exists():
            return ParsePDFResponse(
                success=False,
                error=f"File not found: {file_path}"
            )
        
        # TODO: Implement actual PDF parsing
        # po_data = await pdf_parser.parse_pdf(file_path)
        
        # Placeholder response based on sample data
        po_data = create_sample_po_data()
        
        response = ParsePDFResponse(
            success=True,
            po_number=po_data.po_number,
            vendor=po_data.vendor,
            date=po_data.date.isoformat() if po_data.date else None,
            total_amount=float(po_data.total_amount) if po_data.total_amount else None,
            line_items_count=len(po_data.line_items),
            extraction_confidence=po_data.extraction_confidence,
            extraction_method=po_data.extraction_method
        )
        
        # Store in database if requested
        if store_in_db:
            try:
                database_id = await store_po_in_database(po_data, file_path)
                response.database_id = database_id
                logger.info(f"Stored PO in database with ID: {database_id}")
            except Exception as e:
                logger.error(f"Error storing PO in database: {e}")
                response.error = f"Parsing successful but database storage failed: {str(e)}"
        
        return response
        
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}")
        return ParsePDFResponse(
            success=False,
            error=str(e)
        )


@mcp.tool()
async def search_purchase_orders(query: str, limit: int = 20, include_line_items: bool = False) -> SearchPOResponse:
    """
    Search purchase orders by PO number, vendor, or other criteria.
    
    Args:
        query: Search query (PO number, vendor name, etc.)
        limit: Maximum number of results to return
        include_line_items: Whether to include line item details
    
    Returns:
        SearchPOResponse with matching purchase orders
    """
    try:
        logger.info(f"Searching purchase orders: {query}")
        
        # TODO: Implement actual database search
        # with get_db_session() as db:
        #     search_results = search_purchase_orders(db, query, limit)
        
        # Placeholder search results
        search_results = []
        if query.lower() in ["po-1003", "nova plastics", "polycarbonate"]:
            search_results = [
                {
                    "id": 1,
                    "po_number": "PO-1003",
                    "vendor": "Nova Plastics",
                    "date": "2024-10-08",
                    "total_amount": 77890.00,
                    "line_items_count": 1,
                    "extraction_confidence": 1.0,
                    "pdf_filename": "sample_po.pdf"
                }
            ]
        
        # Add line items if requested
        if include_line_items and search_results:
            for result in search_results:
                # TODO: Fetch actual line items from database
                result["line_items"] = [
                    {
                        "item_description": "Polycarbonate Sheet",
                        "quantity": 200,
                        "unit_price": 389.45,
                        "line_total": 77890.00
                    }
                ]
        
        return SearchPOResponse(
            success=True,
            results=search_results,
            total_count=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Error searching purchase orders: {e}")
        return SearchPOResponse(
            success=False,
            results=[],
            total_count=0,
            error=str(e)
        )


@mcp.tool()
async def get_purchase_order_by_id(po_id: int, include_line_items: bool = True) -> Dict[str, Any]:
    """
    Get a specific purchase order by database ID.
    
    Args:
        po_id: Database ID of the purchase order
        include_line_items: Whether to include line item details
    
    Returns:
        Dictionary with purchase order details
    """
    try:
        logger.info(f"Getting purchase order by ID: {po_id}")
        
        # TODO: Implement actual database lookup
        # with get_db_session() as db:
        #     po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        
        # Placeholder response
        if po_id == 1:
            po_data = {
                "success": True,
                "id": 1,
                "po_number": "PO-1003",
                "vendor": "Nova Plastics",
                "date": "2024-10-08",
                "total_amount": 77890.00,
                "pdf_filename": "sample_po.pdf",
                "extraction_confidence": 1.0,
                "extraction_method": "sample_data",
                "status": "extracted",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            if include_line_items:
                po_data["line_items"] = [
                    {
                        "id": 1,
                        "item_description": "Polycarbonate Sheet",
                        "quantity": 200,
                        "unit_price": 389.45,
                        "line_total": 77890.00
                    }
                ]
            
            return po_data
        else:
            return {
                "success": False,
                "error": f"Purchase order not found with ID: {po_id}"
            }
        
    except Exception as e:
        logger.error(f"Error getting purchase order {po_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def get_purchase_order_summary() -> POSummaryResponse:
    """
    Get summary statistics for all purchase orders.
    
    Returns:
        POSummaryResponse with summary statistics
    """
    try:
        logger.info("Getting purchase order summary")
        
        # TODO: Implement actual database statistics
        # with get_db_session() as db:
        #     stats = get_database_statistics(db)
        
        # Placeholder statistics
        return POSummaryResponse(
            success=True,
            total_pos=1,
            total_value=77890.00,
            unique_vendors=1,
            date_range={
                "earliest": "2024-10-08",
                "latest": "2024-10-08"
            },
            top_vendors=[
                {
                    "name": "Nova Plastics",
                    "total_orders": 1,
                    "total_amount": 77890.00
                }
            ]
        )
        
    except Exception as e:
        logger.error(f"Error getting purchase order summary: {e}")
        return POSummaryResponse(
            success=False,
            error=str(e)
        )


@mcp.tool()
async def list_purchase_orders(offset: int = 0, limit: int = 20, vendor: Optional[str] = None) -> Dict[str, Any]:
    """
    List purchase orders with pagination and optional filtering.
    
    Args:
        offset: Number of records to skip
        limit: Maximum number of records to return
        vendor: Optional vendor name filter
    
    Returns:
        Dictionary with purchase order list and pagination info
    """
    try:
        logger.info(f"Listing purchase orders (offset: {offset}, limit: {limit}, vendor: {vendor})")
        
        # TODO: Implement actual database query with pagination
        # with get_db_session() as db:
        #     query = db.query(PurchaseOrder)
        #     if vendor:
        #         query = query.filter(PurchaseOrder.vendor.ilike(f"%{vendor}%"))
        #     
        #     total_count = query.count()
        #     pos = query.offset(offset).limit(limit).all()
        
        # Placeholder response
        pos = []
        if vendor is None or vendor.lower() in "nova plastics":
            pos = [
                {
                    "id": 1,
                    "po_number": "PO-1003",
                    "vendor": "Nova Plastics",
                    "date": "2024-10-08",
                    "total_amount": 77890.00,
                    "line_items_count": 1,
                    "pdf_filename": "sample_po.pdf",
                    "status": "extracted",
                    "created_at": datetime.now().isoformat()
                }
            ]
        
        return {
            "success": True,
            "purchase_orders": pos,
            "total_count": len(pos),
            "offset": offset,
            "limit": limit,
            "has_more": False
        }
        
    except Exception as e:
        logger.error(f"Error listing purchase orders: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def validate_pdf_format(file_path: str) -> Dict[str, Any]:
    """
    Validate if a PDF file appears to contain purchase order data.
    
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
        
        # TODO: Implement actual PDF validation
        # pdf_info = await pdf_parser.get_pdf_info(file_path)
        # is_valid_po = validate_sample_data_format(pdf_info.get("text_preview", ""))
        
        # Placeholder validation
        file_info = {
            "file_size": Path(file_path).stat().st_size,
            "file_name": Path(file_path).name,
            "file_extension": Path(file_path).suffix,
            "is_pdf": Path(file_path).suffix.lower() == ".pdf"
        }
        
        return {
            "success": True,
            "is_valid_pdf": file_info["is_pdf"],
            "appears_to_be_po": file_info["is_pdf"],  # Placeholder
            "file_info": file_info,
            "validation_confidence": 0.8 if file_info["is_pdf"] else 0.0
        }
        
    except Exception as e:
        logger.error(f"Error validating PDF format: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Helper functions
async def store_po_in_database(po_data, file_path: str) -> int:
    """Store purchase order data in database"""
    try:
        # TODO: Implement actual database storage
        # with get_db_session() as db:
        #     # Create PO record
        #     po_create = PurchaseOrderCreate(
        #         po_number=po_data.po_number,
        #         vendor=po_data.vendor,
        #         date=po_data.date,
        #         total_amount=po_data.total_amount,
        #         pdf_filename=Path(file_path).name,
        #         pdf_path=file_path,
        #         parsing_confidence=po_data.extraction_confidence,
        #         extraction_method=po_data.extraction_method,
        #         raw_text=po_data.raw_text,
        #         extraction_metadata=po_data.metadata
        #     )
        #     
        #     po = PurchaseOrder(**po_create.dict())
        #     db.add(po)
        #     db.flush()
        #     
        #     # Create line items
        #     for item_data in po_data.line_items:
        #         item_create = PurchaseOrderItemCreate(
        #             **item_data,
        #             purchase_order_id=po.id
        #         )
        #         item = PurchaseOrderItem(**item_create.dict())
        #         db.add(item)
        #     
        #     db.commit()
        #     return po.id
        
        # Placeholder implementation
        return 1
        
    except Exception as e:
        logger.error(f"Error storing PO in database: {e}")
        raise


def create_sample_po_data():
    """Create sample PO data for testing"""
    from datetime import datetime
    from decimal import Decimal
    
    # Create a simple object with the sample data
    class SamplePOData:
        def __init__(self):
            self.po_number = "PO-1003"
            self.vendor = "Nova Plastics"
            self.date = datetime(2024, 10, 8)
            self.total_amount = Decimal("77890.00")
            self.line_items = [
                {
                    "item_description": "Polycarbonate Sheet",
                    "quantity": 200,
                    "unit_price": Decimal("389.45"),
                    "line_total": Decimal("77890.00")
                }
            ]
            self.extraction_confidence = 1.0
            self.extraction_method = "sample_data"
            self.raw_text = "Sample PO data"
            self.metadata = {"source": "sample"}
    
    return SamplePOData()


async def main():
    """Main function to run the MCP server"""
    try:
        # TODO: Initialize database
        # await init_database()
        
        logger.info("Starting Purchase Order PDF Parser MCP Server...")
        
        # Create sample data directory
        sample_dir = Path("sample_data")
        sample_dir.mkdir(exist_ok=True)
        
        # TODO: Add any additional initialization
        
        # Run the server
        await mcp.run()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 