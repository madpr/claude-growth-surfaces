# Nightly revenue reconciliation

This repo reconciles the billing export against the ledger and writes a variance
report. It runs unattended every night.

## Rules

- Never write to `ledger/` — it is the source of truth and is append-only upstream.
- Variance under $0.01 is rounding. Do not report it.
- Every figure in the report must cite the row it came from.
- If the export is missing a day, stop and report the gap. Do not interpolate.

## Layout

- `ledger/` — upstream ledger snapshots, read-only
- `exports/` — billing exports, one file per day
- `reports/` — generated output, safe to overwrite
