# Windbrook EF Portal

A financial report portal for EF / Windbrook Solutions. Generates polished SACS (cashflow) and TCC (net worth) PDF reports for client quarterly meetings.

## Setup

```bash
pip install flask reportlab
python app.py
```

Then open http://localhost:5000

## Deployment (Railway)

1. Push to GitHub
2. Connect repo to Railway
3. Set start command: `python app.py`
4. Add volume at `/app/instance` for the SQLite database
5. Add volume at `/app/reports` for generated PDFs

## What it does

- **Client profiles** — store static info once (names, DOBs, SSNs, salary, expense budget, account structure)
- **Quarterly data entry** — enter current balances per quarter; all math is automatic
- **SACS PDF** — 2-page cashflow diagram: Inflow → Outflow → Private Reserve bubbles + FICA/Investment page
- **TCC PDF** — net worth overview with retirement bubbles (by spouse), non-retirement accounts, trust, and liabilities
- **Report history** — re-download any previous quarterly report

## Calculation rules (per client spec)

- Excess cashflow = Inflow − Outflow
- FICA target = (6 × monthly expenses) + total insurance deductibles  
- Grand total = Client 1 Retirement + Client 2 Retirement + Non-Retirement + Trust
- Liabilities are displayed separately — NOT subtracted from net worth
- Non-retirement total excludes trust accounts
