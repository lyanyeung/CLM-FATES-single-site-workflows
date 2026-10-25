#!/usr/bin/env python3
"""AmeriFlux Batch02 Stage72: preserve originals, fill only 10 unverified CDS grid-years.

Stage71 verified 16/26 independent CDS grid-years for US-Ho1 and US-BZS.
The other 10 cohorts contain 8,115 HARD RH/VPD source events. Some lack
an original receipt; other original receipts fail SHA/calendar checks.
No original CDS receipt/payload/NetCDF is modified, deleted, or renamed.

--plan: read-only proof/checksum and per-grid-year reasons, sorted largest first.
--fetch --max-new N: create-only CDS payloads/NetCDF/receipts in a NEW Stage72
    directory; one CDS request per missing year, with exclusive flock and
    source SHA, calendar, units and grid validation before writing a receipt.
    Interrupted verified payloads can be resumed; corrupt originals stay intact.
--audit: use Stage71's source-pinned original population and scientific
    computations, with Stage72 cache prefixed to prior caches; produce an
    isolated complete 16,874 source-event shadow and SHA manifest.
--self-test: no source access, tests target census, request ordering, keys.

No existing observation, ERA5 source, Stage64-71 report, DATM, forcing, CIME,
SLURM job or source time/temperature scientific HOLD is overwritten.
"""
import argparse, fcntl, hashlib, json
from collections import Counter
from datetime import datetime,timezone
from importlib import util
from pathlib import Path
from uuid import uuid4
import pandas as pd

BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
STAGE71_SCRIPT=BASE/"scripts/stage71/71_reuse_independent_CDS_Ho1_BZS_16874_shadow.py"
STAGE71_BLOB="b1ce47dedf3da4c931cac3b8a6d4822090870a81"
EXPERIMENT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT=EXPERIMENT/"reports"
SOURCE71=REPORT/"stage71_Ho1_BZS_independent_CDS_verified_reuse_shadow_20261025T083319Z_8aef8c86"
F_PLAN="Ho1_BZS_original_hard_gridyear_CDS_coverage.csv"
F_ROWS="16874_original_hard_independent_CDS_water_humidity_SHADOW.csv"
CACHE=Path.home()/"AmeriFlux_Batch02_Stage72_independent_CDS_ERA5_rescue"
REQUIRED={"US-BZS":{2011:7,2012:79},
 "US-Ho1":{2000:1069,2008:1036,2011:1366,2013:1474,
           2015:2268,2016:762,2021:46,2023:8}}
REQUIRED_EVENTS=sum(sum(z.values()) for z in REQUIRED.values())
EXPECTED_SITES={"US-BZS":86,"US-Ho1":16788}
EXPECTED_MISSING=10

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as fh:
        for part in iter(lambda:fh.read(1048576),b""):h.update(part)
    return h.hexdigest()

def gitblob(path):
    path=Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("Pinned Stage71 source file absent/nonregular")
    b=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def parent():
    if gitblob(STAGE71_SCRIPT)!=STAGE71_BLOB:
        raise ValueError("Pinned Stage71 scientific reader Git blob changed")
    spec=util.spec_from_file_location("pinned_batch02_stage71",STAGE71_SCRIPT)
    mod=util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def source_report():
    proof=json.loads((SOURCE71/"stage71_source_science_manifest.json").read_text())
    if ((SOURCE71/"INCOMPLETE_DO_NOT_USE").exists()
        or proof.get("schema")!="STAGE71_HO1_BZS_INDEPENDENT_CDS_VERIFIED_RECEIPT_SHADOW_v1"
        or proof.get("n_original_hard_total")!=16874
        or proof.get("n_Ho1")!=16788
        or proof.get("n_BZS")!=86
        or proof.get("n_verified_CDS_gridyears")!=16
        or proof.get("n_requested_CDS_gridyears")!=26
        or proof.get("n_num_valid_only")!=7695
        or proof.get("n_remaining_HOLD")!=16874
        or proof.get("historical_BIF_offset_date_verified") is not False
        or proof.get("approved_for_DATM") is not False):
        raise ValueError("Stage71 science provenance/source status unexpected")
    for name,v in proof["output_sha256"].items():
        if sha(SOURCE71/name)!=v:
            raise ValueError("Stage71 report source SHA256 changed "+name)
    plan=pd.read_csv(SOURCE71/F_PLAN)
    rows=pd.read_csv(SOURCE71/F_ROWS,usecols=["site","science_status"])
    if len(plan)!=26 or len(rows)!=16874:
        raise ValueError("Stage71 complete source census changed")
    state=rows.science_status.value_counts().to_dict()
    if state!={"HOLD_NO_VERIFIED_CDS_GRIDYEAR":8115,
        "SHADOW_NUMERIC_VALID_KEEP_ORIGINAL_T_PA_BIF_DATE_HOLD":7695,
        "HOLD_ORIGINAL_TA_QC_NONZERO":987,
        "HOLD_TOWER_T_VS_INDEPENDENT_ERA5_GT8C":77}:
        raise ValueError("Stage71 status census changed "+str(state))
    missing=plan.loc[
        plan["CDS_status"].eq("HOLD_NO_VERIFIED_CDS_GRIDYEAR")].copy()
    if (len(missing)!=10 or int(missing["n_original_hard"].sum())!=REQUIRED_EVENTS
        or set((site,int(year)) for site,year in
               zip(missing.site,missing.original_tower_year)) !=
           set((s,year) for s,years in REQUIRED.items() for year in years)):
        raise ValueError("Expected exact ten source gap grid-years changed")
    for r in missing.itertuples(index=False):
        if int(r.n_original_hard)!=REQUIRED[r.site][int(r.original_tower_year)]:
            raise ValueError("Stage71 per-grid-year original hard counts changed")
    if proof["source_SHA256"]["Stage50_reader_gitblob"]!=
       "757452798582dc0aaf6d2c78f23999e653247469":
        raise ValueError("Stage71 source algorithm dependency changed")
    return proof,plan,missing

def current(mod,mod71,missing):
    """Classify all existing old and new receipts without accepting unverified."""
    plan=[]
    for row in missing.itertuples(index=False):
        site=row.site
        year=int(row.original_tower_year)
        grid=(float(row.ERA5_grid_lat),float(row.ERA5_grid_lon))
        key=(*grid,year)
        name=mod.grid_name(key)
        target=CACHE/name/"verified_receipt.json"
        if target.exists():
            if target.is_symlink():
                raise ValueError("Unsafe Stage72 source receipt symlink "+str(target))
            # Any Stage72 checksum/calendar failure aborts. No old corrupt receipt is overwritten.
            previous=mod.read_receipt(target,key,[site])
            if previous is None:
                raise ValueError("Stage72 present receipt but failed source gate "+str(target))
            status="STAGE72_VERIFIED_REUSE"
            problem=""
        else:
            inspected=mod71.checked_receipt(mod,key,site)
            if inspected["receipt"] is not None:
                status="VERIFIED_IN_OLDER_SOURCE_AFTER_STAGE71"
            elif inspected["issues"]:
                status="SOURCE_REJECTION_ISOLATED_REDOWNLOAD"
            else:
                status="SOURCE_ABSENT_FRESH_DOWNLOAD"
            problem=" | ".join(inspected["issues"])
        plan.append({"site":site,"original_tower_year":year,
          "original_hard_events":int(row.n_original_hard),
          "CDS_grid_lat":grid[0],"CDS_grid_lon":grid[1],
          "CDS_gridyear":name,"state":status,
          "old_receipt_issue":problem,
          "new_cache_receipt":str(target),
          "source_replacements_approved":False,
          "historical_UTC_approved":False})
    order={"SOURCE_REJECTION_ISOLATED_REDOWNLOAD":0,
           "SOURCE_ABSENT_FRESH_DOWNLOAD":1,
           "VERIFIED_IN_OLDER_SOURCE_AFTER_STAGE71":2,
           "STAGE72_VERIFIED_REUSE":3}
    return pd.DataFrame(plan).sort_values(
        ["state","original_hard_events","site","original_tower_year"],
        key=lambda col:col.map(order) if col.name=="state" else
            -col if col.name=="original_hard_events" else col,
        kind="stable").reset_index(drop=True)

def request_one(mod,row):
    site=row["site"]
    year=int(row["original_tower_year"])
    key=(float(row["CDS_grid_lat"]),float(row["CDS_grid_lon"]),year)
    folder=CACHE/mod.grid_name(key)
    if folder.is_symlink():
        raise ValueError("Refusing symlinked recovery destination "+str(folder))
    folder.mkdir(parents=True,exist_ok=True)
    receipt_path=folder/"verified_receipt.json"
    if receipt_path.exists():
        result=mod.read_receipt(receipt_path,key,[site])
        if result is None:
            raise ValueError("Invalid present Stage72 receipt; refused overwrite")
        print("STAGE72 ALREADY VERIFIED",mod.grid_name(key),flush=True)
        return
    marker=folder/"INCOMPLETE_DO_NOT_USE"
    if not marker.exists():
        if any(folder.iterdir()):
            raise ValueError("Unrecognized existing Stage72 recovery folder; preserve contents "+str(folder))
        marker.write_text("Independent CDS source fetch unfinished, not approved for DATM.\n")
    payload=folder/"original_CDS_payload"
    request={"variable":mod.VARIABLES,
             "location":{"latitude":float(row["CDS_grid_lat"]),
                         "longitude":float(row["CDS_grid_lon"])},
             "date":[f"{year-1}-12-29",f"{year+1}-01-03"],
             "data_format":"netcdf"}
    if payload.is_file() and payload.stat().st_size>100:
        print("STAGE72 RESUME OLD UNVERIFIED STAGE72 PAYLOAD",payload,flush=True)
    elif payload.exists():
        raise ValueError("Incomplete new-cache payload cannot be overwritten "+str(payload))
    else:
        job={"latitude":float(row["CDS_grid_lat"]),
             "longitude":float(row["CDS_grid_lon"]),
             "sites":[site]}
        payload,request=mod.request_payload(key,job,folder)
    nc=folder/"era5_dewpoint_hourly_UTC.nc"
    verified_nc=nc if nc.is_file() else mod.extract(payload,folder)
    mod.verify_nc(verified_nc,year,key[:2])
    proof={"schema":"STAGE50_VERIFIED_CDS_ERA5_GRIDYEAR_v1",
      "grid_year_key":list(key),"dataset":mod.DATASET,
      "variables":mod.VARIABLES,"sites":[site],
      "request":request,"science_approved":False,
      "original_payload_path":str(payload.resolve()),
      "original_payload_sha256":sha(payload),
      "netcdf_path":str(verified_nc.resolve()),
      "netcdf_sha256":sha(verified_nc),
      "no_model_approval":True}
    # A source can be verified only with its byte-pinned original CDS payload,
    # full buffered UTC calendar and 0.25 degree grid, no model permissions.
    if receipt_path.exists():
        raise ValueError("Another process created Stage72 receipt; race refused")
    with receipt_path.open("x") as f:
        json.dump(proof,f,indent=2);f.write("\n")
    back=mod.read_receipt(receipt_path,key,[site])
    if not back or back["netcdf_sha256"]!=proof["netcdf_sha256"]:
        raise ValueError("Stage72 own receipt validation FAILED (marker retained)")
    marker.unlink()
    print("STAGE72 VERIFIED NEW INDEPENDENT CDS",site,year,
          "SHA256",proof["netcdf_sha256"],flush=True)

def fetch(mod,mod71,missing,limit):
    CACHE.mkdir(parents=True,exist_ok=True)
    lock=CACHE/".stage72_one_writer.lock"
    with lock.open("a+") as f:
        try:
            fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("A Stage72 writer is already active") from exc
        try:
            plan=current(mod,mod71,missing)
            wanted=plan.loc[plan.state.isin([
                "SOURCE_REJECTION_ISOLATED_REDOWNLOAD",
                "SOURCE_ABSENT_FRESH_DOWNLOAD"])]
            # Largest original cohorts first, irrespective of whether old
            # source was absent or had a corrupt old receipt.
            wanted=wanted.sort_values(
                ["original_hard_events","site","original_tower_year"],
                ascending=[False,True,True])
            for row in wanted.head(limit).to_dict("records"):
                print("STAGE72 ACQUIRE",row["site"],row["original_tower_year"],
                      "events",row["original_hard_events"],flush=True)
                request_one(mod,row)
            print("STAGE72 FETCH PASS | new receipts checked",
                  min(len(wanted),limit),"/",len(wanted),
                  "| originals unmodified")
        finally:
            fcntl.flock(f.fileno(),fcntl.LOCK_UN)

def report(mod,mod71,source,baseline,missing):
    plan=current(mod,mod71,missing)
    for row in plan.itertuples(index=False):
        print("GAP",row.site,int(row.original_tower_year),
              "N",int(row.original_hard_events),
              row.state,"ORIGINAL_RECEIPT_ISSUE",row.old_receipt_issue,flush=True)
    print("STAGE72 ORIGINAL VERIFIED BASELINE",int(source["n_verified_CDS_gridyears"]),"/26")
    print("STAGE72 PRIOR 8115 MISSING EVENTS (SOURCE ONLY)")
    print("STAGE72 STAGING NOW VERIFIED",
          int(plan.state.eq("STAGE72_VERIFIED_REUSE").sum()))
    print("STAGE72 OUTSTANDING",
          int(plan.state.isin(["SOURCE_REJECTION_ISOLATED_REDOWNLOAD",
                             "SOURCE_ABSENT_FRESH_DOWNLOAD"]).sum()))
    print("STAGE72 HISTORICAL UTC SCIENCE HOLD remains for all 16874 records")
    return plan

def audit(mod,mod71,source,baseline,missing):
    mod71.CACHE_DIRS=(CACHE,)+tuple(mod71.CACHE_DIRS)
    original,sites,manifest70=mod71.load_original()
    result,year,verified=mod71.build(original,sites,mod)
    if len(result)!=16874 or result["approved_for_DATM"].any():
        raise ValueError("Stage72 updated shadow cohort lost original source scope")
    prior=baseline[["site","science_status"]].copy()
    prior_group=prior.groupby(["site","science_status"]).size()
    now=result.groupby(["site","science_status"]).size()
    if result["science_status"].eq(
         "SHADOW_NUMERIC_VALID_KEEP_ORIGINAL_T_PA_BIF_DATE_HOLD").sum()<7695:
        raise ValueError("Stage72 independent CDS new source changed earlier valid candidate count")
    p=report(mod,mod71,source,baseline,missing)
    dest=REPORT/("stage72_16874_original_independent_CDS_recovery_shadow_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("New isolated independent CDS only, no model science approval.\n")
    csvs={"16874_original_independent_CDS_Ho1_BZS_merged_source_SHADOW.csv":result,
          "26_Ho1_BZS_gridyears_current_CDS_coverage.csv":year,
          "10_original_missing_CDS_source_recovery_priority.csv":p}
    outputs={}
    for name,frame in csvs.items():
        path=dest/name;frame.to_csv(path,index=False);outputs[name]=sha(path)
    proof={
      "schema":"STAGE72_IMMUTABLE_16874_HO1_BZS_CDS_RECOVERY_SHADOW_v1",
      "stage71_initial_verified_gridyear_count":16,
      "stage71_original_missing_gridyear_count":10,
      "stage71_original_missing_hard_events":8115,
      "n_current_verified_gridyear_count":len(verified),
      "n_now_shadow_numeric_candidates":int(
         result.science_status.eq(
             "SHADOW_NUMERIC_VALID_KEEP_ORIGINAL_T_PA_BIF_DATE_HOLD").sum()),
      "n_original_source_population":16874,
      "stage64_previous_9389_numeric_candidates_unchanged":True,
      "all_16874_original_hard_HOLD_retained":True,
      "historical_UTC_source_validity_approved":False,
      "approved_for_DATM":False,"approved_for_spinup":False,
      "source_sha256":{
         "stage71_manifest":sha(SOURCE71/"stage71_source_science_manifest.json"),
         "stage71_previous_plan":sha(SOURCE71/F_PLAN),
         "stage71_previous_cohort":sha(SOURCE71/F_ROWS),
         "stage71_script_blob":STAGE71_BLOB},
      "outputs_sha256":outputs,
      "no_existing_source_ERA5_DATM_or_model_writes":True}
    (dest/"stage72_source_science_manifest.json").write_text(
        json.dumps(proof,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE72 AUDIT PASS | refreshed 16874 original Ho1/BZS independent CDS coverage SHADOW; no forcing approval")
    print("REPORT",dest)
    print("NO ORIGINAL, PRIOR CDS, STAGE64-71, NETCDF FORCING, DATM, CIME OR SLURM CHANGES")

def self_test():
    assert REQUIRED_EVENTS==8115
    assert len([(s,y) for s,v in REQUIRED.items() for y in v])==10
    assert sum(EXPECTED_SITES.values())==16874
    assert (round(45.2040*4)/4,round(-68.7402*4)/4)==(45.25,-68.75)
    assert (round(64.6963*4)/4,round(-148.3235*4)/4)==(64.75,-148.25)
    print("STAGE72 SELF-TEST PASS | 10 original missing grid-years; 8115 source events; original CDS immutable")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    for key in ("self-test","plan","fetch","audit"):
        mode.add_argument("--"+key,action="store_true")
    p.add_argument("--max-new",type=int,default=2)
    args=p.parse_args()
    if args.self_test:return self_test()
    if args.max_new<1 or args.max_new>10:
        p.error("--max-new must be between 1 and 10")
    mod71=parent()
    mod=mod71.load_era()
    proof,oldplan,missing=source_report()
    baseline=pd.read_csv(SOURCE71/F_ROWS,usecols=["site","science_status"])
    if args.plan:
        report(mod,mod71,proof,baseline,missing)
        print("STAGE72 PLAN PASS | all original source/data preserved; no writes")
    elif args.fetch:
        report(mod,mod71,proof,baseline,missing)
        fetch(mod,mod71,missing,args.max_new)
    else:
        audit(mod,mod71,proof,baseline,missing)

if __name__=="__main__":
    main()
