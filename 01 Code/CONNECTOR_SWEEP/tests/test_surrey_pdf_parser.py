#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch 5.3 P0.1 regression: Surrey in-process PDF parser.

The live run downloaded both Surrey PDFs successfully but extracted ZERO rows.
This test exercises the hardened multi-strategy parser against representative
synthetic PDFs (ruled-table layout AND flowing-text layout, the two layouts
that caused the live failure) and asserts:

  * recognizable application ids are extracted (25-0366, 26-0004,
    7926-0157-00, 7925-0256-00, ...),
  * extraction is never a silent zero when ids exist in the text,
  * the id-only salvage path works on a degenerate document,
  * a debug artifact is written when extraction is empty,
  * normalized leads carry source_url and a review route.

NOTE: these synthetic PDFs are representative, not byte-identical to Surrey's
live PDFs (which this sandbox cannot reach). Final confirmation must be a live
run on a networked Windows machine; if the live layout still defeats the
parser, the debug artifact this test verifies will capture the real layout.
"""
import io
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CONNECTOR_DIR = os.path.dirname(HERE)
sys.path.insert(0, CONNECTOR_DIR)

import tenderfinder_surrey_inprocess as S  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")
RULED = os.path.join(FIXTURES, "surrey_dp_inprocess_sample.pdf")
TEXTFLOW = os.path.join(FIXTURES, "surrey_rezoning_inprocess_sample.pdf")

REQUIRED_IDS_TEXTFLOW = {"25-0366", "25-0268", "26-0004", "7926-0157-00", "7925-0256-00"}
REQUIRED_IDS_RULED = {"24-0345", "25-0411", "7926-0312-00"}


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


def _appnos(rows):
    return {r.get("app_no") for r in rows if r.get("app_no")}


def main():
    t = T()

    if not (os.path.exists(RULED) and os.path.exists(TEXTFLOW)):
        print("Fixtures missing; run tests/make_surrey_fixtures.py first.")
        return 1

    # ---- ruled-table layout -------------------------------------------------
    rows, dbg = S._extract_pdf_rows(open(RULED, "rb").read(), "DPInProcess",
                                    "Development Permit", debug_dir=None)
    got = _appnos(rows)
    t.check("ruled: rows extracted (>0)", len(rows) > 0, f"rows={len(rows)} strat={dbg['strategy_used']}")
    t.check("ruled: all required ids found", REQUIRED_IDS_RULED.issubset(got),
            f"missing={REQUIRED_IDS_RULED - got}")
    t.check("ruled: not id-only salvage", not dbg["id_only_fallback"])
    t.check("ruled: at least one address parsed",
            any(r.get("address") for r in rows))

    # ---- flowing-text layout (the hard live case) ---------------------------
    rows2, dbg2 = S._extract_pdf_rows(open(TEXTFLOW, "rb").read(), "RezoningInProcess",
                                      "Rezoning", debug_dir=None)
    got2 = _appnos(rows2)
    t.check("textflow: rows extracted (>0)", len(rows2) > 0, f"rows={len(rows2)} strat={dbg2['strategy_used']}")
    t.check("textflow: all required ids found", REQUIRED_IDS_TEXTFLOW.issubset(got2),
            f"missing={REQUIRED_IDS_TEXTFLOW - got2}")
    t.check("textflow: long compound id 7926-0157-00 present", "7926-0157-00" in got2)

    # ---- normalization carries source_url + review route --------------------
    lead = S._normalize_surrey_lead(rows2[0],
                                    "https://www.surrey.ca/sites/default/files/media/documents/RezoningInProcess-Result.pdf",
                                    "RezoningInProcess", "Rezoning", "RUN-TEST")
    t.check("normalize: source_url present", str(lead.get("source_url", "")).startswith("http"))
    t.check("normalize: project_id present", bool(lead.get("project_id")))
    t.check("normalize: fit_score numeric", isinstance(lead.get("fit_score"), (int, float)))
    t.check("normalize: proposed_route set", bool(lead.get("proposed_route")))

    # ---- never-silent-zero salvage on a degenerate blob ---------------------
    salvage = S._emit_rows_from_ids(
        "garbled\x0c layout 25-0366 ... 7925-0256-00 with no parseable columns",
        "Rezoning", "RezoningInProcess")
    t.check("salvage: id-only rows emitted", len(salvage) >= 2,
            f"got {len(salvage)} salvage rows")
    t.check("salvage: ids captured", {r['app_no'] for r in salvage} >= {"25-0366", "7925-0256-00"})

    # ---- debug artifact written when extraction empty -----------------------
    # Build a 1-page PDF with NO recognizable ids so all strategies return [].
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, "This page intentionally contains no application identifiers.")
    c.showPage(); c.save()
    empty_pdf = buf.getvalue()
    with tempfile.TemporaryDirectory() as d:
        rows3, dbg3 = S._extract_pdf_rows(empty_pdf, "EmptyCase", "Rezoning", debug_dir=d)
        artifact = os.path.join(d, "TENDER_FINDER_Surrey_Parse_Debug_EmptyCase.txt")
        t.check("empty: zero rows", len(rows3) == 0, f"rows={len(rows3)}")
        t.check("empty: debug artifact written", os.path.exists(artifact),
                f"path={dbg3.get('debug_path')}")
        if os.path.exists(artifact):
            txt = open(artifact, encoding="utf-8").read()
            t.check("empty: debug artifact has reason + raw text", "reason:" in txt and "RAW TEXT" in txt)

    print(f"\nSurrey parser test: {t.passed} passed, {t.failed} failed")
    return 0 if t.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
