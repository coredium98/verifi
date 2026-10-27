# Vérifi

Vérifi is a financial due diligence screening tool built for small and medium enterprise (SME) acquisitions in Quebec ($500K to $5M in annual revenue).

Buyers in this segment face a structural gap. Full quality-of-earnings (QoE) mandates from accounting firms typically start at $15,000 to $25,000, which forces many individual buyers to evaluate targets using raw broker packages or unadjusted tax filings before signing a letter of intent. Vérifi automates the first forensic pass: it extracts multi-year statement lines from Excel or PDF packages, tests seven accounting manipulation and cash-conversion ratios against industry benchmarks, and prepares a structured pre-LOI brief ready for CPA review.

## Forensic ratio engine

The deterministic engine in `verifi/ratios.py` evaluates seven indicators and reorders them dynamically based on the target's sector (`Manufacturing`, `Retail`, `Professional Services`, `Hospitality`, `Construction`) and the buyer's primary objective (`Cash Flow`, `Growth`, `Asset Acquisition`).

| Ratio | What it measures | High-risk (Red) threshold |
|---|---|---|
| Gross Margin Consistency | Multi-year gross margin spread | Variance above 5.0 percentage points across reported periods |
| Revenue vs. Receivables | Divergence between YoY revenue growth and YoY AR growth | Accounts receivable growing more than 10.0 percentage points faster than revenue |
| Cash vs. Accrual | Gap between reported net income and operating cash flow | Net income positive while operating cash flow is negative, or gap exceeding 15% of revenue |
| Owner Compensation | Officer pay relative to revenue vs. sector floor | Average compensation below 60% of the sector minimum floor (signals overstated EBITDA) |
| EBITDA Stability | Year-over-year operating earnings volatility | YoY swing exceeding 20.0% (reconstructed from Net Income + D&A + Tax + Interest when unreported) |
| Days Sales Outstanding (DSO) | Working capital lockup in trade receivables | Latest DSO exceeding 1.5x the upper bound of the industry benchmark |
| Interest Coverage | Debt service capacity (EBITDA / interest expense) | Coverage below 2.0x in the most recent fiscal year |

## Architecture

```text
verifi/
├── .github/workflows/ci.yml   # Automated Ruff linting and Pytest suite
├── .streamlit/config.toml     # Theme configuration
├── assets/
│   ├── logo.png               # Optimized header mark
│   └── styles.css             # Application stylesheet and custom tooltips
├── demo_data/
│   └── quebec_mfg_demo.xlsx   # Sample 3-year manufacturing statements (2021 to 2023)
├── tests/
│   ├── test_extraction.py     # Parser and data-quality verification
│   └── test_ratios.py         # Forensic threshold and EBITDA reconstruction tests
├── verifi/
│   ├── __init__.py
│   ├── benchmarks.py          # Sector benchmarks and buyer-objective priority matrices
│   ├── extraction.py          # Excel/PDF ingestion and statement completeness scoring
│   ├── ratios.py              # Pure calculation functions for the 7 forensic ratios
│   ├── report.py              # Anthropic Claude prompt builder and report generator
│   └── ui_content.py          # Law 25 privacy disclosures, tooltips, and UI metadata
├── app.py                     # Streamlit entry point
├── pyproject.toml             # Package metadata, Ruff, and Pytest settings
└── requirements.txt           # Pinned runtime dependencies
```

## Local setup

Install the dependencies in a Python 3.11+ virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your Anthropic API key (required only for Step 4 AI memo generation; Steps 1 through 3 run locally and deterministically):

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

Start the application:

```bash
streamlit run app.py
```

Once the interface opens at `http://localhost:8501`, you can upload your own PDF or Excel statements, or click **Load Quebec SME Demo** to run the pipeline on the included three-year manufacturing case (`demo_data/quebec_mfg_demo.xlsx`).

## Running the test suite

```bash
python3 -m unittest discover -s tests -v
```

Or with `pytest` and `ruff`:

```bash
ruff check .
pytest -v
```

## Author

Built by **Zacharie Houle, CPA auditeur**. Licensed under the [MIT License](LICENSE).
