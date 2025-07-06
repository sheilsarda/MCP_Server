"""
Database models for Purchase Order PDF Parser

Models designed to store structured purchase order data extracted from PDFs.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator
import json

Base = declarative_base()


class PurchaseOrder(Base):
    """
    Main purchase order table storing PO header information
    """
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core PO fields based on sample data
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    vendor = Column(String(255), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # Financial totals
    total_amount = Column(Numeric(precision=10, scale=2), nullable=False)
    
    # PDF source information
    pdf_filename = Column(String(255), nullable=False)
    pdf_path = Column(String(500), nullable=False)
    pdf_file_size = Column(Integer, nullable=True)
    pdf_pages = Column(Integer, nullable=True)
    
    # Parsing metadata
    extracted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    parsing_confidence = Column(Numeric(precision=3, scale=2), nullable=True)  # 0.0 to 1.0
    extraction_method = Column(String(50), nullable=True)  # e.g., "regex", "ocr", "template"
    
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
    line_items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PurchaseOrder(po_number='{self.po_number}', vendor='{self.vendor}', total=${self.total_amount})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PO to dictionary for API responses"""
        return {
            "id": self.id,
            "po_number": self.po_number,
            "vendor": self.vendor,
            "date": self.date.isoformat() if self.date else None,
            "total_amount": float(self.total_amount) if self.total_amount else None,
            "pdf_filename": self.pdf_filename,
            "pdf_path": self.pdf_path,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
            "parsing_confidence": float(self.parsing_confidence) if self.parsing_confidence else None,
            "status": self.status,
            "line_items_count": len(self.line_items) if self.line_items else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PurchaseOrderItem(Base):
    """
    Purchase order line items table
    """
    __tablename__ = "purchase_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False, index=True)
    
    # Line item details based on sample data
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
    purchase_order = relationship("PurchaseOrder", back_populates="line_items")
    
    def __repr__(self):
        return f"<PurchaseOrderItem(item='{self.item_description}', qty={self.quantity}, price=${self.unit_price})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert line item to dictionary"""
        return {
            "id": self.id,
            "purchase_order_id": self.purchase_order_id,
            "item_description": self.item_description,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price else None,
            "line_total": float(self.line_total) if self.line_total else None,
            "item_code": self.item_code,
            "unit_of_measure": self.unit_of_measure,
            "line_number": self.line_number,
            "extraction_confidence": float(self.extraction_confidence) if self.extraction_confidence else None
        }


class Vendor(Base):
    """
    Vendor lookup table for normalization
    """
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)  # Cleaned/standardized name
    
    # Vendor details - TODO: Expand as needed
    address = Column(Text, nullable=True)
    contact_info = Column(JSON, nullable=True)
    
    # Statistics
    total_orders = Column(Integer, default=0, nullable=False)
    total_amount = Column(Numeric(precision=12, scale=2), default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Vendor(name='{self.name}', orders={self.total_orders})>"


class ExtractionTemplate(Base):
    """
    Templates for PDF extraction patterns
    """
    __tablename__ = "extraction_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Template patterns
    po_number_pattern = Column(Text, nullable=True)
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
        return f"<ExtractionTemplate(name='{self.name}', active={self.is_active})>"


# Pydantic models for API validation
class PurchaseOrderCreate(BaseModel):
    """Pydantic model for creating purchase orders"""
    po_number: str = Field(..., max_length=50)
    vendor: str = Field(..., max_length=255)
    date: datetime
    total_amount: Decimal = Field(..., ge=0)
    pdf_filename: str = Field(..., max_length=255)
    pdf_path: str = Field(..., max_length=500)
    pdf_file_size: Optional[int] = None
    pdf_pages: Optional[int] = None
    parsing_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    extraction_method: Optional[str] = Field(None, max_length=50)
    raw_text: Optional[str] = None
    extraction_metadata: Optional[Dict[str, Any]] = None
    
    @validator('total_amount')
    def validate_total_amount(cls, v):
        if v <= 0:
            raise ValueError('Total amount must be positive')
        return v


class PurchaseOrderItemCreate(BaseModel):
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


class PurchaseOrderResponse(BaseModel):
    """Pydantic model for API responses"""
    id: int
    po_number: str
    vendor: str
    date: datetime
    total_amount: Decimal
    pdf_filename: str
    extraction_confidence: Optional[Decimal] = None
    status: str
    line_items_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PurchaseOrderItemResponse(BaseModel):
    """Pydantic model for line item responses"""
    id: int
    purchase_order_id: int
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
    # TODO: Implement vendor name normalization
    # - Remove common suffixes (Inc., LLC, Corp., etc.)
    # - Handle common abbreviations
    # - Standardize punctuation and spacing
    # - Convert to title case
    
    return vendor_name.strip().title()


def extract_po_number(text: str) -> Optional[str]:
    """Extract PO number from text using regex patterns"""
    # TODO: Implement PO number extraction
    # - Try multiple regex patterns
    # - Handle different PO number formats
    # - Validate extracted PO numbers
    
    import re
    patterns = [
        r'PO[-\s]?Number:?\s*([A-Z0-9-]+)',
        r'Purchase\s+Order:?\s*([A-Z0-9-]+)',
        r'P\.O\.?\s*:?\s*([A-Z0-9-]+)',
        r'Order\s+Number:?\s*([A-Z0-9-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def parse_currency(amount_str: str) -> Optional[Decimal]:
    """Parse currency string to Decimal"""
    # TODO: Implement robust currency parsing
    # - Handle different currency symbols
    # - Remove thousands separators
    # - Handle negative amounts
    # - Validate decimal places
    
    import re
    # Remove currency symbols and thousands separators
    clean_str = re.sub(r'[$,]', '', amount_str.strip())
    
    try:
        return Decimal(clean_str)
    except:
        return None


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime"""
    # TODO: Implement robust date parsing
    # - Handle multiple date formats
    # - Handle relative dates
    # - Validate date ranges
    
    from dateutil.parser import parse
    try:
        return parse(date_str)
    except:
        return None 