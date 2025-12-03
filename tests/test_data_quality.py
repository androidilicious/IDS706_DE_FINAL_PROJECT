"""
test_data_quality.py

Data quality tests for Olist pipeline.

Tests:
    - Row count validation
    - NULL value checks
    - Foreign key integrity
    - Data range validation
    - Duplicate detection
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 22446)),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'sslmode': 'require'
}


class DataQualityTester:
    """Data quality testing suite."""
    
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def run_query(self, query):
        """Execute query and return result."""
        with self.conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
    
    def test_row_counts(self):
        """Test: All tables have data."""
        print("\n📊 Test 1: Row Count Validation")
        print("-" * 60)
        
        tables = [
            'customers_raw', 'sellers_raw', 'products_raw',
            'orders_raw', 'order_items_raw', 'order_payments_raw',
            'order_reviews_raw', 'geolocation_raw',
            'product_category_name_translation_raw'
        ]
        
        for table in tables:
            count = self.run_query(f"SELECT COUNT(*) FROM {table}")[0][0]
            if count > 0:
                print(f"  ✓ {table}: {count:,} rows")
                self.passed += 1
            else:
                print(f"  ✗ {table}: EMPTY TABLE")
                self.failed += 1
    
    def test_null_values(self):
        """Test: Critical columns have no NULLs."""
        print("\n🔍 Test 2: NULL Value Checks")
        print("-" * 60)
        
        tests = [
            ("customers_raw", "customer_id"),
            ("orders_raw", "order_id"),
            ("orders_raw", "customer_id"),
            ("order_items_raw", "order_id"),
            ("order_items_raw", "product_id"),
            ("products_raw", "product_id"),
            ("sellers_raw", "seller_id"),
        ]
        
        for table, column in tests:
            null_count = self.run_query(
                f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL"
            )[0][0]
            
            if null_count == 0:
                print(f"  ✓ {table}.{column}: No NULLs")
                self.passed += 1
            else:
                print(f"  ✗ {table}.{column}: {null_count} NULL values")
                self.failed += 1
    
    def test_foreign_keys(self):
        """Test: Foreign key integrity."""
        print("\n🔗 Test 3: Foreign Key Integrity")
        print("-" * 60)
        
        # Test: orders.customer_id → customers.customer_id
        orphans = self.run_query("""
            SELECT COUNT(*) FROM orders_raw o
            LEFT JOIN customers_raw c ON o.customer_id = c.customer_id
            WHERE c.customer_id IS NULL
        """)[0][0]
        
        if orphans == 0:
            print(f"  ✓ orders → customers: All valid")
            self.passed += 1
        else:
            print(f"  ✗ orders → customers: {orphans} orphaned records")
            self.failed += 1
        
        # Test: order_items.order_id → orders.order_id
        orphans = self.run_query("""
            SELECT COUNT(*) FROM order_items_raw oi
            LEFT JOIN orders_raw o ON oi.order_id = o.order_id
            WHERE o.order_id IS NULL
        """)[0][0]
        
        if orphans == 0:
            print(f"  ✓ order_items → orders: All valid")
            self.passed += 1
        else:
            print(f"  ✗ order_items → orders: {orphans} orphaned records")
            self.failed += 1
    
    def test_data_ranges(self):
        """Test: Data values in valid ranges."""
        print("\n📏 Test 4: Data Range Validation")
        print("-" * 60)
        
        # Test: Review scores 1-5
        invalid = self.run_query("""
            SELECT COUNT(*) FROM order_reviews_raw
            WHERE review_score NOT BETWEEN 1 AND 5
        """)[0][0]
        
        if invalid == 0:
            print(f"  ✓ Review scores: All in range [1-5]")
            self.passed += 1
        else:
            print(f"  ⚠ Review scores: {invalid} out of range")
            self.warnings += 1
        
        # Test: Positive prices
        invalid = self.run_query("""
            SELECT COUNT(*) FROM order_items_raw
            WHERE price < 0
        """)[0][0]
        
        if invalid == 0:
            print(f"  ✓ Order prices: All positive")
            self.passed += 1
        else:
            print(f"  ✗ Order prices: {invalid} negative values")
            self.failed += 1
    
    def test_duplicates(self):
        """Test: No duplicate primary keys."""
        print("\n🔑 Test 5: Duplicate Detection")
        print("-" * 60)
        
        tests = [
            ("customers_raw", "customer_id"),
            ("sellers_raw", "seller_id"),
            ("products_raw", "product_id"),
            ("orders_raw", "order_id"),
        ]
        
        for table, pk in tests:
            duplicates = self.run_query(f"""
                SELECT COUNT(*) - COUNT(DISTINCT {pk}) FROM {table}
            """)[0][0]
            
            if duplicates == 0:
                print(f"  ✓ {table}.{pk}: No duplicates")
                self.passed += 1
            else:
                print(f"  ✗ {table}.{pk}: {duplicates} duplicates")
                self.failed += 1
    
    def test_date_consistency(self):
        """Test: Date logic validation."""
        print("\n📅 Test 6: Date Consistency")
        print("-" * 60)
        
        # Test: Delivery date after purchase date
        invalid = self.run_query("""
            SELECT COUNT(*) FROM orders_raw
            WHERE order_delivered_customer_date < order_purchase_timestamp
        """)[0][0]
        
        if invalid == 0:
            print(f"  ✓ Delivery dates: All after purchase")
            self.passed += 1
        else:
            print(f"  ✗ Delivery dates: {invalid} before purchase")
            self.failed += 1
    
    def run_all_tests(self):
        """Run complete test suite."""
        print("\n" + "="*70)
        print("DATA QUALITY TEST SUITE")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.test_row_counts()
        self.test_null_values()
        self.test_foreign_keys()
        self.test_data_ranges()
        self.test_duplicates()
        self.test_date_consistency()
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"✓ Passed: {self.passed}")
        print(f"✗ Failed: {self.failed}")
        print(f"⚠ Warnings: {self.warnings}")
        print(f"Total: {self.passed + self.failed + self.warnings}")
        
        success_rate = (self.passed / (self.passed + self.failed)) * 100 if (self.passed + self.failed) > 0 else 0
        print(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        self.conn.close()
        
        if self.failed > 0:
            print("\n❌ TESTS FAILED")
            sys.exit(1)
        else:
            print("\n✅ ALL TESTS PASSED")
            sys.exit(0)


if __name__ == "__main__":
    tester = DataQualityTester()
    tester.run_all_tests()
