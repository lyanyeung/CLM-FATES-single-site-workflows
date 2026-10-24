#!/usr/bin/env python3
"""Stage11O: provenance-pinned ERA5-Land March 2025 US-NC2 evidence download.

--self-test: local synthetic request/clock checks, zero I/O writes.
--check: show exact CDS point/time request, auth and destination; zero writes.
--download: ONE request, write NEW isolated original NetCDF/ZIP and SHA receipt.
--audit: inspect downloaded archive, exact UTC hours, CF units and physics.

This code NEVER selects the tower's true UTC offset, changes Stage07/11h/11l,
changes site temperature or humidity, creates DATM/CIME/Slurm jobs, or
accepts a scientific RH replacement. ERA5-Land is ERA5-driven, not tower truth.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import zipfile

SITE = "US-NC2"
LAT, LON, ELEV_M = 35.8030, -76.6685, 5
PUBLISHED_OFFSET = -5
DATASET = "reanalysis-era5-land-timeseries"
START, END = "2025-03-16", "2025-03-27"
VARIABLES = ("2m_temperature", "2m_dewpoint_temperature", "surface_pressure")
EXPECTED = {"t2m": "K", "d2m": "K", "sp": "Pa"}
EXP = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
OUT_DIR = EXP / "external_evidence/era5land_timeseries/US-NC2/2025"
STEM = "ERA5Land_US-NC2_2025_Mar16_Mar27_t2m_d2m_sp"
EDGES = (
    ("MAR18_NEW_START", "202503181800", "202503181830"),
    ("MAR23_OLD_START", "202503230830", "202503230900"),
    ("MAR23_NEW_END", "202503231500", "202503231530"),
    ("MAR25_NEW_END", "202503251000", "202503251030"),
)


def request():
    return {
        "variable": list(VARIABLES),
        "date": [START, END],
        "location": {"latitude": LAT, "longitude": LON},
        "data_format": "netcdf",
    }


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def expected_hours():
    first = datetime.fromisoformat(START).replace(tzinfo=timezone.utc)
    last = datetime.fromisoformat(END).replace(tzinfo=timezone.utc) + timedelta(hours=23)
    length = int((last - first).total_seconds() // 3600) + 1
    return [first + timedelta(hours=i) for i in range(length)]


def candidate_utc(native_stamp, offset):
    local = datetime.strptime(native_stamp, "%Y%m%d%H%M")
    # Hypothesis only: native LST = UTC + UTC_OFFSET. No adopted correction.
    return (local - timedelta(hours=offset)).replace(tzinfo=timezone.utc)


def self_test():
    req = request()
    if req != {
        "variable": ["2m_temperature", "2m_dewpoint_temperature", "surface_pressure"],
        "date": ["2025-03-16", "2025-03-27"],
        "location": {"latitude": 35.8030, "longitude": -76.6685},
        "data_format": "netcdf",
    }:
        raise AssertionError("Unexpected request contract")
    hours = expected_hours()
    assert len(hours) == 12 * 24 and len(set(hours)) == len(hours)
    assert hours[0].isoformat() == "2025-03-16T00:00:00+00:00"
    assert hours[-1].isoformat() == "2025-03-27T23:00:00+00:00"
    for label, l, r in EDGES:
        assert (datetime.strptime(r, "%Y%m%d%H%M")
                - datetime.strptime(l, "%Y%m%d%H%M")) == timedelta(minutes=30), label
        for offset in (-6, -5, -4):
            assert hours[0] <= candidate_utc(l, offset) <= hours[-1]
            assert hours[0] <= candidate_utc(r, offset) <= hours[-1]
    print("STAGE11O SELF-TEST PASS: 288 expected UTC hours, four boundaries,"
          " -6/-5/-4 clock hypotheses, no source writes")


def classify(path):
    if path.stat().st_size < 1024:
        raise ValueError("CDS download too small; partial retained")
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            if zf.testzip() is not None:
                raise ValueError("ZIP CRC failure")
            members = [x for x in zf.infolist() if not x.is_dir()]
            if not members or len(members) > 8:
                raise ValueError("Unexpected ZIP member count")
            for x in members:
                if (not x.filename.lower().endswith(".nc") or
                        x.filename.startswith("/") or ".." in Path(x.filename).parts
                        or x.file_size > 40_000_000):
                    raise ValueError("Invalid ZIP member " + x.filename)
        return ".zip"
    with path.open("rb") as stream:
        magic = stream.read(8)
    if magic.startswith(b"CDF") or magic == b"\x89HDF\r\n\x1a\n":
        return ".nc"
    raise ValueError("Unrecognized CDS response, not ZIP/NetCDF")


def audit_dataset(path):
    import numpy as np
    from netCDF4 import Dataset, num2date
    got = {}
    meta = {"variables": {}, "member_names": []}
    expected = expected_hours()

    def inspect(ds, name):
        times = ds.variables.get("valid_time", ds.variables.get("time"))
        if times is None:
            raise ValueError("No CF valid_time/time variable: " + name)
        raw = num2date(times[:], getattr(times, "units", ""),
                      calendar=getattr(times, "calendar", "standard"),
                      only_use_cftime_datetimes=False,
                      only_use_python_datetimes=True)
        parsed = [datetime(v.year, v.month, v.day, v.hour, v.minute, v.second,
                           tzinfo=timezone.utc) for v in raw]
        if parsed != expected:
            raise ValueError("Unexpected/missing/reordered UTC hour coverage: " + name)
        lat = float(np.asarray(ds.variables["latitude"][:]).reshape(-1)[0])
        lon = float(np.asarray(ds.variables["longitude"][:]).reshape(-1)[0])
        if abs(lat - LAT) > .151 or abs(lon - LON) > .151:
            raise ValueError("Unexpected returned grid point " + repr((lat, lon)))
        if "grid" in meta and max(
                abs(lat - meta["grid"]["latitude"]),
                abs(lon - meta["grid"]["longitude"])) > 1e-5:
            raise ValueError("Returned fields have inconsistent grid points")
        meta["grid"] = {"latitude": lat, "longitude": lon}
        for field, unit in EXPECTED.items():
            if field not in ds.variables:
                continue
            if field in got:
                raise ValueError("Duplicate NetCDF field " + field)
            v = ds.variables[field]
            if getattr(v, "units", "") != unit:
                raise ValueError("Unexpected units for " + field)
            values = np.asarray(np.ma.asarray(v[:]).filled(np.nan),
                                dtype=float).reshape(-1)
            if len(values) != len(expected) or not np.isfinite(values).all():
                raise ValueError("Missing/nonfinite values in " + field)
            if field in ("t2m", "d2m") and ((values < 160) | (values > 340)).any():
                raise ValueError("Grossly invalid temperature in " + field)
            if field == "sp" and ((values < 40000) | (values > 110000)).any():
                raise ValueError("Grossly invalid pressure")
            got[field] = values
            meta["variables"][field] = {"units": unit, "min": float(values.min()),
                                        "max": float(values.max()), "hours": len(values)}
        meta["member_names"].append(name)

    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            for item in zf.infolist():
                if item.is_dir():
                    continue
                with Dataset("inmemory.nc", "r", memory=zf.read(item)) as ds:
                    inspect(ds, item.filename)
    else:
        with Dataset(str(path), "r") as ds:
            inspect(ds, path.name)

    if set(got) != set(EXPECTED):
        raise ValueError("Missing ERA5-Land t2m/d2m/sp NetCDF groups")
    if (got["d2m"] > got["t2m"] + 0.1).any():
        raise ValueError("Dewpoint exceeds temperature by >0.1 K")
    meta["utc_hours"] = len(expected)
    meta["source"] = DATASET
    meta["status"] = "NETCDF_STRUCTURALLY_VALID_NOT_CLOCK_OR_SCIENCE_APPROVED"
    return meta


def chosen_existing():
    files = [OUT_DIR / (STEM + suffix) for suffix in (".zip", ".nc")]
    present = [x for x in files if x.exists()]
    if len(present) != 1 or present[0].is_symlink() or not present[0].is_file():
        raise ValueError("Expected exactly one previously downloaded artifact")
    return present[0]


def credential_status():
    return (Path.home() / ".cdsapirc").is_file() or bool(os.getenv("CDSAPI_KEY"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--download", action="store_true")
    group.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    print("STAGE11O CDS DATASET:", DATASET)
    print("US-NC2 source BIF: latitude", LAT, "longitude", LON,
          "elevation", ELEV_M, "m; PUBLISHED UTC_OFFSET", PUBLISHED_OFFSET,
          "NOT APPROVED FOR TIME CONVERSION")
    print("REQUEST:", json.dumps(request(), sort_keys=True))
    print("CDS API AVAILABLE:", importlib.util.find_spec("cdsapi") is not None)
    print("CDS CREDENTIALS:", "PRESENT (masked)" if credential_status() else "MISSING")
    print("TARGET ROOT:", OUT_DIR)
    print("NO ERA/tower native time-zone shift authorised.")
    if args.check:
        print("STAGE11O CHECK ONLY: zero CDS requests and zero output writes")
        return
    if args.audit:
        path = chosen_existing()
        receipt = OUT_DIR / (STEM + ".receipt.json")
        if not receipt.is_file() or receipt.is_symlink():
            raise ValueError("Receipt absent or unsafe: " + str(receipt))
        record = json.loads(receipt.read_text(encoding="utf-8"))
        if (record.get("dataset") != DATASET or record.get("request") != request()
                or record.get("site") != SITE
                or record.get("source_sha256") != sha256(path)):
            raise ValueError("Artifact SHA256 or request changed")
        verified = audit_dataset(path)
        print("STAGE11O AUDIT:", json.dumps(verified, sort_keys=True))
        print("STAGE11O SUMMARY: 1/1 external artifact checksum + structural QA PASS; clock_approved=0 science_repair_approved=0")
        return
    if not credential_status():
        raise ValueError("Missing ~/.cdsapirc/CDSAPI_KEY; no request made")
    if importlib.util.find_spec("cdsapi") is None:
        raise ValueError("cdsapi is not installed; no request made")
    if OUT_DIR.is_symlink():
        raise ValueError("Output directory is a symlink")
    for suffix in (".zip", ".nc", ".receipt.json", ".download.partial"):
        if (OUT_DIR / (STEM + suffix)).exists():
            raise FileExistsError("Existing file blocks new download; no overwrite: " +
                                 str(OUT_DIR / (STEM + suffix)))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    import cdsapi
    temp = OUT_DIR / (STEM + ".download.partial")
    print("STAGE11O ONE CDS REQUEST STARTED: exact 2025-03-16 through 2025-03-27 UTC", flush=True)
    cdsapi.Client().retrieve(DATASET, request()).download(str(temp))
    suffix = classify(temp)
    valid = audit_dataset(temp)
    final = OUT_DIR / (STEM + suffix)
    if final.exists():
        raise FileExistsError("Target already exists; keeping partial unmodified")
    os.rename(temp, final)
    receipt = {
        "site": SITE, "dataset": DATASET, "request": request(),
        "original_BIF_location": {"latitude": LAT, "longitude": LON, "elevation_m": ELEV_M},
        "published_utc_offset": PUBLISHED_OFFSET,
        "clock_approved": False, "source": "CDS ERA5-Land point series",
        "status": "DOWNLOADED_AND_STRUCTURALLY_VALID_NOT_SCIENCE_APPROVED",
        "source_file": str(final), "source_sha256": sha256(final),
        "bytes": final.stat().st_size,
        "grid_audit": valid, "created_utc": datetime.now(timezone.utc).isoformat(),
        "changed_original_or_shadow_forcing": False,
    }
    with (OUT_DIR / (STEM + ".receipt.json")).open("x", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")
    print("STAGE11O ARTIFACT:", final)
    print("STAGE11O ARTIFACT SHA256:", receipt["source_sha256"])
    print("STAGE11O STRUCTURAL AUDIT:", json.dumps(valid, sort_keys=True))
    print("STAGE11O SUMMARY: 1/1 downloaded, SHA-pinned and physical-range-screened;")
    print("  UTC_OFFSET approval=0; boundary repair=0; Postv5=0; DATM=0; spinup=0")


if __name__ == "__main__":
    main()
