import anthropic
from benchmarks import BENCHMARKS

def _fmt_ratio(name, result):
    if not result.get("available"):
        return f"{name}: Data not available"
    s = result.get("severity", "unknown").upper()
    lines = [f"{name}: [{s}]"]
    if name == "Gross Margin Consistency":
        lines.append(f"  Values by year: {result.get('values')}%")
        lines.append(f"  Variance: {result.get('variance_pp')} percentage points")
        lines.append(f"  Trend: {result.get('trend')}")
    elif name == "Revenue vs Receivables":
        lines.append(f"  Revenue YoY growth: {result.get('rev_growth')}%")
        lines.append(f"  AR YoY growth: {result.get('ar_growth')}%")
        lines.append(f"  Max divergence: {result.get('max_divergence_pp')} pp")
    elif name == "Cash vs Accrual":
        lines.append(f"  Net income by year: {result.get('ni_values')}")
        lines.append(f"  Operating cash flow by year: {result.get('ocf_values')}")
        lines.append(f"  NI positive while OCF negative in any year: {result.get('ni_positive_ocf_negative')}")
    elif name == "Owner Compensation":
        lines.append(f"  Average: {result.get('avg_pct')}% of revenue")
        lines.append(f"  Industry benchmark: {result.get('benchmark_range')}")
        lines.append(f"  Compensation gap vs benchmark minimum: {result.get('comp_gap')} CAD")
    elif name == "EBITDA Stability":
        lines.append(f"  EBITDA by year: {result.get('values')}")
        lines.append(f"  YoY swings: {result.get('swings')}%")
        lines.append(f"  Trend: {result.get('trend')}")
    elif name == "DSO":
        lines.append(f"  Days Sales Outstanding by year: {result.get('values')} days")
        lines.append(f"  Latest: {result.get('latest')} days")
        lines.append(f"  Industry benchmark: {result.get('benchmark_range')} days")
        lines.append(f"  Trend: {result.get('trend')}")
    elif name == "Interest Coverage":
        lines.append(f"  Coverage ratio by year: {result.get('values')}x")
        lines.append(f"  Latest: {result.get('latest')}x (minimum acceptable: 2.0x)")
    return "\n".join(lines)

def generate_report(industry, objective, doc_type, years, quality, ratios,
                    transaction_size, years_operating, financing, buyer_context=""):
    bench = BENCHMARKS[industry]
    client = anthropic.Anthropic()

    ratio_text = "\n\n".join([
        _fmt_ratio("Gross Margin Consistency", ratios["gross_margin"]),
        _fmt_ratio("Revenue vs Receivables",   ratios["revenue_receivables"]),
        _fmt_ratio("Cash vs Accrual",          ratios["cash_accrual"]),
        _fmt_ratio("Owner Compensation",       ratios["owner_comp"]),
        _fmt_ratio("EBITDA Stability",         ratios["ebitda_stability"]),
        _fmt_ratio("DSO",                      ratios["dso"]),
        _fmt_ratio("Interest Coverage",        ratios["interest_coverage"]),
    ])

    buyer_section = f"\nBUYER'S STATED PRIORITIES:\n{buyer_context}\nAddress these concerns explicitly in the Key Findings and Recommended Next Steps.\n" if buyer_context and buyer_context.strip() else ""

    prompt = f"""You are a financial due diligence analyst specializing in SME acquisitions in Quebec, Canada.

TRANSACTION CONTEXT:
- Industry: {industry}
- Acquisition objective: {objective}
- Transaction size: {transaction_size}
- Business maturity: {years_operating}
- Financing structure: {financing}
- Document type: {doc_type}
- Years of data: {years}
- Data quality: {quality}
{buyer_section}

INDUSTRY BENCHMARKS:
- Normal gross margin: {bench['gross_margin_range'][0]*100:.0f}% to {bench['gross_margin_range'][1]*100:.0f}%
- Normal DSO: {bench['DSO_range'][0]} to {bench['DSO_range'][1]} days
- Normal owner compensation: {bench['owner_comp_pct_range'][0]*100:.0f}% to {bench['owner_comp_pct_range'][1]*100:.0f}% of revenue
- Typical EBITDA multiple for this industry: {bench['ebitda_multiple_range'][0]}x to {bench['ebitda_multiple_range'][1]}x
- Priority ratios for this industry and objective: {', '.join(bench['objective_priority'][objective])}

RATIO FINDINGS:
{ratio_text}

Generate a structured due diligence report with exactly these five sections using markdown.

## Priority Action
One sentence only. The single most urgent thing the buyer must do before proceeding. Make it specific and actionable, not generic.

## Executive Summary
3-4 sentences. First sentence: overall risk rating in bold (Low / Medium / High Risk). Most critical finding. Clear recommendation: proceed, proceed with conditions, or pause.

## Key Findings
One subsection per red or yellow flag using ### for each title. For each:
- What was found (one sentence with specific numbers)
- Why it matters for a {objective} buyer specifically (one to two sentences)
- Normalized EBITDA impact in dollars where relevant
- **Questions to ask the seller:** formatted as a numbered list, no dashes

## Valuation Context
- Show normalized EBITDA calculation explicitly: start from reported EBITDA, apply each adjustment with the dollar amount, arrive at normalized EBITDA
- Apply the industry EBITDA multiple range to normalized EBITDA to get implied valuation range
- Comment on working capital: is the business consuming or releasing cash, and what does the buyer need to budget for on day one beyond the purchase price
- One sentence on how the financing structure ({financing}) affects the risk profile

## Recommended Next Steps
Numbered list of 5 specific actions ordered by priority. Each item one sentence. No dashes.

FORMATTING RULES:
- No dashes anywhere. Use numbered lists or asterisk bullets only.
- Bold all specific dollar amounts and key risk terms.
- Tone: direct, acquisition-focused, no jargon without explanation.
- The buyer objective is {objective} — findings most relevant to that goal come first.
"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    report_text = message.content[0].text
    report_text = report_text.replace("$", "\\$")
    return report_text
