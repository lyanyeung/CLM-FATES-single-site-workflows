#!/usr/bin/env python3
"""Stage13i: audit the *complete* QC1 temperature source artifact around
US-MOz 2005-01-06, rather than confusing a >8 degC threshold with the start
or end of a truly bad source interval.

Compare exact SHA-pinned native half-hour original tower FLUXMET+QC vs its
paired standalone ERA5 companion, and the already-approved Stage13g science
shadow. Inventory actual QC1 gaps, 5/8/10C discrepant runs on the days
surrounding Jan06, and every 2005 QC1 discrepancy. Compute only paired
T/VPD/derived humidity scientific PREVIEWS. No replacements are approved.

--check has zero writes; --run creates only versioned SHA-receipted reports.
Never change raw tower/ERA, Stage07, Stage13g, cases, DATM, PFT, ZBOT, Slurm.
"""
import argparse, hashlib, json, sys, traceback
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VER="batch03-stage13i-v1-20261026-sourceQC1-2005-full-and-near-Jan6"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
S13G=R/"science_trials/stage13g_US_MOz_approved_native_T_VPD_20261026T180756Z_f75518a5"
S13H=R/"reports/stage13h_MOz_Jan2005_full_source_run_20261026T182004Z_d47ac8e2"
ORIGINAL_CANDIDATE=S07/"US-MOz/forcing/processed_v5/US-MOz_CLM_forcing_2004_2021.csv"
CURRENT=S13G/"US-MOz_CLM_forcing_2004_2021_STG13G_RESEARCH_SHADOW.csv"
SELECT_DAY=pd.Timestamp("2005-01-06")
START=pd.Timestamp("2005-01-03")
STOP=pd.Timestamp("2005-01-10")
NROWS=315360
DAYSTART=pd.Timestamp("2005-01-06 00:00")
DAYEND=pd.Timestamp("2005-01-06 23:30")
STEP=pd.Timedelta(minutes=30)

def file(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise RuntimeError("Absent or symlink source "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def saturation_c(t):
    return 6.112*np.exp(17.67*t/(t+243.5))

def read_orig(p,variables):
    cols=["TIMESTAMP_START",*variables]
    data=pd.read_csv(file(p),usecols=cols,dtype={"TIMESTAMP_START":str},low_memory=False)
    ix=pd.to_datetime(data.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    mask=ix.dt.year.between(2004,2021)&~((ix.dt.month==2)&(ix.dt.day==29))
    data=data.loc[mask].copy()
    data.index=pd.DatetimeIndex(ix.loc[mask],name="native_time")
    data.drop(columns=["TIMESTAMP_START"],inplace=True)
    if not data.index.is_monotonic_increasing or data.index.has_duplicates or data.index.hasnans:
        raise RuntimeError("Original tower/ERA native clock duplicated/disordered")
    for v in variables:
        data[v]=pd.to_numeric(data[v],errors="coerce")
        data.loc[data[v]<=-9990,v]=np.nan
    return data

def read_current(p):
    data=pd.read_csv(file(p),dtype={"time":str},low_memory=False)
    ti=pd.to_datetime(data.time,errors="raise")
    data.index=pd.DatetimeIndex(ti,name="native_time")
    if len(data)!=NROWS or data.index.has_duplicates or data.index.hasnans or not data.index.is_monotonic_increasing:
        raise RuntimeError("Current Stage13g research forcing source time is not valid")
    for k in ("TA_USE","VPD_USE","TBOT","QBOT","PSRF"):
        if k not in data:raise RuntimeError("Missing candidate input "+k)
        data[k]=pd.to_numeric(data[k],errors="coerce")
    return data

def groups(index,mask):
    """Native-time contiguous half-hour runs, with NO LEAP/year mixing."""
    vals=np.flatnonzero(np.asarray(mask,dtype=bool))
    if len(vals)==0:return []
    all_=[]
    start=last=int(vals[0])
    for j in vals[1:]:
        j=int(j)
        if j!=last+1 or index[j]-index[last]!=STEP:
            all_.append((start,last))
            start=j
        last=j
    all_.append((start,last))
    return all_

def validate():
    manifest=json.loads(file(S07/"exact_input_manifest.json").read_text())
    hashes={str(Path(p).resolve()):h for p,h in manifest["input_sha256"].items()}
    site=next(s for s in manifest["sites"] if s["site"]=="US-MOz")
    assert site["first_year"]==2004 and site["last_year"]==2021 and site["native_minutes"]==30
    for kind in ("primary","era"):
        p=file(site[kind])
        if sha(p)!=hashes.get(str(p.resolve())):
            raise RuntimeError("Source original altered or differs from exact Stage07 SHA: "+kind)
    stage13g=json.loads(file(S13G/"stage13g_MOz_approved_T_VPD_science_shadow_SHA_receipt.json").read_text())
    if stage13g.get("approved_model_field_edit_rows")!=9 or \
       stage13g.get("source_review",{}).get("2005_Jan06_05_09_source_HOLD_unchanged") is not True or \
       stage13g.get("source_review",{}).get("Postv5_approved") is not False:
        raise RuntimeError("Stage13g recorded approvals/holds do not match operator's decision")
    if sha(CURRENT)!=stage13g.get("all_output_SHA256",{}).get(CURRENT.name):
        raise RuntimeError("Stage13g science shadow altered")
    if sha(ORIGINAL_CANDIDATE)!=stage13g["source_review"].get("original_Stage07_selected_SHA256"):
        raise RuntimeError("Signed Stage07 selected original altered")
    stage13h=json.loads(file(S13H/"stage13h_MOz_2005_QC1_episode_source_SHA_receipt.json").read_text())
    prior=stage13h.get("science",{})
    if (prior.get("source_start")!="2005-01-06 01:30:00" or
        prior.get("source_end")!="2005-01-06 09:00:00" or
        prior.get("source_duration_HH")!=16 or
        prior.get("new_ERA_T_VPD_preview_applied_to_any_forcing") is not False or
        prior.get("operator_approval_required") is not True):
        raise RuntimeError("Original Stage13h reviewed QC1 core event changed")
    if stage13h.get("stage13g_source_model_candidate_SHA256")!=sha(CURRENT):
        raise RuntimeError("Stage13h original Stage13g signed candidate mismatch")
    for name in (
      "jan2005_full_QC1_warm_episode_ERA_paired_science_preview_NOT_APPLIED.csv",
      "jan2005_full_QC1_warm_episode_original_transition_boundaries.csv",
      "2005Jan06_all_48_original_HH_with_ERA_QC_and_stage13g.csv"):
        if sha(S13H/name)!=stage13h.get("output_SHA256",{}).get(name):
            raise RuntimeError("Stage13h previously reviewed scientific context altered "+name)
    return site

def audit():
    site=validate()
    t=read_orig(site["primary"],("TA_F","TA_F_QC","VPD_F","VPD_F_QC"))
    e=read_orig(site["era"],("TA_ERA","VPD_ERA"))
    c=read_current(CURRENT)
    if len(t)!=NROWS or not t.index.equals(e.index) or not t.index.equals(c.index):
        raise RuntimeError("Source tower, standalone ERA, and Stage13g candidate timelines differ")
    d=t.join(e,validate="one_to_one").join(c[["TA_USE","VPD_USE","TBOT","QBOT","PSRF"]],
                                         validate="one_to_one")
    d["tower_minus_ERA_T_C"]=d.TA_F-d.TA_ERA
    d["tower_minus_ERA_VPD_hPa"]=d.VPD_F-d.VPD_ERA
    d["source_T_QC1"]=d.TA_F_QC.eq(1)
    d["source_VPD_QC1"]=d.VPD_F_QC.eq(1)
    d["paired_original_QC1"]=d.source_T_QC1 & d.source_VPD_QC1
    d["both_companions_available"]=np.isfinite(d.TA_ERA)&np.isfinite(d.VPD_ERA)
    d["ERA_pair_water_RH_pct"]=100*(1-d.VPD_ERA/saturation_c(d.TA_ERA))
    pa=np.maximum(d.PSRF.to_numpy(dtype=float),1)
    vap=(saturation_c(d.TA_ERA.to_numpy(dtype=float))-d.VPD_ERA.to_numpy(dtype=float))*100
    d["ERA_pair_expected_QBOT_kgkg"]=0.622*vap/(pa-0.378*vap)
    d["ERA_pair_physics_pass"]=(d.both_companions_available &
       d.ERA_pair_water_RH_pct.gt(0) & d.ERA_pair_water_RH_pct.lt(100) &
       np.isfinite(d.ERA_pair_expected_QBOT_kgkg) &
       d.ERA_pair_expected_QBOT_kgkg.between(0,0.08, inclusive="neither"))
    d["original_pair_water_RH_pct"]=100*(1-d.VPD_F/saturation_c(d.TA_F))
    d["Stage13g_T_repaired_from_Stage07_source"] = ~np.isclose(d.TA_USE,d.TA_F,atol=1e-8,rtol=0)
    # Search a full calendar 2005 year and a 7-day vicinity, plus explicitly
    # include all Stage13h target day time rows.
    year=d.loc["2005"].copy()
    near=d.loc[START:STOP-pd.Timedelta(microseconds=1)].copy()
    day=d.loc["2005-01-06"].copy()
    if len(year)!=17520 or len(day)!=48 or len(near)!=7*48:
        raise RuntimeError("2005 selected native halfhour source cardinality inconsistent")
    if not(d.loc["2005-01-06 09:30","TA_F_QC"]==2 and
           d.loc["2005-01-06 10:30","TA_F_QC"]==2 and
           np.isclose(d.loc["2005-01-06 09:00","TA_F"],8.024)):
        raise RuntimeError("Known QC1->QC2 transitions changed")
    summaries=[]
    for cutoff in (3,5,8,10):
        criteria=(year.source_T_QC1 & year.both_companions_available &
            year.tower_minus_ERA_T_C.abs().gt(cutoff))
        runs=groups(year.index,criteria)
        for first,last in runs:
            seg=year.iloc[first:last+1]
            if not ((seg.index.max()>=START) and (seg.index.min()<STOP)):
                continue
            time_in_day=seg.index[(seg.index>=DAYSTART)&(seg.index<=DAYEND)]
            preexisting=seg.Stage13g_T_repaired_from_Stage07_source
            summaries.append({
                "threshold_abs_TminusERA_C":cutoff,
                "source_native_start":str(seg.index[0]),
                "source_native_end":str(seg.index[-1]),
                "half_hours":len(seg),"hours":len(seg)/2,
                "includes_Jan6":bool(len(time_in_day)>0),
                "Jan6_halfhours":len(time_in_day),
                "signed_difference_min_C":float(seg.tower_minus_ERA_T_C.min()),
                "signed_difference_max_C":float(seg.tower_minus_ERA_T_C.max()),
                "paired_original_VPD_QC1_count":int(seg.paired_original_QC1.sum()),
                "paired_ERA_waterRH_physical_pass_count":int(seg.ERA_pair_physics_pass.sum()),
                "paired_ERA_waterRH_physical_fail_count":int((~seg.ERA_pair_physics_pass).sum()),
                "Stage13g_already_corrected_T_slots":int(preexisting.sum()),
                "operator_approved_this_run":False,
            })
    run=pd.DataFrame(summaries)
    if len(run)==0 or len(run.loc[run.threshold_abs_TminusERA_C.eq(8)&run.includes_Jan6])<2:
        raise RuntimeError("Previously established two separate Jan06 source issues not recovered")
    # Do not interpret the cutoff (3/5/8/10) as true onset of source QC1.
    # Independent long segments of QC1 interpolated data are also inventoried.
    source_runs=groups(year.index,year.source_T_QC1)
    qc_segments=[]
    for a,b in source_runs:
        seg=year.iloc[a:b+1]
        if not ((seg.index.max()>=START) and (seg.index.min()<STOP)):
            continue
        qc_segments.append({
           "QC1_native_start":str(seg.index[0]),"QC1_native_end":str(seg.index[-1]),
           "QC1_halfhours":len(seg),"QC1_hours":len(seg)/2,
           "paired_QC1_VPD_count":int(seg.source_VPD_QC1.sum()),
           "abs_T_ERA_gt3C_count":int(seg.tower_minus_ERA_T_C.abs().gt(3).sum()),
           "abs_T_ERA_gt5C_count":int(seg.tower_minus_ERA_T_C.abs().gt(5).sum()),
           "abs_T_ERA_gt8C_count":int(seg.tower_minus_ERA_T_C.abs().gt(8).sum()),
           "paired_ERA_physical_pass_count":int(seg.ERA_pair_physics_pass.sum()),
           "paired_ERA_physical_fail_count":int((~seg.ERA_pair_physics_pass).sum()),
           "contains_already_approved_2005_10T_repair":
               bool(pd.Timestamp("2005-01-06 10:00") in seg.index),
           "operator_approved_this_run":False
        })
    qcruns=pd.DataFrame(qc_segments)
    cols=["TA_F","TA_F_QC","TA_ERA","VPD_F","VPD_F_QC","VPD_ERA",
          "TA_USE","VPD_USE","QBOT","tower_minus_ERA_T_C",
          "tower_minus_ERA_VPD_hPa","original_pair_water_RH_pct",
          "ERA_pair_water_RH_pct","ERA_pair_physics_pass","Stage13g_T_repaired_from_Stage07_source"]
    day=day[cols].reset_index(names="native_time")
    near=near[cols].reset_index(names="native_time")
    summary={
     "version":VER,"site":"US-MOz",
     "scope":"2005-01-03 through 2005-01-09 inclusive, source QCs and companion ERA",
     "Jan6_total_source_tower_QC1_T_halfhours":int(d.loc["2005-01-06"].source_T_QC1.sum()),
     "Jan6_total_source_tower_QC2_T_halfhours":int(d.loc["2005-01-06"].TA_F_QC.eq(2).sum()),
     "Jan6_source_tower_QC1_T_difference_ERA_gt5C_halfhours":
          int((d.loc["2005-01-06"].source_T_QC1 &
               d.loc["2005-01-06"].tower_minus_ERA_T_C.abs().gt(5)).sum()),
     "Jan6_source_tower_QC1_T_difference_ERA_gt8C_halfhours":
          int((d.loc["2005-01-06"].source_T_QC1 &
               d.loc["2005-01-06"].tower_minus_ERA_T_C.abs().gt(8)).sum()),
     "Jan6_still_unmodified_after_Stage13g_QC1_T_halfhours":
          int((d.loc["2005-01-06"].source_T_QC1 &
               ~d.loc["2005-01-06"].Stage13g_T_repaired_from_Stage07_source).sum()),
     "Jan6_original_QC1_minus_ERA_T_range_C":[
          float(d.loc["2005-01-06"].loc[d.loc["2005-01-06"].source_T_QC1,
               "tower_minus_ERA_T_C"].min()),
          float(d.loc["2005-01-06"].loc[d.loc["2005-01-06"].source_T_QC1,
               "tower_minus_ERA_T_C"].max())],
     "all_2005_QC1_T_count":int(year.source_T_QC1.sum()),
     "all_2005_original_QC1_T_gt5C_vs_ERA_count":
          int((year.source_T_QC1 & year.tower_minus_ERA_T_C.abs().gt(5)).sum()),
     "all_2005_original_QC1_T_gt8C_vs_ERA_count":
          int((year.source_T_QC1 & year.tower_minus_ERA_T_C.abs().gt(8)).sum()),
     "paired_ERA_not_independently_validated":True,
     "no_requested_replacement_applied":True,
     "current_Stage13g_candidate_SHA256":sha(CURRENT),
     "Stage07_primary_and_ERA_sha_pinned":True,
     "original_source_unchanged":True,"Postv5_approved":False,
     "DATM_ready":False,"spinup_authorized":False,
    }
    return day,near,run,qcruns,summary

def show(day,near,run,qcruns,summary):
    print("\n=== SUMMARY: QC1 vs ERA CLUSTERS, NOT SINGLE THRESHOLD EPISODE ===",flush=True)
    for k,v in summary.items():print(k,v,flush=True)
    print("\n=== UNBROKEN ORIGINAL T QC1 INTERVALS AROUND JAN6 ===",flush=True)
    print(qcruns.to_string(index=False),flush=True)
    print("\n=== SOURCE QC1 DIFFERENCE >3,5,8,10C RUNS (ONLY Jan3-9 INTERSECT) ===",flush=True)
    print(run.to_string(index=False),flush=True)
    print("\n=== JAN6 ALL 48 HALF-HOURS | PAIR SOURCE QCs, TEMP, VPD, PHYSICS ===",flush=True)
    print(day[["native_time","TA_F","TA_F_QC","TA_ERA","VPD_F","VPD_F_QC",
          "VPD_ERA","TA_USE","tower_minus_ERA_T_C",
          "ERA_pair_physics_pass","Stage13g_T_repaired_from_Stage07_source"]].to_string(
          index=False,float_format=lambda x:f"{x:.3f}"),flush=True)
    print("\nALL REANALYSIS REPLACEMENTS ARE PREVIEW ONLY. Nothing authorised/applied.",flush=True)

def main():
    p=argparse.ArgumentParser()
    m=p.add_mutually_exclusive_group(required=True)
    for o in ("self-test","check","run"):
        m.add_argument("--"+o,action="store_true")
    args=p.parse_args()
    print("STAGE13I US-MOz COMPLETE SOURCE QC1 MULTIDAY SCIENCE AUDIT | "+VER,flush=True)
    if not (START<DAYSTART<STOP and len(pd.date_range("2005-01-06",periods=48,freq="30min"))==48):
        raise RuntimeError("Stage13i configuration error")
    print("STAGE13I SELF-TEST PASS | never auto modify raw or candidate",flush=True)
    if args.self_test:return
    day,near,groups_,qcruns,summary=audit()
    show(day,near,groups_,qcruns,summary)
    if args.check:
        print("STAGE13I SOURCE CHECK PASS | ZERO WRITES",flush=True);return
    out=R/"reports"/("stage13i_US_MOz_Jan2005_QC1_multiday_episode_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    files={
      "Jan06_all_48_original_source_pairs_and_current_stage13g.csv":day,
      "Jan03_to_Jan09_all_source_ERA_QC_halfhours.csv":near,
      "Jan03_09_discrepant_sourceQC1_threshold_runs.csv":groups_,
      "Jan03_09_true_unbroken_source_QC1_runs.csv":qcruns,
    }
    for n,f in files.items():f.to_csv(out/n,index=False)
    warning="UNAPPROVED_JAN2005_SOURCE_CORRECTION_NO_DATM"
    (out/warning).write_text(
      "Previews only. QC1 source provenance / pair ERA independence not validated."
      " Stage13g, source tower/ERA, PFT/ZBOT/cases, and Slurm remain unchanged."
      " A 5/8C threshold does not define a scientifically verified true QC1"
      " source event boundary. Operator must approve exact bounded event set"
      " after further source provenance review.\n")
    receipt={"version":VER,"science":summary,
      "Stage13h_original_receipt_sha256":sha(S13H/
        "stage13h_MOz_2005_QC1_episode_source_SHA_receipt.json"),
      "Stage13g_signed_original_SHA256":sha(CURRENT),
      "output_SHA256":{n:sha(out/n) for n in [*files,warning]}}
    (out/"stage13i_MOz_source_QC1_2005_multiday_SHA_receipt.json").write_text(
         json.dumps(receipt,indent=2)+"\n")
    print("STAGE13I REPORT",out,flush=True)
    print("NO RAW, ERA, STAGE07, STAGE13G, PFT, ZBOT, CIME, DATM, SLURM WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13I STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)
