"""
run_s3_to_postgres.py

Simplified S3 → PostgreSQL loader (skips Kaggle download and S3 upload).

Use this when:
    - Data is already in S3
    - You want to reload database without re-downloading
    - Testing database load performance

Features:
    - Auto schema creation if needed
    - Smart incremental updates
    - Skips unchanged tables
    - Progress tracking
"""

from create_schema import create_schema, check_tables_exist
from s3_to_rds import load_all_raw_tables

def main():
    print("=" * 60)
    print("S3 -> PostgreSQL Data Load")
    print("=" * 60)
    
    print("\nStep 1: Checking PostgreSQL Schema...")
    exists, tables = check_tables_exist()
    
    if exists:
        print(f"[INFO] Found {len(tables)} existing tables")
        print("[INFO] Will replace data in existing tables")
    else:
        print("[INFO] No schema found. Creating new schema...")
        if not create_schema():
            print("[ERROR] Failed to create schema. Exiting.")
            return
    
    print("\nStep 2: Loading data from S3 to PostgreSQL...")
    if load_all_raw_tables(truncate=True):
        print("\n" + "=" * 60)
        print("DATA LOAD COMPLETED SUCCESSFULLY!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("DATA LOAD FAILED!")
        print("=" * 60)

if __name__ == "__main__":
    main()
