#!/usr/bin/env python3
"""Stage73: reuse immutable independent CDS ERA5 receipts across same-grid towers.

Original Stage62/50 source receipts may list another site sharing the exact
CDS quarter-degree grid/year. Do not confuse source membership mismatch with
invalid original ERA5. Require original receipt source-site membership, grid
key, request-point grid, payload SHA, NetCDF SHA, calendar, units, coordinates.
Create NEW bridge receipts with source provenance, not edit old receipts.
Original Stage71 science remains HOLD; no forcing, CIME, Slurm modifications.
"""
import argparse, fcntl, hashlib, json
from collections import Counter
from datetime import datetime,timezone
from importlib import util
from pathlib import Path
from uuid import uuid4
import pandas as pd

BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
SOURCE=BASE/"scripts/stage72/72_rescue_missing_10_Ho1_BZS_independent_CDS_gridyears.py"
SOURCE_BLOB="3326c317fcf5fada71f15370828245355852948f"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT=ROOT/"reports"
OLD=REPORT/"stage72_16874_original_independent_CDS_recovery_shadow_20261025T084352Z_01da7b3d"
BRIDGE=Path.home()/"AmeriFlux_Batch02_Stage73_same_grid_original_CDS_bridge"
TARGET={2011:1366,2016:762,2021:46,2023:8}
SITE="US-Ho1"

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def gitblob(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():raise ValueError("Pinned script absent")
    b=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def modules():
    if gitblob(SOURCE)!=SOURCE_BLOB:raise ValueError("Stage72 blob changed")
    sp=util.spec_from_file_location("pinned_stage72_bridge",SOURCE)
    s72=util.module_from_spec(sp);sp.loader.exec_module(s72)
    s71=s72.parent()
    era=s71.load_era()
    return s72,s71,era

def upstream(s72):
    m=json.loads((OLD/"stage72_source_science_manifest.json").read_text())
    if ((OLD/"INCOMPLETE_DO_NOT_USE").exists() or
        m.get("schema")!="STAGE72_IMMUTABLE_16874_HO1_BZS_CDS_RECOVERY_SHADOW_v1" or
        m.get("n_current_verified_gridyear_count")!=18 or
        m.get("n_now_shadow_numeric_candidates")!=11432 or
        m.get("n_original_source_population")!=16874 or
        m.get("historical_UTC_source_validity_approved") is not False or
        m.get("approved_for_DATM") is not False):
        raise ValueError("Unexpected Stage72 full-source evidence")
    for name,s in m["outputs_sha256"].items():
        if sha(OLD/name)!=s:raise ValueError("Stage72 SHA256 mismatch "+name)
    _,plan,missing=s72.source_report()
    for year,n in TARGET.items():
        row=missing.loc[(missing.site==SITE)&
            (missing.original_tower_year==year)]
        if len(row)!=1 or int(row.n_original_hard.iloc[0])!=n:
            raise ValueError("Stage71 missing original target census changed "+str(year))
    return m

def candidates(s71,era,year):
    key=(*era.grid_of(45.2040,-68.7402),year)
    out=[]
    for receipt in s71.receipt_candidates(era,key,SITE):
        if not receipt.exists():continue
        row={"source_receipt":str(receipt),"eligible":False,"reason":"",
          "original_sites":[],"original_receipt_sha256":"",
          "netcdf_sha256":"","payload_sha256":""}
        try:
            if receipt.is_symlink() or not receipt.is_file():
                raise ValueError("Unsafe symlink / nonregular receipt")
            meta=json.loads(receipt.read_text())
            members=meta.get("sites")
            if not isinstance(members,list) or not members or any(
                not isinstance(x,str) or not x for x in members):
                raise ValueError("Original site membership malformed")
            if SITE in members:
                raise ValueError("Already member of old receipt; no bridge needed")
            if (meta.get("schema")!="STAGE50_VERIFIED_CDS_ERA5_GRIDYEAR_v1" or
                meta.get("grid_year_key")!=list(key)):
                raise ValueError("Original receipt schema/gridyear mismatch")
            loc=meta["request"]["location"]
            if era.grid_of(float(loc["latitude"]),float(loc["longitude"]))!=key[:2]:
                raise ValueError("CDS request location not at same quarter-degree grid")
            # PASS with the actual original sites only after independent
            # payload SHA, NetCDF SHA, unit/calendar/coordinate verification.
            orig=era.read_receipt(receipt,key,members)
            if orig is None:raise ValueError("Original receipt unexpectedly absent")
            row.update({"eligible":True,"original_sites":members,
             "original_receipt_sha256":sha(receipt),
             "netcdf_sha256":orig["netcdf_sha256"],
             "payload_sha256":orig["original_payload_sha256"]})
        except (OSError,ValueError,KeyError,TypeError,AttributeError) as ex:
            row["reason"]=type(ex).__name__+": "+str(ex)[:320]
        out.append(row)
    return out

def inspect(s71,era):
    result=[]
    for year,n in TARGET.items():
        key=(*era.grid_of(45.2040,-68.7402),year)
        evidence=candidates(s71,era,year)
        valid=[e for e in evidence if e["eligible"]]
        inconsistent=(len(set(e["netcdf_sha256"] for e in valid))>1 or
                      len(set(e["payload_sha256"] for e in valid))>1)
        chosen=valid[0] if valid and not inconsistent else None
        dest=BRIDGE/era.grid_name(key)/"verified_receipt.json"
        bridged=False
        if dest.exists():
            if dest.is_symlink():raise ValueError("Bridge symlink forbidden")
            rec=era.read_receipt(dest,key,[SITE])
            if rec is None:raise ValueError("Existing bridge invalid")
            origin=Path(rec["bridge_source_receipt"])
            if sha(origin)!=rec["bridge_source_receipt_sha256"]:
                raise ValueError("Original source receipt changed under bridge")
            bridged=True
        state=("ALREADY_BRIDGED_VERIFIED" if bridged else
               "HOLD_MULTIPLE_SOURCE_SHA_CONFLICT" if inconsistent else
               "ELIGIBLE_SAME_GRID_PROVEN_SOURCE" if chosen else
               "HOLD_NO_ORIGINAL_SOURCE_PROVEN")
        result.append({"site":SITE,"year":year,"original_events":n,
         "gridyear":era.grid_name(key),"status":state,
         "source_receipt":chosen["source_receipt"] if chosen else "",
         "original_members":",".join(chosen["original_sites"]) if chosen else "",
         "source_receipt_sha256":chosen["original_receipt_sha256"] if chosen else "",
         "netcdf_sha256":chosen["netcdf_sha256"] if chosen else "",
         "payload_sha256":chosen["payload_sha256"] if chosen else "",
         "bridge_receipt":str(dest),
         "source_rejections":[e["reason"] for e in evidence if e["reason"]],
         "DATM_approved":False})
    return pd.DataFrame(result).sort_values("original_events",ascending=False)

def print_plan(plan):
    for row in plan.itertuples(index=False):
        print("STAGE73 SOURCE",row.site,row.year,"N",row.original_events,
            "STATUS",row.status,"ORIGINAL_MEMBERS",row.original_members,
            "ORIGIN",row.source_receipt,flush=True)
        for reason in row.source_rejections:
            print("  REJECTION",reason,flush=True)
    print("STAGE73 ELIGIBLE",plan.status.eq("ELIGIBLE_SAME_GRID_PROVEN_SOURCE").sum(),
          "BRIDGED",plan.status.eq("ALREADY_BRIDGED_VERIFIED").sum(),"/4",flush=True)

def do_bridge(era,plan):
    if BRIDGE.is_symlink():raise ValueError("Unsafe bridge root symlink")
    BRIDGE.mkdir(parents=True,exist_ok=True)
    with (BRIDGE/".stage73_lock").open("a+") as lock:
        try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as ex:
            raise RuntimeError("Another Stage73 bridge writer running") from ex
        try:
            for row in plan.itertuples(index=False):
                if row.status!="ELIGIBLE_SAME_GRID_PROVEN_SOURCE":continue
                key=(*era.grid_of(45.2040,-68.7402),int(row.year))
                p=Path(row.source_receipt)
                src=json.loads(p.read_text())
                orig=era.read_receipt(p,key,src["sites"])
                if orig is None or sha(p)!=row.source_receipt_sha256:
                    raise ValueError("Original receipt mutated since Stage73 --plan")
                dest=Path(row.bridge_receipt)
                dest.parent.mkdir(parents=True,exist_ok=True)
                if any(dest.parent.iterdir()):
                    raise ValueError("Unknown existing bridge destination "+str(dest.parent))
                marker=dest.parent/"INCOMPLETE_DO_NOT_USE"
                marker.write_text("Bridge unapproved pending source QA.\n")
                meta=dict(orig)
                meta.update({"sites":[SITE],
                  "bridge_origin_original_sites":list(orig["sites"]),
                  "bridge_source_receipt":str(p),
                  "bridge_source_receipt_sha256":sha(p),
                  "bridge_original_same_quarter_degree_gridyear":True,
                  "bridge_science_permission":"READ_ONLY_SHADOW_NOT_DATM",
                  "science_approved":False,"no_model_approval":True})
                with dest.open("x") as f:
                    json.dump(meta,f,indent=2,sort_keys=True);f.write("\n")
                checked=era.read_receipt(dest,key,[SITE])
                if checked is None or checked["netcdf_sha256"]!=orig["netcdf_sha256"]:
                    raise ValueError("Created bridge source failed independent CDS read")
                marker.unlink()
                print("STAGE73 BRIDGE PROVEN",SITE,row.year,
                      "ORIGINAL_SOURCE_SHA",sha(p),flush=True)
        finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
    print("STAGE73 BRIDGE PASS | immutable independent CDS source receipts verified")

def do_audit(s72,s71,era,plan,manifest):
    s71.CACHE_DIRS=(BRIDGE,s72.CACHE)+tuple(s71.CACHE_DIRS)
    events,sites,_=s71.load_original()
    shadow,coverage,found=s71.build(events,sites,era)
    if (len(shadow)!=16874 or
        Counter(shadow["site"])!=Counter(s71.COUNTS) or
        shadow["approved_for_DATM"].any() or
        shadow["historical_BIF_time_source_verified"].any()):
        raise ValueError("Refuse any original source/event/time approval")
    summary=inspect(s71,era)
    print_plan(summary)
    print("STAGE73 CURRENT VERIFIED INDEPENDENT CDS",len(found),"/26")
    print("STAGE73 ORIGINAL SOURCE 16874 SCIENCE STATUS",
          shadow["science_status"].value_counts().to_dict())
    dest=REPORT/("stage73_exact_grid_cross_site_verified_CDS_shadow_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("No original source or DATM permission.\n")
    data={"16874_original_independent_CDS_cross_site_SHADOW.csv":shadow,
          "26_gridyear_CDS_verified_coverage.csv":coverage,
          "4_original_cross_site_CDS_provenance_status.csv":summary}
    outputs={}
    for name,frame in data.items():
        p=dest/name;frame.to_csv(p,index=False);outputs[name]=sha(p)
    proof={"schema":"STAGE73_ORIGINAL_HO1_BZS_SAME_GRID_CDS_REUSE_v1",
       "n_original_hard":16874,"n_cross_site_target_years":4,
       "n_current_verified_gridyears":len(found),
       "n_new_numeric_shadow_candidates":int(shadow["science_status"].eq(
            "SHADOW_NUMERIC_VALID_KEEP_ORIGINAL_T_PA_BIF_DATE_HOLD").sum()),
       "n_no_independent_CDS":int(shadow["science_status"].eq(
            "HOLD_NO_VERIFIED_CDS_GRIDYEAR").sum()),
       "all_original_hard_HOLD_retained":True,
       "BIF_historical_UTC_approval":False,
       "DATM_approved":False,"spinup_approved":False,
       "stage64_9389_unchanged":True,
       "parent_SHA256":{"stage72_manifest":sha(
           OLD/"stage72_source_science_manifest.json"),
           "stage72_gitblob":SOURCE_BLOB},
       "output_SHA256":outputs,"no_existing_source_model_writes":True}
    (dest/"stage73_source_science_manifest.json").write_text(
        json.dumps(proof,sort_keys=True,indent=2)+"\n")
    marker.unlink()
    print("STAGE73 AUDIT PASS | full 16874 source-cohort same-grid CDS shadow, original HOLD retained")
    print("REPORT",dest)
    print("NO ORIGINAL TOWER, PRIOR CDS, NETCDF FORCING, DATM, CIME OR SLURM WRITES")

def self_test():
    assert sum(TARGET.values())==2182
    assert 1069+1036+79+7==2191
    assert 2182+2191==4373
    assert 16788+86==16874
    print("STAGE73 SELF-TEST PASS | four cross-site 2182 hard, four absent 2191")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    for option in ("self-test","plan","bridge","audit"):
        group.add_argument("--"+option,action="store_true")
    args=p.parse_args()
    if args.self_test:return self_test()
    s72,s71,era=modules()
    m=upstream(s72)
    plan=inspect(s71,era)
    if args.plan:
        print_plan(plan)
        print("STAGE73 PLAN PASS | original receipts and models untouched")
    elif args.bridge:
        print_plan(plan)
        do_bridge(era,plan)
    else:
        do_audit(s72,s71,era,plan,m)
if __name__=="__main__":
    main()
