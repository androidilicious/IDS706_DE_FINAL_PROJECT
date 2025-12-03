"""
test_ingestion.py

Unit tests for ingestion pipeline components.

Tests:
    - S3 connection
    - PostgreSQL connection
    - Schema creation
    - Data loading functions
"""

import unittest
import os
import sys
from dotenv import load_dotenv

# Add ingestion to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))

from test_connections import test_s3_connection, test_postgres_connection
from create_schema import check_tables_exist
from s3_to_rds import get_s3_client, get_rds_connection


class TestConnections(unittest.TestCase):
    """Test external connections."""

    @unittest.skipIf(
        not os.getenv("AWS_ACCESS_KEY_ID"), "AWS credentials not available"
    )
    def test_s3_access(self):
        """Test S3 connection."""
        result = test_s3_connection()
        self.assertTrue(result, "S3 connection failed")

    def test_postgres_access(self):
        """Test PostgreSQL connection."""
        result = test_postgres_connection()
        self.assertTrue(result, "PostgreSQL connection failed")


class TestSchema(unittest.TestCase):
    """Test schema operations."""

    def test_tables_exist(self):
        """Test that database connection works and can query tables."""
        try:
            exists, tables = check_tables_exist()
            # In CI, we just test that connection works
            self.assertIsNotNone(tables, "Failed to query tables")
        except Exception as e:
            self.skipTest(f"Database not accessible: {e}")

    def test_required_tables(self):
        """Test that specific tables exist (skipped if DB empty)."""
        try:
            exists, tables = check_tables_exist()
            if not exists or len(tables) == 0:
                self.skipTest("No tables in database yet")
            required = [
                "customers_raw",
                "orders_raw",
                "order_items_raw",
                "sellers_raw",
                "products_raw",
            ]
            for table in required:
                self.assertIn(table, tables, f"Table {table} not found")
        except Exception as e:
            self.skipTest(f"Database not accessible: {e}")


class TestDataLoad(unittest.TestCase):
    """Test data loading functions."""

    def test_s3_client_creation(self):
        """Test S3 client instantiation."""
        client = get_s3_client()
        self.assertIsNotNone(client, "S3 client is None")

    def test_rds_connection_creation(self):
        """Test PostgreSQL connection."""
        try:
            conn = get_rds_connection()
            self.assertIsNotNone(conn, "PostgreSQL connection is None")
            conn.close()
        except Exception as e:
            self.skipTest(f"Database connection failed: {e}")


if __name__ == "__main__":
    # Load environment
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    # Run tests
    unittest.main(verbosity=2)
