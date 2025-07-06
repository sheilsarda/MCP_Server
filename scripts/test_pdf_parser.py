## Start a PurchaseOrderParser instance
## call parse_pdf with a sample pdf file
## print the result

from src.pdf_parser.parser import PurchaseOrderPDFParser
import asyncio

parser = PurchaseOrderPDFParser()
result = asyncio.run(parser.parse_pdf("PO-1003_Nova_Plastics.pdf"))
print(result)

"""
INFO: Parsing PDF: PO-1003_Nova_Plastics.pdf
DEBUG: Extracted po_number: PO-1003
DEBUG: Extracted vendor: Nova Plastics
DEBUG: Extracted date: 2024-10-08
DEBUG: Extracted total: 77,890.00
DEBUG: Extracted item: Polycarbonate Sheet
Quantity
DEBUG: Extracted quantity: 200
DEBUG: Extracted unit_price: 389.45
INFO: PDF parsing completed. Confidence: 1.00
PurchaseOrderData(po_number='PO-1003', vendor='Nova Plastics', date=datetime.datetime(2024, 10, 8, 0, 0), total_amount=Decimal('77890.00'), line_items=[{'item_description': 'Polycarbonate Sheet\nQuantity', 'quantity': 200, 'unit_price': Decimal('389.45'), 'line_total': Decimal('77890.00'), 'extraction_confidence': 0.7}], extraction_confidence=1.0, extraction_method='pypdf2', raw_text='Nova Plastics - Purchase Order\nPO Number: PO-1003\nVendor: Nova Plastics\nItem: Polycarbonate Sheet\nQuantity: 200\nUnit Price: $389.45\nTotal: $77,890.00\nDate: 2024-10-08', metadata={})
(mcp) MCP_Serv
"""