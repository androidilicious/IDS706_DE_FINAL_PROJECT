"""
download_from_kaggle.py

Kaggle dataset downloader with project-local credential support.

Downloads Olist Brazilian E-Commerce dataset from Kaggle API.

Features:
    - Uses project-local .kaggle folder if exists
    - Falls back to default ~/.kaggle if not found
    - Automatic unzipping of dataset
    - CSV file validation

Requirements:
    - kaggle.json in .kaggle/ folder (get from kaggle.com/account)
    - kaggle package installed
"""

import os

# ========= KAGGLE CONFIG =========
# Set KAGGLE_CONFIG_DIR to project .kaggle folder if exists
# This allows team members to keep credentials in project folder
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
project_kaggle_dir = os.path.join(project_root, '.kaggle')

if os.path.exists(os.path.join(project_kaggle_dir, 'kaggle.json')):
    os.environ['KAGGLE_CONFIG_DIR'] = project_kaggle_dir
# ================================

from kaggle.api.kaggle_api_extended import KaggleApi

DATASET = "olistbr/brazilian-ecommerce"
LOCAL_DIR = "DE_Project_Data"

def download_kaggle_dataset():
    """Download Olist dataset from Kaggle."""
    try:
        if 'KAGGLE_CONFIG_DIR' in os.environ:
            print(f"[INFO] Using Kaggle credentials from: {os.environ['KAGGLE_CONFIG_DIR']}")
        
        print("[INFO] Authenticating with Kaggle...")
        api = KaggleApi()
        api.authenticate()

        os.makedirs(LOCAL_DIR, exist_ok=True)
        print(f"[INFO] Downloading dataset '{DATASET}' to {LOCAL_DIR}...")
        
        api.dataset_download_files(
            DATASET,
            path=LOCAL_DIR,
            unzip=True
        )
        
        # List downloaded files
        files = [f for f in os.listdir(LOCAL_DIR) if f.endswith('.csv')]
        print(f"[SUCCESS] Downloaded {len(files)} CSV files:")
        for f in files:
            print(f"  - {f}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to download dataset: {e}")
        return False

if __name__ == "__main__":
    download_kaggle_dataset()
