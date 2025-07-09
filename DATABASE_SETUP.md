# 🗄️ Database Configuration Guide

This document explains the centralized database configuration for the Business Document PDF Parser project.

## 📍 **Canonical Database Location**

**Single Source of Truth:** `/home/sheil/MCP_Server/data/business_documents.db`

All components (scripts, workflows, MCP server) now use this centralized location.

## 🔧 **Configuration System**

### **1. Centralized Config (`src/config.py`)**
```python
# Default database location
PROJECT_ROOT/data/business_documents.db

# Environment variable override
BUSINESS_DOCS_DB_PATH=/custom/path/to/database.db
```

### **2. Priority Order**
1. **Environment Variable:** `BUSINESS_DOCS_DB_PATH` (if set)
2. **Default:** `{PROJECT_ROOT}/data/business_documents.db`

### **3. Directory Structure**
```
MCP_Server/
├── data/                          # ✅ Database storage
│   └── business_documents.db      # ✅ Single canonical database
├── logs/                          # ✅ Log files
├── src/                           # ✅ Source code
│   ├── config.py                  # ✅ Centralized configuration
│   └── database/
│       └── connection.py          # ✅ Uses centralized config
├── scripts/                       # ✅ No more local databases
├── sample_data/                   # ✅ PDF samples
└── business_documents.db          # ❌ REMOVED (was duplicate)
```

## 🚀 **Usage Examples**

### **Default Usage (Recommended)**
```python
# All components automatically use the canonical location
from database.queries import search_business_documents

results = search_business_documents("Apex")  # Uses canonical DB
```

### **Custom Database Path**
```bash
# Set environment variable for custom location
export BUSINESS_DOCS_DB_PATH="/path/to/custom/database.db"

# Or set it programmatically
import os
os.environ['BUSINESS_DOCS_DB_PATH'] = '/custom/path/database.db'
```

### **Testing Configuration**
```python
# Check current configuration
python3 -c "import sys; sys.path.insert(0, 'src'); from config import print_config_summary; print_config_summary()"
```

## 🔧 **MCP Server Configuration**

### **Option 1: Environment Variable (Recommended)**
```bash
# Set environment variable before starting MCP server
export BUSINESS_DOCS_DB_PATH="/home/sheil/MCP_Server/data/business_documents.db"

# Start MCP server
python -m src.mcp_server.server
```

### **Option 2: Symlink (Alternative)**
```bash
# Create symlink in Claude's directory
ln -sf /home/sheil/MCP_Server/data/business_documents.db /usr/lib/claude-desktop/business_documents.db
```

### **Option 3: Copy (Simple but needs maintenance)**
```bash
# Copy database to Claude's directory (when database is updated)
cp /home/sheil/MCP_Server/data/business_documents.db /usr/lib/claude-desktop/business_documents.db
```

## 📋 **Migration Checklist**

- [x] ✅ Created centralized config system (`src/config.py`)
- [x] ✅ Updated database connection (`src/database/connection.py`)
- [x] ✅ Created canonical database location (`data/business_documents.db`)
- [x] ✅ Moved existing data to canonical location
- [x] ✅ Removed duplicate database files
- [x] ✅ Tested configuration with search functionality

## 🛠️ **For Developers**

### **Adding New Scripts**
```python
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# This automatically uses the canonical database location
from database.queries import search_business_documents
```

### **Environment Variables**
```bash
# Available environment variables:
BUSINESS_DOCS_DB_PATH          # Database path override
PO_PARSER_DEBUG               # Enable debug mode
PO_PARSER_MAX_PDF_SIZE        # Max PDF file size
PO_PARSER_PARSING_TIMEOUT     # PDF parsing timeout
```

## 🔍 **Troubleshooting**

### **Check Database Location**
```bash
python3 -c "import sys; sys.path.insert(0, 'src'); from config import DATABASE_PATH; print(f'Database: {DATABASE_PATH}')"
```

### **Verify Data Exists**
```bash
python3 scripts/query_database.py | head -20
```

### **Test Search Function**
```bash
python3 -c "
import sys; 
sys.path.insert(0, 'src'); 
from database.queries import search_business_documents; 
results = search_business_documents('Apex'); 
print(f'Found {len(results)} Apex documents')
"
```

## 🎯 **Benefits of This Approach**

1. **🎯 Single Source of Truth** - One canonical database location
2. **🔧 Environment Configurable** - Easy to override for different environments  
3. **📁 Organized Structure** - Clean separation of data, logs, and code
4. **🚀 No More Duplicates** - Eliminates confusion from multiple database files
5. **🔄 Easy Maintenance** - All components automatically use the correct location
6. **🧪 Testing Friendly** - Easy to switch databases for testing 