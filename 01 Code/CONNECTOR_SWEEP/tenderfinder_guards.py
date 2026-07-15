#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tenderfinder_guards.py — TENDER_FINDER sweep safety + classification core
========================================================
Shared logic that decides whether a fetched layer/record is a
real development-application lead or something that must be quarantined.

This module is the single source of truth for:
  * the ArcGIS LAYER DENYLIST (reject layers by name before loading)
  * POSITIVE layer-name scoring (prefer development-application layers)
  * ATTRIBUTE-RICHNESS sampling (reject geometry/OID-only "schema_too_thin" layers)
  * RECORD CLASSIFICATION into the controlled status vocabulary
  * the OUTPUT ROUTER (classification -> destination workbook tab)
  * NORMALISATION helpers used by the multi-key dedup in tenderfinder_master_io.py

Design rule (from the project handoff): denylist + richness gate are applied
*before* anything is loaded into Future_Projects, never after pollution lands.

Safe to import from the sweep, the registry bridge, and the master writer.
"""

import re

from tenderfinder_keywords_config import load_keywords_config

# ---------------------------------------------------------------------------
# 1. LAYER DENYLIST  (reject by name during discovery/ranking, before loading)
#    Ported from tenderfinder_agent2.py _LAYER_DENYLIST and extended per the handoff.
#    Hits here = the layer is NOT a development-application / tender signal.
# ---------------------------------------------------------------------------
LAYER_DENYLIST = [
    "hazard", "dpa", "development permit area", "permit area",
    "marker", "subdivision marker", "survey monument", "monument",
    "watering", "lawn",
    "alr", "agricultural land reserve", "reserve",
    "neighbourhood plan", "neighborhood plan", "np_",
    "asset", "facility", "watercourse", "flood", "slope",
    "creek", "wildfire", "streamside", "riparian",
    "zoning",                      # zoning *base* layer (not "rezoning application")
    "contour", "parcel fabric", "address point", "road centreline",
    "road centerline", "boundary", "garbage", "recycling", "park amenity",
]

# A few denylist tokens must NOT trip on legitimate application layers.
# e.g. "zoning" is denied, but "rezoning application" is wanted. Guard against that.
_DENYLIST_FALSE_FRIENDS = [
    ("zoning", ("rezoning", "rezone")),
    ("reserve", ("reserved",)),            # avoid nuking nothing important, kept narrow
]


def layer_is_denylisted(name):
    """True if a layer NAME indicates it is not a useful dev-app / tender layer."""
    n = (name or "").lower()
    if not n:
        return False
    for bad in LAYER_DENYLIST:
        if bad in n:
            # suppress false friends (e.g. 'zoning' inside 'rezoning application')
            suppress = False
            for token, friends in _DENYLIST_FALSE_FRIENDS:
                if token == bad and any(fr in n for fr in friends):
                    suppress = True
                    break
            if not suppress:
                return True
    return False


# ---------------------------------------------------------------------------
# 2. POSITIVE LAYER-NAME SCORING  (prefer real development-application layers)
#    Positive name match is necessary but NOT sufficient — must still pass the
#    richness gate on sampled records (handoff 7.4).
# ---------------------------------------------------------------------------
POSITIVE_LAYER_TERMS = [
    "active development applications", "development applications",
    "development application", "current applications", "current development",
    "development activity", "planning application", "permit application",
    "rezoning", "subdivision", "development permit", "land development",
    "capital project", "capital projects", "city projects", "project",
]


def score_layer_name(name):
    """Heuristic positive score for a candidate layer name. Higher = better.
    Returns 0 if denylisted (caller should reject regardless)."""
    n = (name or "").lower()
    if not n or layer_is_denylisted(n):
        return 0
    score = 0
    for term in POSITIVE_LAYER_TERMS:
        if term in n:
            # longer, more specific phrases score higher
            score += 2 + len(term.split())
    # strong bonus if the name literally says "application(s)"
    if "application" in n:
        score += 4
    return score


def rank_candidate_layers(candidates):
    """candidates: list of (name, url). Returns them sorted best-first,
    with denylisted layers dropped. Stable for equal scores."""
    scored = []
    for i, (name, url) in enumerate(candidates):
        if layer_is_denylisted(name):
            continue
        scored.append((score_layer_name(name), -i, name, url))
    scored.sort(reverse=True)
    return [(name, url) for _, _, name, url in scored]


# ---------------------------------------------------------------------------
# 3. ATTRIBUTE-RICHNESS SAMPLING  (geometry/OID-only -> schema_too_thin)
#    Ported + strengthened from tenderfinder_agent2._attrs_are_rich_enough.
#    Rule (handoff 7.5): sample first 10-20 records; pass only if records carry
#    >= MIN_USEFUL_FIELDS non-geometry fields AND >=1 key application indicator.
# ---------------------------------------------------------------------------
MIN_USEFUL_FIELDS = 3

GEOM_OID_FIELDS = {
    "objectid", "fid", "globalid", "global_id", "shape", "shape_area",
    "shape_length", "shape__area", "shape__length", "shape.starea()",
    "shape.stlength()", "se_anno_cad_data", "geom", "geometry",
    "geo_point_2d", "geo_shape", "x", "y", "longitude", "latitude",
    "lng", "lat", "esri_oid",
}

# Field-name aliases that indicate a real application/project record.
# A KEY indicator = an application/file/folder/project NUMBER, which is the
# single strongest "this is an application" signal.
KEY_APP_INDICATOR_ALIASES = [
    "applicationno", "appno", "application", "applicationnumber",
    "file", "fileno", "filenumber", "folder", "folderno", "foldernumber",
    "projectno", "projectnumber", "project_id", "projectid", "devappno",
    "casenumber", "referencefile", "devfile", "permitnumber", "permit_number",
]

# Broader set of useful (non-geometry) fields. Presence of >=3 of these
# (by alias-substring match) is required to pass richness.
USEFUL_FIELD_ALIASES = KEY_APP_INDICATOR_ALIASES + [
    "applicationtype", "apptype", "type", "subtype", "category",
    "status", "stage", "applicationstatus", "currentstatus", "milestone",
    "address", "civicaddress", "fulladdress", "location", "siteaddress",
    "propertyaddress", "streetaddress", "street",
    "applicant", "applicantname", "owner", "ownername", "developer",
    "agent", "proponent", "company",
    "description", "projectdescription", "proposal", "purpose", "workproposed",
    "projectname", "name", "details", "summary",
    "date", "dateapplied", "submitted", "received", "decisiondate",
    "url", "link", "ourcity", "moreinfo", "weblink",
]


def _norm_key(k):
    return str(k).lower().replace("_", "").replace(" ", "").replace("-", "")


def _field_matches(field_key, alias_list):
    fk = _norm_key(field_key)
    return any(alias in fk for alias in alias_list)


def record_useful_field_count(attrs):
    """Count non-empty, non-geometry/OID fields in one record."""
    n = 0
    for k, v in attrs.items():
        if _norm_key(k) in {_norm_key(g) for g in GEOM_OID_FIELDS}:
            continue
        if v in (None, ""):
            continue
        n += 1
    return n


def record_has_key_indicator(attrs):
    """True if the record carries at least one application/file/project number
    (non-empty), or an OBJECTID-only fallback is explicitly NOT counted."""
    for k, v in attrs.items():
        if v in (None, ""):
            continue
        if _norm_key(k) in {"objectid", "fid", "globalid"}:
            continue  # OID is not an application number
        if _field_matches(k, KEY_APP_INDICATOR_ALIASES):
            return True
    return False


def sample_richness(records, sample=20):
    """Inspect up to `sample` records. Returns dict:
        passed (bool), reason (str), avg_useful_fields (float),
        records_with_key (int), sampled (int).
    Pass criteria (handoff 7.5):
        * sampled records average >= MIN_USEFUL_FIELDS useful non-geom fields
        * AND at least one sampled record carries a key application indicator
    """
    if not records:
        return {"passed": False, "reason": "no_records", "avg_useful_fields": 0.0,
                "records_with_key": 0, "sampled": 0}
    sub = records[:sample]
    counts = [record_useful_field_count(r) for r in sub]
    with_key = sum(1 for r in sub if record_has_key_indicator(r))
    avg = sum(counts) / len(counts) if counts else 0.0
    passed = (avg >= MIN_USEFUL_FIELDS) and (with_key >= 1)
    if passed:
        reason = "ok"
    elif avg < MIN_USEFUL_FIELDS and with_key == 0:
        reason = "geometry_or_oid_only"
    elif avg < MIN_USEFUL_FIELDS:
        reason = "too_few_useful_fields"
    else:
        reason = "no_application_indicator"
    return {"passed": passed, "reason": reason,
            "avg_useful_fields": round(avg, 2),
            "records_with_key": with_key, "sampled": len(sub)}


# ---------------------------------------------------------------------------
# 4. RECORD / SOURCE CLASSIFICATION  (controlled vocabulary, handoff 7.6 / 11)
# ---------------------------------------------------------------------------
# Trailing / non-future-development signals detected by layer or field names.
TRAILING_NAME_TOKENS = [
    "building permit", "issued building permit", "plumbing permit",
    "building and plumbing", "buildings and plumbing", "business licence",
    "business license", "issued permit", "watering permit", "lawn watering",
    "trade permit", "electrical permit",
]
CAPITAL_NAME_TOKENS = [
    "capital project", "capital projects", "city projects", "city-projects",
    "capital program", "capital plan", "infrastructure project",
]

# Classification labels (records / source returns)
CLASS_DEV_LEAD = "dev_application_lead"
CLASS_CAPITAL = "capital_project"
CLASS_ACTIVE = "active_tender"
CLASS_TRAILING = "building_permit_trailing"
CLASS_WRONG = "wrong_layer"
CLASS_THIN = "schema_too_thin"
CLASS_CONTEXT = "context_only"
CLASS_P3 = "p3_extract_required"
CLASS_MANUAL = "manual_review_needed"

# Output destinations (workbook tabs / queues)
ROUTE = {
    CLASS_DEV_LEAD: "Future_Projects",
    CLASS_CAPITAL:  "Future_Projects",     # no Capital_Context tab in v6/v7 -> FP, flagged
    CLASS_ACTIVE:   "Active_Tenders",
    CLASS_TRAILING: "Rejected_Archive",    # kept as context, marked trailing
    CLASS_WRONG:    "Rejected_Archive",
    CLASS_THIN:     "Rejected_Archive",
    CLASS_CONTEXT:  "Rejected_Archive",
    CLASS_P3:       "Run_Queue",           # P3 manual extract queue
    CLASS_MANUAL:   "Run_Queue",
}


def route_for(classification):
    return ROUTE.get(classification, "Rejected_Archive")


def classify_layer_return(layer_name, richness, denylisted=None):
    """Classify a *layer-level* return after a fetch attempt.
    layer_name : resolved layer/dataset name
    richness   : dict from sample_richness()
    denylisted : optional override; if None it is computed from layer_name.
    Returns one of the CLASS_* labels.
    """
    name = (layer_name or "").lower()
    if denylisted is None:
        denylisted = layer_is_denylisted(name)

    if denylisted:
        return CLASS_WRONG
    if any(tok in name for tok in TRAILING_NAME_TOKENS):
        return CLASS_TRAILING
    if any(tok in name for tok in CAPITAL_NAME_TOKENS):
        # capital context still needs *some* useful fields, else it's thin
        return CLASS_CAPITAL if richness.get("passed") else CLASS_CONTEXT
    if not richness.get("passed"):
        # thin schema with no application indicator -> wrong/thin
        return CLASS_THIN
    # passed richness and looks like an application layer
    return CLASS_DEV_LEAD


# ---------------------------------------------------------------------------
# 5. NORMALISATION HELPERS for multi-key dedup (handoff 13)
# ---------------------------------------------------------------------------
_ADDR_ABBREV = {
    r"\bstreet\b": "st", r"\bavenue\b": "ave", r"\bave\b": "ave",
    r"\bboulevard\b": "blvd", r"\bdrive\b": "dr", r"\broad\b": "rd",
    r"\bcrescent\b": "cres", r"\bplace\b": "pl", r"\bcourt\b": "crt",
    r"\bhighway\b": "hwy", r"\bnorth\b": "n", r"\bsouth\b": "s",
    r"\beast\b": "e", r"\bwest\b": "w", r"\bunit\b": "", r"\bsuite\b": "",
}
_MUNI_ALIASES = {
    "township of langley": "twp-langley", "twp of langley": "twp-langley",
    "tol": "twp-langley", "langley township": "twp-langley",
    "city of langley": "city-langley", "langley city": "city-langley",
    "city of surrey": "surrey", "maple ridge": "maple-ridge",
    "city of maple ridge": "maple-ridge", "pitt meadows": "pitt-meadows",
    "new westminster": "new-west", "city of new westminster": "new-west",
    "port coquitlam": "port-coquitlam", "city of coquitlam": "coquitlam",
    "district of north vancouver": "dnv", "city of north vancouver": "cnv",
    "city of vancouver": "vancouver",
}


def norm_text(s):
    s = str(s or "").strip().lower()
    s = re.sub(r"[^\w\s]", " ", s)       # drop punctuation
    s = re.sub(r"\s+", " ", s).strip()
    return s


def norm_municipality(s):
    n = norm_text(s)
    return _MUNI_ALIASES.get(n, n.replace(" ", "-"))


def norm_appno(s):
    """Normalise an application/file number: strip spaces/punct, upper-case."""
    s = str(s or "").upper()
    s = re.sub(r"[\s\-_/]+", "", s)
    return s


def norm_address(s):
    a = norm_text(s)
    for pat, repl in _ADDR_ABBREV.items():
        a = re.sub(pat, repl, a)
    a = re.sub(r"\s+", " ", a).strip()
    return a


def title_similarity(a, b):
    """Cheap token Jaccard similarity in [0,1] for project-title comparison."""
    ta, tb = set(norm_text(a).split()), set(norm_text(b).split())
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0



def _is_generic_feed_url(source_url):
    """Return True for portal/service endpoints that should not be used as unique project keys."""
    u = str(source_url or "").strip().lower()
    if not u:
        return True
    generic_bits = [
        "/featureserver", "/mapserver", "/arcgis/rest/",
        "/query", "opendata", "catalog/datasets", "portal",
        "rezoninginprocess-result.pdf", "dp-in-process.pdf",
    ]
    return any(bit in u for bit in generic_bits)

def dedup_keys(municipality, app_no="", address="", source_url="",
               owner="", title=""):
    """Build the set of normalised match keys used by the master writer's
    multi-key dedup (handoff 13). Any non-empty key collision = same project."""
    m = norm_municipality(municipality)
    keys = set()
    if app_no:
        keys.add(("muni_appno", m, norm_appno(app_no)))
    if address:
        keys.add(("muni_addr", m, norm_address(address)))
    if source_url and not _is_generic_feed_url(source_url):
        keys.add(("url", norm_text(source_url)))
    if owner and address:
        keys.add(("owner_addr", norm_text(owner), norm_address(address)))
    return keys


# ---------------------------------------------------------------------------
# 6. STRUCTURED FIELD ALIASES + PICKER (ported from tenderfinder_agent2._DEVAPP_FIELD_ALIASES)
#    Used to normalise a raw ArcGIS/ODS attribute dict into FP-lead fields.
# ---------------------------------------------------------------------------
DEVAPP_FIELD_ALIASES = {
    "app_no":    ["applicationno", "appno", "fileno", "filenumber", "file",
                  "applicationnumber", "application", "folderno", "foldernumber",
                  "folder", "permitnumber", "devappno", "projectno", "casenumber",
                  "projectnumber", "referencefile", "devfile"],
    "app_type":  ["applicationtype", "apptype", "applicationtypedesc",
                  "category", "subtype", "projecttype", "permittype", "type"],
    "status":    ["applicationstatus", "currentstatus", "processstage",
                  "statusdesc", "milestone", "folderstatus", "statusdescription",
                  "taskstatus", "amandastatus", "status", "stage", "state"],
    "address":   ["civicaddress", "fulladdress", "siteaddress", "propertyaddress",
                  "streetaddress", "address", "location", "addr", "street", "house"],
    "applicant": ["applicantname", "ownername", "developer", "proponent",
                  "applicant", "owner", "agent", "company"],
    "desc":      ["projectdescription", "workproposed", "description", "details",
                  "purpose", "proposal", "summary", "projectname", "comments",
                  "subtype", "tasktype", "name"],
    "url":       ["ourcityurl", "weblink", "moreinfo", "url", "link", "ourcity"],
}


def pick_field(attrs, which):
    """Return the first non-empty value among the aliases for `which`."""
    al = {_norm_key(k): v for k, v in attrs.items()}
    for alias in DEVAPP_FIELD_ALIASES[which]:
        if alias in al and al[alias] not in (None, ""):
            return al[alias]
    # loose contains-match
    for k, v in al.items():
        if v in (None, ""):
            continue
        if any(alias in k for alias in DEVAPP_FIELD_ALIASES[which]):
            return v
    return ""


# Offline civil-fit heuristic (transparent, rule-based — NOT AI scoring).
# The richer AI pass is PROMPT_DEV_APP_SCORING; this gives loaded rows a usable
# Fit Score so they sort, while staying Verification = "Needs Review".
def _scoring_rule_matches(rule, text, match_fields=None):
    """Match exact rules against preserved fields and other rules against text."""
    if rule.match_type == "exact" and match_fields is not None:
        return any(rule.matches(value) for value in match_fields)
    return rule.matches(text)


def score_civil_fit_breakdown(text_blob, municipality="", match_fields=None):
    """Return the current score plus the rule attribution used to calculate it."""
    config = load_keywords_config()
    text = text_blob or ""
    fields = tuple(value for value in (match_fields or ()) if value not in (None, ""))
    score = 35
    positive_matches = tuple(
        rule for rule in config.rules_for("positive")
        if _scoring_rule_matches(rule, text, fields if match_fields is not None else None)
    )
    negative_matches = tuple(
        rule for rule in config.rules_for("negative")
        if _scoring_rule_matches(rule, text, fields if match_fields is not None else None)
    )
    for rule in positive_matches:
        score += rule.weight
    for rule in negative_matches:
        score += rule.weight
    geography_matches = tuple(
        rule
        for rule in config.rules_for("geography")
        if rule.matches(municipality)
        or _scoring_rule_matches(rule, text, fields if match_fields is not None else None)
    )
    geography_weight = max((rule.weight for rule in geography_matches), default=0)
    if geography_matches:
        score += geography_weight
    client_matches = tuple(
        rule for rule in config.rules_for("client")
        if _scoring_rule_matches(rule, text, fields if match_fields is not None else None)
    )
    client_weight = max((rule.weight for rule in client_matches), default=0)
    if client_matches:
        score += client_weight
    return {
        "fit_score": max(0, min(100, score)),
        "raw_score": score,
        "positive_matches": positive_matches,
        "negative_matches": negative_matches,
        "geography_matches": geography_matches,
        "geography_weight": geography_weight,
        "client_matches": client_matches,
        "client_weight": client_weight,
    }


def score_civil_fit(text_blob, municipality="", match_fields=None):
    """Return a 0-100 offline Fit Score controlled by ``keywords.xlsx``."""
    return score_civil_fit_breakdown(text_blob, municipality, match_fields)["fit_score"]


if __name__ == "__main__":
    # Tiny self-check so `python tenderfinder_guards.py` proves the gates fire.
    assert layer_is_denylisted("Subdivision Markers")
    assert layer_is_denylisted("DPA Hazard - Creek/Slope")
    assert layer_is_denylisted("ALR Polygons")
    assert layer_is_denylisted("Neighbourhood Plan NP_Burke")
    assert not layer_is_denylisted("Active Development Applications")
    assert not layer_is_denylisted("Rezoning Applications")     # false-friend ok
    assert score_layer_name("Active Development Applications") > \
           score_layer_name("Parks")
    thin = sample_richness([{"OBJECTID": 1, "Shape__Area": 2.0}] * 5)
    rich = sample_richness([{"FOLDER_NUMBER": "RZ100710", "STATUS": "1st Reading",
                             "ADDRESS": "123 Main", "TYPE": "Rezoning"}] * 5)
    assert thin["passed"] is False and thin["reason"] == "geometry_or_oid_only"
    assert rich["passed"] is True
    assert route_for(CLASS_DEV_LEAD) == "Future_Projects"
    assert route_for(CLASS_WRONG) == "Rejected_Archive"
    assert pick_field({"FOLDER_NUMBER": "RZ100710"}, "app_no") == "RZ100710"
    assert pick_field({"WorkProposed": "site servicing"}, "desc") == "site servicing"
    s_civil = score_civil_fit("subdivision servicing water main storm sanitary", "Surrey")
    s_vert = score_civil_fit("interior tenant improvement kitchen renovation", "Burnaby")
    assert s_civil > s_vert
    assert classify_layer_return("Subdivision Markers", rich) == CLASS_WRONG
    assert classify_layer_return("Issued Building Permits",
                                 sample_richness([{"PermitNumber": "B1", "Address": "1 A St",
                                                   "TypeOfWork": "x", "Status": "Issued"}]*3)) == CLASS_TRAILING
    print("tenderfinder_guards self-check: OK")
