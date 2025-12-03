"""
create_schema.py

PostgreSQL schema management for raw tables.

Creates database tables from schema_raw.sql DDL script.

Features:
    - Smart schema detection (checks if tables exist)
    - Optional force recreation (drops existing tables)
    - Transaction-based execution
    - Error handling and rollback

Usage:
    from create_schema import create_schema, check_tables_exist
    
    exists, tables = check_tables_exist()
    if not exists:
        create_schema()
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ========= POSTGRESQL CONFIG =========
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT', 22446))
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
# ====================================

def check_tables_exist():
    """
    Check if tables already exist in the database.
    Returns: (exists, table_list)
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            sslmode='require'
        )
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%_raw'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
        
        conn.close()
        return len(tables) > 0, tables
        
    except Exception as e:
        print(f"[ERROR] Failed to check tables: {e}")
        return False, []


def create_schema(force=False):
    """
    Read schema_raw.sql and execute it to create tables.
    
    Args:
        force: If True, drop existing tables before creating
    """
    print("[INFO] Connecting to PostgreSQL database...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode='require'
    )
    conn.autocommit = True
    
    try:
        # Check if tables exist
        exists, tables = check_tables_exist()
        
        if exists and not force:
            print(f"[INFO] Found {len(tables)} existing tables:")
            for table in tables:
                print(f"  - {table}")
            print("[INFO] Skipping schema creation (tables already exist)")
            return True
        
        if exists and force:
            print(f"[WARN] Dropping {len(tables)} existing tables...")
            with conn.cursor() as cur:
                cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
            print("[INFO] Dropped existing schema")
        
        # Read the SQL schema file
        schema_file = os.path.join(os.path.dirname(__file__), 'schema_raw.sql')
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute the schema
        with conn.cursor() as cur:
            print("[INFO] Creating tables...")
            cur.execute(schema_sql)
            print("[SUCCESS] Schema created successfully!")
        
        return True
            
    except Exception as e:
        print(f"[ERROR] Failed to create schema: {e}")
        return False
    finally:
        conn.close()
        print("[INFO] Database connection closed.")

if __name__ == "__main__":
    create_schema()
