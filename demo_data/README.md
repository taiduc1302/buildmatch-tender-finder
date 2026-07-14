# demo_data — SYNTHETIC demo inputs

Everything in this folder is **fictitious**, created for the sanitized portable
package so the workflow can be demonstrated without any real company data.

- `email_alerts\demo_1_roadworks_open.eml` — open municipal roadworks tender
  (City of Exampleville) → lands in **BID NOW**
- `email_alerts\demo_2_watermain_open.eml` — open watermain replacement tender
  (Town of Sampleton) → lands in **BID NOW**
- `email_alerts\demo_3_drainage_closed.eml` — closed drainage culvert tender →
  lands in **history** (proves closed-tender routing)

The sender addresses reuse real public alert-provider domains
(`bidsandtenders.ca`, `bcbid.gov.bc.ca`) only so the provider-detection logic
routes them correctly; issuers, projects, contacts, and URLs are fake and every
body is marked `SYNTHETIC DEMO DATA`.

Used by `run_demo_synthetic.bat` via `--email-import-path demo_data\email_alerts`.

The synthetic **review workbook** (future-project leads: subdivision servicing,
drainage upgrade, park civil works, watermain program, roadworks corridor,
rezoning lead) lives at `inputs\all_live_review.xlsx` — see
`inputs\README_INPUTS.md`.
