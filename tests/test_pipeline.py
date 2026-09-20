import pytest
import pandas as pd
from datetime import date
from edw_core.extractors import (
    ASSETS_METADATA, PARTNERS_METADATA, generate_dates,
    extract_production_telemetry, extract_cash_call_billings
)
from data_quality.assertions import DataQualitySuite, DataQualityError

def test_generate_dates():
    dates = generate_dates(date(2024, 1, 1), days=31)
    assert len(dates) == 31
    assert dates[0]["date_key"] == 20240101
    assert dates[-1]["date_key"] == 20240131

def test_production_volumetric_integrity():
    dates = generate_dates(date(2024, 1, 1), days=7)
    df_prod = extract_production_telemetry(dates)
    
    # 6 assets * 7 days = 42 rows
    assert len(df_prod) == 42
    
    # Assert gross liquids == net crude + produced water
    gross_diff = (df_prod["gross_liquids_bpd"] - (df_prod["net_crude_oil_bopd"] + df_prod["produced_water_bpd"])).abs()
    assert gross_diff.max() <= 0.05

def test_cash_call_financial_integrity():
    dates = generate_dates(date(2024, 1, 1), days=60) # covers Jan 1 and Feb 1
    df_cash = extract_cash_call_billings(dates)
    
    assert not df_cash.empty
    # Assert total billed equals capex + opex
    bill_diff = (df_cash["total_cash_call_billed"] - (df_cash["capital_expenditure_billed"] + df_cash["operating_expenditure_billed"])).abs()
    assert bill_diff.max() <= 0.02

def test_data_quality_suite_passes_valid_data():
    dates = generate_dates(date(2024, 1, 1), days=10)
    df_prod = extract_production_telemetry(dates)
    df_cash = extract_cash_call_billings(dates)

    dq = DataQualitySuite()
    assert dq.validate_production_dataset(df_prod) is True
    assert dq.validate_cash_call_dataset(df_cash) is True

def test_data_quality_suite_catches_corrupted_data():
    dates = generate_dates(date(2024, 1, 1), days=5)
    df_prod = extract_production_telemetry(dates)
    
    # Corrupt a water cut value to 150% (physically impossible)
    df_prod.loc[0, "water_cut_pct"] = 150.0

    dq = DataQualitySuite()
    with pytest.raises(DataQualityError):
        dq.validate_production_dataset(df_prod)
