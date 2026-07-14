# Example Civil Contractor — "Future Projects" Intelligence Agent (Agent #2): Architecture, Data Sources & Recommendations

## TL;DR
- **Build Agent #2 as two distinct horizon variants feeding one shared tracker.** HORIZON A (near-term, 1–3 months) should be driven mostly by *structured* feeds (BidCentral pre-bid, Surrey's ArcGIS development-applications API, municipal council agendas, Metro Vancouver/TransLink/Infrastructure BC pipelines); HORIZON B (early signal, 6–18 months) is where fuzzy LLM "deep research" earns its keep, scanning rezoning/subdivision application trackers, OCP amendments, and development news.
- **Recommended AI architecture: a hybrid orchestrated pipeline — a scheduled Python script (GitHub Actions cron) that (1) pulls structured open-data/RSS feeds directly, (2) calls a deep-research model (Gemini Deep Research API or Perplexity Sonar Deep Research) for broad overnight web collection, and (3) calls the Claude API to dedupe, score against TENDER_FINDER's scope, and write rows + a morning report.** For a non-developer path, Claude Cowork scheduled tasks is the strong runner-up and the fastest to stand up. Realistic cost at twice-weekly cadence: roughly US$30–90/month.
- **The BC Major Projects Inventory is dead** (final Q3 2025 issue; page offline after June 30, 2026). Replace it with the Infrastructure BC "Major Infrastructure Projects Brochure" (semi-annual, public-sector, $50M+) plus the structured municipal application feeds. Treat all LLM deep-research output as leads to verify, never as facts.

## Key Findings

### The data landscape is split: structured where you least need fuzziness, fuzzy where you most need breadth
The single most important design insight is that the two horizons have opposite data characteristics:
- **Near-term (Horizon A)** signals live overwhelmingly in *structured or semi-structured* sources with APIs, RSS, or downloadable datasets — exactly the things you should NOT use an LLM to "discover," because direct ingestion is more reliable and far cheaper.
- **Early-signal (Horizon B)** lives in a long tail of rezoning trackers, council PDFs, OCP amendments, developer press releases, and real-estate/industrial news — heterogeneous, often human-readable-only, and genuinely well-suited to LLM deep research that can read and compact hundreds of pages.

This split should drive the whole build: deterministic feeds first, LLM breadth second.

### Data source automation-friendliness varies sharply by municipality
- **City of Surrey** is the best automation target in the region. Its "Development Applications" dataset (data.surrey.ca, CKAN) — described as "Historic and current sites of Land Development Applications (rezoning, subdivision etc.)" — is available as JSON, GeoJSON, KML, FGDB and via an ArcGIS REST API at gisservices.surrey.ca/arcgis/rest/services. Surrey exposes 400+ layers via RSS, CKAN Action API and ArcGIS REST. This single layer covers rezoning + subdivision + development applications and is the highest-value structured feed for TENDER_FINDER.
- **City of Vancouver** is split. Building permits are a first-class API (opendata.vancouver.ca "issued-building-permits", current-year extract updated daily, CSV/JSON, data since 2017), and zoning is a weekly-updated dataset — but rezoning and development-permit *applications* are human-readable pages/maps only (shapeyourcity.ca/rezoning, vancouver.ca/devapps), with **no CSV/JSON API**. A third party (CityHallWatch) has manually snapshotted these monthly since 2013 precisely because no structured feed exists. These require LLM "reading" of public pages rather than a clean data pull.
- **Township of Langley** publishes a Development Activity Map + Portal and, importantly, a "Development Activity Status Table" on its ArcGIS open-data hub (data-tol.opendata.arcgis.com) — structured and automatable. (Note: as of February 2, 2026 all development applications must be submitted digitally through MyTownship.)
- **Maple Ridge** publishes "Active Development Applications" and a "Land Development Application Viewer" on its ArcGIS hub (opengov.mapleridge.ca / opengov2-mapleridge.opendata.arcgis.com) — structured/automatable.
- **City of Langley** runs a human-readable Development Application Portal plus monthly reports (no API noted); each listing carries applicant + project description (e.g., unit counts, rezoning/DP type).
- Most other municipalities (Burnaby, Coquitlam, Port Coquitlam, Pitt Meadows, Abbotsford, Mission, Delta, Richmond, New Westminster, North/West Vancouver, plus Metro Vancouver and Fraser Valley regional districts) publish development-application maps/lists of varying structure; North Vancouver District's GEOweb offers 170+ weekly-refreshed open datasets. Expect a mix of ArcGIS hubs (automatable) and PDF/HTML (LLM-readable).

### The provincial signal layer has just changed
- **BC Major Projects Inventory (MPI): discontinued.** The gov.bc.ca page states verbatim: "The Q3 2025 issue is now available. No further reports will be produced. This page will remain online until June 30, 2026. After that, access MPI reports from 2004–2025 through the Legislative Library of BC." MPI listed public+private projects "$15 million (Can.) or greater ($20 million or greater in the Lower Mainland)," quarterly, with free Excel/CSV — a genuine loss of a structured early-signal feed. (A legacy geospatial layer, "Major Projects Inventory (Economic) – Points," still sits in the BC Geographic Warehouse/open.canada.ca with CSV/KML, but it is being wound down with the publication.)
- **Best replacement: Infrastructure BC's "BC Major Infrastructure Projects Brochure."** It "focuses on prospective projects from the early planning stage through to pre-procurement, and active procurement that are $50 million and above," released "in the spring and fall of each year," as a free PDF. Caveats: public-sector only (no private), $50M threshold (higher than MPI's $15M), and PDF-only (not a structured dataset) — so it must be parsed/LLM-read, not API-pulled.
- **BC Bid** (bcbid.gov.bc.ca) lists open/closed opportunities but has **no dedicated "upcoming/advance" pipeline feed**; Notices of Intent and RFIs are the only forward signals and are issued case-by-case. (Covered-procurement thresholds changed Jan 1, 2026.)
- **Regional capital pipelines (all public, mostly PDF):** TransLink 2026 Business Plan & Capital Budget and the 2025 Ten-Year Investment Plan (Surrey-Langley SkyTrain, Pattullo Bridge replacement, the three selected BRT corridors); **Metro Vancouver "Current and Upcoming Projects" bidding page** (water/wastewater/solid-waste — directly TENDER_FINDER-relevant for utilities/servicing); City of Vancouver capital plan; BC Hydro and BC Ministry of Transportation capital plans. These are the backbone of direct-to-owner public lookahead.

### Commercial construction-intelligence providers exist but are paid and BC-coverage-variable
- **BidCentral** (bidcentral.ca, an initiative of the BC Construction Association) is the most BC-relevant. Per its own Prebid FAQ, "'Prebid' is information about a future construction project, available before the project is out to tender… BidCentral staff gathers information from hundreds of different public sources… local and municipal governments post zoning applications and building permits," updated **daily**. Premium gives "up to four users per account… unlimited access to 600+ prebid projects and 4100+ current private and public project opportunities across BC," with keyword email alerts and a permits-intelligence layer (PermitsCA). Pricing: ~$875/yr list, with steep regional-association discounts (NRCA: "PAY ONLY $525 FOR BIDCENTRAL PREMIUM"; VICA cites a 60% member discount on annual purchases). **This is the single highest-value paid add-on for TENDER_FINDER** — it already does much of Horizon A's collection.
- **ConstructConnect** (Daily Commercial News / Project Intelligence) covers Canada incl. BC with pre-construction leads and a Bid Center; **BCI Central is now rebranded "LeadManager"**; **BuildCentral** specializes in early-stage leads but is more US-centric. These are subscription products (typically four-figure annual). Assess relevance versus BidCentral, which is purpose-built for BC and likely sufficient.

### AI deep-research and automation tooling (current as of June 2026)
- **Gemini Deep Research** now has a real API — the Interactions API, with agents `deep-research-preview-04-2026` and `deep-research-max-preview-04-2026` ("Maximum comprehensiveness for automated context gathering and synthesis"). It runs async/background (start task → poll), supports document grounding, and is well-suited to programmatic overnight collection. Consumer Gemini also offers "Scheduled Actions" (Google AI Pro/Ultra, up to 10 active actions) that run recurring research with citations.
- **Perplexity Sonar Deep Research** API: per Perplexity's pricing docs and CloudZero (2026), sonar-deep-research bills $2/M input + $8/M output, plus citation tokens (~$2/M), reasoning tokens (~$3/M), and search-query fees ($5 per 1,000 queries); CloudZero estimates "Total: ~$0.30 to $1.30+ per query, depending on context depth," with reasoning tokens "the biggest driver." Consumer-tier Deep Research limits are in flux/disputed (June 2026 trackers variously cite "20 Deep Research queries per day" on Pro) — so do not rely on a consumer subscription; the **API has no such cap** (pay-per-use).
- **Claude API web search** is, per Anthropic's official docs, "$10 per 1,000 searches" plus token costs (Sonnet 4.6 at $3/$15 per MTok); the Batch API gives "a 50% discount on both input and output tokens," and failed searches are not billed. Ideal for the synthesis/scoring/write stage.
- **Claude Cowork scheduled tasks** (shipped Feb 25, 2026; all paid plans — Pro/Max/Team/Enterprise) run recurring agentic workflows (collect→synthesize→write files) with connectors/skills/plugins, on hourly/daily/weekly/weekday cadences. Key limitation per Anthropic's help docs: scheduled tasks "only run while your computer is awake and the Claude Desktop app is open" (skipped runs auto-execute on next wake). **Claude Cloud Routines run server-side without your machine** and are the better unattended option. This is the no-code path and uses TENDER_FINDER's chosen Claude.
- **ChatGPT** has scheduled Tasks (Plus: ~10 Deep Research/month) and Agent mode, but Deep Research "does not independently verify facts," and it cannot reliably write directly to Excel.
- **Orchestration backbone for a Microsoft-365 shop:** Power Automate is the native fit (bundled in M365, native Excel/SharePoint/Outlook connectors, enterprise governance) but premium connectors add cost and its logic is brittle for heavy data transformation; n8n (self-host, free/flat-rate, the strongest LLM/agent nodes, Microsoft Graph for Excel) is the most flexible; Make is the visual middle ground; a plain Python script on GitHub Actions cron is the cheapest and most controllable.

## Details

### HORIZON A — NEAR-TERM (1–3 months to tender)
**Goal:** catch work nearly ready to tender so TENDER_FINDER can pre-position with GCs/owners and get on bid lists.

**Best-fit sources (priority order):**
1. **BidCentral pre-bid section** — purpose-built for projects "available before the project is out to tender," refreshed daily, with keyword alerts. Highest-yield single source for near-term lookahead.
2. **Municipal council agendas & minutes** — servicing agreements, award recommendations, capital approvals (Surrey, Langley Township/City, Maple Ridge, etc.). Mostly PDF/HTML on council portals; some offer RSS/calendar feeds. LLM reading is appropriate here.
3. **Surrey Development Applications API filtered to "Final Approval"/subdivision-plan stage** — Surrey states that after final approval and once the Approving Officer signs the subdivision plan, "servicing and construction can begin." Filtering the structured feed by stage yields precise near-term signals.
4. **Metro Vancouver "Current and Upcoming Projects"** (water/sewer/solid waste) and **GC prequalification notices** (Turner, Bird, Chandos, etc.).
5. **Infrastructure BC brochure** pre-procurement/active-procurement entries ($50M+ public).

**Best AI approach for Horizon A:** *structured-data-first*. Ingest BidCentral alerts (email→parse), Surrey/Langley/Maple Ridge ArcGIS feeds, and Metro Vancouver pages directly; use the LLM only to (a) read council-agenda PDFs and (b) classify/score. Accuracy matters more here, so lean on deterministic feeds.

### HORIZON B — EARLY SIGNAL (6–18 months out)
**Goal:** see subdivisions/servicing forming at the rezoning/application stage, long before tender.

**Best-fit sources:**
1. **Development/rezoning/subdivision application trackers** — Surrey (API), Langley Township (ArcGIS status table), Maple Ridge (ArcGIS), Vancouver (scrape/LLM-read), City of Langley (portal). A *rezoning + subdivision application* is the canonical 6–18-month civil-servicing signal for TENDER_FINDER.
2. **Building-permit open data** as trailing confirmation (Vancouver API; others where available).
3. **OCP / Neighbourhood Concept Plan (NCP) amendments** — Surrey NCPs in particular are strong subdivision precursors.
4. **Real-estate & industrial/logistics development news**, developer announcements (Polygon, Beedie, Wesgroup, etc.), land-assembly news, port/DP World expansions.
5. **Infrastructure BC brochure "early planning" entries**; provincial capital plans.

**Best AI approach for Horizon B:** *LLM deep research* for the overnight broad sweep (exactly Example Reviewer's two-stage concept), because the sources are heterogeneous and largely unstructured. False positives are tolerable here.

### The recommended architecture (primary): Hybrid orchestrated pipeline
A scheduled job (Tuesday & Thursday overnight) that:
1. **Collect — structured:** Python pulls Surrey/Langley/Maple Ridge ArcGIS JSON, the Vancouver building-permits API, Metro Vancouver/TransLink pages, and parses BidCentral alert emails from Outlook.
2. **Collect — fuzzy:** calls **Gemini Deep Research API** (or Perplexity Sonar Deep Research) with TENDER_FINDER's scope-derived keyword/UNSPSC query set to sweep news, developer sites, and council postings, returning a cited digest.
3. **Synthesize:** **Claude (Sonnet 4.6 via API, Batch mode)** dedupes against the active-tender tracker (Agent #1's output) and prior "future" rows, scores each item against TENDER_FINDER's scope rubric, and emits structured rows + a Markdown morning report.
4. **Write:** rows appended to the shared Excel/Google Sheet (via Microsoft Graph for Excel-on-SharePoint), report delivered to Outlook/Teams.

**Why this has priority:** it puts deterministic, hallucination-free structured feeds at the core (where Horizon A accuracy matters), uses the LLM only where it adds unique value (unstructured Horizon B breadth + scoring/writing), is pay-per-use cheap, and runs truly unattended (GitHub Actions cron) rather than depending on a desktop being awake.

**Orchestration choice:** For TENDER_FINDER's Microsoft-365 + technical-builder context, the cheapest/most controllable is a **Python script on GitHub Actions cron**; **Power Automate** is the native M365 alternative (excellent for the final Excel/Outlook write even if Python does collection); **n8n** if they want a visual, self-hosted agent platform with first-class LLM nodes.

### Alternative architectures (for the user to choose from)
- **(B) Claude-centric, no-code: Claude Cowork scheduled task.** One scheduled Cowork task twice weekly does collect (via web search / Firecrawl MCP) → synthesize → write to a file/sheet. *Pros:* fastest to build, no code, uses TENDER_FINDER's chosen Claude, full connector/skill access. *Cons:* by default only runs while the desktop machine is awake and the app is open — mitigate with a dedicated always-on PC or by using **Claude Cloud Routines** (server-side). Strong runner-up; ideal for a fast pilot.
- **(C) Deep-research-tool-centric, low-effort: Gemini Scheduled Actions or ChatGPT scheduled Tasks.** A recurring prompt produces a morning report with citations; a human pastes/exports rows. *Pros:* trivial setup, ~$20/mo. *Cons:* no reliable direct write to Excel, monthly Deep Research caps, weakest dedup/scoring. Good as a 1-week proof of concept only.
- **(D) Structured-data-first only (no deep research).** Ingest only APIs/feeds; LLM used purely to classify. *Pros:* cheapest, most reliable, zero hallucination. *Cons:* misses the unstructured early-signal tail (news, announcements) that is Horizon B's whole point. **Best deployed as the foundation layer under any of the above.**

### Relevance scoring & deduplication
- **Scoring rubric (LLM, 0–100):** strongly upweight subdivision/land-servicing, underground utilities (water/storm/sanitary), bedding gravel, manholes, roadworks, site/structural concrete, footings/foundations, bridges; downweight vertical building/GC scope and vague-scope work; weight by location (Surrey/Langley/Maple Ridge core, then wider Lower Mainland), by owner/developer match to TENDER_FINDER's known clients (City of Surrey, YVR/Vancouver Airport Authority, BC MoTI, Semiahmoo First Nation, Maple Ridge; Turner, Polygon, Beedie, Bird, Chandos, Stuart Olson, DP World), and by stage (apply Horizon A/B tags). Anchor the rubric with TENDER_FINDER's one-paragraph scope statement.
- **Keyword/UNSPSC generation:** feed the scope paragraph to an LLM quarterly to emit (a) UNSPSC commodity codes (earthmoving/excavating, site preparation, sewer/water main construction, road construction, structural concrete families) and (b) free-text keywords; store in a config the pipeline reads. Re-run quarterly per Example Reviewer's plan.
- **Dedup:** fuzzy-match on project name + address/coordinates + owner against (i) the active-tender tracker (Agent #1) and (ii) existing future rows; assign a stable project ID so the same project is collapsed as it migrates Horizon B→A, with a status field tracking the transition.

### Costs & run-frequency
At twice-weekly cadence (~8 runs/month):
- **Hybrid (recommended):** deep research at ~$0.30–$1.30/query (Perplexity Sonar Deep Research) or comparable Gemini API cost × a handful of queries/run, plus Claude Sonnet 4.6 synthesis (Batch = 50% off, so ~$1.50/$7.50 per MTok) — realistically **US$30–90/month** all-in; GitHub Actions free tier likely covers compute.
- **Claude Cowork:** covered by a Claude Pro/Max seat (~$20–100/mo) the team likely already wants.
- **Deep-research-tool-centric:** ~$20/mo (one Gemini AI Pro or ChatGPT Plus subscription).
- **Commercial data (optional):** BidCentral Premium (~$525–875/yr depending on association discount) is the highest-value paid add; ConstructConnect/LeadManager are four-figure annual.
- **Cadence tuning:** twice weekly is sensible; if token cost is a concern, run the expensive deep-research sweep weekly and the cheap structured pull twice weekly. Because false positives are tolerable, you can also widen the deep-research net without much downside beyond review time.

### Risks, legal, reliability
- **Prefer official APIs/open-data/RSS over scraping.** Canadian law (PIPEDA) and recent case law (the Federal Court's Mongohouse/Toronto Real Estate Board injunction, which held unauthorized scraping/circumvention illegal) make scraping of protected or ToS-restricted content risky. Public open-data under municipal open licences (Surrey, Vancouver, Langley, Maple Ridge ArcGIS hubs) is safe and intended for reuse. Where only web pages exist (Vancouver applications, council PDFs), respect robots.txt, rate-limit (1–2s between requests), identify the bot with a clear User-Agent, avoid logins/PII, and prefer LLM "reading" of public pages over bulk scraping/republishing.
- **Hallucination:** LLM deep research can fabricate project names, dates, and values. Mitigate by (a) requiring a source URL per row, (b) flagging any row whose claim isn't backed by a fetchable source as "unverified," (c) cross-checking high-value items against the structured feeds, and (d) treating Horizon B output as leads, not facts. Cross-model checking (e.g., Claude validating Gemini's digest) further reduces error.
- **Validation loop:** have an estimator (e.g., Example Coordinator, who already tracks tenders manually) spot-check a weekly sample; track which surfaced "future" rows later became real tenders to tune the scoring rubric quarterly. This conversion-tracking is also your best ROI metric.

## Recommendations
1. **Stage 1 (week 1–2): Stand up the structured foundation (Option D layer).** Wire Surrey, Langley Township, and Maple Ridge ArcGIS development-application feeds + the Vancouver building-permits API + a BidCentral Premium subscription with keyword alerts into the shared sheet. This alone delivers most of Horizon A with near-zero hallucination risk and the lowest cost.
2. **Stage 2 (week 3–4): Add the LLM synthesis/scoring brain.** Use the Claude API (Sonnet 4.6, Batch) to dedupe against Agent #1, score against the scope rubric, and write the morning report + future rows. Generate the UNSPSC + keyword config from the scope paragraph and schedule a quarterly refresh.
3. **Stage 3 (month 2): Add the fuzzy overnight sweep (Horizon B).** Add the Gemini Deep Research API (or Perplexity Sonar Deep Research) for the unstructured news/announcement/council tail, twice weekly. If the team wants a no-code first step, prototype this as a Claude Cowork scheduled task (on an always-on PC or via Cloud Routines) before committing to the full orchestrated pipeline.
4. **Orchestrate** with a Python GitHub Actions cron (primary, unattended, cheap) or Power Automate for the M365-native Excel/Outlook write step.
5. **Benchmarks that change the plan:**
   - If **>30% of Horizon B rows are unverifiable hallucinations**, cut deep-research breadth and lean structured.
   - If **BidCentral alone surfaces most near-term wins**, deprioritize the council-agenda LLM reading to save tokens.
   - If **Perplexity's consumer caps bite**, switch deep research to the Gemini or Perplexity *API* (pay-per-use, no cap).
   - If **conversion (future row → real tender) is high for one municipality**, weight its feed more heavily and consider a paid commercial provider only if a coverage gap is proven.

## Caveats
- Perplexity's 2026 consumer Deep Research limits are disputed and unconfirmable from official sources (trackers cite figures as varied as "20/day" on Pro) — verify in-app before relying on a consumer subscription. The APIs (Gemini, Perplexity Sonar, Claude) are the reliable automation path.
- The Infrastructure BC brochure is public-sector only, $50M+, and PDF-only; it does not replace MPI's private-sector coverage — the municipal application feeds fill that gap.
- Vancouver development/rezoning *applications* have no structured API; everything else for Vancouver (building permits, zoning) does. Several smaller Lower Mainland municipalities were not individually verified for API availability and should be checked one-by-one during Stage 1.
- BC Bid has no confirmed structured "upcoming opportunities" API; treat it as an active-tender source (Agent #1's domain), not a future-projects feed.
- Cost figures are estimates based on June 2026 published pricing and depend on query depth/volume; validate against a one-month pilot.
- Claude Cowork's "machine must be awake" limitation makes plain scheduled tasks unsuitable for true unattended overnight runs unless paired with an always-on device or Claude Cloud Routines.
