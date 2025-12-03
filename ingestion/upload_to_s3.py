"""
upload_to_s3.py

AWS S3 uploader for raw CSV files.

Uploads local CSV files to S3 bucket for cloud storage layer.

Features:
    - Bulk CSV upload
    - Progress tracking
    - Error handling per file
    - Configurable S3 prefix (folder structure)

Configuration:
    - Credentials from .env file
    - Target: s3://de-27-team3/raw/
"""

import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ========= AWS CREDENTIALS =========
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
# ===================================

# ========= S3 CONFIG =========
BUCKET_NAME = os.getenv('S3_BUCKET', 'de-27-team3')
LOCAL_DIR = "DE_Project_Data"
S3_PREFIX = os.getenv('S3_PREFIX', 'raw/')
REGION = os.getenv('S3_REGION', 'us-east-2')
# ============================


def upload_directory_to_s3(local_dir: str, bucket: str, s3_prefix: str = ""):
    """Upload all CSV files in local_dir to S3 bucket under s3_prefix."""
    s3 = boto3.client(
        "s3",
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    files = [f for f in os.listdir(local_dir) if f.endswith(".csv")]
    if not files:
        print(f"No CSV files found in {local_dir}")
        return

    print(f"Found {len(files)} CSV files in {local_dir}:")
    for f in files:
        print("  -", f)

    for filename in files:
        local_path = os.path.join(local_dir, filename)
        s3_key = f"{s3_prefix.rstrip('/')}/{filename}" if s3_prefix else filename

        print(f"\nUploading {local_path} → s3://{bucket}/{s3_key}")
        try:
            s3.upload_file(local_path, bucket, s3_key)
            print(" Success")
        except ClientError as e:
            print(" Failed:", e)


if __name__ == "__main__":
    upload_directory_to_s3(LOCAL_DIR, BUCKET_NAME, S3_PREFIX)
