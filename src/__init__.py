"""
Purchase Order PDF Parser

A FastMCP-based server for parsing PDF purchase orders and storing them in a database.

# AUDIT FEEDBACK - PACKAGE INITIALIZATION ISSUES:
# 1. **COMMENTED IMPORTS**: Dead code indicates incomplete implementation
# 2. **INCONSISTENT NAMING**: Package called "Purchase Order" but handles multiple document types  
# 3. **MISSING EXPORTS**: No public API defined for package consumers
# 4. **CIRCULAR IMPORTS**: Potential issues with cross-module dependencies
# 5. **VERSION MANAGEMENT**: Version string not connected to proper versioning system

# RECOMMENDATIONS:
# - Remove commented code or implement missing functionality
# - Define clear public API with __all__ 
# - Fix naming to reflect actual scope (Business Document Parser)
# - Add proper version management
"""

__version__ = "1.0.0"
__author__ = "PO Parser Team"  # AUDIT: Should reflect actual team/organization
__description__ = "FastMCP server for parsing PDF purchase orders"  # AUDIT: Description too narrow

# IMPROVEMENT: Define public API exports
# __all__ = [
#     "BusinessDocumentPDFParser",
#     "DocumentType", 
#     "DocumentData",
#     "get_database_session",
#     "initialize_database"
# ]

# AUDIT NOTE: All imports are commented out - indicates incomplete implementation
# This suggests the package is not ready for production use
# Either implement the missing functionality or remove the commented code

# TODO: Add main package imports when implementations are complete
# from .mcp_server.server import mcp, main
# from .database.models import PurchaseOrder, PurchaseOrderItem
# from .database.connection import get_db_session, init_database
# from .pdf_parser.parser import PurchaseOrderPDFParser
# from .config import get_settings 