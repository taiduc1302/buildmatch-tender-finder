# demo_synthetic_sample — sample output built from SYNTHETIC data

This folder is a real run of the demo builder **from this sanitized package**
(2026-07-03, `--no-fetch`, synthetic inputs). It exists so that:

1. you can inspect the output workbook without running anything, and
2. `tests\test_workbook_quality.py` has a default workbook to validate.

All content derives from the synthetic records in `inputs\all_live_review.xlsx`
and `demo_data\email_alerts\` — no real tenders, leads, or company data.

The original project kept a real verified production run here (`demo_p522`);
it was excluded during sanitization because it contained real harvested
intelligence.
