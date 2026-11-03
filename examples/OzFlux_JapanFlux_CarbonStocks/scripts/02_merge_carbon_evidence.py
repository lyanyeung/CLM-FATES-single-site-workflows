#!/usr/bin/env python3
"""Merge the per-network literature evidence into the committed carbon-stock topic files (runs anywhere).

Inputs (a research folder): oz_/jp_carbon_stocks.csv, oz_/jp_disturbance_events.csv and oz_/jp_annual_fluxes.csv,
in the column layouts given in README.md. A network whose files are absent is skipped.

Outputs in data/:
- carbon_stock_evidence_<date>.csv;
- disturbance_management_events_<date>.csv;
- published_annual_fluxes_<date>.csv.

Each output keeps every source column, adds a `network` column, and has its rows sorted by site and id. The script
checks the column layout, that ids are unique, the category values, and that the AU-ASM Cleverly 2022 restriction
is honoured. It also prints the per-site NEE range for the summary page.

Usage: python3 02_merge_carbon_evidence.py --research DIR --date 20261103
       python3 02_merge_carbon_evidence.py --self-test
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
STOCK_COLS = ("evidence_id", "site", "quantity", "value", "unit", "value_kgC_m2", "carbon_fraction_used",
              "depth_top_cm", "depth_bottom_cm", "year_or_period", "method", "tower_specific", "spatial_scope",
              "data_status", "citation", "doi_or_url", "locator", "quote", "verification", "note")
EVENT_COLS = ("event_id", "site", "event_type", "date_start", "date_end", "recurrence", "extent_or_severity",
              "effect_on_stand", "citation", "doi_or_url", "locator", "quote", "verification", "note")
FLUX_COLS = ("flux_id", "site", "period", "NEE_gC_m2_yr", "GPP_gC_m2_yr", "ER_gC_m2_yr", "sign_convention", "method",
             "citation", "doi_or_url", "locator", "quote", "verification", "note")
SETS = (("carbon_stocks", STOCK_COLS, "evidence_id", "carbon_stock_evidence"),
        ("disturbance_events", EVENT_COLS, "event_id", "disturbance_management_events"),
        ("annual_fluxes", FLUX_COLS, "flux_id", "published_annual_fluxes"))
VERIFICATION = {"READ_FULL_TEXT", "READ_ABSTRACT", "READ_WEBPAGE", "SECONDARY_CITATION"}
STATUS = {"OK", "USE_WITH_CAUTION", "EXCLUDED_BY_DATA_PROVIDER", ""}


def read(path):
    text = Path(path).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    return list(csv.DictReader(io.StringIO(text)))


def merge(research):
    out = {}
    for key, cols, idc, _ in SETS:
        rows = []
        for net, prefix in (("OzFlux", "oz"), ("JapanFlux", "jp")):
            p = Path(research) / f"{prefix}_{key}.csv"
            if not p.is_file():
                continue
            got = read(p)
            if got and tuple(got[0].keys()) != cols:
                raise SystemExit(f"{p.name}: columns {tuple(got[0].keys())} differ from {cols}")
            rows += [{"network": net, **r} for r in got]
        ids = [r[idc] for r in rows]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            raise SystemExit(f"{key}: duplicate ids {dup}")
        badv = sorted({r["verification"] for r in rows} - VERIFICATION)
        if badv:
            raise SystemExit(f"{key}: unknown verification values {badv}")
        if key == "carbon_stocks":
            bads = sorted({r["data_status"] for r in rows} - STATUS)
            if bads:
                raise SystemExit(f"carbon_stocks: unknown data_status {bads}")
            for r in rows:
                if r["site"] == "AU-ASM" and "Cleverly" in r["citation"] and "2018" in r["year_or_period"] \
                        and r["data_status"] != "EXCLUDED_BY_DATA_PROVIDER":
                    raise SystemExit(f"{r['evidence_id']}: Cleverly 2022 2018 values must be EXCLUDED_BY_DATA_PROVIDER")
        out[key] = sorted(rows, key=lambda r: (r["site"], r[idc]))
    return out


def nee_ranges(fluxes):
    rng = {}
    for r in fluxes:
        try:
            v = float(r["NEE_gC_m2_yr"])
        except ValueError:
            continue
        lo, hi = rng.get(r["site"], (v, v))
        rng[r["site"]] = (min(lo, v), max(hi, v))
    return rng


def write(out, date):
    for key, cols, _, stem in SETS:
        p = HERE / "data" / f"{stem}_{date}.csv"
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=("network",) + cols, lineterminator="\n")
            w.writeheader()
            w.writerows(out[key])
        print(f"wrote {p.name}: {len(out[key])} rows")


def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        def put(name, cols, rows):
            with open(d / name, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
                w.writeheader(); w.writerows(rows)
        base = {c: "" for c in STOCK_COLS}
        put("oz_carbon_stocks.csv", STOCK_COLS, [
            {**base, "evidence_id": "AU-ASM-C05", "site": "AU-ASM", "citation": "Cleverly J. (2022)",
             "year_or_period": "2018-06-01", "data_status": "EXCLUDED_BY_DATA_PROVIDER", "verification": "READ_WEBPAGE"}])
        put("oz_disturbance_events.csv", EVENT_COLS, [])
        put("oz_annual_fluxes.csv", FLUX_COLS, [
            {**{c: "" for c in FLUX_COLS}, "flux_id": "F1", "site": "AU-How", "NEE_gC_m2_yr": "-424", "verification": "READ_FULL_TEXT"},
            {**{c: "" for c in FLUX_COLS}, "flux_id": "F2", "site": "AU-How", "NEE_gC_m2_yr": "-528.5", "verification": "READ_FULL_TEXT"}])
        out = merge(d)
        assert out["carbon_stocks"][0]["network"] == "OzFlux" and nee_ranges(out["annual_fluxes"]) == {"AU-How": (-528.5, -424.0)}
        put("oz_carbon_stocks.csv", STOCK_COLS, [
            {**base, "evidence_id": "AU-ASM-C05", "site": "AU-ASM", "citation": "Cleverly J. (2022)",
             "year_or_period": "2018-06-01", "data_status": "OK", "verification": "READ_WEBPAGE"}])
        try:
            merge(d)
            raise AssertionError("2018 Cleverly row with status OK was not rejected")
        except SystemExit:
            pass
    print("CARBON MERGE SELF-TEST PASS (layout, network tag, CRLF input, AU-ASM restriction, NEE ranges)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--research")
    ap.add_argument("--date")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    out = merge(a.research)
    write(out, a.date)
    for s, (lo, hi) in sorted(nee_ranges(out["annual_fluxes"]).items()):
        print(f"  {s}: published annual NEE {lo:g} .. {hi:g} g C m-2 yr-1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
