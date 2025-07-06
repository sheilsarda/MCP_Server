# Purchase Order PDF Parser

A FastMCP-based server for parsing PDF purchase orders and storing them in a searchable SQLite database. This project provides automated extraction of structured purchase order data from PDF documents.

## Features

- **PDF Parsing**: Extract structured data from purchase order PDFs using multiple parsing strategies
- **Database Storage**: Store parsed purchase orders in SQLite with full-text search capabilities
- **MCP Tools**: Expose parsing and search functionality through FastMCP tools
- **Multiple Parsers**: Support for PyPDF2, PDFPlumber, and PyMuPDF for robust extraction
- **Regex Patterns**: Configurable regex patterns for different PO formats
- **Confidence Scoring**: Extraction confidence scoring for data quality assessment
- **Search & Filter**: Advanced search and filtering capabilities for stored purchase orders

## Sample Data Format

The parser is designed to extract data from purchase orders in this format:

```
PO Number: PO-1003
Vendor: Nova Plastics
Item: Polycarbonate Sheet
Quantity: 200
Unit Price: $389.45
Total: $77,890.00
Date: 2024-10-08
```

## Project Structure

```
MCP_Server/
├── src/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py              # SQLAlchemy models for PO data
│   │   └── connection.py          # Database connection management
│   ├── pdf_parser/
│   │   ├── __init__.py
│   │   └── parser.py              # PDF parsing with multiple strategies
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   └── server.py              # FastMCP server with PO tools
│   ├── config.py                  # Configuration management
│   └── __init__.py
├── sample_data/
│   └── sample_po.txt              # Sample purchase order format
├── tests/                         # Test files (to be implemented)
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Database Schema

The system uses SQLAlchemy with the following tables:

### `purchase_orders`
- `id`: Primary key
- `po_number`: Purchase order number (unique)
- `vendor`: Vendor/supplier name
- `date`: Purchase order date
- `total_amount`: Total order amount
- `pdf_filename`: Original PDF filename
- `pdf_path`: Path to PDF file
- `extraction_confidence`: Confidence score (0.0-1.0)
- `extraction_method`: Parser used
- `raw_text`: Raw extracted text
- `status`: Processing status
- `created_at`, `updated_at`: Timestamps

### `purchase_order_items`
- `id`: Primary key
- `purchase_order_id`: Foreign key to purchase_orders
- `item_description`: Item description
- `quantity`: Quantity ordered
- `unit_price`: Price per unit
- `line_total`: Total for this line item
- `item_code`: Optional item code
- `unit_of_measure`: Unit of measure (EA, LB, etc.)

### `vendors`
- `id`: Primary key
- `name`: Vendor name
- `normalized_name`: Standardized vendor name
- `total_orders`: Number of orders
- `total_amount`: Total order value

### `extraction_templates`
- `id`: Primary key
- `name`: Template name
- `description`: Template description
- `po_number_pattern`: Regex pattern for PO numbers
- `vendor_pattern`: Regex pattern for vendors
- `date_pattern`: Regex pattern for dates
- `total_pattern`: Regex pattern for totals
- `is_active`: Whether template is active
- `priority`: Template priority (higher = tried first)

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

3. **Set up environment variables** (optional):
   ```bash
   # Copy the example environment file
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Initialize the database**:
   ```bash
   python -c "from src.database.connection import init_database; import asyncio; asyncio.run(init_database())"
   ```

## Usage

### Running the MCP Server

```bash
# From the project root directory
python -m src.mcp_server.server
```

### Available MCP Tools

The server exposes the following tools:

#### 1. `parse_pdf_purchase_order`
Parse a PDF purchase order and extract structured data.

**Parameters:**
- `file_path` (str): Path to the PDF file
- `store_in_db` (bool): Whether to store in database (default: True)

**Returns:**
- `success` (bool): Whether parsing succeeded
- `po_number` (str): Extracted PO number
- `vendor` (str): Extracted vendor name
- `date` (str): Extracted date
- `total_amount` (float): Extracted total amount
- `line_items_count` (int): Number of line items
- `extraction_confidence` (float): Confidence score
- `database_id` (int): Database ID if stored

#### 2. `search_purchase_orders`
Search purchase orders by various criteria.

**Parameters:**
- `query` (str): Search query (PO number, vendor, etc.)
- `limit` (int): Maximum results (default: 20)
- `include_line_items` (bool): Include line item details

**Returns:**
- `success` (bool): Whether search succeeded
- `results` (list): List of matching purchase orders
- `total_count` (int): Total number of results

#### 3. `get_purchase_order_by_id`
Get a specific purchase order by database ID.

**Parameters:**
- `po_id` (int): Database ID of the purchase order
- `include_line_items` (bool): Include line item details

#### 4. `get_purchase_order_summary`
Get summary statistics for all purchase orders.

**Returns:**
- `total_pos` (int): Total number of purchase orders
- `total_value` (float): Total value of all orders
- `unique_vendors` (int): Number of unique vendors
- `top_vendors` (list): Top vendors by order value

#### 5. `list_purchase_orders`
List purchase orders with pagination and filtering.

**Parameters:**
- `offset` (int): Records to skip (default: 0)
- `limit` (int): Maximum records (default: 20)
- `vendor` (str): Optional vendor filter

#### 6. `validate_pdf_format`
Validate if a PDF appears to contain purchase order data.

**Parameters:**
- `file_path` (str): Path to PDF file

**Returns:**
- `is_valid_pdf` (bool): Whether file is a valid PDF
- `appears_to_be_po` (bool): Whether it appears to be a PO
- `validation_confidence` (float): Confidence score

### Example Usage

```python
# Parse a PDF purchase order
result = await parse_pdf_purchase_order("sample_data/po_1003.pdf", store_in_db=True)
print(f"PO Number: {result.po_number}")
print(f"Vendor: {result.vendor}")
print(f"Total: ${result.total_amount}")
print(f"Confidence: {result.extraction_confidence}")

# Search for purchase orders
search_results = await search_purchase_orders("Nova Plastics", limit=10)
for po in search_results.results:
    print(f"PO {po['po_number']}: {po['vendor']} - ${po['total_amount']}")

# Get purchase order summary
summary = await get_purchase_order_summary()
print(f"Total POs: {summary.total_pos}")
print(f"Total Value: ${summary.total_value}")
```

## Configuration

Configuration is managed through environment variables and the `src/config.py` file:

### Key Environment Variables

- `PO_PARSER_DATABASE_URL`: Database connection URL
- `PO_PARSER_MAX_PDF_SIZE`: Maximum PDF file size
- `PO_PARSER_PARSING_TIMEOUT`: PDF parsing timeout
- `PO_PARSER_EXTRACTION_CONFIDENCE_THRESHOLD`: Minimum confidence threshold
- `PO_PARSER_STORAGE_DIRECTORY`: Directory for storing PDFs
- `PO_PARSER_DEBUG`: Enable debug mode

### Configuration File

The `src/config.py` file contains all configurable settings including:

- Regex patterns for data extraction
- Database connection settings
- Parsing strategy preferences
- File size limits
- Logging configuration

## Development

### TODO List

The project includes comprehensive TODO comments throughout the codebase:

#### High Priority (Core Implementation)
- [ ] Complete PDF parsing implementation using PyPDF2, PDFPlumber, and PyMuPDF
- [ ] Implement database operations in server.py
- [ ] Add actual regex pattern matching for PO data extraction
- [ ] Implement extraction template system
- [ ] Add comprehensive error handling and validation

#### Medium Priority (Enhanced Features)
- [ ] Implement advanced line item extraction
- [ ] Add OCR support for scanned PDFs
- [ ] Implement vendor name normalization
- [ ] Add database migration system
- [ ] Create comprehensive test suite

#### Low Priority (Advanced Features)
- [ ] Add support for multiple PO formats
- [ ] Implement machine learning for pattern recognition
- [ ] Add web-based admin interface
- [ ] Create batch processing capabilities
- [ ] Add export functionality (Excel, CSV)

### Adding New Extraction Patterns

To add support for new PO formats:

1. **Add regex patterns** to `src/config.py`:
   ```python
   po_number_patterns = [
       r'PO[-\s]?Number:?\s*([A-Z0-9-]+)',
       r'Your new pattern here'
   ]
   ```

2. **Create extraction templates** in the database:
   ```python
   template = ExtractionTemplate(
       name="new_format",
       po_number_pattern=r'New PO pattern',
       vendor_pattern=r'New vendor pattern',
       priority=90
   )
   ```

3. **Test with sample PDFs** to validate extraction accuracy.

### Testing

```bash
# Run tests (when implemented)
pytest tests/

# Test individual components
python -m src.pdf_parser.parser  # Test PDF parsing
python -m src.config  # Test configuration
```

## Performance Considerations

- **PDF Size**: Limited to 50MB by default (configurable)
- **Parsing Timeout**: 120 seconds by default
- **Concurrent Parsing**: 3 concurrent parsers by default
- **Database**: SQLite with WAL mode for better concurrency
- **Memory**: Parser loads entire PDF into memory

## Troubleshooting

### Common Issues

1. **PDF Parsing Fails**:
   - Check if PDF is encrypted
   - Verify PDF is not corrupted
   - Try different parsing strategies

2. **Low Extraction Confidence**:
   - PDF may have non-standard format
   - Add custom extraction patterns
   - Consider OCR for scanned documents

3. **Database Errors**:
   - Check database file permissions
   - Verify SQLite version compatibility
   - Check disk space

### Debug Mode

Enable debug mode for detailed logging:
```bash
export PO_PARSER_DEBUG=True
python -m src.mcp_server.server
```

## Dependencies

Key dependencies include:

- **FastMCP**: MCP server framework
- **SQLAlchemy**: Database ORM
- **PyPDF2**: Basic PDF parsing
- **PDFPlumber**: Advanced PDF parsing
- **PyMuPDF**: Alternative PDF parsing
- **Pydantic**: Data validation
- **Loguru**: Enhanced logging
- **python-dotenv**: Environment variables

## License

[TODO: Add license information]

## Support

For questions or issues, please [TODO: Add contact information or issue tracker].

## Changelog

### v1.0.0 (Current)
- Initial project setup with comprehensive structure
- Database models for purchase order data
- PDF parser framework with multiple strategies
- FastMCP server with 6 PO management tools
- Configuration management system
- Sample data and documentation
- TODO comments for implementation roadmap
