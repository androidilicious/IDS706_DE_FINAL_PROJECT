# 🏗️ From Order to Insight: Scalable Data Engineering Pipeline for E-Commerce

**Course:** IDS 706 – Data Engineering  
**Instructor:** [Dr. Zhongyuan Yu]  
**Team:** [Pinaki Ghosh, Austin Zhang, Diwas Puri, Michael Badu]  
**Timeline:** Nov 12 → Dec 5 (Final Submission)

## 📘 Project Overview

This project designs and implements a **cloud-ready data engineering pipeline** using the [Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).  
It replicates a real-world enterprise analytics platform — automating data ingestion, transformation, and analysis — to produce reproducible, scalable insights about e-commerce operations, customer satisfaction, and logistics performance.

The final solution will combine **AWS cloud services, containerization, orchestration, and CI/CD automation** to demonstrate practical components of modern data engineering workflows.

## 🎯 Why This Dataset

Olist is a Brazilian marketplace that connects thousands of small sellers with customers nationwide.  
It was selected because:

- **Rich relational structure:** multiple linked tables across orders, customers, products, and logistics.
- **Realistic business process flow:** mirrors the operational data in real e-commerce pipelines.
- **Complete pipeline scope:** enables components for ingestion, transformation, analytics, and visualization within one integrated ecosystem.
- **Open, reproducible data:** no API keys or privacy restrictions - data masked by source to avoid any PII handling

This dataset provides an opportunity to build a pipeline that can demonstrate the entire data engineering lifecycle as well as be applicable for a lightweight production setup

## Schema of the Dataset

<img width="2486" height="1496" alt="image" src="https://github.com/user-attachments/assets/c12594df-4515-45b9-93d4-1a4618ee0f76" />


## 🧩 Logical Architecture (with AWS Integration)

            ┌───────────────────────────────────────┐
            │         External Data Sources         │
            │ Kaggle Olist Dataset, APIs (Weather,  │
            │ Currency, Geolocation)                │
            └────────────────────┬──────────────────┘
                                 │
                         [Data Ingestion]
                                 │
        ┌────────────────────────┴────────────────────────┐
        │                AWS S3 (Raw Zone)                │
        │  - Versioned object storage                     │
        │  - Metadata in DynamoDB                         │
        └────────────────────────┬────────────────────────┘
                                 │
                     [Data Transformation]
                                 │
    ┌────────────────────────────┴────────────────────────────┐
    │   AWS Glue / PySpark / Polars (ETL Processing Layer)    │
    │   - Clean, join, and enrich datasets                    │
    │   - Load curated data into warehouse                    │
    └────────────────────────────┬────────────────────────────┘
                                 │
                         [Data Warehouse]
                                 │
             ┌──────────────────┴──────────────────┐
             │         AWS RDS (PostgreSQL)       │
             │   - Analytical schema (Star/3NF)   │
             │   - SQL views for BI queries       │
             └──────────────────┬──────────────────┘
                                 │
                      [Orchestration & CI/CD]
                                 │
      ┌──────────────────────────┴──────────────────────────┐
      │ Apache Airflow (Amazon MWAA) orchestrating DAGs     │
      │ GitHub Actions → Docker → ECS (build/test/deploy)   │
      └──────────────────────────┬──────────────────────────┘
                                 │
                         [Analysis & Serving]
                                 │
       ┌─────────────────────────┴──────────────────────────┐
       │ Streamlit Dashboard (deployed on AWS EC2)│
       │   with live PostgreSQL connection and KPIs         │
       └────────────────────────────────────────────────────┘


## 🪜 Workflow & Learning Objectives-Planned

| Workflow Stage | Data-Engineering Concept | Expected Deliverable |
|----------------|--------------------------|----------------------|
| **Data Ingestion** | API and batch ingestion from Kaggle → S3 | Automated extraction + Airflow DAG |
| **Data Storage** | Raw → Processed → Analytical zoning | Normalized schema in AWS RDS |
| **Transformation** | Distributed compute, schema evolution | Polars/PySpark ETL jobs |
| **Orchestration** | Scheduling, retry logic, observability | Airflow DAGs with logging and SLA checks |
| **Testing & Validation** | Data quality and schema validation | Great Expectations reports |
| **CI/CD** | Automation and reproducibility | GitHub Actions + Docker build/test pipeline |
| **Analytics & Serving** | Querying, KPIs, and visualization | Streamlit dashboard with insights |
| **Governance & Security** | IAM, least-privilege access | Role-based permissions and audit logs |

## ⚙️ Proposed Tech Stack

| Layer | Tools |
|-------|-------|
| **Compute** | PySpark (Glue) / Polars |
| **Storage & Warehouse** | AWS S3 (Data Lake), AWS RDS (PostgreSQL) |
| **Ingestion** | Kaggle API |
| **Orchestration** | Apache Airflow |
| **Testing** | Great Expectations, Pytest |
| **Containerization** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |
| **Visualization** | Streamlit  |
| **Documentation** | Markdown |


## 🔁 Reproducibility & Scalability

- **Reproducibility**
  - Environment codified via `Dockerfile` + `requirements.txt`
  - Consistent runs through GitHub Actions pipeline  
  - Versioned S3 storage for raw and processed data
  - All configs externalized (`.env`, YAMLs)

- **Scalability**
  - Modular DAGs and transformation scripts
  - Elastic AWS compute and storage (Glue, RDS)
  - Lazy evaluation and partitioned queries in Polars
  - Stateless containers ensure horizontal scalability
 
  ## 🗓️ Project Plan and Twice-a-Week Drops

| Drop | Date | Milestones | Deliverables |
|------|------|-------------|---------------|
| **Drop 1** | **Nov 14** | Environment setup, dataset profiling, schema draft | EDA notebook, draft schema diagram |
| **Drop 2** | **Nov 18** | Data ingestion pipeline + S3 load | Airflow DAG for ingestion, raw data storage validation |
| **Drop 3** | **Nov 21** | ETL transformation logic | PySpark/Polars scripts, processed zone creation |
| **Drop 4** | **Nov 25** | Analytical schema + queries | RDS schema + SQL transformations |
| **Drop 5** | **Nov 28** | Orchestration + CI/CD | Airflow orchestration, Docker + GitHub Actions |
| **Drop 6** | **Dec 2** | Dashboard + testing layer | Streamlit dashboard, Great Expectations suite |
| **Drop 7** | **Dec 5** | Final polish + dry run | Complete repo, video rehearsal, README finalization |
| **Submission** | **Dec 6** | Final delivery | Code + Docs + Video walkthrough |

All deliverables will be merged into `main` via reviewed pull requests, with active commits from each member twice a week.

## 🧱 Development Best Practices to be followed

- **Branching:** Feature branches → Pull Request → Review → Merge  
- **Code Quality:** Black formatter + Pylint + docstrings  
- **Testing:** Pytest + Great Expectations integrated into CI/CD  
- **Observability:** Airflow monitoring, task-level logs  
- **Documentation:** Updated Markdown/Quarto after every drop  
- **Team Workflow:** Asynchronous commits; synchronous check-ins every drop day  
- **Peer Review:** Every merge request requires one documented reviewer's approval

## 📦 Planned Deliverables

| Category | Deliverable | Description |
|-----------|--------------|-------------|
| **Repository** | Complete GitHub repo | Code, docs, notebooks, tests, Docker, CI/CD |
| **Cloud Deployment** | AWS-hosted pipeline | S3 + Glue + RDS + EC2 integration |
| **Transformation Layer** | Polars / PySpark ETL | Data cleaning, joins, enrichments, metrics |
| **Analytics & Dashboard** | Streamlit app | Predefined KPIs and charts |
| **Testing & CI/CD** | Automated validation | GitHub Actions |
| **Documentation** | PDF, diagrams, video | README, architecture, walkthrough demo |

## ⚠️ Risks and Contingencies

| Risk | Impact | Mitigation |
|------|---------|-------------|
| **AWS credential or quota limits** | Delayed deployment | PostgreSQL mirror |
| **Glue or RDS compute limits** | ETL job failure or cost spikes | Process subset data locally, scale on need |
| **Scheduling conflicts** | Progress slippage | Dual ownership per module, fixed drop cadence |
| **Airflow DAG failures** | Pipeline disruption | Local Airflow container fallback |
| **Data quality inconsistencies** | Analysis bias | Early validation using Great Expectations |
| **Cost escalation** | Budget breach | Limit S3 region usage, choose free-tier EC2 instance |

## ⚖️ Trade-Off Decisions

| Area | Options | Decision Basis |
|------|----------|----------------|
| **ETL engine** | Glue vs Polars | Polars for simplicity and control under free tier |
| **Data storage** | Full cloud vs hybrid | Hybrid ensures AWS exposure + cost control |
| **Transformation tool** | dbt vs native code | dbt optional; focus on reproducibility with scripts |
| **Dashboard deployment** | EC2 vs Streamlit Cloud | Streamlit Cloud during dev, EC2 for final demo |
| **Data volume** | Full vs sampled | Sample for testing; scale full later |
| **Automation scope** | Full CI/CD vs scoped | Prioritize lint/test/build integration |

## 🚀 Forward View

| Phase | Focus | Scope |
|--------|--------|--------|
| **During Project (Nov–Dec)** | Build & deploy full batch pipeline | Ingestion → transformation → orchestration → visualization |
| **Next Stage (Post-Project)** | Optimize & automate | dbt lineage docs, CloudFormation templates, role-based access |
| **Future Extensions** | Real-time + ML integration | Kafka streams, feature store, API endpoints for analytics-as-a-service |

## Repository Structure

├── dags/
│ ├── extract_load_dag.py
│ ├── transform_dag.py
│ └── analyze_dag.py
│
├── scripts/
│ ├── ingest_data.py
│ ├── transform_data.py
│ ├── analyze_data.py
│
├── configs/
│ ├── aws_config.yaml
│ └── dbt_project.yml
│
├── tests/
│ ├── test_ingestion.py
│ ├── test_transformations.py
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .github/workflows/ci.yml
├── architecture_diagram.png
└── README.md

## 🌐 Core Data-Engineering Principles Demonstrated

| Principle | Implementation |
|------------|----------------|
| **Scalability** | Modular DAGs, S3-based storage, Polars parallelism |
| **Reproducibility** | Docker + CI/CD ensures identical builds |
| **Observability** | Airflow DAG tracking + CloudWatch logs |
| **Governance** | Schema registry, documentation, versioned data |
| **Security** | IAM roles, private keys via AWS Secrets Manager |
| **Reliability** | Task retries, validation before load |
| **Efficiency** | Partitioned reads, lazy transformations |

---

## 🎯 Expected Outcomes

- Functional **AWS-integrated data engineering pipeline**
- Demonstration of modern DE principles: orchestration, CI/CD, reproducibility
- Analytical insights into **delivery performance, customer behavior, and seller KPIs**
- Repository structured for **scaling to production-ready architecture**

---

## 👥 Team Roles

Each team member contributes across the data pipeline, with ownership distributed by functional areas to ensure redundancy, skill sharing, and parallel progress.

| Role | Responsibilities | Key Deliverables |
|------|------------------|------------------|
| **Data Engineering & Orchestration** | Set up Apache Airflow pipelines for ingestion, transformation, and scheduling. Manage dependencies, retries, and workflow monitoring. | Airflow DAGs, orchestration documentation, pipeline logs. |
| **Data Ingestion & Storage** | Develop scripts for data extraction from Kaggle and APIs. Design S3 bucket structure and RDS schema. Ensure schema consistency and versioned data zones (raw → processed → analytical). | Ingestion scripts, S3/RDS setup, schema documentation. |
| **Data Transformation & Modeling** | Implement transformation logic using Polars or PySpark. Perform joins, aggregations, and feature engineering. Create regression-ready analytical tables. | ETL scripts, transformation notebooks, derived metrics. |
| **Testing & CI/CD Automation** | Build and maintain testing and validation layers. Implement Great Expectations for data quality and GitHub Actions for automated testing and container builds. | Pytest and validation suite, CI/CD pipelines. |
| **Analytics & Visualization** | Design SQL queries and regression models for insights. Build a Streamlit dashboard showcasing KPIs and analysis outcomes. | Analytical notebooks, queries, Streamlit dashboard. |
| **Documentation & Version Control** | Maintain clear documentation, environment reproducibility, and version control discipline. Ensure alignment with the project rubric and reproducibility. | README, environment files, Quarto/Overleaf documentation. |

**Collaboration Model**
- **Twice-weekly commits** aligned with project “drop” plan.  
- **Feature-branch workflow** with code reviews and pull requests before merge.  
- Shared GitHub repository for all code, documentation, and pipeline assets.  
- Inline commenting and task tracking via GitHub


## 🏁 References
- [Olist E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)  
- [AWS Free Tier Services](https://aws.amazon.com/free/)  
- [Apache Airflow Docs](https://airflow.apache.org/docs/)  
- [Polars Docs](https://pola.rs/)  
- [Great Expectations](https://greatexpectations.io/)  
- [Streamlit](https://streamlit.io/)  
