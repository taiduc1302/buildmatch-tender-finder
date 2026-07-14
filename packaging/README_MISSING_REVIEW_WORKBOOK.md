# If TENDER_FINDER says the review workbook is missing

TENDER_FINDER builds its Track A intelligence (BID LATER / Watchlist / Analyzed)
from a reviewed-leads workbook named `all_live_review.xlsx`. It is TENDER_FINDER's
working business data.

If this `inputs` folder does not contain `all_live_review.xlsx`, do ONE
of the following:

1. **Easiest:** copy `all_live_review.xlsx` into this `inputs` folder
   (ask whoever gave you this package for the file). TENDER_FINDER finds it here
   automatically.

2. **Or** run the TENDER_FINDER GUI anyway - when the workbook is missing it opens
   a Browse dialog, lets you point at the file wherever it lives, and
   remembers your choice (saved to `tenderfinder_runtime_config.json` in the
   package folder).

3. **Or** set the `TENDER_FINDER_REVIEW_XLSX` environment variable to the file's
   full path. This overrides everything else.

TENDER_FINDER never fails silently on this and never invents numbers - if the
workbook truly cannot be found, it tells you exactly what it looked for.
