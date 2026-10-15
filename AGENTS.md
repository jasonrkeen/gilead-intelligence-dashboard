> This file mirrors `.github/copilot-instructions.md` and `CLAUDE.md`; keep all three in sync when any changes.

# AGENTS.md — gilead-intelligence-dashboard

## Purpose
A Streamlit-based equity intelligence dashboard for Gilead Sciences integrating market data, SEC financials, segment exposure, pipeline risk, valuation scenarios, and risk-adjusted return modeling.

## Tech stack
- Python; dependencies in `requirements.txt`
- Key libraries: `streamlit`, `pandas`, `numpy`, `yfinance`, `plotly`, `requests`, `beautifulsoup4`, `feedparser`, `fpdf`

## Folder structure
- `assets/` (1 files)
- `utils/` (17 files)
- `README.md`
- `app.py`
- `gilead_intelligence_brief.pdf`
- `requirements.txt`

## Setup, run, test
Commands documented in README.md (referenced files exist):
```bash
pip install -r requirements.txt
streamlit run app.py
```
- No automated tests exist yet; if adding them, use pytest under `tests/`.

## Conventions observed
- Public data sources referenced: SEC, yfinance.
- Write paths relative to the repo root (no absolute local paths).

## Output artifacts
- A PDF report is produced; keep it in sync with model changes.
- Streamlit dashboard: `app.py`, `utils/sec_data.py` (run with `streamlit run <file>`).
- Charts are generated with plotly.

## Guardrails
- Never commit secrets, API keys, tokens, or `.env` files.
- Do not commit large raw datasets or binaries; keep data fetched or documented with its source.
- Keep analysis source-backed: cite data sources and assumptions; label scenario/forecast outputs as model estimates, not facts.
- Preserve reproducibility: no unseeded randomness, no hidden manual steps.
