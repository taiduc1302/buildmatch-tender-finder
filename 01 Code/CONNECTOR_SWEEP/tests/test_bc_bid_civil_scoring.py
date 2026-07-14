from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tenderfinder_demo_three_buckets import civil_keyword_match  # noqa: E402

# Titles and commodity/snippet text verified by direct inspection of the
# Patch 5.13 BID_NOW_Active_Tenders sheet.
FALSE_POSITIVES = [
    (
        "Doc5757626103_RFP_ SeaBus Bearings and Pedestals Repair",
        "231471. Bridge construction and repair service Concrete installation and repair services "
        "Concrete patio construction service. Request for Proposal (BPS). issuer: TransLink"
        "(South Coast British Columbia Transportation Authority). posted 2026-06-30 11:38:12 AM. "
        "closes 2026-07-15 2:00:00 PM.",
    ),
    (
        "RFQ #26-61-REC Arenas Compressor Servicing",
        "26-61-REC. Building and Facility Construction and Maintenance Services. "
        "Request for Quotation (BPS). issuer: City of Vernon. posted 2026-06-30 1:29:25 PM. "
        "closes 2026-07-23 2:00:00 PM.",
    ),
]

# Confirmed by direct inspection of the Patch 5.14 workbook after
# pagination quadrupled the candidate pool (58 vs 15 in 5.13).
NEW_FALSE_POSITIVES_5_15 = [
    "RFQ 48-2026 Main Engines Seawater Cooling Piping Replacement Services",
    "Domestic Hot Water Tank and Boiler Replacement Design-Build",
    # Found during the Patch 5.15 full manual review pass, not named in
    # that patch's prompt but confirmed equipment/technology supply, not
    # civil construction.
    "Water Metering Technology",
    "Supply and Deliver of Custom Misting Station / Water Fountains",
]

# Confirmed by direct inspection after Patch 5.16 raised the BC Bid page
# cap from 5 to 15 (58 -> ~204 candidates). Two of these are systemic
# substring collisions ("road" inside "Broadcasting", "fill" inside
# "Landfill") that could recur on any future BC Bid title using those
# commodity categories, not just these specific titles.
NEW_FALSE_POSITIVES_5_16 = [
    (
        "MCBRIDE - Domestic Hot Water Storage Tank Replacement",
        "N662740005. Professional engineering services. Request for Proposal (BPS). "
        "issuer: Northern Health Authority. posted 2026-06-23 12:53:09 PM. closes 2026-07-21 2:00:00 PM.",
    ),
    (
        "RBCM ITQ - LEARNING #2 Smart Board with Stand",
        "230094. Information Technology Broadcasting and Telecommunications Office Equipment and "
        "Accessories and Supplies Printing and Photographic and Audio and Visual Equipment and Supplies. "
        "Invitation to Quote (BPS). issuer: Procurement Services Branch. posted 2026-06-26 3:56:15 PM. "
        "closes 2026-07-17 2:00:00 PM.",
    ),
    (
        "RBCM ITQ - LEARNING #1 Camera Set Up",
        "230093. Domestic Appliances and Supplies and Consumer Electronic Products Electrical Systems "
        "and Lighting and Components and Accessories and Supplies Electronic Components and Supplies "
        "Information Technology Broadcasting and Telecommunications. Invitation to Quote (BPS). "
        "issuer: Procurement Services Branch. posted 2026-06-26 3:55:00 PM. closes 2026-07-17 2:00:00 PM.",
    ),
    (
        "IT Service Management System Replacement",
        "231336. Information Technology Broadcasting and Telecommunications Software. "
        "Request for Proposal (BPS). issuer: City of North Vancouver. posted 2026-06-26 12:13:15 PM. "
        "closes 2026-08-14 4:00:00 PM.",
    ),
    (
        "RFI# 26-21 Municipal Solid Waste Hauling and Disposal Services",
        "231299. Landfill services Transport services. Request for Information (BPS). "
        "issuer: Cowichan Valley Regional District. posted 2026-06-25 4:26:54 PM. closes 2026-08-06 2:00:00 PM.",
    ),
    (
        "CON#468 ROLL-OFF BIN HAULING SERVICES KITIMAT LANDFILL",
        "231288. Refuse collection and disposal. Request for Proposal (BPS). issuer: District of Kitimat. "
        "posted 2026-06-25 4:05:03 PM. closes 2026-07-14 2:00:00 PM.",
    ),
    (
        "Air-to-Water Heat Pump Workforce Capacity Building",
        "231291. Business and corporate management consultation services. Notice of Intent (BPS). "
        "issuer: City of Vancouver. posted 2026-06-25 4:00:00 PM. closes 2026-07-09 3:00:00 PM.",
    ),
    (
        "Land Disposition for Mixed-Use Development - 3213 & 3217 Happy Valley Road, Langford, BC",
        "231283. Land and Buildings and Structures and Thoroughfares. Request for Proposal (BPS). "
        "issuer: City of Langford. posted 2026-06-25 2:54:23 PM. closes 2026-07-31 3:00:00 PM.",
    ),
    (
        "12987 Pressure Washing",
        "231181. Car wash/cleaning equipment Cleaning, sorting, and grading machine parts and accessories "
        "High pressure cleaning equipment Industrial Cleaning Services Washing machinery. "
        "Request for Proposal (BPS). issuer: City of Kelowna. posted 2026-06-24 10:15:38 AM. "
        "closes 2026-07-23 2:00:00 PM.",
    ),
    (
        "CON#473 KITIMAT SPRAY PARK & PLAYGROUND REVITALIZATION",
        "231346. Recreation and playground and swimming and spa equipment and supplies Water parks. "
        "Invitation to Tender (BPS). issuer: District of Kitimat. posted 2026-06-26 2:22:16 PM. "
        "closes 2026-07-24 2:30:00 PM.",
    ),
]

# Real BC Bid titles that legitimately match "road" or "fill" from genuine
# civil commodity text (not the Broadcasting/Landfill collisions above) -
# locks that the collision fix doesn't over-suppress real matches.
COLLISION_SAFE_TRUE_POSITIVES = [
    (
        "RFQ 2026-01 Landfill Closure Plan",
        "231222. Civil engineering. Request for Quotation (BPS). issuer: North Coast Regional District.",
    ),
    (
        "Req 68797 - 44 standard (knob) top precast concrete interlocking blocks",
        "5657381. Concrete blocks Roads and landscape. Invitation to Quote. issuer: Procurement Services Branch.",
    ),
]

TRUE_POSITIVES = [
    "EN27DCM003 - Wedeene Forest Service Road Grading",
    "Mission Hill Water Treatment Plant - Construction Management Process",
    "Victoria General Hospital Parking Lot Expansion - Paving Contractor",
    "Consulting Engineering Services for the Coquitlam Lake Supply Project (CLWSP) – Water Filtration Plant Design",
    "Powers Creek Water Treatment Plant Division Structure",
]


def main() -> int:
    for title, snippet in FALSE_POSITIVES:
        joined = f"{title} {snippet}"
        assert civil_keyword_match(joined, title) is False, title

    for title in NEW_FALSE_POSITIVES_5_15:
        assert civil_keyword_match(title, title) is False, title

    for title, snippet in NEW_FALSE_POSITIVES_5_16:
        joined = f"{title} {snippet}"
        assert civil_keyword_match(joined, title) is False, title

    for title, snippet in COLLISION_SAFE_TRUE_POSITIVES:
        joined = f"{title} {snippet}"
        assert civil_keyword_match(joined, title) is True, title

    for title in TRUE_POSITIVES:
        assert civil_keyword_match(title, title) is True, title

    print("BC Bid civil keyword scoring test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
