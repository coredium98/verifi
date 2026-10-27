"""Vérifi core package: financial statement extraction, forensic ratios, and report generation."""

from verifi.benchmarks import BENCHMARKS, OBJECTIVE_IMPLICATIONS
from verifi.extraction import MANUAL_FIELDS, assess_quality, extract_from_excel, extract_from_pdf
from verifi.ratios import run_all_ratios
from verifi.report import escape_markdown_dollars, generate_report

__all__ = [
    "BENCHMARKS",
    "MANUAL_FIELDS",
    "OBJECTIVE_IMPLICATIONS",
    "assess_quality",
    "escape_markdown_dollars",
    "extract_from_excel",
    "extract_from_pdf",
    "generate_report",
    "run_all_ratios",
]
