# TENDER_FINDER Patch 5.11 Backlog

Patch 5.10 prioritized Surrey integrity, Abbotsford resilience, run-over-run memory, and the outreach/action layer. These items remain for a future pass.

## Source Discovery

- `new_west_currentdev`: full catalog/directory browse still needs manual UI confirmation for the exact Current Developments dataset. Automated discovery continues to resolve `Permits - Buildings and Plumbing`, which is trailing permit context, not current development applications.
- `burnaby_devapps`: no connector-ready development/rezoning application layer found from public Hub discovery. Manual city-site/P3 extraction remains the likely route.
- `city_langley_devapps`: no connector-ready public FeatureServer found. Keep as manual/P3.
- `van_rezoning` and `van_devpermits`: Opendatasoft slugs remain unresolved; revisit Vancouver catalog naming manually.
- `dnv_devapps`: public REST directory exposes infrastructure/DPA/reference layers, not application records.
- `port_coquitlam_landdev`: public REST directory exposes OCP/zoning/ROW/reference layers, not application records.

## Data Quality

- `surrey_devapps_v2` is a correct per-application layer but status-mixed/historical. Patch 5.11 should decide whether concluded/closed Surrey V2 rows belong in BID LATER, Watchlist, or Analyzed_Set_Aside. Patch 5.10 did not change routing/write gates.
- Add a source-specific current-status filter only after business approval, because removing historical Surrey rows will materially change the visible lead count.
- Consider showing source-status mix counts for Surrey V2 in the Executive Summary.

## Operational Workflow

- Add a lightweight UI/filter preset for Outreach_Tracker statuses if the workbook becomes the weekly operating surface.
- Add a `last_seen_date` column for leads if the user wants aging and stale-lead workflows.
- Add a manual override sheet for aliases/duplicate lead IDs if users find duplicate applications across source systems.
