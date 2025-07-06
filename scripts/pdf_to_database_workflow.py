#!/usr/bin/env python3
"""
PDF to Database Workflow Script

Complete workflow for processing PDF documents and storing extracted data in SQLite database.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pdf_parser.parser import BusinessDocumentPDFParser, PurchaseOrderData, InvoiceData, ReceiptData
from database.setup import initialize_database, get_database_info
from database.connection import DatabaseSession, get_session
from database.models import (
    BusinessDocument, PurchaseOrder, Invoice, Receipt, 
    DocumentLineItem, Vendor, normalize_vendor_name, DocumentType
)


class PDFProcessingWorkflow:
    """Main workflow class for processing PDFs and storing data"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.getcwd(), 'business_documents.db')
        self.parser = BusinessDocumentPDFParser()
        self.processed_documents = []
        self.errors = []
    
    def convert_document_type(self, parser_doc_type):
        """Convert parser DocumentType to database DocumentType"""
        # Import parser DocumentType locally to avoid conflicts
        from pdf_parser.parser import DocumentType as ParserDocumentType
        
        type_mapping = {
            ParserDocumentType.PURCHASE_ORDER: DocumentType.PURCHASE_ORDER,
            ParserDocumentType.INVOICE: DocumentType.INVOICE,
            ParserDocumentType.RECEIPT: DocumentType.RECEIPT,
            ParserDocumentType.UNKNOWN: DocumentType.UNKNOWN
        }
        
        return type_mapping.get(parser_doc_type, DocumentType.UNKNOWN)
    
    async def initialize_database(self):
        """Initialize the database with tables only (no sample data)"""
        print("🔧 Initializing database...")
        
        # Initialize database tables
        initialize_database(self.db_path)
        
        # Show database info
        info = get_database_info(self.db_path)
        print(f"📊 Database initialized: {info}")
        
    async def process_pdf_files(self, pdf_directory: str = "sample_data") -> List[Dict[str, Any]]:
        """Process all PDF files in the specified directory"""
        print(f"📄 Processing PDF files from: {pdf_directory}")
        
        pdf_dir = Path(pdf_directory)
        
        if not pdf_dir.exists():
            print(f"❌ Directory {pdf_directory} does not exist")
            return []
        
        # Find all PDF files
        for file_path in pdf_dir.glob("*.pdf"):
            try:
                print(f"\n🔍 Processing: {file_path.name}")
                
                # Parse the PDF
                document_data = await self.parser.parse_document(str(file_path))
                
                # Store in database
                stored_document = await self.store_document_data(document_data, str(file_path))
                
                if stored_document:
                    self.processed_documents.append({
                        "file_path": str(file_path),
                        "document_type": document_data.document_type.value,
                        "document_number": document_data.document_number,
                        "vendor": document_data.vendor,
                        "confidence": document_data.extraction_confidence,
                        "database_id": stored_document['id']
                    })
                    print(f"✅ Successfully processed and stored: {file_path.name}")
                else:
                    print(f"❌ Failed to store: {file_path.name}")
                    
            except Exception as e:
                error_msg = f"Error processing {file_path.name}: {str(e)}"
                print(f"❌ {error_msg}")
                self.errors.append(error_msg)
        
        return self.processed_documents
    
    async def store_document_data(self, document_data, file_path: str) -> Dict[str, Any]:
        """Store parsed document data in the database and return document info"""
        try:
            with DatabaseSession(self.db_path) as session:
                # Get or create vendor
                vendor = self.get_or_create_vendor(session, document_data.vendor)
                
                # Determine the appropriate date for this document type
                document_date = document_data.date
                
                # For receipts, use date_received if date is None
                from pdf_parser.parser import DocumentType as ParserDocumentType
                if (document_data.document_type == ParserDocumentType.RECEIPT and 
                    document_date is None and 
                    hasattr(document_data, 'date_received') and 
                    document_data.date_received is not None):
                    document_date = document_data.date_received
                
                # Create main business document record
                business_doc = BusinessDocument(
                    document_type=self.convert_document_type(document_data.document_type),
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
                from pdf_parser.parser import DocumentType as ParserDocumentType
                if document_data.document_type == ParserDocumentType.PURCHASE_ORDER:
                    await self.store_purchase_order(session, document_data, business_doc.id)
                elif document_data.document_type == ParserDocumentType.INVOICE:
                    await self.store_invoice(session, document_data, business_doc.id)
                elif document_data.document_type == ParserDocumentType.RECEIPT:
                    await self.store_receipt(session, document_data, business_doc.id)
                
                # Store line items if present
                if document_data.line_items:
                    await self.store_line_items(session, document_data.line_items, business_doc.id)
                
                # Update vendor statistics
                self.update_vendor_statistics(session, vendor, document_data)
                
                session.commit()
                
                # Access ID before session closes to avoid detachment issues
                document_id = business_doc.id
                
                # Create a simple dict with the data we need instead of returning the SQLAlchemy object
                return {
                    'id': document_id,
                    'document_type': business_doc.document_type,
                    'document_number': business_doc.document_number
                }
                
        except Exception as e:
            print(f"❌ Error storing document data: {e}")
            raise
    
    def get_or_create_vendor(self, session, vendor_name: str) -> Vendor:
        """Get or create vendor record"""
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
    
    async def store_purchase_order(self, session, po_data: PurchaseOrderData, document_id: int):
        """Store purchase order specific data"""
        po = PurchaseOrder(
            document_id=document_id,
            po_number=po_data.po_number,
            total_amount=po_data.total_amount
        )
        session.add(po)
    
    async def store_invoice(self, session, invoice_data: InvoiceData, document_id: int):
        """Store invoice specific data"""
        invoice = Invoice(
            document_id=document_id,
            invoice_number=invoice_data.invoice_number,
            reference_po=invoice_data.reference_po,
            total_amount=invoice_data.total_amount,
            item_description=invoice_data.item,
            quantity=invoice_data.quantity,
            unit_price=invoice_data.unit_price
        )
        session.add(invoice)
    
    async def store_receipt(self, session, receipt_data: ReceiptData, document_id: int):
        """Store receipt specific data"""
        receipt = Receipt(
            document_id=document_id,
            receipt_id=receipt_data.receipt_id,
            reference_po=receipt_data.reference_po,
            date_received=receipt_data.date_received,
            item_description=receipt_data.item,
            quantity_received=receipt_data.quantity_received
        )
        session.add(receipt)
    
    async def store_line_items(self, session, line_items: List[Dict[str, Any]], document_id: int):
        """Store line items for a document"""
        for i, item_data in enumerate(line_items):
            line_item = DocumentLineItem(
                document_id=document_id,
                item_description=item_data.get('item_description', ''),
                quantity=item_data.get('quantity', 0),
                unit_price=Decimal(str(item_data.get('unit_price', 0))),
                line_total=Decimal(str(item_data.get('line_total', 0))),
                line_number=i + 1,
                extraction_confidence=Decimal(str(item_data.get('extraction_confidence', 0.0)))
            )
            session.add(line_item)
    
    def update_vendor_statistics(self, session, vendor: Vendor, document_data):
        """Update vendor statistics"""
        from pdf_parser.parser import DocumentType as ParserDocumentType
        
        vendor.total_documents += 1
        
        if document_data.document_type == ParserDocumentType.PURCHASE_ORDER:
            vendor.total_orders += 1
        elif document_data.document_type == ParserDocumentType.INVOICE:
            vendor.total_invoices += 1
        elif document_data.document_type == ParserDocumentType.RECEIPT:
            vendor.total_receipts += 1
        
        # Update total amount if available
        if hasattr(document_data, 'total_amount') and document_data.total_amount:
            vendor.total_amount += document_data.total_amount
    
    async def generate_report(self):
        """Generate processing report"""
        print("\n" + "="*60)
        print("📋 PDF PROCESSING REPORT")
        print("="*60)
        
        print(f"📄 Total documents processed: {len(self.processed_documents)}")
        print(f"❌ Errors encountered: {len(self.errors)}")
        
        if self.processed_documents:
            print("\n📊 Successfully processed documents:")
            for doc in self.processed_documents:
                print(f"  • {doc['file_path']} -> {doc['document_type']} ({doc['document_number']}) - Confidence: {doc['confidence']:.2f}")
        
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  • {error}")
        
        # Database statistics
        await self.show_database_statistics()
    
    async def show_database_statistics(self):
        """Show database statistics"""
        print("\n📊 DATABASE STATISTICS")
        print("-" * 40)
        
        try:
            with DatabaseSession(self.db_path) as session:
                # Count records by table
                business_docs = session.query(BusinessDocument).count()
                pos = session.query(PurchaseOrder).count()
                invoices = session.query(Invoice).count()
                receipts = session.query(Receipt).count()
                line_items = session.query(DocumentLineItem).count()
                vendors = session.query(Vendor).count()
                
                print(f"Business Documents: {business_docs}")
                print(f"Purchase Orders: {pos}")
                print(f"Invoices: {invoices}")
                print(f"Receipts: {receipts}")
                print(f"Line Items: {line_items}")
                print(f"Vendors: {vendors}")
                
                # Show vendor statistics
                print("\n👥 VENDOR STATISTICS:")
                top_vendors = session.query(Vendor).order_by(Vendor.total_documents.desc()).limit(5).all()
                for vendor in top_vendors:
                    print(f"  • {vendor.name}: {vendor.total_documents} docs, ${vendor.total_amount}")
                
        except Exception as e:
            print(f"❌ Error getting database statistics: {e}")
    
    async def query_documents(self, query_type: str = "all"):
        """Query and display documents from database"""
        print(f"\n🔍 QUERYING DOCUMENTS ({query_type.upper()})")
        print("-" * 40)
        
        try:
            with DatabaseSession(self.db_path) as session:
                if query_type == "all":
                    docs = session.query(BusinessDocument).all()
                elif query_type == "po":
                    docs = session.query(BusinessDocument).filter_by(document_type=DocumentType.PURCHASE_ORDER).all()
                elif query_type == "invoice":
                    docs = session.query(BusinessDocument).filter_by(document_type=DocumentType.INVOICE).all()
                elif query_type == "receipt":
                    docs = session.query(BusinessDocument).filter_by(document_type=DocumentType.RECEIPT).all()
                else:
                    docs = session.query(BusinessDocument).all()
                
                for doc in docs:
                    print(f"  📄 {doc.document_type.value.upper()}: {doc.document_number}")
                    print(f"     Vendor: {doc.vendor}")
                    print(f"     Date: {doc.date}")
                    print(f"     File: {doc.pdf_filename}")
                    print(f"     Confidence: {doc.parsing_confidence}")
                    print()
                
        except Exception as e:
            print(f"❌ Error querying documents: {e}")


async def main():
    """Main workflow execution"""
    print("🚀 PDF to Database Workflow Started")
    print("=" * 50)
    
    # Initialize workflow
    workflow = PDFProcessingWorkflow()
    
    try:
        # Step 1: Initialize database
        await workflow.initialize_database()
        
        # Step 2: Process PDF files
        await workflow.process_pdf_files("sample_data")
        
        # Step 3: Generate report
        await workflow.generate_report()
        
        # Step 4: Query documents
        await workflow.query_documents("all")
        
        print("\n✅ Workflow completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 