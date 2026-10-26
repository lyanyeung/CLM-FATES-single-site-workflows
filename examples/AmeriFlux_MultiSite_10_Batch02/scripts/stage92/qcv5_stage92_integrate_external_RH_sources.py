#!/usr/bin/env python3
"""Native HH/HR adaptation of the historical eight-site QC-v5 candidate engine.

Derived from examples/FLUXNET_MultiSite_8/scripts/03_prepare_eight_site_forcing_v5.py.
Only native-grid duration/rate handling and explicit standalone ERA selection
are generalized. Repair thresholds, ordering, RH reconstruction and the
reviewed 1% ERA-RH floor retain the historical algorithm. The Batch02 driver
pins exact sources and audits candidates; this module is never run directly.

Historical method notes:

Keep the official FLUXNET _F series (measured / MDS gapfill / downscaled ERA).
Repair ONLY unmistakable physical errors and strongly corroborated isolated spikes.
V5: Retain v4 corrections and distinguish highly suspicious near-zero
actual vapour pressure episodes from potentially real dry extremes. When site
RH <1% (or negligibly negative from rounding), implied vapour pressure <0.1 hPa, ERA RH >=50%, and measured/site
TA agrees with ERA TA within 8 C, use ERA RH at preserved site TA as a
candidate correction (and ALWAYS require manual review). Less decisive
cases are not changed and remain flagged. The strong-repair rule is an
explicit research choice, not verification of a defective sensor.
Write all v5 results to *processed_v5/*qc_v5; never overwrite v1 or v2 results.
Fill newly missing small gaps by limited interpolation (not precipitation), then
remaining gaps using FLUXNET's site-downscaled *_ERA companion series.
Flag uncertain physical extremes for manual review; DO NOT silently ERA-replace.
This does not download ERA5-Land, set ZBOT, create DATM NetCDF, or submit jobs.
"""
import argparse
from collections import Counter
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SITE_YEARS = {
    "CZ-BK1": (2004, 2025),
    "IT-Ren": (1999, 2025),
    "FR-Hes": (1997, 2025),
    "FR-FBn": (2008, 2024),
    "DE-Hzd": (2010, 2025),
    "CH-Dav": (1997, 2025),
    "BE-Vie": (1996, 2025),
    "IT-Lav": (2003, 2020),
}
STAGE92_SCOPED = {}  # injected by exact SHA-gated Stage92 driver; empty is original behaviour

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
    # True physical impossibility only: do not declare low but positive RH an
    # error, especially at arid sites. Values below 1% are reviewed separately.
    return (temp.notna() & vpd.notna() &
            ((ea <= 0) | (rh > 100.05) | ~np.isfinite(rh)))


def parse_site(site, root, output_root, native_minutes=30, standalone_era=False):
    if native_minutes not in (30, 60):
        raise ValueError("Native interval must be 30 or 60 minutes")
    native_seconds = native_minutes * 60
    start, end = SITE_YEARS[site]
    site_root = root / site
    raw_root = site_root / "forcing" / "raw"
    flux_path = get_one(raw_root, "*FLUXMET_HH*.csv")
    era_path = get_one(raw_root, "*ERA5_HH*.csv")
    print(f"  FLUXMET: {flux_path}", flush=True)
    print(f"  ERA5 companion ({native_minutes} min): {era_path}", flush=True)

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
    expected = pd.date_range(f"{start}-01-01", f"{end+1}-01-01",
                             freq=f"{native_minutes}min", inclusive="left")
    expected = expected[~((expected.month == 2) & (expected.day == 29))]
    if len(d) != len(expected) or not np.array_equal(d.time.values, expected.values):
        raise RuntimeError(f"Primary is not a complete NO_LEAP {native_minutes}-minute timeline")

    eheader = set(pd.read_csv(era_path, nrows=0).columns)
    missing_era_cols = (list(ERA_NAMES.values()) if standalone_era else
                        [col for col in ERA_NAMES.values() if col not in header])
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
        if standalone_era:
            d.drop(columns=list(ERA_NAMES.values()), errors="ignore", inplace=True)
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

    # Before TA/VPD consistency checks, detect joint sensor or gap-fill
    # artifacts. A long plateau of exactly TA=0 and VPD=6.110 (near es(0))
    # produces nearly 0% RH, especially suspicious when ERA indicates moist
    # winter air. Also flag warm-season TA=0 where ERA is >18 C and site VPD
    # is already above the saturated VPD limit at the reported TA.
    # These rules need MULTIPLE corroborating features and are audited.
    flatline_reviews = []
    t0 = current["TA_F"]
    v0 = current["VPD_F"]
    et = d["TA_ERA"]
    ev = d["VPD_ERA"]
    era_pair_ok = (acceptable_era(et, "TA_F") &
                   acceptable_era(ev, "VPD_F") &
                   ~humidity_bad(et, ev) &
                   (ev >= 0))
    es_zero = float(saturation_hpa(0.0))
    paired_zero = (t0.notna() & v0.notna() &
                   t0.abs().le(0.0005) &
                   (v0 - 6.110).abs().le(0.008) &
                   era_pair_ok &
                   ev.lt(2.5) &
                   (v0 - ev).abs().gt(3.0))
    plateau = np.zeros(len(d), dtype=bool)
    for a, b in get_segments(paired_zero):
        # At least three consecutive hours; never assume a single 0 C is bad.
        if b - a >= 180 // native_minutes and (d.time.iloc[b-1] - d.time.iloc[a] ==
                           pd.Timedelta(minutes=native_minutes*(b-a-1))):
            plateau[a:b] = True
    hot_zero = (t0.notna() & v0.notna() &
                t0.abs().le(0.0005) &
                et.gt(18) & (et - t0).gt(15) &
                v0.gt(es_zero + 1) & era_pair_ok)
    # A lone 0 C is insufficient; require an adjacent matching 0 C.
    z = t0.notna() & t0.abs().le(0.0005)
    hot_zero = hot_zero & (z.shift(1, fill_value=False) |
                            z.shift(-1, fill_value=False))
    # Strong warm mismatch: adjust temperature ONLY, retaining observed/filled
    # VPD if it is physically valid at the corrected temperature.
    if hot_zero.any():
        current["TA_F"] = t0.mask(hot_zero, et)
        source["TA_F"] = source["TA_F"].mask(hot_zero,
                                             "era_temperature_zero_dropout")
        mark("TA_F", hot_zero, "warm_zero_TA_sensor_error_ERA_repaired")
        for i in np.flatnonzero(hot_zero.to_numpy()):
            flatline_reviews.append({
                "site": site, "time": d.time.iloc[i].isoformat(),
                "variable": "TA_F", "final_value": float(current["TA_F"].iloc[i]),
                "era_value": float(et.iloc[i]), "difference_to_era": 0.0,
                "previous_value": float(t0.iloc[i-1]) if i else None,
                "next_value": float(t0.iloc[i+1]) if i+1 < len(d) else None,
                "official_qc": d["TA_F_QC"].iloc[i],
                "reason": "warm_zero_TA_replaced_ERA_check_local_station_metadata"
            })
    # A multi-hour pairing of TA=0 with VPD~6.110 hPa indicates a VPD
    # flatline/placeholder, but winter TA=0 C may still be real (for instance,
    # when ERA TA is around 0 C). Preserve the site air temperature unless
    # a separate, strong independent temperature anomaly test is satisfied.
    # Rebuild ONLY VPD using ERA's saturation-deficit fraction at site TA:
    #   VPD_new = es(TA_site) * VPD_ERA / es(TA_ERA)
    # Thus the resulting RH follows the ERA humidity while the reasonable
    # site temperature is preserved. Every corrected point remains REVIEW.
    if plateau.any():
        var = "VPD_F"
        reconstructed = saturation_hpa(current["TA_F"]) * (
            ev / saturation_hpa(et)
        )
        # All plateau ERA pairs are pre-screened (era_pair_ok).
        es_site = saturation_hpa(current["TA_F"])
        permitted = reconstructed.notna() & reconstructed.ge(0) & reconstructed.lt(es_site)
        if not permitted.loc[plateau].all():
            raise RuntimeError("ERA-RH plateau reconstruction failed physical check")
        current[var] = current[var].mask(plateau, reconstructed)
        source[var] = source[var].mask(plateau, "era_RH_at_retained_tower_TA")
        mark(var, plateau, "zero_TA_6p110_plateau_VPD_only_ERA_RH")
        for i in np.flatnonzero(plateau):
            flatline_reviews.append({
                "site": site, "time": d.time.iloc[i].isoformat(),
                "variable": var, "final_value": float(current[var].iloc[i]),
                "era_value": float(ev.iloc[i]),
                "difference_to_era": float(current[var].iloc[i] - ev.iloc[i]),
                "previous_value": float(v0.iloc[i - 1]) if i else None,
                "next_value": float(v0.iloc[i + 1]) if i + 1 < len(d) else None,
                "official_qc": d[var + "_QC"].iloc[i],
                "reason": "VPD_6p110_plateau_repaired_TA_retained_review"
            })
    print(f"  Joint zero artifacts: {int(hot_zero.sum())} warm TA repairs; "
          f"{int(plateau.sum())} winter VPD-only plateau repairs", flush=True)

    # Additional near-zero-vapour screen, after hard physical and joint plateau checks. Important:
    # RH below 1% can be real at arid sites, so low RH ALONE is not repaired.
    # The key independent signals are nearly absent implied vapour pressure,
    # markedly wetter ERA humidity, and agreement in air temperature.
    # The ERA RH is a reanalysis ESTIMATE, not a tower humidity measurement.
    es_before = saturation_hpa(current["TA_F"])
    ea_before = es_before - current["VPD_F"]
    rh_before = 100 * ea_before / es_before
    es_era_for_low = saturation_hpa(d["TA_ERA"])
    era_rh_for_low = 100 * (es_era_for_low - d["VPD_ERA"]) / es_era_for_low
    low_before = (rh_before.ge(0) & rh_before.lt(1)) | (
        rh_before.lt(0) & ea_before.ge(-0.005)
    )
    strong_low = (
        low_before & ea_before.ge(-0.005) & ea_before.le(0.1) &
        era_rh_for_low.between(50, 100) &
        (current["TA_F"] - d["TA_ERA"]).abs().le(8.0) &
        acceptable_era(d["TA_ERA"], "TA_F") &
        acceptable_era(d["VPD_ERA"], "VPD_F")
    )
    reconstructed_strong = es_before * (1.0 - era_rh_for_low / 100.0)
    if not (reconstructed_strong.loc[strong_low].ge(0) &
            reconstructed_strong.loc[strong_low].le(es_before.loc[strong_low])).all():
        raise RuntimeError("Strong low-RH candidate failed physical checks")
    current["VPD_F"] = current["VPD_F"].mask(strong_low, reconstructed_strong)
    source["VPD_F"] = source["VPD_F"].mask(
        strong_low, "candidate_ERA_RH_at_retained_tower_TA")
    mark("VPD_F", strong_low, "near_zero_vapor_pressure_strong_ERA_wet_candidate")

    low_rh_decisions = pd.DataFrame({
        "site": site,
        "time": d.time.loc[low_before].dt.strftime("%Y-%m-%d %H:%M:%S"),
        "TA_final_C": current["TA_F"].loc[low_before],
        "TA_F_QC": d["TA_F_QC"].loc[low_before],
        "VPD_before_hPa": current["VPD_F"].loc[low_before],
        "VPD_F_QC": d["VPD_F_QC"].loc[low_before],
        "implied_vapor_pressure_before_hPa": ea_before.loc[low_before],
        "RH_before_pct": rh_before.loc[low_before],
        "TA_ERA_C": d["TA_ERA"].loc[low_before],
        "VPD_ERA_hPa": d["VPD_ERA"].loc[low_before],
        "ERA_RH_pct": era_rh_for_low.loc[low_before],
        "site_ERA_TA_difference_C": (current["TA_F"] - d["TA_ERA"]).loc[low_before],
        "strong_candidate": strong_low.loc[low_before],
        "decision": np.where(strong_low.loc[low_before],
                             "candidate_reconstruction_review_required",
                             "not_repaired_by_low_RH_rule_other_QC_may_apply"),
        "VPD_after_hPa": current["VPD_F"].loc[low_before],
    })
    low_rh_decisions["RH_after_pct"] = (
        100.0 * (es_before - current["VPD_F"]) / es_before
    ).loc[low_before].to_numpy()
    low_rh_repair_reviews = []
    for i in np.flatnonzero(strong_low.to_numpy()):
        low_rh_repair_reviews.append({
            "site": site, "time": d.time.iloc[i].isoformat(),
            "variable": "VPD_F", "final_value": float(current["VPD_F"].iloc[i]),
            "era_value": float(d["VPD_ERA"].iloc[i]),
            "difference_to_era": float(current["VPD_F"].iloc[i] - d["VPD_ERA"].iloc[i]),
            "previous_value": None, "next_value": None,
            "official_qc": d["VPD_F_QC"].iloc[i],
            "reason": "near_zero_vapor_pressure_candidate_repaired_ERA_RH_review_required"
        })
    print(f"  Low-RH candidate decisions: {int(low_before.sum())} screened; "
          f"{int(strong_low.sum())} high-confidence candidates reconstructed, "
          f"{int((low_before & ~strong_low).sum())} left unchanged", flush=True)

    # Retained v2 safeguard: never automatically delete a plausible TA merely
    # because VPD from a different provenance is incompatible with it.
    # Mark VPD only. Short-gap interpolation is attempted below, then the
    # residual is reconstructed from ERA-derived RH at the preserved site TA.
    pair_bad = humidity_bad(current["TA_F"], current["VPD_F"])
    if pair_bad.any():
        mark("VPD_F", pair_bad, "TA_VPD_inconsistent_VPD_only")
        current["VPD_F"] = current["VPD_F"].mask(pair_bad)

    # True short-gap interpolation: runs larger than limit are NEVER partly
    # interpolated; need two usable boundary observations.
    for v in VARS:
        limit = INTERPOLATE[v] * 30 // native_minutes
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

    # === STAGE92: original-source, strictly scoped EXTERNAL humidity evidence ===
    # The caller supplies SHA-verified historical Stage64/74 source RH and
    # Stage85 Ho1-2000 human-approved tower-T + humidity choices. The patched
    # Stage07 engine still runs all other original QC-v5 logic and maintains
    # the original variable-event ledger. No ERA-RH numeric shadow is promoted
    # to a science-approved production choice by this technical candidate.
    external_review = []
    stage92 = STAGE92_SCOPED.get(site, {})
    clock_keys = d.time.dt.strftime("%Y%m%d%H%M")

    if site == "US-Ho1":
        ho1 = stage92.get("ho1_2000", {})
        all2000 = d.time.dt.year.eq(2000)
        source2000 = clock_keys.loc[all2000]
        missing2000 = set(source2000) - set(ho1)
        if missing2000 or len(source2000) != 17520:
            raise RuntimeError("STAGE92_HO1_2000_SOURCE_NOT_EXACT: count or identities")
        ok_mask = np.zeros(len(d), dtype=bool)
        t_snapshot = current["TA_F"].copy()
        v_snapshot = current["VPD_F"].copy()
        for i in np.flatnonzero(all2000.to_numpy()):
            k = clock_keys.iat[i]
            src = ho1[k]
            raw_t = float(original["TA_F"].iat[i])
            qc_t = d["TA_F_QC"].iat[i]
            if not np.isfinite(raw_t) or not np.isclose(
                 raw_t, float(src["native_TA_F_original_preserved_C"]),rtol=0,atol=1.e-7):
                raise RuntimeError("Stage85 originally approved T source changed "+k)
            sqc = float(src["native_TA_F_original_QC"])
            if not np.isclose(qc_t,sqc,atol=0):
                raise RuntimeError("Stage85 tower-T original QC differs "+k)
            if sqc == 0:
                new_vpd = float(src["new_VPD_hPa"])
                if not np.isfinite(new_vpd):
                    raise RuntimeError("Stage85 measured-QC0 humidity missing "+k)
                current["TA_F"].iat[i] = raw_t
                current["VPD_F"].iat[i] = new_vpd
                source["TA_F"].iat[i] = "official_measured_stage85_preserved"
                source["VPD_F"].iat[i] = "Stage85_"+str(src["new_VPD_source"])
                ok_mask[i] = True
                # These observations have operator approval for exact original
                # Ho1 2000 QC0 T and the Stage85 humidity-only transform.
            else:
                # Non-QC0 original gap-filled/ERA-sourced T remains UNAPPROVED.
                # We retain its source label and do NOT replace QC1/2 with
                # invented measurements; a physical leap is reported separately.
                current["TA_F"].iat[i] = raw_t
                source["TA_F"].iat[i] = "Stage85_original_T_nonQC0_HOLD"
        changed_T = ok_mask & ~np.isclose(
            current["TA_F"].to_numpy(dtype=float),
            t_snapshot.to_numpy(dtype=float),equal_nan=True)
        changed_V = ok_mask & ~np.isclose(
            current["VPD_F"].to_numpy(dtype=float),
            v_snapshot.to_numpy(dtype=float),equal_nan=True)
        mark("TA_F", changed_T, "Stage85_RESTORE_MANUALLY_APPROVED_ORIGINAL_HO1_QC0_T")
        mark("VPD_F", changed_V, "Stage85_RESTORE_APPROVED_HO1_2000_HUMIDITY")
        print("STAGE92 Ho1-2000 Stage85 exact source QC0 reapplication",
              int(ok_mask.sum()),"QC0; nonQC0 remained source-tagged",
              int(all2000.sum()-ok_mask.sum()),flush=True)
        # Stage85 source contains 17568 leap-year half-hours, including 48
        # measured-source QC0 records on Feb29; Stage07 NOLEAP drops those.
        if int(ok_mask.sum()) != 17246:
            raise RuntimeError("Stage85 Ho1 QC0 native NOLEAP scope differs")

    patches=stage92.get("rh", {})
    pre_bad=humidity_bad(current["TA_F"],current["VPD_F"])
    used=Counter()
    rejected=Counter()
    candidate_mask=np.zeros(len(d),dtype=bool)
    for i in np.flatnonzero(pre_bad.to_numpy()):
        key=clock_keys.iat[i]
        cand=patches.get(key)
        if cand is None:
            continue
        rh,source_name,source_t,source_p,source_status = cand
        tnow=float(current["TA_F"].iat[i])
        pnow=float(current["PA_F"].iat[i])
        if (not np.isfinite(tnow) or not np.isfinite(pnow)
            or not np.isfinite(rh) or not 0 < rh <= 100
            or not np.isfinite(source_t) or abs(tnow-source_t)>0.02
            or not np.isfinite(source_p) or abs(pnow-source_p)>0.3):
            rejected[source_name+"_TEMP_PRESSURE_OR_RH"]+=1
            continue
        new=float(saturation_hpa(tnow))*(1-float(rh)/100)
        if not np.isfinite(new) or new<0:
            rejected[source_name+"_VPD"]+=1
            continue
        current["VPD_F"].iat[i]=new
        source["VPD_F"].iat[i]="Stage92_"+source_name+"_NUMERIC_SHADOW"
        candidate_mask[i]=True
        used[source_name]+=1
        if source_status != "STAGE64_PHYSICAL_CANDIDATE":
            external_review.append({
                "site":site,"time":d.time.iat[i].isoformat(),
                "variable":"VPD_F","final_value":new,
                "era_value":float(d["VPD_ERA"].iat[i]) if
                    np.isfinite(d["VPD_ERA"].iat[i]) else None,
                "difference_to_era":None,"previous_value":None,
                "next_value":None,"official_qc":d["VPD_F_QC"].iat[i],
                "reason":"Stage92_EXTERNAL_CDS_HUMIDITY_NUMERIC_ONLY_"+str(source_status)})
    mark("VPD_F",candidate_mask,"Stage92_verified_independent_ERA5_RH_shadow_at_preserved_T")
    print("STAGE92 external source RH applied",site,dict(used),
          "source_mismatch_rejected",dict(rejected),
          "still_bad",int(humidity_bad(current["TA_F"],current["VPD_F"]).sum()),flush=True)
    # === END STAGE92 scoped source additions ===

    # Final humidity reconciliation, retaining plausible tower TA. We use the
    # companion reanalysis relative humidity rather than mixing reanalysis VPD
    # with a tower temperature measured at a different place/height.
    # For tiny negative ERA-derived RH (<=2 percentage points), use a documented
    # 1% floor; otherwise fail rather than invent a repair.
    bad = humidity_bad(current["TA_F"], current["VPD_F"])
    v5_humidity_review = list(external_review)
    if bad.any():
        era_t, era_v = d["TA_ERA"], d["VPD_ERA"]
        es_era = saturation_hpa(era_t)
        rh_era = 100.0 * (es_era - era_v) / es_era
        # Floor is used ONLY for mathematically impossible, slightly negative
        # ERA RH; every such adjustment requires post-run human review.
        min_rh_pct = 1.0
        allowed = (
            acceptable_era(era_t, "TA_F") &
            acceptable_era(era_v, "VPD_F") &
            rh_era.between(-2.0, 100.05) &
            current["TA_F"].notna()
        )
        unresolved = bad & ~allowed
        if unresolved.any():
            ix = np.flatnonzero(unresolved.to_numpy())[:8]
            details = [(str(d.time.iloc[i]), float(current["TA_F"].iloc[i]),
                        float(current["VPD_F"].iloc[i])) for i in ix]
            raise RuntimeError(
                f"{int(unresolved.sum())} impossible humidity pairs require manual resolution; examples {details}")
        good = bad & allowed
        rh_used = rh_era.clip(lower=min_rh_pct, upper=100.0)
        repaired_vpd = saturation_hpa(current["TA_F"]) * (1.0 - rh_used / 100.0)
        current["VPD_F"] = current["VPD_F"].mask(good, repaired_vpd)
        source["VPD_F"] = source["VPD_F"].mask(good, "era_rh_reconstructed_at_tower_TA")
        mark("VPD_F", good, "reconcile_VPD_from_ERA_RH_keep_TA")
        clamped = good & (rh_era < min_rh_pct)
        mark("VPD_F", clamped, "ERA_RH_below_1pct_clipped_requires_review")
        for i in np.flatnonzero(clamped.to_numpy()):
            v5_humidity_review.append({
                "site": site, "time": d.time.iloc[i].isoformat(),
                "variable": "VPD_F", "final_value": float(current["VPD_F"].iloc[i]),
                "era_value": float(era_v.iloc[i]),
                "difference_to_era": float(current["VPD_F"].iloc[i] - era_v.iloc[i]),
                "previous_value": None, "next_value": None,
                "official_qc": d["VPD_F_QC"].iloc[i],
                "reason": "ERA_RH_below_1pct_adjusted_review_needed"
            })

    if humidity_bad(current["TA_F"], current["VPD_F"]).any():
        raise RuntimeError("Final humidity remains physically impossible")

    # Large VPD reconstruction or a QC=0 VPD should never be silently
    # accepted: request a targeted review while keeping the corrected forcing
    # available in the separate v5 trial folder.
    if bad.any():
        impact = good & ~clamped & (
            (current["VPD_F"] - original["VPD_F"]).abs().ge(5.0)
            | d["VPD_F_QC"].eq(0)
        )
        for i in np.flatnonzero(impact.to_numpy()):
            er = d["VPD_ERA"].iloc[i]
            manual_extra = {
                "site": site, "time": d.time.iloc[i].isoformat(),
                "variable": "VPD_F", "final_value": float(current["VPD_F"].iloc[i]),
                "era_value": float(er) if pd.notna(er) else None,
                "difference_to_era": float(current["VPD_F"].iloc[i] - er) if pd.notna(er) else None,
                "previous_value": None, "next_value": None,
                "official_qc": d["VPD_F_QC"].iloc[i],
                "reason": "large_or_measured_VPD_reconstruction_review"
            }
            v5_humidity_review.append(manual_extra)

    # Flag scientifically ambiguous readings without silently overwriting.
    manual = list(v5_humidity_review) + flatline_reviews + low_rh_repair_reviews
    es_final = saturation_hpa(current["TA_F"])
    rh_final = 100.0 * (es_final - current["VPD_F"]) / es_final
    very_low_rh = (current["TA_F"].notna() & current["VPD_F"].notna() &
                   rh_final.between(0.0, 1.0, inclusive="neither"))
    for i in np.flatnonzero(very_low_rh.to_numpy()):
        # Review, not automatic replacement. This may be a real dry extreme.
        manual.append({
            "site": site, "time": d.time.iloc[i].isoformat(),
            "variable": "VPD_F", "final_value": float(current["VPD_F"].iloc[i]),
            "era_value": float(d["VPD_ERA"].iloc[i]) if pd.notna(d["VPD_ERA"].iloc[i]) else None,
            "difference_to_era": float(current["VPD_F"].iloc[i] - d["VPD_ERA"].iloc[i]) if pd.notna(d["VPD_ERA"].iloc[i]) else None,
            "previous_value": None, "next_value": None,
            "official_qc": d["VPD_F_QC"].iloc[i],
            "reason": "very_low_but_positive_RH_preserved_review"
        })
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

    out_qc = output_root / site / "forcing" / "qc_v5"
    out_proc = output_root / site / "forcing" / "processed_v5"
    # Non-destructive, provenance-rich diagnostic of unresolved near-zero RH.
    low_mask = rh_final.ge(0) & rh_final.lt(1)
    low_diag = pd.DataFrame({
        "site": site,
        "time": d.time.loc[low_mask].dt.strftime("%Y-%m-%d %H:%M:%S"),
        "TA_original_C": original["TA_F"].loc[low_mask],
        "TA_final_C": current["TA_F"].loc[low_mask],
        "TA_QC": d["TA_F_QC"].loc[low_mask],
        "TA_ERA_C": d["TA_ERA"].loc[low_mask],
        "VPD_original_hPa": original["VPD_F"].loc[low_mask],
        "VPD_final_hPa": current["VPD_F"].loc[low_mask],
        "VPD_QC": d["VPD_F_QC"].loc[low_mask],
        "VPD_ERA_hPa": d["VPD_ERA"].loc[low_mask],
        "RH_final_pct": rh_final.loc[low_mask],
        "near_zero_TA_and_6p110": (original["TA_F"].abs().le(.0005) &
                                      (original["VPD_F"] - 6.110).abs().le(.008)).loc[low_mask]
    })
    save_csv_atomic(low_diag, out_qc / f"{site}_low_RH_diagnostic.csv")
    save_csv_atomic(low_rh_decisions, out_qc / f"{site}_low_RH_decisions.csv")
    print(f"  Residual RH <1%: {int(low_mask.sum())}; near TA=0 & VPD=6.110: "
          f"{int(low_diag['near_zero_TA_and_6p110'].sum())}", flush=True)
    if len(low_diag):
        print("  Low-RH by year:", low_diag.groupby(low_diag["time"].str[:4]).size().nlargest(5).to_dict(), flush=True)
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

    # Convert accumulated P [mm/native interval] to rate [mm/s].
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
                         "PRECTmms": current["P_F"].clip(lower=0) / native_seconds,
                         "TA_USE": current["TA_F"], "VPD_USE": current["VPD_F"]})
    check_ranges = {"TBOT": (180, 340), "QBOT": (0, 0.08),
                    "PSRF": (49000, 111000), "FSDS": (0, 1600),
                    "FLDS": (0, 800), "WIND": (0, 75),
                    "PRECTmms": (0, 300/native_seconds)}
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
              "script_version": "2026-10-22.qcv5_native_batch02",
              "native_minutes": native_minutes,
              "standalone_era_precedence": standalone_era,
              "reanalysis": "FLUXNET site-downscaled native ERA5 companion, not independently downloaded ERA5-Land",
              "forcing_era_gap_rule": "complete gaps <=120 min interpolated (SW<=60 min), two valid same-year boundaries; precipitation ERA only",
              "humidity_rule": "detect corroborated zero-temperature/6.110 VPD artifacts; keep winter site TA and reconstruct plateau VPD from ERA RH; preserve otherwise plausible TA; reconcile impossible VPD at TA using ERA-derived RH; 1% floor for mildly invalid ERA RH with REVIEW",
              "low_RH_decision_rule": "candidate only if RH<1% or slightly negative from rounding, actual vapor -0.005 to 0.1hPa, ERA RH>=50%, abs(TA_site-TA_ERA)<=8C; use ERA RH at preserved site temperature and force REVIEW; otherwise leave unchanged",
              "low_RH_candidates_reconstructed": int(strong_low.sum()),
              "low_RH_candidates_left_unchanged": int((low_before & ~strong_low).sum()),
              "ZBOT": "not assigned: verify BIFVARINFO before DATM creation"}
    out_qc.mkdir(parents=True, exist_ok=True)
    (out_qc / f"{site}_status.json").write_text(json.dumps(status, indent=2))
    print(f"  RESULT: {status['status']}; {len(forc)} rows; {len(events)} changes; "
          f"{len(manual)} review records", flush=True)
    return status
