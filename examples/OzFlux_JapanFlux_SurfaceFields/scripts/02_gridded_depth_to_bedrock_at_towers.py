#!/usr/bin/env python3
"""Gridded depth-to-bedrock evidence at the 20 OzFlux / JapanFlux towers (runs anywhere with internet; no IRIDIS).

SoilGrids250m 2017 (ISRIC, files.isric.org/soilgrids/former/2017-03-10; Hengl et al. 2017, PLoS ONE 12:e0169748),
read as 3x3 windows of 250 m cells around each tower:
- BDTICM: absolute depth to bedrock (cm). Regolith thickness, which can be tens of metres in old landscapes.
- BDRICM: depth to an R horizon within 0-200 cm (cm; 200 = none found).
- BDRLOG: probability (%) of an R horizon within 0-200 cm.

None of these maps resolves root-restricting layers such as hardpans, laterite, pumice or lava. They are context
for the site evidence, not a replacement for it.

Output: data/gridded_depth_to_bedrock_at_towers_20261103.csv (one row per site x product).

Usage:
  python3 02_gridded_depth_to_bedrock_at_towers.py --coords OZ_JP_20_SITE_COORDINATES_20261103.csv --out OUT.csv
  python3 02_gridded_depth_to_bedrock_at_towers.py --self-test
"""
from __future__ import annotations

import argparse
import csv
import sys

BASE = "https://files.isric.org/soilgrids/former/2017-03-10/data/"
PRODUCTS = (("BDTICM", "BDTICM_M_250m_ll.tif", "cm", "absolute depth to bedrock"),
            ("BDRICM", "BDRICM_M_250m_ll.tif", "cm", "depth to R horizon within 0-200 cm (200 = none)"),
            ("BDRLOG", "BDRLOG_M_250m_ll.tif", "%", "probability of R horizon within 0-200 cm"))
FIELDS = ("site", "product", "description", "unit", "centre", "window3x3_min", "window3x3_max", "window3x3_n",
          "row", "col", "lat", "lon", "url", "status")


def summarise(window, nodata):
    vals = [int(v) for v in window.ravel().tolist() if nodata is None or v != nodata]
    centre = window[1, 1] if window.shape == (3, 3) else None
    centre = None if centre is None or (nodata is not None and centre == nodata) else int(centre)
    return centre, (min(vals) if vals else None), (max(vals) if vals else None), len(vals)


def sample(coords):
    import rasterio
    from rasterio.windows import Window
    rows = []
    with rasterio.Env(GDAL_HTTP_TIMEOUT="60", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
        for prod, fn, unit, desc in PRODUCTS:
            url = BASE + fn
            with rasterio.open("/vsicurl/" + url) as ds:
                for c in coords:
                    lat, lon = float(c["lat"]), float(c["lon"])
                    r, k = ds.index(lon, lat)
                    try:
                        a = ds.read(1, window=Window(k - 1, r - 1, 3, 3))
                        centre, lo, hi, n = summarise(a, ds.nodata)
                        status = "OK" if centre is not None else "NODATA_CENTRE"
                    except Exception as exc:          # one failed read must not stop the others
                        centre = lo = hi = None
                        n, status = 0, "ERROR " + repr(exc)[:120]
                    rows.append(dict(site=c["site"], product=prod, description=desc, unit=unit, centre=centre,
                                     window3x3_min=lo, window3x3_max=hi, window3x3_n=n, row=r, col=k, lat=lat,
                                     lon=lon, url=url, status=status))
                    print(f"  {c['site']} {prod}: centre {centre} {unit} (3x3 {lo}-{hi}, n={n}) {status}", flush=True)
    return rows


def self_test():
    import numpy as np
    w = np.array([[1, 2, 3], [4, 5, 6], [7, -32768, 9]], dtype="int32")
    assert summarise(w, -32768) == (5, 1, 9, 8)
    assert summarise(np.full((3, 3), 255, dtype="uint8"), 255) == (None, None, None, 0)
    print("GRIDDED DEPTH SELF-TEST PASS")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--coords")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    coords = list(csv.DictReader(open(a.coords, newline="")))
    rows = sample(coords)
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
