# Coquitlam FeatureServer Research - Patch 5.8

## Result

Found and live-verified. The existing Coquitlam Development Information service remains the correct application-level layer:

`https://services2.arcgis.com/Q6Lq3evZUGfPrN7o/arcgis/rest/services/Development_Information_Demo/FeatureServer/0`

## Proof

- ArcGIS services directory checked: `https://services2.arcgis.com/Q6Lq3evZUGfPrN7o/arcgis/rest/services/?f=pjson`
- Development Information service metadata checked: `https://services2.arcgis.com/Q6Lq3evZUGfPrN7o/arcgis/rest/services/Development_Information_Demo/FeatureServer/0?f=pjson`
- Query count checked: `/query?where=1%3D1&returnCountOnly=true&f=pjson` returned `473`.
- Sample query checked with `outFields=*`, `returnGeometry=false`, and both `f=pjson` and `f=geojson`; expected fields and sample rows were present.
- Alternative planning services checked:
  - `Planning and Development/FeatureServer`
  - `Planning_and_Development/FeatureServer`
  These contain planning reference layers such as neighbourhood plans, development permit areas, zoning, and OCP layers, not the development-application records TENDER_FINDER needs.

## TENDER_FINDER Live Connector Test

Command run from `01 Code/CONNECTOR_SWEEP`:

`python tenderfinder_raw_sweep.py --only coquitlam_devapps --review-only --out "C:\tenderfinder_out\patch5_8_live\coquitlam_live_review.xlsx"`

Result:

- pulled: `473`
- duplicates skipped: `19`
- normalized/clean future-project leads: `454`
- watchlist: `0`
- bulk: `0`
- rejected: `0`
- protected master touched: `NO` (`--review-only`)

Prior Patch 5.4 proof was `471 pulled / 452 clean`, so the source is live and has grown by two records.
