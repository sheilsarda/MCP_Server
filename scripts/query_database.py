#!/usr/bin/env python3
"""
Simple script to query and display database contents
"""

import os
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.connection import DatabaseSession
from database.models import BusinessDocument, PurchaseOrder, Invoice, Receipt, DocumentLineItem, Vendor

def display_database_contents():
    """Display all database contents in a readable format"""
    
    with DatabaseSession() as session:
        print("🏢 BUSINESS DOCUMENTS")
        print("=" * 50)
        
        docs = session.query(BusinessDocument).all()
        for doc in docs:
            print(f"ID: {doc.id}")
            print(f"Type: {doc.document_type.value}")
            print(f"Number: {doc.document_number}")
            print(f"Vendor: {doc.vendor}")
            print(f"Date: {doc.date}")
            print(f"File: {doc.pdf_filename}")
            print(f"Confidence: {doc.parsing_confidence}")
            print(f"Status: {doc.status}")
            print("-" * 30)
        
        print("\n💰 PURCHASE ORDERS")
        print("=" * 50)
        
        pos = session.query(PurchaseOrder).all()
        for po in pos:
            print(f"ID: {po.id}")
            print(f"Document ID: {po.document_id}")
            print(f"PO Number: {po.po_number}")
            print(f"Total: ${po.total_amount}")
            print("-" * 30)
        
        print("\n📋 INVOICES")
        print("=" * 50)
        
        invoices = session.query(Invoice).all()
        for inv in invoices:
            print(f"ID: {inv.id}")
            print(f"Document ID: {inv.document_id}")
            print(f"Invoice Number: {inv.invoice_number}")
            print(f"Reference PO: {inv.reference_po}")
            print(f"Total: ${inv.total_amount}")
            print(f"Item: {inv.item_description}")
            print(f"Quantity: {inv.quantity}")
            print(f"Unit Price: ${inv.unit_price}")
            print("-" * 30)
        
        print("\n🧾 RECEIPTS")
        print("=" * 50)
        
        receipts = session.query(Receipt).all()
        for rcpt in receipts:
            print(f"ID: {rcpt.id}")
            print(f"Document ID: {rcpt.document_id}")
            print(f"Receipt ID: {rcpt.receipt_id}")
            print(f"Reference PO: {rcpt.reference_po}")
            print(f"Date Received: {rcpt.date_received}")
            print(f"Item: {rcpt.item_description}")
            print(f"Quantity Received: {rcpt.quantity_received}")
            print("-" * 30)
        
        print("\n📝 LINE ITEMS")
        print("=" * 50)
        
        items = session.query(DocumentLineItem).all()
        for item in items:
            print(f"ID: {item.id}")
            print(f"Document ID: {item.document_id}")
            print(f"Item: {item.item_description}")
            print(f"Quantity: {item.quantity}")
            print(f"Unit Price: ${item.unit_price}")
            print(f"Line Total: ${item.line_total}")
            print(f"Confidence: {item.extraction_confidence}")
            print("-" * 30)
        
        print("\n👥 VENDORS")
        print("=" * 50)
        
        vendors = session.query(Vendor).all()
        for vendor in vendors:
            print(f"ID: {vendor.id}")
            print(f"Name: {vendor.name}")
            print(f"Normalized: {vendor.normalized_name}")
            print(f"Total Documents: {vendor.total_documents}")
            print(f"Total Orders: {vendor.total_orders}")
            print(f"Total Invoices: {vendor.total_invoices}")
            print(f"Total Receipts: {vendor.total_receipts}")
            print(f"Total Amount: ${vendor.total_amount}")
            print("-" * 30)

if __name__ == "__main__":
    display_database_contents() 