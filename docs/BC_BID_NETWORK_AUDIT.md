# BC Bid Network Audit - Patch 5.13 (pagination/detail hardening added Patch 5.14; closing-date-aware stop condition added Patch 5.16)

## Scope

- Target browse URL: [https://bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public](https://bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public)
- Login attempted: NO
- CAPTCHA bypass attempted: NO
- Browser method: Playwright
- Browser launch: msedge_headless

## Track 0 - Real Browser Findings

- Final URL: `https://bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public`
- Page title: `Opportunities: BC Bid`
- Platform signal: `Ivalua`
- Browser-check detected: `False`
- CAPTCHA detected: `True`
- Page text sample: `Skip to content Notifications Accessibility Opportunities Contract Awards Unverified Bid Results Login Navigate to the previous page Access to navigation history Opportunities Search by keyword (in Description, ID, Summary, Commodity) Search by Opportunity ID Date format must be YYYY-MM-DD Filter by: Status Open Delete "Open" Delete all values. Opportunity Type Opportunity Type on Historical Records (Apr 1, 2015 - Dec 15, 2022) Region Issue Date (yyyy-MM-dd) Select a date Select a date Organi...`

### Full Request List Observed

- `GET` `document` [https://bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public](https://bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public)
- `GET` `document` [https://bcbid.gov.bc.ca/page.aspx/en/bas/browser_check](https://bcbid.gov.bc.ca/page.aspx/en/bas/browser_check)
- `GET` `stylesheet` [https://bcbid.gov.bc.ca/bare.aspx/en/css/default_style/buyer_ssbc_V2_0_140_20260525_p70984/rev5a585ea635568f88780646f761120bd56727126762267869184/BC_BidR_15-164/css_default_style.css](https://bcbid.gov.bc.ca/bare.aspx/en/css/default_style/buyer_ssbc_V2_0_140_20260525_p70984/rev5a585ea635568f88780646f761120bd56727126762267869184/BC_BidR_15-164/css_default_style.css)
- `GET` `stylesheet` [https://bcbid.gov.bc.ca/dist/third-party/semantic-ui/semantic.min.css?v=20260525113358](https://bcbid.gov.bc.ca/dist/third-party/semantic-ui/semantic.min.css?v=20260525113358)
- `GET` `stylesheet` [https://bcbid.gov.bc.ca/dist/css/ivalua.min.css?v=20260525113354](https://bcbid.gov.bc.ca/dist/css/ivalua.min.css?v=20260525113354)
- `GET` `script` [https://bcbid.gov.bc.ca/dist/js/prototype_extended.min.js?v=20260525113354](https://bcbid.gov.bc.ca/dist/js/prototype_extended.min.js?v=20260525113354)
- `GET` `script` [https://bcbid.gov.bc.ca/bare.aspx/en/js/scope_script/buyer_ssbc_V2_0_140_20260525_p70984/12B5B0895a585ea635568f88780646f761120bd5/js_scope_script.js](https://bcbid.gov.bc.ca/bare.aspx/en/js/scope_script/buyer_ssbc_V2_0_140_20260525_p70984/12B5B0895a585ea635568f88780646f761120bd5/js_scope_script.js)
- `GET` `script` [https://bcbid.gov.bc.ca/dist/js/global_script.min.js?v=20260525113354](https://bcbid.gov.bc.ca/dist/js/global_script.min.js?v=20260525113354)
- `GET` `script` [https://bcbid.gov.bc.ca/dist/js/global_defer_script.min.js?v=20260525113354](https://bcbid.gov.bc.ca/dist/js/global_defer_script.min.js?v=20260525113354)
- `GET` `script` [https://bcbid.gov.bc.ca/dist/js/bas/captcha_script.min.js?v=20260525113356](https://bcbid.gov.bc.ca/dist/js/bas/captcha_script.min.js?v=20260525113356)
- `GET` `script` [https://www.google.com/recaptcha/api.js?render=6LckweAnAAAAAP06dUhCg3zf0WTEXJNkV16V1EKw](https://www.google.com/recaptcha/api.js?render=6LckweAnAAAAAP06dUhCg3zf0WTEXJNkV16V1EKw)
- `GET` `script` [https://bcbid.gov.bc.ca/dist/js/bas_script.min.js?v=20260525113354](https://bcbid.gov.bc.ca/dist/js/bas_script.min.js?v=20260525113354)
- `GET` `image` [https://bcbid.gov.bc.ca/bare.aspx/en/fil/download_public/6b7373df-88bd-480d-8daf-850d9191c9c6](https://bcbid.gov.bc.ca/bare.aspx/en/fil/download_public/6b7373df-88bd-480d-8daf-850d9191c9c6)
- `GET` `image` [https://bcbid.gov.bc.ca/dist/image/header_pics.gif](https://bcbid.gov.bc.ca/dist/image/header_pics.gif)
- `GET` `image` [https://bcbid.gov.bc.ca/dist/image/core/accessibility/default-contrast-thumbnail.png](https://bcbid.gov.bc.ca/dist/image/core/accessibility/default-contrast-thumbnail.png)
- `GET` `image` [https://bcbid.gov.bc.ca/dist/image/core/accessibility/high-contrast-thumbnail.png](https://bcbid.gov.bc.ca/dist/image/core/accessibility/high-contrast-thumbnail.png)
- `GET` `script` [https://www.gstatic.com/recaptcha/releases/TnA7HacJFoBWt9hnlunBlYfK/recaptcha__en.js](https://www.gstatic.com/recaptcha/releases/TnA7HacJFoBWt9hnlunBlYfK/recaptcha__en.js)
- `GET` `image` [https://bcbid.gov.bc.ca/dist/image/header_shading.gif](https://bcbid.gov.bc.ca/dist/image/header_shading.gif)
- `GET` `image` [https://bcbid.gov.bc.ca/dist/image/menu_shading.gif](https://bcbid.gov.bc.ca/dist/image/menu_shading.gif)
- `GET` `font` [https://bcbid.gov.bc.ca/dist/css/semantic-ui/assets/fonts/Lato/Lato-Bold.woff2](https://bcbid.gov.bc.ca/dist/css/semantic-ui/assets/fonts/Lato/Lato-Bold.woff2)
- `GET` `font` [https://bcbid.gov.bc.ca/dist/css/semantic-ui/assets/fonts/FontAwesome6/webfonts/fa-regular-400.woff2](https://bcbid.gov.bc.ca/dist/css/semantic-ui/assets/fonts/FontAwesome6/webfonts/fa-regular-400.woff2)
- `GET` `font` [https://bcbid.gov.bc.ca/dist/css/semantic-ui/assets/fonts/FontAwesome6/webfonts/fa-solid-900.woff2](https://bcbid.gov.bc.ca/dist/css/semantic-ui/assets/fonts/FontAwesome6/webfonts/fa-solid-900.woff2)
- `GET` `font` [https://bcbid.gov.bc.ca/dist/css/semantic-ui/assets/fonts/Lato/Lato-Regular.woff2](https://bcbid.gov.bc.ca/dist/css/semantic-ui/assets/fonts/Lato/Lato-Regular.woff2)
- `GET` `document` [https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LckweAnAAAAAP06dUhCg3zf0WTEXJNkV16V1EKw&co=aHR0cHM6Ly9iY2JpZC5nb3YuYmMuY2E6NDQz&hl=en&v=TnA7HacJFoBWt9hnlunBlYfK&size=invisible&anchor-ms=20000&execute-ms=30000&cb=gyvchtrft81t](https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LckweAnAAAAAP06dUhCg3zf0WTEXJNkV16V1EKw&co=aHR0cHM6Ly9iY2JpZC5nb3YuYmMuY2E6NDQz&hl=en&v=TnA7HacJFoBWt9hnlunBlYfK&size=invisible&anchor-ms=20000&execute-ms=30000&cb=gyvchtrft81t)
- `GET` `stylesheet` [https://www.gstatic.com/recaptcha/releases/TnA7HacJFoBWt9hnlunBlYfK/styles__ltr.css](https://www.gstatic.com/recaptcha/releases/TnA7HacJFoBWt9hnlunBlYfK/styles__ltr.css)
- `GET` `script` [https://www.google.com/recaptcha/api2/webworker.js?hl=en&v=TnA7HacJFoBWt9hnlunBlYfK](https://www.google.com/recaptcha/api2/webworker.js?hl=en&v=TnA7HacJFoBWt9hnlunBlYfK)
- `GET` `image` [https://www.gstatic.com/recaptcha/api2/logo_48.png](https://www.gstatic.com/recaptcha/api2/logo_48.png)
- `GET` `font` [https://fonts.gstatic.com/s/roboto/v48/KFO7CnqEu92Fr1ME7kSn66aGLdTylUAMa3yUBA.woff2](https://fonts.gstatic.com/s/roboto/v48/KFO7CnqEu92Fr1ME7kSn66aGLdTylUAMa3yUBA.woff2)
- `GET` `other` [https://bcbid.gov.bc.ca/dist/image/favicon-32x32.png?v=20260525113354](https://bcbid.gov.bc.ca/dist/image/favicon-32x32.png?v=20260525113354)
- `POST` `xhr` [https://www.google.com/recaptcha/api2/reload?k=6LckweAnAAAAAP06dUhCg3zf0WTEXJNkV16V1EKw](https://www.google.com/recaptcha/api2/reload?k=6LckweAnAAAAAP06dUhCg3zf0WTEXJNkV16V1EKw)
- `POST` `other` [https://bcbid.gov.bc.ca/bare.aspx/en/bas/js_log](https://bcbid.gov.bc.ca/bare.aspx/en/bas/js_log)
- `GET` `script` [https://bcbid.gov.bc.ca/dist/js/rfp_public_script.min.js?v=20260525113354](https://bcbid.gov.bc.ca/dist/js/rfp_public_script.min.js?v=20260525113354)
- `GET` `script` [https://bcbid.gov.bc.ca/dist/js/rfp_script.min.js?v=20260525113354](https://bcbid.gov.bc.ca/dist/js/rfp_script.min.js?v=20260525113354)
- `GET` `font` [https://bcbid.gov.bc.ca/dist/css/semantic-ui/assets/fonts/FontAwesome6/webfonts/fa-light-300.woff2](https://bcbid.gov.bc.ca/dist/css/semantic-ui/assets/fonts/FontAwesome6/webfonts/fa-light-300.woff2)
- `POST` `xhr` [https://bcbid.gov.bc.ca/ajax.aspx/en/rfp/request_browse_public?ivControlUIDsAsync=body:x:grid:upgrid&asyncmodulename=rfp&asyncpagename=request_browse_public](https://bcbid.gov.bc.ca/ajax.aspx/en/rfp/request_browse_public?ivControlUIDsAsync=body:x:grid:upgrid&asyncmodulename=rfp&asyncpagename=request_browse_public)

### API-Looking Endpoints Observed

- [https://bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public](https://bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public) | status=302 | type=unknown | keys=n/a | sample=`<body read failed: Response.text: Response body is unavailable for redirect responses>`
- [https://bcbid.gov.bc.ca/page.aspx/en/bas/browser_check](https://bcbid.gov.bc.ca/page.aspx/en/bas/browser_check) | status=200 | type=text/html | keys=n/a | sample=`<!DOCTYPE html> <html dir="ltr" lang="en"> <head> <title>Browser check: BC Bid </title> <meta charset="utf-8" /> <meta http-equiv="X-UA-Compatible" content="IE=Edge" /> <link rel="stylesheet" href="/bare.aspx/en/css/default_style/buyer_s...`
- [https://bcbid.gov.bc.ca/bare.aspx/en/fil/download_public/6b7373df-88bd-480d-8daf-850d9191c9c6](https://bcbid.gov.bc.ca/bare.aspx/en/fil/download_public/6b7373df-88bd-480d-8daf-850d9191c9c6) | status=200 | type=image/png | keys=n/a | sample=`<body read failed: 'utf-8' codec can't decode byte 0x89 in position 0: invalid start byte>`
- [https://bcbid.gov.bc.ca/bare.aspx/en/bas/js_log](https://bcbid.gov.bc.ca/bare.aspx/en/bas/js_log) | status=204 | type=unknown | keys=n/a | sample=`<body read failed: Response.text: Protocol error (Network.getResponseBody): No resource with given identifier found>`
- [https://bcbid.gov.bc.ca/ajax.aspx/en/rfp/request_browse_public?ivControlUIDsAsync=body:x:grid:upgrid&asyncmodulename=rfp&asyncpagename=request_browse_public](https://bcbid.gov.bc.ca/ajax.aspx/en/rfp/request_browse_public?ivControlUIDsAsync=body:x:grid:upgrid&asyncmodulename=rfp&asyncpagename=request_browse_public) | status=200 | type=text/html | keys=n/a | sample=`50|scriptToLoad||this.ClientID|/dist/js/rfp_public_script.min.js?v=20260525113354|43|scriptToLoad||this.ClientID|/dist/js/rfp_script.min.js?v=20260525113354|75716|updatePanel||body_x_grid_upgrid|<div id="body_x_grid_phcgrid" data-context...`

## Cookie Replay Test

- Same-session cookies set by the public page:
- `UserTimeZoneOffset` domain=`bcbid.gov.bc.ca` path=`/page.aspx/en/bas` httpOnly=False
- `UrlPrefixClientCookieNamebuyer_ssbc` domain=`bcbid.gov.bc.ca` path=`/page.aspx/en/bas` httpOnly=False
- `UserTimeZoneOffset` domain=`bcbid.gov.bc.ca` path=`/page.aspx/en/rfp` httpOnly=False
- `_GRECAPTCHA` domain=`www.google.com` path=`/recaptcha` httpOnly=True
- `ASP.NET_SessionId` domain=`bcbid.gov.bc.ca` path=`/` httpOnly=True

- Plain HTTP replay result: `WORKED`
- [https://bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public](https://bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public) -> status=200 final=https://bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public sample=`<!DOCTYPE html> <html dir="ltr" lang="en"> <head> <title>Opportunities: BC Bid </title> <meta charset="utf-8" /> <meta http-equiv="X-UA-Compatible" content="IE=Edge" /> <link rel="stylesheet" href=...`
- [https://bcbid.gov.bc.ca/page.aspx/en/bas/browser_check](https://bcbid.gov.bc.ca/page.aspx/en/bas/browser_check) -> status=200 final=https://bcbid.gov.bc.ca/page.aspx/en/bas/browser_check sample=`<!DOCTYPE html> <html dir="ltr" lang="en"> <head> <title>Browser check: BC Bid </title> <meta charset="utf-8" /> <meta http-equiv="X-UA-Compatible" content="IE=Edge" /> <link rel="stylesheet" href=...`
- [https://bcbid.gov.bc.ca/bare.aspx/en/fil/download_public/6b7373df-88bd-480d-8daf-850d9191c9c6](https://bcbid.gov.bc.ca/bare.aspx/en/fil/download_public/6b7373df-88bd-480d-8daf-850d9191c9c6) -> status=200 final=https://bcbid.gov.bc.ca/bare.aspx/en/fil/download_public/6b7373df-88bd-480d-8daf-850d9191c9c6 sample=`�PNG      IHDR   �   4   h��   sRGB �� �   gAMA  �� �a    pHYs  �  ��o�d  0IDATx^�] |������V[��ֶ�֪%��p��QDA�oD. $\��!G��hE�J�r !!$�lN$���J��a�s�&��wB8�>�0�f�r�����=��;����~O�yg�ۏ6�...`
- [https://bcbid.gov.bc.ca/bare.aspx/en/bas/js_log](https://bcbid.gov.bc.ca/bare.aspx/en/bas/js_log) -> status=204 final=https://bcbid.gov.bc.ca/bare.aspx/en/bas/js_log sample=``
- [https://bcbid.gov.bc.ca/ajax.aspx/en/rfp/request_browse_public?ivControlUIDsAsync=body:x:grid:upgrid&asyncmodulename=rfp&asyncpagename=request_browse_public](https://bcbid.gov.bc.ca/ajax.aspx/en/rfp/request_browse_public?ivControlUIDsAsync=body:x:grid:upgrid&asyncmodulename=rfp&asyncpagename=request_browse_public) -> status=200 final=https://bcbid.gov.bc.ca/ajax.aspx/en/rfp/request_browse_public?ivControlUIDsAsync=body:x:grid:upgrid&asyncmodulename=rfp&asyncpagename=request_browse_public sample=`<!DOCTYPE html> <html> <body> <form method="post" action="/ajax.aspx/en/rfp/request_browse_public?ivControlUIDsAsync=body:x:grid:upgrid&asyncmodulename=rfp&asyncpagename=request_browse_public" id="...`

## Track 1 Conclusion

- Identified opportunities endpoint: no standalone JSON/XHR opportunities API was exposed before the browser-check wall.
- Direct connector built this patch: `YES`
- Working approach: `plain_http_with_cookies+playwright_pagination`
- Cookie-unlocked listing rows parsed: `202`
- Sample titles:
- PHSA 12728 - BC Patient-Centred Data Collection and Reporting
- City of Abbotsford - Eastern Wellfield - Groundwater Exploratory Wells - Installation
- Repair Services for Audio, Visual, and Lighting Systems
- 2023-34- CLARES COVE LIFT STATION UPGRADES
- RUBY Rubidium Elution System
- Runtime conclusion: `OK_BROWSER_COOKIE_REPLAY`
- Reason: `The browser session set same-session cookies that allowed plain HTTP replay of the public opportunities HTML page.`

## Track 1b - Pagination Hardening (Patch 5.14)

- Pager control detected: `True` (`#body_x_grid_gridPagerBtnNextPage`, AJAX `GoToPageOfGrid`, no plain URL parameter)
- Grid total-record hint: `More than 150 Record(s)`
- Stop condition (Patch 5.16): closing-date relevance window (90 days), hard upper bound `15` pages
- Pages fetched this run: `15`
- Stop reason this run: `hard_cap_reached (15 pages)`
- Rows from page 1 only vs after pagination merge: see `parsed_rows` in DEMO_BUILD_REPORT.md BC Bid section.

## Track 1c - User-Assisted Headed Browser Fallback (Patch 5.18)

Compliant fallback for when the headless attempt lands on the browser-check
wall: opens a VISIBLE browser window to the same public page, never logs in,
never bypasses CAPTCHA, and waits for a person to let the page load (solving
any CAPTCHA themselves) before reading the now-public listing with the same
parser used for the headless path.

- Login attempted: NO (always)
- CAPTCHA bypass attempted: NO (always)
- Browser mode this run: `headless`
- User-assisted fallback used this run: `False`
- Public opportunities page loaded: `True`
- Rows parsed via this path: `202`
- If still blocked after the fallback: TENDER_FINDER reports `BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED`
  (not a fabricated "0 open civil" success) so this is never confused with BC Bid
  genuinely having no open civil tenders today.

## Track 2 - Official Feed / API Search

- [BC Bid resources](https://www2.gov.bc.ca/gov/content/bc-procurement-resources/bc-bid-resources) -> HTTP 200; final=https://www2.gov.bc.ca/gov/content/bc-procurement-resources/bc-bid-resources; notes=Keyword mentions are generic page text or metadata; no explicit public opportunities feed identified.
- [BC Bid for suppliers](https://www2.gov.bc.ca/gov/content/bc-procurement-resources/bc-bid-resources/bc-bid-for-suppliers) -> HTTP 200; final=https://www2.gov.bc.ca/gov/content/bc-procurement-resources/bc-bid-resources/bc-bid-for-suppliers; notes=Keyword mentions are generic page text or metadata; no explicit public opportunities feed identified.
- [BC Bid historical data](https://www2.gov.bc.ca/gov/content/bc-procurement-resources/bc-bid-resources/bc-bid-historical-data) -> HTTP 200; final=https://www2.gov.bc.ca/gov/content/bc-procurement-resources/bc-bid-resources/bc-bid-historical-data; notes=Keyword mentions are generic page text or metadata; no explicit public opportunities feed identified.
- [BC government API directory](https://api.gov.bc.ca/) -> HTTP 200; final=https://api.gov.bc.ca/; notes=No visible BC Bid listing on this page.
- [BC government developer portal](https://developer.gov.bc.ca/) -> HTTP 200; final=https://developer.gov.bc.ca/; notes=No visible BC Bid listing on this page.

## Final Assessment

- BC Bid is running on Ivalua-signaled assets (`ivalua.min.css` and Ivalua copyright headers in delivered JS).
- No official public RSS/API/export endpoint was identified from BC Bid's official resource pages or the BC government API/developer landing pages checked in this patch.
- The viable direct path in Patch 5.13 is browser-seeded session cookies plus plain HTTP replay of the public opportunities HTML page, not a documented feed/API.
- Future patches should not repeat plain HTTP sitemap/feed probing without first checking this audit.
