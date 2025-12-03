"""
orchestration_airflow.py

Airflow DAG for orchestrating the Olist data pipeline.

Pipeline Stages:
    1. Download data from Kaggle
    2. Upload to S3
    3. Create database schema
    4. Load S3 → PostgreSQL
    5. Run data transformations
    6. Data quality checks

Features:
    - Task dependencies
    - Retry logic
    - Email alerts on failure
    - SLA monitoring
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor
import sys
import os

# Add project paths
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'ingestion'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'transformation'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'tests'))

# Import pipeline functions
from download_from_kaggle import download_kaggle_dataset
from upload_to_s3 import upload_directory_to_s3, BUCKET_NAME, LOCAL_DIR, S3_PREFIX
from create_schema import create_schema, check_tables_exist
from s3_to_rds import load_all_raw_tables

# Default arguments for the DAG
default_args = {
    'owner': 'ids706_team',
    'depends_on_past': False,
    'email': ['team@duke.edu'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1),
}

# Define the DAG
dag = DAG(
    'olist_etl_pipeline',
    default_args=default_args,
    description='Olist E-Commerce Data Pipeline',
    schedule_interval='@daily',  # Run daily
    start_date=datetime(2024, 12, 1),
    catchup=False,
    tags=['etl', 'olist', 'e-commerce'],
)

# Task 1: Download from Kaggle
def download_task():
    """Download data from Kaggle."""
    print("[Task 1] Downloading from Kaggle...")
    success = download_kaggle_dataset()
    if not success:
        raise Exception("Kaggle download failed")
    print("[Task 1] ✓ Download complete")

task_download = PythonOperator(
    task_id='download_from_kaggle',
    python_callable=download_task,
    dag=dag,
)

# Task 2: Upload to S3
def upload_task():
    """Upload data to S3."""
    print("[Task 2] Uploading to S3...")
    upload_directory_to_s3(LOCAL_DIR, BUCKET_NAME, S3_PREFIX)
    print("[Task 2] ✓ Upload complete")

task_upload = PythonOperator(
    task_id='upload_to_s3',
    python_callable=upload_task,
    dag=dag,
)

# Task 3: Create/Check Schema
def schema_task():
    """Create or check database schema."""
    print("[Task 3] Checking schema...")
    exists, tables = check_tables_exist()
    if not exists:
        print("[Task 3] Creating schema...")
        create_schema(force=False)
    print(f"[Task 3] ✓ Schema ready ({len(tables)} tables)")

task_schema = PythonOperator(
    task_id='create_schema',
    python_callable=schema_task,
    dag=dag,
)

# Task 4: Load data to PostgreSQL
def load_task():
    """Load data from S3 to PostgreSQL."""
    print("[Task 4] Loading data to PostgreSQL...")
    success = load_all_raw_tables(truncate=False)
    if not success:
        raise Exception("Data load failed")
    print("[Task 4] ✓ Load complete")

task_load = PythonOperator(
    task_id='load_to_postgres',
    python_callable=load_task,
    dag=dag,
)

# Task 5: Run transformations
task_transform = BashOperator(
    task_id='run_transformations',
    bash_command='cd {{ params.project_root }}/transformation && python analyze_with_polars.py',
    params={'project_root': PROJECT_ROOT},
    dag=dag,
)

# Task 6: Data quality tests
task_quality = BashOperator(
    task_id='data_quality_tests',
    bash_command='cd {{ params.project_root }}/tests && python test_data_quality.py',
    params={'project_root': PROJECT_ROOT},
    dag=dag,
)

# Task 7: Generate report
task_report = BashOperator(
    task_id='generate_report',
    bash_command='echo "Pipeline completed at $(date)" >> {{ params.project_root }}/logs/pipeline.log',
    params={'project_root': PROJECT_ROOT},
    dag=dag,
)

# Define task dependencies
task_download >> task_upload >> task_schema >> task_load >> task_transform >> task_quality >> task_report

if __name__ == "__main__":
    dag.test()
