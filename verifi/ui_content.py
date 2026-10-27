"""UI copy, tooltips, badges, and Law 25 privacy disclosures for the Vérifi Streamlit app."""

from __future__ import annotations

from typing import Any, Callable

PRIVACY_NOTICE_MD = """
**Your data is protected.** Vérifi is designed in compliance with Quebec's *Act respecting the protection of personal information in the private sector* (Law 25) and applicable Canadian privacy legislation.

**What we collect:** The financial documents you upload and the information you enter in this form.

**How it is used:** Your data is transmitted to Anthropic's Claude API solely to generate your due diligence report. It is used for no other purpose.

**Storage:** Vérifi does not store your documents or financial data. No information is retained after your session ends.

**Third-party processing:** Report generation is powered by Anthropic's API. Anthropic processes your data under their own privacy policy and does not use it to train models. See anthropic.com/privacy.

**Your rights:** Under Law 25, you have the right to access, correct, and request deletion of any personal information. Contact: privacy@verifi.ca

By uploading a document and clicking Analyze, you consent to this processing.
"""

BADGE_STYLE: dict[str, str] = {
    "red": "badge-red",
    "yellow": "badge-yellow",
    "green": "badge-green",
    "unknown": "badge-unknown",
}

BADGE_LABELS: dict[str, tuple[str, str]] = {
    "red": (
        "🔴 HIGH RISK",
        "This finding exceeds acceptable thresholds and requires investigation before proceeding.",
    ),
    "yellow": (
        "🟡 CAUTION",
        "This finding is outside the normal range. Ask the seller for an explanation.",
    ),
    "green": (
        "🟢 NORMAL",
        "This finding is within the expected range for this industry.",
    ),
    "unknown": (
        "⚪ INSUFFICIENT DATA",
        "Not enough data was found to calculate this ratio reliably.",
    ),
}

RATIO_TOOLTIPS: dict[str, str] = {
    "gross_margin": (
        "Gross Margin = (Revenue minus Cost of Goods Sold) / Revenue. Measures profit after "
        "direct production costs. Inconsistency across years suggests pricing problems, cost shocks, or manipulation."
    ),
    "revenue_receivables": (
        "Compares revenue growth to accounts receivable (money owed by customers) growth. "
        "If receivables grow faster, the business may be booking revenue it has not yet collected in cash."
    ),
    "cash_accrual": (
        "Compares net income (accounting profit) to operating cash flow (actual cash generated). "
        "A business can show profit on paper while running out of cash — a classic manipulation indicator."
    ),
    "owner_comp": (
        "The salary paid to the owner or officers. Below-market compensation inflates reported profit — "
        "the business looks more profitable than it really is because the owner is underpaying themselves."
    ),
    "ebitda_stability": (
        "EBITDA = Earnings Before Interest, Taxes, Depreciation and Amortization. "
        "The standard acquisition profit measure. Large year-over-year swings suggest earnings are not reliable or repeatable."
    ),
    "dso": (
        "Days Sales Outstanding = how many days it takes the business to collect payment from customers. "
        "High DSO means cash is tied up in unpaid invoices. Industry benchmark shown for comparison."
    ),
    "interest_coverage": (
        "EBITDA divided by interest expense. Measures whether the business generates enough profit "
        "to cover its debt payments. Below 2.0x is dangerously thin for a leveraged acquisition."
    ),
}

TREND_TOOLTIPS: dict[str, str] = {
    "Worsening": (
        "This metric has moved in a negative direction. The most recent year is worse "
        "than the earliest year in the data."
    ),
    "Improving": (
        "This metric has moved in a positive direction. The most recent year is better "
        "than the earliest year in the data."
    ),
    "Stable": (
        "This metric has remained relatively flat. Change is less than 3% between "
        "earliest and most recent year."
    ),
}

RATIO_META: dict[str, dict[str, str | Callable[[dict[str, Any]], str]]] = {
    "gross_margin": {
        "label": "Gross Margin Consistency",
        "desc": lambda r: (
            f"Margin ranged {r.get('min')}% to {r.get('max')}% — variance of {r.get('variance_pp')} pp."
            if r.get("available")
            else "Insufficient data."
        ),
    },
    "revenue_receivables": {
        "label": "Revenue vs. Receivables Divergence",
        "desc": lambda r: (
            f"Receivables grew {r.get('max_divergence_pp')} pp faster than revenue."
            if r.get("available")
            else "Insufficient data."
        ),
    },
    "cash_accrual": {
        "label": "Cash vs. Accrual Divergence",
        "desc": lambda r: (
            (
                "Net income positive while OCF negative in at least one year."
                if r.get("ni_positive_ocf_negative")
                else f"Max NI-OCF gap: {r.get('max_divergence_pct_rev')}% of revenue."
            )
            if r.get("available")
            else "Insufficient data."
        ),
    },
    "owner_comp": {
        "label": "Owner Compensation",
        "desc": lambda r: (
            f"Avg {r.get('avg_pct')}% of revenue — benchmark: "
            f"{r.get('benchmark_range', ('?', '?'))[0]} to {r.get('benchmark_range', ('?', '?'))[1]}."
            if r.get("available")
            else "Insufficient data."
        ),
    },
    "ebitda_stability": {
        "label": "EBITDA Stability",
        "desc": lambda r: (
            f"Largest YoY swing: {r.get('max_swing_pct')}%."
            if r.get("available")
            else "Insufficient data."
        ),
    },
    "dso": {
        "label": "Days Sales Outstanding (DSO)",
        "desc": lambda r: (
            f"Latest DSO: {r.get('latest')} days — industry benchmark: "
            f"{r.get('benchmark_range', ('?', '?'))[0]}–{r.get('benchmark_range', ('?', '?'))[1]} days."
            if r.get("available")
            else "Insufficient data."
        ),
    },
    "interest_coverage": {
        "label": "Interest Coverage",
        "desc": lambda r: (
            f"Latest coverage: {r.get('latest')}x EBITDA/interest — minimum acceptable: 2.0x."
            if r.get("available")
            else "Insufficient data."
        ),
    },
}

FIELD_TOOLTIPS: dict[str, str] = {
    "Transaction size": (
        "The approximate annual revenue of the business you are acquiring. Affects benchmarking — "
        "a $400K revenue business has different norms than a $3M one."
    ),
    "Years in operation": (
        "How long the business has been operating. A 3-year decline in a 30-year-old business "
        "signals something different than the same decline in a 4-year-old one."
    ),
    "Financing structure": (
        "How you plan to fund the acquisition. Bank financing makes interest coverage critical. "
        "All-cash buyers care less about debt service capacity."
    ),
    "Acquisition objective": (
        "What you are primarily buying. Cash Flow = stable distributions. Growth = you want to scale. "
        "Asset Acquisition = buying the underlying assets more than the earnings."
    ),
}

DOC_TYPE_HELP = (
    "Formal Financial Statements: professionally prepared by an accountant or auditor — highest reliability. "
    "QuickBooks Export: reliable for transactions but may lack accrual adjustments. "
    "Excel / Other: manually prepared — variable reliability, Vérifi will assess quality before analysis."
)


def tip(label: str, tooltip: str) -> str:
    return f'<span class="tip">{label}<span class="tiptext">{tooltip}</span></span>'


def badge_html(sev: str) -> str:
    cls = BADGE_STYLE.get(sev, "badge-unknown")
    label, tooltip = BADGE_LABELS.get(sev, BADGE_LABELS["unknown"])
    return f'<span class="{cls} tip">{label}<span class="tiptext">{tooltip}</span></span>'
