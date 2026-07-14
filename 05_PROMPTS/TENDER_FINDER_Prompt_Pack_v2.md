# TENDER_FINDER Prompt Pack v2 — the 5 prompts that run the system

Five archetypes cover all 68 sources. Sites add *connectors*, not prompts.
Each prompt is reusable: swap the `{{PLACEHOLDERS}}` and run.

| # | Prompt | Operates on | Layer |
|---|--------|-------------|-------|
| P1 | Universal scope-scoring | the raw sweep rows (any API/RSS/email-derived record) | REFINE — the workhorse |
| P2 | Active-tender parser | a tender email / notice (BC Bid, bids&tenders, GC ITB…) | Horizon A capture |
| P3 | Unstructured dev-app extractor | a PDF/HTML list or planning report (Surrey, Richmond, Langley monthly) | COLLECT for non-API sources |
| P4 | Council-agenda + capital-plan extractor | a council/committee agenda or a capital plan PDF | Horizon B early signal |
| P5 | Weekly dedup + roll-up | the week's scored leads from P1–P4 | normalize + Example Reviewer's digest |

---

## Shared blocks (paste into each prompt where referenced)

**`{{TENDER_FINDER_SCOPE}}`**
```
Example Civil Contractor is a civil / earthwork contractor based in Langley / Maple Ridge, BC.
TENDER_FINDER-fit scopes: site servicing, subdivision servicing, excavation, bulk earthworks,
underground utilities, storm, sanitary, watermain, bedding gravel, manholes, roadworks,
curbs/sidewalks, frontage works, retaining walls, structural concrete, site concrete,
footings/foundations, bridges, municipal/utility infrastructure, and industrial site
preparation. TENDER_FINDER does NOT do vertical buildings or interior work.
Deprioritize: high-rise towers, interiors, building-only projects, small commercial
buildings, licensing-only files, telecom files, and GC-led vertical projects UNLESS
there is a clear, separable civil/site-servicing component.
```

**`{{SCORING}}`** (explicit weights — makes scores repeatable)
```
Score each lead 0–100:
  35%  likely civil scope (how much real earthwork/utilities/roadwork/concrete)
  25%  project-type fit (subdivision/townhouse/industrial site = high; tower/interior = low)
  20%  stage / readiness (closer to servicing tender = higher)
  10%  location fit (priority: Surrey > Township of Langley > City of Langley >
       Maple Ridge > Pitt Meadows > rest of Metro Van / Fraser Valley)
  10%  owner/developer/contact visibility (named owner+agent+civil consultant = higher)
Confidence = High / Medium / Low, based on how much was confirmed vs inferred.
```

**`{{RULES}}`** (the non-negotiables from the Surrey review)
```
- Do NOT invent facts. Any unknown field = "Not available". Never guess owners/dates.
- Separate CONFIRMED facts (project type, address, stage as stated in the record) from
  INFERRED civil scope (what earthwork/utilities the project type implies). Label which is which.
- Estimated tender window ONLY if the stage reasonably supports it; otherwise "Not available".
  A development application is a LEAD signal, never a confirmed bid date.
- Flag any data conflict, duplicate, or changed unit/area count explicitly.
- Geography in {{TENDER_FINDER_SCOPE}} is company context, NOT a search filter — score by the
  source's own records; do not pull in or invent records from other places.
```

---

## P1 — Universal scope-scoring prompt
**When:** after `tenderfinder_raw_sweep.py` produces `tenderfinder_raw_sweep.xlsx`, or on any batch of normalized records (RSS items, parsed emails). This is the prompt you run most.
**Input:** a batch of raw records (paste the rows, or attach the CSV/JSON).
**Output:** a scored, classified, deduped lead table + a 5-line summary.

```
You are a business-development analyst for Example Civil Contractor.

{{TENDER_FINDER_SCOPE}}

You are given a batch of RAW development-application / permit records collected from
public open-data sources. Each record has fields like address, application id,
type/stage, and a raw_json blob. Do not fetch anything new — work only from these records.

{{SCORING}}

{{RULES}}

For each record, output a row with:
  municipality | application id (native_id) | address | project type (confirmed) |
  current stage (confirmed) | likely civil scope (inferred) | confirmed-vs-inferred note |
  relevance score | confidence | estimated tender window or "Not available" |
  data-conflict flag | recommended next action

Then:
1. Rank all records by score, descending.
2. Split into three sections: Strong Fit (>=70), Watchlist (40–69), Exclude (<40).
3. Collapse duplicates: same project across multiple records = one row, keyed by
   address + application id. Note which source records were merged.
4. End with a 5-line summary: how many Strong Fit, the top 3 by score, and any record
   whose data looked conflicting or stale.

Output the table as CSV (so it can drop straight into the tracker).
```

---

## P2 — Active-tender parser
**When:** a tender email or notice hits the shared inbox (BC Bid, bids&tenders, CivicInfo, BidCentral, or a GC ITB from BuildingConnected/SmartBid/iSqFt).
**Input:** the raw email / notice text (forwarded message).
**Output:** one structured tracker row + a bid/no-bid signal.

```
You are screening an active tender / bid invitation for Example Civil Contractor.

{{TENDER_FINDER_SCOPE}}

{{RULES}}

From the notice below, extract ONE structured row:
  source (BC Bid / bids&tenders / CivicInfo / BidCentral / GC name) |
  tender title | owner/client | inviting GC (if a subcontractor invite) | municipality |
  solicitation type (ITT/RFP/RFQ/RFPQ/NOI/ITB/addendum) | scope summary (confirmed) |
  civil scope match (which TENDER_FINDER scopes apply) | closing date & time (verbatim) |
  site / pre-bid meeting date if any | documents location / link |
  fit score 0–100 using {{SCORING}} | confidence | bid / no-bid signal + one-line reason

Rules specific to active tenders:
- Closing date is critical. Quote it exactly; if absent, say "Not available — confirm on portal".
- If it is an addendum, link it to the base solicitation title and note what changed.
- If the scope is vertical-building-only with no separable civil package, mark no-bid and say why.

Tender notice:
{{PASTE_NOTICE}}
```

---

## P3 — Unstructured dev-application extractor
**When:** a source has no API — a PDF list or HTML table (Surrey in-process lists / planning reports, Richmond HTML, City of Langley monthly PDF, Pitt Meadows).
**Input:** the page/PDF content (or a URL the tool can read).
**Output:** the same normalized rows P1 expects, so the two feed one pipeline.

```
You are extracting development-application records for TENDER_FINDER from an unstructured
{{SOURCE_NAME}} document ({{SOURCE_URL}}).

{{TENDER_FINDER_SCOPE}}

{{RULES}}

Read the document and extract EVERY development application / permit / planning file as a row:
  municipality | application id / file no | address(es) | project type (confirmed) |
  current stage / status (confirmed) | unit count or floor area if stated |
  owner / applicant / agent / civil consultant if stated (else "Not available") |
  likely civil scope (inferred) | source link

Extraction discipline:
- One project may appear in several lists (rezoning, subdivision, DP, council). Note when
  the same address+file recurs so P5 can dedupe; do NOT silently merge differing details.
- If a unit count, area, or stage differs between places in the document, output BOTH and
  flag the conflict (this happens in Surrey records).
- Extract the whole list, not just the obvious TENDER_FINDER fits — scoring happens later in P1.
- Do not summarize or paraphrase the source narrative; pull structured fields only.

Then pass the rows to P1 for scoring, or output them as CSV directly.
```

---

## P4 — Council-agenda + capital-plan extractor
**When:** a council/committee agenda or a capital plan / financial plan PDF (Maple Ridge & municipal council agendas, Metro Vancouver / TransLink / MoTI / Infrastructure BC capital plans, municipal 5-year plans).
**Input:** the agenda or capital-plan document (or URL).
**Output:** pre-tender civil signals for the Horizon B watchlist.

```
You are scanning a {{SOURCE_NAME}} document ({{SOURCE_URL}}) for PRE-TENDER civil
signals relevant to Example Civil Contractor (6–18 months ahead).

{{TENDER_FINDER_SCOPE}}

{{RULES}}

Extract any item that signals a future civil/earthwork opportunity:
  item / project name | municipality or agency | what it is (confirmed) |
  signal type (subdivision approval / rezoning approval / servicing agreement /
  DCC project / roadworks approval / water-sewer-drainage capital program /
  contract-award recommendation / pre-tender approval / capital budget line) |
  stage or decision (e.g. Third Reading, awarded, budgeted year) |
  likely civil scope (inferred) | estimated horizon (near / mid / long) or "Not available" |
  dollar value if stated | source link

Rules specific to agendas/capital plans:
- Capture only items with a plausible civil/servicing/roadwork/utility/concrete component.
- Distinguish a budget LINE (money allocated, no tender yet) from an AWARD (already let).
- These are early signals to VERIFY, not confirmed tenders. Mark confidence accordingly.
- For capital plans, list the specific programs/projects, not the plan's prose summary.
```

---

## P5 — Weekly dedup + roll-up
**When:** end of each week, over everything P1–P4 produced.
**Input:** the week's scored rows from all sources.
**Output:** one deduped master list + a short digest for Example Reviewer.

```
You are compiling TENDER_FINDER's weekly tender-intelligence review.

{{TENDER_FINDER_SCOPE}}

You are given this week's scored leads from all sources (active tenders + future projects).

Do the following:
1. Normalize and DEDUPE by address + application id across ALL sources. Same project from
   Surrey list + council agenda + a GC email = one master row. Keep the highest-confidence
   values; list the source records merged; flag any field where sources disagreed.
2. Keep the two horizons separate:
   - Horizon A (active tenders, 0–3 months): sort by closing date, soonest first.
   - Horizon B (future projects, 6–18 months): sort by score, highest first.
3. Produce a short management digest for Example Reviewer:
   - New Strong-Fit active tenders this week (with closing dates).
   - Top 5 new future-project leads (with the single best next action each).
   - Anything time-sensitive (closings within 10 days, addenda, gated items).
   - Any source that produced only noise this week, and any source that produced the
     best lead — this drives the "automate only what earns it" decision.
4. Output two CSV tables (Horizon A, Horizon B) plus the digest as plain text.

{{RULES}}
```

---

### How these connect to the connector pack
P1 runs directly on `tenderfinder_raw_sweep.xlsx`. P3/P4 generate the same row shape for the
non-API sources so everything lands in one pile. P5 is the weekly merge. Start by running
P1 on the first real sweep output and check the Strong-Fit list against Example Coordinator's tracker —
that comparison is the validation gate before any source gets automated.
