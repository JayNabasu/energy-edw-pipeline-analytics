"""
Enterprise Data Warehouse Dimensional Model (Star Schema)
Optimized for Upstream Oil & Gas Operations and Joint Venture Cash-Call Reconciliations.
"""

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class DimAsset(Base):
    __tablename__ = "dim_asset"

    asset_id = Column(Integer, primary_key=True, autoincrement=True)
    asset_code = Column(String(50), unique=True, nullable=False) # e.g. OML-119, OML-20, OML-28, OML-38, OML-49, OML-116
    asset_name = Column(String(100), nullable=False)
    terrain = Column(String(50), nullable=False) # Deepwater, Shallow Water, Onshore Swamp, Land
    operating_entity = Column(String(100), nullable=False) # NEPL, SPDC JV, TEPNG JV, MPN JV
    equity_share_nnpc = Column(Float, nullable=False) # 0.55 (55%), 0.60 (60%)
    gross_capacity_bopd = Column(Float, nullable=False)

    production_records = relationship("FactProduction", back_populates="asset")
    cash_calls = relationship("FactCashCallReconciliation", back_populates="asset")

class DimPartner(Base):
    __tablename__ = "dim_partner"

    partner_id = Column(Integer, primary_key=True, autoincrement=True)
    partner_code = Column(String(50), unique=True, nullable=False) # NEPL, NAPIMS, JV_PARTNER_A, JV_PARTNER_B
    partner_name = Column(String(150), nullable=False)
    equity_percentage = Column(Float, nullable=False)
    contact_email = Column(String(100), nullable=True)

    cash_calls = relationship("FactCashCallReconciliation", back_populates="partner")

class DimDate(Base):
    __tablename__ = "dim_date"

    date_key = Column(Integer, primary_key=True) # YYYYMMDD
    full_date = Column(Date, unique=True, nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    month_name = Column(String(20), nullable=False)

class FactProduction(Base):
    __tablename__ = "fact_production"

    fact_id = Column(Integer, primary_key=True, autoincrement=True)
    date_key = Column(Integer, ForeignKey("dim_date.date_key"), nullable=False)
    asset_id = Column(Integer, ForeignKey("dim_asset.asset_id"), nullable=False)
    
    # Operational Telemetry & Measurements
    gross_liquids_bpd = Column(Float, nullable=False)
    net_crude_oil_bopd = Column(Float, nullable=False)
    associated_gas_mmscfd = Column(Float, nullable=False)
    produced_water_bpd = Column(Float, nullable=False)
    water_cut_pct = Column(Float, nullable=False)
    
    # Budget Targets & Variance Modeling
    target_net_crude_bopd = Column(Float, nullable=False)
    variance_bopd = Column(Float, nullable=False)
    variance_pct = Column(Float, nullable=False)
    downtime_hours = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    asset = relationship("DimAsset", back_populates="production_records")

class FactCashCallReconciliation(Base):
    __tablename__ = "fact_cash_call_reconciliation"

    reconciliation_id = Column(Integer, primary_key=True, autoincrement=True)
    date_key = Column(Integer, ForeignKey("dim_date.date_key"), nullable=False)
    asset_id = Column(Integer, ForeignKey("dim_asset.asset_id"), nullable=False)
    partner_id = Column(Integer, ForeignKey("dim_partner.partner_id"), nullable=False)
    
    billing_period = Column(String(20), nullable=False) # e.g. 2024-Q3
    currency = Column(String(10), default="USD")
    
    # Cash-Call Financials
    capital_expenditure_billed = Column(Float, nullable=False)
    operating_expenditure_billed = Column(Float, nullable=False)
    total_cash_call_billed = Column(Float, nullable=False)
    cash_remitted_by_partner = Column(Float, nullable=False)
    
    # Reconciliation Variance Calculation
    net_variance_amount = Column(Float, nullable=False) # (Total Billed - Remitted)
    variance_status = Column(String(50), nullable=False) # FULLY_PAID, UNDER_FUNDED, OVER_FUNDED
    created_at = Column(DateTime, default=datetime.utcnow)

    asset = relationship("DimAsset", back_populates="cash_calls")
    partner = relationship("DimPartner", back_populates="cash_calls")
