#!/usr/bin/env python3
"""AmeriFlux Batch02 Stage13: audit and plan independent ERA5 dewpoint retrieval.

READ-ONLY by default. --write-plan creates an isolated request manifest only.
NEVER edits raw data, Stage07–12 products, forcing, DATM, CIME or Slurm jobs.
The ERA5 point (0.25 degree nearest grid) is NOT a tower observation.
No local-time to UTC mapping, or half-hourly interpolation, is performed.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
STAGE08 = BASE / "raw_RH_sensitivity_20261022T013805Z_aadaffee"
STAGE11 = BASE / "stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
SITES = ("US-EML", "US-GLE", "US-Ho1", "US-ICh", "US-ICt")
HO1_FALLBACK = (45.204, -68.7402)
DATASET = "reanalysis-era5-single-levels-timeseries"
VARIABLES = ("2m_temperature", "2m_dewpoint_temperature", "surface_pressure")

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()

def verify(report, manifest):
    if not report.is_dir() or not (report / "DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage11 incomplete/not original")
    m = json.loads((report / "manifest.json").read_text())
    if m.get("scientific_status") != "HOLD_INDEPENDENT_VALIDATION_REQUIRED":
        raise ValueError("Stage11 science status differs")
    if int(m["n_target_rows"]) != 4884:
        raise ValueError("Stage11 scope differs")
    r = Path(m["source_stage08"]).resolve()
    if r != STAGE08.resolve() or not (r / "INCOMPLETE_SENSITIVITY_DO_NOT_USE_FOR_DATM").is_file():
        raise ValueError("Expected the pinned Stage08 failure trial")
    for p, digest in m["input_hashes"].items():
        if sha(p) != digest:
            raise ValueError("Pinned source or Stage08 output changed: " + str(p))
    selection = json.loads((r / "exact_input_manifest.json").read_text())
    if selection["algorithm"] != "STAGE07_BLOCKERS_SAME_RELEASE_RAW_RH_SENSITIVITY":
        raise ValueError("Wrong Stage08 algorithm")
    return {s["site"]: s for s in selection["sites"]}, m

def metadata(item):
    raw = Path(item["primary"]).parent
    csv_files = sorted(raw.glob("*_BIF_*.csv"))
    if item["site"] == "US-Ho1":
        if csv_files:
            raise ValueError("US-Ho1 unexpectedly gained BIF; review coordinate source")
        lat, lon = HO1_FALLBACK
        source = "US-Ho1 official site-page fallback (not embedded package)"
        bif = None
        offsets = []
    else:
        if len(csv_files) != 1:
            raise ValueError(f"{item['site']}: expected exactly one site BIF; got {len(csv_files)}")
        bif = csv_files[0]
        coords = {"LOCATION_LAT": set(), "LOCATION_LONG": set()}
        offsets = []
        with bif.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not {"VARIABLE", "DATAVALUE"}.issubset(reader.fieldnames or []):
                raise ValueError("Invalid BIF format: " + str(bif))
            for row in reader:
                if row.get("SITE_ID", "").strip() not in ("", item["site"]):
                    raise ValueError("BIF mixed site rows")
                key = row["VARIABLE"].strip().upper()
                value = (row.get("DATAVALUE") or "").strip()
                if not value or value == "-9999": continue
                if key in coords:
                    coords[key].add(float(value))
                elif "TIMEZONE" in key or "UTC_OFFSET" in key:
                    offsets.append({"key": key, "raw_value": value})
        if any(len(v) != 1 for v in coords.values()):
            raise ValueError("BIF coordinates missing/ambiguous: " + item["site"])
        lat = next(iter(coords["LOCATION_LAT"]))
        lon = next(iter(coords["LOCATION_LONG"]))
        source = "Exact site release BIF"
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Coordinate out of range: " + item["site"])
    return dict(latitude=lat, longitude=lon, coordinate_source=source,
                bif_path=str(bif) if bif else None,
                bif_sha256=sha(bif) if bif else None,
                timezone_metadata=offsets,
                tower_local_standard_to_UTC_offset_hours="UNRESOLVED_MANUAL_VERIFICATION_REQUIRED")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage11-root", type=Path, default=STAGE11)
    parser.add_argument("--write-plan", action="store_true")
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    info, m = verify(args.stage11_root.resolve(), None)
    plan = []
    for site in SITES:
        row = info[site]
        met = metadata(row)
        # Two extra UTC calendar days cover local-standard offsets at both boundaries.
        request = dict(variable=list(VARIABLES),
            location={"longitude": met["longitude"], "latitude": met["latitude"]},
            date=[f"{int(row['first_year'])-1}-12-30/{int(row['last_year'])+1}-01-02"],
            data_format="netcdf")
        entry = dict(site=site, first_year=row["first_year"],
                     last_year=row["last_year"], native_minutes=row["native_minutes"],
                     release=row["release"], metadata=met,
                     cds_dataset=DATASET, cds_request=request,
                     expected_time_axis="ERA5 hourly UTC; tower timestamps use local standard time",
                     note="Retrieve point, not tower height; nearest 0.25 degree grid cell, check elevation bias.")
        plan.append(entry)
        print("SITE",site,"COORD",met["latitude"],met["longitude"],
              "SOURCE",met["coordinate_source"],"UTC offset: UNRESOLVED")
        print("CDS REQUEST", json.dumps(request, sort_keys=True))
    print("STAGE13 PREFLIGHT PASS: 5 locations, 5 CDS point-series requests.")
    print("No forcing file and no model job has been created.")
    if not args.write_plan:
        print("CHECK ONLY: no files written.")
        return 0
    root = (args.output_root.expanduser().resolve() if args.output_root else
            Path.home()/("AmeriFlux_Batch02_stage13_plan_" +
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") +
            "_" + uuid4().hex[:8]))
    source_roots = [BASE.resolve(), Path(args.stage11_root).resolve()]
    if root.exists() or any(root == x or x in root.parents or x in root.parents for x in source_roots):
        raise ValueError("Output must be fresh and outside source trees")
    root.mkdir(parents=True, exist_ok=False)
    receipt=dict(schema="Stage13_ERA5_TD2M_REQUEST_PLAN_v2", algorithm="CDS_ERA5_POINT_SERIES_DEWPOINT",
                 dataset=DATASET, variables=list(VARIABLES),
                 date_request_format="one YYYY-MM-DD/YYYY-MM-DD interval string in a one-element list",
                 stage11_root=str(Path(args.stage11_root).resolve()),
                 stage11_manifest_sha256=sha(Path(args.stage11_root)/"manifest.json"),
                 stage11_proposals_sha256=sha(Path(args.stage11_root)/"cold_humidity_repair_proposals.csv"),
                 script_sha256=sha(Path(__file__)), sites=plan,
                 science_status="RETRIEVAL_PLAN_ONLY_NO_HUMIDITY_APPROVAL",
                 blockers=["UTC offset of tower local standard time requires explicit release-specific confirmation",
                           "ERA5 point elevation/landscape difference must be assessed",
                           "ERA5 is a reanalysis, not independent observed tower humidity",
                           "ERA5 hourly is NOT native 30-minute forcing; no automatic interpolation"],
                 constraints="Do not treat manifest as data download, DATM approval or model-ready forcing")
    (root/"request_plan.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    (root/"DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text("Requests only, no scientific or model approval.\n")
    print("STAGE13 REQUEST PLAN:",root/"request_plan.json")
    print("No CDS request issued. Authenticate and accept CDS licence before any download.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
