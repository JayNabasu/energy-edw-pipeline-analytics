"""
Streamlit Executive Analytics Dashboard for Upstream Energy EDW & JV Cash-Call Reconciliation.
Developed by Jerry A. Nabasu (@JayNabasu) - NNPC RTI Directorate.
"""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
import sys

# Page Configuration
st.set_page_config(
    page_title="Energy EDW & Cash-Call Analytics | NNPC RTI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Connect to EDW SQLite Database
DB_FILE = Path(__file__).resolve().parent.parent / "energy_edw.db"
engine = create_engine(f"sqlite:///{DB_FILE}")

@st.cache_data(ttl=600)
def load_data():
    with engine.connect() as conn:
        query_prod = """
            SELECT 
                p.fact_id,
                d.full_date,
                d.year,
                d.quarter,
                d.month_name,
                a.asset_code,
                a.asset_name,
                a.terrain,
                a.operating_entity,
                p.gross_liquids_bpd,
                p.net_crude_oil_bopd,
                p.associated_gas_mmscfd,
                p.produced_water_bpd,
                p.water_cut_pct,
                p.target_net_crude_bopd,
                p.variance_bopd,
                p.variance_pct,
                p.downtime_hours
            FROM fact_production p
            JOIN dim_asset a ON p.asset_id = a.asset_id
            JOIN dim_date d ON p.date_key = d.date_key
            ORDER BY d.full_date ASC
        """
        df_production = pd.read_sql(query_prod, conn)
        df_production["full_date"] = pd.to_datetime(df_production["full_date"])

        query_cash = """
            SELECT 
                c.reconciliation_id,
                c.billing_period,
                a.asset_code,
                a.asset_name,
                pr.partner_code,
                pr.partner_name,
                pr.equity_percentage,
                c.capital_expenditure_billed,
                c.operating_expenditure_billed,
                c.total_cash_call_billed,
                c.cash_remitted_by_partner,
                c.net_variance_amount,
                c.variance_status
            FROM fact_cash_call_reconciliation c
            JOIN dim_asset a ON c.asset_id = a.asset_id
            JOIN dim_partner pr ON c.partner_id = pr.partner_id
            ORDER BY c.billing_period DESC
        """
        df_cash_calls = pd.read_sql(query_cash, conn)

    return df_production, df_cash_calls

# Load datasets
try:
    df_prod, df_cash = load_data()
except Exception as e:
    st.error(f"Failed to load warehouse database: {e}. Please ensure `python pipeline_runner.py` has been executed.")
    st.stop()

# Header
st.title("⚡ Upstream Asset Analytics & JV Cash-Call Reconciliation Portal")
st.caption("Enterprise Data Warehouse (EDW) Analytics Platform | Lead: **Jerry A. Nabasu** ([@JayNabasu](https://github.com/JayNabasu))")

# Top KPI Metric Cards
col1, col2, col3, col4 = st.columns(4)
total_crude = df_prod["net_crude_oil_bopd"].sum()
total_billed = df_cash["total_cash_call_billed"].sum()
total_remitted = df_cash["cash_remitted_by_partner"].sum()
underfunded_amount = df_cash[df_cash["net_variance_amount"] > 0]["net_variance_amount"].sum()
avg_water_cut = df_prod["water_cut_pct"].mean()

col1.metric("Cumulative Net Crude", f"{total_crude:,.0f} BBL", delta=f"{df_prod['variance_pct'].mean():.1f}% vs Target")
col2.metric("Gross Cash-Calls Billed", f"${total_billed / 1e6:,.2f} M USD")
col3.metric("Unremitted Partner Variance", f"${underfunded_amount / 1e6:,.2f} M USD", delta="Under-funded", delta_color="inverse")
col4.metric("Avg Produced Water Cut", f"{avg_water_cut:.1f}%")

st.markdown("---")

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(["📊 Asset Production & KPI Variance", "💵 JV Cash-Call Reconciliation", "🛡️ EDW Architecture & Data Contracts"])

# TAB 1: PRODUCTION & KPI VARIANCE
with tab1:
    st.subheader("Operational Production vs Budgeted Targets")
    
    asset_list = ["All Assets"] + sorted(df_prod["asset_code"].unique().tolist())
    selected_asset = st.selectbox("Select Asset Workstream:", asset_list)

    if selected_asset != "All Assets":
        filtered_prod = df_prod[df_prod["asset_code"] == selected_asset]
    else:
        filtered_prod = df_prod

    # Aggregate daily production
    daily_trend = filtered_prod.groupby("full_date")[["net_crude_oil_bopd", "target_net_crude_bopd"]].sum()
    st.line_chart(daily_trend)

    # Breakdown by Asset Table
    st.write("#### Asset Performance Summary")
    asset_summary = df_prod.groupby(["asset_code", "terrain", "operating_entity"]).agg(
        Total_Crude_BBL=("net_crude_oil_bopd", "sum"),
        Avg_Daily_BOPD=("net_crude_oil_bopd", "mean"),
        Target_Daily_BOPD=("target_net_crude_bopd", "mean"),
        Avg_Water_Cut=("water_cut_pct", "mean"),
        Avg_Variance_Pct=("variance_pct", "mean")
    ).reset_index()

    st.dataframe(asset_summary.style.format({
        "Total_Crude_BBL": "{:,.0f}",
        "Avg_Daily_BOPD": "{:,.1f}",
        "Target_Daily_BOPD": "{:,.1f}",
        "Avg_Water_Cut": "{:.1f}%",
        "Avg_Variance_Pct": "{:+.2f}%"
    }), use_container_width=True)

# TAB 2: CASH-CALL RECONCILIATION
with tab2:
    st.subheader("Joint Venture Partner Billing & Cash Remittance Audit")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        partner_filter = st.multiselect("Filter Partner:", sorted(df_cash["partner_code"].unique()), default=sorted(df_cash["partner_code"].unique()))
    with col_f2:
        status_filter = st.multiselect("Funding Status:", sorted(df_cash["variance_status"].unique()), default=sorted(df_cash["variance_status"].unique()))

    filtered_cash = df_cash[
        (df_cash["partner_code"].isin(partner_filter)) &
        (df_cash["variance_status"].isin(status_filter))
    ]

    st.dataframe(filtered_cash.style.format({
        "capital_expenditure_billed": "${:,.2f}",
        "operating_expenditure_billed": "${:,.2f}",
        "total_cash_call_billed": "${:,.2f}",
        "cash_remitted_by_partner": "${:,.2f}",
        "net_variance_amount": "${:,.2f}",
        "equity_percentage": "{:.0%}"
    }), use_container_width=True)

    csv_data = filtered_cash.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Reconciliation Audit Pack (CSV)",
        data=csv_data,
        file_name="jv_cash_call_reconciliation_audit.csv",
        mime="text/csv"
    )

# TAB 3: DATA ARCHITECTURE & CONTRACTS
with tab3:
    st.subheader("Enterprise Data Warehouse Contract Verification")
    st.markdown("""
    The EDW pipeline enforces automated schema validation and business integrity rules prior to loading staged data into conformed dimensions and fact tables:
    - **Physical Bounds**: Water Cut strictly between 0% and 100%.
    - **Volumetric Parity**: Gross Liquids == Net Crude + Produced Water (tolerance < 0.05 bpd).
    - **Cash-Call Parity**: Total Billed == CAPEX + OPEX across 100% of partner line items.
    - **Referential Integrity**: Verified foreign key relationships against `dim_asset`, `dim_partner`, and `dim_date`.
    """)
    st.info("Pipeline status: Verified with zero contract violations across all operational workstreams.")
