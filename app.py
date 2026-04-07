import io
import streamlit as st
from extraction import extract_from_excel, extract_from_pdf, assess_quality, MANUAL_FIELDS
from ratios import run_all_ratios
from report import generate_report
from benchmarks import BENCHMARKS, OBJECTIVE_IMPLICATIONS

st.set_page_config(page_title="Vérifi — SME Financial Due Diligence", page_icon="🔍", layout="centered")

import base64

def _logo_b64():
    try:
        with open("Verifi_logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

_logo = _logo_b64()
_logo_html = (
    f'<img src="data:image/png;base64,{_logo}" style="height:64px; margin-right:1.2rem; vertical-align:middle; background:transparent;">'
    if _logo else '🔍'
)

st.markdown(f"""
<style>
/* ── Base palette ──────────────────────────────────────────────── */
:root {{
    --navy:   #1B365D;
    --teal:   #20B2AA;
    --grey:   #4A4A4A;
    --white:  #FFFFFF;
    --bg-alt: #F0F4F8;
    --sage:   #E8F1F0;
    --border: #D6E4F0;
}}

/* ── Header ────────────────────────────────────────────────────── */
.verifi-header {{
    background: linear-gradient(135deg, #1B365D 0%, #1e4d7b 60%, #20B2AA 100%);
    padding: 1.6rem 2rem; border-radius: 12px;
    margin-bottom: 1.5rem; color: white;
    display: flex; align-items: center;
    box-shadow: 0 4px 16px rgba(27,54,93,0.18);
}}
.verifi-header-text h1 {{
    color: white; margin: 0; font-size: 2rem; letter-spacing: -0.5px;
}}
.verifi-header-text p {{
    color: rgba(255,255,255,0.75); margin: 0.2rem 0 0; font-size: 0.95rem;
}}

/* ── Cards ─────────────────────────────────────────────────────── */
.section-card {{
    background: var(--white); border-radius: 10px; padding: 1.5rem;
    margin-bottom: 1.5rem; border: 1px solid var(--border);
    box-shadow: 0 1px 4px rgba(27,54,93,0.07);
}}

/* ── Industry hint ─────────────────────────────────────────────── */
.industry-hint {{
    background: var(--sage); border-left: 4px solid var(--teal);
    padding: 0.7rem 1rem; border-radius: 0 8px 8px 0;
    font-size: 0.88rem; color: var(--navy); margin-top: 0.5rem;
}}

/* ── Confidence box ────────────────────────────────────────────── */
.confidence-box {{
    background: var(--sage); border: 1px solid var(--teal);
    border-radius: 8px; padding: 0.8rem 1rem; margin-top: 0.8rem;
    font-size: 0.9rem; color: var(--navy);
}}

/* ── Severity badges ───────────────────────────────────────────── */
.badge-red     {{ background:#fadbd8; color:#7b241c; padding:3px 12px; border-radius:20px; font-weight:700; font-size:0.8rem; display:inline-block; }}
.badge-yellow  {{ background:#fef9e7; color:#7d6608; padding:3px 12px; border-radius:20px; font-weight:700; font-size:0.8rem; display:inline-block; }}
.badge-green   {{ background:var(--sage); color:#1a6b5a; padding:3px 12px; border-radius:20px; font-weight:700; font-size:0.8rem; display:inline-block; }}
.badge-unknown {{ background:#eaecee; color:#555; padding:3px 12px; border-radius:20px; font-weight:700; font-size:0.8rem; display:inline-block; }}

/* ── Ratio rows ────────────────────────────────────────────────── */
.ratio-row {{ padding: 0.9rem 0; border-bottom: 1px solid #eef2f7; }}
.ratio-implication {{ font-size:0.83rem; color:#4A5568; font-style:italic; margin-top:0.25rem; }}

/* ── CPA banner ────────────────────────────────────────────────── */
.cpa-banner {{
    background: linear-gradient(135deg, #1B365D 0%, #20B2AA 100%);
    border-radius: 10px; padding: 1.5rem 2rem; color: white; margin-top: 2rem;
    box-shadow: 0 4px 16px rgba(27,54,93,0.18);
}}
.cpa-banner h3 {{ color: white; margin: 0 0 0.5rem; }}
.cpa-banner p  {{ color: rgba(255,255,255,0.8); margin: 0; font-size: 0.95rem; }}

/* ── Warning / gap flags ───────────────────────────────────────── */
.seasonal-warn {{
    background: #fef9e7; border-left: 4px solid #f39c12;
    padding: 0.6rem 1rem; border-radius: 0 6px 6px 0;
    font-size: 0.85rem; color: #7d6608; margin-top: 0.5rem;
}}
.missing-flag {{
    background: #f8f9fa; border: 1px dashed #b0bec5;
    border-radius: 8px; padding: 0.6rem 1rem;
    font-size: 0.85rem; color: #555; margin-top: 0.4rem;
}}

/* ── Streamlit overrides ───────────────────────────────────────── */
div[data-testid="stButton"] button[kind="primary"] {{
    background-color: var(--teal) !important;
    border-color: var(--teal) !important;
    color: white !important;
}}
div[data-testid="stButton"] button[kind="primary"]:hover {{
    background-color: #189e97 !important;
    border-color: #189e97 !important;
}}
</style>

<div class="verifi-header">
    {_logo_html}
    <div class="verifi-header-text">
        <h1>Vérifi</h1>
        <p>AI-powered financial due diligence for Quebec SME acquisitions</p>
    </div>
</div>
""", unsafe_allow_html=True)

for key in ["data","quality","ratios","report_text","manual_mode","industry","objective"]:
    if key not in st.session_state:
        st.session_state[key] = None

BADGES = {
    "red":     '<span class="badge-red">🔴 HIGH RISK</span>',
    "yellow":  '<span class="badge-yellow">🟡 CAUTION</span>',
    "green":   '<span class="badge-green">🟢 NORMAL</span>',
    "unknown": '<span class="badge-unknown">⚪ INSUFFICIENT DATA</span>',
}
TREND_ARROW = {"up": "↑", "down": "↓", "flat": "→"}

# ── Ratio display metadata ────────────────────────────────────────────────────
RATIO_META = {
    "gross_margin": {
        "label": "Gross Margin Consistency",
        "desc": lambda r: f"Margin ranged {r.get('min')}% to {r.get('max')}% — variance of {r.get('variance_pp')} pp." if r.get("available") else "Insufficient data.",
    },
    "revenue_receivables": {
        "label": "Revenue vs. Receivables Divergence",
        "desc": lambda r: f"Receivables grew {r.get('max_divergence_pp')} pp faster than revenue." if r.get("available") else "Insufficient data.",
    },
    "cash_accrual": {
        "label": "Cash vs. Accrual Divergence",
        "desc": lambda r: ("Net income positive while OCF negative in at least one year." if r.get("ni_positive_ocf_negative") else f"Max NI-OCF gap: {r.get('max_divergence_pct_rev')}% of revenue.") if r.get("available") else "Insufficient data.",
    },
    "owner_comp": {
        "label": "Owner Compensation",
        "desc": lambda r: f"Avg {r.get('avg_pct')}% of revenue — benchmark: {r.get('benchmark_range',('?','?'))[0]} to {r.get('benchmark_range',('?','?'))[1]}." if r.get("available") else "Insufficient data.",
    },
    "ebitda_stability": {
        "label": "EBITDA Stability",
        "desc": lambda r: f"Largest YoY swing: {r.get('max_swing_pct')}%." if r.get("available") else "Insufficient data.",
    },
    "dso": {
        "label": "Days Sales Outstanding (DSO)",
        "desc": lambda r: f"Latest DSO: {r.get('latest')} days — industry benchmark: {r.get('benchmark_range',('?','?'))[0]}–{r.get('benchmark_range',('?','?'))[1]} days." if r.get("available") else "Insufficient data.",
    },
    "interest_coverage": {
        "label": "Interest Coverage",
        "desc": lambda r: f"Latest coverage: {r.get('latest')}x EBITDA/interest — minimum acceptable: 2.0x." if r.get("available") else "Insufficient data.",
    },
}

# ── Step 1: Onboarding ────────────────────────────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Step 1 — Transaction Context")

col1, col2 = st.columns(2)
with col1:
    industry = st.selectbox("Industry", list(BENCHMARKS.keys()))
    bench = BENCHMARKS[industry]
    st.markdown(f'<div class="industry-hint">📊 For <b>{industry}</b>: {bench["emphasis_reason"]}</div>', unsafe_allow_html=True)
    if bench.get("seasonal"):
        st.markdown(f'<div class="seasonal-warn">⚠️ {bench["seasonal_note"]}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    objective = st.radio("Acquisition objective", ["Cash Flow", "Growth", "Asset Acquisition"], horizontal=True)
    transaction_size = st.radio("Transaction size (revenue)", ["Under \$500K", "\$500K–\$2M", "\$2M–\$5M"], horizontal=True)

with col2:
    doc_type = st.radio("Document type", ["Formal Financial Statements", "QuickBooks Export", "Excel / Other"])
    years = st.radio("Years of data available", ["1 year", "2 years", "3 years"], horizontal=True, index=2)
    years_operating = st.radio("Years in operation", ["Under 5 years", "5–15 years", "15+ years"], horizontal=True, index=1)
    financing = st.radio("Financing structure", ["All Cash", "Bank Financing", "Seller Financing", "Mixed"], horizontal=True)

uploaded_file = st.file_uploader("Upload financial document (PDF or Excel)", type=["pdf","xlsx","xls"])
st.markdown('</div>', unsafe_allow_html=True)

analyze_clicked = st.button("🔍 Analyze Document", type="primary", use_container_width=True)

# ── Analysis pipeline ─────────────────────────────────────────────────────────
if analyze_clicked and uploaded_file:
    file_bytes = io.BytesIO(uploaded_file.read())
    ext = uploaded_file.name.split(".")[-1].lower()
    with st.spinner("Extracting data..."):
        raw = extract_from_pdf(file_bytes) if ext == "pdf" else extract_from_excel(file_bytes)

    quality = assess_quality(raw, years)
    st.session_state.quality   = quality
    st.session_state.data      = raw
    st.session_state.industry  = industry
    st.session_state.objective = objective

    core_count = sum([
        "revenue" in raw,
        "gross_profit" in raw or ("cogs" in raw and "revenue" in raw),
        "net_income" in raw,
        "operating_cash_flow" in raw,
        "accounts_receivable" in raw,
    ])
    if core_count < 3:
        st.session_state.manual_mode = True
    else:
        st.session_state.manual_mode = False
        with st.spinner("Calculating ratios..."):
            st.session_state.ratios = run_all_ratios(raw, industry)

elif analyze_clicked and not uploaded_file:
    st.warning("Please upload a financial document before analyzing.")

# ── Manual fallback ───────────────────────────────────────────────────────────
if st.session_state.manual_mode:
    st.warning("Automatic extraction found fewer than 3 key line items. Please enter data manually.")
    n_years = int(years.split()[0])
    year_labels = [f"Year {i+1}" for i in range(n_years)]
    manual_data = {}
    with st.form("manual_input"):
        st.subheader("Manual Data Entry")
        for key, label in MANUAL_FIELDS:
            cols = st.columns(n_years)
            vals = []
            for i, col in enumerate(cols):
                with col:
                    v = st.number_input(f"{label} ({year_labels[i]})", value=0, step=1000, format="%d", key=f"{key}_{i}")
                    vals.append(float(v))
            manual_data[key] = vals
        if st.form_submit_button("Run Analysis", type="primary"):
            st.session_state.manual_mode = False
            st.session_state.data    = manual_data
            st.session_state.quality = assess_quality(manual_data, years)
            with st.spinner("Calculating ratios..."):
                st.session_state.ratios = run_all_ratios(manual_data, industry)

# ── Step 2: Data Quality ──────────────────────────────────────────────────────
if st.session_state.quality:
    q = st.session_state.quality
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Step 2 — Data Quality Assessment")

    c1, c2, c3 = st.columns(3)
    c1.metric("Income Statement", "✅ Found" if q["has_income_stmt"] else "❌ Not found")
    c2.metric("Balance Sheet",    "✅ Found" if q["has_balance"]     else "❌ Not found")
    c3.metric("Cash Flow Data",   "✅ Found" if q["has_cash_flow"]   else "❌ Not found")

    # Concrete confidence score
    all_keys = ["revenue","gross_profit","net_income","operating_cash_flow",
                "accounts_receivable","owner_comp","ebitda","interest"]
    data = st.session_state.data or {}
    found_count = sum(1 for k in all_keys if k in data)
    total = len(all_keys)

    reliable = [k for k in ["gross_margin","accounts_receivable","ebitda"] if k in data or "gross_profit" in data]
    reliable_labels = []
    if "gross_profit" in data or "cogs" in data: reliable_labels.append("gross margin")
    if "accounts_receivable" in data:            reliable_labels.append("receivables")
    if "ebitda" in data:                         reliable_labels.append("EBITDA")

    estimates = []
    if "operating_cash_flow" not in data: estimates.append("cash flow")
    if "owner_comp" not in data:          estimates.append("owner compensation")

    reliable_str  = ", ".join(reliable_labels) if reliable_labels else "none"
    estimates_str = ", ".join(estimates) if estimates else "none"

    confidence_text = (
        f"Analysis based on <b>{found_count} of {total}</b> key line items. "
        f"<b>Reliable findings:</b> {reliable_str}. "
        + (f"<b>Estimate only:</b> {estimates_str}." if estimates else "All findings are reliable.")
    )
    st.markdown(f'<div class="confidence-box">📋 {confidence_text}</div>', unsafe_allow_html=True)

    score_color = {"Sufficient": "green", "Partial": "orange", "Insufficient": "red"}[q["score"]]
    st.markdown(f"**Overall data quality:** :{score_color}[{q['score']}]")

    if q["missing"]:
        st.info("**Request from seller:**\n\n" + "\n".join(f"- {m}" for m in q["missing"]))

    # Data gaps that cannot be computed from financials
    st.markdown('<div class="missing-flag">⚠️ <b>Revenue concentration data not available</b> — request customer breakdown from seller. A single customer representing 30%+ of revenue is a material acquisition risk not visible in financial statements.</div>', unsafe_allow_html=True)
    st.markdown('<div class="missing-flag">⚠️ <b>Revenue per employee not available</b> — request headcount from seller to assess operational productivity and key-person dependency.</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ── Step 3: Ratio Analysis ────────────────────────────────────────────────────
if st.session_state.ratios:
    ratios    = st.session_state.ratios
    objective = st.session_state.objective or objective
    ind       = st.session_state.industry  or industry
    bench     = BENCHMARKS[ind]

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Step 3 — Ratio Analysis")
    st.caption(f"Findings ordered by priority for a **{objective}** acquisition in **{ind}**.")

    # Reorder by objective priority
    priority_order = bench["objective_priority"].get(objective, list(RATIO_META.keys()))
    implications   = OBJECTIVE_IMPLICATIONS.get(objective, {})

    for key in priority_order:
        if key not in RATIO_META or key not in ratios:
            continue
        meta = RATIO_META[key]
        r    = ratios[key]
        sev  = r.get("severity", "unknown")
        badge = BADGES.get(sev, BADGES["unknown"])
        trend = r.get("trend", "flat")
        arrow = TREND_ARROW.get(trend, "→")

        # For DSO, rising is bad. For OCF, rising is good. Flip arrow meaning in desc.
        trend_color = ""
        if key in ("dso", "revenue_receivables"):
            trend_color = "🔴" if trend == "up" else "🟢" if trend == "down" else "⬜"
        elif key in ("cash_accrual", "ebitda_stability", "interest_coverage", "gross_margin"):
            trend_color = "🟢" if trend == "up" else "🔴" if trend == "down" else "⬜"

        desc        = meta["desc"](r)
        implication = implications.get(key, "")

        st.markdown(f"""
        <div class="ratio-row">
            <div style="display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap;">
                <span style="font-weight:700; min-width:230px;">{meta['label']}</span>
                {badge}
                <span style="font-size:1rem;" title="Trend">{trend_color} {arrow}</span>
            </div>
            <div style="color:#333; font-size:0.9rem; margin-top:0.3rem;">{desc}</div>
            {f'<div class="ratio-implication">→ For a {objective} buyer: {implication}</div>' if implication else ''}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Generate report ───────────────────────────────────────────────────────
    if st.button("📄 Generate AI Due Diligence Report", type="primary", use_container_width=True):
        q = st.session_state.quality or {}
        with st.spinner("Generating report..."):
            try:
                report_text = generate_report(
                    industry=ind, objective=objective,
                    doc_type=doc_type, years=years,
                    quality=q.get("score","Unknown"), ratios=ratios,
                    transaction_size=transaction_size,
                    years_operating=years_operating,
                    financing=financing,
                )
                st.session_state.report_text = report_text
            except Exception as e:
                st.error(f"Report generation failed: {e}")

# ── Step 4: Report + CPA ──────────────────────────────────────────────────────
if st.session_state.report_text:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Step 4 — Due Diligence Report")
    st.markdown(st.session_state.report_text)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="cpa-banner">
        <h3>📋 CPA Advisory Review</h3>
        <p>Your Vérifi report has been submitted for CPA advisory review.
        A licensed Quebec CPA will provide an advisory memo within 48 hours.
        This is an advisory consultation, not an assurance engagement.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("📅 Schedule Included 1-Hour CPA Consultation", use_container_width=True):
        st.info("Consultation scheduling coming soon. A CPA will contact you at your registered email within 24 hours.")

    st.download_button(
        label="⬇️ Download Report",
        data=st.session_state.report_text,
        file_name="verifi_due_diligence_report.txt",
        mime="text/plain",
        use_container_width=True,
    )
