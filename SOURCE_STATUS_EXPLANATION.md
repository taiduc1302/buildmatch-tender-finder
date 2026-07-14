# Source Status Explanation

## Email Alert Intake statuses

- `EMAIL_INTAKE_NO_FILES`: the selected/default folder exists but no `.eml` files were found.
- `EMAIL_INTAKE_PARSED_ROWS`: TENDER_FINDER parsed one or more tender rows from approved `.eml` files.
- `EMAIL_INTAKE_PARSE_ZERO_ROWS`: `.eml` files were present but none produced tender rows.
- `EMAIL_INTAKE_REJECTED_FILES`: `.eml` files were present but only rejected/duplicate outcomes remained.
- `EMAIL_INTAKE_SKIPPED_NO_FOLDER`: TENDER_FINDER had no usable folder path for manual import.

## Routing behavior

- Open and actionable civil email rows go to `BID_NOW_Active_Tenders`.
- Closed or historical email rows go to `Tender_History_Closed_Public`.
- Non-actionable or filtered email rows stay in `Tender_Signals_All` with `filtered_reason`.
