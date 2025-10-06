"""
Database Migration Utilities

Provides utilities for creating, running, and managing database migrations
for the receipt processing system.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import text

from .database import engine, Base, create_tables, drop_tables
from .models import Receipt, ReceiptLineItem, ReceiptVendor


logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations."""

    def __init__(self):
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)

    def create_migration(self, name: str, description: str = "") -> str:
        """Create a new migration file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.sql"
        filepath = self.migrations_dir / filename

        migration_content = f"""-- Migration: {name}
-- Description: {description}
-- Created: {datetime.now().isoformat()}

-- Add your SQL statements here
-- Example:
-- ALTER TABLE receipts ADD COLUMN new_field VARCHAR(100);

-- Rollback statements (optional)
-- ALTER TABLE receipts DROP COLUMN new_field;
"""

        filepath.write_text(migration_content)
        logger.info(f"Created migration: {filepath}")
        return str(filepath)

    def run_migrations(self) -> bool:
        """Run all pending migrations."""
        try:
            # Create migration tracking table if it doesn't exist
            self._create_migration_table()

            # Get list of migration files
            migration_files = sorted(self.migrations_dir.glob("*.sql"))

            if not migration_files:
                logger.info("No migration files found")
                return True

            # Get already applied migrations
            applied_migrations = self._get_applied_migrations()

            # Run pending migrations
            for migration_file in migration_files:
                migration_name = migration_file.stem

                if migration_name not in applied_migrations:
                    logger.info(f"Applying migration: {migration_name}")

                    if self._apply_migration(migration_file):
                        self._record_migration(migration_name)
                        logger.info(f"Successfully applied: {migration_name}")
                    else:
                        logger.error(f"Failed to apply: {migration_name}")
                        return False

            logger.info("All migrations completed successfully")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def _create_migration_table(self):
        """Create the migration tracking table."""
        create_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_name VARCHAR(255) NOT NULL UNIQUE,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        with engine.connect() as connection:
            connection.execute(text(create_sql))
            connection.commit()

    def _get_applied_migrations(self) -> set:
        """Get list of already applied migrations."""
        try:
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT migration_name FROM schema_migrations")
                )
                return {row[0] for row in result}
        except Exception:
            return set()

    def _apply_migration(self, migration_file: Path) -> bool:
        """Apply a single migration file."""
        try:
            sql_content = migration_file.read_text()

            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

            with engine.connect() as connection:
                for statement in statements:
                    # Skip comments
                    if statement.startswith('--'):
                        continue

                    connection.execute(text(statement))

                connection.commit()

            return True

        except Exception as e:
            logger.error(f"Error applying migration {migration_file}: {e}")
            return False

    def _record_migration(self, migration_name: str):
        """Record that a migration has been applied."""
        with engine.connect() as connection:
            connection.execute(
                text("INSERT INTO schema_migrations (migration_name) VALUES (:name)"),
                {"name": migration_name}
            )
            connection.commit()


def init_database():
    """Initialize the database with all tables."""
    logger.info("Initializing database...")

    try:
        # Create all tables
        create_tables()
        logger.info("Database tables created successfully")

        # Insert initial data if needed
        _insert_initial_data()

        logger.info("Database initialization completed")
        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def reset_database():
    """Reset the database by dropping and recreating all tables."""
    logger.warning("Resetting database - all data will be lost!")

    try:
        drop_tables()
        create_tables()
        _insert_initial_data()

        logger.info("Database reset completed")
        return True

    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False


def _insert_initial_data():
    """Insert initial/seed data into the database."""
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check if we already have data
        existing_receipts = db.query(Receipt).count()
        if existing_receipts > 0:
            logger.info("Database already contains data, skipping seed data")
            return

        # Create sample vendor
        sample_vendor = ReceiptVendor(
            name="Demo Store",
            address="123 Main Street, Demo City, DC 12345",
            phone="555-123-4567",
            email="contact@demostore.com"
        )
        db.add(sample_vendor)
        db.flush()

        # Create sample receipt
        sample_receipt = Receipt(
            vendor_id=sample_vendor.id,
            date=datetime.now(),
            subtotal=25.00,
            tax_amount=2.00,
            total_amount=27.00,
            payment_method="credit_card",
            receipt_type="grocery",
            status="processed",
            confidence_score=0.95,
            is_business_expense=False
        )
        db.add(sample_receipt)
        db.flush()

        # Create sample line items
        line_items = [
            ReceiptLineItem(
                receipt_id=sample_receipt.receipt_id,
                line_number=1,
                description="Organic Bananas",
                quantity=2.5,
                unit_price=1.99,
                total_price=4.98,
                category="produce"
            ),
            ReceiptLineItem(
                receipt_id=sample_receipt.receipt_id,
                line_number=2,
                description="Whole Milk - 1 Gallon",
                quantity=1.0,
                unit_price=3.49,
                total_price=3.49,
                category="dairy"
            ),
            ReceiptLineItem(
                receipt_id=sample_receipt.receipt_id,
                line_number=3,
                description="Bread - Whole Wheat",
                quantity=1.0,
                unit_price=2.99,
                total_price=2.99,
                category="bakery"
            ),
            ReceiptLineItem(
                receipt_id=sample_receipt.receipt_id,
                line_number=4,
                description="Chicken Breast - 2 lbs",
                quantity=2.0,
                unit_price=6.99,
                total_price=13.98,
                category="meat"
            )
        ]

        for item in line_items:
            db.add(item)

        db.commit()
        logger.info("Sample data inserted successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to insert initial data: {e}")
        raise
    finally:
        db.close()


def backup_database(backup_path: str = None) -> str:
    """Create a backup of the database."""
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"receipts_backup_{timestamp}.db"

    # For SQLite, we can just copy the file
    database_url = os.getenv("DATABASE_URL", "sqlite:///./receipts.db")

    if database_url.startswith("sqlite"):
        import shutil
        source_path = database_url.replace("sqlite:///", "")
        shutil.copy2(source_path, backup_path)
        logger.info(f"Database backup created: {backup_path}")
        return backup_path
    else:
        # For other databases, would need database-specific backup commands
        raise NotImplementedError("Backup not implemented for non-SQLite databases")


def restore_database(backup_path: str) -> bool:
    """Restore database from backup."""
    try:
        database_url = os.getenv("DATABASE_URL", "sqlite:///./receipts.db")

        if database_url.startswith("sqlite"):
            import shutil
            target_path = database_url.replace("sqlite:///", "")
            shutil.copy2(backup_path, target_path)
            logger.info(f"Database restored from: {backup_path}")
            return True
        else:
            raise NotImplementedError("Restore not implemented for non-SQLite databases")

    except Exception as e:
        logger.error(f"Database restore failed: {e}")
        return False


# CLI commands for database management
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Database migration utilities")
    parser.add_argument("command", choices=["init", "reset", "migrate", "backup", "restore"])
    parser.add_argument("--backup-path", help="Path for backup file")
    parser.add_argument("--migration-name", help="Name for new migration")
    parser.add_argument("--migration-desc", help="Description for new migration")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.command == "init":
        success = init_database()
        sys.exit(0 if success else 1)

    elif args.command == "reset":
        success = reset_database()
        sys.exit(0 if success else 1)

    elif args.command == "migrate":
        manager = MigrationManager()
        if args.migration_name:
            manager.create_migration(args.migration_name, args.migration_desc or "")
        else:
            success = manager.run_migrations()
            sys.exit(0 if success else 1)

    elif args.command == "backup":
        backup_path = backup_database(args.backup_path)
        print(f"Backup created: {backup_path}")

    elif args.command == "restore":
        if not args.backup_path:
            print("--backup-path required for restore command")
            sys.exit(1)
        success = restore_database(args.backup_path)
        sys.exit(0 if success else 1)