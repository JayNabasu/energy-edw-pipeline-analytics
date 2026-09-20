"""
Data Extractors & Mock Telemetry Ingestion for Upstream Assets & JV Billing.
Generates realistic SCADA telemetry, well metering, and cash-call ledger entries.
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Dict, List, Tuple

ASSETS_METADATA = [
    {"asset_code": "OML-119", "asset_name": "OML 119 Deepwater Asset", "terrain": "Deepwater", "operating_entity": "NEPL-NAPIMS JV", "equity_share_nnpc": 0.60, "gross_capacity_bopd": 45000.0},
    {"asset_code": "OML-20", "asset_name": "OML 20 Swamp Asset", "terrain": "Swamp", "operating_entity": "NEPL Operations", "equity_share_nnpc": 1.00, "gross_capacity_bopd": 28000.0},
    {"asset_code": "OML-28", "asset_name": "OML 28 Land Asset", "terrain": "Land", "operating_entity": "SPDC-NEPL JV", "equity_share_nnpc": 0.55, "gross_capacity_bopd": 35000.0},
    {"asset_code": "OML-38", "asset_name": "OML 38 Western Niger Delta", "terrain": "Land", "operating_entity": "NEPL Operations", "equity_share_nnpc": 0.55, "gross_capacity_bopd": 42000.0},
    {"asset_code": "OML-49", "asset_name": "OML 49 Offshore Escravos", "terrain": "Shallow Water", "operating_entity": "CNL-NEPL JV", "equity_share_nnpc": 0.60, "gross_capacity_bopd": 50000.0},
    {"asset_code": "OML-116", "asset_name": "OML 116 Agbara Offshore", "terrain": "Offshore", "operating_entity": "NAOC-NEPL JV", "equity_share_nnpc": 0.60, "gross_capacity_bopd": 22000.0}
]

PARTNERS_METADATA = [
    {"partner_code": "NEPL", "partner_name": "NNPC Exploration & Production Limited", "equity_percentage": 0.55, "contact_email": "finance@nepl.com.ng"},
    {"partner_code": "NAPIMS", "partner_name": "National Petroleum Investment Management Services", "equity_percentage": 0.05, "contact_email": "jv.accounts@napims.com.ng"},
    {"partner_code": "JV_PARTNER_A", "partner_name": "Pan-Atlantic Energy Holdings", "equity_percentage": 0.25, "contact_email": "cashcalls@panatlantic.com"},
    {"partner_code": "JV_PARTNER_B", "partner_name": "Global Upstream E&P Limited", "equity_percentage": 0.15, "contact_email": "accounting@globalep.com"}
]

def generate_dates(start_date: date, days: int = 90) -> List[Dict]:
    date_records = []
    for i in range(days):
        cur_date = start_date + timedelta(days=i)
        date_records.append({
            "date_key": int(cur_date.strftime("%Y%m%d")),
            "full_date": cur_date,
            "year": cur_date.year,
            "quarter": (cur_date.month - 1) // 3 + 1,
            "month": cur_date.month,
            "month_name": cur_date.strftime("%B")
        })
    return date_records

def extract_production_telemetry(dates: List[Dict], seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    records = []

    for asset_idx, asset in enumerate(ASSETS_METADATA, start=1):
        base_capacity = asset["gross_capacity_bopd"]
        
        for d in dates:
            d_key = d["date_key"]
            # Simulate realistic fluctuations around capacity
            efficiency = np.random.uniform(0.78, 0.96)
            water_cut = np.random.uniform(0.12, 0.38) # 12% to 38% water cut
            target_crude = round(base_capacity * 0.88, 2)
            
            gross_liquids = round(base_capacity * efficiency, 2)
            net_crude = round(gross_liquids * (1.0 - water_cut), 2)
            produced_water = round(gross_liquids * water_cut, 2)
            associated_gas = round(net_crude * np.random.uniform(0.0012, 0.0018), 2) # Gas Oil Ratio
            
            variance_bopd = round(net_crude - target_crude, 2)
            variance_pct = round((variance_bopd / target_crude) * 100.0, 2)
            downtime_hours = round(np.random.exponential(1.2), 1) if efficiency < 0.82 else 0.0

            records.append({
                "date_key": d_key,
                "asset_id": asset_idx,
                "gross_liquids_bpd": gross_liquids,
                "net_crude_oil_bopd": net_crude,
                "associated_gas_mmscfd": associated_gas,
                "produced_water_bpd": produced_water,
                "water_cut_pct": round(water_cut * 100.0, 2),
                "target_net_crude_bopd": target_crude,
                "variance_bopd": variance_bopd,
                "variance_pct": variance_pct,
                "downtime_hours": downtime_hours
            })

    return pd.DataFrame(records)

def extract_cash_call_billings(dates: List[Dict], seed: int = 101) -> pd.DataFrame:
    np.random.seed(seed)
    records = []

    # Bill monthly on the 1st of each month
    billing_dates = [d for d in dates if d["full_date"].day == 1]

    for b_date in billing_dates:
        d_key = b_date["date_key"]
        period = f"{b_date['year']}-M{b_date['month']:02d}"

        for asset_idx, asset in enumerate(ASSETS_METADATA, start=1):
            # Base monthly OPEX & CAPEX requirements based on asset size
            monthly_capex = round(np.random.uniform(1500000.0, 4500000.0), 2)
            monthly_opex = round(np.random.uniform(2200000.0, 6000000.0), 2)

            for partner_idx, partner in enumerate(PARTNERS_METADATA, start=1):
                equity = partner["equity_percentage"]
                partner_capex = round(monthly_capex * equity, 2)
                partner_opex = round(monthly_opex * equity, 2)
                total_billed = round(partner_capex + partner_opex, 2)

                # Simulate remittances (some on time, some with variance/under-funding)
                payment_behavior = np.random.choice(["EXACT", "SHORTFALL", "SURPLUS"], p=[0.70, 0.25, 0.05])
                if payment_behavior == "EXACT":
                    remitted = total_billed
                    variance = 0.0
                    status = "FULLY_PAID"
                elif payment_behavior == "SHORTFALL":
                    shortfall_pct = np.random.uniform(0.08, 0.25)
                    remitted = round(total_billed * (1.0 - shortfall_pct), 2)
                    variance = round(total_billed - remitted, 2)
                    status = "UNDER_FUNDED"
                else:
                    surplus = round(np.random.uniform(20000.0, 100000.0), 2)
                    remitted = round(total_billed + surplus, 2)
                    variance = round(total_billed - remitted, 2) # negative indicates surplus
                    status = "OVER_FUNDED"

                records.append({
                    "date_key": d_key,
                    "asset_id": asset_idx,
                    "partner_id": partner_idx,
                    "billing_period": period,
                    "currency": "USD",
                    "capital_expenditure_billed": partner_capex,
                    "operating_expenditure_billed": partner_opex,
                    "total_cash_call_billed": total_billed,
                    "cash_remitted_by_partner": remitted,
                    "net_variance_amount": variance,
                    "variance_status": status
                })

    return pd.DataFrame(records)
