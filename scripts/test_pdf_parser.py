#!/usr/bin/env python3
"""
Test script for PDF parser functionality
Start a PurchaseOrderParser instance, call parse_pdf with sample pdf files and print the result
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pdf_parser.parser import BusinessDocumentPDFParser

parser = BusinessDocumentPDFParser()
result = asyncio.run(parser.parse_document("sample_data/PO-1003_Nova_Plastics.pdf"))
result = asyncio.run(parser.parse_document("sample_data/RCPT-7123_Nova_Plastics.pdf"))
result = asyncio.run(parser.parse_document("sample_data/INV-8893_Nova_Plastics.pdf"))

print(result)
