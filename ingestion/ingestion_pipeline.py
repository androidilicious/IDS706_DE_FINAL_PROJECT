"""
ingestion_pipeline.py

Automated end-to-end data pipeline for Olist E-Commerce dataset.

Pipeline Stages:
    1. Extract: Download data from Kaggle API
    2. Load: Upload raw CSV files to AWS S3
    3. Transform: Create PostgreSQL schema (if not exists)
    4. Load: Load data from S3 to PostgreSQL with smart incremental updates

Features:
    - Idempotent operations (safe to run multiple times)
    - Smart skipping of unchanged data
    - Foreign key constraint handling
    - Progress tracking and detailed logging
    - Error handling with rollback

Usage:
    python ingestion_pipeline.py                    # Normal mode
    python ingestion_pipeline.py --force-schema     # Force schema recreation
"""

import os
import sys
from datetime import datetime

# Import pipeline components
from download_from_kaggle import download_kaggle_dataset
from upload_to_s3 import upload_directory_to_s3, BUCKET_NAME, LOCAL_DIR, S3_PREFIX
from create_schema import create_schema, check_tables_exist
from s3_to_rds import load_all_raw_tables


def log(message, level="INFO"):
    """Print formatted log message with timestamp and level.

    Args:
        message: Message to log
        level: Log level (INFO, SUCCESS, WARN, ERROR)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def run_ingestion_pipeline(force_schema_recreate=False):
    """
    Execute complete ingestion pipeline.

    Args:
        force_schema_recreate: If True, drop and recreate schema even if exists

    Returns:
        bool: True if pipeline succeeds, False otherwise
    """
    print("\n" + "=" * 70)
    print("AUTOMATED INGESTION PIPELINE")
    print("=" * 70)

    # Step 1: Download from Kaggle
    print("\n" + "-" * 70)
    log("STEP 1: Downloading data from Kaggle")
    print("-" * 70)

    if not download_kaggle_dataset():
        log("Failed to download from Kaggle", "ERROR")
        return False

    log("Kaggle download completed successfully", "SUCCESS")

    # Step 2: Upload to S3
    print("\n" + "-" * 70)
    log("STEP 2: Uploading data to S3")
    print("-" * 70)

    try:
        upload_directory_to_s3(LOCAL_DIR, BUCKET_NAME, S3_PREFIX)
        log("S3 upload completed successfully", "SUCCESS")
    except Exception as e:
        log(f"Failed to upload to S3: {e}", "ERROR")
        return False

    # Step 3: Check and create PostgreSQL schema
    print("\n" + "-" * 70)
    log("STEP 3: Checking PostgreSQL schema")
    print("-" * 70)

    exists, tables = check_tables_exist()

    if exists and not force_schema_recreate:
        log(f"Schema already exists with {len(tables)} tables", "INFO")
        log("Skipping schema creation (will replace data in existing tables)", "INFO")
    elif exists and force_schema_recreate:
        log("Forcing schema recreation...", "WARN")
        if not create_schema(force=True):
            log("Failed to recreate schema", "ERROR")
            return False
        log("Schema recreated successfully", "SUCCESS")
    else:
        log("No schema found. Creating new schema...", "INFO")
        if not create_schema(force=False):
            log("Failed to create schema", "ERROR")
            return False
        log("Schema created successfully", "SUCCESS")

    # Step 4: Load data from S3 to PostgreSQL
    print("\n" + "-" * 70)
    log("STEP 4: Loading data from S3 to PostgreSQL")
    print("-" * 70)

    log("Mode: REPLACE (truncating existing data)", "INFO")

    if not load_all_raw_tables(truncate=True):
        log("Failed to load data to PostgreSQL", "ERROR")
        return False

    log("Data load completed successfully", "SUCCESS")

    # Pipeline complete
    print("\n" + "=" * 70)
    log("PIPELINE COMPLETED SUCCESSFULLY!", "SUCCESS")
    print("=" * 70)

    # Summary
    print("\n📊 PIPELINE SUMMARY:")
    print("  ✓ Downloaded data from Kaggle")
    print(f"  ✓ Uploaded to S3: s3://{BUCKET_NAME}/{S3_PREFIX}")
    print(
        f"  ✓ Schema status: {'Recreated' if force_schema_recreate else 'Verified/Created'}"
    )
    print("  ✓ Data loaded to PostgreSQL (existing data replaced)")

    exists, tables = check_tables_exist()
    if exists:
        print(f"\n📋 TABLES IN DATABASE ({len(tables)}):")
        for table in tables:
            print(f"  - {table}")

    print("\n" + "=" * 70 + "\n")
    return True


def main():
    """Main entry point with command line argument support."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Automated ingestion pipeline: Kaggle → S3 → PostgreSQL"
    )
    parser.add_argument(
        "--force-schema-recreate",
        action="store_true",
        help="Force recreation of schema (drops existing tables)",
    )

    args = parser.parse_args()

    try:
        success = run_ingestion_pipeline(
            force_schema_recreate=args.force_schema_recreate
        )
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARN] Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed with unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
