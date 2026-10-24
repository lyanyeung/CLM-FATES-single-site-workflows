#!/usr/bin/env python3
"""Batch03 Stage10a — evidence-only solar clock cross-check, NOT offset approval.

For each of the 32 Stage09a site-years, read the SHA-pinned *raw* FLUXMET/
FULLSET SW_IN_F radiation series at its native HH/HR cadence. Independently
compute astronomical sun elevation using Stage08e pinned coordinates. Test
three timezone hypotheses: the six official BIF UTC_OFFSET values +/-1 hour;
US-Me2 -9/-8/-7 are exploratory because this FULLSET has no release BIF.

Outputs are printed to stdout ONLY. Run with --check or --analyze. No files are
written by this Python script. All offsets remain formally UNAPPROVED; even a
stronger solar match is NOT a replacement for release-specific site metadata.

Stage09i used tower/grid air temperature; this is a complementary (but not
conclusive) radiation-based clock sensitivity. Cloud cover, sensor shading,
tower data gap-filling, seasonal sun angle and QC can bias the score.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
STAGE09A = ROOT / "reports/stage09a_external_dewpoint_plan_20261022T034051Z_437c9c0c"
MANIFEST = Path(__file__).resolve().parents[2] / "sites.tsv"
BASE_RAW = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")

# Stage09h confirmed exactly one published BIF offset per listed site.
# These are TEST CENTRES, not formally approved offsets.
PUBLISHED = {
    "US-Kon": -6, "US-MMS": -5, "US-Me6": -8,
    "US-MtB": -7, "US-NR1": -7, "US-NR3": -7,
}
BIF_SHA256 = {
    "US-Kon": "d9e6548567558b89968ebd3986e436a7651be1fe8435b11f7c714aef87fe66d0",
    "US-MMS": "1f8581489a2b5bdbc4d0aecd8ae78dcefd8c5ab809a5300da6b146038d9ccc58",
    "US-Me6": "e8db4c98b646d730a371d37e6046a3c8e02ffd719ae81f3f3dab9a4ee895d554",
    "US-MtB": "0843108555fc2ebfffefb076a54b657291874822d38bbee6fa6891b184a5f275",
    "US-NR1": "8e97de15995f85f3d438ef3b1c076ec100fd39d1fb565ef9dc1614b85efa1232",
    "US-NR3": "e02c9b6b97ba89ac9e1a70faeb73eeec06d96455d3b6d3dc7c537b774f578d44",
}
# Exact Stage08e historical evidence coordinates; checked against Stage09a
# per-year request metadata. These are not ERA5-Land grid-cell elevations.
COORD = {
    "US-Kon": (39.0824, -96.5603),
    "US-MMS": (39.3232, -86.4131),
    "US-Me2": (44.4526, -121.5589),
    "US-Me6": (44.3233, -121.6078),
    "US-MtB": (32.4160, -110.7256),
    "US-NR1": (40.0329, -105.5464),
    "US-NR3": (40.0520, -105.5864),
}
EXPECTED_BLOCKERS = {
    "US-Kon": 229, "US-MMS": 18, "US-Me2": 4,
    "US-Me6": 1, "US-MtB": 15, "US-NR1": 173, "US-NR3": 1484,
}


def regular(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing, unsafe or symlink input: " + str(path))
    return path


def digest(path):
    h = hashlib.sha256()
    with regular(path).open("rb") as source:
        for piece in iter(lambda: source.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def rows(path, delimiter=","):
    with regular(path).open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source, delimiter=delimiter))


def solar_cos_zenith(utc, latitude, longitude):
    """NOAA-style fractional-year approximation; positive means sun above horizon.

    Input is a UTC-naive DatetimeIndex. Only geometry, not a model of
    atmospheric transmission, radiation, clouds or local topography.
    """
    utc = pd.DatetimeIndex(utc)
    day = utc.dayofyear.to_numpy(dtype=float)
    hour = (utc.hour.to_numpy(dtype=float) +
            utc.minute.to_numpy(dtype=float) / 60.0 +
            utc.second.to_numpy(dtype=float) / 3600.0)
    frac = 2.0 * np.pi / 365.0 * (day - 1 + (hour - 12.0) / 24.0)
    eot_minutes = 229.18 * (
        0.000075 + 0.001868 * np.cos(frac) - 0.032077 * np.sin(frac)
        - 0.014615 * np.cos(2 * frac) - 0.040849 * np.sin(2 * frac)
    )
    decl = (
        0.006918 - 0.399912 * np.cos(frac) + 0.070257 * np.sin(frac)
        - 0.006758 * np.cos(2 * frac) + 0.000907 * np.sin(2 * frac)
        - 0.002697 * np.cos(3 * frac) + 0.00148 * np.sin(3 * frac)
    )
    true_solar_minutes = (hour * 60.0 + eot_minutes + 4.0 * longitude) % 1440.0
    hour_angle = np.deg2rad(true_solar_minutes / 4.0 - 180.0)
    lat = math.radians(latitude)
    return np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl) * np.cos(hour_angle)


def solar_selftest():
    # Geometrically unambiguous equatorial equinox, excluding atmospheric effects.
    dt = pd.DatetimeIndex(["2024-03-20 12:00", "2024-03-20 00:00"])
    val = solar_cos_zenith(dt, 0.0, 0.0)
    if not (val[0] > 0.98 and val[1] < -0.98):
        raise ValueError("Solar geometry self-test failed")
    # UTC=20:00 at longitude -120 is close to apparent local solar noon.
    val = solar_cos_zenith(pd.DatetimeIndex(["2024-03-20 20:00"]), 40.0, -120.0)
    if val[0] < 0.72:
        raise ValueError("Western-US solar geometry sign test failed")


def preflight():
    solar_selftest()
    for directory in (ROOT, STAGE07, STAGE09A, BASE_RAW):
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError("Required directory unavailable or symlink: " + str(directory))
    if not regular(STAGE07 / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage07 hold marker missing")
    packages = {r["site"]: r for r in rows(MANIFEST, delimiter="\t")}
    if len(packages) != 10:
        raise ValueError("Expected exact ten-site Batch03 package manifest")

    stage07 = json.loads(regular(STAGE07 / "exact_input_manifest.json").read_text())
    selected = {r["site"]: r for r in stage07["sites"]}
    pins = {str(Path(p).resolve()): h for p, h in stage07["input_sha256"].items()}
    if set(selected) != set(packages):
        raise ValueError("Stage07 exact source manifest differs from the ten releases")

    evidence = json.loads(regular(STAGE09A / "evidence_receipt.json").read_text())
    plan = json.loads(regular(STAGE09A / "era5land_request_plan.json").read_text())
    inventory = json.loads(regular(STAGE09A / "site_utc_offset_inventory.json").read_text())
    clock = {r["site"]: r for r in inventory}
    if (evidence.get("requests") != 32 or evidence.get("event_count") != 1924
            or len(plan) != 32 or len(clock) != 7
            or set(clock) != set(EXPECTED_BLOCKERS)):
        raise ValueError("Unexpected Stage09a 32-year/1924-event evidence scope")

    acquired = {s: [] for s in EXPECTED_BLOCKERS}
    seen = set()
    for item in plan:
        site, year = item["site"], int(item["year"])
        if site not in acquired or (site, year) in seen:
            raise ValueError("Unknown or duplicated Stage09a site-year")
        seen.add((site, year))
        if year < int(packages[site]["first_year"]) or year > int(packages[site]["last_year"]):
            raise ValueError("Request year outside selected release")
        where = item["request"]["location"]
        if abs(float(where["latitude"]) - COORD[site][0]) > 1e-5 or abs(float(where["longitude"]) - COORD[site][1]) > 1e-5:
            raise ValueError("Site coordinates differ from Stage08e and Stage09a: " + site)
        acquired[site].append(item)
    for site, items in acquired.items():
        if not items or sum(int(i["blocked_native_records"]) for i in items) != EXPECTED_BLOCKERS[site]:
            raise ValueError("Blocked site-year distribution differs for: " + site)

    for site in sorted(acquired):
        info = selected[site]
        if info["release"] != packages[site]["package"]:
            raise ValueError("Selected release changed: " + site)
        if int(info["native_minutes"]) != (60 if site == "US-MMS" else 30):
            raise ValueError("Wrong native HH/HR interval: " + site)
        source_dir = BASE_RAW / site / "forcing/raw" / info["release"]
        if not source_dir.is_dir() or source_dir.is_symlink():
            raise ValueError("Missing exact release folder: " + site)
        for kind in ("primary", "era"):
            path = regular(Path(info[kind]))
            if path.resolve().parent != source_dir.resolve():
                raise ValueError("Raw meteorological file outside release: " + str(path))
            expected_hash = pins.get(str(path.resolve()))
            if not expected_hash or expected_hash != digest(path):
                raise ValueError("Stage07-pinned met/ERA file changed: " + str(path))
        bifs = sorted(source_dir.glob(f"AMF_{site}_FLUXNET_BIF_*.csv"))
        if site == "US-Me2":
            if bifs or clock[site]["status"] != "NO_RELEASE_BIF_FULLSET_SITE_METADATA_REQUIRED":
                raise ValueError("US-Me2 release clock/BIF inventory changed; investigate before audit")
            if clock[site].get("published_utc_offsets"):
                raise ValueError("US-Me2 unexpectedly now has a published offset")
        else:
            if len(bifs) != 1 or digest(bifs[0]) != BIF_SHA256[site]:
                raise ValueError("BIF count/SHA differs from Stage09h: " + site)
            records = [r for r in rows(bifs[0]) if r.get("VARIABLE", "").strip().upper() == "UTC_OFFSET"]
            values = [r.get("DATAVALUE", "").strip() for r in records]
            if len(values) != 1 or float(values[0]) != PUBLISHED[site]:
                raise ValueError("Unverified or ambiguous BIF offset: " + site)
            if (clock[site]["status"] != "ONE_PUBLISHED_OFFSET_PENDING_VALIDATION"
                    or set(map(str, clock[site]["published_utc_offsets"])) != {str(PUBLISHED[site])}):
                raise ValueError("Pinned Stage09a BIF inventory changed: " + site)
        print(f"PIN VERIFIED {site}: primary+ERA SHA256; "
              f"BIF={('ABSENT' if site=='US-Me2' else '1 PUBLISHED')} "
              f"native={info['native_minutes']}min acquired_years={len(acquired[site])}",
              flush=True)
    return selected, acquired


def read_solar_samples(source, years):
    header = set(pd.read_csv(source, nrows=0).columns)
    if not {"TIMESTAMP_START", "SW_IN_F"}.issubset(header):
        raise ValueError("Raw primary source has no SW_IN_F/TIMESTAMP_START: " + str(source))
    qc_field = "SW_IN_F_QC" if "SW_IN_F_QC" in header else None
    cols = ["TIMESTAMP_START", "SW_IN_F"] + ([qc_field] if qc_field else [])
    frame = pd.read_csv(source, usecols=cols, dtype={"TIMESTAMP_START": str},
                        low_memory=False)
    frame = frame.loc[frame["TIMESTAMP_START"].str[:4].isin({str(y) for y in years})].copy()
    frame["time"] = pd.to_datetime(frame["TIMESTAMP_START"],
                                   format="%Y%m%d%H%M", errors="raise")
    if frame["time"].duplicated().any():
        raise ValueError("Raw source contains duplicate local time stamps")
    sw = pd.to_numeric(frame["SW_IN_F"], errors="coerce")
    valid = np.isfinite(sw) & sw.between(0.0, 1600.0)
    # QC0 is useful but not guaranteed to represent entirely independent
    # measurements. We do not label fallback data as QC0.
    if qc_field:
        good = valid & (pd.to_numeric(frame[qc_field], errors="coerce") == 0)
    else:
        good = valid & False
    frame["radiation"] = sw
    frame["valid"] = valid
    frame["qc0"] = good
    return frame[["time", "radiation", "valid", "qc0"]]


def evaluate(local_time, radiation, latitude, longitude, minutes, offset):
    midpoint = pd.DatetimeIndex(local_time) + pd.Timedelta(minutes=minutes / 2.0)
    utc = midpoint - pd.Timedelta(hours=int(offset))
    cosz = solar_cos_zenith(utc, latitude, longitude)
    sw = np.asarray(radiation, dtype=float)
    bright100 = sw > 100.0
    bright50 = sw > 50.0
    if len(sw) < 100 or bright100.sum() < 20 or bright50.sum() < 20:
        return dict(n=len(sw), bright100=int(bright100.sum()), bright50=int(bright50.sum()),
                    dark100=None, night50=None, correlation=None)
    dark100 = int(np.sum(bright100 & (cosz < -0.05)))
    night50 = int(np.sum(bright50 & (cosz < 0)))
    daylight_proxy = np.maximum(cosz, 0.0)
    corr = float(np.corrcoef(sw, daylight_proxy)[0, 1]) if (
        np.std(sw) > 0 and np.std(daylight_proxy) > 0) else float("nan")
    return dict(n=len(sw), bright100=int(bright100.sum()), bright50=int(bright50.sum()),
                dark100=dark100, night50=night50, correlation=corr)


def fmt(x, digits=4):
    if x is None or not np.isfinite(x):
        return "NA"
    return f"{x:.{digits}f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true",
                       help="Audit original source SHA and pinned evidence scope; no data changes")
    group.add_argument("--analyze", action="store_true",
                       help="Read-only astronomical day/night cross-check at all 32 site-years")
    args = parser.parse_args()

    print("STAGE10A — SOLAR-CLOCK SENSITIVITY | READ ONLY", flush=True)
    selected, acquired = preflight()
    print("STAGE10A PREFLIGHT: original source SHA and clock inventory PASS; "
          "7 sites, 32 site-years, 1924 humidity blockers in pinned plan", flush=True)
    print("SCIENTIFIC HOLD: daylight alignment scores NEVER approve an offset.", flush=True)
    if args.check:
        print("CHECK ONLY: no reports, conversions, files, forcing, DATM or model jobs.", flush=True)
        return

    checked_years = 0
    for site in sorted(acquired):
        info = selected[site]
        years = sorted(int(p["year"]) for p in acquired[site])
        primary = Path(info["primary"])
        samples = read_solar_samples(primary, years)
        step = int(info["native_minutes"])
        center = PUBLISHED.get(site, -8)
        offsets = [center - 1, center, center + 1]
        total_by_offset = {o: {"high_n": 0, "dark100": 0, "bright50": 0,
                              "night50": 0, "corr_weighted": 0.0, "corr_count": 0}
                           for o in offsets}
        counts = {"QC0_ONLY": 0, "VALID_INCLUDING_NON_QC0": 0, "INSUFFICIENT": 0}
        print("\n" + "=" * 110)
        print(f"SITE {site} | BIF UTC_OFFSET={PUBLISHED.get(site, 'NO RELEASE BIF')} "
              f"| test offsets={offsets} | native={step}min | years={years}", flush=True)
        print(f"POSITION: lat={COORD[site][0]:.4f}, lon={COORD[site][1]:.4f} "
              "(Stage08e coordinates, NOT gridded model elevation)", flush=True)
        for year in years:
            sub = samples.loc[samples["time"].dt.year == year]
            if sub.empty:
                raise ValueError(f"No source SW_IN_F samples for {site}:{year}")
            base_valid = sub.loc[sub["valid"]]
            qc0_valid = sub.loc[sub["qc0"]]
            if len(qc0_valid) >= 300 and int((qc0_valid["radiation"] > 100).sum()) >= 20:
                use = qc0_valid
                selection = "QC0_ONLY"
            elif len(base_valid) >= 300 and int((base_valid["radiation"] > 100).sum()) >= 20:
                use = base_valid
                selection = "VALID_INCLUDING_NON_QC0"
            else:
                use = base_valid
                selection = "INSUFFICIENT"
            counts[selection] += 1
            checked_years += 1
            print(f"  YEAR {year}: rows={len(sub)} usable={len(base_valid)} "
                  f"SW_QC0={len(qc0_valid)} selected={len(use)} {selection}", flush=True)
            for offset in offsets:
                m = evaluate(use["time"], use["radiation"],
                             COORD[site][0], COORD[site][1], step, offset)
                acc = total_by_offset[offset]
                if m["dark100"] is not None:
                    acc["high_n"] += m["bright100"]
                    acc["dark100"] += m["dark100"]
                    acc["bright50"] += m["bright50"]
                    acc["night50"] += m["night50"]
                    if m["correlation"] is not None and np.isfinite(m["correlation"]):
                        acc["corr_weighted"] += m["correlation"] * m["n"]
                        acc["corr_count"] += m["n"]
        print("  OFFSET SENSITIVITY: high-SW at astronomical night is a clock diagnostic ONLY")
        for offset in offsets:
            x = total_by_offset[offset]
            nighttime_100_pct = 100 * x["dark100"] / x["high_n"] if x["high_n"] else None
            nighttime_50_pct = 100 * x["night50"] / x["bright50"] if x["bright50"] else None
            approx_corr = x["corr_weighted"] / x["corr_count"] if x["corr_count"] else None
            print(
                f"    UTC_OFFSET={offset:+d} "
                f"SW>100_when_sun_below_-0.05={x['dark100']}/{x['high_n']} "
                f"({fmt(nighttime_100_pct,2)}%) "
                f"SW>50_at_solar_night={x['night50']}/{x['bright50']} "
                f"({fmt(nighttime_50_pct,2)}%) "
                f"mean_annual_SW_cosZen_corr={fmt(approx_corr,3)}",
                flush=True,
            )
        print(f"  YEAR INPUT QUALITY: QC0_ONLY={counts['QC0_ONLY']} "
              f"VALID_INCLUDING_NON_QC0={counts['VALID_INCLUDING_NON_QC0']} "
              f"INSUFFICIENT={counts['INSUFFICIENT']}")
        print("  APPROVAL: NONE. Cloud/shade/topography/reanalysis fill and raw SW quality remain caveats.")
        if site == "US-Me2":
            print("  CRITICAL: US-Me2 -9/-8/-7 are hypotheses, NOT metadata. "
                  "Obtain original release/BADM tower clock documentation.")
        if site == "US-MtB":
            print("  CRITICAL: Stage09i has ~7 C median tower/grid mismatch. "
                  "A solar clock test does NOT explain elevation or air temperature bias.")

    if checked_years != 32:
        raise ValueError("Stage10a did not examine exactly all 32 pinned years")
    print("\n" + "=" * 110)
    print("STAGE10A SUMMARY: sites=7/7 site_years=32/32 blocker_scope=1924/1924 "
          "BIF_published=6/7 formally_approved_offsets=0")
    print("NO TIMEZONE DECISION, NO DEWPOINT REPAIR, NO PFT/DATM/MODEL/CIME/SLURM CHANGES.")
    print("NEXT: evaluate solar evidence together with release clock conventions and "
          "official US-Me2 metadata, then design Stage10b per-event humidity QC.")
    print("=" * 110)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE10A STOP:", str(exc), file=sys.stderr, flush=True)
        sys.exit(2)
