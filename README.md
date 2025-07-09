# Business Document PDF Parser

A FastMCP-based server for parsing business PDF documents (purchase orders, invoices, and receipts) and storing them in a searchable SQLite database. This project provides automated extraction of structured data from various business document types.

## Current Status

✅ **Working Features:**
- PDF parsing for purchase orders, invoices, and receipts
- Database storage with SQLite
- 10 functional MCP tools for document management
- Automated workflow scripts for batch processing
- Document type detection and structured data extraction
- Vendor normalization and search capabilities

## Features

- **Multi-Document Support**: Parse purchase orders, invoices, and receipts from PDF files
- **Database Storage**: Store parsed documents in SQLite with comprehensive search capabilities
- **MCP Tools**: 10 FastMCP tools for document parsing, searching, and management
- **PDF Parser**: Robust PDF text extraction using pypdf with fallback strategies
- **Document Type Detection**: Automatic detection of document types based on content patterns
- **Confidence Scoring**: Extraction confidence scoring for data quality assessment
- **Batch Processing**: Scripts for processing multiple documents at once
- **Vendor Management**: Automatic vendor name extraction and normalization

## Supported Document Types

The system currently supports three types of business documents:

1. **Purchase Orders** (PO-XXXX format)
2. **Invoices** (INV-XXXX format)  
3. **Receipts** (RCPT-XXXX format)

## Project Structure

```
MCP_Server/
├── src/
│   ├── database/
│   │   ├── models.py              # SQLAlchemy models for business documents
│   │   ├── connection.py          # Database connection management
│   │   ├── queries.py             # Database query functions
│   │   └── setup.py               # Database initialization
│   ├── pdf_parser/
│   │   └── parser.py              # PDF parsing with document type detection
│   ├── mcp_server/
│   │   └── server.py              # FastMCP server with 10 business document tools
│   ├── config.py                  # Configuration management with environment variables
│   └── __init__.py
├── scripts/
│   ├── pdf_to_database_workflow.py  # Batch processing workflow
│   ├── query_database.py           # Database query utilities
│   ├── clear_database.py           # Database cleanup
│   └── test_pdf_parser.py          # Parser testing
├── sample_data/                    # Sample PDFs for testing
│   ├── PO-1001_Titan_Steel_Co.pdf
│   ├── INV-8891_Titan_Steel_Co.pdf
│   ├── RCPT-7121_Titan_Steel_Co.pdf
│   └── (more samples...)
├── business_documents.db           # SQLite database (created after first run)
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Database Schema

The system uses SQLAlchemy with the following core tables:

### `business_documents` (Main table)
- Document metadata, vendor info, dates, totals
- Document type (purchase_order, invoice, receipt)
- Extraction confidence and methods
- File paths and processing status

### `document_line_items`
- Individual line items for each document
- Item descriptions, quantities, prices
- Linked to parent documents

### `vendors`
- Vendor information and statistics
- Normalized vendor names
- Total order counts and amounts

## Installation

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database** (optional - auto-created on first run):
   ```bash
   python -c "from src.database.setup import initialize_database; initialize_database()"
   ```

## Usage

### Running the MCP Server

```bash
# From the project root directory
python -m src.mcp_server.server
```

### Batch Processing Sample Data

```bash
# Process all sample PDFs and store in database
python -m scripts.pdf_to_database_workflow
```

### Available MCP Tools

The server exposes 10 MCP tools:

#### 1. `parse_pdf_document`
Parse a PDF document and extract structured data.

**Parameters:**
- `file_path` (str): Path to the PDF file
- `store_in_db` (bool): Whether to store in database (default: True)

**Returns:**
- Document details with extracted data and confidence scores

#### 2. `search_documents`
Search documents by various criteria.

**Parameters:**
- `query` (str): Search query (document number, vendor, etc.)
- `limit` (int): Maximum results (default: 20)
- `include_line_items` (bool): Include line item details

#### 3. `get_document_details`
Get a specific document by database ID.

**Parameters:**
- `document_id` (int): Database ID of the document
- `include_line_items` (bool): Include line item details

#### 4. `get_document_summary`
Get summary statistics for all documents.

**Returns:**
- Total documents, total values, vendor counts, etc.

#### 5. `list_documents`
List documents with pagination and filtering.

**Parameters:**
- `offset` (int): Records to skip (default: 0)
- `limit` (int): Maximum records (default: 20)
- `vendor` (str): Optional vendor filter
- `document_type` (str): Optional document type filter

#### 6. `validate_pdf_format`
Validate if a PDF appears to contain business document data.

#### 7. `search_by_document_number`
Search for a document by its specific document number.

#### 8. `search_by_vendor`
Search for documents by vendor name.

#### 9. `get_purchase_orders`
Get purchase orders specifically with pagination.

#### 10. `initialize_database_tables`
Initialize or recreate database tables.

### Example Usage

```python
# Parse a PDF document
result = await parse_pdf_document("sample_data/PO-1003_Nova_Plastics.pdf", store_in_db=True)
print(f"Document: {result.document_number}")
print(f"Type: {result.document_type}")
print(f"Vendor: {result.vendor}")
print(f"Confidence: {result.extraction_confidence}")

# Search for documents
search_results = await search_documents("Nova Plastics", limit=10)
for doc in search_results.results:
    print(f"Doc {doc['document_number']}: {doc['vendor']} - ${doc['total_amount']}")

# Get document summary
summary = await get_document_summary()
print(f"Total Documents: {summary.total_documents}")
print(f"Total Value: ${summary.total_value}")
```

## Configuration

Configuration is managed through environment variables and the `src/config.py` file:

### Key Settings
- `PO_PARSER_DATABASE_URL`: Database connection URL
- `PO_PARSER_MAX_PDF_SIZE`: Maximum PDF file size (50MB default)
- `PO_PARSER_PARSING_TIMEOUT`: PDF parsing timeout (120s default)
- `PO_PARSER_EXTRACTION_CONFIDENCE_THRESHOLD`: Minimum confidence threshold (0.5 default)
- `PO_PARSER_DEBUG`: Enable debug mode

## Development

### Current Implementation Status

**✅ Completed:**
- PDF parsing with pypdf
- Document type detection (PO, Invoice, Receipt)
- Database models and operations
- All 10 MCP tools functional
- Batch processing workflow
- Sample data processing
- Configuration management

**🔄 In Progress:**
- Advanced line item extraction
- Multiple PDF parsing libraries (PDFPlumber, PyMuPDF)
- OCR support for scanned documents

**📋 TODO:**
- Comprehensive test suite
- Web-based admin interface
- Export functionality (Excel, CSV)
- Machine learning for pattern recognition
- Multi-format document support

### Testing

```bash
# Test PDF parsing
python -m scripts.test_pdf_parser

# Test database operations
python -m scripts.query_database

# Process sample data
python -m scripts.pdf_to_database_workflow
```

## Sample Data

The project includes 9 sample PDF files:
- 3 Purchase Orders (PO-1001, PO-1002, PO-1003)
- 3 Invoices (INV-8891, INV-8892, INV-8893)
- 3 Receipts (RCPT-7121, RCPT-7122, RCPT-7123)

Each from vendors: Titan Steel Co, Apex Motors Ltd, Nova Plastics

## Dependencies

Key dependencies include:

- **FastMCP**: MCP server framework
- **SQLAlchemy**: Database ORM
- **pypdf**: PDF parsing
- **Pydantic**: Data validation
- **Loguru**: Enhanced logging
- **python-dotenv**: Environment variables

## Performance

- **PDF Processing**: Successfully processes typical business documents in < 2 seconds
- **Database**: SQLite with optimized indexes for fast searching
- **Confidence Scoring**: Automated quality assessment for extracted data
- **Batch Processing**: Handles multiple documents efficiently

## Troubleshooting

### Common Issues

1. **PDF Parsing Fails**:
   - Check if PDF is encrypted or corrupted
   - Verify file permissions
   - Try with different sample documents

2. **Database Errors**:
   - Check file permissions in project directory
   - Verify SQLite support
   - Run database initialization script

3. **Low Extraction Confidence**:
   - Document may have non-standard format
   - Check if document type is supported
   - Review extraction patterns in config

### Debug Mode

Enable debug mode for detailed logging:
```bash
export PO_PARSER_DEBUG=True
python -m src.mcp_server.server
```

## Support

For questions or issues:
1. Check the `Logs.md` file for recent processing logs
2. Review the sample data processing results
3. Test with the provided sample PDFs

## Changelog

### v1.0.0 (Current - Fully Functional)
- ✅ Complete PDF parsing implementation
- ✅ Multi-document type support (PO, Invoice, Receipt)
- ✅ 10 functional MCP tools
- ✅ Database storage and search
- ✅ Batch processing workflows
- ✅ Sample data processing
- ✅ Configuration management
- ✅ Confidence scoring system
- ✅ Vendor management and normalization
