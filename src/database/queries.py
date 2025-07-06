"""
Database query functions for Business Document PDF Parser

Provides high-level query functions for searching and retrieving business documents.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, text, func
from datetime import datetime, date
from decimal import Decimal

from .models import (
    BusinessDocument, PurchaseOrder, Invoice, Receipt, 
    DocumentLineItem, Vendor, DocumentType
)
from .connection import get_session, DatabaseSession


def search_business_documents(
    query: str,
    db_path: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    document_type: Optional[DocumentType] = None,
    include_line_items: bool = False
) -> List[Dict[str, Any]]:
    """
    Search business documents by query string
    
    Args:
        query: Search query (document number, vendor name, etc.)
        db_path: Database path (optional)
        limit: Maximum results to return
        offset: Number of results to skip
        document_type: Filter by document type
        include_line_items: Whether to include line item details
    
    Returns:
        List of document dictionaries
    """
    with DatabaseSession(db_path) as session:
        # Build base query
        base_query = session.query(BusinessDocument)
        
        if include_line_items:
            base_query = base_query.options(joinedload(BusinessDocument.line_items))
        
        # Add search filters
        if query:
            search_filter = or_(
                BusinessDocument.document_number.ilike(f"%{query}%"),
                BusinessDocument.vendor.ilike(f"%{query}%"),
                BusinessDocument.pdf_filename.ilike(f"%{query}%")
            )
            base_query = base_query.filter(search_filter)
        
        # Add document type filter
        if document_type:
            base_query = base_query.filter(BusinessDocument.document_type == document_type)
        
        # Apply pagination and ordering
        documents = base_query.order_by(
            BusinessDocument.date.desc(),
            BusinessDocument.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        # Convert to dictionaries
        result = []
        for doc in documents:
            doc_dict = doc.to_dict()
            
            # Add line items if requested
            if include_line_items and doc.line_items:
                doc_dict['line_items'] = [item.to_dict() for item in doc.line_items]
            
            result.append(doc_dict)
        
        return result


def get_document_by_id(
    document_id: int,
    db_path: Optional[str] = None,
    include_line_items: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Get a specific document by ID
    
    Args:
        document_id: Document ID
        db_path: Database path (optional)
        include_line_items: Whether to include line item details
    
    Returns:
        Document dictionary or None if not found
    """
    with DatabaseSession(db_path) as session:
        query = session.query(BusinessDocument).filter(BusinessDocument.id == document_id)
        
        if include_line_items:
            query = query.options(joinedload(BusinessDocument.line_items))
        
        doc = query.first()
        
        if not doc:
            return None
        
        doc_dict = doc.to_dict()
        
        # Add line items if requested
        if include_line_items and doc.line_items:
            doc_dict['line_items'] = [item.to_dict() for item in doc.line_items]
        
        # Add document-specific details
        if doc.document_type == DocumentType.PURCHASE_ORDER:
            po = session.query(PurchaseOrder).filter(PurchaseOrder.document_id == document_id).first()
            if po:
                doc_dict['purchase_order'] = po.to_dict()
        
        elif doc.document_type == DocumentType.INVOICE:
            invoice = session.query(Invoice).filter(Invoice.document_id == document_id).first()
            if invoice:
                doc_dict['invoice'] = invoice.to_dict()
        
        elif doc.document_type == DocumentType.RECEIPT:
            receipt = session.query(Receipt).filter(Receipt.document_id == document_id).first()
            if receipt:
                doc_dict['receipt'] = receipt.to_dict()
        
        return doc_dict


def list_business_documents(
    db_path: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    vendor: Optional[str] = None,
    document_type: Optional[DocumentType] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> Dict[str, Any]:
    """
    List business documents with filters and pagination
    
    Args:
        db_path: Database path (optional)
        limit: Maximum results to return
        offset: Number of results to skip
        vendor: Filter by vendor name
        document_type: Filter by document type
        date_from: Filter by date range (start)
        date_to: Filter by date range (end)
    
    Returns:
        Dictionary with documents list and pagination info
    """
    with DatabaseSession(db_path) as session:
        # Build query
        query = session.query(BusinessDocument)
        
        # Add filters
        if vendor:
            query = query.filter(BusinessDocument.vendor.ilike(f"%{vendor}%"))
        
        if document_type:
            query = query.filter(BusinessDocument.document_type == document_type)
        
        if date_from:
            query = query.filter(BusinessDocument.date >= date_from)
        
        if date_to:
            query = query.filter(BusinessDocument.date <= date_to)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        documents = query.order_by(
            BusinessDocument.date.desc(),
            BusinessDocument.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        # Convert to dictionaries
        doc_list = [doc.to_dict() for doc in documents]
        
        return {
            "documents": doc_list,
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": (offset + limit) < total_count
        }


def get_database_summary(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get summary statistics for the database
    
    Args:
        db_path: Database path (optional)
    
    Returns:
        Dictionary with summary statistics
    """
    with DatabaseSession(db_path) as session:
        # Count documents by type
        doc_counts = session.query(
            BusinessDocument.document_type,
            func.count(BusinessDocument.id).label('count')
        ).group_by(BusinessDocument.document_type).all()
        
        # Total documents
        total_docs = session.query(BusinessDocument).count()
        
        # Calculate total amounts
        po_total = session.query(func.sum(PurchaseOrder.total_amount)).scalar() or 0
        invoice_total = session.query(func.sum(Invoice.total_amount)).scalar() or 0
        
        # Get date range
        date_range = session.query(
            func.min(BusinessDocument.date).label('earliest'),
            func.max(BusinessDocument.date).label('latest')
        ).first()
        
        # Top vendors
        top_vendors = session.query(
            Vendor.name,
            Vendor.total_documents,
            Vendor.total_amount
        ).order_by(Vendor.total_documents.desc()).limit(10).all()
        
        # Unique vendors count
        unique_vendors = session.query(Vendor).count()
        
        return {
            "total_documents": total_docs,
            "document_counts": {doc_type.value: count for doc_type, count in doc_counts},
            "total_value": float(po_total + invoice_total),
            "unique_vendors": unique_vendors,
            "date_range": {
                "earliest": date_range.earliest.isoformat() if date_range.earliest else None,
                "latest": date_range.latest.isoformat() if date_range.latest else None
            },
            "top_vendors": [
                {
                    "name": vendor.name,
                    "total_documents": vendor.total_documents,
                    "total_amount": float(vendor.total_amount)
                }
                for vendor in top_vendors
            ]
        }


def search_by_document_number(
    document_number: str,
    db_path: Optional[str] = None,
    exact_match: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Search for a document by document number
    
    Args:
        document_number: Document number to search for
        db_path: Database path (optional)
        exact_match: Whether to do exact match or partial match
    
    Returns:
        Document dictionary or None if not found
    """
    with DatabaseSession(db_path) as session:
        query = session.query(BusinessDocument).options(
            joinedload(BusinessDocument.line_items)
        )
        
        if exact_match:
            query = query.filter(BusinessDocument.document_number == document_number)
        else:
            query = query.filter(BusinessDocument.document_number.ilike(f"%{document_number}%"))
        
        doc = query.first()
        
        if not doc:
            return None
        
        return get_document_by_id(doc.id, db_path, include_line_items=True)


def search_by_vendor(
    vendor_name: str,
    db_path: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Search for documents by vendor name
    
    Args:
        vendor_name: Vendor name to search for
        db_path: Database path (optional)
        limit: Maximum results to return
    
    Returns:
        List of document dictionaries
    """
    return search_business_documents(
        query=vendor_name,
        db_path=db_path,
        limit=limit
    )


def get_purchase_orders(
    db_path: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get purchase orders with their details
    
    Args:
        db_path: Database path (optional)
        limit: Maximum results to return
        offset: Number of results to skip
    
    Returns:
        List of purchase order dictionaries
    """
    with DatabaseSession(db_path) as session:
        pos = session.query(BusinessDocument).join(PurchaseOrder).options(
            joinedload(BusinessDocument.line_items)
        ).filter(
            BusinessDocument.document_type == DocumentType.PURCHASE_ORDER
        ).order_by(
            BusinessDocument.date.desc()
        ).offset(offset).limit(limit).all()
        
        result = []
        for po_doc in pos:
            po_dict = po_doc.to_dict()
            
            # Get PO specific details
            po_details = session.query(PurchaseOrder).filter(
                PurchaseOrder.document_id == po_doc.id
            ).first()
            
            if po_details:
                po_dict['total_amount'] = float(po_details.total_amount) if po_details.total_amount else None
                po_dict['po_number'] = po_details.po_number
            
            # Add line items
            if po_doc.line_items:
                po_dict['line_items'] = [item.to_dict() for item in po_doc.line_items]
            
            result.append(po_dict)
        
        return result


def store_parsed_document(
    document_data,
    file_path: str,
    db_path: Optional[str] = None
) -> int:
    """
    Store parsed document data in the database
    
    Args:
        document_data: Parsed document data object
        file_path: Path to the original PDF file
        db_path: Database path (optional)
    
    Returns:
        Database ID of the stored document
    """
    from pathlib import Path
    
    with DatabaseSession(db_path) as session:
        # Get or create vendor
        vendor = get_or_create_vendor(session, document_data.vendor)
        
        # Determine the appropriate date for this document type
        document_date = document_data.date
        
        # For receipts, use date_received if date is None
        if (document_data.document_type.value == 'receipt' and 
            document_date is None and 
            hasattr(document_data, 'date_received') and 
            document_data.date_received is not None):
            document_date = document_data.date_received
        
        # Create main business document record
        business_doc = BusinessDocument(
            document_type=DocumentType(document_data.document_type.value),
            document_number=document_data.document_number,
            vendor=document_data.vendor,
            date=document_date,
            pdf_filename=Path(file_path).name,
            pdf_path=file_path,
            pdf_file_size=Path(file_path).stat().st_size,
            pdf_pages=1,  # TODO: Get actual page count
            parsing_confidence=Decimal(str(document_data.extraction_confidence)),
            extraction_method=document_data.extraction_method,
            raw_text=document_data.raw_text,
            extraction_metadata=document_data.metadata,
            status="extracted"
        )
        
        session.add(business_doc)
        session.flush()  # Get the ID without committing
        
        # Create document-specific records
        if document_data.document_type.value == 'purchase_order':
            po = PurchaseOrder(
                document_id=business_doc.id,
                po_number=document_data.po_number,
                total_amount=document_data.total_amount
            )
            session.add(po)
            
        elif document_data.document_type.value == 'invoice':
            invoice = Invoice(
                document_id=business_doc.id,
                invoice_number=document_data.invoice_number,
                reference_po=document_data.reference_po,
                total_amount=document_data.total_amount,
                item_description=document_data.item,
                quantity=document_data.quantity,
                unit_price=document_data.unit_price
            )
            session.add(invoice)
            
        elif document_data.document_type.value == 'receipt':
            receipt = Receipt(
                document_id=business_doc.id,
                receipt_id=document_data.receipt_id,
                reference_po=document_data.reference_po,
                date_received=document_data.date_received,
                item_description=document_data.item,
                quantity_received=document_data.quantity_received
            )
            session.add(receipt)
        
        # Store line items if present
        if document_data.line_items:
            for i, item_data in enumerate(document_data.line_items):
                line_item = DocumentLineItem(
                    document_id=business_doc.id,
                    item_description=item_data.get('item_description', ''),
                    quantity=item_data.get('quantity', 0),
                    unit_price=Decimal(str(item_data.get('unit_price', 0))),
                    line_total=Decimal(str(item_data.get('line_total', 0))),
                    line_number=i + 1,
                    extraction_confidence=Decimal(str(item_data.get('extraction_confidence', 0.0)))
                )
                session.add(line_item)
        
        # Update vendor statistics
        update_vendor_statistics(session, vendor, document_data)
        
        session.commit()
        return business_doc.id


def get_or_create_vendor(session: Session, vendor_name: str) -> Vendor:
    """Get or create vendor record"""
    from .models import normalize_vendor_name
    
    if not vendor_name:
        vendor_name = "Unknown Vendor"
    
    # Check if vendor exists
    vendor = session.query(Vendor).filter_by(name=vendor_name).first()
    
    if not vendor:
        # Create new vendor
        vendor = Vendor(
            name=vendor_name,
            normalized_name=normalize_vendor_name(vendor_name)
        )
        session.add(vendor)
        session.flush()
    
    return vendor


def update_vendor_statistics(session: Session, vendor: Vendor, document_data):
    """Update vendor statistics"""
    vendor.total_documents += 1
    
    if document_data.document_type.value == 'purchase_order':
        vendor.total_orders += 1
    elif document_data.document_type.value == 'invoice':
        vendor.total_invoices += 1
    elif document_data.document_type.value == 'receipt':
        vendor.total_receipts += 1
    
    # Update total amount if available
    if hasattr(document_data, 'total_amount') and document_data.total_amount:
        vendor.total_amount += document_data.total_amount


def initialize_database(db_path: Optional[str] = None) -> str:
    """Initialize database with all required tables"""
    from .setup import initialize_database as setup_init_db
    return setup_init_db(db_path)


def get_database_info(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Get database information"""
    from .setup import get_database_info as setup_get_db_info
    return setup_get_db_info(db_path) 