"""Tests for the 7 forensic due diligence ratios and report helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from verifi.extraction import extract_from_excel
from verifi.ratios import (
    calc_cash_accrual,
    calc_dso,
    calc_ebitda_stability,
    calc_gross_margin,
    calc_interest_coverage,
    calc_owner_comp,
    calc_revenue_receivables,
    run_all_ratios,
)
from verifi.report import build_prompt, escape_markdown_dollars

ROOT_DIR = Path(__file__).resolve().parent.parent
DEMO_XLSX = ROOT_DIR / "demo_data" / "quebec_mfg_demo.xlsx"


class TestForensicRatios(unittest.TestCase):
    def test_demo_workbook_triggers_expected_forensic_flags(self) -> None:
        data = extract_from_excel(DEMO_XLSX)
        ratios = run_all_ratios(data, "Manufacturing")

        self.assertEqual(ratios["gross_margin"]["severity"], "red")
        self.assertEqual(ratios["gross_margin"]["variance_pp"], 9.0)

        self.assertEqual(ratios["revenue_receivables"]["severity"], "red")
        self.assertEqual(ratios["revenue_receivables"]["max_divergence_pp"], 28.0)
        self.assertEqual(ratios["revenue_receivables"]["trend"], "up")

        self.assertEqual(ratios["cash_accrual"]["severity"], "red")
        self.assertTrue(ratios["cash_accrual"]["ni_positive_ocf_negative"])

        self.assertEqual(ratios["owner_comp"]["severity"], "red")
        self.assertEqual(ratios["owner_comp"]["comp_gap"], 57850)

        self.assertEqual(ratios["ebitda_stability"]["severity"], "red")
        self.assertEqual(ratios["dso"]["severity"], "green")
        self.assertEqual(ratios["interest_coverage"]["severity"], "green")

    def test_ebitda_reconstruction_when_ebitda_line_missing(self) -> None:
        data = {
            "net_income": [100000.0, 105000.0],
            "depreciation": [20000.0, 20000.0],
            "tax": [15000.0, 15000.0],
            "interest": [10000.0, 10000.0],
        }
        ebitda_res = calc_ebitda_stability(data)
        cov_res = calc_interest_coverage(data)

        self.assertTrue(ebitda_res["available"])
        self.assertEqual(ebitda_res["values"], [145000.0, 150000.0])
        self.assertEqual(ebitda_res["severity"], "green")

        self.assertTrue(cov_res["available"])
        self.assertEqual(cov_res["values"], [14.5, 15.0])
        self.assertEqual(cov_res["severity"], "green")

    def test_healthy_manufacturing_profile_all_green(self) -> None:
        healthy = {
            "revenue": [2000000.0, 2100000.0, 2200000.0],
            "gross_profit": [700000.0, 735000.0, 770000.0],
            "accounts_receivable": [220000.0, 230000.0, 240000.0],
            "net_income": [240000.0, 255000.0, 270000.0],
            "operating_cash_flow": [250000.0, 260000.0, 280000.0],
            "owner_comp": [160000.0, 168000.0, 176000.0],
            "ebitda": [340000.0, 355000.0, 370000.0],
            "interest": [40000.0, 380000.0 / 10, 35000.0],
        }
        self.assertEqual(calc_gross_margin(healthy)["severity"], "green")
        self.assertEqual(calc_revenue_receivables(healthy)["severity"], "green")
        self.assertEqual(calc_cash_accrual(healthy)["severity"], "green")
        self.assertEqual(calc_owner_comp(healthy, "Manufacturing")["severity"], "green")
        self.assertEqual(calc_ebitda_stability(healthy)["severity"], "green")
        self.assertEqual(calc_dso(healthy, "Manufacturing")["severity"], "green")
        self.assertEqual(calc_interest_coverage(healthy)["severity"], "green")

    def test_report_escape_and_prompt_builder(self) -> None:
        raw = "Normalized EBITDA is $145,930 after a $57,850 adjustment."
        escaped = escape_markdown_dollars(raw)
        self.assertEqual(escaped, r"Normalized EBITDA is \$145,930 after a \$57,850 adjustment.")
        # Idempotent if called twice
        self.assertEqual(escape_markdown_dollars(escaped), escaped)

        data = extract_from_excel(DEMO_XLSX)
        ratios = run_all_ratios(data, "Manufacturing")
        prompt = build_prompt(
            industry="Manufacturing",
            objective="Cash Flow",
            doc_type="Excel / Other",
            years="3 years",
            quality="Sufficient",
            ratios=ratios,
            transaction_size="$2M–$5M",
            years_operating="5–15 years",
            financing="Bank Financing",
            buyer_context="Worried about customer concentration.",
        )
        self.assertIn("BUYER'S STATED PRIORITIES:", prompt)
        self.assertIn("Gross Margin Consistency: [RED]", prompt)


if __name__ == "__main__":
    unittest.main()
