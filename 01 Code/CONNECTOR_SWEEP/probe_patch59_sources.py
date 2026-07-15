from __future__ import annotations

import json
import re
import ssl
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from tenderfinder_url_safety import safe_urllib_fetch


REST_RE = re.compile(r"https?://[^\s\"'<>]+?/(?:FeatureServer|MapServer)(?:/\d+)?", re.I)
HEADERS = {"User-Agent": "TENDER_FINDER-Patch59-Probe/1.0"}


def fetch(url: str, timeout: int = 12, verify: bool = True) -> str:
    if not verify:
        raise RuntimeError("TLS certificate verification cannot be disabled")
    return safe_urllib_fetch(
        url,
        headers=HEADERS,
        timeout=timeout,
        max_bytes=10_000_000,
    ).body.decode("utf-8", "replace")


def safe_fetch(url: str) -> tuple[str, str]:
    try:
        return fetch(url), ""
    except Exception as exc:
        return "", f"{type(exc).__name__}: {exc}"


def json_fetch(url: str) -> tuple[dict, str]:
    text, err = safe_fetch(url)
    if err:
        return {}, err
    try:
        return json.loads(text), ""
    except Exception as exc:
        return {}, f"json_error: {exc}"


def layer_meta(layer_url: str) -> dict:
    meta, err = json_fetch(layer_url.rstrip("/") + "?f=json")
    if err:
        return {"url": layer_url, "error": err}
    fields = [f.get("name") for f in (meta.get("fields") or []) if isinstance(f, dict)]
    count_url = layer_url.rstrip("/") + "/query?" + urllib.parse.urlencode({
        "where": "1=1",
        "returnCountOnly": "true",
        "f": "json",
    })
    count_payload, count_err = json_fetch(count_url)
    return {
        "url": layer_url,
        "name": meta.get("name"),
        "type": meta.get("type"),
        "geometryType": meta.get("geometryType"),
        "count": count_payload.get("count"),
        "count_error": count_err,
        "fields": fields[:40],
    }


def service_layers(service_url: str) -> list[str]:
    meta, err = json_fetch(service_url.rstrip("/") + "?f=json")
    if err:
        return []
    return [
        service_url.rstrip("/") + "/" + str(layer["id"])
        for layer in (meta.get("layers") or [])
        if "id" in layer
    ]


def hub_probe(label: str, hub: str, terms: list[str]) -> dict:
    urls: list[str] = []
    notes: list[str] = []
    paths = [
        "/api/feed/dcat-us/1.1.json",
        "/api/search?" + urllib.parse.urlencode({"q": " ".join(terms)}),
    ]
    for path in paths:
        text, err = safe_fetch(hub.rstrip("/") + path)
        if err:
            notes.append(f"{path}: {err}")
        urls.extend(REST_RE.findall(text))

    expanded: list[str] = []
    for url in dict.fromkeys(urls):
        if re.search(r"/(?:FeatureServer|MapServer)/\d+$", url, re.I):
            expanded.append(url)
        else:
            expanded.extend(service_layers(url))

    candidates: list[dict] = []
    for url in dict.fromkeys(expanded):
        meta = layer_meta(url)
        blob = " ".join([
            str(meta.get("name") or ""),
            " ".join(meta.get("fields") or []),
            meta.get("url", ""),
        ]).lower()
        if any(term in blob for term in terms):
            candidates.append(meta)
    return {"label": label, "source": hub, "notes": notes, "candidates": candidates[:20]}


def map_probe(label: str, service: str, terms: list[str]) -> dict:
    candidates: list[dict] = []
    for url in service_layers(service):
        meta = layer_meta(url)
        blob = " ".join([
            str(meta.get("name") or ""),
            " ".join(meta.get("fields") or []),
        ]).lower()
        if any(term in blob for term in terms) or any(token in blob for token in ["application", "permit", "file", "status", "address"]):
            candidates.append(meta)
    return {"label": label, "source": service, "notes": [], "candidates": candidates[:30]}


def ods_probe(label: str, base: str, slugs: list[str]) -> dict:
    candidates: list[dict] = []
    for slug in slugs:
        url = f"{base}/api/explore/v2.1/catalog/datasets/{slug}/records?limit=1"
        payload, err = json_fetch(url)
        fields: list[str] = []
        results = payload.get("results") or []
        if results:
            fields = list(results[0].keys())
        candidates.append({
            "url": url,
            "name": slug,
            "count": payload.get("total_count") or payload.get("nhits"),
            "error": err,
            "fields": fields[:40],
        })
    return {"label": label, "source": base, "notes": [], "candidates": candidates}


TASKS = [
    ("hub", "new_west_currentdev", "https://opendata.newwestcity.ca", ["current", "development", "permit", "application"]),
    ("hub", "burnaby_devapps", "https://opendata-burnaby.hub.arcgis.com", ["development", "rezoning", "permit", "application"]),
    ("hub", "delta_devapps", "https://opendata-deltabc.hub.arcgis.com", ["development", "rezoning", "permit", "application"]),
    ("hub", "city_langley_devapps", "https://data-langleycity.opendata.arcgis.com", ["development", "rezoning", "permit", "application"]),
    ("hub", "abbotsford_devapps", "https://opendata-abbotsford.hub.arcgis.com", ["development", "rezoning", "permit", "application"]),
    ("hub", "port_moody_discovery", "https://opendata-portmoody.hub.arcgis.com", ["development", "rezoning", "permit", "application"]),
    ("hub", "mission_discovery", "https://opendata-districtofmission.hub.arcgis.com", ["development", "rezoning", "permit", "application"]),
    ("hub", "chilliwack_discovery", "https://opendata-chilliwack.hub.arcgis.com", ["development", "rezoning", "permit", "application"]),
    ("hub", "white_rock_discovery", "https://opendata-whiterock.hub.arcgis.com", ["development", "rezoning", "permit", "application"]),
    ("map", "dnv_devapps", "https://www.geoweb.dnv.org/arcgis/rest/services/Data_DynamicLayers/MapServer", ["development", "application", "permit", "rezoning", "planning", "land"]),
    ("map", "port_coquitlam_landdev", "https://maps.portcoquitlam.ca/server/rest/services/DynamicData_LandsAndDevelopment/MapServer", ["development", "application", "permit", "rezoning", "planning", "land"]),
    ("ods", "van_ods", "https://opendata.vancouver.ca", ["rezoning-applications", "development-permit-applications"]),
]


def run_task(task: tuple[str, str, str, list[str]]) -> dict:
    kind, label, source, terms = task
    if kind == "hub":
        return hub_probe(label, source, terms)
    if kind == "map":
        return map_probe(label, source, terms)
    return ods_probe(label, source, terms)


def main() -> int:
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        future_map = {pool.submit(run_task, task): task[1] for task in TASKS}
        for future in as_completed(future_map):
            label = future_map[future]
            try:
                results.append(future.result(timeout=20))
            except Exception as exc:
                results.append({"label": label, "error": f"{type(exc).__name__}: {exc}"})
    print(json.dumps(sorted(results, key=lambda item: item.get("label", "")), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
