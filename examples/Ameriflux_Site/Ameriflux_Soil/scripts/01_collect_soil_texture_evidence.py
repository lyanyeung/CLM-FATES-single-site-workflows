#!/usr/bin/env python3
"""Stage01 (read-only for model inputs): soil texture evidence and CLM-FATES
PCT_SAND / PCT_CLAY recommendation for the 50 AmeriFlux sites.

For every site in Ameriflux_PFT/metadata/sites_50_manifest.csv this script
collects, with provenance:

  REESH      site-measured texture from the AmeriFlux ReESH (Regional Ecosystem
             Soil Hydraulics) project, Zenodo "ReESH_<SITE>" records,
             <SITE>_SoilCharacteristics.csv (MD5 verified on download)
  BADM       SOIL_TEX_* groups in the site's BIF: the FLUXNET-package BIF and,
             with --badm-dir, the full AmeriFlux BADM download
             AMF_<SITE>_BIF_<YYYYMMDD>.xlsx (the full file supersedes the subset).
             Depth from SOIL_TEX_PROFILE_MIN/MAX, else the same horizon in
             another soil group, else data/badm_manual_depth_assignments;
             a group without depth is reported but never used.
  LIT        tower-specific numeric literature values from
             data/literature_soil_evidence_20261026.csv (use_numeric=YES)
  SSURGO     USDA NRCS Soil Data Access, dominant component of the map unit at
             the tower point (US sites only)
  SOILGRIDS  ISRIC SoilGrids 2.0 250 m, six standard depths (all sites)
  SURFACE    the current CLM surface file(s) used by the site's cases
             (CaseDocs/lnd_in fsurdat) or found under the site folder

and maps each profile onto the 10 CLM surface-dataset soil layers (node depths
0.007 ... 2.86 m). The recommendation takes, layer by layer, the first source
in --priority that covers the node depth; below the deepest covered depth the
profile that supplied the layer above is extended (else SSURGO, SoilGrids, then
the deepest measured value). The current surface is used only when nothing else
exists. Organic matter density is reported as a candidate only.

Nothing in CLM/CTSM, cases, surfaces or forcing is modified.

Typical IRIDIS6 use (login node, internet needed for REESH/SSURGO/SoilGrids):
  python3 -B 01_collect_soil_texture_evidence.py --self-test
  python3 -B 01_collect_soil_texture_evidence.py \
      --output-root $HOME/CLM_FATES_SOIL/AmeriFlux50_20261026
  # subset / offline re-run from cache:
  python3 -B 01_... --sites US-Ha1 US-Me2 --output-root ... --no-network
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, re, statistics, sys, time
import urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOIL = HERE.parent
AMF = SOIL.parent
MANIFEST = AMF / "Ameriflux_PFT/metadata/sites_50_manifest.csv"
LIT_CSV = SOIL / "data/literature_soil_evidence_20261026.csv"
REESH_KNOWN = SOIL / "data/reesh_records_found_20261026.csv"
BADM_MANUAL = SOIL / "data/badm_manual_depth_assignments_20261026.csv"
NODES_M = [0.025 * (math.exp(0.5 * (j - 0.5)) - 1.0) for j in range(1, 11)]   # CLM nlevsoifl=10
NODES_CM = [100.0 * z for z in NODES_M]
DEFAULT_PRIORITY = ("REESH", "BADM", "LIT", "SSURGO", "SOILGRIDS")
DEEP_FILL = ("SSURGO", "SOILGRIDS", "REESH", "BADM", "LIT")
SOILGRIDS_DEPTHS = ("0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm")
UA = "CLM-FATES-single-site-workflows soil evidence (research; contact repo owner)"


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def num(x):
    try:
        v = float(str(x).strip())
        return v if math.isfinite(v) and v > -9990 else None
    except (TypeError, ValueError):
        return None


def usda_class(sand, clay):
    if sand is None or clay is None:
        return ""
    silt = 100.0 - sand - clay
    if silt + 1.5 * clay < 15: return "sand"
    if silt + 2 * clay < 30: return "loamy sand"
    if (7 <= clay < 20 and sand > 52) or (clay < 7 and silt < 50): return "sandy loam"
    if 7 <= clay < 27 and 28 <= silt < 50 and sand <= 52: return "loam"
    if silt >= 80 and clay < 12: return "silt"
    if silt >= 50 and clay < 27: return "silt loam"
    if 20 <= clay < 35 and silt < 28 and sand > 45: return "sandy clay loam"
    if 27 <= clay < 40 and 20 < sand <= 45: return "clay loam"
    if 27 <= clay < 40 and sand <= 20: return "silty clay loam"
    if clay >= 35 and sand > 45: return "sandy clay"
    if clay >= 40 and silt >= 40: return "silty clay"
    return "clay"


# ---------------------------------------------------------------- network
class Net:
    def __init__(self, enabled, cache):
        self.enabled, self.cache = enabled, cache
        self.last = {}

    def _wait(self, host, gap):
        dt = time.time() - self.last.get(host, 0)
        if dt < gap:
            time.sleep(gap - dt)
        self.last[host] = time.time()

    def get(self, url, gap=1.0, data=None, headers=None, tries=3):
        if not self.enabled:
            raise RuntimeError("network disabled (--no-network)")
        host = urllib.parse.urlparse(url).netloc
        err = None
        for k in range(tries):
            self._wait(host, gap)
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    return r.read()
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                err = e
                if isinstance(e, urllib.error.HTTPError) and e.code in (400, 401, 403, 404):
                    break
                time.sleep(5 * (k + 1))
        raise RuntimeError(f"GET {url} failed: {err}")


def cached_json(net, path, fetch):
    if path.is_file():
        return json.loads(path.read_text())
    obj = fetch()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1))
    return obj


# ---------------------------------------------------------------- profiles
def interval_profile(rows, label):
    """rows: dicts top, bot, sand, clay (+silt, om_kgm3). Returns sorted intervals."""
    out = []
    for r in rows:
        if r.get("sand") is None or r.get("clay") is None:
            continue
        s, c = float(r["sand"]), float(r["clay"])
        if s + c > 100.0 + 1e-6:
            f = 100.0 / (s + c); s, c = s * f, c * f
        out.append({"top": float(r["top"]), "bot": float(r["bot"]), "sand": s, "clay": c,
                    "om_kgm3": r.get("om_kgm3"), "label": label, "note": r.get("note", "")})
    return sorted(out, key=lambda r: (r["top"], r["bot"]))


def points_to_intervals(samples, label, gap_cm=8.0, tail_cm=15.0):
    """Cluster point samples by depth (a gap > gap_cm cm starts a new cluster), median per cluster,
    then make contiguous intervals with mid-point boundaries."""
    pts = sorted((s for s in samples if s.get("depth") is not None), key=lambda s: s["depth"])
    clusters = []
    if pts and all(s.get("rank") is not None for s in pts):
        # ReESH protocol: each plot sampled at surface / shallow / deep -> group by within-plot rank
        for k in sorted({s["rank"] for s in pts}):
            clusters.append([s for s in pts if s["rank"] == k])
    else:
        for s in pts:
            if clusters and s["depth"] - clusters[-1][-1]["depth"] <= gap_cm:
                clusters[-1].append(s)
            else:
                clusters.append([s])
    med = []
    for cl in clusters:
        tex = [s for s in cl if s.get("sand") is not None and s.get("clay") is not None]
        om = [s["om_kgm3"] for s in cl if s.get("om_kgm3") is not None]
        med.append({"depth": statistics.median(s["depth"] for s in cl),
                    "sand": statistics.median(s["sand"] for s in tex) if tex else None,
                    "clay": statistics.median(s["clay"] for s in tex) if tex else None,
                    "n": len(tex), "om_kgm3": statistics.median(om) if om else None})
    med = [m for m in med if m["sand"] is not None]
    rows = []
    for i, m in enumerate(med):
        top = 0.0 if i == 0 else 0.5 * (med[i - 1]["depth"] + m["depth"])
        bot = m["depth"] + tail_cm if i == len(med) - 1 else 0.5 * (m["depth"] + med[i + 1]["depth"])
        rows.append({"top": top, "bot": max(bot, top + 1.0), "sand": m["sand"], "clay": m["clay"],
                     "om_kgm3": m["om_kgm3"], "note": f"median of {m['n']} samples near {m['depth']:g} cm"})
    return interval_profile(rows, label)


def value_at(profile, depth_cm):
    for r in profile:
        if r["top"] <= depth_cm < r["bot"]:
            return r
    return None


def recommend(profiles, priority):
    """profiles: {source: [intervals]} -> list of 10 layer dicts."""
    layers = []
    for j, z in enumerate(NODES_CM, start=1):
        pick, how = None, ""
        for src in priority:
            r = value_at(profiles.get(src, []), z)
            if r:
                pick, how = (src, r), "COVERED"
                break
        if pick is None:
            prev = layers[-1]["source"] if layers else None
            for src in ((prev,) if prev in DEEP_FILL else ()) + DEEP_FILL:
                prof = [r for r in profiles.get(src, []) if r.get("bot") is not None]
                if prof:
                    deepest = max(prof, key=lambda r: r["bot"])
                    if z >= deepest["bot"]:
                        pick, how = (src, deepest), f"EXTENDED_BELOW_{deepest['bot']:g}cm"
                        break
        if pick is None and profiles.get("SURFACE"):
            r = profiles["SURFACE"][j - 1]
            pick, how = ("SURFACE", r), "KEEP_SURFACE"
        if pick is None:
            layers.append({"layer": j, "node_m": round(NODES_M[j - 1], 4), "PCT_SAND": None, "PCT_CLAY": None,
                           "source": "NONE", "how": "NO_DATA", "usda_class": ""})
            continue
        src, r = pick
        layers.append({"layer": j, "node_m": round(NODES_M[j - 1], 4), "PCT_SAND": round(r["sand"], 2),
                       "PCT_CLAY": round(r["clay"], 2), "source": src, "how": how,
                       "usda_class": usda_class(r["sand"], r["clay"]),
                       "ORGANIC_candidate_kgm3": None if r.get("om_kgm3") is None else round(r["om_kgm3"], 1)})
    return layers


# ---------------------------------------------------------------- sources
def read_manifest(sites):
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    known = [r["site"] for r in rows]
    if sites:
        bad = [s for s in sites if s not in known]
        if bad:
            raise SystemExit("Not in 50-site manifest: " + ",".join(bad))
        rows = [r for r in rows if r["site"] in sites]
    return rows


def find_bif(sites_root, site, package):
    base = sites_root / site / "forcing"
    hits = []
    if base.is_dir():
        for raw in sorted(d for d in base.iterdir() if d.is_dir() and d.name.lower().startswith("raw")):
            hits += [p for p in raw.rglob("*.csv") if "_BIF_" in p.name.upper()]
    if not hits:
        return None, "NO_BIF_FOUND"
    pref = [p for p in hits if package and package in str(p)]
    pick = sorted(pref or hits)[0]
    return pick, ("ONE" if len(hits) == 1 else f"{len(hits)}_FOUND_USED_{'PACKAGE' if pref else 'FIRST'}")


def read_xlsx_rows(path):
    """Minimal first-sheet .xlsx reader (zip + XML), so openpyxl is not required."""
    import zipfile
    import xml.etree.ElementTree as ET
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % ns["m"])))
        sheets = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        root = ET.fromstring(z.read(sheets[0]))
    def col(ref):
        k = 0
        for ch in re.match(r"[A-Z]+", ref).group(0):
            k = k * 26 + ord(ch) - 64
        return k - 1
    table = []
    for row in root.iter("{%s}row" % ns["m"]):
        vals = {}
        for c in row.findall("m:c", ns):
            t, v = c.get("t"), c.find("m:v", ns)
            if t == "s" and v is not None:
                x = shared[int(v.text)]
            elif t == "inlineStr":
                x = "".join(e.text or "" for e in c.iter("{%s}t" % ns["m"]))
            else:
                x = v.text if v is not None else ""
            vals[col(c.get("r"))] = x
        if vals:
            table.append([vals.get(i, "") for i in range(max(vals) + 1)])
    head = [h.strip().upper() for h in table[0]]
    return [dict(zip(head, r + [""] * (len(head) - len(r)))) for r in table[1:]]


def read_bif_rows(path):
    if path.suffix.lower() == ".xlsx":
        rows = read_xlsx_rows(path)
    else:
        with path.open(encoding="latin-1", newline="") as f:
            rows = [{k.strip().upper(): v for k, v in r.items() if k} for r in csv.DictReader(f)]
    need = ("GROUP_ID", "VARIABLE_GROUP", "VARIABLE", "DATAVALUE")
    if rows and not all(k in rows[0] for k in need):
        raise ValueError(f"{path.name}: BIF columns {list(rows[0])}")
    return rows


BAD_STATS = ("min", "max", "minimum", "maximum", "standard deviation", "sd", "standard error", "range")


def parse_bif(path, site=None, manual=None):
    """Returns lat, lon, soil_rows, BADM texture profile, texture-group decisions.
    Depth: SOIL_TEX_PROFILE_MIN/MAX; else the depth of another soil group with
    the same *_HORIZON; else data/badm_manual_depth_assignments_*.csv; else the
    group is recorded but NOT used (no depth is ever assumed)."""
    manual = manual or {}
    groups = {}
    for r in read_bif_rows(path):
        if site and r.get("SITE_ID") and r["SITE_ID"].strip().upper() != site.upper():
            continue
        g = groups.setdefault(str(r["GROUP_ID"]).strip(), {"_group": r["VARIABLE_GROUP"].strip()})
        g.setdefault(r["VARIABLE"].strip(), str(r["DATAVALUE"]).strip())
    lat = lon = None
    soil_rows, tex, decisions = [], [], []
    horizon_depth = {}
    for gid, g in groups.items():
        grp = g["_group"].upper()
        if grp.startswith("GRP_SOIL"):
            pre = grp.replace("GRP_", "")
            hz = g.get(pre + "_HORIZON", "").strip().upper()
            t, b = num(g.get(pre + "_PROFILE_MIN")), num(g.get(pre + "_PROFILE_MAX"))
            if hz and t is not None and b is not None and b > t:
                horizon_depth.setdefault(hz, (t, b))
    for gid, g in groups.items():
        if "LOCATION_LAT" in g and lat is None:
            lat, lon = num(g.get("LOCATION_LAT")), num(g.get("LOCATION_LONG"))
        if not g["_group"].upper().startswith("GRP_SOIL"):
            continue
        for k, v in g.items():
            if k != "_group":
                soil_rows.append({"group_id": gid, "variable_group": g["_group"], "variable": k, "value": v, "bif_file": path.name})
        if g["_group"].upper() != "GRP_SOIL_TEX":
            continue
        sand, clay, silt = num(g.get("SOIL_TEX_SAND")), num(g.get("SOIL_TEX_CLAY")), num(g.get("SOIL_TEX_SILT"))
        if sand is None and clay is None:
            continue
        d = {"group_id": gid, "sand": sand, "silt": silt, "clay": clay, "horizon": g.get("SOIL_TEX_HORIZON", ""),
             "comment": g.get("SOIL_TEX_COMMENT", "")[:300], "bif_file": path.name}
        stat = g.get("SOIL_TEX_SAND_STATISTIC", g.get("SOIL_TEX_CLAY_STATISTIC", "")).strip().lower()
        top, bot = num(g.get("SOIL_TEX_PROFILE_MIN")), num(g.get("SOIL_TEX_PROFILE_MAX"))
        how = "BADM_PROFILE_MIN_MAX"
        if (top is None or bot is None or bot <= top) and d["horizon"].strip().upper() in horizon_depth:
            top, bot = horizon_depth[d["horizon"].strip().upper()]; how = f"DEPTH_FROM_HORIZON_{d['horizon'].strip().upper()}"
        man = manual.get((site, gid))
        if man:
            if man["decision"].upper().startswith("USE"):
                top, bot = num(man["depth_top_cm"]), num(man["depth_bottom_cm"])
                sand = num(man["sand_pct"]) if num(man["sand_pct"]) is not None else sand
                clay = num(man["clay_pct"]) if num(man["clay_pct"]) is not None else clay
                how = "MANUAL_ASSIGNMENT"
            else:
                top = bot = None; how = "MANUAL_" + man["decision"].upper()
            d["manual_rationale"] = man["rationale"]
        if stat in BAD_STATS:
            d.update(decision="NOT_USED_STATISTIC_" + stat.upper().replace(" ", "_"))
        elif sand is None or clay is None:
            d.update(decision="NOT_USED_SAND_OR_CLAY_MISSING" if not how.startswith("MANUAL_") else how)
        elif top is None or bot is None or bot <= top:
            d.update(decision="NOT_USED_NO_DEPTH" if not how.startswith("MANUAL_") else how)
        elif bot <= 0:
            d.update(decision="NOT_USED_ORGANIC_LAYER_ABOVE_MINERAL_ZERO")
        else:
            d.update(decision="USED", depth_top_cm=max(top, 0.0), depth_bottom_cm=bot, depth_source=how)
            tex.append({"top": max(top, 0.0), "bot": bot, "sand": sand, "clay": clay, "note": f"BADM group {gid} {how}"})
        decisions.append(d)
    return lat, lon, soil_rows, interval_profile(tex, "BADM"), decisions


def find_full_badm(badm_dir, site):
    if not badm_dir:
        return None
    hits = [p for p in badm_dir.rglob("*") if p.is_file() and p.suffix.lower() in (".xlsx", ".csv")
            and re.search(r"AMF_" + re.escape(site) + r"_BIF_(\d{8})", p.name, re.I)]
    return max(hits, key=lambda p: re.search(r"_BIF_(\d{8})", p.name).group(1)) if hits else None


def read_manual():
    by = {}
    if BADM_MANUAL.is_file():
        for r in csv.DictReader(BADM_MANUAL.open(encoding="utf-8")):
            by[(r["site"], str(r["group_id"]).strip())] = r
    return by


def reesh(net, site, cache, known):
    """Return (samples, meta). Search Zenodo for ReESH_<SITE>; verify MD5."""
    d = cache / "reesh"; d.mkdir(parents=True, exist_ok=True)
    meta_path = d / f"{site}.json"
    meta = json.loads(meta_path.read_text()) if meta_path.is_file() else None
    if meta is None:
        pat = re.compile(r"^ReESH_(?:US-)?" + re.escape(site) + r"\b", re.I)
        q = urllib.parse.quote(f'title:"ReESH_{site}"')
        hits = json.loads(net.get(f"https://zenodo.org/api/records?q={q}&size=25&sort=mostrecent", gap=2.0))
        recs = [h for h in hits.get("hits", {}).get("hits", []) if pat.search(h.get("metadata", {}).get("title", ""))]
        if not recs and site in known:
            recs = [json.loads(net.get(f"https://zenodo.org/api/records/{known[site]}", gap=2.0))]
        if not recs:
            meta = {"status": "NO_REESH_RECORD", "searched_utc": utc()}
        else:
            rec = recs[0]
            files = [f for f in rec.get("files", []) if f.get("key", "").lower().endswith("soilcharacteristics.csv")]
            if not files:
                meta = {"status": "REESH_RECORD_WITHOUT_SOILCHARACTERISTICS", "record": rec.get("id")}
            else:
                f = files[0]
                blob = net.get(f["links"]["self"], gap=2.0)
                md5 = hashlib.md5(blob).hexdigest()
                want = str(f.get("checksum", "")).replace("md5:", "")
                if want and md5 != want:
                    raise RuntimeError(f"{site}: ReESH MD5 mismatch {md5} != {want}")
                (d / f"{site}_SoilCharacteristics.csv").write_bytes(blob)
                meta = {"status": "OK", "record": rec.get("id"), "doi": rec.get("doi"),
                        "title": rec["metadata"].get("title"), "version_date": rec["metadata"].get("publication_date"),
                        "file": f["key"], "md5": md5, "md5_verified": bool(want), "downloaded_utc": utc(),
                        "license": (rec["metadata"].get("license") or {}).get("id")}
        meta_path.write_text(json.dumps(meta, indent=1))
    if meta.get("status") != "OK":
        return [], meta
    samples = []
    with (d / f"{site}_SoilCharacteristics.csv").open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            om, bd = num(r.get("Pct_OM")), num(r.get("Bulk_Den_g_m3"))
            samples.append({"depth": num(r.get("Depth_cm")), "sand": num(r.get("SAND")), "clay": num(r.get("CLAY")),
                            "silt": num(r.get("SILT")), "pct_om": om, "bd_gcm3": bd,
                            "om_kgm3": None if om is None or bd is None else om / 100.0 * bd * 1000.0,
                            "lat": num(r.get("Latitude")), "lon": num(r.get("Longitude")), "id": r.get("Sample_ID")})
    plots = {}
    for x in samples:
        pid = re.sub(r"_\d+$", "", str(x.get("id") or ""))
        if pid and x["depth"] is not None:
            plots.setdefault(pid, []).append(x)
    if plots and sum(len(v) for v in plots.values()) == len([x for x in samples if x["depth"] is not None]):
        for v in plots.values():
            for k, x in enumerate(sorted(v, key=lambda x: x["depth"])):
                x["rank"] = k
    return samples, meta


SDA_SQL = """SELECT mu.mukey, mu.muname, c.cokey, c.compname, c.comppct_r, c.majcompflag, c.taxorder,
 ch.hzname, ch.hzdept_r, ch.hzdepb_r, ch.sandtotal_r, ch.silttotal_r, ch.claytotal_r, ch.om_r, ch.dbthirdbar_r
FROM mapunit mu INNER JOIN component c ON c.mukey = mu.mukey LEFT JOIN chorizon ch ON ch.cokey = c.cokey
WHERE mu.mukey IN (SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('point({lon} {lat})'))
ORDER BY c.comppct_r DESC, c.cokey, ch.hzdept_r"""


def ssurgo(net, site, lat, lon, cache):
    path = cache / "ssurgo" / f"{site}.json"
    def fetch():
        body = json.dumps({"query": SDA_SQL.format(lat=lat, lon=lon), "format": "JSON+COLUMNNAME"}).encode()
        raw = net.get("https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest", gap=1.0, data=body,
                      headers={"Content-Type": "application/json"})
        js = json.loads(raw) if raw.strip() else {}
        return {"lat": lat, "lon": lon, "retrieved_utc": utc(), "Table": js.get("Table", [])}
    js = cached_json(net, path, fetch)
    tab = js.get("Table") or []
    if len(tab) < 2:
        return [], [], {"status": "NO_SSURGO_MAPUNIT"}
    cols, rows = tab[0], [dict(zip(tab[0], r)) for r in tab[1:]]
    comps = {}
    for r in rows:
        comps.setdefault(r["cokey"], []).append(r)
    def tex_rows(rs):
        return [r for r in rs if num(r["sandtotal_r"]) is not None and num(r["claytotal_r"]) is not None]
    ranked = sorted(comps.values(), key=lambda rs: -(num(rs[0]["comppct_r"]) or 0))
    dom = next((rs for rs in ranked if tex_rows(rs)), None)
    if dom is None:
        return rows, [], {"status": "SSURGO_NO_TEXTURE", "mapunit": rows[0]["muname"]}
    prof = []
    for r in dom:
        om, bd = num(r["om_r"]), num(r["dbthirdbar_r"])
        prof.append({"top": num(r["hzdept_r"]), "bot": num(r["hzdepb_r"]), "sand": num(r["sandtotal_r"]),
                     "clay": num(r["claytotal_r"]), "om_kgm3": None if om is None or bd is None else om / 100 * bd * 1000,
                     "note": f"{r['compname']} {r['hzname']}"})
    prof = [p for p in prof if p["top"] is not None and p["bot"] is not None]
    meta = {"status": "OK", "mapunit": dom[0]["muname"], "mukey": dom[0]["mukey"], "component": dom[0]["compname"],
            "comppct_r": dom[0]["comppct_r"], "taxorder": dom[0]["taxorder"],
            "n_components": len(comps), "organic_horizons_without_texture": sum(1 for r in dom if num(r["sandtotal_r"]) is None)}
    return rows, interval_profile(prof, "SSURGO"), meta


def soilgrids(net, site, lat, lon, cache):
    path = cache / "soilgrids" / f"{site}.json"
    def fetch():
        q = [("lon", f"{lon:.5f}"), ("lat", f"{lat:.5f}")] + [("property", p) for p in ("sand", "silt", "clay", "soc", "bdod")] \
            + [("depth", d) for d in SOILGRIDS_DEPTHS] + [("value", "mean")]
        url = "https://rest.isric.org/soilgrids/v2.0/properties/query?" + urllib.parse.urlencode(q)
        js = json.loads(net.get(url, gap=13.0))   # ISRIC fair use: 5 calls/minute
        js["retrieved_utc"] = utc()
        return js
    js = cached_json(net, path, fetch)
    vals = {}
    for layer in js.get("properties", {}).get("layers", []):
        df = float(layer.get("unit_measure", {}).get("d_factor", 1) or 1)
        for dd in layer.get("depths", []):
            v = dd.get("values", {}).get("mean")
            rng = dd.get("range", {})
            vals.setdefault((rng.get("top_depth"), rng.get("bottom_depth")), {})[layer["name"]] = None if v is None else v / df
    rows = []
    for (top, bot), v in sorted(vals.items()):
        soc, bd = v.get("soc"), v.get("bdod")       # g/kg, kg/dm3 after d_factor
        rows.append({"top": top, "bot": bot, "sand": v.get("sand"), "clay": v.get("clay"), "silt": v.get("silt"),
                     "soc_gkg": soc, "bdod_gcm3": bd,
                     "om_kgm3": None if soc is None or bd is None else 1.724 * soc * bd,
                     "note": "SoilGrids2.0 mean; OM = 1.724*SOC*BD (approx.)"})
    status = "OK" if any(r["sand"] is not None for r in rows) else "SOILGRIDS_NO_DATA"
    return rows, interval_profile(rows, "SOILGRIDS"), {"status": status}


def nml_fsurdat(lnd_in):
    m = re.search(r"^\s*fsurdat\s*=\s*['\"]([^'\"]+)['\"]", lnd_in.read_text(errors="replace"), re.M)
    return m.group(1) if m else None


def find_surfaces(site, sites_root, cases_root, override):
    found = []
    if override:
        found.append((Path(override), "OVERRIDE"))
    if cases_root and cases_root.is_dir():
        for case in sorted(cases_root.glob(f"{site}_*")):
            lnd = case / "CaseDocs/lnd_in"
            if lnd.is_file():
                f = nml_fsurdat(lnd)
                if f:
                    found.append((Path(f), "CASE:" + case.name))
    base = sites_root / site
    if base.is_dir():
        for root, dirs, files in os.walk(base):
            dirs[:] = [x for x in dirs if x.lower() not in ("forcing", "raw", "packages") and not x.lower().startswith("raw")]
            for fn in files:
                if fn.startswith("surfdata") and fn.endswith(".nc"):
                    found.append((Path(root) / fn, "SITE_FOLDER"))
    seen, out = set(), []
    for p, how in found:
        k = str(p)
        if k not in seen and p.is_file():
            seen.add(k); out.append((p, how))
    return out


def read_surface(path, lat, lon):
    from netCDF4 import Dataset
    import numpy as np
    with Dataset(str(path)) as ds:
        def grab(name):
            if name not in ds.variables:
                return None
            a = np.asarray(ds.variables[name][:], dtype=float)
            if a.ndim == 3 and a.shape[1] * a.shape[2] > 1:
                if lat is None:
                    raise ValueError("multi-point surface and no coordinates")
                la = np.asarray(ds.variables["LATIXY"][:], float); lo = np.asarray(ds.variables["LONGXY"][:], float)
                d = (la - lat) ** 2 + (((lo - (lon % 360)) + 180) % 360 - 180) ** 2
                i, k = np.unravel_index(np.argmin(d), d.shape)
                return a[:, i, k]
            return a.reshape(a.shape[0], -1)[:, 0]
        sand, clay, org = grab("PCT_SAND"), grab("PCT_CLAY"), grab("ORGANIC")
    if sand is None or clay is None or len(sand) < 10:
        raise ValueError(f"{path.name}: PCT_SAND/PCT_CLAY with 10 levels not found")
    return [{"top": None, "bot": None, "sand": float(sand[j]), "clay": float(clay[j]),
             "om_kgm3": None if org is None else float(org[j]), "label": "SURFACE"} for j in range(10)]


def read_lit():
    by = {}
    for r in csv.DictReader(LIT_CSV.open(encoding="utf-8")):
        by.setdefault(r["site"], []).append(r)
    return by


def lit_profile(rows):
    numeric = [r for r in rows if r["use_numeric"].upper() == "YES"]
    pts = [r for r in numeric if num(r["depth_top_cm"]) == num(r["depth_bottom_cm"])]
    ints = [r for r in numeric if r not in pts]
    prof = interval_profile([{"top": num(r["depth_top_cm"]), "bot": num(r["depth_bottom_cm"]), "sand": num(r["sand_pct"]),
                              "clay": num(r["clay_pct"]), "note": r["note"]} for r in ints], "LIT")
    if pts:
        prof += points_to_intervals([{"depth": num(r["depth_top_cm"]), "sand": num(r["sand_pct"]),
                                      "clay": num(r["clay_pct"])} for r in pts], "LIT")
    return sorted(prof, key=lambda r: r["top"])


# ---------------------------------------------------------------- driver
def write_csv(path, rows, fields=None):
    rows = list(rows)
    fields = fields or sorted({k for r in rows for k in r}, key=lambda k: (k not in ("site",), k))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def top_mean(layers, key):
    v = [l[key] for l in layers[:5] if l.get(key) is not None]
    return round(sum(v) / len(v), 1) if v else None


def run(a):
    out = a.output_root; cache = out / "cache"; cache.mkdir(parents=True, exist_ok=True)
    net = Net(not a.no_network, cache)
    known = {r["site"]: r["zenodo_record"] for r in csv.DictReader(REESH_KNOWN.open(encoding="utf-8"))}
    lit = read_lit()
    coords_override = {}
    for x in a.coords:
        s, la, lo = x.split(":"); coords_override[s] = (float(la), float(lo))
    surf_override = dict(x.split("=", 1) for x in a.surface)
    T = {k: [] for k in ("coords", "bif", "badm", "reesh", "ssurgo", "soilgrids", "surface", "cand", "rec", "summary", "wide")}
    meta_all = {"generated_utc": utc(), "priority": a.priority, "nodes_m": NODES_M, "network": not a.no_network, "sites": {}}
    for m in read_manifest(a.sites):
        print(f"=== {m['site']}", flush=True)
        try:
            one_site(a, m, net, cache, known, lit, coords_override, surf_override, T, meta_all)
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  SITE FAILED (others continue): {type(e).__name__}: {e}", flush=True)
            T["summary"].append({"site": m["site"], "batch": m["batch"], "tier": "SCRIPT_ERROR", "notes": f"{type(e).__name__}: {e}"})
    finish(out, T, meta_all)


def one_site(a, m, net, cache, known, lit, coords_override, surf_override, T, meta_all):
        s = m["site"]; info = {"batch": m["batch"], "package": m["package"]}
        profiles, notes = {}, []
        lat = lon = None; csrc = ""
        manual = read_manual()
        try:
            bif, how = find_bif(a.sites_root, s, m["package"]); info["bif"] = str(bif) if bif else how
            if bif:
                lat, lon, rows, prof, dec = parse_bif(bif, s, manual); csrc = "BIF"
                T["bif"] += [{"site": s, **r} for r in rows]
                T["badm"] += [{"site": s, "badm_kind": "FLUXNET_PACKAGE_BIF", **d} for d in dec]
                if prof: profiles["BADM"] = prof
                info["bif_soil_rows"] = len(rows)
        except Exception as e:
            notes.append(f"BIF error: {e}")
        full = find_full_badm(a.badm_dir, s)
        info["full_badm"] = str(full) if full else ("NOT_FOUND" if a.badm_dir else "NOT_SUPPLIED")
        if full:
            try:
                la2, lo2, rows, prof, dec = parse_bif(full, s, manual)
                T["bif"] += [{"site": s, **r} for r in rows]
                T["badm"] += [{"site": s, "badm_kind": "FULL_BADM", **d} for d in dec]
                if prof:
                    profiles["BADM"] = prof          # full BADM supersedes the package BIF subset
                if lat is None and la2 is not None:
                    lat, lon, csrc = la2, lo2, "FULL_BADM"
                info["full_badm_soil_rows"] = len(rows)
            except Exception as e:
                notes.append(f"full BADM error: {e}")
        if s in coords_override:
            lat, lon = coords_override[s]; csrc = "OVERRIDE"
        if s in lit:
            p = lit_profile(lit[s])
            if p: profiles["LIT"] = p
            info["literature_rows"] = len(lit[s])
        if "REESH" in a.priority:
            try:
                smp, rm = reesh(net, s, cache, known); info["reesh"] = rm
                if smp:
                    profiles["REESH"] = points_to_intervals(smp, "REESH")
                    T["reesh"] += [{"site": s, "record": rm.get("record"), **x} for x in smp]
                    if lat is None and smp[0].get("lat") is not None:
                        lat, lon, csrc = smp[0]["lat"], smp[0]["lon"], "REESH"
            except Exception as e:
                notes.append(f"ReESH: {e}"); info["reesh"] = {"status": "ERROR", "error": str(e)}
        T["coords"].append({"site": s, "lat": lat, "lon": lon, "coord_source": csrc or "MISSING"})
        if lat is not None and "SSURGO" in a.priority and (s.startswith("US-")):
            try:
                rows, prof, sm = ssurgo(net, s, lat, lon, cache); info["ssurgo"] = sm
                T["ssurgo"] += [{"site": s, **r} for r in rows]
                if prof: profiles["SSURGO"] = prof
            except Exception as e:
                notes.append(f"SSURGO: {e}"); info["ssurgo"] = {"status": "ERROR", "error": str(e)}
        if lat is not None and "SOILGRIDS" in a.priority:
            try:
                rows, prof, gm = soilgrids(net, s, lat, lon, cache); info["soilgrids"] = gm
                T["soilgrids"] += [{"site": s, **r} for r in rows]
                if prof: profiles["SOILGRIDS"] = prof
            except Exception as e:
                notes.append(f"SoilGrids: {e}"); info["soilgrids"] = {"status": "ERROR", "error": str(e)}
        surfs, ref = [], None
        try:
            surfs = find_surfaces(s, a.sites_root, a.cases_root, surf_override.get(s))
            for p, how in surfs:
                try:
                    lay = read_surface(p, lat, lon)
                    for j, l in enumerate(lay, 1):
                        T["surface"].append({"site": s, "surface": str(p), "found_by": how, "layer": j,
                                             "PCT_SAND": round(l["sand"], 2), "PCT_CLAY": round(l["clay"], 2),
                                             "ORGANIC": None if l["om_kgm3"] is None else round(l["om_kgm3"], 1)})
                    rank = (0 if how == "OVERRIDE" else 1 if how.startswith("CASE") else 2, -p.stat().st_mtime)
                    if ref is None or rank < ref[3]:
                        ref = (p, how, lay, rank)
                except Exception as e:
                    notes.append(f"surface {p.name}: {e}")
        except Exception as e:
            notes.append(f"surface search: {e}")
        if ref:
            profiles["SURFACE"] = ref[2]
        for src, prof in profiles.items():
            if src == "SURFACE":
                continue
            for j, z in enumerate(NODES_CM, 1):
                r = value_at(prof, z)
                T["cand"].append({"site": s, "source": src, "layer": j, "node_m": round(NODES_M[j - 1], 4),
                                  "PCT_SAND": None if not r else round(r["sand"], 2), "PCT_CLAY": None if not r else round(r["clay"], 2),
                                  "ORGANIC_candidate_kgm3": None if not r or r.get("om_kgm3") is None else round(r["om_kgm3"], 1),
                                  "covered": bool(r)})
        layers = recommend(profiles, a.priority)
        cur = ref[2] if ref else None
        for l in layers:
            c = cur[l["layer"] - 1] if cur else None
            T["rec"].append({"site": s, **l, "current_surface_PCT_SAND": None if not c else round(c["sand"], 2),
                             "current_surface_PCT_CLAY": None if not c else round(c["clay"], 2),
                             "delta_sand": None if not c or l["PCT_SAND"] is None else round(l["PCT_SAND"] - c["sand"], 2),
                             "delta_clay": None if not c or l["PCT_CLAY"] is None else round(l["PCT_CLAY"] - c["clay"], 2)})
        top_src = [l["source"] for l in layers[:5]]
        primary = max(set(top_src), key=top_src.count) if top_src else "NONE"
        tier = {"REESH": "T1_SITE_MEASURED", "BADM": "T1_SITE_MEASURED", "LIT": "T1_SITE_MEASURED",
                "SSURGO": "T2_SSURGO_POINT", "SOILGRIDS": "T3_SOILGRIDS_250M", "SURFACE": "T4_KEEP_SURFACE"}.get(primary, "NO_DATA")
        flags = []
        site_src = next((x for x in ("REESH", "BADM", "LIT") if x in profiles), None)
        for survey in ("SSURGO", "SOILGRIDS"):
            if site_src and survey in profiles:
                a1 = top_mean(recommend({site_src: profiles[site_src]}, [site_src]), "PCT_SAND")
                a2 = top_mean(recommend({survey: profiles[survey]}, [survey]), "PCT_SAND")
                if a1 is not None and a2 is not None and abs(a1 - a2) > 25:
                    flags.append(f"{site_src}_vs_{survey}_TOP30_SAND_DIFF_{a1 - a2:+.0f}")
        if any(l.get("ORGANIC_candidate_kgm3") and l["ORGANIC_candidate_kgm3"] > 100 for l in layers[:4]):
            flags.append("ORGANIC_RICH_TOPSOIL_REVIEW_ORGANIC")
        lit_cls = "; ".join(sorted({r["texture_class"] for r in lit.get(s, []) if r["texture_class"]}))
        T["summary"].append({"site": s, "batch": m["batch"], "tier": tier, "primary_source": primary,
                             "layer_sources": "|".join(l["source"] for l in layers),
                             "top30cm_PCT_SAND": top_mean(layers, "PCT_SAND"), "top30cm_PCT_CLAY": top_mean(layers, "PCT_CLAY"),
                             "top30cm_class": usda_class(top_mean(layers, "PCT_SAND"), top_mean(layers, "PCT_CLAY")),
                             "current_top30cm_PCT_SAND": None if not cur else round(sum(x["sand"] for x in cur[:5]) / 5, 1),
                             "current_top30cm_PCT_CLAY": None if not cur else round(sum(x["clay"] for x in cur[:5]) / 5, 1),
                             "reference_surface": "" if not ref else f"{ref[1]}:{ref[0]}", "n_surfaces_found": len(surfs),
                             "literature_class": lit_cls, "flags": ";".join(flags), "notes": " | ".join(notes)})
        T["wide"].append({"site": s, "tier": tier, **{f"PCT_SAND_L{l['layer']}": l["PCT_SAND"] for l in layers},
                          **{f"PCT_CLAY_L{l['layer']}": l["PCT_CLAY"] for l in layers}})
        info.update(lat=lat, lon=lon, coord_source=csrc, sources=sorted(profiles), notes=notes)
        meta_all["sites"][s] = info
        print(f"  coords={lat},{lon} ({csrc or 'MISSING'}) sources={sorted(profiles)} tier={tier} "
              f"top30 sand/clay={top_mean(layers, 'PCT_SAND')}/{top_mean(layers, 'PCT_CLAY')}"
              + (f" NOTES: {' | '.join(notes)}" if notes else ""), flush=True)


def finish(out, T, meta_all):
    names = {"coords": "01_site_coordinates.csv", "bif": "02_bif_soil_badm_rows.csv", "reesh": "03_reesh_samples.csv",
             "ssurgo": "04_ssurgo_horizons.csv", "soilgrids": "05_soilgrids_profiles.csv", "surface": "06_current_surface_layers.csv",
             "cand": "07_clm10_candidates_by_source.csv", "rec": "08_RECOMMENDED_CLM10_SOIL_TEXTURE_LONG.csv",
             "wide": "09_RECOMMENDED_CLM10_PCT_SAND_PCT_CLAY_WIDE.csv", "summary": "10_RECOMMENDED_SITE_SUMMARY.csv",
             "badm": "11_badm_soil_tex_groups_and_decisions.csv"}
    for k, fn in names.items():
        if T[k]:
            write_csv(out / fn, T[k])
    (out / "metadata.json").write_text(json.dumps(meta_all, indent=1, default=str) + "\n")
    print("\nWROTE", out)
    for r in T["summary"]:
        g = lambda k: r.get(k, "")
        print(f"{r['site']:7} {r['tier']:18} top30 {g('top30cm_PCT_SAND')}/{g('top30cm_PCT_CLAY')} {str(g('top30cm_class')):16} "
              f"current {g('current_top30cm_PCT_SAND')}/{g('current_top30cm_PCT_CLAY')} {g('flags')} {g('notes')}")


def self_test():
    assert abs(NODES_M[0] - 0.0071) < 1e-4 and abs(NODES_M[9] - 2.8646) < 1e-3
    assert usda_class(93, 1) == "sand" and usda_class(65, 10) == "sandy loam" and usda_class(40, 20) == "loam"
    assert usda_class(20, 15) == "silt loam" and usda_class(10, 35) == "silty clay loam" and usda_class(20, 60) == "clay"
    p = points_to_intervals([{"depth": 0, "sand": 60, "clay": 10}, {"depth": 12, "sand": 66, "clay": 13},
                             {"depth": 16, "sand": 56, "clay": 17}, {"depth": 48, "sand": 72, "clay": 8}], "T")
    assert [round(r["top"], 1) for r in p] == [0, 7.0, 31.0] and p[1]["sand"] == 61.0, p
    lay = recommend({"REESH": p, "SOILGRIDS": interval_profile(
        [{"top": 0, "bot": 100, "sand": 40, "clay": 20}, {"top": 100, "bot": 200, "sand": 30, "clay": 30}], "S")}, DEFAULT_PRIORITY)
    assert [l["source"] for l in lay] == ["REESH"] * 7 + ["SOILGRIDS"] * 3, lay
    assert lay[7]["how"] == "COVERED" and lay[9]["how"].startswith("EXTENDED") and lay[9]["PCT_CLAY"] == 30
    pr = points_to_intervals([{"depth": d, "sand": sa, "clay": 5, "rank": k} for d, sa, k in
                              ((0, 60, 0), (0, 62, 0), (12, 64, 1), (14, 66, 1), (48, 70, 2), (64, 90, 2))], "R")
    assert len(pr) == 3 and pr[2]["sand"] == 80 and pr[2]["top"] == 34.5, pr
    lay = recommend({"LIT": interval_profile([{"top": 0, "bot": 50, "sand": 98, "clay": 1}], "L")}, DEFAULT_PRIORITY)
    assert all(l["PCT_SAND"] == 98 for l in lay) and lay[9]["how"].startswith("EXTENDED")
    surf = [{"top": None, "bot": None, "sand": 30.0 + j, "clay": 20.0, "om_kgm3": None} for j in range(10)]
    lay = recommend({"SURFACE": surf}, DEFAULT_PRIORITY)
    assert all(l["source"] == "SURFACE" for l in lay) and lay[9]["PCT_SAND"] == 39.0, lay
    lay = recommend({"SURFACE": surf, "SOILGRIDS": interval_profile([{"top": 30, "bot": 200, "sand": 50, "clay": 10}], "S")},
                    DEFAULT_PRIORITY)
    assert [l["source"] for l in lay] == ["SURFACE"] * 5 + ["SOILGRIDS"] * 5, lay
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "AMF_XX-Tst_BIF_20260101.csv"
        f.write_text("SITE_ID,GROUP_ID,VARIABLE_GROUP,VARIABLE,DATAVALUE\n"
                     "XX-Tst,1,GRP_SOIL_TEX,SOIL_TEX_SAND,98\nXX-Tst,1,GRP_SOIL_TEX,SOIL_TEX_CLAY,0\n"
                     "XX-Tst,2,GRP_SOIL_TEX,SOIL_TEX_SAND,3\nXX-Tst,2,GRP_SOIL_TEX,SOIL_TEX_CLAY,87\n"
                     "XX-Tst,2,GRP_SOIL_TEX,SOIL_TEX_HORIZON,A\nXX-Tst,3,GRP_SOIL_CHEM,SOIL_CHEM_HORIZON,A\n"
                     "XX-Tst,3,GRP_SOIL_CHEM,SOIL_CHEM_PROFILE_MIN,0\nXX-Tst,3,GRP_SOIL_CHEM,SOIL_CHEM_PROFILE_MAX,11\n")
        _, _, _, prof, dec = parse_bif(f, "XX-Tst", {})
        d = {x["group_id"]: x["decision"] for x in dec}
        assert d == {"1": "NOT_USED_NO_DEPTH", "2": "USED"} and prof[0]["bot"] == 11, (d, prof)
        _, _, _, prof, dec = parse_bif(f, "XX-Tst", {("XX-Tst", "1"): {"decision": "USE", "depth_top_cm": "0", "depth_bottom_cm": "300",
                                                                      "sand_pct": "", "clay_pct": "", "rationale": "t"}})
        assert len(prof) == 2 and find_full_badm(Path(td), "XX-Tst") == f
    rows = [r for r in csv.DictReader(MANIFEST.open(encoding="utf-8"))]
    assert len(rows) == 50 and len({r["site"] for r in rows}) == 50
    lit = read_lit(); assert set(lit) <= {r["site"] for r in rows}, set(lit) - {r["site"] for r in rows}
    me2 = lit_profile(lit["US-Me2"]); assert [r["sand"] for r in me2] == [69, 66, 54]
    print("SOIL STAGE01 SELF-TEST PASS (no network, no writes)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--sites", nargs="+")
    ap.add_argument("--sites-root", type=Path, default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
    ap.add_argument("--cases-root", type=Path, default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases"))
    ap.add_argument("--output-root", type=Path)
    ap.add_argument("--priority", nargs="+", default=list(DEFAULT_PRIORITY), choices=DEFAULT_PRIORITY)
    ap.add_argument("--no-network", action="store_true", help="use BIF, literature and cache only")
    ap.add_argument("--badm-dir", type=Path, help="folder with full AmeriFlux BADM downloads AMF_<SITE>_BIF_<YYYYMMDD>.xlsx")
    ap.add_argument("--coords", nargs="*", default=[], metavar="SITE:LAT:LON")
    ap.add_argument("--surface", nargs="*", default=[], metavar="SITE=/abs/surfdata.nc")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.output_root is None or not a.output_root.is_absolute():
        ap.error("--output-root must be an absolute path")
    a.output_root = a.output_root.expanduser().resolve(); a.output_root.mkdir(parents=True, exist_ok=True)
    run(a)


if __name__ == "__main__":
    main()
