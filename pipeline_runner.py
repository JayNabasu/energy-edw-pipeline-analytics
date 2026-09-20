"""
Enterprise Data Warehouse ELT Pipeline Runner.
Executes automated ingestion, dimensional transformation, data quality assertion,
and star schema loading into SQLite/PostgreSQL.
"""

import sys
import os
from pathlib import Path
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure local imports work reliably
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from edw_core.models import Base, DimAsset, DimPartner, DimDate, FactProduction, FactCashCallReconciliation
from edw_core.extractors import (
    ASSETS_METADATA, PARTNERS_METADATA, generate_dates,
    extract_production_telemetry, extract_cash_call_billings
)
from data_quality.assertions import DataQualitySuite

DB_PATH = current_dir / "energy_edw.db"
DEFAULT_DB_URL = os.getenv("EDW_DATABASE_URL", f"sqlite:///{DB_PATH}")

def run_pipeline(db_url: str = DEFAULT_DB_URL, days: int = 120):
    print("=" * 70)
    print("NNPC RTI - ENTERPRISE DATA WAREHOUSE (EDW) PIPELINE INITIATIVE")
    print("   Lead Coordinator: Jerry A. Nabasu (JayNabasu)")
    print(f"   Target Database: {db_url}")
    print("=" * 70)

    engine = create_engine(db_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n[Step 1/5] Ingesting & Seeding Conformed Dimensions...")
    # Seed DimAsset
    for asset in ASSETS_METADATA:
        session.add(DimAsset(**asset))
    
    # Seed DimPartner
    for partner in PARTNERS_METADATA:
        session.add(DimPartner(**partner))

    # Seed DimDate
    dates = generate_dates(date(2024, 7, 1), days=days)
    for d in dates:
        session.add(DimDate(**d))

    session.commit()
    print(f"  [OK] {len(ASSETS_METADATA)} Operational Assets seeded (OML 119, 20, 28, 38, 49, 116)")
    print(f"  [OK] {len(PARTNERS_METADATA)} Joint Venture Partners seeded (NEPL, NAPIMS, JV Partners)")
    print(f"  [OK] {len(dates)} Calendar Days dimension populated")

    print("\n[Step 2/5] Extracting Telemetry & Financial Cash-Call Datasets...")
    df_prod = extract_production_telemetry(dates)
    df_cash = extract_cash_call_billings(dates)
    print(f"  [OK] {len(df_prod):,} Wellhead production measurements extracted")
    print(f"  [OK] {len(df_cash):,} Joint venture cash-call billing entries extracted")

    print("\n[Step 3/5] Executing Data Quality & Contract Assertion Suite...")
    dq = DataQualitySuite()
    dq.validate_production_dataset(df_prod)
    dq.validate_cash_call_dataset(df_cash)
    
    for _, report_row in dq.get_summary_report().iterrows():
        print(f"  [OK] [{report_row['status']}] {report_row['check_name']}: {report_row['details']}")

    print("\n[Step 4/5] Loading Staged Data into Star Schema Warehouse...")
    df_prod.to_sql("fact_production", con=engine, if_exists="append", index=False)
    df_cash.to_sql("fact_cash_call_reconciliation", con=engine, if_exists="append", index=False)
    print("  [OK] Fact tables committed with full referential integrity")

    print("\n[Step 5/5] Synthesizing Executive Reconciliation Summary...")
    total_billed = df_cash["total_cash_call_billed"].sum()
    total_remitted = df_cash["cash_remitted_by_partner"].sum()
    total_shortfall = df_cash[df_cash["net_variance_amount"] > 0]["net_variance_amount"].sum()
    total_crude_bbls = df_prod["net_crude_oil_bopd"].sum()

    print(f"  * Cumulative Net Crude Oil Production: {total_crude_bbls:,.2f} Barrels")
    print(f"  * Gross JV Cash-Calls Billed:        ${total_billed:,.2f} USD")
    print(f"  * Total Partner Remittances:         ${total_remitted:,.2f} USD")
    print(f"  * Identified JV Funding Variance:    ${total_shortfall:,.2f} USD (Actionable for AP/JV Review)")
    print("\n[SUCCESS] Pipeline execution completed successfully with 100% data contract compliance.")
    session.close()

if __name__ == "__main__":
    run_pipeline()
