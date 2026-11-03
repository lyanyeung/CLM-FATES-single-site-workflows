#!/usr/bin/env python3
"""Build the recommended non-texture surface fields for the 20 OzFlux / JapanFlux sites (runs anywhere, no IRIDIS).

Inputs, all in this folder's data/ directory:
- stage01_surface_fields_at_towers_20261103.csv: the f09 values the point surfaces inherit (IRIDIS Stage01).
- gridded_depth_to_bedrock_at_towers_20261103.csv: SoilGrids250m 2017 products (context only).
- site_surface_decisions_<date>.csv: one row per site. Columns:
    - zbedrock_m: plant-accessible depth from site evidence, blank = none;
    - zbedrock_tier and zbedrock_basis;
    - organic_rule: F09, or SCALE_TO_SITE_STOCK;
    - site_soc_stock_kgC_m2, soc_depth_cm and organic_basis.

Rules:
- zbedrock: the site value where one exists, otherwise the f09 value flagged ZBEDROCK_GRID_ONLY. The column CLM
  would use is reported too:
    - the bedrock layer index nbedrock, exactly as in initVerticalMod. The search starts at the layer holding
      zmin_bedrock = 0.4 m, which is layer 6 (0.32-0.48 m), and takes the layer whose bottom first reaches zbedrock.
      A value of 0.32 m or less matches nothing and gives the FULL column; it is flagged.
    - the depth of that layer's bottom.
  The value only acts with use_bedrock = .true.; with the FATES default (.false.) every site has the full 8.6 m.
- ORGANIC: F09 keeps the f09 profile. SCALE_TO_SITE_STOCK multiplies the whole f09 profile by
  site stock / f09-implied stock over the same depth, with stock = sum(ORGANIC_j / 1.724 * overlap_j). This keeps
  the f09 vertical shape and matches the measured stock. Values are capped at organic_max = 130.
- FMAX and SOIL_COLOR are kept at f09. Landunits become NATVEG 100, with crop / urban / lake / wetland / glacier 0.

Outputs:
- OZ_JP_RECOMMENDED_SURFACE_FIELDS_20_SITES_<date>.csv;
- a table printed for the summary page.

Usage:
  python3 03_build_surface_field_recommendation.py --decisions data/site_surface_decisions_<date>.csv --date <date>
  python3 03_build_surface_field_recommendation.py --self-test
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
OM_PER_C = 1.724
ORGANIC_MAX = 130.0
ZMIN_BEDROCK = 0.4
# 20SL_8.5m soil layer bottoms (m), from the template history file ZSOI/DZSOI (Stage01)
MODEL_BOTTOMS = (0.02, 0.06, 0.12, 0.20, 0.32, 0.48, 0.68, 0.92, 1.20, 1.52, 1.88, 2.28, 2.72, 3.26, 3.90, 4.64,
                 5.48, 6.42, 7.46, 8.60)
# surface-dataset levels (nlevsoifl = 10): node depths zsoifl = 0.025 * (exp(0.5 * (j - 0.5)) - 1)
FL_NODES = tuple(0.025 * (math.exp(0.5 * (j - 0.5)) - 1) for j in range(1, 11))


def fl_interfaces():
    """Bottom interfaces of the 10 surface-dataset levels (CLM convention: midpoints, last = z10 + dz10 / 2)."""
    z = FL_NODES
    zi = [0.5 * (z[j] + z[j + 1]) for j in range(9)]
    zi.append(z[9] + 0.5 * (z[9] - z[8]))
    return tuple(zi)


FL_BOTTOMS = fl_interfaces()


def jmin_bedrock():
    """First layer CLM may use as bedrock layer: the layer that contains zmin_bedrock (initVerticalMod)."""
    jmin = 3
    for j in range(3, len(MODEL_BOTTOMS) + 1):
        if MODEL_BOTTOMS[j - 2] < ZMIN_BEDROCK <= MODEL_BOTTOMS[j - 1]:
            jmin = j
    return jmin


def nbedrock(zbed):
    """CLM bedrock layer index (1-based) and the depth of its bottom for a zbedrock value (use_bedrock on),
    exactly as initVerticalMod. CLM does not raise small values: a zbedrock at or above the bottom of layer
    jmin-1 (0.32 m) matches no layer and falls through to the full column (nlevsoi)."""
    z = float(zbed)
    nb = len(MODEL_BOTTOMS)
    for j in range(jmin_bedrock(), len(MODEL_BOTTOMS) + 1):
        if MODEL_BOTTOMS[j - 2] < z <= MODEL_BOTTOMS[j - 1]:
            nb = j
    return nb, MODEL_BOTTOMS[nb - 1]


def implied_stock(organic, depth_m):
    """Soil organic carbon (kg C m-2) implied by a 10-level ORGANIC profile (kg OM m-3) over 0..depth_m."""
    top, tot = 0.0, 0.0
    for o, bot in zip(organic, FL_BOTTOMS):
        overlap = max(0.0, min(bot, depth_m) - top)
        tot += o / OM_PER_C * overlap
        top = bot
        if top >= depth_m:
            break
    return tot


def scale_to_stock(organic, stock, depth_m):
    f = stock / implied_stock(organic, depth_m)
    return [min(o * f, ORGANIC_MAX) for o in organic], f


def fnum(x):
    return None if x in (None, "") else float(x)


def build(stage01, gridded, decisions):
    f09 = {r["site"]: r for r in stage01 if r["kind"] == "GLOBAL_F09"}
    grid = {}
    for r in gridded:
        grid.setdefault(r["site"], {})[r["product"]] = r
    out = []
    for d in decisions:
        s = d["site"]
        g = f09[s]
        org = [float(g[f"ORGANIC_L{i}"]) for i in range(1, 11)]
        flags = []
        zsite = fnum(d.get("zbedrock_m"))
        z = zsite if zsite is not None else float(g["zbedrock_m"])
        if zsite is None:
            flags.append("ZBEDROCK_GRID_ONLY")
        if z <= MODEL_BOTTOMS[jmin_bedrock() - 2]:
            flags.append("ZBEDROCK_TOO_SHALLOW_GIVES_FULL_COLUMN")
        nb, zbot = nbedrock(z)
        rule = d.get("organic_rule") or "F09"
        factor = 1.0
        if rule == "SCALE_TO_SITE_STOCK":
            org_new, factor = scale_to_stock(org, float(d["site_soc_stock_kgC_m2"]), float(d["soc_depth_cm"]) / 100)
            if any(o >= ORGANIC_MAX for o in org_new):
                flags.append("ORGANIC_CAPPED_130")
        else:
            org_new = org
        bdt = grid.get(s, {}).get("BDTICM", {})
        zsens = fnum(d.get("sensitivity_zbedrock_m"))
        out.append({
            "site": s,
            "zbedrock_class": d.get("zbedrock_class", ""),
            "zbedrock_recommended_m": round(z, 3), "zbedrock_tier": d.get("zbedrock_tier") or "GRID_F09",
            "zbedrock_basis": d.get("zbedrock_basis", ""), "zbedrock_f09_m": float(g["zbedrock_m"]),
            "soilgrids_BDTICM_m": None if not bdt.get("centre") else int(bdt["centre"]) / 100,
            "use_bedrock_on_nbedrock": nb, "use_bedrock_on_soil_bottom_m": zbot,
            "use_bedrock_off_soil_bottom_m": MODEL_BOTTOMS[-1],
            "sensitivity_zbedrock_m": zsens,
            "sensitivity_soil_bottom_m": None if zsens is None else nbedrock(zsens)[1],
            "organic_rule": rule, "organic_scale_factor": round(factor, 3),
            "organic_basis": d.get("organic_basis", ""),
            **{f"ORGANIC_L{i + 1}": round(o, 3) for i, o in enumerate(org_new)},
            "ORGANIC_f09_L1": org[0],
            "FMAX": float(g["FMAX"]), "SOIL_COLOR": int(float(g["SOIL_COLOR"])),
            "PCT_NATVEG": 100, "PCT_CROP": 0, "PCT_URBAN": 0, "PCT_LAKE": 0, "PCT_WETLAND": 0, "PCT_GLACIER": 0,
            "f09_PCT_NATVEG": float(g["PCT_NATVEG"]), "flags": ";".join(flags), "notes": d.get("notes", "")})
    return out


def self_test():
    assert abs(FL_NODES[0] - 0.00710) < 1e-4 and abs(FL_NODES[9] - 2.8650) < 1e-3
    assert abs(FL_BOTTOMS[0] - 0.0175) < 1e-3 and abs(FL_BOTTOMS[9] - 3.4331) < 1e-3, FL_BOTTOMS
    assert jmin_bedrock() == 6                 # layer 6 (0.32-0.48 m) holds zmin_bedrock = 0.4 m
    assert nbedrock(0.2) == (20, 8.60)         # below 0.32 m: no match -> full column, as in CLM
    assert nbedrock(0.33) == (6, 0.48) and nbedrock(0.48) == (6, 0.48)
    assert nbedrock(1.0) == (9, 1.20) and nbedrock(0.92) == (8, 0.92)
    assert nbedrock(31.0) == (20, 8.60)
    org = [10.0] * 10
    assert abs(implied_stock(org, FL_BOTTOMS[9]) - 10 / OM_PER_C * FL_BOTTOMS[9]) < 1e-9
    new, f = scale_to_stock(org, 2 * implied_stock(org, 0.30), 0.30)
    assert abs(f - 2) < 1e-9 and new == [20.0] * 10
    new, _ = scale_to_stock([100.0] * 10, 2 * implied_stock([100.0] * 10, 0.3), 0.3)
    assert new == [ORGANIC_MAX] * 10
    st = [{"site": "XX", "kind": "GLOBAL_F09", "zbedrock_m": "12.8", "FMAX": "0.39", "SOIL_COLOR": "14",
           "PCT_NATVEG": "76", **{f"ORGANIC_L{i}": "20" for i in range(1, 11)}}]
    gr = [{"site": "XX", "product": "BDTICM", "centre": "1965"}]
    r = build(st, gr, [{"site": "XX", "zbedrock_m": "", "organic_rule": "F09"}])[0]
    assert r["zbedrock_recommended_m"] == 12.8 and r["flags"] == "ZBEDROCK_GRID_ONLY" and r["use_bedrock_on_nbedrock"] == 20
    assert r["soilgrids_BDTICM_m"] == 19.65 and r["PCT_NATVEG"] == 100 and r["ORGANIC_L1"] == 20.0
    r = build(st, gr, [{"site": "XX", "zbedrock_m": "0.3", "zbedrock_tier": "T1", "organic_rule": "SCALE_TO_SITE_STOCK",
                        "site_soc_stock_kgC_m2": str(implied_stock([20.0] * 10, 0.3) / 2), "soc_depth_cm": "30"}])[0]
    assert r["use_bedrock_on_soil_bottom_m"] == 8.6 and "ZBEDROCK_TOO_SHALLOW_GIVES_FULL_COLUMN" in r["flags"]
    assert r["ORGANIC_L1"] == 10.0 and r["organic_scale_factor"] == 0.5
    print("SURFACE RECOMMENDATION SELF-TEST PASS (dataset levels, CLM nbedrock, stock scaling and cap, build)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--decisions")
    ap.add_argument("--date")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    rd = lambda p: list(csv.DictReader(open(p, newline="")))
    rows = build(rd(HERE / "data/stage01_surface_fields_at_towers_20261103.csv"),
                 rd(HERE / "data/gridded_depth_to_bedrock_at_towers_20261103.csv"), rd(a.decisions))
    out = HERE / f"OZ_JP_RECOMMENDED_SURFACE_FIELDS_20_SITES_{a.date}.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print("| Site | zbedrock (m) | tier | f09 | BDTICM | use_bedrock on: layers / bottom (m) | ORGANIC L1 (f09 -> rec) | flags |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        print(f"| {r['site']} | {r['zbedrock_recommended_m']} | {r['zbedrock_tier']} | {r['zbedrock_f09_m']} | "
              f"{r['soilgrids_BDTICM_m']} | {r['use_bedrock_on_nbedrock']} / {r['use_bedrock_on_soil_bottom_m']} | "
              f"{r['ORGANIC_f09_L1']} -> {r['ORGANIC_L1']} | {r['flags']} |")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
