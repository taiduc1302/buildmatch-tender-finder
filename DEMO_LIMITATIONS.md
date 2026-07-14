# DEMO LIMITATIONS — Tender Finder

Read this alongside `TEST_RESULTS.md`. Nothing here is a defect — it's a
scope statement so you know exactly what you're looking at.

## 1. This is a starter prototype, not a production SaaS product

Tender Finder, as shipped in this package, is a set of Python scripts and
batch launchers that produce an Excel workbook. There is no database, no
multi-user access, no web UI, no authentication, and no hosting. It was
extracted and sanitized from a working internal prototype so it could be kept,
studied, demonstrated, and used as the foundation for something bigger — see
`FUTURE_WEB_APP_PLAN.md` for that path. Treat it accordingly: a proof of
concept with real, working logic underneath, not a finished product.

## 2. The demo data is entirely synthetic

`inputs\all_live_review.xlsx` (12 records) and `demo_data\email_alerts\*.eml`
(3 emails) are fictitious, created specifically for this package. Municipality
names (Exampleville, Sampleton, Testburg), applicants, addresses, and URLs are
all made up. See `inputs\README_INPUTS.md` and `demo_data\README.md` for the
exact record list. Nothing in the demo output reflects any real tender, lead,
or company.

## 3. Real production outputs were intentionally excluded

The original project's real run history (33,629-row review workbook, 15+ real
output folders, raw harvested data, real working-master workbooks) was removed
during sanitization rather than included — see `SANITIZATION_REPORT.md`. The
only output workbook shipped in this package
(`latest_verified_output\demo_synthetic_sample\`) was generated *by this
package* from the synthetic inputs above, specifically for this handoff.

## 4. Some live connectors require configuration and have not been re-tested

The coded connectors (Surrey, Vancouver, Maple Ridge, Township of Langley,
Coquitlam, Abbotsford development-application feeds, ~20 procurement listing
checks) point at real public endpoints and were working in the original
project. **They have not been re-run from this sanitized package** — target
sites may have changed their structure or access rules since. Expect to debug
before relying on live fetching. Login-gated sources (bids&tenders vendor
alerts, BC Bid notifications, BidCentral, MERX, SAP Ariba) are deliberately
**not scraped** at all — they're placeholders for a registration + email-alert
workflow, by design (the tool never stores portal credentials).

## 5. Some source checks are public-source examples only

The ~300-source registers (`00 Master` Source_Register, `01 Code\
CONNECTOR_SWEEP\data\` backlog, `04 RESEARCH REFERENCE\
SOURCE_REGISTER_EXPANSION`) describe a specific reference region (British
Columbia's Lower Mainland / Fraser Valley) with real public procurement and
development-application portals. This is example/reference content for how to
build out a source register, not a universal, region-agnostic source list.
Adapt it for your own region.

## 6. The anti-fixture / anti-synthetic guards are intentionally strict

The demo builder includes a production guard that refuses to treat rows
tagged as fixture/synthetic/example as real output — see `TEST_RESULTS.md`
§2a for exactly how it behaves on the shipped synthetic data (it correctly
fails two sub-checks). This is deliberate and should not be loosened: it's the
mechanism that would prevent a future real deployment from accidentally
shipping test data as a client-facing report.

## 7. What this means for you

- Want to **see how it works**: run `run_demo_synthetic.bat` — no setup beyond
  Python, no credentials, no real data risk.
- Want to **use it for real tender-finding**: budget time to (a) supply a real
  review workbook, (b) re-verify/fix live connectors for your target sites,
  (c) build your own source register for your region, (d) confirm the
  anti-fixture guard passes cleanly on your real data.
- Want to **build a product on top of it**: start with `FUTURE_WEB_APP_PLAN.md`.
