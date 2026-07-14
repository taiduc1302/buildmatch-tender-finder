# inputs — SYNTHETIC review workbook

`all_live_review.xlsx` in this package is **synthetic**. The original project
shipped a real review workbook here with ~33,600 rows harvested from live
municipal sources; it was excluded during sanitization and replaced with 12
fictitious records covering all four routing buckets:

| Route | Synthetic records |
|---|---|
| `Run_Queue` | 2 source stubs awaiting manual verification |
| `Future_Projects` | 6 leads: 45-lot subdivision servicing (fit 86), watermain replacement program (81), drainage upgrade + detention pond (78), roadworks corridor (74), park civil works (72), mixed-use rezoning lead (65) |
| `Bulk_Intake_Raw` | 3 low-signal building permits |
| `Rejected_Archive` | 2 non-civil rows (sign permit, tenant improvement) |

Municipalities (`Exampleville`, `Sampleton`, `Testburg`), applicants, addresses
and URLs are fictitious; every row's `fit_reason` says `SYNTHETIC DEMO RECORD`.

Column layout is identical to real sweep output (21 columns, sheet name
`review`), so the demo builder consumes it unchanged. For real use, replace
this file with output from your own live sweeps, or point the
`TENDER_FINDER_REVIEW_XLSX` environment variable at your workbook.
