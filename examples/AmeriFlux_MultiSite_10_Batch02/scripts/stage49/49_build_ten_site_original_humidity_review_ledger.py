#!/usr/bin/env python3
"""Batch02 Stage49: read-only, source-pinned, row-level RH/VPD science review.

This builds a separate review ledger from original FLUXNET HH/HR primary files.
It does NOT approve repairs, import in-package *_ERA as independent CDS data,
rebuild Stage07/08 candidates, or alter forcing/NetCDF/CIME/Slurm.
The Stage08 set of 4,884 HOLD rows is a DIFFERENT cohort; no overlap is
claimed without an exact timestamp/source-key join.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import uuid

import numpy as np
import pandas as pd

STAGE48_BLOB = "8856b568d413e3d27c40fd6c6a014a4e755ecfb3"
STAGE48 = Path(__file__).resolve().parents[1] / "stage48" / "48_audit_ten_site_vpd_rh_era_repair_rule.py"
EXPERIMENT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
FIELDS = [
    "site", "source", "source_sha256", "source_csv_row", "timestamp_start",
    "timestamp_end", "year", "native_minutes", "TA_C", "VPD_hPa", "PA_kPa",
    "RH_raw_pct", "RH_derived_water_pct", "TA_original_QC", "VPD_original_QC",
    "flags", "science_route", "external_CDS_source_verified",
    "approved_for_DATM",
]
SCREEN = [
    "HARD_PHYSICS_UNION", "EXTREME_DRY_REVIEW_UNION",
    "RH_INFERRED_LT0", "RH_RAW_NEGATIVE", "RH_RAW_ZERO", "RH_RAW_GT100",
    "WATER_NEG_VPD_SEVERE", "RH_RAW_LT1_POS", "HARD_WITH_TA_QC0",
    "HARD_WITH_VPD_QC0", "RH_FIELD_MISSING_RECORDS",
]


def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def load_stage48():
    if not STAGE48.is_file() or STAGE48.is_symlink():
        raise RuntimeError("Pinned Stage48 sibling script is missing or symlinked")
    actual = git_blob_sha(STAGE48)
    if actual != STAGE48_BLOB:
        raise RuntimeError("Stage48 Git blob mismatch: " + actual)
    spec = importlib.util.spec_from_file_location("batch02_stage48_pinned", STAGE48)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def route(site, flags, i, tq, rh):
    hard = bool(flags["HARD_PHYSICS_UNION"][i])
    dry = bool(flags["EXTREME_DRY_REVIEW_UNION"][i])
    if not hard and dry:
        return "MANUAL_EXTREME_POSITIVE_DRYNESS_NO_AUTO_REPAIR"
    # Slight RH >100% can reflect phase/saturation conventions. It is a
    # numeric screen, NOT automatic evidence of an impossible atmosphere.
    raw_only_phase = (
        bool(flags["RH_RAW_GT100"][i]) and np.isfinite(rh) and rh <= 101
        and not any(bool(flags[k][i]) for k in (
            "RH_INFERRED_LT0", "ACTUAL_VAPOR_NONPOSITIVE",
            "RH_RAW_ZERO", "RH_RAW_NEGATIVE", "WATER_NEG_VPD_SEVERE"))
    )
    if raw_only_phase:
        return "MANUAL_NEAR_SATURATION_OR_PHASE_REVIEW"
    if site == "US-Ho1":
        return "HOLD_HO1_TEMPERATURE_AND_HUMIDITY_PROVENANCE"
    if not np.isfinite(tq):
        return "HOLD_TEMPERATURE_QC_UNAVAILABLE"
    if tq == 2:
        return "MANUAL_JOINT_T_AND_HUMIDITY_QC2"
    if tq != 0:
        return "MANUAL_T_AND_HUMIDITY_QC_NOT_ZERO"
    return "EXTERNAL_CDS_AND_SOURCE_VERIFICATION_REQUIRED_NOT_APPROVED"


def val(x):
    return "" if not np.isfinite(x) else float(x)


def run_site(mod, spec, writer, site_counts, years, chunksize):
    site = spec["site"]
    src = Path(spec["file"])
    if not src.is_file() or src.is_symlink():
        raise ValueError("Missing/nonregular primary: " + str(src))
    digest = mod.sha256(src)
    if digest != spec["sha256"]:
        raise ValueError("Original Stage04b primary SHA256 changed: " + site)
    columns = spec["columns"]
    qc_columns = spec.get("qc_columns", {})
    head = set(pd.read_csv(src, nrows=0).columns)
    rh_name = "RH" if "RH" in head else None
    use = ["TIMESTAMP_START", "TIMESTAMP_END"] + [
        columns[k] for k in ("TA", "VPD", "PA")
    ]
    if rh_name:
        use.append(rh_name)
    for k in ("TA", "VPD"):
        q = qc_columns.get(k)
        if q and q in head:
            use.append(q)
    use = list(dict.fromkeys(use))
    prior = None
    offset = 0
    step = mod.SITE_STEPS[site]
    for chunk in pd.read_csv(src, usecols=use, dtype="string", chunksize=chunksize):
        start_txt = chunk["TIMESTAMP_START"].str.strip().str.replace(
            r"\.0$", "", regex=True)
        end_txt = chunk["TIMESTAMP_END"].str.strip().str.replace(
            r"\.0$", "", regex=True)
        start = pd.to_datetime(start_txt, format="%Y%m%d%H%M", errors="coerce")
        end = pd.to_datetime(end_txt, format="%Y%m%d%H%M", errors="coerce")
        if start.isna().any() or end.isna().any():
            raise ValueError("Invalid original timestamp " + site)
        if ((end-start).dt.total_seconds() != 60 * step).any():
            raise ValueError("Invalid original HH/HR interval " + site)
        if (start.dt.year < int(spec["first_year"])).any() or (
                start.dt.year > int(spec["last_year"])).any():
            raise ValueError("Timestamp outside release period " + site)
        if prior is not None and start.iloc[0] <= prior:
            raise ValueError("Nonmonotone boundary " + site)
        if (start.diff().dropna() <= pd.Timedelta(0)).any():
            raise ValueError("Duplicate/nonmonotone timestamp " + site)
        prior = start.iloc[-1]
        ta = mod.number(chunk[columns["TA"]])
        vpd = mod.number(chunk[columns["VPD"]])
        pa = mod.number(chunk[columns["PA"]])
        rh = mod.number(chunk[rh_name]) if rh_name else np.full(len(chunk), np.nan)
        tq_name = qc_columns.get("TA")
        vq_name = qc_columns.get("VPD")
        tq = (mod.number(chunk[tq_name]) if tq_name in chunk
              else np.full(len(chunk), np.nan))
        vq = (mod.number(chunk[vq_name]) if vq_name in chunk
              else np.full(len(chunk), np.nan))
        masks, inferred = mod.classify(ta, vpd, pa, rh, tq, vq)
        selected = np.flatnonzero(
            masks["HARD_PHYSICS_UNION"] | masks["EXTREME_DRY_REVIEW_UNION"])
        for i in selected:
            i = int(i)
            year = int(start.iloc[i].year)
            flags = "|".join(k for k in mod.LABELS
                             if k not in ("HARD_PHYSICS_UNION",
                                          "EXTREME_DRY_REVIEW_UNION")
                             and masks[k][i])
            science_route = route(site, masks, i, tq[i], rh[i])
            writer.writerow([
                site, spec["source"], digest, offset + i + 2,
                str(start_txt.iloc[i]), str(end_txt.iloc[i]), year, step,
                val(ta[i]), val(vpd[i]), val(pa[i]), val(rh[i]),
                val(inferred[i]), val(tq[i]), val(vq[i]), flags,
                science_route, False, False
            ])
            site_counts[site]["ROW_LEVEL_REVIEW"] += 1
            site_counts[site]["ROUTE_" + science_route] += 1
            years[(site, year)]["ROW_LEVEL_REVIEW"] += 1
        for k in SCREEN:
            n = int(masks[k].sum())
            site_counts[site][k] += n
            for yr, num in Counter(start.dt.year[masks[k]].tolist()).items():
                years[(site, int(yr))][k] += int(num)
        site_counts[site]["ORIGINAL_ROWS"] += len(chunk)
        offset += len(chunk)
    if offset != int(spec["source_records"]):
        raise ValueError("Stage04b original source row count changed: " + site)
    if mod.sha256(src) != digest:
        raise ValueError("Original source SHA256 changed during scan: " + site)
    return digest


def write_summary(path, counts, columns):
    with path.open("w", newline="", encoding="utf-8") as out:
        w = csv.DictWriter(out, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for row in counts:
            w.writerow(row)


def test(mod):
    t = np.array([10., 10., 10., 10.])
    v = np.array([20., 1., 1., 1.])
    p = np.array([98., 98., 98., 98.])
    r = np.array([np.nan, .2, 100.2, 50.])
    tq = np.array([0., 2., 0., np.nan])
    masks, _ = mod.classify(t, v, p, r, tq)
    assert route("US-CMW", masks, 0, tq[0], r[0]).startswith("EXTERNAL_CDS_")
    assert route("US-CMW", masks, 1, tq[1], r[1]).startswith("MANUAL_EXTREME_")
    # Isolate a mild raw RH supersaturation case without derived hard errors.
    assert route("US-CMW", masks, 2, tq[2], r[2]) == (
        "MANUAL_NEAR_SATURATION_OR_PHASE_REVIEW")
    assert route("US-Ho1", masks, 0, tq[0], r[0]).startswith("HOLD_HO1_")
    assert git_blob_sha(STAGE48) == STAGE48_BLOB
    print("STAGE49 SELF-TEST PASS | pinned Stage48, review routing, phase and QC2")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    modes = ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--audit", action="store_true")
    ap.add_argument("--inventory", type=Path)
    ap.add_argument("--report-root", type=Path, default=EXPERIMENT / "reports")
    ap.add_argument("--chunksize", type=int, default=100000)
    opt = ap.parse_args()
    mod = load_stage48()
    if opt.self_test:
        test(mod)
        return
    if opt.inventory is None:
        ap.error("--inventory is required for --check/--audit")
    if opt.chunksize < 1000:
        ap.error("--chunksize must be >=1000")
    specs = mod.load_inventory(opt.inventory)
    inventory_sha_at_start = mod.sha256(opt.inventory)
    if opt.check:
        print("STAGE49 CHECK PASS | Stage48 blob and 10 Stage04b primary entries")
        for x in specs:
            print("READY", x["site"], x["source"], x["sha256"])
        return
    root = opt.report_root.resolve()
    raw = mod.ROOT.resolve()
    if root == raw or raw in root.parents or root == raw.parent:
        raise ValueError("Report root cannot be inside raw primary source area")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = root / ("stage49_original_humidity_review_" + timestamp
                   + "_" + uuid.uuid4().hex[:8])
    dest.mkdir(parents=True, exist_ok=False)
    marker = dest / "INCOMPLETE_DO_NOT_USE"
    marker.write_text("Unfinished Stage49; not scientific approval.\n")
    site_counts = {s: Counter() for s in mod.SITES}
    from collections import defaultdict
    year_counts = defaultdict(Counter)
    checksums = {}
    with (dest / "original_humidity_event_review.csv").open(
            "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        for x in specs:
            sha = run_site(mod, x, writer, site_counts, year_counts, opt.chunksize)
            checksums[x["site"]] = sha
            print("SITE", x["site"], "original rows",
                  site_counts[x["site"]]["ORIGINAL_ROWS"],
                  "hard", site_counts[x["site"]]["HARD_PHYSICS_UNION"],
                  "dry under 1", site_counts[x["site"]]["EXTREME_DRY_REVIEW_UNION"],
                  "unique review", site_counts[x["site"]]["ROW_LEVEL_REVIEW"])
    summary_columns = ["site"] + ["ORIGINAL_ROWS", "ROW_LEVEL_REVIEW"] + SCREEN
    summary_columns += sorted(set(k for v in site_counts.values() for k in v
                                  if k.startswith("ROUTE_")))
    write_summary(dest / "site_science_screen_summary.csv", [
        {"site": s, **site_counts[s]} for s in mod.SITES], summary_columns)
    annual_columns = ["site", "year", "ROW_LEVEL_REVIEW"] + SCREEN
    write_summary(dest / "year_science_screen_summary.csv", [
        {"site": site, "year": year, **counts}
        for (site, year), counts in sorted(year_counts.items())], annual_columns)
    totals = Counter()
    for c in site_counts.values():
        totals.update(c)
    if totals["ORIGINAL_ROWS"] <= 0 or totals["ROW_LEVEL_REVIEW"] < totals["HARD_PHYSICS_UNION"]:
        raise ValueError("Invalid review accounting")
    if mod.sha256(opt.inventory) != inventory_sha_at_start:
        raise ValueError("Stage04b inventory changed during audit")
    provenance = {
        "status": "REVIEW_ONLY_NO_DATM_APPROVAL",
        "stage48_blob_sha1": STAGE48_BLOB,
        "inventory": str(opt.inventory),
        "inventory_sha256": inventory_sha_at_start,
        "primary_sha256_by_site": checksums,
        "totals": dict(totals),
        "stage08_hold_cohort_not_joined": 4884,
        "external_CDS_verified": False,
        "approved_for_DATM": False,
        "notes": "Raw RH >100 and cold water/ice phase need review; "
                 "QC0 does not independently establish truth; no forcing edits."
    }
    (dest / "provenance_and_hold.json").write_text(
        json.dumps(provenance, sort_keys=True, indent=2) + "\n")
    marker.unlink()
    print("STAGE49 AUDIT PASS | report", dest)
    print("TOTAL hard", totals["HARD_PHYSICS_UNION"],
          "positive raw RH <1%", totals["EXTREME_DRY_REVIEW_UNION"],
          "unique review", totals["ROW_LEVEL_REVIEW"])
    print("NO approved ERA repairs; no source, forcing or model changes")


if __name__ == "__main__":
    main()
