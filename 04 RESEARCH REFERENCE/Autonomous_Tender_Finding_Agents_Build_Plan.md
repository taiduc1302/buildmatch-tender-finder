# Autonomous Tender-Finding Agents for Example Civil Contractor Ltd. — Build Plan

## TL;DR
- Build **two agents**: (1) an **Active Tenders agent** that aggregates bid invitations from a shared inbox plus a fixed list of ~12 real BC/Lower Mainland portals into one Excel/Sheets tracker, and (2) a **Future Projects agent** that runs AI deep research twice weekly to surface upcoming subdivision/servicing work before it tenders. Recommended build stack: **Make.com as the orchestration backbone + Claude API for extraction, with Power Automate as the Microsoft-native alternative**, all writing to a shared spreadsheet.
- The highest-leverage move is **subscribing to free native email alerts** (BC Bid commodity-code e-notifications, every bids&tenders municipal portal, CivicInfo BC, BidCentral) into one shared inbox ("estimating@example.com"), then letting AI parse those emails — this captures the large majority of public opportunities reliably and legally without scraping.
- Total realistic running cost is **~$50–150/month** (Make.com Core + Claude/Perplexity usage), plus optional BidCentral Premium ($525 + GST + PST at the member rate) and ConstructConnect if private-GC coverage is wanted. Validate the Active agent **silently against Example Coordinator's manual list for several weeks** before relying on it.

## Key Findings

### Tender Finder's actual scope confirms which tenders matter
Example Civil Contractor Ltd. (tenderfinder.ca) is a Langley/Maple Ridge-based civil contractor doing excavation, utilities (water mains, storm/sanitary), roadworks, structural concrete, bridges and subdivision servicing. Its clients split into two clear channels that the agents must both cover:
- **Direct-to-owner public work**: City of Surrey (20th Ave Overpass), Vancouver Airport Authority, Ministry of Transportation, Semiahmoo First Nation, Maple Ridge (Albion Reservoir). These come through **public procurement portals**.
- **Subcontract/site-package work for GCs and developers**: Turner Construction, Polygon, Beedie, Bird, Chandos, Stuart Olson, DP World. These come through **GC invitation-to-bid systems and direct relationships**, not public portals.

This split is the single most important design fact: **no single portal covers Tender Finder's pipeline.** The Active agent needs both a public-portal channel and an email channel.

### The real BC / Lower Mainland tender sources (the fixed list for Agent #1)

**Tier 1 — Public portals, free, with native email alerts (must-monitor):**
- **BC Bid** (bcbid.gov.bc.ca) — provincial + broader public sector (municipalities, health, Crown corps, UBC, BC Hydro). Free to browse; requires Business BCeID to register. Suppliers subscribe to **UNSPSC commodity codes** and receive **one consolidated email per day** listing matching opportunities. This is the backbone provincial source.
- **bids&tenders** (bidsandtenders.ca) — the platform used by **Surrey, Maple Ridge, Burnaby, Metro Vancouver, Coquitlam** and many more Lower Mainland municipalities. Each municipality has its own subdomain (surrey.bidsandtenders.ca, mapleridge.bidsandtenders.ca, metrovancouver.bidsandtenders.ca, etc.). Free supplier account; sends a **daily email of all opportunities matching selected commodity categories + agencies**, and emails for invitations/addenda. Up to 10 company contacts per account all get notified.
- **CivicInfo BC** (civicinfo.bc.ca/bids) — aggregates BC municipal/regional-district bids. Offers **email alerts/weekly newsletter AND RSS feeds for bids & tenders** — the RSS feed is the single most automation-friendly source found.
- **City of Vancouver supplier portal** (separate from bids&tenders) — Vancouver runs its own supplier portal.
- **City of Coquitlam** — posts on its own site + uses QFile for submissions; also on bids&tenders.
- **TransLink** — uses Ariba Discovery; has a current-opportunities page.

**Tier 2 — Construction-industry marketplaces (paid, high value for subdivision/GC work):**
- **BidCentral** (bidcentral.ca) — the BC Construction Association's marketplace, "BC's largest." Per the Vancouver Island Construction Association, "Premium BidCentral access allows up to four users per account, each of whom has unlimited access to 600+ prebid projects and 4100+ current private and public project opportunities across BC," plus BidCentral On Demand by-invitation bidding "at no extra charge to you or the invited trade contractors." It includes plan rooms, ITB automation and automated new-project notifications. Pricing: the Northern Regional Construction Association states "NRCA MEMBERS RECEIVE A 40% DISCOUNT ON ANNUAL RATES | PAY ONLY $525 FOR BIDCENTRAL PREMIUM," while bidcentral.ca separately advertises a "60% Discount for Regional Construction Association Members" — so the member rate depends on which regional association Tender Finder joins; VICA quotes "$525 + GST + PST." This is the best single source for private and pre-bid subdivision/ICI work that never hits government portals.
- **ConstructConnect / SmartBid** — carries private and public construction tenders; also the platform many GCs use to send ITBs. Paid.
- **MERX** and **Biddingo** — national aggregators; MERX has a separate Private Construction product. Paid. Lower priority since BC Bid + bids&tenders + BidCentral already cover the BC public/private spread.

**Tier 3 — GC invitation-to-bid systems (where Tender Finder's subcontract work actually arrives):**
- **BuildingConnected/Autodesk** — the dominant ITB platform; all invites come from **team@buildingconnected.com** and land in estimators' inboxes and a "Bid Board." Tender Finder should maintain a complete subcontractor profile (scopes + service area) so GCs invite them.
- **SmartBid, Pipeline Suite, iSqFt/ConstructConnect** — other GC bid-distribution tools. These all distribute via email, which is why the **shared inbox is the capture mechanism** for this entire channel.

**Tier 4 — Future-projects intelligence (Agent #2 sources, no tenders yet):**
- **BC Major Projects Inventory** — quarterly Excel/PDF of all BC projects ≥ $15M. NOTE: the Province announced **no further MPI reports after Q3 2025**, page online only until June 30, 2026 — a degrading source, so Agent #2 must not depend on it.
- **Municipal development/subdivision application tracking** (e.g., City of Vancouver development applications, building-permit open data with daily-updated API) — early signal of servicing work 6–18 months out.
- **Council agendas, servicing agreements, developer announcements, real-estate/industrial development news** — the unstructured sources deep research is good at.

### Tooling reality check (2026)
- **Claude Cowork** (Anthropic's desktop agent, in Claude Pro/Max, ~$100–200/mo Max) can read local files, browse via Chrome, generate Excel/PowerPoint, and **run scheduled recurring tasks** — but it's macOS-first, in research preview, Gmail MCP works in Chat not Cowork, and "Chrome automation is slow due to screenshot round-trips." Good for the morning-report synthesis and Future agent; **not reliable as the always-on email-capture engine.**
- **Claude's native Microsoft 365 connector** exists in 2026 and reads Outlook/SharePoint/OneDrive/Teams — but it is **READ-ONLY** (cannot write to a spreadsheet) and is a conversational tool, not a triggered automation. So Claude must be invoked **via API inside an orchestrator** for the write step.
- **Make.com** — has a native Microsoft 365/Outlook "watch emails" trigger, native **Anthropic Claude + OpenAI + Gemini** modules to parse email text to JSON, and Google Sheets/Excel "add row" modules. Per 2026 pricing reviews of make.com/en/pricing, the **Core plan is $10.59/month billed annually for 10,000 credits/month** with unlimited active scenarios and a 1-minute minimum interval (Make switched from "operations" to "credits" on Aug 27, 2025; each module run = 1 credit, AI modules cost more). This is the cheapest true end-to-end automation and the recommended backbone.
- **Power Automate** — Microsoft-native; "When a new email arrives in a shared mailbox" is a **standard (free with M365) trigger**; AI Builder does extraction but its credit model changed (Copilot Credits at $0.01 each; the seeded 5,000 credits/month bundled with Premium are being removed Nov 1, 2026). Best fit given Tender Finder already runs Outlook/Office, but watch AI Builder cost.
- **Zapier** — works but per-task pricing escalates at volume; its free Email Parser is template-only and too rigid for variable bid emails (use AI steps instead).

### Legal/scraping position
Canadian courts have repeatedly found **scraping in violation of a site's Terms of Use unlawful** (Toronto Real Estate Board v. Mongohouse, 2019 Federal Court; Century 21 v. Zoocasa; the 2024 CanLII v. Caseway claim). The safe, decisive rule for Tender Finder: **do not scrape any portal that has a ToS prohibiting it or that requires login.** Instead use the **official, free, sanctioned distribution channels** every one of these portals already offers — email alerts and RSS. This is legally clean, more reliable, and lower-maintenance than scraping.

## Details

### AGENT #1 — ACTIVE TENDERS ("zero tolerance for misses")

**Architecture (recommended): Shared inbox + Make.com + Claude API → shared spreadsheet**

**Step 1 — Create the capture point.** Set up the shared mailbox Example Reviewer proposed (e.g., **estimating@example.com** / "Tender Finder Estimating Opportunities") in Microsoft 365. Then:
- Subscribe THIS inbox to **every free native alert**: BC Bid commodity-code e-notifications; bids&tenders daily-opportunity emails for Surrey, Maple Ridge, Burnaby, Metro Vancouver, Coquitlam (+ any other target municipalities), selecting civil/earthwork/utility/road commodity categories; CivicInfo BC alerts; BidCentral notifications; City of Vancouver portal alerts; TransLink/Ariba.
- Have estimators (Estimator A, Estimator B, Estimator C, Estimator D, Estimator E) set **auto-forward rules** from their personal inboxes for any GC ITB emails (BuildingConnected team@buildingconnected.com, SmartBid, iSqFt, direct developer invites) into estimating@example.com. This consolidates the scattered invitations Example Reviewer described and captures the entire Tier-3 GC channel that no portal exposes.

**Step 2 — Parse with AI.** In Make.com: "Watch emails" on the shared mailbox → Anthropic Claude module with a fixed extraction prompt that returns JSON for: project name, owner/GC, type (subdivision / building-site / road / utility), sector (gov/private/non-profit), location, scope summary, tender close date, source link, date found, source channel. **Claude Haiku 4.5 ($1/$5 per million input/output tokens) — the cheapest current-generation model per Anthropic's platform.claude.com pricing docs — is ideal for this high-volume extraction**, with Sonnet 4.6 ($3/$15) as the fallback for messy emails.

**Step 3 — Add the RSS/portal channel.** Add a Make.com scheduled scenario that reads the **CivicInfo BC RSS feed** (and any other RSS the portals expose) → same Claude parse → same sheet. For portals offering only email, the Step-1 alerts already cover them, so scraping is unnecessary.

**Step 4 — Deduplicate.** Before writing a row, query the sheet for a match on a composite key (normalized project name + owner + close date, or source link). If found, append the new source channel to the existing row's "source channel" field instead of creating a duplicate. This handles the same tender arriving via email + RSS + a GC invite.

**Step 5 — Write to the shared spreadsheet** (Excel Online or Google Sheets) with the fields above + a "status" column (New / Reviewing / Bidding / No-bid). Send a Make.com/Claude-generated **morning digest** to the estimating team.

**Why Make.com over Power Automate as the default:** native multi-model AI modules, lowest cost, and not dependent on the Nov-2026 AI Builder credit changes. **Choose Power Automate instead if** Tender Finder's IT prefers everything inside the Microsoft tenant for governance — the shared-mailbox trigger is free and it writes natively to Excel Online; just budget Copilot Credits for AI Builder.

### AGENT #2 — FUTURE PROJECTS (twice weekly, softer accuracy)

Implement Example Reviewer's two-stage design:
1. **Broad collection (overnight):** A deep-research pass using **Perplexity (Sonar/Deep Research)** or **Gemini/ChatGPT deep research** across council agendas, development-application trackers, Major-Projects-type data, developer/industrial news, and the Tier-1/2 portals' "pre-bid" sections. Keywords are auto-generated by feeding Claude Tender Finder's defined scope (excavation, servicing, subdivision, storm/sanitary, water main, road, site prep) and target geography (Lower Mainland municipalities).
2. **Analysis/synthesis (morning):** Claude (Cowork or API) reads the raw collection, dedupes against Agent #1's sheet, scores relevance to Tender Finder's scope, and writes "future" rows + a readable morning report (project, likely owner/developer, estimated tender window, why it fits Tender Finder, source link).

Run **Tuesday & Thursday overnight** to balance token cost vs. coverage, exactly as Example Reviewer suggested.

### Keyword generation method
Feed the AI a one-paragraph scope statement and have it output (a) UNSPSC commodity codes to subscribe to on BC Bid/bids&tenders, and (b) free-text search keywords for deep research. Re-run quarterly as scope evolves.

## Cost and token considerations
- **Make.com Core:** $10.59/month billed annually (10,000 credits/month) — sufficient for the email-parse + RSS volume Tender Finder will see; AI module runs cost extra credits, so monitor usage.
- **Claude API for parsing:** pennies per email at Haiku 4.5 ($1/$5 per million tokens) or Sonnet 4.6 ($3/$15) rates; realistically **<$20/month** at Tender Finder's volume. Alternatively a **Claude Pro ($20/mo) or Max ($100/mo)** seat on the dedicated Tender Finder account powers Cowork + the synthesis/morning-report work.
- **Perplexity** for Agent #2: Pro is **$20/month or $200/year (~$16.67/mo)**, advertised as "unlimited Pro Search plus 20 Deep Research queries per day" per FelloAI's 2026 breakdown — **however, Perplexity's enterprise matrix now lists Pro Deep Research capped at 20 per month, and there was 2026 user backlash over the cut, so confirm the current limit before committing to twice-weekly runs.** If metered via API, Sonar Deep Research is ~$0.30–$1.30 per deep query.
- **Paid portals (optional but recommended):** BidCentral Premium at the member rate ($525 + GST + PST, requires regional construction association membership); ConstructConnect/MERX only if private-GC coverage proves thin.
- **All-in realistic monthly run cost: ~$50–150/month** software, plus the BidCentral annual subscription. This is trivial against a single missed subdivision tender.

## Recommendations (staged, decisive)

**Stage 0 (Week 1) — Foundations.** Create estimating@example.com shared mailbox on the dedicated Tender Finder Claude/Microsoft work account. Register on BC Bid (Business BCeID) and every target bids&tenders municipality; subscribe to commodity-code alerts. Subscribe to CivicInfo BC alerts/RSS and BidCentral. Set estimator auto-forward rules for GC ITB emails.

**Stage 1 (Weeks 2–3) — Build Agent #1 in Make.com.** Email-watch → Claude parse → dedupe → shared sheet → morning digest. Add the CivicInfo RSS scenario.

**Stage 2 (Weeks 3–6) — Silent validation.** Run Agent #1 in parallel with Example Coordinator's manual tracking **without telling her**. Each week, compare the agent's sheet to Example Coordinator's list: every tender Example Coordinator has that the agent missed is a defect to fix (usually a missing alert subscription or a parse failure). **Benchmark to relax/rely-on: the agent captures 100% of Example Coordinator's items for 3 consecutive weeks** before it becomes the system of record.

**Stage 3 (Weeks 4–6, parallel) — Build Agent #2.** Twice-weekly Perplexity/Gemini collection + Claude synthesis → future rows + morning report.

**Stage 4 — Ongoing.** Quarterly keyword/commodity-code refresh; review whether BidCentral/ConstructConnect/MERX paid coverage is earning its keep based on how many won bids originated there.

**Thresholds that change the plan:**
- If Make.com volume exceeds ~10,000 credits/month → upgrade tier or move to Power Automate inside the tenant.
- If the silent validation shows the agent missing >5% of Example Coordinator's items after fixes → keep manual tracking as primary and treat the agent as a backstop until parity.
- If a target portal's ToS forbids automated access and offers no alert/RSS → keep it as a manual weekly check, do not scrape.

## Caveats
- **Claude Cowork is research-preview, macOS-first, and Gmail-MCP-only in Chat mode** — do not architect the always-on email capture on Cowork; use Make.com/Power Automate for the reliable trigger layer and reserve Cowork/Claude for synthesis and reporting.
- **bids&tenders/BC Bid alert reliability depends on commodity-code selection** — too narrow misses tenders, too broad floods the inbox. The AI parse layer lets Tender Finder subscribe broadly and filter in software, which is the safer setting for a zero-miss requirement.
- **BC Major Projects Inventory is being discontinued** after Q3 2025 — Agent #2 must lean on development-application trackers, council agendas and news instead.
- **Scraping law in Canada is unsettled and trending restrictive** — the plan deliberately avoids ToS-violating scraping in favor of sanctioned alerts/RSS/APIs.
- Some figures (exact BidCentral pricing tiers, Make/Claude monthly totals, the Perplexity Deep Research daily-vs-monthly limit) come from 2026 third-party sources and should be confirmed against official pricing pages before purchase.
- The plan assumes Tender Finder can set auto-forward rules and create a shared mailbox in its Microsoft 365 tenant; if IT policy blocks auto-forwarding, use a distribution list or shared-mailbox delegation instead.