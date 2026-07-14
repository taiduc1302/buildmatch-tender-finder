# TENDER_FINDER Manual Portal Workflow — Patch 5.0

Portal/login sources cannot be auto-scraped. This document defines the manual workflow for each.

## BC Bid
- **Login required:** Business BCeID
- **URL:** https://bcbid.gov.bc.ca
- **Method:** Email alert — set commodity codes for civil/earthwork categories
- **Cadence:** Daily check on alert emails
- **Export:** Download tender details as HTML/PDF, import via `tenderfinder_portal_import.py --source bc_bid`

## CivicInfo BC / Bids & Tenders
- **URL:** https://www.civicinfo.bc.ca/bids
- **Method:** RSS feed (most automatable) — subscribe to RSS, filter for civil/earthwork
- **Cadence:** Daily RSS check
- **Export:** RSS items → CSV import

## Bids & Tenders Municipal Portals
- **URL:** https://www.bidsandtenders.ca
- **Method:** Saved search per municipal subdomain (email notifications)
- **Cadence:** Daily email check
- **Import:** Download from portal, import CSV

## MERX
- **URL:** https://www.merx.com
- **Method:** Saved search + email alert for BC civil/infrastructure categories
- **Login:** Required (registration)
- **Cadence:** Daily

## Bonfire (School Districts, Some Municipalities)
- **URL:** Varies by organization
- **Method:** Each school district has its own Bonfire subdomain
- **Example:** https://sd43.bonfirehub.com
- **Import:** Download CSV from Bonfire → import

## Ariba / SAP (Metro Vancouver, BC Hydro, etc.)
- **URL:** https://www.ariba.com
- **Method:** Supplier registration required; email notifications
- **Login:** Required

## WorkSafeBC / BC Ministry of Transportation
- **URL:** Various
- **Method:** Email alerts or manual check
- **Cadence:** Weekly

## Surrey — Planning Reports Page
- **URL:** https://www.surrey.ca/city-government/council-meetings/planning-reports
- **Method:** Auto-fetched by `surrey_planning_reports` connector (Patch 5.0)
- **Status:** AUTOMATED via `tenderfinder_surrey_inprocess.py`

## BC Hydro Capital Projects
- **URL:** https://www.bchydro.com/about/procurement.html
- **Method:** Manual check or email subscription
- **Cadence:** Monthly

## BC Ferries
- **URL:** https://www.bcferries.com/about/procurement
- **Method:** Manual check
- **Cadence:** Monthly
