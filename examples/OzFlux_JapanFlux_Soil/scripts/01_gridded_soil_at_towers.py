#!/usr/bin/env python3
"""Stage01: gridded soil texture, bulk density, organic carbon and coarse fragments at the 20 OzFlux/JapanFlux towers.

Sources (read point by point from cloud-optimised rasters; nothing is downloaded in full):
  SOILGRIDS  ISRIC SoilGrids 2.0 (250 m, CC BY 4.0), six depths 0-200 cm, USDA particle sizes
             (clay < 2 um, silt 2-50 um, sand 50-2000 um). Properties clay, sand, silt, bdod, soc, cfvo;
             statistics mean, Q0.05, Q0.95 (texture) and mean (others). All sites.
  SLGA       TERN Soil and Landscape Grid of Australia v2 (90 m), six depths 0-200 cm, ISSS particle sizes
             (clay < 2 um, silt 2-20 um, sand 20-2000 um). Clay, sand, silt EV/05/95 and SOC EV. Australian sites only.
             Needs a TERN API key: --tern-key-file FILE (one line) or the TERN_API_KEY environment variable.
             The key is passed to GDAL as HTTP basic auth (user "apikey") and never printed or written.

For each raster the value at the tower pixel is recorded, plus the minimum and maximum over the 3 x 3 pixel window
around it (750 m for SoilGrids, 270 m for SLGA) as a measure of local heterogeneity.

Usage (WSL or an IRIDIS6 login node; internet needed):
  python3 -B 01_gridded_soil_at_towers.py --self-test
  python3 -B 01_gridded_soil_at_towers.py --sites ../data/OZ_JP_20_SITE_COORDINATES_20261103.csv --out-dir OUT
  python3 -B 01_gridded_soil_at_towers.py ... --sources SLGA --tern-key-file ~/.tern_api_key
Outputs in OUT: gridded_soil_at_towers_long.csv, metadata.json. A rerun skips (source, layer) pairs already in the
long CSV unless --refresh is given.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

DEPTHS = ((0, 5), (5, 15), (15, 30), (30, 60), (60, 100), (100, 200))
SOILGRIDS_BASE = "https://files.isric.org/soilgrids/latest/data"
# property: (divisor to the output unit, output unit, statistics)
SOILGRIDS_PROPS = {
    "clay": (10.0, "%", ("mean", "Q0.05", "Q0.95")),
    "sand": (10.0, "%", ("mean", "Q0.05", "Q0.95")),
    "silt": (10.0, "%", ("mean", "Q0.05", "Q0.95")),
    "bdod": (100.0, "g cm-3", ("mean",)),
    "soc": (10.0, "g kg-1", ("mean",)),
    "cfvo": (10.0, "% vol", ("mean",)),
}
SLGA_BASE = "https://data.tern.org.au/model-derived/slga/NationalMaps/SoilAndLandscapeGrid"
SLGA_PROPS = {   # code: (path, date, unit, components)
    "CLY": ("CLY/v2", "20210902", "%", ("EV", "05", "95")),
    "SND": ("SND/v2", "20210902", "%", ("EV", "05", "95")),
    "SLT": ("SLT/v2", "20210902", "%", ("EV", "05", "95")),
    "SOC": ("SOC/90m/v2", "20220727", "%", ("EV",)),
}
SLGA_NAMES = {"CLY": "clay", "SND": "sand_ISSS_20um", "SLT": "silt_ISSS_2_20um", "SOC": "soc_pct"}
FIELDS = ["site", "source", "property", "depth_top_cm", "depth_bottom_cm", "statistic", "value", "unit",
          "window3x3_min", "window3x3_max", "window3x3_n", "row", "col", "particle_scheme", "url", "status"]


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def layers(sources, slga_ok):
    out = []
    if "SOILGRIDS" in sources:
        for p, (div, unit, stats) in SOILGRIDS_PROPS.items():
            for top, bot in DEPTHS:
                for st in stats:
                    url = f"{SOILGRIDS_BASE}/{p}/{p}_{top}-{bot}cm_{st}.vrt"
                    scheme = "USDA" if p in ("clay", "sand", "silt") else ""
                    out.append(dict(source="SOILGRIDS", property=p, top=top, bot=bot, stat=st, url=url, div=div,
                                    unit=unit, scheme=scheme, au_only=False))
    if "SLGA" in sources and slga_ok:
        for code, (path, date, unit, comps) in SLGA_PROPS.items():
            for top, bot in DEPTHS:
                for c in comps:
                    url = f"{SLGA_BASE}/{path}/{code}_{top:03d}_{bot:03d}_{c}_N_P_AU_TRN_N_{date}.tif"
                    scheme = "ISSS" if code in ("CLY", "SND", "SLT") else ""
                    out.append(dict(source="SLGA", property=SLGA_NAMES[code], top=top, bot=bot, stat=c, url=url,
                                    div=1.0, unit=unit, scheme=scheme, au_only=True))
    return out


def window_values(ds, x, y, div):
    """Value at the pixel containing (x, y) in the dataset CRS, and min/max over the 3x3 window."""
    import numpy as np
    from rasterio.windows import Window
    row, col = ds.index(x, y)
    if not (0 <= row < ds.height and 0 <= col < ds.width):
        return None, None, None, 0, row, col
    r0, c0 = max(row - 1, 0), max(col - 1, 0)
    r1, c1 = min(row + 2, ds.height), min(col + 2, ds.width)
    a = ds.read(1, window=Window(c0, r0, c1 - c0, r1 - r0), masked=True).astype(float)
    nod = ds.nodata
    good = ~np.ma.getmaskarray(a)
    if nod is not None:
        good &= a.data != nod
    good &= np.isfinite(a.data)
    centre = a.data[row - r0, col - c0] if good[row - r0, col - c0] else None
    vals = a.data[good] / div
    if vals.size == 0:
        return None, None, None, 0, row, col
    return (None if centre is None else round(float(centre) / div, 4), round(float(vals.min()), 4),
            round(float(vals.max()), 4), int(vals.size), row, col)


def read_layer(L, sites, env_opts):
    import rasterio
    from rasterio.env import Env
    from rasterio.warp import transform
    rows = []
    pts = [s for s in sites if not L["au_only"] or s["network"] == "OzFlux"]
    try:
        with Env(**env_opts):
            with rasterio.open("/vsicurl/" + L["url"]) as ds:
                xs, ys = [float(s["lon"]) for s in pts], [float(s["lat"]) for s in pts]
                if ds.crs is not None and ds.crs.to_epsg() != 4326:
                    xs, ys = transform("EPSG:4326", ds.crs, xs, ys)
                for s, x, y in zip(pts, xs, ys):
                    v, lo, hi, n, row, col = window_values(ds, x, y, L["div"])
                    rows.append(dict(site=s["site"], source=L["source"], property=L["property"],
                                     depth_top_cm=L["top"], depth_bottom_cm=L["bot"], statistic=L["stat"], value=v,
                                     unit=L["unit"], window3x3_min=lo, window3x3_max=hi, window3x3_n=n, row=row,
                                     col=col, particle_scheme=L["scheme"], url=L["url"],
                                     status="OK" if v is not None else "NO_DATA"))
    except Exception as exc:   # report, never guess
        msg = str(exc).replace("\n", " ")[:160]
        for s in pts:
            rows.append(dict(site=s["site"], source=L["source"], property=L["property"], depth_top_cm=L["top"],
                             depth_bottom_cm=L["bot"], statistic=L["stat"], value=None, unit=L["unit"],
                             particle_scheme=L["scheme"], url=L["url"], status="READ_ERROR: " + msg))
    return L, rows


def read_sites(path):
    sites = []
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if not r.get("lat") or not r.get("lon"):
            print(f"  skip {r['site']}: no coordinates yet", flush=True)
            continue
        lat, lon = float(r["lat"]), float(r["lon"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise SystemExit(f"bad coordinates for {r['site']}: {lat}, {lon}")
        sites.append(r)
    return sites


def tern_key(a):
    if a.tern_key_file:
        k = Path(a.tern_key_file).expanduser().read_text().strip()
    else:
        k = os.environ.get("TERN_API_KEY", "").strip()
    return k or None


def run(a):
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sites = read_sites(a.sites)
    key = tern_key(a) if "SLGA" in a.sources else None
    if "SLGA" in a.sources and not key:
        print("SLGA requested but no TERN API key (--tern-key-file or TERN_API_KEY): SLGA skipped", flush=True)
    env_opts = dict(GDAL_HTTP_TIMEOUT=90, GDAL_HTTP_MAX_RETRY=4, GDAL_HTTP_RETRY_DELAY=5,
                    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.vrt,.ovr")
    long_csv = out / "gridded_soil_at_towers_long.csv"
    old = list(csv.DictReader(open(long_csv, encoding="utf-8"))) if long_csv.is_file() and not a.refresh else []
    site_ids = {s["site"] for s in sites}
    done = {(r["source"], r["url"]) for r in old if r["status"] == "OK" and r["site"] in site_ids}
    have_sites = {}
    for r in old:
        if r["status"] == "OK":
            have_sites.setdefault((r["source"], r["url"]), set()).add(r["site"])
    todo = []
    for L in layers(a.sources, key is not None):
        need = {s["site"] for s in sites if not L["au_only"] or s["network"] == "OzFlux"}
        if (L["source"], L["url"]) in done and need <= have_sites.get((L["source"], L["url"]), set()):
            continue
        todo.append(L)
    print(f"{len(sites)} sites, {len(todo)} raster layers to read", flush=True)
    keep = [r for r in old if (r["source"], r["url"]) not in {(L["source"], L["url"]) for L in todo}]
    new = []
    slga_env = dict(env_opts, GDAL_HTTP_AUTH="BASIC", GDAL_HTTP_USERPWD=f"apikey:{key}") if key else env_opts
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(read_layer, L, sites, slga_env if L["source"] == "SLGA" else env_opts) for L in todo]
        for i, f in enumerate(futs, 1):
            L, rows = f.result()
            bad = [r for r in rows if r["status"] != "OK"]
            print(f"  [{i}/{len(todo)}] {L['source']} {L['property']} {L['top']}-{L['bot']} {L['stat']}: "
                  f"{len(rows) - len(bad)} ok" + (f", {len(bad)} {bad[0]['status'][:70]}" if bad else ""), flush=True)
            new += rows
    allrows = sorted(keep + new, key=lambda r: (r["site"], r["source"], r["property"], int(r["depth_top_cm"]),
                                                 r["statistic"]))
    with open(long_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(allrows)
    import rasterio
    meta = {"generated_utc": utc(), "script": Path(__file__).name, "sites_csv": str(a.sites), "sources": a.sources,
            "slga_used": key is not None, "soilgrids_base": SOILGRIDS_BASE, "slga_base": SLGA_BASE,
            "rasterio": rasterio.__version__, "gdal": rasterio.__gdal_version__,
            "n_rows": len(allrows), "n_errors": sum(1 for r in allrows if r["status"] != "OK"),
            "sites": {s["site"]: {"lat": float(s["lat"]), "lon": float(s["lon"]), "coord_source": s.get("coord_source")}
                      for s in sites}}
    (out / "metadata.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(f"written {long_csv} ({len(allrows)} rows, {meta['n_errors']} not OK)", flush=True)
    return 1 if meta["n_errors"] else 0


def self_test():
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin
    import tempfile
    L = layers(("SOILGRIDS", "SLGA"), True)
    assert sum(l["source"] == "SOILGRIDS" for l in L) == 6 * (3 * 3 + 3), len(L)
    assert sum(l["source"] == "SLGA" for l in L) == 6 * (3 * 3 + 1)
    assert any(l["url"].endswith("/clay/clay_0-5cm_mean.vrt") for l in L)
    assert any(l["url"].endswith("/CLY/v2/CLY_000_005_EV_N_P_AU_TRN_N_20210902.tif") for l in L)
    assert any(l["url"].endswith("/SOC/90m/v2/SOC_100_200_EV_N_P_AU_TRN_N_20220727.tif") for l in L)
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "t.tif"
        a = np.arange(25, dtype="int16").reshape(5, 5) * 10
        a[0, 0] = -32768
        with rasterio.open(p, "w", driver="GTiff", height=5, width=5, count=1, dtype="int16", crs="EPSG:4326",
                           transform=from_origin(0, 5, 1, 1), nodata=-32768) as ds:
            ds.write(a, 1)
        with rasterio.open(p) as ds:
            v, lo, hi, n, row, col = window_values(ds, 2.5, 2.5, 10.0)   # centre pixel (2, 2) = 120
            assert (v, lo, hi, n, row, col) == (12.0, 6.0, 18.0, 9, 2, 2), (v, lo, hi, n)
            v, lo, hi, n, row, col = window_values(ds, 0.5, 4.5, 10.0)   # corner: nodata centre, 3 valid neighbours
            assert v is None and n == 3 and lo == 1.0 and hi == 6.0, (v, lo, hi, n)
    print("STAGE01 SELF-TEST PASS (layer list, URLs, 3x3 window, nodata, unit divisor; no network)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--sites")
    ap.add_argument("--out-dir")
    ap.add_argument("--sources", nargs="+", default=["SOILGRIDS", "SLGA"], choices=["SOILGRIDS", "SLGA"])
    ap.add_argument("--tern-key-file")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.sites or not a.out_dir:
        ap.error("--sites and --out-dir are required")
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
