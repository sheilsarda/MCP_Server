## Start a PurchaseOrderParser instance
## call parse_pdf with a sample pdf file
## print the result

from src.pdf_parser.parser import PurchaseOrderPDFParser
import asyncio

parser = PurchaseOrderPDFParser()
result = asyncio.run(parser.parse_pdf("PO-1003_Nova_Plastics.pdf"))
print(result)
