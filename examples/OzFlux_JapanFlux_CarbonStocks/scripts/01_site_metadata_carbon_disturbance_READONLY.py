#!/usr/bin/env python3
"""Stage01 (IRIDIS6, read only): carbon-stock, stand and disturbance / management metadata already inside our own
source files for the 20 OzFlux / JapanFlux sites.

1. JapanFlux packages (nested ZIPs under sites/MY_EC_SITE/<site>/forcing/{packages,raw}). Every BIF
   (BADM Interchange Format) CSV is read. Variable groups for biomass, litter, soil chemistry, disturbance and
   management (GRP_DM_*), dominant disturbance, site description, stand / trees / species, reference papers and
   UTC offset are kept, one line per group instance.
   - LAI and HEIGHTC are summarised per site (number of instances, value range, dates).
   - Every group name found is counted, so nothing is missed.
   - Standalone BADM workbooks are read in full: Disturbance_and_Management, VegCover and Site_General_Info.
2. OzFlux L6 global attributes. All names are listed; values are printed for names or values that mention
   vegetation, canopy, height, age, fire, cyclone, clearing, grazing, logging, dieback, disturbance or history.

Nothing is modified. Output: a new folder $HOME/ozjp_carbon_stage01_<UTC> with bif_groups.tsv, badm_xlsx_rows.tsv
and stage01_carbon.json. The console is capped at --max-lines group lines; the TSVs hold everything.

Usage (login node, conda env clm_fates_env):
  python3 -B 01_site_metadata_carbon_disturbance_READONLY.py --self-test
  python3 -B 01_site_metadata_carbon_disturbance_READONLY.py [--sites JP-Tgf,JP-Tom] [--max-lines 220]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES")
SITES_ROOT = BASE / "sites" / "MY_EC_SITE"
OZ_L6 = {"AU-ASM": ["AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc",
                    "AliceSpringsMulga2_20240821T0700_to_20260423T0000_L6.nc"],
         "AU-Cow": ["CowBay_20090101T0900_to_20260423T0000_L6.nc"], "AU-Cpr": ["Calperum_L6.nc"],
         "AU-DaS": ["DalyUncleared_20080101T0000_to_20260423T0000_L6.nc"], "AU-Dry": ["DryRiver_L6.nc"],
         "AU-Gin": ["Gingin_L6.nc"], "AU-How": ["HowardSprings_L6.nc"], "AU-Stp": ["SturtPlains_L6.nc"],
         "AU-Tum": ["Tumbarumba1_L6.nc"]}
JP_SITES = ("JP-Api", "JP-Fhk", "JP-Fjy", "JP-Khw", "JP-Spp", "JP-Tak", "JP-Tef", "JP-Tgf", "JP-Tmd", "JP-Tom",
            "JP-Yms")
KEEP_GROUP = re.compile(r"^GRP_(AG_|BG_|BIOMASS|ROOT|LITTER|LIT_|WD_|CWD|SOIL_CHEM|SOIL_STOCK|SOIL_DEPTH|DM_|"
                        r"DOM_DIST|SITE_DESC|SITE_CHAR|STAND|TREE|BASAL|SPP|SPECIES|VEG|ALLOM|REFERENCE_PAPER|"
                        r"UTC_OFFSET|IGBP|CLIM_AVG|NEE|GPP|RECO|FLUX_SUM|BIOMASS)", re.I)
SUMMARY_GROUP = re.compile(r"^GRP_(LAI|HEIGHTC)", re.I)
BADM_SHEETS = re.compile(r"Disturbance|Management|VegCover|Site_General|Biomass|Allometr|Litter|Species", re.I)
L6_HIT = re.compile(r"veget|canopy|height|age\b|stand|fire|burn|cyclone|clear|graz|log(ging|ged)|thin|dieback|"
                    r"disturb|history|biomass|basal|species|land.?use|manage", re.I)
DATA_MEMBER = re.compile(r"_(HH|HR|DD|WW|MM|YY)_|FLUXMET|FLUXNET_FULLSET|SUBSET|ERA5|AUXMETEO|AUXNEE", re.I)
NESTED_CAP = 1024 ** 3
META_CAP = 5 * 1024 * 1024


def utc():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def short(v, n=400):
    s = str(v).replace("\t", " ").replace("\r", " ").replace("\n", " | ")
    return s if len(s) <= n else s[:n] + " ..."


# ---------------------------------------------------------------- JapanFlux (readers as in the soil Stage02)
def iter_zip_members(zf, label, depth=0):
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
    except Exception:
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


def parse_bif(site, text, member):
    """Group instances {(group, group_id): OrderedDict(variable -> value)} of one BIF CSV, plus group counts."""
    inst, counts = OrderedDict(), Counter()
    rdr = csv.reader(io.StringIO(text))
    for rec in rdr:
        if len(rec) < 5:
            continue
        sid, gid, group, key = (s.strip() for s in rec[:4])
        val = ",".join(rec[4:]).strip()
        if not group.upper().startswith("GRP_") or (sid and sid != site):
            continue
        k = (group.upper(), gid)
        if k not in inst:
            counts[group.upper()] += 1
            inst[k] = OrderedDict()
        if key in inst[k]:
            inst[k][key] += " ; " + val
        else:
            inst[k][key] = val
    return inst, counts


def summarise_numeric(instances, group):
    vals, dates = [], []
    for (g, _), d in instances.items():
        if g != group:
            continue
        for k, v in d.items():
            ku = k.upper()
            if (ku == group[4:] or ku.startswith(group[4:] + "_")) and not re.search(r"DATE|NUMBER|COMMENT", ku):
                try:
                    vals.append(float(v))
                except ValueError:
                    pass
            if k.upper().endswith("_DATE") or k.upper().endswith("_DATE_START"):
                dates.append(v[:8])
    return {"n": sum(1 for (g, _) in instances if g == group), "min": min(vals) if vals else None,
            "max": max(vals) if vals else None, "first_date": min(dates) if dates else None,
            "last_date": max(dates) if dates else None}


def japanflux_site(site, sites_root):
    roots = [sites_root / site / "forcing" / "packages", sites_root / site / "forcing" / "raw", sites_root / site]
    zips = sorted({p for r in roots if r.is_dir() for p in r.iterdir() if p.is_file() and p.suffix.lower() == ".zip"})
    loose = sorted({p for r in roots if r.is_dir() for p in r.iterdir()
                    if p.is_file() and p.suffix.lower() in (".csv", ".xlsx") and p.stat().st_size < META_CAP})
    out = {"bif": [], "xlsx": [], "members_read": []}

    def handle(label, base, raw):
        up = base.upper()
        if "_BIF_" in up and "VARINFO" not in up and base.lower().endswith(".csv"):
            inst, counts = parse_bif(site, raw.decode("utf-8-sig", errors="replace"), label)
            out["bif"].append({"member": label, "instances": inst, "counts": counts})
            out["members_read"].append(label)
        elif base.lower().endswith(".xlsx") and "BADM" in up and BADM_SHEETS.search(base):
            rows = [(sh, cells) for sh, cells in xlsx_rows(raw)]
            out["xlsx"].append({"member": label, "rows": rows})
            out["members_read"].append(label)

    for p in zips:
        with zipfile.ZipFile(p) as z:
            for label, info, zf in iter_zip_members(z, p.name):
                base = Path(info.filename).name
                if zf is None or info.file_size > META_CAP or (DATA_MEMBER.search(base) and "_BIF_" not in base.upper()):
                    continue
                if base.lower().endswith((".csv", ".xlsx")):
                    handle(label, base, zf.read(info))
    for p in loose:
        handle(str(p), p.name, p.read_bytes())
    return out


def dedupe_bif(bifs):
    """Merge the BIF files of one site; identical group instances (same group, id and content) are kept once."""
    merged, seen = OrderedDict(), set()
    for b in bifs:
        for k, d in b["instances"].items():
            sig = (k, tuple(d.items()))
            if sig in seen:
                continue
            seen.add(sig)
            key = k if k not in merged else (k[0], f"{k[1]}@{b['member'].split('!')[-1]}")
            merged[key] = d
    return merged


# ---------------------------------------------------------------- OzFlux
def l6_attrs(site, files, sites_root):
    from netCDF4 import Dataset
    out = {}
    for fn in files:
        p = sites_root / site / "forcing" / "raw" / fn
        if not p.is_file():
            out[fn] = {"status": "MISSING"}
            continue
        with Dataset(str(p)) as ds:
            attrs = {k: short(ds.getncattr(k), 3000) for k in ds.ncattrs()}
        out[fn] = {"status": "OK", "names": sorted(attrs),
                   "hits": {k: v for k, v in attrs.items() if L6_HIT.search(k) or L6_HIT.search(v)}}
    return out


# ---------------------------------------------------------------- driver
def run(a):
    out = Path(a.out_dir) if a.out_dir else Path.home() / f"ozjp_carbon_stage01_{utc()}"
    out.mkdir(parents=True, exist_ok=False)
    sites = a.sites.split(",") if a.sites else list(OZ_L6) + list(JP_SITES)
    res, bif_rows, xl_rows, printed = {"generated_utc": utc(), "sites": {}}, [], [], 0
    sites_root = Path(a.sites_root)
    for site in sites:
        if site in OZ_L6:
            r = l6_attrs(site, OZ_L6[site], sites_root)
            res["sites"][site] = {"l6": r}
            print(f"== {site} (OzFlux L6 global attributes)")
            for fn, d in r.items():
                if d["status"] != "OK":
                    print(f"  {fn}: {d['status']}")
                    continue
                print(f"  {fn}: {len(d['names'])} attrs: {', '.join(d['names'])[:900]}")
                for k, v in d["hits"].items():
                    print(f"    {k}: {short(v, 260)}")
            continue
        jf = japanflux_site(site, sites_root)
        inst = dedupe_bif(jf["bif"])
        counts = Counter()
        for b in jf["bif"]:
            counts.update(b["counts"])
        summ = {g: summarise_numeric(inst, g) for g in ("GRP_LAI", "GRP_HEIGHTC") if any(k[0] == g for k in inst)}
        res["sites"][site] = {"members_read": jf["members_read"], "group_counts": dict(counts), "summaries": summ}
        print(f"== {site} (JapanFlux: {len(jf['bif'])} BIF, {len(jf['xlsx'])} BADM xlsx)")
        print(f"  groups: {', '.join(f'{g[4:]}x{n}' for g, n in sorted(counts.items()))[:1200]}")
        for g, s in summ.items():
            print(f"  {g}: {s}")
        for (g, gid), d in inst.items():
            row = {"site": site, "group": g, "group_id": gid, "values": json.dumps(d, ensure_ascii=False)}
            bif_rows.append(row)
            if KEEP_GROUP.match(g) and not SUMMARY_GROUP.match(g):
                if printed < a.max_lines:
                    body = "; ".join(f"{k}={v}" for k, v in d.items() if v)
                    print(f"  {g[4:]}#{gid}: {short(body, 230)}")
                printed += 1
        for x in jf["xlsx"]:
            sheet_rows = [(sh, cells) for sh, cells in x["rows"]]
            for sh, cells in sheet_rows:
                xl_rows.append({"site": site, "member": x["member"], "sheet": sh, "cells": " | ".join(cells)})
            name = x["member"].split("!")[-1]
            print(f"  xlsx {name}: {len(sheet_rows)} rows")
            for sh, cells in sheet_rows[:a.xlsx_rows]:
                if printed < a.max_lines:
                    print(f"    {short(' | '.join(c for c in cells if c), 230)}")
                printed += 1
    if printed > a.max_lines:
        print(f"[{printed - a.max_lines} more group lines in the TSVs; console cap --max-lines {a.max_lines}]")
    with open(out / "bif_groups.tsv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=("site", "group", "group_id", "values"), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(bif_rows)
    with open(out / "badm_xlsx_rows.tsv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=("site", "member", "sheet", "cells"), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(xl_rows)
    (out / "stage01_carbon.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False) + "\n")
    print(f"STAGE01 CARBON DONE (read only) | {out} | {len(bif_rows)} BIF group instances, {len(xl_rows)} xlsx rows")
    return 0


def self_test():
    import tempfile
    bif = ("SITE_ID,GROUP_ID,VARIABLE_GROUP,VARIABLE,DATAVALUE\n"
           "JP-Xyz,1,GRP_DM_HARVEST,DM_HARVEST,Clear-cut\n"
           "JP-Xyz,1,GRP_DM_HARVEST,DM_DATE,20030115\n"
           "JP-Xyz,1,GRP_DM_HARVEST,DM_COMMENT,\"all trees, incl. Sasa\"\n"
           "JP-Xyz,2,GRP_LAI,LAI_TOT,3.5\nJP-Xyz,2,GRP_LAI,LAI_DATE,20080701\n"
           "JP-Xyz,3,GRP_LAI,LAI_TOT,5.1\nJP-Xyz,3,GRP_LAI,LAI_DATE,20090801\n"
           "JP-Xyz,4,GRP_AG_BIOMASS_TREE,AG_BIOMASS_TREE,12.3\n"
           "JP-Xyz,5,GRP_INST,INST_MODEL,LI-7500\n"
           "JP-Other,6,GRP_DM_FIRE,DM_FIRE,x\n")
    inst, counts = parse_bif("JP-Xyz", bif, "m")
    assert counts == Counter({"GRP_DM_HARVEST": 1, "GRP_LAI": 2, "GRP_AG_BIOMASS_TREE": 1, "GRP_INST": 1}), counts
    assert inst[("GRP_DM_HARVEST", "1")]["DM_COMMENT"] == "all trees, incl. Sasa"
    assert inst[("GRP_DM_HARVEST", "1")]["DM_DATE"] == "20030115"
    s = summarise_numeric(inst, "GRP_LAI")
    assert s == {"n": 2, "min": 3.5, "max": 5.1, "first_date": "20080701", "last_date": "20090801"}, s
    assert KEEP_GROUP.match("GRP_DM_HARVEST") and KEEP_GROUP.match("GRP_AG_BIOMASS_TREE") and not KEEP_GROUP.match("GRP_INST")
    m = dedupe_bif([{"member": "a!x_BIF_1.csv", "instances": inst}, {"member": "b!y_BIF_2.csv", "instances": inst}])
    assert len(m) == len(inst)
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        site = d / "JP-Xyz" / "forcing" / "packages"
        site.mkdir(parents=True)
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w") as z:
            z.writestr("JPF_JP-Xyz_FLUXNET_BIF_2001-2023_v1.3_r1.csv", bif)
            z.writestr("JPF_JP-Xyz_FLUXNET_FLUXMET_HH_2001-2023.csv", "big data")
        with zipfile.ZipFile(site / "JPF_JP-Xyz.zip", "w") as z:
            z.writestr("JPF_JP-Xyz_FLUXNET_2001-2023_v1.3_r1.zip", inner.getvalue())
        jf = japanflux_site("JP-Xyz", d)
        assert len(jf["bif"]) == 1 and jf["members_read"][0].endswith("_BIF_2001-2023_v1.3_r1.csv")
        out = d / "out"
        rc = run(argparse.Namespace(out_dir=str(out), sites="JP-Xyz", sites_root=str(d), max_lines=50, xlsx_rows=10))
        assert rc == 0
        tsv = (out / "bif_groups.tsv").read_text()
        assert "GRP_DM_HARVEST" in tsv and "GRP_INST" in tsv
    print("STAGE01 CARBON SELF-TEST PASS (BIF grouping / site filter / LAI summary / keep filter / nested zip / "
          "dedupe / driver; no IRIDIS)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--sites")
    ap.add_argument("--sites-root", default=str(SITES_ROOT))
    ap.add_argument("--max-lines", type=int, default=220)
    ap.add_argument("--xlsx-rows", type=int, default=40)
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    return self_test() if a.self_test else run(a)


if __name__ == "__main__":
    sys.exit(main())
