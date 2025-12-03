# 📋 Project Summary

## Quick Reference

### Run Complete Pipeline
```bash
cd ingestion
python ingestion_pipeline.py
```

### Test Before Running
```bash
cd ingestion
python test_connections.py
```

### Project Structure
```
IDS706_DE_FINAL_PROJECT/
├── .env                        # Credentials (DO NOT COMMIT)
├── .env.example                # Credentials template
├── .gitignore                  # Git exclusions
├── requirements.txt            # Python dependencies
├── README.md                   # Main documentation
│
├── .kaggle/                    # Kaggle API credentials
│   └── kaggle.json             # API token (DO NOT COMMIT)
│
├── ingestion/                  # Data pipeline
│   ├── README.md               # Pipeline documentation
│   ├── ingestion_pipeline.py   # Main orchestrator ⭐
│   ├── download_from_kaggle.py # Kaggle downloader
│   ├── upload_to_s3.py         # S3 uploader
│   ├── create_schema.py        # Schema manager
│   ├── s3_to_rds.py            # Data loader
│   ├── run_s3_to_postgres.py   # Simplified loader
│   ├── test_connections.py     # Connection validator
│   └── schema_raw.sql          # DDL script
│
└── notebooks/                  # Analysis notebooks
    └── eda_olist.ipynb         # EDA
```

## Pipeline Flow

```
Kaggle API → Local CSV → AWS S3 → PostgreSQL (Aiven)
   ↓              ↓         ↓            ↓
9 files       120 MB    Raw Zone    9 tables
                                   1.5M rows
```

## Database Schema

| Table | Rows | Dependencies |
|-------|------|--------------|
| customers_raw | 99,441 | None |
| sellers_raw | 3,095 | None |
| products_raw | 32,951 | None |
| geolocation_raw | 1,000,163 | None |
| product_category_name_translation_raw | 71 | None |
| orders_raw | 99,441 | customers_raw |
| order_items_raw | 112,650 | orders_raw, products_raw, sellers_raw |
| order_payments_raw | 103,886 | orders_raw |
| order_reviews_raw | 99,224 | orders_raw |

**Total: 1,551,022 rows**

## Key Features

✅ **Automated**: End-to-end pipeline from Kaggle to PostgreSQL  
✅ **Idempotent**: Safe to run multiple times  
✅ **Smart**: Skips unchanged data (incremental updates)  
✅ **Robust**: Foreign key handling, duplicate detection  
✅ **Monitored**: Progress tracking and detailed logs  
✅ **Secure**: All credentials in .env file  

## Configuration Files

### .env (Root)
```env
# AWS
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
S3_BUCKET=de-27-team3
S3_PREFIX=raw/
S3_REGION=us-east-2

# PostgreSQL
DB_HOST=xxx.aivencloud.com
DB_PORT=22446
DB_NAME=defaultdb
DB_USER=avnadmin
DB_PASSWORD=xxx
```

### .kaggle/kaggle.json (Root)
```json
{
  "username": "your_username",
  "key": "your_api_key"
}
```

Get from: https://www.kaggle.com/account

## Common Tasks

### First-Time Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure Kaggle
# Place kaggle.json in .kaggle/ folder

# 3. Test connections
cd ingestion
python test_connections.py

# 4. Run pipeline
python ingestion_pipeline.py
```

### Daily Operations
```bash
# Quick data refresh (if already in S3)
cd ingestion
python run_s3_to_postgres.py

# Full refresh (from Kaggle)
python ingestion_pipeline.py

# Force schema recreation
python ingestion_pipeline.py --force-schema-recreate
```

### Troubleshooting
```bash
# Test connections
python test_connections.py

# Check S3 contents
aws s3 ls s3://de-27-team3/raw/

# Check database
python -c "from test_connections import test_postgres_connection; test_postgres_connection()"
```

## Performance Metrics

- **Download time**: ~2-3 minutes
- **S3 upload**: ~1-2 minutes
- **Database load**: ~3-5 minutes
- **Total runtime**: ~6-10 minutes

## Data Quality

✅ NaN values → NULL  
✅ Duplicates handled (ON CONFLICT)  
✅ Foreign keys enforced  
✅ DOUBLE PRECISION for large numbers  
✅ Progress tracking for large tables  

## Team

- **Pinaki Ghosh** - Data Engineering & Orchestration
- **Austin Zhang** - Data Transformation & Modeling
- **Diwas Puri** - Data Ingestion & Storage
- **Michael Badu** - Testing & Analytics

## Resources

- **Dataset**: [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- **S3 Bucket**: de-27-team3 (us-east-2)
- **Database**: Aiven PostgreSQL (pg-3729bd9d-bnbgoals.j.aivencloud.com)
- **Repository**: IDS706_DE_FINAL_PROJECT

## Next Steps

1. ✅ Data ingestion complete
2. 🔄 Create transformed tables (analytics layer)
3. 🔄 Build dashboards
4. 🔄 Implement data quality checks
5. 🔄 Schedule automated runs
6. 🔄 Document analytical queries

---

**Last Updated**: December 2, 2024  
**Pipeline Status**: ✅ Fully Operational
