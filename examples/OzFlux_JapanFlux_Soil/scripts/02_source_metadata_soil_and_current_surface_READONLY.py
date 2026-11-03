#!/usr/bin/env python3
"""Stage02 (IRIDIS6, read only): soil information already inside our own OzFlux / JapanFlux source files, tower
coordinates from the original JapanFlux BIF, and the soil currently in every surface file used for the 20 sites.

1. OzFlux L6 NetCDF (sites/MY_EC_SITE/<site>/forcing/raw/<L6 file>): every global attribute is written to JSON;
   attributes whose name or value mentions soil (texture, sand/clay/silt, soil orders, bulk density, ...) are listed.
2. JapanFlux original packages (sites/MY_EC_SITE/<site>/forcing/packages/*.zip, including nested ZIPs): only
   metadata members are opened (BIF / BIFVARINFO CSV, README / TXT, XLSX / CSV under 5 MB whose name is not a
   flux or meteorology product). From BIF: every row of a GRP_SOIL* group, GRP_LOCATION, GRP_IGBP, GRP_SITE_DESC,
   GRP_SITE_CHAR, and any other row whose value mentions soil. From text / XLSX: matching lines or cells.
   Half-hourly data members are never read.
3. Current surfaces: fsurdat of every case under cases/ whose name contains the site ID (CaseDocs/lnd_in),
   surfdata*.nc under $HOME/ozflux_nc_stage0[23]_* and $HOME/ozflux_stage16_reference_* that name the site, and
   surfdata*.nc under sites/MY_EC_SITE/<site>/ (forcing folders skipped). PCT_SAND, PCT_CLAY and ORGANIC on all
   soil levels at the tower grid cell are written per file.

Nothing is modified. Outputs go to a NEW folder (default $HOME/ozjp_soil_stage02_<UTC>):
  ozflux_L6_global_attributes.json, source_soil_metadata_hits.tsv, japanflux_bif_location.tsv,
  current_surface_soil_layers.tsv, stage02_summary.json.

Usage (login node, conda env clm_fates_env):
  python3 -B 02_source_metadata_soil_and_current_surface_READONLY.py --self-test
  python3 -B 02_source_metadata_soil_and_current_surface_READONLY.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES")
SITES_ROOT = BASE / "sites" / "MY_EC_SITE"
CASES_ROOT = BASE / "cases"
OZ_L6 = {   # OzFlux_Batch01_09/data/OZFLUX_09_ORIGINAL_L6_SITES_MANIFEST.tsv (Non-Competition-CLM-experiment)
    "AU-ASM": ["AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc",
               "AliceSpringsMulga2_20240821T0700_to_20260423T0000_L6.nc"],
    "AU-Cow": ["CowBay_20090101T0900_to_20260423T0000_L6.nc"],
    "AU-Cpr": ["Calperum_L6.nc"],
    "AU-DaS": ["DalyUncleared_20080101T0000_to_20260423T0000_L6.nc"],
    "AU-Dry": ["DryRiver_L6.nc"],
    "AU-Gin": ["Gingin_L6.nc"],
    "AU-How": ["HowardSprings_L6.nc"],
    "AU-Stp": ["SturtPlains_L6.nc"],
    "AU-Tum": ["Tumbarumba1_L6.nc"],
}
JP_SITES = ("JP-Api", "JP-Fhk", "JP-Fjy", "JP-Khw", "JP-Spp", "JP-Tak", "JP-Tef", "JP-Tgf", "JP-Tmd", "JP-Tom",
            "JP-Yms")
SOIL_RE = re.compile(
    r"soil|texture|\bsand|\bclay|\bsilt|loam|kandosol|vertosol|podosol|tenosol|chromosol|dermosol|ferrosol|kurosol|"
    r"sodosol|calcarosol|rudosol|hydrosol|organosol|andosol|andisol|cambisol|podzol|regosol|gleysol|histosol|luvisol|"
    r"acrisol|ferralsol|arenosol|leptosol|inceptisol|entisol|ultisol|oxisol|alfisol|kuroboku|bulk.?density|"
    r"organic (matter|carbon)|bedrock|hardpan|laterite|pumice|scoria|volcanic ash|tephra|lava|granite|"
    r"黒ボク|土壌|褐色森林土|火山灰|軽石|粘土|砂", re.I)
# sensor descriptions that mention soil but say nothing about the soil itself
SENSOR_RE = re.compile(
    r"soil (volumetric )?(water|moisture|temperature|heat|respiration|chamber|co2|surface temperature)|"
    r"\b(SWC|TS|G|SHF|Sws|Ts|Fg|Sg)(_[A-Za-z0-9]+)*\b|土壌(水分|温度|呼吸)", re.I)
BIF_KEEP_GROUPS = re.compile(r"^GRP_(SOIL|LOCATION|IGBP|SITE_DESC|SITE_CHAR|CLIM_AVG|LAND_OWNERSHIP)", re.I)
DATA_MEMBER = re.compile(r"_(HH|HR|DD|WW|MM|YY)_|FLUXMET|FLUXNET_FULLSET|SUBSET|ERA5|AUXMETEO|AUXNEE", re.I)
NESTED_CAP = 1024 * 1024 * 1024
META_CAP = 5 * 1024 * 1024


def utc():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def soil_hit(text):
    """True if the text mentions soil after removing soil-sensor phrases."""
    return bool(SOIL_RE.search(SENSOR_RE.sub(" ", str(text))))


def sha256(p, cap=400 * 1024 * 1024):
    p = Path(p)
    if p.stat().st_size > cap:
        return "SKIPPED_LARGE"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def short(v, n=400):
    s = str(v).replace("\t", " ").replace("\r", " ").replace("\n", " | ")
    return s if len(s) <= n else s[:n] + " ..."


# ------------------------------------------------------------------ 1. OzFlux L6 global attributes
def ozflux_attrs(site, files, sites_root, hits):
    from netCDF4 import Dataset
    out = {}
    for fn in files:
        p = sites_root / site / "forcing" / "raw" / fn
        if not p.is_file():
            out[fn] = {"status": "MISSING", "path": str(p)}
            continue
        with Dataset(str(p)) as ds:
            attrs = {k: short(ds.getncattr(k), 4000) for k in ds.ncattrs()}
            lat = attrs.get("latitude") or attrs.get("site_latitude")
            lon = attrs.get("longitude") or attrs.get("site_longitude")
        out[fn] = {"status": "OK", "path": str(p), "n_attrs": len(attrs), "attrs": attrs}
        for k, v in attrs.items():
            if soil_hit(k) or soil_hit(v):
                hits.append(dict(site=site, source="OZFLUX_L6_GLOBAL_ATTR", file=fn, member="", where=k,
                                 group="", key=k, value=short(v)))
        for k in ("latitude", "longitude", "elevation", "altitude", "site_name", "canopy_height", "vegetation",
                  "tower_height"):
            if k in attrs:
                out[fn].setdefault("key_attrs", {})[k] = attrs[k]
        out[fn]["lat_lon_attr"] = [lat, lon]
    return out


# ------------------------------------------------------------------ 2. JapanFlux packages
def iter_zip_members(zf, label, depth=0):
    """Yield (path_label, ZipInfo, ZipFile) for every member, descending into nested ZIPs (bounded size)."""
    for info in zf.infolist():
        if info.is_dir():
            continue
        name = info.filename
        if name.lower().endswith(".zip") and depth < 3:
            if info.file_size > NESTED_CAP:
                yield f"{label}!{name}", info, None
                continue
            buf = io.BytesIO()
            with zf.open(info) as fp:
                for chunk in iter(lambda: fp.read(1 << 22), b""):
                    buf.write(chunk)
            buf.seek(0)
            try:
                with zipfile.ZipFile(buf) as inner:
                    yield from iter_zip_members(inner, f"{label}!{name}", depth + 1)
            except zipfile.BadZipFile:
                yield f"{label}!{name}", info, None
        else:
            yield f"{label}!{name}", info, zf


def xlsx_rows(raw):
    """Rows of all sheets as lists of strings; openpyxl if it can read the file, else a minimal XML reader."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        got = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                cells = ["" if c is None else str(c) for c in row]
                if any(cells):
                    got.append((ws.title, cells))
        yield from got
        return
    except Exception:   # not installed, or a workbook openpyxl rejects
        pass
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            xml = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
            for si in re.findall(r"<si>(.*?)</si>", xml, re.S):
                shared.append("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S)))
        for n in sorted(x for x in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", x)):
            xml = z.read(n).decode("utf-8", "replace")
            for r in re.findall(r"<row[^>]*>(.*?)</row>", xml, re.S):
                cells = []
                for attrs, body in re.findall(r"<c([^>]*)>(.*?)</c>", r, re.S):
                    v = re.search(r"<v>(.*?)</v>", body, re.S)
                    t = re.search(r"<t[^>]*>(.*?)</t>", body, re.S)
                    val = v.group(1) if v else (t.group(1) if t else "")
                    if 't="s"' in attrs and val.isdigit() and int(val) < len(shared):
                        val = shared[int(val)]
                    cells.append(val)
                if any(cells):
                    yield n, cells


def scan_bif(site, text, member, hits, locs):
    rdr = csv.reader(io.StringIO(text))
    for rec in rdr:
        if len(rec) < 5:
            continue
        sid, gid, group, key = (s.strip() for s in rec[:4])
        val = ",".join(rec[4:]).strip()
        if sid and sid != site:
            continue
        if group.upper() == "GRP_LOCATION":
            locs.append(dict(site=site, member=member, group_id=gid, key=key, value=val, line=rdr.line_num))
        if BIF_KEEP_GROUPS.match(group) or soil_hit(key) or soil_hit(val):
            hits.append(dict(site=site, source="JAPANFLUX_BIF", file=member.split("!")[0], member=member,
                             where=f"line {rdr.line_num}", group=f"{group} #{gid}", key=key, value=short(val)))


def japanflux(site, sites_root, hits, locs, inventory, copy_dir=None):
    roots = [sites_root / site / "forcing" / "packages", sites_root / site / "forcing" / "raw", sites_root / site]
    zips, others = [], []
    for r in roots:
        if r.is_dir():
            for p in sorted(r.iterdir()):
                if p.is_file() and p.suffix.lower() == ".zip":
                    zips.append(p)
                elif p.is_file() and p.suffix.lower() in (".csv", ".txt", ".xlsx", ".md", ".json") \
                        and p.stat().st_size < META_CAP:
                    others.append(p)
    zips = sorted(set(zips))
    for p in zips:
        with zipfile.ZipFile(p) as z:
            for label, info, zf in iter_zip_members(z, p.name):
                base = Path(info.filename).name
                inventory.append(dict(site=site, archive=str(p), member=label, size=info.file_size))
                if zf is None or info.file_size > META_CAP:
                    continue
                low = base.lower()
                is_bif = "_BIF_" in base.upper() or low.startswith("bif") or "_bif." in low
                if not is_bif and DATA_MEMBER.search(base):
                    continue
                if not (low.endswith((".csv", ".txt", ".xlsx", ".md", ".json")) or "readme" in low):
                    continue
                raw = zf.read(info)
                note_member(site, label, base, raw, hits, locs, copy_dir)
    for p in sorted(set(others)):
        inventory.append(dict(site=site, archive="", member=str(p), size=p.stat().st_size))
        if DATA_MEMBER.search(p.name) and "_BIF_" not in p.name.upper():
            continue
        note_member(site, str(p), p.name, p.read_bytes(), hits, locs, copy_dir)


KEEP_COPY = re.compile(r"BADM|_BIF_|README|soil", re.I)
WHOLE_CAP = 400


def note_member(site, label, base, raw, hits, locs, copy_dir=None):
    """Scan one metadata member. A file or sheet whose name mentions soil is listed in full (up to WHOLE_CAP rows).
    BADM / BIF / README / soil members are also copied unchanged to copy_dir/<site>/ for later reading."""
    low = base.lower()
    if copy_dir is not None and KEEP_COPY.search(base) and "VARINFO" not in base.upper():
        d = Path(copy_dir) / site
        d.mkdir(parents=True, exist_ok=True)
        (d / base).write_bytes(raw)
    whole = soil_hit(base)
    if low.endswith(".xlsx"):
        try:
            n = 0
            for sheet, cells in xlsx_rows(raw):
                line = " | ".join(c for c in cells if c)
                if whole or soil_hit(sheet) or soil_hit(line) or any(c.upper().startswith("GRP_SOIL") for c in cells):
                    hits.append(dict(site=site, source="JAPANFLUX_XLSX", file=label.split("!")[0], member=label,
                                     where=sheet, group="", key="", value=short(line)))
                    n += 1
                    if n >= WHOLE_CAP:
                        break
        except Exception as exc:
            hits.append(dict(site=site, source="JAPANFLUX_XLSX", file=label.split("!")[0], member=label,
                             where="READ_ERROR", group="", key="", value=short(exc)))
        return
    text = raw.decode("utf-8-sig", errors="replace")
    if "_BIF_" in base.upper() and "VARINFO" not in base.upper():
        scan_bif(site, text, label, hits, locs)
        return
    n = 0
    for i, line in enumerate(text.splitlines(), 1):
        if whole or soil_hit(line):
            src = "JAPANFLUX_BIFVARINFO" if "VARINFO" in base.upper() else "JAPANFLUX_TEXT"
            hits.append(dict(site=site, source=src, file=label.split("!")[0], member=label, where=f"line {i}",
                             group="", key="", value=short(line)))
            n += 1
            if n >= (WHOLE_CAP if whole else 40):
                break


# ------------------------------------------------------------------ 3. current surfaces
def nml_fsurdat(lnd_in):
    m = re.search(r"^\s*fsurdat\s*=\s*['\"]([^'\"]+)['\"]", lnd_in.read_text(errors="replace"), re.M)
    return m.group(1) if m else None


def find_surfaces(site, cases_root, home, sites_root):
    found = []
    if cases_root.is_dir():
        for case in sorted(cases_root.iterdir()):
            if site in case.name and (case / "CaseDocs" / "lnd_in").is_file():
                f = nml_fsurdat(case / "CaseDocs" / "lnd_in")
                if f:
                    found.append((Path(f), "CASE:" + case.name))
    for pat in ("ozflux_nc_stage02_*", "ozflux_nc_stage03_*", "ozflux_stage16_reference_*"):
        for d in sorted(home.glob(pat)):
            if d.is_dir() and not d.is_symlink():
                for p in sorted(d.rglob("surfdata*.nc")):
                    if site in p.name or site in str(p.parent.name):
                        found.append((p, "HOME:" + d.name))
    base = sites_root / site
    if base.is_dir():
        for root, dirs, files in os.walk(base):
            dirs[:] = [x for x in dirs if not x.lower().startswith(("forcing", "raw", "packages", "datm"))]
            for fn in files:
                if fn.startswith("surfdata") and fn.endswith(".nc"):
                    found.append((Path(root) / fn, "SITE_FOLDER"))
    seen, out = set(), []
    for p, how in found:
        k = str(p)
        if p.is_file() and k not in seen:
            seen.add(k)
            out.append((p, how))
        elif not p.is_file() and ("MISSING", k) not in seen:
            seen.add(("MISSING", k))
            out.append((p, how + ":MISSING"))
    return out


def read_surface(path, lat, lon):
    import numpy as np
    from netCDF4 import Dataset
    with Dataset(str(path)) as ds:
        def grab(name):
            if name not in ds.variables:
                return None
            a = np.ma.filled(np.ma.asarray(ds.variables[name][:], dtype=float), np.nan)
            if a.ndim == 3 and a.shape[1] * a.shape[2] > 1:
                la = np.asarray(ds.variables["LATIXY"][:], float)
                lo = np.asarray(ds.variables["LONGXY"][:], float)
                d = (la - lat) ** 2 + (((lo - (lon % 360)) + 180) % 360 - 180) ** 2
                i, k = np.unravel_index(np.argmin(d), d.shape)
                return a[:, i, k]
            return a.reshape(a.shape[0], -1)[:, 0] if a.ndim > 1 else a
        sand, clay, org = grab("PCT_SAND"), grab("PCT_CLAY"), grab("ORGANIC")
        la = grab("LATIXY")
        lo = grab("LONGXY")
    return sand, clay, org, (None if la is None else float(np.ravel(la)[0])), \
        (None if lo is None else float(np.ravel(lo)[0]))


# ------------------------------------------------------------------ driver
def write_tsv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def run(a):
    out = Path(a.out_dir) if a.out_dir else Path.home() / f"ozjp_soil_stage02_{utc()}"
    out.mkdir(parents=True, exist_ok=False)
    coords = {}
    if a.coords and Path(a.coords).is_file():
        for r in csv.DictReader(open(a.coords, encoding="utf-8")):
            if r.get("lat") and r.get("lon"):
                coords[r["site"]] = (float(r["lat"]), float(r["lon"]))
    hits, locs, inventory, surf_rows, summary = [], [], [], [], {"generated_utc": utc(), "sites": {}}
    print("== 1. OzFlux L6 global attributes", flush=True)
    l6 = {}
    for site, files in OZ_L6.items():
        try:
            l6[site] = ozflux_attrs(site, files, a.sites_root, hits)
        except Exception as exc:
            l6[site] = {"status": "READ_ERROR", "error": short(exc)}
        for fn, d in l6[site].items() if isinstance(l6[site], dict) and "status" not in l6[site] else []:
            print(f"  {site} {fn}: {d['status']} attrs={d.get('n_attrs')} lat/lon={d.get('lat_lon_attr')}", flush=True)
    (out / "ozflux_L6_global_attributes.json").write_text(json.dumps(l6, indent=1, ensure_ascii=False) + "\n")
    print("== 2. JapanFlux source metadata", flush=True)
    for site in JP_SITES:
        n0 = len(hits)
        try:
            japanflux(site, a.sites_root, hits, locs, inventory, out / "source_metadata_members")
            st = "OK"
        except Exception as exc:
            st = "READ_ERROR: " + short(exc, 200)
        n_arch = len({r["archive"] for r in inventory if r["site"] == site})
        print(f"  {site}: {st} | archives {n_arch} | members {sum(r['site'] == site for r in inventory)} | "
              f"soil/site hits {len(hits) - n0}", flush=True)
        summary["sites"].setdefault(site, {})["japanflux_scan"] = st
    print("== 3. Current surface soil", flush=True)
    for site in list(OZ_L6) + list(JP_SITES):
        lat, lon = coords.get(site, (None, None))
        js = [l for l in locs if l["site"] == site]
        jlat = next((l["value"] for l in js if l["key"] == "LOCATION_LAT"), None)
        jlon = next((l["value"] for l in js if l["key"] == "LOCATION_LONG"), None)
        if lat is None and jlat and jlon:
            try:
                lat, lon = float(jlat), float(jlon)
            except ValueError:
                pass
        surfs = find_surfaces(site, a.cases_root, Path.home(), a.sites_root)
        summary["sites"].setdefault(site, {})["surfaces"] = []
        for p, how in surfs:
            if how.endswith(":MISSING"):
                print(f"  {site} {how} {p}", flush=True)
                summary["sites"][site]["surfaces"].append({"path": str(p), "found_by": how})
                continue
            try:
                sand, clay, org, la, lo = read_surface(p, lat if lat is not None else 0.0,
                                                       lon if lon is not None else 0.0)
                digest = sha256(p)
                for j in range(len(sand) if sand is not None else 0):
                    surf_rows.append(dict(site=site, found_by=how, path=str(p), sha256=digest, surf_lat=la,
                                          surf_lon=lo, level=j + 1, PCT_SAND=round(float(sand[j]), 3),
                                          PCT_CLAY=round(float(clay[j]), 3),
                                          ORGANIC=None if org is None else round(float(org[j]), 4)))
                top = lambda v: round(float(sum(v[:5]) / 5), 1) if v is not None and len(v) >= 5 else None
                line = (f"  {site} {how} {p.name} sha {digest[:12]} | top30 sand/clay {top(sand)}/{top(clay)} | "
                        f"sand {[round(float(x)) for x in sand[:10]]} clay {[round(float(x)) for x in clay[:10]]} "
                        f"ORG {[round(float(x), 1) for x in org[:10]] if org is not None else None}")
                print(line, flush=True)
                summary["sites"][site]["surfaces"].append({"path": str(p), "found_by": how, "sha256": digest,
                                                           "top30_sand": top(sand), "top30_clay": top(clay)})
            except Exception as exc:
                print(f"  {site} {how} {p}: READ_ERROR {short(exc, 160)}", flush=True)
        if not surfs:
            print(f"  {site}: no surface file found", flush=True)
    write_tsv(out / "source_soil_metadata_hits.tsv", hits,
              ["site", "source", "file", "member", "where", "group", "key", "value"])
    write_tsv(out / "japanflux_bif_location.tsv", locs, ["site", "member", "group_id", "key", "value", "line"])
    write_tsv(out / "japanflux_package_members.tsv", inventory, ["site", "archive", "member", "size"])
    write_tsv(out / "current_surface_soil_layers.tsv", surf_rows,
              ["site", "found_by", "path", "sha256", "surf_lat", "surf_lon", "level", "PCT_SAND", "PCT_CLAY",
               "ORGANIC"])
    summary.update(n_hits=len(hits), n_location_rows=len(locs), n_surface_rows=len(surf_rows), out_dir=str(out))
    (out / "stage02_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print("== SOIL / SITE METADATA HITS (all)", flush=True)
    for h in hits:
        print(f"  {h['site']} | {h['source']} | {Path(h['member'] or h['file']).name} | {h['where']} | "
              f"{h['group']} {h['key']} = {h['value']}", flush=True)
    print("== JAPANFLUX BIF LOCATION", flush=True)
    for l in locs:
        print(f"  {l['site']} #{l['group_id']} {l['key']} = {l['value']}", flush=True)
    print(f"STAGE02 DONE (read only) | {out}", flush=True)
    return 0


def self_test():
    import tempfile
    import numpy as np
    from netCDF4 import Dataset
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        sroot = d / "sites"
        raw = sroot / "AU-ASM" / "forcing" / "raw"
        raw.mkdir(parents=True)
        with Dataset(str(raw / OZ_L6["AU-ASM"][0]), "w") as ds:
            ds.setncattr("soil", "red kandosol, sandy loam")
            ds.setncattr("latitude", "-22.2828")
            ds.setncattr("vegetation1", "Acacia aneura")
        hits = []
        r = ozflux_attrs("AU-ASM", OZ_L6["AU-ASM"], sroot, hits)
        assert r[OZ_L6["AU-ASM"][0]]["status"] == "OK" and r[OZ_L6["AU-ASM"][1]]["status"] == "MISSING"
        assert [h["key"] for h in hits] == ["soil"], hits
        # nested JapanFlux package
        bif = ("SITE_ID,GROUP_ID,VARIABLE_GROUP,VARIABLE,DATAVALUE\n"
               "JP-Tak,1,GRP_LOCATION,LOCATION_LAT,36.14\nJP-Tak,1,GRP_LOCATION,LOCATION_LONG,137.42\n"
               "JP-Tak,2,GRP_SOIL_TEX,SOIL_TEX_SAND,40\nJP-Tak,2,GRP_SOIL_TEX,SOIL_TEX_PROFILE_MIN,0\n"
               "JP-Tak,3,GRP_HEADER,SITE_NAME,Takayama\n"
               "JP-Tak,4,GRP_REFERENCE_PAPER,REFERENCE_PAPER,\"Ohtsuka, soil respiration on an Andosol\"\n")
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w") as z:
            z.writestr("JPF_JP-Tak_FLUXNET_BIF_2000-2021_v1.csv", bif)
            z.writestr("README.txt", "Soil: volcanic ash (Andosol)\nTimes are local standard time\n")
            z.writestr("JPF_JP-Tak_FLUXNET_FLUXMET_HH_2000-2021_v1.csv", "TIMESTAMP_START,TA_F\n" + "x,1\n" * 10)
        pk = sroot / "JP-Tak" / "forcing" / "packages"
        pk.mkdir(parents=True)
        with zipfile.ZipFile(pk / "JPF_JP-Tak.zip", "w") as z:
            z.writestr("JPF_JP-Tak.zip", inner.getvalue())
            z.writestr("DATA/BADM/FLX_JP-Tak_SOIL_profile.csv", "depth,a,b,c\n0-10,45,30,25\n10-30,40,30,30\n")
        hits, locs, inv = [], [], []
        japanflux("JP-Tak", sroot, hits, locs, inv, d / "copies")
        assert sorted(p.name for p in (d / "copies" / "JP-Tak").iterdir()) == [
            "FLX_JP-Tak_SOIL_profile.csv", "JPF_JP-Tak_FLUXNET_BIF_2000-2021_v1.csv", "README.txt"]
        assert sum(h["member"].endswith("SOIL_profile.csv") for h in hits) == 3     # whole file, numbers included
        keys = sorted((h["source"], h["key"] or h["where"]) for h in hits)
        assert ("JAPANFLUX_BIF", "SOIL_TEX_SAND") in keys and ("JAPANFLUX_BIF", "SOIL_TEX_PROFILE_MIN") in keys, keys
        assert ("JAPANFLUX_BIF", "REFERENCE_PAPER") in keys, keys          # value mentions a soil order
        assert ("JAPANFLUX_TEXT", "line 1") in keys and not any("FLUXMET" in h["member"] for h in hits), keys
        assert not any(h["key"] == "SITE_NAME" for h in hits)
        assert {(l["key"], l["value"]) for l in locs} == {("LOCATION_LAT", "36.14"), ("LOCATION_LONG", "137.42")}
        assert len(inv) == 4
        # xlsx fallback reader on a minimal workbook
        xb = io.BytesIO()
        with zipfile.ZipFile(xb, "w") as z:
            z.writestr("xl/sharedStrings.xml", "<sst><si><t>VARIABLE</t></si><si><t>SOIL_CLASSIFICATION</t></si>"
                                               "<si><t>Andosol</t></si></sst>")
            z.writestr("xl/worksheets/sheet1.xml", '<worksheet><sheetData><row r="1"><c t="s"><v>1</v></c>'
                                                   '<c t="s"><v>2</v></c></row></sheetData></worksheet>')
        rows = list(xlsx_rows(xb.getvalue()))
        assert any("SOIL_CLASSIFICATION" in " ".join(c) for _, c in rows), rows
        # surface reader + finder
        sp = d / "home" / "ozflux_nc_stage03_X"
        sp.mkdir(parents=True)
        f = sp / "surfdata_AU-ASM_test.nc"
        with Dataset(str(f), "w") as ds:
            ds.createDimension("nlevsoi", 10); ds.createDimension("lsmlat", 1); ds.createDimension("lsmlon", 1)
            for n, v in (("PCT_SAND", 90.0), ("PCT_CLAY", 6.0), ("ORGANIC", 3.0)):
                x = ds.createVariable(n, "f8", ("nlevsoi", "lsmlat", "lsmlon")); x[:] = v
            for n, v in (("LATIXY", -22.28), ("LONGXY", 133.25)):
                x = ds.createVariable(n, "f8", ("lsmlat", "lsmlon")); x[:] = v
        found = find_surfaces("AU-ASM", d / "nocases", d / "home", sroot)
        assert [h for _, h in found] == ["HOME:ozflux_nc_stage03_X"], found
        sand, clay, org, la, lo = read_surface(found[0][0], -22.28, 133.25)
        assert len(sand) == 10 and float(sand[0]) == 90.0 and float(org[9]) == 3.0 and la == -22.28
    assert soil_hit("黒ボク土") and soil_hit("Red Kandosol") and not soil_hit("canopy height")
    assert not soil_hit("SWC_1_1_1: soil water content at 5 cm") and not soil_hit("TS_2: Soil temperature")
    assert soil_hit("soil temperature probes in a sandy loam") and soil_hit("SOIL_TEX_CLAY")
    print("STAGE02 SELF-TEST PASS (L6 attributes, nested ZIP BIF/README scan skipping data members, BIF location, "
          "xlsx reader, surface finder/reader; no IRIDIS files)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--sites-root", type=Path, default=SITES_ROOT)
    ap.add_argument("--cases-root", type=Path, default=CASES_ROOT)
    ap.add_argument("--coords", help="site coordinate CSV (data/OZ_JP_20_SITE_COORDINATES_*.csv)")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
