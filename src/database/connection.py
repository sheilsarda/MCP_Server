"""
Database connection management for Purchase Order PDF Parser

Handles SQLite database connections, session management, and initialization.
"""

import os
import asyncio
from pathlib import Path
from typing import Generator, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from loguru import logger

from .models import Base, PurchaseOrder, PurchaseOrderItem, Vendor, ExtractionTemplate

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./purchase_orders.db")
DATABASE_PATH = Path("./purchase_orders.db")

# SQLite engine configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
)

# Session configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def enable_foreign_keys(dbapi_connection, connection_record):
    """Enable foreign key constraints for SQLite"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
    cursor.close()


# Enable foreign keys and performance optimizations
event.listen(engine, "connect", enable_foreign_keys)


def create_database():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create initial data
        with get_db_session() as db:
            create_initial_extraction_templates(db)
            
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session for FastAPI-style usage
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """Get a database session for direct usage"""
    return SessionLocal()


async def init_database():
    """Initialize the database asynchronously"""
    try:
        logger.info("Initializing purchase order database...")
        
        if not DATABASE_PATH.exists():
            logger.info("Database file not found, creating new database...")
            create_database()
        else:
            logger.info("Database file exists, verifying schema...")
            # TODO: Add schema migration logic if needed
            
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def create_initial_extraction_templates(db: Session):
    """Create initial extraction templates"""
    try:
        # Check if templates already exist
        existing_templates = db.query(ExtractionTemplate).count()
        if existing_templates > 0:
            logger.info("Extraction templates already exist, skipping creation")
            return
        
        # Create default extraction templates
        templates = [
            {
                "name": "standard_po_format",
                "description": "Standard purchase order format with labeled fields",
                "po_number_pattern": r"PO[-\s]?Number:?\s*([A-Z0-9-]+)",
                "vendor_pattern": r"Vendor:?\s*([A-Za-z\s&.,'-]+)",
                "date_pattern": r"Date:?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                "total_pattern": r"Total:?\s*\$?([0-9,]+\.?\d{0,2})",
                "item_pattern": r"Item:?\s*([A-Za-z\s\-&.,]+)",
                "is_active": True,
                "priority": 100
            },
            {
                "name": "invoice_style_format",
                "description": "Invoice-style format with different field arrangements",
                "po_number_pattern": r"Purchase\s+Order:?\s*([A-Z0-9-]+)",
                "vendor_pattern": r"Bill\s+To:?\s*([A-Za-z\s&.,'-]+)",
                "date_pattern": r"Order\s+Date:?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                "total_pattern": r"Grand\s+Total:?\s*\$?([0-9,]+\.?\d{0,2})",
                "item_pattern": r"Description:?\s*([A-Za-z\s\-&.,]+)",
                "is_active": True,
                "priority": 80
            },
            {
                "name": "generic_fallback",
                "description": "Generic fallback patterns for unrecognized formats",
                "po_number_pattern": r"([A-Z]{2,4}[-]?\d{3,6})",
                "vendor_pattern": r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|LLC|Corp|Co)\.?)?)",
                "date_pattern": r"(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                "total_pattern": r"\$?([0-9,]+\.?\d{0,2})",
                "item_pattern": r"([A-Za-z\s\-&.,]{10,})",
                "is_active": True,
                "priority": 10
            }
        ]
        
        for template_data in templates:
            template = ExtractionTemplate(**template_data)
            db.add(template)
        
        db.commit()
        logger.info(f"Created {len(templates)} initial extraction templates")
        
    except Exception as e:
        logger.error(f"Error creating initial extraction templates: {e}")
        db.rollback()
        raise


# Database utility functions
def get_purchase_order_by_po_number(db: Session, po_number: str) -> Optional[PurchaseOrder]:
    """Get purchase order by PO number"""
    return db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()


def get_purchase_orders_by_vendor(db: Session, vendor: str, limit: int = 100) -> list[PurchaseOrder]:
    """Get purchase orders by vendor"""
    return db.query(PurchaseOrder).filter(PurchaseOrder.vendor.ilike(f"%{vendor}%")).limit(limit).all()


def get_purchase_orders_by_date_range(db: Session, start_date: datetime, end_date: datetime) -> list[PurchaseOrder]:
    """Get purchase orders within date range"""
    return db.query(PurchaseOrder).filter(
        PurchaseOrder.date >= start_date,
        PurchaseOrder.date <= end_date
    ).all()


def search_purchase_orders(db: Session, query: str, limit: int = 50) -> list[PurchaseOrder]:
    """Search purchase orders by various fields"""
    search_term = f"%{query}%"
    return db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number.ilike(search_term) |
        PurchaseOrder.vendor.ilike(search_term) |
        PurchaseOrder.pdf_filename.ilike(search_term)
    ).limit(limit).all()


def get_vendor_by_name(db: Session, name: str) -> Optional[Vendor]:
    """Get or create vendor by name"""
    vendor = db.query(Vendor).filter(Vendor.name == name).first()
    if not vendor:
        # Create new vendor
        from .models import normalize_vendor_name
        vendor = Vendor(
            name=name,
            normalized_name=normalize_vendor_name(name)
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
    return vendor


def update_vendor_statistics(db: Session, vendor_name: str, order_amount: float):
    """Update vendor statistics when new order is added"""
    vendor = get_vendor_by_name(db, vendor_name)
    if vendor:
        vendor.total_orders += 1
        vendor.total_amount += order_amount
        db.commit()


def get_extraction_templates(db: Session, active_only: bool = True) -> list[ExtractionTemplate]:
    """Get extraction templates, ordered by priority"""
    query = db.query(ExtractionTemplate)
    if active_only:
        query = query.filter(ExtractionTemplate.is_active == True)
    return query.order_by(ExtractionTemplate.priority.desc()).all()


def get_database_statistics(db: Session) -> Dict[str, Any]:
    """Get database statistics"""
    try:
        stats = {
            "total_purchase_orders": db.query(PurchaseOrder).count(),
            "total_line_items": db.query(PurchaseOrderItem).count(),
            "total_vendors": db.query(Vendor).count(),
            "extraction_templates": db.query(ExtractionTemplate).count(),
            "latest_po_date": db.query(PurchaseOrder.date).order_by(PurchaseOrder.date.desc()).first(),
            "database_size": DATABASE_PATH.stat().st_size if DATABASE_PATH.exists() else 0
        }
        
        # Get top vendors
        top_vendors = db.query(Vendor).order_by(Vendor.total_amount.desc()).limit(5).all()
        stats["top_vendors"] = [{"name": v.name, "total_orders": v.total_orders, "total_amount": float(v.total_amount)} for v in top_vendors]
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting database statistics: {e}")
        return {}


def backup_database(backup_path: Optional[str] = None):
    """Create a backup of the database"""
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"./backups/po_database_backup_{timestamp}.db"
    
    try:
        # Create backup directory
        backup_path_obj = Path(backup_path)
        backup_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy database file
        import shutil
        shutil.copy2(DATABASE_PATH, backup_path)
        
        logger.info(f"Database backup created: {backup_path}")
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        raise


def optimize_database():
    """Optimize database performance"""
    try:
        with get_db_session() as db:
            # SQLite optimization commands
            db.execute(text("VACUUM"))
            db.execute(text("ANALYZE"))
            db.commit()
        
        logger.info("Database optimization completed")
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise


def check_database_health() -> bool:
    """Check database health and integrity"""
    try:
        with get_db_session() as db:
            # Check database connection
            result = db.execute(text("SELECT 1")).scalar()
            if result != 1:
                return False
            
            # Check integrity
            integrity_result = db.execute(text("PRAGMA integrity_check")).scalar()
            if integrity_result != "ok":
                logger.error(f"Database integrity check failed: {integrity_result}")
                return False
            
            # Check if tables exist
            tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            expected_tables = {"purchase_orders", "purchase_order_items", "vendors", "extraction_templates"}
            existing_tables = {table[0] for table in tables}
            
            if not expected_tables.issubset(existing_tables):
                missing_tables = expected_tables - existing_tables
                logger.error(f"Missing database tables: {missing_tables}")
                return False
            
        logger.info("Database health check passed")
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Context manager for database sessions
class DatabaseManager:
    """Context manager for database operations"""
    
    def __init__(self):
        self.db = None
    
    def __enter__(self) -> Session:
        self.db = get_db_session()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            if exc_type is not None:
                self.db.rollback()
            else:
                self.db.commit()
            self.db.close()


# Usage example:
# with DatabaseManager() as db:
#     po = get_purchase_order_by_po_number(db, "PO-1003")
#     print(po) 