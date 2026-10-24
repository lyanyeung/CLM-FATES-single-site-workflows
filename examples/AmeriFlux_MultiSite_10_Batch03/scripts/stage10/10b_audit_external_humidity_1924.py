#!/usr/bin/env python3
"""Batch03 Stage10b: audit 1,924 humidity blockers against 32 ERA5-Land products.

Scientifically conservative, evidence-only sensitivities:
 A: dewpoint-derived ERA5-Land absolute vapour pressure at retained tower T/P.
 B: ERA5-Land grid relative humidity transferred to retained tower T/P.
Both use liquid-water saturation for consistency with existing QC-v5; subzero
events get a separate ice-saturation CAUTION, not automatic substitution.

BIF offset is provisional at 6 stations; US-Me2 uses UTC-8 as an explicitly
UNAPPROVED hypothesis supported by Stage10a solar diagnostics, NOT release BADM.
At 30/60-minute native interval MIDPOINTS, interpolate the hourly grid data.
Input is SHA-pinned Stage08c residuals + Stage08f MDS + Stage07 exact sources +
Stage09a plan + Stage09f verified ERA5-Land downloads.

--check: complete source/provenance preflight, no output files.
--analyze: complete 1,924-record computation/console summary, no output files.
--run: same computation; creates only NEW isolated reports under reports/stage10b_*
No tower/ERA inputs, source, QC-v5, DATM, cases or Slurm jobs are altered.
Physical screen passes are NOT scientific approval or replacement decisions.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile
from uuid import uuid4

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

sys.dont_write_bytecode = True
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
STAGE08C = ROOT / "reports/stage08c_era_humidity_20261022T031437Z_512e8731"
STAGE08E = ROOT / "reports/stage08e_alternatives_20261022T032727Z_b122e5b0"
STAGE08F = ROOT / "reports/stage08f_mds_pairs_20261022T033321Z_7591f948"
STAGE09A = ROOT / "reports/stage09a_external_dewpoint_plan_20261022T034051Z_437c9c0c"
STAGE09F_SCRIPT = Path(__file__).resolve().parents[1] / "stage09/09f_incremental_dewpoint_queue.py"
BIF_OFFSET = {"US-Kon": -6, "US-MMS": -5, "US-Me6": -8,
              "US-MtB": -7, "US-NR1": -7, "US-NR3": -7}
PROVISIONAL_OFFSET = {**BIF_OFFSET, "US-Me2": -8}
COUNTS = {"US-Kon": 229, "US-MMS": 18, "US-Me2": 4, "US-Me6": 1,
          "US-MtB": 15, "US-NR1": 173, "US-NR3": 1484}
KEYS = ["site", "source_csv_row", "time"]
MDS_FIELDS = [
    "MDS_pair_physical_screen_pass", "MDS_QC_both_0_or_1",
    "MDS_VPD_valid_at_retained_TA", "MDS_RH_at_MDS_TA_pct",
    "MDS_RH_at_retained_TA_pct", "MDS_QBOT_at_MDS_TA_kgkg",
    "review_class"
]
SOURCE_FIELDS = [
    "site", "source_csv_row", "time", "TA_before_fallback_C",
    "VPD_before_fallback_hPa", "PA_before_fallback_kPa",
    "TA_ERA_C", "VPD_ERA_hPa", "ERA_RH_pct",
    "VPD_original_QC", "rejection_primary_reason"
]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for part in iter(lambda: source.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def regular(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected regular file, not symlink or missing: " + str(path))
    return path


def directory(path):
    path = Path(path)
    if not path.is_dir() or path.is_symlink():
        raise ValueError("Missing/unsafe evidence directory: " + str(path))
    return path


def load_queue():
    regular(STAGE09F_SCRIPT)
    spec = importlib.util.spec_from_file_location("batch03_stage09f_stage10b", str(STAGE09F_SCRIPT))
    if not spec or not spec.loader:
        raise ValueError("Cannot import pinned Stage09f verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def numeric(frame, column):
    arr = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    arr[(~np.isfinite(arr)) | (arr <= -9990)] = np.nan
    return arr


def boolean(frame, column):
    return frame[column].astype(str).str.strip().str.lower().isin(["true", "1"]).to_numpy(dtype=bool)


def saturation_water_hpa(t):
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return 6.112 * np.exp(np.clip(17.67 * t / (t + 243.5), -40, 40))


def saturation_ice_hpa(t):
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return 6.112 * np.exp(np.clip(22.46 * t / (t + 272.62), -40, 40))


def q_from_e(e_hpa, pa):
    vapour_pa = e_hpa * 100.0
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        return 0.622 * vapour_pa / (pa - 0.378 * vapour_pa)


def grid_fields(path, year, expected_coord):
    expected_index = pd.date_range(
        f"{year-1}-12-29 00:00:00", f"{year+1}-01-03 23:00:00", freq="h")
    found = {}
    coordinate_samples = []

    def read_nc(ds):
        var = ds.variables.get("valid_time")
        if var is None:
            var = ds.variables.get("time")
        if var is None or not getattr(var, "units", ""):
            raise ValueError("Missing CF UTC valid_time")
        dates = num2date(var[:], var.units,
                         calendar=getattr(var, "calendar", "standard"),
                         only_use_cftime_datetimes=False, only_use_python_datetimes=True)
        dt = pd.DatetimeIndex(pd.to_datetime([str(x) for x in dates]))
        if not dt.equals(expected_index):
            raise ValueError("ERA5-Land UTC time coordinates differ from Stage09f")
        lat = float(np.asarray(ds.variables["latitude"][:]).reshape(-1)[0])
        lon = float(np.asarray(ds.variables["longitude"][:]).reshape(-1)[0])
        if abs(lat - expected_coord[0]) > 0.151 or abs(lon - expected_coord[1]) > 0.151:
            raise ValueError("ERA5-Land grid point differs from request position")
        coordinate_samples.append((lat, lon))
        for field, units in (("t2m", "K"), ("d2m", "K"), ("sp", "Pa")):
            if field not in ds.variables:
                continue
            if field in found:
                raise ValueError("Duplicate gridded variable: " + field)
            v = ds.variables[field]
            if getattr(v, "units", "") != units:
                raise ValueError("Gridded unit changed for " + field)
            x = np.asarray(np.ma.asarray(v[:]).filled(np.nan), dtype=float).reshape(-1)
            if len(x) != len(dt) or not np.isfinite(x).all():
                raise ValueError("Invalid gridded variable values for " + field)
            found[field] = x

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            if zf.testzip() is not None:
                raise ValueError("ERA5-Land ZIP CRC failure: " + str(path))
            members = [x for x in zf.infolist() if x.filename.endswith(".nc")]
            if not 1 <= len(members) <= 6:
                raise ValueError("Unexpected NetCDF ZIP member count")
            for member in members:
                if member.file_size > 100_000_000 or member.filename.startswith("/") or ".." in Path(member.filename).parts:
                    raise ValueError("Unsafe NetCDF ZIP entry")
                with Dataset("inmemory.nc", "r", memory=zf.read(member)) as ds:
                    read_nc(ds)
    elif path.suffix == ".nc":
        with Dataset(str(path), "r") as ds:
            read_nc(ds)
    else:
        raise ValueError("Unexpected downloaded evidence suffix")
    if set(found) != {"t2m", "d2m", "sp"}:
        raise ValueError("Missing complete t2m/d2m/sp hourly evidence")
    if any(abs(p[0]-coordinate_samples[0][0]) > 1e-5 or abs(p[1]-coordinate_samples[0][1]) > 1e-5
           for p in coordinate_samples):
        raise ValueError("Gridded members disagree on location")
    return expected_index, found, coordinate_samples[0]


def interpolate(index, vals, targets):
    src = index.asi8.astype(np.float64) / 1e9
    dst = pd.DatetimeIndex(targets).asi8.astype(np.float64) / 1e9
    if len(dst) and (dst.min() < src[0] or dst.max() > src[-1]):
        raise ValueError("Native event midpoint is outside downloaded UTC evidence period")
    return np.interp(dst, src, vals)


def preflight():
    for p in (ROOT, STAGE07, STAGE08C, STAGE08E, STAGE08F, STAGE09A):
        directory(p)
    regular(STAGE07 / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    c_file = regular(STAGE08C / "era_humidity_residual_details.csv")
    e_policy = json.loads(regular(STAGE08E / "evidence_policy.json").read_text())
    f_policy = json.loads(regular(STAGE08F / "policy.json").read_text())
    f_file = regular(STAGE08F / "mds_pair_at_1924_blockers.csv")
    if (int(e_policy["records"]) != 1924
            or sha(c_file) != e_policy["stage08c_sha256"]
            or int(f_policy["records"]) != 1924
            or Path(f_policy["stage08e_evidence"]).resolve() != STAGE08E
            or sha(STAGE08E / "raw_alternatives_at_blockers.csv") != f_policy["stage08e_evidence_sha256"]):
        raise ValueError("Stage08c–08f cross-report SHA/lineage mismatch")
    original = pd.read_csv(c_file, dtype=str, keep_default_na=False)
    mds = pd.read_csv(f_file, dtype=str, keep_default_na=False)
    if (len(original) != 1924 or len(mds) != 1924 or
            not set(SOURCE_FIELDS).issubset(original.columns) or
            not set(KEYS + MDS_FIELDS).issubset(mds.columns)):
        raise ValueError("Stage08c/08f detailed evidence schema or scope changed")
    if (original.duplicated(KEYS).any() or mds.duplicated(KEYS).any()
            or set(map(tuple, original[KEYS].to_numpy())) != set(map(tuple, mds[KEYS].to_numpy()))):
        raise ValueError("Stage08c/08f source-row identities differ")
    if not original.rejection_primary_reason.eq("ERA_RH_BELOW_MINUS2_PCT").all():
        raise ValueError("Unexpected Stage08c rejection reason")
    joined = original.merge(mds[KEYS + MDS_FIELDS], on=KEYS, validate="one_to_one")
    joined["year"] = pd.to_datetime(joined.time, errors="raise").dt.year
    if len(joined) != 1924 or joined.site.value_counts().to_dict() != COUNTS:
        raise ValueError("Unexpected per-site original blocker counts")

    doc = json.loads(regular(STAGE07 / "exact_input_manifest.json").read_text())
    chosen = {r["site"]: r for r in doc["sites"]}
    pins = {str(Path(p).resolve()): h for p,h in doc["input_sha256"].items()}
    if not set(COUNTS).issubset(chosen) or len(chosen) != 10:
        raise ValueError("Stage07 input release inventory differs")
    verified_sources = {}
    for site in sorted(COUNTS):
        item = chosen[site]
        step = int(item["native_minutes"])
        if step != (60 if site == "US-MMS" else 30):
            raise ValueError("Wrong native interval in pinned Stage07 metadata")
        for kind in ("primary", "era"):
            p = regular(item[kind])
            ref_hash = pins.get(str(p.resolve()))
            if not ref_hash or sha(p) != ref_hash:
                raise ValueError("Source SHA changed: " + str(p))
            verified_sources[str(p)] = ref_hash

    queue = load_queue()
    plan = queue.read_source()
    clk = json.loads(regular(STAGE09A / "site_utc_offset_inventory.json").read_text())
    clk = {r["site"]: r for r in clk}
    if len(clk) != 7 or set(clk) != set(COUNTS):
        raise ValueError("Stage09a clock inventory changed")
    for site in COUNTS:
        published = {str(x).strip() for x in clk[site]["published_utc_offsets"]}
        if site in BIF_OFFSET:
            if (published != {str(BIF_OFFSET[site])} or
                    clk[site]["status"] != "ONE_PUBLISHED_OFFSET_PENDING_VALIDATION"):
                raise ValueError("Published clock changed for " + site)
        elif published or clk[site]["status"] != "NO_RELEASE_BIF_FULLSET_SITE_METADATA_REQUIRED":
            raise ValueError("US-Me2 metadata status changed")
    if len(plan) != 32 or sum(int(x["blocked_native_records"]) for x in plan) != 1924:
        raise ValueError("Stage09a request scope changed")
    items = []
    for r in plan:
        site, year = r["site"], int(r["year"])
        group = joined.loc[(joined.site == site) & (joined.year == year)]
        if len(group) != int(r["blocked_native_records"]):
            raise ValueError(f"Stage08c event rows disagree with Stage09a request count: {site}:{year}")
        state, meta = queue.check_artifact(r)
        if state != "VERIFIED":
            raise ValueError(f"Missing/non-verified external evidence: {site}:{year}, {state}")
        items.append((r, meta))
    if len(items) != 32 or sum(int(x[0]["blocked_native_records"]) for x in items) != 1924:
        raise ValueError("External evidence inventory incomplete")
    return joined, chosen, items, verified_sources, {"stage08c": sha(c_file),
       "stage08f": sha(f_file), "stage09a_receipt": sha(STAGE09A / "evidence_receipt.json")}


def analyze(joined, chosen, items):
    tables = []
    for r, meta in sorted(items, key=lambda item: (item[0]["site"], int(item[0]["year"]))):
        site, year = r["site"], int(r["year"])
        subset = joined.loc[(joined.site == site) & (joined.year == year)].copy()
        offset = PROVISIONAL_OFFSET[site]
        step = int(chosen[site]["native_minutes"])
        product = ROOT / "external_evidence/era5land_timeseries" / site / str(year) / meta["name"]
        position = r["request"]["location"]
        coord = (float(position["latitude"]), float(position["longitude"]))
        times, grid, cell = grid_fields(regular(product), year, coord)
        midpoint = pd.DatetimeIndex(pd.to_datetime(subset.time)) + pd.Timedelta(minutes=step/2)
        utc = midpoint - pd.Timedelta(hours=offset)
        gtemp = interpolate(times, grid["t2m"], utc) - 273.15
        gdew = interpolate(times, grid["d2m"], utc) - 273.15
        gpress = interpolate(times, grid["sp"], utc)
        tower_t = numeric(subset, "TA_before_fallback_C")
        tower_p = numeric(subset, "PA_before_fallback_kPa") * 1000.0
        original_vpd = numeric(subset, "VPD_before_fallback_hPa")
        grid_es = saturation_water_hpa(gtemp)
        grid_ea = saturation_water_hpa(gdew)
        grid_rh = 100.0 * grid_ea / grid_es
        tower_es = saturation_water_hpa(tower_t)

        valid_site = (np.isfinite(tower_t) & (tower_t >= -80) & (tower_t <= 65)
                      & np.isfinite(tower_p) & (tower_p >= 50000) & (tower_p <= 110000))
        valid_grid = ((gdew <= gtemp + 0.1) &
                      (grid_rh > 0) & (grid_rh <= 100.05) &
                      np.isfinite(grid_rh) & np.isfinite(gpress))

        # Sensitivity A: transfer absolute ERA5-Land vapor pressure to tower.
        vpd_abs = tower_es - grid_ea
        rh_abs = 100.0 * grid_ea / tower_es
        q_abs = q_from_e(grid_ea, tower_p)
        pass_abs = (valid_site & valid_grid & np.isfinite(vpd_abs)
                    & (vpd_abs >= 0) & (vpd_abs <= 125)
                    & np.isfinite(rh_abs) & (rh_abs > 0) & (rh_abs <= 100.05)
                    & np.isfinite(q_abs) & (q_abs > 0) & (q_abs <= 0.08))

        # Sensitivity B: transfer GRID RH to tower temperature and tower P.
        ea_rel = tower_es * (grid_rh / 100.0)
        vpd_rel = tower_es - ea_rel
        rh_rel = grid_rh
        q_rel = q_from_e(ea_rel, tower_p)
        pass_rel = (valid_site & valid_grid & np.isfinite(vpd_rel)
                    & (vpd_rel >= 0) & (vpd_rel <= 125)
                    & np.isfinite(rh_rel) & (rh_rel > 0) & (rh_rel <= 100.05)
                    & np.isfinite(q_rel) & (q_rel > 0) & (q_rel <= 0.08))

        ice_es = np.where(tower_t < 0, saturation_ice_hpa(tower_t), tower_es)
        ice_rh_abs = 100.0 * grid_ea / ice_es
        caution_ice_super = (tower_t < 0) & np.isfinite(ice_rh_abs) & (ice_rh_abs > 100.0)
        high_temperature_grid_delta = np.isfinite(tower_t) & (np.abs(tower_t - gtemp) > 5.0)
        high_pressure_grid_delta = np.isfinite(tower_p) & (np.abs(tower_p - gpress) > 15000.0)

        subset["year"] = year
        subset["native_minutes"] = step
        subset["clock_offset_hours_hypothesis"] = offset
        subset["clock_approved"] = False
        subset["utc_midpoint_hypothesis"] = utc.astype(str)
        subset["grid_cell_latitude"] = cell[0]
        subset["grid_cell_longitude"] = cell[1]
        subset["external_file"] = str(product)
        subset["external_sha256"] = meta["sha256"]
        subset["grid_temperature_C"] = gtemp
        subset["grid_dewpoint_C"] = gdew
        subset["grid_pressure_Pa"] = gpress
        subset["tower_minus_grid_temperature_C"] = tower_t - gtemp
        subset["tower_minus_grid_pressure_Pa"] = tower_p - gpress
        subset["grid_relative_humidity_pct"] = grid_rh
        subset["grid_dewpoint_absolute_e_hPa"] = grid_ea
        subset["absolute_vpd_at_tower_T_hPa"] = vpd_abs
        subset["absolute_rh_at_tower_T_pct"] = rh_abs
        subset["absolute_qbot_at_tower_P_kgkg"] = q_abs
        subset["absolute_transfer_physical_pass"] = pass_abs
        subset["relative_vpd_at_tower_T_hPa"] = vpd_rel
        subset["relative_rh_at_tower_T_pct"] = rh_rel
        subset["relative_qbot_at_tower_P_kgkg"] = q_rel
        subset["relative_transfer_physical_pass"] = pass_rel
        subset["MDS_pair_physical_screen_pass"] = boolean(subset, "MDS_pair_physical_screen_pass")
        subset["MDS_QC_both_0_or_1"] = boolean(subset, "MDS_QC_both_0_or_1")
        subset["MDS_VPD_valid_at_retained_TA"] = boolean(subset, "MDS_VPD_valid_at_retained_TA")
        subset["tower_temperature_subzero"] = tower_t < 0
        subset["absolute_transfer_ice_supersaturation_caution"] = caution_ice_super
        subset["grid_tower_temperature_absdiff_gt_5C_caution"] = high_temperature_grid_delta
        subset["grid_tower_pressure_absdiff_gt_15000Pa_caution"] = high_pressure_grid_delta
        subset["absolute_minus_original_vpd_hPa"] = vpd_abs - original_vpd
        subset["relative_minus_original_vpd_hPa"] = vpd_rel - original_vpd
        subset["absolute_minus_mds_vpd_hPa"] = vpd_abs - numeric(subset, "VPD_F_MDS") if "VPD_F_MDS" in subset else np.nan
        subset["review_class_stage10b"] = np.select(
            [~valid_site, ~valid_grid, ~pass_abs & ~pass_rel, pass_abs & pass_rel,
             pass_abs, pass_rel],
            ["HOLD_INVALID_SITE_T_OR_P", "HOLD_INVALID_GRID_PHYSICS",
             "HOLD_BOTH_TRANSFER_SCREENS_FAIL", "REVIEW_BOTH_PHYSICAL",
              "REVIEW_ABSOLUTE_ONLY_PHYSICAL", "REVIEW_RELATIVE_ONLY_PHYSICAL"],
            default="HOLD_UNCLASSIFIED")
        tables.append(subset)

        print(f"STAGE10B YEAR: {site} {year} blockers={len(subset)} "
              f"absolute_physical={int(pass_abs.sum())} "
              f"relative_physical={int(pass_rel.sum())} "
              f"subzero={int((tower_t < 0).sum())} "
              f"grid_temperature_delta_gt5C={int(high_temperature_grid_delta.sum())}",
              flush=True)

    all_events = pd.concat(tables, ignore_index=True).sort_values(KEYS).reset_index(drop=True)
    if len(all_events) != 1924 or all_events.duplicated(KEYS).any():
        raise ValueError("Merged external evidence does not contain exactly 1924 unique source rows")
    site_summary = []
    year_summary = []
    for (site, year), sub in all_events.groupby(["site", "year"], sort=True):
        year_summary.append(summarize(sub, site, year))
    for site, sub in all_events.groupby("site", sort=True):
        site_summary.append(summarize(sub, site, None))
    return all_events, pd.DataFrame(site_summary), pd.DataFrame(year_summary)


def summarize(df, site, year):
    tower_minus_grid = pd.to_numeric(df["tower_minus_grid_temperature_C"], errors="coerce").to_numpy(dtype=float)
    tower_grid_finite = tower_minus_grid[np.isfinite(tower_minus_grid)]
    return dict(
        site=site,
        **({"year": int(year)} if year is not None else {}),
        blockers=len(df),
        UTC_offset_hypothesis=PROVISIONAL_OFFSET[site],
        UTC_offset_approved=False,
        absolute_physical_pass=int(df["absolute_transfer_physical_pass"].sum()),
        relative_physical_pass=int(df["relative_transfer_physical_pass"].sum()),
        both_physical_pass=int((df["absolute_transfer_physical_pass"] &
                                df["relative_transfer_physical_pass"]).sum()),
        neither_physical_pass=int((~df["absolute_transfer_physical_pass"] &
                                   ~df["relative_transfer_physical_pass"]).sum()),
        MDS_pair_physical_pass=int(df["MDS_pair_physical_screen_pass"].sum()),
        MDS_QC_both_0_or_1=int(df["MDS_QC_both_0_or_1"].sum()),
        tower_T_below_0C=int(df["tower_temperature_subzero"].sum()),
        absolute_ice_supersaturation_cautions=int(df["absolute_transfer_ice_supersaturation_caution"].sum()),
        tower_grid_T_absdiff_gt_5C=int(df["grid_tower_temperature_absdiff_gt_5C_caution"].sum()),
        tower_grid_P_absdiff_gt_15000Pa=int(df["grid_tower_pressure_absdiff_gt_15000Pa_caution"].sum()),
        median_tower_minus_grid_T_C=float(np.median(tower_grid_finite)) if len(tower_grid_finite) else None,
        review_required=len(df)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    opts = parser.add_mutually_exclusive_group(required=True)
    opts.add_argument("--check", action="store_true")
    opts.add_argument("--analyze", action="store_true")
    opts.add_argument("--run", action="store_true")
    args = parser.parse_args()
    print("STAGE10B — 1924 HUMIDITY EXTERNAL EVIDENCE SENSITIVITY", flush=True)
    joined, chosen, items, sources, provenance = preflight()
    print("STAGE10B PREFLIGHT: 7/7 sites, 32/32 external site-years, "
          "1924/1924 original humidity blockers SHA/evidence verified", flush=True)
    print("WARNING: clocks PROVISIONAL; US-Me2 UTC-8 is NOT documented release metadata", flush=True)
    if args.check:
        print("CHECK ONLY: no files or jobs created")
        return

    event_table, site_table, year_table = analyze(joined, chosen, items)
    print("\n========== STAGE10B SITE SUMMARY (PHYSICAL SCREENS ONLY) ==========", flush=True)
    print(site_table.to_string(index=False), flush=True)
    print("\nREVIEW CLASS COUNTS:", flush=True)
    print(event_table["review_class_stage10b"].value_counts().to_string(), flush=True)
    print("STAGE10B SUMMARY: source_rows=1924/1924 site_years=32/32 "
          "forcing_changes=0 time_offsets_approved=0 repair_approvals=0", flush=True)
    if args.analyze:
        print("ANALYZE ONLY: computed in memory, no new report files created.", flush=True)
        return

    # New isolated evidence directory only; markers and original sources retained.
    tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    output = ROOT / "reports" / ("stage10b_external_humidity_" + tag)
    output.mkdir(exist_ok=False)
    event_file = output / "humidity_external_sensitivity_1924.csv"
    site_file = output / "site_science_review_summary.csv"
    year_file = output / "site_year_science_review_summary.csv"
    event_table.to_csv(event_file, index=False)
    site_table.to_csv(site_file, index=False)
    year_table.to_csv(year_file, index=False)
    lineage = {
        "scope": "1924 pinned blockers, 7 sites, 32 site-years",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "original_provenance": provenance,
        "pinned_source_SHA256": sources,
        "external_product_SHA256": {f"{x['site']}:{x['year']}": meta["sha256"] for x,meta in items},
        "offsets_tested_provisionally_only": PROVISIONAL_OFFSET,
        "site_Me2_clock": "UTC-8 provisional hypothesis, NO RELEASE BIF, NOT APPROVED",
        "method": "Linear interpolation of ERA5-Land t2m/d2m/sp to native interval UTC midpoint; liquid-water saturation; compare absolute vapour pressure and relative-humidity transfers",
        "cautions": [
            "No elevation correction or 2m/measurement-height transfer validated.",
            "Subzero liquid-water RH differs from ice-relative RH.",
            "ERA5-Land atmospheric forcing is not independent of ERA5.",
            "Thresholds are only physical plausibility screens, not repair approval.",
            "Stage10a solar diagnostic does not authorize an unverified clock shift.",
            "MDS QC and physical plausibility are not independent validation.",
            "No forcing, DATM, source files, CIME case or model jobs changed."
        ],
        "output_SHA256": {
            x.name: sha(x) for x in (event_file, site_file, year_file)
        },
        "decision": "ALL ROWS SCIENTIFIC HOLD; NO REPLACEMENTS APPROVED"
    }
    (output / "provenance_and_science_hold.json").write_text(
        json.dumps(lineage, indent=2) + "\n", encoding="utf-8")
    print("STAGE10B REPORT DIR:", output, flush=True)
    print("REPORT ONLY. Existing source/forcing and all scientific hold markers retained.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE10B ERROR:", str(exc), file=sys.stderr, flush=True)
        sys.exit(2)
