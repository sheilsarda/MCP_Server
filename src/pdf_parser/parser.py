"""
PDF Parser for Business Documents (Purchase Orders, Invoices, Receipts)

Extracts structured data from PDF documents using multiple parsing strategies.

# COMPREHENSIVE AUDIT FEEDBACK - CRITICAL DESIGN ISSUES:

## MAJOR ARCHITECTURAL PROBLEMS:
# ✅ **FAKE ASYNC**: FIXED - All methods now properly synchronous
# 1. **ENUM DUPLICATION**: DocumentType duplicated from models.py - import conflict risk  
# 2. **MONOLITHIC CLASS**: Single class handles parsing, validation, extraction, cleaning
# 3. **POOR ABSTRACTION**: Hardcoded regex patterns mixed with business logic
# 4. **NO STRATEGY PATTERN**: Different document types need different parsing strategies
# 5. **TIGHT COUPLING**: Parser tightly coupled to specific dataclass structures

## CRITICAL BUGS & RELIABILITY ISSUES:  
# 1. **SILENT FAILURES**: Many extraction methods return None without logging why
# 2. **REGEX VULNERABILITIES**: Complex regex patterns could cause ReDoS attacks
# 3. **ENCODING ISSUES**: No handling of non-UTF8 PDFs or special characters
# 4. **MEMORY LEAKS**: Large PDF content kept in memory unnecessarily
# 5. **BRITTLE PATTERNS**: Hardcoded regex will break with format variations
# 6. **CONFIDENCE CALCULATION**: Meaningless confidence score - poor business value

## SECURITY & VALIDATION CONCERNS:
# 1. **NO FILE VALIDATION**: No checks for malicious PDF content or size limits
# 2. **ARBITRARY FILE ACCESS**: No path traversal protection
# 3. **RESOURCE EXHAUSTION**: No timeouts or limits on PDF processing
# 4. **INPUT SANITIZATION**: Extracted text not sanitized before database storage  
# 5. **ERROR INFORMATION LEAKAGE**: File paths and internal details in error messages

## CODE QUALITY VIOLATIONS:
# 1. **COMMENTED IMPORTS**: Dead code indicates incomplete implementation
# 2. **DEBUGGING ARTIFACTS**: logger.debug calls should be removed from production
# 3. **MAGIC NUMBERS**: Hardcoded pattern indexes and confidence thresholds
# 4. **INCONSISTENT ERROR HANDLING**: Mix of exceptions, None returns, empty values
# 5. **POOR NAMING**: Generic method names like _extract_field don't describe purpose
# 6. **MISSING DOCUMENTATION**: Complex regex patterns have no explanation

## PERFORMANCE & SCALABILITY ISSUES:
# ✅ **BLOCKING I/O**: FIXED - Now properly synchronous, no misleading async
# 1. **INEFFICIENT PARSING**: Entire PDF loaded into memory before processing
# 2. **REPEATED REGEX COMPILATION**: Patterns recompiled on every use
# 3. **NO CACHING**: Same documents could be reparsed multiple times
# 4. **MEMORY INEFFICIENT**: Raw text stored multiple times unnecessarily

## RECOMMENDED FIXES:
# ✅ Remove fake async - COMPLETED: All methods now properly synchronous
# 1. Implement strategy pattern for different document types
# 2. Create proper validation pipeline with security checks
# 3. Extract regex patterns to configuration with explanation
# 4. Add comprehensive error handling and logging
# 5. Implement proper caching and resource management
# 6. Split into multiple focused classes (Parser, Validator, Extractor)
"""

import re
import pypdf
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Configure logging to stderr to avoid interfering with MCP JSON-RPC
# AUDIT: Logging configuration belongs in separate module
logger = logging.getLogger(__name__)
# Ensure logs go to stderr
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# TODO: Import PDF parsing libraries (uncomment when packages are installed)
# AUDIT: TODO comments indicate incomplete implementation - technical debt
# import fitz  # PyMuPDF
# import pdfplumber
# from dateutil.parser import parse as parse_date

class DocumentType(Enum):
    """Enumeration of supported document types
    
    # CRITICAL BUG: This enum DUPLICATES the one in models.py
    # This will cause import conflicts and inconsistent behavior
    # SOLUTION: Use shared enums module or import from models
    """
    PURCHASE_ORDER = "purchase_order"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    UNKNOWN = "unknown"

@dataclass
class DocumentData:
    """Base class for structured document data extracted from PDF
    
    # AUDIT ISSUES:
    # 1. **MUTABLE DEFAULTS**: line_items and metadata lists/dicts could be shared
    # 2. **WEAK TYPING**: Optional fields without validation
    # 3. **MIXED RESPONSIBILITIES**: Data container also has business logic in __post_init__
    """
    document_type: DocumentType = DocumentType.UNKNOWN
    document_number: Optional[str] = None
    vendor: Optional[str] = None
    date: Optional[datetime] = None
    line_items: Optional[List[Dict[str, Any]]] = None # catch-all
    extraction_confidence: float = 0.0
    extraction_method: str = "unknown"
    raw_text: str = ""
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        # MUTABLE DEFAULT ANTIPATTERN: These should be set to new instances
        if self.line_items is None:
            self.line_items = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class PurchaseOrderData(DocumentData):
    """Purchase Order specific data
    
    # AUDIT: Redundant field mapping in __post_init__ indicates poor design
    """
    po_number: Optional[str] = None
    total_amount: Optional[Decimal] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.document_type = DocumentType.PURCHASE_ORDER
        # Map po_number to document_number for consistency
        # AUDIT: This mapping logic should be in a service layer, not data class
        if self.po_number:
            self.document_number = self.po_number

@dataclass
class InvoiceData(DocumentData):
    """Invoice specific data
    
    # AUDIT: Nearly identical to ReceiptData - violates DRY principle
    """
    invoice_number: Optional[str] = None
    reference_po: Optional[str] = None
    item: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    # Vendor info is covered in the base class
    
    def __post_init__(self):
        super().__post_init__()
        self.document_type = DocumentType.INVOICE
        # Map invoice_number to document_number for consistency
        if self.invoice_number:
            self.document_number = self.invoice_number

@dataclass
class ReceiptData(DocumentData):
    """Receipt specific data
    
    # AUDIT: Code duplication with InvoiceData - should use common base or composition
    """
    receipt_id: Optional[str] = None
    reference_po: Optional[str] = None
    item: Optional[str] = None
    quantity_received: Optional[int] = None
    date_received: Optional[datetime] = None
    # Vendor info is covered in the base class
    
    def __post_init__(self):
        super().__post_init__()
        self.document_type = DocumentType.RECEIPT
        # Map receipt_id to document_number for consistency
        if self.receipt_id:
            self.document_number = self.receipt_id


class BusinessDocumentPDFParser:
    """
    PDF parser for business documents (Purchase Orders, Invoices, Receipts)
    
    # AUDIT ISSUES:
    # 1. **MONOLITHIC CLASS**: Handles parsing, validation, extraction, cleaning all in one
    # 2. **HARDCODED PATTERNS**: Regex patterns should be configurable/external
    # 3. **NO CACHING**: Compiled regex patterns recreated on every use
    # 4. **POOR ENCAPSULATION**: Large dictionaries of patterns are hard to maintain
    # 5. **MISSING ABSTRACTIONS**: No interfaces or base classes for extensibility
    """
    
    def __init__(self):
        self.supported_extensions = ['.pdf']
        
        # Document type detection patterns
        # AUDIT: These hardcoded patterns are brittle and hard to maintain
        # IMPROVEMENT: Move to external configuration file with documentation
        self.document_type_patterns = {
            DocumentType.PURCHASE_ORDER: [
                r'Purchase\s+Order',
                r'PO\s+Number',
                r'P\.O\.\s+Number'
            ],
            DocumentType.INVOICE: [
                r'Invoice',
                r'Invoice\s+Number',
                r'INV[-\s]?\d+'
            ],
            DocumentType.RECEIPT: [
                r'Receipt',
                r'Delivery\s+Receipt',
                r'Receipt\s+ID',
                r'RCPT[-\s]?\d+'
            ]
        }
        
        # Regex patterns for extracting document data
        # SECURITY ISSUE: Complex regex patterns could be vulnerable to ReDoS attacks
        # MAINTAINABILITY: This massive dictionary is hard to understand and modify
        self.extraction_patterns = {
            # Purchase Order patterns
            'po_number': [
                r'PO[-\s]?Number:?\s*([A-Z0-9-]+)',
                r'Purchase\s+Order:?\s*([A-Z0-9-]+)',
                r'P\.O\.?\s*:?\s*([A-Z0-9-]+)',
                r'Order\s+Number:?\s*([A-Z0-9-]+)',
                r'(PO[-]?\d{3,6})'  # Generic PO pattern
            ],
            
            # Invoice patterns
            'invoice_number': [
                r'Invoice[-\s]?Number:?\s*([A-Z0-9-]+)',
                r'Invoice:?\s*([A-Z0-9-]+)',
                r'INV[-\s]?Number:?\s*([A-Z0-9-]+)',
                r'(INV[-]?\d{3,6})'  # Generic INV pattern
            ],
            
            # Receipt patterns
            'receipt_id': [
                r'Receipt[-\s]?ID:?\s*([A-Z0-9-]+)',
                r'Receipt:?\s*([A-Z0-9-]+)',
                r'RCPT[-\s]?ID:?\s*([A-Z0-9-]+)',
                r'(RCPT[-]?\d{3,6})'  # Generic RCPT pattern
            ],
            
            # Common patterns
            'vendor': [
                r'Vendor:?\s*([A-Za-z\s&.,\'-]+?)(?:\n|$)',
                r'Supplier:?\s*([A-Za-z\s&.,\'-]+?)(?:\n|$)',
                r'Company:?\s*([A-Za-z\s&.,\'-]+?)(?:\n|$)',
                r'Bill\s+To:?\s*([A-Za-z\s&.,\'-]+?)(?:\n|$)'
            ],
            
            'date': [
                r'Date:?\s*(\d{4}-\d{2}-\d{2})',
                r'Date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Order\s+Date:?\s*(\d{4}-\d{2}-\d{2})',
                r'Order\s+Date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Invoice\s+Date:?\s*(\d{4}-\d{2}-\d{2})',
                r'Invoice\s+Date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{4}-\d{2}-\d{2})'  # Generic ISO date
            ],
            
            'date_received': [
                r'Date\s+Received:?\s*(\d{4}-\d{2}-\d{2})',
                r'Date\s+Received:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Received:?\s*(\d{4}-\d{2}-\d{2})',
                r'Received:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            
            'reference_po': [
                r'Reference\s+PO:?\s*([A-Z0-9-]+)',
                r'PO\s+Reference:?\s*([A-Z0-9-]+)',
                r'Original\s+PO:?\s*([A-Z0-9-]+)',
                r'Ref\.?\s+PO:?\s*([A-Z0-9-]+)'
            ],
            
            'total': [
                r'Total:?\s*\$?([0-9,]+\.?\d{0,2})',
                r'Grand\s+Total:?\s*\$?([0-9,]+\.?\d{0,2})',
                r'Amount:?\s*\$?([0-9,]+\.?\d{0,2})',
                r'Sum:?\s*\$?([0-9,]+\.?\d{0,2})'
            ],
            
            'item': [
                r'Item:?\s*([A-Za-z\s\-&.,]+)',
                r'Description:?\s*([A-Za-z\s\-&.,]+)',
                r'Product:?\s*([A-Za-z\s\-&.,]+)'
            ],
            
            'quantity': [
                r'Quantity:?\s*(\d+)',
                r'Qty:?\s*(\d+)',
                r'Amount:?\s*(\d+)\s*(?:EA|Each|Units?)',
                r'(\d+)\s*(?:EA|Each|Units?)'
            ],
            
            'quantity_received': [
                r'Quantity\s+Received:?\s*(\d+)',
                r'Qty\s+Received:?\s*(\d+)',
                r'Received:?\s*(\d+)\s*(?:EA|Each|Units?)'
            ],
            
            'unit_price': [
                r'Unit\s+Price:?\s*\$?([0-9,]+\.?\d{0,2})',
                r'Price:?\s*\$?([0-9,]+\.?\d{0,2})',
                r'Rate:?\s*\$?([0-9,]+\.?\d{0,2})'
            ]
        }
    
    def parse_document(self, file_path: str) -> Union[PurchaseOrderData, InvoiceData, ReceiptData, DocumentData]:
        """
        Parse a PDF document and extract structured data
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            DocumentData object with extracted information (specific subtype based on document type)
            
        # FIXED: Removed fake async - function now properly synchronous
        # REMAINING ISSUES:
        # 1. **SECURITY VULNERABILITY**: No file path validation - directory traversal risk  
        # 2. **RESOURCE MANAGEMENT**: No timeout or size limits - DoS vulnerability
        # 3. **ERROR HANDLING**: Generic validation that doesn't check file type/corruption
        """
        try:
            # SECURITY ISSUE: No path validation or sanitization
            logger.info(f"Parsing document: {file_path}")
            
            # Validate file
            # INSUFFICIENT VALIDATION: Only checks if file exists, not if it's safe
            if not self._validate_pdf(file_path):
                raise ValueError(f"Invalid PDF file: {file_path}")
            
            # Extract raw text
            # Now properly synchronous operation
            raw_text = self._extract_text_with_pypdf(file_path)
            
            # Detect document type
            document_type = self._detect_document_type(raw_text)
            logger.info(f"Detected document type: {document_type.value}")
            
            # Extract structured data based on document type
            if document_type == DocumentType.PURCHASE_ORDER:
                result = self._extract_purchase_order_data(raw_text)
            elif document_type == DocumentType.INVOICE:
                result = self._extract_invoice_data(raw_text)
            elif document_type == DocumentType.RECEIPT:
                result = self._extract_receipt_data(raw_text)
            else:
                # Default to generic document data
                result = self._extract_generic_document_data(raw_text)
            
            result.extraction_method = "pypdf"
            result.raw_text = raw_text
            
            # Post-process and validate
            validated_result = self._validate_and_clean_data(result)
            
            logger.info(f"Document parsing completed. Confidence: {validated_result.extraction_confidence:.2f}")
            return validated_result
            
        except Exception as e:
            logger.error(f"Error parsing document {file_path}: {e}")
            raise
    
    def _detect_document_type(self, text: str) -> DocumentType:
        """Detect the type of document based on text content"""
        text_upper = text.upper()
        
        # Check for each document type
        for doc_type, patterns in self.document_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_upper, re.IGNORECASE):
                    return doc_type
        
        return DocumentType.UNKNOWN
    
    def _extract_purchase_order_data(self, text: str) -> PurchaseOrderData:
        """Extract purchase order specific data"""
        po_data = PurchaseOrderData()
        
        # Extract PO-specific fields
        po_data.po_number = self._extract_field(text, 'po_number')
        po_data.vendor = self._extract_field(text, 'vendor')
        po_data.date = self._parse_date_field(text, 'date')
        po_data.total_amount = self._parse_currency_field(text, 'total')
        po_data.line_items = self._extract_line_items(text)
        
        # Set document_number for consistency
        if po_data.po_number:
            po_data.document_number = po_data.po_number
        
        po_data.extraction_confidence = self._calculate_confidence(po_data)
        
        return po_data
    
    def _extract_invoice_data(self, text: str) -> InvoiceData:
        """Extract invoice specific data"""
        invoice_data = InvoiceData()
        
        # Extract invoice-specific fields
        invoice_data.invoice_number = self._extract_field(text, 'invoice_number')
        invoice_data.reference_po = self._extract_field(text, 'reference_po')
        invoice_data.vendor = self._extract_field(text, 'vendor')
        invoice_data.date = self._parse_date_field(text, 'date')
        invoice_data.total_amount = self._parse_currency_field(text, 'total')
        invoice_data.line_items = self._extract_line_items(text)
        
        # Set document_number for consistency
        if invoice_data.invoice_number:
            invoice_data.document_number = invoice_data.invoice_number
        
        invoice_data.extraction_confidence = self._calculate_confidence(invoice_data)
        
        return invoice_data
    
    def _extract_receipt_data(self, text: str) -> ReceiptData:
        """Extract receipt specific data"""
        receipt_data = ReceiptData()
        
        # Extract receipt-specific fields
        receipt_data.receipt_id = self._extract_field(text, 'receipt_id')
        receipt_data.vendor = self._extract_field(text, 'vendor')
        receipt_data.reference_po = self._extract_field(text, 'reference_po')
        receipt_data.item = self._extract_field(text, 'item')
        receipt_data.quantity_received = self._parse_int_field(text, 'quantity_received')
        receipt_data.date_received = self._parse_date_field(text, 'date_received')
        # receipt_data.line_items = self._extract_line_items(text)
        
        # Set document_number for consistency
        if receipt_data.receipt_id:
            receipt_data.document_number = receipt_data.receipt_id
        
        receipt_data.extraction_confidence = self._calculate_confidence(receipt_data)
        
        return receipt_data
    
    def _extract_generic_document_data(self, text: str) -> DocumentData:
        """Extract generic document data when type is unknown"""
        doc_data = DocumentData()
        
        # Extract common fields
        doc_data.vendor = self._extract_field(text, 'vendor')
        doc_data.date = self._parse_date_field(text, 'date')
        doc_data.line_items = self._extract_line_items(text)
        doc_data.extraction_confidence = self._calculate_confidence(doc_data)
        
        return doc_data
    
    def _validate_pdf(self, file_path: str) -> bool:
        """Validate if file is a readable PDF"""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return False
            
            if file_path_obj.suffix.lower() not in self.supported_extensions:
                return False
            
            # TODO: Add more PDF validation
            # - Check PDF magic number
            # - Verify PDF structure
            # - Check for encryption
            
            return True
            
        except Exception as e:
            logger.error(f"PDF validation failed: {e}")
            return False
    
    def _extract_text_with_pypdf(self, file_path: str) -> str:
        """Extract text using pypdf"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            logger.error(f"pypdf extraction failed: {e}")
            raise
    
    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """Extract a specific field using regex patterns"""
        patterns = self.extraction_patterns.get(field_name, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                result = match.group(1).strip()
                logger.debug(f"Extracted {field_name}: {result}")
                return result
        
        logger.debug(f"Could not extract {field_name}")
        return None
    
    def _parse_date_field(self, text: str, field_name: str) -> Optional[datetime]:
        """Parse date field from text"""
        date_str = self._extract_field(text, field_name)
        if date_str:
            return self._parse_date(date_str)
        return None
    
    def _parse_currency_field(self, text: str, field_name: str) -> Optional[Decimal]:
        """Parse currency field from text"""
        currency_str = self._extract_field(text, field_name)
        if currency_str:
            return self._parse_currency(currency_str)
        return None
    
    def _parse_int_field(self, text: str, field_name: str) -> Optional[int]:
        """Parse integer field from text"""
        int_str = self._extract_field(text, field_name)
        if int_str:
            try:
                return int(int_str)
            except ValueError:
                logger.error(f"Error parsing integer '{int_str}' for field {field_name}")
                return None
        return None
    
    def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract line items from text"""
        # TODO: Implement line item extraction
        # - Look for table-like structures
        # - Match quantities, prices, and descriptions
        # - Handle multi-line items
        # - Calculate line totals
        
        line_items = []
        
        # Simple placeholder logic
        item_match = self._extract_field(text, 'item')
        quantity_match = self._extract_field(text, 'quantity')
        price_match = self._extract_field(text, 'unit_price')
        
        if item_match and quantity_match and price_match:
            quantity = int(quantity_match)
            unit_price = self._parse_currency(price_match)
            
            line_item = {
                'item_description': item_match,
                'quantity': quantity,
                'unit_price': unit_price,
                'line_total': unit_price * quantity if unit_price else None,
                'extraction_confidence': 0.7
            }
            line_items.append(line_item)
        
        return line_items
    
    def _parse_currency(self, amount_str: str) -> Optional[Decimal]:
        """Parse currency string to Decimal"""
        try:
            # Remove currency symbols and thousands separators
            clean_str = re.sub(r'[$,]', '', amount_str.strip())
            return Decimal(clean_str)
        except Exception as e:
            logger.error(f"Error parsing currency '{amount_str}': {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        try:
            # TODO: Use dateutil.parser when available for more robust parsing
            # For now using simple regex patterns - dateutil would handle more formats
            # return parse_date(date_str)
            
            # Simple date parsing for now
            date_patterns = [
                r'(\d{4})-(\d{2})-(\d{2})',
                r'(\d{1,2})/(\d{1,2})/(\d{4})',
                r'(\d{1,2})-(\d{1,2})-(\d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_str)
                if match:
                    if len(match.group(1)) == 4:  # YYYY-MM-DD
                        year, month, day = match.groups()
                    else:  # MM/DD/YYYY or MM-DD-YYYY
                        month, day, year = match.groups()
                    
                    return datetime(int(year), int(month), int(day))
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {e}")
            return None
    
    ## TODO: PRIORITY - Replace this naive confidence calculation with proper validation metrics
    ## Current approach is overly simplistic and provides little business value
    ## Consider: field validation quality, format adherence, cross-validation with known patterns
    def _calculate_confidence(self, doc_data: DocumentData) -> float:
        """Calculate extraction confidence score"""
        confidence_factors = []
        
        # Required fields
        if doc_data.document_number:
            confidence_factors.append(0.3)
        if doc_data.vendor:
            confidence_factors.append(0.2)
        if doc_data.date:
            confidence_factors.append(0.1)
        
        # Total amount (only for documents that have this field)
        total_amount = getattr(doc_data, 'total_amount', None)
        if total_amount:
            confidence_factors.append(0.2)
        
        # Line items
        if doc_data.line_items:
            confidence_factors.append(0.2)
        
        # Document type specific bonuses
        if isinstance(doc_data, PurchaseOrderData) and doc_data.po_number:
            confidence_factors.append(0.1)
        elif isinstance(doc_data, InvoiceData) and doc_data.invoice_number:
            confidence_factors.append(0.1)
        elif isinstance(doc_data, ReceiptData) and doc_data.receipt_id:
            confidence_factors.append(0.1)
        
        # Calculate total confidence
        total_confidence = sum(confidence_factors)
        
        # Bonus for complete data
        if len(confidence_factors) >= 5:
            total_confidence += 0.1
        
        return min(total_confidence, 1.0)
    
    def _validate_and_clean_data(self, doc_data: DocumentData) -> DocumentData:
        """Validate and clean extracted data"""
        try:
            # Clean vendor name
            if doc_data.vendor:
                doc_data.vendor = self._clean_vendor_name(doc_data.vendor)
            
            # Validate document number format
            if doc_data.document_number:
                doc_data.document_number = self._clean_document_number(doc_data.document_number)
            
            # Validate date range
            if doc_data.date:
                if doc_data.date.year < 2000 or doc_data.date.year > 2030:
                    logger.warning(f"Date seems invalid: {doc_data.date}")
                    doc_data.date = None
            
            # Validate amounts (only for documents that have this field)
            total_amount = getattr(doc_data, 'total_amount', None)
            if total_amount and total_amount <= 0:
                logger.warning(f"Total amount seems invalid: {total_amount}")
                setattr(doc_data, 'total_amount', None)
            
            # Validate line items
            if doc_data.line_items:
                for item in doc_data.line_items:
                    if item.get('quantity', 0) <= 0:
                        logger.warning(f"Invalid quantity in line item: {item}")
                    if item.get('unit_price', 0) <= 0:
                        logger.warning(f"Invalid unit price in line item: {item}")
            
            return doc_data
            
        except Exception as e:
            logger.error(f"Error validating data: {e}")
            return doc_data
    
    def _clean_vendor_name(self, vendor: str) -> str:
        """Clean and normalize vendor name"""
        # Remove extra whitespace
        vendor = ' '.join(vendor.split())
        
        # Remove common trailing characters
        vendor = vendor.rstrip('.,;:')
        
        # TODO: Add more vendor name cleaning
        # - Handle common abbreviations
        # - Standardize company suffixes
        # - Remove duplicate words
        
        return vendor
    
    def _clean_document_number(self, doc_number: str) -> str:
        """Clean and normalize document number"""
        # Remove extra whitespace
        doc_number = doc_number.strip()
        
        # Ensure consistent format
        doc_number = doc_number.upper()
        
        # TODO: Add more document number cleaning
        # - Standardize document number format
        # - Add check digits validation
        
        return doc_number
    
    def is_supported(self, file_path: str) -> bool:
        """Check if file type is supported"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def get_document_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic document information"""
        try:
            file_path_obj = Path(file_path)
            
            return {
                "file_size": file_path_obj.stat().st_size,
                "file_name": file_path_obj.name,
                "file_extension": file_path_obj.suffix,
                "created_date": file_path_obj.stat().st_ctime,
                "modified_date": file_path_obj.stat().st_mtime,
                "page_count": 0,  # TODO: Get actual page count
                "is_encrypted": False,  # TODO: Check if PDF is encrypted
                "parser_version": "2.0.0"
            }
            
        except Exception as e:
            logger.error(f"Error getting document info: {e}")
            return {}