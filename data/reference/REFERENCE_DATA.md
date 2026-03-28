# Reference Data Policy (Kaggle-Sourced)

This project uses externally curated reference data from Kaggle to keep the workflow realistic and auditable.

## Required Files
Place CSV files under `data/reference/kaggle/` with these schemas:

1. Brand to generic mapping
- Required columns: `brand,generic`

2. MedDRA SOC mapping
- Required columns: `reaction,soc_name`

## Selection Rules
- If `.env` sets `REFERENCE_BRAND_GENERIC_FILE` or `REFERENCE_MEDDRA_SOC_FILE`, those files are used.
- Otherwise, the pipeline auto-discovers CSV files by required column names.

## Notes
- Keep source provenance (Kaggle dataset URL, version, and download date) in your project documentation.
- Do not commit proprietary or licensed data unless your usage terms allow it.
