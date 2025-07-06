## Start a PurchaseOrderParser instance
## call parse_pdf with a sample pdf file
## print the result

from src.pdf_parser.parser import BusinessDocumentPDFParser
import asyncio

parser = BusinessDocumentPDFParser()
result = asyncio.run(parser.parse_document("PO-1003_Nova_Plastics.pdf"))
print(result)
