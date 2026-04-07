# Vérifi — Setup & Demo Guide

## Install

```bash
pip install streamlit pdfplumber pandas openpyxl anthropic
```

## Set your API key

```bash
export ANTHROPIC_API_KEY=your_key_here
```

On Windows (PowerShell):
```powershell
$env:ANTHROPIC_API_KEY = "your_key_here"
```

## Run

```bash
cd verifi
streamlit run app.py
```

## Demo script (use this exact sequence for the presentation)

1. Open the app in browser (localhost:8501)
2. Select: **Manufacturing** | **Cash Flow** | **Excel / Other** | **3 years**
3. Upload: `demo_data/quebec_mfg_demo.xlsx`
4. Click **Analyze Document**
5. Data quality shows: Sufficient, all three statement types found
6. Click **Generate AI Due Diligence Report**
7. Show the 4 flags: gross margin (red), AR divergence (red), cash/accrual (red), owner comp (red)
8. Click **Schedule CPA Consultation** to show the advisory layer

## Planted flags in the demo file

| Flag | Ratio | Severity | What to say |
|------|-------|----------|-------------|
| 1 | Gross Margin Consistency | RED | "Margin drops 9 percentage points in Year 2 with no recovery. In a manufacturing acquisition, this suggests either a cost shock, a pricing concession, or margin manipulation." |
| 2 | Revenue vs. Receivables | RED | "Revenue grew 12%, receivables grew 40% — 28pp divergence. Either the seller is booking revenue they haven't collected, or a major customer is slow-paying." |
| 3 | Cash vs. Accrual | RED | "In Year 2, net income is positive but operating cash flow is negative. The business reported a profit it did not generate in cash." |
| 4 | Owner Compensation | RED | "$48K on $2.1M revenue is 2.3% — the manufacturing benchmark floor is 5%. This means EBITDA is overstated by at least $57K before normalization." |

## File structure

```
verifi/
├── app.py            — Streamlit app (4 screens)
├── extraction.py     — PDF and Excel parsing
├── ratios.py         — 5 forensic ratio calculations
├── benchmarks.py     — Industry benchmark table
├── report.py         — Claude API prompt and call
├── requirements.txt
└── demo_data/
    └── quebec_mfg_demo.xlsx
```
