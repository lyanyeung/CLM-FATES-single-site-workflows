#!/usr/bin/env python3
"""Stage01 (IRIDIS6, read only): the surface-dataset fields besides texture and PFT that must be fixed before the
spin-up surface is built, at the 20 OzFlux / JapanFlux towers, and the model settings that decide whether they
are used.

1. Project global surface surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc (the source of every point subset here):
   nearest cell and 3x3 land cells around each tower. Fields:
   - zbedrock, ORGANIC (10 levels), FMAX, SOIL_COLOR, SLOPE, STD_ELEV;
   - landunit shares (NATVEG, CROP, LAKE, WETLAND, GLACIER, URBAN);
   - PCT_SAND / PCT_CLAY level 1 for context.
2. Every existing point surface of these sites:
   - from cases/*/CaseDocs/lnd_in;
   - from $HOME/ozflux_nc_stage02_*, ozflux_nc_stage03_*, ozflux_stage16_reference_*;
   - from the site folder.
   Same fields as 1.
3. Template NORMAL400 case:
   - lnd_in settings that decide how these fields act (use_bedrock, soil_layerstruct_predefined,
     lower_boundary_condition, soilwater_movement_method, organic_frac_squared, use_fates_planthydro, paramfile,
     fates_paramfile);
   - the CLM parameter-file scalars organic_max, zbedrock, zbedrock_sf, om_frac_sf;
   - the FATES rooting-depth parameters;
   - the model layer depths ZSOI / DZSOI from one history file.

Nothing is modified. Output: a new folder $HOME/ozjp_surface_stage01_<UTC> with stage01_surface.json and
stage01_surface_fields.tsv.

Usage (login node, conda env clm_fates_env):
  python3 -B 01_surface_fields_at_towers_READONLY.py --self-test
  python3 -B 01_surface_fields_at_towers_READONLY.py --coords OZ_JP_20_SITE_COORDINATES_20261103.csv
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES")
CASES = BASE / "cases"
SITES = BASE / "sites" / "MY_EC_SITE"
GLOBAL_NAME = "surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc"
TEMPLATE = "AT-Neu_B03_FIXNC_NORMAL400"
SCALARS = ("zbedrock", "FMAX", "SOIL_COLOR", "SLOPE", "STD_ELEV", "PCT_NATVEG", "PCT_CROP", "PCT_LAKE",
           "PCT_WETLAND", "PCT_GLACIER", "LANDFRAC_PFT", "PFTDATA_MASK", "peatf", "abm", "gdp")
LEVELS = ("ORGANIC", "PCT_SAND", "PCT_CLAY")
LND_KEYS = ("fsurdat", "use_bedrock", "soil_layerstruct_predefined", "soil_layerstruct_userdefined",
            "lower_boundary_condition", "soilwater_movement_method", "organic_frac_squared", "use_fates_planthydro",
            "baseflow_scalar", "use_hillslope", "h2osfcflag", "paramfile", "fates_paramfile", "rooting_profile_method_water",
            "rooting_profile_method_carbon")
CLM_PARAMS = ("organic_max", "zbedrock", "zbedrock_sf", "om_frac_sf", "pc", "mu")
ROOT_KEY = re.compile(r"zroot|rootprof|root_?prof|rootdepth|root_depth|fates_roots?_", re.I)
TSV_FIELDS = ("site", "kind", "source", "path", "lat", "lon", "dist_deg", "zbedrock", "zbedrock_3x3", "ORGANIC",
              "ORGANIC_3x3_lev1", "FMAX", "FMAX_3x3", "SOIL_COLOR", "SOIL_COLOR_3x3", "SLOPE", "STD_ELEV",
              "PCT_NATVEG", "PCT_CROP", "PCT_LAKE", "PCT_WETLAND", "PCT_GLACIER", "PCT_URBAN", "PCT_SAND1", "PCT_CLAY1")


def utc():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256(p, cap=2 * 1024 ** 3):
    p = Path(p)
    if p.stat().st_size > cap:
        return "SKIPPED_LARGE"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def r3(v):
    try:
        return None if v is None or v != v else round(float(v), 3)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- surfaces
def nearest(la, lo, lat, lon, land=None):
    """(i, k, distance in degrees) of the nearest cell, optionally restricted to land cells."""
    import numpy as np
    d = (la - lat) ** 2 + ((((lo - (lon % 360)) + 180) % 360) - 180) ** 2
    if land is not None:
        d = np.where(land, d, np.inf)
    i, k = np.unravel_index(np.argmin(d), d.shape)
    return int(i), int(k), float(np.sqrt(d[i, k]))


def surface_values(ds, lat, lon):
    """Field values at the nearest cell of a 2-D grid (or the single cell of a point file), plus the range over the
    3x3 land cells around it."""
    import numpy as np
    v = ds.variables

    def arr(name):
        return None if name not in v else np.ma.filled(np.ma.asarray(v[name][:], dtype=float), np.nan)

    la, lo = arr("LATIXY"), arr("LONGXY")
    grid = la is not None and la.ndim == 2 and la.size > 1
    out = {}
    if grid:
        land = arr("LANDFRAC_PFT")
        land = (land > 0) if land is not None else None
        i, k, dist = nearest(la, lo, lat, lon)
        il, kl, distl = nearest(la, lo, lat, lon, land) if land is not None else (i, k, dist)
        out.update(cell=[i, k], cell_lat=float(la[i, k]), cell_lon=float(lo[i, k]), dist_deg=round(dist, 3),
                   nearest_is_land=bool(land[i, k]) if land is not None else None,
                   nearest_land_cell=[il, kl], nearest_land_dist_deg=round(distl, 3))
        ny, nx = la.shape
        nb = [(a, b % nx) for a in range(max(i - 1, 0), min(i + 2, ny)) for b in (k - 1, k, k + 1)]
        nb = [(a, b) for a, b in nb if land is None or land[a, b]]
    else:
        i = k = 0
        out.update(cell=None, cell_lat=None if la is None else float(np.ravel(la)[0]),
                   cell_lon=None if lo is None else float(np.ravel(lo)[0]), dist_deg=None)
        nb = []

    def at(a, ii, kk):
        if a is None:
            return None
        if a.ndim == 0:
            return float(a)
        if grid:
            return a[..., ii, kk] if a.ndim >= 2 else None
        return a.reshape(a.shape[0], -1)[:, 0] if a.ndim > 1 else a

    for name in SCALARS:
        a = arr(name)
        x = at(a, i, k)
        out[name] = None if x is None else r3(np.ravel(x)[0])
        if grid and a is not None and a.ndim == 2 and nb:
            vals = [a[p, q] for p, q in nb]
            out[name + "_3x3"] = [r3(min(vals)), r3(max(vals))]
    u = arr("PCT_URBAN")
    x = at(u, i, k)
    out["PCT_URBAN"] = None if x is None else r3(np.nansum(np.ravel(x)))
    for name in LEVELS:
        a = arr(name)
        x = at(a, i, k)
        out[name] = None if x is None else [r3(t) for t in np.ravel(x)]
        if grid and a is not None and a.ndim == 3 and nb:
            vals = [a[0, p, q] for p, q in nb]
            out[name + "_3x3_lev1"] = [r3(min(vals)), r3(max(vals))]
    return out


def find_global(din_root, override=None):
    if override:
        return Path(override)
    for root, dirs, files in os.walk(Path(din_root) / "lnd" / "clm2"):
        dirs[:] = [d for d in dirs if not d.startswith(("ndep", "paramdata", "firedata", "lai_streams", "urbandata"))]
        if GLOBAL_NAME in files:
            return Path(root) / GLOBAL_NAME
    return None


def nml_value(text, key):
    m = re.search(rf"^\s*{key}\s*=\s*(.+?)\s*$", text, re.M | re.I)
    return m.group(1).strip() if m else None


def find_point_surfaces(site, cases_root, home, sites_root):
    found = []
    if Path(cases_root).is_dir():
        for case in sorted(Path(cases_root).iterdir()):
            f = case / "CaseDocs" / "lnd_in"
            if site in case.name and f.is_file():
                v = nml_value(f.read_text(errors="replace"), "fsurdat")
                if v:
                    found.append((Path(v.strip("'\"")), "CASE:" + case.name))
    for pat in ("ozflux_nc_stage02_*", "ozflux_nc_stage03_*", "ozflux_stage16_reference_*"):
        for d in sorted(Path(home).glob(pat)):
            if d.is_dir() and not d.is_symlink():
                for p in sorted(d.rglob("surfdata*.nc")):
                    if site in p.name or site in p.parent.name:
                        found.append((p, "HOME:" + d.name))
    base = Path(sites_root) / site
    if base.is_dir():
        for root, dirs, files in os.walk(base):
            dirs[:] = [x for x in dirs if not x.lower().startswith(("forcing", "raw", "packages", "datm"))]
            for fn in files:
                if fn.startswith("surfdata") and fn.endswith(".nc"):
                    found.append((Path(root) / fn, "SITE_FOLDER"))
    seen, out = set(), []
    for p, how in found:
        if str(p) not in seen:
            seen.add(str(p))
            out.append((p, how))
    return out


# ---------------------------------------------------------------- model settings
def env_values(case):
    vals = {}
    for f in sorted(Path(case).glob("env_*.xml")):
        for m in re.finditer(r"<entry\s+id=\"([^\"]+)\"\s+value=\"([^\"]*)\"", f.read_text(errors="replace")):
            vals.setdefault(m.group(1), m.group(2))
    for _ in range(6):
        changed = False
        for k, v in vals.items():
            nv = re.sub(r"\$\{?([A-Z_][A-Z0-9_]*)\}?", lambda m: vals.get(m.group(1), m.group(0)), v)
            if nv != v:
                vals[k], changed = nv, True
        if not changed:
            break
    return vals


def clm_param_scalars(path):
    from netCDF4 import Dataset
    out = {}
    with Dataset(str(path)) as ds:
        for k in CLM_PARAMS:
            if k in ds.variables:
                a = ds.variables[k][:]
                out[k] = r3(a.ravel()[0]) if getattr(a, "size", 1) else None
    return out


def fates_root_params(path):
    p = Path(path)
    out = {}
    if p.suffix == ".json":
        P = json.loads(p.read_text())
        P = P.get("parameters", P)
        for k, v in P.items():
            if ROOT_KEY.search(k) or k == "fates_pftname":
                out[k] = v.get("data", v.get("value")) if isinstance(v, dict) else v
    else:
        from netCDF4 import Dataset, chartostring
        with Dataset(str(p)) as ds:
            for k, v in ds.variables.items():
                if k == "fates_pftname":
                    out[k] = [str(s).strip() for s in chartostring(v[:])]
                elif ROOT_KEY.search(k):
                    out[k] = [r3(x) for x in v[:].ravel().tolist()]
    return out


def layer_depths(dout):
    from netCDF4 import Dataset
    hist = sorted((Path(dout) / "lnd" / "hist").glob("*.clm2.h0*.nc")) if dout else []
    for f in hist[:3]:
        with Dataset(str(f)) as ds:
            if "ZSOI" in ds.variables:
                z = ds.variables["ZSOI"][:].reshape(ds.variables["ZSOI"].shape[0], -1)[:, 0]
                dz = ds.variables["DZSOI"][:].reshape(ds.variables["DZSOI"].shape[0], -1)[:, 0] \
                    if "DZSOI" in ds.variables else None
                out = {"file": f.name, "ZSOI_m": [r3(x) for x in z]}
                if dz is not None:
                    out["DZSOI_m"] = [r3(x) for x in dz]
                    out["bottom_m"] = [r3(sum(float(t) for t in dz[:j + 1])) for j in range(len(dz))]
                return out
    return {"file": None}


def model_settings(cases_root, template):
    case = Path(cases_root) / template
    res = {"template": template}
    lnd = case / "CaseDocs" / "lnd_in"
    if not lnd.is_file():
        return {**res, "error": "no CaseDocs/lnd_in"}
    text = lnd.read_text(errors="replace")
    res["lnd_in"] = {k: nml_value(text, k) for k in LND_KEYS}
    unl = case / "user_nl_clm"
    if unl.is_file():
        res["user_nl_clm_sets_use_bedrock"] = bool(re.search(r"^\s*use_bedrock\s*=", unl.read_text(), re.M | re.I))
    pf = (res["lnd_in"].get("paramfile") or "").strip("'\"")
    if pf and Path(pf).is_file():
        res["clm_params"] = {"file": pf, **clm_param_scalars(pf)}
    ff = (res["lnd_in"].get("fates_paramfile") or "").strip("'\"")
    if ff and Path(ff).is_file():
        res["fates_root_params"] = {"file": ff, **fates_root_params(ff)}
    e = env_values(case)
    res["din_loc_root"] = e.get("DIN_LOC_ROOT")
    res["layers"] = layer_depths(e.get("DOUT_S_ROOT"))
    return res


# ---------------------------------------------------------------- driver
def row_for(site, kind, source, path, d):
    org = d.get("ORGANIC") or []
    return {"site": site, "kind": kind, "source": source, "path": str(path),
            "lat": d.get("cell_lat"), "lon": d.get("cell_lon"), "dist_deg": d.get("dist_deg"),
            "zbedrock": d.get("zbedrock"), "zbedrock_3x3": d.get("zbedrock_3x3"),
            "ORGANIC": "/".join(str(x) for x in org), "ORGANIC_3x3_lev1": d.get("ORGANIC_3x3_lev1"),
            "FMAX": d.get("FMAX"), "FMAX_3x3": d.get("FMAX_3x3"), "SOIL_COLOR": d.get("SOIL_COLOR"),
            "SOIL_COLOR_3x3": d.get("SOIL_COLOR_3x3"), "SLOPE": d.get("SLOPE"), "STD_ELEV": d.get("STD_ELEV"),
            "PCT_NATVEG": d.get("PCT_NATVEG"), "PCT_CROP": d.get("PCT_CROP"), "PCT_LAKE": d.get("PCT_LAKE"),
            "PCT_WETLAND": d.get("PCT_WETLAND"), "PCT_GLACIER": d.get("PCT_GLACIER"), "PCT_URBAN": d.get("PCT_URBAN"),
            "PCT_SAND1": (d.get("PCT_SAND") or [None])[0], "PCT_CLAY1": (d.get("PCT_CLAY") or [None])[0]}


def line(r):
    org = r["ORGANIC"].split("/") if r["ORGANIC"] else []
    return (f"zbed {r['zbedrock']} {r['zbedrock_3x3'] or ''} | ORG L1-10 {'/'.join(org)} | FMAX {r['FMAX']} | "
            f"COLOR {r['SOIL_COLOR']} {r['SOIL_COLOR_3x3'] or ''} | SLOPE {r['SLOPE']} SDE {r['STD_ELEV']} | "
            f"NAT {r['PCT_NATVEG']} CROP {r['PCT_CROP']} LAKE {r['PCT_LAKE']} WET {r['PCT_WETLAND']} "
            f"URB {r['PCT_URBAN']} | S/C {r['PCT_SAND1']}/{r['PCT_CLAY1']}")


def run(a):
    from netCDF4 import Dataset
    out = Path(a.out_dir) if a.out_dir else Path.home() / f"ozjp_surface_stage01_{utc()}"
    out.mkdir(parents=True, exist_ok=False)
    coords = list(csv.DictReader(open(a.coords, newline="")))
    res = {"generated_utc": utc(), "sites": {}}
    print("== 3. model settings (template)", flush=True)
    ms = model_settings(a.cases_root, a.template_case)
    res["model_settings"] = ms
    for k, v in (ms.get("lnd_in") or {}).items():
        print(f"  lnd_in {k} = {v}")
    if "user_nl_clm_sets_use_bedrock" in ms:
        print(f"  user_nl_clm sets use_bedrock: {ms['user_nl_clm_sets_use_bedrock']}")
    for k, v in (ms.get("clm_params") or {}).items():
        print(f"  clm param {k} = {v}")
    for k, v in (ms.get("fates_root_params") or {}).items():
        print(f"  fates {k} = {v}")
    lay = ms.get("layers", {})
    print(f"  layers from {lay.get('file')}: ZSOI {lay.get('ZSOI_m')}\n  layer bottoms {lay.get('bottom_m')}")
    gpath = find_global(a.din_root or ms.get("din_loc_root") or BASE / "inputdata", a.global_surfdata)
    res["global_surface"] = {"path": str(gpath) if gpath else None}
    rows = []
    print(f"== 1/2. surface fields at towers | global {gpath}", flush=True)
    gds = Dataset(str(gpath)) if gpath and gpath.is_file() else None
    if gds is not None:
        res["global_surface"]["sha256"] = sha256(gpath)
    try:
        for c in coords:
            site, lat, lon = c["site"], float(c["lat"]), float(c["lon"])
            sres = res["sites"].setdefault(site, {"lat": lat, "lon": lon, "surfaces": []})
            print(f"  {site} ({lat}, {lon})")
            if gds is not None:
                d = surface_values(gds, lat, lon)
                sres["global"] = d
                r = row_for(site, "GLOBAL_F09", "global", gpath, d)
                rows.append(r)
                land = "" if d.get("nearest_is_land") in (True, None) else \
                    f" NEAREST NOT LAND -> land cell {d['nearest_land_cell']} at {d['nearest_land_dist_deg']} deg"
                print(f"    F09 cell {d['cell']} ({d['cell_lat']:.2f},{d['cell_lon']:.2f}) d={d['dist_deg']}{land}\n"
                      f"      {line(r)}")
            for p, how in find_point_surfaces(site, a.cases_root, Path.home(), a.sites_root):
                if not p.is_file():
                    print(f"    {how}: MISSING {p}")
                    continue
                with Dataset(str(p)) as ds:
                    d = surface_values(ds, lat, lon)
                d["sha256"] = sha256(p)
                sres["surfaces"].append({"source": how, "path": str(p), **d})
                r = row_for(site, "POINT", how, p, d)
                rows.append(r)
                print(f"    {how}: {p.name} sha {d['sha256'][:12]}\n      {line(r)}")
    finally:
        if gds is not None:
            gds.close()
    with open(out / "stage01_surface_fields.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TSV_FIELDS, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    (out / "stage01_surface.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(f"STAGE01 SURFACE DONE (read only) | {out}")
    return 0


def self_test():
    import tempfile
    import numpy as np
    from netCDF4 import Dataset
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        g = d / GLOBAL_NAME
        with Dataset(str(g), "w") as ds:
            ds.createDimension("lsmlat", 4); ds.createDimension("lsmlon", 5); ds.createDimension("nlevsoi", 10)
            ds.createDimension("numurbl", 3)
            lat = np.repeat(np.array([-30., -20., -10., 0.])[:, None], 5, 1)
            lon = np.repeat(np.array([120., 130., 140., 150., 359.])[None, :], 4, 0)
            ds.createVariable("LATIXY", "f8", ("lsmlat", "lsmlon"))[:] = lat
            ds.createVariable("LONGXY", "f8", ("lsmlat", "lsmlon"))[:] = lon
            lf = np.ones((4, 5)); lf[1, 1] = 0
            ds.createVariable("LANDFRAC_PFT", "f8", ("lsmlat", "lsmlon"))[:] = lf
            zb = np.arange(20, dtype=float).reshape(4, 5)
            ds.createVariable("zbedrock", "f8", ("lsmlat", "lsmlon"))[:] = zb
            ds.createVariable("SOIL_COLOR", "i4", ("lsmlat", "lsmlon"))[:] = 7
            ds.createVariable("PCT_NATVEG", "f8", ("lsmlat", "lsmlon"))[:] = 90.
            ds.createVariable("PCT_URBAN", "f8", ("numurbl", "lsmlat", "lsmlon"))[:] = 1.
            org = np.zeros((10, 4, 5)); org[:, 2, 2] = np.arange(10)
            ds.createVariable("ORGANIC", "f8", ("nlevsoi", "lsmlat", "lsmlon"))[:] = org
        with Dataset(str(g)) as ds:
            v = surface_values(ds, -20.4, 131.0)       # nearest cell (1,1) is not land
            assert v["cell"] == [1, 1] and v["nearest_is_land"] is False and v["zbedrock"] == 6.0
            assert v["nearest_land_cell"] in ([0, 1], [1, 0], [1, 2], [2, 1]) and v["PCT_URBAN"] == 3.0
            assert v["zbedrock_3x3"] == [0.0, 12.0], v["zbedrock_3x3"]       # 3x3 land cells only
            v = surface_values(ds, -10.0, 140.2)
            assert v["cell"] == [2, 2] and v["ORGANIC"] == [float(x) for x in range(10)] and v["SOIL_COLOR"] == 7.0
            v = surface_values(ds, -10.0, -0.5)        # longitude wrap: -0.5 -> 359.5
            assert v["cell"] == [2, 4]
        p = d / "surfdata_XX-Abc_point.nc"
        with Dataset(str(p), "w") as ds:
            ds.createDimension("lsmlat", 1); ds.createDimension("lsmlon", 1); ds.createDimension("nlevsoi", 10)
            ds.createVariable("LATIXY", "f8", ("lsmlat", "lsmlon"))[:] = -22.3
            ds.createVariable("LONGXY", "f8", ("lsmlat", "lsmlon"))[:] = 133.2
            ds.createVariable("zbedrock", "f8", ("lsmlat", "lsmlon"))[:] = 9.27
            ds.createVariable("ORGANIC", "f8", ("nlevsoi", "lsmlat", "lsmlon"))[:] = np.arange(10).reshape(10, 1, 1)
        with Dataset(str(p)) as ds:
            v = surface_values(ds, -22.3, 133.2)
            assert v["zbedrock"] == 9.27 and v["ORGANIC"][9] == 9.0 and v["cell"] is None
        r = row_for("XX-Abc", "POINT", "x", p, v)
        assert r["ORGANIC"] == "/".join(str(float(x)) for x in range(10)) and "zbed 9.27" in line(r)
        # model settings: lnd_in, user_nl_clm, CLM param file, FATES json, history layers
        case = d / "cases" / TEMPLATE
        (case / "CaseDocs").mkdir(parents=True)
        cp = d / "clm_params.nc"
        with Dataset(str(cp), "w") as ds:
            ds.createVariable("organic_max", "f8", ())[...] = 130.0
            ds.createVariable("zbedrock_sf", "f8", ())[...] = 1.0
        fp = d / "fates.json"
        fp.write_text(json.dumps({"parameters": {"fates_pftname": {"data": ["a", "b"]},
                                                 "fates_allom_zroot_max_z": {"data": [100.0, 100.0]},
                                                 "fates_leaf_slatop": {"data": [0.01, 0.02]}}}))
        (case / "CaseDocs/lnd_in").write_text(f" use_bedrock = .false.\n soil_layerstruct_predefined = '20SL_8.5m'\n"
                                              f" paramfile = '{cp}'\n fates_paramfile = '{fp}'\n")
        (case / "user_nl_clm").write_text("hist_nhtfrq = -24\n")
        arch = d / "archive" / TEMPLATE
        (arch / "lnd/hist").mkdir(parents=True)
        with Dataset(str(arch / f"lnd/hist/{TEMPLATE}.clm2.h0a.2801-01-02-00000.nc"), "w") as ds:
            ds.createDimension("levgrnd", 3); ds.createDimension("lndgrid", 1)
            ds.createVariable("ZSOI", "f8", ("levgrnd", "lndgrid"))[:] = [[0.01], [0.04], [0.09]]
            ds.createVariable("DZSOI", "f8", ("levgrnd", "lndgrid"))[:] = [[0.02], [0.04], [0.06]]
        (case / "env_run.xml").write_text(f'<file><entry id="DOUT_S_ROOT" value="{arch}"></entry>'
                                          f'<entry id="DIN_LOC_ROOT" value="{d}"></entry></file>')
        ms = model_settings(d / "cases", TEMPLATE)
        assert ms["lnd_in"]["use_bedrock"] == ".false." and ms["user_nl_clm_sets_use_bedrock"] is False
        assert ms["clm_params"]["organic_max"] == 130.0 and "zbedrock" not in ms["clm_params"]
        assert list(ms["fates_root_params"]) == ["file", "fates_pftname", "fates_allom_zroot_max_z"]
        assert ms["layers"]["bottom_m"] == [0.02, 0.06, 0.12]
        (d / "lnd/clm2/surfdata_esmf/ctsm5.3.0").mkdir(parents=True)
        (d / "lnd/clm2/surfdata_esmf/ctsm5.3.0" / GLOBAL_NAME).write_bytes(b"x")
        assert find_global(d) == d / "lnd/clm2/surfdata_esmf/ctsm5.3.0" / GLOBAL_NAME
    print("STAGE01 SURFACE SELF-TEST PASS (nearest / land / 3x3 / wrap, point files, lnd_in, CLM and FATES params, "
          "layer depths, global file search; no IRIDIS)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--coords")
    ap.add_argument("--cases-root", default=str(CASES))
    ap.add_argument("--sites-root", default=str(SITES))
    ap.add_argument("--template-case", default=TEMPLATE)
    ap.add_argument("--din-root")
    ap.add_argument("--global-surfdata")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.coords:
        ap.error("--coords is required")
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
