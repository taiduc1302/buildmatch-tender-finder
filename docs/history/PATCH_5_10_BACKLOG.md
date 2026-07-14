# TENDER_FINDER Patch 5.10 Backlog

Patch 5.9 pushed every promising public development-application source that could be verified without login, credentials, or protected-master writes. These items remain unresolved or intentionally deferred.

## Connector Discovery Follow-Ups

- `new_west_currentdev`: still not safely connected. The raw runner resolves `Permits - Buildings and Plumbing`, not the requested Current Developments application layer. A global ArcGIS hit was Westminster, California, not New Westminster, BC. Next step: manual browse of New Westminster open-data UI or city planning pages for the exact Current Developments item ID.
- `burnaby_devapps`: Hub DCAT/search did not expose a non-denylisted development or rezoning application FeatureServer. Next step: manual city-site review and/or planning-board scraping if public.
- `city_langley_devapps`: Hub DCAT/search did not expose a development-application FeatureServer. Next step: manual/P3 extraction from planning pages.
- `van_rezoning` and `van_devpermits`: guessed Opendatasoft slugs returned 404 and catalog search returned no matching dataset. Next step: manual Vancouver open-data catalog browse for renamed datasets, if they exist.
- `delta_devapps`: only Building Permits was found and is retained as trailing context. No current development-application layer found.
- `dnv_devapps`: public DNV service exposes infrastructure/DPA/reference layers, not application records.
- `port_coquitlam_landdev`: public service exposes OCP, zoning, easements, ROW, floodplain, contours, and reference layers, not application records.
- Bonus sources `port_moody_discovery`, `mission_discovery`, `chilliwack_discovery`, and `white_rock_discovery`: ArcGIS Hub probes did not find a current development-application layer in Patch 5.9. Revisit city open-data pages manually.
- BC Data Catalogue: public CKAN searches for exact municipal development-application terms returned no connector-ready aggregate municipal dataset. Broad `development application` search returned many unrelated records.

## Patch 5.10 Priorities

- Make Abbotsford retry more resilient. The standalone live test pulled 503 rows / 500 clean, but the full all-connector run hit an ArcGIS 503 on the first batch.
- Add a source-summary freshness panel to the demo workbook so standalone live proofs can be separated from full-sweep rows.
- Build manual/P3 extraction for New Westminster, Burnaby, and City of Langley if no public FeatureServer layer is found.
- Revisit Vancouver ODS catalog naming and add explicit source research notes for the missing rezoning/development-permit datasets.
- Consider routing Delta building-permit trailing context to `Bulk_Intake_Raw` in a future patch only if the business wants permit after-signal retained outside rejection context.
