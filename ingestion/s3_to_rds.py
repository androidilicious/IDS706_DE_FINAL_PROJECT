"""
s3_to_rds.py

S3 to PostgreSQL data loader with smart incremental updates.

Reads raw CSV files from AWS S3 and loads them into PostgreSQL tables.

Features:
    - Smart incremental loading (skips unchanged tables)
    - Foreign key constraint handling (proper load order)
    - Duplicate detection with ON CONFLICT
    - NaN value handling (converts to None)
    - Progress tracking for large datasets
    - Row count validation

Configuration:
    - S3 Bucket: de-27-team3/raw/
    - Target: PostgreSQL (schema_raw.sql)
    - Load Order: Parent tables → Child tables (respects FK constraints)
"""

import os
import tempfile
import boto3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ========= AWS CREDENTIALS =========
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
# ===================================

# ========= S3 CONFIG =========
S3_BUCKET = os.getenv("S3_BUCKET", "de-27-team3")
S3_PREFIX = os.getenv("S3_PREFIX", "raw/")
S3_REGION = os.getenv("S3_REGION", "us-east-2")
# =============================

# ========= RDS CONFIG (Aiven PostgreSQL) =========
RDS_HOST = os.getenv("DB_HOST")
RDS_PORT = int(os.getenv("DB_PORT", 22446))
RDS_DB = os.getenv("DB_NAME")
RDS_USER = os.getenv("DB_USER")
RDS_PWD = os.getenv("DB_PASSWORD")
# ============================================

# ========= TABLE MAPPING =========
# Maps S3 CSV filenames to PostgreSQL table names
CSV_TABLE_MAP = {
    "olist_customers_dataset.csv": "customers_raw",
    "olist_geolocation_dataset.csv": "geolocation_raw",
    "olist_order_items_dataset.csv": "order_items_raw",
    "olist_order_payments_dataset.csv": "order_payments_raw",
    "olist_order_reviews_dataset.csv": "order_reviews_raw",
    "olist_orders_dataset.csv": "orders_raw",
    "olist_products_dataset.csv": "products_raw",
    "olist_sellers_dataset.csv": "sellers_raw",
    "product_category_name_translation.csv": "product_category_name_translation_raw",
}

# ========= LOAD ORDER (CRITICAL FOR FOREIGN KEYS) =========
# Parent tables MUST be loaded before child tables to satisfy FK constraints
#
# Dependency Graph:
#   customers_raw ──┐
#   sellers_raw ──┐ │
#   products_raw ─┤ ├──> orders_raw ──┬──> order_items_raw
#                 │ │                  ├──> order_payments_raw
#                 │ │                  └──> order_reviews_raw
#                 └─┘
LOAD_ORDER = [
    # Stage 1: Independent tables (no foreign keys)
    "olist_customers_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_geolocation_dataset.csv",
    "product_category_name_translation.csv",
    # Stage 2: Orders (depends on customers)
    "olist_orders_dataset.csv",
    # Stage 3: Order-related tables (depend on orders, products, sellers)
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
]


def get_s3_client():
    """Create a boto3 S3 client with credentials."""
    return boto3.client(
        "s3",
        region_name=S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def list_raw_csv_keys(s3_client):
    """
    List all CSV object keys under the raw/ prefix in the bucket.
    Returns a list of keys like 'raw/olist_customers_dataset.csv'.
    """
    keys = []
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".csv"):
                keys.append(key)
    return keys


def download_key_to_temp(s3_client, key, tmp_dir):
    """
    Download a single S3 object key into a temp directory.
    Returns the local file path.
    """
    filename = os.path.basename(key)
    local_path = os.path.join(tmp_dir, filename)

    # Get file size
    response = s3_client.head_object(Bucket=S3_BUCKET, Key=key)
    file_size_mb = response["ContentLength"] / (1024 * 1024)

    print(f"[INFO] Downloading {filename} ({file_size_mb:.2f} MB) from S3...")
    s3_client.download_file(S3_BUCKET, key, local_path)
    print(f"[INFO] Download complete: {filename}")

    return local_path


def get_rds_connection():
    """
    Create a psycopg2 connection to the Aiven PostgreSQL instance.
    """
    conn = psycopg2.connect(
        host=RDS_HOST,
        port=RDS_PORT,
        dbname=RDS_DB,
        user=RDS_USER,
        password=RDS_PWD,
        sslmode="require",
    )
    conn.autocommit = True
    return conn


def table_exists(table_name, conn):
    """
    Check if a table exists in the database.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
        """,
            (table_name,),
        )
        return cur.fetchone()[0]


def get_table_row_count(table_name, conn):
    """
    Get the number of rows in a table.
    """
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cur.fetchone()[0]


def check_data_match(csv_path, table_name, conn):
    """
    Check if CSV data matches database data.
    Returns True if they match (no need to reload), False otherwise.
    """
    try:
        # Get CSV row count
        df = pd.read_csv(csv_path)
        csv_rows = len(df)

        # Get database row count
        db_rows = get_table_row_count(table_name, conn)

        # If row counts don't match, data is different
        if csv_rows != db_rows:
            return False, csv_rows, db_rows

        # Row counts match - data is likely the same
        return True, csv_rows, db_rows

    except Exception as e:
        print(f"[WARN] Could not compare data: {e}")
        return False, 0, 0


def load_csv_into_table(csv_path, table_name, conn, truncate=True):
    """
    Load a local CSV file into a given raw table.

    Args:
        csv_path: Path to CSV file
        table_name: Target table name
        conn: Database connection
        truncate: If True, truncate table before inserting (replace mode)
    """
    print(f"[INFO] Reading CSV: {os.path.basename(csv_path)}...")
    df = pd.read_csv(csv_path)

    if df.empty:
        print(f"[WARN] {csv_path} is empty, skipping.")
        return

    total_rows = len(df)
    print(f"[INFO] Found {total_rows:,} rows to load")

    # Replace NaN with None for proper NULL handling
    df = df.where(pd.notna(df), None)

    cols = list(df.columns)
    col_list_sql = ",".join(cols)

    # Build a list of tuples for execute_values
    print(f"[INFO] Preparing data for insertion...")
    records = [tuple(row[col] for col in cols) for _, row in df.iterrows()]

    with conn.cursor() as cur:
        # Truncate table before load to replace existing data
        if truncate:
            print(f"[INFO] Truncating table {table_name}...")
            cur.execute(f"TRUNCATE TABLE {table_name} CASCADE;")

        print(f"[INFO] Inserting {total_rows:,} rows into {table_name}...")
        insert_sql = f"INSERT INTO {table_name} ({col_list_sql}) VALUES %s ON CONFLICT DO NOTHING"
        execute_values(cur, insert_sql, records, page_size=1000)
        print(f"[INFO] Insert complete!")

    print(
        f"[SUCCESS] ✓ Loaded {total_rows:,} rows from {os.path.basename(csv_path)} into {table_name}.\n"
    )


def load_all_raw_tables(truncate=True):
    """
    High-level function:
    - list CSVs under raw/ in S3
    - download each to a temp dir
    - load into the corresponding raw table in RDS

    Args:
        truncate: If True, truncate tables before loading (replace mode)
    """
    s3 = get_s3_client()
    keys = list_raw_csv_keys(s3)

    if not keys:
        print("[WARN] No CSV objects found under raw/ in S3.")
        return False

    # Create a map of filename to S3 key
    key_map = {os.path.basename(k): k for k in keys}

    # Filter to only files we can process
    files_to_process = [f for f in LOAD_ORDER if f in key_map]
    total_files = len(files_to_process)
    print(f"\n[INFO] Found {total_files} CSV files to process (in dependency order)\n")

    # Temporary local directory to hold downloads
    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f"[INFO] Using temp directory: {tmp_dir}")
        conn = get_rds_connection()

        try:
            # Process files in the correct order
            for idx, filename in enumerate(files_to_process, 1):
                key = key_map[filename]
                table_name = CSV_TABLE_MAP[filename]

                print("=" * 70)
                print(f"[{idx}/{total_files}] Processing: {filename}")
                print(f"Target table: {table_name}")
                print("=" * 70)

                # Check if table exists
                if not table_exists(table_name, conn):
                    print(
                        f"[ERROR] Table {table_name} does not exist. Run create_schema.py first."
                    )
                    return False

                local_path = download_key_to_temp(s3, key, tmp_dir)

                # Check if data already matches
                print(f"[INFO] Checking if data needs updating...")
                matches, csv_rows, db_rows = check_data_match(
                    local_path, table_name, conn
                )

                if matches:
                    print(
                        f"[SKIP] ✓ Data already up-to-date ({csv_rows:,} rows) - skipping load\n"
                    )
                    continue
                else:
                    if db_rows > 0:
                        print(
                            f"[INFO] Data differs (CSV: {csv_rows:,} rows, DB: {db_rows:,} rows) - updating..."
                        )
                    else:
                        print(f"[INFO] Table empty - loading {csv_rows:,} rows...")

                load_csv_into_table(local_path, table_name, conn, truncate=truncate)

            print("\n" + "=" * 70)
            print(f"[SUCCESS] ✓ Pipeline completed successfully!")
            print("=" * 70 + "\n")
            return True

        except Exception as e:
            print(f"\n[ERROR] Failed to load tables: {e}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            conn.close()
            print("[INFO] Database connection closed.")


if __name__ == "__main__":
    # Entry point for running this script standalone
    print("Starting S3 -> RDS raw ingestion...")
    load_all_raw_tables()
    print("Done.")
