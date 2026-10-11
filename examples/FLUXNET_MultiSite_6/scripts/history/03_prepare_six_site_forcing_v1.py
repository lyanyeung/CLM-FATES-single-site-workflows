#!/usr/bin/env python3
"""Secondary QC for six ICOS/FLUXNET FLUXMET_HH sites (read-only originals).

Keep the official FLUXNET _F series (measured / MDS gapfill / downscaled ERA).
Repair ONLY unmistakable physical errors and strongly corroborated isolated spikes.
Fill newly missing small gaps by limited interpolation (not precipitation), then
remaining gaps using FLUXNET's site-downscaled *_ERA companion series.
Flag uncertain physical extremes for manual review; DO NOT silently ERA-replace.
This does not download ERA5-Land, set ZBOT, create DATM NetCDF, or submit jobs.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SITE_YEARS = {
    "DE-Hai": (2000, 2025),
    "RU-Fyo": (1998, 2025),
    "DE-Tha": (1996, 2025),  # 2026 contains future/missing data
    "DK-Sor": (1996, 2024),
    "NL-Loo": (1997, 2025),  # 2026 contains future/missing data
    "IL-Yat": (2000, 2024),
}
VARS = ["TA_F", "VPD_F", "PA_F", "SW_IN_F", "LW_IN_F", "WS_F", "P_F"]
ERA_NAMES = {k: k.removesuffix("_F") + "_ERA" for k in VARS}
# Very broad automatic-failure ranges; not biome-specific screening thresholds.
HARD = {
    "TA_F": (-80.0, 65.0),      # Celsius
    "VPD_F": (-0.1, 125.0),     # hPa
    "PA_F": (50.0, 110.0),      # kPa
    "SW_IN_F": (-5.0, 1600.0),  # W/m2
    "LW_IN_F": (60.0, 800.0),   # W/m2
    "WS_F": (-0.1, 75.0),      # m/s
    "P_F": (-0.001, 300.0),    # mm / 30 minutes
}
# Review only; a cold winter can cause low LW and real extremes can differ from ERA.
REVIEW = {
    "TA_F": (-55.0, 52.0),
    "LW_IN_F": (100.0, 700.0),
    "WS_F": (0.0, 45.0),
    "VPD_F": (0.0, 100.0),
}
SMALL_NEGATIVE = {"SW_IN_F": 5.0, "WS_F": 0.1, "P_F": 0.001, "VPD_F": 0.1}
INTERPOLATE = {"TA_F": 4, "VPD_F": 4, "PA_F": 4, "SW_IN_F": 2,
               "LW_IN_F": 4, "WS_F": 4, "P_F": 0}


def save_csv_atomic(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".partial")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def get_one(root, glob):
    candidates = sorted(root.rglob(glob))
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one {glob} under {root}; found {len(candidates)}")
    return candidates[0]


def norm_time(series):
    raw = series.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    return pd.to_datetime(raw, format="%Y%m%d%H%M", errors="raise")


def get_segments(mask):
    x = np.asarray(mask, dtype=bool)
    starts_ends = np.diff(np.r_[False, x, False].astype("int8"))
    return zip(np.where(starts_ends == 1)[0], np.where(starts_ends == -1)[0])


def acceptable_era(v, name):
    lo, hi = HARD[name]
    # Tighter longwave minimum for ERA validation than absolute positivity.
    if name == "LW_IN_F":
        lo = 70
    return v.notna() & v.between(lo, hi)


def saturation_hpa(t_c):
    return 6.112 * np.exp(17.67 * t_c / (t_c + 243.5))


def humidity_bad(temp, vpd):
    es = saturation_hpa(temp)
    ea = es - vpd
    rh = 100.0 * ea / es
    return (temp.notna() & vpd.notna() &
            ((ea <= 0) | (rh < 1.0) | (rh > 100.05) | ~np.isfinite(rh)))


def parse_site(site, root, output_root):
    start, end = SITE_YEARS[site]
    site_root = root / site
    raw_root = site_root / "forcing" / "raw"
    flux_path = get_one(raw_root, "*FLUXMET_HH*.csv")
    era_path = get_one(raw_root, "*ERA5_HH*.csv")
    print(f"  FLUXMET: {flux_path}", flush=True)
    print(f"  ERA5 HH: {era_path}", flush=True)

    header = set(pd.read_csv(flux_path, nrows=0).columns)
    required = ["TIMESTAMP_START", *VARS]
    absent = sorted(set(required) - header)
    if absent:
        raise RuntimeError(f"Missing required FLUXMET columns: {absent}")
    flux_columns = required + [v+"_QC" for v in VARS if v+"_QC" in header]
    flux_columns += [name for name in ERA_NAMES.values() if name in header]
    d = pd.read_csv(flux_path, usecols=list(dict.fromkeys(flux_columns)), low_memory=False)
    d["time"] = norm_time(d["TIMESTAMP_START"])
    d = d[(d.time.dt.year >= start) & (d.time.dt.year <= end)].copy()
    d = d[~((d.time.dt.month == 2) & (d.time.dt.day == 29))].copy()
    d.sort_values("time", inplace=True)
    d.reset_index(drop=True, inplace=True)
    if d.time.duplicated().any():
        raise RuntimeError("FLUXMET timestamps are duplicated")
    expected = pd.date_range(f"{start}-01-01", f"{end}-12-31 23:30", freq="30min")
    expected = expected[~((expected.month == 2) & (expected.day == 29))]
    if len(d) != len(expected) or not np.array_equal(d.time.values, expected.values):
        raise RuntimeError("FLUXMET not a complete NO_LEAP 30-minute timeline")

    eheader = set(pd.read_csv(era_path, nrows=0).columns)
    missing_era_cols = [col for col in ERA_NAMES.values() if col not in header]
    use_era = [x for x in missing_era_cols if x in eheader]
    if use_era:
        if "TIMESTAMP_START" not in eheader:
            raise RuntimeError("ERA5_HH has no TIMESTAMP_START")
        era = pd.read_csv(era_path, usecols=["TIMESTAMP_START", *use_era], low_memory=False)
        era["time"] = norm_time(era.TIMESTAMP_START)
        era = era[(era.time.dt.year >= start) & (era.time.dt.year <= end)]
        era = era[~((era.time.dt.month == 2) & (era.time.dt.day == 29))]
        if era.time.duplicated().any():
            raise RuntimeError("ERA5_HH duplicate timestamps")
        d = d.merge(era[["time", *use_era]], on="time", how="left", validate="one_to_one")

    # Re-check provided columns and missing-value conventions.
    for col in [*VARS, *ERA_NAMES.values()]:
        if col not in d.columns:
            d[col] = np.nan
        d[col] = pd.to_numeric(d[col], errors="coerce")
        d.loc[(d[col] <= -9990) | ~np.isfinite(d[col]), col] = np.nan
    for var in VARS:
        qc = var+"_QC"
        if qc not in d:
            d[qc] = np.nan
        d[qc] = pd.to_numeric(d[qc], errors="coerce")
        d.loc[d[qc] <= -9990, qc] = np.nan

    original = {v: d[v].copy() for v in VARS}
    current = {v: d[v].copy() for v in VARS}
    source = {}
    for v in VARS:
        labels = {0: "official_measured", 1: "official_gapfilled", 2: "official_era"}
        source[v] = d[v+"_QC"].map(labels).fillna("official_unknown")
        source[v] = source[v].mask(current[v].isna(), "initial_missing")

    reasons = {v: pd.Series("", index=d.index, dtype="object") for v in VARS}
    def mark(var, loc, reason):
        where = np.flatnonzero(np.asarray(loc, dtype=bool))
        if len(where):
            old = reasons[var].iloc[where]
            reasons[var].iloc[where] = np.where(old.eq(""), reason, old + "|" + reason)
        return len(where)

    # Reset unmistakably impossible readings; never replace only on ERA difference.
    for v in VARS:
        lo, hi = HARD[v]
        bad = current[v].notna() & ~current[v].between(lo, hi)
        if bad.any():
            mark(v, bad, "hard_physical_range")
            current[v] = current[v].mask(bad)
        if v in SMALL_NEGATIVE:
            small = current[v].notna() & current[v].between(-SMALL_NEGATIVE[v], 0, inclusive="left")
            if small.any():
                mark(v, small, "tiny_negative_to_zero")
                current[v] = current[v].mask(small, 0.0)
                source[v] = source[v].mask(small, "small_negative_clipped")

    # Strong isolated anomaly: both adjacent records agree with each other,
    # ERA agrees with the neighbors, and the tested point is far from BOTH.
    for v, delta, neighbor_agreement, era_agreement in [
        ("TA_F", 18, 8, 10), ("LW_IN_F", 120, 55, 70)
    ]:
        x, e = current[v], d[ERA_NAMES[v]]
        left, right = x.shift(1), x.shift(-1)
        # Avoid crossing calendar years or discontinuities at source boundaries.
        mid = (left + right) / 2
        same_year = (d.time.dt.year.eq(d.time.shift(1).dt.year) &
                     d.time.dt.year.eq(d.time.shift(-1).dt.year))
        spike = (x.notna() & left.notna() & right.notna() & same_year &
                 acceptable_era(e, v) &
                 ((left - right).abs() < neighbor_agreement) &
                 ((x - mid).abs() > delta) & ((e - mid).abs() < era_agreement))
        if spike.any():
            mark(v, spike, "isolated_spike_ERA_confirmed")
            current[v] = x.mask(spike)

    # Physically incompatible temperature and vapor pressure deficit require
    # coherent repair: treat the pair together, not VPD alone.
    pair_bad = humidity_bad(current["TA_F"], current["VPD_F"])
    if pair_bad.any():
        for v in ("TA_F", "VPD_F"):
            mark(v, pair_bad, "TA_VPD_inconsistent")
            current[v] = current[v].mask(pair_bad)

    # True short-gap interpolation: runs larger than limit are NEVER partly
    # interpolated; need two usable boundary observations.
    for v in VARS:
        limit = INTERPOLATE[v]
        x = current[v]
        if limit == 0:
            continue
        fill = x.interpolate(method="linear", limit_area="inside")
        good = np.zeros(len(x), dtype=bool)
        for a, b in get_segments(x.isna()):
            if (b - a <= limit and a > 0 and b < len(x) and
                pd.notna(x.iloc[a-1]) and pd.notna(x.iloc[b])):
                # Never cross a calendar/forcing-year boundary for interpolation.
                if d.time.iloc[a-1].year == d.time.iloc[b].year:
                    good[a:b] = True
        newval = fill.where(good)
        valid = good & acceptable_era(newval, v).to_numpy()
        if valid.any():
            current[v] = x.mask(valid, newval)
            source[v] = source[v].mask(valid, "local_short_interpolation")
            mark(v, valid, "short_gap_interpolated")

    # Remaining gaps, including long runs, from companion site-downscaled ERA.
    for v in VARS:
        missing = current[v].isna()
        era_v = d[ERA_NAMES[v]]
        usable = missing & acceptable_era(era_v, v)
        if usable.any():
            current[v] = current[v].mask(usable, era_v)
            source[v] = source[v].mask(usable, "secondary_era_replacement")
            mark(v, usable, "remaining_gap_filled_ERA")
        left = int(current[v].isna().sum())
        if left:
            raise RuntimeError(f"{v}: {left} missing after interpolation/ERA (cannot generate safe DATM)")

    # Final temperature/humidity check. If inconsistent after independent
    # repair, replace both with a physically consistent ERA pair.
    bad = humidity_bad(current["TA_F"], current["VPD_F"])
    if bad.any():
        era_t, era_v = d["TA_ERA"], d["VPD_ERA"]
        validpair = acceptable_era(era_t, "TA_F") & acceptable_era(era_v, "VPD_F")
        validpair &= ~humidity_bad(era_t, era_v)
        if (bad & ~validpair).any():
            raise RuntimeError(f"{int((bad & ~validpair).sum())} invalid humidity pairs cannot be repaired by ERA")
        for v in ("TA_F", "VPD_F"):
            current[v] = current[v].mask(bad, d[ERA_NAMES[v]])
            source[v] = source[v].mask(bad, "secondary_era_replacement")
            mark(v, bad, "final_TA_VPD_joint_ERA")

    # Flag scientifically ambiguous readings without silently overwriting.
    manual = []
    for v, (lo, hi) in REVIEW.items():
        series, era_v = current[v], d[ERA_NAMES[v]]
        candidates = series.notna() & ~series.between(lo, hi)
        for i in np.flatnonzero(candidates.to_numpy()):
            av = float(era_v.iloc[i]) if pd.notna(era_v.iloc[i]) else None
            manual.append({"site": site, "time": d.time.iloc[i].isoformat(),
                           "variable": v, "final_value": float(series.iloc[i]),
                           "era_value": av,
                           "difference_to_era": float(series.iloc[i]-av) if av is not None else None,
                           "previous_value": float(series.iloc[i-1]) if i > 0 and pd.notna(series.iloc[i-1]) else None,
                           "next_value": float(series.iloc[i+1]) if i+1 < len(series) and pd.notna(series.iloc[i+1]) else None,
                           "official_qc": d[v+"_QC"].iloc[i],
                           "reason": "outside_review_range_kept_not_replaced"})

    out_qc = output_root / site / "forcing" / "qc"
    out_proc = output_root / site / "forcing" / "processed"
    events = []
    stats = []
    for v in VARS:
        changed = (~(original[v].eq(current[v]) | (original[v].isna() & current[v].isna()))).fillna(True)
        for i in np.flatnonzero(changed.to_numpy()):
            a, b, era = original[v].iloc[i], current[v].iloc[i], d[ERA_NAMES[v]].iloc[i]
            events.append({"site": site, "time": d.time.iloc[i].isoformat(),
                           "variable": v,
                           "original_value": float(a) if pd.notna(a) else None,
                           "era_reference": float(era) if pd.notna(era) else None,
                           "final_value": float(b) if pd.notna(b) else None,
                           "official_qc": d[v+"_QC"].iloc[i],
                           "final_source": source[v].iloc[i], "reason": reasons[v].iloc[i]})
        record = {"site": site, "variable": v, "count": len(d),
                  "changed_count": int(changed.sum()), "original_missing": int(original[v].isna().sum()),
                  "final_missing": int(current[v].isna().sum()),
                  "manual_review_count": sum(q["variable"] == v for q in manual)}
        for key, value in source[v].value_counts().items():
            record[key + "_count"] = int(value)
        stats.append(record)

    # Convert to forcing convention (VPD hPa, PA kPa, P mm/half-hour).
    es = saturation_hpa(current["TA_F"])
    ea_pa = (es - current["VPD_F"]) * 100
    psrf = current["PA_F"] * 1000
    qbot = 0.622 * ea_pa / (psrf - 0.378 * ea_pa)
    forc = pd.DataFrame({"time": d.time.dt.strftime("%Y-%m-%d %H:%M:%S"),
                         "TBOT": current["TA_F"] + 273.15,
                         "QBOT": qbot, "PSRF": psrf,
                         "FSDS": current["SW_IN_F"].clip(lower=0),
                         "FLDS": current["LW_IN_F"],
                         "WIND": current["WS_F"].clip(lower=0),
                         "PRECTmms": current["P_F"].clip(lower=0) / 1800,
                         "TA_USE": current["TA_F"], "VPD_USE": current["VPD_F"]})
    check_ranges = {"TBOT": (180, 340), "QBOT": (0, 0.08),
                    "PSRF": (49000, 111000), "FSDS": (0, 1600),
                    "FLDS": (0, 800), "WIND": (0, 75),
                    "PRECTmms": (0, 300/1800)}
    for col, (lo, hi) in check_ranges.items():
        if (~np.isfinite(forc[col])).any() or not forc[col].between(lo, hi).all():
            ix = np.flatnonzero(~forc[col].between(lo, hi).to_numpy())[:5]
            raise RuntimeError(f"Final {col} fails sanity at rows {ix.tolist()}; investigate before DATM")

    save_csv_atomic(pd.DataFrame(events, columns=["site", "time", "variable", "original_value",
                        "era_reference", "final_value", "official_qc", "final_source", "reason"]),
                    out_qc / f"{site}_replacement_events.csv")
    save_csv_atomic(pd.DataFrame(manual, columns=["site", "time", "variable", "final_value",
                        "era_value", "difference_to_era", "previous_value", "next_value", "official_qc", "reason"]),
                    out_qc / f"{site}_manual_review.csv")
    save_csv_atomic(pd.DataFrame(stats), out_qc / f"{site}_qc_summary.csv")
    target = out_proc / f"{site}_CLM_forcing_{start}_{end}.csv"
    save_csv_atomic(forc, target)
    status = {"site": site, "first_year": start, "last_year": end,
              "noleap_rows": len(forc), "status": "REVIEW" if manual else "PASS",
              "manual_review_records": len(manual), "changes": len(events),
              "forcing_csv": str(target),
              "FLUXMET_file": str(flux_path), "ERA5_HH_file": str(era_path),
              "script_version": "2026-10-11.a",
              "reanalysis": "FLUXNET site-downscaled ERA5_HH, not independently downloaded ERA5-Land",
              "forcing_era_gap_rule": "short 1-4 half-hours interpolated (shortwave <=2); precipitation ERA only",
              "ZBOT": "not assigned: verify BIFVARINFO before DATM creation"}
    out_qc.mkdir(parents=True, exist_ok=True)
    (out_qc / f"{site}_status.json").write_text(json.dumps(status, indent=2))
    print(f"  RESULT: {status['status']}; {len(forc)} rows; {len(events)} changes; "
          f"{len(manual)} review records", flush=True)
    return status


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
    ap.add_argument("--output-root", type=Path, help="Defaults to --root; leaves raw and surface untouched")
    ap.add_argument("--sites", nargs="+", choices=sorted(SITE_YEARS), default=list(SITE_YEARS))
    args = ap.parse_args()
    results = []
    for site in args.sites:
        print("\n=== " + site + " ===", flush=True)
        try:
            status = parse_site(site, args.root, args.output_root or args.root)
            results.append(status)
        except Exception as exc:
            print(f"  ERROR {site}: {exc}", file=sys.stderr, flush=True)
            status_path = ((args.output_root or args.root) / site / "forcing" /
                           "qc" / f"{site}_status.json")
            status_path.parent.mkdir(parents=True, exist_ok=True)
            status_path.write_text(json.dumps({"site": site, "status": "FAIL", "error": str(exc)}, indent=2))
            results.append({"site": site, "status": "FAIL", "error": str(exc)})
    print("\n=== SIX-SITE SUMMARY ===")
    for x in results:
        print(f"{x['site']:8s} {x['status']:6s} {x.get('changes','-')} modifications; "
              f"{x.get('manual_review_records','-')} to review")
    if any(x["status"] == "FAIL" for x in results):
        sys.exit(1)
    if any(x["status"] == "REVIEW" for x in results):
        print("REVIEW records exist: inspect each site's forcing/qc/*manual_review.csv before DATM.")
    else:
        print("All six sites passed this secondary QC; still verify ZBOT before DATM.")

if __name__ == "__main__":
    main()
