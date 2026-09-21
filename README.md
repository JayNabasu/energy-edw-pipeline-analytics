# Upstream Energy Enterprise Data Warehouse (EDW) & JV Cash-Call Analytics

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg?logo=sqlalchemy)](https://www.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?logo=postgresql)](https://www.postgresql.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B.svg?logo=streamlit)](https://streamlit.io/)
[![Docker Compose](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Jerry%20A.%20Nabasu-blue.svg)](https://github.com/JayNabasu)

An end-to-end Enterprise Data Warehouse (EDW) and operational analytics platform modeling upstream oil & gas telemetry across multi-terrain operating concessions (deepwater, swamp, and onshore), automating Joint Venture (JV) cash-call financial reconciliations, and enforcing strict data quality contracts.

---

## Architectural Highlights

- **Star Schema Dimensional Modeling**: Conformed dimensions (`dim_asset`, `dim_partner`, `dim_date`) joined to grain-level facts (`fact_production` for daily telemetry and `fact_cash_call_reconciliation` for partner billings and remittances).
- **Automated Data Quality & Contracts**: Assertion suite validating physical volumetric bounds (water-cut percentages, conservation of liquids law: Gross = Net Crude + Water) and financial parity (`Total Billed = CAPEX + OPEX`).
- **JV Cash-Call Billing & Reconciliation Engine**: Reconciles monthly cash-call commitments against partner disbursements, detecting under/over-funding variances for executive review.
- **Interactive Streamlit Executive Portal**: Real-time KPI tracking, interactive asset variance exploration vs AOP (Annual Operating Plan) targets, and one-click reconciliation audit pack exports.
- **Production Containerization**: Multi-container `docker-compose` orchestration supporting PostgreSQL 16, automated ELT migration worker, and web dashboard.

---

## Architecture & Data Flow

```mermaid
flowchart TD
    subgraph Sources ["Upstream Operational & Financial Sources"]
        S1[SCADA & Wellhead Metering Telemetry]
        S2[SAP ERP JV Cash-Call Billing Notices]
        S3[Partner Bank Remittance Advices]
    end

    subgraph Ingestion_Transform ["ELT Pipeline Engine (Python / Pandas / SQLAlchemy)"]
        Extract[Extractor & Normalizer] --> DQ{Data Quality Suite}
        DQ -- Violations --> Reject[Quarantine Anomaly Log]
        DQ -- Validated --> StarSchema[Dimensional Transformation]
    end

    subgraph Warehouse ["Enterprise Data Warehouse (PostgreSQL / SQLite)"]
        StarSchema --> DimAsset[(dim_asset)]
        StarSchema --> DimPartner[(dim_partner)]
        StarSchema --> DimDate[(dim_date)]
        StarSchema --> FactProd[(fact_production)]
        StarSchema --> FactCash[(fact_cash_call_reconciliation)]
    end

    subgraph Analytics ["Executive BI Layer"]
        Warehouse --> StreamlitApp[Streamlit Analytics Portal]
        StreamlitApp --> Charts[Concession KPI Variances]
        StreamlitApp --> AuditTable[Partner Variance Discrepancy Matrix]
        StreamlitApp --> CSVExport[Reconciliation Review Packs]
    end

    S1 --> Extract
    S2 --> Extract
    S3 --> Extract
```

---

## Repository Structure

```text
energy-edw-pipeline-analytics/
├── edw_core/
│   ├── models.py                  # SQLAlchemy Star Schema models
│   └── extractors.py              # Telemetry & JV billing generators
├── data_quality/
│   └── assertions.py              # Automated data assertions & contract suite
├── dashboard/
│   └── app.py                     # Interactive Streamlit executive dashboard
├── tests/
│   └── test_pipeline.py           # pytest automated validation suite
├── pipeline_runner.py             # End-to-end ELT orchestration script
├── docker-compose.yml             # Container orchestration (PostgreSQL + Dashboard)
├── Dockerfile                     # Container definition
├── requirements.txt               # Dependencies
├── .gitignore
└── README.md
```

---

## Quick Start Guide

### 1. Local Python Environment Setup
```powershell
# Clone the repository
git clone https://github.com/JayNabasu/energy-edw-pipeline-analytics.git
cd energy-edw-pipeline-analytics

# Install dependencies
pip install -r requirements.txt
```

### 2. Execute the ELT Pipeline
Runs dimensional seeding, ingestion, data quality assertions, and populates the star schema warehouse:
```powershell
python pipeline_runner.py
```

### 3. Run Automated Tests
```powershell
python -m pytest tests/test_pipeline.py
```

### 4. Launch the Executive Dashboard
```powershell
streamlit run dashboard/app.py
```
Open `http://localhost:8501` in your browser to explore asset telemetry, water-cut trends, and partner cash-call reconciliation matrices.

### 5. Run with Docker Compose (PostgreSQL)
```powershell
docker-compose up --build
```

---

## Author & Contact

**Jerry A. Nabasu**  
- **Role**: Automation & Digital Innovation Professional  
- **Directorate**: Research, Technology & Innovation (RTI), NNPC Limited  
- **GitHub**: [@JayNabasu](https://github.com/JayNabasu)  
- **Email**: [jerrynabasu@gmail.com](mailto:jerrynabasu@gmail.com)
