```sh
(mcp) MCP_Serversheil:~/MCP_Server$ python -m scripts.pdf_to_database_workflow
🚀 PDF to Database Workflow Started
==================================================
🔧 Initializing database...
Creating database tables in: /home/sheil/MCP_Server/business_documents.db
2025-07-06 16:37:04,214 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2025-07-06 16:37:04,215 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("business_documents")
2025-07-06 16:37:04,215 INFO sqlalchemy.engine.Engine [raw sql] ()
2025-07-06 16:37:04,216 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("purchase_orders")
2025-07-06 16:37:04,216 INFO sqlalchemy.engine.Engine [raw sql] ()
2025-07-06 16:37:04,216 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("invoices")
2025-07-06 16:37:04,216 INFO sqlalchemy.engine.Engine [raw sql] ()
2025-07-06 16:37:04,216 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("receipts")
2025-07-06 16:37:04,216 INFO sqlalchemy.engine.Engine [raw sql] ()
2025-07-06 16:37:04,217 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("document_line_items")
2025-07-06 16:37:04,217 INFO sqlalchemy.engine.Engine [raw sql] ()
2025-07-06 16:37:04,217 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("vendors")
2025-07-06 16:37:04,217 INFO sqlalchemy.engine.Engine [raw sql] ()
2025-07-06 16:37:04,218 INFO sqlalchemy.engine.Engine PRAGMA main.table_info("extraction_templates")
2025-07-06 16:37:04,218 INFO sqlalchemy.engine.Engine [raw sql] ()
2025-07-06 16:37:04,218 INFO sqlalchemy.engine.Engine COMMIT
2025-07-06 16:37:04,219 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2025-07-06 16:37:04,219 INFO sqlalchemy.engine.Engine 
            CREATE INDEX IF NOT EXISTS idx_business_documents_vendor_date 
            ON business_documents(vendor, date)
        
2025-07-06 16:37:04,219 INFO sqlalchemy.engine.Engine [generated in 0.00027s] ()
2025-07-06 16:37:04,220 INFO sqlalchemy.engine.Engine 
            CREATE INDEX IF NOT EXISTS idx_business_documents_type_date 
            ON business_documents(document_type, date)
        
2025-07-06 16:37:04,220 INFO sqlalchemy.engine.Engine [generated in 0.00019s] ()
2025-07-06 16:37:04,220 INFO sqlalchemy.engine.Engine 
            CREATE INDEX IF NOT EXISTS idx_invoices_reference_po 
            ON invoices(reference_po)
        
2025-07-06 16:37:04,220 INFO sqlalchemy.engine.Engine [generated in 0.00014s] ()
2025-07-06 16:37:04,220 INFO sqlalchemy.engine.Engine 
            CREATE INDEX IF NOT EXISTS idx_receipts_reference_po 
            ON receipts(reference_po)
        
2025-07-06 16:37:04,220 INFO sqlalchemy.engine.Engine [generated in 0.00012s] ()
2025-07-06 16:37:04,221 INFO sqlalchemy.engine.Engine COMMIT
Database initialized successfully at: /home/sheil/MCP_Server/business_documents.db
📊 Database initialized: {'database_path': '/home/sheil/MCP_Server/business_documents.db', 'file_size': 159744, 'tables': {'business_documents': 0, 'document_line_items': 0, 'extraction_templates': 0, 'invoices': 0, 'purchase_orders': 0, 'receipts': 0, 'vendors': 0}}
📄 Processing PDF files from: sample_data

🔍 Processing: RCPT-7122_Apex_Motors_Ltd.pdf
INFO: Parsing document: sample_data/RCPT-7122_Apex_Motors_Ltd.pdf
INFO: Detected document type: receipt
DEBUG: Extracted receipt_id: RCPT-7122
DEBUG: Extracted vendor: Apex Motors Ltd.
DEBUG: Extracted reference_po: PO-1002
DEBUG: Extracted item: Hydraulic Pump
Quantity Received
DEBUG: Extracted quantity_received: 8
DEBUG: Extracted date_received: 2024-10-13
INFO: Document parsing completed. Confidence: 0.60
✅ Successfully processed and stored: RCPT-7122_Apex_Motors_Ltd.pdf

🔍 Processing: INV-8893_Nova_Plastics.pdf
INFO: Parsing document: sample_data/INV-8893_Nova_Plastics.pdf
INFO: Detected document type: invoice
DEBUG: Extracted invoice_number: INV-8893
DEBUG: Extracted reference_po: PO-1003
DEBUG: Extracted vendor: Nova Plastics
DEBUG: Extracted date: 2024-10-14
DEBUG: Extracted total: 77,890.00
DEBUG: Extracted item: Polycarbonate Sheet
Quantity
DEBUG: Extracted quantity: 200
DEBUG: Extracted unit_price: 389.45
INFO: Document parsing completed. Confidence: 1.00
✅ Successfully processed and stored: INV-8893_Nova_Plastics.pdf

🔍 Processing: RCPT-7123_Nova_Plastics.pdf
INFO: Parsing document: sample_data/RCPT-7123_Nova_Plastics.pdf
INFO: Detected document type: receipt
DEBUG: Extracted receipt_id: RCPT-7123
DEBUG: Extracted vendor: Nova Plastics
DEBUG: Extracted reference_po: PO-1003
DEBUG: Extracted item: Polycarbonate Sheet
Quantity Received
DEBUG: Extracted quantity_received: 200
DEBUG: Extracted date_received: 2024-10-15
INFO: Document parsing completed. Confidence: 0.60
✅ Successfully processed and stored: RCPT-7123_Nova_Plastics.pdf

🔍 Processing: INV-8892_Apex_Motors_Ltd.pdf
INFO: Parsing document: sample_data/INV-8892_Apex_Motors_Ltd.pdf
INFO: Detected document type: invoice
DEBUG: Extracted invoice_number: INV-8892
DEBUG: Extracted reference_po: PO-1002
DEBUG: Extracted vendor: Apex Motors Ltd.
DEBUG: Extracted date: 2024-10-12
DEBUG: Extracted total: 130,000.00
DEBUG: Extracted item: Hydraulic Pump
Quantity
DEBUG: Extracted quantity: 10
DEBUG: Extracted unit_price: 13,000.00
INFO: Document parsing completed. Confidence: 1.00
✅ Successfully processed and stored: INV-8892_Apex_Motors_Ltd.pdf

🔍 Processing: PO-1001_Titan_Steel_Co.pdf
INFO: Parsing document: sample_data/PO-1001_Titan_Steel_Co.pdf
INFO: Detected document type: purchase_order
DEBUG: Extracted po_number: PO-1001
DEBUG: Extracted vendor: Titan Steel Co.
DEBUG: Extracted date: 2024-10-01
DEBUG: Extracted total: 117,283.50
DEBUG: Extracted item: Stainless Steel Roll
Quantity
DEBUG: Extracted quantity: 50
DEBUG: Extracted unit_price: 2,345.67
INFO: Document parsing completed. Confidence: 1.00
✅ Successfully processed and stored: PO-1001_Titan_Steel_Co.pdf

🔍 Processing: RCPT-7121_Titan_Steel_Co.pdf
INFO: Parsing document: sample_data/RCPT-7121_Titan_Steel_Co.pdf
INFO: Detected document type: receipt
DEBUG: Extracted receipt_id: RCPT-7121
DEBUG: Extracted vendor: Titan Steel Co.
DEBUG: Extracted reference_po: PO-1001
DEBUG: Extracted item: Stainless Steel Roll
Quantity Received
DEBUG: Extracted quantity_received: 50
DEBUG: Extracted date_received: 2024-10-11
INFO: Document parsing completed. Confidence: 0.60
✅ Successfully processed and stored: RCPT-7121_Titan_Steel_Co.pdf

🔍 Processing: INV-8891_Titan_Steel_Co.pdf
INFO: Parsing document: sample_data/INV-8891_Titan_Steel_Co.pdf
INFO: Detected document type: invoice
DEBUG: Extracted invoice_number: INV-8891
DEBUG: Extracted reference_po: PO-1001
DEBUG: Extracted vendor: Titan Steel Co.
DEBUG: Extracted date: 2024-10-10
DEBUG: Extracted total: 117,283.50
DEBUG: Extracted item: Stainless Steel Roll
Quantity
DEBUG: Extracted quantity: 50
DEBUG: Extracted unit_price: 2,345.67
INFO: Document parsing completed. Confidence: 1.00
✅ Successfully processed and stored: INV-8891_Titan_Steel_Co.pdf

🔍 Processing: PO-1002_Apex_Motors_Ltd.pdf
INFO: Parsing document: sample_data/PO-1002_Apex_Motors_Ltd.pdf
INFO: Detected document type: purchase_order
DEBUG: Extracted po_number: PO-1002
DEBUG: Extracted vendor: Apex Motors Ltd.
DEBUG: Extracted date: 2024-10-05
DEBUG: Extracted total: 124,999.90
DEBUG: Extracted item: Hydraulic Pump
Quantity
DEBUG: Extracted quantity: 10
DEBUG: Extracted unit_price: 12,499.99
INFO: Document parsing completed. Confidence: 1.00
✅ Successfully processed and stored: PO-1002_Apex_Motors_Ltd.pdf

🔍 Processing: PO-1003_Nova_Plastics.pdf
INFO: Parsing document: sample_data/PO-1003_Nova_Plastics.pdf
INFO: Detected document type: purchase_order
DEBUG: Extracted po_number: PO-1003
DEBUG: Extracted vendor: Nova Plastics
DEBUG: Extracted date: 2024-10-08
DEBUG: Extracted total: 77,890.00
DEBUG: Extracted item: Polycarbonate Sheet
Quantity
DEBUG: Extracted quantity: 200
DEBUG: Extracted unit_price: 389.45
INFO: Document parsing completed. Confidence: 1.00
✅ Successfully processed and stored: PO-1003_Nova_Plastics.pdf

============================================================
📋 PDF PROCESSING REPORT
============================================================
📄 Total documents processed: 9
❌ Errors encountered: 0

📊 Successfully processed documents:
  • sample_data/RCPT-7122_Apex_Motors_Ltd.pdf -> receipt (RCPT-7122) - Confidence: 0.60
  • sample_data/INV-8893_Nova_Plastics.pdf -> invoice (INV-8893) - Confidence: 1.00
  • sample_data/RCPT-7123_Nova_Plastics.pdf -> receipt (RCPT-7123) - Confidence: 0.60
  • sample_data/INV-8892_Apex_Motors_Ltd.pdf -> invoice (INV-8892) - Confidence: 1.00
  • sample_data/PO-1001_Titan_Steel_Co.pdf -> purchase_order (PO-1001) - Confidence: 1.00
  • sample_data/RCPT-7121_Titan_Steel_Co.pdf -> receipt (RCPT-7121) - Confidence: 0.60
  • sample_data/INV-8891_Titan_Steel_Co.pdf -> invoice (INV-8891) - Confidence: 1.00
  • sample_data/PO-1002_Apex_Motors_Ltd.pdf -> purchase_order (PO-1002) - Confidence: 1.00
  • sample_data/PO-1003_Nova_Plastics.pdf -> purchase_order (PO-1003) - Confidence: 1.00

📊 DATABASE STATISTICS
----------------------------------------
Business Documents: 9
Purchase Orders: 3
Invoices: 3
Receipts: 3
Line Items: 6
Vendors: 3

👥 VENDOR STATISTICS:
  • Apex Motors Ltd: 3 docs, $254999.90
  • Nova Plastics: 3 docs, $155780.00
  • Titan Steel Co: 3 docs, $234567.00

🔍 QUERYING DOCUMENTS (ALL)
----------------------------------------
  📄 RECEIPT: RCPT-7122
     Vendor: Apex Motors Ltd
     Date: 2024-10-13 00:00:00
     File: RCPT-7122_Apex_Motors_Ltd.pdf
     Confidence: 0.60

  📄 INVOICE: INV-8893
     Vendor: Nova Plastics
     Date: 2024-10-14 00:00:00
     File: INV-8893_Nova_Plastics.pdf
     Confidence: 1.00

  📄 RECEIPT: RCPT-7123
     Vendor: Nova Plastics
     Date: 2024-10-15 00:00:00
     File: RCPT-7123_Nova_Plastics.pdf
     Confidence: 0.60

  📄 INVOICE: INV-8892
     Vendor: Apex Motors Ltd
     Date: 2024-10-12 00:00:00
     File: INV-8892_Apex_Motors_Ltd.pdf
     Confidence: 1.00

  📄 PURCHASE_ORDER: PO-1001
     Vendor: Titan Steel Co
     Date: 2024-10-01 00:00:00
     File: PO-1001_Titan_Steel_Co.pdf
     Confidence: 1.00

  📄 RECEIPT: RCPT-7121
     Vendor: Titan Steel Co
     Date: 2024-10-11 00:00:00
     File: RCPT-7121_Titan_Steel_Co.pdf
     Confidence: 0.60

  📄 INVOICE: INV-8891
     Vendor: Titan Steel Co
     Date: 2024-10-10 00:00:00
     File: INV-8891_Titan_Steel_Co.pdf
     Confidence: 1.00

  📄 PURCHASE_ORDER: PO-1002
     Vendor: Apex Motors Ltd
     Date: 2024-10-05 00:00:00
     File: PO-1002_Apex_Motors_Ltd.pdf
     Confidence: 1.00

  📄 PURCHASE_ORDER: PO-1003
     Vendor: Nova Plastics
     Date: 2024-10-08 00:00:00
     File: PO-1003_Nova_Plastics.pdf
     Confidence: 1.00


✅ Workflow completed successfully!
(mcp) MCP_Serversheil:~/MCP_Server$ 

```