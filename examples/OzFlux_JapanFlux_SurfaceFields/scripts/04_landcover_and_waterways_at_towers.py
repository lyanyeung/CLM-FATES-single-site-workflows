#!/usr/bin/env python3
"""Land cover and nearby rivers at the 20 OzFlux / JapanFlux towers (runs anywhere with internet; no IRIDIS).

1. ESA WorldCover 10 m v200 (2021; Zanaga et al. 2022, CC BY 4.0), public COG tiles on AWS
   (esa-worldcover.s3.eu-central-1.amazonaws.com). Class shares inside circles of 250, 500, 1000 and 2000 m around
   each tower. This answers whether there is real cropland, built-up land or open water near the tower, as opposed to
   the crop / urban shares of the ~100 km f09 cell that the CTSM2000 point surfaces inherit.
2. OpenStreetMap waterways via the Overpass API (data (c) OpenStreetMap contributors, ODbL). Distance from the tower
   to the nearest mapped river (search radius 10 km), stream / canal / drain (3 km) and water body (3 km).
   Only the distances, names and types are kept, not the geometries.

WorldCover cropland (class 40) does not separate pasture from crops, and 2021 is one year. Mapped rivers can be
missing or misplaced in OSM; treat a distance as evidence to check against the site literature, not as proof.

Outputs:
  data/worldcover_landcover_at_towers_20261104.csv  (one row per site x radius)
  data/osm_waterways_near_towers_20261104.csv       (one row per site)

Usage:
  python3 04_landcover_and_waterways_at_towers.py --coords ../OzFlux_JapanFlux_Soil/data/OZ_JP_20_SITE_COORDINATES_20261103.csv \
      --landcover-out LC.csv --waterways-out WW.csv
  python3 04_landcover_and_waterways_at_towers.py --self-test
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
import urllib.parse
import urllib.request

WC_BASE = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
WC_CLASSES = ((10, "tree"), (20, "shrub"), (30, "grass"), (40, "crop"), (50, "built"), (60, "bare"),
              (70, "snow"), (80, "water"), (90, "wetland"), (95, "mangrove"), (100, "moss"))
RADII_M = (250, 500, 1000, 2000)
OVERPASS = "https://overpass-api.de/api/interpreter"
RIVER_SEARCH_M, STREAM_SEARCH_M, WATER_SEARCH_M = 10000, 3000, 3000

LC_FIELDS = (("site", "radius_m", "n_pixels") + tuple("pct_" + n for _, n in WC_CLASSES)
             + ("pct_other", "tiles", "status"))
WW_FIELDS = ("site", "lat", "lon", "nearest_river_name", "nearest_river_m", "rivers_within_10km",
             "nearest_stream_type", "nearest_stream_name", "nearest_stream_m",
             "nearest_water_body_type", "nearest_water_body_name", "nearest_water_body_m", "status")


def wc_tile(lat0, lon0):
    """WorldCover tile name of the 3 x 3 degree tile whose south-west corner is (lat0, lon0)."""
    return f"{'N' if lat0 >= 0 else 'S'}{abs(lat0):02d}{'E' if lon0 >= 0 else 'W'}{abs(lon0):03d}"


def tiles_for_box(south, north, west, east):
    lats = range(math.floor(south / 3) * 3, math.floor(north / 3) * 3 + 1, 3)
    lons = range(math.floor(west / 3) * 3, math.floor(east / 3) * 3 + 1, 3)
    return [(la, lo) for la in lats for lo in lons]


def metres(lat, lon, lat0, lon0):
    """Local equirectangular offsets (m) of (lat, lon) from (lat0, lon0)."""
    return (lon - lon0) * 111320.0 * math.cos(math.radians(lat0)), (lat - lat0) * 110574.0


def count_classes(values, dist, radii=RADII_M):
    import numpy as np
    out = {}
    for r in radii:
        v = values[dist <= r]
        n = int(v.size)
        row = {"n_pixels": n}
        known = 0
        for code, name in WC_CLASSES:
            k = int(np.count_nonzero(v == code))
            known += k
            row["pct_" + name] = round(100.0 * k / n, 2) if n else None
        row["pct_other"] = round(100.0 * (n - known) / n, 2) if n else None
        out[r] = row
    return out


def landcover(site, lat, lon):
    import numpy as np
    import rasterio
    from rasterio.windows import from_bounds
    rmax = max(RADII_M)
    dlat, dlon = rmax / 110574.0 * 1.02, rmax / (111320.0 * math.cos(math.radians(lat))) * 1.02
    south, north, west, east = lat - dlat, lat + dlat, lon - dlon, lon + dlon
    vals, dists, names = [], [], []
    for la, lo in tiles_for_box(south, north, west, east):
        name = wc_tile(la, lo)
        url = f"{WC_BASE}ESA_WorldCover_10m_2021_v200_{name}_Map.tif"
        with rasterio.open("/vsicurl/" + url) as ds:
            b = ds.bounds
            w_, s_, e_, n_ = max(west, b.left), max(south, b.bottom), min(east, b.right), min(north, b.top)
            if w_ >= e_ or s_ >= n_:
                continue
            win = from_bounds(w_, s_, e_, n_, ds.transform).round_offsets().round_lengths()
            a = ds.read(1, window=win)
            t = ds.window_transform(win)
            cols = t.c + (np.arange(a.shape[1]) + 0.5) * t.a
            rows = t.f + (np.arange(a.shape[0]) + 0.5) * t.e
            x = (cols[None, :] - lon) * 111320.0 * math.cos(math.radians(lat))
            y = (rows[:, None] - lat) * 110574.0
            vals.append(a.ravel())
            dists.append(np.sqrt(x * x + y * y).ravel())
            names.append(name)
    values, dist = np.concatenate(vals), np.concatenate(dists)
    res = count_classes(values, dist)
    return [dict(site=site, radius_m=r, tiles="+".join(names), status="OK", **res[r]) for r in RADII_M]


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def inside(pts):
    """Ray casting: is the origin inside the closed ring pts (list of (x, y) in m)?"""
    c = False
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        if (y1 > 0) != (y2 > 0) and 0 < (x2 - x1) * (0 - y1) / (y2 - y1) + x1:
            c = not c
    return c


def way_distance(geom, lat0, lon0, area=False):
    pts = [metres(g["lat"], g["lon"], lat0, lon0) for g in geom]
    if not pts:
        return None
    if len(pts) == 1:
        return math.hypot(*pts[0])
    if area and pts[0] == pts[-1] and inside(pts[:-1]):
        return 0.0
    return min(seg_dist(0.0, 0.0, *pts[i], *pts[i + 1]) for i in range(len(pts) - 1))


def overpass(lat, lon):
    q = (f'[out:json][timeout:90];('
         f'way["waterway"="river"](around:{RIVER_SEARCH_M},{lat},{lon});'
         f'way["waterway"~"^(stream|canal|drain)$"](around:{STREAM_SEARCH_M},{lat},{lon});'
         f'way["natural"="water"](around:{WATER_SEARCH_M},{lat},{lon});'
         f');out tags geom;')
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request(OVERPASS, data=data,
                                 headers={"User-Agent": "CLM-FATES-single-site-workflows surface-fields script 04"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(15 * (attempt + 1))


def waterways(site, lat, lon):
    els = overpass(lat, lon).get("elements", [])
    best = {"river": (None, None, None), "stream": (None, None, None), "water": (None, None, None)}
    rivers = set()
    for e in els:
        tags, geom = e.get("tags", {}), e.get("geometry", [])
        ww, nat = tags.get("waterway"), tags.get("natural")
        name = tags.get("name:en") or tags.get("name") or ""
        if ww == "river":
            kind, typ = "river", "river"
            rivers.add(name or f"way{e['id']}")
        elif ww in ("stream", "canal", "drain"):
            kind, typ = "stream", ww
        elif nat == "water":
            kind, typ = "water", tags.get("water", "water")
        else:
            continue
        d = way_distance(geom, lat, lon, area=(kind == "water"))
        if d is not None and (best[kind][2] is None or d < best[kind][2]):
            best[kind] = (typ, name, round(d))
    return dict(site=site, lat=lat, lon=lon,
                nearest_river_name=best["river"][1], nearest_river_m=best["river"][2],
                rivers_within_10km=len(rivers),
                nearest_stream_type=best["stream"][0], nearest_stream_name=best["stream"][1],
                nearest_stream_m=best["stream"][2],
                nearest_water_body_type=best["water"][0], nearest_water_body_name=best["water"][1],
                nearest_water_body_m=best["water"][2], status="OK")


def self_test():
    import numpy as np
    assert wc_tile(-24, 132) == "S24E132" and wc_tile(33, 138) == "N33E138" and wc_tile(-3, -60) == "S03W060"
    assert tiles_for_box(-22.30, -22.26, 133.23, 133.27) == [(-24, 132)]
    assert tiles_for_box(-33.01, -32.99, 116.99, 117.01) == [(-36, 114), (-36, 117), (-33, 114), (-33, 117)]
    v = np.array([40, 40, 10, 80, 10, 10, 10, 0])
    d = np.array([100, 200, 300, 400, 600, 900, 1500, 1800])
    r = count_classes(v, d)
    assert r[250]["n_pixels"] == 2 and r[250]["pct_crop"] == 100.0
    assert r[500]["pct_crop"] == 50.0 and r[500]["pct_water"] == 25.0 and r[2000]["pct_other"] == 12.5
    assert abs(seg_dist(0, 0, -5, 3, 5, 3) - 3) < 1e-12 and abs(seg_dist(0, 0, 4, 3, 8, 3) - 5) < 1e-12
    sq = [{"lat": la, "lon": lo} for la, lo in ((-1e-3, -1e-3), (-1e-3, 1e-3), (1e-3, 1e-3), (1e-3, -1e-3), (-1e-3, -1e-3))]
    assert way_distance(sq, 0.0, 0.0, area=True) == 0.0
    assert abs(way_distance(sq, 0.0, 0.0, area=False) - 110.574) < 0.01
    print("LANDCOVER / WATERWAYS SELF-TEST PASS")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--coords")
    ap.add_argument("--landcover-out")
    ap.add_argument("--waterways-out")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    import rasterio
    coords = list(csv.DictReader(open(a.coords, encoding="utf-8-sig", newline="")))
    lc_rows, ww_rows = [], []
    with rasterio.Env(GDAL_HTTP_TIMEOUT="60", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
        for c in coords:
            site, lat, lon = c["site"], float(c["lat"]), float(c["lon"])
            try:
                rows = landcover(site, lat, lon)
            except Exception as exc:          # one failed site must not stop the others
                rows = [dict(site=site, radius_m=r, status="ERROR " + repr(exc)[:120]) for r in RADII_M]
            lc_rows += rows
            r1 = next(r for r in rows if r["radius_m"] == 1000)
            print(f"  {site} WorldCover 1 km: crop {r1.get('pct_crop')} % built {r1.get('pct_built')} % "
                  f"water {r1.get('pct_water')} % wetland {r1.get('pct_wetland')} % {r1['status']}", flush=True)
            try:
                w = waterways(site, lat, lon)
            except Exception as exc:
                w = dict(site=site, lat=lat, lon=lon, status="ERROR " + repr(exc)[:120])
            ww_rows.append(w)
            print(f"  {site} OSM: river {w.get('nearest_river_name')!r} {w.get('nearest_river_m')} m; "
                  f"{w.get('nearest_stream_type')} {w.get('nearest_stream_name')!r} {w.get('nearest_stream_m')} m; "
                  f"water {w.get('nearest_water_body_type')} {w.get('nearest_water_body_m')} m {w['status']}", flush=True)
            time.sleep(2)
    for path, fields, rows in ((a.landcover_out, LC_FIELDS, lc_rows), (a.waterways_out, WW_FIELDS, ww_rows)):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {len(rows)} rows to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
