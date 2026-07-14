# Surrey DevApps V2 Research - Patch 5.7

## Result

`surrey_devapps_v2` was **NOT_FOUND** in this patch.

## Attempts

- `https://gis.surrey.ca/server/rest/services/?f=pjson`
  - Result from Python live probe: SSL certificate verification failed in this environment.
  - No connector was added because the service list could not be reliably inspected.
- `https://data.surrey.ca/api/search/v1?query=development%20application`
  - Result: HTTP 200, redirected/rendered the ArcGIS Hub HTML search page rather than a clean JSON API result.
- `https://data.surrey.ca/api/search/v1?query=planning%20application`
  - Result: HTTP 200, redirected/rendered the ArcGIS Hub HTML search page rather than a clean JSON API result.
- Web search for Surrey ArcGIS development/planning application layers did not produce a verified FeatureServer layer suitable for a live connector within the patch time box.

## Next Investigator

Use a browser with the Surrey/ArcGIS Hub UI, inspect network calls for ArcGIS item IDs, and look specifically for development-application or planning-application layers rather than subdivision boundary markers or parcel layers.

## Out Of Scope

Changing `surrey_devapps` routing or replacing the existing connector is out of scope for Patch 5.7 because Track A counts are protected and the current connector history must remain auditable.
