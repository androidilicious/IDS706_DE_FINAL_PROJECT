"""
test_connections.py

Connection validator for AWS S3 and PostgreSQL.

Tests connectivity to data sources before running pipeline.

Features:
    - S3 bucket access validation
    - PostgreSQL connection testing
    - List existing tables in database
    - Display data statistics
    - Verify credentials

Usage:
    python test_connections.py
"""

import os
import boto3
import psycopg2
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ========= AWS CREDENTIALS =========
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET = os.getenv("S3_BUCKET", "de-27-team3")
S3_REGION = os.getenv("S3_REGION", "us-east-2")
# ===================================

# ========= POSTGRESQL CONFIG =========
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 22446))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
# ====================================


def test_s3_connection():
    """Test S3 connection and list objects in bucket."""
    print("\n" + "=" * 60)
    print("Testing S3 Connection...")
    print("=" * 60)

    try:
        s3 = boto3.client(
            "s3",
            region_name=S3_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        # List objects in the raw/ prefix
        print(f"\nListing objects in s3://{S3_BUCKET}/raw/...")
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="raw/", MaxKeys=10)

        if "Contents" in response:
            print(f"✓ Found {len(response['Contents'])} objects:")
            for obj in response["Contents"]:
                size_mb = obj["Size"] / (1024 * 1024)
                print(f"  - {obj['Key']} ({size_mb:.2f} MB)")
            print("\n✓ S3 Connection Successful!")
            return True
        else:
            print("✗ No objects found in raw/ prefix")
            print("  You may need to upload data first using upload_to_s3.py")
            return False

    except ClientError as e:
        print(f"✗ S3 Connection Failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_postgres_connection():
    """Test PostgreSQL connection."""
    print("\n" + "=" * 60)
    print("Testing PostgreSQL Connection...")
    print("=" * 60)

    try:
        print(f"\nConnecting to {DB_HOST}:{DB_PORT}/{DB_NAME}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            sslmode="require",
        )

        # Test query
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"✓ Connected successfully!")
            print(f"  PostgreSQL version: {version[:50]}...")

            # Check if any tables exist
            cur.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%_raw'
            """
            )
            tables = cur.fetchall()

            if tables:
                print(f"\n✓ Found {len(tables)} existing raw tables:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\n⚠ No raw tables found yet")
                print("  Run create_schema.py to create tables")

        conn.close()
        print("\n✓ PostgreSQL Connection Successful!")
        return True

    except Exception as e:
        print(f"✗ PostgreSQL Connection Failed: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("CONNECTION TEST SUITE")
    print("=" * 60)

    s3_ok = test_s3_connection()
    pg_ok = test_postgres_connection()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"S3 Connection:        {'✓ PASS' if s3_ok else '✗ FAIL'}")
    print(f"PostgreSQL Connection: {'✓ PASS' if pg_ok else '✗ FAIL'}")

    if s3_ok and pg_ok:
        print("\n✓ All connections successful! You're ready to run the pipeline.")
    else:
        print("\n✗ Some connections failed. Please check the errors above.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
