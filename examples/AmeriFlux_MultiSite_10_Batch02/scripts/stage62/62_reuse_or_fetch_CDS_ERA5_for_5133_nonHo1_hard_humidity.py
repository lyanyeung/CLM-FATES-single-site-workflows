#!/usr/bin/env python3
"""Stage62: progress the 5,133 uncovered non-Ho1 hard humidity events.

SOURCE: Stage61 exact (site, original local timestamp) residuals, after
the 4,411 Stage60 user-approved scientific water-humidity selections.
Auto-reuse only checksum-and-calendar-verified independent CDS ERA5
t2m/d2m/sp grid-year receipts. With --fetch, retrieve a controlled batch of missing exact grid-years
using Stage50's validated CDS logic. With --auto, retrieve all remaining
missing grid-years in sequential bounded batches, validating each and
then build the candidate ledger in one invocation.
With --stage, create an isolated partial/full humidity patch ledger, keeping
original EC TA/PA if and only if TA valid and |TA-ERA5 T2m| <= 8 C.
Original T anomalies exceeding 8 C stay HOLD, as in previous policy.
US-Ho1's 16,788 cases, including the 917 Stage58 time-provenance HOLD,
are excluded; no guessed UTC time offset, no use of in-package FLUXNET ERA.
The 102 positive RH<1% source events remain separate review, not automatic
repairs. Nothing changes original data/Stage60/NetCDF/DATM/CIME/Slurm.
"""
import argparse
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORTS=ROOT/"reports"
STAGE61=REPORTS/"stage61_stage49_vs_stage60_full_hard_coverage_20261024T114810Z_fc209bf8"
STAGE50_SCRIPT=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02/scripts/stage50/50_prepare_unified_CDS_ERA5_RH_zero_gt100.py"
STAGE50_BLOB="757452798582dc0aaf6d2c78f23999e653247469"
CACHE=Path.home()/"AmeriFlux_Batch02_Stage62_external_CDS_ERA5"
INPUT="original_hard_events_not_in_Stage60_patch.csv"
SITES={"US-BZS":86,"US-CMW":42,"US-EML":2984,"US-GLE":830,
       "US-Ha1":23,"US-Ho2":717,"US-Ho3":39,"US-ICh":48,"US-ICt":364}
N_HO1=16788
PRODUCT="reanalysis-era5-single-levels-timeseries"
GOOD="CANDIDATE_EXTERNAL_ERA5_WATER_HUMIDITY_ORIGINAL_T_PA"

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):
            h.update(block)
    return h.hexdigest()

def gitblob(p):
    b=Path(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def stage50_module():
    if not STAGE50_SCRIPT.is_file() or STAGE50_SCRIPT.is_symlink():
        raise FileNotFoundError("Pinned Stage50 script missing "+str(STAGE50_SCRIPT))
    if gitblob(STAGE50_SCRIPT)!=STAGE50_BLOB:
        raise ValueError("Stage50 script Git blob changed; do not use modified CDS methods")
    spec=importlib.util.spec_from_file_location("batch02_pinned_stage50",STAGE50_SCRIPT)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def input_ledger():
    manifest=STAGE61/"coverage_manifest.json"
    m=json.loads(manifest.read_text())
    if ((STAGE61/"INCOMPLETE_DO_NOT_USE").exists() or
        m.get("schema")!="STAGE61_BATCH02_ORIGINAL_STAGE49_HARD_VS_STAGE60_CROSSWALK_v1" or
        m.get("original_hard_total")!=26332 or
        m.get("original_hard_not_covered")!=21921 or
        m.get("original_hard_covered_by_candidate")!=4411 or
        m.get("stage60_currently_applied_to_forcing")!=0 or
        m.get("approved_for_DATM") is not False or
        m.get("output_sha256",{}).get(INPUT)!=sha(STAGE61/INPUT)):
        raise ValueError("Stage61 original-source hard-anomaly provenance unexpected")
    for name,digest in m.get("output_sha256",{}).items():
        if sha(STAGE61/name)!=digest:
            raise ValueError("Changed Stage61 output: "+name)
    inp=m["input_sha256"]
    for name,path in (
        ("stage49_report_sha256",Path(m["stage49_source"])/"original_humidity_event_review.csv"),
        ("stage49_manifest_sha256",Path(m["stage49_source"])/"provenance_and_hold.json"),
        ("stage60_patch_sha256",Path(m["stage60_source"])/"4411_unique_original_tower_time_ERA5_water_humidity_patch.csv"),
        ("stage60_manifest_sha256",Path(m["stage60_source"])/"unified_science_policy_manifest.json")
    ):
        if sha(path)!=inp[name]:
            raise ValueError("Stage61 pinned parent input changed: "+name)
    a=pd.read_csv(STAGE61/INPUT,dtype={"site":str,"timestamp_start":str,
                                      "source_sha256":str,"local_key":str})
    if len(a)!=21921 or int((a.site=="US-Ho1").sum())!=N_HO1:
        raise ValueError("Stage61 total hard and Ho1 population changed")
    non=a.loc[a.site.ne("US-Ho1")].copy()
    if len(non)!=5133 or Counter(non.site)!=Counter(SITES):
        raise ValueError("Exact 5,133 nine-site target census changed")
    if non.duplicated(["site","timestamp_start"]).any():
        raise ValueError("Duplicate original site/native local timestamp")
    non["native_local"]=pd.to_datetime(non.timestamp_start,
                                      format="%Y%m%d%H%M",errors="raise")
    non["year"]=non.native_local.dt.year
    proof=json.loads((Path(m["stage49_source"])/"provenance_and_hold.json").read_text())
    inventory=Path(proof["inventory"]).resolve(strict=True)
    if sha(inventory)!=proof["inventory_sha256"]:
        raise ValueError("Stage49 primary source inventory altered")
    records=json.loads(inventory.read_text()).get("completed",[])
    specs={}
    for site in SITES:
        original=[r for r in records if r.get("site")==site
                  and not str(r.get("source","")).startswith("ERA5")]
        if len(original)!=1:
            raise ValueError("Site lacks exactly one original primary: "+site)
        s=original[0]
        if (sha(s["file"])!=s["sha256"] or
            proof["primary_sha256_by_site"].get(site)!=s["sha256"] or
            not non.loc[non.site.eq(site),"source_sha256"].eq(s["sha256"]).all()):
            raise ValueError("Original source/Stage49 checksum mismatch "+site)
        specs[site]=s
    return non,specs,{"Stage61_manifest_sha256":sha(manifest),
          "Stage61_uncovered_sha256":sha(STAGE61/INPUT),
          "Stage49_inventory_sha256":sha(inventory),
          "Stage50_script_git_blob_sha1":STAGE50_BLOB}

def site_meta(mod,specs):
    valid={};holds={}
    for site in SITES:
        try:
            values=mod.site_bif(specs[site])
            if values.get("offset_provenance")!="ORIGINAL_RELEASE_BIF":
                raise ValueError("No exact BIF offset evidence")
            valid[site]=values
        except (OSError,KeyError,ValueError) as ex:
            holds[site]="HOLD_ORIGINAL_RELEASE_BIF_UNVERIFIED: "+str(ex)
    return valid,holds

def build_plan(mod,events,info,missing_bif):
    key_site={}
    rows=[]
    for (site,year),grp in events.groupby(["site","year"],sort=True):
        year=int(year)
        if site in missing_bif:
            rows.append(dict(site=site,year=year,n_rows=len(grp),
                 retrieval_status="HOLD_UNVERIFIED_RELEASE_BIF",
                 grid_year_name="",verified_receipt="",utc_offset=""))
            continue
        k=(*info[site]["grid"],year)
        key_site.setdefault(k,[]).append(site)
        rows.append(dict(site=site,year=year,n_rows=len(grp),
             retrieval_status="PENDING_RECEIPT_CHECK",
             grid_year_name=mod.grid_name(k),
             verified_receipt="",utc_offset=info[site]["utc_offset"]))
    jobs={k:{"sites":list(sorted(set(names))),
             "latitude":next(info[site]["lat"] for site in names),
             "longitude":next(info[site]["lon"] for site in names)}
          for k,names in key_site.items()}
    for k,job in jobs.items():
        if any(info[site]["grid"]!=k[:2] for site in job["sites"]):
            raise ValueError("Incompatible shared ERA5 grid-year")
    return pd.DataFrame(rows),jobs

def locate_receipts(mod,plan,jobs):
    found={};missing=[]
    for key in sorted(jobs,key=lambda x:(x[2],x[0],x[1])):
        r,p=mod.resolve_receipt(key,jobs,CACHE)
        if r is None:
            missing.append(key)
        else:
            found[key]=(r,str(p))
    for i,row in plan.iterrows():
        if row["retrieval_status"]!="PENDING_RECEIPT_CHECK":continue
        site=row["site"];year=int(row["year"])
        key=next(k for k in jobs if k[2]==year and site in jobs[k]["sites"])
        receipt=found.get(key)
        plan.at[i,"retrieval_status"]=(
            "VERIFIED_INDEPENDENT_CDS_ERA5_REUSE" if receipt else "CDS_DOWNLOAD_REQUIRED")
        plan.at[i,"verified_receipt"]="" if not receipt else receipt[1]
    return found,missing

def fetch_new(mod,jobs,missing,limit):
    if not missing:
        print("STAGE62 FETCH NOT NEEDED | all verifiable grid-years available")
        return
    CACHE.mkdir(parents=True,exist_ok=True)
    for key in missing[:limit]:
        folder=CACHE/mod.grid_name(key)
        folder.mkdir(parents=True,exist_ok=True)
        marker=folder/"INCOMPLETE_DO_NOT_USE"
        receipt_file=folder/"verified_receipt.json"
        if receipt_file.exists():
            raise ValueError("Existing unaccepted receipt: "+str(receipt_file))
        if not marker.exists():
            if any(folder.iterdir()):
                raise ValueError("Unknown existing unverified CDS folder: "+str(folder))
            marker.write_text("CDS external source retrieval or validation pending.\n")
        payload=folder/"original_CDS_payload"
        request=dict(variable=mod.VARIABLES,
           location=dict(latitude=jobs[key]["latitude"],
                         longitude=jobs[key]["longitude"]),
           date=[f"{key[2]-1}-12-29",f"{key[2]+1}-01-03"],
           data_format="netcdf")
        if payload.is_file() and payload.stat().st_size>100:
            print("STAGE62 REUSING INTERRUPTED CDS PAYLOAD",payload,flush=True)
        elif payload.exists():
            raise ValueError("Incomplete local payload; manual filesystem inspection "+str(payload))
        else:
            payload,request=mod.request_payload(key,jobs[key],folder)
        target=folder/"era5_dewpoint_hourly_UTC.nc"
        nc=target if target.is_file() else mod.extract(payload,folder)
        mod.verify_nc(nc,key[2],key[:2])
        rec={"schema":"STAGE50_VERIFIED_CDS_ERA5_GRIDYEAR_v1",
             "grid_year_key":list(key),"dataset":PRODUCT,
             "variables":mod.VARIABLES,"sites":jobs[key]["sites"],
             "request":request,"science_approved":False,
             "original_payload_path":str(payload.resolve()),
             "original_payload_sha256":sha(payload),
             "netcdf_path":str(nc.resolve()),"netcdf_sha256":sha(nc),
             "no_model_approval":True}
        with receipt_file.open("x") as f:
            json.dump(rec,f,indent=2);f.write("\n")
        marker.unlink()
        print("STAGE62 VERIFIED NEW CDS GRID-YEAR",mod.grid_name(key),
              "NC_SHA",rec["netcdf_sha256"],flush=True)
    print("STAGE62 FETCH PASS | downloaded",min(limit,len(missing)),
          "of",len(missing),"missing verified grid-years")
    print("RERUN Stage62 --stage for the expanded candidate coverage")

def physics(mod,events,info,found,holds):
    dataset=[]
    cache={}
    for (site,year),group in events.groupby(["site","year"],sort=True):
        sub=group.copy()
        if site not in info:
            sub["candidate_status"]="HOLD_RELEASE_BIF_UNVERIFIED"
            dataset.append(sub);continue
        key=(*info[site]["grid"],int(year))
        if key not in found:
            sub["candidate_status"]="HOLD_VERIFIED_EXTERNAL_CDS_GRIDYEAR_MISSING"
            dataset.append(sub);continue
        receipt,receipt_path=found[key]
        netcdf=receipt["netcdf_path"]
        if netcdf not in cache:
            cache[netcdf]=mod.verify_nc(netcdf,int(year),key[:2])
        times,ts,td,ps,rh=cache[netcdf]
        utc=sub.native_local-pd.to_timedelta(info[site]["utc_offset"],unit="h")
        secs=times.astype("int64").to_numpy()/1.e9
        qsecs=utc.astype("int64").to_numpy()/1.e9
        if (qsecs.min()<secs[0] or qsecs.max()>secs[-1]):
            raise ValueError("Verified CDS time coverage gap "+site+" "+str(year))
        era_t=np.interp(qsecs,secs,ts)
        era_rh=np.interp(qsecs,secs,rh)
        original_t=pd.to_numeric(sub["TA_C"],errors="coerce").to_numpy(dtype=float)
        original_p=pd.to_numeric(sub["PA_kPa"],errors="coerce").to_numpy(dtype=float)
        with np.errstate(all="ignore"):
            sat=mod.es(original_t)
            vapor=sat*era_rh/100
            vpd=sat-vapor
            denom=original_p*1000-.378*vapor*100
            specific=.622*vapor*100/denom
        valid=(np.isfinite(original_t)&(original_t>-80)&(original_t<65)&
            np.isfinite(original_p)&(original_p>50)&(original_p<110)&
            np.isfinite(era_rh)&(era_rh>0)&(era_rh<=100.05)&
            np.isfinite(vpd)&(vpd>=-0.005)&np.isfinite(specific)&
            (specific>0)&(specific<.08))
        t_delta=np.abs(original_t-era_t)
        accepted=valid&(t_delta<=8)
        sub["candidate_status"]=np.where(
             accepted,GOOD,np.where(
             ~valid,"HOLD_INVALID_ORIGINAL_T_PA_OR_CDS_PHYSICS",
             "HOLD_ORIGINAL_TOWER_T_VS_ERA5_GT8C"))
        sub["source_UTC_offset_hours"]=info[site]["utc_offset"]
        sub["CDS_grid_year_name"]=mod.grid_name(key)
        sub["CDS_verified_receipt"]=receipt_path
        sub["CDS_netcdf_sha256"]=receipt["netcdf_sha256"]
        sub["ERA5_t2m_C"]=era_t
        sub["original_minus_ERA5_t2m_C"]=original_t-era_t
        sub["ERA5_RH_water_pct"]=era_rh
        sub["candidate_VPD_water_hPa"]=np.where(accepted,vpd,np.nan)
        sub["candidate_QBOT_kgkg"]=np.where(accepted,specific,np.nan)
        sub["approved_for_DATM"]=False
        dataset.append(sub)
    result=pd.concat(dataset,ignore_index=True)
    if len(result)!=5133 or result.duplicated(["site","timestamp_start"]).any():
        raise ValueError("Stage62 unique target scope changed")
    result["approved_for_DATM"]=False
    result["eligible_CDS_water_humidity_candidate"]=result.candidate_status.eq(GOOD)
    return result

def self_test():
    assert sum(SITES.values())==5133
    assert sum(SITES.values())+N_HO1==21921
    assert 4411+21921==26332
    # An existing relative-humidity reference cannot be used as ice VPD.
    tw=np.array([-30.,20.])
    assert np.isfinite(6.112*np.exp(17.67*tw/(tw+243.5))).all()
    print("STAGE62 SELF-TEST PASS | 5133 nine-site hard events, Ho1 16788 isolated")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    acts=ap.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","fetch","stage","auto"):
        acts.add_argument("--"+name,action="store_true")
    ap.add_argument("--max-new",type=int,default=8)
    args=ap.parse_args()
    if args.self_test:return self_test()
    if args.max_new<1:ap.error("--max-new must be >=1")
    mod=stage50_module()
    events,specs,pins=input_ledger()
    info,holds=site_meta(mod,specs)
    plan,jobs=build_plan(mod,events,info,holds)
    found,missing=locate_receipts(mod,plan,jobs)
    print("STAGE62 SOURCE CHECK PASS | 5133 uncovered non-Ho1; 16788 Ho1 separate; 4411 Stage60 unchanged")
    print("SOURCE_BIF_VERIFIED_SITES",list(sorted(info)))
    print("SOURCE_BIF_HOLD_SITES",holds)
    print("GRIDYEARS_REQUIRED",len(jobs),"VERIFIED_REUSABLE",len(found),
          "MISSING_INDEPENDENT_CDS",len(missing))
    print("GRIDYEARS_BLOCKED_BY_BIF",int(plan.retrieval_status.eq("HOLD_UNVERIFIED_RELEASE_BIF").sum()))
    for row in plan.to_dict("records"):
        print("YEAR",row["site"],row["year"],"events",row["n_rows"],
              row["retrieval_status"],row["grid_year_name"])
    print("US-Ho1 remains 16788 original hard events, not an ERA5-ready target set")
    if args.check:
        print("STAGE62 CHECK PASS | zero writes");return
    if args.fetch:
        fetch_new(mod,jobs,missing,args.max_new)
        return
    if args.auto:
        # User authorized physical-rule-based auto-completion. Only verified
        # same-product CDS files, never in-package ERA companions or source edits.
        original_missing=len(missing)
        completed=0
        while missing:
            before_count=len(missing)
            fetch_new(mod,jobs,missing,min(args.max_new,before_count))
            found,missing=locate_receipts(mod,plan,jobs)
            completed+=before_count-len(missing)
            print("STAGE62 AUTO CDS VERIFIED",completed,"/",original_missing,
                  "MISSING",len(missing),flush=True)
            if len(missing)>=before_count:
                raise RuntimeError("Stage62 auto retrieval made no verified progress")
        if not all(r["retrieval_status"] != "CDS_DOWNLOAD_REQUIRED"
                   for r in plan.to_dict("records")):
            raise ValueError("Stage62 stale missing-gridyear plan after auto mode")
        print("STAGE62 AUTO CDS COMPLETE | all",len(jobs),
              "verifiable exact grid-years receipt-checked",flush=True)
    patch=physics(mod,events,info,found,holds)
    counts=dict(Counter(patch.candidate_status))
    print("STAGE62 WATER_HUMIDITY_CANDIDATE_STATUS",counts)
    print("STAGE62 SELECTED",int(patch.eligible_CDS_water_humidity_candidate.sum()),"/5133")
    print("STAGE62 EXTERNAL_ERA5_MISSING",int(patch.candidate_status.eq(
        "HOLD_VERIFIED_EXTERNAL_CDS_GRIDYEAR_MISSING").sum()))
    print("STAGE62 T_VS_ERA5_GT8C",int(patch.candidate_status.eq(
        "HOLD_ORIGINAL_TOWER_T_VS_ERA5_GT8C").sum()))
    dest=REPORTS/("stage62_nonHo1_5133_verified_CDS_stage_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Stage62 selection only, NOT forcing or original-source edits.\n")
    outputs={"5133_uncovered_hard_events_CDS_candidate_status.csv":patch,
             "verified_grid_year_reuse_and_missing_plan.csv":plan,
             "new_ERA5_water_humidity_candidates_original_T_PA.csv":
                 patch.loc[patch.eligible_CDS_water_humidity_candidate].copy()}
    sums={}
    for name,frame in outputs.items():
        f=dest/name
        frame.to_csv(f,index=False)
        sums[name]=sha(f)
    if sha(STAGE61/INPUT)!=pins["Stage61_uncovered_sha256"]:
        raise ValueError("Stage61 report changed while preparing Stage62 output")
    for site in info:
        if sha(info[site]["bif"])!=info[site]["bif_sha256"]:
            raise ValueError("Original site BIF changed during Stage62 output")
    report=dict(schema="STAGE62_BATCH02_NONHO1_5133_CDS_ERA5_REUSE_OR_FETCH_v1",
        target_original_hard_nonHo1=5133,unresolved_original_hard_Ho1=16788,
        prior_stage60_proposals_unmodified=4411,
        independently_verified_CDS_gridyears=len(found),
        missing_CDS_gridyears=len(missing),
        source_BIF_HOLD=holds,source_BIF_verified=info,
        candidate_status_counts=counts,
        n_additional_independent_ERA5_candidates=int(
            patch.eligible_CDS_water_humidity_candidate.sum()),
        external_CDS_dataset=PRODUCT,original_tower_T_and_P_retained=True,
        source_SHA256=pins,outputs_SHA256=sums,
        approved_for_DATM=False,approved_for_spinup=False,
        no_original_or_model_changes=True)
    (dest/"candidate_ledger_manifest.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n")
    marker.unlink()
    print("STAGE62 STAGING PASS | distinct non-Ho1 original 5133 all accounted for")
    if args.auto:
        print("STAGE62 AUTO PASS | verified all accessible CDS grid-years; full 5133 candidate/hold census generated")
    print("REPORT",dest)
    print("NO ORIGINAL, Stage60, NETCDF FORCING, DATM, CIME OR SLURM CHANGES")
if __name__=="__main__":
    main()
