#!/usr/bin/env python3
"""Stage74: recover exactly four absent Ho1/BZS independent CDS ERA5 grid-years.

Operator Stage73 PASS independently verified the full original source cohort
using 22/26 valid grid-years. Original source events still missing independent
CDS years: Ho1 2000 (1069), Ho1 2008 (1036), BZS 2012 (79), BZS 2011 (7).
The Stage73 cross-site exact-grid bridges for Ho1 2011/2016/2021/2023 must
be preserved and reused, not downloaded again.

--plan: prove Stage73 source/output hashes; show exact four missing years,
        current Stage72 cache and any verification errors; NO WRITES.
--fetch: ONLY those four site/years (max-new configurable). Reuse the
         original SHA+calendar checked Stage72 create-only retrieval
         under an exclusive writer lock. Never overwrite old sources.
--audit: rebuild full 16,874 original source shadows via pinned Stage71,
         preferring Stage73 exact-grid bridges and Stage72 new source files.
         Write only a NEW isolated report with SHA256 provenance.
--self-test: source-free checks only.

Even with all 26 external CDS years verified, official historical BIF
UTC-offset applicability, 9,389 previous proposals, 69 other-site T holds,
995 original tower-T QC holds and 82 T-vs-ERA contextual holds are not
automatically approved. Original source, independent CDS, forcing, NetCDF,
DATM, CIME and Slurm must remain unchanged except new standalone CDS
original payload/NC/receipt files within the isolated Stage72 cache.
"""
import argparse
import fcntl
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from importlib import util
from pathlib import Path
from uuid import uuid4
import pandas as pd

BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
STAGE73=BASE/"scripts/stage73/73_same_grid_cross_site_original_CDS_receipts.py"
STAGE73_GIT_BLOB="66af1ae518ff56ff55165c58f26afb5863b6688b"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORTS=ROOT/"reports"
PARENT=REPORTS/"stage73_exact_grid_cross_site_verified_CDS_shadow_20261025T085440Z_4ca0e311"
PARENT_COVERAGE="26_gridyear_CDS_verified_coverage.csv"
MISSING={
    ("US-Ho1",2000):1069,
    ("US-Ho1",2008):1036,
    ("US-BZS",2012):79,
    ("US-BZS",2011):7,
}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def git_blob(path):
    p=Path(path)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Pinned Stage73 source is missing or symlinked")
    b=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def load_modules():
    if git_blob(STAGE73)!=STAGE73_GIT_BLOB:
        raise ValueError("Pinned original Stage73 Python scientific source changed")
    s=util.spec_from_file_location("batch02_stage73_pinned",STAGE73)
    s73=util.module_from_spec(s)
    s.loader.exec_module(s73)
    s72,s71,era=s73.modules()
    return s73,s72,s71,era

def input_gate():
    if (PARENT/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Stage73 upstream report incomplete")
    m=json.loads((PARENT/"stage73_source_science_manifest.json").read_text())
    if (m.get("schema")!="STAGE73_ORIGINAL_HO1_BZS_SAME_GRID_CDS_REUSE_v1"
        or m.get("n_original_hard")!=16874
        or m.get("n_cross_site_target_years")!=4
        or m.get("n_current_verified_gridyears")!=22
        or m.get("n_new_numeric_shadow_candidates")!=13606
        or m.get("n_no_independent_CDS")!=2191
        or m.get("all_original_hard_HOLD_retained") is not True
        or m.get("BIF_historical_UTC_approval") is not False
        or m.get("DATM_approved") is not False
        or m.get("stage64_9389_unchanged") is not True):
        raise ValueError("Stage73 source/science manifest does not match actual operator PASS")
    for name,digest in m["output_SHA256"].items():
        if sha(PARENT/name)!=digest:
            raise ValueError("Original Stage73 output mutated: "+name)
    plan=pd.read_csv(PARENT/PARENT_COVERAGE)
    if len(plan)!=26 or plan["n_original_hard"].sum()!=16874:
        raise ValueError("Stage73 complete source-event year scope changed")
    actual={}
    for row in plan.itertuples(index=False):
        if row.CDS_status=="HOLD_NO_VERIFIED_CDS_GRIDYEAR":
            actual[(row.site,int(row.original_tower_year))]=int(row.n_original_hard)
    if actual!=MISSING:
        raise ValueError("Original four truly unverified CDS target grid-years changed: "+str(actual))
    cross=pd.read_csv(PARENT/"4_original_cross_site_CDS_provenance_status.csv")
    if (len(cross)!=4 or
        not cross["status"].eq("ALREADY_BRIDGED_VERIFIED").all() or
        set(cross["year"].astype(int))!={2011,2016,2021,2023}):
        raise ValueError("Stage73 four verified source bridges changed")
    return m,plan

def target_rows(s73,s72,s71,era):
    # Reuse the Stage73 cross-site bridge, existing verified Stage72 cache,
    # and previously SHA+calendar checked immutable receipts.
    s71.CACHE_DIRS=(s73.BRIDGE,s72.CACHE)+tuple(s71.CACHE_DIRS)
    output=[]
    for (site,year),n in MISSING.items():
        lat,lon=((45.2040,-68.7402) if site=="US-Ho1"
                 else (64.6963,-148.3235))
        grid=era.grid_of(lat,lon)
        key=(*grid,year)
        matched=s71.checked_receipt(era,key,site)
        local=s72.CACHE/era.grid_name(key)/"verified_receipt.json"
        if matched["receipt"] is not None:
            state="VERIFIED_REUSE_ALREADY_PRESENT"
        elif matched["issues"]:
            state="HOLD_UNVERIFIED_SOURCE_EVIDENCE"
        else:
            state="SOURCE_ABSENT_NEEDS_INDEPENDENT_CDS_DOWNLOAD"
        output.append({
          "site":site,"original_tower_year":year,
          "original_hard_events":n,
          "CDS_grid_lat":grid[0],"CDS_grid_lon":grid[1],
          "CDS_gridyear":era.grid_name(key),
          "state":state,"verified_receipt":matched["path"],
          "evidence_rejections":matched["issues"],
          "destination_receipt":str(local),
          "approved_for_DATM":False})
    return pd.DataFrame(output).sort_values(
        ["original_hard_events","site","original_tower_year"],
        ascending=[False,True,True]).reset_index(drop=True)

def display(plan):
    for r in plan.itertuples(index=False):
        print("STAGE74 FOUR-GAP SOURCE",r.site,int(r.original_tower_year),
              "ORIGINAL_HARD",int(r.original_hard_events),
              "GRIDYEAR",r.CDS_gridyear,"STATUS",r.state,flush=True)
        for error in r.evidence_rejections:
            print("  SOURCE_REJECTION",error,flush=True)
    print("STAGE74 CURRENT VERIFIED FOUR-GAP",int(
        plan["state"].eq("VERIFIED_REUSE_ALREADY_PRESENT").sum()),"/4")
    print("STAGE74 STILL WITHOUT CDS",int(
        plan["state"].ne("VERIFIED_REUSE_ALREADY_PRESENT").sum()),
        "GRIDYEARS",int(plan.loc[plan["state"].ne(
            "VERIFIED_REUSE_ALREADY_PRESENT"),"original_hard_events"].sum()),
        "ORIGINAL HARD EVENTS")
    print("STAGE74 NO HISTORICAL UTC/TA/FORCING APPROVAL")

def fetch(s72,era,plan,max_new):
    if s72.CACHE.is_symlink():
        raise ValueError("Refusing Stage72 CDS cache symlink")
    s72.CACHE.mkdir(parents=True,exist_ok=True)
    # Coordinate with Stage72 --fetch so neither downloader writes at
    # the same time. No existing source files or receipts are overwritten.
    with (s72.CACHE/".stage72_one_writer.lock").open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Stage72 / Stage74 fetch already active") from exc
        try:
            pending=plan.loc[plan["state"].eq(
                "SOURCE_ABSENT_NEEDS_INDEPENDENT_CDS_DOWNLOAD")]
            refused=plan.loc[plan["state"].eq(
                "HOLD_UNVERIFIED_SOURCE_EVIDENCE")]
            if len(refused):
                raise ValueError("Unverified original CDS evidence needs inspection before download: "+
                                 str(refused[["site","original_tower_year"]].to_dict("records")))
            for row in pending.head(max_new).to_dict("records"):
                print("STAGE74 FETCH INDEPENDENT CDS",row["site"],
                    int(row["original_tower_year"]),
                    "ORIGINAL HARD",int(row["original_hard_events"]),flush=True)
                s72.request_one(era,row)
            print("STAGE74 FETCH PASS | newly verified isolated grid-years",
                min(len(pending),max_new),"/",len(pending),
                "all original source and model files preserved")
        finally:
            fcntl.flock(lock.fileno(),fcntl.LOCK_UN)

def audit(s73,s72,s71,era,prior):
    s71.CACHE_DIRS=(s73.BRIDGE,s72.CACHE)+tuple(s71.CACHE_DIRS)
    events,stations,source70=s71.load_original()
    rows,coverage,receipts=s71.build(events,stations,era)
    if (len(rows)!=16874 or Counter(rows["site"])!=Counter(s71.COUNTS)
        or rows["approved_for_DATM"].any()
        or rows["historical_BIF_time_source_verified"].any()):
        raise ValueError("Original science cohort or HOLD status altered")
    counts=rows["science_status"].value_counts(dropna=False).to_dict()
    n_num=int(rows["science_status"].eq(
       "SHADOW_NUMERIC_VALID_KEEP_ORIGINAL_T_PA_BIF_DATE_HOLD").sum())
    n_missing=int(rows["science_status"].eq(
       "HOLD_NO_VERIFIED_CDS_GRIDYEAR").sum())
    if n_num<13606 or n_missing>2191 or len(receipts)<22:
        raise ValueError("Previously verified ERA5 source candidates regressed")
    current=target_rows(s73,s72,s71,era)
    display(current)
    print("STAGE74 GRIDYEARS VERIFIED",len(receipts),"/26")
    print("STAGE74 ORIGINAL HARD SOURCE 16874 STATUS",counts)
    target=REPORTS/("stage74_four_missing_years_16874_Ho1_BZS_CDS_SHADOW_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    target.mkdir(parents=True,exist_ok=False)
    marker=target/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Independent CDS shadow only; no DATM forcing approval.\n")
    files={
      "16874_original_hard_independent_CDS_shadow_refreshed.csv":rows,
      "26_site_gridyears_verified_CDS_coverage.csv":coverage,
      "four_genuine_missing_CDS_years_source_status.csv":current}
    hashes={}
    for name,df in files.items():
        out=target/name
        df.to_csv(out,index=False)
        hashes[name]=sha(out)
    proof={
      "schema":"STAGE74_FOUR_GENUINE_CDS_GAP_RECOVERY_SHADOW_v1",
      "original_source_event_count":16874,
      "previous_Stage73_verified_gridyears":22,
      "current_independent_CDS_verified_gridyears":len(receipts),
      "current_independent_ERA5_numeric_shadow":n_num,
      "current_no_independent_CDS_original_events":n_missing,
      "remaining_nonzero_TA_QC":int(counts.get(
        "HOLD_ORIGINAL_TA_QC_NONZERO",0)),
      "remaining_tower_ERA_T_gt8C":int(counts.get(
        "HOLD_TOWER_T_VS_INDEPENDENT_ERA5_GT8C",0)),
      "all_original_hard_HOLD_retained":True,
      "historic_site_BIF_UTC_applicability_approved":False,
      "prior_Stage64_9389_candidates_untouched":True,
      "approved_for_DATM":False,
      "approved_for_spinup":False,
      "source_SHA256":{
        "stage73_report_manifest":sha(PARENT/"stage73_source_science_manifest.json"),
        "stage73_script_git_blob":STAGE73_GIT_BLOB},
      "outputs_sha256":hashes,
      "no_existing_source_or_model_edits":True}
    (target/"stage74_source_science_manifest.json").write_text(
        json.dumps(proof,sort_keys=True,indent=2)+"\n")
    marker.unlink()
    print("STAGE74 AUDIT PASS | four target years independently verified or held; full 16874 source shadow retained")
    print("REPORT",target)
    print("NO ORIGINAL EC, PRIOR CDS, STAGE64-73, NETCDF FORCING, DATM, CIME OR SLURM CHANGES")

def self_test():
    assert sum(MISSING.values())==2191
    assert len(MISSING)==4
    assert sum(y for (site,year),y in MISSING.items() if site=="US-Ho1")==2105
    assert sum(y for (site,year),y in MISSING.items() if site=="US-BZS")==86
    assert 13606+2191+995+82==16874
    print("STAGE74 SELF-TEST PASS | only four genuine CDS gaps, 2191 original hard; no source overwrite")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    for option in ("self-test","plan","fetch","audit"):
        group.add_argument("--"+option,action="store_true")
    p.add_argument("--max-new",type=int,default=2)
    a=p.parse_args()
    if a.self_test:return self_test()
    if not 1<=a.max_new<=4:
        p.error("--max-new must be between 1 and 4")
    s73,s72,s71,era=load_modules()
    prior,old=input_gate()
    plan=target_rows(s73,s72,s71,era)
    if a.plan:
        display(plan)
        print("STAGE74 PLAN PASS | four isolated missing CDS years only; zero writes")
    elif a.fetch:
        display(plan)
        fetch(s72,era,plan,a.max_new)
    else:
        audit(s73,s72,s71,era,prior)
if __name__=="__main__":
    main()
