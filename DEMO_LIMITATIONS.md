# DEMO LIMITATIONS — Tender Finder

Read this alongside `TEST_RESULTS.md`. Nothing here is a defect — it's a
scope statement so you know exactly what you're looking at.

## 1. This is a standalone desktop workflow, not a hosted SaaS product

Tender Finder is a double-clickable Windows GUI around a separate Python
engine that produces Excel workbooks and run manifests. There is no database,
multi-user access, hosted web UI, authentication, or hosting. The standalone
weekly workflow is supported; a future web product remains a separate project.

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

## 4. Live connectors remain dependent on public websites

The configured connectors point at real public endpoints, and those sites may
change structure or access rules at any time. The 2026-07-14 release gate
confirmed Surrey's public tender listing with one controlled request; that is
evidence for that run, not a permanent availability guarantee. Login-gated
sources are deliberately not scraped: use approved email alerts instead. The
tool never stores portal credentials or bypasses CAPTCHA/browser checks.

## 5. Some source checks are public-source examples only

The ~300-source registers (`00 Master` Source_Register, `01 Code\
CONNECTOR_SWEEP\data\` backlog, `04 RESEARCH REFERENCE\
SOURCE_REGISTER_EXPANSION`) describe a specific reference region (British
Columbia's Lower Mainland / Fraser Valley) with real public procurement and
development-application portals. This is example/reference content for how to
build out a source register, not a universal, region-agnostic source list.
Adapt it for your own region.

## 6. The anti-fixture / anti-synthetic guards are intentionally strict

The builder includes a shared production guard that refuses to treat rows
tagged as fixture/synthetic/example as real user-facing output. The historical
Outreach and Dashboard mismatches are fixed; the current offline Self-Test
requires both checks to pass. The guard remains intentionally strict.

## 7. What this means for you

- Want to **see how it works safely**: double-click the GUI, run **Self-Test**,
  then run **Offline/Test Run**. No credentials or public-source fetch is used.
- Want to **use it for live tender-finding**: validate keywords, review the
  enabled rows in `config/sources.csv`, test the selected sources, and then use
  **Live Run**. Recheck any public connector that reports a changed/blocked
  response.
- Want to **build a product on top of it**: start with `FUTURE_WEB_APP_PLAN.md`.
