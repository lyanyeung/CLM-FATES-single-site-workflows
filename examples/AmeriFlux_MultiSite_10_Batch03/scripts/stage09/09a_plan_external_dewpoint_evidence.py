#!/usr/bin/env python3
"""Batch03 Stage09a: pin external dewpoint evidence needs; NO downloads.

Reads Stage08e yearly acquisition inventory, Stage08f MDS screening,
checks original Batch03 BIF UTC_OFFSET metadata without inferring it from
longitude, and drafts CDS ERA5-Land hourly time-series per-site-year requests.
--check writes nothing; --run creates a fresh report, NOT forcing or DATM.
"""
import argparse
import csv
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE = Path(__file__).resolve().parents[2]
STAGE08E = ROOT / "reports/stage08e_alternatives_20261022T032727Z_b122e5b0"
STAGE08F = ROOT / "reports/stage08f_mds_pairs_20261022T033321Z_7591f948"
STAGE07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
EXPECTED = {"US-Kon":229,"US-MMS":18,"US-Me2":4,"US-Me6":1,
            "US-MtB":15,"US-NR1":173,"US-NR3":1484}
VARIABLES = ["2m_temperature","2m_dewpoint_temperature","surface_pressure"]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path, sep=","):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=sep))


def utc_inventory(site, release):
    if site == "US-Me2":
        return [], "NO_RELEASE_BIF_FULLSET_SITE_METADATA_REQUIRED"
    raw = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE") / site / "forcing/raw" / release
    matches = sorted(raw.glob(f"AMF_{site}_FLUXNET_BIF_*.csv"))
    if len(matches) != 1:
        return [], f"BIF_COUNT_{len(matches)}_REVIEW"
    records = read_csv(matches[0])
    found = []
    for r in records:
        if (r.get("VARIABLE") or "").strip().upper() == "UTC_OFFSET":
            found.append({"group_id": r.get("GROUP_ID", ""),
                          "offset_as_published": r.get("DATAVALUE", ""),
                          "source": str(matches[0])})
    if not found:
        return [], "BIF_UTC_OFFSET_NOT_RECORDED"
    unique = sorted({r["offset_as_published"] for r in found if r["offset_as_published"]})
    status = ("ONE_PUBLISHED_OFFSET_PENDING_VALIDATION" if len(unique) == 1
              else "MULTIPLE_PUBLISHED_OFFSETS_REVIEW")
    return found, status


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = ap.parse_args()

    for p in (ROOT, STAGE08E, STAGE08F, STAGE07):
        if not p.is_dir() or p.is_symlink():
            raise ValueError("Missing expected Batch03 evidence directory: " + str(p))
    if not (STAGE07 / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage07 incomplete marker is missing")

    e_policy = json.loads((STAGE08E/"evidence_policy.json").read_text())
    f_policy = json.loads((STAGE08F/"policy.json").read_text())
    e_rows_path = STAGE08E/"external_humidity_acquisition_years.csv"
    f_rows_path = STAGE08F/"mds_pair_site_summary.csv"
    f_detail_path = STAGE08F/"mds_pair_at_1924_blockers.csv"
    if (int(e_policy["records"])!=1924
          or Path(f_policy["stage08e_evidence"]).resolve()!=STAGE08E
          or sha(STAGE08E/"raw_alternatives_at_blockers.csv")!=f_policy["stage08e_evidence_sha256"]
          or int(f_policy["records"])!=1924):
        raise ValueError("Stage08e/f immutable evidence lineage did not match")
    e_rows = read_csv(e_rows_path)
    f_rows = read_csv(f_rows_path)
    manifest = {r["site"]:r for r in read_csv(HERE/"sites.tsv", sep="\t")}
    selected = {r["site"]:r for r in json.loads((STAGE07/"exact_input_manifest.json").read_text())["sites"]}
    if (set(manifest)!={r["site"] for r in selected.values()}
            or set(EXPECTED)!={r["site"] for r in f_rows}
            or len(f_rows)!=7):
        raise ValueError("Incorrect site manifest or Stage08f inventory")
    f_by_site = {r["site"]:r for r in f_rows}
    if (sum(int(r["blockers"]) for r in f_rows)!=1924
            or sum(int(r["MDS_pair_physical_pass"]) for r in f_rows)!=1535
            or sum(int(r["MDS_VPD_valid_retained_TA"]) for r in f_rows)!=421):
        raise ValueError("MDS evidence totals unexpectedly changed")
    if any(int(f_by_site[s]["blockers"])!=n for s,n in EXPECTED.items()):
        raise ValueError("MDS site blocker counts differ")
    if len(e_rows)==0:
        raise ValueError("No requested years in Stage08e evidence")
    years_by_site = defaultdict(list)
    coverage = defaultdict(int)
    for r in e_rows:
        site = r["site"]
        if site not in EXPECTED:
            raise ValueError("Unexpected Batch03 external request site")
        year = int(r["year"])
        if year < int(manifest[site]["first_year"]) or year > int(manifest[site]["last_year"]):
            raise ValueError("Request outside release years")
        years_by_site[site].append(year)
        coverage[site] += int(r["blocked_native_rows"])
    if any(coverage[s]!=EXPECTED[s] for s in EXPECTED):
        raise ValueError("External acquisition event counts differ")
    if any(len(years)!=len(set(years)) for years in years_by_site.values()):
        raise ValueError("Repeated request year")

    tz_rows, plans = [], []
    for site in EXPECTED:
        release = manifest[site]["package"]
        tz, status = utc_inventory(site,release)
        tz_rows.append({"site":site,"status":status,"release":release,
            "published_utc_offsets": [r["offset_as_published"] for r in tz],
            "metadata_groups": tz,
            "note": "Explicit UTC_OFFSET approval required; FLUXNET timestamp START is local standard time, no DST."})
        site_plan = [r for r in e_rows if r["site"]==site]
        for row in sorted(site_plan,key=lambda r:int(r["year"])):
            year=int(row["year"])
            # Three-day padding around a complete year is sufficient for all
            # ordinary continental-US UTC offsets once separately approved.
            # Do not resample or align timestamps in this stage.
            request = {"data_format":"netcdf",
                "date":[f"{year-1}-12-29", f"{year+1}-01-03"],
                "location":{"latitude":float(row["latitude"]),
                            "longitude":float(row["longitude"])},
                "variable":VARIABLES}
            plans.append({"site":site,"year":year,
                "blocked_native_records":int(row["blocked_native_rows"]),
                "data_provider":"CDS reanalysis-era5-land-timeseries",
                "dataset":"reanalysis-era5-land-timeseries",
                "request":request,"utc_offset_status":status,
                "approval":"REQUEST_PLAN_ONLY_NO_CDS_CALL",
                "clock_basis":"FLUXNET_LOCAL_STANDARD_TIME; UTC_OFFSET must be verified before matching"})
        print(f"PLAN: {site:<7} years={sorted(years_by_site[site])}"
              f" blockers={coverage[site]} UTC_OFFSET={status}"
              f" values={[r['offset_as_published'] for r in tz]}",flush=True)
    print("STAGE09A PREFLIGHT: 7/7 sites, 1924 source blockers,"
          f" {len(plans)} yearly requests staged; NO API requests/data written",flush=True)
    if args.check:
        print("CHECK ONLY: no report created, no downloads")
        return 0

    root=ROOT/"reports"
    out=root/("stage09a_external_dewpoint_plan_"+
              datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    (out/"era5land_request_plan.json").write_text(json.dumps(plans,indent=2)+"\n")
    (out/"site_utc_offset_inventory.json").write_text(json.dumps(tz_rows,indent=2)+"\n")
    with (out/"request_summary.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["site","year","blocked_native_records",
            "latitude","longitude","utc_offset_status","approval"])
        writer.writeheader()
        for r in plans:
            item={"site":r["site"],"year":r["year"],
                  "blocked_native_records":r["blocked_native_records"],
                  "latitude":r["request"]["location"]["latitude"],
                  "longitude":r["request"]["location"]["longitude"],
                  "utc_offset_status":r["utc_offset_status"],"approval":r["approval"]}
            writer.writerow(item)
    (out/"evidence_receipt.json").write_text(json.dumps({
      "stage08e_request_years_sha256":sha(e_rows_path),
      "stage08f_mds_summary_sha256":sha(f_rows_path),
      "stage08f_mds_detail_sha256":sha(f_detail_path),
      "site_manifest_sha256":sha(HERE/"sites.tsv"),
      "requests":len(plans),"event_count":1924,
      "notes":["CDS API is NOT invoked by this script.",
        "CDS hourly series represents a 0.1-degree grid point, not tower readings.",
        "The time variable in ERA5-Land is UTC; FLUXNET timestamps are local standard.",
        "Require documented source UTC_OFFSET for each site before merging.",
        "ERA5-Land atmospheric forcing derives from ERA5 and is not independent field observation.",
        "Dewpoint-derived vapor pressure still requires humidity and QC review.",
        "No raw forcing, candidate, DATM, PFT or Slurm job changed."]
    },indent=2)+"\n")
    print("STAGE09A SUMMARY: acquisition_plan_only=True"
          f" sites=7 blockers=1924 annual_requests={len(plans)}")
    print("REPORT DIR:",out)


if __name__=="__main__":
    main()
