# FAERS Signal Detector

Pharmacovigilance signal detection on real FDA Adverse Event Reporting System data,
using industry-standard PRR (Proportional Reporting Ratio) and ROR (Reporting Odds Ratio) methods.

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 15 running locally
- 8GB RAM minimum

### Installation
```bash
git clone <repo>
cd faers-signal-detector
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # Edit with your PostgreSQL credentials
```

### Run the full pipeline
```bash
python pipeline.py --all
```

### Launch dashboard
```bash
streamlit run dashboard/app.py
```

### Run tests
```bash
pytest tests/ -v
```

## Pipeline Steps
1. **Download** - Fetches FAERS ASCII quarterly ZIPs from FDA website
2. **Ingest** - Loads raw pipe-delimited files into PostgreSQL
3. **Clean** - Deduplicates reports, standardizes drug names, normalizes ages
4. **Signals** - Computes PRR/ROR for all drug-event pairs, cumulatively per quarter

## Signal Criteria (Evans et al. 2001)
| Metric | Threshold |
|---|---|
| PRR | >= 2.0 |
| Chi-squared | >= 4.0 |
| Case count | >= 3 |
| ROR 95% CI lower bound | > 1.0 |

## Dashboard Pages
- **Drug Explorer** - Search any drug, view top adverse event signals ranked by PRR
- **Signal Trends** - Track PRR evolution over quarters for any drug-event pair
- **Severity Filter** - Filter signals by outcome (death, hospitalization, etc.)

## Data Source
FDA FAERS Public Dashboard: https://fda.gov/drugs/questions-science-drugs/fda-adverse-event-reporting-system-faers
Freely available, no login required. Updated quarterly.
