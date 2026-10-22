#!/usr/bin/env python3
"""Batch03 Stage09b: one explicit CDS ERA5-Land point/year retrieval.

Default and --check: read-only, no CDS request. --run: download exactly ONE
requested site-year from the pinned Stage09a plan, into isolated external
evidence storage. Never edits raw tower/ERA, QCv5, DATM, cases or jobs.

A download is NOT quality acceptance or a timestamp alignment. This script
deliberately does not interpret local time or fill any humidity blockers.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import zipfile

EXP = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE = Path(__file__).resolve().parents[2]
PLAN_ROOT = EXP / "reports/stage09a_external_dewpoint_plan_20261022T034051Z_437c9c0c"
EXTERNAL_ROOT = EXP / "external_evidence/era5land_timeseries"
DATASET = "reanalysis-era5-land-timeseries"
EXPECTED_SITES = {"US-Kon","US-MMS","US-Me2","US-Me6","US-MtB","US-NR1","US-NR3"}
VARIABLES = {"2m_temperature","2m_dewpoint_temperature","surface_pressure"}
DEFAULT_SITE = "US-NR3"
DEFAULT_YEAR = 2022


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def check_plan():
    for p in (EXP,PLAN_ROOT):
        if not p.is_dir() or p.is_symlink():
            raise RuntimeError("Missing / unsafe Batch03 evidence folder: "+str(p))
    marker=EXP/"qcv5_native_trial_20261022T024559Z_36c46e58/INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"
    if not marker.is_file():
        raise RuntimeError("Stage07 incomplete safety marker unexpectedly absent")
    rec=json.loads((PLAN_ROOT/"evidence_receipt.json").read_text(encoding="utf-8"))
    e=EXP/"reports/stage08e_alternatives_20261022T032727Z_b122e5b0/external_humidity_acquisition_years.csv"
    f=EXP/"reports/stage08f_mds_pairs_20261022T033321Z_7591f948/mds_pair_site_summary.csv"
    d=EXP/"reports/stage08f_mds_pairs_20261022T033321Z_7591f948/mds_pair_at_1924_blockers.csv"
    manifest=BASE/"sites.tsv"
    for file, key in ((e,"stage08e_request_years_sha256"),
                      (f,"stage08f_mds_summary_sha256"),
                      (d,"stage08f_mds_detail_sha256"),
                      (manifest,"site_manifest_sha256")):
        if not file.is_file() or sha(file)!=rec[key]:
            raise RuntimeError("Stage09a pinned evidence changed: "+str(file))
    rows=json.loads((PLAN_ROOT/"era5land_request_plan.json").read_text(encoding="utf-8"))
    clocks=json.loads((PLAN_ROOT/"site_utc_offset_inventory.json").read_text(encoding="utf-8"))
    if len(rows)!=32 or rec["requests"]!=32 or rec["event_count"]!=1924:
        raise RuntimeError("Unexpected Stage09a request count")
    if {r["site"] for r in rows}!=EXPECTED_SITES or len(clocks)!=7:
        raise RuntimeError("Unexpected site inventory")
    if {r["site"] for r in clocks}!=EXPECTED_SITES:
        raise RuntimeError("Clock metadata site inventory mismatch")
    seen=set()
    for r in rows:
        key=(r["site"],int(r["year"]))
        if key in seen:
            raise RuntimeError("Duplicate site/year request")
        seen.add(key)
        req=r["request"]
        if (r["data_provider"]!="CDS reanalysis-era5-land-timeseries"
            or r["dataset"]!=DATASET
            or req.get("data_format")!="netcdf"
            or set(req.get("variable",[]))!=VARIABLES
            or r["approval"]!="REQUEST_PLAN_ONLY_NO_CDS_CALL"
            or not isinstance(req.get("location",{}).get("latitude"),(int,float))
            or not isinstance(req.get("location",{}).get("longitude"),(int,float))):
            raise RuntimeError("Unexpected request fields: "+repr(key))
        if (not isinstance(req.get("date"),list) or len(req["date"])!=2
            or not all(isinstance(x,str) and len(x)==10 for x in req["date"])):
            raise RuntimeError("Unexpected date window: "+repr(key))
        if int(r["blocked_native_records"])<1:
            raise RuntimeError("Unexpected empty event count: "+repr(key))
    if sum(int(r["blocked_native_records"]) for r in rows)!=1924:
        raise RuntimeError("Stage09a event total differs")
    return rows,clocks


def classify_response(path):
    size=path.stat().st_size
    if size<1024:
        raise RuntimeError("CDS response unexpectedly small; kept as .partial")
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            members=[a for a in zf.infolist() if not a.is_dir()]
            if not members or not any(a.filename.lower().endswith(".nc") for a in members):
                raise RuntimeError("ZIP response contains no NetCDF files")
            if any(a.filename.startswith("/") or ".." in Path(a.filename).parts for a in members):
                raise RuntimeError("Unsafe ZIP member path; no extraction attempted")
            failed=zf.testzip()
            if failed is not None:
                raise RuntimeError("ZIP CRC error for "+failed)
            return ".zip",dict(format="ZIP_NETCDF",
                members=[dict(name=a.filename,bytes=a.file_size,crc32=a.CRC)
                         for a in members])
    with path.open("rb") as stream:
        magic=stream.read(8)
    if magic.startswith(b"CDF") or magic==b"\x89HDF\r\n\x1a\n":
        return ".nc",dict(format="NETCDF",members=[])
    raise RuntimeError("Unrecognized CDS response (not ZIP or NetCDF); kept as .partial")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--site",default=DEFAULT_SITE)
    p.add_argument("--year",type=int,default=DEFAULT_YEAR)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    a=p.parse_args()
    rows,clocks=check_plan()
    selected=[r for r in rows if r["site"]==a.site and int(r["year"])==a.year]
    if len(selected)!=1:
        p.error("Site/year is not among the 32 Stage09a approved-for-planning requests")
    row=selected[0]
    # The CDS time-series API requires a single date-range expression.
    # Reject stale Stage09a endpoint-only plans: no downloads with two dates.
    date = row["request"].get("date")
    expected_date = [f"{a.year-1}-12-29/{a.year+1}-01-03"]
    if date != expected_date:
        raise ValueError("Unsafe CDS date range in Stage09a plan: regenerate it with the updated Stage09a script (expected "+str(expected_date)+")")
    clock=next(x for x in clocks if x["site"]==a.site)
    dest=EXTERNAL_ROOT/a.site/str(a.year)
    name=f"ERA5Land_{a.site}_{a.year}_t2m_d2m_sp"
    print("STAGE09B SOURCE:",PLAN_ROOT)
    print("STAGE09B REQUEST:",json.dumps(row["request"],sort_keys=True))
    print("CLOCK:",clock["status"],clock["published_utc_offsets"])
    print("WARNING: no time alignment; local standard time UTC_OFFSET still needs validation.")
    print("CDSAPI:", "installed" if importlib.util.find_spec("cdsapi") else "MISSING (install cdsapi)")
    hasrc=(Path.home()/".cdsapirc").is_file() or bool(os.getenv("CDSAPI_KEY"))
    print("CDS credentials:", "PRESENT (not printed)" if hasrc else "NOT CONFIGURED")
    print("TARGET DIR:",dest)
    print("STAGE09B PREFLIGHT: 32 source requests verified; selected 1 site-year; no API call")
    if a.check:
        print("CHECK ONLY: no data/reports written")
        return
    if not hasrc:
        raise RuntimeError("Set up ~/.cdsapirc in IRIDIS first; no API request made")
    if importlib.util.find_spec("cdsapi") is None:
        raise RuntimeError("cdsapi not installed in environment; no API request made")
    import cdsapi
    if dest.is_symlink():
        raise RuntimeError("Refusing symlink output destination")
    dest.mkdir(parents=True,exist_ok=True)
    if dest.is_symlink():
        raise RuntimeError("Refusing symlink output destination")
    existing=[x for x in (dest/(name+".nc"),dest/(name+".zip"),dest/(name+".receipt.json")) if x.exists()]
    if existing:
        raise FileExistsError("Previous output exists; refusing to overwrite: "+str(existing))
    tmp=dest/(name+".download.partial")
    if tmp.exists():
        raise FileExistsError("Stale/in-progress partial response exists; inspect manually: "+str(tmp))
    print("START CDS RETRIEVAL: ONE request; dataset",DATASET,flush=True)
    client=cdsapi.Client()
    # The request is used verbatim from the hashed Stage09a plan.
    client.retrieve(DATASET,row["request"]).download(str(tmp))
    suffix,meta=classify_response(tmp)
    result=dest/(name+suffix)
    if result.exists():
        raise FileExistsError("Target appeared during transfer; partial retained")
    os.rename(tmp,result)
    receipt=dict(site=a.site,year=a.year,dataset=DATASET,request=row["request"],
                 request_source=str(PLAN_ROOT/"era5land_request_plan.json"),
                 stage09a_receipt_sha256=sha(PLAN_ROOT/"evidence_receipt.json"),
                 utc_offset_status=clock["status"],
                 raw_utc_time_not_joined=True,
                 status="DOWNLOADED_ONLY_NOT_QC_ACCEPTED",
                 created_utc=datetime.now(timezone.utc).isoformat(),
                 response_file=str(result),response_sha256=sha(result),
                 response_bytes=result.stat().st_size,response_type=meta)
    recfile=dest/(name+".receipt.json")
    with recfile.open("x",encoding="utf-8") as out:
        json.dump(receipt,out,indent=2)
        out.write("\n")
    print("STAGE09B SUMMARY: 1/1 CDS request downloaded; SHA256 verified locally")
    print("RESULT FILE:",result)
    print("RECEIPT:",recfile)
    print("NEXT: inspect NetCDF variables, UTC time coverage and grid coordinates; NO substitutions made.")


if __name__=="__main__":
    main()
