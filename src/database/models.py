"""
Database models for Business Document PDF Parser

Models designed to store structured data extracted from PDFs (Purchase Orders, Invoices, Receipts).
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
from enum import Enum

from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator
import json

Base = declarative_base()


class DocumentType(str, Enum):
    """Document types supported by the parser"""
    PURCHASE_ORDER = "purchase_order"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    UNKNOWN = "unknown"


class BusinessDocument(Base):
    """
    Base table for all business documents (POs, Invoices, Receipts)
    """
    __tablename__ = "business_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Document identification
    document_type = Column(SQLEnum(DocumentType), nullable=False, index=True)
    document_number = Column(String(50), nullable=False, index=True)  # PO number, Invoice number, Receipt ID
    
    # Common fields across all document types
    vendor = Column(String(255), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # PDF source information
    pdf_filename = Column(String(255), nullable=False)
    pdf_path = Column(String(500), nullable=False)
    pdf_file_size = Column(Integer, nullable=True)
    pdf_pages = Column(Integer, nullable=True)
    
    # Parsing metadata
    extracted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    parsing_confidence = Column(Numeric(precision=3, scale=2), nullable=True)  # 0.0 to 1.0
    extraction_method = Column(String(50), nullable=True)  # e.g., "pypdf", "ocr", "template"
    
    # Raw extracted data for debugging
    raw_text = Column(Text, nullable=True)
    extraction_metadata = Column(JSON, nullable=True)
    
    # Status tracking
    status = Column(String(20), default="extracted", nullable=False)  # extracted, validated, error
    validation_errors = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    line_items = relationship("DocumentLineItem", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BusinessDocument(type='{self.document_type}', number='{self.document_number}', vendor='{self.vendor}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for API responses"""
        return {
            "id": self.id,
            "document_type": self.document_type.value if self.document_type else None,
            "document_number": self.document_number,
            "vendor": self.vendor,
            "date": self.date.isoformat() if self.date else None,
            "pdf_filename": self.pdf_filename,
            "pdf_path": self.pdf_path,
            "pdf_file_size": self.pdf_file_size,
            "pdf_pages": self.pdf_pages,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
            "parsing_confidence": float(self.parsing_confidence) if self.parsing_confidence else None,
            "extraction_method": self.extraction_method,
            "status": self.status,
            "line_items_count": len(self.line_items) if self.line_items else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PurchaseOrder(Base):
    """
    Purchase Order specific data
    """
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("business_documents.id"), nullable=False, unique=True, index=True)
    
    # PO specific fields
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    total_amount = Column(Numeric(precision=12, scale=2), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("BusinessDocument", backref="purchase_order")
    
    def __repr__(self):
        return f"<PurchaseOrder(po_number='{self.po_number}', total=${self.total_amount})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PO to dictionary"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "po_number": self.po_number,
            "total_amount": float(self.total_amount) if self.total_amount else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Invoice(Base):
    """
    Invoice specific data
    """
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("business_documents.id"), nullable=False, unique=True, index=True)
    
    # Invoice specific fields
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    reference_po = Column(String(50), nullable=True, index=True)
    total_amount = Column(Numeric(precision=12, scale=2), nullable=True)
    
    # Single line item fields (based on sample data structure)
    item_description = Column(String(500), nullable=True)
    quantity = Column(Integer, nullable=True)
    unit_price = Column(Numeric(precision=10, scale=2), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("BusinessDocument", backref="invoice")
    
    def __repr__(self):
        return f"<Invoice(invoice_number='{self.invoice_number}', reference_po='{self.reference_po}', total=${self.total_amount})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Invoice to dictionary"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "invoice_number": self.invoice_number,
            "reference_po": self.reference_po,
            "total_amount": float(self.total_amount) if self.total_amount else None,
            "item_description": self.item_description,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Receipt(Base):
    """
    Receipt specific data
    """
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("business_documents.id"), nullable=False, unique=True, index=True)
    
    # Receipt specific fields
    receipt_id = Column(String(50), unique=True, nullable=False, index=True)
    reference_po = Column(String(50), nullable=True, index=True)
    date_received = Column(DateTime, nullable=True, index=True)
    
    # Single line item fields (based on sample data structure)
    item_description = Column(String(500), nullable=True)
    quantity_received = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("BusinessDocument", backref="receipt")
    
    def __repr__(self):
        return f"<Receipt(receipt_id='{self.receipt_id}', reference_po='{self.reference_po}', qty_received={self.quantity_received})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Receipt to dictionary"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "receipt_id": self.receipt_id,
            "reference_po": self.reference_po,
            "date_received": self.date_received.isoformat() if self.date_received else None,
            "item_description": self.item_description,
            "quantity_received": self.quantity_received,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class DocumentLineItem(Base):
    """
    Line items for documents that have multiple items
    """
    __tablename__ = "document_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("business_documents.id"), nullable=False, index=True)
    
    # Line item details
    item_description = Column(String(500), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(precision=10, scale=2), nullable=False)
    line_total = Column(Numeric(precision=10, scale=2), nullable=False)
    
    # Additional item information
    item_code = Column(String(100), nullable=True)
    unit_of_measure = Column(String(20), nullable=True)  # e.g., "EA", "LB", "FT"
    
    # Extracted metadata
    line_number = Column(Integer, nullable=True)  # Original line number in PDF
    extraction_confidence = Column(Numeric(precision=3, scale=2), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("BusinessDocument", back_populates="line_items")
    
    def __repr__(self):
        return f"<DocumentLineItem(item='{self.item_description}', qty={self.quantity}, price=${self.unit_price})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert line item to dictionary"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "item_description": self.item_description,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price else None,
            "line_total": float(self.line_total) if self.line_total else None,
            "item_code": self.item_code,
            "unit_of_measure": self.unit_of_measure,
            "line_number": self.line_number,
            "extraction_confidence": float(self.extraction_confidence) if self.extraction_confidence else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Vendor(Base):
    """
    Vendor lookup table for normalization
    """
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)  # Cleaned/standardized name
    
    # Vendor details
    address = Column(Text, nullable=True)
    contact_info = Column(JSON, nullable=True)
    
    # Statistics
    total_documents = Column(Integer, default=0, nullable=False)
    total_orders = Column(Integer, default=0, nullable=False)
    total_invoices = Column(Integer, default=0, nullable=False)
    total_receipts = Column(Integer, default=0, nullable=False)
    total_amount = Column(Numeric(precision=12, scale=2), default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Vendor(name='{self.name}', documents={self.total_documents})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert vendor to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "normalized_name": self.normalized_name,
            "address": self.address,
            "contact_info": self.contact_info,
            "total_documents": self.total_documents,
            "total_orders": self.total_orders,
            "total_invoices": self.total_invoices,
            "total_receipts": self.total_receipts,
            "total_amount": float(self.total_amount) if self.total_amount else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ExtractionTemplate(Base):
    """
    Templates for PDF extraction patterns
    """
    __tablename__ = "extraction_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    document_type = Column(SQLEnum(DocumentType), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Template patterns
    document_number_pattern = Column(Text, nullable=True)
    vendor_pattern = Column(Text, nullable=True)
    date_pattern = Column(Text, nullable=True)
    total_pattern = Column(Text, nullable=True)
    item_pattern = Column(Text, nullable=True)
    
    # Template metadata
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # Higher priority templates tried first
    success_rate = Column(Numeric(precision=3, scale=2), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ExtractionTemplate(name='{self.name}', type='{self.document_type}', active={self.is_active})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "document_type": self.document_type.value if self.document_type else None,
            "description": self.description,
            "document_number_pattern": self.document_number_pattern,
            "vendor_pattern": self.vendor_pattern,
            "date_pattern": self.date_pattern,
            "total_pattern": self.total_pattern,
            "item_pattern": self.item_pattern,
            "is_active": self.is_active,
            "priority": self.priority,
            "success_rate": float(self.success_rate) if self.success_rate else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Pydantic models for API validation
class BusinessDocumentCreate(BaseModel):
    """Pydantic model for creating business documents"""
    document_type: DocumentType
    document_number: str = Field(..., max_length=50)
    vendor: str = Field(..., max_length=255)
    date: datetime
    pdf_filename: str = Field(..., max_length=255)
    pdf_path: str = Field(..., max_length=500)
    pdf_file_size: Optional[int] = None
    pdf_pages: Optional[int] = None
    parsing_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    extraction_method: Optional[str] = Field(None, max_length=50)
    raw_text: Optional[str] = None
    extraction_metadata: Optional[Dict[str, Any]] = None


class PurchaseOrderCreate(BaseModel):
    """Pydantic model for creating purchase orders"""
    po_number: str = Field(..., max_length=50)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    
    @validator('total_amount')
    def validate_total_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Total amount must be positive')
        return v


class InvoiceCreate(BaseModel):
    """Pydantic model for creating invoices"""
    invoice_number: str = Field(..., max_length=50)
    reference_po: Optional[str] = Field(None, max_length=50)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    item_description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)


class ReceiptCreate(BaseModel):
    """Pydantic model for creating receipts"""
    receipt_id: str = Field(..., max_length=50)
    reference_po: Optional[str] = Field(None, max_length=50)
    date_received: Optional[datetime] = None
    item_description: Optional[str] = Field(None, max_length=500)
    quantity_received: Optional[int] = Field(None, gt=0)


class DocumentLineItemCreate(BaseModel):
    """Pydantic model for creating line items"""
    item_description: str = Field(..., max_length=500)
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)
    item_code: Optional[str] = Field(None, max_length=100)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    line_number: Optional[int] = None
    extraction_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    
    @validator('line_total')
    def validate_line_total(cls, v, values):
        if 'quantity' in values and 'unit_price' in values:
            expected_total = values['quantity'] * values['unit_price']
            if abs(v - expected_total) > Decimal('0.01'):  # Allow for small rounding differences
                raise ValueError('Line total does not match quantity × unit price')
        return v


class BusinessDocumentResponse(BaseModel):
    """Pydantic model for API responses"""
    id: int
    document_type: DocumentType
    document_number: str
    vendor: str
    date: datetime
    pdf_filename: str
    parsing_confidence: Optional[Decimal] = None
    extraction_method: Optional[str] = None
    status: str
    line_items_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentLineItemResponse(BaseModel):
    """Pydantic model for line item responses"""
    id: int
    document_id: int
    item_description: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    item_code: Optional[str] = None
    unit_of_measure: Optional[str] = None
    line_number: Optional[int] = None
    extraction_confidence: Optional[Decimal] = None
    
    class Config:
        from_attributes = True


# Utility functions for data processing
def normalize_vendor_name(vendor_name: str) -> str:
    """Normalize vendor name for consistent matching"""
    if not vendor_name:
        return ""
    
    # Remove extra whitespace
    normalized = ' '.join(vendor_name.split())
    
    # Remove common suffixes (Inc., LLC, Corp., etc.)
    suffixes = ['Inc.', 'LLC', 'Corp.', 'Corporation', 'Ltd.', 'Limited', 'Co.', 'Company']
    for suffix in suffixes:
        if normalized.endswith(f' {suffix}'):
            normalized = normalized[:-len(suffix)-1]
    
    # Convert to title case
    normalized = normalized.title()
    
    return normalized.strip()


def extract_document_number(text: str, document_type: DocumentType) -> Optional[str]:
    """Extract document number from text based on document type"""
    import re
    
    patterns = {
        DocumentType.PURCHASE_ORDER: [
            r'PO[-\s]?Number:?\s*([A-Z0-9-]+)',
            r'Purchase\s+Order:?\s*([A-Z0-9-]+)',
            r'P\.O\.?\s*:?\s*([A-Z0-9-]+)',
            r'Order\s+Number:?\s*([A-Z0-9-]+)',
            r'(PO[-]?\d{3,6})'
        ],
        DocumentType.INVOICE: [
            r'Invoice[-\s]?Number:?\s*([A-Z0-9-]+)',
            r'Invoice:?\s*([A-Z0-9-]+)',
            r'INV[-\s]?Number:?\s*([A-Z0-9-]+)',
            r'(INV[-]?\d{3,6})'
        ],
        DocumentType.RECEIPT: [
            r'Receipt[-\s]?ID:?\s*([A-Z0-9-]+)',
            r'Receipt:?\s*([A-Z0-9-]+)',
            r'RCPT[-\s]?ID:?\s*([A-Z0-9-]+)',
            r'(RCPT[-]?\d{3,6})'
        ]
    }
    
    for pattern in patterns.get(document_type, []):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def parse_currency(amount_str: str) -> Optional[Decimal]:
    """Parse currency string to Decimal"""
    if not amount_str:
        return None
    
    import re
    # Remove currency symbols and thousands separators
    clean_str = re.sub(r'[$,]', '', amount_str.strip())
    
    try:
        return Decimal(clean_str)
    except:
        return None


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime"""
    if not date_str:
        return None
    
    import re
    
    # Simple date parsing patterns
    date_patterns = [
        r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
        r'(\d{1,2})-(\d{1,2})-(\d{4})'  # MM-DD-YYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                if len(match.group(1)) == 4:  # YYYY-MM-DD
                    year, month, day = match.groups()
                else:  # MM/DD/YYYY or MM-DD-YYYY
                    month, day, year = match.groups()
                
                return datetime(int(year), int(month), int(day))
            except ValueError:
                continue
    
    return None 