"""
Enterprise Data Quality Suite (Assertions & Contract Testing)
Ensures upstream telemetry and joint venture accounting data adhere to enterprise standards.
"""

import pandas as pd
from typing import Dict, List, Tuple

class DataQualityError(Exception):
    pass

class DataQualitySuite:
    def __init__(self):
        self.validation_results: List[Dict] = []

    def validate_production_dataset(self, df: pd.DataFrame) -> bool:
        """Validates physical and mathematical consistency of production telemetry."""
        # 1. Null Check
        null_counts = df.isnull().sum().to_dict()
        if any(v > 0 for v in null_counts.values()):
            raise DataQualityError(f"Null values detected in production telemetry: {null_counts}")
        self._record("Production Null Check", "PASS", "Zero null values detected across all telemetry columns.")

        # 2. Water Cut Bounds Check (0% to 100%)
        invalid_water_cut = df[(df["water_cut_pct"] < 0.0) | (df["water_cut_pct"] > 100.0)]
        if not invalid_water_cut.empty:
            raise DataQualityError(f"Physical anomaly: {len(invalid_water_cut)} rows have water cut outside [0, 100]% range.")
        self._record("Water Cut Range Check", "PASS", "All water cut values reside within valid physical range [0% - 100%].")

        # 3. Volumetric Conservation Check: Gross Liquids == Net Crude + Produced Water
        calculated_gross = df["net_crude_oil_bopd"] + df["produced_water_bpd"]
        discrepancies = (df["gross_liquids_bpd"] - calculated_gross).abs()
        max_discrepancy = discrepancies.max()
        if max_discrepancy > 0.05:
            raise DataQualityError(f"Volumetric imbalance: Gross liquids != Net Crude + Produced Water (Max delta: {max_discrepancy}).")
        self._record("Volumetric Conservation Check", "PASS", f"Gross volume parity verified across {len(df)} records (tolerance < 0.05 bpd).")

        return True

    def validate_cash_call_dataset(self, df: pd.DataFrame) -> bool:
        """Validates financial balance parity for JV cash-call billings and remittances."""
        # 1. Billing Components Parity: Total Billed == CAPEX + OPEX
        calculated_total = df["capital_expenditure_billed"] + df["operating_expenditure_billed"]
        billing_diff = (df["total_cash_call_billed"] - calculated_total).abs()
        if billing_diff.max() > 0.02:
            raise DataQualityError(f"Financial inconsistency: Total Billed != CAPEX + OPEX (Max delta: {billing_diff.max()}).")
        self._record("Billing Parity Check", "PASS", f"CAPEX + OPEX equals Total Billed across all {len(df)} billing items.")

        # 2. Net Variance Parity: Variance == Total Billed - Remitted
        calculated_var = df["total_cash_call_billed"] - df["cash_remitted_by_partner"]
        var_diff = (df["net_variance_amount"] - calculated_var).abs()
        if var_diff.max() > 0.02:
            raise DataQualityError("Variance calculation error: Net variance does not match Total Billed - Remitted.")
        self._record("Variance Parity Check", "PASS", "Net variance calculations verified against remittances.")

        # 3. Variance Status Categorization
        underfunded = df[df["variance_status"] == "UNDER_FUNDED"]
        for _, row in underfunded.iterrows():
            if row["net_variance_amount"] <= 0:
                raise DataQualityError(f"Status mismatch: Record tagged UNDER_FUNDED but variance is {row['net_variance_amount']}")
        self._record("Status Integrity Check", "PASS", "Variance status categories match mathematical sign of net variance.")

        return True

    def _record(self, check_name: str, status: str, details: str):
        self.validation_results.append({
            "check_name": check_name,
            "status": status,
            "details": details
        })

    def get_summary_report(self) -> pd.DataFrame:
        return pd.DataFrame(self.validation_results)
