#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 5.3 P0.2 / P0.4 regression: Vancouver permit routing + write gates.

The live run pulled 20,000 Vancouver permits (strong=3144, watchlist=1261,
bulk=5870, noisy=9725) but the summary reported 17,906 Future_Projects
"eligible leads" -- because _apply_write_gates unconditionally re-routed every
lead to Future_Projects and flipped write_eligible back to True.

These tests assert that:
  * only STRONG Vancouver permits are write-eligible / Future_Projects,
  * watchlist/bulk/noisy are held and keep their routes after write gates,
  * the global eligible count is NOT inflated,
  * _categorize_result reports honest separated counts (P0.4),
  * a genuinely clean connector lead still passes the gate,
  * an explicit min_fit_score can still tighten (but never loosen).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONNECTOR_DIR = os.path.dirname(HERE)
sys.path.insert(0, CONNECTOR_DIR)

import tenderfinder_raw_sweep as RS  # noqa: E402


class T:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def check(self, name, cond, detail=""):
        ok = bool(cond)
        self.passed += ok
        self.failed += (not ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" :: {detail}" if detail else ""))
        return ok


def _van_lead(tier_signal):
    """Make a fake van permit lead whose _raw blob lands in a known tier."""
    raw = {
        "strong":    {"description": "site servicing and subdivision road works civil"},
        "watchlist": {"description": "rezoning application with interior tenant improvement"},
        "bulk":      {"description": "permit issued for accessory structure"},
        "noisy":     {"description": "interior tenant improvement bathroom renovation"},
    }[tier_signal]
    return {"project_id": f"VAN-{tier_signal}", "_raw": raw,
            "fit_score": 50, "proposed_route": "Future_Projects", "write_eligible": True}


def make_van_result():
    leads = ([_van_lead("strong")] * 3 + [_van_lead("watchlist")] * 2 +
             [_van_lead("bulk")] * 4 + [_van_lead("noisy")] * 5)
    # give each lead a unique project_id so dedupe-by-id elsewhere is irrelevant
    for i, l in enumerate(leads):
        l["project_id"] = f"{l['project_id']}-{i}"
    return {"source_id": "van_building_permits",
            "source_name": "Vancouver - Issued Building Permits",
            "leads": leads, "rejected": [], "records_pulled": len(leads),
            "status": "loaded", "output_route": "Future_Projects"}


def make_clean_result():
    leads = [{"project_id": f"MR-{i}", "_raw": {}, "fit_score": 70,
              "proposed_route": "Future_Projects", "write_eligible": True}
             for i in range(3)]
    return {"source_id": "maple_ridge_devapps", "source_name": "Maple Ridge",
            "leads": leads, "rejected": [], "records_pulled": 3,
            "status": "loaded", "output_route": "Future_Projects"}


def main():
    t = T()

    van = make_van_result()
    RS.apply_van_permit_filter(van)
    t.check("van tiers: strong=3", van.get("van_permit_strong") == 3, f"strong={van.get('van_permit_strong')}")
    t.check("van tiers: watchlist=2", van.get("van_permit_watchlist") == 2)
    t.check("van tiers: bulk=4", van.get("van_permit_bulk") == 4)
    t.check("van tiers: noisy=5", van.get("van_permit_noisy") == 5)

    clean = make_clean_result()
    results = [van, clean]

    # The dangerous step: write gates must RESPECT routing (P0.2).
    RS._apply_write_gates(results, min_fit_score=None, max_write_per_source=0)

    eligible = RS._eligible_leads(results)
    van_eligible = [l for l in eligible if l["project_id"].startswith("VAN-")]
    t.check("P0.2: only 3 strong van permits eligible", len(van_eligible) == 3,
            f"van_eligible={len(van_eligible)} (was 14 with the bug)")
    t.check("P0.2: clean connector leads still eligible", len(eligible) - len(van_eligible) == 3)

    # No watchlist/bulk/noisy leaked into Future_Projects.
    leaked = [l for l in eligible
              if l.get("routing_reason", "").startswith("van_permit_") and "strong" not in l.get("routing_reason", "")]
    t.check("P0.2: no watchlist/bulk/noisy leaked to eligible", len(leaked) == 0, f"leaked={len(leaked)}")

    # Routes preserved after gates.
    routes = {}
    for l in van["leads"]:
        routes.setdefault(l.get("proposed_route"), 0)
        routes[l["proposed_route"]] += 1
    t.check("P0.2: bulk routed to Bulk_Intake_Raw", routes.get("Bulk_Intake_Raw") == 4, str(routes))
    t.check("P0.2: noisy routed to Rejected_Archive", routes.get("Rejected_Archive") == 5, str(routes))
    t.check("P0.2: watchlist routed to Run_Queue", routes.get("Run_Queue") == 2, str(routes))
    t.check("P0.2: strong routed to Future_Projects", routes.get("Future_Projects") == 3, str(routes))

    # P0.4: honest categorization.
    cat = RS._categorize_result(van)
    t.check("P0.4: clean_future_projects=3", cat["records_clean_future_projects"] == 3, str(cat))
    t.check("P0.4: watchlist=2", cat["records_watchlist"] == 2, str(cat))
    t.check("P0.4: bulk_intake=4", cat["records_bulk_intake"] == 4, str(cat))
    t.check("P0.4: rejected=5", cat["records_rejected"] == 5, str(cat))

    # P0.4: a manual/no-url connector is reported as manual, not silent zero.
    manual = {"source_id": "coquitlam_devapps", "source_name": "Coquitlam",
              "leads": [], "rejected": [], "records_pulled": 0,
              "status": "needs_exact_url", "output_route": "Run_Queue"}
    mcat = RS._categorize_result(manual)
    t.check("P0.4: manual/p3 connector flagged", mcat["records_manual_or_p3"] == 1, str(mcat))

    # P0.4: a failed-extraction connector (Surrey live failure) is visible.
    failed = {"source_id": "surrey_planning_reports", "source_name": "Surrey",
              "leads": [], "rejected": [], "records_pulled": 0,
              "status": "no_records_extracted", "output_route": "Run_Queue"}
    fcat = RS._categorize_result(failed)
    t.check("P0.4: failed extraction flagged", fcat["records_failed_extraction"] == 1, str(fcat))

    # min_fit_score can still TIGHTEN clean leads (never loosen held ones).
    van2 = make_van_result(); RS.apply_van_permit_filter(van2)
    clean2 = make_clean_result()
    for l in clean2["leads"]:
        l["fit_score"] = 10  # below threshold
    RS._apply_write_gates([van2, clean2], min_fit_score=40, max_write_per_source=0)
    elig2 = RS._eligible_leads([van2, clean2])
    t.check("gate tighten: low-fit clean leads held", all(not l["write_eligible"] for l in clean2["leads"]))
    t.check("gate tighten: strong van still eligible (not loosened or over-tightened)",
            len([l for l in elig2 if l['project_id'].startswith('VAN-')]) == 3)

    # Source summary CSV separates the categories (P0.4).
    import tempfile, csv
    with tempfile.TemporaryDirectory() as d:
        path = RS.write_source_summary([van, clean, manual, failed], d, "RUN-TEST")
        with open(path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        cols = set(rows[0].keys())
        need = {"records_clean_future_projects", "records_watchlist", "records_bulk_intake",
                "records_manual_or_p3", "records_failed_extraction", "duplicates_skipped",
                "route", "status"}
        t.check("P0.4: summary has honest separated columns", need.issubset(cols),
                f"missing={need - cols}")
        vanrow = next(r for r in rows if r["source_id"] == "van_building_permits")
        t.check("P0.4: summary van eligible == 3 (not inflated)",
                vanrow["records_clean_future_projects"] == "3" and vanrow["records_eligible"] == "3",
                f"clean={vanrow['records_clean_future_projects']} eligible={vanrow['records_eligible']}")

    print(f"\nRouting/gate test: {t.passed} passed, {t.failed} failed")
    return 0 if t.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
