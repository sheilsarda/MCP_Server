"""
PDF Parser for Purchase Order Documents

Extracts structured purchase order data from PDF documents using multiple parsing strategies.
"""

import re
import PyPDF2
from pathlib import Path
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass

# TODO: Import PDF parsing libraries (uncomment when packages are installed)
# import fitz  # PyMuPDF
# import pdfplumber
# from dateutil.parser import parse as parse_date

@dataclass
class PurchaseOrderData:
    """Structured purchase order data extracted from PDF"""
    po_number: Optional[str] = None
    vendor: Optional[str] = None
    date: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    line_items: Optional[List[Dict[str, Any]]] = None
    extraction_confidence: float = 0.0
    extraction_method: str = "unknown"
    raw_text: str = ""
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.line_items is None:
            self.line_items = []
        if self.metadata is None:
            self.metadata = {}


class PurchaseOrderPDFParser:
    """
    PDF parser optimized for purchase order documents
    """
    
    def __init__(self):
        self.supported_extensions = ['.pdf']
        
        # Regex patterns for extracting PO data
        self.po_patterns = {
            'po_number': [
                r'PO[-\s]?Number:?\s*([A-Z0-9-]+)',
                r'Purchase\s+Order:?\s*([A-Z0-9-]+)',
                r'P\.O\.?\s*:?\s*([A-Z0-9-]+)',
                r'Order\s+Number:?\s*([A-Z0-9-]+)',
                r'([A-Z]{2,4}[-]?\d{3,6})'  # Generic pattern
            ],
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
                r'(\d{4}-\d{2}-\d{2})'  # Generic ISO date
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
            'unit_price': [
                r'Unit\s+Price:?\s*\$?([0-9,]+\.?\d{0,2})',
                r'Price:?\s*\$?([0-9,]+\.?\d{0,2})',
                r'Rate:?\s*\$?([0-9,]+\.?\d{0,2})'
            ]
        }
    
    async def parse_pdf(self, file_path: str) -> PurchaseOrderData:
        """
        Parse a PDF file and extract purchase order data
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            PurchaseOrderData object with extracted information
        """
        try:
            print(f"INFO: Parsing PDF: {file_path}")
            
            # Validate file
            if not self._validate_pdf(file_path):
                raise ValueError(f"Invalid PDF file: {file_path}")
            
            # Try multiple extraction methods
            extraction_results = []
            
            # Method 1: PyPDF2 (basic text extraction)
            try:
                result = await self._extract_with_pypdf2(file_path)
                extraction_results.append(result)
            except Exception as e:
                print(f"WARNING: PyPDF2 extraction failed: {e}")
            
            # Method 2: PDFPlumber (advanced text extraction)
            try:
                result = await self._extract_with_pdfplumber(file_path)
                extraction_results.append(result)
            except Exception as e:
                print(f"WARNING: PDFPlumber extraction failed: {e}")
            
            # Method 3: PyMuPDF (fallback)
            try:
                result = await self._extract_with_pymupdf(file_path)
                extraction_results.append(result)
            except Exception as e:
                print(f"WARNING: PyMuPDF extraction failed: {e}")
            
            # Select best result
            if not extraction_results:
                raise ValueError("All extraction methods failed")
            
            best_result = max(extraction_results, key=lambda x: x.extraction_confidence)
            
            # Post-process and validate
            validated_result = self._validate_and_clean_data(best_result)
            
            print(f"INFO: PDF parsing completed. Confidence: {validated_result.extraction_confidence:.2f}")
            return validated_result
            
        except Exception as e:
            print(f"ERROR: Error parsing PDF {file_path}: {e}")
            raise
    
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
            print(f"ERROR: PDF validation failed: {e}")
            return False
    
    async def _extract_with_pypdf2(self, file_path: str) -> PurchaseOrderData:
        """Extract data using PyPDF2"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                po_data = self._extract_structured_data(text)
                po_data.extraction_method = "pypdf2"
                po_data.raw_text = text
                return po_data
        except Exception as e:
            print(f"ERROR: PyPDF2 extraction failed: {e}")
            raise
        
        # Placeholder implementation
        # po_data = PurchaseOrderData()
        # po_data.extraction_method = "pypdf2_placeholder"
        # po_data.extraction_confidence = 0.3
        # po_data.raw_text = "TODO: Implement PyPDF2 extraction"
        # return po_data
    
    async def _extract_with_pdfplumber(self, file_path: str) -> PurchaseOrderData:
        """Extract data using pdfplumber"""
        # TODO: Implement pdfplumber extraction
        # try:
        #     with pdfplumber.open(file_path) as pdf:
        #         text = ""
        #         for page in pdf.pages:
        #             text += page.extract_text() or ""
        #         
        #         po_data = self._extract_structured_data(text)
        #         po_data.extraction_method = "pdfplumber"
        #         po_data.raw_text = text
        #         return po_data
        # except Exception as e:
        #     print(f"ERROR: pdfplumber extraction failed: {e}")
        #     raise
        
        # Placeholder implementation
        po_data = PurchaseOrderData()
        po_data.extraction_method = "pdfplumber_placeholder"
        po_data.extraction_confidence = 0.5
        po_data.raw_text = "TODO: Implement pdfplumber extraction"
        return po_data
    
    async def _extract_with_pymupdf(self, file_path: str) -> PurchaseOrderData:
        """Extract data using PyMuPDF"""
        # TODO: Implement PyMuPDF extraction
        # try:
        #     doc = fitz.open(file_path)
        #     text = ""
        #     for page in doc:
        #         text += page.get_text()
        #     doc.close()
        #     
        #     po_data = self._extract_structured_data(text)
        #     po_data.extraction_method = "pymupdf"
        #     po_data.raw_text = text
        #     return po_data
        # except Exception as e:
        #     print(f"ERROR: PyMuPDF extraction failed: {e}")
        #     raise
        
        # Placeholder implementation
        po_data = PurchaseOrderData()
        po_data.extraction_method = "pymupdf_placeholder"
        po_data.extraction_confidence = 0.4
        po_data.raw_text = "TODO: Implement PyMuPDF extraction"
        return po_data
    
    def _extract_structured_data(self, text: str) -> PurchaseOrderData:
        """Extract structured data from raw text using regex patterns"""
        try:
            po_data = PurchaseOrderData()
            po_data.raw_text = text
            
            # Extract PO number
            po_data.po_number = self._extract_field(text, 'po_number')
            
            # Extract vendor
            po_data.vendor = self._extract_field(text, 'vendor')
            
            # Extract date
            date_str = self._extract_field(text, 'date')
            if date_str:
                po_data.date = self._parse_date(date_str)
            
            # Extract total amount
            total_str = self._extract_field(text, 'total')
            if total_str:
                po_data.total_amount = self._parse_currency(total_str)
            
            # Extract line items
            po_data.line_items = self._extract_line_items(text)
            
            # Calculate confidence score
            po_data.extraction_confidence = self._calculate_confidence(po_data)
            
            return po_data
            
        except Exception as e:
            print(f"ERROR: Error extracting structured data: {e}")
            raise
    
    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """Extract a specific field using regex patterns"""
        patterns = self.po_patterns.get(field_name, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                result = match.group(1).strip()
                print(f"DEBUG: Extracted {field_name}: {result}")
                return result
        
        print(f"DEBUG: Could not extract {field_name}")
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
            print(f"ERROR: Error parsing currency '{amount_str}': {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        try:
            # TODO: Use dateutil.parser when available
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
            print(f"ERROR: Error parsing date '{date_str}': {e}")
            return None
    
    def _calculate_confidence(self, po_data: PurchaseOrderData) -> float:
        """Calculate extraction confidence score"""
        confidence_factors = []
        
        # Required fields
        if po_data.po_number:
            confidence_factors.append(0.3)
        if po_data.vendor:
            confidence_factors.append(0.2)
        if po_data.date:
            confidence_factors.append(0.1)
        if po_data.total_amount:
            confidence_factors.append(0.2)
        
        # Line items
        if po_data.line_items:
            confidence_factors.append(0.2)
        
        # Calculate total confidence
        total_confidence = sum(confidence_factors)
        
        # Bonus for complete data
        if len(confidence_factors) == 5:
            total_confidence += 0.1
        
        return min(total_confidence, 1.0)
    
    def _validate_and_clean_data(self, po_data: PurchaseOrderData) -> PurchaseOrderData:
        """Validate and clean extracted data"""
        try:
            # Clean vendor name
            if po_data.vendor:
                po_data.vendor = self._clean_vendor_name(po_data.vendor)
            
            # Validate PO number format
            if po_data.po_number:
                po_data.po_number = self._clean_po_number(po_data.po_number)
            
            # Validate date range
            if po_data.date:
                if po_data.date.year < 2000 or po_data.date.year > 2030:
                    print(f"WARNING: Date seems invalid: {po_data.date}")
                    po_data.date = None
            
            # Validate amounts
            if po_data.total_amount and po_data.total_amount <= 0:
                print(f"WARNING: Total amount seems invalid: {po_data.total_amount}")
                po_data.total_amount = None
            
            # Validate line items
            if po_data.line_items:
                for item in po_data.line_items:
                    if item.get('quantity', 0) <= 0:
                        print(f"WARNING: Invalid quantity in line item: {item}")
                    if item.get('unit_price', 0) <= 0:
                        print(f"WARNING: Invalid unit price in line item: {item}")
            
            return po_data
            
        except Exception as e:
            print(f"ERROR: Error validating data: {e}")
            return po_data
    
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
    
    def _clean_po_number(self, po_number: str) -> str:
        """Clean and normalize PO number"""
        # Remove extra whitespace
        po_number = po_number.strip()
        
        # Ensure consistent format
        po_number = po_number.upper()
        
        # TODO: Add more PO number cleaning
        # - Standardize PO number format
        # - Add check digits validation
        
        return po_number
    
    def is_supported(self, file_path: str) -> bool:
        """Check if file type is supported"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    async def get_pdf_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic PDF information"""
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
                "parser_version": "1.0.0"
            }
            
        except Exception as e:
            print(f"ERROR: Error getting PDF info: {e}")
            return {}


# Utility functions for testing with sample data
def create_sample_po_data() -> PurchaseOrderData:
    """Create sample PO data for testing"""
    return PurchaseOrderData(
        po_number="PO-1003",
        vendor="Nova Plastics",
        date=datetime(2024, 10, 8),
        total_amount=Decimal("77890.00"),
        line_items=[
            {
                "item_description": "Polycarbonate Sheet",
                "quantity": 200,
                "unit_price": Decimal("389.45"),
                "line_total": Decimal("77890.00"),
                "extraction_confidence": 1.0
            }
        ],
        extraction_confidence=1.0,
        extraction_method="sample_data",
        raw_text="Sample PO data for testing"
    )


def validate_sample_data_format(text: str) -> bool:
    """Validate if text matches the sample PO format"""
    required_fields = ["PO Number:", "Vendor:", "Item:", "Quantity:", "Unit Price:", "Total:", "Date:"]
    
    for field in required_fields:
        if field not in text:
            return False
    
    return True 