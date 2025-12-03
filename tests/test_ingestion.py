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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ingestion'))

from test_connections import test_s3_connection, test_postgres_connection
from create_schema import check_tables_exist
from s3_to_rds import get_s3_client, get_rds_connection


class TestConnections(unittest.TestCase):
    """Test external connections."""
    
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
        """Test that all required tables exist."""
        exists, tables = check_tables_exist()
        self.assertTrue(exists, "No tables found in database")
        self.assertEqual(len(tables), 9, f"Expected 9 tables, found {len(tables)}")
    
    def test_required_tables(self):
        """Test that specific tables exist."""
        exists, tables = check_tables_exist()
        required = [
            'customers_raw', 'orders_raw', 'order_items_raw',
            'sellers_raw', 'products_raw'
        ]
        for table in required:
            self.assertIn(table, tables, f"Table {table} not found")


class TestDataLoad(unittest.TestCase):
    """Test data loading functions."""
    
    def test_s3_client_creation(self):
        """Test S3 client instantiation."""
        client = get_s3_client()
        self.assertIsNotNone(client, "S3 client is None")
    
    def test_rds_connection_creation(self):
        """Test PostgreSQL connection."""
        conn = get_rds_connection()
        self.assertIsNotNone(conn, "PostgreSQL connection is None")
        conn.close()


if __name__ == '__main__':
    # Load environment
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    # Run tests
    unittest.main(verbosity=2)
