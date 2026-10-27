"""Tests for financial statement extraction and data quality grading."""

from __future__ import annotations

import unittest
from pathlib import Path

from verifi.extraction import assess_quality, extract_from_excel

ROOT_DIR = Path(__file__).resolve().parent.parent
DEMO_XLSX = ROOT_DIR / "demo_data" / "quebec_mfg_demo.xlsx"


class TestExtraction(unittest.TestCase):
    def test_extract_demo_workbook_completeness(self) -> None:
        data = extract_from_excel(DEMO_XLSX)
        expected_keys = {
            "revenue",
            "cogs",
            "gross_profit",
            "owner_comp",
            "depreciation",
            "ebitda",
            "interest",
            "tax",
            "net_income",
            "operating_cash_flow",
            "accounts_receivable",
        }
        self.assertTrue(expected_keys.issubset(set(data.keys())))
        self.assertEqual(data["revenue"], [1800000.0, 2016000.0, 2117000.0])
        self.assertEqual(data["gross_profit"], [684000.0, 584640.0, 613930.0])
        self.assertEqual(data["operating_cash_flow"], [190000.0, -19360.0, 71930.0])
        self.assertEqual(data["accounts_receivable"], [145000.0, 203000.0, 221000.0])

    def test_assess_quality_sufficient_on_demo(self) -> None:
        data = extract_from_excel(DEMO_XLSX)
        quality = assess_quality(data, "3 years")
        self.assertEqual(quality["score"], "Sufficient")
        self.assertTrue(quality["has_income_stmt"])
        self.assertTrue(quality["has_balance"])
        self.assertTrue(quality["has_cash_flow"])
        self.assertEqual(quality["years_claimed"], 3)
        self.assertEqual(quality["years_found"], 3)
        self.assertEqual(quality["missing"], [])

    def test_assess_quality_detects_missing_historical_years(self) -> None:
        single_year_data = {
            "revenue": [1000000.0],
            "gross_profit": [350000.0],
            "net_income": [120000.0],
            "operating_cash_flow": [110000.0],
            "accounts_receivable": [95000.0],
            "owner_comp": [80000.0],
        }
        quality = assess_quality(single_year_data, "3 years")
        self.assertEqual(quality["score"], "Partial")
        self.assertEqual(quality["years_claimed"], 3)
        self.assertEqual(quality["years_found"], 1)
        self.assertTrue(any("1 of 3 years found" in item for item in quality["missing"]))


if __name__ == "__main__":
    unittest.main()
