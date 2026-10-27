"""Vérifi Streamlit application entry point."""

from __future__ import annotations

import base64
import io
from pathlib import Path

import streamlit as st

from verifi.benchmarks import BENCHMARKS, OBJECTIVE_IMPLICATIONS
from verifi.extraction import MANUAL_FIELDS, assess_quality, extract_from_excel, extract_from_pdf
from verifi.ratios import run_all_ratios
from verifi.report import escape_markdown_dollars, generate_report
from verifi.ui_content import (
     DOC_TYPE_HELP,
    FIELD_TOOLTIPS,
    PRIVACY_NOTICE_MD,
    RATIO_META,
    RATIO_TOOLTIPS,
    TREND_TOOLTIPS,
    badge_html,
    tip,
)

ROOT_DIR = Path(__file__).resolve().parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.png"
STYLES_PATH = ROOT_DIR / "assets" / "styles.css"
DEMO_FILE_PATH = ROOT_DIR / "demo_data" / "quebec_mfg_demo.xlsx"

st.set_page_config(
    page_title="Vérifi — SME Financial Due Diligence",
    page_icon="🔍",
    layout="centered",
)


def _logo_b64() -> str | None:
    if LOGO_PATH.exists():
        return base64.b64encode(LOGO_PATH.read_bytes()).decode()
    return None


def _load_css() -> str:
    if STYLES_PATH.exists():
        return STYLES_PATH.read_text(encoding="utf-8")
    return ""


_logo = _logo_b64()
_logo_html = (
    f'<img src="data:image/png;base64,{_logo}" style="height:64px; margin-right:1.2rem; vertical-align:middle;">'
    if _logo
    else "🔍"
)

st.markdown(
    f"""
<style>
{_load_css()}
</style>

<div class="verifi-header">
    {_logo_html}
    <div class="verifi-header-text">
        <h1>Vérifi</h1>
        <p>AI-powered financial due diligence for Quebec SME acquisitions</p>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Privacy notice ────────────────────────────────────────────────────────────
with st.expander("🔒 Privacy & Data Protection Notice (Law 25 / Quebec)"):
    st.markdown(PRIVACY_NOTICE_MD)

for key in [
    "data",
    "quality",
    "ratios",
    "report_text",
    "manual_mode",
    "industry",
    "objective",
    "buyer_context",
    "transaction_size",
    "years_operating",
    "financing",
    "doc_type",
    "years",
]:
    if key not in st.session_state:
        st.session_state[key] = None

# ── Step 1: Onboarding ────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Step 1 — Transaction Context")

    col1, col2 = st.columns(2)
    with col1:
        industry = st.selectbox("Industry", list(BENCHMARKS.keys()))
        bench = BENCHMARKS[industry]
        st.markdown(
            f'<div class="industry-hint">📊 For <b>{industry}</b>: {bench["emphasis_reason"]}</div>',
            unsafe_allow_html=True,
        )
        if bench.get("seasonal"):
            st.markdown(
                f'<div class="seasonal-warn">⚠️ {bench["seasonal_note"]}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        objective = st.radio(
            "Acquisition objective",
            ["Cash Flow", "Growth", "Asset Acquisition"],
            horizontal=True,
            help=FIELD_TOOLTIPS["Acquisition objective"],
        )
        transaction_size = st.radio(
            "Transaction size (revenue)",
            ["Under $500K", "$500K–$2M", "$2M–$5M"],
            horizontal=True,
            help=FIELD_TOOLTIPS["Transaction size"],
        )

    with col2:
        doc_type = st.radio(
            "Document type",
            ["Formal Financial Statements", "QuickBooks Export", "Excel / Other"],
            help=DOC_TYPE_HELP,
        )
        years = st.radio(
            "Years of data available",
            ["1 year", "2 years", "3 years"],
            horizontal=True,
            index=2,
        )
        years_operating = st.radio(
            "Years in operation",
            ["Under 5 years", "5–15 years", "15+ years"],
            horizontal=True,
            index=1,
            help=FIELD_TOOLTIPS["Years in operation"],
        )
        financing = st.radio(
            "Financing structure",
            ["All Cash", "Bank Financing", "Seller Financing", "Mixed"],
            horizontal=True,
            help=FIELD_TOOLTIPS["Financing structure"],
        )

    st.markdown(
        "**What matters most to you in this acquisition?** *(optional — improves your report)*"
    )
    buyer_context = st.text_area(
        "buyer_context_input",
        placeholder=(
            "Example: I am concerned about key-person risk and whether the business can run "
            "without the current owner. I am also worried about customer concentration."
        ),
        height=90,
        label_visibility="collapsed",
    )

    uploaded_file = st.file_uploader(
        "Upload financial document (PDF or Excel)",
        type=["pdf", "xlsx", "xls"],
    )

btn_col1, btn_col2 = st.columns([2, 1])
with btn_col1:
    analyze_clicked = st.button("🔍 Analyze Document", type="primary", use_container_width=True)
with btn_col2:
    demo_clicked = st.button(
        "🧪 Load Quebec SME Demo",
        use_container_width=True,
        help="Run the forensic pipeline on Les Industries Beaumont Inc. (2021–2023 manufacturing financials).",
    )


def _run_analysis_pipeline(
    raw_data: dict[str, list[float]],
    selected_industry: str,
    selected_objective: str,
    selected_doc_type: str,
    selected_years: str,
    selected_tx_size: str,
    selected_years_op: str,
    selected_financing: str,
    selected_buyer_context: str,
) -> None:
    quality = assess_quality(raw_data, selected_years)
    st.session_state.quality = quality
    st.session_state.data = raw_data
    st.session_state.industry = selected_industry
    st.session_state.objective = selected_objective
    st.session_state.buyer_context = selected_buyer_context
    st.session_state.transaction_size = selected_tx_size
    st.session_state.years_operating = selected_years_op
    st.session_state.financing = selected_financing
    st.session_state.doc_type = selected_doc_type
    st.session_state.years = selected_years
    st.session_state.report_text = None

    core_count = sum(
        [
            "revenue" in raw_data,
            "gross_profit" in raw_data or ("cogs" in raw_data and "revenue" in raw_data),
            "net_income" in raw_data,
            "operating_cash_flow" in raw_data,
            "accounts_receivable" in raw_data,
        ]
    )
    if core_count < 3:
        st.session_state.manual_mode = True
        st.session_state.ratios = None
    else:
        st.session_state.manual_mode = False
        with st.spinner("Calculating ratios..."):
            st.session_state.ratios = run_all_ratios(raw_data, selected_industry)


# ── Analysis pipeline ─────────────────────────────────────────────────────────
if demo_clicked:
    if DEMO_FILE_PATH.exists():
        with st.spinner("Loading demo financials (Les Industries Beaumont Inc.)..."):
            demo_raw = extract_from_excel(DEMO_FILE_PATH)
        _run_analysis_pipeline(
            raw_data=demo_raw,
            selected_industry=industry,
            selected_objective=objective,
            selected_doc_type="Excel / Other",
            selected_years="3 years",
            selected_tx_size=transaction_size,
            selected_years_op=years_operating,
            selected_financing=financing,
            selected_buyer_context=buyer_context,
        )
    else:
        st.error("Demo file not found in demo_data/quebec_mfg_demo.xlsx.")
elif analyze_clicked and uploaded_file:
    file_bytes = io.BytesIO(uploaded_file.read())
    ext = uploaded_file.name.split(".")[-1].lower()
    with st.spinner("Extracting data..."):
        raw = extract_from_pdf(file_bytes) if ext == "pdf" else extract_from_excel(file_bytes)

    _run_analysis_pipeline(
        raw_data=raw,
        selected_industry=industry,
        selected_objective=objective,
        selected_doc_type=doc_type,
        selected_years=years,
        selected_tx_size=transaction_size,
        selected_years_op=years_operating,
        selected_financing=financing,
        selected_buyer_context=buyer_context,
    )
elif analyze_clicked and not uploaded_file:
    st.warning("Please upload a financial document before analyzing, or click 'Load Quebec SME Demo'.")

# ── Manual fallback ───────────────────────────────────────────────────────────
if st.session_state.manual_mode:
    st.warning("Automatic extraction found fewer than 3 key line items. Please enter data manually.")
    n_years = int(years.split()[0])
    year_labels = [f"Year {i + 1}" for i in range(n_years)]
    manual_data: dict[str, list[float]] = {}
    with st.form("manual_input"):
        st.subheader("Manual Data Entry")
        for key, label in MANUAL_FIELDS:
            cols = st.columns(n_years)
            vals: list[float] = []
            for i, col in enumerate(cols):
                with col:
                    v = st.number_input(
                        f"{label} ({year_labels[i]})",
                        value=0,
                        step=1000,
                        format="%d",
                        key=f"{key}_{i}",
                    )
                    vals.append(float(v))
            if any(v != 0 for v in vals):
                manual_data[key] = vals
        if st.form_submit_button("Run Analysis", type="primary"):
            st.session_state.manual_mode = False
            st.session_state.data = manual_data
            st.session_state.quality = assess_quality(manual_data, years)
            with st.spinner("Calculating ratios..."):
                st.session_state.ratios = run_all_ratios(manual_data, industry)

# ── Step 2: Data Quality ──────────────────────────────────────────────────────
if st.session_state.quality:
    q = st.session_state.quality
    with st.container(border=True):
        st.subheader("Step 2 — Data Quality Assessment")

        c1, c2, c3 = st.columns(3)
        c1.metric("Income Statement", "✅ Found" if q["has_income_stmt"] else "❌ Not found")
        c2.metric("Balance Sheet", "✅ Found" if q["has_balance"] else "❌ Not found")
        c3.metric("Cash Flow Data", "✅ Found" if q["has_cash_flow"] else "❌ Not found")

        all_keys = [
            "revenue",
            "gross_profit",
            "net_income",
            "operating_cash_flow",
            "accounts_receivable",
            "owner_comp",
            "ebitda",
            "interest",
        ]
        data = st.session_state.data or {}
        found_count = sum(1 for k in all_keys if k in data)
        total = len(all_keys)

        reliable_labels: list[str] = []
        if "gross_profit" in data or "cogs" in data:
            reliable_labels.append("gross margin")
        if "accounts_receivable" in data:
            reliable_labels.append("receivables")
        if "ebitda" in data:
            reliable_labels.append("EBITDA")

        estimates: list[str] = []
        if "operating_cash_flow" not in data:
            estimates.append("cash flow")
        if "owner_comp" not in data:
            estimates.append("owner compensation")

        reliable_str = ", ".join(reliable_labels) if reliable_labels else "none"
        confidence_text = (
            f"Analysis based on <b>{found_count} of {total}</b> key line items. "
            f"<b>Reliable findings:</b> {reliable_str}. "
            + (
                f"<b>Estimate only:</b> {', '.join(estimates)}."
                if estimates
                else "All findings are reliable."
            )
        )
        st.markdown(f'<div class="confidence-box">📋 {confidence_text}</div>', unsafe_allow_html=True)

        score_color = {"Sufficient": "green", "Partial": "orange", "Insufficient": "red"}[
            q["score"]
        ]
        st.markdown(f"**Overall data quality:** :{score_color}[{q['score']}]")

        if q["missing"]:
            st.info("**Request from seller:**\n\n" + "\n".join(f"- {m}" for m in q["missing"]))
        else:
            st.success("All key financial data was successfully extracted.")

        st.markdown(
            '<div class="missing-flag">⚠️ <b>Revenue concentration data not available</b> — '
            "request customer breakdown from seller. A single customer representing 30%+ of "
            "revenue is a material acquisition risk not visible in financial statements.</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="missing-flag">⚠️ <b>Revenue per employee not available</b> — '
            "request headcount from seller to assess operational productivity and key-person dependency.</div>",
            unsafe_allow_html=True,
        )

# ── Step 3: Ratio Analysis ────────────────────────────────────────────────────
if st.session_state.ratios:
    ratios = st.session_state.ratios
    objective = st.session_state.objective or objective
    ind = st.session_state.industry or industry
    bench = BENCHMARKS[ind]

    with st.container(border=True):
        st.subheader("Step 3 — Ratio Analysis")
        st.caption(
            f"Findings ordered by priority for a **{objective}** acquisition in **{ind}**. "
            "Hover over any title, badge, or trend for definitions."
        )

        priority_order = bench["objective_priority"].get(objective, list(RATIO_META.keys()))
        implications = OBJECTIVE_IMPLICATIONS.get(objective, {})

        for key in priority_order:
            if key not in RATIO_META or key not in ratios:
                continue
            meta = RATIO_META[key]
            r = ratios[key]
            sev = r.get("severity", "unknown")
            trend = r.get("trend", "flat")
            tooltip = RATIO_TOOLTIPS.get(key, "")
            desc_fn = meta["desc"]
            desc = desc_fn(r) if callable(desc_fn) else str(desc_fn)
            implication = implications.get(key, "")

            if trend == "flat":
                trend_label = "Stable"
                trend_style = "color:#7d6608;"
            elif key in ("dso", "revenue_receivables"):
                trend_label = "Worsening" if trend == "up" else "Improving"
                trend_style = "color:#922b21;" if trend == "up" else "color:#1a6b5a;"
            else:
                trend_label = "Improving" if trend == "up" else "Worsening"
                trend_style = "color:#1a6b5a;" if trend == "up" else "color:#922b21;"

            arrow = "⬆" if trend == "up" else ("⬇" if trend == "down" else "→")
            trend_tip = TREND_TOOLTIPS.get(trend_label, "")

            ratio_tip_html = tip(f'<b>{meta["label"]}</b>', tooltip)
            badge = badge_html(sev)
            trend_tip_html = (
                f'<span class="trend-tag tip" style="{trend_style}">'
                f'{arrow} {trend_label}<span class="tiptext">{trend_tip}</span></span>'
            )

            st.markdown(
                f"""
            <div class="ratio-row">
                <div style="display:flex; align-items:center; gap:0.7rem; flex-wrap:wrap; margin-bottom:0.3rem;">
                    {ratio_tip_html}
                    {badge}
                    {trend_tip_html}
                </div>
                <div style="color:#333; font-size:0.9rem;">{desc}</div>
                {f'<div class="ratio-implication">For a {objective} buyer: {implication}</div>' if implication else ''}
            </div>
            """,
                unsafe_allow_html=True,
            )

    if st.button("📄 Generate AI Due Diligence Report", type="primary", use_container_width=True):
        q = st.session_state.quality or {}
        with st.spinner("Generating report..."):
            try:
                report_text = generate_report(
                    industry=ind,
                    objective=objective,
                    doc_type=st.session_state.get("doc_type", doc_type),
                    years=st.session_state.get("years", years),
                    quality=q.get("score", "Unknown"),
                    ratios=ratios,
                    transaction_size=st.session_state.get("transaction_size", transaction_size),
                    years_operating=st.session_state.get("years_operating", years_operating),
                    financing=st.session_state.get("financing", financing),
                    buyer_context=st.session_state.get("buyer_context", ""),
                )
                st.session_state.report_text = report_text
            except Exception as e:
                st.error(f"Report generation failed: {e}")

# ── Step 4: Report + CPA ──────────────────────────────────────────────────────
if st.session_state.report_text:
    with st.container(border=True):
        st.subheader("Step 4 — Due Diligence Report")

        st.markdown(
            """
        <div class="ai-disclaimer">
            ⚠️ <b>Preliminary AI-Generated Report</b> — This report was produced automatically by Vérifi's AI
            analysis engine based on the financial data you submitted. It has <b>not yet been reviewed by a
            licensed CPA</b>. Do not rely on it as a final due diligence opinion. Your final report, including
            a CPA advisory memo, will be delivered within 48 hours of submission.
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(escape_markdown_dollars(st.session_state.report_text))

    st.markdown(
        """
    <div class="cpa-banner">
        <h3>📋 CPA Advisory Review — Next Step</h3>
        <p>Your AI-generated report has been submitted for review by a licensed Quebec CPA.
        Within 48 hours you will receive a <b>CPA advisory memo</b> contextualizing these findings
        with professional judgment. This is an advisory consultation, not an audit or assurance engagement.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("📅 Schedule Included 1-Hour CPA Consultation", use_container_width=True):
        st.info(
            "Consultation scheduling coming soon. A CPA will contact you at your registered email within 24 hours."
        )

    st.download_button(
        label="⬇️ Download Preliminary Report",
        data=st.session_state.report_text,
        file_name="verifi_preliminary_report.md",
        mime="text/markdown",
        use_container_width=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="footer">
    🔒 Vérifi complies with Quebec Law 25 and applicable Canadian privacy legislation.
    Financial data is transmitted securely to Anthropic's API for report generation and is not stored by Vérifi.
    This platform does not provide legal, accounting, or investment advice. © 2026 Vérifi
</div>
""",
    unsafe_allow_html=True,
)
